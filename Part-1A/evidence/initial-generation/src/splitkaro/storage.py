"""JSON persistence with structural validation and atomic writes (FR-011, AC-037..AC-040)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from splitkaro.errors import StorageError
from splitkaro.models import Group

DEFAULT_FILE = "splitkaro.json"
VERSION = 1

_GROUP_KEYS = {
    "name": str,
    "members": list,
    "next_expense_id": int,
    "expenses": list,
    "settlements": list,
    "created_at": str,
}
_EXPENSE_KEYS = {
    "id": int,
    "description": str,
    "paid_by": str,
    "amount_paise": int,
    "split_type": str,
    "shares_paise": dict,
    "created_at": str,
}
_SETTLEMENT_KEYS = {"from": str, "to": str, "amount_paise": int, "created_at": str}


def resolve_path(flag: str | None) -> Path:
    return Path(flag or os.environ.get("SPLITKARO_DATA") or DEFAULT_FILE)


def _check(obj: object, schema: dict[str, type]) -> None:
    if not isinstance(obj, dict):
        raise ValueError("expected object")
    for key, typ in schema.items():
        if key not in obj or not isinstance(obj[key], typ) or isinstance(obj[key], bool):
            raise ValueError(f"bad field {key}")


def _validate(raw: object) -> dict[str, Group]:
    if not isinstance(raw, dict) or raw.get("version") != VERSION:
        raise ValueError("bad root")
    groups_raw = raw.get("groups")
    if not isinstance(groups_raw, dict):
        raise ValueError("bad groups")
    groups: dict[str, Group] = {}
    for name, g in groups_raw.items():
        _check(g, _GROUP_KEYS)
        for e in g["expenses"]:
            _check(e, _EXPENSE_KEYS)
        for s in g["settlements"]:
            _check(s, _SETTLEMENT_KEYS)
        groups[name] = Group.from_dict(g)
    return groups


def load(path: Path) -> dict[str, Group]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return _validate(raw)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise StorageError(f"data file is corrupt: {path}") from exc


def save(path: Path, groups: dict[str, Group]) -> None:
    payload = {"version": VERSION, "groups": {n: g.to_dict() for n, g in sorted(groups.items())}}
    directory = path.parent if str(path.parent) else Path(".")
    directory.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".splitkaro-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except OSError as exc:
        Path(tmp).unlink(missing_ok=True)
        raise StorageError(f"cannot write data file: {path}") from exc
