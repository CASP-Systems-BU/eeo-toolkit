import os
import json
import glob

import pandas as pd

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

        # Extract the main table from JSON and convert it to DataFrame
        df_table = pd.DataFrame(record["table"], columns=COLUMN_NAMES)
        print(df_table)

        # Add job category label to each row
        df_table["JobCategory"] = JOB_CATEGORIES

        # Populate metadata columns from JSON record
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

        # Group to remove duplicate rows for same job category in same file
        group_df = df_table.groupby(
            [
                "State", "City", "Headquarter State", "Headquarter City", "NAICS", "Year",
                "JobCategory", "NAICS Name", "zip code", "HQ zip code", "filename"
            ],
            as_index=False
        ).sum(numeric_only=True)

        # Aggregate with previous data
        if agg_df.empty:
            agg_df = group_df
        else:
            # Align indexes for addition
            agg_df = agg_df.set_index(group_df.columns[:-1])
            group_df = group_df.set_index(group_df.columns[:-1])
            agg_df = agg_df.add(group_df, fill_value=0).reset_index()

    return agg_df

