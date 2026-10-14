"""THE ANGLE-DIRECTION MEASURED ARM CURVE (lane ankle-arms-20260921).

Closes the hind torque book's one BLOCKED cell (b17cbf6c): the ankle
(plantarflexion/dorsiflexion) direction had no measured arm-versus-angle
curve, so its 7.4 N.m cap stayed doc-derived while the admitted record's
straight-line ankle arms fell 1.8-3.7x short of the 5.9171 N.m Oku measured
walk demand.

This module:
  (1) mines the Wiseman macaque model's ANKLE-CROSSING paths (shank_r ->
      foot_r): SOL, MG, LG, TA, TP, PB, PL, EDL II-V, EHL, FDL II-V, FHL -
      17 path entries, 17 SI-compared muscles (FDL II/III/IV share one
      identical SI value triple);
  (2) derives their -dL/dq arm curves over each muscle's SI 2 recorded
      jrange with the pulley lane's EXACT tangent-wrapping machinery
      (imported from the sha-pinned derive_pulley_arms module - cylinders,
      the ellipsoid, quadrant rule, <= pi arcs, fd step 1e-4 rad), the
      scan that makes the FDL/FHL/TP ankle wraps LIVE (they were rigid
      during the pulley lane's MTP scan - the hind book's named future
      work);
  (3) verifies the curves against SI 2's macaque AnkleFE rows (the
      independent authors' reference) under the pulley protocol: unit
      membrane (mm vs cm), the k = 0.11975394 per-taxon scale gate
      (fitted over the point-only ankle class against the MTP-class
      spread; wrapped rows against the knee-class k-scaled tolerance),
      per-muscle sign pattern, triceps magnitude ordering;
  (4) re-derives the ankle torque cap: cap = max over the measured scan of
      sum_m F_m |r_m(q)|, sign-gated per muscle (a muscle contributes only
      where its arm's sign matches the direction), under V1 (Oku measured
      walk forces) and V2 (the record's PCSA x sigma law, PROVISIONAL), on
      S1 (deposit arms) and S2 (arms x k, the k-gated variant), plus walk
      windows under both scene-sense mappings, the triceps-only
      sub-envelope and the FDL slip partition bracket;
  (5) computes the consumption deltas the hind book could not: the
      stance-hold ankle node ratios at cap_new and the ankle chain's
      height-law authority factor (the book's "delta 0 (blocked)" cell).

Read-only over every input (each sha256-verified against receipt.json's
pins at load; REFUSES on mismatch); writes ONLY ankle_arms_book.json inside
this directory (or --out). Pure function of the pinned inputs:
byte-deterministic by construction.

Run from the repo root:
  python -B tools/science_funnel/validation/ankle_arms_20260921/derive_ankle_arms.py
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RECEIPT_PATH = HERE / "receipt.json"
PULLEY_DIR = REPO / "tools/science_funnel/validation/pulley_rederivation_20260920"
sys.path.insert(0, str(PULLEY_DIR))
import derive_pulley_arms as P  # noqa: E402  (the sha-pinned machinery)

OUT_JSON = HERE / "ankle_arms_book.json"

K_GATE = 0.11975394                 # the pulley receipt's fitted per-taxon scalar (S2)
K_MTP_SPREAD = (0.1197283, 0.11976842)
COORD = "r_ankle_flexion"
PHYSICAL_JOINT = "ankle_r"
FD_STEP = 1.0e-4                    # rad, the lane's central-difference step
N_SCAN = 2001                       # samples across each recorded jrange
GRID_STEP_DEG = 0.05

# the point-only ankle class (no wrap references in the model) - the k-fit class
POINT_ONLY = ("R_SOL", "R_MG", "R_TA", "R_PB", "R_PL", "R_EHL")
# the wrapped rows and the surfaces they reference in the deposit
WRAPPED = {"R_FDL_TENDONII": "R_Ankle_Cylinder", "R_FDL_TENDONIII": "R_Ankle_Cylinder",
           "R_FDL_TENDONIV": "R_Ankle_Cylinder", "R_FHL": "R_Ankle_Cylinder",
           "R_TP": "R_Ankle_Cylinder", "R_FDL_TENDONV": "rDistalTibia_ellipsoid",
           "R_LG": "rProxTibiaCylinder (active=false in the deposit)"}
# load-bearing ankle-pulley muscles (zero engagement on R_Ankle_Cylinder = FAIL)
MUST_ENGAGE = ("R_FDL_TENDONII", "R_FDL_TENDONIII", "R_FDL_TENDONIV",
               "R_FHL", "R_TP")
TRICEPS_ORDER = ("R_MG", "R_LG", "R_SOL")   # |MG| > |LG| > |SOL| at both endpoints

# direction classes: muscle -> class membership is decided by the model paths;
# force assignment per variant below. Sign law: plantarflexion arms negative,
# dorsiflexion arms positive under r = -dL/dq on r_ankle_flexion.
PLANTAR_CLASS = ("R_SOL", "R_MG", "R_LG", "R_FDL_TENDONII", "R_FDL_TENDONIII",
                 "R_FDL_TENDONIV", "R_FDL_TENDONV", "R_FHL", "R_TP", "R_PB", "R_PL")
DORSAL_CLASS = ("R_TA", "R_EDL_TENDONII", "R_EDL_TENDONIII", "R_EDL_TENDONIV",
                "R_EDL_TENDONV", "R_EHL")
V1_PLANTAR_FORCES = [  # (muscle, source) - F resolved at run time from pinned inputs
    ("R_SOL", "oku:SOL"), ("R_MG", "gas_split:MG"), ("R_LG", "gas_split:LG"),
    ("R_FDL_TENDONII", "fdl_quarter"), ("R_FDL_TENDONIII", "fdl_quarter"),
    ("R_FDL_TENDONIV", "fdl_quarter"), ("R_FDL_TENDONV", "fdl_quarter"),
]
V2_PLANTAR_FORCES = [
    ("R_SOL", "record:SOL"), ("R_MG", "record:MG"), ("R_LG", "record:LG"),
    ("R_FDL_TENDONII", "record:FDL_quarter"), ("R_FDL_TENDONIII", "record:FDL_quarter"),
    ("R_FDL_TENDONIV", "record:FDL_quarter"), ("R_FDL_TENDONV", "record:FDL_quarter"),
    ("R_FHL", "record:FHL"), ("R_TP", "record:TP_ABSENT_named_gap"),
    ("R_PB", "record:PB"), ("R_PL", "record:PL"),
]
V1_DORSAL_FORCES = [("R_TA", "oku:TA"),
                    ("R_EDL_TENDONII", "oku:EDL_quarter"), ("R_EDL_TENDONIII", "oku:EDL_quarter"),
                    ("R_EDL_TENDONIV", "oku:EDL_quarter"), ("R_EDL_TENDONV", "oku:EDL_quarter")]
V2_DORSAL_FORCES = [("R_TA", "record:TA"),
                    ("R_EDL_TENDONII", "record:EDL_quarter"), ("R_EDL_TENDONIII", "record:EDL_quarter"),
                    ("R_EDL_TENDONIV", "record:EDL_quarter"), ("R_EDL_TENDONV", "record:EDL_quarter"),
                    ("R_EHL", "record:EHL")]


# ---------------------------------------------------------------- helpers

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode("utf-8")


def interp_arm(direction: dict, deg: float) -> float:
    """Linear interpolation of a stored 201-sample measured curve (the hind
    book's convention when it consumed the pulley deliverable)."""
    lo, hi = direction["jrange_deg"]
    s = direction["arm_samples_m"]
    n = len(s)
    x = (deg - lo) / (hi - lo) * (n - 1)
    i = int(x)
    if i < 0 or i > n - 1:
        raise KeyError(f"deg {deg} outside measured scan [{lo}, {hi}]")
    if i == n - 1:
        i, f = n - 2, 1.0
    else:
        f = x - i
    return s[i] * (1.0 - f) + s[i + 1] * f


def common_grid(directions: list, step_deg: float = GRID_STEP_DEG) -> list:
    lo = max(min(d["jrange_deg"]) for d in directions)
    hi = min(max(d["jrange_deg"]) for d in directions)
    if lo > hi:
        raise ValueError(f"empty scan intersection [{lo}, {hi}]")
    n = int(round((hi - lo) / step_deg))
    grid = [lo + k * step_deg for k in range(n + 1)]
    if abs(grid[-1] - hi) > 1e-9:
        grid.append(hi)
    return grid


def signed_envelope(directions: list, forces: list, grid: list, dir_sign: int):
    """tau(q) = sum_m F_m |r_m(q)| over muscles whose arm sign matches the
    direction at q (the declared sign law). forces: list of (F_N, name) with
    F > 0 only; F = 0 entries contribute nothing (named gaps)."""
    samples = []
    per_muscle_at_argmax = None
    best = (-1.0, None)
    for q in grid:
        tau = 0.0
        used = {}
        for (f, name), d in zip(forces, directions):
            if f <= 0.0:
                continue
            r = interp_arm(d, q)
            if dir_sign > 0 and r > 0.0:
                tau += f * r
                used[name] = r
            elif dir_sign < 0 and r < 0.0:
                tau += f * abs(r)
                used[name] = r
        samples.append({"q_deg": round(q, 4), "tau_N_m": round(tau, 6)})
        if tau > best[0]:
            best = (tau, round(q, 4))
            per_muscle_at_argmax = {k: round(v, 6) for k, v in used.items()}
    return samples, best[0], best[1], per_muscle_at_argmax


# ---------------------------------------------------------------- inputs

def load_inputs():
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    pins = receipt["pre_registration"]["inputs_pinned"]
    for key, pin in pins.items():
        p = REPO / pin["path"]
        got = sha256_file(p)
        if got != pin["sha256"]:
            raise SystemExit(
                f"REFUSAL: input sha mismatch {key} ({pin['path']}): {got} != {pin['sha256']}")
    mach_sha = sha256_file(Path(P.__file__))
    if mach_sha != pins["pulley_machinery"]["sha256"]:
        raise SystemExit(f"REFUSAL: imported machinery sha mismatch: {mach_sha}")
    geo = json.loads((REPO / pins["muscle_path_geometry_snapshot"]["path"]).read_text(encoding="utf-8"))
    oku = json.loads((REPO / pins["derived_numbers_snapshot"]["path"]).read_text(encoding="utf-8"))
    zeros = json.loads((REPO / pins["derived_zeros_snapshot"]["path"]).read_text(encoding="utf-8"))
    hold = json.loads((REPO / pins["stance_hold_snapshot"]["path"]).read_text(encoding="utf-8"))
    contract = json.loads((REPO / pins["gait_contract_drives_snapshot"]["path"]).read_text(encoding="utf-8"))
    hind = json.loads((REPO / pins["hind_book"]["path"]).read_text(encoding="utf-8"))
    return receipt, pins, geo, oku, zeros, hold, contract, hind


def read_si2_ankle_rows(receipt):
    """First-occurrence macaque AnkleFE rows straight from the sha-pinned
    xlsx, verified against the receipt's pre-registered transcription
    (refuse on any drift - the receipt's prior IS the pinned reading)."""
    import openpyxl
    si2_path = REPO / receipt["pre_registration"]["inputs_pinned"]["si2"]["path"]
    wb = openpyxl.load_workbook(si2_path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    first = {}
    for i, r in enumerate(rows):
        if r[0] == "AnkleFE" and r[1] == "macaque":
            muscle = r[2]
            if muscle not in first:
                first[muscle] = {"row": i + 1, "min": float(r[3]), "max": float(r[4]),
                                 "jrange_deg": [float(r[6]), float(r[7])]}
    wb.close()
    prior = receipt["prior_reading"]["si2_anklefe_macaque_rows"]["rows_first_occurrence"]
    if set(first) != set(prior):
        raise SystemExit(f"REFUSAL: SI2 ankle muscle set drift: {set(first) ^ set(prior)}")
    for m, p in prior.items():
        got = first[m]
        if (got["row"] != p["row"] or got["min"] != p["min"] or got["max"] != p["max"]
                or got["jrange_deg"] != list(p["jrange_deg"])):
            raise SystemExit(f"REFUSAL: SI2 row drift for {m}: {got} != {p}")
    return first


# ---------------------------------------------------------------- derivation

def derive_ankle_muscle(model, muscle, jrange_deg, n=N_SCAN):
    """The pulley lane's derive_muscle, generalized to the ankle: coordinate
    r_ankle_flexion, physical joint ankle_r, fd = -dL/dq step 1e-4 rad,
    advisory geometric arm on the joint-spanning segment, per-wrap
    engagement bookkeeping. Machinery primitives imported unmodified."""
    lo_deg, hi_deg = jrange_deg
    qs_deg = np.linspace(lo_deg, hi_deg, n)
    qs = qs_deg * (math.pi / 180.0)
    arms = np.empty(n)
    geos = np.empty(n)
    engaged = {}
    contact_samples = {}
    for k, qv in enumerate(qs):
        fk = P.forward_kinematics(model, {COORD: float(qv)})
        _, contacts, _L = P.resolve_path(model, muscle, fk)
        Lp = P.resolve_path(model, muscle,
                            P.forward_kinematics(model, {COORD: float(qv) + FD_STEP}))[2]
        Lm = P.resolve_path(model, muscle,
                            P.forward_kinematics(model, {COORD: float(qv) - FD_STEP}))[2]
        arms[k] = -(Lp - Lm) / (2.0 * FD_STEP)
        axis, origin = P.pin_joint_world_axis(model, fk, PHYSICAL_JOINT)
        geos[k] = P.geometric_arm(model, muscle, fk, axis, origin,
                                  joint_name=PHYSICAL_JOINT)
        for c in contacts:
            e = engaged.setdefault(c["wrap"], [0, 0])
            e[1] += 1
            if c["engaged"]:
                e[0] += 1
        if k in (0, n // 2, n - 1):
            contact_samples[int(k)] = [
                {"wrap": c["wrap"], "engaged": c["engaged"],
                 "arc_rad": (float(c["arc_rad"]) if c["engaged"] else None),
                 "reason": (None if c["engaged"] else c["reason"])}
                for c in contacts]
    imin, imax = int(np.argmin(arms)), int(np.argmax(arms))
    gmin, gmax = int(np.argmin(geos)), int(np.argmax(geos))
    return {
        "muscle": muscle,
        "coordinate": COORD,
        "physical_joint": PHYSICAL_JOINT,
        "jrange_deg": [float(lo_deg), float(hi_deg)],
        "r_fd_min_m": float(arms[imin]),
        "r_fd_max_m": float(arms[imax]),
        "r_fd_min_at_deg": float(qs_deg[imin]),
        "r_fd_max_at_deg": float(qs_deg[imax]),
        "r_geo_min_m": float(geos[gmin]),
        "r_geo_max_m": float(geos[gmax]),
        "fd_geo_max_abs_diff_mm": float(np.max(np.abs(arms - geos)) * 1e3),
        "arm_samples_m": [float(v) for v in arms[::max(1, n // 200)]],
        "geo_samples_m": [float(v) for v in geos[::max(1, n // 200)]],
        "wrap_engaged_of_scanned": {k: v for k, v in engaged.items()},
        "contact_samples": contact_samples,
        "wraps_referenced": [c for c in (WRAPPED.get(muscle, "").split(" (")[0],) if c],
    }


# ---------------------------------------------------------------- SI2 comparison

def compare_si2(si_rows, arms):
    rows = {}
    k_rows = []
    for muscle, si in sorted(si_rows.items()):
        d = arms[muscle]
        fd_min_mm = d["r_fd_min_m"] * 1e3
        fd_max_mm = d["r_fd_max_m"] * 1e3

        def verdict(si_val, fd_mm):
            kr = si_val / fd_mm if abs(fd_mm) > 1e-12 else None
            if muscle in POINT_ONLY and kr is not None:
                k_rows.append(kr)
            return {
                "mm_residual": round(fd_mm - si_val, 6),
                "cm_residual": round(fd_mm / 10.0 - si_val, 6),
                "within_tol_mm": bool(abs(fd_mm - si_val)
                                      <= max(0.25, 0.25 * abs(si_val))),
                "within_tol_cm": bool(abs(fd_mm / 10.0 - si_val)
                                      <= max(0.25, 0.25 * abs(si_val))),
                "k_scaled_residual_mm": round(fd_mm * K_GATE - si_val, 6),
                "within_tol_k": bool(abs(fd_mm * K_GATE - si_val)
                                     <= max(0.25, 0.25 * abs(si_val))),
                "k_this_row": round(kr, 8) if kr is not None else None,
            }
        rows[muscle] = {
            "si2_row": si["row"], "si2_min": si["min"], "si2_max": si["max"],
            "jrange_deg": si["jrange_deg"],
            "derived_min_mm": round(fd_min_mm, 6), "derived_max_mm": round(fd_max_mm, 6),
            "derived_min_at_deg": d["r_fd_min_at_deg"], "derived_max_at_deg": d["r_fd_max_at_deg"],
            "wrap_class": ("point_only" if muscle in POINT_ONLY else WRAPPED.get(muscle, "unknown")),
            "sign_match": bool(np.sign(si["min"]) == np.sign(fd_min_mm)
                               and np.sign(si["max"]) == np.sign(fd_max_mm)),
            "endpoints": {"min": verdict(si["min"], fd_min_mm),
                          "max": verdict(si["max"], fd_max_mm)},
        }
    k_ankle = float(np.mean(k_rows))
    k_spread = (float(min(k_rows)), float(max(k_rows)))
    in_mm = all(r["endpoints"][e]["within_tol_mm"] for r in rows.values() for e in ("min", "max"))
    in_cm = all(r["endpoints"][e]["within_tol_cm"] for r in rows.values() for e in ("min", "max"))
    order_min = (abs(rows["R_MG"]["derived_min_mm"]) > abs(rows["R_LG"]["derived_min_mm"])
                 > abs(rows["R_SOL"]["derived_min_mm"]))
    order_max = (abs(rows["R_MG"]["derived_max_mm"]) > abs(rows["R_LG"]["derived_max_mm"])
                 > abs(rows["R_SOL"]["derived_max_mm"]))
    return {
        "pre_registered_tolerance": "per endpoint |derived - SI| <= max(0.25 mm, 0.25*|SI|) "
                                    "under exactly one unit hypothesis; wrapped rows additionally "
                                    "under SI = derived x k_mtp",
        "unit_verdict": {
            "mm_hypothesis_all_within_tolerance": in_mm,
            "cm_hypothesis_all_within_tolerance": in_cm,
            "pre_registered_requirement": "exactly one of {mm, cm} inside band",
            "outcome": ("mm" if in_mm and not in_cm else
                        "cm" if in_cm and not in_mm else
                        "INVALID - no single raw unit hypothesis survives"),
        },
        "k_gate": {
            "k_ankle_point_class_fitted": round(k_ankle, 8),
            "k_ankle_point_class_spread": [round(k_spread[0], 8), round(k_spread[1], 8)],
            "mtp_class_spread_pre_registered": list(K_MTP_SPREAD),
            "k_ankle_inside_mtp_spread": bool(K_MTP_SPREAD[0] <= k_ankle <= K_MTP_SPREAD[1]),
            "k_used_for_S2": K_GATE,
            "k_provenance": "fitted over the point-only ankle class (SOL, MG, TA, PB, PL, EHL: "
                            "no wrap references - pure point geometry, the MTP-class situation); "
                            "the S2 cap variant uses the pulley receipt's constant "
                            "k = 0.11975394 (the hind book's S2 gate)",
        },
        "triceps_ordering": {"expected": "|MG| > |LG| > |SOL| at both endpoints (SI 2)",
                             "min_endpoint_held": bool(order_min),
                             "max_endpoint_held": bool(order_max)},
        "sign_pattern_all_match": bool(all(r["sign_match"] for r in rows.values())),
        "rows": rows,
    }


# ---------------------------------------------------------------- cap book

def build_direction_book(name, dir_sign, class_names, force_spec, arms, si_rows,
                         forces_ctx, current_cap, demand, walk_window_deg, trace_ctx):
    members = [n for n, _f in force_spec]
    dirs = [arms[m] for m in members]
    grid = common_grid([{"jrange_deg": d["jrange_deg"]} for d in dirs])
    forces = [(f, m) for (m, _src), f in zip(force_spec, [forces_ctx[s] for _m, s in force_spec])]
    samples, cap, argmax, at_argmax = signed_envelope(dirs, forces, grid, dir_sign)
    s2 = cap * K_GATE
    # walk windows under both scene-sense mappings
    wins = {}
    for label, window in walk_window_deg.items():
        lo = max(min(grid), min(window))
        hi = min(max(grid), max(window))
        if lo <= hi:
            sub = [q for q in grid if lo - 1e-9 <= q <= hi + 1e-9]
            _s, c, a, _u = signed_envelope(dirs, forces, sub, dir_sign)
            wins[label] = {"scene_window_deg": [round(x, 4) for x in window],
                           "evaluated_overlap_deg": [round(lo, 4), round(hi, 4)],
                           "cap_N_m": round(c, 6), "argmax_q_deg": a,
                           "note": "evaluated ONLY on the measured overlap - no extrapolation"}
        else:
            wins[label] = {"scene_window_deg": [round(x, 4) for x in window],
                           "evaluated_overlap_deg": None,
                           "note": "no measured overlap - never extrapolated"}
    extrema = {m: {"extrema_mm": [round(arms[m]["r_fd_min_m"] * 1e3, 4),
                                  round(arms[m]["r_fd_max_m"] * 1e3, 4)],
                   "jrange_deg": arms[m]["jrange_deg"],
                   "si2_row": si_rows[m]["row"] if m in si_rows else None}
               for m in members}
    return {
        "direction": name,
        "sign_convention": "r = -dL/dq on r_ankle_flexion; plantarflexion arms NEGATIVE, "
                           "dorsiflexion arms POSITIVE; the scene drive "
                           "ankle_dorsiflexion is dorsiflexion-positive like the model "
                           "coordinate (its record column moment_arms_m_flexion_positive.ankle "
                           "is plantar-POSITIVE: record arm = -(derived arm))",
        "current_cap_N_m": current_cap,
        "demand_peak_walk_N_m": demand,
        "muscle_class": members,
        "measured_curves": extrema,
        "common_grid_deg": {"lo": round(min(grid), 3), "hi": round(max(grid), 3),
                            "step_deg": GRID_STEP_DEG,
                            "note": "intersection of the class's measured scans - every "
                                    "muscle simultaneously measured here"},
        "force_table_N": {m: round(f, 6) for (m, _s), f in zip(force_spec,
                          [forces_ctx[s] for _m, s in force_spec])},
        "variants": {
            "V1_S1_oku_walk_peaks_deposit_arms": {
                "status": forces_ctx["v1_status"],
                "cap_N_m": round(cap, 6), "argmax_q_deg": argmax,
                "arm_signs_at_argmax": at_argmax,
                "delta_N_m": round(cap - current_cap, 6),
                "ratio_vs_current": round(cap / current_cap, 6),
                "coverage_ratio_vs_demand": round(cap / demand, 6),
                "envelope_samples_N_m": samples,
                "trace": trace_ctx,
            },
            "V1_S2_oku_peaks_si_matched_arms": {
                "status": "MEASURED forces x k-scaled arms (k = 0.11975394, the pulley "
                          "receipt's fitted per-taxon scalar - ABSOLUTE-SCALE CAVEAT)",
                "cap_N_m": round(s2, 6), "argmax_q_deg": argmax,
                "argmax_note": "same argmax as S1 - the scale is multiplicative on the arms",
                "delta_N_m": round(s2 - current_cap, 6),
                "ratio_vs_current": round(s2 / current_cap, 6),
                "coverage_ratio_vs_demand": round(s2 / demand, 6),
                "trace": {"k": {"source": "tools/science_funnel/validation/"
                                          "pulley_rederivation_20260920/receipt.json "
                                          "scale_diagnosis.fitted_mtp_class_scalar_k",
                                "sha256": trace_ctx["arms"]["k"]["sha256"], "value": K_GATE}},
            },
        },
        "walk_windows": wins,
    }


def derive():
    (receipt, pins, geo, oku, zeros, hold, contract, hind) = load_inputs()
    model = P.parse_model()
    si_rows = read_si2_ankle_rows(receipt)

    # ---- mine the model's ankle-crossing muscles (declared prior, re-verified here)
    ankle_crossing = []
    for mname, m in sorted(model["muscles"].items()):
        bodies = [p_["body"] for p_ in m["points"]]
        for i in range(len(bodies) - 1):
            if set((bodies[i], bodies[i + 1])) == {"shank_r", "foot_r"}:
                ankle_crossing.append(mname)
                break
    mining = {
        "ankle_crossing_muscles": ankle_crossing,
        "crossing_segment_note": "path spans (shank_r -> foot_r) - the ankle_r "
                                 "parent/child bodies from the pinned model",
        "wrap_references": {m: model["muscles"][m]["wraps"] and
                            [w["wrap_object"] for w in model["muscles"][m]["wraps"]] or []
                            for m in ankle_crossing},
        "inactive_wrap_state": {n: {"active": w["active"]}
                                for n, w in model["wraps"].items() if not w["active"]},
    }

    # ---- derive the 17 arm curves (measured here)
    arms = {}
    for m in ankle_crossing:
        si = si_rows[m]
        arms[m] = derive_ankle_muscle(model, m, si["jrange_deg"], n=N_SCAN)
    si2_comparison = compare_si2(si_rows, arms)

    # ---- measured diagnosis of every SI-shape miss (recorded, never tuned):
    # engagement extent + extrema location per mismatched row, so the miss is
    # attributable to a named branch of the curve, not absorbed into a tolerance
    miss_diagnosis = {"note": "every row the k-scaled tolerance misses, with its wrap "
                              "engagement extent and the branch structure. Mechanism "
                              "reading (hypothesis, clearly marked): the pulley machinery "
                              "is STATELESS per sample (the pulley lane's declared method, "
                              "matching SI on knee/MTP where wraps never disengaged at "
                              "2001/2001); on the ankle scan R_Ankle_Cylinder LIFTS OFF at "
                              "the dorsiflexed end for FDL II-IV/FHL/TP ('no segment "
                              "contact'), the straight tendon path there is the positive "
                              "(dorsiflexion-side) lobe the authors' rows do not carry, "
                              "while every WRAP-ENGAGED branch matches SI x k within "
                              "tolerance",
                      "rows": {}}
    for m, r in si2_comparison["rows"].items():
        misses = [e for e in ("min", "max") if not r["endpoints"][e]["within_tol_k"]]
        if not misses and r["sign_match"]:
            continue
        a = arms[m]
        eng = {w: v for w, v in a["wrap_engaged_of_scanned"].items()}
        miss_diagnosis["rows"][m] = {
            "misses": misses,
            "sign_match": r["sign_match"],
            "wrap_engaged_of_scanned": eng,
            "min_at_deg": a["r_fd_min_at_deg"], "max_at_deg": a["r_fd_max_at_deg"],
            "engaged_branch_residuals_mm": {
                e: r["endpoints"][e]["k_scaled_residual_mm"] for e in ("min", "max")},
        }

    # ---- forces from the pinned inputs
    oku_f = oku["oku_muscle_forces_N"]["before"]
    wl = geo["hindlimb"]["poses"]["walking"]["muscles"]
    pcsa_mg = wl["MG"]["pcsa_m2"]
    pcsa_lg = wl["LG"]["pcsa_m2"]
    gas_shares = {"MG": pcsa_mg / (pcsa_mg + pcsa_lg), "LG": pcsa_lg / (pcsa_mg + pcsa_lg)}
    forces_ctx = {
        "oku:SOL": oku_f["SOL"]["peak_N"],
        "oku:TA": oku_f["TA"]["peak_N"],
        "oku:EDL_quarter": oku_f["EDL"]["peak_N"] / 4.0,
        "gas_split:MG": oku_f["GAS"]["peak_N"] * gas_shares["MG"],
        "gas_split:LG": oku_f["GAS"]["peak_N"] * gas_shares["LG"],
        "fdl_quarter": oku_f["FDL"]["peak_N"] / 4.0,
        "record:SOL": wl["SOL"]["max_force_N"],
        "record:MG": wl["MG"]["max_force_N"],
        "record:LG": wl["LG"]["max_force_N"],
        "record:FDL_quarter": wl["FDL"]["max_force_N"] / 4.0,
        "record:FHL": wl["FHL"]["max_force_N"],
        "record:TP_ABSENT_named_gap": 0.0,
        "record:PB": wl["PB"]["max_force_N"],
        "record:PL": wl["PL"]["max_force_N"],
        "record:TA": wl["TA"]["max_force_N"],
        "record:EDL_quarter": wl["EDL"]["max_force_N"] / 4.0,
        "record:EHL": wl["EHL"]["max_force_N"],
        "v1_status": "MEASURED Oku walk forces x MEASURED(deposit-scale) arms; named gaps "
                     "(no Oku measurement): TP, PB, PL, FHL, EHL; GAS split by record PCSA "
                     "share MG %.6f / LG %.6f; FDL quarter-split across tendons II-V" % (
                         gas_shares["MG"], gas_shares["LG"]),
    }

    def arm_trace(key_path):
        return {"model": {"path": pins["model"]["path"], "sha256": pins["model"]["sha256"]},
                "si2": {"path": pins["si2"]["path"], "sha256": pins["si2"]["sha256"],
                        "key_path": "AnkleFE/macaque rows (first occurrences)"},
                "machinery": {"path": pins["pulley_machinery"]["path"],
                              "sha256": pins["pulley_machinery"]["sha256"]},
                "k": {"source": "tools/science_funnel/validation/pulley_rederivation_20260920/"
                                "receipt.json", "sha256": pins["pulley_receipt"]["sha256"]},
                "key_path": key_path}

    forces_trace = {"oku": {"path": pins["derived_numbers_snapshot"]["path"],
                            "sha256": pins["derived_numbers_snapshot"]["sha256"],
                            "key_path": "oku_muscle_forces_N.before.{SOL,GAS,FDL,TA,EDL}.peak_N"},
                    "record": {"path": pins["muscle_path_geometry_snapshot"]["path"],
                               "sha256": pins["muscle_path_geometry_snapshot"]["sha256"],
                               "key_path": "hindlimb.poses.walking.muscles.*."
                                           "{max_force_N,pcsa_m2}"}}

    # ---- scene walk window (both declared sense mappings), from the pinned snapshot
    ankle_check = next(c for c in zeros["premises"]["joint"]["checks"]
                       if c["name"] == "ankle_rad_range")
    lo_s, hi_s = ankle_check["measured"].split("..")
    scene_rad = (float(lo_s), float(hi_s))
    win_agree = (scene_rad[0] * 180.0 / math.pi, scene_rad[1] * 180.0 / math.pi)
    win_inverted = (-win_agree[1], -win_agree[0])
    walk_windows = {"scene_sense_AGREE": win_agree, "scene_sense_INVERTED": win_inverted}
    scene_window_trace = {"path": pins["derived_zeros_snapshot"]["path"],
                          "sha256": pins["derived_zeros_snapshot"]["sha256"],
                          "key_path": "premises.joint.checks[name=ankle_rad_range].measured",
                          "scene_rad": list(scene_rad)}

    # ---- current caps + demands from the pinned snapshots
    cap_of = {d["coordinate"].rsplit("_", 1)[0]: d["torque_cap_N_m"] for d in contract["contract"]["drives"]}
    current_cap = cap_of["ankle_dorsiflexion"]
    torques = oku["oku_before_alteration"]["torques"]["ankle"]
    demand_plantar = abs(torques["min_Nm"])
    demand_dorsal = abs(torques["max_Nm"])

    # V1 class and V2 class have different memberships/grids - built separately
    v1_members = [m for m, _s in V1_PLANTAR_FORCES]
    v2_members = [m for m, _s in V2_PLANTAR_FORCES]
    plantar_v1 = build_direction_book(
        "ankle_plantarflexion", -1, v1_members, V1_PLANTAR_FORCES, arms, si_rows,
        forces_ctx, current_cap, demand_plantar, walk_windows,
        {"arms": arm_trace("ankle_arms_book.arms.{R_SOL,R_MG,R_LG,R_FDL_TENDONII..V}"),
         "forces": forces_trace})
    plantar_v2 = build_direction_book(
        "ankle_plantarflexion", -1, v2_members, V2_PLANTAR_FORCES, arms, si_rows,
        forces_ctx, current_cap, demand_plantar, walk_windows,
        {"arms": arm_trace("ankle_arms_book.arms.{plantar class}"),
         "forces": forces_trace})
    dorsal_v1 = build_direction_book(
        "ankle_dorsiflexion", +1, [m for m, _s in V1_DORSAL_FORCES], V1_DORSAL_FORCES,
        arms, si_rows, forces_ctx, current_cap, demand_dorsal, walk_windows,
        {"arms": arm_trace("ankle_arms_book.arms.{R_TA,R_EDL_TENDONII..V}"),
         "forces": forces_trace})
    dorsal_v2 = build_direction_book(
        "ankle_dorsiflexion", +1, [m for m, _s in V2_DORSAL_FORCES], V2_DORSAL_FORCES,
        arms, si_rows, forces_ctx, current_cap, demand_dorsal, walk_windows,
        {"arms": arm_trace("ankle_arms_book.arms.{dorsal class}"),
         "forces": forces_trace})

    # ---- triceps-only sub-envelope + FDL partition bracket (declared laws)
    tri_members = ["R_SOL", "R_MG", "R_LG"]
    tri_dirs = [arms[m] for m in tri_members]
    tri_grid = common_grid([{"jrange_deg": d["jrange_deg"]} for d in tri_dirs])
    tri_forces = [(forces_ctx["oku:SOL"], "R_SOL"),
                  (forces_ctx["gas_split:MG"], "R_MG"),
                  (forces_ctx["gas_split:LG"], "R_LG")]
    _ts, cap_tri, arg_tri, _tu = signed_envelope(tri_dirs, tri_forces, tri_grid, -1)
    fdl_names = ["R_FDL_TENDONII", "R_FDL_TENDONIII", "R_FDL_TENDONIV", "R_FDL_TENDONV"]
    fdl_grid = common_grid([{"jrange_deg": arms[m]["jrange_deg"]} for m in fdl_names])
    plantar_arms_on_grid = [interp_arm(arms[m], q) for m in fdl_names for q in fdl_grid]
    fdl_plantar = [abs(a) for a in plantar_arms_on_grid if a < 0.0]
    fdl_bracket = {
        "all_force_on_min_plantar_arm_N_m": round(oku_f["FDL"]["peak_N"] * min(fdl_plantar), 6),
        "all_force_on_max_plantar_arm_N_m": round(oku_f["FDL"]["peak_N"] * max(fdl_plantar), 6),
        "note": "the equal-split cap sits between the single-slip bounds; the partition is "
                "unmeasured and the bracket is its honest width (the hind book's law)",
    }

    cap_book = {
        "cap_law": "cap_new(direction, variant) = max over the measured scan of "
                   "sum_m F_m x |r_m(q)|, sign-gated: a muscle contributes only where its "
                   "arm's sign matches the direction (plantar negative / dorsal positive); "
                   "201-sample stored curves interpolated linearly (the hind book's "
                   "convention consuming the pulley deliverable)",
        "scene_walk_window": scene_window_trace,
        "ankle_plantarflexion": {
            "V1_S1_oku_walk_peaks_deposit_arms": plantar_v1["variants"][
                "V1_S1_oku_walk_peaks_deposit_arms"],
            "V1_S2_oku_peaks_si_matched_arms": plantar_v1["variants"][
                "V1_S2_oku_peaks_si_matched_arms"],
            "V2_S1_pcsa_sigma_deposit_arms_PROVISIONAL": plantar_v2["variants"][
                "V1_S1_oku_walk_peaks_deposit_arms"],
            "V2_S2_pcsa_sigma_si_matched_arms_PROVISIONAL": plantar_v2["variants"][
                "V1_S2_oku_peaks_si_matched_arms"],
            "triceps_only_subenvelope_V1_S1": {
                "status": "the no-cross-joint-force-reuse reading: FDL excluded entirely "
                          "(its Oku force is also the hind book's MTP cap input)",
                "cap_N_m": round(cap_tri, 6), "argmax_q_deg": arg_tri,
                "coverage_ratio_vs_demand": round(cap_tri / demand_plantar, 6),
            },
            "fdl_partition_bracket_V1": fdl_bracket,
            "common_grid_deg_V1": plantar_v1["common_grid_deg"],
            "common_grid_deg_V2": plantar_v2["common_grid_deg"],
            "walk_windows_V1": plantar_v1["walk_windows"],
            "walk_windows_V2": plantar_v2["walk_windows"],
            "force_table_N_V1": plantar_v1["force_table_N"],
            "force_table_N_V2": plantar_v2["force_table_N"],
            "current_cap_N_m": current_cap,
            "current_cap_provenance": "1.25 x doc-rounded Oku ankle peak 5.92 (exact 5.9171) "
                                      "- DOC_DERIVED statics; the hind book's BLOCKED cell",
            "demand_peak_walk_N_m": demand_plantar,
            "muscle_class_V1": v1_members,
            "muscle_class_V2": v2_members,
            "named_gaps": {"V1": ["R_TP", "R_PB", "R_PL", "R_FHL", "R_EHL (dorsal-side muscle)"],
                           "V2": ["R_TP (no record row)"]},
        },
        "ankle_dorsiflexion": {
            "V1_S1_oku_walk_peaks_deposit_arms": dorsal_v1["variants"][
                "V1_S1_oku_walk_peaks_deposit_arms"],
            "V1_S2_oku_peaks_si_matched_arms": dorsal_v1["variants"][
                "V1_S2_oku_peaks_si_matched_arms"],
            "V2_S1_pcsa_sigma_deposit_arms_PROVISIONAL": dorsal_v2["variants"][
                "V1_S1_oku_walk_peaks_deposit_arms"],
            "V2_S2_pcsa_sigma_si_matched_arms_PROVISIONAL": dorsal_v2["variants"][
                "V1_S2_oku_peaks_si_matched_arms"],
            "common_grid_deg_V1": dorsal_v1["common_grid_deg"],
            "common_grid_deg_V2": dorsal_v2["common_grid_deg"],
            "walk_windows_V1": dorsal_v1["walk_windows"],
            "current_cap_N_m": current_cap,
            "demand_peak_walk_N_m": demand_dorsal,
            "muscle_class_V1": [m for m, _s in V1_DORSAL_FORCES],
            "muscle_class_V2": [m for m, _s in V2_DORSAL_FORCES],
            "named_gaps": {"V1": ["R_EHL"], "V2": []},
        },
    }

    # ---- consumption map: the deltas the hind book could not compute
    nodes = []
    cap_v1s1 = plantar_v1["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"]
    cap_v2s1 = plantar_v2["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"]
    cap_v1s2 = plantar_v1["variants"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"]
    cap_exact_current = 7.396
    over_before = 0
    over_after = 0
    for nd in hold["stance_nodes"]:
        tau = nd["tau_ankle_Nm"]
        r_old = abs(tau) / cap_exact_current
        r_new = abs(tau) / cap_v1s1
        if r_old > 1.0:
            over_before += 1
        if r_new > 1.0:
            over_after += 1
        nodes.append({"phi": nd["phi"], "tau_ankle_Nm": tau,
                      "ratio_old_vs_7_396": round(r_old, 4),
                      "ratio_new_vs_book": round(r_new, 4),
                      "over_cap_after": bool(r_new > 1.0)})
    binding = max(hold["stance_nodes"], key=lambda nd: abs(nd["tau_ankle_Nm"]))
    height_factor_v1 = cap_v1s1 / cap_exact_current
    height_factor_v2 = cap_v2s1 / cap_exact_current
    height_factor_v1s2 = cap_v1s2 / cap_exact_current
    hind_receipt = json.loads((REPO / pins["hind_receipt"]["path"]).read_text(encoding="utf-8"))
    ctx = hind_receipt["measured"]["deltas_measured"]["ankle_context"]
    consumption = {
        "schema_part": "chimera.ankle_arms_consumption_map.v1",
        "closes_the_book_cell": "hind_torque_book consumption_map.posture_height_authority."
                                "height_feed_forward: 'the ankle plantar chain ... has NO "
                                "measured-arm book (ankle BLOCKED): the height law's "
                                "feed-forward authority delta is 0 in this lane' - DELTA NOW "
                                "MEASURED below; and hind receipt ankle_context verdict "
                                "'fall 1.8-3.7x SHORT' re-priced by the measured arms",
        "record_before_measured_after": {
            "record_straight_line_envelopes_N_m": {
                "V1": ctx["record_arm_plantar_envelope_V1_N_m"],
                "V2": ctx["record_arm_plantar_envelope_V2_N_m"]},
            "record_shortfall_vs_demand_x": {
                "V1": round(demand_plantar / ctx["record_arm_plantar_envelope_V1_N_m"], 4),
                "V2": round(demand_plantar / ctx["record_arm_plantar_envelope_V2_N_m"], 4)},
            "measured_wrap_arm_caps_N_m": {"V1_S1": round(cap_v1s1, 6),
                                           "V2_S1_PROVISIONAL": round(cap_v2s1, 6)},
            "measured_coverage_ratio_vs_demand": {
                "V1_S1": round(cap_v1s1 / demand_plantar, 4),
                "V2_S1_PROVISIONAL": round(cap_v2s1 / demand_plantar, 4)},
            "source": {"path": pins["hind_receipt"]["path"], "sha256": pins["hind_receipt"]["sha256"],
                       "key_path": "measured.deltas_measured.ankle_context"},
        },
        "stance_hold_ankle_nodes": {
            "consumer": "the hind drive tier's ankle clamp: tau = clamp(..., +/-cap) "
                        "(gait_controller.hpp servo); demands from the wave-4 stance-hold "
                        "statics table (sha-pinned)",
            "cap_exact_current_N_m": cap_exact_current,
            "cap_new_V1_S1_N_m": round(cap_v1s1, 6),
            "nodes_total": len(nodes),
            "over_cap_nodes_before": over_before,
            "over_cap_nodes_after": over_after,
            "binding_node": {"phi": binding["phi"],
                             "demand_N_m": binding["tau_ankle_Nm"],
                             "ratio_before": round(abs(binding["tau_ankle_Nm"]) / cap_exact_current, 4),
                             "ratio_after": round(abs(binding["tau_ankle_Nm"]) / cap_v1s1, 4)},
            "nodes": nodes,
            "trace": {"path": pins["stance_hold_snapshot"]["path"],
                      "sha256": pins["stance_hold_snapshot"]["sha256"],
                      "key_path": "stance_nodes[].tau_ankle_Nm"},
        },
        "height_law_ankle_chain_delta": {
            "definition": "the authority factor cap_new / 7.396 - the cell the hind book put "
                          "at 'delta 0 (blocked)'; the ankle plantar chain is the stance "
                          "height holder, so its cap IS its feed-forward authority",
            "factor_V1_S1": round(height_factor_v1, 4),
            "factor_V2_S1_PROVISIONAL": round(height_factor_v2, 4),
            "factor_V1_S2_si_matched": round(height_factor_v1s2, 4),
            "binding_node_reprice_7_215_over_cap_new": round(abs(binding["tau_ankle_Nm"]) / cap_v1s1, 4),
            "delta_sign_V1_S1": "NEGATIVE (factor < 1): the measured book TIGHTENS the height "
                                "chain the doc cap was padding - the honest number",
            "delta_sign_V2_S1": "POSITIVE (factor > 1): PROVISIONAL capability reading",
            "caveat": "the 0.9-margin wall itself stays KNEE-bound (this lane changes no knee "
                      "number) - the wall's re-hearing remains the posture-cap lane's; what "
                      "measures here is the ankle chain's own authority factor and the "
                      "stance-hold ankle ratios",
            "S2_note": "at the k-gated scale the chain collapses (factor %.4f) - consistent "
                       "with the hind book's S2 collapse at knee/MP" % round(height_factor_v1s2, 4),
        },
        "no_engine_changes_made": True,
        "future_work": ["consume cap_new + the node table in the next gait wave (the tier "
                        "clamp's ankle entry re-prices with them)",
                        "the Guimaraes pairing lane's paired forces upgrade V2 from "
                        "PROVISIONAL; the TP record row closes the V2 plantar gap",
                        "the FDL slip partition narrows the plantar bracket",
                        "the operator-level k resolution (deposit vs SI absolute scale) "
                        "gates ALL engine consumption, as at knee/MP"],
    }

    # ---- falsifier verdicts (read the pre-registration exactly as written)
    verdicts = {}

    def sign_check(name, held_bool, measured):
        return {"name": name, "measured": measured, "verdict": "HELD" if held_bool else "FIRED"}

    pre = receipt["pre_registered_delta_signs"]["ankle_plantarflexion"]
    cap_v1 = plantar_v1["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"]
    cov_v1 = cap_v1 - demand_plantar

    def cap_band_check(name, cap_value, band):
        """The pre-registration pins the band on the CAP value itself (each
        band's derivation_of_band computes a cap), read exactly as written."""
        in_band = bool(band[0] <= cap_value <= band[1])
        return {"name": name, "cap_N_m": round(cap_value, 6), "band_on_cap": band,
                "in_band": in_band,
                "verdict": "HELD" if in_band else "FIRED"}

    verdicts["plantar_V1_S1_delta_sign"] = sign_check(
        "plantar V1_S1 delta sign (cap_new - 7.4 < 0)",
        (cap_v1 - current_cap) < 0, round(cap_v1 - current_cap, 6))
    verdicts["plantar_V1_S1_band_on_cap"] = cap_band_check(
        "plantar V1_S1 band on the CAP value", cap_v1, pre["V1_S1"]["band_N_m"])
    verdicts["plantar_V1_S1_coverage_sign"] = sign_check(
        "plantar V1_S1 covers the walk demand (cap - demand > 0)", cov_v1 > 0,
        round(cov_v1, 6))
    cap_tri_cov = cap_tri - demand_plantar
    verdicts["plantar_V1_S1_triceps_only_below_demand"] = sign_check(
        "triceps-only sub-envelope < demand", cap_tri_cov < 0, round(cap_tri_cov, 6))
    verdicts["plantar_V2_S1"] = {
        "name": "plantar V2_S1", "cap_N_m": round(cap_v2s1, 6),
        "delta_N_m": round(cap_v2s1 - current_cap, 6),
        "expected_sign": "POSITIVE",
        "sign_held": bool(cap_v2s1 - current_cap > 0),
        "band_on_cap": pre["V2_S1"]["band_N_m"],
        "in_band": bool(pre["V2_S1"]["band_N_m"][0] <= cap_v2s1 <= pre["V2_S1"]["band_N_m"][1]),
        "verdict": "HELD" if (cap_v2s1 > current_cap
                              and pre["V2_S1"]["band_N_m"][0] <= cap_v2s1
                              <= pre["V2_S1"]["band_N_m"][1]) else "FIRED"}
    cap_v2s2 = plantar_v2["variants"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"]
    verdicts["plantar_V1_S2"] = {
        "name": "plantar V1_S2", "cap_N_m": round(cap_v1s2, 6),
        "delta_N_m": round(cap_v1s2 - current_cap, 6),
        "expected_sign": "NEGATIVE",
        "sign_held": bool(cap_v1s2 - current_cap < 0),
        "band_on_cap": pre["V1_S2"]["band_N_m"],
        "in_band": bool(pre["V1_S2"]["band_N_m"][0] <= cap_v1s2 <= pre["V1_S2"]["band_N_m"][1]),
        "verdict": "HELD" if (cap_v1s2 < current_cap
                              and pre["V1_S2"]["band_N_m"][0] <= cap_v1s2
                              <= pre["V1_S2"]["band_N_m"][1]) else "FIRED"}
    verdicts["plantar_V2_S2"] = {
        "name": "plantar V2_S2", "cap_N_m": round(cap_v2s2, 6),
        "delta_N_m": round(cap_v2s2 - current_cap, 6),
        "expected_sign": "NEGATIVE",
        "sign_held": bool(cap_v2s2 - current_cap < 0),
        "band_on_cap": pre["V2_S2"]["band_N_m"],
        "in_band": bool(pre["V2_S2"]["band_N_m"][0] <= cap_v2s2 <= pre["V2_S2"]["band_N_m"][1]),
        "verdict": "HELD" if (cap_v2s2 < current_cap
                              and pre["V2_S2"]["band_N_m"][0] <= cap_v2s2
                              <= pre["V2_S2"]["band_N_m"][1]) else "FIRED"}
    verdicts["plantar_V2_gt_V1"] = sign_check("plantar V2_S1 > V1_S1", cap_v2s1 > cap_v1,
                                              {"V2_S1": round(cap_v2s1, 6),
                                               "V1_S1": round(cap_v1, 6)})

    pred = receipt["pre_registered_delta_signs"]["ankle_dorsiflexion"]
    cap_d_v1 = dorsal_v1["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"]
    cap_d_v2 = dorsal_v2["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"]
    cap_d_v1s2 = dorsal_v1["variants"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"]
    cap_d_v2s2 = dorsal_v2["variants"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"]
    verdicts["dorsal_V1_S1"] = {
        "name": "dorsal V1_S1", "cap_N_m": round(cap_d_v1, 6),
        "delta_N_m": round(cap_d_v1 - current_cap, 6),
        "expected_sign": "NEGATIVE",
        "sign_held": bool(cap_d_v1 - current_cap < 0),
        "band_on_cap": pred["V1_S1"]["band_N_m"],
        "in_band": bool(pred["V1_S1"]["band_N_m"][0] <= cap_d_v1 <= pred["V1_S1"]["band_N_m"][1]),
        "verdict": "HELD" if (cap_d_v1 < current_cap
                              and pred["V1_S1"]["band_N_m"][0] <= cap_d_v1
                              <= pred["V1_S1"]["band_N_m"][1]) else "FIRED"}
    verdicts["dorsal_V2_S1"] = {
        "name": "dorsal V2_S1", "cap_N_m": round(cap_d_v2, 6),
        "delta_N_m": round(cap_d_v2 - current_cap, 6),
        "expected_sign": "NEGATIVE",
        "sign_held": bool(cap_d_v2 - current_cap < 0),
        "band_on_cap": pred["V2_S1"]["band_N_m"],
        "in_band": bool(pred["V2_S1"]["band_N_m"][0] <= cap_d_v2 <= pred["V2_S1"]["band_N_m"][1]),
        "verdict": "HELD" if (cap_d_v2 < current_cap
                              and pred["V2_S1"]["band_N_m"][0] <= cap_d_v2
                              <= pred["V2_S1"]["band_N_m"][1]) else "FIRED"}
    verdicts["dorsal_V2_gt_V1"] = sign_check("dorsal V2_S1 > V1_S1", cap_d_v2 > cap_d_v1,
                                             {"V2_S1": round(cap_d_v2, 6),
                                              "V1_S1": round(cap_d_v1, 6)})

    shape = receipt["falsifiers_pre_registered"]["si_shape_per_muscle"]
    uv = si2_comparison["unit_verdict"]
    verdicts["si_shape_unit_verdict"] = sign_check(
        "unit verdict exactly-one-of {mm, cm}",
        uv["outcome"] in ("mm", "cm"), uv["outcome"])
    verdicts["si_shape_k_gate"] = sign_check(
        "k_ankle (point-only class) inside the MTP-class spread %s" % (list(K_MTP_SPREAD),),
        si2_comparison["k_gate"]["k_ankle_inside_mtp_spread"],
        si2_comparison["k_gate"]["k_ankle_point_class_fitted"])
    wrapped_in_tol = all(r["endpoints"][e]["within_tol_k"]
                         for m, r in si2_comparison["rows"].items()
                         if r["wrap_class"] != "point_only" for e in ("min", "max"))
    verdicts["si_shape_wrapped_rows_within_k_tolerance"] = sign_check(
        "wrapped rows within max(0.25 mm, 25%|SI|) under SI = derived x k_mtp",
        wrapped_in_tol,
        {m: [r["endpoints"]["min"]["k_scaled_residual_mm"],
             r["endpoints"]["max"]["k_scaled_residual_mm"]]
         for m, r in si2_comparison["rows"].items() if r["wrap_class"] != "point_only"})
    verdicts["si_shape_sign_pattern"] = sign_check(
        "per-muscle sign pattern matches SI 2", si2_comparison["sign_pattern_all_match"],
        {m: r["sign_match"] for m, r in si2_comparison["rows"].items()
         if not r["sign_match"]} or "all 17 match")
    verdicts["si_shape_triceps_ordering"] = sign_check(
        "|MG| > |LG| > |SOL| at both endpoints",
        si2_comparison["triceps_ordering"]["min_endpoint_held"]
        and si2_comparison["triceps_ordering"]["max_endpoint_held"],
        si2_comparison["triceps_ordering"])

    engage = {m: arms[m]["wrap_engaged_of_scanned"].get("R_Ankle_Cylinder", [0, 0])
              for m in MUST_ENGAGE}
    verdicts["wrap_activity_ankle_cylinder"] = sign_check(
        "R_Ankle_Cylinder engaged on >= 1 sample for FDL II/III/IV, FHL, TP",
        all(v[0] >= 1 for v in engage.values()), engage)
    verdicts["wrap_activity_fdl_v_ellipsoid_and_lg_inactive_state"] = {
        "R_FDL_TENDONV": arms["R_FDL_TENDONV"]["wrap_engaged_of_scanned"],
        "R_LG": arms["R_LG"]["wrap_engaged_of_scanned"],
        "note": "recorded with true extent; LG's rProxTibiaCylinder is active=false in the "
                "deposit (honored deposit state - the advance-named suspect if LG's SI row "
                "alone misses)",
        "verdict": "RECORDED"}

    cons_pre = receipt["pre_registered_delta_signs"]["consumption_deltas"]
    verdicts["consumption_stance_over_cap_count"] = sign_check(
        "stance-hold over-cap ankle count RISES", over_after > over_before,
        {"before": over_before, "after": over_after,
         "pre_registered_prose": cons_pre["stance_hold_over_cap_nodes"]
         .get("derivation_of_band", "")})
    hf = cons_pre["height_law_ankle_chain_authority_factor"]
    hf_band = [0.73, 0.94]
    verdicts["consumption_height_factor_V1_S1"] = {
        "name": "height-law ankle chain authority factor cap_new/7.396",
        "factor": round(height_factor_v1, 4), "expected": hf["expected_sign"],
        "band": hf_band,
        "sign_held": bool(height_factor_v1 < 1.0),
        "in_band": bool(hf_band[0] <= height_factor_v1 <= hf_band[1]),
        "verdict": "HELD" if (height_factor_v1 < 1.0
                              and hf_band[0] <= height_factor_v1 <= hf_band[1]) else "FIRED"}
    verdicts["consumption_height_factor_V2_S1_sign"] = sign_check(
        "height factor V2_S1 > 1 (PROVISIONAL)", height_factor_v2 > 1.0,
        round(height_factor_v2, 4))

    fired = [k for k, v in verdicts.items()
             if isinstance(v, dict) and v.get("verdict") == "FIRED"]
    verdicts["summary"] = {"fired": fired, "all_held": not fired,
                           "note": "any FIRED entry is recorded with its number and left "
                                   "standing - the book is not tuned to re-enter its bands"}

    book = {
        "schema": "chimera.ankle_arms_book.v1",
        "lane": "ankle-arms-20260921",
        "derived_from_commit": "b17cbf6c (agent/hind-torque-book-20260921)",
        "inputs_sha_verified": {k: p["sha256"] for k, p in pins.items()},
        "model_mining": mining,
        "method": {
            "fd_step_rad": FD_STEP, "scan_samples": N_SCAN,
            "grid_step_deg": GRID_STEP_DEG,
            "machinery": "imported unmodified from the sha-pinned pulley module "
                         "(derive_pulley_arms.py): parse_model, forward_kinematics, "
                         "resolve_path (cylinder tangent + quadrant + <=pi arc, ellipsoid "
                         "iterative refinement), pin_joint_world_axis, geometric_arm",
            "scan_protocol": "r_ankle_flexion over each muscle's SI 2 recorded jrange "
                             "(2001 samples, recorded order preserved), all other "
                             "coordinates at model-file defaults; the FDL/FHL/TP ankle "
                             "wraps - rigid during the pulley lane's MTP scan - go live here",
            "arm_definition": "r = -dL/dq, central differences, step 1e-4 rad (authoritative); "
                              "advisory geometric arm reported alongside",
            "advisory_fd_max_abs_diff_mm_by_muscle": {
                m: round(arms[m]["fd_geo_max_abs_diff_mm"], 6) for m in ankle_crossing},
        },
        "arms": arms,
        "si2_comparison": si2_comparison,
        "si2_miss_diagnosis": miss_diagnosis,
        "cap_book": cap_book,
        "consumption_map": consumption,
        "falsifier_verdicts": {"pre_registered": verdicts},
        "determinism": {
            "protocol": "pure function of the sha-verified inputs; the unittest derives "
                        "twice (in-process and subprocess) and compares the deliverable sha256",
            "deliverable_sha256_note": "rerun and compare - identical bytes are the "
                                       "pre-registered determinism check",
        },
    }
    return book


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT_JSON)
    a = ap.parse_args()
    out = a.out.resolve()
    here = HERE.resolve()
    if here not in out.parents and out.parent != here:
        raise SystemExit(f"REFUSAL: --out must live inside {here} "
                         "(no source changes outside the validation dir)")
    book = derive()
    out.write_bytes(canonical_json_bytes(book))
    pv1 = book["cap_book"]["ankle_plantarflexion"]["V1_S1_oku_walk_peaks_deposit_arms"]
    pv2 = book["cap_book"]["ankle_plantarflexion"]["V2_S1_pcsa_sigma_deposit_arms_PROVISIONAL"]
    print(json.dumps({
        "deliverable": str(out),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "plantar_cap_V1_S1_N_m": pv1["cap_N_m"],
        "plantar_cap_V2_S1_PROVISIONAL_N_m": pv2["cap_N_m"],
        "dorsal_cap_V1_S1_N_m": book["cap_book"]["ankle_dorsiflexion"][
            "V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"],
        "k_ankle_point_class": book["si2_comparison"]["k_gate"]["k_ankle_point_class_fitted"],
        "unit_verdict": book["si2_comparison"]["unit_verdict"]["outcome"],
        "stance_over_cap_nodes": [book["consumption_map"]["stance_hold_ankle_nodes"]["over_cap_nodes_before"],
                                  book["consumption_map"]["stance_hold_ankle_nodes"]["over_cap_nodes_after"]],
        "fired": book["falsifier_verdicts"]["pre_registered"]["summary"]["fired"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
