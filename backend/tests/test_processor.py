from pathlib import Path

from app.services import processor


def test_non_invoice_is_skipped_without_running_donut(monkeypatch):
    monkeypatch.setattr(
        processor,
        "run_ocr",
        lambda _: {
            "text": "Resume\nSoftware Engineer\nPython Java",
            "words": [],
            "page_count": 1,
            "engine": "test",
        },
    )
    monkeypatch.setattr(
        processor,
        "extract_with_donut",
        lambda _: (_ for _ in ()).throw(AssertionError("Donut must not run for a resume")),
    )
    result = processor.process_document(Path("unused.pdf"))
    assert result["extraction_status"] == "skipped_non_invoice"
    assert result["raw_extraction"]["document_gate"]["status"] == "not_invoice"
    assert result["extracted_fields"]["currency"]["value"] == "UNKNOWN"
    assert any(
        "does not appear to be an invoice" in issue for issue in result["validation"]["issues"]
    )
