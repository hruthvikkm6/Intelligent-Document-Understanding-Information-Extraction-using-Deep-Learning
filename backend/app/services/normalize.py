import re
from decimal import Decimal, InvalidOperation
from typing import Any

from dateutil import parser as date_parser


def parse_amount(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("−", "-")
    if not text:
        return None
    negative = text.startswith("(") and text.endswith(")")
    cleaned = re.sub(r"[^0-9,.-]", "", text.strip("()"))
    if not cleaned or not re.search(r"\d", cleaned):
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = (
            cleaned.replace(",", "")
            if cleaned.rfind(".") > cleaned.rfind(",")
            else cleaned.replace(".", "").replace(",", ".")
        )
    elif "," in cleaned:
        tail = cleaned.rsplit(",", 1)[-1]
        cleaned = cleaned.replace(",", ".") if len(tail) in (1, 2) else cleaned.replace(",", "")
    try:
        result = Decimal(cleaned)
        if negative:
            result = -result
        return float(result)
    except InvalidOperation:
        return None


def normalize_date(value: Any) -> str | None:
    if not value:
        return None
    try:
        if isinstance(value, dict):
            year, month, day = value.get("year"), value.get("month"), value.get("day")
            if year and month and day:
                value = f"{year}-{int(month):02d}-{int(day):02d}"
        return date_parser.parse(str(value), dayfirst=False, fuzzy=False).date().isoformat()
    except (ValueError, OverflowError, TypeError):
        return None


def find_field(tree: Any, aliases: set[str]) -> Any:
    if isinstance(tree, dict):
        for key, value in tree.items():
            if re.sub(r"[^a-z0-9]", "", str(key).lower()) in aliases:
                if isinstance(value, dict) and "text" in value:
                    return value["text"]
                if isinstance(value, dict):
                    nested = find_field(value, aliases)
                    return nested if nested is not None else value
                return value
        for value in tree.values():
            found = find_field(value, aliases)
            if found is not None:
                return found
    elif isinstance(tree, list):
        for value in tree:
            found = find_field(value, aliases)
            if found is not None:
                return found
    return None


def normalize_line_items(tree: Any) -> list[dict] | None:
    if not isinstance(tree, dict):
        return None
    items = tree.get("menu") or tree.get("items") or tree.get("line_items")
    if not isinstance(items, list):
        return None
    normalized = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(
                {
                    "description": item.get("nm") or item.get("name") or item.get("description"),
                    "quantity": parse_amount(
                        item.get("cnt") or item.get("quantity") or item.get("qty")
                    ),
                    "unit_price": parse_amount(item.get("unitprice") or item.get("unit_price")),
                    "amount": parse_amount(item.get("price") or item.get("amount")),
                }
            )
    return normalized or None


_DATE_TOKEN = r"(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})"
_AMOUNT_TOKEN = r"(?:₹|INR|Rs\.?|USD|\$|EUR|€|GBP|£)?\s*([0-9][0-9,]*(?:\.\d{1,2})?)"


def looks_like_invoice(text: str) -> bool:
    """Conservative OCR text gate; this is routing logic, not an ML classification result."""
    if re.search(r"\b(?:tax\s+)?invoice\b", text, re.IGNORECASE):
        return True
    return bool(
        re.search(r"\bbill\s+to\b", text, re.IGNORECASE)
        and re.search(r"\b(?:subtotal|amount\s+due|total\s+due)\b", text, re.IGNORECASE)
    )


def empty_fields() -> dict[str, dict]:
    names = (
        "vendor_name",
        "invoice_number",
        "invoice_date",
        "due_date",
        "subtotal",
        "tax",
        "total",
        "currency",
        "vendor_address",
        "customer_name",
        "tax_id",
        "line_items",
    )
    return {
        name: {
            "value": "UNKNOWN" if name == "currency" else None,
            "confidence": None,
            "source": None,
        }
        for name in names
    }


def _normalized_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def _assign_candidate(fields: dict[str, dict], name: str, value: Any, source: str) -> None:
    previous = fields[name]["value"]
    if isinstance(previous, (int, float)) and isinstance(value, (int, float)):
        agrees = abs(previous - value) <= max(0.02, abs(value) * 0.005)
    elif previous is not None:
        agrees = _normalized_text(previous) == _normalized_text(value)
    else:
        agrees = False
    if not agrees:
        fields[name] = {"value": value, "confidence": None, "source": source}


def apply_ocr_label_candidates(fields: dict[str, dict], text: str) -> dict[str, dict]:
    """Normalize explicit OCR label/value pairs while retaining model output separately."""
    date_patterns = {
        "invoice_date": rf"\b(?:invoice\s+date|date)\s*[:#=-]?\s*({_DATE_TOKEN})",
        "due_date": rf"\b(?:due\s+date|payment\s+due)\s*[:#=-]?\s*({_DATE_TOKEN})",
    }
    for name, pattern in date_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        normalized = normalize_date(match.group(1)) if match else None
        if normalized:
            _assign_candidate(fields, name, normalized, "ocr_label_candidate")

    amount_patterns = {
        "subtotal": rf"\b(?:sub\s*total|net\s+amount)\b\s*[:=]?\s*{_AMOUNT_TOKEN}",
        "tax": rf"\b(?:GST(?:\s*\([^)]*\))?|tax(?:\s+amount)?|VAT)\s*[:=]?\s*{_AMOUNT_TOKEN}",
        "total": rf"\b(?:grand\s+total|amount\s+due|total(?:\s+(?:INR|USD|EUR|GBP))?)\b\s*[:=]?\s*{_AMOUNT_TOKEN}",
    }
    for name, pattern in amount_patterns.items():
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for match in reversed(matches):
            value = parse_amount(match.group(1))
            if value is not None:
                _assign_candidate(fields, name, value, "ocr_label_candidate")
                break

    invoice_number = re.search(
        r"(?i)\b(?:invoice\s*(?:number|no\.?|#)|inv\.?\s*(?:no\.?|#))\s*[:#-]?\s*([A-Z0-9][A-Z0-9/-]{2,})\b",
        text,
    )
    if invoice_number:
        _assign_candidate(fields, "invoice_number", invoice_number.group(1), "ocr_label_candidate")

    currency_match = re.search(
        r"₹|\$|€|£|\b(?:INR|USD|EUR|GBP|JPY|CAD|AUD|CNY|SGD|AED|CHF)\b",
        text,
        re.IGNORECASE,
    )
    if currency_match:
        currency = {
            "₹": "INR",
            "INR": "INR",
            "$": "USD",
            "USD": "USD",
            "EUR": "EUR",
            "€": "EUR",
            "GBP": "GBP",
            "£": "GBP",
            "JPY": "JPY",
            "CAD": "CAD",
            "AUD": "AUD",
            "CNY": "CNY",
            "SGD": "SGD",
            "AED": "AED",
            "CHF": "CHF",
        }.get(currency_match.group(0).upper(), "INR" if currency_match.group(0) == "₹" else None)
        if currency:
            _assign_candidate(fields, "currency", currency, "ocr_label_candidate")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and fields["vendor_name"]["value"] is None:
        header = lines[0]
        if len(header) <= 80 and not re.search(
            r"\b(?:invoice|tax|date|bill\s+to)\b", header, re.IGNORECASE
        ):
            _assign_candidate(fields, "vendor_name", header, "ocr_header_candidate")
    return fields


def normalize_extraction(raw: dict, ocr: dict, threshold: float) -> dict:
    donut = raw.get("donut", {})
    tree = donut.get("json", {})
    labels = {
        "vendor_name": {
            "vendor",
            "vendorname",
            "merchant",
            "merchantname",
            "supplier",
            "suppliername",
        },
        "invoice_number": {"invoicenumber", "invoiceno", "invoiceid", "receiptno", "receiptid"},
        "invoice_date": {"invoicedate", "date", "receiptdate"},
        "due_date": {"duedate", "paymentdue"},
        "subtotal": {"subtotal", "subtotalprice", "netamount", "amountbeforetax"},
        "tax": {"tax", "taxamount", "taxprice", "vat", "gst"},
        "total": {"total", "totalprice", "totalamount", "grandtotal", "amountdue"},
        "currency": {"currency"},
        "vendor_address": {"vendoraddress", "address"},
        "customer_name": {"customer", "customername", "billto"},
        "tax_id": {"gstin", "taxid", "vatnumber"},
    }
    score = donut.get("sequence_confidence")
    # Fallback text candidate lookup is explicitly OCR-derived and does not claim ML extraction confidence.
    text = ocr.get("text", "")
    fields: dict[str, dict] = {}
    for name, aliases in labels.items():
        value = find_field(tree, aliases)
        if name == "vendor_name" and isinstance(tree, dict) and isinstance(tree.get("store"), dict):
            value = tree["store"].get("name") or value
        source = "donut" if value is not None else None
        confidence = score if value is not None else None
        if name in ("invoice_date", "due_date") and value is not None:
            value = normalize_date(value)
        if name in ("subtotal", "tax", "total") and value is not None:
            value = parse_amount(value)
        if name == "currency" and value is not None:
            code_map = {
                "₹": "INR",
                "RS": "INR",
                "RUPEE": "INR",
                "INR": "INR",
                "$": "USD",
                "USD": "USD",
                "€": "EUR",
                "EUR": "EUR",
                "£": "GBP",
                "GBP": "GBP",
                "JPY": "JPY",
                "CAD": "CAD",
                "AUD": "AUD",
                "CNY": "CNY",
                "SGD": "SGD",
                "AED": "AED",
                "CHF": "CHF",
            }
            value = code_map.get(str(value).strip().upper())
            if value is None:
                source = None
                confidence = None
        if name == "currency" and value is None:
            match = re.search(r"₹|INR|\$|USD|€|EUR|£|GBP", text, re.I)
            value = (
                {
                    "₹": "INR",
                    "INR": "INR",
                    "$": "USD",
                    "USD": "USD",
                    "€": "EUR",
                    "EUR": "EUR",
                    "£": "GBP",
                    "GBP": "GBP",
                }.get(
                    match.group(0).upper() if match and match.group(0).isalpha() else match.group(0)
                )
                if match
                else None
            )
            source = "ocr_candidate" if value else None
        fields[name] = {
            "value": value,
            "confidence": confidence if confidence is None else round(float(confidence), 4),
            "source": source,
        }
    line_items = normalize_line_items(tree)
    fields["line_items"] = {
        "value": line_items,
        "confidence": score if line_items else None,
        "source": "donut" if line_items else None,
    }
    # Donut's receipt model cannot identify invoice semantics reliably; no value is synthesized when absent.
    fields["currency"]["value"] = fields["currency"]["value"] or "UNKNOWN"
    return apply_ocr_label_candidates(fields, text)
