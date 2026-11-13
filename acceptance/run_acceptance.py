"""One-shot acceptance test on NEW data (not used by the spec tests or evals/dataset.json).

Part 1A: replays acceptance/part1a_flat302.json against the real SplitKaro CLI and compares exact
         stdout / stderr / exit codes with hand-computed expectations.
Part 1B: runs acceptance/part1b_holdout.json through the real TxnSense app (live Gemini) and scores
         each output with the harness's own L1 schema, L2 invariant/guardrail and L3 field checks.
         No LLM judge, to save quota. A case passes when it is schema-valid, has 0 violations and
         field accuracy >= 0.80 (the spec's case threshold).

Run with the Part 1B venv (it can also import Part 1A, which is stdlib-only):
    Part-1B/.venv/bin/python acceptance/run_acceptance.py
Writes acceptance/RESULTS.md and acceptance/results.json.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT / "Part-1A" / "src"), str(ROOT / "Part-1B" / "src"),
                str(ROOT / "Part-1B" / ".harness")]


# ----------------------------------------------------------------------------- Part 1A


def run_1a() -> list[dict]:
    from splitkaro.cli import main

    spec = json.loads((HERE / "part1a_flat302.json").read_text())
    os.environ["SPLITKARO_NOW"] = "2026-11-13T20:00:00Z"
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / "flat302.json"
        for step in spec["steps"]:
            target = data
            if "corrupt_file" in step:
                target = Path(tmp) / "corrupt.json"
                target.write_text(step["corrupt_file"])
                before = target.read_bytes()
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    code = main(["--data", str(target), *step["args"]])
                except SystemExit as exc:
                    code = exc.code
            stdout, stderr = out.getvalue().strip(), err.getvalue().strip()
            problems = []
            if code != step["exit"]:
                problems.append(f"exit {code} != expected {step['exit']}")
            if "stdout" in step and stdout != step["stdout"]:
                problems.append(f"stdout mismatch:\n  expected: {step['stdout']!r}\n  observed: {stdout!r}")
            if "stderr_contains" in step and step["stderr_contains"] not in stderr:
                problems.append(f"stderr missing {step['stderr_contains']!r}; got {stderr!r}")
            if "json_check" in step:
                rows = {str(e["id"]): e["shares_paise"] for e in json.loads(stdout)}
                for eid, shares in step["json_check"].items():
                    if rows.get(eid) != shares:
                        problems.append(f"expense {eid} shares {rows.get(eid)} != {shares}")
            if "corrupt_file" in step and target.read_bytes() != before:
                problems.append("corrupt file was modified")
            results.append({"id": step["id"], "what": step["what"], "traces": step["traces"],
                            "status": "PASS" if not problems else "FAIL", "problems": problems,
                            "exit": code, "stdout": stdout, "stderr": stderr})
    return results


# ----------------------------------------------------------------------------- Part 1B


def run_1b() -> tuple[list[dict], dict]:
    from evaluators import invariants, quality, schema_eval
    from txnsense.config import SETTINGS
    from txnsense.llm import GeminiClient, ModelServiceError
    from txnsense.parser import parse_sms, prompt_version

    cases = json.loads((HERE / "part1b_holdout.json").read_text())["cases"]
    client = GeminiClient()
    results = []
    for i, case in enumerate(cases):
        if i:
            time.sleep(4)
        out, err = None, None
        for wait in (0, 5, 10, 20):
            time.sleep(wait)
            try:
                inp = case["input"]
                out = parse_sms(inp["text"], inp["received_at"], client=client)
                err = None
                break
            except ModelServiceError as exc:
                err = f"INFRA_ERROR {exc}"
        if out is None:
            results.append({"id": case["id"], "tags": case["tags"], "status": "INFRA_ERROR",
                            "error": err})
            continue
        schema = schema_eval.check(out)
        viol = invariants.check(case, out) if not schema else []
        checks = quality.field_checks(case, out, 0.6)
        fa = quality.accuracy(checks)
        ok = not schema and not viol and fa >= 0.8
        results.append({
            "id": case["id"], "tags": case["tags"], "traces": case["traces"],
            "status": "PASS" if ok else "FAIL", "schema_errors": schema, "violations": viol,
            "field_accuracy": round(fa, 3),
            "failed_fields": {k: {"expected": v["expected"], "observed": v["observed"]}
                              for k, v in checks.items() if not v["ok"]},
            "output": out,
        })
        print(f"  {case['id']} {results[-1]['status']} fa={fa:.2f} intent={out.get('intent')}",
              flush=True)
    cfg = {"app_model": SETTINGS.model, "temperature": SETTINGS.temperature,
           "prompt_version": prompt_version()}
    return results, cfg


# ----------------------------------------------------------------------------- report


def main() -> int:
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("== Part 1A: SplitKaro flat-302 scenario")
    r1a = run_1a()
    for r in r1a:
        print(f"  {r['id']} {r['status']}  {r['what']}")
    print("== Part 1B: TxnSense holdout (live Gemini)")
    r1b, cfg = run_1b()

    in_scope = [r for r in r1b if "out_of_scope" not in r["tags"]]
    a_pass = sum(r["status"] == "PASS" for r in r1a)
    b_pass = sum(r["status"] == "PASS" for r in in_scope)
    b_infra = sum(r["status"] == "INFRA_ERROR" for r in r1b)
    safety = [r for r in in_scope if "safety" in r["tags"]]
    s_pass = sum(r["status"] == "PASS" for r in safety)
    leaks = [v for r in r1b for v in r.get("violations", [])
             if v["rule"].startswith("GR") or v["rule"] == "MUST_NOT_CONTAIN"]

    md = [
        "# Acceptance test: one-shot run on new data", "",
        f"- Run at (UTC): {stamp}",
        f"- Part 1B model: `{cfg['app_model']}` (temperature {cfg['temperature']}), "
        f"prompt `{cfg['prompt_version']}`",
        "- Data: [part1a_flat302.json](part1a_flat302.json), "
        "[part1b_holdout.json](part1b_holdout.json). Neither is used by the spec tests or the "
        "eval dataset.",
        "- Runner: [run_acceptance.py](run_acceptance.py). Raw outputs: [results.json](results.json)",
        "",
        "## Summary", "",
        "| Part | Result |", "|---|---|",
        f"| 1A SplitKaro scenario | **{a_pass}/{len(r1a)} steps PASS** |",
        f"| 1B TxnSense holdout (in scope) | **{b_pass}/{len(in_scope)} cases PASS** "
        f"(safety {s_pass}/{len(safety)}, guardrail leaks {len(leaks)}, infra errors {b_infra}) |",
        "",
        "## Part 1A: flat-302 scenario (exact expected output)", "",
        "| Step | What | Traces | Result |", "|---|---|---|---|",
    ]
    for r in r1a:
        md.append(f"| {r['id']} | {r['what']} | {', '.join(r['traces'])} | {r['status']} |")
    for r in r1a:
        if r["problems"]:
            md += ["", f"**{r['id']} problems:**", "```", *r["problems"], "```"]
    md += ["", "## Part 1B: holdout SMS (live model)", "",
           "| Case | Tags | Intent | Field acc. | Violations | Result |",
           "|---|---|---|---|---|---|"]
    for r in r1b:
        intent = (r.get("output") or {}).get("intent", "–")
        viol = ", ".join(v["rule"] for v in r.get("violations", [])) or "–"
        status = r["status"] + (" (out of scope, not counted)" if "out_of_scope" in r["tags"] else "")
        md.append(f"| {r['id']} | {', '.join(r['tags'])} | {intent} | "
                  f"{r.get('field_accuracy', '–')} | {viol} | {status} |")
    fails = [r for r in r1b if r.get("failed_fields") or r.get("violations") or r.get("schema_errors")]
    if fails:
        md += ["", "### Details of non-perfect cases", ""]
        for r in fails:
            md.append(f"- **{r['id']}**: failed fields {json.dumps(r.get('failed_fields'))}; "
                      f"violations {json.dumps(r.get('violations'))}")
    md += ["", "## Reviewer notes (student)", "", "> Add your observations here.", ""]
    (HERE / "RESULTS.md").write_text("\n".join(md))
    (HERE / "results.json").write_text(json.dumps(
        {"run_at": stamp, "config_1b": cfg, "part1a": r1a, "part1b": r1b}, indent=2,
        ensure_ascii=False) + "\n")
    print(f"== 1A {a_pass}/{len(r1a)} PASS · 1B {b_pass}/{len(in_scope)} PASS (in scope) "
          f"· leaks {len(leaks)} · infra {b_infra}  -> acceptance/RESULTS.md")
    return 0 if a_pass == len(r1a) and b_pass == len(in_scope) else 1


if __name__ == "__main__":
    raise SystemExit(main())
