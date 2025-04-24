import os
from typing import Dict, List
import fitz

from utilities.load_config import load_cell_coordination_config
from utilities.dir_helper import create_dir_if_not_exists
from logger.logger import Logger


def get_files_in_directory(directory, extension=".pdf"):
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist.")
    return [f for f in os.listdir(directory) if f.lower().endswith(extension)]


def file_exists(path: str) -> bool:
    return os.path.exists(path)


def gen_cell(
    page, fields, key, output_folder, filename, section, scale_factor=3, padding=45
):
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

    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    filename_no_ext = os.path.splitext(filename)[0]
    file_dir = os.path.dirname(pdf_path)

    key_map = load_cell_coordination_config(form_config)

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
