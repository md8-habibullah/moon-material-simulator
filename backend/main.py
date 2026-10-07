"""Moon-Material Simulator API.

Run from the backend folder:  uvicorn main:app --reload --host 127.0.0.1 --port 8000
The hosted site on GitHub Pages runs the same model in the browser; this API serves it to
scripts and notebooks and adds live NASA NTRS search.
"""
import logging
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from config import ALLOWED_ORIGINS, MAX_COMPARE_ITEMS
from models.property_model import PropertyModel
from services import ntrs
from services.catalog import build_catalog
from utils.materials import MAX_TOTAL_FILLER_WT, RANGES, in_situ_fraction

log = logging.getLogger("moon-material-api")
state: dict = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    model = PropertyModel.train()
    state["model"] = model
    state["catalog"] = build_catalog(model)
    yield
    state.clear()


app = FastAPI(title="Moon-Material Simulator API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


class Composition(BaseModel):
    binder: Literal["PHB", "PLA", "PEEK", "LDPE"] = "PHB"
    regolith: Literal["lunar_highlands", "lunar_mare", "martian"]
    regolith_wt: float = Field(ge=RANGES["regolith_wt"][0], le=RANGES["regolith_wt"][1], description="Regolith, weight %")
    fiber_wt: float = Field(0, ge=RANGES["fiber_wt"][0], le=RANGES["fiber_wt"][1], description="Basalt fibre, weight %")
    particle_size: float = Field(60, ge=RANGES["particle_size"][0], le=RANGES["particle_size"][1], description="Median grain size, µm")
    temperature: float = Field(23, ge=RANGES["temperature"][0], le=RANGES["temperature"][1], description="Operating temperature, °C")

    @model_validator(mode="after")
    def total_filler(self):
        if self.regolith_wt + self.fiber_wt > MAX_TOTAL_FILLER_WT:
            raise ValueError(f"regolith_wt + fiber_wt must not exceed {MAX_TOTAL_FILLER_WT}")
        return self


class CompareRequest(BaseModel):
    items: list[Composition] = Field(min_length=1, max_length=MAX_COMPARE_ITEMS)


def _predict(items: list[Composition]) -> list[dict]:
    rows = [c.model_dump() for c in items]
    results = state["model"].predict_many(rows)
    return [
        {
            "inputs": row,
            **result,
            "units": state["catalog"]["units"],
            "in_situ_fraction": round(in_situ_fraction(row["regolith_wt"], row["fiber_wt"], row["binder"]), 4),
        }
        for row, result in zip(rows, results)
    ]


@app.get("/api/health")
def health():
    return {"status": "ok", "model_ready": "model" in state}


@app.get("/api/catalog")
def catalog():
    return state["catalog"]


@app.get("/api/model")
def model_info():
    return state["catalog"]["model"]


@app.get("/api/validation")
def validation():
    return {"points": state["catalog"]["validation"]}


@app.post("/api/predict")
def predict(composition: Composition):
    return _predict([composition])[0]


@app.post("/api/compare")
def compare(req: CompareRequest):
    return {"results": _predict(req.items)}


@app.get("/api/research")
def research(q: str = Query(min_length=2, max_length=100, pattern=r"^[\w\s\-+.,'()/&]+$")):
    try:
        return {"query": q, "source": "live", "results": ntrs.search(q)}
    except ntrs.NTRSError as exc:
        log.warning("NTRS search failed: %s", exc)
        raise HTTPException(status_code=502, detail="NASA NTRS is unavailable right now. Try again shortly.") from None
