# Implementation Plan: SplitKaro — Group Expense Splitter & Settlement CLI

**Branch**: `001-group-expense-splitter` | **Date**: 2026-11-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-group-expense-splitter/spec.md`

## Summary

A stdlib-only Python CLI (`splitkaro`) that stores groups, expenses and settlements in one JSON
file. Money is integer paise end-to-end; splits use "floor then alphabetical remainder"; settle-up
uses a deterministic largest-debtor/largest-creditor greedy algorithm. A local harness
(`.harness/run_harness.py`) enforces lint, SAST, spec-derived tests, coverage, AC traceability and
an integrity lock on the approved spec and tests.

## Technical Context

**Language/Version**: Python 3.11+ (developed on 3.15)
**Primary Dependencies**: none at runtime (argparse, json, dataclasses, decimal for parsing only)
**Storage**: single JSON file, atomic write via temp file + `os.replace`
**Testing**: pytest, pytest-cov, hypothesis (property tests for invariants AC-021/AC-027)
**Target Platform**: macOS / Linux terminal
**Project Type**: CLI (single project)
**Performance Goals**: `balances`/`settle` < 1 s for 20 members × 5 000 expenses (SC-004)
**Constraints**: no float for money, no network, deterministic output, exit codes 0–5
**Scale/Scope**: personal / small-group use, ≤ 20 members per group

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How the plan complies | Status |
|-----------|----------------------|--------|
| I. Spec is source of truth | Every module/function cites FR/AC ids in tasks.md; G5 checks AC coverage | PASS |
| II. Money is exact | `money.py` parses `str → int paise` with `Decimal` only for parsing; all arithmetic on `int` | PASS |
| III. Deterministic CLI | argparse adapter maps domain errors → exit codes; ties sorted by name; `SPLITKARO_NOW` clock | PASS |
| IV. Spec-derived tests | tests named `test_ac0xx_*`; hypothesis tests for invariants; G0 hash lock | PASS |
| V. Data safety & security | `storage.py` atomic write, structural validation before any write; bandit gate | PASS |
| VI. Simplicity | 5 small modules, no runtime deps | PASS |

Re-check after Phase 1 design: PASS (no violations, Complexity Tracking empty).

## Project Structure

### Documentation (this feature)

```text
specs/001-group-expense-splitter/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Phase 1 entities + validation
├── quickstart.md        # Phase 1 run/verify guide
├── contracts/cli.md     # Phase 1 CLI contract (commands, output, exit codes)
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (Part-1A root)

```text
src/splitkaro/
├── __init__.py
├── __main__.py          # python -m splitkaro
├── errors.py            # SplitKaroError hierarchy → exit codes
├── models.py            # Group, Expense, Settlement dataclasses
├── money.py             # parse_amount, format_paise, allocate_equal, allocate_percent
├── service.py           # business rules: groups, expenses, balances, settle, pay
├── storage.py           # load/validate/atomic save
└── cli.py               # argparse adapter, output formatting, exit codes
tests/
├── conftest.py          # run_cli helper, tmp data file, fixed clock
├── contract/            # CLI-level tests: exact stdout/stderr/exit code per AC
├── unit/                # money + service unit tests
└── property/            # hypothesis invariants (AC-021, AC-027)
.harness/
├── run_harness.py       # single entry point, runs G0–G5, writes evidence
├── gates.json           # thresholds (copied from constitution)
├── integrity.lock       # SHA-256 of spec.md + tests/** at approval time
└── ruff.toml / .bandit  # tool configuration
evidence/
├── initial-generation/  # snapshot of first agent-generated src/
├── final-generation/    # snapshot after harness-driven repair
├── harness-results/     # run-NNN.json per harness execution
└── harness-log.md
```

**Structure Decision**: single-project CLI layout above; tests split by contract/unit/property so
the harness can report which level failed.

## Harness Design (feeds tasks Phase 6)

| Gate | Command | Evidence captured on failure |
|------|---------|------------------------------|
| G0 Integrity | compare SHA-256 of `spec.md`, `tests/**` with `integrity.lock` | changed files + hashes |
| G1 Lint | `ruff check src tests` + `ruff format --check src tests` | rule id, file:line, message |
| G2 SAST | `bandit -r src -ll -f json` | test id, severity, file:line |
| G3 Tests | `pytest -q --junitxml` | failing test, AC id, assertion expected vs observed |
| G4 Coverage | `pytest --cov=src --cov-fail-under=90` | total %, uncovered lines |
| G5 Traceability | regex `AC-\d{3}` in spec vs tests | list of untested ACs |

Each run writes `evidence/harness-results/run-NNN.json` and a `feedback-NNN.md` (structured prompt
for the coding agent when any gate fails) and appends a summary row to `evidence/harness-log.md`.

## Complexity Tracking

No constitution violations to justify.
