"""O2 script 2 — TARGET palm sign: paddle resting-flexion curvature (sagitta test).

Reads baseline_snapshot/inputs/monkey_birth.bin + monkey_joints.bin ONLY through the
byte-identical module copy work/mesh_target_o2.py (== baseline code/mesh_target.py,
sha256 268f139a...; verified before reuse), paths repointed to the snapshot.

FROZEN METHOD (O2 brief, preregistered): a relaxed primate hand curls volar-ward —
the palm face is CONCAVE along the length, the dorsum CONVEX. Measure the paddle's
mid-line curvature (chord vs arc sagitta along the length axis, BOTH faces); the
sagitta DIFFERENCE over the DISTAL HALF identifies concave vs convex.
FROZEN THRESHOLD: sagitta difference > 1 mm over the distal half (paddle length
111.3 mm, C2 -> distal-half window = 55.65..111.3 mm from wrist_R along the axis).
FROZEN FALSIFIER: a convex-palm/flat result -> report numbers.
FROZEN STOP RULE: curvature below threshold and no existing image -> BLOCKER.

Stationing: along the elbow->wrist axis direction a (the C2/C3 receipts' axis; the
paddle PCA axis is 10.3 deg off it, C2 — the PCA-axis variant is computed as a
sensitivity check). Thickness line = the C3 paddle-flat line (principal section
azimuth 87 deg mod 180, boot +-0.7-1.1 deg); the signed +T convention is the FIXED
rule "rejection of global +x on the plane orthogonal to a" (C3's e1), stated per side.

Readouts per window:
  mid-line  : centroid T-coordinate vs station -> signed sagitta vs chord (+ quad fit)
  face+ / face- : per-station extreme surface heights -> each profile's signed sagitta
  D1 = sagitta(face+) - sagitta(face-)   <- the FROZEN decision quantity
  D2 = mid-line signed sagitta           <- independent direction readout
Uniform bending predicts: both face sagittae share the sign of D2 (both arcs bow away
from the center of curvature), the CONVEX face has the LARGER |sagitta|, and the
mid-line bows toward the convex face. Rim rounding at the window ends contaminates
D1 toward "faces converge" — recorded via the thickness profile and a trimmed window.

Figures: matplotlib Agg BEFORE pyplot import (CPU-only; gaming-safety rule).
Writes receipts/o2_target_curvature.json.  No writes outside audits/O2_hand_orientation/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gaming-safety: software renderer, BEFORE pyplot import
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
HERE = Path(r"E:\PythonChimera\forearm_package\audits\O2_hand_orientation")
OUT = HERE / "receipts" / "o2_target_curvature.json"
FIGDIR = HERE / "figures"
sys.path.insert(0, str(HERE / "work"))
from mesh_target_o2 import MonkeyTarget  # noqa: E402  (byte-identical baseline copy)

EXPECT_SHA = {
    "birth": "550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c",
    "pack": "74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662",
}

PADDLE_LEN_MM = 111.3          # C2 (r<25 mm tube); 111.4 with r<40
DISTAL_HALF = (0.5, 1.0)       # FROZEN window fraction of the paddle length


def unit(v):
    return v / np.linalg.norm(v)


def transverse_basis(a):
    """C3's fixed rule: e1 = rejection of global +x on plane orthogonal to a; e2 = a x e1."""
    x = np.array([1.0, 0.0, 0.0])
    e1 = x - a * (a @ x)
    if np.linalg.norm(e1) < 1e-9:
        x = np.array([0.0, 0.0, 1.0])
        e1 = x - a * (a @ x)
    e1 = unit(e1)
    e2 = np.cross(a, e1)
    return e1, e2


def section_points(V, F, origin, a, t, rmax=0.045):
    """Exact triangle-plane intersection (C3's construction; no slab bias, no bridging)."""
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
        pairs = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if dd[i] == 0.0 or (dd[i] > 0) != (dd[j] > 0):
                pairs.append((i, j))
        for i, j in pairs:
            if dd[i] == dd[j]:
                continue
            w = dd[i] / (dd[i] - dd[j])
            p = V[ids[i]] + w * (V[ids[j]] - V[ids[i]])
            if np.linalg.norm(p - (origin + a * t)) <= rmax:
                pts.append(p)
    return np.array(pts)


def pca_axis(mt, w, a, rmax=0.025):
    """Paddle's own PCA axis over wrist-distal vertices within rmax of the axis line."""
    rel = mt.V - w
    t = rel @ a
    perp = rel - np.outer(t, a)
    r = np.linalg.norm(perp, axis=1)
    sel = (t > 0.005) & (r < rmax)
    P = mt.V[sel]
    c = P.mean(axis=0)
    _, _, Vt = np.linalg.svd(P - c, full_matrices=False)
    return unit(Vt[0]), float(np.degrees(np.arccos(min(1.0, abs(float(Vt[0] @ a)))))), int(sel.sum())


