import json
from pathlib import Path

from bowden_pii import detect


def test_deterministic_smoke_fixture_matches_expected_labels() -> None:
    fixture = Path("data/benchmarks/deterministic_smoke.jsonl")
    for line in fixture.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        labels = [span.label for span in detect(row["text"])]
        assert labels == row["expected_labels"], row["id"]
