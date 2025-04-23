"""
This script processes EEO-5 staff composition data and generates 
different levels of differentially private contingency tables.

Steps:
1. Load and melt the original dataset to a long format with extracted fields: Race, Gender, Work Type, and Job Category.
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

# Laplace noise parameter (epsilon)
epsilon = 1 / 21

# Input/output paths
input_dir = "/home/node0/Documents/eeo5_json_corrected/filtered"
output_dir = f"{input_dir}/../eeo5_contingency_tables"
output_dir_dp = f"{input_dir}/../eeo5_contingency_tables_dp"

# Feature columns for analysis
all_fields = ['Race', 'Gender', 'Work Type', 'Job Category', 'Type of Agent']

# Load raw flattened EEO-5 data
agg_df = pd.read_csv(os.path.join(input_dir, "eeo5.csv"), low_memory=False)

# === MELT into long format ===
# Identify columns to melt (i.e., demographic breakdowns)
id_vars = ['Type of Agent']
# You already have a long list of value_vars provided in the script
# (value_vars = [ ... ])

# Melt to long format and extract Race, Gender, Work Type, and Job Category
df_melted = agg_df.melt(id_vars=id_vars, value_vars=value_vars,
                        var_name='Race_Gender_Work Type_Job Category',
                        value_name='Count')
df_melted[['Race', 'Gender', 'Work Type', 'Job Category']] = df_melted[
    'Race_Gender_Work Type_Job Category'].str.rsplit('_', n=3, expand=True)
df_melted = df_melted.drop(columns=['Race_Gender_Work Type_Job Category'])

# === Group and aggregate ===
df_melted = df_melted.groupby(all_fields)['Count'].sum().reset_index()
df_melted.to_csv(os.path.join(input_dir, "melted_data.csv"), index=False)

# Reload the melted file
df_melted = pd.read_csv(os.path.join(input_dir, "melted_data.csv"))

# === Generate 3-way contingency tables with differential privacy ===
three_combos = list(combinations(all_fields, 3))
two_combos = list(combinations(all_fields, 2))
noisy_three_way_tables = []

for combo in three_combos:
    grouped = df_melted.groupby(list(combo))['Count'].sum().reset_index()
    # Add Laplace noise for differential privacy
    grouped['Count'] = grouped['Count'] + np.random.laplace(loc=0, scale=1 / epsilon, size=len(grouped))
    filename = '_'.join(combo).replace(' ', '_') + '_contingency.csv'
    noisy_three_way_tables.append(grouped.copy())
    grouped.to_csv(os.path.join(output_dir_dp, "three_way", filename), index=False)
    print(f"Saved: {filename}")

# === Derive 2-way tables by collapsing 3-way tables ===
two_way_table_dict = defaultdict(list)

for table in noisy_three_way_tables:
    features = [col for col in table.columns if col != 'Count']
    for i in range(3):
        for j in range(i + 1, 3):
            A, B = features[i], features[j]
            collapsed = table.groupby([A, B])['Count'].sum().reset_index()
            collapsed.set_index([A, B], inplace=True)
            two_way_table_dict[frozenset([A, B])].append(collapsed)

# Combine and median-aggregate to get final 2-way tables
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

# Combine and median-aggregate to get final 1-way tables
final_one_way_tables = {}

for feature, tables in one_way_table_dict.items():
    combined = pd.concat(tables, axis=1)
    median_series = combined.median(axis=1)
    median_series.index.names = list(next(iter(tables)).index.names)
    median_table = median_series.reset_index(name='Count')
    filename = f"Employee_Distribution_by_{feature}.csv"
    median_table.to_csv(os.path.join(output_dir_dp, filename), index=False)
    final_one_way_tables[feature] = median_table
