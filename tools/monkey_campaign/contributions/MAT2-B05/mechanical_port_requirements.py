"""MAT2-B05 — real mechanical port requirements (derivation + implementation).

Task card B05 / MAT2-B05, criteria sha256
6b8fda77de9184ced004bcb6b14b83c0e46139981609a4a9f72975a738ebc8da:

  "Actual port patch/stiffness/couple/weight/frame inputs qualify or remain
   blocked. Material-first addition: Use material-law/interface definitions
   with declared stiffness, pressure limits and attachment area at chosen
   detail; distinguish engineering assumptions from measured anatomy."

Calculation contract C17 "Finite attachment mechanics" (required inputs: patch
area/shape, areal stiffness, couple resistance, weights, frame; method: derive
attachment stiffness and rotational resistance using the approved finite-area
formulation; output: actual anatomical port qualification; verification:
analytic/independent checks and real-parameter bounds; synthetic lambda_min
does not transfer).

THE EIGHT PORTS are the ENDPOINT sites of the foreign-forearm tendons on
radius/radius_l, pinned by the sha256-pinned attachment_candidates document
(rev 5): radius {BIClong-P11, BICshort-P8, BRD-P3, PT-P5} and radius_l
{BIClong_l-P11, BICshort_l-P8, BRD_l-P3, PT_l-P5}.  Every non-endpoint site is
a tendon WAYPOINT and is refused as a port (never reinterpreted).

HONESTY RULES (enforced by named refusals, see Refusal):
  * every copied input is byte-pinned (sha256) — no drifted evidence;
  * a numeric in a measured-anatomy slot MUST carry a provenance pin; declared
    engineering requirements are labeled `synthetic_authored` and NEVER
    qualify a port;
  * mechanical_qualification is true ONLY if every required input row of that
    port has status `qualified`;
  * the C17 admission gate tests the MEASURED weakest eigenvalue of the
    rotational block M = sum_i w_i [a~]_x^T Kbar [a~]_x against an AUTHORED
    requirement `k_couple_min`; a synthetic demo lambda_min is refused as
    qualification evidence;
  * port anchors are MATERIAL POINTS (rest anchor + mean body translation,
    the MAT2-M05 A1 correction / durable lesson 3); a deformed-face-centroid
    anchor convention is refused.

Commands (run from this directory, /c/Python314/python):
    python -B mechanical_port_requirements.py derive
    python -B mechanical_port_requirements.py verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re
import shutil
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent

SCHEMA = "chimera.mechanical_port_requirements.v1"
OBJECT_ID = "mat2-b05-mechanical-port-requirements"
TASK_ID = "MAT2-B05"
CRITERIA_SHA256 = "6b8fda77de9184ced004bcb6b14b83c0e46139981609a4a9f72975a738ebc8da"
PREREGISTRATION = HERE / "PREREGISTRATION.md"

# ---------------------------------------------------------------------------
# Pinned inputs (bytes copied into data/, sha256 recorded; origin recorded)
# ---------------------------------------------------------------------------
INPUT_PINS = [
    {
        "id": "attachment_candidates",
        "file": "data/attachment_candidates_854f7097.json",
        "sha256": "854f70976deb10264f052a8dafc3247c9bf6bf03761748e343329ce30e1032ae",
        "origin": {
            "class": "host_artifact_untracked",
            "source_path": "E:\\PythonChimera\\.tmp\\anatomy_compiler\\runs\\attachment_candidates.json",
            "note": ("attachment candidates rev 5; 'derived from the fitted packet site/tendon "
                     "order + the fit's own recorded transforms and measurements; nothing "
                     "re-measured or re-invented' (revision_safety, verbatim). Upstream "
                     "provenance embedded in the document: source_xml_raw_sha256 "
                     "675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1, "
                     "source_xml_canonical_sha256 7caa32c6e31e319876ea21625b662c5c00e736038f542b38ce6b0cb81aadc8a5, "
                     "fitted_packet_sha256 a447555069748d7fe421ff2a4ddeaa108729924ae088478741c86c38c3880937"),
        },
    },
    {
        "id": "mechanical_requirements_cannot_produce",
        "file": "data/mechanical_requirements_cannot_produce.json",
        "sha256": "639a4a4b7ab6039ad61a23aced8d838f01ee744d44efcb042e01d0303cfe40b6",
        "origin": {
            "class": "git",
            "branch": "origin/forearm-package-20260924",
            "commit": "64ed7cd3f9f5f244d721971c2797d02e0b4a5288",
            "path": "tools/assembly_handoff/inputs/mechanical_requirements.cannot_produce.json",
        },
    },
    {
        "id": "material_volume_input",
        "file": "data/material_volume_input.json",
        "sha256": "6e8033f26c823f410eb5beb8fdaaefd4c0c37db61327a86221e087bc832b9ddc",
        "origin": {
            "class": "git",
            "branch": "origin/review/MAT2-B03",
            "commit": "72822775a6756891e8dda6ee7f06d1a20b5ec38c",
            "path": "tools/monkey_campaign/contributions/MAT2-B03/material_volume_input.json",
            "note": ("byte-identical at origin/review/MAT2-M05 cadaabc6ae0522c2530ce6fa090f07725d19a25f; "
                     "MAT2-B03 counted mass total 0.044702393754434 kg"),
        },
    },
    {
        "id": "frame_forest",
        "file": "data/frame_forest.json",
        "sha256": "156ef55722e1ecda3238f3733131eb707f209cb93531d0e133227b00ebba8203",
        "origin": {
            "class": "git",
            "branch": "origin/review/MAT2-B04",
            "commit": "ba24f78622bbf5e1e0e4338187e7889b7da221f5",
            "path": "tools/monkey_campaign/contributions/MAT2-B04/frame_forest.json",
            "note": ("byte-identical at origin/review/MAT2-M05 cadaabc6ae0522c2530ce6fa090f07725d19a25f; "
                     "chimera.assembly_frame_forest.v1 with authored roots root_pelvis/root_thorax/"
                     "root_ulna/root_ulna_l; no_fusion_statement honored"),
        },
    },
    {
        "id": "arm_rigid_laws",
        "file": "data/arm_rigid_laws.json",
        "sha256": "a9e971db4b36c1a6c35f9c27171ebd06787d5ffc96d58cd4b039e9e4e7f02d32",
        "origin": {
            "class": "git",
            "branch": "origin/review/MAT2-M04",
            "commit": "f53d384b5c548cea7592a8231fdc5b87c6d9cea5",
            "path": "tools/monkey_campaign/contributions/MAT2-M04/arm_rigid_laws.json",
            "note": ("byte-identical at origin/review/MAT2-M05 cadaabc6ae0522c2530ce6fa090f07725d19a25f; "
                     "all seven arm regions rigid, source_status synthetic_authored"),
        },
    },
    {
        "id": "interface_state",
        "file": "data/interface_state.json",
        "sha256": "c09bdf0564d152fa8b9a41489bd874fd0570f75e40ed3ce848f4c474fd0320c6",
        "origin": {
            "class": "git",
            "branch": "origin/review/MAT2-M05",
            "commit": "cadaabc6ae0522c2530ce6fa090f07725d19a25f",
            "path": "tools/monkey_campaign/contributions/MAT2-M05/interface_state.json",
        },
    },
    {
        "id": "interface_exchange_source",
        "file": "data/interface_exchange_m05.py",
        "sha256": "295e6c898ada14918f09b2b0633f5926c1623c9e09cd37258e516ab57450b9b9",
        "origin": {
            "class": "git",
            "branch": "origin/review/MAT2-M05",
            "commit": "cadaabc6ae0522c2530ce6fa090f07725d19a25f",
            "path": "tools/monkey_campaign/contributions/MAT2-M05/interface_exchange.py",
            "note": "declared interface constants are parsed from these pinned bytes, never hand-copied",
        },
    },
    {
        "id": "pressure_state",
        "file": "data/pressure_state.json",
        "sha256": "8182da4720f26154dfff3c54711e66cb318cc7bb9c989de77b7ee0a2f2b2ec03",
        "origin": {
            "class": "git",
            "branch": "origin/review/MAT2-M03",
            "commit": "70aff3ed0566c2c38d2a31e3f4d40ef18950af7a",
            "path": "tools/monkey_campaign/contributions/MAT2-M03/pressure_state.json",
        },
    },
]

C17_AUTHORITY = {
    "formulation_document": {
        "class": "host_artifact_untracked",
        "path": "E:\\PythonChimera\\tools\\finite_area_attachment\\DERIVATION.md",
        "sha256": "b28cbf09fa934755656937892e040bb7bf2231730723605758a0fc4410281dab",
    },
    "admission_battery": {
        "class": "host_artifact_untracked",
        "path": "E:\\PythonChimera\\tools\\finite_area_attachment\\test_dynamics_and_corrections.py",
        "sha256": "5ebb6d163e3e7208540046a015ce1b066ed53eac45f78b5134e48c5959cc2d42",
    },
    "note": ("C17-approved finite-area formulation: patch points x_i with area-quadrature weights "
             "w_i (sum 1), bone state (c, R), bone-local anchors a_i, energy "
             "Pi = 1/2 sum w_i e_i^T W e_i, Kbar = kappa_areal * A_patch; rotational block about "
             "the anchor centroid M = sum_i w_i [a~_i]_x^T Kbar [a~_i]_x; admission accepts iff "
             "lambda_min(M) >= k_couple_min where k_couple_min is an AUTHORED requirement unless "
             "independently sourced; isotropic scalar k must equal kappa_areal*A_patch within "
             "1e-3 relative (consistent provenance never admits by itself). The synthetic "
             "lambda_min = 32 N*m/rad demo result does NOT transfer (C17 verification clause). "
             "This module re-implements the closed-form block and the gate; it does not import "
             "the untracked reference."),
}

# Anchor conventions (MAT2-M05 A1 correction / durable lesson 3)
ANCHOR_CONVENTIONS = {
    "material_point": {
        "rule": "rest anchor + mean body translation",
        "authority": "MAT2-M05 correction A1 and durable lesson 3: ports are material points; "
                     "anchoring interface geometry to a deforming face centroid wobbles under "
                     "one-sided loads",
    },
    "deformed_face_centroid": {
        "rule": "anchor follows the deformed face centroid",
        "refusal": "deformed_centroid_anchor_refused",
    },
}

# Authored engineering requirements at CHOSEN DETAIL (source_status
# synthetic_authored; they are requirement declarations, never measurements).
CHOSEN_DETAIL = {
    "patch_shape": "disc",
    "patch_radius_m": 2.5e-3,
    "patch_plane_normal_source_local": [1.0, 0.0, 0.0],
    "patch_anchor_angles_rad": [0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0],
    "quadrature": "uniform_3_rim_anchors",
}

NAMED_MISSING_EVIDENCE = {
    "frame": [
        "an accepted ulna-edge correspondence (architect decision 4: U-STR verdict-ready pending "
        "volr-side roll sign identification; radius-record supersession acceptance still open)",
        "an authorized binding of the fitted packet frames to the authored frame forest "
        "(MAT2-B04 no_fusion_statement: fitted frames bind by stable name only; authoring the "
        "alignment would be a guessed alignment)",
    ],
    "patch_area_m2": [
        "a measured attachment footprint (the pinned source records exactly one POINT per site: "
        "source_pos_local; no footprint/area measurement exists in any pinned source)",
        "an accepted correspondence that would place the footprint on the real target bone "
        "geometry (blocked with the frame input)",
    ],
    "kappa_areal_n_m3": [
        "a measured areal stiffness density for the tendon-to-bone attachment (no measured value "
        "exists in any pinned source; MAT2-M04 assigns the arm regions rigid with source_status "
        "synthetic_authored and invents no soft-tissue stiffness)",
    ],
    "k_couple_min_n_m_per_rad": [
        "a sourced minimum rotational-resistance requirement (none exists in any pinned source; "
        "the value carried below is an AUTHORED requirement, and the C17 clause 'synthetic "
        "lambda_min does not transfer' forbids using any synthetic demo result as qualification "
        "evidence)",
    ],
    "weights_carried_load": [
        "a counted, validated carried-load mass for the hand/forearm (the .osim segment masses "
        "are EXCLUDED transported claims — 17.039978509953905 kg, never counted; the hand shell "
        "carries ZERO volume-owned mass in the pinned B03 document; hand assembly identity and "
        "scale remain unresolved per A04/A05)",
    ],
}


class Refusal(Exception):
    """Named refusal; code is machine-comparable, message carries the context."""

    def __init__(self, code, message=""):
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def canonical_json(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def write_text_canonical(path, text):
    path = pathlib.Path(path)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def check_input_pins(root=HERE, pin_overrides=None):
    overrides = dict(pin_overrides or {})
    for pin in INPUT_PINS:
        path = root / pin["file"]
        if not path.exists():
            raise Refusal("input_pin_missing", pin["id"])
        got = sha256_file(path)
        want = overrides.get(pin["id"], pin["sha256"])
        if got != want:
            raise Refusal("input_pin_mismatch", f"{pin['id']} got {got} want {want}")
    return {pin["id"]: pin["sha256"] for pin in INPUT_PINS}


def parse_m05_constants(root=HERE):
    """Declared interface constants, parsed from the pinned M05 source bytes."""
    text = (root / "data" / "interface_exchange_m05.py").read_text(encoding="utf-8")
    wanted = {
        "K_CONTACT_PA_PER_M": "k_contact_pa_per_m",
        "K_TENSION_N_PER_M": "k_tension_n_per_m",
        "K_SHEAR_N_PER_M": "k_shear_n_per_m",
        "K_TWIST_N_M_PER_RAD": "k_twist_n_m_per_rad",
    }
    out = {}
    for symbol, name in wanted.items():
        m = re.search(rf"^{symbol}\s*=\s*([0-9.eE+-]+)\s", text, flags=re.M)
        if not m:
            raise Refusal("m05_constant_not_found", symbol)
        out[name] = float(m.group(1))
    return out


def resolve_anchor_convention(name):
    conv = ANCHOR_CONVENTIONS.get(name)
    if conv is None:
        raise Refusal("unknown_anchor_convention", str(name))
    if "refusal" in conv:
        raise Refusal(conv["refusal"], name)
    return conv


# ---------------------------------------------------------------------------
# C17 finite-area machinery (closed form + independent eigen solver)
# ---------------------------------------------------------------------------
def skew(a):
    x, y, z = float(a[0]), float(a[1]), float(a[2])
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])


def rotational_block(anchors, weights, kbar):
    """M = sum_i w_i [a~_i]_x^T Kbar [a~_i]_x about the weighted centroid."""
    a = np.asarray(anchors, dtype=float)
    w = np.asarray(weights, dtype=float)
    if a.shape[0] != w.shape[0] or a.shape[1] != 3:
        raise Refusal("c17_input_shape_invalid", f"anchors {a.shape} weights {w.shape}")
    if abs(float(w.sum()) - 1.0) > 1e-12:
        raise Refusal("quadrature_weights_not_normalized", repr(float(w.sum())))
    if np.any(w <= 0.0):
        raise Refusal("quadrature_weight_not_positive", "")
    centroid = w @ a
    at = a - centroid
    M = np.zeros((3, 3))
    for i in range(a.shape[0]):
        S = skew(at[i])
        M += float(w[i]) * (S.T @ np.asarray(kbar, dtype=float) @ S)
    return M, centroid


def eig_sym3_analytic(M):
    """Independent closed-form eigenvalues of a symmetric 3x3 matrix
    (trigonometric solution of the cubic characteristic polynomial) — does not
    call numpy's eigensolver."""
    M = np.asarray(M, dtype=float)
    p1 = M[0, 1] ** 2 + M[0, 2] ** 2 + M[1, 2] ** 2
    q = np.trace(M) / 3.0
    p2 = (M[0, 0] - q) ** 2 + (M[1, 1] - q) ** 2 + (M[2, 2] - q) ** 2 + 2.0 * p1
    p = math.sqrt(p2 / 6.0)
    B = (M - q * np.eye(3)) / p
    r = np.linalg.det(B) / 2.0
    r = max(-1.0, min(1.0, r))
    phi = math.acos(r) / 3.0
    eig1 = q + 2.0 * p * math.cos(phi)
    eig3 = q + 2.0 * p * math.cos(phi + 2.0 * math.pi / 3.0)
    eig2 = 3.0 * q - eig1 - eig3
    return sorted([eig1, eig2, eig3])


