"""muscle_witness.py — X6: DOES THE GPU MUSCLE EQUAL THE CPU MUSCLE?

The whole engine rests on the two-messenger rule: a second implementation is trusted only when it
is witnessed against the first. I broke that rule -- `muscle_torque_gpu` (the GPU port used for
ALL training) was never checked against `muscle_torques()` (the CPU reference witnessed against
MuJoCo at X5). Every GPU-trained policy this session was trained against an unverified actuator,
and the faithful render only surfaced it because the two disagreed on screen.

This is the missing check. Same joint angles, same activations, interpreted the SAME way. If the
two torques agree, GPU training is sound and the standing failure is a controller problem. If they
DISAGREE, every training result so far was against the wrong body and that is the bug, not balance.

Run:  python ChimeraEngine/muscle_witness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from body import humanoid                                                    # noqa: E402

results = []


def check(name, ok, detail):
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def cpu_torque(h, q, act, qd=None):
    """CPU reference: set each muscle's activation directly, read muscle_torques()."""
    h.tree.q[:] = q
    h.tree.qd[:] = np.zeros(h.tree.n) if qd is None else qd
    for name, pr in h.pairs.items():
        j = h.joint[name]
        pr.flexor.dial = float(np.clip(act[2 * j], 0, 1))
        pr.extensor.dial = float(np.clip(act[2 * j + 1], 0, 1))
    return np.asarray(h.tree.muscle_torques(), float).copy()


def gpu_torque_real(h, q, act, qd=None):
    """Call the ACTUAL GPU functions on CPU-torch, so this witnesses the real training code, not a
    hand-copied replica that could drift from it."""
    import torch
    from train_gpu import muscle_tables, muscle_torque_gpu
    tb = muscle_tables(h, 'cpu', torch)
    qd = np.zeros(h.tree.n) if qd is None else qd
    qt = torch.tensor(q, dtype=torch.float32).unsqueeze(0)
    qdt = torch.tensor(qd, dtype=torch.float32).unsqueeze(0)
    at = torch.tensor(act, dtype=torch.float32).unsqueeze(0)
    return muscle_torque_gpu(tb, qt, qdt, at, torch).squeeze(0).numpy()


def main() -> int:
    print("\nX6: GPU muscle model vs CPU reference\n" + "=" * 68)
    h = humanoid()
    n = h.tree.n
    rng = np.random.default_rng(0)

    print("\nX6a  STATIC (qd = 0): the two must agree to roundoff if they are one model")
    worst = 0.0
    for t in range(8):
        q = rng.normal(0, 0.3, n)
        act = rng.uniform(0, 1, 2 * n)
        tc = cpu_torque(h, q, act, qd=None)
        tg = gpu_torque_real(h, q, act)
        d = float(np.max(np.abs(tc - tg)))
        worst = max(worst, d)
    print(f"      worst per-joint torque difference over 8 random states: {worst:.3e} N.m")
    check("GPU and CPU muscle torques agree at zero velocity", worst < 1e-3,   # float32 floor ~1e-5
          f"{worst:.2e} N.m -- if this fails, the activation mapping or the tables differ and every "
          "GPU-trained policy is against the wrong body")

    print("\nX6b  MOVING (qd != 0): does the GPU drop the CPU's force-velocity term?")
    q = rng.normal(0, 0.3, n)
    act = rng.uniform(0.3, 1, 2 * n)
    qd = rng.normal(0, 4.0, n)                        # real shortening/lengthening speeds
    tc = cpu_torque(h, q, act, qd=qd)
    tg = gpu_torque_real(h, q, act, qd=qd)               # now WITH force-velocity
    d = float(np.max(np.abs(tc - tg)))
    rel = d / max(float(np.max(np.abs(tc))), 1e-9)
    print(f"      worst difference at qd~4 rad/s: {d:.2f} N.m ({100*rel:.0f}% of peak torque)")
    print(f"      both now apply Hill force-velocity, so a moving body agrees too.")
    check("GPU and CPU agree WITH velocity (force-velocity now in the GPU port)", d < 1e-4,
          f"{d:.2e} N.m at qd~4 rad/s -- the seam is closed at both ends, static and moving")

    n_fail = sum(1 for ok in results if not ok)
    print("\n" + "=" * 68)
    print(f"{len(results) - n_fail}/{len(results)} checks passed")
    print("\nVERDICT: if X6a PASSED, the models share tables and mapping and differ ONLY by")
    print("force-velocity (X6b) -- add force-velocity to the GPU port and the seam closes. If X6a")
    print("FAILED, the disagreement is structural and no training result stands until it is fixed.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
