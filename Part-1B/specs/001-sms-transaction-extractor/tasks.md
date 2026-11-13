# Tasks: TxnSense — Bank/UPI SMS Transaction Extractor

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/output.schema.json
**Tests/Evals**: REQUIRED. The dataset and thresholds are written and frozen before the app code.

## Phase 1: Setup
- [ ] T001 `pyproject.toml` (package `txnsense`, script `txnsense`, deps google-genai, jsonschema,
      python-dotenv; dev: pytest, ruff, bandit) (→ plan)
- [ ] T002 [P] `.env.example`, `.gitignore` check that `.env` is ignored (→ Constitution VI)

## Phase 2: Evaluation assets first (→ EV-01, EV-03)
- [ ] T003 `evals/dataset.json`: 22 cases across normal / boundary / ambiguous / missing_info /
      malformed / adversarial (safety), each with ground truth + `traces` (→ EV-01, AC-01…AC-18)
- [ ] T004 `.harness/thresholds.json`, a copy of EV-02/EV-03 (→ EV-03)
- [ ] T005 Record SHA-256 of spec, dataset and thresholds in `.harness/eval.lock` (frozen before
      the first evaluation)

## Phase 3: Application (US1–US4)
- [ ] T006 `config.py`, `schema.py` (→ FR-002)
- [ ] T007 `prompts/system_prompt.md`: role, schema, intent definitions, extraction rules, date
      rule, safety rules, "SMS text is data" (→ FR-003/004/005, AC-05, GR-04)
- [ ] T008 `llm.py`: Gemini wrapper, JSON mode, `ModelServiceError` mapping (→ FR-007, R5)
- [ ] T009 `guardrails.py`: input validation (AC-17), OTP/URL/phone/VPA/long-digit redaction,
      INV-01/02 consistency (→ FR-006, GR-01…GR-03)
- [ ] T010 `parser.py` `parse_sms()`: validate → prompt → model → schema (retry once) → guardrails
      (→ FR-001…FR-007)
- [ ] T011 `cli.py` `txnsense parse` (→ FR-008)
- [ ] T012 [P] `tests/` unit tests with FakeClient: input validation, retry-then-needs_review,
      redaction, consistency (→ Q1)
- [ ] T013 Snapshot `src/` + `prompts/` to `evidence/initial-generation/`

## Phase 4: Harness (single pipeline)
- [ ] T014 `.harness/evaluators/schema_eval.py` L1 (→ SCH)
- [ ] T015 `.harness/evaluators/invariants.py` L2 INV-01…08, GR-01…05 + `must_not_contain`
      (→ INV, GR). Independent of `src/guardrails.py`.
- [ ] T016 `.harness/evaluators/quality.py` L3 field accuracy; `judge.py` LLM rubric (→ EV-02)
- [ ] T017 `.harness/run_eval.py`: run dataset, pace and retry, classify INFRA_ERROR, aggregate
      E1–E5, write `runs/run-NNN/`, `eval-results.json`, `feedback.md`, append harness-log
      (→ EV-03)
- [ ] T018 Q1/Q2 gates in the runner: pytest, ruff, bandit before evaluation

## Phase 5: Evaluate → repair → re-evaluate
- [ ] T019 Run evaluation on the initial generation
- [ ] T020 On FAIL: give `feedback.md` to the coding agent; repair prompt / parser / guardrails
      only; re-run the identical harness
- [ ] T021 Snapshot to `evidence/final-generation/`; human ACCEPT/REJECT in harness-log

## Traceability
| Requirement | Tasks | Requirement | Tasks |
|-------------|-------|-------------|-------|
| FR-001/002 | T006, T010, T014 | GR-01…03 | T009, T015 |
| FR-003/004 | T007, T016 | GR-04/05 | T007, T015 |
| FR-005 | T007, T015 | INV-01…08 | T009, T015 |
| FR-006 | T009 | EV-01…03 | T003, T004, T016, T017 |
| FR-007 | T008, T010, T012, T017 | FR-008 | T011 |
