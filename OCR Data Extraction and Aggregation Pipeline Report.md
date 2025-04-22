# **OCR Data Extraction and Aggregation Pipeline Report**

## **1. Introduction**

This report outlines the development and implementation of an OCR (Optical Character Recognition) pipeline for processing structured and semi-structured form data. The primary objective was to extract key data fields from scanned or digital forms and perform downstream aggregation and analysis.

---

## **2. System Design**

### **2.1 Overview**

The system processes batches of form documents (PDF or image-based) through the following stages:

1. **Input Handling** – Accepts scanned PDFs or image files.  
2. **Preprocessing** – Enhances image quality for improved OCR performance.  
3. **OCR Processing** – Extracts text using a deep learning-based OCR engine.  
4. **Postprocessing & Parsing** – Segments recognized content into structured fields.  
5. **Validation & Cleaning** – Validates extracted data (e.g., zip codes, city names) against reference lists.  
6. **Aggregation & Analysis** – Groups, summarizes, and exports data for reporting. 


### **2.2 OCR Engine Selection**

We did some researches on 3 different OCR engines: Tesseract, Nougat and DocTR.

### **2.3 Pipeline Components**

| Component           | Technology Used            | Description                                    |
|---------------------|-----------------------------|------------------------------------------------|
| Image Preprocessing | OpenCV, PIL                 | Binarization, scaling, padding                |
| OCR Engine          | DocTR / TrOCR / Tesseract   | Handwritten and printed text recognition       |
| Postprocessing      | Custom Python scripts       | Field extraction, form segmentation            |
| Data Aggregation    | pandas                      | CSV/JSON parsing, groupby, statistical summaries |
| Validation          | Reference lookups, fuzzy matching | Ensures consistent location names and identifiers |

---

## **3. Design Decisions**

### **3.1 Offline Capability**

Given privacy constraints, the entire pipeline was designed to run in a secure, air-gapped environment. All models and tools used are available offline after initial setup.

### **3.2 Choice of OCR Engine**

Several OCR solutions were evaluated. Deep learning-based engines (e.g., TrOCR) outperformed traditional engines on handwritten inputs. However, fallback options like Tesseract were retained for robustness.

### **3.3 Form-Specific Tuning**

Form layouts were manually reviewed to build custom parsing logic for different form types (e.g., EEO-1, EEO-5). This reduced parsing errors and improved extraction accuracy.

### **3.4 Modular Architecture**

Each stage of the pipeline was built as an independent, reusable module, allowing for easier debugging, parallelization, and future upgrades.

---

## **4. How to Run the Pipeline**

### **4.1 Requirements**

- Python ≥ 3.8  
- Dependencies listed in `requirements.txt`  
- Offline OCR models downloaded and stored locally  

### **4.2 Steps**

```bash
# 1. Set up virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Place input PDFs in `input/` directory

# 3. Run the pipeline
python run_pipeline.py --input_dir input/ --output_dir output/ --log log.txt

# 4. Output includes:
#    - JSON files per form
#    - Aggregated CSV tables
#    - Logs for traceability
```

### **4.3 Configuration**

Parameters (e.g., page scaling, noise thresholds, model paths) can be edited in `config.yaml`.

---

## **5. Evaluation**

The pipeline was tested on a sample of **[X]** forms with varying quality and layout. Key findings:

- Average field-level accuracy: **[e.g., 92.5%]**
- Aggregation consistency across batches verified
- OCR accuracy reduced on extremely faint or low-resolution scans

---

## **6. Limitations and Challenges**

- **Handwritten data variability** – Especially problematic with cursive or non-standard characters  
- **Form layout shifts** – Misalignment between scanned templates required layout-aware logic  
- **Zip-to-county mapping** – Incomplete coverage in reference data introduced edge-case handling

---

## **7. Future Work**

- Integrate a layout detection model for dynamic form segmentation  
- Expand support for additional form types and formats  
- Train a custom OCR model fine-tuned on our own dataset  
- Build a small web-based viewer for reviewing and correcting OCR results

---

## **8. Conclusion**

The pipeline successfully automates the extraction and aggregation of key information from structured and semi-structured forms. With modular components, offline support, and customizable validation, it forms a robust foundation for further enhancements.
