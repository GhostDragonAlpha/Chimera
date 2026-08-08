"""theStandingHuman v2-rigid -- the MUSCLE battery (Lane M4).

RULE 0 -- STATEMENT: the frame stands when and only when derived muscle
torques close the free dofs of the kinematic tree.  K3 measured the
unactuated frame crumpling from t=0 (ropes changed nothing); v2 closes every
free dof with the PD loop of kinematic/muscle_controller.py at the gains
derived by kinematic/muscles.py (kp = 2*m*g*d, kd = 2*I*omega_n, torque caps
from specific tension x PCSA x moment arm -- no tuning, no training).

PREDICTION (named before the run): MAIN (muscles on, rotation locks OFF)
passes (a) LIMIT, (b) CAPTURE, (c) FRAME, (d) LIGAMENT, (e) STAND over the
t>=1200 verdict window at 8000 ticks @ 1 kHz; CONTROL (muscles relaxed at
tick 1200, the analog of K3's ligament cut) falls with extra COM drop vs MAIN
> L_leg*sin(12 deg) ~= 0.185 m inside 600 ticks.

FALSIFIERS: the six meters of demo_kinematic.py, UNCHANGED.  The battery
code, the bars, the window, the cadence are K3's; the only new physics is the
muscle channel.  A meter failing is a falsifier firing -- record, don't patch.

Usage:
    python LightEngine/demo_kinematic_v2.py            # MAIN + CONTROL
    python LightEngine/demo_kinematic_v2.py main       # MAIN only
"""

from __future__ import annotations

import math
import os
import sys
import time

import numpy as np

from LightEngine.kinematic import build_spec
from LightEngine.kinematic import transforms
from LightEngine.kinematic.dynamics import center_of_mass, init_state, step
from LightEngine.kinematic.muscle_controller import MuscleController
from LightEngine.demo_kinematic import (
    CONTROL_CUT_TICK,
    CONTROL_WINDOW,
    DT,
    N_TICKS,
    SAMPLE_EVERY,
    SETTLE_TICK,
    _joint_measurements,
    _m_fail,
    _support_polygon,
    _verdict,
)
from LightEngine.demo_skeleton import _point_in_polygon_xy
from LightEngine.kinematic.skeleton_spec import D_EQ_LU


