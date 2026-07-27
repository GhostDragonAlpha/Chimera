"""train_stand.py — THE REAL GOAL: KEEP THE HEAD UP (operator, 2026-07-27).

    "The head and torso find greatest efficiency aligned with gravity... you want the head as high
     as possible at all times. Look at a giraffe."

The reach task had no organizing principle -- a limb touching an arbitrary point serves nothing.
This is the goal a body actually has: hold the head high against gravity, standing on the ground.
Every limb motion is judged only by whether it keeps the head up. Walking, getting up and balance
are all this same objective from different starting poses.

    ON THE GROUND, IN GRAVITY, WITH CONTACT -- all three of which the reach task lacked, and all
    three of which the operator said were missing. The physics is MuJoCo's, which IS the game's
    physics (FastBody). The numpy engine has not been witnessed against MuJoCo's contact solver, so
    this run is honestly scoped as "MuJoCo contact", not "witnessed against our reference".

    REWARD IS HEAD HEIGHT, nothing else invented. Mean head world-z over the episode, so the policy
    has to get the head up AND KEEP it there -- a body that lunges upright and topples scores worse
    than one that holds. No pose reference, no "looks natural" term. Uprightness and coordinated
    limbs are not rewarded; they are what MAXIMISING head height turns out to require.

Run:  python ChimeraEngine/train_stand.py [--gens N] [--pop N]
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

DT = 1e-3
CONTROL_EVERY = 10                    # 100 Hz
EPISODE = 2.0                         # long enough that toppling is punished, not just the lunge
HID = 32
LR = 0.5
STAND_H = 1.65      # a standing head; the reward gains nothing above this


def main() -> int:
    import torch, warp as wp, mujoco, mujoco_warp as mjw
    gens = int(sys.argv[sys.argv.index('--gens') + 1]) if '--gens' in sys.argv else 40
    pop = int(sys.argv[sys.argv.index('--pop') + 1]) if '--pop' in sys.argv else 256
    dev = 'cuda'
    torch.manual_seed(5)

    h = humanoid()
    n = h.tree.n
    mjm = mujoco.MjModel.from_xml_string(to_mjcf(h, dt=DT, floor=True))
    mjd = mujoco.MjData(mjm)
    mjd.qpos[2] = 1.05
    mujoco.mj_forward(mjm, mjd)
    HEAD = mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, 'head')

    W = pop
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=W * 8)
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    xpos = wp.to_torch(d.xpos)
    tb = muscle_tables(h, dev, torch)

    # observation: up-vector (3) + head height (1) + base ang vel (3) + q (18) + qd (18) = 43
    OBS = 3 + 1 + 3 + n * 2
    P = OBS * HID + HID + HID * ACT_DIM + ACT_DIM

    print('\nTRAIN: KEEP THE HEAD UP  (ground + gravity + contact)\n' + '=' * 74)
    print(f'  {pop} bodies stepped in one kernel   policy {OBS} -> {HID} -> {ACT_DIM} = {P} params')
    print(f'  reward = mean head height over {EPISODE}s   |  {torch.cuda.get_device_name(0)}')
    print(f'  uncontrolled baseline: head collapses to ~0.15 m; standing head is ~1.6 m\n')
    print(f"  {'gen':>4}{'best m':>9}{'mean m':>9}{'worst m':>9}{'bodies/s':>10}{'sec':>7}")
    print('  ' + '-' * 52)

    mu = torch.randn(P, device=dev) * 0.05
    sigma = 0.10
    best_ever, best_theta = -1e9, None
    n_steps = int(EPISODE / DT)
    t_all = time.perf_counter()

    def quat_up(q):                                  # world up-vector of the torso, from base quat
        w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
        return torch.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], 1)

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
        qpos[:, 2] = 1.02                            # standing, just above the floor
        qpos[:, 3] = 1.0                             # upright quaternion
        qpos[:, 7:] = torch.randn(W, n, device=dev, generator=gen) * 0.08   # a small shove to react to
        mjw.forward(m, d)

        head_sum = torch.zeros(W, device=dev); cnt = 0
        for k in range(0, n_steps, CONTROL_EVERY):
            q = torch.nan_to_num(qpos[:, 7:]); qd = torch.nan_to_num(qvel[:, 6:])
            up = quat_up(torch.nan_to_num(qpos[:, 3:7]))
            hz = xpos[:, HEAD, 2:3]
            ob = torch.nan_to_num(torch.cat([up, hz, qvel[:, 3:6], q, qd], 1)).clamp(-30, 30)
            a = 0.5 * (torch.tanh(torch.bmm(torch.tanh(torch.bmm(ob.unsqueeze(1), W1)
                       + b1.unsqueeze(1)), W2) + b2.unsqueeze(1)).squeeze(1) + 1.0)
            ctrl[:] = torch.nan_to_num(muscle_torque_gpu(tb, q, qd, a, torch)).clamp(-400, 400)
            for _ in range(CONTROL_EVERY):
                mjw.step(m, d)
            # CAP AT STANDING HEIGHT. Uncapped "head height" is maximised by JUMPING -- the first
            # run launched the body to 6.46 m and out of frame, which is the optimiser auditing the
            # spec exactly as CLAUDE.md warns. A jump earns nothing above the cap, and the crash
            # after it scores LOW, so a jump-and-fall averages worse than steady standing. This is
            # the operator's giraffe point made precise: head high in a SUSTAINABLE posture, not a
            # peak. Feet must also stay near the floor -- a body in the air is not standing.
            hh = torch.nan_to_num(xpos[:, HEAD, 2], nan=0.0).clamp(0, STAND_H)
            airborne = (qpos[:, 2] > 1.15)                 # pelvis launched clear of standing height
            head_sum += torch.where(airborne, torch.zeros_like(hh), hh); cnt += 1

        fit = (head_sum / max(cnt, 1))               # mean head height, metres
        f = fit.detach().cpu().numpy()
        ranks = np.empty(pop); ranks[np.argsort(f)] = np.arange(pop)
        adv = torch.tensor(ranks / (pop - 1) - 0.5, dtype=torch.float32, device=dev)
        pert = torch.cat([eps, -eps])
        mu = mu + (LR / (pop * sigma)) * (pert.T @ adv)
        if f.max() > best_ever:
            best_ever = float(f.max()); best_theta = mu.detach().cpu().numpy().copy()
        print(f'  {g:4d}{f.max():9.3f}{f.mean():9.3f}{f.min():9.3f}'
              f'{W/(time.perf_counter()-tg):10.0f}{time.perf_counter()-tg:7.1f}')

    print('\n  ' + '-' * 52)
    print(f'  total {time.perf_counter()-t_all:.0f}s   best mean head height {best_ever:.3f} m')
    if best_theta is not None:
        np.save(Path(__file__).resolve().parent / 'stand_policy.npy', best_theta)
        print('  saved stand_policy.npy')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
