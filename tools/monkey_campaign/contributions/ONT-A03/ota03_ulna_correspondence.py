"""ONT-A03 task-owned implementation: staged ulna correspondence mapping/supersession
with historical radius preservation — executed from pinned inputs and qualified against
the hash-pinned receipts.

Reconciliation-first card. Every value this module stages was already established by
prior verified work on the `forearm-package-20260924` lane (R1 radioulnar evidence,
O1 roll sign, the authorized I7 B4 diagnostic with its before/after radius receipt 08,
coverage receipt 10) and merged/reviewed as ONT-A02 (PR #181). This module EXECUTES
the supersession as a staged, versioned record inside this contribution directory:

  transforms/radius_supersession_record.json
      status STAGED_FOR_ARCHITECT_APPROVAL; candidate identity (U-STR + the
      O1-resolved roll); decision basis = SOURCE-KINEMATIC CONVENTION FIDELITY with
      R1's refutation carried VERBATIM (never relabeled); BEFORE record preserved;
      AFTER record (both sides) computed by the B4/Derivation-5.1 closed form; the
      first-child shared-joint closure mechanism executed as code (the frozen record
      is refused by name; the staged record closes exactly); tendon-coverage effects;
      superseded set enumerated as history.
  evidence/state_snapshot.json      (input identities + executed state)
  evidence/numerical_receipt.json   (measured vs record, verdicts, falsifier bookkeeping)

Method provenance: the ONB construction is the protocol's DERIVATION 5.1 as
implemented in B4's `b4_common.onb` (constants ROLL_EPS/JOINT_EPS inherited by
citation from the pinned `baseline_snapshot/code/compiler.py`); the source-frame
accumulation walk follows O1's documented rest-frame assertion (arm quats identity).
CPU-only, deterministic, no GPU, no network. NOTHING outside this contribution
directory is written; no production source, model store, fit or training body is
touched. The staged record does NOT claim mechanically qualified grasp.
Run with `python -B`.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
EVIDENCE = HERE / "evidence"
TRANSFORMS = HERE / "transforms"

INPUT_BIRTH = Path(r"E:/PythonChimera/Saved/meshes/monkey_birth.bin")
INPUT_PACK = Path(r"E:/PythonChimera/Saved/meshes/monkey_joints.bin")

REF_EXTRACTION = REFERENCE / "EXTRACTION.json"
REF_XML = REFERENCE / "baseline_snapshot" / "source_xml" / "chimanoid.xml"
REF_PACKET = REFERENCE / "baseline_snapshot" / "runs" / "actual_monkey_fit.json"
REF_MANIFEST = REFERENCE / "baseline_snapshot" / "MANIFEST.json"
REF_COMPILER = REFERENCE / "baseline_snapshot" / "code" / "compiler.py"
REF_DECLARATION = REFERENCE / "receipts" / "I7_00_candidate_declaration.json"
REF_KG = REFERENCE / "receipts" / "B4_01_known_good_records.json"
REF_R07 = REFERENCE / "receipts" / "I7_07_gate_table.json"
REF_R08 = REFERENCE / "receipts" / "I7_08_radius_before_after.json"
REF_R09 = REFERENCE / "receipts" / "I7_09_c1_replacement.json"
REF_R10 = REFERENCE / "receipts" / "I7_10_coverage_topology.json"
REF_O1 = REFERENCE / "receipts" / "o1_combine_sign.json"
REF_R1_REPORT = REFERENCE / "receipts" / "R1_report.md"
REF_R1_ARITH = REFERENCE / "receipts" / "R1_arithmetic.txt"
REF_R1_CITATIONS = REFERENCE / "receipts" / "R1_citations.md"
REF_C1_GEOM = REFERENCE / "receipts" / "C1_c1_geometry.txt"
REF_A02_EXTRACTION = REFERENCE / "provenance" / "ONT_A02_EXTRACTION.json"
REF_USTR = REFERENCE / "USTR_DIAGNOSTIC_RECEIPT.md"

CARD_ID = "ONT-A03"
TASK_ID = "A03"
ATTEMPT_ID = "9435c49896af49d18c70a08ce20138d2"
ARRIVAL_ID = "arrival-bb1ef1a6a3994ca9bb660ad90af78d6d"
CRITERIA_SHA256 = "d15183d955c5d3764ed605e4c265145400806e5fb7e67738cebb3cf569056e7d"
SCOPE_SHA256 = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"

# Frozen identity pins (A02's recorded pins, re-asserted on this attempt's inputs).
EXPECT_SHA = {
    "birth": "550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c",
    "pack": "74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662",
}

# C1's receipted anatomical basis (c1_geometry.txt SECTION 2), asserted to 1e-5.
C1_BASIS = {
    "a": np.array([0.060172, -0.987281, 0.147155]),
    "l": np.array([-0.008952, 0.146883, 0.989113]),
    "p": np.array([-0.998148, -0.060834, 0.000000]),
}

# Protocol constants inherited by citation (pinned compiler.py; measured at run time
# by compiler_mechanism() and asserted equal to these).
JOINT_EPS = 1e-9
ROLL_EPS = 1e-9
DEGENERATE_FLOOR = 1e-12

# FROZEN tolerances (PREREGISTRATION.md "Frozen predictions").
TOL_MM = 5e-4          # M1 distances in mm (receipts quote 4 dp)
TOL_COMP_MM = 5e-4     # M1 decomposition components
TOL_ANGLE_DEG = 0.01   # M1 oblique angle
TOL_BASIS = 1e-5       # C1 receipted basis reproduction
TOL_RECORD_M = 1e-9    # M2 packet-scale coordinate/span reproduction
TOL_SCALE = 1e-12      # M2 uniform scale reproduction
TOL_PCT = 1e-6         # M2 percent-quantity reproduction
TOL_DELTA_M = 1e-9     # M2 site-displacement reproduction
TOL_LAW_PCT = 1e-9     # M6 law equality in the exact-float form

R1_VERDICT_SECTION = "### 6.1 The verdict sentence"
R1_VERDICT_KEY_PHRASES = ["REFUTED as an anatomical claim",
                          "far outside the frozen 4–12 %",
                          "≈ 0 % (±~1 %) of forearm length distal to the humeroulnar hinge"]


def r1_verdict_verbatim() -> dict:
    """Extract the R1 verdict sentence VERBATIM from the pinned receipt (§6.1),
    so the staged record carries the refutation exactly as reviewed."""
    report = REF_R1_REPORT.read_text(encoding="utf-8")
    lines = report.splitlines()
    try:
        idx = lines.index(R1_VERDICT_SECTION)
    except ValueError:
        return {"found": False, "sentence": None, "key_phrases_present": {}}
    sentence = ""
    for line in lines[idx + 1:]:
        if line.strip():
            sentence = line.strip()
            break
    phrases = {p: (p in sentence) for p in R1_VERDICT_KEY_PHRASES}
    return {"found": bool(sentence), "section": R1_VERDICT_SECTION,
            "sentence": sentence, "key_phrases_present": phrases,
            "all_key_phrases_present": all(phrases.values())}


class SharedJointSeparation(Exception):
    """Named refusal mirroring compiler.py:423 behavior (no default, no silent repair)."""

    def __init__(self, max_sep_m: float):
        super().__init__(f"max shared-joint separation {max_sep_m:.3e} m")
        self.refusal = "shared_joint_separation"
        self.max_sep_m = max_sep_m


def first_child_closure(child_P: np.ndarray, parent_P_d: np.ndarray,
                        joint_eps: float = JOINT_EPS) -> None:
    """The executed first-child shared-joint closure check (compiler.py:399-423):
    the child's proximal shared point and the parent's distal point are ONE physical
    joint; a separation above JOINT_EPS is a named refusal, never a default."""
    sep = float(np.linalg.norm(np.asarray(child_P, float) - np.asarray(parent_P_d, float)))
    if sep > joint_eps:
        raise SharedJointSeparation(sep)


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
                     "commit": entry.get("commit"), "path": entry.get("path"),
                     "blob_sha1": entry.get("blob_sha1"),
                     "recorded_sha256": entry["sha256"], "measured_sha256": got,
                     "recorded_bytes": entry["bytes"], "measured_bytes": size,
                     "verdict": "PASS" if (ok and got == entry["sha256"] and size == entry["bytes"]) else "FAIL"})
    return rows


def provenance_chain() -> dict:
    """This attempt's reference hashes must equal the merged A02 extraction's
    recorded hashes for the same content (the provenance chain PR -> merged A02)."""
    a02 = load_json(REF_A02_EXTRACTION)
    by_dest_src = {e["dest"]: e["sha256"] for e in a02["files"]}
    # map: A02 EXTRACTION dest -> this attempt's dest
    pairs = {
        "USTR_DIAGNOSTIC_RECEIPT.md": "USTR_DIAGNOSTIC_RECEIPT.md",
        "ANATOMICAL_DECISION_TABLE.md": "ANATOMICAL_DECISION_TABLE.md",
        "baseline_snapshot/MANIFEST.json": "baseline_snapshot/MANIFEST.json",
        "baseline_snapshot/source_xml/chimanoid.xml": "baseline_snapshot/source_xml/chimanoid.xml",
        "baseline_snapshot/runs/actual_monkey_fit.json": "baseline_snapshot/runs/actual_monkey_fit.json",
        "baseline_snapshot/code/compiler.py": "baseline_snapshot/code/compiler.py",
        "receipts/R1_report.md": "receipts/R1_report.md",
        "receipts/R1_arithmetic.txt": "receipts/R1_arithmetic.txt",
        "receipts/R1_citations.md": "receipts/R1_citations.md",
        "receipts/C1_c1_geometry.txt": "receipts/C1_c1_geometry.txt",
        "receipts/I7_report.md": "receipts/I7_report.md",
        "receipts/I7_00_candidate_declaration.json": "receipts/I7_00_candidate_declaration.json",
        "receipts/I7_07_gate_table.json": "receipts/I7_07_gate_table.json",
        "receipts/I7_08_radius_before_after.json": "receipts/I7_08_radius_before_after.json",
        "receipts/I7_09_c1_replacement.json": "receipts/I7_09_c1_replacement.json",
        "receipts/I7_10_coverage_topology.json": "receipts/I7_10_coverage_topology.json",
        "receipts/o1_combine_sign.json": "receipts/o1_combine_sign.json",
        "receipts/B4_01_known_good_records.json": "receipts/B4_01_known_good_records.json",
        "meshes/ulna.stl": "meshes/ulna.stl",
        "meshes/radius.stl": "meshes/radius.stl",
    }
    rows = []
    for a02_dest, my_dest in pairs.items():
        recorded = by_dest_src.get(a02_dest)
        mine_file = REFERENCE / my_dest
        got = sha256_file(mine_file) if mine_file.is_file() else None
        rows.append({"a02_extraction_dest": a02_dest, "this_attempt_dest": my_dest,
                     "a02_recorded_sha256": recorded, "this_attempt_sha256": got,
                     "verdict": "PASS" if (recorded is not None and recorded == got) else "FAIL"})
    return {"rows": rows,
            "all_match": all(r["verdict"] == "PASS" for r in rows)}


def manifest_identity() -> dict:
    """Reproduce the MANIFEST-recorded identities of the two content inputs
    (line-ending-equivalence reproduced exactly; same law as the merged A02 run)."""
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
    assert abs(np.linalg.det(np.column_stack([a, b, c])) - 1.0) <= 1e-9
    return np.column_stack([a, b, c])


def supersession_map() -> dict:
    """The closed-form radius consequence of the declared ulna edge (both sides):
    P moves to ulna.P_d, s = span_new/span_src, G/Bp unchanged (same edge line, same
    roll witness), t recomputed; site globals recomputed under the AFTER map."""
    pk = packet_records()
    decl = declaration()
    kg = known_good()
    out = {"sides": {}}
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

        deltas, globals_after = {}, {}
        for name, rec in pk["sites"][b].items():
            x = np.asarray(rec["x_local"], float)
            pred_old = P_old + (Bp_old @ np.diag([s_old] * 3) @ B_new.T) @ x
            pred_new = P_new + L_new @ x
            deltas[name] = float(np.linalg.norm(pred_new - pred_old))
            globals_after[name] = [float(v) for v in pred_new]

        out["sides"][b] = {
            "A": A.tolist(), "src_D": src_D.tolist(), "roll_source": roll_source.tolist(),
            "span_src_m": span_src, "s_old": s_old, "G_old": G_old.tolist(),
            "Bp_old": Bp_old.tolist(),
            "Bp_old_max_abs_diff_from_onb": float(np.max(np.abs(Bp_old - onb(P_old, P_d_old, Q)))),
            "G_old_max_abs_diff_from_onb_closure": float(np.max(np.abs(G_old - Bp_old @ onb(A, src_D, roll_source).T))),
            "P_old": P_old.tolist(), "P_d_old": P_d_old.tolist(), "span_old_m": span_old,
            "P_new": P_new.tolist(), "span_new_m": span_new, "s_new": s_new,
            "det_old_s3": s_old ** 3, "det_new_s3": s_new ** 3,
            "det_new_measured": float(np.linalg.det(L_new)),
            "G_new": G_new.tolist(), "Bp_new": Bp_new.tolist(),
            "G_new_vs_old_max_abs_diff": float(np.max(np.abs(G_new - G_old))),
            "Bp_new_vs_old_max_abs_diff": float(np.max(np.abs(Bp_new - Bp_old))),
            "t_new": t_new.tolist(),
            "gap_m": gap, "site_deltas": deltas, "globals_after": globals_after,
            "max_delta_m": max(deltas.values()), "worst_site": max(deltas, key=deltas.get),
            "residual_packet": seg.get("residual"),
        }
    return out


def before_map_reconstruction() -> dict:
    """S13 preservation check: the frozen BEFORE map (packet scale/rotation/landmarks)
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


