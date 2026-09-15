"""DEFECT 7 -- runtime-to-graph matching chooses ambiguous cells greedily.

engine_live.map_cells_to_instances (lines 127-142) takes matches[0] with no
ambiguity flag, so two graph instances claiming the same band BOTH join the
same live cell and a matching cell goes unused.  engine_live.cross_check
(lines 66-74) excludes already-used cells but is STILL greedy: instance order
decides which cell each instance gets, with no ambiguity flag -- a wrong-cell
assignment decides pass/fail even when a perfect assignment existed.

EXPECTED-HONEST: band-matching ambiguity MUST be surfaced (e.g.
match: "ambiguous N candidates" and no silent engine_cell_index), and a
verification verdict must not depend on instance iteration order when a
consistent assignment exists.
OBSERVED (base a12bfbcc): with two verified instances at band [0, 0.338] and
two live cells at the same band carrying each other's v0, BOTH instances fail
their v0 check under cross_check although the consistent assignment
(_a->cell1, _b->cell0) exists; map_cells_to_instances double-books cell 0 and
never mentions the ambiguity.
"""

import json

import harness
import engine_live


BAND = [0.0, 0.338]
V0_A = 0.287914
V0_B = 0.105210

INSTANCES = [
    {"id": "inst.band.feet_a", "kind": "volume", "name": "feet band sub A",
     "classification": "type.A1", "status": "verified", "priority": "P0",
     "spatial": {"band_y": list(BAND), "v0_m3": V0_A},
     "physical": {"region_a": "region.feet_a", "law": "P = -(V-V0)/(kappa*V0)"},
     "falsifier": {"statement": "sealed iff conserved", "status": "passing"}},
    {"id": "inst.band.feet_b", "kind": "volume", "name": "feet band sub B",
     "classification": "type.A1", "status": "verified", "priority": "P0",
     "spatial": {"band_y": list(BAND), "v0_m3": V0_B},
     "physical": {"region_a": "region.feet_b", "law": "P = -(V-V0)/(kappa*V0)"},
     "falsifier": {"statement": "sealed iff conserved", "status": "passing"}},
]

# cell 0 carries B's v0, cell 1 carries A's v0 (a perfect assignment exists)
CELLS = [
    {"ylo": BAND[0], "yhi": BAND[1], "v0": V0_B, "V": V0_B, "degenerate": False},
    {"ylo": BAND[0], "yhi": BAND[1], "v0": V0_A, "V": V0_A, "degenerate": False},
]


def run():
    g = harness.min_store(objects=INSTANCES)
    tick = {"cells": [dict(c) for c in CELLS], "n_cells": 2, "sealed": True,
            "seal_refusal": None, "conserve_pct": 1e-6, "V_whole": V0_A + V0_B,
            "ts_us": 1, "ticks": 731615}

    # -- inspection join: greedy matches[0], no used-exclusion, no flag
    rows = engine_live.map_cells_to_instances(g, tick)
    join = [
        {"graph_id": r["graph_id"], "engine_cell_index": r["engine_cell_index"],
         "match": r["match"], "live_V_m3": r["live_V_m3"]}
        for r in rows
    ]

    # -- verification: greedy WITH used-exclusion, still order-dependent
    report = engine_live.cross_check(g, tick)
    v0_checks = [
        {"check": c["check"], "ok": c["ok"], "detail": c["detail"]}
        for c in report["checks"] if "v0 matches" in c["check"]
    ]
    both_failed = all(not c["ok"] for c in v0_checks) and len(v0_checks) == 2
    any_ambiguity_flag = any(
        "ambiguous" in json.dumps(c).lower() for c in report["checks"]
    ) or any("ambiguous" in json.dumps(r).lower() for r in rows)

    reproduced = (
        join[0]["engine_cell_index"] == join[1]["engine_cell_index"] == 0
        and join[0]["match"] == "by band geometry"        # no ambiguity surfaced
        and not any_ambiguity_flag
        and both_failed
    )
    return harness.verdict(
        defect="D7",
        title="runtime-to-graph matching chooses ambiguous cells greedily "
              "(matches[0]; used-exclusion in cross_check is still greedy/unflagged)",
        expected_honest="ambiguous band matches MUST be flagged and MUST NOT "
                        "silently decide pass/fail when a consistent assignment "
                        "exists (join both instances to distinct cells, or "
                        "report 'ambiguous: N candidates')",
        observed="map_cells_to_instances double-books live cell 0 (both rows "
                 "engine_cell_index=0, cell 1 unused, match='by band geometry'); "
                 "cross_check fails BOTH v0 checks under greedy used-exclusion "
                 "although the perfect assignment (_a->cell1, _b->cell0) exists; "
                 "no ambiguity flag anywhere",
        reproduced=reproduced,
        evidence={
            "join_rows": join,
            "cross_check_v0_checks": v0_checks,
            "cross_check_pass": report["pass"],
            "consistent_assignment_exists": True,
            "cells_offered": CELLS,
            "code_refs": "engine_live.py:129/139/142 (join), :65-74 (cross_check)",
        },
        contract_refs=["engine_live.py:116-153", "engine_live.py:55-86"],
    )


def test_defect_7_reproduced():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
