# Global submission on spaceappschallenge.org: copy-paste answers

Where: your team page on spaceappschallenge.org → **Project** tab (it appears 14 Nov, 9:00 a.m. Dhaka time).
Deadline: **Sunday 15 Nov 2026, 11:59 p.m. Dhaka time.** Only the last saved version is judged.
Rules checked against the official 2026 Project Submission Guide
(https://www.spaceappschallenge.org/resources/project-submission-guide/).

Copy the text between the dashed lines into each box. This folder is git-ignored; it never goes to GitHub.

---

## Before you start (5 minutes)

1. **Upload the 30-second demo to YouTube.** The Project Demo must be a video of **30 seconds or less**
   (or at most 7 slides). Longer demos are not eligible for Global Judging, so the 3:59 film can't go in this field.
   File: `moon-material-simulator/video/film/renders/moon-material-simulator_demo30.mp4` (29.5 s, 1080p, English,
   burned-in captions). Set it to **Public** or **Unlisted** (both open without sign-in), then open the link in a private
   window to check it plays. YouTube title and description are at the end of this file.
2. **Check the team.** Every member must be a confirmed participant at the same Local Event (Dhaka).
3. **Check ages.** Demos and projects may not show anyone under 18. The 30-second demo shows names only, no photos.
   The 4-minute film shows team photos: link it only if all five of you are 18 or older.
4. **Coordinate.** One person edits at a time (the page has an edit lock, and another member can overwrite unsaved
   changes). Press **Save Progress** often.

---

## Project Name

----------------------------------------------------------------
Moon-Material Simulator
----------------------------------------------------------------

## High-Level Project Summary

----------------------------------------------------------------
Moon-Material Simulator is a free browser app for the challenge "Abandoned but not Forgotten". It tells the stories of eight NASA machines still on the Moon and Mars, then lets you rebuild one of their parts from local dust and break it in 3D. You design a composite of Moon or Mars dust and plastic, including the bacteria-grown bioplastic NASA Glenn showed in 2026, and a physics model corrected with 1,470 audited lab values predicts eight properties, each linked to the NASA report or paper behind it. It helps engineers choose a mix before a single sample is printed, and helps students, teachers and space fans learn from NASA's real data.
----------------------------------------------------------------

## Link to Project Demo

----------------------------------------------------------------
https://youtu.be/kRjf5DvXlKA
----------------------------------------------------------------

## Link to Final Project

----------------------------------------------------------------
https://md8-habibullah.github.io/moon-material-simulator/
----------------------------------------------------------------

## Detailed Project Description

----------------------------------------------------------------
THE CHALLENGE: ABANDONED BUT NOT FORGOTTEN
NASA left machines on the Moon and Mars. We tell eight of their stories: Surveyor 3, the Apollo 11 laser reflector, the Apollo 15 rover, Apollo 17's lander and its taped fender on the Moon; Viking 1, Sojourner, Opportunity and Ingenuity on Mars. Each one is also a materials experiment that never ended. Apollo 12 brought pieces of Surveyor 3 home after 31 months on the Moon, and apart from paint darkened by dust and sunlight, nothing had seriously failed. Apollo 17 fixed a broken fender with maps and tape, because there are no spare parts on the Moon.

THE PROBLEM
A broken tool on the Moon can mean a resupply launch at up to $1 million per kg (NASA Glenn, NTRS 20260007758). In September 2026 NASA Glenn showed a material that could be made on site: a biodegradable plastic (PHB) grown inside bacteria fed with CO2 or crew waste, mixed with simulated Moon and Mars dust, for brackets, wrenches and chairs. The open question is which mix to make. You can't test every combination on Earth, and you can't afford to get it wrong on the Moon.

WHAT IT DOES
A free simulator that runs in any browser, in five steps:
- Learn: spin a Moon or Mars globe built from NASA maps and open a machine's story: NASA photo, what it did, why it is still there, the materials lesson and NASA sources. A "Try it" button rebuilds one of its parts from local dust.
- Design: pick a binder (NASA's bacterial PHB, PLA, PEEK, LDPE, PEI or PPSU), a soil (lunar highlands, lunar mare, Martian) and a process (printing, injection molding, hot pressing, sintered brick); set regolith up to 92.5%, basalt fibre, grain size and temperature. Eight properties update live with uncertainty, each marked "lab-backed" or "physics estimate". One click shows the real measurements behind a number, down to the table cell in the paper.
- Test: orbit the 3D microstructure, watch it print layer by layer, then load a wrench, a shelf bracket or a shelter brick until it breaks, in the habitat, at lunar noon or lunar night. It reports the breaking load, the safety factor and whether the part bends or snaps.
- Optimize: choose a use (wrench, bracket, chair, lunar wall panel, Mars shelter block, thruster nozzle). It tests about 5,000 mixes and ranks them, most locally sourced first. It says honestly when nothing works: no plastic survives a thruster nozzle.
- Plan: compare up to four formulas and estimate the launch mass and cost saved by printing parts on site.

HOW IT WORKS
We transcribed 1,470 values from 11 sources (5 NASA reports, 6 peer-reviewed or preprint studies), each tied to its page, table, row and column. Our Evidence Auditor re-found every value in its source PDF: 0 transcription errors, and 181 problems documented inside the papers themselves (swapped 0/90 degree values, MPa written for GPa, an impossible -273 C glass transition). A physics model calibrated on NASA data is corrected by a Gaussian process trained on 152 real measurements from 7 studies. Tested on mixes the model never saw, the average compressive-strength error falls from 230% (physics alone) to 34%, stiffness from 65% to 19%, density from 16% to 5%, thermal conductivity from 32% to 7%. The uncertainty is calibrated: 90% of held-out mixes fall inside the 90% band. Honest limit: 152 measurements is a small, patchy dataset, so where there is no lab data near a mix, the app says "physics estimate". Use it to explore and shortlist, not as qualified design values.

BENEFITS AND WHO IT IS FOR
Engineers and mission planners can choose a mix before printing a single sample, and see how sure the prediction is and which lab data supports it. Just as much, it is for students, teachers and anyone who loves rockets and space: every number links to the NASA report or paper it comes from, so it works as a classroom tool. It is free, needs no installation or account, and is open source.

WHAT WE HOPE TO ACHIEVE
Turn what the machines we left behind taught us into better choices for the next things we build on the Moon and Mars: fewer kilograms launched, fewer failed parts, and data anyone can check. Next: a Moon site picker using an open lunar regolith database, flexural strength as a ninth property, more lab data for the sparse binders and processes, Mars-specific validation, and a comparison with NASA's MISSE-23 flight results once they are published.

TOOLS, LANGUAGES AND SOFTWARE
JavaScript (React, Vite, three.js, Chart.js) in the browser, with the models exported to run client-side (no server needed); Python (FastAPI, scikit-learn, SciPy, NumPy, pandas, PyMuPDF) for the evidence pipeline, models and optional API; GitHub Actions and GitHub Pages for tests and hosting; HyperFrames for the videos. No hardware. Open source under the MIT licence.

LINKS
- Live app: https://md8-habibullah.github.io/moon-material-simulator/
- Source code and documentation: https://github.com/md8-habibullah/moon-material-simulator
- Full 4-minute story film: https://youtu.be/Bub3y_H-RUI

TEAM DREAMS OF X
Five friends, one team: Mahdin Islam Mukim, Maliha Sanjana, Lamisa Yeasmin Nakia, Yousuf Abdullah and Md. Habibullah Sharif. We researched, designed, built and tested it together.
----------------------------------------------------------------

(If any team member is under 18, delete the "Full 4-minute story film" line, because that film shows team photos.)

## Use of Super Intelligence (SI)

----------------------------------------------------------------
- Claude (Anthropic), through Claude Code: a coding and writing assistant. It helped us write and debug the app (React/three.js frontend, Python backend, models, evidence auditor), transcribe values from the public NASA reports and open-access papers listed in our references into CSV files, draft the documentation, and build the videos in HyperFrames (HTML-to-video). Every transcribed value was re-checked against its source PDF by our auditor, and we reviewed and tested all code and text. This is acknowledged in the project's README (section "Use of AI").
- ElevenLabs (AI text-to-speech): the narration voice in the 4-minute film, reading our own script; this is stated in its YouTube description and its file metadata. The 30-second demo uses an AI voice cloned from team member Md. Habibullah Sharif's own voice, with his consent (F5-TTS, open source, run locally), reading our script; this is credited on screen, in the description and in the file metadata. Whisper speech recognition (open source, run locally) timed the captions to the words.
- Inside the app, our own machine-learning models: a scikit-learn Random Forest trained on data generated by our physics model, and a Gaussian-process correction trained on 152 real lab measurements from 7 studies. They run in the browser.
- No AI-generated images, video footage or music, and we did not use or modify NASA logos or mission insignia: photos and maps are NASA's, app footage is our own screen recordings and 3D renders, the music is synthesised by our own code, and the sound effects come from Pixabay.
----------------------------------------------------------------

## NASA Data

(To be eligible for a Global Award you must use at least one NASA data source or resource. We used twelve.)

----------------------------------------------------------------
1. NASA Glenn, "Under the Microscope: NASA-Made Material for Moon Manufacturing" (2026). https://www.nasa.gov/image-article/nasa-made-material-moon-manufacturing/ — Defines the project: the bacterial bioplastic binder and the target uses (bracket, wrench, chair); its micrographs inspire the app's polarised-light view.
2. NTRS 20260007758, Christy et al., NASA Glenn, "Biosynthesized Thermoplastic/Regolith Composites" (2026). https://ntrs.nasa.gov/citations/20260007758 — PHB with five Moon/Mars simulants: tensile strength and decomposition temperature fit and validate the model; launch-cost range for the mission calculator.
3. NTRS 20260003641, Christy et al., NASA Glenn, "Polymer/Regolith Composites for In-Space Manufacturing" (2026). https://ntrs.nasa.gov/citations/20260003641 — Processing routes and the 0 to 80 wt% loading range used in the simulator.
4. NTRS 20230015024, Gelino et al., NASA Kennedy Swamp Works (2023). https://ntrs.nasa.gov/citations/20230015024 — Binder properties at room temperature and 77 K, plus 18 measured 3D-printed PLA + LHS-1/BP-1 results used to calibrate and validate.
5. NTRS 20240004186, NASA Kennedy, regolith polymer composite presentation (2024). https://ntrs.nasa.gov/citations/20240004186 — Values transcribed and audited into our evidence dataset.
6. NTRS 20030020808, NASA, "Predictions for Radiation Shielding Materials" (2003). https://ntrs.nasa.gov/citations/20030020808 — Polyethylene/regolith values transcribed and audited into our evidence dataset.
7. NASA Technical Reports Server (NTRS) API. https://ntrs.nasa.gov/api/citations/search — In-app search of related NASA reports.
8. NASA Space Science Data Coordinated Archive (NSSDCA). https://nssdc.gsfc.nasa.gov/nmc/ — Mission facts and sources for the eight machine stories.
9. NASA Image and Video Library and Planetary Photojournal. https://images.nasa.gov and https://photojournal.jpl.nasa.gov — Photos of the eight machines (AS12-48-7134, AS11-40-5948, AS15-86-11603, AS17-137-20979, PIA12920, PIA00381, PIA04318, PIA20285, PIA24648), credited in the app.
10. Apollo Lunar Surface Journal. https://www.nasa.gov/history/alsj/UL12Sandblast.html — Surveyor 3 story: the parts Apollo 12 brought home and what they showed.
11. NASA SVS CGI Moon Kit (Lunar Reconnaissance Orbiter). https://svs.gsfc.nasa.gov/4720 — Texture of the 3D Moon globe and the Moon in our videos.
12. NASA 3D Resources. https://science.nasa.gov/3d-resources/ — Texture of the 3D Mars globe.
----------------------------------------------------------------

## Space Agency Partner Data and Other References

----------------------------------------------------------------
Space agency partner data: none. We did not use data from partner agencies (ESA, JAXA, CSA, ISRO and others); all agency data is NASA's, listed above.

Peer-reviewed and preprint studies (measured values in our evidence dataset; all open access, CC BY 4.0)
- Li H. et al., Polymers 12(8):1724, 2020 (PLA + CLRS-1 lunar simulant). https://doi.org/10.3390/polym12081724
- Alexander-Roy L., Ranaiefar M., Singh M., Halbig M., Polymers 17(19):2685, 2025 (basalt moon dust + PLA). https://doi.org/10.3390/polym17192685
- Torre R., Ferro C.G., Bono L., Cowley A., Applied Sciences 15(2):679, 2025 (regolith-rich PEEK bricks). https://doi.org/10.3390/app15020679
- Moazen S. et al., Acta Astronautica 237:409-420, 2025 (LDPE + LMS-1D). https://doi.org/10.1016/j.actaastro.2025.08.012
- Storozhuk I.P. et al., Polymers 18(19):2371, 2026 (PPSU/PEI + up to 92.5 wt% lunar simulant). https://doi.org/10.3390/polym18192371
- Finite-Element Modeling of Additively Manufactured Regolith-Filled PEEK, Preprints.org 202606.1562 v1, 2026 (simulation values, marked as not peer reviewed). https://doi.org/10.20944/preprints202606.1562.v1
- Gasteiner L., Murdoch N., D'Angelo O., "An Open Database of Lunar Regolith and Simulants Properties", arXiv 2602.03829, 2026 (background). https://arxiv.org/abs/2602.03829

Software (open-source licences)
- React, Vite, three.js, Chart.js, lucide, FastAPI, scikit-learn, SciPy, NumPy, pandas, PyMuPDF, GSAP, HyperFrames.

Media
- Photos, maps and concept art: NASA (public domain U.S. Government work), credited where they appear.
- Narration: the 30-second demo in an AI clone of Md. Habibullah Sharif's voice (F5-TTS); the 4-minute film in an ElevenLabs AI voice reading our own script. Music: synthesised by our own code. Sound effects: Pixabay (Pixabay Content License).
- No copyrighted material is used without permission. This project is not endorsed by NASA.

Full source list with licences and file hashes: https://github.com/md8-habibullah/moon-material-simulator/blob/main/research/sources.csv
----------------------------------------------------------------

## Image (optional)

Upload `moon-material-simulator/video/youtube/thumbnail.jpg` (1280×720, NASA photo of Surveyor 3, no team photos),
or a screenshot of the app.

## Submit

1. Tick the Terms and Conditions box.
2. Tick the box confirming the work is your own original work.
3. Click **Submit for Judging**. The button stays inactive until every required field is filled.
4. Look for the confirmation banner. You can edit and resubmit until the deadline; the last saved submission counts.

---

## YouTube: the 30-second demo

Title, description, tags, thumbnail, subtitles, settings and share posts:
`moon-material-simulator/video/youtube/demo30/YOUTUBE.md`.
