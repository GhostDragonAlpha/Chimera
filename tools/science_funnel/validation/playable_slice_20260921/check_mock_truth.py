"""check_mock_truth.py -- F-SLICE-MOCK-TRUTH (grep-auditable, both directions).

The mock registry is the honesty contract: the set of MOCK[id] and
DECLARED[id] marker tokens in the slice's code must EQUAL the registry's
fantasy + declared id sets, exactly. A mock site without a registry entry, or
a registry entry without a code site, is FAIL.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"
CODE_FILES = ["scene_boot.py", "slice_server.py", "index.html",
              "run_slice.ps1", "PlayableSlice.bat", "mock_registry.json"]

MOCK_RE = re.compile(r"MOCK\[([a-z0-9_]+)\]")
DECL_RE = re.compile(r"DECLARED\[([a-z0-9_]+)\]")


def main() -> int:
    reg = json.loads((SLICE / "mock_registry.json").read_text(encoding="utf-8"))
    reg_mock = {m["id"] for m in reg["fantasy"]}
    reg_decl = {d["id"] for d in reg["declared"]}

    code_mock: dict[str, list[str]] = {}
    code_decl: dict[str, list[str]] = {}
    for name in CODE_FILES:
        p = SLICE / name
        text = p.read_text(encoding="utf-8")
        for m in MOCK_RE.finditer(text):
            code_mock.setdefault(m.group(1), []).append(f"{name}:{text[:m.start()].count(chr(10)) + 1}")
        for m in DECL_RE.finditer(text):
            code_decl.setdefault(m.group(1), []).append(f"{name}:{text[:m.start()].count(chr(10)) + 1}")

    missing_in_registry = sorted(set(code_mock) - reg_mock)
    missing_in_code = sorted(reg_mock - set(code_mock))
    missing_decl_registry = sorted(set(code_decl) - reg_decl)
    missing_decl_code = sorted(reg_decl - set(code_decl))

    ok = not (missing_in_registry or missing_in_code
              or missing_decl_registry or missing_decl_code)
    out = {
        "falsifier": "F-SLICE-MOCK-TRUTH",
        "pass": ok,
        "registry_fantasy_ids": sorted(reg_mock),
        "registry_declared_ids": sorted(reg_decl),
        "code_mock_sites": code_mock,
        "code_declared_sites": code_decl,
        "mocks_in_code_not_registry": missing_in_registry,
        "registry_mocks_without_code_site": missing_in_code,
        "declared_in_code_not_registry": missing_decl_registry,
        "registry_declared_without_code_site": missing_decl_code,
    }
    (HERE / "mock_truth.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
