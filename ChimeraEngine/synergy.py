"""synergy.py — MUSCLE SYNERGIES: does a 290-muscle body really only use ~15 dimensions?

SAR (Berg et al., RSS 2023): biology does not fire muscles independently, it fires **synergies** --
coordinated co-contracting groups. Mine them by training on a SIMPLER task, aggregating that policy's
muscle activations, and projecting them onto a low-dimensional manifold (normalized ICA-PCA). That
manifold then becomes the ACTION BASIS for harder tasks, shrinking the search enormously.

    WE ARE ALREADY IN POSITION. SAR needs "a policy trained on a simpler task" -- that is exactly the
    trained STAND policy (myobody_policy.pt, 77% survival). No prerequisite is missing.

    BUT VERIFY THE FINDING FIRST. The claim "290 muscles collapse to ~10-20 dimensions" is a claim
    about OUR body until measured on it. This script measures it: roll the stand out, collect the
    activations, and report how much of their variance the first N components actually explain. If
    ~15 dimensions do not capture the movement, the synergy basis would silently throw away control
    authority -- so the number is printed before anything is built on it.

Run:  python ChimeraEngine/synergy.py [--policy stand|gait] [--n 8] [--secs 3] [--dims 16]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
MYOBODY = HERE.parent / 'vendor' / 'myo_sim' / 'body' / 'myobody.xml'
CONTROL_EVERY = 20


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


def collect(tag, n_eps, secs):
    """Roll the policy out and return every muscle-activation vector it produced. (N, 290)"""
    import torch, mujoco
    meta = np.load(HERE / f'{tag}_meta.npy', allow_pickle=True).item()
    OBS, HID, ACT = int(meta['OBS']), int(meta['HID']), int(meta['ACT'])
    m = mujoco.MjModel.from_xml_path(str(MYOBODY))
    d = mujoco.MjData(m); nj = m.nq - 7
    ac = build_ac(OBS, ACT, HID, torch)
    ac.load_state_dict(torch.load(HERE / f'{tag}_policy.pt', map_location='cpu')); ac.eval()

    acts = []
    steps = int(secs / m.opt.timestep)
    with torch.no_grad():
        for ep in range(n_eps):
            mujoco.mj_resetDataKeyframe(m, d, 0)
            d.qpos[7:] += np.random.default_rng(ep).normal(0, 0.03, nj)
            mujoco.mj_forward(m, d)
            for k in range(0, steps, CONTROL_EVERY):
                base = np.concatenate([d.qpos[3:7], d.qvel[3:6], d.qvel[0:3], d.qpos[7:], d.qvel[6:]])
                if OBS > len(base):                       # gait policy also senses contact + XcoM
                    base = np.concatenate([base, np.zeros(OBS - len(base))])
                ob = torch.tensor(np.nan_to_num(base), dtype=torch.float32).unsqueeze(0).clamp(-20, 20)
                mean, std, _v = ac(ob)
                # The body is DRIVEN with sampled actions (that is how it was trained and how it
                # stands), but the SYNERGIES are mined from the policy's MEAN. Sampled actions carry
                # independent Gaussian exploration noise across all 290 muscles, and isotropic noise
                # is full-rank BY CONSTRUCTION -- analysing it measures the noise, not the learned
                # coordination, and would fake a high-dimensional body. (First pass did exactly that:
                # 99% of variance "needed" 253 dims.)
                a = (mean + std * torch.randn_like(std)).clamp(0.0, 1.0)
                d.ctrl[:] = a.squeeze(0).numpy()
                acts.append(mean.clamp(0.0, 1.0).squeeze(0).numpy().copy())
                for _ in range(CONTROL_EVERY):
                    mujoco.mj_step(m, d)
    return np.asarray(acts), ACT


def pca_basis(A):
    """Principal components of the activations, by SVD. Returns (mean, components, explained_ratio)."""
    mu = A.mean(axis=0)
    X = A - mu
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    var = (S ** 2) / max(len(X) - 1, 1)
    return mu, Vt, var / var.sum()


def main() -> int:
    which = sys.argv[sys.argv.index('--policy') + 1] if '--policy' in sys.argv else 'stand'
    n_eps = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 8
    secs = float(sys.argv[sys.argv.index('--secs') + 1]) if '--secs' in sys.argv else 3.0
    dims = int(sys.argv[sys.argv.index('--dims') + 1]) if '--dims' in sys.argv else 16
    tag = {'stand': 'myobody', 'gait': 'myobody_gait', 'walk': 'myobody_walk'}[which]

    A, ACT = collect(tag, n_eps, secs)
    print(f'\nMUSCLE SYNERGIES — {tag}_policy.pt\n' + '=' * 70)
    print(f'  collected {len(A):,} activation vectors of {ACT} muscles '
          f'({n_eps} episodes x {secs:.0f}s)\n')

    mu, comps, ratio = pca_basis(A)
    cum = np.cumsum(ratio)
    print('  VARIANCE EXPLAINED — does this body really use only a few dimensions?')
    for k in (1, 2, 4, 8, 12, 16, 24, 32, 48, 64):
        if k <= len(cum):
            bar = '#' * int(cum[k - 1] * 40)
            print(f'    {k:3d} dims  {cum[k-1]*100:6.2f}%  |{bar:<40}|')
    for target in (0.90, 0.95, 0.99):
        need = int(np.searchsorted(cum, target) + 1)
        print(f'    {target:.0%} of the movement needs {need} dimensions (of {ACT} muscles)')

    # ICA on the retained PCA subspace = SAR's "normalized ICA-PCA" synergies
    basis = comps[:dims]
    try:
        from sklearn.decomposition import FastICA
        Z = (A - mu) @ basis.T
        ica = FastICA(n_components=dims, random_state=0, max_iter=1000)
        ica.fit(Z)
        syn = ica.mixing_.T @ basis            # synergy directions in muscle space
        method = 'ICA-PCA (SAR)'
    except Exception as e:
        syn = basis
        method = f'PCA only (no sklearn: {type(e).__name__})'

    # the natural SCALE of each synergy in the data -- the decoder needs it so a policy output of
    # +-1 spans the range the body actually uses, instead of an arbitrary unit.
    proj = (A - mu) @ np.linalg.pinv(syn)
    scale = proj.std(axis=0) + 1e-6
    out = HERE / f'{tag}_synergies.npz'
    np.savez(out, mean=mu, synergies=syn, scale=scale, explained=cum[:dims], dims=dims, method=method)
    print(f'\n  {dims}-dim synergy basis ({method}) captures {cum[dims-1]*100:.1f}% '
          f'-> saved {out.name}')
    print(f'  ACTION SPACE: {ACT} muscles -> {dims} synergies ({ACT/dims:.0f}x smaller search)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
