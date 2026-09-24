"""A1 measurement 3 (corrected): 2D (b,c) geometry with the skin loop selected by
OWNERSHIP (not point count), crevice depth profile, and harness validation against
a RESOLVED site's recorded distance (ECRL_l-P2, recorded 0.004597397 m).
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

    fit = json = None
    import json as _json
    fit = _json.load(open(os.path.join(SNAP, "runs", "actual_monkey_fit.json")))

    # exact site b/c from the packet (not rounded prints)
    sites = {}
    for s in fit["sites"]:
        if s.get("segment") == "radius_l" and s.get("name") in (
                "ECRB_l-P3", "ECRL_l-P3", "ECRL_l-P2") and not s.get("unresolved"):
            p = np.asarray(s["fitted_pos_global"], dtype=np.float64)
            rel = p - P
            sites[s["name"]] = (float(rel @ a_dir), float(rel @ bu), float(rel @ cu))
    for k, v in sorted(sites.items()):
        print(f"site {k}: axial={v[0]:.9f} b={v[1]:.9f} c={v[2]:.9f}")

    # ---- harness validation vs a RESOLVED site (ECRL_l-P2, 1 identified loop) ----
    ax2, b2, c2 = sites["ECRL_l-P2"]
    segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, ax2)
    loops, _, _ = te._chain_closed_loops(segs)
    for pts, tris in loops:
        owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)
        if tris and owned / len(tris) >= 0.5:
            rel = pts - P
            poly = np.column_stack([rel @ bu, rel @ cu])
            d = te._dist_to_poly(b2, c2, poly)
            rec = fit["measurements"]["envelope_containment_loop"]["radius_l"]["per_site"]["ECRL_l-P2"]
            print(f"\nVALIDATION ECRL_l-P2: recomputed dist {d:.9f} m vs recorded "
                  f"{rec['dist_to_loop_m']} m (|diff| {abs(d-rec['dist_to_loop_m']):.3e})")

    # ---- corrected 2D geometry at the two wrist axials ----
    for name in ("ECRB_l-P3", "ECRL_l-P3"):
        ax, sb, sc = sites[name]
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, ax)
        loops, _, _ = te._chain_closed_loops(segs)
        skin = tiny = None
        for pts, tris in loops:
            owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)
            if tris and owned / len(tris) >= 0.5:
                if len(pts) == 50:
                    skin = pts
                elif len(pts) == 3:
                    tiny = pts
        skin_bc = np.column_stack([((skin - P) @ bu), ((skin - P) @ cu)])
        tiny_bc = np.column_stack([((tiny - P) @ bu), ((tiny - P) @ cu)])
        # radial stats about the forearm axis point at this axial (origin of b,c)
        r_skin = np.linalg.norm(skin_bc, axis=1)
        r_tiny = np.linalg.norm(tiny_bc, axis=1)
        print(f"\n{name} axial {ax:.9f}:")
        print(f"  skin polygon: {len(skin_bc)} vtx, radius min {r_skin.min()*1000:.3f} mm "
              f"max {r_skin.max()*1000:.3f} mm mean {r_skin.mean()*1000:.3f} mm")
        print(f"  tiny polygon: {len(tiny_bc)} vtx, radius min {r_tiny.min()*1000:.3f} mm "
              f"max {r_tiny.max()*1000:.3f} mm centroid radius "
              f"{float(np.linalg.norm(tiny_bc.mean(axis=0)))*1000:.3f} mm")
        tb, tc = float(tiny_bc[:, 0].mean()), float(tiny_bc[:, 1].mean())
        inside = te._in_polygon(tb, tc, skin_bc)
        d_edge = te._dist_to_poly(tb, tc, skin_bc)
        print(f"  tiny centroid ({tb:.6f},{tc:.6f}) inside skin polygon: {inside}, "
              f"signed dist to skin edge {d_edge*1000:.4f} mm")
        for other in ("ECRB_l-P3", "ECRL_l-P3"):
            ob, oc = sites[other][1], sites[other][2]
            d_skin = te._dist_to_poly(ob, oc, skin_bc)
            d_tiny = te._dist_to_poly(ob, oc, tiny_bc)
            ns = int(np.argmin(np.linalg.norm(skin_bc - np.array([ob, oc]), axis=1)))
            nt = int(np.argmin(np.linalg.norm(tiny_bc - np.array([ob, oc]), axis=1)))
            print(f"    verdict-if-site={other}: d_skin={d_skin*1000:.4f} mm d_tiny={d_tiny*1000:.4f} mm"
                  f"  nearest-skin-vtx ({skin_bc[ns,0]:.6f},{skin_bc[ns,1]:.6f})"
                  f"  nearest-tiny-vtx ({tiny_bc[nt,0]:.6f},{tiny_bc[nt,1]:.6f})")

    # ---- crevice depth: fan base ring vertices radii at the tip axial ----
    print("\ncrevice geometry (3D, at the tip):")
    tip = mt.V[6586]
    r_tip = tip - P
    perp = r_tip - (r_tip @ a_dir) * a_dir
    print(f"  tip 6586 == 6596: {bool(np.allclose(mt.V[6586], mt.V[6596]))}, "
          f"radial distance from axis {float(np.linalg.norm(perp))*1000:.3f} mm, "
          f"axial {float(r_tip @ a_dir)*1000:.3f} mm")
    for v in (6582, 6585, 6596, 6601, 6607):
        vp = mt.V[v] - P
        vp_perp = vp - (vp @ a_dir) * a_dir
        print(f"  vtx {v} ({mt.names[int(mt.assign[v])]}) radial "
              f"{float(np.linalg.norm(vp_perp))*1000:.3f} mm axial {float(vp @ a_dir)*1000:.3f} mm "
              f"pos {np.round(mt.V[v], 5).tolist()}")
    # sliver triangle 34872 edge lengths
    f = mt.F[34872]
    pts = mt.V[f]
    el = [float(np.linalg.norm(pts[i] - pts[(i + 1) % 3])) * 1000 for i in range(3)]
    print(f"  tri 34872 edge lengths: {[round(x,3) for x in el]} mm")
    f = mt.F[34888]
    pts = mt.V[f]
    el = [float(np.linalg.norm(pts[i] - pts[(i + 1) % 3])) * 1000 for i in range(3)]
    print(f"  tri 34888 edge lengths: {[round(x,3) for x in el]} mm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
