"""policy_gait_eval.py — measure the trained myobody WALK policy against the CMU mocap reference.

THE CONTRACT IS THE RECOVERED ONE. The rollout replicates train_myobody_walk.py / gait_myobody.py
(deleted in 79214ce, recovered from git into ChimeraEngine/output/_recovered_*.py) byte-for-byte:
keyframe + N(0, 0.03) joint noise, CONTROL_EVERY = 20, sampled actions clamped to [0, 1],
obs = [qpos[3:7], qvel[3:6], qvel[0:3], qpos[7:], qvel[6:]].clamp(-20, 20). The contact dyad
(MuJoCo truth vs geometric proxy) and WORST-OF-N scoring come from the same witness.

ANGLE MATH IS THE MOCAP MATH. Hip/knee/ankle sagittal angles are computed from world segment
vectors with the same conventions as tools/mocap_gait.py, so the A/B is apples-to-apples.

Run:  C:\\Python314\\python.exe tools/policy_gait_eval.py [--policy myobody_walk_policy.pt] [--n 5] [--secs 10]
Writes: research_references/human/gait_vs_mocap_report.json
        research_references/human/gait_vs_mocap_report.md
        ChimeraEngine/output/policy_walk_trace.npz        (raw traces for the A/B plot)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'ChimeraEngine'
MYOBODY = ROOT / 'external' / 'myo_sim' / 'body' / 'myobody.xml'
REF = ROOT / 'research_references' / 'human' / 'mocap_walk_reference.json'
OUT_JSON = ROOT / 'research_references' / 'human' / 'gait_vs_mocap_report.json'
OUT_MD = ROOT / 'research_references' / 'human' / 'gait_vs_mocap_report.md'
OUT_TRACE = HERE / 'output' / 'policy_walk_trace.npz'
CONTROL_EVERY = 20

BODIES = {  # segment endpoints for the vector-angle math (same roles as the CMU joints)
    'hip_r': 'femur_r', 'knee_r': 'tibia_r', 'ankle_r': 'talus_r', 'toe_r': 'toes_r',
    'hip_l': 'femur_l', 'knee_l': 'tibia_l', 'ankle_l': 'talus_l', 'toe_l': 'toes_l',
    'pelvis': 'pelvis', 'trunk': 'torso',
}


def load_gait():
    spec = importlib.util.spec_from_file_location('chimera_gait', Path(__file__).parent / 'chimera_gait.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_ac(OBS, ACT, HID, torch):
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

    return AC()


def foot_sets(m, mujoco):
    links = ['heel_L', 'toe_L', 'heel_R', 'toe_R']
    bodies = {'heel_L': 'calcn_l', 'toe_L': 'toes_l', 'heel_R': 'calcn_r', 'toe_R': 'toes_r'}
    geoms = {k: [] for k in links}
    for gi in range(m.ngeom):
        g = m.geom(gi)
        if g.contype[0] == 0 and g.conaffinity[0] == 0:
            continue
        bn = m.body(g.bodyid[0]).name
        for k, b in bodies.items():
            if bn == b:
                geoms[k].append(gi)
    floor = {gi for gi in range(m.ngeom) if m.geom(gi).type[0] == mujoco.mjtGeom.mjGEOM_PLANE}
    return links, geoms, floor


def geom_low(m, d, gi, mujoco):
    g = m.geom(gi)
    z = float(d.geom_xpos[gi][2])
    R = np.array(d.geom_xmat[gi]).reshape(3, 3)
    s = np.asarray(g.size, dtype=float)
    t = int(g.type[0])
    if t == mujoco.mjtGeom.mjGEOM_SPHERE:
        return z - s[0]
    if t == mujoco.mjtGeom.mjGEOM_CAPSULE:
        return z - (abs(R[2, 2]) * s[1] + s[0])
    if t == mujoco.mjtGeom.mjGEOM_ELLIPSOID:
        return z - float(np.sqrt(((R[2, :3] * s[:3]) ** 2).sum()))
    if t == mujoco.mjtGeom.mjGEOM_BOX:
        return z - float((np.abs(R[2, :3]) * s[:3]).sum())
    return z - float(s[0])


def seg_angle(vf, vu):
    return np.degrees(np.arctan2(vf, -vu))


def angles_from_positions(bp, fwd2):
    """Same vector math as mocap_gait.sagittal_angles, on myobody body positions.

    bp: dict role -> (T,3) world positions. fwd2: horizontal unit vector of travel.
    Returns hip/knee/ankle (T,) per side.
    """
    up3 = np.array([0.0, 0.0, 1.0])
    fwd3 = np.array([fwd2[0], fwd2[1], 0.0])

    def proj(role):
        v = bp[role]
        return np.stack([v @ fwd3, v @ up3], axis=1)

    out = {}
    trunk = proj('trunk') - proj('pelvis')
    th_trunk = seg_angle(-trunk[:, 0], -trunk[:, 1])
    for s in ('r', 'l'):
        thigh = proj(f'knee_{s}') - proj(f'hip_{s}')
        shank = proj(f'ankle_{s}') - proj(f'knee_{s}')
        foot = proj(f'toe_{s}') - proj(f'ankle_{s}')
        th_thigh = seg_angle(thigh[:, 0], thigh[:, 1])
        th_shank = seg_angle(shank[:, 0], shank[:, 1])
        flen = np.linalg.norm(foot, axis=1) + 1e-9
        foot_pitch = np.degrees(np.arcsin(np.clip(foot[:, 1] / flen, -1, 1)))
        out[f'hip_{s}'] = th_thigh - th_trunk
        out[f'knee_{s}'] = th_thigh - th_shank
        out[f'ankle_{s}'] = foot_pitch - th_shank
    return out


def rollout(m, d, ac, torch, mujoco, secs, seed):
    links, geoms, floor = foot_sets(m, mujoco)
    nj = m.nq - 7
    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[7:] += np.random.default_rng(seed).normal(0, 0.03, nj)
    mujoco.mj_forward(m, d)
    q = d.qpos[3:7]
    head = np.array([1 - 2 * (q[2] ** 2 + q[3] ** 2), 2 * (q[1] * q[2] + q[0] * q[3])])
    head /= (np.linalg.norm(head) + 1e-6)
    start_xy = d.qpos[0:2].copy()
    stand_z = float(m.key_qpos[0][2])

    bid = {role: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, name) for role, name in BODIES.items()}
    steps = int(secs / m.opt.timestep)
    dt_ctrl = m.opt.timestep * CONTROL_EVERY
    truth, lows, bodypos, rootxy, rootz, speed = [], [], [], [], [], []
    fell_at = None
    with torch.no_grad():
        for k in range(0, steps, CONTROL_EVERY):
            ob = torch.tensor(np.nan_to_num(np.concatenate(
                [d.qpos[3:7], d.qvel[3:6], d.qvel[0:3], d.qpos[7:], d.qvel[6:]])),
                dtype=torch.float32).unsqueeze(0).clamp(-20, 20)
            mean, std, _v = ac(ob)
            a = mean + std * torch.randn_like(std)
            d.ctrl[:] = a.clamp(0.0, 1.0).squeeze(0).numpy()
            for _ in range(CONTROL_EVERY):
                mujoco.mj_step(m, d)
            touched = set()
            for ci in range(d.ncon):
                c = d.contact[ci]
                g1, g2 = int(c.geom1), int(c.geom2)
                other = g2 if g1 in floor else (g1 if g2 in floor else None)
                if other is None:
                    continue
                for name, gl in geoms.items():
                    if other in gl:
                        touched.add(name)
            truth.append([1 if L in touched else 0 for L in links])
            lows.append([min(geom_low(m, d, gi, mujoco) for gi in geoms[L]) for L in links])
            bodypos.append({role: d.xpos[b].copy() for role, b in bid.items()})
            rootxy.append(float(np.dot(d.qpos[0:2] - start_xy, head)))
            rootz.append(float(d.qpos[2]))
            speed.append(float(np.dot(d.qvel[0:2], head)))
            if fell_at is None and d.qpos[2] < 0.6 * stand_z:
                fell_at = k * m.opt.timestep
    dist = float(np.dot(d.qpos[0:2] - start_xy, head))
    bp = {role: np.array([b[role] for b in bodypos]) for role in bid}
    ang = angles_from_positions(bp, head)
    return {
        'truth': np.array(truth), 'lows': np.array(lows), 'links': links,
        'angles': ang, 'dist': dist, 'fell_at': fell_at, 'dt': dt_ctrl,
        'rootxy': np.array(rootxy), 'rootz': np.array(rootz), 'speed': np.array(speed),
    }


def strike_metrics(contact_lr, dt):
    """Steps from foot contact (heel OR toe per side). Returns cadence, duty, n_strikes."""
    out = {}
    all_st = []
    for side, cols in (('L', [0, 1]), ('R', [2, 3])):
        c = (contact_lr[:, cols].sum(1) > 0).astype(int)
        d = np.diff(np.concatenate([[0], c, [0]]))
        st = np.where(d == 1)[0]
        off = np.where(d == -1)[0]
        strides = np.diff(st) * dt if len(st) > 1 else np.array([])
        pairs = [(s, off[off > s][0]) for s in st if np.any(off > s)]
        duty = float(np.mean([(o - s) * dt for s, o in pairs]) / np.mean(strides)) if pairs and len(strides) else None
        out[side] = {'n_strikes': int(len(st)),
                     'stride_s': float(np.mean(strides)) if len(strides) else None,
                     'duty': duty}
        all_st += list(st)
    if len(all_st) > 2:
        all_st = np.sort(all_st)
        out['cadence'] = 60.0 * (len(all_st) - 1) / ((all_st[-1] - all_st[0]) * dt)
    else:
        out['cadence'] = None
    return out


def envelope(angles, strikes, n=101):
    xs = np.linspace(0, 100, n)
    mats = []
    for a, b in zip(strikes[:-1], strikes[1:]):
        if b - a < 4:
            continue
        mats.append(np.interp(xs, np.linspace(0, 100, b - a), angles[a:b]))
    if len(mats) < 2:
        return None, 0
    return np.array(mats).mean(0), len(mats)


def phase_err(ref, pol):
    """Circular cross-correlation: best lag (% cycle) and RMSE at that lag."""
    r = np.asarray(ref, float)
    p = np.asarray(pol, float)
    r = r - r.mean(); p = p - p.mean()
    best = (0, np.inf)
    n = len(r)
    for lag in range(n):
        ps = np.roll(p, lag)
        e = float(np.sqrt(np.mean((r - ps) ** 2)))
        if e < best[1]:
            best = (lag * 100.0 / n, e)
    # amplitude ratio on top
    return best[0], best[1]


def main():
    import torch
    import mujoco
    pol_name = sys.argv[sys.argv.index('--policy') + 1] if '--policy' in sys.argv else 'myobody_walk_policy.pt'
    N = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 5
    secs = float(sys.argv[sys.argv.index('--secs') + 1]) if '--secs' in sys.argv else 10.0
    ref = json.loads(REF.read_text())

    ppath = Path(pol_name)
    if not ppath.is_absolute():
        ppath = (ROOT / pol_name) if (ROOT / pol_name).exists() else (HERE / pol_name)
    suffix = '' if ppath.stem == 'myobody_walk_policy' else f'__{ppath.stem.replace("_policy", "")}'
    out_json = OUT_JSON.with_name(OUT_JSON.stem + suffix + '.json')
    out_md = OUT_MD.with_name(OUT_MD.stem + suffix + '.md')
    out_trace = OUT_TRACE.with_name(OUT_TRACE.stem + suffix + '.npz')
    meta_name = str(ppath).replace('_policy.pt', '_meta.npy')
    meta = np.load(meta_name, allow_pickle=True).item()
    OBS, HID, ACT = int(meta['OBS']), int(meta['HID']), int(meta['ACT'])
    G = load_gait()
    torch.manual_seed(0)
    m = mujoco.MjModel.from_xml_path(str(MYOBODY))
    d = mujoco.MjData(m)
    ac = build_ac(OBS, ACT, HID, torch)
    ac.load_state_dict(torch.load(ppath, map_location='cpu', weights_only=False))
    ac.eval()

    print(f'\nPOLICY GAIT vs MOCAP — {pol_name}, {N} starts x {secs:.0f}s\n' + '=' * 74)
    runs = [rollout(m, d, ac, torch, mujoco, secs, s) for s in range(N)]

    # contact dyad calibration (same sweep as the recovered witness)
    T_all = np.concatenate([r['truth'] for r in runs])
    H_all = np.concatenate([r['lows'] for r in runs])
    cand = np.arange(0.0, 0.121, 0.002)
    scores = [float(((H_all <= c).astype(int) == T_all).mean()) for c in cand]
    bi = int(np.argmax(scores))
    thresh = float(cand[bi])
    print(f'  contact dyad: threshold {thresh * 100:.1f} cm -> {scores[bi]:.1%} truth agreement')

    per_run = []
    for s, r in enumerate(runs):
        proxy = (r['lows'] <= thresh).astype(int)
        a = G.analyze({'contact': proxy, 'links': r['links'], 'dt_sample': r['dt'],
                       'distance': r['dist']})
        ev = strike_metrics(proxy, r['dt'])
        per_run.append({'seed': s, 'analyze': a, 'events': ev, 'dist': r['dist'],
                        'fell_at': r['fell_at'],
                        'survival_s': r['fell_at'] if r['fell_at'] is not None else secs})
        print(f'  seed {s}: dist {r["dist"]:5.2f} m  periodicity {a["periodicity"]:.2f}  '
              f'duty {a["duty_mean"]:.2f}  '
              + (f'FELL @{r["fell_at"]:.1f}s' if r['fell_at'] is not None else 'stayed up'))

    worst = min(per_run, key=lambda r: r['analyze']['periodicity'])
    a = worst['analyze']

    # policy envelopes from the BEST surviving run, if it has cycles at all
    best_run = max(zip(per_run, runs), key=lambda pr: pr[0]['survival_s'])[1]
    best_e = max(per_run, key=lambda r: r['survival_s'])
    proxy_best = (best_run['lows'] <= thresh).astype(int)
    env_pol = {}
    strikes = {}
    for side, cols, sfx in (('L', [0, 1], 'l'), ('R', [2, 3], 'r')):
        c = (proxy_best[:, cols].sum(1) > 0).astype(int)
        dd = np.diff(np.concatenate([[0], c, [0]]))
        st = np.where(dd == 1)[0]
        strikes[sfx] = st
    for joint in ('hip', 'knee', 'ankle'):
        ms = []
        for sfx in ('l', 'r'):
            e, nc = envelope(best_run['angles'][f'{joint}_{sfx}'], strikes[sfx])
            if e is not None:
                ms.append(e)
        env_pol[joint] = np.mean(ms, 0).tolist() if ms else None

    comparison = {
        'cadence': {'ref_steps_min': ref['cadence_steps_per_min'],
                    'policy_steps_min': best_e['events'].get('cadence'),
                    'ratio': (best_e['events'].get('cadence') / ref['cadence_steps_per_min'])
                    if best_e['events'].get('cadence') else None},
        'stride_m': {'ref': ref['stride_length_m'],
                     'policy': None, 'note': 'policy stride requires surviving strides; see events'},
        'duty_factor': {'ref': ref['duty_factor'], 'policy_worst': a['duty_mean']},
        'periodicity': {'policy_worst_of_N': a['periodicity'], 'threshold_walk': 0.6},
        'survival_s': {'min': min(r['survival_s'] for r in per_run),
                       'max': max(r['survival_s'] for r in per_run)},
        'distance_m': {'min': min(r['dist'] for r in per_run),
                       'max': max(r['dist'] for r in per_run)},
        'angle_phase_error': {},
        'classification': a['classification'],
    }
    for joint in ('hip', 'knee', 'ankle'):
        if env_pol[joint] is not None:
            lag, rmse = phase_err(ref['envelopes_deg'][joint]['mean'], env_pol[joint])
            comparison['angle_phase_error'][joint] = {'lag_pct_cycle': round(lag, 1),
                                                      'rmse_deg': round(rmse, 1)}
        else:
            comparison['angle_phase_error'][joint] = None

    report = {
        'policy': pol_name,
        'rollout_contract': 'recovered train_myobody_walk.py: keyframe+noise(0.03), CONTROL_EVERY=20, '
                            'sampled actions clamp[0,1], obs=[quat, angvel, linvel, qpos[7:], qvel[6:]]',
        'n_seeds': N, 'secs_per_seed': secs,
        'contact_proxy_threshold_m': thresh, 'contact_dyad_agreement': scores[bi],
        'reference_summary': {k: ref[k] for k in ('cadence_steps_per_min', 'stride_length_m',
                                                  'duty_factor', 'speed_m_s', 'stride_time_s')},
        'per_seed': [{'seed': r['seed'], 'dist_m': round(r['dist'], 3),
                      'fell_at_s': r['fell_at'], 'periodicity': round(r['analyze']['periodicity'], 3),
                      'duty_mean': round(r['analyze']['duty_mean'], 3),
                      'suspension_frac': round(r['analyze']['suspension_frac'], 3),
                      'classification': r['analyze']['classification'],
                      'events': r['events']} for r in per_run],
        'worst_of_N': {'periodicity': a['periodicity'], 'duty_mean': a['duty_mean'],
                       'period_s': a['period_s'], 'classification': a['classification']},
        'comparison': comparison,
        'policy_envelopes_deg': env_pol,
    }
    out_json.write_text(json.dumps(report, indent=2, default=str))

    np.savez(out_trace,
             ref_hip=ref['envelopes_deg']['hip']['mean'], ref_knee=ref['envelopes_deg']['knee']['mean'],
             ref_ankle=ref['envelopes_deg']['ankle']['mean'],
             ref_hip_std=ref['envelopes_deg']['hip']['std'],
             ref_knee_std=ref['envelopes_deg']['knee']['std'],
             ref_ankle_std=ref['envelopes_deg']['ankle']['std'],
             pol_angles_t=np.arange(len(best_run['rootz'])) * best_run['dt'],
             pol_rootz=best_run['rootz'], pol_speed=best_run['speed'],
             **{f'pol_{k}': v for k, v in best_run['angles'].items()},
             env_pol_hip=np.array(env_pol['hip']) if env_pol['hip'] else np.array([]),
             env_pol_knee=np.array(env_pol['knee']) if env_pol['knee'] else np.array([]),
             env_pol_ankle=np.array(env_pol['ankle']) if env_pol['ankle'] else np.array([]))

    verdict_lines = []
    surv = comparison['survival_s']
    if a['periodicity'] < 0.6 or surv['min'] < secs:
        verdict_lines.append('GAP IS LARGE — the policy does not sustain a measurable gait.')
    else:
        verdict_lines.append('Policy gait is measurable; see per-joint phase errors.')

    md = f"""# Myobody walk policy vs CMU mocap (35_01 walk) — A/B report

