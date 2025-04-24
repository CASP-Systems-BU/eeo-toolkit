"""
deduplicate.py

This script scans a given directory (recursively) to detect and optionally delete duplicate files based on their contents.
It compares files using SHA-256 hashing and groups duplicates by file extension and content hash.
Users can specify file types of interest or scan all file types.
"""

import os
import hashlib
from collections import defaultdict


def get_file_hash(file_path, chunk_size=4096):
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path (str): Path to the file.
        chunk_size (int): Size of the chunk to read the file in bytes. Default is 4096.

    Returns:
        str: The computed hash string.
    """
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(directory, file_extensions=None):
    """
    Find duplicate files in a directory by comparing their content hashes.

    Args:
        directory (str): Path of the directory to scan.
        file_extensions (set[str], optional): Set of allowed file extensions (e.g., {'.csv', '.txt'}). If None, all files are included.

    Returns:
        dict: A dictionary mapping file extensions to lists of duplicate file groups.
    """

    # Step 1: Group files by file extension and size
    size_dict = defaultdict(lambda: defaultdict(list))  # {file_extension: {file_size: [file_paths]}}

    for root, _, files in os.walk(directory):
        for file in files:
            ext = file.lower().split('.')[-1]
            if file_extensions and f".{ext}" not in file_extensions:
                continue  # Skip file if its extension is not in the specified list

            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            size_dict[ext][file_size].append(file_path)

    # Step 2: For files with same extension and size, compute and group by content hash
    hash_dict = defaultdict(lambda: defaultdict(list))  # {file_extension: {hash: [file_paths]}}

    for ext, size_groups in size_dict.items():
        for file_list in size_groups.values():
            if len(file_list) > 1:  # Only process if multiple files share same size
                for file_path in file_list:
                    file_hash = get_file_hash(file_path)
                    hash_dict[ext][file_hash].append(file_path)

    # Step 3: Collect and return duplicate file groups (length > 1)
    duplicates = {ext: [files for files in hashes.values() if len(files) > 1] for ext, hashes in hash_dict.items()}

    return duplicates


def delete_duplicates(duplicates):
    """
    Print and delete duplicate files, keeping one file per group.

    Args:
        duplicates (dict): Dictionary of duplicate files grouped by extension and content hash.
    """
    if any(duplicates.values()):
        print("\nDuplicate Files Found:")
        for ext, dup_groups in duplicates.items():
            if dup_groups:
                print(f"\nDuplicates for *.{ext}:")
                for idx, dup_group in enumerate(dup_groups, start=1):
                    print(f"  Group {idx}:")
                    print(f"    Kept: {dup_group[0]}")
                    for file in dup_group[1:]:  # Keep the first file, delete the rest
                        try:
                            os.remove(file)
                            print(f"    Deleted: {file}")
                        except Exception as e:
                            print(f"    Failed to delete {file}: {e}")
    else:
        print("No duplicate files found.")


if __name__ == "__main__":
    # Prompt user for directory and optional file extensions
    directory = input("Enter the directory to scan for duplicates: ").strip()
    file_extensions = input(
        "Enter file extensions to check (comma-separated, e.g., .pdf,.xlsx,.csv,.png), or leave blank for all: ").strip()

    # Parse user input into a set of file extensions or None
    file_extensions = set(file_extensions.lower().split(',')) if file_extensions else None

    # Detect and delete duplicates
    duplicates = find_duplicates(directory, file_extensions)
    delete_duplicates(duplicates)
