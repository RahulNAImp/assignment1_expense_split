# Assignment 1: Spec-Driven Development & Harness Engineering

**Course:** AI-Augmented Software Development Life Cycle (SE ZG534), BITS Pilani WILP, S1 2026
**Student:** Rahul Rangnath Nandanwar · 2026NS93095 · 2026ns93095@wilp.bits-pilani.ac.in

Two small applications built with the **GitHub Spec Kit** workflow
(`constitution → specify → clarify → plan → tasks → analyze → implement`), each validated by a
harness that is independent of the AI-generated code.

| Part | Application | Nature | Harness verdict |
|------|-------------|--------|-----------------|
| [Part-1A](Part-1A/) | **SplitKaro**: group expense splitter & settle-up CLI (exact paise, deterministic settlement) | Deterministic | run-001 FAIL → repair → run-002 **PASS** (6/6 gates) |
| [Part-1B](Part-1B/) | **TxnSense**: Gemini-powered Bank/UPI SMS → structured transaction, with OTP/phishing/injection guardrails | Non-deterministic (LLM) | run-001 FAIL (E3 safety 0.857) → prompt repair → run-003/run-004 **PASS** (E3 1.0, E4 0.984) |

## Where to look (evidence map)

| What the assignment asks for | Part 1A | Part 1B |
|------------------------------|---------|---------|
| Constitution | [constitution.md](Part-1A/.specify/memory/constitution.md) | [constitution.md](Part-1B/.specify/memory/constitution.md) |
| Specification + acceptance criteria | [spec.md](Part-1A/specs/001-group-expense-splitter/spec.md) (40 ACs) | [spec.md](Part-1B/specs/001-sms-transaction-extractor/spec.md) (schema, INV, GR, EV) |
| Clarifications | `## Clarifications` in each spec | same |
| Plan / research / data model / contracts | [plan.md](Part-1A/specs/001-group-expense-splitter/plan.md) | [plan.md](Part-1B/specs/001-sms-transaction-extractor/plan.md), [output.schema.json](Part-1B/specs/001-sms-transaction-extractor/contracts/output.schema.json) |
| Tasks + analyze | [tasks.md](Part-1A/specs/001-group-expense-splitter/tasks.md), [analysis.md](Part-1A/specs/001-group-expense-splitter/analysis.md) | [tasks.md](Part-1B/specs/001-sms-transaction-extractor/tasks.md), [analysis.md](Part-1B/specs/001-sms-transaction-extractor/analysis.md) |
| Source | [src/splitkaro](Part-1A/src/splitkaro) | [src/txnsense](Part-1B/src/txnsense), [prompts/](Part-1B/prompts) |
| Tests / evals | [tests/](Part-1A/tests) (contract, unit, property) | [evals/dataset.json](Part-1B/evals/dataset.json) (25 cases), [tests/](Part-1B/tests) |
| Harness | [.harness/run_harness.py](Part-1A/.harness/run_harness.py) | [.harness/run_eval.py](Part-1B/.harness/run_eval.py) + [evaluators/](Part-1B/.harness/evaluators) |
| Initial vs final generation | [evidence/initial-generation](Part-1A/evidence/initial-generation), [final-generation](Part-1A/evidence/final-generation) | [evidence/initial-generation](Part-1B/evidence/initial-generation), [final-generation](Part-1B/evidence/final-generation) |
| Harness results | [evidence/harness-results/](Part-1A/evidence/harness-results) | [evidence/eval-results.json](Part-1B/evidence/eval-results.json), [evidence/runs/](Part-1B/evidence/runs) |
| Harness log + human decision | [harness-log.md](Part-1A/evidence/harness-log.md) | [harness-log.md](Part-1B/evidence/harness-log.md) |

The **git history** is part of the evidence: each Spec Kit step, test lock, initial generation,
harness run and repair is a separate commit (`git log --oneline`).

## How to run

Prerequisites: Python ≥ 3.11 and [uv](https://docs.astral.sh/uv/) (or `python -m venv` + `pip`).

### Part 1A: SplitKaro (no network, no keys)

```bash
cd Part-1A
uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"
export PYTHONPATH=src            # see harness-log run-001: macOS may hide .pth files
python -m splitkaro group create goa --members ravi,asha,meera
python -m splitkaro expense add goa --paid-by ravi --amount 900 --desc Dinner
python -m splitkaro balances goa
python -m splitkaro settle goa
python .harness/run_harness.py --label "my run"     # gates G0–G5 → evidence/
```

### Part 1B: TxnSense (needs a free Gemini API key)

```bash
cd Part-1B
cp .env.example .env             # put YOUR key in .env; .env is git-ignored
uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"
export PYTHONPATH=src
python -m txnsense.cli parse "Rs.450.00 debited from A/c XX1234 on 12-11-26 to VPA swiggy@icici UPI Ref 432112345678" --received-at 2026-11-13T09:00:00+05:30
pytest                                              # offline unit tests (fake LLM)
python .harness/run_eval.py --label "my run"        # 25 cases, ~5 min (free-tier pacing)
```

The model defaults to `gemini-3.5-flash-lite` (app) and `gemini-3.5-flash` (judge); override with
`TXNSENSE_MODEL` / `TXNSENSE_JUDGE_MODEL`. Quota and 5xx errors are reported as `INFRA_ERROR`,
never as application results.

## Security

No API key, credential or `.env` file is committed (`.gitignore`; checked with `git grep` over the
full history before every push). `Part-1B/.env.example` contains only a placeholder.

## Tools and AI usage

- Spec Kit `specify-cli` 1.3.3 (integration: `claude`), Python 3.11, ruff, bandit, pytest,
  hypothesis, jsonschema, google-genai.
- Coding agent: Claude Code (Claude Opus 5.5) generated the Spec Kit artifacts, code, tests and
  harnesses under the student's direction. The student made the clarification decisions recorded
  in each spec and the final human ACCEPT/REJECT decisions. Every AI-assisted commit carries a
  `Co-Authored-By` trailer.
- Demo video: terminal recorded with charmbracelet/vhs (real command execution), narrated with
  the student's own cloned voice (Voicebox), assembled with ffmpeg. See [demo/](demo/).
