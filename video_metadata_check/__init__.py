"""
Video Metadata Check Module

This module provides functionality to extract and analyze video metadata,
including frame rates, duration, resolution, file size, and codec information.
Supports both individual video analysis and comparison of multiple videos.
"""

__version__ = "1.0.0"
__author__ = "Video Processing Project"

from .metadata_extractor import VideoMetadataExtractor
from .metadata_comparator import VideoMetadataComparator
from .report_generator import ReportGenerator

__all__ = [
    'VideoMetadataExtractor',
    'VideoMetadataComparator',
    'ReportGenerator'
]
