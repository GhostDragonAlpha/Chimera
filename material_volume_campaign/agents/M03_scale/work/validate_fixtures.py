"""M03: validate every fixture document against the EXISTING schema files in
tools/ (read-only usage). Exits nonzero on any validation failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parent
FIXTURES = AGENTS / "fixtures"
TOOLS = AGENTS.parents[2] / "tools"

ADMISSION_SCHEMA = TOOLS / "material_volume_admission_schema.json"
GROUPS_SCHEMA = TOOLS / "material_volume_body_export_schema.json"


def main() -> int:
    admission_schema = json.loads(ADMISSION_SCHEMA.read_text(encoding="utf-8"))
    groups_schema = json.loads(GROUPS_SCHEMA.read_text(encoding="utf-8"))
    failures = 0
    for path in sorted(FIXTURES.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        if path.name == "groups.json":
            schema, validator = groups_schema, jsonschema.Draft202012Validator
        else:
            schema, validator = admission_schema, jsonschema.Draft202012Validator
        errors = sorted(validator(schema).iter_errors(document), key=lambda e: e.path)
        if errors:
            failures += len(errors)
            print(f"FAIL {path.name}")
            for error in errors:
                print(f"  {'/'.join(map(str, error.path))}: {error.message}")
        else:
            print(f"PASS {path.name}")
    print("schema validation:", "FAILED" if failures else "ALL PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
