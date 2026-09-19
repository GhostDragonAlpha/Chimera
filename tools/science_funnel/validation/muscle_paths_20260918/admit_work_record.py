"""Idempotent Rule-0 admission for the muscle path geometry derivation.

Adds to the authored program:
  source.operator.muscle_paths_20260918     -- the lane brief as source
  work.creature.muscle_path_geometry        -- the Rule-0 work record (active
                                               specification, category work)
  model.creature.muscle_path_geometry       -- the derived geometry record
                                               (the deliverable JSON payload,
                                               content-sha pinned)
then rebuilds the canonical graph through tools/creature_graph/build_graph.py.

Run from the repository root with the assigned project Python:
  python -m tools.science_funnel.validation.muscle_paths_20260918.admit_work_record
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PROGRAM = os.path.join(ROOT, "tools", "creature_graph", "data", "authored",
                       "project_program.json")
BASE_COMMIT = "c43d3363"
ADMITTED_UTC = "2026-09-18T10:00:00+00:00"
SOURCE_ID = "source.operator.muscle_paths_20260918"
WORK_ID = "work.creature.muscle_path_geometry"
MODEL_ID = "model.creature.muscle_path_geometry"
DELIVERABLE = os.path.join(HERE, "muscle_path_geometry.json")
DOC = "docs/research/20260918_muscle_path_derivation.md"
RECEIPT = ("tools/science_funnel/validation/muscle_paths_20260918/"
           "receipt.json")

FALSIFIER_RESULTS = {
    "arm_consistency": "held (worst |r_geometric - (-dL/dq)| 4.3e-10 m on "
                       "straight paths, 39 muscles x 7 coordinates x 2 poses)",
    "conditional_continuity": "held (measured jump 1.0e-4 m, bound 5e-3 m)",
    "hindlimb_torque_coverage": "partly falsified (held: hip_extension 17.9x, "
                                "hip_flexion 2.6x, knee_flexion 4.6x, "
                                "ankle_dorsiflexion 108.6x, "
                                "ankle_plantarflexion 0.82x within the "
                                "declared 25% uncertainty; FALSIFIED: "
                                "knee_extension and mtp_flexion - the "
                                "straight-line proxy has no patella and no "
                                "mtp pulley)",
}


def _deliverable():
    with open(DELIVERABLE, encoding="utf-8") as stream:
        return json.load(stream)


def _sha(path):
    with open(path, "rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def build_objects():
    deliverable = _deliverable()
    deliverable_sha = _sha(DELIVERABLE)
    source = {
        "id": SOURCE_ID,
        "kind": "source",
        "name": "Operator dispatches the MUSCLE-PATHS derivation lane",
        "status": "extracted",
        "physical": {
            "text": "Derive macaque muscle path geometry from the pinned "
                    "arm model and the Guimaraes/Oku hindlimb data: extract "
                    "arm paths, estimate hindlimb straight-line paths from "
                    "segment lengths + functional groups, compute moment "
                    "arms at two poses per limb, derive force capability and "
                    "torque envelopes, and cross-check against -dL/dq and "
                    "the Oku walking torques.",
            "selection": "MUSCLE-PATHS lane brief, branched from "
                         "origin/master at " + BASE_COMMIT + ".",
        },
    }
    work = {
        "id": WORK_ID,
        "kind": "work",
        "name": "Derive muscle path geometry, moment arms and torque "
                "envelopes for the macaque arm and hindlimb",
        "status": "specified",
        "priority": "P1",
        "dependencies": ["model.anatomy.macaque_arm"],
        "evidence": [],
        "falsifier": {
            "statement": "The derivation is false if any straight-path "
                         "moment arm differs from -dL/dq beyond 1e-6 m at "
                         "either pose, if a resolved path endpoint lies "
                         "inside a wrap cylinder, if the conditional-point "
                         "length jump exceeds 5 mm, or if the hindlimb "
                         "envelope misses an Oku walking torque direction by "
                         "more than the declared 25% uncertainty (measured: "
                         "knee_extension and mtp_flexion ARE falsified and "
                         "their numbers are barred from force claims).",
            "status": "measured",
            "results": FALSIFIER_RESULTS,
            "receipt": RECEIPT,
        },
        "physical": {
            "statement": "Muscle paths, moment arms and maximum force "
                         "capability can be derived for the pinned 39-muscle "
                         "arm model and estimated for the 30 admitted "
                         "Guimaraes hindlimb muscles, and the resulting "
                         "torque envelopes either cover or measurably fail "
                         "the Oku 2021 walking torques under a derived "
                         "specific tension.",
            "prediction": "Straight-path moment arms equal -dL/dq to "
                          "1e-6 m; the hindlimb envelope covers hip "
                          "extension, knee flexion and ankle directions; "
                          "the patella-less straight proxy fails knee "
                          "extension and the pulley-less proxy fails mtp "
                          "flexion - both failures visible in the record.",
            "contract": {
                "schema": "chimera.muscle_path_geometry.v1",
                "base_commit": BASE_COMMIT,
                "derivation": DOC,
                "deliverable": {
                    "path": "tools/science_funnel/validation/"
                            "muscle_paths_20260918/muscle_path_geometry.json",
                    "sha256": deliverable_sha,
                },
                "receipt": RECEIPT,
                "tests": "tools/science_funnel/tests/test_muscle_paths.py",
                "method": {
                    "arm": "parse_source() paths; conditional via ranges; "
                           "analytic cylinder wrapping (quadrant + <=pi arc "
                           "rules); ellipsoid/torus contacts unresolved with "
                           "r_eff*(pi-2) bounds; moment arms twice "
                           "(geometric perpendicular distance vs -dL/dq, "
                           "topology-frozen central differences)",
                    "hindlimb": "straight-line paths from Oku 2021 Table 1 "
                                "segment lengths + Guimaraes Table 3 "
                                "functional groups; landmarks recorded per "
                                "muscle; force = PCSA x derived specific "
                                "tension x cos(pennation); specific tension "
                                "least-squares from mass-adjusted Oku Fmax "
                                "vs matched PCSA (1.281 MPa, residuals "
                                "published)",
                },
                "owned_files": [
                    "tools/science_funnel/validation/"
                    "muscle_paths_20260918/",
                    "tools/science_funnel/tests/test_muscle_paths.py",
                    "docs/research/20260918_muscle_path_derivation.md",
                ],
                "not_implemented": [
                    "no runtime actuation, activation dynamics, tendon "
                    "compliance or time integration",
                    "no full wrapping solver for ellipsoid/torus contacts",
                    "no claim that the hindlimb attachment landmarks "
                    "reproduce dissection geometry",
                    "knee_extension and mtp_flexion directions falsified: "
                    "not usable for force claims",
                    "the existing work.creature.macaque_muscle_paths "
                    "(full source wrapping semantics) stays separate and "
                    "open",
                ],
            },
        },
        "project_spec": {
            "schema": "chimera.project_spec.v1",
            "admission": "active_specification",
            "category": "work",
            "origin_id": SOURCE_ID,
            "admitted_utc": ADMITTED_UTC,
            "authorization": "Operator MUSCLE-PATHS lane brief",
            "authority_scope": "Derivation, admission and mechanical "
                               "validation only; no runtime qualification.",
        },
    }
    model = {
        "id": MODEL_ID,
        "kind": "model_definition",
        "name": "Derived macaque muscle path geometry, moment arms and "
                "torque envelopes (arm + hindlimb, two poses)",
        "status": "extracted",
        "dependencies": [],
        "evidence": [],
        "provenance": {
            "source_id": SOURCE_ID,
            "source_revision": BASE_COMMIT,
            "derived_from": ["source.anatomy.macaque_arm"],
            "deliverable_sha256": deliverable_sha,
            "arm_source_revision":
                deliverable["source_pins"]["macaque_arm"]
                ["monkeyArm_current.osim"]["sha256"],
        },
        "physical": deliverable,
        "notes": "Derived record: every number traces to the pinned sources "
                 "through the derivation chain in docs/research/"
                 "20260918_muscle_path_derivation.md. Status stays "
                 "'extracted': a derivation is not a verification.",
    }
    relations = [
        {"src": WORK_ID, "rel": "derived_from", "dst": SOURCE_ID,
         "note": "Operator-directed MUSCLE-PATHS lane admission"},
        {"src": MODEL_ID, "rel": "derived_from", "dst": SOURCE_ID,
         "note": "Derived geometry record produced by the lane"},
        {"src": MODEL_ID, "rel": "derived_from",
         "dst": "source.anatomy.macaque_arm",
         "note": "Arm path points and wrap surfaces from the pinned model"},
    ]
    return [source, work, model], relations


def reconcile_program():
    with open(PROGRAM, encoding="utf-8-sig") as stream:
        program = json.load(stream)
    changed = []
    known = {obj["id"]: obj for obj in program["objects"]}
    objects, relations = build_objects()
    for obj in objects:
        if known.get(obj["id"]) != obj:
            if obj["id"] in known:
                program["objects"] = [obj if old["id"] == obj["id"] else old
                                      for old in program["objects"]]
                changed.append(obj["id"] + " (updated to declared state)")
            else:
                program["objects"].append(obj)
                changed.append(obj["id"] + " (admitted)")
    edges = {(e["src"], e["rel"], e["dst"], e.get("note", ""))
             for e in program["relations"]}
    for rel in relations:
        key = (rel["src"], rel["rel"], rel["dst"], rel.get("note", ""))
        if key not in edges:
            program["relations"].append(dict(rel))
            changed.append("relation %s -%s-> %s"
                           % (rel["src"], rel["rel"], rel["dst"]))
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
    evidence_count = sum(1 for o in graph.objects.values()
                         if o["kind"] == "evidence")
    print("admission:", "; ".join(changed) if changed else "no-op")
    print("rebuilt", os.path.normpath(path), "objects", len(graph.objects),
          "relations", len(graph.relations), "graph_hash", graph.graph_hash())
    print("evidence records:", evidence_count, "(must stay 11)")
    print("declared_utc", datetime.now(timezone.utc).isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
