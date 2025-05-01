"""
Module: split_pages.py

Detects content boundaries in PDF pages, crops to those bounds,
splits multi-page EEO-1 forms into individual page PDFs,
validates section headers using OCR predictions and sequence matching,
and logs processing steps and errors.
"""

import os
import cv2
import fitz
import numpy as np
from PIL import Image
from difflib import SequenceMatcher

from utilities.load_config import load_cell_coordination_config
from utilities.dir_helper import create_dir_if_not_exists
from logger.logger import Logger


def detect_outer_edges_in_pdf(page, scale_factor=1):
    """
    Render a PDF page to grayscale, detect edges, and return the
    bounding rectangle around the detected content edges.

    :param page (fitz.Page): The PDF page to analyze.
    :param scale_factor (float): Zoom factor for rendering to improve edge detection.

    returns fitz.Rect: Bounding box of detected content edges.
    """
    """Detect edges and return the bounding box of content."""
    pix = page.get_pixmap(
        matrix=fitz.Matrix(scale_factor, scale_factor), colorspace=fitz.csGRAY
    )
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w)

    edges = cv2.Canny(img, 50, 150)

    y_coords, x_coords = np.where(edges > 0)
    min_x, max_x = x_coords.min(), x_coords.max()
    min_y, max_y = y_coords.min(), y_coords.max()

    return fitz.Rect(min_x, min_y, max_x, max_y)


def crop_pdf_to_bounds(pdf_path, filename, output_folder, scale_factor=3):
    """
    Crop each page of a PDF to the detected content bounds and
    save as a new multi-page PDF with fixed dimensions.

    :param pdf_path (str): Path to the source PDF.
    :param filename (str): Base filename for the output.
    :param output_folder (str): Directory where the cropped PDF will be saved.
    :param scale_factor (int): Zoom factor when cropping to maintain resolution.

    :returns str: Path to the saved cropped PDF file.
    """
    DEFAULT_WIDTH = 523
    DEFAULT_HEIGHT = 679

    pdf_doc = fitz.open(pdf_path)
    new_doc = fitz.open()

    for i, page in enumerate(pdf_doc):
        detected_rect = detect_outer_edges_in_pdf(page)

        cropped_page = new_doc.new_page(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT)

        cropped_pix = page.get_pixmap(
            matrix=fitz.Matrix(scale_factor, scale_factor),
            clip=detected_rect,
            colorspace=fitz.csGRAY,
        )

        # Insert cropped content into the new page
        cropped_page.insert_image(cropped_page.rect, pixmap=cropped_pix)

    # Save the final cropped PDF
    out_path = os.path.join(output_folder, f"{filename}_cropped.pdf")
    new_doc.save(out_path)
    new_doc.close()
    return out_path


def process_pdf(
    form_type: str, pdf_path: str, form_config: str, predictor, sim_threshold: float=0.70, log_dir: str = "../logs"
):
    """
    Main entry point: splits an input PDF into pages (for EEO-1) or copies intact,
    crops to content bounds, and optionally filters pages by header similarity.

    :param form_type (str): 'eeo1' or 'eeo5'.
    :param pdf_path (str): Path to the input PDF file directory.
    :param form_config (str): Path to the config mapping for header detection.
    :param predictor: OCR predictor callable that returns page blocks with text.
    :param sim_threshold (float): Similarity threshold to retain pages.
    :param log_dir: Log directory path
    """
    file_dir = os.path.dirname(pdf_path)
    key_map = load_cell_coordination_config(form_config)
    output_dir = f"{file_dir}/tmp"
    os.makedirs(output_dir, exist_ok=True)
    global file_logger
    create_dir_if_not_exists(log_dir)

    base_filename = os.path.basename(pdf_path).replace(".pdf", "")
    file_logger = Logger(
        log_file_path=f"{log_dir}/split_pages_{base_filename}.log",
        prefix="SPLIT_PAGES",
    )
    try:
        doc = fitz.open(pdf_path)
        if form_type == "eeo1":
            for page_num in range(len(doc)):
                file_logger.info(f"Processing {base_filename} - Page {page_num + 1}")
                new_pdf_path = os.path.join(
                    output_dir, f"{base_filename}_page{page_num + 1}.pdf"
                )
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                new_doc.save(new_pdf_path)
                new_doc.close()
                cut_edges(new_pdf_path)
                check_page(new_pdf_path, key_map, predictor, sim_threshold, page_num)
        else:
            file_logger.info(f"Processing {base_filename}")
            new_pdf_path = os.path.join(output_dir, f"{base_filename}.pdf")
            doc.save(new_pdf_path)
            cut_edges(new_pdf_path)
        doc.close()

    except Exception as e:
        file_logger.error(f"Error processing {pdf_path}: {e}")


def cut_edges(pdf_path: str):
    """
    Crop the PDF to the detected content bounds and save it.
        
    :prarm pdf_path (str): Path to the PDF file to crop.
    """
    file_dir = os.path.dirname(pdf_path)
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    crop_pdf_to_bounds(pdf_path, filename, file_dir, scale_factor=3)
    os.remove(pdf_path)


def check_page(new_pdf_path, key_map, predictor, sim_threshold, page_num):
    """
    Use OCR predictor to extract the first line of text and compare against
    expected header, removing pages below similarity threshold.

    :param pdf_path (str): Path to the cropped PDF page.
    :param key_map (dict): Mapping of sections to detection rects.
    :param predictor: Doctr OCR predictor instance
    :param sim_threshold (float): Minimum ratio to keep the page.
    :param page_num (int): Current page number (for logging).
    """
    dir_name = os.path.dirname(new_pdf_path)
    filename = os.path.splitext(os.path.basename(new_pdf_path))[0]
    tmp_pdf_path = os.path.join(dir_name, f"{filename}_cropped.pdf")
    new_doc = fitz.open(tmp_pdf_path)
    page = new_doc[0]
    rect = fitz.Rect(*(key_map["a"]["TYPE_OF_REPORT"]))
    cropped_pix = page.get_pixmap(clip=rect)
    img = Image.frombytes(
        "RGB", (cropped_pix.width, cropped_pix.height), cropped_pix.samples
    )
    img_np = np.array(img)
    result = predictor([img_np])

    LINE = "SECTION A - TYPE OF REPORT"

    try:
        first_line = result.pages[0].blocks[0].lines[0]
        page_text = " ".join([word.value for word in first_line.words])
        similarity_score = SequenceMatcher(None, LINE, page_text).ratio()
        if similarity_score >= sim_threshold:
            file_logger.info(f"Page {page_num + 1} saved: {tmp_pdf_path}")
            filename = os.path.splitext(os.path.basename(tmp_pdf_path))[0]
            file_logger.info(
                f"Page {page_num + 1} of file {filename} has been processed."
            )
        else:
            file_logger.info(
                f"Page {page_num + 1} removed: {tmp_pdf_path}\tText: {page_text}\tSimilarity Score: {similarity_score}"
            )
            os.remove(tmp_pdf_path)
    except Exception as e:
        file_logger.warning(
            f"Some error predicting {LINE}, exception: {e}, removing it..."
        )
        os.remove(tmp_pdf_path)
    new_doc.close()
