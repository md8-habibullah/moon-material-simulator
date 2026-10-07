"""Train the model and write everything the static frontend needs to frontend/src/generated/.

Run from the backend folder:  python -m scripts.export_frontend [--skip-ntrs]

Outputs:
  forest.json           the trained Random Forest, for in-browser predictions
  catalog.json          materials, uses, physics constants, metrics, NASA validation and sources
  parity_fixtures.json  Python predictions the JS engine must reproduce (frontend `npm test`)
  ntrs_snapshot.json    NASA NTRS search results, so the research panel works on GitHub Pages
"""
import argparse
import json
import random
from datetime import date

from config import BASE_DIR, DATA_PATH, RANDOM_SEED
from data.generate_dataset import generate
from models.property_model import PropertyModel
from services import ntrs
from services.catalog import build_catalog
from utils.materials import BINDERS, MAX_TOTAL_FILLER_WT, RANGES, REGOLITHS

OUT_DIR = BASE_DIR.parent / "frontend" / "src" / "generated"
SNAPSHOT_QUERIES = [
    "regolith polymer composite",
    "lunar regolith simulant polymer",
    "polyhydroxybutyrate",
    "in-situ resource utilization regolith manufacturing",
    "regolith additive construction",
    "lunar regolith simulant mechanical properties",
]
PINNED = ["20230015024", "20240004186"]


def write(name: str, payload) -> None:
    path = OUT_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"  wrote {path.relative_to(BASE_DIR.parent)} ({path.stat().st_size // 1024} KB)")


def parity_rows(n: int = 60) -> list[dict]:
    rng = random.Random(RANDOM_SEED)
    rows = []
    for _ in range(n):
        regolith_wt = round(rng.uniform(*RANGES["regolith_wt"]), 2)
        fiber_wt = round(min(rng.choice([0.0, rng.uniform(*RANGES["fiber_wt"])]), MAX_TOTAL_FILLER_WT - regolith_wt), 2)
        rows.append(
            {
                "binder": rng.choice(list(BINDERS)),
                "regolith": rng.choice(list(REGOLITHS)),
                "regolith_wt": regolith_wt,
                "fiber_wt": fiber_wt,
                "particle_size": round(rng.uniform(*RANGES["particle_size"]), 1),
                "temperature": round(rng.uniform(*RANGES["temperature"]), 1),
            }
        )
    return rows


def ntrs_snapshot() -> dict:
    seen, results = set(), []
    for query in SNAPSHOT_QUERIES:
        for record in ntrs.search(query, size=10):
            if record["id"] not in seen:
                seen.add(record["id"])
                results.append({**record, "query": query})
    results.sort(key=lambda r: (r["id"] not in PINNED, -(r["year"] or 0)))
    return {"fetched": date.today().isoformat(), "queries": SNAPSHOT_QUERIES, "results": results[:40]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-ntrs", action="store_true", help="keep the existing NTRS snapshot")
    args = parser.parse_args()

    if not DATA_PATH.exists():
        generate().to_csv(DATA_PATH, index=False)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    model = PropertyModel.train()
    print(f"Trained on {model.training_rows} rows; hold-out R² " + ", ".join(f"{k}={v['r2']}" for k, v in model.metrics.items()))
    write("forest.json", model.export())
    write("catalog.json", build_catalog(model))
    rows = parity_rows()
    write("parity_fixtures.json", [{"input": r, **p} for r, p in zip(rows, model.predict_many(rows))])

    if args.skip_ntrs:
        print("  kept existing ntrs_snapshot.json")
        return
    try:
        write("ntrs_snapshot.json", ntrs_snapshot())
    except ntrs.NTRSError as exc:
        if (OUT_DIR / "ntrs_snapshot.json").exists():
            print(f"  NTRS unavailable ({exc}); kept existing ntrs_snapshot.json")
        else:
            raise


if __name__ == "__main__":
    main()
