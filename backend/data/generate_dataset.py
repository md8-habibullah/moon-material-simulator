"""Generate the synthetic training set in data/regolith_composites.csv.

Run from the backend folder:  python -m data.generate_dataset
The output is deterministic (fixed seed), so re-running gives the same file.
"""
import numpy as np
import pandas as pd

from config import DATA_PATH, RANDOM_SEED
from utils.materials import POLYMERS, REGOLITHS, composite_properties

N_SAMPLES = 1800
# Lab-to-lab scatter for printed composite coupons is typically several percent.
NOISE = {"tensile_strength": 0.05, "elastic_modulus": 0.04, "compressive_strength": 0.05, "thermal_stability": 0.015}


def generate(n: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        polymer = rng.choice(list(POLYMERS))
        regolith = rng.choice(list(REGOLITHS))
        wt = round(float(rng.uniform(0, 50)), 1)
        temp = round(float(rng.uniform(-180, 150)), 1)
        props = composite_properties(wt, regolith, polymer, temp)
        noisy = {k: round(v * (1 + rng.normal(0, NOISE[k])), 3) for k, v in props.items()}
        rows.append({"regolith_wt": wt, "regolith_type": regolith, "polymer_type": polymer, "temperature": temp, **noisy})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
    print(f"Wrote {len(df)} rows to {DATA_PATH}")
