from bowden_pii import detect, redact


def test_detect_finds_ahv_iban_and_email() -> None:
    text = "Anna: AHV 756.9217.0769.85, IBAN CH93 0076 2011 6238 5295 7, anna@example.ch"
    spans = detect(text)

    assert [span.label for span in spans] == ["AHV", "IBAN", "EMAIL"]
    assert [span.source for span in spans] == ["rule", "rule", "rule"]


def test_detect_finds_uid_vat_card_url_and_ip() -> None:
    text = (
        "UID CHE-100.155.212, VAT CHE-107.787.577 IVA, card 4111 1111 1111 1111, "
        "portal https://example.ch/login, host 192.168.1.10"
    )
    spans = detect(text)

    assert [span.label for span in spans] == [
        "UID",
        "VAT_ID",
        "CREDIT_CARD",
        "URL",
        "IP_ADDRESS",
    ]


def test_detect_finds_qr_iban_phone_and_mac() -> None:
    text = "QR CH57 3000 0123 4567 8901 2, phone +41 79 123 45 67, mac aa:bb:cc:dd:ee:ff"
    spans = detect(text)

    assert [span.label for span in spans] == ["QR_IBAN", "PHONE", "MAC_ADDRESS"]


def test_vat_span_wins_over_overlapping_uid_span() -> None:
    result = redact("Invoice CHE-107.787.577 IVA")

    assert result.redacted == "Invoice [VAT_ID_1]"
    assert result.spans[0]["label"] == "VAT_ID"
    assert list(result.placeholder_map) == ["[VAT_ID_1]"]


def test_redact_replaces_values_and_keeps_local_placeholder_map() -> None:
    text = "AHV 756.9217.0769.85 and iban CH93 0076 2011 6238 5295 7"
    result = redact(text)

    assert result.redacted == "AHV [AHV_1] and iban [IBAN_1]"
    assert result.audit == {
        "policy": "strict",
        "total_spans": 2,
        "labels": {"AHV": 1, "IBAN": 1},
        "sources": {"rule": 2},
        "conflicts": [],
        "raw_values_in_audit": False,
    }
    assert result.spans == [
        {
            "start": 4,
            "end": 20,
            "label": "AHV",
            "source": "rule",
            "rule_id": "ch_ahv_ean13_v1",
            "confidence": 1.0,
            "replacement": "[AHV_1]",
        },
        {
            "start": 30,
            "end": 56,
            "label": "IBAN",
            "source": "rule",
            "rule_id": "iban_iso13616_mod97_v1",
            "confidence": 1.0,
            "replacement": "[IBAN_1]",
        },
    ]
    assert result.placeholder_map["[AHV_1]"].value == "756.9217.0769.85"
    assert result.placeholder_map["[IBAN_1]"].normalized == "CH93 0076 2011 6238 5295 7"


def test_redact_reuses_placeholder_for_same_normalized_value() -> None:
    text = "Use 756.9217.0769.85, then 7569217076985 again."
    result = redact(text)

    assert result.redacted == "Use [AHV_1], then [AHV_1] again."
    assert list(result.placeholder_map) == ["[AHV_1]"]


def test_redact_policy_controls_optional_labels() -> None:
    text = "Email anna@example.ch, site https://example.ch, UID CHE-100.155.212"

    strict = redact(text, policy="strict")
    permissive = redact(text, policy="permissive")

    assert strict.redacted == "Email [EMAIL_1], site [URL_1], UID [UID_1]"
    assert permissive.redacted == "Email [EMAIL_1], site https://example.ch, UID CHE-100.155.212"


def test_redact_audit_reports_overlap_conflicts_without_values() -> None:
    result = redact("Invoice CHE-107.787.577 IVA")

    assert result.audit["conflicts"] == [
        {
            "kept": {
                "start": 8,
                "end": 27,
                "label": "VAT_ID",
                "source": "rule",
                "rule_id": "ch_vat_uid_suffix_v1",
                "confidence": 1.0,
            },
            "dropped": {
                "start": 8,
                "end": 23,
                "label": "UID",
                "source": "rule",
                "rule_id": "ch_uid_mod11_v1",
                "confidence": 1.0,
            },
            "reason": "overlap_precedence",
        }
    ]
