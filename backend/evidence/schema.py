"""Columns, vocabularies and unit conversions for the evidence dataset (research/EXTRACTION_SPEC.md)."""
import re

from config import BASE_DIR

REPO_DIR = BASE_DIR.parent
RESEARCH_DIR = REPO_DIR / "research"
PDF_DIR = RESEARCH_DIR / "pdfs"
EXTRACTION_DIR = RESEARCH_DIR / "extraction"
SOURCES_CSV = RESEARCH_DIR / "sources.csv"
AUDIT_DIR = RESEARCH_DIR / "audit"
EVIDENCE_DIR = BASE_DIR / "data" / "evidence"
MEASUREMENTS_CSV = EVIDENCE_DIR / "measurements.csv"

EXTRACTION_COLUMNS = [
    "source_id", "page", "anchor_type", "anchor_id", "row_label", "col_label", "value_raw", "value", "std", "n",
    "unit_raw", "binder", "binder_grade", "filler", "soil_type", "regolith_wt_target", "regolith_wt_actual",
    "regolith_vol", "fiber_wt", "d50_um", "process", "orientation", "infill_pct", "environment", "temperature_c",
    "property", "test_standard", "origin", "extraction", "confidence", "notes",
]
DERIVED_COLUMNS = ["obs_id", "model_property", "value_si", "std_si", "unit_si", "regolith_wt", "cited", "duplicate_of"]
MEASUREMENT_COLUMNS = ["obs_id", *EXTRACTION_COLUMNS, *DERIVED_COLUMNS[1:]]

ANCHOR_TYPES = {"table", "text", "figure"}
SOIL_TYPES = {"lunar_highlands", "lunar_mare", "lunar_generic", "martian", "basalt", "none", ""}
PROCESSES = {"FFF", "pellet_AM", "injection", "compression", "hot_press", "cold_sinter", "sinter", "FEM", "analytical", "compounding", ""}
ORIGINS = {"experimental", "simulation"}
EXTRACTIONS = {"table", "text", "chart_digitized"}
CONFIDENCES = {"high", "medium", "low"}

# Canonical unit per property, and plausible range in that unit (outside it, the auditor asks a human to look).
PROPERTY_UNITS = {
    "tensile_strength": ("MPa", 0.05, 600),
    "yield_strength_tensile": ("MPa", 0.05, 600),
    "tensile_modulus": ("GPa", 0.005, 120),
    "elongation_at_break": ("%", 0.01, 1500),
    "compressive_strength": ("MPa", 0.05, 800),
    "compressive_yield_strength": ("MPa", 0.05, 800),
    "compressive_modulus": ("GPa", 0.005, 120),
    "flexural_strength": ("MPa", 0.05, 600),
    "flexural_modulus": ("GPa", 0.005, 120),
    "shear_strength": ("MPa", 0.05, 400),
    "shear_modulus": ("GPa", 0.005, 60),
    "storage_modulus": ("GPa", 0.0005, 120),
    "impact_strength": ("kJ/m2", 0.05, 300),
    "hardness_shore_d": ("Shore D", 1, 100),
    "density": ("g/cm3", 0.3, 8.0),  # up to dense oxide minerals (wüstite 5.7, ilmenite 4.7)
    "porosity": ("%", 0, 80),
    "water_absorption": ("%", 0, 50),
    "thermal_conductivity": ("W/(m·K)", 0.01, 10),
    "cte": ("1e-6/K", 0.1, 400),
    "glass_transition": ("°C", -150, 400),
    "melting_temp": ("°C", 40, 450),
    "crystallization_temp": ("°C", 0, 400),
    "decomposition_temp": ("°C", 150, 700),
    "hdt": ("°C", 20, 400),
    "crystallinity": ("%", 0, 100),
    "melt_flow_index": ("g/10 min", 0, 500),  # 0 = no measurable flow
}


# Names the extractors used that mean a vocabulary property (the original name is kept in `property`).
MODEL_PROPERTY_ALIASES = {"elastic_modulus": "tensile_modulus", "effective_elastic_modulus": "tensile_modulus"}

# Recorded and documented, but not material properties the simulator predicts.
AUX_PROPERTIES = {
    "filler_wt_measured", "filler_wt_deviation_from_target", "filler_volume_fraction", "particle_area_fraction",
    "particle_size_fraction", "matrix_homogenized_modulus", "particle_elastic_modulus", "particle_density",
    "bulk_density", "outgassing_tml", "total_mass_loss",
    # radiation shielding (S013) and print-quality metrics (S007): kept as evidence, not predicted
    "harderian_tumor_prevalence_excess", "dose_equivalent_gcr_1yr", "seu_count", "dose_reduction_per_areal_density",
    "cell_death_rate_c3h10t1_2", "cell_transformation_rate_c3h10t1_2", "decomposition_temp_5pct_mass_loss",
    "decomposition_temp_10pct_mass_loss", "softening_temp_tma", "compressive_max_load", "warpage", "warpage_arc_radius",
    "dimensional_deviation_mean", "dimensional_deviation_sd", "overhang_spoon_bow_angle", "sintering_shrinkage", "molecular_weight_mw", "molecular_weight_mn",
    "polydispersity_index", "decomposition_onset_t5", "residual_char", "cold_crystallization_enthalpy",
    "melting_enthalpy", "flexural_strain_at_break", "pore_length", "pore_width", "pore_spacing", "poisson_ratio",
}
AUX_PREFIXES = ("chemical_composition_",)
AUX_SUFFIXES = ("_pct",)  # percentage changes quoted in text


