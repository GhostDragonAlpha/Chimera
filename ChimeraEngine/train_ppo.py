"""train_ppo.py — PPO on the batched GPU sim, against the imitation reward.

The reference-motion reward is correctly shaped (train_imitate: keeps the head up, no jump, no
collapse) but ES cannot optimise 2,564 parameters from a population gradient -- proven by the
pop-128 -> pop-512 sweep that doubled the score yet still peaked and declined. PPO uses the TRUE
policy gradient, backprop through the policy, which is sample-efficient exactly where the ES
estimate is not.

    MODEL-FREE, so the sim stays a black box. During a rollout the policy acts and the sim steps;
    (obs, action, logprob, reward, value) are stored DETACHED. Gradients flow only through the
    actor-critic in the update phase, on that stored data -- so nothing has to differentiate
    through mujoco_warp, and the no-CPU-sync-in-the-rollout rule holds (the only sync is moving the
    finished rollout tensors, which already live on the GPU).

    THE PIECES, standard PPO: a Gaussian actor (mean network + learnable log-std), a critic,
    GAE(gamma, lambda) advantages, a clipped surrogate loss, a value loss, an entropy bonus, and
    several Adam epochs over minibatches of the flattened (T*W) rollout.

    THE MUSCLE IS THE WITNESSED ONE (X6, 2/2). THE REWARD is the validated imitation reward.

Run:  python ChimeraEngine/train_ppo.py [--iters N] [--envs N]
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
from gpu_gate import GPUHeatGate                                             # noqa: E402

DT = 5e-4
CONTROL_EVERY = 20
T = 100                               # control-steps per rollout (2.0 s at 100 Hz)
HID = 64
GAMMA = 0.99
LAM = 0.95
CLIP = 0.2
EPOCHS = 5
MINIBATCH = 4096
LR = 3e-4
ENT = 0.003
VCOEF = 0.5


def build_ac(OBS, torch, dev):
    import torch.nn as nn

    class AC(nn.Module):
        def __init__(self):
            super().__init__()
            self.body = nn.Sequential(nn.Linear(OBS, HID), nn.Tanh(),
                                      nn.Linear(HID, HID), nn.Tanh())
            self.mean = nn.Linear(HID, ACT_DIM)
            self.v = nn.Linear(HID, 1)
            self.log_std = nn.Parameter(torch.full((ACT_DIM,), -0.7))
            for lin in (self.mean, self.v):
                nn.init.orthogonal_(lin.weight, 0.01); nn.init.zeros_(lin.bias)

        def forward(self, o):
            h = self.body(o)
            return self.mean(h), self.log_std.exp(), self.v(h).squeeze(-1)

    return AC().to(dev)


def main() -> int:
    import torch, warp as wp, mujoco, mujoco_warp as mjw
    iters = int(sys.argv[sys.argv.index('--iters') + 1]) if '--iters' in sys.argv else 60
    envs = int(sys.argv[sys.argv.index('--envs') + 1]) if '--envs' in sys.argv else 256
    dev = 'cuda'
    torch.manual_seed(0)

    h = humanoid(); n = h.tree.n
    mjm = mujoco.MjModel.from_xml_string(to_mjcf(h, dt=DT, floor=True))
    mjd = mujoco.MjData(mjm)
    HEAD = mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, 'head')
    mjd.qpos[:] = 0; mjd.qpos[3] = 1.0
    for z in np.linspace(1.15, 0.85, 40):
        mjd.qpos[2] = z; mujoco.mj_forward(mjm, mjd)
        if min(mjd.xpos[i][2] for i in range(1, mjm.nbody)) <= 0.01:
            break
    STAND_Z = float(z) + 0.01

    W = envs
    m = mjw.put_model(mjm)
    # nconmax is PER WORLD (mujoco_warp allocates nconmax*nworld total contacts). A humanoid
    # on a floor plane with self-collision off makes only a few dozen contacts; 64/world is
    # ample and matches the library's own default heuristic (~48). The old `W*8` treated this
    # per-world number as a total, so the pool was 8*W*W -- exactly 2**31 at W=16384, which
    # overflowed warp's int32 array shape. Per-world constant is correct at every population.
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=64)
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    xpos = wp.to_torch(d.xpos)
    tb = muscle_tables(h, dev, torch)
    q_ref = torch.zeros(n, device=dev)

    OBS = 3 + 3 + n * 2
    ac = build_ac(OBS, torch, dev)
    opt = torch.optim.Adam(ac.parameters(), lr=LR)

    print(f'\nPPO: imitate the standing reference\n' + '=' * 74)
    print(f'  {W} envs x {T} steps = {W*T} samples/iter   actor-critic {OBS}->{HID}->{ACT_DIM}')
    print(f'  reward = pose-match x uprightness x root-height (the validated imitation reward)\n')
    print(f"  {'iter':>4}{'reward/step':>12}{'poseMatch':>10}{'value':>8}{'sec':>7}")
    print('  ' + '-' * 46)

    def quat_up(q):
        w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
        return torch.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], 1)

    def observe():
        q = torch.nan_to_num(qpos[:, 7:]); qd = torch.nan_to_num(qvel[:, 6:])
        up = quat_up(torch.nan_to_num(qpos[:, 3:7]))
        return torch.nan_to_num(torch.cat([up, qvel[:, 3:6], q, qd], 1)).clamp(-20, 20)

    def reward():
        pose = torch.exp(-2.0 * torch.nan_to_num(qpos[:, 7:] - q_ref).pow(2).mean(1))
        upr = torch.clamp(quat_up(torch.nan_to_num(qpos[:, 3:7]))[:, 2], 0.0, 1.0)
        hh = torch.clamp(torch.nan_to_num(xpos[:, HEAD, 2], nan=0.0) / 1.55, 0.0, 1.0)
        return pose * upr * hh

    gen = torch.Generator(device=dev).manual_seed(1)
    heat = GPUHeatGate().start()          # the GPU must get HOT or this run does not count
    t_all = time.perf_counter()
    for it in range(iters):
        ti = time.perf_counter()
        # reset all envs to the standing start
        qpos.zero_(); qvel.zero_()
        qpos[:, 2] = STAND_Z; qpos[:, 3] = 1.0
        qpos[:, 7:] = torch.randn(W, n, device=dev, generator=gen) * 0.06
        mjw.forward(m, d)

        obs_b = torch.zeros(T, W, OBS, device=dev)
        act_b = torch.zeros(T, W, ACT_DIM, device=dev)
        lp_b = torch.zeros(T, W, device=dev)
        val_b = torch.zeros(T, W, device=dev)
        rew_b = torch.zeros(T, W, device=dev)

        # ── ROLLOUT (no grad; the sim is a black box) ──
        with torch.no_grad():
            for t in range(T):
                o = observe()
                mean, std, v = ac(o)
                dist = torch.distributions.Normal(mean, std)
                raw = dist.sample()
                lp = dist.log_prob(raw).sum(-1)
                a = raw.clamp(0.0, 1.0)                       # muscle activations in [0,1]
                ctrl[:] = torch.nan_to_num(muscle_torque_gpu(tb, qpos[:, 7:], qvel[:, 6:], a, torch)
                                           ).clamp(-400, 400)
                for _ in range(CONTROL_EVERY):
                    mjw.step(m, d)
                obs_b[t] = o; act_b[t] = raw; lp_b[t] = lp; val_b[t] = v; rew_b[t] = reward()
            _, _, last_v = ac(observe())

        # ── GAE ──
        adv = torch.zeros(T, W, device=dev); gae = torch.zeros(W, device=dev)
        for t in reversed(range(T)):
            nextv = last_v if t == T - 1 else val_b[t + 1]
            delta = rew_b[t] + GAMMA * nextv - val_b[t]
            gae = delta + GAMMA * LAM * gae
            adv[t] = gae
        ret = adv + val_b
        # flatten
        bo = obs_b.reshape(-1, OBS); ba = act_b.reshape(-1, ACT_DIM)
        blp = lp_b.reshape(-1); badv = adv.reshape(-1); bret = ret.reshape(-1)
        badv = (badv - badv.mean()) / (badv.std() + 1e-8)
        N = bo.shape[0]

        # ── PPO UPDATE ──
        for _ in range(EPOCHS):
            idx = torch.randperm(N, device=dev)
            for s in range(0, N, MINIBATCH):
                mb = idx[s:s + MINIBATCH]
                mean, std, v = ac(bo[mb])
                dist = torch.distributions.Normal(mean, std)
                lp = dist.log_prob(ba[mb]).sum(-1)
                ratio = (lp - blp[mb]).exp()
                a_mb = badv[mb]
                s1 = ratio * a_mb
                s2 = torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a_mb
                pol_loss = -torch.min(s1, s2).mean()
                val_loss = (v - bret[mb]).pow(2).mean()
                ent = dist.entropy().sum(-1).mean()
                loss = pol_loss + VCOEF * val_loss - ENT * ent
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(ac.parameters(), 1.0)
                opt.step()

        pm = torch.exp(-2.0 * qpos[:, 7:].pow(2).mean(1)).mean().item()
        print(f'  {it:4d}{rew_b.mean().item():12.4f}{pm:10.3f}{val_b.mean().item():8.3f}'
              f'{time.perf_counter()-ti:7.1f}')

    print('\n  ' + '-' * 46)
    print(f'  total {time.perf_counter()-t_all:.0f}s')
    torch.save(ac.state_dict(), Path(__file__).resolve().parent / 'ppo_policy.pt')
    np.save(Path(__file__).resolve().parent / 'ppo_meta.npy',
            dict(OBS=OBS, HID=HID, STAND_Z=STAND_Z))
    print('  saved ppo_policy.pt')
    heat.enforce()                        # REFUSES (exit 1) if the GPU stayed cold
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
