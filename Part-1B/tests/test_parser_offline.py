"""Deterministic unit tests (gate Q1) with a fake LLM client: no network, no API key."""

from __future__ import annotations

import json

import pytest

from txnsense import guardrails
from txnsense.parser import parse_sms
from txnsense.schema import schema_errors

R = "2026-11-13T09:00:00+05:30"


class FakeClient:
    model = "fake"

    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)
        self.calls = 0

    def generate(self, system: str, user: str) -> str:
        self.calls += 1
        return self.responses.pop(0)


def ok_txn(**over) -> dict:
    base = {
        "intent": "transaction",
        "transaction": {
            "direction": "debit",
            "amount": "450.00",
            "currency": "INR",
            "channel": "upi",
            "counterparty": "Swiggy",
            "category": "food",
            "account_last4": "1234",
            "txn_date": "2026-11-12",
            "reference_id": "432112345678",
            "available_balance": None,
        },
        "missing_fields": [],
        "risk": {"level": "none", "reasons": []},
        "summary": "Paid 450.00 to Swiggy via UPI.",
        "confidence": 0.9,
    }
    base.update(over)
    return base


@pytest.mark.parametrize("text", ["", "   ", "x" * 1001])
def test_ac17_invalid_input_never_calls_model(text):
    client = FakeClient()
    out = parse_sms(text, R, client=client)
    assert out["intent"] == "invalid_input"
    assert client.calls == 0
    assert schema_errors(out) == []


def test_valid_response_passes_through():
    client = FakeClient(json.dumps(ok_txn()))
    out = parse_sms("Rs.450.00 debited ... swiggy", R, client=client)
    assert out["intent"] == "transaction"
    assert out["transaction"]["amount"] == "450.00"
    assert schema_errors(out) == []


def test_fr007_retry_once_then_needs_review():
    client = FakeClient("not json", json.dumps({"intent": "bogus"}))
    out = parse_sms("Rs 10 debited", R, client=client)
    assert client.calls == 2
    assert out["intent"] == "needs_review"
    assert out["missing_fields"] == ["model_output"]
    assert schema_errors(out) == []


def test_fr007_retry_recovers():
    client = FakeClient("{oops", json.dumps(ok_txn()))
    out = parse_sms("Rs.450.00 debited", R, client=client)
    assert out["intent"] == "transaction"
    assert client.calls == 2


def test_gr01_otp_scrubbed_everywhere():
    sms = "OTP 482913 for txn of Rs 2,499.00 at FLIPKART"
    leaky = ok_txn(summary="OTP 482913 used for Flipkart payment")
    out = parse_sms(sms, R, client=FakeClient(json.dumps(leaky)))
    assert "482913" not in json.dumps(out)


def test_gr02_phishing_payload_removed_and_high_risk():
    sms = "KYC expired, update at bit.ly/abc or call 9876543210"
    model = {
        "intent": "phishing",
        "transaction": None,
        "missing_fields": [],
        "risk": {"level": "low", "reasons": ["asks to visit bit.ly/abc"]},
        "summary": "Scam asking to call 9876543210",
        "confidence": 0.8,
    }
    out = parse_sms(sms, R, client=FakeClient(json.dumps(model)))
    dumped = json.dumps(out)
    assert "bit.ly" not in dumped and "9876543210" not in dumped
    assert out["risk"]["level"] == "high"


def test_inv01_inv02_consistency_enforced():
    model = ok_txn(intent="otp", missing_fields=["amount"])
    out = parse_sms("123456 is your OTP", R, client=FakeClient(json.dumps(model)))
    assert out["transaction"] is None
    assert out["missing_fields"] == []


def test_find_otps():
    assert guardrails.find_otps("834221 is your OTP for login") == {"834221"}
    assert guardrails.find_otps("Your OTP is 4821") == {"4821"}
    assert guardrails.find_otps("Rs 500 debited") == set()


def test_inv01_partial_transaction_on_needs_review_is_normalised_not_rejected():
    """Acceptance H06: needs_review + partial transaction (amount=null) keeps the real reason."""
    model = {
        "intent": "needs_review",
        "transaction": {
            "direction": "debit",
            "amount": None,
            "currency": "INR",
            "channel": "card",
            "counterparty": "AMAZON",
            "category": "shopping",
            "account_last4": "7712",
            "txn_date": "2026-11-13",
            "reference_id": None,
            "available_balance": None,
        },
        "missing_fields": ["amount"],
        "risk": {"level": "none", "reasons": []},
        "summary": "Card transaction at AMAZON detected, but the amount is missing.",
        "confidence": 0.9,
    }
    client = FakeClient(json.dumps(model))
    out = parse_sms("Your HDFC Bank Credit Card XX7712 has been used at AMAZON.", R, client=client)
    assert client.calls == 1
    assert out["intent"] == "needs_review"
    assert out["missing_fields"] == ["amount"]
    assert out["transaction"] is None
    assert schema_errors(out) == []


def test_transaction_intent_with_invalid_object_still_rejected():
    """Normalisation must not hide a broken transaction: intent=transaction + amount=null fails."""
    bad = ok_txn()
    bad["transaction"]["amount"] = None
    client = FakeClient(json.dumps(bad), json.dumps(bad))
    out = parse_sms("Rs debited", R, client=client)
    assert out["missing_fields"] == ["model_output"]
