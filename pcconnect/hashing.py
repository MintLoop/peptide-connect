"""Content hashing for change detection and dedup (Master Pack §10, §14)."""
import hashlib
import json


def sha256_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(text):
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def canonical_json(obj):
    """Deterministic JSON serialization (sorted keys) so content hashes are stable."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_obj(obj):
    return sha256_text(canonical_json(obj))
