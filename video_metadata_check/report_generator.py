"""
Report generation module for video metadata.

This module provides functionality to generate human-readable reports in multiple formats
including console output, JSON, CSV, and plain text files.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class ReportGenerator:
    """
    Generates reports from video metadata in various formats.

    Supports console output, JSON export, CSV export, and plain text reports
    with comprehensive metadata information and comparison results.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize ReportGenerator.

        Args:
            output_dir (Optional[str]): Directory to save report files. If None, uses current directory.
        """
        self.output_dir = output_dir if output_dir else "."

    def generate_console_report(self, metadata_list: List[Dict[str, Any]],
                                comparison_results: Optional[Dict[str, Any]] = None) -> None:
        """
        Generate and print a formatted console report.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            comparison_results (Optional[Dict[str, Any]]): Comparison results if comparing videos
        """
        print("\n" + "=" * 80)
        print("VIDEO METADATA REPORT")
        print("=" * 80)
        print(f"Total videos analyzed: {len(metadata_list)}")
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        if not metadata_list:
            print("No video metadata available.")
            return

        # Display individual video information
        for idx, metadata in enumerate(metadata_list, 1):
            self._print_video_metadata(idx, metadata)

        # Display comparison results if available
        if comparison_results:
            self._print_comparison_results(comparison_results)

    def _print_video_metadata(self, index: int, metadata: Dict[str, Any]) -> None:
        """
        Print formatted metadata for a single video.

        Args:
            index (int): Video number
            metadata (Dict[str, Any]): Video metadata
        """
        print(f"\n[Video {index}] {metadata.get('filename', 'Unknown')}")
        print("-" * 80)

        # Essential metadata (always show these)
        essential_fields = {
            'recording_fps': ('Recording Frame Rate', lambda x: f"{x:.2f} FPS"),
            'fps': ('Playback Frame Rate', lambda x: f"{x:.2f} FPS"),
            'actual_fps': ('Actual Frame Rate', lambda x: f"{x:.2f} FPS"),
            'duration': ('Duration', lambda x: self._format_duration(x)),
            'frame_count': ('Number of Frames', lambda x: f"{x:,}"),
            'resolution': ('Resolution', lambda x: f"{x}"),
            'file_size_mb': ('File Size', lambda x: f"{x:.2f} MB" if x < 1024 else f"{x/1024:.2f} GB"),
        }

        for field, (label, formatter) in essential_fields.items():
            value = metadata.get(field)
            if value is not None:
                try:
                    formatted_value = formatter(value)
                    print(f"  {label:.<30} {formatted_value}")
                except:
                    print(f"  {label:.<30} {value}")

        # Additional metadata (if available)
        additional_fields = {
            'width': ('Width', lambda x: f"{x} px"),
            'height': ('Height', lambda x: f"{x} px"),
            'aspect_ratio': ('Aspect Ratio', lambda x: x),
            'video_codec': ('Video Codec', lambda x: x),
            'audio_codec': ('Audio Codec', lambda x: x if x != 'None' else 'No Audio'),
            'bitrate': ('Bitrate', lambda x: f"{x/1_000_000:.2f} Mbps" if x > 0 else 'N/A'),
            'format_name': ('Format', lambda x: x),
        }

        has_additional = False
        for field, (label, formatter) in additional_fields.items():
            value = metadata.get(field)
            if value is not None:
                if not has_additional:
                    print("  " + "-" * 40)
                    has_additional = True
                try:
                    formatted_value = formatter(value)
                    print(f"  {label:.<30} {formatted_value}")
                except:
                    print(f"  {label:.<30} {value}")

    def _print_comparison_results(self, comparison_results: Dict[str, Any]) -> None:
        """
        Print formatted comparison results.

        Args:
            comparison_results (Dict[str, Any]): Comparison results
        """
        print("\n" + "=" * 80)
        print("COMPARISON RESULTS")
        print("=" * 80)

        # Show matching fields
        if comparison_results.get('matching_fields'):
            print("\n✓ Fields that MATCH across all videos:")
            for field in comparison_results['matching_fields']:
                field_result = comparison_results['field_results'].get(field, {})
                field_name = field_result.get('field_name', field)
                common_value = field_result.get('common_value', 'N/A')
                print(f"  • {field_name}: {common_value}")

        # Show mismatching fields
        if comparison_results.get('mismatching_fields'):
            print("\n✗ Fields that DIFFER across videos:")
            for field in comparison_results['mismatching_fields']:
                field_result = comparison_results['field_results'].get(field, {})
                field_name = field_result.get('field_name', field)
                videos_by_value = field_result.get('videos_by_value', {})

                print(f"\n  • {field_name}:")
                for value, videos in videos_by_value.items():
                    print(f"    - {value}: {len(videos)} video(s)")
                    for video in videos[:3]:  # Show first 3 videos
                        print(f"      └─ {video}")
                    if len(videos) > 3:
                        print(f"      └─ ... and {len(videos) - 3} more")

    def save_json_report(self, metadata_list: List[Dict[str, Any]],
                        comparison_results: Optional[Dict[str, Any]] = None,
                        filename: Optional[str] = None) -> str:
        """
        Save metadata as JSON file.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            comparison_results (Optional[Dict[str, Any]]): Comparison results if available
            filename (Optional[str]): Custom filename. If None, generates timestamped filename.

        Returns:
            str: Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"video_metadata_{timestamp}.json"

        filepath = Path(self.output_dir) / filename

        report_data = {
            'generated_at': datetime.now().isoformat(),
            'total_videos': len(metadata_list),
            'videos': metadata_list
        }

        if comparison_results:
            report_data['comparison'] = comparison_results

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ JSON report saved: {filepath}")
        return str(filepath)

    def save_csv_report(self, metadata_list: List[Dict[str, Any]],
                       filename: Optional[str] = None) -> str:
        """
        Save metadata as CSV file.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            filename (Optional[str]): Custom filename. If None, generates timestamped filename.

        Returns:
            str: Path to saved file
        """
        if not metadata_list:
            print("No metadata to save.")
            return ""

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"video_metadata_{timestamp}.csv"

        filepath = Path(self.output_dir) / filename

        # Define CSV columns (essential fields)
        csv_columns = [
            'filename',
            'fps',
            'actual_fps',
            'duration',
            'frame_count',
            'width',
            'height',
            'resolution',
            'file_size_mb',
            'video_codec',
            'audio_codec',
            'bitrate',
            'format_name'
        ]

        # Filter columns that exist in data
        available_columns = []
        for col in csv_columns:
            if any(col in metadata for metadata in metadata_list):
                available_columns.append(col)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=available_columns, extrasaction='ignore')
            writer.writeheader()

            for metadata in metadata_list:
                # Create row with only available columns
                row = {col: metadata.get(col, 'N/A') for col in available_columns}
                writer.writerow(row)

        print(f"\n✓ CSV report saved: {filepath}")
        return str(filepath)

    def save_text_report(self, metadata_list: List[Dict[str, Any]],
                        comparison_results: Optional[Dict[str, Any]] = None,
                        filename: Optional[str] = None) -> str:
        """
        Save metadata as human-readable text file.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            comparison_results (Optional[Dict[str, Any]]): Comparison results if available
            filename (Optional[str]): Custom filename. If None, generates timestamped filename.

        Returns:
            str: Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"video_metadata_report_{timestamp}.txt"

        filepath = Path(self.output_dir) / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write("VIDEO METADATA REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total videos analyzed: {len(metadata_list)}\n")
            f.write(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")

            # Write individual video information
            for idx, metadata in enumerate(metadata_list, 1):
                f.write(f"\n[Video {idx}] {metadata.get('filename', 'Unknown')}\n")
                f.write("-" * 80 + "\n")

                self._write_video_metadata_to_file(f, metadata)

            # Write comparison results if available
            if comparison_results:
                f.write("\n" + "=" * 80 + "\n")
                f.write("COMPARISON RESULTS\n")
                f.write("=" * 80 + "\n")

                self._write_comparison_to_file(f, comparison_results)

        print(f"\n✓ Text report saved: {filepath}")
        return str(filepath)

    def _write_video_metadata_to_file(self, file_handle, metadata: Dict[str, Any]) -> None:
        """Write formatted metadata to file."""
        essential_fields = [
            ('fps', 'Recording Frame Rate', 'FPS'),
            ('actual_fps', 'Actual Frame Rate', 'FPS'),
            ('duration', 'Duration', 'seconds'),
            ('frame_count', 'Number of Frames', ''),
            ('resolution', 'Resolution', ''),
            ('file_size_mb', 'File Size', 'MB'),
            ('video_codec', 'Video Codec', ''),
            ('audio_codec', 'Audio Codec', ''),
        ]

        for field, label, unit in essential_fields:
            value = metadata.get(field)
            if value is not None:
                if unit:
                    file_handle.write(f"  {label:.<30} {value} {unit}\n")
                else:
                    file_handle.write(f"  {label:.<30} {value}\n")

    def _write_comparison_to_file(self, file_handle, comparison_results: Dict[str, Any]) -> None:
        """Write comparison results to file."""
        # Write matching fields
        if comparison_results.get('matching_fields'):
            file_handle.write("\n✓ Fields that MATCH across all videos:\n")
            for field in comparison_results['matching_fields']:
                field_result = comparison_results['field_results'].get(field, {})
                field_name = field_result.get('field_name', field)
                common_value = field_result.get('common_value', 'N/A')
                file_handle.write(f"  • {field_name}: {common_value}\n")

        # Write mismatching fields
        if comparison_results.get('mismatching_fields'):
            file_handle.write("\n✗ Fields that DIFFER across videos:\n")
            for field in comparison_results['mismatching_fields']:
                field_result = comparison_results['field_results'].get(field, {})
                field_name = field_result.get('field_name', field)
                videos_by_value = field_result.get('videos_by_value', {})

                file_handle.write(f"\n  • {field_name}:\n")
                for value, videos in videos_by_value.items():
                    file_handle.write(f"    - {value}: {len(videos)} video(s)\n")
                    for video in videos:
                        file_handle.write(f"      └─ {video}\n")

    def _format_duration(self, duration_seconds: float) -> str:
        """
        Format duration in seconds to HH:MM:SS.

        Args:
            duration_seconds (float): Duration in seconds

        Returns:
            str: Formatted duration string
        """
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