def model_property(prop: str) -> str:
    """The vocabulary property a row measures, or '' if it is auxiliary/unknown."""
    prop = MODEL_PROPERTY_ALIASES.get(prop, prop)
    return prop if prop in PROPERTY_UNITS else ""


def is_known_property(prop: str) -> bool:
    return (prop in PROPERTY_UNITS or prop in MODEL_PROPERTY_ALIASES or prop in AUX_PROPERTIES
            or prop.startswith(AUX_PREFIXES) or prop.endswith(AUX_SUFFIXES))


_SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")


def _norm_unit(unit: str) -> str:
    u = (unit or "").strip().translate(_SUPERSCRIPTS)
    u = u.replace("×", "").replace("*", "")
    u = u.replace("³", "3").replace("²", "2").replace("μ", "µ").replace("·", "").replace("⋅", "").replace(" ", "")
    u = u.replace("^", "").replace("−", "-").replace("–", "-")
    return u.lower()


# (property-family canonical unit, normalised raw unit) -> multiplier, or a callable for offsets.
_FACTORS = {
    "MPa": {"mpa": 1, "n/mm2": 1, "kpa": 1e-3, "gpa": 1e3, "pa": 1e-6, "psi": 0.00689476, "ksi": 6.89476},
    "GPa": {"gpa": 1, "mpa": 1e-3, "kpa": 1e-6, "msi": 6.89476, "ksi": 0.00689476},
    "g/cm3": {"g/cm3": 1, "g/cc": 1, "g/ml": 1, "kg/m3": 1e-3, "g/cm-3": 1, "gcm-3": 1},
    "%": {"%": 1, "wt%": 1, "vol%": 1, "vol.%": 1, "mm/mm": 100, "mm/mm(strain)": 100},
    "W/(m·K)": {"w/(mk)": 1, "w/mk": 1, "w/(m*k)": 1, "wm-1k-1": 1, "w/(mk)": 1, "w/m/k": 1, "w/(m°c)": 1},
    "1e-6/K": {"1e-6/k": 1, "10-6k-1": 1, "10-6/k": 1, "ppm/k": 1, "µm/(m°c)": 1, "µm/m°c": 1, "×10-6k-1": 1,
               "x10-6k-1": 1, "×10-6/k": 1, "10-6/°c": 1, "1/k": 1e6, "k-1": 1e6},
    "kJ/m2": {"kj/m2": 1, "j/m2": 1e-3},
    "Shore D": {"shored": 1, "": 1, "hd": 1},
    "g/10 min": {"g/10min": 1},
}


def to_canonical(prop: str, value: float, unit_raw: str):
    """Return (value_si, unit_si) or (None, reason) when the unit can't be converted."""
    if prop not in PROPERTY_UNITS:
        return None, f"property '{prop}' not in vocabulary"
    unit_si = PROPERTY_UNITS[prop][0]
    u = _norm_unit(unit_raw)
    if unit_si == "°C":
        if u in ("°c", "c", "ºc", "degc", "˚c"):
            return value, unit_si
        if u == "k":
            return value - 273.15, unit_si
        if u in ("°f", "f"):
            return (value - 32) * 5 / 9, unit_si
        return None, f"unknown temperature unit '{unit_raw}'"
    factors = _FACTORS.get(unit_si, {})
    if unit_si == "1e-6/K" and re.search(r"10-6|ppm|[uµ]m/m", u):
        return value, unit_si  # per K and per °C are the same size for an expansion coefficient
    if unit_si == "W/(m·K)" and re.fullmatch(r"w/\(?m\.?x?k\)?|wm-1k-1", u.replace("·", "")):
        return value, unit_si
    if u in factors:
        return value * factors[u], unit_si
    if _norm_unit(unit_si) == u:
        return value, unit_si
    return None, f"cannot convert '{unit_raw}' to {unit_si}"


_NUM = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def parse_number(text) -> float | None:
    if text is None:
        return None
    s = str(text).strip().replace("−", "-").replace("–", "-").replace(" ", "").replace(" ", "")
    if not s or s.lower() in ("nan", "none"):
        return None
    if _NUM.match(s):
        return float(s)
    return None
