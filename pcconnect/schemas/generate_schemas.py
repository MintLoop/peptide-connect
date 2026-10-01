#!/usr/bin/env python3
"""Schema generator for Peptide Connect V0.

Single source of truth for all canonical schemas. Emits JSON Schema (draft 2020-12)
files into pcconnect/schemas/. Generated files are committed so the pipeline does not
depend on running this script, but any enum change MUST be made here, not in the
generated JSON.

Conventions:
- evidence states: VERIFIED, LIKELY, POSSIBLE, UNVERIFIED, CONTRADICTED, UNRESOLVED,
  INSUFFICIENT_EVIDENCE  (Master Pack §3)
- extraction confidence: HIGH, MEDIUM, LOW only — never pseudo-calibrated floats
- provenance classes: Master Pack §9
- business roles: Master Pack §7.2
- identity resolution states: Master Pack §7.1
"""
import json
import os

# This script lives inside the schemas directory itself.
SCHEMA_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Canonical vocabularies (Master Pack §3, §7, §9)
# ---------------------------------------------------------------------------
EVIDENCE_STATES = [
    "VERIFIED", "LIKELY", "POSSIBLE", "UNVERIFIED",
    "CONTRADICTED", "UNRESOLVED", "INSUFFICIENT_EVIDENCE",
]
CONFIDENCE = ["HIGH", "MEDIUM", "LOW"]
SEVERITY = ["LOW", "MEDIUM", "HIGH"]
SOURCE_TYPES = [
    "janoshik", "finnrick", "peptidebenchmark", "supplier_site", "b2b_directory",
    "whatsapp_export", "telegram_export", "pdf_document", "image_document",
    "regulatory_source", "manual_evidence",
]
PROVENANCE_CLASSES = [
    "PC_CONTROLLED_PURCHASE", "INDEPENDENTLY_SOURCED", "COMMUNITY_SUBMITTED",
    "VENDOR_SUBMITTED", "VENDOR_COA", "AGGREGATOR_OBSERVED", "UNKNOWN",
]
BUSINESS_ROLES = [
    "MANUFACTURER", "CONTRACT_MANUFACTURER", "TRADING_COMPANY", "EXPORT_AGENT",
    "DISTRIBUTOR", "WHOLESALER", "RESELLER", "RESEARCH_SUPPLIER", "UNKNOWN",
]
RESOLUTION_STATES = [
    "VERIFIED_MATCH", "LIKELY_MATCH", "POSSIBLE_MATCH", "UNRESOLVED", "DIFFERENT_ENTITY",
]
ANALYTICAL_DIMENSIONS = [
    "identity", "purity", "quantity", "endotoxin", "sterility", "heavy_metals",
    "residual_solvents", "water_content", "counterion", "contamination_screening",
    "other",
]
CLAIM_STATUS = ["VERIFIED", "PARTIALLY_SUPPORTED", "UNVERIFIED", "CONTRADICTED"]

# Compact Runtime Prompts layering rule
VISUAL_MODALITIES = ["VISIBLE_TEXT", "VISUAL_OBSERVATION", "MODEL_INTERPRETATION"]

SHA_RE = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}


def prop(name, schema, required=False):
    return name, schema, required


def obj(props, required=None, extra=False, defs=None):
    d = {"type": "object", "additionalProperties": extra}
    if defs:
        d["$defs"] = defs
    d["properties"] = {n: s for n, s, _ in props}
    req = required if required is not None else [n for n, _, r in props if r]
    if req:
        d["required"] = req
    return d


def arr(items, extra=False):
    return {"type": "array", "items": items}


def enumstr(values):
    return {"type": "string", "enum": list(values)}


def dt():
    return {"type": "string", "format": "date-time"}


def nullable(x):
    out = dict(x)
    t = out.get("type")
    if isinstance(t, list):
        return out
    out["type"] = [t, "null"]
    return out


