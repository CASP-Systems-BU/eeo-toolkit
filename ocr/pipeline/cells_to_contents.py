"""
Module: cells_to_contents.py

Processes OCR-extracted cell images to extract text and table data,
validates and post-processes numerical tables, merges EEO-5 sections,
and outputs consolidated JSON results.
"""

import gc
import os
import re
import json
import shutil
from typing import Dict, List, Tuple, Union

from doctr.io import DocumentFile

from utilities.dir_helper import create_dir_if_not_exists
from logger.logger import Logger
from utilities.table_validator import table_validator, update_total
from pipeline.checkboxes import extract_from_checkbox
from utilities.dir_helper import get_files_in_directory

CONFIDENCE_THRESHOLD = 0.8  # Minimum confidence to accept an OCR digit
EEO5_TABLE_SECTION_SET = {"a1", "a2", "a3", "b", "c"}  # Valid sections for EEO-5 tables

# Initialize a default logger; will be reconfigured per file
file_logger = Logger(
    log_file_path="output.log",
    prefix="CELL_TO_CONTENTS",
)


def get_current_processing_files(out_dir: str) -> List[str]:
    """
    List PDF files in the temporary output directory to process.

    :param out_dir: Directory containing split cell PDF pages
    :return: List of filenames to process
    """
    temp_files = get_files_in_directory(out_dir)
    if not temp_files:
        file_logger.error("No PDF files found in the output directory")
    return temp_files


def post_process_table(
    digit_table: List[List[Union[int, str]]], confidence_table: List[List[float]]
) -> None:
    """
    Validate and clean up a numerical table:
    - Replace missing or invalid entries with zero
    - Warn on low-confidence OCR digits

    :param digit_table: 2D array of raw digit strings or -1 for empty
    :param confidence_table: Parallel 2D array of confidences
    """
    for i in range(len(confidence_table)):
        for j in range(len(confidence_table[i])):
            val = digit_table[i][j]
            conf = confidence_table[i][j]

            # Empty cell
            if val == -1:
                file_logger.warning(f"Empty_cell,loc:[{j}, {i}]")
                digit_table[i][j] = 0
            # Non-digit content
            elif not isinstance(val, str) or not val.isdigit():
                file_logger.warning(f"Invalid_digit,val:{val},loc:[{j}, {i}]")
                digit_table[i][j] = 0
            # Low-confidence but digit
            elif conf < CONFIDENCE_THRESHOLD:
                file_logger.warning(
                    f"Unconfident_cell,val:{val},conf:{conf:.2f},loc:[{j}, {i}]"
                )
            # Convert valid digit string to int
            digit_table[i][j] = int(digit_table[i][j])


def parse_doctr_json_output(data: dict) -> Tuple[List[str], List[float]]:
    """
    Flatten doctr JSON output to lists of text lines and confidences.

    :param data: Raw JSON from doctr predictor
    :return: (list of text lines, list of average confidences)
    """
    str_lines: List[str] = []
    confidence_lines: List[float] = []
    for page in data.get("pages", []):
        for block in page.get("blocks", []):
            for line in block.get("lines", []):
                words = [w["value"] for w in line.get("words", [])]
                confs = [w["confidence"] for w in line.get("words", [])]
                if not words:
                    continue
                # Join words into a single line
                line_text = " ".join(words)
                avg_conf = sum(confs) / len(confs)
                str_lines.append(line_text)
                confidence_lines.append(avg_conf)
    return str_lines, confidence_lines


def calculate_midpoint(
    topright: List[float],
    bottomleft: List[float],
    total_width: float,
    total_height: float,
) -> Tuple[float, float]:
    """
    Compute the midpoint of a word's bounding box, scaled to PDF dimensions.

    :param topright: [x, y] of top-right corner (normalized)
    :param bottomleft: [x, y] of bottom-left corner (normalized)
    :param total_width: PDF page width in pixels
    :param total_height: PDF page height in pixels
    :return: (mid_x, mid_y) in pixel coordinates
    """
    if len(topright) != 2 or len(bottomleft) != 2:
        raise ValueError("topright and bottomleft must be of length 2")

    mid_x = (topright[0] + bottomleft[0]) * total_width / 2
    mid_y = (topright[1] + bottomleft[1]) * total_height / 2
    return mid_x, mid_y


