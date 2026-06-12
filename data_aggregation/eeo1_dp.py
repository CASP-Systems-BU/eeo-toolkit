"""
This script applies differential privacy to pre-melted EEO-1 contingency tables.
It expects the output of eeo1_melt.py (melted_data.csv) as input and produces:
1. A noisy 4-way main table (JobCategory x NAICS x Race x Gender).
2. Nine noisy 3-way side tables over curated dimension combinations.
Both the real (pre-noise) and noisy versions of each table are saved as CSVs.
"""

import pandas as pd
import os

# opendp setup
import opendp.prelude as dp
dp.enable_features("contrib")

# Input/output paths
input_dir = "/home/node0/Documents/csv_output"

# Define the 4-way and curated 3-way dimension combos for aggregation
four_combo = ['JobCategory', 'NAICS_label', 'Race', 'Gender']
three_combos = [
    ('JobCategory', 'Organizational Size Binned', 'Race'),
    ('JobCategory', 'Organizational Size Binned', 'Gender'),
    ('NAICS_label', 'Organizational Size Binned', 'Race'),
    ('NAICS_label', 'Organizational Size Binned', 'Gender'),
    ('JobCategory', 'County Name', 'Race'),
    ('JobCategory', 'County Name', 'Gender'),
    ('NAICS_label', 'County Name', 'Race'),
    ('NAICS_label', 'County Name', 'Gender'),
    ('Gender', 'Organizational Size Binned', 'Race'),
]

# === Load pre-melted data ===
df = pd.read_csv(os.path.join(input_dir, "melted_data.csv"))

# Remove Public Administration industry type (covered by EEO-4 instead)
df_new = df[~(df["NAICS_label"] == "Public Administration")]

# === Build and noise the 4-way main table ===
# Generate the real (pre-noise) table for reference
main_df = df_new.groupby(four_combo)['Count'].sum().reset_index()

# Add Laplace noise to the 4-way table
main_epsilon = 0.4
space = (dp.atom_domain(T=int, nan=False), dp.absolute_distance(T=int))
laplace_noise_main = dp.m.make_laplace(*space, scale=1.0 / main_epsilon)
main_df['Count'] = main_df['Count'].apply(lambda x: laplace_noise_main(x))
main_df.to_csv("main.csv", index=False)

# === Build and noise each 3-way side table ===
# whoops, actually made 9 of them this year using this epsilon
side_epsilon = 0.7 / 8
laplace_noise_side = dp.m.make_laplace(*space, scale=1.0 / side_epsilon)

for combo in three_combos:
    side_df = df_new.groupby(list(combo))['Count'].sum().reset_index()
    filename = 'side_' + ''.join(field[0] for field in combo) + '.csv'
    # Save real table, then overwrite Count column in-place with noisy values
    side_df.to_csv("temp_real_" + filename, index=False)
    side_df['Count'] = side_df['Count'].apply(lambda x: laplace_noise_side(x))
    side_df.to_csv("temp_dp_" + filename, index=False)
