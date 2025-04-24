
# Data Aggregation and Privacy-Preserving Contingency Tables

This subdirectory contains scripts for parsing, processing, and aggregating structured EEO-1 and EEO-5 form data into various levels of contingency tables, with support for differential privacy, visualization, and ZIP-to-county mapping.

---

## Overview

### Purpose
This pipeline processes EEO-1 and EEO-5 form data to:

- Normalize and flatten JSON files
- Enrich with NAICS and county-level data
- Generate 3-way, 2-way, and 1-way contingency tables
- Apply Laplace noise for differential privacy (ε = 1/21)
- Enforce suppression thresholds (e.g., counts < 50 → 0)
- Visualize results in multi-panel bar charts

### Output
- `aggregation.csv`, `join_with_county.csv`: Raw + enriched data
- `*_contingency.csv`: 1-way, 2-way, 3-way tables (DP-protected)
- `.png`: Visualization for each contingency table

---

## How to Use
Remember to set the input and output directories for each script as needed.
### Step 1: Aggregate JSON to CSV
```bash
python eeo1_handler.py
python eeo5_handler.py
```

### Step 2: Generate Contingency Tables (Differentially Private)
```bash
python eeo1_melt.py
python eeo5_melt.py
```

### Step 3: Suppress Low Counts
```bash
python round_count.py
```

### Step 4: Visualize Contingency Tables
```bash
python visualize.py
```

---

## Requirements

The same as the project requirements.

---

## Notes

- **Differential privacy** is applied using Laplace mechanism with ε = 1/21.
- Sheet name truncation is handled to fit Excel's 31-character limit.
