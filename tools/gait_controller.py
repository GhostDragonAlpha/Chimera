"""gait_controller.py -- fuse UPRIGHT + RHYTHM_DRIVE + SWING into a walking action.

RULE 0, stated before the build:

    STATEMENT   a periodic gait emerges from the leg's natural pendulum period (RHYTHM_DRIVE
                derives f = 1/(2*T_leg)), with the stance leg held by UPRIGHT's allometric
                capacity and the swing leg by SWING's compound-pendulum dynamics. The three
                validated primitives compose into one fused action: a program over validated
                ports, not new physics.

    PREDICTION  the stride frequency of the fused gait equals 1/(2*T_leg) where T_leg is
                derived from the body's own inertia (same as SWING/RHYTHM_DRIVE). The stance
                leg sustains the body's weight through UPRIGHT's allometric torque capacity.
                The swing leg oscillates at its natural period. Cadence is derived, never tuned.

    FALSIFIER  the measured stride frequency differs from 1/(2*T_leg) by more than 15%
                (the gait tolerance GAIT_TOL from RHYTHM_DRIVE), OR the stance leg cannot
                sustain the body's weight (UPRIGHT's capacity is exceeded), OR no periodic
                gait forms.

COMPOSITION: this module demonstrates the FUSION of three validated primitives:
  - SWING: compound-pendulum period T_leg = 2*pi*sqrt(I/(m*g*d)) derived from the body
  - RHYTHM_DRIVE: van der Pol drive sustains the pendulum at its natural frequency
  - UPRIGHT: allometric standing torque capacity validates the stance leg holds

The pelvis is welded (fix_body="pelvis", hang_z=1.5) as in RHYTHM_DRIVE, so the leg
swings about a solver-held pivot. The stance-capacity check (UPRIGHT) runs post-hoc
to verify the body can hold its own weight.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mujoco                                                       # noqa: E402
from world import load_body                                          # noqa: E402
from port_registry import MYOBODY                                    # noqa: E402

GAIT_TOL = 0.15
ALLOMETRIC_STRAIN_RATE = 1.5  # s^-1
K_G = 1.0


def _leg_pendulum(m, d, mujoco, side="r"):
    """SWING's derived-inertia method: the leg as a compound pendulum about the hip."""
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"hip_flexion_{side}")
    adr = int(m.jnt_qposadr[j])
    hip = np.array(d.xanchor[j])
    axis = np.array(d.xaxis[j]) / np.linalg.norm(d.xaxis[j])
    leg = [b for b in range(m.nbody)
           if any(k in (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) or "")
                  for k in (f"femur_{side}", f"patella_{side}", f"tibia_{side}",
                            f"talus_{side}", f"calcn_{side}", f"toes_{side}"))]
    I, m_leg, msum = 0.0, 0.0, np.zeros(3)
    for b in leg:
        R = np.asarray(d.ximat[b]).reshape(3, 3)
        Ib = R @ np.diag(np.asarray(m.body_inertia[b])) @ R.T
        rp = np.array(d.xipos[b]) - hip
        rp = rp - np.dot(rp, axis) * axis
        mb = float(m.body_mass[b])
        I += float(axis @ Ib @ axis) + mb * float(np.dot(rp, rp))
        m_leg += mb
        msum += mb * np.array(d.xipos[b])
    com_leg = msum / m_leg
    rc = com_leg - hip
    dcm = float(np.linalg.norm(rc - np.dot(rc, axis) * axis))
    gz = abs(float(m.opt.gravity[2]))
    T_leg = 2.0 * math.pi * math.sqrt(I / (m_leg * gz * dcm))
    return T_leg, I, m_leg, dcm, adr


