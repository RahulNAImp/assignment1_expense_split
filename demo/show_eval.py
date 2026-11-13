"""Print a compact comparison of saved TxnSense evaluation runs (used in the demo video)."""

import json
import sys
from pathlib import Path

RUNS = Path(__file__).resolve().parent.parent / "Part-1B" / "evidence" / "runs"

BRIEF = "--brief" in sys.argv
for run in [a for a in sys.argv[1:] if not a.startswith("--")]:
    r = json.loads((RUNS / run / "eval-results.json").read_text())
    agg = r["aggregate"]
    print(f"\n{run}  ->  {r['overall']}" if BRIEF else f"\n{run}  [{r['label']}]  ->  {r['overall']}")
    print(f"  model={r['config']['app_model']} judge={r['config']['judge_model']} "
          f"prompt={r['config']['prompt_version']}  cases={agg['cases']}")
    for k, v in agg["metrics"].items():
        print(f"  {'OK ' if v['ok'] else 'XX '} {k:<22} {v['value']!s:<7} (threshold {v['threshold']})")
    for c in r["results"]:
        if c["id"] == "S02" and not BRIEF:
            t = (c["output"] or {}).get("transaction") or {}
            print(f"  S02 -> intent={c['output']['intent']} amount={t.get('amount')} "
                  f"merchant={t.get('counterparty')} status={c['status']}")
