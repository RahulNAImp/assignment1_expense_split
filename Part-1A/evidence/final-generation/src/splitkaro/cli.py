"""argparse adapter: commands, human/JSON output, error -> exit code (contracts/cli.md)."""

from __future__ import annotations

import argparse
import json
import sys

from splitkaro import service, storage
from splitkaro.errors import SplitKaroError
from splitkaro.money import format_paise


def _positive_int(text: str) -> int:
    if not text.isdigit() or int(text) < 1:
        raise argparse.ArgumentTypeError(f"invalid id: {text!r}")
    return int(text)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="splitkaro", description="Split group expenses exactly.")
    p.add_argument("--data", help="data file (default: $SPLITKARO_DATA or ./splitkaro.json)")
    sub = p.add_subparsers(dest="cmd", required=True)

    group = sub.add_parser("group", help="manage groups").add_subparsers(
        dest="group_cmd", required=True
    )
    g_create = group.add_parser("create")
    g_create.add_argument("name")
    g_create.add_argument("--members", required=True)
    g_list = group.add_parser("list")
    g_list.add_argument("--json", action="store_true")
    g_show = group.add_parser("show")
    g_show.add_argument("name")
    g_show.add_argument("--json", action="store_true")

    expense = sub.add_parser("expense", help="manage expenses").add_subparsers(
        dest="expense_cmd", required=True
    )
    e_add = expense.add_parser("add")
    e_add.add_argument("group")
    e_add.add_argument("--paid-by", required=True)
    e_add.add_argument("--amount", required=True)
    e_add.add_argument("--desc", required=True)
    e_add.add_argument("--split", choices=service.SPLIT_TYPES, default="equal")
    e_add.add_argument("--among")
    e_add.add_argument("--shares")
    e_list = expense.add_parser("list")
    e_list.add_argument("group")
    e_list.add_argument("--json", action="store_true")
    e_del = expense.add_parser("delete")
    e_del.add_argument("group")
    e_del.add_argument("id", type=_positive_int)

    bal = sub.add_parser("balances")
    bal.add_argument("group")
    bal.add_argument("--json", action="store_true")

    st = sub.add_parser("settle")
    st.add_argument("group")
    st.add_argument("--json", action="store_true")

    pay = sub.add_parser("pay")
    pay.add_argument("group")
    pay.add_argument("--from", dest="from_m", required=True)
    pay.add_argument("--to", dest="to_m", required=True)
    pay.add_argument("--amount", required=True)
    return p


def _emit_json(obj: object) -> None:
    print(json.dumps(obj, indent=2))


def run(args: argparse.Namespace) -> int:
    path = storage.resolve_path(args.data)
    groups = storage.load(path)
    dirty = False

    if args.cmd == "group":
        if args.group_cmd == "create":
            g = service.create_group(groups, args.name, args.members)
            dirty = True
            print(f"Created group {g.name} with {len(g.members)} members: {', '.join(g.members)}")
        elif args.group_cmd == "list":
            names = sorted(groups)
            if args.json:
                _emit_json(names)
            else:
                print("\n".join(names) if names else "No groups.")
        else:
            g = service.get_group(groups, args.name)
            if args.json:
                _emit_json(
                    {
                        "name": g.name,
                        "members": g.members,
                        "expense_count": len(g.expenses),
                        "settlement_count": len(g.settlements),
                    }
                )
            else:
                print(f"{g.name}: {', '.join(g.members)}")

    elif args.cmd == "expense":
        if args.expense_cmd == "add":
            e = service.add_expense(
                groups,
                args.group,
                args.paid_by,
                args.amount,
                args.desc,
                args.split,
                args.among,
                args.shares,
            )
            dirty = True
            print(f"Added expense {e.id} ({format_paise(e.amount_paise)}) to {args.group}")
        elif args.expense_cmd == "list":
            g = service.get_group(groups, args.group)
            if args.json:
                _emit_json(
                    [
                        {
                            "id": e.id,
                            "description": e.description,
                            "paid_by": e.paid_by,
                            "amount": format_paise(e.amount_paise),
                            "amount_paise": e.amount_paise,
                            "split_type": e.split_type,
                            "shares_paise": e.shares_paise,
                            "created_at": e.created_at,
                        }
                        for e in g.expenses
                    ]
                )
            elif not g.expenses:
                print("No expenses.")
            else:
                for e in g.expenses:
                    print(
                        f"#{e.id}  {format_paise(e.amount_paise)}  paid by {e.paid_by}  "
                        f'"{e.description}"  [{e.split_type}]'
                    )
        else:
            service.delete_expense(groups, args.group, args.id)
            dirty = True
            print(f"Deleted expense {args.id} from {args.group}")

    elif args.cmd == "balances":
        g = service.get_group(groups, args.group)
        bal = service.balances(g)
        if args.json:
            _emit_json(
                [
                    {"member": m, "balance": format_paise(v), "balance_paise": v}
                    for m, v in bal.items()
                ]
            )
        else:
            width = max(len(m) for m in bal)
            for m, v in bal.items():
                print(f"{m:<{width}}  {format_paise(v, signed=True)}")

    elif args.cmd == "settle":
        g = service.get_group(groups, args.group)
        transfers = service.settle(g)
        if args.json:
            _emit_json(
                [
                    {"from": f, "to": t, "amount": format_paise(a), "amount_paise": a}
                    for f, t, a in transfers
                ]
            )
        elif not transfers:
            print("All settled up.")
        else:
            for f, t, a in transfers:
                print(f"{f} -> {t} {format_paise(a)}")

    elif args.cmd == "pay":
        s = service.pay(groups, args.group, args.from_m, args.to_m, args.amount)
        dirty = True
        print(f"Recorded payment {s.from_member} -> {s.to_member} {format_paise(s.amount_paise)}")

    if dirty:
        storage.save(path, groups)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except SplitKaroError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
