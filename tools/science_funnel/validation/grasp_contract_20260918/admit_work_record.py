"""Idempotent Rule-0 admission for the bounded grasp contract.

This script reconciles the small authored project program and then rebuilds the
canonical graph through tools/creature_graph/build_graph.py. It admits a
contract and a derivation; it does not implement or verify runtime grasping.

Run from the repository root with the assigned project Python:
  python -m tools.science_funnel.validation.grasp_contract_20260918.admit_work_record
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PROGRAM = os.path.join(ROOT, "tools", "creature_graph", "data", "authored",
                       "project_program.json")
BASE_COMMIT = "4b047609c8f51782da10c9d63726f10ddb525cbc"
ADMITTED_UTC = "2026-09-18T03:30:00+00:00"
SOURCE_ID = "source.operator.coupled_arm_grasp_20260918"
WORK_ID = "work.creature.coupled_arm_grasp"

SOURCE = {
    "id": SOURCE_ID,
    "kind": "source",
    "name": "Operator dispatches the bounded coupled-arm grasp contract",
    "status": "extracted",
    "physical": {
        "text": "Admit the bounded grasp membrane before any runtime implementation: "
                "a spherical hand proxy between two opposing parallel planes, a "
                "finite squeeze store, anti-parallel friction rows, and a capped "
                "catch impulse.",
        "selection": "GRASP-CONTRACT lane brief, branched from origin/master at "
                     + BASE_COMMIT + ".",
    },
}

WORK = {
    "id": WORK_ID,
    "kind": "work",
    "name": "Derive and admit the bounded two-coordinate arm grasp contract",
    "status": "specified",
    "priority": "P0",
    "dependencies": ["model.dynamics.coupled_arm"],
    "evidence": [],
    "falsifier": {
        "statement": "The grasp contract is false if any of its four preregistered "
                     "energy, cone, release-control, or zero-squeeze controls fails "
                     "when the future runtime slice is implemented.",
        "status": "preregistered",
        "tests": [
            "A grasp that pulls the planes together without a store debit is not grasp (energy falsifier).",
            "|f_pair| <= mu*(lambda_n1+lambda_n2) cone always.",
            "Releasing one plane returns EXACTLY the qualified frictionless/contact control bit-for-bit.",
            "Zero-squeeze grasp is bit-identically the qualified friction world.",
        ],
    },
    "physical": {
        "statement": "For a fixed-root shoulder/elbow arm, the grasp reaction pair and "
                     "its squeeze store can be written as a bounded, energy-accounted "
                     "contact contract without claiming that opposing parallel-plane "
                     "rows span both joint coordinates.",
        "prediction": "At the settled 20/20 pose the opposing plane rows have rank one "
                      "with determinant below numerical precision; an independent "
                      "normal/tangent pair has a nonzero mass-metric determinant, and "
                      "the capped catch removes normal closing velocity while its "
                      "normal/tangential dissipation split closes exactly.",
        "contract": {
            "schema": "chimera.grasp_contract.v1",
            "base_commit": BASE_COMMIT,
            "derivation": "docs/research/20260918_grasp_derivation.md",
            "prestudy": "tools/science_funnel/validation/grasp_contract_20260918/prestudy.json",
            "prestudy_script": "tools/science_funnel/validation/grasp_contract_20260918/prestudy.py",
            "qualified_controls": [
                "tools/science_funnel/validation/coupled_contact_20260917/receipt.json",
                "tools/science_funnel/validation/coupled_friction_20260917/receipt.json",
            ],
            "geometry": {
                "proxy": "sphere",
                "planes": "opposing parallel planes",
                "pair_is_reaction_pair": True,
                "normal_rows": "a and -a",
                "two_dof_full_rank_requires": "a second effective row b with det([a;b]) != 0",
            },
            "law": [
                "g1=n·x+d/2-r and g2=d/2-n·x-r are unilateral gaps.",
                "G_pair=[a;-a], a=n^T J; opposing parallel planes are rank <= 1.",
                "Squeeze work is integral F_s dδ and debits a finite store; opening returns no credit.",
                "Stick KKT uses A_ij=row_i M^-1 row_j^T and factorized det(A)=A_nn A_tt-A_nt^2.",
                "The pair Coulomb cone is |f_pair| <= mu*(lambda_n1+lambda_n2).",
                "A capped catch re-solves normal impulse after tangential clipping using exact M^-1 cross-coupling.",
            ],
            "owned_files": [
                "ChimeraEngine/engine/coupled_dynamics.hpp",
                "ChimeraEngine/engine/tests_coupled_arm/native.cpp",
                "tools/science_funnel/coupled_scene.py",
                "tools/science_funnel/tests/test_coupled_arm.py",
                "tools/science_funnel/tests/test_coupled_scene.py",
                "tools/science_funnel/tests/qualify_coupled_live.py",
                "tools/science_funnel/validation/grasp_contract_20260918/",
            ],
            "not_implemented": [
                "no runtime grasp state or engine code in this admission",
                "no coupled_dynamics.hpp edit in this lane",
                "no free-root, whole-animal, muscle, distributed-contact, rolling, wrapping, or GPU claim",
                "no claim that two opposing parallel planes immobilize both DOF",
                "no implementation-level bit-identity result beyond the prior qualified controls",
                "prior friction receipt independent-review minor findings remain open and are not promoted",
            ],
        },
    },
    "project_spec": {
        "schema": "chimera.project_spec.v1",
        "admission": "active_specification",
        "category": "work",
        "origin_id": SOURCE_ID,
        "admitted_utc": ADMITTED_UTC,
        "authorization": "Operator GRASP-CONTRACT lane brief",
        "authority_scope": "Derivation and Rule-0 admission only; no runtime qualification.",
    },
}

RELATION = {
    "src": WORK_ID,
    "rel": "derived_from",
    "dst": SOURCE_ID,
    "note": "Operator-directed bounded grasp contract admission",
}


def reconcile_program() -> list[str]:
    with open(PROGRAM, encoding="utf-8-sig") as stream:
        program = json.load(stream)
    changed: list[str] = []
    known = {obj["id"]: obj for obj in program["objects"]}
    for obj in (SOURCE, WORK):
        if known.get(obj["id"]) != obj:
            if obj["id"] in known:
                program["objects"] = [obj if old["id"] == obj["id"] else old
                                      for old in program["objects"]]
                changed.append(obj["id"] + " (updated to declared state)")
            else:
                program["objects"].append(obj)
                changed.append(obj["id"] + " (admitted)")
    edges = {(edge["src"], edge["rel"], edge["dst"], edge.get("note", ""))
             for edge in program["relations"]}
    key = (RELATION["src"], RELATION["rel"], RELATION["dst"], RELATION["note"])
    if key not in edges:
        program["relations"].append(dict(RELATION))
        changed.append("relation " + WORK_ID + " -> " + SOURCE_ID)
    if changed:
        raw = (json.dumps(program, ensure_ascii=False, indent=1) + "\n").encode()
        with open(PROGRAM, "wb") as stream:
            stream.write(raw)
    return changed


def main() -> int:
    changed = reconcile_program()
    sys.path.insert(0, os.path.join(ROOT, "tools", "creature_graph"))
    import build_graph

    graph = build_graph.build()
    errors = graph.check()
    if errors:
        raise SystemExit("store check FAILED:\n  " + "\n  ".join(errors))
    path = graph.save()
    print("admission:", "; ".join(changed) if changed else "no-op")
    print("rebuilt", os.path.normpath(path), "objects", len(graph.objects),
          "relations", len(graph.relations), "graph_hash", graph.graph_hash())
    print("declared_utc", datetime.now(timezone.utc).isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
