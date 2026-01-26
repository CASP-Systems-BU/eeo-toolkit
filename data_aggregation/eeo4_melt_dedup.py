"""
This script processes EEO-4 staff composition data and generates
different levels of differentially private contingency tables.

This is the dedup version that excludes Table C (new hires) to avoid
double-counting, as new hires are a subset of full-time staff.

Steps:
1. Load and melt the original dataset to a long format with extracted fields:
   Race, Gender, Work Type, Job Category, and Salary Range (for full-time staff).
2. Aggregate counts grouped by combinations of demographic and job-related features.
3. Apply Laplace noise to create differentially private 3-way tables.
4. Derive 2-way tables by collapsing over one dimension of 3-way tables and taking the median.
5. Generate 1-way marginal distributions for each feature.

Output:
- Differentially private 1-way, 2-way, and 3-way contingency tables as CSVs.
"""

import pandas as pd
import os
import numpy as np
from itertools import combinations
from collections import defaultdict
from const import EEO4_TABLE_JOB_CATEGORIES, EEO4_TABLE_A_SALARY_RANGES, EEO5_COLUMN_NAMES

# Laplace noise parameter (epsilon)
epsilon = 1 / 21

# Input/output paths
input_dir = "/Users/anthonytsehuang/Documents/eeo-clone/output_eeo4/filter_output_test"
output_dir_dp = f"{input_dir}/../eeo4_contingency_tables_dedup_dp"

all_fields = ["Race", "Gender", "Work Type", "Job Category", "Government Function"]
RACE_GENDER_COLS = EEO5_COLUMN_NAMES[:-1]
JOB_CATEGORIES = EEO4_TABLE_JOB_CATEGORIES[:-1]
SALARY_RANGES = EEO4_TABLE_A_SALARY_RANGES

# Format: "{Race}_{Gender}_{Work Type}_{Job Category}" or "{Race}_{Gender}_{Work Type}_{Job Category}, {Salary Range}"
value_vars = []

for job_cat in JOB_CATEGORIES:
    for salary in SALARY_RANGES:
        for race_gender in RACE_GENDER_COLS:
            value_vars.append(f"{race_gender}_FULL-TIME STAFF_{job_cat}, {salary}")

for job_cat in JOB_CATEGORIES:
    for race_gender in RACE_GENDER_COLS:
        value_vars.append(f"{race_gender}_PART-TIME STAFF_{job_cat}")

agg_df = pd.read_csv(os.path.join(input_dir, "eeo4_dedup.csv"), low_memory=False)
id_vars = ["government_function"]

# Filter to only columns that exist in the dataframe
existing_value_vars = [v for v in value_vars if v in agg_df.columns]
print(f"Melting {len(existing_value_vars)} columns out of {len(value_vars)} expected")

df_melted = agg_df.melt(
    id_vars=id_vars,
    value_vars=existing_value_vars,
    var_name="Race_Gender_Work_Type_Job_Category",
    value_name="Count",
)

def parse_column_name(col_name):
    """Parse column name into Race, Gender, Work Type, Job Category."""
    parts = col_name.split("_")
    race = parts[0]
    gender = parts[1]

    rest = "_".join(parts[2:])
    if rest.startswith("FULL-TIME STAFF_"):
        work_type = "FULL-TIME STAFF"
        job_category = rest.replace("FULL-TIME STAFF_", "")
    elif rest.startswith("PART-TIME STAFF_"):
        work_type = "PART-TIME STAFF"
        job_category = rest.replace("PART-TIME STAFF_", "")
    else:
        work_type = "Unknown"
        job_category = rest

    return pd.Series([race, gender, work_type, job_category])

df_melted[["Race", "Gender", "Work Type", "Job Category"]] = df_melted["Race_Gender_Work_Type_Job_Category"].apply(parse_column_name)
df_melted = df_melted.drop(columns=["Race_Gender_Work_Type_Job_Category"])

# Rename government_function to Government Function
df_melted = df_melted.rename(columns={"government_function": "Government Function"})

# === Group and aggregate ===
df_melted = df_melted.groupby(all_fields)["Count"].sum().reset_index()
df_melted.to_csv(os.path.join(input_dir, "melted_data_dedup.csv"), index=False)

print(f"Melted data saved with {len(df_melted)} rows")

# Reload the melted file
df_melted = pd.read_csv(os.path.join(input_dir, "melted_data_dedup.csv"))

# Create output directories
os.makedirs(os.path.join(output_dir_dp, "three_way"), exist_ok=True)
os.makedirs(os.path.join(output_dir_dp, "two_way"), exist_ok=True)

# === Generate 3-way contingency tables with differential privacy ===
three_combos = list(combinations(all_fields, 3))
noisy_three_way_tables = []

for combo in three_combos:
    grouped = df_melted.groupby(list(combo))["Count"].sum().reset_index()
    # Add Laplace noise for differential privacy
    grouped["Count"] = grouped["Count"] + np.random.laplace(
        loc=0, scale=1 / epsilon, size=len(grouped)
    )
    filename = "_".join(combo).replace(" ", "_") + "_contingency.csv"
    noisy_three_way_tables.append(grouped.copy())
    grouped.to_csv(os.path.join(output_dir_dp, "three_way", filename), index=False)
    print(f"Saved: {filename}")

# === Derive 2-way tables by collapsing 3-way tables ===
two_way_table_dict = defaultdict(list)

for table in noisy_three_way_tables:
    features = [col for col in table.columns if col != "Count"]
    for i in range(3):
        for j in range(i + 1, 3):
            A, B = features[i], features[j]
            collapsed = table.groupby([A, B])["Count"].sum().reset_index()
            collapsed.set_index([A, B], inplace=True)
            two_way_table_dict[frozenset([A, B])].append(collapsed)

# Combine and median-aggregate to get final 2-way tables
final_two_way_tables = {}

for pair, tables in two_way_table_dict.items():
    combined = pd.concat(tables, axis=1)
    median_series = combined.median(axis=1)
    median_series.index.names = list(next(iter(tables)).index.names)
    median_table = median_series.reset_index(name="Count")
    filename = "_".join(pair).replace(" ", "_") + "_contingency.csv"
    median_table.to_csv(os.path.join(output_dir_dp, "two_way", filename), index=False)
    final_two_way_tables[pair] = median_table

# === Derive 1-way tables from 2-way tables ===
one_way_table_dict = defaultdict(list)

for pair, table in final_two_way_tables.items():
    A, B = list(pair)
    for feature in [A, B]:
        collapsed = table.groupby(feature)["Count"].sum().reset_index()
        collapsed.set_index(feature, inplace=True)
        one_way_table_dict[feature].append(collapsed)

# Combine and median-aggregate to get final 1-way tables
final_one_way_tables = {}

for feature, tables in one_way_table_dict.items():
    combined = pd.concat(tables, axis=1)
    median_series = combined.median(axis=1)
    median_series.index.names = list(next(iter(tables)).index.names)
    median_table = median_series.reset_index(name="Count")
    filename = f"Employee_Distribution_by_{feature}.csv"
    median_table.to_csv(os.path.join(output_dir_dp, filename), index=False)
    final_one_way_tables[feature] = median_table

print("Done!")
