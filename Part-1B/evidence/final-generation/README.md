# Final generation snapshot

`src/` and `prompts/` as evaluated by **run-006** (final, PASS) and acceptance run 2 (11/11).

Two harness-driven repairs since `../initial-generation/`:
1. `prompts/system_prompt.md` (commit `253c047`): OTP+amount+merchant precedence, from eval run-001 case S02.
2. `src/txnsense/parser.py` (commit `ec28b33`): INV-01 normalisation before schema validation, from acceptance case H06.

See `../harness-log.md` §3.1 and §3.3. Compare with `diff -r evidence/initial-generation evidence/final-generation`.
