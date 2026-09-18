"""Benchmark fixture scoring for deterministic detection."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from bowden_pii import detect


def score_fixture(path: Path) -> dict[str, object]:
    rows = 0
    exact_label_matches = 0
    false_positives = 0
    false_negatives = 0
    failures: list[dict[str, object]] = []
    label_scores: dict[str, Counter[str]] = {}
    slice_scores: dict[str, Counter[str]] = {}

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        rows += 1
        expected = list(row["expected_labels"])
        actual = [span.label for span in detect(row["text"])]
        row_slice = row.get("slice", "unknown")
        slice_scores.setdefault(row_slice, Counter())["rows"] += 1

        expected_counts = Counter(expected)
        actual_counts = Counter(actual)
        for label in sorted(set(expected_counts) | set(actual_counts)):
            scores = label_scores.setdefault(label, Counter())
            scores["tp"] += min(expected_counts[label], actual_counts[label])
            scores["fp"] += max(0, actual_counts[label] - expected_counts[label])
            scores["fn"] += max(0, expected_counts[label] - actual_counts[label])

        if actual == expected:
            exact_label_matches += 1
            slice_scores[row_slice]["exact_label_matches"] += 1
            continue

        row_fp = sum((actual_counts - expected_counts).values())
        row_fn = sum((expected_counts - actual_counts).values())
        false_positives += row_fp
        false_negatives += row_fn
        slice_scores[row_slice]["false_positives"] += row_fp
        slice_scores[row_slice]["false_negatives"] += row_fn
        failures.append({"id": row["id"], "expected": expected, "actual": actual})

    return {
        "rows": rows,
        "exact_label_matches": exact_label_matches,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "labels": {
            label: {
                "tp": counts["tp"],
                "fp": counts["fp"],
                "fn": counts["fn"],
            }
            for label, counts in sorted(label_scores.items())
        },
        "slices": {
            name: {
                "rows": counts["rows"],
                "exact_label_matches": counts["exact_label_matches"],
                "false_positives": counts["false_positives"],
                "false_negatives": counts["false_negatives"],
            }
            for name, counts in sorted(slice_scores.items())
        },
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a bowden-pii JSONL benchmark fixture.")
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args(argv)

    print(json.dumps(score_fixture(args.fixture), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
