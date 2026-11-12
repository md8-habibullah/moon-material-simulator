"""Download the research PDFs listed in research/sources.csv into research/pdfs/ and check their hashes.

Run from the repository root:  python research/download_sources.py

The PDFs are not committed (size and third-party copyright), but the audit and the evidence crops
need them. A hash mismatch means the publisher changed the file: page numbers in the extraction
may no longer line up, so re-run the auditor before trusting it.
"""
import csv
import hashlib
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF_DIR = HERE / "pdfs"


def main() -> int:
    PDF_DIR.mkdir(exist_ok=True)
    problems = 0
    with open(HERE / "sources.csv", newline="", encoding="utf-8") as fh:
        for src in csv.DictReader(fh):
            target = PDF_DIR / src["file"]
            if not target.exists():
                if not src.get("pdf_url"):
                    print(f"  {src['source_id']}: no download URL; get it from {src['url']}")
                    problems += 1
                    continue
                print(f"  {src['source_id']}: downloading {src['pdf_url']}")
                try:
                    req = urllib.request.Request(src["pdf_url"], headers={"User-Agent": "moon-material-simulator research downloader"})
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        target.write_bytes(resp.read())
                except Exception as exc:  # report and carry on with the rest
                    print(f"  {src['source_id']}: download failed ({exc}); get it from {src['url']}")
                    problems += 1
                    continue
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if src.get("sha256") and digest != src["sha256"]:
                print(f"  {src['source_id']}: hash differs from sources.csv. The file changed; re-run the auditor.")
                problems += 1
            else:
                print(f"  {src['source_id']}: ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
