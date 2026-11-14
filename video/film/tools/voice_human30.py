"""Use a team member's own recorded voice for the 30-second demo (instead of the AI voice).

Run from video/film:
    python3 tools/voice_human30.py <recording> [--cut A-B ...] [--cap 0.30] [--budget 26.6]

1. Decodes the recording (any format ffmpeg reads, e.g. a WhatsApp .ogg voice note) to 48 kHz mono.
2. Removes the --cut ranges (seconds in the original: a restart, a cough), trims the silence before and after.
3. Shortens every pause longer than --cap seconds, cutting from the middle of the silence.
4. Cleans the sound: high-pass at 80 Hz, gentle noise reduction, light compression, loudness to -16 LUFS.
5. If the speech is still longer than --budget seconds, raises the tempo with Rubber Band (pitch and
   formants kept) just enough to fit.
6. Transcribes the result locally (HyperFrames' Whisper, medium.en model; nothing leaves the machine), aligns it to the script
   in tools/vo_demo30.json, and snaps word boundaries to the measured pauses, so the scene cuts and the
   captions land on the spoken words.

Writes assets/voice/d30_human.wav and assets/voice/d30_human.asr.json (the script's words with times), which
tools/build_demo30.py uses when D30_VOICE=human (the default once the file exists).
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
# What the speaker says (clean verbatim): the demo script as read aloud.
NAME = "d30_human"     # --name d30_clone for the cloned voice (tools/clone_voice30.py)


def set_name(name):
    """Point the script text and the output files at one voice: d30_human or d30_clone."""
    global NAME, SCRIPT, OUT_WAV, OUT_ASR, ASR_CACHE
    NAME = name
    SCRIPT = json.loads((ROOT / "tools" / "vo_demo30.json").read_text())["d30_human"].split()
    OUT_WAV = ROOT / "assets" / "voice" / f"{name}.wav"
    OUT_ASR = ROOT / "assets" / "voice" / f"{name}.asr.json"
    ASR_CACHE = ROOT / "assets" / "voice" / "raw" / f"{name}.whisper.json"   # git-ignored


set_name(NAME)
SR = 48000
SIL_DB = -38.0


def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def read_f32(path):
    raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                                   "-f", "f32le", "-"])
    return np.frombuffer(raw, dtype=np.float32).copy()


def write_wav(x, path):
    run("ffmpeg", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
        "-c:a", "pcm_s16le", str(path), input=x.astype(np.float32).tobytes())


def envelope(x, win=0.02):
    n = int(SR * win)
    return np.convolve(np.abs(x), np.ones(n) / n, "same")


def silences(x, min_len=0.12):
    """[(start, end)] of runs below SIL_DB longer than min_len seconds (inside the speech)."""
    quiet = envelope(x) < 10 ** (SIL_DB / 20)
    out, i, n = [], 0, len(x)
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) / SR >= min_len:
                out.append((i / SR, j / SR))
            i = j
        else:
            i += 1
    return out


def speech_span(x):
    idx = np.where(envelope(x) > 10 ** (SIL_DB / 20))[0]
    return idx[0] / SR, idx[-1] / SR


def cut(x, ranges):
    keep = np.ones(len(x), bool)
    for a, b in ranges:
        keep[int(a * SR):int(b * SR)] = False
    return x[keep]


def squeeze_pauses(x, cap):
    parts, cursor = [], 0
    for a, b in silences(x):
        if b - a > cap:
            mid, half = (a + b) / 2, cap / 2
            parts.append(x[cursor:int((mid - half) * SR)])
            cursor = int((mid + half) * SR)
    parts.append(x[cursor:])
    return np.concatenate(parts)


def transcribe(wav, model="medium.en"):
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ, DO_NOT_TRACK="1", HYPERFRAMES_NO_TELEMETRY="1")
        p = subprocess.run(["npx", "--yes", "hyperframes@0.9.39", "transcribe", str(wav), "--engine", "whisper",
                            "--model", model, "--json", "-d", d], capture_output=True, text=True, env=env, cwd=ROOT)
        words = []
        for line in (p.stdout + "\n" + p.stderr).splitlines():
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get("type") == "words":
                words += msg["words"]
        if not words:
            sys.exit("Transcription returned no words:\n" + p.stderr[-2000:])
        return words


def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def _fill(times):
    """Give unmatched words times between their neighbours, in proportion to their length."""
    i = 0
    while i < len(times):
        if times[i] is None:
            j = i
            while times[j] is None:
                j += 1
            a, b = times[i - 1][1], times[j][0]
            lens = [len(SCRIPT[m]) + 2 for m in range(i, j)]
            t = a
            for m, ln in zip(range(i, j), lens):
                d = (b - a) * ln / sum(lens)
                times[m] = [t + 0.02, t + d]
                t += d
            i = j
        i += 1
    return times


def align(asr, speech_end, pauses):
    """Give each script word a start/end time from the ASR words, corrected with the measured pauses."""
    a_tok, s_tok = [norm(w["text"]) for w in asr], [norm(w) for w in SCRIPT]
    # Whisper's clock drifts on long files: rescale it so its last word ends where the speech ends.
    k = speech_end / max(asr[-1]["end"], 0.1)
    times = [None] * len(SCRIPT)
    widx = {}                                   # script word -> index of the ASR word it matched
    matched = 0
    for blk in difflib.SequenceMatcher(None, s_tok, a_tok, autojunk=False).get_matching_blocks():
        for i in range(blk.size):
            w = asr[blk.b + i]
            times[blk.a + i] = [w["start"] * k, w["end"] * k]
            widx[blk.a + i] = blk.b + i
            matched += 1
    times[0] = times[0] or [0.0, 0.3]
    times[-1] = times[-1] or [speech_end - 0.4, speech_end]
    times = _fill(times)
    # Snap: each measured pause sits at a word boundary. A pause of 0.25 s or more goes to the nearest comma or
    # full stop within 1.6 s (else a boundary Whisper heard, else the nearest within 0.9 s); a shorter gap only
    # to a boundary Whisper heard within 0.3 s, otherwise it is left alone. Snapped boundaries become fixed anchors.
    fixed = {}
    punct = lambda m: SCRIPT[m].endswith((".", ",", ":"))
    for a, b in sorted(pauses, key=lambda p: p[0] - p[1]):          # longest pauses first
        mid = (a + b) / 2
        gap = lambda m: abs((times[m][1] + times[m + 1][0]) / 2 - mid)
        free = [m for m in range(len(SCRIPT) - 1) if m not in fixed]
        heard = lambda m: m in widx and m + 1 in widx and widx[m + 1] == widx[m] + 1
        by_ear = [m for m in free if gap(m) < 0.3 and heard(m)]        # Whisper heard both words, back to back
        if b - a >= 0.25:       # a real pause: almost always a comma or full stop
            near = [m for m in free if gap(m) < 1.6 and punct(m)] or by_ear or [m for m in free if gap(m) < 0.9]
        else:                   # a short gap: only where Whisper clearly puts a word boundary
            near = by_ear
        if not near:
            continue
        m = min(near, key=gap)
        fixed[m] = (a, b)
    # Rebuild: keep matched words that agree with the anchors, then refill everything else.
    out = [None] * len(SCRIPT)
    for m, (a, b) in fixed.items():
        out[m] = [None, a]
        out[m + 1] = [b, None]
    for m, t in enumerate(times):
        if out[m] is None:
            continue
        if out[m][0] is None:
            out[m][0] = min(t[0], out[m][1] - 0.08)
        if out[m][1] is None:
            out[m][1] = max(t[1], out[m][0] + 0.08)
    anchors = sorted(fixed)
    for m, t in enumerate(times):
        if out[m] is not None:
            continue
        # A matched word keeps its time only if it falls between the surrounding anchors.
        lo = max([fixed[x][1] for x in anchors if x < m] or [0.0])
        hi = min([fixed[x][0] for x in anchors if x >= m] or [speech_end])
        if lo <= t[0] < t[1] <= hi + 0.05 and norm(SCRIPT[m]) in a_tok:
            out[m] = list(t)
    out[0] = out[0] or [0.0, 0.3]
    out[-1] = out[-1] or [speech_end - 0.4, speech_end]
    out = _fill(out)
    for m in range(1, len(out)):
        out[m][0] = max(out[m][0], out[m - 1][1])
        out[m][1] = max(out[m][1], out[m][0] + 0.05)
    return [{"text": w, "start": round(t[0], 3), "end": round(t[1], 3)} for w, t in zip(SCRIPT, out)], matched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recording")
    ap.add_argument("--cut", action="append", default=[], help="A-B seconds in the original to remove")
    ap.add_argument("--cap", type=float, default=0.30, help="longest pause kept, seconds")
    ap.add_argument("--budget", type=float, default=26.6, help="longest speech allowed, seconds")
    ap.add_argument("--realign", action="store_true", help="only redo the alignment from the cached transcript")
    ap.add_argument("--name", default="d30_human", help="output name: d30_human (recording) or d30_clone (cloned voice)")
    args = ap.parse_args()
    set_name(args.name)
    if args.realign:
        y = read_f32(OUT_WAV)
        asr = json.loads(ASR_CACHE.read_text())
        words, matched = align(asr, speech_span(y)[1], silences(y))
        OUT_ASR.write_text(json.dumps(words, indent=0))
        print(f"realigned: {matched}/{len(SCRIPT)} script words matched")
        return

    x = read_f32(args.recording)
    x = cut(x, [tuple(map(float, c.split("-"))) for c in args.cut])
    s0, s1 = speech_span(x)
    x = x[max(int((s0 - 0.04) * SR), 0):int((s1 + 0.12) * SR)]
    x = squeeze_pauses(x, args.cap)
    length = len(x) / SR
    tempo = max(1.0, length / args.budget)
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / "in.wav", Path(d) / "out.wav"
        write_wav(x, src)
        chain = ("highpass=f=80,afftdn=nr=10:nf=-50,"
                 "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,"
                 + (f"rubberband=tempo={tempo:.4f}:formant=preserved:pitchq=quality," if tempo > 1.0005 else "")
                 + f"loudnorm=I=-16:TP=-1.5:LRA=9,aresample={SR}")
        run("ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-af", chain, "-ac", "1", str(dst))
        y = read_f32(dst)
    # loudnorm can leave a little padding; trim again so the first word starts at ~0.
    s0, s1 = speech_span(y)
    y = y[max(int((s0 - 0.03) * SR), 0):int((s1 + 0.10) * SR)]
    OUT_WAV.parent.mkdir(parents=True, exist_ok=True)
    write_wav(y, OUT_WAV)
    dur = len(y) / SR
    asr = transcribe(OUT_WAV)
    ASR_CACHE.parent.mkdir(parents=True, exist_ok=True)
    ASR_CACHE.write_text(json.dumps(asr))
    words, matched = align(asr, speech_span(y)[1], silences(y))
    OUT_ASR.write_text(json.dumps(words, indent=0))
    print(f"recording -> {dur:.2f} s (pauses capped at {args.cap} s, tempo {tempo:.3f}x)")
    print(f"whisper heard: {' '.join(w['text'] for w in asr)}")
    print(f"script words matched to speech: {matched}/{len(SCRIPT)}")
    print(f"wrote {OUT_WAV.relative_to(ROOT)} and {OUT_ASR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
