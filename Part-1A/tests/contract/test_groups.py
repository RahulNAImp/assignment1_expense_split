"""US1 - Create a group. AC-001 ... AC-006."""


def test_ac001_create_group_sorts_members(cli):
    r = cli("group", "create", "goa", "--members", "ravi,asha,meera")
    assert r.code == 0
    assert r.out.strip() == "Created group goa with 3 members: asha, meera, ravi"
    show = cli("group", "show", "goa", "--json").json()
    assert show["members"] == ["asha", "meera", "ravi"]


def test_ac002_duplicate_group_is_conflict(goa):
    r = goa("group", "create", "goa", "--members", "x,y")
    assert r.code == 4
    assert "group goa already exists" in r.err


def test_ac003_member_count_bounds(cli):
    r = cli("group", "create", "solo", "--members", "asha")
    assert r.code == 1
    assert "a group needs 2 to 20 members" in r.err
    many = ",".join(f"m{i:02d}" for i in range(21))
    r = cli("group", "create", "big", "--members", many)
    assert r.code == 1
    assert "a group needs 2 to 20 members" in r.err
    ok = ",".join(f"m{i:02d}" for i in range(20))
    assert cli("group", "create", "big", "--members", ok).code == 0


def test_ac004_duplicate_member_case_insensitive(cli):
    r = cli("group", "create", "goa", "--members", "asha,Asha,ravi")
    assert r.code == 1
    assert "duplicate member: asha" in r.err


def test_ac005_invalid_names(cli):
    r = cli("group", "create", "Goa Trip", "--members", "asha,ravi")
    assert r.code == 1
    assert "invalid group name" in r.err
    r = cli("group", "create", "goa", "--members", "asha,9ravi")
    assert r.code == 1
    assert "invalid member name" in r.err


def test_ac006_group_list_json_sorted(cli):
    cli("group", "create", "zoo", "--members", "a,b")
    cli("group", "create", "flat-12", "--members", "a,b")
    r = cli("group", "list", "--json")
    assert r.code == 0
    assert r.json() == ["flat-12", "zoo"]
