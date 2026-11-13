"""parse_sms(): validate, prompt, model, schema (retry once), guardrails (FR-001..FR-007)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from txnsense import guardrails
from txnsense.config import PROJECT_ROOT
from txnsense.llm import GeminiClient, LLMClient
from txnsense.schema import schema_errors

PROMPT_PATH = PROJECT_ROOT / "prompts" / "system_prompt.md"
IST = ZoneInfo("Asia/Kolkata")


def system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def prompt_version() -> str:
    return hashlib.sha256(system_prompt().encode()).hexdigest()[:12]


def _user_message(text: str, received_at: str, sender: str | None) -> str:
    return json.dumps(
        {"sms_text": text, "sender": sender, "received_at": received_at}, ensure_ascii=False
    )


def _needs_review_model_output() -> dict:
    return {
        "intent": "needs_review",
        "transaction": None,
        "missing_fields": ["model_output"],
        "risk": {"level": "none", "reasons": []},
        "summary": "Could not read this message reliably; please review it manually.",
        "confidence": 0.0,
    }


def parse_sms(
    text: str,
    received_at: str | None = None,
    sender: str | None = None,
    client: LLMClient | None = None,
) -> dict:
    reason = guardrails.validate_input(text)
    if reason:
        return guardrails.invalid_input_result(reason)

    received_at = received_at or datetime.now(IST).isoformat(timespec="seconds")
    client = client or GeminiClient()
    system = system_prompt()
    user = _user_message(text, received_at, sender)

    for _attempt in range(2):  # FR-007: one retry on schema-invalid output
        raw = client.generate(system, user)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not schema_errors(result):
            return guardrails.apply(result, text)
    return _needs_review_model_output()
