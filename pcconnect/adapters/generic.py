"""Generic source adapters (Master Pack §4). Each emits the canonical envelope.

Deterministic-first: every adapter extracts what code can extract (URLs, emails,
phones, WhatsApp numbers, Telegram handles, dates, report IDs — §10) and leaves
free-text interpretation to the tiered model layer via `llm_fields`.
"""
import re

from .base import SourceAdapter, register_adapter, canonical_url

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.\-]?)?(?:\(\d{2,4}\)[\s.\-]?)?\d{3,4}[\s.\-]?\d{3,4}(?:[\s.\-]?\d{2,4})?")
WA_RE = re.compile(r"(?:whatsapp|wa)\s*[:#]?\s*(\+?\d[\d\s.\-]{7,16}\d)", re.IGNORECASE)
TG_RE = re.compile(r"(?:telegram|tg)\s*[:#]?\s*@?([A-Za-z][A-Za-z0-9_]{4,31})", re.IGNORECASE)
TG_AT_RE = re.compile(r"(?<![\w@])@([A-Za-z][A-Za-z0-9_]{4,31})\b")
DOMAIN_RE = re.compile(r"\b((?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+(?:com|net|org|io|shop|co|is|to|tech|dev|app|pharmacy|example|test|invalid|localhost))\b", re.IGNORECASE)


def extract_contact_signals(text):
    """Deterministic contact extraction (§10) — identical across adapters."""
    signals = {"emails": [], "phones": [], "whatsapp": [], "telegram": [], "domains": []}
    if not text:
        return signals
    signals["emails"] = sorted(set(EMAIL_RE.findall(text)))
    signals["phones"] = sorted(set(p.strip() for p in PHONE_RE.findall(text) if 7 <= len(re.sub(r"\D", "", p)) <= 15))
    for m in WA_RE.finditer(text):
        num = re.sub(r"[^\d+]", "", m.group(1))
        if 8 <= len(num.lstrip("+")) <= 15:
            signals["whatsapp"].append(num)
    seen_tg = set()
    for m in TG_RE.finditer(text):
        h = m.group(1).lower()  # telegram handles are case-insensitive identities
        if h not in seen_tg:
            seen_tg.add(h)
            signals["telegram"].append(h)
    for m in TG_AT_RE.finditer(text):
        h = m.group(1).lower()
        if h not in seen_tg:
            seen_tg.add(h)
            signals["telegram"].append(h)
    signals["whatsapp"] = sorted(set(signals["whatsapp"]))
    signals["telegram"] = sorted(set(signals["telegram"]))
    for m in DOMAIN_RE.finditer(text):
        d = m.group(1).lower()
        if d not in signals["emails"] and not any(d.endswith(e.split("@")[-1]) and len(d) == len(e.split("@")[-1]) for e in signals["emails"]):
            signals["domains"].append(d)
    signals["domains"] = sorted(set(signals["domains"]))
    return signals


def normalize_phone(raw):
    """E.164-ish normalization without guessing country (no fabricated digits)."""
    if not raw:
        return None
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("+"):
        return digits
    if len(digits) <= 15:
        return digits if digits.startswith("0") is False else digits  # keep as-is; country unknown
    return digits[:15]


class TextEnvelopeAdapter(SourceAdapter):
    """Shared machinery for text-bearing sources: deterministic contact extraction,
    change-hashable content, and an explicit `llm_fields` list telling the tier
    layer which fields require model extraction (and nothing more)."""

    def parse(self, raw):
        text = raw.get("text", "")
        content = {
            "title": raw.get("title"),
            "text": text,
            "contact_signals": extract_contact_signals(text),
            "claims_language": self._claims(text),
        }
        content = {k: v for k, v in content.items() if v is not None}
        content["llm_fields"] = self.llm_fields()
        return content

    def llm_fields(self):
        return ["identity", "business_role_claims", "supplier_claims", "addresses"]

    def _claims(self, text):
        """Deterministic claim-language flags: marketing vocabulary present in text.
        These are CLAIMS, never facts (Master Pack §3.1)."""
        if not text:
            return []
        flags = []
        for label, pat in [
            ("manufacturer_claim", r"\bmanufacturer\b"),
            ("gmp_claim", r"\bGMP\b"),
            ("third_party_tested_claim", r"\bthird[\s-]party tested\b"),
            ("purity_claim", r"\b\d{1,2}\.\d%\s*(?:purity|pure)?\b"),
            ("every_batch_tested_claim", r"\bevery batch tested\b"),
            ("us_warehouse_claim", r"\bUS warehouse\b"),
            ("direct_claim", r"\bdirect(?:ly)? from (?:the )?manufacturer\b"),
        ]:
            if re.search(pat, text, re.IGNORECASE):
                flags.append(label)
        return flags


@register_adapter
class SupplierSiteAdapter(TextEnvelopeAdapter):
    source_type = "supplier_site"
    adapter_version = "supplier_site_v0.1"

    def record_id(self, raw):
        url = canonical_url(raw.get("url") or "")
        if not url:
            raise ValueError("supplier_site record without url")
        return url

    def source_url(self, raw):
        return canonical_url(raw.get("url") or "")

    def parse(self, raw):
        content = super(SupplierSiteAdapter, self).parse(raw)
        # domain is derived from the URL when present (stronger than text scan)
        content["domain"] = _domain_of(raw.get("url")) or (content.get("contact_signals", {}).get("domains") or [None])[0]
        return content


