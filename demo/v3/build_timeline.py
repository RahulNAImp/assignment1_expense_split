"""Write demo/video/src/v3/timeline.json from voice beats + console clips (demo v3)."""

import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
VIDEO = HERE.parent / "video"
V2 = HERE.parent / "v2" / "build"
FPS = 30
# id: (slide, clip path, clip starts at beat, tag, caption)
SCENES = {
    "v01_intro": ("intro", None, 0, "", ""),
    "v02_split_idea": ("split_idea", None, 0, "", ""),
    "v03_split_shares": ("split_shares", None, 0, "", ""),
    "v04_split_balance": ("split_balance", None, 0, "", ""),
    "v05_split_settle": ("split_settle", None, 0, "", ""),
    "v06_split_console": (None, HERE / "build" / "v06_split_console.mp4", 0, "PART 1A", "Same example, running live in the terminal"),
    "v07_split_code": (None, HERE / "build" / "v07_split_code.mp4", 0, "PART 1A", "The real code, and its tests passing"),
    "v08_harness": ("harness", HERE / "build" / "v08_harness.mp4", 2, "PART 1A", "One command: all 6 checks PASS"),
    "v09_txn_idea": ("txn_idea", None, 0, "", ""),
    "v10_txn_console": (None, HERE / "build" / "v10_txn_console.mp4", 0, "PART 1B", "Live Gemini calls: normal, scam, trick message"),
    "v11_txn_eval": ("eval", HERE / "build" / "v11_txn_eval.mp4", 1, "PART 1B", "Final result: 25 / 25 pass"),
    "v12_outro": ("outro", None, 0, "", ""),
}


def dur(p: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def main() -> None:
    beats = json.loads((HERE / "build" / "beats.json").read_text())
    pub = VIDEO / "public" / "v3"
    pub.mkdir(parents=True, exist_ok=True)
    out = []
    for sid, (slide, clip, from_beat, tag, caption) in SCENES.items():
        b = beats[sid]
        a = b["audioSec"]
        shutil.copy(HERE / "build" / "audio" / f"{sid}.wav", pub / f"{sid}.wav")
        e = {"id": sid, "audio": f"v3/{sid}.wav", "beats": b["beats"], "tag": tag, "caption": caption}
        if slide:
            e["slide"] = slide
        length = a + 0.9 if clip else max(a + 1.8, 6.0)  # slides get reading time
        if clip:
            v = dur(clip)
            shutil.copy(clip, pub / f"{sid}.mp4")
            start = b["beats"][from_beat] if from_beat else 0.0
            e.update(clip=f"v3/{sid}.mp4", clipFrames=int(v * FPS) - 1, clipFromBeat=from_beat)
            length = max(length, start + v + 0.3)  # console demo always plays in full
        e["frames"] = int(round(length * FPS))
        out.append(e)
        print(f"{sid:<18} voice {a:5.1f}s  clip {dur(clip) if clip else 0:5.1f}s -> {length:5.1f}s  beats {b['beats']}")
    total = sum(e["frames"] for e in out)
    (VIDEO / "src" / "v3" / "timeline.json").write_text(json.dumps({"fps": FPS, "totalFrames": total, "scenes": out}, indent=2))
    print(f"total {total / FPS:.1f}s")


if __name__ == "__main__":
    main()
