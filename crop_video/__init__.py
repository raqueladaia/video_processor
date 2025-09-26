"""
Crop Video Module

This module provides a GUI-based tool for cropping videos by drawing rectangular
regions on video frames. It supports multi-region cropping with custom naming
and batch processing for directories.

Key Features:
- Interactive GUI for drawing crop rectangles on video frames
- Multi-region support with custom naming for each rectangle
- Batch processing for single videos or entire directories
- Quality-preserving video processing using FFmpeg
- Output organization into named folders per crop region
- Save/load crop configurations for reuse
- Original file protection (creates copies only)

Author: Video Processing Project
"""

# Version information
__version__ = "1.0.0"
__author__ = "Video Processing Project"

# Import main components for easier access
try:
    from .main import main
    from .video_processor import CropVideoProcessor
    from .rectangle_manager import Rectangle, RectangleManager
    from .gui_components import CropVideoGUI
    from .crop_data import CropDataManager
except ImportError:
    # Handle relative imports when running directly
    pass

__all__ = [
    'main',
    'CropVideoProcessor',
    'Rectangle',
    'RectangleManager',
    'CropVideoGUI',
    'CropDataManager'
]