from bowden_pii.hybrid import merge_detections
from bowden_pii.policy import threshold_for_policy
from bowden_pii.types import Detection


def span(
    start: int,
    end: int,
    label: str,
    source: str,
    confidence: float = 1.0,
) -> Detection:
    return Detection(
        start=start,
        end=end,
        label=label,
        value=f"value-{label}",
        source=source,
        rule_id=f"{source}:{label}",
        confidence=confidence,
    )


def test_merge_keeps_rule_span_when_neural_overlaps() -> None:
    result = merge_detections(
        rule_detections=[span(4, 20, "IBAN", "rule")],
        neural_detections=[span(8, 18, "PERSON", "neural", confidence=0.99)],
        threshold=0.7,
        allowed_labels={"IBAN", "PERSON"},
    )

    assert [(item.start, item.end, item.label, item.source) for item in result.detections] == [
        (4, 20, "IBAN", "rule")
    ]
    assert len(result.conflicts) == 1
    assert result.conflicts[0].reason == "neural_overlap_rule"
    public = result.conflicts[0].to_public_dict()
    assert "value-IBAN" not in str(public)
    assert "value-PERSON" not in str(public)


def test_merge_accepts_non_overlapping_neural_span() -> None:
    result = merge_detections(
        rule_detections=[span(0, 8, "EMAIL", "rule")],
        neural_detections=[span(20, 30, "PERSON", "neural", confidence=0.91)],
        threshold=0.7,
        allowed_labels={"EMAIL", "PERSON"},
    )

    assert [(item.start, item.end, item.label) for item in result.detections] == [
        (0, 8, "EMAIL"),
        (20, 30, "PERSON"),
    ]
    assert result.conflicts == []


def test_merge_drops_below_threshold_neural_span() -> None:
    result = merge_detections(
        rule_detections=[],
        neural_detections=[span(2, 12, "PERSON", "neural", confidence=0.69)],
        threshold=0.7,
        allowed_labels={"PERSON"},
    )

    assert result.detections == []
    assert result.conflicts[0].reason == "below_threshold"


def test_merge_keeps_higher_confidence_neural_overlap() -> None:
    result = merge_detections(
        rule_detections=[],
        neural_detections=[
            span(2, 12, "PERSON", "neural", confidence=0.74),
            span(2, 18, "STREET_NAME", "neural", confidence=0.94),
        ],
        threshold=0.7,
        allowed_labels={"PERSON", "STREET_NAME"},
    )

    assert [(item.start, item.end, item.label) for item in result.detections] == [
        (2, 18, "STREET_NAME")
    ]
    assert result.conflicts[0].reason == "neural_overlap_neural"


def fake_neural_detector(_text: str) -> list[Detection]:
    return [
        Detection(
            start=0,
            end=10,
            label="PERSON",
            value="Mia Keller",
            source="neural",
            rule_id="fake-person",
            confidence=0.95,
        )
    ]


def test_hybrid_detect_includes_rule_and_neural_spans() -> None:
    from bowden_pii import hybrid_detect

    text = "Mia Keller uses mia@example.ch"

    spans = hybrid_detect(text, fake_neural_detector, threshold=0.7)

    assert [(item.label, item.source) for item in spans] == [
        ("PERSON", "neural"),
        ("EMAIL", "rule"),
    ]


def test_hybrid_redact_replaces_rule_and_neural_spans() -> None:
    from bowden_pii import hybrid_redact

    text = "Mia Keller uses mia@example.ch"

    result = hybrid_redact(text, fake_neural_detector, threshold=0.7)

    assert result.redacted == "[PERSON_1] uses [EMAIL_1]"
    assert result.audit["sources"] == {"neural": 1, "rule": 1}


def test_existing_runtime_stays_deterministic_only() -> None:
    from bowden_pii import detect, redact

    text = "Mia Keller uses mia@example.ch"

    assert [(item.label, item.source) for item in detect(text)] == [("EMAIL", "rule")]
    assert redact(text).redacted == "Mia Keller uses [EMAIL_1]"


def test_threshold_for_policy_returns_hybrid_presets() -> None:
    assert threshold_for_policy("strict") == 0.5
    assert threshold_for_policy("balanced") == 0.7
    assert threshold_for_policy("permissive") == 0.9


def test_hybrid_detect_uses_policy_threshold_when_threshold_omitted() -> None:
    from bowden_pii import hybrid_detect

    def weak_detector(_text: str) -> list[Detection]:
        return [
            Detection(
                start=0,
                end=10,
                label="PERSON",
                value="Mia Keller",
                source="neural",
                rule_id="weak-person",
                confidence=0.6,
            )
        ]

    text = "Mia Keller uses mia@example.ch"

    strict = hybrid_detect(text, weak_detector, policy="strict")
    permissive = hybrid_detect(text, weak_detector, policy="permissive")

    assert [(item.label, item.source) for item in strict] == [
        ("PERSON", "neural"),
        ("EMAIL", "rule"),
    ]
    assert [(item.label, item.source) for item in permissive] == [("EMAIL", "rule")]
