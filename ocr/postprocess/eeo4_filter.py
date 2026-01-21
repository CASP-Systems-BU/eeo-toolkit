"""
eeo4_filter.py

This script processes OCR-parsed JSON files of EEO-4 reports, extracting and cleaning key metadata for
government function-level reporting. EEO-4 forms are split into a cover file (agency metadata) and
multiple group files (one per government function), which this script merges together.

---

Key Features:
- Merges cover file metadata with each group file
- Extracts metadata including jurisdiction name, city, county, state, ZIP code, and reporting year
- Identifies which government function each group represents
- Retrieves form tables (A, B, C) with employment data
- Extracts department/agency information and remarks
- Standardizes field formats (e.g., uppercase county)
- Writes filtered and normalized metadata to a new directory
"""

import glob
import json
import os
import re
from typing import List, Dict, Optional


# ===============> Const Starts <===============
# Government function names
GOVERNMENT_FUNCTIONS = [
    "FINANCIAL ADMINISTRATION GENERAL CONTROL",
    "STREETS AND HIGHWAYS",
    "PUBLIC WELFARE",
    "POLICE PROTECTION",
    "FIRE PROTECTION",
    "NATURAL RESOURCES PARKS AND RECREATION",
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
# ===============> Const Ends <===============


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


def get_selected_function(json_data: List[Dict]) -> str:
    """
    Determine which government function this group represents.-

    :param json_data: List of field dictionaries from OCR JSON
    :return: The selected government function, or empty string if none found
    """
    for field in json_data:
        if field.get("id") == "function-FUNCTION":
            content = field.get("content", [])
            if isinstance(content, list) and len(content) > 0:
                func_text = content[0]
                if " - - " in func_text:
                    func_name = func_text.split(" - - ", 1)[1].strip()
                    return func_name
                elif " - " in func_text:
                    func_name = func_text.split(" - ", 1)[1].strip()
                    return func_name
                elif "- " in func_text:
                    func_name = func_text.split("- ", 1)[1].strip()
                    return func_name
                elif " -" in func_text:
                    func_name = func_text.split(" -", 1)[1].strip()
                    return func_name
                elif "-" in func_text:
                    func_name = func_text.split("-", 1)[1].strip()
                    return func_name
                return func_text
    return ""


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
    group_data["government_function"] = get_selected_function(json_data)

    return group_data


def get_base_filename(filepath: str) -> str:
    """
    Extract the base filename (without _cover or _groupN suffix).

    :param filepath: Full file path
    :return: Base filename for matching cover to groups
    """
    filename = os.path.basename(filepath)
    # Remove _cropped_result.json suffix
    filename = filename.replace("_cropped_result.json", "")
    # Remove _cover or _groupN suffix
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
            if base_name not in group_files:
                group_files[base_name] = []
            group_files[base_name].append(json_file)

    # Process each set of cover + groups
    for base_name, cover_path in cover_files.items():
        # Load cover metadata
        with open(cover_path, "r") as f:
            cover_json = json.load(f)
        cover_metadata = extract_cover_metadata(cover_json)

        # Get associated group files
        groups = group_files.get(base_name, [])
        groups.sort()  # Ensure consistent ordering (group1, group2, ...)

        # Build single output document with cover metadata and all groups
        json_output = {}
        json_output["filename"] = base_name

        # Add cover metadata
        json_output["jurisdiction_name"] = cover_metadata.get("jurisdiction_name", "")
        json_output["address"] = cover_metadata.get("address", "")
        json_output["city"] = cover_metadata.get("city", "")
        json_output["county"] = cover_metadata.get("county", "")
        json_output["state"] = cover_metadata.get("state", "")
        json_output["zipcode"] = cover_metadata.get("zipcode", "")
        json_output["control_number"] = cover_metadata.get("control_number", "")
        json_output["reporting_year"] = cover_metadata.get("reporting_year", "-1")
        json_output["government_type"] = cover_metadata.get("government_type", "")
        json_output["functions_other_description"] = cover_metadata.get("functions_other_description", "")

        # Process all group files and collect into array
        function_reports = []
        for group_path in groups:
            with open(group_path, "r") as f:
                group_json = json.load(f)

            group_data = extract_group_data(group_json)

            # Extract group number from filename
            group_num = 0
            group_match = re.search(r"_group(\d+)", os.path.basename(group_path))
            if group_match:
                group_num = int(group_match.group(1))

            # Build group record
            group_record = {
                "group_number": group_num,
                "government_function": group_data.get("government_function", ""),
                "departments_included": group_data.get("departments_included", ""),
                "departments_not_included": group_data.get("departments_not_included", ""),
                "remarks": group_data.get("remarks", ""),
                "table_a": group_data.get("table_a", []),
                "table_b": group_data.get("table_b", []),
                "table_c": group_data.get("table_c", [])
            }
            function_reports.append(group_record)

        json_output["function_reports"] = function_reports

        # Write single output JSON per jurisdiction
        output_filename = f"{base_name}.json"
        output_path = os.path.join(json_output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(json_output, file, indent=4)

        print(f"Processed: {output_filename} ({len(function_reports)} function reports)")

    print(f"\nProcessing complete. Output written to: {json_output_dir}")
