"""ONT-A02 task-owned verifier: radioulnar definition, independent evidence, B4 result
and before/after radius mapping — re-measured from pinned inputs.

Reconciliation-first card: every clause of the done_when was already established by
prior verified work on the `forearm-package-20260924` lane (R1 radioulnar evidence,
O1 roll sign, I7 authorized B4 diagnostic with its before/after radius receipt).
This module RE-MEASURES the definition and mapping numbers from the pinned inputs
(chimanoid.xml, the session-5 packet, the frozen I7 candidate declaration and the
B4 known-good records), cross-checks every number against the hash-pinned receipts,
and emits
  evidence/state_snapshot.json    (input identities + presented state)
  evidence/numerical_receipt.json (measured vs record, verdicts, falsifier bookkeeping)
Outcome is decided by the FROZEN rules in PREREGISTRATION.md. Nothing is tuned;
falsifier hits are reported as they fall. NOTHING is executed against any store: the
old radius record and every failed alternative remain preserved.

Method provenance: the ONB construction is the protocol's DERIVATION 5.1 as
implemented in B4's `b4_common.onb` (constants ROLL_EPS/DEGENERATE_FLOOR inherited
by citation); the source-frame accumulation walk follows O1's documented rest-frame
assertion (arm quats identity). CPU-only, deterministic, no GPU, no network.
Run with `python -B`.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
EVIDENCE = HERE / "evidence"

INPUT_BIRTH = Path(r"E:/PythonChimera/Saved/meshes/monkey_birth.bin")
INPUT_PACK = Path(r"E:/PythonChimera/Saved/meshes/monkey_joints.bin")

REF_EXTRACTION = REFERENCE / "EXTRACTION.json"
REF_XML = REFERENCE / "baseline_snapshot" / "source_xml" / "chimanoid.xml"
REF_PACKET = REFERENCE / "baseline_snapshot" / "runs" / "actual_monkey_fit.json"
REF_MANIFEST = REFERENCE / "baseline_snapshot" / "MANIFEST.json"
REF_DECLARATION = REFERENCE / "receipts" / "I7_00_candidate_declaration.json"
REF_KG = REFERENCE / "receipts" / "B4_01_known_good_records.json"
REF_R07 = REFERENCE / "receipts" / "I7_07_gate_table.json"
REF_R08 = REFERENCE / "receipts" / "I7_08_radius_before_after.json"
REF_R09 = REFERENCE / "receipts" / "I7_09_c1_replacement.json"
REF_R10 = REFERENCE / "receipts" / "I7_10_coverage_topology.json"
REF_O1 = REFERENCE / "receipts" / "o1_combine_sign.json"
REF_R1_ARITH = REFERENCE / "receipts" / "R1_arithmetic.txt"
REF_R1_CITATIONS = REFERENCE / "receipts" / "R1_citations.md"
REF_C1_GEOM = REFERENCE / "receipts" / "C1_c1_geometry.txt"

# Frozen identity pins (O1's expected input hashes, reused; A01's vendor pin for the
# ulna mesh; radius.stl pinned by this attempt's extraction, asserted below).
EXPECT_SHA = {
    "birth": "550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c",
    "pack": "74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662",
    "ulna_stl": "710264159b68764d4bbd2b0e0b3b0d0c9b7bd67de9d3b0d33f8a1e8a2c9c8b0d",  # placeholder, replaced by extraction
}
# The placeholders above are replaced from reference/EXTRACTION.json at run time; the
# literal values below are the ones asserted when the extraction is absent (never used).
MESH_PIN_NAMES = {"meshes/ulna.stl": "ulna_stl", "meshes/radius.stl": "radius_stl"}

# C1's receipted anatomical basis (c1_geometry.txt SECTION 2), asserted to 1e-5.
C1_BASIS = {
    "a": np.array([0.060172, -0.987281, 0.147155]),
    "l": np.array([-0.008952, 0.146883, 0.989113]),
    "p": np.array([-0.998148, -0.060834, 0.000000]),
}

# Protocol constants inherited by citation (B4 challenge_protocol / compiler.py).
ROLL_EPS = 1e-9
DEGENERATE_FLOOR = 1e-12

# FROZEN tolerances (PREREGISTRATION.md "Frozen predictions").
TOL_MM = 1e-4          # N1 distances in mm (receipts quote 4 dp)
TOL_COMP_MM = 5e-4     # N1 decomposition components (receipts quote 3 dp)
TOL_ANGLE_DEG = 0.01   # N1 oblique angle
TOL_BASIS = 1e-5       # C1 receipted basis reproduction
TOL_RECORD_M = 1e-9    # N2 packet-scale coordinate/span reproduction
TOL_SCALE = 1e-12      # N2 uniform scale reproduction
TOL_PCT = 1e-6         # N2 percent-quantity reproduction
TOL_DELTA_M = 1e-9     # N2 site-displacement reproduction
TOL_RESIDUAL_DEG = 1e-9  # N4 O1 residual reproduction
TOL_LAW_PCT = 1e-9     # N2 law equality in the exact-float form


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(cid: str, description: str, recorded, measured, tol, verdict: bool,
          unit: str = "", source: str = "") -> dict:
    diff = None
    if isinstance(recorded, (int, float)) and isinstance(measured, (int, float)):
        diff = float(measured) - float(recorded)
    return {"id": cid, "description": description, "recorded": recorded,
            "measured": measured, "difference": diff, "tolerance": tol, "unit": unit,
            "verdict": "PASS" if verdict else "FAIL", "source": source}


def close(measured: float, recorded: float, tol: float) -> bool:
    return math.isfinite(measured) and math.isfinite(recorded) and abs(measured - recorded) <= tol


def reference_integrity() -> list[dict]:
    """Every reference/ file must match EXTRACTION.json (raw sha256 + bytes)."""
    ext = load_json(REF_EXTRACTION)
    rows = []
    for entry in ext["files"]:
        p = REFERENCE / entry["dest"]
        ok = p.is_file()
        got = sha256_file(p) if ok else None
        size = p.stat().st_size if ok else -1
        rows.append({"dest": entry["dest"], "origin": entry["origin"],
                     "path": entry.get("path"), "blob_sha1": entry.get("sha1") or entry.get("blob_sha1"),
                     "recorded_sha256": entry["sha256"], "measured_sha256": got,
                     "recorded_bytes": entry["bytes"], "measured_bytes": size,
                     "verdict": "PASS" if (ok and got == entry["sha256"] and size == entry["bytes"]) else "FAIL"})
    return rows


def manifest_identity() -> dict:
    """Reproduce the MANIFEST-recorded identities of the two content inputs.

    The audit-time working tree carried Windows line endings: the packet reproduces
    under a full CRLF conversion; the XML reproduces when ONLY its final newline is
    CRLF. Both transformations are recorded; the LF blob sagas are asserted against
    EXTRACTION.json anyway (reference_integrity)."""
    man_files = load_json(REF_MANIFEST)["files"]

    xml = REF_XML.read_bytes()
    xml_crlf_tail = xml[: xml.rfind(b"\n")] + b"\r\n"
    pkt = REF_PACKET.read_bytes()
    out = {
        "xml": {"manifest_recorded": man_files["source_xml/chimanoid.xml"]["sha256"],
                "lf_blob_sha256": sha256_bytes(xml),
                "crlf_tail_sha256": sha256_bytes(xml_crlf_tail),
                "lf_bytes": len(xml), "crlf_tail_bytes": len(xml_crlf_tail),
                "manifest_bytes": man_files["source_xml/chimanoid.xml"]["bytes"]},
        "packet": {"manifest_recorded": man_files["runs/actual_monkey_fit.json"]["sha256"],
                   "lf_blob_sha256": sha256_bytes(pkt),
                   "crlf_sha256": sha256_bytes(pkt.replace(b"\n", b"\r\n")),
                   "lf_bytes": len(pkt),
                   "crlf_bytes": len(pkt.replace(b"\n", b"\r\n")),
                   "manifest_bytes": man_files["runs/actual_monkey_fit.json"]["bytes"]},
    }
    out["xml"]["verdict"] = "PASS" if (
        out["xml"]["crlf_tail_sha256"] == out["xml"]["manifest_recorded"]
        and out["xml"]["crlf_tail_bytes"] == out["xml"]["manifest_bytes"]) else "FAIL"
    out["packet"]["verdict"] = "PASS" if (
        out["packet"]["crlf_sha256"] == out["packet"]["manifest_recorded"]
        and out["packet"]["crlf_bytes"] == out["packet"]["manifest_bytes"]) else "FAIL"
    return out


# ------------------------------------------------------------- source XML ----
def quat_rotmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def source_geometry() -> dict:
    """Rest-pose offsets from the pinned XML (chain read verbatim; quats identity)."""
    root = ET.parse(str(REF_XML)).getroot()
    bodies = {}

    def walk(elem, parent_world, parent_rot):
        name = elem.get("name")
        pos = np.array([float(v) for v in (elem.get("pos") or "0 0 0").split()])
        quat = np.array([float(v) for v in (elem.get("quat") or "1 0 0 0").split()])
        rot = parent_rot @ quat_rotmat(quat)
        world = parent_world + parent_rot @ pos
        bodies[name] = {"world": world, "rot": rot, "quat": quat, "local_pos": pos}
        for child in elem.findall("body"):
            walk(child, world, rot)

    wb = root.find("worldbody")
    for b in wb.findall("body"):
        walk(b, np.zeros(3), np.eye(3))

    out = {}
    for side, (ulna, radius, hand) in {"right": ("ulna", "radius", "hand_r"),
                                       "left": ("ulna_l", "radius_l", "hand_l")}.items():
        chain = [ulna, radius, hand]
        quats_ok = all(np.allclose(bodies[n]["quat"], [1, 0, 0, 0]) for n in chain)
        u2r = bodies[radius]["local_pos"].copy()
        r2h = bodies[hand]["local_pos"].copy()
        e2h = u2r + r2h
        out[side] = {"u2r": u2r.tolist(), "r2h": r2h.tolist(), "e2h": e2h.tolist(),
                     "u2r_norm_m": float(np.linalg.norm(u2r)),
                     "r2h_norm_m": float(np.linalg.norm(r2h)),
                     "e2h_norm_m": float(np.linalg.norm(e2h)),
                     "chain_sum_m": float(np.linalg.norm(u2r) + np.linalg.norm(r2h)),
                     "quats_identity": bool(quats_ok),
                     "elbow_world_m": bodies[ulna]["world"].tolist(),
                     "radius_world_m": bodies[radius]["world"].tolist(),
                     "hand_world_m": bodies[hand]["world"].tolist()}
    return out


def anatomical_decomposition(u2r: np.ndarray, e2h: np.ndarray) -> dict:
    a = u2r * 0.0 + e2h / np.linalg.norm(e2h)
    # lateral = +z orthogonalized (C1 Section 2)
    z = np.array([0.0, 0.0, 1.0])
    l = z - a * (a @ z)
    l = l / np.linalg.norm(l)
    p = np.cross(a, l)
    axial = float(u2r @ a)
    lateral = float(u2r @ l)
    post = float(u2r @ p)
    resid = float(np.linalg.norm(u2r - (axial * a + lateral * l + post * p)))
    angle = float(math.degrees(math.acos(max(-1.0, min(1.0, (u2r @ a) / np.linalg.norm(u2r))))))
    return {"a": a, "l": l, "p": p, "axial_mm": axial * 1000.0,
            "lateral_mm": lateral * 1000.0, "posterior_mm": post * 1000.0,
            "perp_norm_mm": float(np.linalg.norm(u2r - axial * a)) * 1000.0,
            "angle_deg": angle, "reconstruction_residual_m": resid}


def meshes_and_scales() -> dict:
    """XML-declared geom scales for the two vendor bone meshes (presentation pin)."""
    root = ET.parse(str(REF_XML)).getroot()
    out = {}
    for mesh in root.iter("mesh"):
        name = mesh.get("name")
        if name in ("ulna", "radius"):
            out[name] = {"file": mesh.get("file"),
                         "scale": [float(v) for v in mesh.get("scale").split()]}
    return out


# ----------------------------------------------------------------- packets ---
def packet_records() -> dict:
    pkt = load_json(REF_PACKET)
    segs = {s["source_body"]: s for s in pkt["segments"]}
    sites: dict[str, dict[str, dict]] = {}
    for s in pkt["sites"]:
        sites.setdefault(s["segment"], {})[s["name"]] = {
            "x_local": s["source_pos_local"], "fitted_global": s["fitted_pos_global"]}
    return {"packet": pkt, "segments": segs, "sites": sites}


def declaration() -> dict:
    return load_json(REF_DECLARATION)


def known_good() -> dict:
    return load_json(REF_KG)


def onb(p0, p1, q):
    """DERIVATION 5.1 ONB construction (B4 b4_common.onb, constants inherited)."""
    a = np.asarray(p1, float) - np.asarray(p0, float)
    n = np.linalg.norm(a)
    if n < DEGENERATE_FLOOR:
        raise ValueError("degenerate bone")
    a = a / n
    p0 = np.asarray(p0, float)
    q = np.asarray(q, float)
    t = (q - p0) - a * (a @ (q - p0))
    tnorm = float(np.linalg.norm(t))
    if tnorm < ROLL_EPS:
        raise ValueError("axis_parallel_roll")
    b = t / tnorm
    c = np.cross(a, b)
    B = np.column_stack([a, b, c])
    assert abs(np.linalg.det(B) - 1.0) <= 1e-9
    return B


def radius_before_after() -> dict:
    pk = packet_records()
    decl = declaration()
    kg = known_good()
    out = {"sides": {}, "checks": []}

    for b, side_key in (("radius", "ulna"), ("radius_l", "ulna_l")):
        seg = pk["segments"][b]
        rec_k = kg["records"][b]["landmarks"]
        rec_u = decl["records"][side_key]["landmarks"]
        A = np.asarray(seg["source_origin"], float)
        src_D = np.asarray(rec_k["dist"]["source"], float)
        roll_source = np.asarray(rec_k["roll"]["source"], float)
        P_old = np.asarray(seg["fitted_origin"], float)
        P_d_old = np.asarray(seg["dist_landmark"], float)
        s_old = float(seg["scale"][0])
        G_old = np.asarray(seg["rotation"], float)
        Bp_old = np.asarray(seg["frame_basis"], float)
        P_new = np.asarray(rec_u["dist"]["target"], float)
        Q = np.asarray(rec_u["roll"]["target"], float)

        span_src = float(np.linalg.norm(src_D - A))
        span_old = float(np.linalg.norm(P_d_old - P_old))
        span_new = float(np.linalg.norm(P_d_old - P_new))
        s_new = span_new / span_src
        B_new = onb(A, src_D, roll_source)
        Bp_new = onb(P_new, P_d_old, Q)
        G_new = Bp_new @ B_new.T
        L_new = Bp_new @ np.diag([s_new] * 3) @ B_new.T
        t_new = P_new - G_new @ A
        gap = float(np.linalg.norm(P_old - P_new))

        deltas = {}
        for name, rec in pk["sites"][b].items():
            x = np.asarray(rec["x_local"], float)
            pred_old = P_old + (Bp_old @ np.diag([s_old] * 3) @ B_new.T) @ x
            pred_new = P_new + L_new @ x
            deltas[name] = float(np.linalg.norm(pred_new - pred_old))

        out["sides"][b] = {
            "A": A.tolist(), "src_D": src_D.tolist(), "roll_source": roll_source.tolist(),
            "span_src_m": span_src, "s_old": s_old, "G_old": G_old.tolist(),
            "Bp_old_max_abs_diff_from_onb": float(np.max(np.abs(Bp_old - onb(P_old, P_d_old, Q)))),
            "G_old_max_abs_diff_from_onb_closure": float(np.max(np.abs(G_old - Bp_old @ onb(A, src_D, roll_source).T))),
            "P_old": P_old.tolist(), "P_d_old": P_d_old.tolist(), "span_old_m": span_old,
            "P_new": P_new.tolist(), "span_new_m": span_new, "s_new": s_new,
            "det_old_s3": s_old ** 3, "det_new_s3": s_new ** 3,
            "G_new_vs_old_max_abs_diff": float(np.max(np.abs(G_new - G_old))),
            "Bp_new_vs_old_max_abs_diff": float(np.max(np.abs(Bp_new - Bp_old))),
            "t_new": t_new.tolist(),
            "gap_m": gap, "site_deltas": deltas,
            "max_delta_m": max(deltas.values()), "worst_site": max(deltas, key=deltas.get),
            "residual_packet": seg.get("residual"),
        }
    return out


def before_map_reconstruction() -> dict:
    """No-execution check: the frozen BEFORE map (packet scale/rotation/landmarks)
    reproduces the packet's own fitted globals for every radius site, and the radius
    distal landmark is unchanged. A non-zero deviation would mean this attempt touched
    the record; it must be zero."""
    pk = packet_records()
    kg = known_good()
    out = {}
    for b in ("radius", "radius_l"):
        seg = pk["segments"][b]
        rec_k = kg["records"][b]["landmarks"]
        A = np.asarray(seg["source_origin"], float)
        src_D = np.asarray(rec_k["dist"]["source"], float)
        s_old = float(seg["scale"][0])
        Bp_old = np.asarray(seg["frame_basis"], float)
        P_old = np.asarray(seg["fitted_origin"], float)
        B = onb(A, src_D, np.asarray(rec_k["roll"]["source"], float))
        worst = 0.0
        for name, rec in pk["sites"][b].items():
            pred = P_old + (Bp_old @ np.diag([s_old] * 3) @ B.T) @ np.asarray(rec["x_local"], float)
            worst = max(worst, float(np.linalg.norm(pred - np.asarray(rec["fitted_global"], float))))
        out[b] = {
            "max_abs_deviation_m": worst,
            "fitted_origin_equals_prox_landmark": bool(np.allclose(P_old, np.asarray(rec_k["prox"]["target"], float), atol=0.0)),
            "dist_landmark_equals_packet": bool(np.allclose(np.asarray(seg["dist_landmark"], float), np.asarray(rec_k["dist"]["target"], float), atol=0.0)),
            "n_sites": len(pk["sites"][b]),
        }
    return out


def fraction_law(src: dict) -> dict:
    pk = packet_records()
    decl = declaration()
    k_rad = float(decl["records"]["ulna"]["implied_axial_scale"])
    seg = pk["segments"]["radius"]
    span_t_old = float(np.linalg.norm(np.asarray(seg["dist_landmark"], float)
                                      - np.asarray(seg["fitted_origin"], float)))
    src_off = src["right"]["u2r_norm_m"]
    src_forearm = src["right"]["e2h_norm_m"]
    derived_mm = src_off * k_rad * 1000.0
    frac_source = 100.0 * src_off / src_forearm
    frac_target = 100.0 * derived_mm / (span_t_old * 1000.0)
    ratio = k_rad / (span_t_old / src_forearm)
    return {"derived_distal_point_mm": derived_mm,
            "target_per_edge_fraction_pct": frac_target,
            "source_authored_fraction_pct": frac_source,
            "drift_factor": ratio,
            "law_product_pct": frac_source * ratio,
            "law_exact": abs(frac_source * ratio - frac_target) <= TOL_LAW_PCT}


# ------------------------------------------------------------------ B4 -------
def b4_presentation() -> dict:
    gate = load_json(REF_R07)
    r08 = load_json(REF_R08)
    r09 = load_json(REF_R09)
    r10 = load_json(REF_R10)
    verdicts = {}
    for side in ("ulna", "ulna_l"):
        verdicts[side] = {k: v["verdict"] for k, v in gate[side].items()}
    t6 = gate["_T6_utility_ban"]
    n_pass = sum(1 for side in verdicts.values() for v in side.values() if v == "PASS")
    n_cells = sum(len(side) for side in verdicts.values())
    return {
        "protocol": "existing B4 T1-T6, tolerances unchanged (challenge_protocol §2-§4, amendments A1-A5)",
        "side_test_verdicts": verdicts,
        "side_test_verdict_cells": n_cells,
        "side_test_pass": n_pass,
        "t6_process": {"verdict": t6["verdict"],
                       "banned_evidence_occurrences": t6["banned_evidence_occurrences"]},
        "t6_per_side_headline": "12/12 side-test verdicts + T6 process PASS (I7 report wording; 07 receipt stores T6 once, T1-T5 per side)",
        "key_numbers": {
            "t2_source_bone_len_m": gate["ulna"]["T2_landmark_sufficiency"]["source_bone_len_m"],
            "t2_target_pair_len_m": gate["ulna"]["T2_landmark_sufficiency"]["target_pair_len_m"],
            "t4_ortho_note": "orthonormality 4.1e-16 / det(Q) 1 / anchor gap 0.0 (receipt 07 subchecks)",
            "t4_c1_worst_delta_pts": gate["ulna"]["T4_transform_explainability"]["worst_c1_delta_pts"],
            "t5_resolution_count": gate["ulna"]["T5_uniqueness"]["resolution_supporters"],
        },
        "before_after_receipt_ok": r08.get("ok"),
        "c1_replacement_ok": r09.get("ok"),
        "coverage": {"scenario_counts": r10.get("scenario_counts"), "ok": r10.get("ok")},
        "bounds": "SOURCE-KINEMATIC FIDELITY ONLY; R1 refutation retained; no production radius "
                  "supersession, hand fit or training-body change authorized or executed; a "
                  "diagnostic PASS does not close A03.",
    }


def o1_evidence() -> dict:
    o1 = load_json(REF_O1)
    decl = load_json(REF_DECLARATION)
    declared = decl["roll_choice"]["o1_receipted_residuals_deg"]
    recorded = {c["roll_candidate"]: c["error_no_flip_deg"]
                for c in o1.get("per_candidate", []) if "roll_candidate" in c}
    out = {"receipt_keys": sorted(o1.keys()), "declared_residuals_deg": declared,
           "recorded_error_no_flip_deg": recorded,
           "unanimous_verdict": o1.get("unanimous_verdict"),
           "sign_mapping": o1.get("SIGN_VERDICT", {}).get("world_mapping")}
    rows = []
    for site, val in declared.items():
        rec = recorded.get(site)
        rows.append({"site": site, "declared": val, "receipt": rec,
                     "verdict": ("PASS" if (isinstance(rec, (int, float))
                                            and close(float(rec), float(val), TOL_RESIDUAL_DEG))
                                 else ("RECORDED_ONLY" if rec is None else "FAIL"))})
    out["rows"] = rows
    out["law"] = decl["roll_choice"]["law"]
    out["sign_basis"] = decl["roll_choice"]["sign_basis"]
    out["residual_role"] = "the residual SELECTS the pair and is NOT validation (roll-ref site circular, C3 §2.5)"
    return out


def primary_evidence(src: dict) -> dict:
    """R1's applicable primary sources + the band arithmetic, from the pinned receipts."""
    arith = REF_R1_ARITH.read_text(encoding="utf-8")
    citations = REF_R1_CITATIONS.read_text(encoding="utf-8")
    return {
        "applicable_lane": "HUMAN base anatomy — the source is FreeMusco's fictional "
                           "'Chimanoid' (modified human model); no species-specific osteometry can exist.",
        "sources": [
            {"id": "S1", "citation": "London 1981, JBJS Am 63:529-535 (8 elbows, true-lateral roentgenography)",
             "finding": "flexion about a single axis through the trochlear sulcus and capitellar periphery; "
                        "the radius center is AT the elbow joint."},
            {"id": "S2", "citation": "Brownhill et al. 2009, J Biomech Eng 131:021005 (12 cadaveric specimens)",
             "finding": "the radial head is a defining landmark OF the ulnohumeral flexion axis; its center lies on the hinge."},
            {"id": "S3", "citation": "Hollister et al. 1994, Clin Orthop 298:272-276 (fresh specimens)",
             "finding": "the forearm rotation axis runs from the radial head center to the distal ulna center; the radial "
                        "head is the proximal terminus — no positive distal fraction."},
        ],
        "convergent_finding": "radial head center ≈ 0 % ± ~1 % of forearm length distal to the humeroulnar hinge "
                              "(coaxial; transverse-dominated offset), outside the frozen 4-12 % band by >= 3.0 points.",
        "inapplicable_recorded": "Macaca morphometry (Cheng & Scott 2000; Graham & Scott 2003) measures other quantities; "
                                 "recorded INAPPLICABLE, never forced.",
        "in_model_corroboration": "the model's own radius biceps-tuberosity site sits at 8.020 % axial — the radius ANATOMY "
                                  "does not start at its body origin (qualitative only).",
        "band_margin_points": 4.0 - 1.0,
        "arith_receipt_excerpt": arith.strip().splitlines()[-8:],
        "citations_receipt_excerpt": citations.strip().splitlines()[:12],
    }


