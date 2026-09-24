"""B5 schema gate: validate fixture JSONs against the SHIPPED schemas (read-only)."""
import json
import os
import sys

import jsonschema

WS = "E:/ChimeraWork/mvc-20260924"
FIX = os.path.join(WS, "material_volume_campaign", "agents", "B5_subdivision", "fixtures")
ADMISSION_SCHEMA = os.path.join(WS, "tools", "material_volume_admission_schema.json")
GROUPS_SCHEMA = os.path.join(WS, "tools", "material_volume_body_export_schema.json")


def main():
    with open(ADMISSION_SCHEMA, encoding="utf-8") as fh:
        admission_schema = json.load(fh)
    with open(GROUPS_SCHEMA, encoding="utf-8") as fh:
        groups_schema = json.load(fh)
    results = []
    ok = True
    for level in ("l0", "l1", "l2", "l3"):
        for name, schema in (("manifest", admission_schema), ("partition", admission_schema),
                             ("groups", groups_schema)):
            path = os.path.join(FIX, f"{level}_{name}.json")
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            validator = jsonschema.Draft202012Validator(schema)
            errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
            passed = not errors
            ok &= passed
            results.append(f"{level}_{name}.json: {'PASS' if passed else 'FAIL'}")
            for error in errors[:5]:
                results.append(f"    {list(error.path)}: {error.message}")
    print("\n".join(results))
    print(f"TOTAL: {'12/12 PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
