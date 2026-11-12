"""
Moon Material Extractor GUI v3
Three-stage, NO-AI workflow:
1. Scan PDFs/documents: extract text, native tables, OCR fallback, and chart/figure images.
2. Review candidates and select scientific properties of interest.
3. Build/export a combined dataset.

Scientific values are candidates, not verified measurements. Chart images are
preserved for review; automatic numerical chart digitization is deliberately
not guessed without reliable axis calibration.
"""

from pathlib import Path
import re, os, sys, json, threading, queue, traceback, subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import pandas as pd

SUPPORTED = {'.pdf', '.docx', '.txt', '.md', '.html', '.htm', '.csv', '.xlsx'}

PROPERTIES = {
    'tensile_strength': (r'tensile\s+strength|ultimate\s+tensile|\bUTS\b|σ\s*max', r'MPa|GPa|psi|ksi'),
    'tensile_modulus': (r'tensile\s+modulus|young.?s\s+modulus|elastic\s+modulus', r'GPa|MPa|psi|ksi'),
    'elongation_at_break': (r'elongation(?:\s+at\s+break)?|strain\s+at\s+break', r'%'),
    'flexural_strength': (r'flexural\s+strength|bending\s+strength', r'MPa|GPa|psi|ksi'),
    'flexural_modulus': (r'flexural\s+modulus|bending\s+modulus', r'GPa|MPa|psi|ksi'),
    'compressive_strength': (r'compressive\s+(?:yield\s+)?strength|compression\s+strength', r'MPa|GPa|psi|ksi'),
    'compressive_modulus': (r'compressive\s+modulus|compression\s+modulus', r'GPa|MPa'),
    'maximum_stress_unspecified': (r'maximum\s+stress|peak\s+stress|max\s+stress', r'MPa|GPa|psi|ksi'),
    'density': (r'\bdensity\b', r'g\s*/\s*cm(?:3|³)|kg\s*/\s*m(?:3|³)'),
    'porosity': (r'\bporosity\b', r'%'),
    'glass_transition': (r'glass\s+transition|\bTg\b', r'°\s*C|℃|K'),
    'melting_temperature': (r'melting\s+(?:temperature|point)|\bTm\b', r'°\s*C|℃|K'),
    'degradation_temperature': (r'degradation\s+temperature|decomposition\s+temperature|\bT5\s*%|\bTd\b', r'°\s*C|℃|K'),
    'thermal_conductivity': (r'thermal\s+conductivity', r'W\s*/\s*m\s*K|W\s*m-1\s*K-1'),
    'regolith_content': (r'regolith|simulant|CLRS|BP-1|LHS-1|LMS-1|MGS-1|JSC-1A?|NU-LHT', r'wt\.?\s*%|vol\.?\s*%|%'),
    'particle_size': (r'particle\s+size|median\s+(?:particle\s+)?diameter|\bD50\b', r'µm|μm|um|microns?|mm'),
    'printing_temperature': (r'nozzle\s+temperature|printing\s+temperature|print\s+temperature', r'°\s*C|℃'),
    'layer_height': (r'layer\s+(?:height|thickness)', r'mm|µm|μm'),
    'infill': (r'\binfill\b', r'%'),
}
POLYMERS = ['PLA', 'PEEK', 'PHB', 'PP', 'LDPE', 'HDPE', 'ABS', 'PETG', 'PEKK', 'PA12', 'nylon', 'PEI', 'PPSU', 'epoxy']
SIMULANTS = ['BP-1', 'LHS-1', 'LHS-1E', 'LMS-1', 'LMS-1D', 'MGS-1', 'JSC-1A', 'NU-LHT', 'CLRS-1', 'JEZ-1']
NUM = r'[-+]?\d+(?:[.,]\d+)?(?:\s*(?:±|\+/-)\s*\d+(?:[.,]\d+)?)?'

def safe(s):
    return re.sub(r'[<>:"/\\|?*]', '_', str(s))

def clean_scientific_text(text):
    """Normalize common PDF text artifacts without inventing missing content."""
    text = (text or "").replace("\u00ad", "")
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = re.sub(r"-\s*\n\s*(?=[a-z])", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    # Recover a subset of missing spaces caused by PDF character positioning.
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[.!?])(?=[A-Z])", " ", text)
    return text.strip()


