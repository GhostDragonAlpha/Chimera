"""DEFECT 9 -- gaps.py:49-66 emits ONE wall row PER bounds_region RELATION (no
dedup by wall id) and :66 sums n_support over those rows; the verdict at :73
is "physically bounded" iff n_support >= 2 and status == verified.  Because
relations preserve multiplicity BY DESIGN (store.relate), registering the SAME
single wall twice manufactures closure for a compartment that has exactly one
physical wall.

EXPECTED-HONEST: "physically bounded" must require DISTINCT bounding walls
(an enclosure needs more than one wall); duplicate relation rows pointing at
the same membrane must count once.  Observed with ONE wall registered once,
a verified compartment must NOT read "physically bounded".
OBSERVED (base a12bfbcc): the duplicate edge alone flips the verdict from
"boundary pending build" to "physically bounded"; bounding_membranes lists the
same membrane id twice.
"""

import json

import harness
import gaps

WALL = {
    "id": "memb.septum.solo", "kind": "surface",
    "name": "the compartment's ONLY wall",
    "classification": "type.A1", "status": "geometry_built", "priority": "P0",
    "spatial": None,
    "geometry": {"shape": "single wall", "is_placeholder": False},
    "physical": {"region_a": "region.solo", "region_b": "region.outside",
                 "law": "seal law"},
    "falsifier": {"statement": "not a seal until closure is proven",
                  "status": "untested"},
}
COMPARTMENT = {
    "id": "inst.comp.solo", "kind": "volume",
    "name": "solo compartment (one wall in the world)",
    "classification": "type.A1", "status": "verified", "priority": "P0",
    "spatial": None, "geometry": {"is_placeholder": False},
    "physical": {"region_a": "region.solo", "law": "P = -(V-V0)/(kappa*V0)"},
    "falsifier": {"statement": "sealed iff conserved", "status": "passing"},
}
REGION_SOLO = {
    "id": "region.solo", "kind": "region", "name": "solo region",
    "status": "specified", "priority": "P1",
}
REGION_OUTSIDE = {
    "id": "region.outside", "kind": "region", "name": "outside the wall",
    "status": "specified", "priority": "P1",
}


def _store(n_wall_registrations):
    return harness.min_store(
        objects=[WALL, COMPARTMENT, REGION_SOLO, REGION_OUTSIDE],
        relations=[("memb.septum.solo", "bounds_region", "region.solo",
                    "the one wall") ] * n_wall_registrations,
    )


def run():
    # control: the honest world -- one wall registered ONCE
    one = gaps.q_unsupported_boundaries(_store(1))
    row_one = [r for r in one if r["compartment"] == "inst.comp.solo"][0]

    # the defect: the SAME wall registered twice (multiplicity is by design)
    two = gaps.q_unsupported_boundaries(_store(2))
    row_two = [r for r in two if r["compartment"] == "inst.comp.solo"][0]

    supports = [w["membrane"] for w in row_two["bounding_membranes"]
                if w["physically_supported"]]
    reproduced = (
        row_one["verdict"] == "boundary pending build"
        and row_two["verdict"] == "physically bounded"
        and supports == ["memb.septum.solo", "memb.septum.solo"]
    )
    return harness.verdict(
        defect="D9",
        title="duplicate boundary edges manufacture closure (no wall-id dedup; "
              "n_support sums relation rows)",
        expected_honest="closure must count DISTINCT walls: one wall registered "
                        "twice is one wall, verdict stays 'boundary pending "
                        "build' (an enclosure needs >1 wall)",
        observed="one registration -> 'boundary pending build'; the SAME wall "
                 "registered twice -> 'physically bounded'; "
                 "bounding_membranes lists memb.septum.solo twice",
        reproduced=reproduced,
        evidence={
            "one_registration": {
                "verdict": row_one["verdict"],
                "bounding_membranes": row_one["bounding_membranes"],
            },
            "two_registrations": {
                "verdict": row_two["verdict"],
                "bounding_membranes": row_two["bounding_membranes"],
            },
            "supported_rows_duplicate_case": supports,
            "code_refs": "gaps.py:49-66 (per-relation rows), :66 (n_support sum), "
                         ":73 (verdict iff n_support>=2 and verified)",
        },
        contract_refs=["gaps.py:37-79", "store.py:63-72 (multiplicity by design)"],
    )


def test_defect_9_reproduced():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
