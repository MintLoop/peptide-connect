#!/usr/bin/env python3
"""Generate V0 experiment fixtures (Master Pack §15).

Synthetic but realistic:
- 500 janoshik records across 10 supplier entities / 8 compounds
- supplier sites (with marketing claims + contact signals)
- b2b directory listings (some SYNDICATING janoshik reports — lineage tests)
- whatsapp + telegram transcripts
- one regulatory record
- one image-document placeholder (visual route)

Names/numbers are fabricated test data, labeled as such in every record.
"""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "fixtures", "v0")

SUPPLIERS = [
    # name, domain, wa, tg, role_language
    ("Nordwind Bio Labs", "nordwindbio.example", "+49 170 555 0101", "@nordwindbio", "manufacturer"),
    ("Alpine Peptide Works", "alpineworks.example", "+41 76 555 0102", "@alpineworks", "manufacturer"),
    ("Kestrel Research", "kestrelresearch.example", "+44 7700 900103", "@kestrel_res", "research supplier"),
    ("Meridian Supply Co", "meridiansupply.example", "+1 305 555 0104", "@meridian_supply", "distributor"),
    ("VelaTide Trading", "velatide.example", "+852 5555 0105", "@velatide", "trading company"),
    ("Orion Peptide Group", "orionpeptide.example", "+1 646 555 0106", "@orionpep", "manufacturer"),
    ("Solstice Biolabs", "solsticebio.example", "+34 600 555 0107", "@solsticebio", "research supplier"),
    ("Halcyon Chem", "halcyonchem.example", "+1 213 555 0108", "@halcyon_chem", "wholesaler"),
    ("Polaris Peptides", "polarispeptide.example", "+48 512 555 0109", "@polarispep", "distributor"),
    ("Zephyr Bio Sourcing", "zephyrbio.example", "+31 6 5555 0110", "@zephyrbio", "export agent"),
]

COMPOUNDS = ["retatrutide", "semaglutide", "tirzepatide", "tesamorelin",
             "bpc-157", "ipamorelin", "cjc-1295", "melanotan-ii"]

DIMENSION_LINE_TEMPLATES = [
    ("identity", "Identity (LC-MS): confirmed"),
    ("purity", "Purity (HPLC): {purity}%"),
    ("quantity", "Quantity (fill weight): {qty} mg"),
    ("endotoxin", "Endotoxin: < {endo} EU/mg"),
    ("sterility", "Sterility: passed"),
    ("heavy_metals", "Heavy metals: within limits"),
    ("residual_solvents", "Residual solvents (GC-MS): below LOD"),
    ("water_content", "Water content (KF): {water}%"),
]


def janoshik_record(rng, idx):
    name, domain, wa, tg, role = SUPPLIERS[idx % len(SUPPLIERS)]
    compound = rng.choice(COMPOUNDS)
    report_id = 210000 + idx
    lot = "%s-%04d%s" % (compound[:2].upper(), 900 + (idx % 100), rng.choice("ABC"))
    dims = rng.sample(DIMENSION_LINE_TEMPLATES, k=rng.randint(2, 6))
    lines = [
        "Report no: %d" % report_id,
        "Date of test: 2026-%02d-%02d" % (rng.randint(1, 9), rng.randint(1, 28)),
        "Sample name: %s" % compound.capitalize(),
        "Lot: %s" % lot,
        "Submitter: %s" % name,
    ]
    for dim, tpl in dims:
        lines.append(tpl.format(purity=rng.choice(["98.7", "99.1", "99.2", "99.6"]),
                                qty=rng.choice([5, 10, 15]),
                                endo=rng.choice(["0.5", "1.0"]),
                                water=rng.choice(["0.8", "1.2"])))
    if rng.random() < 0.12:
        lines.append("Paid by: %s" % name)  # vendor-paid → independence signal
    return {"report_id": str(report_id), "text": "\n".join(lines),
            "_fixture_note": "synthetic test data — not a real report"}


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(20260930)  # deterministic fixtures

    items = []
    # 500 janoshik records
    for i in range(500):
        items.append({"source_type": "janoshik", "raw": janoshik_record(rng, i)})

    # 10 supplier sites
    for i, (name, domain, wa, tg, role) in enumerate(SUPPLIERS):
        text = "%s — %s. " % (name, role.capitalize())
        if i % 3 == 0:
            text += "Direct manufacturer with GMP facility. "
        if i % 4 == 1:
            text += "Every batch tested by third-party laboratory. "
        text += "Email: sales@%s WhatsApp: %s Telegram: %s" % (domain, wa, tg)
        items.append({"source_type": "supplier_site",
                      "raw": {"url": "https://%s/about" % domain, "title": name, "text": text}})

    # b2b directory listings — 3 of them SYNDICATE janoshik reports (lineage test)
    for i, (name, domain, wa, tg, role) in enumerate(SUPPLIERS[:5]):
        text = "%s (%s) — peptide supplier. " % (name, role)
        if i < 3:
            text += "Lab-tested: janoshik report %d. " % (210000 + i)  # references family
        text += "Contact: info@%s" % domain
        items.append({"source_type": "b2b_directory",
                      "raw": {"listing_id": "DIR-%02d" % i, "title": name, "text": text}})

    # whatsapp + telegram transcripts
    for i, (name, domain, wa, tg, role) in enumerate(SUPPLIERS[:6]):
        items.append({
            "source_type": "whatsapp_export",
            "raw": {"conversation_id": "WA-%02d" % i, "counterpart": wa,
                    "text": "[2026-09-2%d] Us: Do you have a COA for retatrutide?\n"
                            "[2026-09-2%d] %s: Yes, we can provide COA on request.\n"
                            "[2026-09-2%d] Us: Is every batch tested?\n"
                            "[2026-09-2%d] %s: Yes every batch is tested."
                            % (i % 8, i % 8, name, (i + 1) % 8, (i + 1) % 8, name)},
        })
    for i, (name, domain, wa, tg, role) in enumerate(SUPPLIERS[:4]):
        items.append({
            "source_type": "telegram_export",
            "raw": {"conversation_id": "TG-%02d" % i, "counterpart": tg,
                    "text": "[2026-09-2%d] Us: Can you confirm your manufacturing location?\n"
                            "[2026-09-2%d] %s: We work with partner facilities in Europe."
                            % (i % 8, i % 8, name)},
        })

    # regulatory + manual evidence
    items.append({"source_type": "regulatory_source",
                  "raw": {"record_id": "REG-2026-001",
                          "text": "Import alert 99-08: detention of peptide shipments listing Meridian Supply Co as consignee."}})
    items.append({"source_type": "manual_evidence",
                  "raw": {"evidence_id_manual": "MAN-2026-001",
                          "text": "Manual note (2026-09-15): Nordwind Bio Labs claims ISO 9001 certification; certificate document not yet received."}})

    # image document (visual route smoke)
    items.append({"source_type": "image_document",
                  "raw": {"image_id": "IMG-COA-001", "path": "fixtures/v0/images/coa_placeholder.png",
                          "text": ""}})

    out_path = os.path.join(OUT, "v0_ingest_items.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"_fixture_note": "all records synthetic test data for the V0 experiment",
                   "items": items}, f, indent=1)
    counts = {}
    for it in items:
        counts[it["source_type"]] = counts.get(it["source_type"], 0) + 1
    print("wrote %s: %d items" % (out_path, len(items)))
    print(json.dumps(counts, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