def admission(anchors, weights, k, k_couple_min, kappa_areal=None, patch_area=None):
    """C17 admission gate.  k is the (isotropic) scalar bond stiffness [N/m];
    k_couple_min is an AUTHORED requirement [N*m/rad].  With kappa_areal AND
    patch_area supplied, provenance consistency k = kappa_areal*patch_area is
    enforced within 1e-3 relative (named refusal otherwise).  Returns the
    ascending eigenvalues and the verdict; NEVER mutates its inputs."""
    if not (math.isfinite(k) and k > 0.0):
        raise Refusal("k_not_finite_positive", repr(k))
    if not (math.isfinite(k_couple_min) and k_couple_min > 0.0):
        raise Refusal("k_couple_min_not_finite_positive", repr(k_couple_min))
    if (kappa_areal is None) != (patch_area is None):
        raise Refusal("kappa_area_provenance_partial", "")
    if kappa_areal is not None:
        if not (math.isfinite(kappa_areal) and kappa_areal > 0.0
                and math.isfinite(patch_area) and patch_area > 0.0):
            raise Refusal("kappa_area_provenance_not_finite_positive", "")
        if abs(k - kappa_areal * patch_area) > 1e-3 * abs(k):
            raise Refusal("k_provenance_inconsistent",
                          f"k={k!r} != kappa_areal*patch_area={kappa_areal * patch_area!r}")
    kbar = np.eye(3) * k
    M, centroid = rotational_block(anchors, weights, kbar)
    lam_np = sorted(float(v) for v in np.linalg.eigvalsh(M))
    lam_an = eig_sym3_analytic(M)
    scale = max(abs(v) for v in lam_np) or 1.0
    rel = max(abs(a - b) for a, b in zip(lam_np, lam_an)) / scale
    return {
        "centroid": [float(v) for v in centroid],
        "eigenvalues_measured_n_m_per_rad": lam_np,
        "eigenvalues_analytic_n_m_per_rad": lam_an,
        "eigen_solver_rel_err": rel,
        "lambda_min_n_m_per_rad": lam_np[0],
        "k_couple_min_required_n_m_per_rad": float(k_couple_min),
        "admitted": bool(lam_np[0] >= k_couple_min),
        "kappa_areal_n_m3": kappa_areal,
        "patch_area_m2": patch_area,
        "k_n_per_m": float(k),
    }


