"""Property tests for invariants (SC-002): AC-021 conservation, AC-027 settle-up property,
and the share-sum invariant (FR-004). Runs >= 500 generated command sequences."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from splitkaro.cli import main

MEMBERS = ["asha", "bala", "chitra", "dev", "esha", "farhan"]


def run(data: str, *args: str) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(["--data", data, *args])
        except SystemExit as exc:  # pragma: no cover - argparse
            code = exc.code
    return code, out.getvalue()


expense_st = st.tuples(
    st.integers(min_value=0, max_value=5),  # payer index
    st.integers(min_value=1, max_value=5_000_000),  # amount in paise
    st.lists(st.integers(min_value=0, max_value=5), min_size=1, max_size=6, unique=True),
)


@settings(max_examples=500, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(n=st.integers(min_value=2, max_value=6), expenses=st.lists(expense_st, max_size=8))
def test_ac021_ac027_conservation_and_settle_property(n, expenses):
    os.environ["SPLITKARO_NOW"] = "2026-11-13T10:00:00Z"
    members = MEMBERS[:n]
    with tempfile.TemporaryDirectory() as d:
        data = os.path.join(d, "s.json")
        assert run(data, "group", "create", "g", "--members", ",".join(members))[0] == 0
        for payer_i, paise, among_i in expenses:
            payer = members[payer_i % n]
            among = sorted({members[i % n] for i in among_i})
            amount = f"{paise // 100}.{paise % 100:02d}"
            code, _ = run(
                data,
                "expense",
                "add",
                "g",
                "--paid-by",
                payer,
                "--amount",
                amount,
                "--desc",
                "p",
                "--among",
                ",".join(among),
            )
            assert code == 0

        # share-sum invariant (FR-004)
        for e in json.loads(run(data, "expense", "list", "g", "--json")[1]):
            assert sum(e["shares_paise"].values()) == e["amount_paise"]

        # AC-021 conservation
        bal = json.loads(run(data, "balances", "g", "--json")[1])
        assert sum(b["balance_paise"] for b in bal) == 0

        # AC-027 settle property
        transfers = json.loads(run(data, "settle", "g", "--json")[1])
        assert len(transfers) <= n - 1
        assert all(t["amount_paise"] > 0 for t in transfers)
        for t in transfers:
            code, _ = run(
                data, "pay", "g", "--from", t["from"], "--to", t["to"], "--amount", t["amount"]
            )
            assert code == 0
        bal = json.loads(run(data, "balances", "g", "--json")[1])
        assert all(b["balance_paise"] == 0 for b in bal)
        assert json.loads(run(data, "settle", "g", "--json")[1]) == []
