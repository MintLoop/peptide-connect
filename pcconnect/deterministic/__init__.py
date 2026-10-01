"""Deterministic tier (Master Pack §10).

Everything here is pure code — no LLM. The pipeline runs this BEFORE any model
call so models never perform work code can do reliably.
"""
import re

from ..adapters.generic import extract_contact_signals, normalize_phone

__all__ = [
    "extract_contact_signals", "normalize_phone", "normalize_telegram",
    "extract_lot_numbers", "extract_report_ids", "extract_certificate_ids",
    "extract_dates", "extract_purity_values", "detect_content_change",
]


def normalize_telegram(handle):
    """Canonical Telegram handle: lowercase, @-stripped."""
    if not handle:
        return None
    h = handle.strip()
    if h.startswith("@"):
        h = h[1:]
    return h.lower() or None


LOT_RE = re.compile(r"\b(?:lot|batch)(?:\s+(?:no|number|id))?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-]{2,15})\b", re.IGNORECASE)
REPORT_RE = re.compile(r"\b(?:report|test)(?:\s+(?:no|number|id))?\s*[:#]?\s*([0-9]{4,8})\b", re.IGNORECASE)
CERT_RE = re.compile(r"\b(?:certificate|cert)\s+(?:no|number|id)\s*[:#]?\s*([A-Z0-9][A-Z0-9\-]{2,20})\b", re.IGNORECASE)
DATE_RE = re.compile(r"\b(20[0-9]{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01]))\b")
PURITY_RE = re.compile(r"\b(\d{1,2}\.\d)\s*%?\s*(?:purity|pure|HPLC)?", re.IGNORECASE)


def extract_lot_numbers(text):
    return sorted(set(m.group(1).upper() for m in LOT_RE.finditer(text or "")))


def extract_report_ids(text):
    return sorted(set(m.group(1) for m in REPORT_RE.finditer(text or "")))


def extract_certificate_ids(text):
    return sorted(set(m.group(1) for m in REG_EXPR.finditer(text or "")))


def extract_dates(text):
    return sorted(set(m.group(1) for m in DATE_RE.finditer(text or "")))


def extract_purity_values(text):
    return sorted(set(m.group(1) for m in PURITY_RE.finditer(text or "")))


def detect_content_change(old_hash, new_hash):
    """§14: unchanged content skips deep extraction and all LLM calls."""
    if not old_hash:
        return "new"
    if old_hash == new_hash:
        return "unchanged"
    return "changed"


# patch the typo-safe name
REG_EXPR = CERT_RE
