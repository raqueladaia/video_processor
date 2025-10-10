"""
Common user interface utilities.

This module provides shared UI functionality including input validation,
user prompts, and progress display.
"""

import os
from pathlib import Path
from typing import List, Optional, Union


def get_user_input(prompt: str, validation_func=None, error_message: str = "Invalid input. Please try again.") -> str:
    """
    Get user input with optional validation.

    Args:
        prompt (str): Prompt to display to user
        validation_func: Function to validate input (should return bool)
        error_message (str): Message to show on validation failure

    Returns:
        str: Valid user input
    """
    while True:
        user_input = input(prompt).strip()

        if validation_func is None or validation_func(user_input):
            return user_input
        else:
            print(error_message)


def get_file_path(prompt: str, must_exist: bool = True) -> str:
    """
    Get a file path from user with validation.

    Args:
        prompt (str): Prompt to display to user
        must_exist (bool): Whether the file must already exist

    Returns:
        str: Valid file path
    """
    def validate_path(path: str) -> bool:
        if not path:
            return False

        path_obj = Path(path)

        if must_exist:
            return path_obj.exists()
        else:
            # For new files, check if parent directory exists
            return path_obj.parent.exists()

    error_msg = f"Path must {'exist' if must_exist else 'be in an existing directory'}."
    return get_user_input(prompt, validate_path, error_msg)


def get_directory_path(prompt: str, must_exist: bool = True) -> str:
    """
    Get a directory path from user with validation.

    Args:
        prompt (str): Prompt to display to user
        must_exist (bool): Whether the directory must already exist

    Returns:
        str: Valid directory path
    """
    def validate_directory(path: str) -> bool:
        if not path:
            return False

        path_obj = Path(path)

        if must_exist:
            return path_obj.exists() and path_obj.is_dir()
        else:
            # For new directories, check if parent exists
            return path_obj.parent.exists()

    error_msg = f"Directory must {'exist' if must_exist else 'be in an existing location'}."
    return get_user_input(prompt, validate_directory, error_msg)


def get_positive_number(prompt: str, number_type=float) -> Union[int, float]:
    """
    Get a positive number from user.

    Args:
        prompt (str): Prompt to display to user
        number_type: Type of number to get (int or float)

    Returns:
        Union[int, float]: Valid positive number
    """
    def validate_number(value: str) -> bool:
        try:
            num = number_type(value)
            return num > 0
        except ValueError:
            return False

    error_msg = f"Please enter a positive {number_type.__name__}."
    value_str = get_user_input(prompt, validate_number, error_msg)
    return number_type(value_str)


def get_yes_no_choice(prompt: str, default: Optional[bool] = None) -> bool:
    """
    Get a yes/no choice from user.

    Args:
        prompt (str): Prompt to display to user
        default (Optional[bool]): Default choice if user just presses Enter

    Returns:
        bool: True for yes, False for no
    """
    # Add default indication to prompt
    if default is not None:
        default_str = "Y/n" if default else "y/N"
        full_prompt = f"{prompt} [{default_str}]: "
    else:
        full_prompt = f"{prompt} [y/n]: "

    def validate_choice(value: str) -> bool:
        if not value and default is not None:
            return True
        return value.lower() in ['y', 'yes', 'n', 'no']

    error_msg = "Please enter 'y' for yes or 'n' for no."
    choice = get_user_input(full_prompt, validate_choice, error_msg)

    # Handle default case
    if not choice and default is not None:
        return default

    return choice.lower() in ['y', 'yes']


def get_choice_from_list(prompt: str, choices: List[str], show_numbers: bool = True) -> str:
    """
    Get user choice from a list of options.

    Args:
        prompt (str): Prompt to display to user
        choices (List[str]): List of available choices
        show_numbers (bool): Whether to show numbers for each choice

    Returns:
        str: Selected choice
    """
    print(prompt)

    if show_numbers:
        for i, choice in enumerate(choices, 1):
            print(f"{i}. {choice}")

        def validate_choice(value: str) -> bool:
            try:
                num = int(value)
                return 1 <= num <= len(choices)
            except ValueError:
                return False

        error_msg = f"Please enter a number between 1 and {len(choices)}."
        choice_num = get_user_input("Enter your choice: ", validate_choice, error_msg)
        return choices[int(choice_num) - 1]
    else:
        for choice in choices:
            print(f"- {choice}")

        def validate_choice(value: str) -> bool:
            return value in choices

        error_msg = f"Please enter one of: {', '.join(choices)}"
        return get_user_input("Enter your choice: ", validate_choice, error_msg)


