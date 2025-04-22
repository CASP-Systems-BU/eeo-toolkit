import os
import shutil

def classify_files_by_extension(directory):
    """
    Classifies files in the specified directory based on their extensions
    and moves them into corresponding subdirectories.
    """
    if not os.path.exists(directory):
        print("Error: The specified directory does not exist.")
        return

    # Process each file in the directory
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)

        # Skip directories
        if os.path.isdir(file_path):
            continue

        # Get file extension (excluding the dot) and handle files without extensions
        file_extension = os.path.splitext(file)[1][1:].lower()
        if not file_extension:
            file_extension = "No_Extension"

        # Create a directory for the extension if it doesn't exist
        extension_folder = os.path.join(directory, file_extension)
        os.makedirs(extension_folder, exist_ok=True)

        # Move the file to its respective folder
        shutil.move(file_path, os.path.join(extension_folder, file))
        print(f"Moved: {file} -> {extension_folder}")

    print("\nFile classification by extension completed.")

# Example usage
if __name__ == "__main__":
    target_directory = input("Enter the directory to organize: ").strip()
    classify_files_by_extension(target_directory)
