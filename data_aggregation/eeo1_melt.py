"""
This script reads and melts EEO-1 data into a long format (Race x Gender x Dimensions).
It performs the following steps:
1. Loads raw EEO-1 data and filters out summary job categories.
2. Melts wide Race/Gender columns into long format.
3. Materializes the full Cartesian product of dimension values (missing combos → 0).
The output is melted_data.csv, consumed by eeo1_dp.py for differential privacy.
"""

import pandas as pd
import os
from const import RACE_GENDER_COLUMNS

# Input/output paths
input_dir = "/home/node0/Documents/csv_output"

# Define fields for analysis
all_fields = ['JobCategory', 'NAICS_label', 'Organizational Size Binned', 'County Name', 'Race', 'Gender']
excluded_jobs = ["CURRENT REPORTING YEAR TOTAL", "PRIOR REPORTING YEAR TOTAL"]

# === Load and preprocess the data ===
agg_df = pd.read_csv(os.path.join(input_dir, "join_with_county.csv"), low_memory=False)

# Filter out summary job categories
df_filtered = agg_df[~agg_df["JobCategory"].isin(excluded_jobs)].copy()

# === Convert to long format ===
id_vars = ['JobCategory', 'NAICS_label', 'Organizational Size Binned', 'County Name']
value_vars = RACE_GENDER_COLUMNS

# Melt wide format into long format by Race and Gender
df_melted = df_filtered.melt(id_vars=id_vars, value_vars=value_vars, var_name='Race_Gender', value_name='Count')
df_melted[['Race', 'Gender']] = df_melted['Race_Gender'].str.rsplit(' ', n=1, expand=True)
df_melted = df_melted.drop(columns=['Race_Gender'])

# Aggregate identical records
df_melted = df_melted.groupby(all_fields)['Count'].sum().reset_index()

# Materialize the full Cartesian product so every combination exists; missing combinations fill with 0
# to ensure downstream contingency tables have aligned indices
full_index = pd.MultiIndex.from_product([df_melted[f].unique() for f in all_fields], names=all_fields)
df_melted = df_melted.set_index(all_fields).reindex(full_index, fill_value=0).reset_index()

df_melted.to_csv(os.path.join(input_dir, "melted_data.csv"), index=False)

print(f"\nMelted data saved with {len(df_melted)} rows")