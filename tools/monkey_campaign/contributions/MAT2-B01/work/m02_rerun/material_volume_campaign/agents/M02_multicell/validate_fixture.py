"""Validate the M02 fixture documents against the EXISTING shipped schemas.

Read-only with respect to tools/ (schemas are loaded, never modified).
Exit 0 = all three documents validate; nonzero = validation failure (preserved).
"""
from __future__ import annotations

import json
import os
import sys

import jsonschema

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

ADMISSION_SCHEMA = os.path.join(WS, "tools", "material_volume_admission_schema.json")
GROUPS_SCHEMA = os.path.join(WS, "tools", "material_volume_body_export_schema.json")
FIX = os.path.join(HERE, "fixtures")


def main():
    with open(ADMISSION_SCHEMA, encoding="utf-8") as fh:
        admission_schema = json.load(fh)
    with open(GROUPS_SCHEMA, encoding="utf-8") as fh:
        groups_schema = json.load(fh)

    results = []
    ok = True
    checks = [
        ("mc_manifest.json", admission_schema),
        ("mc_partition.json", admission_schema),
        ("mc_groups.json", groups_schema),
    ]
    for name, schema in checks:
        with open(os.path.join(FIX, name), encoding="utf-8") as fh:
            doc = json.load(fh)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
        if errors:
            ok = False
            for e in errors:
                results.append(f"FAIL {name}: {'/'.join(map(str, e.path))}: {e.message}")
        else:
            results.append(f"PASS {name}: valid against {schema.get('$id', '?')}")

    # also validate each manifest/partition against its SPECIFIC definition
    with open(os.path.join(FIX, "mc_manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    with open(os.path.join(FIX, "mc_partition.json"), encoding="utf-8") as fh:
        partition = json.load(fh)
    for name, doc, key in (("mc_manifest.json", manifest, "fittingManifest"),
                           ("mc_partition.json", partition, "materialPartition")):
        sub = dict(admission_schema)
        sub["$ref"] = f"#/$defs/{key}"
        sub.pop("oneOf", None)
        errors = sorted(jsonschema.Draft202012Validator(sub).iter_errors(doc),
                        key=lambda e: list(e.path))
        if errors:
            ok = False
            for e in errors:
                results.append(f"FAIL {name} vs {key}: {e.message}")
        else:
            results.append(f"PASS {name}: valid against $defs/{key}")

    print(f"jsonschema version: {jsonschema.__version__ if hasattr(jsonschema, '__version__') else 'n/a'}")
    for line in results:
        print(line)
    print("SCHEMA VALIDATION:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
