"""Fit the ElevenLabs takes to the 240-second budget without spending more credits.

Run from video/film after tools/voice_el.py:
    python3 tools/fit_voice.py

voice_el.py writes assets/voice/<scene>.wav; the first run here moves those untouched takes to
assets/voice/raw/ and never changes them again, so this script can be re-run with other numbers.
For each scene it (1) shortens only pauses longer than CAP seconds, cutting from the middle of
the silence, then (2) changes the tempo with Rubber Band (pitch kept, formants preserved), and
rewrites the word timings in <scene>.asr.json to match.
"""
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICE = ROOT / "assets" / "voice"
RAW = VOICE / "raw"
ORDER = list(json.loads((ROOT / "tools" / "vo.json").read_text()))
CAP = 0.45                     # longest pause kept between two words, in seconds
TEMPO = {sid: 1.02 for sid in ORDER}
# The calmest takes (fewest words per second) get a little more, so the pace is even across the film.
TEMPO.update({"r1": 1.06, "s1": 1.06, "s4": 1.06, "s5": 1.06, "s6b": 1.06, "team": 1.06})
SR = 44100


def run(*cmd):
    subprocess.run(cmd, check=True)


def main():
    RAW.mkdir(exist_ok=True)
    total = 0.0
    for sid in ORDER:
        wav, asr = VOICE / f"{sid}.wav", VOICE / f"{sid}.asr.json"
        if not (RAW / f"{sid}.wav").exists():
            shutil.copy2(wav, RAW / f"{sid}.wav")
            shutil.copy2(asr, RAW / f"{sid}.asr.json")
        words = json.loads((RAW / f"{sid}.asr.json").read_text())
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                             "-of", "csv=p=0", str(RAW / f"{sid}.wav")]).decode())
        # Segments of the original to keep: everything except the middle of overlong pauses.
        keep, cursor = [], 0.0
        for a, b in zip(words, words[1:]):
            gap = b["start"] - a["end"]
            if gap > CAP:
                cut = gap - CAP
                mid = a["end"] + gap / 2
                keep.append((cursor, mid - cut / 2))
                cursor = mid + cut / 2
        keep.append((cursor, dur))
        # Map an original time to its time after the cuts.
        def squeeze(t):
            out = 0.0
            for s, e in keep:
                if t <= s:
                    break
                out += min(t, e) - s
            return out
        sel = "+".join(f"between(t,{s:.4f},{e:.4f})" for s, e in keep)
        k = TEMPO[sid]
        run("ffmpeg", "-loglevel", "error", "-y", "-i", str(RAW / f"{sid}.wav"),
            "-af", f"aselect='{sel}',asetpts=N/SR/TB,rubberband=tempo={k}:formant=preserved,aresample={SR}",
            "-ac", "1", str(wav))
        fitted = [dict(w, start=round(squeeze(w["start"]) / k, 3), end=round(squeeze(w["end"]) / k, 3)) for w in words]
        asr.write_text(json.dumps(fitted, indent=0))
        total += fitted[-1]["end"]
        print(f"  {sid:5} {words[-1]['end']:6.2f} s -> {fitted[-1]['end']:6.2f} s  (tempo {k})")
    print(f"speech total {total:.2f} s")


if __name__ == "__main__":
    main()
