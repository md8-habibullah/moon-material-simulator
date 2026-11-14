"""Build the 30-second Project Demo: writes demo30.html and compositions/d30*.html.

Space Apps 2026 rule: the Project Demo is a video of 30 seconds or less (or 7 slides at most), in
English, showing the team, the challenge and the project. The 4-minute film stays the full story.

Run from video/film, after tools/voice_human30.py (or tools/voice_demo30.py for the AI voice):
    python3 tools/build_demo30.py
    npx --yes hyperframes@0.9.39 render -c demo30.html -o renders/moon-material-simulator_demo30.mp4

Reuses the film's styles, helpers and assets (tools/build.py); the voice take is the clock.
"""
import json
import os
import subprocess
from pathlib import Path

from build import BASE_CSS, JS_HELPERS, TEAM, brackets, scene_file, stars, video, wspan, FPS

ROOT = Path(__file__).resolve().parent.parent
# Narration: "clone" = Habibullah's voice cloned with F5-TTS (tools/clone_voice30.py), "human" = his own recording
# (tools/voice_human30.py), "ai" = the ElevenLabs take (tools/voice_demo30.py). The first that exists is used;
# override with D30_VOICE=clone|human|ai.
VOICES = {"clone": ("d30_clone", "Narration: AI voice cloned from Md. Habibullah Sharif's own voice (F5-TTS)"),
          "human": ("d30_human", "Narration: Md. Habibullah Sharif (Dreams of X)"),
          "ai": ("d30", "Narration: AI-generated voice (ElevenLabs)")}
VOICE = os.environ.get("D30_VOICE") or next(v for v in ("clone", "human", "ai")
                                            if (ROOT / "assets" / "voice" / f"{VOICES[v][0]}.wav").exists())
VO_FILE, CREDIT = VOICES[VOICE]
WORDS = json.loads((ROOT / "assets" / "voice" / f"{VO_FILE}.asr.json").read_text())
VO_AT = 0.35 if VOICE in ("human", "clone") else 0.60   # the first word starts here (the human read is longer)
TOTAL = 29.50           # under the 30-second limit, with margin
VO_LEN = round(float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                              str(ROOT / "assets" / "voice" / f"{VO_FILE}.wav")]).decode()), 3)
URL = "md8-habibullah.github.io/moon-material-simulator"


def _hits(word):
    key = word.lower()
    return [w for w in WORDS if w["text"].lower().strip(".,:;!?'") in (key, key + "'s")]


def at(word, n=1):
    """Film time at which the n-th occurrence of `word` (exact, case-insensitive) begins."""
    return round(VO_AT + _hits(word)[n - 1]["start"], 3)


def end_of(word, n=1):
    return round(VO_AT + _hits(word)[n - 1]["end"], 3)


# Scene boundaries: each cut lands just before the sentence it illustrates.
CUTS = [0.0, at("Abandoned") - 0.4, at("The", 2) - 0.2, at("Our") - 0.2, at("Rebuild") - 0.2, at("Next") - 0.2, TOTAL]
IDS = ["d30a", "d30b", "d30c", "d30d", "d30e", "d30f"]
START = dict(zip(IDS, CUTS))
DUR = {sid: round(CUTS[i + 1] - CUTS[i], 3) for i, sid in enumerate(IDS)}


def local(t, sid):
    return round(t - START[sid], 3)


# ---------------------------------------------------------------- scenes ----------------------------

def team_names(cls="h3", size=34, gap=40):
    names = "".join(f'<span class="{cls}" style="font-size:{size}px;white-space:nowrap">{name}</span>' for _, name, _ in TEAM)
    return f'<div style="display:flex;gap:14px {gap}px;flex-wrap:wrap;justify-content:center">{names}</div>'


