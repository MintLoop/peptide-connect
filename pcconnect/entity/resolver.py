"""Entity resolution (Master Pack §7).

Two separate tasks, never conflated:
1. identity resolution — do identifiers refer to the same entity?
2. business-role classification — what is the entity's supply-chain role?

Deterministic blocking keys first (exact domain / phone / WhatsApp / Telegram /
email matches). BGE-M3 embeddings generate CANDIDATES only — embedding similarity
is never identity proof. Ambiguous merges are flagged, never executed.
"""
from .. import ids as idlib
from ..deterministic import normalize_telegram

# fields where an exact match is strong identity evidence
STRONG_KEYS = ["domain", "email", "whatsapp", "telegram", "phone", "marketplace_profile"]


def build_blocking_records(suppliers):
    """Invert the supplier table into key -> [supplier_id] maps for exact blocking."""
    blocks = {k: {} for k in STRONG_KEYS}
    for sup in suppliers:
        for key in STRONG_KEYS:
            values = sup.get(key) or []
            if isinstance(values, str):
                values = [values]
            for v in values:
                if v is None:
                    continue
                nv = _norm_key(key, v)
                if nv:
                    blocks[key].setdefault(nv, []).append(sup["supplier_id"])
    return blocks


def _norm_key(kind, value):
    v = str(value).strip().lower()
    if not v:
        return None
    if kind == "domain":
        return v[4:] if v.startswith("www.") else v
    if kind in ("whatsapp", "phone"):
        digits = re.sub(r"\D", "", v)
        return digits or None
    if kind == "telegram":
        return normalize_telegram(v)
    return v


import re  # noqa: E402 — used by _norm_key


def resolve_identity(observation, suppliers, blocks, embedding_candidates=None):
    """Resolve one observation against known suppliers.

    Returns a resolution dict:
      {state, matched_supplier_id, evidence, requires_validation}

    States: VERIFIED_MATCH / LIKELY_MATCH / POSSIBLE_MATCH / UNRESOLVED /
    DIFFERENT_ENTITY (Master Pack §7.1). Never silently merges ambiguous entities.
    """
    evidence = []
    matches = {}
    for key in STRONG_KEYS:
        values = observation.get(key) or []
        if isinstance(values, str):
            values = [values]
        for v in values:
            nv = _norm_key(key, v)
            if not nv:
                continue
            for sid in blocks.get(key, {}).get(nv, []):
                matches.setdefault(sid, []).append("exact_%s:%s" % (key, nv))

    if not matches and observation.get("name") and embedding_candidates:
        # candidates are CANDIDATE_EVIDENCE only — never identity proof
        for sid in embedding_candidates:
            matches.setdefault(sid, []).append("embedding_candidate:%s" % sid)

    if not matches:
        return {"state": "UNRESOLVED", "matched_supplier_id": None,
                "evidence": [], "requires_validation": False}

    if len(matches) == 1:
        sid, ev = next(iter(matches.items()))
        strong = [e for e in ev if e.startswith("exact_")]
        if strong:
            return {"state": "VERIFIED_MATCH", "matched_supplier_id": sid,
                    "evidence": strong, "requires_validation": False}
        return {"state": "POSSIBLE_MATCH", "matched_supplier_id": sid,
                "evidence": ev, "requires_validation": True}

    # multiple candidate entities — ambiguous, flag do not merge
    return {"state": "UNRESOLVED", "matched_supplier_id": None,
            "evidence": ["ambiguous:%s" % ",".join(sorted(matches))],
            "requires_validation": True,
            "candidates": sorted(matches)}


def new_supplier_from_observation(observation, source_id_str, observed_at, supplier_seq):
    """Mint a new canonical supplier from an unresolved observation."""
    sup = {
        "supplier_id": "SUP-%03d" % supplier_seq,
        "canonical_name": observation.get("name") or observation.get("canonical_name") or "UNKNOWN",
        "resolution_status": "UNRESOLVED",
        "domain": observation.get("domain") or [],
        "email": observation.get("email") or [],
        "phone": observation.get("phone") or [],
        "whatsapp": observation.get("whatsapp") or [],
        "telegram": observation.get("telegram") or [],
        "marketplace_profile": observation.get("marketplace_profile") or [],
        "created_from_source": source_id_str,
        "created_at": observed_at,
    }
    return sup
