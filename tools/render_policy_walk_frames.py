"""render_policy_walk_frames.py — render the myobody walk policy's gait through OUR splat pipeline.

Six frames across the policy's best measured attempt (the gait witness says it falls at 1.2-1.7 s,
so the frames span 0..1.2 s — the walk it actually has). Mesh -> splat reuses
tools/verify_myo_splat.py's build_body_buffer per frame; rendering is ParticleEngine's
FullGPUPipeline, the engine the game actually draws with.

Run (env per the operator's CUDA notes):
  CUDA_PATH=...v12.8 PATH=+nvvm/bin+bin C:\\Python314\\python.exe tools/render_policy_walk_frames.py
Writes: ChimeraEngine/output/policy_walk_frames_0..5.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
from world import load_body

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'ChimeraEngine'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
MYOBODY = ROOT / 'external' / 'myo_sim' / 'body' / 'myobody.xml'
CONTROL_EVERY = 20
FRAME_TIMES = [0.0, 0.24, 0.48, 0.72, 0.96, 1.20]

NCOLS = 28


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
    import torch
    import mujoco
    from PIL import Image
    from verify_myo_splat import build_body_buffer

    meta = np.load(HERE / 'myobody_walk_meta.npy', allow_pickle=True).item()
    OBS, HID, ACT = int(meta['OBS']), int(meta['HID']), int(meta['ACT'])
    torch.manual_seed(0)
    # rule 20: the instrument must stand in the same world as the thing it judges.
    m, _g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    ac = build_ac(OBS, ACT, HID, torch)
    ac.load_state_dict(torch.load(HERE / 'myobody_walk_policy.pt', map_location='cpu'))
    ac.eval()

    # rollout, snapshotting state at the frame times (seed 0 noise, like the witness's seed 0)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[7:] += np.random.default_rng(0).normal(0, 0.03, m.nq - 7)
    mujoco.mj_forward(m, d)
    snaps = {}
    steps = int(max(FRAME_TIMES) / m.opt.timestep) + CONTROL_EVERY
    with torch.no_grad():
        for k in range(0, steps, CONTROL_EVERY):
            t = k * m.opt.timestep
            for ft in FRAME_TIMES:
                if ft not in snaps and t >= ft:
                    snaps[ft] = (d.qpos.copy(), d.qvel.copy())
            ob = torch.tensor(np.nan_to_num(np.concatenate(
                [d.qpos[3:7], d.qvel[3:6], d.qvel[0:3], d.qpos[7:], d.qvel[6:]])),
                dtype=torch.float32).unsqueeze(0).clamp(-20, 20)
            mean, std, _v = ac(ob)
            a = mean + std * torch.randn_like(std)
            d.ctrl[:] = a.clamp(0.0, 1.0).squeeze(0).numpy()
            for _ in range(CONTROL_EVERY):
                mujoco.mj_step(m, d)
    print(f'  snapshots at {sorted(snaps)}')

    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    out_dir = HERE / 'output'
    for i, ft in enumerate(FRAME_TIMES):
        qp, qv = snaps[ft]
        d.qpos[:] = qp
        d.qvel[:] = qv
        mujoco.mj_forward(m, d)
        buf = build_body_buffer(m, d, MYOBODY, total_grains=60000, seed=5)
        rx, ry = float(qp[0]), float(qp[1])
        campos = (rx + 1.7, ry - 1.9, 1.05)
        target = np.array([rx, ry, 0.95])
        dvec = target - np.array(campos)
        yaw = float(np.arctan2(dvec[1], dvec[0]))
        pitch = float(np.arctan2(dvec[2], float(np.hypot(dvec[0], dvec[1]))))
        cam = FirstPersonCamera(campos, yaw=yaw, pitch=pitch)
        p = cam.params(720, 540)
        pipe.upload(buf)
        img = pipe.render_from_gpu(cam, p)
        out = out_dir / f'policy_walk_frames_{i}.png'
        Image.fromarray(img).save(out)
        print(f'  frame {i} (t={ft:.2f}s, root z={qp[2]:.2f}) -> {out.name}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
