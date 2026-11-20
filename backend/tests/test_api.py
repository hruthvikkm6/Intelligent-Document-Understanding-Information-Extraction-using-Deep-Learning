import os
import shutil
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test-documents.db"
os.environ["UPLOAD_DIR"] = "./test-uploads"

from app.database.session import Base, engine
from app.main import app
from fastapi.testclient import TestClient


def test_health_and_document_not_found():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["database"] == "ok"
        assert client.get("/api/v1/documents/missing-id").status_code == 404


def test_health_reports_database_outage_without_traceback(monkeypatch):
    def unavailable():
        raise OSError("private database connection detail")

    monkeypatch.setattr(engine, "connect", unavailable)
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        assert response.json()["status"] == "degraded"
        assert "private database" not in response.text


def test_upload_validation():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("bad.exe", b"not executable", "application/octet-stream")},
        )
        assert response.status_code == 415


def test_upload_file_preview_and_delete():
    payload = b"\x89PNG\r\n\x1a\nsynthetic-test-payload"
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/documents/upload", files={"file": ("invoice.png", payload, "image/png")}
        )
        assert created.status_code == 201
        document_id = created.json()["id"]
        listing = client.get("/api/v1/documents")
        assert listing.status_code == 200
        assert any(item["id"] == document_id for item in listing.json()["items"])
        preview = client.get(f"/api/v1/documents/{document_id}/file")
        assert preview.status_code == 200
        assert preview.content == payload
        assert client.delete(f"/api/v1/documents/{document_id}").status_code == 204
        assert client.get(f"/api/v1/documents/{document_id}").status_code == 404


def teardown_module():
    engine.dispose()
    Path("test-documents.db").unlink(missing_ok=True)
    shutil.rmtree("test-uploads", ignore_errors=True)
