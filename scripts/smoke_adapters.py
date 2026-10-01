#!/usr/bin/env python3
"""Smoke: all 11 adapters emit schema-valid envelopes; canonical_url behaves."""
import json
import sys

sys.path.insert(0, __file__.rsplit("/scripts/", 1)[0])

from pcconnect.adapters.base import canonical_url, get_adapter
from pcconnect.adapters import janoshik, generic  # noqa: F401 — registers adapters
from jsonschema import Draft202012Validator

CASES = [
    ("janoshik", {"report_id": "211414", "text": "Report no: 211414\nSample name: Retatrutide\nLot: RT-0926A\nPurity (HPLC): 99.2%\nEndotoxin: < 0.5 EU/mg"}),
    ("supplier_site", {"url": "https://ExampleVendor.com/about/?utm_source=x", "title": "About", "text": "We are a manufacturer with GMP facility. Email: sales@examplevendor.com WhatsApp: +1 305 555 0142"}),
    ("b2b_directory", {"listing_id": "L-77", "text": "Listing: Peptide Wholesaler Ltd, email info@pwl.example"}),
    ("finnrick", {"entry_id": "FR-9", "text": "Finnrick entry noting janoshik report 211414 for retatrutide"}),
    ("peptidebenchmark", {"entry_id": "PB-3", "text": "Benchmark entry: semaglutide 99.1%"}),
    ("whatsapp_export", {"conversation_id": "WA-1", "counterpart": "+1 305 555 0142", "text": "[2026-09-28] Supplier: yes we test every batch"}),
    ("telegram_export", {"conversation_id": "TG-1", "counterpart": "@pep_supplier", "text": "[2026-09-29] Supplier: COA available on request"}),
    ("pdf_document", {"doc_id": "DOC-1", "filename": "coa.pdf", "text": "Certificate of Analysis sample text"}),
    ("image_document", {"image_id": "IMG-1", "path": "fixtures/v0/coa_screenshot.png", "text": ""}),
    ("regulatory_source", {"record_id": "REG-1", "text": "Company X flagged in import alert 99-99"}),
    ("manual_evidence", {"evidence_id_manual": "MAN-1", "text": "Manual note: supplier claims GMP cert from issuer Y"}),
]

v = Draft202012Validator(json.load(open("pcconnect/schemas/envelope.schema.json")))
fails = 0
for st, raw in CASES:
    adapter = get_adapter(st)
    env = adapter.emit(raw, retrieved_at="2026-09-30T20:00:00Z")
    errs = list(v.iter_errors(env))
    status = "OK " if not errs else "FAIL"
    if errs:
        fails += 1
        print("%s %-18s -> %s" % (status, st, [e.message for e in errs][:2]))
    else:
        print("%s %-18s -> %s" % (status, st, env["source_record_id"]))

# canonical URL checks
url_cases = [
    ("HTTPS://Example.COM:443/a/?utm_source=x#frag", "https://example.com/a"),
    ("https://shop.example.co/", "https://shop.example.co"),
    ("http://example.org:8080/x?b=2&a=1", "http://example.org:8080/x?a=1&b=2"),
]
for raw, expect in url_cases:
    got = canonical_url(raw)
    mark = "OK " if got == expect else "FAIL"
    if got != expect:
        fails += 1
    print("%s canonical_url(%r) = %r" % (mark, raw, got))

sys.exit(1 if fails else 0)
