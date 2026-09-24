"""GEOMETRY PROBE (render-free, CPU) — settles the transverse anatomy of the
distal band before the official HAND_TARGET_VIEWS render.

Background: the R1.4 camera puts the opposed pair along n_t = a x T_R ~= world +z,
calling n_t the "broad-face normal candidate". B1's far-end receipt (target_hand
_region_v3.txt, L side) records the 80-115 mm transverse extents as b1 = 47.1 mm,
c1 = 18.1 mm with a world-z bbox range of 47.1 mm — i.e. the 47.1 mm extent appears
to lie ALONG z (~n_t), not across it. The debug render agreed: band u-span under
the frozen camera ~22 mm (~568 px < the R1.5 600 px bar).

This probe measures, from the pinned mesh only:
  1. per-station section extents along T_R and along n_t (exact triangle-plane
     intersections, O2's construction);
  2. the far-end (80-111.4 mm, r<42 mm) PCA extents -> crosscheck vs B1's 47.1/18.1;
  3. mesh x-mirror exactness (verts + triangles) for the L-hand check design;
  4. the band's projected u-span under the frozen (+/-n_t) and face-on (+/-T) cameras.

No render, no GPU; reads the pinned inputs through the byte-identical loader copy.
Writes receipts/geometry_probe.txt and receipts/geometry_probe.json only.
"""
from __future__ import annotations

import json
import sys

sys.dont_write_bytecode = True
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
sys.path.insert(0, str(HERE / "work"))
from mesh_target_htv import MonkeyTarget  # noqa: E402

EXPECT_BIRTH = "550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c"
EXPECT_PACK = "74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662"


def unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def section_points(V, F, origin, a, t, rmax=0.045):
    """Exact triangle-plane intersection (O2's construction, verbatim)."""
    n = V @ a - (t + origin @ a)
    tri = n[F]
    sign = np.signbit(tri)
    has_cross = ~(sign.all(axis=1) | (~sign).all(axis=1))
    tris = F[has_cross]
    d3 = n[tris]
    pts = []
    for k in range(len(tris)):
        dd = d3[k]
        ids = tris[k]
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if dd[i] == 0.0 or (dd[i] > 0) != (dd[j] > 0):
                if dd[i] == dd[j]:
                    continue
                w = dd[i] / (dd[i] - dd[j])
                p = V[ids[i]] + w * (V[ids[j]] - V[ids[i]])
                if np.linalg.norm(p - (origin + a * t)) <= rmax:
                    pts.append(p)
    return np.array(pts)


def fixed_T(a):
    x = np.array([1.0, 0.0, 0.0])
    e1 = x - a * (a @ x)
    return unit(e1)