def profile(mt, w, a, e1, stations_mm, rmax=0.045):
    """Per-station mid-line / face heights along +T = e1."""
    rows = []
    for tmm in stations_mm:
        pts = section_points(mt.V, mt.F, w, a, tmm / 1000.0, rmax=rmax)
        if len(pts) < 8:
            rows.append(None)
            continue
        rel = pts - (w + a * (tmm / 1000.0))
        tt = rel @ e1                       # thickness coordinate (+T)
        ww = rel @ np.cross(a, e1)          # width coordinate (in-plane check)
        tmax, tmin = float(tt.max()), float(tt.min())
        th = tmax - tmin
        cen = float(tt.mean())
        # face band means (top/bottom 20% of local thickness) as sensitivity readout
        band = 0.2 * th
        fplus_band = float(tt[tt > tmin + 0.8 * th].mean()) if th > 1e-9 else tmax
        fminus_band = float(tt[tt < tmin + 0.2 * th].mean()) if th > 1e-9 else tmin
        rows.append(
            {
                "t_mm": float(tmm), "n": int(len(pts)),
                "tmax_mm": tmax * 1000, "tmin_mm": tmin * 1000,
                "thickness_mm": th * 1000, "centroid_T_mm": cen * 1000,
                "faceplus_max_mm": tmax * 1000, "faceminus_min_mm": tmin * 1000,
                "faceplus_band_mm": fplus_band * 1000, "faceminus_band_mm": fminus_band * 1000,
                "width_extent_mm": float(ww.max() - ww.min()) * 1000,
                "centroid_W_mm": float(ww.mean()) * 1000,
            }
        )
    return [r for r in rows if r is not None]


def sagitta(ts, ys, lo, hi):
    """Signed sagitta of profile ys(t) vs the chord over [lo, hi]; + quad-fit curvature.
    Positive = profile bows toward +T relative to the chord."""
    m = (ts >= lo) & (ts <= hi)
    t, y = ts[m], ys[m]
    if len(t) < 5:
        return None
    y0 = np.interp(lo, t, y)
    y1 = np.interp(hi, t, y)
    chord = y0 + (y1 - y0) * (t - lo) / (hi - lo)
    dev = y - chord
    i = int(np.argmax(np.abs(dev)))
    # quadratic fit (robust to facet staircasing): y = a + b t + c t^2
    c = np.polyfit(t - t.mean(), y, 2)
    tm = 0.5 * (lo + hi)
    sag_q = float(np.polyval(c, tm - t.mean()) - (y0 + (y1 - y0) * (tm - lo) / (hi - lo)))
    return {
        "window_mm": [lo, hi], "n_stations": int(len(t)),
        "sagitta_max_signed_mm": float(dev[i]), "at_t_mm": float(t[i]),
        "sagitta_quadfit_mm": sag_q,
        "quad_c2_mm_per_mm2": float(c[0]),
    }


