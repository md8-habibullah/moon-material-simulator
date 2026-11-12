"""Everything the frontend needs to know about materials, uses, the model and its NASA sources.

Served at GET /api/catalog and written to frontend/src/generated/catalog.json by
scripts/export_frontend.py, so the hosted (static) site and the API always agree.
"""
import csv

import sklearn

from config import BASE_DIR
from models.property_model import FOREST_PARAMS, PropertyModel
from utils import materials as m
from utils.applications import APPLICATIONS
from utils.data_processor import FEATURE_COLUMNS, TARGET_COLUMNS, UNITS

NASA_POINTS_PATH = BASE_DIR / "data" / "nasa_reference_points.csv"
SOURCES_PATH = BASE_DIR.parent / "research" / "sources.csv"


def evidence_sources() -> dict:
    """The research registry (research/sources.csv), keyed by source id, for citations in the app."""
    if not SOURCES_PATH.exists():
        return {}
    with open(SOURCES_PATH, newline="", encoding="utf-8") as fh:
        keep = ("title", "authors", "year", "venue", "doi", "url", "ntrs_id", "licence", "type", "binders", "fillers")
        return {r["source_id"]: {k: r[k] for k in keep} for r in csv.DictReader(fh)}

NASA_SOURCES = [
    {
        "id": "nasa-glenn-2026",
        "kind": "NASA article",
        "title": "Under the Microscope: NASA-Made Material for Moon Manufacturing",
        "publisher": "NASA Glenn Research Center (E. Bausback)",
        "date": "2026-09-29",
        "url": "https://www.nasa.gov/image-article/nasa-made-material-moon-manufacturing/",
        "used_for": "The core idea: a biodegradable plastic grown by bacteria (fed CO₂ or crew waste), "
        "mixed with simulated Moon and Mars dust, which made it stronger. Target uses: brackets, wrenches, chairs.",
    },
    {
        "id": "20260007758",
        "kind": "NTRS presentation",
        "title": "Biosynthesized Thermoplastic/Regolith Composites for Closed-Loop In-Space Manufacturing",
        "publisher": "NASA Glenn Research Center (A. Christy), ACS Fall 2026",
        "date": "2026-08-12",
        "url": "https://ntrs.nasa.gov/citations/20260007758",
        "used_for": "The NASA Glenn PHB + regolith study behind the article: tensile strength (slide 17), "
        "decomposition temperature and crystallinity (slide 9) for five lunar and Martian simulants, "
        "and the $4,000 to $1M+ per kg launch-cost range.",
    },
    {
        "id": "20260003641",
        "kind": "NTRS presentation",
        "title": "Polymer/Regolith Composites for In-Space Manufacturing on the Moon and Mars",
        "publisher": "NASA Glenn Research Center (A. Christy, M. Ranaiefar, W. Fuchs)",
        "date": "2026-04-29",
        "url": "https://ntrs.nasa.gov/citations/20260003641",
        "used_for": "Processing routes (compression and injection molding up to 80 wt%, filament extrusion, 3D printing).",
    },
    {
        "id": "20230015024",
        "kind": "NTRS conference paper",
        "title": "Selection, Production, and Properties of Regolith Polymer Composites for Lunar Construction",
        "publisher": "NASA Kennedy Space Center Swamp Works, SpaceFactory, LERA (Gelino et al.)",
        "date": "2023-10-18",
        "url": "https://ntrs.nasa.gov/citations/20230015024",
        "used_for": "Binder properties (Appendix Table 8, incl. PHA/PHB and 77 K values) and 18 measured, "
        "3D-printed LHS-1/BP-1 + PLA composite results (Tables 2-4) used to calibrate and validate the model.",
    },
    {
        "id": "20240004186",
        "kind": "NTRS presentation",
        "title": "Selection, Production and Properties of Regolith Polymer Composite for Lunar Construction",
        "publisher": "NASA Kennedy Space Center",
        "date": "2024-04-10",
        "url": "https://ntrs.nasa.gov/citations/20240004186",
        "used_for": "Context on printing regolith-polymer composites for lunar infrastructure.",
    },
]


