import pandas as pd
import os

csv_folder = '/Users/rekkles/Downloads/eeo5_contingency_tables_dp'
output_excel = 'combined_output_eeo5.xlsx'

used_sheet_names = set()

def get_unique_sheet_name(base_name):
    base = base_name[:31]
    name = base
    i = 1
    while name in used_sheet_names:
        suffix = f"_{i}"
        name = (base[:31 - len(suffix)] + suffix) if len(base) + len(suffix) > 31 else base + suffix
        i += 1
    used_sheet_names.add(name)
    return name

with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith('.csv'):
            df = pd.read_csv(os.path.join(csv_folder, csv_file))
            base_name = os.path.splitext(csv_file)[0]
            sheet_name = get_unique_sheet_name(base_name)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Excel file created with all unique sheet names.")
