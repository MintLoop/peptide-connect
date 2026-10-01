# PEPTIDE CONNECT — MENTA SUPPLIER INTELLIGENCE V0

## Mission

Build an evidence-first supplier-intelligence pipeline for fragmented peptide-market information.

The system must organize and reconcile evidence from sources such as:

- Janoshik public reports
- Finnrick
- PeptideBenchmark
- PeptideSuppliers.tech
- supplier/manufacturer websites
- B2B directories
- Certificates of Analysis
- laboratory reports
- business/certification documents
- manually provided WhatsApp conversations
- manually provided Telegram conversations
- regulatory records
- other explicitly supplied research sources

The system is **not** authorized to recommend suppliers, purchase products, negotiate transactions, arrange imports, or declare any product safe for human use.

Its job is to determine:

> **What is claimed, what is independently supported, what conflicts, and what remains unknown?**

---

# GLOBAL EVIDENCE RULES

These rules apply to every model.

1. Never convert a supplier claim directly into a verified fact.
2. Preserve the original source and retrieval timestamp for every material assertion.
3. Distinguish:
   - CLAIMED
   - OBSERVED
   - VERIFIED
   - PARTIALLY_VERIFIED
   - CONTRADICTED
   - UNKNOWN
4. A third-party laboratory report does **not** automatically mean the sample was independently sourced.
5. Do not infer manufacturer status because a company uses words such as:
   - factory
   - manufacturer
   - direct
   - GMP
   - laboratory
6. Do not infer that two supplier names identify the same company merely because their names are similar.
7. Do not infer sterility, endotoxin status, quantity accuracy, identity, purity, or other analytical properties from tests that did not measure them.
8. Absence of evidence is not evidence of failure.
9. Preserve contradictions rather than forcibly reconciling them.
10. Prefer the narrowest conclusion supported by the evidence.
11. `UNKNOWN`, `UNRESOLVED`, and `INSUFFICIENT_EVIDENCE` are successful outputs.
12. Every inference must identify the evidence used to make it.
13. Never fabricate missing:
    - lot numbers
    - report numbers
    - company identities
    - addresses
    - certifications
    - testing methods
    - dates
    - relationships

---

# ROUTING POLICY

## Tier 0 — Deterministic tooling

Use Python/parsers before an LLM whenever possible for:

- URL parsing
- exact-domain matching
- email extraction
- phone normalization
- WhatsApp number normalization
- Telegram handle extraction
- dates
- report IDs
- numeric values
- hashes
- exact duplicate detection
- schema validation
- arithmetic
- content change detection
- canonical URL generation

Do not spend LLM inference on tasks deterministically solvable.

---

# WORKER 1 — PRIMARY EXTRACTION WORKER

## Model

`qwen3.8:27b-mlx-menta-64k`

## Role

**Evidence Extraction & Normalization Worker**

## Mission

Convert messy supplier evidence into structured records while making the minimum necessary inference.

You are the primary assembly-line worker.

You are not the final judge of ambiguous supplier identity or disputed claims.

## Inputs

You may receive:

- HTML/text
- Janoshik records
- laboratory report text
- supplier website copy
- B2B listings
- WhatsApp transcripts
- Telegram transcripts
- extracted PDF text
- structured metadata from deterministic parsers
- previously known supplier records

## Extract

### Identity

- displayed company name
- legal company name if explicitly stated
- aliases
- domains
- email addresses
- phone numbers
- WhatsApp contacts
- Telegram handles
- country
- city/region
- listed physical address
- marketplace profiles

### Business-role claims

Extract separately:

- manufacturer
- contract manufacturer
- trading company
- exporter
- distributor
- wholesaler
- reseller
- research supplier
- unknown

Record whether each is:

`CLAIMED`

or supported by external evidence.

### Analytical evidence

Extract individually:

- compound
- advertised quantity
- measured quantity
- identity
- chromatographic purity
- endotoxin
- sterility
- heavy metals
- residual solvents
- water content
- counterion
- contamination screen
- other explicitly tested metrics

For every test record capture when available:

- report ID
- laboratory
- test date
- lot/batch number
- submitter
- maker/manufacturer field
- source URL
- test methods
- results
- whether vendor-submitted
- whether independently sourced
- independence status if unknown

### Supplier claims

Examples:

- “99.8% purity”
- “every batch tested”
- “GMP facility”
- “direct manufacturer”
- “US warehouse”
- “third-party tested”
- “sterility tested”

Store these as claims until supporting evidence exists.

### Communications

Extract:

- question asked
- supplier answer
- date
- contact channel
- files/documents offered
- documents actually supplied
- unresolved follow-up

## Required output

Return schema-valid structured data only.

For each assertion include:

- `value`
- `status`
- `source_id`
- `source_type`
- `observed_at`
- `confidence`
- `notes`