def qualification_evidence(lambda_min, source_status):
    """A lambda_min may only be cited as QUALIFICATION evidence when its source
    status is measured/researched.  C17: synthetic lambda_min does not
    transfer."""
    if source_status in ("measured", "researched"):
        return {"lambda_min_n_m_per_rad": float(lambda_min), "source_status": source_status,
                "accepted_as_qualification_evidence": True}
    raise Refusal("synthetic_lambda_min_does_not_transfer",
                  f"source_status={source_status!r}")


# ---------------------------------------------------------------------------
# pinned evidence readers
# ---------------------------------------------------------------------------
PORT_BODY_ORDER = ("radius", "radius_l")


def _membership_endpoint(site):
    """Classification AUTHORITY is the tendon_membership path role (the ordered
    path record); the endpoint_roles display field is cross-checked against
    it, never trusted alone."""
    roles = {m.get("role") for m in (site.get("tendon_membership") or [])}
    if not roles:
        return False
    if roles == {"waypoint"}:
        return False
    if roles <= {"first_endpoint", "last_endpoint"}:
        return True
    raise Refusal("mixed_role_site", f"{site.get('site_id')!r} membership roles {sorted(roles)!r}")


def extract_sites(root=HERE):
    cand = load_json(root / "data" / "attachment_candidates_854f7097.json")
    if cand.get("kind") != "attachment_candidates" or int(cand.get("revision", -1)) != 5:
        raise Refusal("attachment_candidates_revision_unexpected",
                      f"kind={cand.get('kind')!r} revision={cand.get('revision')!r}")
    ports, waypoints = [], []
    for body in PORT_BODY_ORDER:
        b = cand["bodies"][body]
        for site in b["candidates"]:
            display_roles = list(site.get("endpoint_roles") or [])
            is_endpoint = _membership_endpoint(site)
            if bool(display_roles) != is_endpoint:
                raise Refusal("endpoint_role_inconsistent",
                              f"{site['site_id']} display {display_roles!r} vs membership "
                              f"{sorted({m.get('role') for m in site['tendon_membership']})!r} "
                              "(port_vs_waypoint_rule: only first/last path entries are endpoints)")
            roles = display_roles
            rec = {
                "site_id": site["site_id"],
                "source_body": site["source_body"],
                "source_pos_local": list(site["source_pos_local"]),
                "source_pos_local_units": site["source_pos_local_units"],
                "endpoint_roles": roles,
                "tendon_membership": site.get("tendon_membership", []),
                "source_mechanical_qualification": site.get("mechanical_qualification"),
                "source_mechanical_qualification_note": site.get("mechanical_qualification_note"),
                "fitted_reference": {
                    "resolved": site["fitted"]["resolved"],
                    "fitted_pos_local": list(site["fitted"]["fitted_pos_local"]),
                    "fitted_pos_global": list(site["fitted"]["fitted_pos_global"]),
                    "transform_application": site["transform_application"],
                },
            }
            (ports if roles else waypoints).append(rec)
    expected_ports = {
        "radius": {"BIClong-P11", "BICshort-P8", "BRD-P3", "PT-P5"},
        "radius_l": {"BIClong_l-P11", "BICshort_l-P8", "BRD_l-P3", "PT_l-P5"},
    }
    got = {}
    for p in ports:
        got.setdefault(p["source_body"], set()).add(p["site_id"])
    if got != expected_ports:
        raise Refusal("port_set_mismatch", f"got {got!r}")
    if len(ports) != 8 or len(waypoints) != 24:
        raise Refusal("site_count_mismatch", f"ports={len(ports)} waypoints={len(waypoints)}")
    return cand, ports, waypoints


