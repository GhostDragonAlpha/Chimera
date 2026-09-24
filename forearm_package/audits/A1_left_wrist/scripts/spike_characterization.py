"""A1 measurement 2: characterize the LEFT wrist skin spike that produces the
second identified loop.
  - true owner of tri 34874 and TRUE owner_fraction of the tiny loop
    (baseline's chain bookkeeping reports [seed, seed, mid] and drops the
     closing triangle; recompute the honest set)
  - vertex fan at spike tip 6586 (valence, incident triangles)
  - 2D (b,c) geometry: is the tiny loop inside/outside the skin polygon; nearest
    boundary points for each site; why tiny/skin distances coincide for ECRL
  - onset axial of the tiny loop (bisection) and persistence distally
"""
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "work"))

from mesh_target import MonkeyTarget  # noqa: E402
import target_envelope as te  # noqa: E402
from compiler import onb_from_points  # noqa: E402

SNAP = "E:/PythonChimera/forearm_package/baseline_snapshot"


def _band_roll(mt, prox_joint, P, a):
    verts = mt.band_verts(prox_joint)
    rel = verts - P
    perp = rel - np.outer(rel @ a, a)
    d2 = (perp ** 2).sum(axis=1)
    return verts[int(np.argmax(d2))].copy()


def point_in_poly(px, py, poly):
    # te._in_polygon is the baseline's own ray-cast test
    return te._in_polygon(px, py, poly)


