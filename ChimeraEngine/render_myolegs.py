"""render_myolegs.py — WITNESS the trained myoLegs standing policy. Pictures, not numbers.

Rolls the trained 80-muscle policy out on ONE myoLegs body (CPU, full solver) from the standing
keyframe and renders it, so "it holds the stand" is something you watch. The network and observation
are byte-for-byte train_myolegs's, and the weights are its saved myolegs_policy.pt, so the body you
see is the body it trained.

Run:  python ChimeraEngine/render_myolegs.py [--out myolegs_stand]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
MYOLEGS = HERE.parent / 'vendor' / 'myo_sim' / 'leg' / 'myolegs.xml'
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

    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'myolegs_stand'
    meta = np.load(HERE / 'myolegs_meta.npy', allow_pickle=True).item()
    OBS, HID, ACT, STAND_Z = int(meta['OBS']), int(meta['HID']), int(meta['ACT']), float(meta['STAND_Z'])

    m = mujoco.MjModel.from_xml_path(str(MYOLEGS))
    d = mujoco.MjData(m)
    nj = m.nq - 7
    ac = build_ac(OBS, ACT, HID, torch)
    ac.load_state_dict(torch.load(HERE / 'myolegs_policy.pt', map_location='cpu'))
    ac.eval()

    mujoco.mj_resetDataKeyframe(m, d, 0)              # standing keyframe
    d.qpos[7:] += np.random.default_rng(0).normal(0, 0.03, nj)
    mujoco.mj_forward(m, d)

    cam = mujoco.MjvCamera(); mujoco.mjv_defaultCamera(cam)
    cam.distance, cam.elevation, cam.azimuth = 3.0, -8.0, 130.0
    cam.lookat[:] = [0.0, 0.0, 0.8]
    rend = mujoco.Renderer(m, height=680, width=480)

    frames, heights = [], []
    steps = int(3.0 / m.opt.timestep)
    with torch.no_grad():
        for k in range(0, steps, CONTROL_EVERY):
            quat = torch.tensor(np.nan_to_num(d.qpos[3:7]), dtype=torch.float32).unsqueeze(0)
            angv = torch.tensor(np.nan_to_num(d.qvel[3:6]), dtype=torch.float32).unsqueeze(0)
            linv = torch.tensor(np.nan_to_num(d.qvel[0:3]), dtype=torch.float32).unsqueeze(0)
            qj = torch.tensor(np.nan_to_num(d.qpos[7:]), dtype=torch.float32).unsqueeze(0)
            qdj = torch.tensor(np.nan_to_num(d.qvel[6:]), dtype=torch.float32).unsqueeze(0)
            ob = torch.nan_to_num(torch.cat([quat, angv, linv, qj, qdj], 1)).clamp(-20, 20)
            mean, _s, _v = ac(ob)
            d.ctrl[:] = mean.clamp(0.0, 1.0).squeeze(0).numpy()   # 80 muscle activations
            for _ in range(CONTROL_EVERY):
                mujoco.mj_step(m, d)
            pz = float(d.qpos[2]); heights.append(pz)
            cam.azimuth = 130.0 + 20.0 * k / steps
            rend.update_scene(d, cam)
            img = Image.fromarray(rend.render()); dr = ImageDraw.Draw(img)
            dr.rectangle([0, 0, 480, 60], fill=(8, 10, 18))
            good = pz > 0.75
            dr.text((12, 8), f't = {k*m.opt.timestep:4.2f}s   myoLegs 80-muscle standing policy',
                    fill=(210, 220, 240))
            dr.text((12, 32), f'pelvis {pz:4.2f} m   (keyframe {STAND_Z:.2f})   '
                              f'{"STANDING" if good else "..."}',
                    fill=(120, 230, 160) if good else (240, 170, 120))
            frames.append(img)

    gif = HERE.parent / f'{out}.gif'
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=70, loop=0)
    png = HERE.parent / f'{out}.png'
    grid = Image.new('RGB', (480 * 2, 680 * 2), (8, 10, 18))
    for idx, fi in enumerate([0, len(frames) // 3, 2 * len(frames) // 3, len(frames) - 1]):
        grid.paste(frames[fi], (480 * (idx % 2), 680 * (idx // 2)))
    grid.save(png)
    print(f'  pelvis start {heights[0]:.2f} m -> end {heights[-1]:.2f} m   (keyframe standing {STAND_Z:.2f})')
    print(f'  wrote {gif.name} and {png.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
