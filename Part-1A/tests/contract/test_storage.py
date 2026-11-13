"""US7 - Safe persistence. AC-037 ... AC-040."""

import json

import pytest
from splitkaro.cli import main


def test_ac037_missing_file_reads_as_empty(cli, data_file):
    r = cli("group", "list")
    assert r.code == 0
    assert r.out.strip() == "No groups."
    assert cli("group", "list", "--json").json() == []
    assert not data_file.exists()


@pytest.mark.parametrize(
    "content",
    [
        b"{not json",
        b"[]",
        b'{"version": 1}',
        b'{"version": 99, "groups": {}}',
        b'{"version": 1, "groups": {"goa": {"name": "goa"}}}',
        b'{"version": 1, "groups": {"goa": {"name": "goa", "members": ["a", "b"], '
        b'"next_expense_id": 1, "expenses": [], "settlements": [], "created_at": 5}}}',
    ],
)
@pytest.mark.parametrize(
    "command",
    [
        ["group", "list"],
        ["group", "create", "x", "--members", "a,b"],
        ["balances", "goa"],
    ],
)
def test_ac038_corrupt_file_untouched(cli, data_file, content, command):
    data_file.write_bytes(content)
    r = cli(*command)
    assert r.code == 5
    assert "data file is corrupt" in r.err
    assert "Traceback" not in r.err
    assert data_file.read_bytes() == content


def test_ac039_persists_across_runs(cli, data_file):
    cli("group", "create", "goa", "--members", "asha,ravi")
    cli("expense", "add", "goa", "--paid-by", "asha", "--amount", "10", "--desc", "X")
    stored = json.loads(data_file.read_text())
    assert stored["version"] == 1
    assert stored["groups"]["goa"]["expenses"][0]["amount_paise"] == 1000
    assert cli("balances", "goa", "--json").json()[0]["balance_paise"] == 500


def test_ac040_env_var_and_default_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SPLITKARO_NOW", "2026-11-13T10:00:00Z")
    env_file = tmp_path / "env.json"
    monkeypatch.setenv("SPLITKARO_DATA", str(env_file))
    assert main(["group", "create", "goa", "--members", "a,b"]) == 0
    assert env_file.exists()

    monkeypatch.delenv("SPLITKARO_DATA")
    workdir = tmp_path / "wd"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    assert main(["group", "create", "goa", "--members", "a,b"]) == 0
    assert (workdir / "splitkaro.json").exists()

    flag_file = tmp_path / "flag.json"
    monkeypatch.setenv("SPLITKARO_DATA", str(env_file))
    assert main(["--data", str(flag_file), "group", "create", "zoo", "--members", "a,b"]) == 0
    assert "zoo" in json.loads(flag_file.read_text())["groups"]
    assert "zoo" not in json.loads(env_file.read_text())["groups"]
    capsys.readouterr()
