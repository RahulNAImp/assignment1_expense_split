# Phase 0 Research: SplitKaro

## R1 — Money representation
- **Decision**: integer paise everywhere; parse input with regex `^\d{1,7}(\.\d{1,2})?$` then
  `Decimal` → `int(value * 100)`.
- **Rationale**: Constitution II forbids float; ints make the conservation invariant exact.
- **Alternatives**: `Decimal` throughout (heavier, still needs quantize rules); float (rejected:
  `0.1 + 0.2 != 0.3`).

## R2 — Remainder allocation (from Clarification 2026-11-13)
- **Decision**: `base = floor(amount * weight / total_weight)` per participant, then distribute
  `amount − Σbase` paise one each to participants sorted by name.
- **Rationale**: deterministic, order-independent, simple to explain and test.
- **Alternatives**: largest-remainder (Hamilton) method — fairer for percentages but harder to
  predict by hand; payer absorbs — rejected by student in clarification.

## R3 — Settlement algorithm
- **Decision**: greedy: largest debtor pays largest creditor `min(debt, credit)`; ties by name.
- **Rationale**: each step zeroes at least one member ⇒ ≤ n − 1 transfers (AC-027); O(n² ) for
  n ≤ 20 is trivial. True minimum-transfer settlement is NP-hard (subset-sum) and unnecessary.
- **Alternatives**: exact minimisation via subset search (rejected: exponential, non-obvious
  output); pairwise debts without netting (rejected: up to n(n−1)/2 transfers).

## R4 — CLI framework
- **Decision**: `argparse` (stdlib). argparse exits 2 on usage errors, which matches the contract.
- **Alternatives**: click/typer (rejected: runtime dependency, Constitution VI).

## R5 — Atomic persistence
- **Decision**: `tempfile.NamedTemporaryFile(dir=same_dir, delete=False)` → write → `flush` +
  `os.fsync` → `os.replace`. Validate structure on load; on failure raise `StorageError` (exit 5)
  before any write is attempted.

## R6 — Harness tooling
- **Decision**: ruff (lint+format), bandit (SAST, `-ll` = MEDIUM+), pytest + pytest-cov,
  hypothesis for property tests, a Python runner (no Makefile dependency) so it works on macOS
  and Linux identically.
