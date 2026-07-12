"""
extractor.py - Core LLM extraction logic with Groq.
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

SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
SYSTEM_PROMPT = open(SYSTEM_PROMPT_PATH).read() if SYSTEM_PROMPT_PATH.exists() else "Extract document data and return JSON only."
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def extract_document(file_path: str) -> ExtractedDocument:
    print(f"📄 Reading document: {file_path}")
    raw_text = read_document(file_path)
    print(f"✅ Extracted {len(raw_text)} characters of text")
    print("🤖 Sending to Groq LLM for extraction...")
    raw_json_str = _call_groq(raw_text)
    print("🔍 Parsing JSON response...")
    raw_dict = _parse_json(raw_json_str)
    print("✅ Validating extracted fields...")
    return validate_extraction(raw_dict)


def _call_groq(document_text: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not found in .env file.")

    client = Groq(api_key=api_key, http_client=httpx.Client(verify=True))

    if len(document_text) > 5000:
        print("⚠ Document truncated to 5000 chars.")
        document_text = document_text[:5000]

    user_message = f"""You are extracting data from a financial document.
Return ONLY a JSON object. No explanation. No markdown.

DOCUMENT TEXT:
==============
{document_text}
==============

RULES:
1. vendor must be a JSON object with keys: name, address, contact, gstin
2. buyer must be a JSON object with keys: name, address, gstin
3. line_items must be a list of objects each with: description, quantity, unit_price, total
4. description in line_items must be the ACTUAL product name (e.g. "Amul Butter 500g")
5. NEVER use string values for vendor or buyer - always use JSON objects
6. tax = CGST + SGST combined
7. Remove commas from all numbers
8. document_type = "invoice" or "receipt" or "purchase_order"

Return JSON starting with {{ and ending with }}
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
    return response.choices[0].message.content.strip()


def _parse_json(raw_str: str) -> dict:
    cleaned = raw_str.strip()
    if "```" in cleaned:
        lines = [l for l in cleaned.split("\n") if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM.\nError: {e}\nResponse: {raw_str[:500]}")


def save_result(result: ExtractedDocument, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"💾 Result saved to: {output_path}")
