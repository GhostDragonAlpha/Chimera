"""Object debug viewer — camera locked on target, orbits at fixed distance."""
import sys, math, time, numpy as np
import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from ParticleEngine.core import ParticleSimulator
from ParticleEngine.control_vars import default_physics_registry
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera
from ParticleEngine.kernels.standard import gravity_kernel, box_boundary_kernel


def look_at(cam, target, orbit_angle, elevation, distance):
    cx = target[0] + math.cos(orbit_angle) * math.cos(elevation) * distance
    cy = target[1] + math.sin(orbit_angle) * math.cos(elevation) * distance
    cz = target[2] + math.sin(elevation) * distance
    cam.position[0] = cx; cam.position[1] = cy; cam.position[2] = cz
    dx = target[0] - cx; dy = target[1] - cy; dz = target[2] - cz
    cam.yaw = math.atan2(dy, dx)
    cam.pitch = math.atan2(dz, math.sqrt(dx*dx + dy*dy))


def build_debug_sphere(sim, center=(0,0,0), radius=200):
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(5000):
        y = 1 - (i/4999)*2
        r_at_y = math.sqrt(1 - y*y)
        th = golden * i
        x = math.cos(th)*r_at_y; z = math.sin(th)*r_at_y
        sim.spawn(1,'dust',(x*radius+center[0], y*radius+center[1], z*radius+center[2]),
                  0, mass=1e9, life=-1,
                  color=(abs(x), abs(y), abs(z), 0.9), size=1.5)
    # ring
    for i in range(1500):
        a = 2*math.pi*i/1500
        sim.spawn(1,'sand',(math.cos(a)*(radius*1.4)+center[0], center[1], math.sin(a)*(radius*1.4)+center[2]),
                  0, mass=1e9, life=-1, color=(0.95, 0.7, 0.2, 0.95), size=1.0)
    # cube wireframe
    s = radius * 1.75
    for i in range(400):
        t = i/400
        if t < 0.125: p = (-s+2*s*t*8, -s, -s)
        elif t < 0.25: p = (s, -s+2*s*(t-0.125)*8, -s)
        elif t < 0.375: p = (s, s, -s+2*s*(t-0.25)*8)
        elif t < 0.5: p = (-s+2*s*(t-0.375)*8, s, s)
        elif t < 0.625: p = (-s, s-2*s*(t-0.5)*8, s)
        elif t < 0.75: p = (-s, -s, s-2*s*(t-0.625)*8)
        elif t < 0.875: p = (-s+2*s*(t-0.75)*8, -s, -s)
        else: p = (s, -s+2*s*(t-0.875)*8, -s)
        sim.spawn(1,'social',(p[0]+center[0], p[1]+center[1], p[2]+center[2]),
                  0, mass=1e9, life=-1, color=(0.2, 1.0, 0.2, 0.85), size=0.7)


def main():
    sim = ParticleSimulator(15000)
    reg = default_physics_registry()
    sim.add_kernel(gravity_kernel, 'g'); sim.add_kernel(box_boundary_kernel, 'b')
    reg.set('gravity', (0,0,0))
    reg.set('boundary_min', (-5000, -5000, -5000))
    reg.set('boundary_max', (5000, 5000, 5000))
    build_debug_sphere(sim)
    for _ in range(5): sim.step(1/60, reg.snapshot())

    pipe = FullGPUPipeline(base_scale=0.8)
    pipe.upload(sim._data[:sim.count])
    cvars = reg.snapshot()
    C = (0, 0, 0)

    fig, ax = plt.subplots(figsize=(8, 8)); plt.ion()
    fig.canvas.manager.set_window_title('Chimera — Object Debug Viewer (close window to quit)')
    W = H = 700
    cam = FirstPersonCamera((0, -800, 0), yaw=math.pi/2, pitch=0)
    p = cam.params(W, H)
    img = pipe.render_from_gpu(cam, p)
    im = ax.imshow(img); ax.axis('off')
    txt = ax.text(10, 20, '', color='white', fontsize=11, bbox=dict(facecolor='black', alpha=0.5))
    ax.set_title('Object Debug Viewer — camera locked on target, orbiting')

    print(f"  {pipe._n} particles | Sphere + Ring + Cube wireframe")
    print(f"  Camera always locked on center. Close window to quit.\n")

    times, angle, running = [], 0, True
    def on_close(e):
        nonlocal running; running = False
    fig.canvas.mpl_connect('close_event', on_close)

    while running:
        t0 = time.time()
        angle += 0.008
        el = 0.3 * math.sin(angle * 0.5)
        look_at(cam, C, angle, el, 800)
        pipe.step_particles(1/60, cvars)
        img = pipe.render_from_gpu(cam, cam.params(W, H))
        im.set_data(img)
        times.append(time.time() - t0)
        if len(times) > 30: times.pop(0)
        fps = len(times) / sum(times) if times else 0
        txt.set_text(f'FPS: {fps:.0f} | {pipe._n} splats | orbit={angle:.1f}rad')
        fig.canvas.draw_idle()
        plt.pause(0.001)

    plt.close()
    print("Closed.")

if __name__ == "__main__":
    main()
