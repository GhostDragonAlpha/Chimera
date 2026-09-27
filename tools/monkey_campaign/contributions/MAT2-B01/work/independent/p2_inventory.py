"""P2 — unique-test inventory over the frozen modules at 1af0bbde.

Re-executes verification-receipt check V2 independently: unique identity =
(module, qualified name), enumerated by unittest discovery over the exact
frozen module bytes (blob-form extraction). Discovery only; no test is
executed by this script. Falsifier F-B01-2 fires unless the split is exactly
17/21/8/5/8/7 (total 66).
"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "frozen" / "1af0bbde" / "tools"
RUNS = HERE.parent / "runs"

EXPECTED = {
    "material_volume_checks": 17,
    "material_volume_admission_checks": 21,
    "material_volume_body_export_checks": 8,
    "material_volume_shared_interface_proof": 5,
    "material_volume_frame_composition_proof": 8,
    "material_volume_export_proof_verify": 7,
}

sys.path.insert(0, str(TOOLS))


def qualified_names(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from qualified_names(item)
        else:
            yield f"{item.__class__.__module__}.{item.id()}"


def main():
    inventory = {}
    for mod_name, expected in EXPECTED.items():
        module = __import__(mod_name)
        suite = unittest.TestLoader().loadTestsFromModule(module)
        names = sorted(set(qualified_names(suite)))
        inventory[mod_name] = {"count": len(names), "expected": expected,
                               "names": names}
    total = sum(v["count"] for v in inventory.values())
    ok = total == 66 and all(v["count"] == v["expected"]
                             for v in inventory.values())
    RUNS.mkdir(parents=True, exist_ok=True)
    with open(RUNS / "p2_inventory.json", "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump({"total": total, "ok": ok, "inventory": inventory}, fh,
                  indent=1)
    for mod, v in inventory.items():
        print(f"{mod}: {v['count']} (expected {v['expected']})")
    print(f"total unique identities: {total} (expected 66); "
          f"F-B01-2 fired: {not ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
