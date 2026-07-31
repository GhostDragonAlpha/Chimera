"""train_myobody_mocap.py — BOUNDED fine-tune of the myobody walk policy with a mocap-tracking reward.

WHY: the shipped myobody_walk_policy.pt is an iter-24 checkpoint whose own training log ended at 0%
survival; measured (tools/policy_gait_eval.py, worst-of-5) it falls at 1.2-1.7 s with periodicity
0.34-0.51. The gap against the CMU 35_01 walk reference is large, so the operator's rule fires:
close it, in a bounded way.

WHAT CHANGED vs the recovered train_myobody_walk.py (only these):
  1. warm-start from myobody_walk_policy.pt (not the stand policy),
  2. + mocap envelope tracking: per control step, hip/knee/ankle sagittal angles (SAME vector math
     as tools/mocap_gait.py and tools/policy_gait_eval.py) are compared against the reference
     envelopes (mocap_walk_reference.json) at an open-loop phase clock running at the reference
     stride rate (2*pi / 1.127 s). Reward += W_TRACK * mean_joints exp(-(err/SIGMA)^2).
  3. bounded: --seconds wall-clock budget (default 840 s), fewer envs for more iters/min,
     checkpoint to ChimeraEngine/output/myobody_walk_mocap_policy.pt (an OUTPUT artifact;
     ChimeraEngine state files are not touched).

Run:  C:\\Python314\\python.exe tools/train_myobody_mocap.py [--envs 1024] [--seconds 840]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'ChimeraEngine'
MYOBODY = ROOT / 'external' / 'myo_sim' / 'body' / 'myobody.xml'
REF = ROOT / 'research_references' / 'human' / 'mocap_walk_reference.json'
OUT_PT = HERE / 'output' / 'myobody_walk_mocap_policy.pt'
OUT_META = HERE / 'output' / 'myobody_walk_mocap_meta.npy'

T = 150
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
ALIVE_BONUS = 0.8        # round 5: survival must out-pay a 2-second sprint (measured: round 4
                         # charged and crashed at ~2 s on every seed -- fwd 1.2, alive 0.8 is the
                         # pendulum's damping, not a new guess)
FALL_FRAC = 0.6
EFFORT = 0.01
TARGET_SPEED = None                   # None -> read from the mocap reference (1.285 m/s)
W_TRACK = 1.0                     # weight of the mocap envelope matching term
SIGMA_DEG = 15.0                  # tolerance band, degrees
# THE CURRICULUM, learned from a dead run: W_TRACK at full weight from iter 0 pulled the stand
# policy off its feet (survival 68.8% -> 0.4% in 4 iters). The track term is OFF for the first
# RAMP_START iters while survival stabilises, then ramps in linearly over RAMP_LEN.
RAMP_START = 8
RAMP_LEN = 16

BODIES = {'hip_r': 'femur_r', 'knee_r': 'tibia_r', 'ankle_r': 'talus_r', 'toe_r': 'toes_r',
          'hip_l': 'femur_l', 'knee_l': 'tibia_l', 'ankle_l': 'talus_l', 'toe_l': 'toes_l',
          'pelvis': 'pelvis', 'trunk': 'torso'}


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

        def forward(self, o):
            h = self.body(o)
            return self.mean(h), self.log_std.exp(), self.v(h).squeeze(-1)

    return AC().to('cuda')


def main() -> int:
    import torch
    import warp as wp
    import mujoco
    import mujoco_warp as mjw

    envs = int(sys.argv[sys.argv.index('--envs') + 1]) if '--envs' in sys.argv else 1024
    budget = float(sys.argv[sys.argv.index('--seconds') + 1]) if '--seconds' in sys.argv else 840.0
    init = Path(sys.argv[sys.argv.index('--init') + 1]) if '--init' in sys.argv \
        else HERE / 'myobody_walk_policy.pt'
    dev = 'cuda'
    torch.manual_seed(0)

    ref = json.loads(REF.read_text())
    stride_s = float(ref['stride_time_s'])
    omega = 2.0 * np.pi / stride_s
    target_speed = float(ref['speed_m_s']) if TARGET_SPEED is None else TARGET_SPEED
    env_ref = {j: torch.tensor(np.array(ref['envelopes_deg'][j]['mean'], dtype=np.float32),
                               device=dev) for j in ('hip', 'knee', 'ankle')}

    mjm = mujoco.MjModel.from_xml_path(str(MYOBODY))
    mjd = mujoco.MjData(mjm)
    nq, nv, nu = mjm.nq, mjm.nv, mjm.nu
    nj = nq - 7
    q_key = mjm.key_qpos[0].copy()
    quat_key = torch.tensor(q_key[3:7], dtype=torch.float32, device=dev)
    STAND_Z = float(q_key[2])
    FALL_Z = FALL_FRAC * STAND_Z
    body_id = {role: mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, n) for role, n in BODIES.items()}

    W = envs
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=100, njmax=512)
    qpos = wp.to_torch(d.qpos)
    qvel = wp.to_torch(d.qvel)
    ctrl = wp.to_torch(d.ctrl)
    xpos = wp.to_torch(d.xpos)                      # (W, nbody, 3)
    q_key_t = torch.tensor(q_key, dtype=torch.float32, device=dev)

    OBS = 4 + 3 + 3 + nj * 2
    ACT = nu
    ac = build_ac(OBS, ACT, torch)
    ac.load_state_dict(torch.load(init, map_location=dev))
    print(f'  warm-started from {init}')
    opt = torch.optim.Adam(ac.parameters(), lr=LR)

    print(f'\nPPO FINE-TUNE: walk policy + MOCAP ENVELOPE tracking '
          f'(w={W_TRACK} ramped in after iter {RAMP_START}, sigma={SIGMA_DEG} deg, '
          f'clock {omega:.2f} rad/s, target {target_speed:.2f} m/s)\n' + '=' * 74)
    print(f'  {W} envs x {T} steps   wall-clock budget {budget:.0f}s   -> {OUT_PT}')
    print(f"  {'iter':>4}{'reward':>9}{'fwd':>7}{'track':>8}{'surv%':>7}{'sec':>7}{'total':>8}")

    def quat_fwd(q):
        w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
        return torch.stack([1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)], 1)

    def heading_xy(q):
        f = quat_fwd(torch.nan_to_num(q))[:, :2]
        return f / (f.norm(dim=1, keepdim=True) + 1e-6)

    def observe():
        return torch.nan_to_num(torch.cat([torch.nan_to_num(qpos[:, 3:7]), qvel[:, 3:6],
                                           qvel[:, 0:3], qpos[:, 7:], qvel[:, 6:]], 1)).clamp(-20, 20)

    def seg_angle(v, head):
        """v: (W,3) segment vector; head: (W,2) travel direction. Degrees from straight-down."""
        vf = (v[:, :2] * head).sum(-1)
        vu = v[:, 2]
        return torch.rad2deg(torch.atan2(vf, -vu))

    def joint_angles(head):
        """(W,6): hip/knee/ankle x r/l, same vector math as the evaluators."""
        p = {role: xpos[:, b, :] for role, b in body_id.items()}
        trunk = p['trunk'] - p['pelvis']
        th_trunk = seg_angle(-trunk, head)
        hips, knees, ankles = [], [], []
        for s in ('r', 'l'):
            thigh = p[f'knee_{s}'] - p[f'hip_{s}']
            shank = p[f'ankle_{s}'] - p[f'knee_{s}']
            foot = p[f'toe_{s}'] - p[f'ankle_{s}']
            th_thigh = seg_angle(thigh, head)
            th_shank = seg_angle(shank, head)
            flen = foot.norm(dim=-1).clamp_min(1e-9)
            foot_pitch = torch.rad2deg(torch.asin((foot[:, 2] / flen).clamp(-1, 1)))
            hips.append(th_thigh - th_trunk)
            knees.append(th_thigh - th_shank)
            ankles.append(foot_pitch - th_shank)
        return torch.stack(hips + knees + ankles, 1)          # matches ref_angles order

    def ref_angles(phase01):
        """(W,6) reference envelope values at cycle phase 0..1."""
        idx = (phase01 * 100).long().clamp(0, 100)
        r = torch.stack([env_ref['hip'][idx], env_ref['knee'][idx], env_ref['ankle'][idx]], 1)
        return r.repeat_interleave(2, dim=1)                # hip_r,hip_l? -> order: build (W,3)->(W,6)

    gen = torch.Generator(device=dev).manual_seed(1)
    t_all = time.perf_counter()
    it = 0
    while time.perf_counter() - t_all < budget:
        ti = time.perf_counter()
        qpos[:] = q_key_t.unsqueeze(0)
        qvel.zero_()
        qpos[:, 7:] += torch.randn(W, nj, device=dev, generator=gen) * 0.03
        mjw.forward(m, d)
        head0 = heading_xy(qpos[:, 3:7])
        start_xy = qpos[:, 0:2].clone()
        phase0 = torch.rand(W, device=dev, generator=gen)   # desynchronized clocks across envs

        obs_b = torch.zeros(T, W, OBS, device=dev)
        act_b = torch.zeros(T, W, ACT, device=dev)
        lp_b = torch.zeros(T, W, device=dev)
        val_b = torch.zeros(T, W, device=dev)
        rew_b = torch.zeros(T, W, device=dev)
        alive_b = torch.zeros(T, W, device=dev)
        alive = torch.ones(W, device=dev)
        fwd_sum = torch.zeros(W, device=dev)
        track_sum = torch.zeros(W, device=dev)
        dt_ctrl = mjm.opt.timestep * CONTROL_EVERY

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
                vtrack = torch.clamp(fwd / target_speed, -0.5, 1.5)
                # THE PARKING EXPLOIT, measured: alive+track alone pays 0.71 for standing still
                # with good joint shapes (round 3: 90% survival, 0.07 fwd). The forward term must
                # dominate the reward or the optimiser parks -- x2, measured from that audit.
                upr = torch.clamp(torch.abs((torch.nan_to_num(qpos[:, 3:7]) * quat_key).sum(1)), 0, 1)
                alive = alive * (torch.nan_to_num(qpos[:, 2]) > FALL_Z).float()
                effort = raw.clamp(0.0, 1.0).pow(2).mean(1)
                phase01 = (phase0 + t * dt_ctrl * omega / (2 * np.pi)) % 1.0
                ang = joint_angles(head0)
                ra = ref_angles(phase01)
                terr = (ang - ra) / SIGMA_DEG
                track = torch.exp(-terr.pow(2)).mean(1)
                obs_b[t] = o; act_b[t] = raw; lp_b[t] = lp; val_b[t] = v
                w_track = W_TRACK * min(1.0, max(0.0, (it - RAMP_START) / RAMP_LEN))
                rew_b[t] = (1.2 * vtrack * upr + ALIVE_BONUS - EFFORT * effort + 0.5 * w_track * track) * alive
                alive_b[t] = alive
                fwd_sum += fwd * alive
                track_sum += track * alive
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
        ent_coef = ENT * max(0.0, 1.0 - it / 30.0)

        for _ in range(EPOCHS):
            idxp = torch.randperm(N, device=dev)
            for s in range(0, N, MINIBATCH):
                mb = idxp[s:s + MINIBATCH]
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

        mean_fwd = (fwd_sum / T).mean().item()
        mean_track = (track_sum / T).mean().item()
        surv = 100.0 * alive_b[-1].mean().item()
        el = time.perf_counter() - t_all
        print(f'  {it:4d}{rew_b.mean().item():9.4f}{mean_fwd:7.3f}{mean_track:8.3f}{surv:7.1f}'
              f'{time.perf_counter()-ti:7.1f}{el:8.0f}', flush=True)
        torch.save(ac.state_dict(), OUT_PT)
        np.save(OUT_META, dict(OBS=OBS, HID=HID, ACT=ACT, STAND_Z=STAND_Z,
                               NOTE='fine-tuned from myobody_walk_policy.pt with mocap envelope '
                                    'tracking reward; see tools/train_myobody_mocap.py'))
        it += 1

    print(f'\n  BOUND REACHED: {it} iterations in {time.perf_counter()-t_all:.0f}s')
    print(f'  saved {OUT_PT}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
