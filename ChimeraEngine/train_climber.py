"""train_climber.py — ONE limb moves, the others HOLD. The mountain-climber primitive.

    "A mountain climber moves one limb at a time maintaining three points of contact at all times."
    "One type of electron -- the simplest reducible item gives the most complexity."
                                                                    -- the operator, 2026-07-27

This is the ONE-ELECTRON principle applied to control. Not a monolithic net learning whole-body
balance (which drifts -- confirmed this session), but ONE small controller for ONE reducible act:
move a single limb from where it is to a target, while the OTHER contacts hold the body.
Instantiated per limb and composed, this is standing, stepping, climbing and getting up -- the
same rule fired again, the way every electron is the same field fired again.

    WHY IT LEARNS WHERE BALANCE DID NOT. It is QUASI-STATIC by construction. The body starts in a
    settled multi-contact sprawl (dropped and left to rest), and only ONE limb is asked to move.
    The remaining contacts are a wide, stable base, so the COM stays inside the support and no
    dynamic balancing is required. That is the trick the mountain climber uses, and it is why
    "keep the others, move one" is safe where "stand on two from scratch" is not.

    THE REWARD IS DENSE ON EVERY TERM: swing limb toward its target, every step; the other contacts
    stay planted, every step, on every limb. No scalar a jump can max, no sparse did-you-end-upright.

    THE MUSCLE IS THE WITNESSED ONE (X6, muscle_witness 2/2) -- the first training on the correct
    actuator.

Run:  python ChimeraEngine/train_climber.py [--gens N] [--pop N]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from body import ACT_DIM, humanoid                                           # noqa: E402
from mjcf_body import to_mjcf                                                # noqa: E402
from train_gpu import muscle_tables, muscle_torque_gpu                       # noqa: E402

DT = 5e-4
CONTROL_EVERY = 20
SETTLE = 0.4
EPISODE = 1.4
HID = 32
LR = 0.5
SWING = 'forearmL'


def main() -> int:
    import torch, warp as wp, mujoco, mujoco_warp as mjw
    gens = int(sys.argv[sys.argv.index('--gens') + 1]) if '--gens' in sys.argv else 40
    pop = int(sys.argv[sys.argv.index('--pop') + 1]) if '--pop' in sys.argv else 256
    dev = 'cuda'
    torch.manual_seed(8)

    h = humanoid()
    n = h.tree.n
    mjm = mujoco.MjModel.from_xml_string(to_mjcf(h, dt=DT, floor=True))
    mjd = mujoco.MjData(mjm); mjd.qpos[2] = 0.55; mujoco.mj_forward(mjm, mjd)
    bid = lambda s: mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, s)
    SW = bid(SWING); HEAD = bid('head')
    HOLD = [bid(s) for s in ('footL', 'footR', 'forearmR', 'shinL', 'shinR', 'chest')]

    W = pop
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=64)   # PER WORLD, not total (W*10 overflows int32 at large W)
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    xpos = wp.to_torch(d.xpos)
    tb = muscle_tables(h, dev, torch)

    OBS = 3 + 3 + n * 2 + 3 + 3 * len(HOLD)
    P = OBS * HID + HID + HID * ACT_DIM + ACT_DIM

    print('\nTRAIN: ONE limb moves, the others HOLD  (mountain-climber primitive)\n' + '=' * 74)
    print(f'  {pop} bodies in one kernel   policy {OBS} -> {HID} -> {ACT_DIM} = {P} params')
    print(f'  quasi-static: settle into a sprawl, then move {SWING} to a target')
    print(f'  reward: swing reaches target + {len(HOLD)} support contacts stay planted\n')
    print(f"  {'gen':>4}{'best':>8}{'mean':>8}{'reach':>8}{'holdErr':>9}{'bod/s':>7}{'sec':>6}")
    print('  ' + '-' * 52)

    def quat_up(q):
        w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
        return torch.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], 1)

    mu = torch.randn(P, device=dev) * 0.05
    sigma = 0.10
    best_ever, best_theta = -1e9, None
    settle_steps = int(SETTLE / DT); ep_steps = int(EPISODE / DT)
    t_all = time.perf_counter()

    for g in range(gens):
        tg = time.perf_counter()
        half = pop // 2
        eps = torch.randn(half, P, device=dev)
        theta = mu + sigma * torch.cat([eps, -eps])
        i = 0
        W1 = theta[:, i:i + OBS * HID].view(W, OBS, HID); i += OBS * HID
        b1 = theta[:, i:i + HID]; i += HID
        W2 = theta[:, i:i + HID * ACT_DIM].view(W, HID, ACT_DIM); i += HID * ACT_DIM
        b2 = theta[:, i:i + ACT_DIM]

        gen = torch.Generator(device=dev).manual_seed(4242)
        qpos.zero_(); qvel.zero_()
        qpos[:, 2] = 0.55
        qpos[:, 3] = 1.0
        qpos[:, 7:] = torch.randn(W, n, device=dev, generator=gen) * 0.3
        mjw.forward(m, d)
        for _ in range(settle_steps):
            mjw.step(m, d)
        holds = [xpos[:, b].clone() for b in HOLD]
        target = xpos[:, SW].clone()
        target[:, 0] += 0.20; target[:, 2] += 0.15

        reach_sum = torch.zeros(W, device=dev); hold_sum = torch.zeros(W, device=dev); cnt = 0
        for k in range(0, ep_steps, CONTROL_EVERY):
            q = torch.nan_to_num(qpos[:, 7:]); qd = torch.nan_to_num(qvel[:, 6:])
            up = quat_up(torch.nan_to_num(qpos[:, 3:7]))
            swing_err = torch.nan_to_num(target - xpos[:, SW])
            hold_errs = [torch.nan_to_num(xpos[:, b] - holds[hi]) for hi, b in enumerate(HOLD)]
            ob = torch.nan_to_num(torch.cat([up, qvel[:, 3:6], q, qd, swing_err] + hold_errs,
                                            1)).clamp(-20, 20)
            a = 0.5 * (torch.tanh(torch.bmm(torch.tanh(torch.bmm(ob.unsqueeze(1), W1)
                       + b1.unsqueeze(1)), W2) + b2.unsqueeze(1)).squeeze(1) + 1.0)
            ctrl[:] = torch.nan_to_num(muscle_torque_gpu(tb, q, qd, a, torch)).clamp(-400, 400)
            for _ in range(CONTROL_EVERY):
                mjw.step(m, d)
            reach_sum += torch.nan_to_num(torch.linalg.norm(target - xpos[:, SW], dim=1),
                                          nan=1.0).clamp(max=1.0)
            hold_sum += sum(torch.nan_to_num(torch.linalg.norm(xpos[:, b] - holds[hi], dim=1),
                                             nan=0.5).clamp(max=0.5) for hi, b in enumerate(HOLD))
            cnt += 1

        reach_m = reach_sum / max(cnt, 1)
        hold_m = hold_sum / max(cnt, 1) / len(HOLD)
        fit = -reach_m - 2.0 * hold_m
        f = fit.detach().cpu().numpy()
        ranks = np.empty(pop); ranks[np.argsort(f)] = np.arange(pop)
        adv = torch.tensor(ranks / (pop - 1) - 0.5, dtype=torch.float32, device=dev)
        pert = torch.cat([eps, -eps])
        mu = mu + (LR / (pop * sigma)) * (pert.T @ adv)
        bi = int(f.argmax())
        if f.max() > best_ever:
            best_ever = float(f.max()); best_theta = mu.detach().cpu().numpy().copy()
        print(f'  {g:4d}{f.max():8.3f}{f.mean():8.3f}{reach_m[bi].item():8.3f}'
              f'{hold_m[bi].item():9.3f}{W/(time.perf_counter()-tg):7.0f}{time.perf_counter()-tg:6.1f}')

    print('\n  ' + '-' * 52)
    print(f'  total {time.perf_counter()-t_all:.0f}s   best {best_ever:.3f}')
    if best_theta is not None:
        np.save(Path(__file__).resolve().parent / 'transition_ground.npy', best_theta)
        print('  saved transition_ground.npy')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
