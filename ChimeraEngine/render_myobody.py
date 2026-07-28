"""render_myobody.py — WITNESS the trained FULL-BODY (290-muscle) standing policy.

Rolls the trained myobody policy out on ONE body from the standing keyframe and renders it, so we can
see whether it stands AND whether the arms hang quietly (the test of the process-not-position
principle: their rest position was never commanded, only "be still + don't waste drive"). Network +
observation are byte-for-byte train_myobody's. Samples actions (the policy trains stochastic then
anneals); pass --mean once converged.

Run:  python ChimeraEngine/render_myobody.py [--out myobody_stand] [--mean]
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
            self.mean = nn.Linear(HID, ACT)
            self.v = nn.Linear(HID, 1)
            self.log_std = nn.Parameter(torch.full((ACT,), -0.7))

        def forward(self, o):
            h = self.body(o)
            return self.mean(h), self.log_std.exp(), self.v(h).squeeze(-1)

    return AC()


def main() -> int:
    import torch, mujoco
    from PIL import Image, ImageDraw
    torch.manual_seed(0)

    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'myobody_stand'
    use_mean = '--mean' in sys.argv
    meta = np.load(HERE / 'myobody_meta.npy', allow_pickle=True).item()
    OBS, HID, ACT, STAND_Z = int(meta['OBS']), int(meta['HID']), int(meta['ACT']), float(meta['STAND_Z'])

    m = mujoco.MjModel.from_xml_path(str(MYOBODY))
    m.vis.global_.offheight = 760
    m.vis.global_.offwidth = 520
    d = mujoco.MjData(m); nj = m.nq - 7
    ac = build_ac(OBS, ACT, HID, torch)
    ac.load_state_dict(torch.load(HERE / 'myobody_policy.pt', map_location='cpu')); ac.eval()

    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[7:] += np.random.default_rng(0).normal(0, 0.03, nj)
    mujoco.mj_forward(m, d)

    cam = mujoco.MjvCamera(); mujoco.mjv_defaultCamera(cam)
    cam.distance, cam.elevation, cam.azimuth = 3.6, -8.0, 130.0
    cam.lookat[:] = [0.0, 0.0, 0.9]
    rend = mujoco.Renderer(m, height=720, width=500)

    frames, heights = [], []
    steps = int(3.0 / m.opt.timestep)
    with torch.no_grad():
        for k in range(0, steps, CONTROL_EVERY):
            ob = torch.tensor(np.nan_to_num(np.concatenate([d.qpos[3:7], d.qvel[3:6], d.qvel[0:3],
                              d.qpos[7:], d.qvel[6:]])), dtype=torch.float32).unsqueeze(0).clamp(-20, 20)
            mean, std, _v = ac(ob)
            a = mean if use_mean else mean + std * torch.randn_like(std)
            d.ctrl[:] = a.clamp(0.0, 1.0).squeeze(0).numpy()
            for _ in range(CONTROL_EVERY):
                mujoco.mj_step(m, d)
            pz = float(d.qpos[2]); heights.append(pz)
            cam.azimuth = 130.0 + 20.0 * k / steps
            rend.update_scene(d, cam)
            img = Image.fromarray(rend.render()); dr = ImageDraw.Draw(img)
            dr.rectangle([0, 0, 500, 60], fill=(8, 10, 18))
            good = pz > 0.7
            dr.text((12, 8), f't = {k*m.opt.timestep:4.2f}s   full-body 290-muscle standing policy',
                    fill=(210, 220, 240))
            dr.text((12, 32), f'root {pz:4.2f} m   (keyframe {STAND_Z:.2f})   '
                              f'{"STANDING" if good else "..."}',
                    fill=(120, 230, 160) if good else (240, 170, 120))
            frames.append(img)

    gif = HERE.parent / f'{out}.gif'
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=70, loop=0)
    png = HERE.parent / f'{out}.png'
    grid = Image.new('RGB', (500 * 2, 720 * 2), (8, 10, 18))
    for idx, fi in enumerate([0, len(frames) // 3, 2 * len(frames) // 3, len(frames) - 1]):
        grid.paste(frames[fi], (500 * (idx % 2), 720 * (idx // 2)))
    grid.save(png)
    print(f'  root start {heights[0]:.2f} m -> end {heights[-1]:.2f} m   (keyframe standing {STAND_Z:.2f})')
    print(f'  wrote {gif.name} and {png.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
