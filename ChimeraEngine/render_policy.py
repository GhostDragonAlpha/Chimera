"""render_policy.py — SHOW IT MOVING.

    "I really do not care for your words anymore. The only thing that's true is the pictures and
     movies that come out."                                  -- the operator, 2026-07-27

Fair. Everything in this engine has been reported as numbers, and numbers are exactly the thing a
reader has to take on trust. This renders the trained policy driving the real body, so the claim
"it moves the limb toward a target" is something you can look at instead of something I assert.

    THE GEOMS ARE VISUAL ONLY. contype/conaffinity 0 so they never collide, and every body already
    carries an explicit <inertial> with the compiler set inertiafromgeom="false" -- verified: the
    model renders with 18 geoms and masses 70.000000000 kg, identical to nine decimals. What you
    are watching is the same body mjcf_witness measured agreeing with our engine to 1e-13 m, not a
    stand-in built for the camera.

Run:  python ChimeraEngine/render_policy.py [--out NAME]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from body import ACT_DIM, humanoid                                           # noqa: E402
from mjcf_body import to_mjcf                                                # noqa: E402

DT, CONTROL_EVERY, HID, REACH = 5e-4, 20, 24, 0.28
SWING = 'forearmL'


def main() -> int:
    import mujoco
    from PIL import Image, ImageDraw

    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'transition'
    h = humanoid()
    n = h.tree.n
    m = mujoco.MjModel.from_xml_string(to_mjcf(h, dt=DT, gravity=(0, 0, 0), visual=True))
    d = mujoco.MjData(m)
    B = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, SWING)
    P = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'pelvis')

    theta = np.load(HERE / 'transition_policy_gpu.npy')
    OBS = 3 + 1 + 3 + n * 2 + 3
    i = 0
    W1 = theta[i:i + OBS * HID].reshape(OBS, HID); i += OBS * HID
    b1 = theta[i:i + HID]; i += HID
    W2 = theta[i:i + HID * ACT_DIM].reshape(HID, ACT_DIM); i += HID * ACT_DIM
    b2 = theta[i:i + ACT_DIM]

    tdir = np.array([1.0, 0.0, 0.3]); tdir /= np.linalg.norm(tdir)
    tgt = tdir * REACH
    rng = np.random.default_rng(11)
    mujoco.mj_resetData(m, d)
    d.qpos[7:] = rng.normal(0, 0.25, n)
    d.qvel[6:] = rng.normal(0, 0.20, n)
    mujoco.mj_forward(m, d)

    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.distance, cam.elevation, cam.azimuth = 2.4, -12.0, 128.0
    cam.lookat[:] = [0.0, 0.0, -0.35]
    rend = mujoco.Renderer(m, height=640, width=820)

    frames, track = [], []
    steps = int(1.4 / DT)
    for k in range(0, steps, CONTROL_EVERY):
        q, qd = d.qpos[7:].copy(), d.qvel[6:].copy()
        tip = d.xpos[B] - d.xpos[P]
        err = tgt - tip
        ob = np.concatenate([np.zeros(3), [9.8], d.qvel[3:6], q, qd, err])
        a = 0.5 * (np.tanh(np.tanh(ob @ W1 + b1) @ W2 + b2) + 1.0)
        for j, pr in enumerate(h.pairs.values()):
            pr.drive(2.0 * a[2 * j] - 1.0, co_contract=a[2 * j + 1] * 0.5)
        d.ctrl[:] = np.nan_to_num(h.tree.muscle_torques()
                                  if False else _tau(h, q, a, n)).clip(-400, 400)
        for _ in range(CONTROL_EVERY):
            mujoco.mj_step(m, d)
        dist = float(np.linalg.norm(tgt - (d.xpos[B] - d.xpos[P])))
        track.append(dist)
        cam.azimuth = 128.0 + 26.0 * k / steps
        rend.update_scene(d, cam)
        img = Image.fromarray(rend.render())
        dr = ImageDraw.Draw(img)
        dr.rectangle([0, 0, 820, 62], fill=(8, 10, 18))
        dr.text((14, 8), f't = {k*DT:4.2f}s     target 0.280 m from the pelvis', fill=(210, 220, 240))
        dr.text((14, 30), f'limb-to-target  {dist:5.3f} m'
                          f'   {"CLOSING" if len(track) > 1 and dist < track[-2] else "":8s}',
                fill=(120, 230, 160) if dist < track[0] else (240, 170, 120))
        w = int(800 * min(1.0, dist / 0.6))
        dr.rectangle([14, 52, 14 + w, 57], fill=(120, 230, 160) if dist < track[0] else (240, 170, 120))
        frames.append(img)

    gif = HERE.parent / f'{out}.gif'
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=70, loop=0)
    png = HERE.parent / f'{out}.png'
    grid = Image.new('RGB', (820 * 2, 640 * 2), (8, 10, 18))
    for idx, fi in enumerate([0, len(frames) // 3, 2 * len(frames) // 3, len(frames) - 1]):
        grid.paste(frames[fi], (820 * (idx % 2), 640 * (idx // 2)))
    grid.save(png)
    print(f'  start {track[0]:.3f} m -> end {track[-1]:.3f} m   closest {min(track):.3f} m')
    print(f'  wrote {gif.name} ({len(frames)} frames) and {png.name}')
    return 0


def _tau(h, q, a, n):
    """The same muscle model, driven from the policy's activations."""
    h.tree.q[:] = q
    return h.tree.muscle_torques()


if __name__ == '__main__':
    raise SystemExit(main())
