# CLI Contract: `splitkaro`

Global options (before the sub-command): `--data PATH` (AC-040).

| Command | Success stdout (human) | `--json` |
|---------|------------------------|----------|
| `group create NAME --members a,b,c` | `Created group NAME with N members: a, b, c` | – |
| `group list [--json]` | one name per line, or `No groups.` | `["goa", ...]` |
| `group show NAME [--json]` | `NAME: a, b, c` | `{"name","members","expense_count","settlement_count"}` |
| `expense add GROUP --paid-by M --amount A --desc D [--split equal\|exact\|percent] [--among a,b] [--shares a=x,b=y]` | `Added expense ID (A) to GROUP` | – |
| `expense list GROUP [--json]` | `#ID  A  paid by M  "D"  [split]` per line or `No expenses.` | array of `{id, description, paid_by, amount, amount_paise, split_type, shares_paise, created_at}` |
| `expense delete GROUP ID` | `Deleted expense ID from GROUP` | – |
| `balances GROUP [--json]` | `member  +x.xx` per line (sign always shown, `0.00` unsigned) | `[{"member","balance","balance_paise"}]` |
| `settle GROUP [--json]` | `from -> to x.xx` per line, or `All settled up.` | `[{"from","to","amount","amount_paise"}]` |
| `pay GROUP --from A --to B --amount X` | `Recorded payment A -> B X` | – |

## Exit codes
| Code | Meaning | Examples |
|------|---------|----------|
| 0 | success | |
| 1 | validation error | invalid amount, shares mismatch, cannot pay yourself |
| 2 | usage error (argparse) | unknown option, non-integer id, bad `--split` value |
| 3 | not found | unknown group / member / expense |
| 4 | conflict / business rule | duplicate group, overpayment, delete after settlement |
| 5 | storage error | corrupt data file |

Errors are printed to stderr as `error: <message>` with no traceback.
