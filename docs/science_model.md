# Science model

[← Back to README](../README.md) · Code: [`backend/utils/materials.py`](../backend/utils/materials.py)

The simulator predicts eight properties of a printed or molded **binder + regolith (+ basalt fibre)** composite. It
combines a physics model calibrated on NASA measurements, a Random Forest trained on that model, and explicit
temperature physics.

## 1. Inputs

| Input | Range | Notes |
| --- | --- | --- |
| Binder | PHB, PLA, PEEK, LDPE | PHB is NASA Glenn's bacterial bioplastic (poly(3-hydroxybutyrate)) |
| Regolith | lunar highlands, lunar mare, Martian | LHS-1/LSP-2-type, LMS-1/BP-1-type, MGS-1/JEZ-1-type simulants |
| Regolith content | 0–80 wt% | NASA Glenn processed PHB up to 80 wt% |
| Basalt fibre | 0–15 wt% | regolith + fibre ≤ 85 wt% |
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

## 4. Machine learning

- **Dataset:** 6,000 random mixes from the physics model at 23 °C, with 0.4–5% Gaussian scatter.
- **Features:** raw inputs, physics-informed features (volume fractions, bond, bond × volume, porosity, grain
  stiffness, density estimate), and binder/soil one-hots.
- **Targets:** log(property / pure-binder property), standardized. Learning ratios stops the binder's scale from
  dominating.
- **Model:** `RandomForestRegressor(n_estimators=28, max_depth=12, min_samples_leaf=5)`, one multi-output forest.
- **Uncertainty:** the standard deviation across trees after mapping each tree's output back to real units.
- **Hold-out R² (1,200 mixes):** 0.989 (tensile) to 0.9997 (decomposition temperature).
- **Against NASA (56 points, per print direction):** 6.0% mean error on Glenn PHB, 17.3% on Kennedy PLA.

## 5. Temperature physics (applied per tree)

- **Cold:** linear interpolation between 1.0 at 23 °C and NASA's 77 K ratio (log-linear for elongation).
- **Hot:** strength and stiffness × σ((T_service − T)/12) normalized at 23 °C; elongation rises as the matrix softens.

## 6. Limitations

- The training data are synthetic. The model interpolates the calibrated physics; it has not learned from thousands
  of coupons.
- PHB compressive strength, conductivity and density, and every PEEK/LDPE composite value, are estimates without NASA
  composite data.
- Print anisotropy (0° vs 90°) is averaged; real parts vary more.
- No radiation, UV, vacuum outgassing or long-term creep effects yet. NASA's MISSE-23/24 and LESTR results will
  inform these.
