"""action_rhythm.py -- RHYTHM_DRIVE: cadence is derived, never tuned.

RULE 0, stated before the build, because this membrane is a theory:

    STATEMENT   a passive limit-cycle gait emerges from the leg's natural pendulum period
                under drive. The hip is driven by a muscle torque whose ONLY set point is the
                muscle's own contraction velocity -- not a cadence anyone dials in. What settles
                is a self-sustaining swing whose frequency is the body's own leg inertia. Cadence
                is derived, never tuned (THE_WOLFRAM_FRAME section cadence).

    PREDICTION  the leg's compound-pendulum period T_leg = 2*pi*sqrt(I/(m g d)) is derived from
                the model's own inertia the way SWING did. The preferred stride frequency is
                f = 1/(2*T_leg): one leg oscillation = one step, a stride = two steps
                (THE_MATHEMATICS_OF_WALKING: T = 1.506 s -> step 0.753 s). The driven limit
                cycle's stride frequency must equal 1/(2*T_leg).

    FALSIFIER   (stated before running) no stable limit cycle forms, or the measured stride
                frequency differs from 1/(2*T_leg) by more than the gait tolerance = 15% -- the
                same band SWING held its period to. Either would mean the cadence this body walks
                at is not its own leg's pendulum period and is being selected from outside.

LAWS ENFORCED. Reuse SWING's derived-inertia method (composite rigid body about the hip's
medio-lateral axis). ALLOMETRY: the drive's velocity scale Q is the muscle's allometric maximum
contraction velocity (strain rate x fiber length, size-independent rate) converted to an angular
rate by the leg's moment arm -- it sets the limit-cycle AMPLITUDE, never its frequency. No human
cadence number is imported anywhere.

WHY THE DRIVE DOES NOT SET THE CADENCE. The muscle torque is a van der Pol actuator:
    tau = +G * qv * (1 - (qv/Q)^2)
At low speed it is a NEGATIVE damper (the muscle does net positive work, sustaining the swing);
above Q it resists (the muscle cannot shorten faster than it physiologically can). Q is the
allometric contraction-velocity ceiling and fixes only how far the leg swings -- the frequency
that emerges is the pendulum's own, set by I, m, g, d. G is a single derived constant (muscle
torque scale ~ the body-weight torque), and it cannot move the frequency: a van der Pol limit
cycle sits at its linear natural frequency for any G that sustains it. So the cadence is pinned
by the body, and the drive is what keeps the pendulum from damping out, not what tells it how fast.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mujoco                                                       # noqa: E402
from world import load_body                                        # noqa: E402
from port_registry import MYOBODY, action_test                     # noqa: E402
import port_tests                                                   # noqa: E402  registers the ports this action rests on


GAIT_TOL = 0.15               # the gait tolerance, declared before the run
ALLOMETRIC_STRAIN_RATE = 1.5  # s^-1, skeletal-muscle max strain rate (size-independent)
K_G = 1.0                     # muscle torque scale as a fraction of the body-weight torque
BRACE_TOL_DEG = 1.0


def brace(m, d, q0, g, free=()):
    """An ORTHOSIS, copied from action_tests.py so this module is standalone. Hold every joint
    but `free` at q0, using the model's OWN passive spring (jnt_stiffness + dof_damping), which
    MuJoCo integrates implicitly. The hip is left free; the leg swings and nothing else moves."""
    W = float(np.sum(m.body_mass)) * g
    K = W * 0.9201 / math.radians(BRACE_TOL_DEG)
    C = 2.0 * math.sqrt(K * 3.0)
    skip = {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, x) for x in free}
    for j in range(m.njnt):
        if m.jnt_type[j] in (2, 3) and j not in skip:
            a, f = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
            m.jnt_stiffness[j] = K
            m.qpos_spring[a] = q0[a]
            m.dof_damping[f] = C
    return K


def _leg_pendulum(m, d, mujoco, side="r"):
    """SWING's derived-inertia method: the leg as a compound pendulum about the hip.

    Returns (T_leg, I, m_leg, d_com, adr) where T_leg = 2*pi*sqrt(I/(m g d)). Copied from a_swing
    so the two membranes measure the same body and agree on T_leg to the digit.
    """
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


@action_test(
    "rhythm_drive", ["rigid_body", "spindle", "hill_muscle"],
    "a passive limit-cycle gait emerges from the leg's natural pendulum period under drive: the "
    "hip, driven only by a muscle contraction-velocity-limited torque, settles to a self-sustaining "
    "swing whose frequency is the body's own leg inertia -- cadence is derived, never tuned",
    "T_leg = 2*pi*sqrt(I/(m g d)) is derived from the model's own inertia the way SWING did, and "
    "the preferred stride frequency is f = 1/(2*T_leg) (one leg oscillation = one step, a stride = "
    "two). The driven limit cycle's stride frequency must equal 1/(2*T_leg)",
    "no stable limit cycle forms, or the measured stride frequency differs from 1/(2*T_leg) by "
    "more than the gait tolerance (15%, the band SWING held its period to), which would mean the "
    "cadence this body walks at is not its own leg's pendulum period")
def a_rhythm_drive(arg=None):
    # WELD THE PELVIS, HANG THE LEG 1.5 m CLEAR -- the same compound-pendulum instrument SWING
    # uses, so the leg swings about a solver-held pivot and nothing teleports.
    m, g = load_body(MYOBODY, mujoco, fix_body="pelvis", hang_z=1.5)
    d = mujoco.MjData(m)
    mujoco.mj_resetData(m, d)
    d.qpos[7:] = m.key_qpos[0][7:]
    mujoco.mj_forward(m, d)

    T_leg, I, m_leg, dcm, adr = _leg_pendulum(m, d, mujoco, "r")
    dof = int(m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "hip_flexion_r")])

    # THE PREDICTION, from the body and nothing else.
    f_pred = 1.0 / (2.0 * T_leg)                 # stride frequency, derived

    # BRACE EVERY OTHER JOINT (free = hip_flexion_r), exactly as SWING does, so the leg swings
    # and nothing else wobbles or folds.
    brace(m, d, np.array(d.qpos), g, free=("hip_flexion_r",))

    # THE DRIVE, DERIVED FROM MUSCLE CONTRACTION VELOCITY (allometric), not from any cadence.
    # Q_ang = v_max / r_moment: the muscle's allometric maximum shortening velocity (strain rate
    #   x fiber length ~ strain rate x d_com) seen through the leg's moment arm. It sets only
    #   the swing AMPLITUDE, never the frequency.
    v_max = ALLOMETRIC_STRAIN_RATE * dcm          # m/s, allometric
    Q_ang = v_max / max(dcm, 1e-6)                # rad/s -- angular ceiling
    # G: a single derived constant. Muscle torque scale ~ body-weight torque (K_G), expressed as
    #   a van-der-Pol "damping" coefficient G = K_G * (m_leg g d_com) / Q_ang. Its magnitude
    #   decides whether the swing is sustained, not how fast it swings.
    G = K_G * (m_leg * g * dcm) / max(Q_ang, 1e-6)

    # START DISPLACED so the drive has a swing to sustain (the brace held the other joints).
    q0 = np.array(d.qpos)
    d.qpos[adr] = q0[adr] + math.radians(20.0)
    mujoco.mj_forward(m, d)

    N = 12000
    ts, qs = [], []
    for i in range(N):
        qv = float(d.qvel[dof])
        # van der Pol muscle torque: NEGATIVE damper below Q_ang (energy in), positive above it
        # (the muscle cannot shorten faster than it physiologically can). No frequency is fed in.
        tau = G * qv * (1.0 - (qv / Q_ang) ** 2)
        d.qfrc_applied[:] = 0.0
        d.qfrc_applied[dof] = tau
        mujoco.mj_step(m, d)
        ts.append(d.time)
        qs.append(float(d.qpos[adr]))

    qs = np.array(qs) - np.mean(qs)
    # upward zero crossings -> the leg's natural oscillation period
    zc = [ts[i] for i in range(1, len(qs)) if qs[i - 1] < 0 <= qs[i]]
    # keep only the tail (after the van-der-Pol transient has settled into the limit cycle)
    tail = zc[int(len(zc) * 0.4):] if len(zc) > 3 else zc
    T_meas = float(np.mean(np.diff(tail))) if len(tail) > 2 else float("nan")
    f_meas = 1.0 / (2.0 * T_meas) if (T_meas == T_meas and T_meas > 0) else float("nan")
    if len(tail) > 3:
        per = np.diff(tail)
        stable = float(np.std(per) / np.mean(per)) < 0.10
        n_cycles = len(tail) - 1
    else:
        stable = False
        n_cycles = max(len(tail) - 1, 0)

    err = (abs(f_meas - f_pred) / f_pred) if (f_pred > 0 and f_meas == f_meas) else 1.0
    ok = stable and err < GAIT_TOL
    return dict(pass_=ok, got=f"f = {f_meas:.4f} Hz",
                detail=f"T_leg = {T_leg:.4f} s (I {I:.4f} kg.m2, leg {m_leg:.3f} kg, "
                        f"pivot->CoM {dcm:.4f} m) -> predicted stride f = 1/(2*T_leg) = "
                        f"{f_pred:.4f} Hz. Drive: allometric v_max {v_max:.3f} m/s, Q_ang "
                        f"{Q_ang:.3f} rad/s, G {G:.2f}. MEASURED limit-cycle stride f = "
                        f"{f_meas:.4f} Hz over {n_cycles} cycles (T_meas {T_meas:.4f} s, "
                        f"{100*err:.1f}% off, stable={stable}). "
                        + ("Cadence pinned by the body: the drive only sustains the swing."
                           if ok else "FALSIFIER FIRED: cadence not the body's own pendulum period."))
