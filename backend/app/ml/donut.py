"""Pretrained Donut document extraction. It is not fine-tuned by this project."""

import logging
from threading import Lock

from PIL import Image

from app.core.config import get_settings

logger = logging.getLogger(__name__)
_lock = Lock()
_processor = None
_model = None


def model_status() -> str:
    return f"{get_settings().model_name} (pretrained CORD receipt model)"


def extract_with_donut(image: Image.Image) -> dict:
    """Generate structured document text and a sequence-derived confidence score."""
    global _processor, _model
    settings = get_settings()
    if not settings.enable_donut:
        raise RuntimeError("Donut inference is disabled. Set ENABLE_DONUT=true to enable it.")
    with _lock:
        if _model is None:
            import torch
            from transformers import DonutProcessor, VisionEncoderDecoderModel

            _processor = DonutProcessor.from_pretrained(settings.model_name)
            _model = VisionEncoderDecoderModel.from_pretrained(settings.model_name)
            device = (
                "cuda"
                if settings.device == "auto" and torch.cuda.is_available()
                else ("cpu" if settings.device == "auto" else settings.device)
            )
            _model.to(device).eval()
            _model._document_device = device
        processor, model = _processor, _model
    import torch

    image = image.convert("RGB")
    inputs = processor(image, return_tensors="pt")
    inputs = {key: value.to(model._document_device) for key, value in inputs.items()}
    decoder_input_ids = processor.tokenizer(
        "<s_cord-v2>", add_special_tokens=False, return_tensors="pt"
    ).input_ids.to(model._document_device)
    with torch.inference_mode():
        output = model.generate(
            **inputs,
            decoder_input_ids=decoder_input_ids,
            max_length=settings.max_model_tokens,
            return_dict_in_generate=True,
            output_scores=True,
        )
    sequence = output.sequences[0]
    text = processor.batch_decode(sequence.unsqueeze(0), skip_special_tokens=True)[0]
    parsed = processor.token2json(processor.tokenizer.decode(sequence, skip_special_tokens=False))
    # Mean probability of selected generated tokens; reflects decoding certainty, not field accuracy.
    probs = [score.float().softmax(-1).max(-1).values.item() for score in output.scores]
    confidence = sum(probs) / len(probs) if probs else None
    return {
        "json": parsed,
        "generated_text": text,
        "sequence_confidence": confidence,
        "model": settings.model_name,
        "model_task": "CORD receipt parsing",
    }
