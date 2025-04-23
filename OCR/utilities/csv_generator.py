import csv
import json
import re
import os
import glob
from typing import List

def get_all_json_files(path: str)-> List[str]:
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

json_input_dir = "../../files/batch_1/results"
output_dir = "../../files/batch_1/test"

GENDER_LIST = ["Male", "Female", "Male", "Male", "Male", "Male", "Male",
               "Male", "Female", "Female", "Female", "Female", "Female", "Female"]
RACE_LIST = ["Hispanic or Latino", "Hispanic or Latino", "White",
             "Black or African American", "Asian",
             "Native Hawaiian or Other Pacific Islander", "American Indian or Alaska Native",
             "Two or More Races", "White",
             "Black or African American", "Asian",
             "Native Hawaiian or Other Pacific Islander", "American Indian or Alaska Native",
             "Two or More Races"]
JOB_LIST = ["Executive/Senior Level Officials and Managers", "First/Mid-Level Officials and Managers",
            "Professionals", "Technicians", "Sales Workers", "Administrative Support Workers",
            "Craft Workers", "Operatives", "Laborers and Helpers", "Service Workers"]
json_files = get_all_json_files(json_input_dir)
state_idx = 5
city_idx = 2
employer_name_idx = 3
hq_city_idx = 7
hq_state_idx = 11
ein_idx = 13
naics_idx = 14
table_idx = 17
csv_file = "output.csv"
naics_file_path = "../../public_data/naics_codes.csv"
naics_map = {}
with open(naics_file_path, newline='', encoding='utf-8') as naics_file:
    reader = csv.DictReader(naics_file)
    for row in reader:
        code = row['\ufeff2022 NAICS Code'].strip()
        name = row['2022 NAICS Title'].strip()
        naics_map[code] = name
for json_file in json_files:
    json_output = {}
    with open(json_file, "r") as f:
        json_data = json.load(f)
        with open(os.path.join(output_dir, csv_file), "a", newline='', encoding='utf-8') as file:
            filename = json_file.split("/")[-1].split("_cropped")[0]
            json_output["filename"] = filename.split("_page")[0]
            json_output["employer_name"] = get_extracted_str(json_data[employer_name_idx]["content"])
            json_output["state"] = get_extracted_str(json_data[state_idx]["content"])
            json_output["city"] = get_extracted_str(json_data[city_idx]["content"])
            json_output["headquarter_state"] = get_extracted_str(json_data[hq_state_idx]["content"])
            json_output["headquarter_city"] = get_extracted_str(json_data[hq_city_idx]["content"])
            json_output["EIN"] = get_extracted_str(json_data[ein_idx]["content"])
            naics_str = get_extracted_str(json_data[naics_idx]["content"])
            match = re.search(r"\d+", naics_str)
            json_output["NAICS"] = ""
            json_output["NAICS_name"] = ""
            if match:
                code = match.group()
                json_output["NAICS"] = code
                naics_name = naics_map.get(code, "")
                json_output["NAICS_name"] = naics_name
            match = re.search(r"\b(19|20)\d{2}\b", json_data[15]["content"][0])
            res_year = -1
            if match:
                res_year = int(match.group())
            json_output["reporting_year"] = res_year
            if json_output["state"] != "MA" and json_output["headquarter_state"] != "MA":
                continue
            table = json_data[table_idx]["content"]
            for i in range(len(table) - 2):
                for j in range(len(table[0]) - 1):
                    json_output["gender"] = GENDER_LIST[j]
                    json_output["race"] = RACE_LIST[j]
                    json_output["job category"] = JOB_LIST[i]
                    json_output["label"] = "current"
                    json_output["total"] = table[i][j]
                    writer = csv.DictWriter(file, fieldnames=json_output.keys(), extrasaction='ignore')
                    if file.tell() == 0:
                        writer.writeheader()
                    writer.writerow(json_output)
            for j in range(len(table[-2]) - 1):
                json_output["gender"] = GENDER_LIST[j]
                json_output["race"] = RACE_LIST[j]
                json_output["job category"] = "N/A"
                json_output["label"] = "current"
                json_output["total"] = table[-2][j]
                writer.writerow(json_output)

            for j in range(len(table[-1]) - 1):
                json_output["gender"] = GENDER_LIST[j]
                json_output["race"] = RACE_LIST[j]
                json_output["job category"] = "N/A"
                json_output["label"] = "prior"
                json_output["total"] = table[-1][j]
                writer.writerow(json_output)


