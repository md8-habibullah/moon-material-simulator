# Final local submission: copy-paste answers

Form: https://www.nasaspaceappsbd.com/participant/final-submission
Copy the text between the lines into each box. Everything here is checked against the repo and the live links.

---

## 03 Project

### Project name

Moon-Material Simulator

### High-level summary (limit 1000)

----------------------------------------------------------------
Moon-Material Simulator is a free browser app for the challenge "Abandoned but not Forgotten". It tells the stories of eight NASA machines still on the Moon and Mars, then lets you rebuild one of their parts from local dust and break it in 3D. You design a composite of Moon or Mars dust and plastic, including the bacteria-grown bioplastic NASA Glenn showed in 2026, and a physics model corrected with 1,470 audited lab values predicts eight properties, each linked to the NASA report or paper behind it. It helps engineers choose a mix before a single sample is printed, and helps students, teachers and space fans learn from NASA's real data.
----------------------------------------------------------------

### Project details (limit 5000)

Replace the old team-recruitment text in this box with this:

----------------------------------------------------------------
THE CHALLENGE: ABANDONED BUT NOT FORGOTTEN
NASA left machines on the Moon and Mars. We tell eight of their stories: Surveyor 3, the Apollo 11 laser reflector, the Apollo 15 rover, Apollo 17's lander and its taped fender on the Moon; Viking 1, Sojourner, Opportunity and Ingenuity on Mars. Each one is also a materials experiment that never ended. Apollo 12 brought pieces of Surveyor 3 home after 31 months on the Moon, and apart from paint darkened by dust and sunlight, nothing had seriously failed. Apollo 17 fixed a broken fender with maps and tape, because there are no spare parts on the Moon.

THE PROBLEM
A broken tool on the Moon can mean a resupply launch at up to $1 million per kg (NASA Glenn, NTRS 20260007758). In September 2026 NASA Glenn showed a material that could be made on site: a biodegradable plastic (PHB) grown inside bacteria fed with CO2 or crew waste, mixed with simulated Moon and Mars dust, for brackets, wrenches and chairs. The open question is which mix to make. You can't test every combination on Earth, and you can't afford to get it wrong on the Moon.