def d30a():
    sid, D = "d30a", DUR["d30a"]
    bg, bg_js = stars(sid, D, 0.85)
    body = f"""{bg}
{brackets(sid)}
<div id="a-kick" class="abs kick" style="left:0;width:1920px;top:250px;text-align:center">NASA Space Apps Challenge 2026 · Dhaka</div>
<div id="a-head" class="abs" style="left:0;width:1920px;top:330px;display:flex;justify-content:center;align-items:center;gap:30px">
  <div style="width:120px;height:120px;border-radius:24px;overflow:hidden;background:#fff"><img src="assets/brand/dreams-of-x-logo.jpeg" style="width:100%;height:100%;object-fit:contain" alt="Dreams of X logo"></div>
  <div class="h1">Team <span class="cyan">Dreams of X</span></div></div>
<div id="a-names" class="abs" style="left:160px;width:1600px;top:560px">{team_names()}</div>
"""
    js = f"""{bg_js}
land('#a-kick', 0.05);
land('#a-head', 0.15, {{ scale: 0.92, y: 0 }});
tl.fromTo('#a-names .h3', {{ opacity: 0, y: 18 }}, {{ opacity: 1, y: 0, duration: 0.35, stagger: 0.08, ease: 'expo.out' }}, 0.45);
"""
    return scene_file(sid, D, "", body, js), {"impact_logo": 0.2}


def d30b():
    sid, D = "d30b", DUR["d30b"]
    t_ab, t_title = local(at("Abandoned"), sid), local(at("Moon-Material"), sid)
    bg, bg_js = stars(sid, D, 0.7)
    body = f"""{bg}
<div id="b-moon" class="abs" style="left:1040px;top:120px;width:840px;height:840px;border-radius:50%;overflow:hidden">
  <video id="b-moon-v" class="clip" src="assets/clips/moon_spin.mp4" muted playsinline data-start="0" data-duration="{D:.3f}" data-media-start="0"
    style="position:absolute;inset:0;width:840px;height:840px;object-fit:cover"></video></div>
<div id="b-chip" class="abs" style="left:150px;top:250px"><span class="chip cyan">Our challenge</span></div>
<div id="b-chal" class="abs h2" style="left:150px;top:330px;width:900px">{wspan("Abandoned but not Forgotten")}</div>
<div id="b-built" class="abs kick" style="left:150px;top:560px;color:#8f9cb2">So we built</div>
<div id="b-title" class="abs h1 cyan" style="left:150px;top:610px;width:960px">Moon-Material Simulator</div>
<div id="b-src" class="abs src" style="left:1040px;top:64px;width:840px;text-align:center">Moon map: NASA SVS CGI Moon Kit</div>
"""
    js = f"""{bg_js}
tl.fromTo('#b-moon', {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.9, ease: 'expo.out' }}, 0.05);
land('#b-chip', 0.1);
words('#b-chal', {max(t_ab - 0.15, 0.2):.3f}, 0.09);
land('#b-built', {t_title - 0.45:.3f});
land('#b-title', {t_title - 0.1:.3f}, {{ scale: 0.94, y: 0 }});
tl.fromTo('#b-src', {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.4 }}, 0.6);
"""
    return scene_file(sid, D, "", body, js), {"whoosh_in": 0.0, "pop_chal": t_ab, "impact_title": t_title}


RELICS = [("surveyor3", "Surveyor 3", "Moon · 1967", "AS12-48-7134"),
          ("apollo15-rover", "Apollo 15 rover", "Moon · 1971", "AS15-86-11603"),
          ("apollo17-fender", "Apollo 17 rover fender", "Moon · 1972", "AS17-137-20979")]


