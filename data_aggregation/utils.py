import os

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
    files = [f for f in os.listdir(directory) if f.lower().endswith(extension)]
    files.sort()
    return files