def init_data_table_and_conf_table(
    table_config: Dict,
) -> Tuple[List[List[int]], List[List[float]]]:
    """
    Initialize empty digit and confidence tables based on config shape.

    :param table_config: (rows, cols) for the table
    :return: (digit_table, confidence_table)
    """
    rows, cols = get_table_row_and_col_num(table_config)
    digit_table = [[-1] * cols for _ in range(rows)]
    confidence_table = [[-1.0] * cols for _ in range(rows)]
    return digit_table, confidence_table


def get_table_row_and_col_num(table_config: Dict) -> Tuple[int, int]:
    """
    Extract the number of rows and columns defined in the table configuration.

    :param table_config: Sequence where
        - index 0 is the number of rows
        - index 1 is the number of columns
    :return: A tuple containing
        - row count (int)
        - column count (int)
    """
    return table_config[0], table_config[1]


def parse_doctr_json_output_table(
    form_type: str,
    data,
    table_config: Dict,
    sect: Union[str, None] = None,
    padding: int = 45,
) -> Tuple[List[str], List[float]]:
    """
    Parse paginated doctr output into a structured numeric table.
    Supports EEO-1 (full-page table) and EEO-5 (section-specific tables).

    :param form_type: 'eeo1' or 'eeo5'
    :param data: Raw doctr JSON
    :param table_config: Config for table dimensions
    :param sect: For eeo5, section key ('a1','b', etc.)
    :param padding: Margin in pixels before table grid
    :return: (digit_table, confidence_table)
    """
    # Initialize default
    digit_table = [[-1]]
    confidence_table = [[-1]]

    if form_type == "eeo1":
        row_num, col_num = get_table_row_and_col_num(table_config)
        digit_table, confidence_table = init_data_table_and_conf_table(table_config)
        for page in data.get("pages", []):
            page_dimensions = page.get("dimensions")
            # Scale down by 2: `read_pdf` from docTR scales up by 2 by default
            total_height, total_width = page_dimensions[0] / 2, page_dimensions[1] / 2

            avg_cell_width = (total_width - 2 * padding) / col_num

            for block in page.get("blocks", {}):
                for line in block.get("lines", {}):
                    for raw_word in line.get("words", {}):
                        mid_x, mid_y = calculate_midpoint(
                            raw_word["geometry"][0],
                            raw_word["geometry"][1],
                            total_width,
                            total_height,
                        )

                        val, conf = raw_word["value"], raw_word["confidence"]

                        x_relative = int((mid_x - padding) // avg_cell_width)
                        y_relative = int((mid_y - padding) // 25)  # 25px is the fixed row height for EEO-1; EEO-5/4 compute this dynamically
                        if y_relative >= row_num:
                            y_relative = row_num - 1

                        if not val.isdigit():
                            file_logger.warning(
                                f"Invalid_digit,val:{val},loc:[{x_relative}, {y_relative}]"
                            )

                        # Keep the first valid digit seen; prefer any digit over a non-digit placeholder (-1)
                        if (
                            digit_table[y_relative][x_relative] == -1
                            or not digit_table[y_relative][x_relative].isdigit()
                        ):
                            digit_table[y_relative][x_relative] = val
                            confidence_table[y_relative][x_relative] = conf
    elif form_type == "eeo5":
        if sect is None or sect not in EEO5_TABLE_SECTION_SET:
            file_logger.error(f"sect invalid: {sect}")
        else:
            row_num, col_num = get_table_row_and_col_num(table_config[sect])
            digit_table, confidence_table = init_data_table_and_conf_table(
                table_config[sect]
            )
            for page in data.get("pages", []):
                page_dimensions = page.get("dimensions")
                # Scale down by 2: `read_pdf` from docTR scales up by 2 by default
                total_height, total_width = (
                    page_dimensions[0] / 2,
                    page_dimensions[1] / 2,
                )

                avg_cell_height = (total_height - 2 * padding) / row_num
                avg_cell_width = (total_width - 2 * padding) / col_num

                for block in page.get("blocks", {}):
                    for line in block.get("lines", {}):
                        for raw_word in line.get("words", {}):
                            mid_x, mid_y = calculate_midpoint(
                                raw_word["geometry"][0],
                                raw_word["geometry"][1],
                                total_width,
                                total_height,
                            )

                            val, conf = raw_word["value"], raw_word["confidence"]

                            x_relative = int((mid_x - padding) // avg_cell_width)
                            y_relative = int((mid_y - padding) // avg_cell_height)
                            if y_relative >= row_num:
                                y_relative = row_num - 1

                            if not val.isdigit():
                                file_logger.warning(
                                    f"Invalid_digit,val:{val},loc:[{x_relative}, {y_relative}]"
                                )

                            if (
                                digit_table[y_relative][x_relative] == -1
                                or not digit_table[y_relative][x_relative].isdigit()
                            ):
                                digit_table[y_relative][x_relative] = val
                                confidence_table[y_relative][x_relative] = conf
    elif form_type in ("eeo4_type1", "eeo4_type2"):
        if sect is None or sect not in table_config:
            file_logger.error(f"sect invalid: {sect}")
        else:
            row_num, col_num = get_table_row_and_col_num(table_config[sect])
            digit_table, confidence_table = init_data_table_and_conf_table(
                table_config[sect]
            )
            for page in data.get("pages", []):
                page_dimensions = page.get("dimensions")
                # Scale down by 2: `read_pdf` from docTR scales up by 2 by default
                total_height, total_width = (
                    page_dimensions[0] / 2,
                    page_dimensions[1] / 2,
                )

                avg_cell_height = (total_height - 2 * padding) / row_num
                avg_cell_width = (total_width - 2 * padding) / col_num

                for block in page.get("blocks", {}):
                    for line in block.get("lines", {}):
                        for raw_word in line.get("words", {}):
                            val, conf = raw_word["value"], raw_word["confidence"]
                            if row_num == 1 and col_num == 1:
                                x_relative, y_relative = 0, 0
                            else:
                                mid_x, mid_y = calculate_midpoint(
                                    raw_word["geometry"][0],
                                    raw_word["geometry"][1],
                                    total_width,
                                    total_height,
                                )
                                x_relative = int((mid_x - padding) // avg_cell_width)
                                y_relative = int((mid_y - padding) // avg_cell_height)
                                if y_relative >= row_num:
                                    y_relative = row_num - 1

                            if not val.isdigit():
                                file_logger.warning(
                                    f"Invalid_digit,val:{val},loc:[{x_relative}, {y_relative}]"
                                )

                            if (
                                digit_table[y_relative][x_relative] == -1
                                or not digit_table[y_relative][x_relative].isdigit()
                            ):
                                digit_table[y_relative][x_relative] = val
                                confidence_table[y_relative][x_relative] = conf

    if form_type == "eeo1":
        post_process_table(digit_table, confidence_table)
        is_row_valid, is_col_valid = table_validator(
            form_type, digit_table, confidence_table
        )
        if all(is_col_valid) and all(is_row_valid):
            file_logger.info("Valid table")
        elif (
            all(is_row_valid)
            and all(is_col_valid[:-1])
            and not is_col_valid[-1]
            and update_total(digit_table)
        ):
            file_logger.info("Valid table, invalid sum")
        else:
            file_logger.warning(f"Invalid table:row-{is_row_valid},col-{is_col_valid}")

    return (digit_table, confidence_table)


def is_eeo4_table_cell(filename: str) -> Tuple[bool, str]:
    """
    Identify whether a cell filename corresponds to an EEO-4 table section.

    :param filename: Name of the cell PDF file
    :return: Tuple where
        - first element is True if it matches a table section pattern, False otherwise
        - second element is the section identifier or empty string
    """
    m = re.match(r".+_section_table\d*_(.+)$", filename)
    return (bool(m), m.group(1) if m else "")


def is_eeo5_table_cell(filename: str) -> Tuple[bool, str]:
    """
    Identify whether a cell filename corresponds to an EEO-5 table section.

    :param filename: Name of the cell PDF file
    :return: Tuple where
        - first element is True if it matches a table section pattern, False otherwise
        - second element is the section identifier ('a1', 'a2', 'a3', 'b', 'c') or empty string
    """
    m = re.match(r".+_section_table_(a1|a2|a3|b|c)$", filename)
    return (bool(m), m.group(1) if m else "")


def merge_eeo5_table_a(table_raw: Dict) -> Tuple[List, List]:
    """
    Merge subtables A1, A2, and A3 for section A of EEO-5 into a single table.

    :param table_raw: Mapping of raw table data for keys 'a1', 'a2', 'a3'
    :return: A tuple containing
        - combined data rows (list)
        - combined confidence scores (list)
    """
    data = table_raw["a1"][0] + table_raw["a2"][0] + table_raw["a3"][0]
    conf = table_raw["a1"][1] + table_raw["a2"][1] + table_raw["a3"][1]
    return data, conf


def merge_eeo5_table(table_raw: Dict) -> Dict:
    """
    Combine all raw tables for EEO-5 into a single consolidated mapping.

    :param table_raw: Mapping of raw table data for keys 'a1', 'a2', 'a3', 'b', 'c'
    :return: Dictionary with keys
        - 'a': merged A section (data & confidence)
        - 'b': raw B section or ([], []) if missing
        - 'c': raw C section or ([], []) if missing
    """
    combined = {
        "a": merge_eeo5_table_a(table_raw),
        "b": table_raw.get("b", ([], [])),
        "c": table_raw.get("c", ([], [])),
    }
    return combined


def merge_eeo4_table_vertical(table_raw: Dict, section_keys: List[str]) -> Tuple[List, List]:
    """
    Vertically concatenate multiple table sections into a single column.

    :param table_raw: Dictionary containing raw table data
    :param section_keys: List of section keys to merge (e.g., ['a1', 'a5', 'atotal1'])
    :return: Tuple of (merged_data, merged_confidence)
    """
    merged_data = []
    merged_conf = []

    for key in section_keys:
        data, conf = table_raw.get(key, ([], []))
        merged_data += data
        merged_conf += conf

    return merged_data, merged_conf


def merge_eeo4_table_horizontal(columns: List[Tuple[List, List]]) -> Tuple[List, List]:
    """
    Horizontally merge multiple columns/column groups into a single wide table.

    :param columns: List of (data, confidence) tuples to merge horizontally
    :return: Tuple of (final_data, final_confidence) as a single wide table
    """
    # Verify all columns have the same number of rows; truncate to minimum
    num_rows = len(columns[0][0])
    for idx, (data, _) in enumerate(columns):
        if len(data) != num_rows:
            file_logger.warning(
                f"Row count mismatch: column 0 has {num_rows} rows, "
                f"column {idx} has {len(data)} rows — truncating to minimum"
            )
    num_rows = min(len(data) for data, _ in columns)

    final_data = []
    final_conf = []

    for i in range(num_rows):
        row_data = []
        row_conf = []

        for data, conf in columns:
            if i < len(data):
                # Ensure data is a list for concatenation
                cell_data = data[i] if isinstance(data[i], list) else [data[i]]
                cell_conf = conf[i] if isinstance(conf[i], list) else [conf[i]]
                row_data.extend(cell_data)
                row_conf.extend(cell_conf)

        final_data.append(row_data)
        final_conf.append(row_conf)

    return final_data, final_conf


def merge_eeo4_type2_table(table_raw: Dict) -> Dict:
    """
    Combine all raw tables for EEO-4 munis into the same consolidated format as eeo4.

    Each block (a1..a5, a6..a8+atotal, b, btotal, c, ctotal) is stored as four columns:
    *_hisp (2 cols), *_male (6 cols), *_female (6 cols), *_total (1 col) = 15 cols per row.

    :param table_raw: Mapping of raw table data keyed by field name
    :return: Dictionary with keys 'a', 'b', 'c' matching the eeo4 merge output format
    """
    def merge_block(prefix):
        """Horizontally merge the four column-groups for a given row-block prefix."""
        return merge_eeo4_table_horizontal([
            table_raw.get(f"{prefix}_hisp",   ([], [])),
            table_raw.get(f"{prefix}_male",   ([], [])),
            table_raw.get(f"{prefix}_female", ([], [])),
            table_raw.get(f"{prefix}_total",  ([], [])),
        ])

    # Full-time table A: rows 1-40 (a1..a5) then rows 41-64 (a6..a8) + row 65 (atotal)
    a_blocks = [merge_block(f"a{i}") for i in range(1, 6)]   # rows 1-40
    a_blocks += [merge_block(f"a{i}") for i in range(6, 9)]  # rows 41-64
    a_blocks.append(merge_block("atotal"))                    # row 65

    final_a_data: List = []
    final_a_conf: List = []
    for data, conf in a_blocks:
        final_a_data.extend(data)
        final_a_conf.extend(conf)

    # Part-time table B: rows 66-73 (b) + row 74 (btotal)
    final_b_data, final_b_conf = merge_eeo4_table_vertical(
        {k: v for k, v in [("b", merge_block("b")), ("btotal", merge_block("btotal"))]},
        ["b", "btotal"],
    )

    # New hire table C: rows 75-82 (c) + row 83 (ctotal)
    final_c_data, final_c_conf = merge_eeo4_table_vertical(
        {k: v for k, v in [("c", merge_block("c")), ("ctotal", merge_block("ctotal"))]},
        ["c", "ctotal"],
    )

    return {
        "a": (final_a_data, final_a_conf),
        "b": (final_b_data, final_b_conf),
        "c": (final_c_data, final_c_conf),
    }


def merge_eeo4_table(table_raw: Dict) -> Dict:
    """
    Combine all raw tables for EEO-4 into a single consolidated mapping.

    :param table_raw: Mapping of raw table data for all table sections
    :return: Dictionary with key 'a' containing the fully merged table
    """
    # Full Time Employee Table
    merged_a1 = merge_eeo4_table_vertical(table_raw, ["a1", "a5", "atotal1"])
    merged_a2 = merge_eeo4_table_vertical(table_raw, ["a2", "a6", "atotal2"])
    merged_a3 = merge_eeo4_table_vertical(table_raw, ["a3", "a7", "atotal3"])
    merged_a4 = merge_eeo4_table_vertical(table_raw, ["a4", "a8", "atotal4"])

    final_a_data, final_a_conf = merge_eeo4_table_horizontal(
        [merged_a1, merged_a2, merged_a3, merged_a4]
    )

    # Other Than Full Time Employee Table
    merged_bhistm = merge_eeo4_table_vertical(table_raw, ["bhistm_1", "bhistm_2", "bhistm_3", "bhistm_4", "bhistm_5", "bhistm_total"])
    merged_bhistf = merge_eeo4_table_vertical(table_raw, ["bhistf_1", "bhistf_2", "bhistf_3", "bhistf_4", "bhistf_5", "bhistf_total"])
    merged_brest = merge_eeo4_table_vertical(table_raw, ["brest_1", "brest_2", "brest_3", "brest_4", "brest_5", "brest_total"])
    merged_btotal = merge_eeo4_table_vertical(table_raw, ["btotal_1", "btotal_2", "btotal_3", "btotal_4", "btotal_5", "btotal_total"])

    final_b_data, final_b_conf = merge_eeo4_table_horizontal(
        [merged_bhistm, merged_bhistf, merged_brest, merged_btotal]
    )


    # New Hires Table
    merged_chistm = merge_eeo4_table_vertical(table_raw, ["chistm_1", "chistm_2", "chistm_3", "chistm_4", "chistm_5", "chistm_total"])
    merged_chistf = merge_eeo4_table_vertical(table_raw, ["chistf_1", "chistf_2", "chistf_3", "chistf_4", "chistf_5", "chistf_total"])
    merged_crest = merge_eeo4_table_vertical(table_raw, ["crest_1", "crest_2", "crest_3", "crest_4", "crest_5", "crest_total"])
    merged_ctotal = merge_eeo4_table_vertical(table_raw, ["ctotal_1", "ctotal_2", "ctotal_3", "ctotal_4", "ctotal_5", "ctotal_total"])

    final_c_data, final_c_conf = merge_eeo4_table_horizontal(
        [merged_chistm, merged_chistf, merged_crest, merged_ctotal]
    )

    return {"a": (final_a_data, final_a_conf),
            "b": (final_b_data, final_b_conf),
            "c": (final_c_data, final_c_conf)}

def extract_contents(
    form_type: str,
    pdf_tmp_path: str,
    cell_dir: str,
    checkbox_config: str,
    result_dir: str,
    predictor,
    table_config: Dict,
    log_dir: str = "../logs"
) -> None:
    """
    Main pipeline to:
      1. Iterate over cell PDFs
      2. Run OCR predictor
      3. Parse text or table output
      4. Validate and merge tables
      5. Extract checkbox data
      6. Save consolidated JSON results

    :param form_type: 'eeo1' or 'eeo5'
    :param pdf_tmp_path: Temp PDF pages directory
    :param cell_dir: Directory of individual cell PDFs
    :param checkbox_config: Path to checkbox schema YAML
    :param result_dir: Output JSON directory
    :param predictor: Doctr OCR predictor instance
    :param table_config: Table schema mapping
    :param log_dir: Log directory path
    """

    # Prepare logging per file
    global file_logger
    create_dir_if_not_exists(log_dir)

    # Gather cell files to process
    files = get_current_processing_files(cell_dir)
    if len(files) == 0:
        return

    # Determine base filename for logs and JSON
    sect_filename = os.path.splitext(os.path.basename(files[0]))[0]
    filename = sect_filename.split("_section_")[0]

    file_logger = Logger(
        log_file_path=f"{log_dir}/{filename}.log",
        prefix="CELL_TO_CONTENTS",
    )
    cells = sorted(get_files_in_directory(cell_dir), key=lambda x: x)

    file_logger.info(f"********** Processing File {filename} **********")

    # PHASE 2-1: Detect text in cells
    contents_raw = dict()
    table_raw = dict()
    for cell in cells:
        cellname = os.path.splitext(cell)[0]

        # skip Section E and F: docTR cannot detect cross mark
        if cellname.endswith("ef_SECTION_E_AND_F"):
            continue
        if cellname.endswith("section_a_TYPE_OF_AGENCY"):
            continue
        cell_file = f"{cell_dir}/{cell}"
        file_logger.info(f"Processing cell {cell_file}...")

        doc = DocumentFile.from_pdf(cell_file)
        gc.collect()
        result = predictor(doc)  # raw json output from docTR
        del doc
        gc.collect()
        raw_result = result.export()
        if form_type == "eeo1":
            if cellname.endswith("h_TABLE"):
                (str_lines, confidence_lines) = parse_doctr_json_output_table(
                    form_type, raw_result, table_config
                )
            else:
                (str_lines, confidence_lines) = parse_doctr_json_output(raw_result)
            contents_raw[cellname] = (str_lines, confidence_lines)
        elif form_type in ("eeo4_type1", "eeo4_type2"):
            ok, sect = is_eeo4_table_cell(cellname)
            if ok:
                (str_lines, confidence_lines) = parse_doctr_json_output_table(
                    form_type, raw_result, table_config, sect
                )
                table_raw[sect] = (str_lines, confidence_lines)
            else:
                (str_lines, confidence_lines) = parse_doctr_json_output(raw_result)
                contents_raw[cellname] = (str_lines, confidence_lines)
        elif form_type == "eeo5":
            ok, sect = is_eeo5_table_cell(cellname)
            if ok:
                (str_lines, confidence_lines) = parse_doctr_json_output_table(
                    form_type, raw_result, table_config, sect
                )
                table_raw[sect] = (str_lines, confidence_lines)
            else:
                (str_lines, confidence_lines) = parse_doctr_json_output(raw_result)
                contents_raw[cellname] = (str_lines, confidence_lines)

    # Merge and post-process EEO-5 tables if present
    if form_type == "eeo5":
        tables = merge_eeo5_table(table_raw)
        for k in tables.keys():
            data_table, conf_table = tables[k][0], tables[k][1]

            post_process_table(data_table, conf_table)
            is_row_valid, is_col_valid = table_validator(
                form_type, data_table, conf_table
            )
            if all(is_col_valid) and all(is_row_valid):
                file_logger.info("Valid table")
            elif (
                all(is_row_valid)
                and all(is_col_valid[:-1])
                and not is_col_valid[-1]
                and update_total(data_table)
            ):
                file_logger.info("Valid table, invalid sum")
            else:
                file_logger.warning(
                    f"Invalid table:row-{is_row_valid},col-{is_col_valid}"
                )

            contents_raw[f"the_section_table_{k.upper()}"] = data_table, conf_table

    # Merge and post-process EEO-4 tables if present
    if form_type == "eeo4_type1":
        tables = merge_eeo4_table(table_raw)
        for k in tables.keys():
            data_table, conf_table = tables[k][0], tables[k][1]
            post_process_table(data_table, conf_table)
            contents_raw[f"the_section_table_{k.upper()}"] = data_table, conf_table

    if form_type == "eeo4_type2":
        tables = merge_eeo4_type2_table(table_raw)
        for k in tables.keys():
            data_table, conf_table = tables[k][0], tables[k][1]
            post_process_table(data_table, conf_table)
            if data_table and data_table[-1][-1] == 0:
                data_table[-1][-1] = sum(data_table[-1][:-1])
            contents_raw[f"the_section_table_{k.upper()}"] = data_table, conf_table

    # PHASE 2-2: TXT to JSON
    # Build final JSON structure
    json_data = []
    pattern = re.compile(r".*_section_([a-z]+)_([a-zA-Z0-9_]+)", re.IGNORECASE)
    for section_key in contents_raw.keys():
        match = pattern.match(section_key)
        if match:
            section, field = match.groups()
            content = contents_raw[section_key]
            json_data.append(
                {
                    "id": f"{section}-{field}",
                    "section": section,
                    "content": content[0],
                    "confidence": content[1],
                }
            )
    json_data = sorted(json_data, key=lambda x: x["id"])

    create_dir_if_not_exists(result_dir)

    output_json_path = f"{result_dir}/{filename}_result.json"
    file_logger.info(f"Saving JSON result to {output_json_path}")
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)

    # Extract checkboxes and clean up
    if form_type == "eeo1":
        file_logger.info(f"Processing cell {result_dir}/{filename}_section_ef...")
    elif form_type == "eeo5":
        file_logger.info(f"Processing cell {result_dir}/{filename}_section_a...")
    extract_from_checkbox(
        form_type, pdf_tmp_path, result_dir, filename + ".pdf", checkbox_config
    )
    shutil.rmtree(cell_dir)
    os.makedirs(cell_dir, exist_ok=True)
