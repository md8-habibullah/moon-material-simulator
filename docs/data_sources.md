# NASA data sources

[← Back to README](../README.md)

Every NASA source the simulator uses, and exactly how. All are public; NASA material is a U.S. Government work.

## 1. NASA Glenn: "Under the Microscope: NASA-Made Material for Moon Manufacturing"

NASA image article, 29 September 2026. <https://www.nasa.gov/image-article/nasa-made-material-moon-manufacturing/>

- **What it says:** NASA Glenn mixed a biodegradable plastic, which bacteria can produce from crew waste or CO₂, with
  simulated Moon and Mars dust. Target uses are structural brackets, wrenches and chairs. Samples are being tested in
  Glenn's Lunar Environment Structural Test Rig and will fly on MISSE-23.
- **How we use it:** it defines the project: the hero binder (bacterial bioplastic), the "made on site" logic in the
  mission calculator, and the wrench, bracket and chair uses in the optimizer.

## 2. NTRS 20260007758: "Biosynthesized Thermoplastic/Regolith Composites for Closed-Loop In-Space Manufacturing"

A. Christy, NASA Glenn, ACS Fall 2026. <https://ntrs.nasa.gov/citations/20260007758>

- **Identifies the plastic** as poly(3-hydroxybutyrate), PHB, tested with five simulants: JEZ-1, LHS-1, LMS-1, LSP-2
  and MGS-1.
- **Slide 17, tensile strength (injection molded):** 15 points (neat PHB 29.4 MPa; 16–24 MPa at 20–80 wt%). Used to
  fit PHB's tensile curve and as validation points.
- **Slide 9, decomposition temperature:** 21 points (lunar simulants about 272–283 °C; Martian ones drop to about
  260–270 °C because of iron). Used to fit the decomposition-temperature model.
- **Slide 9, crystallinity:** falls from 66% to about 27% with loading. Drives the micrograph view.
- **Abstract:** launch prices "from $4,000 to more than $1 million per kg". Used for the presets in the mission
  calculator.
- **Other findings shown in the app:** faster crystallisation with regolith (hot-stage microscopy), and survival at
  12 K in vacuum for 24 h (LESTR). NASA lists "computational modeling to predict materials performance" as a next step.

Chart values were read by eye from the slides and are marked approximate in the CSV.

## 3. NTRS 20260003641: "Polymer/Regolith Composites for In-Space Manufacturing on the Moon and Mars"

A. Christy, M. Ranaiefar, W. Fuchs, NASA Glenn, 2026. <https://ntrs.nasa.gov/citations/20260003641>

- Processing routes (compression molding up to 80 wt%, injection molding, filament extrusion, 3D printing). This
  sets our 0–80 wt% range and the process pipeline in the app.

## 4. NTRS 20230015024: "Selection, Production, and Properties of Regolith Polymer Composites for Lunar Construction"

Gelino et al., NASA Kennedy Space Center Swamp Works with SpaceFactory and LERA, 2023.
<https://ntrs.nasa.gov/citations/20230015024>

- **Appendix Table 8:** room-temperature and 77 K properties of PHA/PHB, PLA, PEEK and LDPE (tensile, modulus,
  elongation, HDT, Tg, Tm). Used as binder baselines and cryogenic ratios.
- **Tables 2–4:** 18 measured results for 3D-printed LHS-1 + PLA and BP-1 + PLA at 70–85 wt% target loadings
  (actual 61.5–78 wt% by TGA/ash): tensile, compressive and modulus in 0° and 90° print directions. Used to calibrate
  and validate PLA composites.
- **Drying procedure** (simulant dried at 204 °C) is shown in the process pipeline.

## 5. NTRS 20240004186: "Selection, Production and Properties of Regolith Polymer Composite for Lunar Construction"

NASA Kennedy presentation, 2024. <https://ntrs.nasa.gov/citations/20240004186>. Background on printing
regolith-polymer composites for lunar infrastructure.

## 6. NASA Technical Reports Server API

<https://ntrs.nasa.gov/api/citations/search>

- `scripts/export_frontend.py` saves results for six queries (e.g. "regolith polymer composite",
  "polyhydroxybutyrate") into `frontend/src/generated/ntrs_snapshot.json` on every deploy, for the hosted research
  panel.
- With the backend running, `/api/research` searches NTRS live.

## Not NASA data (and labelled as such)

- **Synthetic training set:** generated from the calibrated physics model.
- **Approximate oxide compositions** of the three soil types, typical published simulant values, rounded.
- **Estimates:** compressive strength, thermal conductivity and density of binders; PEEK/LDPE composite constants.
