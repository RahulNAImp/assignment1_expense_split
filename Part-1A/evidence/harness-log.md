# Part 1A Harness Log — SplitKaro


### run-001 — initial generation (T028) — **FAIL**

- Time (UTC): 2026-11-13T06:14:18Z
- Git commit under test: `d14de50`
- Result file: `evidence/harness-results/run-001.json`
- Feedback for agent: `evidence/harness-results/run-001-feedback.md`

| Gate | Result | Summary |
|------|--------|---------|
| G0 Integrity | ✅ PASS | 16 locked files; changed=0 missing=0 new_tests=0 |
| G1 Lint & format | ❌ FAIL | 3 lint violation(s), 0 file(s) need formatting |
| G2 Security/SAST | ✅ PASS | 0 finding(s) >= MEDIUM (0 total incl. LOW) |
| G3 Spec tests | ❌ FAIL | 0/4 passed, 4 failed, 0 skipped |
| G4 Coverage | ❌ FAIL | None% line coverage (threshold 90%) |
| G5 Traceability | ✅ PASS | 40/40 acceptance criteria referenced by tests |
