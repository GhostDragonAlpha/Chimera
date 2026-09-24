"""A1 audit recompute: enumerate ALL closed section loops at the LEFT wrist sites'
axial positions, with per-loop ownership fractions and per-loop signed distances.

Runs ONLY from this directory tree; imports the byte-identical copies of baseline
modules in ../work/; reads snapshot inputs READ-ONLY (explicit paths, never the
default Saved/meshes paths, never writing into baseline_snapshot/).

Provenance of copied helper bodies (verbatim, from baseline_snapshot/code/):
  _band_roll        actual_target_fit.py lines 89-98
  sites_bc builder  actual_target_fit.py lines 309-335 (_fitted_sites_bc) adapted
                    to read fitted_pos_global from the recorded fit packet (the
                    packet's own per-site record, so the fit is NOT re-run).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
sys.path.insert(0, WORK)

from mesh_target import MonkeyTarget  # noqa: E402
import target_envelope as te  # noqa: E402
from compiler import onb_from_points  # noqa: E402

SNAP = "E:/PythonChimera/forearm_package/baseline_snapshot"
OUT = "E:/PythonChimera/forearm_package/audits/A1_left_wrist/receipts"
PK = ("elbow_L", "wrist_L")
WRIST_SITES = ("ECRB_l-P3", "ECRL_l-P3")


# ---- verbatim copy: actual_target_fit.py lines 89-98 ----
def _band_roll(mt, prox_joint, P, a):
    verts = mt.band_verts(prox_joint)
    if len(verts) == 0:
        raise RuntimeError(f"joint {prox_joint} has no vertices")
    rel = verts - P
    perp = rel - np.outer(rel @ a, a)
    d2 = (perp ** 2).sum(axis=1)
    return verts[int(np.argmax(d2))].copy()


def main() -> int:
    mt = MonkeyTarget(
        birth_path=os.path.join(SNAP, "inputs", "monkey_birth.bin"),
        pack_path=os.path.join(SNAP, "inputs", "monkey_joints.bin"),
    )
    print(f"birth sha256 {mt.birth_sha}")
    print(f"pack  sha256 {mt.pack_sha}")
    print(f"mesh verts {len(mt.V)} tris {len(mt.F)}")

    P = mt.joint_pos(PK[0])
    P_d = mt.joint_pos(PK[1])
    q = _band_roll(mt, PK[0], P, P_d - P)
    _, bu, cu = onb_from_points(P, P_d, q)
    a_dir = (P_d - P) / np.linalg.norm(P_d - P)  # caller line: actual_target_fit.py:555
    print(f"P(elbow_L)  = {P.tolist()}")
    print(f"P_d(wrist_L)= {P_d.tolist()}")
    print(f"|P_d - P|   = {float(np.linalg.norm(P_d - P)):.9f} m")

    # ---- sites_bc reconstructed from the recorded fit packet (fitted_pos_global) ----
    fit = json.load(open(os.path.join(SNAP, "runs", "actual_monkey_fit.json")))
    recorded = fit["measurements"]["envelope_containment_loop"]["radius_l"]["per_site"]
    sites_bc = []
    for s in fit["sites"]:
        if s.get("segment") != "radius_l" or s.get("unresolved"):
            continue
        if not s.get("name"):
            continue
        p = np.asarray(s["fitted_pos_global"], dtype=np.float64)
        rel = p - P
        sites_bc.append({
            "name": s["name"],
            "axial": float(rel @ a_dir),
            "b": float(rel @ bu),
            "c": float(rel @ cu),
        })
    print(f"\nsites_bc reconstructed for radius_l: {len(sites_bc)} sites")
    axial_check = []
    for st in sites_bc:
        r = recorded.get(st["name"])
        if r is None:
            continue
        dax = abs(st["axial"] - r["axial_m"])
        axial_check.append({"site": st["name"], "recomputed_axial_m": st["axial"],
                            "recorded_axial_m": r["axial_m"], "abs_diff_m": dax})
    wrist = [st for st in sites_bc if st["name"] in WRIST_SITES]
    for st in wrist:
        r = recorded[st["name"]]
        print(f"  {st['name']}: recomputed axial {st['axial']:.9f} m vs recorded "
              f"{r['axial_m']:.9f} m (|diff| {abs(st['axial']-r['axial_m']):.3e} m), "
              f"b={st['b']:.6f} c={st['c']:.6f}")

    # ---- ownership: verbatim rule from target_envelope.py lines 471-473 ----
    owner_set = {mt.idx[n] for n in PK if n in mt.idx}
    print(f"\nowner_set (joint names): {sorted(mt.names[i] for i in owner_set)}")
    o1 = mt.assign[mt.F[:, 0]]
    o2 = mt.assign[mt.F[:, 1]]
    o3 = mt.assign[mt.F[:, 2]]
    tri_owner = np.where(o1 == o2, o1, o3)  # majority of 3

    def enumerate_at(axial: float):
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial)
        loops, n_open, n_degen = te._chain_closed_loops(segs)
        recs = []
        for pts, tris in loops:
            owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)
            frac = owned / len(tris) if tris else 0.0
            hist = {}
            for t in tris:
                nm = mt.names[int(tri_owner[t])]
                hist[nm] = hist.get(nm, 0) + 1
            rel = pts - P
            poly = np.column_stack([rel @ bu, rel @ cu])
            recs.append({
                "points": int(len(pts)),
                "n_cut_triangles": int(len(tris)),
                "owner_fraction": round(float(frac), 6),
                "owner_histogram": hist,
                "identified": bool(frac >= 0.5),
                "centroid_m": [round(float(v), 6) for v in pts.mean(axis=0)],
                "signed_dist_m": {
                    st["name"]: round(float(te._dist_to_poly(st["b"], st["c"], poly)), 9)
                    for st in wrist
                },
            })
        return {
            "axial_m": axial,
            "n_cut_segments": len(segs),
            "n_loops": len(loops),
            "n_open_chains": n_open,
            "n_degenerate_chains": n_degen,
            "loops": recs,
        }

    results = {}
    for st in wrist:
        axial = st["axial"]
        e1 = enumerate_at(axial)
        e2 = enumerate_at(axial)  # determinism check: identical repeat
        det = json.dumps(e1, sort_keys=True) == json.dumps(e2, sort_keys=True)
        e1["deterministic_repeat_identical"] = det
        results[st["name"]] = e1
        print(f"\n=== {st['name']} @ axial {axial:.9f} m ===")
        print(f"cut segments {e1['n_cut_segments']}, closed loops {e1['n_loops']}, "
              f"open {e1['n_open_chains']}, degenerate {e1['n_degenerate_chains']}, "
              f"repeat-identical {det}")
        for i, lp in enumerate(e1["loops"]):
            print(f"  loop[{i}] pts={lp['points']:3d} tris={lp['n_cut_triangles']:3d} "
                  f"frac={lp['owner_fraction']:.4f} identified={lp['identified']} "
                  f"owners={lp['owner_histogram']} "
                  f"dist={lp['signed_dist_m']} centroid={lp['centroid_m']}")

    # ---- axial scan around the wrist: where does each loop exist? ----
    print("\n--- axial scan 0.0460 .. 0.0575 m (0.5 mm steps) ---")
    scan = []
    for ax in np.arange(0.0460, 0.0575 + 1e-12, 0.0005):
        ax = round(float(ax), 9)
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, ax)
        loops, n_open, n_degen = te._chain_closed_loops(segs)
        fr = []
        for pts, tris in loops:
            owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)
            fr.append((int(len(pts)), round(owned / len(tris), 4) if tris else 0.0))
        fr.sort(key=lambda t: -t[1])
        n_ident = sum(1 for _, f in fr if f >= 0.5)
        scan.append({"axial_m": ax, "n_loops": len(loops), "n_identified": n_ident,
                     "loops_points_frac": fr})
        print(f"  axial {ax:.4f}: loops={len(loops)} identified={n_ident} "
              f"(pts,frac)={fr}")

    # ---- locate the tiny identified loop: which triangles, where, what component ----
    tiny_info = []
    for st in wrist:
        e = results[st["name"]]
        for lp_rec in e["loops"]:
            if lp_rec["points"] <= 6 and lp_rec["identified"]:
                # rerun to grab triangle indices for that loop
                segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, e["axial_m"])
                loops, _, _ = te._chain_closed_loops(segs)
                for pts, tris in loops:
                    if len(pts) == lp_rec["points"] and all(
                        int(tri_owner[t]) in owner_set for t in tris
                    ):
                        tv = mt.V[np.unique(mt.F[tris].ravel())]
                        tiny_info.append({
                            "site": st["name"],
                            "axial_m": e["axial_m"],
                            "loop_points": int(len(pts)),
                            "triangles": [int(t) for t in tris],
                            "tri_owner_names": [mt.names[int(tri_owner[t])] for t in tris],
                            "vertex_ids": [int(v) for v in np.unique(mt.F[tris].ravel())],
                            "vertex_bbox_m": {
                                "min": [round(float(v), 6) for v in tv.min(axis=0)],
                                "max": [round(float(v), 6) for v in tv.max(axis=0)],
                            },
                            "wrist_joint_m": [round(float(v), 6) for v in P_d],
                            "dist_centroid_to_wrist_joint_m": round(
                                float(np.linalg.norm(pts.mean(axis=0) - P_d)), 6),
                        })
    print("\n--- tiny identified loops ---")
    print(json.dumps(tiny_info, indent=1))

    out = {
        "sites_bc_all_radius_l": axial_check,
        "wrist_sites": [
            {k: st[k] for k in ("name", "axial", "b", "c")} for st in wrist
        ],
        "enumerations": results,
        "axial_scan": scan,
        "tiny_loops": tiny_info,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "recompute_loops.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nwrote {OUT}/recompute_loops.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
