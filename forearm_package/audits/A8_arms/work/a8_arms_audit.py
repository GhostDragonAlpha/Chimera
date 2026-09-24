"""A8 audit: moment arms + force transmission over the declared forearm pose range.

Independent re-implementation of the moment-arm machinery per DERIVATION.md
  8.1 motion model (hinge axes omega=G*omega_src, hinge center = fitted child origin,
      root free-fly coords arm=0 rigid_reference),
  8.2 analytic gradient (dL/dq sum over polyline segments, subtree membership),
  8.3 central FD eps=5e-7, criterion |analytic-FD|/(1+|FD|) < 1e-9.
Everything is computed from RECORDED artifacts (runs/*.json + source_xml) — the
candidate geometry is RECONSTRUCTED from the recorded (db, dc) and the envelope
frame, no optimization is re-run.

Read-only everywhere except this work/ directory.
"""
from __future__ import annotations

import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from mesh_target_a8 import MonkeyTarget  # noqa: E402  (work-local patched copy)

BASE = Path(r"E:/PythonChimera/forearm_package/baseline_snapshot")
HERE = Path(__file__).parent
RECEIPTS = HERE.parent / "receipts"

FD_EPS_DERIV = 5e-7      # DERIVATION.md 8.3
FD_EPS_CODE = 1e-5       # compiler.py L46 (recorded runs used this)
MATCH_TOL = 1e-9         # DERIVATION.md 8.3 match criterion

ROOT_BODY = "pelvis"


def unit(v):
    n = float(np.linalg.norm(v))
    return v / n


# ------------------------------------------------------------------ artifact load
def load_fit():
    return json.loads((BASE / "runs" / "actual_monkey_fit.json").read_text())


def load_candidates():
    return json.loads((BASE / "runs" / "experiment_transverse_candidate.json").read_text())


def load_attachments():
    return json.loads((BASE / "runs" / "attachment_candidates.json").read_text())


def parse_xml_tree():
    """body name -> parent name (None for root), from XML body nesting."""
    root = ET.parse(str(BASE / "source_xml" / "chimanoid.xml")).getroot()
    parent = {}

    def walk(el, par):
        for b in el.findall("body"):
            parent[b.get("name")] = par
            walk(b, b.get("name"))

    wb = root.find("worldbody")
    walk(wb, None)
    return parent


def parse_xml_joint_ranges():
    """joint name -> range string, first occurrence (direct-child rule per DERIVATION 2)."""
    root = ET.parse(str(BASE / "source_xml" / "chimanoid.xml")).getroot()
    ranges = {}
    for j in root.iter("joint"):
        n = j.get("name")
        if n and n not in ranges:
            ranges[n] = j.get("range")
    return ranges


def subtree(parent_of, body):
    kids = {}
    for c, p in parent_of.items():
        if p is not None:
            kids.setdefault(p, set()).add(c)

    def rec(n):
        s = {n}
        for c in kids.get(n, ()):
            s |= rec(c)
        return s

    return rec(body)


# ------------------------------------------------------------------ arms (own impl)
def analytic_arm(pts, in_sub, jnt, reason_out):
    """dL/dq per DERIVATION 8.2. pts: list of (3,) float or None (unresolved site)."""
    if jnt["body"] == ROOT_BODY:
        reason_out.append("rigid_reference_root")
        return 0.0
    if jnt["status"] == "unresolved_body":
        reason_out.append("unresolved_owner")
        return float("nan")
    if any(p is None for p in pts):
        reason_out.append("path_incomplete")
        return float("nan")
    J = np.asarray(jnt["origin"], dtype=np.float64)
    ax = np.asarray(jnt["axis"], dtype=np.float64)
    if jnt["joint_type"] == "slide":
        arm = 0.0
        for i in range(len(pts) - 1):
            u = pts[i + 1] - pts[i]
            n = float(np.linalg.norm(u))
            if n < 1e-15:
                continue
            u = u / n
            arm += float(u @ ax) * (int(in_sub[i + 1]) - int(in_sub[i]))
        return arm
    arm = 0.0
    for i in range(len(pts) - 1):
        u = pts[i + 1] - pts[i]
        n = float(np.linalg.norm(u))
        if n < 1e-15:
            continue
        u = u / n
        for idx, sgn in ((i, -1.0), (i + 1, +1.0)):
            if not in_sub[idx]:
                continue
            ds = np.cross(ax, pts[idx] - J)
            arm += sgn * float(u @ ds)
    return arm


