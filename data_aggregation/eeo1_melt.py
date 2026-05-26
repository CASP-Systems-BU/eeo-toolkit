"""
This script generates differentially private contingency tables from EEO-1 data.
It performs the following steps:
1. Reads and melts EEO-1 data into a long format (Race x Gender x Dimensions).
2. Aggregates counts into a 4-way main table (JobCategory x NAICS x Race x Gender).
3. Applies OpenDP Laplace noise to the 4-way table and 9 curated 3-way side tables.
The output includes a differentially private 4-way main table and 3-way side tables,
saved as individual CSV files.
"""

import pandas as pd
import os
import numpy as np
from itertools import combinations
from collections import defaultdict
from const import RACE_GENDER_COLUMNS

# opendp setup
import opendp.prelude as dp
dp.enable_features("contrib")

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

# Reload for safety
df = pd.read_csv(os.path.join(input_dir, "melted_data.csv"))

# remove Public Administration industry type (this is in EEO-4 instead)
df_new = df[~(df["NAICS_label"] == "Public Administration")]

# === Generate all 3-way combinations ===
# three_combos = list(combinations(all_fields, 3))
# two_combos = list(combinations(all_fields, 2))
four_combo = ['JobCategory', 'NAICS_label', 'Race', 'Gender']
three_combos = [('JobCategory', 'Organizational Size Binned', 'Race'), ('JobCategory', 'Organizational Size Binned', 'Gender'), ('NAICS_label', 'Organizational Size Binned', 'Race'), ('NAICS_label', 'Organizational Size Binned', 'Gender'), ('JobCategory', 'County Name', 'Race'), ('JobCategory', 'County Name', 'Gender'), ('NAICS_label', 'County Name', 'Race'), ('NAICS_label', 'County Name', 'Gender'), ('Gender', 'Organizational Size Binned', 'Race')]

# Save the (real!) main 4-way table
main_df = df_new.groupby(four_combo)['Count'].sum().reset_index()
main_df.to_csv("temp_real_main.csv", index=False)

# Add Laplace noise and save the noisy 4-way table
main_epsilon = 0.4
space = (dp.atom_domain(T=int, nan=False), dp.absolute_distance(T=int))
laplace_noise_main = dp.m.make_laplace(*space, scale=1.0/main_epsilon)
main_df['Count'] = main_df['Count'].apply(lambda x: laplace_noise_main(x))
main_df.to_csv("dp_main.csv", index=False)


# Add Laplace noise and save each 3-way side table
# noisy_three_way_tables = []
side_epsilon = 0.7 / 8 # whoops, actually made 9 of them this year using this epsilon
laplace_noise_side = dp.m.make_laplace(*space, scale=1.0/side_epsilon)

for combo in three_combos:
    side_df = df_new.groupby(list(combo))['Count'].sum().reset_index()
    filename = 'side_' + ''.join(field[0] for field in combo) + '.csv'
    side_df.to_csv("temp_real_" + filename, index=False)
    side_df['Count'] = side_df['Count'].apply(lambda x: laplace_noise_side(x))
    side_df.to_csv("temp_dp_" + filename, index=False)