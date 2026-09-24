"""C3 script 1 — source-side geometry for the circularity + orientation-uniqueness audit.

Reads ONLY baseline_snapshot/source_xml/chimanoid.xml (stdlib ElementTree, live elements).
Computes, with the exact intake semantics (world = parent_world + parent_rot @ pos,
rot = parent_rot @ quat_to_rotmat(quat)):
  - body origins of the right-arm chain; the ulna->radius vector (the C1 "direction" fact)
  - the 10 ulna sites: |p| from the ulna origin, and perp distances to
      (a) the U-STR axis (ulna_origin -> radius_origin)
      (b) the U-ANA axis (ulna_origin -> ECU-P4)
  - roll-witness ||t|| for the three roll candidates ECU-P2 / ANC-P2 / TRIlat-P5 under
    BOTH authorings' axes, with both axis DIRECTIONS (+a / -a) — ||t|| is a line-perp
    distance, hence direction-invariant; the produced b,c vectors flip sign with a.
  - hand_r: the 27 skeleton-mesh geom positions (local; lunate has no pos attr -> 0)
    and the 5 tendon-site positions (local); best-fit plane of each set (SVD);
    residuals; plane-normal angle between the sets (the construction-perp-validation test).
Writes receipts JSON to the C3 receipts dir. No writes outside audits/C3_independent_challenge/.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
XML = BASE / "source_xml" / "chimanoid.xml"
OUT = Path(r"E:\PythonChimera\forearm_package\audits\C3_independent_challenge\receipts\c3_source_geometry.json")


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
        if g.get("type", "mesh") == "mesh" or True:
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


def perp_dist(p, line_point, a):
    d = p - line_point
    return float(np.linalg.norm(d - a * (a @ d)))


def best_fit_plane(pts):
    """centroid, normal (unit), singular values of centered pts, signed perp distances."""
    c = pts.mean(axis=0)
    X = pts - c
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    n = Vt[-1]
    d = X @ n
    return c, n, S, d


def main():
    root = ET.parse(str(XML)).getroot()
    wb = root.find("worldbody")
    bodies, sites, geoms = {}, {}, []
    for b in wb.findall("body"):
        walk(b, np.zeros(3), np.eye(3), bodies, sites, geoms)

    out = {}
    out["inputs"] = {"xml": str(XML), "sha256_note": "see MANIFEST.json:248 (675e00d0...)"}

    # ---- right-arm chain origins ------------------------------------------
    hum, uln, rad, hnd = bodies["humerus"], bodies["ulna"], bodies["radius"], bodies["hand_r"]
    out["origins"] = {
        "humerus": hum.tolist(), "ulna": uln.tolist(),
        "radius": rad.tolist(), "hand_r": hnd.tolist(),
    }
    v_ur = rad - uln
    v_rh = hnd - rad
    v_uh = hnd - uln
    out["chain_vectors"] = {
        "ulna_to_radius": v_ur.tolist(), "abs_ulna_to_radius": float(np.linalg.norm(v_ur)),
        "radius_to_hand": v_rh.tolist(), "abs_radius_to_hand": float(np.linalg.norm(v_rh)),
        "ulna_to_hand": v_uh.tolist(), "abs_ulna_to_hand": float(np.linalg.norm(v_uh)),
    }

    # ---- ulna sites ---------------------------------------------------------
    ulna_sites = [
        "TRIlong-P5", "TRIlat-P5", "TRImed-P5", "ANC-P2", "BRA-P4",
        "BRA-P3", "ECU-P2", "ECU-P3", "ECU-P4", "PT-P2",
    ]
    a_str = unit(v_ur)                    # U-STR source axis
    e4 = uln + sites["ECU-P4"]["pos_local"]
    a_ana = unit(e4 - uln)                # U-ANA source axis
    site_rows = []
    for sn in ulna_sites:
        g = uln + sites[sn]["pos_local"]
        rel = g - uln
        site_rows.append(
            {
                "site": sn,
                "pos_global": g.tolist(),
                "abs_p_from_ulna_origin": float(np.linalg.norm(rel)),
                "perp_to_USTR_axis": perp_dist(g, uln, a_str),
                "perp_to_UANA_axis": perp_dist(g, uln, a_ana),
                "axial_to_USTR_axis": float(rel @ a_str),
                "axial_to_UANA_axis": float(rel @ a_ana),
            }
        )
    out["ulna_sites"] = site_rows
    out["ulna_axes"] = {"USTR_unit": a_str.tolist(), "UANA_unit": a_ana.tolist()}
    out["axis_direction_note"] = (
        "||t|| roll witnesses are per-line-perp distances: invariant to the +a/-a "
        "direction ambiguity. Flipping the axis direction flips b and c (180-deg roll), "
        "never any magnitude."
    )

    roll_cands = ["ECU-P2", "ANC-P2", "TRIlat-P5"]
    out["roll_witnesses"] = {}
    for rc in roll_cands:
        g = uln + sites[rc]["pos_local"]
        row = {}
        for label, a in (("USTR", a_str), ("UANA", a_ana)):
            t = (g - uln) - a * (a @ (g - uln))
            row[f"roll_witness_t_norm_{label}"] = float(np.linalg.norm(t))
        out["roll_witnesses"][rc] = row
    # also the b-axis azimuth each roll candidate would impose, per axis, as a check
    # that different candidates give genuinely different rolls:
    def frame_from(a, q_point):
        t = (q_point - uln) - a * (a @ (q_point - uln))
        b = unit(t)
        c = np.cross(a, b)
        return b, c

    out["roll_azimuth_separation_USTR"] = {}
    for rc in roll_cands:
        b_rc, _ = frame_from(a_str, uln + sites[rc]["pos_local"])
        b_e2, _ = frame_from(a_str, uln + sites["ECU-P2"]["pos_local"])
        out["roll_azimuth_separation_USTR"][rc] = float(
            np.degrees(np.arctan2(np.cross(b_e2, b_rc) @ a_str, b_e2 @ b_rc))
        )

    # map's roll-candidate table cross-check: its "perp" numbers vs measured |p|
    out["map_roll_table_crosscheck"] = {
        "ECU-P2": {"map_perp": 0.0448, "measured_abs_p": out["ulna_sites"][6]["abs_p_from_ulna_origin"],
                   "measured_perp_USTR": out["roll_witnesses"]["ECU-P2"]["roll_witness_t_norm_USTR"],
                   "measured_perp_UANA": out["roll_witnesses"]["ECU-P2"]["roll_witness_t_norm_UANA"]},
        "ANC-P2": {"map_perp": 0.0260, "measured_abs_p": out["ulna_sites"][3]["abs_p_from_ulna_origin"],
                   "measured_perp_USTR": out["roll_witnesses"]["ANC-P2"]["roll_witness_t_norm_USTR"],
                   "measured_perp_UANA": out["roll_witnesses"]["ANC-P2"]["roll_witness_t_norm_UANA"]},
        "TRIlat-P5": {"map_perp": 0.0243, "measured_abs_p": out["ulna_sites"][1]["abs_p_from_ulna_origin"],
                      "measured_perp_USTR": out["roll_witnesses"]["TRIlat-P5"]["roll_witness_t_norm_USTR"],
                      "measured_perp_UANA": out["roll_witnesses"]["TRIlat-P5"]["roll_witness_t_norm_UANA"]},
        "note": "TRIlat-P5/ANC-P2 map numbers equal measured |p| to 4 decimals; ECU-P2 map "
                "0.0448 matches neither |p| (0.0457) nor any axis perp. See report.",
    }

    # ---- TRI triplet identity ----------------------------------------------
    out["tri_triplet"] = {
        "TRIlong-P5": sites["TRIlong-P5"]["pos_local"].tolist(),
        "TRIlat-P5": sites["TRIlat-P5"]["pos_local"].tolist(),
        "TRImed-P5": sites["TRImed-P5"]["pos_local"].tolist(),
        "identical": bool(
            np.array_equal(sites["TRIlong-P5"]["pos_local"], sites["TRIlat-P5"]["pos_local"])
            and np.array_equal(sites["TRIlong-P5"]["pos_local"], sites["TRImed-P5"]["pos_local"])
        ),
    }

    # ---- hand_r: 27 skeleton geoms + 5 sites, plane fits --------------------
    hand_geoms = [g for g in geoms if g["body"] == "hand_r" and g["type"] == "mesh"]
    caps = [g for g in geoms if g["body"] == "hand_r" and g["type"] == "capsule"]
    assert len(hand_geoms) == 27, len(hand_geoms)
    assert len(caps) == 3
    P27 = np.array([g["pos_local"] for g in hand_geoms])
    names27 = [g["name"] for g in hand_geoms]
    # NOTE: the muscle is ECRB (extensor carpi radialis brevis); the C3/C2 briefs'
    # "ECBR-P4" is a typo for ECRB-P4 (XML L664).
    hand_sites = ["ECRL-P4", "ECRB-P4", "ECU-P6", "FCR-P3", "FCU-P4"]
    P5 = np.array([sites[sn]["pos_local"] for sn in hand_sites])

    def plane_report(pts, label):
        c, n, S, d = best_fit_plane(pts)
        return {
            "set": label,
            "n_points": int(len(pts)),
            "centroid_local": c.tolist(),
            "normal_unit_undirected": n.tolist(),
            "singular_values": S.tolist(),
            "planarity_margin_sigma2_over_sigma3": float(S[1] / S[2]) if S[2] > 0 else None,
            "residual_rms_m": float(np.sqrt((d ** 2).mean())),
            "residual_max_m": float(np.abs(d).max()),
            "perp_distances_m": d.tolist(),
            "extent_in_plane_m": float(np.sqrt(S[0] ** 2 / len(pts) + S[1] ** 2 / len(pts))),
        }

    rep27 = plane_report(P27, "27_skeleton_geoms")
    rep5 = plane_report(P5, "5_tendon_sites")
    n27, n5 = np.array(rep27["normal_unit_undirected"]), np.array(rep5["normal_unit_undirected"])
    cosang = abs(float(n27 @ n5))
    rep5["sites_about_geom_plane"] = {
        "perp_distance_of_each_site_to_27geom_plane_m": [
            float((p - np.array(rep27["centroid_local"])) @ n27) for p in P5
        ],
    }
    # palm-only variant: the 8 carpals + 5 metacarpals (named explicitly; NOTE
    # "scaphoid" contains the substring "ph" so a substring filter would drop it)
    palm_names = [
        "pisiform", "lunate", "scaphoid", "triquetrum", "hamate", "capitate",
        "trapezoid", "trapezium", "1mc", "2mc", "3mc", "4mc", "5mc",
    ]
    P13 = np.array([g["pos_local"] for g in hand_geoms if g["name"] in palm_names])
    assert len(P13) == 13, len(P13)
    rep13 = plane_report(P13, "13_carpals_metacarpals")

    # jackknife (leave-one-out) spread of each plane normal — the normal's
    # uncertainty given the set's own residual curvature (discrimination margin)
    def jackknife_normals(pts):
        norms = []
        for i in range(len(pts)):
            sub = np.delete(pts, i, axis=0)
            _, n, _, _ = best_fit_plane(sub)
            norms.append(n)
        norms = np.array(norms)
        # angular deviation of each leave-one-out normal from the full-set normal
        c, n_full, _, _ = best_fit_plane(pts)
        devs = np.degrees(np.arccos(np.clip(np.abs(norms @ n_full), 0.0, 1.0)))
        return float(devs.mean()), float(devs.max())

    jk27 = jackknife_normals(P27)
    jk13 = jackknife_normals(P13)
    jk5 = jackknife_normals(P5)
    out["hand_plane_normal_jackknife_deg"] = {
        "geoms_27": {"mean": jk27[0], "max": jk27[1]},
        "carpals_metacarpals_13": {"mean": jk13[0], "max": jk13[1]},
        "sites_5": {"mean": jk5[0], "max": jk5[1]},
        "note": "plane normals are UNDIRECTED: deviations reported as acute angles",
    }

    # does the 27-geom plane contain the source hand length axis? (if the axis lies
    # in the plane, the ONB roll b = n x a is unique up to sign -> 180-deg ambiguity
    # is the ONLY remaining freedom; if not, the in-plane azimuth of Q matters too)
    a_hand_src = unit(P27[names27.index("3distph")])  # wrist origin = hand body origin
    ang_n27_a = float(np.degrees(np.arccos(min(1.0, abs(float(n27 @ a_hand_src))))))
    ang_n13_a = float(np.degrees(np.arccos(min(1.0, abs(float(np.array(rep13["normal_unit_undirected"]) @ a_hand_src))))))
    ang_n5_a = float(np.degrees(np.arccos(min(1.0, abs(float(n5 @ a_hand_src))))))
    out["hand_axis_in_plane_deg"] = {
        "angle_normal_to_length_axis_27": ang_n27_a,
        "angle_normal_to_length_axis_13": ang_n13_a,
        "angle_normal_to_length_axis_5": ang_n5_a,
        "length_axis_unit_local": a_hand_src.tolist(),
        "note": "90 deg means the axis lies IN the plane",
    }
    # acute angle between the palm subset plane and the 27-geom plane, and vs sites
    n13 = np.array(rep13["normal_unit_undirected"])
    ang2713 = float(np.degrees(np.arccos(min(1.0, abs(float(n27 @ n13))))))

    out["hand_planes"] = {
        "geoms_27": rep27,
        "sites_5": rep5,
        "carpals_metacarpals_13": rep13,
        "acute_angle_between_normals_deg": float(np.degrees(np.arccos(min(1.0, cosang)))),
        "acute_angle_27_vs_13_deg": ang2713,
        "geom_names": [g["name"] for g in hand_geoms],
        "geom_missing_pos_attr": [g["name"] for g in hand_geoms if not g["has_pos_attr"]],
    }

    # direction A residual metric: spread of the 5 sites about the 27-geom plane
    d5_on_27 = np.array(rep5["sites_about_geom_plane"]["perp_distance_of_each_site_to_27geom_plane_m"])
    out["hand_planes"]["direction_A_geoms_construct_sites_validate"] = {
        "site_plane_spread_rms_m": float(np.sqrt((d5_on_27 ** 2).mean())),
        "site_plane_spread_max_m": float(np.abs(d5_on_27).max()),
        "geom_plane_residual_rms_m": rep27["residual_rms_m"],
        "margin_ratio_site_spread_over_geom_rms": float(
            np.sqrt((d5_on_27 ** 2).mean()) / rep27["residual_rms_m"]
        ),
    }
    # direction B: 5-site plane vs the 27 geoms
    d27_on_5 = (P27 - np.array(rep5["centroid_local"])) @ n5
    out["hand_planes"]["direction_B_sites_construct_geoms_validate"] = {
        "geom_plane_spread_rms_m": float(np.sqrt((d27_on_5 ** 2).mean())),
        "geom_plane_spread_max_m": float(np.abs(d27_on_5).max()),
        "site_plane_residual_rms_m": rep5["residual_rms_m"],
        "margin_ratio_geom_spread_over_site_rms": float(
            np.sqrt((d27_on_5 ** 2).mean()) / max(rep5["residual_rms_m"], 1e-15)
        ),
    }

    # source palm extents for H-ASP (b,c) and 3distph
    names27 = [g["name"] for g in hand_geoms]
    i3d = names27.index("3distph")
    out["hand_length_refs"] = {
        "3distph_abs_p": float(np.linalg.norm(P27[i3d])),
        "distallest_geom": min(
            ((float(np.linalg.norm(p)), nm) for p, nm in zip(P27, names27)),
            key=lambda t: -t[0],
        ),
        "metacarpal_x_range_m": [
            float(min(g["pos_local"][0] for g in hand_geoms if g["name"].endswith("mc"))),
            float(max(g["pos_local"][0] for g in hand_geoms if g["name"].endswith("mc"))),
        ],
    }

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    # console digest
    print(f"|ulna->radius| = {np.linalg.norm(v_ur):.6f} m  vec {np.round(v_ur,6).tolist()}")
    print(f"|radius->hand| = {np.linalg.norm(v_rh):.6f} m")
    print("roll witnesses (m):")
    for rc in roll_cands:
        r = out["roll_witnesses"][rc]
        print(f"  {rc:11s} USTR {r['roll_witness_t_norm_USTR']:.6f}  UANA {r['roll_witness_t_norm_UANA']:.6f}")
    print(f"hand plane normals angle (acute) = {out['hand_planes']['acute_angle_between_normals_deg']:.3f} deg")
    print(f"27 vs 13 (palm) plane angle = {out['hand_planes']['acute_angle_27_vs_13_deg']:.3f} deg")
    print(f"jackknife normal spread: 27 {jk27}  13 {jk13}  5 {jk5} (mean,max deg)")
    print(f"axis-in-plane check (90=axis in plane): 27 {ang_n27_a:.2f}  13 {ang_n13_a:.2f}  5 {ang_n5_a:.2f} deg")
    print(f"dir A: sites-about-geom-plane rms {out['hand_planes']['direction_A_geoms_construct_sites_validate']['site_plane_spread_rms_m']*1000:.2f} mm vs geom rms {rep27['residual_rms_m']*1000:.2f} mm")
    print(f"dir B: geoms-about-site-plane rms {out['hand_planes']['direction_B_sites_construct_geoms_validate']['geom_plane_spread_rms_m']*1000:.2f} mm vs site rms {rep5['residual_rms_m']*1000:.3f} mm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
