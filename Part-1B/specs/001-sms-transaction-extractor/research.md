# Phase 0 Research: TxnSense

## R1 — Model choice
- **Decision**: app `gemini-3.5-flash-lite`, judge `gemini-3.5-flash`.
- **Evidence**: on 2026-11-13 the probe calls returned OK in 1.3 s (flash-lite) and 3.0 s (flash).
  `gemini-2.5-flash` returned 404 ("no longer available to new users") and `gemini-3.8-flash`
  returned 503 "high demand".
- **Rationale**: free tier, fast, JSON mode supported. A small model makes the harness meaningful
  because real mistakes are likely. The judge uses a different, stronger model so it does not
  grade its own output.

## R2 — Structured output
- **Decision**: `response_mime_type=application/json`, schema described in the prompt; output
  validated locally with `jsonschema` (draft 2020-12).
- **Alternative**: SDK `response_json_schema` enforcement. It is stronger, but a schema
  violation is still possible in principle and the app must validate either way. Kept as a
  possible repair if L1 fails.

## R3 — Guardrails in code
- **Decision**: after validation, the post-processor (a) removes any OTP-like code found in the
  input from all output strings, (b) for `phishing`, strips URLs, phone numbers and VPAs,
  (c) masks any 9+ digit run outside `reference_id`, (d) enforces INV-01/02 consistency.
- **Rationale**: Constitution III. Prompts reduce risk but cannot guarantee it.

## R4 — Semantic scoring
- **Decision**: exact match for enums, amount, date and last4; token-set similarity
  (`difflib.SequenceMatcher` on normalised lower-case alphanumerics) ≥ 0.6 against any accepted
  alias for counterparty; set membership for category; LLM judge rubric (1–5) for summary only.

## R5 — Infra vs application failures
- **Decision**: `google.genai.errors.ServerError`, `ClientError` with 429, and timeouts
  → `ModelServiceError`. The runner retries 3× with exponential backoff (5 s, 10 s, 20 s), then
  records `INFRA_ERROR`. Schema/guardrail failures are application failures and are never retried
  by the harness.
