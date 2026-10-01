"""Base adapter: canonical envelope contract + change detection hooks (§4, §14)."""
import datetime
import os

from .. import hashing


def utcnow_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_url(url):
    """Deterministic URL normalization (Master Pack §10).

    Strips fragments, trailing slash, tracking params, default ports, and
    scheme case so that syndicated copies of the same page hash identically.
    """
    if not url:
        return None
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    scheme, rest = url.split("://", 1)
    scheme = scheme.lower()
    # split path / query / fragment
    fragment = ""
    if "#" in rest:
        rest, fragment = rest.split("#", 1)
    query = ""
    if "?" in rest:
        rest, query = rest.split("?", 1)
    host, _, path = rest.partition("/")
    host = host.lower()
    if ":" in host:
        host, port = host.split(":", 1)
        if not ((scheme == "https" and port == "443") or (scheme == "http" and port == "80")):
            host = "%s:%s" % (host, port)
    if path.endswith("/"):
        path = path.rstrip("/")
    # strip common tracking params
    if query:
        keep = [kv for kv in query.split("&")
                if kv and not kv.lower().startswith(("utm_", "ref=", "fbclid", "gclid"))]
        query = "&".join(sorted(keep))
    out = "%s://%s%s" % (scheme, host, "/" + path if path else "")
    if query:
        out += "?" + query
    return out


class SourceAdapter(object):
    """Adapters ingest a raw fixture/payload and emit canonical envelopes.

    Subclasses implement `parse()` returning a dict of envelope `content`.
    `emit()` builds the full envelope, hashes it, and records change state.
    """

    source_type = None  # override
    adapter_version = None  # override, e.g. "janoshik_v0.1"

    def __init__(self):
        if not self.source_type or not self.adapter_version:
            raise NotImplementedError("adapters must define source_type and adapter_version")

    # -- subclass API -------------------------------------------------------
    def parse(self, raw):
        raise NotImplementedError

    def record_id(self, raw):
        raise NotImplementedError

    def source_url(self, raw):
        # return type widened for adapters whose sources have URLs
        return None  # type: ignore[override]

    # -- envelope assembly --------------------------------------------------
    def emit(self, raw, retrieved_at=None):
        content = self.parse(raw)
        record_id = self.record_id(raw)
        envelope = {
            "source_type": self.source_type,
            "source_record_id": str(record_id),
            "source_url": self.source_url(raw),
            "retrieved_at": retrieved_at or utcnow_iso(),
            "raw_content_hash": hashing.sha256_obj(content),
        "content": content,
            "attachments": [],
            "adapter_version": self.adapter_version,
        }
        return envelope


_REGISTRY = {}


def register_adapter(cls):
    _REGISTRY[cls.source_type] = cls
    return cls


def get_adapter(source_type):
    if source_type not in _REGISTRY:
        raise KeyError("no adapter registered for source_type=%r (have: %s)"
                       % (source_type, ", ".join(sorted(_REGISTRY))))
    return _REGISTRY[source_type]()
