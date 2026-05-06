"""
eeo4_type2_filter.py

Processes OCR-parsed JSON files of EEO-4 munis reports. Unlike the standard EEO-4,
munis forms have no cover page — all jurisdiction metadata (title, a, b, c sections)
lives on page 0 of each group file alongside the first table.

This script groups files by base filename, reads metadata from the first group, then
outputs one flat JSON per group file with the shared metadata attached — matching the
output format produced by eeo4_type1_filter.py and compatible with eeo4_handler.py.
"""

import glob
import json
import os
import re
from typing import List, Dict, Optional

from eeo4_type1_filter import (
    get_all_json_files,
    get_extracted_str,
    get_field_by_id,
    get_selected_government_type,
    get_selected_function,
    extract_cover_metadata,
    extract_group_data,
)


def get_base_filename(filepath: str) -> str:
    """
    Extract the base filename without the _groupN suffix or result extension.

    :param filepath: Full file path
    :return: Base filename for grouping files from the same document
    """
    filename = os.path.basename(filepath)
    filename = filename.replace("_cropped_result.json", "")
    filename = re.sub(r"_group\d+$", "", filename)
    return filename


if __name__ == "__main__":
    json_input_dir = input("Enter the input JSON directory: ")
    json_output_dir = input("Enter the output JSON directory: ")

    os.makedirs(json_output_dir, exist_ok=True)

    json_files = get_all_json_files(json_input_dir)

    # Collect only group files; there are no cover files for munis
    group_files: Dict[str, List[str]] = {}
    for json_file in json_files:
        filename = os.path.basename(json_file)
        if "_group" not in filename:
            continue
        base_name = get_base_filename(json_file)
        group_files.setdefault(base_name, []).append(json_file)

    processed = 0
    for base_name, groups in group_files.items():
        groups.sort()

        # Metadata lives on page 0 of every group — read from the first one
        with open(groups[0], "r") as f:
            first_group_json = json.load(f)
        cover_metadata = extract_cover_metadata(first_group_json)

        for group_path in groups:
            with open(group_path, "r") as f:
                group_json = json.load(f)

            group_data = extract_group_data(group_json)

            group_stem = os.path.basename(group_path).replace("_cropped_result.json", "")
            output_path = os.path.join(json_output_dir, group_stem + ".json")

            json_output: Dict = {
                "filename": group_stem,
                "jurisdiction_name": cover_metadata.get("jurisdiction_name", ""),
                "address": cover_metadata.get("address", ""),
                "city": cover_metadata.get("city", ""),
                "county": cover_metadata.get("county", ""),
                "state": cover_metadata.get("state", ""),
                "zipcode": cover_metadata.get("zipcode", ""),
                "control_number": cover_metadata.get("control_number", ""),
                "reporting_year": cover_metadata.get("reporting_year", "-1"),
                "government_type": cover_metadata.get("government_type", ""),
                "functions_other_description": cover_metadata.get("functions_other_description", ""),
                "function_number": group_data.get("function_number", 0),
                "government_function": group_data.get("government_function", ""),
                "departments_included": group_data.get("departments_included", ""),
                "departments_not_included": group_data.get("departments_not_included", ""),
                "remarks": group_data.get("remarks", ""),
                "table_a": group_data.get("table_a", []),
                "table_b": group_data.get("table_b", []),
                "table_c": group_data.get("table_c", []),
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_output, f, indent=4)

            print(f"Processed: {group_stem}.json")
            processed += 1

    print(f"\nProcessing complete. {processed} files written to: {json_output_dir}")
