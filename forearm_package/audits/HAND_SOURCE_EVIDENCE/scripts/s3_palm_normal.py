"""S3 — the FROZEN palm-normal derivation (prereg sec.3), run ONCE, then the frozen
acceptance checks (sec.4). No tuning; margins recorded whatever they are.

Method (frozen): pisiform-signed palm-plate plane.
  Plate = 12 bones: pisiform, lunate, scaphoid, triquetrum, hamate, capitate, trapezoid,
  trapezium, 2mc, 3mc, 4mc, 5mc (NO thumb ray, NO phalanges).
  n_hat = smallest-eigenvalue eigenvector of the union placed-vertex covariance.
  n_palm = n_hat * sign((c_pisi - c_rest) . n_hat)   [pisiform = palmar sesamoid;
  its protrusion side IS the palm side - external anatomical fact, Gray's anatomy].
Acceptance (frozen): s_i = (site_i - c_all) . n_palm ; flexors FCR-P3/FCU-P4 must be >0,
extensors ECRL-P4/ECRB-P4/ECU-P6 must be <0; CLEAN = all five agree.
Mirror (frozen): left derivation on z-mirrored geometry must give n_L = (n_x, n_y, -n_z).

READ-ONLY inputs. Writes receipts/s3_palm_normal.json inside the audit dir.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import handlib as H  # noqa: E402
import numpy as np  # noqa: E402

OUT = H.OUT / "receipts" / "s3_palm_normal.json"
PLATE = H.PLATE  # frozen 12


def derive(plate_tris_by_bone):
    """frozen method on a dict bone -> placed triangles; returns everything."""
    union = np.vstack([plate_tris_by_bone[b].reshape(-1, 3) for b in PLATE])
    c_all = union.mean(axis=0)
    X = union - c_all
    cov = (X.T @ X) / len(X)
    w, V = np.linalg.eigh(cov)
    n_hat = V[:, 0]  # smallest eigenvalue
    if n_hat[np.argmax(np.abs(n_hat))] < 0:  # canonical display orientation only
        n_hat = -n_hat
    c_pisi = plate_tris_by_bone["pisiform"].reshape(-1, 3).mean(axis=0)
    rest = [b for b in PLATE if b != "pisiform"]
    c_rest = np.vstack([plate_tris_by_bone[b].reshape(-1, 3)
                        for b in rest]).mean(axis=0)
    diff = c_pisi - c_rest
    dot = float(diff @ n_hat)
    sign = 1.0 if dot >= 0 else -1.0
    n_palm = n_hat * sign
    resid = union @ n_hat - union @ n_hat  # placeholder no-op
    offs = union @ n_hat  # signed distances to the plane through origin of X frame
    rms = float(np.sqrt(np.mean((offs - (c_all @ n_hat)) ** 2)))
    return {
        "c_all": c_all, "c_pisi": c_pisi, "c_rest": c_rest, "diff": diff,
        "eigenvalues": w, "n_hat": n_hat, "dot_pisiform_rule": dot,
        "sign": sign, "n_palm": n_palm, "plate_rms_residual_m": rms,
        "n_union_verts": int(len(union)),
    }


def main() -> int:
    t0 = time.time()
    anchors_r, anchors_l, sites_r, _, _ = H.parse_hand_xml()
    rec = {"method": "pisiform-signed palm-plate plane (prereg sec.3, frozen)",
           "plate_bones": PLATE, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}

    placed = {}
    for b in H.BONES:
        tri, _ = H.load_stl(H.VENDOR / f"{b}.stl")
        placed[b] = tri + anchors_r[b][None, None, :]

    # ---------- gate (frozen): all 12 plate bones clear identity per R2 A3 bar ----
    s2 = json.loads((H.OUT / "receipts" / "s2_identity.json").read_text())
    s2b = json.loads((H.OUT / "receipts" / "s2b_cmc_diagnosis.json").read_text())
    rec["gate_inputs"] = {
        "site_anchor_class_max_mm": 0.8031,   # ECRL-P4->2mc; see s2 receipt table
        "extent_record_reproduced": s2["record_reproduction"],
        "cmc_surf_gaps_mm": {k: v["surf_to_surf_gap_mm"]
                             for k, v in s2b["cmc_pairs"].items()},
        "note": "primary 19-link rule FIRED (preserved); R2-A3 bar evidence: sites "
                "0.06-0.80mm, ray links 1.35-2.55mm, CMC surf gaps 0.00mm",
    }

    # ---------- derivation, RIGHT ------------------------------------------------
    d = derive({b: placed[b] for b in PLATE})
    n = d["n_palm"]
    rec["right"] = {
        "n_hat_unsigned": [float(x) for x in d["n_hat"]],
        "eigenvalues_cov": [float(x) for x in d["eigenvalues"]],
        "c_pisi_minus_c_rest_mm": [float(x * 1000) for x in d["diff"]],
        "pisiform_sign_rule_dot_mm": float(d["dot_pisiform_rule"] * 1000),
        "sign_applied": float(d["sign"]),
        "n_palm_hand_r_local": [float(x) for x in n],
        "plate_rms_residual_mm": float(d["plate_rms_residual_m"] * 1000),
        "angle_deg_to_minus_z": float(np.degrees(np.arccos(
            np.clip(n @ np.array([0.0, 0.0, -1.0]), -1, 1)))),
        "angle_deg_to_plus_z": float(np.degrees(np.arccos(
            np.clip(n @ np.array([0.0, 0.0, 1.0]), -1, 1)))),
        "c_all_hand_r_local_mm": [float(x * 1000) for x in d["c_all"]],
        "c_pisi_mm": [float(x * 1000) for x in d["c_pisi"]],
    }
    print(f"n_palm (hand_r local) = [{n[0]:+.6f}, {n[1]:+.6f}, {n[2]:+.6f}]  "
          f"pisiform-rule dot = {d['dot_pisiform_rule']*1000:+.2f} mm")

    # ---------- acceptance: the frozen site split (F-R2b closure test) -----------
    c_all = d["c_all"]
    rows = []
    clean = True
    for sname, (p, comp) in H.SITES.items():
        p = np.array(p)
        s = float((p - c_all) @ n)
        want = "palm(+)" if comp == "flexor" else "dorsal(-)"
        ok = (s > 0) if comp == "flexor" else (s < 0)
        clean &= ok
        rows.append({"site": sname, "compartment": comp, "expect": want,
                     "offset_along_n_palm_mm": s * 1000, "agree": bool(ok)})
        print(f"site {sname:8s} {comp:8s} expect {want:8s}  s = {s*1000:+7.2f} mm  "
              f"{'OK' if ok else 'VIOLATION'}")
    rec["acceptance_split"] = {"rows": rows, "clean": bool(clean),
                               "criterion": "flexors >0, extensors <0 (all five)"}
    rec["falsifier_b_fired"] = not clean

    # ---------- mirror exactness + LEFT derivation (falsifier (c)) ---------------
    def zflip(a):
        return np.array([a[0], a[1], -a[2]])
    mir_exact = {}
    for b in H.BONES:
        mir_exact[b] = float(np.max(np.abs(
            anchors_l[b + "_l"] - zflip(anchors_r[b]))))
    for sname, (p, _) in H.SITES.items():
        pass  # left sites are not in the SITES dict; read from XML below
    # left sites: parse hand_l body sites directly
    import xml.etree.ElementTree as ET
    root = ET.parse(H.XML).getroot()
    left_sites = {}
    for body in root.iter("body"):
        if body.get("name") == "hand_l":
            for s in body.findall("site"):
                nm = s.get("name")
                base = nm.replace("_l", "") + "-P" + nm.split("-P")[-1] \
                    if "-P" in nm else nm
                left_sites[nm] = np.array([float(v) for v in s.get("pos").split()])
    site_mirror = {}
    for sname, (p, comp) in H.SITES.items():
        nm = sname.replace("-P", "_l-P")
        if nm in left_sites:
            site_mirror[sname] = float(np.max(np.abs(left_sites[nm] - zflip(p))))
    rec["mirror"] = {
        "anchor_z_mirror_max_abs_mm": float(max(mir_exact.values()) * 1000),
        "anchor_z_mirror_per_bone_mm": {k: v * 1000 for k, v in mir_exact.items()},
        "site_z_mirror_max_abs_mm": (float(max(site_mirror.values()) * 1000)
                                     if site_mirror else None),
        "left_stl_in_vendor": False,
        "limitation": "left <name>_l.stl absent from vendor set; left identity not "
                      "testable on disk (prereg sec.2.6c) - check is construction-level",
    }
    # left derivation: same frozen method on z-mirrored geometry at left anchors
    placed_l = {}
    for b in PLATE:
        tri, _ = H.load_stl(H.VENDOR / f"{b}.stl")
        placed_l[b] = (tri * np.array([1.0, 1.0, -1.0])[None, None, :]
                       + anchors_l[b + "_l"][None, None, :])
    dl = derive(placed_l)
    nl = dl["n_palm"]
    mirror_ok = float(np.max(np.abs(nl - zflip(n)))) < 1e-9
    rec["left"] = {
        "n_palm_hand_l_local": [float(x) for x in nl],
        "pisiform_sign_rule_dot_mm": float(dl["dot_pisiform_rule"] * 1000),
        "equals_exact_mirror_of_right": bool(mirror_ok),
        "left_split_clean_same_method": None,
    }
    rows_l = []
    clean_l = True
    for sname, (p, comp) in H.SITES.items():
        nm = sname.replace("-P", "_l-P")
        if nm not in left_sites:
            continue
        p = np.array(p)
        s = float((zflip(p) - dl["c_all"]) @ nl)
        ok = (s > 0) if comp == "flexor" else (s < 0)
        clean_l &= ok
        rows_l.append({"site": nm, "compartment": comp,
                       "offset_along_n_palm_mm": s * 1000, "agree": bool(ok)})
    rec["left"]["left_split_clean_same_method"] = bool(clean_l)
    rec["left"]["rows"] = rows_l
    rec["falsifier_c_fired"] = not (mirror_ok and rec["mirror"]["anchor_z_mirror_max_abs_mm"] < 1e-9)
    print(f"left n_palm = [{nl[0]:+.6f}, {nl[1]:+.6f}, {nl[2]:+.6f}]  exact mirror: {mirror_ok}")
    print(f"left split clean: {clean_l}")

    rec["elapsed_s"] = time.time() - t0
    OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({rec['elapsed_s']:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
