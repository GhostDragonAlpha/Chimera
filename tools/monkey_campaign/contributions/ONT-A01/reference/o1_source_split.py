"""O1 script 2 — SOURCE labeling: per-site signed dorsovolar (+x) table, flexor/dorsal
split verdict, bone-surface resolution, and the U-STR source-frame roll geometry.

Reads ONLY baseline_snapshot/source_xml/chimanoid.xml (stdlib ElementTree, intake
walk semantics) + this audit's own receipt o1_ulna_mesh_probe.json. Writes only inside
audits/O1_ulna_orientation/. PREREGISTERED METHOD (a) exactly:
  signed dorsovolar coordinate = the site's +x component in the source rest frame
  (bodies axis-aligned at rest, quat identity asserted -> local x IS world +x).
Compartment semantics (frozen, EXTERNAL-cited in receipts/external_citations.md):
  flexors BRA/PT = volar (expected +x); extensors TRI/ANC/ECU = dorsal (expected -x).
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

O1 = Path(r"E:\PythonChimera\forearm_package\audits\O1_ulna_orientation")
BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
XML = BASE / "source_xml" / "chimanoid.xml"
OUT = O1 / "receipts" / "o1_source_split.json"

ULNA_SITES = [
    "TRIlong-P5", "TRIlat-P5", "TRImed-P5", "ANC-P2", "BRA-P4",
    "BRA-P3", "ECU-P2", "ECU-P3", "ECU-P4", "PT-P2",
]
FLEXORS = {"BRA-P4", "BRA-P3", "PT-P2"}          # frozen: volar
EXTENSORS = {"TRIlong-P5", "TRIlat-P5", "TRImed-P5", "ANC-P2", "ECU-P2", "ECU-P3", "ECU-P4"}
RADIUS_SITE_CLASSES = {  # for the corroboration panel only
    "BIClong": "elbow flexor (anterior arm)", "BICshort": "elbow flexor (anterior arm)",
    "BRD": "elbow flexor, anterolateral course", "ECRL": "extensor (anterolateral course)",
    "ECRB": "extensor (anterolateral course)", "ECU": "extensor (posterior)",
    "FCR": "flexor (volar)", "FCU": "flexor (volar)", "PT": "flexor (volar)",
}
ROLL_CANDIDATES = ["ECU-P2", "ANC-P2", "TRIlat-P5"]  # C3 §2.5 declared set


def _vec(text):
    return np.array([float(v) for v in (text or "").split()], dtype=np.float64)


def walk(elem, parent_world, parent_rot, bodies, sites):
    name = elem.get("name")
    pos = _vec(elem.get("pos", "0 0 0"))
    quat = _vec(elem.get("quat", "1 0 0 0"))
    rot = parent_rot @ quat_rotmat(quat)
    world = parent_world + parent_rot @ pos
    bodies[name] = {"world": world, "rot": rot, "quat": quat}
    for s in elem.findall("site"):
        sites[s.get("name")] = {"body": name, "pos_local": _vec(s.get("pos", "0 0 0"))}
    for child in elem.findall("body"):
        walk(child, world, rot, bodies, sites)


def quat_rotmat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def unit(v):
    return v / np.linalg.norm(v)


def main() -> int:
    root = ET.parse(str(XML)).getroot()
    wb = root.find("worldbody")
    bodies, sites = {}, {}
    for b in wb.findall("body"):
        walk(b, np.zeros(3), np.eye(3), bodies, sites)

    # axis-aligned rest-frame assertion on the right-arm chain (method precondition)
    chain = ["humerus", "ulna", "radius", "hand_r"]
    quats = {n: bodies[n]["quat"].tolist() for n in chain}
    axis_aligned = all(np.allclose(bodies[n]["quat"], [1, 0, 0, 0]) for n in chain)
    assert axis_aligned, quats

    uln = bodies["ulna"]["world"]
    rad = bodies["radius"]["world"]
    hnd = bodies["hand_r"]["world"]
    v_ur = rad - uln
    v_uh = hnd - uln
    a_str = unit(v_ur)              # U-STR source axis (ulna origin -> radius origin)
    a_anat = unit(v_uh)             # anatomical forearm axis (elbow -> wrist), C1 frame
    ew_mm = float(np.linalg.norm(v_uh) * 1000)

    # ---- preregistered per-site table ----------------------------------------
    probe = json.loads((O1 / "receipts" / "o1_ulna_mesh_probe.json").read_text())
    surf = {r["site"]: r for r in probe["site_surface_test"]}
    bone_st = probe["bone_x_extent_at_site_stations"]

    rows = []
    for sn in ULNA_SITES:
        p = sites[sn]["pos_local"]
        rel = uln + p - uln
        ax_mm = float(rel @ a_anat * 1000)
        cls = "flexor(volar)" if sn in FLEXORS else "extensor(dorsal)"
        expect = 1.0 if sn in FLEXORS else -1.0
        sign = 1.0 if p[0] > 0 else -1.0
        st = bone_st[sn]
        rows.append({
            "site": sn,
            "compartment_class": cls,
            "pos_local_m": p.tolist(),
            "dorsovolar_signed_x_mm": float(p[0] * 1000),          # THE method-(a) number
            "lateral_z_mm": float(p[2] * 1000),
            "axial_anatomical_mm": ax_mm,
            "axial_percent_of_elbow_wrist": float(100.0 * ax_mm / ew_mm),
            "abs_p_mm": float(np.linalg.norm(rel) * 1000),
            "x_sign_agrees_with_compartment": bool(sign == expect),
            # bone-surface context (audit receipt o1_ulna_mesh_probe.json):
            "bone_x_span_at_station_mm": [st["bone_x_min_m"] * 1000, st["bone_x_max_m"] * 1000],
            "site_volar_face_fraction_at_station": st["site_x_fraction_of_breadth"],
            "dist_to_bone_surface_mm": surf[sn]["dist_to_surface_m"] * 1000,
        })

    # ---- split verdicts -------------------------------------------------------
    flex_x = [r["dorsovolar_signed_x_mm"] for r in rows if r["site"] in FLEXORS]
    ext_x = [r["dorsovolar_signed_x_mm"] for r in rows if r["site"] in EXTENSORS]
    clean_raw = all(v > 0 for v in flex_x) and all(v < 0 for v in ext_x)
    dissenters_raw = [r["site"] for r in rows if not r["x_sign_agrees_with_compartment"]]
    # bone-local reading: site on the volar half of the LOCAL bone breadth (frac > 0.5)
    # vs dorsal half (frac < 0.5); course points evaluated by the same fraction.
    bone_clean = True
    bone_rows = []
    for r in rows:
        f = r["site_volar_face_fraction_at_station"]
        expect_volar = r["site"] in FLEXORS
        ok = (f > 0.5) == expect_volar
        bone_clean &= ok
        bone_rows.append({"site": r["site"], "volar_face_fraction": f,
                          "expected_volar": expect_volar, "agrees": bool(ok)})

    out = {
        "inputs": {"xml": str(XML), "walk": "intake semantics (world = parent_world + parent_rot @ pos)"},
        "rest_frame_assertion": {"axis_aligned_quats": quats, "axis_aligned": axis_aligned},
        "origins_m": {"ulna": uln.tolist(), "radius": rad.tolist(), "hand_r": hnd.tolist()},
        "axes": {
            "USTR_source_axis_unit": a_str.tolist(),
            "anatomical_forearm_axis_unit": a_anat.tolist(),
            "elbow_to_wrist_mm": ew_mm,
        },
        "site_table": rows,
        "split_verdict": {
            "RAW_preregistered_method_a": {
                "flexor_x_mm": flex_x, "extensor_x_mm": ext_x,
                "clean_raw_split": bool(clean_raw),
                "dissenter_sites": dissenters_raw,
                "stop_rule_text": "if the flexor/dorsal split is mixed -> UNRESOLVED SIGN blocker",
                "mixed_raw_split": bool(not clean_raw),
            },
            "BONE_SURFACE_RESOLUTION": {
                "per_site": bone_rows,
                "clean_bone_local_split": bool(bone_clean),
                "basis": "volar/dorsal half of the LOCAL bone cross-section breadth at each "
                         "site's own station (bone = the source's own mesh asset, identity "
                         "tested in o1_ulna_mesh_probe.json; NOT containment, NOT mechanical)",
            },
            "falsifier_PT_dorsal": {
                "PT_dorsovolar_x_mm": float(sites["PT-P2"]["pos_local"][0] * 1000),
                "PT_medial_z_mm": float(sites["PT-P2"]["pos_local"][2] * 1000),
                "PT_bone_volar_face_fraction": bone_st["PT-P2"]["site_x_fraction_of_breadth"],
                "fired": bool(sites["PT-P2"]["pos_local"][0] < 0),
            },
        },
        "radius_corroboration_panel": radius_panel(bodies, sites, RADIUS_SITE_CLASSES),
        "ustr_frame": ustr_frame(a_str, uln, sites),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"elbow->wrist {ew_mm:.1f} mm; USTR axis {np.round(a_str,4).tolist()}")
    print(f"{'site':11s} {'x_dv mm':>9s} {'z_lat mm':>9s} {'axial mm':>9s} {'ax %EW':>7s} "
          f"{'bone volar-frac':>15s} {'class':>16s} agree")
    for r in rows:
        print(f"{r['site']:11s} {r['dorsovolar_signed_x_mm']:+9.2f} {r['lateral_z_mm']:+9.2f} "
              f"{r['axial_anatomical_mm']:9.2f} {r['axial_percent_of_elbow_wrist']:7.2f} "
              f"{r['site_volar_face_fraction_at_station']:15.2f} {r['compartment_class']:>16s} "
              f"{'RAW-OK' if r['x_sign_agrees_with_compartment'] else 'RAW-DISSENT'}")
    print(f"RAW split clean: {clean_raw} (dissenters: {dissenters_raw})")
    print(f"BONE-LOCAL split clean: {bone_clean}")
    print(f"falsifier PT-dorsal fired: {out['split_verdict']['falsifier_PT_dorsal']['fired']}")
    fr = out["ustr_frame"]["roll_candidates"]
    for k, v in fr.items():
        print(f"roll cand {k:11s} b_az_in_e-basis {v['b_azimuth_e_basis_deg']:+8.2f}  "
              f"volar_az_rel_to_b {v['volar_azimuth_relative_to_b_deg']:+8.2f}")
    print(f"wrote {OUT}")
    return 0


def radius_panel(bodies, sites, classes):
    """Corroboration only: radius-body sites' dorsovolar x with compartment labels."""
    rows = []
    for sn, s in sites.items():
        if s["body"] != "radius":
            continue
        fam = next((c for k, c in classes.items() if sn.startswith(k)), "?")
        rows.append({"site": sn, "class": fam,
                     "dorsovolar_signed_x_mm": float(s["pos_local"][0] * 1000),
                     "lateral_z_mm": float(s["pos_local"][2] * 1000)})
    return rows


