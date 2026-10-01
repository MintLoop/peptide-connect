#!/usr/bin/env python3
"""Debug: which records trigger the Granite audit, and why."""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pcconnect.pipeline import Pipeline
from pcconnect.adapters.base import utcnow_iso

with open(os.path.join(ROOT, "fixtures", "v0", "v0_ingest_items.json")) as f:
    items = json.load(f)["items"]

tmp = tempfile.mkdtemp(prefix="pcv0_dbg2_")
try:
    p = Pipeline(tmp, offline=True)
    granite_sources = []
    orig = p._needs_granite
    def spy(envelope, det):
        r = orig(envelope, det)
        if r:
            granite_sources.append((envelope["source_type"],
                                    envelope["source_record_id"],
                                    (envelope["content"].get("claims_language"))))
        return r
    p._needs_granite = spy
    for item in items:
        p.ingest_one(item["source_type"], item["raw"], retrieved_at=utcnow_iso())
    print("granite triggers: %d" % len(granite_sources))
    for st, rid, flags in granite_sources:
        print("  %-18s %-28s %s" % (st, rid[:28], flags))
    print("counter granite_escalations:", p.counters["granite_escalations"])
finally:
    shutil.rmtree(tmp)
