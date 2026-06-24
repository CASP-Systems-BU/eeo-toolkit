"""
This script applies differential privacy to pre-melted EEO-5 contingency tables.
It expects the output of eeo5_melt.py (melted_data.csv) as input and produces:
1. A noisy 4-way main table (Work Type × Job Category × Race × Gender).
2. Five noisy 3-way side tables pairing Type of Agent with substantive and demographic dimensions.
All tables are saved as CSVs.
"""

import os
import pandas as pd

import opendp.prelude as dp
dp.enable_features("contrib")

# Input path (must match eeo5_melt.py output location)
input_dir = "/home/node0/Documents/eeo5_json_corrected/filtered"

# === Load pre-melted data ===
read_df = pd.read_csv(os.path.join(input_dir, "melted_data.csv"))


def make_file(the_df, the_combo, the_laplace, the_filename):
    """Aggregate, apply Laplace noise, and save noisy table."""
    temp_df = the_df.groupby(list(the_combo))['Count'].sum().reset_index()
    temp_df['Count'] = temp_df['Count'].apply(lambda x: the_laplace(int(x)))
    temp_df.to_csv(os.path.join(input_dir, the_filename + ".csv"), index=False)


# === Main table: Work Type × Job Category × Race × Gender ===

main_epsilon = 0.7
space = (dp.atom_domain(T=int, nan=False), dp.absolute_distance(T=int))
laplace_noise_main = dp.m.make_laplace(*space, scale=1.0 / main_epsilon)

make_file(read_df, ['Work Type', 'Job Category', 'Race', 'Gender'], laplace_noise_main, 'WCRG')

# === Side tables ===
side_epsilon = 0.3
laplace_noise_side = dp.m.make_laplace(*space, scale=1.0 / side_epsilon)

# Job category × Race × Gender
make_file(read_df, ['Job Category', 'Race', 'Gender'], laplace_noise_side, 'JRG')

# Type of Agent crossed with Work Type
make_file(read_df, ['Type of Agent', 'Work Type', 'Race'],   laplace_noise_side, 'TWR')
make_file(read_df, ['Type of Agent', 'Work Type', 'Gender'], laplace_noise_side, 'TWG')

# Type of Agent crossed with Job Category
make_file(read_df, ['Type of Agent', 'Job Category', 'Race'],   laplace_noise_side, 'TJR')
make_file(read_df, ['Type of Agent', 'Job Category', 'Gender'], laplace_noise_side, 'TJG')
