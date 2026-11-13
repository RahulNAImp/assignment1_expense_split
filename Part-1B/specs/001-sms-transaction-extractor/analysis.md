# Specification Analysis Report (/speckit.analyze): 2026-11-13

| ID | Category | Severity | Location | Finding | Resolution |
|----|----------|----------|----------|---------|------------|
| B1 | Coverage | MEDIUM | AC-17 vs EV | `invalid_input` never calls the model, so the judge has no meaningful summary to grade | quality.py treats a deterministic summary as N/A; the weight is renormalised (as EV-02 allows when the judge is unavailable) |
| B2 | Ambiguity | MEDIUM | INV-04 | "matches an amount in the input": how are `Rs 2,499` and `2499.00` compared? | Normalise both: strip `,`, `₹`, `Rs`, `INR`; compare as numbers to 2 dp |
| B3 | Consistency | LOW | INV-08 wording | "unless tagged otherwise" is vague | Harness applies INV-08 strictly; the dataset never expects high risk for those intents |
| B4 | Coverage | LOW | SC-004 latency | No dataset check for latency | Runner records `latency_s` per case; reported, not gated |
| B5 | Constitution | none | none | No violations | none |

Coverage: 18/18 ACs referenced by ≥ 1 dataset case; 8/8 INV and 5/5 GR checked by T015; 0 CRITICAL
issues, so implementation may proceed.
