# EEO Report Postprocessing

This subdirectory contains scripts used to clean, filter, and normalize the raw OCR outputs from EEO-1 and EEO-5 reports after initial recognition. These scripts prepare the data for further aggregation and analysis.

---

## Overview

### Purpose

The postprocessing pipeline:

- Filters out consolidated EEO-1 reports and keeps only establishment-level forms
- Extracts relevant metadata from raw OCR-parsed JSON files
- Normalizes field values such as ZIP codes, NAICS codes, and checkboxes
- Identifies reports relevant to Massachusetts (MA) based on location metadata

### Output

- Filtered, cleaned JSON files with standardized fields
- Ready for downstream aggregation into contingency tables

---

## How to Use

Remember to modify the paths in the scripts to point to your input and output directories.
### Step 1: Filter EEO-1 Forms
Only keeps non-consolidated forms and forms relevant to Massachusetts.
```bash
python eeo1_filter.py
```

### Step 2: Filter EEO-5 Forms
Extracts metadata, county/city/ZIP/state info, and form tables for valid reports.
```bash
python eeo5_filter.py
```

---

## Requirements

- Python 3.10.12
- `rapidfuzz` (`pip install rapidfuzz`) – used for fuzzy string matching in EEO-1

---

## Notes

- `eeo1_filter.py` uses ZIP code and state matching to determine Massachusetts relevance.
- `eeo5_filter.py` parses checkbox values and table fields needed for public education reporting.
- Both scripts assume input files follow a consistent OCR JSON format.
