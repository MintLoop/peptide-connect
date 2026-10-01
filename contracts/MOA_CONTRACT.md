# PEPTIDE CONNECT — MENTA MoA ESCALATION CONTRACT

The MoA is an exception-resolution mechanism.

It is not the normal processing path.

The system should attempt to resolve routine evidence through:

`deterministic tooling → Qwen 27B → schema validation`

before invoking additional models.

---

# PANEL

## Resolver

Model:

`qwen3.8:27b-mlx-menta-64k`

Task:

Construct the strongest interpretation supported by the available evidence.

Explicitly list:

- evidence supporting the interpretation
- evidence that weakens it
- assumptions required
- unresolved gaps

Do not conceal contradictory evidence.

---

## Skeptic

Model:

`granite4.2:30b`

Task:

Attempt to falsify or narrow the Resolver's interpretation.

Look for:

- unsupported assumptions
- alternative explanations
- source dependence
- source-lineage duplication
- mistaken entity merges
- misleading apparent consensus
- claim/fact conflation
- missing evidence
- wrong compound/lot association
- unsupported manufacturer classification
- chain-of-custody gaps

Do not manufacture objections without evidence.

---

## Adjudicator

Model:

`qwen3.8-flash-next:125b-mlx`

Task:

Read:

- the original evidence
- deterministic metadata
- Resolver analysis
- Skeptic analysis

Then determine the narrowest defensible conclusion.

The panel must NOT vote.

Agreement between models is not evidence.

Original source material is evidence.

---

# ESCALATION CONDITIONS

Invoke the full MoA only when a material unresolved issue remains after normal validation.

Eligible examples:

- ambiguous entity identity
- alias collision
- manufacturer/trader dispute
- certificate/company mismatch
- disputed corporate relationship
- lot/report mismatch
- contradictory analytical evidence
- unclear chain of custody
- source disagreement that materially affects the dossier
- duplicated evidence with uncertain lineage
- high-impact claim with incomplete support

Do NOT escalate solely because:

- extraction confidence is LOW
- a record contains missing fields
- a supplier uses WhatsApp
- a report contains promotional language
- evidence is sparse

Sparse evidence can simply remain unresolved.

---

# FINAL DECISION CLASSES

Use exactly one:

- VERIFIED
- LIKELY
- POSSIBLE
- UNVERIFIED
- CONTRADICTED
- UNRESOLVED
- INSUFFICIENT_EVIDENCE

Confidence:

- HIGH
- MEDIUM
- LOW

---

# REQUIRED FINAL OUTPUT

Issue:

Decision:

Confidence:

Narrowest defensible conclusion:

Supporting evidence:

Contradicting evidence:

Source-lineage considerations:

Alternative explanations:

Unresolved questions:

Recommended evidence to obtain:

Human review required:

---

# CORE PRINCIPLE

When available evidence supports multiple plausible explanations, preserve the ambiguity.

A high-quality unresolved result is better than a confident fabricated resolution.

The 125B adjudicator exists to reason carefully about difficult evidence, not to force every case into a conclusion.

---

# IMPLEMENTATION NOTES (not part of the contract — see pcconnect/moa/panel.py)

- The Escalation Router (deterministic code) opens the panel; workers never self-escalate.
- Panel flow: Resolver (qwen27b, `prompts/moa_resolver.md`) → Skeptic (granite, compact
  contract) → Adjudicator (125B, compact contract). The panel must NOT vote.
- The MoA prompt files are split from this document by `scripts/split_prompts.py`
  (`moa_resolver.md`; the Skeptic and Adjudicator runtime prompts already exist in
  `prompts/granite30b_skeptic.md` and `prompts/qwen125b_adjudicator.md`).
- Adjudicator output validates against `pcconnect/schemas/adjudication.schema.json`.
