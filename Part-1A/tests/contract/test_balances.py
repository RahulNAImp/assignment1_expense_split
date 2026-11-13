"""US4 - Balances. AC-020, AC-022, AC-023 (AC-021 lives in tests/property)."""


def test_ac020_balances_human_output(goa):
    goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "900", "--desc", "Dinner")
    goa("expense", "add", "goa", "--paid-by", "asha", "--amount", "300", "--desc", "Cab")
    r = goa("balances", "goa")
    assert r.code == 0
    assert [ln.split() for ln in r.lines] == [
        ["asha", "-100.00"],
        ["meera", "-400.00"],
        ["ravi", "+500.00"],
    ]


def test_ac022_balances_json_shape(goa):
    goa("expense", "add", "goa", "--paid-by", "ravi", "--amount", "900", "--desc", "Dinner")
    goa("expense", "add", "goa", "--paid-by", "asha", "--amount", "300", "--desc", "Cab")
    r = goa("balances", "goa", "--json")
    assert r.json() == [
        {"member": "asha", "balance": "-100.00", "balance_paise": -10000},
        {"member": "meera", "balance": "-400.00", "balance_paise": -40000},
        {"member": "ravi", "balance": "500.00", "balance_paise": 50000},
    ]


def test_ac023_no_expenses_all_zero(goa):
    assert goa("balances", "goa", "--json").json() == [
        {"member": "asha", "balance": "0.00", "balance_paise": 0},
        {"member": "meera", "balance": "0.00", "balance_paise": 0},
        {"member": "ravi", "balance": "0.00", "balance_paise": 0},
    ]
    r = goa("balances", "goa")
    assert [ln.split() for ln in r.lines] == [["asha", "0.00"], ["meera", "0.00"], ["ravi", "0.00"]]
