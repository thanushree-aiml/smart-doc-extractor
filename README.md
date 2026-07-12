# 📄 Document Data Extractor Agent

An AI-powered agent that extracts structured JSON from messy financial documents — invoices, receipts, and purchase orders — with automatic sanity checks and validation.

Built for the **Rooman AI Challenge — 24-Hour AI Agent Challenge**

---

## What It Does

- Reads PDF, TXT, or image documents
- Extracts key fields: vendor, buyer, line items, totals, dates, GST, payment method
- Validates the output using Pydantic schemas
- Runs automatic sanity checks (line items sum, subtotal + tax = total, date format)
- Outputs clean, structured JSON
- Works across multiple document layouts (invoice, receipt, purchase order)

---

## Tech Stack

| Component | Tool |
|---|---|
| LLM | Groq API (llama3-70b-8192) |
| PDF Reading | pdfplumber |
| Image OCR | pytesseract |
| Validation | Pydantic v2 |
| CLI Display | Rich |
| Environment | python-dotenv |

---

## Project Structure

```
document-data-extractor/
├── main.py                    # CLI entry point
├── agent/
│   ├── extractor.py           # Core LLM extraction logic
│   ├── validator.py           # Pydantic schemas + sanity checks
│   └── reader.py              # PDF / image / text reader
├── prompts/
│   └── system_prompt.txt      # LLM instructions
├── samples/
│   ├── invoice_1.txt          # Sample GST invoice
│   ├── receipt_1.txt          # Sample supermarket receipt
│   ├── purchase_order_1.txt   # Sample purchase order
│   └── outputs/               # Extracted JSON results
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/thanushreevn/document-data-extractor.git
cd document-data-extractor
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a Groq API key

- Sign up free at [console.groq.com](https://console.groq.com)
- Create an API key

### 5. Configure environment

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

---

## Running the Agent

### Process a single file

```bash
python main.py --file samples/invoice_1.txt
python main.py --file samples/receipt_1.txt
python main.py --file samples/purchase_order_1.txt
```

### Run on all sample files at once

```bash
python main.py --demo
```

### Process your own document

```bash
python main.py --file path/to/your/document.pdf
```

---

## Sample Output

### Input: `invoice_1.txt` (GST Invoice)

```json
{
  "document_type": "invoice",
  "document_id": "INV-2024-00892",
  "date": "2024-03-15",
  "vendor": {
    "name": "TechSupply Pvt. Ltd.",
    "address": "42, Electronics Complex, Phase 2, Bengaluru - 560100, Karnataka",
    "contact": "+91-80-4567-8901",
    "gstin": "29AABCT1234A1Z5"
  },
  "buyer": {
    "name": "Infovision Systems Pvt. Ltd.",
    "address": "18, MG Road, Bengaluru - 560001",
    "gstin": "29AACFI5678B1Z3"
  },
  "line_items": [
    { "description": "Laptop - Dell Inspiron", "quantity": 2, "unit_price": 55000.0, "total": 110000.0 },
    { "description": "Wireless Mouse (Logitech)", "quantity": 5, "unit_price": 1200.0, "total": 6000.0 },
    { "description": "USB-C Hub (7-port)", "quantity": 3, "unit_price": 2500.0, "total": 7500.0 },
    { "description": "HDMI Cable 2m", "quantity": 10, "unit_price": 350.0, "total": 3500.0 },
    { "description": "Laptop Bag (15.6 inch)", "quantity": 2, "unit_price": 1800.0, "total": 3600.0 }
  ],
  "subtotal": 130600.0,
  "tax": 23508.0,
  "tax_rate_percent": 18.0,
  "total": 154108.0,
  "currency": "INR",
  "payment_method": "Bank Transfer (NEFT)",
  "validation_warnings": []
}
```

---

## Sanity Checks

The agent automatically validates:

| Check | What It Does |
|---|---|
| Line items sum | Sum of all item totals must ≈ subtotal (±₹2 tolerance) |
| Total check | Subtotal + tax must ≈ total (±₹2 tolerance) |
| Date format | Normalizes all dates to ISO format (YYYY-MM-DD) |
| Document type | Must be one of: invoice, receipt, purchase_order |
| Vendor presence | Warns if vendor name not found |
| Empty line items | Warns if total exists but no items extracted |

---

## Design Decisions & Tradeoffs

### Why Groq + llama3-70b?
- Free tier with generous rate limits — ideal for a 24-hour challenge
- llama3-70b is strong at structured extraction tasks with zero-shot prompting
- Low latency (~1–2s per document) vs OpenAI GPT-4

### Why pdfplumber over PyPDF2?
- pdfplumber preserves table structure — critical for line-item extraction in invoices
- PyPDF2 often merges table columns into a single jumbled string

### Why Pydantic v2?
- Type-safe schema definition with automatic coercion
- `@model_validator` enables cross-field sanity checks in one place
- Cleaner than manual dict validation

### Why temperature=0.0?
- Extraction is a deterministic task — we want consistent, reproducible outputs
- Higher temperature introduces unnecessary randomness in field values

### Limitations
- **Scanned PDFs**: pdfplumber cannot read image-based (scanned) PDFs — requires pytesseract OCR, which depends on Tesseract being installed
- **Context window**: llama3-70b has an 8192 token limit; very long multi-page documents are truncated
- **Complex layouts**: Highly stylized or multi-column PDF layouts may not extract cleanly
- **Currency detection**: Defaults to INR; international documents may need manual currency hints

### What I'd Add with More Time
- Vision model support (Claude claude-sonnet-4-6 or GPT-4V) for scanned/image PDFs
- Confidence score per extracted field
- A simple Streamlit or FastAPI UI for drag-and-drop document upload
- Batch processing with a summary CSV of all extractions
- Unit tests for each validator and sanity check

---

## Author

**Thanushree V N**
B.E. in Artificial Intelligence & Machine Learning (VTU, 2026)
# smart-doc-extractor
