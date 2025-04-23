"""
This script processes a collection of JSON files containing tabular EEO data,
extracts structured fields along with metadata, and compiles all records into
a single aggregated pandas DataFrame. It handles duplicate job category entries
by grouping and summing numeric fields. This is especially useful for converting
scanned and OCR-processed form outputs into a structured tabular format for analysis.
"""

import os
import json
import glob
import pandas as pd

# Import predefined constants for expected columns and job categories
from const import COLUMN_NAMES, JOB_CATEGORIES

def json_to_df(path: str):
    """
    Load JSON files from nested directories, extract structured data,
    assign metadata columns, and aggregate the data into a single DataFrame.
    """
    # Define the columns for the final aggregated DataFrame
    agg_columns = COLUMN_NAMES + [
        "State", "City", "Headquarter State", "Headquarter City", "NAICS", "Year",
        "JobCategory", "NAICS Name", "zip code", "HQ zip code", "filename"
    ]
    agg_df = pd.DataFrame(columns=agg_columns)

    # Recursively collect paths to all JSON files in the directory
    json_file_paths = glob.glob(os.path.join(path, "**", "*.json"), recursive=True)

    for file_path in json_file_paths:
        print(file_path)
        with open(file_path, "r") as f:
            record = json.load(f)

        # Extract the main table from JSON and convert it to a DataFrame
        df_table = pd.DataFrame(record["table"], columns=COLUMN_NAMES)
        print(df_table)

        # Add job category labels to each row in the DataFrame
        df_table["JobCategory"] = JOB_CATEGORIES

        # Append identifying and contextual metadata from the JSON record
        df_table["City"] = record["city"]
        df_table["State"] = record["state"]
        df_table["Headquarter State"] = record["headquarter_state"]
        df_table["Headquarter City"] = record["headquarter_city"]
        df_table["NAICS"] = record["NAICS"]
        df_table["NAICS Name"] = record["NAICS_name"]
        df_table["zip code"] = str(record["zipcode"])
        df_table["HQ zip code"] = str(record["headquarter_zipcode"])
        df_table["filename"] = record["filename"]
        df_table["Year"] = record["reporting_year"]

        # Group by unique identifiers to remove duplicates and sum numeric columns
        group_df = df_table.groupby(
            [
                "State", "City", "Headquarter State", "Headquarter City", "NAICS", "Year",
                "JobCategory", "NAICS Name", "zip code", "HQ zip code", "filename"
            ],
            as_index=False
        ).sum(numeric_only=True)

        # Aggregate this record's data into the running DataFrame
        if agg_df.empty:
            agg_df = group_df
        else:
            # Align by index and sum up matching rows
            agg_df = agg_df.set_index(group_df.columns[:-1])
            group_df = group_df.set_index(group_df.columns[:-1])
            agg_df = agg_df.add(group_df, fill_value=0).reset_index()

    return agg_df
