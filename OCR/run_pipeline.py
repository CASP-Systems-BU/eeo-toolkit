import os
import shutil
from OCR.pipeline.split_pages import process_pdf
from OCR.pipeline.pdf_to_cells import pdf_to_cells
from OCR.pipeline.cells_to_contents import extract_contents
from OCR.utils.dir_helper import create_dir_if_not_exists, get_files_in_directory
from doctr.models import ocr_predictor
from utils.load_config import load_table_config, load_section_config

input_dir = "../files"  # The directory containing your PDF forms
res_dir = f"{input_dir}/results"  # The directory for the output json files

table_config_path = "config/table_config.yaml"  # DON'T MODIFY: The table schema config file for EEO-1 and EEO-5
section_config_path = "config/section_config.yaml"  # DON'T MODIFY: The section schema config file for EEO-1 and EEO-5

FORM_TYPE = "eeo1"
# FORM_TYPE = "eeo5"

if FORM_TYPE == "eeo1":
    form_config = "config/eeo1_typed_type1.yaml"
    checkbox_config = "config/eeo1_typed_type1_checkbox.yaml"
    PAGE_NUM_LS = [0]
elif FORM_TYPE == "eeo5":
    form_config = "config/eeo5_typed.yaml"
    checkbox_config = "config/eeo1_typed_type1_checkbox.yaml"
    PAGE_NUM_LS = [0, 1]
else:
    raise Exception(f"Invalid FORM_TYPE: {FORM_TYPE}")



if __name__ == "__main__":
    predictor = ocr_predictor(
        det_arch="fast_base",
        reco_arch="crnn_mobilenet_v3_large",
        pretrained=True,
        assume_straight_pages=True,
        detect_orientation=True,
        straighten_pages=False,
    )
    create_dir_if_not_exists(res_dir)
    table_config = load_table_config(table_config_path, FORM_TYPE)
    section_config = load_section_config(section_config_path, FORM_TYPE)
    pdf_files = get_files_in_directory(input_dir)
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        process_pdf(FORM_TYPE, pdf_path, form_config, predictor)

        pdf_tmp_path = os.path.join(input_dir, "tmp")

        inner_pdf_files = get_files_in_directory(pdf_tmp_path)
        for inner_pdf_file in inner_pdf_files:
            cur_pdf_path = os.path.join(pdf_tmp_path, inner_pdf_file)
            pdf_to_cells(cur_pdf_path, form_config, section_config, PAGE_NUM_LS)

            cell_path = os.path.join(pdf_tmp_path, "cells")
            extract_contents(FORM_TYPE, pdf_tmp_path, cell_path, checkbox_config, res_dir, predictor, table_config)

        # os.system(f"rm -rf {pdf_tmp_path}")
        shutil.rmtree(pdf_tmp_path)
        os.makedirs(pdf_tmp_path, exist_ok=True)