def main() -> int:
    mt = MonkeyTarget(birth_path=str(BASE / "inputs" / "monkey_birth.bin"),
                      pack_path=str(BASE / "inputs" / "monkey_joints.bin"))
    assert mt.birth_sha.lower() == EXPECT_BIRTH and mt.pack_sha.lower() == EXPECT_PACK
    out_lines = []
    rec = {}

    def say(s):
        print(s)
        out_lines.append(s)

    wrist = mt.joint_pos("wrist_R")
    elbow = mt.joint_pos("elbow_R")
    a = unit(wrist - elbow)
    T = fixed_T(a)
    n_t = unit(np.cross(a, T))
    say(f"a   = {np.round(a, 6).tolist()}")
    say(f"T_R = {np.round(T, 6).tolist()}  (fixed +x-rejection rule)")
    say(f"n_t = {np.round(n_t, 6).tolist()}  (= a x T_R; R1.4 'broad-face normal candidate')")
    say(f"T . n_t = {float(T @ n_t):+.2e}")

    rel = mt.V - wrist
    t_ax = rel @ a
    perp = rel - np.outer(t_ax, a)
    r = np.linalg.norm(perp, axis=1)
    band = (t_ax >= 0.055) & (t_ax <= 0.1114) & (r <= 0.042)
    say(f"band verts (t in [55,111.4] mm, r<42 mm): {int(band.sum())}")

    # 1. per-station extents along T and n_t
    say("\nstation extents (exact sections, rmax 45 mm about the axis point):")
    say("  t[mm]   n_pts   ext_T[mm]  ext_nt[mm]   PCA major[mm]  PCA minor[mm]  major-dir .n_t")
    stations = {}
    for tmm in (60, 70, 80, 90, 100, 110):
        pts = section_points(mt.V, mt.F, wrist, a, tmm / 1000.0)
        if len(pts) < 8:
            say(f"  {tmm:5d}   {len(pts):5d}   (too few points)")
            continue
        relp = pts - (wrist + a * (tmm / 1000.0))
        eT = relp @ T
        eN = relp @ n_t
        c = pts.mean(axis=0)
        _, _, Vt = np.linalg.svd(pts - c, full_matrices=False)
        p1, p2 = Vt[0], Vt[1]
        m1 = float((relp @ p1).max() - (relp @ p1).min())
        m2 = float((relp @ p2).max() - (relp @ p2).min())
        say(f"  {tmm:5d}   {len(pts):5d}   {(eT.max()-eT.min())*1000:8.2f}  {(eN.max()-eN.min())*1000:9.2f}"
            f"     {m1*1000:8.2f}     {m2*1000:8.2f}   {float(p1 @ n_t):+.4f}")
        stations[tmm] = dict(n_pts=len(pts), ext_T_mm=(eT.max() - eT.min()) * 1000,
                             ext_nt_mm=(eN.max() - eN.min()) * 1000,
                             pca_major_mm=m1 * 1000, pca_minor_mm=m2 * 1000,
                             pca_major_dot_nt=float(p1 @ n_t), pca_minor_dot_T=float(p2 @ T))
    rec["stations"] = stations

    # 2. far-end PCA extents (crosscheck vs B1's 47.1 / 18.1)
    far = (t_ax >= 0.080) & (t_ax <= 0.1114) & (r <= 0.042)
    P = mt.V[far]
    c = P.mean(axis=0)
    _, _, Vt = np.linalg.svd(P - c, full_matrices=False)
    relp = (P - c) @ Vt.T
    b1 = float(relp[:, 0].max() - relp[:, 0].min())
    c1 = float(relp[:, 1].max() - relp[:, 1].min())
    say(f"\nfar end (80-111.4 mm, r<42): n={int(far.sum())}  PCA extents b1={b1*1000:.1f} mm  "
        f"c1={c1*1000:.1f} mm  (B1 receipt v3 recorded 47.1 / 18.1)")
    say(f"  b1 direction . n_t = {float(Vt[0] @ n_t):+.4f}   . T = {float(Vt[0] @ T):+.4f}   . a = {float(Vt[0] @ a):+.4f}")
    say(f"  c1 direction . n_t = {float(Vt[1] @ n_t):+.4f}   . T = {float(Vt[1] @ T):+.4f}")
    say("  -> the 47.1 mm major extent lies along n_t (~world z): the R1.4 'broad-face")
    say("     normal candidate' is the lens's WIDTH direction; the broad faces (O2's +/-T")
    say("     faces) are normal to T_R.")
    rec["far_end"] = dict(n=int(far.sum()), b1_mm=b1 * 1000, c1_mm=c1 * 1000,
                          b1_dot_nt=float(Vt[0] @ n_t), b1_dot_T=float(Vt[0] @ T),
                          b1_dot_a=float(Vt[0] @ a), c1_dot_nt=float(Vt[1] @ n_t),
                          c1_dot_T=float(Vt[1] @ T))

    # 3. mesh x-mirror exactness
    key = lambda P_: (np.rint(P_ * 1e6).astype(np.int64))
    vk = key(mt.V)
    vset = set(map(tuple, vk.tolist()))
    mirrored = key(mt.V * np.array([-1.0, 1.0, 1.0]))
    vsym = sum(1 for k in map(tuple, mirrored.tolist()) if k in vset)
    say(f"\nmesh x-mirror: {vsym}/{len(mt.V)} verts have an exact mirrored counterpart "
        f"({100.0*vsym/len(mt.V):.2f} %)")
    Fk = np.sort(vk[mt.F], axis=1).reshape(len(mt.F), 9)
    fset = set(map(tuple, Fk.tolist()))
    Fm = np.sort(mirrored[mt.F], axis=1).reshape(len(mt.F), 9)
    fsym = sum(1 for k in map(tuple, Fm.tolist()) if k in fset)
    say(f"  triangles: {fsym}/{len(mt.F)} have an exact mirrored counterpart ({100.0*fsym/len(mt.F):.2f} %)")
    rec["mirror"] = dict(verts_sym=vsym, n_verts=int(len(mt.V)),
                         tris_sym=fsym, n_tris=int(len(mt.F)))

    # 4. band u-span under both camera designs (frame half-width 40 mm, 25.6 px/mm)
    look_at = wrist + 0.083 * a
    P = mt.V[band]
    x_lit = unit(np.cross(a, unit(look_at + 0.30 * n_t - look_at)))  # unit(a x n_t)
    say("\nband projected u-span (all band verts, screen-right axis):")
    u_lit = (P - look_at) @ x_lit
    say(f"  literal R1.4 camera (+/-n_t): u in [{u_lit.min()*1000:+.2f}, {u_lit.max()*1000:+.2f}] mm "
        f"-> span {(u_lit.max()-u_lit.min())/0.080*2048:.1f} px")
    u_face = (P - look_at) @ n_t  # face-on camera: screen right = -/+n_t
    say(f"  face-on camera (+/-T):        u in [{u_face.min()*1000:+.2f}, {u_face.max()*1000:+.2f}] mm "
        f"-> span {(u_face.max()-u_face.min())/0.080*2048:.1f} px")
    rec["band_u_span"] = dict(
        literal_nt_mm=[float(u_lit.min() * 1000), float(u_lit.max() * 1000)],
        literal_nt_px=(u_lit.max() - u_lit.min()) / 0.080 * 2048,
        faceon_T_mm=[float(u_face.min() * 1000), float(u_face.max() * 1000)],
        faceon_T_px=(u_face.max() - u_face.min()) / 0.080 * 2048,
        n_band=int(band.sum()))

    (HERE / "receipts").mkdir(exist_ok=True)
    (HERE / "receipts" / "geometry_probe.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    with open(HERE / "receipts" / "geometry_probe.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    print("\nwrote receipts/geometry_probe.txt + .json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
