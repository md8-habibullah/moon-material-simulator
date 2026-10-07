"""Feature encoding shared by training, the API and the browser export, so all three agree.

The forest models composition -> room-temperature properties; temperature is applied afterwards
by explicit physics (utils.materials.temperature_factors). Besides the raw inputs, the model gets a few physics-informed features (volume fractions, grain
bond, porosity, grain stiffness, theoretical density). They are cheap, deterministic functions of
the inputs, mirrored line-for-line in frontend/src/lib/engine/features.js, and they let a small
forest pick up second-order effects such as regolith type and grain size.
"""
import numpy as np
import pandas as pd

from .materials import (
    BINDERS,
    REGOLITHS,
    porosity,
    size_factor,
    theoretical_density,
    volume_fractions,
)

RAW_FEATURES = ["regolith_wt", "fiber_wt", "particle_size"]
PHYSICS_FEATURES = ["phi_regolith", "phi_fiber", "bond", "reinforcement", "porosity", "grain_modulus", "density_estimate"]
FEATURE_COLUMNS = [
    *RAW_FEATURES,
    *PHYSICS_FEATURES,
    *[f"binder_{b}" for b in BINDERS],
    *[f"regolith_{r}" for r in REGOLITHS],
]
TARGET_COLUMNS = [
    "tensile_strength",
    "elastic_modulus",
    "compressive_strength",
    "elongation_at_break",
    "density",
    "thermal_conductivity",
    "max_service_temp",
    "decomposition_temp",
]
UNITS = {
    "tensile_strength": "MPa",
    "elastic_modulus": "GPa",
    "compressive_strength": "MPa",
    "elongation_at_break": "%",
    "density": "g/cm³",
    "thermal_conductivity": "W/m·K",
    "max_service_temp": "°C",
    "decomposition_temp": "°C",
}


def physics_features(regolith_wt: float, fiber_wt: float, particle_size: float, binder: str, regolith: str) -> dict:
    r = REGOLITHS[regolith]
    phi_r, phi_f = volume_fractions(regolith_wt, fiber_wt, binder, regolith)
    bond = r["interface_quality"] * BINDERS[binder]["filler_affinity"] * size_factor(particle_size)
    p = porosity(phi_r + phi_f, r["void_factor"])
    return {
        "phi_regolith": phi_r,
        "phi_fiber": phi_f,
        "bond": bond,
        "reinforcement": bond * phi_r,
        "porosity": p,
        "grain_modulus": r["grain_modulus"] if regolith_wt > 0 else 0.0,
        "density_estimate": theoretical_density(regolith_wt, fiber_wt, binder, regolith) * (1 - p),
    }


def encode_row(row: dict) -> list[float]:
    phys = physics_features(row["regolith_wt"], row["fiber_wt"], row["particle_size"], row["binder"], row["regolith"])
    values = {
        **{k: float(row[k]) for k in RAW_FEATURES},
        **phys,
        **{f"binder_{b}": float(row["binder"] == b) for b in BINDERS},
        **{f"regolith_{r}": float(row["regolith"] == r) for r in REGOLITHS},
    }
    return [values[c] for c in FEATURE_COLUMNS]


def encode_rows(rows: list[dict]) -> np.ndarray:
    return np.array([encode_row(r) for r in rows], dtype=float)


def encode_frame(df: pd.DataFrame) -> np.ndarray:
    return encode_rows(df[["binder", "regolith", *RAW_FEATURES]].to_dict("records"))
