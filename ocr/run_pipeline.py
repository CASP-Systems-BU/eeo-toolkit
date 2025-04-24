"""
Script to run OCR pipeline on PDF forms in a directory.
Processes each PDF by splitting pages, extracting table cells, and extracting contents,
then outputs results as JSON files.
"""

import os
import shutil

from doctr.models import ocr_predictor

from ocr.pipeline.split_pages import process_pdf
from ocr.pipeline.pdf_to_cells import pdf_to_cells
from ocr.pipeline.cells_to_contents import extract_contents
from ocr.utilities.dir_helper import create_dir_if_not_exists, get_files_in_directory
from utilities.load_config import load_table_config, load_section_config


def main():
    """
    Main function to initialize OCR predictor and process all PDFs.
    """
    
    # ===================================> User Input Starts <===================================
    # Directory containing input PDF forms
    input_dir = input("Enter the input directory: ")
    # Directory to store result JSON files
    res_dir = input(
        'Enter the output directory (if empty, output_dir is "`input_dir`/results"): '
    )
    if res_dir == "":
        res_dir = os.path.join(input_dir, "results")

    # Choose form type: EEO-1 or EEO-5
    FORM_TYPE = input("Enter the form type (eeo1 or eeo5): ")

    # Paths to configuration files (do not modify)
    table_config_path = "config/table_config.yaml"
    section_config_path = "config/section_config.yaml"
    
    # ===================================> User Input Ends <===================================

    # Load specific form and checkbox configs based on form type
    if FORM_TYPE == "eeo1":
        form_config = "config/eeo1_typed_type1.yaml"
        checkbox_config = "config/eeo1_typed_type1_checkbox.yaml"
        PAGE_NUM_LS = [0]  # Pages to process for EEO-1
    elif FORM_TYPE == "eeo5":
        form_config = "config/eeo5_typed.yaml"
        checkbox_config = (
            "config/eeo1_typed_type1_checkbox.yaml"  # Common checkbox config
        )
        PAGE_NUM_LS = [0, 1]  # Pages to process for EEO-5
    else:
        raise Exception(f"Invalid FORM_TYPE: {FORM_TYPE}")

    # Initialize the OCR predictor with specified architectures
    predictor = ocr_predictor(
        det_arch="fast_base",
        reco_arch="crnn_mobilenet_v3_large",
        pretrained=True,
        assume_straight_pages=True,
        detect_orientation=True,
        straighten_pages=False,
    )

    # Create result directory if it doesn't exist
    create_dir_if_not_exists(res_dir)

    # Load table and section configurations
    table_config = load_table_config(table_config_path, FORM_TYPE)
    section_config = load_section_config(section_config_path, FORM_TYPE)

    # Get list of PDF files from input directory
    pdf_files = get_files_in_directory(input_dir)

    # Process each PDF file
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        # Split the PDF into individual pages and perform initial OCR
        process_pdf(FORM_TYPE, pdf_path, form_config, predictor)

        # Temporary directory for intermediate PDF pages
        pdf_tmp_path = os.path.join(input_dir, "tmp")

        # Iterate over the generated page PDFs
        inner_pdf_files = get_files_in_directory(pdf_tmp_path)
        for inner_pdf_file in inner_pdf_files:
            cur_pdf_path = os.path.join(pdf_tmp_path, inner_pdf_file)
            # Convert PDF pages to table cells
            pdf_to_cells(cur_pdf_path, form_config, section_config, PAGE_NUM_LS)

            # Directory containing cell images
            cell_path = os.path.join(pdf_tmp_path, "cells")
            # Extract contents from cells and generate results
            extract_contents(
                FORM_TYPE,
                pdf_tmp_path,
                cell_path,
                checkbox_config,
                res_dir,
                predictor,
                table_config,
            )

        # Clean up temporary directory for next PDF
        shutil.rmtree(pdf_tmp_path)
        os.makedirs(pdf_tmp_path, exist_ok=True)


if __name__ == "__main__":
    main()
