"""Command line interface for local redaction smoke tests."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from bowden_pii.hybrid import hybrid_redact
from bowden_pii.neural import MiniLMTokenDetector
from bowden_pii.redact import redact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Redact Swiss/EU PII from local text.")
    parser.add_argument("text", nargs="?", help="Text to redact. Reads stdin when omitted.")
    parser.add_argument(
        "--mode",
        choices=["deterministic", "hybrid"],
        default="deterministic",
        help="Detector mode.",
    )
    parser.add_argument(
        "--policy",
        default="strict",
        choices=["strict", "balanced", "permissive"],
        help="Redaction policy profile.",
    )
    parser.add_argument(
        "--model-dir", help="Local token-classifier model directory for hybrid mode."
    )
    parser.add_argument("--threshold", type=float, default=None, help="Override hybrid threshold.")
    parser.add_argument("--json", action="store_true", help="Emit full JSON result.")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.mode == "hybrid" and not args.model_dir:
        parser.print_usage(sys.stderr)
        print("bowden-pii: error: --model-dir is required for hybrid mode", file=sys.stderr)
        return 2

    text = args.text if args.text is not None else sys.stdin.read()
    if args.mode == "hybrid":
        detector = MiniLMTokenDetector.from_model_dir(args.model_dir)
        result = hybrid_redact(
            text,
            detector,
            threshold=args.threshold,
            policy=args.policy,
        )
    else:
        result = redact(text, policy=args.policy)
    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(result.redacted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
