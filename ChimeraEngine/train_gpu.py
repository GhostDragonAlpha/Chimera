"""train_gpu.py — THE WHOLE POPULATION IN ONE KERNEL (THE_BODY.md §9.6).

The CPU trainer ran 24 genomes sequentially at ~0.57 s each, which is why the population was 24 --
and 2,028 parameters against 24 samples is far below what an evolution strategy needs. That is not
a tuning problem, it is a throughput problem, and this project measured the answer long ago:
mujoco-warp does the whole population in ONE kernel.

    THE ONE RULE (CLAUDE.md, paid for): NOTHING READS BACK FROM THE GPU INSIDE THE ROLLOUT LOOP.
    A previous attempt in this repo did 1,575 CPU<->GPU syncs per batch and ran 300x SLOWER than
    the CPU it was meant to beat. So the policy AND the muscle model both have to live on the GPU
    -- `wp.to_torch` gives zero-copy views of MuJoCo's own qpos/qvel/ctrl arrays, and every step of
    obs -> action -> tau -> ctrl happens in torch on those views without a single transfer.

    THE MUSCLE MODEL IS PORTED, NOT APPROXIMATED. r(q) is a uniformly-sampled table (body.py), so
    interpolation is an index and a lerp -- no searchsorted, no kernel. L(q) comes from the same
    table's cumulative integral, exactly as on the CPU. The Hill force-length curve is one exp().
    What runs here is the same arithmetic mjcf_witness X5 measured agreeing to 4.06x convergence.

    ONE WORLD = ONE (GENOME, TARGET) PAIR. mujoco-warp batches N copies of one MODEL, which is
    exactly right: the body is fixed and only the controller varies. (Morphology is NOT
    GPU-batchable for the same reason -- that stays on the CPU, and it is why the bestiary is a
    different problem.)

Run:  python ChimeraEngine/train_gpu.py [--gens N] [--pop N] [--quick]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from body import ACT_DIM, humanoid                                           # noqa: E402
from mjcf_body import to_mjcf                                                # noqa: E402

DT = 5e-4
CONTROL_EVERY = 20                    # 100 Hz neural drive
EPISODE = 1.0
HID = 24
SWING = 'forearmL'
LR = 0.5
REACH = 0.28


def muscle_tables(h, device, torch):
    """Lift our CPU muscle model onto the GPU: arm table, length table, and the Hill constants."""
    n = h.tree.n
    S = len(next(iter(h.pairs.values())).flexor.arm_q)
    aq = np.zeros((n, S)); ar = np.zeros((n, S)); ac = np.zeros((n, S))
    tmax = np.zeros((n, 2)); rest = np.zeros((n, 2)); width = np.zeros((n, 2))
    for name, pr in h.pairs.items():
        j = h.joint[name]
        f = pr.flexor
        aq[j] = f.arm_q; ar[j] = f.arm_r; ac[j] = f.arm_cum
        for k, msc in enumerate((pr.flexor, pr.extensor)):
            tmax[j, k] = msc.max_tension; rest[j, k] = msc.rest_length; width[j, k] = msc.width
    T = lambda a: torch.tensor(a, dtype=torch.float32, device=device)
    return dict(q0=T(aq[:, 0]), dq=T(aq[:, 1] - aq[:, 0]), S=S,
                r=T(ar), cum=T(ac), L0=T(np.full(n, 0.30 * h.height)),
                tmax=T(tmax), rest=T(rest), width=T(width), n=n)


def muscle_torque_gpu(tb, q, qd, act, torch):
    """tau = T(a, L) * r(q), batched over worlds. Uniform grid, so interp is an index and a lerp."""
    W, n = q.shape
    # NaN DEFEATS clamp AND long(). A world whose sim blew up carries NaN in q; clamp passes NaN
    # straight through, .long() on NaN is undefined, and the resulting garbage index walks off the
    # gather -- which surfaces as a CUDA device-side assert with no line number and no clue.
    # Scrubbing first is not defensive coding, it is the difference between a diverged world
    # scoring badly and the whole batch dying.
    q = torch.nan_to_num(q, nan=0.0, posinf=0.0, neginf=0.0)
    qd = torch.nan_to_num(qd, nan=0.0, posinf=0.0, neginf=0.0)
    x = torch.clamp((q - tb['q0']) / tb['dq'], 0.0, tb['S'] - 1.0001)
    i0 = x.long().clamp(0, tb['S'] - 2); fr = (x - i0.float()).unsqueeze(-1)
    gather = lambda M: torch.stack([M[:, 0], M[:, 1]], -1) if False else None
    r0 = torch.gather(tb['r'].expand(W, -1, -1), 2, i0.unsqueeze(-1)).squeeze(-1)
    r1 = torch.gather(tb['r'].expand(W, -1, -1), 2, (i0 + 1).unsqueeze(-1)).squeeze(-1)
    c0 = torch.gather(tb['cum'].expand(W, -1, -1), 2, i0.unsqueeze(-1)).squeeze(-1)
    c1 = torch.gather(tb['cum'].expand(W, -1, -1), 2, (i0 + 1).unsqueeze(-1)).squeeze(-1)
    f = fr.squeeze(-1)
    r = r0 + (r1 - r0) * f                                    # signed moment arm, flexor sense
    L = tb['L0'] - (c0 + (c1 - c0) * f)                       # L(q) = L0 - integral of r
    e = (L.unsqueeze(-1) / tb['rest'] - 1.0) / tb['width']
    fl = torch.exp(-e * e)                                    # Hill force-length
    a = act.view(W, n, 2).clamp(0.0, 1.0)
    Tn = a * tb['tmax'] * fl
    return (Tn[..., 0] - Tn[..., 1]) * r                      # flexor pulls +r, extensor -r


def main() -> int:
    import torch, warp as wp, mujoco, mujoco_warp as mjw
    quick = '--quick' in sys.argv
    gens = int(sys.argv[sys.argv.index('--gens') + 1]) if '--gens' in sys.argv else (8 if quick else 40)
    pop = int(sys.argv[sys.argv.index('--pop') + 1]) if '--pop' in sys.argv else (64 if quick else 256)
    dev = 'cuda'
    torch.manual_seed(3)

    h = humanoid()
    n = h.tree.n
    # ZERO GRAVITY. This is the FREE-SPACE reach -- the EVA case floating_witness F4 measured --
    # and it is the scope mjcf_witness X5 witnessed. With gravity on and no ground the body simply
    # falls 4.9 m in a second, so the reach error was ~5 m no matter what the muscles did and every
    # score sat on the clamp floor. The task was unmeasurable, not unlearnable.
    mjm = mujoco.MjModel.from_xml_string(to_mjcf(h, dt=DT, gravity=(0.0, 0.0, 0.0)))
    mjd = mujoco.MjData(mjm)
    mujoco.mj_forward(mjm, mjd)

    dirs = np.array([[1, 0, .3], [0, 1, .3], [-.6, .5, .6], [.5, -.8, 0], [.2, .2, -1], [-.7, -.4, .4]], float)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    D = len(dirs)
    W = pop * D                                               # one world per (genome, target)

    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W)
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    tb = muscle_tables(h, dev, torch)

    OBS = 3 + 1 + 3 + n * 2 + 3
    P = OBS * HID + HID + HID * ACT_DIM + ACT_DIM
    B_SWING = mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, SWING)
    B_PELVIS = mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, 'pelvis')
    xpos = wp.to_torch(d.xpos)                      # (worlds, bodies, 3) -- the REAL limb position

    print(f'\nTRAIN ON THE GPU: the whole population in one kernel\n' + '=' * 74)
    print(f'  {pop} genomes x {D} targets = {W} WORLDS stepped simultaneously')
    print(f'  policy {OBS} -> {HID} -> {ACT_DIM} = {P} params   |  {torch.cuda.get_device_name(0)}')
    print(f"\n  {'gen':>4}{'best':>9}{'mean':>9}{'worst':>9}{'evals/s':>10}{'sec':>7}")
    print('  ' + '-' * 48)

    tgt = torch.tensor(np.repeat(dirs[None].repeat(pop, 0).reshape(W, 3), 1, 0),
                       dtype=torch.float32, device=dev) * REACH
    mu = torch.randn(P, device=dev) * 0.05
    sigma, best_ever, best_theta = 0.12, -1e9, None
    n_steps = int(EPISODE / DT)
    t_all = time.perf_counter()

    for g in range(gens):
        tg = time.perf_counter()
        half = pop // 2
        eps = torch.randn(half, P, device=dev)
        theta = (mu + sigma * torch.cat([eps, -eps])).repeat_interleave(D, 0)   # (W, P)
        i = 0
        W1 = theta[:, i:i + OBS * HID].view(W, OBS, HID); i += OBS * HID
        b1 = theta[:, i:i + HID]; i += HID
        W2 = theta[:, i:i + HID * ACT_DIM].view(W, HID, ACT_DIM); i += HID * ACT_DIM
        b2 = theta[:, i:i + ACT_DIM]

        # reset every world; randomise the pose per GENOME-target so all genomes face the same set
        gen = torch.Generator(device=dev).manual_seed(1000 + 0)
        qpos.zero_(); qvel.zero_()
        qpos[:, 3] = 1.0
        qpos[:, 7:] = torch.randn(W, n, device=dev, generator=gen) * 0.25
        qvel[:, 6:] = torch.randn(W, n, device=dev, generator=gen) * 0.20
        mjw.forward(m, d)

        held = torch.zeros(W, device=dev); nheld = 0
        for k in range(0, n_steps, CONTROL_EVERY):
            q = torch.nan_to_num(qpos[:, 7:]); qd = torch.nan_to_num(qvel[:, 6:])
            # BODY-RELATIVE, not world. The planner asks for a contact placed relative to the
            # BODY, so the target has to travel with it -- measuring a falling pelvis against a
            # world-fixed point measures gravity, not control.
            tip = xpos[:, B_SWING] - xpos[:, B_PELVIS]
            err = tgt - tip
            ob = torch.nan_to_num(torch.cat([torch.zeros(W, 3, device=dev),
                            torch.full((W, 1), 9.8, device=dev),
                            qvel[:, 3:6], q, qd, err], 1)).clamp(-50, 50)
            a = 0.5 * (torch.tanh(torch.bmm(torch.tanh(torch.bmm(ob.unsqueeze(1), W1) + b1.unsqueeze(1)),
                                            W2) + b2.unsqueeze(1)).squeeze(1) + 1.0)
            ctrl[:] = torch.nan_to_num(muscle_torque_gpu(tb, q, qd, a, torch)).clamp(-400, 400)
            for _ in range(CONTROL_EVERY):
                mjw.step(m, d)
            if k > n_steps * 0.66:
                held += torch.nan_to_num(torch.linalg.norm(err, dim=1),
                                         nan=5.0, posinf=5.0).clamp(0, 5); nheld += 1

        # THE ONLY SYNC IN THE WHOLE GENERATION -- one read of W floats, after the rollout
        fit_w = (2.0 - 6.0 * (held / max(nheld, 1))).nan_to_num(-10.0).clamp(-10, 10)
        fit = fit_w.view(pop, D).mean(1)                      # TRAIN on the mean over targets
        f = fit.detach().cpu().numpy()

        ranks = np.empty(pop); ranks[np.argsort(f)] = np.arange(pop)
        adv = torch.tensor(ranks / (pop - 1) - 0.5, dtype=torch.float32, device=dev)
        pert = torch.cat([eps, -eps])
        mu = mu + (LR / (pop * sigma)) * (pert.T @ adv)
        if f.max() > best_ever:
            best_ever = float(f.max()); best_theta = (mu.detach().cpu().numpy().copy())
        dt_g = time.perf_counter() - tg
        print(f'  {g:4d}{f.max():9.3f}{f.mean():9.3f}{f.min():9.3f}'
              f'{W / dt_g:10.0f}{dt_g:7.2f}')

    print('\n  ' + '-' * 48)
    print(f'  total {time.perf_counter()-t_all:.0f}s   best {best_ever:.3f}')
    if best_theta is not None:
        np.save(Path(__file__).resolve().parent / 'transition_policy_gpu.npy', best_theta)
        print('  saved transition_policy_gpu.npy')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
