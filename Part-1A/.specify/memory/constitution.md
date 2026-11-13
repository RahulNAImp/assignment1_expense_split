# SplitKaro Constitution

## Core Principles

### I. Specification Is the Source of Truth (NON-NEGOTIABLE)
- Every behaviour of SplitKaro MUST trace to a functional requirement (`FR-xxx`) or acceptance
  scenario (`AC-xxx`) in `specs/001-group-expense-splitter/spec.md`.
- Behaviour that is not in the specification MUST NOT be implemented.
- If an ambiguity or defect is discovered after approval, it is fixed in the specification first
  (dated entry under `Clarifications` or `Revision History`), then propagated to plan → tasks →
  tests → code. Code is never changed to "redefine" the spec.

### II. Money Is Exact
- All monetary values MUST be represented internally as integer **paise** (1 INR = 100 paise).
  Binary floating point (`float`) MUST NOT be used for money anywhere in `src/`.
- Input amounts are parsed from decimal strings with at most 2 fractional digits; anything else is
  a validation error.
- Every rounding decision (equal and percentage splits) MUST follow the single remainder rule in
  the specification, so the same input always yields the same paise allocation.
- **Conservation invariant**: for every group, at every point in time, the sum of all member
  balances MUST equal exactly 0 paise. The sum of an expense's shares MUST equal its amount.

### III. Deterministic, Observable CLI Contract
- SplitKaro is a single command-line program. Normal output → stdout; diagnostics → stderr.
- Every read command MUST support `--json`, whose shape is fixed by the specification.
- Exit codes are part of the contract and MUST be exactly: `0` success, `1` validation error,
  `2` usage error, `3` not found, `4` conflict / business-rule violation, `5` storage error.
- Same data file + same arguments + same injected clock ⇒ byte-identical output. Ordering ties are
  always broken by a documented rule (member name, then id), never by dict/hash order.

### IV. Test-First, Spec-Derived Tests (NON-NEGOTIABLE)
- Each acceptance scenario `AC-xxx` MUST have at least one automated test referencing that ID.
- Tests assert exact values (paise, ordering, exit codes, JSON fields) — never just "no crash".
- Invariants in Principle II MUST additionally be checked by property-style tests over many
  generated inputs.
- The coding agent MUST NOT delete, skip, `xfail`, or weaken a failing test, and MUST NOT lower a
  harness threshold. The approved spec and the test suite are hash-locked by the harness.

### V. Data Safety & Security
- Persistence is one local JSON file written atomically (temp file in same dir + `os.replace`).
- A corrupt or structurally invalid data file MUST yield exit `5` and MUST NOT be modified.
- No network access, no `eval`/`exec`, no `pickle`, no `subprocess` with `shell=True`,
  no hard-coded secrets.

### VI. Simplicity
- Python ≥ 3.11 standard library only at runtime. Dev-only tools allowed for the harness.
- Layers: `models` (dataclasses) → `money` (parsing/allocation) → `service` (business rules,
  settlement) → `storage` (JSON) → `cli` (argparse adapter). No layer imports a layer above it.

## Measurable Engineering Constraints (Quality Gates)

| Gate | Tool | Pass condition |
|------|------|----------------|
| G0 Integrity | harness SHA-256 lock | approved spec + tests unchanged unless a revision is logged |
| G1 Lint & format | `ruff check`, `ruff format --check` | 0 violations |
| G2 Security (SAST) | `bandit -r src` | 0 findings of severity ≥ MEDIUM |
| G3 Spec tests | `pytest` | 100 % pass, 0 skipped / xfailed |
| G4 Coverage | `pytest-cov` | line coverage of `src/` ≥ 90 % |
| G5 Traceability | harness AC scan | every `AC-xxx` in spec referenced by ≥ 1 test |

- Performance: `balances` and `settle` on a group of 20 members and 5 000 expenses complete in
  < 1 s.
- All gates run from one command, `python .harness/run_harness.py`, which writes a JSON result
  file and appends a human-readable entry to `evidence/harness-log.md`.

## Development Workflow

1. `/speckit.constitution` → `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` →
   `/speckit.tasks` → `/speckit.analyze` → `/speckit.implement`.
2. The first agent-generated implementation is snapshotted to `evidence/initial-generation/`
   before any harness-driven change.
3. Harness failures are captured as structured evidence (gate, command, stdout/stderr, failing
   test/rule, expected vs observed) and fed back to the coding agent; the same gates re-run
   unchanged.
4. A human records the final ACCEPT/REJECT decision after the automated harness result.

## Governance

- This constitution overrides ad-hoc instructions given to the coding agent.
- Amendments require a semantic version bump, a dated note here, and a commit prefixed
  `docs(constitution):`. A quality gate may only change through an amendment, never to make a
  failing run pass.

**Version**: 1.0.0 | **Ratified**: 2026-11-13 | **Last Amended**: 2026-11-13
