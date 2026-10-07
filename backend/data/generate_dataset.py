"""Generate the synthetic training set in data/regolith_composites.csv (properties at 23 °C).

Run from the backend folder:  python -m data.generate_dataset
The output is deterministic (fixed seed), so re-running gives the same file.
"""
import math

import numpy as np
import pandas as pd

from config import DATA_PATH, RANDOM_SEED
from utils.materials import BINDERS, MAX_TOTAL_FILLER_WT, RANGES, REGOLITHS, room_temperature_properties

N_SAMPLES = 6000
# Coupon-to-coupon scatter for printed composites (NASA's 0°/90° results differ by far more).
NOISE = {
    "tensile_strength": 0.03,
    "elastic_modulus": 0.025,
    "compressive_strength": 0.03,
    "elongation_at_break": 0.05,
    "density": 0.005,
    "thermal_conductivity": 0.025,
    "max_service_temp": 0.01,
    "decomposition_temp": 0.004,
}


def generate(n: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    lo_d, hi_d = RANGES["particle_size"]
    rows = []
    for _ in range(n):
        binder = str(rng.choice(list(BINDERS)))
        regolith = str(rng.choice(list(REGOLITHS)))
        regolith_wt = round(float(rng.uniform(*RANGES["regolith_wt"])), 1)
        fiber_wt = 0.0 if rng.random() < 0.5 else round(float(rng.uniform(*RANGES["fiber_wt"])), 1)
        fiber_wt = min(fiber_wt, MAX_TOTAL_FILLER_WT - regolith_wt)
        particle_size = round(math.exp(rng.uniform(math.log(lo_d), math.log(hi_d))), 1)
        props = room_temperature_properties(regolith_wt, fiber_wt, particle_size, regolith, binder)
        noisy = {k: round(v * (1 + rng.normal(0, NOISE[k])), 4) for k, v in props.items()}
        rows.append(
            {
                "binder": binder,
                "regolith": regolith,
                "regolith_wt": regolith_wt,
                "fiber_wt": fiber_wt,
                "particle_size": particle_size,
                **noisy,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
    print(f"Wrote {len(df)} rows to {DATA_PATH}")
