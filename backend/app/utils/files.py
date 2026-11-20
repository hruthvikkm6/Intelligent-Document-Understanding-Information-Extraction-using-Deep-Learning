import re
from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED = {
    ".pdf": {"application/pdf"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".tif": {"image/tiff"},
    ".tiff": {"image/tiff"},
    ".webp": {"image/webp"},
}


def safe_filename(name: str) -> str:
    leaf = Path(name.replace("\\", "/")).name
    clean = re.sub(r"[^A-Za-z0-9._-]", "_", leaf).strip("._")
    return clean[:180] or "document"


def validate_upload(upload: UploadFile, size: int, max_size: int) -> str:
    ext = Path(safe_filename(upload.filename or "")).suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload a PDF, PNG, JPEG, TIFF, or WebP document.",
        )
    if upload.content_type not in ALLOWED[ext]:
        raise HTTPException(
            status_code=415, detail="The file extension and content type do not match."
        )
    if size <= 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if size > max_size:
        raise HTTPException(
            status_code=413, detail=f"File exceeds the {max_size // (1024 * 1024)} MB upload limit."
        )
    return ext


def validate_signature(ext: str, content: bytes) -> bool:
    if ext == ".pdf":
        return content.startswith(b"%PDF")
    if ext == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if ext in {".jpg", ".jpeg"}:
        return content.startswith(b"\xff\xd8\xff")
    if ext in {".tif", ".tiff"}:
        return content.startswith((b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"))
    if ext == ".webp":
        return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    return False
