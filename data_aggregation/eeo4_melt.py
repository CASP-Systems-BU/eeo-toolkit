"""
This script reads and melts EEO-4 staff composition data into a long format.

Steps:
1. Load and melt the original dataset to a long format with extracted fields:
   Race, Gender, Work Type, Job Category, and Salary Range (for full-time staff).
2. Merge in state employment data (full-time, part-time, new hires).
3. Aggregate counts and build a full index so every combination is represented.

Output is melted_data.csv, consumed by eeo4_dp.py for differential privacy.
"""

import pandas as pd
import os
from itertools import product as iterproduct
from const import EEO4_TABLE_JOB_CATEGORIES, EEO4_TABLE_A_SALARY_RANGES, EEO5_COLUMN_NAMES

# Input/output paths
input_dir = "/home/eolwd/data/eeo4_csv"
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
        salary_range = "-"

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

