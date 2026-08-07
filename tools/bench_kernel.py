"""
LightEngine kernel scaling benchmark.

Builds N non-overlapping grains on a cubic lattice at spacing ~0.05 lu and
times one velocity-Verlet tick (DRAW + RESISTANCE + velocity-Verlet
integration) on the CUDA path.  Reports steps/sec and a log-log scaling
exponent from the measured points.

Usage:
    python tools/bench_kernel.py

Output:
    LightEngine/output/print_bench_kernel_log.txt
    LightEngine/output/bench_kernel_report.md
"""

from __future__ import annotations

import math
import os
import sys
import time
import traceback

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LightEngine import kernel
from LightEngine.constants import DT, R_WALL

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "LightEngine", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOG_PATH = os.path.join(OUTPUT_DIR, "print_bench_kernel_log.txt")
REPORT_PATH = os.path.join(OUTPUT_DIR, "bench_kernel_report.md")

SPACING = 0.05
SIZES = [512, 1024, 2048, 4096, 8192, 16384]
WARMUP_STEPS = 2
TIME_STEPS = 10
PER_SIZE_TIMEOUT_S = 120.0  # abort if 10 steps exceed this


def make_lattice(n: int, spacing: float = SPACING, jitter: float = 0.0, seed: int = 20260807):
    """Return non-overlapping (N,3) positions on a cubic lattice."""
    rng = np.random.default_rng(seed)
    # cube side length in grains
    side = int(math.ceil(n ** (1.0 / 3.0)))
    positions = []
    for idx in range(n):
        ix = idx % side
        iy = (idx // side) % side
        iz = idx // (side * side)
        p = np.array([ix - side / 2.0, iy - side / 2.0, iz - side / 2.0], dtype=np.float32)
        if jitter > 0.0:
            p += rng.uniform(-jitter, jitter, size=3)
        positions.append(p)
    pos = np.array(positions, dtype=np.float32) * spacing
    # remove net momentum anchor: center at origin
    pos -= pos.mean(axis=0)
    return pos


def time_steps(sim: kernel.VelocityVerlet, steps: int) -> float:
    """Return wall-clock seconds for ``steps`` full velocity-Verlet ticks."""
    start = time.perf_counter()
    for _ in range(steps):
        sim.step(DT)
    if sim.use_cuda:
        kernel.cuda.synchronize()
    return time.perf_counter() - start


def fit_loglog(ns: list[int], steps_per_sec: list[float]) -> tuple[float, float]:
    """Fit steps/sec = C * N^p and return (p, C).  Uses all points."""
    x = np.log(np.array(ns, dtype=np.float64))
    y = np.log(np.array(steps_per_sec, dtype=np.float64))
    A = np.vstack([x, np.ones_like(x)]).T
    p, log_c = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(p), float(np.exp(log_c))


def main():
    log_lines = []
    write = lambda s: (log_lines.append(s), print(s))

    write("=" * 70)
    write("LightEngine kernel scaling benchmark")
    write(f"Device: CUDA available = {kernel.cuda_is_available()}")
    if kernel.cuda_is_available():
        write(f"Device name: {kernel._cuda_device.name.decode('utf-8', errors='replace')}")
    write(f"DT = {DT}, R_WALL = {R_WALL}, lattice spacing = {SPACING}")
    write(f"Sizes: {SIZES}")
    write(f"Timing {TIME_STEPS} steps after {WARMUP_STEPS} warmup steps")
    write(f"Per-size timeout: {PER_SIZE_TIMEOUT_S}s for {TIME_STEPS} steps")
    write("=" * 70)

    results = []
    for n in SIZES:
        write("")
        write(f"N = {n}")
        try:
            pos = make_lattice(n, SPACING)
            vel = np.zeros_like(pos)
            sim = kernel.VelocityVerlet(n, use_cuda=True)
            sim.set_state(pos, vel)
            sim.compute_acceleration()

            # warmup
            for _ in range(WARMUP_STEPS):
                sim.step(DT)
            kernel.cuda.synchronize()

            # timed run
            t0 = time.perf_counter()
            elapsed = time_steps(sim, TIME_STEPS)
            if time.perf_counter() - t0 > PER_SIZE_TIMEOUT_S:
                write(f"  ABORT: {elapsed:.3f}s for {TIME_STEPS} steps exceeds timeout")
                break

            steps_per_sec = TIME_STEPS / elapsed
            sec_per_step = elapsed / TIME_STEPS
            results.append((n, steps_per_sec, sec_per_step))
            write(f"  {TIME_STEPS} steps in {elapsed:.4f}s -> {steps_per_sec:.2f} steps/sec")
            write(f"  {sec_per_step * 1e3:.4f} ms/step")

            # peak memory proxy: none exposed; report array sizes
            bytes_pos_vel = 2 * n * 3 * 4
            bytes_acc_tmp = 2 * n * 3 * 4
            write(f"  host array footprint ~ {(bytes_pos_vel + bytes_acc_tmp) / 1e6:.2f} MB")
        except Exception as e:
            write(f"  FAILED: {e}")
            traceback.print_exc()
            break

    write("")
    write("=" * 70)
    write("Summary table")
    write("=" * 70)
    header = f"{'N':>8} {'steps/sec':>14} {'ms/step':>12}"
    write(header)
    for n, sps, spp in results:
        write(f"{n:>8} {sps:>14.2f} {spp * 1e3:>12.4f}")

    if len(results) >= 2:
        ns = [r[0] for r in results]
        sps = [r[1] for r in results]
        p, c = fit_loglog(ns, sps)
        write("")
        write(f"Log-log fit: steps/sec = {c:.3e} * N^{p:.3f}")

        # extrapolate to 30k and 50k for one 8000-tick print
        for target in (30000, 50000):
            pred_sps = c * (target ** p)
            wall_s = 8000.0 / pred_sps
            wall_h = wall_s / 3600.0
            write(f"N={target}: predicted {pred_sps:.2f} steps/sec -> 8000-tick print = {wall_s:.1f}s ({wall_h:.2f}h)")

    with open(LOG_PATH, "w", encoding="ascii") as f:
        f.write("\n".join(log_lines) + "\n")
    write("")
    write(f"Log written to {LOG_PATH}")

    # Markdown report is written by the caller/analysis step; this script only
    # writes the raw log so the report can include the validated neighbor list.


if __name__ == "__main__":
    main()
