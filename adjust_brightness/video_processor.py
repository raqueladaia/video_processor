"""
Video Processing Module for Brightness and Contrast Adjustment

This module handles the actual video processing operations, including applying
brightness and contrast adjustments using FFmpeg directly for fast, high-quality processing.

Author: Video Processing Project
"""

import cv2
import numpy as np
from pathlib import Path
import sys
import os
import subprocess
import re
import tempfile
import json
from typing import Optional, Callable, Tuple

# Add parent directory to path for shared module imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.file_utils import create_output_directory, sanitize_filename, get_unique_filename
from shared.video_utils import get_video_info, is_valid_video_file


class VideoProcessor:
    """
    Handles video processing operations for brightness and contrast adjustment.

    Uses FFmpeg directly for fast, high-quality video processing while
    maintaining original video properties and codec settings.
    """

    def __init__(self):
        """Initialize the video processor."""
        self.temp_dir = None
        self.current_preview_frame = None

    def apply_brightness_contrast(self, input_path: str, output_path: str,
                                  brightness: int = 0, contrast: int = 0,
                                  progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Apply brightness and contrast adjustments to a video file using FFmpeg.

        Args:
            input_path (str): Path to input video file
            output_path (str): Path for output video file
            brightness (int): Brightness adjustment (-100 to +100)
            contrast (int): Contrast adjustment (-100 to +100)
            progress_callback (Optional[Callable[[float], None]]): Callback for progress updates

        Returns:
            bool: True if processing successful, False otherwise
        """
        try:
            # Validate input file
            if not is_valid_video_file(input_path):
                print(f"Error: Invalid video file: {input_path}")
                return False

            # Create output directory if it doesn't exist
            output_dir = Path(output_path).parent
            if not create_output_directory(str(output_dir)):
                print(f"Error: Could not create output directory: {output_dir}")
                return False

            # Convert brightness and contrast values to match OpenCV preview calculation
            # OpenCV uses: beta = brightness * 2.55, alpha = 1.0 + (contrast / 100.0)
            # FFmpeg eq filter: brightness = beta/255, contrast = alpha
            brightness_value = (brightness * 2.55) / 255.0  # Convert to FFmpeg range
            contrast_value = 1.0 + (contrast / 100.0)  # Same as OpenCV alpha

            # Clamp values to safe ranges
            brightness_value = max(-1.0, min(1.0, brightness_value))
            contrast_value = max(0.1, min(3.0, contrast_value))

            # Build FFmpeg command
            cmd = [
                'ffmpeg', '-y',  # -y to overwrite output files
                '-i', input_path,
            ]

            # Add video filter if adjustments are needed
            if brightness != 0 or contrast != 0:
                filter_str = f"eq=brightness={brightness_value}:contrast={contrast_value}"
                cmd.extend(['-vf', filter_str])

            # Add output settings for quality preservation
            cmd.extend([
                '-c:v', 'libx264',  # Use H.264 codec
                '-crf', '18',       # High quality setting
                '-preset', 'medium', # Balance speed vs compression
                '-c:a', 'copy',     # Copy audio without re-encoding
                output_path
            ])

            # Get video duration for progress calculation
            video_info = get_video_info(input_path)
            total_duration = video_info['duration'] if video_info else 0

            # Execute FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # Monitor progress
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break

                if output and progress_callback and total_duration > 0:
                    # Parse FFmpeg progress output
                    progress = self._parse_ffmpeg_progress(output, total_duration)
                    if progress is not None:
                        progress_callback(progress)

            # Wait for process to complete
            process.wait()

            if process.returncode == 0:
                print(f"Successfully processed video: {output_path}")
                return True
            else:
                stderr_output = process.stderr.read() if process.stderr else "Unknown error"
                print(f"FFmpeg error: {stderr_output}")
                return False

        except Exception as e:
            print(f"Error processing video {input_path}: {e}")
            return False

    def create_preview_frame(self, video_path: str, start_time: float = 0) -> Optional[np.ndarray]:
        """
        Extract a preview frame from a video using FFmpeg.

        Args:
            video_path (str): Path to the source video
            start_time (float): Time in seconds to extract frame from

        Returns:
            Optional[np.ndarray]: Preview frame as BGR numpy array or None if error
        """
        try:
            # Build FFmpeg command to extract a single frame
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', video_path,
                '-vframes', '1',
                '-f', 'image2pipe',
                '-vcodec', 'png',
                '-'
            ]

            # Execute FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            stdout, stderr = process.communicate()

            if process.returncode == 0 and stdout:
                # Convert PNG data to numpy array
                nparr = np.frombuffer(stdout, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is not None:
                    self.current_preview_frame = frame.copy()
                    return frame

            return None

        except Exception as e:
            print(f"Error creating preview frame from {video_path}: {e}")
            return None

    def apply_preview_adjustments(self, brightness: int = 0, contrast: int = 0) -> Optional[np.ndarray]:
        """
        Apply brightness/contrast adjustments to the current preview frame using FFmpeg.
        
        This ensures the preview matches exactly what will be saved in the final video.

        Args:
            brightness (int): Brightness adjustment (-100 to +100)
            contrast (int): Contrast adjustment (-100 to +100)

        Returns:
            Optional[np.ndarray]: Adjusted frame as numpy array (BGR format) or None if error
        """
        if self.current_preview_frame is None:
            return None

        try:
            # Use FFmpeg to apply adjustments for consistency with final output
            # Create a temporary file for the current frame
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_input:
                # Save current frame as PNG
                cv2.imwrite(temp_input.name, self.current_preview_frame)
                temp_input_path = temp_input.name

            # Apply adjustments using FFmpeg
            adjusted_frame = self._apply_ffmpeg_adjustments_to_frame(
                temp_input_path, brightness, contrast
            )

            # Clean up temporary file
            try:
                os.unlink(temp_input_path)
            except:
                pass

            return adjusted_frame

        except Exception as e:
            print(f"Error applying preview adjustments: {e}")
            return None

    def create_preview_with_adjustments(self, video_path: str, brightness: int = 0,
                                       contrast: int = 0, start_time: float = 0) -> Optional[np.ndarray]:
        """
        Create a preview frame with brightness/contrast adjustments applied using FFmpeg.

        Args:
            video_path (str): Path to the source video
            brightness (int): Brightness adjustment (-100 to +100)
            contrast (int): Contrast adjustment (-100 to +100)
            start_time (float): Time in seconds to extract frame from

        Returns:
            Optional[np.ndarray]: Adjusted preview frame or None if error
        """
        try:
            # Convert brightness and contrast values to FFmpeg format
            brightness_value = brightness / 100.0
            contrast_value = 1.0 + (contrast / 100.0)

            # Clamp values
            brightness_value = max(-1.0, min(1.0, brightness_value))
            contrast_value = max(0.1, min(3.0, contrast_value))

            # Build FFmpeg command with filters
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', video_path,
                '-vframes', '1',
                '-f', 'image2pipe',
                '-vcodec', 'png'
            ]

            # Add filter if adjustments are needed
            if brightness != 0 or contrast != 0:
                filter_str = f"eq=brightness={brightness_value}:contrast={contrast_value}"
                cmd.extend(['-vf', filter_str])

            cmd.append('-')

            # Execute FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            stdout, stderr = process.communicate()

            if process.returncode == 0 and stdout:
                # Convert PNG data to numpy array
                nparr = np.frombuffer(stdout, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                return frame

            return None

        except Exception as e:
            print(f"Error creating preview with adjustments: {e}")
            return None

    def generate_output_path(self, input_path: str, output_dir: str,
                             brightness: int = 0, contrast: int = 0) -> str:
        """
        Generate an appropriate output path for processed video.

        Args:
            input_path (str): Path to input video
            output_dir (str): Output directory
            brightness (int): Brightness adjustment applied
            contrast (int): Contrast adjustment applied

        Returns:
            str: Generated output path
        """
        input_file = Path(input_path)
        filename_base = input_file.stem

        # Create suffix based on adjustments
        suffix_parts = []
        if brightness != 0:
            suffix_parts.append(f"b{brightness:+d}")
        if contrast != 0:
            suffix_parts.append(f"c{contrast:+d}")

        suffix = "_" + "_".join(suffix_parts) if suffix_parts else "_adjusted"

        # Create safe filename
        new_filename = sanitize_filename(f"{filename_base}{suffix}")
        output_path = str(Path(output_dir) / f"{new_filename}{input_file.suffix}")

        # Ensure unique filename
        return get_unique_filename(str(Path(output_path).with_suffix('')), input_file.suffix)

    def check_ffmpeg_availability(self) -> bool:
        """
        Check if FFmpeg is available and working.

        Returns:
            bool: True if FFmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def cleanup(self):
        """Clean up any temporary resources."""
        self.current_preview_frame = None

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
            except:
                pass  # Ignore cleanup errors

    def _parse_ffmpeg_progress(self, output_line: str, total_duration: float) -> Optional[float]:
        """
        Parse FFmpeg progress output to extract completion percentage.

        Args:
            output_line (str): Line from FFmpeg stderr output
            total_duration (float): Total video duration in seconds

        Returns:
            Optional[float]: Progress percentage (0-100) or None if cannot parse
        """
        try:
            # Look for time= pattern in FFmpeg output
            time_match = re.search(r'time=(\d+):(\d+):(\d+)\.(\d+)', output_line)
            if time_match:
                hours = int(time_match.group(1))
                minutes = int(time_match.group(2))
                seconds = int(time_match.group(3))
                centiseconds = int(time_match.group(4))

                current_time = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
                progress = min(100.0, (current_time / total_duration) * 100.0)
                return progress

            return None

        except Exception:
            return None

    def _adjust_frame_brightness_contrast(self, frame: np.ndarray,
                                          brightness: int, contrast: int) -> np.ndarray:
        """
        Apply brightness and contrast adjustments to a single frame using OpenCV.

        Args:
            frame (np.ndarray): Input frame (BGR format)
            brightness (int): Brightness adjustment (-100 to +100)
            contrast (int): Contrast adjustment (-100 to +100)

        Returns:
            np.ndarray: Adjusted frame
        """
        # Convert brightness and contrast to appropriate ranges
        beta = brightness * 2.55  # Brightness adjustment in range [0, 255]
        alpha = 1.0 + (contrast / 100.0)  # Contrast multiplier

        # Clamp values to safe ranges
        alpha = max(0.1, min(3.0, alpha))
        beta = max(-255, min(255, beta))

        # Apply adjustments: new_pixel = alpha * pixel + beta
        adjusted = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

        return adjusted

    def _apply_ffmpeg_adjustments_to_frame(self, input_path: str, brightness: int, contrast: int) -> Optional[np.ndarray]:
        """
        Apply brightness/contrast adjustments to a single frame using FFmpeg.
        
        This method uses the same FFmpeg processing as the final video output.

        Args:
            input_path (str): Path to input image file
            brightness (int): Brightness adjustment (-100 to +100)
            contrast (int): Contrast adjustment (-100 to +100)

        Returns:
            Optional[np.ndarray]: Adjusted frame as numpy array (BGR format) or None if error
        """
        try:
            # Convert brightness and contrast values to match OpenCV preview calculation
            # OpenCV uses: beta = brightness * 2.55, alpha = 1.0 + (contrast / 100.0)
            # FFmpeg eq filter: brightness = beta/255, contrast = alpha
            brightness_value = (brightness * 2.55) / 255.0  # Convert to FFmpeg range
            contrast_value = 1.0 + (contrast / 100.0)  # Same as OpenCV alpha

            # Clamp values to safe ranges
            brightness_value = max(-1.0, min(1.0, brightness_value))
            contrast_value = max(0.1, min(3.0, contrast_value))

            # Build FFmpeg command for single frame processing
            cmd = [
                'ffmpeg', '-y',
                '-i', input_path,
            ]

            # Add video filter if adjustments are needed
            if brightness != 0 or contrast != 0:
                filter_str = f"eq=brightness={brightness_value}:contrast={contrast_value}"
                cmd.extend(['-vf', filter_str])

            # Output to stdout as PNG
            cmd.extend([
                '-f', 'image2pipe',
                '-vcodec', 'png',
                '-'
            ])

            # Execute FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            stdout, stderr = process.communicate()

            if process.returncode == 0 and stdout:
                # Convert PNG data to numpy array
                nparr = np.frombuffer(stdout, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                return frame

            return None

        except Exception as e:
            print(f"Error applying FFmpeg adjustments to frame: {e}")
            return None

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()