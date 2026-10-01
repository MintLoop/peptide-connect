# RUNBOOK.md — Peptide Connect Supplier Intelligence V0

All commands run from the repo root (`Sites/peptide-connect`) with the system
Python 3.9 (`/usr/bin/python3`). Dependencies: `jsonschema`, `pytest` (already in
the user site-packages). No other packages required.

## Environment

- Local model fleet via Ollama at `http://127.0.0.1:11434/v1` (all five worker
  models installed — see `config/models.yaml`).
- Fleet conventions (Menta): check `menta-guard.py status` before loading models;
  serialize heavy runs; never abort a sibling session's generation. The 125B
  adjudicator is MLX-served and heavy — invoke only via the pipeline's material-
  issue gate, never directly.

## Daily commands

```bash
# regenerate schemas after editing pcconnect/schemas/generate_schemas.py
/usr/bin/python3 pcconnect/schemas/generate_schemas.py
/usr/bin/python3 scripts/validate_schemas.py

# regenerate fixtures (deterministic seed 20260930)
/usr/bin/python3 scripts/make_fixtures.py

# full offline run (no models) + artifacts
/usr/bin/python3 scripts/run_v0.py --offline
/usr/bin/python3 scripts/build_artifacts.py artifacts/v0

# live run (routes through the real fleet; serialize per Menta rules)
/usr/bin/python3 scripts/run_v0.py            # full 528-item fixture set
/usr/bin/python3 scripts/run_v0.py --limit 20 # smoke first

# re-ingestion check (idempotency): run again, expect 528 unchanged, 0 new
/usr/bin/python3 scripts/run_v0.py --offline

# tests
/usr/bin/python3 -m pytest tests/test_v0.py -q

# live model-route verification (one minimal call per worker model)
/usr/bin/python3 scripts/verify_model_routes.py
```

## Incremental ingestion semantics

Each source record's `sync_state.json` entry tracks `content_hash`,
`last_checked_at`, `last_successful_sync`, `status`. Unchanged content short-
circuits the pipeline BEFORE any model call (§14). Changed content reprocesses;
the idempotent stores prevent duplicate evidence (§18).

## Live-run escalation discipline

- Routing: `pcconnect/moa/router.py` decides — workers never self-escalate.
- The MoA panel (Resolver → Skeptic → Adjudicator) opens only when a material
  unresolved issue remains after normal validation (`should_open_panel`,
  `pcconnect/moa/panel.py`). Do-NOT-escalate: LOW confidence, missing fields,
  WhatsApp usage, promotional language, sparse evidence.
- The panel must NOT vote. Agreement between models is not evidence; original
  source material is evidence. The 125B adjudicator returns the narrowest
  defensible conclusion using the 7 decision classes — preserving ambiguity
  when evidence supports multiple plausible explanations.
- `human_review` events land in `run_events.jsonl` with the disputed issue; these
  are terminal for the run — resolve them by hand, never by re-running.

## Artifacts (§16)

`scripts/build_artifacts.py artifacts/v0` writes to `artifacts/v0/`:
`canonical_suppliers.jsonl`, `supplier_observations.jsonl`, `analytical_evidence.jsonl`,
`source_records.jsonl`, `evidence_lineage.jsonl`, `supplier_aliases.csv`,
`analytical_coverage_matrix.csv`, `claims_vs_evidence.csv`, `entity_conflicts.csv`,
`unresolved_entities.csv`, `followup_questions.csv`, `sync_receipt.json`.
Run metrics land in `run_metrics.json`; per-model call/token metrics inside it.

## Troubleshooting

- **`no adapter registered for source_type=...`** — import `pcconnect.adapters`
  (the package registers all built-ins); never import a lone adapter module.
- **Schema failures > 2% on live runs** — the primary worker's contract prompt
  (`prompts/qwen27b_extraction.md`) plus retry hint handle most; persistent
  failures indicate a schema/prompt drift — regenerate schemas and re-run.
- **125B invocations > 10% of records** — the MoA gate is misconfigured or Granite is
  over-objecting; inspect `run_events.jsonl` route reasons and `moa_panel` events
  before anything else.
- **pymupdf missing** — in-vivo PDF text extraction is blocked; supply
  pre-extracted text via the fixture `text` field (adapter notes this).

## Next milestones

1. Live extraction pass over the 528-record corpus (Qwen 27B tier) — the offline
   stubs assert nothing by design; this produces the first real observations.
2. BGE-M3 candidate retrieval wired into entity resolution (embeddings computed,
   candidates flagged POSSIBLE_MATCH, never auto-merged).
3. Dossier synthesizer live pass (Qwen 27B with the synthesizer contract).
