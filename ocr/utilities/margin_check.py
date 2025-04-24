"""
margin_check.py

This script validates the row/column margin totals in EEO-1 and EEO-5 tables extracted from OCR-parsed JSON files.
It ensures the reported totals match calculated row and column sums, helping identify data extraction or OCR issues.
Significant mismatches are printed and a summary of differences is saved as JSON.

---

Key Features:
- Verifies consistency of margins in EEO-1 (single table) and EEO-5 (multiple tables: A, B, C)
- Detects mismatches between reported and calculated totals
- Flags records with significant discrepancies (e.g., differences > 10)
- Checks for valid checkbox selection in EEO-5 (exactly one of four should be selected)
"""

import json
from typing import List
import os
import glob


def get_all_json_files(path: str) -> List[str]:
    """
    Recursively collect all JSON files under the specified path.
    """
    dirs = [
        os.path.join(path, d)
        for d in os.listdir(path)
        if os.path.isdir(os.path.join(path, d))
    ]
    dirs.append(path)
    json_files = []
    for d in dirs:
        json_files.extend(glob.glob(os.path.join(d, "*.json")))
    json_files.sort()
    return json_files


def cal_eeo1_margin_diff(input_dir):
    """
    Compute and log differences between row/column totals and reported totals in EEO-1 tables.
    """
    json_files = get_all_json_files(input_dir)
    diff_cnt = dict()
    for file in json_files:
        with open(file, "r") as f:
            json_data = json.load(f)
        table = json_data.get("table")

        # Reported whole total is the bottom-right cell
        whole_total = table[-2][-1]

        # Row and column sums exclude total row/column
        row_sum = sum(row[-1] for i, row in enumerate(table) if i < len(table) - 2)
        col_sum = sum(table[-2][:-1])

        diff = 0
        if row_sum != whole_total:
            diff = abs(row_sum - whole_total)
        if col_sum != whole_total:
            diff = max(diff, abs(col_sum - whole_total))

        if diff != 0:
            diff_cnt[diff] = diff_cnt.get(diff, 0) + 1
        if diff > 10:
            print(file, diff)

    with open(os.path.join(output_dir, "margin_diff_eeo1.json"), "w") as file:
        json.dump(diff_cnt, file, indent=4)


def update_diff_cnt(diff_cnt, json_data, table_name, file):
    """
    Helper to compute and record discrepancies in margin totals for a given EEO-5 table.
    """
    table = json_data.get(table_name)
    if not table:
        return
    whole_total = table[-1][-1]
    row_sum = sum(row[-1] for i, row in enumerate(table) if i < len(table) - 1)
    col_sum = sum(table[-1][:-1])

    diff = 0
    if row_sum != whole_total:
        diff = abs(row_sum - whole_total)
    if col_sum != whole_total:
        diff = max(diff, abs(col_sum - whole_total))

    if diff != 0:
        diff_cnt.setdefault(table_name, {})
        diff_cnt[table_name][diff] = diff_cnt[table_name].get(diff, 0) + 1
    if diff > 10:
        print(file, diff)


def cal_eeo5_margin_diff(input_dir: str, output_dir: str):
    """
    Analyze EEO-5 tables for margin discrepancies and checkbox validation.
    """
    json_files = get_all_json_files(input_dir)
    diff_cnt = dict()

    for file in json_files:
        with open(file, "r") as f:
            json_data = json.load(f)

        # Check all EEO-5 tables
        update_diff_cnt(diff_cnt, json_data, "table_a", file)
        update_diff_cnt(diff_cnt, json_data, "table_b", file)
        update_diff_cnt(diff_cnt, json_data, "table_c", file)

        # Validate that only one checkbox option is selected
        is_pub = json_data.get("Local Public School", False)
        is_sp = json_data.get("Special Regional Agency", False)
        is_st = json_data.get("State Education Agency", False)
        is_other = json_data.get("Other", False)
        checkboxes = [is_pub, is_sp, is_st, is_other]
        if sum(checkboxes) != 1:
            print(file, checkboxes)

    with open(os.path.join(output_dir, "margin_diff_eeo5.json"), "w") as file:
        json.dump(diff_cnt, file, indent=4)


# Main execution
if __name__ == "__main__":
    input_dir = "/home/node1/Documents/eeo1_json"

    # Set the output directory for diff summaries (default = same as input)
    output_dir = "/home/node1/Documents/eolwd/eolwd/OCR/utils"

    cal_eeo5_margin_diff(input_dir, output_dir)
    # cal_eeo1_margin_diff(input_dir)
