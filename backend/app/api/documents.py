import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.models import Document
from app.database.session import get_db
from app.schemas.document import DocumentList, DocumentOut
from app.services.processor import process_document
from app.utils.files import safe_filename, validate_signature, validate_upload

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    settings = get_settings()
    content = await file.read(settings.max_file_size + 1)
    ext = validate_upload(file, len(content), settings.max_file_size)
    if not validate_signature(ext, content):
        raise HTTPException(
            status_code=400, detail="The uploaded file signature does not match its declared type."
        )
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    original = safe_filename(file.filename or "document")
    stored = f"{uuid4().hex}{ext}"
    stored_path = settings.upload_dir / stored
    stored_path.write_bytes(content)
    record = Document(
        original_filename=original,
        stored_filename=stored,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    try:
        db.add(record)
        db.commit()
    except Exception as exc:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        logger.exception("Document metadata persistence failed")
        raise HTTPException(
            status_code=503, detail="Document storage is temporarily unavailable. Please retry."
        ) from exc
    db.refresh(record)
    logger.info("Document uploaded id=%s bytes=%s", record.id, record.size_bytes)
    return record


@router.post("/{document_id}/process", response_model=DocumentOut)
def process(document_id: str, db: Session = Depends(get_db)):
    record = db.get(Document, document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    if record.status == "processing":
        raise HTTPException(status_code=409, detail="Document is already processing.")
    record.status = "processing"
    db.commit()
    try:
        result = process_document(get_settings().upload_dir / record.stored_filename)
        record.ocr_result = result["ocr_result"]
        record.raw_extraction = result["raw_extraction"]
        record.extracted_fields = result["extracted_fields"]
        record.validation = result["validation"]
        record.processing_time_ms = result["processing_time_ms"]
        record.ocr_status = "completed"
        record.extraction_status = result["extraction_status"]
        record.status = (
            "completed" if result["extraction_status"] == "completed" else "completed_with_warnings"
        )
        record.processed_at = datetime.now(UTC)
        record.error_message = None
        db.commit()
        db.refresh(record)
        return record
    except Exception as exc:
        db.rollback()
        record = db.get(Document, document_id)
        record.status = "failed"
        record.ocr_status = "failed"
        record.error_message = "Document processing failed. Check server logs for details."
        db.commit()
        logger.exception(
            "Document processing failed id=%s type=%s", document_id, type(exc).__name__
        )
        raise HTTPException(
            status_code=422,
            detail="We could not process this document. Check that it is readable and try again.",
        ) from exc


@router.get("", response_model=DocumentList)
def list_documents(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    items = db.scalars(
        select(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit)
    ).all()
    total = db.scalar(select(func.count()).select_from(Document)) or 0
    return {"items": items, "total": total}


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    record = db.get(Document, document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    return record


@router.get("/{document_id}/file")
def get_document_file(document_id: str, db: Session = Depends(get_db)):
    record = db.get(Document, document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    path = get_settings().upload_dir / record.stored_filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored document file is unavailable.")
    return FileResponse(
        path,
        media_type=record.content_type,
        headers={"Content-Disposition": "inline", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    record = db.get(Document, document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    stored = get_settings().upload_dir / record.stored_filename
    db.delete(record)
    db.commit()
    stored.unlink(missing_ok=True)
