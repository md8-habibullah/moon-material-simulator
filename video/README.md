# 240 Seconds of Glory: Moon-Material Simulator

[← Back to README](../README.md) · Live app: <https://md8-habibullah.github.io/moon-material-simulator/>

> **Version 3 (13 November 2026), for the challenge "Abandoned but not Forgotten".** The rendered film
> (`film/renders/moon-material-simulator_v3_one-team.mp4`, 3:58.1) follows the narration in
> [`film/tools/vo.json`](film/tools/vo.json): 12 scenes in one young, soft male voice (ElevenLabs "Will",
> `film/tools/voice_el.py`), fitted to the 240-second limit by `film/tools/fit_voice.py` (pauses over 0.45 s shortened,
> tempo raised 2 to 6% with pitch kept). It opens with the machines NASA left on the Moon and Mars and what they taught
> us about materials. The team scene shows all five members equally ("five friends, one team"). The close is a 3D
> reel of the app (the dust sample, the bracket and brick breaking) and a scroll through the site, for engineers and,
> just as much, for students, teachers and space fans. Subtitles: `film/tools/srt.py`. Version 2 (two voices, team
> scene with a "built most of it" line) is replaced. The rest of this document is the original v1 script; its
> verified numbers and evidence rules still apply.

> **30-second Project Demo (14 November 2026).** The Space Apps 2026 Project Demo must be a video of 30 seconds or
> less (or at most 7 slides), so the global submission links a separate cut, published at <https://youtu.be/kRjf5DvXlKA>:
> `film/renders/moon-material-simulator_demo30.mp4` (29.5 s). Narration in [`film/tools/vo_demo30.json`](film/tools/vo_demo30.json)
> (same "Will" voice, `film/tools/voice_demo30.py`); scenes, burned-in captions and sound from
> `film/tools/build_demo30.py`, which writes `film/demo30.html` and `film/compositions/d30*.html`. Team, challenge,
> project, the machines left behind, the app, the 3D part test, the evidence, and the live link, with the AI voice
> credited on screen and in the file metadata. Render: `npx --yes hyperframes@0.9.39 render -c demo30.html -o renders/moon-material-simulator_demo30.mp4`
> from `film/` (with `DO_NOT_TRACK=1`).
>
> **Cloned-voice version (14 November 2026).** `film/renders/moon-material-simulator_demo30_clone.mp4` (29.5 s)
> opens with "Hey, I'm Habibullah, and this is my team, Dreams of X." over the team card. The narration is an AI voice
> cloned from Md. Habibullah Sharif's own voice, with his consent: `film/tools/clone_voice30.py` runs F5-TTS 1.1.22
> locally (`~/.venvs/f5tts`, CPU) with a 9.7 s reference from his voice note, then `film/tools/voice_human30.py --name
> d30_clone` fits it to the time (pauses capped at 0.3 s, tempo +2.3%) and aligns the words with local Whisper. His
> own recording had children audible in the background (the rules bar audio of anyone under 18), so it is not used.
> Credited on screen and in the file metadata; subtitles `youtube/demo30/captions_en_clone.srt`.

Team **Dreams of X** · NASA Space Apps Challenge 2026 · script v1, 2026-11-12

This is the production script for both videos: **Video 2 (Local Judging)** is the master, and **Video 1 
(Prescreening)** is a cut of it (section 5). It covers what is said, what is shown, which assets to record or make,
who speaks, and how it is edited, second by second.

Every number in the voice-over comes from the running app or the audit, and section 1 lists where each one comes
from. If the app changes before recording, re-check them.

---

## 0. The idea in one line, and the story

**One line:** NASA can now grow plastic on the Moon. We built the tool that tells you which mix to make, and proves
every answer with NASA's own data.

**The story:** a wrench breaks, and we find out why and fix it.

1. **Cold open:** a wrench made of NASA's bacterial plastic and moon dust snaps in our simulator.
2. **Problem:** a replacement from Earth costs up to $1 million per kg. NASA Glenn's new material could be made on
   site, but nobody knows which mix to make.
3. **Solution:** the simulator.
4. **Proof that it is real:** 1,470 values from NASA and peer-reviewed reports, each re-checked against the PDF by
   our auditor, and a model whose honest error on unseen mixes we measured.
5. **Back to the wrench:** we explain why it broke (lunar noon softens it, lunar night makes it brittle), then the
   optimizer finds a fully local mix that holds.
6. **Impact and close.**

The broken wrench at the start and the wrench that holds at the end are the same part, and that pairing is what
judges remember.

**Criteria targets.** Every scene is tagged with the criteria it earns:

| Criterion | Where it is earned |
| --- | --- |
| Impact (20) | S1, S2, S6c, S7 |
| Creativity (20) | S3, S5, S6a and S6b |
| Validity (20) | S4, S5, S6 |
| Relevance (20) | S2, S4 |
| Presentation (20) | The whole film |
| Teamwork (+5) | Five voices or faces, and the team card |
| User Experience (+5) | S3, S6 |
| NASA Data Usage (+5) | S4 (named out loud in Video 2) |
| Repository and project page (+1, +1) | S7 end card, and proof-of-work shots in S4 and S5 |

---

## 1. Ground rules: what must be true on screen

### Verified numbers

