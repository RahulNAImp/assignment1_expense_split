"""One continuous Voicebox take per SCENE (chatterbox caps a take at ~40 s, so a whole-video take
truncates). No effects (they caused a metallic sound): only trim + loudness normalisation.

Slide steps inside a scene are timed by word position, snapped to the nearest natural pause in
the take. Output: build/audio/<scene>.wav and build/beats.json (format used by build_timeline).
"""

import json
import re
import subprocess
import sys
import time

from voice_beats import BUILD, OUT, dur, ff, req, take
from voice_single import script_text

RATE_OK = (2.0, 3.3)


def pauses(path) -> list[float]:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-40dB:d=0.12",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    s = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]
    e = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
    return [(a + b) / 2 for a, b in zip(s, e)]


def main(names: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _, scenes = script_text()
    pid = next(p for p in json.loads(req("GET", "/profiles")) if p["name"].strip() == "Rahul")["id"]
    meta_f = BUILD / "beats.json"
    meta = json.loads(meta_f.read_text()) if meta_f.exists() else {}
    for name, beats in scenes.items():
        if names and name not in names:
            continue
        t0 = time.time()
        text = " ".join(beats)
        words = len(text.split())
        best = None
        for seed in (7, 108, 209, 310):
            w = take(pid, text, seed)
            rate = words / dur(w)
            if RATE_OK[0] <= rate <= RATE_OK[1]:
                best = w
                break
            print(f"   retry {name}: {rate:.2f} words/s (seed {seed})", flush=True)
            best = best or w
        out = OUT / f"{name}.wav"
        ff("-i", str(best), "-af", "aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11", "-ac", "2", str(out))
        total = dur(out)
        # beat starts: word-proportional estimate snapped to the nearest pause (within 1.2 s)
        ps = pauses(out)
        starts, acc = [0.0], 0
        for b in beats[:-1]:
            acc += len(b.split())
            est = total * acc / words
            near = min(ps, key=lambda p: abs(p - est), default=est)
            starts.append(round(near if abs(near - est) <= 1.2 else est, 3))
        meta[name] = {"beats": starts, "audioSec": round(total, 3)}
        meta_f.write_text(json.dumps(meta, indent=2))
        print(f"{name}: {total:.1f}s, {words / total:.2f} w/s, beats {starts}, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