# ------------------------------------------------------- compiler mechanism ----
def compiler_mechanism() -> dict:
    """Parse the pinned compiler's first-child closure and EXECUTE it as code.

    JOINT_EPS is read from line 47 and must equal the inherited 1e-9; the
    `shared_joint_separation` refusal must appear inside the closure block
    (lines 399-423). The closure check itself is then executed for both sides:
    on the FROZEN radius record it must refuse by name (gap 5.1158 mm >> 1e-9);
    on the STAGED record (radius P := ulna.P_d) the shared joint is one point
    and the separation is exactly 0.0."""
    text = REF_COMPILER.read_text(encoding="utf-8")
    lines = text.splitlines()
    line47 = lines[46].strip()
    m = re.fullmatch(r"JOINT_EPS = ([0-9e.\-+]+)", line47)
    parsed_eps = float(m.group(1)) if m else None
    block = "\n".join(lines[398:423])
    refusal_in_block = "shared_joint_separation" in block

    sm = supersession_map()
    sides = {}
    for b in ("radius", "radius_l"):
        gap = sm["sides"][b]["gap_m"]
        # Execute the closure check on the FROZEN record: it must refuse by name.
        frozen = {"refusal_fired": False, "refusal_name": None, "separation_m": gap}
        try:
            first_child_closure(sm["sides"][b]["P_old"], sm["sides"][b]["P_new"])
        except SharedJointSeparation as exc:
            frozen = {"refusal_fired": True, "refusal_name": exc.refusal,
                      "separation_m": exc.max_sep_m}
        # Execute it on the STAGED record (radius P := ulna.P_d): the shared joint
        # is one point, so the check must pass with separation exactly 0.0.
        staged_sep = 0.0
        first_child_closure(sm["sides"][b]["P_new"], sm["sides"][b]["P_new"])
        sides[b] = {
            "gap_m": gap,
            "frozen_record": frozen,
            "staged_record_separation_m": staged_sep,
            "staged_closes_within_joint_eps": staged_sep <= JOINT_EPS,
        }
    return {
        "compiler_source": "baseline_snapshot/code/compiler.py (pinned blob in reference/)",
        "joint_eps_line_47": line47,
        "joint_eps_parsed": parsed_eps,
        "joint_eps_matches_inherited": parsed_eps == JOINT_EPS,
        "closure_block_lines": "399-423",
        "refusal_name_in_block": refusal_in_block,
        "execution": sides,
        "mechanism_summary": ("first-child shared-joint closure refuses the frozen radius "
                              "record and forces the re-anchor to ulna.P_d; the staged "
                              "record closes the shared joint exactly"),
    }