| Claim used in the video | Value | Where it comes from |
| --- | --- | --- |
| Resupply cost | up to **$1,000,000 per kg** | NASA Glenn, NTRS 20260007758 (README "The problem") |
| Earth–Moon distance | about **384,000 km** | Mean distance 384,400 km |
| NASA Glenn material (2026) | Plastic (PHB) grown in bacteria fed with CO₂ or crew waste, mixed with Moon and Mars dust simulants | nasa.gov image article (Sept 2026); NTRS 20260003641, 20260007758 |
| Sources registered / transcribed | 13 / 11 | [`research/sources.csv`](../research/sources.csv) |
| Values transcribed | **1,470**, each with page, table, row and column | [`research/extraction/`](../research/extraction/) |
| Transcription errors found by the auditor | **0** | [`research/audit/`](../research/audit/) |
| Problems inside the papers themselves | **181** | [`research/audit/`](../research/audit/) (SOURCE_ISSUE) |
| Original calibration points re-verified | **56 of 56** | audit, MODEL_REFERENCE_MATCH |
| Real measurements the model learns from | **152**, from **7** studies | Hero stats, [`docs/evidence.md`](../docs/evidence.md) |
| Compressive strength error, physics alone → with lab data (unseen mixes) | **230% → 34%** | [`docs/science_model.md`](../docs/science_model.md) |
| Stiffness | **65% → 19%** | as above |
| Density | **16% → 5%** | as above |
| Thermal conductivity | **32% → 7%** | as above |
| Compressive strength, whole new study left out | **78%** (stated as a limit) | as above |
| Evidence drawer example (PEI, 80% lunar mare, hot-pressed) | predicts **117 MPa**; paper measured **119 MPa** | S008, Figure 11 |
| PHB wrench, 38% lunar highlands, molded, 20 °C | breaks at **71 N**; needs **72 N**; safety factor **0.98×** | Part test |
| Same wrench at lunar noon (127 °C) | safety factor **0.16×** (softens) | Part test |
| Same wrench at lunar night (−173 °C) | **1.83×**, but **brittle (snaps)** | Part test |
| Mixes the optimizer tests for a wrench | **4,662** (say "nearly 5,000") | Optimizer |
| Optimizer's top wrench mix | PHB + **45%** lunar highlands + **15%** basalt fibre, 25 µm grains, **100% local**; breaks at **124 N**; **1.71×**; bends before breaking | Optimizer, then Part test |
| Thruster nozzle | **no mix works**, and the app says so | Optimizer |
| Mission impact | **25 parts × 0.4 kg = 10 kg** not launched; **up to $10 million** at $1M/kg | Impact tab (default inputs) |

### Never say or show

- **"R² 0.99" or "99% accurate".** That score was measured on our own synthetic data, not real samples. The
  honest numbers are the ones in the table above.
- **"NASA-approved", "NASA's tool" or the NASA logo.** The NASA insignia ("meatball") and logotype ("worm") need NASA
  permission and imply endorsement. NASA photos are fine with credit ("Image: NASA"). Use the Space Apps logo only
  as its brand guidelines allow.
- **"Real regolith".** The studies used regolith **simulants** (lab copies of Moon and Mars soil). Say "simulated Moon
  dust" or "simulant".
- **"Tested in the lab".** Our part test is a simulation: beam formulas applied to the model's predictions. It is fine
  to say "the simulator predicts".

### Two things the team must settle before recording

1. **Challenge name.** Challenges are published on 13 November. Replace every `[CHALLENGE]` below with the exact title,
   and the `[CHALLENGE ASK]` with one sentence of its statement.
2. **Work done before the hackathon.** The repository and an earlier pitch video date from October 2026. Read the 2026
   Space Apps rules on prior work. If disclosure is required or wise, the end card has a slot for one line (S7).

---

## 2. Timeline at a glance

The mentor's split, compared with this script:

| Segment | Mentor's plan | This script | Why it changed |
| --- | --- | --- | --- |
| Problem | 0:00–0:30 | 0:00–0:37 (S1, S2) | Opens on the breaking wrench: a moving image in the first second, not a title |
| Solution | 0:30–1:05 | 0:37–1:03 (S3) | Same |
| NASA data | 1:05–1:50 | 1:03–1:45 (S4) | Same |
| Technology and science | 1:50–2:55 | 1:45–2:28 (S5) | Shorter: the demo proves the science again |
| Live demo | 2:55–3:40 | 2:28–3:32 (S6) | Longer: the demo is the strongest evidence of a working product |
| Impact and close | 3:40–4:00 | 3:32–4:00 (S7) | Same |

Scene by scene:

| Scene | Time | Length | Content | Voice |
| --- | --- | --- | --- | --- |
| S1 | 0:00–0:15 | 15 s | Cold open: the wrench snaps | Mahdin |
| S2 | 0:15–0:37 | 22 s | NASA's breakthrough, and the open question | Mahdin |
| S3 | 0:37–1:03 | 26 s | The solution: the simulator | Maliha |
| S4 | 1:03–1:45 | 42 s | NASA data and the Evidence Auditor | Lamisa |
| S5 | 1:45–2:28 | 43 s | Science and honest validation | Yousuf |
| S6a | 2:28–2:54 | 26 s | Demo: why the wrench broke | Habibullah |
| S6b | 2:54–3:13 | 19 s | Demo: the optimizer fixes it | Habibullah |
| S6c | 3:13–3:32 | 19 s | Demo: honest "no", and launch mass saved | Habibullah |
| S7 | 3:32–4:00 | 28 s | Impact, team, close | Mahdin |

