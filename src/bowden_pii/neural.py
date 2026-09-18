"""Neural token-classifier detector utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bowden_pii.types import Detection


@dataclass
class MiniLMTokenDetector:
    model: Any
    tokenizer: Any
    id_to_label: dict[int, str]
    device: str
    max_length: int = 256

    @classmethod
    def from_model_dir(
        cls,
        model_dir: str,
        device: str | None = None,
        max_length: int = 256,
    ) -> MiniLMTokenDetector:
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer

        if device is None:
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        model = AutoModelForTokenClassification.from_pretrained(model_dir, local_files_only=True)
        id_to_label = normalize_id_to_label(model.config.id2label)
        model.to(torch.device(device))
        model.eval()
        return cls(
            model=model,
            tokenizer=tokenizer,
            id_to_label=id_to_label,
            device=device,
            max_length=max_length,
        )

    def __call__(self, text: str) -> list[Detection]:
        import torch

        encoded = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            return_offsets_mapping=True,
            return_tensors="pt",
        )
        offsets = [tuple(offset) for offset in encoded.pop("offset_mapping")[0].tolist()]
        batch = {key: value.to(torch.device(self.device)) for key, value in encoded.items()}
        with torch.no_grad():
            output = self.model(**batch)
        probabilities = output.logits.softmax(dim=-1)[0].detach().cpu()
        predicted_ids = output.logits.argmax(dim=-1)[0].detach().cpu()
        token_predictions: list[tuple[int, int, str, float]] = []
        for token_index, (start, end) in enumerate(offsets):
            if start == end:
                continue
            pred_id = int(predicted_ids[token_index])
            token_predictions.append(
                (
                    start,
                    end,
                    self.id_to_label[pred_id],
                    float(probabilities[token_index][pred_id]),
                )
            )
        return detections_from_token_predictions(text, token_predictions)


def normalize_id_to_label(raw_id_to_label: dict[int | str, str]) -> dict[int, str]:
    return {int(index): label for index, label in raw_id_to_label.items()}


def detections_from_token_predictions(
    text: str,
    token_predictions: list[tuple[int, int, str, float]],
) -> list[Detection]:
    detections: list[Detection] = []
    active_label: str | None = None
    active_start: int | None = None
    active_end: int | None = None
    active_confidences: list[float] = []

    def close_active() -> None:
        nonlocal active_label, active_start, active_end, active_confidences
        if active_label is None or active_start is None or active_end is None:
            return
        detections.append(
            Detection(
                start=active_start,
                end=active_end,
                label=active_label,
                value=text[active_start:active_end],
                source="neural",
                rule_id=f"minilm:{active_label}",
                confidence=min(active_confidences) if active_confidences else 1.0,
            )
        )
        active_label = None
        active_start = None
        active_end = None
        active_confidences = []

    for start, end, bio_label, confidence in token_predictions:
        if bio_label == "O":
            close_active()
            continue
        prefix, label = split_bio_label(bio_label)
        starts_new = prefix == "B" or active_label != label
        if starts_new:
            close_active()
            active_label = label
            active_start = start
            active_end = end
            active_confidences = [confidence]
        else:
            active_end = end
            active_confidences.append(confidence)
    close_active()
    return detections


def split_bio_label(label: str) -> tuple[str, str]:
    if "-" not in label:
        return "B", label
    prefix, entity_label = label.split("-", 1)
    return prefix, entity_label
