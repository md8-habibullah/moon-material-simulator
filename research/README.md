# Research data

Everything behind the simulator's "lab-backed" numbers. See [docs/evidence.md](../docs/evidence.md) for the full
story.

| Path | What it is |
| --- | --- |
| `sources.csv` | The 13 sources: citation, licence, type, direct PDF link, SHA-256 of the file we transcribed |
| `download_sources.py` | Downloads the PDFs into `pdfs/` (not committed) and checks their hashes |
| `EXTRACTION_SPEC.md` | The transcription rules: one row per number, with page, table, row and column anchors |
| `extraction/S0xx.csv` | The transcribed values per source |
| `extraction/S0xx_issues.md` | Problems found inside each paper (contradictions, unit slips, missing points) |
| `audit/` | Evidence Auditor output: `audit_comments.csv`, `audit_report.html` (open it in a browser), `audit_index.json` |
| `legacy/` | The team's earlier automatic extraction (`candidate_values_all.csv`, chart inventory, extractor GUI), used as a coverage check |

Rebuild everything from the `backend/` folder:

```bash
python ../research/download_sources.py
python -m evidence.build && python -m evidence.audit
python -m scripts.export_frontend
```