**Voice-over budget:** about 495 words in 240 s, an average of 124 words a minute. That is a calm pace with room to
breathe. Edit to finish at **3:55–3:58**; never go over 4:00.

---

## 3. Full script: Video 2 (Local Judging, master)   

Each scene gives: **Visual** (what is on screen), **On-screen text**, **VO** (word count), **Sound**, **Assets**
(IDs from section 6) and **Edit notes**.

### S1 · 0:00–0:15 · Cold open: the wrench snaps · Impact

**Visual**
- 0:00–0:03: black, then a fade into the Part test in full screen. A tan wrench sits on its bolt above the glowing
  floor and starfield, with the camera slowly orbiting.
- 0:03–0:09: the load arrow pushes down. The wrench bends, its colours run from blue to red at the root, and the
  gauge fills.
- 0:09–0:11: it snaps. The handle falls slowly in lunar gravity, fragments scatter, and the red banner reads "Broke
  at 71 N".
- 0:11–0:15: hold on the broken wrench, with a slow push-in, and dim slightly for the text.

**On-screen text** (fades in at 0:11, lower left)
> **Resupply from Earth: up to $1,000,000 per kg**
> <small>NASA Glenn Research Center · NTRS 20260007758</small>

**VO** (Mahdin, 30 words)
> On the Moon, a broken wrench is not a small problem. *(beat)* The next one is three hundred and eighty-four thousand
> kilometres away, and sending it can cost up to a million dollars per kilogram.

**Sound:** the app's own audio, recorded live: low hum, rising creak, then the crack. The music starts at 0:11:
a single low synth note that swells.

**Assets:** REC-01, MG-02

**Edit notes:** no logo and no title card first, so the first frame already moves. The crack lands on "broken"
(about 0:04 in the VO); time the VO start so it does.

---

### S2 · 0:15–0:37 · NASA's breakthrough and the open question · Relevance, Impact

**Visual**
- 0:15–0:22: the NASA Glenn photo of the bacterial plastic samples mixed with simulants, with a slow Ken Burns
  zoom. Credit, bottom right: "Image: NASA".
- 0:22–0:28: Moon-surface B-roll (Apollo or LRO, public domain).
- 0:28–0:37: motion graphic "Which mix?". A grid of possibilities explodes outward:
  - 6 binders × 3 soils × 5 processes × 0–92.5% dust × fibre × grain size,
  - landing on "≈ 5,000 combinations for one wrench",
  - then question marks over a wrench, a bracket and a brick.

**On-screen text**
- 0:16: lower third: "NASA Glenn, 2026: plastic grown by bacteria + simulated Moon and Mars dust"
- 0:30: "Which mix? How much dust? Strong enough?"
- 0:34: small, top left: "Challenge: [CHALLENGE]"

**VO** (Mahdin, 48 words)
> In 2026, NASA Glenn grew a plastic inside bacteria and mixed it with simulated Moon and Mars dust: a material that
> could be made on site. *(beat)* But which mix? How much dust, which dust, and is it strong enough for a wrench?
> You can't test every combination on Earth.

**Sound:** the music builds (ambient pads, slow pulse). A soft whoosh as the grid explodes.

**Assets:** IMG-01, IMG-02, MG-03

**Edit notes:** "You can't test every combination" lands as the grid fills the screen.

---

### S3 · 0:37–1:03 · The solution · Creativity, User Experience

**Visual:** a fast, clean montage of the real app, cut on the beat.
- 0:37–0:42: the hero section, which reads "Design a building material from moon dust…".
- 0:42–0:50: Step 1, Design: clicking Bio-PHB, Lunar highlands and Injection molding, then dragging the regolith
  slider.
- 0:50–0:56: the Results panel updating live, with the cursor circling a "Lab-backed" chip and a "Physics estimate"
  chip.
- 0:56–1:03: the 3D sample in full screen. Orbit and zoom, then press "Print it": the glowing nozzle builds the sample
  layer by layer.

**On-screen text**
- 0:38: title card, top centre: **Moon-Material Simulator** · "Dreams of X"
- 0:51: callout arrows: "8 properties, live" · "how sure it is" · "lab-backed or physics?"
- 0:58: small: "Runs in your browser · open source"

**VO** (Maliha, 57 words)
> For the [CHALLENGE] challenge, we built the Moon-Material Simulator. *(beat)* Pick a binder, a soil, and how the part
> is made. Instantly, a physics model corrected by machine learning predicts eight properties, shows how sure it is,
> and tells you whether each number is backed by real lab data. *(beat)* It runs in any browser, and it's open source.

**Sound:** the music settles into its main groove. UI clicks come from the screen recording, kept quiet. The printer
ticks of "Print it" stay audible under the VO.

**Assets:** REC-02, REC-03, REC-04, MG-01

**Edit notes:** this scene sells User Experience, so the cursor must move smoothly with no hunting. Use cursor
highlighting and a 1.1–1.2× zoom on the panel being used.

---

### S4 · 1:03–1:45 · NASA data and the Evidence Auditor · Relevance, Validity, NASA Data Usage

