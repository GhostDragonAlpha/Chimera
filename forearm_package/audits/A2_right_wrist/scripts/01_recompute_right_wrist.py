"""01_recompute_right_wrist.py — A2 audit: reproduce the RIGHT wrist-level section
loops at ECRB-P3 / ECRL-P3 exactly as the baseline loop authority computed them,
then enumerate ALL closed loops with ownership + per-loop signed distances.

Runs from work/ copies of baseline modules (target_envelope.py verbatim;
mesh_target.py with only the two input path constants repointed to the baseline
snapshot inputs). PYTHONDONTWRITEBYTECODE=1 is set by the caller.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
sys.path.insert(0, str(WORK))

import target_envelope as te  # noqa: E402  (verbatim baseline copy)
from mesh_target import MonkeyTarget  # noqa: E402
from frame_utils import onb_from_points  # noqa: E402 (verbatim compiler.py extract)

BASE = Path("E:/PythonChimera/forearm_package/baseline_snapshot")
FIT_JSON = BASE / "runs/actual_monkey_fit.json"
OUT = HERE.parent / "receipts"

MARGIN = 0.001
OWNER_JOINTS = ("elbow_R", "wrist_R")  # actual_target_fit.py L522/556: right side pk


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def main() -> int:
    fit = json.loads(FIT_JSON.read_text())

    # ---------- 0. input identity ----------
    ti = {i["kind"]: i for i in fit["target_inputs"]}
    ok_b = sha256(BASE / "inputs/monkey_birth.bin") == ti["target_mesh"]["sha256"]
    ok_j = sha256(BASE / "inputs/monkey_joints.bin") == ti["target_binding_pack"]["sha256"]
    print(f"[0] input identity: birth {ok_b}  pack {ok_j}")
    assert ok_b and ok_j, "snapshot inputs do not match the recorded fit inputs"

    mt = MonkeyTarget(str(BASE / "inputs/monkey_birth.bin"), str(BASE / "inputs/monkey_joints.bin"))
    print(f"[0] mesh verts {len(mt.V)} tris {len(mt.F)}  pack joints {len(mt.names)}")

    # ---------- 1. rebuild the exact right-side frame (actual_target_fit.py L523-528, 554-557) ----------
    P = mt.joint_pos("elbow_R")
    P_d = mt.joint_pos("wrist_R")
    a = P_d - P
    L = float(np.linalg.norm(a))
    a_dir = a / L
    # _band_roll (actual_target_fit.py L89-97): proximal joint band vertex farthest off-axis
    verts = mt.band_verts("elbow_R")
    rel = verts - P
    perp = rel - np.outer(rel @ a_dir, a_dir)
    q = verts[int(np.argmax((perp ** 2).sum(axis=1)))].copy()
    _, bu, cu = onb_from_points(P, P_d, q)
    print(f"[1] elbow_R {np.round(P,6).tolist()}  wrist_R {np.round(P_d,6).tolist()}  axis_len_m {L:.9f}")
    print(f"    roll witness q {np.round(q,6).tolist()}")
    print(f"    bu {np.round(bu,9).tolist()}  cu {np.round(cu,9).tolist()}")

    # ---------- 2. rebuild sites_bc exactly as _fitted_sites_bc (actual_target_fit.py L309-334) ----------
    sites_bc = []
    xcheck = []
    for s in fit["sites"]:
        if s.get("segment") != "radius" or s.get("unresolved"):
            continue
        p = np.asarray(s["fitted_pos_global"], dtype=np.float64)
        r = p - P
        rec = {"name": s["name"], "axial": float(r @ a_dir), "b": float(r @ bu), "c": float(r @ cu)}
        sites_bc.append(rec)
        loc = s["fitted_pos_local"]  # stored [axial,b,c]
        xcheck.append((s["name"], abs(rec["axial"] - loc[0]), abs(rec["b"] - loc[1]), abs(rec["c"] - loc[2])))
    worst = max(max(d[1:]) for d in xcheck)
    print(f"[2] rebuilt {len(sites_bc)} resolved right sites; max |recomputed - stored fitted_pos_local| = {worst:.3e} m")
    assert worst < 1e-6, "frame reconstruction mismatch"

    # ---------- 3. run the baseline authority and compare to the recorded packet ----------
    ct = te.section_loop_containment(mt, P, a_dir, bu, cu, sites_bc, margin_m=MARGIN,
                                     owner_joint_names=OWNER_JOINTS)
    stored = fit["measurements"]["envelope_containment_loop"]["radius"]
    print(f"[3] recomputed counts: inside {ct['n_inside']} tight {ct['n_inside_insufficient_clearance']} "
          f"outside {ct['n_outside']} unresolved {ct['n_unresolved']}  (stored: "
          f"{stored['n_inside']}/{stored['n_inside_insufficient_clearance']}/{stored['n_outside']}/{stored['n_unresolved']})")
    mismatches = []
    for n, rec in ct["per_site"].items():
        srec = stored["per_site"][n]
        for k in ("verdict", "reason", "axial_m", "n_loops", "n_identified_loops",
                  "n_open_chains", "n_degenerate_chains", "n_cut_segments",
                  "dist_to_loop_m", "loop_points"):
            if rec.get(k) != srec.get(k):
                mismatches.append((n, k, rec.get(k), srec.get(k)))
    print(f"[3] per-site record mismatches vs stored packet: {len(mismatches)}")
    for m in mismatches[:10]:
        print("    MISMATCH", m)
    assert not mismatches, "recomputation does not reproduce the stored records"

    # ---------- 4. deep dive: ALL loops at the two ambiguous axials ----------
    tris_owner = te.section_loop_containment.__globals__  # not used; local recompute below
    o1, o2, o3 = mt.assign[mt.F[:, 0]], mt.assign[mt.F[:, 1]], mt.assign[mt.F[:, 2]]
    tri_owner = np.where(o1 == o2, o1, o3)  # verbatim majority-of-3 (target_envelope.py L473)
    owner_set = {mt.idx[n] for n in OWNER_JOINTS if n in mt.idx}
    print(f"[4] owner_set names: {OWNER_JOINTS} -> indices {sorted(owner_set)}")

    names = mt.names
    site_by_axial = {round(s["axial"], 9): s for s in sites_bc if s["name"] in ("ECRB-P3", "ECRL-P3")}

    deep = {}
    for axial, site in sorted(site_by_axial.items()):
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial)
        loops, n_open, n_degen = te._chain_closed_loops(segs)
        print(f"\n[4] axial {axial:.9f} m  ({site['name']})  cut segments {len(segs)}  "
              f"closed loops {len(loops)}  open {n_open}  degenerate {n_degen}")
        rows = []
        for li, (pts, tris) in enumerate(loops):
            owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)
            frac = owned / len(tris) if tris else 0.0
            hist: dict[str, int] = {}
            for t in tris:
                hist[names[int(tri_owner[t])]] = hist.get(names[int(tri_owner[t])], 0) + 1
            relp = pts - P
            cent = pts.mean(axis=0)
            poly = np.column_stack([relp @ bu, relp @ cu])
            d_site = te._dist_to_poly(float(site["b"]), float(site["c"]), poly)
            per = float(np.linalg.norm(np.diff(np.vstack([poly, poly[:1]]), axis=0), axis=1).sum())
            area = 0.0
            x, y = poly[:, 0], poly[:, 1]
            area = 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))
            row = {
                "loop": li, "n_points": int(len(pts)), "n_tris": int(len(tris)),
                "owner_fraction": round(float(frac), 4), "owner_histogram": hist,
                "centroid_m": [round(float(v), 6) for v in cent],
                "axial_of_centroid_m": round(float(relp.mean(axis=0) @ a_dir), 6),
                "radial_dist_of_centroid_m": round(float(np.linalg.norm(relp.mean(axis=0) - (relp.mean(axis=0) @ a_dir) * a_dir)), 6),
                "bbox_min_m": [round(float(v), 6) for v in pts.min(axis=0)],
                "bbox_max_m": [round(float(v), 6) for v in pts.max(axis=0)],
                "perimeter_m": round(per, 6), "polygon_area_m2": round(area, 9),
                "dist_site_m": round(float(d_site), 9),
                "dist_site_class": ("outside" if d_site > 0 else ("inside" if d_site <= -MARGIN else "inside_tight")),
            }
            rows.append(row)
            print(f"    loop {li}: pts {len(pts):3d} tris {len(tris):3d} owner_frac {frac:.4f} "
                  f"hist {hist} centroid {np.round(cent,4).tolist()}")
            print(f"            bbox {np.round(pts.min(axis=0),4).tolist()} .. {np.round(pts.max(axis=0),4).tolist()}"
                  f"  perim {per*1000:.2f} mm area {area*1e6:.2f} mm^2")
            print(f"            site {site['name']} signed dist {d_site*1000:+.3f} mm -> {row['dist_site_class']}")
        n_ident = sum(1 for r in rows if r["owner_fraction"] >= 0.5)
        print(f"    => identified loops (frac >= 0.5): {n_ident}")
        deep[str(axial)] = {"site": site["name"], "n_cut_segments": len(segs), "n_loops": len(loops),
                            "n_open": n_open, "n_degenerate": n_degen,
                            "n_identified": n_ident, "loops": rows}

    OUT.joinpath("step2_deep_loops.json").write_text(json.dumps(deep, indent=1))

    # ---------- 5. determinism: run cut+chain again, compare loop structure ----------
    for axial in site_by_axial:
        segs2 = te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial)
        loops2, n_open2, n_degen2 = te._chain_closed_loops(segs2)
        sig1 = [(len(p), sorted(t for t in tr)) for p, tr in te._chain_closed_loops(te._plane_cut_segments(mt.V, mt.F, P, a_dir, axial))[0]]
        sig2 = [(len(p), sorted(t for t in tr)) for p, tr in loops2]
        print(f"[5] determinism @ {axial:.9f}: identical loop signatures on re-run = {sig1 == sig2} "
              f"(open {n_open2} degen {n_degen2})")

    # ---------- 6. dense axial sweep near the wrist: where does the 2nd loop exist? ----------
    print("\n[6] dense axial sweep (right forearm axis, 40..58 mm, 0.25 mm step):")
    sweep = []
    t0 = 0.040
    while t0 <= 0.058 + 1e-12:
        segs = te._plane_cut_segments(mt.V, mt.F, P, a_dir, t0)
        loops, n_open, n_degen = te._chain_closed_loops(segs)
        fr = []
        for pts, tris in loops:
            owned = sum(1 for t in tris if int(tri_owner[t]) in owner_set)
            fr.append((len(pts), round(owned / len(tris), 4) if tris else 0.0))
        n_ident = sum(1 for _, f in fr if f >= 0.5)
        sweep.append({"axial_m": round(t0, 9), "n_loops": len(loops), "n_open": n_open,
                      "n_degenerate": n_degen, "loops_pt_frac": fr, "n_identified": n_ident})
        t0 += 0.00025
    for r in sweep:
        tag = "SITE-REGION" if 0.050 <= r["axial_m"] <= 0.054 else ""
        print(f"    axial {r['axial_m']:.5f}  loops {r['n_loops']}  identified {r['n_identified']}  "
              f"open {r['n_open']}  degen {r['n_degenerate']}  (pts,frac) {r['loops_pt_frac']}  {tag}")
    OUT.joinpath("step2_axial_sweep.json").write_text(json.dumps(sweep, indent=1))

    # ---------- 7. falsifier check ----------
    verdicts = {ax: d["n_identified"] for ax, d in deep.items()}
    print(f"\n[7] PREREGISTRATION: identified loops per site (recomputed): {verdicts}")
    fired = all(v == 1 for v in verdicts.values())
    print(f"    FALSIFIER (exactly one loop per site) FIRED: {fired}")

    # ---------- 8. pack joint inventory (context for owner histograms) ----------
    print("\n[8] pack joint names:", ", ".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
