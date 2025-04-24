"""
Module: load_config.py

Provides utility functions to load and validate YAML configuration files for:
- Cell coordination (coordinates for cropping PDF cells)
- Generic YAML configurations
- Table and section mappings based on form type
Ensures file existence before parsing and returns structured dictionaries.
"""

import os
import yaml
from typing import Dict


def is_file_or_dir_exist(path: str) -> bool:
    """
    Check whether a file or directory exists at the given path.

    Args:
        path (str): Filesystem path to check.

    Returns:
        bool: True if the path exists, False otherwise.
    """
    if os.path.exists(path):
        return True
    return False


def load_cell_coordination_config(file_path: str) -> Dict:
    """
    Load the YAML config mapping cell identifiers to their PDF cropping coordinates.

    Args:
        file_path (str): Path to the cell coordination YAML file.

    Returns:
        Dict: Mapping of sections to cell coordinate dicts, or None if missing.
    """
    print(f"Log: Loading {file_path}...")
    if not is_file_or_dir_exist(file_path):
        print("Error: The specified config file does not exist.")
        return

    with open(file_path, "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


def load_yaml_config(file_path: str) -> Dict:
    """
    Load a YAML file and return its contents as a dictionary.

    Args:
        file_path (str): Path to the YAML configuration file.

    Returns:
        Dict: Parsed YAML content, or None if file is missing.
    """
    if not is_file_or_dir_exist(file_path):
        print("Error: The specified config file does not exist.")
        return

    with open(file_path, "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


def load_table_config(file_path: str, form_type: str) -> Dict:
    """
    Load table-specific configuration for a given form type from a YAML file.

    Args:
        file_path (str): Path to the YAML configuration file.
        form_type (str): Top-level key in YAML (e.g., 'eeo1', 'eeo5').

    Returns:
        Dict: Table configuration for the specified form type, or None if missing.
    """
    data = load_yaml_config(file_path)
    return data[form_type]


def load_section_config(file_path: str, form_type: str) -> Dict:
    """
    Load section-mapping configuration for a given form type from a YAML file.

    Args:
        file_path (str): Path to the YAML configuration file.
        form_type (str): Top-level key in YAML (e.g., 'eeo1', 'eeo5').

    Returns:
        Dict: Section configuration for the specified form type, or None if missing.
    """
    data = load_yaml_config(file_path)
    return data[form_type]
