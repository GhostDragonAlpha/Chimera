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
    """Lift the muscle model onto the GPU. PER-MUSCLE tables (flexor AND extensor), because the two
    have OPPOSITE length curves -- the bug X6 caught was using the flexor's length for both, which
    put every extensor's force-length factor at the wrong length (219 N.m off at rest)."""
    n = h.tree.n
    S = len(next(iter(h.pairs.values())).flexor.arm_q)
    aq = np.zeros((n, S))
    ar = np.zeros((n, 2, S)); ac = np.zeros((n, 2, S))       # [joint, muscle, sample]
    tmax = np.zeros((n, 2)); rest = np.zeros((n, 2)); width = np.zeros((n, 2))
    vmax = np.zeros((n, 2)); L0 = np.zeros((n, 2))
    for name, pr in h.pairs.items():
        j = h.joint[name]
        aq[j] = pr.flexor.arm_q                              # same sample grid for both
        for k, msc in enumerate((pr.flexor, pr.extensor)):
            ar[j, k] = msc.arm_r; ac[j, k] = msc.arm_cum     # each muscle's OWN arm and integral
            tmax[j, k] = msc.max_tension; rest[j, k] = msc.rest_length
            width[j, k] = msc.width; vmax[j, k] = msc.vmax; L0[j, k] = msc.arm_L0
    T = lambda a: torch.tensor(a, dtype=torch.float32, device=device)
    return dict(q0=T(aq[:, 0]), dq=T(aq[:, 1] - aq[:, 0]), S=S,
                r=T(ar), cum=T(ac), L0=T(L0), tmax=T(tmax), rest=T(rest),
                width=T(width), vmax=T(vmax), n=n)


def _muscle_rL(tb, q, torch):
    """Interpolate each muscle's OWN moment arm r(q) and length L(q). (W,n,2) each. Extracted from
    muscle_torque_gpu UNCHANGED so the stretch reflex reuses the exact same interpolation the torque
    uses -- one code path, and the X6 witness that covers the torque covers this too."""
    W, n = q.shape
    q = torch.nan_to_num(q)
    x = torch.clamp((q - tb['q0']) / tb['dq'], 0.0, tb['S'] - 1.0001)
    i0 = x.long().clamp(0, tb['S'] - 2)
    f = (x - i0.float()).unsqueeze(-1)                       # (W, n, 1)

    def gather_ms(tab, idx):                                 # tab (n,2,S), idx (W,n) -> (W,n,2)
        te = tab.unsqueeze(0).expand(W, -1, -1, -1)
        ii = idx.unsqueeze(-1).unsqueeze(-1).expand(W, n, 2, 1)
        return torch.gather(te, 3, ii).squeeze(-1)

    r0 = gather_ms(tb['r'], i0); r1 = gather_ms(tb['r'], i0 + 1)
    c0 = gather_ms(tb['cum'], i0); c1 = gather_ms(tb['cum'], i0 + 1)
    r = r0 + (r1 - r0) * f                                   # (W, n, 2) each muscle's own arm
    L = tb['L0'].unsqueeze(0) - (c0 + (c1 - c0) * f)         # (W, n, 2) each muscle's own length
    return r, L


def reflex_activation(tb, q, qd, q_ref, torch, kp=5.0, kd=0.4, cap=0.6):
    """SPINAL STRETCH REFLEX (myotatic) -- the biological PD, and the 'hold the leg rigid' mechanism.

    A muscle stretched past the length it has in the reference pose, OR lengthening, reflexively
    contracts to resist the stretch -- exactly the knee-jerk loop, sensed by the muscle spindle
    (length + rate). It is RESTORING by construction: of an antagonist pair, only the STRETCHED
    muscle fires, so a knee beginning to buckle drives its EXTENSOR (not its flexor) and the buckle
    is opposed. This is what a spinal cord does; it is not a robotics position servo bolted on top.

    Returns extra activation in [0, cap] per muscle (W, n, 2), added to the policy's command. The
    policy then learns ON a spinally-stabilized body instead of having to invent damping from raw
    open-loop activation -- the missing ingredient the SOTA supplies with a PD controller.
    """
    W, n = q.shape
    r, L = _muscle_rL(tb, q, torch)
    qr = q_ref.unsqueeze(0).expand(W, n) if q_ref.dim() == 1 else q_ref
    _, L_ref = _muscle_rL(tb, qr, torch)
    rest = torch.where(tb['rest'] > 0.0, tb['rest'], torch.ones_like(tb['rest']))
    stretch = (L - L_ref) / rest                            # >0 : longer than at the reference pose
    rate = (-(r * qd.unsqueeze(-1))) / (tb['vmax'] * rest)  # dL/dt normalized (lengthening = +)
    return torch.clamp(kp * torch.clamp(stretch, min=0.0)
                       + kd * torch.clamp(rate, min=0.0), 0.0, cap)


