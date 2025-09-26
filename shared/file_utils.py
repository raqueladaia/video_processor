"""
Common file handling utilities.

This module provides shared file and directory operations including
path validation, directory creation, and file discovery.
"""

import os
from pathlib import Path
from typing import List, Optional, Generator


def validate_input_path(path: str) -> bool:
    """
    Validate that an input path exists and is accessible.

    Args:
        path (str): Path to validate

    Returns:
        bool: True if path exists and is accessible, False otherwise
    """
    try:
        path_obj = Path(path)
        return path_obj.exists()
    except Exception:
        return False


def create_output_directory(directory_path: str) -> bool:
    """
    Create an output directory if it doesn't exist.

    Args:
        directory_path (str): Path to the directory to create

    Returns:
        bool: True if directory was created or already exists, False on error
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False


def find_video_files(directory: str, recursive: bool = True) -> List[str]:
    """
    Find all video files in a directory.

    Args:
        directory (str): Directory to search in
        recursive (bool): Whether to search subdirectories

    Returns:
        List[str]: List of paths to video files found
    """
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    video_files = []

    try:
        directory_path = Path(directory)

        if not directory_path.exists():
            return video_files

        # Use glob pattern based on recursive parameter
        pattern = "**/*" if recursive else "*"

        for file_path in directory_path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                video_files.append(str(file_path))

    except Exception as e:
        print(f"Error searching for video files in {directory}: {e}")

    return sorted(video_files)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.

    Args:
        filename (str): Original filename

    Returns:
        str: Sanitized filename safe for use on filesystem
    """
    # Characters that are invalid in filenames on Windows/Linux
    invalid_chars = '<>:"/\\|?*'

    # Replace invalid characters with underscore
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')

    # Remove any leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')

    # Ensure filename is not empty
    if not sanitized:
        sanitized = "unnamed_file"

    return sanitized


def get_unique_filename(base_path: str, extension: str = "") -> str:
    """
    Generate a unique filename by adding a number suffix if file exists.

    Args:
        base_path (str): Base path without extension
        extension (str): File extension (optional)

    Returns:
        str: Unique filename that doesn't exist on filesystem
    """
    counter = 1
    original_path = f"{base_path}{extension}"

    # If file doesn't exist, return original path
    if not Path(original_path).exists():
        return original_path

    # Find a unique name by adding numbers
    while True:
        new_path = f"{base_path}_{counter}{extension}"
        if not Path(new_path).exists():
            return new_path
        counter += 1


def get_file_size_mb(file_path: str) -> Optional[float]:
    """
    Get file size in megabytes.

    Args:
        file_path (str): Path to the file

    Returns:
        Optional[float]: File size in MB, or None if error
    """
    try:
        size_bytes = Path(file_path).stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except Exception:
        return None


def ensure_output_dir_structure(base_dir: str, video_name: str) -> str:
    """
    Create and return output directory structure for a video.

    Args:
        base_dir (str): Base output directory
        video_name (str): Name of the video (used for subdirectory)

    Returns:
        str: Path to the created output directory
    """
    # Sanitize video name for use as directory name
    safe_video_name = sanitize_filename(Path(video_name).stem)

    # Create output directory path
    output_dir = Path(base_dir) / safe_video_name

    # Create the directory
    create_output_directory(str(output_dir))

    return str(output_dir)