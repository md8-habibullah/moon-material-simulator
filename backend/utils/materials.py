"""Material catalogue and the physics model behind the synthetic training set.

Pure-binder values are approximate, typical figures for printed parts at 23 °C. Filler effects
use classic particulate-composite models whose constants were tuned so PLA composites land near
NASA's measured lunar-simulant + PLA results (NTRS 20230015024, see
data/nasa_reference_points.csv). The output is a set of plausible trends for exploring the
design space, not certified design values. docs/science_model.md explains every equation.
"""
import math

ROOM_TEMP_C = 23.0

# Unless marked "estimate", binder values come from NASA NTRS 20230015024, Appendix Table 8
# ("Selected Polymer Properties", room temperature and 77 K). PLA values there are for 3D-printed parts.
BINDERS = {
    "PHB": {
        "label": "Bio-PHB",
        "name": "Bacterial bioplastic (PHA/PHB)",
        "summary": "Grown inside bacteria fed CO₂ or crew waste. NASA Glenn's 2026 material.",
        "biodegradable": True,
        "made_on_site": True,
        "density": 1.24,  # g/cm³ (estimate)
        # Neat, plant-based PHB, injection molded: NASA Glenn (NTRS 20260007758, slide 17).
        # Table 8's generic PHA/PHB figure is 37.5 MPa.
        "tensile_strength": 29.4,  # MPa
        "elastic_modulus": 3.75,  # GPa
        "compressive_strength": 45.0,  # MPa (estimate)
        "elongation_at_break": 15.5,  # %
        "thermal_conductivity": 0.20,  # W/m·K (estimate)
        "heat_deflection_temp": 92.0,  # °C at 0.45 MPa
        "glass_transition": 13.5,  # °C
        "melting_point": 176.5,  # °C
        "decomposition_temp": 281.7,  # °C, NASA Glenn DSC/TGA (NTRS 20260007758, slide 9)
        # How well grains bond to this binder (0..1).
        "filler_affinity": 1.0,
        # Tensile strength vs filler volume fraction φ: ratio = r + (1 - r)·exp(-φ/φ0).
        # Fitted to NASA Glenn's injection-molded PHB + regolith results (20-80 wt%).
        "tensile_plateau": 0.72,
        "tensile_knee": 0.07,
        # How strongly iron-bearing grains catalyse thermal decomposition (polyesters are sensitive).
        "fe_sensitivity": 1.0,
        # °C of heat resistance gained per unit filler volume fraction. Semicrystalline binders gain
        # most because grains nucleate crystals (the "spherulites" in NASA's micrographs).
        "hdt_gain": 90.0,
        # Property ratios at 77 K (-196 °C) versus room temperature.
        "cryo_strength_ratio": 2.0,  # estimate
        "cryo_modulus_ratio": 1.5,  # estimate
        "cryo_elongation_ratio": 0.2,  # estimate
    },
    "PLA": {
        "label": "PLA",
        "name": "Polylactic acid (3D-printed)",
        "summary": "Plant-based and biodegradable. NASA Kennedy printed it with lunar simulant.",
        "biodegradable": True,
        "made_on_site": False,
        "density": 1.24,
        "tensile_strength": 41.6,
        "elastic_modulus": 1.17,
        "compressive_strength": 60.0,  # estimate
        "elongation_at_break": 6.4,
        "thermal_conductivity": 0.13,  # estimate
        "heat_deflection_temp": 56.0,
        "glass_transition": 57.0,
        "melting_point": 156.0,
        "decomposition_temp": 340.0,  # estimate
        "filler_affinity": 0.9,
        # Fitted to NASA Kennedy's printed LHS-1 / BP-1 + PLA results (60-78 wt%).
        "tensile_plateau": 0.34,
        "tensile_knee": 0.125,
        "fe_sensitivity": 0.8,
        "hdt_gain": 25.0,
        "cryo_strength_ratio": 87.0 / 41.6,
        "cryo_modulus_ratio": 1.67 / 1.17,
        "cryo_elongation_ratio": 5.7 / 6.4,
    },
    "PEEK": {
        "label": "PEEK",
        "name": "Polyether ether ketone",
        "summary": "High-temperature engineering plastic. Strong, but shipped from Earth.",
        "biodegradable": False,
        "made_on_site": False,
        "density": 1.30,
        "tensile_strength": 95.0,
        "elastic_modulus": 3.5,
        "compressive_strength": 118.0,  # estimate
        "elongation_at_break": 70.0,
        "thermal_conductivity": 0.25,  # estimate
        "heat_deflection_temp": 186.0,
        "glass_transition": 143.0,
        "melting_point": 343.0,
        "decomposition_temp": 575.0,  # estimate
        "filler_affinity": 0.85,
        "tensile_plateau": 0.35,  # estimate
        "tensile_knee": 0.15,  # estimate
        "fe_sensitivity": 0.1,
        "hdt_gain": 60.0,
        "cryo_strength_ratio": 200.0 / 95.0,
        "cryo_modulus_ratio": 5.40 / 3.50,
        "cryo_elongation_ratio": 8.0 / 70.0,
    },
    "LDPE": {
        "label": "LDPE",
        "name": "Low-density polyethylene",
        "summary": "Flexible, hydrogen-rich commodity plastic, shipped from Earth.",
        "biodegradable": False,
        "made_on_site": False,
        "density": 0.92,
        "tensile_strength": 10.2,
        "elastic_modulus": 0.23,
        "compressive_strength": 12.0,  # estimate
        "elongation_at_break": 445.0,
        "thermal_conductivity": 0.33,  # estimate
        "heat_deflection_temp": 42.0,
        "glass_transition": -108.0,
        "melting_point": 106.5,
        "decomposition_temp": 430.0,  # estimate
        "filler_affinity": 0.6,  # non-polar, so grains bond poorly
        "tensile_plateau": 0.2,  # estimate
        "tensile_knee": 0.12,  # estimate
        "fe_sensitivity": 0.2,
        "hdt_gain": 50.0,
        "cryo_strength_ratio": 118.0 / 10.2,
        "cryo_modulus_ratio": 5.0,  # estimate (blank in the NASA table)
        "cryo_elongation_ratio": 2.0 / 445.0,
    },
}

