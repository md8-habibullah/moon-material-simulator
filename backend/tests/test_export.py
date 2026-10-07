"""The exported forest JSON must reproduce the Python model, since the hosted site runs on it."""
import math

import numpy as np
import pytest

from models.property_model import PropertyModel
from utils.data_processor import FEATURE_COLUMNS, TARGET_COLUMNS, encode_rows
from utils.materials import binder_baseline, temperature_factors


@pytest.fixture(scope="module")
def model():
    return PropertyModel.train()


def walk(tree, x):
    node = 0
    while tree["f"][node] != -1:
        # sklearn compares float32(x) against a float64 threshold.
        node = tree["l"][node] if np.float32(x[tree["f"][node]]) <= tree["t"][node] else tree["r"][node]
    return tree["l"][node]


def predict_from_json(export, row):
    x = encode_rows([row])[0]
    n = len(export["targets"])
    mean, std = export["transform"]["mean"], export["transform"]["std"]
    base = binder_baseline(row["binder"])
    per_tree = []
    for tree in export["trees"]:
        leaf = walk(tree, x)
        z = tree["v"][leaf * n : (leaf + 1) * n]
        props = {t: math.exp(z[i] * std[i] + mean[i]) * base[t] for i, t in enumerate(export["targets"])}
        factors = temperature_factors(row["binder"], props["max_service_temp"], row["temperature"])
        per_tree.append([props[t] * factors[t] for t in export["targets"]])
    return np.mean(per_tree, axis=0)


def test_export_shape(model):
    export = model.export()
    assert export["features"] == FEATURE_COLUMNS
    assert export["targets"] == TARGET_COLUMNS
    assert len(export["trees"]) == model.forest.n_estimators


@pytest.mark.parametrize(
    "row",
    [
        {"binder": "PHB", "regolith": "lunar_highlands", "regolith_wt": 10, "fiber_wt": 0, "particle_size": 60, "temperature": 23},
        {"binder": "PLA", "regolith": "lunar_mare", "regolith_wt": 74.5, "fiber_wt": 5, "particle_size": 25, "temperature": -173},
        {"binder": "PEEK", "regolith": "martian", "regolith_wt": 45.3, "fiber_wt": 12, "particle_size": 140, "temperature": 127},
        {"binder": "LDPE", "regolith": "lunar_highlands", "regolith_wt": 0, "fiber_wt": 0, "particle_size": 10, "temperature": -200},
    ],
)
def test_json_forest_matches_python(model, row):
    expected = model.predict_many([row])[0]["properties"]
    got = predict_from_json(model.export(), row)
    for i, target in enumerate(TARGET_COLUMNS):
        assert got[i] == pytest.approx(expected[target], rel=1e-3, abs=1e-3)
