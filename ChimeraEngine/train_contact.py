"""train_contact.py — CONTACT-FIRST STANDING (THE_BODY.md §4, operator 2026-07-27).

The head-height reward taught the body to JUMP: told to maximise head height, the literal optimum
is a rocket, and no cap fully closed that hole. The fix is not another reward tweak -- it is the
contact-first architecture. The planner supplies FOOTHOLDS; the controller is trained only to hold
them while keeping the body up. A jump breaks every contact, so the exploit dies by construction
rather than by penalty.

    THE PLANNER'S ROLE, honestly scoped. `planner.py` (7/7 witnessed) decides WHERE contacts go and
    validates a stance against six measured limits -- friction cone, support polygon, reach. For a
    standing stance its answer is "feet on fixed footholds under the body, COM between them", and
    that is what this trainer encodes as the GPU target. I do NOT call the Python planner inside the
    rollout -- 256 worlds x 200 steps would be 50,000 CPU calls per generation and would break the
    no-sync rule this project paid 300x for. The planner defines the target; the GPU realises it.
    The full planner still runs at plan-time to pick the NEXT foothold for a step; standing is the
    degenerate case where the plan does not change.

    WHY THIS IS DENSE WHERE HEAD-HEIGHT WAS SPARSE. "Keep the head high" gives one scalar that a
    jump maxes out. "Keep each foot on its foothold" gives a gradient every single step the foot
    drifts, on every limb -- and it is unspoofable by jumping, because leaving the ground IS the
    failure the term measures.

Run:  python ChimeraEngine/train_contact.py [--gens N] [--pop N]
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
CONTROL_EVERY = 10
EPISODE = 2.0
HID = 32
LR = 0.5
STAND_H = 1.65


def main() -> int:
    import torch, warp as wp, mujoco, mujoco_warp as mjw
    gens = int(sys.argv[sys.argv.index('--gens') + 1]) if '--gens' in sys.argv else 40
    pop = int(sys.argv[sys.argv.index('--pop') + 1]) if '--pop' in sys.argv else 256
    dev = 'cuda'
    torch.manual_seed(6)

    h = humanoid()
    n = h.tree.n
    mjm = mujoco.MjModel.from_xml_string(to_mjcf(h, dt=DT, floor=True))
    mjd = mujoco.MjData(mjm)
    mjd.qpos[2] = 1.02
    mujoco.mj_forward(mjm, mjd)
    HEAD = mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, 'head')
    FL = mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, 'footL')
    FR = mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, 'footR')

    W = pop
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=W * 8)
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    xpos = wp.to_torch(d.xpos)
    tb = muscle_tables(h, dev, torch)

    # obs: up(3) + head_z(1) + base angvel(3) + q(18) + qd(18) + footL err(3) + footR err(3) = 49
    OBS = 3 + 1 + 3 + n * 2 + 6
    P = OBS * HID + HID + HID * ACT_DIM + ACT_DIM

    print('\nTRAIN: CONTACT-FIRST STANDING  (planner footholds + head up)\n' + '=' * 74)
    print(f'  {pop} bodies in one kernel   policy {OBS} -> {HID} -> {ACT_DIM} = {P} params')
    print(f'  reward = head height (capped) MINUS foot drift from the planned footholds')
    print(f'  a jump lifts the feet -> foot drift explodes -> the exploit cannot pay\n')
    print(f"  {'gen':>4}{'best':>8}{'mean':>8}{'headM':>8}{'footErr':>9}{'bod/s':>8}{'sec':>6}")
    print('  ' + '-' * 52)

    def quat_up(q):
        w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
        return torch.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], 1)

    mu = torch.randn(P, device=dev) * 0.05
    sigma = 0.10
    best_ever, best_theta = -1e9, None
    n_steps = int(EPISODE / DT)
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
        qpos[:, 2] = 1.02
        qpos[:, 3] = 1.0
        qpos[:, 7:] = torch.randn(W, n, device=dev, generator=gen) * 0.08
        mjw.forward(m, d)
        # THE FOOTHOLDS: where the feet START are where the planner says they must STAY for this
        # stance. Fixed in the world; the controller's whole job is to keep them here.
        fhL = xpos[:, FL].clone()
        fhR = xpos[:, FR].clone()

        head_sum = torch.zeros(W, device=dev); foot_sum = torch.zeros(W, device=dev); cnt = 0
        for k in range(0, n_steps, CONTROL_EVERY):
            q = torch.nan_to_num(qpos[:, 7:]); qd = torch.nan_to_num(qvel[:, 6:])
            up = quat_up(torch.nan_to_num(qpos[:, 3:7]))
            eL = torch.nan_to_num(xpos[:, FL] - fhL); eR = torch.nan_to_num(xpos[:, FR] - fhR)
            ob = torch.nan_to_num(torch.cat([up, xpos[:, HEAD, 2:3], qvel[:, 3:6], q, qd, eL, eR],
                                            1)).clamp(-30, 30)
            a = 0.5 * (torch.tanh(torch.bmm(torch.tanh(torch.bmm(ob.unsqueeze(1), W1)
                       + b1.unsqueeze(1)), W2) + b2.unsqueeze(1)).squeeze(1) + 1.0)
            ctrl[:] = torch.nan_to_num(muscle_torque_gpu(tb, q, qd, a, torch)).clamp(-400, 400)
            for _ in range(CONTROL_EVERY):
                mjw.step(m, d)
            head_sum += torch.nan_to_num(xpos[:, HEAD, 2], nan=0.0).clamp(0, STAND_H)
            foot_sum += (torch.linalg.norm(torch.nan_to_num(xpos[:, FL] - fhL), dim=1)
                         + torch.linalg.norm(torch.nan_to_num(xpos[:, FR] - fhR), dim=1))
            cnt += 1

        head_m = head_sum / max(cnt, 1)
        foot_m = foot_sum / max(cnt, 1)
        fit = head_m - 3.0 * foot_m                  # head up, feet planted
        f = fit.detach().cpu().numpy()
        ranks = np.empty(pop); ranks[np.argsort(f)] = np.arange(pop)
        adv = torch.tensor(ranks / (pop - 1) - 0.5, dtype=torch.float32, device=dev)
        pert = torch.cat([eps, -eps])
        mu = mu + (LR / (pop * sigma)) * (pert.T @ adv)
        bi = int(f.argmax())
        if f.max() > best_ever:
            best_ever = float(f.max()); best_theta = mu.detach().cpu().numpy().copy()
        print(f'  {g:4d}{f.max():8.3f}{f.mean():8.3f}{head_m[bi].item():8.2f}'
              f'{foot_m[bi].item():9.3f}{W/(time.perf_counter()-tg):8.0f}{time.perf_counter()-tg:6.1f}')

    print('\n  ' + '-' * 52)
    print(f'  total {time.perf_counter()-t_all:.0f}s   best {best_ever:.3f}')
    if best_theta is not None:
        np.save(Path(__file__).resolve().parent / 'contact_policy.npy', best_theta)
        print('  saved contact_policy.npy')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
