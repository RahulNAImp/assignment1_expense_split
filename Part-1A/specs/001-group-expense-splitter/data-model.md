# Data Model: SplitKaro

## Group
| Field | Type | Rules |
|-------|------|-------|
| name | str | `^[a-z0-9][a-z0-9-]{0,29}$`, unique (AC-002, AC-005) |
| members | list[str] | 2–20, unique, lower-case, `^[a-z][a-z0-9_]{0,19}$`, sorted (AC-001, AC-003–005) |
| next_expense_id | int | starts at 1, only increases (AC-034) |
| expenses | list[Expense] | ascending id |
| settlements | list[Settlement] | append-only |
| created_at | str | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ` |

## Expense
| Field | Type | Rules |
|-------|------|-------|
| id | int | ≥ 1, unique within group |
| description | str | 1–100 chars after trim (AC-013) |
| paid_by | str | member of group (AC-011) |
| amount_paise | int | 1 … 100 000 000 (AC-010) |
| split_type | str | `equal` \| `exact` \| `percent` |
| shares | dict[str, int] | keys ⊆ members; Σ values == amount_paise (FR-004/005) |
| created_at | str | ISO-8601 UTC |

## Settlement
| Field | Type | Rules |
|-------|------|-------|
| from | str | member, ≠ to (AC-031) |
| to | str | member |
| amount_paise | int | > 0 and ≤ min(debt(from), credit(to)) (AC-032) |
| created_at | str | ISO-8601 UTC |

## Derived: Balance
`balance(m) = Σ amount(e where paid_by=m) − Σ shares[m] + Σ settlements from m − Σ settlements to m`
Invariant: `Σ balance(m) == 0` for every group (AC-021).

## File layout
```json
{"version": 1, "groups": {"goa": {"name": "goa", "members": ["asha","meera","ravi"],
  "next_expense_id": 2, "expenses": [...], "settlements": [...], "created_at": "..."}}}
```
Any deviation (missing key, wrong type, unknown version) ⇒ corrupt ⇒ exit 5 (AC-038).
