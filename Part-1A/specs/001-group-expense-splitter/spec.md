# Feature Specification: SplitKaro — Group Expense Splitter & Settlement CLI

**Feature Branch**: `001-group-expense-splitter`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "A command-line tool for friends/flatmates who share costs on a trip
or in a flat. Users create a group, record who paid for what and how the cost is split (equally,
by exact amounts, or by percentage), see each member's net balance, and get a short list of
payments that settles everyone up. Money must be exact to the paisa and every result must be
deterministic so it can be verified with exact tests."

## Clarifications

### Session 2026-11-13

- Q: When an equal or percentage split leaves leftover paise, who receives them? → A: One paisa
  each to the participating members in alphabetical order, independent of the payer. Applied to
  AC-008, AC-018, FR-004.
- Q: May a recorded payment exceed what the sender owes or the receiver is owed? → A: No. Reject
  with exit 4 and `payment exceeds outstanding balance`. Applied to AC-032, FR-009.
- Q: May an expense be deleted after any settlement has been recorded in the group? → A: No.
  Reject with exit 4 and `cannot delete expense after settlements`. Applied to AC-035, FR-010.

## User Scenarios & Testing *(mandatory)*

Reference group used in the scenarios below (unless stated otherwise): group `goa` with members
`asha`, `meera`, `ravi` (member order is always alphabetical).

### User Story 1 - Create a group (Priority: P1)

A user creates a named group with its members before recording any expense.

**Why this priority**: Every other story needs a group.

**Independent Test**: Run `group create` and `group show --json` against an empty data file and
compare exact output.

**Acceptance Scenarios**:

1. **AC-001** **Given** an empty data file, **When** the user runs
   `group create goa --members ravi,asha,meera`, **Then** exit code is `0`, stdout is
   `Created group goa with 3 members: asha, meera, ravi`, and the stored members are sorted
   alphabetically.
2. **AC-002** **Given** group `goa` exists, **When** the user runs `group create goa ...` again,
   **Then** exit code is `4` and stderr contains `group goa already exists`.
3. **AC-003** **Given** fewer than 2 or more than 20 distinct members, **Then** exit code is `1`
   and stderr contains `a group needs 2 to 20 members`.
4. **AC-004** **Given** a member list containing a duplicate (e.g. `asha,Asha,ravi` — names are
   lower-cased before comparison), **Then** exit code is `1` and stderr contains
   `duplicate member: asha`.
5. **AC-005** **Given** an invalid group name (must match `^[a-z0-9][a-z0-9-]{0,29}$`) or member
   name (must match `^[a-z][a-z0-9_]{0,19}$` after lower-casing), **Then** exit code is `1` and
   stderr contains `invalid group name` / `invalid member name`.
6. **AC-006** **Given** groups exist, **When** the user runs `group list --json`, **Then** stdout is
   a JSON array of group names sorted alphabetically.

---

### User Story 2 - Record an equally split expense (Priority: P1)

A member pays for something shared and the cost is divided equally.

**Why this priority**: The most common real-world action; MVP.

**Independent Test**: Create group, add one expense, check `expense list --json` shares in paise.

**Acceptance Scenarios**:

1. **AC-007** **Given** group `goa`, **When** the user runs
   `expense add goa --paid-by ravi --amount 900 --desc "Dinner"`, **Then** expense id `1` is
   created, split defaults to `equal` among all members, each share is `300.00`, exit `0`, stdout
   `Added expense 1 (900.00) to goa`.
2. **AC-008** **Given** an equal split that does not divide exactly, e.g. `--amount 100.00` paid by
   `ravi` among all 3 members, **Then** every share is first rounded down to the paisa
   (`33.33`) and the leftover paise are given one each to participants in alphabetical order:
   asha `33.34`, meera `33.33`, ravi `33.33` (the payer gets no special treatment). Shares sum to
   exactly `100.00`.
3. **AC-009** **Given** `--among asha,ravi`, **Then** only those members get a share and `meera`'s
   share is `0` (she is not part of the expense).
4. **AC-010** **Given** an amount that is not a positive decimal with at most 2 fractional digits
   (e.g. `0`, `-5`, `10.999`, `abc`, `1,000`) or is greater than `1000000.00`, **Then** exit code is
   `1`, stderr contains `invalid amount`, and nothing is stored.
5. **AC-011** **Given** `--paid-by` or an `--among` member that is not in the group, **Then** exit
   code is `3` and stderr contains `member <name> not found in group goa`.
6. **AC-012** **Given** a non-existent group, **Then** exit code is `3` and stderr contains
   `group <name> not found`.
7. **AC-013** **Given** an empty or whitespace-only `--desc`, or longer than 100 characters,
   **Then** exit code is `1` and stderr contains `invalid description`.

---

### User Story 3 - Unequal splits: exact amounts and percentages (Priority: P2)

Some costs are not shared equally (one person had a bigger meal, rent split by room size).

**Why this priority**: Important for realism but the product works without it.

**Independent Test**: Add one `exact` and one `percent` expense; compare stored shares in paise.

