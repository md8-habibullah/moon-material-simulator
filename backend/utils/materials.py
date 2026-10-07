"""Reference material properties and the physics heuristics behind the synthetic dataset.

All values are approximate, room-temperature (23 °C) figures for unfilled polymers taken
from typical datasheet ranges. They are a starting point for the prototype, not certified
design values. See docs/data_dictionary.md for the assumptions.
"""
import math

ROOM_TEMP_C = 23.0

POLYMERS = {
    "PLA": {
        "name": "Polylactic acid",
        "biodegradable": True,
        "density": 1.24,  # g/cm³
        "tensile_strength": 60.0,  # MPa
        "elastic_modulus": 3.5,  # GPa
        "compressive_strength": 95.0,  # MPa
        "heat_deflection_temp": 55.0,  # °C
    },
    "PEEK": {
        "name": "Polyether ether ketone",
        "biodegradable": False,
        "density": 1.30,
        "tensile_strength": 100.0,
        "elastic_modulus": 3.7,
        "compressive_strength": 125.0,
        "heat_deflection_temp": 152.0,
    },
    "LDPE": {
        "name": "Low-density polyethylene",
        "biodegradable": False,
        "density": 0.92,
        "tensile_strength": 11.0,
        "elastic_modulus": 0.25,
        "compressive_strength": 14.0,
        "heat_deflection_temp": 45.0,
    },
}

REGOLITHS = {
    "lunar": {
        "name": "Lunar highlands regolith simulant",
        "density": 2.90,  # particle density, g/cm³
        # 0..1, how well grains bond to the polymer. Angular, glassy lunar grains interlock well.
        "interface_quality": 0.85,
    },
    "martian": {
        "name": "Martian global regolith simulant",
        "density": 2.75,
        # Fine clays and salts in Martian soil weaken the polymer-grain interface.
        "interface_quality": 0.72,
    },
}

# Surface temperature extremes commonly cited for mission planning, in °C.
ENVIRONMENTS = {
    "lunar": {"min_temp": -173.0, "max_temp": 127.0},
    "martian": {"min_temp": -125.0, "max_temp": 20.0},
}


def volume_fraction(regolith_wt: float, polymer: str, regolith: str) -> float:
    """Convert regolith weight % into volume fraction of filler."""
    w = regolith_wt / 100.0
    if w <= 0:
        return 0.0
    rho_f = REGOLITHS[regolith]["density"]
    rho_m = POLYMERS[polymer]["density"]
    return (w / rho_f) / (w / rho_f + (1 - w) / rho_m)


def _temperature_factor(temp_c: float, softening_c: float, cold_gain: float) -> float:
    """Scale a room-temperature property to `temp_c`.

    Above room temperature the matrix softens along a sigmoid centred on its heat
    deflection temperature; below it, polymers stiffen and strengthen modestly.
    """
    def soft(t):
        return 1.0 / (1.0 + math.exp((t - softening_c) / 12.0))

    hot = soft(temp_c) / soft(ROOM_TEMP_C)
    cold = 1.0 + cold_gain * max(0.0, ROOM_TEMP_C - temp_c)
    return max(0.05, min(hot, 1.0) * cold)


def composite_properties(regolith_wt: float, regolith: str, polymer: str, temp_c: float) -> dict:
    """Noise-free property estimate for one composition, used to build the training set."""
    p = POLYMERS[polymer]
    r = REGOLITHS[regolith]
    phi = volume_fraction(regolith_wt, polymer, regolith)
    q = r["interface_quality"]

    # Guth–Gold stiffening for rigid particles, scaled by how well they bond.
    modulus = p["elastic_modulus"] * (1 + q * (2.5 * phi + 14.1 * phi**2))
    # Nicolais–Narkis strength loss for particulate fillers; better bonding loses less.
    tensile = p["tensile_strength"] * (1 - 1.21 * phi ** (2 / 3) * (1.1 - q))
    # Rigid grains carry compressive load well.
    compressive = p["compressive_strength"] * (1 + 0.9 * phi * q)
    # Inorganic filler restricts chain mobility and raises the softening point.
    hdt = p["heat_deflection_temp"] + 60.0 * phi * q

    return {
        "tensile_strength": tensile * _temperature_factor(temp_c, hdt, 0.0012),
        "elastic_modulus": modulus * _temperature_factor(temp_c, hdt, 0.002),
        "compressive_strength": compressive * _temperature_factor(temp_c, hdt, 0.0012),
        "thermal_stability": hdt,
    }