def resolve_port(site_id, root=HERE):
    """Resolve a site as a PORT.  Waypoints are refused (never reinterpreted
    as attachment ports)."""
    cand, ports, waypoints = extract_sites(root)
    for p in ports:
        if p["site_id"] == site_id:
            return p
    for wpt in waypoints:
        if wpt["site_id"] == site_id:
            raise Refusal("waypoint_not_a_port",
                          f"{site_id} roles={wpt['endpoint_roles']!r} (port_vs_waypoint_rule: "
                          "intermediate entries are waypoints and never endpoints)")
    raise Refusal("site_not_found", site_id)


def cross_check_cannot_produce(ports, root=HERE):
    cp = load_json(root / "data" / "mechanical_requirements_cannot_produce.json")
    listed = {row["port_id"]: row for row in cp["ports_missing_parameters"]}
    mine = {p["site_id"]: p for p in ports}
    if set(listed) != set(mine) or cp["evidence"]["ports_identified"] != 8:
        raise Refusal("cannot_produce_list_mismatch", f"{sorted(listed)} vs {sorted(mine)}")
    for pid, row in listed.items():
        if row["source_body"] != mine[pid]["source_body"]:
            raise Refusal("cannot_produce_body_mismatch", pid)
        if row.get("mechanical_qualification") is not False:
            raise Refusal("cannot_produce_qualification_drift", pid)
    expected_missing = {"patch_area_m2", "kappa_areal_n_m3", "k_couple_min_n_m_per_rad",
                        "weights", "anchor_frame_id (bound authored root frame)",
                        "endpoints[*].local_frame_id (bound authored frame)"}
    for pid, row in listed.items():
        if set(row["missing_parameters"]) != expected_missing:
            raise Refusal("cannot_produce_missing_params_drift", pid)
    return cp


def read_b03_masses(root=HERE):
    mvi = load_json(root / "data" / "material_volume_input.json")
    if mvi.get("schema") != "chimera.material_state.v1":
        raise Refusal("material_volume_schema_unexpected", mvi.get("schema", ""))
    out = {}
    for m in mvi["matter"]:
        out[m["id"]] = {"mass_kg": m["mass_kg"], "provenance": m["provenance"]}
    return out


def read_b04_roots(root=HERE):
    ff = load_json(root / "data" / "frame_forest.json")
    if ff.get("schema") != "chimera.assembly_frame_forest.v1":
        raise Refusal("frame_forest_schema_unexpected", ff.get("schema", ""))
    roots = {}
    for fid in ("root_ulna", "root_ulna_l"):
        f = ff["frames"][fid]
        roots[fid] = {
            "body": f["body"],
            "origin_m": list(f["origin_m"]),
            "basis_rows": [list(row) for row in f["basis_rows"]],
            "parent_frame_id": f["parent_frame_id"],
            "scale_to_m": f["scale_to_m"],
            "coordinate_unit": f["coordinate_unit"],
            "handedness": f["handedness"],
            "evidence": f["evidence"],
            "chain_lines": [hop["line"] for hop in f["chain"]],
        }
    return roots, ff.get("no_fusion_statement", "")


def read_m04_region_laws(root=HERE):
    laws = load_json(root / "data" / "arm_rigid_laws.json")
    if laws.get("schema") != "chimera.passive_law.v1":
        raise Refusal("passive_law_schema_unexpected", laws.get("schema", ""))
    assign = {a["region_id"]: a for a in laws["assignments"]}
    for region in ("radius", "ulna", "humerus", "hand"):
        if region not in assign:
            raise Refusal("m04_region_assignment_missing", region)
    profile = {p["id"]: p for p in laws["profiles"]}["rigid"]
    return {"profile_id": "rigid", "profile_source_status": profile["source_status"],
            "constitutive_equation": profile["constitutive_equation"],
            "assignments": {k: {"profile_id": v["profile_id"], "provenance": v["provenance"]}
                            for k, v in assign.items()}}


def read_m03_pressure_limits(root=HERE):
    ps = load_json(root / "data" / "pressure_state.json")
    law = next(l for l in ps["laws"] if l["kind"] == "pressure_deformation")
    prm = law["parameters"]
    return {
        "source_id": prm["source_id"],
        "max_delta_p_pa": prm["max_delta_p_pa"],
        "max_dv_dt_m3_per_s": prm["max_dv_dt_m3_per_s"],
        "p_ext_pa": prm["p_ext_pa"],
        "p_int_peak_pa": prm["p_int_peak_pa"],
        "traction_rule": prm["traction_rule"],
        "provenance": law["provenance"],
        "source_status": "synthetic_authored",
    }


def max_delta_p_refusal(limit, delta_p):
    if abs(delta_p) > limit:
        raise Refusal("pressure_source_delta_p_limit_exceeded",
                      f"|{delta_p}| > {limit}")


# ---------------------------------------------------------------------------
# document assembly
# ---------------------------------------------------------------------------
def patch_anchors_local(radius_m, normal, angles):
    """Three rim anchors of the declared disc, in source-local coordinates,
    centered at the origin of the patch frame (caller adds the port center).
    Material-point convention: these are REST anchors."""
    n = np.asarray(normal, dtype=float)
    n = n / np.linalg.norm(n)
    helper = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(n, helper))) > 0.9:
        helper = np.array([0.0, 1.0, 0.0])
    u = np.cross(n, helper)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    pts = []
    for ang in angles:
        d = math.cos(ang) * u + math.sin(ang) * v
        pts.append([float(radius_m * d[0]), float(radius_m * d[1]), float(radius_m * d[2])])
    return pts