# ---------------------------------------------------------------------------
# envelope.schema.json  (Master Pack §4)
# ---------------------------------------------------------------------------
def build_envelope():
    attachment = obj([
        prop("filename", {"type": "string"}),
        prop("sha256", SHA_RE),
        prop("media_type", {"type": "string"}),
        prop("text_hash", nullable(SHA_RE)),
    ])
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "envelope.schema.json",
        "title": "Canonical Evidence Envelope",
        "description": "Emitted by every source adapter before any LLM sees the data. "
                       "The model layer never sees source-specific mechanics.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "source_type", "source_record_id", "retrieved_at", "raw_content_hash",
            "content", "adapter_version",
        ],
        "properties": {
            "source_type": enumstr(SOURCE_TYPES),
            "source_record_id": {"type": "string", "minLength": 1},
            "source_url": nullable({"type": "string"}),
            "retrieved_at": dt(),
            "raw_content_hash": SHA_RE,
            "content": {"type": "object"},
            "attachments": arr(attachment),
            "adapter_version": {"type": "string"},
        },
    }


# ---------------------------------------------------------------------------
# observation.schema.json  (Master Pack §6)
# ---------------------------------------------------------------------------
def build_observation():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "observation.schema.json",
        "title": "Append-Only Supplier Observation",
        "description": "Historical claims are never overwritten. A superseded observation "
                       "keeps its value and gains a superseded_by pointer.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "observation_id", "entity_id", "field", "value", "source_id", "observed_at",
        ],
        "properties": {
            "observation_id": {"type": "string", "pattern": "^OBS-[0-9]{8}$"},
            "entity_id": {"type": "string", "pattern": "^SUP-[0-9]{3}$|^ENT-[0-9]{3}$"},
            "field": {"type": "string", "minLength": 1},
            "value": {},
            "source_id": {"type": "string", "pattern": "^SRC-[0-9]{8}$"},
            "observed_at": dt(),
            "valid_from": nullable(dt()),
            "superseded_by": nullable({"type": "string", "pattern": "^OBS-[0-9]{8}$"}),
            "confidence": enumstr(CONFIDENCE),
            "notes": nullable({"type": "string"}),
        },
    }


# ---------------------------------------------------------------------------
# analytical.schema.json  (Master Pack §8)
# ---------------------------------------------------------------------------
def build_analytical():
    dimension = obj([
        prop("tested", {"type": "boolean"}),
        prop("result", nullable({"type": "string"})),
        prop("method", nullable({"type": "string"})),
        prop("status", enumstr(EVIDENCE_STATES)),
        prop("report_ref", nullable({"type": "string", "pattern": "^EV-[0-9]{8}$|^SRC-[0-9]{8}$"})),
    ], required=["tested", "status"])
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "analytical.schema.json",
        "title": "Analytical Evidence Record (compound- and lot-specific)",
        "description": "Never summarize 'supplier has sterility testing'. Every dimension "
                       "is tracked per compound/lot; untested dimensions are never inferred "
                       "as passed (tested=false, status stays UNVERIFIED).",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "analytical_record_id", "supplier_id", "compound", "laboratory",
            "evidence_family_id", "dimensions", "provenance", "sample_source",
            "independence_status", "source_id",
        ],
        "properties": {
            "analytical_record_id": {"type": "string", "pattern": "^ANL-[0-9]{8}$"},
            "supplier_id": {"type": "string", "pattern": "^SUP-[0-9]{3}$"},
            "compound": {"type": "string", "minLength": 1},
            "lot": nullable({"type": "string"}),
            "laboratory": {"type": "string"},
            "report_id": nullable({"type": "string"}),
            "evidence_family_id": {"type": "string", "pattern": "^EF-[0-9]{8}$"},
            "dimensions": {
                "type": "object",
                "propertyNames": {"enum": ANALYTICAL_DIMENSIONS},
                "additionalProperties": dimension,
            },
            "provenance": enumstr(PROVENANCE_CLASSES),
            "sample_source": enumstr(["vendor_submitted", "independent", "community", "pc_controlled", "unknown"]),
            "independence_status": enumstr(["INDEPENDENT", "NOT_INDEPENDENT", "UNKNOWN"]),
            "test_date": nullable(dt()),
            "report_url": nullable({"type": "string"}),
            "source_id": {"type": "string", "pattern": "^SRC-[0-9]{8}$"},
            "adapter_version": {"type": "string"},
        },
    }


