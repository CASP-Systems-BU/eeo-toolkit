"""
eeo4_type1_filter.py

This script processes OCR-parsed JSON files of EEO-4 reports, extracting and cleaning key metadata for
government function-level reporting. EEO-4 forms are split into a cover file (agency metadata) and
multiple group files (one per government function). This script outputs one flat JSON per group file,
attaching the shared cover metadata to each.

---

Key Features:
- Attaches cover file metadata to each group file
- Extracts metadata including jurisdiction name, city, county, state, ZIP code, and reporting year
- Identifies which government function each group represents
- Retrieves form tables (A, B, C) with employment data
- Extracts department/agency information and remarks
- Standardizes field formats (e.g., uppercase county)
- Writes one normalized JSON per government function report to the output directory
"""

import glob
import json
import os
import re
from typing import List, Dict, Optional


# === Const Starts ===
# Government function names
GOVERNMENT_FUNCTIONS = [
    "FINANCIAL ADMINISTRATION/GENERAL CONTROL",
    "STREETS AND HIGHWAYS",
    "PUBLIC WELFARE",
    "POLICE PROTECTION",
    "FIRE PROTECTION",
    "NATURAL RESOURCES/PARKS AND RECREATION",
    "HOSPITALS",
    "HEALTH",
    "HOUSING",
    "COMMUNITY DEVELOPMENT",
    "CORRECTIONS",
    "UTILITIES AND TRANSPORTATION",
    "SANITATION AND SEWAGE",
    "EMPLOYMENT SECURITY",
    "OTHER"
]

# Government type options
GOVERNMENT_TYPES = [
    "State",
    "County",
    "City",
    "Township",
    "Special District",
    "Other"
]
# === Const Ends ===


def get_all_json_files(path: str) -> List[str]:
    """
    Recursively retrieve all JSON files under the specified directory.

    :param path: Root directory in which to search for JSON files
    :return: Sorted list of file paths to all found JSON files
    """
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    dirs.append(path)
    json_files = []
    for d in dirs:
        json_files.extend(glob.glob(os.path.join(d, "*.json")))
    json_files.sort()
    return json_files


def get_extracted_str(content) -> str:
    """
    Extract the recognized string from an OCR content list.

    :param content: OCR 'content' list where index 1 holds the recognized text if present
    :return: The extracted string, or an empty string if unavailable
    """
    if isinstance(content, list) and len(content) > 1:
        return content[1]
    return ""


def get_field_by_id(json_data: List[Dict], field_id: str) -> Optional[Dict]:
    """
    Find a field in the JSON data by its 'id' value.

    :param json_data: List of field dictionaries from OCR JSON
    :param field_id: The 'id' value to search for
    :return: The matching field dictionary, or None if not found
    """
    for field in json_data:
        if field.get("id") == field_id:
            return field
    return None


def get_selected_government_type(json_data: List[Dict]) -> str:
    """
    Determine which government type is selected from checkbox data.

    :param json_data: List of field dictionaries from OCR JSON
    :return: The selected government type, or empty string if none selected
    """
    # Find the checkbox version of TYPE_OF_GOVERNMENT (has dict content)
    for field in json_data:
        if field.get("id") == "a-TYPE_OF_GOVERNMENT":
            content = field.get("content", {})
            if isinstance(content, dict):
                for gov_type in GOVERNMENT_TYPES:
                    if content.get(gov_type, False):
                        return gov_type
    return ""


