"""
Main entry point for Video Processing Tools.

This script provides a unified interface to access both video processing programs:
1. Long Video Chopping - Segments videos into smaller chunks
2. Snippet Selection - Extracts snippets around specific timestamps

Author: Video Processing Project
"""

import sys
import os
from pathlib import Path

# Add shared modules to path
sys.path.append(str(Path(__file__).parent))

from shared.user_interface import get_choice_from_list, print_section_header


def main():
    """Main function providing menu to choose between programs."""
    try:
        print_section_header("Video Processing Tools")
        print("Welcome to the Video Processing Toolkit!")
        print("This toolkit provides two main video processing capabilities:\n")

        print("1. Long Video Chopping:")
        print("   - Segments long videos into smaller consecutive chunks")
        print("   - Specify desired chunk duration")
        print("   - Works with single videos or entire folders")
        print("   - Original files are never modified\n")

        print("2. Snippet Selection:")
        print("   - Extracts specific segments around timestamps of interest")
        print("   - Uses Excel file with timestamp data")
        print("   - Configurable before/after duration")
        print("   - Generates CSV reports with metadata\n")

        # Get user choice
        choice = get_choice_from_list(
            "Which tool would you like to use?",
            ["Long Video Chopping", "Snippet Selection", "Exit"]
        )

        if choice == "Long Video Chopping":
            print_section_header("Starting Long Video Chopping")
            try:
                # Import and run long video chopping
                from long_video_chopping import main as lvc_main
                lvc_main.main()
            except ImportError:
                print("Error: Long Video Chopping module not found.")
                print("Please ensure all required files are present.")
            except Exception as e:
                print(f"Error running Long Video Chopping: {e}")

        elif choice == "Snippet Selection":
            print_section_header("Starting Snippet Selection")
            try:
                # Import and run snippet selection
                from snippet_selection import main as ss_main
                ss_main.main()
            except ImportError:
                print("Error: Snippet Selection module not found.")
                print("Please ensure all required files are present.")
            except Exception as e:
                print(f"Error running Snippet Selection: {e}")

        elif choice == "Exit":
            print("Thank you for using Video Processing Tools!")
            return

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please check your installation and try again.")


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['cv2', 'moviepy', 'pandas', 'openpyxl', 'numpy']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("Error: Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install missing packages using:")
        print("pip install -r requirements.txt")
        return False

    return True


def print_system_info():
    """Print system and installation information."""
    print("System Information:")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script location: {Path(__file__).parent.absolute()}")


if __name__ == "__main__":
    # Optional: Check dependencies before running
    if "--check-deps" in sys.argv:
        print_section_header("Dependency Check")
        if check_dependencies():
            print("All required dependencies are installed.")
        sys.exit(0)

    # Optional: Print system info
    if "--info" in sys.argv:
        print_section_header("System Information")
        print_system_info()
        sys.exit(0)

    # Run main program
    main()