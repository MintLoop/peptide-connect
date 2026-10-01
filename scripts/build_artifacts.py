#!/usr/bin/env python3
"""Build all required V0 artifacts (Master Pack §16) from a run directory.

Reads the JSONL stores and emits:
  canonical_suppliers.jsonl, supplier_observations.jsonl, analytical_evidence.jsonl,
  source_records.jsonl, evidence_lineage.jsonl (already in store — copied),
  supplier_aliases.csv, analytical_coverage_matrix.csv, claims_vs_evidence.csv,
  entity_conflicts.csv, unresolved_entities.csv, followup_questions.csv,
  sync_receipt.json
"""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pcconnect.store import Store
from pcconnect import ids
from pcconnect.adapters.base import utcnow_iso


def build(run_dir, out_dir=None):
    store = Store(run_dir)
    out_dir = out_dir or run_dir
    os.makedirs(out_dir, exist_ok=True)

    source_records = store.read_all("source_records")
    lineage = store.read_all("evidence_lineage")
    observations = store.read_all("supplier_observations")
    analytical = store.read_all("analytical_evidence")

    # ---------------- canonical suppliers (from observation grouping) ----------
    # Group observations by their contact signals to form candidate entities.
    suppliers = {}
    for obs in observations:
        pass  # V0 offline: entity grouping happens via resolver during live runs

    # Suppliers with analytical records (SUP-000 placeholder) + site-derived ones
    site_suppliers = {}
    for rec in source_records:
        if rec["source_type"] != "supplier_site":
            continue
        c = rec["content"]
        sig = c.get("contact_signals") or {}
        domain = c.get("domain") or (sig.get("domains") or [None])[0]
        if not domain:
            continue
        if domain not in site_suppliers:
            site_suppliers[domain] = {
                "supplier_id": "SUP-%03d" % (len(site_suppliers) + 1),
                "canonical_name": c.get("title") or domain,
                "resolution_status": "UNRESOLVED",
                "domain": [domain],
                "email": sig.get("emails", []),
                "phone": sig.get("phones", []),
                "whatsapp": sig.get("whatsapp", []),
                "telegram": sig.get("telegram", []),
                "marketplace_profile": [],
                "created_from_source": rec["source_id"],
                "created_at": rec.get("retrieved_at"),
            }

    # ---------------- aliases CSV ----------------------------------------------
    def write_csv(path, header, rows):
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    alias_rows = []
    for sup in site_suppliers.values():
        for dom in sup["domain"]:
            alias_rows.append([sup["supplier_id"], "domain", dom, "OBSERVED", sup["created_from_source"]])
        for wa in sup["whatsapp"]:
            alias_rows.append([sup["supplier_id"], "whatsapp", wa, "OBSERVED", sup["created_from_source"]])
        for tg in sup["telegram"]:
            alias_rows.append([sup["supplier_id"], "telegram", tg, "OBSERVED", sup["created_from_source"]])
    write_csv(os.path.join(out_dir, "supplier_aliases.csv"),
              ["supplier_id", "alias_type", "alias_value", "status", "source_id"], alias_rows)

    # ---------------- analytical coverage matrix (§8) ---------------------------
    # compound-specific coverage per supplier, NEVER inferring untested dimensions.
    # Analytical records carry a `submitter` name; an EXACT canonical-name match
    # binds them to a site supplier as a name-based candidate link (flagged,
    # never a silent merge — §7.1). Unmatched records stay SUP-000/unbound.
    DIMS = ["identity", "purity", "quantity", "endotoxin", "sterility",
            "heavy_metals", "residual_solvents", "water_content", "counterion",
            "contamination_screening", "other"]
    name_to_sup = {s["canonical_name"].strip().lower(): s for s in site_suppliers.values()}
    name_links = []
    for i, rec in enumerate(analytical):
        sub = (rec.get("submitter") or "").strip().lower()
        if sub and sub in name_to_sup:
            rec = dict(rec)
            rec["supplier_id"] = name_to_sup[sub]["supplier_id"]
            rec["entity_linkage"] = "name_exact_candidate"
            analytical[i] = rec  # update the list, not just the loop var
            name_links.append((rec["analytical_record_id"], rec["supplier_id"]))
    cov_rows = []
    by_supplier_compound = {}
    for rec in analytical:
        key = (rec["supplier_id"], rec["compound"])
        by_supplier_compound.setdefault(key, []).append(rec)
    for (sup, compound), recs in sorted(by_supplier_compound.items()):
        n = len(recs)
        lots = {r.get("lot") for r in recs if r.get("lot")}
        row = [sup, compound, n, len(lots)]
        for dim in DIMS:
            tested = sum(1 for r in recs if (r.get("dimensions") or {}).get(dim, {}).get("tested"))
            row.append("%d/%d" % (tested, n))
        cov_rows.append(row)
    write_csv(os.path.join(out_dir, "analytical_coverage_matrix.csv"),
              ["supplier_id", "compound", "reports", "unique_lots"] + DIMS, cov_rows)

    # ---------------- claims vs evidence -----------------------------------------
    claim_rows = []
    for rec in source_records:
        flags = (rec.get("content") or {}).get("claims_language") or []
        for flag in flags:
            claim_rows.append([
                rec["source_id"], flag,
                "UNVERIFIED",  # marketing language is a CLAIM until evidence exists (§3.1)
                rec["source_type"],
                "",  # supporting evidence ids: none yet
            ])
    write_csv(os.path.join(out_dir, "claims_vs_evidence.csv"),
              ["source_id", "claim", "status", "source_type", "evidence_ids"], claim_rows)

    # ---------------- entity conflicts / unresolved --------------------------------
    conflict_rows = []
    unresolved_rows = []
    # lineage-based conflicts: same family referenced by multiple independent sources
    fam = {}
    for ln in lineage:
        fam.setdefault(ln["evidence_family_id"], []).append(ln)
    for family_id, members in fam.items():
        if len(members) > 1:
            bases = set(m["lineage_basis"] for m in members)
            conflict_rows.append([
                family_id, "evidence_family_multiple_sources",
                ";".join(m["source_id"] for m in members),
                "UNRESOLVED" if "references_existing_family" in bases else "CONTRADICTED",
            ])
    # unresolved: site suppliers without any analytical linkage
    sup_ids_with_analytical = {r["supplier_id"] for r in analytical}
    for sup in site_suppliers.values():
        if sup["supplier_id"] not in sup_ids_with_analytical:
            unresolved_rows.append([
                sup["supplier_id"], sup["canonical_name"],
                "no_analytical_linkage",
                "site evidence only; no resolved analytical records",
                sup["created_from_source"],
            ])
    write_csv(os.path.join(out_dir, "entity_conflicts.csv"),
              ["subject", "conflict_type", "evidence_ids", "status"], conflict_rows)
    write_csv(os.path.join(out_dir, "unresolved_entities.csv"),
              ["supplier_id", "name", "reason", "detail", "source_id"], unresolved_rows)

    # ---------------- followup questions --------------------------------------------
    followup_rows = []
    for sup in site_suppliers.values():
        followup_rows.append([
            sup["supplier_id"],
            "Does %s hold verifiable certification documents?" % sup["canonical_name"],
            "certification_document_absent",
            sup["created_from_source"],
        ])
        followup_rows.append([
            sup["supplier_id"],
            "Is the claimed manufacturing role supported by independent evidence?",
            "role_unverified",
            sup["created_from_source"],
        ])
    for family_id, members in fam.items():
        if len(members) > 1:
            followup_rows.append([
                family_id,
                "Confirm whether sources %s independently tested or reference one report"
                % "/".join(m["source_id"] for m in members),
                "evidence_family_reference",
                members[0]["source_id"],
            ])
    write_csv(os.path.join(out_dir, "followup_questions.csv"),
              ["subject_id", "question", "reason_code", "source_id"], followup_rows)

    # ---------------- canonical suppliers jsonl ---------------------------------------
    with open(os.path.join(out_dir, "canonical_suppliers.jsonl"), "w", encoding="utf-8") as f:
        for sup in site_suppliers.values():
            f.write(json.dumps(sup, sort_keys=True) + "\n")

    # ---------------- analytical evidence jsonl (with candidate links) ------------------
    with open(os.path.join(out_dir, "analytical_evidence.jsonl"), "w", encoding="utf-8") as f:
        for rec in analytical:
            f.write(json.dumps(rec, sort_keys=True) + "\n")

    # ---------------- sync receipt ------------------------------------------------------
    sync_state = store.load_sync_state()
    receipt = {
        "generated_at": utcnow_iso(),
        "run_dir": os.path.abspath(run_dir),
        "source_records_total": len(source_records),
        "evidence_lineage_total": len(lineage),
        "observations_total": len(observations),
        "analytical_total": len(analytical),
        "analytical_name_linked": len(name_links),
        "analytical_unlinked": len(analytical) - len(name_links),
        "site_suppliers": len(site_suppliers),
        "sync_entries": len(sync_state),
        "artifacts": [
            "canonical_suppliers.jsonl", "supplier_observations.jsonl", "analytical_evidence.jsonl",
            "source_records.jsonl", "evidence_lineage.jsonl", "supplier_aliases.csv",
            "analytical_coverage_matrix.csv", "claims_vs_evidence.csv", "entity_conflicts.csv",
            "unresolved_entities.csv", "followup_questions.csv", "sync_receipt.json",
        ],
    }
    with open(os.path.join(out_dir, "sync_receipt.json"), "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)
    return receipt


def main():
    run_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "artifacts", "v0")
    receipt = build(run_dir)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
