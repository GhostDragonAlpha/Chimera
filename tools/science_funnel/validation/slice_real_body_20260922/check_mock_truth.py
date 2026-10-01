"""check_mock_truth.py -- F-SLICE-MOCK-TRUTH (grep-auditable, both directions).

The slice's own honesty contract, re-run after the real-body upgrade: the set
of MOCK[id] and DECLARED[id] marker tokens in the slice's code must EQUAL the
registry's fantasy + declared id sets, exactly. Plus the retirement audit the
upgrade names: mock_physics_body must have ZERO code sites anywhere in the
slice files (one fewer mock, grep-auditable), and its retirement must be
recorded in the registry.
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
RETIRED_ID = "mock_physics_body"


def main() -> int:
    reg = json.loads((SLICE / "mock_registry.json").read_text(encoding="utf-8"))
    reg_mock = {m["id"] for m in reg["fantasy"]}
    reg_decl = {d["id"] for d in reg["declared"]}

    code_mock: dict[str, list[str]] = {}
    code_decl: dict[str, list[str]] = {}
    retired_token_sites: list[str] = []
    retired_prose_hits: list[str] = []
    for name in CODE_FILES:
        p = SLICE / name
        text = p.read_text(encoding="utf-8")
        for m in MOCK_RE.finditer(text):
            code_mock.setdefault(m.group(1), []).append(f"{name}:{text[:m.start()].count(chr(10)) + 1}")
        for m in DECL_RE.finditer(text):
            code_decl.setdefault(m.group(1), []).append(f"{name}:{text[:m.start()].count(chr(10)) + 1}")
        if MOCK_RE.search(text) and RETIRED_ID in {m.group(1) for m in MOCK_RE.finditer(text)}:
            retired_token_sites.append(name)
        if RETIRED_ID in text and name != "mock_registry.json":
            retired_prose_hits.append(name)

    missing_in_registry = sorted(set(code_mock) - reg_mock)
    missing_in_code = sorted(reg_mock - set(code_mock))
    missing_decl_registry = sorted(set(code_decl) - reg_decl)
    missing_decl_code = sorted(reg_decl - set(code_decl))
    retired_gone = len(retired_token_sites) == 0 and RETIRED_ID not in reg_mock
    retired_recorded = any(r.get("id") == RETIRED_ID for r in reg.get("retired", []))
    one_fewer_mock = reg_mock == {"mock_carry"}

    ok = not (missing_in_registry or missing_in_code
              or missing_decl_registry or missing_decl_code) \
        and retired_gone and retired_recorded and one_fewer_mock
    out = {
        "falsifier": "F-SLICE-MOCK-TRUTH",
        "pass": bool(ok),
        "registry_fantasy_ids": sorted(reg_mock),
        "registry_declared_ids": sorted(reg_decl),
        "registry_reality_ids": sorted(r["id"] for r in reg["reality"]),
        "code_mock_sites": code_mock,
        "code_declared_sites": code_decl,
        "mocks_in_code_not_registry": missing_in_registry,
        "registry_mocks_without_code_site": missing_in_code,
        "declared_in_code_not_registry": missing_decl_registry,
        "registry_declared_without_code_site": missing_decl_code,
        "retirement": {
            "id": RETIRED_ID,
            "mock_token_sites_remaining": retired_token_sites,
            "prose_mentions_recorded_for_transparency": retired_prose_hits,
            "gone_from_code_and_fantasy": retired_gone,
            "recorded_in_registry_retired": retired_recorded,
            "one_fewer_mock": one_fewer_mock,
            "before": ["mock_carry", "mock_physics_body"],
            "after": sorted(reg_mock),
        },
    }
    (HERE / "mock_truth.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
