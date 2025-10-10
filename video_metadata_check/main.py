"""
Main entry point for Video Metadata Check tool.

This tool extracts and analyzes video metadata, supports comparison of multiple videos,
and generates reports in various formats (console, JSON, CSV, TXT).
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path to import shared modules
sys.path.append(str(Path(__file__).parent.parent))

from shared.user_interface import (
    get_file_path, get_directory_path, get_choice_from_list,
    get_yes_no_choice, print_section_header, get_multiple_choices_from_list
)
from shared.file_utils import find_video_files

try:
    from .metadata_extractor import VideoMetadataExtractor
    from .metadata_comparator import VideoMetadataComparator
    from .report_generator import ReportGenerator
except ImportError:
    from metadata_extractor import VideoMetadataExtractor
    from metadata_comparator import VideoMetadataComparator
    from report_generator import ReportGenerator


def main():
    """Main function for Video Metadata Check tool."""
    print_section_header("Video Metadata Check Tool")
    print("This tool extracts and analyzes video metadata.")
    print("Supports individual analysis and comparison of multiple videos.\n")

    try:
        # Step 1: Get input from user
        input_choice = get_choice_from_list(
            "What would you like to analyze?",
            ["Single video file", "Directory containing videos"]
        )

        video_files = []

        if input_choice == "Single video file":
            video_file = get_file_path("Enter path to video file: ")
            video_files = [video_file]
        else:
            input_folder = get_directory_path("Enter path to directory containing videos: ")
            print("\nSearching for video files...")
            video_files = find_video_files(input_folder, recursive=True)

            if not video_files:
                print("No video files found in the specified directory.")
                return

            print(f"Found {len(video_files)} video file(s)")

        # Step 2: Extract metadata from all videos
        print_section_header("Extracting Metadata")
        extractor = VideoMetadataExtractor()
        metadata_list = []

        for idx, video_path in enumerate(video_files, 1):
            print(f"Processing video {idx}/{len(video_files)}: {Path(video_path).name}")
            metadata = extractor.extract_metadata(video_path)

            if metadata:
                metadata_list.append(metadata)
            else:
                print(f"  Warning: Could not extract metadata from {Path(video_path).name}")

        if not metadata_list:
            print("\nNo metadata could be extracted. Please check your video files.")
            return

        print(f"\n✓ Successfully extracted metadata from {len(metadata_list)} video(s)")

        # Step 3: Determine if we should compare videos
        comparison_results = None

        if len(metadata_list) > 1:
            should_compare = get_yes_no_choice(
                "\nWould you like to compare these videos?",
                default=True
            )

            if should_compare:
                comparison_results = perform_comparison(metadata_list)

        # Step 4: Generate reports
        print_section_header("Generating Reports")

        # Get output directory for file reports
        save_files = get_yes_no_choice(
            "Would you like to save reports to files?",
            default=True
        )

        output_dir = None
        if save_files:
            output_dir = get_directory_path(
                "Enter output directory for reports: ",
                must_exist=False
            )
            Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Generate console report
        generator = ReportGenerator(output_dir)
        print_section_header("Metadata Report")
        generator.generate_console_report(metadata_list, comparison_results)

        # Save file reports if requested
        if save_files:
            print("\nSaving file reports...")

            # Ask which formats to save
            format_choice = get_choice_from_list(
                "\nWhich formats would you like to save?",
                ["All formats (JSON, CSV, TXT)", "Select specific formats"]
            )

            formats_to_save = ['json', 'csv', 'txt']

            if format_choice == "Select specific formats":
                selected_formats = get_multiple_choices_from_list(
                    "Select report formats to save:",
                    ["JSON (structured data)", "CSV (spreadsheet)", "TXT (human-readable)"],
                    allow_all=True
                )

                # Map selections to format names
                format_map = {
                    "JSON (structured data)": 'json',
                    "CSV (spreadsheet)": 'csv',
                    "TXT (human-readable)": 'txt'
                }
                formats_to_save = [format_map[fmt] for fmt in selected_formats]

            # Save selected formats
            if 'json' in formats_to_save:
                generator.save_json_report(metadata_list, comparison_results)

            if 'csv' in formats_to_save:
                generator.save_csv_report(metadata_list)

            if 'txt' in formats_to_save:
                generator.save_text_report(metadata_list, comparison_results)

        print_section_header("Analysis Complete")
        print(f"Analyzed {len(metadata_list)} video(s)")

        if comparison_results:
            matching_count = len(comparison_results.get('matching_fields', []))
            mismatching_count = len(comparison_results.get('mismatching_fields', []))
            print(f"Comparison: {matching_count} matching field(s), {mismatching_count} differing field(s)")

        if save_files:
            print(f"Reports saved to: {output_dir}")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your input and try again.")


def perform_comparison(metadata_list):
    """
    Perform comparison of multiple videos.

    Args:
        metadata_list: List of metadata dictionaries

    Returns:
        Comparison results dictionary
    """
    print_section_header("Comparison Setup")

    comparator = VideoMetadataComparator()
    comparable_fields = comparator.get_comparable_field_names()

    # Ask which fields to compare
    print("\nAvailable metadata fields for comparison:")
    field_choices = list(comparable_fields.values())
    field_choices.append("All fields")

    selected_choice = get_choice_from_list(
        "Which fields would you like to compare?",
        ["Common fields (FPS, Resolution, Duration)", "Select specific fields", "All fields"]
    )

    fields_to_compare = []

    if selected_choice == "Common fields (FPS, Resolution, Duration)":
        fields_to_compare = ['fps', 'resolution', 'duration']

    elif selected_choice == "Select specific fields":
        # Create list of selectable fields
        selectable_fields = [f"{name} ({key})" for key, name in comparable_fields.items()]

        selected_fields = get_multiple_choices_from_list(
            "Select fields to compare:",
            selectable_fields,
            allow_all=True
        )

        # Extract field keys from selections
        for selection in selected_fields:
            # Find the field key from the selection string
            for key, name in comparable_fields.items():
                if f"{name} ({key})" == selection:
                    fields_to_compare.append(key)
                    break

    else:  # All fields
        fields_to_compare = list(comparable_fields.keys())

    # Perform comparison
    print(f"\nComparing {len(fields_to_compare)} field(s) across {len(metadata_list)} video(s)...")
    comparison_results = comparator.compare_videos(metadata_list, fields_to_compare)

    # Ask if user wants to check if all videos should match
    should_validate = get_yes_no_choice(
        "\nWould you like to check if all videos share specific characteristics?",
        default=False
    )

    if should_validate:
        validate_criteria(metadata_list, comparator, fields_to_compare)

    return comparison_results


def validate_criteria(metadata_list, comparator, fields_to_compare):
    """
    Validate videos against user-specified criteria.

    Args:
        metadata_list: List of metadata dictionaries
        comparator: VideoMetadataComparator instance
        fields_to_compare: List of field names being compared
    """
    print("\n" + "-" * 80)
    print("VALIDATION SETUP")
    print("-" * 80)

    print("\nFor each field, specify the expected value that all videos should have.")
    print("Leave blank to skip validation for that field.\n")

    criteria = {}

    for field in fields_to_compare:
        field_name = comparator.get_comparable_field_names().get(field, field)

        # Get first video's value as suggestion
        first_value = metadata_list[0].get(field, 'N/A')

        prompt = f"{field_name} (current: {first_value}): "
        user_input = input(prompt).strip()

        if user_input:
            # Try to convert to appropriate type
            try:
                if '.' in user_input:
                    criteria[field] = float(user_input)
                elif user_input.isdigit():
                    criteria[field] = int(user_input)
                else:
                    criteria[field] = user_input
            except ValueError:
                criteria[field] = user_input

    if criteria:
        print("\nValidating videos against criteria...")
        validation_results = comparator.check_criteria(metadata_list, criteria)

        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)

        if validation_results['all_pass']:
            print(f"\n✓ All {len(metadata_list)} video(s) meet the specified criteria!")
        else:
            passing = len(validation_results['passing_videos'])
            failing = len(validation_results['failing_videos'])

            print(f"\n✓ {passing} video(s) pass")
            print(f"✗ {failing} video(s) fail")

            if validation_results['failing_videos']:
                print("\nFailing videos:")
                for failure in validation_results['failing_videos']:
                    print(f"\n  {failure['video']}:")
                    for fail_detail in failure['failures']:
                        print(f"    - {fail_detail['field']}: expected {fail_detail['expected']}, got {fail_detail['actual']}")


if __name__ == "__main__":
    main()
