"""train_myobody_gait.py — a real GAIT, not travel: capture-point foot placement + contact sensing.

The gait witness convicted the previous walk: **periodicity 0.24 -- "thrashing that happens to
travel"** -- airborne 15% (a walk is NEVER airborne), support_min 0, wildly asymmetric (toe_R duty
0.78 vs toe_L 0.25, heels never landing), falling at 1.1-1.4 s. It was a controlled topple over a
dragging toe. Two things were missing, and the witness named them.

    1. THE BODY WAS BLIND TO ITS OWN FEET. The observation had no contact, so the policy could not
       know stance from swing -- it had no idea which membrane (STAND / STEP) it was in. Contact is
       now observed, via the geometric proxy CALIBRATED against MuJoCo's own contact list to
       **99% agreement** (gait_myobody.py): the lowest point of each foot's collision geoms, honouring
       capsule/ellipsoid shape and orientation. It needs no contact readback, so it costs ZERO CPU
       syncs in a batched GPU rollout.

    2. NOTHING SAID WHERE TO PLANT. The fix is Hof's **capture point / extrapolated CoM**:

           XcoM = com_xy + com_velocity_xy / w0,     w0 = sqrt(g / L)

       To not fall, plant the foot where your momentum is carrying you. One term encodes BOTH
       failures: reward `exp(-k * distance from XcoM to the nearest PLANTED foot)`, which is 0 when
       airborne (no planted foot) and 1 when planted right at the capture point. Always-supported and
       correct-placement, in a single number.

    AND IT IS GRAVITY-ADAPTIVE FOR FREE. w0 = sqrt(g/L): on the Moon g is 1/6, so w0 shrinks ~2.4x,
    the foot plants ~2.4x further ahead and the pendulum swings slower -- the long floaty Moon stride
    EMERGES from the formula. One cited rule walks on every world. (docs/WALKING_MECHANICS.md)

    PROCESS, NOT POSITION: nothing here commands a gait, a stride length or a pose. It commands
    "go forward, stay up, and plant where your momentum takes you" -- to satisfy that while always
    supported, the body has no choice but to ALTERNATE feet. The cycle must emerge; we never script it.

Run:  python ChimeraEngine/train_myobody_gait.py [--envs N] [--iters N] [--speed 0.8] [--smoke]
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

T = 150
CONTROL_EVERY = 20
HID = 256
GAMMA, LAM, CLIP = 0.99, 0.95, 0.2
EPOCHS, MINIBATCH, LR = 5, 8192, 3e-4
ENT, VCOEF = 0.004, 0.5
ALIVE_BONUS = 0.4
# "ALIVE" MUST MEAN STANDING. At 0.6 the alive line sat at 0.59 m while the standing keyframe is
# 0.98 m -- a body folded into a crouch kept collecting ALIVE_BONUS every step, so the cheapest way
# to score was SINK AND STOP MOVING. Measured live: the synergy run's survival climbed 16% -> 48%
# while its distance FELL 0.44 -> 0.20 m. That is the satisficer, not a gait.
# Sized from measurement, not taste: 12 seeds of the trained stand land at 0.87-1.03 m (collapses at
# 0.20-0.21), and human walking dips the CoM only ~4 cm. 0.8 * 0.98 = 0.78 m keeps every real stand
# and every normal gait dip, and excludes the crouch.
FALL_FRAC = 0.8
EFFORT = 0.01
TARGET_SPEED = 0.8
CAPTURE = 0.8                         # weight of the capture-point term (support + placement in one)
CAP_K = 3.0                           # exp(-CAP_K * metres) -- ~0.05 at 1 m off the capture point
CONTACT_Z = 0.002                     # calibrated threshold (gait_myobody.py swept it: 99% agreement)
LINK_BODIES = ['calcn_l', 'toes_l', 'calcn_r', 'toes_r']    # heel_L, toe_L, heel_R, toe_R


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


def warm_start_from_stand(ac, path, OBS_new, torch, dev):
    """Load the STAND policy into the wider network: the observation grew by the new contact/XcoM
    inputs, so layer 1 takes the old columns from the stand and ZEROS the new ones -- the body keeps
    its balance on day one and learns what the new senses mean from there."""
    if not path.exists():
        return False
    sd = torch.load(path, map_location=dev)
    w = sd.get('body.0.weight')
    if w is None:
        return False
    own = ac.state_dict()
    old_obs = w.shape[1]
    if old_obs > OBS_new:
        return False
    neww = own['body.0.weight'].clone(); neww.zero_()
    neww[:, :old_obs] = w
    sd = dict(sd); sd['body.0.weight'] = neww
    ac.load_state_dict(sd, strict=True)
    print(f'  warm-started from the STAND policy (obs {old_obs} -> {OBS_new}, new senses zeroed)')
    return True


def foot_geom_tables(mjm, mujoco, torch, dev):
    """Per-link collision-geom indices + the shape constants the low-point formula needs."""
    idx, is_cap, s0, s1, s3 = [], [], [], [], []
    per_link = []
    for bname in LINK_BODIES:
        gl = []
        for gi in range(mjm.ngeom):
            g = mjm.geom(gi)
            if g.contype[0] == 0 and g.conaffinity[0] == 0:
                continue
            if mjm.body(g.bodyid[0]).name == bname:
                gl.append(gi)
        per_link.append(gl)
    flat = [gi for gl in per_link for gi in gl]
    for gi in flat:
        g = mjm.geom(gi); s = np.asarray(g.size, dtype=np.float32)
        cap = int(g.type[0]) == int(mujoco.mjtGeom.mjGEOM_CAPSULE)
        is_cap.append(cap); s0.append(s[0]); s1.append(s[1]); s3.append(s[:3])
    T_ = lambda a, dt=torch.float32: torch.tensor(np.asarray(a), dtype=dt, device=dev)
    # slice boundaries so each link can take a min over its own geoms
    bounds, o = [], 0
    for gl in per_link:
        bounds.append((o, o + len(gl))); o += len(gl)
    return (T_(flat, torch.long), T_(is_cap, torch.bool), T_(s0), T_(s1), T_(np.array(s3)), bounds)


def foot_low(geom_xpos, geom_xmat, tb, torch):
    """Lowest world-z of every foot geom, honouring shape + orientation. (W, nfootgeoms)"""
    flat, is_cap, s0, s1, s3, _ = tb
    z = geom_xpos[:, flat, 2]                                   # (W, G)
    R2 = geom_xmat[:, flat, 2, :]                               # (W, G, 3) world-z row
    low_cap = z - (R2[:, :, 2].abs() * s1 + s0)                 # capsule: half-length along local z + radius
    low_ell = z - torch.sqrt(((R2 * s3) ** 2).sum(-1) + 1e-12)  # ellipsoid: projected semi-axis
    return torch.where(is_cap.unsqueeze(0), low_cap, low_ell)


def main() -> int:
    import torch, warp as wp, mujoco, mujoco_warp as mjw
    iters = int(sys.argv[sys.argv.index('--iters') + 1]) if '--iters' in sys.argv else 60
    envs = int(sys.argv[sys.argv.index('--envs') + 1]) if '--envs' in sys.argv else 4096
    tgt = float(sys.argv[sys.argv.index('--speed') + 1]) if '--speed' in sys.argv else TARGET_SPEED
    smoke = '--smoke' in sys.argv
    if smoke:
        envs, iters = 128, 3
    dev = 'cuda'
    torch.manual_seed(0)

    mjm = mujoco.MjModel.from_xml_path(str(MYOBODY))
    mjd = mujoco.MjData(mjm)
    nj = mjm.nq - 7
    q_key = mjm.key_qpos[0].copy()
    quat_key = torch.tensor(q_key[3:7], dtype=torch.float32, device=dev)
    STAND_Z = float(q_key[2]); FALL_Z = FALL_FRAC * STAND_Z
    mujoco.mj_resetDataKeyframe(mjm, mjd, 0); mujoco.mj_forward(mjm, mjd)
    L_PEND = float(mjd.subtree_com[0][2])                  # CoM height = the pendulum length
    G = float(-mjm.opt.gravity[2])
    OMEGA0 = float(np.sqrt(G / max(L_PEND, 1e-3)))         # w0 = sqrt(g/L) -- gravity enters HERE
    BODY_ID = [mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, b) for b in LINK_BODIES]

    W = envs
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=100, njmax=512)
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    gxpos = wp.to_torch(d.geom_xpos); gxmat = wp.to_torch(d.geom_xmat)
    xpos = wp.to_torch(d.xpos); scom = wp.to_torch(d.subtree_com)
    q_key_t = torch.tensor(q_key, dtype=torch.float32, device=dev)
    tb = foot_geom_tables(mjm, mujoco, torch, dev)
    bounds = tb[5]
    bid = torch.tensor(BODY_ID, dtype=torch.long, device=dev)
    DT_CTRL = mjm.opt.timestep * CONTROL_EVERY

    OBS = 4 + 3 + 3 + nj * 2 + 4 + 2          # + 4 foot contacts + XcoM offset (x,y)
    ACT = mjm.nu
    ac = build_ac(OBS, ACT, torch)
    if not smoke:
        warm_start_from_stand(ac, HERE / 'myobody_policy.pt', OBS, torch, dev)
    opt = torch.optim.Adam(ac.parameters(), lr=LR)

    print(f'\nPPO: a real GAIT for the {ACT}-muscle body  (capture point + contact sensing)\n' + '=' * 76)
    print(f'  {W} envs x {T} steps   pendulum L={L_PEND:.2f} m  g={G:.2f}  w0={OMEGA0:.2f} rad/s')
    print(f'  reward = speed-track x upright + {CAPTURE}*capture(support & placement) + alive - effort')
    print(f'  capture point: XcoM = com + v/w0 ; reward exp(-{CAP_K}*dist to nearest PLANTED foot)\n')
    print(f"  {'iter':>4}{'reward':>10}{'fwd':>8}{'dist':>8}{'capture':>9}{'support':>9}{'surv%':>7}{'sec':>7}")
    print('  ' + '-' * 62)

    def contacts():
        """(W,4) float 0/1 -- is each foot link planted? The 99%-agreement calibrated proxy."""
        low = foot_low(gxpos, gxmat, tb, torch)
        cols = [low[:, a:b].min(dim=1).values for (a, b) in bounds]
        return (torch.stack(cols, 1) <= CONTACT_Z).float()

    def observe(c, xoff):
        return torch.nan_to_num(torch.cat([torch.nan_to_num(qpos[:, 3:7]), qvel[:, 3:6], qvel[:, 0:3],
                                           qpos[:, 7:], qvel[:, 6:], c, xoff], 1)).clamp(-20, 20)

    gen = torch.Generator(device=dev).manual_seed(1)
    heat = None if smoke else GPUHeatGate().start()
    t_all = time.perf_counter()
    for it in range(iters):
        ti = time.perf_counter()
        qpos[:] = q_key_t.unsqueeze(0); qvel.zero_()
        qpos[:, 7:] += torch.randn(W, nj, device=dev, generator=gen) * 0.03
        mjw.forward(m, d)
        head0 = None
        start_xy = qpos[:, 0:2].clone()
        prev_com = scom[:, 0, :2].clone()

        obs_b = torch.zeros(T, W, OBS, device=dev); act_b = torch.zeros(T, W, ACT, device=dev)
        lp_b = torch.zeros(T, W, device=dev); val_b = torch.zeros(T, W, device=dev)
        rew_b = torch.zeros(T, W, device=dev); alive_b = torch.zeros(T, W, device=dev)
        alive = torch.ones(W, device=dev)
        cap_sum = torch.zeros(W, device=dev); sup_sum = torch.zeros(W, device=dev)
        fwd_sum = torch.zeros(W, device=dev)

        with torch.no_grad():
            q0 = torch.nan_to_num(qpos[:, 3:7])
            f = torch.stack([1 - 2 * (q0[:, 2]**2 + q0[:, 3]**2),
                             2 * (q0[:, 1] * q0[:, 2] + q0[:, 0] * q0[:, 3])], 1)
            head0 = f / (f.norm(dim=1, keepdim=True) + 1e-6)
            c = contacts()
            com = scom[:, 0, :2]
            xcom = com + (com - prev_com) / DT_CTRL / OMEGA0
            for t in range(T):
                o = observe(c, xcom - com)
                mean, std, v = ac(o)
                dist_n = torch.distributions.Normal(mean, std)
                raw = dist_n.sample(); lp = dist_n.log_prob(raw).sum(-1)
                ctrl[:] = raw.clamp(0.0, 1.0)
                for _ in range(CONTROL_EVERY):
                    mjw.step(m, d)

                c = contacts()
                com = scom[:, 0, :2]
                com_v = (com - prev_com) / DT_CTRL
                prev_com = com.clone()
                xcom = com + com_v / OMEGA0                     # THE CAPTURE POINT
                foot_xy = xpos[:, bid, :2]                      # (W,4,2)
                dfoot = (foot_xy - xcom.unsqueeze(1)).norm(dim=2)
                dmask = torch.where(c > 0.5, dfoot, torch.full_like(dfoot, 9.0))
                dmin = dmask.min(dim=1).values                  # 9.0 when airborne -> capture ~0
                capture = torch.exp(-CAP_K * dmin)              # support AND placement, one number

                fwd = (torch.nan_to_num(qvel[:, 0:2]) * head0).sum(1)
                vtrack = torch.clamp(fwd / tgt, -0.5, 1.0)
                upr = torch.clamp(torch.abs((torch.nan_to_num(qpos[:, 3:7]) * quat_key).sum(1)), 0, 1)
                alive = alive * (torch.nan_to_num(qpos[:, 2]) > FALL_Z).float()
                effort = raw.clamp(0.0, 1.0).pow(2).mean(1)

                obs_b[t] = o; act_b[t] = raw; lp_b[t] = lp; val_b[t] = v
                rew_b[t] = (vtrack * upr + CAPTURE * capture + ALIVE_BONUS
                            - EFFORT * effort) * alive
                alive_b[t] = alive
                cap_sum += capture * alive; sup_sum += (c.sum(1) > 0).float() * alive
                fwd_sum += fwd * alive
            _, _, last_v = ac(observe(c, xcom - com))

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
                dist_n = torch.distributions.Normal(mean, std)
                lp = dist_n.log_prob(ba[mb]).sum(-1)
                ratio = (lp - blp[mb]).exp(); a_mb = badv[mb]
                s1_ = ratio * a_mb
                s2_ = torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a_mb
                loss = (-torch.min(s1_, s2_).mean() + VCOEF * (v - bret[mb]).pow(2).mean()
                        - ent_coef * dist_n.entropy().sum(-1).mean())
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(ac.parameters(), 1.0)
                opt.step()

        dist_m = ((qpos[:, 0:2] - start_xy) * head0).sum(1).mean().item()
        surv = 100.0 * alive_b[-1].mean().item()
        if it == 0:
            init_dist = dist_m
        final_dist = dist_m
        print(f'  {it:4d}{rew_b.mean().item():10.4f}{(fwd_sum / T).mean().item():8.3f}{dist_m:8.2f}'
              f'{(cap_sum / T).mean().item():9.3f}{(sup_sum / T).mean().item():9.3f}'
              f'{surv:7.1f}{time.perf_counter()-ti:7.1f}')
        if not smoke and (it + 1) % 8 == 0:
            torch.save(ac.state_dict(), HERE / 'myobody_gait_policy.pt')
            np.save(HERE / 'myobody_gait_meta.npy',
                    dict(OBS=OBS, HID=HID, ACT=ACT, STAND_Z=STAND_Z, OMEGA0=OMEGA0))

    print('\n  ' + '-' * 62)
    print(f'  total {time.perf_counter()-t_all:.0f}s')
    torch.save(ac.state_dict(), HERE / 'myobody_gait_policy.pt')
    np.save(HERE / 'myobody_gait_meta.npy',
            dict(OBS=OBS, HID=HID, ACT=ACT, STAND_Z=STAND_Z, OMEGA0=OMEGA0))
    print('  saved myobody_gait_policy.pt')
    if heat is not None:
        heat.enforce(improved=final_dist - init_dist, threshold=0.5, metric='forward distance (m)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