REGOLITHS = {
    "lunar_highlands": {
        "label": "Lunar highlands",
        "simulant": "LHS-1-type simulant",
        "body": "moon",
        "summary": "Bright anorthosite-rich soil, like the Artemis south-pole sites.",
        "density": 2.90,  # particle density, g/cm³
        "interface_quality": 0.85,  # angular, glassy grains interlock well
        "grain_modulus": 70.0,  # GPa, anorthosite-rich grains
        "void_factor": 1.0,  # dry, so parts consolidate well
        # Drop in binder decomposition temperature: -max·(1 - exp(-wt/scale)). Fitted to NASA
        # Glenn's PHB data for LHS-1 and LSP-2 (NTRS 20260007758, slide 9).
        "decomp_drop_max": 6.0,
        "decomp_drop_scale": 40.0,
        "thermal_conductivity": 1.5,  # solid grain, W/m·K
        "color": "#b9bec8",
        # Approximate bulk oxide composition, wt% (rounded, typical of highlands soil).
        "oxides": {"SiO₂": 45, "Al₂O₃": 26, "CaO": 15, "MgO": 6, "FeO": 6, "Other": 2},
    },
    "lunar_mare": {
        "label": "Lunar mare",
        "simulant": "BP-1 / LMS-1-type simulant",
        "body": "moon",
        "summary": "Dark basaltic plains soil, rich in iron and titanium (ilmenite).",
        "density": 3.10,
        "interface_quality": 0.80,
        "grain_modulus": 85.0,  # dense basalt with ilmenite
        "void_factor": 1.4,  # many fines trap air
        "decomp_drop_max": 10.0,  # fitted to NASA Glenn's LMS-1 data
        "decomp_drop_scale": 50.0,
        "thermal_conductivity": 2.0,
        "color": "#6e757f",
        "oxides": {"SiO₂": 43, "FeO": 17, "Al₂O₃": 13, "CaO": 11, "MgO": 9, "TiO₂": 5, "Other": 2},
    },
    "martian": {
        "label": "Martian",
        "simulant": "MGS-1-type simulant",
        "body": "mars",
        "summary": "Iron-oxide-rich basaltic soil with clays and salts.",
        "density": 2.80,
        "interface_quality": 0.82,  # NASA Glenn's MGS-1 composites held strength as well as lunar ones
        "grain_modulus": 55.0,  # weathered, clay-bearing grains
        "void_factor": 1.2,  # hydrated minerals release some water during melt processing
        # Iron-rich Martian simulants lower PHB's decomposition temperature by 12-22 °C
        # (NASA Glenn, MGS-1 and JEZ-1, NTRS 20260007758 slide 9).
        "decomp_drop_max": 21.0,
        "decomp_drop_scale": 22.0,
        "thermal_conductivity": 1.4,
        "color": "#c4643a",
        "oxides": {"SiO₂": 45, "FeO": 17, "Al₂O₃": 10, "MgO": 8, "CaO": 7, "SO₃": 6, "Other": 7},
    },
}

