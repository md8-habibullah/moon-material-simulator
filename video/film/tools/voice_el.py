"""Narration with ElevenLabs: one take per scene, timed to the word.

Run from video/film (the key comes from .env, which git ignores; it is never printed):
    python3 tools/voice_el.py r1            # one scene
    python3 tools/voice_el.py all           # every scene in tools/vo.json
    python3 tools/voice_el.py all --missing # only scenes without a take yet

Writes assets/voice/<scene>.wav and assets/voice/<scene>.asr.json (word timings from ElevenLabs'
character alignment), which tools/build.py reads. Each request passes the neighbouring scenes' text,
so the delivery flows from one scene into the next. Every character spoken counts against the plan's
quota, so the script refuses to run past it.
"""
import base64
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VO = json.loads((ROOT / "tools" / "vo.json").read_text())
ORDER = list(VO)
OUT = ROOT / "assets" / "voice"
API = "https://api.elevenlabs.io/v1"
MODEL = "eleven_multilingual_v2"

GEORGE = "JBFqnCBsd6RMkjVDRZzb"   # warm British storyteller: the story and the demo
ALICE = "Xb7hH8MSUJpSbSDYk0k2"    # clear British educator: the product, the science, the team
CAST = {sid: ALICE if sid in {"s3", "s4", "s5", "team"} else GEORGE for sid in ORDER}
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.2, "use_speaker_boost": True, "speed": 1.0}
# Alice reads slower than George, and the film must stay under 240 s: ElevenLabs' own speed control keeps it natural.
SPEED = {"s3": 1.12, "s4": 1.12, "s5": 1.12, "team": 1.12, "r2": 1.05, "s2": 1.05, "s6a": 1.05}


def load_key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set (put it in video/film/.env)")
    return key


def call(key, path, body=None):
    req = urllib.request.Request(f"{API}{path}", data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def words_from_alignment(al):
    """Group the per-character alignment into whitespace-separated words."""
    words, cur = [], None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if cur:
                words.append(cur)
            cur = None
            continue
        if cur is None:
            cur = {"text": ch, "start": round(s, 3), "end": round(e, 3)}
        else:
            cur["text"] += ch
            cur["end"] = round(e, 3)
    if cur:
        words.append(cur)
    return words


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    key = load_key()
    scenes = ORDER if args[0] == "all" else [a for a in args if a in VO]
    if "--missing" in args:
        scenes = [s for s in scenes if not (OUT / f"{s}.wav").exists()]
    need = sum(len(VO[s]) for s in scenes)
    sub = call(key, "/user/subscription")
    left = sub["character_limit"] - sub["character_count"]
    print(f"{len(scenes)} scene(s), {need} characters; {left} left this month")
    if need > left:
        sys.exit("Not enough characters left; nothing was generated.")
    OUT.mkdir(parents=True, exist_ok=True)
    for sid in scenes:
        i = ORDER.index(sid)
        body = {"text": VO[sid], "model_id": MODEL, "voice_settings": dict(SETTINGS, speed=SPEED.get(sid, 1.0)),
                "previous_text": VO[ORDER[i - 1]] if i > 0 else None,
                "next_text": VO[ORDER[i + 1]] if i + 1 < len(ORDER) else None}
        d = call(key, f"/text-to-speech/{CAST[sid]}/with-timestamps?output_format=mp3_44100_128", body)
        mp3 = OUT / f"{sid}.mp3"
        mp3.write_bytes(base64.b64decode(d["audio_base64"]))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "1", str(OUT / f"{sid}.wav")], check=True)
        mp3.unlink()
        words = words_from_alignment(d["alignment"])
        (OUT / f"{sid}.asr.json").write_text(json.dumps(words, indent=0))
        dur = words[-1]["end"] if words else 0
        print(f"  {sid:5} {CAST[sid] == GEORGE and 'George' or 'Alice':6} {len(words):3} words  {dur:6.2f} s  {len(words) / max(dur, 0.1):.2f} w/s")


if __name__ == "__main__":
    main()
