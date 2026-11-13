"""SC-004: balances and settle < 1 s for 20 members x 5 000 expenses (T031)."""

import json
import time

from splitkaro.cli import main


def test_sc004_performance(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("SPLITKARO_NOW", "2026-11-13T10:00:00Z")
    members = [f"m{i:02d}" for i in range(20)]
    expenses = []
    for i in range(5000):
        payer = members[i % 20]
        share = {m: 100 for m in members}
        expenses.append(
            {
                "id": i + 1,
                "description": "e",
                "paid_by": payer,
                "amount_paise": 2000,
                "split_type": "equal",
                "shares_paise": share,
                "created_at": "2026-11-13T10:00:00Z",
            }
        )
    data = {
        "version": 1,
        "groups": {
            "big": {
                "name": "big",
                "members": members,
                "next_expense_id": 5001,
                "expenses": expenses,
                "settlements": [],
                "created_at": "2026-11-13T10:00:00Z",
            }
        },
    }
    path = tmp_path / "big.json"
    path.write_text(json.dumps(data))
    for cmd in (["balances", "big"], ["settle", "big"]):
        start = time.perf_counter()
        assert main(["--data", str(path), *cmd]) == 0
        assert time.perf_counter() - start < 1.0
    capsys.readouterr()
