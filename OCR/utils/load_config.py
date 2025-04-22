import os
import yaml
from typing import Dict


def is_file_or_dir_exist(path: str) -> bool:
    if os.path.exists(path):
        return True
    return False


def load_cell_coordination_config(file_path: str) -> Dict:
    """
    Load the yaml config file of the cell coordination for cutting.
    """
    print(f"Log: Loading {file_path}...")
    if not is_file_or_dir_exist(file_path):
        print("Error: The specified config file does not exist.")
        return

    with open(file_path, "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


def load_yaml_config(file_path: str) -> Dict:
    if not is_file_or_dir_exist(file_path):
        print("Error: The specified config file does not exist.")
        return

    with open(file_path, "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


def load_table_config(file_path: str, form_type: str) -> Dict:
    data = load_yaml_config(file_path)
    return data[form_type]


def load_section_config(file_path: str, form_type: str) -> Dict:
    data = load_yaml_config(file_path)
    return data[form_type]