**Visual**
- 1:03–1:15: "source wall". The cover pages of the real reports fly in as cards, each labelled:
  - NASA Glenn: NTRS 20260003641 and NTRS 20260007758 (bacterial PHB + LMS-1, LSP-2, LHS-1, MGS-1, JEZ-1)
  - NASA Kennedy: NTRS 20230015024 and NTRS 20240004186 (PLA + LHS-1 / BP-1 pellet printing)
  - NASA, 2003: NTRS 20030020808 (polyethylene + regolith, radiation shielding)
  - Peer-reviewed: Polymers, Acta Astronautica, Applied Sciences (5 studies)
- 1:15–1:24: a counter animation: **13 sources → 1,470 values**. A PDF table gets a coloured box on one cell, with
  the label "page · table · row · column".
- 1:24–1:36: screen recording of the audit report. Scroll the findings, open one crop with coloured boxes (row,
  column, our value), and filter to SOURCE_ISSUE.
- 1:36–1:45: three stat tiles snap in, one by one:
  **0** transcription errors · **181** problems found inside the papers · **56 / 56** original calibration points
  re-verified.

**On-screen text:** the source names above (small and accurate), the counter, the tiles. In the corner of the audit
footage: "Our auditor never edits data. It only comments."

**VO** (Lamisa, 85 words)
> Our science stands on NASA's own data: NASA Glenn's 2026 bacterial-plastic reports, NASA Kennedy's
> regolith-printing studies, and a 2003 NASA report on polyethylene and regolith, plus peer-reviewed papers. *(beat)*
> We transcribed 1,470 measured values, each tied to its page, table, row and column. Then we built an auditor that
> finds every number again in the original PDF. It never edits data; it only comments. *(beat)* Zero transcription
> errors, and 181 problems inside the papers themselves.

**Sound:** the music drops to a lighter, ticking texture, and the counters get soft digital ticks. Each stat tile gets
a soft "thunk".

**Assets:** IMG-03 (PDF cover pages, rendered from `research/pdfs/` (not in git; fetch with [`research/download_sources.py`](../research/download_sources.py))), MG-04, MG-05, REC-12, REC-14

**Edit notes:** in Video 2, the NASA source names must be **spoken**, which is a requirement. Keep the NTRS numbers on
screen long enough to read (at least 2 s each). The audit crop is the credibility shot: zoom in on the coloured boxes.

---

### S5 · 1:45–2:28 · Science and honest validation · Validity, Creativity

**Visual**
- 1:45–1:58: animated pipeline diagram, built left to right:
  **Physics** (composite equations, temperature effects) → **Fast emulator** (28-tree random forest, runs in the
  browser) → **Learned correction** (Gaussian process trained on 152 real measurements) → **Prediction + likely range
  + evidence link**.
- 1:58–2:14: bar chart with paired bars per property, "physics alone" (grey) next to "with lab data" (accent). The
  bars animate down:
  compressive 230% → 34% · stiffness 65% → 19% · density 16% → 5% · thermal conductivity 32% → 7%.
  Caption: "Average error on mixes the model never saw".
- 2:14–2:18: honest-limits card: "A study it has never seen: 78% (compressive). We show this too."
- 2:18–2:28: screen recording of the evidence drawer for PEI with 80% lunar mare, hot-pressed:
  - the compressive-strength chip is clicked,
  - the drawer opens to the nearest real measurements, and the crop of the paper's Figure 11 expands,
  - side by side: **"Predicted 117 MPa" | "Measured 119 MPa (S008, Fig. 11)"**.

**On-screen text:** diagram labels; chart title "Average error on mixes the model never saw"; the honest-limits card;
the predicted-versus-measured labels.

**VO** (Yousuf, 88 words)
> Physics alone isn't enough: on real samples, its compressive-strength predictions were off by up to 230 percent. So
> we kept the physics and taught a Gaussian process its mistakes, using 152 real measurements from seven studies.
> *(beat)* On mixes it never saw, the error drops from 230 to 34 percent for compressive strength, 65 to 19 for
> stiffness, 16 to 5 for density. A completely new study is harder, and we say so. *(beat)* And every prediction
> links to its evidence: this one says 117 megapascals. The paper measured 119.

**Sound:** the music returns to the main groove. A small "pop" as each bar settles. Hold a short pause in the music on
"117 … 119".

**Assets:** MG-06, MG-07, MG-08, REC-05, REC-06

**Edit notes:** this is the Validity peak, so give "117 / 119" a full second of silence. Never show the synthetic
emulator R² here.

---

### S6a · 2:28–2:54 · Demo: why the wrench broke · Validity, User Experience

**Visual** (Part test, full screen, continuous screen recording; speed up only the dead time)
- 2:28–2:36: back to the wrench from S1, at the habitat setting. Fast-forward the load (1.5×). The banner reads
  "Broke at 71 N".
- 2:36–2:39: overlay the facts card from under the viewer: Breaks at 71 N · Design load 72 N · **Safety factor
  0.98×** in red.
- 2:39–2:45: click **Lunar noon, 127 °C**. The scene goes harsh white under a black sky, and the safety factor drops
  to **0.16×**.
- 2:45–2:54: click **Lunar night, −173 °C**. The scene goes blue and the safety factor rises to 1.83×, with "Snaps
  suddenly" under "How it breaks". Run it: it snaps with no bending.