WHAT WE BUILT
A free simulator that runs in any browser, in five steps:
- Learn: spin a Moon or Mars globe built from NASA maps and open a machine's story: NASA photo, what it did, why it is still there, the materials lesson and NASA sources. A "Try it" button rebuilds one of its parts from local dust.
- Design: pick a binder (NASA's bacterial PHB, PLA, PEEK, LDPE, PEI or PPSU), a soil (lunar highlands, lunar mare, Martian) and a process (printing, injection molding, hot pressing, sintered brick); set regolith up to 92.5%, basalt fibre, grain size and temperature. Eight properties update live with uncertainty, each marked "lab-backed" or "physics estimate". One click shows the real measurements behind a number, down to the table cell in the paper.
- Test: orbit the 3D microstructure, watch it print layer by layer, then load a wrench, a shelf bracket or a shelter brick until it breaks, in the habitat, at lunar noon or lunar night. It reports the breaking load, the safety factor and whether the part bends or snaps.
- Optimize: choose a use (wrench, bracket, chair, lunar wall panel, Mars shelter block, thruster nozzle). It tests about 5,000 mixes and ranks them, most locally sourced first. It says honestly when nothing works: no plastic survives a thruster nozzle.
- Plan: compare up to four formulas and estimate the launch mass and cost saved by printing parts on site.

HOW IT WORKS
We transcribed 1,470 values from 11 sources (5 NASA reports, 6 peer-reviewed or preprint studies), each tied to its page, table, row and column. Our Evidence Auditor re-found every value in its source PDF: 0 transcription errors, and 181 problems documented inside the papers themselves (swapped 0/90 degree values, MPa written for GPa, an impossible -273 C glass transition). A physics model calibrated on NASA data is corrected by a Gaussian process trained on 152 real measurements from 7 studies. Tested on mixes the model never saw, the average compressive-strength error falls from 230% (physics alone) to 34%, stiffness from 65% to 19%, density from 16% to 5%, thermal conductivity from 32% to 7%. The uncertainty is calibrated: 90% of held-out mixes fall inside the 90% band. Honest limit: 152 measurements is a small, patchy dataset, so where there is no lab data near a mix, the app says "physics estimate". Use it to explore and shortlist, not as qualified design values.

WHO IT IS FOR
Engineers and mission planners who want to choose a mix before printing a single sample, and just as much students, teachers and anyone who loves rockets and space. Every number links to the NASA report or paper it comes from, so it works as a classroom tool too.

TECHNOLOGY
React, Vite, three.js and Chart.js in the browser, with the models exported to run client-side (no server needed); Python, FastAPI, scikit-learn, SciPy and PyMuPDF for the evidence pipeline, models and optional API; GitHub Actions and GitHub Pages for tests and hosting. Open source under the MIT licence.

WHAT WE WOULD BUILD NEXT
The same method works for Mars. Next: a Moon site picker using an open lunar regolith database, flexural strength as a ninth property, more lab data for the sparse binders and processes, and a comparison with NASA's MISSE-23 flight results once they are published.

TEAM DREAMS OF X
Five friends, one team: Mahdin Islam Mukim, Maliha Sanjana, Lamisa Yeasmin Nakia, Yousuf Abdullah and Md. Habibullah Sharif. We researched, designed, built and tested it together.

Live app: https://md8-habibullah.github.io/moon-material-simulator/
----------------------------------------------------------------

---

## 04 Links (already filled and green)

- Video: https://youtu.be/Bub3y_H-RUI
- GitHub: https://github.com/md8-habibullah/moon-material-simulator
- Project page: https://www.spaceappschallenge.org/2026/find-a-team/dreams-of-x1

---

## 05 Data used

### NASA data (click "+ Add" for each row: Dataset name | Link | How you used it)

1. NASA Glenn: "Under the Microscope: NASA-Made Material for Moon Manufacturing" (2026)
   https://www.nasa.gov/image-article/nasa-made-material-moon-manufacturing/
   Defines the project: the bacterial bioplastic binder and the target uses (bracket, wrench, chair); its micrographs inspire the app's polarised-light view.

2. NTRS 20260007758: Christy, NASA Glenn, "Biosynthesized Thermoplastic/Regolith Composites" (2026)
   https://ntrs.nasa.gov/citations/20260007758
   PHB with five Moon/Mars simulants: tensile strength and decomposition temperature fit and validate the model; launch-cost range for the mission calculator.

3. NTRS 20260003641: Christy et al., NASA Glenn, "Polymer/Regolith Composites for In-Space Manufacturing" (2026)
   https://ntrs.nasa.gov/citations/20260003641
   Processing routes and the 0 to 80 wt% loading range used in the simulator.

4. NTRS 20230015024: Gelino et al., NASA Kennedy Swamp Works (2023)
   https://ntrs.nasa.gov/citations/20230015024
   Binder properties at room temperature and 77 K, plus 18 measured 3D-printed PLA + LHS-1/BP-1 results used to calibrate and validate.

5. NTRS 20240004186: NASA Kennedy, regolith polymer composite presentation (2024)
   https://ntrs.nasa.gov/citations/20240004186
   Values transcribed and audited into our evidence dataset; background on printing regolith composites.

6. NTRS 20030020808: NASA, "Predictions for Radiation Shielding Materials" (2003)
   https://ntrs.nasa.gov/citations/20030020808
   Polyethylene/regolith values transcribed and audited into our evidence dataset.

7. NASA Technical Reports Server (NTRS) API
   https://ntrs.nasa.gov/api/citations/search
   In-app search of related NASA reports (live with the backend; a snapshot on the hosted site).

8. NASA Space Science Data Coordinated Archive (NSSDCA)
   https://nssdc.gsfc.nasa.gov/nmc/
   Mission facts and sources for the eight machine stories.

9. NASA Image and Video Library and Planetary Photojournal
   https://images.nasa.gov
   Photos of the eight machines on the story cards (Apollo frames and PIA images, credited in the app).

10. Apollo Lunar Surface Journal
    https://www.nasa.gov/history/alsj/
    Surveyor 3 story: the parts Apollo 12 brought home and what they showed.

11. NASA SVS CGI Moon Kit (Lunar Reconnaissance Orbiter)
    https://svs.gsfc.nasa.gov/4720
    Texture of the 3D Moon globe and the Moon in our banner.

12. NASA 3D Resources (Mars map)
    https://science.nasa.gov/3d-resources/
    Texture of the 3D Mars globe.

### Other space agency data

Leave empty. We did not use ESA, JAXA, CSA or ISRO data.

### Other datasets (data, libraries, APIs)

1. Li et al. 2020, Polymers 12:1724 (PLA + CLRS-1 lunar simulant)
   https://doi.org/10.3390/polym12081724
   Measured values in our evidence dataset (CC BY 4.0).

2. Alexander-Roy et al. 2025, Polymers 17:2685 (basalt moon dust + PLA, NASA Glenn co-authors)
   https://doi.org/10.3390/polym17192685
   Measured values in our evidence dataset (CC BY 4.0).

3. Torre et al. 2025, Applied Sciences 15:679 (regolith-rich PEEK bricks)
   https://doi.org/10.3390/app15020679
   Measured values in our evidence dataset (CC BY 4.0).

4. Moazen et al. 2025, Acta Astronautica 237:409-420 (LDPE + LMS-1D)
   https://doi.org/10.1016/j.actaastro.2025.08.012
   Measured values in our evidence dataset (CC BY 4.0).

5. Storozhuk et al. 2026, Polymers 18:2371 (PPSU/PEI + up to 92.5 wt% lunar simulant)
   https://doi.org/10.3390/polym18192371
   Measured values in our evidence dataset (CC BY 4.0).

6. Preprints.org 202606.1562 (2026), finite-element model of regolith-filled PEEK
   https://doi.org/10.20944/preprints202606.1562.v1
   Simulation values, marked as not peer reviewed (CC BY 4.0).

7. Open-source libraries: React, Vite, three.js, Chart.js, lucide; Python, FastAPI, scikit-learn, SciPy, NumPy, pandas, PyMuPDF
   https://github.com/md8-habibullah/moon-material-simulator
   The app, 3D views, charts, models and the PDF auditor.

---

## 06 Use of AI and references

### Use of AI

----------------------------------------------------------------
- Claude (Anthropic), through Claude Code: a coding and writing assistant. It helped us write and debug the app (React/three.js frontend, Python backend, models, evidence auditor), transcribe values from the public NASA reports and open-access papers listed under References into CSV files, draft the documentation, and build the pitch video in HyperFrames (HTML-to-video). Every transcribed value was re-checked against its source PDF by our auditor, and we reviewed and tested all code and text.
- ElevenLabs (AI text-to-speech): the narration voice in the video, reading our own script. The video description says the narration is an AI voice.
- Inside the app, our own machine-learning models: a scikit-learn Random Forest trained on data generated by our physics model, and a Gaussian-process correction trained on 152 real lab measurements from 7 studies. They run in the browser.
- No AI-generated images or music: photos and maps are NASA's, app images are our own screenshots and 3D renders, the music is synthesised by our own code, and the sound effects come from Pixabay.
----------------------------------------------------------------

### References

----------------------------------------------------------------
NASA sources
- NASA Glenn, "Under the Microscope: NASA-Made Material for Moon Manufacturing", 2026. https://www.nasa.gov/image-article/nasa-made-material-moon-manufacturing/
- Christy A. et al., "Biosynthesized Thermoplastic/Regolith Composites for Closed-Loop In-Space Manufacturing", NASA Glenn, ACS Fall 2026, NTRS 20260007758. https://ntrs.nasa.gov/citations/20260007758
- Christy A., Ranaiefar M., Fuchs W., "Polymer/Regolith Composites for In-Space Manufacturing on the Moon and Mars", NASA Glenn, 2026, NTRS 20260003641. https://ntrs.nasa.gov/citations/20260003641
- Gelino N.J. et al., "Selection, Production, and Properties of Regolith Polymer Composites for Lunar Construction", NASA Kennedy, 2023, NTRS 20230015024. https://ntrs.nasa.gov/citations/20230015024
- NASA Kennedy, "Selection, Production and Properties of Regolith Polymer Composite for Lunar Construction" (presentation), 2024, NTRS 20240004186. https://ntrs.nasa.gov/citations/20240004186
- NASA, "Predictions for Radiation Shielding Materials", 2003, NTRS 20030020808. https://ntrs.nasa.gov/citations/20030020808
- NASA Technical Reports Server API. https://ntrs.nasa.gov/api/citations/search
- NASA NSSDCA spacecraft records (Surveyor 3, Apollo 11/15/17 LM, Viking 1 Lander, Mars Pathfinder, Opportunity, Mars 2020). https://nssdc.gsfc.nasa.gov/nmc/
- Apollo Lunar Surface Journal, Surveyor 3 parts. https://www.nasa.gov/history/alsj/UL12Sandblast.html
- NASA photos AS12-48-7134, AS11-40-5948, AS15-86-11603, AS17-137-20979 (https://images.nasa.gov) and PIA12920, PIA00381, PIA04318, PIA20285, PIA24648 (https://photojournal.jpl.nasa.gov)
- NASA SVS CGI Moon Kit (LRO). https://svs.gsfc.nasa.gov/4720
- NASA 3D Resources. https://science.nasa.gov/3d-resources/

Peer-reviewed and preprint studies
- Li H. et al., Polymers 12(8):1724, 2020. https://doi.org/10.3390/polym12081724
- Alexander-Roy L., Ranaiefar M., Singh M., Halbig M., Polymers 17(19):2685, 2025. https://doi.org/10.3390/polym17192685
- Torre R., Ferro C.G., Bono L., Cowley A., Applied Sciences 15(2):679, 2025. https://doi.org/10.3390/app15020679
- Moazen S. et al., Acta Astronautica 237:409-420, 2025. https://doi.org/10.1016/j.actaastro.2025.08.012
- Storozhuk I.P. et al., Polymers 18(19):2371, 2026. https://doi.org/10.3390/polym18192371
- Finite-Element Modeling of Additively Manufactured Regolith-Filled PEEK, Preprints.org 202606.1562 v1, 2026 (not peer reviewed). https://doi.org/10.20944/preprints202606.1562.v1
- Gasteiner L., Murdoch N., D'Angelo O., "An Open Database of Lunar Regolith and Simulants Properties", arXiv 2602.03829, 2026 (background). https://arxiv.org/abs/2602.03829

Software and media
- React, Vite, three.js, Chart.js, lucide, FastAPI, scikit-learn, SciPy, NumPy, pandas, PyMuPDF (open-source licences)
- HyperFrames (video), ElevenLabs (narration voice), Pixabay sound effects (Pixabay Content License)
- Full source list with licences and file hashes: https://github.com/md8-habibullah/moon-material-simulator/blob/main/research/sources.csv
----------------------------------------------------------------

---

## 07 Declaration and agreements

- "Our project's interface is accessible, with sound and image: anyone can use it." Tick it. The app has text labels for screen readers on its buttons and 3D views, alt text on images, keyboard-usable controls, reduced-motion support, and sound that is optional. For the video, make sure the English subtitles are on YouTube: in YouTube Studio, Subtitles, upload moon-material-simulator/video/youtube/captions_en.srt.
- "Our NASA Space Apps project page is filled in and submitted on spaceappschallenge.org." Leave it unticked for now. NASA opens project submission on 14 November; tick it only after you have submitted there.
- Final box ("I have read these, and every member of my team agrees"): tick it once the team has read the terms.
