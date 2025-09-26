"""
Adjust Brightness Module

This module provides a GUI-based tool for adjusting the brightness and contrast
of videos. It supports both single video files and batch processing of directories.

Key Features:
- Interactive GUI with real-time video preview
- Brightness and contrast adjustment sliders
- Intelligent brightness suggestions based on video analysis
- Batch processing for multiple videos
- Quality-preserving video processing
- Original file protection (creates copies only)

Author: Video Processing Project
"""

# Version information
__version__ = "1.0.0"
__author__ = "Video Processing Project"

# Import main components for easier access
try:
    from .main import main
    from .video_processor import VideoProcessor
    from .brightness_analyzer import BrightnessAnalyzer
    from .gui_components import AdjustBrightnessGUI
except ImportError:
    # Handle relative imports when running directly
    pass

__all__ = [
    'main',
    'VideoProcessor',
    'BrightnessAnalyzer',
    'AdjustBrightnessGUI'
]