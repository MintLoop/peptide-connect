"""Peptide Connect Supplier Intelligence V0.

Three-layer contract system:
- contracts/MASTER_PACK.md           — architecture (governs everything)
- contracts/COMPACT_RUNTIME_PROMPTS  — persistent per-worker contracts (prompts/)
- contracts/MOA_CONTRACT.md          — exceptional escalation governance (pcconnect/moa/)

Layers are deliberately separate; do not collapse them.
"""

__version__ = "0.1.0"
