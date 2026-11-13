"""SplitKaro deterministic harness (task T027).

Runs every quality gate from the constitution, independently of the generated implementation:

    G0 Integrity      approved spec + spec-derived tests unchanged (SHA-256 vs integrity.lock)
    G1 Lint & format  ruff check + ruff format --check
    G2 Security/SAST  bandit, severity >= MEDIUM
    G3 Spec tests     pytest, 100 % pass, 0 skipped/xfailed
    G4 Coverage       line coverage of src/ >= threshold
    G5 Traceability   every AC-xxx in spec referenced by >= 1 test

All gates always run (no short-circuit) so one execution yields complete evidence.

Outputs
    evidence/harness-results/run-NNN.json      machine-readable result
    evidence/harness-results/run-NNN-feedback.md  structured failure evidence for the coding agent
    evidence/harness-log.md                    appended human-readable entry

Usage:  python .harness/run_harness.py --label "initial generation"
Exit code: 0 = all gates PASS, 1 = at least one gate FAIL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed argument lists, no shell
import sys
import tempfile
import xml.etree.ElementTree as ET  # nosec B405 - parses our own pytest junit output
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / ".harness"
EVIDENCE = ROOT / "evidence"
RESULTS = EVIDENCE / "harness-results"
LOG = EVIDENCE / "harness-log.md"
SPEC = ROOT / "specs" / "001-group-expense-splitter" / "spec.md"
GATES = json.loads((HARNESS / "gates.json").read_text())
RUFF_CFG = str(HARNESS / "ruff.toml")
BIN = Path(sys.executable).parent


def tool(name: str) -> str:
    candidate = BIN / name
    return str(candidate) if candidate.exists() else name


def sh(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)  # nosec B603


def clip(text: str, limit: int = 4000) -> str:
    return text if len(text) <= limit else text[:limit] + f"\n... [{len(text) - limit} chars cut]"


# --------------------------------------------------------------------------- gates


def gate_integrity() -> dict:
    lock = json.loads((HARNESS / "integrity.lock").read_text())
    changed, missing = [], []
    for rel, expected in lock["files"].items():
        p = ROOT / rel
        if not p.exists():
            missing.append(rel)
        elif hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            changed.append(rel)
    current_tests = {
        str(f.relative_to(ROOT))
        for f in (ROOT / "tests").rglob("*.py")
        if "__pycache__" not in f.parts
    }
    added = sorted(current_tests - set(lock["files"]))
    ok = not changed and not missing
    return {
        "gate": "G0 Integrity",
        "status": "PASS" if ok else "FAIL",
        "summary": f"{len(lock['files'])} locked files; changed={len(changed)} "
        f"missing={len(missing)} new_tests={len(added)}",
        "details": {"changed": changed, "missing": missing, "new_unlocked_tests": added,
                    "lock_reason": lock.get("reason")},
    }


def gate_lint() -> dict:
    check = sh([tool("ruff"), "check", "--config", RUFF_CFG, "--output-format", "json",
                "src", "tests"])
    fmt = sh([tool("ruff"), "format", "--config", RUFF_CFG, "--check", "src", "tests"])
    try:
        violations = json.loads(check.stdout or "[]")
    except json.JSONDecodeError:
        violations = [{"code": "RUFF-ERROR", "message": check.stderr}]
    unformatted = [ln for ln in fmt.stdout.splitlines() if ln.startswith("Would reformat")]
    items = [
        {
            "rule": v.get("code"),
            "file": str(Path(v.get("filename", "")).relative_to(ROOT))
            if v.get("filename") else "",
            "line": (v.get("location") or {}).get("row"),
            "message": v.get("message"),
        }
        for v in violations
    ]
    total = len(items) + len(unformatted)
    ok = total <= GATES["lint_max_violations"] and fmt.returncode in (0, 1)
    return {
        "gate": "G1 Lint & format",
        "status": "PASS" if ok else "FAIL",
        "summary": f"{len(items)} lint violation(s), {len(unformatted)} file(s) need formatting",
        "details": {"violations": items, "unformatted": unformatted},
        "stdout": clip(fmt.stdout + fmt.stderr),
    }


def gate_security() -> dict:
    res = sh([tool("bandit"), "-r", "src", "-f", "json", "-q"])
    try:
        report = json.loads(res.stdout)
    except json.JSONDecodeError:
        return {"gate": "G2 Security/SAST", "status": "FAIL", "summary": "bandit did not run",
                "stdout": clip(res.stdout), "stderr": clip(res.stderr)}
    order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    floor = order[GATES["bandit_min_severity"]]
    findings = [
        {
            "test_id": r["test_id"],
            "severity": r["issue_severity"],
            "confidence": r["issue_confidence"],
            "file": str(Path(r["filename"])),
            "line": r["line_number"],
            "message": r["issue_text"],
        }
        for r in report.get("results", [])
    ]
    blocking = [f for f in findings if order.get(f["severity"], 0) >= floor]
    ok = len(blocking) <= GATES["bandit_max_findings"]
    return {
        "gate": "G2 Security/SAST",
        "status": "PASS" if ok else "FAIL",
        "summary": f"{len(blocking)} finding(s) >= {GATES['bandit_min_severity']} "
        f"({len(findings)} total incl. LOW)",
        "details": {"blocking": blocking, "all": findings},
    }


def gate_tests_and_coverage() -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory() as tmp:
        junit = Path(tmp) / "junit.xml"
        cov = Path(tmp) / "cov.json"
        res = sh([
            sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            f"--junitxml={junit}", "--cov=src/splitkaro", f"--cov-report=json:{cov}",
            "--cov-report=term-missing:skip-covered",
        ])
        failures, total, skipped = [], 0, 0
        if junit.exists():
            tree = ET.parse(junit)  # nosec B314 - trusted local file produced above
            for case in tree.iter("testcase"):
                total += 1
                name = f"{case.get('classname')}::{case.get('name')}"
                for tag in ("failure", "error"):
                    node = case.find(tag)
                    if node is not None:
                        m = re.search(r"ac(\d{3})", case.get("name", ""), re.I)
                        failures.append({
                            "test": name,
                            "acceptance_criterion": f"AC-{m.group(1)}" if m else None,
                            "kind": tag,
                            "message": (node.get("message") or "")[:500],
                            "detail": clip(node.text or "", 2500),
                        })
                if case.find("skipped") is not None:
                    skipped += 1
        cov_pct = None
        missing_lines = {}
        if cov.exists():
            data = json.loads(cov.read_text())
            cov_pct = round(data["totals"]["percent_covered"], 2)
            missing_lines = {
                f: d["missing_lines"] for f, d in data["files"].items() if d["missing_lines"]
            }
    passed = total - len(failures) - skipped
    tests_ok = (
        total > 0 and not failures and skipped <= GATES["tests_max_skipped"]
        and res.returncode in (0, 1)
    )
    tests = {
        "gate": "G3 Spec tests",
        "status": "PASS" if tests_ok else "FAIL",
        "summary": f"{passed}/{total} passed, {len(failures)} failed, {skipped} skipped",
        "details": {"failures": failures},
        "stdout": clip(res.stdout, 6000),
        "stderr": clip(res.stderr, 2000),
    }
    cov_ok = cov_pct is not None and cov_pct >= GATES["coverage_min_percent"]
    coverage = {
        "gate": "G4 Coverage",
        "status": "PASS" if cov_ok else "FAIL",
        "summary": f"{cov_pct}% line coverage (threshold {GATES['coverage_min_percent']}%)",
        "details": {"percent": cov_pct, "missing_lines": missing_lines},
    }
    return tests, coverage


def gate_traceability() -> dict:
    spec_acs = sorted(set(re.findall(r"\bAC-(\d{3})\b", SPEC.read_text())))
    test_text = "\n".join(
        f.read_text() for f in (ROOT / "tests").rglob("*.py") if "__pycache__" not in f.parts
    )
    referenced = set(re.findall(r"(?i)ac[-_]?(\d{3})", test_text))
    untested = [f"AC-{a}" for a in spec_acs if a not in referenced]
    return {
        "gate": "G5 Traceability",
        "status": "PASS" if not untested else "FAIL",
        "summary": f"{len(spec_acs) - len(untested)}/{len(spec_acs)} acceptance criteria "
        "referenced by tests",
        "details": {"untested": untested},
    }


# --------------------------------------------------------------------------- evidence


def next_run_number() -> int:
    nums = [int(m.group(1)) for p in RESULTS.glob("run-*.json")
            if (m := re.match(r"run-(\d+)\.json", p.name))]
    return max(nums, default=0) + 1


def feedback_markdown(run_id: str, gates: list[dict]) -> str:
    lines = [
        f"# Harness feedback for coding agent — {run_id}",
        "",
        "Repair the implementation in `src/` so that the failing gates pass.",
        "Rules (constitution IV): do NOT edit the spec, the tests, `.harness/`, or thresholds;",
        "do NOT add skip/xfail/noqa/nosec to silence a gate. Fix the root cause.",
        "",
    ]
    for g in gates:
        if g["status"] == "PASS":
            continue
        lines += [f"## {g['gate']} — FAIL", "", f"Summary: {g['summary']}", ""]
        d = g.get("details", {})
        for f in d.get("failures", []):
            lines += [
                f"### Failed test `{f['test']}`",
                f"- Acceptance criterion: {f['acceptance_criterion'] or 'n/a'}",
                f"- Expected vs observed: `{f['message']}`",
                "```text", f["detail"].strip(), "```", "",
            ]
        for v in d.get("violations", []):
            lines.append(f"- `{v['rule']}` {v['file']}:{v['line']} — {v['message']}")
        for f in d.get("blocking", []):
            lines.append(f"- `{f['test_id']}` ({f['severity']}) {f['file']}:{f['line']} — "
                         f"{f['message']}")
        if d.get("untested"):
            lines.append(f"- Untested acceptance criteria: {', '.join(d['untested'])}")
        if d.get("changed") or d.get("missing"):
            lines.append(f"- Locked files changed: {d.get('changed')} missing: {d.get('missing')}")
        if g["gate"] == "G4 Coverage":
            lines.append(f"- Uncovered lines: {json.dumps(d.get('missing_lines'))}")
        lines.append("")
    return "\n".join(lines)


def append_log(run_id: str, label: str, result: dict) -> None:
    if not LOG.exists():
        LOG.write_text("# Part 1A Harness Log — SplitKaro\n\n")
    rows = "\n".join(
        f"| {g['gate']} | {'✅ PASS' if g['status'] == 'PASS' else '❌ FAIL'} | {g['summary']} |"
        for g in result["gates"]
    )
    entry = (
        f"\n### {run_id} — {label} — **{result['overall']}**\n\n"
        f"- Time (UTC): {result['timestamp']}\n"
        f"- Git commit under test: `{result['git_commit']}`\n"
        f"- Result file: `evidence/harness-results/{run_id}.json`\n"
        + (f"- Feedback for agent: `evidence/harness-results/{run_id}-feedback.md`\n"
           if result["overall"] == "FAIL" else "")
        + f"\n| Gate | Result | Summary |\n|------|--------|---------|\n{rows}\n"
    )
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="manual run")
    args = ap.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    run_id = f"run-{next_run_number():03d}"
    print(f"== SplitKaro harness {run_id}: {args.label}")

    gates = [gate_integrity(), gate_lint(), gate_security()]
    tests, coverage = gate_tests_and_coverage()
    gates += [tests, coverage, gate_traceability()]
    overall = "PASS" if all(g["status"] == "PASS" for g in gates) else "FAIL"

    commit = sh(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()
    dirty = bool(sh(["git", "status", "--porcelain", "src"]).stdout.strip())
    result = {
        "run_id": run_id,
        "label": args.label,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": commit + ("+uncommitted-src" if dirty else ""),
        "python": sys.version.split()[0],
        "thresholds": GATES,
        "overall": overall,
        "gates": gates,
    }
    (RESULTS / f"{run_id}.json").write_text(json.dumps(result, indent=2) + "\n")
    if overall == "FAIL":
        (RESULTS / f"{run_id}-feedback.md").write_text(feedback_markdown(run_id, gates))
    append_log(run_id, args.label, result)

    for g in gates:
        print(f"  [{g['status']}] {g['gate']}: {g['summary']}")
    print(f"== OVERALL: {overall}  (evidence/harness-results/{run_id}.json)")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
