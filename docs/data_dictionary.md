# Data dictionary

The training set lives in `backend/data/regolith_composites.csv` and is produced by
`backend/data/generate_dataset.py` (1,800 rows, fixed seed, so it is reproducible).

**It is synthetic.** Each row is a physics-based estimate with random scatter added, standing in for
measured data until we can calibrate against real test results.

## Columns

| Column | Type | Unit | Range | Meaning |
| --- | --- | --- | --- | --- |
| `regolith_wt` | float | wt% | 0–50 | Regolith share of the composite by weight |
| `regolith_type` | string | – | `lunar`, `martian` | Which simulant the filler represents |
| `polymer_type` | string | – | `PLA`, `PEEK`, `LDPE` | Polymer matrix (binder) |
| `temperature` | float | °C | −180 to 150 | Temperature the property is evaluated at |
| `tensile_strength` | float | MPa | target | Stress at break in tension |
| `elastic_modulus` | float | GPa | target | Stiffness (Young's modulus) |
| `compressive_strength` | float | MPa | target | Crushing strength |
| `thermal_stability` | float | °C | target | Maximum service temperature (heat-deflection style softening point) |

## How a row is generated

1. **Volume fraction.** Weight % is converted to filler volume fraction φ using particle densities
   (lunar 2.90 g/cm³, Martian 2.75 g/cm³) and polymer densities (PLA 1.24, PEEK 1.30, LDPE 0.92).
2. **Stiffness:** Guth–Gold model for rigid particles, `E = E_m · (1 + q · (2.5φ + 14.1φ²))`.
3. **Tensile strength:** Nicolais–Narkis model for particulate fillers,
   `σ = σ_m · (1 − 1.21 · φ^(2/3) · (1.1 − q))`. Weaker bonding loses more strength.
4. **Compressive strength:** `σ_c = σ_c,m · (1 + 0.9 · φ · q)`. Rigid grains carry compressive load.
5. **Max service temperature:** `T = HDT_m + 60 · φ · q`. Inorganic filler restricts chain mobility.
6. **Temperature effect:** above room temperature, properties fall along a sigmoid centred on the
   composite's softening point; below it, polymers stiffen and strengthen modestly.
7. **Scatter:** multiplicative Gaussian noise (4–5 % for mechanical properties, 1.5 % for
   temperature), similar to lab-to-lab variation in printed coupons.

`q` is an interface-quality factor: 0.85 for lunar grains (angular and glassy, so they interlock well)
and 0.72 for Martian grains (fine clays and salts weaken bonding).

## Reference values for the pure polymers (23 °C)

| Polymer | Tensile (MPa) | Modulus (GPa) | Compressive (MPa) | Softening point (°C) | Biodegradable |
| --- | --- | --- | --- | --- | --- |
| PLA | 60 | 3.5 | 95 | 55 | Yes |
| PEEK | 100 | 3.7 | 125 | 152 | No |
| LDPE | 11 | 0.25 | 14 | 45 | No |

These are typical datasheet-range values, not certified design data.

## Model

`RandomForestRegressor` (150 trees, `min_samples_leaf=2`) with one multi-output head for all four
targets, trained on an 80/20 split. Features: `regolith_wt`, `is_martian`, one-hot polymer, and
`temperature`. The API reports the standard deviation across trees as a rough uncertainty band, and
`GET /api/model` returns hold-out R² and MAE per property.
