"""
Video metadata extraction module.

This module provides functionality to extract comprehensive metadata from video files
including frame rates, duration, resolution, codecs, and file properties.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
import cv2

import sys
sys.path.append(str(Path(__file__).parent.parent))

from shared.file_utils import get_file_size_mb


class VideoMetadataExtractor:
    """
    Extracts comprehensive metadata from video files.

    Uses OpenCV and FFprobe to gather detailed information about video properties,
    codecs, frame rates, and file characteristics.
    """

    def __init__(self):
        """Initialize VideoMetadataExtractor."""
        self.ffprobe_available = self._check_ffprobe()

    def _check_ffprobe(self) -> bool:
        """
        Check if FFprobe is available on the system.

        Returns:
            bool: True if FFprobe is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def extract_metadata(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract all metadata from a video file.

        Args:
            video_path (str): Path to the video file

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing all metadata, or None if extraction fails
        """
        if not os.path.exists(video_path):
            print(f"Error: Video file not found: {video_path}")
            return None

        metadata = {}

        # Get basic metadata using OpenCV
        opencv_metadata = self._extract_opencv_metadata(video_path)
        if opencv_metadata:
            metadata.update(opencv_metadata)
        else:
            print(f"Warning: Could not extract metadata using OpenCV for {video_path}")
            return None

        # Get additional metadata using FFprobe if available
        if self.ffprobe_available:
            ffprobe_metadata = self._extract_ffprobe_metadata(video_path)
            if ffprobe_metadata:
                metadata.update(ffprobe_metadata)

        # Get file properties
        file_metadata = self._extract_file_metadata(video_path)
        metadata.update(file_metadata)

        # Calculate actual frame rate (verify against recorded)
        metadata['actual_fps'] = self._calculate_actual_fps(metadata)

        return metadata

    def _extract_opencv_metadata(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata using OpenCV.

        Args:
            video_path (str): Path to the video file

        Returns:
            Optional[Dict[str, Any]]: Metadata dictionary or None if extraction fails
        """
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                return None

            # Extract all available properties
            metadata = {
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fourcc': int(cap.get(cv2.CAP_PROP_FOURCC)),
            }

            # Calculate duration
            if metadata['fps'] > 0:
                metadata['duration'] = metadata['frame_count'] / metadata['fps']
            else:
                metadata['duration'] = 0.0

            # Calculate resolution string
            metadata['resolution'] = f"{metadata['width']}x{metadata['height']}"

            # Calculate aspect ratio
            if metadata['height'] > 0:
                aspect_ratio = metadata['width'] / metadata['height']
                metadata['aspect_ratio'] = f"{aspect_ratio:.2f}:1"
            else:
                metadata['aspect_ratio'] = "Unknown"

            # Convert FOURCC to codec string
            metadata['video_codec_fourcc'] = self._fourcc_to_string(metadata['fourcc'])

            cap.release()

            return metadata

        except Exception as e:
            print(f"Error extracting OpenCV metadata: {e}")
            return None

    def _extract_ffprobe_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract additional metadata using FFprobe.

        Args:
            video_path (str): Path to the video file

        Returns:
            Dict[str, Any]: Additional metadata from FFprobe
        """
        metadata = {}

        try:
            # Run FFprobe to get JSON output
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                data = json.loads(result.stdout)

                # Extract format information
                if 'format' in data:
                    format_info = data['format']
                    metadata['format_name'] = format_info.get('format_name', 'Unknown')
                    metadata['format_long_name'] = format_info.get('format_long_name', 'Unknown')
                    metadata['bitrate'] = int(format_info.get('bit_rate', 0))
                    metadata['ffprobe_duration'] = float(format_info.get('duration', 0))

                # Extract video stream information
                if 'streams' in data:
                    for stream in data['streams']:
                        if stream.get('codec_type') == 'video':
                            metadata['video_codec'] = stream.get('codec_name', 'Unknown')
                            metadata['video_codec_long'] = stream.get('codec_long_name', 'Unknown')
                            metadata['pix_fmt'] = stream.get('pix_fmt', 'Unknown')

                            # Get frame rate from stream
                            r_frame_rate = stream.get('r_frame_rate', '0/0')
                            if '/' in r_frame_rate:
                                num, den = r_frame_rate.split('/')
                                if int(den) > 0:
                                    metadata['stream_fps'] = int(num) / int(den)

                        elif stream.get('codec_type') == 'audio':
                            metadata['audio_codec'] = stream.get('codec_name', 'None')
                            metadata['audio_codec_long'] = stream.get('codec_long_name', 'None')
                            metadata['sample_rate'] = stream.get('sample_rate', 'N/A')
                            metadata['channels'] = stream.get('channels', 'N/A')

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"Warning: FFprobe extraction failed: {e}")

        return metadata

    def _extract_file_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract file system metadata.

        Args:
            video_path (str): Path to the video file

        Returns:
            Dict[str, Any]: File metadata
        """
        metadata = {}

        try:
            path_obj = Path(video_path)

            metadata['filename'] = path_obj.name
            metadata['file_extension'] = path_obj.suffix
            metadata['file_path'] = str(path_obj.absolute())

            # Get file size
            size_mb = get_file_size_mb(video_path)
            if size_mb:
                metadata['file_size_mb'] = size_mb
                metadata['file_size_gb'] = size_mb / 1024

                # Format file size for human readability
                if size_mb < 1024:
                    metadata['file_size_formatted'] = f"{size_mb:.2f} MB"
                else:
                    metadata['file_size_formatted'] = f"{size_mb/1024:.2f} GB"
            else:
                metadata['file_size_mb'] = 0
                metadata['file_size_gb'] = 0
                metadata['file_size_formatted'] = "Unknown"

        except Exception as e:
            print(f"Error extracting file metadata: {e}")

        return metadata

    def _calculate_actual_fps(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate actual FPS from frame count and duration.

        This verifies the recorded FPS by calculating from actual frame count.

        Args:
            metadata (Dict[str, Any]): Existing metadata

        Returns:
            float: Calculated actual FPS
        """
        try:
            frame_count = metadata.get('frame_count', 0)
            duration = metadata.get('duration', 0)

            if duration > 0 and frame_count > 0:
                return frame_count / duration
            else:
                return 0.0

        except Exception:
            return 0.0

    def _fourcc_to_string(self, fourcc: int) -> str:
        """
        Convert FOURCC integer code to string representation.

        Args:
            fourcc (int): FOURCC code as integer

        Returns:
            str: FOURCC as string (e.g., 'H264', 'MJPG')
        """
        try:
            # Convert integer to 4-character string
            fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            return fourcc_str.strip()
        except Exception:
            return "Unknown"

    def format_metadata_for_display(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Format metadata values for human-readable display.

        Args:
            metadata (Dict[str, Any]): Raw metadata

        Returns:
            Dict[str, str]: Formatted metadata for display
        """
        formatted = {}

        # Format duration
        if 'duration' in metadata:
            duration = metadata['duration']
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            formatted['duration'] = f"{hours:02d}:{minutes:02d}:{seconds:02d} ({duration:.2f}s)"

        # Format FPS
        if 'fps' in metadata:
            formatted['recording_fps'] = f"{metadata['fps']:.2f}"
        if 'actual_fps' in metadata:
            formatted['actual_fps'] = f"{metadata['actual_fps']:.2f}"

        # Format frame count
        if 'frame_count' in metadata:
            formatted['frame_count'] = f"{metadata['frame_count']:,}"

        # Format resolution
        if 'resolution' in metadata:
            formatted['resolution'] = metadata['resolution']

        # Format file size
        if 'file_size_formatted' in metadata:
            formatted['file_size'] = metadata['file_size_formatted']

        # Format bitrate
        if 'bitrate' in metadata and metadata['bitrate'] > 0:
            bitrate_mbps = metadata['bitrate'] / 1_000_000
            formatted['bitrate'] = f"{bitrate_mbps:.2f} Mbps"

        # Add codec information
        if 'video_codec' in metadata:
            formatted['video_codec'] = metadata['video_codec']
        elif 'video_codec_fourcc' in metadata:
            formatted['video_codec'] = metadata['video_codec_fourcc']

        if 'audio_codec' in metadata:
            formatted['audio_codec'] = metadata['audio_codec']

        return formatted