def extract_dois(text):
    """Extract bounded DOI candidates and trim likely concatenated title text."""
    found = []
    for match in re.finditer(r"10\.\d{4,9}/[A-Za-z0-9._;()/:+-]{3,90}", text or "", re.I):
        doi = match.group(0).rstrip(".,;:)")
        doi = re.split(r"(?<=[0-9a-z])(?=[A-Z][a-z])", doi, maxsplit=1)[0]
        if 8 <= len(doi) <= 100 and doi not in found:
            found.append(doi)
    return found


def metadata(text):
    doi = extract_dois(text)
    polys = [p for p in POLYMERS if re.search(
        r"(?<![A-Za-z0-9])" + re.escape(p) + r"(?![A-Za-z0-9])", text, re.I)]
    sims = [s for s in SIMULANTS if re.search(re.escape(s), text, re.I)]
    # Composition must have an explicit wt.% or vol.% unit. Bare '%' is excluded.
    compositions = re.findall(
        r"\b\d+(?:[.,]\d+)?\s*(?:wt\.?\s*%|vol\.?\s*%|%\s*(?:wt|vol)\b)", text, re.I
    )
    temps = re.findall(r"[-+]?\d+(?:[.,]\d+)?\s*(?:°\s*C\b|℃|K\b)", text, re.I)
    return doi, polys, sims, compositions, temps


