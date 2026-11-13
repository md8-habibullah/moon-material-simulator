"""Build the 240 Seconds of Glory film: writes index.html and compositions/*.html.

Run from video/film:  python3 tools/build.py

The voice-over is the clock. With HeyGen word timings in assets/voice/<scene>.words.json (and the audio
in assets/voice/<scene>.wav) every cue lands on its word; without them, cues are estimated from the
word count so the film can be previewed before the voice exists. Re-run after changing the voice.
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VO = json.loads((ROOT / "tools" / "vo.json").read_text())
ORDER = ["r1", "r2", "s1", "s2", "s3", "s4", "s5", "s6a", "s6b", "s6c", "team", "s7"]
LEAD = 0.30          # seconds of picture before the first word of a scene
TAIL = {"s7": 4.2}   # end card holds after the last word
DEFAULT_TAIL = 0.35
EST_WPS = 2.35       # estimated words per second when no voice exists yet
FPS = 30

CHAPTERS = [("r1", "01", "Left behind"), ("s1", "02", "The problem"), ("s3", "03", "The solution"), ("s4", "04", "NASA data"),
            ("s5", "05", "The science"), ("s6a", "06", "Live demo"), ("team", "07", "The team"), ("s7", "08", "Impact")]


# ---------------------------------------------------------------- timing -------------------------

def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower().replace("’", "'"))


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    return float(out.stdout.strip())


def load_asr(path):
    d = json.loads(path.read_text())
    words = d if isinstance(d, list) else d.get("words", [])
    return [w for w in words if norm(w.get("text", ""))]


def align(script, asr):
    """Script words with times from the speech recogniser. Matching words copy its times; where the
    wording differs ("384,000" vs "three hundred and eighty-four thousand"), the span's time is shared
    out by word length. Captions therefore show the script, timed to the real voice."""
    import difflib
    toks = script.split()
    a = [norm(t) for t in toks]
    b = [norm(w["text"]) for w in asr]
    out = [None] * len(toks)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                w = asr[j1 + k]
                out[i1 + k] = {"text": toks[i1 + k], "start": w["start"], "end": w["end"]}
        elif i2 > i1:
            if j2 > j1:
                t0, t1 = asr[j1]["start"], asr[j2 - 1]["end"]
            else:  # words the recogniser missed: squeeze them between their neighbours
                t0 = asr[j1 - 1]["end"] if j1 > 0 else 0.0
                t1 = asr[j1]["start"] if j1 < len(asr) else t0 + 0.3 * (i2 - i1)
                t1 = max(t1, t0 + 0.12 * (i2 - i1))
            lens = [max(len(a[k]), 1) for k in range(i1, i2)]
            tot, acc = sum(lens), t0
            for k, L in zip(range(i1, i2), lens):
                d = (t1 - t0) * L / tot
                out[k] = {"text": toks[k], "start": round(acc, 3), "end": round(acc + d, 3)}
                acc += d
    return out


class Voice:
    def __init__(self, sid):
        self.sid = sid
        self.text = VO[sid]
        wav = ROOT / "assets" / "voice" / f"{sid}.wav"
        asr = ROOT / "assets" / "voice" / f"{sid}.asr.json"
        self.real = wav.exists()
        if self.real and asr.exists():
            self.duration = probe_duration(wav)
            self.words = align(self.text, load_asr(asr))
        else:
            toks = self.text.split()
            self.duration = len(toks) / EST_WPS
            step = self.duration / len(toks)
            self.words = [{"text": t, "start": i * step, "end": (i + 1) * step} for i, t in enumerate(toks)]
        self.speech_end = self.words[-1]["end"] if self.words else self.duration
        self.scene = LEAD + max(self.duration, self.speech_end) + TAIL.get(sid, DEFAULT_TAIL)

    def at(self, phrase, offset=0.0):
        """Scene time of the first word of `phrase` (matched on normalised words)."""
        target = [norm(t) for t in phrase.split() if norm(t)]
        seq = [norm(w["text"]) for w in self.words]
        for i in range(len(seq)):
            if seq[i:i + len(target)] == target:
                return round(LEAD + self.words[i]["start"] + offset, 3)
        # Numbers may come back spelled differently: fall back to a looser match on the first token.
        for i, s in enumerate(seq):
            if target and target[0] in s:
                return round(LEAD + self.words[i]["start"] + offset, 3)
        raise KeyError(f"{self.sid}: cue '{phrase}' not found")


VOICES = {sid: Voice(sid) for sid in ORDER}
STARTS, t = {}, 0.0
for sid in ORDER:
    STARTS[sid] = round(t, 3)
    t += VOICES[sid].scene
TOTAL = round(t, 3)


# ---------------------------------------------------------------- shared ----------------------------

FONT = """
@font-face { font-family: 'Space Grotesk'; src: url('assets/fonts/SpaceGrotesk-latin.woff2') format('woff2');
  font-weight: 300 700; font-display: block; }
"""

BASE_CSS = FONT + """
#root { position: absolute; inset: 0; overflow: hidden; background: #02040a; color: #e7edf7;
  font-family: 'Space Grotesk', 'Inter', 'JetBrains Mono', sans-serif; }
