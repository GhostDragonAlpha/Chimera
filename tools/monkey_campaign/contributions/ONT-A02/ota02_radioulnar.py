"""ONT-A02 task-owned verifier: radioulnar definition, B4 result binding, and the
before/after radius consequence, re-derived from pins.

Reconciliation-first card. The historical evidence (O1 roll sign at c3255f74,
R1 radioulnar refutation at d02af013, isolated U-STR B4 diagnostic at f1023853)
stands as pinned history. This module RE-DERIVES the numerical content this card
must present, with its own implementation, from byte-pinned inputs
(reference/EXTRACTION.json), and cross-checks every number against the pinned
receipts under the FROZEN tolerances in PREREGISTRATION.md:

  evidence/state_snapshot.json    (input identities + presented state)
  evidence/numerical_receipt.json (recomputed vs receipt, verdicts, outcome)

Probes (PREREGISTRATION):
  P1 source radioulnar identity (C01 frames/units/correspondence)
  P2 owner discrimination (wrong owners must NOT reproduce the offset)
  P3 target before/after map (closed form, both sides + mirror)
  P4 closure mechanism (gap >> JOINT_EPS -> refusal fires)
  P5 C01 round-trip/handedness/landmark oracles + packet site reproduction
  P6 C16 coverage topology from XML ownership (three scenarios)
  P7 R1 drift law + retained anatomical refutation
  (P8 is the visual capture: ota02_render_views.py)

Honesty: CPU-only, deterministic, no GPU/network/native run; nothing is executed
against any store; the after-map is a closed-form diagnostic consequence ONLY,
unauthorized and unexecuted as a production supersession. Run with `python -B`.
"""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
EVIDENCE = HERE / "evidence"

# Pinned read-only inputs in the source worktree (identities asserted before use).
INPUT_BIRTH = Path(r"E:/PythonChimera/Saved/meshes/monkey_birth.bin")
INPUT_PACK = Path(r"E:/PythonChimera/Saved/meshes/monkey_joints.bin")
INPUT_ULNA_STL = Path(r"E:/PythonChimera/vendor/myo_sim/meshes/ulna.stl")
# A01 EXPECT_SHA (OTA01 pins; the same physical target inputs).
EXPECT_SHA = {
    "birth": "550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c",
    "pack": "74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662",
}

PINS = {
    "chimanoid_xml": "f1023853:forearm_package/baseline_snapshot/source_xml/chimanoid.xml",
    "packet": "f1023853:forearm_package/baseline_snapshot/runs/actual_monkey_fit.json",
    "i7_candidate_declaration": "f1023853:forearm_package/audits/I7_ustr_diagnostic/"
                                "receipts/00_candidate_declaration.json",
    "i7_gate_table": "f1023853:forearm_package/audits/I7_ustr_diagnostic/receipts/"
                     "07_gate_table.json",
    "i7_radius_before_after": "f1023853:forearm_package/audits/I7_ustr_diagnostic/"
                              "receipts/08_radius_before_after.json",
    "i7_coverage_topology": "f1023853:forearm_package/audits/I7_ustr_diagnostic/"
                            "receipts/10_coverage_topology.json",
    "b4_known_good": "f1023853:forearm_package/audits/B4_correspondence_challenge/"
                     "receipts/01_known_good_records.json",
    "o1_source_split": "c3255f74:forearm_package/audits/O1_ulna_orientation/receipts/"
                       "o1_source_split.json",
    "o1_combine_sign": "c3255f74:forearm_package/audits/O1_ulna_orientation/receipts/"
                       "o1_combine_sign.json",
    "r1_arithmetic": "d02af013:forearm_package/audits/R1_radioulnar_evidence/receipts/"
                     "arithmetic.txt",
    "r1_report": "d02af013:forearm_package/audits/R1_radioulnar_evidence/report.md",
    "o1_report": "c3255f74:forearm_package/audits/O1_ulna_orientation/report.md",
    "ustr_receipt_addendum": "f1023853:forearm_package/USTR_DIAGNOSTIC_RECEIPT.md",
}

# ---- FROZEN tolerances (PREREGISTRATION.md; frozen before any probe ran). ----
TOL_LANDMARK_M = 1e-12        # XML-derived origins vs declared source landmarks
TOL_MM_COARSE = 5e-4          # mm-scale scalar reproductions (spans, offsets)
TOL_MM_FINE = 1e-3            # coarser mm reproductions (source chains)
TOL_UNITLESS = 1e-12          # scale/det/frac/mirror-unitless reproductions
TOL_SCALE_REL = 5e-15         # s_after receipt reproduction (exact-float region)
TOL_PCT = 5e-13               # scale_change_pct reproduction
TOL_ORTH = 1e-12              # ONB det, G-difference, L = s*G
TOL_ROUNDTRIP = 1e-12         # L^-1 L = I, landmark map oracles
TOL_RECON_M = 1e-6            # protocol RECON_TOL_M (packet site reproduction)
TOL_MIRROR_M = 1e-9           # left/right mirror agreement (vectors)
TOL_DRIFT_PTS = 1e-6          # R1 5.3 drift-law consistency
TOL_DERIVED_GAP_M = 1e-11     # closed-form derived point vs declared-anchor gap
JOINT_EPS = 1e-9              # compiler.py:47 shared-joint closure (protocol value)
K_RADIUS = 0.22170679566544982  # the known-good radius edge scale (packet/declaration)

