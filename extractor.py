"""
extractor.py
------------
Core extraction logic using Groq LLM.
"""

import os
import json
import httpx
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

from agent.reader import read_document
from agent.validator import validate_extraction, ExtractedDocument

load_dotenv()

# Load system prompt
SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
if SYSTEM_PROMPT_PATH.exists():
    with open(SYSTEM_PROMPT_PATH, "r") as f:
        SYSTEM_PROMPT = f.read()
else:
    SYSTEM_PROMPT = "Extract document data and return JSON only."

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def extract_document(file_path: str) -> ExtractedDocument:
    """Main entry point — reads file, calls LLM, validates output."""

    print(f"📄 Reading document: {file_path}")
    raw_text = read_document(file_path)
    print(f"✅ Extracted {len(raw_text)} characters of text")

    print("🤖 Sending to Groq LLM for extraction...")
    raw_json_str = _call_groq(raw_text)

    print("🔍 Parsing JSON response...")
    raw_dict = _parse_json(raw_json_str)

    print("✅ Validating extracted fields...")
    result = validate_extraction(raw_dict)

    return result


def _call_groq(document_text: str) -> str:
    """Calls Groq API with document text and returns raw JSON string."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not found in .env file.")

    # Fix for httpx proxies issue on Mac
    http_client = httpx.Client(verify=True)
    client = Groq(api_key=api_key, http_client=http_client)

    # Truncate if too long
    max_chars = 5000
    if len(document_text) > max_chars:
        print(f"⚠ Document truncated to {max_chars} chars.")
        document_text = document_text[:max_chars]

    user_message = f"""Extract all data from this document and return JSON only.

DOCUMENT:
=========
{document_text}
=========

Remember:
- Return ONLY the JSON object starting with {{ and ending with }}
- Use actual product/item names in line_items descriptions, never "Unknown Item"
- Vendor name is the seller/shop name at the top of the document
- Add CGST + SGST together for the tax field
- Remove commas from all numbers
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        max_tokens=2048,
    )

    raw = response.choices[0].message.content.strip()
    return raw


def _parse_json(raw_str: str) -> dict:
    """Safely parses LLM response into a Python dict."""

    cleaned = raw_str.strip()

    # Strip markdown code blocks if present
    if "```" in cleaned:
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    # Find JSON object boundaries
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned invalid JSON.\nError: {e}\n"
            f"Raw response (first 500 chars):\n{raw_str[:500]}"
        )


def save_result(result: ExtractedDocument, output_path: str):
    """Saves extraction result to JSON file."""
    output_dict = result.model_dump()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=2, ensure_ascii=False)
    print(f"💾 Result saved to: {output_path}")