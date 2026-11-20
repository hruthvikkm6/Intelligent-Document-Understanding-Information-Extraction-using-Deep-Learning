from app.ocr import engine
from PIL import Image


def test_ocr_returns_word_boxes_and_engine_confidence(tmp_path, monkeypatch):
    path = tmp_path / "one.png"
    Image.new("RGB", (50, 50), "white").save(path)
    monkeypatch.setattr(engine.pytesseract, "image_to_osd", lambda *a, **k: {"rotate": 0})

    def image_data(image, **kwargs):
        assert image.size == (100, 100)
        return {
            "text": ["Invoice", ""],
            "conf": ["91", "-1"],
            "left": [4, 0],
            "top": [7, 0],
            "width": [31, 0],
            "height": [8, 0],
        }

    monkeypatch.setattr(
        engine.pytesseract,
        "image_to_data",
        image_data,
    )
    result = engine.run_ocr(path)
    assert result["page_count"] == 1
    assert result["text"] == "Invoice"
    assert result["words"] == [
        {"text": "Invoice", "bbox": [4, 7, 35, 15], "confidence": 0.91, "page": 1}
    ]
    assert 0.9 < result["mean_confidence"] < 0.92
