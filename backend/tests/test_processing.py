import pytest
from app.core.config import Settings
from app.services.normalize import (
    looks_like_invoice,
    normalize_date,
    normalize_extraction,
    parse_amount,
)
from app.services.validation import validate_fields
from app.utils.files import safe_filename
from pydantic import ValidationError


def test_parse_amount_locale_formats():
    assert parse_amount("₹ 53,100.00") == 53100.0
    assert parse_amount("1.234,56") == 1234.56
    assert parse_amount("(42.50)") == -42.5
    assert parse_amount("no amount") is None


def test_normalize_date():
    assert normalize_date("Nov 18, 2026") == "2026-11-18"
    assert normalize_date("not a date") is None
    assert normalize_date({"year": "2026", "month": "11", "day": "18"}) == "2026-11-18"


def test_ocr_candidates_require_invoice_number_label():
    result = normalize_extraction(
        {}, {"text": "TAX INVOICE Invoice Number: NS-2026-1042 ₹", "words": []}, 0.55
    )
    assert result["invoice_number"]["value"] == "NS-2026-1042"
    assert result["invoice_number"]["confidence"] is None
    assert result["invoice_number"]["source"] == "ocr_label_candidate"


def test_invoice_label_candidates_extract_visible_fields():
    text = "\n".join(
        [
            "NORTHSTAR OFFICE SUPPLIES",
            "TAX INVOICE",
            "Invoice Number: NS-2026-1042",
            "Invoice Date: 18 Nov 2026",
            "Due Date: 18 Dec 2026",
            "Subtotal = 45,000.00",
            "GST (18%) = 8,100.00",
            "TOTAL INR = 53,100.00",
        ]
    )
    fields = normalize_extraction({}, {"text": text, "words": []}, 0.55)
    assert fields["vendor_name"]["value"] == "NORTHSTAR OFFICE SUPPLIES"
    assert fields["invoice_number"]["value"] == "NS-2026-1042"
    assert fields["invoice_date"]["value"] == "2026-11-18"
    assert fields["due_date"]["value"] == "2026-12-18"
    assert fields["subtotal"]["value"] == 45000.0
    assert fields["tax"]["value"] == 8100.0
    assert fields["total"]["value"] == 53100.0
    assert fields["currency"]["value"] == "INR"
    assert fields["total"]["source"] == "ocr_label_candidate"
    assert fields["total"]["confidence"] is None


def test_invoice_gate_accepts_invoice_and_skips_resume_text():
    assert looks_like_invoice("NORTHSTAR TAX INVOICE Invoice Number INV-100")
    assert not looks_like_invoice("Software Engineer Resume Experience Skills Java Python")


def test_validation_flags_missing_and_arithmetic_mismatch():
    fields = {
        "invoice_number": {"value": None},
        "currency": {"value": "UNKNOWN"},
        "subtotal": {"value": 100.0, "confidence": 0.8},
        "tax": {"value": 10.0, "confidence": 0.8},
        "total": {"value": 120.0, "confidence": 0.2},
    }
    result = validate_fields(fields, 0.55)
    assert result["status"] == "warning"
    assert any("below" in issue for issue in result["issues"])
    assert any("differs" in issue for issue in result["issues"])
    assert any("Vendor name was not identified" == issue for issue in result["issues"])


def test_safe_filename_removes_paths_and_unsafe_chars():
    assert safe_filename("../../weird file?.pdf") == "weird_file_.pdf"


def test_configuration_rejects_invalid_limits():
    with pytest.raises(ValidationError):
        Settings(confidence_threshold=1.5)
    with pytest.raises(ValidationError):
        Settings(max_file_size=0)
