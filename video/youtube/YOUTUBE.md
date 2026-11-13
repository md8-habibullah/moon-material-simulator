# YouTube upload kit: the 240-second pitch film (v2, "Abandoned but not Forgotten")

Everything needed to upload `video/film/renders/moon-material-simulator_v2_abandoned.mp4` (3:58.7, 1080p30). Copy each
block as it is.

| File | Use it for |
| --- | --- |
| `../film/renders/moon-material-simulator_v2_abandoned.mp4` | The video |
| `thumbnail.jpg` | Custom thumbnail (1280 × 720) |
| `captions_en.srt` | English subtitles (62 cues, timed to the ElevenLabs voice) |

---

## Title

Pick one (all under YouTube's 100-character limit).

**Recommended:**

```
What NASA Left on the Moon Teaches Us to Build | Moon-Material Simulator | NASA Space Apps 2026
```

Alternatives:

```
Abandoned but Not Forgotten: Rebuilding NASA's Machines from Moon Dust | NASA Space Apps 2026
```

```
Can Moon Dust Make a Wrench? | Moon-Material Simulator | NASA Space Apps 2026
```

---

## Description

```
On the Moon and on Mars, there are machines NASA left behind: a lander from 1967, rovers parked by astronauts, a helicopter that flew 72 times. They're abandoned, but not forgotten. Each one still tells us what those worlds do to the things we build.

For the NASA Space Apps 2026 challenge "Abandoned but not Forgotten", we built the Moon-Material Simulator: it tells the stories of those machines, then lets you design a material from NASA's bacteria-grown bioplastic and Moon or Mars dust, and break it on screen before anyone prints it.

▶ Try it live (runs in any browser): https://md8-habibullah.github.io/moon-material-simulator/
💻 Source code (MIT): https://github.com/md8-habibullah/moon-material-simulator

WHAT IT DOES
• Stories: a Moon and Mars globe with 8 NASA machines where they still sit (Surveyor 3, the Apollo 11 laser reflector, the Apollo 15 rover, Apollo 17, Viking 1, Sojourner, Opportunity, Ingenuity), each with a NASA photo, its story, the materials lesson it taught, and a "Try it" button.
• Design: pick a binder, a soil and how the part is made; a physics model corrected by machine learning predicts 8 properties instantly, with a likely range.
• Evidence: every number says whether it is backed by real lab data, and links to the exact page and table in the source paper.
• Test: load a wrench, a shelf bracket or a shelter brick until it breaks, inside the habitat, at lunar noon or at lunar night.
• Optimize: nearly 5,000 mixes tested and ranked, most locally sourced first. It says honestly when nothing works.

THE DATA
• 1,470 measured values transcribed from NASA reports and peer-reviewed papers, each tied to its page.
• An Evidence Auditor re-found every value in its original PDF: 0 transcription errors, and 181 problems found inside the papers themselves.
• On mixes the model never saw, the compressive-strength error drops from 230% (physics alone) to 34%.

CHAPTERS
0:00 The machines NASA left behind
0:17 What they taught us
0:37 One broken wrench
0:48 A plastic grown inside bacteria
1:05 The Moon-Material Simulator
1:27 Built on NASA's own data
1:56 The science: physics + machine learning
2:32 Live demo: the wrench test
2:51 The optimizer finds a mix
3:07 Rocket nozzle and a 25-part kit
3:19 Team Dreams of X
3:37 What we build next

NASA SOURCES
• NASA Glenn, NTRS 20260007758: https://ntrs.nasa.gov/citations/20260007758
• NASA Glenn, NTRS 20260003641: https://ntrs.nasa.gov/citations/20260003641
• NASA Kennedy, NTRS 20230015024: https://ntrs.nasa.gov/citations/20230015024
• NASA Kennedy, NTRS 20240004186: https://ntrs.nasa.gov/citations/20240004186
• NASA, NTRS 20030020808: https://ntrs.nasa.gov/citations/20030020808
• Surveyor 3 parts returned by Apollo 12, NASA SP-284: https://www.nasa.gov/history/alsj/UL12Sandblast.html
• NASA spacecraft records (NSSDCA): https://nssdc.gsfc.nasa.gov/
Full source list: https://github.com/md8-habibullah/moon-material-simulator/blob/main/research/sources.csv

TEAM DREAMS OF X
Mahdin Islam Mukim (Team Lead) · Maliha Sanjana (UI/UX Designer) · Lamisa Yeasmin Nakia (Research & Storytelling Lead) · Yousuf Abdullah (AI/ML Researcher, Data Scientist: research, data analysis, the AI models, the dataset and the source papers) · Md. Habibullah Sharif (Systems Architect: the architecture and the whole app, UI/UX, 3D, simulator engine and backend)

CREDITS
All app footage is the real simulator. Photos: NASA (Apollo 12, 15 and 17; JPL Viking, Sojourner, Opportunity and Ingenuity; LRO/Arizona State University). Microscope images and concept art: NASA (public domain). Moon and Mars globes from NASA maps. Narration: AI voices (ElevenLabs). Original music made for this film. Sound effects: Pixabay. This project is not endorsed by NASA.

#NASASpaceApps #SpaceApps2026 #AbandonedButNotForgotten
```

---

## Tags

Paste into **Tags** (under YouTube's 500-character limit):

```
NASA Space Apps, Space Apps 2026, Abandoned but not Forgotten, Moon-Material Simulator, Dreams of X, Surveyor 3, Apollo, lunar rover, Ingenuity, Opportunity rover, moon dust, lunar regolith, in-situ resource utilization, ISRU, bioplastic, NASA Glenn, Artemis, space manufacturing, materials science, machine learning, three.js, hackathon
```

---

## Settings

| Setting | Choose |
| --- | --- |
| Thumbnail | Upload `thumbnail.jpg` |
| Audience | **No, it's not made for kids** (it is suitable for them, but this is the setting for a general-audience pitch) |
| Visibility | **Public**, or **Unlisted** if you want it hidden from search until judging. Both open without sign-in, which Space Apps needs. Never **Private**: judges can't open it. |
| Category | Science & Technology |
| Video language | English |
| Caption certification | None of these: the content has never aired on TV in the U.S. |
| Subtitles | Subtitles → Add language → English → Upload file → **With timing** → `captions_en.srt` |
| Altered or synthetic content | **No**. The narration is an AI voice, but it doesn't imitate a real person, and nothing shows realistic events that didn't happen. The team photos are real and unaltered. The description says the voice is AI anyway. |
| Licence | Standard YouTube Licence |
| Comments | On |

**End screen:** skip it. The film's last card already shows the app link, the QR code (bottom left) and the team names
(right), and YouTube's end-screen elements would cover them.

---

## Pinned comment

```
▶ Meet the machines NASA left behind, then try to rebuild their parts from Moon dust: https://md8-habibullah.github.io/moon-material-simulator/
```

---

## After uploading

Swap the old pitch link (`https://youtu.be/1Gtmq5XUytc`, the earlier October video) for the new one in these places:

1. `README.md`, at the top (two links: the text link and the thumbnail)
2. `docs/demo_script.md`, line 3
3. `frontend/src/lib/catalog.js`, `VIDEO_URL` (this drives the "Watch the pitch" buttons in the app)

Then put the same link in the Space Apps project page's video field.

## Before you publish, check

- Watch it once with sound, start to end.
- The thumbnail and subtitles show up in the YouTube preview.
- The live-app link in the description opens the simulator.
