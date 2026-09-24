"""O2 script 1 — SOURCE palm sign: 5 named tendon sites vs the 27-geom palm plane.

Reads ONLY baseline_snapshot/source_xml/chimanoid.xml (stdlib ElementTree).
Construction semantics replicated from the C3 receipt (intake walk
world = parent_world + parent_rot @ pos; rot = parent_rot @ quat_to_rotmat(quat);
plane = centroid + SVD of centered points; normal = last right singular vector,
UNDIRECTED).  The 27 skeleton geoms construct the plane; the 5 sites NEVER enter
the construction (C3 direction A, rms 8.88 mm <= plane's own 10.66 mm).

FROZEN METHOD (O2 brief, preregistered before evaluation):
  per-site SIGNED offset along the plane normal; compartment semantics demand
  FCR-P3/FCU-P4 (flexors, volar) on one side and ECRB-P4/ECRL-P4/ECU-P6
  (extensors, dorsal) on the other; a CLEAN split fixes the source palm direction.
FROZEN FALSIFIER: any extensor site on the palm side or vice versa -> report numbers.
FROZEN STOP RULE: mixed compartment signs -> UNRESOLVED SIGN = BLOCKER; do not force.

Diagnostics recorded alongside the frozen test (reported as diagnosis, never as a
replacement decision rule):
  - decomposition of each offset into palmar-dorsal (z) term vs in-plane tilt term
  - the same offsets against the 13 carpals+metacarpals palm-subset plane
  - raw local z of the sites (fully construction-free)
  - leave-one-geom-out jackknife of the whole pipeline (27 refits)
  - L/R mirror (hand_l) reproduction

Figures: matplotlib with Agg BEFORE pyplot import (CPU-only; gaming-safety rule).
Writes receipts/o2_source_sign.json.  No writes outside audits/O2_hand_orientation/.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gaming-safety: software renderer, BEFORE pyplot import
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
XML = BASE / "source_xml" / "chimanoid.xml"
HERE = Path(r"E:\PythonChimera\forearm_package\audits\O2_hand_orientation")
OUT = HERE / "receipts" / "o2_source_sign.json"
FIGDIR = HERE / "figures"

FLEXORS = ["FCR-P3", "FCU-P4"]          # volar compartment (frozen external evidence)
EXTENSORS = ["ECRB-P4", "ECRL-P4", "ECU-P6"]  # dorsal compartment (frozen external evidence)
HAND_SITES = ["ECRL-P4", "ECRB-P4", "ECU-P6", "FCR-P3", "FCU-P4"]  # C3 receipt order


def _vec(text):
    return np.array([float(v) for v in (text or "").split()], dtype=np.float64)


def _quat_to_rotmat(q):
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def walk(elem, parent_world, parent_rot, bodies, sites, geoms):
    name = elem.get("name")
    pos = _vec(elem.get("pos", "0 0 0"))
    quat = _vec(elem.get("quat", "1 0 0 0"))
    rot = parent_rot @ _quat_to_rotmat(quat)
    world = parent_world + parent_rot @ pos
    bodies[name] = world
    for s in elem.findall("site"):
        sites[s.get("name")] = {"body": name, "pos_local": _vec(s.get("pos", "0 0 0"))}
    for g in elem.findall("geom"):
        geoms.append(
            {
                "name": g.get("name"),
                "type": g.get("type"),
                "body": name,
                "pos_local": _vec(g.get("pos", "0 0 0")),
                "has_pos_attr": g.get("pos") is not None,
            }
        )
    for child in elem.findall("body"):
        walk(child, world, rot, bodies, sites, geoms)


def unit(v):
    return v / np.linalg.norm(v)


def best_fit_plane(pts):
    """centroid, normal (unit, undirected), singular values, signed perp distances."""
    c = pts.mean(axis=0)
    X = pts - c
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    n = Vt[-1]
    d = X @ n
    return c, n, S, d


def site_offsets(P27, names27, site_pts, site_names, site_locals, sfx=""):
    """27-geom plane + per-site signed offsets, with z/tilt decomposition."""
    c, n, S, d27 = best_fit_plane(P27)
    off = {}
    decomp = {}
    for p, sn, loc in zip(site_pts, site_names, site_locals):
        rel = p - c
        o = float(rel @ n)
        z_term = float(n[2] * (loc[2] - c[2]))          # palmar-dorsal part (local z)
        tilt_term = float(o - z_term)                    # in-plane position x plane tilt
        off[sn] = o
        decomp[sn] = {"total_m": o, "z_term_m": z_term, "tilt_term_m": tilt_term}
    # 13-geom palm subset plane (diagnosis only)
    palm_names = [
        "pisiform", "lunate", "scaphoid", "triquetrum", "hamate", "capitate",
        "trapezoid", "trapezium", "1mc", "2mc", "3mc", "4mc", "5mc",
    ]
    palm_names = [nm + sfx for nm in palm_names] if sfx else palm_names
    P13 = np.array([P27[names27.index(nm)] for nm in palm_names])
    c13, n13, S13, _ = best_fit_plane(P13)
    off13 = {sn: float((p - c13) @ n13) for p, sn in zip(site_pts, site_names)}
    return {
        "centroid_local": c.tolist(), "normal_unit_undirected": n.tolist(),
        "singular_values": [float(s) for s in S],
        "geom_resid_rms_m": float(np.sqrt((d27 ** 2).mean())),
        "geom_resid_max_m": float(np.abs(d27).max()),
        "site_offsets_m": off, "site_offset_decomposition_m": decomp,
        "palm13_centroid_local": c13.tolist(),
        "palm13_normal_unit_undirected": n13.tolist(),
        "palm13_site_offsets_m": off13,
        "angle_n27_n13_deg": float(np.degrees(np.arccos(min(1.0, abs(float(n @ n13)))))),
    }


def split_verdict(off_by_name):
    """FROZEN criterion: clean split iff flexors share one sign, extensors the other."""
    fl = {k: off_by_name[k] for k in FLEXORS}
    ex = {k: off_by_name[k] for k in EXTENSORS}
    fl_signs = {k: (1 if v > 0 else -1 if v < 0 else 0) for k, v in fl.items()}
    ex_signs = {k: (1 if v > 0 else -1 if v < 0 else 0) for k, v in ex.items()}
    clean = len(set(fl_signs.values())) == 1 and len(set(ex_signs.values())) == 1 \
        and set(fl_signs.values()) != set(ex_signs.values())
    # falsifier evaluation for BOTH possible palm assignments
    viol_palm_pos = {k: v for k, v in ex.items() if v > 0}     # extensor on + side (palm := +)
    viol_palm_neg = {k: v for k, v in ex.items() if v < 0}     # extensor on - side (palm := -)
    violP = {**{f"flexor:{k}": v for k, v in fl.items() if v < 0}, **{f"extensor:{k}": v for k, v in viol_palm_neg.items()}}
    violN = {**{f"flexor:{k}": v for k, v in fl.items() if v > 0}, **{f"extensor:{k}": v for k, v in viol_palm_pos.items()}}
    return {
        "flexor_offsets_m": fl, "extensor_offsets_m": ex,
        "clean_split_frozen_criterion": bool(clean),
        "if_palm_is_plus_side_violations_m": violP,
        "if_palm_is_minus_side_violations_m": violN,
    }


def jackknife_split(P27, names27, site_pts, site_names, verdict_names):
    """Leave-one-geom-out: refit plane, recompute the 5 offsets. 27 refits.
    verdict_names: bare (unsuffixed) names in the same order, for split_verdict."""
    per_site = {vn: [] for vn in verdict_names}
    clean_counts = 0
    for i in range(len(P27)):
        sub = np.delete(P27, i, axis=0)
        c, n, _, _ = best_fit_plane(sub)
        off = {vn: float((p - c) @ n) for p, vn in zip(site_pts, verdict_names)}
        for vn, v in off.items():
            per_site[vn].append(v)
        if split_verdict(off)["clean_split_frozen_criterion"]:
            clean_counts += 1
    return {
        "n_refits": len(P27),
        "per_site_offset_min_m": {k: float(min(v)) for k, v in per_site.items()},
        "per_site_offset_max_m": {k: float(max(v)) for k, v in per_site.items()},
        "refits_with_clean_split": clean_counts,
        "omitted_geom_of_worst_flip": None,
    }


def main() -> int:
    root = ET.parse(str(XML)).getroot()
    wb = root.find("worldbody")
    bodies, sites, geoms = {}, {}, []
    for b in wb.findall("body"):
        walk(b, np.zeros(3), np.eye(3), bodies, sites, geoms)

    out = {"inputs": {"xml": str(XML)}, "frozen": {
        "flexors_volar": FLEXORS, "extensors_dorsal": EXTENSORS,
        "criterion": "clean split: both flexors one side, all three extensors the other",
        "falsifier": "any extensor on the palm side or vice versa -> report numbers",
        "stop_rule": "mixed compartment signs -> UNRESOLVED SIGN = BLOCKER; do not force",
    }}

    # origin cross-check vs C3 receipt (same walk semantics)
    out["origin_crosscheck"] = {
        "hand_r_world": bodies["hand_r"].tolist(),
        "hand_l_world": bodies["hand_l"].tolist(),
        "c3_quoted_hand_r": [-0.0731, 0.532647, 0.202699],
    }

    res = {}
    for side, hname, sfx in (("right", "hand_r", ""), ("left", "hand_l", "_l")):
        hand_geoms = [g for g in geoms if g["body"] == hname and g["type"] == "mesh"]
        assert len(hand_geoms) == 27, (side, len(hand_geoms))
        names27 = [g["name"] for g in hand_geoms]
        P27 = np.array([g["pos_local"] for g in hand_geoms])
        # left-hand site names embed the side before the phase: ECRL_l-P4
        snames = [n.replace("-P", f"{sfx}-P") for n in HAND_SITES] if sfx else list(HAND_SITES)
        site_pts = np.array([sites[sn]["pos_local"] for sn in snames])
        site_locals = [sites[sn]["pos_local"].copy() for sn in snames]

        r = site_offsets(P27, names27, site_pts, snames, site_locals, sfx=sfx)
        # strip side suffix for the shared report keys
        r["site_offsets_m"] = {k.replace(f"{sfx}-P", "-P"): v for k, v in r["site_offsets_m"].items()}
        r["site_offset_decomposition_m"] = {
            k.replace(f"{sfx}-P", "-P"): v for k, v in r["site_offset_decomposition_m"].items()}
        r["palm13_site_offsets_m"] = {
            k.replace(f"{sfx}-P", "-P"): v for k, v in r["palm13_site_offsets_m"].items()}
        r["raw_local_z_m"] = {
            n.replace(f"{sfx}-P", "-P"): float(p[2]) for p, n in zip(site_pts, snames)}
        r["split_verdict_frozen"] = split_verdict(r["site_offsets_m"])
        jk = jackknife_split(P27, names27, site_pts, snames, HAND_SITES)
        r["jackknife"] = jk
        r["geom_names"] = names27
        r["geom_missing_pos_attr"] = [g["name"] for g in hand_geoms if not g["has_pos_attr"]]
        res[side] = r

    out["hands"] = res

    # SVD sign-flip invariance assertion (split must be invariant)
    rr = res["right"]
    flipped = {k: -v for k, v in rr["site_offsets_m"].items()}
    a = split_verdict(rr["site_offsets_m"])["clean_split_frozen_criterion"]
    b = split_verdict(flipped)["clean_split_frozen_criterion"]
    assert a == b
    out["sign_flip_invariance"] = "split verdict invariant under n -> -n (asserted)"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")

    # ---- console digest ----------------------------------------------------
    for side in ("right", "left"):
        r = res[side]
        print(f"--- hand_{side} ---")
        print(f"  27-geom plane normal n (undirected): "
              f"{np.round(r['normal_unit_undirected'], 6).tolist()}")
        print(f"  plane centroid (local m): {np.round(r['centroid_local'], 6).tolist()}")
        print(f"  geom residual rms/max: {r['geom_resid_rms_m']*1000:.2f} / "
              f"{r['geom_resid_max_m']*1000:.2f} mm")
        print("  per-site SIGNED offsets along n (mm)  [z-term | tilt-term]  "
              "| palm13-plane (mm) | raw local z (mm):")
        for sn in HAND_SITES:
            d = r["site_offset_decomposition_m"][sn]
            print(f"    {sn:8s} {r['site_offsets_m'][sn]*1000:+7.2f}   "
                  f"[{d['z_term_m']*1000:+7.2f} | {d['tilt_term_m']*1000:+7.2f}]   "
                  f"{r['palm13_site_offsets_m'][sn]*1000:+7.2f}   "
                  f"{r['raw_local_z_m'][sn]*1000:+7.2f}")
        sv = r["split_verdict_frozen"]
        print(f"  FROZEN clean-split criterion: {sv['clean_split_frozen_criterion']}")
        print(f"    violations if palm := +n side: "
              f"{ {k: round(v*1000, 2) for k, v in sv['if_palm_is_plus_side_violations_m'].items()} }")
        print(f"    violations if palm := -n side: "
              f"{ {k: round(v*1000, 2) for k, v in sv['if_palm_is_minus_side_violations_m'].items()} }")
        jk = r["jackknife"]
        print(f"  jackknife: {jk['refits_with_clean_split']}/{jk['n_refits']} refits clean")
        for sn in HAND_SITES:
            lo = jk["per_site_offset_min_m"][sn] * 1000
            hi = jk["per_site_offset_max_m"][sn] * 1000
            print(f"    {sn:8s} jackknife offset range [{lo:+7.2f}, {hi:+7.2f}] mm")
    print(f"n27 vs palm13 plane angle: {res['right']['angle_n27_n13_deg']:.2f} deg")
    print("origin crosscheck hand_r:", out["origin_crosscheck"]["hand_r_world"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
