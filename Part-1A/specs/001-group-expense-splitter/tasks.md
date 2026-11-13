# Tasks: SplitKaro — Group Expense Splitter & Settlement CLI

**Input**: Design documents from `/specs/001-group-expense-splitter/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Tests**: REQUIRED (Constitution IV — test-first). Test tasks for a story are written and
hash-locked *before* the story's implementation tasks.

Format: `[ID] [P?] [Story] Description (→ traces)`; `[P]` = can run in parallel.

## Phase 1: Setup

- [x] T001 Create `pyproject.toml` (package `splitkaro`, console script, dev extras: pytest,
      pytest-cov, hypothesis, ruff, bandit) (→ plan Technical Context)
- [x] T002 [P] Create `src/splitkaro/` package skeleton and `__main__.py` (→ plan Structure)
- [x] T003 [P] Create `.harness/ruff.toml`, `.harness/gates.json` with thresholds from the
      constitution Quality Gates table (→ Constitution G1–G5)

## Phase 2: Foundational

- [x] T004 `errors.py`: `ValidationError`(1), `NotFoundError`(3), `ConflictError`(4),
      `StorageError`(5) (→ FR-013)
- [x] T005 `models.py`: Group/Expense/Settlement dataclasses + to/from dict (→ data-model.md)
- [x] T006 `storage.py`: path resolution, structural validation, atomic save
      (→ FR-011, AC-037–AC-040)
- [x] T007 `money.py`: `parse_amount`, `format_paise`, `allocate_equal`, `allocate_percent`
      (→ FR-003, FR-004, AC-008, AC-010, AC-018)
- [x] T008 `tests/conftest.py`: `run_cli` helper (in-process, captures stdout/stderr/exit code),
      temp data file, fixed `SPLITKARO_NOW`

## Phase 3: Spec-derived tests (written first, then locked)

- [x] T009 [P] [US1] `tests/contract/test_groups.py` — AC-001…AC-006
- [x] T010 [P] [US2] `tests/contract/test_expense_equal.py` — AC-007…AC-013
- [x] T011 [P] [US3] `tests/contract/test_expense_unequal.py` — AC-014…AC-019
- [x] T012 [P] [US4] `tests/contract/test_balances.py` — AC-020, AC-022, AC-023
- [x] T013 [P] [US5] `tests/contract/test_settle_pay.py` — AC-024…AC-032
- [x] T014 [P] [US6] `tests/contract/test_expense_manage.py` — AC-033…AC-036
- [x] T015 [P] [US7] `tests/contract/test_storage.py` — AC-037…AC-040
- [x] T016 [P] `tests/unit/test_money.py` — parsing/formatting/allocation boundaries
- [x] T017 [P] `tests/property/test_invariants.py` — hypothesis: AC-021 conservation,
      AC-027 settle property, share-sum invariant (→ SC-002)
- [x] T018 Generate `.harness/integrity.lock` (SHA-256 of spec.md + tests/**) (→ G0)

## Phase 4: Implementation by user story (P1 first)

- [x] T019 [US1] `service.create_group`, `list_groups`, `show_group` (→ FR-001)
- [x] T020 [US2] `service.add_expense` equal split incl. `--among` (→ FR-002, FR-004)
- [x] T021 [US3] exact + percent split validation and allocation (→ FR-005)
- [x] T022 [US4] `service.balances` (→ FR-006, FR-007)
- [x] T023 [US5] `service.settle` greedy + `service.pay` with overpayment guard (→ FR-008, FR-009)
- [x] T024 [US6] `service.list_expenses`, `delete_expense` with settlement guard (→ FR-010)
- [x] T025 `cli.py`: argparse tree, human + JSON output, error → exit code mapping
      (→ FR-012, FR-013, contracts/cli.md)
- [x] T026 Snapshot first generated `src/` to `evidence/initial-generation/` (→ Workflow step 2)

## Phase 5: Harness

- [x] T027 `.harness/run_harness.py`: gates G0–G5, `run-NNN.json`, `feedback-NNN.md`,
      append to `evidence/harness-log.md` (→ plan Harness Design)
- [x] T028 Run harness on initial generation; record result
- [x] T029 If any gate fails: feed `feedback-NNN.md` to the coding agent, repair `src/` only,
      re-run identical gates (repeat until PASS or REJECT)
- [x] T030 Snapshot accepted `src/` to `evidence/final-generation/`; human ACCEPT/REJECT entry

## Phase 6: Polish

- [x] T031 [P] Performance check SC-004 (20 members × 5 000 expenses < 1 s) as a test
- [ ] T032 [P] Part-1A README section: how to run app + harness

## Dependencies

Setup → Foundational → Tests (locked) → Implementation (US1 → US2 → US3/US4 → US5 → US6) →
Harness → Polish. T026 must happen before T027 is first executed.

## Traceability Matrix (requirement → tasks)

| FR | Tasks | | FR | Tasks |
|----|-------|-|----|-------|
| FR-001 | T009, T019 | | FR-008 | T013, T017, T023 |
| FR-002 | T010, T020 | | FR-009 | T013, T023 |
| FR-003 | T007, T010, T016 | | FR-010 | T014, T024 |
| FR-004 | T007, T010, T011, T016 | | FR-011 | T006, T015 |
| FR-005 | T011, T021 | | FR-012 | T012, T013, T025 |
| FR-006 | T012, T022 | | FR-013 | T004, T025 |
| FR-007 | T017, T022 | | FR-014 | T008, T005 |
