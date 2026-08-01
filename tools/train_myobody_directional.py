"""train_myobody_directional.py — direction-conditioned fine-tune of the mocap walk policy.

WHY: myobody_walk_mocap_policy.pt walks FORWARD only (the reward's velocity term is a dot with
the spawn heading, and its tracking envelope is the CMU 35_01 forward walk). The measured
directional gaits now exist (research_references/human/mocap_directional_reference.json:
backward + sidestep left/right from CMU 136/141/111/113/076), so the same bounded PPO fine-tune
is rerun with a movement COMMAND in the obs and per-command speed/envelope targets.

WHAT CHANGED vs train_myobody_mocap.py (only these):
  1. OBS += 4: one-hot command over [forward, backward, left, right], sampled per env per
     episode (this trainer resets every env each iteration, so the resample point is the
     iteration reset). Sampling is majority-forward -- P_CMD = [0.5, 1/6, 1/6, 1/6] -- so the
     already-trained forward skill keeps half the gradient signal and does not collapse.
  2. The velocity term projects qvel[0:2] onto the COMMANDED direction (cmd_dir, built by
     rotating the frozen spawn heading head0 by 0/180/+90/-90 deg) and scales by that
     direction's MEASURED target speed: forward 1.285 m/s (mocap_walk_reference.json),
     backward 0.6, left 0.631, right 0.655 (mocap_directional_reference.json). Backward
     motion therefore pays positive, exactly like forward does for the forward command.
  3. The tracking term reads the matching direction's envelopes. Forward/backward use the
     same curve for both legs; a sidestep uses the LEAD envelope for the leg on the side of
     travel and the TRAIL envelope for the crossing leg (command "left" -> left leg leads).
     All four directions are pre-baked into one (4, 101, 6) table REF_ALL and gathered per
     env, so the per-step cost is unchanged.
  4. The phase clock runs at each command's own stride time: forward uses the reference
     stride_time_s (1.127 s); the directional file carries no stride time, so it is derived
     as stride_m / speed_m_s (backward 1.541 s, left 0.913 s, right 0.911 s).
  5. warm-start from output/myobody_walk_mocap_policy.pt with a PARTIAL load: every tensor
     whose shape matches is copied; body.0.weight grew by the 4 command columns, which are
     seeded with ~1e-3 noise (a command the net has never seen must start as a near-no-op).
  6. checkpoint to ChimeraEngine/output/myobody_walk_directional_policy.pt -- a NEW artifact.
     myobody_walk_mocap_policy.pt and myobody_walk_policy.pt are NEVER written (asserted).

UNCHANGED: the curriculum ramp (track term off until iter RAMP_START, then linear over
RAMP_LEN), ALIVE_BONUS, the parking-exploit guard (velocity term x2 weight so it dominates
alive+track), EFFORT, GAE/PPO hyperparameters, and the sagittal angle math -- joint angles
stay in the BODY-FACING frame (head0) for every command, because the envelopes are sagittal
hip/knee/ankle curves; only the velocity term knows about the travel direction.

Run:  C:\\Python314\\python.exe tools/train_myobody_directional.py [--envs 1024] [--seconds 840]
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
REF_FWD = ROOT / 'research_references' / 'human' / 'mocap_walk_reference.json'
REF_DIR = ROOT / 'research_references' / 'human' / 'mocap_directional_reference.json'
OUT_PT = HERE / 'output' / 'myobody_walk_directional_policy.pt'
OUT_META = HERE / 'output' / 'myobody_walk_directional_meta.npy'
# HARD GUARD: this script must never clobber the forward-only policies it warm-starts from.
assert OUT_PT.name not in ('myobody_walk_mocap_policy.pt', 'myobody_walk_policy.pt')

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
ALIVE_BONUS = 0.8        # same damping as the mocap trainer: survival must out-pay a sprint
FALL_FRAC = 0.6
EFFORT = 0.01
W_TRACK = 1.0                     # weight of the mocap envelope matching term
SIGMA_DEG = 15.0                  # tolerance band, degrees
# THE CURRICULUM, inherited from the mocap trainer: W_TRACK at full weight from iter 0 pulled
# the policy off its feet. OFF for RAMP_START iters, then linear over RAMP_LEN.
RAMP_START = 8
RAMP_LEN = 16

# THE COMMAND ENCODING: one-hot over 4 directions, in this fixed order. Majority-forward
# sampling keeps the trained skill dominant; the other three split the remainder evenly.
CMDS = ('forward', 'backward', 'left', 'right')
CMD_DIM = len(CMDS)
P_CMD = (0.5, 1.0 / 6.0, 1.0 / 6.0, 1.0 / 6.0)

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


def close_curve(curve):
    """The forward envelopes are 101 points (closed loop); the directional ones are 100.
    Append the first sample so one (4, 101, ...) table serves all four directions."""
    return list(curve) + [curve[0]] if len(curve) == 100 else list(curve)


def build_ref_table(ref_fwd, ref_dir, dev, torch):
    """(4, 101, 6) reference envelopes, column order [hip_r, hip_l, knee_r, knee_l,
    ankle_r, ankle_l] -- matching joint_angles(). LEAD/TRAIL mapping for sidesteps: the
    lead leg is the one on the side of travel, so 'left' puts the trail curve on the
    RIGHT column and the lead curve on the LEFT column (and vice versa for 'right')."""
    np_ = np

    def both_legs(env):
        return np_.stack([env['hip'], env['hip'], env['knee'], env['knee'],
                          env['ankle'], env['ankle']], 1)          # (101, 6)

    def split_legs(env, lead_side):
        lead = {j: close_curve(env['lead'][j]) for j in ('hip', 'knee', 'ankle')}
        trail = {j: close_curve(env['trail'][j]) for j in ('hip', 'knee', 'ankle')}
        r, l = (trail, lead) if lead_side == 'l' else (lead, trail)
        return np_.stack([r['hip'], l['hip'], r['knee'], l['knee'],
                          r['ankle'], l['ankle']], 1)

    fwd = {j: close_curve(ref_fwd['envelopes_deg'][j]['mean']) for j in ('hip', 'knee', 'ankle')}
    bwd = {j: close_curve(ref_dir['backward']['envelopes_deg'][j]) for j in ('hip', 'knee', 'ankle')}
    table = np_.stack([both_legs(fwd), both_legs(bwd),
                       split_legs(ref_dir['left']['envelopes_deg'], 'l'),
                       split_legs(ref_dir['right']['envelopes_deg'], 'r')])
    return torch.tensor(table, dtype=torch.float32, device=dev)


def main() -> int:
    import torch
    import warp as wp
    import mujoco
    import mujoco_warp as mjw

    envs = int(sys.argv[sys.argv.index('--envs') + 1]) if '--envs' in sys.argv else 1024
    budget = float(sys.argv[sys.argv.index('--seconds') + 1]) if '--seconds' in sys.argv else 840.0
    init = Path(sys.argv[sys.argv.index('--init') + 1]) if '--init' in sys.argv \
        else HERE / 'output' / 'myobody_walk_mocap_policy.pt'
    out = Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else OUT_PT
    assert out.name not in ('myobody_walk_mocap_policy.pt', 'myobody_walk_policy.pt'), \
        f'refusing to overwrite the forward-only policy: {out}'
    dev = 'cuda'
    torch.manual_seed(0)

    ref_fwd = json.loads(REF_FWD.read_text())
    ref_dir = json.loads(REF_DIR.read_text())
    # PER-COMMAND targets, all measured: speeds straight from the two reference files;
    # stride time for the phase clock (forward carries it, the rest are stride_m / speed_m_s).
    speed_m_s = torch.tensor([float(ref_fwd['speed_m_s'])] +
                             [float(ref_dir[c]['speed_m_s']) for c in CMDS[1:]],
                             dtype=torch.float32, device=dev)
    stride_s = torch.tensor([float(ref_fwd['stride_time_s'])] +
                            [float(ref_dir[c]['stride_m']) / float(ref_dir[c]['speed_m_s'])
                             for c in CMDS[1:]], dtype=torch.float32, device=dev)
    ref_all = build_ref_table(ref_fwd, ref_dir, dev, torch)
    p_cmd = torch.tensor(P_CMD, dtype=torch.float32, device=dev)

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

    OBS = 4 + 3 + 3 + nj * 2 + CMD_DIM              # old obs + one-hot command
    ACT = nu
    ac = build_ac(OBS, ACT, torch)

    # PARTIAL WARM-START: the obs grew by CMD_DIM, so body.0.weight cannot load wholesale.
    # Copy every tensor that shape-matches; for body.0.weight keep the trained columns and
    # seed the 4 new command columns with ~1e-3 noise (near-no-op for unseen inputs).
    sd_new = ac.state_dict()
    sd_old = torch.load(init, map_location=dev)
    loaded, grown, skipped = [], [], []
    for k, v in sd_old.items():
        if k in sd_new and sd_new[k].shape == v.shape:
            sd_new[k] = v
            loaded.append(k)
        elif k == 'body.0.weight' and v.shape[1] + CMD_DIM == sd_new[k].shape[1]:
            noise = torch.randn(sd_new[k][:, -CMD_DIM:].shape, device=dev) * 1e-3
            sd_new[k] = torch.cat([v, noise], 1)
            grown.append(f'{k} {tuple(v.shape)} -> {tuple(sd_new[k].shape)} '
                         f'(new {CMD_DIM} command cols ~N(0, 1e-3))')
        else:
            skipped.append(f'{k} {tuple(v.shape)} vs {tuple(sd_new[k].shape)}')
    ac.load_state_dict(sd_new)
    print(f'  warm-start from {init}: {len(loaded)} tensors copied verbatim')
    for g in grown:
        print(f'    GROWN {g}')
    for s in skipped:
        print(f'    SKIPPED {s}')
    opt = torch.optim.Adam(ac.parameters(), lr=LR)

    print(f'\nPPO FINE-TUNE: mocap policy + DIRECTIONAL commands '
          f'(one-hot {CMDS}, P={P_CMD}; speeds_m_s={[round(float(s), 3) for s in speed_m_s]}, '
          f'track w={W_TRACK} ramped in after iter {RAMP_START}, sigma={SIGMA_DEG} deg)\n' + '=' * 74)
    print(f'  {W} envs x {T} steps   wall-clock budget {budget:.0f}s   -> {out}')
    print(f"  {'iter':>4}{'reward':>9}{'cmdv':>7}{'track':>8}{'surv%':>7}{'sec':>7}{'total':>8}"
          f"   per-cmd mean speed along command, m/s")

    def quat_fwd(q):
        w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
        return torch.stack([1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)], 1)

    def heading_xy(q):
        f = quat_fwd(torch.nan_to_num(q))[:, :2]
        return f / (f.norm(dim=1, keepdim=True) + 1e-6)

    def observe(cmd1h):
        base = torch.nan_to_num(torch.cat([torch.nan_to_num(qpos[:, 3:7]), qvel[:, 3:6],
                                           qvel[:, 0:3], qpos[:, 7:], qvel[:, 6:]], 1)).clamp(-20, 20)
        return torch.cat([base, cmd1h], 1)          # command rides unclamped, it is already 0/1

    def seg_angle(v, head):
        """v: (W,3) segment vector; head: (W,2) travel direction. Degrees from straight-down."""
        vf = (v[:, :2] * head).sum(-1)
        vu = v[:, 2]
        return torch.rad2deg(torch.atan2(vf, -vu))

    def joint_angles(head):
        """(W,6): hip/knee/ankle x r/l, same vector math as the evaluators. Sagittal angles
        live in the BODY-FACING frame (head0) for every command -- only the velocity term
        uses the commanded travel direction."""
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
        return torch.stack(hips + knees + ankles, 1)          # [hip_r,hip_l,knee_r,knee_l,ankle_r,ankle_l]

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
        # THE EPISODE'S COMMAND: sampled per env at reset, one-hot into the obs, and turned
        # into a world-frame travel direction by rotating the frozen spawn heading.
        # left = rotate head0 +90 deg in the xy plane -> (-y, x); right = (y, -x).
        cmd = torch.multinomial(p_cmd.expand(W, CMD_DIM), 1, generator=gen).squeeze(1)
        cmd1h = torch.nn.functional.one_hot(cmd, CMD_DIM).float()
        cand = torch.stack([head0, -head0,
                            torch.stack([-head0[:, 1], head0[:, 0]], 1),
                            torch.stack([head0[:, 1], -head0[:, 0]], 1)], 1)   # (W,4,2)
        cmd_dir = cand[torch.arange(W, device=dev), cmd]
        tgt_speed = speed_m_s[cmd]                  # (W,) per-env target, m/s
        stride_env = stride_s[cmd]                  # (W,) per-env stride clock, s
        phase0 = torch.rand(W, device=dev, generator=gen)   # desynchronized clocks across envs

        obs_b = torch.zeros(T, W, OBS, device=dev)
        act_b = torch.zeros(T, W, ACT, device=dev)
        lp_b = torch.zeros(T, W, device=dev)
        val_b = torch.zeros(T, W, device=dev)
        rew_b = torch.zeros(T, W, device=dev)
        alive_b = torch.zeros(T, W, device=dev)
        alive = torch.ones(W, device=dev)
        fwd_sum = torch.zeros(W, device=dev)        # projected speed along cmd_dir, m/s
        track_sum = torch.zeros(W, device=dev)
        dt_ctrl = mjm.opt.timestep * CONTROL_EVERY

        with torch.no_grad():
            for t in range(T):
                o = observe(cmd1h)
                mean, std, v = ac(o)
                dist = torch.distributions.Normal(mean, std)
                raw = dist.sample()
                lp = dist.log_prob(raw).sum(-1)
                ctrl[:] = raw.clamp(0.0, 1.0)
                for _ in range(CONTROL_EVERY):
                    mjw.step(m, d)
                # velocity projected on the COMMANDED direction, scaled by its measured
                # target speed: backward motion pays positive under a backward command.
                fwd = (torch.nan_to_num(qvel[:, 0:2]) * cmd_dir).sum(1)
                vtrack = torch.clamp(fwd / tgt_speed, -0.5, 1.5)
                # THE PARKING EXPLOIT still applies per direction: alive+track alone pays for
                # standing still with good joint shapes, so the velocity term keeps its x2
                # weight (1.2 vs 0.5 * w_track) and must dominate the reward.
                upr = torch.clamp(torch.abs((torch.nan_to_num(qpos[:, 3:7]) * quat_key).sum(1)), 0, 1)
                alive = alive * (torch.nan_to_num(qpos[:, 2]) > FALL_Z).float()
                effort = raw.clamp(0.0, 1.0).pow(2).mean(1)
                phase01 = (phase0 + t * dt_ctrl / stride_env) % 1.0
                ang = joint_angles(head0)
                idx = (phase01 * 100).long().clamp(0, 100)
                ra = ref_all[cmd, idx]                      # (W,6) this command's envelopes
                terr = (ang - ra) / SIGMA_DEG
                track = torch.exp(-terr.pow(2)).mean(1)
                obs_b[t] = o; act_b[t] = raw; lp_b[t] = lp; val_b[t] = v
                w_track = W_TRACK * min(1.0, max(0.0, (it - RAMP_START) / RAMP_LEN))
                rew_b[t] = (1.2 * vtrack * upr + ALIVE_BONUS - EFFORT * effort + 0.5 * w_track * track) * alive
                alive_b[t] = alive
                fwd_sum += fwd * alive
                track_sum += track * alive
            _, _, last_v = ac(observe(cmd1h))

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

        mean_cmdv = (fwd_sum / T).mean().item()             # m/s along the commanded direction
        mean_track = (track_sum / T).mean().item()
        surv = 100.0 * alive_b[-1].mean().item()
        per_cmd = []
        for ci in range(CMD_DIM):
            msk = cmd == ci
            if msk.any():
                per_cmd.append(f'{CMDS[ci][:4]}={(fwd_sum[msk] / T).mean().item():.3f}(n={int(msk.sum())})')
        el = time.perf_counter() - t_all
        print(f'  {it:4d}{rew_b.mean().item():9.4f}{mean_cmdv:7.3f}{mean_track:8.3f}{surv:7.1f}'
              f'{time.perf_counter()-ti:7.1f}{el:8.0f}   ' + ' '.join(per_cmd), flush=True)
        torch.save(ac.state_dict(), out)
        np.save(OUT_META, dict(OBS=OBS, HID=HID, ACT=ACT, CMD_DIM=CMD_DIM, CMDS=CMDS,
                               OBS_LAYOUT='[quat(4), angvel(3), linvel(3), qpos(nj), qvel(nj), '
                                          'cmd_onehot(4: forward,backward,left,right)]',
                               STAND_Z=STAND_Z,
                               NOTE='direction-conditioned fine-tune from myobody_walk_mocap_policy.pt; '
                                    'see tools/train_myobody_directional.py'))
        it += 1

    print(f'\n  BOUND REACHED: {it} iterations in {time.perf_counter()-t_all:.0f}s')
    print(f'  saved {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
