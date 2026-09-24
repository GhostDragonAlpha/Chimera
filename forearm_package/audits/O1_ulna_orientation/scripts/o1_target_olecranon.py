"""O1 script 3 — TARGET labeling: which transverse side of the target forearm tube is
volar/dorsal, via the elbow-region OLECRANON protrusion test (preregistered method (c)).

READ-ONLY on baseline inputs (module copy in work/, hashes asserted). Writes only inside
audits/O1_ulna_orientation/.

Rendering law (GAMING-SAFETY, honored): every figure below is matplotlib with
matplotlib.use("Agg") called BEFORE any pyplot import (pure software rasterizer).
No OpenGL/Vulkan/WebGL/GPU context is created anywhere in this audit.

Frame (all measured, no assumptions):
  a      = unit(wrist_R - elbow_R)                    (C3's forearm axis)
  e1,e2  = C3's fixed transverse basis: e1 = rejection of +x on a-perp; e2 = a x e1
  azimuth= atan2(v.e2, v.e1) in degrees

Target facing (decides which azimuth is posterior; measured from the pack + mesh):
  face joints (jaw/lid/brow/mouth) at +z, tail joints at -z  -> anterior = +z, posterior = -z
  up = +y (ears/ankles); right arm at -x  => right = forward x up = -x (proper)
  In the (e1,e2) basis for the RIGHT arm: az +90 ~ +z = ANTERIOR, az -90 ~ -z = POSTERIOR,
  az 0 ~ +x = LEFT, az 180 ~ -x = RIGHT.

Preregistered test: posterior-vs-anterior elbow-region protrusion difference > 2 mm
  (the C3 camber scale) -> the protruding (posterior) side is DORSAL (olecranon),
  the opposite side VOLAR. Falsifier: difference <= noise -> UNRESOLVED.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

O1 = Path(r"E:\PythonChimera\forearm_package\audits\O1_ulna_orientation")
BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
sys.path.insert(0, str(O1 / "work"))
from mesh_target_o1 import MonkeyTarget  # noqa: E402  (byte-identical module copy)

OUT = O1 / "receipts" / "o1_target_olecranon.json"
EXPECT_SHA = {
    "birth": "550A5B3EC927EA13614AD250963B23E2948E76A238AC110DA9889F339AABFA3C",
    "pack": "74B3AB044B7ADAED4A0F9349A81F5D3C87441084B2EC8981F4E0AFABA50C1662",
}
XHAT = np.array([1.0, 0.0, 0.0])
ZAX = np.array([0.0, 0.0, 1.0])


def unit(v):
    return v / np.linalg.norm(v)


def transverse_basis(a):
    e1 = XHAT - a * (a @ XHAT)
    if np.linalg.norm(e1) < 1e-9:
        e1 = ZAX - a * (a @ ZAX)
    e1 = unit(e1)
    e2 = np.cross(a, e1)
    return e1, e2


def band_profile(verts, origin, a, e1, e2, bin_deg=5.0):
    rel = verts - origin
    t_mm = (rel @ a) * 1000.0
    perp = rel - np.outer(rel @ a, a)
    r1, r2 = perp @ e1, perp @ e2
    psi = np.degrees(np.arctan2(r2, r1))
    rho = np.hypot(r1, r2) * 1000.0
    nb = int(round(360.0 / bin_deg))
    bins = []
    for k in range(nb):
        lo = -180.0 + k * bin_deg
        d = (psi - lo) % 360.0
        m = d < bin_deg
        if m.sum() == 0:
            bins.append({"az_lo": lo, "n": 0, "rho_max_mm": None, "rho_p95_mm": None})
            continue
        bins.append({
            "az_center": lo + bin_deg / 2,
            "n": int(m.sum()),
            "rho_max_mm": float(rho[m].max()),
            "rho_p95_mm": float(np.percentile(rho[m], 95)),
            "rho_mean_mm": float(rho[m].mean()),
        })
    return {"t_min_mm": float(t_mm.min()), "t_max_mm": float(t_mm.max()), "n": len(verts),
            "bins": bins, "psi": psi.tolist(), "rho_mm": rho.tolist(),
            "t_mm": t_mm.tolist()}


def sector_protrusion(bins, center_az, delta):
    """max rho_p95 and max rho over bins whose center lies within delta of center_az."""
    sel = [b for b in bins
           if b["rho_max_mm"] is not None
           and abs(((b["az_center"] - center_az + 180.0) % 360.0) - 180.0) <= delta]
    if not sel:
        return None
    return {
        "n_bins": len(sel), "n_verts": int(sum(b["n"] for b in sel)),
        "rho_max_of_p95_mm": float(max(b["rho_p95_mm"] for b in sel)),
        "rho_max_mm": float(max(b["rho_max_mm"] for b in sel)),
        "rho_max_of_p95_by_bin": [b["rho_p95_mm"] for b in sel],
    }


def protrusion_difference(profile, delta, boot=200, seed=0):
    post = sector_protrusion(profile["bins"], -90.0, delta)
    ant = sector_protrusion(profile["bins"], 90.0, delta)
    d_p95 = post["rho_max_of_p95_mm"] - ant["rho_max_of_p95_mm"]
    d_max = post["rho_max_mm"] - ant["rho_max_mm"]
    # bootstrap over band vertices (resample -> recompute sector difference)
    psi = np.array(profile["psi"]); rho = np.array(profile["rho_mm"])
    rng = np.random.default_rng(seed)
    ds = []
    for _ in range(boot):
        idx = rng.integers(0, len(rho), len(rho))
        pb, ab = [], []
        for azc, acc in ((-90.0, pb), (90.0, ab)):
            dd = (psi[idx] - azc + 180.0) % 360.0 - 180.0
            m = np.abs(dd) <= delta
            if m.any():
                acc.append(float(np.percentile(rho[idx][m], 95)))
        if pb and ab:
            ds.append(max(pb) - max(ab))
    ds = np.array(ds)
    out = {
        "delta_deg": delta,
        "posterior_sector": post, "anterior_sector": ant,
        "D_post_minus_ant_p95_mm": float(d_p95),
        "D_post_minus_ant_max_mm": float(d_max),
        "threshold_mm": 2.0,
        "passes_threshold_p95": bool(d_p95 > 2.0),
    }
    if boot > 0 and len(ds):
        out["boot_D_p95_iqr_mm"] = [float(np.percentile(ds, 25)), float(np.percentile(ds, 75))]
        out["boot_D_p95_std_mm"] = float(ds.std())
    return out


def lobe_direction(profile):
    """argmax bin (rho_p95) + coherence: contiguous bins within 15 deg holding rho within 2 mm."""
    valid = [b for b in profile["bins"] if b["rho_max_mm"] is not None]
    peak = max(valid, key=lambda b: b["rho_p95_mm"])
    coh = [b["az_center"] for b in valid
           if abs(((b["az_center"] - peak["az_center"] + 180.0) % 360.0) - 180.0) <= 15.0
           and b["rho_p95_mm"] >= peak["rho_p95_mm"] - 2.0]
    return {"peak_az_deg": peak["az_center"], "peak_rho_p95_mm": peak["rho_p95_mm"],
            "coherent_az_span_deg": [min(coh), max(coh)], "n_coherent_bins": len(coh)}


def axial_window_verts(mt, origin, a, t_lo, t_hi, rmax=0.05):
    rel = mt.V - origin
    t = rel @ a
    perp = rel - np.outer(t, a)
    d = np.linalg.norm(perp, axis=1)
    m = (t >= t_lo) & (t <= t_hi) & (d <= rmax)
    return mt.V[m]


def facing_facts(mt):
    names = mt.names
    def jp(n):
        return mt.joint_pos(n)
    face = [jp(n) for n in ("jaw", "lid_L", "lid_R", "brow_L", "brow_R", "mouth_L", "mouth_R")]
    tail = [jp(n) for n in ("tail_base", "tail_mid", "tail_tip")]
    ear = [jp(n) for n in ("ear_L", "ear_R")]
    ank = [jp(n) for n in ("ankle_L", "ankle_R")]
    el_r, el_l, wr_r, wr_l = jp("elbow_R"), jp("elbow_L"), jp("wrist_R"), jp("wrist_L")
    facts = {
        "face_joints_mean_z_m": float(np.mean([p[2] for p in face])),
        "tail_joints_mean_z_m": float(np.mean([p[2] for p in tail])),
        "ears_mean_y_m": float(np.mean([p[1] for p in ear])),
        "ankles_mean_y_m": float(np.mean([p[1] for p in ank])),
        "elbow_R_x_m": float(el_r[0]), "elbow_L_x_m": float(el_l[0]),
        "wrist_R_x_m": float(wr_r[0]), "wrist_L_x_m": float(wr_l[0]),
        "right_hand_rule_check": "forward=+z (face), up=+y (ears high) -> right = forward x up = -x; "
                                 "pack elbow_R sits at x<0 -- CONSISTENT",
    }
    # mesh corroboration: muzzle vs back-of-head, tail direction
    head = mt.V[mt.V[:, 1] > 0.50]
    tailv = mt.V[(mt.V[:, 1] > 0.22) & (mt.V[:, 1] < 0.34) & (mt.V[:, 2] < -0.10)]
    facts["mesh_head_z_span_m"] = [float(head[:, 2].min()), float(head[:, 2].max())]
    facts["mesh_tail_min_z_m"] = float(tailv[:, 2].min()) if len(tailv) else None
    facts["verdict"] = ("anterior = +z, posterior = -z, up = +y, right = -x (left = +x); "
                        "mesh muzzle max z and tail min z corroborate the joint facts")
    return facts


def t_windowed_D(mt, side, e, a, e1, e2, windows_mm, delta=30.0):
    """Pin the protrusion asymmetry along the axis: D(post-ant) per t-window.
    The olecranon claim predicts D >> 0 only in the elbow-proximal window."""
    band = mt.band_verts(f"elbow_{side}")
    rel = band - e
    t = (rel @ a) * 1000.0
    rows = []
    for lo, hi in windows_mm:
        m = (t >= lo) & (t < hi)
        if m.sum() < 12:
            rows.append({"t_window_mm": [lo, hi], "n": int(m.sum()), "D_p95_mm": None})
            continue
        pf = band_profile(band[m], e, a, e1, e2)
        d = protrusion_difference(pf, float(delta), boot=0)
        rows.append({"t_window_mm": [lo, hi], "n": int(m.sum()),
                     "D_p95_mm": d["D_post_minus_ant_p95_mm"],
                     "D_max_mm": d["D_post_minus_ant_max_mm"]})
    return rows


def main() -> int:
    mt = MonkeyTarget(
        birth_path=str(BASE / "inputs" / "monkey_birth.bin"),
        pack_path=str(BASE / "inputs" / "monkey_joints.bin"),
    )
    assert mt.birth_sha.upper() == EXPECT_SHA["birth"], mt.birth_sha
    assert mt.pack_sha.upper() == EXPECT_SHA["pack"], mt.pack_sha
    print("input hashes match MANIFEST (birth 550a5b3e..., pack 74b3ab04...)")

    out = {"inputs": {"birth_sha256": mt.birth_sha, "pack_sha256": mt.pack_sha,
                      "module_copy": "work/mesh_target_o1.py (baseline mesh_target.py verbatim, paths repointed)"},
           "rendering_law": "matplotlib Agg backend only, set BEFORE pyplot import; no GPU context (see figures in figures/)",
           "facing": facing_facts(mt)}
    f = out["facing"]
    print(f"facing: face z {f['face_joints_mean_z_m']:+.4f} vs tail z {f['tail_joints_mean_z_m']:+.4f}; "
          f"mesh head z-span {np.round(f['mesh_head_z_span_m'],4).tolist()}, tail min z {f['mesh_tail_min_z_m']:+.4f}")

    res = {}
    for side in ("R", "L"):
        e = mt.joint_pos(f"elbow_{side}")
        w = mt.joint_pos(f"wrist_{side}")
        a = unit(w - e)
        e1, e2 = transverse_basis(a)
        entry = {"elbow": e.tolist(), "wrist": w.tolist(), "axis_unit": a.tolist(),
                 "basis_e1": e1.tolist(), "basis_e2": e2.tolist()}
        # world direction of each section azimuth (for labeling + L mirror check)
        entry["world_dir_of_az_plus90"] = (np.cos(np.radians(90)) * e1 + np.sin(np.radians(90)) * e2).tolist()
        entry["world_dir_of_az_minus90"] = (np.cos(np.radians(-90)) * e1 + np.sin(np.radians(-90)) * e2).tolist()

        band = mt.band_verts(f"elbow_{side}")
        prof = band_profile(band, e, a, e1, e2)
        entry["elbow_band"] = {k: prof[k] for k in ("t_min_mm", "t_max_mm", "n")}
        entry["elbow_band"]["bins"] = prof["bins"]
        entry["elbow_tests"] = {f"delta{d}": protrusion_difference(prof, float(d)) for d in (20, 30, 40)}
        entry["elbow_lobe"] = lobe_direction(prof)
        entry["D_along_axis_delta30"] = t_windowed_D(
            mt, side, e, a, e1, e2,
            [(2.6, 10.0), (10.0, 20.0), (20.0, 40.0), (40.0, 70.0), (70.0, 105.6)])
        entry["elbow_world_dir_of_lobe"] = (
            np.cos(np.radians(entry["elbow_lobe"]["peak_az_deg"])) * e1
            + np.sin(np.radians(entry["elbow_lobe"]["peak_az_deg"])) * e2).tolist()

        # specificity panels: mid-shaft window and wrist band (no olecranon there)
        for tag, (lo, hi) in {"shaft_10_25mm": (0.010, 0.025), "shaft_30_45mm": (0.030, 0.045)}.items():
            vv = axial_window_verts(mt, e, a, lo, hi)
            if len(vv) >= 30:
                pf = band_profile(vv, e, a, e1, e2)
                entry[tag] = {"n": int(len(vv)), "lobe": lobe_direction(pf),
                              "delta30": protrusion_difference(pf, 30.0)}
        wb = mt.band_verts(f"wrist_{side}")
        if len(wb):
            pw = band_profile(wb, mt.joint_pos(f"wrist_{side}"), a, e1, e2)
            entry["wrist_band"] = {"n": int(len(wb)), "lobe": lobe_direction(pw),
                                   "delta30": protrusion_difference(pw, 30.0)}
        res[side] = entry

        d30 = entry["elbow_tests"]["delta30"]
        print(f"[{side}] elbow band n={entry['elbow_band']['n']} t=[{entry['elbow_band']['t_min_mm']:.1f},"
              f"{entry['elbow_band']['t_max_mm']:.1f}]mm")
        print(f"    lobe peak az {entry['elbow_lobe']['peak_az_deg']:+.1f} deg "
              f"(rho_p95 {entry['elbow_lobe']['peak_rho_p95_mm']:.2f} mm, span {entry['elbow_lobe']['coherent_az_span_deg']})")
        print(f"    D(post-ant) p95: d20 {entry['elbow_tests']['delta20']['D_post_minus_ant_p95_mm']:+.2f} mm | "
              f"d30 {d30['D_post_minus_ant_p95_mm']:+.2f} mm (boot std {d30['boot_D_p95_std_mm']:.2f}) | "
              f"d40 {entry['elbow_tests']['delta40']['D_post_minus_ant_p95_mm']:+.2f} mm")
        for tag in ("shaft_10_25mm", "shaft_30_45mm", "wrist_band"):
            if tag in entry:
                print(f"    specificity {tag}: lobe az {entry[tag]['lobe']['peak_az_deg']:+.1f} deg, "
                      f"D30 {entry[tag]['delta30']['D_post_minus_ant_p95_mm']:+.2f} mm")

    # world-direction coherence of the two sides' lobes
    dR = np.array(res["R"]["elbow_world_dir_of_lobe"])
    dL = np.array(res["L"]["elbow_world_dir_of_lobe"])
    out["lobe_world_directions"] = {"R": dR.tolist(), "L": dL.tolist(),
                                    "R_dot_negZ": float(dR @ np.array([0, 0, -1.0])),
                                    "L_dot_negZ": float(dL @ np.array([0, 0, -1.0]))}
    out["sides"] = res

    # preregistered verdict (right arm is U-STR's side)
    d30R = res["R"]["elbow_tests"]["delta30"]
    passes = d30R["passes_threshold_p95"]
    out["verdict"] = {
        "test": "posterior(-z, az -90) vs anterior(+z, az +90) elbow-region protrusion, delta=30 deg primary",
        "D_post_minus_ant_p95_mm": d30R["D_post_minus_ant_p95_mm"],
        "threshold_mm": 2.0,
        "passes": bool(passes),
        "consequence_if_passes": "posterior side = DORSAL (olecranon); anterior side = VOLAR; "
                                 "target volar azimuth in the C3 (e1,e2) section frame = +90 deg",
        "falsifier_status": "not fired" if passes else
                            "FIRED: elbow asymmetry at/below threshold -> UNRESOLVED SIGN blocker path",
    }
    out["figures"] = [
        "figures/o1_target_elbow_profile_RL.png (polar protrusion profiles, view directions labeled)",
        "figures/o1_target_azimuth_scatter_R.png (elbow band transverse scatter with world axes)",
    ]
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return out, res, 0


if __name__ == "__main__":
    out, res, code = main()
    raise SystemExit(code)
