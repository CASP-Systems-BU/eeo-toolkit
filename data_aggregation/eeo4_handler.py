"""
This script flattens structured EEO-4 JSON records into a tabular CSV format.
EEO-4 filter output contains top-level jurisdiction metadata and a nested
`function_reports` array (one per government function). This script creates
one CSV row per function report, repeating the jurisdiction metadata.
"""

import pandas as pd
import os
import json
from utils import get_files_in_directory
from const import EEO4_TABLE_JOB_CATEGORIES, EEO4_TABLE_A_SALARY_RANGES, EEO5_COLUMN_NAMES

# === Paths ===
json_input_dir = "/Users/anthonytsehuang/Documents/eeo-clone/output_eeo4/filter_output_test"
output_dir = "/Users/anthonytsehuang/Documents/eeo-clone/output_eeo4/filter_output_test"

EEO4_TABLE_A_ROW_NAMES = [f"{cat}, {sal}" for cat in EEO4_TABLE_JOB_CATEGORIES[:-1] for sal in EEO4_TABLE_A_SALARY_RANGES] + ["Total"]
EEO4_COLUMN_NAMES = EEO5_COLUMN_NAMES

# === Load all JSON files ===
flat_rows = []
json_files = get_files_in_directory(json_input_dir, extension="json")

for json_file in json_files:
    json_path = os.path.join(json_input_dir, json_file)
    with open(json_path) as f:
        data = json.load(f)

    # Extract top-level information
    metadata = {
        "filename": data.get("filename", ""),
        "jurisdiction_name": data.get("jurisdiction_name", ""),
        "address": data.get("address", ""),
        "city": data.get("city", ""),
        "county": data.get("county", ""),
        "state": data.get("state", ""),
        "zipcode": data.get("zipcode", ""),
        "control_number": data.get("control_number", ""),
        "reporting_year": data.get("reporting_year", ""),
        "government_type": data.get("government_type", ""),
        "functions_other_description": data.get("functions_other_description", ""),
    }

    # Process each function report
    function_reports = data.get("function_reports", [])
    for report in function_reports:
        flat_row = metadata.copy()

        # Add function report specific fields
        flat_row["function_number"] = report.get("function_number", 0)
        flat_row["government_function"] = report.get("government_function", "")
        flat_row["departments_included"] = report.get("departments_included", "")
        flat_row["departments_not_included"] = report.get("departments_not_included", "")
        flat_row["remarks"] = report.get("remarks", "")

        # Flatten Table A (full-time)
        table_a = report.get("table_a", [])
        for i, row in enumerate(table_a):
            if i >= len(EEO4_TABLE_A_ROW_NAMES) - 1:
                continue  # Skip total row
            row_name = "FULL-TIME STAFF_" + EEO4_TABLE_A_ROW_NAMES[i]
            for j, val in enumerate(row):
                if j < len(EEO4_COLUMN_NAMES) - 1:
                    flat_row[f"{EEO4_COLUMN_NAMES[j]}_{row_name}"] = val

        # Flatten Table B (part-time)
        table_b = report.get("table_b", [])
        for i, row in enumerate(table_b):
            if i >= len(EEO4_TABLE_JOB_CATEGORIES) - 1:
                continue
            row_name = "PART-TIME STAFF_" + EEO4_TABLE_JOB_CATEGORIES[i]
            for j, val in enumerate(row):
                if j < len(EEO4_COLUMN_NAMES) - 1:
                    flat_row[f"{EEO4_COLUMN_NAMES[j]}_{row_name}"] = val

        # Flatten Table C (new hires)
        table_c = report.get("table_c", [])
        for i, row in enumerate(table_c):
            if i >= len(EEO4_TABLE_JOB_CATEGORIES) - 1:
                continue
            row_name = "FULL-TIME NEW HIRES_" + EEO4_TABLE_JOB_CATEGORIES[i]
            for j, val in enumerate(row):
                if j < len(EEO4_COLUMN_NAMES) - 1:
                    flat_row[f"{EEO4_COLUMN_NAMES[j]}_{row_name}"] = val

        if flat_row['government_function'] != "OTHER":
            flat_row['functions_other_description'] = ""
        flat_rows.append(flat_row)

# === Convert to DataFrame and export ===
df = pd.DataFrame(flat_rows)
df.to_csv(os.path.join(output_dir, "eeo4.csv"), index=False)

# === Reload and print county-level summary ===
df = pd.read_csv(os.path.join(output_dir, "eeo4.csv"))
print(f"Total rows: {len(df)}")
if 'county' in df.columns:
    group_counts = df.groupby('county').size()
    print(group_counts)
