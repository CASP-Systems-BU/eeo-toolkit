"""
eeo1_filter.py

This script filters and extracts metadata from raw OCR-parsed JSON files for EEO-1 reports.
It identifies establishment-level (non-consolidated) reports and keeps only those associated
with Massachusetts (MA) by checking various address fields and ZIP codes.

The resulting filtered metadata is saved as simplified JSON files for downstream processing.

---

Key Features:
- Filters out consolidated reports using fuzzy string matching
- Matches employer or HQ location to Massachusetts by ZIP/state
- Extracts metadata such as EIN, NAICS code, employer name, city/state, and reporting year
"""

import csv
import glob
import json
import os
import re
from typing import List
from rapidfuzz import fuzz

# Input/output paths
# json_input_dir = "/home/node0/Documents/project/data/valid_submissions/typed/type2/results"
# json_output_dir = "/home/node0/Documents/project/data/valid_submissions/typed/type2/filtered"
json_input_dir = input("Enter the input JSON directory: ")
json_output_dir = input("Enter the output JSON directory: ")


def get_all_json_files(path: str) -> List[str]:
    """
    Recursively retrieve all JSON files under the specified path.
    """
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    dirs.append(path)
    json_files = []
    for d in dirs:
        json_files.extend(glob.glob(os.path.join(d, "*.json")))
    json_files.sort()
    return json_files


def get_extracted_str(content):
    """
    Extract string value from OCR 'content' list.
    """
    if len(content) > 1:
        return content[1]
    return ""

# Field indices based on expected JSON structure
city_idx = 2
employer_name_idx = 3
state_idx = 5
zip_idx = 6
hq_city_idx = 7
hq_state_idx = 11
hq_zip_idx = 12
ein_idx = 13
naics_idx = 14
table_idx = 17

# Similarity threshold for fuzzy matching
sim_threshold = 80

# Paths to public reference files
naics_file_path = "../../public_data/naics_codes.csv"
uscities_file_path = "../../public_data/uscities.csv"

# Constants
CONSOLIDATED_REPORT = "CONSOLIDATED REPORT"

# Lookup tables
naics_map = {}
ma_zip_set = set()


json_files = get_all_json_files(json_input_dir)

# Load Massachusetts ZIP codes
with open(uscities_file_path, newline='', encoding='utf-8') as uscities_file:
    reader = csv.DictReader(uscities_file)
    for row in reader:
        state_id = row['state_id'].strip()
        if state_id == "MA":
            zips = row['zips'].strip().split(" ")
            for zip in zips:
                ma_zip_set.add(zip)

# Load NAICS code-to-name mapping
with open(naics_file_path, newline='', encoding='utf-8') as naics_file:
    reader = csv.DictReader(naics_file)
    for row in reader:
        code = row['\ufeff2022 NAICS Code'].strip()
        name = row['2022 NAICS Title'].strip()
        naics_map[code] = name

# Process each OCR JSON file
for json_file in json_files:
    json_output = {}

    with open(json_file, "r") as f:
        json_data = json.load(f)

        # Derive clean filename
        filename = json_file.split("/")[-1].split("_cropped")[0]

        # Fuzzy match to skip consolidated reports
        type_of_report = get_extracted_str(json_data[0]["content"])
        similarity_score = fuzz.ratio(type_of_report, CONSOLIDATED_REPORT)
        if similarity_score > sim_threshold:
            continue

        # Extract metadata fields
        json_output["filename"] = filename.split("_page")[0]
        json_output["type_of_report"] = type_of_report
        json_output["employer_name"] = get_extracted_str(json_data[employer_name_idx]["content"])
        json_output["state"] = get_extracted_str(json_data[state_idx]["content"])
        json_output["city"] = get_extracted_str(json_data[city_idx]["content"])
        json_output["headquarter_state"] = get_extracted_str(json_data[hq_state_idx]["content"])
        json_output["headquarter_city"] = get_extracted_str(json_data[hq_city_idx]["content"])
        json_output["EIN"] = get_extracted_str(json_data[ein_idx]["content"])
        json_output["zipcode"] = get_extracted_str(json_data[zip_idx]["content"])
        json_output["headquarter_zipcode"] = get_extracted_str(json_data[hq_zip_idx]["content"])

        # Parse and match NAICS code
        naics_str = get_extracted_str(json_data[naics_idx]["content"])
        match = re.search(r"\d+", naics_str)
        if match:
            code = match.group()
            json_output["NAICS"] = code
            json_output["NAICS_name"] = naics_map.get(code, "")
        else:
            json_output["NAICS"] = ""
            json_output["NAICS_name"] = ""

        # Extract reporting year if available
        res_year = -1
        if len(json_data[15]["content"]) > 0:
            match = re.search(r"\b(19|20)\d{2}\b", json_data[15]["content"][0])
            if match:
                res_year = int(match.group())
        json_output["reporting_year"] = res_year

        # Include raw table field (unstructured)
        json_output["table"] = json_data[table_idx]["content"]

        # Filter: include only reports tied to Massachusetts (by state or ZIP)
        if (
            json_output["state"] == "MA"
            or json_output["headquarter_state"] == "MA"
            or json_output["zipcode"] in ma_zip_set
            or json_output["headquarter_zipcode"] in ma_zip_set
        ):
            json_output_name = filename + ".json"
            json_output_path = os.path.join(json_output_dir, json_output_name)
            with open(json_output_path, "w", encoding="utf-8") as file:
                json.dump(json_output, file, indent=4)
