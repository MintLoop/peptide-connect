"""Deterministic ID minting. IDs derive from content — stable across runs — but
the STORE allocates them with collision probing (same natural key always reuses
its allocated id; hash collisions probe forward), so repeated ingestion never
duplicates evidence (Master Pack §18).

ID spaces are 8 digits wide: at 500 records the birthday-collision expectation
in a 5-digit space is ~1.4 (observed: 3 lost records in the first V0 run);
8 digits drops it to ~6e-4, and probing makes it exactly zero.
"""
import hashlib


def _h(*parts):
    """Stable hex digest of the joined parts."""
    basis = "\u241f".join(str(p) for p in parts)
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def _fmt(prefix, x):
    return "%s-%08d" % (prefix, x)


def source_id(source_type, source_record_id):
    """SRC-XXXXXXXX — base id for (source_type, source_record_id)."""
    return _fmt("SRC", int(_h(source_type, source_record_id)[:12], 16) % 100000000)


def evidence_id(source_id_str):
    """EV-XXXXXXXX — one per source record's normalized evidence."""
    return _fmt("EV", int(_h("EV", source_id_str)[:12], 16) % 100000000)


def evidence_family_id(laboratory, report_ref):
    """EF-XXXXXXXX — syndication family: same (lab, report) = same family,
    regardless of how many webpages reference it (Master Pack §5)."""
    return _fmt("EF", int(_h("EF", laboratory, report_ref)[:12], 16) % 100000000)


def observation_id(entity_id, field, value, source_id_str, observed_at):
    """OBS-XXXXXXXX — append-only observation identity."""
    return _fmt("OBS", int(_h("OBS", entity_id, field, value, source_id_str, observed_at)[:12], 16) % 100000000)


def analytical_record_id(supplier_id, compound, report_ref):
    """ANL-XXXXXXXX — one analytical record per (supplier, compound, report)."""
    return _fmt("ANL", int(_h("ANL", supplier_id, compound, report_ref)[:12], 16) % 100000000)


def dossier_id(supplier_id, generated_at):
    return "DSR-%s" % _h(supplier_id, generated_at)[:8].upper()