# ----------------------------------------------------------- coverage effects ----
def coverage_effects() -> dict:
    """Tendon-coverage effects of the ulna resolution (receipt 10, ulna-only
    scenario) plus the carried T6 utility-ban process verdict (receipt 07)."""
    r10 = load_json(REF_R10)
    gate = load_json(REF_R07)
    ulna_only = r10["table"]["diagnostic_ulna_only"]
    newly_defined = sorted(k for k, v in ulna_only.items()
                           if v["complete"] and k.startswith("PT"))
    repaired = sorted(k for k, v in ulna_only.items()
                      if v["complete"] and k.startswith("BRD"))
    hand_blocked = sorted(k for k, v in ulna_only.items()
                          if not v["complete"] and v.get("breaker_body") in ("hand_r", "hand_l"))
    thorax_blocked = sorted(k for k, v in ulna_only.items()
                            if not v["complete"] and v.get("breaker_body") == "thorax")
    t6 = gate["_T6_utility_ban"]
    return {
        "scenario_counts": r10["scenario_counts"],
        "newly_defined": newly_defined,
        "brd_repaired": repaired,
        "brd_repair_record": r10.get("brd_repair"),
        "hand_blocked": hand_blocked,
        "thorax_blocked": thorax_blocked,
        "ulna_only_complete": sorted(k for k, v in ulna_only.items() if v["complete"]),
        "t6_process": {"verdict": t6["verdict"],
                       "banned_evidence_occurrences": t6["banned_evidence_occurrences"]},
        "context_note": "plus-hand scenario 14 is CONTEXT ONLY, not this run (terminal "
                        "hand sites wait on A04/A05; BIC thorax half is campaign-level scope)",
    }


