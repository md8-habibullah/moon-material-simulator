"""Evidence for the website: every real measurement behind the model, with a picture of where it came from.

Writes
  frontend/src/generated/evidence_points.json   measurements (value, mix, source, page, audit verdict)
  frontend/public/evidence/<obs_id>.jpg         a crop of the source PDF with the value boxed

Only first-hand, experimental, room-temperature measurements of properties the simulator predicts
are exported (cited literature values and duplicates are left out). Crops need the PDFs in
research/pdfs; without them the points are still exported, just without pictures.
"""
import base64
import json

from config import BASE_DIR
from evidence.schema import AUDIT_DIR, PDF_DIR
from models.evidence_model import TARGET_PROPERTY, EvidenceModel, usable_measurements

FRONTEND = BASE_DIR.parent / "frontend"
CROP_DIR = FRONTEND / "public" / "evidence"
PROPERTY_TO_TARGET = {v: k for k, v in TARGET_PROPERTY.items()}


def export(model: EvidenceModel, sources: dict) -> list[dict]:
    audit = json.loads((AUDIT_DIR / "audit_index.json").read_text()) if (AUDIT_DIR / "audit_index.json").exists() else {}
    df = usable_measurements()
    used = {target: set(d["obs_id"]) for target, d in model.training.items()}
    CROP_DIR.mkdir(parents=True, exist_ok=True)
    # Re-render crops only where the PDFs are present (they are not in git, e.g. in CI); otherwise
    # keep the committed pictures.
    have_pdfs = all((PDF_DIR / src["file"]).exists() for sid, src in sources.items() if sid in set(df["source_id"]))
    if have_pdfs:
        from evidence.report import _crop  # needs PyMuPDF + Pillow (requirements-dev.txt)

        for old in CROP_DIR.glob("*.jpg"):
            old.unlink()
    points = []
    for _, r in df.iterrows():
        target = PROPERTY_TO_TARGET[r["model_property"]]
        a = audit.get(r["obs_id"], {})
        verdicts = a.get("verdicts", [])
        main = next((v for v in verdicts if v["verdict"] in (
            "CELL_MATCH", "TEXT_MATCH", "ROW_MATCH", "SPLIT_MATCH", "PAGE_MATCH", "CHART_ESTIMATE", "SCAN_VISUAL")), verdicts[0] if verdicts else None)
        img = f"{r['obs_id']}.jpg" if (CROP_DIR / f"{r['obs_id']}.jpg").exists() else None
        src = sources.get(r["source_id"])
        if have_pdfs and src:
            boxes = [tuple(b) for b in a.get("boxes", [])]
            full = not boxes
            try:
                data = _crop(src["file"], int(r["page"]), boxes, full, pad=26)
                img = f"{r['obs_id']}.jpg"
                (CROP_DIR / img).write_bytes(base64.b64decode(data))
            except Exception as exc:  # keep exporting even if one page fails to render
                print(f"  ! crop failed for {r['obs_id']}: {exc}")
        points.append({
            "id": r["obs_id"],
            "target": target,
            "value": round(float(r["value_si"]), 4),
            "std": None if r["std_si"] != r["std_si"] else round(float(r["std_si"]), 4),
            "unit": r["unit_si"],
            "binder": r["binder_key"],
            "filler": r["filler"],
            "soil": r["soil"],
            "wt": round(float(r["wt"]), 2),
            "phi": round(float(r["phi"]), 4),
            "process": r["process_key"],
            "orientation": r["orientation"] or None,
            "source": r["source_id"],
            "page": int(r["page"]),
            "anchor": r["anchor_id"],
            "row": r["row_label"] or None,
            "col": r["col_label"] or None,
            "value_raw": r["value_raw"],
            "unit_raw": r["unit_raw"],
            "extraction": r["extraction"],
            "confidence": r["confidence"],
            "verdict": main["verdict"] if main else None,
            "audit": main["message"] if main else None,
            "severity": a.get("severity"),
            "used": r["obs_id"] in used.get(target, set()),
            "img": img,
        })
    return points
