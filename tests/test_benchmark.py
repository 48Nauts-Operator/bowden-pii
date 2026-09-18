from pathlib import Path

from bowden_pii.benchmark import score_fixture


def test_score_fixture_reports_clean_smoke_benchmark() -> None:
    result = score_fixture(Path("data/benchmarks/deterministic_smoke.jsonl"))

    assert result["rows"] == 15
    assert result["exact_label_matches"] == 15
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["slices"] == {
        "clean": {
            "rows": 10,
            "exact_label_matches": 10,
            "false_positives": 0,
            "false_negatives": 0,
        },
        "negative": {
            "rows": 5,
            "exact_label_matches": 5,
            "false_positives": 0,
            "false_negatives": 0,
        },
    }
    assert result["labels"]["VAT_ID"] == {"tp": 4, "fp": 0, "fn": 0}
    assert result["failures"] == []
