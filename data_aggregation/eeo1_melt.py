"""
This script generates differentially private contingency tables from EEO-1 data.
It performs the following steps:
1. Reads and melts EEO-1 data into a long format (Race x Gender x Dimensions).
2. Aggregates counts for all 3-way combinations of key fields.
3. Applies Laplace noise to ensure differential privacy.
4. Derives 2-way tables from the noisy 3-way tables using median aggregation.
5. Further collapses to 1-way tables for basic feature distributions.
The output includes differentially private one-way, two-way, and three-way tables,
saved as individual CSV files for each combination.
"""

import pandas as pd
import os
import numpy as np
from itertools import combinations
from collections import defaultdict
from const import RACE_GENDER_COLUMNS

# Laplace noise scale
epsilon = 1 / 21

# Input/output paths
input_dir = "/home/node0/Documents/csv_output"
output_dir = f"{input_dir}/eeo1_contingency_tables"
output_dir_dp = f"{input_dir}/eeo1_contingency_tables_dp"

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
df_melted.to_csv(os.path.join(input_dir, "melted_data.csv"), index=False)

# Reload for safety
df_melted = pd.read_csv(os.path.join(input_dir, "melted_data.csv"))

# === Generate all 3-way combinations ===
three_combos = list(combinations(all_fields, 3))
two_combos = list(combinations(all_fields, 2))
noisy_three_way_tables = []

# Add Laplace noise and save each 3-way contingency table
for combo in three_combos:
    grouped = df_melted.groupby(list(combo))['Count'].sum().reset_index()
    grouped['Count'] = grouped['Count'] + np.random.laplace(loc=0, scale=1 / epsilon, size=len(grouped))
    filename = '_'.join(combo).replace(' ', '_') + '_contingency.csv'
    noisy_three_way_tables.append(grouped.copy())
    grouped.to_csv(os.path.join(output_dir_dp, "three_way", filename), index=False)
    print(f"Saved: {filename}")

# === Derive 2-way tables from 3-way tables by marginalizing ===
two_way_table_dict = defaultdict(list)

# For each 3-way table, collapse along all 2-way pairs
for table in noisy_three_way_tables:
    features = [col for col in table.columns if col != 'Count']
    for i in range(3):
        for j in range(i + 1, 3):
            A, B = features[i], features[j]
            collapsed = table.groupby([A, B])['Count'].sum().reset_index()
            collapsed.set_index([A, B], inplace=True)
            two_way_table_dict[frozenset([A, B])].append(collapsed)

# Combine 2-way tables using median across all derived versions
final_two_way_tables = {}

for pair, tables in two_way_table_dict.items():
    combined = pd.concat(tables, axis=1)
    median_series = combined.median(axis=1)
    median_series.index.names = list(next(iter(tables)).index.names)
    median_table = median_series.reset_index(name='Count')
    filename = '_'.join(pair).replace(' ', '_') + '_contingency.csv'
    median_table.to_csv(os.path.join(output_dir_dp, "two_way", filename), index=False)
    final_two_way_tables[pair] = median_table

# === Derive 1-way tables from 2-way tables ===
one_way_table_dict = defaultdict(list)

for pair, table in final_two_way_tables.items():
    A, B = list(pair)
    for feature in [A, B]:
        collapsed = table.groupby(feature)['Count'].sum().reset_index()
        collapsed.set_index(feature, inplace=True)
        one_way_table_dict[feature].append(collapsed)

# Combine 1-way tables using median
final_one_way_tables = {}

for feature, tables in one_way_table_dict.items():
    combined = pd.concat(tables, axis=1)
    median_series = combined.median(axis=1)
    median_series.index.names = list(next(iter(tables)).index.names)
    median_table = median_series.reset_index(name='Count')
    filename = f"Employee_Distribution_by_{feature}.csv"
    median_table.to_csv(os.path.join(output_dir_dp, filename), index=False)
    final_one_way_tables[feature] = median_table
