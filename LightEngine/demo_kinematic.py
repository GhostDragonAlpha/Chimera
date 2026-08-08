"""theStandingHuman v1 — RIGID-model falsifier battery (Lane K3).

The grain-era battery (LightEngine/demo_skeleton.py) ran the print and asked
whether the printed grains held.  The rigid runtime (kinematic/dynamics.py)
asks the same constitution questions of the 77-link rigid skeleton:

  (a) LIMIT     (grain INTEGRITY): per-link transverse reaction moment from
                the joint impulses must stay under M_fail = sigma * Z,
                sigma = 170 MPa (ANATOMY-DATUM cortical strength),
                Z = pi D^3 / 32 with D = the link's ANATOMY-DATUM diameter.
                A bone under a moment above M_fail is a broken bone.
  (b) CAPTURE   : joint-center separation <= d_eq_m (the measured joint
                play; beyond it the joint is dislocated).
  (c) FRAME     : whole-body COM projects inside the support polygon
                (convex hull of the foot contact points).
  (d) LIGAMENT  (grain ROPE): tension-only -- no sample may show a ligament
                carrying force while shorter than its rest length
                (compression), and the loaded set must show load.
  (e) STAND     : head z within z0 +/- (H_head * tan(2 deg) + d_eq_m),
                the spine v2 frame bar plus the play allowance.
  (f) CONTROL   : ligaments cut at settle -> COM drop >
                L_leg * sin(12 deg) within 600 ticks.  The frame MUST fall.

PREDICTION (named before the run, per RULE 0): the rigid model with v1's
COM geometry tips in the SAME direction as the grain run's measured drift
(x 1.29 -> 1.73 lu) but faster and cleaner, because a rigid joint cannot
ooze; and the control MUST fall this time (the grain control's refusal to
fall was one of v1's falsifiers).

The lurch protocol carries over: meters listen from t=0, the verdict window
is t=1200-8000 only (1.2x the 1000-tick decay bound measured on v1/v2).

Usage:
    python LightEngine/demo_kinematic.py            # MAIN + CONTROL
    python LightEngine/demo_kinematic.py main       # MAIN only
"""

from __future__ import annotations

import math
import sys
import time

import numpy as np

from LightEngine.kinematic import build_spec
from LightEngine.kinematic import transforms
from LightEngine.kinematic.dynamics import (
    center_of_mass,
    contact_forces,
    init_state,
    step,
)
from LightEngine.kinematic.skeleton_spec import D_EQ_LU
from LightEngine.demo_skeleton import (
    _convex_hull_xy,
    _point_in_polygon_xy,
)

# ---------------------------------------------------------------------------
# Derived bars (ANATOMY-DATUM / derived at init, never tuned)
# ---------------------------------------------------------------------------
SIGMA_BONE = 170.0e6       # ANATOMY-DATUM: cortical bone strength (Pa).
DT = 1e-3                  # tick (s); the solver was verified at 1 kHz.
N_TICKS = 8000             # verdict protocol length (as v1).
SETTLE_TICK = 1200         # verdict window opens (lurch protocol, v1).
CONTROL_CUT_TICK = 1200    # control: ropes cut after settle.
CONTROL_WINDOW = 600       # control: fall must begin within these ticks.
SAMPLE_EVERY = 20          # meter cadence (ticks).
STAND_ANGLE = math.radians(2.0)    # spine v2 frame bar.
FALL_ANGLE = math.radians(12.0)    # sacrum-tilt failure angle (spine v1/v2).


def _support_polygon(state) -> np.ndarray:
    """Convex hull of the foot contact points (world xy)."""
    pts = []
    for rec in state["contact_records"]:
        li = rec["link_idx"]
        R = transforms.to_matrix(state["quat"][li])
        p = state["pos"][li] + R @ rec["offset_local"]
        pts.append(p[:2])
    return _convex_hull_xy(np.asarray(pts, dtype=np.float64))


def _joint_measurements(spec, state):
    """Per-joint separation (m) and per-child-link transverse reaction
    moment (N m) for the current tick's recorded impulses."""
    dt = state["dt"] or DT
    seps = {}
    moments = {}
    for ji, name in enumerate(state["joint_names"]):
        pa = state["joint_parent"][ji]
        cb = state["joint_child"][ji]
        R_p = transforms.to_matrix(state["quat"][pa])
        R_c = transforms.to_matrix(state["quat"][cb])
        p_p = state["pos"][pa] + R_p @ state["r_joint_parent_local"][ji]
        p_c = state["pos"][cb] + R_c @ state["r_joint_child_local"][ji]
        seps[name] = float(np.linalg.norm(p_c - p_p))
        # Moment about the child COM from this tick's joint impulses;
        # transverse part (perpendicular to the link's long axis) bends the
        # bone shaft.
        torque = state["joint_impulses_lin"][ji] * 0.0 \
            + state["joint_impulses_ang"][ji] / dt
        link = spec["links"][state["link_names"][cb]]
        axis = link["basis_z"]
        t_vec = torque - float(torque @ axis) * axis
        moments[state["link_names"][cb]] = float(np.linalg.norm(t_vec))
    return seps, moments


