"""Render a Chimera survival world scene and save to disk."""
import sys, time, numpy as np
from pathlib import Path
from ParticleEngine.core import ParticleSimulator
from ParticleEngine.kernels.standard import (
    gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel,
    temperature_kernel, color_lifetime_kernel)
from ParticleEngine.control_vars import default_physics_registry
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera
from ChimeraEngine.dialectic.world import chimera_survival_world

w = chimera_survival_world()
OUT = Path(__file__).resolve().parents[2] / "ParticleEngine" / "output"   # repo root (moved into rendering/ by the reorg)
OUT.mkdir(exist_ok=True)

print(f"Chimera: {w.name}")
print(f"  Gravity: {w.gravity}  Wind: {w.ambient_wind}")
print(f"  {len(w.spawn_zones)} spawn zones, {len(w.attractors)} attractors")

# Build simulation
sim = ParticleSimulator(sum(sz.count for sz in w.spawn_zones) + 5000)
reg = default_physics_registry()
for k in [gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel,
           temperature_kernel, color_lifetime_kernel]:
    sim.add_kernel(k, k.__name__)

for sz in w.spawn_zones:
    sim.spawn(sz.count, sz.type_name, sz.center, sz.spread,
              mass=sz.mass, life=sz.life, color=sz.color, size=sz.size)
    print(f"  Spawned {sz.count:>5d} {sz.type_name}")

# Settle on CPU first
reg.set("gravity", w.gravity)
reg.set("wind_vector", w.ambient_wind)
for k, v in w.cvars.items():
    reg.set(k, v)

print(f"\nSettling {w.name} for 5s...")
for f in range(300):
    sim.step(1/60, reg.snapshot())

# Upload to GPU
pipe = FullGPUPipeline()
pipe.upload(sim._data[:sim.count])

# Add attractors
from ParticleEngine.core import PARTICLE_TYPES
for a in w.attractors:
    for tname, strength in a.type_affinity.items():
        tcode = PARTICLE_TYPES.get(tname)
        if tcode is not None:
            pipe.attractors.append(
                (a.position[0], a.position[1], a.position[2],
                 strength, tcode, a.radius))
    print(f"  Attractor '{a.label}': {a.type_affinity}")

cvars = reg.snapshot()

# Render from multiple angles
cam = FirstPersonCamera((300, -1200, 600), yaw=np.radians(20), pitch=np.radians(-12))
cam_positions = [
    (300, -1200, 600, 20, -12, "overview"),
    (0, -500, 200, 0, -5, "habitat_approach"),
    (500, -300, 150, -30, -8, "ground_level"),
    (-200, -800, 400, 15, -10, "npc_village_view"),
]

for fx, fy, fz, yaw_d, pitch_d, label in cam_positions:
    cam = FirstPersonCamera((fx, fy, fz), yaw=np.radians(yaw_d), pitch=np.radians(pitch_d))

    # Run a few frames for dynamics
    for _ in range(10):
        pipe.step_particles(1/60, cvars)

    p = cam.params(1024, 768)
    img = pipe.render_from_gpu(cam, p)
    from PIL import Image
    fname = OUT / f"chimera_{label}.png"
    Image.fromarray(img).save(fname)
    print(f"  Saved {fname} ({img.shape[1]}x{img.shape[0]}, max_rgb={img.max()})")

print(f"\nScenes saved to {OUT}/")
