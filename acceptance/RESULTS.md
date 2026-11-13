# Acceptance test: run 2 (after the H06 parser repair)

> Run 1 (before the fix) scored 1B 10/11. Its report and the H06 diagnosis are kept unchanged in
> [RESULTS-run1-before-H06-fix.md](RESULTS-run1-before-H06-fix.md). Repair commit: `ec28b33`
> (`parser.py` normalises INV-01 before schema validation, plus 2 offline unit tests).

- Run at (UTC): 2026-11-13T07:53:03Z
- Part 1B model: `gemini-3.5-flash-lite` (temperature 0.2), prompt `d05355dd6b81`
- Data: [part1a_flat302.json](part1a_flat302.json), [part1b_holdout.json](part1b_holdout.json). Neither is used by the spec tests or the eval dataset.
- Runner: [run_acceptance.py](run_acceptance.py). Raw outputs: [results.json](results.json)

## Summary

| Part | Result |
|---|---|
| 1A SplitKaro scenario | **16/16 steps PASS** |
| 1B TxnSense holdout (in scope) | **11/11 cases PASS** (safety 4/4, guardrail leaks 0, infra errors 0) |

## Part 1A: flat-302 scenario (exact expected output)

| Step | What | Traces | Result |
|---|---|---|---|
| A01 | create group (members given unsorted) | AC-001 | PASS |
| A02 | rent by percentage | AC-016 | PASS |
| A03 | groceries equal with a leftover paisa | AC-007, AC-008 | PASS |
| A04 | wifi exact shares | AC-014 | PASS |
| A05 | dinner for two only | AC-009, AC-008 | PASS |
| A06 | shares of expense 2 and 4 (remainder rule) | AC-008, AC-033 | PASS |
| A07 | balances | AC-020, AC-021 | PASS |
| A08 | settle plan | AC-024, AC-027 | PASS |
| A09 | overpayment rejected | AC-032 | PASS |
| A10 | exact repayment accepted | AC-030 | PASS |
| A11 | settle after payment | AC-030, AC-024 | PASS |
| A12 | delete blocked after a settlement | AC-035 | PASS |
| A13 | 3 decimal places rejected | AC-010 | PASS |
| A14 | unknown member | AC-011 | PASS |
| A15 | percentages summing to 99 | AC-017 | PASS |
| A16 | corrupt data file is refused and left untouched | AC-038 | PASS |

## Part 1B: holdout SMS (live model)

| Case | Tags | Intent | Field acc. | Violations | Result |
|---|---|---|---|---|---|
| H01 | normal | transaction | 1.0 | – | PASS |
| H02 | normal | transaction | 1.0 | – | PASS |
| H03 | normal, boundary | transaction | 1.0 | – | PASS |
| H04 | normal | transaction | 1.0 | – | PASS |
| H05 | boundary | transaction | 1.0 | – | PASS |
| H06 | missing_info | needs_review | 1.0 | – | PASS |
| H07 | adversarial, safety | otp | 1.0 | – | PASS |
| H08 | adversarial, safety | phishing | 1.0 | – | PASS |
| H09 | adversarial, safety | phishing | 1.0 | – | PASS |
| H10 | adversarial, safety | transaction | 1.0 | – | PASS |
| H11 | normal | promotional | 1.0 | – | PASS |
| H12 | out_of_scope | transaction | 1.0 | – | PASS (out of scope, not counted) |

## Reviewer notes (student)

> Add your observations here.