FIBER = {
    "name": "Basalt fibre",
    "summary": "Short fibres drawn from melted regolith basalt.",
    "density": 2.65,
    "thermal_conductivity": 1.7,
    # Effective contributions of short, randomly oriented fibres (well below the fibre's own
    # ~85 GPa / ~2 GPa because chopped fibres transfer load poorly).
    "modulus_gain": 17.0,  # GPa per unit fibre volume fraction
    "tensile_gain": 200.0,  # MPa per unit fibre volume fraction, scaled by binder affinity
    "compressive_gain": 100.0,
}

# Surface temperature extremes commonly cited for mission planning, °C.
ENVIRONMENTS = {
    "moon": {"label": "Moon", "min_temp": -173.0, "max_temp": 127.0},
    "mars": {"label": "Mars", "min_temp": -125.0, "max_temp": 20.0},
}

RANGES = {
    "regolith_wt": (0.0, 80.0),
    "fiber_wt": (0.0, 15.0),
    "particle_size": (10.0, 150.0),
    "temperature": (-200.0, 150.0),
}
MAX_TOTAL_FILLER_WT = 85.0

# Model constants, fitted against the NASA PLA composite measurements in
# data/nasa_reference_points.csv (see docs/science_model.md for the fit and its residuals).
BOND_REFERENCE = 0.85  # bond quality (interface × size factor) the tensile fits were made at
COMPRESSIVE_DECAY = 1.5  # exp(-k·φ²): rigid grains keep carrying compressive load longer
MAX_PACKING = 0.75  # Lewis–Nielsen maximum packing fraction for printed composites
ROOM_TO_77K = ROOM_TEMP_C - (-196.0)
POROSITY_BASE, POROSITY_COEF = 0.01, 0.12
SIZE_REF_UM, SIZE_COEF, SIZE_MIN, SIZE_MAX = 60.0, 0.22, 0.7, 1.4
SOFTENING_WIDTH = 12.0  # °C
HOT_STRETCH_WIDTH, HOT_STRETCH_GAIN = 10.0, 1.5


def volume_fractions(regolith_wt: float, fiber_wt: float, binder: str, regolith: str) -> tuple[float, float]:
    """Weight % of regolith and fibre -> volume fractions of each."""
    w_r, w_f = regolith_wt / 100.0, fiber_wt / 100.0
    w_m = 1.0 - w_r - w_f
    v_r = w_r / REGOLITHS[regolith]["density"]
    v_f = w_f / FIBER["density"]
    v_m = w_m / BINDERS[binder]["density"]
    total = v_r + v_f + v_m
    return v_r / total, v_f / total


def porosity(phi_total: float, void_factor: float = 1.0) -> float:
    """Highly filled melts are harder to consolidate, so printed parts trap more voids."""
    return POROSITY_BASE + POROSITY_COEF * void_factor * phi_total**2


