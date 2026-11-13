"""Original ambient score for the film, synthesised from scratch (no samples, no licence questions).

Run from video/film after tools/build.py (it reads tools/timing.json for the section times):
    ../../backend/.venv/bin/python tools/music.py
Writes assets/audio/music.mp3, loudness-normalised to -14 LUFS (it plays at 0.14 under the voice).

100 BPM, A minor. Sections follow the story: open, curious pads and a soft pluck for the machines NASA left
behind, a tense drone for the broken wrench, the pads open when the
simulator appears, a driving pulse under the data and the science, the harmony tightens on the failing
wrench, lifts to C major when the optimizer's wrench holds, and resolves under the end card.
"""
import json
import subprocess
from pathlib import Path

import numpy as np
from scipy.signal import lfilter

ROOT = Path(__file__).resolve().parent.parent
T = json.loads((ROOT / "tools" / "timing.json").read_text())
SR = 44100
TOTAL = T["total"] + 0.5
N = int(TOTAL * SR)
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
st = T["starts"]
cue = T["cues"]
LIFT = st["s6b"] + cue["s6b"]["impact_held"]          # the wrench holds: the music turns major
SOLUTION = st["s3"]
PROBLEM = st["s1"]                                   # the story of the machines ends; the problem begins
DATA = st["s4"]
DEMO = st["s6a"]
CLOSE = st["s7"]
t = np.arange(N) / SR
rng = np.random.default_rng(2026)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], x)


def smooth_step(x, a, b):
    y = np.clip((x - a) / max(b - a, 1e-6), 0, 1)
    return y * y * (3 - 2 * y)


def saw(freq, phase=0.0):
    return 2 * ((t * freq + phase) % 1.0) - 1


# Chords per bar. Minor while there is a problem, major once it is solved.
MINOR = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 60], [55, 59, 62, 67]]   # Am7 Fmaj7 C G
TENSE = [[57, 60, 63, 67], [56, 60, 63, 68], [53, 57, 60, 63], [52, 56, 59, 64]]   # darker turn for the demo
MAJOR = [[48, 52, 55, 59], [53, 57, 60, 64], [55, 59, 62, 67], [57, 60, 64, 69]]   # Cmaj7 F G Am


