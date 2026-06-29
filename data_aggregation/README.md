
# Data Aggregation and Differentially Private Contingency Tables

This directory contains the post-OCR pipeline for EEO-1, EEO-4, and EEO-5 form data: parsing raw submissions, building contingency tables, applying differential privacy, and generating publication-ready Excel workbooks.

---

## Pipeline Overview

Each form type (EEO-1, EEO-4, EEO-5) runs through the same four stages in order:

```
Handler → Melt → DP → Sheet Generation
```

### Stage 1 — Handler
Parses raw EEO submissions, joins with NAICS/county reference data, and writes an enriched CSV.

```bash
python eeo1_handler.py         # → join_with_county.csv  (input_dir: /home/node0/Documents/csv_output)
python eeo4_handler.py         # → join_with_county.csv  (input_dir: /home/eolwd/data/eeo4_csv)
python eeo5_handler.py         # → eeo5.csv  (input_dir: /home/node0/Documents/eeo5_json_corrected/filtered)
python eeo5_handler_dedup.py   # → eeo5.csv  (same dir; drops Table C / new hires entirely)
```

`eeo5_handler_dedup.py` and `eeo5_melt_dedup.py` are a matched pair — use the dedup handler only with the dedup melt script, since the dedup handler's `eeo5.csv` has no new-hires columns for the full melt script to find.

### Stage 2 — Melt
Pivots wide Race × Gender columns into long format and materializes the full Cartesian product of dimension values so every combination is represented (missing combos fill with 0).

```bash
python eeo1_melt.py         # → melted_data.csv
python eeo4_melt.py         # → melted_data.csv  (also merges state employment data)
python eeo5_melt.py         # → melted_data.csv
python eeo5_melt_dedup.py   # → melted_data.csv  (excludes FULL-TIME NEW HIRES; pair with eeo5_handler_dedup.py)
```

### Stage 3 — Differential Privacy
Aggregates counts into contingency tables and adds Laplace noise.

```bash
python eeo1_dp.py   # → main.csv, side_GOR/JOG/NOG/JCG/JCR/JOR/NCG/NCR/NOR.csv
python eeo4_dp.py   # → WFRG_all_hires.csv, WFRG_new_hires.csv, JRG.csv, TFG.csv, TFR.csv
python eeo5_dp.py   # → WCRG.csv, JRG.csv, TWR.csv, TWG.csv, TJR.csv, TJG.csv
```

Privacy budgets:
- **EEO-1**: main table ε = 0.4; each of the 9 side tables ε = 0.7/8
- **EEO-4**: main WFRG table ε = 0.7; side tables (WFRG new hires, JRG, TFG, TFR) ε = 0.3 each
- **EEO-5**: main WCRG table ε = 0.7; side tables (JRG, TWR, TWG, TJR, TJG) ε = 0.3 each

### Stage 4 — Sheet Generation
Adjusts the noisy tables to enforce non-negativity of marginals via Mixed Integer Programming (cvxpy), applies structural zeroes where applicable, and writes Excel workbooks for publication.

```bash
python eeo1_sheet_generation.py
python eeo4_sheet_generation.py
python eeo5_sheet_generation.py
```

**EEO-1 outputs** (written to `output_dir`):
- `main_adj.csv`, `side_*_adj.csv`, `side_CNR.csv`, `side_NOG_adj_structured.csv`, `side_NOR_adj_structured.csv`
- `MA_Workforce_2026_EEO1_remove_all_zeroes.xlsx` — zero rows stripped from all tables
- `MA_Workforce_2026_EEO1_remove_structured_zeroes.xlsx` — only impossible NAICS × org-size rows removed

**EEO-4 outputs** (written to `output_dir`):
- `JRG_adj.csv`, `TFG_adj.csv`, `TFR_adj.csv`, `WFRG_combo_4way.csv`, `WFRG_combo_4way_adj.csv`, `WFRG_combo_adj.csv`
- `MA_Workforce_2026_EEO4_raw.xlsx` — raw noisy counts for review
- `MA_Workforce_2026_EEO4_remove_all_zeroes.xlsx` — negative counts clamped to zero
- `MA_Workforce_2026_EEO4_remove_structured_zeroes.xlsx` — MIP-adjusted counts for publication

**EEO-5 outputs** (written to `output_dir`):
- `WCRG_adj.csv`, `JRG_adj.csv`, `TWR_adj.csv`, `TWG_adj.csv`, `TJR_adj.csv`, `TJG_adj.csv`
- `MA_Workforce_2026_EEO5_raw.xlsx` — raw noisy counts for review
- `MA_Workforce_2026_EEO5_remove_all_zeroes.xlsx` — negative counts clamped to zero
- `MA_Workforce_2026_EEO5_adjusted.xlsx` — MIP-adjusted counts for publication

---

## Support Files

| File | Purpose |
|---|---|
| `const.py` | Shared constants (race/gender column names, job categories, salary ranges) |
| `utils.py` | Shared utility functions |
| `aggregation.py` | General aggregation helpers |
| `combine_csv.py` | Combines a directory of CSVs into a single Excel workbook (legacy EEO-5 contingency-table review tool; not part of the current pipeline) |
| `pyplots.py` | Visualization helpers |

---

## Requirements

See the project-level `requirements.txt`. Key dependencies: `pandas`, `numpy`, `cvxpy` (with CBC/SCIP/GLPK_MI solvers), `opendp`, `openpyxl`.
