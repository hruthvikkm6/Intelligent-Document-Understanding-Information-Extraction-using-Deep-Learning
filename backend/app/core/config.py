from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Intelligent Document Understanding"
    database_url: str = "sqlite:///./data/documents.db"
    upload_dir: Path = Path("./data/uploads")
    max_file_size: int = Field(default=15 * 1024 * 1024, gt=0, le=200 * 1024 * 1024)
    confidence_threshold: float = Field(default=0.55, ge=0, le=1)
    model_name: str = "naver-clova-ix/donut-base-finetuned-cord-v2"
    max_model_tokens: int = Field(default=256, ge=64, le=768)
    enable_donut: bool = True
    device: str = "auto"
    tesseract_cmd: str | None = None
    pdf_dpi: int = Field(default=180, ge=72, le=400)
    max_pdf_pages: int = Field(default=20, ge=1, le=100)
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
