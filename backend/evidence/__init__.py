"""Evidence pipeline: real measurements from research papers, and an auditor that checks them.

    research/extraction/<SOURCE>.csv   hand-transcribed values with page/table/row/column anchors
            │  python -m evidence.build
            ▼
    data/evidence/measurements.csv     merged, schema-checked, units normalised
            │  python -m evidence.audit
            ▼
    research/audit/audit_comments.csv  one comment per finding (the data is never modified)
    research/audit/audit_report.html   self-contained report with highlighted PDF crops

The auditor only reads. It re-finds every value in its source PDF and says whether the cell, row,
column, page and unit agree. People decide what to change.
"""
