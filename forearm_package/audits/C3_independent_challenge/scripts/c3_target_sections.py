"""C3 script 2 — target-side orientation measurements (right + left forearm skin tube,
elbow-band roll vertex, distal paddle).

Reads ONLY baseline_snapshot/inputs/monkey_birth.bin + monkey_joints.bin through a
byte-identical module copy of baseline mesh_target.py (work/mesh_target_c3.py) with
paths repointed to the snapshot. Hashes are printed and must equal MANIFEST.json.

Measurements (geometry only; no anatomy claim beyond what is stated):
  1. Forearm skin cross-sections at axial stations along the elbow->wrist axis
     (including a PROXIMAL station t<0 for the live "both axis directions" ambiguity
     of the U-STR authoring). Sections are exact triangle-plane intersection segments
     (no vertex-slab bias, no bridging). Per station:
       - centroid offset from the axis (magnitude + azimuth in a fixed transverse basis)
       - transverse covariance eigenvalues (eccentricity ratio) + principal azimuth
       - bootstrap (triangle resample) azimuth/eccentricity noise floor
  2. The elbow band roll vertex (the _band_roll construction family the resolved
     radius uses): top-10 off-axis band vertices, their azimuths, gap structure.
  3. The distal paddle: same section stats at paddle stations (paddle-flat normal =
     thickness principal line; camber = centroid offset). Both sides.
Writes receipts JSON. No writes outside audits/C3_independent_challenge/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

C3 = Path(r"E:\PythonChimera\forearm_package\audits\C3_independent_challenge")
BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
sys.path.insert(0, str(C3 / "work"))
from mesh_target_c3 import MonkeyTarget  # noqa: E402  (module copy, baseline logic verbatim)

OUT = C3 / "receipts" / "c3_target_sections.json"

EXPECT_SHA = {
    "birth": "550a5b3ec927ea13614ad250963b23e2948e76a238ac110da9889f339aabfa3c",
    "pack": "74b3ab044b7adaed4a0f9349a81f5d3c87441084b2ec8981f4e0afaba50c1662",
}


def unit(v):
    return v / np.linalg.norm(v)


def transverse_basis(a):
    """Fixed rule: e1 = rejection of global +x on the plane orthogonal to a; e2 = a x e1."""
    x = np.array([1.0, 0.0, 0.0])
    e1 = x - a * (a @ x)
    if np.linalg.norm(e1) < 1e-9:
        x = np.array([0.0, 0.0, 1.0])
        e1 = x - a * (a @ x)
    e1 = unit(e1)
    e2 = np.cross(a, e1)
    return e1, e2


def section_points(V, F, origin, a, t, rmax=0.045):
    """Exact triangle-plane intersection: plane = {p: (p-origin)@a == t}.
    Returns segment-endpoint samples of the section curve within rmax of the axis line."""
    n = V @ a - (t + origin @ a)
    tri = n[F]  # (M,3) signed distances of triangle vertices
    sign = np.signbit(tri)
    has_cross = ~(sign.all(axis=1) | (~sign).all(axis=1))
    tris = F[has_cross]
    d3 = n[tris]
    pts = []
    for k in range(len(tris)):
        dd = d3[k]
        ids = tris[k]
        # the crossing edge(s): vertex pairs with opposite signs
        pairs = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if dd[i] == 0.0 or (dd[i] > 0) != (dd[j] > 0):
                pairs.append((i, j))
        seen = []
        for i, j in pairs:
            if dd[i] == dd[j]:
                continue
            w = dd[i] / (dd[i] - dd[j])
            p = V[ids[i]] + w * (V[ids[j]] - V[ids[i]])
            seen.append(p)
        for p in seen:
            rel = p - (origin + a * t)
            if np.linalg.norm(rel) <= rmax:
                pts.append(p)
    return np.array(pts)


def section_stats(pts, origin, a, t, e1, e2, n_boot=200, seed=0):
    """centroid offset, eccentricity, azimuths, bootstrap noise floor."""
    if len(pts) < 8:
        return None
    cplane = origin + a * t
    rel = pts - cplane
    r = np.column_stack([rel @ e1, rel @ e2])
    cen = r.mean(axis=0)
    off = float(np.linalg.norm(cen))
    off_az = float(np.degrees(np.arctan2(cen[1], cen[0])))
    X = r - cen
    C = (X.T @ X) / len(X)
    ev, evec = np.linalg.eigh(C)  # ascending
    lam1, lam2 = float(ev[1]), float(ev[0])
    ratio = lam1 / lam2 if lam2 > 1e-12 else float("inf")
    v1 = evec[:, 1]
    az1 = float(np.degrees(np.arctan2(v1[1], v1[0])))
    az1 = ((az1 + 90.0) % 180.0) - 90.0  # mod 180 principal-line convention
    # bootstrap over section segments (resample points; azimuth + ratio noise floor)
    rng = np.random.default_rng(seed)
    azs, rats = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, len(r), len(r))
        rb = r[idx]
        cb = rb.mean(axis=0)
        Xb = rb - cb
        Cb = (Xb.T @ Xb) / len(Xb)
        evb, evecb = np.linalg.eigh(Cb)
        if evb[0] > 1e-12:
            vb = evecb[:, 1]
            azb = float(np.degrees(np.arctan2(vb[1], vb[0])))
            azs.append(((azb + 90.0) % 180.0) - 90.0)
            rats.append(float(evb[1] / evb[0]))
    azs, rats = np.array(azs), np.array(rats)
    # circular std for mod-180 azimuths: double-angle
    ang = np.radians(2 * np.array(azs))
    R = np.hypot(np.sin(ang).mean(), np.cos(ang).mean())
    az_std = float(np.degrees(np.sqrt(-2 * np.log(max(R, 1e-12))) / 2))
    # bootstrap noise floor of the SIGNED centroid-offset azimuth (mean feature)
    off_azs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(r), len(r))
        cb = r[idx].mean(axis=0)
        azb = float(np.degrees(np.arctan2(cb[1], cb[0])))
        off_azs.append(azb)
    off_ang = np.radians(np.array(off_azs))
    Roff = np.hypot(np.sin(off_ang).mean(), np.cos(off_ang).mean())
    off_az_std = float(np.degrees(np.sqrt(-2 * np.log(max(Roff, 1e-12)))))
    return {
        "t_mm": t * 1000.0,
        "n_pts": int(len(pts)),
        "radial_extent_mm": [float(np.linalg.norm(r, axis=1).min() * 1000), float(np.linalg.norm(r, axis=1).max() * 1000)],
        "centroid_offset_mm": off * 1000.0,
        "centroid_offset_azimuth_deg": off_az,
        "boot_centroid_azimuth_circstd_deg": off_az_std,
        "eccentricity_ratio_l1_over_l2": ratio,
        "principal_azimuth_deg_mod180": az1,
        "boot_principal_azimuth_circstd_deg": az_std,
        "boot_eccentricity_iqr": [float(np.percentile(rats, 25)), float(np.percentile(rats, 75))],
    }


def band_roll_structure(mt, joint, origin, a, e1, e2, topk=10):
    verts = mt.band_verts(joint)
    if len(verts) == 0:
        return None
    rel = verts - origin
    perp = rel - np.outer(rel @ a, a)
    d = np.linalg.norm(perp, axis=1)
    order = np.argsort(-d)[:topk]
    rows = []
    for i in order:
        az = float(np.degrees(np.arctan2(perp[i] @ e2, perp[i] @ e1)))
        rows.append({"perp_mm": float(d[i] * 1000), "azimuth_deg": az})
    return {"n_band": int(len(verts)), "top": rows,
            "gap_ratio_d1_over_d2": float(d[order[0]] / d[order[1]])}


def arm_pipeline(mt, side, stations_mm):
    e = mt.joint_pos(f"elbow_{side}")
    w = mt.joint_pos(f"wrist_{side}")
    a = unit(w - e)
    e1, e2 = transverse_basis(a)
    L = float(np.linalg.norm(w - e))
    out = {
        "elbow": e.tolist(), "wrist": w.tolist(), "axis_unit": a.tolist(),
        "axis_len_m": L, "basis_e1": e1.tolist(), "basis_e2": e2.tolist(),
        "sections": [], "paddle_sections": [],
    }
    for tmm in stations_mm:
        t = tmm / 1000.0
        pts = section_points(mt.V, mt.F, e, a, t)
        st = section_stats(pts, e, a, t, e1, e2)
        if st:
            out["sections"].append(st)
    # paddle: distal of wrist, along the same axis direction
    for tmm in (75, 82, 89, 96, 103, 110):
        t = tmm / 1000.0
        pts = section_points(mt.V, mt.F, w, a, t, rmax=0.040)
        st = section_stats(pts, w, a, t, e1, e2)
        if st:
            out["paddle_sections"].append(st)
    out["band_roll"] = band_roll_structure(mt, f"elbow_{side}", e, a, e1, e2)
    return out


def main():
    mt = MonkeyTarget(
        birth_path=str(BASE / "inputs" / "monkey_birth.bin"),
        pack_path=str(BASE / "inputs" / "monkey_joints.bin"),
    )
    assert mt.birth_sha.lower() == EXPECT_SHA["birth"], mt.birth_sha
    assert mt.pack_sha.lower() == EXPECT_SHA["pack"], mt.pack_sha
    print("input hashes match MANIFEST (birth 550a5b3e..., pack 74b3ab04...)")

    stations = [-5, 4, 8, 12, 16, 20, 24, 28, 32, 40, 48]
    out = {
        "inputs": {"birth_sha256": mt.birth_sha, "pack_sha256": mt.pack_sha,
                   "module_copy": "work/mesh_target_c3.py (baseline mesh_target.py verbatim, paths repointed)"},
        "right": arm_pipeline(mt, "R", stations),
        "left": arm_pipeline(mt, "L", stations),
        "method_note": (
            "sections = exact triangle-plane intersection segment endpoints within rmax of "
            "the axis line (no slab bias, no bridging); principal azimuths mod 180; "
            "bootstrap = 200 point resamples; both ulna-axis DIRECTIONS (+a/-a) leave every "
            "reported magnitude and mod-180 line invariant by construction (a sign flip "
            "negates both e1,e2 projections and shifts azimuths by 180 deg = identity on "
            "mod-180 lines; per-line distances unchanged)"
        ),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")

    for side in ("right", "left"):
        print(f"--- {side} forearm (axis len {out[side]['axis_len_m']*1000:.1f} mm) ---")
        for s in out[side]["sections"]:
            print(f"  t={s['t_mm']:6.1f} mm n={s['n_pts']:4d} ecc={s['eccentricity_ratio_l1_over_l2']:5.2f} "
                  f"az1={s['principal_azimuth_deg_mod180']:7.2f} (boot std {s['boot_principal_azimuth_circstd_deg']:4.1f}) "
                  f"off={s['centroid_offset_mm']:5.2f}mm az_off={s['centroid_offset_azimuth_deg']:7.2f}")
        print(f"  elbow band roll vertex: top perp {out[side]['band_roll']['top'][0]['perp_mm']:.2f} mm "
              f"az {out[side]['band_roll']['top'][0]['azimuth_deg']:.1f} deg; "
              f"d1/d2 gap {out[side]['band_roll']['gap_ratio_d1_over_d2']:.3f}")
        print("  paddle sections:")
        for s in out[side]["paddle_sections"]:
            print(f"    t={s['t_mm']:6.1f} mm n={s['n_pts']:4d} ecc={s['eccentricity_ratio_l1_over_l2']:6.1f} "
                  f"az1={s['principal_azimuth_deg_mod180']:7.2f} (boot std {s['boot_principal_azimuth_circstd_deg']:4.1f}) "
                  f"off={s['centroid_offset_mm']:5.2f}mm az_off={s['centroid_offset_azimuth_deg']:7.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
