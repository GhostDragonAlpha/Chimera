"""A1 diagnostic: dissect the tiny 3-point identified loop at the LEFT wrist axials.
Answers: which segments/triangles form it, is one triangle really used twice, where
does it sit relative to the skin loop, and does the plane pass exactly through a
shared mesh vertex (explaining identical signed distances).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "work"))

from mesh_target import MonkeyTarget  # noqa: E402
import target_envelope as te  # noqa: E402
from compiler import onb_from_points  # noqa: E402

SNAP = "E:/PythonChimera/forearm_package/baseline_snapshot"
PK = ("elbow_L", "wrist_L")


def _band_roll(mt, prox_joint, P, a):
    verts = mt.band_verts(prox_joint)
    rel = verts - P
    perp = rel - np.outer(rel @ a, a)
    d2 = (perp ** 2).sum(axis=1)
    return verts[int(np.argmax(d2))].copy()


def main() -> int:
    mt = MonkeyTarget(
        birth_path=os.path.join(SNAP, "inputs", "monkey_birth.bin"),
        pack_path=os.path.join(SNAP, "inputs", "monkey_joints.bin"),
    )
    P = mt.joint_pos(PK[0])
    P_d = mt.joint_pos(PK[1])
    q = _band_roll(mt, PK[0], P, P_d - P)
    _, bu, cu = onb_from_points(P, P_d, q)
    a_dir = (P_d - P) / np.linalg.norm(P_d - P)

    for label, axial in (("ECRL_l-P3", 0.05348295905204865),
                         ("ECRB_l-P3", 0.051510357325562375)):
        print(f"\n================ {label} axial {axial:.12f} ================")
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial)
        loops, n_open, n_degen = te._chain_closed_loops(segs)
        # exact-plane vertex check: any |d| < 1e-9 m?
        d = (mt.V - P) @ a_dir - axial
        nv_on_plane = int(np.sum(np.abs(d) < 1e-9))
        print(f"mesh vertices with |d|<1e-9 m of the plane: {nv_on_plane}")
        print(f"segments {len(segs)}, loops {len(loops)}, open {n_open}, degen {n_degen}")
        for li, (pts, tris) in enumerate(loops):
            if len(pts) > 6:
                continue
            print(f"\nTINY loop[{li}]: {len(pts)} pts, tri list {tris}")
            for k, p in enumerate(pts):
                print(f"  pt[{k}] = {np.round(p, 6).tolist()}")
            # find the contributing segments by matching endpoints
            for t in sorted(set(tris)):
                f = mt.F[t]
                dd = d[f]
                print(f"  tri {t}: verts {f.tolist()} d={np.round(dd, 9).tolist()} "
                      f"assign={mt.assign[f].tolist()} "
                      f"({[mt.names[int(mt.assign[v])] for v in f]})")
                print(f"    tri verts: {np.round(mt.V[f], 6).tolist()}")
            # segment provenance: match each loop edge to a segment
            def key(p):
                return (round(float(p[0]) / 1e-7), round(float(p[1]) / 1e-7),
                        round(float(p[2]) / 1e-7))
            seg_by_key = {}
            for i, s in enumerate(segs):
                seg_by_key.setdefault(key(s[0]), []).append(i)
            print("  loop-edge -> segment match:")
            for k in range(len(pts)):
                p_cur, p_nxt = pts[k], pts[(k + 1) % len(pts)]
                cands = seg_by_key.get(key(p_cur), [])
                match = None
                for i in cands:
                    s = segs[i]
                    if key(s[1]) == key(p_nxt):
                        match = i
                        break
                if match is not None:
                    s = segs[match]
                    print(f"    edge[{k}] -> segment {match} tri {s[2]} "
                          f"len {float(np.linalg.norm(s[1]-s[0]))*1000:.4f} mm")
                else:
                    print(f"    edge[{k}] -> NO EXACT SEGMENT MATCH")
            # geometric relation to the 50-pt skin loop in the (b,c) plane
            for lj, (pts2, tris2) in enumerate(loops):
                if len(pts2) != 50 or lj == li:
                    continue
                rel2 = pts2 - P
                poly2 = np.column_stack([rel2 @ bu, rel2 @ cu])
                rel = pts - P
                poly_t = np.column_stack([rel @ bu, rel @ cu])
                dmin = min(float(np.linalg.norm(p - poly2)) for p in poly_t)
                print(f"  min 2D distance tiny-loop->skin-loop[{lj}]: {dmin*1000:.6f} mm")
        # what are triangles 34872 / 34888 in the mesh? connected component walk
        print("\ncomponent walk from the tiny loop's triangles:")
        seed = sorted({34872, 34888})
        # build edge -> triangles map once
        from collections import defaultdict
        edge_map = defaultdict(list)
        for f in range(len(mt.F)):
            a0, b0, c0 = mt.F[f]
            for u, v in ((a0, b0), (b0, c0), (c0, a0)):
                edge_map[(min(u, v), max(u, v))].append(f)
        seen = set(seed)
        stack = list(seed)
        while stack:
            f = stack.pop()
            a0, b0, c0 = mt.F[f]
            for u, v in ((a0, b0), (b0, c0), (c0, a0)):
                for g in edge_map[(min(u, v), max(u, v))]:
                    if g not in seen:
                        seen.add(g)
                        stack.append(g)
        print(f"  edge-connected component size: {len(seen)} triangles")
        comp_verts = np.unique(mt.F[np.array(sorted(seen))].ravel())
        comp_V = mt.V[comp_verts]
        print(f"  component bbox min {np.round(comp_V.min(axis=0),4).tolist()} "
              f"max {np.round(comp_V.max(axis=0),4).tolist()}")
        own = mt.assign[comp_verts]
        hist = {}
        for o in own:
            hist[mt.names[int(o)]] = hist.get(mt.names[int(o)], 0) + 1
        print(f"  component vertex owners (top 6): "
              f"{sorted(hist.items(), key=lambda kv: -kv[1])[:6]}")
        # is the component manifold-closed? count edge incidence
        inc = defaultdict(int)
        for f in seen:
            a0, b0, c0 = mt.F[f]
            for u, v in ((a0, b0), (b0, c0), (c0, a0)):
                inc[(min(u, v), max(u, v))] += 1
        bad = sum(1 for e, c in inc.items() if c != 2)
        print(f"  component edges total {len(inc)}, non-manifold/boundary edges {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
