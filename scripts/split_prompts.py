#!/usr/bin/env python3
"""Split contracts/COMPACT_RUNTIME_PROMPTS.md into per-worker prompt files.

Each runtime worker receives ONLY its own compact contract (plus schema + evidence
packet) — per the Compact Runtime Prompts layering rule. This script guarantees the
per-worker files in prompts/ stay byte-faithful to the contract layer.
"""
import os
import re
import sys

CONTRACT = os.path.join(os.path.dirname(__file__), "..", "contracts", "COMPACT_RUNTIME_PROMPTS.md")
OUTDIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

# H1 section title -> output filename
SECTION_MAP = [
    ("QWEN 27B", "qwen27b_extraction.md"),
    ("GRANITE 4.2 30B", "granite30b_skeptic.md"),
    ("QWEN 125B", "qwen125b_adjudicator.md"),
    ("QWEN-VL 32B", "qwen_vl_examiner.md"),
    ("GLM-OCR", "glm_ocr_fallback.md"),
    ("BGE-M3", "bge_m3_retriever.md"),
    ("DOSSIER SYNTHESIZER", "dossier_synthesizer.md"),
]

HEADER_PREAMBLE = "The Master Pack governs architecture. This is your persistent runtime contract. Follow it exactly."


def main():
    with open(CONTRACT, "r", encoding="utf-8") as f:
        text = f.read()

    # Split on top-level headings, keeping the heading with its section.
    parts = re.split(r"(?m)^(?=# )", text)
    matched = {}
    for part in parts:
        title_line = part.split("\n", 1)[0].lstrip("# ").strip()
        for key, fname in SECTION_MAP:
            if title_line.upper().startswith(key.upper()) and fname not in matched:
                matched[fname] = part.rstrip() + "\n"
                break

    os.makedirs(OUTDIR, exist_ok=True)
    written = []
    for _, fname in SECTION_MAP:
        if fname not in matched:
            print("MISSING SECTION: %s" % fname, file=sys.stderr)
            sys.exit(1)
        path = os.path.join(OUTDIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(matched[fname])
        written.append(fname)

    print("Wrote %d prompt files: %s" % (len(written), ", ".join(written)))


if __name__ == "__main__":
    main()