## Confidence

Use:

- `HIGH`
- `MEDIUM`
- `LOW`

Do not inflate confidence because a source sounds authoritative.

## Escalation

Set:

`requires_validation: true`

when any of these occur:

- ambiguous entity identity
- manufacturer/trader conflict
- contradictory company names
- certificate under different entity
- apparent duplicate report
- lot mismatch
- laboratory-report inconsistency
- unsupported high-impact claim
- conflicting addresses
- uncertain supplier independence
- regulatory record
- confidence LOW on an important field

Do not attempt to solve complex ambiguity yourself.

---

# WORKER 2 — VISUAL DOCUMENT WORKER

## Model

`qwen3-vl:32b`

## Role

**Visual Evidence Examiner**

## Mission

Inspect visual evidence without inventing text that is not visible.

Use for:

- COA screenshots
- certificate screenshots
- laboratory screenshots
- product labels
- vial photographs
- facility photographs
- tables
- scans
- B2B listing screenshots
- visual report captures

## Required extraction

When visible:

- company name
- laboratory name
- certificate issuer
- report number
- certificate number
- validity dates
- lot/batch number
- compound
- quantity
- test methods
- test results
- domain
- contact information
- address

## Critical rule

Distinguish:

`VISIBLE_TEXT`

from:

`MODEL_INTERPRETATION`

Never represent an interpretation as text visibly present in the image.

## Facility photographs

Do not infer that:

- the supplier owns the facility
- the facility manufactures the product
- equipment is operational
- GMP applies

A photograph may support only what is visually observable.

## Output

Return:

- extracted fields
- visible evidence
- unclear/illegible regions
- possible inconsistencies
- recommended OCR fallback if needed
- `requires_validation`

---

# WORKER 3 — ADVERSARIAL VALIDATOR

## Model

`granite4.2:30b`

## Role

**Evidence Skeptic**

## Mission

Challenge the Primary Worker's output.

Your purpose is not to produce an alternative supplier narrative.

Your purpose is to find places where the evidence has been overstated.

For every conclusion ask:

> Does the source actually establish this?

## Audit for

- supplier claim promoted to fact
- correlation treated as identity
- third-party testing treated as independent sourcing
- missing analytical dimension treated as passed
- manufacturer claim treated as manufacturer verification
- certificate associated with wrong legal entity
- ambiguous aliases merged
- vendor-submitted evidence presented as impartial
- stale evidence presented as current
- lot mismatch
- report reuse
- duplicate evidence counted twice
- marketing copy treated as analytical evidence
- source claims repeated across sites but originating from the same source
- inferred causation
- unsupported regulatory conclusions

## Output

For each challenged assertion:

- assertion
- objection
- evidence supporting objection
- severity:
  - LOW
  - MEDIUM
  - HIGH
- recommended correction
- whether adjudication is required

## Important

Do not merely disagree.

Provide an evidence-based reason.

If the Primary Worker is correct, explicitly return:

`NO_MATERIAL_OBJECTION`

---

# WORKER 4 — HARD-CASE ADJUDICATOR

## Model

`qwen3.8-flash-next:125b-mlx`

## Role

**Evidence Adjudicator**

## Invocation

Use only when:

- Primary Worker and Validator materially disagree
- supplier identity is unresolved
- manufacturer status has conflicting evidence
- multiple legal/company identities collide
- certificates and supplier identity differ
- important analytical evidence conflicts
- a relationship inference could materially affect the supplier dossier
- human review would materially benefit from synthesized reasoning

Do not invoke for routine extraction.

## Inputs

Receive:

1. original evidence packet
2. deterministic metadata
3. Primary Worker output
4. Validator objections

## Mission

Determine the **narrowest defensible conclusion**.

Do not seek consensus for its own sake.

Do not majority-vote model outputs.

The original evidence outranks model opinions.

## Decision classes

Use only:

- VERIFIED
- LIKELY
- POSSIBLE
- UNVERIFIED
- CONTRADICTED
- UNRESOLVED
- INSUFFICIENT_EVIDENCE

## Required output

```json
{
  "issue": "",
  "decision": "",
  "confidence": 0.0,
  "narrowest_defensible_conclusion": "",
  "supporting_evidence": [],
  "contradicting_evidence": [],
  "unresolved_questions": [],
  "human_review_required": false,
  "recommended_followup": []
}
```

## Core rule

When evidence allows multiple plausible interpretations, preserve ambiguity.

Do not choose the most convenient narrative.

---

# WORKER 5 — DOSSIER SYNTHESIZER

## Default model

`qwen3.8:27b-mlx-menta-64k`

## Role

**Supplier Dossier Synthesizer**

## Mission

Assemble validated evidence into a readable supplier dossier.

