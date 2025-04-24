"""
classify.py

This script organizes files in a given directory by file type (based on extension).
Each file is moved into a subdirectory named after its extension (e.g., `.pdf` files go into a `pdf/` folder).
Files with no extension are moved into a `No_Extension/` folder.

In the context of OCR preprocessing, this script is useful for filtering out unsupported file types like `.csv` or `.xlsx`
before running the OCR pipeline, which only accepts form-structured documents (e.g., `.pdf`, `.png`).
"""

import os
import shutil

def classify_files_by_extension(directory):
    """
    Classifies files in the specified directory based on their extensions
    and moves them into corresponding subdirectories.

    Args:
        directory (str): Path of the directory containing files to classify.
    """
    if not os.path.exists(directory):
        print("Error: The specified directory does not exist.")
        return

    # Iterate over each file in the directory
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)

        # Skip subdirectories
        if os.path.isdir(file_path):
            continue

        # Extract file extension (without the dot), normalize to lowercase
        file_extension = os.path.splitext(file)[1][1:].lower()

        # If no extension, assign a default folder name
        if not file_extension:
            file_extension = "No_Extension"

        # Prepare the target subdirectory for this extension
        extension_folder = os.path.join(directory, file_extension)
        os.makedirs(extension_folder, exist_ok=True)

        # Move the file to the corresponding extension folder
        shutil.move(file_path, os.path.join(extension_folder, file))
        print(f"Moved: {file} -> {extension_folder}")

    print("\nFile classification by extension completed.")

# Example usage
if __name__ == "__main__":
    # Prompt user to enter the directory containing files to be organized
    target_directory = input("Enter the directory to organize: ").strip()
    classify_files_by_extension(target_directory)
