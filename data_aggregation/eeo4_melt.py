"""
This script processes EEO-4 staff composition data and generates
different levels of differentially private contingency tables.

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
from itertools import combinations, product as iterproduct
from collections import defaultdict
from const import EEO4_TABLE_JOB_CATEGORIES, EEO4_TABLE_A_SALARY_RANGES, EEO5_COLUMN_NAMES

# Laplace noise parameter (epsilon)
epsilon = 1 / 21

# Input/output paths
input_dir = "/home/eolwd/data/eeo4_csv"
output_dir_dp = f"{input_dir}/eeo4_contingency_tables_dp"
state_dir = "/home/eolwd/data/state_data"

all_fields = ["Race", "Gender", "Work Type", "Job Category", "Salary Range", "Government Function", "Government Type"]
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

for job_cat in JOB_CATEGORIES:
    for race_gender in RACE_GENDER_COLS:
        value_vars.append(f"{race_gender}_FULL-TIME NEW HIRES_{job_cat}")

FUNCTION_NUMBER_TO_NAME = {1 : "FINANCIAL ADMINISTRATION/GENERAL CONTROL",
2 : "STREETS AND HIGHWAYS",
3 : "PUBLIC WELFARE",
4 : "POLICE PROTECTION",
5 : "FIRE PROTECTION",
6 : "NATURAL RESOURCES/PARKS AND RECREATION",
7 : "HOSPITALS",
8 : "HEALTH",
9 : "HOUSING",
10 : "COMMUNITY DEVELOPMENT",
11 : "CORRECTIONS",
12 : "UTILITIES AND TRANSPORTATION",
13 : "SANITATION AND SEWAGE",
14 : "EMPLOYMENT SECURITY",
15 : "OTHER",
100 : "UNSPECIFIED"
}

agg_df = pd.read_csv(os.path.join(input_dir, "join_with_county.csv"), low_memory=False)

# Prefer function_number when present — more reliable than the raw government_function string
if "function_number" in agg_df.columns:
    agg_df["government_function"] = agg_df["function_number"].map(FUNCTION_NUMBER_TO_NAME).fillna(agg_df["government_function"])

potential_id_vars = ["government_function", "government_type", "state", "reporting_year", "Organizational Size Binned"]
id_vars = [col for col in potential_id_vars if col in agg_df.columns]

# Filter to only columns that exist in the dataframe
existing_value_vars = [v for v in value_vars if v in agg_df.columns]

df_melted = agg_df.melt(
    id_vars=id_vars,
    value_vars=existing_value_vars,
    var_name="Race_Gender_Work_Type_Job_Category",
    value_name="Count",
)


def parse_column_name(col_name):
    """Parse a compound column name into Race, Gender, Work Type, Job Category, and Salary Range.

    Expected format: "{Race}_{Gender}_{Work Type}_{Job Category}" or
    "{Race}_{Gender}_FULL-TIME STAFF_{Job Category}, {Salary Range}"
    """
    parts = col_name.split("_")
    race = parts[0]
    gender = parts[1]
    rest = "_".join(parts[2:])

    if rest.startswith("FULL-TIME STAFF_"):
        work_type = "FULL-TIME STAFF"
        job_salary = rest.replace("FULL-TIME STAFF_", "")
        if ", $" in job_salary:
            job_category, salary_range = job_salary.rsplit(", $", 1)
            salary_range = "$" + salary_range
        else:
            job_category = job_salary
            salary_range = "-"
    elif rest.startswith("PART-TIME STAFF_"):
        work_type = "PART-TIME STAFF"
        job_category = rest.replace("PART-TIME STAFF_", "")
        salary_range = "-"
    elif rest.startswith("FULL-TIME NEW HIRES_"):
        work_type = "NEW HIRES"
        job_category = rest.replace("FULL-TIME NEW HIRES_", "")
        salary_range = "-"
    else:
        work_type = "Unknown"
        job_category = rest

    return pd.Series([race, gender, work_type, job_category, salary_range])

df_melted[["Race", "Gender", "Work Type", "Job Category", "Salary Range"]] = df_melted["Race_Gender_Work_Type_Job_Category"].apply(parse_column_name)
df_melted = df_melted.drop(columns=["Race_Gender_Work_Type_Job_Category"])

# Rename government_function to Government Function
df_melted = df_melted.rename(columns={"government_function": "Government Function", "government_type" : "Government Type"})

# === Group and aggregate ===
all_fields = [f for f in all_fields if f in df_melted.columns]
df_melted = df_melted.groupby(all_fields, dropna=False)["Count"].sum().reset_index()

# === Load and normalize state employment data ===
# Maps state CSV race/gender column headers to normalized (Race, Gender) tuples.
# State data uses a different naming convention than the local government data.
STATE_DEMO_COL_MAP = {
"HISPANIC OR LATINO Male" : ("Hispanic or Latino", "Male"),
"HISPANIC OR LATINO Female" : ("Hispanic or Latino", "Female"),
"NOT-HISPANIC OR LATINO White Male" : ("White", "Male"),
"NOT-HISPANIC OR LATINO Black or African American Male" : ("Black or African American", "Male"),
"NOT-HISPANIC OR LATINO Asian Male" : ("Asian", "Male"),
"NOT-HISPANIC OR LATINO Native Hawaiian or Other Pacific Islander Male" : ("Native Hawaiian or Other Pacific Islander", "Male"),
"NOT-HISPANIC OR LATINO American Indian or Alaska Native Male" : ("American Indian or Alaska Native", "Male"),
"NOT-HISPANIC OR LATINO Two or more races Male" : ("Two or More Races", "Male"),
"NOT-HISPANIC OR LATINO White Female" : ("White", "Female"),
"NOT-HISPANIC OR LATINO Black or African American Female" : ("Black or African American", "Female"),
"NOT-HISPANIC OR LATINO Asian Female" : ("Asian", "Female"),
"NOT-HISPANIC OR LATINO Native Hawaiian or Other Pacific Islander Female" : ("Native Hawaiian or Other Pacific Islander", "Female"),
"NOT-HISPANIC OR LATINO American Indian or Alaska Native Female" : ("American Indian or Alaska Native", "Female"),
"NOT-HISPANIC OR LATINO Two or more races Female" : ("Two or More Races", "Female"),
}

def _load_state_data(filepath, job_cat_col, work_type, output_filename, has_salary_range=False):
    """Load and normalize a state employment CSV into the long format used by df_melted.

    has_salary_range=True: file has a salary range column that needs renaming and
    normalization, and it becomes an id_var in the melt. False: salary range is
    not in the source — it is set to "-" after melting (part-time and new hires).
    """
    raw = pd.read_csv(filepath, low_memory=False)
    rename_map = {job_cat_col: "Job Category"}
    if has_salary_range:
        rename_map["Annual Salary (in thousands)"] = "Salary Range"
    raw.rename(columns=rename_map, inplace=True)
    raw["Job Category"] = raw["Job Category"].str.split(":").str[0]  # State CSVs append a descriptor after ":" — strip it
    raw["Job Category"] = raw["Job Category"].str.replace("Officials and Administrators", "Officials - Administrators")  # Reconcile naming discrepancy with local data
    if has_salary_range:
        raw["Salary Range"] = raw["Salary Range"].str.replace("-$", " - ")  # Normalize state salary range format to match local data
        raw["Salary Range"] = raw["Salary Range"].str.replace("$ 0.1 - 15.9", "$0.1 - 15.9")  # Fix specific formatting quirk in state source
    id_vars = ["Function", "Job Category"] + (["Salary Range"] if has_salary_range else [])
    demo_cols = [c for c in raw.columns if c in STATE_DEMO_COL_MAP]
    melted = raw.melt(id_vars=id_vars, value_vars=demo_cols, var_name="_demo", value_name="Count")
    if not has_salary_range:
        melted["Salary Range"] = "-"
    melted["Race"] = melted["_demo"].map(lambda c: STATE_DEMO_COL_MAP[c][0])
    melted["Gender"] = melted["_demo"].map(lambda c: STATE_DEMO_COL_MAP[c][1])
    melted["Work Type"] = work_type
    melted["Government Function"] = melted["Function"].map(FUNCTION_NUMBER_TO_NAME).fillna("UNSPECIFIED")
    melted["Government Type"] = "State"
    melted["Count"] = pd.to_numeric(melted["Count"], errors="coerce").fillna(0).astype(int)
    melted = melted.drop(columns=["_demo", "Function"])
    melted = melted.reindex(columns=df_melted.columns, fill_value=pd.NA)
    melted.to_csv(os.path.join(input_dir, output_filename), index=False)
    return melted

state_fulltime_melted = _load_state_data(
    os.path.join(state_dir, "E4_001_2025_Full-Time.csv"),
    job_cat_col="Full-Time Employees\tJob Categories",
    work_type="FULL-TIME STAFF",
    output_filename="state_fulltime.csv",
    has_salary_range=True,
)

state_parttime_melted = _load_state_data(
    os.path.join(state_dir, "E4_001_2025_Other_Than_Full-Time.csv"),
    job_cat_col="Other Than Full-Time Employees\tJob Categories",
    work_type="PART-TIME STAFF",
    output_filename="state_parttime.csv",
)

state_newhire_melted = _load_state_data(
    os.path.join(state_dir, "E4_001_2025_New_Hires.csv"),
    job_cat_col="New Hires During Fiscal Year\t(01-JUL-2024 - 30-JUN-2025)\tJob Categories",
    work_type="NEW HIRES",
    output_filename="state_newhire.csv",
)

# === Merge state data into local dataset and re-aggregate ===
df_melted = pd.concat([df_melted, state_fulltime_melted, state_parttime_melted, state_newhire_melted], ignore_index = True)
df_melted = df_melted.groupby(all_fields, dropna=False)["Count"].sum().reset_index()

MA_COUNTIES = ["Barnstable", "Berkshire", "Bristol", "Dukes", "Essex", "Franklin", "Hampden", "Hampshire", "Middlesex", "Nantucket", "Norfolk", "Plymouth", "Suffolk", "Worcester", "Unspecified"]

# === Build full index to ensure every combination is represented ===
# Work Type and Salary Range are coupled (only FULL-TIME STAFF has salary ranges;
# PART-TIME STAFF and NEW HIRES use "-"), so they are handled as pairs rather than
# independent dimensions. Missing combinations are filled with 0 after the merge.
dim = {f:sorted(df_melted[f].dropna().unique().tolist()) for f in all_fields if f not in ("Work Type", "Salary Range")}

work_salary_pairs = (
[("FULL-TIME STAFF", s) for s in SALARY_RANGES] +
[("PART-TIME STAFF", "-")] +
[("NEW HIRES", "-")])

other_fields = [f for f in all_fields if f not in ("Work Type", "Salary Range")]
full_rows = []
for wt, sal in work_salary_pairs:
    for combo in iterproduct(*[dim[f] for f in other_fields]):
        row = dict(zip(other_fields, combo))
        row["Work Type"] = wt
        row["Salary Range"] = sal
        full_rows.append(row)

full_index_df = pd.DataFrame(full_rows, columns=all_fields)
df_melted = full_index_df.merge(df_melted, on= all_fields, how = 'left')
df_melted["Count"] = df_melted["Count"].fillna(0).astype(int)

df_melted.to_csv(os.path.join(input_dir, "melted_data.csv"), index=False)

print(f"\nMelted data saved with {len(df_melted)} rows")

# Reload the melted file
df_melted = pd.read_csv(os.path.join(input_dir, "melted_data.csv"))

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
    # Each 3-way table contributes 3 pairwise 2-way marginals
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
