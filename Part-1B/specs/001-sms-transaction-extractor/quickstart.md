# Quickstart: TxnSense

```bash
cd Part-1B
cp .env.example .env              # put your own Gemini API key in .env (never commit it)
uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"

txnsense parse "Rs.450.00 debited from A/c XX1234 on 12-11-26 to VPA swiggy@icici UPI Ref 432112345678" \
    --received-at 2026-11-13T09:00:00+05:30

pytest                                   # deterministic unit tests (no network)
python .harness/run_eval.py --label "..."  # full evaluation → evidence/
```
