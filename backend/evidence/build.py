"""Merge research/extraction/*.csv into data/evidence/measurements.csv.

Run from the backend folder:  python -m evidence.build

Nothing is dropped or corrected here. Rows keep their values exactly as transcribed. The build only
adds derived columns: a stable obs_id, the value in the canonical unit for its property, and the
effective regolith wt% (measured if the source gives it, otherwise the target). Rows whose unit can't
be converted keep an empty value_si, and the auditor reports them.
"""
import csv
import re

from .schema import (
    EVIDENCE_DIR,
    EXTRACTION_COLUMNS,
    EXTRACTION_DIR,
    MEASUREMENTS_CSV,
    MEASUREMENT_COLUMNS,
    model_property,
    parse_number,
    to_canonical,
)


def read_extraction(path) -> tuple[list[dict], list[str]]:
    """Rows of one extraction CSV plus any header problems."""
    problems = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = [h.strip() for h in (reader.fieldnames or [])]
        missing = [c for c in EXTRACTION_COLUMNS if c not in header]
        extra = [c for c in header if c not in EXTRACTION_COLUMNS]
        if missing:
            problems.append(f"{path.name}: missing columns {missing}")
        if extra:
            problems.append(f"{path.name}: unexpected columns {extra}")
        rows = [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in reader]
    return rows, problems


def derive(row: dict, obs_id: str) -> dict:
    out = {c: row.get(c, "") for c in EXTRACTION_COLUMNS}
    out["obs_id"] = obs_id
    value, std = parse_number(row.get("value")), parse_number(row.get("std"))
    prop = model_property(row.get("property", ""))
    out["model_property"] = prop
    value_si, unit_si = (None, "")
    if value is not None and prop:
        value_si, unit_or_reason = to_canonical(prop, value, row.get("unit_raw", ""))
        unit_si = unit_or_reason if value_si is not None else ""
    std_si = None
    if std is not None and value not in (None, 0) and value_si is not None:
        std_si = std * value_si / value
    out["value_si"] = "" if value_si is None else f"{value_si:.6g}"
    out["std_si"] = "" if std_si is None else f"{std_si:.6g}"
    out["unit_si"] = unit_si
    actual, target = parse_number(row.get("regolith_wt_actual")), parse_number(row.get("regolith_wt_target"))
    wt = actual if actual is not None else target
    out["regolith_wt"] = "" if wt is None else f"{wt:g}"
    out["cited"] = "yes" if row.get("notes", "").upper().startswith("CITED:") else "no"
    # Extractors mark values that repeat another source (e.g. a slide restating a paper's table).
    dup = re.search(r"DUPLICATE of (S\d{3})", row.get("notes", ""), re.I)
    out["duplicate_of"] = dup.group(1).upper() if dup else ""
    return out


def build() -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    for path in sorted(EXTRACTION_DIR.glob("S*.csv")):
        source_rows, file_problems = read_extraction(path)
        problems += file_problems
        source_id = path.stem
        for i, row in enumerate(source_rows, start=1):
            if row.get("source_id") and row["source_id"] != source_id:
                problems.append(f"{path.name} row {i}: source_id {row['source_id']} differs from file name")
            row["source_id"] = source_id
            rows.append(derive(row, f"{source_id}-{i:03d}"))
    return rows, problems


def main() -> None:
    rows, problems = build()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(MEASUREMENTS_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MEASUREMENT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    by_source = {}
    for r in rows:
        by_source[r["source_id"]] = by_source.get(r["source_id"], 0) + 1
    print(f"Wrote {len(rows)} measurements to {MEASUREMENTS_CSV}")
    print("  " + ", ".join(f"{k}: {v}" for k, v in sorted(by_source.items())))
    for p in problems:
        print(f"  ! {p}")


if __name__ == "__main__":
    main()
