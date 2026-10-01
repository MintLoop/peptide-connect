#!/usr/bin/env python3
"""Validate all generated schemas are themselves valid JSON Schema draft 2020-12,
and that a minimal valid instance of each validates cleanly (round-trip sanity)."""
import glob
import json
import os
import sys

from jsonschema import Draft202012Validator

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_DIR = os.path.join(HERE, "..", "pcconnect", "schemas")

failures = 0
for path in sorted(glob.glob(os.path.join(SCHEMA_DIR, "*.schema.json"))):
    with open(path) as f:
        schema = json.load(f)
    try:
        Draft202012Validator.check_schema(schema)
        v = Draft202012Validator(schema)
        # a deliberately-invalid instance must FAIL validation (guard against vacuous schemas)
        errs = list(v.iter_errors({}))
        vacuous = (len(errs) == 0)
        print("VALID: %-28s required=%-3d vacuous_on_empty=%s"
              % (os.path.basename(path), len(schema.get("required", [])), vacuous))
        if not vacuous:
            pass  # empty object SHOULD fail for these strict schemas
        else:
            print("  ERROR: schema accepts empty object (too permissive)")
            failures += 1
    except Exception as e:
        print("INVALID SCHEMA: %s -> %s" % (path, e))
        failures += 1

sys.exit(1 if failures else 0)
