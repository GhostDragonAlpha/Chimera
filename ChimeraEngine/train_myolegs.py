"""train_myolegs.py — PPO teaches MyoSuite's 80-muscle myoLegs to STAND, on the GPU.

The hand-built 2-muscle-per-joint body could not stand at any reflex gain (render_ppo --passive:
head 1.56 -> 0.15 m, worse when stiffer). The operator's diagnosis was right: standing needs the
FULL musculature -- biarticular muscles that couple joints, redundancy for an all-directions
stiffness field, the postural chain -- which a single antagonist pair cannot have. So we adopt
MyoSuite's validated myoLegs: 80 Hill muscles, 80 tendons, 324 anatomical wrap surfaces, a floating
pelvis, and a shipped standing keyframe. It loads in our mujoco 3.10 AND batches on mujoco_warp, so
the GPU stack, the 54 C heat gate and PPO all transfer unchanged.

    NATIVE MUSCLES. The policy outputs 80 activations in [0,1] straight into d.ctrl; mujoco_warp
    computes tendon paths, moment arms and Hill forces on the GPU. We delete our own muscle math and
    inherit a validated one -- and the no-CPU-sync-in-the-rollout rule still holds.

    THE TASK is DeepMimic-style: hold the standing keyframe. reward = height x uprightness, an alive
    bonus, early termination the instant the pelvis drops -- the body cannot bank a graceful fall.

    THE GPU MUST GET HOT (>=54 C) or the run is refused: the operator's un-fakeable measure.

Run:  python ChimeraEngine/train_myolegs.py [--envs N] [--iters N] [--smoke]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gpu_gate import GPUHeatGate                                             # noqa: E402

MYOLEGS = HERE.parent / 'vendor' / 'myo_sim' / 'leg' / 'myolegs.xml'

T = 100                               # control-steps per rollout
CONTROL_EVERY = 20                    # sim steps per control step (myoLegs dt = 1e-3 -> 2.0 s episode)
HID = 128
GAMMA = 0.99
LAM = 0.95
CLIP = 0.2
EPOCHS = 5
MINIBATCH = 8192
LR = 3e-4
ENT = 0.004
VCOEF = 0.5
ALIVE_BONUS = 0.2                     # reward per living control-step
FALL_Z = 0.55                         # pelvis below this height (m) => fallen; that world terminates
EFFORT = 0.002                        # small penalty on mean squared activation (energy / anti-thrash)


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
    envs = int(sys.argv[sys.argv.index('--envs') + 1]) if '--envs' in sys.argv else 8192
    smoke = '--smoke' in sys.argv
    if smoke:
        envs, iters = 256, 3
    dev = 'cuda'
    torch.manual_seed(0)

    mjm = mujoco.MjModel.from_xml_path(str(MYOLEGS))
    mjd = mujoco.MjData(mjm)
    nq, nv, nu = mjm.nq, mjm.nv, mjm.nu
    nj = nq - 7                                        # joint dofs (exclude the free root)
    q_key = mjm.key_qpos[0].copy()                     # the shipped standing keyframe
    quat_key = torch.tensor(q_key[3:7], dtype=torch.float32, device=dev)
    STAND_Z = float(q_key[2])

    W = envs
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=64, njmax=256)   # myoLegs logs ~198 constraint rows
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    q_key_t = torch.tensor(q_key, dtype=torch.float32, device=dev)

    OBS = 4 + 3 + 3 + nj * 2                           # root quat, root angvel, root linvel, q, qd
    ACT = nu                                           # 80 muscle activations
    ac = build_ac(OBS, ACT, torch)
    opt = torch.optim.Adam(ac.parameters(), lr=LR)

    print(f'\nPPO: myoLegs learns to STAND  ({nu} muscles, {nj} joints)\n' + '=' * 74)
    print(f'  {W} envs x {T} steps = {W*T} samples/iter   actor-critic {OBS}->{HID}->{ACT}')
    print(f'  reward = height x uprightness + alive bonus; terminate when pelvis < {FALL_Z} m\n')
    print(f"  {'iter':>4}{'reward/step':>12}{'height':>8}{'upright':>8}{'surv%':>7}{'sec':>7}")
    print('  ' + '-' * 48)

    def observe():
        quat = torch.nan_to_num(qpos[:, 3:7])
        return torch.nan_to_num(torch.cat([quat, qvel[:, 3:6], qvel[:, 0:3],
                                           qpos[:, 7:], qvel[:, 6:]], 1)).clamp(-20, 20)

    def height_upright():
        h = torch.clamp(torch.nan_to_num(qpos[:, 2]) / STAND_Z, 0.0, 1.0)
        upr = torch.abs((torch.nan_to_num(qpos[:, 3:7]) * quat_key).sum(1))   # |dot(q, q_key)|
        return h, torch.clamp(upr, 0.0, 1.0)

    gen = torch.Generator(device=dev).manual_seed(1)
    heat = None if smoke else GPUHeatGate().start()
    t_all = time.perf_counter()
    for it in range(iters):
        ti = time.perf_counter()
        qpos[:] = q_key_t.unsqueeze(0)                # reset every world to the standing keyframe
        qvel.zero_()
        qpos[:, 7:] += torch.randn(W, nj, device=dev, generator=gen) * 0.03   # small pose noise
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
                ctrl[:] = raw.clamp(0.0, 1.0)         # 80 muscle activations, native actuators
                for _ in range(CONTROL_EVERY):
                    mjw.step(m, d)
                h, upr = height_upright()
                alive = alive * (torch.nan_to_num(qpos[:, 2]) > FALL_Z).float()
                effort = raw.clamp(0.0, 1.0).pow(2).mean(1)
                obs_b[t] = o; act_b[t] = raw; lp_b[t] = lp; val_b[t] = v
                rew_b[t] = (h * upr + ALIVE_BONUS - EFFORT * effort) * alive
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
        # ANNEAL the entropy bonus to 0 over the run: early iters explore (need noise to find the
        # stand), late iters converge so the log_std shrinks and the MEAN action itself stands --
        # a clean deterministic controller instead of one that only holds up under sampling.
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
        surv = 100.0 * alive_b[-1].mean().item()
        if it == 0:
            init_surv = surv
        final_surv = surv
        print(f'  {it:4d}{rew_b.mean().item():12.4f}{h.mean().item():8.3f}{upr.mean().item():8.3f}'
              f'{surv:7.1f}{time.perf_counter()-ti:7.1f}')
        # CHECKPOINT every 8 iters so the idle CPU can render progress WHILE the GPU keeps training
        if not smoke and (it + 1) % 8 == 0:
            torch.save(ac.state_dict(), HERE / 'myolegs_policy.pt')
            np.save(HERE / 'myolegs_meta.npy', dict(OBS=OBS, HID=HID, ACT=ACT, STAND_Z=STAND_Z))

    print('\n  ' + '-' * 48)
    print(f'  total {time.perf_counter()-t_all:.0f}s')
    torch.save(ac.state_dict(), HERE / 'myolegs_policy.pt')
    np.save(HERE / 'myolegs_meta.npy', dict(OBS=OBS, HID=HID, ACT=ACT, STAND_Z=STAND_Z))
    print('  saved myolegs_policy.pt')
    if heat is not None:
        # the work-gate's verdict is the LEARNING CURVE (survival start -> end), not temperature
        heat.enforce(improved=final_surv - init_surv, threshold=10.0, metric='survival%')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
