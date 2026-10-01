# AGENT_BRIEF.md — Peptide Connect Supplier Intelligence

## What this system is

An evidence-first supplier-intelligence pipeline for the fragmented research-peptide
market. It converts fragmented evidence (lab reports, supplier sites, directories,
messaging transcripts, documents) into provenance-backed supplier dossiers. It NEVER
reduces suppliers to good/bad labels, and never converts claims into facts.

## The three contract layers (do not collapse)

1. **Master Pack** (`contracts/MASTER_PACK.md`) — the architecture. Evidence rules,
   source adapters, entity model, analytical model, routing tiers, acceptance criteria.
   Governs everything; never resent to workers with routine calls.
2. **Compact Runtime Prompts** (`contracts/COMPACT_RUNTIME_PROMPTS.md` → `prompts/*.md`) —
   persistent per-worker contracts. Each worker receives ONLY: its compact prompt, the
   relevant schema, the minimum evidence packet, and candidate records.
3. **MoA Contract** (`contracts/MOA_CONTRACT.md`) — exceptional escalation governance.
   The Escalation Router (deterministic code, `pcconnect/moa/router.py`) alone promotes
   packets between tiers. The 125B gate requires ALL of: Granite HIGH-severity objection
   with adjudication_required, a material-issue category, and dossier impact.

## Model assignments (config/models.yaml)

| Tier | Model | Role |
|---|---|---|
| 0 | deterministic code | parsing, normalization, change detection, blocking |
| 1 | `qwen3.8:27b-mlx-menta-64k` | primary extraction + normalization + synthesis |
| 1V | `qwen3-vl:32b` | visual examination (never authenticity) |
| 1E | `bge-m3:567m` | entity candidate retrieval (never identity proof) |
| OCR | `glm-ocr:bf16` | fallback text extraction (normalized afterward) |
| 2 | `granite4.2:30b` | adversarial validation |
| 3 | `qwen3.8-flash-next:125b-mlx` | exceptional adjudication (material issues only) |

## Hard rules every agent must know

- Never convert a supplier claim into a verified fact.
- Preserve provenance for every material assertion (source_id on everything).
- Evidence states: VERIFIED / LIKELY / POSSIBLE / UNVERIFIED / CONTRADICTED /
  UNRESOLVED / INSUFFICIENT_EVIDENCE. Confidence: HIGH / MEDIUM / LOW only.
- Third-party lab testing ≠ independent sampling.
- Do not infer manufacturer status from marketing language.
- Do not merge entities on name similarity alone; embedding similarity is candidate
  evidence, never identity proof.
- Untested analytical dimensions are never inferred as passed.
- UNKNOWN / UNRESOLVED / INSUFFICIENT_EVIDENCE are successful outcomes.
- Never fabricate lot numbers, report IDs, entities, addresses, certificates, dates.
- Visual appearance never establishes document authenticity.

## Repository layout

```
contracts/          the three contract layers (verbatim, authoritative)
prompts/            per-worker runtime contracts (split from Compact Runtime Prompts)
config/models.yaml  model + routing configuration
pcconnect/          the pipeline package
  adapters/         11 source adapters → canonical envelopes
  deterministic/    Tier 0 (no LLM)
  entity/           identity resolution (≠ business-role classification)
  moa/              escalation router (MoA contract)
  schemas/          canonical JSON schemas + generator
  store/            append-only idempotent JSONL stores
  tiers.py          model tier client (contracts + schema validation + metrics)
  pipeline.py       orchestrator (routing flows, incremental sync)
scripts/            fixtures, runner, artifact builder, verification, tests helper
tests/              pytest suite (17 tests)
fixtures/v0/        528 synthetic records (labeled synthetic)
artifacts/v0/       run outputs + all required V0 artifacts
experiments/        live model-route verification receipts
```

## V0 boundary

No commerce, no purchasing, no automatic supplier outreach, no production frontend.
V0 proves: fragmented evidence → reliable, provenance-backed supplier dossiers.
