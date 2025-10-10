"""
Video metadata comparison module.

This module provides functionality to compare metadata across multiple videos,
detect similarities and differences, and validate against user-specified criteria.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict


class VideoMetadataComparator:
    """
    Compares metadata across multiple videos.

    Identifies matching and mismatching properties, groups videos by characteristics,
    and validates against user-defined criteria.
    """

    # Define available metadata fields for comparison
    COMPARABLE_FIELDS = {
        'fps': 'Frame Rate (FPS)',
        'actual_fps': 'Actual Frame Rate',
        'resolution': 'Resolution',
        'width': 'Width',
        'height': 'Height',
        'duration': 'Duration',
        'frame_count': 'Frame Count',
        'video_codec': 'Video Codec',
        'audio_codec': 'Audio Codec',
        'bitrate': 'Bitrate',
        'aspect_ratio': 'Aspect Ratio',
        'file_size_mb': 'File Size (MB)'
    }

    def __init__(self):
        """Initialize VideoMetadataComparator."""
        pass

    def compare_videos(self, metadata_list: List[Dict[str, Any]],
                      fields_to_compare: List[str]) -> Dict[str, Any]:
        """
        Compare metadata across multiple videos for specified fields.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            fields_to_compare (List[str]): List of field names to compare

        Returns:
            Dict[str, Any]: Comparison results including matches, mismatches, and groupings
        """
        if not metadata_list:
            return {'error': 'No metadata provided for comparison'}

        if not fields_to_compare:
            return {'error': 'No fields specified for comparison'}

        comparison_results = {
            'total_videos': len(metadata_list),
            'fields_compared': fields_to_compare,
            'field_results': {},
            'matching_fields': [],
            'mismatching_fields': [],
            'video_groups': {}
        }

        # Compare each field
        for field in fields_to_compare:
            if field not in self.COMPARABLE_FIELDS:
                continue

            field_result = self._compare_field(metadata_list, field)
            comparison_results['field_results'][field] = field_result

            # Track which fields match/mismatch across all videos
            if field_result['all_match']:
                comparison_results['matching_fields'].append(field)
            else:
                comparison_results['mismatching_fields'].append(field)

        return comparison_results

    def _compare_field(self, metadata_list: List[Dict[str, Any]],
                      field: str) -> Dict[str, Any]:
        """
        Compare a specific field across all videos.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            field (str): Field name to compare

        Returns:
            Dict[str, Any]: Comparison result for this field
        """
        values = []
        videos_by_value = defaultdict(list)

        # Collect values and group videos
        for idx, metadata in enumerate(metadata_list):
            value = metadata.get(field)

            # Handle missing values
            if value is None:
                value = 'N/A'

            # Round floating point values for comparison
            if isinstance(value, float):
                value = round(value, 2)

            values.append(value)
            video_filename = metadata.get('filename', f'Video {idx + 1}')
            videos_by_value[str(value)].append(video_filename)

        # Analyze results
        unique_values = set(values)
        all_match = len(unique_values) == 1

        result = {
            'field_name': self.COMPARABLE_FIELDS[field],
            'all_match': all_match,
            'unique_values': list(unique_values),
            'value_count': len(unique_values),
            'videos_by_value': dict(videos_by_value)
        }

        # If all match, store the common value
        if all_match:
            result['common_value'] = list(unique_values)[0]

        return result

    def check_criteria(self, metadata_list: List[Dict[str, Any]],
                       criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if videos meet user-specified criteria.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            criteria (Dict[str, Any]): Dictionary of field: expected_value pairs

        Returns:
            Dict[str, Any]: Results of criteria validation
        """
        validation_results = {
            'total_videos': len(metadata_list),
            'criteria_checked': criteria,
            'passing_videos': [],
            'failing_videos': [],
            'all_pass': True,
            'field_validation': {}
        }

        # Check each video against criteria
        for metadata in metadata_list:
            video_name = metadata.get('filename', 'Unknown')
            video_passes = True
            failures = []

            for field, expected_value in criteria.items():
                actual_value = metadata.get(field)

                # Round floating point for comparison
                if isinstance(actual_value, float):
                    actual_value = round(actual_value, 2)
                if isinstance(expected_value, float):
                    expected_value = round(expected_value, 2)

                # Check if value matches
                if actual_value != expected_value:
                    video_passes = False
                    failures.append({
                        'field': field,
                        'expected': expected_value,
                        'actual': actual_value
                    })

            if video_passes:
                validation_results['passing_videos'].append(video_name)
            else:
                validation_results['failing_videos'].append({
                    'video': video_name,
                    'failures': failures
                })
                validation_results['all_pass'] = False

        return validation_results

    def group_by_similarity(self, metadata_list: List[Dict[str, Any]],
                           group_by_fields: List[str]) -> Dict[str, List[str]]:
        """
        Group videos by similar metadata characteristics.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            group_by_fields (List[str]): Fields to use for grouping

        Returns:
            Dict[str, List[str]]: Groups of videos with similar characteristics
        """
        groups = defaultdict(list)

        for metadata in metadata_list:
            video_name = metadata.get('filename', 'Unknown')

            # Create a signature from the specified fields
            signature_parts = []
            for field in group_by_fields:
                value = metadata.get(field, 'N/A')
                if isinstance(value, float):
                    value = round(value, 2)
                signature_parts.append(f"{field}={value}")

            signature = ", ".join(signature_parts)
            groups[signature].append(video_name)

        return dict(groups)

    def detect_anomalies(self, metadata_list: List[Dict[str, Any]],
                        field: str, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Detect videos with anomalous values for a specific field.

        Uses statistical methods to find outliers.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            field (str): Field to check for anomalies
            threshold (float): Threshold for considering a value anomalous (as fraction)

        Returns:
            List[Dict[str, Any]]: List of anomalous videos with details
        """
        # Extract numeric values
        values = []
        video_values = []

        for metadata in metadata_list:
            value = metadata.get(field)
            if value is not None and isinstance(value, (int, float)):
                values.append(float(value))
                video_values.append({
                    'video': metadata.get('filename', 'Unknown'),
                    'value': value
                })

        if len(values) < 2:
            return []

        # Calculate mean and standard deviation
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5

        # Find anomalies (values more than threshold away from mean)
        anomalies = []
        for item in video_values:
            deviation = abs(item['value'] - mean)
            if std_dev > 0:
                normalized_deviation = deviation / mean
                if normalized_deviation > threshold:
                    anomalies.append({
                        'video': item['video'],
                        'value': item['value'],
                        'mean': mean,
                        'deviation': deviation,
                        'deviation_percent': normalized_deviation * 100
                    })

        return anomalies

    def get_summary_statistics(self, metadata_list: List[Dict[str, Any]],
                               field: str) -> Dict[str, Any]:
        """
        Calculate summary statistics for a numeric field.

        Args:
            metadata_list (List[Dict[str, Any]]): List of metadata dictionaries
            field (str): Numeric field to analyze

        Returns:
            Dict[str, Any]: Summary statistics (min, max, mean, median, etc.)
        """
        values = []

        for metadata in metadata_list:
            value = metadata.get(field)
            if value is not None and isinstance(value, (int, float)):
                values.append(float(value))

        if not values:
            return {'error': 'No numeric values found'}

        values.sort()
        n = len(values)

        stats = {
            'count': n,
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / n,
            'range': max(values) - min(values)
        }

        # Calculate median
        if n % 2 == 0:
            stats['median'] = (values[n//2 - 1] + values[n//2]) / 2
        else:
            stats['median'] = values[n//2]

        # Calculate standard deviation
        mean = stats['mean']
        variance = sum((x - mean) ** 2 for x in values) / n
        stats['std_dev'] = variance ** 0.5

        return stats

    @staticmethod
    def get_comparable_field_names() -> Dict[str, str]:
        """
        Get dictionary of comparable field names and their display names.

        Returns:
            Dict[str, str]: Field name to display name mapping
        """
        return VideoMetadataComparator.COMPARABLE_FIELDS.copy()
