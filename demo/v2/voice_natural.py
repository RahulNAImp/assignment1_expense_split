"""Natural-sounding narration from the local Voicebox API (profile 'Rahul', chatterbox).

Why per line: long-text generation is chunked by Voicebox and joined with a 50 ms crossfade,
which removes breathing room. Here every script line is synthesised separately (seed derived from
the line, so intonation varies naturally between sentences), trimmed, faded, and joined using the
speaker's OWN rhythm, measured from the Voicebox reference recording:
  line ends with ","  -> 0.18-0.28 s
  line ends with "."  -> 0.32-0.48 s (a real breath before ~35 % of new sentences)
  blank line          -> 0.55-0.75 s + one of the speaker's real breaths
Breaths are cut from the reference clip (build/breaths/). A faint room tone and a very short
early reflection make it sound mic-recorded rather than synthesised.

Usage: python demo/v2/voice_natural.py [scene ...]      (default: all scenes)
Output: demo/v2/build/audio/<scene>.wav ; per-line cache in demo/v2/build/lines/
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
SCRIPT = HERE / "script.md"
OUT = HERE / "build" / "audio"
LINES = HERE / "build" / "lines"
SEED = 7  # base; per-line seed = SEED + hash(line) % 1000
BREATHS = sorted((HERE / "build" / "breaths").glob("breath*.wav"))
SR = 48000


def req(method: str, path: str, body: dict | None = None) -> bytes:
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=900) as resp:  # noqa: S310 - localhost only
        return resp.read()


def scenes() -> dict[str, list[str | None]]:
    """Scene -> list of lines; None marks a blank line (beat)."""
    text = SCRIPT.read_text()
    parts = re.split(r"^## (\w+)\s*$", text, flags=re.M)
    out: dict[str, list[str | None]] = {}
    for i in range(1, len(parts), 2):
        items: list[str | None] = []
        for ln in parts[i + 1].strip().splitlines():
            if ln.startswith(">"):
                continue
            if not ln.strip():
                if items and items[-1] is not None:
                    items.append(None)
            else:
                items.append(ln.strip())
        while items and items[-1] is None:
            items.pop()
        out[parts[i]] = items
    return out


def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def synth(profile_id: str, line: str) -> Path:
    seed = SEED + int(hashlib.sha1(line.encode()).hexdigest(), 16) % 1000
    key = hashlib.sha1(f"{seed}|{line}".encode()).hexdigest()[:16]
    clean = LINES / f"{key}.wav"
    if clean.exists():
        return clean
    gen = json.loads(req("POST", "/generate", {
        "profile_id": profile_id, "text": line, "language": "en", "engine": "chatterbox",
        "seed": seed, "normalize": True}))
    gid = gen["id"]
    while True:
        st = json.loads(req("GET", f"/history/{gid}"))
        if st["status"] in ("completed", "failed", "cancelled"):
            break
        time.sleep(2)
    if st["status"] != "completed":
        raise RuntimeError(f"generation {st['status']} for {line!r}: {st.get('error')}")
    raw = LINES / f"{key}.raw.wav"
    raw.write_bytes(req("GET", f"/history/{gid}/export-audio"))
    # Trim leading/trailing silence, resample, 15 ms fades to avoid clicks.
    ff("-i", str(raw), "-af",
       "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,"
       "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse,"
       f"aresample={SR},afade=t=in:d=0.015,areverse,afade=t=in:d=0.03,areverse",
       "-ac", "1", str(clean))
    raw.unlink()
    return clean


def pause_after(line: str | None, rng: random.Random) -> tuple[float, bool]:
    """(silence seconds, insert a breath?)"""
    if line is None:
        return rng.uniform(0.55, 0.75), True
    if line.endswith(","):
        return rng.uniform(0.18, 0.28), False
    return rng.uniform(0.32, 0.48), rng.random() < 0.35


def build_scene(profile_id: str, name: str, items: list[str | None]) -> float:
    rng = random.Random(name)  # deterministic per scene
    parts: list[tuple[str, float, bool]] = []  # (file, gap seconds, breath?)
    for idx, item in enumerate(items):
        if item is None:
            continue
        t = time.time()
        wav = synth(profile_id, item)
        print(f"   {name} [{idx + 1}/{len(items)}] {time.time() - t:4.0f}s  {item[:60]}", flush=True)
        nxt = items[idx + 1] if idx + 1 < len(items) else "END"
        gap, breath = (0.0, False) if nxt == "END" else pause_after(None if nxt is None else item, rng)
        parts.append((str(wav), gap, breath))
    # Build concat list with generated silences.
    sil_dir = HERE / "build" / "silence"
    sil_dir.mkdir(parents=True, exist_ok=True)
    lst = HERE / "build" / f"{name}.concat.txt"
    lines = []
    def silence(sec: float) -> str:
        sil = sil_dir / f"{int(sec * 1000)}.wav"
        if not sil.exists():
            ff("-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", f"{sec:.3f}", str(sil))
        return f"file '{sil}'"

    for wav, gap, breath in parts:
        lines.append(f"file '{wav}'")
        if gap <= 0:
            continue
        if breath and BREATHS:
            # silence, then the speaker's inhale right before the next phrase
            lines.append(silence(max(0.12, gap - 0.3)))
            lines.append(f"file '{rng.choice(BREATHS)}'")
            lines.append(silence(0.06))
        else:
            lines.append(silence(gap))
    lst.write_text("\n".join(lines) + "\n")
    dry = HERE / "build" / f"{name}.dry.wav"
    ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "pcm_s16le", str(dry))
    out = OUT / f"{name}.wav"
    # Faint room tone under the voice, then loudness-normalise for video (-16 LUFS).
    ff("-i", str(dry), "-f", "lavfi", "-i", f"anoisesrc=color=pink:r={SR}:a=0.0008",
       "-filter_complex", "[0:a]aecho=0.85:0.4:14|23:0.10|0.06[v];"
       "[v][1:a]amix=inputs=2:duration=first:normalize=0,"
       "loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo",
       "-ar", str(SR), str(out))
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout)
    return dur


def main(names: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    LINES.mkdir(parents=True, exist_ok=True)
    profile = next(p for p in json.loads(req("GET", "/profiles")) if p["name"].strip() == "Rahul")
    all_scenes = scenes()
    for name in names or list(all_scenes):
        t = time.time()
        d = build_scene(profile["id"], name, all_scenes[name])
        print(f"{name}: {d:.1f}s audio in {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
