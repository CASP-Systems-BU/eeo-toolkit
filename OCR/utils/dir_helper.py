import os

def create_dir_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_files_in_directory(directory, extension="pdf"):
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")
    return [f for f in os.listdir(directory) if f.lower().endswith(extension)]

def is_file_or_dir_exist(path: str) -> bool:
    if os.path.exists(path):
        return True
    return False