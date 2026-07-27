"""render_ppo.py — SHOW THE PPO STANDING POLICY holding itself up against gravity.

    "The only thing that's true is the pictures and movies that come out."   -- the operator

train_ppo learns, on the GPU (witnessed by the heat gate at 58 C, 92% util), to imitate the
standing reference: match q=0, stay upright, keep the head high. This rolls that trained policy
out on ONE body under real gravity on the floor and renders it, so "it holds the stand" is
something you can watch instead of a reward number I report.

    ONE BODY, CPU. This is the development side of the split: training runs 65,536 worlds on the
    GPU; witnessing a single body needs no GPU at all. The muscle model, the observation vector and
    the network are byte-for-byte the ones train_ppo used -- build_ac and observe() are copied from
    it, and the weights are its saved ppo_policy.pt -- so the body you watch is the body it trained.

Run:  python ChimeraEngine/render_ppo.py [--out ppo_stand]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from body import ACT_DIM, humanoid                                           # noqa: E402
from mjcf_body import to_mjcf                                                # noqa: E402
from train_gpu import muscle_tables, muscle_torque_gpu                       # noqa: E402

DT = 5e-4
CONTROL_EVERY = 20


def build_ac(OBS, HID, torch):
    """The SAME actor-critic as train_ppo.build_ac -- identical module names so the saved
    state_dict loads exactly. Only the constructor is needed here (we act, we don't train)."""
    import torch.nn as nn

    class AC(nn.Module):
        def __init__(self):
            super().__init__()
            self.body = nn.Sequential(nn.Linear(OBS, HID), nn.Tanh(),
                                      nn.Linear(HID, HID), nn.Tanh())
            self.mean = nn.Linear(HID, ACT_DIM)
            self.v = nn.Linear(HID, 1)
            self.log_std = nn.Parameter(torch.full((ACT_DIM,), -0.7))

        def forward(self, o):
            h = self.body(o)
            return self.mean(h), self.log_std.exp(), self.v(h).squeeze(-1)

    return AC()


def quat_up(q, torch):
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return torch.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], 1)


def main() -> int:
    import torch, mujoco
    from PIL import Image, ImageDraw

    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'ppo_stand'
    dev = 'cpu'
    # --passive zeroes the policy so ONLY the spinal reflex acts: does the pre-configured body stand
    # with no learned control at all? --gain scales the reflex strength to probe how stiff it needs.
    PASSIVE = '--passive' in sys.argv
    GAIN = float(sys.argv[sys.argv.index('--gain') + 1]) if '--gain' in sys.argv else 1.0
    REFLEX = (5.0 * GAIN, 0.4 * GAIN, 0.6)

    meta = np.load(HERE / 'ppo_meta.npy', allow_pickle=True).item()
    OBS, HID, STAND_Z = int(meta['OBS']), int(meta['HID']), float(meta['STAND_Z'])

    h = humanoid(); n = h.tree.n
    m = mujoco.MjModel.from_xml_string(to_mjcf(h, dt=DT, floor=True))
    d = mujoco.MjData(m)
    HEAD = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'head')
    tb = muscle_tables(h, dev, torch)
    q_ref = torch.zeros(n)                            # standing reference for the stretch reflex

    ac = build_ac(OBS, HID, torch)
    ac.load_state_dict(torch.load(HERE / 'ppo_policy.pt', map_location=dev))
    ac.eval()

    # start from the standing reference, with the same small shove train_ppo resets with
    mujoco.mj_resetData(m, d)
    d.qpos[2] = STAND_Z; d.qpos[3] = 1.0
    d.qpos[7:] += np.random.default_rng(0).normal(0, 0.06, n)
    mujoco.mj_forward(m, d)

    cam = mujoco.MjvCamera(); mujoco.mjv_defaultCamera(cam)
    cam.distance, cam.elevation, cam.azimuth = 3.4, -6.0, 120.0
    cam.lookat[:] = [0.0, 0.0, 0.85]
    rend = mujoco.Renderer(m, height=680, width=480)

    frames, heads, ups = [], [], []
    steps = int(2.5 / DT)
    with torch.no_grad():
        for k in range(0, steps, CONTROL_EVERY):
            q = torch.tensor(np.nan_to_num(d.qpos[7:]), dtype=torch.float32).unsqueeze(0)
            qd = torch.tensor(np.nan_to_num(d.qvel[6:]), dtype=torch.float32).unsqueeze(0)
            quat = torch.tensor(np.nan_to_num(d.qpos[3:7]), dtype=torch.float32).unsqueeze(0)
            angvel = torch.tensor(np.nan_to_num(d.qvel[3:6]), dtype=torch.float32).unsqueeze(0)
            up = quat_up(quat, torch)
            ob = torch.nan_to_num(torch.cat([up, angvel, q, qd], 1)).clamp(-20, 20)
            mean, _std, _v = ac(ob)                       # deterministic: act on the mean
            a = torch.zeros(1, ACT_DIM) if PASSIVE else mean.clamp(0.0, 1.0)
            tau = torch.nan_to_num(muscle_torque_gpu(tb, q, qd, a, torch,
                                   q_ref=q_ref, reflex=REFLEX)).clamp(-400, 400)
            d.ctrl[:] = tau.squeeze(0).numpy()
            for _ in range(CONTROL_EVERY):
                mujoco.mj_step(m, d)

            head_z = float(d.xpos[HEAD][2]); heads.append(head_z)
            up_z = float(up[0, 2]); ups.append(up_z)
            cam.azimuth = 120.0 + 22.0 * k / steps
            rend.update_scene(d, cam)
            img = Image.fromarray(rend.render()); dr = ImageDraw.Draw(img)
            dr.rectangle([0, 0, 480, 66], fill=(8, 10, 18))
            dr.text((12, 8), f't = {k*DT:4.2f}s     PPO standing policy  (65,536-world GPU run)',
                    fill=(210, 220, 240))
            good = up_z > 0.7 and head_z > 1.2
            dr.text((12, 30), f'head {head_z:4.2f} m    upright {up_z:+4.2f}    '
                              f'{"STANDING" if good else "..."}',
                    fill=(120, 230, 160) if good else (240, 170, 120))
            w = int(456 * max(0.0, min(1.0, head_z / 1.55)))
            dr.rectangle([12, 56, 12 + w, 61], fill=(120, 230, 160) if good else (240, 170, 120))
            frames.append(img)

    gif = HERE.parent / f'{out}.gif'
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=70, loop=0)
    png = HERE.parent / f'{out}.png'
    grid = Image.new('RGB', (480 * 2, 680 * 2), (8, 10, 18))
    for idx, fi in enumerate([0, len(frames) // 3, 2 * len(frames) // 3, len(frames) - 1]):
        grid.paste(frames[fi], (480 * (idx % 2), 680 * (idx // 2)))
    grid.save(png)
    print(f'  head start {heads[0]:.2f} m -> end {heads[-1]:.2f} m   (1.55 = fully upright)')
    print(f'  upright start {ups[0]:+.2f} -> end {ups[-1]:+.2f}   (1.0 = torso vertical)')
    print(f'  wrote {gif.name} ({len(frames)} frames) and {png.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
