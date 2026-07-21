"""
Demo — run the particle engine headless to verify it works.

Usage:
    python -m ParticleEngine.demo         # 300 frames, 60fps, verbose
    python -m ParticleEngine.demo --frames 600 --fps 30
"""

import sys
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description="Chimera Particle Engine — headless demo.")
    parser.add_argument("--frames", type=int, default=300, help="Simulation frames")
    parser.add_argument("--fps", type=int, default=60, help="Simulation frame rate")
    parser.add_argument("--particles", type=int, default=10000, help="Total particles to spawn")
    parser.add_argument("--no-stats", action="store_true", help="Suppress per-frame stats")
    args = parser.parse_args()

    print(f" Chimera Particle Engine — Demo")
    print(f"   {args.frames} frames @ {args.fps}fps ({args.frames/args.fps:.1f}s sim time)")
    print(f"   {args.particles} particles, headless mode")
    print()

    from ParticleEngine.core import ParticleSimulator
    from ParticleEngine.kernels.standard import (
        gravity_kernel, wind_kernel, ground_collision_kernel,
        accumulation_kernel, box_boundary_kernel, color_lifetime_kernel,
    )
    from ParticleEngine.control_vars import default_physics_registry

    # ── Setup ──
    sim = ParticleSimulator(max_particles=args.particles + 5000)
    reg = default_physics_registry()

    sim.add_kernel(gravity_kernel, "gravity")
    sim.add_kernel(wind_kernel, "wind")
    sim.add_kernel(ground_collision_kernel, "ground_collision")
    sim.add_kernel(box_boundary_kernel, "box_boundary")
    sim.add_kernel(accumulation_kernel, "accumulation")
    sim.add_kernel(color_lifetime_kernel, "color_lifetime")

    # ── Spawn ──
    n_dust = int(args.particles * 0.6)
    n_sand = args.particles - n_dust

    print(f"Spawning {n_dust} dust + {n_sand} sand particles...")
    sim.spawn(
        count=n_dust, type_name="dust",
        position=(0, 0, 500), spread=300.0,
        mass=0.005, life=-1,
        color=(0.7, 0.65, 0.55, 0.7), size=0.5,
        props=(0.0, 20.0, 0, 0),    # prop0=accumulation, prop1=temperature
    )
    sim.spawn(
        count=n_sand, type_name="sand",
        position=(200, 100, 600), spread=250.0,
        mass=0.02, life=-1,
        color=(0.85, 0.68, 0.38, 0.85), size=0.35,
        props=(0.0, 20.0, 0, 0),
    )

    # ── Environment: light gravity, gentle wind ──
    reg.set("gravity", (0.0, 0.0, -490.0))    # Half Earth gravity
    reg.set("wind_vector", (40.0, 15.0, 2.0))
    reg.set("wind_strength", 0.4)
    reg.set("restitution", 0.15)
    reg.set("ground_level", 0.0)
    reg.set("accumulation_rate", 0.03)

    # ── Run ──
    dt = 1.0 / args.fps
    t_start = time.time()

    for frame in range(args.frames):
        sim.step(dt, reg.snapshot())

        if not args.no_stats and frame % 60 == 0:
            s = sim.stats()
            wall_t = time.time() - t_start
            print(
                f"  frame {frame:4d}/{args.frames}  "
                f"active: {s['active']:6d}  "
                f"dust: {s['by_type'].get('dust', 0):5d}  "
                f"sand: {s['by_type'].get('sand', 0):5d}  "
                f"sim_time: {frame*dt:.1f}s  "
                f"wall: {wall_t:.2f}s  "
                f"({frame/(wall_t+0.001):.0f} fps wall)"
            )

    # ── Results ──
    elapsed = time.time() - t_start
    final = sim.stats()

    print()
    print("=" * 50)
    print(" FINAL STATE")
    print(f"  Total particles alive:  {final['active']}")
    print(f"  Dust:                   {final['by_type'].get('dust', 0)}")
    print(f"  Sand:                   {final['by_type'].get('sand', 0)}")
    print(f"  Wall time:              {elapsed:.2f}s")
    print(f"  Sim FPS:                {args.frames/elapsed:.0f} fps")
    print(f"  Particles/sec:          {args.particles * args.frames / elapsed:,.0f}")

    # Check settled particles
    dust_mask = sim.types() == 0  # dust
    sand_mask = sim.types() == 1  # sand
    settled_dust = sim._data[:sim.count, 12][dust_mask].mean()  # avg accumulation
    settled_sand = sim._data[:sim.count, 12][sand_mask].mean()
    print(f"  Avg dust accumulation:  {settled_dust:.4f}")
    print(f"  Avg sand accumulation:  {settled_sand:.4f}")

    # Temperature check
    avg_temp_dust = sim._data[:sim.count, 13][dust_mask].mean()
    avg_temp_sand = sim._data[:sim.count, 13][sand_mask].mean()
    print(f"  Avg dust temperature:   {avg_temp_dust:.1f}")
    print(f"  Avg sand temperature:   {avg_temp_sand:.1f}")
    print("=" * 50)

    if elapsed < 0.5 and args.frames >= 60:
        print()
        print(" Particle engine benchmark passed — sub-second sim for {args.frames} frames.")
        print(" This is Python with NumPy. With Taichi GPU kernels, expect 10-100x more.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
