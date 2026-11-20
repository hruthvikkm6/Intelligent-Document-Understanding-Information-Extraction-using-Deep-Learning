from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FieldValue(BaseModel):
    value: Any = None
    confidence: float | None = None
    source: str | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: str
    ocr_status: str
    extraction_status: str
    extracted_fields: dict[str, Any] | None = None
    raw_extraction: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    ocr_result: dict[str, Any] | None = None
    processing_time_ms: float | None = None
    error_message: str | None = None
    created_at: datetime
    processed_at: datetime | None = None


class DocumentList(BaseModel):
    items: list[DocumentOut]
    total: int


class HealthOut(BaseModel):
    status: str
    database: str
    extraction_model: str
