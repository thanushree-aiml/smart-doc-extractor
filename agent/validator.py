"""
validator.py - Defensive Pydantic schemas that handle any LLM output format.
"""

from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional
from datetime import datetime


class VendorInfo(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    gstin: Optional[str] = None


class BuyerInfo(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None


class LineItem(BaseModel):
    description: Optional[str] = "Unknown Item"
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class ExtractedDocument(BaseModel):
    document_type: Optional[str] = "invoice"
    document_id: Optional[str] = None
    date: Optional[str] = None
    vendor: Optional[VendorInfo] = None
    buyer: Optional[BuyerInfo] = None
    line_items: List[LineItem] = []
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    tax_rate_percent: Optional[float] = None
    total: Optional[float] = None
    currency: str = "INR"
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    validation_warnings: List[str] = []

    @field_validator("document_type", mode="before")
    @classmethod
    def validate_document_type(cls, v):
        if v is None:
            return "invoice"
        allowed = {"invoice", "receipt", "purchase_order"}
        cleaned = str(v).lower().strip()
        return cleaned if cleaned in allowed else "invoice"

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"]:
            try:
                return datetime.strptime(str(v), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return str(v)

    @model_validator(mode="after")
    def run_sanity_checks(self):
        warnings = []
        tolerance = 2.0

        if self.line_items and self.subtotal is not None:
            computed = sum(i.total for i in self.line_items if i.total is not None)
            if computed > 0 and abs(computed - self.subtotal) > tolerance:
                warnings.append(f"⚠ Line items sum ({computed:.2f}) != subtotal ({self.subtotal:.2f})")

        if self.subtotal is not None and self.total is not None:
            expected = round(self.subtotal + (self.tax or 0.0), 2)
            if abs(expected - self.total) > tolerance:
                warnings.append(f"⚠ Subtotal ({self.subtotal}) + Tax ({self.tax or 0}) = {expected}, but total is {self.total}")

        if self.total is not None and len(self.line_items) == 0:
            warnings.append("⚠ Total found but no line items extracted.")

        if self.vendor is None or self.vendor.name is None:
            warnings.append("⚠ Vendor name could not be extracted.")

        self.validation_warnings = warnings
        return self


def _to_float(val) -> Optional[float]:
    """Safely convert any value to float, removing commas."""
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def validate_extraction(raw_dict: dict) -> ExtractedDocument:
    """
    Converts raw LLM dict into validated ExtractedDocument.
    Handles ALL edge cases: string vendor, missing fields, wrong types.
    """

    # Fix vendor — LLM sometimes returns a string instead of a dict
    vendor_raw = raw_dict.get("vendor")
    if isinstance(vendor_raw, str):
        raw_dict["vendor"] = VendorInfo(name=vendor_raw)
    elif isinstance(vendor_raw, dict):
        raw_dict["vendor"] = VendorInfo(
            name=vendor_raw.get("name"),
            address=vendor_raw.get("address"),
            contact=vendor_raw.get("contact"),
            gstin=vendor_raw.get("gstin"),
        )
    else:
        raw_dict["vendor"] = None

    # Fix buyer — same issue
    buyer_raw = raw_dict.get("buyer")
    if isinstance(buyer_raw, str):
        raw_dict["buyer"] = BuyerInfo(name=buyer_raw)
    elif isinstance(buyer_raw, dict):
        raw_dict["buyer"] = BuyerInfo(
            name=buyer_raw.get("name"),
            address=buyer_raw.get("address"),
            gstin=buyer_raw.get("gstin"),
        )
    else:
        raw_dict["buyer"] = None

    # Fix line_items — handle all possible formats
    line_items_raw = raw_dict.get("line_items", [])
    safe_items = []

    if isinstance(line_items_raw, list):
        for item in line_items_raw:
            if isinstance(item, dict):
                # Get description from multiple possible keys
                desc = (
                    item.get("description")
                    or item.get("name")
                    or item.get("item")
                    or item.get("product")
                    or "Unknown Item"
                )
                safe_items.append(LineItem(
                    description=str(desc).strip() if desc else "Unknown Item",
                    quantity=_to_float(item.get("quantity") or item.get("qty")),
                    unit_price=_to_float(item.get("unit_price") or item.get("price") or item.get("rate")),
                    total=_to_float(item.get("total") or item.get("amount") or item.get("line_total")),
                ))
            elif isinstance(item, str):
                safe_items.append(LineItem(description=item))

    raw_dict["line_items"] = safe_items

    # Fix all numeric fields
    for field in ["subtotal", "tax", "tax_rate_percent", "total"]:
        raw_dict[field] = _to_float(raw_dict.get(field))

    # Remove unknown fields
    known = set(ExtractedDocument.model_fields.keys())
    raw_dict = {k: v for k, v in raw_dict.items() if k in known}

    return ExtractedDocument(**raw_dict)
