"""L1: structural validation against the spec's JSON Schema contract (SCH)."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "specs" / "001-sms-transaction-extractor" / "contracts" / "output.schema.json"
_VALIDATOR = Draft202012Validator(json.loads(SCHEMA.read_text()))


def check(output: object) -> list[str]:
    return [
        f"SCH {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in _VALIDATOR.iter_errors(output)
    ]
