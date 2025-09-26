"""
Video Processor Module for Crop Video Tool

This module handles video cropping operations using FFmpeg for fast, high-quality
processing. It supports multi-region cropping and batch processing with organized
output directory structure.

Author: Video Processing Project
"""

import os
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple
import sys

# Add parent directory to path for shared module imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.file_utils import create_output_directory, sanitize_filename, find_video_files
from shared.video_utils import get_video_info, is_valid_video_file

try:
    from .rectangle_manager import Rectangle, RectangleManager
except ImportError:
    from rectangle_manager import Rectangle, RectangleManager


class CropVideoProcessor:
    """
    Handles video cropping operations using FFmpeg for multiple crop regions
    with batch processing capabilities and organized output structure.
    """

    def __init__(self):
        """Initialize the video processor."""
        self.temp_dir = None

    def crop_single_video(self, video_path: str, rectangles: List[Rectangle],
                         output_base_dir: str,
                         progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, bool]:
        """
        Crop a single video into multiple regions using FFmpeg.

        Args:
            video_path (str): Path to input video file
            rectangles (List[Rectangle]): List of crop rectangles
            output_base_dir (str): Base directory for output folders
            progress_callback (Optional[Callable[[str, float], None]]): Progress callback

        Returns:
            Dict[str, bool]: Success status for each crop region (region_name -> success)
        """
        results = {}

        if not rectangles:
            return results

        # Validate input video
        if not is_valid_video_file(video_path):
            print(f"Error: Invalid video file: {video_path}")
            return results

        # Get video info for progress calculation
        video_info = get_video_info(video_path)
        if not video_info:
            print(f"Error: Could not get video information: {video_path}")
            return results

        video_duration = video_info['duration']
        input_file = Path(video_path)

        # Process each crop region
        for i, rectangle in enumerate(rectangles):
            if progress_callback:
                overall_progress = (i / len(rectangles)) * 100
                progress_callback(f"Processing region '{rectangle.name}'", overall_progress)

            # Create output directory for this region
            region_dir = Path(output_base_dir) / sanitize_filename(rectangle.name)
            if not create_output_directory(str(region_dir)):
                print(f"Error: Could not create output directory: {region_dir}")
                results[rectangle.name] = False
                continue

            # Generate output filename
            output_filename = f"{input_file.stem}_{rectangle.name}{input_file.suffix}"
            output_path = region_dir / output_filename

            # Crop the video
            success = self._crop_video_region(
                video_path, rectangle, str(output_path), video_duration,
                lambda p: progress_callback(f"Processing region '{rectangle.name}'",
                                          (i / len(rectangles)) * 100 + p / len(rectangles)) if progress_callback else None
            )

            results[rectangle.name] = success

        if progress_callback:
            progress_callback("Processing complete", 100.0)

        return results

    def crop_video_batch(self, video_paths: List[str], rectangles: List[Rectangle],
                        output_base_dir: str,
                        progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Dict[str, bool]]:
        """
        Crop multiple videos with the same set of rectangles.

        Args:
            video_paths (List[str]): List of video file paths
            rectangles (List[Rectangle]): List of crop rectangles
            output_base_dir (str): Base directory for output folders
            progress_callback (Optional[Callable[[str, float], None]]): Progress callback

        Returns:
            Dict[str, Dict[str, bool]]: Results nested by video_path -> region_name -> success
        """
        results = {}
        total_videos = len(video_paths)

        for video_idx, video_path in enumerate(video_paths):
            video_name = Path(video_path).name

            if progress_callback:
                video_progress = (video_idx / total_videos) * 100
                progress_callback(f"Processing video {video_idx + 1}/{total_videos}: {video_name}", video_progress)

            # Process single video
            video_results = self.crop_single_video(
                video_path, rectangles, output_base_dir,
                lambda region_msg, region_progress: progress_callback(
                    f"Video {video_idx + 1}/{total_videos}: {region_msg}",
                    video_progress + (region_progress / total_videos)
                ) if progress_callback else None
            )

            results[video_path] = video_results

        return results

    def crop_directory(self, input_dir: str, rectangles: List[Rectangle],
                      output_base_dir: str,
                      progress_callback: Optional[Callable[[str, float], None]] = None) -> Dict[str, Dict[str, bool]]:
        """
        Crop all videos in a directory with the same set of rectangles.

        Args:
            input_dir (str): Directory containing videos
            rectangles (List[Rectangle]): List of crop rectangles
            output_base_dir (str): Base directory for output folders
            progress_callback (Optional[Callable[[str, float], None]]): Progress callback

        Returns:
            Dict[str, Dict[str, bool]]: Results nested by video_path -> region_name -> success
        """
        # Find all video files
        video_files = find_video_files(input_dir, recursive=True)

        if not video_files:
            if progress_callback:
                progress_callback("No video files found in directory", 0)
            return {}

        if progress_callback:
            progress_callback(f"Found {len(video_files)} video files", 0)

        # Process batch
        return self.crop_video_batch(video_files, rectangles, output_base_dir, progress_callback)

    def validate_crop_rectangles(self, rectangles: List[Rectangle], video_width: int, video_height: int) -> List[str]:
        """
        Validate crop rectangles against video dimensions.

        Args:
            rectangles (List[Rectangle]): Rectangles to validate
            video_width (int): Video width in pixels
            video_height (int): Video height in pixels

        Returns:
            List[str]: List of validation error messages
        """
        errors = []

        for rect in rectangles:
            # Check if rectangle is within bounds
            if rect.x < 0 or rect.y < 0:
                errors.append(f"Rectangle '{rect.name}' has negative coordinates")

            if rect.x + rect.width > video_width:
                errors.append(f"Rectangle '{rect.name}' extends beyond video width")

            if rect.y + rect.height > video_height:
                errors.append(f"Rectangle '{rect.name}' extends beyond video height")

            # Check minimum size
            if rect.width < 10 or rect.height < 10:
                errors.append(f"Rectangle '{rect.name}' is too small (minimum 10x10 pixels)")

            # Check for valid name
            if not rect.name or not rect.name.strip():
                errors.append(f"Rectangle at ({rect.x}, {rect.y}) has no name")

        return errors

    def get_output_directory_structure(self, rectangles: List[Rectangle], output_base_dir: str) -> Dict[str, str]:
        """
        Get the directory structure that will be created for output.

        Args:
            rectangles (List[Rectangle]): List of crop rectangles
            output_base_dir (str): Base output directory

        Returns:
            Dict[str, str]: Mapping of region names to their output directories
        """
        structure = {}
        base_path = Path(output_base_dir)

        for rect in rectangles:
            safe_name = sanitize_filename(rect.name)
            region_dir = base_path / safe_name
            structure[rect.name] = str(region_dir)

        return structure

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

    def _crop_video_region(self, input_path: str, rectangle: Rectangle, output_path: str,
                          total_duration: float,
                          progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Crop a single region from a video using FFmpeg with stream copy optimization.

        Args:
            input_path (str): Input video path
            rectangle (Rectangle): Crop rectangle
            output_path (str): Output video path
            total_duration (float): Total video duration for progress calculation
            progress_callback (Optional[Callable[[float], None]]): Progress callback

        Returns:
            bool: True if cropping was successful
        """
        try:
            # Try stream copy first (much faster)
            success = self._crop_video_region_stream_copy(input_path, rectangle, output_path, total_duration, progress_callback)
            
            if success:
                print(f"Successfully cropped region '{rectangle.name}' with stream copy: {output_path}")
                return True
            else:
                # Stream copy failed, try with fast re-encoding
                print(f"Stream copy failed for '{rectangle.name}', falling back to fast re-encoding...")
                return self._crop_video_region_fast_reencoding(input_path, rectangle, output_path, total_duration, progress_callback)

        except Exception as e:
            print(f"Error cropping video region '{rectangle.name}': {e}")
            return False

    def _crop_video_region_stream_copy(self, input_path: str, rectangle: Rectangle, output_path: str,
                                      total_duration: float,
                                      progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Crop a single region from a video using FFmpeg stream copy (fastest method).

        Args:
            input_path (str): Input video path
            rectangle (Rectangle): Crop rectangle
            output_path (str): Output video path
            total_duration (float): Total video duration for progress calculation
            progress_callback (Optional[Callable[[float], None]]): Progress callback

        Returns:
            bool: True if cropping was successful
        """
        try:
            # Build FFmpeg command for stream copy
            cmd = [
                'ffmpeg', '-y',  # -y to overwrite output files
                '-i', input_path,
            ]

            # Add crop filter
            crop_filter = rectangle.get_ffmpeg_crop_filter()
            cmd.extend(['-vf', crop_filter])

            # Use stream copy (no re-encoding)
            cmd.extend([
                '-c', 'copy',  # Copy video stream without re-encoding
                output_path
            ])

            # Execute FFmpeg
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            if process.returncode == 0:
                return True
            else:
                # Log the error for debugging
                print(f"Stream copy failed for '{rectangle.name}': {process.stderr}")
                return False

        except Exception as e:
            print(f"Error with stream copy cropping for '{rectangle.name}': {e}")
            return False

    def _crop_video_region_fast_reencoding(self, input_path: str, rectangle: Rectangle, output_path: str,
                                          total_duration: float,
                                          progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Crop a single region from a video using FFmpeg with fast re-encoding (fallback method).

        Args:
            input_path (str): Input video path
            rectangle (Rectangle): Crop rectangle
            output_path (str): Output video path
            total_duration (float): Total video duration for progress calculation
            progress_callback (Optional[Callable[[float], None]]): Progress callback

        Returns:
            bool: True if cropping was successful
        """
        try:
            # Build FFmpeg command for fast re-encoding
            cmd = [
                'ffmpeg', '-y',  # -y to overwrite output files
                '-i', input_path,
            ]

            # Add crop filter
            crop_filter = rectangle.get_ffmpeg_crop_filter()
            cmd.extend(['-vf', crop_filter])

            # Use fast encoding settings
            cmd.extend([
                '-c:v', 'libx264',  # Use H.264 codec
                '-preset', 'fast',  # Faster than 'medium'
                '-crf', '23',       # Good quality, faster than 18
                output_path
            ])

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
                print(f"Successfully cropped region '{rectangle.name}' with fast re-encoding: {output_path}")
                return True
            else:
                stderr_output = process.stderr.read() if process.stderr else "Unknown error"
                print(f"FFmpeg error cropping '{rectangle.name}': {stderr_output}")
                return False

        except Exception as e:
            print(f"Error with fast re-encoding cropping for '{rectangle.name}': {e}")
            return False

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

    def cleanup(self):
        """Clean up any temporary resources."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
            except:
                pass  # Ignore cleanup errors

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()