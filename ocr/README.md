# OCR Pipeline for EEO PDF Forms

Converts typed EEO-1 and EEO-4 PDF forms into structured JSON using DocTR. Runs fully offline in an air-gapped environment.

---

## Directory Structure

```
ocr/
├── run_pipeline.py        # Main entry point
├── config/                # YAML cell & checkbox coordinate maps
├── pipeline/              # Core OCR stages (split → cells → contents → checkboxes)
├── preprocess/            # Optional cleaning before OCR (classify, dedup, re-render)
├── postprocess/           # Per-form-type filters and JSON validation
├── utilities/             # Shared helpers (config loading, table validation, logging)
├── visualization/         # GUI tools (coordinate extraction, JSON viewer)
└── logger/                # Custom logger (file + console output)
```

---

## How to Use

> [!CAUTION]
> Only official standard EEO forms are supported. Third-party or customized form layouts require new YAML coordinate maps.

### Step 1 — (Optional) Preprocess

Clean the input PDFs before OCR:

```bash
python3 ocr/preprocess/classify.py       # Sort files by extension (remove non-PDFs)
python3 ocr/preprocess/deduplicate.py    # Remove duplicate forms via SHA-256 hashing
python3 ocr/preprocess/re_render_pdf.py  # Fix misaligned checkboxes/text via Firefox headless re-print
```

All three steps are optional. Run them in order if input quality is uncertain.

### Step 2 — Run OCR

```bash
python3 ocr/run_pipeline.py <input_dir> [output_dir] <form_type> <form_config> <checkbox_config> [log_dir]
```

| Argument | Required | Description |
|---|---|---|
| `input_dir` | Yes | Directory containing input PDF forms |
| `output_dir` | No | Output directory for JSON files (default: `input_dir/results/`) |
| `form_type` | Yes | One of: `eeo1`, `eeo4_type1`, `eeo4_type2`, `eeo5` |
| `form_config` | Yes | Path to cell coordinate YAML (see `config/`) |
| `checkbox_config` | Yes | Path to checkbox coordinate YAML (see `config/`) |
| `log_dir` | No | Log output directory (default: `../logs/`) |

**Examples:**

```bash
# EEO-1
python3 ocr/run_pipeline.py /data/eeo1_pdfs/ /data/eeo1_results/ \
    eeo1 config/eeo1_typed_type1.yaml config/eeo1_typed_type1_checkbox.yaml

# EEO-4 (government function forms with cover page)
python3 ocr/run_pipeline.py /data/eeo4_pdfs/ /data/eeo4_results/ \
    eeo4_type1 config/eeo4_typed_type1.yaml config/eeo4_typed_checkbox.yaml

# EEO-4 (municipalities forms without cover page)
python3 ocr/run_pipeline.py /data/eeo4_munis/ /data/eeo4_munis_results/ \
    eeo4_type2 config/eeo4_typed_type2.yaml config/eeo4_typed_checkbox.yaml
```

**Outputs:** One `<formname>_result.json` per PDF in `output_dir/`. A temporary `tmp/` directory is created and cleaned up automatically per form.

### Step 3 — Postprocess (Filter & Validate)

After OCR, run the per-form-type filter scripts (located in `postprocess/`):

```bash
python3 ocr/postprocess/json_validator.py    # EEO-1: validate OCR confidence and table structure
python3 ocr/postprocess/eeo1_filter.py       # EEO-1: filter to Massachusetts establishments
python3 ocr/postprocess/eeo4_type1_filter.py # EEO-4: merge cover + group pages (gov function forms)
python3 ocr/postprocess/eeo4_type2_filter.py # EEO-4: process munis forms (no cover page)
```

| Script | Form | Purpose |
|---|---|---|
| `json_validator.py` | EEO-1 | Confidence threshold check, table structure validation, city/state fuzzy correction |
| `eeo1_filter.py` | EEO-1 | Filter to MA establishments, extract EIN/NAICS/employer metadata |
| `eeo4_type1_filter.py` | EEO-4 | Attach cover-page metadata to each group file (one per government function) |
| `eeo4_type2_filter.py` | EEO-4 | Same output format as type1 but for forms with metadata embedded on page 0 |

---

## Configuration

Cell and checkbox coordinate maps live in `config/`. Each YAML maps named regions to `(x1, y1, x2, y2)` bounding boxes:

**Cell layout:**
```yaml
table:
  CELL_NAME: !!python/tuple
    - upper_right_x
    - upper_right_y
    - bottom_left_x
    - bottom_left_y
```

**Checkbox layout:**
```yaml
checkbox_field: !!python/tuple
  - upper_right_x
  - upper_right_y
  - bottom_left_x
  - bottom_left_y
```

Available configs:

| Form | Cells | Checkboxes |
|---|---|---|
| EEO-1 Type 1 | `eeo1_typed_type1.yaml` | `eeo1_typed_type1_checkbox.yaml` |
| EEO-1 Type 2 | `eeo1_typed_type2.yaml` | `eeo1_typed_type2_checkbox.yaml` |
| EEO-4 Type 1 | `eeo4_typed_type1.yaml` | `eeo4_typed_checkbox.yaml` |
| EEO-4 Type 2 | `eeo4_typed_type2.yaml` | `eeo4_typed_checkbox.yaml` |

> [!TIP]
> To define or update a coordinate map, use the GUI coordinate tool:
> ```bash
> python3 ocr/visualization/get_location.py
> ```
> Click on cell corners in the PDF viewer to read off coordinates.

> [!NOTE]
> EEO-1 coordinates are measured after whitespace cropping. Run the pipeline once to confirm crop boundaries before finalizing a new YAML.

---

## Utilities

| Script | Purpose |
|---|---|
| `utilities/table_validator.py` | Validate extracted table row/column sums |
| `utilities/margin_check.py` | Standalone check: compare reported vs. computed totals |
| `utilities/get_log_summary.py` | Parse run logs and summarize OCR errors and accuracy rate |
| `visualization/visualize_data.py` | GUI JSON viewer: browse results with bounding boxes and table rendering |

---

## Logging

Logs are written to `logs/` (or the `log_dir` argument) with one file per form. Run `utilities/get_log_summary.py` to produce a summary across all log files.

---

## Troubleshooting

- **No OCR output** — Verify `det_arch` and `reco_arch` in `run_pipeline.py` match the installed DocTR model files.
- **Invalid table sums** — Adjust cell coordinates in the relevant YAML or raise `CONFIDENCE_THRESHOLD`.
- **Stale `tmp/` directory** — Delete it manually; the pipeline cleans it automatically between runs but not on a hard crash.
