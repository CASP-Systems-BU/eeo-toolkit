"""
organize_results.py

Organizes OCR result JSON files and their corresponding PDFs into
separate subdirectories named after each form's base filename.
"""

import os
import re
import shutil

# Directory containing the result files (JSON and PDFs)
RESULTS_DIR = "/home/node3/Documents/batch_3/results"


def extract_filename(src_file: str) -> str:
    """
    Extract the base filename from a JSON result file name.
    E.g., 'myform_page_2_result.json' -> 'myform'.

    :param src_file: Filename of the JSON result
    :return: Extracted base name before '_page_<n>_result.json'
    """
    match = re.match(r"(.+?)_page_\d+_result\.json", src_file)
    if not match:
        raise ValueError(f"Filename does not match expected pattern: {src_file}")
    return match.group(1)


if __name__ == "__main__":
    # Loop through all files in the results directory
    for json_file in os.listdir(RESULTS_DIR):
        # Process only JSON result files
        if not json_file.endswith(".json"):
            continue

        json_path = os.path.join(RESULTS_DIR, json_file)
        # Derive the base name (form identifier)
        base_name = extract_filename(json_file)
        print(f"Processing: {json_file} -> Directory: {base_name}")

        # Construct expected PDF filename for this form
        pdf_filename = f"{base_name}.pdf"
        pdf_path = os.path.join(RESULTS_DIR, pdf_filename)

        # Create a subdirectory for this form’s files
        dest_dir = os.path.join(RESULTS_DIR, base_name)
        os.makedirs(dest_dir, exist_ok=True)

        # Move the JSON file into the subdirectory
        dest_json = os.path.join(dest_dir, json_file)
        shutil.move(json_path, dest_json)

        # If the corresponding PDF exists, move it as well
        if os.path.exists(pdf_path):
            dest_pdf = os.path.join(dest_dir, pdf_filename)
            shutil.move(pdf_path, dest_pdf)
        else:
            # Warn if the PDF is missing
            print(f"Warning: PDF not found for {base_name}: expected {pdf_filename}")
