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
from typing import Dict

from typing import List, Tuple, Union

from doctr.io import DocumentFile

from OCR.utilities.dir_helper import create_dir_if_not_exists
from OCR.logger.logger import Logger
from OCR.utilities.table_validator import table_validator, update_total
from OCR.pipeline.checkboxes import extract_from_checkbox, debug_checkbox
from OCR.utilities.dir_helper import get_files_in_directory

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
    Extract number of rows and columns from table config.
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
            # !! REQUIERED to scale down by 2: `read_pdf` from docTR scales up by 2 by default
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
                        y_relative = int((mid_y - padding) // 25)
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
                # !!! REQUIERED to scale down by 2: `read_pdf` from docTR scales up by 2 by default
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


def is_eeo5_table_cell(filename: str) -> Tuple[bool, str]:
    """
    Identify if a cell filename corresponds to an EEO-5 table section.
    """
    m = re.match(r".+_section_table_(a1|a2|a3|b|c)$", filename)
    return (bool(m), m.group(1) if m else "")


def merge_eeo5_table_a(table_raw: Dict) -> Tuple[List, List]:
    """
    Merge A1, A2, A3 subtables for section A of EEO-5.
    """
    data = table_raw["a1"][0] + table_raw["a2"][0] + table_raw["a3"][0]
    conf = table_raw["a1"][1] + table_raw["a2"][1] + table_raw["a3"][1]
    return data, conf


def merge_eeo5_table(table_raw: Dict) -> Dict:
    """
    Combine raw tables for EEO-5 into a single mapping.
    """
    combined = {
        "a": merge_eeo5_table_a(table_raw),
        "b": table_raw.get("b", ([], [])),
        "c": table_raw.get("c", ([], [])),
    }
    return combined


def extract_contents(
    form_type: str,
    pdf_tmp_path: str,
    cell_dir: str,
    checkbox_config: str,
    result_dir: str,
    predictor,
    table_config: Dict,
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
    """
    
    # Prepare logging per file
    global file_logger
    log_dir = os.path.join("..", "..", "logs")
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
    
    # PRASE 2-1: Detect text in cells
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

            print(data_table)
            print(conf_table)
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

    # PRASE 2-2: TXT to JSON
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