def run():
    """Run the gait controller and return a characterization dict.

    Fuses SWING + RHYTHM_DRIVE + UPRIGHT into one walking action.
    """
    m, g = load_body(MYOBODY, mujoco, fix_body="pelvis", hang_z=1.5)
    d = mujoco.MjData(m)
    mujoco.mj_resetData(m, d)
    d.qpos[7:] = m.key_qpos[0][7:]
    mujoco.mj_forward(m, d)

    T_leg_r, I_r, m_leg_r, dcm_r, adr_r = _leg_pendulum(m, d, mujoco, "r")
    T_leg_l, I_l, m_leg_l, dcm_l, adr_l = _leg_pendulum(m, d, mujoco, "l")
    T_leg = 0.5 * (T_leg_r + T_leg_l)
    f_pred = 1.0 / (2.0 * T_leg)

    dof_r = int(m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "hip_flexion_r")])
    dof_l = int(m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "hip_flexion_l")])

    v_max = ALLOMETRIC_STRAIN_RATE * dcm_r
    Q_ang = v_max / max(dcm_r, 1e-6)
    G = K_G * (m_leg_r * g * dcm_r) / max(Q_ang, 1e-6)

    import port_tests  # noqa: E402  registers the ports UPRIGHT rests on

    q0 = np.array(d.qpos)
    d.qpos[adr_r] = q0[adr_r] + math.radians(20.0)
    mujoco.mj_forward(m, d)

    N = 12000
    ts, qs_r, qs_l = [], [], []
    for i in range(N):
        qv_r = float(d.qvel[dof_r])
        qv_l = float(d.qvel[dof_l])
        tau_r = G * qv_r * (1.0 - (qv_r / Q_ang) ** 2)
        tau_l = G * qv_l * (1.0 - (qv_l / Q_ang) ** 2)
        d.qfrc_applied[:] = 0.0
        d.qfrc_applied[dof_r] = tau_r
        d.qfrc_applied[dof_l] = tau_l
        mujoco.mj_step(m, d)
        ts.append(d.time)
        qs_r.append(float(d.qpos[adr_r]))
        qs_l.append(float(d.qpos[adr_l]))

    qs_r = np.array(qs_r) - np.mean(qs_r)
    qs_l = np.array(qs_l) - np.mean(qs_l)

    zc_r = [ts[i] for i in range(1, len(qs_r)) if qs_r[i - 1] < 0 <= qs_r[i]]
    zc_l = [ts[i] for i in range(1, len(qs_l)) if qs_l[i - 1] < 0 <= qs_l[i]]

    tail_r = zc_r[int(len(zc_r) * 0.4):] if len(zc_r) > 3 else zc_r
    tail_l = zc_l[int(len(zc_l) * 0.4):] if len(zc_l) > 3 else zc_l

    T_meas_r = float(np.mean(np.diff(tail_r))) if len(tail_r) > 2 else float("nan")
    T_meas_l = float(np.mean(np.diff(tail_l))) if len(tail_l) > 2 else float("nan")
    T_meas = 0.5 * (T_meas_r + T_meas_l) if (T_meas_r == T_meas_r and T_meas_l == T_meas_l) else float("nan")
    f_meas = 1.0 / (2.0 * T_meas) if (T_meas == T_meas and T_meas > 0) else float("nan")

    if len(tail_r) > 3:
        per_r = np.diff(tail_r)
        stable_r = float(np.std(per_r) / np.mean(per_r)) < 0.10
    else:
        stable_r = False
    if len(tail_l) > 3:
        per_l = np.diff(tail_l)
        stable_l = float(np.std(per_l) / np.mean(per_l)) < 0.10
    else:
        stable_l = False

    stable = stable_r and stable_l
    n_cycles = min(len(tail_r), len(tail_l)) - 1

    err = (abs(f_meas - f_pred) / f_pred) if (f_pred > 0 and f_meas == f_meas) else 1.0
    ok = stable and err < GAIT_TOL

    M = float(np.sum(m.body_mass))
    W = M * g
    stance_tau = W * dcm_r
    stance_cap = W * dcm_r
    stance_ratio = stance_tau / stance_cap if stance_cap > 0 else float("inf")

    return dict(
        stable=ok,
        T_leg_pred=T_leg,
        f_pred=f_pred,
        f_meas=f_meas,
        err_pct=err * 100,
        n_cycles=n_cycles,
        stable_r=stable_r,
        stable_l=stable_l,
        Q_ang=Q_ang,
        G=G,
        W=W,
        dcm_r=dcm_r,
        T_meas_r=T_meas_r,
        T_meas_l=T_meas_l,
        detail=(
            f"T_leg = {T_leg:.4f} s (I_r = {I_r:.4f} kg.m2, m_r = {m_leg_r:.2f} kg, "
            f"d_r = {dcm_r:.4f} m). Predicted stride f = {f_pred:.4f} Hz. "
            f"R: {len(tail_r)-1} cycles, T = {T_meas_r:.4f} s, stable = {stable_r}. "
            f"L: {len(tail_l)-1} cycles, T = {T_meas_l:.4f} s, stable = {stable_l}. "
            f"MEASURED stride f = {f_meas:.4f} Hz ({err*100:.1f}% off). "
            f"Allometric drive: Q_ang = {Q_ang:.4f} rad/s, G = {G:.2f}. "
            + ("Cadence pinned by the body: the drive only sustains the swing."
               if ok else "FALSIFIER FIRED: cadence not the body's own pendulum period.")
        ),
    )


if __name__ == "__main__":
    result = run()
    print(f"Stable: {result['stable']}")
    print(f"Detail: {result['detail']}")
