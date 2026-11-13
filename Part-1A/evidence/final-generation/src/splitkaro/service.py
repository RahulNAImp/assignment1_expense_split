"""Business rules (FR-001..FR-010). Pure functions over the in-memory group map."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime

from splitkaro import money
from splitkaro.errors import ConflictError, NotFoundError, ValidationError
from splitkaro.models import Expense, Group, Settlement

GROUP_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,29}$")
MEMBER_RE = re.compile(r"^[a-z][a-z0-9_]{0,19}$")
SPLIT_TYPES = ("equal", "exact", "percent")


def now() -> str:
    """Injectable clock (FR-014)."""
    fixed = os.environ.get("SPLITKARO_NOW")
    if fixed:
        return fixed
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- groups (US1)


def create_group(groups: dict[str, Group], name: str, members_csv: str) -> Group:
    if not GROUP_RE.match(name):
        raise ValidationError(f"invalid group name: {name!r}")
    members: list[str] = []
    for raw in members_csv.split(","):
        m = raw.strip().lower()
        if not MEMBER_RE.match(m):
            raise ValidationError(f"invalid member name: {raw!r}")
        if m in members:
            raise ValidationError(f"duplicate member: {m}")
        members.append(m)
    if not 2 <= len(members) <= 20:
        raise ValidationError("a group needs 2 to 20 members")
    if name in groups:
        raise ConflictError(f"group {name} already exists")
    group = Group(name=name, members=sorted(members), created_at=now())
    groups[name] = group
    return group


def get_group(groups: dict[str, Group], name: str) -> Group:
    if name not in groups:
        raise NotFoundError(f"group {name} not found")
    return groups[name]


def _member(group: Group, name: str) -> str:
    m = name.strip().lower()
    if m not in group.members:
        raise NotFoundError(f"member {m} not found in group {group.name}")
    return m


# ---------------------------------------------------------------- expenses (US2, US3, US6)


def _parse_shares(group: Group, shares_csv: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for part in shares_csv.split(","):
        if "=" not in part:
            raise ValidationError(f"invalid share: {part!r} (expected name=value)")
        name, value = part.split("=", 1)
        m = _member(group, name)
        if m in parsed:
            raise ValidationError(f"duplicate member in shares: {m}")
        parsed[m] = value.strip()
    return parsed


def add_expense(
    groups: dict[str, Group],
    group_name: str,
    paid_by: str,
    amount: str,
    description: str,
    split: str = "equal",
    among: str | None = None,
    shares: str | None = None,
) -> Expense:
    group = get_group(groups, group_name)
    payer = _member(group, paid_by)
    amount_paise = money.parse_amount(amount)
    desc = description.strip()
    if not desc or len(desc) > 100:
        raise ValidationError("invalid description (1-100 characters)")
    if split not in SPLIT_TYPES:
        raise ValidationError(f"invalid split type: {split}")

    if split == "equal":
        if shares is not None:
            raise ValidationError("--shares is not allowed with equal split")
        participants = group.members
        if among is not None:
            participants = []
            for raw in among.split(","):
                m = _member(group, raw)
                if m not in participants:
                    participants.append(m)
        allocation = money.allocate_equal(amount_paise, participants)
    else:
        if among is not None:
            raise ValidationError("--among is only allowed with equal split")
        if shares is None:
            raise ValidationError("--shares is required for exact/percent split")
        raw_shares = _parse_shares(group, shares)
        if split == "exact":
            allocation = {}
            for m, v in raw_shares.items():
                try:
                    allocation[m] = money.parse_amount(v)
                except ValidationError:
                    raise ValidationError(f"share for {m} must be positive") from None
            total = sum(allocation.values())
            if total != amount_paise:
                raise ValidationError(
                    f"shares total {money.format_paise(total)} does not match amount "
                    f"{money.format_paise(amount_paise)}"
                )
        else:
            bps = {}
            for m, v in raw_shares.items():
                bp = money.parse_percent(v)
                if bp <= 0:
                    raise ValidationError(f"share for {m} must be positive")
                bps[m] = bp
            if sum(bps.values()) != 10_000:
                raise ValidationError("percentages must sum to 100")
            allocation = money.allocate_percent(amount_paise, bps)

    expense = Expense(
        id=group.next_expense_id,
        description=desc,
        paid_by=payer,
        amount_paise=amount_paise,
        split_type=split,
        shares_paise=dict(sorted(allocation.items())),
        created_at=now(),
    )
    group.expenses.append(expense)
    group.next_expense_id += 1
    return expense


def delete_expense(groups: dict[str, Group], group_name: str, expense_id: int) -> Expense:
    group = get_group(groups, group_name)
    for e in group.expenses:
        if e.id == expense_id:
            if group.settlements:
                raise ConflictError("cannot delete expense after settlements")
            group.expenses.remove(e)
            return e
    raise NotFoundError(f"expense {expense_id} not found in group {group.name}")


# ---------------------------------------------------------------- balances & settle (US4, US5)


def balances(group: Group) -> dict[str, int]:
    bal = dict.fromkeys(group.members, 0)
    for e in group.expenses:
        bal[e.paid_by] += e.amount_paise
        for m, share in e.shares_paise.items():
            bal[m] -= share
    for s in group.settlements:
        bal[s.from_member] += s.amount_paise
        bal[s.to_member] -= s.amount_paise
    return dict(sorted(bal.items()))


def settle(group: Group) -> list[tuple[str, str, int]]:
    """Deterministic greedy settle-up (AC-024)."""
    bal = balances(group)
    transfers: list[tuple[str, str, int]] = []
    while True:
        debtors = [(-v, m) for m, v in bal.items() if v < 0]
        creditors = [(v, m) for m, v in bal.items() if v > 0]
        if not debtors or not creditors:
            break
        debt, debtor = min(debtors, key=lambda x: (-x[0], x[1]))
        credit, creditor = min(creditors, key=lambda x: (-x[0], x[1]))
        amount = min(debt, credit)
        transfers.append((debtor, creditor, amount))
        bal[debtor] += amount
        bal[creditor] -= amount
    return transfers


def pay(
    groups: dict[str, Group], group_name: str, from_m: str, to_m: str, amount: str
) -> Settlement:
    group = get_group(groups, group_name)
    sender = _member(group, from_m)
    receiver = _member(group, to_m)
    if sender == receiver:
        raise ValidationError("cannot pay yourself")
    amount_paise = money.parse_amount(amount)
    bal = balances(group)
    if amount_paise > -bal[sender] or amount_paise > bal[receiver]:
        raise ConflictError("payment exceeds outstanding balance")
    s = Settlement(sender, receiver, amount_paise, now())
    group.settlements.append(s)
    return s
