"""Shared fixtures for spec-derived tests (T008).

Tests call the CLI in-process through ``splitkaro.cli.main`` and assert exact stdout, stderr and
exit codes as defined in specs/001-group-expense-splitter/spec.md and contracts/cli.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

FIXED_NOW = "2026-11-13T10:00:00Z"


@dataclass
class Result:
    code: int
    out: str
    err: str

    @property
    def lines(self) -> list[str]:
        return [ln for ln in self.out.splitlines() if ln.strip()]

    def json(self):
        return json.loads(self.out)


@pytest.fixture
def data_file(tmp_path: Path) -> Path:
    return tmp_path / "splitkaro.json"


@pytest.fixture
def cli(data_file: Path, capsys, monkeypatch):
    """Run the CLI with ``--data <tmp file>`` and a fixed clock."""
    from splitkaro.cli import main

    monkeypatch.setenv("SPLITKARO_NOW", FIXED_NOW)
    monkeypatch.delenv("SPLITKARO_DATA", raising=False)

    def run(*args: str, use_data_flag: bool = True) -> Result:
        argv = (["--data", str(data_file)] if use_data_flag else []) + list(args)
        capsys.readouterr()
        try:
            code = main(argv)
        except SystemExit as exc:  # argparse usage errors
            code = exc.code if isinstance(exc.code, int) else 2
        captured = capsys.readouterr()
        return Result(code=code, out=captured.out, err=captured.err)

    return run


@pytest.fixture
def goa(cli):
    """Reference group from the spec: goa = asha, meera, ravi."""
    r = cli("group", "create", "goa", "--members", "ravi,asha,meera")
    assert r.code == 0, r.err
    return cli


def balances(cli, group: str = "goa") -> dict[str, int]:
    r = cli("balances", group, "--json")
    assert r.code == 0, r.err
    return {row["member"]: row["balance_paise"] for row in r.json()}
