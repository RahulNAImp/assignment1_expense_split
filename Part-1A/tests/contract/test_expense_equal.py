"""US2 - Equal split expenses. AC-007 ... AC-013."""

import pytest

from tests.conftest import balances


def shares(cli, expense_id=1, group="goa"):
    rows = cli("expense", "list", group, "--json").json()
    row = next(e for e in rows if e["id"] == expense_id)
    return row["shares_paise"]


def test_ac007_equal_split_default(goa):
    r = goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "900", "--desc", "Dinner")
    assert r.code == 0
    assert r.out.strip() == "Added expense 1 (900.00) to goa"
    rows = goa("expense", "list", "goa", "--json").json()
    assert rows[0]["split_type"] == "equal"
    assert rows[0]["shares_paise"] == {"asha": 30000, "meera": 30000, "ravi": 30000}


def test_ac008_remainder_alphabetical_not_payer(goa):
    goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "100.00", "--desc", "Snacks")
    s = shares(goa)
    assert s == {"asha": 3334, "meera": 3333, "ravi": 3333}
    assert sum(s.values()) == 10000


def test_ac009_among_subset(goa):
    goa(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "asha",
        "--amount",
        "500",
        "--desc",
        "Taxi",
        "--among",
        "asha,ravi",
    )
    assert shares(goa) == {"asha": 25000, "ravi": 25000}
    assert balances(goa)["meera"] == 0


@pytest.mark.parametrize(
    "amount", ["0", "-5", "10.999", "abc", "1,000", "1000000.01", "", "0.00", "1e3"]
)
def test_ac010_invalid_amounts(goa, amount):
    r = goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", amount, "--desc", "X")
    assert r.code == 1
    assert "invalid amount" in r.err
    assert goa("expense", "list", "goa", "--json").json() == []


def test_ac010_upper_bound_inclusive(goa):
    r = goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "1000000.00", "--desc", "X")
    assert r.code == 0


def test_ac011_unknown_member(goa):
    r = goa("expense", "add", "goa", "--paid-by", "karan", "--amount", "10", "--desc", "X")
    assert r.code == 3
    assert "member karan not found in group goa" in r.err
    r = goa(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "ravi",
        "--amount",
        "10",
        "--desc",
        "X",
        "--among",
        "ravi,karan",
    )
    assert r.code == 3
    assert "member karan not found in group goa" in r.err


def test_ac012_unknown_group(goa):
    r = goa("expense", "add", "manali", "--paid-by", "ravi", "--amount", "10", "--desc", "X")
    assert r.code == 3
    assert "group manali not found" in r.err


@pytest.mark.parametrize("desc", ["", "   ", "x" * 101])
def test_ac013_invalid_description(goa, desc):
    r = goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "10", "--desc", desc)
    assert r.code == 1
    assert "invalid description" in r.err


def test_ac013_description_boundary_100_ok(goa):
    r = goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "10", "--desc", "x" * 100)
    assert r.code == 0
