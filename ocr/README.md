# OCR Pipeline for EEO PDF Files

The repository contains scripts that converts typed and scanned PDF documents into structured JSON data using OCR.

---

## Folder Structure

```
├── ocr/
│   ├── config/           # YAML for cell & checkbox layouts
│   ├── pipeline/         # Cell extraction, OCR, JSON conversion
│   ├── preprocess/       # Classification, deduplication, render scripts
│   ├── postprocess/      # Data validation
│   ├── visualization/    # GUI tools (coord extraction, JSON viewer)
│   ├── utilities/        # Helper functions
│   └── README.md         # This documentation
└── ...
```

---

## Installation
[Requirements](../README.md#31-requirements)

## How to Use

> [!CAUTION]
> The current version of the OCR pipeline only supports the official standard EEO forms. Any third-party and customized forms are not supported.

### Configure the Pipeline

- The pipeline relies on coordinate maps for each cell and checkbox region. Make sure the following files are present under `OCR/config`:
  - **EEO-1 Type1**:
    - `eeo1_typed_type1.yaml` (cells)
    - `eeo1_typed_type1_checkbox.yaml`
  - **EEO-1 Type2**:
    - `eeo1_typed_type2.yaml`
    - `eeo1_typed_type2_checkbox.yaml`
  - **EEO-5**:
    - `eeo5_typed.yaml`
    - `eeo5_typed_checkbox.yaml`

**Cell layout YAML**:

```yaml
table:
  CELL_NAME: !!python/tuple
    - upper_right_x
    - upper_right_y
    - bottom_left_x
    - bottom_left_y
```

**Checkbox layout YAML**:

```yaml
checkbox_field: !!python/tuple
  - upper_right_x
  - upper_right_y
  - bottom_left_x
  - bottom_left_y
```


> [!TIP]
> To define new layouts, use the GUI utility and click on the corners of the cells to get their coordinates:
>
> ```bash
> python3 ocr/visualization/get_location.py
> ```
>
> and click cell corners to get the coordination.

> [!NOTE]
> Mention 
> The coordination for EEO-1 forms are generated after the white-space-cutting.
> The EEO-5 forms do not have scaling issues and do not require the white-space-cutting.
> In case there are form alignment issues, you may want to trim white margins before fetching the coordinates.

### Running the Pipeline

#### 1. Pre-Processing (Optional)

#### 1.1 Classification

Use `ocr/preprocess/classify.py` to separate EEO-1 vs. EEO-5 PDFs.

```bash
python3 ocr/preprocess/classify.py
```

#### 1.2 Deduplication

Identify and remove duplicate forms based on file hashes:

```bash
python3 ocr/preprocess/deduplicate.py
```

#### 1.3 Layer Rendering Fix

Apply rendering corrections for PDF layers that misalign text and forms:

```bash
python3 ocr/preprocess/re_render_pdf.py
```

#### 2. Run OCR Tool

Edit `run_pipeline.py` to set:

- `input_dir`
- `FORM_TYPE` (`eeo1` or `eeo5`)
- Paths to YAML configs

Then:

```bash
python3 ocr/run_pipeline.py
```

This generates `<formname>_result.json` files under `../files/results`.

---



## Logging

All pipeline logs are stored under `logs/` with filenames `<formname>.log`. Uses a prefixed timestamp format.

---

## Troubleshooting

- **No OCR output?** Verify `det_arch` and `reco_arch` in `run_pipeline.py` match installed DocTR models.
- **Invalid table sums?** Adjust `table_config.yaml` cell coordinates or increase `CONFIDENCE_THRESHOLD`.
- **Missing files?** Make sure intermediate `tmp/` directory is cleared after each run by `run_pipeline.py`.
