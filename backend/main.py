"""Moon-Material Simulator API.

Run from the backend folder:  uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import ALLOWED_ORIGINS, MAX_COMPARE_ITEMS
from models.property_model import PropertyModel
from utils.data_processor import UNITS
from utils.materials import ENVIRONMENTS, POLYMERS, REGOLITHS, volume_fraction

state: dict = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    state["model"] = PropertyModel.train()
    yield
    state.clear()


app = FastAPI(title="Moon-Material Simulator API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


class Composition(BaseModel):
    regolith_wt: float = Field(ge=0, le=50, description="Regolith content, weight %")
    regolith_type: Literal["lunar", "martian"]
    polymer_type: Literal["PLA", "PEEK", "LDPE"]
    temperature: float = Field(ge=-180, le=150, description="Operating temperature, °C")


class CompareRequest(BaseModel):
    items: list[Composition] = Field(min_length=1, max_length=MAX_COMPARE_ITEMS)


def _predict(c: Composition) -> dict:
    result = state["model"].predict(c.regolith_wt, c.regolith_type, c.polymer_type, c.temperature)
    env = ENVIRONMENTS[c.regolith_type]
    return {
        "inputs": c.model_dump(),
        **result,
        "units": UNITS,
        "volume_fraction": round(volume_fraction(c.regolith_wt, c.polymer_type, c.regolith_type), 4),
        "survives_surface_max_temp": result["properties"]["thermal_stability"] >= env["max_temp"],
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "model_ready": "model" in state}


@app.get("/api/options")
def options():
    return {
        "polymers": {k: {"name": v["name"], "biodegradable": v["biodegradable"]} for k, v in POLYMERS.items()},
        "regoliths": {k: {"name": v["name"]} for k, v in REGOLITHS.items()},
        "environments": ENVIRONMENTS,
        "ranges": {"regolith_wt": [0, 50], "temperature": [-180, 150]},
        "units": UNITS,
    }


@app.get("/api/model")
def model_info():
    model: PropertyModel = state["model"]
    return {
        "algorithm": "RandomForestRegressor (scikit-learn)",
        "training_rows": model.training_rows,
        "holdout_metrics": model.metrics,
        "feature_importance": model.feature_importance(),
        "data": "Synthetic, physics-informed dataset (see docs/data_dictionary.md)",
    }


@app.post("/api/predict")
def predict(composition: Composition):
    return _predict(composition)


@app.post("/api/compare")
def compare(req: CompareRequest):
    return {"results": [_predict(c) for c in req.items]}
