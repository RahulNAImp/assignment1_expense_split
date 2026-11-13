# Implementation Plan: TxnSense — Bank/UPI SMS Transaction Extractor

**Branch**: `001-sms-transaction-extractor` | **Date**: 2026-11-13 | **Spec**: [spec.md](./spec.md)

## Summary

A Python package and CLI that sends one SMS and its `received_at` timestamp to Gemini with a
versioned system prompt and JSON output mode. The response is validated against
`contracts/output.schema.json`, then deterministic guardrails (OTP/URL/identifier redaction,
intent/transaction consistency) run before the result is returned. A separate evaluation harness
runs `evals/dataset.json` through the app and scores each case in three layers
(schema → invariants/guardrails → semantic + LLM judge) against the EV-03 thresholds.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `google-genai` (Gemini SDK), `jsonschema`, `python-dotenv`
**Model (app)**: `gemini-3.5-flash-lite`, temperature 0.2 (env `TXNSENSE_MODEL`, `TXNSENSE_TEMPERATURE`)
**Model (judge)**: `gemini-3.5-flash`, temperature 0. A different model and a different call from
the app, as Constitution V requires.
**Storage**: none (stateless); evaluation evidence written to `evidence/`
**Testing**: pytest for deterministic code with a fake LLM client (no network); the eval harness
covers the model-dependent behaviour
**Target Platform**: macOS / Linux CLI
**Constraints**: free-tier rate limits, so the runner paces calls (≥ 4 s apart) and retries
429/5xx up to 3 times with backoff; anything still failing is `INFRA_ERROR`
**Scale/Scope**: one SMS per call; dataset of 22 cases

## Constitution Check

| Principle | Plan compliance | Status |
|-----------|-----------------|--------|
| I Spec is truth | Dataset cases carry `traces` to AC/INV/GR ids; thresholds file mirrors EV-03 | PASS |
| II Contract over prose | JSON Schema contract file; app validates + retries once (FR-007) | PASS |
| III Guardrails in code | `guardrails.py` post-processor; harness re-checks independently | PASS |
| IV Grounding | INV-04/05 checked by harness; prompt instructs "only from text" | PASS |
| V Layered eval | `.harness/evaluators/{schema,invariants,quality,judge}.py` + `run_eval.py` | PASS |
| VI Secrets | key from `.env` only; results log model, temperature, prompt hash, dataset hash | PASS |

## Project Structure

```text
specs/001-sms-transaction-extractor/   spec, plan, research, data-model, contracts/, tasks
prompts/system_prompt.md               versioned system prompt (hash recorded per run)
src/txnsense/
├── config.py        model + temperature from env
├── schema.py        load + validate output schema
├── llm.py           Gemini client wrapper → ModelServiceError on infra failure
├── guardrails.py    input validation (AC-17), post-processing GR-01…GR-05, consistency INV-01/02
├── parser.py        parse_sms(): validate input → prompt → model → schema → guardrails
└── cli.py           `txnsense parse "<sms>" --received-at ...`
tests/               unit tests with FakeClient (no network)
evals/dataset.json   ≥ 15 cases (22) with ground truth + traces
.harness/
├── thresholds.json  EV-03 thresholds (copied from spec, frozen)
├── evaluators/      schema_eval.py (L1), invariants.py (L2), quality.py (L3), judge.py (L3 LLM)
└── run_eval.py      single pipeline → evidence/
evidence/
├── initial-generation/  final-generation/
├── runs/run-NNN/outputs.jsonl   raw model outputs per case
├── eval-results.json            latest run (plus runs/run-NNN/eval-results.json)
└── harness-log.md
```

## Evaluation Pipeline (single harness)

```text
dataset.json → parse_sms() → output
   → L1 jsonschema (contracts/output.schema.json)            → schema_valid
   → L2 invariants INV-01..08 + guardrails GR-01..05          → violations[]
   → L3 field accuracy vs ground truth (+ aliases/sets)       → field_accuracy
        + LLM judge rubric on summary (gemini-3.5-flash)      → judge_score
   → case score (EV-02) → aggregate E1..E5 (EV-03) → PASS / FAIL / INCONCLUSIVE
   → FAIL ⇒ evidence/runs/run-NNN/feedback.md (case, input, output, failed rule, expected)
```

## Complexity Tracking

None.