def _run_v2(spec, state, label, controller, relax_muscles_at=None):
    """Run the battery with the muscle loop attached; return sampled metrics.

    Mirrors demo_kinematic._run tick-for-tick; the only additions are
    controller.apply(state) before each step and the relax hook (the CONTROL
    protocol: muscles go slack at the cut tick, so the frame must fall).
    """
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
        "max_sep": {},
        "max_moment_ratio": {},
        "com_inside_poly": True,
        "com_xy": [],
        "lig_compression_events": 0,
        "lig_max_force": 0.0,
        "head_z_min": math.inf,
        "head_z_max": -math.inf,
        "com_z_trace": [],
        "vmax": 0.0,
        "com_drift_x_lu": (com0[0] / float(spec["lam"]), None),
        # v2-only telemetry: how hard the muscles are working.
        "max_torque": 0.0,
    }

    relaxed = False
    t0 = time.time()
    for tick in range(N_TICKS + 1):
        if relax_muscles_at is not None and tick == relax_muscles_at and not relaxed:
            controller.enabled = False
            relaxed = True
            metrics["com_z_at_relax"] = float(center_of_mass(spec, state)[2])
        controller.apply(state)
        step(spec, state, DT, n_proj_iters=20)
        # Telemetry: peak muscle torque applied this tick (impulse / dt).
        motor_imp = state.get("motor_impulses")
        if motor_imp is not None and motor_imp.shape[0] > 0:
            tick_peak = float(np.max(np.abs(motor_imp))) / DT
            metrics["max_torque"] = max(metrics["max_torque"], tick_peak)

        vmax = float(np.max(np.linalg.norm(state["lin_vel"], axis=1)))
        metrics["vmax"] = max(metrics["vmax"], vmax)

        if tick % SAMPLE_EVERY != 0:
            continue
        in_window = tick >= SETTLE_TICK

        com = center_of_mass(spec, state)
        metrics["com_z_trace"].append((tick, float(com[2])))
        seps, moments = _joint_measurements(spec, state)

        # (d) ligament compression audit, identical to K3.
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


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    # CONTACT_LINKS=1 is the forefoot-contact membrane: support points ahead
    # of the MTP joint attach to the metatarsals/forefoot links instead of
    # tarsals, so the toe fold presses its own contacts into the ground.
    contact_links = os.environ.get("CONTACT_LINKS", "0") == "1"
    spec = build_spec(1.80, 80.0, contact_links=contact_links)

    # v3c A/B: CONTACTS_IN_SOLVE=1 moves the ground-contact rows into the
    # direct solve (default off: the post-solve sweep).  Same six meters,
    # same windows -- the run that decides the flag default.
    # CONTACT_FRICTION picks the friction mode when in-solve: 1 = full
    # cone in-solve (v3a, measured leaky), 2 = hybrid (v3e: normals
    # in-solve, friction swept, bounded at sweep-level steady state),
    # 3 = warm-start cone (friction-placement membrane: rows in-solve,
    # bound fixed all tick from the previous tick's normal impulse).
    in_solve = os.environ.get("CONTACTS_IN_SOLVE", "0") == "1"
    fric_mode = int(os.environ.get("CONTACT_FRICTION", "1"))
    # Ghost-free stack (the fall-saga forensics): POS_PASS_MODE=1 is
    # translation-only coincidence with the ligament position projection
    # retired; LIG_PLAY_BAND=1 adds the measured joint play to the
    # ligament rest; LIG_FORCE_LIMIT=1 clamps ligament impulses to
    # f_max * dt.  All default off: legacy stays bit-identical.
    pos_pass_mode = int(os.environ.get("POS_PASS_MODE", "0"))
    lig_play_band = os.environ.get("LIG_PLAY_BAND", "0") == "1"
    lig_force_limit = os.environ.get("LIG_FORCE_LIMIT", "0") == "1"

    state = init_state(spec)
    # v2 constitution: the muscles, NOT the rotation locks, close the free
    # dofs.  (2026-08-08 correction, autopsy + bone-closure + lock-split
    # saga: locks were NEVER vacuous -- they act only on locked axes, and
    # CONTROL still falls on every run; the toxic component was the
    # position-pass stabilization, not the rows.)  ROTATION_LOCKS picks
    # the lock mode for A/B: 0=off (default), 1=legacy both, 2=velocity
    # rows, 3=position pass, 4=Baumgarte bias rows.
    state["rotation_locks"] = int(os.environ.get("ROTATION_LOCKS", "0"))
    state["pos_pass_mode"] = pos_pass_mode
    state["lig_play_band"] = lig_play_band
    state["lig_force_limit"] = lig_force_limit
    if in_solve:
        state["contacts_in_solve"] = True
        state["contact_friction"] = fric_mode
    main_ctrl = MuscleController(spec, state)
    print(f"actuators: {len(main_ctrl.actuators)} "
          f"(torque limits {min(a['torque_limit_Nm'] for a in main_ctrl.actuators):.1f}"
          f"-{max(a['torque_limit_Nm'] for a in main_ctrl.actuators):.1f} N m)")
    mode_name = {0: "NONE", 1: "FULL CONE", 2: "HYBRID SWEPT",
                 3: "WARM-START CONE", 4: "FROZEN CONE",
                 5: "HYBRID -MUSCLE", 6: "ROLLING-BLIND",
                 7: "DERIVED-MU"}.get(fric_mode, str(fric_mode))
    if in_solve:
        print(f"ground loop: CONTACTS IN SOLVE, friction {mode_name}")
    main_metrics = _run_v2(spec, state, "MAIN", main_ctrl)
    print(f"[MAIN] peak actuator link-torque {main_metrics['max_torque']:.2f} N m")

    control_metrics = None
    if which == "both":
        state_c = init_state(spec)
        state_c["rotation_locks"] = int(os.environ.get("ROTATION_LOCKS", "0"))
        state_c["pos_pass_mode"] = pos_pass_mode
        state_c["lig_play_band"] = lig_play_band
        state_c["lig_force_limit"] = lig_force_limit
        if in_solve:
            state_c["contacts_in_solve"] = True
            state_c["contact_friction"] = fric_mode
        control_ctrl = MuscleController(spec, state_c)
        control_metrics = _run_v2(spec, state_c, "CONTROL", control_ctrl,
                                  relax_muscles_at=CONTROL_CUT_TICK)

    verdict = _verdict(main_metrics, spec, control_metrics,
                       title="STANDING HUMAN v2 -- MUSCLE BATTERY" + (
                           f" [CONTACTS IN SOLVE, friction {mode_name}]"
                           if in_solve else ""))
    # OPERATOR DATUM 6 (THE HUMAN terminal, 2026-08-08): head height is
    # the posture REWARD -- elevation buys environmental read, so a
    # stander extends, it does not merely not-fall.  A REPORT, not a
    # seventh gate: achieved max head height in the verdict window vs
    # the bind height (the skeleton's available maximum).
    for m in (main_metrics, control_metrics):
        if m is None:
            continue
        print(f"[{m['label']}] datum-6 head height: window max "
              f"{m['head_z_max']:.3f} m vs bind {m['head_z0']:.3f} m "
              f"({100.0 * m['head_z_max'] / m['head_z0']:.1f}%)")
    # OPERATOR DATUM 8 (THE HUMAN terminal, 2026-08-08): maximum head height
    # is a product of STANCE WIDTH -- the legs are struts, so lateral foot
    # offset beyond hip width costs vertical reach, and standing is a RANGE
    # from squat to full extension, not a point.  A REPORT, not a gate.  The
    # stance-aware ceiling is derived from the leg-as-strut geometry:
    # ceiling = head_z0 - (L_leg - sqrt(L_leg^2 - d_lat^2)), with d_lat the
    # per-leg lateral offset of foot center beyond the hip center.  No
    # tuning: L_leg is the scaling table's femur + tibia fractions, the
    # stance and hip widths come from the spec's own geometry.
    leg_m = (0.245 + 0.25) * 1.80  # femur + tibia length fractions (table)
    foot_c = {
        side: float(np.mean([cp["point_m"][1] for cp in spec["contacts"][side]]))
        for side in ("L", "R")
    }
    stance_w = abs(foot_c["L"] - foot_c["R"])
    hip_w = abs(float(spec["links"]["femur_L"]["prox_m"][1])
                - float(spec["links"]["femur_R"]["prox_m"][1]))
    d_lat = max(0.0, (stance_w - hip_w) / 2.0)
    drop = leg_m - math.sqrt(max(0.0, leg_m * leg_m - d_lat * d_lat))
    for m in (main_metrics, control_metrics):
        if m is None:
            continue
        ceiling = m["head_z0"] - drop
        print(f"[{m['label']}] datum-8 stance-aware ceiling: {ceiling:.3f} m "
              f"(stance {stance_w:.3f} m vs hips {hip_w:.3f} m), achieved "
              f"{100.0 * m['head_z_max'] / ceiling:.1f}%")
    failed = [k for k, ok in verdict.items() if not ok]
    print(f"\nVERDICT: {'FALSIFIED: ' + ', '.join(failed) if failed else 'STANDS'}")
    return verdict


if __name__ == "__main__":
    main()
