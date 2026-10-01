#!/usr/bin/env python3
"""Debug the panel path: why the regulatory record stores instead of opening the panel."""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pcconnect.pipeline import Pipeline
from pcconnect.moa import should_open_panel

tmp = tempfile.mkdtemp(prefix="pcv0_dbg3_")
try:
    p = Pipeline(tmp, offline=True)
    out = p.ingest_one("regulatory_source",
                       {"record_id": "REG-2026-001",
                        "text": "Import alert 99-08: detention of peptide shipments listing Meridian Supply Co as consignee."},
                       retrieved_at="2026-09-30T20:00:00Z")
    print("outcome state:", out["outcome"]["state"])
    # replicate the gate decision manually
    envelope = None
    for line in open(os.path.join(tmp, "source_records.jsonl")):
        rec = json.loads(line)
        if rec["source_type"] == "regulatory_source":
            envelope = rec
            break
    det = p._deterministic_pass(envelope["content"], "regulatory_source")
    extraction = {"assertions": [], "requires_validation": False}
    issue = p._classify_issue(envelope, det, extraction)
    print("issue:", json.dumps(issue))
    ok, reason = should_open_panel(extraction, {"verdict": "OBJECTIONS"}, issue)
    print("gate with OBJECTIONS:", ok, reason)
    ok2, reason2 = should_open_panel(extraction, {"verdict": "NO_MATERIAL_OBJECTION"}, issue)
    print("gate with NO_OBJECTION:", ok2, reason2)
    print("counters:", json.dumps(p.counters))
finally:
    shutil.rmtree(tmp)