**On-screen text:** callouts at each step: "0.98× · fails" → "Noon: softens · 0.16×" → "Night: stronger, but brittle".

**VO** (Habibullah, 60 words)
> Back to our wrench: bacterial plastic with 38 percent lunar highlands dust. The part test applies beam theory to the
> model's predictions. It breaks at 71 newtons, just short of the 72 needed to tighten a bolt. *(beat)* At lunar noon it
> softens to a sixth of that. At lunar night it's almost twice as strong, but brittle: it snaps instead of bending.

**Sound:** the app's creak and crack, live. A low hum under the noon section and a colder, airy pad under the night
section.

**Assets:** REC-07

**Edit notes:** keep the HUD numbers legible. If the VO is tight, cut from the noon click straight to the night snap.

---

### S6b · 2:54–3:13 · Demo: the optimizer fixes it · Creativity, Impact

**Visual**
- 2:54–3:00: the Optimize section. Choose "Wrench / hand tool" and run it. The counter shows the mixes tested, and the
  results appear.
- 3:00–3:04: the top result is highlighted: PHB + 45% lunar highlands + 15% basalt fibre · **100% local**. Press
  **Load**.
- 3:04–3:13: the Part test on the new mix, at the habitat setting. Load it: the green banner "Design load held"
  appears with the app's chime, and the gauge keeps rising. The facts card reads **safety factor 1.71×** · "Bends,
  then breaks".

**On-screen text:** "Nearly 5,000 mixes tested" · "100% made from local resources" · "1.71× · bends before it breaks".

**VO** (Habibullah, 37 words)
> So we ask the optimizer. It tests nearly five thousand mixes and finds one made entirely from local resources: 45
> percent dust and 15 percent basalt fibre. *(beat)* Safety factor 1.7, and it bends before it breaks.

**Sound:** the music lifts (major key, warmer). The chime on "Design load held" is the payoff sound of the film.

**Assets:** REC-08, REC-09

**Edit notes:** this is the turning point of the story. Cut so the chime lands on "Safety factor 1.7".

---

### S6c · 3:13–3:32 · Demo: an honest "no", and the launch mass saved · Validity, Impact

**Visual**
- 3:13–3:20: the optimizer with "Thruster nozzle" chosen. It shows no feasible mix and an honest message pointing to
  sintered regolith or ceramics instead.
- 3:20–3:32: the Impact tab: 25 parts of 0.4 kg, with the binder grown on site and the fibre drawn on site. Counters
  animate to **10 kg not launched** and **up to $10,000,000**.

**On-screen text:** "It tells you when nothing works" · "25 parts × 0.4 kg = 10 kg not launched".

**VO** (Habibullah, 33 words)
> Ask it for a rocket nozzle, and it honestly says no plastic survives. *(beat)* And a kit of 25 small parts printed
> on site keeps 10 kilograms off the launch pad: up to 10 million dollars.

**Sound:** a soft negative blip on "no", then a rising tone as the counters run.

**Assets:** REC-10, REC-11

---

### S7 · 3:32–4:00 · Impact, team, close · Impact, Teamwork, Presentation

**Visual**
- 3:32–3:44: wide NASA Artemis or Moon-base concept B-roll, then the Moon from orbit, with a slow drift.
- 3:44–3:52: team card. Five photos, or 1-second video clips of each person at the hackathon, with name and role:
  - Mahdin Islam Mukim, Team Lead
  - Yousuf Abdullah, Data Scientist
  - Md. Habibullah Sharif, Systems Architect
  - Maliha Sanjana, UI/UX Designer
  - Lamisa Yeasmin Nakia, Research & Storytelling Lead
- 3:52–4:00: end card on a dark space background:
  - the **Moon-Material Simulator** title,
  - the live app URL and a QR code: `md8-habibullah.github.io/moon-material-simulator`,
  - the repository: `github.com/md8-habibullah/moon-material-simulator`,
  - small text: "Built on NASA open data (NTRS) and peer-reviewed studies · Open source (licence as in repo)",
  - an optional prior-work line, if required: "Prototype started October 2026; data pipeline, auditor and evidence
    model built for Space Apps 2026."

**VO** (Mahdin, 57 words)
> Every kilogram made on the Moon is a kilogram we don't have to launch. Our simulator helps engineers choose the right
> mix before a single sample is printed, and shows which real measurement backs every answer. *(beat)* The same
> method works for Mars, and for any material where data is scarce. *(beat)* We are Dreams of X. Try it yourself.

**Sound:** the music resolves and ends on a clean hit at 3:57. The last 2 s are near-silent under the end card.

**Assets:** IMG-04, IMG-05, TEAM-01, MG-09, MG-10

**Edit notes:** the end card holds for at least 6 s, so a judge can read or scan it.

---

## 4. Full voice-over, clean copy (for the recording booth)

Read at a calm pace. *(beat)* = half-second pause. Bold = stress the word.

**MAHDIN (S1–S2)**
On the Moon, a **broken wrench** is not a small problem. *(beat)* The next one is three hundred and eighty-four
thousand kilometres away, and sending it can cost up to a **million dollars per kilogram**.
In 2026, NASA Glenn grew a plastic **inside bacteria** and mixed it with simulated Moon and Mars dust: a material that
could be **made on site**. *(beat)* But **which mix**? How much dust, which dust, and is it strong enough for a
wrench? You can't test every combination on Earth.

