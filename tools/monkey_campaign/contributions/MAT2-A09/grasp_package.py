"""MAT2-A09: issue the grasp anatomy input package (one versioned document).

Implements the frozen PREREGISTRATION.md (this directory, commits 2640fa86 +
Amendment A1 8079b0a6) exactly: ONE versioned package document
(schema chimera.a09_grasp_anatomy_package.v1) built ONLY from pinned sealed
upstream bytes, carrying supported mappings, parameters, provenance, explicit
gaps, the skeletal/tissue/interface graph, each explicit reduction
(RED-1..RED-7) and the material-first removal closure (removal of represented
tissue removes its mechanical connections; per-muscle degrees sum to exactly
74 = 48 path records + 26 attachment interfaces).

Upstream authority, read verbatim and unmodified (sha-pinned; drift refuses
`input_pin_drift`): A06 attachment_ownership.v1, A07
attachment_placement_resolution.v1, A08 a08_parameter_envelope.v1, A05
mutation structure, M02 pinned arm model + graph rows, M03 pressure_state,
M04 arm_rigid_laws, M05 interface_state, M09 experiment receipt/trace, and
the completion-map catalog records (C01/C05/C06/C17/C18).

The registries are READ-ONLY to this card: no upstream byte changes, no
rebuilt variants. No fitting experiment is run or simulated (sealed A07 law:
the whole-document scan refuses fitted*/optimized* keys). No new numerical
result is claimed: every number in the document is a count, a verbatim
carried value, or a sha256. C17 stays open exactly as A06/A07 left it.

CPU-only; stdlib; deterministic (no stochastic inputs, no wall-clock; two
consecutive --emit runs are byte-identical). Refusals are named codes;
nothing is silently repaired.

Modes:
  --emit        build + verify, write grasp_package.json (canonical bytes)
  --verify      load + verify the on-disk document against pinned bytes
  --self-check  build + verify in memory (no write)
  --falsify     run tamper arms FB1-FB7 (clean control first, named
                premature guards), write evidence/falsifier_receipt.json
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
REPO_ROOT = CONTRIB.parent.parent.parent          # .../checkout
DOC_PATH = HERE / "grasp_package.json"

SCHEMA = "chimera.a09_grasp_anatomy_package.v1"
OBJECT_ID = "mat2_a09_grasp_anatomy_package"
REVISION = 1
TASK_ID = "MAT2-A09"
TASK_ID_SHORT = "A09"
DATE_FROZEN = "2026-09-30"
CRITERIA_SHA256 = "f56d4ddbb0cf92a0897d30cda743a37554d9d7a30c6d69f151c6b41360f6026f"
SCOPE_SHA256 = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
DEFINITION_RAW_SHA256 = "57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1"
ATTEMPT_ID = "2c3a18f2fa494ce1a06ca691dd9fe03c"
AGENT_ID = "chimera-worker-A09"
BASE_HEAD = "ee2bcb98cd627b796662edaf9ad75b8c1f7f7be5"
PREREG_SHAS = {
    "PREREGISTRATION.md_freeze_2640fa86": True,
    "PREREGISTRATION.md_amendment_A1_8079b0a6": True,
}
DONE_WHEN_VERBATIM = (
    "One versioned package carries supported mappings, parameters, provenance "
    "and explicit gaps. Material-first addition: Package the skeletal/tissue/"
    "interface graph and each explicit reduction; removal of represented "
    "tissue must remove its mechanical connection.")
CARD_OBSERVATION_VERBATIM = "Anatomy completion does not itself prove climbing"
CARD_FALSIFIER_VERBATIM = (
    "Wrong owner/frame, hidden outside placement, clipped/occluded subject or "
    "label ambiguity fails. View toggles must preserve the physical state hash.")

# ---- input pins (PREREGISTRATION.md section 4 + Amendment A1) --------------
# role -> (kind, path, sha256); kind 'repo' paths are relative to the repo root.
PINS = {
    "a06_ownership": ("repo", "tools/monkey_campaign/contributions/MAT2-A06/attachment_ownership.json",
                      "f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c"),
    "a07_placement_resolution": ("repo", "tools/monkey_campaign/contributions/MAT2-A07/placement_resolution.json",
                                 "cd596d7c21fa81a4c2632e13b63ba26e62da51d44eca2355147fd5dff1587490"),
    "a08_parameter_envelope": ("repo", "tools/monkey_campaign/contributions/MAT2-A08/parameter_envelope.json",
                               "2fb43fd44f13e8b927142d72b79d36246ee7d71fd954a39ffeb12b74dc716424"),
    "a05_mutation_structure": ("repo", "tools/monkey_campaign/contributions/MAT2-A05/mutation_structure.json",
                               "48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649"),
    "m02_osim": ("repo", "tools/monkey_campaign/contributions/MAT2-M02/data/macaque_arm/monkeyArm_current.osim",
                 "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"),
    "m02_graph_pins": ("repo", "tools/monkey_campaign/contributions/MAT2-M02/data/graph_pins.json",
                       "849f9988d1a6ccb451bb45d79f298dd954c4e5605acd19d7d882a5c70a285b97"),
    "m03_pressure_state": ("repo", "tools/monkey_campaign/contributions/MAT2-M03/pressure_state.json",
                           "8182da4720f26154dfff3c54711e66cb318cc7bb9c989de77b7ee0a2f2b2ec03"),
    "m04_arm_rigid_laws": ("repo", "tools/monkey_campaign/contributions/MAT2-M04/arm_rigid_laws.json",
                           "a9e971db4b36c1a6c35f9c27171ebd06787d5ffc96d58cd4b039e9e4e7f02d32"),
    "m05_interface_state": ("repo", "tools/monkey_campaign/contributions/MAT2-M05/interface_state.json",
                            "c09bdf0564d152fa8b9a41489bd874fd0570f75e40ed3ce848f4c474fd0320c6"),
    "m09_experiment_receipt": ("repo", "tools/monkey_campaign/contributions/MAT2-M09/experiment_receipt.json",
                               "b949374dd9a9b7918daf179d0bf415ab88e1032d52721c8fb794abe31b6ccf24"),
    "m09_experiment_trace": ("repo", "tools/monkey_campaign/contributions/MAT2-M09/experiment_trace.json",
                             "273dbc4f8c73a6f562c0260050f7d23012288af29426f4d7b8a191b35efeb744"),
    "completion_map": ("repo", "tools/monkey_campaign/monkey_completion_map.json",
                       "3efbfb141299d7cad63724431f7e5269febe15eee68d812b80d91de324385b84"),
    "host_osim": ("host", "E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim",
                  "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"),
    "host_hand_vtp": ("host", "E:/PythonChimera/tools/science_funnel/data/macaque_arm/Geometry/hand.vtp",
                      "a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6"),
}

# ---- frozen counts (PREREGISTRATION.md section 7) --------------------------
FROZEN = {
    "a06_path_records": 48,
    "a06_attachments": 26,
    "a06_bonds": 22,
    "a06_containment_edges": 31,
    "a06_grasp_endpoints": 6,
    "grasp_scope_muscles": 13,
    "path_role_origin_attachment": 13,
    "path_role_insertion_attachment": 13,
    "path_role_path_waypoint": 21,
    "path_role_conditional_waypoint": 1,
    "path_owner_radius": 18,
    "path_owner_hand": 17,
    "path_owner_humerus": 8,
    "path_owner_ulna": 5,
    "attach_bone_hand": 13,
    "attach_bone_humerus": 8,
    "attach_bone_ulna": 4,
    "attach_bone_radius": 1,
    "endpoint_owner_distal_plus_anchor": 6,
    "a07_path_resolutions": 48,
    "a07_attachment_resolutions": 26,
    "a07_waypoint_resolutions": 22,
    "a07_endpoint_resolutions": 6,
    "a07_mutant_mapped": 3,
    "a07_pending_assembly_mapping": 14,
    "a07_envelope_measured_outside": 8,
    "a07_outside_insertions": 4,
    "a07_outside_waypoints": 4,
    "a07_pending_and_outside": 7,
    "a08_actuator_rows": 39,
    "a08_engineering_rows": 15,
    "a08_unresolved_entries": 8,
    "skeletal_nodes": 24,
    "tissue_nodes": 39,
    "tissue_grasp_relevant": 13,
    "tissue_parameters_only": 26,
    "connections_total": 74,
    "reductions": 7,
    "contracts": 5,
}

GRASP_MUSCLES = [
    "abd_poll_longus", "ext_carp_rad_brevis", "ext_carpi_rad_longus",
    "ext_carpi_ulnaris", "ext_digiti", "ext_digitorum", "ext_indicis",
    "flex_carpi_radialis", "flex_carpi_ulnaris", "flex_digit_profundus",
    "flex_digit_superficialis", "flex_poll_longus", "palmaris_longus"]
FOREARM_SKELETAL = ["humerus", "ulna", "radius", "hand"]
MUTATION_FRAME = "macaque_arm_hand_mutation_frame"
OSIM_HAND_FRAME = "osim.body.hand"

PROVENANCE_CLASSES = ("source_backed", "declared_carrier_not_source_backed",
                      "chosen_engineering", "explicitly_unresolved")


class Refusal(ValueError):
    """Named refusal; the message IS the machine code + detail."""


def require(cond, code, detail=""):
    if not cond:
        raise Refusal(f"{code}: {detail}")


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# ---------- pinned input loading ----------
def pin_root(kind):
    return REPO_ROOT if kind == "repo" else None


def load_pins(override_dir=None):
    """Load + sha-verify every pinned input; returns {role: parsed json}.

    override_dir: when set, 'repo' pins are read from this directory tree
    (falsifier FB7 uses a tampered copy tree; nothing on disk is mutated).
    """
    docs = {}
    for role, (kind, rel, want) in PINS.items():
        if kind == "repo":
            path = pathlib.Path(pin_root("repo")) / rel
            if override_dir is not None:
                cand = pathlib.Path(override_dir) / rel
                if cand.is_file():   # tampered COPY shadowing the pinned file
                    path = cand
        else:
            path = pathlib.Path(rel)
        got = sha256_file(path)
        require(got == want, "input_pin_drift",
                f"{role} expected {want} got {got} at {path}")
        if path.suffix == ".json":
            docs[role] = json.loads(path.read_text(encoding="utf-8"))
        else:
            docs[role] = {"_bytes_sha256": got, "_path": str(path).replace("\\", "/")}
    return docs


# ---------- builders ----------
def build_frame_chain(P):
    a06 = P["a06_ownership"]
    frames = a06["frames"]
    require(frames["mutant_frame"]["frame_id"] == MUTATION_FRAME, "a06_frame_shape")
    require(frames["osim_hand_frame"]["frame_id"] == OSIM_HAND_FRAME, "a06_frame_shape")
    m02 = P["m02_graph_pins"]
    require(m02["model"]["units"]["length"] == "m", "m02_units")
    return {
        "frames": frames,
        "law": ("every packaged position carries its source frame declaration; "
                "NO transform is composed between frames and NO new fit is "
                "recorded (C01: the round-trip/handedness/landmark verification "
                "is registered as still REQUIRED downstream)"),
        "osim_model_frame_note": ("M02 graph_pins body_frames (11 frames incl. "
                                  "ground/sternum/clavicle/scapula) stay a pinned "
                                  "REFERENCE for the C01 chain; shoulder-chain "
                                  "bodies are outside the grasp-scope package "
                                  "(explicit, not silent)"),
        "hand_vtp_capture_context_sha256": P["host_hand_vtp"]["_bytes_sha256"],
    }


def build_skeletal_graph(P):
    a05 = P["a05_mutation_structure"]
    a06 = P["a06_ownership"]
    bodies = a05["bodies"]
    require(len(bodies) == 19, "a05_body_count", str(len(bodies)))
    nodes = []
    for b in bodies:
        nodes.append({"node_id": b["id"], "name": b["name"], "kind": "skeletal",
                      "source": "a05_mutation_structure", "parent": b["parent"],
                      "status": b.get("status")})
    nodes.append({"node_id": "ref.macaque_arm_hand_mutation.body.macaque_hand_anchor",
                  "name": "macaque_hand_anchor", "kind": "skeletal",
                  "source": "a06_bonds/a05_anchor_transfer", "parent": None,
                  "status": "recorded_anchor"})
    for name in FOREARM_SKELETAL:
        nodes.append({"node_id": "osim.body." + name, "name": name,
                      "kind": "skeletal", "source": "a06_path_owner/a06_attachment_bone",
                      "parent": None, "status": "grasp_scope_forearm"})
    require(len(nodes) == FROZEN["skeletal_nodes"], "skeletal_node_count",
            str(len(nodes)))
    node_ids = {n["node_id"] for n in nodes}
    bonds = a06["bonds"]
    containment = a06["containment_edges"]
    require(len(bonds) == FROZEN["a06_bonds"], "bond_count")
    require(len(containment) == FROZEN["a06_containment_edges"], "containment_count")
    for b in bonds:
        require(b["child_body"] in node_ids, "bond_child_unknown_body",
                b["bond_id"] + " -> " + b["child_body"])
    for e in containment:
        require(e.get("kind") == "containment", "containment_kind", e.get("edge_id", "?"))
    return {
        "nodes": nodes,
        "bonds_carried": bonds,
        "containment_edges_carried": containment,
        "law_statement": a06["law_statement"],
        "note": ("bonds and containment edges are carried verbatim; A06 law: "
                 "containment edges and rig parentage are placement/ontology "
                 "only; a mechanical bond or tissue-to-bone attachment exists "
                 "only through its explicit record"),
    }


def build_tissue_graph(P):
    a08 = P["a08_parameter_envelope"]
    rows = a08["biological_registry"]["actuator_rows"]
    require(len(rows) == FROZEN["a08_actuator_rows"], "actuator_row_count")
    grasp = set(GRASP_MUSCLES)
    nodes = []
    for r in rows:
        m = r["osim_muscle"]
        nodes.append({
            "node_id": "muscle." + m,
            "osim_muscle": m,
            "kind": "tissue_muscle",
            "grasp_relevant": m in grasp,
            "parameter_row": r,
            "parameters_source": {
                "document": "repo:tools/monkey_campaign/contributions/MAT2-A08/parameter_envelope.json",
                "sha256": PINS["a08_parameter_envelope"][2],
                "registry": "biological_registry",
            },
            "provenance_class": r["source_class"],
            "path_geometry": ("packaged" if m in grasp else
                              "not_packaged_grasp_scope_boundary (explicit gap, "
                              "never silently dropped)"),
        })
    require(len(nodes) == FROZEN["tissue_nodes"], "tissue_node_count")
    n_grasp = sum(1 for n in nodes if n["grasp_relevant"])
    require(n_grasp == FROZEN["tissue_grasp_relevant"], "grasp_relevant_count")
    require(n_grasp + FROZEN["tissue_parameters_only"] == FROZEN["tissue_nodes"],
            "tissue_partition")
    for n in nodes:
        require(n["provenance_class"] in PROVENANCE_CLASSES, "provenance_vocabulary",
                n["node_id"] + " " + str(n["provenance_class"]))
    return {"nodes": nodes}


def build_interface_graph(P):
    a06 = P["a06_ownership"]
    a07 = P["a07_placement_resolution"]
    path_records = a06["path_records"]
    attachments = a06["attachments"]
    endpoints = a06["grasp_endpoints"]
    require(len(path_records) == FROZEN["a06_path_records"], "path_record_count")
    require(len(attachments) == FROZEN["a06_attachments"], "attachment_count")
    require(len(endpoints) == FROZEN["a06_grasp_endpoints"], "endpoint_count")
    role_counts = {}
    for r in path_records:
        role_counts[r["role"]] = role_counts.get(r["role"], 0) + 1
    require(role_counts == {"origin_attachment": FROZEN["path_role_origin_attachment"],
                            "insertion_attachment": FROZEN["path_role_insertion_attachment"],
                            "path_waypoint": FROZEN["path_role_path_waypoint"],
                            "conditional_waypoint": FROZEN["path_role_conditional_waypoint"]},
            "path_role_counts", json.dumps(role_counts))
    owner_counts = {}
    for r in path_records:
        owner_counts[r["owner_body"]] = owner_counts.get(r["owner_body"], 0) + 1
    require(owner_counts == {"radius": FROZEN["path_owner_radius"],
                             "hand": FROZEN["path_owner_hand"],
                             "humerus": FROZEN["path_owner_humerus"],
                             "ulna": FROZEN["path_owner_ulna"]},
            "path_owner_counts", json.dumps(owner_counts))
    bone_counts = {}
    for a in attachments:
        bone_counts[a["bone"]] = bone_counts.get(a["bone"], 0) + 1
    require(bone_counts == {"hand": FROZEN["attach_bone_hand"],
                            "humerus": FROZEN["attach_bone_humerus"],
                            "ulna": FROZEN["attach_bone_ulna"],
                            "radius": FROZEN["attach_bone_radius"]},
            "attach_bone_counts", json.dumps(bone_counts))
    require(all(e["owner_body"].startswith("ref.macaque_arm_hand_mutation.body.")
                for e in endpoints), "endpoint_owner_form")

    a07_path = {r["record_id"]: r for r in a07["path_resolutions"]}
    a07_att = {r["attachment_id"]: r for r in a07["attachment_resolutions"]}
    a07_wp = {r["path_record_id"]: r for r in a07["waypoint_resolutions"]}
    require(len(a07_path) == FROZEN["a07_path_resolutions"], "a07_path_res_count")
    require(len(a07_att) == FROZEN["a07_attachment_resolutions"], "a07_att_res_count")
    require(len(a07_wp) == FROZEN["a07_waypoint_resolutions"], "a07_wp_res_count")
    a07_ep = {r["endpoint_id"]: r for r in a07["grasp_endpoint_resolutions"]}
    require(len(a07_ep) == FROZEN["a07_endpoint_resolutions"], "a07_ep_res_count")

    connections = []
    for r in path_records:
        res = a07_path.get(r["record_id"])
        require(res is not None, "a07_resolution_missing", r["record_id"])
        require(res["muscle"] == r["muscle"], "connection_muscle_join", r["record_id"])
        require(res["owner_body"] == r["owner_body"], "wrong_owner",
                r["record_id"])
        connections.append({
            "connection_id": r["record_id"],
            "kind": "tendon_path_record",
            "muscle_node": "muscle." + r["muscle"],
            "owner_body": "osim.body." + r["owner_body"],
            "role": r["role"],
            "location_m": r["location_m"],
            "frame_decl": OSIM_HAND_FRAME,
            "frame_note": ("owner-body-local per A06 frames.osim_hand_frame; "
                           "carried verbatim, no transform composed"),
            "on_hand_body": r["on_hand_body"],
            "terminal_resolution": {
                "state": res["resolution"],
                "placement_failed_outside": res["placement_failed_outside"],
                "mutant_mapping_status": res["mutant_mapping_status"],
                "envelope_measurement": res["envelope_measurement"],
            },
            "carried_from": "a07_placement_resolution.path_resolutions",
        })
    for a in attachments:
        res = a07_att.get(a["attachment_id"])
        require(res is not None, "a07_resolution_missing", a["attachment_id"])
        muscle = a["attachment_id"].split(".")[1]
        require(res.get("tissue") == muscle or res.get("tissue") is None,
                "attachment_tissue_join", a["attachment_id"])
        connections.append({
            "connection_id": a["attachment_id"],
            "kind": "attachment_interface",
            "muscle_node": "muscle." + muscle,
            "owner_body": "osim.body." + a["bone"],
            "interface_id": a["interface_id"],
            "path_record_id": res.get("path_record_id"),
            "role": res["role"],
            "location_m": a["location_m"],
            "frame_decl": OSIM_HAND_FRAME,
            "frame_note": ("owner-body-local per A06 frames.osim_hand_frame; "
                           "carried verbatim, no transform composed"),
            "terminal_resolution": {
                "state": res["resolution"],
                "osim_reference_placement": res["osim_reference_placement"],
                "placement_failed_outside": res["placement_failed_outside"],
            },
            "c17_status": "carried_open",
            "carried_from": "a07_placement_resolution.attachment_resolutions",
        })
    waypoint_rows = []
    for r in path_records:
        if r["role"] in ("path_waypoint", "conditional_waypoint"):
            wres = a07_wp.get(r["record_id"])
            require(wres is not None, "a07_waypoint_resolution_missing", r["record_id"])
            waypoint_rows.append(dict(wres))
    require(len(waypoint_rows) == FROZEN["a07_waypoint_resolutions"],
            "waypoint_resolution_join", str(len(waypoint_rows)))
    endpoint_rows = []
    for e in endpoints:
        res = a07_ep.get(e["endpoint_id"])
        require(res is not None, "a07_resolution_missing", e["endpoint_id"])
        require(res["owner_body"] == e["owner_body"], "wrong_owner", e["endpoint_id"])
        endpoint_rows.append({
            "endpoint_id": e["endpoint_id"],
            "owner_body": e["owner_body"],
            "position_m": e["position_m"],
            "frame_decl": MUTATION_FRAME,
            "frame_note": ("A06 frames.mutant_frame: recorded A05 anchor "
                           "transfer, coordinates in the macaque hand frame; "
                           "carried verbatim, no transform composed"),
            "role": res["role"],
            "terminal_resolution": {"state": res["resolution"]},
            "approved_by": e["approved_by"],
            "carried_from": "a07_placement_resolution.grasp_endpoint_resolutions",
        })
    return {
        "connections": connections,
        "waypoint_resolutions_carried": waypoint_rows,
        "grasp_endpoints": endpoint_rows,
        "c17_block": a07["c17"],
        "carried_observation": a07["carried_observation"],
    }


def compute_removal_closure(interface):
    """Material-first law: removing a muscle removes EXACTLY its connections."""
    per_muscle = {m: {"path_records": 0, "attachment_interfaces": 0,
                      "connection_ids": []} for m in GRASP_MUSCLES}
    for c in interface["connections"]:
        m = c["muscle_node"].split(".", 1)[1]
        require(m in per_muscle, "connection_outside_grasp_scope", c["connection_id"])
        key = ("path_records" if c["kind"] == "tendon_path_record"
               else "attachment_interfaces")
        per_muscle[m][key] += 1
        per_muscle[m]["connection_ids"].append(c["connection_id"])
    total = 0
    for m, d in per_muscle.items():
        require(len(d["connection_ids"]) == d["path_records"] + d["attachment_interfaces"],
                "per_muscle_degree", m)
        total += d["path_records"] + d["attachment_interfaces"]
    require(total == FROZEN["connections_total"], "connections_total",
            str(total))
    return {
        "law": ("removal of a represented tissue node removes EXACTLY its "
                "incident mechanical connections; the reduced package must "
                "have zero dangling references (dynamic precedent: sealed M09 "
                "T4 release removes ALL bond-type connective material bitwise)"),
        "per_muscle": per_muscle,
        "connections_total": total,
        "grasp_muscles": len(per_muscle),
    }


def reduced_package(doc, muscle):
    """Apply the declared removal operator to an in-memory package document."""
    red = copy.deepcopy(doc)
    node = "muscle." + muscle
    red["tissue_graph"]["nodes"] = [n for n in red["tissue_graph"]["nodes"]
                                    if n["node_id"] != node]
    red["interface_graph"]["connections"] = [
        c for c in red["interface_graph"]["connections"]
        if c["muscle_node"] != node]
    red["removal_closure"]["applied_removals"] = red["removal_closure"].get(
        "applied_removals", []) + [node]
    return red


def check_no_dangling(doc, expect_removed=None):
    """P7 closure: every remaining connection references existing nodes."""
    tissue = {n["node_id"] for n in doc["tissue_graph"]["nodes"]}
    skeletal = {n["node_id"] for n in doc["skeletal_graph"]["nodes"]}
    for c in doc["interface_graph"]["connections"]:
        require(c["muscle_node"] in tissue, "dangling_connection_after_removal",
                c["connection_id"] + " -> " + c["muscle_node"])
        require(c["owner_body"] in skeletal, "dangling_owner_after_removal",
                c["connection_id"] + " -> " + c["owner_body"])
    for e in doc["interface_graph"]["grasp_endpoints"]:
        require(e["owner_body"] in skeletal, "dangling_owner_after_removal",
                e["endpoint_id"])
    for b in doc["skeletal_graph"]["bonds_carried"]:
        require(b["child_body"] in skeletal, "dangling_bond_after_removal",
                b["bond_id"])
    return True


def build_reductions(P):
    m09r = P["m09_experiment_receipt"]
    m09t = P["m09_experiment_trace"]
    probes = m09r["probes"]
    require(m09r["probes"]["X1_pass"] is True, "m09_x1_pass")
    bound_rev = max(int(k) for k in m09t["documents"])
    bound_doc = m09t["documents"][str(bound_rev)]["document"]
    return [
        {"id": "RED-1", "name": "rigid-by-declaration passive law",
         "reduces": "arm-segment passive response to declared rigidity",
         "sealed_source": {"document": "repo:tools/monkey_campaign/contributions/MAT2-M04/arm_rigid_laws.json",
                           "sha256": PINS["m04_arm_rigid_laws"][2]},
         "carried": {"region_assignments": len(P["m04_arm_rigid_laws"]["assignments"])},
         "removal_semantics": ("removing the declaration reverts the region to "
                               "unpinned passive behavior; no mechanical "
                               "connection is silently retained (the A08 "
                               "engineering row set is the ONLY carrier)")},
        {"id": "RED-2", "name": "active-pressure membrane tissue",
         "reduces": "soft-tissue volume to the authored membrane carrier",
         "sealed_source": {"document": "repo:tools/monkey_campaign/contributions/MAT2-M03/pressure_state.json",
                           "sha256": PINS["m03_pressure_state"][2]},
         "carried": {"object_id": P["m03_pressure_state"]["object_id"],
                     "schema": P["m03_pressure_state"]["schema"],
                     "revision": P["m03_pressure_state"]["revision"]},
         "removal_semantics": ("removing the membrane removes its mass and "
                               "pressure constants from the package; they "
                               "appear ONLY under engineering_carriers and "
                               "never re-enter the tissue namespace")},
        {"id": "RED-3", "name": "loose-bones assembly by explicit connective matter",
         "reduces": "joints to explicit bonds + local contact (no joint elements)",
         "sealed_source": {"document": "repo:tools/monkey_campaign/contributions/MAT2-M09/",
                           "receipt_sha256": PINS["m09_experiment_receipt"][2],
                           "trace_sha256": PINS["m09_experiment_trace"][2]},
         "carried": {"x1_pass": probes["X1_pass"],
                     "t4_bitwise_zero_after_release":
                         probes["T4"]["bitwise_zero_after_release"],
                     "t4_released_doc_bond_count":
                         probes["T4"]["released_doc_bond_count"],
                     "t4_e_diss_release_j": probes["T4"]["e_diss_release_j"],
                     "bound_doc_revision": bound_rev,
                     "bound_doc_bonds": len(bound_doc["bonds"]),
                     "bound_doc_contacts": len(bound_doc["contacts"]),
                     "bound_doc_regions": len(bound_doc["regions"]),
                     "t5_refusals": probes["T5"]["refusals"]},
         "removal_semantics": ("the measured M09 release IS the removal law: "
                               "explicit release removes ALL bond-type "
                               "connective material bitwise "
                               "(T4 bitwise_zero_after_release true)")},
        {"id": "RED-4", "name": "measurement-only restraint",
         "reduces": "constraint bookkeeping to a per-tick derived record",
         "sealed_source": {"document": "repo:tools/monkey_campaign/contributions/MAT2-M09/",
                           "receipt_sha256": PINS["m09_experiment_receipt"][2]},
         "carried": {"ast_restraint_probe": probes["p_ast_restraint"]["ok"],
                     "ast_no_joint_probe": probes["p_ast_no_joint"]["ok"]},
         "removal_semantics": ("the restraint record never applies force and "
                               "vanishes bitwise with the connections it is "
                               "derived from (M09 P-AST-restraint)")},
        {"id": "RED-5", "name": "axis-aligned envelope bounds test",
         "reduces": "mesh-inside placement tests to the A05-recorded per-axis "
                    "bounds measurement (declared approximation)",
         "sealed_source": {"document": "repo:tools/monkey_campaign/contributions/MAT2-A07/placement_resolution.json",
                           "sha256": PINS["a07_placement_resolution"][2]},
         "carried": {"envelope_test": P["a07_placement_resolution"]["envelope_test"]},
         "removal_semantics": ("removing the reduction removes the recorded "
                               "outside/inside classifications with it; the "
                               "package never carries a classification without "
                               "its instrument")},
        {"id": "RED-6", "name": "osim path-point tendon reduction",
         "reduces": "tendon geometry to path-point records + parameter rows "
                    "(no volumes; muscle mass/PCSA absent, U-gaps carried)",
         "sealed_source": {"documents": ["repo:tools/monkey_campaign/contributions/MAT2-A06/attachment_ownership.json",
                                         "repo:tools/monkey_campaign/contributions/MAT2-A08/parameter_envelope.json"],
                           "sha256s": [PINS["a06_ownership"][2],
                                       PINS["a08_parameter_envelope"][2]]},
         "carried": {"path_point_records": FROZEN["a06_path_records"]},
         "removal_semantics": ("a muscle's path-point records ARE its "
                               "mechanical geometry; removal takes them "
                               "(see removal_closure)")},
        {"id": "RED-7", "name": "hand mutation structure",
         "reduces": "digit anatomy to the authored hybrid mutant structure "
                    "with its recorded assembly mapping",
         "sealed_source": {"document": "repo:tools/monkey_campaign/contributions/MAT2-A05/mutation_structure.json",
                           "sha256": PINS["a05_mutation_structure"][2]},
         "carried": {"bodies": len(P["a05_mutation_structure"]["bodies"]),
                     "captain_decision": P["a05_mutation_structure"]["captain_decision"]},
         "removal_semantics": ("removing a digit body removes its bonds, its "
                               "endpoint ownership and every connection that "
                               "references it; the closure check refuses any "
                               "dangling survivor")},
    ]


def build_engineering_carriers(P):
    a08 = P["a08_parameter_envelope"]
    eng = a08["engineering_registry"]
    require(eng["row_count"] == FROZEN["a08_engineering_rows"], "eng_row_count")
    m05 = P["m05_interface_state"]
    return {
        "rows_carried": eng["rows"],
        "registry_note": eng["schema_note"],
        "disjointness": ("biological vs engineering namespaces share zero row "
                         "identity (sealed A08 law, inherited)"),
        "m05_interface_carrier": {
            "schema": m05["schema"], "task": m05["task"],
            "object_id": m05["bound_summary"]["object_id"],
            "bound_summary": m05["bound_summary"],
            "sha256": PINS["m05_interface_state"][2],
            "role": "bond/contact port semantics carrier (engineering)"},
        "m09_demonstrator_rig": {
            "note": ("demonstrator rig, never biological: two bone-shaped XPBD "
                     "scaffolds + 2 explicit bonds + 1 local contact at the "
                     "bound revision"),
            "sha256s": {"experiment_receipt": PINS["m09_experiment_receipt"][2],
                        "experiment_trace": PINS["m09_experiment_trace"][2]}},
        "never_biological": True,
    }


def build_explicit_gaps(P):
    a08 = P["a08_parameter_envelope"]
    a07 = P["a07_placement_resolution"]
    a07wp = [r["path_record_id"] for r in a07["waypoint_resolutions"]]
    pending = [c["connection_id"] for c in P["_interface"]["connections"]
               if c["terminal_resolution"].get("mutant_mapping_status")
               == "pending_assembly_mapping"]
    require(len(pending) == FROZEN["a07_pending_assembly_mapping"],
            "pending_count", str(len(pending)))
    outside = [c["connection_id"] for c in P["_interface"]["connections"]
               if c["kind"] == "tendon_path_record"
               and c["terminal_resolution"].get("placement_failed_outside")]
    require(len(outside) == FROZEN["a07_envelope_measured_outside"],
            "outside_count", str(len(outside)))
    gaps = []
    for u in a08["unresolved_entries"]:
        gaps.append({"gap_id": "A08-" + u["id"], "carried_from": "a08_parameter_envelope",
                     "entry": u})
    gaps.append({
        "gap_id": "A07-pending-assembly-mappings",
        "carried_from": "a07_placement_resolution",
        "count": len(pending),
        "record_ids": pending,
        "missing_evidence": "recorded_assembly_mapping_decision",
        "authorizing_rank": "recorded lead or captain decision",
    })
    gaps.append({
        "gap_id": "A07-measured-outside-placements",
        "carried_from": "a07_placement_resolution",
        "count": len(outside),
        "record_ids": outside,
        "note": ("measured outside the A05-recorded envelope bounds; carried "
                 "as declared deviations, never repaired here (no fitting)"),
    })
    gaps.append({
        "gap_id": "A09-grasp-scope-boundary-non-grasp-actuators",
        "count": FROZEN["tissue_parameters_only"],
        "detail": ("26 A08 actuator rows carry parameters but no packaged path "
                   "geometry: A06 grasp scope = muscles with at least one path "
                   "point on osim body 'hand'; C18 routing for these stays out "
                   "of grasp scope and is named, never silently dropped"),
        "authorizing_rank": "a separately scoped package extension card",
    })
    gaps.append({
        "gap_id": "A09-shoulder-chain-out-of-scope",
        "detail": ("M02 graph_pins shoulder-chain bodies (ground/sternum/"
                   "clavicle/scapula and other arm-region frames) are not "
                   "packaged; the grasp-scope skeletal set is the 19 A05 digit "
                   "bodies + anchor + {humerus, ulna, radius, hand}"),
        "authorizing_rank": "a separately scoped package extension card",
    })
    gaps.append({
        "gap_id": "A09-skin-fat-geometry-absent",
        "carried_from": "m02_graph_pins.scope_limitation",
        "detail": P["m02_graph_pins"]["scope_limitation"],
    })
    gaps.append({
        "gap_id": "C17-attachment-mechanics-open",
        "carried_from": "a06/a07",
        "status": "open",
        "required_inputs": a07["c17"]["required_inputs"],
        "note": ("no patch area/shape, areal stiffness, couple resistance or "
                 "weights exist in the pinned sources; none is invented "
                 "(no synthetic lambda_min)"),
    })
    return {
        "gaps": gaps,
        "carried_observation": {
            "verbatim": CARD_OBSERVATION_VERBATIM,
            "a07_carried": a07["carried_observation"],
            "resolution": "explicitly_unresolved (anatomy completion does not "
                          "itself prove climbing)",
        },
    }


def build_contracts(P):
    catalog = {}
    mapdoc = P["completion_map"]
    def collect(o):
        if isinstance(o, dict):
            if o.get("id") in ("C01", "C05", "C06", "C17", "C18") and "title" in o \
                    and o["id"] not in catalog:
                catalog[o["id"]] = o
            for v in o.values():
                collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
    collect(mapdoc)
    require(sorted(catalog) == ["C01", "C05", "C06", "C17", "C18"],
            "contract_catalog_missing", ",".join(sorted(catalog)))
    supply = {
        "C01": {"supplied_by": ["frame_chain"],
                "status_map": {"axes/units/conventions": "source_backed (A06 "
                               "frames + M02 graph_pins, pinned)",
                               "round-trip verification": "explicitly_unresolved "
                               "(registered still-REQUIRED downstream)"}},
        "C05": {"supplied_by": ["skeletal_graph", "interface_graph"],
                "status_map": {"joint axes/attachment frames": "declared "
                               "(A06 bonds + A05 parentage, carried verbatim)",
                               "limits": "explicitly_unresolved (no biological "
                               "ROM limits in pinned sources; A08 U-gaps)",
                               "FK/Jacobian evaluation": "explicitly_unresolved "
                               "(registered still-REQUIRED downstream)"}},
        "C06": {"supplied_by": ["tissue_graph", "engineering_carriers"],
                "status_map": {"mass/inertia": "declared (A08 rows; segment "
                               "bands INSIDE-1SD screens carried)",
                               "loads evaluation": "explicitly_unresolved "
                               "(registered still-REQUIRED downstream)"}},
        "C17": {"supplied_by": ["interface_graph"],
                "status_map": {"patch area/shape, areal stiffness, couple "
                               "resistance, weights, frame":
                               "explicitly_unresolved (open; A06/A07 carried "
                               "blocks verbatim; zero numbers)"}},
        "C18": {"supplied_by": ["interface_graph"],
                "status_map": {"owned endpoints/waypoints": "source_backed "
                               "(A06 ownership + A07 terminal resolutions)",
                               "joint positions": "declared (A05/M02 frames)",
                               "wrapping model": "explicitly_unresolved",
                               "l(q)/moment-arm evaluation":
                               "explicitly_unresolved (finite differences/"
                               "virtual work + unresolved-owner rejection "
                               "still REQUIRED downstream)"}},
    }
    rows = []
    for cid in ("C01", "C05", "C06", "C17", "C18"):
        c = catalog[cid]
        rows.append({
            "id": cid,
            "title": c["title"],
            "required_inputs_catalog": c["required_inputs"],
            "result_status": c["result_status"],
            "supplied_by": supply[cid]["supplied_by"],
            "per_input_status": supply[cid]["status_map"],
            "status": "OPEN INVENTORY (no new numerical result claimed)",
        })
    return rows


def build_consumer_contract():
    return [
        {"consumer": "MAT2-G01 (support and grip feasibility)",
         "consumes": ["skeletal_graph", "interface_graph.grasp_endpoints",
                      "tissue_graph actuator bounds"],
         "blocking_gaps": ["A08-U1 force envelope class",
                           "A07-pending-assembly-mappings"],
         "note": ("actuator bound claims stay declared_carrier, "
                  "force_runtime_ready false (A08 law)")},
        {"consumer": "MAT2-G02 (finite-area anatomical attachments)",
         "consumes": ["interface_graph.connection attachment_interfaces",
                      "calculation_contracts C17"],
         "blocking_gaps": ["C17-attachment-mechanics-open"],
         "note": ("C17 required_inputs are open; no synthetic lambda_min may "
                  "transfer (sealed catalog law)")},
        {"consumer": "MAT2-G03 (tendon lengths and moment arms)",
         "consumes": ["interface_graph.connections",
                      "calculation_contracts C18", "frame_chain"],
         "blocking_gaps": ["A09-grasp-scope-boundary-non-grasp-actuators"],
         "note": ("unresolved bodies cannot appear as zero arms (C18 "
                  "unresolved-owner rejection, registered downstream)")},
    ]


# ---------- whole-document validation (recompute-and-refuse) ----------
def validate_document(doc, P):
    """Recompute every carried fact from the pinned bytes; refuse on drift."""
    if "_interface" not in P:
        P["_interface"] = build_interface_graph(P)
    require(doc["schema"] == SCHEMA, "schema")
    # P6/P7 closure FIRST: a dangling reference voids every later count
    # conversation (also the correct first refusal for a tampered reduction).
    check_no_dangling(doc)
    require(doc["identity"]["criteria_sha256"] == CRITERIA_SHA256, "criteria_identity")
    require(doc["identity"]["scope_sha256"] == SCOPE_SHA256, "scope_identity")
    require(doc["identity"]["definition_raw_sha256"] == DEFINITION_RAW_SHA256,
            "definition_identity")
    require(doc["identity"]["task_id"] == TASK_ID, "task_identity")
    require(doc["identity"]["base_head"] == BASE_HEAD, "base_identity")

    # P2 frozen counts
    counts = doc["counts"]
    for k, v in FROZEN.items():
        require(counts.get(k) == v, "frozen_count_mismatch",
                f"{k}={counts.get(k)} want {v}")

    # P3 provenance totality
    for n in doc["tissue_graph"]["nodes"]:
        require(n.get("provenance_class") in PROVENANCE_CLASSES,
                "silent_default_refused", n["node_id"])
        require(n.get("parameter_row") is not None,
                "silent_default_refused", n["node_id"] + " missing parameter row")

    # P4 parameter carriage: field-for-field vs pinned A08 rows
    a08rows = {r["osim_muscle"]: r for r in
               P["a08_parameter_envelope"]["biological_registry"]["actuator_rows"]}
    compared_fields = 0
    for n in doc["tissue_graph"]["nodes"]:
        src = a08rows[n["osim_muscle"]]
        for k, v in src.items():
            require(n["parameter_row"].get(k) == v, "parameter_carriage_mismatch",
                    f"{n['node_id']}.{k}")
            compared_fields += 1
    eng_src = P["a08_parameter_envelope"]["engineering_registry"]["rows"]
    eng_doc = doc["engineering_carriers"]["rows_carried"]
    require(len(eng_doc) == len(eng_src), "parameter_carriage_mismatch", "eng count")
    for a, b in zip(eng_doc, eng_src):
        require(a == b, "parameter_carriage_mismatch", a.get("id", "?"))
        compared_fields += 1
    u_src = {u["id"]: u for u in P["a08_parameter_envelope"]["unresolved_entries"]}
    for g in doc["explicit_gaps"]["gaps"]:
        if g["gap_id"].startswith("A08-"):
            u = u_src[g["gap_id"].split("-", 1)[1]]
            require(g["entry"] == u, "parameter_carriage_mismatch", g["gap_id"])
            compared_fields += 1

    # P5 placement carriage + measured honesty (recompute the axis-aligned test)
    et = doc["explicit_reductions"][4]["carried"]["envelope_test"]
    lo, hi = et["bounds_lo_m"], et["bounds_hi_m"]
    a07map = {r["record_id"]: r for r in P["a07_placement_resolution"]["path_resolutions"]}
    outside_total = 0
    for c in doc["interface_graph"]["connections"]:
        src = a07map.get(c["connection_id"])
        if src is None:
            continue  # attachment interface rows are checked below
        require(c["terminal_resolution"]["state"] == src["resolution"],
                "placement_carriage_mismatch", c["connection_id"])
        require(c["owner_body"] == "osim.body." + src["owner_body"],
                "wrong_owner", c["connection_id"])
        em = c["terminal_resolution"]["envelope_measurement"]
        if em.get("in_scope"):
            pos = c["location_m"]
            recomputed = []
            for axis_i, axis in enumerate(("x", "y", "z")):
                if pos[axis_i] < lo[axis_i]:
                    recomputed.append({"axis": axis, "kind": "below_lo",
                                       "excess_m": pos[axis_i] - lo[axis_i]})
                elif pos[axis_i] > hi[axis_i]:
                    recomputed.append({"axis": axis, "kind": "above_hi",
                                       "excess_m": pos[axis_i] - hi[axis_i]})
            require(em["outside_axes"] == recomputed, "hidden_outside_refused",
                    c["connection_id"] + f" recomputed {recomputed}")
            require(c["terminal_resolution"]["placement_failed_outside"]
                    == bool(recomputed), "hidden_outside_refused",
                    c["connection_id"] + " flag vs recomputed")
            if recomputed:
                outside_total += 1
    a07att = {r["attachment_id"]: r for r in
              P["a07_placement_resolution"]["attachment_resolutions"]}
    for c in doc["interface_graph"]["connections"]:
        if c["kind"] != "attachment_interface":
            continue
        src = a07att.get(c["connection_id"])
        require(src is not None, "placement_carriage_mismatch", c["connection_id"])
        require(c["terminal_resolution"]["state"] == src["resolution"],
                "placement_carriage_mismatch", c["connection_id"])
        require(c.get("path_record_id") == src.get("path_record_id"),
                "placement_carriage_mismatch", c["connection_id"] + " join key")
        joined = a07map.get(c.get("path_record_id"))
        if joined is not None:
            require(c["terminal_resolution"]["placement_failed_outside"]
                    == joined["placement_failed_outside"],
                    "hidden_outside_refused",
                    c["connection_id"] + " vs joined path record")
    require(outside_total == FROZEN["a07_envelope_measured_outside"],
            "hidden_outside_refused", f"outside_total={outside_total}")

    # P6 owner/frame closure
    frames = {MUTATION_FRAME, OSIM_HAND_FRAME}
    for c in doc["interface_graph"]["connections"]:
        require(c["frame_decl"] in frames, "frame_mismatch_refused",
                c["connection_id"] + " " + c["frame_decl"])
    for e in doc["interface_graph"]["grasp_endpoints"]:
        require(e["frame_decl"] == MUTATION_FRAME, "frame_mismatch_refused",
                e["endpoint_id"])

    # P7 removal closure recompute
    rc = doc["removal_closure"]
    recomputed = compute_removal_closure(P["_interface"])
    require(rc["per_muscle"] == recomputed["per_muscle"], "removal_closure_mismatch")
    require(rc["connections_total"] == FROZEN["connections_total"],
            "removal_closure_mismatch", "total")
    deg_sum = sum(d["path_records"] + d["attachment_interfaces"]
                  for d in rc["per_muscle"].values())
    require(deg_sum == FROZEN["connections_total"], "removal_closure_mismatch",
            "degree sum")

    # P8 reduction ledger
    reds = doc["explicit_reductions"]
    require(len(reds) == FROZEN["reductions"], "reduction_count")
    for r in reds:
        require(r.get("removal_semantics"), "missing_removal_semantics", r["id"])
        require(r.get("sealed_source"), "missing_removal_semantics", r["id"])

    # P9 contracts vs pinned catalog text
    require(len(doc["calculation_contracts"]) == FROZEN["contracts"],
            "contract_count")
    catalog = {}
    def collect(o):
        if isinstance(o, dict):
            if o.get("id") in ("C01", "C05", "C06", "C17", "C18") and "title" in o \
                    and o["id"] not in catalog:
                catalog[o["id"]] = o
            for v in o.values():
                collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
    collect(P["completion_map"])
    for row in doc["calculation_contracts"]:
        c = catalog[row["id"]]
        require(row["title"] == c["title"], "contract_carriage_mismatch", row["id"])
        require(row["required_inputs_catalog"] == c["required_inputs"],
                "contract_carriage_mismatch", row["id"])
        require(row["result_status"] == c["result_status"],
                "contract_carriage_mismatch", row["id"])
        require(row["status"] == "OPEN INVENTORY (no new numerical result claimed)",
                "contract_carriage_mismatch", row["id"])
    require(doc["interface_graph"]["c17_block"] == P["a07_placement_resolution"]["c17"],
            "c17_carriage_mismatch")

    # P10 no fitting anywhere
    scan_fitting(doc)

    # frame pin + osim pin identity
    require(doc["frame_chain"]["hand_vtp_capture_context_sha256"]
            == PINS["host_hand_vtp"][2], "input_pin_drift", "hand_vtp")
    return {"compared_fields": compared_fields,
            "outside_total": outside_total}


def scan_fitting(doc):
    """Sealed A07 law: no fitted*/optimized* key anywhere."""
    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                kl = k.lower()
                if kl.startswith("fitted") or kl.startswith("optimized") \
                        or kl.endswith("_fit") or kl == "new_fit":
                    raise Refusal(f"fitting_unauthorized_refused: {path}/{k}")
                walk(v, path + "/" + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
    walk(doc)


# ---------- build ----------
def build_document():
    P = load_pins()
    interface = build_interface_graph(P)
    P["_interface"] = interface
    doc = {
        "schema": SCHEMA,
        "object_id": OBJECT_ID,
        "revision": REVISION,
        "identity": {
            "task_id": TASK_ID, "task_id_short": TASK_ID_SHORT,
            "title": "Issue the grasp anatomy input package",
            "criteria_sha256": CRITERIA_SHA256,
            "scope_sha256": SCOPE_SHA256,
            "definition_raw_sha256": DEFINITION_RAW_SHA256,
            "attempt_id": ATTEMPT_ID, "agent_id": AGENT_ID,
            "base_head": BASE_HEAD,
            "date_frozen": DATE_FROZEN,
            "preregistration": ("PREREGISTRATION.md freeze 2640fa86 + "
                                "Amendment A1 8079b0a6 (pre-implementation)"),
            "composed_against": "CARD_STARTER.md v2",
            "done_when_verbatim": DONE_WHEN_VERBATIM,
            "card_observation_verbatim": CARD_OBSERVATION_VERBATIM,
            "card_falsifier_verbatim": CARD_FALSIFIER_VERBATIM,
        },
        "input_pins": {role: {"kind": kind, "path": path, "sha256": sha}
                       for role, (kind, path, sha) in PINS.items()},
        "frame_chain": build_frame_chain(P),
        "skeletal_graph": build_skeletal_graph(P),
        "tissue_graph": build_tissue_graph(P),
        "interface_graph": interface,
        "engineering_carriers": build_engineering_carriers(P),
        "explicit_reductions": build_reductions(P),
        "removal_closure": compute_removal_closure(interface),
        "explicit_gaps": build_explicit_gaps(P),
        "calculation_contracts": build_contracts(P),
        "consumer_contract": build_consumer_contract(),
    }
    counts = dict(FROZEN)
    counts["a07_waypoint_resolutions"] = len(doc["interface_graph"]["waypoint_resolutions_carried"])
    doc["counts"] = counts
    # P6/P7 on the full package BEFORE any tamper can run
    check_no_dangling(doc)
    validate_document(doc, P)
    return doc


def canonical_bytes(doc):
    return (json.dumps(doc, indent=1, ensure_ascii=True,
                       sort_keys=False) + "\n").encode("utf-8")


def document_sha(doc):
    return hashlib.sha256(canonical_bytes(doc)).hexdigest()


# ---------- falsifier arms ----------
def run_falsifier_arms():
    P = load_pins()
    arms = {}

    def arm(n, name, tamper_fn, expected_code):
        # clean control FIRST
        clean_doc = build_document()
        clean_ok = True
        guard = f"a09_fb{n}_premature"
        try:
            validate_document(clean_doc, load_pins())
            clean_detail = "clean control validated"
        except Refusal as err:
            clean_ok = False
            clean_detail = f"CLEAN CONTROL REFUSED: {err}"
        require(clean_ok, guard, clean_detail)
        # tampered fixture
        tampered = build_document()
        tamper_fn(tampered)
        bit = False
        detail = ""
        try:
            validate_document(tampered, load_pins())
            detail = "NOT REFUSED (arm did not bit)"
        except Refusal as err:
            detail = str(err)
            bit = detail.startswith(expected_code)
        row = {
            "arm": name, "expected_refusal": expected_code,
            "bit": bit, "observed": detail[:300],
            "clean_control": {
                "metric_scope": "full-document validate_document on untampered bytes",
                "value": clean_detail, "within_tolerance": clean_ok,
                "guard": guard}}
        require(bit, f"a09_fb{n}_no_bit", f"{name}: {detail}")
        arms[f"FB{n}_{name}"] = row

    def t1(doc):
        for c in doc["interface_graph"]["connections"]:
            if c["kind"] == "tendon_path_record" and c["owner_body"] == "osim.body.radius":
                c["owner_body"] = "osim.body.hand"
                return
        raise AssertionError("t1 fixture not found")
    arm(1, "wrong_owner_refused", t1, "wrong_owner")

    def t2(doc):
        doc["interface_graph"]["grasp_endpoints"][0]["frame_decl"] = OSIM_HAND_FRAME
    arm(2, "frame_mismatch_refused", t2, "frame_mismatch_refused")

    def t3(doc):
        for c in doc["interface_graph"]["connections"]:
            if c["terminal_resolution"].get("placement_failed_outside"):
                c["terminal_resolution"]["envelope_measurement"]["outside_axes"] = []
                c["terminal_resolution"]["placement_failed_outside"] = False
                return
        raise AssertionError("t3 fixture not found")
    arm(3, "hidden_outside_refused", t3, "hidden_outside_refused")

    def t4(doc):
        red = reduced_package(doc, "abd_poll_longus")
        keep = [c for c in doc["interface_graph"]["connections"]
                if c["muscle_node"] == "muscle.abd_poll_longus"][0]
        red["interface_graph"]["connections"].append(copy.deepcopy(keep))
        doc.clear()
        doc.update(red)
    arm(4, "dangling_connection_after_removal_refused", t4,
        "dangling_connection_after_removal")

    def t5(doc):
        doc["tissue_graph"]["nodes"][0].pop("provenance_class")
    arm(5, "silent_default_refused", t5, "silent_default_refused")

    def t6(doc):
        doc["interface_graph"]["connections"][0]["fitted_origin_m"] = [0.0, 0.0, 0.0]
    arm(6, "fitting_unauthorized_refused", t6, "fitting_unauthorized_refused")

    # FB7 pin drift: tampered COPY tree (nothing on disk mutated)
    clean_ok_guard = "a09_fb7_premature"
    clean_doc = build_document()
    try:
        validate_document(clean_doc, load_pins())
        clean_ok = True
        clean_detail = "clean control validated"
    except Refusal as err:
        clean_ok = False
        clean_detail = f"CLEAN CONTROL REFUSED: {err}"
    require(clean_ok, clean_ok_guard, clean_detail)
    import tempfile
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        (tmp_root / "tools/monkey_campaign/contributions").mkdir(parents=True)
        rel = "tools/monkey_campaign/contributions/MAT2-A06/attachment_ownership.json"
        src = pathlib.Path(pin_root("repo")) / rel
        dst = tmp_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        raw = dst.read_bytes()
        require(b'"revision":1' in raw, "fb7_fixture_form",
                "revision key not in pinned byte form")
        dst.write_bytes(raw.replace(b'"revision":1', b'"revision":2', 1))
        drift = ""
        bit7 = False
        try:
            load_pins(override_dir=tmp_root)
            drift = "NOT REFUSED (arm did not bit)"
        except Refusal as err:
            drift = str(err)
            bit7 = drift.startswith("input_pin_drift")
        require(bit7, "a09_fb7_no_bit", f"input_pin_drift: {drift}")
        arms["FB7_input_pin_drift"] = {
            "arm": "input_pin_drift", "expected_refusal": "input_pin_drift",
            "bit": bit7, "observed": drift[:300],
            "clean_control": {
                "metric_scope": "pin load on untampered tree (tampered COPY only)",
                "value": clean_detail, "within_tolerance": clean_ok,
                "guard": clean_ok_guard}}

    receipt = {
        "schema": "chimera.a09_falsifiers.v1",
        "task_id": TASK_ID,
        "F_all_green": all(a["bit"] for a in arms.values()),
        "arms": arms,
        "law": ("every arm: passing clean control FIRST, named premature guard, "
                "receipt row with clean_control; each bits on its tampered "
                "fixture only"),
    }
    return receipt


# ---------- main ----------
def main(argv):
    if "--falsify" in argv:
        receipt = run_falsifier_arms()
        out = HERE / "evidence" / "falsifier_receipt.json"
        out.parent.mkdir(exist_ok=True)
        out.write_bytes((json.dumps(receipt, indent=1) + "\n").encode("utf-8"))
        print("falsifier receipt:", out)
        for name, row in receipt["arms"].items():
            print(f"  {name}: bit={row['bit']}")
        print("F_all_green:", receipt["F_all_green"])
        return 0
    doc = build_document()
    if "--verify" in argv:
        ondisk = json.loads(DOC_PATH.read_text(encoding="utf-8"))
        P = load_pins()
        P["_interface"] = build_interface_graph(P)
        validate_document(ondisk, P)
        print("verify OK:", DOC_PATH)
        print("document sha256:", document_sha(ondisk))
        return 0
    if "--self-check" in argv:
        print("self-check OK; document sha256:", document_sha(doc))
        return 0
    DOC_PATH.write_bytes(canonical_bytes(doc))
    print("emit OK:", DOC_PATH)
    print("document sha256:", document_sha(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
