"""play_myolegs.py — INTERACTIVE: the space bar is the verb STAND.

The first playable piece of the game's control layer: a live myoLegs body in a real-time window.
The space bar drives the trained standing policy -- press it and the 80 muscles fire to hold the body
up; toggle it off and the muscles go slack and it crumples (a ragdoll). This is a player input wired
straight to a trained behavior: SPACE is not an item, it is the VERB.

    Controls:
      SPACE  toggle STAND (the trained policy) on / off
      R      reset to the standing keyframe (use after a fall)
      ESC    quit (or close the window)

Runs on CPU in a real-time viewer, so it does not touch GPU training. Uses whatever
myolegs_policy.pt currently is -- for the cleanest hold, run it after the deterministic-stand
training finishes. The policy is STOCHASTIC, so it is sampled (a natural, slightly-alive stand);
after entropy annealing the mean would work too.

Run:  python ChimeraEngine/play_myolegs.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
MYOLEGS = HERE.parent / 'vendor' / 'myo_sim' / 'leg' / 'myolegs.xml'
CONTROL_EVERY = 20
KEY_SPACE, KEY_R = 32, 82             # GLFW key codes


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
    import torch, mujoco, mujoco.viewer

    # a stable snapshot of the good stand, immune to training that overwrites myolegs_policy.pt
    pol = HERE / 'myolegs_stand_play.pt'
    mpath = HERE / 'myolegs_stand_play_meta.npy'
    if not pol.exists():                              # fall back to the live policy if no snapshot
        pol, mpath = HERE / 'myolegs_policy.pt', HERE / 'myolegs_meta.npy'
    meta = np.load(mpath, allow_pickle=True).item()
    OBS, HID, ACT = int(meta['OBS']), int(meta['HID']), int(meta['ACT'])
    m = mujoco.MjModel.from_xml_path(str(MYOLEGS))
    d = mujoco.MjData(m); nj = m.nq - 7
    ac = build_ac(OBS, ACT, HID, torch)
    ac.load_state_dict(torch.load(pol, map_location='cpu')); ac.eval()

    def reset():
        mujoco.mj_resetDataKeyframe(m, d, 0)
        d.qpos[7:] += np.random.default_rng().normal(0, 0.02, nj)
        mujoco.mj_forward(m, d)

    reset()
    state = {'stand': True}                            # start standing so the window opens upright

    def key_cb(keycode):
        if keycode == KEY_SPACE:
            state['stand'] = not state['stand']
            print('STAND engaged' if state['stand'] else 'ragdoll (muscles slack)')
        elif keycode == KEY_R:
            reset(); state['stand'] = True; print('reset to standing keyframe (STAND engaged)')

    print(__doc__.split('Run:')[0])
    dt = m.opt.timestep * CONTROL_EVERY
    with mujoco.viewer.launch_passive(m, d, key_callback=key_cb) as viewer:
        while viewer.is_running():
            t0 = time.time()
            if state['stand']:
                ob = torch.tensor(np.nan_to_num(np.concatenate([d.qpos[3:7], d.qvel[3:6], d.qvel[0:3],
                                  d.qpos[7:], d.qvel[6:]])), dtype=torch.float32).unsqueeze(0).clamp(-20, 20)
                with torch.no_grad():
                    mean, std, _v = ac(ob)
                    a = (mean + std * torch.randn_like(std)).clamp(0.0, 1.0)
                d.ctrl[:] = a.squeeze(0).numpy()
            else:
                d.ctrl[:] = 0.0                        # slack muscles -> ragdoll
            for _ in range(CONTROL_EVERY):
                mujoco.mj_step(m, d)
            viewer.sync()
            slack = dt - (time.time() - t0)            # pace to real time
            if slack > 0:
                time.sleep(slack)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
