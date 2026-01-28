# Instructions for running pipeline on EEO-4 files:

## How to Use

### Requirements

The same as the project requirements.

### Step 1: run_pipeline.py

Run:
```bash
cd ocr
python3 run_pipeline.py <INPUT PATH WITH EEO4 PDF FILES> <OUTPUT PATH FOR JSON FILES> eeo4 config/eeo4_typed.yaml config/eeo4_typed_checkbox.yaml <PATH FOR LOGS>
```

Inputs EEO-4 pdf files. Outputs files for each eeo-4 pdf file in the input directory. Each pdf file outputs a json file for its first page and json files for each function listed in the file.

The dimensions for the checkboxes are set in eeo4_typed_checkbox.yaml.

The dimensions for tables is set on eeo4_typed.yaml.  Here is a description for the table variables set in that file:

<details>
<summary>Variable Description</summary>

- table1:
  - a1: Hispanic Male column for rows 1-40 (full-time)
  - a2: Hispanic Female column for rows 1-40 (full-time)
  - a3: Other demographic columns for rows 1-40 (full-time)
  - a4: Row sum column for rows 1-40 (full-time)
- table2:
  - a5: Hispanic Male column for rows 41-64 (full-time)
  - a6: Hispanic Female column for rows 41-64 (full-time)
  - a7: Other demographic columns for rows 41-64 (full-time)
  - a8: Row sum column for rows 41-64 (full-time)
  - atotal1: Hispanic Male column for row 65 (full-time total)
  - atotal2: Hispanic Female column for row 65 (full-time total)
  - atotal3: Other demographic columns for row 65 (full-time total)
  - atotal4: Row sum column for row 65 (full-time total)
  - bhistm_1: Hispanic Male column for row 66 (part-time officials)
  - bhistf_1: Hispanic Female column for row 66 (part-time officials)
  - brest_1: Other demographic columns for row 66 (part-time officials)
  - btotal_1: Row sum column for row 66 (part-time officials)
  - bhistm_2: Hispanic Male column for rows 67-70 (part-time)
  - bhistf_2: Hispanic Female column for rows 67-70 (part-time)
  - brest_2: Other demographic columns for rows 67-70 (part-time)
  - btotal_2: Row sum column for rows 67-70 (part-time)
  - bhistm_3: Hispanic Male column for row 71 (part-time administrative)
  - bhistf_3: Hispanic Female column for row 71 (part-time administrative)
  - brest_3: Other demographic columns for row 71 (part-time administrative)
  - btotal_3: Row sum column for row 71 (part-time administrative)
  - bhistm_4: Hispanic Male column for row 72 (part-time skilled craft)
  - bhistf_4: Hispanic Female column for row 72 (part-time skilled craft)
  - brest_4: Other demographic columns for row 72 (part-time skilled craft)
  - btotal_4: Row sum column for row 72 (part-time skilled craft)
  - bhistm_5: Hispanic Male column for row 73 (part-time maintenance)
  - bhistf_5: Hispanic Female column for row 73 (part-time maintenance)
  - brest_5: Other demographic columns for row 73 (part-time maintenance)
  - btotal_5: Row sum column for row 73 (part-time maintenance)
  - bhistm_total: Hispanic Male column for row 74 (part-time total)
  - bhistf_total: Hispanic Female column for row 74 (part-time total)
  - brest_total: Other demographic columns for row 74 (part-time total)
  - btotal_total: Row sum column for row 74 (part-time total)
- table3:
  - chistm_1: Hispanic Male column for row 75 (new hire officials)
  - chistf_1: Hispanic Female column for row 75 (new hire officials)
  - crest_1: Other demographic columns for row 75 (new hire officials)
  - ctotal_1: Row sum column for row 75 (new hire officials)
  - chistm_2: Hispanic Male column for rows 76-79 (new hire)
  - chistf_2: Hispanic Female column for rows 76-79 (new hire)
  - crest_2: Other demographic columns for rows 76-79 (new hire)
  - ctotal_2: Row sum column for rows 76-79 (new hire)
  - chistm_3: Hispanic Male column for row 80 (new hire administrative)
  - chistf_3: Hispanic Female column for row 80 (new hire administrative)
  - crest_3: Other demographic columns for row 80 (new hire administrative)
  - ctotal_3: Row sum column for row 80 (new hire administrative)
  - chistm_4: Hispanic Male column for row 81 (new hire skilled craft)
  - chistf_4: Hispanic Female column for row 81 (new hire skilled craft)
  - crest_4: Other demographic columns for row 81 (new hire skilled craft)
  - ctotal_4: Row sum column for row 81 (new hire skilled craft)
  - chistm_5: Hispanic Male column for row 82 (new hire maintenance)
  - chistf_5: Hispanic Female column for row 82 (new hire maintenance)
  - crest_5: Other demographic columns for row 82 (new hire maintenance)
  - ctotal_5: Row sum column for row 82 (new hire maintenance)
  - chistm_total: Hispanic Male column for row 83 (new hire total)
  - chistf_total: Hispanic Female column for row 83 (new hire total)
  - crest_total: Other demographic columns for row 83 (new hire total)
  - ctotal_total: Row sum column for row 83 (new hire total)
</details>

### Step 2: eeo4_filter.py

Run:
```bash
cd postprocess
python3 eeo4_filter.py
```

```
Enter the input JSON directory: #ENTER PATH TO JSON FILES HERE
```

```
Enter the output JSON directory: #ENTER PATH TO OUTPUT COMBINED JSON FILE HERE
```

Inputs json files generated by run_pipeline.py.  Outputs a combined json file for each original pdf.

### Step 3: eeo4_handler.py

Edit line 15 to an input path for a combined json (ideally the output path used for eeo4_filter.py).
Edit line 16 to an output path for your csv.

```bash
cd ../../data_aggregation #if you're still in ocr/postprocess from step one
python3 eeo4_handler.py
```

Notes:
- eeo4_handler_dedup.py works the same way.
  - Edit lines 19 and 20 for an input and output directory and then run by calling python3 eeo4_handler_dedup.py.
  - It ignores the third table for new hires.
- eeo4_melt.py works the same way.
  - Edit lines 28 and 29 for an input and output directory and then run by calling python3 eeo4_melt.py.
  - This outputs multiple differentially private contingency tables rather than the flat table outputted by eeo4_handler.py.
- eeo4_melt_dedup.py works the same way.
  - Edit lines 31 and 32 for an input and output directory and then run by calling python3 eeo4_melt_dedup.py.
  - This outputs multiple differentially private contingency tables like eeo4_melt.py, but ignores the third table for new hires.
