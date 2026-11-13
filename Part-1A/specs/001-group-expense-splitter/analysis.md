# Specification Analysis Report (/speckit.analyze) — 2026-11-13

Scope: spec.md (40 ACs, 14 FRs, 5 SCs), plan.md, tasks.md (32 tasks), constitution v1.0.0.

| ID | Category | Severity | Location | Summary | Recommendation / Resolution |
|----|----------|----------|----------|---------|------------------------------|
| A1 | Coverage | LOW | SC-004 | Performance criterion had no task in first tasks draft | Added T031 |
| A2 | Consistency | MEDIUM | spec AC-022 vs contracts/cli.md | JSON balance sign: spec says no `+` in JSON, human output shows `+` | Contract table states human sign rule; JSON follows AC-022. Consistent. |
| A3 | Ambiguity | MEDIUM | AC-019 | Is `--split exact` without `--shares` usage or validation error? | Treat as validation error (exit 1, `--shares is required for exact/percent split`). Implementation detail within AC-019 family; no spec change needed. |
| A4 | Underspecification | LOW | AC-027 | "applying all transfers" must use `pay` semantics | Property test applies transfers through `service.pay`. |
| A5 | Constitution | — | all | No violations found; every principle mapped in plan Constitution Check | — |

**Coverage summary**: 14/14 FRs have ≥ 1 task; 40/40 ACs map to a test task (T009–T017);
0 unmapped tasks; 0 CRITICAL issues → implementation may proceed.