# --------------------------------------------------------------- receipts -----
def build_evidence() -> tuple[dict, dict]:
    integrity = reference_integrity()
    manifest = manifest_identity()
    src = source_geometry()
    decompo = anatomical_decomposition(np.asarray(src["right"]["u2r"], float),
                                       np.asarray(src["right"]["e2h"], float))
    meshes = meshes_and_scales()
    map_ = radius_before_after()
    law = fraction_law(src)
    b4 = b4_presentation()
    o1 = o1_evidence()
    primary = primary_evidence(src)

    r08 = load_json(REF_R08)
    decl = declaration()
    k_rad = float(decl["records"]["ulna"]["implied_axial_scale"])
    checks: list[dict] = []

    # N0 — identities (falsifier F1)
    checks.append(check("N0.reference_integrity", "every reference/ file matches EXTRACTION.json",
                        True, all(r["verdict"] == "PASS" for r in integrity), 0,
                        all(r["verdict"] == "PASS" for r in integrity), "", "reference/EXTRACTION.json"))
    checks.append(check("N0.xml_manifest_identity", "XML reproduces the MANIFEST-recorded identity (single trailing CRLF)",
                        True, manifest["xml"]["verdict"] == "PASS", 0, manifest["xml"]["verdict"] == "PASS",
                        "", "baseline_snapshot/MANIFEST.json"))
    checks.append(check("N0.packet_manifest_identity", "packet reproduces the MANIFEST-recorded identity (full CRLF)",
                        True, manifest["packet"]["verdict"] == "PASS", 0, manifest["packet"]["verdict"] == "PASS",
                        "", "baseline_snapshot/MANIFEST.json"))
    birth_ok = sha256_file(INPUT_BIRTH) == EXPECT_SHA["birth"]
    pack_ok = sha256_file(INPUT_PACK) == EXPECT_SHA["pack"]
    checks.append(check("N0.mesh_input_pins", "monkey_birth.bin / monkey_joints.bin hash pins",
                        [EXPECT_SHA["birth"], EXPECT_SHA["pack"]],
                        [sha256_file(INPUT_BIRTH), sha256_file(INPUT_PACK)], 0, birth_ok and pack_ok,
                        "", "O1 frozen EXPECT_SHA"))

    # N1 — definition from the pinned XML alone (physical quantities, C1 receipt 4 dp)
    checks.append(check("N1.u2r_mm", "|ulna->radius| source offset", 23.0746,
                        src["right"]["u2r_norm_m"] * 1000.0, 5e-4, close(src["right"]["u2r_norm_m"] * 1000.0, 23.0746, 5e-4),
                        "mm", "C1 c1_geometry.txt / R1 §3"))
    checks.append(check("N1.r2h_mm", "|radius->hand_r| source span", 292.0294,
                        src["right"]["r2h_norm_m"] * 1000.0, 5e-4, close(src["right"]["r2h_norm_m"] * 1000.0, 292.0294, 5e-4),
                        "mm", "C1 c1_geometry.txt / R1 §3"))
    checks.append(check("N1.e2h_mm", "|elbow->hand| straight-line", 305.7922,
                        src["right"]["e2h_norm_m"] * 1000.0, 5e-4, close(src["right"]["e2h_norm_m"] * 1000.0, 305.7922, 5e-4),
                        "mm", "C1 c1_geometry.txt / R1 §3"))
    checks.append(check("N1.axial_mm", "axial component of the ulna->radius offset", 14.324,
                        decompo["axial_mm"], TOL_COMP_MM, close(decompo["axial_mm"], 14.324, TOL_COMP_MM),
                        "mm", "C1 §2 / R1 §3"))
    checks.append(check("N1.lateral_mm", "lateral component", 18.088, decompo["lateral_mm"],
                        TOL_COMP_MM, close(decompo["lateral_mm"], 18.088, TOL_COMP_MM), "mm", "C1 §2 / R1 §3"))
    checks.append(check("N1.posterior_mm", "posterior component", 0.301, decompo["posterior_mm"],
                        TOL_COMP_MM, close(decompo["posterior_mm"], 0.301, TOL_COMP_MM), "mm", "C1 §2 / R1 §3"))
    checks.append(check("N1.angle_deg", "obliquity of the offset to the forearm axis", 51.63,
                        decompo["angle_deg"], TOL_ANGLE_DEG, close(decompo["angle_deg"], 51.63, TOL_ANGLE_DEG),
                        "deg", "C1 §2 / R1 §3"))
    checks.append(check("N1.source_fraction_pct", "authored fraction = |ulna->radius| / |elbow->hand|",
                        7.5459, law["source_authored_fraction_pct"], 1e-3,
                        close(law["source_authored_fraction_pct"], 7.5459, 1e-3), "%", "R1 arithmetic.txt"))
    for name, idx in (("a", 0), ("l", 1), ("p", 2)):
        got = np.asarray([decompo["a"], decompo["l"], decompo["p"]][idx], float)
        diff = float(np.max(np.abs(got - C1_BASIS[name])))
        checks.append(check(f"N1.basis_{name}", f"anatomical basis {name} reproduces C1's receipted value",
                            C1_BASIS[name].tolist(), got.round(6).tolist(), TOL_BASIS, diff <= TOL_BASIS,
                            "vector", "C1 §2"))
    checks.append(check("N1.quats_identity", "arm-chain rest quats identity (C1/DERIVATION precondition)",
                        True, src["right"]["quats_identity"], 0.0, bool(src["right"]["quats_identity"]),
                        "", "C1 §1"))

    # N2 — before/after mapping vs the I7 receipt 08
    for b, rk in (("radius", "radius"), ("radius_l", "radius_l")):
        rs = map_["sides"][b]
        rb = r08["before"][rk]
        ra = r08["after"][rk]
        rm = r08["mechanism"][rk]
        checks.append(check(f"N2.{b}.span_old_m", f"{b} packet span", rb["span_m"], rs["span_old_m"],
                            TOL_RECORD_M, close(rs["span_old_m"], rb["span_m"], TOL_RECORD_M), "m", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.s_old", f"{b} packet scale", rb["scale"], rs["s_old"], TOL_SCALE,
                            close(rs["s_old"], rb["scale"], TOL_SCALE), "", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.P_old", f"{b} before anchor P", rb["P"], rs["P_old"], TOL_RECORD_M,
                            all(close(a, c, TOL_RECORD_M) for a, c in zip(rs["P_old"], rb["P"])), "m", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.gap_m", f"{b} closure gap |P_old - P_new|", rm["gap_m"], rs["gap_m"],
                            TOL_RECORD_M, close(rs["gap_m"], rm["gap_m"], TOL_RECORD_M), "m", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.s_new", f"{b} after scale", ra["scale"], rs["s_new"], TOL_SCALE,
                            close(rs["s_new"], ra["scale"], TOL_SCALE), "", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.span_new_m", f"{b} after span", ra["span_m"], rs["span_new_m"],
                            TOL_RECORD_M, close(rs["span_new_m"], ra["span_m"], TOL_RECORD_M), "m", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.det_new", f"{b} det(full map) after = s^3", ra["det_full_map_L"],
                            rs["det_new_s3"], 1e-15, close(rs["det_new_s3"], ra["det_full_map_L"], 1e-15), "", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.G_unchanged", f"{b} rigid part G vs packet (max abs diff)",
                            ra["G_vs_packet_max_abs_diff"], rs["G_new_vs_old_max_abs_diff"], 1e-15,
                            close(rs["G_new_vs_old_max_abs_diff"], ra["G_vs_packet_max_abs_diff"], 1e-15), "", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.max_delta_m", f"{b} max site displacement", r08["site_deltas"][rk]["max_displacement_m"],
                            rs["max_delta_m"], TOL_DELTA_M, close(rs["max_delta_m"], r08["site_deltas"][rk]["max_displacement_m"], TOL_DELTA_M),
                            "m", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.worst_site", f"{b} worst-displaced site", r08["site_deltas"][rk]["worst_site"],
                            rs["worst_site"], 0.0, rs["worst_site"] == r08["site_deltas"][rk]["worst_site"], "", "I7 receipt 08"))
        # per-site deltas
        worst = max((abs(rs["site_deltas"][n] - v) for n, v in r08["site_deltas"][rk]["all"].items()), default=0.0)
        checks.append(check(f"N2.{b}.site_deltas_all", f"{b} all {len(rs['site_deltas'])} site deltas",
                            "receipt 08 all[]", f"max abs diff {worst:.3e}", TOL_DELTA_M, worst <= TOL_DELTA_M, "m", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.n_sites", f"{b} site count", r08["site_deltas"][rk]["n_sites"],
                            len(rs["site_deltas"]), 0, len(rs["site_deltas"]) == r08["site_deltas"][rk]["n_sites"], "", "I7 receipt 08"))
        checks.append(check(f"N2.{b}.G_closure", f"{b} packet rotation reconstructs as Bp@B^T",
                            "A4/B4 verified", f"max abs diff {rs['G_old_max_abs_diff_from_onb_closure']:.3e}", 1e-9,
                            rs["G_old_max_abs_diff_from_onb_closure"] <= 1e-9, "", "A4/B4 (this attempt's 3rd check)"))
    checks.append(check("N2.fraction_law", "7.5459% x k_rad/axis-ratio = target fraction (exact-float form)",
                        r08["fractions"]["target_per_edge_fraction_pct"], law["law_product_pct"],
                        TOL_LAW_PCT, law["law_exact"], "%", "R1 §5.3 / I7 receipt 08"))
    checks.append(check("N2.derived_mm", "derived distal point = |ulna->radius| x k_rad", r08["fractions"]["derived_distal_point_mm"],
                        law["derived_distal_point_mm"], TOL_COMP_MM, close(law["derived_distal_point_mm"], r08["fractions"]["derived_distal_point_mm"], TOL_COMP_MM),
                        "mm", "I7 receipt 08"))
    checks.append(check("N2.drift_factor", "k_rad / (target forearm ratio)", r08["fractions"]["drift_factor"],
                        law["drift_factor"], TOL_PCT, close(law["drift_factor"], r08["fractions"]["drift_factor"], TOL_PCT),
                        "", "R1 §5.3"))
    checks.append(check("N2.scale_change_pct", "uniform scale change", r08["after"]["radius"]["scale_change_pct"],
                        100.0 * (map_["sides"]["radius"]["s_new"] / map_["sides"]["radius"]["s_old"] - 1.0), TOL_PCT,
                        close(100.0 * (map_["sides"]["radius"]["s_new"] / map_["sides"]["radius"]["s_old"] - 1.0),
                              r08["after"]["radius"]["scale_change_pct"], TOL_PCT), "%", "I7 receipt 08"))

    # N3 — B4 presentation identity
    checks.append(check("N3.gate_cells", "T1-T5 verdict cells both sides all PASS",
                        f"{b4['side_test_verdict_cells']} cells", f"{b4['side_test_pass']} PASS", 0,
                        b4["side_test_pass"] == b4["side_test_verdict_cells"], "", "I7 receipt 07"))
    checks.append(check("N3.t6", "T6 utility-ban process PASS, 0 banned occurrences",
                        {"verdict": "PASS", "banned": 0}, b4["t6_process"], 0,
                        b4["t6_process"]["verdict"] == "PASS" and b4["t6_process"]["banned_evidence_occurrences"] == 0,
                        "", "I7 receipt 07"))
    checks.append(check("N3.receipt_08_ok", "before/after receipt internal ok flag", True, r08.get("ok"),
                        0, r08.get("ok") is True, "", "I7 receipt 08"))
    checks.append(check("N3.coverage_ok", "coverage topology receipt ok flag", True, b4["coverage"]["ok"],
                        0, b4["coverage"]["ok"] is True, "", "I7 receipt 10"))

    # N4 — independent evidence checks
    checks.append(check("N4.band_margin", "primary fraction 0-1% vs frozen 4-12% band margin",
                        3.0, primary["band_margin_points"], 0.0, primary["band_margin_points"] >= 3.0, "points", "R1 §6.1"))
    for row in o1["rows"]:
        if row["receipt"] is not None:
            ok = close(float(row["receipt"]), float(row["declared"]), TOL_RESIDUAL_DEG)
            checks.append(check(f"N4.o1_{row['site']}", "O1 declared residual reproduces from the O1 receipt",
                                row["receipt"], row["declared"], TOL_RESIDUAL_DEG, ok, "deg", "o1_combine_sign.json"))
    checks.append(check("N4.c1_10of10", "C1's independent 10/10 landmark set reproduced under the declared frame",
                        True, load_json(REF_R09)["ok"], 0, load_json(REF_R09)["ok"] is True, "", "I7 receipt 09"))
    checks.append(check("N4.o1_unanimous", "O1 receipt unanimous NO-FLIP sign verdict",
                        True, o1["unanimous_verdict"], 0, o1["unanimous_verdict"] is True,
                        "", "o1_combine_sign.json"))
    # fraction cross-check against the R1 receipt's rounded arithmetic
    checks.append(check("N4.arith_source_pct", "R1 arithmetic receipt source fraction (rounded inputs)",
                        7.54585630372521, law["source_authored_fraction_pct"], 1e-5,
                        close(law["source_authored_fraction_pct"], 7.54585630372521, 1e-5), "%", "R1 arithmetic.txt"))

    n_fail = sum(1 for c in checks if c["verdict"] != "PASS")
    state = {
        "schema": "chimera.ont_a02_state.v1",
        "task_id": "A02", "card_id": "ONT-A02",
        "attempt_id": "a6c4ddd216a648348d0810f05dd464d4",
        "arrival_id": "arrival-db815a40e472418c810c538a333bbc5e",
        "criteria_sha256": "ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1",
        "scope_sha256": "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6",
        "inputs": {
            "reference_extraction_sha256": sha256_file(REF_EXTRACTION),
            "xml_sha256": sha256_file(REF_XML),
            "packet_sha256": sha256_file(REF_PACKET),
            "manifest_sha256": sha256_file(REF_MANIFEST),
            "declaration_sha256": sha256_file(REF_DECLARATION),
            "known_good_sha256": sha256_file(REF_KG),
            "receipt_07_sha256": sha256_file(REF_R07),
            "receipt_08_sha256": sha256_file(REF_R08),
            "receipt_09_sha256": sha256_file(REF_R09),
            "receipt_10_sha256": sha256_file(REF_R10),
            "o1_combine_sign_sha256": sha256_file(REF_O1),
            "r1_arithmetic_sha256": sha256_file(REF_R1_ARITH),
            "r1_citations_sha256": sha256_file(REF_R1_CITATIONS),
            "c1_geometry_sha256": sha256_file(REF_C1_GEOM),
            "monkey_birth_sha256": sha256_file(INPUT_BIRTH),
            "monkey_joints_sha256": sha256_file(INPUT_PACK),
            "ulna_stl_sha256": sha256_file(REFERENCE / "meshes" / "ulna.stl"),
            "radius_stl_sha256": sha256_file(REFERENCE / "meshes" / "radius.stl"),
        },
        "input_pins": {
            "birth_expected": EXPECT_SHA["birth"], "pack_expected": EXPECT_SHA["pack"],
            "birth_ok": sha256_file(INPUT_BIRTH) == EXPECT_SHA["birth"],
            "pack_ok": sha256_file(INPUT_PACK) == EXPECT_SHA["pack"],
        },
        "reference_integrity": integrity,
        "manifest_identity": manifest,
        "definition": {
            "source": source_geometry(),
            "anatomical_decomposition_right": {k: (v.tolist() if isinstance(v, np.ndarray) else v)
                                               for k, v in decompo.items()},
            "meshes_declared": meshes,
            "what_it_measures": "radius BODY-ORIGIN frame offset in the ulna frame (kinematic joint-frame "
                                "offset), rest pose; NOT a bone-landmark distance and NOT a radial-head position",
            "definition_text": "P body_origin:ulna <-> elbow_R; P_d body_origin:radius <-> derived point "
                               "elbow_R + 5.1158 mm along unit(elbow->wrist)",
        },
        "independent_evidence": primary,
        "o1_evidence": o1,
        "b4_result": b4,
        "before_after_mapping": map_,
        "fraction_law": law,
        "checks": checks,
        "check_summary": {"total": len(checks), "pass": len(checks) - n_fail, "fail": n_fail},
        "bounds": {
            "b4": "source-kinematic fidelity only; R1 refutation retained",
            "executed": False,
            "preserved": "old radius record, U-ANA, H-BODY and every failed alternative remain history",
            "a03": "a diagnostic PASS does not close A03 or authorize mechanically qualified grasp",
        },
    }
    receipt = {
        "schema": "chimera.ont_a02_numerical_receipt.v1",
        "task_id": "A02", "card_id": "ONT-A02",
        "attempt_id": state["attempt_id"],
        "preregistration_sha256": sha256_file(HERE / "PREREGISTRATION.md"),
        "checks": checks,
        "summary": state["check_summary"],
        "outcome": ("PRESENTED_AND_VERIFIED" if n_fail == 0 else "PRESENTED_WITH_DISCREPANCY"),
        "falsifier_bookkeeping": {
            "F1_identity": "no identity mismatch" if all(r["verdict"] == "PASS" for r in integrity)
                           and manifest["xml"]["verdict"] == "PASS" and manifest["packet"]["verdict"] == "PASS"
                           else "identity mismatch recorded",
            "F2_value": f"{n_fail} value checks outside tolerance" if n_fail else "none",
            "F3_visual": "reported by the capture manifest validation + bounds regression (see render receipt)",
            "F4_execution": "no execution, no write outside the attempt workspace, no anatomical relabeling",
        },
    }
    return state, receipt


def write_receipts() -> tuple[dict, dict]:
    EVIDENCE.mkdir(exist_ok=True)
    state, receipt = build_evidence()
    (EVIDENCE / "state_snapshot.json").write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    receipt["state_snapshot_sha256"] = sha256_file(EVIDENCE / "state_snapshot.json")
    (EVIDENCE / "numerical_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    return state, receipt


def main() -> int:
    state, receipt = write_receipts()
    s = state["check_summary"]
    print(f"checks {s['pass']}/{s['total']} PASS  outcome={receipt['outcome']}")
    for c in state["checks"]:
        if c["verdict"] != "PASS":
            print(f"  FAIL {c['id']}: recorded={c['recorded']} measured={c['measured']} tol={c['tolerance']}")
    print("definition:", json.dumps(state["definition"]["anatomical_decomposition_right"], default=str)[:220])
    print("law:", {k: round(v, 9) if isinstance(v, float) else v for k, v in state["fraction_law"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
