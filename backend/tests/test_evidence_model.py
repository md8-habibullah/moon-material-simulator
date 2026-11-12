"""The evidence correction must beat physics alone on real data it never saw, and stay in sync with the browser grid."""
import numpy as np
import pytest

from models.evidence_model import PHI_GRID, EvidenceModel, interpolate, usable_measurements


@pytest.fixture(scope="module")
def model():
    return EvidenceModel.train()


def test_uses_only_first_hand_room_temperature_measurements():
    df = usable_measurements()
    assert len(df) >= 100
    assert set(df["origin"]) == {"experimental"}
    assert set(df["cited"]) == {"no"}
    assert df["temp"].between(15, 30).all()
    assert df["process_key"].notna().all()


@pytest.mark.parametrize("target", ["compressive_strength", "density", "thermal_conductivity", "elastic_modulus"])
def test_beats_physics_on_untested_mixes(model, target):
    v = model.validation[target]["new_mix"]
    assert v["hybrid_mape"] < 0.6 * v["physics_mape"], v


def test_uncertainty_is_calibrated_on_untested_mixes(model):
    # With the calibration factor, at least ~80% of held-out mixes fall inside the 90% band.
    for target, v in model.validation.items():
        assert v["new_mix"]["coverage90"] >= 0.6, (target, v["new_mix"])
        assert v["new_mix"]["calibration"] >= 1.0


def test_far_from_data_falls_back_to_physics(model):
    # A binder/process with no data anywhere: correction near 0, uncertainty larger than near data.
    mu_far, sd_far = model.correction("decomposition_temp", 0.3, "PEEK", "fff")
    mu_near, sd_near = model.correction("decomposition_temp", 0.3, "PHB", "molded")
    assert abs(mu_far) < 0.02
    assert sd_far > sd_near


def test_grid_interpolation_matches_the_gp_at_grid_points(model):
    grid = model.export_grid()
    for target in grid["targets"]:
        for phi in PHI_GRID[::6]:
            mu, sd = model.correction(target, float(phi), "PLA", "pellet")
            g_mu, g_sd, _, _ = interpolate(grid, target, "PLA", "pellet", float(phi))
            assert g_mu == pytest.approx(mu, abs=1e-3)
            assert g_sd == pytest.approx(sd, abs=1e-3)
    assert np.all(np.diff(grid["phi"]) > 0)
