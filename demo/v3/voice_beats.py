"""Voice for demo v3: one continuous Voicebox take per BEAT (paragraph), joined per scene.

Beats = paragraphs separated by blank lines in script.md. Each beat is a single uninterrupted
take (natural flow), and beats are joined with ~0.5 s pauses. Beat start times are written to
build/beats.json so Remotion can reveal each slide step exactly when its sentence starts.

Usage: python demo/v3/voice_beats.py [scene ...]
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

API = "http://localhost:17493"
HERE = Path(__file__).parent
BUILD = HERE / "build"
TAKES = BUILD / "takes"
OUT = BUILD / "audio"
SR = 48000
SEED = 7


def req(method: str, path: str, body: dict | None = None) -> bytes:
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=900) as resp:  # noqa: S310 - localhost only
        return resp.read()


def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def dur(p: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)


def scenes() -> dict[str, list[str]]:
    text = (HERE / "script.md").read_text()
    parts = re.split(r"^## (\w+)\s*$", text, flags=re.M)
    out = {}
    for i in range(1, len(parts), 2):
        body = "\n".join(ln for ln in parts[i + 1].splitlines() if not ln.startswith(">"))
        beats = [" ".join(b.split()) for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]
        out[parts[i]] = beats
    return out


def take(profile_id: str, text: str, seed: int = SEED) -> Path:
    key = hashlib.sha1(f"{seed}|{text}".encode()).hexdigest()[:16]
    clean = TAKES / f"{key}.wav"
    if clean.exists():
        return clean
    gen = json.loads(req("POST", "/generate", {
        "profile_id": profile_id, "text": text, "language": "en", "engine": "chatterbox",
        "seed": seed, "normalize": True, "max_chunk_chars": 5000, "crossfade_ms": 0}))
    while True:
        st = json.loads(req("GET", f"/history/{gen['id']}"))
        if st["status"] in ("completed", "failed", "cancelled"):
            break
        time.sleep(3)
    if st["status"] != "completed":
        raise RuntimeError(f"{st['status']}: {st.get('error')} for {text[:60]!r}")
    raw = TAKES / f"{key}.raw.wav"
    raw.write_bytes(req("GET", f"/history/{gen['id']}/export-audio"))
    ff("-i", str(raw), "-af",
       "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
       "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.12,areverse,"
       f"aresample={SR},afade=t=in:d=0.02", "-ac", "1", str(clean))
    raw.unlink()
    return clean


RATE_OK = (2.0, 3.45)  # words/second; outside this the take is likely truncated or stretched


def good_take(profile_id: str, text: str) -> Path:
    """Regenerate with other seeds when the speaking rate shows dropped/stretched words."""
    words = len(text.split())
    best, best_err = None, 1e9
    for seed in (SEED, SEED + 101, SEED + 202, SEED + 303):
        w = take(profile_id, text, seed)
        rate = words / dur(w)
        if RATE_OK[0] <= rate <= RATE_OK[1]:
            return w
        err = abs(rate - 2.8)
        if err < best_err:
            best, best_err = w, err
        print(f"   retry: {rate:.2f} w/s for {text[:50]!r} (seed {seed})", flush=True)
    return best


def main(names: list[str]) -> None:
    for d in (TAKES, OUT):
        d.mkdir(parents=True, exist_ok=True)
    profile = next(p for p in json.loads(req("GET", "/profiles")) if p["name"].strip() == "Rahul")
    beats_file = BUILD / "beats.json"
    meta = json.loads(beats_file.read_text()) if beats_file.exists() else {}
    for name, beats in scenes().items():
        if names and name not in names:
            continue
        t0 = time.time()
        rng = random.Random(name)
        files, starts, t = [], [], 0.0
        sil_dir = BUILD / "silence"
        sil_dir.mkdir(exist_ok=True)
        for i, b in enumerate(beats):
            w = good_take(profile["id"], b)
            starts.append(round(t, 3))
            files.append(w)
            t += dur(w)
            if i < len(beats) - 1:
                gap = round(rng.uniform(0.45, 0.6), 2)
                sil = sil_dir / f"{int(gap * 100)}.wav"
                if not sil.exists():
                    ff("-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", str(gap), str(sil))
                files.append(sil)
                t += gap
        lst = BUILD / f"{name}.txt"
        lst.write_text("".join(f"file '{f}'\n" for f in files))
        dry = BUILD / f"{name}.dry.wav"
        ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "pcm_s16le", str(dry))
        out = OUT / f"{name}.wav"
        ff("-i", str(dry), "-f", "lavfi", "-i", f"anoisesrc=color=pink:r={SR}:a=0.0008",
           "-filter_complex", "[0:a]aecho=0.85:0.4:14|23:0.10|0.06[v];"
           "[v][1:a]amix=inputs=2:duration=first:normalize=0,"
           "loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo", "-ar", str(SR), str(out))
        meta[name] = {"beats": starts, "audioSec": round(dur(out), 3)}
        beats_file.write_text(json.dumps(meta, indent=2))
        print(f"{name}: {len(beats)} beats, {dur(out):.1f}s, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
