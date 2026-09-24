"""O1 script 3b — DIRECTED section test (decisive form of preregistered method (c)).

The rig's elbow_R vertex band extends t=[2.6,105.6] mm (its distal part is proximal-paw
skin; its proximal windows are too sparse for sector statistics), so the band-based
sector test is not reliable for the elbow region. This script replaces it with EXACT
triangle-plane cross-sections (the C3-S2 method: intersection segment endpoints, no
vertex-slab bias) and measures the DIRECTED radial profile rho(psi) at proximal
stations along the forearm axis:

  rho(psi; t) = max radius of the section curve within the 5-deg azimuth bin psi,
  D(t)        = [max rho in the posterior sector (az -90 +-30 deg, world -z)]
              - [max rho in the anterior sector (az +90 +-30 deg, world +z)].

Olecranon claim (preregistered): the posterior surface protrudes at the elbow:
D(t) > 2 mm (the C3 camber scale) for stations near the elbow. Falsifier: no station
near the elbow with D > 2 mm (bootstrap noise floor reported per station).

Reads ONLY baseline inputs through the work/ module copy (hash-asserted). Writes only
inside audits/O1_ulna_orientation/. Figures: matplotlib Agg (set before pyplot import),
no GPU context.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

O1 = Path(r"E:\PythonChimera\forearm_package\audits\O1_ulna_orientation")
BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
sys.path.insert(0, str(O1 / "work"))
from mesh_target_o1 import MonkeyTarget  # noqa: E402

OUT = O1 / "receipts" / "o1_target_sections_directed.json"
EXPECT_SHA = {
    "birth": "550A5B3EC927EA13614AD250963B23E2948E76A238AC110DA9889F339AABFA3C",
    "pack": "74B3AB044B7ADAED4A0F9349A81F5D3C87441084B2EC8981F4E0AFABA50C1662",
}
XHAT = np.array([1.0, 0.0, 0.0])
ZAX = np.array([0.0, 0.0, 1.0])
STATIONS_MM = [-8, -5, -2, 0, 2, 4, 6, 8, 10, 12, 16, 20, 30, 48]
DELTA = 30.0
BIN = 5.0


def unit(v):
    return v / np.linalg.norm(v)


def transverse_basis(a):
    e1 = XHAT - a * (a @ XHAT)
    if np.linalg.norm(e1) < 1e-9:
        e1 = ZAX - a * (a @ ZAX)
    e1 = unit(e1)
    e2 = np.cross(a, e1)
    return e1, e2


def section_points(V, F, origin, a, t, rmax=0.045):
    """Exact triangle-plane intersection segment endpoints within rmax of the axis line
    (method identical to C3-S2 scripts/c3_target_sections.py::section_points)."""
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


def directed_profile(pts, cplane, e1, e2, bin_deg=BIN):
    rel = pts - cplane
    r1, r2 = rel @ e1, rel @ e2
    psi = np.degrees(np.arctan2(r2, r1))
    rho = np.hypot(r1, r2) * 1000.0
    nb = int(round(360.0 / bin_deg))
    prof = np.full(nb, np.nan)
    for k in range(nb):
        lo = -180.0 + k * bin_deg
        m = ((psi - lo) % 360.0) < bin_deg
        if m.any():
            prof[k] = rho[m].max()
    return prof, psi, rho


def sector_max(prof, center_az, delta=DELTA):
    az_centers = np.array([-180.0 + (k + 0.5) * BIN for k in range(len(prof))])
    d = np.abs((az_centers - center_az + 180.0) % 360.0 - 180.0)
    m = (d <= delta) & ~np.isnan(prof)
    return float(np.nanmax(prof[m])) if m.any() else None


def station_stats(pts, origin, a, t, e1, e2, boot=200, seed=0):
    if len(pts) < 8:
        return {"t_mm": t * 1000.0, "n": int(len(pts)), "usable": False}
    cplane = origin + a * t
    prof, psi, rho = directed_profile(pts, cplane, e1, e2)
    post = sector_max(prof, -90.0)
    ant = sector_max(prof, +90.0)
    D = post - ant
    rng = np.random.default_rng(seed)
    Ds, lobes = [], []
    az_centers = np.array([-180.0 + (k + 0.5) * BIN for k in range(len(prof))])
    for _ in range(boot):
        idx = rng.integers(0, len(rho), len(rho))
        pb, ab = [], []
        for azc, acc in ((-90.0, pb), (90.0, ab)):
            dd = np.abs((psi[idx] - azc + 180.0) % 360.0 - 180.0)
            m = dd <= DELTA
            if m.any():
                acc.append(float(rho[idx][m].max()))
        if pb and ab:
            Ds.append(max(pb) - max(ab))
        k = int(np.nanargmax(prof))
        lobes.append(az_centers[k])
    Ds = np.array(Ds)
    kpk = int(np.nanargmax(prof))
    return {
        "t_mm": t * 1000.0, "n": int(len(pts)), "usable": True,
        "rho_post_max_mm": post, "rho_ant_max_mm": ant,
        "D_post_minus_ant_mm": float(D),
        "boot_D_iqr_mm": [float(np.percentile(Ds, 25)), float(np.percentile(Ds, 75))],
        "boot_D_std_mm": float(Ds.std()),
        "D_above_2mm": bool(D > 2.0),
        "lobe_az_deg": float(az_centers[kpk]),
        "lobe_rho_mm": float(prof[kpk]),
        "profile_rho_max_by_bin_mm": [None if np.isnan(v) else float(v) for v in prof],
    }


def main() -> int:
    mt = MonkeyTarget(
        birth_path=str(BASE / "inputs" / "monkey_birth.bin"),
        pack_path=str(BASE / "inputs" / "monkey_joints.bin"),
    )
    assert mt.birth_sha.upper() == EXPECT_SHA["birth"], mt.birth_sha
    assert mt.pack_sha.upper() == EXPECT_SHA["pack"], mt.pack_sha
    print("input hashes match MANIFEST")

    out = {"inputs": {"birth_sha256": mt.birth_sha, "pack_sha256": mt.pack_sha},
           "method": ("exact triangle-plane sections (C3-S2 method), directed radial profile "
                      "rho(psi) = max radius per 5-deg bin; D(t) = posterior sector max "
                      "(az -90+-30, world -z) - anterior sector max (az +90+-30, world +z); "
                      "bootstrap = 200 point resamples per station"),
           "rendering_law": "matplotlib Agg only (set before pyplot import), no GPU context",
           "sides": {}}

    for side in ("R", "L"):
        e = mt.joint_pos(f"elbow_{side}")
        w = mt.joint_pos(f"wrist_{side}")
        a = unit(w - e)
        e1, e2 = transverse_basis(a)
        rows = []
        for tmm in STATIONS_MM:
            pts = section_points(mt.V, mt.F, e, a, tmm / 1000.0)
            st = station_stats(pts, e, a, tmm / 1000.0, e1, e2)
            rows.append(st)
            if st["usable"]:
                print(f"[{side}] t={st['t_mm']:+6.1f} n={st['n']:3d} "
                      f"post {st['rho_post_max_mm']:6.2f} ant {st['rho_ant_max_mm']:6.2f} "
                      f"D={st['D_post_minus_ant_mm']:+6.2f} (boot std {st['boot_D_std_mm']:4.2f}) "
                      f"lobe {st['lobe_az_deg']:+7.1f}")
        out["sides"][side] = {"axis_unit": a.tolist(), "e1": e1.tolist(), "e2": e2.tolist(),
                              "elbow": e.tolist(), "stations": rows}
        out["sides"][side]["max_D_elbow_region"] = max(
            (r["D_post_minus_ant_mm"] for r in rows if r["usable"] and r["t_mm"] <= 16.0),
            default=None)

    # preregistered verdict on the right (U-STR) side
    R = out["sides"]["R"]["stations"]
    elbow_rows = [r for r in R if r["usable"] and r["t_mm"] <= 16.0]
    best = max(elbow_rows, key=lambda r: r["D_post_minus_ant_mm"])
    any_pass = any(r["D_above_2mm"] for r in elbow_rows)
    out["verdict"] = {
        "side": "R",
        "best_elbow_station": best,
        "any_elbow_station_D_above_2mm": bool(any_pass),
        "threshold_mm": 2.0,
        "passes": bool(any_pass),
        "consequence_if_passes": "posterior (az -90, world -z) = DORSAL; anterior (az +90, world +z) = VOLAR; "
                                 "target volar azimuth in the C3 (e1,e2) section frame = +90 deg",
        "falsifier_status": "not fired" if any_pass else "FIRED -> UNRESOLVED SIGN blocker path",
    }
    print("verdict:", json.dumps({k: v for k, v in out["verdict"].items() if k != "best_elbow_station"}))
    print("best elbow station:", {k: v for k, v in best.items() if not k.startswith("profile")})
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return out, 0


if __name__ == "__main__":
    out, code = main()
    raise SystemExit(code)