# ---------------------------------------------------------------------------
# lineage.schema.json  (Master Pack §5)
# ---------------------------------------------------------------------------
def build_lineage():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "lineage.schema.json",
        "title": "Evidence Lineage Record",
        "description": "One analytical evidence family, not three confirmations: a supplier "
                       "page, an aggregator, and a directory all referencing the same "
                       "Janoshik report share an evidence_family_id.",
        "type": "object",
        "additionalProperties": False,
        "required": ["evidence_id", "source_id", "evidence_family_id", "recorded_at"],
        "properties": {
            "evidence_id": {"type": "string", "pattern": "^EV-[0-9]{8}$"},
            "source_id": {"type": "string", "pattern": "^SRC-[0-9]{8}$"},
            "upstream_source_id": nullable({"type": "string", "pattern": "^SRC-[0-9]{8}$"}),
            "evidence_family_id": {"type": "string", "pattern": "^EF-[0-9]{8}$"},
            "lineage_basis": nullable({"type": "string"}),
            "recorded_at": dt(),
        },
    }


# ---------------------------------------------------------------------------
# dossier.schema.json  (Master Pack §13)
# ---------------------------------------------------------------------------
def build_dossier():
    pv = obj([
        prop("value", {"type": "string", "minLength": 1}),
        prop("status", enumstr(EVIDENCE_STATES)),
        prop("source_id", {"type": "string"}),
        prop("observed_at", dt()),
        prop("confidence", enumstr(CONFIDENCE)),
    ], required=["value", "status", "source_id", "observed_at", "confidence"])

    coverage = obj([
        prop("reports", {"type": "integer", "minimum": 0}),
        prop("tested", {"type": "integer", "minimum": 0}),
        prop("coverage_ratio", {"type": "number", "minimum": 0, "maximum": 1}),
    ], required=["reports", "tested", "coverage_ratio"])

    compound_block = obj([
        prop("compound", {"type": "string"}),
        prop("report_count", {"type": "integer", "minimum": 0}),
        prop("unique_lots", {"type": "integer", "minimum": 0}),
        prop("coverage", {
            "type": "object",
            "propertyNames": {"enum": ANALYTICAL_DIMENSIONS},
            "additionalProperties": coverage,
        }),
    ], required=["compound", "report_count", "unique_lots", "coverage"])

    cert = obj([
        prop("claim", {"type": "string"}),
        prop("document_received", {"type": "boolean"}),
        prop("holder_name", nullable({"type": "string"})),
        prop("issuer", nullable({"type": "string"})),
        prop("certificate_id", nullable({"type": "string"})),
        prop("validity_period", nullable({"type": "string"})),
        prop("verification_status", enumstr(EVIDENCE_STATES)),
        prop("source_ids", arr({"type": "string"})),
    ], required=["claim", "document_received", "holder_name", "issuer", "verification_status"])

    claim_row = obj([
        prop("claim", {"type": "string"}),
        prop("status", enumstr(CLAIM_STATUS)),
        prop("evidence_ids", arr({"type": "string"})),
    ], required=["claim", "status", "evidence_ids"])

    conflict = obj([
        prop("subject", {"type": "string"}),
        prop("values", arr({"type": "string"})),
        prop("evidence_ids", arr({"type": "string"})),
        prop("status", enumstr(["UNRESOLVED", "CONTRADICTED"])),
        prop("resolution", nullable({"type": "string"})),
    ], required=["subject", "values", "evidence_ids", "status"])

    unknown = obj([
        prop("question", {"type": "string"}),
        prop("source_ids", arr({"type": "string"})),
    ], required=["question", "source_ids"])

    comm = obj([
        prop("channel", enumstr(["whatsapp", "telegram"])),
        prop("date", dt()),
        prop("question", {"type": "string"}),
        prop("answer", nullable({"type": "string"})),
        prop("source_id", {"type": "string"}),
    ], required=["channel", "date", "question", "source_id"])

    role = obj([
        prop("claimed_role", enumstr(BUSINESS_ROLES)),
        prop("observed_role", enumstr(BUSINESS_ROLES)),
        prop("role_status", enumstr(EVIDENCE_STATES)),
        prop("evidence", arr({"type": "string"})),
    ], required=["claimed_role", "observed_role", "role_status"])

    identity = obj([
        prop("canonical_name", {"type": "string", "minLength": 1}),
        prop("resolution_status", enumstr(RESOLUTION_STATES)),
        prop("resolution_evidence", arr({"type": "string"})),
        prop("legal_names", arr(pv)),
        prop("aliases", arr(pv)),
        prop("domains", arr(pv)),
        prop("emails", arr(pv)),
        prop("phones", arr(pv)),
        prop("whatsapp", arr(pv)),
        prop("telegram", arr(pv)),
        prop("addresses", arr(pv)),
        prop("marketplace_profiles", arr(pv)),
    ], required=["canonical_name", "resolution_status"])

    freshness = obj([
        prop("latest_supplier_observation", nullable(dt())),
        prop("latest_analytical_record", nullable(dt())),
        prop("latest_communication", nullable(dt())),
        prop("latest_regulatory_check", nullable(dt())),
        prop("latest_website_check", nullable(dt())),
    ], required=[
        "latest_supplier_observation", "latest_analytical_record",
        "latest_communication", "latest_regulatory_check", "latest_website_check",
    ])

    prov_counts = obj(
        [prop(p, {"type": "integer", "minimum": 0}) for p in PROVENANCE_CLASSES],
        required=list(PROVENANCE_CLASSES),
    )

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "dossier.schema.json",
        "title": "Canonical Supplier Dossier",
        "description": "Assembled from validated records only. Synthesis never introduces "
                       "new facts or resolves previously unresolved issues.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "dossier_id", "supplier_id", "generated_at", "identity", "business_role",
            "analytical_evidence", "provenance", "certifications", "claims_vs_evidence",
            "conflicts", "unknowns", "communications", "freshness",
        ],
        "properties": {
            "dossier_id": {"type": "string", "pattern": "^DSR-[0-9A-Z]{8}$"},
            "supplier_id": {"type": "string", "pattern": "^SUP-[0-9]{3}$"},
            "generated_at": dt(),
            "identity": identity,
            "business_role": role,
            "analytical_evidence": arr(compound_block),
            "provenance": prov_counts,
            "certifications": arr(cert),
            "claims_vs_evidence": arr(claim_row),
        },
        # conflicts / unknowns / communications / freshness / followup_questions
        # appended below (kept out of 'properties' dict literal for clarity)
    }


