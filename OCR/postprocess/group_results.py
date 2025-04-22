import os
import re
import shutil

RESULTS_DIR="/home/node3/Documents/batch_3/results"

def extract_filename(src_file):
    return re.match(r"(.+?)_page_\d+_result.json", src_file).group(1)

for json_file in os.listdir(RESULTS_DIR):
    if json_file.endswith(".json"):
        json_file_path = os.path.join(RESULTS_DIR, json_file)
        extracted_filename = extract_filename(json_file)

        print(f"File: {json_file}\tExtractedName: {extract_filename(json_file)}")

        source_pdf_file = f"{extracted_filename}.pdf"
        source_pdf_file_path = os.path.join(RESULTS_DIR, source_pdf_file)

        dest_dir_path = os.path.join(RESULTS_DIR, extracted_filename)
        os.makedirs(dest_dir_path, exist_ok=True)
        dest_json_path = os.path.join(dest_dir_path, json_file)
        dest_pdf_path = os.path.join(dest_dir_path, source_pdf_file)

        shutil.move(json_file_path, dest_json_path)