.grp { position: absolute; inset: 0; }
.abs { position: absolute; }
.bg { position: absolute; left: -120px; top: -60px; width: 2160px; height: 1215px; object-fit: cover; }
.kick { font-family: 'JetBrains Mono', monospace; font-size: 28px; letter-spacing: .16em; text-transform: uppercase;
  color: #7fe3ff; }
.h0 { font-size: 150px; font-weight: 700; letter-spacing: -.03em; line-height: .95; }
.h1 { font-size: 96px; font-weight: 700; letter-spacing: -.02em; line-height: 1.02; }
.h2 { font-size: 64px; font-weight: 700; letter-spacing: -.015em; line-height: 1.05; }
.h3 { font-size: 44px; font-weight: 600; line-height: 1.15; }
.body { font-size: 34px; font-weight: 500; color: #c9d6ea; line-height: 1.3; }
.src { font-family: 'JetBrains Mono', monospace; font-size: 28px; color: #8f9cb2; letter-spacing: .04em; }
.mono { font-family: 'JetBrains Mono', monospace; }
.cyan { color: #7fe3ff; } .orange { color: #ff9a4d; } .green { color: #2fd39b; } .red { color: #ff6b6b; }
.amber { color: #ffb547; } .muted { color: #8f9cb2; }
.panel { background: rgba(8, 16, 30, .80); border: 1px solid rgba(127, 227, 255, .28); border-radius: 18px;
  box-shadow: 0 30px 80px -30px rgba(0, 0, 0, .8), 0 0 40px -14px rgba(127, 227, 255, .35); }
.shot { display: block; border-radius: 14px; border: 1px solid rgba(127, 227, 255, .25);
  box-shadow: 0 40px 90px -30px rgba(0, 0, 0, .9); }
.w { display: inline-block; white-space: pre; }
.chip { display: inline-block; padding: 10px 22px; border-radius: 999px; font-family: 'JetBrains Mono', monospace;
  font-size: 28px; letter-spacing: .06em; text-transform: uppercase; border: 1.5px solid currentColor;
  background: rgba(2, 4, 10, .72); }
.readout { position: absolute; padding: 26px 34px; border-radius: 16px; background: rgba(2, 6, 14, .82);
  border: 1px solid rgba(127, 227, 255, .3); backdrop-filter: blur(6px); }
.readout .big { font-size: 84px; font-weight: 700; letter-spacing: -.02em; line-height: 1; }
.readout .lbl { font-family: 'JetBrains Mono', monospace; font-size: 28px; letter-spacing: .12em;
  text-transform: uppercase; color: #8f9cb2; }
.vw { position: absolute; inset: 0; transform-origin: 50% 50%; }
.vw video { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }
.brk { position: absolute; width: 70px; height: 70px; border-color: rgba(127, 227, 255, .75); border-style: solid; }
.tag { position: absolute; left: 96px; top: 112px; font-family: 'JetBrains Mono', monospace; font-size: 28px;
  letter-spacing: .14em; text-transform: uppercase; color: #e7edf7; padding: 8px 16px; border-radius: 8px;
  background: rgba(2, 4, 10, .7); border: 1px solid rgba(127, 227, 255, .35); }
.tag i { display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #ff6b6b;
  margin-right: 12px; box-shadow: 0 0 12px #ff6b6b; vertical-align: 1px; }
"""

JS_HELPERS = """
const tl = gsap.timeline({ paused: true });
const q = (s) => document.querySelector(s);
const fmtInt = (v) => Math.round(v).toLocaleString('en-US');
function count(sel, from, to, at, dur, fmt) {
  const o = { v: from };
  tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.12, ease: 'power1.out' }, at);
  tl.fromTo(o, { v: from }, { v: to, duration: dur, ease: 'power2.out',
    onUpdate: () => { const el = q(sel); if (el) el.textContent = fmt(o.v); } }, at);
}
function words(sel, at, gap) {
  tl.fromTo(sel + ' .w', { opacity: 0, filter: 'blur(8px)' },
    { opacity: 1, filter: 'blur(0px)', duration: 0.16, stagger: gap || 0.07, ease: 'power2.out' }, at);
}
function land(sel, at, from) {
  tl.fromTo(sel, Object.assign({ opacity: 0, y: 26, filter: 'blur(6px)' }, from || {}),
    { opacity: 1, y: 0, x: 0, scale: 1, filter: 'blur(0px)', duration: 0.6, ease: 'expo.out' }, at);
}
function out(sel, at) {
  tl.to(sel, { opacity: 0, filter: 'blur(6px)', duration: 0.22, ease: 'power3.in' }, at);
}
"""


def wspan(text, cls=""):
    return "".join(f'<span class="w {cls}">{w} </span>' for w in text.split())


def clip(cid, start, dur, inner, cls="grp", style=""):
    return (f'<div id="{cid}" class="clip {cls}" data-start="{start:.3f}" data-duration="{max(dur, 0.1):.3f}" '
            f'style="{style}">{inner}</div>')


def video(cid, src, start, dur, media_start=0.0, rate=1.0, wrap_style=""):
    rate_attr = f' data-playback-rate="{rate:.3f}"' if abs(rate - 1) > 1e-3 else ""
    return (f'<div id="{cid}-wrap" class="vw" style="{wrap_style}"><video id="{cid}" class="clip" src="{src}" muted playsinline '
            f'data-start="{start:.3f}" data-duration="{max(dur, 0.1):.3f}" data-media-start="{max(media_start, 0):.3f}"{rate_attr}></video></div>')


def brackets(prefix):
    return "".join([
        f'<div class="brk" id="{prefix}-b1" style="left:60px;top:60px;border-left-width:3px;border-top-width:3px"></div>',
        f'<div class="brk" id="{prefix}-b2" style="right:60px;top:60px;border-right-width:3px;border-top-width:3px"></div>',
        f'<div class="brk" id="{prefix}-b3" style="left:60px;bottom:60px;border-left-width:3px;border-bottom-width:3px"></div>',
        f'<div class="brk" id="{prefix}-b4" style="right:60px;bottom:60px;border-right-width:3px;border-bottom-width:3px"></div>',
    ])


def scene_file(sid, dur, css, body, js):
    return f"""<template>
  <style>{BASE_CSS}{css}</style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080" data-duration="{dur:.3f}">
{body}
  </div>
  <script>
{JS_HELPERS}
{js}
window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def stars(sid, dur, opacity=1.0):
    return (f'<img id="{sid}-bg" class="bg" src="assets/bg/stars.jpg" style="opacity:{opacity}" alt="">',
            f"tl.fromTo('#{sid}-bg', {{ x: 0 }}, {{ x: -70, duration: {dur:.3f}, ease: 'none' }}, 0);")


# ---------------------------------------------------------------- scenes ----------------------------

TEAM = [("mahdin", "Mahdin Islam Mukim", "Team Lead"), ("maliha", "Maliha Sanjana", "UI/UX Designer"),
        ("lamisa", "Lamisa Yeasmin Nakia", "Research &amp; Storytelling Lead"),
        ("yousuf", "Yousuf Abdullah", "AI/ML Researcher · Data Scientist"), ("habibullah", "Md. Habibullah Sharif", "Systems Architect")]


def r1():
    """The machines NASA left behind: the app's Stories globe, then three of the machines, then Mars."""
    v, sid = VOICES["r1"], "r1"
    D = v.scene
    t_lander, t_rovers, t_heli, t_72 = v.at("A lander from 1967"), v.at("Rovers parked"), v.at("A little helicopter"), v.at("72")
    t_aband, t_each = v.at("They're abandoned"), v.at("each one still tells")
    bg, bgjs = stars(sid, D)
    cards = [("surveyor3", "Surveyor 3", "Moon · 1967", "-3"),
             ("apollo15-rover", "Apollo 15 rover", "Moon · 1971", "2"),
             ("ingenuity", "Ingenuity helicopter", "Mars · 2021", "-2")]
    cards_html = ""
    for i, (img, name, meta, rot) in enumerate(cards):
        cards_html += f'''<div id="r1-k{i}" class="abs panel" style="left:{150 + i * 560}px;top:250px;width:520px;padding:14px;transform:rotate({rot}deg)">
          <div style="width:492px;height:380px;border-radius:10px;overflow:hidden"><img src="assets/relics/{img}.jpg" style="width:100%;height:100%;object-fit:cover" alt="{name}, NASA photo"></div>
          <div class="h3" style="font-size:36px;margin-top:14px">{name}</div><div class="src" style="color:#7fe3ff">{meta}</div></div>'''
    body = f"""
{bg}
{video('r1-v1', 'assets/clips/c20_stories_moon.mp4', 0, t_lander - 0.05, 0.0)}
{clip('r1-hud1', 0, t_lander - 0.05, brackets('r1') + '<div class="tag" style="left:auto;right:96px"><i></i>Real app · Stories · the machines NASA left behind</div>')}
{clip('r1-cards', t_lander - 0.15, t_aband - t_lander + 0.1, f'''
  <div class="abs kick" style="left:150px;top:150px">Abandoned, not forgotten · NASA photos</div>
  {cards_html}
  <div id="r1-72" class="abs" style="left:1270px;top:800px"><span id="r1-n" class="h2 mono orange">0</span><span class="h3" style="margin-left:14px">flights on Mars</span></div>''')}
{video('r1-v2', 'assets/clips/c20_stories_mars.mp4', t_aband - 0.1, D - t_aband + 0.1, 0.0)}
{clip('r1-title', t_aband - 0.1, D - t_aband + 0.1, '''
  <div class="abs" style="left:0;top:600px;width:1920px;height:330px;background:linear-gradient(180deg,rgba(2,4,10,0),rgba(2,4,10,.88) 45%)"></div>
  <div class="abs kick" style="left:150px;top:690px">NASA Space Apps 2026 · our challenge</div>
  <div id="r1-t" class="abs h1" style="left:150px;top:735px"><span class="w">Abandoned, </span><span class="w">but </span><span class="w cyan">not </span><span class="w cyan">forgotten.</span></div>''')}
"""
    js = f"""{bgjs}
tl.fromTo('#r1-v1-wrap', {{ opacity: 0, scale: 1.06 }}, {{ opacity: 1, scale: 1, duration: 0.9, ease: 'expo.out' }}, 0);
tl.fromTo('#r1-hud1 .brk', {{ opacity: 0, scale: 1.3 }}, {{ opacity: 1, scale: 1, duration: 0.5, stagger: 0.05, ease: 'expo.out' }}, 0.2);
land('#r1-hud1 .tag', 0.4);
land('#r1-cards .kick', {t_lander - 0.1:.3f});
land('#r1-k0', {t_lander:.3f}, {{ y: 60, scale: 0.9 }});
land('#r1-k1', {t_rovers:.3f}, {{ y: 60, scale: 0.9 }});
land('#r1-k2', {t_heli:.3f}, {{ y: 60, scale: 0.9 }});
tl.fromTo('#r1-cards img', {{ scale: 1 }}, {{ scale: 1.08, duration: {t_aband - t_lander:.3f}, ease: 'none' }}, {t_lander:.3f});
land('#r1-72', {t_72 - 0.3:.3f}, {{ x: 30, y: 0 }});
count('#r1-n', 0, 72, {t_72 - 0.25:.3f}, 1.0, fmtInt);
tl.fromTo('#r1-v2-wrap', {{ clipPath: 'circle(0% at 50% 45%)' }}, {{ clipPath: 'circle(80% at 50% 45%)', duration: 0.6, ease: 'power2.out' }}, {t_aband - 0.1:.3f});
land('#r1-title .kick', {t_aband:.3f});
words('#r1-t', {t_aband + 0.05:.3f}, 0.12);
out('#r1-title .h1', {t_each + 1.6:.3f});
out('#r1-title .kick', {t_each + 1.6:.3f});
"""
    cues = {"whoosh_cards": t_lander - 0.2, "pop_72": t_72 + 0.75, "whoosh_mars": t_aband - 0.2}
    return scene_file(sid, D, "", body, js), cues


def r2():
    """What two of those machines taught us: Surveyor 3's parts survived; Apollo 17 fixed a fender with maps."""
    v, sid = VOICES["r2"], "r2"
    D = v.scene
    t_31, t_failed, t_later, t_maps, t_up = (v.at("After 31 months"), v.at("nothing had seriously failed"), v.at("Later"),
                                             v.at("maps and tape"), v.at("Up there"))
    body = f"""
{clip('r2-a', 0, t_later - 0.05, f'''
  <div id="r2-ph" class="abs" style="left:0;top:0;width:1920px;height:1080px;overflow:hidden">
    <img id="r2-img" src="assets/relics/surveyor3.jpg" style="position:absolute;left:640px;top:-200px;width:1280px;height:1280px;object-fit:cover" alt="Apollo 12 astronaut beside Surveyor 3"></div>
  <div class="abs" style="left:0;top:0;width:1100px;height:1080px;background:linear-gradient(90deg,rgba(2,4,10,.96) 55%,rgba(2,4,10,0))"></div>
  <div class="abs" style="left:150px;top:190px;width:820px">
    <div class="kick">Apollo 12 · November 1969</div>
    <div class="h2" style="margin-top:14px">{wspan("Astronauts visit")}<span class="w cyan">Surveyor 3</span></div>
    <div id="r2-m" class="abs" style="left:0;top:270px;white-space:nowrap"><span id="r2-n" class="h0 mono cyan" style="font-size:150px">0</span><span class="h3" style="margin-left:18px">months on the Moon</span></div>
    <div id="r2-ok" class="abs chip green" style="left:0;top:500px;font-size:32px">No serious failures</div>
    <div id="r2-src" class="abs src" style="left:0;top:580px">NASA SP-284 · 1972</div></div>
  <div class="abs src" style="right:96px;top:840px;background:rgba(2,4,10,.75);padding:4px 12px;border-radius:8px">Photo: NASA, AS12-48-7134</div>''')}
{clip('r2-b', t_later - 0.1, t_up - t_later + 0.05, f'''
  <div id="r2-fp" class="abs panel" style="left:960px;top:150px;width:780px;height:780px;overflow:hidden;padding:0">
    <img id="r2-fimg" src="assets/relics/apollo17-fender.jpg" style="width:100%;height:100%;object-fit:cover" alt="Apollo 17 rover fender rebuilt from maps and clamps">
    <div id="r2-ring" class="abs" style="left:150px;top:300px;width:330px;height:300px;border:4px solid #ff9a4d;border-radius:50%;box-shadow:0 0 30px rgba(255,154,77,.8)"></div></div>
  <div class="abs" style="left:150px;top:220px;width:760px">
    <div class="kick">Apollo 17 · December 1972</div>
    <div class="h2" style="margin-top:14px">{wspan("A broken fender,")}<br>{wspan("fixed with", "")}<span class="w orange">maps and tape</span></div>
    <div id="r2-chips" style="margin-top:40px">
      <span class="chip orange" style="margin:0 12px 14px 0">Folded maps</span>
      <span class="chip orange" style="margin:0 12px 14px 0">Tape</span>
      <span class="chip orange" style="margin:0 12px 14px 0">Clamps</span></div></div>
  <div class="abs src" style="left:960px;top:112px">Photo: NASA, AS17-137-20979</div>''')}
{clip('r2-c', t_up - 0.1, D - t_up + 0.1, '''
  <div class="abs" style="left:0;top:330px;width:1920px;text-align:center">
    <div class="kick muted">Up there</div>
    <div id="r2-none" class="h0" style="margin-top:20px">There are <span class="orange">no spare parts.</span></div></div>''')}
<div id="r2-in" class="clip abs" data-start="0" data-duration="0.4" style="left:0;top:0;width:1920px;height:1080px;background:#000"></div>
"""
    js = f"""
tl.fromTo('#r2-in', {{ opacity: 1 }}, {{ opacity: 0, duration: 0.35, ease: 'power2.out' }}, 0);
tl.fromTo('#r2-img', {{ scale: 1.0, x: 0 }}, {{ scale: 1.12, x: -60, duration: {t_later:.3f}, ease: 'none' }}, 0);
land('#r2-a .kick', 0.2);
words('#r2-a .h2', 0.4, 0.1);
land('#r2-m', {t_31 - 0.2:.3f});
count('#r2-n', 0, 31, {t_31 - 0.1:.3f}, 1.0, fmtInt);
tl.fromTo('#r2-ok', {{ opacity: 0, scale: 1.6, rotation: -3 }}, {{ opacity: 1, scale: 1, rotation: -3, duration: 0.3, ease: 'expo.out' }}, {t_failed:.3f});
land('#r2-src', {t_failed + 0.4:.3f});
land('#r2-fp', {t_later - 0.05:.3f}, {{ x: 80, y: 0 }});
tl.fromTo('#r2-fimg', {{ scale: 1.15 }}, {{ scale: 1.0, duration: {t_up - t_later:.3f}, ease: 'power1.out' }}, {t_later:.3f});
land('#r2-b .kick', {t_later:.3f});
words('#r2-b .h2', {t_later + 0.2:.3f}, 0.08);
tl.fromTo('#r2-ring', {{ opacity: 0, scale: 1.4 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: 'expo.out' }}, {t_maps - 0.2:.3f});
tl.fromTo('#r2-chips .chip', {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.4, stagger: 0.18, ease: 'expo.out' }}, {t_maps:.3f});
land('#r2-c .kick', {t_up:.3f});
tl.fromTo('#r2-none', {{ opacity: 0, scale: 1.08, filter: 'blur(10px)' }}, {{ opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.5, ease: 'expo.out' }}, {t_up + 0.1:.3f});
"""
    cues = {"pop_ok": t_failed + 0.1, "whoosh_fender": t_later - 0.2}
    return scene_file(sid, D, "", body, js), cues


def s1():
    v, sid = VOICES["s1"], "s1"
    D = v.scene
    t_broken, t_next, t_million = v.at("broken"), v.at("The next one"), v.at("a million dollars")
    brk_media = 7.1                      # the wrench snaps 7.1 s into c01
    t_snap = t_broken + 0.25
    v_start = 0.0
    ms = brk_media - (t_snap - v_start)
    bg, bgjs = stars(sid, D)
    body = f"""
{bg}
{video('s1-v', 'assets/clips/c01_wrench_break.mp4', v_start, t_next + 0.1 - v_start, ms, 1.0, 'transform-origin:34% 46%')}
{clip('s1-flash', t_snap - 0.02, 0.5, '', 'grp', 'background:radial-gradient(circle at 34% 46%, rgba(255,240,220,.95), rgba(255,107,107,.55) 30%, transparent 70%);opacity:0')}
{clip('s1-hud', 0.0, t_next + 0.1, brackets('s1') + '<div class="tag"><i></i>Real app footage · part test · PHB + 38% lunar dust</div>')}
{clip('s1-l1', t_snap + 0.35, t_next - t_snap - 0.3,
      f'<div class="abs h1" style="left:192px;top:790px;text-shadow:0 6px 34px #000,0 0 12px #000">{wspan("One broken")}<span class="w orange">wrench.</span></div>')}
{clip('s1-dist', t_next - 0.2, t_million - t_next - 0.05, f'''
  <img id="s1-moon" class="abs" src="assets/nasa/moon_disc.png" style="left:1030px;top:110px;width:760px;height:760px" alt="The Moon">
  <div id="s1-earth" class="abs" style="left:250px;top:700px;width:64px;height:64px;border-radius:50%;
    background:radial-gradient(circle at 35% 35%, #9fd8ff, #2a6fd6 55%, #0b2a66);box-shadow:0 0 40px rgba(90,170,255,.8)"></div>
  <div class="abs kick" style="left:205px;top:790px">Earth</div>
  <svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">
    <path id="s1-arc" d="M 282 732 Q 760 160 1250 470" fill="none" stroke="#7fe3ff" stroke-width="4"
      stroke-dasharray="14 12" pathLength="1000" stroke-dashoffset="1000" style="filter:drop-shadow(0 0 8px #7fe3ff)"/>
  </svg>
  <div id="s1-pod" class="abs" style="left:0;top:0;width:22px;height:22px;border-radius:50%;background:#ff9a4d;box-shadow:0 0 24px #ff9a4d"></div>
  <div class="abs" style="left:520px;top:250px;text-align:center">
    <div id="s1-km" class="h1 mono cyan">0 km</div>
    <div class="kick" style="color:#8f9cb2;margin-top:8px">from Earth to the Moon</div>
  </div>''')}
<div id="s1-dip" class="clip abs" data-start="{D - 0.25:.3f}" data-duration="0.25" style="left:0;top:0;width:1920px;height:1080px;background:#000;opacity:0"></div>
{clip('s1-money', t_million - 0.25, D - t_million + 0.25, f'''
  <img class="abs" src="assets/nasa/moon_disc.png" style="left:1180px;top:200px;width:700px;height:700px;opacity:.35" alt="">
  <div class="abs" style="left:192px;top:250px">
    <div class="kick orange">Resupply from Earth · up to</div>
    <div id="s1-usd" class="h0 orange" style="margin-top:14px;text-shadow:0 0 24px rgba(255,154,77,.35)">$0</div>
    <div class="h3" style="margin-top:18px">per kilogram, to send one spare part</div>
    <div class="src" style="margin-top:34px">NASA Glenn Research Center · NTRS 20260007758</div>
  </div>''')}
"""
    js = f"""{bgjs}
tl.fromTo('#s1-v-wrap', {{ scale: 1.0 }}, {{ scale: 1.16, duration: 0.45, ease: 'expo.out' }}, {t_snap:.3f});
tl.fromTo('#s1-v-wrap', {{ x: 0 }}, {{ keyframes: [{{ x: -18 }}, {{ x: 14 }}, {{ x: -9 }}, {{ x: 5 }}, {{ x: 0 }}], duration: 0.36, ease: 'none' }}, {t_snap:.3f});
tl.fromTo('#s1-flash', {{ opacity: 0 }}, {{ keyframes: [{{ opacity: 0.85, duration: 0.06 }}, {{ opacity: 0, duration: 0.4 }}] }}, {t_snap - 0.02:.3f});
tl.fromTo('#s1-hud .brk', {{ opacity: 0, scale: 1.3 }}, {{ opacity: 1, scale: 1, duration: 0.5, stagger: 0.05, ease: 'expo.out' }}, 0.1);
land('#s1-hud .tag', 0.25);
words('#s1-l1', {t_snap + 0.4:.3f}, 0.09);
out('#s1-l1', {t_next - 0.3:.3f});
land('#s1-moon', {t_next - 0.15:.3f}, {{ scale: 0.86, y: 0 }});
land('#s1-earth', {t_next:.3f}, {{ scale: 0.4, y: 0 }});
tl.fromTo('#s1-arc', {{ attr: {{ 'stroke-dashoffset': 1000 }} }}, {{ attr: {{ 'stroke-dashoffset': 0 }}, duration: 1.6, ease: 'power2.inOut' }}, {t_next + 0.2:.3f});
const pod = {{ p: 0 }};
tl.fromTo(pod, {{ p: 0 }}, {{ p: 1, duration: 1.6, ease: 'power2.inOut', onUpdate: () => {{
  const t = pod.p, x = (1-t)*(1-t)*282 + 2*(1-t)*t*760 + t*t*1250, y = (1-t)*(1-t)*732 + 2*(1-t)*t*160 + t*t*470;
  gsap.set('#s1-pod', {{ x: x - 11, y: y - 11 }}); }} }}, {t_next + 0.2:.3f});
count('#s1-km', 0, 384400, {t_next + 0.3:.3f}, 1.5, (v) => fmtInt(v) + ' km');
land('#s1-money .kick', {t_million - 0.2:.3f});
count('#s1-usd', 0, 1000000, {t_million - 0.1:.3f}, 1.3, (v) => '$' + fmtInt(v));
land('#s1-money .h3', {t_million + 0.25:.3f});
land('#s1-money .src', {t_million + 0.6:.3f});
tl.fromTo('#s1-dip', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2, ease: 'power2.in' }}, {D - 0.22:.3f});
"""
    cues = {"crack": t_snap, "whoosh_dist": t_next - 0.25, "pop_usd": t_million + 1.15}
    return scene_file(sid, D, "", body, js), cues


def s2():
    v, sid = VOICES["s2"], "s2"
    D = v.scene
    t_glenn, t_bact, t_site = v.at("NASA Glenn"), v.at("inside bacteria"), v.at("made on site")
    t_which, t_much, t_strong, t_cant = v.at("But which mix"), v.at("How much dust"), v.at("strong enough"), v.at("You can't test")
    bg, bgjs = stars(sid, D)
    slots = [("Binder", ["PLA", "PEEK", "LDPE", "PEI", "PPSU", "PLA", "PEEK", "PHB"]),
             ("Soil", ["Lunar mare", "Martian", "Lunar mare", "Martian", "Lunar mare", "Lunar highlands"]),
             ("Made by", ["Filament", "Pellet", "Hot-pressed", "Sintered", "Filament", "Molded"]),
             ("Dust", ["10%", "60%", "85%", "25%", "92.5%", "50%", "70%", "38%"])]
    slot_html = ""
    for i, (name, vals) in enumerate(slots):
        items = "".join(f'<div style="height:96px;line-height:96px;white-space:nowrap">{x}</div>' for x in vals)
        slot_html += f'''<div class="abs panel" style="left:{192 + i * 392}px;top:430px;width:360px;height:150px;overflow:hidden">
          <div class="kick" style="position:absolute;left:24px;top:8px;color:#8f9cb2">{name}</div>
          <div style="position:absolute;left:24px;top:46px;width:320px;height:96px;overflow:hidden" data-layout-ignore>
          <div id="s2-col{i}" class="h3" style="position:absolute;left:0;top:0;width:320px;font-size:40px">{items}</div></div></div>'''
    body = f"""
{bg}
{clip('s2-a', 0, t_which - 0.05, f'''
  <div class="abs kick" style="left:192px;top:112px">NASA Glenn Research Center · September 2026</div>
  <div class="abs h2" style="left:192px;top:150px;width:1540px">{wspan("A plastic grown inside bacteria,")}<span class="w cyan">+ simulated Moon & Mars dust</span></div>
  <div id="s2-p1" class="abs panel" style="left:192px;top:300px;width:740px;height:520px;overflow:hidden">
    <img id="s2-i1" src="assets/nasa/lsp-2-100x.jpg" style="width:100%;height:100%;object-fit:cover" alt="NASA Glenn microscope image, Moon dust composite">
    <div class="abs chip" style="left:20px;bottom:20px;color:#e7edf7">Moon dust simulant · 100×</div></div>
  <div id="s2-p2" class="abs panel" style="left:988px;top:300px;width:740px;height:520px;overflow:hidden">
    <img id="s2-i2" src="assets/nasa/jez-1-100x.jpg" style="width:100%;height:100%;object-fit:cover" alt="NASA Glenn microscope image, Mars dust composite">
    <div class="abs chip" style="left:20px;bottom:20px;color:#ffb38a">Mars dust simulant · 100×</div></div>
  <div class="abs src" style="right:192px;top:832px">Microscope images: NASA</div>
  <div id="s2-site" class="abs chip green" style="left:192px;top:832px">Could be made on site</div>''')}
{clip('s2-b', t_which - 0.1, D - t_which + 0.1, f'''
  <div class="abs src" style="left:192px;top:112px" data-var-text="challenge">NASA Space Apps 2026 · Abandoned but not Forgotten</div>
  <div id="s2-which" class="abs h0" style="left:192px;top:180px">{wspan("Which")}<span class="w orange">mix?</span></div>
  {slot_html}
  <div id="s2-q" class="abs" style="left:192px;top:630px">
    <span class="chip cyan" style="margin-right:18px">How much dust?</span>
    <span class="chip cyan" style="margin-right:18px">Which dust?</span>
    <span class="chip orange">Strong enough?</span></div>
  <div id="s2-cnt" class="abs" style="left:192px;top:730px">
    <span id="s2-n" class="h1 mono orange">0</span>
    <span class="h3" style="margin-left:18px">possible mixes for one wrench. Too many to test on Earth.</span></div>''')}
<div id="s2-in" class="clip abs" data-start="0" data-duration="0.4" style="left:0;top:0;width:1920px;height:1080px;background:#000"></div>
"""
    rolls = ""
    for i, (_, vals) in enumerate(slots):
        end_y = -(len(vals) - 1) * 96
        rolls += f"tl.fromTo('#s2-col{i}', {{ y: 0 }}, {{ y: {end_y}, duration: {1.3 + i * 0.35:.2f}, ease: 'power3.inOut' }}, {t_which + 0.5:.3f});\n"
    js = f"""{bgjs}
tl.fromTo('#s2-in', {{ opacity: 1 }}, {{ opacity: 0, duration: 0.3, ease: 'power2.out' }}, 0);
land('#s2-a .kick', 0.2);
words('#s2-a .h2', {t_glenn:.3f}, 0.07);
land('#s2-p1', 0.3, {{ x: -60, y: 0 }});
land('#s2-p2', 0.55, {{ x: 60, y: 0 }});
tl.fromTo('#s2-i1', {{ scale: 1.04 }}, {{ scale: 1.16, duration: {t_which:.3f}, ease: 'none' }}, 0);
tl.fromTo('#s2-i2', {{ scale: 1.16 }}, {{ scale: 1.04, duration: {t_which:.3f}, ease: 'none' }}, 0);
land('#s2-a .src', {t_glenn + 0.9:.3f});
land('#s2-site', {t_site - 0.9:.3f}, {{ scale: 0.8, y: 0 }});
tl.fromTo('#s2-which .w', {{ opacity: 0, scale: 1.4, filter: 'blur(10px)' }}, {{ opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.35, stagger: 0.12, ease: 'expo.out' }}, {t_which:.3f});
land('#s2-b .src', {t_which + 0.2:.3f});
tl.fromTo('#s2-b .panel', {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.5, stagger: 0.08, ease: 'expo.out' }}, {t_which + 0.3:.3f});
{rolls}
tl.fromTo('#s2-q .chip', {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.45, stagger: {(t_strong - t_much) / 2:.3f}, ease: 'expo.out' }}, {t_much:.3f});
land('#s2-cnt', {t_cant - 1.0:.3f});
count('#s2-n', 0, 4662, {t_cant - 0.9:.3f}, 1.4, fmtInt);
"""
    cues = {"whoosh_which": t_which - 0.15, "pop_cnt": t_cant + 1.2}
    return scene_file(sid, D, "", body, js), cues


def s3():
    v, sid = VOICES["s3"], "s3"
    D = v.scene
    t_name, t_pick, t_inst = v.at("Moon-Material Simulator"), v.at("Pick a binder"), v.at("Instantly")
    t_eight, t_sure, t_lab, t_browser = v.at("eight properties"), v.at("how sure"), v.at("real lab data"), v.at("It runs in any browser")
    bg, bgjs = stars(sid, D)
    title = "".join(f'<span class="w">{c}</span>' for c in "MOON-MATERIAL SIMULATOR")
    hero_start, hero_end = t_pick - 0.2, t_pick + 1.6
    ui_start = hero_end - 0.05
    ui_window = t_browser - 0.25 - ui_start
    rate = min(1.0, max(0.75, 9.5 / max(ui_window, 1)))
    body = f"""
{bg}
{clip('s3-title', 0, t_pick - 0.15, f'''
  <div id="s3-logo" class="abs" style="left:870px;top:150px;width:180px;height:180px;border-radius:28px;overflow:hidden;background:#fff;box-shadow:0 0 50px rgba(127,227,255,.35)">
    <img src="assets/brand/dreams-of-x-logo.jpeg" style="width:100%;height:100%;object-fit:contain" alt="Dreams of X logo"></div>
  <div id="s3-name" class="abs h1" style="left:0;width:1920px;top:400px;text-align:center;font-size:118px">{title}</div>
  <div id="s3-scan" class="abs" style="left:0;top:385px;width:220px;height:150px;background:linear-gradient(90deg,transparent,rgba(127,227,255,.55),transparent);mix-blend-mode:screen"></div>
  <div id="s3-sub" class="abs body" style="left:0;width:1920px;top:560px;text-align:center">by <b class="cyan">Dreams of X</b> · Abandoned but not Forgotten</div>''')}
{clip('s3-hero', hero_start, hero_end - hero_start, '<div id="s3-hz" class="abs" style="left:0;top:0;width:1920px;height:1080px;transform-origin:530px 728px"><img src="assets/screens/hero.png" style="width:1920px;height:1080px" alt="Simulator home page"></div>')}
<img id="s3-simstill" class="clip abs" src="assets/screens/simulator.png" data-start="{ui_start:.3f}" data-duration="{t_browser - 0.2 - ui_start:.3f}" style="left:0;top:0;width:1920px;height:1080px" alt="">
{video('s3-ui', 'assets/clips/u03_design.mp4', ui_start, t_browser - 0.2 - ui_start, 0.0, rate)}
{clip('s3-hud', ui_start, t_browser - 0.2 - ui_start, '<div class="tag" style="left:auto;right:96px"><i></i>Real app · drag the slider, every number updates</div>')}
{clip('s3-iso', t_eight - 0.5, t_browser - t_eight + 0.6, f'''
  <div id="s3-dim" class="abs" style="left:0;top:0;width:1920px;height:1080px;background:rgba(2,4,10,.62)"></div>
  <div id="s3-grid" class="abs" style="left:1210px;top:140px;width:500px;height:780px;border-radius:16px;overflow:hidden;
     border:1.5px solid rgba(127,227,255,.6);box-shadow:0 0 60px rgba(127,227,255,.35),0 40px 90px -30px #000">
    <img src="assets/screens/hi_property_grid.png" style="width:500px;height:780px;object-fit:cover;object-position:top" alt="Results panel close-up"></div>
  <div id="s3-c1" class="abs chip cyan" style="left:760px;top:170px">8 properties · live</div>
  <div id="s3-c2" class="abs chip orange" style="left:760px;top:330px">Likely range</div>
  <div id="s3-c3" class="abs chip green" style="left:690px;top:490px">Lab-backed or physics estimate</div>''')}
{video('s3-print', 'assets/clips/c02_print.mp4', t_browser - 0.25, D - t_browser + 0.25, 0.2)}
{clip('s3-end', t_browser - 0.1, D - t_browser + 0.1, '''
  <div class="abs" style="left:192px;top:700px">
    <div class="h2">Runs in any <span class="cyan">browser</span>. Open source.</div>
    <div class="src" style="margin-top:14px">github.com/md8-habibullah/moon-material-simulator</div></div>''')}
"""
    js = f"""{bgjs}
land('#s3-logo', 0.1, {{ scale: 0.7, y: 0 }});
tl.fromTo('#s3-name .w', {{ opacity: 0.0, filter: 'blur(10px)' }}, {{ opacity: 1, filter: 'blur(0px)', duration: 0.2, stagger: 0.045, ease: 'power2.out' }}, {max(0.4, t_name - 0.6):.3f});
tl.fromTo('#s3-scan', {{ x: -260 }}, {{ x: 1960, duration: 1.0, ease: 'power2.inOut' }}, {t_name + 0.4:.3f});
land('#s3-sub', 0.5);
tl.fromTo('#s3-hz', {{ scale: 1 }}, {{ scale: 1.08, duration: 1.1, ease: 'power2.inOut' }}, {hero_start:.3f});
tl.to('#s3-hz', {{ scale: 7, duration: 0.55, ease: 'power3.in' }}, {hero_end - 0.6:.3f});
tl.fromTo('#s3-ui-wrap', {{ scale: 1.25, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.5, ease: 'expo.out' }}, {ui_start:.3f});
land('#s3-hud .tag', {ui_start + 0.3:.3f});
tl.to('#s3-ui-wrap', {{ x: -330, scale: 0.86, duration: 0.8, ease: 'power2.inOut' }}, {t_eight - 0.5:.3f});
tl.fromTo('#s3-dim', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: 'power2.out' }}, {t_eight - 0.45:.3f});
land('#s3-grid', {t_eight - 0.2:.3f}, {{ x: 80, y: 0 }});
land('#s3-c1', {t_eight - 0.3:.3f}, {{ x: -40, y: 0 }});
land('#s3-c2', {t_sure - 0.4:.3f}, {{ x: -40, y: 0 }});
land('#s3-c3', {t_lab - 0.8:.3f}, {{ x: -40, y: 0 }});
tl.fromTo('#s3-print-wrap', {{ clipPath: 'circle(0% at 70% 50%)' }}, {{ clipPath: 'circle(80% at 70% 50%)', duration: 0.6, ease: 'power2.out' }}, {t_browser - 0.25:.3f});
land('#s3-end .h2', {t_browser:.3f});
land('#s3-end .src', {t_browser + 0.8:.3f});
"""
    cues = {"whoosh_zoom": hero_end - 0.55, "click_hero": hero_end - 0.7, "pop_c1": t_eight + 0.1, "pop_c2": t_sure + 0.1,
            "pop_c3": t_lab + 0.1, "whoosh_print": t_browser - 0.3}
    return scene_file(sid, D, "", body, js), cues


def s4():
    v, sid = VOICES["s4"], "s4"
    D = v.scene
    t_data, t_glenn, t_ken, t_2003, t_peer = (v.at("NASA's own data"), v.at("Glenn's"), v.at("Kennedy's"),
                                             v.at("2003"), v.at("peer-reviewed"))
    t_trans, t_page, t_aud, t_never, t_zero, t_181 = (v.at("We transcribed"), v.at("its page"), v.at("built an auditor"),
                                                       v.at("never edits"), v.at("Zero"), v.at("181"))
    bg, bgjs = stars(sid, D, 0.8)
    docs = [("s011_p1", "NASA Glenn", "NTRS 20260007758", "glenn"), ("s006_p1", "NASA Glenn", "NTRS 20260003641", "glenn"),
            ("s003_p1", "NASA Kennedy", "NTRS 20230015024", "ken"), ("s012_p1", "NASA Kennedy", "NTRS 20240004186", "ken"),
            ("s013_p1", "NASA · 2003", "NTRS 20030020808", "n03"),
            ("s001_p1", "Polymers", "2020 · CC BY", "peer"), ("s002_p1", "Polymers", "2025 · CC BY", "peer"),
            ("s004_p1", "Applied Sciences", "2025 · CC BY", "peer"), ("s007_p1", "Acta Astronautica", "2025 · CC BY", "peer"),
            ("s008_p1", "Polymers", "2026 · CC BY", "peer")]
    cards = ""
    for i, (img, org, ident, grp) in enumerate(docs):
        row, col = divmod(i, 5)
        x, y = 188 + col * 312, 190 + row * 345
        cards += f'''<div id="s4-d{i}" class="abs panel s4-{grp}" style="left:{x}px;top:{y}px;width:296px;height:320px;overflow:hidden">
          <img src="assets/docs/{img}.jpg" style="width:296px;height:220px;object-fit:cover;object-position:top" alt="{org} document">
          <div style="padding:10px 12px"><div class="h3" style="font-size:28px;white-space:nowrap">{org}</div>
          <div class="mono" style="font-size:28px;color:#7fe3ff;margin-top:2px;white-space:nowrap;letter-spacing:-.03em">{ident}</div></div></div>'''
    body = f"""
{bg}
{clip('s4-wall', 0, t_trans - 0.05, f'''
  <div class="abs kick" style="left:196px;top:112px">The evidence · NASA Technical Reports Server + peer-reviewed studies</div>
  {cards}''')}
{clip('s4-page', t_trans - 0.1, t_aud - t_trans + 0.05, f'''
  <div id="s4-pg" class="abs panel" style="left:192px;top:120px;width:560px;height:792px;overflow:hidden;background:#fff">
    <div id="s4-pgz" class="abs" style="left:0;top:0;width:560px;height:792px;transform-origin:24% 13%">
      <img src="assets/docs/s008_p15.jpg" style="width:560px;height:792px;display:block" alt="Paper page 15, Figure 11">
      <div id="s4-box" class="abs" style="left:14px;top:22px;width:262px;height:190px;border:3px solid #ff9a4d;border-radius:5px;box-shadow:0 0 16px rgba(255,154,77,.8)"></div></div></div>
  <div class="abs" style="left:860px;top:150px">
    <div class="kick muted">13 sources →</div>
    <div id="s4-n" class="h0 cyan mono" style="font-size:190px">0</div>
    <div class="h2" style="margin-top:6px">measured values</div>
    <div id="s4-chips" style="margin-top:44px;width:860px">
      <span class="chip orange" style="margin:0 12px 14px 0">Page 15</span>
      <span class="chip orange" style="margin:0 12px 14px 0">Figure 11</span>
      <span class="chip orange" style="margin:0 12px 14px 0">Row · PEI composites</span>
      <span class="chip orange" style="margin:0 12px 14px 0">Column · compressive strength</span></div>
    <div class="src" style="margin-top:22px">Every value carries its address in the source PDF</div></div>''')}
{clip('s4-audit', t_aud - 0.1, t_zero - t_aud + 0.05, f'''
  <div class="abs kick" style="left:192px;top:112px">Evidence auditor · <span class="mono">python -m evidence.audit</span></div>
  <div id="s4-stats" class="abs" style="left:192px;top:160px;width:1536px;border-radius:10px;overflow:hidden;border:1px solid rgba(127,227,255,.3)">
    <img src="assets/screens/hi_audit_stats.png" style="width:1536px;display:block" alt="Audit summary: 1470 measurements, 0 errors"></div>
  <div id="s4-card" class="abs" style="left:310px;top:300px;width:1300px;border-radius:12px;overflow:hidden;border:1px solid rgba(127,227,255,.35)">
    <img src="assets/screens/audit_card.png" style="width:1300px;display:block" alt="One audit finding with the PDF crop">
    <div id="s4-sweep" class="abs" style="left:0;top:0;width:1300px;height:8px;background:#7fe3ff;box-shadow:0 0 30px 8px rgba(127,227,255,.7)"></div></div>
  <div id="s4-stamp" class="abs chip amber" style="left:1110px;top:250px;font-size:30px">Comments only · never edits data</div>''')}
{clip('s4-tiles', t_zero - 0.15, D - t_zero + 0.15, f'''
  <div class="abs kick" style="left:192px;top:112px">Audit result</div>
  <div id="s4-t0" class="abs" style="left:192px;top:190px"><div id="s4-z" class="h0 green" style="font-size:260px">0</div>
    <div class="h3">transcription errors</div><div class="src">1,470 values re-found in their PDFs</div></div>
  <div id="s4-t1" class="abs" style="left:900px;top:200px"><div id="s4-p" class="h0 amber" style="font-size:180px">0</div>
    <div class="h3">problems inside the papers</div><div class="src">logged with page and quote</div></div>
  <div id="s4-t2" class="abs" style="left:900px;top:560px"><div class="h1 cyan">56 / 56</div>
    <div class="h3">original NASA calibration points re-verified</div></div>''')}
"""
    js = f"""{bgjs}
land('#s4-wall .kick', 0.15);
tl.fromTo('#s4-wall .panel', {{ opacity: 0, rotationY: 65, z: -300, transformPerspective: 1400 }},
  {{ opacity: 1, rotationY: 0, z: 0, transformPerspective: 1400, duration: 0.7, stagger: 0.07, ease: 'expo.out' }}, {max(0.2, t_data - 0.2):.3f});
function glow(cls, at) {{ tl.fromTo(cls, {{ borderColor: 'rgba(127,227,255,.28)', boxShadow: '0 0 0 rgba(127,227,255,0)' }},
  {{ borderColor: '#7fe3ff', boxShadow: '0 0 46px rgba(127,227,255,.75)', duration: 0.35, ease: 'power2.out' }}, at);
  tl.to(cls, {{ borderColor: 'rgba(127,227,255,.28)', boxShadow: '0 0 0 rgba(127,227,255,0)', duration: 0.6 }}, at + 1.4); }}
glow('.s4-glenn', {t_glenn:.3f}); glow('.s4-ken', {t_ken:.3f}); glow('.s4-n03', {t_2003:.3f}); glow('.s4-peer', {t_peer:.3f});
land('#s4-pg', {t_trans - 0.05:.3f}, {{ x: -60, y: 0 }});
count('#s4-n', 0, 1470, {t_trans + 0.2:.3f}, 1.5, fmtInt);
land('#s4-page .kick', {t_trans:.3f}); land('#s4-page .h2', {t_trans + 0.5:.3f});
tl.fromTo('#s4-pgz', {{ scale: 1 }}, {{ scale: 1.9, duration: 1.0, ease: 'power2.inOut' }}, {t_page - 0.3:.3f});
tl.fromTo('#s4-box', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: 'power2.out' }}, {t_page + 0.5:.3f});
tl.fromTo('#s4-chips .chip', {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.45, stagger: 0.2, ease: 'expo.out' }}, {t_trans + 0.9:.3f});
land('#s4-page .src', {t_trans + 1.2:.3f});
land('#s4-audit .kick', {t_aud:.3f});
land('#s4-stats', {t_aud + 0.1:.3f});
land('#s4-card', {t_aud + 0.35:.3f}, {{ scale: 0.94, y: 0 }});
tl.fromTo('#s4-sweep', {{ y: 0, opacity: 1 }}, {{ y: 500, opacity: 0.2, duration: 1.8, ease: 'power1.inOut' }}, {t_aud + 0.7:.3f});
tl.fromTo('#s4-stamp', {{ opacity: 0, scale: 1.8, rotation: -4 }}, {{ opacity: 1, scale: 1, rotation: -4, duration: 0.3, ease: 'expo.out' }}, {t_never - 0.35:.3f});
land('#s4-tiles .kick', {t_zero - 0.1:.3f});
land('#s4-t0', {t_zero - 0.05:.3f}, {{ scale: 0.8, y: 0 }});
land('#s4-t1', {t_181 - 0.15:.3f}, {{ x: 40, y: 0 }});
count('#s4-p', 0, 181, {t_181 - 0.1:.3f}, 1.2, fmtInt);
land('#s4-t2', {t_181 + 0.6:.3f}, {{ x: 40, y: 0 }});
tl.to('#s4-tiles', {{ x: -160, filter: 'blur(14px)', opacity: 0, duration: 0.25, ease: 'power3.in' }}, {D - 0.25:.3f});
"""
    cues = {"whoosh_page": t_trans - 0.1, "whoosh_audit": t_aud - 0.1, "pop_stamp": t_never - 0.3, "pop_zero": t_zero,
            "pop_181": t_181 + 1.0, "pop_56": t_181 + 0.65, "whoosh_out": D - 0.3}
    return scene_file(sid, D, "", body, js), cues


def s5():
    v, sid = VOICES["s5"], "s5"
    D = v.scene
    t_230, t_kept, t_gp, t_152 = v.at("230 percent"), v.at("kept the physics"), v.at("Gaussian process"), v.at("152")
    t_never, t_34, t_65, t_16 = v.at("never saw"), v.at("34 percent"), v.at("65 to 19"), v.at("16 to 5")
    t_new, t_ev, t_117, t_119 = v.at("completely new study"), v.at("every prediction links"), v.at("117"), v.at("119")
    bg, bgjs = stars(sid, D, 0.7)
    nodes = [("Physics", "composite equations, temperature effects"),
             ("Fast emulator", "28-tree random forest, runs in your browser"),
             ("Learned correction", "Gaussian process trained on <b id='s5-152' class='cyan'>0</b> real measurements, 7 studies"),
             ("Prediction", "value + likely range + link to the evidence")]
    nodes_html = ""
    for i, (h, b) in enumerate(nodes):
        x = 192 + i * 392
        nodes_html += f'''<div id="s5-n{i}" class="abs panel" style="left:{x}px;top:300px;width:350px;height:380px;padding:28px">
          <div class="kick" style="color:#8f9cb2">Step {i + 1}</div>
          <div class="h3" style="margin-top:10px">{h}</div><div class="body" style="font-size:28px;margin-top:12px">{b}</div></div>'''
        if i < 3:
            nodes_html += f'<div id="s5-l{i}" class="abs" style="left:{x + 350}px;top:488px;width:42px;height:4px;background:#7fe3ff;box-shadow:0 0 12px #7fe3ff;transform-origin:left center"></div>'
    rows = [("Compressive strength", 230, 34), ("Stiffness", 65, 19), ("Density", 16, 5), ("Thermal conductivity", 32, 7)]
    rows_html = ""
    for i, (name, a, b) in enumerate(rows):
        y = 280 + i * 135
        rows_html += f'''<div class="abs h3" style="left:192px;top:{y}px;width:470px;font-size:38px">{name}</div>
          <div class="abs" style="left:680px;top:{y - 2}px;width:860px;height:30px;border-radius:8px;background:#4b5566"></div>
          <div id="s5-b{i}" class="abs" style="left:680px;top:{y + 36}px;width:{860 * b / a:.0f}px;height:30px;border-radius:8px;background:#7fe3ff;box-shadow:0 0 18px rgba(127,227,255,.6);transform-origin:left center"></div>
          <div id="s5-v{i}" class="abs mono h3" style="left:1560px;top:{y + 4}px;font-size:40px"><span class="muted">{a}%</span> → <span class="cyan">{b}%</span></div>'''
    body = f"""
{bg}
{clip('s5-a', 0, t_kept - 0.05, '''
  <div class="abs kick red" style="left:192px;top:200px">Physics alone · compressive strength · real samples</div>
  <div id="s5-230" class="abs h0 red" style="left:180px;top:260px;font-size:300px">0%</div>
  <div class="abs h3" style="left:192px;top:610px">average error before learning from lab data</div>''')}
{clip('s5-pipe', t_kept - 0.1, t_never - t_kept + 0.05, f'''
  <div class="abs kick" style="left:192px;top:200px">How the prediction is made</div>
  {nodes_html}''')}
{clip('s5-bars', t_never - 0.1, t_ev - t_never + 0.05, f'''
  <div class="abs kick" style="left:192px;top:130px">Average error on mixes the model never saw</div>
  <div class="abs src" style="left:680px;top:200px"><span style="color:#aab4c4">■ physics alone</span>   <span class="cyan">■ + learned from lab data</span></div>
  {rows_html}
  <div id="s5-honest" class="abs panel" style="left:560px;top:300px;width:800px;padding:40px 46px;border-color:#ffb547;box-shadow:0 0 60px rgba(255,181,71,.35)">
    <div class="kick amber">A study it has never seen</div>
    <div class="h0 amber" style="font-size:170px;margin-top:6px">78%</div>
    <div class="h3">compressive-strength error. Harder, and we say so.</div></div>''')}
{clip('s5-ev', t_ev - 0.1, D - t_ev + 0.1, f'''
  <div class="abs kick" style="left:192px;top:112px">Every prediction links to its evidence</div>
  <div id="s5-evimg" class="abs" style="left:192px;top:170px;width:560px;height:745px;border-radius:14px;overflow:hidden;border:1px solid rgba(127,227,255,.35)">
    <img src="assets/screens/hi_evidence_119.png" style="width:560px;display:block" alt="Evidence drawer: 119 MPa measured, S008 Figure 11"></div>
  <div class="abs" style="left:860px;top:220px">
    <div class="kick cyan">Predicted</div><div id="s5-117" class="h0 cyan">0 <span style="font-size:60px">MPa</span></div></div>
  <div class="abs" style="left:860px;top:500px">
    <div class="kick green">Measured in the paper</div><div id="s5-119" class="h0 green">0 <span style="font-size:60px">MPa</span></div>
    <div class="src" style="margin-top:14px">Storozhuk et al. 2026 · Polymers · Figure 11 · PEI + 80% lunar simulant, hot-pressed</div></div>''')}
"""
    js = f"""{bgjs}
land('#s5-a .kick', 0.15);
count('#s5-230', 0, 230, {t_230 - 0.3:.3f}, 1.2, (v) => fmtInt(v) + '%');
land('#s5-a .h3', {t_230 - 0.2:.3f});
land('#s5-pipe .kick', {t_kept:.3f});
tl.fromTo('#s5-pipe .panel', {{ opacity: 0, y: 40, filter: 'blur(6px)' }}, {{ opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.6, stagger: 0.35, ease: 'expo.out' }}, {t_kept + 0.1:.3f});
tl.fromTo('#s5-pipe [id^=s5-l]', {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.3, stagger: 0.35, ease: 'power2.out' }}, {t_kept + 0.45:.3f});
tl.fromTo('#s5-n2', {{ borderColor: 'rgba(127,227,255,.28)' }}, {{ borderColor: '#7fe3ff', boxShadow: '0 0 60px rgba(127,227,255,.6)', scale: 1.05, duration: 0.4, ease: 'expo.out' }}, {t_gp:.3f});
count('#s5-152', 0, 152, {t_152 - 0.3:.3f}, 1.0, fmtInt);
land('#s5-bars .kick', {t_never:.3f}); land('#s5-bars .src', {t_never + 0.3:.3f});
const rowsAt = [{t_34 - 0.6:.3f}, {t_65:.3f}, {t_16:.3f}, {t_16 + 1.1:.3f}];
rowsAt.forEach((at, i) => {{
  tl.fromTo('#s5-b' + i, {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.7, ease: 'expo.out' }}, at);
  tl.fromTo('#s5-v' + i, {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: 'expo.out' }}, at + 0.15);
}});
tl.fromTo('#s5-honest', {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: 'expo.out' }}, {t_new:.3f});
land('#s5-ev .kick', {t_ev:.3f});
land('#s5-evimg', {t_ev + 0.15:.3f}, {{ x: -50, y: 0 }});
countU('#s5-117', 0, 117, {t_117 - 0.4:.3f}, 0.9);
countU('#s5-119', 0, 119, {t_119 - 0.3:.3f}, 0.9);
land('#s5-ev .src', {t_ev + 0.9:.3f});
"""
    js = """function countU(sel, from, to, at, dur) { const o = { v: from };
  tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: 0.12 }, at);
  tl.fromTo(o, { v: from }, { v: to, duration: dur, ease: 'power2.out', onUpdate: () => { const el = q(sel);
    if (el) el.innerHTML = Math.round(o.v) + ' <span style="font-size:60px">MPa</span>'; } }, at); }
""" + js
    cues = {"pop_230": t_230 + 0.9, "whoosh_pipe": t_kept - 0.1, "pop_gp": t_gp, "whoosh_bars": t_never - 0.1,
            "pop_honest": t_new + 0.05, "whoosh_ev": t_ev - 0.1, "pop_117": t_117 + 0.5, "pop_119": t_119 + 0.6}
    return scene_file(sid, D, "", body, js), cues


def readout(cid, kicker, value, value_cls, note, note_cls="muted", left=1180, top=560):
    return f'''<div id="{cid}" class="readout" style="left:{left}px;top:{top}px;width:600px">
      <div class="lbl">{kicker}</div><div class="big {value_cls}" style="margin-top:10px">{value}</div>
      <div class="h3 {note_cls}" style="font-size:34px;margin-top:10px">{note}</div></div>'''


def s6a():
    v, sid = VOICES["s6a"], "s6a"
    D = v.scene
    t_71, t_72, t_noon, t_night, t_brittle, t_snaps = (v.at("71"), v.at("72"), v.at("At lunar noon"), v.at("At lunar night"),
                                                       v.at("brittle"), v.at("snaps"))
    # c01 (habitat): snaps at 7.1 s. c04: noon from 0.6 s, night from 5.0 s, snaps at about 14.2 s.
    a_end = t_noon - 0.05
    a_ms = max(0.0, 7.1 - (t_72 + 0.7))
    n_start = t_night - 0.1
    night_need = (t_snaps + 0.25) - n_start
    n_rate = max(1.0, (14.2 - 5.2) / max(night_need, 0.5))
    n_ms = 14.2 - night_need * n_rate
    body = f"""
{video('s6a-v1', 'assets/clips/c01_wrench_break.mp4', 0, a_end, a_ms)}
{video('s6a-v2', 'assets/clips/c04_noon_night.mp4', t_noon - 0.1, n_start - t_noon + 0.1, 0.5)}
{video('s6a-v3', 'assets/clips/c04_noon_night.mp4', n_start, D - n_start, n_ms, n_rate)}
{clip('s6a-hud', 0, D, brackets('s6a') + '<div class="tag"><i></i>Real app footage · part test · beam theory on the model&#39;s predictions</div>')}
{clip('s6a-r1', t_71 - 0.2, a_end - t_71 + 0.15, readout('s6a-ro1', 'Inside the habitat · 20 °C', '0.98×', 'red', 'breaks at 71 N · needs 72 N', 'h3'))}
{clip('s6a-r2', t_noon - 0.05, n_start - t_noon + 0.05, readout('s6a-ro2', 'Lunar noon · +127 °C', '0.16×', 'amber', 'softens'))}
{clip('s6a-r3', t_night, D - t_night, readout('s6a-ro3', 'Lunar night · −173 °C', '1.83×', 'green', '<span id="s6a-brittle" class="amber">but brittle: it snaps</span>'))}
"""
    js = f"""
tl.fromTo('#s6a-v1-wrap', {{ clipPath: 'circle(0% at 50% 50%)' }}, {{ clipPath: 'circle(75% at 50% 50%)', duration: 0.55, ease: 'power2.out' }}, 0);
tl.fromTo('#s6a-hud .brk', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, stagger: 0.05 }}, 0.2);
land('#s6a-hud .tag', 0.3);
land('#s6a-ro1', {t_71 - 0.15:.3f}, {{ x: 60, y: 0 }});
land('#s6a-ro2', {t_noon:.3f}, {{ x: 60, y: 0 }});
land('#s6a-ro3', {t_night + 0.05:.3f}, {{ x: 60, y: 0 }});
tl.fromTo('#s6a-brittle', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {t_brittle - 0.1:.3f});
tl.fromTo('#s6a-v3-wrap', {{ x: 0 }}, {{ keyframes: [{{ x: -14 }}, {{ x: 10 }}, {{ x: -6 }}, {{ x: 0 }}], duration: 0.3, ease: 'none' }}, {t_snaps + 0.25:.3f});
"""
    cues = {"crack_habitat": t_72 + 0.7, "whoosh_noon": t_noon - 0.15, "whoosh_night": n_start - 0.05, "crack_night": t_snaps + 0.25}
    return scene_file(sid, D, "", body, js), cues


def s6b():
    v, sid = VOICES["s6b"], "s6b"
    D = v.scene
    t_opt, t_5k, t_ent, t_45, t_sf, t_bends = (v.at("ask the optimizer"), v.at("five thousand"), v.at("entirely"),
                                              v.at("45 percent"), v.at("Safety factor"), v.at("bends before"))
    o_end = t_ent - 0.15
    o_rate = min(1.6, max(0.8, 7.0 / max(o_end, 1)))
    w_start = t_sf - 1.3
    w_ms = 4.25 - (t_sf + 0.05 - w_start)       # "Design load held" appears ~4.25 s into c06
    body = f"""<div id="s6b-all" class="abs" style="left:0;top:0;width:1920px;height:1080px">
{video('s6b-v1', 'assets/clips/u05_optimizer.mp4', 0, o_end, 0.0, o_rate)}
{clip('s6b-hud', 0, o_end, '<div class="tag" style="left:auto;right:96px"><i></i>Real app · optimizer · wrench</div>')}
{clip('s6b-cnt', t_5k - 0.3, o_end - t_5k + 0.3, readout('s6b-ro0', 'Mixes tested', '<span id="s6b-n">0</span>', 'cyan', 'every binder × process × soil × loading', 'muted', 1180, 640))}
{clip('s6b-rank', o_end - 0.05, w_start - o_end + 0.1, f'''
  <div id="s6b-rk" class="abs" style="left:260px;top:150px;width:1400px;border-radius:14px;overflow:hidden;border:1px solid rgba(127,227,255,.35);box-shadow:0 40px 90px -30px #000">
    <img src="assets/screens/hi_ranked.png" style="width:1400px;display:block" alt="Optimizer ranking: #1 45% lunar highlands + 15% basalt fibre in Bio-PHB">
    <div id="s6b-hl" class="abs" style="left:0;top:0;width:1400px;height:186px;border:4px solid #2fd39b;border-radius:12px;box-shadow:0 0 40px rgba(47,211,155,.6)"></div></div>
  <div id="s6b-local" class="abs chip green" style="left:260px;top:930px;font-size:30px">100% local · 45% dust + 15% basalt fibre</div>''')}
{video('s6b-v2', 'assets/clips/c06_winner.mp4', w_start, D - w_start, max(0.0, w_ms))}
{clip('s6b-hud2', w_start, D - w_start, brackets('s6b') + '<div class="tag"><i></i>Real app footage · the optimizer&#39;s wrench</div>')}
{clip('s6b-r', t_sf - 0.1, D - t_sf + 0.1, readout('s6b-ro1', 'Safety factor · design load held', '1.71×', 'green', '<span id="s6b-bend">bends before it breaks</span>', 'green', 1180, 560))}
</div>"""
    js = f"""
land('#s6b-hud .tag', 0.25);
land('#s6b-ro0', {t_5k - 0.25:.3f}, {{ x: 60, y: 0 }});
count('#s6b-n', 0, 4662, {t_5k - 0.2:.3f}, 1.3, fmtInt);
tl.fromTo('#s6b-rk', {{ opacity: 0, scale: 1.06, filter: 'blur(10px)' }}, {{ opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.5, ease: 'expo.out' }}, {o_end:.3f});
tl.fromTo('#s6b-hl', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {o_end + 0.5:.3f});
land('#s6b-local', {t_45 - 0.2:.3f}, {{ scale: 0.8, y: 0 }});
tl.fromTo('#s6b-v2-wrap', {{ clipPath: 'inset(0% 50% 0% 50%)' }}, {{ clipPath: 'inset(0% 0% 0% 0%)', duration: 0.5, ease: 'power3.out' }}, {w_start:.3f});
tl.fromTo('#s6b-hud2 .brk', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, stagger: 0.05 }}, {w_start + 0.2:.3f});
land('#s6b-hud2 .tag', {w_start + 0.3:.3f});
land('#s6b-ro1', {t_sf:.3f}, {{ x: 60, y: 0 }});
tl.fromTo('#s6b-bend', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {t_bends - 0.1:.3f});
tl.fromTo('#s6b-all', {{ x: 0, filter: 'blur(0px)' }}, {{ x: -160, filter: 'blur(14px)', duration: 0.22, ease: 'power3.in' }}, {D - 0.22:.3f});
"""
    cues = {"pop_cnt": t_5k + 1.0, "whoosh_rank": o_end - 0.1, "pop_local": t_45, "impact_held": t_sf + 0.05, "riser_held": t_sf + 0.05,
            "crack_winner": w_start + (6.6 - max(0.0, w_ms)), "whoosh_out": D - 0.25}
    return scene_file(sid, D, "", body, js), cues


def s6c():
    v, sid = VOICES["s6c"], "s6c"
    D = v.scene
    t_noz, t_no, t_kit, t_10kg, t_10m = (v.at("rocket nozzle"), v.at("honestly says no"), v.at("a kit of 25"),
                                         v.at("10 kilograms"), v.at("10 million"))
    bg, bgjs = stars(sid, D, 0.8)
    thumbs = ["wrench", "bracket", "brick"]
    grid = ""
    for i in range(25):
        r, c = divmod(i, 5)
        grid += (f'<div class="abs s6c-cell" style="left:{192 + c * 132}px;top:{250 + r * 132}px;width:120px;height:120px;'
                 f'border-radius:12px;overflow:hidden;border:1px solid rgba(127,227,255,.35)">'
                 f'<img src="assets/screens/thumb_{thumbs[i % 3]}.jpg" style="width:120px;height:120px;object-fit:cover" alt=""></div>')
    body = f"""
{bg}
<div id="s6c-all" class="abs" style="left:0;top:0;width:1920px;height:1080px">
{clip('s6c-noz', 0, t_kit - 0.05, f'''
  <div class="abs kick" style="left:192px;top:112px">Optimizer · thruster nozzle</div>
  <div id="s6c-nz" class="abs" style="left:340px;top:170px;width:1240px;border-radius:14px;overflow:hidden;border:1px solid rgba(255,107,107,.45)">
    <img src="assets/screens/hi_nozzle.png" style="width:1240px;display:block" alt="Optimizer: no mix survives a thruster nozzle"></div>
  <div id="s6c-stamp" class="abs chip red" style="left:1180px;top:760px;font-size:40px">No mix works</div>''')}
{clip('s6c-imp', t_kit - 0.1, D - t_kit + 0.1, f'''
  <div class="abs kick" style="left:192px;top:180px">25 parts × 0.4 kg, printed on site</div>
  {grid}
  <div class="abs" style="left:1000px;top:250px">
    <div id="s6c-kg" class="h0 cyan">0 kg</div><div class="h3">kept off the launch pad</div></div>
  <div class="abs" style="left:1000px;top:540px">
    <div id="s6c-usd" class="h0 orange" style="font-size:120px">$0</div><div class="h3">at NASA's upper resupply cost</div>
    <div class="src" style="margin-top:12px">Impact tab · $1M per kg · NASA Glenn NTRS 20260007758</div></div>''')}
</div>
<div id="s6c-flood" class="clip abs" data-start="{D - 0.45:.3f}" data-duration="0.45" style="left:0;top:0;width:1920px;height:1080px;background:#000;opacity:0"></div>
"""
    js = f"""{bgjs}
tl.fromTo('#s6c-all', {{ x: 160, filter: 'blur(14px)' }}, {{ x: 0, filter: 'blur(0px)', duration: 0.3, ease: 'expo.out' }}, 0);
land('#s6c-noz .kick', 0.2);
land('#s6c-nz', 0.25, {{ scale: 0.95, y: 0 }});
tl.fromTo('#s6c-stamp', {{ opacity: 0, scale: 1.8, rotation: -5 }}, {{ opacity: 1, scale: 1, rotation: -5, duration: 0.3, ease: 'expo.out' }}, {t_no:.3f});
land('#s6c-imp .kick', {t_kit:.3f});
tl.fromTo('#s6c-imp .s6c-cell', {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.35, stagger: 0.045, ease: 'back.out(1.6)' }}, {t_kit + 0.1:.3f});
count('#s6c-kg', 0, 10, {t_10kg - 0.3:.3f}, 1.0, (v) => fmtInt(v) + ' kg');
land('#s6c-imp .h3', {t_10kg + 0.3:.3f});
count('#s6c-usd', 0, 10000000, {t_10m - 0.3:.3f}, 1.3, (v) => '$' + fmtInt(v));
tl.fromTo('#s6c-flood', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: 'power2.inOut' }}, {D - 0.45:.3f});
"""
    cues = {"pop_stamp": t_no + 0.05, "whoosh_kit": t_kit - 0.1, "pop_kg": t_10kg + 0.7, "pop_usd": t_10m + 1.0}
    return scene_file(sid, D, "", body, js), cues


def team():
    """Team Dreams of X: five equal cards, one per member, and the work they did together."""
    v, sid = VOICES["team"], "team"
    D = v.scene
    t_dox, t_five = v.at("We're Dreams of X"), v.at("five friends")
    t_names = [v.at(n) for n in ("Mahdin", "Maliha", "Lamisa", "Yousuf", "Habibullah")]
    t_we = v.at("We researched")
    bg, bgjs = stars(sid, D, 0.8)
    cards_html = ""
    for i, (img, name, role) in enumerate(TEAM):
        cards_html += f'''<div id="tm-c{i}" class="abs panel" style="left:{122 + i * 340}px;top:290px;width:316px;padding:12px;text-align:center">
          <div style="width:292px;height:292px;border-radius:12px;overflow:hidden"><img src="assets/team/{img}.jpg" style="width:100%;height:100%;object-fit:cover;object-position:50% 25%" alt="{name}"></div>
          <div class="h3" style="font-size:29px;line-height:1.15;margin-top:14px;height:68px;display:flex;align-items:center;justify-content:center">{name}</div>
          <div class="src" style="color:#7fe3ff;line-height:1.35;margin-top:6px;height:84px">{role}</div></div>'''
    verbs = ["Researched", "Designed", "Built", "Tested"]
    verbs_html = "".join(f'<div class="chip tm-v" style="font-size:28px">{w}</div>' for w in verbs)
    body = f"""
{bg}
<div id="tm-head" class="abs" style="left:122px;top:110px;display:flex;align-items:center;gap:22px">
  <div id="tm-logo" style="width:84px;height:84px;border-radius:18px;overflow:hidden;background:#fff"><img src="assets/brand/dreams-of-x-logo.jpeg" style="width:100%;height:100%;object-fit:contain" alt="Dreams of X logo"></div>
  <div><div id="tm-title" class="h2">Team <span class="cyan">Dreams of X</span></div>
  <div id="tm-sub" class="body" style="margin-top:4px">Five friends, <span class="orange">one team.</span></div></div></div>
{cards_html}
<div id="tm-verbs" class="abs" style="left:122px;top:840px;width:1676px;display:flex;gap:18px;align-items:center;justify-content:center">
  {verbs_html}<div id="tm-tog" class="h3" style="font-size:34px;margin-left:8px">together.</div></div>
"""
    js = f"""{bgjs}
land('#tm-logo', {max(0.1, t_dox - 0.2):.3f}, {{ scale: 0.6, y: 0 }});
land('#tm-title', {max(0.2, t_dox - 0.1):.3f});
land('#tm-sub', {t_five - 0.1:.3f});
""" + "".join(f"land('#tm-c{i}', {t - 0.15:.3f}, {{ y: 50 }});\n" for i, t in enumerate(t_names)) + f"""
tl.fromTo('#tm-verbs .tm-v', {{ opacity: 0, y: 24, scale: 0.9 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.4, stagger: 0.16, ease: 'back.out(1.7)' }}, {t_we - 0.05:.3f});
land('#tm-tog', {t_we + 0.75:.3f});
"""
    cues = {f"pop_c{i}": t for i, t in enumerate(t_names)}
    cues["sparkle_tog"] = t_we + 0.8
    return scene_file(sid, D, "", body, js), cues


def s7():
    """Close: what the simulator is for. Engineers get a fast 3D test reel, learners a tour of the site, then Mars and the end card."""
    v, sid = VOICES["s7"], "s7"
    D = v.scene
    t_now, t_learn, t_mars, t_try = v.at("Now our simulator"), v.at("And it's for"), v.at("The same method"), v.at("Try it yourself")
    t_stu, t_tea, t_rock = v.at("students"), v.at("teachers"), v.at("rockets")
    t_nasa, t_meas = v.at("explore NASA's"), v.at("measurement")
    bg, bgjs = stars(sid, D)
    end_at = t_try - 0.35
    # The 3D reel: three shots, hard cuts with a flash. Breaks: bracket and brick both snap 6.25 s into their clips.
    b0 = t_now - 0.15
    b1 = b0 + 1.45
    b2 = b1 + 1.5
    b3 = t_learn - 0.1
    brk1, brk2 = b1 + 1.0, b2 + 0.75
    shots = [("s7-r0", "assets/clips/c02_sample_orbit.mp4", b0, b1, 0.5, "3D dust sample"),
             ("s7-r1", "assets/clips/c11_bracket.mp4", b1, b2, 6.25 - 1.0, "Shelf bracket test"),
             ("s7-r2", "assets/clips/c12_brick.mp4", b2, b3, 6.25 - 0.75, "Brick crush test")]
    reel = ""
    for cid, src, s0, s1, ms, label in shots:
        reel += (f"""
    <div id="{cid}-card" class="abs" style="opacity:0;left:0;top:0;width:1200px;height:675px;border-radius:18px;overflow:hidden;border:1px solid rgba(127,227,255,.45);box-shadow:0 30px 90px -20px rgba(0,0,0,.9),0 0 60px -12px rgba(127,227,255,.5)">
      {video(cid + '-v', src, s0, s1 - s0, ms)}
      <div class="abs chip cyan" style="left:24px;bottom:24px;font-size:28px;background:rgba(5,12,24,.85)">{label}</div></div>""")
    rate = min(1.4, 11.4 / max(t_mars - 0.15 - (t_learn - 0.1), 1.0))
    t_end_c = t_mars - 0.15
    body = f"""
{bg}
<div id="s7-moonwrap" class="abs" style="left:880px;top:40px;width:1000px;height:1000px;-webkit-mask-image:radial-gradient(circle closest-side, #000 98.5%, transparent 100%);mask-image:radial-gradient(circle closest-side, #000 98.5%, transparent 100%)">
<video id="s7-moon" class="clip" src="assets/clips/moon_spin.mp4" muted playsinline data-start="0" data-duration="{t_now:.3f}" data-media-start="0" style="width:1000px;height:1000px"></video></div>
{clip('s7-a', 0.0, b0, """
  <div class="abs" style="left:192px;top:330px;width:760px">
    <div id="s7-l1" class="h1">The machines we <span class="cyan">left behind</span></div>
    <div id="s7-l2" class="h1" style="margin-top:6px">teach us how to <span class="orange">build next.</span></div></div>""")}
<div id="s7-in" class="clip abs" data-start="0" data-duration="0.6" style="left:0;top:0;width:1920px;height:1080px;background:#000"></div>
<div class="abs" style="left:360px;top:240px;width:1200px;height:675px;perspective:1700px">{reel}</div>
{clip('s7-reel', b0, b3 - b0, f"""
  <div id="s7-rk" class="abs" style="left:150px;top:86px"><div class="kick">For engineers</div>
    <div class="h3" style="font-size:40px;margin-top:6px">Break it in 3D <span class="orange">before you print it.</span></div></div>
  <div id="s7-fl" class="abs" style="left:0;top:0;width:1920px;height:1080px;background:radial-gradient(circle at 50% 55%, rgba(220,250,255,.9), rgba(127,227,255,.35) 45%, transparent 75%);opacity:0"></div>""")}
<div class="abs" style="left:110px;top:150px;width:1120px;height:676px;perspective:1800px">
    <div id="s7-br" class="abs panel" style="opacity:0;left:0;top:0;width:1120px;height:676px;padding:0;overflow:hidden;border-color:rgba(127,227,255,.5);box-shadow:0 30px 90px -20px rgba(0,0,0,.9),0 0 70px -14px rgba(127,227,255,.45)">
      <div style="height:46px;display:flex;align-items:center;gap:10px;padding:0 18px;background:rgba(14,26,44,.95);border-bottom:1px solid rgba(127,227,255,.25)">
        <span style="width:13px;height:13px;border-radius:50%;background:#ff6b6b"></span><span style="width:13px;height:13px;border-radius:50%;background:#ffc861"></span><span style="width:13px;height:13px;border-radius:50%;background:#62d68b"></span>
        <span class="mono" data-layout-ignore style="margin-left:16px;font-size:19px;color:#cfe0ff">md8-habibullah.github.io/moon-material-simulator</span></div>
      <div style="position:relative;width:1120px;height:630px;overflow:hidden">
        {video('s7-scroll', 'assets/clips/c30_scroll.mp4', b3, t_end_c - b3, 0.0, rate, 'width:1120px;height:630px')}</div></div></div>
{clip('s7-learn', b3, t_end_c - b3, f"""
  <div class="abs" style="left:1290px;top:170px;width:540px">
    <div id="s7-lk" class="kick">Made for learning</div>
    <div id="s7-lh" class="h2" style="font-size:54px;margin-top:8px">Curious about <span class="cyan">space?</span></div>
    <div style="display:flex;flex-direction:column;align-items:flex-start;gap:16px;margin-top:30px">
      <div id="s7-who0" class="chip cyan" style="font-size:30px">Students</div>
      <div id="s7-who1" class="chip cyan" style="font-size:30px">Teachers</div>
      <div id="s7-who2" class="chip orange" style="font-size:30px">Rocket &amp; space fans</div></div>
    <div id="s7-l3" class="body" style="margin-top:34px">Explore <span class="cyan">NASA's real data</span>,</div>
    <div id="s7-l4" class="body" style="margin-top:6px">and the measurement behind every answer.</div></div>""")}
{video('s7-mv', 'assets/clips/c20_stories_mars.mp4', t_end_c, end_at - t_end_c, 1.5)}
{clip('s7-mars', t_end_c, end_at - t_end_c, f"""
  <div class="abs" style="left:0;top:0;width:1920px;height:1080px;background:linear-gradient(90deg, rgba(3,7,15,.92) 0%, rgba(3,7,15,.55) 45%, transparent 75%)"></div>
  <div id="s7-mt" class="abs" style="left:192px;top:420px;width:900px"><div class="kick">Next stop</div>
    <div class="h1" style="margin-top:8px">Same method works for <span class="orange">Mars.</span></div></div>""")}
{clip('s7-end', end_at, D - end_at, f"""
  <div class="abs" style="left:192px;top:130px;width:980px">
    <div id="s7-logo" style="width:120px;height:120px;border-radius:22px;overflow:hidden;background:#fff;margin-bottom:28px">
      <img src="assets/brand/dreams-of-x-logo.jpeg" style="width:100%;height:100%;object-fit:contain" alt="Dreams of X"></div>
    <div class="h1" style="font-size:88px">Moon-Material<br>Simulator</div>
    <div id="s7-aud" class="body" style="margin-top:14px;font-size:30px">For engineers, students, teachers and <span class="orange">anyone who loves space.</span></div>
    <div class="body" style="margin-top:18px">Try it yourself:</div>
    <div class="h3 cyan mono" style="font-size:30px;margin-top:8px;white-space:nowrap">md8-habibullah.github.io/moon-material-simulator</div>
    <div class="src" style="margin-top:14px">github.com/md8-habibullah/moon-material-simulator</div>
    <div style="display:flex;gap:26px;align-items:center;margin-top:26px">
      <img id="s7-qr" src="assets/brand/qr_live_app.png" style="width:180px;height:180px;border-radius:12px" alt="QR code to the live app">
      <div class="src" data-layout-ignore style="width:620px;font-size:21px;line-height:1.5">Images: NASA (Glenn, LRO / SVS).<br>Data: NASA NTRS reports and peer-reviewed studies (CC BY 4.0).<br>Open source.</div></div></div>
  <div class="abs" style="left:1220px;top:200px">
    <div class="kick" style="margin-bottom:26px">Team Dreams of X</div>{"".join(f'<div class="s7-m" style="margin-bottom:22px"><div class="h3" style="font-size:38px">{n}</div><div class="src" style="color:#7fe3ff">{r}</div></div>' for _, n, r in TEAM)}</div>""")}
"""
    js = f"""{bgjs}
tl.fromTo('#s7-in', {{ opacity: 1 }}, {{ opacity: 0, duration: 0.5, ease: 'power2.out' }}, 0);
tl.fromTo('#s7-moonwrap', {{ scale: 0.92, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 1.4, ease: 'expo.out' }}, 0);
tl.to('#s7-moonwrap', {{ x: 200, opacity: 0, duration: 0.45, ease: 'power3.in' }}, {b0 - 0.45:.3f});
tl.to('#s7-a', {{ opacity: 0, x: -60, duration: 0.4, ease: 'power3.in' }}, {b0 - 0.4:.3f});
land('#s7-l1', 0.4);
land('#s7-l2', 1.1);
land('#s7-rk', {b0 + 0.05:.3f}, {{ x: -40, y: 0 }});
tl.fromTo('#s7-r0-card', {{ rotationY: -32, rotationX: 10, scale: 0.86 }}, {{ rotationY: -8, rotationX: 4, scale: 1, duration: {b1 - b0:.3f}, ease: 'power2.out' }}, {b0:.3f});
tl.fromTo('#s7-r1-card', {{ rotationY: 26, rotationX: -6, scale: 0.9 }}, {{ rotationY: 8, rotationX: 0, scale: 1, duration: {brk1 - b1:.3f}, ease: 'power2.out' }}, {b1:.3f});
tl.to('#s7-r1-card', {{ scale: 1.14, duration: {b2 - brk1:.3f}, ease: 'expo.out' }}, {brk1:.3f});
tl.fromTo('#s7-r2-card', {{ rotationX: 22, rotationY: -14, scale: 0.9 }}, {{ rotationX: 4, rotationY: 0, scale: 1, duration: {brk2 - b2:.3f}, ease: 'power2.out' }}, {b2:.3f});
tl.to('#s7-r2-card', {{ scale: 1.12, duration: {b3 - brk2:.3f}, ease: 'expo.out' }}, {brk2:.3f});
""" + "".join(f"tl.set('#s7-fl', {{ opacity: 0.75 }}, {t:.3f});\ntl.to('#s7-fl', {{ opacity: 0, duration: 0.22, ease: 'power2.out' }}, {t + 0.001:.3f});\n" for t in (b1, b2, brk1, brk2)) + \
        "".join(f"tl.set('#{c}-card', {{ opacity: 1 }}, {s0:.3f});\ntl.set('#{c}-card', {{ opacity: 0 }}, {s1:.3f});\n" for c, _, s0, s1, _, _ in shots) + "".join(
        f"tl.fromTo('#{c}', {{ x: -14 }}, {{ x: 0, duration: 0.3, ease: 'elastic.out(1.2, 0.3)' }}, {t:.3f});\n" for c, t in (("s7-r1-card", brk1), ("s7-r2-card", brk2))) + f"""
tl.fromTo('#s7-br', {{ rotationY: 22, rotationX: 6, opacity: 0, x: -80 }}, {{ rotationY: 7, rotationX: 2, opacity: 1, x: 0, duration: 0.7, ease: 'expo.out' }}, {b3:.3f});
tl.to('#s7-br', {{ rotationY: 2, duration: {t_end_c - b3 - 0.7:.3f}, ease: 'none' }}, {b3 + 0.7:.3f});
land('#s7-lk', {b3 + 0.15:.3f});
land('#s7-lh', {b3 + 0.35:.3f});
""" + "".join(f"tl.fromTo('#s7-who{i}', {{ opacity: 0, x: 50, scale: 0.85 }}, {{ opacity: 1, x: 0, scale: 1, duration: 0.4, ease: 'back.out(1.8)' }}, {t - 0.1:.3f});\n"
                for i, t in enumerate((t_stu, t_tea, t_rock))) + f"""
land('#s7-l3', {t_nasa - 0.1:.3f});
land('#s7-l4', {t_meas - 0.1:.3f});
tl.set('#s7-br', {{ opacity: 0 }}, {t_end_c:.3f});
land('#s7-mt', {t_end_c + 0.1:.3f}, {{ x: -50, y: 0 }});
land('#s7-logo', {end_at + 0.1:.3f}, {{ scale: 0.6, y: 0 }});
tl.fromTo('#s7-end .h1', {{ opacity: 0, filter: 'blur(10px)' }}, {{ opacity: 1, filter: 'blur(0px)', duration: 0.5, ease: 'expo.out' }}, {end_at + 0.25:.3f});
land('#s7-aud', {end_at + 0.45:.3f});
tl.fromTo('#s7-end .s7-m', {{ opacity: 0, x: 40 }}, {{ opacity: 1, x: 0, duration: 0.5, stagger: 0.12, ease: 'expo.out' }}, {end_at + 0.3:.3f});
land('#s7-end .body:not(#s7-aud)', {t_try - 0.1:.3f});
land('#s7-end .h3.cyan', {t_try + 0.1:.3f});
land('#s7-end .src', {t_try + 0.4:.3f});
land('#s7-qr', {t_try + 0.6:.3f}, {{ scale: 0.7, y: 0 }});
"""
    cues = {"glitch_in": b0, "glitch_c1": b1, "glitch_c2": b2, "crack_br": brk1, "bass_br": brk1, "crack_bk": brk2, "bass_bk": brk2,
            "whoosh_learn": b3 - 0.1, "ping_stu": t_stu, "ping_tea": t_tea, "ping_rock": t_rock, "pop_nasa": t_nasa,
            "gtex_mars": t_end_c, "impact_end": end_at + 0.25, "sparkle_qr": t_try + 0.6}
    css = ("#s7-r0-v, #s7-r1-v, #s7-r2-v { width: 1200px; height: 675px; }\n"
           "#s7-scroll { width: 1120px; height: 630px; }\n")
    return scene_file(sid, D, css, body, js), cues


BUILDERS = {"r1": r1, "r2": r2, "team": team, "s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5, "s6a": s6a, "s6b": s6b, "s6c": s6c, "s7": s7}


# ---------------------------------------------------------------- HUD and captions -------------------

def hud():
    chapters = ""
    for i, (sid, num, label) in enumerate(CHAPTERS):
        start = STARTS[sid]
        end = STARTS[CHAPTERS[i + 1][0]] if i + 1 < len(CHAPTERS) else TOTAL
        chapters += (f'<div id="hud-c{num}" class="clip hud-ch" data-start="{start:.3f}" data-duration="{end - start:.3f}">'
                     f'<span class="cyan">{num}</span> · {label}</div>')
    css = """
.hud-band { position: absolute; left: 0; top: 0; width: 1920px; height: 104px; background: linear-gradient(180deg, rgba(2,4,10,.92), rgba(2,4,10,.55) 70%, rgba(2,4,10,0)); }
.hud-top { position: absolute; left: 96px; right: 96px; top: 40px; height: 34px; display: flex; justify-content: space-between;
  font-family: 'JetBrains Mono', monospace; font-size: 28px; letter-spacing: .12em; text-transform: uppercase; color: rgba(231,237,247,.62); }
.hud-ch { position: absolute; right: 300px; top: 40px; font-family: 'JetBrains Mono', monospace; font-size: 28px; letter-spacing: .14em;
  text-transform: uppercase; color: rgba(231,237,247,.75); }
#root { background: transparent; }
"""
    body = f"""
<div class="hud-band"></div>
<div class="hud-top"><span>Dreams of X // Moon-Material Simulator</span><span id="hud-t" class="mono">T+00:00</span></div>
{chapters}
"""
    js = f"""
const clock = {{ t: 0 }};
tl.fromTo(clock, {{ t: 0 }}, {{ t: {TOTAL:.3f}, duration: {TOTAL:.3f}, ease: 'none', onUpdate: () => {{
  const s = Math.floor(clock.t), el = q('#hud-t');
  if (el) el.textContent = 'T+' + String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }} }}, 0);
"""
    return scene_file("hud", TOTAL, css, body, js)


def captions():
    # Spoken numbers read better as digits on screen.
    display = {("three", "hundred", "and", "eightyfour", "thousand"): "384,000"}
    groups = []
    for sid in ORDER:
        v = VOICES[sid]
        if not v.real:
            continue
        ws, i = [], 0
        while i < len(v.words):
            for key, shown in display.items():
                seg = v.words[i:i + len(key)]
                if tuple(norm(w["text"]) for w in seg) == key:
                    ws.append({"text": shown, "start": seg[0]["start"], "end": seg[-1]["end"]})
                    i += len(key)
                    break
            else:
                ws.append(v.words[i])
                i += 1
        cur = []
        for w in ws:
            cur.append(w)
            end_sentence = w["text"].rstrip().endswith((".", "?", "!", ":", ";", ","))
            if len(cur) >= 5 or (end_sentence and len(cur) >= 2):
                groups.append((sid, cur)); cur = []
        if cur:
            groups.append((sid, cur))
    if not groups:
        return None
    css = """
#root { background: transparent; }
.cap { position: absolute; left: 0; width: 1920px; top: 958px; text-align: center; }
.cap span.box { display: inline-block; padding: 8px 22px 10px; border-radius: 12px; background: rgba(0,0,0,.42);
  font-family: 'Space Grotesk', 'Inter', sans-serif; font-weight: 600; font-size: 44px; color: #f4f7fb; letter-spacing: -.005em; }
"""
    body, js = "", ""
    for i, (sid, ws) in enumerate(groups):
        base = STARTS[sid] + LEAD
        start = base + ws[0]["start"] - 0.05
        end = base + ws[-1]["end"] + 0.12
        if i + 1 < len(groups):
            nsid, nws = groups[i + 1]
            end = min(end, STARTS[nsid] + LEAD + nws[0]["start"] - 0.06)
        text = " ".join(w["text"] for w in ws)
        body += f'<div id="cap{i}" class="clip cap" data-start="{start:.3f}" data-duration="{max(end - start, 0.3):.3f}"><span class="box">{text}</span></div>\n'
    return scene_file("captions", TOTAL, css, body, js)


# ---------------------------------------------------------------- sound ------------------------------

def sound_tags(all_cues):
    """Music bed, voice per scene, and effects placed on their visible causes."""
    tags = []
    music = ROOT / "assets" / "audio" / "music.mp3"
    if music.exists():
        tags.append(f'<audio id="music" class="clip" src="assets/audio/music.mp3" data-start="0" data-duration="{TOTAL:.3f}" data-volume="0.12" data-fade-in="1.5" data-fade-out="3"></audio>')
    for sid in ORDER:
        wav = ROOT / "assets" / "voice" / f"{sid}.wav"
        if wav.exists():
            tags.append(f'<audio id="vo-{sid}" class="clip" src="assets/voice/{sid}.wav" data-start="{STARTS[sid] + LEAD:.3f}" data-duration="{VOICES[sid].duration:.3f}" data-volume="1"></audio>')
    sfx_dir = ROOT / "assets" / "sfx"
    takes = {}
    for f in sorted(sfx_dir.glob("*.mp3")) + sorted(sfx_dir.glob("*.wav")):
        takes.setdefault(f.stem.split("_")[0], []).append(f)
    gains = {"crack": 0.75, "whoosh": 0.22, "pop": 0.2, "impact": 0.6, "click": 0.25, "riser": 0.3,
             "glitch": 0.32, "gtex": 0.22, "ping": 0.22, "bass": 0.5, "sparkle": 0.25}
    # Where each file hits (seconds into it); the hit lands one frame after its picture.
    peaks = {"crack_a": 0.55, "crack_b": 1.95, "impact_a": 2.06, "pop_a": 0.12, "pop_b": 0.33,
             "whoosh_a": 0.16, "whoosh_b": 0.29, "riser_a": 9.95,
             "glitch_a": 0.48, "gtex_a": 0.293, "ping_a": 0.323, "bass_a": 0.052, "sparkle_a": 0.025}
    used = {}
    n = 0
    for sid, cues in all_cues.items():
        for name, at in cues.items():
            kind = name.split("_")[0]
            if kind not in takes:
                continue
            k = used.get(kind, 0); used[kind] = k + 1
            f = takes[kind][k % len(takes[kind])]
            start = STARTS[sid] + at - peaks.get(f.stem, 0.0) + 1 / FPS
            if start < 0:
                continue
            tags.append(f'<audio id="sfx{n}" class="clip" src="assets/sfx/{f.name}" data-start="{start:.3f}" data-volume="{gains.get(kind, 0.5)}"></audio>')
            n += 1
    return tags


# ---------------------------------------------------------------- write ------------------------------

def main():
    comp = ROOT / "compositions"
    comp.mkdir(exist_ok=True)
    all_cues = {}
    for sid in ORDER:
        html, cues = BUILDERS[sid]()
        (comp / f"{sid}.html").write_text(html)
        all_cues[sid] = cues
    # A low digital glitch as each chapter label changes (not on the first frame of the film).
    for sid, _, _ in CHAPTERS[1:]:
        all_cues[sid]["gtex_chapter"] = 0.05
    (comp / "hud.html").write_text(hud())
    cap = captions()
    if cap:
        (comp / "captions.html").write_text(cap)
    elif (comp / "captions.html").exists():
        (comp / "captions.html").unlink()

    hosts = []
    for i, sid in enumerate(ORDER):
        hosts.append(f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{STARTS[sid]:.3f}" data-duration="{VOICES[sid].scene:.3f}" data-track-index="1" '
                     f'data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:1"></div>')
    hosts.append(f'<div id="hud" data-composition-id="hud" data-composition-src="compositions/hud.html" data-start="0" '
                 f'data-duration="{TOTAL:.3f}" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:5"></div>')
    if cap:
        hosts.append(f'<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" '
                     f'data-duration="{TOTAL:.3f}" data-track-index="3" data-track-kind="captions" data-width="1920" data-height="1080" style="z-index:6"></div>')
    audio = sound_tags(all_cues)
    variables = json.dumps([{"id": "challenge", "type": "string", "label": "Challenge name",
                             "default": "NASA Space Apps 2026 · Abandoned but not Forgotten"}])
    index = f"""<!doctype html>
<html lang="en" data-composition-variables='{variables}'>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Moon-Material Simulator · 240 Seconds of Glory</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #02040a; }}
      #main {{ position: absolute; inset: 0; background: #02040a; }}
    </style>
  </head>
  <body>
    <div id="main" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1920" data-height="1080">
      {chr(10).join('      ' + h for h in hosts)}
      {chr(10).join('      ' + a for a in audio)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
    (ROOT / "index.html").write_text(index)
    (ROOT / "tools" / "timing.json").write_text(json.dumps({"total": TOTAL, "starts": STARTS,
        "scenes": {s: round(VOICES[s].scene, 3) for s in ORDER}, "voice": {s: VOICES[s].real for s in ORDER},
        "cues": all_cues}, indent=1))
    print(f"total {TOTAL:.2f} s  ({'voice' if all(VOICES[s].real for s in ORDER) else 'estimated timing'})")
    for s in ORDER:
        print(f"  {s:4} start {STARTS[s]:7.2f}  len {VOICES[s].scene:6.2f}")


if __name__ == "__main__":
    main()
