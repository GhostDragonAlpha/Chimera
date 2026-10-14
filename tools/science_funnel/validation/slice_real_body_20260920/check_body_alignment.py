"""check_body_alignment.py -- F-ALIGNMENT: the femur mesh vs the assembly's
hip/knee joint centers, through the EXACT standing compose (lane
slice_real_body_20260920; the prediction and the 5 mm bound were named in
record.md BEFORE this run -- the previous instance never measured this).

The joint centers are the pose chain's own pivots, in bind CT millimetres:
  hip  L/R: the hip battery's fitted femoral-head centers (dv.hip[s]["c"],
            cross-checked against the battery's axis pivots at the house
            rounding) -- each femur's FK chain anchors here, so the pivot is
            its bitwise fixed point under the FK,
  knee L/R: the realizing-gap midpoints M of bond.joint_02_06 / bond.joint_03_07
            (dv.knee[s]["M"]) -- the knee's relative rotation anchors at M in
            the FEMUR's frame, so the posed knee center is T[femur].pts(M).

Through the standing compose (FK -> pinned registration -> standing placement,
the same code path scene_boot.build_standing_layer runs), for each femur
(bones 02, 03), against TWO meshes:

  payload femur: the decimated committed body bone the ENGINE rides
                 (its vertex block of the merged payload compose -- located by
                 per-bone vertex counts and BITWISE-ANCHORED: this script's
                 copied compose of that bone must equal the merged compose's
                 block exactly, or nothing downstream means anything),
  preview femur: the full-resolution committed _lo preview -- the geometry
                 class the pivots were fitted on.

MEASURED per pivot: d_surf(pivot, payload femur) and d_surf(pivot, preview
femur) (exact point-to-triangle minimum; scene metres -> mm), and, hips only,
the winding number of the closed payload femur at the pivot.

PASS (the record.md bound):
  - hip L and R: strictly inside the payload femur (|winding| == 1, d > 0), and
  - all four pivots: |d_surf(payload) - d_surf(preview)| <= 5.0 mm
    (the mission-named bound; the derived expectation is sub-millimetre --
    body_manifest's own QEM deviation max_dev_mm <= 0.6827 -- so a pass NEAR
    5 mm is a near-fire and is reported as one).
The knee containment test is waived BY DERIVATION (record.md): M is the
midpoint of the realizing closest pair, in the joint gap by construction --
its cross-check |d_surf(preview femur, M) - gap0/2| is recorded.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools" / "science_funnel" / "validation"
                       / "standing_pose_20260921"))
sys.path.insert(0, str(ROOT / "tools" / "science_funnel" / "validation"
                       / "hip_pivot_proof_20260921"))
sys.path.insert(0, str(ROOT / "tools" / "playable_slice"))

import scene_boot as sb  # noqa: E402
from standing_pose_core import rnd  # noqa: E402  (the house rounding)
from standing_pose_core import StandingDerivation  # noqa: E402
from tools.science_funnel import ct_skeleton_layer as CSL  # noqa: E402
from tools.science_funnel import ct_skeleton_triangle as CST  # noqa: E402

BOUND_MM = 5.0     # the mission-named bound (record.md, F-ALIGNMENT)

BODY_DIR = ROOT / ("tools/science_funnel/data/morphosource_ct/"
                   "meshes_body_20260922")
FEMURS = {"L": 2, "R": 3}      # bond.joint_01_02 / bond.joint_01_03 children


# ── exact point-to-mesh measurements ────────────────────────────────────────

def point_tri_distance(p: np.ndarray, a: np.ndarray, b: np.ndarray,
                       c: np.ndarray) -> float:
    """Exact point-to-triangle distance, ONE point vs MANY triangles
    (Ericson's clamped barycentric rule, vectorized). metres in, metres out."""
    ab, ac = b - a, c - a
    ap = p[None, :] - a
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = p[None, :] - b
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p[None, :] - c
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va, vb = (ab * ab).sum(1), (ac * ac).sum(1)
    vc = d1 * d4 - d3 * d2
    vb2 = d5 * d2 - d1 * d6
    va2 = d3 * d6 - d5 * d4
    with np.errstate(divide="ignore", invalid="ignore"):
        s_ab = np.where(d1 - d3 != 0, d1 / (d1 - d3), 0.0)
        s_ac = np.where(d2 - d6 != 0, d2 / (d2 - d6), 0.0)
        den_bc = (d4 - d3) + (d5 - d6)
        s_bc = np.where(den_bc != 0, (d4 - d3) / den_bc, 0.0)
        den_i = np.where((va2 + vb2 + vc) != 0, 1.0 / (va2 + vb2 + vc), 0.0)
        w_i, v_i = vb2 * den_i, vc * den_i
    best = np.full(len(a), np.inf)
    sq = lambda x: float(np.dot(x, x))
    cands = [
        ((d1 <= 0) & (d2 <= 0), ap),                                  # vertex A
        ((d3 >= 0) & (d4 <= d3), bp),                                 # vertex B
        ((d6 >= 0) & (d5 <= d6), cp),                                 # vertex C
        ((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + ab * s_ab[:, None] - p[None, :]),
        ((vb2 <= 0) & (d2 >= 0) & (d6 <= 0), a + ac * s_ac[:, None] - p[None, :]),
        ((va2 <= 0) & (d4 >= d3) & (d5 >= d6), b + ab * s_bc[:, None] - p[None, :]),
    ]
    for mask, vec in cands:
        d = np.einsum("ij,ij->i", vec, vec)
        best = np.where(mask & (d < best), d, best)
    # interior (least priority): A + ab*v + ac*w
    p_int = a + ab * v_i[:, None] + ac * w_i[:, None] - p[None, :]
    d_int = np.einsum("ij,ij->i", p_int, p_int)
    fallback = ~((d1 <= 0) & (d2 <= 0)) & ~((d3 >= 0) & (d4 <= d3)) \
        & ~((d6 >= 0) & (d5 <= d6)) & ~((vc <= 0) & (d1 >= 0) & (d3 <= 0)) \
        & ~((vb2 <= 0) & (d2 >= 0) & (d6 <= 0)) & ~((va2 <= 0) & (d4 >= d3)
                                                    & (d5 >= d6))
    best = np.where(fallback & (d_int < best), d_int, best)
    return float(np.sqrt(best.min()))


def winding_number(p: np.ndarray, verts: np.ndarray,
                   tris: np.ndarray) -> float:
    """Signed winding number of a CLOSED mesh at p (Van Oosterom & Strackee
    solid angle). |w| == 1 inside, 0 outside (the mesh is measured closed)."""
    a = verts[tris[:, 0]] - p
    b = verts[tris[:, 1]] - p
    c = verts[tris[:, 2]] - p
    la = np.linalg.norm(a, axis=1)
    lb = np.linalg.norm(b, axis=1)
    lc = np.linalg.norm(c, axis=1)
    triple = np.einsum("ij,ij->i", a, np.cross(b, c))
    numer = np.abs(triple)
    denom = (la * lb * lc + (a * b).sum(1) * lc
             + (a * c).sum(1) * lb + (b * c).sum(1) * la)
    omega = 2.0 * np.arctan2(numer, denom)
    return float((np.sign(triple) * omega).sum() / (4.0 * np.pi))


# ── the standing compose, verbatim from scene_boot (anchored below) ─────────

def build_compose():
    pose = json.loads(sb.POSE_JSON.read_text(encoding="utf-8"))
    x_rec = np.array(pose["variables"]["x_R12"], dtype=np.float64)
    dv = StandingDerivation()
    raw = CSL.WALKER_DERIVED_PATH.read_bytes()
    assert CSL._sha256(raw) == CSL.WALKER_DERIVED_SHA256, "walker pin drift"
    hat = float(json.loads(raw)["body_model"]["segments_Table1"]["HAT"]["length_m"])
    composite = CSL.load_obj_vertices(CSL.PREVIEW_DIR / CSL.COMPOSITE_PREVIEW)
    scale, R_reg, t_reg, _ = CSL.ct_registration(composite, hat, sb.SEAT_HEIGHT_M)

    P_ct = dv.pad_centroids(x_rec)
    _, n_ct = dv._plane_stats(P_ct)
    n_scene0 = R_reg @ n_ct
    up = np.array([0.0, 1.0, 0.0])
    v = n_scene0 / np.linalg.norm(n_scene0)
    c = float(v @ up)
    axis = np.cross(v, up)
    s = float(np.linalg.norm(axis))
    if s < 1e-15:
        R_place = np.eye(3)
    else:
        axis = axis / s
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]],
                      [-axis[1], axis[0], 0]])
        R_place = np.eye(3) + K * s + K @ K * (1.0 - c)
    pad_scene = (P_ct @ R_reg.T) * scale / 1000.0 + t_reg
    pad_scene = pad_scene @ R_place.T
    lift = float(pad_scene[:, 1].mean())

    def pose_mm(points_ct_mm: np.ndarray) -> np.ndarray:
        out = CSL.apply_registration(np.asarray(points_ct_mm, np.float64),
                                     scale, R_reg, t_reg)
        return out @ R_place.T - np.array([0.0, lift, 0.0])

    return dv, x_rec, scale, pose_mm


