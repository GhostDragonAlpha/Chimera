"""A4 audit — independent verification of exported local-to-world transforms and
bilateral symmetry of the actual-monkey forearm fit.

Writes receipts ONLY to the A4 audit dir. Never touches baseline_snapshot.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT = Path(r"E:\PythonChimera\forearm_package\audits\A4_transforms")
WORK = AUDIT / "work"
sys.path.insert(0, str(WORK / "code"))

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
RUNS = BASE / "runs"
XML = BASE / "source_xml" / "chimanoid.xml"
BIRTH = BASE / "inputs" / "monkey_birth.bin"
PACK = BASE / "inputs" / "monkey_joints.bin"

from intake import load_source, global_site_positions  # noqa: E402
from mesh_target import MonkeyTarget  # noqa: E402
from actual_target_fit import build_correspondence_envelope  # noqa: E402
from compiler import onb_from_points  # noqa: E402

R = {}

# ---------------------------------------------------------------- load artifacts
packet = json.load(open(RUNS / "attachment_candidates.json", encoding="utf-8"))
fit = json.load(open(RUNS / "actual_monkey_fit.json", encoding="utf-8"))
exp = json.load(open(RUNS / "experiment_transverse_candidate.json", encoding="utf-8"))
mirror_read = json.load(open(RUNS / "mirror_read.json", encoding="utf-8"))

assert set(packet["bodies"].keys()) == {"radius", "radius_l"}, "unexpected bodies in packet"

# ------------------------------------------------- rebuild the fit's own resolution
real = load_source(str(XML))
sw = global_site_positions(real)
mt = MonkeyTarget(birth_path=str(BIRTH), pack_path=str(PACK))
corr, _ = build_correspondence_envelope(real, mt, sw)

seg_fit = {s["source_body"]: s for s in fit["segments"]}
site_fit = {s["name"]: s for s in fit["sites"]}


def resolve(ref: str) -> np.ndarray:
    kind, name = ref.split(":", 1)
    if kind == "body_origin":
        return np.asarray(real.body_by_name[name].pos_global, dtype=np.float64)
    if kind == "site":
        return np.asarray(sw[name], dtype=np.float64)
    raise ValueError(ref)


# ------------------------------------------------- criterion 1: per-body transform audit
transform_audit = {}
for body in ("radius", "radius_l"):
    bd = packet["bodies"][body]
    l2w = bd["local_to_world"]
    R_pkg = np.asarray(l2w["R_source_local_to_target"], dtype=np.float64)
    t_pkg = np.asarray(l2w["t_fitted_origin_m"], dtype=np.float64)

    # rebuild B from the same landmark resolution the fit used
    src_lm = corr.source_landmarks
    P0 = resolve(src_lm[f"{body}.prox"])
    P1 = resolve(src_lm[f"{body}.dist"])
    Q = resolve(src_lm[f"{body}.roll"])
    B = np.column_stack(onb_from_points(P0, P1, Q))
    landmarks_used = {
        "prox": (src_lm[f"{body}.prox"], P0.tolist()),
        "dist": (src_lm[f"{body}.dist"], P1.tolist()),
        "roll": (src_lm[f"{body}.roll"], Q.tolist()),
    }

    # composition from the FIT's full-precision segment record
    seg = seg_fit[body]
    Bp = np.asarray(seg["frame_basis"], dtype=np.float64)
    scale = np.asarray(seg["scale"], dtype=np.float64)
    t_fit = np.asarray(seg["fitted_origin"], dtype=np.float64)
    R_rebuilt = Bp @ np.diag(scale) @ B.T

    # orthonormality / determinant of the exported R
    orth_max = float(np.max(np.abs(R_pkg.T @ R_pkg - np.eye(3))))
    det_R = float(np.linalg.det(R_pkg))
    sv = np.linalg.svd(R_pkg, compute_uv=False)
    s_uniform = float(sv.mean())
    Qmat = R_pkg / s_uniform
    orth_Q = float(np.max(np.abs(Qmat.T @ Qmat - np.eye(3))))
    det_Q = float(np.linalg.det(Qmat))
    sv_spread = float(sv.max() - sv.min())

    transform_audit[body] = {
        "orth_max_abs_RtR_minus_I": orth_max,
        "det_R": det_R,
        "singular_values": sv.tolist(),
        "sv_spread": sv_spread,
        "uniform_scale_from_R": s_uniform,
        "fit_scale": scale.tolist(),
        "scaled_rotation_Q": {
            "orth_max_abs_QtQ_minus_I": orth_Q,
            "det_Q": det_Q,
        },
        "t_packet": t_pkg.tolist(),
        "t_fit_fitted_origin": t_fit.tolist(),
        "t_packet_minus_fit_max_abs": float(np.max(np.abs(t_pkg - t_fit))),
        "R_packet_minus_rebuilt_max_abs": float(np.max(np.abs(R_pkg - R_rebuilt))),
        "det_R_expected_s3": float(np.prod(scale)),
        "landmarks_used": landmarks_used,
        "packet_recorded_recon_err": l2w["max_world_reconstruction_error_m"],
    }

# ------------------------------------------------- criterion 2: 32-site reconstruction
site_rows = []
for body in ("radius", "radius_l"):
    bd = packet["bodies"][body]
    l2w = bd["local_to_world"]
    R_pkg = np.asarray(l2w["R_source_local_to_target"], dtype=np.float64)
    t_pkg = np.asarray(l2w["t_fitted_origin_m"], dtype=np.float64)

    # full-precision side
    seg = seg_fit[body]
    Bp = np.asarray(seg["frame_basis"], dtype=np.float64)
    scale = np.asarray(seg["scale"], dtype=np.float64)
    t_fit = np.asarray(seg["fitted_origin"], dtype=np.float64)
    src_lm = corr.source_landmarks
    B = np.column_stack(onb_from_points(
        resolve(src_lm[f"{body}.prox"]), resolve(src_lm[f"{body}.dist"]), resolve(src_lm[f"{body}.roll"])))
    R_full = Bp @ np.diag(scale) @ B.T

    for rec in bd["candidates"]:
        sid = rec["site_id"]
        x = np.asarray(rec["source_pos_local"], dtype=np.float64)
        w_pkg = np.asarray(rec["fitted"]["fitted_pos_global"], dtype=np.float64)
        e_packet = float(np.linalg.norm(t_pkg + R_pkg @ x - w_pkg))
        sf = site_fit[sid]
        x_fit = np.asarray(sf["source_pos_local"], dtype=np.float64)
        w_fit = np.asarray(sf["fitted_pos_global"], dtype=np.float64)
        e_full = float(np.linalg.norm(t_fit + R_full @ x_fit - w_fit))
        e_src = float(np.max(np.abs(x - x_fit)))
        site_rows.append({
            "site_id": sid, "body": body,
            "recon_err_packet_m": e_packet,
            "recon_err_fullprec_m": e_full,
            "src_local_vs_fit_max_abs": e_src,
            "resolved": rec["fitted"]["resolved"],
        })

e_pkt = np.array([r["recon_err_packet_m"] for r in site_rows])
e_full = np.array([r["recon_err_fullprec_m"] for r in site_rows])
worst_pkt = site_rows[int(np.argmax(e_pkt))]["site_id"]
worst_full = site_rows[int(np.argmax(e_full))]["site_id"]
recon = {
    "n_sites": len(site_rows),
    "all_resolved": all(r["resolved"] for r in site_rows),
    "source_local_all_equal_fit": all(r["src_local_vs_fit_max_abs"] == 0.0 for r in site_rows),
    "packet_export_recon_max_m": float(e_pkt.max()),
    "packet_export_recon_mean_m": float(e_pkt.mean()),
    "packet_export_worst_site": worst_pkt,
    "full_precision_recon_max_m": float(e_full.max()),
    "full_precision_recon_mean_m": float(e_full.mean()),
    "full_precision_worst_site": worst_full,
    "claim_step_A_max_m": exp["step_A_verification"]["reconstruction_max_err_m"],
    "rows": site_rows,
}

# ------------------------------------------------- criterion 3: bilateral mirror
# pairing by name: strip/add _l ; verify tendon family identity too
fit_tendon_sites = {t["name"]: t["sites"] for t in fit["tendons"]}


def family_of(site_id: str) -> tuple[str, str]:
    """(family, side): BRD_l-P2 -> ('BRD-P2','l'); BRD-P2 -> ('BRD-P2','r')."""
    if "_l-" in site_id:
        return site_id.replace("_l-", "-"), "l"
    return site_id, "r"


def tendon_family(name: str) -> str:
    return name[:-2] if name.endswith("_tendon") and "_l_tendon" in name else name


pairs = []
right_ids = [r["site_id"] for r in packet["bodies"]["radius"]["candidates"]]
left_ids = {r["site_id"] for r in packet["bodies"]["radius_l"]["candidates"]}
packet_rec = {}
for body in ("radius", "radius_l"):
    for rec in packet["bodies"][body]["candidates"]:
        packet_rec[rec["site_id"]] = rec

all_matched = True
for rid in sorted(right_ids):
    lid = rid.replace("-P", "_l-P")
    if lid not in left_ids:
        all_matched = False
        continue
    fam, _ = family_of(rid)
    assert family_of(lid) == (fam, "l"), (rid, lid)
    # tendon-family identity: membership sets must correspond under _l
    mr = packet_rec[rid]["tendon_membership"]
    ml = packet_rec[lid]["tendon_membership"]
    fam_r = sorted(
        (m["tendon"][:-len("_tendon")], m["index_in_path"], m["path_length"], m["role"])
        for m in mr)
    fam_l = sorted(
        (m["tendon"][:-len("_tendon")][:-2], m["index_in_path"], m["path_length"], m["role"])
        for m in ml)
    tendons_ok = fam_r == fam_l
    # also against the fit's ordered tendon paths
    fit_r = sorted((tn[:-len("_tendon")], p.index(rid) if rid in p else -1, len(p))
                   for tn, p in fit_tendon_sites.items() if rid in p)
    fit_l = sorted((tn[:-len("_tendon")][:-2], p.index(lid) if lid in p else -1, len(p))
                   for tn, p in fit_tendon_sites.items() if lid in p)
    pairs.append({
        "family": fam, "right": rid, "left": lid,
        "tendon_family_ok_packet": tendons_ok,
        "tendon_family_ok_fit": fit_r == fit_l,
    })

# plane from the fit's own data — step A's derivation: mean x of the target-mesh
# pack joints spine_lower/spine_mid/spine_upper (same MonkeyTarget the fit used)
spine_names = ("spine_lower", "spine_mid", "spine_upper")
spine_x = [float(mt.joint_pos(n)[0]) for n in spine_names]
sx_packet = float(np.mean(spine_x))
sx_recorded = float(exp["step_A_verification"]["mirror"]["sagittal_plane_x_m"])

# data-driven plane: mid-x of the paired world points themselves
mid_xs = []
wr = {r["site_id"]: np.asarray(r["fitted"]["fitted_pos_global"]) for r in packet["bodies"]["radius"]["candidates"]}
wl = {r["site_id"]: np.asarray(r["fitted"]["fitted_pos_global"]) for r in packet["bodies"]["radius_l"]["candidates"]}
for p in pairs:
    a, b = wr[p["right"]], wl[p["left"]]
    mid_xs.append(0.5 * (a[0] + b[0]))
plane_points = float(np.mean(mid_xs))

mirror_tables = {}
for tag, plane in (("recorded", sx_recorded), ("packet_spine_mean", sx_packet), ("points_midplane", plane_points), ("zero", 0.0)):
    rows = []
    for p in pairs:
        a, b = wr[p["right"]], wl[p["left"]]
        refl = np.array([2.0 * plane - a[0], a[1], a[2]])
        d = float(np.linalg.norm(refl - b))
        rows.append({"pair": p["family"], "right": p["right"], "left": p["left"],
                     "dist_m": d, "dist_mm": 1000.0 * d,
                     "tendon_family_ok_packet": p["tendon_family_ok_packet"],
                     "tendon_family_ok_fit": p["tendon_family_ok_fit"]})
    ds = np.array([r["dist_m"] for r in rows])
    mirror_tables[tag] = {
        "plane_x_m": plane,
        "n_pairs": len(rows),
        "max_m": float(ds.max()),
        "mean_m": float(ds.mean()),
        "worst_pair": rows[int(np.argmax(ds))]["pair"],
        "n_over_20mm": int((ds > 0.02).sum()),
        "rows": rows,
    }

# mirror_read.json details (synthetic twin; policy evidence only)
R["mirror_read_meta"] = {
    "fit_mode": mirror_read["meta"]["fit_mode"],
    "frame_handedness": mirror_read["meta"]["frame_handedness"],
    "mirror_reflect": mirror_read["meta"].get("mirror_reflect"),
    "handedness": mirror_read["audit"]["correspondence"]["handedness"],
    "mirror_plane_normal": mirror_read["audit"]["correspondence"]["mirror_plane_normal"],
}
R["fit_meta"] = {
    "fit_mode": fit["meta"]["fit_mode"],
    "frame_handedness": fit["meta"]["frame_handedness"],
    "handedness": fit["audit"]["correspondence"]["handedness"],
    "mirror_plane_normal": fit["audit"]["correspondence"]["mirror_plane_normal"],
    "global_scale": fit["audit"]["correspondence"]["global_scale"],
    "chirality_det": fit["residuals"]["chirality_det"],
    "coordinate_conventions_right": fit["meta"]["coordinate_conventions"]["right"],
}

out = {
    "transform_audit": transform_audit,
    "reconstruction": recon,
    "pairing": {"all_right_matched_left": all_matched, "n_pairs": len(pairs),
                "all_tendon_family_ok_packet": all(p["tendon_family_ok_packet"] for p in pairs),
                "all_tendon_family_ok_fit": all(p["tendon_family_ok_fit"] for p in pairs)},
    "spine_x_joints": dict(zip(spine_names, spine_x)),
    "mirror_tables": mirror_tables,
    "meta": {k: R[k] for k in ("mirror_read_meta", "fit_meta")},
}
(AUDIT / "work" / "a4_results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

# ---------------------------------------------------------------- console summary
print("== transform audit ==")
for body, a in transform_audit.items():
    print(body, json.dumps({k: v for k, v in a.items() if k != "landmarks_used"}, indent=1))
    print(" landmarks:", json.dumps(a["landmarks_used"]))
print("== reconstruction ==")
print(json.dumps({k: v for k, v in recon.items() if k != "rows"}, indent=1))
print("== pairing ==")
print(json.dumps(out["pairing"], indent=1))
print("== spine x ==", json.dumps(out["spine_x_joints"]))
for tag, m in mirror_tables.items():
    print(f"== mirror[{tag}] ==", json.dumps({k: v for k, v in m.items() if k != "rows"}))
print("== mirror[recorded] rows ==")
for r_ in mirror_tables["recorded"]["rows"]:
    print(f"  {r_['pair']:<14} {r_['dist_mm']:9.4f} mm  tendon_ok={r_['tendon_family_ok_packet']}/{r_['tendon_family_ok_fit']}")
print("== meta ==")
print(json.dumps(out["meta"], indent=1))
