"""Evidence Auditor: checks every measurement against its source PDF and writes comments.

Run from the backend folder:  python -m evidence.audit

It NEVER edits data. Output:
  research/audit/audit_comments.csv   one row per finding
  research/audit/audit_index.json     per-observation verdict + PDF location (used by the website)
  research/audit/audit_report.html    self-contained report with highlighted PDF crops

Checks
  location   the value is re-found in the PDF: right page, right table row and column, right unit
  schema     vocabularies, numbers, page ranges, convertible units
  sanity     values outside plausible physical ranges (often a unit slip), std larger than the value
  composition measured vs target filler content
  duplicates the same cell transcribed twice
  spread     the same mix measured by different labs disagrees (information, not an error)
  sources    problems inside the papers themselves (from research/extraction/*_issues.md)
  model      the simulator's own calibration points (data/nasa_reference_points.csv) vs the evidence
  coverage   numbers the earlier automatic extraction found that the dataset doesn't contain
"""
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from config import BASE_DIR

from .pdfindex import Box, NumberHit, open_pdf
from .schema import (
    ANCHOR_TYPES,
    AUDIT_DIR,
    CONFIDENCES,
    EXTRACTION_DIR,
    EXTRACTIONS,
    MEASUREMENTS_CSV,
    ORIGINS,
    PROCESSES,
    PROPERTY_UNITS,
    RESEARCH_DIR,
    is_known_property,
    SOIL_TYPES,
    SOURCES_CSV,
    parse_number,
)

SEVERITY = {
    # verdict: (severity, short meaning)
    "CELL_MATCH": ("ok", "value found in the cited table cell"),
    "TEXT_MATCH": ("ok", "value found in the cited text"),
    "ROW_MATCH": ("ok", "value found on the cited row (column header not located)"),
    "PAGE_MATCH": ("info", "value found on the cited page; cell position not confirmed"),
    "ROUNDING": ("info", "differs from the source only by rounding"),
    "CHART_ESTIMATE": ("info", "read from a chart; check visually"),
    "SCAN_VISUAL": ("info", "scanned page: the text layer can't be trusted, so check the page image"),
    "CELL_MISMATCH": ("error", "the cited cell holds a different number"),
    "WRONG_COLUMN": ("error", "value is on the cited row but in another column"),
    "WRONG_ROW": ("error", "value is in the cited column but on another row"),
    "UNIT_MISMATCH": ("error", "the source has this value in another unit (×1000)"),
    "WRONG_PAGE": ("warning", "value not on the cited page, but found on another page"),
    "NOT_FOUND": ("error", "value not found in the source"),
    "SPLIT_MATCH": ("ok", "value found, printed split over two or three text fragments"),
    "SCHEMA": ("error", "row breaks the extraction spec"),
    "RANGE_ONLY": ("info", "a range or bound, kept for context; not used by the model"),
    "VOCAB": ("warning", "value outside the controlled vocabulary"),
    "UNIT_UNCONVERTIBLE": ("warning", "unit can't be converted to the canonical unit"),
    "UNIT_SUSPECT": ("warning", "value outside the plausible range for this property"),
    "STD_SUSPECT": ("warning", "standard deviation is as large as the value"),
    "COMPOSITION": ("info", "measured filler content differs from the target"),
    "DUPLICATE": ("warning", "the same cell was transcribed more than once"),
    "CROSS_SOURCE_SPREAD": ("info", "different labs disagree on a comparable mix"),
    "SOURCE_ISSUE": ("info", "problem inside the source paper itself"),
    "MODEL_REFERENCE_MATCH": ("ok", "simulator calibration point agrees with the evidence"),
    "MODEL_REFERENCE_MISMATCH": ("error", "simulator calibration point disagrees with the evidence"),
    "MODEL_REFERENCE_UNVERIFIED": ("warning", "simulator calibration point has no matching evidence row"),
    "POSSIBLE_MISSED_VALUE": ("info", "the source mentions this number but the dataset doesn't contain it"),
}

COLORS = {"row": (0.10, 0.45, 0.95), "col": (0.55, 0.25, 0.85), "ours": (0.10, 0.65, 0.25), "cell": (0.90, 0.15, 0.15)}
DASH_TABLE = str.maketrans({c: "-" for c in "‐‑‒–—−"})  # every dash/minus variant -> "-"


@dataclass
class Comment:
    verdict: str
    message: str
    obs_id: str = ""
    source_id: str = ""
    page: int | None = None
    anchor_id: str = ""
    row_label: str = ""
    col_label: str = ""
    field_name: str = "value"
    our_value: str = ""
    source_value: str = ""
    boxes: list = field(default_factory=list)  # [(kind, (x0, y0, x1, y1))]
    full_page: bool = False

    @property
    def severity(self) -> str:
        return SEVERITY[self.verdict][0]


