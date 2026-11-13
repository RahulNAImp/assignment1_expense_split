"""Measure narration + screen recordings and write demo/video/src/timeline.json for Remotion.

Copies assets into demo/video/public/{audio,clips}. Scene length = max(voice + 1.2 s, clip).
"""

import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
BUILD = HERE / "build"
VIDEO = HERE.parent / "video"
FPS = 30
SCENES = [
    ("s01_title", "card", "", ""),
    ("s02_workflow", "card", "", ""),
    ("s03_1a_spec", "clip", "PART 1A", "Constitution gates and a spec-driven decision"),
    ("s04_1a_demo", "clip", "PART 1A", "SplitKaro running: exact paise, deterministic settle-up"),
    ("s05_1a_harness", "clip", "PART 1A", "Harness: 6 gates, a real failure, a real repair"),
    ("s06_1b_spec", "clip", "PART 1B", "Contract, guardrails and a threshold declared up front"),
    ("s07_1b_demo", "clip", "PART 1B", "TxnSense live on Gemini: normal, phishing, injection"),
    ("s08_1b_harness", "clip", "PART 1B", "Evaluation harness: run-001 FAIL, repair, final PASS"),
    ("s09_acceptance", "clip", "ACCEPTANCE", "New data: 10/11, diagnose H06, fix, 11/11"),
    ("s10_outro", "card", "", ""),
]


def dur(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main() -> None:
    (VIDEO / "public" / "audio").mkdir(parents=True, exist_ok=True)
    (VIDEO / "public" / "clips").mkdir(parents=True, exist_ok=True)
    scenes = []
    for sid, kind, tag, caption in SCENES:
        audio = BUILD / "audio" / f"{sid}.wav"
        a = dur(audio)
        shutil.copy(audio, VIDEO / "public" / "audio" / audio.name)
        entry = {"id": sid, "kind": kind, "tag": tag, "caption": caption,
                 "audio": f"audio/{audio.name}", "audioSec": round(a, 3)}
        length = a + 1.2
        if kind == "clip":
            clip = BUILD / f"{sid}.mp4"
            v = dur(clip)
            shutil.copy(clip, VIDEO / "public" / "clips" / clip.name)
            entry.update(clip=f"clips/{clip.name}", clipSec=round(v, 3),
                         clipFrames=int(v * FPS) - 1)
            length = max(length, v + 0.5)
        entry["frames"] = int(round(length * FPS))
        scenes.append(entry)
        print(f"{sid:<16} voice {a:6.1f}s clip {entry.get('clipSec', 0):6.1f}s -> {length:6.1f}s")
    total = sum(s["frames"] for s in scenes)
    (VIDEO / "src" / "timeline.json").write_text(
        json.dumps({"fps": FPS, "totalFrames": total, "scenes": scenes}, indent=2) + "\n")
    print(f"total {total / FPS:.1f}s ({total} frames)")


if __name__ == "__main__":
    main()
