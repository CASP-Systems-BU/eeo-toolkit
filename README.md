# OCR Pipeline for EEO-1 and EEO-5 PDF Files

A compliance automation toll for processing **EEO-1** and **EEO-5** PDF reports as required by 141 of the Acts of 2024
(*Massachusetts Salary Range Transparency Law*). Convert typed and scanned PDF documents into structured JSOn data with
automated OCR processing and workforce statistics aggregation.

## Table of content

## Features

This implementation provides:

- **PDF-to-JSON Conversion**: OCR pipeline for digitizing EEO reports.
- **Data Aggregation**: Workforce statistics and wage analysis.
- **Form Layout Configuration**: Allows customizable config for different layouts of EEO-1 and EEO-5 forms.

## Technical stacks

- **Programming language**: Python
- **OCR**: DocTR
- **Data aggregation**: Pandas
- **Data visualization**: Matplotlib

## Installation

1. Clone the repo
2. Create a new Python environment or use your existing environment:
    ```shell
    python3 -m venv myenv # Replace "myenv" with your env name
    source myenv/bin/activate
    ```
3. Install the Python dependencies:
    ```shell
    pip install -r requirements.txt
    ```
3. Deactivate the environments:
    ```shell
    deactivate
    ```

## Usage

### 1. Customize Configurable YAML files *(If Needed)*

In order to use the current OCR pipeline, you need to ensure you have both the correct coordination layout config files
and checkout box config files.
If not, you need to manually extract the upper-right-corner and bottom-left-corner coordination info of each cell to the
config file.

To extract the coordination, we provide you a GUI script: [OCR/get_location.py](OCR/visualization/get_location.py). Simply run
```python3 get_location.py```
to get the coordination.

Under [OCR/config](./OCR/config), we provided you some config files:

- **EEO-1:**
    - Type1 Cells: [eeo1_typed_type1.yaml](./OCR/config/eeo1_typed_type1.yaml)
    - Type1 Checkboxes: [eeo1_typed_type1_checkbox.yaml](./OCR/config/eeo1_typed_type1_checkbox.yaml)
    - Type2 Cells: [eeo1_typed_type2.yaml](./OCR/config/eeo1_typed_type2.yaml)
    - Type2 Checkboxes: [eeo1_typed_type2_checkbox.yaml](./OCR/config/eeo1_typed_type2_checkbox.yaml)
- **EEO-5:**
    - Cells: [eeo5_typed.yaml](./OCR/config/eeo5_typed.yaml)
    - Checkboxes: [eeo5_typed_checkbox.yaml](./OCR/config/eeo5_typed_checkbox.yaml)

When processing the data, our team noticed that EEO-1 forms has two different layouts.
These two schemas would be able to handle the most of the files. If you notice many invalid data in the
extracted json results, it might due to different form layouts.

Schema of the form cell coordination layout config file:

```yaml
section_name:
  CELL_NAME: !!python/tuple
    - "upper_right_corner_x_axis_value"
    - "upper_right_corner_y_axis_value"
    - "bottom_left_corner_x_axis_value"
    - "bottom_left_corner_y_axis_value"
```

Schema of the checkbox coordination config file:

```yaml
check_box_name: !!python/tuple
  - "upper_right_corner_x_axis_value"
  - "upper_right_corner_y_axis_value"
  - "bottom_left_corner_x_axis_value"
  - "bottom_left_corner_y_axis_value"
```

### 2. PDF File Pre-Processing *(Optionally)*

#### 1) Classification

The script [OCR/preprocess/classify.py](./OCR/preprocess/classify.py) allows you to classify submitted files by forms.

#### 2) Deduplication

The script [OCR/preprocess/deduplicate.py](./OCR/preprocess/deduplicate.py) is for the form deduplication. Our
approach for deduplication is to compute the hash of the form and compare.

#### 3) PDF layer rendering

We notice that a large proportion of the submitted PDF forms have the rendering issue in Python. The issue is the form
layout and the form input data are in different layouts, and the input data positions in the form are incorrect. Thus,
we provide you the script [OCR/preprocess/process_pdf.py](./OCR/preprocess/process_pdf.py) to fix the layer rendering
issue.

### 3. Run OCR Pipeline

Go to [OCR/run_pipeline.py](./OCR/run_pipeline.py). Make sure all the config variables, including paths, config files,
form types
are correct.

Then, run ```python3 run_pipeline.py``` to process PDF files into json outputs.

### 4. Data Aggregation

TODO