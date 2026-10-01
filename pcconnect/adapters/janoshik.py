"""Janoshik public analytical report adapter (reference adapter, Master Pack §4).

Parses the deterministic fields of a Janoshik-style public test record:
- report number, test date, lab (Janoshik), submitter, sample name
- per-dimension results (identity, purity, quantity, endotoxin, sterility, ...)
- declared sample source / payment attribution when present

The adapter NEVER infers: untested dimensions stay tested=false; independence
is UNKNOWN unless the record itself declares who submitted/paid.
"""
import re

from .base import SourceAdapter, register_adapter

# Compound token normalization (deterministic, no LLM): common market aliases
# mapped to a canonical lowercase token. Deliberately small — unknown tokens
# pass through as-is rather than being guessed (no fabricated normalization).
COMPOUND_ALIASES = {
    "retatrutide": "retatrutide",
    "rt-": "retatrutide",  # guarded by prefix rule below
    "semaglutide": "semaglutide",
    "tirzepatide": "tirzepatide",
    "tesamorelin": "tesamorelin",
    "bpc-157": "bpc-157",
    "bpc157": "bpc-157",
    "tb-500": "tb-500",
    "tb500": "tb-500",
    "cjc-1295": "cjc-1295",
    "ipamorelin": "ipamorelin",
    "mt-ii": "melanotan-ii",
    "melanotan 2": "melanotan-ii",
}

# Analytical dimension extraction: (schema dimension, regex on result lines)
DIMENSION_PATTERNS = [
    ("identity", r"(?:identity|identification|ms|lc-ms)\b"),
    ("purity", r"(?:purity|hplc|chromatographic purity)\b"),
    ("quantity", r"(?:quantity|content|amount|fill(?:ed)? (?:mass|weight))\b"),
    ("endotoxin", r"endotoxin\b"),
    ("sterility", r"sterility\b"),
    ("heavy_metals", r"(?:heavy metals|lead|arsenic|cadmium|mercury|elemental)\b"),
    ("residual_solvents", r"(?:residual solvents|gc(?:-[fm]s)?)\b"),
    ("water_content", r"(?:water content|moisture|karl fischer|kf)\b"),
    ("counterion", r"(?:counterion|counter-ion|acetate|trifluoroacetate|tfa salt)\b"),
    ("contamination_screening", r"(?:contamination|bioburden|particulate)\b"),
]


@register_adapter
class JanoshikAdapter(SourceAdapter):
    source_type = "janoshik"
    adapter_version = "janoshik_v0.1"

    def parse(self, raw):
        raw = raw if isinstance(raw, dict) else {"text": str(raw)}
        text = raw.get("text", "")
        content = {
            "laboratory": "Janoshik",
            "report_id": self._first(text, r"report(?:\s+(?:no|number|id))?\s*[:#]?\s*([0-9]{5,8})",
                                    raw.get("report_id")),
            "test_date": self._first(text, r"(?:date(?:d)?(?:\s+of)?\s+(?:test|analysis|report)|tested)\s*[:#]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", raw.get("test_date")),
            "submitter": self._first(text, r"(?:submitter|submit(?:ted)?\s+by)\s*[:#]?\s*(.+?)(?:\n|$)", raw.get("submitter")),
            "paid_by": self._first(text, r"paid\s+by\s*[:#]?\s*(.+?)(?:\n|$)", raw.get("paid_by")),
            "compound": self._compound(text, raw.get("compound")),
            "lot": self._first(text, r"(?:lot|batch)(?:\s+(?:no|number|id))?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-]{2,})", raw.get("lot")),
            "dimensions": self._dimensions(text, raw.get("dimensions")),
            "sample_source": raw.get("sample_source", "unknown"),
            "notes": raw.get("notes"),
        }
        content = {k: v for k, v in content.items() if v is not None}
        return content

    def record_id(self, raw):
        raw = raw if isinstance(raw, dict) else {"text": str(raw)}
        rid = raw.get("report_id") or self._first(raw.get("text", ""), r"report(?:\s+(?:no|number|id))?\s*[:#]?\s*([0-9]{5,8})")
        if not rid:
            raise ValueError("janoshik record without report id — refusing to fabricate one")
        return rid

    def source_url(self, raw):
        raw = raw if isinstance(raw, dict) else {"text": str(raw)}
        url = raw.get("source_url")
        return canonical_url_str(url) if url else None

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _first(text, pattern, default=None):
        if not text:
            return default
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else default

    @staticmethod
    def _compound(text, default=None):
        if default:
            return COMPOUND_ALIASES.get(default.lower().strip(), default.lower().strip())
        for line in (text or "").splitlines():
            low = line.lower()
            m = re.search(r"sample(?:\s+name)?\s*[:#]\s*(.+)", low)
            if m:
                token = m.group(1).strip()
                return COMPOUND_ALIASES.get(token, token)
            for alias, canon in COMPOUND_ALIASES.items():
                if alias.endswith("-"):  # prefix rule
                    if re.search(r"\b" + re.escape(alias) + r"[0-9]", low):
                        return canon
                elif re.search(r"\b" + re.escape(alias) + r"\b", low):
                    return canon
        return None

    @staticmethod
    def _dimensions(text, default=None):
        """Extract per-dimension tested flags + raw result strings.

        Tested means a line mentions the dimension. Untested dimensions are
        absent (never inferred). Results are raw text — the LLM tier interprets
        them later; the adapter only marks presence.
        """
        dims = {}
        lines = (text or "").splitlines()
        for dim, pattern in DIMENSION_PATTERNS:
            pat = re.compile(pattern, re.IGNORECASE)
            hit_lines = [ln.strip() for ln in lines if pat.search(ln)]
            if hit_lines:
                dims[dim] = {"tested": True, "raw_results": hit_lines[:4]}
        if not dims and isinstance(default, dict):
            for k, v in default.items():
                dims[k] = {"tested": bool(v), "raw_results": []} if not isinstance(v, dict) else v
        return dims


def canonical_url_str(url):
    from .base import canonical_url
    return canonical_url(url)
