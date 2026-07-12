# Smart Document Extractor Agent

An AI-powered document extraction system that converts unstructured financial documents into structured JSON using Large Language Models (LLMs). The application supports invoices, receipts, and purchase orders while performing schema validation and financial sanity checks to improve the reliability and consistency of extracted data.

Developed as part of the **Rooman AI Challenge – 24-Hour AI Agent Challenge**.

---

# Table of Contents

- Overview
- Features
- System Architecture
- Technology Stack
- Project Structure
- Installation
- Configuration
- Usage
- Sample Output
- Validation
- Design Decisions
- Limitations
- Future Improvements
- Requirements
- Author
- License

---

# Overview

The Smart Document Extractor Agent automates the extraction of structured information from financial documents. Instead of manually parsing invoices, receipts, or purchase orders, the system leverages an LLM to identify important business fields and returns standardized JSON output suitable for downstream processing.

The extracted output is validated using Pydantic models, followed by sanity checks to ensure numerical consistency and data integrity.

---

# Features

- Extracts structured information from invoices, receipts, and purchase orders
- Supports text files, PDF documents, and image-based documents
- Converts unstructured document content into structured JSON
- Performs schema validation using Pydantic
- Executes automatic financial sanity checks
- Normalizes dates into ISO format (`YYYY-MM-DD`)
- Detects missing mandatory fields
- Identifies inconsistencies in extracted totals
- Command-line interface for processing individual or multiple documents

---

# System Architecture

```
Input Document
        │
        ▼
Document Reader
(Text / PDF / OCR)
        │
        ▼
LLM Extraction Engine
(Groq Llama 3)
        │
        ▼
Schema Validation
(Pydantic)
        │
        ▼
Sanity Checks
        │
        ▼
Structured JSON Output
```

---

# Technology Stack

| Category | Technology |
|----------|------------|
| Programming Language | Python 3.12+ |
| Large Language Model | Groq API (Llama 3 70B 8192) |
| PDF Processing | pdfplumber |
| OCR | pytesseract |
| Data Validation | Pydantic v2 |
| CLI Interface | Rich |
| Environment Management | python-dotenv |

---

# Project Structure

```
smart-doc-extractor/
│
├── agent/
│   ├── extractor.py
│   ├── reader.py
│   └── validator.py
│
├── prompts/
│   └── system_prompt.txt
│
├── samples/
│   ├── invoice_1.txt
│   ├── receipt_1.txt
│   ├── purchase_order_1.txt
│   └── outputs/
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

# Installation

## Clone the Repository

```bash
git clone https://github.com/thanushree-aiml/smart-doc-extractor.git
cd smart-doc-extractor
```

## Create a Virtual Environment

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Configuration

Create a `.env` file in the project root directory.

```env
GROQ_API_KEY=your_groq_api_key
```

The `.env` file is excluded from version control through `.gitignore` and should never be committed to the repository.

---

# Usage

## Process a Single Document

```bash
python main.py --file samples/invoice_1.txt
```

```bash
python main.py --file samples/receipt_1.txt
```

```bash
python main.py --file samples/purchase_order_1.txt
```

## Process All Sample Documents

```bash
python main.py --demo
```

## Process a Custom Document

```bash
python main.py --file path/to/document.pdf
```

---

# Supported Document Types

- Invoice
- Receipt
- Purchase Order

The system can be extended to support additional document formats by introducing new validation schemas and prompt instructions.

---

# Sample Output

```json
{
  "document_type": "invoice",
  "document_id": "INV-2024-00892",
  "date": "2024-03-15",
  "vendor": {
    "name": "TechSupply Pvt. Ltd.",
    "gstin": "29AABCT1234A1Z5"
  },
  "buyer": {
    "name": "Infovision Systems Pvt. Ltd."
  },
  "subtotal": 130600.0,
  "tax": 23508.0,
  "total": 154108.0,
  "currency": "INR",
  "validation_warnings": []
}
```

---

# Validation

The application performs multiple validation and consistency checks before producing the final output.

| Validation | Description |
|------------|-------------|
| Schema Validation | Ensures extracted fields conform to the defined Pydantic model |
| Line Item Validation | Confirms that the sum of all line items matches the subtotal |
| Total Validation | Verifies that subtotal plus tax equals the final total |
| Date Normalization | Converts dates into ISO (`YYYY-MM-DD`) format |
| Required Field Validation | Detects missing vendor or document information |
| Document Type Validation | Restricts output to supported document categories |
| Empty Line Item Detection | Warns when totals exist but no line items are extracted |

---

# Design Decisions

## Large Language Model

The project uses **Groq's Llama 3 70B** model because it provides fast inference, strong zero-shot extraction capabilities, and a generous developer tier suitable for rapid prototyping.

## PDF Processing

`pdfplumber` was selected because it preserves table structures significantly better than traditional PDF parsing libraries, improving invoice line-item extraction.

## Data Validation

Pydantic v2 provides structured schema validation, automatic type conversion, and cross-field validation, reducing the need for manual validation logic.

## Deterministic Generation

The model operates with a temperature of **0.0** to ensure deterministic and reproducible extraction results.

---

# Limitations

- OCR accuracy depends on the quality of scanned documents.
- Very large documents may exceed the model's context window.
- Complex multi-column layouts may require additional preprocessing.
- Currency detection currently defaults to INR.

---

# Future Improvements

- Vision-language model support for scanned documents
- Confidence scores for extracted fields
- FastAPI REST API
- Streamlit-based web interface
- Batch processing for multiple documents
- Comprehensive unit and integration tests
- Docker support
- GitHub Actions CI/CD pipeline

---

# Requirements

- Python 3.12 or later
- Groq API Key
- Tesseract OCR (required for image-based documents)

Install all dependencies using:

```bash
pip install -r requirements.txt
```

---

# Author

**Thanushree V N**

Bachelor of Engineering in Artificial Intelligence and Machine Learning (VTU)

GitHub: https://github.com/thanushree-aiml

---

# License

This project is intended for educational, research, and demonstration purposes.
