"""Find numbers and labels on PDF pages, with their positions.

PyMuPDF gives every word on a page with its bounding box. We split words into number tokens
(a word like "15.2±0.3" holds two numbers) and match multi-word labels that may wrap over several
lines, as table headers often do. Coordinates are PDF points (1/72 inch), origin top-left.
"""
import re
from dataclasses import dataclass
from functools import lru_cache

import pymupdf

from .schema import PDF_DIR

SUBTOKEN_RE = re.compile(r"[^\W_]+(?:\.[0-9]+)?|[°%]")  # any letters incl. Greek (σ, χ), digits, ° and %
NUMBER_RE = re.compile(r"[-−–]?\d+(?:\.\d+)?(?:[eE][-−]?\d+)?")
DEGREE_CHARS = str.maketrans({"º": "°", "˚": "°", "ᵒ": "°"})
DASH_TABLE = str.maketrans({c: "-" for c in "‐‑‒–—−"})  # every dash/minus variant -> "-"


@dataclass(frozen=True)
class Box:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def yc(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def h(self) -> float:
        return self.y1 - self.y0

    def union(self, other: "Box") -> "Box":
        return Box(min(self.x0, other.x0), min(self.y0, other.y0), max(self.x1, other.x1), max(self.y1, other.y1))

    def as_tuple(self) -> tuple:
        return (round(self.x0, 1), round(self.y0, 1), round(self.x1, 1), round(self.y1, 1))


@dataclass(frozen=True)
class NumberHit:
    text: str
    value: float
    box: Box


@dataclass(frozen=True)
class LabelHit:
    box: Box
    score: float
    words: tuple
    bottom: Box  # the label's lowest line: for a wrapped column header, the part right above the data
    cost: float = 0.0  # total gap along the chain of matched tokens (lower = more compact)


def normalise_number_text(s: str) -> str:
    return s.strip().translate(DASH_TABLE).lstrip("+")


def _norm_word(w: str) -> str:
    w = w.translate(DEGREE_CHARS).lower()
    w = w.replace("−", "-").replace("–", "-")
    return w.strip(" \t()[]{},;:*†‡\"'")


def _label_tokens(label: str) -> list[str]:
    return [t for t in (_norm_word(w) for w in label.split()) if t]


class PdfDoc:
    def __init__(self, path):
        self.path = path
        self.doc = pymupdf.open(path)
        self._words = {}

    @property
    def page_count(self) -> int:
        return self.doc.page_count

    def words(self, page_no: int) -> list:
        """Words on a 1-based page: (Box, text)."""
        if page_no not in self._words:
            page = self.doc[page_no - 1]
            self._words[page_no] = [(Box(w[0], w[1], w[2], w[3]), w[4]) for w in page.get_text("words")]
        return self._words[page_no]

    def numbers(self, page_no: int) -> list[NumberHit]:
        hits = []
        for box, text in self.words(page_no):
            n = len(text) or 1
            for m in NUMBER_RE.finditer(text):
                raw = normalise_number_text(m.group())
                try:
                    value = float(raw)
                except ValueError:
                    continue
                # Approximate the sub-word box by character position.
                x0 = box.x0 + (box.x1 - box.x0) * m.start() / n
                x1 = box.x0 + (box.x1 - box.x0) * m.end() / n
                hits.append(NumberHit(raw, value, Box(x0, box.y0, x1, box.y1)))
        return hits

    def find_number(self, page_no: int, value_raw: str, value: float | None) -> list[NumberHit]:
        """Exact textual matches first; numeric matches (e.g. "7" vs "7.0") second."""
        target = normalise_number_text(value_raw).replace(" ", "")
        if not NUMBER_RE.fullmatch(target):
            # Ratios ("70:30"), inequalities ("<0.002") and ranges ("17–24") match whole words.
            words = [(b, normalise_number_text(t).strip("(),;")) for b, t in self.words(page_no)]
            return [
                NumberHit(t, value if value is not None else float("nan"), b)
                for b, t in words if target in (t, t.lstrip("≈~"))  # "≈247–248" holds "247–248"
            ]
        hits = self.numbers(page_no)
        exact = [h for h in hits if h.text == target]
        if exact:
            return exact
        if value is None:
            return []
        return [h for h in hits if abs(h.value - value) <= 1e-9 * max(1.0, abs(value))]

    def subtokens(self, page_no: int) -> list:
        """Words split at punctuation ("BP-1/PLA" -> bp, 1, pla), with approximate sub-boxes."""
        key = ("sub", page_no)
        if key not in self._words:
            out = []
            for box, text in self.words(page_no):
                t = _norm_word(text)
                n = len(t) or 1
                for m in SUBTOKEN_RE.finditer(t):
                    x0 = box.x0 + (box.x1 - box.x0) * m.start() / n
                    x1 = box.x0 + (box.x1 - box.x0) * m.end() / n
                    out.append((Box(x0, box.y0, x1, box.y1), m.group()))
            self._words[key] = out
        return self._words[key]

    def find_label(self, page_no: int, label: str, near: Box | None = None) -> LabelHit | None:
        hits = self.find_labels(page_no, label, near)
        return hits[0] if hits else None

    def find_labels(self, page_no: int, label: str, near: Box | None = None) -> list[LabelHit]:
        """All matches of a label that may wrap over lines or be split across words ("LHS-" / "1/PLA").

        Tokens are chained in reading order: each next token is either just to the right on the same
        line, or on one of the next two lines aligned with the label's start or centre (stacked table
        headers). Ranking: share of tokens matched, then the chain's total gap, then closeness to `near`.
        """
        tokens = [t for w in label.split() for t in SUBTOKEN_RE.findall(_norm_word(w))]
        if not tokens:
            return []
        words = self.subtokens(page_no)
        if not words:
            return []
        line_h = max(6.0, sorted(b.h for b, _ in words)[len(words) // 2])
        found = {}
        for k0, first in enumerate(tokens[:3]):  # tolerate a missing first token or two
            for i, (start, w) in enumerate(words):
                if w != first:
                    continue
                used, boxes, cost, prev = {i}, [start], 0.0, start
                for tok in tokens[k0 + 1:]:
                    best_c = None
                    for j, (b, t) in enumerate(words):
                        if j in used or t != tok:
                            continue
                        dy = b.yc - prev.yc
                        if abs(dy) < 0.5 * line_h and -2.5 <= b.x0 - prev.x1 <= 45:
                            c = max(0.0, b.x0 - prev.x1)
                        elif 0.5 * line_h <= dy <= 2.6 * line_h:
                            # A wrapped line sits under the previous one (stacked header) or starts where
                            # the label started (wrapped row label). Words of a neighbouring column don't.
                            overlaps = any(b.x0 < o.x1 + 6 and o.x0 - 6 < b.x1 for o in (prev, start))
                            if not overlaps and abs(b.x0 - start.x0) > 8:
                                continue
                            c = dy + 0.5 * min(abs(b.xc - prev.xc), abs(b.x0 - start.x0))
                        else:
                            continue
                        if best_c is None or c < best_c[0]:
                            best_c = (c, j, b)
                    if best_c is None:
                        cost += 3 * line_h  # missing token: small penalty, keep chaining from prev
                        continue
                    cost += best_c[0]
                    used.add(best_c[1])
                    boxes.append(best_c[2])
                    prev = best_c[2]
                score = len(boxes) / len(tokens)
                box = boxes[0]
                for b in boxes[1:]:
                    box = box.union(b)
                low = max(b.yc for b in boxes)
                bottom_boxes = [b for b in boxes if low - b.yc < 0.5 * line_h]
                bottom = bottom_boxes[0]
                for b in bottom_boxes[1:]:
                    bottom = bottom.union(b)
                near_cost = (abs(box.yc - near.yc) + abs(box.xc - near.xc)) if near is not None else 0.0
                key = (-round(score, 6), round(cost, 1), near_cost)
                hit = LabelHit(box, score, tuple(boxes), bottom, cost)
                if box.as_tuple() not in found or key < found[box.as_tuple()][0]:
                    found[box.as_tuple()] = (key, hit)
        need = 1.0 if len(tokens) == 1 else 0.75
        return [h for _, h in sorted(found.values(), key=lambda kh: kh[0]) if h.score >= need]

    def find_token_near(self, page_no: int, token: str, region: Box) -> Box | None:
        """A single token (e.g. an orientation like 90°) inside a region."""
        want = _norm_word(token).replace(" ", "")
        want_alt = {want, want.replace("°", ""), want.replace("°", "o")}
        found = [
            b
            for b, t in self.words(page_no)
            if _norm_word(t).replace(" ", "") in want_alt and region.x0 <= b.xc <= region.x1 and region.y0 <= b.yc <= region.y1
        ]
        return min(found, key=lambda b: (b.y0, b.x0)) if found else None

    def render(self, page_no: int, clip: Box, zoom: float = 2.0):
        page = self.doc[page_no - 1]
        rect = pymupdf.Rect(clip.x0, clip.y0, clip.x1, clip.y1) & page.rect
        return page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=rect), rect

    def page_rect(self, page_no: int) -> Box:
        r = self.doc[page_no - 1].rect
        return Box(r.x0, r.y0, r.x1, r.y1)


def _area(b: Box) -> float:
    return (b.x1 - b.x0) * (b.y1 - b.y0)


@lru_cache(maxsize=32)
def open_pdf(filename: str) -> PdfDoc:
    return PdfDoc(PDF_DIR / filename)
