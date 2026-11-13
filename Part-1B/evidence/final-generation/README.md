# Final generation snapshot (T021)

`src/` and `prompts/` at the state evaluated by run-003, run-004 and run-005 (all PASS).

- `src/`: byte-identical to `../initial-generation/src/`.
- `prompts/system_prompt.md`: one repair (commit `253c047`) adding the OTP+amount+merchant
  precedence rule, driven by run-001 case S02. See `../harness-log.md` §3.1.

Compare: `diff -r evidence/initial-generation evidence/final-generation`