**MALIHA (S3)**
For the [CHALLENGE] challenge, we built the **Moon-Material Simulator**. *(beat)* Pick a binder, a soil, and how the
part is made. Instantly, a physics model corrected by machine learning predicts **eight properties**, shows **how
sure it is**, and tells you whether each number is **backed by real lab data**. *(beat)* It runs in any browser, and
it's open source.

**LAMISA (S4)**
Our science stands on **NASA's own data**: NASA Glenn's 2026 bacterial-plastic reports, NASA Kennedy's
regolith-printing studies, and a 2003 NASA report on polyethylene and regolith, plus peer-reviewed papers. *(beat)*
We transcribed **1,470** measured values, each tied to its page, table, row and column. Then we built an **auditor**
that finds every number again in the original PDF. It never edits data; it only comments. *(beat)* **Zero**
transcription errors, and **181** problems inside the papers themselves.

**YOUSUF (S5)**
Physics alone isn't enough: on real samples, its compressive-strength predictions were off by up to **230 percent**.
So we kept the physics and taught a **Gaussian process** its mistakes, using **152 real measurements** from seven
studies. *(beat)* On mixes it never saw, the error drops from 230 to **34 percent** for compressive strength, 65 to
**19** for stiffness, 16 to **5** for density. A completely new study is harder, **and we say so**. *(beat)* And
every prediction links to its evidence: this one says **117** megapascals. The paper measured **119**.

**HABIBULLAH (S6)**
Back to our wrench: bacterial plastic with 38 percent lunar highlands dust. The part test applies beam theory to the
model's predictions. It breaks at **71** newtons, just short of the **72** needed to tighten a bolt. *(beat)* At
lunar **noon** it softens to a sixth of that. At lunar **night** it's almost twice as strong, but **brittle**: it
snaps instead of bending.
So we ask the **optimizer**. It tests nearly five thousand mixes and finds one made **entirely from local
resources**: 45 percent dust and 15 percent basalt fibre. *(beat)* Safety factor **1.7**, and it **bends before it
breaks**.
Ask it for a rocket nozzle, and it **honestly says no** plastic survives. *(beat)* And a kit of 25 small parts printed
on site keeps **10 kilograms** off the launch pad: up to **10 million dollars**.

**MAHDIN (S7)**
Every kilogram made on the Moon is a kilogram we **don't have to launch**. Our simulator helps engineers choose the
right mix **before a single sample is printed**, and shows which real measurement backs every answer. *(beat)* The
same method works for **Mars**, and for any material where data is scarce. *(beat)* We are **Dreams of X**. Try it
yourself.

### Pronunciation guide

| Word | Say |
| --- | --- |
| regolith | REG-uh-lith |
| simulant / simulated | SIM-yuh-lunt / SIM-yuh-lay-ted |
| PHB | P-H-B (if spoken in full: poly-hy-DROX-ee-BYOO-tih-rate) |
| Gaussian | GOW-see-un |
| megapascals | MEG-uh-pass-kulz |
| Glenn (NASA Glenn) | Glen |
| basalt | buh-SALT |
| polyethylene | pol-ee-ETH-ih-leen |

---

## 5. Video 1 (Prescreening): what changes

The prescreening video must show the **concept, team names, problem and challenge statement, and approach**. A
working demo is optional. Reuse the master edit with these changes:

| Scene | Video 1 change | New length |
| --- | --- | --- |
| S1 | Same cold open | 15 s |
| S2 | Add the challenge statement, **read aloud** (see below) | 30 s |
| S3 | Same | 26 s |
| S4 | Shorter: the source wall and the counters, skipping the audit-report footage. Sources can be named on screen only. | 30 s |
| S5 | Shorter: the pipeline diagram and the accuracy bars, without the evidence drawer | 30 s |
| S6 | Replace with "What you can do with it": a 35 s montage of the wrench breaking and holding, Print it, and the optimizer, with no step-by-step | 35 s |
| S7 | Team first: each member on camera for 4–5 s saying their name and role (Teamwork), then impact and the end card | 74 s |

Total: 15 + 30 + 26 + 30 + 30 + 35 + 74 = 240 s.

**Extra S2 line for Video 1** (Mahdin, about 20 words, after "…made on site."):
> Our challenge, [CHALLENGE], asks us to [CHALLENGE ASK]. *(beat)*

**S6, Video 1 VO** (Habibullah, 55 words):
> With the simulator you can design a mix, watch it being printed, and load a real part until it breaks: in the
> habitat, at lunar noon or at lunar night. When a part fails, the optimizer searches thousands of mixes for one that
> holds, made from local resources, and tells you honestly when nothing works.

**S7, Video 1 team round** (each person, on camera, about 8 words):
> "I'm Mahdin, team lead." · "I'm Yousuf, I built the model's data science." · "I'm Habibullah, I built the system." ·
> "I'm Maliha, I designed the experience." · "I'm Lamisa, I led the research and the story."

Then the S7 master VO and the end card.

---

## 6. Assets: everything to record, make or collect

### 6.1 Screen recordings (REC)

**Before recording:**
- Commit and deploy, so the live URL in the video shows these features.
- Record from a real browser with GPU acceleration: Chrome, Brave or Edge, **not** a headless browser.

**Recording settings:**

