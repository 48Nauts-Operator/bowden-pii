from bowden_pii.neural import detections_from_token_predictions


def test_detections_from_token_predictions_merges_bio_tokens() -> None:
    text = "Mia Keller uses mia@example.ch"
    detections = detections_from_token_predictions(
        text,
        [
            (0, 3, "B-PERSON", 0.95),
            (4, 10, "I-PERSON", 0.91),
            (11, 15, "O", 0.99),
            (16, 19, "B-EMAIL", 0.93),
            (19, 30, "I-EMAIL", 0.88),
        ],
    )

    assert [
        (item.start, item.end, item.label, item.value, item.confidence) for item in detections
    ] == [
        (0, 10, "PERSON", "Mia Keller", 0.91),
        (16, 30, "EMAIL", "mia@example.ch", 0.88),
    ]
