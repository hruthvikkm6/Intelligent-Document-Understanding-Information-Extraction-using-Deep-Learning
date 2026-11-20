import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.documents import router as documents_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database import models  # noqa: F401
from app.database.session import Base, engine
from app.ml.donut import model_status

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    if settings.database_url.startswith("sqlite"):
        from pathlib import Path

        Path(settings.database_url.removeprefix("sqlite:///")).parent.mkdir(
            parents=True, exist_ok=True
        )
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception("Database initialization failed; API will start in degraded mode")
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Invoice OCR and pretrained document understanding API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
app.include_router(documents_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        database = "ok"
    except Exception:
        logger.exception("Database health check failed")
        database = "unavailable"
    return JSONResponse(
        {
            "status": "ok" if database == "ok" else "degraded",
            "database": database,
            "extraction_model": model_status(),
        },
        status_code=200 if database == "ok" else 503,
    )
