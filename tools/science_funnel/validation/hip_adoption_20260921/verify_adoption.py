"""The hip-adoption battery: every pre-registered falsifier, measured.

Lane agent/hip-bond-adoption_20260921. Reads ONLY committed artifacts
(fresh-clone mode): the adopted definition, its base blob (git show),
the committed candidate table, the committed derivation book, the
committed preview meshes. Refuses loudly on any falsifier.

Usage (repo root):
    python -B tools/science_funnel/validation/hip_adoption_20260921/verify_adoption.py
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.matter_kernel import definition as kdef  # noqa: E402
from tools.science_funnel.common import Refusal, require  # noqa: E402
from tools.science_funnel import matter_skeleton_import as msi  # noqa: E402

BODY_REL = ("tools/science_funnel/data/morphosource_ct/"
            "matter_skeleton/infant_skeleton.body.json")
BASE_COMMIT = "3539fdb9"
CANDIDATES_PATH = msi.REPO_ROOT / (
    "tools/science_funnel/validation/axial_adjacency_20260920/"
    "candidate_bonds.json")
BOOK_PATH = msi.REPO_ROOT / (
    "tools/science_funnel/validation/matter_skeleton_20260920/"
    "derivation.json")
OUT_PATH = LANE_DIR / "verify.json"

EXPECTED_COMPONENTS = sorted(
    [[1, 2, 3, 6, 7, 15, 17, 18, 20, 21, 22, 23, 24, 25],
     [4, 8, 10, 12], [5, 9, 11, 13], [14], [16], [19]], key=min)
HIP_IDS = ["bond.joint_01_02", "bond.joint_01_03"]
SINGLETONS = [14, 16, 19]


def git_bytes(rev_rel: str) -> bytes:
    out = subprocess.run(["git", "show", rev_rel], cwd=REPO_ROOT,
                         capture_output=True)
    require(out.returncode == 0, "git_show_failed",
            f"{rev_rel}: {out.stderr.decode()}")
    return out.stdout


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def membrane_geometry(parsed: dict) -> dict:
    """geometry_preserved vs the source OBJs (the import lane's own loop)."""
    worst_bbox = 0.0
    for mem in parsed["membranes"]:
        rank = mem["rank"]
        verts64, faces = msi.parse_obj(msi.obj_path(rank))
        f32 = msi.to_f32(verts64)
        blob = (msi.OUT_DIR / mem["triangles"]).read_bytes()
        require(len(blob) == 36 * len(faces), "blob_size", mem["id"])
        readback = []
        for off in range(0, len(blob), kdef.TRIANGLE_BYTES):
            vals = struct.unpack_from("<9f", blob, off)
            readback.append((tuple(vals[0:3]), tuple(vals[3:6]),
                             tuple(vals[6:9])))
        expected = [(f32[a], f32[b], f32[c]) for a, b, c in faces]
        require(readback == expected, "blob_faces", mem["id"])
        src_hash = hashlib.sha256(
            msi.vertex_records(f32, faces)).hexdigest()
        require(src_hash == mem["vertex_sha256"], "vertex_hash", mem["id"])
        rb_verts = [v for tri in readback for v in tri]
        rb_min, rb_max = msi.bbox(rb_verts)
        s_min, s_max = msi.bbox(verts64)
        dev = max(max(abs(a - b) for a, b in zip(rb_min, s_min)),
                  max(abs(a - b) for a, b in zip(rb_max, s_max)))
        worst_bbox = max(worst_bbox, dev)
        require(dev <= msi.BBOX_TOL_MM, "bbox_tol", f"{mem['id']}: {dev}")
    return {
        "compartments": len(parsed["membranes"]),
        "face_count_equal": True,
        "vertex_count_equal": True,
        "per_face_float32_equal": True,
        "worst_bbox_dev_mm": worst_bbox,
        "bbox_tolerance_mm": msi.BBOX_TOL_MM,
        "vertex_sha256_all_match": True,
    }


def bond_pairs(bonds: list) -> set:
    return {tuple(sorted((int(b["members"][0].split("_")[1]),
                          int(b["members"][1].split("_")[1]))))
            for b in bonds}


def main() -> int:
    results: dict = {}

    body_path = msi.OUT_DIR / "infant_skeleton.body.json"
    parsed = kdef.parse_body(body_path)
    body = read_json(body_path)
    base = json.loads(git_bytes(f"{BASE_COMMIT}:{BODY_REL}").decode("utf-8"))
    candidates = read_json(CANDIDATES_PATH)
    book = read_json(BOOK_PATH)

    # -- F4 kernel_conformance -------------------------------------------
    require(len(parsed["membranes"]) == 25, "kernel_membranes",
            f"expected 25, got {len(parsed['membranes'])}")
    require(len(parsed["bonds"]) == 23, "kernel_bonds",
            f"expected 23 (21 + 2 hips), got {len(parsed['bonds'])}")
    mass_rel = max(abs(m["mass"] - m["mass_derived"]) / m["mass_derived"]
                   for m in parsed["membranes"])
    require(mass_rel <= kdef.MASS_TOLERANCE, "kernel_mass_tol", str(mass_rel))
    results["kernel_conformance"] = {
        "falsifier": "F4_kernel_and_book",
        "pass": True,
        "measured": {
            "parser": "tools.matter_kernel.definition.parse_body",
            "membranes": len(parsed["membranes"]),
            "bonds": len(parsed["bonds"]),
            "stated_vs_kernel_derived_mass_max_rel": mass_rel,
        },
    }

    # -- F1 geometry_preserved: vs source OBJs AND vs the base blob ------
    geo = membrane_geometry(parsed)
    untouched_keys = ["schema", "specimen", "stage", "units",
                      "membrane_layer", "materials", "membranes"]
    diff_keys = [k for k in untouched_keys if body[k] != base[k]]
    require(not diff_keys, "definition_touch", str(diff_keys))
    geo["sections_equal_to_base_blob"] = untouched_keys
    results["geometry_preserved"] = {
        "falsifier": "F1_geometry_preserved",
        "pass": True,
        "measured": geo,
    }

    # -- F2 adjacency_reproduced (bond class law) ------------------------
    _, edges = msi.load_identifications()
    def_edges = {}
    for b in parsed["bonds"]:
        u = int(b["members"][0].split("_")[1])
        v = int(b["members"][1].split("_")[1])
        def_edges[tuple(sorted((u, v)))] = b
    committed_pairs = set(edges)
    require(committed_pairs <= set(def_edges), "dropped_joints",
            str(committed_pairs - set(def_edges)))
    gap_dev = max(abs(def_edges[k]["rest_length_mm"] - edges[k]["gap_mm"])
                  for k in committed_pairs)
    require(gap_dev <= 0.005, "gap_tol", str(gap_dev))

    hip_pairs = {tuple(sorted((int(b["members"][0].split("_")[1]),
                               int(b["members"][1].split("_")[1]))))
                 for b in parsed["bonds"] if b["id"] in HIP_IDS}
    require(hip_pairs == {(1, 2), (1, 3)}, "hip_pairs", str(hip_pairs))
    cand_by_id = {c["id"]: c for c in candidates["bonds"]}
    max_rest_dev = 0.0
    for hid in HIP_IDS:
        b = next(x for x in parsed["bonds"] if x["id"] == hid)
        c = cand_by_id[hid]
        for field in ("material", "members", "cure_strength",
                      "measured_gap_mm", "refined_gap_mm",
                      "closest_points_mm", "anatomical_reading"):
            require(b[field] == c[field], "candidate_field",
                    f"{hid}.{field}: {b[field]!r} != {c[field]!r}")
        require(b["rest_length_mm"] == b["measured_gap_mm"], "rest_law", hid)
        require(b["refined_gap_mm"] <= b["measured_gap_mm"], "refined_law",
                hid)
        max_rest_dev = max(max_rest_dev,
                           abs(b["rest_length_mm"] - c["measured_gap_mm"]))
    require(max_rest_dev == 0.0, "hip_rest_length", str(max_rest_dev))
    for b in parsed["bonds"]:
        require(b["rest_length_mm"] == b["measured_gap_mm"], "rest_equals_gap",
                b["id"])

    # pose class: the 6 curl contacts live in metadata, NEVER in bonds
    pose = body["pose_contacts"]["contacts"]
    require(len(pose) == 6, "pose_count", str(len(pose)))
    pose_pairs = {tuple(sorted((int(p["members"][0].split("_")[1]),
                                int(p["members"][1].split("_")[1]))))
                  for p in pose}
    curl_pairs = {tuple(sorted((int(c["members"][0].split("_")[1]),
                                int(c["members"][1].split("_")[1]))))
                  for c in candidates["bonds"]
                  if c.get("pre_registered") is False}
    require(pose_pairs == curl_pairs, "pose_pairs",
            f"{pose_pairs} != {curl_pairs}")
    leaked = pose_pairs & set(def_edges)
    require(not leaked, "pose_leaked_into_bonds", str(leaked))

    # refusal class: shoulders and singletons carry no bond
    require(not ({(1, 4), (1, 5)} & set(def_edges)),
            "shoulder_bonded", "refused shoulders must not be bonds")
    bonded_ranks = {r for pr in def_edges for r in pr}
    require(not (set(SINGLETONS) & bonded_ranks), "singleton_bonded",
            str(set(SINGLETONS) & bonded_ranks))
    refusals = {r["id"]: r for r in body["refused_joints"]["refusals"]}
    require(len(refusals) == 5, "refusal_count", str(len(refusals)))
    require(refusals["refusal.shoulder_01_04"]["measured_gap_mm"] == 5.0
            and refusals["refusal.shoulder_01_05"]["measured_gap_mm"] == 4.6,
            "shoulder_numbers", "recorded refusal numbers must be verbatim")
    require("metric_artifact" in refusals["refusal.singleton_19"],
            "artifact_record", "singleton-19 metric artifact must be named")

    results["adjacency_reproduced"] = {
        "falsifier": "F2_bond_class_law",
        "pass": True,
        "measured": {
            "bonds": len(parsed["bonds"]),
            "committed_edges_reproduced": len(committed_pairs),
            "hip_bonds_adopted": 2,
            "max_committed_rest_length_dev_mm": gap_dev,
            "max_hip_rest_length_dev_mm": max_rest_dev,
            "rest_length_equals_measured_gap_all_bonds": True,
            "pose_contacts_recorded": len(pose),
            "pose_pairs_in_bonds": 0,
            "refused_recorded": len(refusals),
            "invented_joints": 0,
            "dropped_joints": 0,
        },
    }

    # -- F3 component consequence ----------------------------------------
    comps = msi.components(parsed)
    comps_sorted = sorted([sorted(c) for c in comps], key=min)
    require(comps_sorted == EXPECTED_COMPONENTS, "components",
            f"expected {EXPECTED_COMPONENTS}, got {comps_sorted}")
    results["component_consequence"] = {
        "falsifier": "F3_component_consequence",
        "pass": True,
        "measured": {
            "components_before": 8,
            "components_after": len(comps),
            "components": comps_sorted,
            "note": "composite + both hind chains joined via the 2 hip "
                    "bonds; fore chains separate (curl contacts carry no "
                    "graph edges); singletons 14/16/19 isolated",
        },
    }

    # -- F4 mass_book unchanged -------------------------------------------
    tot = book["totals"]
    by_rank = {c["rank"]: c for c in book["compartments"]}
    worst_mass_dev = 0.0
    for mem in body["membranes"]:
        comp = by_rank[mem["rank"]]
        require(abs(mem["thickness"] - comp["thickness_mm_equivalent"])
                <= 1e-9, "thickness_drift", mem["id"])
        # book masses are grams (body.json: kg); compare in grams
        worst_mass_dev = max(worst_mass_dev,
                             abs(mem["mass"] * 1000.0 - comp["mass_g"]))
        require(abs(mem["mass"] * 1000.0 - comp["mass_g"]) <= 1e-6,
                "mass_drift", mem["id"])
    require(tot["total_mass_g"] == 52.3139, "total_mass",
            str(tot["total_mass_g"]))
    results["mass_book"] = {
        "falsifier": "F4_kernel_and_book",
        "pass": True,
        "measured": {
            "total_mass_g": tot["total_mass_g"],
            "unchanged_vs_derivation_book": True,
            "worst_compartment_mass_abs_dev_g": worst_mass_dev,
            "total_volume_mesh_mm3": tot["total_volume_mm3_mesh"],
            "total_volume_delta_pct": tot["total_volume_delta_pct"],
            "named_deviations_count": len(tot["named_deviations"]),
        },
    }

    # -- stage_true (pose/stage honesty carries the metadata sections) ----
    stage = parsed["stage"]
    require(stage["life_stage"] == "infant" and stage["scale"] == 1.0
            and stage["allometric_scaling_applied"] is False, "stage_law",
            json.dumps(stage))
    results["stage_true"] = {
        "pass": True,
        "measured": {
            "life_stage": stage["life_stage"],
            "scale": stage["scale"],
            "pose_sections": ["pose_contacts", "refused_joints", "adoption"],
            "pose_law": "6 curl contacts recorded as pose metadata, 0 as "
                        "bonds -- the stage/pose honesty",
        },
    }

    # -- determinism: committed file == adoption of the base blob ---------
    out = subprocess.run(
        [sys.executable, "-B",
         str(LANE_DIR / "adopt.py").replace("\\", "/"), "check"],
        cwd=REPO_ROOT, capture_output=True)
    require(out.returncode == 0, "adoption_drift",
            out.stdout.decode() + out.stderr.decode())
    results["determinism"] = {
        "falsifier": "F5_fresh_clone_bytes",
        "pass": True,
        "measured": {
            "adopt_check": "committed body.json byte-identical to the "
                           "deterministic adoption of base blob "
                           f"{BASE_COMMIT}",
        },
    }

    text = json.dumps(results, indent=1, ensure_ascii=False,
                      allow_nan=False) + "\n"
    OUT_PATH.write_text(text, encoding="utf-8", newline="\n")
    print(f"hip_adoption verify OK: 25 membranes, 23 bonds "
          f"(21 committed + 2 hips), 6 pose contacts recorded, "
          f"{len(comps)} components, mass book unchanged; "
          f"all falsifiers green")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as ref:
        print(f"REFUSED {ref}", file=sys.stderr)
        sys.exit(2)