def chord_at(time):
    bar = int(time // BAR)
    if time >= LIFT:
        return MAJOR[bar % 4]
    if DEMO <= time < LIFT:
        return TENSE[bar % 4]
    return MINOR[bar % 4]


# ---- pad: detuned saws per chord note, bar by bar, crossfaded and low-passed.
pad = np.zeros(N)
bars = int(TOTAL // BAR) + 1
fade = int(0.35 * SR)
for b in range(bars):
    s0, s1 = int(b * BAR * SR), min(N, int((b + 1) * BAR * SR) + fade)
    if s0 >= N:
        break
    seg_t = t[s0:s1]
    notes = chord_at(b * BAR + 0.01)
    seg = np.zeros(s1 - s0)
    for n in notes:
        f = midi(n)
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            seg += 2 * ((seg_t * ff + rng.random()) % 1.0) - 1
    env = np.ones(s1 - s0)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] *= np.linspace(1, 0, fade)
    pad[s0:s1] += seg * env / (len(notes) * 3)
# Filter opens with the story: closed at the start, open for the solution, brightest after the lift.
cut = 500 + 700 * (1 - smooth_step(t, PROBLEM - 1.5, PROBLEM + 0.5)) + 900 * smooth_step(t, SOLUTION - 2, SOLUTION + 2) + 700 * smooth_step(t, LIFT - 1, LIFT + 1) \
      - 500 * smooth_step(t, DEMO - 1, DEMO + 1) * (1 - smooth_step(t, LIFT - 1, LIFT + 1))
pad_lo = lowpass(pad, 400)
pad_hi = lowpass(pad, 1800)
mix = np.clip((cut - 400) / 1400, 0, 1)
pad = pad_lo * (1 - mix) + pad_hi * mix

# ---- sub bass: chord root, a soft swell on each beat (sidechain feel).
bass = np.zeros(N)
beat_phase = (t % BEAT) / BEAT
duck = 0.55 + 0.45 * np.minimum(1, beat_phase * 4)
roots = np.array([midi(chord_at(x)[0] - 12) for x in np.arange(0, TOTAL + BAR, BAR)])
root_f = roots[(t // BAR).astype(int)]
phase = np.cumsum(root_f) / SR
bass = np.sin(2 * np.pi * phase) * duck

# ---- arpeggio: plucked 8th notes from the solution onward, with a dotted-8th echo.
arp = np.zeros(N)
eighth = BEAT / 2
k = 0
time = 0.0
while time < TOTAL - 1:
    story = time < PROBLEM - 0.5
    if (story and k % 2 == 0) or (time >= SOLUTION and not (CLOSE + 8 < time)):
        notes = chord_at(time)
        n = notes[[0, 2, 1, 3, 2, 1, 3, 2][k % 8]] + 12
        s0 = int(time * SR)
        L = int(0.5 * SR)
        s1 = min(N, s0 + L)
        tt = np.arange(s1 - s0) / SR
        f = midi(n)
        tone = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 7.5)
        arp[s0:s1] += tone * (0.55 + 0.45 * ((k % 4) == 0))
    time += eighth
    k += 1
delay = int(BEAT * 0.75 * SR)
echo = np.zeros(N)
echo[delay:] = arp[:-delay] * 0.38
echo2 = np.zeros(N)
echo2[2 * delay:] = arp[:-2 * delay] * 0.15
arp = lowpass(arp + echo + echo2, 3500)
arp_gain = 0.2 + 0.8 * smooth_step(t, DATA - 1, DATA + 1) + 0.25 * (1 - smooth_step(t, PROBLEM - 1, PROBLEM))
arp_gain *= 1 - 0.5 * smooth_step(t, DEMO - 1, DEMO + 1) * (1 - smooth_step(t, LIFT - 0.5, LIFT + 0.5))

# ---- hats: soft filtered-noise ticks on 16ths through the data, science and demo.
hats = np.zeros(N)
sixteenth = BEAT / 4
time, k = DATA, 0
while time < CLOSE:
    s0 = int(time * SR)
    L = int(0.05 * SR)
    burst = rng.standard_normal(min(L, N - s0)) * np.exp(-np.arange(min(L, N - s0)) / SR * 90)
    hats[s0:s0 + len(burst)] += burst * (1.0 if k % 4 == 2 else 0.45)
    time += sixteenth
    k += 1
hats = hats - lowpass(hats, 6000)

# ---- intro drone: low fifth that holds the tension of the broken wrench.
drone = (np.sin(2 * np.pi * midi(33) * t) + 0.5 * np.sin(2 * np.pi * midi(40) * t)) * smooth_step(t, PROBLEM - 1, PROBLEM + 1) * (1 - smooth_step(t, SOLUTION, SOLUTION + 4))

# ---- master
out = (0.55 * pad + 0.42 * bass + 0.30 * arp * arp_gain + 0.06 * hats + 0.35 * drone)
level = 0.75 + 0.25 * smooth_step(t, SOLUTION - 1, SOLUTION + 1) + 0.3 * smooth_step(t, LIFT - 0.2, LIFT + 0.4)
level *= 1 + 0.6 * smooth_step(t, T["total"] - 6, T["total"] - 4.5)        # swells under the end card
level *= np.minimum(1, t / 2.0) * (1 - smooth_step(t, TOTAL - 3.2, TOTAL - 0.2))
out *= level
out /= np.max(np.abs(out)) + 1e-9
stereo = np.stack([out, np.roll(out, int(0.012 * SR))], axis=1) * 0.9

wav = ROOT / "assets" / "audio" / "music.wav"
wav.parent.mkdir(parents=True, exist_ok=True)
pcm = (stereo * 32767).astype("<i2").tobytes()
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-b:a", "192k", str(wav.with_suffix(".mp3"))],
               input=pcm, check=True)
print("music", round(TOTAL, 1), "s → assets/audio/music.mp3")