def get_multiple_choices_from_list(prompt: str, choices: List[str], allow_all: bool = True) -> List[str]:
    """
    Get multiple user choices from a list of options.

    User can select individual items by number, ranges (e.g., 1-3), or 'all'.

    Args:
        prompt (str): Prompt to display to user
        choices (List[str]): List of available choices
        allow_all (bool): Whether to allow 'all' as an option

    Returns:
        List[str]: List of selected choices
    """
    print(prompt)
    print("\nAvailable options:")
    for i, choice in enumerate(choices, 1):
        print(f"{i}. {choice}")

    if allow_all:
        print("\nYou can enter:")
        print("  - Individual numbers (e.g., '1')")
        print("  - Multiple numbers separated by commas (e.g., '1,3,5')")
        print("  - Ranges (e.g., '1-3' for items 1 through 3)")
        print("  - 'all' to select all options")
    else:
        print("\nYou can enter:")
        print("  - Individual numbers (e.g., '1')")
        print("  - Multiple numbers separated by commas (e.g., '1,3,5')")
        print("  - Ranges (e.g., '1-3' for items 1 through 3)")

    def validate_and_parse(value: str) -> Optional[List[int]]:
        """
        Validate and parse user input into list of indices.

        Returns None if invalid, list of indices (1-based) if valid.
        """
        value = value.strip().lower()

        # Handle 'all' option
        if allow_all and value == 'all':
            return list(range(1, len(choices) + 1))

        # Parse comma-separated values
        selected_indices = []
        parts = value.split(',')

        try:
            for part in parts:
                part = part.strip()

                # Check if it's a range (e.g., '1-3')
                if '-' in part:
                    range_parts = part.split('-')
                    if len(range_parts) != 2:
                        return None
                    start = int(range_parts[0].strip())
                    end = int(range_parts[1].strip())

                    if start < 1 or end > len(choices) or start > end:
                        return None

                    selected_indices.extend(range(start, end + 1))
                else:
                    # Single number
                    num = int(part)
                    if num < 1 or num > len(choices):
                        return None
                    selected_indices.append(num)

            # Remove duplicates and sort
            selected_indices = sorted(list(set(selected_indices)))
            return selected_indices

        except ValueError:
            return None

    # Get and validate input
    while True:
        user_input = input("Enter your selection: ").strip()
        parsed_indices = validate_and_parse(user_input)

        if parsed_indices is not None:
            # Convert indices to actual choices
            selected_choices = [choices[i - 1] for i in parsed_indices]
            print(f"\nSelected {len(selected_choices)} option(s): {', '.join(selected_choices)}")
            return selected_choices
        else:
            if allow_all:
                print("Invalid input. Please enter numbers (1-" + str(len(choices)) + "), ranges, or 'all'.")
            else:
                print("Invalid input. Please enter numbers (1-" + str(len(choices)) + ") or ranges.")


def print_progress(current: int, total: int, description: str = "Processing"):
    """
    Print a simple progress indicator.

    Args:
        current (int): Current progress count
        total (int): Total count
        description (str): Description of what's being processed
    """
    percentage = (current / total) * 100 if total > 0 else 0
    print(f"{description}: {current}/{total} ({percentage:.1f}%)")


def print_section_header(title: str):
    """
    Print a formatted section header.

    Args:
        title (str): Title of the section
    """
    print(f"\n{'=' * 50}")
    print(f"{title}")
    print(f"{'=' * 50}")


def print_file_info(file_path: str, size_mb: Optional[float] = None, duration: Optional[float] = None):
    """
    Print formatted file information.

    Args:
        file_path (str): Path to the file
        size_mb (Optional[float]): File size in MB
        duration (Optional[float]): Duration in seconds (for videos)
    """
    filename = Path(file_path).name
    print(f"File: {filename}")

    if size_mb is not None:
        print(f"Size: {size_mb} MB")

    if duration is not None:
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        print(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")

    print(f"Path: {file_path}")
    print("-" * 40)