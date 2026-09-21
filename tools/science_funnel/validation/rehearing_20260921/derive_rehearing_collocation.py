"""The re-hearing: wave-10 collocation re-run at the measured (d) caps.

Lane: tools/science_funnel/validation/rehearing_20260921/
Rule 0: receipt.json pre-registered BEFORE this script existed (PR1-PR8).

Copied+modified from gait_zero_20260919/derive_reachable_vault.py (wave 10,
the same proven pattern as the posture-cap lane's derive_posture_cap_sweep.py):
the vendored generator is executed UNMODIFIED as the instrument (falsifier
PR1), and this driver re-implements ONLY the leg-cap normalization - knee/MP
at the hind book's MEASURED V1_S1 caps, the ankle SIGN-GATED at the ankle
book's measured caps (cap_law: plantar negative / dorsal positive), hip and
posture HELD at the instrument's own constants.  Formulation otherwise
UNCHANGED: 21 periodic theta/theta-dot nodes, T=0.71 s, finite-difference
theta_ddot, mean-of-node-maxima objective, hard 0.9 posture constraint,
trapezoidal kinematics, SLSQP(maxiter=500, ftol=1e-10), bounds +-0.6 rad /
+-8 rad/s.  Starts: the banked optimum (warm) and the vendored fresh starts.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize, minimize_scalar

LANE = Path(__file__).resolve().parent
REPO = LANE.parents[3]
GZ = LANE / "inputs" / "run_env" / "tools" / "science_funnel" / "validation" / "gait_zero_20260919"
sys.path.insert(0, str(GZ))
import derive_reachable_vault as rv  # noqa: E402  (the vendored instrument module)
import derive_trunk_pitch as st  # noqa: E402

BANKED = LANE / "inputs" / "vendored_gait_zero" / "trunk_vault_reachable.wave10.json"
ANKLE_BOOK = LANE / "inputs" / "ankle_arms_book.json"
STATICS_COMMITTED = LANE / "inputs" / "statics_lane_committed_deliverable.json"
ANKLE_COMMITTED = LANE / "inputs" / "ankle_lane_committed_deliverable.json"
HIND_BOOK = REPO / "tools" / "science_funnel" / "validation" / "hind_torque_book_20260921" / "hind_torque_book.json"
RECEIPT = LANE / "receipt.json"
OUT = LANE / "rehearing_20260921.json"

PINS = {
    "wave10_generator": (GZ / "derive_reachable_vault.py",
                         "0c722cffae81268c2a4933ed3f482e7af6c942afe66e35f9d6380893d1acf2a5"),
    "wave10_statics_module": (GZ / "derive_trunk_pitch.py",
                              "5be624d304f029d6de92559650a438bca531c30b6eaf111c1459d0e9374fac16"),
    "wave10_deliverable": (BANKED,
                           "e922153318778e4cd8c1891f59454261c6d5be0a77aebdc5f78d2758ccd2faa7"),
    "derived_numbers": (LANE / "inputs" / "run_env" / "tools" / "science_funnel" / "validation"
                        / "gait_controller_20260918" / "derived_numbers.json",
                        "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173"),
    "ankle_arms_book": (ANKLE_BOOK,
                        "7ce03069c1e033b52db0fb315d218eb2223e79a67a9018123da206d68adcb6f6"),
    "hind_torque_book": (HIND_BOOK,
                         "9fc5c0ba09f6ec183d5348bb21cc5dc18b5987240406ccdcdbb34e514e26f01c"),
    "statics_lane_committed_deliverable": (STATICS_COMMITTED,
                                           "21d3dbbe2a477d67f7d7d5572f0171cd0c2e8cfe34a6cd1770ccd81abf06908a"),
    "ankle_lane_committed_deliverable": (ANKLE_COMMITTED,
                                         "31c6e3fb717c310086e0bf023b8b45f6cf2335692e15e9794eaa325f402184ea"),
    "receipt": (RECEIPT, None),  # content recorded, sha reported (receipt pins itself before the script exists)
}

N = rv.N
T = rv.T
DT = rv.DT
LIMIT = rv.LIMIT          # 0.9 * 11.2125 - the instrument's own posture constraint, HELD
CAP_POST = rv.CAP_POST    # 11.2125 - the instrument's own posture cap, HELD
HIP_CAP = st.CAP["hip"]   # held (the instrument's internal doc cap; the posture drive borrows it)


def verify_pins() -> dict:
    got = {}
    for name, (path, want) in PINS.items():
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if want is not None and sha != want:
            raise SystemExit(f"PIN MISMATCH {name}: {sha} != {want} - refusing to run")
        got[name] = {"path": str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path),
                     "sha256": sha,
                     "expected": want}
    return got


def cap_book_values() -> dict:
    """Measured caps, every one read from its sha-pinned book (no literals)."""
    ankle = json.loads(ANKLE_BOOK.read_text(encoding="utf-8"))["cap_book"]
    hind = json.loads(HIND_BOOK.read_text(encoding="utf-8"))["rederivation"]
    return {
        "D": {"knee": hind["knee_extension"]["variants"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"],
              "mp": hind["mtp_flexion"]["variants"]["V1_S1_oku_walk_peaks_deposit_arms_equal_split"]["cap_N_m"],
              "ankle_p": ankle["ankle_plantarflexion"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"],
              "ankle_d": ankle["ankle_dorsiflexion"]["V1_S1_oku_walk_peaks_deposit_arms"]["cap_N_m"]},
        "S2": {"knee": hind["knee_extension"]["variants"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"],
               "mp": hind["mtp_flexion"]["variants"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"],
               "ankle_p": ankle["ankle_plantarflexion"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"],
               "ankle_d": ankle["ankle_dorsiflexion"]["V1_S2_oku_peaks_si_matched_arms"]["cap_N_m"]},
    }


def make_metrics(leg_caps, sign_gated: bool):
    """The vendored metrics with ONLY the leg-cap normalization changed.

    sign_gated=False reproduces the vendored law exactly (abs/CAP lookup) and
    is used for the wrapper-drift check at doc caps; sign_gated=True is the
    ankle book's cap_law: plantar (tau<0) at ankle_p, dorsal (tau>=0) at ankle_d.
    """
    def metrics(x):
        theta, vel = rv.unpack(x)
        acc = rv.periodic_accel(vel)
        rows = []
        for i in range(N):
            tau = rv.row(theta[i], i)
            static = float(tau[2])
            gravity = rv.M_HAT * rv.G * rv.R_HAT * math.sin(float(theta[i]))
            inertial = rv.I_HAT * float(acc[i])
            required = static + gravity + inertial
            if sign_gated:
                a = float(tau[5])
                ankle_ratio = (abs(a) / leg_caps["ankle_p"] if a < 0.0
                               else abs(a) / leg_caps["ankle_d"])
                leg_ratios = [abs(float(tau[3])) / HIP_CAP,
                              abs(float(tau[4])) / leg_caps["knee"],
                              ankle_ratio,
                              abs(float(tau[6])) / leg_caps["mp"]]
            else:
                leg_ratios = [abs(float(tau[3])) / st.CAP["hip"],
                              abs(float(tau[4])) / st.CAP["knee"],
                              abs(float(tau[5])) / st.CAP["ankle"],
                              abs(float(tau[6])) / st.CAP["mp"]]
            rows.append({"phi": i / 20.0, "theta_rad": float(theta[i]),
                         "theta_dot_rad_s": float(vel[i]),
                         "theta_ddot_rad_s2": float(acc[i]),
                         "static_posture_Nm": static,
                         "gravity_Nm": gravity,
                         "inertial_Nm": inertial,
                         "required_posture_Nm": required,
                         "posture_ratio": abs(required) / CAP_POST,
                         "stance_ratio": max(leg_ratios),
                         "leg_ratios": leg_ratios})
        return rows
    return metrics


def solve(leg_caps, sign_gated, x0_list, tag):
    """One SLSQP solve per start - the vendored objective/constraints verbatim."""
    metrics = make_metrics(leg_caps, sign_gated)

    def objective(x):
        rs = metrics(x)
        ratios = np.array([max(r["stance_ratio"], r["posture_ratio"]) for r in rs])
        return float(np.mean(ratios) + 1e-4 * np.mean(rv.unpack(x)[1] ** 2)
                     + 1e-5 * np.mean(np.diff(np.r_[rv.unpack(x)[0], rv.unpack(x)[0][0]]) ** 2))

    def constraints(x):
        rs = metrics(x)
        return np.array([LIMIT - abs(r["required_posture_Nm"]) for r in rs])

    def kinematic_constraints(x):
        theta, vel = rv.unpack(x)
        return np.roll(theta, -1) - theta - 0.5 * DT * (np.roll(vel, -1) + vel)

    bounds = [(-0.6, 0.6)] * N + [(-8.0, 8.0)] * N
    runs = []
    for name, x0 in x0_list:
        result = minimize(objective, np.asarray(x0, dtype=float), method="SLSQP", bounds=bounds,
                          constraints=[{"type": "ineq", "fun": constraints},
                                       {"type": "eq", "fun": kinematic_constraints}],
                          options={"maxiter": 500, "ftol": 1e-10, "disp": False})
        rs = metrics(result.x)
        max_required = max(abs(r["required_posture_Nm"]) for r in rs)
        wall = max(max(r["stance_ratio"], r["posture_ratio"]) for r in rs)
        worst = max(rs, key=lambda r: max(r["stance_ratio"], r["posture_ratio"]))
        joints = ["hip", "knee", "ankle", "mp", "posture"]
        terms_at_worst = dict(zip(joints, worst["leg_ratios"] + [worst["posture_ratio"]]))
        binder = max(terms_at_worst, key=lambda j: terms_at_worst[j])
        runs.append({
            "start": name, "success": bool(result.success), "message": str(result.message),
            "objective": round(float(result.fun), 9),
            "wall_max_combined": round(float(wall), 9),
            "wall_node_phi": worst["phi"],
            "wall_binder": binder,
            "wall_terms": {j: round(v, 9) for j, v in terms_at_worst.items()},
            "max_required_posture_Nm": round(float(max_required), 9),
            "posture_constraint_limit_Nm": LIMIT,
            "posture_constraint_holds": bool(max_required <= LIMIT + 1e-7),
            "theta_rad": [round(float(t), 9) for t in rv.unpack(result.x)[0]],
            "theta_dot_rad_s": [round(float(v), 9) for v in rv.unpack(result.x)[1]],
        })
    return {"tag": tag, "runs": runs}


def maximin_bound(leg_caps, sign_gated):
    """max over nodes of (min over theta of the node's stance_ratio).

    A lower bound on the achievable wall within the formulation: the wall at a
    node >= that node's stance_ratio >= the node's theta-minimum, and the leg
    torque at a node depends only on that node's own theta (receipt's
    formulation_law).  Grid 0.005 rad then bounded scalar refinement.
    """
    metrics = make_metrics(leg_caps, sign_gated)

    def stance_at(i, th):
        x = np.zeros(2 * N)
        x[i] = th
        return metrics(x)[i]["stance_ratio"]

    nodes = []
    lb = 0.0
    for i in range(N):
        grid = [round(-0.6 + 0.005 * k, 6) for k in range(241)]
        vals = [stance_at(i, th) for th in grid]
        k = int(np.argmin(vals))
        res = minimize_scalar(lambda th: stance_at(i, th),
                              bounds=(max(-0.6, grid[k] - 0.006), min(0.6, grid[k] + 0.006)),
                              method="bounded", options={"xatol": 1e-6})
        best_th = float(res.x) if res.fun < vals[k] else grid[k]
        best_v = float(min(res.fun, vals[k]))
        x = np.zeros(2 * N)
        x[i] = best_th
        row = metrics(x)[i]
        joints = ["hip", "knee", "ankle", "mp"]
        terms = dict(zip(joints, row["leg_ratios"]))
        binder = max(terms, key=lambda j: terms[j])
        nodes.append({"phi": i / 20.0, "lb_stance_ratio": round(best_v, 9),
                      "argmin_theta_rad": round(best_th, 9), "binder": binder,
                      "terms": {j: round(v, 9) for j, v in terms.items()},
                      "sign_class": "plantar" if rv.row(best_th, i)[5] < 0 else "dorsal"})
        lb = max(lb, best_v)
    worst = max(nodes, key=lambda n: n["lb_stance_ratio"])
    over = [n["phi"] for n in nodes if n["lb_stance_ratio"] > 1.0]
    return {"maximin_lower_bound": round(lb, 9), "binding_node_phi": worst["phi"],
            "over_unity_lb_phis": over, "nodes": nodes}


def run_instrument() -> dict:
    """The vendored generator, unmodified, as a subprocess (PR1)."""
    out_path = GZ / "trunk_vault_reachable.json"
    if out_path.exists():
        out_path.unlink()
    proc = subprocess.run([sys.executable, "-B", str(GZ / "derive_reachable_vault.py")],
                          capture_output=True, text=True, timeout=7200)
    if proc.returncode != 0:
        raise SystemExit(f"instrument run failed: {proc.stderr[-2000:]}")
    data = out_path.read_bytes()
    r = json.loads(data)
    banked = json.loads(BANKED.read_text(encoding="utf-8"))
    checks = {
        "max_ratio_to_cap": {"banked": banked["max_ratio_to_cap"], "run": r["max_ratio_to_cap"],
                             "band": [1.3227, 1.3229],
                             "in_band": bool(1.3227 <= r["max_ratio_to_cap"] <= 1.3229)},
        "max_posture_ratio_to_cap": {"banked": banked["max_posture_ratio_to_cap"], "run": r["max_posture_ratio_to_cap"],
                                     "band": [0.89999, 0.90001],
                                     "in_band": bool(0.89999 <= r["max_posture_ratio_to_cap"] <= 0.90001)},
        "objective": {"banked": banked["objective"], "run": r["objective"],
                      "band": [0.8941, 0.8943],
                      "in_band": bool(0.8941 <= r["objective"] <= 0.8943)},
        "success": {"banked": banked["success"], "run": r["success"], "equal": bool(r["success"] == banked["success"])},
        "feasible": {"banked": banked["feasible"], "run": r["feasible"], "equal": bool(r["feasible"] == banked["feasible"])},
        "verdict_class": {"banked": banked["verdict"].split(":")[0], "run": r["verdict"].split(":")[0],
                          "equal": bool(r["verdict"].split(":")[0] == banked["verdict"].split(":")[0])},
        "bytes_equal_to_banked": bool(data == BANKED.read_bytes()),
    }
    checks["held"] = all([checks["max_ratio_to_cap"]["in_band"], checks["max_posture_ratio_to_cap"]["in_band"],
                          checks["objective"]["in_band"], checks["success"]["equal"],
                          checks["feasible"]["equal"], checks["verdict_class"]["equal"]])
    return {"method": "vendored derive_reachable_vault.py run UNMODIFIED (subprocess, python -B)",
            "written_sha256": hashlib.sha256(data).hexdigest(),
            "checks": checks}


def wrapper_drift_check(banked) -> dict:
    """The lane wrapper at doc caps must equal the vendored metrics EXACTLY."""
    x = np.array([n["theta_rad"] for n in banked["nodes"]]
                 + [n["theta_dot_rad_s"] for n in banked["nodes"]])
    mine = make_metrics({}, False)(x)
    theirs = rv.metrics(x)
    fields = ("phi", "theta_rad", "theta_dot_rad_s", "theta_ddot_rad_s2", "static_posture_Nm",
              "gravity_Nm", "inertial_Nm", "required_posture_Nm", "posture_ratio",
              "stance_ratio", "leg_ratios")
    mismatches = []
    for a, b, i in zip(mine, theirs, range(N)):
        for f in fields:
            if a[f] != b[f]:
                mismatches.append((i, f))
    return {"fields": list(fields), "node_mismatches": mismatches[:10],
            "n_mismatches": len(mismatches), "exact": len(mismatches) == 0}


def reprice_d_wall(banked, caps) -> dict:
    """The statics lanes' live-pin re-price law on the banked wave-10 table.

    capA = the LIVE DOC pins (7.4 / 6.6375 / 11.2125 / 0.8875 / posture 11.2125),
    the statics chain's convention; the ankle term priced at the PLANTAR factor
    under the receipt's named law.  Field-for-field vs the ankle lane's
    committed D wall block (rounded exactly as committed: 6 decimals).
    """
    cap_a = {"hip": 11.2125, "knee": 6.6375, "ankle": 7.4, "mp": 0.8875}
    h = {"hip": cap_a["hip"] / cap_a["hip"], "knee": cap_a["knee"] / caps["knee"],
         "ankle": cap_a["ankle"] / caps["ankle_p"], "mp": cap_a["mp"] / caps["mp"],
         "posture": 1.0}
    nodes = []
    hist = {}
    for n in banked["nodes"]:
        terms = {"hip": n["leg_ratios"][0] * h["hip"], "knee": n["leg_ratios"][1] * h["knee"],
                 "ankle": n["leg_ratios"][2] * h["ankle"], "mp": n["leg_ratios"][3] * h["mp"],
                 "posture": n["posture_ratio"]}
        binder = max(terms, key=lambda j: terms[j])
        hist[binder] = hist.get(binder, 0) + 1
        nodes.append({"phi": n["phi"], "terms": {j: round(v, 6) for j, v in terms.items()},
                      "combined": round(max(terms.values()), 6), "binder": binder})
    mx = max(nodes, key=lambda n: n["combined"])
    wall = {"headroom_factors": {j: round(v, 8) for j, v in h.items()},
            "nodes": nodes,
            "max_combined_ratio": mx["combined"],
            "max_binder": {"joint": mx["binder"], "phi": mx["phi"]},
            "crosses_1_0": bool(mx["combined"] <= 1.0),
            "margin_0_9_reachable": bool(mx["combined"] <= 0.9),
            "knee_term_at_phi_0_75": next(n["terms"]["knee"] for n in nodes if n["phi"] == 0.75),
            "ankle_term_at_phi_0_5": next(n["terms"]["ankle"] for n in nodes if n["phi"] == 0.5),
            "binder_histogram": hist}
    committed = json.loads(ANKLE_COMMITTED.read_text(encoding="utf-8"))
    ref = committed["margin_wall"]["D_measured_ankle_unblocked"]
    diffs = []
    for k in ("max_combined_ratio", "ankle_term_at_phi_0_5", "knee_term_at_phi_0_75",
              "crosses_1_0", "margin_0_9_reachable", "binder_histogram"):
        if wall[k] != ref[k]:
            diffs.append(k)
    if wall["max_binder"] != ref["max_binder"]:
        diffs.append("max_binder")
    for a, b in zip(wall["nodes"], ref["nodes"]):
        if a["phi"] != b["phi"] or a["terms"] != b["terms"] or a["combined"] != b["combined"] or a["binder"] != b["binder"]:
            diffs.append(f"node@{b['phi']}")
    return {"wall": wall,
            "committed_ref_sha256": PINS["ankle_lane_committed_deliverable"][1],
            "chain_note": ("the (d) wall block is committed in the ANKLE lane's deliverable "
                           "(31c6e3fb..., in-tree at this base); the receipt's "
                           "inputs_pinned.statics_lane_deliverable attribution to 21d3dbbe named the "
                           "STATICS lane's deliverable, which carries A/B/C/S2 only - recorded in the "
                           "measured block as a lane-side attribution note, the priors unedited"),
            "field_diffs": diffs, "field_for_field_equal": len(diffs) == 0}


def shift_metrics(banked, best_run, caps) -> dict:
    """Where the load moved: best (d) run vs the banked optimum (both priced at (d))."""
    m = make_metrics(caps, True)
    bx = np.array([n["theta_rad"] for n in banked["nodes"]]
                  + [n["theta_dot_rad_s"] for n in banked["nodes"]])
    b_rows = m(bx)
    rx = np.array(best_run["theta_rad"] + best_run["theta_dot_rad_s"])
    r_rows = m(rx)
    per_node = []
    for b, r in zip(b_rows, r_rows):
        per_node.append({"phi": b["phi"],
                         "theta_banked_rad": round(b["theta_rad"], 9), "theta_run_rad": round(r["theta_rad"], 9),
                         "theta_delta_rad": round(r["theta_rad"] - b["theta_rad"], 9),
                         "ankle_demand_banked_Nm": round(abs(rv.row(b["theta_rad"], int(b["phi"] * 20))[5]), 6),
                         "ankle_demand_run_Nm": round(abs(rv.row(r["theta_rad"], int(b["phi"] * 20))[5]), 6),
                         "knee_ratio_banked": round(b["leg_ratios"][1], 6), "knee_ratio_run": round(r["leg_ratios"][1], 6),
                         "hip_ratio_banked": round(b["leg_ratios"][0], 6), "hip_ratio_run": round(r["leg_ratios"][0], 6)})
    return {"per_node": per_node,
            "note": "demand ratios priced at the (d) caps for both trajectories; raw N.m from the vendored statics"}


def derive_once(pins, caps, banked) -> dict:
    env = {"python": sys.version.split()[0],
           "numpy": np.__version__,
           "scipy": __import__("scipy").__version__,
           "platform": sys.platform}

    instrument = run_instrument()
    drift = wrapper_drift_check(banked)
    reprice = reprice_d_wall(banked, caps["D"])
    # chain direction: receipt -> deliverable. The receipt's CONTENT sha must
    # not enter the deliverable (the measured block is appended after the
    # derive); the receipt is recorded by path only.
    inputs_recorded = {k: ({"path": v["path"]} if k == "receipt" else v) for k, v in pins.items()}

    bound_d = maximin_bound(caps["D"], True)
    bound_s2 = maximin_bound(caps["S2"], True)

    old = np.array([-0.254, -0.0835, 0.087, 0.2575, 0.3292, 0.2182, 0.1201,
                    0.0588, -0.0441, -0.1568, -0.254, -0.0835, 0.087,
                    0.2575, 0.3292, 0.2182, 0.1201, 0.0588, -0.0441, -0.1568, -0.254])
    warm = np.array([n["theta_rad"] for n in banked["nodes"]]
                    + [n["theta_dot_rad_s"] for n in banked["nodes"]])
    starts = [("warm_banked_optimum", warm), ("fresh_zero", np.zeros(2 * N)),
              ("fresh_wave8", np.r_[old, np.gradient(old, DT)])]

    colloc = {"D": solve(caps["D"], True, starts, "D_measured"),
              "S2": solve(caps["S2"], True, starts, "S2_si_matched_gate")}

    d_walls = {r["start"]: r for r in colloc["D"]["runs"]}
    best = min(d_walls.values(), key=lambda r: r["wall_max_combined"])
    achievable = best["wall_max_combined"]
    bound_ok = all(r["wall_max_combined"] >= bound_d["maximin_lower_bound"] - 1e-9
                   for r in colloc["D"]["runs"])
    closed = achievable >= 1.0

    s2_walls = {r["start"]: r["wall_max_combined"] for r in colloc["S2"]["runs"]}

    shift = shift_metrics(banked, best, caps["D"])

    verdict = {
        "achievable_wall_D": achievable,
        "achieving_run": best["start"],
        "maximin_bound_D": bound_d["maximin_lower_bound"],
        "bound_respected_by_every_run": bool(bound_ok),
        "crosses_1_0": bool(achievable < 1.0),
        "verdict": ("REOPENS: the measured-caps biped admits a collocated trajectory under 1.0"
                    if achievable < 1.0 else
                    "CLOSED at the trajectory level: the minimum achievable wall under (d) is >= 1.0 "
                    "- no periodic collocated theta trajectory within the formulation clears the measured "
                    "caps; the measured-caps bipedal vault question is closed with the statics, and the "
                    "quadruped line stands alone as the only admissible gait line at (d)"),
        "quadruped_statement": ("the maximin bound over-unity nodes (phis "
                                f"{bound_d['over_unity_lb_phis']}) admit NO theta in the bounds that "
                                "clears 1.0 on any leg ratio - the vendored statics module's own verdict "
                                "rule: statically infeasible at any trunk pitch; the quadruped lane "
                                "stands alone at the measured (d) caps"),
        "scale_gate": ("S1 GATE (deposit arm scale): this verdict. At the SI-matched S2 scale the measured "
                       f"walls are {json.dumps(s2_walls)} (bound {bound_s2['maximin_lower_bound']}) - every "
                       "S1 verdict inverts; no engine consumption until the operator resolves the "
                       "deposit-vs-SI divergence (k = 0.11975394), the standing gate inherited verbatim"),
    }

    return {
        "schema": "chimera.rehearing_collocation.deliverable.v1",
        "lane": "rehearing_20260921",
        "branch": "agent/measured-caps-collocation-20260921",
        "derived_from_commit": "906368142212a5ff18b13bf4b0e5088e36a1a81d",
        "receipt": {"path": "tools/science_funnel/validation/rehearing_20260921/receipt.json",
                    "note": ("the receipt pins THIS deliverable (measured.deliverable.sha256); the reverse "
                             "pin is a path only - the receipt's measured block is appended after the derive, "
                             "so a content pin here would break cross-run determinism")},
        "inputs": inputs_recorded,
        "environment": env,
        "cap_sets_used": {
            "D": {**caps["D"], "hip": HIP_CAP, "posture": CAP_POST,
                  "provenance": "knee/mp hind book V1_S1; ankle plantar/dorsal ankle book V1_S1 (sign-gated); hip/posture HELD at the instrument's constants (the posture drive borrows the hip cap)"},
            "S2": {**caps["S2"], "hip": HIP_CAP, "posture": CAP_POST,
                   "provenance": "the k-gated inversion bracket (k = 0.11975394)"},
        },
        "instrument_reproduction": instrument,
        "wrapper_drift_check": drift,
        "reprice_D_chain": reprice,
        "maximin_bound": {"D": bound_d, "S2": bound_s2},
        "collocation_runs": colloc,
        "verdict": verdict,
        "trajectory_shift": shift,
    }


def canonical(d: dict) -> bytes:
    return (json.dumps(d, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def main():
    pins = verify_pins()
    caps = cap_book_values()
    banked = json.loads(BANKED.read_text(encoding="utf-8"))
    d1 = derive_once(pins, caps, banked)
    b1 = canonical(d1)
    d2 = derive_once(pins, caps, banked)
    b2 = canonical(d2)
    deterministic = b1 == b2
    if not deterministic:
        raise SystemExit("DETERMINISM FAILURE: two in-process derives differ")
    OUT.write_bytes(b1)
    sha = hashlib.sha256(b1).hexdigest()
    v = d1["verdict"]
    print(json.dumps({
        "deliverable": str(OUT), "sha256": sha, "determinism": "byte-identical x2",
        "instrument_held": d1["instrument_reproduction"]["checks"]["held"],
        "instrument_bytes_equal_banked": d1["instrument_reproduction"]["checks"]["bytes_equal_to_banked"],
        "wrapper_drift_exact": d1["wrapper_drift_check"]["exact"],
        "reprice_chain_equal": d1["reprice_D_chain"]["field_for_field_equal"],
        "maximin_bound_D": v["maximin_bound_D"],
        "achievable_wall_D": v["achievable_wall_D"], "achieving_run": v["achieving_run"],
        "crosses_1_0": v["crosses_1_0"],
        "walls_per_start_D": {r["start"]: r["wall_max_combined"] for r in d1["collocation_runs"]["D"]["runs"]},
        "walls_per_start_S2": {r["start"]: r["wall_max_combined"] for r in d1["collocation_runs"]["S2"]["runs"]},
        "verdict": v["verdict"],
    }, indent=1))


if __name__ == "__main__":
    main()
