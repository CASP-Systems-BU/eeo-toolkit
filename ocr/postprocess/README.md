# EEO Report Postprocessing

This subdirectory contains scripts used to clean, validate, filter, and normalize the raw OCR outputs from EEO-1 and EEO-5 reports after initial recognition. These scripts ensure only high-quality, relevant data moves forward for aggregation and analysis.

---

## Overview

### Purpose

The postprocessing pipeline:

- Validates OCR confidence scores, table integrity, and corrects city/state information via fuzzy matching
- Filters out consolidated EEO-1 reports and keeps only establishment-level forms
- Extracts relevant metadata from raw OCR-parsed JSON files
- Normalizes field values such as ZIP codes, NAICS codes, and checkboxes
- Identifies reports relevant to Massachusetts (MA) based on location metadata


### Output

- Filtered, cleaned JSON files with standardized fields
- Reports with city/state corrections and table structure validation
- Summary log highlighting invalid or low-confidence files
- Ready for downstream aggregation into contingency tables

---

## How to Use

Remember to modify the paths in the scripts to point to your input and output directories.

### Step 1: Validate and Correct EEO-1 JSONs
Performs text confidence checks, table validation, and city/state correction using fuzzy matching.
```bash
python json_validator.py
```

### Step 2: Filter EEO-1 Forms
Keeps only non-consolidated reports relevant to Massachusetts.
```bash
python eeo1_filter.py
```

### Step 3: Filter EEO-5 Forms
Extracts structured metadata including location, checkbox status, and form tables.
```bash
python eeo5_filter.py
```

---

## Requirements

- Python 3.10.12
- `rapidfuzz` (`pip install rapidfuzz`) – used for fuzzy string matching
- Custom module: `table_validator` (must be located in the project’s `utilities` folder)

---

## Notes
- `json_validator.py` corrects misread city/state fields, validates form content for EEO-1s, and logs summary reports.
- `eeo1_filter.py` filters based on Massachusetts relevance using ZIP/state fields.
- `eeo5_filter.py` handles structured education form parsing including checkboxes.
- All scripts expect input OCR JSONs in a consistent format as produced by the document parser.
