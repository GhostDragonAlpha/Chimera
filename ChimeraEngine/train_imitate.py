"""train_imitate.py — REFERENCE-MOTION IMITATION (DeepMimic's load-bearing idea).

Five sparse-reward tasks did not learn: head height, reach, contact-first standing, the climber.
The common failure was a reward that is sparse in ACTION space -- many muscle patterns give the same
head height, so the gradient the optimiser sees is weak and it drifts.

DeepMimic's insight: imitate a REFERENCE MOTION. The reward becomes "match this target pose, joint
by joint", which is DENSE in exactly the space the muscles control -- every joint that deviates is
penalised immediately, so the gradient points straight at the fix. That is the ingredient the last
five runs lacked, and it is tried here FIRST with the proven ES (not a from-scratch PPO that could
hide its own bugs) to isolate whether the reward was the problem.

    THE REFERENCE. The body is BUILT upright at q = 0 -- neutral joints, standing. So the simplest
    valid reference motion is "hold the standing pose": q_ref = 0, torso vertical. Holding it against
    gravity IS balance; the imitation reward just tells the controller, at every joint, which way is
    back toward standing. A moving reference (a crawl or step cycle) is the same machinery with a
    time-varying q_ref -- this is the still frame of it.

    THE MUSCLE IS THE WITNESSED ONE (X6, 2/2) -- the correct actuator.

Run:  python ChimeraEngine/train_imitate.py [--gens N] [--pop N]
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
EPISODE = 2.0
HID = 32
LR = 0.5


def main() -> int:
    import torch, warp as wp, mujoco, mujoco_warp as mjw
    gens = int(sys.argv[sys.argv.index('--gens') + 1]) if '--gens' in sys.argv else 40
    pop = int(sys.argv[sys.argv.index('--pop') + 1]) if '--pop' in sys.argv else 256
    dev = 'cuda'
    torch.manual_seed(9)

    h = humanoid()
    n = h.tree.n
    mjm = mujoco.MjModel.from_xml_string(to_mjcf(h, dt=DT, floor=True))
    mjd = mujoco.MjData(mjm); mjd.qpos[2] = 1.0; mujoco.mj_forward(mjm, mjd)
    HEAD = mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, 'head')

    W = pop
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=64)   # PER WORLD, not total (W*8 overflows int32 at large W)
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    xpos = wp.to_torch(d.xpos)
    tb = muscle_tables(h, dev, torch)

    q_ref = torch.zeros(n, device=dev)              # THE REFERENCE: neutral standing pose
    # find the pelvis height at which feet rest on the floor, at q_ref, so the start is a real stand
    mjd.qpos[:] = 0; mjd.qpos[3] = 1.0
    for z in np.linspace(1.15, 0.85, 40):
        mjd.qpos[2] = z; mujoco.mj_forward(mjm, mjd)
        if min(mjd.xpos[i][2] for i in range(1, mjm.nbody)) <= 0.01:
            break
    STAND_Z = float(z) + 0.01
    print(f"  reference: q=0 upright, pelvis at {STAND_Z:.3f} m (feet on floor)")

    OBS = 3 + 3 + n * 2                              # up, base angvel, q, qd
    P = OBS * HID + HID + HID * ACT_DIM + ACT_DIM

    print('\nTRAIN: IMITATE THE STANDING REFERENCE  (dense pose reward)\n' + '=' * 74)
    print(f'  {pop} bodies in one kernel   policy {OBS} -> {HID} -> {ACT_DIM} = {P} params')
    print(f'  reward = pose match exp(-|q-qref|) x uprightness -- dense in joint space\n')
    print(f"  {'gen':>4}{'best':>8}{'mean':>8}{'poseMatch':>10}{'headM':>8}{'bod/s':>7}{'sec':>6}")
    print('  ' + '-' * 54)

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
        qpos[:, 2] = STAND_Z
        qpos[:, 3] = 1.0
        qpos[:, 7:] = torch.randn(W, n, device=dev, generator=gen) * 0.06   # small shove to correct
        mjw.forward(m, d)

        pose_sum = torch.zeros(W, device=dev); head_sum = torch.zeros(W, device=dev); cnt = 0
        for k in range(0, n_steps, CONTROL_EVERY):
            q = torch.nan_to_num(qpos[:, 7:]); qd = torch.nan_to_num(qvel[:, 6:])
            up = quat_up(torch.nan_to_num(qpos[:, 3:7]))
            ob = torch.nan_to_num(torch.cat([up, qvel[:, 3:6], q, qd], 1)).clamp(-20, 20)
            a = 0.5 * (torch.tanh(torch.bmm(torch.tanh(torch.bmm(ob.unsqueeze(1), W1)
                       + b1.unsqueeze(1)), W2) + b2.unsqueeze(1)).squeeze(1) + 1.0)
            ctrl[:] = torch.nan_to_num(muscle_torque_gpu(tb, q, qd, a, torch)).clamp(-400, 400)
            for _ in range(CONTROL_EVERY):
                mjw.step(m, d)
            # DENSE IMITATION: pose match x uprightness, both in [0,1], per step
            pose = torch.exp(-2.0 * torch.nan_to_num(qpos[:, 7:] - q_ref).pow(2).mean(1))
            upr = torch.clamp(quat_up(torch.nan_to_num(qpos[:, 3:7]))[:, 2], 0.0, 1.0)
            # HEIGHT is required, or a rigid body that sinks straight down scores pose=1, upr=1 --
            # the hack the first run found (poseMatch 1.0 at headM 0.0). DeepMimic's root term.
            hh = torch.clamp(torch.nan_to_num(xpos[:, HEAD, 2], nan=0.0) / 1.55, 0.0, 1.0)
            pose_sum += pose * upr * hh
            head_sum += torch.nan_to_num(xpos[:, HEAD, 2], nan=0.0).clamp(0, 1.7)
            cnt += 1

        pose_m = pose_sum / max(cnt, 1)
        fit = pose_m
        f = fit.detach().cpu().numpy()
        ranks = np.empty(pop); ranks[np.argsort(f)] = np.arange(pop)
        adv = torch.tensor(ranks / (pop - 1) - 0.5, dtype=torch.float32, device=dev)
        pert = torch.cat([eps, -eps])
        mu = mu + (LR / (pop * sigma)) * (pert.T @ adv)
        bi = int(f.argmax())
        if f.max() > best_ever:
            best_ever = float(f.max()); best_theta = mu.detach().cpu().numpy().copy()
        print(f'  {g:4d}{f.max():8.3f}{f.mean():8.3f}{pose_m[bi].item():10.3f}'
              f'{(head_sum[bi]/max(cnt,1)).item():8.2f}{W/(time.perf_counter()-tg):7.0f}'
              f'{time.perf_counter()-tg:6.1f}')

    print('\n  ' + '-' * 54)
    print(f'  total {time.perf_counter()-t_all:.0f}s   best pose-match {best_ever:.3f} '
          f'(1.0 = held the standing reference perfectly)')
    if best_theta is not None:
        np.save(Path(__file__).resolve().parent / 'imitate_policy.npy', best_theta)
        print('  saved imitate_policy.npy')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