# The 16-tendon grasp set is DEFINED by the pinned receipt 10 table keys (the
# I7/B2 coverage contract); this module re-derives each row's content from XML.
GRASP_TENDONS_RIGHT = ["ECRB_tendon", "ECRL_tendon", "ECU_tendon", "FCR_tendon",
                       "FCU_tendon", "PT_tendon", "BIClong_tendon", "BICshort_tendon",
                       "BRD_tendon"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def load_json(rel: str):
    return json.loads((REFERENCE / rel).read_text(encoding="utf-8"))


def _quat_rotmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


# ------------------------------------------------------------ XML walk ----
def xml_world():
    """Rest-pose global body origins and site globals, site/joint owners and
    tendon paths from the pinned chimanoid.xml (live elements only; ElementTree
    drops XML comments, matching the intake law)."""
    root = ET.parse(str(REFERENCE / "chimanoid.xml")).getroot()
    bodies = {}
    site_owner = {}
    site_global = {}
    joint_owner = {}

    def walk(elem, parent_world, parent_rot, parent_name):
        name = elem.get("name")
        pos = np.array([float(v) for v in (elem.get("pos") or "0 0 0").split()])
        quat = np.array([float(v) for v in (elem.get("quat") or "1 0 0 0").split()])
        rot = parent_rot @ _quat_rotmat(quat)
        world = parent_world + parent_rot @ pos
        bodies[name] = {"pos_global": world, "pos_local": pos,
                        "parent": parent_name, "rot": rot}
        for s in elem.findall("site"):
            nm = s.get("name")
            if nm:
                site_owner[nm] = name
                sp = np.array([float(v) for v in (s.get("pos") or "0 0 0").split()])
                site_global[nm] = world + rot @ sp
        for j in elem.findall("joint"):
            if j.get("name"):
                joint_owner[j.get("name")] = name
        for child in elem.findall("body"):
            walk(child, world, rot, name)

    wb = root.find("worldbody")
    for b in wb.findall("body"):
        walk(b, np.zeros(3), np.eye(3), None)

    tendon_paths = {}
    for sp in root.find("tendon").findall("spatial"):
        tendon_paths[sp.get("name")] = [s.get("site")
                                        for s in sp.findall("site") if s.get("site")]
    return bodies, site_owner, joint_owner, tendon_paths, site_global


def onb(p0, p1, q):
    """DERIVATION 5.1 ONB construction law (own implementation of the pinned
    compiler.onb_from_points procedure): first basis vector along p0->p1, roll
    fixed by the projected witness q, right-handed."""
    a = unit(np.asarray(p1, float) - np.asarray(p0, float))
    t = np.asarray(q, float) - np.asarray(p0, float)
    t = t - a * (a @ t)
    n = float(np.linalg.norm(t))
    if n < 1e-9:
        raise ValueError("axis_parallel_roll")
    b = t / n
    c = np.cross(a, b)
    B = np.column_stack([a, b, c])
    assert abs(np.linalg.det(B) - 1.0) <= TOL_ORTH
    return B


def target_joints():
    """elbow_R/wrist_R (+L twins) from the hash-pinned target pack (A01 loader)."""
    sys.path.insert(0, str(REFERENCE))
    from mesh_target_o1 import MonkeyTarget  # hash-pinned copy of O1's loader
    mt = MonkeyTarget(birth_path=str(INPUT_BIRTH), pack_path=str(INPUT_PACK))
    assert mt.birth_sha.lower() == EXPECT_SHA["birth"], mt.birth_sha
    assert mt.pack_sha.lower() == EXPECT_SHA["pack"], mt.pack_sha
    joints = {n: mt.joint_pos(n) for n in
              ("elbow_R", "wrist_R", "elbow_L", "wrist_L")}
    return joints


# ------------------------------------------------------- P1/P2: source ----
def probe_radioulnar_source(bodies, site_global, declared):
    """P1 radioulnar identity from raw XML; P2 wrong-owner discrimination."""
    ulna = bodies["ulna"]["pos_global"]
    radius = bodies["radius"]["pos_global"]
    hand_r = bodies["hand_r"]["pos_global"]
    humerus = bodies["humerus"]["pos_global"]

    # C01 owner/frame binding: XML-derived origins must equal the declared
    # candidate's source landmarks (ulna.prox source = ulna origin, ulna.dist
    # source = radius origin, ulna.roll source = TRIlat-P5 global).
    dec = declared["records"]["ulna"]["landmarks"]
    d_ulna = float(np.linalg.norm(ulna - np.array(dec["prox"]["source"])))
    d_radius = float(np.linalg.norm(radius - np.array(dec["dist"]["source"])))
    d_roll = float(np.linalg.norm(site_global["TRIlat-P5"]
                                  - np.array(dec["roll"]["source"])))

    off_ulna_frame = radius - ulna           # the authored radioulnar offset
    src_off_mm = float(np.linalg.norm(off_ulna_frame)) * 1000.0
    src_forearm_mm = float(np.linalg.norm(hand_r - ulna)) * 1000.0
    src_radius_edge_mm = float(np.linalg.norm(hand_r - radius)) * 1000.0
    frac_pct = 100.0 * src_off_mm / src_forearm_mm
    axis = unit(hand_r - ulna)
    axial_mm = float(off_ulna_frame @ axis) * 1000.0
    obliq_deg = float(np.degrees(np.arccos(
        min(1.0, abs(axial_mm) / src_off_mm))))
    lat_mm = float(np.sqrt(max(0.0, src_off_mm ** 2 - axial_mm ** 2)))

    # P2 wrong-owner discrimination: these must NOT reproduce src_off_mm.
    wrong = {
        "humerus_to_radius_origin_mm": float(np.linalg.norm(radius - humerus)) * 1000.0,
        "ulna_origin_to_hand_r_mm": src_forearm_mm,
        "radius_origin_to_hand_r_mm": src_radius_edge_mm,
        "hand_r_local_minus_radius_local_mm":
            float(np.linalg.norm(bodies["hand_r"]["pos_local"]
                                 - bodies["radius"]["pos_local"])) * 1000.0,
    }
    wrong_match = {k: bool(abs(v - src_off_mm) <= TOL_MM_COARSE)
                   for k, v in wrong.items()}

    probe = {
        "ulna_origin_m": ulna.tolist(),
        "radius_origin_m": radius.tolist(),
        "hand_r_origin_m": hand_r.tolist(),
        "offset_vector_ulna_frame_m": off_ulna_frame.tolist(),
        "offset_norm_mm": src_off_mm,
        "source_forearm_ulna_to_hand_mm": src_forearm_mm,
        "source_radius_edge_radius_to_hand_mm": src_radius_edge_mm,
        "authored_fraction_pct": frac_pct,
        "axial_component_mm": abs(axial_mm),
        "lateral_component_mm": lat_mm,
        "obliquity_deg": obliq_deg,
        "declared_source_binding_max_diff_m": max(d_ulna, d_radius, d_roll),
        "declared_source_binding_ok": bool(max(d_ulna, d_radius,
                                               d_roll) <= TOL_LANDMARK_M),
        "wrong_owner_norms_mm": wrong,
        "wrong_owner_reproductions": wrong_match,
        "receipt_values_mm": {"offset": 23.0746, "forearm": 305.7922,
                              "radius_edge": 292.0294},
        "diff_offset_mm": src_off_mm - 23.0746,
        "diff_forearm_mm": src_forearm_mm - 305.7922,
        "diff_radius_edge_mm": src_radius_edge_mm - 292.0294,
    }
    probe["verdict"] = bool(
        probe["declared_source_binding_ok"]
        and abs(probe["diff_offset_mm"]) <= TOL_MM_COARSE
        and abs(probe["diff_forearm_mm"]) <= TOL_MM_FINE
        and abs(probe["diff_radius_edge_mm"]) <= TOL_MM_FINE
        and abs(frac_pct - 7.5459) <= 1e-3
        and abs(obliq_deg - 51.63) <= 0.05
        and not any(wrong_match.values()))
    return probe


# ------------------------------------------- P3/P4/P5: before/after map ----
def _similarity_maps(side, bodies, site_global, declared, kg, seg):
    """Closed-form BEFORE/AFTER similarity maps for one radius edge.

    AFTER construction (declared candidate, closed form), following the pinned
    I7 receipt-08 construction law: source ONB from (radius origin A -> hand
    origin src_D, the RADIUS EDGE'S OWN roll source landmark), target ONB from
    (ulna.P_d -> wrist_R, the declared roll witness Q); s_after =
    |P_d - P_new| / |src_D - A|; G = Bp B^T; L = Bp diag(s) B^T = s*G;
    t = P_new - G A. The U-STR candidate's roll site (TRIlat-P5) belongs to the
    ULNA edge declaration; the radius edge keeps its own recorded roll source.
    BEFORE is the packet's own recorded record combined with the same source ONB
    (the source landmarks are identical before/after by construction).
    """
    body = "radius_l" if side == "l" else "radius"
    hand = "hand_l" if side == "l" else "hand_r"
    A = np.array(seg["source_origin"], float)
    src_D = bodies[hand]["pos_global"]
    roll_src = np.array(kg["records"][body]["landmarks"]["roll"]["source"], float)
    roll_tgt_kg = np.array(kg["records"][body]["landmarks"]["roll"]["target"], float)
    # the packet's recorded roll_ref_point IS the target-side witness
    assert float(np.linalg.norm(roll_tgt_kg - np.array(seg["roll_ref_point"]))) \
        <= TOL_LANDMARK_M, "packet roll_ref_point disagrees with known-good roll target"
    src_span = float(np.linalg.norm(src_D - A))

    s_old = float(seg["scale"][0])
    G_old = np.array(seg["rotation"], float)
    Bp_old = np.array(seg["frame_basis"], float)
    P_old = np.array(seg["fitted_origin"], float)
    P_d_old = np.array(kg["records"][body]["landmarks"]["dist"]["target"], float)

    ulna_body = "ulna_l" if side == "l" else "ulna"
    dec = declared["records"][ulna_body]["landmarks"]
    P_new = np.array(dec["dist"]["target"], float)
    Q = np.array(dec["roll"]["target"], float)
    # declared dependency (by reuse, declared not hidden): the U-STR witness
    # target is the radius edge's own declared roll target, reused EXACTLY
    assert float(np.linalg.norm(Q - roll_tgt_kg)) <= TOL_LANDMARK_M

    span_old = float(np.linalg.norm(P_d_old - P_old))
    span_new = float(np.linalg.norm(P_d_old - P_new))
    s_new = span_new / src_span

    B_src = onb(A, src_D, roll_src)
    Bp_new = onb(P_new, P_d_old, Q)
    G_new = Bp_new @ B_src.T
    L_new = Bp_new @ np.diag([s_new] * 3) @ B_src.T
    t_new = P_new - G_new @ A

    L_old = Bp_old @ np.diag([s_old] * 3) @ B_src.T
    return {
        "side": side, "body": body, "A": A, "src_D": src_D, "roll_src": roll_src,
        "src_span": src_span, "s_old": s_old, "G_old": G_old, "Bp_old": Bp_old,
        "P_old": P_old, "P_d_old": P_d_old, "span_old": span_old,
        "P_new": P_new, "Q": Q, "span_new": span_new, "s_new": s_new,
        "B_src": B_src, "Bp_new": Bp_new, "G_new": G_new, "L_new": L_new,
        "t_new": t_new, "L_old": L_old,
    }


def probe_before_after(bodies, site_global, declared, kg, packet, receipt08):
    """P3/P4/P5: map construction, mechanism, oracles, site deltas, mirror."""
    segs = {s["source_body"]: s for s in packet["segments"]}
    out = {"sides": {}}
    fired = []

    for side in ("r", "l"):
        seg = segs["radius_l" if side == "l" else "radius"]
        M = _similarity_maps(side, bodies, site_global, declared, kg, seg)
        rec_b = receipt08["before"][M["body"]]
        rec_a = receipt08["after"][M["body"]]

        det_B = float(np.linalg.det(M["B_src"]))
        det_Bp = float(np.linalg.det(M["Bp_new"]))
        L_minus_sG = float(np.max(np.abs(M["L_new"] - M["s_new"] * M["G_new"])))
        rt = float(np.max(np.abs(np.linalg.inv(M["L_new"]) @ M["L_new"] - np.eye(3))))
        d_G = float(np.max(np.abs(M["G_new"] - M["G_old"])))

        # landmark oracle: the maps carry the radius body origin -> P and the
        # hand origin -> P_d exactly (closed form; no receipt floats consumed).
        pred_D_new = M["P_new"] + M["L_new"] @ (M["src_D"] - M["A"])
        lm_D_new = float(np.linalg.norm(pred_D_new - M["P_d_old"]))
        pred_D_old = M["P_old"] + M["L_old"] @ (M["src_D"] - M["A"])
        lm_D_old = float(np.linalg.norm(pred_D_old - M["P_d_old"]))

        # mechanism: forced closure gap vs protocol epsilon
        gap = float(np.linalg.norm(M["P_old"] - M["P_new"]))
        refusal_fires = bool(gap > JOINT_EPS)

        # packet site reproduction (BEFORE law) + AFTER deltas (closed form)
        sites = [s for s in packet["sites"] if s["segment"] == M["body"]]
        recon_err_old = 0.0
        deltas = {}
        for s in sites:
            x = np.array(s["source_pos_local"], float)
            fit = np.array(s["fitted_pos_global"], float)
            recon_err_old = max(recon_err_old, float(np.linalg.norm(
                M["P_old"] + M["L_old"] @ x - fit)))
            deltas[s["name"]] = float(np.linalg.norm(
                (M["P_new"] + M["L_new"] @ x) - (M["P_old"] + M["L_old"] @ x)))
        worst = max(deltas.items(), key=lambda kv: kv[1])
        scale_change_pct = 100.0 * (M["s_new"] / M["s_old"] - 1.0)

        checks = {
            "span_old_m": abs(M["span_old"] - rec_b["span_m"]) <= TOL_LANDMARK_M,
            "s_old": abs(M["s_old"] - rec_b["scale"]) <= TOL_UNITLESS,
            "P_old_m": float(np.max(np.abs(M["P_old"]
                                           - np.array(rec_b["P"])))) <= TOL_LANDMARK_M,
            "P_d_old_m": float(np.max(np.abs(M["P_d_old"]
                                             - np.array(rec_b["P_d"])))) <= TOL_LANDMARK_M,
            "span_new_m": abs(M["span_new"] - rec_a["span_m"]) <= TOL_LANDMARK_M,
            "s_new": abs(M["s_new"] - rec_a["scale"]) <= TOL_SCALE_REL,
            "P_new_m": float(np.max(np.abs(M["P_new"]
                                           - np.array(rec_a["P"])))) <= TOL_LANDMARK_M,
            "t_new_m": float(np.max(np.abs(M["t_new"]
                                           - np.array(rec_a["t"])))) <= TOL_LANDMARK_M,
            "detL_equals_s_cubed": abs(float(np.linalg.det(M["L_new"]))
                                       - M["s_new"] ** 3) <= 1e-12 * M["s_new"] ** 3 + 1e-18,
            "detL_receipt": abs(float(np.linalg.det(M["L_new"]))
                                - rec_a["det_full_map_L"]) <= 1e-15,
            "G_unchanged": bool(d_G <= TOL_ORTH),
            "scale_change_pct": abs(scale_change_pct
                                    - rec_a["scale_change_pct"]) <= TOL_PCT,
            "gap_m": abs(gap - receipt08["mechanism"][M["body"]]["gap_m"])
            <= TOL_LANDMARK_M,
            "refusal_fires": refusal_fires,
            "onb_dets": bool(abs(det_B - 1.0) <= TOL_ORTH
                             and abs(det_Bp - 1.0) <= TOL_ORTH),
            "L_equals_sG": bool(L_minus_sG <= TOL_ORTH),
            "roundtrip": bool(rt <= TOL_ROUNDTRIP),
            "landmark_map_after_D": bool(lm_D_new <= TOL_ROUNDTRIP),
            "landmark_map_before_D": bool(lm_D_old <= TOL_ROUNDTRIP),
            "packet_sites_reproduced": bool(recon_err_old <= TOL_RECON_M),
            "worst_delta_vs_receipt_m": bool(
                abs(worst[1] - receipt08["site_deltas"][M["body"]]
                    ["max_displacement_m"]) <= 1e-12
                and worst[0] == receipt08["site_deltas"][M["body"]]["worst_site"]),
            # the recorded "-7.93 %" transcription slip (I7 report section 3
            # correction) must NOT reproduce; the exact change is -7.9015 %
            "transcription_slip_rejected": bool(abs(scale_change_pct + 7.93) > 1e-3),
        }
        side_ok = all(bool(v) if isinstance(v, (bool, np.bool_)) else True
                      for v in checks.values())
        if not side_ok:
            fired.append(f"P3/P4/P5:{M['body']}")
        out["sides"][side] = {
            "body": M["body"],
            "P_old_m": M["P_old"].tolist(),
            "P_d_old_m": M["P_d_old"].tolist(),
            "P_new_m": M["P_new"].tolist(),
            "t_new_m": M["t_new"].tolist(),
            "span_old_m": M["span_old"],
            "span_new_m": M["span_new"],
            "s_old": M["s_old"],
            "s_new": M["s_new"],
            "src_span_m": M["src_span"],
            "gap_m": gap,
            "joint_eps": JOINT_EPS,
            "refusal_would_fire": refusal_fires,
            "det_B_src": det_B,
            "det_Bp_new": det_Bp,
            "L_minus_sG_max": L_minus_sG,
            "roundtrip_max": rt,
            "G_vs_packet_max_abs_diff": d_G,
            "scale_change_pct": scale_change_pct,
            "site_deltas_m": deltas,
            "worst_site": worst[0],
            "worst_delta_m": worst[1],
            "packet_reconstruction_max_err_m": recon_err_old,
            "landmark_oracle_after_D_m": lm_D_new,
            "landmark_oracle_before_D_m": lm_D_old,
            "checks": checks,
            "ok": bool(side_ok),
        }

    # mirror agreement (R side vs x-mirrored L side). The frozen P3 prediction
    # claimed <=1e-9 m mirror agreement for ALL vectors; the translation t_new
    # is NOT mirror-exact because the source authoring is asymmetric (the
    # receipt's own t values carry the same ~2.7e-05 m asymmetry). Both
    # readings are preserved: the over-broad prediction is RECORDED AS FIRED
    # (never silently re-tuned) and the corrected structural reading - the
    # asymmetry itself reproduces the receipt exactly - is presented alongside.
    r, l = out["sides"]["r"], out["sides"]["l"]
    mir = lambda v: [-v[0], v[1], v[2]]  # noqa: E731
    rec_t_r = receipt08["after"]["radius"]["t"]
    rec_t_l = receipt08["after"]["radius_l"]["t"]
    receipt_t_asym = float(np.max(np.abs(
        np.array(mir(rec_t_r)) - np.array(rec_t_l))))
    mirror_diffs = {
        "P_new": float(np.max(np.abs(np.array(mir(r["P_new_m"]))
                                     - np.array(l["P_new_m"])))),
        "P_d_old": float(np.max(np.abs(np.array(mir(r["P_d_old_m"]))
                                       - np.array(l["P_d_old_m"])))),
        "t_new": float(np.max(np.abs(np.array(mir(r["t_new_m"]))
                                     - np.array(l["t_new_m"])))),
        "span_new": abs(r["span_new_m"] - l["span_new_m"]),
        "s_new": abs(r["s_new"] - l["s_new"]),
    }
    mirror_ok = bool(mirror_diffs["P_new"] <= TOL_MIRROR_M
                     and mirror_diffs["P_d_old"] <= TOL_MIRROR_M
                     and mirror_diffs["t_new"] <= 1e-4
                     and abs(mirror_diffs["t_new"] - receipt_t_asym) <= 1e-12
                     and mirror_diffs["span_new"] <= TOL_UNITLESS
                     and mirror_diffs["s_new"] <= TOL_UNITLESS)
    if not mirror_ok:
        fired.append("P3:mirror_structural")
    if mirror_diffs["t_new"] > TOL_MIRROR_M:
        # the frozen prediction as written (<=1e-9 m for all vectors) failed;
        # recorded, both readings preserved (falsified-prediction, not tuning)
        fired.append("P3:mirror_t_overbroad_prediction")
    return out["sides"], mirror_diffs, mirror_ok, fired


def probe_fractions(src_probe, sides):
    """R1 5.3 drift law from independently recomputed quantities.

    Two readings are preserved for the receipt comparisons: receipt 08's
    fractions block consumed 9-decimal truncated constants (src offset
    0.023074640 m, target forearm 0.064744899 m), so its printed fraction
    differs from this attempt's full-precision value by ~5e-8 pts; the printed
    value is exactly reproducible from those truncated constants (second check).
    """
    k_rad = K_RADIUS
    src_off_mm = src_probe["offset_norm_mm"]
    src_forearm_mm = src_probe["source_forearm_ulna_to_hand_mm"]
    tgt_forearm_mm = sides["r"]["span_old_m"] * 1000.0
    derived_mm = src_off_mm * k_rad
    frac_target_pct = 100.0 * derived_mm / tgt_forearm_mm
    frac_source_pct = 100.0 * src_off_mm / src_forearm_mm
    ratio = k_rad / (tgt_forearm_mm / src_forearm_mm)
    drift_check_pct = frac_source_pct * ratio
    rec08 = load_json("i7_receipts/08_radius_before_after.json")["fractions"]
    # exact reproduction of the receipt's printed value FROM ITS TRUNCATED INPUTS
    rec_derived = 0.023074640 * k_rad * 1000.0
    rec_frac_target = 100.0 * rec_derived / (0.064744899 * 1000.0)
    out = {
        "derived_distal_point_mm": derived_mm,
        "target_per_edge_fraction_pct": frac_target_pct,
        "source_authored_fraction_pct": frac_source_pct,
        "drift_factor": ratio,
        "drift_check_pct": drift_check_pct,
        "receipt": rec08,
        "receipt_truncated_input_reproduction": {
            "inputs": {"src_offset_m": 0.023074640,
                       "tgt_forearm_m": 0.064744899},
            "derived_mm": rec_derived,
            "frac_target_pct": rec_frac_target,
            "derived_matches_receipt": bool(abs(rec_derived
                                                - rec08["derived_distal_point_mm"])
                                            <= 1e-12),
            "frac_matches_receipt": bool(abs(rec_frac_target
                                             - rec08["target_per_edge_fraction_pct"])
                                         <= 1e-12),
        },
        "checks": {
            "derived_vs_receipt": bool(abs(derived_mm
                                           - rec08["derived_distal_point_mm"])
                                       <= TOL_MM_COARSE),
            "frac_target_vs_receipt": bool(abs(frac_target_pct
                                               - rec08["target_per_edge_fraction_pct"])
                                           <= 1e-6),
            "drift_law": bool(abs(drift_check_pct - frac_target_pct)
                              <= TOL_DRIFT_PTS),
            "derived_matches_declared_gap": bool(abs(derived_mm / 1000.0
                                                     - sides["r"]["gap_m"])
                                                 <= TOL_DERIVED_GAP_M),
            "receipt_truncation_reproduced": bool(
                abs(rec_derived - rec08["derived_distal_point_mm"]) <= 1e-12
                and abs(rec_frac_target
                        - rec08["target_per_edge_fraction_pct"]) <= 1e-12),
        },
    }
    out["ok"] = all(bool(v) for v in out["checks"].values())
    return out


# ------------------------------------------------- P6: coverage topology ----
def probe_coverage(bodies, site_owner, joint_owner, tendon_paths, receipt10):
    """C16 coverage classification from XML ownership under three scenarios."""
    packet = load_json("packet/actual_monkey_fit.json")
    baseline_resolved = {s["source_body"] for s in packet["segments"]}
    diagnostic = baseline_resolved | {"ulna", "ulna_l"}
    plus_hand = diagnostic | {"hand_r", "hand_l"}

    def classify(tendon, resolved):
        path = tendon_paths[tendon]
        unresolved = [s for s in path if site_owner.get(s) not in resolved]
        if not unresolved:
            return {"complete": True, "earliest_unresolved_site": None,
                    "breaker_body": None, "unresolved_owners": []}
        owners = []
        for s in unresolved:
            o = site_owner.get(s)
            if o not in owners:
                owners.append(o)
        return {"complete": False, "earliest_unresolved_site": unresolved[0],
                "breaker_body": site_owner.get(unresolved[0]),
                "unresolved_owners": sorted(owners)}

    grasp = []
    for base in GRASP_TENDONS_RIGHT:
        grasp.append(base)
        grasp.append(base.replace("_tendon", "_l_tendon"))
    missing = [t for t in grasp if t not in tendon_paths]
    assert not missing, f"tendon paths missing from XML: {missing}"

    rows = {}
    counts = {"baseline": 0, "diagnostic_ulna_only": 0, "plus_hand": 0}
    for t in grasp:
        cb = classify(t, baseline_resolved)
        cd = classify(t, diagnostic)
        ch = classify(t, plus_hand)
        counts["baseline"] += int(cb["complete"])
        counts["diagnostic_ulna_only"] += int(cd["complete"])
        counts["plus_hand"] += int(ch["complete"])
        rows[t] = {"baseline": cb, "diagnostic_ulna_only": cd,
                   "plus_hand": ch, "n_sites": len(tendon_paths[t])}

    rec_counts = receipt10["scenario_counts"]
    rec_table = receipt10["table"]["baseline"]
    checks = {
        "baseline_complete": counts["baseline"] == rec_counts["baseline"],
        "diagnostic_complete": counts["diagnostic_ulna_only"]
        == rec_counts["diagnostic_ulna_only"],
        "plus_hand_complete": counts["plus_hand"]
        == rec_counts["diagnostic_plus_hand (context, NOT this run)"],
        "per_tendon_baseline": all(
            rows[t]["baseline"]["complete"] == rec_table[t]["complete"]
            and rows[t]["baseline"]["breaker_body"] == rec_table[t]["breaker_body"]
            and set(rows[t]["baseline"]["unresolved_owners"])
            == set(rec_table[t]["unresolved_owners"])
            and rows[t]["n_sites"] == rec_table[t]["n_sites"]
            for t in grasp),
        "joint_owner": joint_owner.get("elbow_flexion") == "ulna"
        and joint_owner.get("elbow_flexion_l") == "ulna_l",
    }
    probe = {
        "baseline_resolved_bodies": sorted(baseline_resolved),
        "scenario_counts": counts,
        "joint_owner_elbow_flexion": joint_owner.get("elbow_flexion"),
        "joint_owner_elbow_flexion_l": joint_owner.get("elbow_flexion_l"),
        "newly_defined_diagnostic": sorted(
            t for t in grasp if not rows[t]["baseline"]["complete"]
            and rows[t]["diagnostic_ulna_only"]["complete"]),
        "hand_blocked_baseline": sorted(
            t for t in grasp
            if "hand_r" in rows[t]["baseline"]["unresolved_owners"]
            or "hand_l" in rows[t]["baseline"]["unresolved_owners"]),
        "thorax_blocked_baseline": sorted(
            t for t in grasp
            if "thorax" in rows[t]["baseline"]["unresolved_owners"]),
        "rows": rows,
        "checks": checks,
        "receipt_counts": rec_counts,
    }
    probe["ok"] = all(bool(v) for v in checks.values())
    return probe


# ------------------------------------------------------- P7: R1 law ----
def probe_r1_retention(fractions):
    """The anatomical refutation is RETAINED. R1's frozen falsifier: PRIMARY
    data (radial head center at ~0-1 % of forearm length, three sources)
    placing the radial anchor OUTSIDE the frozen [4,12] % plausibility band
    refutes the anatomical reading of the authored/target fraction. The target
    fraction 7.90 % sits INSIDE [4,12] but OUTSIDE the primary band - exactly
    the refuted-anatomy / retained-kinematics split of R1 section 6."""
    tgt_pct = fractions["target_per_edge_fraction_pct"]
    band_lo, band_hi = 4.0, 12.0
    primary = [0.0, 1.0]
    falsifier_fired = bool(primary[1] < band_lo or primary[0] > band_hi)
    target_outside_primary = bool(tgt_pct < primary[0] or tgt_pct > primary[1])
    out = {
        "r1_refutation_status": "RETAINED_FIRED",
        "anatomical_support": False,
        "target_fraction_pct": tgt_pct,
        "frozen_plausibility_band_pct": [band_lo, band_hi],
        "primary_band_pct_recorded": primary,
        "primary_data_outside_plausibility_band": falsifier_fired,
        "falsifier_fired": falsifier_fired,
        "target_outside_primary_band": target_outside_primary,
        "drift_law_consistent": bool(fractions["checks"]["drift_law"]),
        "kinematic_reading": ("preserves the source author's joint-frame "
                              "convention (R1 5.3 drift law); source-kinematic "
                              "fidelity only, never anatomy"),
        "bounds": ("after-map is an UNAUTHORIZED, UNEXECUTED production "
                   "supersession candidate; the B4 PASS is source-kinematic "
                   "fidelity only (I7 memo); no A03/grasp claim"),
    }
    if not (falsifier_fired and target_outside_primary):
        out["r1_refutation_status"] = "REFUTATION_LOST"
    out["ok"] = bool(out["r1_refutation_status"] == "RETAINED_FIRED"
                     and out["drift_law_consistent"])
    return out


# ------------------------------------------------------------ assemble ----
def build_state_and_receipt():
    EVIDENCE.mkdir(exist_ok=True)
    bodies, site_owner, joint_owner, tendon_paths, site_global = xml_world()
    declared = load_json("i7_receipts/00_candidate_declaration.json")
    kg = load_json("b4_receipts/01_known_good_records.json")
    packet = load_json("packet/actual_monkey_fit.json")
    receipt08 = load_json("i7_receipts/08_radius_before_after.json")
    receipt10 = load_json("i7_receipts/10_coverage_topology.json")
    gate07 = load_json("i7_receipts/07_gate_table.json")

    joints = target_joints()
    # target binding: declared proximal anchors are the packet elbow joints and
    # the known-good radius distal anchor is the wrist joint
    bind = {
        "elbow_R_vs_declared_ulna_prox_m": float(np.linalg.norm(
            joints["elbow_R"]
            - np.array(declared["records"]["ulna"]["landmarks"]["prox"]["target"]))),
        "wrist_R_vs_knowngood_radius_dist_m": float(np.linalg.norm(
            joints["wrist_R"]
            - np.array(kg["records"]["radius"]["landmarks"]["dist"]["target"]))),
    }
    assert bind["elbow_R_vs_declared_ulna_prox_m"] <= TOL_LANDMARK_M, bind
    assert bind["wrist_R_vs_knowngood_radius_dist_m"] <= TOL_LANDMARK_M, bind

    p_src = probe_radioulnar_source(bodies, site_global, declared)
    sides, mirror_diffs, mirror_ok, fired = probe_before_after(
        bodies, site_global, declared, kg, packet, receipt08)
    fractions = probe_fractions(p_src, sides)
    coverage = probe_coverage(bodies, site_owner, joint_owner, tendon_paths,
                              receipt10)
    r1 = probe_r1_retention(fractions)
    if not p_src["verdict"]:
        fired.append("P1/P2:source")
    if not fractions["ok"]:
        fired.append("P7:fractions")
    if not coverage["ok"]:
        fired.append("P6:coverage")
    if not r1["ok"]:
        fired.append("P7:r1_retention")

    inputs = {
        "chimanoid_xml": {"path": str(REFERENCE / "chimanoid.xml"),
                          "sha256": sha256_file(REFERENCE / "chimanoid.xml")},
        "packet": {"path": str(REFERENCE / "packet/actual_monkey_fit.json"),
                   "sha256": sha256_file(REFERENCE / "packet/actual_monkey_fit.json")},
        "candidate_declaration": {
            "path": str(REFERENCE / "i7_receipts/00_candidate_declaration.json"),
            "sha256": sha256_file(
                REFERENCE / "i7_receipts/00_candidate_declaration.json")},
        "known_good": {
            "path": str(REFERENCE / "b4_receipts/01_known_good_records.json"),
            "sha256": sha256_file(
                REFERENCE / "b4_receipts/01_known_good_records.json")},
        "receipt_08": {
            "path": str(REFERENCE / "i7_receipts/08_radius_before_after.json"),
            "sha256": sha256_file(
                REFERENCE / "i7_receipts/08_radius_before_after.json")},
        "receipt_10": {
            "path": str(REFERENCE / "i7_receipts/10_coverage_topology.json"),
            "sha256": sha256_file(
                REFERENCE / "i7_receipts/10_coverage_topology.json")},
        "birth": {"path": str(INPUT_BIRTH), "sha256": sha256_file(INPUT_BIRTH)},
        "pack": {"path": str(INPUT_PACK), "sha256": sha256_file(INPUT_PACK)},
        "ulna_stl": {"path": str(INPUT_ULNA_STL),
                     "sha256": sha256_file(INPUT_ULNA_STL)},
    }
    assert inputs["birth"]["sha256"] == EXPECT_SHA["birth"]
    assert inputs["pack"]["sha256"] == EXPECT_SHA["pack"]

    b4_presented = {
        "pin": PINS["i7_gate_table"],
        "agent": "M-A02diag (2026-09-24, I7 isolated U-STR B4 diagnostic)",
        "verdicts_presented": gate07,
        "reading": ("12/12 side-test verdicts + T6 process PASS on the EXISTING "
                    "B4 T1-T6 protocol, tolerances unchanged. SOURCE-KINEMATIC "
                    "FIDELITY ONLY: it does not answer anatomy (R1 refutation "
                    "retained), authorize a production supersession, close A03, "
                    "or qualify grasp (I7 memo, verbatim bounds)."),
    }

    state = {
        "schema": "chimera.ota02_state.v1",
        "task_id": "A02",
        "card_id": "ONT-A02",
        "attempt_id": "b4a2b12b8c854e55bc400c64a502c85c",
        "criteria_sha256":
            "ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1",
        "preregistration": "PREREGISTRATION.md (frozen before probes)",
        "pins": PINS,
        "inputs": inputs,
        "source_rest_frame": {
            "definition": "chimanoid.xml authored rest pose; ulna frame +x volar, "
                          "+y proximal, +z right; arm-chain quats identity",
            "ulna_origin_m": bodies["ulna"]["pos_global"].tolist(),
            "radius_offset_in_ulna_frame_m":
                p_src["offset_vector_ulna_frame_m"],
        },
        "target_world_frame": {
            "definition": "pack frame (O1 sec.1): anterior +z, up +y, right -x",
            "elbow_R_m": joints["elbow_R"].tolist(),
            "wrist_R_m": joints["wrist_R"].tolist(),
        },
        "radioulnar_definition": p_src,
        "before_after_radius_map": {
            "right": {k: v for k, v in sides["r"].items()
                      if k not in ("site_deltas_m", "checks")},
            "left": {k: v for k, v in sides["l"].items()
                     if k not in ("site_deltas_m", "checks")},
            "site_deltas_right_m": sides["r"]["site_deltas_m"],
            "site_deltas_left_m": sides["l"]["site_deltas_m"],
            "right_checks": sides["r"]["checks"],
            "left_checks": sides["l"]["checks"],
            "mirror_max_diffs": mirror_diffs,
            "mirror_ok": mirror_ok,
            "fractions": fractions,
            "status": ("CLOSED_FORM_DIAGNOSTIC_CONSEQUENCE_ONLY; "
                       "UNAUTHORIZED AND UNEXECUTED as production supersession"),
        },
        "b4_result_presented": b4_presented,
        "coverage_topology": {k: v for k, v in coverage.items() if k != "rows"},
        "r1_refutation": r1,
        "target_binding": bind,
        "fired_falsifiers": fired,
        "outcome": ("PRESENTED_AND_REPRODUCED" if not fired
                    else "DISCREPANCY_RECORDED"),
        "done_when": ("Radioulnar definition, independent evidence, B4 result and "
                      "before/after radius mapping are presented (all four "
                      "presented here; visual component in capture_manifest.json)"),
        "honesty": {
            "cpu_only": True, "gpu_used": False, "network_used": False,
            "deterministic": True, "native_engine_run": False,
            "supersession_executed": False,
            "note": "offline re-derivation from pinned inputs; no store touched",
        },
    }

    receipt = dict(state)
    receipt["schema"] = "chimera.ota02_numerical_receipt.v1"
    return state, receipt


def write_receipts():
    state, receipt = build_state_and_receipt()
    (EVIDENCE / "state_snapshot.json").write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    (EVIDENCE / "numerical_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    return state, receipt


def main() -> int:
    state, _ = write_receipts()
    print("outcome:", state["outcome"], "| fired:", state["fired_falsifiers"])
    p = state["radioulnar_definition"]
    print("P1/P2 source:", p["verdict"], "| offset",
          round(p["offset_norm_mm"], 6), "mm | frac",
          round(p["authored_fraction_pct"], 6), "pct | obliquity",
          round(p["obliquity_deg"], 3), "deg")
    m = state["before_after_radius_map"]
    print("P3-P5 right:", m["right"]["ok"], "| s_new",
          f"{m['right']['s_new']:.17g}", "| change_pct",
          f"{m['right']['scale_change_pct']:.12f}", "| gap_mm",
          round(m["right"]["gap_m"] * 1000.0, 6))
    print("P3-P5 left:", m["left"]["ok"], "| mirror_ok", m["mirror_ok"])
    print("P6 coverage:", state["coverage_topology"]["scenario_counts"],
          "| newly_defined:", state["coverage_topology"]["newly_defined_diagnostic"])
    print("P7 R1:", state["r1_refutation"]["r1_refutation_status"],
          "| drift_law:", state["r1_refutation"]["drift_law_consistent"])
    print("wrote", EVIDENCE / "state_snapshot.json")
    print("wrote", EVIDENCE / "numerical_receipt.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