def d30c():
    sid, D = "d30c", DUR["d30c"]
    t_mach, t_mat = local(at("machines"), sid), local(at("materials"), sid)
    bg, bg_js = stars(sid, D, 0.6)
    cards = ""
    for i, (img, name, where, cred) in enumerate(RELICS):
        x = 150 + i * 560
        cards += (f'<div id="c-r{i}" class="abs panel" style="left:{x}px;top:300px;width:500px;padding:12px">'
                  f'<div style="width:476px;height:360px;border-radius:12px;overflow:hidden"><img src="assets/relics/{img}.jpg" '
                  f'style="width:100%;height:100%;object-fit:cover" alt="{name}, photo NASA {cred}"></div>'
                  f'<div class="h3" style="font-size:34px;margin-top:14px">{name}</div>'
                  f'<div class="src" style="margin-top:4px">{where.split(" · ")[1]} · NASA {cred}</div></div>')
    body = f"""{bg}
<div id="c-kick" class="abs kick" style="left:150px;top:170px">Left behind, still teaching</div>
{cards}
<div id="c-note" class="abs h3" style="left:150px;top:820px;width:1620px">What the Moon does to <span class="orange">materials</span>.</div>
"""
    js = f"""{bg_js}
land('#c-kick', 0.05);
tl.fromTo('#c-r0, #c-r1, #c-r2', {{ opacity: 0, y: 40, filter: 'blur(6px)' }}, {{ opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.5, stagger: 0.28, ease: 'expo.out' }}, {max(t_mach - 0.3, 0.1):.3f});
land('#c-note', {t_mach + 0.2:.3f});
"""
    return scene_file(sid, D, "", body, js), {"whoosh_in": 0.0, "pop_r0": t_mach - 0.3, "pop_r2": t_mach + 0.26}


def d30d():
    sid, D = "d30d", DUR["d30d"]
    t_glenn = local(at("NASA", 2), sid)
    body = f"""{video('d-v', 'assets/clips/u03_design.mp4', 0, D, 0.6)}
<div class="abs" style="left:0;top:0;width:1920px;height:220px;background:linear-gradient(180deg,rgba(2,4,10,.85),rgba(2,4,10,0))"></div>
<div class="tag"><i></i>Live app · free · in the browser</div>
<div id="d-c1" class="readout" style="left:96px;top:620px;max-width:820px">
  <div class="lbl">Material</div><div class="h3" style="margin-top:8px">NASA Glenn's bioplastic <span class="orange">+ Moon dust</span></div></div>
<div id="d-c2" class="readout" style="left:1000px;top:620px;max-width:820px">
  <div class="lbl">Trained on</div><div class="h3" style="margin-top:8px"><span class="cyan">1,470</span> lab values · <span class="green">0</span> transcription errors</div></div>
"""
    js = f"""
tl.fromTo('#d-v-wrap', {{ scale: 1.0 }}, {{ scale: 1.06, duration: {D:.3f}, ease: 'none' }}, 0);
land('#d-c1', {t_glenn - 0.1:.3f});
land('#d-c2', {t_glenn + 1.7:.3f});
"""
    return scene_file(sid, D, "", body, js), {"whoosh_in": 0.0, "pop_c1": t_glenn, "pop_c2": t_glenn + 1.7}


def d30e():
    sid, D = "d30e", DUR["d30e"]
    t_test, t_see = local(at("test"), sid), local(at("see"), sid)
    snap_media = 7.1                          # the wrench snaps 7.1 s into c01
    ms = snap_media - (t_test + 0.75)         # snap lands on "3D"
    cut = round(t_see - 0.3, 3)
    body = f"""{video('e-v', 'assets/clips/c01_wrench_break.mp4', 0, cut + 0.05, ms)}
<div class="tag"><i></i>Part test · 3D</div>
<div id="e-ev" class="clip grp" data-start="{cut:.3f}" data-duration="{D - cut:.3f}" style="background:#02040a">
  <div class="abs kick" style="left:150px;top:200px">Every number links to its page</div>
  <div class="abs h2" style="left:150px;top:260px;width:820px">See the <span class="green">evidence</span> behind it.</div>
  <div id="e-shot" class="abs" style="left:1060px;top:150px;width:700px;height:800px;overflow:hidden;border-radius:14px">
    <img class="shot" src="assets/screens/hi_evidence_119.png" style="width:700px" alt="Evidence drawer in the app showing the paper's figure"></div>
</div>
"""
    js = f"""
tl.fromTo('#e-v-wrap', {{ scale: 1.0 }}, {{ scale: 1.08, duration: {cut:.3f}, ease: 'none' }}, 0);
tl.fromTo('#e-shot img', {{ y: 0 }}, {{ y: -60, duration: {D - cut:.3f}, ease: 'none' }}, {cut:.3f});
land('#e-shot', {cut + 0.05:.3f}, {{ x: 60, y: 0 }});
"""
    return scene_file(sid, D, "", body, js), {"whoosh_in": 0.0, "crack": t_test + 0.75, "whoosh_ev": cut}


