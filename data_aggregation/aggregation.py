import os
import json
import glob

import pandas as pd

from const import COLUMN_NAMES, RACE_PAIRS, JOB_CATEGORIES, RACE_GENDER_COLUMNS
from custom_types import YearType, TableType


def json_to_df(path: str, year_type: YearType):
    agg_columns = COLUMN_NAMES + ["State", "City", "Headquarter State", "Headquarter City", "NAICS", "Year", "JobCategory", "NAICS Name", "zip code", "HQ zip code", "filename"]
    agg_df = pd.DataFrame(columns=agg_columns)

    json_file_paths = glob.glob(os.path.join(path, "**", "*.json"), recursive=True)

    for file_path in json_file_paths:
        print(file_path)
        with open(file_path, "r") as f:
            record = json.load(f)
        df_table = pd.DataFrame(record["table"], columns=COLUMN_NAMES)
        print(df_table)

        # Assign the job category labels (one label per row).
        df_table["JobCategory"] = JOB_CATEGORIES

        # Attach identifying columns.
        df_table["City"] = record["city"]
        df_table["State"] = record["state"]
        df_table["Headquarter State"] = record["headquarter_state"]
        df_table["Headquarter City"] = record["headquarter_city"]
        df_table["NAICS"] = record["NAICS"]
        df_table["NAICS Name"] = record["NAICS_name"]
        df_table["zip code"] = str(record["zipcode"])
        df_table['zip code'] = df_table['zip code'].astype(str)
        df_table["HQ zip code"] = str(record["headquarter_zipcode"])
        df_table['HQ zip code'] = df_table['HQ zip code'].astype(str)
        df_table["filename"] = record["filename"]
        df_table["Year"] = record["reporting_year"]  # from the JSON record

        # Optionally, group by City, NAICS, Year, JobCategory if
        # you suspect duplicates for the same job category in multiple records.
        group_df = df_table.groupby(
            ["State", "City", "Headquarter State", "Headquarter City", "NAICS", "Year", "JobCategory", "NAICS Name", "zip code", "HQ zip code", "filename"], as_index=False
        ).sum(numeric_only=True)

        # Merge into our aggregator DataFrame.
        if agg_df.empty:
            agg_df = group_df
        else:
            agg_df = agg_df.set_index(["State", "City", "Headquarter State", "Headquarter City", "NAICS", "Year", "JobCategory", "NAICS Name", "zip code", "HQ zip code", "filename"])
            group_df = group_df.set_index(["State", "City", "Headquarter State", "Headquarter City", "NAICS", "Year", "JobCategory", "NAICS Name", "zip code", "HQ zip code", "filename"])
            agg_df = agg_df.add(group_df, fill_value=0).reset_index()

    return agg_df


def _create_gender_race_contingency(agg_df: pd.DataFrame) -> pd.DataFrame:
    # We'll build a long-format list of dictionaries.
    long_rows = []

    # Loop through each aggregated row.
    for _, row in agg_df.iterrows():
        for race, cols in RACE_PAIRS.items():
            # Create a record for Male.
            long_rows.append({"Gender": "Male", "Race": race, "Count": row[cols[0]]})
            # Create a record for Female.
            long_rows.append({"Gender": "Female", "Race": race, "Count": row[cols[1]]})

    # Create a DataFrame from the long rows.
    df_long = pd.DataFrame(long_rows)

    # Group by Gender and Race, summing the counts.
    contingency = (
        df_long.groupby(["Gender", "Race"])["Count"].sum().unstack("Race", fill_value=0)
    )
    return contingency


