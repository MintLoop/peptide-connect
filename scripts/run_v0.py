#!/usr/bin/env python3
"""Run the V0 experiment (offline or live) over the fixture set.

Usage:
  run_v0.py [--offline] [--limit N] [--run-dir DIR]

Offline: no model calls — stubs are zero-assertion, honestly labeled.
Live: routes through the real local fleet (Qwen 27B / Granite / etc.).
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pcconnect.pipeline import Pipeline
from pcconnect.adapters.base import utcnow_iso


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--run-dir", default=os.path.join(ROOT, "artifacts", "v0"))
    args = ap.parse_args()

    fixture_path = os.path.join(ROOT, "fixtures", "v0", "v0_ingest_items.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"]
    if args.limit:
        items = items[:args.limit]

    print("mode=%s items=%d run_dir=%s" % ("offline" if args.offline else "live", len(items), args.run_dir))
    t0 = time.time()
    p = Pipeline(args.run_dir, offline=args.offline)
    states = {}
    for i, item in enumerate(items):
        out = p.ingest_one(item["source_type"], item["raw"], retrieved_at=utcnow_iso())
        s = out.get("outcome", {}).get("state", out.get("state", "?")) if isinstance(out, dict) else "?"
        states[s] = states.get(s, 0) + 1
        if (i + 1) % 100 == 0:
            print("  %d/%d processed (%.1fs elapsed)" % (i + 1, len(items), time.time() - t0))
    elapsed = time.time() - t0

    metrics = {
        "run_metrics": p.counters,
        "model_metrics": p.metrics.snapshot(),
        "states": states,
        "processing_time_s": round(elapsed, 2),
        "mode": "offline" if args.offline else "live",
        "items": len(items),
        "completed_at": utcnow_iso(),
    }
    with open(os.path.join(args.run_dir, "run_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
