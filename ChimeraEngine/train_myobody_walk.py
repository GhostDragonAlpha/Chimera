"""train_myobody_walk.py — PPO teaches the FULL-BODY 290-muscle humanoid to WALK.

Warm-started from the full-body STAND (balance first, then gait). Isaac-Gym-style VELOCITY TRACKING,
process-not-position: reward the OUTCOME (move forward at a target speed while staying upright), never
a target gait -- the stride pattern and the arm swing EMERGE. No reference motion needed; it is also
the task reward AMP later adds a style reward onto.

Run:  python ChimeraEngine/train_myobody_walk.py [--envs N] [--iters N] [--speed 1.0] [--no-resume]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gpu_gate import GPUHeatGate                                             # noqa: E402

MYOBODY = HERE.parent / 'vendor' / 'myo_sim' / 'body' / 'myobody.xml'

T = 150                               # control-steps per rollout (3.0 s -> several strides)
CONTROL_EVERY = 20
HID = 256
GAMMA = 0.99
LAM = 0.95
CLIP = 0.2
EPOCHS = 5
MINIBATCH = 8192
LR = 3e-4
ENT = 0.004
VCOEF = 0.5
ALIVE_BONUS = 0.4                     # staying up must BEAT a doomed forward lunge, or it dives & falls
FALL_FRAC = 0.6
EFFORT = 0.01                         # relax wasted drive (arms) -- but legs are free to step
TARGET_SPEED = 1.0
FWD_LOCAL = np.array([1.0, 0.0, 0.0])  # body local +X as forward; VERIFY on run 1 (flip if it walks backward)


def build_ac(OBS, ACT, torch):
    import torch.nn as nn

    class AC(nn.Module):
        def __init__(self):
            super().__init__()
            self.body = nn.Sequential(nn.Linear(OBS, HID), nn.Tanh(),
                                      nn.Linear(HID, HID), nn.Tanh())
            self.mean = nn.Linear(HID, ACT)
            self.v = nn.Linear(HID, 1)
            self.log_std = nn.Parameter(torch.full((ACT,), -0.7))
            for lin in (self.mean, self.v):
                nn.init.orthogonal_(lin.weight, 0.01); nn.init.zeros_(lin.bias)

        def forward(self, o):
            h = self.body(o)
            return self.mean(h), self.log_std.exp(), self.v(h).squeeze(-1)

    return AC().to('cuda')


def main() -> int:
    import torch, warp as wp, mujoco, mujoco_warp as mjw
    iters = int(sys.argv[sys.argv.index('--iters') + 1]) if '--iters' in sys.argv else 60
    envs = int(sys.argv[sys.argv.index('--envs') + 1]) if '--envs' in sys.argv else 4096
    tgt = float(sys.argv[sys.argv.index('--speed') + 1]) if '--speed' in sys.argv else TARGET_SPEED
    resume = '--no-resume' not in sys.argv
    smoke = '--smoke' in sys.argv
    if smoke:
        envs, iters, resume = 128, 3, False
    dev = 'cuda'
    torch.manual_seed(0)

    mjm = mujoco.MjModel.from_xml_path(str(MYOBODY))
    mjd = mujoco.MjData(mjm)
    nq, nv, nu = mjm.nq, mjm.nv, mjm.nu
    nj = nq - 7
    q_key = mjm.key_qpos[0].copy()
    quat_key = torch.tensor(q_key[3:7], dtype=torch.float32, device=dev)
    STAND_Z = float(q_key[2])
    FALL_Z = FALL_FRAC * STAND_Z

    W = envs
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=100, njmax=512)
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    q_key_t = torch.tensor(q_key, dtype=torch.float32, device=dev)

    OBS = 4 + 3 + 3 + nj * 2
    ACT = nu
    ac = build_ac(OBS, ACT, torch)
    if resume and (HERE / 'myobody_policy.pt').exists():
        ac.load_state_dict(torch.load(HERE / 'myobody_policy.pt', map_location=dev))
        print('  warm-started from the full-body STAND policy (balance first, then gait)')
    opt = torch.optim.Adam(ac.parameters(), lr=LR)

    print(f'\nPPO: the FULL-BODY {nu}-muscle humanoid learns to WALK at {tgt:.1f} m/s\n' + '=' * 74)
    print(f'  {W} envs x {T} steps = {W*T} samples/iter   reward = speed-track x upright + alive')
    print(f'  terminate when root < {FALL_Z:.2f} m; entropy annealed for a deterministic gait\n')
    print(f"  {'iter':>4}{'reward/step':>12}{'fwd m/s':>9}{'dist m':>8}{'surv%':>7}{'sec':>7}")
    print('  ' + '-' * 50)

    def quat_fwd(q):
        w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
        return torch.stack([1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)], 1)

    def heading_xy(q):
        f = quat_fwd(torch.nan_to_num(q))[:, :2]
        return f / (f.norm(dim=1, keepdim=True) + 1e-6)

    def observe():
        return torch.nan_to_num(torch.cat([torch.nan_to_num(qpos[:, 3:7]), qvel[:, 3:6], qvel[:, 0:3],
                                           qpos[:, 7:], qvel[:, 6:]], 1)).clamp(-20, 20)

    gen = torch.Generator(device=dev).manual_seed(1)
    heat = None if smoke else GPUHeatGate().start()
    t_all = time.perf_counter()
    for it in range(iters):
        ti = time.perf_counter()
        qpos[:] = q_key_t.unsqueeze(0)
        qvel.zero_()
        qpos[:, 7:] += torch.randn(W, nj, device=dev, generator=gen) * 0.03
        mjw.forward(m, d)
        head0 = heading_xy(qpos[:, 3:7])
        start_xy = qpos[:, 0:2].clone()

        obs_b = torch.zeros(T, W, OBS, device=dev)
        act_b = torch.zeros(T, W, ACT, device=dev)
        lp_b = torch.zeros(T, W, device=dev)
        val_b = torch.zeros(T, W, device=dev)
        rew_b = torch.zeros(T, W, device=dev)
        alive_b = torch.zeros(T, W, device=dev)
        alive = torch.ones(W, device=dev)
        fwd_sum = torch.zeros(W, device=dev)

        with torch.no_grad():
            for t in range(T):
                o = observe()
                mean, std, v = ac(o)
                dist = torch.distributions.Normal(mean, std)
                raw = dist.sample()
                lp = dist.log_prob(raw).sum(-1)
                ctrl[:] = raw.clamp(0.0, 1.0)
                for _ in range(CONTROL_EVERY):
                    mjw.step(m, d)
                fwd = (torch.nan_to_num(qvel[:, 0:2]) * head0).sum(1)
                vtrack = torch.clamp(fwd / tgt, -0.5, 1.0)
                upr = torch.clamp(torch.abs((torch.nan_to_num(qpos[:, 3:7]) * quat_key).sum(1)), 0, 1)
                alive = alive * (torch.nan_to_num(qpos[:, 2]) > FALL_Z).float()
                effort = raw.clamp(0.0, 1.0).pow(2).mean(1)
                obs_b[t] = o; act_b[t] = raw; lp_b[t] = lp; val_b[t] = v
                rew_b[t] = (vtrack * upr + ALIVE_BONUS - EFFORT * effort) * alive
                alive_b[t] = alive
                fwd_sum += fwd * alive
            _, _, last_v = ac(observe())

        adv = torch.zeros(T, W, device=dev); gae = torch.zeros(W, device=dev)
        for t in reversed(range(T)):
            nextv = last_v if t == T - 1 else val_b[t + 1]
            mask = alive_b[t]
            delta = rew_b[t] + GAMMA * nextv * mask - val_b[t]
            gae = delta + GAMMA * LAM * mask * gae
            adv[t] = gae
        ret = adv + val_b
        bo = obs_b.reshape(-1, OBS); ba = act_b.reshape(-1, ACT)
        blp = lp_b.reshape(-1); badv = adv.reshape(-1); bret = ret.reshape(-1)
        badv = (badv - badv.mean()) / (badv.std() + 1e-8)
        N = bo.shape[0]
        ent_coef = ENT * max(0.0, 1.0 - it / max(1, iters - 1))

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
                loss = pol_loss + VCOEF * val_loss - ent_coef * ent
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(ac.parameters(), 1.0)
                opt.step()

        dist_m = (((qpos[:, 0:2] - start_xy) * head0).sum(1) * alive).mean().item()
        mean_fwd = (fwd_sum / T).mean().item()
        surv = 100.0 * alive_b[-1].mean().item()
        if it == 0:
            init_dist = dist_m
        final_dist = dist_m
        print(f'  {it:4d}{rew_b.mean().item():12.4f}{mean_fwd:9.3f}{dist_m:8.2f}{surv:7.1f}'
              f'{time.perf_counter()-ti:7.1f}')
        if not smoke and (it + 1) % 8 == 0:
            torch.save(ac.state_dict(), HERE / 'myobody_walk_policy.pt')
            np.save(HERE / 'myobody_walk_meta.npy', dict(OBS=OBS, HID=HID, ACT=ACT, STAND_Z=STAND_Z))

    print('\n  ' + '-' * 50)
    print(f'  total {time.perf_counter()-t_all:.0f}s')
    torch.save(ac.state_dict(), HERE / 'myobody_walk_policy.pt')
    np.save(HERE / 'myobody_walk_meta.npy', dict(OBS=OBS, HID=HID, ACT=ACT, STAND_Z=STAND_Z))
    print('  saved myobody_walk_policy.pt')
    if heat is not None:
        heat.enforce(improved=final_dist - init_dist, threshold=1.0, metric='forward distance (m)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
