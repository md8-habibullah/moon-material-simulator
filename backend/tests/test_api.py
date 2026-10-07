import pytest
from fastapi.testclient import TestClient

import main
from services import ntrs

BASE = {"binder": "PHB", "regolith": "lunar_highlands", "regolith_wt": 30, "fiber_wt": 0, "particle_size": 60, "temperature": 23}
TARGETS = {
    "tensile_strength",
    "elastic_modulus",
    "compressive_strength",
    "elongation_at_break",
    "density",
    "thermal_conductivity",
    "max_service_temp",
    "decomposition_temp",
}


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "model_ready": True}


def test_predict_returns_all_properties(client):
    body = client.post("/api/predict", json=BASE).json()
    assert set(body["properties"]) == TARGETS
    assert set(body["uncertainty"]) == TARGETS
    assert all(v > 0 for v in body["properties"].values())
    assert body["in_situ_fraction"] == 1.0  # regolith is local and PHB can be grown on site


def test_shipped_binder_lowers_in_situ_fraction(client):
    body = client.post("/api/predict", json={**BASE, "binder": "PEEK"}).json()
    assert body["in_situ_fraction"] == pytest.approx(0.30)


def test_defaults_fill_optional_fields(client):
    body = client.post("/api/predict", json={"regolith": "martian", "regolith_wt": 20}).json()
    assert body["inputs"]["binder"] == "PHB"
    assert body["inputs"]["temperature"] == 23


@pytest.mark.parametrize(
    "patch",
    [
        {"regolith_wt": 81},
        {"regolith_wt": -1},
        {"fiber_wt": 16},
        {"regolith_wt": 80, "fiber_wt": 10},  # over the 85 wt% total filler limit
        {"particle_size": 5},
        {"regolith": "venus"},
        {"binder": "ABS"},
        {"temperature": 900},
    ],
)
def test_rejects_invalid_input(client, patch):
    assert client.post("/api/predict", json={**BASE, **patch}).status_code == 422


def test_compare_limits_items(client):
    assert len(client.post("/api/compare", json={"items": [BASE] * 3}).json()["results"]) == 3
    assert client.post("/api/compare", json={"items": [BASE] * 7}).status_code == 422
    assert client.post("/api/compare", json={"items": []}).status_code == 422


def test_catalog_has_everything_the_frontend_needs(client):
    catalog = client.get("/api/catalog").json()
    for key in ("binders", "regoliths", "applications", "physics", "model", "validation", "sources"):
        assert catalog[key]
    assert catalog["model"]["training_rows"] > 4000
    assert all(m["r2"] > 0.95 for m in catalog["model"]["holdout_metrics"].values())


def test_research_proxies_ntrs(client, monkeypatch):
    monkeypatch.setattr(ntrs, "search", lambda q, size=8: [{"id": "1", "title": f"about {q}"}])
    body = client.get("/api/research", params={"q": "regolith polymer"}).json()
    assert body["results"][0]["title"] == "about regolith polymer"


def test_research_hides_upstream_errors(client, monkeypatch):
    def boom(q, size=8):
        raise ntrs.NTRSError("connection reset by https://internal.example")

    monkeypatch.setattr(ntrs, "search", boom)
    res = client.get("/api/research", params={"q": "regolith"})
    assert res.status_code == 502
    assert "internal.example" not in res.text


@pytest.mark.parametrize("q", ["", "x", "a" * 101, "regolith<script>", "http://169.254.169.254/"])
def test_research_validates_query(client, q):
    assert client.get("/api/research", params={"q": q}).status_code == 422
