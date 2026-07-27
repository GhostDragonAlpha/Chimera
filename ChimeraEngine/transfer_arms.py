"""transfer_arms.py — take the moment-arm curves OFF MyoSuite and ONTO our joints.

    "The muscle transmission is decided by nature so we have to find actual biological data that's
     been recorded."                                            -- the operator, 2026-07-26

MyoSuite's models carry cadaver dissection, MRI and ultrasound as tendon paths wrapping around
geometry. Rather than re-derive that, sweep each joint, read the moment arm the geometry produces,
and FIT our `r(q) = r0 + r1 cos(q - q_peak)` to it. The fit is not the source of truth -- the
sweep is; the fit is just how our engine stores it.

    THE COUPLED-JOINT TRAP, and it is why the knee read 3.2 mm instead of 46. An OpenSim knee
    drives four other DOFs (two translations, two rotations) through EQUALITY CONSTRAINTS. Writing
    qpos and calling mj_forward does NOT enforce them -- equalities produce constraint FORCES, not
    kinematic substitution -- so the patellofemoral mechanism never moves. And the patella IS a
    pulley: it holds the quadriceps tendon off the joint centre, which is the entire reason the
    knee's arm is large and flat. Miss the coupling and you delete the patella.

    The fix is exact and cheap: mjEQ_JOINT stores the polynomial q_dependent = a0 + a1 q + a2 q^2
    + a3 q^3 + a4 q^4 in eq_data. Evaluate it and write the dependent joints yourself.

Run:  python ChimeraEngine/transfer_arms.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
LEG = ROOT / 'external' / 'myo_sim' / 'leg' / 'myolegs.xml'
BODY = ROOT / 'external' / 'myo_sim' / 'body' / 'myobody.xml'


def _id(m, objtype, name) -> int:
    import mujoco
    i = mujoco.mj_name2id(m, objtype, name)
    # mj_name2id returns -1 for an unknown name, and qpos[-1] / ten_length[-1] are VALID indices --
    # so a typo silently reads the LAST element and reports a plausible constant. Two lookups
    # failed exactly this way before this assert existed.
    assert i >= 0, f'no such {objtype}: {name}'
    return i


def apply_couplings(m, d, driver_adr: int) -> None:
    """Enforce every mjEQ_JOINT whose independent joint is the one we just moved."""
    import mujoco
    for e in range(m.neq):
        if m.eq_type[e] != mujoco.mjtEq.mjEQ_JOINT or not m.eq_active0[e]:
            continue
        dep, ind = int(m.eq_obj1id[e]), int(m.eq_obj2id[e])
        if ind < 0:
            continue
        a_ind = m.jnt_qposadr[ind]
        if a_ind != driver_adr:
            continue
        q = d.qpos[a_ind]
        c = m.eq_data[e][:5]
        d.qpos[m.jnt_qposadr[dep]] = c[0] + c[1]*q + c[2]*q**2 + c[3]*q**3 + c[4]*q**4


def moment_arm(m, d, joint: str, actuators, ang: float, h: float = 2e-4) -> float:
    """r = -dL/dq, averaged over a muscle group, with the couplings honoured at BOTH samples."""
    import mujoco
    adr = m.jnt_qposadr[_id(m, mujoco.mjtObj.mjOBJ_JOINT, joint)]
    tens = [int(m.actuator_trnid[_id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, a), 0]) for a in actuators]
    out = []
    for s in (+h, -h):
        d.qpos[:] = m.qpos0
        d.qpos[adr] = ang + s
        apply_couplings(m, d, adr)
        mujoco.mj_forward(m, d)
        out.append(np.array([d.ten_length[t] for t in tens]))
    return float(np.mean(-(out[0] - out[1]) / (2 * h)))


def sweep(model_path, joint, actuators, lo_deg, hi_deg, n=25):
    import mujoco
    m = mujoco.MjModel.from_xml_path(str(model_path))
    d = mujoco.MjData(m)
    qs = np.radians(np.linspace(lo_deg, hi_deg, n))
    rs = np.array([moment_arm(m, d, joint, actuators, q) for q in qs])
    return qs, np.abs(rs)


def fit_cosine(qs, rs):
    """Least-squares fit of r0 + r1 cos(q - qp), done linearly: r0 + A cos q + B sin q."""
    M = np.stack([np.ones_like(qs), np.cos(qs), np.sin(qs)], axis=1)
    c, *_ = np.linalg.lstsq(M, rs, rcond=None)
    r0, A, B = c
    r1 = float(np.hypot(A, B))
    qp = float(np.arctan2(B, A))
    pred = r0 + r1 * np.cos(qs - qp)
    rms = float(np.sqrt(np.mean((pred - rs) ** 2)))
    return float(r0), r1, qp, rms


# our joint -> (model, MyoSuite joint, the muscle group that crosses it, sweep range)
MAP = {
    'hip_pitch':   (LEG, 'hip_flexion_r', ('glmax1_r', 'glmax2_r', 'glmax3_r'), -20, 90),
    'hip_roll':    (LEG, 'hip_adduction_r', ('glmed1_r', 'glmed2_r', 'addlong_r'), -30, 30),
    'knee':        (LEG, 'knee_angle_r', ('recfem_r', 'vasint_r', 'vaslat_r', 'vasmed_r'), -100, 0),
    'ankle_pitch': (LEG, 'ankle_angle_r', ('soleus_r', 'gasmed_r', 'gaslat_r'), -30, 20),
    'ankle_roll':  (LEG, 'subtalar_angle_r', ('tibpost_r', 'perlong_r'), -20, 20),
}


def main() -> int:
    try:
        import mujoco  # noqa: F401
    except ImportError:
        print('mujoco not installed')
        return 1
    print('\nTRANSFER: MyoSuite moment arms -> our r(q) = r0 + r1 cos(q - q_peak)\n' + '=' * 76)
    print(f"{'our joint':<14}{'r0 mm':>8}{'swing':>8}{'q_peak':>9}{'fit RMS':>9}   measured range")
    print('-' * 76)
    table = {}
    for name, (path, mjnt, acts, lo, hi) in MAP.items():
        try:
            qs, rs = sweep(path, mjnt, acts, lo, hi)
        except AssertionError as e:
            print(f'{name:<14}  SKIPPED -- {e}')
            continue
        r0, r1, qp, rms = fit_cosine(qs, rs)
        swing = r1 / max(abs(r0), 1e-9)
        table[name] = (round(r0, 4), round(swing, 3), round(qp, 3))
        print(f'{name:<14}{r0*1000:8.1f}{swing:8.3f}{np.degrees(qp):8.0f}d{rms*1000:8.2f}   '
              f'{rs.min()*1000:.1f}-{rs.max()*1000:.1f} mm over {lo:.0f}..{hi:.0f} deg')
    print('-' * 76)
    print('\nMOMENT_ARM entries (paste into body.py):')
    for k, (r0, sw, qp) in table.items():
        print(f"    '{k}': ({r0:.4f}, {sw:.3f}, {qp:+.3f}, 'MYOSUITE'),")
    print('\nNOTE: the SWEEP is the source of truth; the cosine fit is only how our engine stores')
    print('it. Where the RMS is large the real curve is not a cosine, and that joint deserves a')
    print('tabulated r(q) rather than a fit.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
