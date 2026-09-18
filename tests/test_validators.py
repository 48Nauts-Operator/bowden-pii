from bowden_pii.rules import make_iban, make_valid_ahv, make_valid_uid
from bowden_pii.validators import (
    format_ahv,
    format_iban,
    format_swiss_vat,
    format_uid,
    is_qr_iban,
    is_valid_ahv,
    is_valid_credit_card,
    is_valid_iban,
    is_valid_swiss_phone,
    is_valid_swiss_vat,
    is_valid_uid,
    normalize_swiss_phone,
)


def test_valid_ahv_accepts_standard_and_compact_forms() -> None:
    assert is_valid_ahv("756.9217.0769.85")
    assert is_valid_ahv("7569217076985")
    assert format_ahv("7569217076985") == "756.9217.0769.85"


def test_invalid_ahv_rejects_bad_checksum_and_prefix() -> None:
    assert not is_valid_ahv("756.9217.0769.84")
    assert not is_valid_ahv("123.4567.8910.19")


def test_make_valid_ahv_generates_ean13_check_digit() -> None:
    generated = make_valid_ahv("756921707698")
    assert generated == "756.9217.0769.85"
    assert is_valid_ahv(generated)


def test_valid_iban_accepts_swiss_example() -> None:
    assert is_valid_iban("CH93 0076 2011 6238 5295 7")
    assert is_valid_iban("CH9300762011623852957")
    assert format_iban("CH9300762011623852957") == "CH93 0076 2011 6238 5295 7"


def test_invalid_iban_rejects_bad_checksum_and_length() -> None:
    assert not is_valid_iban("CH94 0076 2011 6238 5295 7")
    assert not is_valid_iban("CH93 0076")


def test_make_iban_generates_valid_value() -> None:
    generated = make_iban("CH", "00762011623852957")
    assert generated == "CH93 0076 2011 6238 5295 7"
    assert is_valid_iban(generated)


def test_qr_iban_detection_uses_qr_iid_range() -> None:
    assert is_qr_iban("CH57 3000 0123 4567 8901 2")
    assert is_qr_iban("CH06 3100 0123 4567 8901 2")
    assert not is_qr_iban("CH93 0076 2011 6238 5295 7")


def test_uid_accepts_valid_mod11_value() -> None:
    assert is_valid_uid("CHE-100.155.212")
    assert is_valid_uid("100.155.212")
    assert format_uid("CHE100155212") == "CHE-100.155.212"


def test_uid_rejects_bad_checksum() -> None:
    assert not is_valid_uid("CHE-100.155.213")


def test_make_valid_uid_generates_valid_value() -> None:
    generated = make_valid_uid("10015521")
    assert generated == "CHE-100.155.212"
    assert is_valid_uid(generated)


def test_swiss_vat_accepts_valid_uid_with_suffix() -> None:
    assert is_valid_swiss_vat("CHE-107.787.577 IVA")
    assert is_valid_swiss_vat("CHE-100.155.212 MWST")
    assert format_swiss_vat("CHE107787577IVA") == "CHE-107.787.577 IVA"


def test_swiss_vat_rejects_bad_checksum_and_missing_suffix() -> None:
    assert not is_valid_swiss_vat("CHE-107.787.578 IVA")
    assert not is_valid_swiss_vat("CHE-100.155.212")


def test_credit_card_luhn_validation() -> None:
    assert is_valid_credit_card("4111 1111 1111 1111")
    assert not is_valid_credit_card("4111 1111 1111 1112")


def test_swiss_phone_validation_and_normalization() -> None:
    assert is_valid_swiss_phone("+41 79 123 45 67")
    assert is_valid_swiss_phone("0041 44 123 45 67")
    assert is_valid_swiss_phone("079 123 45 67")
    assert normalize_swiss_phone("079 123 45 67") == "+41 79 123 45 67"
    assert not is_valid_swiss_phone("+49 30 123456")
