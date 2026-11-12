# SPEC: Moon-Material Simulator, 240 Seconds of Glory

```text
GOAL:    a judge finishes convinced that a working tool, built on NASA's own data and honest about its
         error, can pick the right Moon-made material: the wrench that broke is fixed by the end.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps.
TIME:    target ≤ 238 s (Space Apps cap 240 s) = ≤ 7,140 frames. The voice-over is the clock:
         every scene starts 0.35 s before its first word and ends 0.45 s after its last.
LOOK:    the medium is the product's own mission console: deep-space ground #02040a with a seeded
         starfield photo (bg/stars.jpg, drifting 3°/s equivalent: 40 px over a scene), real app
         footage, real NASA images and real PDF pages.
         ink #e7edf7; muted #8f9cb2; data/UI accent cyan #7fe3ff; action/load/heat orange #ff9a4d;
         pass green #2fd39b; fail red #ff6b6b; caution amber #ffb547. One accent word per line.
         Display: Space Grotesk 700 (the app's face), 96 px heroes at -2% tracking, 64 px heads;
         body Space Grotesk 500 34 px; data and source lines JetBrains Mono 22-26 px, +14% tracking.
         Glow only where the product glows (3D footage, stress colours, HUD lines): text-shadow ≤ 24 px.
         Panels: rgba(8,16,30,.78), 1 px rgba(127,227,255,.28) border, radius 18 px.
OBJECTS: the wrench, bracket and brick are the app's own 3D parts (recorded, never redrawn);
         the Moon is NASA LROC colour + LOLA elevation; documents are rendered from the real PDFs;
         NASA Glenn's microscope photos of the material; the Dreams of X logo file.
MOTION:  arrivals expo.out 0.5-0.7 s; camera moves power2.inOut 0.8-1.2 s; exits power3.in 0.25 s;
         words 0.07 s apart; numbers count up in 1.2-1.6 s then hold; one hero move per shot.
TRANSITIONS: dip cut (S1→S2), zoom through a UI element (S3), whip with 14 px blur (S4→S5, S6b→S6c),
         iris from the result (S5→S6a), colour flood to black (S6c→S7). Hard cuts only inside scenes.
SOUND:   HeyGen voice per scene; one music bed at 0.12-0.14 under voice, swelling in the gaps;
         effects only on visible causes: crack (wrench, brick), whoosh (scene seams), pop (numbers
         and tiles landing), click (UI clicks in footage).
CAPTIONS: burned in, Space Grotesk 600 44 px on a 36% black scrim, 3-5 words per group,
         96 px from the bottom; all scene text stays above y = 880.
SHOTS:   see compositions/ (one file per scene, s1 ... s7) and video/README.md for the words.
BANNED:  invented UI or numbers; a title over a dimmed screenshot; three cards in a row with no
         cause; everything fading up at once; titles drifting after they land; corner brackets as
         decoration (they appear only around real footage, labelled REAL APP FOOTAGE);
         the NASA insignia; "R² 0.99".
QA:      t≈4 s wrench snaps on the word "broken"; S4 NTRS ids readable ≥ 2 s; S5 "117 / 119" holds
         ≥ 1 s; S6b "Design load held" lands with the chime; last frame shows URL + QR ≥ 4 s.
```
