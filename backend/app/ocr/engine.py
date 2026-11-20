import logging
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

import pytesseract
from PIL import Image, ImageOps
from pytesseract import Output

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class OCRWord:
    text: str
    bbox: list[int]
    confidence: float
    page: int


def _pages(path: Path) -> list[Image.Image]:
    if path.suffix.lower() == ".pdf":
        from pdf2image import convert_from_path

        pages = convert_from_path(
            str(path),
            dpi=get_settings().pdf_dpi,
            first_page=1,
            last_page=get_settings().max_pdf_pages,
        )
    else:
        pages = [Image.open(path)]
    return [ImageOps.exif_transpose(page).convert("RGB") for page in pages]


def run_ocr(path: Path) -> dict:
    settings = get_settings()
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    else:
        candidates = [shutil.which("tesseract")]
        if os.name == "nt":
            candidates.extend(
                [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                ]
            )
        detected = next(
            (candidate for candidate in candidates if candidate and Path(candidate).is_file()), None
        )
        if detected:
            pytesseract.pytesseract.tesseract_cmd = detected
    pages = _pages(path)
    if not pages:
        raise ValueError("The document contains no pages.")
    words: list[OCRWord] = []
    page_text: list[str] = []
    for index, image in enumerate(pages, 1):
        # Upscale small scans and let Tesseract's orientation detection handle rotation where possible.
        if min(image.size) < 1000:
            scale = min(2.0, 1000 / min(image.size))
            image = image.resize((int(image.width * scale), int(image.height * scale)))
        try:
            orientation = pytesseract.image_to_osd(image, output_type=Output.DICT)
            rotation = int(orientation.get("rotate", 0))
            if rotation:
                image = image.rotate(rotation, expand=True)
        except (pytesseract.TesseractError, OSError):
            logger.debug("Orientation detection unavailable for page %s", index)
        result = pytesseract.image_to_data(image, output_type=Output.DICT, config="--psm 3")
        lines: dict[tuple[int, int, int], list[str]] = {}
        for i, token in enumerate(result["text"]):
            text = token.strip()
            try:
                confidence = float(result["conf"][i]) / 100
            except (ValueError, TypeError):
                continue
            if not text or confidence < 0:
                continue
            x, y, w, h = (int(result[k][i]) for k in ("left", "top", "width", "height"))
            words.append(OCRWord(text, [x, y, x + w, y + h], max(0, min(1, confidence)), index))
            line_key = tuple(
                int(result.get(key, [0] * len(result["text"]))[i])
                for key in ("block_num", "par_num", "line_num")
            )
            lines.setdefault(line_key, []).append(text)
        page_text.append("\n".join(" ".join(tokens) for tokens in lines.values()))
    if not words:
        raise ValueError("OCR found no readable text. Try a sharper scan or a supported file.")
    return {
        "text": "\n".join(page_text),
        "words": [asdict(word) for word in words],
        "page_count": len(pages),
        "engine": "Tesseract OCR",
        "mean_confidence": sum(w.confidence for w in words) / len(words),
    }
