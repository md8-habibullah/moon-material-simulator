"""The physics model has to agree with NASA's measurements and with what the pitch video claims."""
import csv

import pytest

from config import BASE_DIR
from utils.materials import composite_properties, in_situ_fraction, room_temperature_properties


def rt(binder, wt, regolith="lunar_highlands", fiber=0, size=60):
    return room_temperature_properties(wt, fiber, size, regolith, binder)


def _grouped_errors(property_name=None):
    """Model vs NASA, averaging 0°/90° results (the model predicts orientation-averaged values)."""
    with open(BASE_DIR / "data" / "nasa_reference_points.csv", newline="") as fh:
        points = list(csv.DictReader(fh))
    groups = {}
    for p in points:
        if property_name and p["property"] != property_name:
            continue
        key = (p["binder"], p["regolith"], p["regolith_wt_actual"], p["temperature_c"], p["property"])
        groups.setdefault(key, []).append(float(p["value"]))
    errors = []
    for (binder, regolith, wt, temp, prop), values in groups.items():
        regolith = regolith if regolith != "none" else "lunar_highlands"
        predicted = composite_properties(float(wt), 0, 60, regolith, binder, float(temp))[prop]
        measured = sum(values) / len(values)
        errors.append(abs(predicted - measured) / measured)
    return errors


def test_matches_nasa_measurements():
    errors = _grouped_errors()
    assert len(errors) >= 35
    assert sum(errors) / len(errors) < 0.10
    assert max(errors) < 0.35


def test_matches_nasa_glenn_phb_tensile():
    errors = _grouped_errors("tensile_strength")
    assert sum(errors) / len(errors) < 0.10


def test_phb_keeps_most_strength_at_high_loading():
    """NASA Glenn: PHB composites held 16-23 MPa from 20 to 80 wt% (neat 29.4 MPa)."""
    assert rt("PHB", 0)["tensile_strength"] == pytest.approx(29.4, rel=0.01)
    assert rt("PHB", 80)["tensile_strength"] > 0.55 * rt("PHB", 0)["tensile_strength"]


def test_video_claims_ten_percent_tool_fifty_percent_structure():
    ten, fifty = rt("PHB", 10), rt("PHB", 50)
    assert ten["tensile_strength"] > fifty["tensile_strength"]  # strong
    assert ten["elongation_at_break"] > fifty["elongation_at_break"]  # flexible
    assert fifty["density"] > ten["density"]  # dense
    assert fifty["max_service_temp"] > ten["max_service_temp"]  # heat resistant
    assert fifty["elastic_modulus"] > ten["elastic_modulus"]  # stiff, for structures


def test_iron_rich_martian_soil_lowers_decomposition_temperature():
    """NASA Glenn: MGS-1 / JEZ-1 cut PHB's decomposition temperature by 12-22 °C."""
    drop_mars = rt("PHB", 0)["decomposition_temp"] - rt("PHB", 40, "martian")["decomposition_temp"]
    drop_moon = rt("PHB", 0)["decomposition_temp"] - rt("PHB", 40, "lunar_highlands")["decomposition_temp"]
    assert 12 < drop_mars < 22
    assert drop_moon < 6


def test_finer_grains_are_stronger():
    assert rt("PHB", 30, size=15)["tensile_strength"] > rt("PHB", 30, size=150)["tensile_strength"]


def test_basalt_fibre_reinforces():
    assert rt("PHB", 30, fiber=10)["tensile_strength"] > rt("PHB", 30)["tensile_strength"]
    assert rt("PHB", 30, fiber=10)["elastic_modulus"] > rt("PHB", 30)["elastic_modulus"]


@pytest.mark.parametrize("binder", ["PHB", "PLA", "PEEK", "LDPE"])
def test_matrix_softens_above_its_service_temperature(binder):
    props = rt(binder, 30)
    hot = composite_properties(30, 0, 60, "lunar_highlands", binder, props["max_service_temp"] + 30)
    assert hot["tensile_strength"] < 0.2 * props["tensile_strength"]


def test_pla_at_77k_matches_nasa_table():
    assert composite_properties(0, 0, 60, "lunar_highlands", "PLA", -196)["tensile_strength"] == pytest.approx(87, rel=0.05)


def test_in_situ_fraction():
    assert in_situ_fraction(40, 5, "PHB") == 1.0
    assert in_situ_fraction(40, 5, "PEEK") == pytest.approx(0.45)
