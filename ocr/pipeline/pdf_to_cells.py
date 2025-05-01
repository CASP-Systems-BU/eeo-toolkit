"""
Module: pdf_to_cells.py

Splits PDF forms into individual cell PDFs based on predefined coordinates,
applies padding around each cell, and logs processing steps. Includes utilities
for file discovery and existence checks.
"""

import os
from typing import Dict, List
import fitz

from utilities.load_config import load_cell_coordination_config
from utilities.dir_helper import create_dir_if_not_exists
from logger.logger import Logger


def get_files_in_directory(directory: str, extension: str = ".pdf"):
    """

    :param directory: file directory
    :param data: Raw doctr JSON

    :return: a list of files in 'directory' matching the given 'extension'.

    :raise FileNotFoundError: If the specified directory does not exist.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")
    files = [f for f in os.listdir(directory) if f.lower().endswith(extension)]
    files.sort()
    return files


def file_exists(path: str) -> bool:
    """
    Check whether a file exists at the given path.

    :param path: Path to the file
    :return: True if the file exists, False otherwise
    """
    return os.path.exists(path)


def gen_cell(
    page, fields, key, output_folder, filename, section, scale_factor=3, padding=45
):
    """
    Crop a specified region from a PDF page, add padding, and save as a new PDF cell.

    Steps:
      1. Render the clipped region at the given scale factor in grayscale.
      2. Compute new page dimensions by adding padding.
      3. Create a new PDF page and insert the cropped image centered.
      4. Save the padded cell PDF to the output folder.

    :param page: fitz.Page object representing the PDF page
    :param fields: Mapping of cell keys to fitz.Rect coordinates
    :param key: The specific cell key to crop
    :param output_folder: Directory to save the cropped cell PDFs
    :param filename: Base filename (without extension) for output
    :param section: Section identifier used in the output filename
    :param scale_factor: Zoom factor for rendering (default: 3)
    :param padding: Number of pixels to pad around the cropped region (default: 45)
    """
    new_doc = fitz.open()

    rect = fields[key]

    cropped_pix = page.get_pixmap(
        matrix=fitz.Matrix(scale_factor, scale_factor),
        clip=rect,
        colorspace=fitz.csGRAY,
    )

    pad_x = padding
    pad_y = padding

    # New page dimensions with padding
    new_width = cropped_pix.width + 2 * pad_x
    new_height = cropped_pix.height + 2 * pad_y

    # Create a new page with larger dimensions
    new_page = new_doc.new_page(width=new_width, height=new_height)

    # Insert the image centered on the new page
    new_page.insert_image(
        fitz.Rect(pad_x, pad_y, pad_x + cropped_pix.width, pad_y + cropped_pix.height),
        pixmap=cropped_pix,
    )

    # Save the new cropped PDF with padding
    out_path = os.path.join(output_folder, f"{filename}_section_{section}_{key}.pdf")
    new_doc.save(out_path)
    new_doc.close()
    file_logger.info(f"Cropped PDF with padding saved to {out_path}")


def split_section(
    page: fitz.Page, section: str, filename: str, output_folder: str, key_map: dict
):
    """
    Split a PDF page into individual cell PDFs for a given section.

    Steps:
      1. Retrieve the coordinate mapping for the section.
      2. Call gen_cell for each key in that section.

    :param page: fitz.Page object representing the PDF page
    :param section: Section identifier (e.g., 'E', 'A')
    :param filename: Base filename for output PDFs
    :param output_folder: Directory in which to save cell PDFs
    :param key_map: Mapping of all sections to their field coordinate dicts
    """
    file_logger.info(f"Splitting Section {section} of the PDF...")
    fields = key_map[section]

    for key in fields.keys():
        gen_cell(page, fields, key, output_folder, filename, section)


def pdf_to_cells(
    pdf_path: str,
    form_config: str,
    section_config: Dict,
    page_num_ls: List[int],
    log_dir: str = "../logs",
):
    """
    Orchestrate splitting a PDF into individual cell PDFs across specified pages.

    Steps:
      1. Load section-to-coordinate mapping from the form config.
      2. Initialize logging and ensure output directories exist.
      3. For each page index, split into cells based on section_config.

    :param pdf_path: Path to the input PDF file
    :param form_config: Path to YAML config mapping sections to cell coordinates
    :param section_config: Mapping from page indices to lists of section identifiers
    :param page_num_ls: List of page indices to process
    :param log_dir: Directory for log files (default: "../logs")
    """
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    filename_no_ext = os.path.splitext(filename)[0]
    file_dir = os.path.dirname(pdf_path)

    key_map = load_cell_coordination_config(form_config)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    global file_logger
    file_logger = Logger(
        log_file_path=f"{log_dir}/{filename_no_ext}.log",
        prefix="PDF_TO_CELLS",
    )

    create_dir_if_not_exists(log_dir)

    if key_map == {}:
        file_logger.error("Empty config")
        return

    if not file_exists(pdf_path):
        file_logger.error(f"File {pdf_path} does not exist.")
        return

    # PRASE 1: Split PDF into sections
    out_dir = os.path.join(file_dir, "cells")
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)

    # # Split the PDF into sections
    for page_num in page_num_ls:
        cur_page = doc[page_num]
        cur_page_conf = section_config[page_num]
        for sect in cur_page_conf:
            split_section(cur_page, sect, filename, out_dir, key_map)

    doc.close()
