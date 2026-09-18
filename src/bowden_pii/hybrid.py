"""Hybrid deterministic plus neural detection and redaction."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from bowden_pii.placeholders import PlaceholderBuilder
from bowden_pii.policy import labels_for_policy, threshold_for_policy
from bowden_pii.rules import rule_detection_report
from bowden_pii.types import Detection, DetectionConflict, RedactionResult

NeuralDetector = Callable[[str], Iterable[Detection]]


@dataclass(frozen=True)
class HybridDetectionResult:
    detections: list[Detection]
    conflicts: list[DetectionConflict]


def merge_detections(
    rule_detections: Iterable[Detection],
    neural_detections: Iterable[Detection],
    threshold: float,
    allowed_labels: set[str] | frozenset[str],
) -> HybridDetectionResult:
    accepted = sorted(
        [item for item in rule_detections if item.label in allowed_labels],
        key=detection_position_key,
    )
    conflicts: list[DetectionConflict] = []
    neural_candidates = [item for item in neural_detections if item.label in allowed_labels]

    for candidate in sorted(neural_candidates, key=neural_priority_key):
        if candidate.confidence < threshold:
            conflicts.append(
                DetectionConflict(
                    kept=candidate,
                    dropped=candidate,
                    reason="below_threshold",
                )
            )
            continue
        overlapping_rule = first_overlap(candidate, accepted, source="rule")
        if overlapping_rule is not None:
            conflicts.append(
                DetectionConflict(
                    kept=overlapping_rule,
                    dropped=candidate,
                    reason="neural_overlap_rule",
                )
            )
            continue
        overlapping_neural = first_overlap(candidate, accepted, source="neural")
        if overlapping_neural is not None:
            conflicts.append(
                DetectionConflict(
                    kept=overlapping_neural,
                    dropped=candidate,
                    reason="neural_overlap_neural",
                )
            )
            continue
        accepted.append(candidate)
        accepted.sort(key=detection_position_key)

    return HybridDetectionResult(detections=accepted, conflicts=conflicts)


def neural_priority_key(detection: Detection) -> tuple[float, int, int]:
    return (-detection.confidence, -(detection.end - detection.start), detection.start)


def detection_position_key(detection: Detection) -> tuple[int, int, str]:
    return (detection.start, detection.end, detection.label)


def first_overlap(
    candidate: Detection,
    detections: Iterable[Detection],
    source: str,
) -> Detection | None:
    for detection in detections:
        if detection.source == source and candidate.overlaps(detection):
            return detection
    return None


def hybrid_detect(
    text: str,
    neural_detector: NeuralDetector,
    threshold: float | None = None,
    policy: str = "strict",
) -> list[Detection]:
    threshold = threshold_for_policy(policy) if threshold is None else threshold
    rule_detections, _rule_conflicts = rule_detection_report(text)
    result = merge_detections(
        rule_detections=rule_detections,
        neural_detections=list(neural_detector(text)),
        threshold=threshold,
        allowed_labels=labels_for_policy(policy),
    )
    return result.detections


def hybrid_redact(
    text: str,
    neural_detector: NeuralDetector,
    threshold: float | None = None,
    policy: str = "strict",
) -> RedactionResult:
    threshold = threshold_for_policy(policy) if threshold is None else threshold
    rule_detections, rule_conflicts = rule_detection_report(text)
    result = merge_detections(
        rule_detections=rule_detections,
        neural_detections=list(neural_detector(text)),
        threshold=threshold,
        allowed_labels=labels_for_policy(policy),
    )
    placeholders = PlaceholderBuilder()
    pieces: list[str] = []
    public_spans: list[dict[str, object]] = []
    cursor = 0

    for detection in result.detections:
        placeholder = placeholders.placeholder_for(detection)
        pieces.append(text[cursor : detection.start])
        pieces.append(placeholder)
        public_spans.append(detection.to_public_dict(replacement=placeholder))
        cursor = detection.end

    pieces.append(text[cursor:])
    counts = Counter(detection.label for detection in result.detections)
    sources = Counter(detection.source for detection in result.detections)

    return RedactionResult(
        redacted="".join(pieces),
        spans=public_spans,
        placeholder_map=placeholders.placeholder_map,
        audit={
            "policy": policy,
            "threshold": threshold,
            "total_spans": len(result.detections),
            "labels": dict(sorted(counts.items())),
            "sources": dict(sorted(sources.items())),
            "conflicts": [
                conflict.to_public_dict() for conflict in [*rule_conflicts, *result.conflicts]
            ],
            "raw_values_in_audit": False,
        },
    )
