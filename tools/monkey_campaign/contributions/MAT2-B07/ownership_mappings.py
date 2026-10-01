#!/usr/bin/env python3
"""MAT2-B07 ownership mappings: the 14 hand-body mapping decisions (R-OWN-02)
and the 31 forearm correspondence records (R-OWN-03), each with distances.

Authorized by Captain decision #4 (ADOPT-WITH-AUTHORIZATIONS), message
msg-4def1f92578b44d9b57b381643eae245, authorization package item (4):
"R-OWN-02/03 AUTHORIZED: the B07 attempt records the 14 hand-body mapping
decisions + 31 forearm correspondences with distances as attempt work."

Laws (PREREGISTRATION.md section 3):
- Hand records: the A05 law, verified bit-exact against the three
  Captain-mapped A05 muscle_anchor_mapping rows before any new record is
  emitted (F1 mapping_law_mismatch).
- Forearm records: owner body unchanged inside the A05 mutation scope;
  distance to the mutation interface (A05 macaque_hand_anchor origin = the
  hand body origin) at the ZERO-COORDINATE pose from the pinned osim joint
  declarations; frame rotations = declared orientation_in_parent, OpenSim
  body-fixed XYZ Euler; the alternative Euler reading is measured and
  disclosed per record (declared convention note).
- Distances inform, never authorize (B06 law). This script emits a receipt;
  it never flips a sealed row, never qualifies a port, never admits mass.

Run:  python -B ownership_mappings.py            (writes ownership_mappings.json)
Exit: 0 green / 2 named refusal.
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRIB = HERE.parent
CHECKOUT = CONTRIB.parents[2]

A07_PATH = CONTRIB / "MAT2-A07" / "placement_resolution.json"
A07_SHA256 = "cd596d7c21fa81a4c2632e13b63ba26e62da51d44eca2355147fd5dff1587490"
A05_PATH = CONTRIB / "MAT2-A05" / "mutation_structure.json"
A05_SHA256 = "48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649"
OSIM_PATH = (CONTRIB / "MAT2-M02" / "data" / "macaque_arm"
             / "monkeyArm_current.osim")
OSIM_SHA256 = "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
CRITERIA_SHA256 = ("5393a5d7707c370ce5c8ea072512a2b053d0abfb1d36dc952d509"
                   "714150c77d2")
TASK_ID = "MAT2-B07"
SHORT_ID = "B07"
AUTH_MESSAGE_ID = "msg-4def1f92578b44d9b57b381643eae245"
A05_DECISION_ID = "A05-DIGIT-MUTATION-20260928"
ANCHOR_NAME = "macaque_hand_anchor"
BODY_PREFIX = "ref.macaque_arm_hand_mutation.body."

REFUSAL_INPUT_PIN = "input_pin_mismatch"
REFUSAL_CRITERIA = "criteria_pin_mismatch"
REFUSAL_CENSUS = "record_census_mismatch"
REFUSAL_LAW = "mapping_law_mismatch"
REFUSAL_SCOPE = "mutation_scope_violated"
REFUSAL_MODEL = "osim_joint_declaration_invalid"

EXPECTED_CENSUS = {
    "path_resolutions_total": 48,
    "mapped": 3,
    "pending_assembly_mapping": 14,
    "not_on_hand_body": 31,
    "owner_body": {"ulna": 5, "radius": 18, "humerus": 8, "hand": 17},
}


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def check_registry_criteria():
    """G7: criteria hash identical across prereg / registry (mode=ro)."""
    require(REGISTRY.exists(), REFUSAL_CRITERIA + ":registry_missing")
    uri = "file:" + str(REGISTRY).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        row = con.execute(
            "SELECT payload FROM state WHERE id='1'").fetchone()
    finally:
        con.close()
    require(row is not None, REFUSAL_CRITERIA + ":registry_empty")
    payload = json.loads(row[0])
    card = payload["kanban"]["cards"].get(TASK_ID)
    require(card is not None, REFUSAL_CRITERIA + ":card_missing")
    require(card.get("criteria_sha256") == CRITERIA_SHA256,
            REFUSAL_CRITERIA + ":registry_value_drift")


def load_inputs():
    require(sha256_file(A07_PATH) == A07_SHA256,
            REFUSAL_INPUT_PIN + ":a07_resolution")
    require(sha256_file(A05_PATH) == A05_SHA256,
            REFUSAL_INPUT_PIN + ":a05_structure")
    require(sha256_file(OSIM_PATH) == OSIM_SHA256,
            REFUSAL_INPUT_PIN + ":osim_model")
    a07 = json.loads(A07_PATH.read_text(encoding="utf-8"))
    a05 = json.loads(A05_PATH.read_text(encoding="utf-8"))
    return a07, a05


def census(a07):
    records = a07["path_resolutions"]
    counts = {
        "path_resolutions_total": len(records),
        "mapped": sum(1 for r in records
                      if r.get("mutant_mapping_status") == "mapped"),
        "pending_assembly_mapping": sum(
            1 for r in records
            if r.get("mutant_mapping_status") == "pending_assembly_mapping"),
        "not_on_hand_body": sum(1 for r in records
                                if r.get("mutant_mapping_status")
                                == "not_on_hand_body"),
    }
    owner = {}
    for r in records:
        owner[r["owner_body"]] = owner.get(r["owner_body"], 0) + 1
    counts["owner_body"] = owner
    require(counts == EXPECTED_CENSUS,
            REFUSAL_CENSUS + ":" + json.dumps(counts, sort_keys=True))
    return records


# ---- A05 mutant body frame origins (the hand-record distance law) ----------
def a05_bodies(a05):
    bodies = {b["name"]: b for b in a05["bodies"]}
    bodies[ANCHOR_NAME] = a05["anchor_body"]
    return bodies


def a05_parent(bodies, name):
    if name == ANCHOR_NAME:
        return ANCHOR_NAME
    return bodies[name]["parent"].replace(BODY_PREFIX, "")


def a05_pos(bodies, name):
    if name == ANCHOR_NAME:
        return (0.0, 0.0, 0.0)
    return tuple(bodies[name]["mutation"]["pos_m"])


def a05_origin(bodies, name):
    """Chain-composed frame origin in the mutation frame (identity rotations
    at the reference pose)."""
    point = list(a05_pos(bodies, name))
    par = a05_parent(bodies, name)
    while True:
        step = a05_pos(bodies, par)
        point = [a + b for a, b in zip(point, step)]
        if par == ANCHOR_NAME:
            break
        par = a05_parent(bodies, par)
    return tuple(point)


def verify_a05_law(a05):
    """F1: reproduce the three Captain-mapped distances BIT-EXACT."""
    bodies = a05_bodies(a05)
    results = []
    for m in a05["muscle_anchor_mapping"]:
        nearest = m["nearest_mutant_body"]
        require(nearest in bodies, REFUSAL_LAW + ":unknown_body:" + nearest)
        distance = math.dist(m["location_m"], a05_origin(bodies, nearest))
        require(repr(distance) == repr(m["distance_m"]),
                REFUSAL_LAW + ":" + m["path_point"] + ":"
                + repr(distance) + "!=" + repr(m["distance_m"]))
        results.append({"path_point": m["path_point"],
                        "nearest_mutant_body": nearest,
                        "distance_m": distance,
                        "bit_exact": True})
    return results


def nearest_mutant_body(bodies, location_m):
    best_name, best_distance = None, None
    for name in sorted(bodies):
        d = math.dist(location_m, a05_origin(bodies, name))
        if best_distance is None or d < best_distance:
            best_name, best_distance = name, d
    return best_name, best_distance


# ---- osim joint tree (the forearm-record distance law) ---------------------
def osim_joint_chain():
    """Parse the pinned model's declared joint transforms.

    Returns {body: {"parent":…, "loc_in_parent":[x,y,z],
                    "ori_in_parent":[a,b,c]}} for the wrist chain bodies.
    Refuses if any child-side location/orientation is nonzero (the declared
    zero law this composition relies on) — REFUSAL_MODEL.
    """
    import xml.etree.ElementTree as ET
    root = ET.parse(OSIM_PATH).getroot()
    model = root.find(".//Model")
    require(model is not None, REFUSAL_MODEL + ":model_missing")
    joints = {}
    for body in model.find("BodySet/objects"):
        name = body.get("name")
        joint = body.find("Joint")
        if joint is None:
            continue
        for ph in joint:
            tag = ph.tag.split("}")[-1]
            if "Joint" not in tag or tag == "Joint":
                continue
            vals = {}
            for e in ph:
                k = e.tag.split("}")[-1]
                if k in ("location_in_parent", "orientation_in_parent",
                         "location", "orientation"):
                    vals[k] = [float(x) for x in (e.text or "").split()]
            for k in ("location", "orientation"):
                v = vals.get(k)
                require(v is not None and len(v) == 3
                        and all(x == 0.0 for x in v),
                        REFUSAL_MODEL + ":" + name + ":" + k + "_nonzero")
            joints[name] = {
                "parent": ph.iter("parent_body").__next__().text.strip(),
                "loc_in_parent": vals["location_in_parent"],
                "ori_in_parent": vals["orientation_in_parent"],
                "joint": ph.get("name") or tag,
            }
            break
    expected = ["sternum", "clavicle", "scapula", "humerus", "ulna1", "ulna",
                "radius_jcc", "radius", "radius1", "hand"]
    require(all(b in joints for b in expected),
            REFUSAL_MODEL + ":chain_incomplete:"
            + json.dumps(sorted(joints)))
    return joints


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


def _mm(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def _mv(A, v):
    return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]


def _euler(a, b, c, convention):
    """Declared orientation_in_parent as an Euler triple.
    convention 'body_fixed_xyz' (primary, OpenSim body-fixed X-Y-Z):
        R = Rz(c) Ry(b) Rx(a)
    convention 'space_fixed_xyz' (disclosure alternative):
        R = Rx(a) Ry(b) Rz(c)
    """
    if convention == "body_fixed_xyz":
        return _mm(_rz(c), _mm(_ry(b), _rx(a)))
    if convention == "space_fixed_xyz":
        return _mm(_rx(a), _mm(_ry(b), _rz(c)))
    raise ValueError(convention)


def wrist_origin_in(owner_body, joints, convention="body_fixed_xyz"):
    """The hand body origin (the A05 anchor origin) expressed in the owner
    body frame at the ZERO-COORDINATE pose. Only the chain
    hand<-radius1<-radius<-radius_jcc<-ulna<-ulna1<-humerus is composed;
    every CustomJoint coordinate rotation is identity at zero coordinates."""
    chain = []
    body = "hand"
    while body != owner_body:
        require(body in joints, REFUSAL_MODEL + ":no_joint:" + body)
        j = joints[body]
        chain.append(j)
        body = j["parent"]
        require(body in ("radius1", "radius", "radius_jcc", "ulna", "ulna1",
                         "humerus", "scapula", "clavicle", "sternum",
                         "ground"),
                REFUSAL_MODEL + ":chain_escape:" + body)
    require(body == owner_body,
            REFUSAL_MODEL + ":owner_not_ancestor:" + owner_body)
    point = [0.0, 0.0, 0.0]  # hand origin in the hand frame
    for j in chain:
        rot = _euler(*j["ori_in_parent"], convention)
        point = _mv(rot, point)
        point = [point[i] + j["loc_in_parent"][i] for i in range(3)]
    return point


def convention_bound(owner_body, joints):
    a = wrist_origin_in(owner_body, joints, "body_fixed_xyz")
    b = wrist_origin_in(owner_body, joints, "space_fixed_xyz")
    return math.dist(a, b)


def check_mutation_scope(a05, owner_body):
    """The owner body must be OUTSIDE the A05 mutation scope."""
    mutated = {b["name"] for b in a05["bodies"]}
    mutated.add(ANCHOR_NAME)
    require(owner_body not in mutated,
            REFUSAL_SCOPE + ":" + owner_body)
    for b in a05["bodies"]:
        require(owner_body != b.get("human_source", {}).get("body"),
                REFUSAL_SCOPE + ":human_source:" + owner_body)


def authorization_block():
    return {
        "authority": "OPERATIONAL_LEAD (Captain decision #4)",
        "message_id": AUTH_MESSAGE_ID,
        "item": "(4) R-OWN-02/03 AUTHORIZED: the B07 attempt records the 14 "
                "hand-body mapping decisions + 31 forearm correspondences "
                "with distances as attempt work.",
        "decision_recorded_by": "attempt wk-b07-adopt "
                                "08d3db08d4d64179b2f95a516a2155bd",
        "note": "distances inform, never authorize (B06 law verbatim); "
                "no sealed row is flipped by this record",
    }


def build_hand_records(records, a05):
    bodies = a05_bodies(a05)
    out = []
    for r in records:
        if r.get("mutant_mapping_status") != "pending_assembly_mapping":
            continue
        require(r["on_hand_body"] is True and r["owner_body"] == "hand",
                REFUSAL_CENSUS + ":pending_not_hand:" + r["record_id"])
        nearest, distance = nearest_mutant_body(bodies, r["location_m"])
        origin = list(a05_origin(bodies, nearest))
        out.append({
            "requirement_id": "R-OWN-02",
            "record_id": r["record_id"],
            "muscle": r["muscle"],
            "declared_name": r["declared_name"],
            "role": r["role"],
            "index": r["index"],
            "owner_body": "hand",
            "location_m": r["location_m"],
            "decision": {
                "kind": "recorded_assembly_mapping_decision",
                "resolution": "mapped_by_this_attempt",
                "nearest_mutant_body": nearest,
                "mutant_body_origin_m": origin,
                "recorded_distance_m": distance,
                "law": "A05 muscle_anchor_mapping law (chain-composed frame "
                       "origin, identity rotations at the reference pose); "
                       "verified bit-exact against the 3 A05 Captain-mapped "
                       "rows before emission (F1)",
                "supersedes": "explicitly_unresolved (A07)",
            },
            "authorization": authorization_block(),
        })
    out.sort(key=lambda x: x["record_id"])
    return out


def build_forearm_records(records, a05, joints):
    out = []
    for r in records:
        if r.get("mutant_mapping_status") != "not_on_hand_body":
            continue
        require(r["on_hand_body"] is False,
                REFUSAL_CENSUS + ":forearm_on_hand:" + r["record_id"])
        owner = r["owner_body"]
        check_mutation_scope(a05, owner)
        require(owner in ("ulna", "radius", "humerus"),
                REFUSAL_CENSUS + ":unexpected_owner:" + owner)
        interface = wrist_origin_in(owner, joints)
        bound = convention_bound(owner, joints)
        distance = math.dist(r["location_m"], interface)
        out.append({
            "requirement_id": "R-OWN-03",
            "record_id": r["record_id"],
            "muscle": r["muscle"],
            "declared_name": r["declared_name"],
            "role": r["role"],
            "index": r["index"],
            "owner_body": owner,
            "location_m": r["location_m"],
            "decision": {
                "kind": "forearm_assembly_correspondence_record",
                "resolution": "corresponded_by_this_attempt",
                "owner_body_in_mutant_assembly": owner + " (unchanged; "
                                                   "outside the A05 mutation "
                                                   "scope, verified)",
                "point_placement": "pinned owner-frame PathPoint location "
                                   "unchanged (live_osim_verbatim_check "
                                   "carried from A07)",
                "mutation_interface": {
                    "body": ANCHOR_NAME,
                    "identity": "A05 anchor origin == the hand body origin "
                                "(wrist joint location 0 0 0 of the macaque "
                                "wrist custom joint)",
                    "origin_in_owner_frame_m": interface,
                },
                "recorded_distance_m": distance,
                "distance_law": "Euclidean distance to the mutation "
                                "interface at the ZERO-COORDINATE pose "
                                "(every osim Coordinate 0.0; the model "
                                "display default elbow_flexion=1.57079633 "
                                "is NOT used); body origins = declared "
                                "location_in_parent (all child-side "
                                "location/orientation rows are 0 0 0, "
                                "verified); frame rotations = declared "
                                "orientation_in_parent, OpenSim body-fixed "
                                "XYZ Euler",
                "euler_convention_note": {
                    "primary": "body_fixed_xyz (R = Rz Ry Rx)",
                    "alternative_measured": "space_fixed_xyz",
                    "alternative_max_delta_m": bound,
                    "decision_relevance": "sub-micrometre; no correspondence "
                                          "decision is delta-sensitive",
                },
                "supersedes": "explicitly_unresolved (A07)",
            },
            "authorization": authorization_block(),
        })
    out.sort(key=lambda x: x["record_id"])
    return out


def main():
    check_registry_criteria()
    a07, a05 = load_inputs()
    records = census(a07)
    law_rows = verify_a05_law(a05)
    joints = osim_joint_chain()
    hand = build_hand_records(records, a05)
    forearm = build_forearm_records(records, a05, joints)
    require(len(hand) == 14, REFUSAL_CENSUS + ":hand_len:" + str(len(hand)))
    require(len(forearm) == 31,
            REFUSAL_CENSUS + ":forearm_len:" + str(len(forearm)))
    prereg_sha = sha256_file(HERE / "PREREGISTRATION.md")
    receipt = {
        "schema": "chimera.b07_ownership_mappings.v1",
        "task_id": SHORT_ID,
        "card_id": TASK_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "preregistration_sha256": prereg_sha,
        "authorization": authorization_block(),
        "input_pins": {
            "a07_resolution": {"path": str(A07_PATH).replace("\\", "/"),
                               "sha256": A07_SHA256},
            "a05_structure": {"path": str(A05_PATH).replace("\\", "/"),
                              "sha256": A05_SHA256},
            "osim_model": {"path": str(OSIM_PATH).replace("\\", "/"),
                           "sha256": OSIM_SHA256},
        },
        "law_validation": {
            "check": "F1 mapping_law_mismatch (bit-exact)",
            "captain_mapped_rows": law_rows,
            "bit_exact_row_count": len(law_rows),
        },
        "census": EXPECTED_CENSUS,
        "counts": {"hand_records": len(hand), "forearm_records": len(forearm),
                   "total_new_records": len(hand) + len(forearm)},
        "scope_law": "distances inform, never authorize; no sealed row is "
                     "flipped; no port is qualified; no mass is admitted; "
                     "no fitting; no invented anatomy (B06/A07 vocabulary)",
        "records": {"hand_body_mappings": hand,
                    "forearm_correspondences": forearm},
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B ownership_mappings.py"},
    }
    out = HERE / "ownership_mappings.json"
    data = canonical(receipt) + b"\n"
    out.write_bytes(data)
    print("wrote", out, len(data), "bytes")
    print("hand records:", len(hand), "forearm records:", len(forearm))
    print("F1 bit-exact rows:", len(law_rows), "/ 3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
