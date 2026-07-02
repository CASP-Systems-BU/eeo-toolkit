"""
This script converts EEO-4 filter output JSON files into a tabular CSV format.
Each JSON file represents one government function report and contains both
jurisdiction metadata and function-specific table data at the top level.
"""

import pandas as pd
import numpy as np
import os
import json
from utils import get_files_in_directory
from const import EEO4_TABLE_JOB_CATEGORIES, EEO4_TABLE_A_SALARY_RANGES, EEO5_COLUMN_NAMES

# === Paths ===
json_input_dir = "/home/eolwd/data/eeo4_filter"
output_dir = "/home/eolwd/data/eeo4_csv"

EEO4_TABLE_A_ROW_NAMES = [f"{cat}, {sal}" for cat in EEO4_TABLE_JOB_CATEGORIES[:-1] for sal in EEO4_TABLE_A_SALARY_RANGES] + ["Total"]
EEO4_COLUMN_NAMES = EEO5_COLUMN_NAMES

# === Load all JSON files ===
flat_rows = []
json_files = get_files_in_directory(json_input_dir, extension="json")

for json_file in json_files:
    json_path = os.path.join(json_input_dir, json_file)
    with open(json_path) as f:
        data = json.load(f)

    flat_row = {
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
        "functions_other_description": data.get("functions_other_description", "").replace(";", " |"),
        "function_number": data.get("function_number", 0),
        "government_function": data.get("government_function", ""),
        "departments_included": data.get("departments_included", "").replace(";", " |"),
        "departments_not_included": data.get("departments_not_included", "").replace(";", " |"),
        "remarks": data.get("remarks", "").replace(";", " |"),
    }

    # Flatten Table A (full-time)
    table_a = data.get("table_a", [])
    for i, row in enumerate(table_a):
        if i >= len(EEO4_TABLE_A_ROW_NAMES) - 1:
            continue  # Skip total row
        row_name = "FULL-TIME STAFF_" + EEO4_TABLE_A_ROW_NAMES[i]
        for j, val in enumerate(row):
            if j < len(EEO4_COLUMN_NAMES) - 1:
                flat_row[f"{EEO4_COLUMN_NAMES[j]}_{row_name}"] = val

    # Flatten Table B (part-time)
    table_b = data.get("table_b", [])
    for i, row in enumerate(table_b):
        if i >= len(EEO4_TABLE_JOB_CATEGORIES) - 1:
            continue
        row_name = "PART-TIME STAFF_" + EEO4_TABLE_JOB_CATEGORIES[i]
        for j, val in enumerate(row):
            if j < len(EEO4_COLUMN_NAMES) - 1:
                flat_row[f"{EEO4_COLUMN_NAMES[j]}_{row_name}"] = val

    # Flatten Table C (new hires)
    table_c = data.get("table_c", [])
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
df.to_csv(os.path.join(output_dir, "aggregation.csv"), index=False)

# === Reload for county-level processing ===
df = pd.read_csv(os.path.join(output_dir, "aggregation.csv"))


fulltime_cols = [c for c in df.columns if "FULL-TIME STAFF" in c]
org_size_df = df.groupby("filename")[fulltime_cols].sum().sum(axis=1).reset_index()
org_size_df.columns = ["filename", "Organizational Size"]
org_size_df.to_csv(os.path.join(output_dir, "org_size.csv"), index=False)

df = df.merge(org_size_df, on="filename", how="left")
bins = np.unique(np.nanpercentile(df['Organizational Size'].dropna(), [0, 25, 50, 75, 100]))

if len(bins) > 1:
    all_labels = ['Small', 'Medium', 'Large', 'Very Large']
    df['Organizational Size Binned'] = pd.cut(
        df['Organizational Size'],
        bins=bins,
        labels=all_labels[:len(bins) - 1],
        include_lowest=True
    )

df['zip5'] = df['zipcode'].astype(str).str.extract(r"^(\d{4,5})")[0].str.zfill(5)
df.to_csv(os.path.join(output_dir, "join.csv"), index=False)

# === Step 5: Join with ZIP-to-county mapping ===
zip_to_county_df = pd.read_csv("../public_data/geocorr2022_2510107037.csv")
zip_to_county_df = zip_to_county_df.iloc[3:, :]
zip_to_county_df['zcta'] = zip_to_county_df['zcta'].astype(str)
zip_to_county_df = zip_to_county_df.sort_values("afact", ascending=False).drop_duplicates(subset="zcta", keep="first")
zip_to_county_df = zip_to_county_df[['zcta', 'CountyName']]

# Merge geocorr ZIP-to-county data
df = df.merge(zip_to_county_df, left_on='zip5', right_on='zcta', how='left')
if "CountyName" in df.columns:
    df['County Only'] = df['CountyName'].str.replace(r"\s[A-Z]{2}$", "", regex=True)
else:
    df['County Only'] = np.nan

additional_zip_df = pd.read_csv("../public_data/uscities.csv")
additional_zip_df = additional_zip_df[additional_zip_df["state_id"] == "MA"]
additional_zip_df['zips'] = additional_zip_df['zips'].str.strip("[]").str.split()
additional_zip_df = additional_zip_df.explode('zips')[['zips', 'county_name']].drop_duplicates(subset='zips', keep='first').rename(
        columns={'zips': 'zip', 'county_name': 'county_fallback'})

df = df.merge(additional_zip_df, left_on='zip5', right_on='zip', how='left')

df['County Name'] = np.where(
    df['County Only'].notna() & (df['County Only'] != ""),
    df['County Only'],
    df.get("county_fallback", np.nan)
)

df = df.drop(columns=[
        'county', 'county_fallback', 'zip', 'County Only', 'CountyName', 'zcta', 'zip5'
    ], errors='ignore')

df = df[df["state"].str.upper() == "MA"]
df.to_csv(os.path.join(output_dir, "join_with_county.csv"), index=False)
print("Saved join_with_county.csv")
