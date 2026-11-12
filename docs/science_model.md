# Science model

[← Back to README](../README.md) · Code: [`backend/utils/materials.py`](../backend/utils/materials.py)

The simulator predicts eight properties of a printed, molded or pressed **binder + regolith (+ basalt fibre)**
composite. It combines four parts:

1. A physics model calibrated on NASA measurements (sections 2-3).
2. A Random Forest that copies that model so it runs in the browser (section 4).
3. A Gaussian-process **evidence correction** learned from 152 real lab measurements in 7 studies (section 5).
4. Explicit temperature physics (section 6).

## 1. Inputs

| Input | Range | Notes |
| --- | --- | --- |
| Binder | PHB, PLA, PEEK, LDPE, PEI, PPSU | PHB is NASA Glenn's bacterial bioplastic (poly(3-hydroxybutyrate)); PEI/PPSU baselines from S008 and S003 Table 8 |
| Process | filament printing, pellet printing, injection molding, hot pressing, pressed + sintered brick | Default per binder: the route its lab data used |
| Regolith | lunar highlands, lunar mare, Martian | LHS-1/LSP-2-type, LMS-1/BP-1-type, MGS-1/JEZ-1-type simulants |
| Regolith content | 0–92.5 wt% | NASA Glenn processed PHB up to 80 wt%; S008 hot-pressed PEI up to 92.5 wt% |
| Basalt fibre | 0–15 wt% | regolith + fibre ≤ 95 wt% |
| Median grain size | 10–150 µm | |
| Operating temperature | −200 to 150 °C | 77 K = −196 °C |

## 2. Room-temperature physics

Weight fractions become volume fractions φ using particle densities (highlands 2.90, mare 3.10, Martian 2.80, basalt
fibre 2.65 g/cm³) and binder densities. Then:

| Property | Model |
| --- | --- |
| Porosity | p = 0.01 + 0.12 · v · φ_total², where v is the soil's void factor (highlands 1.0, mare 1.4 for fines, Martian 1.2 for hydrated minerals) |
| Grain bond | q = interface quality (soil) × filler affinity (binder) × size factor; size factor = 1 + 0.22 · ln(60 µm / d), clipped to 0.7–1.4 |
| Tensile strength | σ = σ_m · [r + (1 − r) · e^(−φ_r/φ₀)] · (1 − 2(p − 0.01)) + 200 · φ_f · affinity. Strength falls, then plateaus at r, scaled by q/0.85. **r and φ₀ fitted per binder** (below). |
| Stiffness | Lewis–Nielsen: E/E_m = (1 + A·B·φ) / (1 − B·ψ·φ), A = 1.5, B from grain/binder modulus ratio, ψ with max packing 0.75; × (1 − 1.5p) + 17 GPa · φ_f |
| Compressive strength | σ_c = σ_c,m · (1 + q·φ_r) · e^(−1.5 φ_r²) · (1 − 2p) + 100 · φ_f · affinity |
| Flexibility | Nielsen: ε = ε_m · (1 − φ_total^(1/3))^1.5 |
| Density | rule of mixtures × (1 − p) |
| Thermal conductivity | Maxwell–Eucken with grain conductivity (highlands 1.5, mare 2.0, Martian 1.4 W/m·K) |
| Max service temperature | HDT_m + gain · φ_total · q, capped 10 °C below the melting point (fillers nucleate crystals) |
| Decomposition temperature | T_d,m − s · Δ_max · (1 − e^(−wt/scale)); iron-rich Martian soil Δ_max = 21 °C, scale 22 wt%; mare 10/50; highlands 6/40; binder sensitivity s (PHB 1.0) |

## 3. Calibration against NASA

Constants were fitted to the NASA points in
[`backend/data/nasa_reference_points.csv`](../backend/data/nasa_reference_points.csv):

