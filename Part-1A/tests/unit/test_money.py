"""Unit tests for money handling (Constitution II; FR-003, FR-004; AC-008, AC-010, AC-018)."""

import pytest

from splitkaro.errors import ValidationError
from splitkaro.money import (
    allocate_equal,
    allocate_percent,
    format_paise,
    parse_amount,
    parse_percent,
)


@pytest.mark.parametrize(
    ("text", "paise"),
    [
        ("1", 100),
        ("0.5", 50),
        ("0.01", 1),
        ("10.05", 1005),
        ("1000000.00", 100_000_000),
        ("007.10", 710),
    ],
)
def test_parse_amount_valid(text, paise):
    assert parse_amount(text) == paise


@pytest.mark.parametrize(
    "text",
    [
        "0",
        "0.00",
        "-1",
        "+1",
        "1.234",
        ".5",
        "5.",
        "1e2",
        "nan",
        "1 000",
        "1000000.01",
        "",
        " 5",
        "₹5",
    ],
)
def test_parse_amount_invalid(text):
    with pytest.raises(ValidationError, match="invalid amount"):
        parse_amount(text)


@pytest.mark.parametrize(
    ("paise", "text"),
    [(0, "0.00"), (5, "0.05"), (-5, "-0.05"), (10000, "100.00"), (-123456, "-1234.56")],
)
def test_format_paise(paise, text):
    assert format_paise(paise) == text


def test_format_paise_signed():
    assert format_paise(50000, signed=True) == "+500.00"
    assert format_paise(-1, signed=True) == "-0.01"
    assert format_paise(0, signed=True) == "0.00"


def test_parse_percent():
    assert parse_percent("50") == 5000
    assert parse_percent("33.33") == 3333
    with pytest.raises(ValidationError):
        parse_percent("33.333")


def test_allocate_equal_remainder_alphabetical():
    assert allocate_equal(10000, ["ravi", "asha", "meera"]) == {
        "asha": 3334,
        "meera": 3333,
        "ravi": 3333,
    }
    assert allocate_equal(2, ["c", "b", "a"]) == {"a": 1, "b": 1, "c": 0}
    assert allocate_equal(1, ["x", "y", "z"]) == {"x": 1, "y": 0, "z": 0}


def test_allocate_percent_floor_then_remainder():
    assert allocate_percent(10001, {"ravi": 5000, "asha": 5000}) == {"asha": 5001, "ravi": 5000}
    assert allocate_percent(100000, {"a": 3333, "b": 3333, "c": 3334}) == {
        "a": 33330,
        "b": 33330,
        "c": 33340,
    }
    # 0.10 split 3 ways by 33.33/33.33/33.34 -> floors 3,3,3 ; 1 paisa to 'a'
    assert allocate_percent(10, {"a": 3333, "b": 3333, "c": 3334}) == {"a": 4, "b": 3, "c": 3}


def test_money_module_never_uses_float():
    import inspect

    import splitkaro.money as m

    src = inspect.getsource(m)
    assert "float(" not in src
