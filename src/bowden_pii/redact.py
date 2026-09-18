"""Public detection and redaction API."""

from __future__ import annotations

from collections import Counter

from bowden_pii.placeholders import PlaceholderBuilder
from bowden_pii.policy import labels_for_policy
from bowden_pii.rules import rule_detection_report, rule_detections
from bowden_pii.types import Detection, RedactionResult


def detect(text: str) -> list[Detection]:
    """Detect deterministic PII spans in `text`."""

    return rule_detections(text)


def redact(text: str, policy: str = "strict") -> RedactionResult:
    """Redact deterministic PII spans and return local placeholder metadata."""

    allowed_labels = labels_for_policy(policy)
    all_detections, conflicts = rule_detection_report(text)
    detections = [detection for detection in all_detections if detection.label in allowed_labels]
    placeholders = PlaceholderBuilder()
    pieces: list[str] = []
    public_spans: list[dict[str, object]] = []
    cursor = 0

    for detection in detections:
        placeholder = placeholders.placeholder_for(detection)
        pieces.append(text[cursor : detection.start])
        pieces.append(placeholder)
        public_spans.append(detection.to_public_dict(replacement=placeholder))
        cursor = detection.end

    pieces.append(text[cursor:])
    counts = Counter(detection.label for detection in detections)

    return RedactionResult(
        redacted="".join(pieces),
        spans=public_spans,
        placeholder_map=placeholders.placeholder_map,
        audit={
            "policy": policy,
            "total_spans": len(detections),
            "labels": dict(sorted(counts.items())),
            "sources": {"rule": len(detections)},
            "conflicts": [conflict.to_public_dict() for conflict in conflicts],
            "raw_values_in_audit": False,
        },
    )
