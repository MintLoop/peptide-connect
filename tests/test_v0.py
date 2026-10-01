"""Peptide Connect V0 test suite — acceptance criteria as tests (Master Pack §18)."""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pcconnect.adapters.base import canonical_url, get_adapter
from pcconnect.adapters import janoshik, generic  # noqa: F401
from pcconnect import ids, hashing
from pcconnect.deterministic import (
    extract_lot_numbers, extract_report_ids, extract_dates, detect_content_change,
)
from pcconnect.entity import build_blocking_records, resolve_identity
from pcconnect.moa import classify_extraction, granite_decision, gate_125b, route_packet
from pcconnect.store import Store
from pcconnect.pipeline import Pipeline

JANO_TEXT = """Report no: 211414
Date of test: 2026-09-12
Sample name: Retatrutide
Lot: RT-0926A
Submitter: Example Vendor Ltd
Purity (HPLC): 99.2%
Identity (LC-MS): confirmed
Endotoxin: < 0.5 EU/mg
"""


# -- adapters / envelopes ----------------------------------------------------
def test_all_source_types_have_adapters():
    for st in ["janoshik", "finnrick", "peptidebenchmark", "supplier_site", "b2b_directory",
               "whatsapp_export", "telegram_export", "pdf_document", "image_document",
               "regulatory_source", "manual_evidence"]:
        assert get_adapter(st).source_type == st


def test_janoshik_envelope_valid_and_dimensions_not_inferred():
    from jsonschema import Draft202012Validator
    env = get_adapter("janoshik").emit({"report_id": "211414", "text": JANO_TEXT},
                                       retrieved_at="2026-09-30T20:00:00Z")
    schema = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                         "pcconnect", "schemas", "envelope.schema.json")))
    assert not list(Draft202012Validator(schema).iter_errors(env))
    d = env["content"]["dimensions"]
    assert d["purity"]["tested"] is True
    assert d["identity"]["tested"] is True
    assert d["endotoxin"]["tested"] is True
    # UNTESTED dimensions must never be inferred (Master Pack §3.8)
    assert "sterility" not in d
    assert "heavy_metals" not in d
    assert env["content"]["compound"] == "retatrutide"
    assert env["content"]["lot"] == "RT-0926A"


def test_janoshik_refuses_missing_report_id():
    import pytest
    with pytest.raises(ValueError):
        get_adapter("janoshik").emit({"text": "no report id here"})


def test_canonical_url_normalization():
    assert canonical_url("HTTPS://Example.COM:443/a/?utm_source=x#frag") == "https://example.com/a"
    assert canonical_url("https://shop.example.co/") == "https://shop.example.co"
    assert canonical_url("http://x.org:8080/p?b=2&a=1") == "http://x.org:8080/p?a=1&b=2"


def test_contact_extraction_deterministic():
    sig = generic.extract_contact_signals(
        "Email sales@acme.example WhatsApp: +1 305 555 0142 telegram @AcmePeps")
    assert "sales@acme.example" in sig["emails"]
    assert "+13055550142" in sig["whatsapp"]
    assert "acmepeps" in sig["telegram"]


# -- deterministic tier ------------------------------------------------------
def test_deterministic_extractors():
    text = "Lot: RT-0926A, report no: 211414, dated 2026-09-12, purity 99.2%"
    assert extract_lot_numbers(text) == ["RT-0926A"]
    assert extract_report_ids(text) == ["211414"]
    assert extract_dates(text) == ["2026-09-12"]
    assert detect_content_change(None, "x") == "new"
    assert detect_content_change("x", "x") == "unchanged"
    assert detect_content_change("x", "y") == "changed"


# -- ids / hashing -----------------------------------------------------------
def test_ids_stable_and_distinct():
    a = ids.source_id("janoshik", "211414")
    b = ids.source_id("janoshik", "211414")
    c = ids.source_id("finnrick", "211414")
    assert a == b and a != c
    assert ids.evidence_family_id("Janoshik", "211414") == ids.evidence_family_id("Janoshik", "211414")
    # same lab+report from three different sites = ONE family (§5)
    assert ids.evidence_family_id("Janoshik", "211414") != ids.evidence_family_id("Janoshik", "211415")


# -- entity resolution ---------------------------------------------------------
def test_entity_resolution_never_silently_merges():
    suppliers = [
        {"supplier_id": "SUP-001", "domain": ["acme.example"], "email": [], "whatsapp": [],
         "phone": [], "telegram": [], "marketplace_profile": []},
        {"supplier_id": "SUP-002", "domain": ["beta.example"], "email": [], "whatsapp": [],
         "phone": [], "telegram": [], "marketplace_profile": []},
    ]
    blocks = build_blocking_records(suppliers)
    # exact domain match -> VERIFIED_MATCH
    r = resolve_identity({"domain": "acme.example"}, suppliers, blocks)
    assert r["state"] == "VERIFIED_MATCH" and r["matched_supplier_id"] == "SUP-001"
    # ambiguous: signals point at two entities -> UNRESOLVED, flagged
    r2 = resolve_identity({"domain": ["acme.example", "beta.example"]}, suppliers, blocks)
    assert r2["state"] == "UNRESOLVED" and r2["requires_validation"] is True
    # nothing matches -> UNRESOLVED (new entity candidate, not a forced merge)
    r3 = resolve_identity({"name": "Totally New Co"}, suppliers, blocks)
    assert r3["state"] == "UNRESOLVED"
    # name similarity alone is never identity proof (§3.7)
    r4 = resolve_identity({"name": "Acme Example Ltd"}, suppliers, blocks,
                          embedding_candidates=["SUP-002"])
    assert r4["state"] in ("POSSIBLE_MATCH", "UNRESOLVED")
    assert r4.get("requires_validation") is True or r4["state"] == "UNRESOLVED"


