"""Chimera Engine — animated GPU particle viewer (matplotlib)."""
import sys, time, argparse, numpy as np
import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from ParticleEngine.core import ParticleSimulator
from ParticleEngine.kernels.standard import gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel
from ParticleEngine.control_vars import default_physics_registry
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--particles", type=int, default=10000)
    p.add_argument("--width", type=int, default=800)
    p.add_argument("--height", type=int, default=600)
    args = p.parse_args()

    # Init simulation
    sim = ParticleSimulator(args.particles + 5000)
    reg = default_physics_registry()
    for k in [gravity_kernel, wind_kernel, box_boundary_kernel, accumulation_kernel]:
        sim.add_kernel(k, k.__name__)
    nd, ns = int(args.particles * 0.45), int(args.particles * 0.35)
    na = args.particles - nd - ns
    print(f"Spawning {nd} dust + {ns} sand + {na} atmosphere")
    sim.spawn(nd, 'dust', (-400, -200, 400), 500, mass=0.005, life=-1,
              color=(0.8, 0.72, 0.55, 0.85), size=0.6)
    sim.spawn(ns, 'sand', (200, 100, 500), 400, mass=0.02, life=-1,
              color=(0.95, 0.75, 0.35, 0.9), size=0.45)
    sim.spawn(na, 'atmosphere', (0, -100, 1200), 1000, mass=0.001, life=-1,
              color=(0.4, 0.5, 0.85, 0.06), size=6.0)
    for _ in range(60): sim.step(1/60, reg.snapshot())

    pipe = FullGPUPipeline(base_scale=0.7)
    pipe.upload(sim._data[:sim.count])
    cvars = {'gravity': (0, 0, -200), 'wind_vector': (8, 4, 2), 'wind_strength': 0.2,
             'boundary_min': (-5000, -5000, -500), 'boundary_max': (5000, 5000, 5000),
             'boundary_restitution': 0.3, 'accumulation_threshold': 8.0, 'accumulation_rate': 0.08}

    cam = FirstPersonCamera((-300, -800, 350), yaw=np.radians(20), pitch=np.radians(-8))

    fig, ax = plt.subplots(figsize=(args.width/100, args.height/100))
    plt.ion()
    fig.canvas.manager.set_window_title('Chimera Engine — GPU Particle Renderer')

    p = cam.params(args.width, args.height)
    img = pipe.render_from_gpu(cam, p)
    im = ax.imshow(img)
    ax.set_title('Chimera Engine — Animated GPU Render (close window to quit)')
    ax.axis('off')
    fps_text = ax.text(10, 20, '', color='white', fontsize=11,
                       bbox=dict(facecolor='black', alpha=0.5))

    print(f"\n  Window open — {pipe._n} particles @ {args.width}x{args.height}")
    print(f"  Camera auto-flying. Close the window to quit.\n")

    times, running = [], True

    def on_close(event):
        nonlocal running
        running = False
    fig.canvas.mpl_connect('close_event', on_close)

    while running:
        t0 = time.time()
        cam.tick(dyaw=0.3, dpitch=0.1, right=2.0, forward=1.0, dt=1/60)
        pipe.step_particles(1/60, cvars)
        p = cam.params(args.width, args.height)
        img = pipe.render_from_gpu(cam, p)
        im.set_data(img)
        times.append(time.time() - t0)
        if len(times) > 30: times.pop(0)
        fps = len(times) / sum(times) if times else 0
        fps_text.set_text(f'FPS: {fps:.0f} | {pipe._n} particles | '
                          f'({cam.position[0]:.0f}, {cam.position[1]:.0f}, {cam.position[2]:.0f})')
        fig.canvas.draw_idle()
        plt.pause(0.001)

    plt.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
