"""Demo: one genome -> one SDF grid -> physics (GPU) + splats (GPU) from that grid.

Run from repo root:  python ChimeraEngine/demo_sdf_show.py

It drops the genome-grown body, solves contact on the GPU, and emits the render splat
buffer ON the GPU (no host voxel loop). Saves one image per phase to the temp dir so
the demo is visible without a live viewer.
"""
import math
import numpy as np
from core.terrarium import Genome
from sdf_body import body_from_genome, SDFWorld
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera
from master_loop_sdf import MATERIAL_OPTICS, ground_splat_buffer

VOXEL = 0.08
PLANE_Y = 0.0
DT = 1 / 60.0
SUB = 4


def make_body():
    g = Genome.quadruped()
    body = body_from_genome(g, seed=1, voxel_size=VOXEL)
    body.x = np.array([0.0, 6.0, 0.0], dtype=float)
    return body


def build_mat_table():
    names = body.grid._material_names if (body := None) is None else None
    # material names come from the grid; we fill per-call below
    return None


def render(body, world, pipe, cam, out_path):
    vol = world._gpu_vols[0]
    names = body.grid._material_names
    rgba = np.array([list(MATERIAL_OPTICS.get(n, ((0, 0, 0), 0))[0]) +
                    [MATERIAL_OPTICS.get(n, ((0, 0, 0), 0))[1]] for n in names], np.float32)
    if rgba.shape[0] == 0:
        rgba = np.zeros((1, 4), np.float32)
    world._gpu.set_material_table(rgba)
    bbuf = world._gpu.emit_splat_buffer(body, vol)          # <-- GPU emit, 51k splats
    gbuf = ground_splat_buffer(0.0, 50.0)
    buf = np.vstack([bbuf, gbuf]) if bbuf.shape[0] else gbuf
    pipe.upload(np.ascontiguousarray(buf), term="")
    img = pipe.render_from_gpu(cam, cam.params(1024, 760))
    from PIL import Image
    Image.fromarray(img).save(out_path)
    return img, bbuf.shape[0]


def main():
    import os, tempfile

    body = make_body()
    print(f"genome body: {len(body.grid)} stored voxels, mass={body.mass:.1f}")

    world = SDFWorld(bodies=[body], gravity=np.array([0.0, -9.81, 0.0]),
                     dt=DT, substeps=SUB, use_gpu=True, contact_stride=6)
    world.add_ground(half_extent=50.0, y=PLANE_Y)
    print(f"surface splats (stride 1): {body.world_points(1).shape[0]}")

    pipe = FullGPUPipeline(bg=(0.01, 0.01, 0.04))
    cam = FirstPersonCamera(
        position=np.array([-10.0, 7.0, -10.0], np.float32),
        yaw=math.radians(45), pitch=math.radians(-20),
        fov=math.radians(50), near=0.1, far=50.0,
    )

    tmp = tempfile.gettempdir()
    frames = [0, 8, 16, 24, 32, 48]  # key poses: airborne, first contact, settling, rest
    step = 0
    for target in frames:
        while step <= target:
            world.step()
            step += 1
        img, n = render(body, world, pipe, cam, os.path.join(tmp, f"sdf_demo_{target:03d}.png"))
        print(f"  step {step-1:3d}  t={ (step-1)*DT:.2f}s  com_y={body.x[1]:.3f}  "
              f"|v|={np.linalg.norm(body.v):.3f}  splats={n} -> {os.path.join(tmp, f'sdf_demo_{target:03d}.png')}")

    print("\nSaved frames show the same SDF grid as contact shape + render splats.")
    print("Run `python ChimeraEngine/master_loop_sdf.py` for the full 240-step run + verdicts.")


if __name__ == "__main__":
    main()
