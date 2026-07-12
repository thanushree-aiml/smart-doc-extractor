"""
validator.py
------------
Pydantic schemas with defensive handling for missing/malformed LLM output.
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
        if str(v).lower() not in allowed:
            return "invoice"
        return str(v).lower()

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"]:
            try:
                parsed = datetime.strptime(str(v), fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return str(v)

    @model_validator(mode="after")
    def run_sanity_checks(self):
        warnings = []
        tolerance = 2.0

        if self.line_items and self.subtotal is not None:
            computed_sum = sum(
                item.total for item in self.line_items
                if item.total is not None
            )
            if computed_sum > 0:
                diff = abs(computed_sum - self.subtotal)
                if diff > tolerance:
                    warnings.append(
                        f"⚠ Line items sum ({computed_sum:.2f}) does not match subtotal ({self.subtotal:.2f}). Difference: {diff:.2f}"
                    )

        if self.subtotal is not None and self.total is not None:
            tax_amount = self.tax or 0.0
            expected_total = round(self.subtotal + tax_amount, 2)
            diff = abs(expected_total - self.total)
            if diff > tolerance:
                warnings.append(
                    f"⚠ Subtotal ({self.subtotal}) + Tax ({tax_amount}) = {expected_total}, but total is {self.total}. Difference: {diff:.2f}"
                )

        if self.total is not None and len(self.line_items) == 0:
            warnings.append("⚠ Total found but no line items extracted.")

        if self.vendor is None or self.vendor.name is None:
            warnings.append("⚠ Vendor name could not be extracted.")

        self.validation_warnings = warnings
        return self


def validate_extraction(raw_dict: dict) -> ExtractedDocument:
    """
    Safely converts raw LLM dict into validated ExtractedDocument.
    Handles missing, null, or malformed fields defensively.
    """

    # Safely handle vendor
    vendor_raw = raw_dict.get("vendor")
    if isinstance(vendor_raw, dict):
        raw_dict["vendor"] = VendorInfo(**{
            k: v for k, v in vendor_raw.items()
            if k in VendorInfo.model_fields
        })
    elif vendor_raw is None:
        raw_dict["vendor"] = None

    # Safely handle buyer
    buyer_raw = raw_dict.get("buyer")
    if isinstance(buyer_raw, dict):
        raw_dict["buyer"] = BuyerInfo(**{
            k: v for k, v in buyer_raw.items()
            if k in BuyerInfo.model_fields
        })
    elif buyer_raw is None:
        raw_dict["buyer"] = None

    # Safely handle line_items — most common source of crashes
    line_items_raw = raw_dict.get("line_items", [])
    safe_line_items = []

    if isinstance(line_items_raw, list):
        for item in line_items_raw:
            if isinstance(item, dict):
                # Ensure description always exists
                if not item.get("description"):
                    item["description"] = "Unknown Item"
                # Convert string numbers to float safely
                for field in ["quantity", "unit_price", "total"]:
                    val = item.get(field)
                    if val is not None:
                        try:
                            # Remove commas from numbers like "1,10,000"
                            item[field] = float(str(val).replace(",", ""))
                        except (ValueError, TypeError):
                            item[field] = None
                safe_line_items.append(LineItem(**{
                    k: v for k, v in item.items()
                    if k in LineItem.model_fields
                }))

    raw_dict["line_items"] = safe_line_items

    # Convert numeric fields safely
    for field in ["subtotal", "tax", "tax_rate_percent", "total"]:
        val = raw_dict.get(field)
        if val is not None:
            try:
                raw_dict[field] = float(str(val).replace(",", ""))
            except (ValueError, TypeError):
                raw_dict[field] = None

    # Remove unknown fields to avoid Pydantic errors
    known_fields = set(ExtractedDocument.model_fields.keys())
    raw_dict = {k: v for k, v in raw_dict.items() if k in known_fields}

    return ExtractedDocument(**raw_dict)