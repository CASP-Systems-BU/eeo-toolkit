"""
json_validator.py

This script validates the OCR output JSON files for EEO-1 forms. It performs multiple checks including:
- Text confidence threshold enforcement
- Table structural validation (with optional leniency for the last row)
- Location correction using fuzzy city/state matching
- Reporting year extraction

It also logs a summary of the validation results, identifying files with structural issues, low text confidence, and missing location metadata.

---

Key Features:
- Checks if the confidence score for non-title content is above a threshold
- Validates tables using domain-specific row/column checks
- Fixes OCR errors in city/state fields using fuzzy matching and U.S. reference data
- Generates a validation summary log with counts and filenames of problematic files

---

Warning:
- This script now only supports EEO-1 forms. EEO-5 forms are not supported.
"""

import csv
import os
import json
import glob
import re
from rapidfuzz import process, fuzz
from ..utilities.table_validator import column_validator, row_validator_with_correction
from typing import Dict, Tuple, List

json_input_dir = "../../files/batch_1/results"  # MODIFY ME: Input directory for JSON files


def write_to_log(path: str, message: str) -> None:
    """Append a message to a log file."""
    with open(path, "a") as f:
        f.write(message)


def validate_text(data: Dict, threshold: float = 0.5) -> Tuple[bool, str]:
    """Validate that all confidence scores (excluding title) are above the threshold."""
    confidences = data["confidence"]
    if len(confidences) < 2:
        return True, "empty_content"
    for conf in confidences[1:]:
        if conf < threshold:
            return False, "low_confidence"
    return True, ""


def validate_table(data: Dict) -> Tuple[bool, bool]:
    """Validate table structure and optionally allow the last row to be invalid."""
    table: List[List[int]] = data["content"]
    conf_table: List[List[int]] = data["confidence"]
    col_validations: List[int] = column_validator("eeo1", table)
    row_validations: List[int] = row_validator_with_correction("eeo1", table, conf_table)
    return (all(col_validations) and all(row_validations)), (
        all(col_validations) and all(row_validations[:-1])
    )


def get_current_year(data: Dict):
    """Extract the reporting year from a content string."""
    content = data["content"]
    match = re.search(r"\b(19|20)\d{2}\b", content[0])
    return int(match.group()) if match else -1


def load_city_state_reference(csv_path):
    """Load valid city-state combinations from a reference CSV."""
    city_state_list = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            city = row['city'].strip().upper()
            state_id = row['state_id'].strip()
            city_state_list.append((city, state_id))
    return city_state_list


def create_search_sets(city_state_list):
    """Generate lists of all unique cities and states from reference data."""
    all_cities = list(set(city for city, _ in city_state_list))
    all_state_ids = list(set(state_id for _, state_id in city_state_list))
    return all_cities, all_state_ids


def correct_city_state(ocr_city, ocr_state_id, city_state_list, city_list, state_id_list, threshold=80):
    """Correct city/state using fuzzy matching against known reference values."""
    matched_state, state_score, _ = process.extractOne(ocr_state_id, state_id_list, scorer=fuzz.ratio)
    matched_city, city_score, _ = process.extractOne(ocr_city, city_list, scorer=fuzz.ratio)
    if state_score >= threshold and city_score >= threshold and (matched_city, matched_state) in city_state_list:
        return matched_city, matched_state
    return ocr_city, ocr_state_id


def get_all_json_files(path: str) -> List[str]:
    """Recursively find all JSON files in the given path."""
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    dirs.append(path)
    json_files = []
    for d in dirs:
        json_files.extend(glob.glob(os.path.join(d, "*.json")))
    json_files.sort()
    return json_files


# Setup and load data
json_files = get_all_json_files(json_input_dir)
city_state_csv = "../../config/uscities.csv"
reference_data = load_city_state_reference(city_state_csv)
city_list, state_id_list = create_search_sets(reference_data)

# Validation tracking
cnt = 0
invalid_table_files = []
partial_invalid_table_files = []
invalid_text_json_files = []
missing_locations = []
year_map = {}

# Validation loop
for json_file in json_files:
    json_file_path = json_file
    is_valid_text = True
    is_valid_table, is_partial_valid_table = True, True

    with open(json_file_path, "r+") as f:
        cnt += 1
        json_data = json.load(f)

        for index, item in enumerate(json_data):
            item_id = item["id"]
            if item_id == "h-TABLE":
                is_valid_table, is_partial_valid_table = validate_table(item)
            elif item_id != "E-AND_F":
                is_valid, _ = validate_text(item)
                if not is_valid:
                    is_valid_text = False
            if item_id == "h-CURRENT_YEAR_REPORTING_TOTAL_LABEL":
                year = get_current_year(item)
                year_map[year] = year_map.get(year, 0) + 1
            if item_id == "b-CITY_TOWN":
                if len(item["content"]) >= 2 and len(json_data[index + 3]["content"]) >= 2:
                    ocr_city = item["content"][1]
                    ocr_state_id = json_data[index + 3]["content"][1]
                    corrected_ocr_city, corrected_ocr_state_id = correct_city_state(
                        ocr_city, ocr_state_id, reference_data, city_list, state_id_list)
                    item["content"][1] = corrected_ocr_city
                    json_data[index + 3]["content"][1] = corrected_ocr_state_id
                else:
                    missing_locations.append(json_file)

        if not is_valid_text:
            invalid_text_json_files.append(json_file)
        if not is_valid_table:
            invalid_table_files.append(json_file)
        if not is_partial_valid_table:
            partial_invalid_table_files.append(json_file)

        f.seek(0)
        json.dump(json_data, f, indent=2)
        f.truncate()

# Write validation summary
summary = "Validation Summary\n"
summary += f"Number of json files: {cnt}\n"
summary += f"Number of partial invalid json files: {len(partial_invalid_table_files)}\n"
summary += f"Number of invalid json files: {len(invalid_table_files)}\n"
summary += f"Number of invalid text json files: {len(invalid_text_json_files)}\n"
summary += f"Year map:\n{year_map}\n"
summary += f"Number of files missing location:\n{len(missing_locations)}\n"
summary += f"Names of partial invalid json files: {partial_invalid_table_files}\n"
summary += f"Names of invalid json files: {invalid_table_files}\n"
summary += f"Names of invalid text json files: {invalid_text_json_files}\n"
summary += f"Names of missing-location json files: {missing_locations}\n"

write_to_log("validation_summary.log", summary)
