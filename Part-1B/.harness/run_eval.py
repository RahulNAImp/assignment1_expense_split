"""TxnSense single evaluation harness (tasks T017/T018).

Pipeline:  G0 lock check → Q1 pytest → Q2 ruff + bandit
        → for each case in evals/dataset.json:
              app parse_sms()  (INFRA errors retried 3x, then INFRA_ERROR)
              L1 schema → L2 invariants/guardrails → L3 field accuracy + LLM judge
        → aggregate E1..E5 vs .harness/thresholds.json → PASS / FAIL / INCONCLUSIVE

Evidence: evidence/runs/run-NNN/{outputs.jsonl, eval-results.json, feedback.md}
          evidence/eval-results.json (latest), evidence/harness-log.md (appended)

Usage: python .harness/run_eval.py --label "initial generation" [--cases N01,S06] [--no-judge]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess  # nosec B404 - fixed argument lists
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".harness"))

from evaluators import invariants, quality, schema_eval  # noqa: E402
from evaluators.judge import JUDGE_MODEL, Judge  # noqa: E402

from txnsense import parser as app  # noqa: E402
from txnsense.config import SETTINGS  # noqa: E402
from txnsense.llm import GeminiClient, ModelServiceError  # noqa: E402

DATASET = ROOT / "evals" / "dataset.json"
THRESHOLDS = json.loads((ROOT / ".harness" / "thresholds.json").read_text())
EVIDENCE = ROOT / "evidence"
RUNS = EVIDENCE / "runs"
LOG = EVIDENCE / "harness-log.md"
PACE_S = 4.0
BACKOFF = (5, 10, 20)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sh(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)  # nosec B603


def tool(name: str) -> str:
    p = Path(sys.executable).parent / name
    return str(p) if p.exists() else name


# ------------------------------------------------------------------ static gates


def gate_lock() -> dict:
    lock = json.loads((ROOT / ".harness" / "eval.lock").read_text())
    changed = [f for f, h in lock["files"].items() if sha(ROOT / f) != h]
    return {
        "gate": "G0 Eval integrity",
        "status": "FAIL" if changed else "PASS",
        "summary": f"{len(lock['files'])} frozen files, changed={changed}",
    }


def gate_unit() -> dict:
    r = sh([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"])
    last = (r.stdout.strip().splitlines() or [""])[-1]
    return {
        "gate": "Q1 Unit tests",
        "status": "PASS" if r.returncode == 0 else "FAIL",
        "summary": last,
        "stdout": r.stdout[-3000:],
    }


def gate_static() -> dict:
    cfg = str(ROOT / ".harness" / "ruff.toml")
    ruff = sh([tool("ruff"), "check", "--config", cfg, "src", "tests"])
    bandit = sh([tool("bandit"), "-q", "-r", "src", "-ll", "-f", "json"])
    try:
        findings = len(json.loads(bandit.stdout).get("results", []))
    except json.JSONDecodeError:
        findings = -1
    ok = ruff.returncode == 0 and findings == 0
    return {
        "gate": "Q2 Lint/SAST",
        "status": "PASS" if ok else "FAIL",
        "summary": f"ruff rc={ruff.returncode}, bandit >=MEDIUM findings={findings}",
        "stdout": (ruff.stdout + ruff.stderr)[-3000:],
    }


# ------------------------------------------------------------------ per case


def call_app(case: dict, client: GeminiClient) -> tuple[dict | None, str | None, float, int]:
    inp = case["input"]
    attempts = 0
    for wait in (0, *BACKOFF):
        if wait:
            time.sleep(wait)
        attempts += 1
        start = time.perf_counter()
        try:
            out = app.parse_sms(inp["text"], inp["received_at"], inp.get("sender"), client=client)
            return out, None, time.perf_counter() - start, attempts
        except ModelServiceError as exc:
            err = str(exc)
        except Exception as exc:  # application crash = application failure, not infra
            return None, f"APP_EXCEPTION {type(exc).__name__}: {exc}", 0.0, attempts
    return None, f"INFRA_ERROR {err}", 0.0, attempts


def evaluate_case(case: dict, client: GeminiClient, judge: Judge | None) -> dict:
    out, err, latency, attempts = call_app(case, client)
    res: dict = {
        "id": case["id"],
        "tags": case["tags"],
        "traces": case["traces"],
        "attempts": attempts,
        "latency_s": round(latency, 2),
        "output": out,
    }
    if err and err.startswith("INFRA_ERROR"):
        res.update(status="INFRA_ERROR", error=err, score=None)
        return res
    if err:
        res.update(status="FAIL", error=err, schema_valid=False, violations=[], score=0.0)
        return res

    schema_errs = schema_eval.check(out)
    violations = invariants.check(case, out) if not schema_errs else []
    checks = quality.field_checks(case, out, THRESHOLDS["counterparty_similarity_min"])
    fa = quality.accuracy(checks)

    judge_score, judge_reason = None, "n/a"
    deterministic = out.get("intent") == "invalid_input"
    if judge and not schema_errs and not deterministic:
        try:
            time.sleep(PACE_S)
            judge_score, judge_reason = judge.score(
                case["input"]["text"], out, case.get("rubric_note")
            )
        except Exception as exc:  # judge unavailable -> renormalise (EV-02)
            judge_reason = f"judge unavailable: {type(exc).__name__}: {str(exc)[:120]}"

    if schema_errs or violations:
        score = 0.0
    elif judge_score is None:
        score = fa
    else:
        score = THRESHOLDS["field_weight"] * fa + THRESHOLDS["judge_weight"] * judge_score
    res.update(
        status="PASS" if score >= THRESHOLDS["case_pass_score"] else "FAIL",
        schema_valid=not schema_errs,
        schema_errors=schema_errs,
        violations=violations,
        field_checks=checks,
        field_accuracy=round(fa, 3),
        judge_score=None if judge_score is None else round(judge_score, 3),
        judge_reason=judge_reason,
        score=round(score, 3),
    )
    return res


# ------------------------------------------------------------------ aggregate + evidence


def aggregate(results: list[dict]) -> dict:
    t = THRESHOLDS
    infra = [r for r in results if r["status"] == "INFRA_ERROR"]
    scored = [r for r in results if r["status"] != "INFRA_ERROR"]
    n = len(scored) or 1
    schema_rate = sum(bool(r.get("schema_valid")) for r in scored) / n
    violations = sum(len(r.get("violations", [])) for r in scored)
    safety = [r for r in scored if "safety" in r["tags"]]
    safety_rate = sum(r["status"] == "PASS" for r in safety) / (len(safety) or 1)
    mean = sum(r["score"] for r in scored) / n
    infra_rate = len(infra) / (len(results) or 1)
    e = {
        "E1_schema_validity": {
            "value": round(schema_rate, 3),
            "threshold": f">= {t['E1_schema_validity_min']}",
            "ok": schema_rate >= t["E1_schema_validity_min"],
        },
        "E2_violations": {
            "value": violations,
            "threshold": f"<= {t['E2_max_violations']}",
            "ok": violations <= t["E2_max_violations"],
        },
        "E3_safety_pass_rate": {
            "value": round(safety_rate, 3),
            "threshold": f">= {t['E3_safety_pass_rate_min']}",
            "ok": safety_rate >= t["E3_safety_pass_rate_min"],
        },
        "E4_mean_score": {
            "value": round(mean, 3),
            "threshold": f">= {t['E4_mean_score_min']}",
            "ok": mean >= t["E4_mean_score_min"],
        },
        "E5_infra_error_rate": {
            "value": round(infra_rate, 3),
            "threshold": f"<= {t['E5_infra_error_rate_max']}",
            "ok": infra_rate <= t["E5_infra_error_rate_max"],
        },
    }
    quality_ok = all(
        e[k]["ok"]
        for k in ("E1_schema_validity", "E2_violations", "E3_safety_pass_rate", "E4_mean_score")
    )
    if not e["E5_infra_error_rate"]["ok"]:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS" if quality_ok else "FAIL"
    judged = [r for r in scored if r.get("judge_score") is not None]
    judgeable = [
        r
        for r in scored
        if r.get("schema_valid") and (r.get("output") or {}).get("intent") != "invalid_input"
    ]
    judge_cov = {
        "judged": len(judged),
        "judgeable": len(judgeable),
        "coverage": round(len(judged) / (len(judgeable) or 1), 3),
        "note": "informational; unjudged cases are renormalised to field accuracy (EV-02)",
    }
    return {
        "metrics": e,
        "eval_verdict": verdict,
        "judge_coverage": judge_cov,
        "cases": {
            "total": len(results),
            "passed": sum(r["status"] == "PASS" for r in results),
            "failed": sum(r["status"] == "FAIL" for r in results),
            "infra_error": len(infra),
        },
    }


def feedback(run_id: str, results: list[dict], cases: dict[str, dict], gates: list[dict]) -> str:
    out = [
        f"# Evaluation feedback for coding agent — {run_id}",
        "",
        "Fix the root cause in `src/` or `prompts/` (application code, prompt, parser, guardrails).",
        "Do NOT edit evals/dataset.json, .harness/, thresholds, the spec or the schema; do not",
        "remove cases or disable guardrails.",
        "",
    ]
    for g in gates:
        if g["status"] != "PASS":
            out += [
                f"## {g['gate']} — FAIL",
                "",
                g["summary"],
                "```",
                g.get("stdout", ""),
                "```",
                "",
            ]
    for r in results:
        if r["status"] != "FAIL":
            continue
        c = cases[r["id"]]
        out += [
            f"## Case {r['id']} ({', '.join(r['tags'])}) — score {r.get('score')}",
            f"- Traces: {', '.join(c['traces'])}",
            f"- Input: `{c['input']['text'][:300]}` (received_at {c['input']['received_at']})",
        ]
        if r.get("error"):
            out.append(f"- Error: {r['error']}")
        for s in r.get("schema_errors", []):
            out.append(f"- L1 schema: {s}")
        for v in r.get("violations", []):
            out.append(f"- L2 {v['rule']}: {v['detail']}")
        for k, chk in (r.get("field_checks") or {}).items():
            if not chk["ok"]:
                out.append(
                    f"- L3 field `{k}`: expected {chk['expected']!r}, observed {chk['observed']!r}"
                )
        if r.get("judge_score") is not None and r["judge_score"] < 0.75:
            out.append(f"- L3 judge {r['judge_score']}: {r['judge_reason']}")
        out += [
            "- Output:",
            "```json",
            json.dumps(r.get("output"), indent=2, ensure_ascii=False),
            "```",
            "",
        ]
    return "\n".join(out)


def append_log(run_id: str, label: str, result: dict) -> None:
    if not LOG.exists():
        LOG.write_text(
            "# Part 1B Harness Log — TxnSense\n\n## Evaluation runs (appended by run_eval.py)\n"
        )
    agg = result["aggregate"]
    m = agg["metrics"]
    gate_rows = "\n".join(
        f"| {g['gate']} | {g['status']} | {g['summary']} |" for g in result["static_gates"]
    )
    metric_rows = "\n".join(
        f"| {k} | {v['value']} | {v['threshold']} | {'✅' if v['ok'] else '❌'} |"
        for k, v in m.items()
    )
    failed = [r for r in result["results"] if r["status"] != "PASS"]
    fail_rows = (
        "\n".join(
            f"| {r['id']} | {r['status']} | {r.get('score')} | "
            + "; ".join(
                [v["rule"] for v in r.get("violations", [])]
                + [f"{k}" for k, c in (r.get("field_checks") or {}).items() if not c["ok"]]
                + ([r["error"][:60]] if r.get("error") else [])
            )
            + " |"
            for r in failed
        )
        or "| – | – | – | – |"
    )
    cfg = result["config"]
    LOG.open("a", encoding="utf-8").write(
        f"\n### {run_id} — {label} — **{result['overall']}**\n\n"
        f"- Time (UTC): {result['timestamp']} · commit `{cfg['git_commit']}`\n"
        f"- App model `{cfg['app_model']}` (temperature {cfg['temperature']}), judge `{cfg['judge_model']}`, "
        f"prompt `{cfg['prompt_version']}`, dataset `{cfg['dataset_sha256'][:12]}`\n"
        f"- Cases: {agg['cases']}\n- LLM-judge coverage: {agg.get('judge_coverage')}\n"
        f"- Results: `evidence/runs/{run_id}/`\n\n"
        f"| Gate | Status | Summary |\n|---|---|---|\n{gate_rows}\n\n"
        f"| Metric | Value | Threshold | OK |\n|---|---|---|---|\n{metric_rows}\n\n"
        f"Non-passing cases:\n\n| Case | Status | Score | Failed checks |\n|---|---|---|---|\n{fail_rows}\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="manual run")
    ap.add_argument("--cases", help="comma-separated subset (debug only; logged)")
    ap.add_argument("--no-judge", action="store_true")
    args = ap.parse_args()

    dataset = json.loads(DATASET.read_text())
    cases = {c["id"]: c for c in dataset["cases"]}
    selected = [cases[i] for i in args.cases.split(",")] if args.cases else list(cases.values())
    label = args.label + (f" [subset: {args.cases}]" if args.cases else "")

    RUNS.mkdir(parents=True, exist_ok=True)
    n = max([int(p.name.split("-")[1]) for p in RUNS.glob("run-*")], default=0) + 1
    run_id = f"run-{n:03d}"
    run_dir = RUNS / run_id
    run_dir.mkdir()
    print(f"== TxnSense eval {run_id}: {label}  ({len(selected)} cases)", flush=True)

    gates = [gate_lock(), gate_unit(), gate_static()]
    for g in gates:
        print(f"  [{g['status']}] {g['gate']}: {g['summary']}", flush=True)

    client = GeminiClient()
    judge = None if args.no_judge else Judge()
    results = []
    with (run_dir / "outputs.jsonl").open("w", encoding="utf-8") as fh:
        for i, case in enumerate(selected):
            if i:
                time.sleep(PACE_S)
            r = evaluate_case(case, client, judge)
            results.append(r)
            fh.write(json.dumps({"id": r["id"], "output": r["output"]}, ensure_ascii=False) + "\n")
            viol = ",".join(v["rule"] for v in r.get("violations", []))
            print(
                f"  {r['id']:<4} {r['status']:<11} score={r.get('score')} "
                f"intent={(r['output'] or {}).get('intent')} {viol}",
                flush=True,
            )

    agg = aggregate(results)
    static_ok = all(g["status"] == "PASS" for g in gates)
    overall = agg["eval_verdict"] if static_ok or agg["eval_verdict"] == "INCONCLUSIVE" else "FAIL"
    import google.genai as gg

    result = {
        "run_id": run_id,
        "label": label,
        "overall": overall,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": {
            "app_model": SETTINGS.model,
            "temperature": SETTINGS.temperature,
            "judge_model": None if args.no_judge else JUDGE_MODEL,
            "prompt_version": app.prompt_version(),
            "dataset_sha256": sha(DATASET),
            "thresholds": THRESHOLDS,
            "google_genai": gg.__version__,
            "python": platform.python_version(),
            "git_commit": sh(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()
            + (
                "+dirty"
                if sh(["git", "status", "--porcelain", "src", "prompts"]).stdout.strip()
                else ""
            ),
        },
        "static_gates": gates,
        "aggregate": agg,
        "results": results,
    }
    (run_dir / "eval-results.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    if not args.cases:
        (EVIDENCE / "eval-results.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        )
    if overall != "PASS":
        (run_dir / "feedback.md").write_text(feedback(run_id, results, cases, gates))
    append_log(run_id, label, result)

    print("  metrics:", {k: v["value"] for k, v in agg["metrics"].items()})
    print("  judge coverage:", agg["judge_coverage"])
    print(f"== OVERALL: {overall}  (evidence/runs/{run_id}/)")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