def disc_matrix_identity_check(anchors_abs, center, normal, k, radius_m):
    """Independent ALGEBRAIC check used instead of a second generic eigensolver:
    for three uniform rim anchors of a radius-r disc with isotropic K = k I, the
    rotational block must equal (k r^2 / 2)(I + n n^T) (Frobenius), whose
    spectrum is {k r^2/2, k r^2/2, k r^2}.  Returns the relative Frobenius
    error of that identity."""
    n = np.asarray(normal, dtype=float)
    n = n / np.linalg.norm(n)
    a = np.asarray(anchors_abs, dtype=float) - np.asarray(center, dtype=float)
    w = np.full(a.shape[0], 1.0 / a.shape[0])
    M, _ = rotational_block(a, w, np.eye(3) * k)
    expected = (k * radius_m ** 2 / 2.0) * (np.eye(3) + np.outer(n, n))
    denom = np.linalg.norm(expected, "fro")
    rel = float(np.linalg.norm(M - expected, "fro") / denom)
    return rel


def input_rows_for_port(port, b03_masses, b04_roots, no_fusion, m05, m03, m04):
    center = port["source_pos_local"]
    r_p = CHOSEN_DETAIL["patch_radius_m"]
    area = math.pi * r_p * r_p
    kappa = m05["k_contact_pa_per_m"]           # Pa/m == N/m^3 (areal stiffness density)
    k = kappa * area
    k_couple_min = m05["k_twist_n_m_per_rad"]   # authored requirement, carried from declared law
    normal = CHOSEN_DETAIL["patch_plane_normal_source_local"]
    anchors = [[c + d for c, d in zip(center, a)]
               for a in patch_anchors_local(r_p, normal, CHOSEN_DETAIL["patch_anchor_angles_rad"])]
    weights = [1.0 / 3.0] * 3
    gate = admission(anchors, weights, k, k_couple_min,
                     kappa_areal=kappa, patch_area=area)
    lam = gate["lambda_min_n_m_per_rad"]
    identity_rel = disc_matrix_identity_check(anchors, center, normal, k, r_p)
    r_needed = (2.0 * k_couple_min / (kappa * area * 1.0)) ** 0.5  # lambda_min = k r^2 / 2

    missing_frame = NAMED_MISSING_EVIDENCE["frame"]
    qualified_roots = {
        fid: {
            "status_row": "qualified_reference_only",
            "authority": "MAT2-B04 authored frame forest (placement only; pinned chains)",
            **val,
        } for fid, val in b04_roots.items()
    }
    return {
        "anchor_frame_id": {
            "status": "blocked",
            "requirement": "bound authored root frame",
            "missing_evidence": missing_frame,
            "qualified_references_available": qualified_roots,
            "no_fusion_statement": no_fusion,
        },
        "endpoints_local_frame_id": {
            "status": "blocked",
            "requirement": "bound authored frame for every endpoint",
            "missing_evidence": missing_frame,
            "provisional_fitted_reference": {
                "record": "fitted_pos_global = fitted_origin + R @ source_pos_local (pinned "
                          "attachment_candidates fitted record)",
                "fitted_reference": port["fitted_reference"],
                "status_note": "provisional U-STR fitted record; never merged; does not bind",
            },
        },
        "patch_area_m2": {
            "status": "blocked_as_measured",
            "missing_evidence": NAMED_MISSING_EVIDENCE["patch_area_m2"],
            "authored_requirement": {
                "shape": CHOSEN_DETAIL["patch_shape"],
                "center_source_local_m": center,
                "plane_normal_source_local": normal,
                "radius_m": r_p,
                "area_m2": area,
                "anchor_angles_rad": CHOSEN_DETAIL["patch_anchor_angles_rad"],
                "source_status": "synthetic_authored",
                "note": "attachment area at CHOSEN DETAIL (engineering assumption), not a "
                        "measured footprint",
            },
        },
        "kappa_areal_n_m3": {
            "status": "blocked_as_measured",
            "missing_evidence": NAMED_MISSING_EVIDENCE["kappa_areal_n_m3"],
            "authored_requirement": {
                "value_n_m3": kappa,
                "carried_from": {
                    "input_pin": "interface_exchange_source",
                    "symbol": "K_CONTACT_PA_PER_M",
                    "declared_value_pa_per_m": m05["k_contact_pa_per_m"],
                    "dimensional_note": "Pa/m == N/m^3 (areal stiffness density)",
                },
                "source_status": "synthetic_authored",
            },
        },
        "k_couple_min_n_m_per_rad": {
            "status": "blocked_as_measured",
            "missing_evidence": NAMED_MISSING_EVIDENCE["k_couple_min_n_m_per_rad"],
            "authored_requirement": {
                "value_n_m_per_rad": k_couple_min,
                "carried_from": {
                    "input_pin": "interface_exchange_source",
                    "symbol": "K_TWIST_N_M_PER_RAD",
                    "declared_value_n_m_per_rad": m05["k_twist_n_m_per_rad"],
                },
                "source_status": "synthetic_authored",
            },
        },
        "weights": {
            "status": "split",
            "qualified": {
                "input_pin": "material_volume_input",
                "counted_bone_mass_radius_kg": b03_masses["bone_radius"]["mass_kg"],
                "counted_bone_mass_radius_provenance": b03_masses["bone_radius"]["provenance"],
                "counted_arm_total_kg": sum(
                    m["mass_kg"] for mid, m in b03_masses.items() if mid.startswith("bone_")),
                "note": "real counted masses of the target arm's bone regions (B03, C02 ledger)",
            },
            "blocked": {
                "carried_load_segment_weights": {
                    "status": "blocked",
                    "missing_evidence": NAMED_MISSING_EVIDENCE["weights_carried_load"],
                },
            },
            "quadrature_w_i": weights,
            "quadrature_source_status": "synthetic_authored",
        },
        "pressure_limits": {
            "status": "declared",
            "carried_from": {"input_pin": "pressure_state", "law_id": m03["source_id"]},
            "limits": {k: m03[k] for k in
                       ("max_delta_p_pa", "max_dv_dt_m3_per_s", "p_ext_pa", "p_int_peak_pa",
                        "traction_rule")},
            "source_status": m03["source_status"],
            "provenance": m03["provenance"],
        },
        "stiffness_law_reference": {
            "input_pin": "arm_rigid_laws",
            "profile_id": m04["profile_id"],
            "radius_assignment": m04["assignments"]["radius"],
            "note": "arm regions are RIGID (declared, synthetic_authored); no soft-tissue "
                    "stiffness is invented, so the attachment areal stiffness stays an authored "
                    "engineering requirement",
        },
        "c17_requirement_check": {
            "anchors_source_local_m": anchors,
            "quadrature_w_i": weights,
            "k_n_per_m": gate["k_n_per_m"],
            "kappa_areal_n_m3": gate["kappa_areal_n_m3"],
            "patch_area_m2": gate["patch_area_m2"],
            "eigenvalues_measured_n_m_per_rad": gate["eigenvalues_measured_n_m_per_rad"],
            "eigenvalues_analytic_n_m_per_rad": gate["eigenvalues_analytic_n_m_per_rad"],
            "eigen_solver_rel_err": gate["eigen_solver_rel_err"],
            "matrix_identity_rel_err": identity_rel,
            "independent_check": "algebraic identity M == (k r^2/2)(I + n n^T); the generic "
                                 "trigonometric cubic eigensolver is a diagnostic only (its "
                                 "accuracy is clustering-limited when two eigenvalues coincide)",
            "lambda_min_closed_form_n_m_per_rad": k * r_p * r_p / 2.0,
            "lambda_min_n_m_per_rad": lam,
            "k_couple_min_required_n_m_per_rad": k_couple_min,
            "admitted": gate["admitted"],
            "sizing_radius_to_meet_requirement_m": r_needed,
            "verdict_note": ("requirement check on DECLARED inputs at chosen detail; NOT an "
                             "anatomical qualification; C17: synthetic lambda_min does not "
                             "transfer"),
        },
    }


