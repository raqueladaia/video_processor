"""
Brightness and Contrast Analysis Module

This module provides algorithms for analyzing video frames to determine optimal
brightness and contrast settings. It uses histogram analysis and statistical
measures to suggest improvements.

Author: Video Processing Project
"""

import cv2
import numpy as np
from typing import Tuple, Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to path for shared module imports
sys.path.append(str(Path(__file__).parent.parent))


class BrightnessAnalyzer:
    """
    Analyzes video frames to suggest optimal brightness and contrast adjustments.

    Uses histogram analysis, statistical measures, and image quality metrics
    to determine if a video is under-exposed, over-exposed, or has poor contrast.
    """

    def __init__(self):
        """Initialize the brightness analyzer with default thresholds."""
        # Brightness analysis thresholds
        self.dark_threshold = 85  # Pixels below this are considered dark
        self.bright_threshold = 170  # Pixels above this are considered bright
        self.optimal_mean_range = (90, 165)  # Optimal brightness range for mean pixel value

        # Contrast analysis thresholds
        self.low_contrast_threshold = 40  # Standard deviation threshold for low contrast
        self.optimal_contrast_range = (50, 80)  # Optimal contrast range

    def analyze_frame(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Analyze a single frame for brightness and contrast characteristics.

        Args:
            frame (np.ndarray): Input video frame (BGR format)

        Returns:
            Dict[str, float]: Analysis results containing various metrics
        """
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Calculate basic statistics
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)

        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_normalized = hist.flatten() / hist.sum()

        # Analyze brightness distribution
        dark_pixels_ratio = np.sum(hist_normalized[:self.dark_threshold])
        bright_pixels_ratio = np.sum(hist_normalized[self.bright_threshold:])
        mid_pixels_ratio = 1.0 - dark_pixels_ratio - bright_pixels_ratio

        # Calculate dynamic range
        min_val, max_val = np.min(gray), np.max(gray)
        dynamic_range = max_val - min_val

        # Calculate contrast using RMS contrast
        rms_contrast = np.sqrt(np.mean((gray - mean_brightness) ** 2))

        # Detect histogram peaks to assess exposure
        hist_peaks = self._detect_histogram_peaks(hist_normalized)

        return {
            'mean_brightness': mean_brightness,
            'std_brightness': std_brightness,
            'dark_pixels_ratio': dark_pixels_ratio,
            'bright_pixels_ratio': bright_pixels_ratio,
            'mid_pixels_ratio': mid_pixels_ratio,
            'dynamic_range': dynamic_range,
            'rms_contrast': rms_contrast,
            'histogram_peaks': hist_peaks,
            'min_value': min_val,
            'max_value': max_val
        }

    def analyze_video_sample(self, video_path: str, sample_frames: int = 10) -> Dict[str, float]:
        """
        Analyze a sample of frames from a video to get overall characteristics.

        Args:
            video_path (str): Path to the video file
            sample_frames (int): Number of frames to sample for analysis

        Returns:
            Dict[str, float]: Average analysis results across sampled frames
        """
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        # Get total frame count
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total_frames == 0:
            cap.release()
            raise ValueError(f"Video has no frames: {video_path}")

        # Calculate frame indices to sample evenly throughout the video
        frame_indices = np.linspace(0, total_frames - 1, min(sample_frames, total_frames), dtype=int)

        analyses = []

        for frame_idx in frame_indices:
            # Seek to the specific frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if ret:
                analysis = self.analyze_frame(frame)
                analyses.append(analysis)

        cap.release()

        if not analyses:
            raise ValueError(f"Could not analyze any frames from video: {video_path}")

        # Calculate average metrics across all analyzed frames
        avg_analysis = {}
        for key in analyses[0].keys():
            if key == 'histogram_peaks':
                # For peaks, take the most common peak position
                all_peaks = [analysis[key] for analysis in analyses]
                avg_analysis[key] = self._average_peaks(all_peaks)
            else:
                avg_analysis[key] = np.mean([analysis[key] for analysis in analyses])

        return avg_analysis

    def suggest_adjustments(self, analysis: Dict[str, float]) -> Dict[str, int]:
        """
        Suggest brightness and contrast adjustments based on analysis results.

        Args:
            analysis (Dict[str, float]): Analysis results from analyze_frame or analyze_video_sample

        Returns:
            Dict[str, int]: Suggested brightness and contrast adjustments (-100 to +100)
        """
        brightness_adjustment = 0
        contrast_adjustment = 0

        mean_brightness = analysis['mean_brightness']
        rms_contrast = analysis['rms_contrast']
        dark_pixels_ratio = analysis['dark_pixels_ratio']
        bright_pixels_ratio = analysis['bright_pixels_ratio']

        # Brightness adjustment suggestions
        if mean_brightness < self.optimal_mean_range[0]:
            # Video is too dark
            if dark_pixels_ratio > 0.3:  # More than 30% dark pixels
                brightness_adjustment = min(50, int((self.optimal_mean_range[0] - mean_brightness) * 0.8))
            else:
                brightness_adjustment = min(30, int((self.optimal_mean_range[0] - mean_brightness) * 0.5))

        elif mean_brightness > self.optimal_mean_range[1]:
            # Video is too bright
            if bright_pixels_ratio > 0.3:  # More than 30% bright pixels
                brightness_adjustment = max(-50, int((self.optimal_mean_range[1] - mean_brightness) * 0.8))
            else:
                brightness_adjustment = max(-30, int((self.optimal_mean_range[1] - mean_brightness) * 0.5))

        # Contrast adjustment suggestions
        if rms_contrast < self.low_contrast_threshold:
            # Low contrast - suggest increasing
            contrast_adjustment = min(40, int((self.optimal_contrast_range[0] - rms_contrast) * 0.8))

        elif rms_contrast > self.optimal_contrast_range[1]:
            # Too high contrast - suggest reducing
            contrast_adjustment = max(-20, int((self.optimal_contrast_range[1] - rms_contrast) * 0.3))

        return {
            'brightness': brightness_adjustment,
            'contrast': contrast_adjustment
        }

    def get_analysis_description(self, analysis: Dict[str, float]) -> str:
        """
        Generate a human-readable description of the video analysis.

        Args:
            analysis (Dict[str, float]): Analysis results

        Returns:
            str: Human-readable description of the video characteristics
        """
        mean_brightness = analysis['mean_brightness']
        rms_contrast = analysis['rms_contrast']
        dark_pixels_ratio = analysis['dark_pixels_ratio']
        bright_pixels_ratio = analysis['bright_pixels_ratio']

        description_parts = []

        # Brightness assessment
        if mean_brightness < self.optimal_mean_range[0]:
            if dark_pixels_ratio > 0.4:
                description_parts.append("Video is significantly under-exposed (very dark)")
            else:
                description_parts.append("Video is somewhat under-exposed (dark)")
        elif mean_brightness > self.optimal_mean_range[1]:
            if bright_pixels_ratio > 0.4:
                description_parts.append("Video is significantly over-exposed (very bright)")
            else:
                description_parts.append("Video is somewhat over-exposed (bright)")
        else:
            description_parts.append("Video brightness is in optimal range")

        # Contrast assessment
        if rms_contrast < self.low_contrast_threshold:
            description_parts.append("low contrast (appears flat or washed out)")
        elif rms_contrast > self.optimal_contrast_range[1]:
            description_parts.append("high contrast (may appear harsh)")
        else:
            description_parts.append("good contrast")

        return ", ".join(description_parts).capitalize()

    def _detect_histogram_peaks(self, hist_normalized: np.ndarray) -> List[int]:
        """
        Detect peaks in the histogram to identify dominant brightness values.

        Args:
            hist_normalized (np.ndarray): Normalized histogram

        Returns:
            List[int]: List of histogram peak positions
        """
        # Use simple peak detection - find local maxima above threshold
        peaks = []
        threshold = 0.01  # 1% of pixels

        for i in range(1, len(hist_normalized) - 1):
            if (hist_normalized[i] > threshold and
                hist_normalized[i] > hist_normalized[i-1] and
                hist_normalized[i] > hist_normalized[i+1]):
                peaks.append(i)

        return peaks

    def _average_peaks(self, all_peaks: List[List[int]]) -> List[int]:
        """
        Calculate average peak positions across multiple frames.

        Args:
            all_peaks (List[List[int]]): List of peak lists from multiple frames

        Returns:
            List[int]: Average peak positions
        """
        if not all_peaks:
            return []

        # Flatten all peaks and find the most common ones
        all_peak_values = []
        for peaks in all_peaks:
            all_peak_values.extend(peaks)

        if not all_peak_values:
            return []

        # Group similar peak values and return representatives
        unique_peaks = []
        all_peak_values.sort()

        for peak in all_peak_values:
            # Group peaks within 10 units of each other
            if not unique_peaks or abs(peak - unique_peaks[-1]) > 10:
                unique_peaks.append(peak)

        return unique_peaks