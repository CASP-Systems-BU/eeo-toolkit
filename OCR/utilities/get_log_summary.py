import os
import re
from typing import List

from dir_helper import get_files_in_directory


def get_filename(path: str) -> str:
    filename_with_ext = os.path.basename(path)
    filename, _ = os.path.splitext(filename_with_ext)
    return filename


def get_invalid_table_message(path: str, line: str) -> str:
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
    pattern = r"val:(\d+),conf:([\d\.]+),loc:\[([^\]]+)\]"

    filename = get_filename(path)
    msg = f"UNCONFIDENT_CELL-{filename}:"

    match = re.search(pattern, line)
    if match:
        val = int(match.group(1))  # Convert captured string to int
        conf = float(match.group(2))  # Convert captured string to float

        loc_str = match.group(3)
        loc = [int(s.strip()) for s in loc_str.split(",")]
        msg += f"val:{val},conf:{conf},loc:{loc}\n"
    else:
        msg += "WARNING-info not found\n"
    return msg


def write_to_log(path: str, message: str) -> None:
    with open(path, "a") as f:
        f.write(message)


def examine_single_log(path: str, out_log: str) -> bool:
    isValidTable = False
    with open(path, "r") as f:
        lines = f.readlines()
        for line in lines:
            line_ls = line.split(",")
            line_set = set(line_ls)
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
    summary_log_filename = f"{out_path}"

    valid_table_cnt = 0
    invalid_table_cnt = 0
    for _, log in enumerate(logs):
        log_path = f"{log_dir}/{log}"
        isValidTable = examine_single_log(log_path, summary_log_filename)
        if isValidTable:
            valid_table_cnt += 1
        else:
            invalid_table_cnt += 1

    with open(summary_log_filename, "a") as f:
        f.write(f"Total Logs: {len(logs)}\n")
        f.write(
            f"Summary: {valid_table_cnt} valid tables, {invalid_table_cnt} invalid tables\n"
        )
        f.write(
            f"Summary: accuracy: {valid_table_cnt / (valid_table_cnt + invalid_table_cnt) * 100}%\n"
        )


if __name__ == "__main__":
    log_dir = "../../logs"
    logs = get_files_in_directory(log_dir, "log")
    logs.sort()
    summary_log_path = "../../summary.log"
    process_logs(logs, log_dir, summary_log_path)