def physics_constants() -> dict:
    """Constants the browser engine needs to mirror utils.materials exactly."""
    return {
        "room_temp": m.ROOM_TEMP_C,
        "room_to_77k": m.ROOM_TO_77K,
        "porosity_base": m.POROSITY_BASE,
        "porosity_coef": m.POROSITY_COEF,
        "size_ref_um": m.SIZE_REF_UM,
        "size_coef": m.SIZE_COEF,
        "size_min": m.SIZE_MIN,
        "size_max": m.SIZE_MAX,
        "softening_width": m.SOFTENING_WIDTH,
        "hot_stretch_width": m.HOT_STRETCH_WIDTH,
        "hot_stretch_gain": m.HOT_STRETCH_GAIN,
        "max_total_filler_wt": m.MAX_TOTAL_FILLER_WT,
        "baseline_keys": m.BASELINE_KEYS,
    }


def nasa_validation(model: PropertyModel) -> list[dict]:
    """NASA's measured composites next to what the model predicts for the same mix."""
    with open(NASA_POINTS_PATH, newline="") as fh:
        points = list(csv.DictReader(fh))
    rows = [
        {
            "binder": p["binder"],
            "regolith": p["regolith"] if p["regolith"] != "none" else "lunar_highlands",
            "regolith_wt": float(p["regolith_wt_actual"]),
            "fiber_wt": 0.0,
            "particle_size": m.SIZE_REF_UM,
            "temperature": float(p["temperature_c"]),
            # NASA Glenn injection-molded its PHB coupons; NASA Kennedy printed PLA from pellets.
            "process": "molded" if p["binder"] == "PHB" else "pellet" if p["binder"] == "PLA" else None,
        }
        for p in points
    ]
    predictions = model.predict_many(rows)
    out = []
    for p, pred in zip(points, predictions):
        value = float(p["value"])
        predicted = pred["properties"][p["property"]]
        out.append(
            {
                "source": p["source"],
                "table": p["table"],
                "binder": p["binder"],
                "regolith": p["regolith"],
                "simulant": p["simulant"] or None,
                "regolith_wt": float(p["regolith_wt_actual"]),
                "regolith_wt_target": float(p["regolith_wt_target"]),
                "orientation": p["orientation"] or None,
                "temperature": float(p["temperature_c"]),
                "property": p["property"],
                "measured": value,
                "std": float(p["std"]) if p["std"] else None,
                "predicted": round(predicted, 3),
                "error_pct": round((predicted - value) / value * 100, 1),
                "note": p["note"],
            }
        )
    return out


def evidence_summary(model: PropertyModel) -> dict:
    """What the evidence correction was trained on and how well it predicts held-out data."""
    grid = model.evidence_grid or {"targets": {}}
    return {
        target: {
            "property": t["property"],
            "n_train": t["n_train"],
            "sources": t["sources"],
            "calibration": t["calibration"],
            "validation": t["validation"],
            "hyper": t["hyper"],
        }
        for target, t in grid["targets"].items()
    }


def binder_processes(model: PropertyModel) -> dict:
    """For each binder, the processes it has real measurements for (any property)."""
    grid = model.evidence_grid or {"targets": {}}
    out = {b: set() for b in m.BINDERS}
    for t in grid["targets"].values():
        for key, cell in t["table"].items():
            binder, process = key.split("|")
            if any(cell["same"]):
                out[binder].add(process)
    return {b: sorted(v) for b, v in out.items()}


def build_catalog(model: PropertyModel) -> dict:
    return {
        "binders": m.BINDERS,
        "processes": m.PROCESSES,
        "default_process": m.DEFAULT_PROCESS,
        "binder_processes": binder_processes(model),
        "regoliths": m.REGOLITHS,
        "fiber": m.FIBER,
        "environments": m.ENVIRONMENTS,
        "ranges": {k: list(v) for k, v in m.RANGES.items()},
        "targets": TARGET_COLUMNS,
        "units": UNITS,
        "applications": APPLICATIONS,
        "physics": physics_constants(),
        "model": {
            "algorithm": "RandomForestRegressor (scikit-learn)",
            "sklearn_version": sklearn.__version__,
            "params": {k: v for k, v in FOREST_PARAMS.items() if k != "n_jobs"},
            "training_rows": model.training_rows,
            "features": FEATURE_COLUMNS,
            "holdout_metrics": model.metrics,
            "feature_importance": model.feature_importance(),
        },
        "validation": nasa_validation(model),
        "evidence": evidence_summary(model),
        "evidence_sources": evidence_sources(),
        "sources": NASA_SOURCES,
    }
