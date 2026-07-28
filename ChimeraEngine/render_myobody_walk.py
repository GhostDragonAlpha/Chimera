"""render_myobody_walk.py — WITNESS the full-body walking policy, camera tracking the body.

Rolls the trained myobody_walk policy out on one body and renders it with a camera that FOLLOWS the
root, so forward progress is visible and we can see whether it steps (a gait) or lurches. Reports
metres travelled -- the honest number the training's `dist` column hides (it multiplies by alive).

Run:  python ChimeraEngine/render_myobody_walk.py [--out myobody_walk] [--mean]
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


def main() -> int:
    import torch, mujoco
    from PIL import Image, ImageDraw
    torch.manual_seed(0)

    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'myobody_walk'
    use_mean = '--mean' in sys.argv
    meta = np.load(HERE / 'myobody_walk_meta.npy', allow_pickle=True).item()
    OBS, HID, ACT, STAND_Z = int(meta['OBS']), int(meta['HID']), int(meta['ACT']), float(meta['STAND_Z'])

    m = mujoco.MjModel.from_xml_path(str(MYOBODY))
    m.vis.global_.offheight = 760; m.vis.global_.offwidth = 540
    d = mujoco.MjData(m); nj = m.nq - 7
    ac = build_ac(OBS, ACT, HID, torch)
    ac.load_state_dict(torch.load(HERE / 'myobody_walk_policy.pt', map_location='cpu')); ac.eval()

    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[7:] += np.random.default_rng(0).normal(0, 0.03, nj)
    mujoco.mj_forward(m, d)
    q = d.qpos[3:7]
    fwd = np.array([1 - 2 * (q[2]**2 + q[3]**2), 2 * (q[1]*q[2] + q[0]*q[3])])
    head = fwd / (np.linalg.norm(fwd) + 1e-6)
    start_xy = d.qpos[0:2].copy()

    cam = mujoco.MjvCamera(); mujoco.mjv_defaultCamera(cam)
    cam.distance, cam.elevation, cam.azimuth = 4.2, -10.0, 90.0
    rend = mujoco.Renderer(m, height=720, width=520)

    frames, dists = [], []
    steps = int(4.0 / m.opt.timestep)
    fell_at = None
    with torch.no_grad():
        for k in range(0, steps, CONTROL_EVERY):
            ob = torch.tensor(np.nan_to_num(np.concatenate([d.qpos[3:7], d.qvel[3:6], d.qvel[0:3],
                              d.qpos[7:], d.qvel[6:]])), dtype=torch.float32).unsqueeze(0).clamp(-20, 20)
            mean, std, _v = ac(ob)
            a = mean if use_mean else mean + std * torch.randn_like(std)
            d.ctrl[:] = a.clamp(0.0, 1.0).squeeze(0).numpy()
            for _ in range(CONTROL_EVERY):
                mujoco.mj_step(m, d)
            dist = float(np.dot(d.qpos[0:2] - start_xy, head)); dists.append(dist)
            if fell_at is None and d.qpos[2] < 0.6 * STAND_Z:
                fell_at = k * m.opt.timestep
            cam.lookat[:] = [d.qpos[0], d.qpos[1], 0.8]
            rend.update_scene(d, cam)
            img = Image.fromarray(rend.render()); dr = ImageDraw.Draw(img)
            dr.rectangle([0, 0, 520, 60], fill=(8, 10, 18))
            up = d.qpos[2]; walking = up > 0.6 * STAND_Z and dist > 0.2
            dr.text((12, 8), f't={k*m.opt.timestep:4.2f}s   full-body walking policy', fill=(210, 220, 240))
            dr.text((12, 32), f'forward {dist:5.2f} m   root {up:4.2f} m   '
                              f'{"WALKING" if walking else ("fell" if up < 0.6*STAND_Z else "...")}',
                    fill=(120, 230, 160) if walking else (240, 170, 120))
            frames.append(img)

    gif = HERE.parent / f'{out}.gif'
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=60, loop=0)
    png = HERE.parent / f'{out}.png'
    grid = Image.new('RGB', (520 * 2, 720 * 2), (8, 10, 18))
    for idx, fi in enumerate([0, len(frames) // 3, 2 * len(frames) // 3, len(frames) - 1]):
        grid.paste(frames[fi], (520 * (idx % 2), 720 * (idx // 2)))
    grid.save(png)
    peak = max(dists)
    print(f'  forward: peak {peak:.2f} m, ended {dists[-1]:.2f} m'
          + (f'   FELL at {fell_at:.1f}s' if fell_at else '   stayed up 4s'))
    print(f'  wrote {gif.name} and {png.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