def analyze_side(mt, side):
    e = mt.joint_pos(f"elbow_{side}")
    w = mt.joint_pos(f"wrist_{side}")
    a = unit(w - e)
    e1, e2 = transverse_basis(a)
    L_forearm = float(np.linalg.norm(w - e))
    pca, pca_ang, pca_n = pca_axis(mt, w, a)

    stations = np.arange(40.0, 116.0, 1.0)   # 0..111.3 is the paddle; a margin past the tip
    prof = profile(mt, w, a, e1, stations)
    ts = np.array([r["t_mm"] for r in prof])

    lo, hi = DISTAL_HALF[0] * PADDLE_LEN_MM, DISTAL_HALF[1] * PADDLE_LEN_MM
    mid = sagitta(ts, np.array([r["centroid_T_mm"] for r in prof]), lo, hi)
    fp = sagitta(ts, np.array([r["faceplus_max_mm"] for r in prof]), lo, hi)
    fm = sagitta(ts, np.array([r["faceminus_min_mm"] for r in prof]), lo, hi)
    fpb = sagitta(ts, np.array([r["faceplus_band_mm"] for r in prof]), lo, hi)
    fmb = sagitta(ts, np.array([r["faceminus_band_mm"] for r in prof]), lo, hi)

    D1 = None if (fp is None or fm is None) else fp["sagitta_max_signed_mm"] - fm["sagitta_max_signed_mm"]
    D1q = None if (fp is None or fm is None) else fp["sagitta_quadfit_mm"] - fm["sagitta_quadfit_mm"]
    # trimmed diagnostic window (last 8 mm excluded: rim rounding; first 4 mm: bulge shoulder)
    tri = sagitta(ts, np.array([r["centroid_T_mm"] for r in prof]), lo, hi - 8.0)
    fp_tri = sagitta(ts, np.array([r["faceplus_max_mm"] for r in prof]), lo, hi - 8.0)
    fm_tri = sagitta(ts, np.array([r["faceminus_min_mm"] for r in prof]), lo, hi - 8.0)
    D1_tri = None if (fp_tri is None or fm_tri is None) else \
        fp_tri["sagitta_max_signed_mm"] - fm_tri["sagitta_max_signed_mm"]

    return {
        "side": side, "elbow": e.tolist(), "wrist": w.tolist(),
        "axis_unit_a": a.tolist(), "forearm_len_mm": L_forearm * 1000,
        "basis_e1_plusT": e1.tolist(), "basis_e2": e2.tolist(),
        "paddle_pca_axis": pca.tolist(), "paddle_pca_vs_a_deg": pca_ang, "pca_n_verts": pca_n,
        "stations_used_n": len(prof),
        "profile": {
            "t_mm": [r["t_mm"] for r in prof],
            "tmax_mm": [r["faceplus_max_mm"] for r in prof],
            "tmin_mm": [r["faceminus_min_mm"] for r in prof],
            "centroid_T_mm": [r["centroid_T_mm"] for r in prof],
            "thickness_mm": [r["thickness_mm"] for r in prof],
            "faceplus_band_mm": [r["faceplus_band_mm"] for r in prof],
            "faceminus_band_mm": [r["faceminus_band_mm"] for r in prof],
            "width_extent_mm": [r["width_extent_mm"] for r in prof],
            "centroid_W_mm": [r["centroid_W_mm"] for r in prof],
            "n_pts": [r["n"] for r in prof],
        },
        "thickness_profile_mm": {int(r["t_mm"]): round(r["thickness_mm"], 2) for r in prof},
        "frozen_window_mm": [lo, hi],
        "midline_sagitta": mid, "faceplus_sagitta": fp, "faceminus_sagitta": fm,
        "faceplus_band_sagitta": fpb, "faceminus_band_sagitta": fmb,
        "D1_sagitta_difference_mm": D1, "D1_quadfit_mm": D1q,
        "D2_midline_signed_sagitta_mm": None if mid is None else mid["sagitta_max_signed_mm"],
        "D2_quadfit_mm": None if mid is None else mid["sagitta_quadfit_mm"],
        "trimmed_window_diagnostic": {
            "window_mm": [lo, hi - 8.0],
            "midline": tri, "faceplus": fp_tri, "faceminus": fm_tri, "D1_mm": D1_tri,
        },
    }


def main() -> int:
    mt = MonkeyTarget(
        birth_path=str(BASE / "inputs" / "monkey_birth.bin"),
        pack_path=str(BASE / "inputs" / "monkey_joints.bin"),
    )
    assert mt.birth_sha.lower() == EXPECT_SHA["birth"], mt.birth_sha
    assert mt.pack_sha.lower() == EXPECT_SHA["pack"], mt.pack_sha
    print("input hashes match MANIFEST (birth 550a5b3e..., pack 74b3ab04...)")

    out = {
        "inputs": {"birth_sha256": mt.birth_sha, "pack_sha256": mt.pack_sha,
                   "module_copy": "work/mesh_target_o2.py (baseline mesh_target.py verbatim, "
                                  "sha256 268f139a..., paths repointed to snapshot)"},
        "frozen": {
            "paddle_len_mm": PADDLE_LEN_MM, "window_fraction": DISTAL_HALF,
            "threshold_mm": 1.0,
            "statement": "sagitta difference (face+ minus face-) > 1 mm over the distal half",
        },
    }
    for side in ("R", "L"):
        r = analyze_side(mt, side)
        out[side] = r
        print(f"--- side {side} ---")
        print(f"  +T basis e1 = {np.round(r['basis_e1_plusT'], 4).tolist()}  "
              f"(fixed rule: rejection of +x on plane ⟂ a)")
        print(f"  paddle PCA vs a: {r['paddle_pca_vs_a_deg']:.1f} deg ({r['pca_n_verts']} verts)")
        print(f"  frozen window {r['frozen_window_mm'][0]:.1f}..{r['frozen_window_mm'][1]:.1f} mm, "
              f"{r['stations_used_n']} stations")
        for k in ("midline_sagitta", "faceplus_sagitta", "faceminus_sagitta"):
            s = r[k]
            print(f"  {k:18s} sag {s['sagitta_max_signed_mm']:+7.3f} mm @t={s['at_t_mm']:6.1f} "
                  f"(quadfit {s['sagitta_quadfit_mm']:+7.3f} mm)")
        print(f"  D1 (frozen sagitta difference) = {r['D1_sagitta_difference_mm']:+.3f} mm "
              f"(quadfit {r['D1_quadfit_mm']:+.3f} mm)  threshold |D1| > 1.0 mm")
        print(f"  D2 (mid-line signed sagitta)   = {r['D2_midline_signed_sagitta_mm']:+.3f} mm "
              f"(quadfit {r['D2_quadfit_mm']:+.3f} mm)")
        tr = r["trimmed_window_diagnostic"]
        print(f"  trimmed-window diagnostic: D1 = {tr['D1_mm'] if tr['D1_mm'] is None else round(tr['D1_mm'], 3)} mm")

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