def ustr_frame(a_str, uln, sites):
    """U-STR source frame geometry: roll-candidate b/c bases and where the source
    volar direction (+x) sits in each."""
    xhat = np.array([1.0, 0.0, 0.0])
    # fixed e-rule transverse basis (same rule as C3's target section basis)
    e1 = unit(xhat - a_str * (a_str @ xhat))
    e2 = np.cross(a_str, e1)
    v_volar = unit(xhat - a_str * (a_str @ xhat))   # transverse part of +x (volar)
    az = lambda v: float(np.degrees(np.arctan2(v @ e2, v @ e1)))
    cands = {}
    for rc in ROLL_CANDIDATES:
        t = (sites[rc]["pos_local"]) - a_str * (a_str @ sites[rc]["pos_local"])
        b = unit(t)
        c = np.cross(a_str, b)
        cands[rc] = {
            "b_unit": b.tolist(), "c_unit": c.tolist(),
            "b_azimuth_e_basis_deg": az(b),
            "volar_azimuth_relative_to_b_deg": float(np.degrees(np.arctan2(v_volar @ c, v_volar @ b))),
            "roll_witness_norm_m": float(np.linalg.norm(t)),
        }
    return {
        "e1_unit": e1.tolist(), "e2_unit": e2.tolist(),
        "volar_transverse_unit": v_volar.tolist(),
        "volar_azimuth_e_basis_deg": az(v_volar),
        "note": "volar azimuth is 0 deg in the e-rule basis BY CONSTRUCTION (e1 = rejection "
                "of +x); the non-trivial content is each roll candidate's azimuth relative "
                "to it, and (in o1_combine) the target-side azimuths",
        "roll_candidates": cands,
    }


if __name__ == "__main__":
    raise SystemExit(main())