def muscle_torque_gpu(tb, q, qd, act, torch, q_ref=None, reflex=(5.0, 0.4, 0.6)):
    """tau = sum over the joint's two muscles of T(a, L, v) * r(q), batched over worlds.

    Each muscle uses its OWN arm and length table (X6 fix), and the Hill force-velocity term the
    first port dropped is restored. Witnessed against the CPU reference by muscle_witness (X6).

    With `q_ref` given, the spinal stretch reflex is ADDED to `act` before the force is computed
    (reflex=(kp, kd, cap)); with q_ref=None this is byte-identical to the X6-witnessed path, so the
    witness still holds and the reflex is strictly opt-in.
    """
    W, n = q.shape
    qd = torch.nan_to_num(qd)
    r, L = _muscle_rL(tb, q, torch)
    # GUARD rest <= 0 exactly as the CPU force_length/force_velocity do: return 1.0. Several leg
    # muscles have negative rest_length (L0 = 0.30*height is smaller than the moment-arm integral),
    # and the CPU DISABLES both curves there. Without this guard the GPU computed a bogus factor --
    # the 107 N.m residual X6 still saw after the per-muscle-table fix.
    active = tb['rest'] > 0.0
    e = (L / torch.where(active, tb['rest'], torch.ones_like(tb['rest'])) - 1.0) / tb['width']
    fl = torch.where(active, torch.exp(-e * e), torch.ones_like(e))
    v = r * qd.unsqueeze(-1)
    vn = torch.clamp(v / (tb['vmax'] * torch.where(active, tb['rest'], torch.ones_like(tb['rest']))),
                     -5.0, 5.0)
    # EACH branch uses vn clamped to ITS OWN domain, so no denominator can hit the singularity that
    # torch.where would otherwise evaluate in the unused branch (vn=0.25 -> 1-4vn=0 -> NaN, which
    # poisoned the whole batch -> every world scored 0).
    vp = torch.clamp(vn, min=0.0); vm = torch.clamp(vn, max=0.0)
    fv_pos = torch.clamp((1.0 - vp) / (1.0 + 4.0 * vp), min=0.0)
    fv_neg = torch.clamp(1.5 - 0.5 * (1.0 + vm) / (1.0 - 4.0 * vm), max=1.5)
    fv = torch.where(active, torch.where(vn >= 0.0, fv_pos, fv_neg), torch.ones_like(vn))
    a = act.view(W, n, 2).clamp(0.0, 1.0)
    if q_ref is not None:                                    # add the spinal stretch reflex
        a = torch.clamp(a + reflex_activation(tb, q, qd, q_ref, torch, *reflex), 0.0, 1.0)
    Tn = a * tb['tmax'] * fl * fv
    return (Tn * r).sum(-1)                                  # each muscle's tension times its arm


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

    OBS = 3 + 1 + 3 + n * 2 + 3 + 3   # + tip velocity toward target (the braking signal)
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
            if k == 0:
                prev_tip = tip.clone()
            tipvel = (tip - prev_tip) / (DT * CONTROL_EVERY)   # THE ARRESTING SIGNAL: how fast the
            prev_tip = tip.clone()                             # limb is moving, so it can brake
            ob = torch.nan_to_num(torch.cat([torch.zeros(W, 3, device=dev),
                            torch.full((W, 1), 9.8, device=dev),
                            qvel[:, 3:6], q, qd, err, tipvel], 1)).clamp(-50, 50)
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
        np.save(Path(__file__).resolve().parent / 'transition_policy_vel.npy', best_theta)
        print('  saved transition_policy_gpu.npy')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
