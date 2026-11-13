"""Create the integrity lock (gate G0) over the approved spec and the spec-derived tests.

Run ONLY by a human after reviewing spec/tests (task T018), or after a documented spec revision.
The coding agent must not run this to make a failing G0 pass.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCKED = ["specs/001-group-expense-splitter/spec.md", "tests"]


def locked_files() -> list[Path]:
    files: list[Path] = []
    for entry in LOCKED:
        p = ROOT / entry
        if p.is_file():
            files.append(p)
        else:
            files.extend(sorted(f for f in p.rglob("*.py") if "__pycache__" not in f.parts))
    return files


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    reason = " ".join(sys.argv[1:]) or "initial approval (T018)"
    lock = {
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": reason,
        "files": {str(f.relative_to(ROOT)): digest(f) for f in locked_files()},
    }
    (ROOT / ".harness" / "integrity.lock").write_text(json.dumps(lock, indent=2) + "\n")
    print(f"locked {len(lock['files'])} files: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
