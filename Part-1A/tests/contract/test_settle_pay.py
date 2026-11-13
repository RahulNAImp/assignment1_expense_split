"""US5 - Settle up and record payments. AC-024 ... AC-032 (AC-027 also in tests/property)."""

from tests.conftest import balances


def seed_ac025(cli):
    # asha +600, meera -100, ravi -500
    r = cli(
        "expense",
        "add",
        "goa",
        "--paid-by",
        "asha",
        "--amount",
        "600",
        "--desc",
        "Hotel",
        "--split",
        "exact",
        "--shares",
        "meera=100,ravi=500",
    )
    assert r.code == 0, r.err
    assert balances(cli) == {"asha": 60000, "meera": -10000, "ravi": -50000}


def test_ac024_ac025_greedy_largest_first(goa):
    seed_ac025(goa)
    r = goa("settle", "goa")
    assert r.code == 0
    assert r.lines == ["ravi -> asha 500.00", "meera -> asha 100.00"]


def test_ac026_four_members_with_ties(cli):
    cli("group", "create", "trip", "--members", "a,b,c,d")
    cli(
        "expense",
        "add",
        "trip",
        "--paid-by",
        "a",
        "--amount",
        "300",
        "--desc",
        "X",
        "--split",
        "exact",
        "--shares",
        "c=250,d=50",
    )
    cli(
        "expense",
        "add",
        "trip",
        "--paid-by",
        "b",
        "--amount",
        "200",
        "--desc",
        "Y",
        "--split",
        "exact",
        "--shares",
        "d=200",
    )
    assert balances(cli, "trip") == {"a": 30000, "b": 20000, "c": -25000, "d": -25000}
    r = cli("settle", "trip", "--json")
    assert r.json() == [
        {"from": "c", "to": "a", "amount": "250.00", "amount_paise": 25000},
        {"from": "d", "to": "b", "amount": "200.00", "amount_paise": 20000},
        {"from": "d", "to": "a", "amount": "50.00", "amount_paise": 5000},
    ]


def test_ac027_applying_transfers_clears_balances(goa):
    seed_ac025(goa)
    for t in goa("settle", "goa", "--json").json():
        r = goa("pay", "goa", "--from", t["from"], "--to", t["to"], "--amount", t["amount"])
        assert r.code == 0, r.err
    assert set(balances(goa).values()) == {0}


def test_ac028_settle_is_read_only(goa, data_file):
    seed_ac025(goa)
    before = data_file.read_bytes()
    goa("settle", "goa")
    goa("settle", "goa", "--json")
    assert data_file.read_bytes() == before


def test_ac029_all_settled(goa):
    r = goa("settle", "goa")
    assert r.code == 0
    assert r.out.strip() == "All settled up."
    assert goa("settle", "goa", "--json").json() == []


def test_ac030_pay_records_settlement(goa):
    seed_ac025(goa)
    r = goa("pay", "goa", "--from", "ravi", "--to", "asha", "--amount", "500")
    assert r.code == 0
    assert r.out.strip() == "Recorded payment ravi -> asha 500.00"
    assert balances(goa) == {"asha": 10000, "meera": -10000, "ravi": 0}


def test_ac031_cannot_pay_yourself(goa):
    r = goa("pay", "goa", "--from", "ravi", "--to", "ravi", "--amount", "5")
    assert r.code == 1
    assert "cannot pay yourself" in r.err


def test_ac032_overpayment_rejected(goa, data_file):
    seed_ac025(goa)
    before = data_file.read_bytes()
    r = goa("pay", "goa", "--from", "ravi", "--to", "asha", "--amount", "500.01")
    assert r.code == 4
    assert "payment exceeds outstanding balance" in r.err
    assert data_file.read_bytes() == before
    # receiver side: meera owes 100, asha is owed 600 -> 100.01 exceeds meera's debt
    r = goa("pay", "goa", "--from", "meera", "--to", "asha", "--amount", "100.01")
    assert r.code == 4
    # creditor paying a creditor: asha owes nothing
    r = goa("pay", "goa", "--from", "asha", "--to", "ravi", "--amount", "1")
    assert r.code == 4
    assert goa("pay", "goa", "--from", "ravi", "--to", "asha", "--amount", "500").code == 0


def test_ac032_payment_exceeding_receiver_credit(cli):
    cli("group", "create", "trip", "--members", "a,b,c")
    # a +100, b +100, c -200
    cli(
        "expense",
        "add",
        "trip",
        "--paid-by",
        "a",
        "--amount",
        "100",
        "--desc",
        "X",
        "--split",
        "exact",
        "--shares",
        "c=100",
    )
    cli(
        "expense",
        "add",
        "trip",
        "--paid-by",
        "b",
        "--amount",
        "100",
        "--desc",
        "Y",
        "--split",
        "exact",
        "--shares",
        "c=100",
    )
    r = cli("pay", "trip", "--from", "c", "--to", "a", "--amount", "150")
    assert r.code == 4
    assert "payment exceeds outstanding balance" in r.err
