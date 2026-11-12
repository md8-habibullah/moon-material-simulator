# Evidence extraction spec

Every measured value in the evidence dataset must be **traceable to an exact spot in a source PDF**. The Evidence Auditor
(`backend/audit/`) re-finds each value in the PDF using these anchors. It never edits data. It writes comments only.

Source PDFs live in `research/pdfs/` (not committed to git; see `research/sources.csv` for URLs and hashes).

## Output files (one pair per source)

- `research/extraction/<SOURCE_ID>.csv`: measurements, schema below
- `research/extraction/<SOURCE_ID>_issues.md`: problems found in the source itself (see "Source issues")

## CSV schema (UTF-8, comma-separated, header row exactly as listed)

| Column | Meaning |
| --- | --- |
| `source_id` | e.g. `S003` |
| `page` | **PDF page index, 1-based** (as used by `pdftotext -f N -l N`), *not* the printed page number |
| `anchor_type` | `table`, `text` or `figure` |
| `anchor_id` | As printed: `Table 3`, `Figure 5`, `Slide 17`. For text, the section heading. |
| `row_label` | The row's label exactly as printed (e.g. `70/30 BP-1/PLA`). Empty for text. |
| `col_label` | The column header exactly as printed, joined to one line (e.g. `Avg Ultimate Flexural Strength (MPa)`). Empty for text. |
| `value_raw` | The number **exactly as printed** (e.g. `30.17`, `7.0`, `1.2E-5`). Charts: your digitized number. |
| `value` | Numeric value in the printed unit |
| `std` | Standard deviation / ± if given, else empty |
| `n` | Number of specimens if given, else empty |
| `unit_raw` | Unit as printed (`MPa`, `GPa`, `g/cm3`, `%`, `°C`, `W/(m·K)`, …) |
| `binder` | Polymer: `PLA`, `PHB`, `PEEK`, `PEKK`, `LDPE`, `HDPE`, `UHMWPE`, `MDPE`, `PE`, `PP`, `PEI`, `PPSU`, `epoxy`, … |
| `binder_grade` | Commercial grade / supplier if stated |
| `filler` | Simulant name as printed (`LHS-1`, `BP-1`, `CLRS-1`, `LMS-1D`, `MGS-1`, `JSC-1A`, basalt moon dust, …). `none` for neat polymer. |
| `soil_type` | `lunar_highlands`, `lunar_mare`, `lunar_generic`, `martian`, `basalt`, `none` |
| `regolith_wt_target` | Filler wt% as designed (0–100). Convert ratios: `80:20 LHS-1:PLA` means 80. |
| `regolith_wt_actual` | Measured filler wt% (TGA/ash) if the source gives it |
| `regolith_vol` | Filler vol% if given |
| `fiber_wt` | Fibre wt% if any |
| `d50_um` | Median filler particle size, µm, if stated for this material |
| `process` | `FFF` (filament printing), `pellet_AM` (pellet/FGF printing), `injection`, `compression`, `hot_press`, `cold_sinter`, `sinter`, `FEM` (simulation) |
| `orientation` | Print/raster orientation as printed (`0°`, `90°`, `XY`, …) |
| `infill_pct` | Infill % if given |
| `environment` | `air`, `vacuum`, `TVAC`, `cryo` (where the specimen was *made or conditioned* or tested, as stated) |
| `temperature_c` | Test temperature °C (room temperature = 23 if stated as RT/ambient). 77 K = −196. |
| `property` | Controlled vocabulary below |
| `test_standard` | e.g. `ASTM D638` if stated |
| `origin` | `experimental` or `simulation` |
| `extraction` | `table`, `text`, or `chart_digitized` |
| `confidence` | `high` (printed number), `medium` (clear chart, read to within about 2% of axis span), `low` (crowded or ambiguous chart) |
| `notes` | Anything a checker needs: processing details, which lab, conditioning, "value read from bar top", axis range used… |

### Property vocabulary

`tensile_strength`, `tensile_modulus`, `elongation_at_break`, `yield_strength_tensile`, `compressive_strength`,
`compressive_yield_strength`, `compressive_modulus`, `flexural_strength`, `flexural_modulus`, `shear_strength`,
`shear_modulus`, `impact_strength`, `hardness_shore_d`, `density`, `porosity`, `water_absorption`,
`thermal_conductivity`, `cte`, `glass_transition`, `melting_temp`, `crystallization_temp`, `decomposition_temp`,
`crystallinity`, `hdt`, `storage_modulus`, `melt_flow_index`, `viscosity`. If none fits, use a clear snake_case name and
explain it in `notes`.

## Rules

1. **Only real numbers from the source.** Never infer, average or compute a value unless the source prints it. Ranges
   ("16–23 MPa") go in `notes`, not `value`.
2. **Tables first, then text, then charts.** Read charts only when the number appears nowhere as text. To read a
   chart, render the page (`pdftoppm -f N -l N -r 150 -png file.pdf out`) and look at it. Record the axis range you used in
   `notes`. Use `confidence` `medium` or `low`.
3. **One row per number.** A table cell with 0° and 90° results gives two rows.
4. **Keep both the experimental and the simulation values, labelled with `origin`.** Do not mix them up.
5. **Literature-comparison tables** (values a paper quotes from *other* papers): include them only with
   `notes` starting `CITED:` plus the citation, so they can be traced or excluded.
6. **Neat polymer baselines matter** (filler `none`, wt 0). Always capture them.
7. `value_raw` must be copied character-for-character so the auditor can find it on the page.

## Source issues (`<SOURCE_ID>_issues.md`)

List every problem **inside the source itself**, with the page and a short verbatim quote:
- text contradicts its own table or figure (swapped values, different numbers)
- wrong or inconsistent units (MPa vs GPa)
- table rows or columns that don't add up, duplicated or ambiguous labels
- values that can't be tied to a specific composition

Format: `- p.<page> <anchor> | <type> | "<quote>" vs "<quote>" | <one-line explanation>`
