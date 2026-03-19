"""
json_validator_eeo4.py

Validates OCR output JSON files for EEO-4 forms. Adapted from json_validator.py with
EEO-4-specific changes:
- Table IDs: "table-A", "table-B", "table-C" instead of "h-TABLE"
- Table validation: row-sum checks only (column totals span multiple sections)
- City/state correction: uses "b-CITY" and "b-STATE" field IDs directly
- Year extraction: parses "Reporting Year" from "title-CONTROL_NUMBER_YEAR"
"""

import csv
import os
import json
import glob
import re
import shutil
from rapidfuzz import process, fuzz
from ..utilities.table_validator import row_validator_with_correction
from typing import Dict, Tuple, List, Optional


EEO4_TABLE_IDS = {"table-A", "table-B", "table-C"}
SKIP_TEXT_IDS = EEO4_TABLE_IDS


def write_to_log(path: str, message: str) -> None:
    with open(path, "a") as f:
        f.write(message)


def validate_text(data: Dict, threshold: float = 0.5) -> Tuple[bool, str]:
    """
    Validate that all confidence scores (excluding the title) are above a threshold.
    """
    confidences = data["confidence"]
    if not isinstance(confidences, list) or len(confidences) < 2:
        return True, "empty_content"
    for conf in confidences[1:]:
        if isinstance(conf, (int, float)) and conf < threshold:
            return False, "low_confidence"
    return True, ""


def validate_table_rows(data: Dict) -> Tuple[bool, bool]:
    """
    Validate EEO-4 table row sums against the last-column total.
    Column validation is skipped because EEO-4 column totals span multiple table sections.

    Returns (is_valid, is_partial_valid) where partial uses a magnitude threshold of 10.
    """
    table = data.get("content", [])
    conf_table = data.get("confidence", [])

    if not table or not isinstance(table[0], list):
        return True, True

    # Pad confidence table if missing or mismatched
    if not conf_table or not isinstance(conf_table[0], list):
        conf_table = [[1.0] * len(row) for row in table]

    row_validations = row_validator_with_correction("eeo1", table, conf_table)
    row_error = sum(
        abs(sum(table[i][:-1]) - table[i][-1])
        for i in range(len(table))
        if table[i]
    )
    is_valid = all(row_validations)
    is_partial = is_valid or row_error < 10
    return is_valid, is_partial


def measure_table_error(data: Dict) -> int:
    table = data.get("content", [])
    if not table or not isinstance(table[0], list):
        return 0
    return sum(
        abs(sum(row[:-1]) - row[-1])
        for row in table
        if row
    )


def get_field_by_id(json_data: List[Dict], field_id: str) -> Optional[Dict]:
    for field in json_data:
        if field.get("id") == field_id:
            return field
    return None


def get_reporting_year(json_data: List[Dict]) -> int:
    """
    Extract reporting year from the title-CONTROL_NUMBER_YEAR field.
    """
    field = get_field_by_id(json_data, "title-CONTROL_NUMBER_YEAR")
    if field:
        for item in field.get("content", []):
            match = re.search(r"Reporting Year[:\s]*(\d{4})", item, re.IGNORECASE)
            if match:
                return int(match.group(1))
            match = re.search(r"\b(19|20)\d{2}\b", item)
            if match:
                return int(match.group())
    return -1


def load_city_state_reference(csv_path: str) -> List[Tuple[str, str]]:
    city_state_list = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            city = row['city'].strip().upper()
            state_id = row['state_id'].strip()
            city_state_list.append((city, state_id))
    return city_state_list


def create_search_sets(city_state_list: List[Tuple[str, str]]):
    all_cities = list(set(city for city, _ in city_state_list))
    all_state_ids = list(set(state_id for _, state_id in city_state_list))
    return all_cities, all_state_ids


def correct_city_state(ocr_city, ocr_state_id, city_state_list, city_list, state_id_list, threshold=80):
    matched_state, state_score, _ = process.extractOne(ocr_state_id, state_id_list, scorer=fuzz.ratio)
    matched_city, city_score, _ = process.extractOne(ocr_city, city_list, scorer=fuzz.ratio)
    if state_score >= threshold and city_score >= threshold and (matched_city, matched_state) in city_state_list:
        return matched_city, matched_state
    return ocr_city, ocr_state_id


def get_all_json_files(path: str) -> List[str]:
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    dirs.append(path)
    json_files = []
    for d in dirs:
        json_files.extend(glob.glob(os.path.join(d, "*.json")))
    json_files.sort()
    return json_files


