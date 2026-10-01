"""Escalation Router (MoA contract, contracts/MOA_CONTRACT.md).

Deterministic code — never a model — decides escalation. Workers never escalate
themselves. The 125B gate requires ALL of: Granite HIGH-severity objection with
adjudication_required, a material-issue category, and dossier impact.
"""
from ..adapters.base import utcnow_iso

# Material issue categories eligible for MoA escalation (MoA contract §ESCALATION CONDITIONS)
ELIGIBLE_ISSUES = {
    "ambiguous_entity_identity",
    "alias_collision",
    "manufacturer_trader_dispute",
    "certificate_company_mismatch",
    "disputed_corporate_relationship",
    "lot_report_mismatch",
    "contradictory_analytical_evidence",
    "unclear_chain_of_custody",
    "source_disagreement_affecting_dossier",
    "duplicated_evidence_with_uncertain_lineage",
    "high_impact_claim_with_incomplete_support",
}

# Reasons that are NEVER sufficient to escalate on their own (MoA contract)
NON_ESCALATION_REASONS = [
    "extraction confidence is low",
    "missing fields",
    "supplier uses whatsapp",
    "promotional language",
    "evidence is sparse",
]

# Legacy category aliases (kept so existing callers keep working)
MATERIAL_ISSUES = ELIGIBLE_ISSUES

ROUTE_CLASSES = ("routine", "questionable", "hard", "visual")


def classify_extraction(extraction, envelope=None):
    """Route classification for a Primary Worker extraction (MoA §2).

    - routine: schema-valid, requires_validation=false
    - questionable: requires_validation=true (Granite audit)
    - visual: image evidence needing Qwen-VL first
    """
    if envelope is not None and envelope.get("source_type") == "image_document":
        return "visual"
    if not isinstance(extraction, dict):
        return "questionable"  # malformed output always gets the skeptic
    if extraction.get("_route_hint") == "visual":
        return "visual"
    if extraction.get("requires_validation") is True:
        return "questionable"
    return "routine"


def granite_decision(objections):
    """Interpret Granite's audit result.

    NO_MATERIAL_OBJECTION (or empty list) -> record stands.
    Otherwise each objection carries severity + adjudication_required.
    Returns (verdict, needs_adjudication, material_categories).
    """
    if objections is None:
        return "NO_MATERIAL_OBJECTION", False, []
    if isinstance(objections, str):
        if objections.strip().upper().startswith("NO_MATERIAL_OBJECTION"):
            return "NO_MATERIAL_OBJECTION", False, []
        return "OBJECTIONS", False, []
    if isinstance(objections, list) and not objections:
        return "NO_MATERIAL_OBJECTION", False, []
    needs_adj = False
    categories = []
    for ob in objections:
        if not isinstance(ob, dict):
            continue
        if str(ob.get("severity", "")).upper() == "HIGH" and ob.get("adjudication_required") is True:
            needs_adj = True
            cat = ob.get("material_issue_category")
            if cat:
                categories.append(cat)
    return "OBJECTIONS", needs_adj, categories


def gate_125b(granite_objections, issue_category, dossier_impact=True):
    """The 125B material-issue gate (MoA contract §3).

    ALL must hold:
      1. Granite HIGH-severity objection with adjudication_required=true
      2. the disputed issue is a material-issue category
      3. resolution would change the dossier
    A LOW-confidence worker return is NOT a trigger by itself.
    """
    verdict, needs_adj, categories = granite_decision(granite_objections)
    if verdict == "NO_MATERIAL_OBJECTION":
        return False, "no_material_objection"
    if not needs_adj:
        return False, "objections_not_material"
    cats = set(categories) | ({issue_category} if issue_category else set())
    if not cats & MATERIAL_ISSUES:
        return False, "category_not_material"
    if not dossier_impact:
        return False, "no_dossier_impact"
    return True, "material_issue"


def route_packet(packet):
    """Full routing decision for one evidence packet, Master Pack §12.

    Returns a route record: {route, steps, escalated, reason}.
    """
    extraction = packet.get("extraction")
    envelope = packet.get("envelope")
    route = classify_extraction(extraction, envelope=envelope)
    steps = ["adapter", "deterministic", "qwen27b"]
    record = {
        "packet_id": packet.get("packet_id"),
        "route": route,
        "steps": list(steps),
        "escalated": False,
        "reason": None,
        "at": utcnow_iso(),
    }
    if route == "routine":
        record["steps"].append("schema_validation")
        record["steps"].append("store")
        return record
    if route == "visual":
        record["steps"] = ["adapter", "deterministic", "qwen_vl", "qwen27b", "schema_validation", "store"]
        record["steps"].insert(3, "glm_ocr?")  # only if visual extraction inadequate
        return record
    # questionable
    record["steps"].append("granite30b")
    objections = packet.get("granite_objections")
    invoke, reason = gate_125b(objections, packet.get("issue_category"))
    if invoke:
        record["route"] = "hard"
        record["steps"].append("qwen125b")
        record["escalated"] = True
        record["reason"] = reason
        record["steps"].append("store_or_human_review")
    else:
        record["steps"].append("correct_or_store")
        record["reason"] = reason
    return record