def main() -> int:
    mt = MonkeyTarget(
        birth_path=os.path.join(SNAP, "inputs", "monkey_birth.bin"),
        pack_path=os.path.join(SNAP, "inputs", "monkey_joints.bin"),
    )
    P = mt.joint_pos("elbow_L")
    P_d = mt.joint_pos("wrist_L")
    q = _band_roll(mt, "elbow_L", P, P_d - P)
    _, bu, cu = onb_from_points(P, P_d, q)
    a_dir = (P_d - P) / np.linalg.norm(P_d - P)
    o1 = mt.assign[mt.F[:, 0]]
    o2 = mt.assign[mt.F[:, 1]]
    o3 = mt.assign[mt.F[:, 2]]
    tri_owner = np.where(o1 == o2, o1, o3)
    owner_set = {mt.idx[n] for n in ("elbow_L", "wrist_L")}

    print("== triangle ownership (majority-of-3, baseline rule) ==")
    for t in (34872, 34874, 34888):
        f = mt.F[t]
        print(f"  tri {t}: verts {f.tolist()} assign {[mt.names[int(v)] for v in mt.assign[f]]}"
              f" -> majority owner {mt.names[int(tri_owner[t])]}"
              f" in owner_set: {int(tri_owner[t]) in owner_set}")

    print("\n== true tiny-loop ownership at both axials ==")
    for label, axial in (("ECRB_l-P3", 0.051510357325562375),
                         ("ECRL_l-P3", 0.05348295905204865)):
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial)
        loops, _, _ = te._chain_closed_loops(segs)
        for pts, tris in loops:
            if len(pts) == 3:
                seg_tris = []
                # recover the TRUE per-segment triangles by endpoint matching
                def key(p):
                    return (round(float(p[0]) / 1e-7), round(float(p[1]) / 1e-7),
                            round(float(p[2]) / 1e-7))
                m = defaultdict(list)
                for i, s in enumerate(segs):
                    m[key(s[0])].append(i)
                for k in range(3):
                    cands = m.get(key(pts[k]), [])
                    for i in cands:
                        s = segs[i]
                        if key(s[1]) == key(pts[(k + 1) % 3]) or key(s[0]) == key(pts[(k + 1) % 3]):
                            seg_tris.append(int(s[2]))
                            break
                true_tris = sorted(set(seg_tris))
                owned = sum(1 for t in true_tris if int(tri_owner[t]) in owner_set)
                print(f"  {label}: loop points {len(pts)}, true segment triangles "
                      f"{true_tris}, owned {owned}/{len(true_tris)} = "
                      f"{owned/len(true_tris):.4f} "
                      f"(baseline reported frac 1.0 from [seed,seed,mid])")

    print("\n== spike tip fan at vertex 6586 ==")
    fan = [f for f in range(len(mt.F)) if 6586 in mt.F[f]]
    print(f"  triangles incident to vertex 6586: {len(fan)} -> {fan}")
    print(f"  their majority owners: {[mt.names[int(tri_owner[t])] for t in fan]}")
    vpos = mt.V[6586]
    axial_v = float((vpos - P) @ a_dir)
    rel = vpos - P
    print(f"  tip 6586 pos {np.round(vpos, 6).tolist()}  axial {axial_v:.6f} m "
          f"({axial_v/0.064744899*100:.1f}% of elbow->wrist length) "
          f"b={float(rel@bu):.6f} c={float(rel@cu):.6f}")
    # also vertex 6596 (second near-plane vertex)
    v2 = mt.V[6596]
    r2 = v2 - P
    print(f"  vert 6596 pos {np.round(v2, 6).tolist()}  axial {float((v2-P)@a_dir):.6f} m "
          f"b={float(r2@bu):.6f} c={float(r2@cu):.6f}")

    print("\n== 2D geometry at each site's axial ==")
    sites = {
        "ECRB_l-P3": (0.051510357325562375, -0.005574, 0.003171),
        "ECRL_l-P3": (0.05348295905204865, -0.006758, 0.002002),
    }
    for name, (axial, sb, sc) in sites.items():
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial)
        loops, _, _ = te._chain_closed_loops(segs)
        skin = tiny = None
        for pts, tris in loops:
            if len(pts) == 50:
                skin = pts
            elif len(pts) == 3:
                tiny = pts
        skin_bc = np.column_stack([((skin - P) @ bu), ((skin - P) @ cu)])
        tiny_bc = np.column_stack([((tiny - P) @ bu), ((tiny - P) @ cu)])
        tb, tc = float(tiny_bc[:, 0].mean()), float(tiny_bc[:, 1].mean())
        inside = point_in_poly(tb, tc, skin_bc)
        d_edge = te._dist_to_poly(tb, tc, skin_bc)
        print(f"  {name}: tiny centroid (b,c)=({tb:.6f},{tc:.6f}) "
              f"inside skin polygon: {inside}, signed dist to skin edge {d_edge*1000:.4f} mm")
        for lbl, (sbb, scc) in (("ECRB_l-P3", (sites["ECRB_l-P3"][1], sites["ECRB_l-P3"][2])),
                                ("ECRL_l-P3", (sites["ECRL_l-P3"][1], sites["ECRL_l-P3"][2]))):
            d_skin = te._dist_to_poly(sbb, scc, skin_bc)
            d_tiny = te._dist_to_poly(sbb, scc, tiny_bc)
            # nearest boundary vertex of each polygon
            ns = np.argmin(np.linalg.norm(skin_bc - np.array([sbb, scc]), axis=1))
            nt = np.argmin(np.linalg.norm(tiny_bc - np.array([sbb, scc]), axis=1))
            print(f"    site {lbl}: d_skin={d_skin*1000:.4f} mm  d_tiny={d_tiny*1000:.4f} mm  "
                  f"nearest skin vtx (b,c)=({skin_bc[ns,0]:.6f},{skin_bc[ns,1]:.6f})  "
                  f"nearest tiny vtx (b,c)=({tiny_bc[nt,0]:.6f},{tiny_bc[nt,1]:.6f})")

    print("\n== onset of the tiny loop (bisection 0.0505 .. 0.0515) and distal persistence ==")
    def has_tiny(axial):
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial)
        loops, _, _ = te._chain_closed_loops(segs)
        return any(len(p) == 3 for p, _ in loops)
    lo, hi = 0.0505, 0.0515
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if has_tiny(mid):
            hi = mid
        else:
            lo = mid
    print(f"  tiny loop onset axial (has_tiny flips true): between {lo:.9f} and {hi:.9f} m "
          f"-> onset ~ {hi*1000:.3f} mm along axis ({hi/0.064744899*100:.1f}% of forearm)")
    last = None
    ax = hi
    while ax < 0.085:
        ax += 0.001
        if has_tiny(ax):
            last = ax
        else:
            break
    print(f"  tiny loop persists (1 mm steps) until at least {last:.4f} m"
          f" (wrist joint axial = {float((P_d-P)@a_dir):.6f} m)" if last else "  not persistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