def get_selected_function(json_data: List[Dict]) -> tuple:
    """
    Determine which government function this group represents.

    :param json_data: List of field dictionaries from OCR JSON
    :return: Tuple of (function_number, function_name) where function_number is 1-indexed
    """
    for field in json_data:
        if field.get("id") == "function-FUNCTION":
            content = field.get("content", [])
            if isinstance(content, list) and len(content) > 0:
                func_text = content[0]
                func_name = ""
                func_number = 0

                # Try to extract function number from "Function X - NAME" pattern
                func_num_match = re.search(r"Function\s*(\d+)", func_text, re.IGNORECASE)
                if func_num_match:
                    func_number = int(func_num_match.group(1))

                # Extract function name after the dash — OCR produces inconsistent spacing around
                # dashes, so each variant is tried in order from most to least specific
                if " - - " in func_text:
                    func_name = func_text.split(" - - ", 1)[1].strip()
                elif " - " in func_text:
                    func_name = func_text.split(" - ", 1)[1].strip()
                elif "- " in func_text:
                    func_name = func_text.split("- ", 1)[1].strip()
                elif " -" in func_text:
                    func_name = func_text.split(" -", 1)[1].strip()
                elif "-" in func_text:
                    func_name = func_text.split("-", 1)[1].strip()
                else:
                    func_name = func_text

                # If we didn't get a function number from the text, try to match by name
                if func_number == 0 and func_name:
                    # Try exact match first
                    func_name_upper = func_name.upper()
                    for i, gf in enumerate(GOVERNMENT_FUNCTIONS):
                        if gf == func_name_upper:
                            func_number = i + 1  # 1-indexed
                            break
                    # If no exact match, try partial match
                    if func_number == 0:
                        for i, gf in enumerate(GOVERNMENT_FUNCTIONS):
                            if gf in func_name_upper or func_name_upper in gf:
                                func_number = i + 1
                                break

                return (func_number, func_name)
    return (0, "")


def extract_cover_metadata(json_data: List[Dict]) -> Dict:
    """
    Extract metadata from a cover JSON file.

    :param json_data: List of field dictionaries from cover OCR JSON
    :return: Dictionary containing extracted cover metadata
    """
    metadata = {}

    # Extract jurisdiction name
    name_field = get_field_by_id(json_data, "b-NAME")
    if name_field:
        metadata["jurisdiction_name"] = get_extracted_str(name_field.get("content", []))

    # Extract address
    address_field = get_field_by_id(json_data, "b-ADDRESS")
    if address_field:
        metadata["address"] = get_extracted_str(address_field.get("content", []))

    # Extract city
    city_field = get_field_by_id(json_data, "b-CITY")
    if city_field:
        metadata["city"] = get_extracted_str(city_field.get("content", []))

    # Extract county (uppercase)
    county_field = get_field_by_id(json_data, "b-COUNTY")
    if county_field:
        metadata["county"] = get_extracted_str(county_field.get("content", [])).upper()

    # Extract state
    state_field = get_field_by_id(json_data, "b-STATE")
    if state_field:
        metadata["state"] = get_extracted_str(state_field.get("content", []))

    # Extract ZIP code
    zip_field = get_field_by_id(json_data, "b-ZIPCODE")
    if zip_field:
        metadata["zipcode"] = get_extracted_str(zip_field.get("content", []))

    # Extract control number and reporting year
    title_field = get_field_by_id(json_data, "title-CONTROL_NUMBER_YEAR")
    if title_field:
        content = title_field.get("content", [])
        for item in content:
            if "Control Number" in item:
                match = re.search(r"Control Number[:\s]*(\d+)", item)
                if match:
                    metadata["control_number"] = match.group(1)
            if "Reporting Year" in item:
                match = re.search(r"Reporting Year[:\s]*(\d{4})", item)
                if match:
                    metadata["reporting_year"] = match.group(1)

    # Extract government type
    metadata["government_type"] = get_selected_government_type(json_data)

    # Extract "Other" specification for government type
    other_field = get_field_by_id(json_data, "c-FUNCTIONS_OTHER")
    if other_field:
        content = other_field.get("content", [])
        # Skip the header line and join the rest
        if len(content) > 1:
            metadata["functions_other_description"] = " ".join(content[1:])

    return metadata


