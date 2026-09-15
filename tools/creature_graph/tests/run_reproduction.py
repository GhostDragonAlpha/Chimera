"""Plain-python runner for the F2 graph-regression suite (also runs under pytest).

Usage:
  python tests/run_reproduction.py            # run all, print verdict table,
                                              # rewrite tests/reproduction_output.json
  python tests/run_reproduction.py D1 D9      # run a subset by defect id

Suite convention: each module's run() returns a verdict dict.  "REPRODUCED"
means the defect's observed behavior differs from the architectural contract
(the defect is live on this base); "REFUTED" means the measurement exonerates
it.  The pytest wrappers assert REPRODUCED, so a future repair turns the suite
red -- that is the signal to update REPRODUCTION_REPORT.md and CODEX_PACKET.md.
"""

import importlib
import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

import harness  # noqa: E402  (also puts tools/creature_graph on sys.path)

MODULES = [
    "test_d1_physics_fields_omit_value",
    "test_d2_relation_capture_missing",
    "test_d3_empty_capture_passes",
    "test_d4_rebuild_restamps_capture",
    "test_d5_projection_id_collision",
    "test_d6_load_ignores_schema_version",
    "test_d7_greedy_cell_matching",
    "test_d8_conservation_falsy_zero",
    "test_d9_duplicate_boundary_closure",
    "test_qs_query_semantics",
]

OUTPUT_PATH = os.path.join(TESTS_DIR, "reproduction_output.json")


def main(argv):
    wanted = set(argv)
    results = []
    for name in MODULES:
        mod = importlib.import_module(name)
        v = mod.run()
        if wanted and v["defect"] not in wanted:
            continue
        results.append(v)
        mark = {"REPRODUCED": "REPRODUCED", "REFUTED": "REFUTED "}[v["verdict"]]
        print(f"[{mark}] {v['defect']}: {v['title']}")
        print(f"          expected-honest: {v['expected_honest']}")
        print(f"          observed       : {v['observed']}")
        if v["verdict"] != "REPRODUCED":
            print(f"          !! measured exoneration -- update the report")

    n = len(results)
    n_ok = sum(1 for r in results if r["verdict"] == "REPRODUCED")
    print(f"\n{n} run: {n_ok} REPRODUCED, {n - n_ok} REFUTED "
          f"(base a12bfbcc; REPRODUCED = defect live)")

    payload = {
        "suite": "F2-graph-regressions adversarial reproduction suite",
        "base_commit": "a12bfbcc494a273b4739f86a83e19001343ee70c",
        "branch": "glm53/graph-tests",
        "schema_version_under_test": "2.0.0",
        "convention": "REPRODUCED = observed behavior violates the architectural "
                      "contract stated per test (defect live on this base); "
                      "REFUTED = measured exoneration",
        "results": results,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False, default=str)
    print(f"recorded: {os.path.normpath(OUTPUT_PATH)}")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
