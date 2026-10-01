"""MoA panel orchestration (contracts/MOA_CONTRACT.md — the verbatim contract).

The MoA is an exception-resolution mechanism, NOT the normal processing path.
Normal path first: deterministic → Qwen 27B → schema validation. Only when a
material unresolved issue REMAINS after normal validation does the Escalation
Router open the panel: Resolver (qwen27b) → Skeptic (granite) → Adjudicator (125B).

The panel must NOT vote. Agreement between models is not evidence. Original
source material is evidence.
"""
from ..adapters.base import utcnow_iso
from .router import ELIGIBLE_ISSUES, NON_ESCALATION_REASONS

# Models (MoA contract §PANEL)
RESOLVER_MODEL = "qwen3.8:27b-mlx-menta-64k"
SKEPTIC_MODEL = "granite4.2:30b"
ADJUDICATOR_MODEL = "qwen3.8-flash-next:125b-mlx"

DECISION_CLASSES = ["VERIFIED", "LIKELY", "POSSIBLE", "UNVERIFIED",
                    "CONTRADICTED", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"]
CONFIDENCE = ["HIGH", "MEDIUM", "LOW"]


def should_open_panel(extraction, granite_result, issue):
    """MoA contract §ESCALATION CONDITIONS.

    Invoke the full MoA only when a material unresolved issue remains after
    normal validation (deterministic → Qwen 27B → schema validation → Granite).

    Returns (open: bool, reason: str).
    """
    # 1. A material unresolved issue must exist
    if not issue or issue.get("category") not in ELIGIBLE_ISSUES:
        return False, "no_eligible_material_issue"
    # 2. Normal validation must have run first (Granite audit present)
    if granite_result is None:
        return False, "normal_validation_not_attempted"
    verdict = granite_result.get("verdict") if isinstance(granite_result, dict) else None
    if verdict == "NO_MATERIAL_OBJECTION":
        # Granite found nothing material — no unresolved issue REMAINS
        return False, "no_unresolved_issue_after_validation"
    # 3. Do-NOT-escalate list: these are never sufficient on their own
    reason = (issue.get("escalation_reason") or "").lower()
    for banned in NON_ESCALATION_REASONS:
        if banned and banned in reason:
            return False, "non_escalation_reason:%s" % banned
    return True, "material_issue_remains_after_validation"


def run_panel(call_tier, packet, issue):
    """Run the three-model panel. `call_tier` is Pipeline._call_tier.

    Returns the adjudication record (adjudication.schema.json-shaped) or an
    error marker. The panel does NOT vote — the Adjudicator alone decides,
    reading original evidence + deterministic metadata + Resolver + Skeptic.
    """
    # Resolver: strongest interpretation supported by the evidence
    resolver_out = call_tier("moa_resolver", RESOLVER_MODEL, dict(packet, issue=issue))
    resolver = resolver_out.get("output")

    # Skeptic: attempt to falsify or narrow the Resolver's interpretation
    skeptic_packet = dict(packet, issue=issue, resolver_analysis=resolver)
    skeptic_out = call_tier("granite30b_skeptic", SKEPTIC_MODEL, skeptic_packet)
    skeptic = skeptic_out.get("output")

    # Adjudicator: narrowest defensible conclusion (reads everything)
    adj_packet = dict(packet, issue=issue, resolver_analysis=resolver, skeptic_analysis=skeptic)
    adj_out = call_tier("qwen125b_adjudicator", ADJUDICATOR_MODEL, adj_packet)
    adjudication = adj_out.get("output")

    return {
        "panel_id": "MOA-%s" % (packet.get("packet_id") or "?"),
        "opened_at": utcnow_iso(),
        "issue": issue,
        "resolver": resolver,
        "skeptic": skeptic,
        "adjudication": adjudication,
    }
