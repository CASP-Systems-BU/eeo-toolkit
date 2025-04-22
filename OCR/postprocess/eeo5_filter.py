import glob
import json
import os
import re
from typing import List


def get_all_json_files(path: str) -> List[str]:
    dirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    dirs.append(path)
    json_files = []
    for d in dirs:
        json_files.extend(glob.glob(os.path.join(d, "*.json")))
    json_files.sort()
    return json_files


def get_extracted_str(content):
    if len(content) > 1:
        return content[1]
    return ""


json_input_dir = "/home/node0/Documents/eeo5_json_corrected/raw_json"
json_output_dir = "/home/node0/Documents/eeo5_json_corrected/filtered"
json_files = get_all_json_files(json_input_dir)
zip_idx = 5
state_idx = 4
city_idx = 1
county_idx = 2
table_a_idx = 10
table_b_idx = 11
table_c_idx = 12
reporting_year_idx = 13
checkbox_idx = 14

for json_file in json_files:
    json_output = {}
    with open(json_file, "r") as f:
        json_data = json.load(f)
        filename = json_file.split("/")[-1].split("_cropped")[0]
        json_output["filename"] = filename.split("_page")[0]
        json_output["state"] = get_extracted_str(json_data[state_idx]["content"])
        json_output["county"] = get_extracted_str(json_data[county_idx]["content"]).upper()
        json_output["city"] = get_extracted_str(json_data[city_idx]["content"])
        json_output["zipcode"] = get_extracted_str(json_data[zip_idx]["content"])
        res_year = -1
        if len(json_data[reporting_year_idx]["content"]) > 1:
            match = re.search(r"\b(19|20)\d{2}\b", json_data[reporting_year_idx]["content"][1])
            if match:
                res_year = int(match.group())

        json_output["reporting_year"] = str(res_year)
        json_output["table_a"] = json_data[table_a_idx]["content"]
        json_output["table_b"] = json_data[table_b_idx]["content"]
        json_output["table_c"] = json_data[table_c_idx]["content"]

        json_output["Local Public School"] = json_data[checkbox_idx]["content"]["Local Public School"]
        json_output["Special Regional Agency"] = json_data[checkbox_idx]["content"]["Special Regional Agency"]
        json_output["State Education Agency"] = json_data[checkbox_idx]["content"]["State Education Agency"]
        json_output["Other"] = json_data[checkbox_idx]["content"]["Other"]

        json_output_name = filename + ".json"
        json_output_path = os.path.join(json_output_dir, json_output_name)
        with open(json_output_path, "w", encoding="utf-8") as file:
            json.dump(json_output, file, indent=4)
