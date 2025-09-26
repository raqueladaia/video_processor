"""
Excel file parsing module for reading timestamp data.

This module handles reading Excel files containing video timestamps and
associated metadata such as arousal types and comments.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
import re


class ExcelParser:
    """
    Handles parsing Excel files containing video timestamp data.

    Expected Excel format:
    - Column with video names (can be in any column)
    - Column with timestamps (can be time format or seconds)
    - Optional columns for arousal type and comments
    """

    def __init__(self):
        """Initialize ExcelParser."""
        self.timestamp_columns = ['time', 'timestamp', 'time_of_interest', 'start_time']
        self.video_name_columns = ['video', 'video_name', 'file', 'filename', 'file_name']
        self.arousal_columns = ['arousal', 'arousal_type', 'type', 'category']
        self.comment_columns = ['comment', 'comments', 'description', 'notes']

    def parse_excel(self, excel_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse Excel file and extract timestamp data.

        Args:
            excel_path (str): Path to the Excel file

        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary mapping video names to
                lists of timestamp information dictionaries
        """
        try:
            print(f"Reading Excel file: {Path(excel_path).name}")

            # Read Excel file - try first sheet
            df = pd.read_excel(excel_path, sheet_name=0)

            print(f"Excel file contains {len(df)} rows and {len(df.columns)} columns")
            print(f"Columns: {list(df.columns)}")

            # Identify relevant columns
            video_col = self._find_column(df, self.video_name_columns)
            timestamp_col = self._find_column(df, self.timestamp_columns)
            arousal_col = self._find_column(df, self.arousal_columns)
            comment_col = self._find_column(df, self.comment_columns)

            if not video_col:
                print("Error: Could not find video name column in Excel file")
                print(f"Expected column names: {self.video_name_columns}")
                return {}

            if not timestamp_col:
                print("Error: Could not find timestamp column in Excel file")
                print(f"Expected column names: {self.timestamp_columns}")
                return {}

            print(f"Using video column: {video_col}")
            print(f"Using timestamp column: {timestamp_col}")
            if arousal_col:
                print(f"Using arousal column: {arousal_col}")
            if comment_col:
                print(f"Using comment column: {comment_col}")

            # Group data by video name
            result = {}
            processed_rows = 0

            for index, row in df.iterrows():
                try:
                    # Get video name
                    video_name = str(row[video_col]).strip()
                    if pd.isna(row[video_col]) or not video_name:
                        continue

                    # Remove file extension if present
                    video_name = Path(video_name).stem

                    # Get timestamp
                    timestamp_value = row[timestamp_col]
                    if pd.isna(timestamp_value):
                        continue

                    # Convert timestamp to seconds
                    timestamp_seconds = self._convert_timestamp_to_seconds(timestamp_value)
                    if timestamp_seconds is None:
                        print(f"Warning: Could not parse timestamp '{timestamp_value}' in row {index + 2}")
                        continue

                    # Create timestamp info dictionary
                    timestamp_info = {
                        'time': timestamp_value,
                        'time_seconds': timestamp_seconds,
                        'arousal_type': str(row[arousal_col]).strip() if arousal_col and not pd.isna(row[arousal_col]) else '',
                        'comments': str(row[comment_col]).strip() if comment_col and not pd.isna(row[comment_col]) else ''
                    }

                    # Add to result
                    if video_name not in result:
                        result[video_name] = []

                    result[video_name].append(timestamp_info)
                    processed_rows += 1

                except Exception as e:
                    print(f"Warning: Error processing row {index + 2}: {e}")
                    continue

            print(f"Successfully processed {processed_rows} timestamp entries")
            print(f"Found data for {len(result)} video(s)")

            return result

        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return {}

    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """
        Find a column in the dataframe by checking possible names.

        Args:
            df (pd.DataFrame): The dataframe to search
            possible_names (List[str]): List of possible column names

        Returns:
            Optional[str]: The actual column name if found, None otherwise
        """
        df_columns_lower = [col.lower() for col in df.columns]

        for possible_name in possible_names:
            if possible_name.lower() in df_columns_lower:
                # Return the actual column name (preserving case)
                index = df_columns_lower.index(possible_name.lower())
                return df.columns[index]

        return None

    def _convert_timestamp_to_seconds(self, timestamp_value: Any) -> Optional[float]:
        """
        Convert various timestamp formats to seconds.

        Args:
            timestamp_value: The timestamp value from Excel

        Returns:
            Optional[float]: Timestamp in seconds, or None if conversion failed
        """
        try:
            # If it's already a number, assume it's seconds
            if isinstance(timestamp_value, (int, float)):
                return float(timestamp_value)

            # If it's a string, try to parse different formats
            if isinstance(timestamp_value, str):
                timestamp_str = timestamp_value.strip()

                # Try HH:MM:SS format
                if ':' in timestamp_str:
                    parts = timestamp_str.split(':')
                    if len(parts) == 3:  # HH:MM:SS
                        hours = float(parts[0])
                        minutes = float(parts[1])
                        seconds = float(parts[2])
                        return hours * 3600 + minutes * 60 + seconds
                    elif len(parts) == 2:  # MM:SS
                        minutes = float(parts[0])
                        seconds = float(parts[1])
                        return minutes * 60 + seconds

                # Try to parse as a direct number
                try:
                    return float(timestamp_str)
                except ValueError:
                    pass

            # If it's a pandas Timestamp, try to extract time
            if hasattr(timestamp_value, 'hour'):
                return (timestamp_value.hour * 3600 +
                       timestamp_value.minute * 60 +
                       timestamp_value.second +
                       timestamp_value.microsecond / 1000000)

            return None

        except Exception:
            return None

    def validate_excel_format(self, excel_path: str) -> Dict[str, Any]:
        """
        Validate Excel file format and provide format information.

        Args:
            excel_path (str): Path to the Excel file

        Returns:
            Dict[str, Any]: Validation results and format information
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=0)

            validation_result = {
                'is_valid': False,
                'has_video_column': False,
                'has_timestamp_column': False,
                'has_arousal_column': False,
                'has_comment_column': False,
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'errors': []
            }

            # Check for required columns
            video_col = self._find_column(df, self.video_name_columns)
            timestamp_col = self._find_column(df, self.timestamp_columns)
            arousal_col = self._find_column(df, self.arousal_columns)
            comment_col = self._find_column(df, self.comment_columns)

            validation_result['has_video_column'] = video_col is not None
            validation_result['has_timestamp_column'] = timestamp_col is not None
            validation_result['has_arousal_column'] = arousal_col is not None
            validation_result['has_comment_column'] = comment_col is not None

            if not video_col:
                validation_result['errors'].append(f"Missing video name column. Expected one of: {self.video_name_columns}")

            if not timestamp_col:
                validation_result['errors'].append(f"Missing timestamp column. Expected one of: {self.timestamp_columns}")

            # File is valid if it has both required columns
            validation_result['is_valid'] = video_col is not None and timestamp_col is not None

            return validation_result

        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e)
            }