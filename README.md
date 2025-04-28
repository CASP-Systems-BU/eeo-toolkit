# EEO Form OCR Pipeline

---

## Description

A compliance automation tool for processing **EEO-1** and **EEO-5** PDF reports as required by *Section 141 of the Massachusetts Salary Range Transparency Law (2024)*. Converts typed and scanned PDF documents into structured JSON data with automated OCR processing and workforce statistics aggregation.

---

## Folder Structure

```
├── data_aggregation/     # Data aggregation scripts
├── ocr/                  # OCR pipeline
│   ├── config/           # YAML for cell & checkbox layouts
│   ├── pipeline/         # ocr split, cell extraction, JSON conversion
│   ├── preprocess/       # classify, dedupe, rendering scripts
│   ├── postprocess/      # validation and summary
│   ├── visualization/    # GUI tools (coord extraction, JSON viewer)
├── public_data/          # CVS data for the data mapping (zipcodes, RUCA codes, County info, etc.)
├── run_pipeline.py       # Main entrypoint
├── requirements.txt      # Program dependencies
└── README.md             # This documentation
```
