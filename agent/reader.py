"""
reader.py
---------
Reads documents (PDF, image, or plain text) and returns raw text content.

Supported formats:
- .pdf  → extracted using pdfplumber (preserves layout and tables)
- .txt  → read directly
- .png / .jpg / .jpeg → OCR using pytesseract
"""

import pdfplumber
import pytesseract
from PIL import Image
from pathlib import Path


def read_document(file_path: str) -> str:
    """
    Takes a file path and returns its text content as a string.
    Raises ValueError for unsupported file types.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _read_pdf(path)
    elif suffix == ".txt":
        return _read_text(path)
    elif suffix in [".png", ".jpg", ".jpeg"]:
        return _read_image(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use PDF, TXT, or image files.")


def _read_pdf(path: Path) -> str:
    """
    Extracts text from a PDF using pdfplumber.
    Handles multi-page PDFs by joining all pages.
    Also attempts to extract tables and append them as text.
    """
    extracted_text = []

    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Extract plain text
            text = page.extract_text()
            if text:
                extracted_text.append(f"--- Page {page_num} ---\n{text}")

            # Extract tables if present (invoices often have item tables)
            tables = page.extract_tables()
            for table in tables:
                table_text = _table_to_text(table)
                if table_text:
                    extracted_text.append(f"[TABLE]\n{table_text}\n[/TABLE]")

    if not extracted_text:
        raise ValueError("No text could be extracted from this PDF. It may be scanned — try using an image instead.")

    return "\n\n".join(extracted_text)


def _read_text(path: Path) -> str:
    """Reads a plain .txt file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _read_image(path: Path) -> str:
    """
    Uses pytesseract OCR to extract text from an image.
    Requires tesseract to be installed on the system.
    """
    try:
        image = Image.open(path)
        text = pytesseract.image_to_string(image)
        if not text.strip():
            raise ValueError("OCR returned no text. The image may be too low quality.")
        return text
    except Exception as e:
        raise RuntimeError(f"Image OCR failed: {e}\nMake sure tesseract is installed: https://github.com/tesseract-ocr/tesseract")


def _table_to_text(table: list) -> str:
    """Converts a pdfplumber table (list of lists) to readable text."""
    if not table:
        return ""
    rows = []
    for row in table:
        # Filter None cells
        cleaned = [str(cell).strip() if cell else "" for cell in row]
        rows.append(" | ".join(cleaned))
    return "\n".join(rows)