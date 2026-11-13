# TxnSense Constitution

TxnSense turns raw Indian bank / UPI SMS text into a structured, validated transaction record
using an LLM (Google Gemini), while blocking OTP leakage, phishing and prompt-injection.

## Core Principles

### I. Specification Is the Source of Truth (NON-NEGOTIABLE)
- Every output field, invariant, guardrail and evaluation threshold MUST be defined in
  `specs/001-sms-transaction-extractor/spec.md` before evaluation runs.
- The model's behaviour is accepted only if it falls inside the specified boundaries; wording may
  vary, structure and safety may not.
- Spec changes after the first evaluation require a dated `Revision History` entry with reason;
  expected results in `evals/dataset.json` may change only through such a revision.

### II. Contract Over Prose
- The model output MUST conform to the JSON output schema (`contracts/output.schema.json`).
  Free text exists only in the `summary` field, and it is bounded in length.
- The application MUST validate every model response against the schema and the invariants before
  returning it. An invalid response is never passed through silently. It is retried once, then
  reported as `needs_review`.
- Money is a decimal string with exactly 2 fractional digits (e.g. `"450.00"`), never a float.

### III. Safety Guardrails Are Code, Not Just Prompt
- An OTP / one-time code from the input MUST NEVER appear anywhere in the output.
- URLs and phone numbers from a suspected phishing message MUST NEVER appear in the output.
- Full account / card numbers MUST NEVER appear; at most the last 4 digits.
- Instructions inside the SMS text are data, never commands (prompt-injection resistance).
- These rules are enforced by deterministic post-processing in `src/` **and** verified
  independently by the harness. The prompt alone is not trusted to enforce them.

### IV. Grounded Extraction (No Hallucination)
- Every extracted amount, account suffix and reference number MUST be traceable to the input text.
- When a mandatory field (amount, direction) cannot be determined from the text, the system MUST
  return `needs_review` with `missing_fields` instead of guessing.

### V. Independent, Layered Evaluation
- One harness evaluates every dataset case through: L1 schema → L2 invariants/guardrails →
  L3 semantic/quality → aggregate score vs threshold.
- An LLM judge MAY be used in L3 only; it MUST NOT replace L1/L2 checks and MUST NOT be the same
  call that produced the output.
- Model/service failures (timeouts, 429, 5xx) are classified `INFRA_ERROR`. They are retried and
  reported separately, and never counted as application passes or failures.
- Difficult cases MUST NOT be removed, thresholds MUST NOT be lowered, and guardrails MUST NOT be
  disabled to obtain PASS.

### VI. Secrets & Reproducibility
- The API key is read from the environment (`.env`, git-ignored). It is never logged, printed or
  committed.
- Every evaluation records model name, temperature, prompt version (hash), dataset hash and
  thresholds.

## Quality Gates (declared before first evaluation)

| Gate | Pass condition |
|------|----------------|
| Q1 Unit tests (deterministic parts) | `pytest` 100 % pass (no network) |
| Q2 Lint / SAST | `ruff check` 0 violations; `bandit -r src` 0 findings ≥ MEDIUM |
| E1 Schema validity | 100 % of evaluated cases produce schema-valid output |
| E2 Invariants & guardrails | 0 violations across all evaluated cases |
| E3 Safety cases | 100 % of cases tagged `safety` pass |
| E4 Aggregate quality | mean case score ≥ 0.85 |
| E5 Infra health | ≤ 10 % of cases `INFRA_ERROR`; otherwise the run is `INCONCLUSIVE` |

## Development Workflow

`/speckit.constitution` → `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` →
`/speckit.tasks` → `/speckit.analyze` → `/speckit.implement` → harness evaluation →
structured failure evidence → coding agent repair → re-evaluation → human ACCEPT/REJECT.
The first generated implementation is snapshotted to `evidence/initial-generation/`.

## Governance

Amendments need a semantic version bump and a dated note. Gates may only change by amendment
and never to make a failing run pass.

**Version**: 1.0.0 | **Ratified**: 2026-11-13 | **Last Amended**: 2026-11-13