def derive(root=HERE, pin_overrides=None):
    pins = check_input_pins(root, pin_overrides)
    prereg_sha = sha256_file(PREREGISTRATION) if PREREGISTRATION.exists() else None
    cand, ports, waypoints = extract_sites(root)
    cp = cross_check_cannot_produce(ports, root)
    b03 = read_b03_masses(root)
    b04_roots, no_fusion = read_b04_roots(root)
    m04 = read_m04_region_laws(root)
    m05 = parse_m05_constants(root)
    m03 = read_m03_pressure_limits(root)
    conv = resolve_anchor_convention("material_point")

    port_docs = []
    for port in ports:
        rows = input_rows_for_port(port, b03, b04_roots, no_fusion, m05, m03, m04)
        required = ["anchor_frame_id", "endpoints_local_frame_id", "patch_area_m2",
                    "kappa_areal_n_m3", "k_couple_min_n_m_per_rad", "weights"]
        all_qualified = all(
            (rows[r]["status"] == "qualified" if r != "weights"
             else rows[r].get("status") == "qualified")
            for r in required
        )
        blocked_reasons = []
        for r in required:
            st = rows[r].get("status")
            if st != "qualified":
                blocked_reasons.append({
                    "input": r, "status": st,
                    "missing_evidence": rows[r].get(
                        "missing_evidence",
                        rows[r].get("blocked", {}).get("carried_load_segment_weights", {}).get(
                            "missing_evidence")),
                })
        port_docs.append({
            "port_id": port["site_id"],
            "source_body": port["source_body"],
            "endpoint_roles": port["endpoint_roles"],
            "tendon_membership": port["tendon_membership"],
            "source_pos_local_m": port["source_pos_local"],
            "source_pos_local_units": port["source_pos_local_units"],
            "source_mechanical_qualification": port["source_mechanical_qualification"],
            "source_mechanical_qualification_note": port["source_mechanical_qualification_note"],
            "anchor_convention": {"kind": "material_point", "rule": conv["rule"],
                                  "authority": conv["authority"]},
            "inputs": rows,
            "inputs_all_qualified": all_qualified,
            "blocked_reasons": blocked_reasons,
            "mechanical_qualification": bool(all_qualified),
        })

    ledger = {
        "qualified": [
            {"input": "weights.counted_arm_bone_masses",
             "evidence": "material_volume_input (B03 C02 counted ledger; bone_radius "
                         f"{b03['bone_radius']['mass_kg']!r} kg; researched density provenance)",
             "pin": pins["material_volume_input"]},
            {"input": "frame.authored_root_frames",
             "evidence": "frame_forest (B04 authored placement only; root_ulna/root_ulna_l exist "
                         "with pinned chimanoid.xml chains)",
             "pin": pins["frame_forest"],
             "boundary": "qualified as authored placement references ONLY; a bound PORT frame "
                         "stays blocked on the accepted correspondence"},
        ],
        "blocked": [
            {"input": "anchor_frame_id", "missing_evidence": NAMED_MISSING_EVIDENCE["frame"]},
            {"input": "endpoints_local_frame_id",
             "missing_evidence": NAMED_MISSING_EVIDENCE["frame"]},
            {"input": "patch_area_m2",
             "missing_evidence": NAMED_MISSING_EVIDENCE["patch_area_m2"]},
            {"input": "kappa_areal_n_m3",
             "missing_evidence": NAMED_MISSING_EVIDENCE["kappa_areal_n_m3"]},
            {"input": "k_couple_min_n_m_per_rad",
             "missing_evidence": NAMED_MISSING_EVIDENCE["k_couple_min_n_m_per_rad"]},
            {"input": "weights.carried_load_segment_weights",
             "missing_evidence": NAMED_MISSING_EVIDENCE["weights_carried_load"]},
        ],
        "authored_engineering_requirements": [
            {"input": "patch_area_m2", "source_status": "synthetic_authored",
             "detail": "disc radius 2.5e-3 m at chosen detail"},
            {"input": "kappa_areal_n_m3", "source_status": "synthetic_authored",
             "detail": "carried from pinned M05 K_CONTACT_PA_PER_M = 1.0e5 Pa/m == N/m^3"},
            {"input": "k_couple_min_n_m_per_rad", "source_status": "synthetic_authored",
             "detail": "carried from pinned M05 K_TWIST_N_M_PER_RAD = 0.8 N*m/rad"},
            {"input": "weights.quadrature_w_i", "source_status": "synthetic_authored",
             "detail": "uniform 3-rim-anchor quadrature (sum 1)"},
            {"input": "pressure_limits", "source_status": "synthetic_authored",
             "detail": "carried from pinned M03 pressure source limits"},
        ],
    }

    doc = {
        "schema": SCHEMA,
        "object_id": OBJECT_ID,
        "revision": 1,
        "task_id": TASK_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "preregistration_sha256": prereg_sha,
        "observation": "Eight ports missing parameters; source tendon points are insufficient",
        "port_source_rule": cand["port_vs_waypoint_rule"],
        "input_pins": INPUT_PINS,
        "c17_authority": C17_AUTHORITY,
        "anchor_convention": {"kind": "material_point",
                              "declared_rule": conv["rule"],
                              "authority": conv["authority"],
                              "refused_alternative": ANCHOR_CONVENTIONS["deformed_face_centroid"]["refusal"]},
        "qualification_rule": ("mechanical_qualification is true ONLY if every required input row "
                              "of the port has status qualified; authored requirements, declared "
                              "laws and demonstrated gate mechanics NEVER qualify a port"),
        "input_status_ledger": ledger,
        "ports": port_docs,
        "waypoints_refused_as_ports": [w["site_id"] for w in waypoints],
        "counts": {
            "ports": len(port_docs),
            "waypoints_refused": len(waypoints),
            "ports_mechanically_qualified": sum(1 for p in port_docs
                                                if p["mechanical_qualification"]),
            "ports_remaining_blocked": sum(1 for p in port_docs
                                           if not p["mechanical_qualification"]),
        },
        "determinism": {"canonical_json": True, "random": "none", "wall_clock": "none"},
        "honest_limits": [
            "the eight anatomical ports remain mechanically UNQUALIFIED; the card's 'qualify or "
            "remain blocked' is executed by naming the missing evidence per input",
            "the C17 requirement check runs on DECLARED inputs at chosen detail (engineering "
            "assumptions labeled synthetic_authored); it demonstrates the approved gate "
            "mechanics and the real-parameter outcome of the declared values, not anatomy",
            "no native-engine runtime run is claimed; runtime-facing qualification belongs to "
            "downstream checkpoints (V11 / B06 / B07)",
        ],
    }
    return doc


