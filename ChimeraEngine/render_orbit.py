"""render_orbit.py -- turn a term's Chimera-Engine splat scene into a rotating movie (the world, turning).

Same Gaussian-splat pipeline the Engine proves with (splat_appearance.scene_buffer -> FullGPUPipeline),
just orbited so the operator can SEE it as a real 3D body, not a single still. Stays entirely inside
the Chimera Engine -- no foreign renderer."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import splat_appearance as SA
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera


def main() -> int:
    term = sys.argv[sys.argv.index('--term') + 1] if '--term' in sys.argv else 'theTerrain'
    dist = float(sys.argv[sys.argv.index('--dist') + 1]) if '--dist' in sys.argv else 152.0
    N = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 36
    buf = SA.scene_buffer(term)
    if buf is None:
        print(f'no scene for {term}'); return 1
    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    pipe.upload(buf)
    frames = []
    for i in range(N):
        a = 2.0 * np.pi * i / N
        cam_pos = (dist * np.cos(a), dist * np.sin(a), dist * 0.20)
        cx, cy, cz = cam_pos
        yaw = float(np.arctan2(-cy, -cx)); pitch = float(np.arctan2(-cz, float(np.hypot(cx, cy))))
        cam = FirstPersonCamera(cam_pos, yaw=yaw, pitch=pitch)
        p = cam.params(720, 540)
        frames.append(Image.fromarray(pipe.render_from_gpu(cam, p)))
    out = HERE.parent / f'orbit_{term}.gif'
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=55, loop=0)
    print('wrote', out, f'({N} frames)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
