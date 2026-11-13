"""One continuous take per scene from the local Voicebox API (profile 'Rahul', chatterbox).

Each scene's script is sent as ONE request with chunking disabled (max_chunk_chars=5000), so the
model keeps natural intonation and flow across sentences, with no stitched lines. Afterwards:
  * the speaker's own breaths (cut from the Voicebox reference clip, build/breaths/) are MIXED
    softly into the take's natural pauses (no audio is cut or shifted),
  * a faint room tone + very short early reflection are added (mic-recorded feel),
  * loudness is normalised to -16 LUFS for video.

Usage: python demo/v2/voice_take.py [scene ...]     (default: all scenes)
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from voice_natural import SCRIPT, req, scenes  # same script + API helper

HERE = Path(__file__).parent
OUT = HERE / "build" / "audio"
RAW = HERE / "build" / "takes"
BREATHS = sorted((HERE / "build" / "breaths").glob("breath*.wav"))
SEED = 7
SR = 48000


def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def scene_text(items: list[str | None]) -> str:
    # Lines join into flowing prose; a blank line (new idea) becomes a paragraph break.
    paras, cur = [], []
    for it in items:
        if it is None:
            paras.append(" ".join(cur))
            cur = []
        else:
            cur.append(it)
    paras.append(" ".join(cur))
    return "\n\n".join(p for p in paras if p)


def pauses(path: Path) -> list[tuple[float, float]]:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af",
                          "silencedetect=noise=-38dB:d=0.32", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    s = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]
    e = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
    return list(zip(s, e))


def take(profile_id: str, name: str, text: str) -> float:
    gen = json.loads(req("POST", "/generate", {
        "profile_id": profile_id, "text": text, "language": "en", "engine": "chatterbox",
        "seed": SEED, "normalize": True, "max_chunk_chars": 5000, "crossfade_ms": 0}))
    while True:
        st = json.loads(req("GET", f"/history/{gen['id']}"))
        if st["status"] in ("completed", "failed", "cancelled"):
            break
        time.sleep(3)
    if st["status"] != "completed":
        raise RuntimeError(f"{name}: {st['status']} {st.get('error')}")
    raw = RAW / f"{name}.wav"
    raw.write_bytes(req("GET", f"/history/{gen['id']}/export-audio"))
    # Trim leading/trailing silence only.
    clean = RAW / f"{name}.clean.wav"
    ff("-i", str(raw), "-af",
       "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
       "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse,"
       f"aresample={SR}", "-ac", "1", str(clean))

    # Breaths: mixed into natural pauses >= 0.32 s, ending just before speech resumes.
    rng = random.Random(name)
    inputs, mixes, labels = ["-i", str(clean)], [], ""
    for k, (a, b) in enumerate(pauses(clean)):
        short = (b - a) < 0.45
        if not BREATHS or (short and rng.random() > 0.4):
            continue
        br = rng.choice(BREATHS)
        start = max(a + 0.05, b - 0.42)
        inputs += ["-i", str(br)]
        idx = len(inputs) // 2 - 1
        mixes.append(f"[{idx}:a]volume=0.9,adelay={int(start * 1000)}:all=1[b{k}]")
        labels += f"[b{k}]"
    voice = RAW / f"{name}.breath.wav"
    if mixes:
        graph = ";".join(mixes) + f";[0:a]{labels}amix=inputs={len(mixes) + 1}:duration=first:normalize=0"
        ff(*inputs, "-filter_complex", graph, str(voice))
    else:
        voice = clean

    out = OUT / f"{name}.wav"
    ff("-i", str(voice), "-f", "lavfi", "-i", f"anoisesrc=color=pink:r={SR}:a=0.0008",
       "-filter_complex", "[0:a]aecho=0.85:0.4:14|23:0.10|0.06[v];"
       "[v][1:a]amix=inputs=2:duration=first:normalize=0,"
       "loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo", "-ar", str(SR), str(out))
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout)


def main(names: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    profile = next(p for p in json.loads(req("GET", "/profiles")) if p["name"].strip() == "Rahul")
    all_scenes = scenes()
    for name in names or list(all_scenes):
        t = time.time()
        d = take(profile["id"], name, scene_text(all_scenes[name]))
        print(f"{name}: {d:.1f}s one take, {time.time() - t:.0f}s to generate", flush=True)


if __name__ == "__main__":
    _ = SCRIPT
    main(sys.argv[1:])