def generate_contingency_table(
    agg_df, table_type: TableType, year_type: YearType = None
) -> pd.DataFrame:

    if table_type == TableType.NAICS_AND_GENDER:
        if year_type is not None:
            if year_type == YearType.CURRENT:
                agg_df = agg_df.loc[
                    agg_df["JobCategory"] == "CURRENT REPORTING YEAR TOTAL"
                ].copy()
            elif year_type == YearType.PREVIOUS:
                agg_df = agg_df.loc[
                    agg_df["JobCategory"] == "PRIOR REPORTING YEAR TOTAL"
                ].copy()
        else:
            raise Exception("table_type cannot be empty")

        male_columns = [
            col for col in COLUMN_NAMES if "Male" in col and col != "Row Total"
        ]
        female_columns = [
            col for col in COLUMN_NAMES if "Female" in col and col != "Row Total"
        ]

        agg_df.loc[:, "Total Male"] = agg_df[male_columns].sum(axis=1)
        agg_df.loc[:, "Total Female"] = agg_df[female_columns].sum(axis=1)

        naics_gender_ct = (
            agg_df.groupby("NAICS_label")[["Total Male", "Total Female"]].sum().reset_index()
        )
        return naics_gender_ct

    elif table_type == TableType.NAICS_AND_RACE:
        if year_type is not None:
            if year_type == YearType.CURRENT:
                agg_df = agg_df.loc[
                    agg_df["JobCategory"] == "CURRENT REPORTING YEAR TOTAL"
                ].copy()
            elif year_type == YearType.PREVIOUS:
                agg_df = agg_df.loc[
                    agg_df["JobCategory"] == "PRIOR REPORTING YEAR TOTAL"
                ].copy()
        else:
            raise Exception("table_type cannot be empty")

        for race, cols in RACE_PAIRS.items():
            agg_df.loc[:, race] = agg_df[cols].sum(axis=1)

        race_ct = agg_df.groupby("NAICS_label")[list(RACE_PAIRS.keys())].sum().reset_index()
        return race_ct

    elif table_type == TableType.GENDER_AND_RACE:
        if year_type is not None:
            if year_type == YearType.CURRENT:
                agg_df = agg_df.loc[
                    agg_df["JobCategory"] == "CURRENT REPORTING YEAR TOTAL"
                ].copy()
            elif year_type == YearType.PREVIOUS:
                agg_df = agg_df.loc[
                    agg_df["JobCategory"] == "PRIOR REPORTING YEAR TOTAL"
                ].copy()
        else:
            raise Exception("table_type cannot be empty")
        return _create_gender_race_contingency(agg_df)

    elif table_type == TableType.GENDER_AND_JOB:
        df_filtered = agg_df.loc[
            ~agg_df["JobCategory"].isin(
                ["CURRENT REPORTING YEAR TOTAL", "PRIOR REPORTING YEAR TOTAL"]
            )
        ].copy()

        male_columns = [
            col for col in COLUMN_NAMES if "Male" in col and col != "Row Total"
        ]
        female_columns = [
            col for col in COLUMN_NAMES if "Female" in col and col != "Row Total"
        ]

        df_filtered.loc[:, "Total Male"] = df_filtered[male_columns].sum(axis=1)
        df_filtered.loc[:, "Total Female"] = df_filtered[female_columns].sum(axis=1)

        gender_job_ct = (
            df_filtered.groupby("JobCategory")[["Total Male", "Total Female"]]
            .sum()
            .reset_index()
        )
        return gender_job_ct

    elif table_type == TableType.RACE_AND_JOB:
        df_filtered = agg_df.loc[
            ~agg_df["JobCategory"].isin(
                ["CURRENT REPORTING YEAR TOTAL", "PRIOR REPORTING YEAR TOTAL"]
            )
        ].copy()
        for race, cols in RACE_PAIRS.items():
            df_filtered.loc[:, race] = df_filtered[cols].sum(axis=1)
        race_job_ct = (
            df_filtered.groupby("JobCategory")[list(RACE_PAIRS.keys())]
            .sum()
            .reset_index()
        )
        return race_job_ct

    elif table_type == TableType.NAICS_AND_JOB:
        df_filtered = agg_df.loc[
            ~agg_df["JobCategory"].isin(
                ["CURRENT REPORTING YEAR TOTAL", "PRIOR REPORTING YEAR TOTAL"]
            )
        ].copy()
        naics_job_ct = (
            df_filtered.groupby(["NAICS_label", "JobCategory"])["Row Total"]
            .sum()
            .unstack("JobCategory", fill_value=0)
            .reset_index()
        )
        return naics_job_ct

    elif table_type == TableType.GENDER_RACE_JOB:
        df_filtered = agg_df.loc[
            ~agg_df["JobCategory"].isin(
                ["CURRENT REPORTING YEAR TOTAL", "PRIOR REPORTING YEAR TOTAL"]
            )
        ].copy()
        tri_ct = (
            df_filtered.groupby(["JobCategory"])[RACE_GENDER_COLUMNS]
            .sum()
            .reset_index()
        )
        return tri_ct

