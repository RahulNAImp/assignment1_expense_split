# Quickstart: SplitKaro

```bash
cd Part-1A
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

export SPLITKARO_DATA=/tmp/demo.json
splitkaro group create goa --members ravi,asha,meera
splitkaro expense add goa --paid-by ravi --amount 900 --desc Dinner
splitkaro expense add goa --paid-by asha --amount 300 --desc Cab
splitkaro balances goa        # asha -100.00, meera -400.00, ravi +500.00  (AC-020)
splitkaro settle goa          # meera -> ravi 400.00, asha -> ravi 100.00
splitkaro pay goa --from meera --to ravi --amount 400

python .harness/run_harness.py   # runs gates G0–G5, writes evidence/
```
