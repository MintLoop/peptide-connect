"""V0 pipeline orchestrator.

Implements Master Pack §12 routing flows over the three contract layers:
  adapter → deterministic tier → (visual?) qwen27b → (granite?) → (125B?) → store

Incremental ingestion (§14): unchanged content (by raw_content_hash) skips all
LLM calls and preserves prior normalized evidence. Idempotent stores mean
repeated ingestion never duplicates evidence (§18).
"""
import datetime
import json
import os
import re
import time

from . import hashing
from . import ids
from . import tiers
from .adapters import base as adapters_base
from .adapters.base import get_adapter, utcnow_iso
from .entity import build_blocking_records, resolve_identity, new_supplier_from_observation
from .moa import route_packet, gate_125b, granite_decision
from .store import Store

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")
SCHEMAS = {}  # name -> loaded schema


def _load_schema(name):
    if name not in SCHEMAS:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas", name)
        with open(path, "r", encoding="utf-8") as f:
            SCHEMAS[name] = json.load(f)
    return SCHEMAS[name]


def _load_prompt(fname):
    with open(os.path.join(PROMPTS_DIR, fname), "r", encoding="utf-8") as f:
        return f.read()


# ----------------------------------------------------------------------------
class Pipeline(object):
    def __init__(self, store_dir, offline=False):
        self.store = Store(store_dir)
        self.metrics = tiers.Metrics()
        self.offline = offline
        tiers.OFFLINE_MODE = offline
        self.counters = {
            "records_discovered": 0,
            "unchanged_records": 0,
            "changed_records": 0,
            "new_records": 0,
            "deterministic_only_records": 0,
            "qwen27b_calls": 0,
            "granite_escalations": 0,
            "qwen125b_escalations": 0,
            "qwen_vl_calls": 0,
            "ocr_fallbacks": 0,
            "schema_validation_failures": 0,
            "evidence_family_duplicates_removed": 0,
            "invalid_escalations": 0,
            "human_review_queue": 0,
        }
        self.supplier_seq = 0

    # -- ingestion -------------------------------------------------------------
    def ingest(self, raw_items, retrieved_at=None):
        """Ingest a list of {source_type, raw} items through the full pipeline."""
        for item in raw_items:
            self.ingest_one(item["source_type"], item["raw"], retrieved_at=retrieved_at)

    def ingest_one(self, source_type, raw, retrieved_at=None):
        self.counters["records_discovered"] += 1
        adapter = get_adapter(source_type)

        # 1. adapter emits canonical envelope
        envelope = adapter.emit(raw, retrieved_at=retrieved_at)

        # 2. deterministic change detection (§14): skip LLM work when unchanged
        sync = self.store.sync_entry(source_type, envelope["source_record_id"])
        change_state = "new"
        if sync:
            change_state = "unchanged" if sync.get("content_hash") == envelope["raw_content_hash"] else "changed"
        if change_state == "unchanged":
            self.counters["unchanged_records"] += 1
            self.store.update_sync_entry(
                source_type, envelope["source_record_id"],
                last_checked_at=utcnow_iso(),
                status="unchanged_skip",
            )
            return {"state": "unchanged", "source_record_id": envelope["source_record_id"]}

        # 3. store the source record (idempotent by source_id)
        status, sid = self.store.put_source_record(envelope)
        sid = sid if isinstance(sid, str) else sid
        if change_state == "new":
            self.counters["new_records"] += 1
        else:
            self.counters["changed_records"] += 1

        # 4. evidence-family dedup (§5): same (lab, report) = one family.
        # Cross-source references count: a finnrick/directory/aggregator record
        # whose TEXT cites a lab report joins that report's family as a
        # reference, not an independent confirmation.
        content = envelope["content"]
        lab = content.get("laboratory")
        report_ref = content.get("report_id") or envelope["source_record_id"]
        if not lab:
            cited = self._cited_lab_report(content)
            if cited:
                lab, report_ref = cited
                cross_reference = True
            else:
                cross_reference = False
        else:
            cross_reference = False
        family = ids.evidence_family_id(lab or source_type, report_ref)
        ev_id = ids.evidence_id(sid)
        lineage = {
            "evidence_id": ev_id,
            "source_id": sid,
            "upstream_source_id": None,
            "evidence_family_id": family,
            "lineage_basis": "same_lab_and_report_id" if lab else "source_record",
            "recorded_at": utcnow_iso(),
        }
        # upstream lineage: if another source already references this family,
        # mark this record as a reference (not independent confirmation)
        existing_family_sources = [
            ln for ln in self.store.read_all("evidence_lineage")
            if ln["evidence_family_id"] == family
        ]
        if existing_family_sources:
            lineage["upstream_source_id"] = existing_family_sources[0]["source_id"]
            lineage["lineage_basis"] = "references_existing_family"
            if not cross_reference:
                cross_reference = True
            self.counters["evidence_family_duplicates_removed"] += 1
        l_status, _ = self.store.put_evidence_lineage(lineage)
        if l_status == "duplicate":
            # lineage record already exists (repeated ingestion) — not a new duplicate
            if change_state == "new":
                self.counters["evidence_family_duplicates_removed"] -= 1

        # 5. deterministic extraction of what code can extract (§10)
        det = self._deterministic_pass(content, source_type)

        # 6. route through the model tiers (§12)
        outcome = self._route_and_extract(envelope, sid, det)

        # 7. record sync state for next run
        self.store.update_sync_entry(
            source_type, envelope["source_record_id"],
            content_hash=envelope["raw_content_hash"],
            last_checked_at=utcnow_iso(),
            last_successful_sync=utcnow_iso(),
            status="processed",
            records_seen=1,
            records_changed=0 if change_state == "unchanged" else 1,
        )
        return {"state": change_state, "source_id": sid, "outcome": outcome}

    # -- deterministic pass ------------------------------------------------------
    def _cited_lab_report(self, content):
        """Detect a lab-report citation in text (e.g. 'janoshik report 211414').

        Returns (laboratory, report_ref) or None. Deterministic only — §10.
        """
        text = (content.get("text") or "").lower()
        for lab_name in ("janoshik",):
            m = re.search(lab_name + r"\s+report\s+(?:no\.?\s*[:#]?\s*)?([0-9]{4,8})", text)
            if m:
                return lab_name.capitalize(), m.group(1)
        return None

    def _deterministic_pass(self, content, source_type):
        from .deterministic import (
            extract_lot_numbers, extract_report_ids, extract_dates,
            extract_purity_values,
        )
        text = content.get("text", "") or ""
        det = {
            "lots": extract_lot_numbers(text),
            "report_ids": extract_report_ids(text),
            "dates": extract_dates(text),
            "purity_values": extract_purity_values(text),
            "contact_signals": content.get("contact_signals") or {},
        }
        if source_type == "janoshik":
            det["compound"] = content.get("compound")
            det["dimensions"] = content.get("dimensions")
            det["lab_report_id"] = content.get("report_id")
        return det

    # -- routing ------------------------------------------------------------------
    def _route_and_extract(self, envelope, sid, det):
        packet = {
            "packet_id": sid,
            "envelope": envelope,
            "deterministic": det,
        }
        route = route_packet(packet)
        self.store.event("route", **{k: route[k] for k in ("route", "escalated", "reason") if k in route})

        # Visual route: image → Qwen-VL → adequate? → (GLM-OCR) → Qwen 27B
        if route["route"] == "visual":
            self.counters["qwen_vl_calls"] += 1
            vl_out = self._call_tier(
                "qwen_vl_examiner", "qwen3-vl:32b",
                packet, schema=None,
            )
            vl = vl_out.get("output") or {}
            if not isinstance(vl, dict) or not vl.get("extraction_adequate", False):
                self.counters["ocr_fallbacks"] += 1
                ocr_out = self._call_tier("glm_ocr_fallback", "glm-ocr:bf16", packet)
                packet["ocr_text"] = (ocr_out.get("output") or {}).get("ocr_text", "")
            extraction_result = self._call_tier(
                "qwen27b_extraction", "qwen3.8:27b-mlx-menta-64k",
                packet, schema=_load_schema("extraction.schema.json"),
            )
            return self._store_extraction(sid, envelope, extraction_result, route)

        # Text routes: routine / questionable / hard
        extraction_result = self._call_tier(
            "qwen27b_extraction", "qwen3.8:27b-mlx-menta-64k",
            packet, schema=_load_schema("extraction.schema.json"),
        )
        extraction = extraction_result.get("output")
        if not isinstance(extraction, dict) or extraction.get("_schema_errors"):
            self.counters["schema_validation_failures"] += 1
            self.store.event("schema_failure", source_id=sid)
            # one bounded retry with error feedback
            packet["retry_hint"] = "Your previous output failed schema validation: %s" % (
                extraction.get("_schema_errors") if isinstance(extraction, dict) else "non-dict output")
            extraction_result = self._call_tier(
                "qwen27b_extraction", "qwen3.8:27b-mlx-menta-64k",
                packet, schema=_load_schema("extraction.schema.json"),
            )
            extraction = extraction_result.get("output")
            if not isinstance(extraction, dict) or extraction.get("_schema_errors"):
                self.counters["schema_validation_failures"] += 1
                self.store.event("schema_failure_final", source_id=sid)
                return {"state": "schema_failure", "source_id": sid}

        # re-classify after extraction (requires_validation may be set)
        route2 = route_packet({"packet_id": sid, "extraction": extraction})
        if route2["route"] == "questionable" or self._needs_granite(envelope, det):
            self.counters["granite_escalations"] += 1
            gran_out = self._call_tier("granite30b_skeptic", "granite4.2:30b", {
                "packet_id": sid,
                "envelope": envelope,
                "deterministic": det,
                "extraction": extraction,
            })
            objections = gran_out.get("output")
            verdict, needs_adj, categories = granite_decision(objections)
            if verdict == "OBJECTIONS":
                invoke, reason = gate_125b(objections, None)
                if invoke:
                    self.counters["qwen125b_escalations"] += 1
                    adj_out = self._call_tier("qwen125b_adjudicator", "qwen3.8-flash-next:125b-mlx", {
                        "packet_id": sid,
                        "envelope": envelope,
                        "deterministic": det,
                        "extraction": extraction,
                        "objections": objections,
                    })
                    adj = adj_out.get("output") or {}
                    if isinstance(adj, dict) and adj.get("human_review_required"):
                        self.counters["human_review_queue"] += 1
                        self.store.event("human_review", source_id=sid, issue=adj.get("issue"))
                        return {"state": "human_review", "source_id": sid, "adjudication": adj}
                # objections not material -> apply Granite corrections if any
                corrections = self._apply_corrections(extraction, objections)
                return self._store_extraction(sid, envelope, {"output": corrections}, route2)
            return self._store_extraction(sid, envelope, {"output": extraction}, route2)
        return self._store_extraction(sid, envelope, {"output": extraction}, route2)

    # -- persistence of validated extractions -----------------------------------
    def _store_extraction(self, sid, envelope, extraction_result, route):
        """Persist a validated primary-worker extraction as observations /
        analytical records, with provenance on every field (Master Pack §6, §8)."""
        extraction = extraction_result.get("output") if isinstance(extraction_result, dict) else None
        if not isinstance(extraction, dict) or extraction.get("_schema_errors"):
            self.counters["schema_validation_failures"] += 1
            self.store.event("schema_failure", source_id=sid)
            return {"state": "schema_failure", "source_id": sid}
        stored = {"observations": 0, "analytical": 0, "claims": 0}
        observed_at = envelope.get("retrieved_at") or utcnow_iso()
        for a in extraction.get("assertions", []):
            field = a.get("field")
            value = a.get("value")
            if field is None:
                continue
            # identity/observation fields -> append-only observations
            if field in ("identity", "business_role_claims", "supplier_claims", "addresses"):
                obs = {
                    "observation_id": ids.observation_id(sid, field, hashing.canonical_json(value), sid, observed_at),
                    "entity_id": "SUP-000",  # placeholder: entity binding happens at resolution
                    "entity_field": field,
                    "field": field,
                    "value": value,
                    "source_id": sid,
                    "observed_at": observed_at,
                    "confidence": a.get("confidence", "LOW"),
                    "status": a.get("status", "UNKNOWN"),
                }
                st, _ = self.store.put_observation(obs)
                if st == "appended":
                    stored["observations"] += 1
            elif field == "analytical":
                for dim, info in (value or {}).items() if isinstance(value, dict) else []:
                    pass  # analytical persisted via evidence-family records below
        # analytical records from janoshik-style envelopes
        content = envelope.get("content") or {}
        if content.get("dimensions"):
            family = ids.evidence_family_id(content.get("laboratory") or envelope["source_type"],
                                            content.get("report_id") or envelope["source_record_id"])
            anl_id = ids.analytical_record_id("SUP-000", content.get("compound") or "unknown", family)
            dims = {}
            for dim, info in (content.get("dimensions") or {}).items():
                dims[dim] = {
                    "tested": bool(info.get("tested")),
                    "result": (info.get("raw_results") or [None])[0],
                    "method": None,
                    "status": "UNVERIFIED" if info.get("tested") else "UNVERIFIED",
                }
            rec = {
                "analytical_record_id": anl_id,
                "supplier_id": "SUP-000",
                "submitter": content.get("submitter"),  # candidate-link key, not proof (§7.1)
                "compound": content.get("compound") or "unknown",
                "lot": content.get("lot"),
                "laboratory": content.get("laboratory") or "unknown",
                "report_id": content.get("report_id"),
                "evidence_family_id": family,
                "dimensions": dims,
                "provenance": "UNKNOWN",
                "sample_source": "unknown",
                "independence_status": "UNKNOWN",
                "source_id": sid,
                "adapter_version": envelope.get("supplier_adapter_version", envelope.get("adapter_version")),
            }
            st, _ = self.store.put_analytical(rec)
            stored["analytical"] += 1 if st == "appended" else 0
        self.store.event("stored", source_id=sid, route=route.get("route"), **stored)
        return {"state": "stored", "source_id": sid, **stored}

    def _needs_granite(self, envelope, det):
        """Policy: which deterministic signals force a Granite audit even when the
        primary worker did not set requires_validation."""
        content = envelope["content"]
        if envelope["source_type"] == "regulatory_source":
            return True
        if content.get("claims_language"):
            return True  # marketing-claim language present — skeptic must audit
        return False

    def _apply_corrections(self, extraction, objections):
        """Apply Granite's recommended corrections to assertion-level fields.

        Only demotions are allowed (e.g. VERIFIED -> UNVERIFIED); a validator can
        never promote an assertion or add new facts.
        """
        if not isinstance(objections, list):
            return extraction
        demote = {"VERIFIED": 1, "PARTIALLY_VERIFIED": 2, "OBSERVED": 3, "CLAIMED": 4, "UNKNOWN": 5}
        for ob in objections:
            if not isinstance(ob, dict):
                continue
            rec = ob.get("recommended_correction") or {}
            if not isinstance(rec, dict):
                continue
            idx = rec.get("assertion_index")
            new_status = rec.get("status")
            if idx is None or new_status not in demote:
                continue
            for a in extraction.get("assertions", []):
                if a.get("field") == rec.get("field") or True:
                    if a.get("status") in demote and demote[new_status] > demote.get(a.get("status"), 9):
                        a["status"] = new_status
                        a["notes"] = (a.get("notes", "") + " [granite_correction]").strip()
        return extraction

    def _call_tier(self, worker, model, packet, schema=None):
        prompt_file = {
            "qwen27b_extraction": "qwen27b_extraction.md",
            "granite30b_skeptic": "granite30b_skeptic.md",
            "qwen125b_adjudicator": "qwen125b_adjudicator.md",
            "qwen_vl_examiner": "qwen_vl_examiner.md",
            "glm_ocr_fallback": "glm_ocr_fallback.md",
            "dossier_synthesizer": "dossier_synthesizer.md",
        }[worker]
        system = _load_prompt(prompt_file)
        user = self._build_packet_brief(worker, packet)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        result = tiers.call_worker(worker, model, messages, schema=schema, metrics=self.metrics, label=packet.get("packet_id"))
        model_key = {
            "qwen27b_extraction": "qwen27b_calls",
            "granite30b_skeptic": "granite_escalations",
            "qwen125b_adjudicator": "qwen125b_escalations",
            "qwen_vl_examiner": "qwen_vl_calls",
            "glm_ocr_fallback": "ocr_fallbacks",
        }.get(worker)
        if model_key and result.get("schema_ok") is not None:
            pass  # counted at call sites to avoid double counting retries
        return result

    def _build_packet_brief(self, worker, packet):
        """Per Compact Runtime Prompts: worker receives ONLY its contract (system),
        the schema (already enforced), the minimum evidence packet, and candidates."""
        parts = []
        env = packet.get("envelope") or {}
        det = packet.get("deterministic") or {}
        parts.append("EVIDENCE PACKET %s" % packet.get("packet_id"))
        parts.append("source_type: %s | adapter: %s" % (env.get("source_type"), env.get("adapter_version")))
        if det:
            parts.append("deterministic_metadata: " + hashing.canonical_json(det))
        if packet.get("ocr_text") is not None:
            parts.append("ocr_text: " + packet["ocr_text"])
        if worker == "granite30b_skeptic":
            parts.append("extraction_to_audit: " + hashing.canonical_json(packet.get("extraction") or {}))
        if worker == "qwen125b_adjudicator":
            parts.append("extraction: " + hashing.canonical_json(packet.get("extraction") or {}))
            parts.append("objections: " + hashing.canonical_json(packet.get("objections") or []))
        content = env.get("content") or {}
        body = content.get("text") or hashing.canonical_json(content)
        parts.append("evidence_content: " + (body[:6000] if isinstance(body, str) else hashing.canonical_json(body)[:6000]))
        if packet.get("retry_hint"):
            parts.append("RETRY NOTE: " + packet["retry_hint"])
        return "\n".join(p for p in parts if p)