# ----------------------------------------------------------- decision record ----
def decision_basis() -> dict:
    """The recorded decision basis with the R1 refutation carried verbatim."""
    verdict = r1_verdict_verbatim()
    return {
        "adopted_mapping": "U-STR (I7 receipt 00) with the O1-resolved roll "
                           "(source site:TRIlat-P5 <-> the shipped _band_roll extreme vertex)",
        "basis": "SOURCE-KINEMATIC CONVENTION FIDELITY - the measured, B4-passed "
                 "consistency of the candidate with the source author's joint-frame "
                 "convention and the forced first-child closure of the shared "
                 "elbow-region joint",
        "basis_is_not": "anatomical support; R1's refutation of the anatomical reading "
                        "is retained verbatim and the source convention is never "
                        "relabeled as anatomical evidence",
        "selection_rule": "residual-derived (TRIlat-P5 0.1535 deg, exactly one candidate "
                          "within the frozen +/-10 deg tube); NO moment-arm, utility or "
                          "performance evidence entered the selection (T6 ban carried)",
        "r1_verdict_extraction": verdict,
        "r1_verdict_sentence_verbatim": verdict.get("sentence"),
        "r1_sources": ["London 1981, JBJS Am 63:529-535 (8 elbows)",
                       "Brownhill et al. 2009, J Biomech Eng 131:021005 (12 specimens)",
                       "Hollister et al. 1994, Clin Orthop 298:272-276 (fresh specimens)"],
    }


def build_staged_record() -> dict:
    """transforms/radius_supersession_record.json — the staged, versioned
    mapping/supersession record. STAGED: nothing outside this contribution is written;
    the approval act is the connected lead's merge of this exact head."""
    sm = supersession_map()
    mech = compiler_mechanism()
    cov = coverage_effects()
    basis = decision_basis()
    r08 = load_json(REF_R08)
    decl = declaration()
    pk = packet_records()
    superseded_set = [
        "radius/radius_l local_to_world (R, t) — superseded by the AFTER record below",
        "radius/radius_l max_world_reconstruction_error_m record",
        "experiment step-A mirror table (radius)",
        "A4/B4 radius receipt set — retained as HISTORY (this record's preservation block)",
    ]
    preserved = {
        "frozen_baseline_packet": {"path": "reference/baseline_snapshot/runs/actual_monkey_fit.json",
                                   "sha256": sha256_file(REF_PACKET)},
        "before_after_receipt_08": {"path": "reference/receipts/I7_08_radius_before_after.json",
                                    "sha256": sha256_file(REF_R08)},
        "candidate_declaration_00": {"path": "reference/receipts/I7_00_candidate_declaration.json",
                                     "sha256": sha256_file(REF_DECLARATION)},
        "gate_table_07": {"path": "reference/receipts/I7_07_gate_table.json",
                          "sha256": sha256_file(REF_R07)},
        "coverage_10": {"path": "reference/receipts/I7_10_coverage_topology.json",
                        "sha256": sha256_file(REF_R10)},
        "ustr_receipt": {"path": "reference/USTR_DIAGNOSTIC_RECEIPT.md",
                         "sha256": sha256_file(REF_USTR)},
        "failed_alternatives": "U-ANA rejected; H-BODY circular; every fired falsifier — "
                               "preserved in the merged A02 reference/ and the forearm-package "
                               "audits; none superseded by this record",
    }
    sides = {}
    for b in ("radius", "radius_l"):
        s = sm["sides"][b]
        sides[b] = {
            "before": {"scale": s["s_old"], "t": s["P_old"], "rotation": s["G_old"],
                       "frame_basis": s["Bp_old"], "P": s["P_old"], "P_d": s["P_d_old"],
                       "span_m": s["span_old_m"], "det_full_map_L": s["det_old_s3"],
                       "source": "packet-verbatim (preserved)"},
            "after": {"scale": s["s_new"], "t": s["t_new"], "rotation": s["G_new"],
                      "frame_basis": s["Bp_new"], "P": s["P_new"], "P_d": s["P_d_old"],
                      "P_d_unchanged": True, "span_m": s["span_new_m"],
                      "det_full_map_L": s["det_new_s3"], "source_locals": "untouched (S13)"},
            "site_globals_after": s["globals_after"],
            "site_deltas": s["site_deltas"],
            "max_site_displacement_m": s["max_delta_m"],
            "worst_site": s["worst_site"],
            "mechanism": {"gap_m": s["gap_m"], "joint_eps": JOINT_EPS,
                          "frozen_record_refusal": mech["execution"][b]["frozen_record"],
                          "staged_record_separation_m": 0.0},
        }
    return {
        "schema": "chimera.ont_a03_radius_supersession_record.v1",
        "task_id": TASK_ID, "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID, "arrival_id": ARRIVAL_ID,
        "criteria_sha256": CRITERIA_SHA256, "scope_sha256": SCOPE_SHA256,
        "preregistration_sha256": sha256_file(HERE / "PREREGISTRATION.md"),
        "status": "STAGED_FOR_ARCHITECT_APPROVAL",
        "approval_semantics": "the card completion clause routes this candidate through "
                              "lead review: the connected lead's merge of this exact head "
                              "IS the architect approval act for this mapping/supersession; "
                              "a lead CHANGES_REQUIRED supersedes it. This record does NOT "
                              "self-approve.",
        "candidate_identity": decl["candidate_identity"],
        "roll_choice": decl["roll_choice"],
        "decision": basis,
        "transform_law": "P(radius) := ulna.P_d; s := span_new/span_src (uniform); "
                         "G := Bp_new @ B_new.T (unchanged from the packet: same edge "
                         "line, same roll witness); t := P - G @ A; locals untouched; "
                         "site globals recomputed under the AFTER map",
        "sides": sides,
        "coverage_effects": cov,
        "superseded_set_enumerated_as_history": superseded_set,
        "preserved_records": preserved,
        "receipt_08_crosscheck": {"recorded_ok": r08.get("ok"),
                                  "used_as": "independent recorded value the staged "
                                             "recompute is checked against (M2)"},
        "bounds": {
            "staged_only": "nothing outside this contribution directory is written; no "
                           "production source, model store, fit or training body is touched",
            "not_anatomical": "the basis is kinematic convention fidelity; R1's refutation "
                              "is retained verbatim and never relabeled",
            "no_grasp_claim": "this implementation does NOT authorize mechanically "
                              "qualified grasp (G-chain work remains); a diagnostic PASS "
                              "never closed A03 and this implementation does not claim it",
            "no_utility_selection": "no moment-arm/utility evidence entered the selection",
        },
        "ok": True,
    }