def size_factor(particle_size: float) -> float:
    """Finer grains give more bonded interface per volume, up to a point."""
    return min(SIZE_MAX, max(SIZE_MIN, 1.0 + SIZE_COEF * math.log(SIZE_REF_UM / particle_size)))


def theoretical_density(regolith_wt: float, fiber_wt: float, binder: str, regolith: str) -> float:
    w_r, w_f = regolith_wt / 100.0, fiber_wt / 100.0
    return 1.0 / (
        w_r / REGOLITHS[regolith]["density"]
        + w_f / FIBER["density"]
        + (1 - w_r - w_f) / BINDERS[binder]["density"]
    )


def lewis_nielsen(phi: float, matrix_modulus: float, grain_modulus: float) -> float:
    """Stiffening ratio E_composite / E_matrix for rigid, roughly equiaxed grains."""
    a = 1.5  # Einstein coefficient - 1 for spheres
    ratio = grain_modulus / matrix_modulus
    b = (ratio - 1) / (ratio + a)
    psi = 1 + ((1 - MAX_PACKING) / MAX_PACKING**2) * phi
    return (1 + a * b * phi) / max(0.15, 1 - b * psi * phi)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, x))))


def _softening(temp_c: float, hdt: float) -> float:
    """Fraction of room-temperature stiffness/strength left as the matrix nears its softening point."""
    return min(1.0, _sigmoid((hdt - temp_c) / SOFTENING_WIDTH) / _sigmoid((hdt - ROOM_TEMP_C) / SOFTENING_WIDTH))


def _cold_ratio(temp_c: float, ratio_77k: float, log_scale: bool = False) -> float:
    """Interpolate a property ratio between room temperature (1.0) and 77 K (ratio_77k)."""
    t = min(1.0, max(0.0, (ROOM_TEMP_C - temp_c) / ROOM_TO_77K))
    if log_scale:
        return math.exp(math.log(ratio_77k) * t)
    return 1.0 + (ratio_77k - 1.0) * t


BASELINE_KEYS = {
    "tensile_strength": "tensile_strength",
    "elastic_modulus": "elastic_modulus",
    "compressive_strength": "compressive_strength",
    "elongation_at_break": "elongation_at_break",
    "density": "density",
    "thermal_conductivity": "thermal_conductivity",
    "max_service_temp": "heat_deflection_temp",
    "decomposition_temp": "decomposition_temp",
}


def binder_baseline(binder: str) -> dict:
    """Room-temperature properties of the unfilled binder, keyed like the model targets."""
    b = BINDERS[binder]
    return {target: b[key] for target, key in BASELINE_KEYS.items()}


