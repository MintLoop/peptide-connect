"""Model tier client (Master Pack §11).

Stdlib-only HTTP against the local Ollama OpenAI-compatible surface. Each call:
- loads the worker's OWN compact runtime contract (prompt layer) — the Master
  Pack is never resent with routine calls
- validates JSON output against the worker's schema before returning
- records per-model metrics (calls, tokens, schema failures, latency)
- OFFLINE_MODE: deterministic stub responses so the whole pipeline runs and
  tests without any model resident (used by fixtures/tests/smoke)
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")

BASE_URL = "http://127.0.0.1:11434/v1"
TIMEOUT_S = 300
OFFLINE_MODE = False  # set by pipeline from config/env


class Metrics(object):
    def __init__(self):
        self.calls = {}
        self.schema_failures = {}
        self.token_usage = {}
        self.latency_s = {}

    def record(self, model, tokens=None, schema_ok=True, latency=0.0):
        self.calls[model] = self.calls.get(model, 0) + 1
        if tokens:
            u = self.token_usage.get(model, {"prompt": 0, "completion": 0})
            u["prompt"] += tokens.get("prompt_tokens", 0)
            u["completion"] += tokens.get("completion_tokens", 0)
            self.token_usage[model] = u
        if not schema_ok:
            self.schema_failures[model] = self.schema_failures.get(model, 0) + 1
        self.latency_s[model] = self.latency_s.get(model, 0.0) + latency

    def snapshot(self):
        return {
            "calls": dict(self.calls),
            "schema_failures": dict(self.schema_failures),
            "token_usage": dict(self.token_usage),
            "latency_s": {k: round(v, 2) for k, v in self.latency_s.items()},
        }


def _post(url, payload, timeout=TIMEOUT_S):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat(model, messages, temperature=0.1, max_tokens=2048, response_format_json=True):
    """One chat call. Returns (content, usage)."""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if response_format_json:
        payload["response_format"] = {"type": "json_object"}
    resp = _post(BASE_URL + "/chat/completions", payload)
    content = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return content, resp.get("usage", {})


def embed(texts, model="bge-m3:567m"):
    resp = _post(BASE_URL + "/embeddings", {"model": model, "input": texts})
    return [d["embedding"] for d in resp.get("data", [])]


def extract_json(text):
    """Tolerant JSON extraction from model output (fenced or prose-wrapped)."""
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except ValueError:
        pass
    # fenced block
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except ValueError:
            pass
    # first balanced object
    start = text.find("{")
    if start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except ValueError:
                        break
    return None


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * y for x, y in zip(b, b)) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def call_worker(worker, model, messages, schema=None, metrics=None, label=None):
    """Call one runtime worker with its OWN contract prompt + schema + packet.

    Layers respected: worker gets (1) compact system prompt, (2) schema,
    (3) evidence packet, (4) candidate records — nothing else (Compact Runtime
    Prompts layering rule). Offline mode returns a deterministic stub.
    """
    t0 = time.time()
    if OFFLINE_MODE:
        content = _offline_stub(worker, messages)
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
    else:
        try:
            content, usage = chat(model, messages)
        except (urllib.error.URLError, OSError, ValueError) as e:
            if metrics:
                metrics.record(model, schema_ok=False, latency=time.time() - t0)
            return {"error": "transport_error: %s" % e, "worker": worker}
    obj = extract_json(content)
    schema_ok = True
    if schema is not None and isinstance(obj, dict):
        from jsonschema import Draft202012Validator
        v = Draft202012Validator(schema)
        errs = list(v.iter_errors(obj))
        schema_ok = not errs
        if errs:
            obj = {"_schema_errors": [e.message for e in errs[:5]], **(obj if isinstance(obj, dict) else {})}
    if metrics:
        metrics.record(model, tokens=usage, schema_ok=schema_ok, latency=time.time() - t0)
    return {"worker": worker, "model": model, "output": obj, "schema_ok": schema_ok, "label": label}


# ----------------------------------------------------------------------------
# Offline stubs — deterministic, contract-shaped. They intentionally demonstrate
# the pipeline mechanics (routing, validation, lineage, dedup) without models;
# they are NOT evidence and are labeled as such in every artifact.
# ----------------------------------------------------------------------------
def _offline_stub(worker, messages):
    packet_hint = ""
    for m in messages:
        if m.get("role") == "user":
            packet_hint = m.get("content", "")
            break
    import hashlib
    if worker == "qwen27b_extraction":
        # Schema-valid offline extraction: correct IDs, ZERO assertions.
        # Offline mode claims nothing — assertions only come from real models.
        m = re.search(r"EVIDENCE PACKET (SRC-[0-9]{5})", packet_hint)
        sid = m.group(1) if m else "SRC-00000"
        ext_num = int(hashlib.sha256(sid.encode()).hexdigest()[:12], 16) % 1000000
        return json.dumps({
            "extraction_id": "EXT-%06d" % ext_num,
            "source_id": sid,
            "assertions": [],
            "requires_validation": False,
            "notes": "offline stub — zero assertions, not evidence",
        })
    stubs = {
        "granite30b_skeptic": "NO_MATERIAL_OBJECTION",
        "granite_skeptic": "NO_MATERIAL_OBJECTION",
        "moa_resolver": {
            "interpretation": "offline stub — not evidence",
            "supporting_evidence": [],
            "weakening_evidence": [],
            "assumptions_required": [],
            "unresolved_gaps": [],
        },
        "qwen125b_adjudicator": {
            "issue": "offline stub adjudication",
            "decision": "UNRESOLVED",
            "confidence": "HIGH",
            "narrowest_defensible_conclusion": "offline stub — not evidence",
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "source_lineage_considerations": [],
            "alternative_explanations": [],
            "unresolved_questions": [],
            "recommended_evidence_to_obtain": [],
            "human_review_required": True,
        },
        "qwen_vl_examiner": {
            "visible_text": [],
            "visual_observation": [],
            "model_interpretation": [],
            "extraction_adequate": False,
            "requires_validation": False,
            "recommend_ocr_fallback": True,
        },
        "glm_ocr_fallback": {"ocr_text": "", "uncertain_regions": []},
        "dossier_synthesizer": {"dossier_stub": True, "note": "offline stub — not evidence"},
    }
    return json.dumps(stubs.get(worker, {"stub": True, "worker": worker}))