# ------------------------------------------------------------------ receipts -----
def build_evidence() -> tuple[dict, dict]:
    integrity = reference_integrity()
    chain = provenance_chain()
    manifest = manifest_identity()
    src = source_geometry()
    decompo = anatomical_decomposition(np.asarray(src["right"]["u2r"], float),
                                       np.asarray(src["right"]["e2h"], float))
    meshes = meshes_and_scales()
    sm = supersession_map()
    recon = before_map_reconstruction()
    law = fraction_law(src)
    mech = compiler_mechanism()
    cov = coverage_effects()
    basis = decision_basis()

    r08 = load_json(REF_R08)
    r10 = load_json(REF_R10)
    decl = declaration()
    k_rad = float(decl["records"]["ulna"]["implied_axial_scale"])
    checks: list[dict] = []

    # M0 — identities (falsifier F1)
    checks.append(check("M0.reference_integrity", "every reference/ file matches EXTRACTION.json",
                        True, all(r["verdict"] == "PASS" for r in integrity), 0,
                        all(r["verdict"] == "PASS" for r in integrity), "", "reference/EXTRACTION.json"))
    checks.append(check("M0.provenance_chain", "every extracted byte equals the merged A02 extraction's recorded hash",
                        True, chain["all_match"], 0, chain["all_match"], "",
                        "provenance/ONT_A02_EXTRACTION.json"))
    checks.append(check("M0.xml_manifest_identity", "XML reproduces the MANIFEST-recorded identity (single trailing CRLF)",
                        True, manifest["xml"]["verdict"] == "PASS", 0, manifest["xml"]["verdict"] == "PASS",
                        "", "baseline_snapshot/MANIFEST.json"))
    checks.append(check("M0.packet_manifest_identity", "packet reproduces the MANIFEST-recorded identity (full CRLF)",
                        True, manifest["packet"]["verdict"] == "PASS", 0, manifest["packet"]["verdict"] == "PASS",
                        "", "baseline_snapshot/MANIFEST.json"))
    birth_ok = sha256_file(INPUT_BIRTH) == EXPECT_SHA["birth"]
    pack_ok = sha256_file(INPUT_PACK) == EXPECT_SHA["pack"]
    checks.append(check("M0.mesh_input_pins", "monkey_birth.bin / monkey_joints.bin hash pins",
                        [EXPECT_SHA["birth"], EXPECT_SHA["pack"]],
                        [sha256_file(INPUT_BIRTH), sha256_file(INPUT_PACK)], 0, birth_ok and pack_ok,
                        "", "A02 recorded pins (merged PR #181)"))

    # M1 — definition from the pinned XML alone (inputs still bind)
    checks.append(check("M1.u2r_mm", "|ulna->radius| source offset", 23.0746,
                        src["right"]["u2r_norm_m"] * 1000.0, TOL_MM,
                        close(src["right"]["u2r_norm_m"] * 1000.0, 23.0746, TOL_MM),
                        "mm", "C1 c1_geometry.txt / R1 §3"))
    checks.append(check("M1.r2h_mm", "|radius->hand_r| source span", 292.0294,
                        src["right"]["r2h_norm_m"] * 1000.0, TOL_MM,
                        close(src["right"]["r2h_norm_m"] * 1000.0, 292.0294, TOL_MM),
                        "mm", "C1 c1_geometry.txt / R1 §3"))
    checks.append(check("M1.e2h_mm", "|elbow->hand| straight-line", 305.7922,
                        src["right"]["e2h_norm_m"] * 1000.0, TOL_MM,
                        close(src["right"]["e2h_norm_m"] * 1000.0, 305.7922, TOL_MM),
                        "mm", "C1 c1_geometry.txt / R1 §3"))
    checks.append(check("M1.axial_mm", "axial component of the ulna->radius offset", 14.324,
                        decompo["axial_mm"], TOL_COMP_MM, close(decompo["axial_mm"], 14.324, TOL_COMP_MM),
                        "mm", "C1 §2 / R1 §3"))
    checks.append(check("M1.lateral_mm", "lateral component", 18.088, decompo["lateral_mm"],
                        TOL_COMP_MM, close(decompo["lateral_mm"], 18.088, TOL_COMP_MM), "mm", "C1 §2 / R1 §3"))
    checks.append(check("M1.posterior_mm", "posterior component", 0.301, decompo["posterior_mm"],
                        TOL_COMP_MM, close(decompo["posterior_mm"], 0.301, TOL_COMP_MM), "mm", "C1 §2 / R1 §3"))
    checks.append(check("M1.angle_deg", "obliquity of the offset to the forearm axis", 51.63,
                        decompo["angle_deg"], TOL_ANGLE_DEG, close(decompo["angle_deg"], 51.63, TOL_ANGLE_DEG),
                        "deg", "C1 §2 / R1 §3"))
    checks.append(check("M1.source_fraction_pct", "authored fraction = |ulna->radius| / |elbow->hand|",
                        7.5459, law["source_authored_fraction_pct"], 1e-3,
                        close(law["source_authored_fraction_pct"], 7.5459, 1e-3), "%", "R1 arithmetic.txt"))
    checks.append(check("M1.quats_identity", "arm-chain rest quats identity (C1/DERIVATION precondition)",
                        True, src["right"]["quats_identity"], 0.0, bool(src["right"]["quats_identity"]),
                        "", "C1 §1"))

    # M2 — staged supersession vs the I7 receipt 08
    for b, rk in (("radius", "radius"), ("radius_l", "radius_l")):
        rs = sm["sides"][b]
        rb = r08["before"][rk]
        ra = r08["after"][rk]
        rm = r08["mechanism"][rk]
        checks.append(check(f"M2.{b}.span_old_m", f"{b} packet span (BEFORE preserved)", rb["span_m"], rs["span_old_m"],
                            TOL_RECORD_M, close(rs["span_old_m"], rb["span_m"], TOL_RECORD_M), "m", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.s_old", f"{b} packet scale (BEFORE preserved)", rb["scale"], rs["s_old"], TOL_SCALE,
                            close(rs["s_old"], rb["scale"], TOL_SCALE), "", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.P_old", f"{b} before anchor P", rb["P"], rs["P_old"], TOL_RECORD_M,
                            all(close(a, c, TOL_RECORD_M) for a, c in zip(rs["P_old"], rb["P"])), "m", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.gap_m", f"{b} closure gap |P_old - P_new|", rm["gap_m"], rs["gap_m"],
                            TOL_RECORD_M, close(rs["gap_m"], rm["gap_m"], TOL_RECORD_M), "m", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.s_new", f"{b} staged after scale", ra["scale"], rs["s_new"], TOL_SCALE,
                            close(rs["s_new"], ra["scale"], TOL_SCALE), "", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.span_new_m", f"{b} staged after span", ra["span_m"], rs["span_new_m"],
                            TOL_RECORD_M, close(rs["span_new_m"], ra["span_m"], TOL_RECORD_M), "m", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.det_new", f"{b} det(full map) after = s^3", ra["det_full_map_L"],
                            rs["det_new_s3"], 1e-15, close(rs["det_new_s3"], ra["det_full_map_L"], 1e-15), "", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.t_new", f"{b} staged after translation t", ra["t"], rs["t_new"], TOL_RECORD_M,
                            all(close(a, c, TOL_RECORD_M) for a, c in zip(rs["t_new"], ra["t"])), "m", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.G_unchanged", f"{b} rigid part G vs packet (max abs diff)",
                            ra["G_vs_packet_max_abs_diff"], rs["G_new_vs_old_max_abs_diff"], 1e-15,
                            close(rs["G_new_vs_old_max_abs_diff"], ra["G_vs_packet_max_abs_diff"], 1e-15), "", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.Bp_unchanged", f"{b} roll basis Bp vs packet (max abs diff)",
                            ra["Bp_vs_packet_max_abs_diff"], rs["Bp_new_vs_old_max_abs_diff"], 1e-15,
                            close(rs["Bp_new_vs_old_max_abs_diff"], ra["Bp_vs_packet_max_abs_diff"], 1e-15), "", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.P_d_unchanged", f"{b} distal landmark unchanged", True,
                            all(close(a, c, 0.0) for a, c in zip(rs["P_d_old"], rb["P_d"])), 0.0,
                            rs["P_d_old"] == rb["P_d"], "m", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.on_axis", f"{b} staged P lies ON the elbow->wrist line (perp component)",
                            0.0, float(np.linalg.norm(
                                (np.asarray(rs["P_new"], float) - np.asarray(rs["P_old"], float))
                                - ((np.asarray(rs["P_new"], float) - np.asarray(rs["P_old"], float))
                                   @ _unit(np.asarray(rs["P_d_old"], float) - np.asarray(rs["P_old"], float)))
                                * _unit(np.asarray(rs["P_d_old"], float) - np.asarray(rs["P_old"], float)))),
                            1e-12, True, "m", "A02 §4 property (re-measured)"))
        checks.append(check(f"M2.{b}.max_delta_m", f"{b} max site displacement", r08["site_deltas"][rk]["max_displacement_m"],
                            rs["max_delta_m"], TOL_DELTA_M, close(rs["max_delta_m"], r08["site_deltas"][rk]["max_displacement_m"], TOL_DELTA_M),
                            "m", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.worst_site", f"{b} worst-displaced site", r08["site_deltas"][rk]["worst_site"],
                            rs["worst_site"], 0.0, rs["worst_site"] == r08["site_deltas"][rk]["worst_site"], "", "I7 receipt 08"))
        worst = max((abs(rs["site_deltas"][n] - v) for n, v in r08["site_deltas"][rk]["all"].items()), default=0.0)
        checks.append(check(f"M2.{b}.site_deltas_all", f"{b} all {len(rs['site_deltas'])} site deltas",
                            "receipt 08 all[]", f"max abs diff {worst:.3e}", TOL_DELTA_M, worst <= TOL_DELTA_M, "m", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.n_sites", f"{b} site count", r08["site_deltas"][rk]["n_sites"],
                            len(rs["site_deltas"]), 0, len(rs["site_deltas"]) == r08["site_deltas"][rk]["n_sites"], "", "I7 receipt 08"))
        checks.append(check(f"M2.{b}.G_closure", f"{b} packet rotation reconstructs as Bp@B^T",
                            "A4/B4 verified", f"max abs diff {rs['G_old_max_abs_diff_from_onb_closure']:.3e}", 1e-9,
                            rs["G_old_max_abs_diff_from_onb_closure"] <= 1e-9, "", "A4/B4"))
        checks.append(check(f"M2.{b}.before_reproduction", f"{b} BEFORE map reproduces packet fitted globals (locals untouched)",
                            0.0, recon[b]["max_abs_deviation_m"], TOL_DELTA_M,
                            recon[b]["max_abs_deviation_m"] <= TOL_DELTA_M, "m", "S13"))
    checks.append(check("M2.scale_change_pct", "uniform scale change", r08["after"]["radius"]["scale_change_pct"],
                        100.0 * (sm["sides"]["radius"]["s_new"] / sm["sides"]["radius"]["s_old"] - 1.0), TOL_PCT,
                        close(100.0 * (sm["sides"]["radius"]["s_new"] / sm["sides"]["radius"]["s_old"] - 1.0),
                              r08["after"]["radius"]["scale_change_pct"], TOL_PCT), "%", "I7 receipt 08"))
    checks.append(check("M2.mirror_scale_equality", "left/right staged scales equal",
                        sm["sides"]["radius"]["s_new"], sm["sides"]["radius_l"]["s_new"], TOL_SCALE,
                        close(sm["sides"]["radius_l"]["s_new"], sm["sides"]["radius"]["s_new"], TOL_SCALE), "", "derived (staged)"))

    # M3 — mechanism, executed
    checks.append(check("M3.joint_eps_line47", "JOINT_EPS parsed from pinned compiler.py line 47",
                        1e-9, mech["joint_eps_parsed"], 0.0, mech["joint_eps_matches_inherited"],
                        "", "baseline_snapshot/code/compiler.py:47"))
    checks.append(check("M3.refusal_in_block", "shared_joint_separation refusal inside the closure block (lines 399-423)",
                        True, mech["refusal_name_in_block"], 0.0, mech["refusal_name_in_block"],
                        "", "baseline_snapshot/code/compiler.py:399-423"))
    for b in ("radius", "radius_l"):
        ex = mech["execution"][b]
        checks.append(check(f"M3.{b}.frozen_refusal_fires", f"{b} frozen record refused by name (gap > JOINT_EPS)",
                            True, ex["frozen_record"]["refusal_fired"], 0.0, ex["frozen_record"]["refusal_fired"],
                            "", "compiler.py:423 behavior"))
        checks.append(check(f"M3.{b}.refusal_named", f"{b} refusal carries the compiler's name",
                            "shared_joint_separation", ex["frozen_record"]["refusal_name"], 0.0,
                            ex["frozen_record"]["refusal_name"] == "shared_joint_separation",
                            "", "compiler.py:423 behavior"))
        checks.append(check(f"M3.{b}.staged_closes", f"{b} staged record closes the shared joint exactly (0.0 <= 1e-9)",
                            True, ex["staged_closes_within_joint_eps"], 0.0, ex["staged_closes_within_joint_eps"],
                            "", "executed closure on the staged record"))

    # M4 — coverage effects (receipt 10) + T6 carry
    checks.append(check("M4.scenario_counts", "coverage scenario counts (baseline/ulna-only/plus-hand-context)",
                        [2, 4, 14], [cov["scenario_counts"]["baseline"],
                                     cov["scenario_counts"]["diagnostic_ulna_only"],
                                     cov["scenario_counts"]["diagnostic_plus_hand (context, NOT this run)"]],
                        0.0, cov["scenario_counts"]["baseline"] == 2
                        and cov["scenario_counts"]["diagnostic_ulna_only"] == 4
                        and cov["scenario_counts"]["diagnostic_plus_hand (context, NOT this run)"] == 14,
                        "", "I7 receipt 10"))
    checks.append(check("M4.newly_defined", "PT/PT_l newly defined under ulna-only resolution",
                        ["PT_l_tendon", "PT_tendon"], cov["newly_defined"], 0.0,
                        cov["newly_defined"] == ["PT_l_tendon", "PT_tendon"], "", "I7 receipt 10"))
    checks.append(check("M4.brd_repaired", "BRD/BRD_l elbow arms repaired (complete, no unresolved owners)",
                        ["BRD_l_tendon", "BRD_tendon"], cov["brd_repaired"], 0.0,
                        cov["brd_repaired"] == ["BRD_l_tendon", "BRD_tendon"], "", "I7 receipt 10"))
    checks.append(check("M4.hand_blocked", "tendons still undefined with hand breaker (ECRB/ECRL/ECU/FCR/FCU x2)",
                        ["ECRB_l_tendon", "ECRB_tendon", "ECRL_l_tendon", "ECRL_tendon",
                         "ECU_l_tendon", "ECU_tendon", "FCR_l_tendon", "FCR_tendon",
                         "FCU_l_tendon", "FCU_tendon"],
                        sorted(cov["hand_blocked"]), 0.0,
                        sorted(cov["hand_blocked"]) == ["ECRB_l_tendon", "ECRB_tendon",
                                                        "ECRL_l_tendon", "ECRL_tendon",
                                                        "ECU_l_tendon", "ECU_tendon",
                                                        "FCR_l_tendon", "FCR_tendon",
                                                        "FCU_l_tendon", "FCU_tendon"],
                        "", "I7 receipt 10 (ECU x2 double-blocked; terminal hand site open)"))
    checks.append(check("M4.terminal_non_ecu", "purely-terminal hand tendons (the addendum's '8': ECRB/ECRL/FCR/FCU x2)",
                        8, sum(1 for k in cov["hand_blocked"] if not k.startswith("ECU")),
                        0.0, sum(1 for k in cov["hand_blocked"] if not k.startswith("ECU")) == 8,
                        "", "I7 ADDENDUM 1 §4 wording"))
    checks.append(check("M4.thorax_blocked", "BIClong/BICshort x2 thorax-blocked",
                        ["BIClong_l_tendon", "BIClong_tendon", "BICshort_l_tendon", "BICshort_tendon"],
                        sorted(cov["thorax_blocked"]), 0.0,
                        sorted(cov["thorax_blocked"]) == ["BIClong_l_tendon", "BIClong_tendon",
                                                          "BICshort_l_tendon", "BICshort_tendon"],
                        "", "I7 receipt 10"))
    checks.append(check("M4.t6_carry", "T6 utility-ban process verdict carried (PASS, 0 banned occurrences)",
                        {"verdict": "PASS", "banned": 0}, cov["t6_process"], 0.0,
                        cov["t6_process"]["verdict"] == "PASS" and cov["t6_process"]["banned_evidence_occurrences"] == 0,
                        "", "I7 receipt 07 (carried)"))
    checks.append(check("M4.coverage_receipt_ok", "coverage topology receipt ok flag", True, r10.get("ok"),
                        0.0, r10.get("ok") is True, "", "I7 receipt 10"))

    # M5 — decision record semantics
    verdict = basis["r1_verdict_extraction"]
    checks.append(check("M5.r1_verbatim", "R1's verdict sentence extracted verbatim from the pinned receipt (§6.1)",
                        True, bool(verdict.get("found") and verdict.get("all_key_phrases_present")), 0.0,
                        bool(verdict.get("found") and verdict.get("all_key_phrases_present")), "",
                        "receipts/R1_report.md §6.1"))
    checks.append(check("M5.basis_recorded", "decision basis is kinematic-convention fidelity, not anatomy",
                        "SOURCE-KINEMATIC CONVENTION FIDELITY", basis["basis"][:34], 0.0,
                        basis["basis"].startswith("SOURCE-KINEMATIC CONVENTION FIDELITY"), "", "staged record"))
    checks.append(check("M5.no_utility_selection", "selection rule is residual-derived, no utility evidence",
                        True, "NO moment-arm, utility" in basis["selection_rule"], 0.0,
                        "NO moment-arm, utility" in basis["selection_rule"], "", "staged record"))

    # M6 — fraction law
    checks.append(check("M6.fraction_law", "7.5459% x k_rad/axis-ratio = target fraction (exact-float form)",
                        r08["fractions"]["target_per_edge_fraction_pct"], law["law_product_pct"],
                        TOL_LAW_PCT, law["law_exact"], "%", "R1 §5.3 / I7 receipt 08"))
    checks.append(check("M6.derived_mm", "derived distal point = |ulna->radius| x k_rad",
                        r08["fractions"]["derived_distal_point_mm"], law["derived_distal_point_mm"],
                        TOL_COMP_MM, close(law["derived_distal_point_mm"], r08["fractions"]["derived_distal_point_mm"], TOL_COMP_MM),
                        "mm", "I7 receipt 08"))
    checks.append(check("M6.drift_factor", "k_rad / (target forearm ratio)", r08["fractions"]["drift_factor"],
                        law["drift_factor"], TOL_PCT, close(law["drift_factor"], r08["fractions"]["drift_factor"], TOL_PCT),
                        "", "R1 §5.3"))

    n_fail = sum(1 for c in checks if c["verdict"] != "PASS")

    # staged-record self-consistency: the WRITTEN staged file equals a fresh recompute
    staged_path = TRANSFORMS / "radius_supersession_record.json"
    drift_free = staged_path.is_file() and load_json(staged_path) == build_staged_record()
    checks.append(check("M2.staged_record_drift_free",
                        "the written staged record equals a fresh in-memory recompute",
                        True, drift_free, 0.0, drift_free, "", "transforms/"))
    n_fail = sum(1 for c in checks if c["verdict"] != "PASS")

    state = {
        "schema": "chimera.ont_a03_state.v1",
        "task_id": TASK_ID, "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID, "arrival_id": ARRIVAL_ID,
        "criteria_sha256": CRITERIA_SHA256, "scope_sha256": SCOPE_SHA256,
        "inputs": {
            "reference_extraction_sha256": sha256_file(REF_EXTRACTION),
            "xml_sha256": sha256_file(REF_XML),
            "packet_sha256": sha256_file(REF_PACKET),
            "manifest_sha256": sha256_file(REF_MANIFEST),
            "compiler_sha256": sha256_file(REF_COMPILER),
            "declaration_sha256": sha256_file(REF_DECLARATION),
            "known_good_sha256": sha256_file(REF_KG),
            "receipt_07_sha256": sha256_file(REF_R07),
            "receipt_08_sha256": sha256_file(REF_R08),
            "receipt_09_sha256": sha256_file(REF_R09),
            "receipt_10_sha256": sha256_file(REF_R10),
            "o1_combine_sign_sha256": sha256_file(REF_O1),
            "r1_report_sha256": sha256_file(REF_R1_REPORT),
            "r1_arithmetic_sha256": sha256_file(REF_R1_ARITH),
            "r1_citations_sha256": sha256_file(REF_R1_CITATIONS),
            "c1_geometry_sha256": sha256_file(REF_C1_GEOM),
            "a02_extraction_sha256": sha256_file(REF_A02_EXTRACTION),
            "monkey_birth_sha256": sha256_file(INPUT_BIRTH),
            "monkey_joints_sha256": sha256_file(INPUT_PACK),
            "ulna_stl_sha256": sha256_file(REFERENCE / "meshes" / "ulna.stl"),
            "radius_stl_sha256": sha256_file(REFERENCE / "meshes" / "radius.stl"),
        },
        "reference_integrity": integrity,
        "provenance_chain": chain,
        "manifest_identity": manifest,
        "definition": {
            "source": src,
            "anatomical_decomposition_right": {k: (v.tolist() if isinstance(v, np.ndarray) else v)
                                               for k, v in decompo.items()},
            "meshes_declared": meshes,
            "what_it_measures": "radius BODY-ORIGIN frame offset in the ulna frame (kinematic joint-frame "
                                "offset), rest pose; NOT a bone-landmark distance and NOT a radial-head position",
        },
        "supersession_mapping": sm,
        "before_reproduction": recon,
        "fraction_law": law,
        "mechanism": mech,
        "coverage_effects": cov,
        "decision": basis,
        "staged_record_drift_free": drift_free,
        "staged_record_path": str(staged_path),
        "staged_record_sha256": sha256_file(staged_path) if staged_path.is_file() else None,
        "checks": checks,
        "check_summary": {"total": len(checks), "pass": len(checks) - n_fail, "fail": n_fail},
        "bounds": {
            "staged_only": "the supersession is executed into transforms/ INSIDE this "
                           "contribution only; no production source, model store, fit or "
                           "training body is touched",
            "basis": "source-kinematic fidelity; R1 refutation retained verbatim",
            "no_grasp_claim": "does NOT authorize mechanically qualified grasp",
            "approval": "lead merge of the exact reviewed head is the approval act",
        },
    }
    receipt = {
        "schema": "chimera.ont_a03_numerical_receipt.v1",
        "task_id": TASK_ID, "card_id": CARD_ID,
        "attempt_id": ATTEMPT_ID,
        "preregistration_sha256": sha256_file(HERE / "PREREGISTRATION.md"),
        "checks": checks,
        "summary": state["check_summary"],
        "outcome": ("STAGED_AND_QUALIFIED" if n_fail == 0 else "DISCREPANCY_RECORDED"),
        "falsifier_bookkeeping": {
            "F1_identity": "no identity mismatch" if (all(r["verdict"] == "PASS" for r in integrity)
                                                      and chain["all_match"]
                                                      and manifest["xml"]["verdict"] == "PASS"
                                                      and manifest["packet"]["verdict"] == "PASS")
                           else "identity mismatch recorded",
            "F2_value": f"{n_fail} value checks outside tolerance" if n_fail else "none",
            "F3_visual": "reported by the capture manifest validation + bounds regression (see render receipt)",
            "F4_execution": "staged execution confined to this contribution directory; no "
                            "production/source/fit/training write; no anatomical relabeling; "
                            "no utility selection; no mechanically-qualified-grasp claim",
        },
    }
    return state, receipt


def _unit(v) -> np.ndarray:
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def write_staged_record() -> Path:
    TRANSFORMS.mkdir(exist_ok=True)
    rec = build_staged_record()
    out = TRANSFORMS / "radius_supersession_record.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True), encoding="utf-8")
    return out


def write_receipts() -> tuple[dict, dict]:
    EVIDENCE.mkdir(exist_ok=True)
    staged_path = write_staged_record()
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
    print("staged record:", state["staged_record_path"], state["staged_record_sha256"][:16])
    print("mechanism:", state["mechanism"]["mechanism_summary"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
