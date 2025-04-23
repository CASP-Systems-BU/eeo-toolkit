"""
This script flattens structured EEO-5 JSON records into a tabular CSV format.
It handles nested dictionaries, multi-dimensional lists (tables A, B, and C),
and conditional metadata like agency types. The flattened data is saved as
a CSV, and a summary count of records grouped by 'county' is printed.
"""

import pandas as pd
import os
import json
from OCR.utilities.dir_helper import get_files_in_directory
from const import EEO5_COLUMN_NAMES, EEO5_TABLE_A_ROW_NAMES, EEO5_TABLE_B_ROW_NAMES, EEO5_TABLE_C_ROW_NAMES

# === Paths ===
json_input_dir = "/home/node0/Documents/eeo5_json_corrected/filtered"
output_dir = "/home/node0/Documents/eeo5_json_corrected/filtered"

# === Load all JSON files ===
flat_rows = []
json_files = get_files_in_directory(json_input_dir, extension="json")

for json_file in json_files:
    json_path = os.path.join(json_input_dir, json_file)
    with open(json_path) as f:
        data = json.load(f)

    flat_row = {}

    for key, value in data.items():
        if isinstance(value, dict):
            # Flatten nested dictionaries by prefixing keys
            for sub_key, sub_val in value.items():
                flat_row[f"{key}.{sub_key}"] = sub_val

        elif isinstance(value, list):
            # Handle 2D tables (list of lists)
            if all(isinstance(row, list) for row in value):
                for i, row in enumerate(value):
                    for j, val in enumerate(row):
                        # Skip the total column
                        if j != len(EEO5_COLUMN_NAMES) - 1:
                            # Determine which table this is (A, B, or C)
                            if key == "table_a":
                                if i == len(EEO5_TABLE_A_ROW_NAMES) - 1:
                                    continue  # Skip total row
                                row_name = "FULL-TIME STAFF_" + EEO5_TABLE_A_ROW_NAMES[i]
                            elif key == "table_b":
                                if i == len(EEO5_TABLE_B_ROW_NAMES) - 1:
                                    continue
                                row_name = "PART-TIME STAFF_" + EEO5_TABLE_B_ROW_NAMES[i]
                            else:
                                if i == len(EEO5_TABLE_C_ROW_NAMES) - 1:
                                    continue
                                row_name = "FULL-TIME NEW HIRES_" + EEO5_TABLE_C_ROW_NAMES[i]

                            # Construct column name: "Race_Gender_RowName" => value
                            flat_row[f"{EEO5_COLUMN_NAMES[j]}_{row_name}"] = val

            else:
                # Flatten simple lists by index
                for i, val in enumerate(value):
                    flat_row[f"{key}_{i}"] = val

        else:
            # Determine agent type from boolean flags
            if key in ["Local Public School", "Special Regional Agency", "State Education Agency", "Other"]:
                if value:
                    flat_row["Type of Agent"] = key
            else:
                flat_row[key] = value

    flat_rows.append(flat_row)

# === Convert to DataFrame and export ===
df = pd.DataFrame(flat_rows)
df.to_csv(os.path.join(output_dir, "eeo5.csv"), index=False)

# === Reload and print county-level summary ===
df = pd.read_csv(os.path.join(output_dir, "eeo5.csv"))
group_counts = df.groupby('county').size()
print(group_counts)
