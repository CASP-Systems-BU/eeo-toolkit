"""
This script applies differential privacy to pre-melted EEO-4 contingency tables.
It expects the output of eeo4_melt.py (melted_data.csv) as input and produces:
1. A noisy main table (Work Type x Salary x Government Function x Race x Gender).
2. Side tables for new hires, job category, and government type splits.
Both tables are saved as CSVs.
"""

import pandas as pd
import os

# opendp setup
import opendp.prelude as dp
dp.enable_features("contrib")

# Input path (must match eeo4_melt.py output location)
input_dir = "/home/eolwd/data/eeo4_csv"

# === Load pre-melted data ===
read_df = pd.read_csv(os.path.join(input_dir, "melted_data.csv"))

# Define fields for analysis (removing 'Government Type')
# 'Government Function'       # 16
# 'Job Category'              # 8
# 'Work Type', 'Salary Range' # 7 after grouping
# 'Race', 'Gender'            # 7 * 2
all_but_type = ['Work Type', 'Salary Range', 'Government Function', 'Job Category', 'Race', 'Gender']
true_df = read_df.groupby(all_but_type)['Count'].sum().reset_index()

# Collapse the salary ranges < $43k
true_df['Salary Range Groups'] = true_df['Salary Range'].map({
        '$0.1 - 15.9':  '$0.1 - 42.9',
        '$16.0 - 19.9': '$0.1 - 42.9',
        '$20.0 - 24.9': '$0.1 - 42.9',
        '$25.0 - 32.9': '$0.1 - 42.9',
        '$33.0 - 42.9': '$0.1 - 42.9',
        '$43.0 - 54.9': '$43.0 - 54.9',
        '$55.0 - 69.9': '$55.0 - 69.9',
        '$70.0 PLUS':   '$70.0 PLUS',
        '-':            '-'
})
true_df = true_df.groupby(['Work Type', 'Salary Range Groups', 'Government Function', 'Job Category', 'Race', 'Gender'])['Count'].sum().reset_index()

# Split into new hires vs all employees (new and otherwise)
new_df = true_df[true_df['Work Type'] == 'NEW HIRES']
all_df = true_df[true_df['Work Type'] != 'NEW HIRES']


def make_file(the_df, the_combo, the_laplace, the_filename):
    """Aggregate, apply Laplace noise, and save noisy table."""
    temp_df = the_df.groupby(list(the_combo))['Count'].sum().reset_index()
    temp_df['Count'] = temp_df['Count'].apply(lambda x: the_laplace(x))
    temp_df.to_csv(os.path.join(input_dir, the_filename + ".csv"), index=False)


# === Main table: Work Type + Salary x Government Function x Race x Gender (all employees) ===
main_epsilon = 0.7
space = (dp.atom_domain(T=int, nan=False), dp.absolute_distance(T=int))
laplace_noise_main = dp.m.make_laplace(*space, scale=1.0 / main_epsilon)

make_file(all_df, ['Work Type', 'Salary Range Groups', 'Government Function', 'Race', 'Gender'], laplace_noise_main, 'WFRG_all_hires')

# === Side tables ===
side_epsilon = 0.3
laplace_noise_side = dp.m.make_laplace(*space, scale=1.0 / side_epsilon)

# Same dimensions as main, but for new hires only
make_file(new_df, ['Work Type', 'Salary Range Groups', 'Government Function', 'Race', 'Gender'], laplace_noise_side, 'WFRG_new_hires')

# Job category x Race x Gender (all employees)
make_file(all_df, ['Job Category', 'Race', 'Gender'], laplace_noise_side, 'JRG')

# Build a Government Type breakdown (State vs Local) across all non-new-hire employees
temp_df = read_df.groupby(['Government Type', 'Work Type', 'Government Function', 'Race', 'Gender'])['Count'].sum().reset_index()

# Remove new hires
type_df = temp_df[temp_df['Work Type'] != 'NEW HIRES']

# Collapse Government Types to just state vs local governments
type_df['Gov Type'] = type_df['Government Type'].map({
        'City':     'Local',
        'County':   'Local',
        'Other':    'State',
        'State':    'State',
        'Township': 'Local'
})

# Drop Work Type and the original 5-option Government Type
type_df = type_df.groupby(['Gov Type', 'Government Function', 'Race', 'Gender'])['Count'].sum().reset_index()

# Reuse the same side epsilon for government type tables
laplace_noise_side = dp.m.make_laplace(*space, scale=1.0 / side_epsilon)

# Keep Gender but not Race
make_file(type_df, ['Gov Type', 'Government Function', 'Gender'], laplace_noise_side, 'TFG')

# Keep Race but not Gender
make_file(type_df, ['Gov Type', 'Government Function', 'Race'], laplace_noise_side, 'TFR')
