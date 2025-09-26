"""
CSV management module for generating processing reports.

This module handles creating and updating CSV files that contain information
about processed video snippets including metadata from the original Excel file.
"""

import csv
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class CSVManager:
    """
    Manages CSV report generation for snippet processing results.

    Creates a CSV file containing information about each processed snippet
    including the original video name, timestamp, arousal type, and comments.
    """

    def __init__(self, output_dir: str):
        """
        Initialize CSVManager.

        Args:
            output_dir (str): Directory where CSV report will be saved
        """
        self.output_dir = output_dir
        self.csv_records = []
        self.csv_headers = [
            'snippet_filename',
            'original_video',
            'timestamp_hhmmss',
            'timestamp_seconds',
            'arousal_type',
            'comments',
            'processing_date',
            'snippet_path'
        ]

    def add_snippet_record(self, video_name: str, timestamp_info: Dict[str, Any], snippet_path: str):
        """
        Add a record for a processed snippet.

        Args:
            video_name (str): Name of the original video
            timestamp_info (Dict[str, Any]): Timestamp information from Excel
            snippet_path (str): Path to the created snippet file
        """
        try:
            # Convert timestamp to hhmmss format
            timestamp_seconds = timestamp_info.get('time_seconds', 0)
            hhmmss = self._seconds_to_hhmmss(timestamp_seconds)

            record = {
                'snippet_filename': Path(snippet_path).name,
                'original_video': video_name,
                'timestamp_hhmmss': hhmmss,
                'timestamp_seconds': timestamp_seconds,
                'arousal_type': timestamp_info.get('arousal_type', ''),
                'comments': timestamp_info.get('comments', ''),
                'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'snippet_path': snippet_path
            }

            self.csv_records.append(record)

        except Exception as e:
            print(f"Error adding CSV record: {e}")

    def save_report(self, filename: str = None) -> str:
        """
        Save the CSV report to file.

        Args:
            filename (str, optional): Custom filename for the report

        Returns:
            str: Path to the saved CSV file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"snippet_processing_report_{timestamp}.csv"

            csv_path = os.path.join(self.output_dir, filename)

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)

                # Write header
                writer.writeheader()

                # Write records
                for record in self.csv_records:
                    writer.writerow(record)

            print(f"CSV report saved: {Path(csv_path).name}")
            print(f"Report contains {len(self.csv_records)} snippet record(s)")

            return csv_path

        except Exception as e:
            print(f"Error saving CSV report: {e}")
            return ""

    def load_existing_report(self, csv_path: str) -> bool:
        """
        Load an existing CSV report.

        Args:
            csv_path (str): Path to existing CSV file

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            self.csv_records = []

            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    self.csv_records.append(row)

            print(f"Loaded {len(self.csv_records)} records from existing CSV")
            return True

        except Exception as e:
            print(f"Error loading CSV report: {e}")
            return False

    def update_existing_report(self, csv_path: str):
        """
        Update an existing CSV report with new records.

        Args:
            csv_path (str): Path to existing CSV file
        """
        try:
            # Load existing records
            existing_records = []
            if os.path.exists(csv_path):
                with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    existing_records = list(reader)

            # Combine with new records
            all_records = existing_records + self.csv_records

            # Write updated file
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writeheader()

                for record in all_records:
                    writer.writerow(record)

            print(f"Updated CSV report with {len(self.csv_records)} new record(s)")
            print(f"Total records in report: {len(all_records)}")

        except Exception as e:
            print(f"Error updating CSV report: {e}")

    def get_processed_videos(self, csv_path: str) -> List[str]:
        """
        Get list of videos that have already been processed based on CSV report.

        Args:
            csv_path (str): Path to CSV report file

        Returns:
            List[str]: List of video names that have been processed
        """
        try:
            if not os.path.exists(csv_path):
                return []

            processed_videos = set()

            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    original_video = row.get('original_video', '')
                    if original_video:
                        processed_videos.add(original_video)

            return list(processed_videos)

        except Exception as e:
            print(f"Error reading processed videos from CSV: {e}")
            return []

    def _seconds_to_hhmmss(self, seconds: float) -> str:
        """
        Convert seconds to HH:MM:SS format.

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

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a summary of the processing results.

        Returns:
            Dict[str, Any]: Summary statistics
        """
        try:
            total_snippets = len(self.csv_records)
            unique_videos = len(set(record['original_video'] for record in self.csv_records))

            # Count by arousal type
            arousal_counts = {}
            for record in self.csv_records:
                arousal_type = record.get('arousal_type', 'Unknown')
                if arousal_type in arousal_counts:
                    arousal_counts[arousal_type] += 1
                else:
                    arousal_counts[arousal_type] = 1

            return {
                'total_snippets': total_snippets,
                'unique_videos': unique_videos,
                'arousal_type_counts': arousal_counts,
                'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            print(f"Error generating summary report: {e}")
            return {}