def _m_fail(link) -> float:
    """Bending failure moment sigma * Z for a solid circular section."""
    D = float(link["row"].get("anatomical_diameter_m",
                              link["row"]["outer_diameter_m"]))
    Z = math.pi * D ** 3 / 32.0
    return SIGMA_BONE * Z


def _run(spec, state, label, cut_ligaments_at=None):
    """Run the battery and return the sampled metrics."""
    d_eq_m = float(spec["lam"]) * D_EQ_LU
    poly = _support_polygon(state)
    skull = state["name_to_idx"]["skull"]
    head_z0 = float(state["pos"][skull][2])
    com0 = center_of_mass(spec, state).copy()

    metrics = {
        "label": label,
        "d_eq_m": d_eq_m,
        "head_z0": head_z0,
        "com0": com0,
        "max_sep": {},          # per joint, verdict window
        "max_moment_ratio": {}, # per link, verdict window, M / M_fail
        "com_inside_poly": True,
        "com_xy": [],           # trace
        "lig_compression_events": 0,
        "lig_max_force": 0.0,
        "head_z_min": math.inf,
        "head_z_max": -math.inf,
        "com_z_trace": [],
        "vmax": 0.0,
        "com_drift_x_lu": (com0[0] / float(spec["lam"]), None),
    }

    cut_done = False
    t0 = time.time()
    for tick in range(N_TICKS + 1):
        if cut_ligaments_at is not None and tick == cut_ligaments_at and not cut_done:
            for key in ("lig_idx_a", "lig_idx_b", "lig_off_a", "lig_off_b",
                        "lig_rest"):
                state[key] = state[key][:0]
            state["lig_records"] = []
            cut_done = True
            metrics["com_z_at_cut"] = float(center_of_mass(spec, state)[2])
        step(spec, state, DT, n_proj_iters=20)

        vmax = float(np.max(np.linalg.norm(state["lin_vel"], axis=1)))
        metrics["vmax"] = max(metrics["vmax"], vmax)

        if tick % SAMPLE_EVERY != 0:
            continue
        in_window = tick >= SETTLE_TICK

        com = center_of_mass(spec, state)
        metrics["com_z_trace"].append((tick, float(com[2])))
        seps, moments = _joint_measurements(spec, state)

        # (d) ligament compression audit, every sample: force while SHORTER
        # than rest by more than the play allowance.  (The impulse is solved
        # pre-integration; a post-integration sample can read length < rest
        # by sub-play amounts without any compression force existing.)
        dt = state["dt"] or DT
        for li, rec in enumerate(state["lig_records"]):
            f = float(np.linalg.norm(state["lig_impulses_lin"][li])) / dt
            metrics["lig_max_force"] = max(metrics["lig_max_force"], f)
            ia, ib = rec["idx_a"], rec["idx_b"]
            Ra = transforms.to_matrix(state["quat"][ia])
            Rb = transforms.to_matrix(state["quat"][ib])
            pa = state["pos"][ia] + Ra @ rec["offset_a_local"]
            pb = state["pos"][ib] + Rb @ rec["offset_b_local"]
            length = float(np.linalg.norm(pb - pa))
            if f > 1e-9 and length < rec["rest_length_m"] - d_eq_m:
                metrics["lig_compression_events"] += 1

        if not in_window:
            continue

        for name, s in seps.items():
            metrics["max_sep"][name] = max(metrics["max_sep"].get(name, 0.0), s)
        for lname, m in moments.items():
            ratio = m / _m_fail(spec["links"][lname])
            metrics["max_moment_ratio"][lname] = max(
                metrics["max_moment_ratio"].get(lname, 0.0), ratio)
        metrics["com_xy"].append((tick, float(com[0]), float(com[1])))
        if not _point_in_polygon_xy(com[:2], poly):
            metrics["com_inside_poly"] = False
        hz = float(state["pos"][skull][2])
        metrics["head_z_min"] = min(metrics["head_z_min"], hz)
        metrics["head_z_max"] = max(metrics["head_z_max"], hz)

    metrics["com_drift_x_lu"] = (
        metrics["com_drift_x_lu"][0],
        float(center_of_mass(spec, state)[0]) / float(spec["lam"]),
    )
    metrics["wall_s"] = time.time() - t0
    return metrics


