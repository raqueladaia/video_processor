"""
Crop Data Management Module

This module handles saving and loading crop rectangle configurations to/from
JSON files, enabling users to reuse crop settings across different videos.

Author: Video Processing Project
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Add parent directory to path for shared module imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from .rectangle_manager import Rectangle, RectangleManager
except ImportError:
    from rectangle_manager import Rectangle, RectangleManager


class CropDataManager:
    """
    Manages saving and loading of crop rectangle configurations.

    Provides functionality to save crop patterns as templates and load them
    for reuse with different videos.
    """

    def __init__(self):
        """Initialize the crop data manager."""
        self.default_extension = ".crop"

    def save_crop_configuration(self, rectangles: List[Rectangle], file_path: str,
                               video_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save crop rectangles to a JSON file.

        Args:
            rectangles (List[Rectangle]): List of rectangles to save
            file_path (str): Path to save the configuration file
            video_info (Optional[Dict[str, Any]]): Optional video information

        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Ensure file has proper extension
            if not file_path.endswith(self.default_extension):
                file_path += self.default_extension

            # Prepare data structure
            crop_data = {
                'version': '1.0',
                'video_info': video_info or {},
                'rectangles': [rect.to_dict() for rect in rectangles],
                'metadata': {
                    'count': len(rectangles),
                    'names': [rect.name for rect in rectangles]
                }
            }

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(crop_data, f, indent=2, ensure_ascii=False)

            print(f"Crop configuration saved: {file_path}")
            return True

        except Exception as e:
            print(f"Error saving crop configuration: {e}")
            return False

    def load_crop_configuration(self, file_path: str) -> Optional[List[Rectangle]]:
        """
        Load crop rectangles from a JSON file.

        Args:
            file_path (str): Path to the configuration file

        Returns:
            Optional[List[Rectangle]]: List of loaded rectangles, or None if error
        """
        try:
            if not os.path.exists(file_path):
                print(f"Crop configuration file not found: {file_path}")
                return None

            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                crop_data = json.load(f)

            # Validate data structure
            if not self._validate_crop_data(crop_data):
                print(f"Invalid crop configuration format: {file_path}")
                return None

            # Load rectangles
            rectangles = []
            for rect_data in crop_data.get('rectangles', []):
                try:
                    rect = Rectangle.from_dict(rect_data)
                    rectangles.append(rect)
                except Exception as e:
                    print(f"Error loading rectangle: {e}")
                    continue

            print(f"Loaded {len(rectangles)} crop rectangles from: {file_path}")
            return rectangles

        except Exception as e:
            print(f"Error loading crop configuration: {e}")
            return None

    def save_as_template(self, rectangles: List[Rectangle], template_name: str,
                        video_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save crop rectangles as a reusable template.

        Args:
            rectangles (List[Rectangle]): List of rectangles to save
            template_name (str): Name for the template
            video_info (Optional[Dict[str, Any]]): Optional video information

        Returns:
            bool: True if save was successful, False otherwise
        """
        # Create templates directory
        templates_dir = Path.home() / '.video_processing' / 'crop_templates'
        templates_dir.mkdir(parents=True, exist_ok=True)

        # Generate template file path
        safe_name = self._sanitize_template_name(template_name)
        template_path = templates_dir / f"{safe_name}{self.default_extension}"

        return self.save_crop_configuration(rectangles, str(template_path), video_info)

    def load_template(self, template_name: str) -> Optional[List[Rectangle]]:
        """
        Load crop rectangles from a saved template.

        Args:
            template_name (str): Name of the template to load

        Returns:
            Optional[List[Rectangle]]: List of loaded rectangles, or None if error
        """
        templates_dir = Path.home() / '.video_processing' / 'crop_templates'
        safe_name = self._sanitize_template_name(template_name)
        template_path = templates_dir / f"{safe_name}{self.default_extension}"

        return self.load_crop_configuration(str(template_path))

    def list_templates(self) -> List[str]:
        """
        Get list of available template names.

        Returns:
            List[str]: List of template names
        """
        templates_dir = Path.home() / '.video_processing' / 'crop_templates'

        if not templates_dir.exists():
            return []

        templates = []
        for file_path in templates_dir.glob(f"*{self.default_extension}"):
            # Remove extension and return original name
            template_name = file_path.stem
            templates.append(template_name)

        return sorted(templates)

    def delete_template(self, template_name: str) -> bool:
        """
        Delete a saved template.

        Args:
            template_name (str): Name of the template to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            templates_dir = Path.home() / '.video_processing' / 'crop_templates'
            safe_name = self._sanitize_template_name(template_name)
            template_path = templates_dir / f"{safe_name}{self.default_extension}"

            if template_path.exists():
                template_path.unlink()
                print(f"Template deleted: {template_name}")
                return True
            else:
                print(f"Template not found: {template_name}")
                return False

        except Exception as e:
            print(f"Error deleting template: {e}")
            return False

    def export_configuration(self, rectangles: List[Rectangle], export_path: str,
                           video_info: Optional[Dict[str, Any]] = None,
                           include_metadata: bool = True) -> bool:
        """
        Export crop configuration to a specified location with additional metadata.

        Args:
            rectangles (List[Rectangle]): List of rectangles to export
            export_path (str): Path to export the configuration
            video_info (Optional[Dict[str, Any]]): Optional video information
            include_metadata (bool): Whether to include additional metadata

        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            # Prepare enhanced data structure
            crop_data = {
                'version': '1.0',
                'video_info': video_info or {},
                'rectangles': [rect.to_dict() for rect in rectangles]
            }

            if include_metadata:
                import datetime
                crop_data['metadata'] = {
                    'count': len(rectangles),
                    'names': [rect.name for rect in rectangles],
                    'export_date': datetime.datetime.now().isoformat(),
                    'total_area': sum(rect.width * rect.height for rect in rectangles),
                    'bounding_box': self._calculate_bounding_box(rectangles) if rectangles else None
                }

            # Write to file
            return self.save_crop_configuration(rectangles, export_path, video_info)

        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False

    def get_configuration_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a crop configuration file without loading rectangles.

        Args:
            file_path (str): Path to the configuration file

        Returns:
            Optional[Dict[str, Any]]: Configuration metadata, or None if error
        """
        try:
            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                crop_data = json.load(f)

            info = {
                'version': crop_data.get('version', 'unknown'),
                'rectangle_count': len(crop_data.get('rectangles', [])),
                'video_info': crop_data.get('video_info', {}),
                'metadata': crop_data.get('metadata', {}),
                'file_size': os.path.getsize(file_path)
            }

            return info

        except Exception as e:
            print(f"Error reading configuration info: {e}")
            return None

    def _validate_crop_data(self, crop_data: Dict[str, Any]) -> bool:
        """
        Validate the structure of loaded crop data.

        Args:
            crop_data (Dict[str, Any]): Data loaded from JSON file

        Returns:
            bool: True if data structure is valid, False otherwise
        """
        try:
            # Check required fields
            if not isinstance(crop_data, dict):
                return False

            if 'rectangles' not in crop_data:
                return False

            rectangles = crop_data['rectangles']
            if not isinstance(rectangles, list):
                return False

            # Validate each rectangle
            for rect_data in rectangles:
                if not isinstance(rect_data, dict):
                    return False

                required_fields = ['x', 'y', 'width', 'height', 'name']
                for field in required_fields:
                    if field not in rect_data:
                        return False

            return True

        except Exception:
            return False

    def _sanitize_template_name(self, name: str) -> str:
        """
        Sanitize template name for use as filename.

        Args:
            name (str): Original template name

        Returns:
            str: Sanitized filename
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')

        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')

        # Ensure name is not empty
        if not sanitized:
            sanitized = "unnamed_template"

        return sanitized

    def _calculate_bounding_box(self, rectangles: List[Rectangle]) -> Dict[str, int]:
        """
        Calculate the bounding box that contains all rectangles.

        Args:
            rectangles (List[Rectangle]): List of rectangles

        Returns:
            Dict[str, int]: Bounding box coordinates
        """
        if not rectangles:
            return {'x': 0, 'y': 0, 'width': 0, 'height': 0}

        min_x = min(rect.x for rect in rectangles)
        min_y = min(rect.y for rect in rectangles)
        max_x = max(rect.x2 for rect in rectangles)
        max_y = max(rect.y2 for rect in rectangles)

        return {
            'x': min_x,
            'y': min_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }