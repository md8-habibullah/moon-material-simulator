# Legacy: the team's first extraction pipeline

The team's first pass at the research data, built by **Yousuf Abdullah** (Dreams of X) in a separate repository,
[YousufAbdullah0001/Moon-Material-Simulator](https://github.com/YousufAbdullah0001/Moon-Material-Simulator), and merged
here on 2026-11-13 so the project lives in one place.

The extractor read the source PDFs automatically and wrote every number it found as a *candidate* (status `PENDING`).
The simulator does not train on these candidates. The verified, page-anchored values in [`../extraction/`](../extraction/)
replaced them. We keep them as a **coverage check**: the Evidence Auditor compares the two, and any candidate that is
missing from the verified set is a value worth a second look.

| File | What it is |
| --- | --- |
| `moon_extractor_gui_v4_no_ai.py` | The extractor (Tkinter GUI, no AI): text, tables, chart pages and candidate numbers from each PDF |
| `candidate_values_all.csv` | 505 candidate values with source file, page and the surrounding text |
| `chart_inventory.csv` | Charts and figures found per page, for manual reading |
| `tables/` | 40 tables the extractor pulled from the PDFs, one CSV per table (`<source>_p<page>_t<n>.csv`) |
| `source_links.md` | The original source list by dataset (A to F), with reading status at the time |

Not carried over:

- **Page images and full page text** (about 130 MB). They are copies of copyrighted papers and the extractor rebuilds
  them from the PDFs (`python ../download_sources.py` fetches those).
- **Empty placeholder files** (processed CSVs, notebooks, docs) that the old repository reserved for later work. That
  work now lives in `backend/evidence/` and `backend/models/`.

Licence: the code and data here are covered by this repository's [MIT licence](../../LICENSE). The extracted values
come from the cited papers; see [`../sources.csv`](../sources.csv) for each paper's own licence.
