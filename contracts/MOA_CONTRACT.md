# PEPTIDE CONNECT — MoA ESCALATION CONTRACT

This document governs **exceptional escalations only**. It is the third layer of the
system, separate from the Master Pack (architecture) and the Compact Runtime Prompts
(persistent worker contracts).

Routine work never consults this document. A worker that is unsure sets
`requires_validation=true` and stops; the router — not the worker — decides escalation.

---

## 1. Escalation authority

Only the **Escalation Router** (deterministic code, `pcconnect/moa/router.py`) may
promote a packet to a higher tier. Workers never escalate themselves, never invoke
other workers, and never retry each other's output.

## 2. Route classes

| Route    | Flow                                                          | Trigger |
|----------|---------------------------------------------------------------|---------|
| routine  | Adapter → Deterministic → Qwen 27B → Schema Validation → Store | `requires_validation=false`, schema-valid |
| questionable | Adapter → Deterministic → Qwen 27B → Granite 30B → Correct/Store | `requires_validation=true`, or Granite audit requested by policy |
| hard     | Adapter → Deterministic → Qwen 27B → Granite 30B → Qwen 125B → Store or HUMAN_REVIEW | Granite objection with `severity=HIGH` AND `adjudication_required=true` |
| visual   | Image → Qwen-VL → adequate? → Qwen 27B : (GLM-OCR → Qwen 27B) | image_document attachments |

## 3. Material-issue test (the 125B gate)

Qwen 125B is invoked **only** when ALL hold:

1. Granite returned a material objection (`severity=HIGH`, `adjudication_required=true`),
   or two independent evidence records conflict on a dossier-material field.
2. The disputed issue is one of:
   - difficult identity collision
   - conflicting corporate identities
   - manufacturer/trader dispute
   - certificate/entity conflict
   - disputed lot/report association
   - complex cross-source contradiction
   - unclear chain of custody
   - high-impact unresolved relationship
3. Resolving the issue would change the dossier (a field's stored value or state).

A LOW-confidence return from another worker is **not** an escalation trigger by itself.
Escalation without a material issue is a contract violation and is counted in run metrics
as `invalid_escalations`.

## 4. Adjudicator boundaries

- The 125B resolves **only the disputed issue** — it never re-extracts the packet.
- The original evidence outranks model opinions; model agreement is not evidence.
- Output must use exactly one decision state from the 7 canonical states.
- `human_review_required=true` routes to HUMAN_REVIEW; no automated overwrite.

## 5. Human review

HUMAN_REVIEW is a terminal state for the run. The packet is stored with its conflict
intact (never force-reconciled), listed in `unresolved_entities.csv` /
`entity_conflicts.csv`, and queued in `followup_questions.csv`. Nothing in the pipeline
may resolve it automatically afterward.

## 6. Non-goals

This contract does not govern supplier contact, purchasing, or commerce. It governs
evidence adjudication only.
