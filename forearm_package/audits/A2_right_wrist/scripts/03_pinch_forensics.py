"""03_pinch_forensics.py — A2 audit: is the second identified loop (a) a distinct skin
surface, or one continuous cross-section curve split at a tangency/pinch point?
Measure: exact shared point, mesh-vertex coincidence, plane signed distances at fold
vertices, segment-endpoint valence at the pinch, pack blend weights at fold vertices,
fold onset bracket, ownership margins."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
sys.path.insert(0, str(WORK))

import target_envelope as te  # noqa: E402
from mesh_target import MonkeyTarget  # noqa: E402
from frame_utils import onb_from_points  # noqa: E402

BASE = Path("E:/PythonChimera/forearm_package/baseline_snapshot")
OWNER_JOINTS = ("elbow_R", "wrist_R")


def main() -> int:
    mt = MonkeyTarget(str(BASE / "inputs/monkey_birth.bin"), str(BASE / "inputs/monkey_joints.bin"))
    names = mt.names
    P = mt.joint_pos("elbow_R")
    P_d = mt.joint_pos("wrist_R")
    a_dir = (P_d - P) / np.linalg.norm(P_d - P)
    verts = mt.band_verts("elbow_R")
    rel = verts - P
    perp = rel - np.outer(rel @ a_dir, a_dir)
    q = verts[int(np.argmax((perp ** 2).sum(axis=1)))].copy()
    _, bu, cu = onb_from_points(P, P_d, q)
    owner_set = {mt.idx[n] for n in OWNER_JOINTS}
    tri_owner = np.where(mt.assign[mt.F[:, 0]] == mt.assign[mt.F[:, 1]],
                         mt.assign[mt.F[:, 0]], mt.assign[mt.F[:, 2]])

    for site, axial in (("ECRB-P3", 0.051510357), ("ECRL-P3", 0.053482959)):
        print(f"\n=== {site} @ axial {axial*1000:.6f} mm ===")
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial)
        loops, n_open, n_degen = te._chain_closed_loops(segs)
        idl = [(p, t) for p, t in loops
               if sum(1 for x in t if int(tri_owner[x]) in owner_set) / max(len(t), 1) >= 0.5]
        idl.sort(key=lambda pt: len(pt[0]))
        (sp, st), (mp, mtr) = idl

        # exact shared point between sliver and main
        D = np.linalg.norm(sp[:, None, :] - mp[None, :, :], axis=2)
        i, j = np.unravel_index(np.argmin(D), D.shape)
        dmin = float(D[i, j])
        pinch = sp[i]
        print(f"  min dist sliver<->main: {dmin:.6e} m at sliver pt {i} == main pt {j}: "
              f"pinch {pinch.tolist()}")

        # is the pinch exactly a mesh vertex?
        dv = np.linalg.norm(mt.V - pinch, axis=1)
        vid = int(np.argmin(dv))
        print(f"  nearest mesh vertex to pinch: id {vid} dist {float(dv[vid]):.6e} m "
              f"coord {mt.V[vid].tolist()} assign {names[int(mt.assign[vid])]}")

        # sliver source triangles: unique tri ids, vertices, plane signed distances
        tri_ids = sorted(set(st))
        print(f"  sliver chain tri entries {st} -> unique source triangles {tri_ids}")
        for t in tri_ids:
            vlist = [int(v) for v in mt.F[t]]
            dd = [float((mt.V[v] - P) @ a_dir - axial) for v in vlist]
            print(f"    tri {t}: verts {vlist} assign {[names[int(mt.assign[v])] for v in vlist]}")
            print(f"          plane signed dist d per vertex: {['%.3e' % x for x in dd]}")

        # segment-endpoint valence at the pinch (4 => one curve split into two chains)
        def key(p, tol=1e-7):
            return (round(float(p[0]) / tol), round(float(p[1]) / tol), round(float(p[2]) / tol))
        k = key(pinch)
        end_map = defaultdict(list)
        for i2, seg in enumerate(segs):
            end_map[key(seg[0])].append(i2)
            end_map[key(seg[1])].append(i2)
        print(f"  segment-endpoint valence at pinch key: {len(end_map.get(k, []))} "
              f"(segments {end_map.get(k, [])})")

        # do the two sliver triangles share a mesh edge/vertex with each other (fold ridge)?
        t0, t1 = tri_ids[0], tri_ids[-1]
        shared = set(int(v) for v in mt.F[t0]) & set(int(v) for v in mt.F[t1])
        print(f"  sliver triangles share mesh vertices: {sorted(shared)}")

        # ownership margins
        owned_m = sum(1 for x in mtr if int(tri_owner[x]) in owner_set)
        print(f"  main loop ownership: {owned_m}/{len(mtr)} -> fraction {owned_m/len(mtr):.2f}; "
              f"foreign tris needed to drop below 0.5: {owned_m - len(mtr)//2 if owned_m > len(mtr)//2 else 0}"
              f" (threshold margin)")
        print(f"  sliver (chain entries): {len(st)} entries, {len(tri_ids)} unique tris; "
              f"double-counted entries: {len(st) - len(tri_ids)}")

    # pack blend weights at fold vertices (w, w2 arrays of the JNT3 pack)
    print("\n=== pack blend weights (w, w2) at fold-adjacent vertices ===")
    pk = mt._pk
    # find fold triangles near the wrist: triangles cut by axial 0.053482959 owned by side
    segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, 0.053482959)
    loops, _, _ = te._chain_closed_loops(segs)
    idl = [(p, t) for p, t in loops
           if sum(1 for x in t if int(tri_owner[x]) in owner_set) / max(len(t), 1) >= 0.5]
    idl.sort(key=lambda pt: len(pt[0]))
    (sp, st), (mp, mtr) = idl
    fold_v = sorted(set(int(v) for t in sorted(set(st)) for v in mt.F[t]))
    print(f"  fold vertex ids {fold_v}")
    for v in fold_v:
        o = int(mt.assign[v])
        w = float(pk["w"][v]); w2 = float(pk["w2"][v]); o2 = int(pk["joint2"][v])
        print(f"    v{v}: assign {names[o]:9s} w {w:.4f} | joint2 {names[o2]:9s} w2 {w2:.4f}")

    # fold onset fine bracket
    def n_id_at(ax):
        sg = te._plane_cut_segments(mt.V, mt.F, P, a_dir, ax)
        lp, _, _ = te._chain_closed_loops(sg)
        return sum(1 for p, t in lp
                   if t and sum(1 for x in t if int(tri_owner[x]) in owner_set) / len(t) >= 0.5)
    print("\n=== fold onset fine bracket ===")
    for ax in (0.05110, 0.05112, 0.051121, 0.051122, 0.0511219, 0.05112192, 0.05115, 0.05120, 0.05125):
        print(f"  axial {ax*1000:.6f} mm -> identified {n_id_at(ax)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
