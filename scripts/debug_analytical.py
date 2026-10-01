#!/usr/bin/env python3
"""Debug: why the analytical record is not persisted for the janoshik record."""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

JANO_TEXT = """Report no: 211414
Date of test: 2026-09-12
Sample name: Retatrutide
Lot: RT-0926A
Submitter: Example Vendor Ltd
Purity (HPLC): 99.2%
Identity (LC-MS): confirmed
Endotoxin: < 0.5 EU/mg
"""

from pcconnect.pipeline import Pipeline

tmp = tempfile.mkdtemp(prefix="pcv0_dbg_")
try:
    p = Pipeline(tmp, offline=True)
    out = p.ingest_one("janoshik", {"report_id": "211414", "text": JANO_TEXT},
                       retrieved_at="2026-09-30T20:00:00Z")
    print("outcome:", json.dumps(out, indent=1, default=str))
    print("counters:", json.dumps(p.counters, indent=1))
    ev_file = os.path.join(tmp, "run_events.jsonl")
    if os.path.exists(ev_file):
        for line in open(ev_file):
            print("event:", line.strip())
    ae = os.path.join(tmp, "analytical_evidence.jsonl")
    print("analytical file exists:", os.path.exists(ae))
finally:
    shutil.rmtree(tmp)
