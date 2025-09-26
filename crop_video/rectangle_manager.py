"""
Rectangle Manager Module for Crop Video Tool

This module handles the creation, editing, and management of crop rectangles
for video cropping operations. It provides classes for individual rectangles
and a manager for handling multiple rectangles.

Author: Video Processing Project
"""

import json
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import sys

# Add parent directory to path for shared module imports
sys.path.append(str(Path(__file__).parent.parent))


class Rectangle:
    """
    Represents a crop rectangle with coordinates, name, and visual properties.

    Coordinates are stored in video pixel space and converted to relative
    coordinates for display and FFmpeg processing.
    """

    def __init__(self, x: int, y: int, width: int, height: int, name: str = ""):
        """
        Initialize a crop rectangle.

        Args:
            x (int): X coordinate of top-left corner
            y (int): Y coordinate of top-left corner
            width (int): Width of the rectangle
            height (int): Height of the rectangle
            name (str): Name identifier for this crop region
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name or f"region_{id(self)}"
        self.color = "#FF0000"  # Default red color
        self.selected = False

    @property
    def x2(self) -> int:
        """Right edge x coordinate."""
        return self.x + self.width

    @property
    def y2(self) -> int:
        """Bottom edge y coordinate."""
        return self.y + self.height

    @property
    def center(self) -> Tuple[int, int]:
        """Center point of the rectangle."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains_point(self, x: int, y: int) -> bool:
        """
        Check if a point is inside this rectangle.

        Args:
            x (int): X coordinate to check
            y (int): Y coordinate to check

        Returns:
            bool: True if point is inside rectangle
        """
        return (self.x <= x <= self.x2 and
                self.y <= y <= self.y2)

    def is_valid(self) -> bool:
        """
        Check if rectangle has valid dimensions.

        Returns:
            bool: True if rectangle has positive width and height
        """
        return self.width > 0 and self.height > 0

    def normalize_coordinates(self, video_width: int, video_height: int) -> Dict[str, float]:
        """
        Convert pixel coordinates to normalized coordinates (0-1 range).

        Args:
            video_width (int): Width of the video in pixels
            video_height (int): Height of the video in pixels

        Returns:
            Dict[str, float]: Normalized coordinates
        """
        return {
            'x': self.x / video_width,
            'y': self.y / video_height,
            'width': self.width / video_width,
            'height': self.height / video_height
        }

    def get_ffmpeg_crop_filter(self) -> str:
        """
        Generate FFmpeg crop filter string for this rectangle.

        Returns:
            str: FFmpeg crop filter in format "crop=w:h:x:y"
        """
        return f"crop={self.width}:{self.height}:{self.x}:{self.y}"

    def resize(self, new_width: int, new_height: int):
        """
        Resize the rectangle.

        Args:
            new_width (int): New width
            new_height (int): New height
        """
        self.width = max(1, new_width)
        self.height = max(1, new_height)

    def move(self, new_x: int, new_y: int):
        """
        Move the rectangle to new position.

        Args:
            new_x (int): New x coordinate
            new_y (int): New y coordinate
        """
        self.x = new_x
        self.y = new_y

    def constrain_to_bounds(self, max_width: int, max_height: int):
        """
        Constrain rectangle to fit within video bounds.

        Args:
            max_width (int): Maximum width (video width)
            max_height (int): Maximum height (video height)
        """
        # Constrain position
        self.x = max(0, min(self.x, max_width - 1))
        self.y = max(0, min(self.y, max_height - 1))

        # Constrain size
        self.width = min(self.width, max_width - self.x)
        self.height = min(self.height, max_height - self.y)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert rectangle to dictionary for serialization.

        Returns:
            Dict[str, Any]: Rectangle data as dictionary
        """
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'name': self.name,
            'color': self.color
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rectangle':
        """
        Create rectangle from dictionary data.

        Args:
            data (Dict[str, Any]): Rectangle data

        Returns:
            Rectangle: New rectangle instance
        """
        rect = cls(
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            name=data['name']
        )
        rect.color = data.get('color', '#FF0000')
        return rect

    def copy(self) -> 'Rectangle':
        """
        Create a copy of this rectangle.

        Returns:
            Rectangle: New rectangle instance with same properties
        """
        return Rectangle.from_dict(self.to_dict())

    def __str__(self) -> str:
        """String representation of rectangle."""
        return f"Rectangle('{self.name}': {self.x},{self.y} {self.width}x{self.height})"

    def __repr__(self) -> str:
        """Detailed string representation of rectangle."""
        return (f"Rectangle(x={self.x}, y={self.y}, width={self.width}, "
                f"height={self.height}, name='{self.name}')")


class RectangleManager:
    """
    Manages a collection of crop rectangles with operations for creation,
    editing, validation, and persistence.
    """

    def __init__(self):
        """Initialize the rectangle manager."""
        self.rectangles: List[Rectangle] = []
        self.selected_rectangle: Optional[Rectangle] = None
        self.video_width = 0
        self.video_height = 0
        self.colors = [
            "#FF0000",  # Red
            "#00FF00",  # Green
            "#0000FF",  # Blue
            "#FFFF00",  # Yellow
            "#FF00FF",  # Magenta
            "#00FFFF",  # Cyan
            "#FFA500",  # Orange
            "#800080",  # Purple
            "#FFC0CB",  # Pink
            "#A52A2A"   # Brown
        ]
        self.color_index = 0

    def set_video_dimensions(self, width: int, height: int):
        """
        Set video dimensions for validation and coordinate conversion.

        Args:
            width (int): Video width in pixels
            height (int): Video height in pixels
        """
        self.video_width = width
        self.video_height = height

        # Constrain existing rectangles to new bounds
        for rect in self.rectangles:
            rect.constrain_to_bounds(width, height)

    def add_rectangle(self, x: int, y: int, width: int, height: int, name: str = "") -> Rectangle:
        """
        Add a new rectangle to the collection.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Width
            height (int): Height
            name (str): Optional name for the rectangle

        Returns:
            Rectangle: The created rectangle
        """
        if not name:
            name = f"region_{len(self.rectangles) + 1}"

        # Ensure unique name
        name = self._get_unique_name(name)

        # Create rectangle
        rect = Rectangle(x, y, width, height, name)

        # Assign color
        rect.color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1

        # Constrain to video bounds if dimensions are set
        if self.video_width > 0 and self.video_height > 0:
            rect.constrain_to_bounds(self.video_width, self.video_height)

        self.rectangles.append(rect)
        return rect

    def remove_rectangle(self, rectangle: Rectangle) -> bool:
        """
        Remove a rectangle from the collection.

        Args:
            rectangle (Rectangle): Rectangle to remove

        Returns:
            bool: True if rectangle was removed
        """
        if rectangle in self.rectangles:
            self.rectangles.remove(rectangle)
            if self.selected_rectangle == rectangle:
                self.selected_rectangle = None
            return True
        return False

    def get_rectangle_at_point(self, x: int, y: int) -> Optional[Rectangle]:
        """
        Find the topmost rectangle containing the given point.

        Args:
            x (int): X coordinate
            y (int): Y coordinate

        Returns:
            Optional[Rectangle]: Rectangle at point, or None
        """
        # Search in reverse order to get topmost rectangle
        for rect in reversed(self.rectangles):
            if rect.contains_point(x, y):
                return rect
        return None

    def select_rectangle(self, rectangle: Optional[Rectangle]):
        """
        Select a rectangle for editing.

        Args:
            rectangle (Optional[Rectangle]): Rectangle to select, or None to deselect
        """
        # Deselect previous
        if self.selected_rectangle:
            self.selected_rectangle.selected = False

        # Select new
        self.selected_rectangle = rectangle
        if rectangle:
            rectangle.selected = True

    def rename_rectangle(self, rectangle: Rectangle, new_name: str) -> bool:
        """
        Rename a rectangle with validation.

        Args:
            rectangle (Rectangle): Rectangle to rename
            new_name (str): New name

        Returns:
            bool: True if rename was successful
        """
        if not new_name or not new_name.strip():
            return False

        unique_name = self._get_unique_name(new_name.strip(), exclude=rectangle)
        rectangle.name = unique_name
        return True

    def get_all_names(self) -> List[str]:
        """
        Get list of all rectangle names.

        Returns:
            List[str]: List of rectangle names
        """
        return [rect.name for rect in self.rectangles]

    def validate_all_rectangles(self) -> List[str]:
        """
        Validate all rectangles and return list of issues.

        Returns:
            List[str]: List of validation error messages
        """
        errors = []

        if not self.rectangles:
            errors.append("No crop rectangles defined")
            return errors

        for i, rect in enumerate(self.rectangles):
            if not rect.is_valid():
                errors.append(f"Rectangle '{rect.name}' has invalid dimensions")

            if self.video_width > 0 and self.video_height > 0:
                if rect.x2 > self.video_width or rect.y2 > self.video_height:
                    errors.append(f"Rectangle '{rect.name}' extends beyond video bounds")

        # Check for duplicate names
        names = [rect.name for rect in self.rectangles]
        duplicates = set([name for name in names if names.count(name) > 1])
        for dup_name in duplicates:
            errors.append(f"Duplicate rectangle name: '{dup_name}'")

        return errors

    def clear_all(self):
        """Remove all rectangles."""
        self.rectangles.clear()
        self.selected_rectangle = None
        self.color_index = 0

    def get_crop_summary(self) -> Dict[str, Any]:
        """
        Get summary of all crop rectangles for processing.

        Returns:
            Dict[str, Any]: Summary data for video processing
        """
        return {
            'video_dimensions': {
                'width': self.video_width,
                'height': self.video_height
            },
            'rectangles': [rect.to_dict() for rect in self.rectangles],
            'count': len(self.rectangles)
        }

    def _get_unique_name(self, base_name: str, exclude: Optional[Rectangle] = None) -> str:
        """
        Generate a unique name based on the given base name.

        Args:
            base_name (str): Base name to make unique
            exclude (Optional[Rectangle]): Rectangle to exclude from name check

        Returns:
            str: Unique name
        """
        existing_names = set()
        for rect in self.rectangles:
            if rect != exclude:
                existing_names.add(rect.name)

        if base_name not in existing_names:
            return base_name

        # Add number suffix to make unique
        counter = 1
        while f"{base_name}_{counter}" in existing_names:
            counter += 1

        return f"{base_name}_{counter}"

    def __len__(self) -> int:
        """Return number of rectangles."""
        return len(self.rectangles)

    def __iter__(self):
        """Iterate over rectangles."""
        return iter(self.rectangles)

    def __getitem__(self, index: int) -> Rectangle:
        """Get rectangle by index."""
        return self.rectangles[index]