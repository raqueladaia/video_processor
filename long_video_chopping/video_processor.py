"""
Video processing module for segmenting videos into chunks.

This module handles the core video segmentation functionality using OpenCV
and MoviePy for accurate video cutting and file management.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
import cv2
from moviepy import VideoFileClip

import sys
sys.path.append(str(Path(__file__).parent.parent))

from shared.file_utils import (
    ensure_output_dir_structure, sanitize_filename,
    get_unique_filename
)
from shared.video_utils import get_video_duration, format_duration


class VideoProcessor:
    """
    Handles video segmentation and chunk creation.

    This class provides methods to split videos into smaller chunks while
    ensuring original files are never modified.
    """

    def __init__(self, output_base_dir: str):
        """
        Initialize VideoProcessor.

        Args:
            output_base_dir (str): Base directory where output files will be saved
        """
        self.output_base_dir = output_base_dir

    def split_video(self, video_path: str, chunk_duration: float) -> bool:
        """
        Split a video into chunks of specified duration.

        Args:
            video_path (str): Path to the input video file
            chunk_duration (float): Duration of each chunk in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Starting to process: {Path(video_path).name}")

            # Get video information
            total_duration = get_video_duration(video_path)
            if not total_duration:
                print(f"Error: Could not get duration for {video_path}")
                return False

            # Create output directory for this video
            video_name = Path(video_path).stem
            output_dir = ensure_output_dir_structure(self.output_base_dir, video_name)

            print(f"Output directory: {output_dir}")
            print(f"Total duration: {format_duration(total_duration)}")
            print(f"Chunk duration: {format_duration(chunk_duration)}")

            # Use MoviePy for more accurate video cutting
            with VideoFileClip(video_path) as video:
                current_time = 0
                chunk_number = 1

                while current_time < total_duration:
                    # Calculate end time for this chunk
                    end_time = min(current_time + chunk_duration, total_duration)

                    # Generate output filename
                    chunk_filename = f"{video_name}_{chunk_number:03d}{Path(video_path).suffix}"
                    chunk_path = os.path.join(output_dir, chunk_filename)

                    # Make sure filename is unique
                    chunk_path = get_unique_filename(
                        os.path.join(output_dir, Path(chunk_filename).stem),
                        Path(chunk_filename).suffix
                    )

                    print(f"Creating chunk {chunk_number}: {format_duration(current_time)} - {format_duration(end_time)}")

                    try:
                        # Extract the chunk
                        chunk = video.subclip(current_time, end_time)

                        # Write the chunk to file
                        chunk.write_videofile(
                            chunk_path,
                            audio_codec='aac',
                            verbose=False,
                            logger=None
                        )

                        chunk.close()

                        print(f"✓ Created: {Path(chunk_path).name}")

                    except Exception as e:
                        print(f"✗ Error creating chunk {chunk_number}: {e}")
                        continue

                    # Move to next chunk
                    current_time = end_time
                    chunk_number += 1

            print(f"Successfully created {chunk_number - 1} chunks")
            return True

        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            return False

    def copy_video_as_chunk(self, video_path: str) -> bool:
        """
        Copy a video as a single chunk (for videos shorter than chunk duration).

        Args:
            video_path (str): Path to the input video file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create output directory for this video
            video_name = Path(video_path).stem
            output_dir = ensure_output_dir_structure(self.output_base_dir, video_name)

            # Generate output filename
            chunk_filename = f"{video_name}_001{Path(video_path).suffix}"
            chunk_path = os.path.join(output_dir, chunk_filename)

            # Make sure filename is unique
            chunk_path = get_unique_filename(
                os.path.join(output_dir, Path(chunk_filename).stem),
                Path(chunk_filename).suffix
            )

            # Copy the file
            shutil.copy2(video_path, chunk_path)

            print(f"✓ Copied as single chunk: {Path(chunk_path).name}")
            return True

        except Exception as e:
            print(f"Error copying video {video_path}: {e}")
            return False

    def get_chunk_info(self, video_path: str, chunk_duration: float) -> dict:
        """
        Get information about how a video would be chunked without actually processing it.

        Args:
            video_path (str): Path to the input video file
            chunk_duration (float): Duration of each chunk in seconds

        Returns:
            dict: Information about the chunking process
        """
        try:
            total_duration = get_video_duration(video_path)
            if not total_duration:
                return {"error": "Could not read video duration"}

            # Calculate number of chunks
            import math
            num_chunks = math.ceil(total_duration / chunk_duration)

            # Calculate the duration of the last chunk
            last_chunk_duration = total_duration - ((num_chunks - 1) * chunk_duration)

            return {
                "total_duration": total_duration,
                "chunk_duration": chunk_duration,
                "num_chunks": num_chunks,
                "last_chunk_duration": last_chunk_duration,
                "formatted_total_duration": format_duration(total_duration),
                "formatted_chunk_duration": format_duration(chunk_duration),
                "formatted_last_chunk_duration": format_duration(last_chunk_duration)
            }

        except Exception as e:
            return {"error": str(e)}