def d30f():
    sid, D = "d30f", DUR["d30f"]
    t_mars = local(at("Mars"), sid)
    body = f"""{video('f-v', 'assets/clips/c20_stories_mars.mp4', 0, D, 0.5)}
<div class="abs" style="inset:0;background:linear-gradient(180deg,rgba(2,4,10,.62) 0%,rgba(2,4,10,.8) 30%,rgba(2,4,10,.96) 48%)"></div>
<div id="f-next" class="abs h0" style="left:0;width:1920px;top:200px;text-align:center">Next stop: <span class="orange">Mars.</span></div>
<div id="f-card" class="abs panel" style="background:#08101e;left:240px;top:470px;width:1440px;padding:34px 44px;display:flex;gap:40px;align-items:center">
  <img id="f-qr" src="assets/brand/qr_live_app.png" style="width:190px;height:190px;border-radius:12px" alt="QR code to the live app">
  <div style="flex:1">
    <div class="kick">Try it free · open source</div>
    <div class="h3 cyan mono" style="font-size:36px;margin-top:10px;white-space:nowrap">{URL}</div>
    <div class="body" style="font-size:28px;margin-top:16px">Team Dreams of X: Mahdin Islam Mukim · Maliha Sanjana · Lamisa Yeasmin Nakia · Yousuf Abdullah · Md. Habibullah Sharif</div>
    <div id="f-credit" class="src" style="margin-top:16px">{CREDIT} · Images: NASA</div>
  </div></div>
"""
    js = f"""
land('#f-next', 0.05, {{ scale: 0.94, y: 0 }});
land('#f-card', 0.3);
"""
    return scene_file(sid, D, "", body, js), {"whoosh_in": 0.0, "impact_mars": t_mars, "sparkle_card": 0.3}


BUILDERS = {"d30a": d30a, "d30b": d30b, "d30c": d30c, "d30d": d30d, "d30e": d30e, "d30f": d30f}


# ---------------------------------------------------------------- captions + sound -----------------

# Hand-set caption lines (each phrase whole); the word timings place them. Used by the burned-in captions
# and by tools/srt_demo30.py for the YouTube subtitle file, so both always match.
CAPTION_LINES = {
    "human": ["Hey, I'm Habibullah,", "and this is my team, Dreams of X.",
              "For NASA's Abandoned but not Forgotten challenge,", "we built the Moon-Material Simulator.",
              "The machines left on the Moon", "show what it does to materials.",
              "Our free app predicts how NASA's bioplastic", "mixed with Moon dust will perform.",
              "Rebuild a broken part, test it in 3D,", "and see the evidence behind every number.", "Next stop: Mars."],
    "ai": ["We're Dreams of X.", "For NASA's Abandoned but not Forgotten challenge,",
           "we built the Moon-Material Simulator.", "The machines left on the Moon",
           "show what it does to materials.", "Our free browser app predicts how",
           "NASA Glenn's bioplastic mixed with Moon dust", "will perform, from real, audited lab data.",
           "Rebuild a broken part, test it in 3D,", "and see the evidence behind every number.", "Next stop: Mars."],
}["ai" if VOICE == "ai" else "human"]


def caption_cues():
    """(start, end, text) in film time for each caption line."""
    groups, i = [], 0
    for line in CAPTION_LINES:
        n = len(line.split())
        assert [w["text"] for w in WORDS[i:i + n]] == line.split(), line
        groups.append(WORDS[i:i + n]); i += n
    assert i == len(WORDS)
    cues = []
    for k, ws in enumerate(groups):
        start = VO_AT + ws[0]["start"] - 0.05
        end = VO_AT + ws[-1]["end"] + 0.15
        if k + 1 < len(groups):
            end = min(end, VO_AT + groups[k + 1][0]["start"] - 0.06)
        cues.append((round(start, 3), round(max(end, start + 0.3), 3), " ".join(w["text"] for w in ws)))
    return cues


