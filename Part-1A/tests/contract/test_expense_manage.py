"""US6 - List and delete expenses. AC-033 ... AC-036."""

from tests.conftest import FIXED_NOW, balances


def test_ac033_expense_list_json(goa):
    goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "900", "--desc", "Dinner")
    goa(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "asha",
        "--amount",
        "100.00",
        "--desc",
        "Chai",
        "--among",
        "asha,meera",
    )
    rows = goa("expense", "list", "goa", "--json").json()
    assert [r["id"] for r in rows] == [1, 2]
    assert rows[1] == {
        "id": 2,
        "description": "Chai",
        "paid_by": "asha",
        "amount": "100.00",
        "amount_paise": 10000,
        "split_type": "equal",
        "shares_paise": {"asha": 5000, "meera": 5000},
        "created_at": FIXED_NOW,
    }


def test_ac033_expense_list_empty_human(goa):
    r = goa("expense", "list", "goa")
    assert r.code == 0
    assert r.out.strip() == "No expenses."


def test_ac034_delete_recomputes_and_never_reuses_ids(goa):
    goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "900", "--desc", "Dinner")
    goa("expense", "add", "goa", "--paid-by", "asha", "--amount", "300", "--desc", "Cab")
    r = goa("expense", "delete", "goa", "2")
    assert r.code == 0
    assert r.out.strip() == "Deleted expense 2 from goa"
    assert balances(goa) == {"asha": -30000, "meera": -30000, "ravi": 60000}
    r = goa("expense", "add", "goa", "--paid-by", "asha", "--amount", "30", "--desc", "Tea")
    assert r.out.strip() == "Added expense 3 (30.00) to goa"


def test_ac035_delete_blocked_after_settlement(goa):
    goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "900", "--desc", "Dinner")
    assert goa("pay", "goa", "--from", "asha", "--to", "ravi", "--amount", "100").code == 0
    r = goa("expense", "delete", "goa", "1")
    assert r.code == 4
    assert "cannot delete expense after settlements" in r.err
    assert len(goa("expense", "list", "goa", "--json").json()) == 1


def test_ac036_delete_unknown_expense(goa):
    r = goa("expense", "delete", "goa", "42")
    assert r.code == 3
    assert "expense 42 not found in group goa" in r.err


def test_ac036_non_integer_id_is_usage_error(goa):
    assert goa("expense", "delete", "goa", "abc").code == 2