def analytic_arm_alt(pts, in_sub, jnt):
    """Independent algebraic form used only as an internal crosscheck:
    per-segment d|p_{i+1}-p_i|/dq = u . (w x (p_{i+1}-J)) * in(i+1)
                                  - u . (w x (p_i-J))   * in(i)
    accumulated without the endpoint-pairing shortcut."""
    if jnt["body"] == ROOT_BODY or jnt["status"] == "unresolved_body":
        return float("nan")
    if any(p is None for p in pts):
        return float("nan")
    J = np.asarray(jnt["origin"], dtype=np.float64)
    ax = np.asarray(jnt["axis"], dtype=np.float64)
    if jnt["joint_type"] == "slide":
        return float("nan")  # not used for slides
    total = 0.0
    for i in range(len(pts) - 1):
        seg = pts[i + 1] - pts[i]
        n = float(np.linalg.norm(seg))
        if n < 1e-15:
            continue
        u = seg / n
        d = np.zeros(3)
        if in_sub[i + 1]:
            d = d + np.cross(ax, pts[i + 1] - J)
        if in_sub[i]:
            d = d - np.cross(ax, pts[i] - J)
        total += float(u @ d)
    return total


def rodrigues(ax, dq):
    ax = np.asarray(ax, dtype=np.float64)
    c, s = math.cos(dq), math.sin(dq)
    k = ax
    return np.array([
        [c + k[0] ** 2 * (1 - c), k[0] * k[1] * (1 - c) - k[2] * s, k[0] * k[2] * (1 - c) + k[1] * s],
        [k[1] * k[0] * (1 - c) + k[2] * s, c + k[1] ** 2 * (1 - c), k[1] * k[2] * (1 - c) - k[0] * s],
        [k[2] * k[0] * (1 - c) - k[1] * s, k[2] * k[1] * (1 - c) + k[0] * s, c + k[2] ** 2 * (1 - c)],
    ])


def fd_arm(pts, in_sub, jnt, eps, reason_out):
    """Central FD per DERIVATION 8.3: re-path the polyline under the edited joint."""
    if jnt["body"] == ROOT_BODY:
        reason_out.append("rigid_reference_root")
        return 0.0
    if jnt["status"] == "unresolved_body":
        reason_out.append("unresolved_owner")
        return float("nan")
    if any(p is None for p in pts):
        reason_out.append("path_incomplete")
        return float("nan")
    J = np.asarray(jnt["origin"], dtype=np.float64)
    ax = np.asarray(jnt["axis"], dtype=np.float64)
    sub_ix = [i for i in range(len(pts)) if in_sub[i]]

    def L(dq):
        moved = [np.asarray(p, dtype=np.float64).copy() for p in pts]
        if jnt["joint_type"] == "slide":
            for i in sub_ix:
                moved[i] = moved[i] + ax * dq
        else:
            R = rodrigues(ax, dq)
            for i in sub_ix:
                moved[i] = J + R @ (moved[i] - J)
        return float(sum(float(np.linalg.norm(moved[i + 1] - moved[i])) for i in range(len(moved) - 1)))

    return (L(eps) - L(-eps)) / (2.0 * eps)


# ------------------------------------------------------------------ envelope frame
def band_roll(mt, prox_joint, P, a):
    verts = mt.band_verts(prox_joint)
    rel = verts - P
    perp = rel - np.outer(rel @ a, a)
    d2 = (perp ** 2).sum(axis=1)
    return verts[int(np.argmax(d2))].copy()


def onb(p0, p1, q):
    a = unit(p1 - p0)
    t = (q - p0) - a * (a @ (q - p0))
    b = unit(t)
    c = np.cross(a, b)
    assert abs(np.linalg.det(np.column_stack([a, b, c])) - 1.0) < 1e-9
    return a, b, c


def side_frames(mt, pk):
    P = mt.joint_pos(pk[0])
    P_d = mt.joint_pos(pk[1])
    q = band_roll(mt, pk[0], P, P_d - P)
    a, bu, cu = onb(P, P_d, q)
    return P, P_d, a, bu, cu


