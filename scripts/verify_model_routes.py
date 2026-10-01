#!/usr/bin/env python3
"""Live model-route verification for Peptide Connect V0 (Master Pack §11).

One minimal generation per worker model through the /v1 surface (the exact
transport the pipeline uses). HTTP 200 + non-empty usage = PASS. Serialized
ascending by size; granite first (already resident). Receipts land in
experiments/model-route-verification/.
"""
import json
import os
import time
import urllib.request

BASE = "http://127.0.0.1:11434/v1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "experiments", "model-route-verification")

# (worker, model, kind, payload builder) — ascending size, granite first (resident)
WORKERS = [
    ("entity_candidate_retriever", "bge-m3:567m", "embeddings", ["Shanghai ChangFoo Biotechnology Co., Ltd.", "ChangFoo Bio"]),
    ("primary_extraction_worker", "qwen3.8:27b-mlx-menta-64k", "chat",
     [{"role": "system", "content": "Return JSON only."},
      {"role": "user", "content": "Return {\"ok\": true, \"worker\": \"qwen27b\"} as JSON."}]),
    ("evidence_skeptic", "granite4.2:30b", "chat",
     [{"role": "system", "content": "You are an evidence skeptic. Reply tersely."},
      {"role": "user", "content": "Reply with exactly: NO_MATERIAL_OBJECTION"}]),
    ("visual_examiner", "qwen3-vl:32b", "chat",
     [{"role": "system", "content": "Answer directly with no preamble and no thinking block."},
      {"role": "user", "content": "Reply with exactly: VISUAL_OK"}]),
    ("ocr_fallback", "glm-ocr:bf16", "chat",
     [{"role": "system", "content": "Extract readable text only."},
      {"role": "user", "content": "Reply with exactly: OCR_OK"}]),
    ("hard_case_adjudicator", "qwen3.8-flash-next:125b-mlx", "chat",
     [{"role": "system", "content": "Answer directly with no preamble and no thinking block."},
      {"role": "user", "content": "Reply with exactly: ADJUDICATOR_OK"}]),
]


def post(path, payload, timeout=900):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body, time.time() - t0


def main():
    os.makedirs(OUT, exist_ok=True)
    receipts = []
    for worker, model, kind, payload in WORKERS:
        rec = {"worker": worker, "model": model, "kind": kind}
        print("[%s] testing %s ..." % (worker, model), flush=True)
        try:
            if kind == "embeddings":
                body, elapsed = post("/embeddings", {"model": model, "input": payload})
                dims = len((body.get("data") or [{}])[0].get("embedding", []))
                rec.update({"status": "PASS" if dims > 0 else "FAIL",
                            "embedding_dims": dims, "elapsed_s": round(elapsed, 1)})
            else:
                body, elapsed = post("/chat/completions", {
                    "model": model, "messages": payload,
                    "max_tokens": 64, "temperature": 0.0, "stream": False,
                })
                choice = (body.get("choices") or [{}])[0]
                content = (choice.get("message") or {}).get("content", "")
                finish = choice.get("finish_reason")
                usage = body.get("usage") or {}
                # thinking models may burn the cap in reasoning: empty content +
                # finish=length is still a PASS (skill: record finish_reason)
                ok = bool(usage) and (content.strip() or finish == "length")
                rec.update({
                    "status": "PASS" if ok else "FAIL",
                    "content": (content or "")[:120],
                    "finish_reason": finish,
                    "usage": usage,
                    "elapsed_s": round(elapsed, 1),
                })
        except Exception as e:
            rec.update({"status": "ERROR", "error": str(e)[:300]})
        receipts.append(rec)
        print("    -> %s (%ss)" % (rec["status"], rec.get("elapsed_s", "?")), flush=True)
        with open(os.path.join(OUT, "receipts.json"), "w") as f:
            json.dump({"completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "receipts": receipts}, f, indent=2)
    passed = sum(1 for r in receipts if r["status"] == "PASS")
    print("DONE: %d/%d PASS" % (passed, len(receipts)))


if __name__ == "__main__":
    main()
