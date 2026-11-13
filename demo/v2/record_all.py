"""Record every scene tape with vhs, then jump-cut long dead waits (> 12 s frozen screen,
e.g. the harness computing before it prints) down to 1.5 s. Run from the repo root."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAPES = ROOT / "demo" / "v2" / "tapes"
BUILD = ROOT / "demo" / "v2" / "build"
MAX_FREEZE, KEEP = 12.0, 1.5


def freezes(path: Path) -> list[tuple[float, float]]:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf",
                          "freezedetect=n=0.001:d=3", "-map", "0:v", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"freeze_start: ([0-9.]+)", err)]
    ends = [float(x) for x in re.findall(r"freeze_end: ([0-9.]+)", err)]
    return list(zip(starts, ends))


def trim(path: Path) -> None:
    cuts = [(a + KEEP, b) for a, b in freezes(path) if b - a > MAX_FREEZE]
    if not cuts:
        return
    keep, t = [], 0.0
    for a, b in cuts:
        keep.append((t, a))
        t = b
    keep.append((t, None))
    parts = "".join(
        f"[0:v]trim=start={s}{f':end={e}' if e else ''},setpts=PTS-STARTPTS[p{i}];"
        for i, (s, e) in enumerate(keep))
    graph = parts + "".join(f"[p{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=1[v]"
    raw = path.with_suffix(".raw.mp4")
    path.rename(raw)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-filter_complex", graph,
                    "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                    str(path)], check=True)
    print(f"   trimmed {path.name}: cut {[(round(a, 1), round(b, 1)) for a, b in cuts]}")


def main(names: list[str]) -> None:
    for tape in sorted(TAPES.glob("*.tape")):
        if names and tape.stem not in names:
            continue
        subprocess.run(["vhs", str(tape)], cwd=ROOT, capture_output=True, check=True)
        out = BUILD / f"{tape.stem}.mp4"
        trim(out)
        dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout
        print(f"{tape.stem}: {float(dur):.1f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
