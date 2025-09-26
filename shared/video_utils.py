"""
Common video utility functions.

This module provides shared video processing functionality including
duration calculation, validation, and format checking.
"""

import cv2
from pathlib import Path
from typing import Optional, Tuple


def get_video_duration(video_path: str) -> Optional[float]:
    """
    Get the duration of a video file in seconds.

    Args:
        video_path (str): Path to the video file

    Returns:
        Optional[float]: Duration in seconds, or None if unable to read video
    """
    try:
        # Open video file using OpenCV
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return None

        # Get frame count and frame rate
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Release the video capture object
        cap.release()

        # Calculate duration
        if fps > 0:
            duration = frame_count / fps
            return duration
        else:
            return None

    except Exception as e:
        print(f"Error reading video {video_path}: {e}")
        return None


def is_valid_video_file(file_path: str) -> bool:
    """
    Check if a file is a valid video file.

    Args:
        file_path (str): Path to the file to check

    Returns:
        bool: True if file is a valid video, False otherwise
    """
    # Check if file exists
    if not Path(file_path).exists():
        return False

    # Check file extension
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    file_extension = Path(file_path).suffix.lower()

    if file_extension not in valid_extensions:
        return False

    # Try to open with OpenCV to verify it's readable
    try:
        cap = cv2.VideoCapture(file_path)
        is_valid = cap.isOpened()
        cap.release()
        return is_valid
    except:
        return False


def get_video_info(video_path: str) -> Optional[dict]:
    """
    Get comprehensive information about a video file.

    Args:
        video_path (str): Path to the video file

    Returns:
        Optional[dict]: Dictionary with video information, or None if error
    """
    try:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return None

        # Get video properties
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        cap.release()

        # Calculate duration
        duration = frame_count / fps if fps > 0 else 0

        return {
            'path': video_path,
            'duration': duration,
            'frame_count': int(frame_count),
            'fps': fps,
            'width': width,
            'height': height,
            'resolution': f"{width}x{height}"
        }

    except Exception as e:
        print(f"Error getting video info for {video_path}: {e}")
        return None


def format_duration(duration_seconds: float) -> str:
    """
    Format duration from seconds to human-readable format.

    Args:
        duration_seconds (float): Duration in seconds

    Returns:
        str: Formatted duration as "HH:MM:SS"
    """
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    seconds = int(duration_seconds % 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def calculate_chunks(total_duration: float, chunk_duration: float) -> int:
    """
    Calculate the number of chunks a video will be split into.

    Args:
        total_duration (float): Total video duration in seconds
        chunk_duration (float): Desired chunk duration in seconds

    Returns:
        int: Number of chunks that will be created
    """
    import math
    return math.ceil(total_duration / chunk_duration)