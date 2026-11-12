"""Self-contained HTML report for the Evidence Auditor (no network, images embedded).

Each finding with a PDF location gets a crop of the source page with coloured boxes:
  blue = row label, purple = column header / figure, green = our value where found,
  red = what the cited cell actually holds when it differs.
"""
import base64
import html
import io
from collections import Counter, defaultdict
from datetime import date

from PIL import Image, ImageDraw

from .pdfindex import Box, open_pdf
from .schema import AUDIT_DIR

BOX_RGB = {"row": (26, 115, 242), "col": (140, 64, 217), "ours": (26, 166, 64), "cell": (230, 38, 38)}
SEV_ORDER = {"error": 0, "warning": 1, "info": 2, "ok": 3}
MAX_WIDTH_PX = 900


def _crop(source_file: str, page: int, boxes: list, full_page: bool, pad: float = 22.0) -> str | None:
    doc = open_pdf(source_file)
    page_box = doc.page_rect(page)
    if full_page or not boxes:
        clip = page_box
    else:
        b = Box(*boxes[0][1])
        for _, t in boxes[1:]:
            b = b.union(Box(*t))
        clip = Box(max(page_box.x0, b.x0 - pad * 3), max(page_box.y0, b.y0 - pad), min(page_box.x1, b.x1 + pad * 3), min(page_box.y1, b.y1 + pad))
    width_pt = clip.x1 - clip.x0
    zoom = min(1.8, MAX_WIDTH_PX / max(1.0, width_pt))
    pix, rect = doc.render(page, clip, zoom)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    draw = ImageDraw.Draw(img)
    for kind, (x0, y0, x1, y1) in boxes:
        sx0, sy0 = (x0 - rect.x0) * zoom, (y0 - rect.y0) * zoom
        sx1, sy1 = (x1 - rect.x0) * zoom, (y1 - rect.y0) * zoom
        draw.rectangle([sx0 - 2, sy0 - 2, sx1 + 2, sy1 + 2], outline=BOX_RGB[kind], width=3)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=58, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def write_report(comments, rows, sources) -> None:
    rows_by_id = {r["obs_id"]: r for r in rows}
    images, image_keys = {}, {}

    def image_for(c):
        # Verified rows don't need a picture; anything a human should look at gets one.
        if c.severity == "ok":
            return None
        src = sources.get(c.source_id)
        if not src or not c.page or not (c.boxes or c.full_page):
            return None
        key = (c.source_id, c.page) if c.full_page and not c.boxes else (c.source_id, c.page, tuple(c.boxes), c.full_page)
        if key not in image_keys:
            try:
                data = _crop(src["file"], c.page, c.boxes, c.full_page)
            except Exception as exc:  # a broken page shouldn't stop the report
                print(f"  ! could not render {c.source_id} p.{c.page}: {exc}")
                return None
            image_keys[key] = f"i{len(image_keys)}"
            images[image_keys[key]] = data
        return image_keys[key]

    by_source = defaultdict(list)
    for c in comments:
        by_source[c.source_id or "dataset"].append(c)

    sev_counts = Counter(c.severity for c in comments)
    verdict_counts = Counter(c.verdict for c in comments)
    measured = len(rows)
    located = sum(1 for c in comments if c.verdict in ("CELL_MATCH", "TEXT_MATCH", "ROW_MATCH"))

    parts = []
    for sid in sorted(by_source, key=lambda s: (s == "dataset", s)):
        items = sorted(by_source[sid], key=lambda c: (SEV_ORDER[c.severity], c.obs_id, c.verdict))
        src = sources.get(sid, {})
        title = html.escape(src.get("title", "Dataset-level findings"))
        n_rows = sum(1 for r in rows if r["source_id"] == sid)
        sc = Counter(c.severity for c in items)
        badge = " ".join(f'<span class="pill {s}">{s} {sc[s]}</span>' for s in ("error", "warning", "info", "ok") if sc[s])
        link = f' · <a href="{html.escape(src["url"])}">{html.escape(src.get("venue", ""))}</a>' if src.get("url") else ""
        parts.append(f'<section class="src" data-src="{sid}"><h2>{sid} <small>{title}</small></h2><p class="meta">{n_rows} measurements{link} · licence {html.escape(src.get("licence", "?"))} {badge}</p>')
        for c in items:
            m = rows_by_id.get(c.obs_id, {})
            img = image_for(c)
            what = ""
            if m:
                cond = ", ".join(x for x in (
                    m.get("binder"), m.get("filler") and m["filler"] != "none" and m["filler"],
                    m.get("regolith_wt") and f"{m['regolith_wt']} wt%", m.get("orientation"), m.get("process"),
                    m.get("environment") and m["environment"] != "air" and m["environment"],
                    m.get("temperature_c") and m["temperature_c"] not in ("23", "") and f"{m['temperature_c']} °C",
                ) if x)
                what = f'<div class="what"><b>{html.escape(m.get("property", ""))}</b> = {html.escape(m.get("value_raw", ""))} {html.escape(m.get("unit_raw", ""))} <span class="cond">{html.escape(cond)}</span></div>'
            loc = " · ".join(html.escape(x) for x in (
                c.page and f"p.{c.page}", c.anchor_id, c.row_label and f"row “{c.row_label}”", c.col_label and f"col “{c.col_label}”",
            ) if x)
            img_html = f'<img data-k="{img}" alt="PDF crop">' if img else ""
            parts.append(
                f'<article class="c {c.severity}" data-sev="{c.severity}" data-verdict="{c.verdict}">'
                f'<header><span class="pill {c.severity}">{c.verdict}</span> <code>{html.escape(c.obs_id)}</code> <span class="loc">{loc}</span></header>'
                f'{what}<p>{html.escape(c.message)}</p>{img_html}</article>'
            )
        parts.append("</section>")

    verdict_rows = "".join(
        f'<tr><td><span class="pill {SEV(v)}">{v}</span></td><td>{n}</td></tr>' for v, n in verdict_counts.most_common()
    )
    image_js = "{" + ",".join(f'"{k}":"{v}"' for k, v in images.items()) + "}"
    page = TEMPLATE.format(
        date=date.today().isoformat(),
        measured=measured,
        located=located,
        errors=sev_counts["error"],
        warnings=sev_counts["warning"],
        infos=sev_counts["info"],
        oks=sev_counts["ok"],
        verdict_rows=verdict_rows,
        body="".join(parts),
        images=image_js,
    )
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "audit_report.html").write_text(page, encoding="utf-8")