if __name__ == "__main__":
    json_input_dir = input("Input directory of JSON outputs: ")

    json_files = get_all_json_files(json_input_dir)
    city_state_csv = "../../config/uscities.csv"
    reference_data = load_city_state_reference(city_state_csv)
    city_list, state_id_list = create_search_sets(reference_data)

    cnt = 0
    invalid_table_files = []
    partial_invalid_table_files = []
    invalid_text_json_files = []
    missing_locations = []
    year_map = {}
    error_magnitudes = []
    file_error_magnitudes = {}

    for json_file in json_files:
        is_valid_text = True
        is_valid_table, is_partial_valid_table = True, True
        file_magnitude = 0

        with open(json_file, "r+") as f:
            cnt += 1
            json_data = json.load(f)

            for item in json_data:
                item_id = item.get("id", "")

                # Table validation
                if item_id in EEO4_TABLE_IDS:
                    v, pv = validate_table_rows(item)
                    if not v:
                        is_valid_table = False
                    if not pv:
                        is_partial_valid_table = False
                    mag = measure_table_error(item)
                    file_magnitude += mag
                    error_magnitudes.append(mag)

                # Text confidence validation (skip table fields)
                elif item_id not in SKIP_TEXT_IDS:
                    valid, _ = validate_text(item)
                    if not valid:
                        is_valid_text = False

            # Year extraction
            year = get_reporting_year(json_data)
            year_map[year] = year_map.get(year, 0) + 1

            # City/state correction using named field IDs
            city_field = get_field_by_id(json_data, "b-CITY")
            state_field = get_field_by_id(json_data, "b-STATE")
            if (city_field and len(city_field.get("content", [])) >= 2 and
                    state_field and len(state_field.get("content", [])) >= 2):
                ocr_city = city_field["content"][1]
                ocr_state = state_field["content"][1]
                corrected_city, corrected_state = correct_city_state(
                    ocr_city, ocr_state, reference_data, city_list, state_id_list
                )
                city_field["content"][1] = corrected_city
                state_field["content"][1] = corrected_state
            else:
                missing_locations.append(json_file)

            if not is_valid_text:
                invalid_text_json_files.append(json_file)
            if not is_valid_table:
                invalid_table_files.append(json_file)
            if not is_partial_valid_table:
                partial_invalid_table_files.append(json_file)

            file_error_magnitudes[json_file] = file_magnitude

            f.seek(0)
            json.dump(json_data, f, indent=2)
            f.truncate()

    # Summary
    summary = "Validation Summary (EEO-4)\n"
    summary += f"Number of json files: {cnt}\n"
    summary += f"Number of partial invalid json files: {len(partial_invalid_table_files)}\n"
    summary += f"Number of invalid json files: {len(invalid_table_files)}\n"
    summary += f"Number of invalid text json files: {len(invalid_text_json_files)}\n"
    summary += f"Year map:\n{year_map}\n"
    summary += f"Number of files missing location: {len(missing_locations)}\n"
    summary += f"Names of partial invalid json files: {partial_invalid_table_files}\n"
    summary += f"Names of invalid json files: {invalid_table_files}\n"
    summary += f"Names of invalid text json files: {invalid_text_json_files}\n"
    summary += f"Names of missing-location json files: {missing_locations}\n"

    if error_magnitudes:
        from collections import Counter
        zero      = [m for m in error_magnitudes if m == 0]
        b1_10     = [m for m in error_magnitudes if 1 <= m <= 10]
        b11_20    = [m for m in error_magnitudes if 11 <= m <= 20]
        b21_50    = [m for m in error_magnitudes if 21 <= m <= 50]
        b51_100   = [m for m in error_magnitudes if 51 <= m <= 100]
        above_100 = [m for m in error_magnitudes if m > 100]
        files_above_100 = {f: m for f, m in file_error_magnitudes.items() if m > 100}
        summary += f"Error magnitude distribution (row discrepancy per table per file):\n"
        summary += f"  Min: {min(error_magnitudes)}\n"
        summary += f"  Max: {max(error_magnitudes)}\n"
        summary += f"  Avg: {sum(error_magnitudes)/len(error_magnitudes):.1f}\n"
        summary += f"  Counts: {dict(sorted(Counter(error_magnitudes).items()))}\n"
        summary += f"  Tables with error = 0:    {len(zero)}\n"
        summary += f"  Tables with error 1-10:   {len(b1_10)}\n"
        summary += f"  Tables with error 11-20:  {len(b11_20)}\n"
        summary += f"  Tables with error 21-50:  {len(b21_50)}\n"
        summary += f"  Tables with error 51-100: {len(b51_100)}\n"
        summary += f"  Tables with error > 100:  {len(above_100)}\n"
        summary += f"  Names of files with error > 100: {files_above_100}\n"

    write_to_log("validation_summary_eeo4.log", summary)

    # Sort files into subfolders by total error magnitude
    category_folders = {
        "0_errors":  lambda m: m == 0,
        "1_to_10":   lambda m: 1 <= m <= 10,
        "11_to_20":  lambda m: 11 <= m <= 20,
        "21_to_50":  lambda m: 21 <= m <= 50,
        "51_to_100": lambda m: 51 <= m <= 100,
        "above_100": lambda m: m > 100,
    }
    for folder_name in category_folders:
        os.makedirs(os.path.join(json_input_dir, folder_name), exist_ok=True)
    for json_file, magnitude in file_error_magnitudes.items():
        for folder_name, condition in category_folders.items():
            if condition(magnitude):
                shutil.move(json_file, os.path.join(json_input_dir, folder_name, os.path.basename(json_file)))
                break
