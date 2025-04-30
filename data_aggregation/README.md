
# Data Aggregation and Differentially Private Contingency Tables

This directory contains scripts for parsing, processing, aggregating, visualizing and anonymizing structured EEO-1 and EEO-5 form data.

---

## Overview

The scripts provide the following functionality for the EEO-1 and EEO-5 form data:

- Normalize and flatten JSON files
- Enrich with NAICS and county-level data
- Generate 3-way, 2-way, and 1-way contingency tables
- Apply Laplace noise for differential privacy (ε = 1/21)
- Visualize results in multi-panel bar charts


---

## How to Use

### Requirements

The same as the project requirements.

Read the paths from parameters.
### Step 1: Aggregate JSON to CSV
```bash
python eeo1_handler.py
python eeo5_handler.py
```
Output files:
- `aggregation.csv`, `join_with_county.csv`: Raw + enriched data

### Step 2: Generate Contingency Tables (Differentially Private)
> [!NOTE]
> **Differential privacy** is applied using Laplace mechanism with ε = 1/21.

```bash
python eeo1_melt.py
python eeo5_melt.py
```
Output files:
- `*_contingency.csv`: 1-way, 2-way, 3-way tables

### Step 3: Visualize Contingency Tables
```bash
python visualize.py
```
Output files:
- `.png`: Pie charts for each contingency table


---
