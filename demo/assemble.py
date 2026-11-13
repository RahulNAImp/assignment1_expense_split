"""Assemble the demo video: each terminal segment + its narration, then concatenate (ffmpeg)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).parent / "build"
SEGMENTS = ["intro", "1a", "1b", "outro"]
OUT = BUILD / "AI-SDLC-Assignment1-Demo-2026NS93095.mp4"


def dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(out.strip())


def build_segment(name: str) -> Path:
    video, audio = BUILD / f"{name}.mp4", BUILD / "audio" / f"{name}.wav"
    v, a = dur(video), dur(audio)
    target = max(v, a + 1.5)
    stretch = min(target / v, 1.5) if target > v else 1.0  # slow typing slightly to match voice
    freeze = max(0.0, target - v * stretch)
    vf = (f"setpts={stretch:.4f}*PTS,tpad=stop_mode=clone:stop_duration={freeze:.2f},"
          "scale=1600:900,fps=30,format=yuv420p")
    af = f"adelay=600|600,apad,atrim=0:{target:.2f}"
    seg = BUILD / f"seg_{name}.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(audio),
         "-filter_complex", f"[0:v]{vf}[v];[1:a]aformat=sample_rates=48000:channel_layouts=stereo,{af}[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{target:.2f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
         str(seg)],
        check=True,
    )
    print(f"{name}: video {v:.1f}s x{stretch:.2f} + freeze {freeze:.1f}s, voice {a:.1f}s -> {target:.1f}s")
    return seg


def main() -> None:
    names = sys.argv[1:] or SEGMENTS
    segs = [build_segment(n) for n in names]
    lst = BUILD / "concat.txt"
    lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", "-movflags", "+faststart", str(OUT)], check=True)
    print(f"-> {OUT} ({dur(OUT):.1f}s)")


if __name__ == "__main__":
    main()
