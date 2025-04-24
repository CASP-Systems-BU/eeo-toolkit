# PDF and File Preprocessing for OCR Pipelines

This subdirectory contains scripts to prepare scanned documents and related files for OCR-based form processing. The utilities help ensure that only valid, non-duplicate, and properly rendered files are passed to the OCR engine.

---

## Overview

### Purpose

This preprocessing pipeline supports the OCR workflow by:

- **Deduplicating files** using SHA-256 content hashes to avoid redundant processing
- **Classifying files** based on extension to filter out unsupported types (e.g., `.csv`, `.xlsx`)
- **Re-rendering PDFs** using Firefox headless printing to fix layout issues such as misaligned checkboxes or form fields

### Output

- Only one retained copy per duplicate group
- Organized folders by file type (e.g., `pdf/`, `xlsx/`, `No_Extension/`)
- Re-rendered and corrected PDF documents
- Comprehensive logs for actions taken

---

## How to Use

Be sure to update file paths and Firefox settings in the scripts as needed.

### Step 1: Deduplicate Files
Remove exact duplicate files based on content hash.

```bash
python deduplicate.py
```

### Step 2: Classify Files by Type
Organize files into folders by extension and separate out unsupported types.

```bash
python classify.py
```

### Step 3: Re-render PDFs with Layout Fixes (Optional)
Fix formatting issues in PDF forms by printing them via a headless Firefox session.

```bash
python re_render_pdf.py
```

---

## Requirements

- Python 3.10.12
- Firefox (installed via Snap or system)
- [Geckodriver](https://github.com/mozilla/geckodriver) (make sure path is set in `re_render_pdf.py`)
- Selenium (`pip install selenium`)

---

## Notes

- `re_render_pdf.py` assumes Firefox profile access and a configured environment for headless PDF printing.
- Run `classify.py` before OCR to filter out non-form file types like `.csv` or `.xlsx`.
- The Firefox browser is restarted periodically in `re_render_pdf.py` to prevent crashes during batch processing.
