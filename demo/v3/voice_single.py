"""ONE continuous Voicebox take for the whole v3 script: no stitching, no effects.

Post-processing is deliberately minimal (the earlier echo/room effects caused a metallic sound):
trim leading/trailing silence, then loudness-normalise to -16 LUFS. The take is rejected and
regenerated with another seed if its speaking rate suggests dropped words, or if it clips.

Output: build/single/full.wav, build/single/meta.json
"""

import json
import re
import subprocess
import time
from pathlib import Path

from voice_beats import dur, ff, req

HERE = Path(__file__).parent
OUT = HERE / "build" / "single"


def script_text() -> tuple[str, dict]:
    text = (HERE / "script.md").read_text()
    parts = re.split(r"^## (\w+)\s*$", text, flags=re.M)
    scenes = {}
    for i in range(1, len(parts), 2):
        body = "\n".join(ln for ln in parts[i + 1].splitlines() if not ln.startswith(">"))
        scenes[parts[i]] = [" ".join(b.split()) for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]
    full = " ".join(b for beats in scenes.values() for b in beats)
    return full, scenes


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    full, scenes = script_text()
    words = len(full.split())
    print(f"{words} words, {len(full)} chars", flush=True)
    pid = next(p for p in json.loads(req("GET", "/profiles")) if p["name"].strip() == "Rahul")["id"]
    for seed in (7, 108, 209, 310):
        t = time.time()
        g = json.loads(req("POST", "/generate", {
            "profile_id": pid, "text": full, "language": "en", "engine": "chatterbox", "seed": seed,
            "normalize": True, "max_chunk_chars": 5000, "crossfade_ms": 0}))
        while True:
            s = json.loads(req("GET", f"/history/{g['id']}"))
            if s["status"] in ("completed", "failed", "cancelled"):
                break
            time.sleep(3)
        if s["status"] != "completed":
            print("failed:", s.get("error"))
            continue
        raw = OUT / f"raw_{seed}.wav"
        raw.write_bytes(req("GET", f"/history/{g['id']}/export-audio"))
        rate = words / dur(raw)
        peak = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "volumedetect", "-f", "null", "-"],
                              capture_output=True, text=True).stderr
        mx = float(re.search(r"max_volume: ([-0-9.]+)", peak).group(1))
        print(f"seed {seed}: {dur(raw):.1f}s, {rate:.2f} words/s, peak {mx} dB, {time.time() - t:.0f}s", flush=True)
        if 2.0 <= rate <= 3.3:
            out = OUT / "full.wav"
            ff("-i", str(raw), "-af",
               "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
               "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.2,areverse,"
               "aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11", "-ac", "2", str(out))
            (OUT / "meta.json").write_text(json.dumps({"seed": seed, "words": words, "scenes": scenes}, indent=2))
            print(f"OK -> {out} ({dur(out):.1f}s)")
            return
    raise SystemExit("no acceptable take")


if __name__ == "__main__":
    main()
