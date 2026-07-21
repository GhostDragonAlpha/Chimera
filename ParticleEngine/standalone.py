"""Chimera Particle Engine — GPU standalone demo. Zero Unreal Engine dependency."""
import sys, time, argparse, numpy as np
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description="Chimera Particle Engine — GPU")
    p.add_argument("--frames", type=int, default=120)
    p.add_argument("--particles", type=int, default=10000)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--width", type=int, default=400)
    p.add_argument("--height", type=int, default=300)
    p.add_argument("--save", action="store_true")
    p.add_argument("--save-every", type=int, default=10)
    p.add_argument("--cam-speed", type=float, default=300.0)
    args = p.parse_args()

    from ParticleEngine.core import ParticleSimulator
    from ParticleEngine.kernels.standard import gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel
    from ParticleEngine.control_vars import default_physics_registry
    from ParticleEngine.camera import FirstPersonCamera
    from ParticleEngine.gpu_pipeline import FullGPUPipeline

    OUT = Path(__file__).resolve().parent / "output"
    OUT.mkdir(exist_ok=True)

    # CPU: configure and spawn particles
    sim = ParticleSimulator(args.particles + 5000)
    reg = default_physics_registry()
    for k in [gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel]:
        sim.add_kernel(k, k.__name__)

    nd = int(args.particles * 0.45); ns = int(args.particles * 0.35)
    na = args.particles - nd - ns
    print(f"Spawning {nd} dust + {ns} sand + {na} atmosphere")
    sim.spawn(nd, 'dust', (-500, -300, 600), 500, mass=0.005, life=-1,
              color=(0.75, 0.68, 0.55, 0.8), size=0.5)
    sim.spawn(ns, 'sand', (300, 200, 700), 400, mass=0.02, life=-1,
              color=(0.9, 0.72, 0.35, 0.9), size=0.4)
    sim.spawn(na, 'atmosphere', (0, 0, 2500), 1000, mass=0.001, life=-1,
              color=(0.5, 0.6, 0.85, 0.08), size=12.0)
    for f in range(10): sim.step(1/60, reg.snapshot())

    # Upload to GPU once
    pipe = FullGPUPipeline()
    pipe.upload(sim._data[:sim.count])

    cam = FirstPersonCamera((200, -600, 300), np.radians(15), np.radians(-10),
                            move_speed=args.cam_speed, sensitivity=0.004)
    cvars = {'gravity': (0, 0, -300), 'wind_vector': (20, 10, 5), 'wind_strength': 0.3,
             'boundary_min': (-5000, -5000, -500), 'boundary_max': (5000, 5000, 5000),
             'boundary_restitution': 0.4, 'accumulation_threshold': 5.0, 'accumulation_rate': 0.05}
    dt = 1.0 / args.fps

    print(f"\n{'='*55}")
    print(f" GPU RENDER — {args.frames} frames @ {args.fps}fps")
    print(f" {args.particles} particles | {args.width}x{args.height}")
    print(f"{'='*55}\n")

    t_start = time.time()
    for f in range(args.frames):
        cam.tick(dyaw=0.5, dpitch=0.0, right=2.0, forward=1.5, dt=dt)
        img = pipe.step_and_render(dt, cvars, cam, cam.params(args.width, args.height))

        if args.save and f % args.save_every == 0:
            from PIL import Image
            Image.fromarray(img).save(OUT / f"frame_{f:04d}.png")

        if f % 30 == 0:
            wt = time.time() - t_start
            print(f"  frame {f:4d}  pos: ({cam.position[0]:6.0f},{cam.position[1]:6.0f},{cam.position[2]:5.0f})  wall: {wt:.1f}s")

    elapsed = time.time() - t_start
    print(f"\n{'='*55}")
    print(f" COMPLETE — {args.frames} frames in {elapsed:.1f}s ({args.frames/elapsed:.0f} FPS)")
    print(f"{'='*55}")

    if args.save:
        from PIL import Image
        Image.fromarray(img).save(OUT / "final_frame.png")
        print(f" Frames saved to {OUT}/")

    return 0

if __name__ == "__main__":
    sys.exit(main())
