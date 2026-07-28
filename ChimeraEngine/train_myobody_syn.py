"""train_myobody_syn.py — the same gait task, but the policy ACTS IN SYNERGY SPACE (16, not 290).

STEP 1 of the frontier plan, alone. This file is `train_myobody_gait.py` with **exactly one thing
changed**: the action space. Same body, same reward (speed-track x upright + capture point + alive
- effort), same contact sensing, same warm start, same everything -- so whatever differs is
attributable to the synergies and nothing else. (Three coupled changes would be a three-body problem:
no attributable solution. CPG and latent exploration stay untouched.)

    MEASURED, NOT ASSUMED: mining the trained STAND policy's mean activations, 8 dimensions explain
    91% of this body's movement and 16 explain ~96% (synergy.py). So the policy emits 16 synergy
    coefficients and a fixed basis decodes them to 290 muscle activations:

        activations = clip( mean + (coeff * scale) @ synergies , 0, 1 )

    THE STAND TRANSFERS EXACTLY. A 290-output head cannot load into a 16-output one, but the map is
    linear, so the stand's final layer can be *projected* into synergy space in closed form:
        W_new = (P^T W_old) / scale ,  b_new = ((b_old - mean) @ P) / scale ,  P = pinv(synergies)
    which reproduces the stand's own output through the decoder (to the basis's ~96% fidelity). The
    body keeps its balance on day one instead of relearning it in a new action space.

Run:  python ChimeraEngine/train_myobody_syn.py [--envs N] [--iters N] [--dims 16] [--smoke]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gpu_gate import GPUHeatGate                                             # noqa: E402
from train_myobody_gait import (MYOBODY, T, CONTROL_EVERY, HID, GAMMA, LAM, CLIP, EPOCHS,
                                MINIBATCH, LR, ENT, VCOEF, ALIVE_BONUS, FALL_FRAC, EFFORT,
                                TARGET_SPEED, CAPTURE, CAP_K, CONTACT_Z, LINK_BODIES,
                                build_ac, foot_geom_tables, foot_low)                # noqa: E402


def load_synergies(path, torch, dev):
    z = np.load(path, allow_pickle=True)
    mu = torch.tensor(z['mean'], dtype=torch.float32, device=dev)          # (290,)
    syn = torch.tensor(z['synergies'], dtype=torch.float32, device=dev)    # (K, 290)
    scale = torch.tensor(z['scale'], dtype=torch.float32, device=dev)      # (K,)
    return mu, syn, scale, int(z['dims']), float(z['explained'][-1])


def project_head(sd, mu, syn, scale, torch):
    """Project the STAND policy's 290-output head into K-dim synergy space, in closed form."""
    P = torch.linalg.pinv(syn)                                             # (290, K)
    W_old = sd['mean.weight'].to(P.dtype)                                  # (290, HID)
    b_old = sd['mean.bias'].to(P.dtype)                                    # (290,)
    W_new = (P.T @ W_old) / scale.unsqueeze(1)                             # (K, HID)
    b_new = ((b_old - mu) @ P) / scale                                     # (K,)
    return W_new, b_new


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
    L_PEND = float(mjd.subtree_com[0][2]); G = float(-mjm.opt.gravity[2])
    OMEGA0 = float(np.sqrt(G / max(L_PEND, 1e-3)))
    BODY_ID = [mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, b) for b in LINK_BODIES]

    mu_s, syn, scale, K, expl = load_synergies(HERE / 'myobody_synergies.npz', torch, dev)

    W = envs
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=100, njmax=512)
    qpos = wp.to_torch(d.qpos); qvel = wp.to_torch(d.qvel); ctrl = wp.to_torch(d.ctrl)
    gxpos = wp.to_torch(d.geom_xpos); gxmat = wp.to_torch(d.geom_xmat)
    xpos = wp.to_torch(d.xpos); scom = wp.to_torch(d.subtree_com)
    q_key_t = torch.tensor(q_key, dtype=torch.float32, device=dev)
    tb = foot_geom_tables(mjm, mujoco, torch, dev); bounds = tb[5]
    bid = torch.tensor(BODY_ID, dtype=torch.long, device=dev)
    DT_CTRL = mjm.opt.timestep * CONTROL_EVERY

    OBS = 4 + 3 + 3 + nj * 2 + 4 + 2
    NMUS = mjm.nu
    ac = build_ac(OBS, K, torch)                      # <-- the ONE change: K outputs, not 290
    if not smoke and (HERE / 'myobody_policy.pt').exists():
        sd = torch.load(HERE / 'myobody_policy.pt', map_location=dev)
        own = ac.state_dict()
        w = sd['body.0.weight']
        neww = own['body.0.weight'].clone(); neww.zero_(); neww[:, :w.shape[1]] = w
        own['body.0.weight'] = neww; own['body.0.bias'] = sd['body.0.bias']
        own['body.2.weight'] = sd['body.2.weight']; own['body.2.bias'] = sd['body.2.bias']
        own['v.weight'] = sd['v.weight']; own['v.bias'] = sd['v.bias']
        Wn, bn = project_head(sd, mu_s, syn, scale, torch)
        own['mean.weight'] = Wn; own['mean.bias'] = bn
        ac.load_state_dict(own)
        print(f'  warm-started from the STAND policy, head PROJECTED into {K}-dim synergy space')
    opt = torch.optim.Adam(ac.parameters(), lr=LR)

    def decode(c):
        """K synergy coefficients -> 290 muscle activations."""
        return torch.clamp(mu_s + (c * scale) @ syn, 0.0, 1.0)

    print(f'\nPPO in SYNERGY SPACE — {NMUS} muscles driven by {K} synergies '
          f'({expl*100:.1f}% of movement)\n' + '=' * 78)
    print(f'  {W} envs x {T} steps   action space {NMUS} -> {K}  ({NMUS//K}x smaller search)')
    print(f'  reward identical to train_myobody_gait (capture point w0={OMEGA0:.2f}); ONLY the '
          f'action space differs\n')
    print(f"  {'iter':>4}{'reward':>10}{'fwd':>8}{'dist':>8}{'capture':>9}{'support':>9}{'surv%':>7}{'sec':>7}")
    print('  ' + '-' * 62)

    def contacts():
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
        start_xy = qpos[:, 0:2].clone(); prev_com = scom[:, 0, :2].clone()

        obs_b = torch.zeros(T, W, OBS, device=dev); act_b = torch.zeros(T, W, K, device=dev)
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
            c = contacts(); com = scom[:, 0, :2]; xcom = com.clone()
            for t in range(T):
                o = observe(c, xcom - com)
                mean, std, v = ac(o)
                dist_n = torch.distributions.Normal(mean, std)
                raw = dist_n.sample(); lp = dist_n.log_prob(raw).sum(-1)
                ctrl[:] = decode(raw)                       # synergies -> 290 muscles
                for _ in range(CONTROL_EVERY):
                    mjw.step(m, d)

                c = contacts(); com = scom[:, 0, :2]
                com_v = (com - prev_com) / DT_CTRL; prev_com = com.clone()
                xcom = com + com_v / OMEGA0
                dfoot = (xpos[:, bid, :2] - xcom.unsqueeze(1)).norm(dim=2)
                dmin = torch.where(c > 0.5, dfoot, torch.full_like(dfoot, 9.0)).min(dim=1).values
                capture = torch.exp(-CAP_K * dmin)

                fwd = (torch.nan_to_num(qvel[:, 0:2]) * head0).sum(1)
                vtrack = torch.clamp(fwd / tgt, -0.5, 1.0)
                upr = torch.clamp(torch.abs((torch.nan_to_num(qpos[:, 3:7]) * quat_key).sum(1)), 0, 1)
                alive = alive * (torch.nan_to_num(qpos[:, 2]) > FALL_Z).float()
                effort = decode(raw).pow(2).mean(1)
                obs_b[t] = o; act_b[t] = raw; lp_b[t] = lp; val_b[t] = v
                rew_b[t] = (vtrack * upr + CAPTURE * capture + ALIVE_BONUS - EFFORT * effort) * alive
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
        bo = obs_b.reshape(-1, OBS); ba = act_b.reshape(-1, K)
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
                loss = (-torch.min(ratio * a_mb,
                                   torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a_mb).mean()
                        + VCOEF * (v - bret[mb]).pow(2).mean()
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
            torch.save(ac.state_dict(), HERE / 'myobody_syn_policy.pt')
            np.save(HERE / 'myobody_syn_meta.npy',
                    dict(OBS=OBS, HID=HID, ACT=K, NMUS=NMUS, STAND_Z=STAND_Z, OMEGA0=OMEGA0))

    print('\n  ' + '-' * 62)
    print(f'  total {time.perf_counter()-t_all:.0f}s')
    torch.save(ac.state_dict(), HERE / 'myobody_syn_policy.pt')
    np.save(HERE / 'myobody_syn_meta.npy',
            dict(OBS=OBS, HID=HID, ACT=K, NMUS=NMUS, STAND_Z=STAND_Z, OMEGA0=OMEGA0))
    print('  saved myobody_syn_policy.pt')
    if heat is not None:
        heat.enforce(improved=final_dist - init_dist, threshold=0.5, metric='forward distance (m)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
