"""
Main entry point for adjust brightness program.

This program provides a GUI-based tool for adjusting the brightness and contrast
of videos. It supports both single video files and batch processing of directories
containing multiple videos.

Key Features:
- Interactive GUI with real-time video preview
- Brightness and contrast adjustment sliders
- Intelligent brightness suggestions based on video analysis
- Batch processing for multiple videos
- Quality-preserving video processing using FFmpeg
- Original file protection (creates copies only)

Author: Video Processing Project
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path to import shared modules
sys.path.append(str(Path(__file__).parent.parent))

from shared.user_interface import print_section_header


def check_gui_dependencies():
    """
    Check if GUI dependencies are available.

    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    missing_deps = []

    # Check tkinter availability
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter")

    # Check PIL/Pillow availability
    try:
        from PIL import Image, ImageTk
    except ImportError:
        missing_deps.append("Pillow (PIL)")

    # Check OpenCV availability
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")

    # Check subprocess availability (should be built-in)
    try:
        import subprocess
    except ImportError:
        missing_deps.append("subprocess (built-in module)")

    # Check numpy availability
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")

    if missing_deps:
        print("Error: Missing required dependencies for GUI:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install missing dependencies:")
        if "tkinter" in missing_deps:
            print("  - tkinter: Usually included with Python, but may need to be installed separately on some systems")
        if "Pillow (PIL)" in missing_deps:
            print("  - Pillow: pip install Pillow")
        if "opencv-python" in missing_deps:
            print("  - OpenCV: pip install opencv-python")
        if "subprocess (built-in module)" in missing_deps:
            print("  - subprocess: This should be included with Python")
        if "numpy" in missing_deps:
            print("  - NumPy: pip install numpy")
        print("\nOr install all requirements: pip install -r requirements.txt")
        return False

    return True


def check_ffmpeg_availability():
    """
    Check if FFmpeg is available for video processing.

    Returns:
        bool: True if FFmpeg is available, False otherwise
    """
    try:
        import subprocess
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("Warning: FFmpeg is not installed or not available in system PATH.")
        print("FFmpeg is required for video processing.")
        print("Please install FFmpeg and ensure it's available in your system PATH.")
        print("Download from: https://ffmpeg.org/download.html")
        return False
    except Exception:
        print("Warning: Could not verify FFmpeg installation.")
        print("Video processing may not work properly.")
        return False


def main():
    """Main function for adjust brightness program."""
    print_section_header("Video Brightness Adjustment Tool")
    print("This tool provides a GUI interface for adjusting video brightness and contrast.")
    print("Features include real-time preview, intelligent suggestions, and batch processing.")
    print("Original videos are never modified - only copies are created.\n")

    try:
        # Check dependencies
        print("Checking dependencies...")

        if not check_gui_dependencies():
            print("\nCannot start the application due to missing dependencies.")
            return False

        # Check FFmpeg (warning only, not critical)
        ffmpeg_available = check_ffmpeg_availability()
        if ffmpeg_available:
            print("FFmpeg detected - video processing will be optimized.")
        else:
            print("FFmpeg not detected - proceeding with basic processing.")

        print("All required dependencies are available.")
        print("\nStarting GUI application...")

        # Import and start GUI
        try:
            from .gui_components import AdjustBrightnessGUI
        except ImportError:
            # Handle relative imports when running directly
            from gui_components import AdjustBrightnessGUI

        # Create and run the GUI application
        app = AdjustBrightnessGUI()
        app.run()

        print("Application closed.")
        return True

    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
        return False
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please check your installation and try again.")
        return False


def run_command_line_mode():
    """
    Alternative command-line mode for systems without GUI support.

    This provides basic functionality without the GUI interface.
    """
    print("GUI mode not available. Command-line mode not yet implemented.")
    print("Please install GUI dependencies to use this tool.")
    return False


if __name__ == "__main__":
    # Check if GUI mode is requested or if running directly
    if "--cli" in sys.argv or "--command-line" in sys.argv:
        success = run_command_line_mode()
    else:
        success = main()

    # Exit with appropriate code
    sys.exit(0 if success else 1)