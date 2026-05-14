"""
dir_helper.py

Utility module for basic file system operations commonly used across OCR pipelines and preprocessing workflows.
Provides helper functions to safely create directories, list files by extension, and check the existence of files or folders.
"""

import glob
import os

def create_dir_if_not_exists(directory):
    """
    Create a directory if it does not already exist.

    Args:
        directory (str): Path of the directory to create.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_files_in_directory(directory, extension="pdf"):
    """
    Retrieve a list of files in a directory that match a specific file extension.

    Args:
        directory (str): Path to the directory to scan.
        extension (str): File extension to filter by (default is 'pdf').

    Returns:
        List[str]: List of file names matching the extension.

    Raises:
        FileNotFoundError: If the provided directory does not exist.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")
    return [f for f in os.listdir(directory) if f.lower().endswith(extension)]


def is_file_or_dir_exist(path: str) -> bool:
    """
    Check if a given file or directory exists.

    Args:
        path (str): Path to the file or directory.

    Returns:
        bool: True if the path exists, otherwise False.
    """
    return os.path.exists(path)


def get_all_json_files(path: str) -> list:
    """
    Recursively retrieve all JSON files under the specified directory.

    Args:
        path (str): Root directory in which to search for JSON files.

    Returns:
        List[str]: Sorted list of file paths to all found JSON files.
    """
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    dirs.append(path)
    json_files = []
    for d in dirs:
        json_files.extend(glob.glob(os.path.join(d, "*.json")))
    json_files.sort()
    return json_files
