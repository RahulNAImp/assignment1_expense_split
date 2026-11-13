"""Exact money handling in integer paise (Constitution II; FR-003, FR-004)."""

from __future__ import annotations

import re
from decimal import Decimal

from splitkaro.errors import ValidationError

MAX_PAISE = 100_000_000  # 1 000 000.00 INR
_AMOUNT_RE = re.compile(r"^\d{1,7}(\.\d{1,2})?$")
_PERCENT_RE = re.compile(r"^\d{1,3}(\.\d{1,2})?$")


def parse_amount(text: str) -> int:
    """Parse a positive decimal string with <= 2 fractional digits into paise (AC-010)."""
    if not _AMOUNT_RE.match(text):
        raise ValidationError(f"invalid amount: {text!r}")
    paise = int(Decimal(text) * 100)
    if paise <= 0 or paise > MAX_PAISE:
        raise ValidationError(f"invalid amount: {text!r}")
    return paise


def parse_percent(text: str) -> int:
    """Parse a percentage with <= 2 fractional digits into basis points (1% = 100)."""
    if not _PERCENT_RE.match(text):
        raise ValidationError(f"invalid percentage: {text!r}")
    return int(Decimal(text) * 100)


def format_paise(paise: int, signed: bool = False) -> str:
    sign = "-" if paise < 0 else ("+" if signed and paise > 0 else "")
    rupees, rem = divmod(abs(paise), 100)
    return f"{sign}{rupees}.{rem:02d}"


def _distribute_remainder(base: dict[str, int], remainder: int) -> dict[str, int]:
    """Give leftover paise one each to participants in alphabetical order (Clarification)."""
    names = sorted(base)
    for i in range(remainder):
        base[names[i % len(names)]] += 1
    return dict(sorted(base.items()))


def allocate_equal(amount_paise: int, members: list[str]) -> dict[str, int]:
    n = len(members)
    base = {m: amount_paise // n for m in members}
    return _distribute_remainder(base, amount_paise - sum(base.values()))


def allocate_percent(amount_paise: int, basis_points: dict[str, int]) -> dict[str, int]:
    base = {m: amount_paise * bp // 10_000 for m, bp in basis_points.items()}
    return _distribute_remainder(base, amount_paise - sum(base.values()))
