
# Data Aggregation and Differentially Private Contingency Tables

This directory contains scripts for parsing, processing, aggregating, visualizing and anonymizing structured EEO-1 and EEO-5 form data.

---

## Overview

The scripts process EEO-1 and EEO-5 form data to:

- Normalize and flatten JSON files
- Enrich with NAICS and county-level data
- Generate 3-way, 2-way, and 1-way contingency tables
- Apply Laplace noise for differential privacy (ε = 1/21)
- Visualize results in multi-panel bar charts


---

## How to Use
Read the paths from parameters.
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

### Step 3: Visualize Contingency Tables
```bash
python visualize.py
```

The scripts will generate the following outputs:
- `aggregation.csv`, `join_with_county.csv`: Raw + enriched data
- `*_contingency.csv`: 1-way, 2-way, 3-way tables
- `.png`: Pie charts for each contingency table


---

## Requirements

The same as the project requirements.

---


## Notes

- **Differential privacy** is applied using Laplace mechanism with ε = 1/21.
- Sheet name truncation is handled to fit Excel's 31-character limit.
