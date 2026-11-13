"""US3 - Exact and percentage splits. AC-014 ... AC-019."""

import pytest


def last_shares(cli):
    return cli("expense", "list", "goa", "--json").json()[-1]["shares_paise"]


def test_ac014_exact_split(goa):
    r = goa(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "asha",
        "--amount",
        "1000",
        "--desc",
        "Rent",
        "--split",
        "exact",
        "--shares",
        "asha=500,meera=300,ravi=200",
    )
    assert r.code == 0
    assert last_shares(goa) == {"asha": 50000, "meera": 30000, "ravi": 20000}


def test_ac015_exact_mismatch(goa):
    r = goa(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "asha",
        "--amount",
        "1000",
        "--desc",
        "Rent",
        "--split",
        "exact",
        "--shares",
        "asha=500,ravi=400",
    )
    assert r.code == 1
    assert "shares total 900.00 does not match amount 1000.00" in r.err


def test_ac016_percent_split(goa):
    r = goa(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "asha",
        "--amount",
        "1000",
        "--desc",
        "Fuel",
        "--split",
        "percent",
        "--shares",
        "asha=50,meera=25,ravi=25",
    )
    assert r.code == 0
    assert last_shares(goa) == {"asha": 50000, "meera": 25000, "ravi": 25000}


def test_ac017_percent_must_sum_100(goa):
    r = goa(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "asha",
        "--amount",
        "1000",
        "--desc",
        "Fuel",
        "--split",
        "percent",
        "--shares",
        "asha=50,meera=30,ravi=10",
    )
    assert r.code == 1
    assert "percentages must sum to 100" in r.err


def test_ac018_percent_remainder_rule(goa):
    r = goa(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "ravi",
        "--amount",
        "100.01",
        "--desc",
        "Tea",
        "--split",
        "percent",
        "--shares",
        "ravi=50,asha=50",
    )
    assert r.code == 0
    assert last_shares(goa) == {"asha": 5001, "ravi": 5000}


def test_ac018_percent_with_decimals(goa):
    r = goa(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "ravi",
        "--amount",
        "1000",
        "--desc",
        "Tea",
        "--split",
        "percent",
        "--shares",
        "asha=33.33,meera=33.33,ravi=33.34",
    )
    assert r.code == 0
    assert last_shares(goa) == {"asha": 33330, "meera": 33330, "ravi": 33340}


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        (["--shares", "asha=10"], "--shares is not allowed with equal split"),
        (
            ["--split", "exact", "--among", "asha,ravi", "--shares", "asha=5,ravi=5"],
            "--among is only allowed with equal split",
        ),
        (["--split", "exact", "--shares", "asha=5,asha=5"], "duplicate member in shares: asha"),
        (["--split", "exact", "--shares", "asha=10,ravi=0"], "share for ravi must be positive"),
        (["--split", "percent", "--shares", "asha=100,ravi=0"], "share for ravi must be positive"),
    ],
)
def test_ac019_option_conflicts(goa, extra, message):
    r = goa("expense", "add", "goa", "--paid-by", "asha", "--amount", "10", "--desc", "X", *extra)
    assert r.code == 1
    assert message in r.err
