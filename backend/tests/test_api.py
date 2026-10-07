import pytest
from fastapi.testclient import TestClient

from main import app

BASE = {"regolith_wt": 30, "regolith_type": "lunar", "polymer_type": "PLA", "temperature": 23}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "model_ready": True}


def test_predict_returns_all_properties(client):
    body = client.post("/api/predict", json=BASE).json()
    assert set(body["properties"]) == {"tensile_strength", "elastic_modulus", "compressive_strength", "thermal_stability"}
    assert all(v > 0 for v in body["properties"].values())
    assert 0 < body["volume_fraction"] < 0.3


def test_regolith_stiffens_the_matrix(client):
    neat = client.post("/api/predict", json={**BASE, "regolith_wt": 0}).json()["properties"]
    filled = client.post("/api/predict", json={**BASE, "regolith_wt": 45}).json()["properties"]
    assert filled["elastic_modulus"] > neat["elastic_modulus"]


def test_peek_handles_heat_better_than_pla(client):
    pla = client.post("/api/predict", json=BASE).json()["properties"]
    peek = client.post("/api/predict", json={**BASE, "polymer_type": "PEEK"}).json()["properties"]
    assert peek["thermal_stability"] > pla["thermal_stability"]


@pytest.mark.parametrize(
    "patch",
    [{"regolith_wt": 80}, {"regolith_wt": -1}, {"regolith_type": "venus"}, {"polymer_type": "ABS"}, {"temperature": 900}],
)
def test_rejects_invalid_input(client, patch):
    assert client.post("/api/predict", json={**BASE, **patch}).status_code == 422


def test_compare_limits_items(client):
    assert len(client.post("/api/compare", json={"items": [BASE] * 3}).json()["results"]) == 3
    assert client.post("/api/compare", json={"items": [BASE] * 7}).status_code == 422
    assert client.post("/api/compare", json={"items": []}).status_code == 422


def test_model_info(client):
    info = client.get("/api/model").json()
    assert info["training_rows"] > 1000
    assert all(m["r2"] > 0.8 for m in info["holdout_metrics"].values())