def validate_requirements_document(doc):
    """Independent validator over an EMITTED requirements document (works on a
    tampered copy too): qualification may only follow fully-qualified input
    rows, and every qualified measured slot must carry its provenance pin."""
    required = ["anchor_frame_id", "endpoints_local_frame_id", "patch_area_m2",
                "kappa_areal_n_m3", "k_couple_min_n_m_per_rad", "weights"]
    for port in doc["ports"]:
        rows = port["inputs"]
        all_qualified = all(rows[r].get("status") == "qualified" for r in required)
        if port["mechanical_qualification"] and not all_qualified:
            raise Refusal("qualify_requires_all_inputs_qualified",
                          f"{port['port_id']} qualification flipped while required inputs are "
                          f"{[(r, rows[r].get('status')) for r in required]!r}")
        if port["mechanical_qualification"] != all_qualified:
            raise Refusal("qualification_understated", port["port_id"])
        for name in required:
            row = rows[name]
            if row.get("status") == "qualified":
                pinned = row.get("input_pin") or row.get("evidence_pin") or row.get("pin")
                if not pinned:
                    raise Refusal("unknown_provenance_value",
                                  f"{port['port_id']}.{name} claims qualified without a "
                                  "provenance pin")
        auth = rows["patch_area_m2"].get("authored_requirement", {})
        if auth.get("source_status") != "synthetic_authored":
            raise Refusal("authored_requirement_mislabeled",
                          f"{port['port_id']}.patch_area_m2 {auth.get('source_status')!r}")
    return True


def write_outputs(doc, root=HERE):
    validate_requirements_document(doc)
    doc_path = write_text_canonical(root / "mechanical_port_requirements.json",
                                    canonical_json(doc))
    receipt = {
        "schema": "chimera.derivation_receipt.v1",
        "task_id": TASK_ID,
        "object_id": OBJECT_ID,
        "document": "mechanical_port_requirements.json",
        "document_sha256": sha256_file(doc_path),
        "input_pins": {p["id"]: p["sha256"] for p in INPUT_PINS},
        "counts": doc["counts"],
        "determinism": doc["determinism"],
    }
    write_text_canonical(root / "derivation_receipt.json", canonical_json(receipt))
    return doc_path, receipt


def verify(root=HERE):
    """Re-checks on the exact committed artifacts; returns the verification
    receipt dict (also written to work/runs/verification_receipt.json)."""
    checks = []

    def check(name, ok, detail):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    doc_a = derive(root)
    doc_b = derive(root)
    check("P8_determinism", canonical_json(doc_a) == canonical_json(doc_b),
          "two derivations byte-identical")
    pins = check_input_pins(root)
    check("P2_input_pins", len(pins) == len(INPUT_PINS), f"{len(pins)} pins byte-exact")

    counts = doc_a["counts"]
    check("P1_port_inventory", counts["ports"] == 8 and counts["waypoints_refused"] == 24,
          f"ports={counts['ports']} waypoints_refused={counts['waypoints_refused']}")
    check("P4_all_blocked", counts["ports_remaining_blocked"] == 8
          and counts["ports_mechanically_qualified"] == 0,
          "all 8 ports remain blocked with named missing evidence")

    pr = doc_a["ports"][0]
    rad_mass = pr["inputs"]["weights"]["qualified"]["counted_bone_mass_radius_kg"]
    check("P3_b03_mass_pin", rad_mass == 0.00910051480229847,
          f"bone_radius counted mass {rad_mass!r} kg bitwise from pinned B03")
    gate = pr["inputs"]["c17_requirement_check"]
    rel = abs(gate["lambda_min_n_m_per_rad"] - gate["lambda_min_closed_form_n_m_per_rad"]) \
        / gate["lambda_min_closed_form_n_m_per_rad"]
    check("P5_disc_closed_form", rel <= 1e-12,
          f"lambda_min {gate['lambda_min_n_m_per_rad']:.6e} vs closed form "
          f"{gate['lambda_min_closed_form_n_m_per_rad']:.6e} (rel {rel:.3e})")
    check("P5_matrix_identity", all(
        p["inputs"]["c17_requirement_check"]["matrix_identity_rel_err"] <= 1e-12
        for p in doc_a["ports"]),
        f"algebraic identity M == (k r^2/2)(I + n n^T) worst rel "
        f"{max(p['inputs']['c17_requirement_check']['matrix_identity_rel_err'] for p in doc_a['ports']):.3e}")
    check("P5_eigen_solvers_agree", gate["eigen_solver_rel_err"] <= 1e-6,
          f"numpy eigvalsh vs analytic cubic worst rel {gate['eigen_solver_rel_err']:.3e} "
          "(diagnostic; clustering-limited)")
    check("P6_admission_outcome", gate["admitted"] is False
          and gate["lambda_min_n_m_per_rad"] < gate["k_couple_min_required_n_m_per_rad"],
          f"declared patch lambda_min {gate['lambda_min_n_m_per_rad']:.6e} < authored "
          f"requirement {gate['k_couple_min_required_n_m_per_rad']:.1f} -> not admitted "
          "(real-parameter outcome of declared values, recorded honestly)")
    status_ok = all(
        row["inputs"]["anchor_frame_id"]["status"] == "blocked"
        and row["inputs"]["patch_area_m2"]["status"] == "blocked_as_measured"
        and row["inputs"]["kappa_areal_n_m3"]["authored_requirement"]["source_status"]
        == "synthetic_authored"
        for row in doc_a["ports"])
    check("P3_status_ledger", status_ok, "frame blocked; patch blocked as measured; authored "
                                         "requirements labeled synthetic_authored on every port")
    anchor_ok = all(row["anchor_convention"]["kind"] == "material_point"
                    for row in doc_a["ports"])
    check("P7_anchor_convention", anchor_ok,
          "material-point anchors (rest anchor + mean body translation) on every port")
    m03 = read_m03_pressure_limits(root)
    refused = False
    try:
        max_delta_p_refusal(m03["max_delta_p_pa"], m03["max_delta_p_pa"] * 1.0000001)
    except Refusal as r:
        refused = r.code == "pressure_source_delta_p_limit_exceeded"
    check("P10_pressure_limit_refusal", refused,
          f"M03 delta-p limit {m03['max_delta_p_pa']} Pa enforced by named refusal")

    ledger = doc_a["input_status_ledger"]
    check("P9_ledger_explicit",
          len(ledger["blocked"]) == 6 and len(ledger["qualified"]) == 2
          and len(ledger["authored_engineering_requirements"]) == 5,
          f"blocked={len(ledger['blocked'])} qualified={len(ledger['qualified'])} "
          f"authored={len(ledger['authored_engineering_requirements'])}")
    validate_requirements_document(doc_a)
    check("P4b_document_validator", True,
          "emitted document passes validate_requirements_document (qualification rule + "
          "provenance pins)")

    runs = root / "work" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "chimera.verification_receipt.v1",
        "task_id": TASK_ID,
        "checks": checks,
        "passed": sum(1 for c in checks if c["ok"]),
        "failed": sum(1 for c in checks if not c["ok"]),
        "determinism_note": "derive() twice; canonical bytes compared",
    }
    write_text_canonical(runs / "verification_receipt.json", canonical_json(receipt))
    return receipt


