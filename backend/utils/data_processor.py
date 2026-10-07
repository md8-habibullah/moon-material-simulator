"""Feature encoding shared by training and the API so both see identical inputs."""
import numpy as np
import pandas as pd

from .materials import POLYMERS

FEATURE_COLUMNS = ["regolith_wt", "is_martian", *[f"polymer_{p}" for p in POLYMERS], "temperature"]
TARGET_COLUMNS = ["tensile_strength", "elastic_modulus", "compressive_strength", "thermal_stability"]

UNITS = {
    "tensile_strength": "MPa",
    "elastic_modulus": "GPa",
    "compressive_strength": "MPa",
    "thermal_stability": "°C",
}


def encode_frame(df: pd.DataFrame) -> np.ndarray:
    """Turn raw composition columns into the model's numeric feature matrix."""
    features = pd.DataFrame(
        {
            "regolith_wt": df["regolith_wt"].astype(float),
            "is_martian": (df["regolith_type"] == "martian").astype(float),
            **{f"polymer_{p}": (df["polymer_type"] == p).astype(float) for p in POLYMERS},
            "temperature": df["temperature"].astype(float),
        }
    )
    return features[FEATURE_COLUMNS].to_numpy()


def encode_one(regolith_wt: float, regolith_type: str, polymer_type: str, temperature: float) -> np.ndarray:
    row = pd.DataFrame(
        [{"regolith_wt": regolith_wt, "regolith_type": regolith_type, "polymer_type": polymer_type, "temperature": temperature}]
    )
    return encode_frame(row)
