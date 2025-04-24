import csv
import os
import json
import glob
import re
import pandas as pd
from rapidfuzz import process, fuzz
from table_validator import column_validator, row_validator_with_correction
from typing import Dict, Tuple, List


def write_to_log(path: str, message: str) -> None:
    with open(path, "a") as f:
        f.write(message)


def validate_text(data: Dict, threshold: float = 0.5) -> Tuple[bool, str]:
    confidences = data["confidence"]
    if len(confidences) < 2:
        return True, "empty_content"
    else:
        # ignore the first element: title
        for conf in confidences[1:]:
            if conf < threshold:
                return False, "low_confidence"
    return True, ""


def validate_table(data: Dict) -> Tuple[bool, bool]:
    """
    Validate table
    
    Returns:
    - True if the table is valid
    - True if the table is valid except for the last row, which is the prior year total (EEO1)
    """
    table: List[List[int]] = data["content"]
    conf_table: List[List[int]] = data["confidence"]
    col_validations: List[int] = column_validator("eeo1", table)

    row_validations: List[int] = row_validator_with_correction("eeo1", table, conf_table)
    row_validations_except_last: List[int] = row_validations[:-1]

    return (all(col_validations) and all(row_validations)), (
            all(col_validations) and all(row_validations_except_last)
    )


def get_current_year(data: Dict):
    content = data["content"]
    match = re.search(r"\b(19|20)\d{2}\b", content[0])
    res_year = -1
    if match:
        res_year = int(match.group())
    else:
        "not found"
    return res_year


def load_city_state_reference(csv_path):
    city_state_list = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            city = row['city'].strip().upper()
            state_id = row['state_id'].strip()
            city_state_list.append((city, state_id))
    return city_state_list


def create_search_sets(city_state_list):
    all_cities = list(set(city for city, _ in city_state_list))
    all_state_ids = list(set(state_id for _, state_id in city_state_list))
    return all_cities, all_state_ids


def correct_city_state(ocr_city, ocr_state_id, city_state_list, city_list,
                       state_id_list, threshold=80):
    matched_state, state_score, _ = process.extractOne(ocr_state_id, state_id_list, scorer=fuzz.ratio)
    matched_city, city_score, _ = process.extractOne(ocr_city, city_list, scorer=fuzz.ratio)
    if state_score >= threshold and city_score >= threshold:
        if (matched_city, matched_state) in city_state_list:
            return matched_city, matched_state
    return ocr_city, ocr_state_id


def validate(validations):
    for validation in validations:
        if not validation:
            return False
    return True


def get_all_json_files(path: str) -> List[str]:
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    dirs.append(path)
    json_files = []
    for d in dirs:
        json_files.extend(glob.glob(os.path.join(d, "*.json")))
    json_files.sort()
    return json_files


json_input_dir = "../../files/batch_1/results"
json_files = get_all_json_files(json_input_dir)
print(len(json_files))
cnt = 0
cnt_map = dict()
invalid_table_files = []
# partial results are calculated without considering the last row of the table
partial_invalid_table_files = []
invalid_text_json_files = []
missing_locations = []
year_map = dict()
city_state_csv = "../../config/uscities.csv"
reference_data = load_city_state_reference(city_state_csv)
city_list, state_id_list = create_search_sets(reference_data)
for json_file in json_files:
    # json_file_path = os.path.join(json_input_dir, json_file)
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
                is_valid, err = validate_text(item)
                if not is_valid:
                    is_valid_text = False
            if item_id == "h-CURRENT_YEAR_REPORTING_TOTAL_LABEL":
                year = get_current_year(item)
                year_map[year] = year_map.get(year, 0) + 1

            if item_id == "b-CITY_TOWN":
                if len(item["content"]) >= 2 and len(json_data[index + 3]["content"]) >= 2:
                    ocr_city = item["content"][1]
                    ocr_state_id = json_data[index + 3]["content"][1]
                    corrected_ocr_city, corrected_ocr_state_id = correct_city_state(ocr_city, ocr_state_id,
                                                                                    reference_data, city_list,
                                                                                    state_id_list)
                    item["content"][1] = corrected_ocr_city
                    json_data[index + 3]["content"][1] = corrected_ocr_state_id
                else:
                    missing_locations.append(json_file)
                # print(ocr_city, corrected_ocr_city)
                # print(ocr_state_id, corrected_ocr_state_id)
        if not is_valid_text:
            invalid_text_json_files.append(json_file)
        if not is_valid_table:
            invalid_table_files.append(json_file)
        if not is_valid_table and not is_partial_valid_table:
            partial_invalid_table_files.append(json_file)
        f.seek(0)
        json.dump(json_data, f, indent=2)
        f.truncate()

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
