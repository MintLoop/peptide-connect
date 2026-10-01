"""Store layer: append-only JSONL collections with idempotent writes and
per-source sync state for incremental ingestion (Master Pack §6, §14, §16).
"""
import json
import os

from .. import hashing
from .. import ids

# collection name -> filename in the run directory
COLLECTIONS = {
    "source_records": "source_records.jsonl",
    "evidence_lineage": "evidence_lineage.jsonl",
    "supplier_observations": "supplier_observations.jsonl",
    "analytical_evidence": "analytical_evidence.jsonl",
    "canonical_suppliers": "canonical_suppliers.jsonl",
    "dossiers": "dossiers.jsonl",
    "run_events": "run_events.jsonl",
}


class Store(object):
    def __init__(store, root):
        store.root = os.path.abspath(root)
        os.makedirs(store.root, exist_ok=True)
        store._sync_state_path = os.path.join(store.root, "sync_state.json")
        store._sync_state = None

    # -- path helpers ---------------------------------------------------------
    def path(store, collection):
        if collection not in COLLECTIONS:
            raise KeyError("unknown collection %r (have: %s)" % (collection, ", ".join(COLLECTIONS)))
        return os.path.join(store.root, COLLECTIONS[collection])

    # -- idempotent append ------------------------------------------------------
    def _load_ids(store, collection, key):
        """Load existing primary keys from a collection file (for idempotency)."""
        p = store.path(collection)
        found = set()
        if not os.path.exists(p):
            return found
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if key in rec:
                    found.add(rec[key])
        return found

    def append_once(store, collection, record, key_field):
        """Append record unless a record with the same key_field value exists.

        Returns ("appended", record) or ("duplicate", existing_key_present).
        Repeated ingestion never duplicates evidence (Master Pack §18).
        """
        key_val = record.get(key_field)
        if key_val is None:
            raise ValueError("record missing key field %r" % key_field)
        p = store.path(collection)
        existing = store._load_ids(collection, key_field)
        if key_val in existing:
            return "duplicate", key_val
        with open(p, "a", encoding="u8") as f:
            f.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        return "appended", key_val

    # -- reading ----------------------------------------------------------------
    def read_all(store, collection):
        p = store.path(collection)
        out = []
        if not os.path.exists(p):
            return out
        with open(p, "r", encoding="u8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def read_all_by_key(store, collection, key_field):
        out = {}
        for rec in store.read_all(collection):
            out[rec.get(key_field)] = rec
        return out

    # -- sync state (incremental ingestion, §14) --------------------------------
    def load_sync_state(store):
        if store._sync_state is not None:
            return store._sync_state
        if os.path.exists(store._sync_state_path):
            with open(store._sync_state_path, "r", encoding="u8") as f:
                store._sync_state = json.load(f)
        else:
            store._sync_state = {}
        return store._sync_state

    def sync_entry(store, source_type, source_record_id):
        st = store.load_sync_state()
        return st.get("%s:%s" % (source_type, source_record_id), {})

    def update_sync_entry(store, source_type, source_record_id, **fields):
        st = store.load_sync_state()
        key = "%s:%s" % (source_type, source_record_id)
        entry = st.get(key, {})
        entry.update(fields)
        entry["source_type"] = source_type
        entry["source_record_id"] = source_record_id
        st[key] = entry
        store._save_sync_state()

    def _save_sync_state(store):
        tmp = store._sync_state_path + ".tmp"
        with open(tmp, "w", encoding="u8") as f:
            json.dump(store._sync_state, f, sort_keys=True, indent=1)
        os.replace(tmp, store._sync_state_path)

    # -- events ---------------------------------------------------------------
    def event(store, kind, **fields):
        from ..adapters.base import utcnow_iso
        rec = {"event": kind, "at": utcnow_iso()}
        rec.update(fields)
        with open(store.path("run_events"), "a", encoding="u8") as f:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")

    # -- convenience wrappers with canonical IDs --------------------------------
    def _append_with_id(self, collection, record, id_field, natural_key_fields, base_id):
        """Idempotent append with natural-key dedup and collision-probed IDs.

        - same natural key -> duplicate (reuse existing id)
        - id collision with a DIFFERENT natural key -> probe forward until free
        """
        natural_key = tuple(record.get(f) for f in natural_key_fields)
        existing = self._load_natural_keys(collection, natural_key_fields)
        if natural_key in existing:
            return "duplicate", existing[natural_key][id_field]
        taken_ids = self._load_ids(collection, id_field)
        new_id = base_id
        bump = 0
        while new_id in taken_ids:
            bump += 1
            prefix, num = base_id.rsplit("-", 1)
            new_id = "%s-%08d" % (prefix, (int(num) + bump) % 100000000)
        record = dict(record)
        record[id_field] = new_id
        with open(self.path(collection), "a", encoding="u8") as f:
            f.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        return "appended", new_id

    def _load_natural_keys(self, collection, natural_key_fields):
        """natural_key tuple -> record, for records having all key fields."""
        p = self.path(collection)
        out = {}
        if not os.path.exists(p):
            return out
        with open(p, "r", encoding="u8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                key = tuple(rec.get(f) for f in natural_key_fields)
                if all(k is not None for k in key):
                    out[key] = rec
        return out

    def put_source_record(self, envelope):
        return self._append_with_id(
            "source_records", dict(envelope), "source_id",
            ("source_type", "source_record_id"),
            ids.source_id(envelope["source_type"], envelope["source_record_id"]),
        )

    def put_evidence_lineage(self, lineage):
        return self._append_with_id(
            "evidence_lineage", lineage, "evidence_id",
            ("source_id",), lineage["evidence_id"],
        )

    def put_observation(self, obs):
        return self._append_with_id(
            "supplier_observations", obs, "observation_id",
            ("entity_id", "field", "value", "source_id", "observed_at"),
            obs["observation_id"],
        )

    def put_analytical(self, rec):
        return self._append_with_id(
            "analytical_evidence", rec, "analytical_record_id",
            ("supplier_id", "compound", "evidence_family_id", "lot"),
            rec["analytical_record_id"],
        )

    def put_supplier(self, rec):
        return self.append_once("canonical_suppliers", rec, "supplier_id")

    def put_dossier(self, rec):
        return self.append_once("dossiers", rec, "dossier_id")
