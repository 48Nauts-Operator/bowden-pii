"""Redaction policy profiles."""

from __future__ import annotations

POLICY_LABELS: dict[str, frozenset[str]] = {
    "strict": frozenset(
        {
            "AHV",
            "IBAN",
            "QR_IBAN",
            "UID",
            "VAT_ID",
            "CREDIT_CARD",
            "EMAIL",
            "PHONE",
            "URL",
            "IP_ADDRESS",
            "MAC_ADDRESS",
            "PERSON",
            "STREET_NAME",
            "BUILDING_NUMBER",
            "ZIP_CODE",
            "CITY",
        }
    ),
    "balanced": frozenset(
        {
            "AHV",
            "IBAN",
            "QR_IBAN",
            "UID",
            "VAT_ID",
            "CREDIT_CARD",
            "EMAIL",
            "PHONE",
            "IP_ADDRESS",
            "MAC_ADDRESS",
            "PERSON",
            "STREET_NAME",
            "BUILDING_NUMBER",
            "ZIP_CODE",
            "CITY",
        }
    ),
    "permissive": frozenset(
        {
            "AHV",
            "IBAN",
            "QR_IBAN",
            "VAT_ID",
            "CREDIT_CARD",
            "EMAIL",
            "PHONE",
        }
    ),
}

POLICY_THRESHOLDS: dict[str, float] = {
    "strict": 0.5,
    "balanced": 0.7,
    "permissive": 0.9,
}


def labels_for_policy(policy: str) -> frozenset[str]:
    try:
        return POLICY_LABELS[policy]
    except KeyError as exc:
        choices = ", ".join(sorted(POLICY_LABELS))
        raise ValueError(f"unknown policy {policy!r}; expected one of: {choices}") from exc


def threshold_for_policy(policy: str) -> float:
    try:
        return POLICY_THRESHOLDS[policy]
    except KeyError as exc:
        choices = ", ".join(sorted(POLICY_THRESHOLDS))
        raise ValueError(f"unknown policy {policy!r}; expected one of: {choices}") from exc