| Setting | Value |
| --- | --- |
| Tool | OBS Studio (free) |
| Canvas | 1920×1080 or 2560×1440, at **60 fps** |
| Encoder | NVENC or x264 |
| Quality | CQ 18–20 |
| Format | MKV, remuxed to MP4 afterwards |
| Audio | Desktop audio on its own track; the app's sound effects are real |

**Browser:**
- Window 1920×1080, zoom 100%.
- Theme: **dark** (moon icon in the navbar). Bookmarks bar hidden, other tabs closed, notifications off.
- Use a cursor highlighter (OBS plugin, or the OS setting) and move the mouse slowly.

**App setup:** turn **sound on** with the speaker icon in the 3D view. Use the full-screen button for every 3D shot.

| ID | What to capture | URL or how to get there | Actions | Used in |
| --- | --- | --- | --- | --- |
| REC-01 | Wrench snapping (habitat) | `/?b=PHB&p=molded&r=lunar_highlands&w=38&f=0&d=60&t=20#simulator` → Part test tab → full screen | Let it orbit for 3 s, then press "Load it until it breaks"; keep recording 5 s after the break. Do 3 takes. | S1 |
| REC-02 | Hero and design controls | `/` | Scroll the hero, click Start designing, then click Bio-PHB, Lunar highlands and Injection molding; drag regolith 10 → 38% | S3 |
| REC-03 | Results updating | Same | Drag regolith 38 → 60 → 38 slowly; hover a "Lab-backed" chip and a "Physics estimate" chip | S3 |
| REC-04 | 3D sample | 3D sample tab → full screen | Orbit by dragging, click and scroll to zoom, then press **Print it** and capture the whole build | S3 |
| REC-05 | Evidence drawer | `/?b=PEI&p=hot_pressed&r=lunar_mare&w=80&f=0&d=60&t=20#simulator` | Click the compressive-strength chip, scroll to the S008 Fig. 11 point, open its picture. Check that it reads 117 vs 119. | S5 |
| REC-06 | Accuracy table | Science section ("Accuracy on real lab data") | Slow scroll; hold 3 s | S5 (backup for MG-07) |
| REC-07 | Wrench at noon and night | REC-01 URL → Part test | Habitat run (1 take), then click Lunar noon (pause 3 s), then Lunar night and run it | S6a |
| REC-08 | Optimizer, wrench | Optimize section | Choose Wrench / hand tool, show the results, press **Load** on #1 | S6b |
| REC-09 | Winning wrench holds | `/?b=PHB&p=molded&r=lunar_highlands&w=45&f=15&d=25&t=20#simulator` → Part test | Run: capture the "Design load held" chime, then the break at about 124 N; show the facts card (1.71×) | S6b |
| REC-10 | Nozzle refusal | Optimize → Thruster nozzle | Show the "no mix" message | S6c |
| REC-11 | Mission impact | Impact section | Defaults: 0.4 kg × 25, $1M/kg, binder grown and fibre drawn on site; show 10 kg and $10M | S6c |
| REC-12 | Audit report | Open [`research/audit/audit_report.html`](../research/audit/audit_report.html) in the browser | Scroll the findings, open one crop with boxes, filter to SOURCE_ISSUE, open the S003 0°/90° issue | S4 |
| REC-13 | Proof of work (optional in S5) | Terminal | `cd backend && pytest -q` → "64 passed"; `cd frontend && npm test` → "pass 5" | S5 cutaway, 1 s |
| REC-14 | NASA NTRS pages | ntrs.nasa.gov/citations/20260007758 and 20230015024 | Show the title and the "NASA Glenn" / "Kennedy" centre fields | S4 |

### 6.2 Motion graphics to build (MG)