def extract_group_data(json_data: List[Dict]) -> Dict:
    """
    Extract data from a group JSON file.

    :param json_data: List of field dictionaries from group OCR JSON
    :return: Dictionary containing extracted group data
    """
    group_data = {}

    # Extract departments included
    dept_included_field = get_field_by_id(json_data, "e-DEPARTMENTS_AGENCIES_INCLUDED")
    if dept_included_field:
        content = dept_included_field.get("content", [])
        # Skip header line if present
        if len(content) > 1:
            group_data["departments_included"] = " ".join(content[1:])
        else:
            group_data["departments_included"] = ""

    # Extract departments not included
    dept_excluded_field = get_field_by_id(json_data, "f-DEPARTMENTS_AGENCIES_NOT_INCLUDED")
    if dept_excluded_field:
        content = dept_excluded_field.get("content", [])
        if len(content) > 1:
            group_data["departments_not_included"] = " ".join(content[1:])
        else:
            group_data["departments_not_included"] = ""

    # Extract remarks
    remarks_field = get_field_by_id(json_data, "g-REMARKS")
    if remarks_field:
        content = remarks_field.get("content", [])
        if len(content) > 1:
            group_data["remarks"] = " ".join(content[1:])
        else:
            group_data["remarks"] = ""

    # Extract tables
    table_a_field = get_field_by_id(json_data, "table-A")
    if table_a_field:
        group_data["table_a"] = table_a_field.get("content", [])

    table_b_field = get_field_by_id(json_data, "table-B")
    if table_b_field:
        group_data["table_b"] = table_b_field.get("content", [])

    table_c_field = get_field_by_id(json_data, "table-C")
    if table_c_field:
        group_data["table_c"] = table_c_field.get("content", [])

    # Extract which government function this group represents
    func_number, func_name = get_selected_function(json_data)
    group_data["function_number"] = func_number
    group_data["government_function"] = func_name

    return group_data


def get_base_filename(filepath: str) -> str:
    """
    Extract the base filename (without _cover or _groupN suffix).

    :param filepath: Full file path
    :return: Base filename for matching cover to groups
    """
    filename = os.path.basename(filepath)
    filename = filename.replace("_cropped_result.json", "")
    filename = re.sub(r"_(cover|group\d+)$", "", filename)
    return filename


if __name__ == "__main__":
    # Input/output directories
    json_input_dir = input("Enter the input JSON directory: ")
    json_output_dir = input("Enter the output JSON directory: ")

    # Ensure output directory exists
    os.makedirs(json_output_dir, exist_ok=True)

    json_files = get_all_json_files(json_input_dir)

    # Separate cover files and group files
    cover_files = {}  # base_filename -> filepath
    group_files = {}  # base_filename -> [list of group filepaths]

    for json_file in json_files:
        filename = os.path.basename(json_file)
        base_name = get_base_filename(json_file)

        if "_cover" in filename:
            cover_files[base_name] = json_file
        elif "_group" in filename:
            group_files.setdefault(base_name, []).append(json_file)

    # Output one flat JSON per group file
    processed = 0
    for base_name, cover_path in cover_files.items():
        with open(cover_path, "r") as f:
            try:
                cover_json = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Skipping {cover_path}: {e}")
                continue
        cover_metadata = extract_cover_metadata(cover_json)

        groups = group_files.get(base_name, [])
        groups.sort()

        for group_path in groups:
            with open(group_path, "r") as f:
                try:
                    group_json = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Skipping {group_path}: {e}")
                    continue

            group_data = extract_group_data(group_json)

            # Derive output filename from group file (preserves _group1, _group2, etc.)
            group_stem = os.path.basename(group_path).replace("_cropped_result.json", "")
            output_path = os.path.join(json_output_dir, group_stem + ".json")

            json_output = {
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

            with open(output_path, "w", encoding="utf-8") as file:
                json.dump(json_output, file, indent=4)

            print(f"Processed: {group_stem}.json")
            processed += 1

    print(f"\nProcessing complete. {processed} files written to: {json_output_dir}")