def _verdict(metrics, spec, control_metrics=None,
             title="STANDING HUMAN v1 -- RIGID MODEL BATTERY"):
    """Print the falsifier battery verdict."""
    d_eq = metrics["d_eq_m"]
    H = metrics["head_z0"]
    stand_band = H * math.tan(STAND_ANGLE) + d_eq
    print(f"\n[{metrics['label']}] {title}")
    print(f"  wall time {metrics['wall_s']:.0f}s  vmax {metrics['vmax']:.3f} m/s")
    print("  NOTE: the floor holds ONLY the feet (10 contact points).  A crumpled")
    print("  link below z=0 is a model limitation, not a measurement; (c)/(e) read")
    print("  the crumple honestly only until floor penetration dominates.")

    # (a) LIMIT
    worst_link, worst_ratio = "", 0.0
    for lname, ratio in metrics["max_moment_ratio"].items():
        if ratio > worst_ratio:
            worst_link, worst_ratio = lname, ratio
    limit_ok = worst_ratio <= 1.0
    print(f"  (a) LIMIT     : {'PASS' if limit_ok else 'FAIL'}  "
          f"worst {worst_link} M/M_fail = {worst_ratio:.3f}")

    # (b) CAPTURE
    worst_joint, worst_sep = "", 0.0
    for jname, s in metrics["max_sep"].items():
        if s > worst_sep:
            worst_joint, worst_sep = jname, s
    capture_ok = worst_sep <= d_eq
    print(f"  (b) CAPTURE   : {'PASS' if capture_ok else 'FAIL'}  "
          f"worst {worst_joint} sep = {worst_sep:.6f} m (band {d_eq:.6f})")

    # (c) FRAME
    print(f"  (c) FRAME     : {'PASS' if metrics['com_inside_poly'] else 'FAIL'}  "
          f"COM x drift {metrics['com_drift_x_lu'][0]:.2f} -> "
          f"{metrics['com_drift_x_lu'][1]:.2f} lu")

    # (d) LIGAMENT
    lig_ok = metrics["lig_compression_events"] == 0
    print(f"  (d) LIGAMENT  : {'PASS' if lig_ok else 'FAIL'}  "
          f"compression events {metrics['lig_compression_events']}, "
          f"max force {metrics['lig_max_force']:.1f} N")

    # (e) STAND
    z_lo = metrics["head_z0"] - stand_band
    z_hi = metrics["head_z0"] + stand_band
    stand_ok = metrics["head_z_min"] >= z_lo and metrics["head_z_max"] <= z_hi
    print(f"  (e) STAND     : {'PASS' if stand_ok else 'FAIL'}  "
          f"head z [{metrics['head_z_min']:.3f}, {metrics['head_z_max']:.3f}] "
          f"vs band [{z_lo:.3f}, {z_hi:.3f}]")

    verdict = {
        "limit": limit_ok,
        "capture": capture_ok,
        "frame": metrics["com_inside_poly"],
        "ligament": lig_ok,
        "stand": stand_ok,
    }

    # (f) CONTROL -- COMPARATIVE extra drop.  v1's absolute bar assumed a
    # SETTLED standing frame at cut time; this frame is unactuated and
    # crumples from t=0, so by the cut tick the COM is already low and the
    # absolute bar is meaningless.  Derivation: if the ligament network
    # carries load, cutting it must drop the COM FASTER than the intact
    # frame falls; the extra drop over the same window is the rope load made
    # visible.  Bar = L_leg * sin(12 deg), the v1 sacrum-tilt failure drop.
    if control_metrics is not None:
        leg = (0.245 + 0.25) * 1.80  # femur + tibia length fractions (table)
        delta_fail = leg * math.sin(FALL_ANGLE)
        main_z = {t: z for t, z in metrics["com_z_trace"]}
        extra = 0.0
        for t, z in control_metrics["com_z_trace"]:
            if CONTROL_CUT_TICK <= t <= CONTROL_CUT_TICK + CONTROL_WINDOW \
                    and t in main_z:
                extra = max(extra, main_z[t] - z)
        control_fell = extra > delta_fail
        verdict["control"] = control_fell
        print(f"  (f) CONTROL   : {'PASS' if control_fell else 'FAIL'}  "
              f"extra COM drop vs MAIN {extra:.3f} m in {CONTROL_WINDOW} ticks "
              f"(bar {delta_fail:.3f} m)")
    return verdict


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    spec = build_spec(1.80, 80.0)

    state = init_state(spec)
    # v1 constitution: ROM from the ligament network, not rotation locks.
    state["rotation_locks"] = False
    main_metrics = _run(spec, state, "MAIN")

    control_metrics = None
    if which == "both":
        state_c = init_state(spec)
        state_c["rotation_locks"] = False
        control_metrics = _run(spec, state_c, "CONTROL",
                               cut_ligaments_at=CONTROL_CUT_TICK)

    verdict = _verdict(main_metrics, spec, control_metrics)
    failed = [k for k, ok in verdict.items() if not ok]
    print(f"\nVERDICT: {'FALSIFIED: ' + ', '.join(failed) if failed else 'STANDS'}")
    return verdict


if __name__ == "__main__":
    main()
