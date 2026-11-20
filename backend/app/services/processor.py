import logging
import time
from pathlib import Path

from PIL import Image

from app.core.config import get_settings
from app.ml.donut import extract_with_donut
from app.ocr.engine import run_ocr
from app.services.normalize import empty_fields, looks_like_invoice, normalize_extraction
from app.services.validation import validate_fields

logger = logging.getLogger(__name__)


def _first_page(path: Path) -> Image.Image:
    if path.suffix.lower() == ".pdf":
        from pdf2image import convert_from_path

        return convert_from_path(str(path), dpi=get_settings().pdf_dpi, first_page=1, last_page=1)[
            0
        ]
    return Image.open(path)


def process_document(path: Path) -> dict:
    started = time.perf_counter()
    logger.info("OCR started")
    ocr = run_ocr(path)
    logger.info("OCR completed pages=%s words=%s", ocr["page_count"], len(ocr["words"]))
    raw = {"ocr_engine": ocr["engine"], "model_name": get_settings().model_name}
    if not looks_like_invoice(ocr["text"]):
        logger.info("Invoice pre-check skipped document understanding inference")
        raw["document_gate"] = {
            "status": "not_invoice",
            "method": "conservative OCR keyword pre-check",
        }
        validation = validate_fields(empty_fields(), get_settings().confidence_threshold)
        validation["issues"].insert(
            0, "This document does not appear to be an invoice; document understanding was skipped."
        )
        return {
            "ocr_result": ocr,
            "raw_extraction": raw,
            "extracted_fields": empty_fields(),
            "validation": validation,
            "extraction_status": "skipped_non_invoice",
            "processing_time_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    try:
        logger.info("Donut extraction started")
        raw["donut"] = extract_with_donut(_first_page(path))
        extraction_status = "completed"
    except Exception as exc:
        logger.exception("Document understanding inference failed")
        raw["model_error"] = type(exc).__name__
        extraction_status = "unavailable"
    fields = normalize_extraction(raw, ocr, get_settings().confidence_threshold)
    validation = validate_fields(fields, get_settings().confidence_threshold)
    return {
        "ocr_result": ocr,
        "raw_extraction": raw,
        "extracted_fields": fields,
        "validation": validation,
        "extraction_status": extraction_status,
        "processing_time_ms": round((time.perf_counter() - started) * 1000, 2),
    }