# ---------------------------------------------------------------------------
# falsifier harness (tampered COPIES only; real inputs never modified)
# ---------------------------------------------------------------------------
def _tampered_copy(mutate, root=HERE, scratch=None):
    """Copy the contribution data into a scratch tree, mutate it, and return
    the tree for probing.  The caller owns cleanup.  Never touches root."""
    import shutil
    scratch = pathlib.Path(scratch) if scratch is not None else root / "work" / "falsifiers"
    scratch.mkdir(parents=True, exist_ok=True)
    troot = pathlib.Path(scratch)
    if troot.exists():
        shutil.rmtree(troot)
    troot.mkdir(parents=True)
    shutil.copytree(root / "data", troot / "data")
    mutate(troot)
    return troot


def _pin_overrides_for(troot):
    """Pin overrides that re-pin a TAMPERED tree to its actual bytes — used
    ONLY by semantic-guard falsifiers (F2/F3) so the pin guard (F1) does not
    mask the semantic probe.  The real derive never uses overrides."""
    return {p["id"]: sha256_file(troot / p["file"]) for p in INPUT_PINS}


def falsifier_proofs(root=HERE):
    """Each falsifier bites on a tampered COPY; the real artifact is re-derived
    afterwards and byte-compared to the committed document."""
    proofs = []

    def record(fid, expected_code, fn):
        try:
            fn()
            proofs.append({"id": fid, "bites": False, "expected_code": expected_code,
                           "detail": "tampered copy probed WITHOUT refusing — falsifier did not bite"})
        except Refusal as r:
            bites = expected_code in (None, r.code)
            proofs.append({"id": fid, "bites": bites, "code": r.code,
                           "expected_code": expected_code, "detail": r.message})

    # F1 — byte tamper of a pinned input: the pin guard itself must bite.
    def f1():
        def mutate(troot):
            p = troot / "data" / "attachment_candidates_854f7097.json"
            b = bytearray(p.read_bytes())
            b[0] = b[0] ^ 0x01
            p.write_bytes(bytes(b))
        troot = _tampered_copy(mutate, root)
        derive(troot)
    record("F1_input_pin_tamper", "input_pin_mismatch", f1)

    # F2 — promote an intermediate WAYPOINT to an endpoint port.  The pin guard
    # is deliberately re-pinned to the tampered bytes so the SEMANTIC guard is
    # what bites (the display endpoint_roles field must agree with the
    # authoritative tendon path roles; resolve_port refuses waypoints).
    def f2():
        def mutate(troot):
            p = troot / "data" / "attachment_candidates_854f7097.json"
            d = json.loads(p.read_text(encoding="utf-8"))
            for site in d["bodies"]["radius"]["candidates"]:
                if site["site_id"] == "BIClong-P9":
                    site["endpoint_roles"] = ["first_endpoint"]
            p.write_text(json.dumps(d), encoding="utf-8")
        troot = _tampered_copy(mutate, root)
        try:
            resolve_port("BIClong-P9", root=troot)
            raise AssertionError("resolve_port accepted a promoted waypoint")
        except Refusal as r:
            if r.code != "waypoint_not_a_port":
                raise
        derive(troot, pin_overrides=_pin_overrides_for(troot))
    record("F2_waypoint_promotion", "endpoint_role_inconsistent", f2)

    # F3 — flip a port's mechanical_qualification while required inputs are
    # blocked (F3a); claim a qualified measured value without provenance (F3b).
    def f3a():
        committed = root / "mechanical_port_requirements.json"
        if not committed.exists():
            raise AssertionError("emit the document before running falsifiers")
        doc = load_json(committed)
        doc["ports"][0]["mechanical_qualification"] = True
        validate_requirements_document(doc)
    record("F3a_qualification_promotion", "qualify_requires_all_inputs_qualified", f3a)

    def f3b():
        committed = root / "mechanical_port_requirements.json"
        doc = load_json(committed)
        doc["ports"][0]["inputs"]["patch_area_m2"] = {
            "status": "qualified", "value_m2": 3.14e-5}
        validate_requirements_document(doc)
    record("F3b_unprovenanced_qualified_value", "unknown_provenance_value", f3b)

    # F4 — provenance-free scalar k: k must equal kappa_areal*A_patch.
    def f4():
        admission([[0.0025, 0.0, 0.0], [-0.00125, 0.002165, 0.0], [-0.00125, -0.002165, 0.0]],
                  [1 / 3, 1 / 3, 1 / 3], k=1.9634954084936207, k_couple_min=1e-6,
                  kappa_areal=1.0e5, patch_area=2.0e-5)
    record("F4_k_provenance_break", "k_provenance_inconsistent", f4)

    # F5 — a synthetic demo lambda_min cited as qualification evidence.
    def f5():
        qualification_evidence(32.0, "synthetic_authored")
    record("F5_synthetic_lambda_min_transfer", "synthetic_lambda_min_does_not_transfer", f5)

    # F6 — deformed-face-centroid anchor convention (M05 A1 lesson).
    def f6():
        resolve_anchor_convention("deformed_face_centroid")
    record("F6_deformed_centroid_anchor", "deformed_centroid_anchor_refused", f6)

    real = derive(root)
    committed = root / "mechanical_port_requirements.json"
    real_sha = hashlib.sha256(canonical_json(real).encode("utf-8")).hexdigest()
    disk_sha = sha256_file(committed) if committed.exists() else "(not yet written)"
    proofs.append({
        "id": "real_artifact_untouched",
        "bites": None if disk_sha == "(not yet written)" else (disk_sha == real_sha),
        "detail": f"committed document sha256 {disk_sha}; re-derived canonical sha256 {real_sha}",
    })
    scratch = root / "work" / "falsifiers"
    if scratch.exists():
        shutil.rmtree(scratch)
    return proofs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=["derive", "verify", "falsifiers"])
    args = ap.parse_args(argv)
    if args.command == "derive":
        doc = derive()
        path, receipt = write_outputs(doc)
        print("document:", path)
        print("document sha256:", receipt["document_sha256"])
        print("counts:", json.dumps(receipt["counts"], sort_keys=True))
        return 0
    if args.command == "verify":
        receipt = verify()
        for c in receipt["checks"]:
            print(("PASS" if c["ok"] else "FAIL"), c["name"], "-", c["detail"])
        print(f"checks: {receipt['passed']}/{len(receipt['checks'])} passed, "
              f"{receipt['failed']} failed")
        return 1 if receipt["failed"] else 0
    proofs = falsifier_proofs()
    out = HERE / "work" / "runs"
    out.mkdir(parents=True, exist_ok=True)
    (out / "falsifier_log.json").write_text(canonical_json({"falsifiers": proofs}),
                                            encoding="utf-8")
    for p in proofs:
        if p["bites"] is None:
            print("---", p["id"], "-", p["detail"])
        else:
            print(("BITES" if p["bites"] else "NO-BITE"), p["id"],
                  f"({p.get('code', '')}) {p.get('detail', '')}")
    return 0 if all(p["bites"] for p in proofs if p["bites"] is not None) else 1


if __name__ == "__main__":
    sys.exit(main())