**Acceptance Scenarios**:

1. **AC-014** **Given** `expense add goa --paid-by asha --amount 1000 --desc Rent --split exact
   --shares asha=500,meera=300,ravi=200`, **Then** shares are exactly `500.00/300.00/200.00`.
2. **AC-015** **Given** exact shares that do not sum to the amount (e.g. `asha=500,ravi=400` for
   `1000`), **Then** exit code is `1` and stderr contains
   `shares total 900.00 does not match amount 1000.00`.
3. **AC-016** **Given** `--split percent --shares asha=50,meera=25,ravi=25` on `--amount 1000`,
   **Then** shares are `500.00/250.00/250.00`.
4. **AC-017** **Given** percentages that do not sum to exactly `100` (e.g. `50,30,10`), **Then**
   exit code is `1` and stderr contains `percentages must sum to 100`.
5. **AC-018** **Given** a percentage split that produces fractional paise
   (e.g. `--amount 100.01 --split percent --shares asha=50,ravi=50`), **Then** each share is first
   rounded down to the paisa and the leftover paise are allocated with the same remainder rule as
   AC-008: asha `50.01`, ravi `50.00`; shares sum to exactly `100.01`.
6. **AC-019** **Given** `--shares` used with `--split equal`, or `--among` used with
   `exact`/`percent`, or a member listed twice in `--shares`, or a share/percentage ≤ 0, **Then**
   exit code is `1` and stderr explains the conflict (`--shares is not allowed with equal split`,
   `--among is only allowed with equal split`, `duplicate member in shares: <name>`,
   `share for <name> must be positive`).

---

### User Story 4 - See balances (Priority: P1)

Each member wants to know whether they owe money or are owed money.

**Why this priority**: The core question the product answers.

**Independent Test**: Seed known expenses, run `balances goa --json`, compare exact values.

**Acceptance Scenarios**:

1. **AC-020** **Given** expense 1 (ravi paid 900 equal) and expense 2 (asha paid 300 equal),
   **When** the user runs `balances goa`, **Then** stdout is exactly (one line per member,
   alphabetical): `asha -100.00`, `meera -400.00`, `ravi +500.00`.
   Worked: balance = `paid − owed + settlements paid − settlements received`;
   asha paid 300, owes 300 + 100 → −100; meera paid 0, owes 300 + 100 → −400;
   ravi paid 900, owes 300 + 100 → +500. Sum = 0.
2. **AC-021** **Conservation invariant**: for any sequence of valid commands, the sum of all
   member balances in a group is exactly `0` paise.
3. **AC-022** `balances goa --json` returns an array sorted by member name with objects
   `{"member": str, "balance": "<signed decimal string with 2 places>", "balance_paise": int}`;
   zero is `"0.00"`, positive has no `+` sign in JSON, negative has a leading `-`.
4. **AC-023** **Given** a group with no expenses, **Then** every balance is `0.00`.

---

### User Story 5 - Settle up (Priority: P1)

The group wants the shortest practical list of "who pays whom" to clear all balances, and to
record payments once made.

**Why this priority**: The end goal of the product.

**Independent Test**: Seed balances, run `settle goa --json`, compare exact ordered transfers;
then apply them with `pay` and verify all balances are zero.

**Acceptance Scenarios**:

1. **AC-024** **Settlement algorithm (deterministic greedy)**: repeatedly take the debtor with the
   largest debt and the creditor with the largest credit (ties broken by member name ascending),
   transfer `min(debt, credit)`, and repeat until all balances are zero. Transfers are output in
   the order generated.
2. **AC-025** **Given** balances asha `+600.00`, meera `-100.00`, ravi `-500.00`, **When** the user
   runs `settle goa`, **Then** the output is exactly `ravi -> asha 500.00` then
   `meera -> asha 100.00`.
3. **AC-026** **Given** a 4-member group `trip` with balances a `+300`, b `+200`, c `-250`,
   d `-250`, **Then** transfers are exactly `c -> a 250.00`, `d -> b 200.00`, `d -> a 50.00`.
4. **AC-027** **Property**: for any group of n members, `settle` proposes at most `n − 1`
   transfers, every amount is > 0, and applying all proposed transfers makes every balance 0.
5. **AC-028** `settle` is read-only: it never changes stored data.
6. **AC-029** **Given** all balances are zero, **Then** human output is `All settled up.`, JSON is
   `[]`, exit `0`.
7. **AC-030** **When** the user runs `pay goa --from ravi --to asha --amount 500`, **Then** a
   settlement is recorded, ravi's balance increases by 500.00 and asha's decreases by 500.00.
8. **AC-031** **Given** a payment where `--from` equals `--to`, **Then** exit code is `1` and stderr
   contains `cannot pay yourself`.
9. **AC-032** **Given** a payment larger than what `--from` owes or than what `--to` is owed,
   **Then** exit code is `4`, stderr contains `payment exceeds outstanding balance`, and nothing
   is stored. (E.g. with ravi at `-500.00` and asha at `+600.00`, `pay --amount 500.01` is
   rejected; `--amount 500` is accepted.)

