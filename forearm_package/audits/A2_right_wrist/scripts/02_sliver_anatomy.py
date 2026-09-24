"""02_sliver_anatomy.py — A2 audit: decisive measurements on the second identified
loop (the sliver), the degenerate chains, ownership detail, fold axial extent, and
hull-diagnostic coverage at the two RIGHT wrist sites."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
sys.path.insert(0, str(WORK))

import target_envelope as te  # noqa: E402
from mesh_target import MonkeyTarget  # noqa: E402
from frame_utils import onb_from_points  # noqa: E402

BASE = Path("E:/PythonChimera/forearm_package/baseline_snapshot")
FIT_JSON = BASE / "runs/actual_monkey_fit.json"
OUT = HERE.parent / "receipts"
MARGIN = 0.001
OWNER_JOINTS = ("elbow_R", "wrist_R")


def main() -> int:
    fit = json.loads(FIT_JSON.read_text())
    mt = MonkeyTarget(str(BASE / "inputs/monkey_birth.bin"), str(BASE / "inputs/monkey_joints.bin"))
    names = mt.names

    P = mt.joint_pos("elbow_R")
    P_d = mt.joint_pos("wrist_R")
    a = P_d - P
    L = float(np.linalg.norm(a))
    a_dir = a / L
    verts = mt.band_verts("elbow_R")
    rel = verts - P
    perp = rel - np.outer(rel @ a_dir, a_dir)
    q = verts[int(np.argmax((perp ** 2).sum(axis=1)))].copy()
    _, bu, cu = onb_from_points(P, P_d, q)

    o1, o2, o3 = mt.assign[mt.F[:, 0]], mt.assign[mt.F[:, 1]], mt.assign[mt.F[:, 2]]
    tri_owner = np.where(o1 == o2, o1, o3)
    owner_set = {mt.idx[n] for n in OWNER_JOINTS}

    def cut(axial):
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial)
        return segs, *te._chain_closed_loops(segs)

    # instrumented chaining: faithful copy of _chain_closed_loops that ALSO returns
    # degenerate (closed, <4 point) chains' content (marked lines only)
    def chain_debug(segs, tol=1e-7):
        from collections import defaultdict

        def key(p):
            return (round(float(p[0]) / tol), round(float(p[1]) / tol), round(float(p[2]) / tol))

        end_map = defaultdict(list)
        for i, seg in enumerate(segs):
            tri = seg[2] if len(seg) > 2 else -1
            end_map[key(seg[0])].append((i, 0))
            end_map[key(seg[1])].append((i, 1))
        used = [False] * len(segs)
        loops, degens, n_open = [], [], 0
        for i0 in range(len(segs)):
            if used[i0]:
                continue
            used[i0] = True
            tri0 = segs[i0][2] if len(segs[i0]) > 2 else -1
            chain = [(segs[i0][0], tri0), (segs[i0][1], tri0)]
            closed = False
            for _ in range(len(segs) + 1):
                tail = key(chain[-1][0])
                nxt = None
                for (j, end) in end_map[tail]:
                    if not used[j]:
                        nxt = (j, end)
                        break
                if nxt is None:
                    break
                j, end = nxt
                used[j] = True
                seg_j = segs[j]
                chain.append((seg_j[1 - end], seg_j[2] if len(seg_j) > 2 else -1))
                if key(chain[-1][0]) == key(chain[0][0]):
                    closed = True
                    break
            if closed and len(chain) >= 4:
                loops.append((np.array([c[0] for c in chain[:-1]]), [c[1] for c in chain[:-1]]))
            elif closed:
                degens.append((np.array([c[0] for c in chain[:-1]]), [c[1] for c in chain[:-1]]))
            else:
                n_open += 1
        return loops, degens, n_open

    sites = {"ECRB-P3": 0.051510357, "ECRL-P3": 0.053482959}
    report = {}

    for sname, axial in sites.items():
        segs, loops, n_open, n_degen = cut(axial)
        loops_d, degens, n_open_d = chain_debug(segs)
        assert len(loops_d) == len(loops) and n_open_d == n_open
        ident = []
        print(f"\n=== {sname} @ {axial:.9f} m ===")
        # A. degenerate chains
        deg_info = []
        for k, (pts, tris) in enumerate(degens):
            hist = {}
            for t in tris:
                h = names[int(tri_owner[t])]
                hist[h] = hist.get(h, 0) + 1
            per = float(np.linalg.norm(np.diff(np.vstack([pts, pts[:1]]), axis=0), axis=1).sum())
            deg_info.append({"n_pts": int(len(pts)), "owner_hist": hist,
                             "perimeter_m": round(per, 9),
                             "centroid_m": [round(float(v), 6) for v in pts.mean(axis=0)]})
            print(f"  degenerate chain {k}: pts {len(pts)} tris {len(tris)} owner {hist} "
                  f"perim {per*1000:.3f} mm centroid {np.round(pts.mean(axis=0),5).tolist()}")
        # B. sliver vs main loop
        idl = [(pts, tris) for pts, tris in loops
               if sum(1 for t in tris if int(tri_owner[t]) in owner_set) / max(len(tris), 1) >= 0.5]
        assert len(idl) == 2
        idl.sort(key=lambda pt: len(pt[0]))
        sliver, main = idl  # sliver = fewer points (3); main = 50
        d3 = np.linalg.norm(sliver[0][:, None, :] - main[0][None, :, :], axis=2)
        dmin = float(d3.min())
        poly_s = np.column_stack([(sliver[0] - P) @ bu, (sliver[0] - P) @ cu])
        poly_m = np.column_stack([(main[0] - P) @ bu, (main[0] - P) @ cu])
        cent_s_bc = poly_s.mean(axis=0)
        in_main = te._in_polygon(float(cent_s_bc[0]), float(cent_s_bc[1]), poly_m)
        d_cent_to_main = te._dist_to_poly(float(cent_s_bc[0]), float(cent_s_bc[1]), poly_m)
        # signed distances of both sites to both loops
        pkt = {s["name"]: s for s in fit["sites"]}
        site_bc = {}
        for other, oax in sites.items():
            p = np.asarray(pkt[other]["fitted_pos_global"], dtype=np.float64)
            r = p - P
            site_bc[other] = (float(r @ a_dir), float(r @ bu), float(r @ cu))
        dist_table = {}
        for other, (_, bb, cc) in site_bc.items():
            dm = te._dist_to_poly(bb, cc, poly_m)
            dsl = te._dist_to_poly(bb, cc, poly_s)
            dist_table[other] = {"main_loop_m": round(float(dm), 9), "sliver_loop_m": round(float(dsl), 9)}
            print(f"  site {other}: signed dist main {dm*1000:+.3f} mm ({'outside' if dm>0 else 'inside'}) | "
                  f"sliver {dsl*1000:+.3f} mm ({'outside' if dsl>0 else 'inside'}) | "
                  f"delta {abs(dm-dsl)*1000:.3f} mm")
        # C. sliver source triangles + their vertices' pack ownership
        tri_ids = sorted(set(sliver[1]))
        vown = []
        for t in tri_ids:
            vown.append([names[int(mt.assign[v])] for v in mt.F[t]])
        area_s = 0.5 * abs(float(np.dot(poly_s[:, 0], np.roll(poly_s[:, 1], -1)) -
                                 np.dot(poly_s[:, 1], np.roll(poly_s[:, 0], -1))))
        area_m = 0.5 * abs(float(np.dot(poly_m[:, 0], np.roll(poly_m[:, 1], -1)) -
                                 np.dot(poly_m[:, 1], np.roll(poly_m[:, 0], -1))))
        # main loop ownership margin
        n_main = len(main[1])
        owned_main = sum(1 for t in main[1] if int(tri_owner[t]) in owner_set)
        n_sliv = len(sliver[1])
        owned_sliv = sum(1 for t in sliver[1] if int(tri_owner[t]) in owner_set)
        print(f"  sliver: {n_sliv} pts {n_sliv} tris, owned {owned_sliv}/{n_sliv} (frac {owned_sliv/n_sliv:.2f}); "
              f"area {area_s*1e6:.3f} mm^2 = {area_s/area_m*1e4:.3f}% of main loop area")
        print(f"  main  : {n_main} pts {n_main} tris, owned {owned_main}/{n_main} (frac {owned_main/n_main:.2f}); "
              f"area {area_m*1e6:.2f} mm^2")
        print(f"  min 3D distance sliver-point to main-loop-point: {dmin*1000:.3f} mm")
        print(f"  sliver centroid in (b,c): inside main polygon = {in_main}; "
              f"signed dist to main boundary {d_cent_to_main*1000:+.3f} mm")
        print(f"  sliver triangle vertex owners (pack assign): {vown}")
        report[sname] = {"axial_m": axial, "degenerate_chains": deg_info,
                         "dist_table": dist_table,
                         "sliver_area_m2": area_s, "main_area_m2": area_m,
                         "min_dist_sliver_main_m": dmin,
                         "sliver_vertex_owners": vown}

    # D. fold axial extent: bisect appearance, extend sweep to find end
    def n_ident_at(ax):
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, ax)
        loops, n_open, n_degen = te._chain_closed_loops(segs)
        n_id = 0
        for pts, tris in loops:
            owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)
            if tris and owned / len(tris) >= 0.5:
                n_id += 1
        return n_id, len(loops)

    lo, hi = 0.05100, 0.05125
    assert n_ident_at(lo)[0] == 1 and n_ident_at(hi)[0] == 2
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if n_ident_at(mid)[0] >= 2:
            hi = mid
        else:
            lo = mid
    print(f"\n  sliver appears between axial {lo*1000:.6f} and {hi*1000:.6f} mm "
          f"(bisected to {hi*1000:.6f} mm)")
    end = None
    ax = 0.058
    while ax <= 0.080:
        n_id, n_loops = n_ident_at(ax)
        if n_id < 2:
            end = ax
            break
        ax += 0.00025
    print(f"  sliver still present up to {ax-0.00025:.5f} m; "
          f"{'last 2-id axial ' + format(ax-0.00025,'.5f') if end else 'no end found <= 0.080 m'}"
          + (f"; at {end:.5f} identified={n_ident_at(end)[0]}" if end else ""))
    sites_ax = (0.051510357, 0.053482959)
    print(f"  site axials {sites_ax[0]*1000:.3f} / {sites_ax[1]*1000:.3f} mm vs fold span "
          f"[{hi*1000:.3f} .. {ax:.3f} mm]")
    report["fold_span_m"] = [float(hi), (float(end) if end else 0.080)]

    # E. hull-diagnostic coverage at the two sites
    print("\n  hull diagnostic (measurements.envelope_containment.radius.per_site):")
    hull = fit["measurements"]["envelope_containment"]["radius"]["per_site"]
    for s in ("ECRB-P3", "ECRL-P3"):
        print(f"    {s}: {json.dumps(hull[s])}")
    sel = fit["measurements"]["outer_envelope"]["radius"]["selected_geometry"]
    print(f"    sections at t {sel['section_t']} x axis_len {sel['axis_len_m']:.6f} m -> "
          f"axial positions {[round(t*sel['axis_len_m'],6) for t in sel['section_t']]}, "
          f"band half {sel['section_axial_band_half_m']} m")

    OUT.joinpath("step2b_sliver_anatomy.json").write_text(json.dumps(report, indent=1))
    print("\nreceipt: step2b_sliver_anatomy.json written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
