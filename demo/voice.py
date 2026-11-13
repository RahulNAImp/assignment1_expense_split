"""Generate narration audio per scene with the local Voicebox API (profile 'Rahul').

Usage: python voice.py [--script v2/script.md --out v2/build/audio] [scene ...]
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

API = "http://localhost:17493"
HERE = Path(__file__).parent
OUT = HERE / "build" / "audio"


def req(method: str, path: str, body: dict | None = None) -> bytes:
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=600) as resp:  # noqa: S310 - localhost only
        return resp.read()


SCRIPT = HERE / "narration.md"


def segments() -> dict[str, str]:
    text = SCRIPT.read_text()
    parts = re.split(r"^## (\w+)\s*$", text, flags=re.M)
    out = {}
    for i in range(1, len(parts), 2):
        body = parts[i + 1].split("\n# ")[0]
        spoken = [ln for ln in body.splitlines() if ln.strip() and not ln.startswith(">")]
        out[parts[i]] = " ".join(spoken).strip()
    return out


def main(names: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    profile = next(p for p in json.loads(req("GET", "/profiles")) if p["name"].strip() == "Rahul")
    segs = segments()
    for name in names or list(segs):
        t = time.time()
        gen = json.loads(req("POST", "/generate", {
            "profile_id": profile["id"], "text": segs[name], "language": "en",
            "engine": "chatterbox"}))
        gid = gen["id"]
        while True:
            st = json.loads(req("GET", f"/history/{gid}"))
            if st["status"] in ("completed", "failed", "cancelled"):
                break
            time.sleep(3)
        if st["status"] != "completed":
            sys.exit(f"{name}: generation {st['status']}: {st.get('error')}")
        (OUT / f"{name}.wav").write_bytes(req("GET", f"/history/{gid}/export-audio"))
        print(f"{name}: {st['duration']:.1f}s audio in {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--script"]:
        SCRIPT = HERE / args[1]
        OUT = HERE / args[3]
        args = args[4:]
    main(args)
