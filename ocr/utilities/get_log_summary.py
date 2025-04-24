"""
get_log_summary.py

This script parses and summarizes log files generated from OCR postprocessing or table validation runs.
It extracts error messages related to invalid tables and low-confidence cells, formats them for readability,
and computes an overall accuracy rate.

---

Key Features:
- Scans all `.log` files in a specified directory
- Identifies and categorizes:
  - Invalid table structures
  - Low-confidence OCR cells
- Outputs formatted error summaries to a single summary file
- Reports total counts and percentage of valid vs. invalid tables
"""

import os
import re
from typing import List
from dir_helper import get_files_in_directory


def get_filename(path: str) -> str:
    """
    Extracts the filename (without extension) from a full path.
    """
    filename_with_ext = os.path.basename(path)
    filename, _ = os.path.splitext(filename_with_ext)
    return filename


def get_invalid_table_message(path: str, line: str) -> str:
    """
    Parse and format invalid table message from a log line.
    """
    pattern = r"row-\[([^\]]+)\],col-\[([^\]]+)\]"
    filename = get_filename(path)
    msg = "ERROR_IN_TABLE-"
    match = re.search(pattern, line)
    if match:
        row_str = match.group(1)
        col_str = match.group(2)
        row_list = [s.strip() == "True" for s in row_str.split(",")]
        col_list = [s.strip() == "True" for s in col_str.split(",")]
        msg += f"{filename}:row-{row_list},col-{col_list}\n"
    else:
        msg += f"{filename}:WARNING-info not found\n"
    return msg


def get_unconfident_cell_message(path: str, line: str) -> str:
    """
    Parse and format message for an OCR cell with low confidence.
    """
    pattern = r"val:(\d+),conf:([\d\.]+),loc:\[([^\]]+)\]"
    filename = get_filename(path)
    msg = f"UNCONFIDENT_CELL-{filename}:"
    match = re.search(pattern, line)
    if match:
        val = int(match.group(1))
        conf = float(match.group(2))
        loc_str = match.group(3)
        loc = [int(s.strip()) for s in loc_str.split(",")]
        msg += f"val:{val},conf:{conf},loc:{loc}\n"
    else:
        msg += "WARNING-info not found\n"
    return msg


def write_to_log(path: str, message: str) -> None:
    """
    Append a formatted message to a log file.
    """
    with open(path, "a") as f:
        f.write(message)


def examine_single_log(path: str, out_log: str) -> bool:
    """
    Process a single log file to extract table validity and error messages.

    Returns:
        bool: True if the table is marked valid, False otherwise.
    """
    isValidTable = False
    with open(path, "r") as f:
        lines = f.readlines()
        for line in lines:
            if "Valid table" in line:
                isValidTable = True
            elif "Invalid table" in line:
                msg = get_invalid_table_message(path, line)
                write_to_log(out_log, msg)
            elif "Unconfident_cell" in line:
                msg = get_unconfident_cell_message(path, line)
                write_to_log(out_log, msg)
    return isValidTable


def process_logs(logs: List[str], log_dir: str, out_path: str) -> None:
    """
    Process all logs in a directory and summarize validation results.

    Args:
        logs (List[str]): List of log filenames.
        log_dir (str): Path to the log directory.
        out_path (str): Path to write the summary log file.
    """
    valid_table_cnt = 0
    invalid_table_cnt = 0

    for log in logs:
        log_path = os.path.join(log_dir, log)
        isValidTable = examine_single_log(log_path, out_path)
        if isValidTable:
            valid_table_cnt += 1
        else:
            invalid_table_cnt += 1

    with open(out_path, "a") as f:
        f.write(f"Total Logs: {len(logs)}\n")
        f.write(f"Summary: {valid_table_cnt} valid tables, {invalid_table_cnt} invalid tables\n")
        if valid_table_cnt + invalid_table_cnt > 0:
            accuracy = valid_table_cnt / (valid_table_cnt + invalid_table_cnt) * 100
            f.write(f"Summary: accuracy: {accuracy:.2f}%\n")


# Example usage
if __name__ == "__main__":
    log_dir = "../../logs"
    logs = get_files_in_directory(log_dir, "log")
    logs.sort()
    summary_log_path = "../../summary.log"
    process_logs(logs, log_dir, summary_log_path)