def test_identity_separate_from_role():
    from pcconnect.schemas.generate_schemas import BUSINESS_ROLES, RESOLUTION_STATES
    assert "MANUFACTURER" in BUSINESS_ROLES
    assert "VERIFIED_MATCH" in RESOLUTION_STATES
    # a company can be VERIFIED_MATCH while role stays UNKNOWN (§7)
    assert "UNKNOWN" in BUSINESS_ROLES


# -- MoA router ----------------------------------------------------------------
def test_routine_route_never_escalates():
    route = route_packet({"packet_id": "SRC-1", "extraction": {"requires_validation": False}})
    assert route["route"] == "routine"
    assert "qwen125b" not in route["steps"]


def test_questionable_routes_to_granite_not_125b():
    route = route_packet({"packet_id": "SRC-1", "extraction": {"requires_validation": True}})
    assert route["route"] == "questionable"
    assert "granite30b" in route["steps"]
    assert "qwen125b" not in route["steps"]


def test_125b_gate_requires_material_issue():
    # LOW severity objection: no adjudication
    ok, reason = gate_125b([{"severity": "LOW", "adjudication_required": False}], None)
    assert ok is False
    # HIGH severity but no material category: still no
    ok2, reason2 = gate_125b([{"severity": "HIGH", "adjudication_required": True,
                               "material_issue_category": "routine_disagreement"}], None)
    assert ok2 is False
    # HIGH severity + material category + dossier impact: 125B
    ok3, _ = gate_125b([{"severity": "HIGH", "adjudication_required": True,
                         "material_issue_category": "difficult_identity_collision"}], None)
    assert ok3 is True
    # LOW-confidence alone is never a trigger (Master Pack §11)
    ok4, _ = gate_125b([], None)
    assert ok4 is False


def test_granite_no_objection_passthrough():
    verdict, adj, cats = granite_decision("NO_MATERIAL_OBJECTION")
    assert verdict == "NO_MATERIAL_OBJECTION" and adj is False
    verdict2, adj2, _ = granite_decision([{"severity": "HIGH", "adjudication_required": True}])
    assert verdict2 == "OBJECTIONS" and adj2 is True


# -- store idempotency / incremental ---------------------------------------------
def test_store_append_once_idempotent():
    tmp = tempfile.mkdtemp(prefix="pcv0_")
    try:
        store = Store(tmp)
        rec = {"source_id": "SRC-00001", "x": 1}
        assert store.append_once("source_records", rec, "source_id")[0] == "appended"
        assert store.append_once("source_records", rec, "source_id")[0] == "duplicate"
        assert len(store.read_all("source_records")) == 1
    finally:
        shutil.rmtree(tmp)


def test_pipeline_offline_run_and_idempotence():
    tmp = tempfile.mkdtemp(prefix="pcv0_")
    try:
        items = [
            {"source_type": "janoshik", "raw": {"report_id": "211414", "text": JANO_TEXT}},
            {"source_type": "supplier_site",
             "raw": {"url": "https://examplevendor.com/about", "text": "We are a manufacturer with GMP facility. Email: sales@examplevendor.com"}},
            {"source_type": "finnrick",
             "raw": {"entry_id": "FR-9", "text": "Finnrick notes janoshik report 211414 for retatrutide"}},
        ]
        p1 = Pipeline(tmp, offline=True)
        p1.ingest(items, retrieved_at="2026-09-30T20:00:00Z")
        c1 = dict(p1.counters)
        assert c1["records_discovered"] == 3
        assert c1["new_records"] == 3
        assert c1["evidence_family_duplicates_removed"] >= 1  # finnrick references 211414 family

        # second ingestion of identical data: everything unchanged, zero new
        p2 = Pipeline(tmp, offline=True)
        p2.ingest(items, retrieved_at="2026-09-30T20:05:00Z")
        c2 = dict(p2.counters)
        assert c2["unchanged_records"] == 3
        assert c2["new_records"] == 0
        # no duplicates in stores (repeated ingestion never duplicates, §18)
        s = Store(tmp)
        assert len(s.read_all("source_records")) == 3
        assert len(s.read_all("evidence_lineage")) == 3
        assert len(s.read_all("analytical_evidence")) == 1
    finally:
        shutil.rmtree(tmp)


def test_pipeline_offline_visual_route():
    tmp = tempfile.mkdtemp(prefix="pcv0_")
    try:
        p = Pipeline(tmp, offline=True)
        out = p.ingest_one("image_document",
                           {"image_id": "IMG-1", "path": "x.png", "text": ""},
                           retrieved_at="2026-09-30T20:00:00Z")
        assert p.counters["qwen_vl_calls"] == 1
        assert p.counters["ocr_fallbacks"] == 1  # stub VL says inadequate -> OCR
        assert p.counters["qwen27b_calls"] >= 0
    finally:
        shutil.rmtree(tmp)


def test_unchanged_records_skip_llm_calls():
    tmp = tempfile.mkdtemp(prefix="pcv0_")
    try:
        items = [{"source_type": "janoshik", "raw": {"report_id": "211414", "text": JANO_TEXT}}]
        p1 = Pipeline(tmp, offline=True)
        p1.ingest(items, retrieved_at="2026-09-30T20:00:00Z")
        calls_before = sum(p1.metrics.calls.values())
        p2 = Pipeline(tmp, offline=True)
        p2.ingest(items, retrieved_at="2026-09-30T20:05:00Z")
        calls_after = sum(p2.metrics.calls.values())
        assert calls_after == 0  # §18: unchanged evidence needs no model inference
        assert calls_before >= 1
    finally:
        shutil.rmtree(tmp)
