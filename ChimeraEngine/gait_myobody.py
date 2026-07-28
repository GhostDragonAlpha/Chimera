"""gait_myobody.py — DOES IT WALK, OR DOES IT JUST ARRIVE?

The walk render showed 1.11 m travelled. That is a RECEIPT, not a gait -- this studio has already
been fooled once by exactly that number (a celebrated "walker" scored periodicity 0.25: no repeating
cycle at all, no limit cycle, no gait). So before building anything on top of the walk, MEASURE it
with the project's own witness: `Chimera/core/gait.py` (Hildebrand footfall diagram, duty factor, and
PERIODICITY = autocorrelation of the support signal, 1.0 = metronome, 0.0 = seizure). That math is
reused here verbatim, not reinvented.

    CONTACT IS MEASURED TWICE -- a dyad, and it calibrates the trainer.
      * TRUTH: MuJoCo's own contact list (floor geom vs the foot collision geoms). Exact, CPU-only.
      * PROXY: the foot geoms' lowest point below a height threshold. Cheap, needs no contact
        readback -- so it is what the GPU trainer can compute in-kernel with ZERO CPU syncs.
    They must agree. The agreement % is printed, and it is what licenses using the proxy in training.

    WORST OF N -- one rollout is a coin toss (this project's hardest-won rule). Every metric is
    reported for N randomized starts, and the WORST is the honest score.

Run:  python ChimeraEngine/gait_myobody.py [--policy walk|stand] [--n 5] [--secs 4]
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
MYOBODY = HERE.parent / 'vendor' / 'myo_sim' / 'body' / 'myobody.xml'
GAIT_PY = HERE.parent / 'Chimera' / 'core' / 'gait.py'
CONTROL_EVERY = 20
FOOT_Z = 0.02                          # proxy threshold: foot lowest point within 2 cm of the floor


def load_gait_module():
    """Import Chimera/core/gait.py by path (stdlib+numpy only, so no package machinery needed)."""
    spec = importlib.util.spec_from_file_location('chimera_gait', GAIT_PY)
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
            self.mean = nn.Linear(HID, ACT); self.v = nn.Linear(HID, 1)
            self.log_std = nn.Parameter(torch.full((ACT,), -0.7))

        def forward(self, o):
            h = self.body(o)
            return self.mean(h), self.log_std.exp(), self.v(h).squeeze(-1)

    return AC()


def foot_sets(m, mujoco):
    """The four contact links, and for each the collision geoms MuJoCo will actually report."""
    links = ['heel_L', 'toe_L', 'heel_R', 'toe_R']
    bodies = {'heel_L': 'calcn_l', 'toe_L': 'toes_l', 'heel_R': 'calcn_r', 'toe_R': 'toes_r'}
    geoms = {k: [] for k in links}
    for gi in range(m.ngeom):
        g = m.geom(gi)
        if g.contype[0] == 0 and g.conaffinity[0] == 0:
            continue                                   # visual-only geom, never contacts
        bn = m.body(g.bodyid[0]).name
        for k, b in bodies.items():
            if bn == b:
                geoms[k].append(gi)
    floor = [gi for gi in range(m.ngeom) if m.geom(gi).type[0] == mujoco.mjtGeom.mjGEOM_PLANE]
    return links, geoms, set(floor)


def _geom_low(m, d, gi, mujoco):
    """World-z of a geom's LOWEST point, honouring its shape and orientation.

    The first pass used `size[0]` for every geom, which is only the radius of a SPHERE -- these feet
    are CAPSULES (radius, half-length along local z) and an ELLIPSOID (three semi-axes), so a rotated
    foot's true low point was wrong and the contact proxy only agreed 75% with MuJoCo's truth.
    """
    g = m.geom(gi)
    z = float(d.geom_xpos[gi][2])
    R = np.array(d.geom_xmat[gi]).reshape(3, 3)
    s = np.asarray(g.size, dtype=float)
    t = int(g.type[0])
    if t == mujoco.mjtGeom.mjGEOM_SPHERE:
        return z - s[0]
    if t == mujoco.mjtGeom.mjGEOM_CAPSULE:
        return z - (abs(R[2, 2]) * s[1] + s[0])            # half-length along local z, plus radius
    if t == mujoco.mjtGeom.mjGEOM_ELLIPSOID:
        return z - float(np.sqrt(((R[2, :3] * s[:3]) ** 2).sum()))
    if t == mujoco.mjtGeom.mjGEOM_BOX:
        return z - float((np.abs(R[2, :3]) * s[:3]).sum())
    return z - float(s[0])


def rollout(m, d, ac, torch, mujoco, links, geoms, floor, secs, seed, decode=None, OBS=None):
    """One episode. Returns the two contact traces + distance travelled.

    `decode` maps a synergy-space action to 290 muscle activations (None = the policy already emits
    muscles). `OBS` lets the walk/gait/synergy policies receive the LARGER observation they were
    trained on (contacts + capture-point offset) -- feeding a policy a different observation than it
    trained on would measure a different controller than the one we are judging.
    """
    nj = m.nq - 7
    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[7:] += np.random.default_rng(seed).normal(0, 0.03, nj)
    mujoco.mj_forward(m, d)
    q = d.qpos[3:7]
    head = np.array([1 - 2 * (q[2]**2 + q[3]**2), 2 * (q[1]*q[2] + q[0]*q[3])])
    head /= (np.linalg.norm(head) + 1e-6)
    start_xy = d.qpos[0:2].copy()
    stand_z = float(m.key_qpos[0][2])

    truth, proxy = [], []
    fell_at = None
    steps = int(secs / m.opt.timestep)
    OMEGA0 = float(np.sqrt(-m.opt.gravity[2] / max(d.subtree_com[0][2], 1e-3)))
    prev_com = d.subtree_com[0][:2].copy()
    last_c = np.zeros(len(links)); last_xoff = np.zeros(2)
    with torch.no_grad():
        for k in range(0, steps, CONTROL_EVERY):
            base = np.concatenate([d.qpos[3:7], d.qvel[3:6], d.qvel[0:3], d.qpos[7:], d.qvel[6:]])
            if OBS is not None and OBS > len(base):          # the policy also senses contact + XcoM
                base = np.concatenate([base, last_c, last_xoff])
            ob = torch.tensor(np.nan_to_num(base), dtype=torch.float32).unsqueeze(0).clamp(-20, 20)
            mean, std, _v = ac(ob)
            a = mean + std * torch.randn_like(std)
            act = decode(a) if decode is not None else a.clamp(0.0, 1.0)
            d.ctrl[:] = act.squeeze(0).numpy()
            for _ in range(CONTROL_EVERY):
                mujoco.mj_step(m, d)
            # TRUTH: MuJoCo's own contact list
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
            # PROXY: record the lowest point of each link's collision geoms (GPU-computable from
            # geom pose alone -- no contact readback, so no CPU sync in a batched rollout). The
            # height->contact THRESHOLD is calibrated against the truth below, never guessed.
            lows = [min(_geom_low(m, d, gi, mujoco) for gi in geoms[L]) for L in links]
            proxy.append(lows)
            # feed the NEXT step the senses the policy was trained on
            last_c = np.array([1.0 if lo <= 0.002 else 0.0 for lo in lows])
            com = d.subtree_com[0][:2].copy()
            com_v = (com - prev_com) / (m.opt.timestep * CONTROL_EVERY)
            prev_com = com
            last_xoff = com_v / OMEGA0                      # XcoM offset = v / omega0
            if fell_at is None and d.qpos[2] < 0.6 * stand_z:
                fell_at = k * m.opt.timestep
    dist = float(np.dot(d.qpos[0:2] - start_xy, head))
    dt_sample = m.opt.timestep * CONTROL_EVERY
    return (np.array(truth), np.array(proxy), dist, fell_at, dt_sample)


def main() -> int:
    import torch, mujoco
    which = sys.argv[sys.argv.index('--policy') + 1] if '--policy' in sys.argv else 'walk'
    N = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 5
    secs = float(sys.argv[sys.argv.index('--secs') + 1]) if '--secs' in sys.argv else 4.0
    tag = {'walk': 'myobody_walk', 'stand': 'myobody', 'gait': 'myobody_gait',
           'syn': 'myobody_syn'}[which]
    meta = np.load(HERE / f'{tag}_meta.npy', allow_pickle=True).item()
    OBS, HID, ACT = int(meta['OBS']), int(meta['HID']), int(meta['ACT'])

    G = load_gait_module()
    m = mujoco.MjModel.from_xml_path(str(MYOBODY))
    d = mujoco.MjData(m)
    ac = build_ac(OBS, ACT, HID, torch)
    ac.load_state_dict(torch.load(HERE / f'{tag}_policy.pt', map_location='cpu')); ac.eval()

    decode = None
    if 'NMUS' in meta:                                  # a SYNERGY policy: 16 coeffs -> 290 muscles
        z = np.load(HERE / 'myobody_synergies.npz', allow_pickle=True)
        mu_s = torch.tensor(z['mean'], dtype=torch.float32)
        syn = torch.tensor(z['synergies'], dtype=torch.float32)
        sc = torch.tensor(z['scale'], dtype=torch.float32)
        decode = lambda c: torch.clamp(mu_s + (c * sc) @ syn, 0.0, 1.0)
        print(f'  synergy policy: {ACT} coefficients decoded to {int(meta["NMUS"])} muscles')
    links, geoms, floor = foot_sets(m, mujoco)

    print(f'\nGAIT WITNESS — {tag}_policy.pt, {N} randomized starts of {secs:.0f}s\n' + '=' * 74)
    print(f'  contact links: {links}   (proxy threshold {FOOT_Z*100:.0f} cm)\n')

    # pass 1: collect truth + raw foot heights, then CALIBRATE the proxy threshold against truth
    raw = [rollout(m, d, ac, torch, mujoco, links, geoms, floor, secs, s, decode, OBS)
           for s in range(N)]
    T_all = np.concatenate([r[0] for r in raw]); H_all = np.concatenate([r[1] for r in raw])
    cand = np.arange(0.0, 0.121, 0.002)
    scores = [float(((H_all <= c).astype(int) == T_all).mean()) for c in cand]
    best = int(np.argmax(scores)); thresh = float(cand[best])
    print(f'  proxy calibration: best height threshold {thresh*100:.1f} cm '
          f'-> {scores[best]:.1%} agreement with MuJoCo truth (swept 0-12 cm)\n')

    results, agrees = [], []
    for s, (truth, heights, dist, fell, dts) in enumerate(raw):
        proxy = (heights <= thresh).astype(int)
        agree = float((truth == proxy).mean())
        agrees.append(agree)
        tr = {'contact': truth, 'links': links, 'dt_sample': dts, 'distance': dist}
        a = G.analyze(tr)
        results.append((a, tr, dist, fell))
        print(f'  seed {s}: dist {dist:5.2f} m  periodicity {a["periodicity"]:.2f}  '
              f'duty {a["duty_mean"]:.2f}  support_min {a["support_min"]}  '
              f'{"fell @%.1fs" % fell if fell else "stayed up"}   [contact agree {agree:.0%}]')

    # WORST OF N is the honest score
    worst = min(results, key=lambda r: r[0]['periodicity'])
    a, tr, dist, fell = worst
    print('\n' + '-' * 74)
    print(f'  CONTACT DYAD: MuJoCo truth vs geometric proxy agree {np.mean(agrees):.1%} '
          f'(min {np.min(agrees):.0%}) — licenses the proxy for GPU training' if np.mean(agrees) > 0.9
          else f'  CONTACT DYAD: only {np.mean(agrees):.1%} agreement — the proxy threshold needs work')
    print(f'\n  WORST OF {N} (the honest score):')
    print(f'    periodicity  {a["periodicity"]:.2f}   (1.0 = a metronome, 0.0 = no cycle at all)')
    print(f'    period       {a["period_s"]:.2f} s')
    print(f'    duty factor  {a["duty_mean"]:.2f}   feet found: {a["n_feet"]}/4')
    print(f'    suspension   {a["suspension_frac"]:.0%}   support_min {a["support_min"]}')
    print(f'    distance     {dist:.2f} m')
    print(f'\n  VERDICT: {a["classification"]}')
    print('\n  HILDEBRAND FOOTFALL (worst seed, # = foot down):')
    C = tr['contact']
    for i, L in enumerate(links):                     # own diagram: gait.py's assumes numeric link ids
        line = ''.join('#' if c else '.' for c in C[:, i])
        print(f'    {L:>7}  |{line}|  duty {C[:, i].mean():.2f}')
    sup = C.sum(axis=1)
    print(f'    {"support":>7}  |' + ''.join(str(min(int(s), 9)) for s in sup) + '|  '
          f'airborne {(sup == 0).mean():.0%}  (a WALK is never airborne)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