def captions():
    css = """
#root { background: transparent; }
.cap { position: absolute; left: 0; width: 1920px; top: 958px; text-align: center; }
.cap span.box { display: inline-block; padding: 8px 22px 10px; border-radius: 12px; background: rgba(0,0,0,.55);
  font-family: 'Space Grotesk', 'Inter', sans-serif; font-weight: 600; font-size: 44px; color: #f4f7fb; letter-spacing: -.005em; }
"""
    body = ""
    for i, (start, end, text) in enumerate(caption_cues()):
        body += f'<div id="cap{i}" class="clip cap" data-start="{start:.3f}" data-duration="{end - start:.3f}"><span class="box">{text}</span></div>\n'
    return scene_file("d30cap", TOTAL, css, body, "")


def sound_tags(all_cues):
    tags = [f'<audio id="d30-music" class="clip" src="assets/audio/music.mp3" data-start="0" data-duration="{TOTAL:.3f}" '
            f'data-media-start="60" data-volume="0.12" data-fade-in="0.8" data-fade-out="2.5"></audio>',
            f'<audio id="d30-vo" class="clip" src="assets/voice/{VO_FILE}.wav" data-start="{VO_AT:.3f}" '
            f'data-duration="{VO_LEN:.3f}" data-volume="1"></audio>']
    files = {"whoosh": ["whoosh_a", "whoosh_b"], "pop": ["pop_a", "pop_b"], "impact": ["impact_a"], "crack": ["crack_a"],
             "sparkle": ["sparkle_a"]}
    gains = {"crack": 0.7, "whoosh": 0.22, "pop": 0.2, "impact": 0.5, "sparkle": 0.25}
    peaks = {"crack_a": 0.55, "impact_a": 2.06, "pop_a": 0.12, "pop_b": 0.33, "whoosh_a": 0.16, "whoosh_b": 0.29, "sparkle_a": 0.025}
    used, n = {}, 0
    for sid, cues in all_cues.items():
        for name, t in cues.items():
            kind = name.split("_")[0]
            if kind == "whoosh" and sid == "d30a":
                continue
            k = used.get(kind, 0); used[kind] = k + 1
            f = files[kind][k % len(files[kind])]
            start = START[sid] + t - peaks[f] + 1 / FPS
            if start < 0:
                continue
            tags.append(f'<audio id="d30-sfx{n}" class="clip" src="assets/sfx/{f}.mp3" data-start="{start:.3f}" data-volume="{gains[kind]}"></audio>')
            n += 1
    return tags


def main():
    comp = ROOT / "compositions"
    all_cues = {}
    for sid in IDS:
        html, cues = BUILDERS[sid]()
        (comp / f"{sid}.html").write_text(html)
        all_cues[sid] = cues
    (comp / "d30cap.html").write_text(captions())
    hosts = [f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
             f'data-start="{START[sid]:.3f}" data-duration="{DUR[sid]:.3f}" data-track-index="1" data-track-kind="graphics" '
             f'data-width="1920" data-height="1080" style="z-index:1"></div>' for sid in IDS]
    hosts.append(f'<div id="d30cap" data-composition-id="d30cap" data-composition-src="compositions/d30cap.html" data-start="0" '
                 f'data-duration="{TOTAL:.3f}" data-track-index="3" data-track-kind="captions" data-width="1920" data-height="1080" style="z-index:6"></div>')
    audio = sound_tags(all_cues)
    nl = "\n      "
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Moon-Material Simulator · 30-second demo</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #02040a; }}
      #main {{ position: absolute; inset: 0; background: #02040a; }}
    </style>
  </head>
  <body>
    <div id="main" data-composition-id="main" data-start="0" data-duration="{TOTAL:.3f}" data-width="1920" data-height="1080">
      {nl.join(hosts)}
      {nl.join(audio)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
    (ROOT / "demo30.html").write_text(html)
    print(f"voice: {VOICE} ({VO_FILE}.wav, {VO_LEN:.2f} s); total {TOTAL:.2f} s, last word ends {VO_AT + WORDS[-1]['end']:.2f} s")
    for sid in IDS:
        print(f"  {sid}  start {START[sid]:6.2f}  len {DUR[sid]:5.2f}")


if __name__ == "__main__":
    main()
