"""
LightEngine Barnes-Hut DRAW scaling benchmark.

Builds N non-overlapping grains on a cubic lattice at spacing ~0.05 lu and
times one Barnes-Hut DRAW force evaluation (CPU tree build + GPU traversal)
using the validated theta.  Reports steps/sec, compares to the pairwise
extrapolation from Lane K, and projects wall-clock for 8000-tick prints at
500k and 6.4M grains.

Usage:
    python tools/bench_bh.py

Output:
    LightEngine/output/print_bench_bh_log.txt
    LightEngine/output/bench_bh_report.md
"""

from __future__ import annotations

import math
import os
import sys
import time
import traceback

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from LightEngine import bh_draw
from LightEngine.constants import G, EPS

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "LightEngine", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOG_PATH = os.path.join(OUTPUT_DIR, "print_bench_bh_log.txt")
REPORT_PATH = os.path.join(OUTPUT_DIR, "bench_bh_report.md")

SPACING = 0.05
THETA = bh_draw.DEFAULT_THETA  # validated default (set by tests)
LEAF_SIZE = 16
SIZES = [16384, 65536, 262144, 1048576, 2097152, 4194304]
WARMUP_RUNS = 1
TIME_RUNS = 3
PER_SIZE_TIMEOUT_S = 60.0
OOM_RETRY_WAIT_S = 60.0

# Pairwise extrapolation from Lane K benchmark.
PAIRWISE_COEF = 2.88e4
PAIRWISE_EXP = -0.686


def jittered_lattice(n: int, spacing: float = SPACING,
                     jitter_frac: float = 0.2, seed: int = 42) -> np.ndarray:
    """Non-overlapping grains: cubic lattice plus small jitter."""
    rng = np.random.default_rng(seed)
    side = int(math.ceil(n ** (1.0 / 3.0)))
    pos = []
    for idx in range(n):
        ix = idx % side
        iy = (idx // side) % side
        iz = idx // (side * side)
        p = np.array([ix - side / 2.0, iy - side / 2.0, iz - side / 2.0],
                     dtype=np.float32)
        p += rng.uniform(-jitter_frac, jitter_frac, size=3)
        pos.append(p)
    pos = np.array(pos, dtype=np.float32) * spacing
    pos -= pos.mean(axis=0)
    return pos


def pairwise_steps_per_sec(n: int) -> float:
    """Extrapolated pairwise full-step rate from Lane K."""
    return PAIRWISE_COEF * (n ** PAIRWISE_EXP)


def time_bh_draw(pos: np.ndarray, runs: int) -> tuple[float, int]:
    """
    Return average wall-clock seconds for one BH DRAW evaluation and the
    number of successful runs.  Rebuilds the tree every run.
    """
    total = 0.0
    for _ in range(runs):
        t0 = time.perf_counter()
        bh_draw.compute_draw_bh(pos, theta=THETA, leaf_size=LEAF_SIZE)
        total += time.perf_counter() - t0
    return total / runs, runs


def fit_loglog(ns: list[int], steps_per_sec: list[float]) -> tuple[float, float]:
    """Fit steps/sec = C * N^p and return (p, C)."""
    x = np.log(np.array(ns, dtype=np.float64))
    y = np.log(np.array(steps_per_sec, dtype=np.float64))
    A = np.vstack([x, np.ones_like(x)]).T
    p, log_c = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(p), float(np.exp(log_c))


def run_size(n: int, attempt: int = 0):
    """Benchmark one size with OOM retry logic."""
    pos = jittered_lattice(n)
    try:
        # Warmup.
        bh_draw.compute_draw_bh(pos, theta=THETA, leaf_size=LEAF_SIZE)
        bh_draw.cuda.synchronize()

        t0 = time.perf_counter()
        avg_time, _ = time_bh_draw(pos, TIME_RUNS)
        elapsed = time.perf_counter() - t0
        if elapsed > PER_SIZE_TIMEOUT_S:
            return None, f"timeout: {elapsed:.1f}s > {PER_SIZE_TIMEOUT_S}s"
        steps_per_sec = 1.0 / avg_time
        return steps_per_sec, None
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        if "out of memory" in msg.lower() or "cuda" in msg.lower():
            if attempt == 0:
                print(f"  OOM/cuda error at N={n}; waiting {OOM_RETRY_WAIT_S}s then retrying")
                time.sleep(OOM_RETRY_WAIT_S)
                return run_size(n, attempt=1)
        return None, msg


def main():
    log_lines = []
    write = lambda s: (log_lines.append(s), print(s))

    write("=" * 70)
    write("LightEngine Barnes-Hut DRAW scaling benchmark")
    write(f"G = {G}, EPS = {EPS}, theta = {THETA}, leaf_size = {LEAF_SIZE}")
    write(f"Device: CUDA available = {bh_draw.cuda.is_available()}")
    write(f"Sizes: {SIZES}")
    write(f"Timing {TIME_RUNS} runs after {WARMUP_RUNS} warmup")
    write(f"Per-size timeout: {PER_SIZE_TIMEOUT_S}s")
    write("=" * 70)

    results = []
    for n in SIZES:
        write("")
        write(f"N = {n}")
        try:
            sps, err = run_size(n)
            if err:
                write(f"  ABORT: {err}")
                break
            pairwise_sps = pairwise_steps_per_sec(n)
            speedup = sps / pairwise_sps
            results.append((n, sps, pairwise_sps, speedup))
            write(f"  BH steps/sec    = {sps:.2f}")
            write(f"  Pairwise extrap = {pairwise_sps:.2f}")
            write(f"  Speedup         = {speedup:.2f}x")
        except Exception as e:
            write(f"  FAILED: {e}")
            traceback.print_exc()
            break

    write("")
    write("=" * 70)
    write("Summary table")
    write("=" * 70)
    header = f"{'N':>10} {'BH sps':>14} {'pairwise sps':>14} {'speedup':>10}"
    write(header)
    for n, sps, pair_sps, speedup in results:
        write(f"{n:>10} {sps:>14.2f} {pair_sps:>14.2f} {speedup:>10.2f}")

    if len(results) >= 2:
        ns = [r[0] for r in results]
        sps = [r[1] for r in results]
        p, c = fit_loglog(ns, sps)
        write("")
        write(f"BH log-log fit: steps/sec = {c:.3e} * N^{p:.3f}")

        # Crossover with pairwise extrapolation.
        # c * N^p = PAIRWISE_COEF * N^PAIRWISE_EXP
        # N^(p - PAIRWISE_EXP) = PAIRWISE_COEF / c
        denom = p - PAIRWISE_EXP
        if denom != 0.0:
            crossover = (PAIRWISE_COEF / c) ** (1.0 / denom)
            write(f"Crossover N (BH faster than pairwise extrap): {crossover:.0f}")

        # Projections for 8000-tick prints.
        write("")
        write("8000-tick print projections (DRAW-only, BH):")
        for target in (500000, 6400000):
            pred_sps = c * (target ** p)
            wall_s = 8000.0 / pred_sps
            wall_h = wall_s / 3600.0
            write(f"  N={target:>7}: {pred_sps:.2f} steps/sec -> {wall_s:.1f}s ({wall_h:.2f}h)")

    with open(LOG_PATH, "w", encoding="ascii") as f:
        f.write("\n".join(log_lines) + "\n")
    write("")
    write(f"Log written to {LOG_PATH}")


if __name__ == "__main__":
    main()
