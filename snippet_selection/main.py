"""
Main entry point for snippet selection program.

This program extracts video snippets around specific times of interest based on
an Excel file containing timestamps and metadata. It searches for videos in
input folders (including subfolders) and creates snippets with configurable
duration before and after each timestamp.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path to import shared modules
sys.path.append(str(Path(__file__).parent.parent))

from shared.user_interface import (
    get_file_path, get_directory_path, get_positive_number,
    get_yes_no_choice, print_section_header, print_file_info,
    get_choice_from_list, print_progress
)
from shared.file_utils import find_video_files, validate_input_path, create_output_directory
from shared.video_utils import get_video_info, format_duration

try:
    from .excel_parser import ExcelParser
    from .video_extractor import VideoExtractor
    from .csv_manager import CSVManager
    from .file_manager import FileManager
except ImportError:
    from excel_parser import ExcelParser
    from video_extractor import VideoExtractor
    from csv_manager import CSVManager
    from file_manager import FileManager


def main():
    """Main function for snippet selection program."""
    print_section_header("Video Snippet Selection Tool")
    print("This tool extracts video snippets around specific times of interest.")
    print("Times are read from an Excel file, and snippets are saved with metadata.\n")

    try:
        # Get input folder
        input_folder = get_directory_path(
            "Enter path to input folder containing videos: "
        )

        # Get Excel file with timestamps
        excel_file = get_file_path(
            "Enter path to Excel file with timestamps: "
        )

        # Get duration settings (with defaults)
        print("\nDuration settings:")
        print("Default: 5 seconds before and 10 seconds after each timestamp")

        use_defaults = get_yes_no_choice("Use default duration settings?", default=True)

        if use_defaults:
            before_duration = 5.0
            after_duration = 10.0
        else:
            before_duration = get_positive_number(
                "Enter seconds to include BEFORE each timestamp: ",
                number_type=float
            )
            after_duration = get_positive_number(
                "Enter seconds to include AFTER each timestamp: ",
                number_type=float
            )

        # Get output directory
        output_dir = get_directory_path(
            "Enter output directory (where snippets will be saved): ",
            must_exist=False
        )

        # Create output directory if it doesn't exist
        create_output_directory(output_dir)

        print_section_header("Processing Setup")

        # Initialize components
        excel_parser = ExcelParser()
        file_manager = FileManager(input_folder)
        video_extractor = VideoExtractor(output_dir, before_duration, after_duration)
        csv_manager = CSVManager(output_dir)

        # Parse Excel file
        print("Reading Excel file...")
        timestamps_data = excel_parser.parse_excel(excel_file)

        if not timestamps_data:
            print("No valid timestamp data found in Excel file.")
            return

        print(f"Found timestamp data for {len(timestamps_data)} video(s)")

        # Find all video files in input folder
        print("Searching for video files...")
        found_videos = file_manager.find_all_videos()

        if not found_videos:
            print("No video files found in the input folder.")
            return

        print(f"Found {len(found_videos)} video file(s) in input folder")

        # Match videos with timestamp data
        print("Matching videos with timestamp data...")
        video_matches = file_manager.match_videos_with_timestamps(timestamps_data, found_videos)

        # Report missing videos
        missing_videos = [video_name for video_name in timestamps_data.keys()
                         if video_name not in video_matches]

        if missing_videos:
            print(f"\nWarning: {len(missing_videos)} video(s) not found:")
            for video_name in missing_videos:
                print(f"  - {video_name}")

            choice = get_choice_from_list(
                "\nHow would you like to proceed?",
                ["Continue without missing videos", "Stop and check missing videos"]
            )

            if choice == "Stop and check missing videos":
                return

        if not video_matches:
            print("No matching videos found for timestamp data.")
            return

        # Check for already processed videos
        print("Checking for already processed videos...")
        already_processed = []
        for video_name in video_matches.keys():
            if video_extractor.is_video_already_processed(video_name):
                already_processed.append(video_name)

        if already_processed:
            print(f"\n{len(already_processed)} video(s) appear to be already processed:")
            for video_name in already_processed:
                print(f"  - {video_name}")

            choice = get_choice_from_list(
                "\nHow would you like to handle already processed videos?",
                ["Reprocess all videos", "Skip already processed videos"]
            )

            if choice == "Skip already processed videos":
                for video_name in already_processed:
                    del video_matches[video_name]

        if not video_matches:
            print("No videos to process after filtering.")
            return

        print_section_header("Processing Videos")
        print(f"Processing {len(video_matches)} video(s)...")

        # Process each video
        total_snippets_created = 0
        processed_count = 0

        for video_name, video_path in video_matches.items():
            processed_count += 1
            print_progress(processed_count, len(video_matches), "Videos processed")

            print(f"\nProcessing: {video_name}")

            # Get video information
            video_info = get_video_info(video_path)
            if not video_info:
                print(f"Error: Could not read video file {video_path}")
                continue

            print_file_info(video_path, duration=video_info['duration'])

            # Get timestamps for this video
            video_timestamps = timestamps_data[video_name]
            print(f"Found {len(video_timestamps)} timestamp(s) for this video")

            # Extract snippets for each timestamp
            snippets_created = 0
            for timestamp_info in video_timestamps:
                try:
                    success = video_extractor.extract_snippet(
                        video_path,
                        video_name,
                        timestamp_info,
                        video_info['duration']
                    )

                    if success:
                        snippets_created += 1
                        # Add to CSV report
                        csv_manager.add_snippet_record(
                            video_name,
                            timestamp_info,
                            video_extractor.get_last_created_snippet_path()
                        )

                except Exception as e:
                    print(f"Error processing timestamp {timestamp_info.get('time', 'unknown')}: {e}")

            print(f"✓ Created {snippets_created} snippet(s) for {video_name}")
            total_snippets_created += snippets_created

        # Save CSV report
        print("\nSaving processing report...")
        csv_manager.save_report()

        print_section_header("Processing Complete")
        print(f"Successfully processed {processed_count} video(s)")
        print(f"Created {total_snippets_created} snippet(s)")
        print(f"Output saved to: {output_dir}")
        print(f"Processing report saved as CSV in the output directory")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your input and try again.")


if __name__ == "__main__":
    main()