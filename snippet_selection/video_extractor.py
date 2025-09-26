"""
Video extraction module for creating snippets around timestamps.

This module handles extracting video snippets from larger videos based on
specific timestamps with configurable before/after durations.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from moviepy.editor import VideoFileClip

import sys
sys.path.append(str(Path(__file__).parent.parent))

from shared.file_utils import sanitize_filename, get_unique_filename, create_output_directory
from shared.video_utils import format_duration


class VideoExtractor:
    """
    Handles extraction of video snippets around specific timestamps.

    Creates video snippets with specified duration before and after
    each timestamp, saving them with descriptive filenames.
    """

    def __init__(self, output_dir: str, before_duration: float, after_duration: float):
        """
        Initialize VideoExtractor.

        Args:
            output_dir (str): Base output directory for snippets
            before_duration (float): Seconds to include before timestamp
            after_duration (float): Seconds to include after timestamp
        """
        self.output_dir = output_dir
        self.before_duration = before_duration
        self.after_duration = after_duration
        self.last_created_snippet_path = ""

    def extract_snippet(self, video_path: str, video_name: str,
                       timestamp_info: Dict[str, Any], video_duration: float) -> bool:
        """
        Extract a snippet from a video around a specific timestamp.

        Args:
            video_path (str): Path to the source video file
            video_name (str): Name of the video (without extension)
            timestamp_info (Dict[str, Any]): Timestamp information from Excel
            video_duration (float): Total duration of the video in seconds

        Returns:
            bool: True if extraction successful, False otherwise
        """
        try:
            timestamp_seconds = timestamp_info['time_seconds']

            # Calculate start and end times for snippet
            start_time = max(0, timestamp_seconds - self.before_duration)
            end_time = min(video_duration, timestamp_seconds + self.after_duration)

            # Skip if the snippet would be too short
            if end_time - start_time < 1.0:
                print(f"Warning: Snippet too short ({end_time - start_time:.1f}s), skipping")
                return False

            # Generate output filename
            timestamp_hhmmss = self._seconds_to_hhmmss(timestamp_seconds)
            arousal_type = timestamp_info.get('arousal_type', '')

            # Create filename with timestamp
            filename_parts = [video_name, timestamp_hhmmss]
            if arousal_type:
                # Sanitize arousal type for filename
                safe_arousal = sanitize_filename(arousal_type)
                filename_parts.append(safe_arousal)

            snippet_filename = "_".join(filename_parts) + Path(video_path).suffix
            snippet_path = os.path.join(self.output_dir, snippet_filename)

            # Ensure filename is unique
            snippet_path = get_unique_filename(
                os.path.join(self.output_dir, Path(snippet_filename).stem),
                Path(snippet_filename).suffix
            )

            print(f"Extracting snippet: {format_duration(start_time)} - {format_duration(end_time)}")
            print(f"Output: {Path(snippet_path).name}")

            # Extract the snippet using MoviePy
            with VideoFileClip(video_path) as video:
                snippet = video.subclip(start_time, end_time)

                # Write the snippet
                snippet.write_videofile(
                    snippet_path,
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )

                snippet.close()

            # Store the path for CSV recording
            self.last_created_snippet_path = snippet_path

            print(f"✓ Created snippet: {Path(snippet_path).name}")
            return True

        except Exception as e:
            print(f"Error extracting snippet at {timestamp_info.get('time', 'unknown')}: {e}")
            return False

    def is_video_already_processed(self, video_name: str) -> bool:
        """
        Check if a video has already been processed by looking for existing snippets.

        Args:
            video_name (str): Name of the video to check

        Returns:
            bool: True if snippets for this video already exist
        """
        try:
            # Look for any files that start with the video name
            output_path = Path(self.output_dir)

            if not output_path.exists():
                return False

            for file_path in output_path.glob(f"{video_name}_*"):
                if file_path.is_file():
                    return True

            return False

        except Exception:
            return False

    def get_last_created_snippet_path(self) -> str:
        """
        Get the path of the last created snippet.

        Returns:
            str: Path to the last created snippet file
        """
        return self.last_created_snippet_path

    def get_snippet_info(self, video_path: str, timestamp_seconds: float,
                        video_duration: float) -> Dict[str, Any]:
        """
        Get information about a snippet without actually creating it.

        Args:
            video_path (str): Path to the source video
            timestamp_seconds (float): Timestamp in seconds
            video_duration (float): Total video duration

        Returns:
            Dict[str, Any]: Information about the potential snippet
        """
        try:
            start_time = max(0, timestamp_seconds - self.before_duration)
            end_time = min(video_duration, timestamp_seconds + self.after_duration)

            return {
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'formatted_start': format_duration(start_time),
                'formatted_end': format_duration(end_time),
                'formatted_duration': format_duration(end_time - start_time),
                'is_valid': end_time - start_time >= 1.0
            }

        except Exception as e:
            return {'error': str(e)}

    def _seconds_to_hhmmss(self, seconds: float) -> str:
        """
        Convert seconds to HHMMSS format for filename.

        Args:
            seconds (float): Time in seconds

        Returns:
            str: Time in HHMMSS format
        """
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)

            return f"{hours:02d}{minutes:02d}{secs:02d}"

        except Exception:
            return "000000"

    def cleanup_failed_snippets(self):
        """
        Clean up any partially created snippet files from failed extractions.
        """
        try:
            output_path = Path(self.output_dir)

            if not output_path.exists():
                return

            # Look for very small video files that might be incomplete
            for file_path in output_path.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.mp4', '.avi', '.mov']:
                    # Check file size - if it's very small, it might be incomplete
                    file_size = file_path.stat().st_size
                    if file_size < 1024:  # Less than 1KB
                        print(f"Removing potentially incomplete file: {file_path.name}")
                        file_path.unlink()

        except Exception as e:
            print(f"Error during cleanup: {e}")

    def set_durations(self, before_duration: float, after_duration: float):
        """
        Update the before and after durations.

        Args:
            before_duration (float): New before duration in seconds
            after_duration (float): New after duration in seconds
        """
        self.before_duration = before_duration
        self.after_duration = after_duration

    def get_durations(self) -> tuple:
        """
        Get the current before and after durations.

        Returns:
            tuple: (before_duration, after_duration) in seconds
        """
        return (self.before_duration, self.after_duration)