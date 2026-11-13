"""Output schema contract (spec SCH / contracts/output.schema.json)."""

from __future__ import annotations

import json
from functools import lru_cache

from jsonschema import Draft202012Validator

from txnsense.config import PROJECT_ROOT

SCHEMA_PATH = (
    PROJECT_ROOT / "specs" / "001-sms-transaction-extractor" / "contracts" / "output.schema.json"
)


@lru_cache(maxsize=1)
def validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA_PATH.read_text()))


def schema_errors(obj: object) -> list[str]:
    return [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in validator().iter_errors(obj)
    ]