def main():
    os.makedirs(SCHEMA_DIR, exist_ok=True)
    # envelope / observation / analytical / lineage are complete as built
    schemas = {
        "envelope.schema.json": build_envelope(),
        "observation.schema.json": build_observation(),
        "analytical.schema.json": build_analytical(),
        "lineage.schema.json": build_lineage(),
    }
    dossier = build_dossier()
    # finish dossier: conflicts, unknowns, communications, freshness, followups
    dossier["properties"]["conflicts"] = arr({
        "type": "object",
        "additionalProperties": False,
        "required": ["subject", "values", "evidence_ids", "status"],
        "properties": {
            "subject": {"type": "string"},
            "values": {"type": "array", "items": {"type": "string"}},
            "evidence_ids": {"type": "array", "items": {"type": "string"}},
            "status": {"type": "string", "enum": ["UNRESOLVED", "CONTRADICTED"]},
            "resolution": {"type": ["string", "null"]},
        },
    })
    dossier["properties"]["unknowns"] = arr({
        "type": "object",
        "additionalProperties": False,
        "required": ["question", "source_ids"],
        "properties": {
            "question": {"type": "string"},
            "source_ids": {"type": "array", "items": {"type": "string"}},
        },
    })
    dossier["properties"]["communications"] = arr({
        "type": "object",
        "additionalProperties": False,
        "required": ["channel", "date", "question", "source_id"],
        "properties": {
            "channel": {"type": "string", "enum": ["whatsapp", "telegram"]},
            "date": {"type": "string", "format": "date-time"},
            "question": {"type": "string"},
            "answer": {"type": ["string", "null"]},
            "source_id": {"type": "string"},
        },
    })
    dossier["properties"]["freshness"] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "latest_supplier_observation", "latest_analytical_record",
            "latest_communication", "latest_regulatory_check", "latest_website_check",
        ],
        "properties": {
            "latest_supplier_observation": {"type": ["string", "null"], "format": "date-time"},
            "latest_analytical_record": {"type": ["string", "null"], "format": "date-time"},
            "latest_communication": {"type": ["string", "null"], "format": "date-time"},
            "latest_regulatory_check": {"type": ["string", "null"], "format": "date-time"},
            "latest_website_check": {"type": ["string", "null"], "format": "date-time"},
        },
    }
    dossier["properties"]["followup_questions"] = {"type": "array", "items": {"type": "string"}}
    schemas["dossier.schema.json"] = dossier

    for fname, schema in schemas.items():
        path = os.path.join(SCHEMA_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, sort_keys=False)
            f.write("\n")
        print("wrote %s" % path)


if __name__ == "__main__":
    main()
