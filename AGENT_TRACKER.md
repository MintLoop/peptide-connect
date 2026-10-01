# AGENT_TRACKER.md — Peptide Connect Supplier Intelligence V0

## Status: V0 IMPLEMENTED (offline-verified, live-route verification in flight)

| Component | Status | Evidence |
|---|---|---|
| Contract layers (Master Pack / Compact Runtime / MoA) | ✅ done | `contracts/` (3 files, byte-faithful), `prompts/` (7 split worker contracts) |
| Canonical schemas (envelope, observation, analytical, lineage, dossier, extraction) | ✅ done | `pcconnect/schemas/` — generated from single source, all validate as draft 2020-12 |
| Source adapters (11 source types) | ✅ done | `pcconnect/adapters/` — all emit schema-valid envelopes (17 tests) |
| Deterministic tier (§10) | ✅ done | `pcconnect/deterministic/` — URLs, contacts, lots, reports, dates, hashes, change detection |
| Entity resolution (§7) | ✅ done | `pcconnect/entity/resolver.py` — exact-key blocking, never silent merges, identity ≠ role |
| MoA escalation router (§11-12) | ✅ done | `pcconnect/moa/router.py` — routine/questionable/hard/visual + material-issue 125B gate |
| Model tier client | ✅ done | `pcconnect/tiers.py` — per-worker contract prompts, schema validation, metrics, offline stubs |
| Pipeline orchestrator | ✅ done | `pcconnect/pipeline.py` — routing flows, incremental sync, idempotent stores |
| Required artifacts (§16) | ✅ done | `scripts/build_artifacts.py` — all 12 artifacts from `artifacts/v0/` |
| Offline V0 experiment (528 records) | ✅ done | 528/528 stored, 0 schema failures, 3.1s; re-ingest = 0 new, 0 LLM calls |
| Live model-route verification | ✅ done | `experiments/model-route-verification/receipts.json` — 6/6 PASS (2026-09-30) |
| PDF text extraction (in-vivo) | ⛔ blocked | `pymupdf` unavailable under system Python 3.9 — fixture-supplied text used; adapter marked |
| Entity grouping to 10 canonical suppliers (live model pass) | ⏳ next | offline candidate links done (500 name-linked, flagged `name_exact_candidate`) |

## Routing decisions log

- 500 clean janoshik records → **routine** (deterministic + stub extraction, no Granite)
- 14 claim-language records (6 sites, 2 directories, 6 WhatsApp) + 1 regulatory record → **questionable** (Granite audit)
- 1 image document → **visual** (Qwen-VL → OCR fallback → Qwen 27B)
- 0 records → **hard/MoA panel** (offline skeptic stubs return NO_MATERIAL_OBJECTION, so
  nothing remains unresolved after normal validation — contract-correct)
- 125B invocations: **0** in the offline corpus run; panel mechanics verified by direct
  test (`test_panel_runs_resolver_skeptic_adjudicator_offline`) and the gate tests

## MoA panel (contracts/MOA_CONTRACT.md — verbatim contract layer)

- Panel: Resolver (`qwen3.8:27b-mlx-menta-64k`, `prompts/moa_resolver.md`) → Skeptic
  (`granite4.2:30b`) → Adjudicator (`qwen3.8-flash-next:125b-mlx`). No voting.
- Gate (`pcconnect/moa/panel.py::should_open_panel`): panel opens only when an
  eligible issue (11 categories) remains unresolved AFTER normal validation.
- Do-not-escalate list enforced: LOW confidence, missing fields, WhatsApp usage,
  promotional language, sparse evidence — never sufficient alone.
- Adjudication output schema: `pcconnect/schemas/adjudication.schema.json` —
  the contract's REQUIRED FINAL OUTPUT fields exactly (11 fields, decision
  enum = 7 classes, confidence enum = HIGH/MEDIUM/LOW).

## Failure examples caught in testing

1. **ID-space collision** (fixed): 5-digit hash IDs lost 3 of 528 records to birthday collisions
   (`source_records_total=525`). Fixed: 8-digit IDs + natural-key dedup + collision probing.
   Regression test added (`test_store_append_once_idempotent`).
2. **Missing adapter registration**: pipeline standalone runs lacked the janoshik adapter
   (import side-effect). Fixed: `pcconnect/adapters/__init__.py` auto-registers all adapters.
3. **Schema-invalid offline stub**: first stub returned a nonconforming extraction →
   100% schema failures. Fixed: stub is now schema-valid with ZERO assertions (offline mode
   claims nothing — honest by construction).
4. **Submitter regex mismatch**: adapter expected "submitted by", fixtures (and real Janoshik
   records) use "Submitter:". Fixed: regex accepts both; 500/500 submitters now parsed.

## Known limitations

- Offline-mode stubs assert nothing, so observation counts are 0 and dossiers are not
  synthesized — evidence assertions require the live tier (next milestone).
- Entity binding uses exact canonical-name match only (flagged candidate links); embedding
  candidates (bge-m3) are wired but not yet exercised in the pipeline.
- In-vivo PDF/image ingestion: PDF text layer must be pre-extracted (pymupdf blocked);
  image route exercised with stub visual output.
