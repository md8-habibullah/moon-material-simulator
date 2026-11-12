"""The Evidence Auditor must re-find values in their source PDF and name the right kind of error.

Cases use NASA KSC's paper (S003, NTRS 20230015024): Table 3 has 0°/90° sub-rows and wrapped,
stacked headers; Table 4 has a two-level header (0°/90° over Average/Std Dev.). Skipped when the
PDF hasn't been downloaded (research/pdfs is not in git; see research/download_sources.py).
"""
import pytest

from evidence.audit import check_location, load_sources
from evidence.schema import PDF_DIR, parse_number, to_canonical

SOURCES = load_sources()
S003 = SOURCES["S003"]
pytestmark = pytest.mark.skipif(not (PDF_DIR / S003["file"]).exists(), reason="S003 PDF not downloaded")

BASE = dict(obs_id="T", source_id="S003", anchor_type="table", extraction="table", confidence="high", notes="", unit_raw="MPa")
T3 = dict(page="10", anchor_id="Table 3")
T4 = dict(page="11", anchor_id="Table 4", orientation="")

CASES = [
    ("CELL_MATCH", {**T3, "row_label": "70/30 BP-1/PLA", "col_label": "Avg Ultimate Flexural Strength (MPa)", "orientation": "0º", "value_raw": "30.17"}),
    ("CELL_MATCH", {**T3, "row_label": "70/30 BP-1/PLA", "col_label": "Avg Ultimate Flexural Strength (MPa)", "orientation": "90º", "value_raw": "17.50"}),
    ("WRONG_ROW", {**T3, "row_label": "70/30 BP-1/PLA", "col_label": "Avg Ultimate Flexural Strength (MPa)", "orientation": "90º", "value_raw": "30.17"}),
    ("CELL_MATCH", {**T3, "row_label": "85/15 BP1/PLA", "col_label": "Avg Ultimate Tensile Strength (MPa)", "orientation": "90º", "value_raw": "11.40"}),
    ("UNIT_MISMATCH", {**T3, "row_label": "85/15 BP1/PLA", "col_label": "Avg Compressive Modulus (Gpa)", "orientation": "0º", "value_raw": "6300"}),
    ("CELL_MATCH", {**T3, "row_label": "80/20 BP1/PLA w/ Additive", "col_label": "Avg Flexural Modulus (GPa)", "orientation": "90º", "value_raw": "3.13"}),
    ("ROUNDING", {**T3, "row_label": "80/20 BP1/PLA w/ Additive", "col_label": "Avg Flexural Modulus (GPa)", "orientation": "90º", "value_raw": "3.1"}),
    ("CELL_MATCH", {**T3, "row_label": "80/20 LHS-1/PLA", "col_label": "Avg Ultimate Flexural Strength (MPa)", "orientation": "90º", "value_raw": "14.90"}),
    ("WRONG_ROW", {**T3, "row_label": "80/20 BP1/PLA", "col_label": "Avg Ultimate Compressive Strength (MPa)", "orientation": "0º", "value_raw": "47.88"}),
    ("CELL_MATCH", {**T3, "row_label": "80/20 BP1/PLA", "col_label": "Avg Ultimate Compressive Strength (MPa)", "orientation": "90º", "value_raw": "47.88"}),
    ("CELL_MATCH", {**T4, "row_label": "Tensile Strength (MPa)", "col_label": "0º Average", "value_raw": "15.2"}),
    ("CELL_MATCH", {**T4, "row_label": "Flexural Strength (MPa)", "col_label": "90º Average", "value_raw": "16.6"}),
    ("WRONG_COLUMN", {**T4, "row_label": "Flexural Strength (MPa)", "col_label": "90º Average", "value_raw": "24"}),
    ("CELL_MATCH", {**T4, "row_label": "Compression Modulus (GPa)", "col_label": "90º Std Dev.", "value_raw": "0.07"}),
    ("WRONG_PAGE", {**T3, "page": "5", "row_label": "70/30 BP-1/PLA", "col_label": "Avg Ultimate Tensile Strength (MPa)", "orientation": "0º", "value_raw": "10.92"}),
    ("TEXT_MATCH", {"page": "11", "anchor_type": "text", "anchor_id": "Strength Properties Discussion", "row_label": "", "col_label": "", "orientation": "", "value_raw": "23.86"}),
]


@pytest.mark.parametrize("expected,case", CASES, ids=[f"{e}-{c['value_raw']}" for e, c in CASES])
def test_location_verdicts(expected, case):
    row = {**BASE, **case, "value": case["value_raw"]}
    assert check_location(row, S003).verdict == expected


def test_unit_conversion():
    assert to_canonical("tensile_modulus", 7000, "MPa") == (7.0, "GPa")
    assert to_canonical("compressive_strength", 2.0, "ksi")[0] == pytest.approx(13.79, rel=1e-3)
    assert to_canonical("decomposition_temp", 554.85, "K")[0] == pytest.approx(281.7)
    assert to_canonical("density", 1500, "kg/m3") == (1.5, "g/cm3")
    assert to_canonical("tensile_strength", 1, "furlongs")[0] is None
    assert parse_number("−1.5") == -1.5 and parse_number("n/a") is None
