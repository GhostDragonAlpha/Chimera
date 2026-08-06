"""
THE RUN per docs/THE_KERNEL.md.

N = 4096 identical points, structureless start in a bounded region, fixed seed.
Runs the predicted scenario and prints:
  - per-phase metrics (cluster count, bound mass fraction, edge sharpness)
  - the FALSIFIER VERDICT: PASS / COLLAPSE / DISPERSE / FLICKER
  - numbers behind the verdict

Dumps begin / mid / end frames via ParticleEngine.FullGPUPipeline to
LightEngine/output/.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import os
import numpy as np

from LightEngine import kernel
from LightEngine.constants import G, R_WALL, R_BOND, R_C, DT

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Run parameters (declared once, not tuned between runs) ──────────
N = 4096
SEED = 20260806
BOX = 10.0                 # positions uniformly in [-BOX/2, BOX/2]^3
VEL_SIGMA = 1.0            # structureless Gaussian velocity dispersion

# ── Observation window (derived, not picked — THE_KERNEL.md) ────────
# Run 1 used TOTAL_TICKS=1000 = 0.5 time units = 0.10 t_ff and fired
# DISPERSE on a window too short for the draw to act.  The window is
# derived from the free-fall time of the initial cloud:
#   t_ff = 1/sqrt(G * rho), rho = N / BOX^3
# Declared before this run: observe for T_FF_COUNT free-fall times.
T_FF_COUNT = 10
RHO = N / BOX ** 3
T_FF = 1.0 / math.sqrt(G * RHO)
TOTAL_TICKS = int(math.ceil(T_FF_COUNT * T_FF / DT))
SAMPLE_EVERY = max(1, TOTAL_TICKS // 40)
METRIC_R_INNER = R_BOND * 0.5
METRIC_R_OUTER = R_C

# ── Falsifier thresholds (named before the run) ─────────────────────
COLLAPSE_MAX_CLUSTER_FRAC = 0.95      # one blob swallows >95% of points
DISPERSE_MAX_CLUSTER_FRAC = 0.10      # largest clump < 10% of points at end
DISPERSE_RADIUS_GROWTH = 10.0         # system radius grows >10x initial
FLICKER_CV_THRESHOLD = 0.20           # cluster count CV > 20% in final 25%
BOUND_MASS_PERSISTENCE = 0.15         # bound fraction swing > 15% in final 25%


def structureless_start(n: int, box: float, vel_sigma: float, seed: int):
    """Return (positions, velocities) for a structureless initial state."""
    rng = np.random.default_rng(seed)
    pos = rng.uniform(-box / 2, box / 2, (n, 3)).astype(np.float32)
    vel = rng.normal(0, vel_sigma, (n, 3)).astype(np.float32)
    # remove net momentum so the whole cloud does not drift
    vel -= vel.mean(axis=0)
    return pos, vel


def _union_find(n: int):
    parent = np.arange(n, dtype=np.int32)
    size = np.ones(n, dtype=np.int32)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra = find(a)
        rb = find(b)
        if ra == rb:
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]

    return find, union


def _pairwise_r2(pos: np.ndarray, chunk: int = 512):
    """
    Yield (row_start, row_stop, r2_chunk) squared-distance blocks.

    Chunked so the full N x N matrix is never materialized at once.
    """
    pos64 = pos.astype(np.float64)
    n = pos64.shape[0]
    sq = np.einsum("ij,ij->i", pos64, pos64)
    for lo in range(0, n, chunk):
        hi = min(lo + chunk, n)
        # r2[i,j] = |x_i|^2 + |x_j|^2 - 2 x_i . x_j
        r2 = sq[lo:hi, None] + sq[None, :] - 2.0 * (pos64[lo:hi] @ pos64.T)
        yield lo, hi, r2


def cluster_count_and_sizes(pos: np.ndarray, r_cut: float) -> tuple[int, np.ndarray]:
    """Connected components using the resistance neighbor cutoff r_c."""
    n = pos.shape[0]
    find, union = _union_find(n)
    rc2 = r_cut * r_cut
    for lo, hi, r2 in _pairwise_r2(pos):
        ii, jj = np.nonzero(r2 <= rc2)
        ii = ii + lo
        keep = ii < jj  # each unordered pair once, self excluded
        for a, b in zip(ii[keep], jj[keep]):
            union(int(a), int(b))
    roots = np.array([find(i) for i in range(n)])
    unique, sizes = np.unique(roots, return_counts=True)
    return len(unique), sizes


def bound_mass_fraction(pos: np.ndarray, r_bond: float) -> float:
    """Fraction of particles that have at least one neighbor within r_bond."""
    n = pos.shape[0]
    rb2 = r_bond * r_bond
    bound = np.zeros(n, dtype=bool)
    for lo, hi, r2 in _pairwise_r2(pos):
        hits = (r2 <= rb2)
        # exclude self-hits: row i compares with column i
        for k in range(hi - lo):
            hits[k, lo + k] = False
        bound[lo:hi] = hits.any(axis=1)
    return float(bound.sum()) / n


def edge_sharpness(pos: np.ndarray, r_inner: float, r_outer: float) -> float:
    """
    Mean density inside dense cores vs. density in the surrounding shell,
    using the resistance neighbor list itself.
    """
    n = pos.shape[0]
    ri2 = r_inner * r_inner
    ro2 = r_outer * r_outer
    inner_counts = np.zeros(n, dtype=np.float64)
    outer_counts = np.zeros(n, dtype=np.float64)
    for lo, hi, r2 in _pairwise_r2(pos):
        for k in range(hi - lo):
            r2[k, lo + k] = np.inf  # exclude self
        inner_counts[lo:hi] += (r2 <= ri2).sum(axis=1)
        outer_counts[lo:hi] += ((r2 > ri2) & (r2 <= ro2)).sum(axis=1)
    # only particles that have a dense core contribute to the ratio
    mask = inner_counts > 0
    if not mask.any():
        return 0.0
    core = inner_counts[mask].mean()
    shell = outer_counts[mask].mean()
    return float(core / (shell + 1.0))


def system_radius(pos: np.ndarray) -> float:
    """Max distance from the centroid."""
    c = pos.mean(axis=0)
    return float(np.max(np.linalg.norm(pos - c, axis=1)))


def dump_frame(pos: np.ndarray, path: str, camera_pos=(25.0, 25.0, 25.0)):
    """Render the point set through ParticleEngine and save a PNG."""
    from ParticleEngine.gpu_pipeline import FullGPUPipeline
    from ParticleEngine.camera import FirstPersonCamera

    n = pos.shape[0]
    pipe = FullGPUPipeline(bg=(0.01, 0.01, 0.05), base_scale=0.5)
    buffer = np.zeros((n, 28), dtype=np.float32)
    buffer[:, 0:3] = pos
    buffer[:, 3:6] = 0.0
    buffer[:, 6:9] = 0.0
    buffer[:, 9] = 1.0          # mass
    buffer[:, 10] = -1.0        # immortal
    buffer[:, 11] = 3.0         # SOLID
    buffer[:, 16:19] = 0.9      # color
    buffer[:, 19] = 0.9         # alpha
    buffer[:, 20] = 0.04        # size

    pipe.upload(buffer, term="light_seed")

    cam = FirstPersonCamera(
        position=camera_pos,
        yaw=math.atan2(-camera_pos[1], -camera_pos[0]),
        pitch=math.asin(-camera_pos[2] / max(np.linalg.norm(camera_pos), 1e-6)),
        fov=np.radians(60),
        near=0.1,
        far=1000.0,
    )
    params = cam.params(width=800, height=600)
    img = pipe.render_from_gpu(cam, params)

    try:
        from PIL import Image
        Image.fromarray(img).save(path)
    except Exception as e:
        print(f"[demo_seed] could not save frame: {e}")


def main():
    print("=" * 60)
    print("THE KERNEL — first light-era run")
    print(f"N={N}, seed={SEED}, box={BOX}, dt={DT}, ticks={TOTAL_TICKS}")
    print("=" * 60)

    pos, vel = structureless_start(N, BOX, VEL_SIGMA, SEED)
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.compute_acceleration()

    metrics = {
        "tick": [],
        "clusters": [],
        "max_cluster": [],
        "bound_frac": [],
        "edge": [],
        "radius": [],
        "radiated_energy": [],
        "radiated_power": [],
    }

    # pre-initial frame
    dump_frame(sim.pos.copy(), os.path.join(OUTPUT_DIR, "frame_begin.png"))

    for tick in range(1, TOTAL_TICKS + 1):
        sim.step(DT)
        if tick % SAMPLE_EVERY == 0 or tick == TOTAL_TICKS:
            n_clust, sizes = cluster_count_and_sizes(sim.pos, R_C)
            bound_frac = bound_mass_fraction(sim.pos, R_BOND)
            edge = edge_sharpness(sim.pos, METRIC_R_INNER, METRIC_R_OUTER)
            rad = system_radius(sim.pos)
            metrics["tick"].append(tick)
            metrics["clusters"].append(n_clust)
            metrics["max_cluster"].append(int(sizes.max()))
            metrics["bound_frac"].append(bound_frac)
            metrics["edge"].append(edge)
            metrics["radius"].append(rad)
            metrics["radiated_energy"].append(float(sim.radiated_energy))
            metrics["radiated_power"].append(float(sim.last_radiated_power))
            print(f"tick={tick:6d} | clusters={n_clust:4d} | "
                  f"max={sizes.max():4d} | bound={bound_frac:.3f} | "
                  f"edge={edge:.3f} | radius={rad:.3f} | "
                  f"E_rad={sim.radiated_energy:.4f} | P_rad={sim.last_radiated_power:.4f}")
        if tick == TOTAL_TICKS // 2:
            dump_frame(sim.pos.copy(), os.path.join(OUTPUT_DIR, "frame_mid.png"))

    dump_frame(sim.pos.copy(), os.path.join(OUTPUT_DIR, "frame_end.png"))

    # ── Falsifier verdict ───────────────────────────────────────────
    clusters = np.array(metrics["clusters"], dtype=np.float64)
    bound_fracs = np.array(metrics["bound_frac"], dtype=np.float64)
    radii = np.array(metrics["radius"], dtype=np.float64)
    final_max = metrics["max_cluster"][-1]
    final_bound = bound_fracs[-1]
    initial_radius = radii[0]
    final_radius = radii[-1]

    # final 25% of samples
    q = max(1, len(clusters) // 4)
    late_clusters = clusters[-q:]
    late_bound = bound_fracs[-q:]
    cluster_cv = float(late_clusters.std() / (late_clusters.mean() + 1e-12))
    bound_swing = float(late_bound.max() - late_bound.min())

    verdict = "PASS"
    reasons = []
    if final_max >= N * COLLAPSE_MAX_CLUSTER_FRAC:
        verdict = "COLLAPSE"
        reasons.append(f"max_cluster={final_max} >= {COLLAPSE_MAX_CLUSTER_FRAC*N:.0f}")
    if final_max <= N * DISPERSE_MAX_CLUSTER_FRAC and final_bound < 0.3:
        verdict = "DISPERSE"
        reasons.append(f"max_cluster={final_max} <= {DISPERSE_MAX_CLUSTER_FRAC*N:.0f} and bound_frac={final_bound:.3f}")
    if final_radius > initial_radius * DISPERSE_RADIUS_GROWTH:
        verdict = "DISPERSE"
        reasons.append(f"radius {final_radius:.3f} > {DISPERSE_RADIUS_GROWTH}x initial {initial_radius:.3f}")
    if cluster_cv > FLICKER_CV_THRESHOLD:
        verdict = "FLICKER"
        reasons.append(f"cluster_count CV={cluster_cv:.3f} > {FLICKER_CV_THRESHOLD}")
    if bound_swing > BOUND_MASS_PERSISTENCE:
        verdict = "FLICKER"
        reasons.append(f"bound_frac swing={bound_swing:.3f} > {BOUND_MASS_PERSISTENCE}")

    final_rad_energy = float(metrics["radiated_energy"][-1])
    final_rad_power = float(metrics["radiated_power"][-1])

    print("=" * 60)
    print(f"FALSIFIER VERDICT: {verdict}")
    print(f"  final clusters          = {int(clusters[-1])}")
    print(f"  final max cluster size  = {final_max}")
    print(f"  final bound mass frac   = {final_bound:.4f}")
    print(f"  final system radius     = {final_radius:.4f}")
    print(f"  cluster count CV (late) = {cluster_cv:.4f}")
    print(f"  bound frac swing (late) = {bound_swing:.4f}")
    print(f"  radiated energy         = {final_rad_energy:.4f}")
    print(f"  radiated power          = {final_rad_power:.4f}")
    if reasons:
        print("  reasons:")
        for r in reasons:
            print(f"    - {r}")
    else:
        print("  reasons: none — prediction held")
    print(f"  output frames: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
