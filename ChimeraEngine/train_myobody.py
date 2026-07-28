"""train_myobody.py — PPO teaches the FULL-BODY 290-muscle MyoSuite humanoid to STAND.

myoLegs (80 muscles) was the locomotion subset; this is the whole musculoskeletal human -- legs,
torso, arms, spine, 290 Hill muscles, 944 tendon-wrap surfaces, 52 dof. A body that crawls, climbs,
and holds things needs all of it, which the operator caught: "where's all the other muscles."

    SAME PROVEN RECIPE as the myoLegs stand (keyframe reset, height x uprightness reward, alive
    bonus, early termination, entropy anneal, the learning-based work-gate) -- only the instrument is
    bigger. 290 muscles is a 3.6x larger action space and ~3x heavier to simulate, so it trains
    slower and needs more iterations than legs; the METHOD is unchanged.

    Verified: myobody.xml loads in mujoco 3.10 and batches on mujoco_warp (put_model + step). The
    work-gate's verdict is the LEARNING CURVE (survival), not temperature; time is a readout.

Run:  python ChimeraEngine/train_myobody.py [--envs N] [--iters N] [--smoke]
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

T = 100
CONTROL_EVERY = 20
HID = 256                             # bigger net for the 290-muscle action space
GAMMA = 0.99
LAM = 0.95
CLIP = 0.2
EPOCHS = 5
MINIBATCH = 8192
LR = 3e-4
ENT = 0.004
VCOEF = 0.5
ALIVE_BONUS = 0.2
FALL_FRAC = 0.6                       # fallen when root drops below FALL_FRAC * standing height
EFFORT = 0.01                         # cost of muscle drive: relax what doesn't earn reward (the arms)
STILL = 0.3                           # reward a SETTLED body (low joint velocity) -- process, not a target pose


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
    smoke = '--smoke' in sys.argv
    if smoke:
        envs, iters = 128, 3
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
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=100, njmax=512)   # more muscles/wraps -> more constraints
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    q_key_t = torch.tensor(q_key, dtype=torch.float32, device=dev)

    OBS = 4 + 3 + 3 + nj * 2
    ACT = nu
    ac = build_ac(OBS, ACT, torch)
    opt = torch.optim.Adam(ac.parameters(), lr=LR)

    print(f'\nPPO: the FULL-BODY {nu}-muscle humanoid learns to STAND  ({nj} joints)\n' + '=' * 74)
    print(f'  {W} envs x {T} steps = {W*T} samples/iter   actor-critic {OBS}->{HID}->{ACT}')
    print(f'  reward = height x uprightness + alive; terminate when root < {FALL_Z:.2f} m\n')
    print(f"  {'iter':>4}{'reward/step':>12}{'height':>8}{'upright':>8}{'still':>8}{'surv%':>7}{'sec':>7}")
    print('  ' + '-' * 48)

    def observe():
        quat = torch.nan_to_num(qpos[:, 3:7])
        return torch.nan_to_num(torch.cat([quat, qvel[:, 3:6], qvel[:, 0:3],
                                           qpos[:, 7:], qvel[:, 6:]], 1)).clamp(-20, 20)

    def height_upright():
        h = torch.clamp(torch.nan_to_num(qpos[:, 2]) / STAND_Z, 0.0, 1.0)
        upr = torch.abs((torch.nan_to_num(qpos[:, 3:7]) * quat_key).sum(1))
        return h, torch.clamp(upr, 0.0, 1.0)

    gen = torch.Generator(device=dev).manual_seed(1)
    heat = None if smoke else GPUHeatGate().start()
    t_all = time.perf_counter()
    for it in range(iters):
        ti = time.perf_counter()
        qpos[:] = q_key_t.unsqueeze(0)
        qvel.zero_()
        qpos[:, 7:] += torch.randn(W, nj, device=dev, generator=gen) * 0.03
        qpos[:, 2] += torch.randn(W, device=dev, generator=gen) * 0.01
        mjw.forward(m, d)

        obs_b = torch.zeros(T, W, OBS, device=dev)
        act_b = torch.zeros(T, W, ACT, device=dev)
        lp_b = torch.zeros(T, W, device=dev)
        val_b = torch.zeros(T, W, device=dev)
        rew_b = torch.zeros(T, W, device=dev)
        alive_b = torch.zeros(T, W, device=dev)
        alive = torch.ones(W, device=dev)

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
                h, upr = height_upright()
                # "be still", NOT "match a pose": reward low joint velocity so the body settles and
                # the arms stop flailing -- their resting position EMERGES, it is never commanded.
                still = torch.exp(-STILL * torch.nan_to_num(qvel[:, 6:]).pow(2).mean(1))
                alive = alive * (torch.nan_to_num(qpos[:, 2]) > FALL_Z).float()
                effort = raw.clamp(0.0, 1.0).pow(2).mean(1)
                obs_b[t] = o; act_b[t] = raw; lp_b[t] = lp; val_b[t] = v
                rew_b[t] = (h * upr * (0.5 + 0.5 * still) + ALIVE_BONUS - EFFORT * effort) * alive
                alive_b[t] = alive
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

        h, upr = height_upright()
        still = torch.exp(-STILL * torch.nan_to_num(qvel[:, 6:]).pow(2).mean(1))
        surv = 100.0 * alive_b[-1].mean().item()
        if it == 0:
            init_surv = surv
        final_surv = surv
        print(f'  {it:4d}{rew_b.mean().item():12.4f}{h.mean().item():8.3f}{upr.mean().item():8.3f}'
              f'{still.mean().item():8.3f}{surv:7.1f}{time.perf_counter()-ti:7.1f}')
        if not smoke and (it + 1) % 8 == 0:
            torch.save(ac.state_dict(), HERE / 'myobody_policy.pt')
            np.save(HERE / 'myobody_meta.npy', dict(OBS=OBS, HID=HID, ACT=ACT, STAND_Z=STAND_Z))

    print('\n  ' + '-' * 48)
    print(f'  total {time.perf_counter()-t_all:.0f}s')
    torch.save(ac.state_dict(), HERE / 'myobody_policy.pt')
    np.save(HERE / 'myobody_meta.npy', dict(OBS=OBS, HID=HID, ACT=ACT, STAND_Z=STAND_Z))
    print('  saved myobody_policy.pt')
    if heat is not None:
        heat.enforce(improved=final_surv - init_surv, threshold=10.0, metric='survival%')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
