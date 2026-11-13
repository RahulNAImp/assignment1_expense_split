"""Entities from data-model.md."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Expense:
    id: int
    description: str
    paid_by: str
    amount_paise: int
    split_type: str
    shares_paise: dict[str, int]
    created_at: str


@dataclass
class Settlement:
    from_member: str
    to_member: str
    amount_paise: int
    created_at: str

    def to_dict(self) -> dict:
        return {
            "from": self.from_member,
            "to": self.to_member,
            "amount_paise": self.amount_paise,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Settlement:
        return cls(d["from"], d["to"], d["amount_paise"], d["created_at"])


@dataclass
class Group:
    name: str
    members: list[str]
    created_at: str
    next_expense_id: int = 1
    expenses: list[Expense] = field(default_factory=list)
    settlements: list[Settlement] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "members": self.members,
            "next_expense_id": self.next_expense_id,
            "expenses": [asdict(e) for e in self.expenses],
            "settlements": [s.to_dict() for s in self.settlements],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Group:
        return cls(
            name=d["name"],
            members=list(d["members"]),
            created_at=d["created_at"],
            next_expense_id=d["next_expense_id"],
            expenses=[Expense(**e) for e in d["expenses"]],
            settlements=[Settlement.from_dict(s) for s in d["settlements"]],
        )
