"""Narration for the 30-second Project Demo (Space Apps rule: a demo video is 30 s or less).

Run from video/film:  python3 tools/voice_demo30.py
Same voice and settings as the film (tools/voice_el.py). Writes the untouched take to
assets/voice/raw/d30.* and a copy to assets/voice/d30.wav + d30.asr.json for demo30.html.
"""
import base64, json, shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_el as v

ROOT = v.ROOT
TEXT = json.loads((ROOT / "tools" / "vo_demo30.json").read_text())["d30"]
SPEED = 1.08

key = v.load_key()
sub = v.call(key, "/user/subscription")
left = sub["character_limit"] - sub["character_count"]
print(f"{len(TEXT)} characters; {left} left this month")
if len(TEXT) > left:
    sys.exit("Not enough characters left; nothing was generated.")
d = v.call(key, f"/text-to-speech/{v.WILL}/with-timestamps?output_format=mp3_44100_128",
           {"text": TEXT, "model_id": v.MODEL, "voice_settings": dict(v.SETTINGS, speed=SPEED)})
raw = ROOT / "assets" / "voice" / "raw"
raw.mkdir(parents=True, exist_ok=True)
mp3 = raw / "d30.mp3"
mp3.write_bytes(base64.b64decode(d["audio_base64"]))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "1", str(raw / "d30.wav")], check=True)
words = v.words_from_alignment(d["alignment"])
(raw / "d30.asr.json").write_text(json.dumps(words, indent=0))
shutil.copy2(raw / "d30.wav", ROOT / "assets" / "voice" / "d30.wav")
shutil.copy2(raw / "d30.asr.json", ROOT / "assets" / "voice" / "d30.asr.json")
print(f"{len(words)} words, {words[-1]['end']:.2f} s")
