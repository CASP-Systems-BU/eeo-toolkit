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


def get_files_in_directory(directory, extension=".pdf"):
    """
    
    :param directory
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

    Returns:
        bool: True if the file exists, False otherwise.
    """
    return os.path.exists(path)


def gen_cell(
    page, fields, key, output_folder, filename, section, scale_factor=3, padding=45
):
    """
    Crop a region specified by 'fields[key]' from 'page', add padding,
    and save as a new PDF cell file.

    Args:
        page (fitz.Page): PDF page object.
        fields (dict): Mapping of cell keys to fitz.Rect coordinates.
        key (str): The specific cell key to crop.
        output_folder (str): Directory to save cropped cell PDFs.
        filename (str): Base filename without extension.
        section (str): Section identifier for naming.
        scale_factor (int): Zoom factor for rendering.
        padding (int): Padding (in pixels) around the cropped region.
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
    Split a PDF page into multiple cell PDFs for a given section.

    Args:
        page (fitz.Page): PDF page object.
        section (str): Section identifier.
        filename (str): Base filename.
        output_folder (str): Directory for saving cell PDFs.
        key_map (dict): Mapping of all sections to their field coordinates.
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
    Orchestrate the splitting of a PDF into individual cell PDFs.

    Args:
        pdf_path (str): Path to input PDF file.
        form_config (str): Config mapping sections to cell coordinates.
        section_config (Dict[int, List[str]]): Mapping of page indices to section lists.
        page_num_ls (List[int]): Page indices to process.
        log_dir (str): Directory for log files.
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