def block_tris(tris_all: np.ndarray, lo: int, hi: int) -> np.ndarray:
    m = tris_all[(tris_all >= lo).all(1) & (tris_all < hi).all(1)]
    return m - lo


# ── the falsifier ────────────────────────────────────────────────────────────

def main() -> int:
    dv, x_rec, scale, pose_mm = build_compose()
    T = dv.fk(x_rec)

    # the two merged composes (payload + full-resolution preview ghost)
    verts_body, tris_body, _ = sb.build_standing_layer(preview_dir=BODY_DIR,
                                                       obj_suffix="_body")
    verts_prev, tris_prev, _ = sb.build_standing_layer_cached()

    # per-bone blocks, in meshes/manifest.json order (both composes append in
    # this order); counts read from the mesh files themselves
    man = json.loads((CSL.CT_DIR / "meshes" / "manifest.json").read_text())
    names = [Path(e["file"]).name for e in man["bones"]]
    counts_body, counts_prev, off_b, off_p = [], [], 0, 0
    blocks = {}
    for name in names:
        vb, _ = CST.load_obj_mesh(BODY_DIR / name.replace(".obj", "_body.obj"))
        vp, _ = CST.load_obj_mesh(CSL.PREVIEW_DIR
                                  / name.replace(".obj", "_lo.obj"))
        bone = int(name.split("_")[1])
        blocks[bone] = (off_b, off_b + len(vb), off_p, off_p + len(vp))
        counts_body.append(len(vb))
        counts_prev.append(len(vp))
        off_b += len(vb)
        off_p += len(vp)
    assert sum(counts_body) == len(verts_body), "payload block split drift"
    assert sum(counts_prev) == len(verts_prev), "preview block split drift"

    # BITWISE ANCHOR: this script's compose must reproduce the merged blocks
    anchors = {}
    for side, bone in FEMURS.items():
        v_mm, _ = CST.load_obj_mesh(
            BODY_DIR / [n for n in names if int(n.split("_")[1]) == bone][0]
            .replace(".obj", "_body.obj"))
        lo, hi, _, _ = blocks[bone]
        mine = pose_mm(T[bone].pts(v_mm))
        anchors[f"payload_femur_{side}"] = bool(
            np.array_equal(mine, verts_body[lo:hi]))
        pv_mm, _ = CST.load_obj_mesh(
            CSL.PREVIEW_DIR
            / [n for n in names if int(n.split("_")[1]) == bone][0]
            .replace(".obj", "_lo.obj"))
        _, _, plo, phi = blocks[bone]
        mine_p = pose_mm(T[bone].pts(pv_mm))
        anchors[f"preview_femur_{side}"] = bool(
            np.array_equal(mine_p, verts_prev[plo:phi]))
    if not all(anchors.values()):
        raise RuntimeError("compose anchor failed: this script's compose path "
                           "does not bitwise-match the merged composes")

    # the pivots
    battery = dv.hip_battery
    pivots = {}
    for side, bone in FEMURS.items():
        k = "0%d" % bone
        c = dv.hip[side]["c"]
        assert [rnd(x) for x in c] == \
            [rnd(x) for x in battery["axis"]["pivot_%s_mm" % k]], \
            "hip pivot vs battery axis drift (%s)" % side
        posed_c = T[bone].pts(c[None, :])
        assert np.array_equal(posed_c[0], c), "hip pivot fixed point broken"
        M = dv.knee[side]["M"]
        posed_M = T[bone].pts(M[None, :])   # the femur carries the knee center
        pivots[side] = {"hip_c_ctmm": c, "knee_M_ctmm": M,
                        "hip_scene_m": pose_mm(posed_c)[0],
                        "knee_scene_m": pose_mm(posed_M)[0],
                        "gap0_mm": float(dv.knee[side]["gap0_mm"])}

    # measure
    sides = {}
    all_ok = True
    for side, bone in FEMURS.items():
        lo, hi, plo, phi = blocks[bone]
        f_pay_v, f_pay_t = verts_body[lo:hi], block_tris(tris_body, lo, hi)
        f_prv_v, f_prv_t = verts_prev[plo:phi], block_tris(tris_prev, plo, phi)
        rec = {}
        for joint in ("hip", "knee"):
            p = pivots[side][f"{joint}_scene_m"]
            d_pay = point_tri_distance(p, f_pay_v[f_pay_t[:, 0]],
                                       f_pay_v[f_pay_t[:, 1]],
                                       f_pay_v[f_pay_t[:, 2]]) * 1000.0
            d_prv = point_tri_distance(p, f_prv_v[f_prv_t[:, 0]],
                                       f_prv_v[f_prv_t[:, 1]],
                                       f_prv_v[f_prv_t[:, 2]]) * 1000.0
            entry = {"d_payload_mm": round(d_pay, 6),
                     "d_preview_mm": round(d_prv, 6),
                     "delta_mm": round(abs(d_pay - d_prv), 6),
                     "within_bound": bool(abs(d_pay - d_prv) <= BOUND_MM)}
            if joint == "hip":
                w = winding_number(p, f_pay_v, f_pay_t)
                entry["winding_payload"] = round(w, 6)
                entry["strictly_inside"] = bool(abs(w) > 0.5 and d_pay > 1e-9)
                entry["pass"] = bool(entry["strictly_inside"]
                                     and entry["within_bound"])
            else:
                entry["gap0_over_2_mm"] = round(pivots[side]["gap0_mm"] / 2.0,
                                                6)
                entry["preview_vs_gap_cross_check_mm"] = round(
                    abs(d_prv - pivots[side]["gap0_mm"] / 2.0), 6)
                entry["pass"] = entry["within_bound"]
            rec[joint] = entry
            all_ok &= bool(entry["pass"])
        sides[side] = rec

    out = {
        "falsifier": "F-ALIGNMENT",
        "pass": bool(all_ok),
        "bound_mm": BOUND_MM,
        "measured": {
            "compose_anchor_bitwise": anchors,
            "scale_registration": float(scale),
            "payload_femur_blocks": {s: [blocks[b][0], blocks[b][1]]
                                     for s, b in FEMURS.items()},
            "sides": sides,
        },
        "law": "the joint centers are the pose chain's own pivots (hip: the "
               "fitted femoral-head fixed points; knee: the realizing-gap "
               "midpoints, carried by the femur's FK); the mesh the engine "
               "rides may not move the anatomy at any pivot by more than the "
               "mission-named 5 mm vs the geometry class the pivots were "
               "fitted on, and a hip head center must lie inside its femur",
    }
    (HERE / "alignment.json").write_text(json.dumps(out, indent=1),
                                         encoding="utf-8")
    print(json.dumps(out["measured"]["sides"], indent=1))
    print("pass:", out["pass"])
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
