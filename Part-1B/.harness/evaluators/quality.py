"""L3: semantic / quality evaluation against ground truth (spec EV-02)."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

TXN_FIELDS = ("direction", "amount", "account_last4", "txn_date", "channel", "available_balance")


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9@.]+", " ", s.lower()).split())


def similarity(a: str, b: str) -> float:
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def field_checks(case: dict, output: dict, min_sim: float) -> dict[str, dict]:
    exp = case["expected"]
    acc = case.get("accept", {})
    txn = output.get("transaction") or {}
    checks: dict[str, dict] = {}

    allowed = exp["intent"] if isinstance(exp["intent"], list) else [exp["intent"]]
    checks["intent"] = {
        "expected": allowed,
        "observed": output.get("intent"),
        "ok": output.get("intent") in allowed,
    }
    for f in TXN_FIELDS:
        if f in exp:
            obs = txn.get(f)
            checks[f] = {"expected": exp[f], "observed": obs, "ok": obs == exp[f]}
    if "missing_fields" in exp:
        obs = output.get("missing_fields") or []
        checks["missing_fields"] = {
            "expected": exp["missing_fields"],
            "observed": obs,
            "ok": set(exp["missing_fields"]) <= set(obs),
        }
    if "risk_level" in exp:
        obs = (output.get("risk") or {}).get("level")
        checks["risk_level"] = {
            "expected": exp["risk_level"],
            "observed": obs,
            "ok": obs == exp["risk_level"],
        }
    if "counterparty" in acc:
        obs = txn.get("counterparty") or ""
        best = max((similarity(obs, a) for a in acc["counterparty"]), default=0.0)
        checks["counterparty"] = {
            "expected": acc["counterparty"],
            "observed": obs,
            "similarity": round(best, 3),
            "ok": best >= min_sim,
        }
    if "category" in acc:
        obs = txn.get("category")
        checks["category"] = {
            "expected": acc["category"],
            "observed": obs,
            "ok": obs in acc["category"],
        }
    return checks


def accuracy(checks: dict[str, dict]) -> float:
    return sum(c["ok"] for c in checks.values()) / len(checks) if checks else 1.0
