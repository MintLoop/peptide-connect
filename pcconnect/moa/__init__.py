"""MoA layer: exception-resolution mechanism (contracts/MOA_CONTRACT.md).

The MoA is NOT the normal processing path. Normal path:
deterministic → Qwen 27B → schema validation. The panel (Resolver → Skeptic →
Adjudicator) opens only for material unresolved issues that remain after normal
validation, per the contract's escalation conditions.
"""
from .router import (
    classify_extraction, granite_decision, gate_125b, route_packet,
    ELIGIBLE_ISSUES, NON_ESCALATION_REASONS, MATERIAL_ISSUES,
)
from .panel import should_open_panel, run_panel, RESOLVER_MODEL, SKEPTIC_MODEL, ADJUDICATOR_MODEL

__all__ = [
    "classify_extraction", "granite_decision", "gate_125b", "route_packet",
    "ELIGIBLE_ISSUES", "NON_ESCALATION_REASONS", "MATERIAL_ISSUES",
    "should_open_panel", "run_panel",
    "RESOLVER_MODEL", "SKEPTIC_MODEL", "ADJUDICATOR_MODEL",
]