# ------------------------------------------------------------------ main
def main() -> int:
    fit = load_fit()
    cand = load_candidates()
    att = load_attachments()
    parent_of = parse_xml_tree()
    xml_ranges = parse_xml_joint_ranges()

    joints = {j["name"]: j for j in fit["joints"]}
    sites = {s["name"]: s for s in fit["sites"]}
    tendons = {t["name"]: t for t in fit["tendons"]}
    muscles = {m.get("tendon"): m for m in fit["muscles"]}

    # ---- the 32 sites and the tendons touching them -------------------------
    names32 = set()
    side_of_site = {}
    for bn, b in att["bodies"].items():
        for r in b["candidates"]:
            names32.add(r["site_id"])
            side_of_site[r["site_id"]] = bn
    touching = [t["name"] for t in fit["tendons"] if names32 & set(t["sites"])]
    touching.sort()
    print(f"[scope] 32-site packet bodies: {sorted(att['bodies'].keys())}")
    print(f"[scope] {len(names32)} sites; tendons touching them: {len(touching)}")

    # ---- subtree sets per joint body ----------------------------------------
    subtrees = {b: subtree(parent_of, b) for b in parent_of}

    def pts_of(tname):
        t = tendons[tname]
        out = []
        for nm, p in zip(t["sites"], t["points"]):
            out.append(None if p is None else np.asarray(p, dtype=np.float64))
        return out

    def in_sub_of(tname, body):
        sub = subtrees[body]
        t = tendons[tname]
        return [sites[nm]["segment"] in sub for nm in t["sites"]]

    # sanity: fitted joint axes unit-norm where finite
    axnorm = {}
    for jn, j in joints.items():
        ax = np.asarray(j["axis"], dtype=np.float64)
        axnorm[jn] = float(np.linalg.norm(ax)) if np.all(np.isfinite(ax)) else None
    bad_axes = {jn: v for jn, v in axnorm.items() if v is not None and abs(v - 1.0) > 1e-9}
    print(f"[axes] non-unit fitted axes (finite): {bad_axes if bad_axes else 'none'}")

    # ================================================== STEP 2/3 census + FD
    census = []
    fd_table = []
    max_ratio = 0.0
    n_ratio = 0
    n_nan_both = 0
    n_zero = 0
    nonzero_pairs = []
    recorded_mismatch = 0.0
    recorded_fd_mismatch_eps5 = None
    for tname in touching:
        t = tendons[tname]
        pts = pts_of(tname)
        insub_cache = {}
        for jn, j in joints.items():
            if j["body"] not in insub_cache:
                insub_cache[j["body"]] = in_sub_of(tname, j["body"])
            in_sub = insub_cache[j["body"]]
            rsn: list[str] = []
            a_mine = analytic_arm(pts, in_sub, j, rsn)
            a_alt = analytic_arm_alt(pts, in_sub, j)
            # recorded value from the fit packet
            rec = next((m for m in t["moment_arms"] if m["coord"] == jn), None)
            a_rec = rec["analytic"] if rec else None
            if a_rec is not None and math.isfinite(a_mine):
                recorded_mismatch = max(recorded_mismatch, abs(a_mine - a_rec))
            finite = math.isfinite(a_mine)
            if finite and abs(a_mine) > 0.0:
                nonzero_pairs.append((tname, jn, a_mine))
            if finite and a_mine == 0.0:
                n_zero += 1
            alt_diff = (abs(a_mine - a_alt)
                        if (finite and math.isfinite(a_alt) and j["joint_type"] != "slide") else None)
            census.append({
                "tendon": tname, "coord": jn, "coord_body": j["body"],
                "analytic": a_mine, "recorded_analytic": a_rec,
                "alt_form_diff": alt_diff, "reason": "|".join(rsn) or "computed",
            })
            # FD crosscheck (both epsilons)
            rfd: list[str] = []
            fd = fd_arm(pts, in_sub, j, FD_EPS_DERIV, rfd)
            fd5 = fd_arm(pts, in_sub, j, FD_EPS_CODE, rfd)
            entry = {
                "tendon": tname, "coord": jn, "analytic": a_mine,
                "fd_eps5e7": fd, "fd_eps1e5": fd5, "reason": "|".join(rsn) or "computed",
            }
            if math.isfinite(a_mine) and math.isfinite(fd):
                ratio = abs(a_mine - fd) / (1.0 + abs(fd))
                entry["ratio_eps5e7"] = ratio
                max_ratio = max(max_ratio, ratio)
                n_ratio += 1
                if recorded_fd_mismatch_eps5 is None and math.isfinite(fd5):
                    recorded_fd_mismatch_eps5 = 0.0
                if math.isfinite(fd5):
                    recorded_fd_mismatch_eps5 = max(
                        recorded_fd_mismatch_eps5, abs(fd5 - (rec["finite_difference"] if rec else fd5)))
            else:
                n_nan_both += 1
                entry["ratio_eps5e7"] = None
            fd_table.append(entry)
    print(f"[census] finite pairs={sum(1 for c in census if math.isfinite(c['analytic']))} "
          f"zero pairs={n_zero} NONZERO pairs={len(nonzero_pairs)} nan pairs={n_nan_both}")
    print(f"[fd] finite compared={n_ratio} max|a-fd|/(1+|fd|) @eps=5e-7 = {max_ratio:.3e} (tol 1e-9)")
    print(f"[rec] max |my_analytic - recorded_analytic| = {recorded_mismatch:.3e}")
    if recorded_fd_mismatch_eps5 is not None:
        print(f"[rec] max |my_fd@1e-5 - recorded_fd(1e-5)| = {recorded_fd_mismatch_eps5:.3e}")
    alt_max = max((c["alt_form_diff"] for c in census if c["alt_form_diff"] is not None), default=None)
    print(f"[alt] max |endpoint-pairing form - per-segment form| = {alt_max if alt_max is None else f'{alt_max:.3e}'}")

    # ================================================== STEP 1 zero-arm law
    mt = MonkeyTarget()
    print(f"[mesh] birth sha {mt.birth_sha[:16]}... pack sha {mt.pack_sha[:16]}...")
    man = json.loads((BASE / "MANIFEST.json").read_text())
    exp_birth = man["files"]["inputs/monkey_birth.bin"]["sha256"]
    exp_pack = man["files"]["inputs/monkey_joints.bin"]["sha256"]
    mesh_sha_ok = (mt.birth_sha.upper() == exp_birth.upper()
                   and mt.pack_sha.upper() == exp_pack.upper())  # MANIFEST lowercase, loader upper()
    print(f"[mesh] input hashes match MANIFEST: {mesh_sha_ok}")

    frames = {}
    for body, pk in (("radius", ("elbow_R", "wrist_R")), ("radius_l", ("elbow_L", "wrist_L"))):
        P, P_d, a, bu, cu = side_frames(mt, pk)
        frames[body] = dict(P=P, P_d=P_d, a=a, bu=bu, cu=cu)

    step_c = cand["step_C_candidate"]
    db_r, dc_r = step_c["radius"]["db_m"], step_c["radius"]["dc_m"]
    db_l, dc_l = step_c["radius_l"]["db_m"], step_c["radius_l"]["dc_m"]
    print(f"[cand] recorded db,dc right=({db_r},{dc_r}) left=({db_l},{dc_l})")

    # candidate positions: recorded baseline + recorded (db,dc) in the rebuilt frame
    shift = {}
    disp_check = {}
    for nm in names32:
        s = sites[nm]
        f = frames[side_of_site[nm]]
        db, dc = (db_r, dc_r) if side_of_site[nm] == "radius" else (db_l, dc_l)
        v = db * f["bu"] + dc * f["cu"]
        shift[nm] = np.asarray(s["fitted_pos_global"], dtype=np.float64) + v
        disp_check[nm] = float(np.linalg.norm(v))

    rec_disp = step_c["radius"]["per_site_displacement_m"]
    disp_err = max(abs(disp_check[nm] - rec_disp[nm]) for nm in rec_disp)
    print(f"[cand] max |rebuilt displacement - recorded per_site_displacement_m| = {disp_err:.3e} m "
          f"(recorded rounding 1e-9)")

    def arm_set(use_candidate):
        def pos(nm):
            if nm in shift and use_candidate:
                return shift[nm]
            p = sites[nm]["fitted_pos_global"]
            return None if p is None else np.asarray(p, dtype=np.float64)

        out = {}
        for tname in touching:
            t = tendons[tname]
            pts = [pos(nm) for nm in t["sites"]]
            for jn, j in joints.items():
                sub = subtrees[j["body"]]
                in_sub = [sites[nm]["segment"] in sub for nm in t["sites"]]
                r: list[str] = []
                out[(tname, jn)] = analytic_arm(pts, in_sub, j, r)
        return out

    arms_b = arm_set(False)
    arms_c = arm_set(True)
    both_finite = [(k, arms_b[k], arms_c[k]) for k in arms_b
                   if math.isfinite(arms_b[k]) and math.isfinite(arms_c[k])]
    nan_b = sum(1 for k in arms_b if not math.isfinite(arms_b[k]))
    nan_c = sum(1 for k in arms_c if not math.isfinite(arms_c[k]))
    nan_mismatch = [k for k in arms_b if math.isfinite(arms_b[k]) != math.isfinite(arms_c[k])]
    max_delta = max(abs(c - b) for _, b, c in both_finite)
    max_abs_arm = max(abs(b) for _, b, _ in both_finite)
    max_nonzero_base = max((abs(b) for _, b, c in both_finite if b != 0.0), default=0.0)
    print(f"[zero-law] pairs={len(arms_b)} finite-both={len(both_finite)} "
          f"nan base={nan_b} nan cand={nan_c} nan-mismatch={len(nan_mismatch)}")
    print(f"[zero-law] max |arm_cand - arm_base| over finite pairs = {max_delta:.3e} m "
          f"(floor: recorded deltas round(,12); max abs arm value = {max_abs_arm:.3e})")
    print(f"[zero-law] max nonzero |arm| in baseline finite set = {max_nonzero_base:.3e}")

    rec_deltas = {k: v["moment_arm_max_abs_delta_m"] for k, v in cand["tendon_deltas"].items()
                  if k in touching}
    rec_delta_max = max(v for v in rec_deltas.values() if v is not None)
    print(f"[zero-law] recorded moment_arm_max_abs_delta_m over the {len(rec_deltas)} scoped tendons: "
          f"max={rec_delta_max!r}")

    # path-length deltas for comparable scoped tendons (BRD/BRD_l) as a crosscheck
    pl = {}
    for tname in touching:
        t = tendons[tname]
        pts_b = [np.asarray(p, dtype=np.float64) for p in t["points"] if p is not None]
        pts_c = [(shift.get(nm) if shift.get(nm) is not None else np.asarray(p, dtype=np.float64))
                 for nm, p in zip(t["sites"], t["points"]) if p is not None]
        if len(pts_b) == len(t["sites"]):
            lb = sum(float(np.linalg.norm(pts_b[i + 1] - pts_b[i])) for i in range(len(pts_b) - 1))
            lc = sum(float(np.linalg.norm(pts_c[i + 1] - pts_c[i])) for i in range(len(pts_c) - 1))
            pl[tname] = lc - lb
    for k, v in pl.items():
        rec_v = cand["tendon_deltas"][k]["path_length_delta_m"]
        print(f"[pl] {k}: recomputed dL={v:.12f} m  recorded={rec_v} m  |diff|={abs(v-rec_v):.3e}")

    # ================================================== STEP 4 window audit
    window = []
    for tname in touching:
        t = tendons[tname]
        m = muscles.get(tname)
        L0 = t["rest_length"]
        lrf = m["lengthrange_fitted"] if m else None
        lrs = m["lengthrange_src"] if m else None
        row = {
            "tendon": tname, "status": t["status"],
            "unresolved_in_chain": sorted({sites[nm]["segment"] for nm in t["sites"]
                                           if sites[nm]["unresolved"]}),
            "L0": L0, "lengthrange_src": lrs, "lengthrange_fitted": lrf,
            "force": m["force"] if m else None,
            "timeconst": m["timeconst"] if m else None,
            "phys_flag": None,
        }
        if lrf is not None and L0 is not None:
            lo, hi = lrf
            inside = lo <= L0 <= hi
            row["L0_inside"] = inside
            row["margin_lo_m"] = L0 - lo
            row["margin_hi_m"] = hi - L0
            row["excursion_margin_m"] = min(L0 - lo, hi - L0)
        else:
            row["L0_inside"] = None
            row["excursion_margin_m"] = None
        if m and m["status"] == "path:derived|physiology:requires_physiological_rerun":
            row["phys_flag"] = "requires_physiological_rerun"
        elif m:
            row["phys_flag"] = "path_incomplete (no lengthrange' computed; force/timeconst ingested_unchanged)"
        window.append(row)

    # q-ranges: XML verbatim vs fitted-carried, for the arm-chain coordinates
    arm_coords = ["shoulder_elv", "shoulder_rot", "elv_angle", "elbow_flexion",
                  "wrist_dev_r", "wrist_flex_r", "wrist_3_r",
                  "shoulder_elv_l", "shoulder_rot_l", "elv_angle_l", "elbow_flexion_l",
                  "wrist_dev_l", "wrist_flex_l", "wrist_3_l"]
    ranges = {}
    for jn in arm_coords:
        j = joints[jn]
        xr = xml_ranges.get(jn)
        fitted = j["range"]
        verbatim = None
        if xr is not None:
            xs = [float(v) for v in xr.split()]
            verbatim = (abs(xs[0] - fitted[0]) < 1e-12 and abs(xs[1] - fitted[1]) < 1e-12)
        ranges[jn] = {"body": j["body"], "status": j["status"], "range_fitted": fitted,
                      "range_xml": xr, "verbatim_match": verbatim,
                      "axis_finite": bool(np.all(np.isfinite(np.asarray(j["axis"], dtype=np.float64))))}

    # elbow-entry index + straightness of the resolved run
    runs = {}
    for tname in touching:
        t = tendons[tname]
        stem = tname[: -len("_tendon")]
        sub = subtrees["ulna_l"] if stem.endswith("_l") else subtrees["ulna"]
        entry = next((i for i, nm in enumerate(t["sites"]) if sites[nm]["segment"] in sub), None)
        # resolved (finite) run
        fin = [i for i, p in enumerate(t["points"]) if p is not None]
        straight = None
        max_dev = None
        if len(fin) >= 3:
            pr = [np.asarray(t["points"][i], dtype=np.float64) for i in fin]
            d = pr[-1] - pr[0]
            Ln = float(np.linalg.norm(d))
            if Ln > 1e-12:
                devs = [float(np.linalg.norm(np.cross(unit(d), p - pr[0]))) for p in pr[1:-1]]
                max_dev = max(devs)
                straight = max_dev
        runs[tname] = {"elbow_entry_index": entry, "n_resolved_pts": len(fin),
                       "max_interior_offline_dev_m": max_dev,
                       "resolved_run_endpoints": [t["sites"][fin[0]], t["sites"][fin[-1]]] if fin else None}

    # ---------------------------------------------------------------- dump
    out = {
        "scope": {"n_sites": len(names32), "n_tendons": len(touching), "tendons": touching,
                  "site_bodies": sorted(att["bodies"].keys())},
        "mesh_input_hashes_match_manifest": mesh_sha_ok,
        "step1_zero_law": {
            "n_pairs": len(arms_b), "n_finite_both": len(both_finite),
            "n_nan_base": nan_b, "n_nan_cand": nan_c,
            "n_finiteness_mismatch": len(nan_mismatch),
            "max_abs_delta": max_delta, "max_abs_arm_finite": max_abs_arm,
            "max_nonzero_baseline_arm": max_nonzero_base,
            "recorded_scoped_max_delta": rec_delta_max,
            "db_dc_recorded": {"radius": [db_r, dc_r], "radius_l": [db_l, dc_l]},
            "displacement_rebuild_max_err_m": disp_err,
            "path_length_deltas": pl,
        },
        "step2_census": census,
        "nonzero_pairs": [{"tendon": t, "coord": c, "value": v} for t, c, v in nonzero_pairs],
        "step3_fd": {"eps_deriv": FD_EPS_DERIV, "tol": MATCH_TOL,
                     "n_compared": n_ratio, "max_ratio": max_ratio,
                     "n_nan_both": n_nan_both,
                     "recorded_fd_mismatch_eps1e5": recorded_fd_mismatch_eps5},
        "step4_window": window,
        "ranges": ranges,
        "runs": runs,
        "census_max_recorded_mismatch": recorded_mismatch,
        "alt_form_max_diff": alt_max,
    }
    (RECEIPTS / "a8_arms_results.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"[out] receipts/a8_arms_results.json written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