| Binder | Tensile plateau r | Knee φ₀ | Fitted to |
| --- | --- | --- | --- |
| PHB | 0.72 | 0.07 | NASA Glenn injection-molded PHB + LMS-1, LSP-2, MGS-1, JEZ-1, LHS-1 at 20–80 wt% |
| PLA | 0.34 | 0.125 | NASA Kennedy 3D-printed PLA + LHS-1 / BP-1 at 61–78 wt% |
| PEEK, LDPE | 0.35, 0.20 | 0.15, 0.12 | no NASA composite data; estimates |

Cold behaviour uses NASA's Table 8 ratios between 77 K and room temperature. For PLA, tensile strength goes from 41.6
to 87 MPa, stiffness from 1.17 to 1.67 GPa, and elongation from 6.4% to 5.7%.

### Residuals (physics model vs NASA, 0°/90° averaged)

| Dataset | Property | Mean abs. error |
| --- | --- | --- |
| NASA Glenn PHB | tensile strength | 6.3% |
| NASA Glenn PHB | decomposition temperature | 0.6% |
| NASA Kennedy PLA | tensile strength | 6.3% |
| NASA Kennedy PLA | compressive strength | 7.7% |
| NASA Kennedy PLA | stiffness | 2.9% |

The largest single miss is BP-1 + PLA at 61.5 wt% tensile strength, about +55%. NASA's own 0°/90° results for that
mix differ by 30%.

### What NASA's data changed in our model

Our first version assumed regolith makes the bioplastic stronger at low loading and that Martian soil bonds worse.
NASA Glenn's measurements say otherwise:
- Tensile strength **drops** from 29.4 MPa (neat PHB) to about 21–24 MPa at 20 wt%, then **plateaus**, still holding
  16–23 MPa at 80 wt%.
- Martian simulants hold strength as well as lunar ones. Their real signature is **thermal**: iron lowers PHB's
  decomposition temperature by 12–22 °C.

The model follows the data.

## 4. Physics emulator (Random Forest)

The forest's job is to make the physics model fast and portable (it runs in the browser). It adds no new
knowledge; section 5 is where real data comes in.

- **Dataset:** 9,000 random mixes from the physics model at 23 °C (6 binders, 0–92.5 wt%), with 0.4–5% Gaussian scatter.
- **Features:** raw inputs, physics-informed features (volume fractions, bond, bond × volume, porosity, grain
  stiffness, density estimate), and binder/soil one-hots.
- **Targets:** log(property / pure-binder property), standardized. Learning ratios stops the binder's scale from
  dominating.
- **Model:** `RandomForestRegressor(n_estimators=28, max_depth=12, min_samples_leaf=5)`, one multi-output forest.
- **Uncertainty:** the standard deviation across trees after mapping each tree's output back to real units.
- **Emulator fidelity (R² on 1,800 held-out synthetic mixes):** 0.981 (conductivity) to 0.9996 (decomposition
  temperature). This shows the forest copies the physics faithfully. It says nothing about whether the physics is
  right; section 5 tests that against real data.

## 5. Evidence correction (Gaussian process on real measurements)

Code: [`backend/models/evidence_model.py`](../backend/models/evidence_model.py) · Data: [evidence pipeline](evidence.md)

