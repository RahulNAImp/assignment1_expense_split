"""Record v3 tapes and jump-cut long dead waits (reuses demo/v2/record_all.trim)."""

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("rec", HERE.parent / "v2" / "record_all.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)

TRIM = {"v08_harness"}

for name in sys.argv[1:]:
    subprocess.run(["vhs", str(HERE / "tapes" / f"{name}.tape")], cwd=ROOT, capture_output=True, check=True)
    out = HERE / "build" / f"{name}.mp4"
    if name in TRIM:  # only scenes whose long freeze is a dead wait (harness computing)
        rec.trim(out)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                       capture_output=True, text=True).stdout
    print(f"{name}: {float(d):.1f}s", flush=True)