def room_temperature_properties(
    regolith_wt: float,
    fiber_wt: float,
    particle_size: float,
    regolith: str,
    binder: str,
) -> dict:
    """Noise-free property estimate for one composition at 23 °C."""
    b, r = BINDERS[binder], REGOLITHS[regolith]
    phi_r, phi_f = volume_fractions(regolith_wt, fiber_wt, binder, regolith)
    phi_t = phi_r + phi_f
    q = r["interface_quality"] * b["filler_affinity"]
    g = size_factor(particle_size)
    p = porosity(phi_t, r["void_factor"])

    # Strength drops as grains break up the matrix, then levels off at a plateau set by how well
    # grains bond. Fitted per binder to NASA Glenn (PHB) and NASA Kennedy (PLA) measurements.
    plateau = min(0.95, b["tensile_plateau"] * q * g / BOND_REFERENCE)
    tensile_ratio = plateau + (1 - plateau) * math.exp(-phi_r / b["tensile_knee"])
    tensile = (
        b["tensile_strength"] * tensile_ratio * (1 - 2 * (p - POROSITY_BASE))
        + FIBER["tensile_gain"] * phi_f * b["filler_affinity"]
    )
    compressive = (
        b["compressive_strength"] * (1 + q * g * phi_r) * math.exp(-COMPRESSIVE_DECAY * phi_r**2) * (1 - 2 * p)
        + FIBER["compressive_gain"] * phi_f * b["filler_affinity"]
    )
    modulus = (
        b["elastic_modulus"] * lewis_nielsen(phi_r, b["elastic_modulus"], r["grain_modulus"]) * (1 - 1.5 * p)
        + FIBER["modulus_gain"] * phi_f
    )

    # Nielsen-type loss of stretch as rigid grains pin the chains (steeper for printed parts).
    elongation = b["elongation_at_break"] * max(0.004, (1 - phi_t ** (1 / 3))) ** 1.5

    density = theoretical_density(regolith_wt, fiber_wt, binder, regolith) * (1 - p)

    # Maxwell–Eucken for conductive particles in an insulating matrix.
    k_m = b["thermal_conductivity"]
    k_p = (phi_r * r["thermal_conductivity"] + phi_f * FIBER["thermal_conductivity"]) / phi_t if phi_t > 0 else k_m
    conductivity = k_m * (k_p + 2 * k_m + 2 * phi_t * (k_p - k_m)) / (k_p + 2 * k_m - phi_t * (k_p - k_m))

    hdt = min(b["heat_deflection_temp"] + b["hdt_gain"] * phi_t * q, b["melting_point"] - 10.0)

    decomposition = b["decomposition_temp"] - b["fe_sensitivity"] * r["decomp_drop_max"] * (
        1 - math.exp(-regolith_wt / r["decomp_drop_scale"])
    )

    return {
        "tensile_strength": tensile,
        "elastic_modulus": modulus,
        "compressive_strength": compressive,
        "elongation_at_break": elongation,
        "density": density,
        "thermal_conductivity": conductivity * (1 - p),
        "max_service_temp": hdt,
        "decomposition_temp": decomposition,
    }


def temperature_factors(binder: str, max_service_temp: float, temp_c: float) -> dict:
    """Multipliers that move room-temperature properties to `temp_c`.

    Cold: interpolate towards NASA's measured 77 K ratios (Table 8). Hot: the matrix softens along
    a sigmoid centred on the composite's own max service temperature. Mirrored in
    frontend/src/lib/engine/temperature.js.
    """
    b = BINDERS[binder]
    soft = _softening(temp_c, max_service_temp)
    hot_stretch = (1 + HOT_STRETCH_GAIN * _sigmoid((temp_c - max_service_temp) / HOT_STRETCH_WIDTH)) / (
        1 + HOT_STRETCH_GAIN * _sigmoid((ROOM_TEMP_C - max_service_temp) / HOT_STRETCH_WIDTH)
    )
    return {
        "tensile_strength": soft * _cold_ratio(temp_c, b["cryo_strength_ratio"]),
        "elastic_modulus": soft * _cold_ratio(temp_c, b["cryo_modulus_ratio"]),
        "compressive_strength": soft * _cold_ratio(temp_c, b["cryo_strength_ratio"]),
        "elongation_at_break": _cold_ratio(temp_c, b["cryo_elongation_ratio"], log_scale=True) * hot_stretch,
        "density": 1.0,
        "thermal_conductivity": 1.0,
        "max_service_temp": 1.0,
        "decomposition_temp": 1.0,
    }


def composite_properties(
    regolith_wt: float,
    fiber_wt: float,
    particle_size: float,
    regolith: str,
    binder: str,
    temp_c: float,
) -> dict:
    """Noise-free property estimate for one composition at one temperature."""
    props = room_temperature_properties(regolith_wt, fiber_wt, particle_size, regolith, binder)
    factors = temperature_factors(binder, props["max_service_temp"], temp_c)
    return {k: v * factors[k] for k, v in props.items()}


def in_situ_fraction(regolith_wt: float, fiber_wt: float, binder: str) -> float:
    """Share of the part's mass that could come from local resources (0..1).

    Regolith and basalt fibre are local by definition. The binder counts as local only when it
    can be grown on site (the bacterial bioplastic).
    """
    local = regolith_wt + fiber_wt
    if BINDERS[binder]["made_on_site"]:
        local += 100.0 - regolith_wt - fiber_wt
    return local / 100.0
