# Review: Moon-Material Simulator, 240 Seconds of Glory (v1)

Length 223.4 s (3:43), 1920 × 1080, 30 fps. Output: `renders/moon-material-simulator_240s.mp4`.

## Creative calls

- **Story:** the script in `../README.md` (the wrench that breaks, then holds). No alternative storylines were built; the
  script was already agreed.
- **Look:** the product's own mission-console style (space black, cyan data, orange load), with a HUD bar (chapter and
  mission clock). Corner brackets and "REAL APP FOOTAGE" tags appear only over real recordings.
- **Footage:** every app shot is the real app, recorded deterministically at 30 fps (`tools/capture.mjs`): the clock is
  frozen and stepped one frame at a time, so the 3D is smooth even on this machine.
- **NASA material:**
  - NASA Glenn microscope images (credit NASA).
  - A Moon rendered from NASA LROC colour and LOLA elevation maps (SVS CGI Moon Kit).
  - NASA concept art.
  - Real PDF pages from `research/pdfs`.
- **Voice:** Kokoro, local and free, with three voices: am_michael (S1, S2, S6, S7), af_heart (S3, S4) and bm_george (S5),
  at 0.9× speed. HeyGen voices needed a paid plan, and the user chose the free local voice.
- **Captions:** the script's own words, timed by aligning them to a Whisper (base.en) transcript of each voice file.
- **Music:** an original score synthesised in `tools/music.py` (the user chose generated music). Sound effects come from
  the bundled Pixabay library (no attribution required).

## Measured, looked at, and not checked

- **Measured:**
  - `hyperframes check` passes, with 0 errors.
  - Music loudness is −13.3 LUFS before the 0.14 bed gain.
  - Effect peaks are aligned to their pictures.
  - Caption timing comes from the voice transcript.
- **Looked at:** the review beat sheets, the seam strips and the targeted snapshots for every scene.
- **Not checked by ear:** nobody heard the mix. The voice, the music and the effect levels were measured, not listened
  to. Play it once before submitting.

## Weakest shots, and what to do with more time

- **S3 (solution):** the slider footage is small UI behind the isolated results panel. A tighter recording of just the
  results card updating would read better.
- **S2 opening:** the first 0.3 s is an almost empty starfield before the microscope images land.
- **The voice:** the local voice is clear but synthetic. Re-recording with the team's own voices, following the
  script's cast list, would add authenticity and Teamwork points. Drop WAVs into `assets/voice/<scene>.wav`, run
  `npx hyperframes transcribe` on each one and rename the result to `<scene>.asr.json`, then run `python3 tools/build.py`
  and the film retimes itself.

## Warnings kept on purpose

- **`nested_media_start_basis_ambiguous`:** scene videos are timed locally in their scene, as intended.
- **`duplicate_media_discovery_risk`:** the 25-part grid deliberately repeats three thumbnails.
- **`gsap_repeated_fromto_without_baseline`:** these are the count-up number proxies.

## Rebuild

```bash
python3 tools/build.py                          # scenes + index from vo.json and the voice timings
../../backend/.venv/bin/python tools/music.py   # re-score to the current timing
python3 tools/build.py                          # pick up the new music length
npx hyperframes check
npx hyperframes render --workers 2 -o renders/moon-material-simulator_240s.mp4
```