---

### User Story 6 - Correct mistakes (Priority: P3)

A user lists expenses and deletes one entered by mistake.

**Why this priority**: Needed, but rare.

**Independent Test**: Add two expenses, delete one, compare balances.

**Acceptance Scenarios**:

1. **AC-033** `expense list goa --json` returns expenses in ascending id order with fields defined
   in *Key Entities*.
2. **AC-034** **When** the user runs `expense delete goa 1`, **Then** the expense is removed,
   balances are recomputed, and ids are never reused.
3. **AC-035** **Given** settlements have already been recorded in the group, **When** the user
   deletes an expense, **Then** exit code is `4`, stderr contains
   `cannot delete expense after settlements`, and the expense remains.
4. **AC-036** **Given** a non-existent expense id, **Then** exit code is `3` and stderr contains
   `expense <id> not found in group goa`.

---

### User Story 7 - Safe persistence (Priority: P1)

Data must survive across runs and never be silently destroyed.

**Acceptance Scenarios**:

1. **AC-037** **Given** no data file, **When** a read command runs, **Then** it behaves as empty
   (e.g. `group list` → `No groups.` / `[]`) and does not create the file.
2. **AC-038** **Given** a data file containing invalid JSON or JSON with the wrong structure,
   **When** any command runs, **Then** exit code is `5`, stderr contains `data file is corrupt`,
   and the file is byte-for-byte unchanged.
3. **AC-039** Data written by one process is read back identically by a later process.
4. **AC-040** The data file path is `--data PATH`, else environment variable `SPLITKARO_DATA`,
   else `./splitkaro.json`.

### Edge Cases

- Amount exactly `1000000.00` is accepted; `1000000.01` is rejected.
- Amount `0.01` split equally among 3 members: one member owes `0.01`, two owe `0.00`
  (shares of 0 paise are allowed only as a result of rounding, never as user input).
- Member names are case-insensitive on input and stored lower-case.
- Command-line ids that are not positive integers → usage error (exit `2`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create named groups of 2–20 uniquely named members.
- **FR-002**: System MUST record expenses with payer, amount, description and split type
  (`equal` default, `exact`, `percent`).
- **FR-003**: System MUST represent money as integer paise and parse amounts as decimal strings
  with ≤ 2 fractional digits, in the range `0.01`–`1000000.00`.
- **FR-004**: System MUST allocate equal and percentage splits so shares sum exactly to the amount:
  round each share down to the paisa, then give leftover paise one each to participants in
  alphabetical order.
- **FR-005**: System MUST validate exact shares sum to the amount and percentages sum to exactly 100.
- **FR-006**: System MUST compute each member's balance as
  `paid − owed + settlements paid − settlements received`.
- **FR-007**: System MUST guarantee the conservation invariant (balances sum to 0).
- **FR-008**: System MUST propose settlements with the deterministic greedy algorithm (AC-024) and
  never more than `n − 1` transfers.
- **FR-009**: System MUST record payments between members (`pay`) and reject any payment that
  exceeds the sender's debt or the receiver's credit (exit 4).
- **FR-010**: System MUST list and delete expenses; ids are monotonically increasing per group and
  never reused; deletion is refused (exit 4) once the group has any settlement.
- **FR-011**: System MUST persist data to one JSON file atomically and refuse to touch a corrupt
  file (exit 5).
- **FR-012**: System MUST provide `--json` output for `group list`, `group show`, `expense list`,
  `balances` and `settle`.
- **FR-013**: System MUST use exit codes `0/1/2/3/4/5` as defined in the constitution.
- **FR-014**: System MUST take "now" from env `SPLITKARO_NOW` (ISO-8601 UTC) when set, so stored
  timestamps are deterministic in tests.

### Key Entities

- **Group**: `name`, `members` (sorted list of names), `next_expense_id` (int),
  `expenses` (list), `settlements` (list), `created_at`.
- **Expense**: `id` (int ≥ 1), `description`, `paid_by`, `amount_paise` (int),
  `split_type` (`equal|exact|percent`), `shares` (object member → paise, only participating
  members), `created_at`.
- **Settlement**: `from`, `to`, `amount_paise`, `created_at`.
- **Data file**: `{"version": 1, "groups": {name: Group}}`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % of acceptance scenarios AC-001…AC-040 are covered by at least one passing
  automated test.
- **SC-002**: Across ≥ 500 randomly generated valid command sequences, the conservation
  invariant and the settle-up property (AC-027) hold in 100 % of cases.
- **SC-003**: Every invalid input in this specification produces the specified exit code and
  message (no stack traces shown to the user).
- **SC-004**: `balances` and `settle` complete in under 1 second for 20 members × 5 000 expenses.
- **SC-005**: A corrupt data file is never modified (verified byte-for-byte).

## Assumptions

- Single currency (INR). Multi-currency, receipts, and online payments are out of scope.
- Single user / single process at a time; concurrent writers are out of scope.
- Members cannot be added to or removed from a group after creation in v1.
