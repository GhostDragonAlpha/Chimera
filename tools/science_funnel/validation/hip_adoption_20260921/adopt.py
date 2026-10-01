"""Hip-bond adoption: the integrator act the adjacency lane deferred.

Lane agent/hip-bond-adoption-20260921. Adopts the measured cross-component
adjacency (tools/science_funnel/validation/axial_adjacency_20260920/) into
the matter skeleton definition BY ANATOMICAL CLASS:

  joint class   the 2 pre_registered:true hip bonds (femur<->composite,
                law gap 1.44/1.49 mm) join `bonds` -- cartilage material,
                cure 13 MPa, rest_length = the MEASURED LAW GAP (the
                vertex metric that defined the 21 committed bonds; the
                refined gaps 1.403/1.343 ride as named metadata), the
                exact 21-bond format, 0 invented / 0 dropped.
  pose class    the 6 pre_registered:false curl appositions (hands 8/9,
                forearms 11/13, feet 15/17) are the curled fetal
                specimen's real contacts, NOT joints -- recorded in a
                top-level `pose_contacts` metadata section the kernel
                parser ignores; they add NO graph edges, so components
                do not merge through them.
  refusal class the 2 shoulders (4.60/5.00 mm, falsifier F2 fired) and
                the 3 singletons stay refused -- recorded with their
                numbers in `refused_joints`; singleton 19's 0.0 mm
                face-contact stays a NAMED vertex-vertex metric artifact
                for successor law work, never self-granted.

Structural consequence (derived, not chosen): components 8 -> 6 -- the two
femoral chains join the composite's component through the hips and
nothing else changes.

Rule 0 receipt: tools/science_funnel/validation/hip_adoption_20260921/
receipt.json (statement / prediction / falsifiers banked and hashed in
preregistration.sha256 BEFORE any edit).

Usage (repo root):
    python -B tools/science_funnel/validation/hip_adoption_20260921/adopt.py write
    python -B tools/science_funnel/validation/hip_adoption_20260921/adopt.py check

write  reads the PRE-adoption definition from the pinned base commit's
       blob (git show BASE_COMMIT:path -- the worktree may already carry
       the adoption), applies the class law, writes the adopted
       definition.
check  regenerates the adoption from the base blob and demands
       byte-identity with the committed adopted file (the lane's
       determinism proof; runs in a TRUE fresh clone too).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[3]

BASE_COMMIT = "3539fdb9"
BODY_REL = "tools/science_funnel/data/morphosource_ct/matter_skeleton/infant_skeleton.body.json"
CANDIDATES_REL = "tools/science_funnel/validation/axial_adjacency_20260920/candidate_bonds.json"

ADOTTED_COUNT = 2   # joint class
POSE_COUNT = 6      # pose class
REFUSED_COUNT = 5   # 2 shoulders + 3 singletons (recorded, not bonds)


class Refusal(Exception):
    pass


def require(cond, code, detail):
    if not cond:
        raise Refusal(f"{code}: {detail}")


def git_bytes(rev_rel: str) -> bytes:
    out = subprocess.run(["git", "show", rev_rel], cwd=REPO_ROOT,
                         capture_output=True)
    if out.returncode != 0:
        raise Refusal("git_show_failed", f"{rev_rel}: {out.stderr.decode()}")
    return out.stdout


def read_json_bytes(raw: bytes):
    return json.loads(raw.decode("utf-8"))


def adopt(base_body: dict, candidates: dict) -> dict:
    """Apply the class law. Deterministic: same inputs -> same dict."""
    hips = [b for b in candidates["bonds"] if b.get("pre_registered") is True]
    curls = [b for b in candidates["bonds"] if b.get("pre_registered") is False]
    require(len(hips) == ADOTTED_COUNT, "hip_count",
            f"expected {ADOTTED_COUNT} pre-registered GREEN bonds, got {len(hips)}")
    require(len(curls) == POSE_COUNT, "pose_count",
            f"expected {POSE_COUNT} discovered curl contacts, got {len(curls)}")
    require(hips == sorted(hips, key=lambda b: b["id"]), "candidate_order",
            "hip bonds must keep the candidate file's order")
    require(curls == sorted(curls, key=lambda b: b["id"]), "candidate_order",
            "curl contacts must keep the candidate file's order")

    existing = {b["id"] for b in base_body["bonds"]}
    for b in hips + curls:
        require(b["id"] not in existing, "duplicate_bond", b["id"])
        for m in b["members"]:
            require(m in {mem["id"] for mem in base_body["membranes"]},
                    "unknown_member", f"{b['id']}: {m}")

    # -- joint class: the exact 21-bond format + measured metadata carried
    adopted_bonds = []
    for b in hips:
        adopted_bonds.append({
            "id": b["id"],
            "material": b["material"],
            "members": list(b["members"]),
            "cure_strength": b["cure_strength"],
            "rest_length_mm": b["measured_gap_mm"],
            "measured_gap_mm": b["measured_gap_mm"],
            "refined_gap_mm": b["refined_gap_mm"],
            "closest_points_mm": b["closest_points_mm"],
            "anatomical_reading": b["anatomical_reading"],
            "evidence": (b["evidence"]
                         + f"; adopted by lane {candidates['lane']} successor "
                           "agent/hip-bond-adoption-20260921 from "
                           "candidate_bonds.json " + b["id"]
                           + " (pre-registered GREEN, rest_length = the law "
                             "gap per the refinement_law: bonds are defined "
                             "on the vertex metric); receipt "
                             "tools/science_funnel/validation/"
                             "hip_adoption_20260921/receipt.json"),
        })

    # -- pose class: metadata only, NEVER bonds
    pose_contacts = {
        "status": ("RECORDED, NOT BONDED -- the discovered (unpre-registered) "
                   "curl appositions from axial_adjacency_20260920 are the "
                   "specimen's actual contacts in the curled fetal pose it "
                   "was CT-scanned in: real measured geometry, NOT "
                   "anatomical joints. A standing-pose animal would not have "
                   "them. The biological law's stage/pose honesty applies to "
                   "pose: they ride this metadata section, never the bond "
                   "graph, so no connected component merges through them."),
        "measured_source": ("tools/science_funnel/validation/"
                            "axial_adjacency_20260920/candidate_bonds.json "
                            "(pre_registered: false entries, verbatim); "
                            "receipt of the same lane"),
        "contacts": [{
            "id": b["id"].replace("bond.", "pose."),
            "members": list(b["members"]),
            "measured_gap_mm": b["measured_gap_mm"],
            "refined_gap_mm": b["refined_gap_mm"],
            "closest_points_mm": b["closest_points_mm"],
            "components": list(b["components"]),
            "anatomical_reading": b["anatomical_reading"],
            "evidence": b["evidence"],
        } for b in curls],
    }

    refused_joints = {
        "status": ("HONEST REFUSALS -- measured on the law metric and never "
                   "tuned away; no bond is claimed. The 8-component reading "
                   "stands as anatomy for these pairs."),
        "measured_source": ("tools/science_funnel/validation/"
                            "axial_adjacency_20260920/receipt.json "
                            "pre_registered_outcomes + verdicts"),
        "refusals": [
            {
                "id": "refusal.shoulder_01_04",
                "members": ["mem.bone_01", "mem.bone_04"],
                "pair_prediction": "P3 shoulder A",
                "measured_gap_mm": 5.0,
                "verdict": ("REFUSED (law gap 5.00 mm > 3.0 mm cut) -- "
                            "falsifier F2 fired: at CT this specimen's "
                            "shoulder carries a real cartilage-plus-soft-"
                            "tissue gap; no bond."),
            },
            {
                "id": "refusal.shoulder_01_05",
                "members": ["mem.bone_01", "mem.bone_05"],
                "pair_prediction": "P4 shoulder B",
                "measured_gap_mm": 4.6,
                "verdict": ("REFUSED (law gap 4.60 mm > 3.0 mm cut) -- "
                            "falsifier F2 fired; no bond."),
            },
            {
                "id": "refusal.singleton_16",
                "members": ["mem.bone_16"],
                "pair_prediction": "P5",
                "measured_row_minimum_mm": 5.82,
                "composite_gap_mm": 22.9,
                "femur2_gap_mm": 5.82,
                "verdict": ("REFUSED -- falsifier F3 fired (both "
                            "pre-registered partners > 3.0 mm; nothing in "
                            "the full row is <= 3.0); stays isolated."),
            },
            {
                "id": "refusal.singleton_14",
                "members": ["mem.bone_14"],
                "pair_prediction": "P6",
                "measured_row_minimum_mm": 6.99,
                "row_minimum_partner": "foot_class rank 24",
                "composite_gap_mm": 29.75,
                "verdict": ("REFUSED -- falsifier F3 fired; stays isolated."),
            },
            {
                "id": "refusal.singleton_19",
                "members": ["mem.bone_19"],
                "pair_prediction": "P6",
                "measured_row_minimum_mm": 7.71,
                "row_minimum_partner": "foot_class rank 22",
                "composite_gap_mm": 36.93,
                "metric_artifact": ("the true surface gap to the composite "
                                    "is 0.0 mm (refined): a composite "
                                    "preview vertex lies on a singleton-19 "
                                    "triangle face -- face-face contact "
                                    "invisible to the committed vertex-"
                                    "vertex law metric. NAMED successor law "
                                    "work (a surface-metric adjacency class "
                                    "owned by a lane that owns that law); "
                                    "NOT self-granted here; 19 stays "
                                    "isolated in this graph."),
                "verdict": ("REFUSED on the law metric -- falsifier F3 "
                            "fired; stays isolated."),
            },
        ],
    }

    adoption = {
        "lane": "agent/hip-bond-adoption-20260921",
        "receipt": ("tools/science_funnel/validation/hip_adoption_20260921/"
                    "receipt.json"),
        "preregistration_sha256": ("pinned in tools/science_funnel/validation/"
                                   "hip_adoption_20260921/preregistration.sha256 "
                                   "(receipt pre-state hash "
                                   "620292c0209561fdea65af0241ef1e5211a1938126"
                                   "70c61ca5cb690c1dad478d, hashed before any "
                                   "edit)"),
        "base_commit": BASE_COMMIT,
        "bond_source": ("axial_adjacency_20260920 candidate_bonds.json "
                        "pre_registered:true entries, verbatim fields"),
        "rest_length_law": ("rest_length_mm = the measured LAW gap (vertex "
                            "metric) per the measurement lane's "
                            "refinement_law; refined_gap_mm recorded as "
                            "metadata, never substituted"),
        "class_law": ("2 hip bonds (joint class) joined the graph; 6 curl "
                      "appositions (pose class) recorded in pose_contacts, "
                      "no graph edges; 2 shoulders + 3 singletons (refusal "
                      "class) recorded in refused_joints"),
        "components_before": 8,
        "components_after": 6,
        "component_consequence": ("the two femoral chains joined the "
                                  "composite's component through the hip "
                                  "bonds; the fore chains and singletons "
                                  "did not merge (curl contacts carry no "
                                  "graph edges)"),
        "geometry_untouched": ("bonds + metadata only; every triangle blob, "
                               "vertex record, thickness and mass is "
                               "byte-identical to the pre-adoption "
                               "definition"),
    }

    body = dict(base_body)  # top-level key order preserved
    body["bonds"] = list(base_body["bonds"]) + adopted_bonds
    body["pose_contacts"] = pose_contacts
    body["refused_joints"] = refused_joints
    body["adoption"] = adoption
    return body


def dumps(body: dict) -> bytes:
    text = json.dumps(body, indent=1, ensure_ascii=False, allow_nan=False)
    return (text + "\n").encode("utf-8")


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "check"
    base_body = read_json_bytes(git_bytes(f"{BASE_COMMIT}:{BODY_REL}"))
    candidates = read_json_bytes(git_bytes(f"{BASE_COMMIT}:{CANDIDATES_REL}"))
    adopted = dumps(adopt(base_body, candidates))
    target = REPO_ROOT / BODY_REL
    if cmd == "write":
        target.write_bytes(adopted)
        print(f"adopt: wrote {BODY_REL} ({len(adopted)} bytes) from base "
              f"{BASE_COMMIT}: 2 hip bonds joined, 6 curl contacts recorded "
              f"as pose metadata, 5 refusals recorded")
        return 0
    if cmd == "check":
        committed = target.read_bytes()
        if committed != adopted:
            raise Refusal("adoption_drift",
                          "committed body.json != deterministic adoption of "
                          f"base {BASE_COMMIT}")
        print(f"adopt check OK: committed definition is byte-identical to "
              f"the deterministic adoption of base {BASE_COMMIT}")
        return 0
    raise Refusal("unknown_command", cmd)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Refusal as ref:
        print(f"REFUSED {ref}", file=sys.stderr)
        sys.exit(2)
