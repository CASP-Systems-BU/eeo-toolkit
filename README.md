# **README**
# Add names and links
## **1. Introduction**

This is a library for processing scanned or digital EEO-1 and EEO-5 PDF reports as required by 141 of the Acts of 2024 (Massachusetts Salary Range Transparency Law).

The repository also includes tools for post-processing, data aggregation and analysis of the extracted data.

The repository provides custom parsing logic for different form types (e.g., EEO-1, EEO-5). This reduced parsing errors and improved extraction accuracy.

---

## **2. Library Overview**


The pipeline processes EEO-1 and EEO-5 forms (PDF or images) in batches and includes the following stages:

1.**Preprocessing** – Enhances image quality for improved OCR performance.  
2.**Optical Character Recognition** – Extracts text using a deep learning-based OCR engine.  
3.**Postprocessing & Parsing** – Segments content into structured fields.  
4.**Validation & Cleaning** – Validates extracted data (e.g., zip codes, city names) against public datasets.  
5.**Aggregation & Analysis** – Groups, aggregates, and exports data for reporting.


### **Pipeline Components**

| Component           | Tool Used   | Description                                                    |
| ------------------- |-------------|----------------------------------------------------------------|
| Image Preprocessing | OpenCV, PIL | Deduplication, formatting, scaling, padding                    |
| OCR Engine          | DocTR       | Handwritten and printed text recognition                       |
| Postprocessing      | Python      | Field extraction, form segmentation, validation and correction |
| Data Aggregation    | Pandas      | CSV/JSON parsing, group-by, statistical summaries              |


Each component is built as an independent, reusable module, facilitating extensibility and debugging.


---

## **3. How to Run the Pipeline**

### **3.1 Requirements**

- Ubuntu 22.04.5 LTS
- Python ≥ 3.10.12
- Dependencies listed in `requirements.txt`  
- Offline OCR models downloaded and stored locally  

### **3.2 Steps**
1. **Clone the repository**

    ```bash
   git clone
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **(Optional) Deactivate** when done:
   ```bash
   deactivate
   ```

---

## **4. OCR Tools Explored**


The entire pipeline is designed to run in an air-gapped environment. All models and tools used are available offline after the initial setup.


For the purpose of this project, we explored 3 different OCR tools: Tesseract, Nougat and DocTR.

| OCR Engine | Accuracy                                                                                                             | Support Complex Layout | Support Handwritten Forms |                Comments                                             |
|------------|----------------------------------------------------------------------------------------------------------------------|------------------------|---------------------------|---------------------------------------------------------------------|
| Tesseract  | Lightweight; supports traditional (non-ML) OCR methods; high throughput                                              | -                      |                           | Cannot distinguish form borders and handle complex layouts          |
| Donut      | High accuracy on scientific documents                                                                                | -                      |                           | Heavy dependencies and large model footprint; Require self-training |
| DocTR      | High accuracy across varied document types; handles complex layouts (tables, columns); built-in multilingual support | -                      |                           |  No good support for handle handwritten forms;                      |


---


## **5. Limitations and Challenges**

- **Handwritten data variability** – Especially problematic with cursive or non-standard characters

---

## **6. Ongoing Work**

- Integrate a layout detection model for dynamic form segmentation  
- Expand support for additional form types and formats  
- Train a custom OCR model fine-tuned on EEO forms  
- Build an interactive viewer for browsing OCR results