def _decimals(text: str) -> int:
    return len(text.split(".")[1]) if "." in text else 0


def _same_number(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def _rounds_to(ours_text: str, ours: float, src: NumberHit) -> bool:
    d = min(_decimals(ours_text), _decimals(src.text))
    return round(ours, d) == round(src.value, d) and not _same_number(ours, src.value)


def _overlaps(a: Box, b: Box, pad: float = 0.0) -> bool:
    return a.x0 - pad < b.x1 and b.x0 - pad < a.x1 and a.y0 - pad < b.y1 and b.y0 - pad < a.y1


def load_sources() -> dict:
    with open(SOURCES_CSV, newline="", encoding="utf-8") as fh:
        return {r["source_id"]: r for r in csv.DictReader(fh)}


def load_measurements() -> list[dict]:
    with open(MEASUREMENTS_CSV, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- location check
def _text_left_of(doc, page, box: Box, max_words: int = 6) -> str:
    same_line = [(b, t) for b, t in doc.words(page) if abs(b.yc - box.yc) < 0.6 * box.h and b.x1 <= box.x0]
    same_line.sort(key=lambda w: w[0].x0)
    return " ".join(t for _, t in same_line[:max_words])


def _text_above(doc, page, box: Box, max_words: int = 8) -> str:
    above = [
        (b, t)
        for b, t in doc.words(page)
        if b.y1 <= box.y0 and box.y0 - b.y1 < 110 and box.x0 - 15 <= b.xc <= box.x1 + 15
        and re.search(r"[A-Za-z°º]", t)  # header words, not the numbers stacked above in the column
    ]
    above.sort(key=lambda w: (-w[0].y0, w[0].x0))
    return " ".join(t for _, t in sorted(above[:max_words], key=lambda w: (w[0].y0, w[0].x0)))


def _split_match(doc, page, value_raw) -> Box | None:
    """A number broken over 2-3 consecutive fragments ("184." + "5", "247" "–" "248")."""
    target = normalise_value_raw(value_raw)
    words = doc.words(page)
    for i in range(len(words)):
        joined, box = "", None
        for j in range(i, min(i + 3, len(words))):
            b, t = words[j]
            if box is not None and (abs(b.yc - box.yc) > 2.6 * max(6.0, b.h) or abs(b.x0 - box.x1) > 60 and abs(b.yc - box.yc) < 0.5 * b.h):
                break
            joined += normalise_value_raw(t)
            box = b if box is None else box.union(b)
            if j > i and joined == target:
                return box
            if not target.startswith(joined):
                break
    return None


def _search_other_pages(doc, value_raw, value, skip_page) -> list[int]:
    return [p for p in range(1, doc.page_count + 1) if p != skip_page and doc.find_number(p, value_raw, value)]


def _unit_variants(doc, page, value) -> list[NumberHit]:
    out = []
    for factor in (1000.0, 0.001):
        target = value * factor
        out += [h for h in doc.numbers(page) if _same_number(h.value, target)]
    return out


def _numbers_right_of(doc, page, box: Box) -> int:
    pad = 0.4 * max(6.0, min(box.h, 14.0))
    return sum(1 for h in doc.numbers(page) if h.box.x0 > box.x1 and box.y0 - pad <= h.box.yc <= box.y1 + pad)


CAPTION_RE = re.compile(r"^(table|figure|fig\.?)$", re.I)


def _captions(doc, page) -> list:
    """Caption starts on a page: "Table 5. ..." begins its line, unlike "... in Table 5."."""
    words = doc.words(page)
    out = []
    for i, (b, t) in enumerate(words):
        if not CAPTION_RE.match(t.strip(".")):
            continue
        nxt = words[i + 1] if i + 1 < len(words) else None
        if not nxt or abs(nxt[0].yc - b.yc) > 0.5 * b.h:
            continue
        if not any(abs(o.yc - b.yc) < 0.5 * b.h and 0 <= b.x0 - o.x1 < 25 for o, _ in words):
            out.append((b, t.lower()[:3], nxt[1].strip(".:").lower()))
    return out


def table_regions(doc, page, anchor_id: str) -> list[Box]:
    """Candidate vertical extents of the cited table: below its caption (usual) or above it."""
    m = re.match(r"\s*(table|figure|fig\.?)\s*([A-Za-z]?\d+[A-Za-z]?)", anchor_id or "", re.I)
    if not m:
        return []
    kind, num = m.group(1).lower()[:3], m.group(2).lower()
    caps = _captions(doc, page)
    mine = [b for b, k, n in caps if k == kind and n == num]
    if not mine:
        return []
    cap = min(mine, key=lambda b: b.y0)
    pb = doc.page_rect(page)
    later = [b.y0 for b, _, _ in caps if b.y0 > cap.y1 + 4]
    earlier = [b.y1 for b, _, _ in caps if b.y1 < cap.y0 - 4]
    below = Box(pb.x0, cap.y0 - 2, pb.x1, min(later) - 1 if later else pb.y1)
    above = Box(pb.x0, max(earlier) + 1 if earlier else pb.y0, pb.x1, cap.y1 + 2)
    return [below, above]


def _in_region(box: Box, region: Box | None) -> bool:
    return region is None or region.y0 <= box.yc <= region.y1


def _row_numbers(doc, page, row_box: Box, label_boxes) -> list[NumberHit]:
    band_pad = 0.35 * max(6.0, row_box.h if row_box.h < 20 else 8.0)
    return [
        h for h in doc.numbers(page)
        if row_box.y0 - band_pad <= h.box.yc <= row_box.y1 + band_pad and h.box.x0 >= row_box.x0 - 4
        and not any(_overlaps(h.box, b, -0.5) for b in label_boxes)
    ]


def _holds(h: NumberHit, value_raw: str, value) -> bool:
    return h.text == normalise_value_raw(value_raw) or (value is not None and _same_number(h.value, value))


def normalise_value_raw(v: str) -> str:
    return (v or "").strip().translate(DASH_TABLE).replace(" ", "").lstrip("+")


def _label_continues(doc, page, hit) -> bool:
    """True when more words (not data, not an orientation like 90°) sit right under the label."""
    b = hit.box
    lh = max(6.0, min(b.h, 14.0))
    for w, t in doc.words(page):
        if b.y1 - 1 < w.y0 < b.y1 + 0.9 * lh and w.x0 < b.x1 and b.x0 < w.x1 and w not in hit.words:
            if re.search(r"[A-Za-z]", t) and not re.fullmatch(r"\d+\s*[°º˚]?", t):
                return True
    return False


def _pick_row(doc, page, label, regions, value_raw, value):
    """Returns (hit, confident, note). Prefers rows inside the cited table that carry data."""
    hits = doc.find_labels(page, label)
    if not hits:
        return None, False, ""
    region = next((r for r in regions if any(_in_region(h.box, r) for h in hits)), None)
    pool = [h for h in hits if _in_region(h.box, region)] or hits
    best = pool[0].score
    top = [h for h in pool if h.score >= best - 1e-6]
    rowlike = [h for h in top if _numbers_right_of(doc, page, h.box) >= 1] or top
    # A table label sits on one line; prose that happens to contain the label wraps (higher cost).
    rowlike = [h for h in rowlike if h.cost <= rowlike[0].cost + 4]
    if len(rowlike) > 1 and value_raw:
        # The label repeats (a chart axis under the table, a longer label): if exactly one copy holds
        # our value, that is the row. Noted, because the label alone doesn't decide it.
        holding = [h for h in rowlike if any(_holds(n, value_raw, value) for n in _row_numbers(doc, page, h.box, h.words))]
        if len(holding) == 1:
            return holding[0], False, f"Row label occurs {len(rowlike)}× on the page; used the one that holds this value."
    if len(rowlike) > 1:
        # Drop labels whose text continues on the next line ("80/20 BP1/PLA" + "w/ Additive").
        rowlike = [h for h in rowlike if not _label_continues(doc, page, h)] or rowlike
    confident = best >= 1.0 and len(rowlike) == 1
    note = "" if confident else ("Row label matched only partly." if best < 1.0 else f"Row label occurs {len(rowlike)}× on the page.")
    return rowlike[0], confident, note


def _pick_col(doc, page, label, row_hit, region):
    """Returns (hit, confident, note). Prefers a header inside the cited table, just above the row."""
    hits = doc.find_labels(page, label)
    if not hits:
        return None, False, ""
    pool = [h for h in hits if _in_region(h.bottom, region)] or hits
    fallback = False
    if pool[0].score < 1.0:
        # Spanning headers ("Pore Size" over "Length (mm) | Width (mm)") rarely line up with one
        # column. Fall back to the longest tail of the label that matches exactly.
        words = label.split()
        for k in range(1, len(words)):
            tail = [h for h in doc.find_labels(page, " ".join(words[k:])) if h.score >= 1.0 and _in_region(h.bottom, region)]
            if row_hit:
                tail = [h for h in tail if h.bottom.y1 <= row_hit.box.y0 + 2 and row_hit.box.y0 - h.bottom.y1 < 400]
            if tail:
                pool, fallback = tail, True
                break
    top = [h for h in pool if h.score >= pool[0].score - 1e-6]
    pick, rivals = top[0], top
    if row_hit:
        above = [h for h in top if h.bottom.y1 <= row_hit.box.y0 + 2 and row_hit.box.y0 - h.bottom.y1 < 400]
        if not above:
            return pick, False, "No matching column header above the row."
        if above:
            key = lambda h: (round(h.cost / 15), row_hit.box.y0 - h.bottom.y1)
            pick = min(above, key=key)
            # Rivals: equally compact headers at the same height (e.g. "µ" under two different groups).
            rivals = [h for h in above if round(h.cost / 15) == round(pick.cost / 15) and abs(h.bottom.yc - pick.bottom.yc) < 3]
    confident = pick.score >= 1.0 and not fallback and len(rivals) == 1
    note = "" if confident else ("Column header matched only by its last line." if fallback else "Column header matched only partly." if pick.score < 1.0 else "Column header is not unique.")
    return pick, confident, note


def check_location(m: dict, src: dict) -> Comment:
    base = dict(
        obs_id=m["obs_id"], source_id=m["source_id"], anchor_id=m["anchor_id"], row_label=m["row_label"],
        col_label=m["col_label"], our_value=m["value_raw"],
    )
    page = int(m["page"])
    base["page"] = page
    doc = open_pdf(src["file"])
    value = parse_number(m["value"])
    value_raw = m["value_raw"] or m["value"]
    hits = doc.find_number(page, value_raw, value)

    if m["extraction"] == "chart_digitized" or m["anchor_type"] == "figure":
        note = f" Reader's note: {m['notes']}" if m.get("notes") else ""
        return Comment(
            "CHART_ESTIMATE",
            f"Digitized from {m['anchor_id'] or 'a chart'} (confidence {m['confidence'] or '?'}). Compare the number with the chart.{note}",
            full_page=True, **base,
        )

    if value is None:  # a range or bound ("17–24", "<17"), often printed as a label: just find it
        if hits:
            return Comment("PAGE_MATCH", f"The range/bound {value_raw} appears on the cited page.", boxes=[("ours", hits[0].box.as_tuple())], **base)
        return _not_on_page(doc, m, page, value_raw, value, base)

    if m["anchor_type"] == "text":
        if hits:
            return Comment("TEXT_MATCH", "Found in the text of the cited page.", boxes=[("ours", hits[0].box.as_tuple())], **base)
        return _not_on_page(doc, m, page, value_raw, value, base)

    # Table: find the row (refined by orientation for 0°/90° sub-rows) and the column header.
    regions = table_regions(doc, page, m["anchor_id"])
    row_hit, row_ok, row_note = _pick_row(doc, page, m["row_label"], regions, value_raw, value) if m["row_label"] else (None, False, "")
    region = next((r for r in regions if row_hit and _in_region(row_hit.box, r)), regions[0] if regions else None)
    col_hit, col_ok, col_note = _pick_col(doc, page, m["col_label"], row_hit, region) if m["col_label"] else (None, False, "")
    confident = row_ok and col_ok
    caveat = " ".join(n for n in (row_note, col_note) if n)
    boxes, label_boxes, row_box = [], [], None
    if row_hit:
        row_box = row_hit.box
        label_boxes += list(row_hit.words)
        if m["orientation"]:
            area = Box(row_box.x0 - 60, row_box.y0 - 2, row_box.x1 + 240, row_box.y1 + 5 * max(8.0, row_box.h))
            tok = doc.find_token_near(page, m["orientation"], area)
            if tok:
                row_box = Box(row_box.x0, min(row_box.y0, tok.y0) if tok.yc < row_box.y1 else tok.y0, max(row_box.x1, tok.x1), tok.y1)
                label_boxes.append(tok)
        boxes.append(("row", row_box.as_tuple()))
    if col_hit:
        label_boxes += list(col_hit.words)
        boxes.append(("col", col_hit.box.as_tuple()))

    def is_label(h: NumberHit) -> bool:
        return any(_overlaps(h.box, b, -0.5) for b in label_boxes)

    in_row = _row_numbers(doc, page, row_box, label_boxes) if row_box else []
    cell = None
    if row_box and col_hit:
        band = col_hit.bottom  # the header line right above the data says which column it is
        pad = max(10.0, 0.4 * (band.x1 - band.x0))
        in_col = [h for h in in_row if band.x0 - pad < h.box.xc < band.x1 + pad]
        if in_col:
            # A cell may print "64.3 ± 3.3": if our number is in the cell, that's the match.
            exact = [h for h in in_col if _holds(h, value_raw, value)]
            cell = min(exact or in_col, key=lambda h: abs(h.box.xc - band.xc))
    tail = f" {caveat}" if caveat else ""

    if cell and _holds(cell, value_raw, value):
        boxes.append(("ours", cell.box.as_tuple()))
        return Comment("CELL_MATCH", f"Row, column and value agree with the source.{tail}", source_value=cell.text, boxes=boxes, **base)
    row_matches = [h for h in in_row if _holds(h, value_raw, value)]

    if cell and confident:
        boxes.append(("cell", cell.box.as_tuple()))
        if value is not None and _rounds_to(value_raw, value, cell):
            return Comment("ROUNDING", f"The source prints {cell.text}; ours is {value_raw}.", source_value=cell.text, boxes=boxes, **base)
        if value is not None and any(_same_number(cell.value, value * f) for f in (1000.0, 0.001)):
            return Comment("UNIT_MISMATCH", f"The source cell holds {cell.text}, ours is {value_raw} ({m['unit_raw']}). A factor of 1000 apart: check the unit.", source_value=cell.text, boxes=boxes, **base)
        if row_matches:
            h = row_matches[0]
            boxes.append(("ours", h.box.as_tuple()))
            header = _text_above(doc, page, h.box)
            return Comment("WRONG_COLUMN", f"The cited cell holds {cell.text}. Our value {value_raw} is on the same row under \"{header}\".", source_value=cell.text, boxes=boxes, **base)
        for h in hits:
            if is_label(h):
                continue
            if abs(h.box.xc - cell.box.xc) < max(12.0, 0.6 * (cell.box.x1 - cell.box.x0) + 8):
                boxes.append(("ours", h.box.as_tuple()))
                left = _text_left_of(doc, page, h.box)
                swap = " The orientation labels may be swapped." if m["orientation"] and re.search(r"\d+\s*[°º˚]", left) else ""
                return Comment("WRONG_ROW", f"The cited cell holds {cell.text}. Our value {value_raw} is in the same column on the row \"{left}\".{swap}", source_value=cell.text, boxes=boxes, **base)
        return Comment("CELL_MISMATCH", f"The cited cell holds {cell.text}; ours is {value_raw}.", source_value=cell.text, boxes=boxes, **base)

    # Geometry not certain enough to call an error: report the strongest evidence we have.
    if row_matches:
        boxes.append(("ours", row_matches[0].box.as_tuple()))
        why = "" if not m["col_label"] else (" The column could not be confirmed." if not caveat else "")
        return Comment("ROW_MATCH", f"Value found on the cited row.{why}{tail}", boxes=boxes, **base)
    page_matches = [h for h in hits if not is_label(h)]
    if page_matches:
        boxes += [("ours", h.box.as_tuple()) for h in page_matches[:4]]
        missing = [n for n, ok in (("row", row_hit), ("column", col_hit)) if not ok and m["row_label" if n == "row" else "col_label"]]
        why = f" ({' and '.join(missing)} label not located on the page)" if missing else ""
        return Comment("PAGE_MATCH", f"Value {value_raw} appears on the page {len(page_matches)}× but not at the located row/column{why}.{tail}", boxes=boxes, **base)
    return _not_on_page(doc, m, page, value_raw, value, base, boxes)


def _not_on_page(doc, m, page, value_raw, value, base, boxes=None) -> Comment:
    boxes = list(boxes or [])
    if value is not None:
        variants = _unit_variants(doc, page, value)
        if variants:
            boxes.append(("cell", variants[0].box.as_tuple()))
            return Comment("UNIT_MISMATCH", f"{value_raw} is not on the page, but {variants[0].text} is (×1000 apart). Check the unit ({m['unit_raw']}).", source_value=variants[0].text, boxes=boxes, **base)
    split = _split_match(doc, page, value_raw)
    if split:
        return Comment("SPLIT_MATCH", f"{value_raw} is printed split over neighbouring text fragments on the cited page.", boxes=boxes + [("ours", split.as_tuple())], **base)
    other = _search_other_pages(doc, value_raw, value, page)
    if other:
        return Comment("WRONG_PAGE", f"{value_raw} is not on page {page} but appears on page(s) {', '.join(map(str, other[:8]))}.", boxes=boxes, full_page=not boxes, **base)
    return Comment("NOT_FOUND", f"{value_raw} was not found anywhere in the PDF text. It may be a chart reading or a typo.", boxes=boxes, full_page=not boxes, **base)


# ---------------------------------------------------------------- dataset checks
def check_schema(m: dict, sources: dict) -> list[Comment]:
    out = []
    base = dict(obs_id=m["obs_id"], source_id=m["source_id"], anchor_id=m["anchor_id"], our_value=m["value_raw"])

    def add(verdict, msg, fld):
        out.append(Comment(verdict, msg, field_name=fld, page=parse_number(m["page"]) and int(float(m["page"])), **base))

    if m["source_id"] not in sources:
        add("SCHEMA", f"Unknown source_id {m['source_id']}.", "source_id")
        return out
    page = parse_number(m["page"])
    if page is None or page != int(page):
        add("SCHEMA", f"page '{m['page']}' is not an integer.", "page")
    if parse_number(m["value"]) is None:
        if m["value"] == "" and m["value_raw"]:
            add("RANGE_ONLY", f"'{m['value_raw']}' is a range or bound; kept for context.", "value")
        else:
            add("SCHEMA", f"value '{m['value']}' is not a number.", "value")
    if not m["value_raw"]:
        add("SCHEMA", "value_raw is empty, so the value can't be traced.", "value_raw")
    for fld, allowed in (("anchor_type", ANCHOR_TYPES), ("origin", ORIGINS), ("extraction", EXTRACTIONS),
                         ("confidence", CONFIDENCES), ("soil_type", SOIL_TYPES), ("process", PROCESSES)):
        if m[fld] not in allowed:
            add("VOCAB", f"{fld} '{m[fld]}' is not one of {sorted(a for a in allowed if a)}.", fld)
    if not is_known_property(m["property"]):
        add("VOCAB", f"property '{m['property']}' is outside the vocabulary (kept, but not used by the model).", "property")
    elif m["model_property"] and not m["value_si"] and parse_number(m["value"]) is not None:
        add("UNIT_UNCONVERTIBLE", f"unit '{m['unit_raw']}' can't be converted to {PROPERTY_UNITS[m['model_property']][0]}.", "unit_raw")
    for fld in ("regolith_wt_target", "regolith_wt_actual", "regolith_vol", "fiber_wt"):
        v = parse_number(m[fld])
        if m[fld] and (v is None or not 0 <= v <= 100):
            add("SCHEMA", f"{fld} '{m[fld]}' must be a number from 0 to 100.", fld)
    return out


def check_sanity(m: dict) -> list[Comment]:
    out = []
    base = dict(obs_id=m["obs_id"], source_id=m["source_id"], anchor_id=m["anchor_id"], our_value=m["value_raw"],
                page=int(float(m["page"])) if parse_number(m["page"]) is not None else None)
    v, s = parse_number(m["value_si"]), parse_number(m["std_si"])
    if m["model_property"] and v is not None:
        unit, lo, hi = PROPERTY_UNITS[m["model_property"]]
        if not lo <= v <= hi:
            out.append(Comment("UNIT_SUSPECT", f"{m['property']} = {v:g} {unit} is outside the plausible {lo:g}–{hi:g} {unit}. Check the unit ({m['unit_raw']}).", field_name="unit_raw", **base))
    if v and s is not None and s >= abs(v) and m["property"] not in ("glass_transition",):
        out.append(Comment("STD_SUSPECT", f"std {m['std']} is not smaller than the value {m['value']}.", field_name="std", **base))
    target, actual = parse_number(m["regolith_wt_target"]), parse_number(m["regolith_wt_actual"])
    if target is not None and actual is not None and abs(target - actual) >= 5:
        out.append(Comment("COMPOSITION", f"Measured filler content {actual:g} wt% vs target {target:g} wt% ({actual - target:+g} points). The model uses the measured value.", field_name="regolith_wt_actual", **base))
    return out


def check_duplicates(rows: list[dict]) -> list[Comment]:
    out, seen = [], defaultdict(list)
    for m in rows:
        key = (m["source_id"], m["page"], m["anchor_id"], m["row_label"], m["col_label"], m["orientation"], m["property"],
               m["temperature_c"], m["environment"], m["regolith_wt_target"], m["filler"], m["binder"], m["value_raw"])
        seen[key].append(m)
    for group in seen.values():
        if len(group) > 1 and group[0]["anchor_type"] == "table":
            ids = ", ".join(g["obs_id"] for g in group)
            for g in group[1:]:
                out.append(Comment("DUPLICATE", f"Same cell and conditions as {group[0]['obs_id']} ({ids}).", obs_id=g["obs_id"], source_id=g["source_id"], page=int(g["page"]), anchor_id=g["anchor_id"], our_value=g["value_raw"]))
    return out


def check_spread(rows: list[dict]) -> list[Comment]:
    """Comparable experimental measurements from different sources that disagree by >25%."""
    groups = defaultdict(list)
    for m in rows:
        v, wt = parse_number(m["value_si"]), parse_number(m["regolith_wt"])
        if v is None or wt is None or m["origin"] != "experimental" or m["cited"] == "yes" or m["duplicate_of"]:
            continue
        temp = parse_number(m["temperature_c"])
        key = (m["binder"].upper(), m["soil_type"], round(wt / 5) * 5, m["process"], m["model_property"], round((temp if temp is not None else 23) / 10))
        groups[key].append((v, m))
    out = []
    for key, items in groups.items():
        if len({m["source_id"] for _, m in items}) < 2:
            continue
        values = [v for v, _ in items]
        lo, hi = min(values), max(values)
        if lo > 0 and hi / lo > 1.25:
            listing = "; ".join(f"{m['source_id']} {v:g}" for v, m in sorted(items, key=lambda t: t[0]))
            binder, soil, wt, process, prop, _ = key
            out.append(Comment("CROSS_SOURCE_SPREAD", f"{binder} + {soil} ≈{wt} wt% ({process or 'process ?'}), {prop}: {listing} {PROPERTY_UNITS.get(prop, ('',))[0]} (×{hi / lo:.2f} apart). The model treats this as real uncertainty.", field_name=prop))
    return out


ISSUE_LINE = re.compile(r"^\s*-\s*p\.?\s*(\d+)\s*(.*)$")


def source_issues() -> list[Comment]:
    out = []
    for path in sorted(EXTRACTION_DIR.glob("S*_issues.md")):
        sid = path.stem.split("_")[0]
        for line in path.read_text(encoding="utf-8").splitlines():
            m = ISSUE_LINE.match(line)
            if m:
                out.append(Comment("SOURCE_ISSUE", m.group(2).strip(" |"), source_id=sid, page=int(m.group(1)), field_name="source"))
    return out


REFERENCE_SOURCES = {"NTRS 20230015024": ["S003"], "NTRS 20260007758": ["S011", "S006"]}
REFERENCE_PROPERTY = {"elastic_modulus": "tensile_modulus"}


def _norm_orientation(o: str) -> str:
    return re.sub(r"[°º˚\s]|deg", "", (o or "").lower())


def check_model_reference(rows: list[dict]) -> list[Comment]:
    path = BASE_DIR / "data" / "nasa_reference_points.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        refs = list(csv.DictReader(fh))
    out = []
    for i, r in enumerate(refs, start=2):
        sources = REFERENCE_SOURCES.get(r["source"], [])
        prop = REFERENCE_PROPERTY.get(r["property"], r["property"])
        ref_v = float(r["value"])
        wt = float(r["regolith_wt_target"] or 0)
        temp = float(r["temperature_c"] or 23)
        cands = []
        for m in rows:
            if m["source_id"] not in sources or m["property"] != prop or m["binder"].upper() != r["binder"].upper():
                continue
            mwt = parse_number(m["regolith_wt_target"]) or 0.0
            if abs(mwt - wt) > 0.6:
                continue
            filler = (m["filler"] or "none").upper().replace(" ", "")
            want = (r["simulant"] or "none").upper().replace(" ", "")
            if want != "NONE" and want not in filler:
                continue
            mt = parse_number(m["temperature_c"])
            if abs((mt if mt is not None else 23) - temp) > 2:
                continue
            if _norm_orientation(r["orientation"]) and _norm_orientation(m["orientation"]) and _norm_orientation(r["orientation"]) != _norm_orientation(m["orientation"]):
                continue
            v = parse_number(m["value_si"]) if r["unit"] == PROPERTY_UNITS.get(prop, ("",))[0] else parse_number(m["value"])
            if v is not None:
                cands.append((v, m))
        label = f"nasa_reference_points.csv line {i}: {r['binder']} + {r['simulant'] or 'none'} {r['regolith_wt_target']} wt% {r['orientation']} {r['property']} = {ref_v:g} {r['unit']}"
        if not cands:
            out.append(Comment("MODEL_REFERENCE_UNVERIFIED", f"{label}. No matching evidence row.", source_id=sources[0] if sources else "", field_name="nasa_reference_points", our_value=r["value"]))
            continue
        best_v, best_m = min(cands, key=lambda c: abs(c[0] - ref_v))
        chart = best_m["extraction"] == "chart_digitized" or "chart" in r["note"].lower()
        tol = max(0.05 * abs(best_v), 0.6) if chart else max(0.005 * abs(best_v), 0.011)
        verdict = "MODEL_REFERENCE_MATCH" if abs(best_v - ref_v) <= tol else "MODEL_REFERENCE_MISMATCH"
        how = "chart readings, ±5% allowed" if chart else "printed values"
        out.append(Comment(verdict, f"{label}. Evidence {best_m['obs_id']} = {best_v:g} ({how}).", obs_id=best_m["obs_id"], source_id=best_m["source_id"], page=int(best_m["page"]), field_name="nasa_reference_points", our_value=r["value"], source_value=f"{best_v:g}"))
    return out


LEGACY_SOURCE_MAP = {
    "S001_": "S001", "S002_": "S002", "S003_": "S003", "S004_790763": "S004", "S004_preprints": "S005",
    "S005_preprints": "S005", "S006_": "S006", "S007_": "S007", "S008_": "S008",
}
LEGACY_PROPERTIES = {
    "compressive_strength", "density", "porosity", "flexural_strength", "tensile_modulus", "tensile_strength",
    "elongation_at_break", "flexural_modulus", "melting_temperature", "glass_transition", "compressive_modulus",
}


def check_coverage(rows: list[dict]) -> list[Comment]:
    """Numbers the earlier automatic extraction flagged as HIGH-confidence properties but the dataset lacks."""
    path = RESEARCH_DIR / "legacy" / "candidate_values_all.csv"
    if not path.exists():
        return []
    have = defaultdict(set)
    for m in rows:
        v = parse_number(m["value"])
        if v is not None:
            have[m["source_id"]].add(round(v, 4))
    out = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for c in csv.DictReader(fh):
            sid = next((v for k, v in LEGACY_SOURCE_MAP.items() if c["source_file"].startswith(k)), None)
            v = parse_number(c["value_raw"])
            if not sid or v is None or c["confidence"] != "HIGH" or c["property_guess"] not in LEGACY_PROPERTIES:
                continue
            if sid not in have or round(v, 4) in have[sid]:
                continue
            out.append(Comment("POSSIBLE_MISSED_VALUE", f"Earlier automatic extraction: {c['property_guess']} {c['value_raw']} {c['unit_raw']} in \"{c['context_sentence'][:220]}\"", source_id=sid, page=int(c["page"]), field_name=c["property_guess"], source_value=c["value_raw"]))
    return out


# ---------------------------------------------------------------- run
def run() -> list[Comment]:
    sources = load_sources()
    rows = load_measurements()
    comments = []
    for m in rows:
        schema = check_schema(m, sources)
        comments += schema
        fatal = any(c.verdict == "SCHEMA" and c.field_name in ("source_id", "page") for c in schema)
        if not fatal:
            src = sources[m["source_id"]]
            if int(float(m["page"])) > open_pdf(src["file"]).page_count:
                comments.append(Comment("SCHEMA", f"page {m['page']} is beyond the PDF's {open_pdf(src['file']).page_count} pages.", obs_id=m["obs_id"], source_id=m["source_id"], field_name="page"))
            elif src.get("text_layer") == "scan":
                comments.append(Comment("SCAN_VISUAL", f"{m['anchor_id']}: scanned report, so the number can't be re-found in text. Compare with the page image.", obs_id=m["obs_id"], source_id=m["source_id"], page=int(float(m["page"])), anchor_id=m["anchor_id"], row_label=m["row_label"], col_label=m["col_label"], our_value=m["value_raw"], full_page=True))
            else:
                comments.append(check_location(m, src))
        comments += check_sanity(m)
    comments += check_duplicates(rows)
    comments += check_spread(rows)
    comments += source_issues()
    comments += check_model_reference(rows)
    comments += check_coverage(rows)
    return comments


def write_outputs(comments: list[Comment], rows: list[dict]) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["severity", "verdict", "obs_id", "source_id", "page", "anchor_id", "row_label", "col_label", "field", "our_value", "source_value", "comment"]
    order = {"error": 0, "warning": 1, "info": 2, "ok": 3}
    with open(AUDIT_DIR / "audit_comments.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for c in sorted(comments, key=lambda c: (order[c.severity], c.source_id, c.obs_id)):
            w.writerow([c.severity, c.verdict, c.obs_id, c.source_id, c.page or "", c.anchor_id, c.row_label, c.col_label, c.field_name, c.our_value, c.source_value, c.message])
    index = {}
    for c in comments:
        if not c.obs_id:
            continue
        entry = index.setdefault(c.obs_id, {"verdicts": [], "severity": "ok", "page": c.page, "boxes": []})
        entry["verdicts"].append({"verdict": c.verdict, "severity": c.severity, "message": c.message})
        if order[c.severity] < order[entry["severity"]]:
            entry["severity"] = c.severity
        if c.boxes and not entry["boxes"]:
            entry["boxes"] = c.boxes
    (AUDIT_DIR / "audit_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))


def main() -> None:
    from .report import write_report

    rows = load_measurements()
    comments = run()
    write_outputs(comments, rows)
    write_report(comments, rows, load_sources())
    counts = Counter(c.verdict for c in comments)
    sev = Counter(c.severity for c in comments)
    print(f"Audited {len(rows)} measurements: " + ", ".join(f"{k} {sev.get(k, 0)}" for k in ("error", "warning", "info", "ok")))
    for verdict, n in counts.most_common():
        print(f"  {verdict:28s} {n}")
    print(f"Wrote {AUDIT_DIR / 'audit_comments.csv'}, audit_index.json, audit_report.html")


if __name__ == "__main__":
    main()


