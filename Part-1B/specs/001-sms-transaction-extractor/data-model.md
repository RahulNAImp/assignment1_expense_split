# Data Model: TxnSense

- **SmsInput**: `text` (1–1000 chars), `sender` (optional str), `received_at` (ISO-8601 with offset).
- **ParseResult**: see `contracts/output.schema.json` (spec SCH table).
- **EvalCase** (`evals/dataset.json`):
  - `id` (str, e.g. `N01`), `tags` (list: `normal|boundary|ambiguous|missing_info|malformed|adversarial|safety`)
  - `input`: `{text, sender?, received_at}`
  - `expected`: `{intent, direction?, amount?, txn_date?, account_last4?, channel?, available_balance?, missing_fields?, risk_level?}`.
    Only the listed keys are scored.
  - `accept`: `{counterparty?: [aliases], category?: [allowed]}`
  - `must_not_contain`: strings that must not appear anywhere in the serialized output
  - `traces`: requirement ids (AC/INV/GR/FR)
- **CaseResult** (`eval-results.json`): `id, status (PASS|FAIL|INFRA_ERROR), schema_valid,
  violations[], field_checks{}, field_accuracy, judge_score, score, output, latency_s`.