**Policy:** `{pol_name}` (PPO, 290-muscle MyoSuite myobody; recovered rollout contract)
**Reference:** CMU MoCap subject 35 walk, 120 Hz — see `mocap_walk_reference.json`
**Method:** {N} randomized starts x {secs:.0f} s, WORST-of-N scoring (project rule), contact dyad
(MuJoCo truth vs geometric proxy, {scores[bi]:.1%} agreement at {thresh * 100:.1f} cm).

## Reference (real human, measured)

| metric | value |
|---|---|
| cadence | {ref['cadence_steps_per_min']} steps/min |
| stride length | {ref['stride_length_m']} m ({ref['stride_length_leg_lengths']} leg lengths) |
| stride time | {ref['stride_time_s']} s |
| duty factor | {ref['duty_factor']} |
| speed | {ref['speed_m_s']} m/s |

## Policy (measured, worst of {N})

| metric | value |
|---|---|
| classification | {a['classification']} |
| periodicity | {a['periodicity']:.2f} (walk needs >= ~0.6) |
| duty factor | {a['duty_mean']:.2f} (human 0.55-0.65) |
| survival | {surv['min']:.1f} - {surv['max']:.1f} s of {secs:.0f} s |
| forward distance | {comparison['distance_m']['min']:.2f} - {comparison['distance_m']['max']:.2f} m |
| cadence | {best_e['events'].get('cadence') or 'n/a'} steps/min |

## Verdict

{verdict_lines[0]}

Per-seed detail and angle phase errors: `gait_vs_mocap_report.json`.
"""
    out_md.write_text(md)
    print(f'\n  VERDICT: {verdict_lines[0]}')
    print(f'  wrote {OUT_JSON.name}, {OUT_MD.name}, {OUT_TRACE.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