Real coupons depart from the physics because of how they were made, how well the binder wets the grains, and lab
scatter. For each property with enough data we learn that departure in log space:

    log(measured) = log(physics(x)) + δ(φ, binder, process) + noise,      δ ~ GP(0, k)

    k = r(φ,φ')·[ s_all² + s_binder²·same binder + s_process²·same process + s_pair²·same binder and process ]

Here r is a squared-exponential kernel on the filler volume fraction φ. Effects can be shared across everything,
per binder, per process or per binder-process pair, and the marginal likelihood decides how much of each.
Hyperpriors are centred on the size of the property's own corrections. Each point's noise is a fitted floor plus
its reported standard deviation. Far from any data δ → 0, so the prediction returns to physics and its ± grows.
The ± bands are widened by a calibration factor until 90% of held-out mixes fall inside them.

**Training data:** first-hand, experimental, room-temperature measurements of the predicted properties. Excluded:
cited values, duplicates between NASA decks, vacuum-cured bricks, low-confidence chart readings, and composites
whose filler content isn't stated. That leaves 152 values from S001, S003, S004, S006, S007, S008 and S011.

**Validation: average error on measurements the model never saw**

| Property | n | Sources | Physics alone | + lab data (untested mix) | New study left out | ± calibration |
| --- | --- | --- | --- | --- | --- | --- |
| Tensile strength | 35 | S001, S003, S006/S011, S007 | 19% | 18% | 19% | ×1.02 |
| Stiffness | 8 | S003, S007 | 65% | 19% | 53% | ×1.00 |
| Compressive strength | 36 | S003, S004, S008 | 230% | 34% | 78% | ×1.06 |
| Density | 25 | S003, S008 | 16% | 5% | 11% | ×1.02 |
| Thermal conductivity | 14 | S008 | 32% | 7% | n/a (one study) | ×1.22 |
| Decomposition temperature | 34 | S001, S006/S011 | 1.1% | 1.3% | 1.3% | ×1.09 |

- *Untested mix* (leave-one-mix-out): each tested mix (study × binder × process × filler level) is predicted
  without its own data. This is how the simulator is used.
- *New study* (leave-one-study-out): a whole lab is left out, the hardest test. A process that only one study used
  (S004's cold-compacted, sintered PEEK bricks) can't be predicted from the others. That is why compressive
  strength stays at 78%. The website marks such predictions "Physics estimate" or "Related data".
- Decomposition temperature gains nothing because the physics was already fitted to the same NASA Glenn points.

**In the browser** the GP is exported as a table over φ = 0…0.9 for every binder × process
(`evidence_grid.json`). Python and JavaScript interpolate the same table, and a parity test checks them on 60
random mixes. Per tree, the forest's room-temperature output is multiplied by exp(δ) before the temperature
physics. The final uncertainty combines the tree spread with the GP's. The API returns both a symmetric
`uncertainty` (kept for compatibility) and a `range`: value × e^(±s) with s = √((tree sd / value)² + GP sd²), about
a 68% band. The app shows the range whenever it is wide, because the error is multiplicative and a ± would dip
below zero.

**Part test.** The 3D part test applies textbook formulas to the predicted properties at the chosen temperature
(`frontend/src/lib/engine/parts.js`, unit-tested against hand calculations):

| Part | Load case | Breaks when | Design load (assumed) |
| --- | --- | --- | --- |
| Wrench, 6 × 20 mm handle, 120 mm arm | Cantilever bending | σ = F·L / Z reaches tensile strength (Z = b h² / 6) | 10 N·m on an M6 bolt |
| Shelf bracket, 30 × 8 mm arm, 100 mm long | Cantilever bending | as above | 20 kg in lunar gravity |
| Shelter brick, 200 × 100 × 60 mm | Uniform compression | σ = F / A reaches compressive strength | 2 m of wall plus 3 m of regolith shielding above it |

The breaking range scales with the strength range. Bending is drawn exaggerated so it is visible; deflection uses
δ = F L³ / 3EI with the predicted stiffness. "Snaps" vs "bends first" follows elongation at break (below 2%). The
stress picture uses beam theory (simplified around the wrench head), not finite elements.

## 6. Temperature physics (applied per tree)

- **Cold:** linear interpolation between 1.0 at 23 °C and NASA's 77 K ratio (log-linear for elongation).
- **Hot:** strength and stiffness × σ((T_service − T)/12) normalized at 23 °C; elongation rises as the matrix softens.

## 7. Limitations

- Real data are sparse: 152 measurements, and each study used one binder and one process. The evidence model
  interpolates well within a tested material system and transfers only partly to a new one (see the new-study
  column).
- Where a chip says "Physics estimate" there are no lab data near that mix. Examples are PHB compressive strength
  and conductivity, PEEK tensile, and every flexibility and max-service-temperature value.
- Simulants are not real regolith (no agglutinates or nanophase iron), and S008's VI-75 simulant is far richer in
  SiO₂ than lunar soil.
- Print anisotropy (0° vs 90°) is averaged; real parts vary more.
- No radiation, UV, vacuum outgassing or long-term creep effects yet. NASA's MISSE-23/24 and LESTR results will
  inform these.
