"""
This script reads all CSV files from a specified folder and writes them into a single Excel file,
with each CSV stored as a separate sheet. It ensures that each sheet name is unique and does not
exceed Excel's 31-character limit. This is especially useful when consolidating a large number
of structured data files (e.g., contingency tables) into one workbook for easy review or sharing.
"""

import pandas as pd
import os

# Define the directory containing CSV files and the output Excel filename
csv_folder = '/Users/rekkles/Downloads/eeo5_contingency_tables_dp'
output_excel = 'combined_output_eeo5.xlsx'

# Track sheet names used to ensure uniqueness and respect Excel's 31-character limit
used_sheet_names = set()

def get_unique_sheet_name(base_name):
    """
    Generate a unique Excel sheet name from the given base name.
    Truncate to 31 characters (Excel limit) and append a numeric suffix if needed to avoid duplicates.
    """
    base = base_name[:31]
    name = base
    i = 1
    while name in used_sheet_names:
        suffix = f"_{i}"
        name = (base[:31 - len(suffix)] + suffix) if len(base) + len(suffix) > 31 else base + suffix
        i += 1
    used_sheet_names.add(name)
    return name

# Create a single Excel file with each CSV as a separate sheet
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith('.csv'):
            # Read the CSV file into a DataFrame
            df = pd.read_csv(os.path.join(csv_folder, csv_file))
            # Get base name (without .csv extension) and compute a valid, unique sheet name
            base_name = os.path.splitext(csv_file)[0]
            sheet_name = get_unique_sheet_name(base_name)
            # Write DataFrame to the Excel sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Excel file created with all unique sheet names.")
