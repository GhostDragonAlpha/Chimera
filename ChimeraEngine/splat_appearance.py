"""splat_appearance.py -- THE APPEARANCE as a Gaussian-splat MOVIE (beginning -> end), via ParticleEngine.

The mandatory visual test judges the REAL engine render, not a diagram; and a term is a SLICE of the
timeline UNFOLDING, so the appearance is a MOVIE: a particle scene rendered at its BEGINNING (t=0,
dispersed) and its END (settled -- a central attractor draws the body together). Two ends of the
dial. The physics (the agent) owns this; the human side reads it.

Terms with a scene render as splats; terms without one return None (the engine falls back to the
matplotlib placeholder until their scene is authored). Needs the GPU (Numba CUDA) -- rendering is
physics, so it belongs to the same hardware.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# term -> scene spec: a particle body of a colour, drawn together by a central attractor as it evolves.
SCENES = {
    "theStar":        {"type": "atmosphere", "count": 7000, "spread": 55, "size": 3.4,
                       "color": (1.0, 0.93, 0.82, 1.0), "pull": 1.4, "cam": (0.0, -210.0, 26.0)},
    "aPlanet":        {"type": "water", "count": 7000, "spread": 70, "size": 3.0,
                       "color": (0.28, 0.52, 0.78, 1.0), "pull": 1.1, "cam": (0.0, -250.0, 34.0)},
    "thePlanets":     {"type": "dust", "count": 6000, "spread": 120, "size": 2.6,
                       "color": (0.85, 0.55, 0.40, 1.0), "pull": 0.5, "cam": (0.0, -330.0, 60.0)},
    "theSolarSystem": {"type": "atmosphere", "count": 6000, "spread": 140, "size": 2.6,
                       "color": (1.0, 0.9, 0.75, 1.0), "pull": 0.8, "cam": (0.0, -360.0, 70.0)},
}


def project_movie(term: str, out_dir) -> dict | None:
    """Render `term`'s splat movie -> {"begin": path, "end": path}, or None if it has no scene."""
    spec = SCENES.get(term)
    if not spec:
        return None
    import numpy as np
    from PIL import Image
    from ParticleEngine.core import ParticleSimulator, PARTICLE_TYPES
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera
    from ParticleEngine.control_vars import default_physics_registry

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    sim = ParticleSimulator(spec["count"] + 64)
    sim.spawn(spec["count"], spec["type"], position=(0, 0, 0), spread=float(spec["spread"]),
              color=spec["color"], size=float(spec["size"]), life=-1.0)

    pipe = FullGPUPipeline(bg=(0.015, 0.015, 0.04))
    pipe.upload(sim._data[:sim._count])
    # a central attractor draws the body together -- the timeline unfolding from cloud to form
    pipe.attractors.append((0.0, 0.0, 0.0, float(spec["pull"]), PARTICLE_TYPES[spec["type"]], 500.0))
    reg = default_physics_registry()
    reg.set("gravity", (0.0, 0.0, 0.0))                  # SPACE: bodies float, they do not fall out of frame
    reg.set("wind_vector", (0.0, 0.0, 0.0))
    cvars = reg.snapshot()
    cx, cy, cz = spec["cam"]                              # AIM at the body (origin): yaw=0 looks +X, so compute it
    yaw = float(np.arctan2(-cy, -cx))
    pitch = float(np.arctan2(-cz, float(np.hypot(cx, cy))))
    cam = FirstPersonCamera(spec["cam"], yaw=yaw, pitch=pitch)
    p = cam.params(720, 540)

    begin = out / f"movie_{term}_begin.png"
    Image.fromarray(pipe.render_from_gpu(cam, p)).save(begin)
    for _ in range(90):                                  # evolve to the settled END state
        pipe.step_particles(1 / 60, cvars)
    end = out / f"movie_{term}_end.png"
    Image.fromarray(pipe.render_from_gpu(cam, p)).save(end)
    return {"begin": str(begin), "end": str(end)}


if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else "theStar"
    import numpy as np
    from PIL import Image
    m = project_movie(term, Path(__file__).parent / "output")
    for k, v in (m or {}).items():
        arr = np.asarray(Image.open(v))
        print(f"  {k}: {v}  max_rgb={int(arr.max())}")
