"""Deterministic guardrails (Constitution III; spec FR-006, GR-01..GR-03, INV-01/02, AC-17)."""

from __future__ import annotations

import re

MAX_LEN = 1000
OTP_RE = re.compile(
    r"(?i)(?:otp|one[- ]time|verification code|passcode)\D{0,20}(\d{4,8})|(\d{4,8})\D{0,20}"
    r"(?:is your|is the)\s+(?:otp|one[- ]time|verification code|passcode)"
)
URL_RE = re.compile(r"(?i)\b(?:https?://\S+|www\.\S+|[a-z0-9-]+\.(?:ly|in|com|co|me|io)/\S*)")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[- ]?)?\d{10}(?!\d)")
VPA_RE = re.compile(r"(?i)\b[\w.\-]+@[a-z]{2,}\b")
LONG_DIGITS_RE = re.compile(r"\d{9,}")


def validate_input(text: str) -> str | None:
    """Return a reason if the input is invalid (AC-17), else None."""
    if not text or not text.strip():
        return "empty message"
    if len(text) > MAX_LEN:
        return f"message longer than {MAX_LEN} characters"
    return None


def invalid_input_result(reason: str) -> dict:
    return {
        "intent": "invalid_input",
        "transaction": None,
        "missing_fields": [],
        "risk": {"level": "none", "reasons": []},
        "summary": f"Input rejected: {reason}.",
        "confidence": 1.0,
    }


def find_otps(text: str) -> set[str]:
    found = set()
    for m in OTP_RE.finditer(text):
        found.update(g for g in m.groups() if g)
    return found


def _scrub(value: str, secrets: set[str], phishing: bool) -> str:
    for s in secrets:
        value = value.replace(s, "[redacted]")
    if phishing:
        value = URL_RE.sub("[link removed]", value)
        value = PHONE_RE.sub("[number removed]", value)
        value = VPA_RE.sub("[id removed]", value)
    return value


def apply(result: dict, sms_text: str) -> dict:
    """Post-process a schema-valid model result."""
    otps = find_otps(sms_text)
    phishing = result.get("intent") == "phishing"

    # INV-01 consistency
    if result["intent"] != "transaction":
        result["transaction"] = None
    # INV-02 consistency
    if result["intent"] != "needs_review":
        result["missing_fields"] = []

    # INV-03: phishing is always high risk
    if phishing:
        result["risk"]["level"] = "high"
        if not result["risk"]["reasons"]:
            result["risk"]["reasons"] = ["Message shows common phishing patterns."]

    # GR-01 / GR-02 on every free-text field
    result["summary"] = _scrub(result["summary"], otps, phishing)
    result["risk"]["reasons"] = [_scrub(r, otps, phishing) for r in result["risk"]["reasons"]]
    txn = result.get("transaction")
    if txn:
        for key in ("counterparty", "reference_id"):
            if isinstance(txn.get(key), str):
                txn[key] = _scrub(txn[key], otps, phishing)
        # GR-03: mask long digit runs outside reference_id
        if isinstance(txn.get("counterparty"), str):
            txn["counterparty"] = LONG_DIGITS_RE.sub("[number removed]", txn["counterparty"])
    result["summary"] = LONG_DIGITS_RE.sub("[number removed]", result["summary"])
    return result