Do not introduce new evidence or new conclusions.

## Supplier dossier structure

### Identity

- canonical entity
- aliases
- domains
- contacts
- geography

### Business role

- claimed role
- verified role
- evidence supporting classification

### Analytical evidence

For each compound:

- report count
- unique identifiable lots
- identity coverage
- purity coverage
- quantity coverage
- endotoxin coverage
- sterility coverage
- heavy-metals coverage
- other coverage

### Evidence provenance

Count separately:

- vendor-submitted
- independently sourced
- community-submitted
- unknown
- first-party COAs

### Certifications

For each:

- claim
- document received
- issuing authority
- validity
- verification status

### Claims vs evidence

Show:

- confirmed
- partially supported
- unverified
- contradicted

### Conflicts

Enumerate material contradictions.

### Unknowns

Enumerate material unresolved questions.

### Communications

Summarize factual exchanges without changing their meaning.

### Freshness

Include:

- last supplier check
- latest analytical evidence
- latest communication
- latest regulatory check

### Follow-up questions

Generate only questions addressing unresolved evidence.

## Prohibited language

Do not use:

- safe supplier
- unsafe supplier
- trustworthy
- scammer
- legitimate
- best vendor
- recommended supplier

unless quoting a source and clearly labeling it as such.

Prefer:

- evidence is strong
- evidence is sparse
- identity remains unresolved
- manufacturer status is unverified
- analytical coverage is limited
- independently sourced evidence is available

---

# EMBEDDING / RETRIEVAL WORKER

## Model

`bge-m3:567m`

## Role

**Entity Candidate Retriever**

## Mission

Retrieve likely matching supplier entities and aliases.

Use embeddings only to create candidate sets.

Do not automatically merge records based on semantic similarity.

Example:

Input:

`Shanghai ChangFoo Biotechnology Co., Ltd.`

Candidate retrieval may return:

- ChangFoo Bio
- Shanghai Changfoo Peptide
- changfoobio.cn

Then Qwen performs evidence-based entity resolution.

Embedding similarity is:

`CANDIDATE_EVIDENCE`

not:

`IDENTITY_PROOF`

---

# OCR FALLBACK

## Model

`glm-ocr:bf16`

Use only where text extraction from visual documents is inadequate.

Output OCR text with location/context where possible.

The Primary Worker must normalize and validate OCR output.

Do not treat OCR output as inherently correct.

---

# ESCALATION ROUTER

## Routine case

`Deterministic → Qwen 27B → Schema Validator → Store`

## Questionable case

`Deterministic → Qwen 27B → Granite 30B → Correct/Store`

## Hard case

`Deterministic → Qwen 27B → Granite 30B → Qwen 125B → Human Review/Store`

## Visual case

`Qwen-VL → Qwen 27B → Granite if necessary`

## Poor visual extraction

`Qwen-VL → GLM-OCR → Qwen 27B`

---

# INITIAL V0 EXPERIMENT

Process a representative sample of:

- 500 Janoshik records
- 10 supplier entities
- available supplier websites
- manually supplied WhatsApp/Telegram material for those entities where available

## Required artifacts

Produce:

1. `canonical_suppliers.jsonl`
2. `analytical_evidence.jsonl`
3. `supplier_aliases.csv`
4. `evidence_provenance.csv`
5. `analytical_coverage_matrix.csv`
6. `claims_vs_evidence.csv`
7. `entity_conflicts.csv`
8. `unresolved_entities.csv`
9. `followup_questions.csv`
10. `sync_receipt.json`

## Run metrics

Record:

- records processed
- deterministic-only records
- Qwen calls
- Granite escalations
- 125B escalations
- visual-model calls
- OCR fallbacks
- invalid-schema rate
- unresolved-entity count
- unsupported-inference corrections
- tokens used per model
- total processing time

---

# ACCEPTANCE CRITERIA

V0 passes when:

- ≥98% outputs validate against schema
- every material fact retains provenance
- supplier claims remain separate from verified facts
- analytical test dimensions remain separate
- evidence independence is never inferred without support
- ambiguous entity merges are flagged
- no supplier recommendations are produced
- repeated ingestion does not duplicate evidence
- unchanged evidence can be detected without model inference
- <10% of routine records require 125B adjudication
- representative manual review shows low unsupported-inference rate

The system must prefer uncertainty over fabricated certainty.

---

# DOCUMENTATION

Record implementation and experiment results in:

- `AGENT_TRACKER.md`
- `AGENT_BRIEF.md`
- `RUNBOOK.md`

Include:

- model routing decisions
- failure examples
- schema changes
- false merges
- missed merges
- unsupported conclusions caught by Validator
- cases escalated to 125B
- cost/latency observations

Do not expand scope into purchasing, commerce, or supplier recommendation during V0.