def split_contexts(text):
    text = clean_scientific_text(text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", text)
    return [p.strip() for p in parts if p.strip()]


def looks_like_equation_or_reference(context):
    low = context.lower()
    if any(token in low for token in (
        "where ", "equation", "eq.", "∆h", "δh", "χ (%)", "×100",
        "× 100", "reference value", "100% crystalline", "calculated as"
    )):
        return True
    math_symbols = sum(context.count(ch) for ch in ("=", "∑", "√", "∆", "×"))
    return math_symbols >= 3


def make_candidate(record, context, prop, value, unit, doi, polys, sims,
                   compositions, temps, confidence, note):
    material_terms = list(dict.fromkeys(polys + sims))
    return {
        "source_file": record["source_file"],
        "page": record["page"],
        "extraction_method": record["extraction_method"],
        "property_guess": prop,
        "value_raw": value.strip(),
        "unit_raw": unit.strip(),
        "polymer_candidates": ";".join(polys),
        "simulant_candidates": ";".join(sims),
        "material_context": ";".join(material_terms),
        "regolith_content_candidates": ";".join(compositions),
        "temperature_candidates": ";".join(temps),
        "doi_candidates": ";".join(doi),
        "confidence": confidence,
        "filter_note": note,
        "context_sentence": context[:900],
        "review_status": "PENDING",
        "reviewer_value": "",
        "reviewer_unit": "",
        "review_notes": ""
    }

def render_pdf_page(pdf_path, page_index, zoom=2.0):
    import fitz
    import numpy as np
    import cv2
    doc = fitz.open(str(pdf_path))
    page = doc[page_index]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    doc.close()
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def extract_pdf(path, outdir, use_ocr=True, tesseract_path=''):
    import pdfplumber
    records, table_frames, chart_rows = [], [], []
    chart_dir = outdir / 'chart_review_images'
    chart_dir.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(str(path)) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            text = page.extract_text(x_tolerance=1.5, y_tolerance=3, layout=False) or ''
            method = 'PDF_TEXT'
            image = None

            # OCR whole page when embedded text is absent/very sparse.
            if len(text.strip()) < 40 and use_ocr:
                try:
                    import pytesseract
                    from PIL import Image
                    if tesseract_path:
                        pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    image = render_pdf_page(path, page_no - 1, 2.2)
                    rgb = image[:, :, ::-1]
                    text = pytesseract.image_to_string(Image.fromarray(rgb), lang='eng')
                    method = 'OCR'
                except Exception as exc:
                    method = 'OCR_ERROR'
                    print(f'OCR warning {path.name} p{page_no}: {exc}')

            records.append({
                'source_file': path.name, 'page': page_no,
                'extraction_method': method, 'text': text
            })

            # Native PDF table extraction.
            try:
                found = page.extract_tables() or []
                for table_no, table in enumerate(found, 1):
                    if not table or len(table) < 2:
                        continue
                    width = max(len(row or []) for row in table)
                    rows = [(row or []) + [''] * (width - len(row or [])) for row in table]
                    df = pd.DataFrame(rows)
                    df.insert(0, 'source_file', path.name)
                    df.insert(1, 'page', page_no)
                    df.insert(2, 'table_number', table_no)
                    table_frames.append((f'{safe(path.stem)}_p{page_no}_t{table_no}', df))
            except Exception as exc:
                print(f'Table warning {path.name} p{page_no}: {exc}')

            # Flag likely chart/figure pages and preserve a page image for review.
            low = text.lower()
            chart_words = ('figure', 'fig.', 'bar chart', 'bending modulus',
                           'compressive modulus', 'plot', 'graph', 'strength [')
            has_graphics = bool(page.images) or len(page.rects) >= 5 or len(page.curves) >= 5
            chart_hint = any(w in low for w in chart_words)
            if has_graphics and (chart_hint or len(page.images) > 0):
                try:
                    if image is None:
                        image = render_pdf_page(path, page_no - 1, 2.0)
                    img_path = chart_dir / f'{safe(path.stem)}_page_{page_no}.png'
                    import cv2
                    cv2.imwrite(str(img_path), image)
                    chart_rows.append({
                        'source_file': path.name, 'page': page_no,
                        'image_path': str(img_path),
                        'detection_reason': 'graphics_and_chart_keywords' if chart_hint else 'page_contains_graphics',
                        'numeric_status': 'REVIEW_REQUIRED'
                    })
                except Exception as exc:
                    print(f'Chart image warning {path.name} p{page_no}: {exc}')
    return records, table_frames, chart_rows

def extract_other(path):
    ext = path.suffix.lower()
    if ext == '.docx':
        from docx import Document
        d = Document(str(path))
        rec = [{'source_file': path.name, 'page': i + 1, 'extraction_method': 'DOCX',
                'text': p.text} for i, p in enumerate(d.paragraphs) if p.text.strip()]
        tables = []
        for tn, table in enumerate(d.tables, 1):
            rows = [[c.text.strip() for c in row.cells] for row in table.rows]
            if rows:
                width = max(map(len, rows))
                df = pd.DataFrame([r + [''] * (width-len(r)) for r in rows])
                df.insert(0, 'source_file', path.name)
                df.insert(1, 'table_number', tn)
                tables.append((f'{safe(path.stem)}_t{tn}', df))
        return rec, tables
    if ext in {'.txt', '.md'}:
        text = path.read_text(encoding='utf-8', errors='replace')
    elif ext in {'.html', '.htm'}:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(path.read_text(encoding='utf-8', errors='replace'), 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer']): tag.decompose()
        text = soup.get_text('\n', strip=True)
    elif ext == '.csv':
        text = pd.read_csv(path).to_string(index=False)
    elif ext == '.xlsx':
        sheets = pd.read_excel(path, sheet_name=None)
        rec = [{'source_file': path.name, 'page': f'sheet:{name}',
                'extraction_method': 'XLSX', 'text': df.to_string(index=False)}
               for name, df in sheets.items()]
        return rec, []
    else:
        return [], []
    return [{'source_file': path.name, 'page': 1, 'extraction_method': ext[1:].upper(),
             'text': text}], []

def build_candidates(records):
    """
    Context-aware, rule-based candidate extraction (no AI).

    Composition values require explicit wt.%/vol.% plus material context.
    Mechanical/thermal values must be near the matching property phrase.
    Equation-like passages are excluded from candidate generation.
    """
    rows = []
    for record in records:
        for context in split_contexts(record.get("text", "")):
            if looks_like_equation_or_reference(context):
                continue

            doi, polys, sims, compositions, temps = metadata(context)

            composition_pattern = re.compile(
                rf"(?P<value>{NUM})\s*(?P<unit>wt\.?\s*%|vol\.?\s*%|%\s*(?:wt|vol)\b)",
                re.I
            )
            has_material_context = bool(
                sims or re.search(
                    r"\b(regolith|simulant|composite|composites|filler|reinforced)\b",
                    context, re.I
                )
            )
            if has_material_context:
                composition_matches = []
                for match in composition_pattern.finditer(context):
                    composition_matches.append((match.group("value"), match.group("unit")))

                # Handle shared-unit lists such as "5 and 10 wt.% CLRS-1".
                shared_unit_pattern = re.compile(
                    rf"(?P<first>{NUM})\s*(?:and|&)\s*(?P<second>{NUM})\s*"
                    rf"(?P<unit>wt\.?\s*%|vol\.?\s*%|%\s*(?:wt|vol)\b)",
                    re.I
                )
                for match in shared_unit_pattern.finditer(context):
                    composition_matches.append((match.group("first"), match.group("unit")))
                    composition_matches.append((match.group("second"), match.group("unit")))

                seen_compositions = set()
                for value, unit in composition_matches:
                    key = (value.strip(), unit.strip().lower())
                    if key in seen_compositions:
                        continue
                    seen_compositions.add(key)
                    rows.append(make_candidate(
                        record, context, "regolith_content",
                        value, unit,
                        doi, polys, sims, compositions, temps,
                        "MEDIUM",
                        "Explicit wt.%/vol.% near material context; verify exact composite association."
                    ))

            for prop, (name_rx, unit_rx) in PROPERTIES.items():
                if prop == "regolith_content":
                    continue
                name_matches = list(re.finditer(name_rx, context, re.I))
                if not name_matches:
                    continue
                value_pattern = re.compile(
                    rf"(?P<value>{NUM})\s*(?P<unit>{unit_rx})(?![A-Za-z])",
                    re.I
                )
                property_values = [
                    (m.group("value"), m.group("unit"), m.start())
                    for m in value_pattern.finditer(context)
                ]
                # Handle shared-unit pairs such as "64.3 and 55.2 MPa".
                shared_values = re.compile(
                    rf"(?P<first>{NUM})\s*(?:and|&)\s*(?P<second>{NUM})\s*"
                    rf"(?P<unit>{unit_rx})(?![A-Za-z])",
                    re.I
                )
                for m in shared_values.finditer(context):
                    property_values.append((m.group("first"), m.group("unit"), m.start()))
                    property_values.append((m.group("second"), m.group("unit"), m.start()))

                seen_property_values = set()
                for value, unit, value_start in property_values:
                    pair = (value, unit.lower())
                    if pair in seen_property_values:
                        continue
                    seen_property_values.add(pair)
                    distance = min(
                        0 if nm.start() <= value_start <= nm.end()
                        else min(abs(value_start-nm.end()), abs(nm.start()-value_start))
                        for nm in name_matches
                    )
                    if distance > 180:
                        continue
                    rows.append(make_candidate(
                        record, context, prop, value, unit,
                        doi, polys, sims, compositions, temps,
                        "HIGH" if distance <= 60 else "MEDIUM",
                        "Property/value proximity heuristic; verify which material each value belongs to."
                    ))

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(subset=[
            "source_file", "page", "property_guess", "value_raw",
            "unit_raw", "context_sentence"
        ]).reset_index(drop=True)
    return df

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('Moon Material Extractor v4 — No AI (Context-aware)')
        self.root.geometry('1180x820')
        self.q = queue.Queue()
        self.paths = []
        self.records = []
        self.candidates = pd.DataFrame()
        self.tables = []
        self.charts = []
        self.output_dir = tk.StringVar(value=str(Path.home() / 'Moon_Material_Dataset'))
        self.use_ocr = tk.BooleanVar(value=True)
        self.tesseract = tk.StringVar()
        self.selected_properties = {k: tk.BooleanVar(value=True) for k in PROPERTIES}
        self._build_ui()
        self.root.after(150, self.poll)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10); main.pack(fill='both', expand=True)
        files = ttk.LabelFrame(main, text='Input documents', padding=8); files.pack(fill='x')
        row = ttk.Frame(files); row.pack(fill='x')
        ttk.Button(row, text='Add PDF / files', command=self.add_files).pack(side='left')
        ttk.Button(row, text='Add folder', command=self.add_folder).pack(side='left', padx=5)
        ttk.Button(row, text='Remove selected', command=self.remove).pack(side='left')
        ttk.Button(row, text='Clear', command=self.clear).pack(side='left', padx=5)
        self.file_list = tk.Listbox(files, height=4, selectmode='extended')
        self.file_list.pack(fill='x', pady=5)

        stages = ttk.LabelFrame(main, text='Three-stage workflow', padding=8)
        stages.pack(fill='x', pady=8)
        srow = ttk.Frame(stages); srow.pack(fill='x')
        self.scan_btn = ttk.Button(srow, text='1. SCAN: Text + Tables + Charts', command=self.start_scan)
        self.scan_btn.pack(side='left')
        self.review_btn = ttk.Button(srow, text='2. REVIEW: Select properties', command=self.open_review)
        self.review_btn.pack(side='left', padx=8)
        self.export_btn = ttk.Button(srow, text='3. BUILD DATASET', command=self.export_dataset)
        self.export_btn.pack(side='left')
        self.progress = ttk.Progressbar(stages, mode='indeterminate')
        self.progress.pack(fill='x', pady=8)

        opts = ttk.Frame(main); opts.pack(fill='x')
        ttk.Checkbutton(opts, text='Use OCR for scanned / image-only PDF pages', variable=self.use_ocr).pack(side='left')
        ttk.Label(opts, text='Tesseract executable (optional):').pack(side='left', padx=(12,4))
        ttk.Entry(opts, textvariable=self.tesseract, width=38).pack(side='left')
        ttk.Button(opts, text='Browse', command=self.pick_tesseract).pack(side='left', padx=4)

        out = ttk.LabelFrame(main, text='Dataset output folder', padding=6); out.pack(fill='x', pady=6)
        ttk.Entry(out, textvariable=self.output_dir).pack(side='left', fill='x', expand=True)
        ttk.Button(out, text='Browse', command=self.pick_output).pack(side='left', padx=5)
        ttk.Button(out, text='Open folder', command=self.open_output).pack(side='left')

        self.nb = ttk.Notebook(main); self.nb.pack(fill='both', expand=True, pady=6)
        self.preview_tab = ttk.Frame(self.nb); self.property_tab = ttk.Frame(self.nb)
        self.chart_tab = ttk.Frame(self.nb); self.log_tab = ttk.Frame(self.nb)
        self.nb.add(self.preview_tab, text='Candidate preview')
        self.nb.add(self.property_tab, text='Property selection & review')
        self.nb.add(self.chart_tab, text='Chart images detected')
        self.nb.add(self.log_tab, text='Process log')
        self.tree = ttk.Treeview(self.preview_tab, show='headings')
        self.tree.pack(fill='both', expand=True)
        self.prop_canvas = tk.Canvas(self.property_tab, height=180)
        self.prop_canvas.pack(fill='x')
        self.prop_frame = ttk.Frame(self.prop_canvas)
        self.prop_canvas.create_window((0,0), window=self.prop_frame, anchor='nw')
        for i, (name, var) in enumerate(self.selected_properties.items()):
            ttk.Checkbutton(self.prop_frame, text=name, variable=var).grid(row=i//4, column=i%4, sticky='w', padx=8, pady=3)
        reviewbar = ttk.Frame(self.property_tab); reviewbar.pack(fill='x')
        ttk.Button(reviewbar, text='Accept selected candidate', command=lambda:self.set_review('ACCEPTED')).pack(side='left')
        ttk.Button(reviewbar, text='Reject selected candidate', command=lambda:self.set_review('REJECTED')).pack(side='left', padx=5)
        self.review_tree = ttk.Treeview(self.property_tab, show='headings', height=10)
        self.review_tree.pack(fill='both', expand=True)
        self.chart_tree = ttk.Treeview(self.chart_tab, show='headings')
        self.chart_tree.pack(fill='both', expand=True)
        self.log = ScrolledText(self.log_tab, state='disabled'); self.log.pack(fill='both', expand=True)
        ttk.Label(main, text='NO AI mode. Context-aware candidates only; equations/bare percentages are filtered. Verify every value before ML use.',
                  foreground='#9a4b00').pack(anchor='w')

    def logmsg(self, msg):
        self.log.configure(state='normal'); self.log.insert('end', msg+'\n')
        self.log.see('end'); self.log.configure(state='disabled')

    def add_files(self):
        for p in filedialog.askopenfilenames(filetypes=[('Supported files', ' '.join('*'+e for e in SUPPORTED)), ('All files','*.*')]):
            if p not in self.paths: self.paths.append(p)
        self.refresh_files()

    def add_folder(self):
        p = filedialog.askdirectory()
        if p and p not in self.paths: self.paths.append(p)
        self.refresh_files()

    def refresh_files(self):
        self.file_list.delete(0,'end')
        for p in self.paths: self.file_list.insert('end',p)

    def remove(self):
        for i in reversed(self.file_list.curselection()): del self.paths[i]
        self.refresh_files()

    def clear(self):
        self.paths=[]; self.refresh_files()

    def pick_output(self):
        p=filedialog.askdirectory()
        if p: self.output_dir.set(p)

    def pick_tesseract(self):
        p=filedialog.askopenfilename(filetypes=[('Tesseract','tesseract.exe'),('All files','*.*')])
        if p: self.tesseract.set(p)

    def start_scan(self):
        if not self.paths:
            messagebox.showwarning('No input','Add one or more files/folders first.'); return
        self.scan_btn.state(['disabled']); self.progress.start(10)
        args=(list(self.paths), self.output_dir.get(), self.use_ocr.get(), self.tesseract.get())
        threading.Thread(target=self.scan_worker,args=args,daemon=True).start()

    def scan_worker(self, paths, outpath, useocr, tess):
        try:
            out=Path(outpath); out.mkdir(parents=True,exist_ok=True)
            files=[]
            for item in paths:
                p=Path(item)
                if p.is_file(): files.append(p)
                elif p.is_dir(): files.extend(f for f in p.rglob('*') if f.is_file() and f.suffix.lower() in SUPPORTED)
            files=sorted(set(f for f in files if f.suffix.lower() in SUPPORTED and out.resolve() not in f.resolve().parents))
            if not files: raise ValueError('No supported files found.')
            all_records=[]; all_tables=[]; all_charts=[]
            for p in files:
                self.q.put(('log',f'Scanning {p.name}'))
                try:
                    if p.suffix.lower()=='.pdf':
                        rec,tabs,charts=extract_pdf(p,out,useocr,tess)
                    else:
                        rec,tabs=extract_other(p); charts=[]
                    all_records.extend(rec); all_tables.extend(tabs); all_charts.extend(charts)
                except Exception as exc:
                    self.q.put(('log',f'ERROR {p.name}: {exc}'))
            self.records=all_records; self.tables=all_tables; self.charts=all_charts
            # Save raw extracted text and native tables separately.
            (out/'extracted_text').mkdir(exist_ok=True)
            for idx,r in enumerate(all_records):
                name=f"{safe(Path(r['source_file']).stem)}_page_{safe(r['page'])}_{idx}.txt"
                (out/'extracted_text'/name).write_text(r['text'],encoding='utf-8')
            tdir=out/'tables'; tdir.mkdir(exist_ok=True)
            for name,df in all_tables: df.to_csv(tdir/(name+'.csv'),index=False,encoding='utf-8-sig')
            pd.DataFrame(all_charts,columns=['source_file','page','image_path','detection_reason','numeric_status']).to_csv(out/'chart_inventory.csv',index=False,encoding='utf-8-sig')
            self.candidates=build_candidates(all_records)
            if not self.candidates.empty:
                self.candidates.to_csv(out/'candidate_values_all.csv',index=False,encoding='utf-8-sig')
            self.q.put(('loaded',None))
            self.q.put(('log',f'Scan complete: {len(all_records)} text records, {len(all_tables)} table(s), {len(all_charts)} chart/figure page(s), {len(self.candidates)} numeric candidates.'))
            self.q.put(('done',None))
        except Exception as exc:
            self.q.put(('error',str(exc)+'\n'+traceback.format_exc()))

    def open_review(self):
        if self.candidates.empty:
            messagebox.showinfo('Nothing to review','Run Stage 1 Scan first.'); return
        self.nb.select(self.property_tab)

    def set_review(self,status):
        sel=self.review_tree.selection()
        if not sel: messagebox.showinfo('Select row','Select a candidate first.'); return
        idx=int(sel[0]); self.candidates.at[idx,'review_status']=status
        self.show_candidates()

    def show_candidates(self):
        df=self.candidates
        cols=['source_file','page','property_guess','value_raw','unit_raw','extraction_method','review_status']
        for tree in (self.tree,self.review_tree):
            tree.delete(*tree.get_children()); tree['columns']=cols
            for c in cols:
                tree.heading(c,text=c); tree.column(c,width=145,stretch=True)
            if df is not None and not df.empty:
                for i,r in df.iterrows():
                    tree.insert('','end',iid=str(i),values=[r.get(c,'') for c in cols])

    def show_charts(self):
        self.chart_tree.delete(*self.chart_tree.get_children())
        cols=['source_file','page','image_path','detection_reason','numeric_status']
        self.chart_tree['columns']=cols
        for c in cols:
            self.chart_tree.heading(c,text=c); self.chart_tree.column(c,width=180,stretch=True)

        for i,r in enumerate(self.charts):
            self.chart_tree.insert('','end',iid=str(i),values=[r.get(c,'') for c in cols])

    def export_dataset(self):
        if self.candidates.empty and not self.tables:
            messagebox.showinfo('No data','Run Stage 1 Scan first.'); return
        out=Path(self.output_dir.get()); out.mkdir(parents=True,exist_ok=True)
        chosen=[k for k,v in self.selected_properties.items() if v.get()]
        df=self.candidates.copy()
        if not df.empty:
            df=df[df.property_guess.isin(chosen)].copy()
            # Keep all selected-property candidates in candidate dataset; verified subset is separate.
            df.to_csv(out/'dataset_candidates.csv',index=False,encoding='utf-8-sig')
            accepted=df[df.review_status=='ACCEPTED'].copy()
            if not accepted.empty:
                accepted['dataset_status']='MANUALLY_ACCEPTED'
                accepted.to_csv(out/'dataset_verified.csv',index=False,encoding='utf-8-sig')
            else:
                pd.DataFrame(columns=list(df.columns)+['dataset_status']).to_csv(out/'dataset_verified.csv',index=False,encoding='utf-8-sig')
        # One workbook bundle: text-derived candidates, each raw table, chart inventory, verified rows.
        # Tables retain their original cell layout; they are not guessed into scientific measurements.
        try:
            with pd.ExcelWriter(out/'dataset_bundle.xlsx', engine='openpyxl') as writer:
                if not df.empty:
                    df.to_excel(writer, sheet_name='Text_Candidates', index=False)
                else:
                    pd.DataFrame(columns=['source_file','page','property_guess','value_raw','unit_raw']).to_excel(
                        writer, sheet_name='Text_Candidates', index=False)
                if self.tables:
                    for idx, (table_name, table_df) in enumerate(self.tables, 1):
                        sheet = safe(table_name)[:31] or f'Table_{idx}'
                        table_df.to_excel(writer, sheet_name=sheet, index=False)
                if self.charts:
                    pd.DataFrame(self.charts).to_excel(writer, sheet_name='Chart_Inventory', index=False)
                else:
                    pd.DataFrame(columns=['source_file','page','image_path','numeric_status']).to_excel(
                        writer, sheet_name='Chart_Inventory', index=False)
                verified_path = out/'dataset_verified.csv'
                if verified_path.exists():
                    pd.read_csv(verified_path).to_excel(writer, sheet_name='Verified_Candidates', index=False)
        except Exception as exc:
            self.logmsg(f'Workbook bundle warning: {exc}')

        # Keep raw table rows in their original layout; do not silently coerce them into measurements.
        manifest={
            'workflow':'three_stage_no_ai',
            'stages':['scan_text_tables_charts','select_and_review_properties','build_dataset'],
            'selected_properties':chosen,
            'text_records':len(self.records),'native_tables':len(self.tables),
            'chart_pages':len(self.charts),'candidate_values':len(df) if not df.empty else 0,
            'chart_numeric_extraction':'not_auto_generated; chart images saved for manual review and future calibrated digitization',
            'warning':'Candidates are unverified. Verify units, material, composition, test conditions and source context.'
        }
        (out/'dataset_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        self.logmsg('Dataset built. See dataset_bundle.xlsx, dataset_candidates.csv, dataset_verified.csv, tables/, chart_review_images/, chart_inventory.csv.')
        messagebox.showinfo('Dataset created','Dataset export complete. Unverified candidates and manually accepted values are saved separately.')

    def open_output(self):
        p=Path(self.output_dir.get()); p.mkdir(parents=True,exist_ok=True)
        if sys.platform.startswith('win'): os.startfile(str(p))
        elif sys.platform=='darwin': subprocess.Popen(['open',str(p)])
        else: subprocess.Popen(['xdg-open',str(p)])

    def poll(self):
        try:
            while True:
                typ,val=self.q.get_nowait()
                if typ=='log': self.logmsg(val)
                elif typ=='loaded':
                    self.show_candidates(); self.show_charts()
                elif typ=='error':
                    self.logmsg(val); self.finish()
                    messagebox.showerror('Scan error',val.splitlines()[0])
                elif typ=='done':
                    self.finish(); messagebox.showinfo('Scan complete','Stage 1 complete. Review candidates and chart images, then build the dataset.')
        except queue.Empty:
            pass
        self.root.after(150,self.poll)

    def finish(self):
        self.progress.stop(); self.scan_btn.state(['!disabled'])

if __name__=='__main__':
    root=tk.Tk()
    App(root)
    root.mainloop()