| ID | What | Notes |
| --- | --- | --- |
| MG-01 | Title card "Moon-Material Simulator · Dreams of X" | Space Grotesk (the app's font), cyan glow |
| MG-02 | Stat card "$1,000,000 per kg" with source line | Number counts up from $0 in 1 s |
| MG-03 | "Which mix?" combinatorics grid | 6 × 3 × 5 × loadings → "≈ 5,000 for one wrench" |
| MG-04 | Source wall | Real PDF cover pages (rendered from `research/pdfs/` (not in git; fetch with [`research/download_sources.py`](../research/download_sources.py))) as cards with NTRS IDs |
| MG-05 | Counters and stat tiles | 13 → 1,470; tiles 0 · 181 · 56/56 |
| MG-06 | Pipeline diagram | Physics → emulator → learned correction → prediction + range + evidence |
| MG-07 | Accuracy bar chart | Paired bars, 4 properties; title "Average error on mixes the model never saw" |
| MG-08 | Honest-limits card | "A study it has never seen: 78% (compressive). We show this too." |
| MG-09 | Team card | 5 photos or clips, names and roles |
| MG-10 | End card | URL, QR code, repo, credits line, optional prior-work line |
| MG-11 | Callouts and lower thirds | One style for the whole film (section 7) |

### 6.3 Images and footage from outside the project (IMG)

| ID | What | Where to get it | Licence note |
| --- | --- | --- | --- |
| IMG-01 | NASA Glenn bacterial-plastic samples | nasa.gov image article "NASA-made material for Moon manufacturing" (link in the README) | NASA media is generally not copyrighted; credit "Image: NASA". Check the page for any third-party credit. |
| IMG-02 | Moon surface B-roll | NASA Image and Video Library (images.nasa.gov): Apollo surface photos, LRO imagery; NASA SVS "CGI Moon Kit" | Same as above; no NASA insignia |
| IMG-03 | Cover and table pages of our sources | Rendered from `research/pdfs/` (not in git; fetch with [`research/download_sources.py`](../research/download_sources.py)) | NASA reports are public; for journal papers, show only short crops (all are CC BY: credit authors and journal) |
| IMG-04 | Artemis or Moon-base concept art | images.nasa.gov ("Artemis base camp concept") | Credit "Concept: NASA" |
| IMG-05 | Moon from orbit | NASA SVS (Moon phase and libration renders) | Credit "NASA SVS" |

### 6.4 Team material (TEAM)

- **TEAM-01:** one clean photo of each member: shoulders up, the same background, landscape. Better still, a
  2-second video clip of each person working at the hackathon.
- **For Video 1:** each member records their line facing the camera, framed the same way, with a phone held
  horizontally at eye level, next to a window for light.
- **A group shot** of the five at the venue (Teamwork).

### 6.5 Audio

- **Voice:** see section 8.
- **Music:** a single royalty-free ambient or electronic track, 90–110 BPM, with a build and a resolution. Sources:
  YouTube Audio Library, or Pixabay Music. Read the licence of the track you choose and keep a copy of it.
  No commercial songs.
- **Sound effects:** the app's own sounds (creak, crack, chime, print ticks), recorded live in REC-01, 04, 07 and 09.
  Add a few soft UI ticks and whooshes from a free library (Pixabay SFX), checking the licence.

---

## 7. Look and edit style

| Item | Choice |
| --- | --- |
| Colours | Space black `#02040a`; cyan `#7fe3ff` (data and UI); orange `#ff9a4d` (load, heat, action); green `#2fd39b` (pass); red `#ff6b6b` (fail). The same palette as the app. |
| Fonts | Space Grotesk for titles and labels (the app's font); a monospace font for NTRS IDs and numbers |
| Lower thirds | Left-aligned, thin cyan rule, max 2 lines, at least 2.5 s on screen |
| Captions | **Burned-in English subtitles** for every word of VO (judges, accents, sound-off viewing). Max 2 lines and 42 characters per line, on a semi-transparent dark box. Also export an `.srt`. |
| Numbers | Any number that is spoken also appears on screen, the same as in section 1 |
| Transitions | Cuts on the beat; whip-pans or light glows only between acts (S2→S3, S5→S6, S6→S7). No star wipes or page curls. |
| Pace | No shot under 1.5 s with text on it; nothing static for more than 6 s |
| Screen recordings | Gentle 1.05–1.2× punch-ins on the area being used; never crop away the cursor |
| Credits | Tiny on-screen credits on every outside image ("Image: NASA", "Concept: NASA", the source ID for crops) |

**Export:** 1920×1080 (or 3840×2160), 30 or 60 fps, H.264 MP4 at 12–20 Mbps, AAC 48 kHz. Loudness: about −14 LUFS
integrated, true peak −1 dBTP. Keep the voice clearly on top: music sits 18–24 dB below the voice while someone
speaks.

---

## 8. Recording the voice

- **One quiet room, the same microphone for everyone.** A phone in a closet full of clothes beats a laptop mic in an
  echoing room. Put the mic 15–20 cm from the mouth, slightly off to the side.
- **Record every scene 3 times:** natural, slower, and more energetic. Record 10 s of room silence first (for noise
  removal).
- **Pace:** about 125–135 words a minute, which feels slow when you read it. Smile on S1, S6b and S7.
- **Format:** WAV, 48 kHz, 24-bit. Clean-up chain: gentle noise reduction, high-pass at 80 Hz, light compression, then
  loudness.
- **Fewer voices:** if five voices are too uneven, use two (Mahdin for S1–S3 and S7, Habibullah for S4–S6) and show all
  five on camera in S7.

---

## 9. Plan for 13–15 November

| When | Task | Who |
| --- | --- | --- |
| 13 Nov, when challenges go live | Fill in `[CHALLENGE]` and `[CHALLENGE ASK]`; decide the prior-work line | Mahdin, Lamisa |
| 13 Nov | Commit and deploy; record REC-01 to REC-14 | Habibullah |
| 13–14 Nov | Build MG-01 to MG-11; gather IMG; take TEAM photos and clips | Maliha (with Claude if wanted) |
| 14 Nov | Record the voice-over (section 4); record the Video 1 team lines | Everyone |
| 14 Nov, evening | Rough cut of Video 2; check its length is ≤ 3:58 | Editor |
| 15 Nov | Captions, music mix, loudness, Video 1 cut, export, upload; complete the project page and repository link | Editor, Mahdin |

### Final checklist before upload  

- [ ] Both videos are 4:00 or shorter
- [ ] Every number matches section 1, with no synthetic R²
- [ ] NASA datasets are named out loud in Video 2
- [ ] Team names are visible (both videos); the challenge statement is read aloud (Video 1)
- [ ] No NASA insignia; every outside image is credited
- [ ] Captions are burned in, and an `.srt` exists
- [ ] The live URL and repository in the end card open, the repository is public, and the project page is complete
- [ ] Music licence saved
- [ ] The prior-work disclosure decision is made
