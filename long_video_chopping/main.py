"""
Main entry point for long video chopping program.

This program segments a given video into smaller consecutive videos based on
user-specified chunk duration. It handles both single video files and folders
containing multiple videos.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path to import shared modules
sys.path.append(str(Path(__file__).parent.parent))

from shared.user_interface import (
    get_file_path, get_directory_path, get_positive_number,
    get_yes_no_choice, print_section_header, print_file_info,
    get_choice_from_list
)
from shared.file_utils import find_video_files, validate_input_path
from shared.video_utils import get_video_info, format_duration, calculate_chunks
try:
    from .video_processor import VideoProcessor
except ImportError:
    from video_processor import VideoProcessor


def main():
    """Main function for long video chopping program."""
    print_section_header("Long Video Chopping Tool")
    print("This tool segments videos into smaller consecutive chunks.")
    print("Original videos are never modified - only copies are created.\n")

    try:
        # Get input (video file or folder)
        input_choice = get_choice_from_list(
            "What would you like to process?",
            ["Single video file", "Folder containing videos"]
        )

        video_files = []

        if input_choice == "Single video file":
            # Get single video file
            video_file = get_file_path("Enter path to video file: ")
            video_files = [video_file]
        else:
            # Get folder containing videos
            input_folder = get_directory_path("Enter path to folder containing videos: ")
            print("\nSearching for video files...")
            video_files = find_video_files(input_folder, recursive=True)

            if not video_files:
                print("No video files found in the specified folder.")
                return

            print(f"Found {len(video_files)} video file(s):")
            for i, file_path in enumerate(video_files, 1):
                print(f"{i}. {Path(file_path).name}")

            if not get_yes_no_choice("\nProceed with these files?", default=True):
                return

        # Get chunk duration
        print("\nChunk duration settings:")
        duration_seconds = get_positive_number(
            "Enter desired chunk duration in seconds: ",
            number_type=float
        )

        # Get output directory
        output_dir = get_directory_path(
            "Enter output directory (where chunked videos will be saved): ",
            must_exist=False
        )

        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Process each video file
        processor = VideoProcessor(output_dir)

        print_section_header("Processing Videos")

        for i, video_file in enumerate(video_files, 1):
            print(f"\nProcessing video {i}/{len(video_files)}")

            # Get video information
            video_info = get_video_info(video_file)
            if not video_info:
                print(f"Error: Could not read video file {video_file}")
                continue

            # Display video information
            print_file_info(
                video_file,
                duration=video_info['duration']
            )

            # Calculate number of chunks
            num_chunks = calculate_chunks(video_info['duration'], duration_seconds)
            print(f"Will create {num_chunks} chunk(s) of {duration_seconds} seconds each")

            if video_info['duration'] > duration_seconds:
                # Confirm processing for this video
                if len(video_files) > 1:
                    if not get_yes_no_choice(f"Process this video?", default=True):
                        print(f"Skipping {Path(video_file).name}")
                        continue

                # Process the video
                success = processor.split_video(video_file, duration_seconds)

                if success:
                    print(f"✓ Successfully processed {Path(video_file).name}")
                else:
                    print(f"✗ Failed to process {Path(video_file).name}")
            else:
                print(f"Video is shorter than chunk duration. Copying as single chunk...")
                success = processor.copy_video_as_chunk(video_file)

                if success:
                    print(f"✓ Successfully copied {Path(video_file).name}")
                else:
                    print(f"✗ Failed to copy {Path(video_file).name}")

        print_section_header("Processing Complete")
        print(f"All videos have been processed. Output saved to: {output_dir}")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your input and try again.")


if __name__ == "__main__":
    main()