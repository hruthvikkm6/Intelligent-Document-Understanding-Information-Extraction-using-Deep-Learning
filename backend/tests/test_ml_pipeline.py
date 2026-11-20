from app.services.normalize import normalize_extraction
from app.services.validation import validate_fields


def test_pretrained_model_output_maps_to_api_fields():
    raw = {
        "donut": {
            "json": {
                "store": {"name": "Sample Vendor"},
                "date": {"year": "2026", "month": "11", "day": "18"},
                "total": {
                    "subtotal_price": "100.00",
                    "tax_price": "18.00",
                    "total_price": "118.00",
                },
                "menu": [{"nm": "Paper", "cnt": "2", "unitprice": "50.00", "price": "100.00"}],
            },
            "sequence_confidence": 0.82,
        }
    }
    fields = normalize_extraction(raw, {"text": "Invoice Number: AC-101 INR", "words": []}, 0.55)
    assert fields["vendor_name"]["value"] == "Sample Vendor"
    assert fields["invoice_number"]["value"] == "AC-101"
    assert fields["invoice_date"]["value"] == "2026-11-18"
    assert fields["subtotal"]["value"] == 100.0
    assert fields["tax"]["value"] == 18.0
    assert fields["total"]["value"] == 118.0
    assert fields["line_items"]["value"][0] == {
        "description": "Paper",
        "quantity": 2.0,
        "unit_price": 50.0,
        "amount": 100.0,
    }
    assert fields["total"]["confidence"] == 0.82


def test_empty_model_output_yields_null_values_and_warnings():
    fields = normalize_extraction({}, {"text": "", "words": []}, 0.55)
    assert all(field["value"] is None or field["value"] == "UNKNOWN" for field in fields.values())
    validation = validate_fields(fields, 0.55)
    assert validation["status"] == "warning"
    assert "Total amount was not identified" in validation["issues"]


def test_ocr_candidate_corrects_disagreement_but_keeps_agreeing_model_field():
    raw = {
        "donut": {
            "json": {"subtotal": "182026", "tax": "48", "total": {"total_price": "53,100.00"}},
            "sequence_confidence": 0.91,
        }
    }
    text = "TAX INVOICE\nSubtotal = 45,000.00\nGST (18%) = 8,100.00\nTOTAL INR = 53,100.00"
    fields = normalize_extraction(raw, {"text": text, "words": []}, 0.55)
    assert fields["subtotal"]["value"] == 45000.0
    assert fields["subtotal"]["source"] == "ocr_label_candidate"
    assert fields["tax"]["value"] == 8100.0
    assert fields["tax"]["source"] == "ocr_label_candidate"
    assert fields["total"]["value"] == 53100.0
    assert fields["total"]["source"] == "donut"
    assert fields["total"]["confidence"] == 0.91
