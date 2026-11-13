# Initial generation snapshot (T013)

`src/` and `prompts/` as first produced by the coding agent (Claude Code, Claude Opus 5.5) from
tasks T006–T012, **before** the evaluation harness was run for the first time.

During `/speckit.implement` the agent ran only the offline unit tests (`pytest`, 10/10) and ruff
on its own code (one E501 line-length fix to a docstring). No model call against the evaluation
dataset had been made.
