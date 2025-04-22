import os
import hashlib
from collections import defaultdict


def get_file_hash(file_path, chunk_size=4096):
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(directory, file_extensions=None):
    """Find duplicate files in a directory based on content hash, grouped by file type."""

    # Step 1: Group files by size and extension
    size_dict = defaultdict(lambda: defaultdict(list))  # {file_extension: {size: [file_paths]}}

    for root, _, files in os.walk(directory):
        for file in files:
            ext = file.lower().split('.')[-1]
            if file_extensions and f".{ext}" not in file_extensions:
                continue  # Skip file if it's not in the specified extensions

            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            size_dict[ext][file_size].append(file_path)

    # Step 2: Compute hashes only for files with the same size and extension
    hash_dict = defaultdict(lambda: defaultdict(list))  # {file_extension: {hash: [file_paths]}}

    for ext, size_groups in size_dict.items():
        for file_list in size_groups.values():
            if len(file_list) > 1:  # Only check files that have duplicates in size
                for file_path in file_list:
                    file_hash = get_file_hash(file_path)
                    hash_dict[ext][file_hash].append(file_path)

    # Step 3: Collect duplicate sets
    duplicates = {ext: [files for files in hashes.values() if len(files) > 1] for ext, hashes in hash_dict.items()}

    return duplicates

def delete_duplicates(duplicates):
    if any(duplicates.values()):
        print("\nDuplicate Files Found:")
        for ext, dup_groups in duplicates.items():
            if dup_groups:
                print(f"\nDuplicates for *.{ext}:")
                for idx, dup_group in enumerate(dup_groups, start=1):
                    print(f"  Group {idx}:")
                    print(f"    Kept: {dup_group[0]}")
                    for file in dup_group[1:]:
                        try:
                            os.remove(file)
                            print(f"    Deleted: {file}")
                        except Exception as e:
                            print(f"    Failed to delete {file}: {e}")
    else:
        print("No duplicate files found.")

if __name__ == "__main__":
    directory = input("Enter the directory to scan for duplicates: ").strip()
    file_extensions = input(
        "Enter file extensions to check (comma-separated, e.g., .pdf,.xlsx,.csv,.png), or leave blank for all: ").strip()

    # Convert user input into a set of file extensions
    file_extensions = set(file_extensions.lower().split(',')) if file_extensions else None

    duplicates = find_duplicates(directory, file_extensions)

    delete_duplicates(duplicates)