def _domain_of(url):
    if not url:
        return None
    m = re.match(r"[a-z]+://([^/:?#]+)", url.strip().lower())
    if not m:
        return None
    host = m.group(1)
    host = host[4:] if host.startswith("www.") else host
    return host


@register_adapter
class B2BDirectoryAdapter(TextEnvelopeAdapter):
    source_type = "b2b_directory"
    adapter_version = "b2b_directory_v0.1"

    def record_id(self, raw):
        key = raw.get("listing_id") or raw.get("url") or raw.get("title")
        if not key:
            raise ValueError("b2b_directory record without listing_id/url/title")
        return str(key)

    def source_url(self, raw):
        return canonical_url(raw.get("url")) if raw.get("url") else None


@register_adapter
class FinnrickAdapter(TextEnvelopeAdapter):
    source_type = "finnrick"
    adapter_version = "finnrick_v0.1"

    def record_id(self, raw):
        key = raw.get("entry_id") or raw.get("url") or raw.get("title")
        if not key:
            raise ValueError("finnrick record without entry_id/url/title")
        return str(key)

    def source_url(self, raw):
        return canonical_url(raw.get("url")) if raw.get("url") else None


@register_adapter
class PeptideBenchmarkAdapter(TextEnvelopeAdapter):
    source_type = "peptidebenchmark"
    adapter_version = "peptidebenchmark_v0.1"

    def record_id(self, raw):
        key = raw.get("entry_id") or raw.get("url") or raw.get("title")
        if key:
            return str(key)
        raise ValueError("peptidebenchmark record without entry_id/url/title")

    def source_url(self, raw):
        return canonical_url(raw.get("url")) if raw.get("url") else None


@register_adapter
class WhatsAppExportAdapter(TextEnvelopeAdapter):
    source_type = "whatsapp_export"
    adapter_version = "whatsapp_export_v0.1"

    def record_id(self, raw):
        # conversation identity = channel + counterpart number
        key = raw.get("conversation_id") or raw.get("counterpart") or raw.get("export_file")
        if not key:
            raise ValueError("whatsapp_export without conversation_id/counterpart/export_file")
        return str(key)

    def parse(self, raw):
        content = super(WhatsAppExportAdapter, self).parse(raw)
        content["counterpart"] = normalize_phone(raw.get("counterpart"))
        content["channel"] = "whatsapp"
        return content


@register_adapter
class TelegramExportAdapter(TextEnvelopeAdapter):
    source_type = "telegram_export"
    adapter_version = "telegram_export_v0.1"

    def record_id(self, raw):
        key = raw.get("conversation_id") or raw.get("counterpart") or raw.get("export_file")
        if not key:
            raise ValueError("telegram_export without conversation_id/counterpart/export_file")
        return str(key)

    def parse(self, raw):
        content = super(TelegramExportAdapter, self).parse(raw)
        content["counterpart"] = raw.get("counterpart")
        content["channel"] = "telegram"
        return content


@register_adapter
class PDFDocumentAdapter(TextEnvelopeAdapter):
    source_type = "pdf_document"
    adapter_version = "pdf_document_v0.1"

    def record_id(self, raw):
        key = raw.get("doc_id") or raw.get("filename")
        if not key:
            raise ValueError("pdf_document without doc_id/filename")
        return str(key)

    def parse(self, raw):
        content = super(PDFDocumentAdapter, self).parse(raw)
        content["filename"] = raw.get("filename")
        content["pdf_extracted_text"] = raw.get("text", "")  # BLOCKED: pymupdf absent — text must be pre-extracted
        content["pdf_extraction_note"] = "text layer supplied by fixture; in-vivo PDF text extraction not implemented (pymupdf unavailable)"
        return content


@register_adapter
class ImageDocumentAdapter(TextEnvelopeAdapter):
    source_type = "image_document"
    adapter_version = "image_document_v0.1"

    def record_id(self, raw):
        key = raw.get("image_id") or raw.get("path") or raw.get("filename")
        if not key:
            raise ValueError("image_document without image_id/path/filename")
        return str(key)

    def parse(self, raw):
        content = super(ImageDocumentAdapter, self).parse(raw)
        content["image_path"] = raw.get("path") or raw.get("filename")
        content["route"] = "visual"  # Master Pack §12: Image → Qwen-VL → (GLM-OCR) → Qwen 27B
        return content


@register_adapter
class RegulatorySourceAdapter(TextEnvelopeAdapter):
    source_type = "regulatory_source"
    adapter_version = "regulatory_source_v0.1"

    def record_id(self, raw):
        key = raw.get("record_id") or raw.get("url") or raw.get("title")
        if not key:
            raise ValueError("regulatory_source without record_id/url/title")
        return str(key)

    def source_url(self, raw):
        return canonical_url(raw.get("url")) if raw.get("url") else None

    def llm_fields(self):
        return ["entity_name", "action_type", "action_summary"]


@register_adapter
class ManualEvidenceAdapter(TextEnvelopeAdapter):
    source_type = "manual_evidence"
    adapter_version = "manual_evidence_v0.1"

    def record_id(self, raw):
        key = raw.get("evidence_id_manual") or raw.get("filename") or raw.get("title")
        if not key:
            raise ValueError("manual_evidence without evidence_id_manual/filename/title")
        return str(key)

    def llm_fields(self):
        return ["identity", "business_role_claims", "supplier_claims", "addresses", "certifications"]
