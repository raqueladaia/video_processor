"""
File management module for finding and matching video files.

This module handles discovering video files in directories (including subdirectories)
and matching them with timestamp data from Excel files.
"""

import os
from pathlib import Path
from typing import Dict, List, Set
import difflib

import sys
sys.path.append(str(Path(__file__).parent.parent))

from shared.file_utils import find_video_files
from shared.video_utils import is_valid_video_file


class FileManager:
    """
    Manages file discovery and matching for video processing.

    Handles finding video files in directory structures and matching
    them with video names from Excel timestamp data.
    """

    def __init__(self, input_directory: str):
        """
        Initialize FileManager.

        Args:
            input_directory (str): Root directory to search for video files
        """
        self.input_directory = input_directory
        self.found_videos = []
        self.video_cache = {}

    def find_all_videos(self) -> List[str]:
        """
        Find all video files in the input directory and subdirectories.

        Returns:
            List[str]: List of paths to video files found
        """
        try:
            print(f"Searching for videos in: {self.input_directory}")

            # Use shared utility to find video files
            self.found_videos = find_video_files(self.input_directory, recursive=True)

            # Validate each video file
            valid_videos = []
            for video_path in self.found_videos:
                if is_valid_video_file(video_path):
                    valid_videos.append(video_path)
                else:
                    print(f"Warning: Invalid video file skipped: {Path(video_path).name}")

            self.found_videos = valid_videos

            # Create cache for quick lookups
            self._build_video_cache()

            print(f"Found {len(self.found_videos)} valid video file(s)")

            return self.found_videos

        except Exception as e:
            print(f"Error finding video files: {e}")
            return []

    def match_videos_with_timestamps(self, timestamp_data: Dict[str, List],
                                   found_videos: List[str] = None) -> Dict[str, str]:
        """
        Match video names from timestamp data with actual video files.

        Args:
            timestamp_data (Dict[str, List]): Timestamp data keyed by video name
            found_videos (List[str], optional): List of found video files

        Returns:
            Dict[str, str]: Dictionary mapping video names to file paths
        """
        if found_videos is None:
            found_videos = self.found_videos

        matches = {}

        try:
            # Create a mapping of video names (without extensions) to full paths
            video_name_to_path = {}
            for video_path in found_videos:
                video_name = Path(video_path).stem
                video_name_to_path[video_name.lower()] = video_path

            # Try to match each video name from timestamp data
            for excel_video_name in timestamp_data.keys():
                excel_name_lower = excel_video_name.lower()

                # Direct match first
                if excel_name_lower in video_name_to_path:
                    matches[excel_video_name] = video_name_to_path[excel_name_lower]
                    continue

                # Try fuzzy matching for close names
                best_match = self._find_best_match(excel_video_name, list(video_name_to_path.keys()))

                if best_match:
                    print(f"Fuzzy match: '{excel_video_name}' -> '{best_match}'")
                    matches[excel_video_name] = video_name_to_path[best_match]

            print(f"Successfully matched {len(matches)} video(s)")

            return matches

        except Exception as e:
            print(f"Error matching videos with timestamps: {e}")
            return {}

    def get_missing_videos(self, timestamp_data: Dict[str, List],
                          found_videos: List[str] = None) -> List[str]:
        """
        Get list of video names that have timestamp data but no matching video file.

        Args:
            timestamp_data (Dict[str, List]): Timestamp data keyed by video name
            found_videos (List[str], optional): List of found video files

        Returns:
            List[str]: List of video names that couldn't be matched
        """
        if found_videos is None:
            found_videos = self.found_videos

        matches = self.match_videos_with_timestamps(timestamp_data, found_videos)
        missing = [video_name for video_name in timestamp_data.keys()
                  if video_name not in matches]

        return missing

    def get_video_statistics(self) -> Dict[str, int]:
        """
        Get statistics about found video files.

        Returns:
            Dict[str, int]: Statistics including file counts by extension
        """
        try:
            stats = {
                'total_videos': len(self.found_videos),
                'extensions': {}
            }

            for video_path in self.found_videos:
                ext = Path(video_path).suffix.lower()
                if ext in stats['extensions']:
                    stats['extensions'][ext] += 1
                else:
                    stats['extensions'][ext] = 1

            return stats

        except Exception as e:
            print(f"Error getting video statistics: {e}")
            return {'total_videos': 0, 'extensions': {}}

    def _build_video_cache(self):
        """Build a cache for quick video file lookups."""
        self.video_cache = {}

        for video_path in self.found_videos:
            video_name = Path(video_path).stem
            self.video_cache[video_name.lower()] = video_path

    def _find_best_match(self, target_name: str, candidate_names: List[str],
                        threshold: float = 0.6) -> str:
        """
        Find the best matching video name using fuzzy matching.

        Args:
            target_name (str): Name to match
            candidate_names (List[str]): List of candidate names
            threshold (float): Minimum similarity threshold (0.0-1.0)

        Returns:
            str: Best matching name, or empty string if no good match
        """
        try:
            target_lower = target_name.lower()

            # Get similarity scores for all candidates
            matches = difflib.get_close_matches(
                target_lower,
                candidate_names,
                n=1,
                cutoff=threshold
            )

            return matches[0] if matches else ""

        except Exception:
            return ""

    def validate_input_directory(self) -> bool:
        """
        Validate that the input directory exists and is accessible.

        Returns:
            bool: True if directory is valid, False otherwise
        """
        try:
            input_path = Path(self.input_directory)
            return input_path.exists() and input_path.is_dir()

        except Exception:
            return False

    def get_directory_info(self) -> Dict[str, any]:
        """
        Get information about the input directory.

        Returns:
            Dict[str, any]: Directory information
        """
        try:
            input_path = Path(self.input_directory)

            if not input_path.exists():
                return {'exists': False}

            # Count subdirectories
            subdirs = [p for p in input_path.iterdir() if p.is_dir()]

            # Count all files
            all_files = [p for p in input_path.rglob('*') if p.is_file()]

            return {
                'exists': True,
                'path': str(input_path.absolute()),
                'subdirectory_count': len(subdirs),
                'total_file_count': len(all_files),
                'video_file_count': len(self.found_videos)
            }

        except Exception as e:
            return {'exists': False, 'error': str(e)}