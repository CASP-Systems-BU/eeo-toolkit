
# Figure Generation

This directory produces the publication-ready charts and summary tables for the 2026 Massachusetts Workforce Data Report. It consumes the MIP-adjusted CSV outputs from `data_aggregation/` (Stage 7) and writes figures and companion tables to a configured output directory.

---

## How to Use

### Requirements

- Dependencies listed in the project-level `requirements.txt` (key: `matplotlib`, `pandas`)
- Montserrat font installed on your system (used for all chart text)

### Steps

Configure the input and output paths in the relevant config file, then run:

```bash
python eeo1_figure_generation.py   # Figures 1–13
python eeo4_figure_generation.py   # Figures 14–29
python eeo5_figure_generation.py   # Figures 30–41
```

---

## Inputs

| Script                        | Input files                                    |
|-------------------------------|------------------------------------------------|
| `eeo1_figure_generation.py`   | `main_adj.csv`, `side_JOG_adj.csv`, `side_JOR_adj.csv` |
| `eeo4_figure_generation.py`   | `JRG_adj.csv`, `WFRG_combo_adj.csv` |
| `eeo5_figure_generation.py`   | `JRG_adj.csv`, `WCRG_adj.csv`, `TWG_adj.csv`, `TWR_adj.csv` |

Input paths are set in the config files (`INPUT_DIR`).

---

## Outputs

Each figure function writes:
- A `.png` chart to `OUTPUT_DIR`
- A companion summary `.csv` table to `TABLE_DIR` (a subdirectory of `OUTPUT_DIR`)

---

## File Structure

| File / Directory         | Purpose                                                        |
|--------------------------|----------------------------------------------------------------|
| `eeo1_figure_config.py`  | Paths, color palette, display orders for EEO-1 figures        |
| `eeo4_figure_config.py`  | Paths, color palette, display orders, salary labels for EEO-4  |
| `eeo5_figure_config.py`  | Paths, 7-race color palette, work type / agent type orders for EEO-5 |
| `eeo1_figure_generation.py` | Entry point — loads EEO-1 data and calls figure functions  |
| `eeo4_figure_generation.py` | Entry point — loads EEO-4 data and calls figure functions  |
| `eeo5_figure_generation.py` | Entry point — loads EEO-5 data and calls figure functions  |
| `figures/`               | One module per figure (`figure_1.py` … `figure_41.py`)         |

---

## Configuration

Edit `eeo1_figure_config.py`, `eeo4_figure_config.py`, or `eeo5_figure_config.py` to change:

- `INPUT_DIR` — where adjusted CSVs are read from
- `OUTPUT_DIR` — where `.png` files are written
- `TABLE_DIR` — where summary `.csv` tables are written
