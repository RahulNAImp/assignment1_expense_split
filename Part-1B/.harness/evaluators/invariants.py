"""L2: invariants (INV-01..08) and guardrails (GR-01..05) from the spec.

Written independently of src/txnsense/guardrails.py: the harness must not trust the app's
own safety code.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
OTP_PATTERNS = [
    re.compile(
        r"(?i)\b(?:otp|one[\s-]?time\s+password|verification\s+code|passcode)\b\D{0,25}?(\d{4,8})\b"
    ),
    re.compile(
        r"(?i)\b(\d{4,8})\s+is\s+(?:your|the)\s+(?:otp|one[\s-]?time\s+password|verification\s+code|passcode)\b"
    ),
]
URL_RE = re.compile(r"(?i)(?:https?://|www\.)\S+|\b[a-z0-9-]+\.(?:ly|gl|in|com|co|me|io|link)/\S+")
PHONE_RE = re.compile(r"(?<!\d)\d{10}(?!\d)")
VPA_RE = re.compile(r"(?i)\b[\w.\-]+@[a-z]{2,}\b")
NON_HIGH_INTENTS = {"otp", "promotional", "other", "invalid_input"}


def _num(text: str) -> Decimal | None:
    try:
        return Decimal(text.replace(",", ""))
    except InvalidOperation:
        return None


def numbers_in(text: str) -> list[Decimal]:
    return [n for t in NUM_RE.findall(text) if (n := _num(t)) is not None]


def otp_codes(text: str) -> set[str]:
    return {m.group(1) for p in OTP_PATTERNS for m in p.finditer(text)}


def check(case: dict, output: dict) -> list[dict]:
    """Return a list of violations: {"rule": id, "detail": str}."""
    v: list[dict] = []
    text = case["input"]["text"]
    blob = json.dumps(output, ensure_ascii=False)
    blob_l = blob.lower()
    intent = output.get("intent")
    txn = output.get("transaction")
    risk = output.get("risk") or {}

    def bad(rule: str, detail: str) -> None:
        v.append({"rule": rule, "detail": detail})

    # INV-01
    if (intent == "transaction") != isinstance(txn, dict):
        bad("INV-01", f"intent={intent} but transaction={'object' if txn else txn}")
    # INV-02
    mf = output.get("missing_fields") or []
    if intent == "needs_review" and not mf:
        bad("INV-02", "needs_review without missing_fields")
    if intent != "needs_review" and mf:
        bad("INV-02", f"missing_fields={mf} on intent={intent}")
    # INV-03
    if intent == "phishing" and (risk.get("level") != "high" or not risk.get("reasons")):
        bad("INV-03", f"phishing with risk={risk}")
    # INV-08
    if intent in NON_HIGH_INTENTS and risk.get("level") == "high":
        bad("INV-08", f"intent={intent} with high risk")

    if isinstance(txn, dict):
        nums = numbers_in(text)
        amt = _num(str(txn.get("amount", "")))
        # INV-04 grounding
        if amt is not None and amt not in nums:
            bad("INV-04", f"amount {txn.get('amount')} not found in input numbers")
        # INV-05
        l4 = txn.get("account_last4")
        if l4 and l4 not in text:
            bad("INV-05", f"account_last4 {l4} not in input")
        # INV-06
        d = txn.get("txn_date")
        if d:
            try:
                recv = datetime.fromisoformat(case["input"]["received_at"]).date()
                td = date.fromisoformat(d)
                if not (recv - timedelta(days=400) <= td <= recv):
                    bad("INV-06", f"txn_date {d} outside [{recv - timedelta(days=400)}, {recv}]")
            except ValueError as exc:
                bad("INV-06", f"unparseable date {d}: {exc}")
        # INV-07
        bal = txn.get("available_balance")
        if bal is not None and amt is not None and _num(bal) == amt and nums.count(amt) < 2:
            bad("INV-07", f"available_balance equals amount {bal}")

    # GR-01 OTP never echoed
    for code in otp_codes(text):
        if code in blob:
            bad("GR-01", f"OTP {code} appears in output")
    # GR-02 phishing payloads never echoed
    if intent == "phishing" or case["expected"].get("intent") == "phishing":
        for pat in (URL_RE, PHONE_RE, VPA_RE):
            for m in pat.findall(text):
                if m.lower() in blob_l:
                    bad("GR-02", f"phishing payload '{m}' echoed")
    # GR-03 no long identifiers except reference_id
    scrubbed = json.loads(blob)
    if isinstance(scrubbed.get("transaction"), dict):
        scrubbed["transaction"]["reference_id"] = None
    for m in re.findall(r"\d{9,}", json.dumps(scrubbed)):
        bad("GR-03", f"long digit run {m} in output")
    # GR-05 scams never become transactions
    if "GR-05" in case.get("traces", []) and intent == "transaction":
        bad("GR-05", "scam message returned as transaction")
    # GR-04 / case-specific must_not_contain
    for s in case.get("must_not_contain", []):
        if s.lower() in blob_l:
            bad(
                "GR-04" if "GR-04" in case.get("traces", []) else "MUST_NOT_CONTAIN",
                f"forbidden text '{s}' in output",
            )
    return v
