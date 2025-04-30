# EEO Form Postprocessing

This directory contains scripts to clean, validate, filter, and normalize the raw OCR outputs from EEO-1 and EEO-5 reports.

---

## Overview

The postprocessing pipeline provides the following functionality:

- Validate OCR confidence scores, table integrity, and correct city/state information via fuzzy string matching
- Filter out consolidated EEO-1 reports and keep only establishment-level forms
- Extract relevant metadata from raw OCR-parsed JSON files
- Normalize field values such as ZIP codes, NAICS codes, and checkboxes
- Identify forms relevant to Massachusetts (MA) based on location metadata


---

## How to Use

Remember to modify the paths in the scripts to point to your input and output directories.
### Requirements

- Python 3.10.12
- `rapidfuzz` (`pip install rapidfuzz`) – used for fuzzy string matching
- Custom module: `table_validator` (must be located in the project’s `utilities` folder)



### Step 1: Validate and Correct EEO-1 JSONs
> [!NOTE]
> `json_validator.py` corrects misread city/state fields, validates form content for EEO-1s, and logs summary reports.

Performs text confidence checks, table validation, and city/state correction using fuzzy matching.
```bash
python json_validator.py
```

Output files:
- Files with city/state corrections and table structure validation
- Summary log highlighting invalid or low-confidence files

### Step 2: Filter EEO-1 Forms
> [!NOTE]
>`eeo1_filter.py` filters based on Massachusetts relevance using ZIP/state fields.

Keeps only non-consolidated reports relevant to Massachusetts.
```bash
python eeo1_filter.py
```
Output files:
- Filtered EEO-1 JSON files for Massachusetts (MA) only with standardized fields

### Step 3: Filter EEO-5 Forms
> [!NOTE]
> `eeo5_filter.py` handles structured education form parsing including checkboxes.

Extracts structured metadata including location, checkbox status, and form tables.
```bash
python eeo5_filter.py
```
Output files:
- Filtered EEO-5 JSON files with standardized fields