def SEV(verdict: str) -> str:
    from .audit import SEVERITY

    return SEVERITY[verdict][0]


TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Evidence Audit</title>
<style>
:root{{--bg:#f7f7f5;--fg:#1d1f23;--muted:#5d6470;--card:#fff;--line:#e2e2de;--err:#c62828;--warn:#b26a00;--info:#1f5fbf;--ok:#2e7d32}}
@media (prefers-color-scheme:dark){{:root{{--bg:#15171b;--fg:#e8e9ec;--muted:#a1a7b3;--card:#1e2127;--line:#30343c;--err:#ef6b6b;--warn:#f0a73a;--info:#7aa7f0;--ok:#6cc070}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;padding:24px max(16px,4vw)}}
h1{{font-size:22px;margin:0 0 4px}}h2{{font-size:17px;margin:28px 0 2px}}h2 small{{font-weight:400;color:var(--muted)}}
.meta,.loc,.cond{{color:var(--muted)}}a{{color:var(--info)}}
.summary{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}}.stat{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;min-width:120px}}
.stat b{{display:block;font-size:22px}}
.pill{{display:inline-block;border-radius:999px;padding:0 8px;font-size:12px;font-weight:600;border:1px solid currentColor}}
.pill.error{{color:var(--err)}}.pill.warning{{color:var(--warn)}}.pill.info{{color:var(--info)}}.pill.ok{{color:var(--ok)}}
.c{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);border-radius:8px;padding:10px 14px;margin:10px 0}}
.c.error{{border-left-color:var(--err)}}.c.warning{{border-left-color:var(--warn)}}.c.info{{border-left-color:var(--info)}}.c.ok{{border-left-color:var(--ok)}}
.c p{{margin:6px 0}}.c img{{max-width:100%;border:1px solid var(--line);border-radius:4px;margin-top:6px;background:#fff}}
.filters{{position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:2;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid var(--line)}}
.filters label{{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:3px 10px;cursor:pointer}}
table{{border-collapse:collapse}}td{{padding:2px 10px 2px 0}}.legend span{{margin-right:14px}}
code{{font-size:12px}}
</style></head><body>
<h1>Evidence Audit</h1>
<p class="meta">Moon-Material Simulator · generated {date} by <code>python -m evidence.audit</code>. The auditor never changes data; it only comments.</p>
<div class="summary">
<div class="stat"><b>{measured}</b>measurements</div><div class="stat"><b>{located}</b>re-found in the cited cell/text</div>
<div class="stat"><b style="color:var(--err)">{errors}</b>errors</div><div class="stat"><b style="color:var(--warn)">{warnings}</b>warnings</div>
<div class="stat"><b style="color:var(--info)">{infos}</b>info</div><div class="stat"><b style="color:var(--ok)">{oks}</b>ok</div>
</div>
<details><summary>All verdicts</summary><table>{verdict_rows}</table></details>
<p class="legend">Boxes on crops: <span style="color:#1a73f2">■ row label</span><span style="color:#8c40d9">■ column header / figure</span><span style="color:#1aa640">■ our value</span><span style="color:#e62626">■ what the cited cell holds</span></p>
<div class="filters">Show:
<label><input type="checkbox" value="error" checked> errors</label><label><input type="checkbox" value="warning" checked> warnings</label>
<label><input type="checkbox" value="info" checked> info</label><label><input type="checkbox" value="ok"> ok</label></div>
{body}
<script>
const IMG={images};
document.querySelectorAll('img[data-k]').forEach(i=>{{i.src='data:image/jpeg;base64,'+IMG[i.dataset.k]}});
function apply(){{const on=new Set([...document.querySelectorAll('.filters input:checked')].map(x=>x.value));
document.querySelectorAll('article.c').forEach(a=>a.hidden=!on.has(a.dataset.sev));}}
document.querySelectorAll('.filters input').forEach(x=>x.addEventListener('change',apply));apply();
</script></body></html>
"""
