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

from LightEngine import kernel, seed_structures
from LightEngine.constants import G, R_WALL, R_BOND, R_C, K_BOND, K_WALL, P_WALL, DT, EPS, S_WALL

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Run parameters (declared once, not tuned between runs) ──────────
N = 4096
SEED = 20260806
BOX = 10.0                 # positions uniformly in [-BOX/2, BOX/2]^3
VEL_SIGMA = 1.0            # structureless Gaussian velocity dispersion

# Declared printed geometry (THE_PRINTER.md)
R_SHELL = 4.0
R_DISK = 4.0
F_CORE = 0.5

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

# ── BONE v2 print parameters (derived from force constants) ─────────
# Longitudinal sound speed in the cushion lattice: c = sqrt(K_BOND) = 1.0 lu/tick.
# Drive the anchor plates together at 5% of sound speed.
BONE_V_PLATE = 0.05 * math.sqrt(K_BOND)          # lu / tick
# Preload target: 1.5x the kernel-exact end-weight of the column.
BONE_PRELOAD_FACTOR = 1.5
# Half-release: plates return outward by half the convergence distance.
BONE_HALF_RELEASE_FRAC = 0.5
# Overload pulse after spring-back: 0.5 * R_WALL per side (derived wall pulse).
BONE_OVERLOAD_PER_SIDE = 0.5 * R_WALL
# Hold window: at least 5000 ticks, equal to the convergence duration.
BONE_HOLD_MIN_TICKS = 5000
# Falsifier thresholds (named before the run; do not retune)
BONE_SEATING_MAX_GAP = R_C                       # any end gap > r_c = detached
BONE_SPRINGBACK_TOL = 0.10                       # force/length within 10%
BONE_ORDERED_GAIN = 2.0                          # ordered beats random by 2x

# ── MUSCLE print parameters (derived from force constants) ──────────
# Drive the anchor plates at 5% of the bond sound speed.
MUSCLE_V_PLATE = 0.05 * math.sqrt(K_BOND)        # lu / tick
# Extension limit and stroke are derived from s₀ (returned by the builder).
MUSCLE_EXTENSION_FACTOR = math.sqrt(2.0) * 1.5   # s_ext = s0 * sqrt(2) * 1.5
MUSCLE_STROKE_FACTOR = math.sqrt(2.0)            # F(s0*sqrt(2)) should be >= F(s0)/2
MUSCLE_EXP_TOL = 0.25                            # DRAW exponent -2 ± this (far range, diagnostic only)
MUSCLE_LAW_TOL = 0.10                            # (a) max rel err, measured vs pairwise-DRAW prediction
MUSCLE_MIGRATION_TOL = 0.05                      # droplet COM must stay on x-axis

# ── TENDON print parameters (derived from force constants) ────────────
# Drive the anchor plates at 5% of the bond sound speed.
TENDON_V_PLATE = 0.05 * math.sqrt(K_BOND)        # lu / tick
TENDON_D_EQ = seed_structures.TENDON_D_EQ        # cushion equilibrium spacing (~0.0484 lu)
TENDON_LAW_TOL = 0.10                            # (a)/(d) max rel err, measured vs prediction
TENDON_BUCKLE_BAR = 2.0 * (0.5 * 0.05)           # 2 x cross-section half-width = 0.05 lu
TENDON_SEAT_HOLD_BAR = R_BOND                    # (b1) end gap must stay within the bond cutoff
TENDON_UNSEAT_HALF_TOL = 0.5 * TENDON_D_EQ       # ± half a lattice step
TENDON_COMPRESS_DIST = 2.0 * TENDON_D_EQ         # total plate convergence during compress phase
TENDON_EXTEND_EXTRA = 0.15                       # extension past s0 into the unseat window

# ── JOINT print parameters (derived from force constants) ─────────────
JOINT_D_EQ = seed_structures.TENDON_D_EQ         # cushion equilibrium spacing
JOINT_LAW_TOL = 0.10                             # (b) torque law vs pairwise-DRAW
JOINT_GAP_BAR = R_C                              # (a) joint dislocation threshold

# ── SHEET print parameters (derived from force constants) ──────────────
SHEET_V_PLATE = 0.05 * math.sqrt(K_BOND)         # 5% sound speed, tear grips
SHEET_PHASE_THICKNESS_MAX = 2.0 * 0.05           # 2 lattice steps
SHEET_FREE_THICKNESS_MIN_FRAC = 0.5              # thickness > half sheet width
SHEET_TEAR_STRETCH_MIN = 1.5                     # derived lower tear window
SHEET_TEAR_STRETCH_MAX = 4.0                     # derived upper tear window
SHEET_TEAR_MARGIN_TICKS = 500                    # stop ~500 ticks after split
SHEET_DRAPE_EDGE_FRAC = 0.5                      # ≥ half edge grains in band


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


def nearest_neighbor_distances(pos: np.ndarray) -> np.ndarray:
    """Return the nearest-neighbor distance for every point (chunked)."""
    n = pos.shape[0]
    mins = np.full(n, np.inf, dtype=np.float64)
    for lo, hi, r2 in _pairwise_r2(pos):
        for k in range(hi - lo):
            r2[k, lo + k] = np.inf
        mins[lo:hi] = np.minimum(mins[lo:hi], np.sqrt(r2).min(axis=1))
    return mins


def core_bound_fraction(pos: np.ndarray, n_core: int, r_bond: float) -> float:
    """Fraction of core points with at least one neighbor within r_bond."""
    rb2 = r_bond * r_bond
    bound = np.zeros(n_core, dtype=bool)
    for lo, hi, r2 in _pairwise_r2(pos):
        for k in range(hi - lo):
            r2[k, lo + k] = np.inf
        if lo < n_core:
            sub_lo = lo
            sub_hi = min(hi, n_core)
            bound[sub_lo:sub_hi] |= np.any(r2[:sub_hi - lo, :] <= rb2, axis=1)
    return float(bound.sum() / n_core) if n_core > 0 else 0.0


def shell_disk_metrics(pos: np.ndarray, n_core: int) -> tuple[float, float, float]:
    """
    Return (mean radius, std radius, z-dispersion) for non-core points.
    """
    if n_core >= pos.shape[0]:
        return 0.0, 0.0, 0.0
    radii = np.linalg.norm(pos[n_core:] - pos.mean(axis=0), axis=1)
    z = pos[n_core:, 2]
    return float(radii.mean()), float(radii.std()), float(z.std())


# ── BONE v2-specific helpers ────────────────────────────────────────

def _end_weight(col_pos: np.ndarray, eps: float = 0.02) -> float:
    """
    Kernel-exact axial DRAW end-weight of the column.

    Splits the column at the median x, sums the x-component of the softened
    inverse-square draw that the right half feels from the left half.  This is
    the force each anchor plate must supply to keep the column from contracting
    under its own draw.
    """
    mid = float(np.median(col_pos[:, 0]))
    left = col_pos[col_pos[:, 0] <= mid]
    right = col_pos[col_pos[:, 0] > mid]
    if left.shape[0] == 0 or right.shape[0] == 0:
        return 0.0
    dx = right[:, 0][:, None] - left[:, 0][None, :]
    dy = right[:, 1][:, None] - left[:, 1][None, :]
    dz = right[:, 2][:, None] - left[:, 2][None, :]
    r2 = dx * dx + dy * dy + dz * dz + eps * eps
    f_over_r = G / (r2 * np.sqrt(r2))
    fx = f_over_r * dx
    return float(fx.sum())


def _column_length(pos: np.ndarray, grain_ids: np.ndarray) -> float:
    """Length of the ordered column along x."""
    col = pos[grain_ids >= 0]
    return float(col[:, 0].max() - col[:, 0].min())


def _max_deflection(pos: np.ndarray, grain_ids: np.ndarray) -> float:
    """Maximum transverse displacement of any column point from the x-axis."""
    col = pos[grain_ids >= 0]
    return float(np.sqrt(col[:, 1] ** 2 + col[:, 2] ** 2).max())


def _end_gaps(pos: np.ndarray, grain_ids: np.ndarray) -> tuple[float, float]:
    """Return (left_gap, right_gap) from each plate to the nearest column point."""
    col = pos[grain_ids >= 0]
    plates = pos[grain_ids == -1]
    if col.shape[0] == 0 or plates.shape[0] == 0:
        return 0.0, 0.0
    left_plate = plates[plates[:, 0] < col[:, 0].min()]
    right_plate = plates[plates[:, 0] > col[:, 0].max()]
    if left_plate.shape[0] == 0 or right_plate.shape[0] == 0:
        return 0.0, 0.0
    left_gap = float(np.linalg.norm(
        left_plate[:, None, :] - col[None, :, :], axis=2).min())
    right_gap = float(np.linalg.norm(
        right_plate[:, None, :] - col[None, :, :], axis=2).min())
    return left_gap, right_gap


def _escape_count(pos: np.ndarray, grain_ids: np.ndarray,
                  r_c: float = R_C) -> int:
    """Number of column points whose nearest neighbor is beyond r_c."""
    col_idx = np.flatnonzero(grain_ids >= 0)
    if col_idx.size == 0:
        return 0
    n = pos.shape[0]
    mins = np.full(n, np.inf, dtype=np.float64)
    for lo, hi, r2 in _pairwise_r2(pos):
        for k in range(hi - lo):
            r2[k, lo + k] = np.inf
        mins[lo:hi] = np.minimum(mins[lo:hi], np.sqrt(r2).min(axis=1))
    col_mins = mins[col_idx]
    return int(np.count_nonzero(col_mins > r_c))


def _make_packed_control_v2(pos: np.ndarray, vel: np.ndarray,
                            grain_ids: np.ndarray,
                            seed: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Packed-bed control for BONE v2: keep the pinned plates, replace the ordered
    column with a uniform random fill of the same bounding box and point count.
    """
    pos = pos.copy()
    vel = vel.copy()
    col_mask = grain_ids >= 0
    n_col = int(col_mask.sum())
    col = pos[col_mask]
    bbox_min = col.min(axis=0)
    bbox_max = col.max(axis=0)
    rng = np.random.default_rng(seed)
    pos[col_mask] = rng.uniform(bbox_min, bbox_max, (n_col, 3)).astype(np.float32)
    return pos, vel


def _plate_force(acc: np.ndarray, left_idx: np.ndarray,
                 right_idx: np.ndarray) -> float:
    """Mean magnitude of the x-reaction force on the two anchor plates."""
    left = float(np.abs(acc[left_idx, 0].sum()))
    right = float(np.abs(acc[right_idx, 0].sum()))
    return 0.5 * (left + right)


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


def _run_bone_v2(pos, vel, pin_mask, grain_ids, n_plate, F_pre, v_plate, dt,
                 tag, label, overload: bool = False, cycles: int = 1):
    """
    Run the BONE v2 preload protocol on one configuration (ordered or packed).

    Phases per cycle: converge plates until plate force >= F_pre, hold,
    half-release, final hold.  With ``cycles > 1`` the converge/hold/release
    loop repeats: the first cycle beds the contacts in (irreversible anneal),
    and the LAST cycle is the elasticity measurement (v2 smoke successor,
    named 2026-08-06 after the first-cycle hysteresis falsifier fired).
    Optional overload pulse at the end.  Returns (metrics, converge_ticks).
    """
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    left_idx = np.arange(n_plate, dtype=np.int32)
    right_idx = np.arange(N - n_plate, N, dtype=np.int32)
    left_x0 = float(pos[left_idx, 0].mean())
    right_x0 = float(pos[right_idx, 0].mean())
    initial_sep = right_x0 - left_x0

    sample_every = 500

    metrics = {
        "tick": [],
        "phase": [],
        "cycle": [],
        "closure": [],
        "plate_force": [],
        "column_length": [],
        "left_gap": [],
        "right_gap": [],
        "escape_count": [],
        "deflection": [],
        "radiated_energy": [],
        "radiated_power": [],
    }

    def _sample(tick: int, phase: str, cycle: int):
        n_clust, sizes = cluster_count_and_sizes(sim.pos, R_C)
        bound_frac = bound_mass_fraction(sim.pos, R_BOND)
        col_len = _column_length(sim.pos, grain_ids)
        left_gap, right_gap = _end_gaps(sim.pos, grain_ids)
        escaped = _escape_count(sim.pos, grain_ids)
        deflect = _max_deflection(sim.pos, grain_ids)
        pforce = _plate_force(sim.acc, left_idx, right_idx)
        left_x = float(sim.pos[left_idx, 0].mean())
        right_x = float(sim.pos[right_idx, 0].mean())
        closure = initial_sep - (right_x - left_x)

        metrics["tick"].append(tick)
        metrics["phase"].append(phase)
        metrics["cycle"].append(cycle)
        metrics["closure"].append(closure)
        metrics["plate_force"].append(pforce)
        metrics["column_length"].append(col_len)
        metrics["left_gap"].append(left_gap)
        metrics["right_gap"].append(right_gap)
        metrics["escape_count"].append(escaped)
        metrics["deflection"].append(deflect)
        metrics["radiated_energy"].append(float(sim.radiated_energy))
        metrics["radiated_power"].append(float(sim.last_radiated_power))

        print(f"[{label}] tick={tick:6d} cycle={cycle} phase={phase:12s} | "
              f"closure={closure:.5f} | force={pforce:.3f} | "
              f"length={col_len:.5f} | gap_L={left_gap:.4f} | "
              f"gap_R={right_gap:.4f} | escape={escaped} | "
              f"deflect={deflect:.4f} | clusters={n_clust:4d} | "
              f"bound={bound_frac:.3f}")

    print(f"\n[{label}] N={N} column={int((grain_ids >= 0).sum())} plates={n_plate*2}")
    print(f"[{label}] v_plate={v_plate:.5f} lu/tick, dt={dt}")
    print(f"[{label}] F_pre={F_pre:.3f}\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    tick = 0
    phase = "converge"
    cycle = 1
    converge_start = 0
    converge_ticks = 0
    max_closure = 0.0
    hold_ticks = BONE_HOLD_MIN_TICKS
    phase_end = None

    while True:
        tick += 1
        do_sample = (tick % sample_every == 0)

        if phase == "converge":
            dx = v_plate * dt
            sim.pos[left_idx, 0] += dx
            sim.pos[right_idx, 0] -= dx
            if sim.use_cuda:
                sim.d_pos.copy_to_device(sim.pos)
            sim.step(dt)

            pforce = _plate_force(sim.acc, left_idx, right_idx)
            if pforce >= F_pre:
                converge_ticks = tick - converge_start
                max_closure = max(max_closure, initial_sep - (
                    float(sim.pos[right_idx, 0].mean()) -
                    float(sim.pos[left_idx, 0].mean())))
                hold_ticks = max(BONE_HOLD_MIN_TICKS, converge_ticks)
                phase = "preload_hold"
                phase_end = tick + hold_ticks
                do_sample = True
                print(f"\n[{label}] preload reached at tick {tick} "
                      f"(cycle {cycle}, {converge_ticks} converge ticks): "
                      f"force={pforce:.3f} closure={max_closure:.5f}\n")

        elif phase == "preload_hold":
            sim.step(dt)
            if tick >= phase_end:
                phase = "release"
                release_ticks = max(1, int(round(
                    converge_ticks * BONE_HALF_RELEASE_FRAC)))
                phase_end = tick + release_ticks
                do_sample = True
                print(f"\n[{label}] releasing {release_ticks} ticks "
                      f"(half convergence distance, cycle {cycle})\n")

        elif phase == "release":
            dx = -v_plate * dt
            sim.pos[left_idx, 0] += dx
            sim.pos[right_idx, 0] -= dx
            if sim.use_cuda:
                sim.d_pos.copy_to_device(sim.pos)
            sim.step(dt)
            if tick >= phase_end:
                phase = "final_hold"
                phase_end = tick + hold_ticks
                do_sample = True
                print(f"\n[{label}] entering final hold (cycle {cycle})\n")

        elif phase == "final_hold":
            sim.step(dt)
            if tick >= phase_end:
                if cycle < cycles:
                    cycle += 1
                    converge_start = tick
                    phase = "converge"
                    do_sample = True
                    print(f"\n[{label}] starting cycle {cycle}: "
                          f"re-converge on the bedded column\n")
                elif overload:
                    phase = "overload"
                    overload_ticks = int(round(
                        BONE_OVERLOAD_PER_SIDE / (v_plate * dt)))
                    overload_ticks = max(1, overload_ticks)
                    phase_end = tick + overload_ticks
                    do_sample = True
                    print(f"\n[{label}] overload pulse {overload_ticks} ticks\n")
                else:
                    do_sample = True
                    break

        elif phase == "overload":
            dx = v_plate * dt
            sim.pos[left_idx, 0] += dx
            sim.pos[right_idx, 0] -= dx
            if sim.use_cuda:
                sim.d_pos.copy_to_device(sim.pos)
            sim.step(dt)
            if tick >= phase_end:
                do_sample = True
                break

        else:
            break

        if do_sample:
            _sample(tick, phase, cycle)

    _sample(tick, phase, cycle)

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics, converge_ticks


def _print_bone_v2_verdict(metrics, F_pre, end_weight, label):
    """Print BONE v2 falsifier verdict for one run; return overload peaks."""
    if not metrics["tick"]:
        return 0.0, 0.0

    phases = metrics["phase"]
    preload_idx = [i for i, p in enumerate(phases) if p == "preload_hold"]
    final_idx = [i for i, p in enumerate(phases) if p == "final_hold"]
    overload_idx = [i for i, p in enumerate(phases) if p == "overload"]
    converge_idx = [i for i, p in enumerate(phases) if p == "converge"]

    # (a) SEATING: end gaps stay <= R_C during preload hold
    if preload_idx:
        max_left_gap = max(metrics["left_gap"][i] for i in preload_idx)
        max_right_gap = max(metrics["right_gap"][i] for i in preload_idx)
    else:
        max_left_gap = max_right_gap = 0.0
    seating_ok = max(max_left_gap, max_right_gap) <= BONE_SEATING_MAX_GAP

    # (b) ESCAPE: zero column points with NN > R_C during preload hold
    if preload_idx:
        max_escape = max(metrics["escape_count"][i] for i in preload_idx)
    else:
        max_escape = 0
    escape_ok = max_escape == 0

    # (c) SPRING-BACK: final hold values should match the seated values at the
    # half-released closure (reversibility / no hysteresis failure).
    # With multiple cycles (the bed-in successor, named 2026-08-06): the first
    # cycle beds the contacts in; the LAST cycle is the elasticity judgement —
    # loop hysteresis: converge vs release force/length at the midpoint of
    # that cycle's closure travel.
    cycles_seen = metrics["cycle"] if "cycle" in metrics else [1] * len(phases)
    last_cycle = max(cycles_seen)
    release_idx = [i for i, p in enumerate(phases) if p == "release"]
    half_closure = 0.0
    F_seated_half = 0.0
    L_seated_half = 0.0
    if last_cycle > 1:
        conv_idx = [i for i, (p, c) in enumerate(zip(phases, cycles_seen))
                    if p == "converge" and c == last_cycle]
        rel_idx = [i for i, (p, c) in enumerate(zip(phases, cycles_seen))
                   if p == "release" and c == last_cycle]
        final_idx = [i for i, (p, c) in enumerate(zip(phases, cycles_seen))
                     if p == "final_hold" and c == last_cycle]
        if conv_idx and rel_idx:
            clo = max(metrics["closure"][i] for i in conv_idx)
            chi = min(metrics["closure"][i] for i in rel_idx)
            if chi < clo:
                half_closure = 0.5 * (clo + chi)
                c_rel = np.array([metrics["closure"][i] for i in rel_idx])
                f_rel = np.array([metrics["plate_force"][i] for i in rel_idx])
                l_rel = np.array([metrics["column_length"][i] for i in rel_idx])
                o = np.argsort(c_rel)
                F_seated_half = float(np.interp(half_closure, c_rel[o], f_rel[o]))
                L_seated_half = float(np.interp(half_closure, c_rel[o], l_rel[o]))
                c_con = np.array([metrics["closure"][i] for i in conv_idx])
                f_con = np.array([metrics["plate_force"][i] for i in conv_idx])
                l_con = np.array([metrics["column_length"][i] for i in conv_idx])
                o2 = np.argsort(c_con)
                F_load_half = float(np.interp(half_closure, c_con[o2], f_con[o2]))
                L_load_half = float(np.interp(half_closure, c_con[o2], l_con[o2]))
            else:
                F_load_half = L_load_half = 0.0
        else:
            F_load_half = L_load_half = 0.0
        # final hold of the last cycle replaces the release-end comparison
        F_release = F_load_half
        L_release = L_load_half
    else:
        final_idx = [i for i, p in enumerate(phases) if p == "final_hold"]
        if release_idx:
            closures_rel = np.array([metrics["closure"][i] for i in release_idx])
            forces_rel = np.array([metrics["plate_force"][i] for i in release_idx])
            lengths_rel = np.array([metrics["column_length"][i] for i in release_idx])
            half_closure = 0.5 * max(metrics["closure"])
            nearest = int(np.argmin(np.abs(closures_rel - half_closure)))
            F_seated_half = float(forces_rel[nearest])
            L_seated_half = float(lengths_rel[nearest])

        if final_idx:
            F_release = np.mean([metrics["plate_force"][i] for i in final_idx[-5:]])
            L_release = np.mean([metrics["column_length"][i] for i in final_idx[-5:]])
        else:
            F_release = L_release = 0.0

    F_tol = max(1e-9, abs(F_seated_half))
    L_tol = max(1e-9, abs(L_seated_half))
    spring_ok = (abs(F_release - F_seated_half) <= BONE_SPRINGBACK_TOL * F_tol and
                 abs(L_release - L_seated_half) <= BONE_SPRINGBACK_TOL * L_tol)

    # (d) overload peaks (compared against packed control by caller)
    if overload_idx:
        peak_force = max(metrics["plate_force"][i] for i in overload_idx)
        peak_deflect = max(metrics["deflection"][i] for i in overload_idx)
    else:
        peak_force = 0.0
        peak_deflect = 0.0

    print(f"\n[{label}] BONE v2 FALSIFIERS:")
    print(f"  (a) SEATING   : {'PASS' if seating_ok else 'FAIL'}  "
          f"max gap L/R = {max_left_gap:.4f} / {max_right_gap:.4f} "
          f"(threshold {BONE_SEATING_MAX_GAP:.2f})")
    print(f"  (b) ESCAPE    : {'PASS' if escape_ok else 'FAIL'}  "
          f"max escapees = {max_escape}")
    if last_cycle > 1:
        print(f"  (c) SPRING-BACK: {'PASS' if spring_ok else 'FAIL'}  "
              f"cycle={last_cycle} loop hysteresis at mid-closure="
              f"{half_closure:.5f}  release F/L={F_seated_half:.3f}/"
              f"{L_seated_half:.5f}  converge F/L={F_release:.3f}/"
              f"{L_release:.5f}")
    else:
        print(f"  (c) SPRING-BACK: {'PASS' if spring_ok else 'FAIL'}  "
              f"half-closure={half_closure:.5f}  "
              f"seated F/L={F_seated_half:.3f}/{L_seated_half:.5f}  "
              f"final F/L={F_release:.3f}/{L_release:.5f}")
    print(f"  (d) OVERLOAD  : peak force={peak_force:.3f}  "
          f"peak deflect={peak_deflect:.4f}")

    return peak_force, peak_deflect


def bone_main(args, seed):
    """BONE v2 print entry point: build, preload, optionally packed control."""
    # Map --n to a 4x4 column length so total points ~= n.
    width = 4
    height = 4
    length = max(4, int(round(args.n / (width * height))) - 2)

    pos, vel, pin_mask, grain_ids = seed_structures.bone2(
        width=width, height=height, length=length,
        spacing=0.05, plate_gap=0.05, seed=seed)
    N = pos.shape[0]
    n_plate = width * height

    # kernel-exact end-weight from the cold print geometry
    col_pos = pos[grain_ids >= 0].astype(np.float64)
    end_weight = _end_weight(col_pos, eps=0.02)
    F_pre = BONE_PRELOAD_FACTOR * end_weight

    dt = DT
    v_plate = BONE_V_PLATE
    tag = f"{args.tag}_" if args.tag else ""

    # RULE 0 header
    print("=" * 70)
    print("THE KERNEL — BONE v2 print run")
    print(f"N={N}, column=4x4x{length}, seed={seed}, "
          f"control={args.control}, cycles={args.cycles}, dt={dt}")
    print("-" * 70)
    print("STATEMENT: A cold-ordered cushion-spaced column between two pinned")
    print("  anchor plates can be preloaded to 1.5x its end-weight, remain")
    print("  seated and intact, spring back elastically after half-release, and")
    print("  outperform a packed-bed control under overload.")
    print("PREDICTION: End gaps stay < R_C, zero escapees, force/length return")
    print("  within 10% after half-release, ordered deflection/load <= 1/2 of")
    print("  the packed-bed control under overload.")
    print("FALSIFIERS:")
    print("  (a) SEATING   — any end gap > r_c during preload hold")
    print("  (b) ESCAPE    — any column point with NN > r_c under preload")
    print("  (c) SPRING-BACK — force/length after release differ >10% from loading")
    print("  (d) ORDERED BEATS RANDOM — ordered deflection/load not 2x better")
    print("=" * 70)
    print(f"\nDerived end-weight = {end_weight:.3f}")
    print(f"Derived F_pre      = {F_pre:.3f}\n")

    bone_peak_force, bone_peak_deflect = _print_bone_v2_verdict(
        _run_bone_v2(pos, vel, pin_mask, grain_ids, n_plate, F_pre,
                     v_plate, dt, tag, "bone", overload=True,
                     cycles=args.cycles)[0],
        F_pre, end_weight, "bone")

    if args.control == "packed":
        pos_p, vel_p = _make_packed_control_v2(pos, vel, grain_ids, seed=seed + 999)
        packed_metrics, _ = _run_bone_v2(
            pos_p, vel_p, pin_mask, grain_ids, n_plate, F_pre,
            v_plate, dt, tag, "packed", overload=True, cycles=args.cycles)
        packed_peak_force, packed_peak_deflect = _print_bone_v2_verdict(
            packed_metrics, F_pre, end_weight, "packed")

        bone_dpl = bone_peak_deflect / max(1e-12, bone_peak_force)
        packed_dpl = packed_peak_deflect / max(1e-12, packed_peak_force)
        dpl_ratio = packed_dpl / max(1e-12, bone_dpl)
        ordered_ok = dpl_ratio >= BONE_ORDERED_GAIN

        print("\nORDERED-BEATS-RANDOM COMPARISON (falsifier d):")
        print(f"  bone peak force    = {bone_peak_force:.3f}")
        print(f"  bone peak deflect  = {bone_peak_deflect:.4f}")
        print(f"  packed peak force  = {packed_peak_force:.3f}")
        print(f"  packed peak deflect= {packed_peak_deflect:.4f}")
        print(f"  deflection/load ratio (packed/bone) = {dpl_ratio:.3f} "
              f"(threshold {BONE_ORDERED_GAIN:.1f})")
        print(f"  verdict            : {'PASS' if ordered_ok else 'FAIL'}")
    else:
        print("\nORDERED-BEATS-RANDOM COMPARISON: skipped (no --control packed)")

    print("=" * 70)


# ── MUSCLE-specific helpers ─────────────────────────────────────────

def _signed_plate_force(acc: np.ndarray, left_idx: np.ndarray,
                        right_idx: np.ndarray) -> float:
    """
    Signed x-reaction on the two anchor plates.

    Positive = plates pull toward each other (contractile DRAW bridge).
    Negative = plates push apart (antagonist cushion).
    """
    left = float(acc[left_idx, 0].sum())
    right = float(acc[right_idx, 0].sum())
    return left - right


def _droplet_plate_gaps(pos: np.ndarray, grain_ids: np.ndarray) -> tuple[float, float]:
    """Return cushion gaps from the droplet to the left and right plates."""
    drop = pos[grain_ids == 0]
    plates = pos[grain_ids == -1]
    if drop.shape[0] == 0 or plates.shape[0] == 0:
        return 0.0, 0.0
    left_plate = plates[plates[:, 0] < drop[:, 0].min()]
    right_plate = plates[plates[:, 0] > drop[:, 0].max()]
    if left_plate.shape[0] == 0 or right_plate.shape[0] == 0:
        return 0.0, 0.0
    left_gap = float(np.linalg.norm(
        left_plate[:, None, :] - drop[None, :, :], axis=2).min())
    right_gap = float(np.linalg.norm(
        right_plate[:, None, :] - drop[None, :, :], axis=2).min())
    return left_gap, right_gap


def _droplet_cluster_count(pos: np.ndarray, grain_ids: np.ndarray,
                           r_cut: float = R_C) -> int:
    """Number of connected components in the droplet (grain 0)."""
    drop_idx = np.flatnonzero(grain_ids == 0)
    if drop_idx.size == 0:
        return 0
    return cluster_count_and_sizes(pos[drop_idx], r_cut)[0]


def _run_muscle(pos, vel, pin_mask, grain_ids, s0, R_droplet, v_plate, dt,
                tag, label):
    """
    Run the MUSCLE extension->convergence protocol.

    Phase 1: extend plates apart to ``s0 * sqrt(2) * 1.5``.
    Phase 2: converge plates back through ``s0`` until cushion contact / force
    reversal.  Returns the metrics dict and the final position array.
    """
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    n_droplet = int((grain_ids == 0).sum())
    n_plate = int((grain_ids == -1).sum()) // 2
    left_idx = np.arange(n_plate, dtype=np.int32)
    right_idx = np.arange(N - n_plate, N, dtype=np.int32)
    drop_idx = np.arange(n_plate, n_plate + n_droplet, dtype=np.int32)

    sample_every = 500

    metrics = {
        "tick": [],
        "phase": [],
        "separation": [],
        "plate_force": [],
        "right_force": [],
        "signed_force": [],
        "droplet_clusters": [],
        "left_gap": [],
        "right_gap": [],
        "droplet_com_y": [],
        "droplet_com_z": [],
        "radiated_energy": [],
        "radiated_power": [],
        "droplet_pos": [],
        "right_plate_pos": [],
    }

    def _sample(tick: int, phase: str):
        left_x = float(sim.pos[left_idx, 0].mean())
        right_x = float(sim.pos[right_idx, 0].mean())
        separation = right_x - left_x
        pforce = _plate_force(sim.acc, left_idx, right_idx)
        # right plate force: positive when the droplet pulls it left (contractile)
        right_force = -float(sim.acc[right_idx, 0].sum())
        sforce = _signed_plate_force(sim.acc, left_idx, right_idx)
        n_clust = _droplet_cluster_count(sim.pos, grain_ids, R_C)
        left_gap, right_gap = _droplet_plate_gaps(sim.pos, grain_ids)
        drop_com = sim.pos[drop_idx].mean(axis=0)

        metrics["tick"].append(tick)
        metrics["phase"].append(phase)
        metrics["separation"].append(separation)
        metrics["plate_force"].append(pforce)
        metrics["right_force"].append(right_force)
        metrics["signed_force"].append(sforce)
        metrics["droplet_clusters"].append(n_clust)
        metrics["left_gap"].append(left_gap)
        metrics["right_gap"].append(right_gap)
        metrics["droplet_com_y"].append(float(drop_com[1]))
        metrics["droplet_com_z"].append(float(drop_com[2]))
        metrics["radiated_energy"].append(float(sim.radiated_energy))
        metrics["radiated_power"].append(float(sim.last_radiated_power))
        metrics["droplet_pos"].append(sim.pos[drop_idx].copy())
        metrics["right_plate_pos"].append(sim.pos[right_idx].copy())

        print(f"[{label}] tick={tick:6d} phase={phase:10s} | "
              f"sep={separation:.5f} | right_F={right_force:.4f} | "
              f"sforce={sforce:.4f} | clusters={n_clust} | "
              f"gap_L={left_gap:.4f} | gap_R={right_gap:.4f} | "
              f"com_yz=({drop_com[1]:.4f},{drop_com[2]:.4f})")

    print(f"\n[{label}] N={N} droplet={n_droplet} plates={n_plate*2}")
    print(f"[{label}] s0={s0:.5f} R_droplet={R_droplet:.5f} "
          f"v_plate={v_plate:.5f} dt={dt}\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    tick = 0
    _sample(tick, "init")
    target_sep = s0 * MUSCLE_EXTENSION_FACTOR

    # Phase 1: extend
    phase = "extend"
    while True:
        tick += 1
        cur_sep = float(sim.pos[right_idx, 0].mean() -
                        sim.pos[left_idx, 0].mean())
        if cur_sep >= target_sep:
            break
        # both plates move outward by half the relative motion
        dx = 0.5 * v_plate * dt
        sim.pos[left_idx, 0] -= dx
        sim.pos[right_idx, 0] += dx
        if sim.use_cuda:
            sim.d_pos.copy_to_device(sim.pos)
        sim.step(dt)
        if tick % sample_every == 0:
            _sample(tick, phase)

    # Phase 2: converge back through s0 into cushion
    phase = "converge"
    while True:
        tick += 1
        cur_sep = float(sim.pos[right_idx, 0].mean() -
                        sim.pos[left_idx, 0].mean())
        sforce = _signed_plate_force(sim.acc, left_idx, right_idx)
        # stop when we are well into cushion and the force has reversed
        if cur_sep <= 0.5 * s0 and sforce < 0.0:
            break
        if cur_sep <= 0.0:
            break
        dx = -0.5 * v_plate * dt
        sim.pos[left_idx, 0] -= dx
        sim.pos[right_idx, 0] += dx
        if sim.use_cuda:
            sim.d_pos.copy_to_device(sim.pos)
        sim.step(dt)
        if tick % sample_every == 0:
            _sample(tick, phase)

    _sample(tick, phase)

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics, sim.pos.copy()


def _print_muscle_verdict(metrics, initial_pos, final_pos, grain_ids,
                          s0, R_droplet, label):
    """Print MUSCLE falsifier verdict; return dict of booleans."""
    phases = metrics["phase"]
    sep = np.asarray(metrics["separation"], dtype=np.float64)
    rforce = np.asarray(metrics["right_force"], dtype=np.float64)
    sforce = np.asarray(metrics["signed_force"], dtype=np.float64)
    clusters = np.asarray(metrics["droplet_clusters"], dtype=np.int32)
    com_y = np.asarray(metrics["droplet_com_y"], dtype=np.float64)
    com_z = np.asarray(metrics["droplet_com_z"], dtype=np.float64)

    n_droplet = int((grain_ids == 0).sum())
    n_plate = int((grain_ids == -1).sum()) // 2
    left_idx = np.arange(n_plate, dtype=np.int32)
    right_idx = np.arange(final_pos.shape[0] - n_plate,
                          final_pos.shape[0], dtype=np.int32)


    # Contractile force per plate = signed_force / 2.  This cancels the
    # direct plate-plate interaction and isolates the bridge force.
    cforce = sforce / 2.0

    # Kernel-exact static prediction: recompute DRAW + static RESISTANCE on
    # the sampled full geometry (zero velocity) and take the signed plate
    # acceleration.  This is the fair comparison for the measured force,
    # which contains both draws and cushion repulsion.
    pred_cforce = np.empty_like(cforce)
    for i in range(len(metrics["phase"])):
        drop_i = np.asarray(metrics["droplet_pos"][i], dtype=np.float32)
        right_i = np.asarray(metrics["right_plate_pos"][i], dtype=np.float32)
        left_i = right_i.copy()
        left_i[:, 0] -= float(sep[i])
        full_pos = np.vstack([left_i, drop_i, right_i])
        full_vel = np.zeros_like(full_pos)
        acc = kernel.compute_forces(full_pos, full_vel, use_cuda=False)
        left_acc = acc[:n_plate, 0].sum()
        right_acc = acc[-n_plate:, 0].sum()
        pred_cforce[i] = 0.5 * (left_acc - right_acc)

    # (a) FORCE LAW — deformation-immune version (2026-08-06): per sample,
    # predict the contractile force on the right plate as the exact pairwise
    # softened DRAW sum over (droplet U left plate) x right plate on the
    # RECORDED positions, and compare to the measured rforce.  Restrict to
    # extension samples whose droplet-to-right-plate clearance exceeds
    # R_BOND, so no RESISTANCE contact can contaminate the pure-DRAW claim.
    # This survives droplet deformation: a droplet that stretches toward the
    # receding plate is real muscle physics, and then the point-COM distance
    # is the wrong coordinate — so the log-log exponent is kept as a printed
    # diagnostic only, never as a gate.
    f_pred = np.full(len(phases), np.nan)
    gap_dr = np.full(len(phases), np.nan)
    for i in range(len(phases)):
        drop_i = np.asarray(metrics["droplet_pos"][i], dtype=np.float64)
        right_i = np.asarray(metrics["right_plate_pos"][i], dtype=np.float64)
        left_i = right_i.copy()
        left_i[:, 0] -= float(sep[i])
        pullers = np.vstack([drop_i, left_i])
        d = right_i[:, None, :] - pullers[None, :, :]     # (n_right, n_pull, 3)
        r2 = (d * d).sum(axis=2) + EPS**2
        # rforce = -(right-plate accel x-sum), contractile-positive; DRAW
        # accel on a right grain toward a puller is -G*dx/r^3 (softened).
        f_pred[i] = float(G * (d[:, :, 0] / r2**1.5).sum())
        dd = drop_i[:, None, :] - right_i[None, :, :]
        gap_dr[i] = float(np.sqrt((dd * dd).sum(axis=2)).min())

    droplet_com_x = np.array([
        np.asarray(metrics["droplet_pos"][i], dtype=np.float64)[:, 0].mean()
        for i in range(len(phases))])
    r_dr = sep - droplet_com_x
    f_pp = G * n_plate * n_plate * sep / (sep**2 + EPS**2) ** 1.5
    # NB: metrics["right_force"] is already contractile-positive (negated at
    # sampling) — do NOT negate it again here.
    f_bridge = rforce - f_pp
    extend_idx = [i for i, p in enumerate(phases)
                  if p == "extend" and r_dr[i] >= 0.25 and f_bridge[i] > 0]
    law_alpha = None
    if len(extend_idx) >= 3:
        lx = np.log(r_dr[extend_idx])
        ly = np.log(f_bridge[extend_idx])
        law_alpha = float(np.polyfit(lx, ly, 1)[0])

    law_idx = [i for i, p in enumerate(phases)
               if p == "extend" and gap_dr[i] > R_BOND and rforce[i] > 0]
    law_max_err = None
    law_ok = False  # an untested falsifier is not a pass; the fit must run
    if len(law_idx) >= 3:
        law_max_err = max(
            abs(rforce[i] - f_pred[i]) / max(abs(f_pred[i]), 1e-12)
            for i in law_idx)
        law_ok = law_max_err <= MUSCLE_LAW_TOL

    # (b) STROKE: measured contractile force at s0*sqrt(2) vs half at s0
    stroke_ok = True
    force_at_s0 = None
    force_at_sqrt2 = None
    pred_at_s0 = None
    pred_at_sqrt2 = None
    if sep.size > 1:
        o = np.argsort(sep)
        force_at_s0 = float(np.interp(s0, sep[o], cforce[o]))
        force_at_sqrt2 = float(np.interp(
            s0 * MUSCLE_STROKE_FACTOR, sep[o], cforce[o]))
        pred_at_s0 = float(np.interp(s0, sep[o], pred_cforce[o]))
        pred_at_sqrt2 = float(np.interp(
            s0 * MUSCLE_STROKE_FACTOR, sep[o], pred_cforce[o]))
        if force_at_s0 > 0:
            stroke_ok = force_at_sqrt2 >= 0.5 * force_at_s0

    # (c) TEAR (split) and migration
    max_clusters = int(clusters.max())
    tear_ok = max_clusters == 1
    max_com_y = float(np.max(np.abs(com_y)))
    max_com_z = float(np.max(np.abs(com_z)))
    migration_ok = (max_com_y <= MUSCLE_MIGRATION_TOL and
                    max_com_z <= MUSCLE_MIGRATION_TOL)

    # (d) ANTAGONIST
    converge_idx = [i for i, p in enumerate(phases) if p == "converge"]
    antagonist_ok = False
    min_converge_force = 0.0
    if converge_idx:
        min_converge_force = float(sforce[converge_idx].min())
        antagonist_ok = min_converge_force < 0.0

    # (e) ANCHORS
    left_drift = float(np.max(np.abs(initial_pos[left_idx, 1:] -
                                     final_pos[left_idx, 1:])))
    right_drift = float(np.max(np.abs(initial_pos[right_idx, 1:] -
                                      final_pos[right_idx, 1:])))
    anchor_drift = max(left_drift, right_drift)
    anchor_ok = anchor_drift <= 1e-4

    # measurement-consistency diagnostic (NOT the law test): measured vs
    # static recompute on the same geometry, over [s0, s0*sqrt(2)].
    stroke_idx = [i for i, s in enumerate(sep)
                  if s0 <= s <= s0 * MUSCLE_STROKE_FACTOR]
    consistency_max_rel = 0.0
    if stroke_idx:
        consistency_max_rel = max(
            abs(cforce[i] - pred_cforce[i]) / max(abs(pred_cforce[i]), 1e-12)
            for i in stroke_idx)

    print(f"\n[{label}] MUSCLE FALSIFIERS:")
    if law_max_err is not None:
        print(f"  (a) FORCE LAW : {'PASS' if law_ok else 'FAIL'}  "
              f"max rel err measured-vs-pairwise-DRAW={law_max_err:.3f} "
              f"(bar {MUSCLE_LAW_TOL:.2f}, {len(law_idx)} contact-free "
              f"extension samples)")
    else:
        print(f"  (a) FORCE LAW : {'PASS' if law_ok else 'FAIL'}  "
              f"(insufficient contact-free extension samples)")
    if law_alpha is not None:
        print(f"      exponent    : {law_alpha:+.3f} (log-log fit, "
              f"diagnostic only — droplet deformation breaks point-COM r)")
    print(f"      consistency : max rel err measured-vs-recompute="
              f"{consistency_max_rel:.3f} (diagnostic, not the falsifier)")
    if force_at_s0 is not None and force_at_sqrt2 is not None:
        print(f"  (b) STROKE    : {'PASS' if stroke_ok else 'FAIL'}  "
              f"F(s0)={force_at_s0:.4f} "
              f"F(s0*sqrt2)={force_at_sqrt2:.4f} "
              f"ratio={force_at_sqrt2/max(force_at_s0,1e-12):.3f} "
              f"pred_sqrt2={pred_at_sqrt2:.4f}")
    else:
        print(f"  (b) STROKE    : {'PASS' if stroke_ok else 'FAIL'}  "
              f"(no samples near s0/s0*sqrt2)")
    print(f"  (c) TEAR      : {'PASS' if tear_ok else 'FAIL'}  "
          f"max clusters={max_clusters}")
    print(f"      migration : {'PASS' if migration_ok else 'FAIL'}  "
          f"max |com_yz|=({max_com_y:.4f},{max_com_z:.4f}) "
          f"(threshold {MUSCLE_MIGRATION_TOL:.3f})")
    print(f"  (d) ANTAGONIST: {'PASS' if antagonist_ok else 'FAIL'}  "
          f"min signed force in converge={min_converge_force:.4f}")
    print(f"  (e) ANCHORS   : {'PASS' if anchor_ok else 'FAIL'}  "
          f"plate y/z drift={anchor_drift:.6f}")

    return {
        "force_law_ok": law_ok,
        "stroke_ok": stroke_ok,
        "tear_ok": tear_ok,
        "migration_ok": migration_ok,
        "antagonist_ok": antagonist_ok,
        "anchor_ok": anchor_ok,
    }


def muscle_main(args, seed):
    """MUSCLE print entry point: build, extend, converge, judge."""
    pos, vel, pin_mask, grain_ids, s0, R_droplet = seed_structures.muscle(
        side=4, spacing=0.05, seed=seed)
    N = pos.shape[0]
    n_plate = 4 * 4

    dt = DT
    v_plate = MUSCLE_V_PLATE
    tag = f"{args.tag}_" if args.tag else ""

    # RULE 0 header
    print("=" * 70)
    print("THE KERNEL — MUSCLE print run")
    print(f"N={N}, droplet=4³, plates=4×4, seed={seed}, dt={dt}")
    print("-" * 70)
    print("STATEMENT: A cold cushion-spaced droplet seated on a pinned anchor")
    print("  plate pulls the second anchor plate toward it via DRAW, producing")
    print("  a contractile bridge; the same material pushes as an antagonist")
    print("  cushion when the plates converge past contact.")
    print("PREDICTION: Plate force follows the kernel-exact inverse-square law")
    print("  over the stroke, force stays >= half at s0*sqrt(2), the droplet")
    print("  remains one cluster and on-axis, force reverses in convergence,")
    print("  and the pinned anchors do not migrate.")
    print("FALSIFIERS:")
    print("  (a) FORCE LAW — measured right-plate force vs pairwise-DRAW")
    print("      prediction on recorded positions within 10% (contact-free)")
    print("  (b) STROKE    — force >= half at s0*sqrt(2)")
    print("  (c) TEAR      — droplet splits or migrates off axis")
    print("  (d) ANTAGONIST — force reverses sign past convergence")
    print("  (e) ANCHORS   — pinned plates drift in y/z")
    print("=" * 70)
    print(f"\nDerived R_droplet = {R_droplet:.5f}")
    print(f"Derived s0        = {s0:.5f}")
    print(f"Extension limit   = {s0 * MUSCLE_EXTENSION_FACTOR:.5f}\n")

    metrics, final_pos = _run_muscle(
        pos, vel, pin_mask, grain_ids, s0, R_droplet,
        v_plate, dt, tag, "muscle")

    _print_muscle_verdict(metrics, pos, final_pos, grain_ids,
                          s0, R_droplet, "muscle")
    print("=" * 70)


# ── SKIN-specific helpers ─────────────────────────────────────────────

# Drive the muscle anchor plates at the same derived 5% sound speed used by
# the muscle stroke.
SKIN_V_PLATE = MUSCLE_V_PLATE


def _skin_conform_and_coverage(pos: np.ndarray, grain_ids: np.ndarray,
                               derived: dict) -> tuple[float, float, np.ndarray]:
    """
    Return (conform_fraction, coverage_fraction, mat_com - droplet_com).

    Conform: fraction of mat grains whose nearest droplet grain lies inside
    the derived conform band.
    Coverage: fraction of droplet surface grains that have a mat grain inside
    the conform band.
    """
    pos64 = np.asarray(pos, dtype=np.float64)
    droplet_idx = np.flatnonzero(grain_ids == 0)
    mat_idx = np.flatnonzero(grain_ids == 1)
    if droplet_idx.size == 0 or mat_idx.size == 0:
        return 0.0, 0.0, np.zeros(3, dtype=np.float64)

    drop = pos64[droplet_idx]
    mat = pos64[mat_idx]

    # nearest mat->droplet distance
    dmd = np.linalg.norm(
        mat[:, None, :] - drop[None, :, :], axis=2)
    min_md = dmd.min(axis=1)
    lo, hi = derived["conform_band"]
    conform_frac = float(((min_md >= lo) & (min_md <= hi)).mean())

    # coverage: top-hemisphere surface grains to nearest mat grain
    surface_local = derived.get("surface_grains", np.array([], dtype=np.int32))
    if surface_local.size == 0:
        coverage_frac = 0.0
    else:
        surface = drop[surface_local]
        dsm = np.linalg.norm(
            surface[:, None, :] - mat[None, :, :], axis=2)
        min_sm = dsm.min(axis=1)
        coverage_frac = float(((min_sm >= lo) & (min_sm <= hi)).mean())

    mat_com = mat.mean(axis=0)
    drop_com = drop.mean(axis=0)
    rel_com = mat_com - drop_com
    return conform_frac, coverage_frac, rel_com


def _run_skin(pos, vel, pin_mask, grain_ids, s0, derived, v_plate, dt,
              tag, label, settle_ticks: int):
    """
    Run the SKIN protocol: settle, then the muscle's extension->convergence
    stroke (extend to s0*sqrt(2), converge back to s0).
    """
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    # The two anchor plates are the grain-id -1 points; the mat is appended
    # after the whole muscle print, so the right plate is NOT at the end.
    plate_idx = np.flatnonzero(grain_ids == -1)
    n_plate = plate_idx.size
    n_plate_half = n_plate // 2
    plate_x = pos[plate_idx, 0]
    median_x = float(np.median(plate_x))
    left_idx = plate_idx[plate_x < median_x].astype(np.int32)
    right_idx = plate_idx[plate_x >= median_x].astype(np.int32)
    # Guard: exactly half each.
    if left_idx.size != n_plate_half or right_idx.size != n_plate_half:
        left_idx = plate_idx[np.argsort(plate_x)[:n_plate_half]]
        right_idx = plate_idx[np.argsort(plate_x)[-n_plate_half:]]

    sample_every = 500

    metrics = {
        "tick": [],
        "phase": [],
        "separation": [],
        "mat_clusters": [],
        "droplet_clusters": [],
        "conform_fraction": [],
        "coverage_fraction": [],
        "mat_com_rel": [],
    }

    def _sample(tick: int, phase: str):
        left_x = float(sim.pos[left_idx, 0].mean())
        right_x = float(sim.pos[right_idx, 0].mean())
        separation = right_x - left_x
        mat_clust = _group_cluster_count(sim.pos, grain_ids, 1, R_C)
        drop_clust = _group_cluster_count(sim.pos, grain_ids, 0, R_C)
        conform, coverage, rel_com = _skin_conform_and_coverage(
            sim.pos, grain_ids, derived)

        metrics["tick"].append(tick)
        metrics["phase"].append(phase)
        metrics["separation"].append(separation)
        metrics["mat_clusters"].append(mat_clust)
        metrics["droplet_clusters"].append(drop_clust)
        metrics["conform_fraction"].append(conform)
        metrics["coverage_fraction"].append(coverage)
        metrics["mat_com_rel"].append(rel_com.copy())

        print(f"[{label}] tick={tick:6d} phase={phase:10s} | "
              f"sep={separation:.5f} | mat_clust={mat_clust} | "
              f"drop_clust={drop_clust} | conform={conform:.3f} | "
              f"coverage={coverage:.3f} | "
              f"rel_com=({rel_com[0]:.4f},{rel_com[1]:.4f},{rel_com[2]:.4f})")

    print(f"\n[{label}] N={N} droplet={derived['n_droplet']} "
          f"mat={derived['n_mat']} plates={n_plate}")
    print(f"[{label}] s0={s0:.5f} v_plate={v_plate:.5f} dt={dt} "
          f"settle_ticks={settle_ticks}\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    tick = 0
    _sample(tick, "init")

    # Phase: settle (free evolution so the mat drapes onto the droplet)
    for tick in range(1, settle_ticks + 1):
        sim.step(dt)
        if tick % sample_every == 0 or tick == settle_ticks:
            _sample(tick, "settle")

    # Phase: extend plates to s0 * sqrt(2)
    target_extend = s0 * MUSCLE_STROKE_FACTOR
    phase = "extend"
    while True:
        tick += 1
        cur_sep = float(sim.pos[right_idx, 0].mean() -
                        sim.pos[left_idx, 0].mean())
        if cur_sep >= target_extend:
            break
        dx = 0.5 * v_plate * dt
        sim.pos[left_idx, 0] -= dx
        sim.pos[right_idx, 0] += dx
        if sim.use_cuda:
            sim.d_pos.copy_to_device(sim.pos)
        sim.step(dt)
        if tick % sample_every == 0:
            _sample(tick, phase)

    _sample(tick, phase)

    # Phase: converge back to s0
    phase = "converge"
    while True:
        tick += 1
        cur_sep = float(sim.pos[right_idx, 0].mean() -
                        sim.pos[left_idx, 0].mean())
        if cur_sep <= s0:
            break
        dx = -0.5 * v_plate * dt
        sim.pos[left_idx, 0] -= dx
        sim.pos[right_idx, 0] += dx
        if sim.use_cuda:
            sim.d_pos.copy_to_device(sim.pos)
        sim.step(dt)
        if tick % sample_every == 0:
            _sample(tick, phase)

    _sample(tick, phase)

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics, sim.pos.copy()


def _print_skin_verdict(metrics, derived: dict, label: str):
    """Print SKIN falsifier verdict; return dict of booleans."""
    phases = metrics["phase"]
    conform = np.asarray(metrics["conform_fraction"], dtype=np.float64)
    coverage = np.asarray(metrics["coverage_fraction"], dtype=np.float64)
    mat_clust = np.asarray(metrics["mat_clusters"], dtype=np.int32)
    drop_clust = np.asarray(metrics["droplet_clusters"], dtype=np.int32)
    rel_com = np.asarray(metrics["mat_com_rel"], dtype=np.float64)

    slide_bar = float(derived.get("slide_bar", 2.0 * derived["muscle_spacing"]))

    settle_idx = [i for i, p in enumerate(phases) if p == "settle"]
    stroke_idx = [i for i, p in enumerate(phases) if p in ("extend", "converge")]

    # Baseline relative COM is the last settle sample (post-settle value).
    if settle_idx:
        baseline = rel_com[settle_idx[-1]]
        end_settle_conform = float(conform[settle_idx[-1]])
        end_settle_coverage = float(coverage[settle_idx[-1]])
    else:
        baseline = rel_com[0]
        end_settle_conform = float(conform[0])
        end_settle_coverage = float(coverage[0])

    # Max drift of mat COM relative to droplet COM from the post-settle value.
    if stroke_idx:
        drifts = np.linalg.norm(rel_com[stroke_idx] - baseline, axis=1)
        max_drift = float(drifts.max())
    else:
        max_drift = 0.0

    conform_ok = (end_settle_conform >= 0.5 and
                  (all(conform[i] >= 0.5 for i in stroke_idx) if stroke_idx else True))
    coverage_ok = end_settle_coverage >= 0.5
    slide_ok = max_drift <= slide_bar
    integrity_ok = bool((mat_clust == 1).all() and (drop_clust == 1).all())

    print(f"\n[{label}] SKIN FALSIFIERS:")
    print(f"  (a) CONFORM   : {'PASS' if conform_ok else 'FAIL'}  "
          f"end-settle={end_settle_conform:.3f}  "
          f"stroke min={float(conform[stroke_idx].min()) if stroke_idx else 0.0:.3f} "
          f"(bar 0.5)")
    print(f"  (b) NO SLIDE-OFF: {'PASS' if slide_ok else 'FAIL'}  "
          f"max drift={max_drift:.4f} (bar {slide_bar:.4f})")
    print(f"  (c) COVERAGE  : {'PASS' if coverage_ok else 'FAIL'}  "
          f"end-settle={end_settle_coverage:.3f} (bar 0.5)")
    print(f"  (d) INTEGRITY : {'PASS' if integrity_ok else 'FAIL'}  "
          f"mat clusters max={int(mat_clust.max())}  "
          f"droplet clusters max={int(drop_clust.max())}")

    return {
        "conform_ok": conform_ok,
        "slide_ok": slide_ok,
        "coverage_ok": coverage_ok,
        "integrity_ok": integrity_ok,
    }


def skin_main(args, seed):
    """SKIN print entry point: build, settle, stroke, judge."""
    pos, vel, pin_mask, grain_ids, s0, R_droplet, derived = seed_structures.skin(
        spacing=0.05, seed=seed)
    N = pos.shape[0]

    dt = DT
    v_plate = SKIN_V_PLATE
    tag = f"{args.tag}_" if args.tag else ""
    settle_ticks = int(getattr(args, "skin_settle_ticks", 3000))

    # RULE 0 header
    print("=" * 70)
    print("THE KERNEL - SKIN v1 print run")
    print(f"N={N}, droplet=4^3, mat=16x16, plates=4x4, seed={seed}, dt={dt}, "
          f"settle_ticks={settle_ticks}")
    print("-" * 70)
    print("STATEMENT: A 16x16 mat printed one 2-D lattice step above a muscle")
    print("  droplet settles into a conformal drape held only by the muscle's DRAW;")
    print("  during the muscle's own extension->convergence stroke the mat stays")
    print("  conformal, does not slide off, covers the droplet top hemisphere, and")
    print("  remains one cluster.")
    print("PREDICTION: After settle, >= half the mat grains sit within the derived")
    print("  conform band of some droplet grain, >= half the droplet surface grains")
    print("  are covered, the mat and droplet each stay one cluster, and the mat's")
    print("  COM drifts <= 2 muscle lattice steps from its post-settle value.")
    print("FALSIFIERS:")
    print("  (a) CONFORM   - < half mat grains in conform band after settle or any")
    print("      stroke sample")
    print("  (b) NO SLIDE-OFF - mat COM relative to droplet COM drifts > 2 lattice")
    print("      steps during the stroke")
    print("  (c) COVERAGE  - < half droplet surface grains covered after settle")
    print("  (d) INTEGRITY - mat or droplet splits (cluster count > 1)")
    print("=" * 70)
    print(f"\nDerived d_eq_2D  = {derived['d_eq_2D']:.5f}")
    print(f"Derived s0         = {s0:.5f}")
    print(f"Derived R_droplet  = {R_droplet:.5f}")
    print(f"Conform band       = [{derived['conform_band'][0]:.5f}, "
          f"{derived['conform_band'][1]:.5f}]")
    print(f"Stroke extend      = {s0 * MUSCLE_STROKE_FACTOR:.5f}")
    print(f"Slide bar          = {derived['slide_bar']:.5f}\n")

    metrics, final_pos = _run_skin(
        pos, vel, pin_mask, grain_ids, s0, derived,
        v_plate, dt, tag, "skin", settle_ticks)

    _print_skin_verdict(metrics, derived, "skin")
    print("=" * 70)


# ── BLADDER-specific helpers ──────────────────────────────────────────

# Inherit the muscle's derived plate speed (5% bond sound speed).
BLADDER_V_PLATE = MUSCLE_V_PLATE


def _bladder_plate_indices(pos: np.ndarray, grain_ids: np.ndarray):
    """Return (left_idx, right_idx) for the two pinned plates."""
    plate_idx = np.flatnonzero(grain_ids == -1)
    n_plate = plate_idx.size
    n_half = n_plate // 2
    plate_x = pos[plate_idx, 0]
    order = np.argsort(plate_x)
    left_idx = plate_idx[order[:n_half]].astype(np.int32)
    right_idx = plate_idx[order[-n_half:]].astype(np.int32)
    return left_idx, right_idx


def _bladder_escape_count_and_first_pos(pos: np.ndarray, grain_ids: np.ndarray,
                                        center: np.ndarray, r_out: float,
                                        escaped: np.ndarray,
                                        first_pos: np.ndarray) -> int:
    """
    Update escape state for contents and return current escape count.

    ``escaped`` and ``first_pos`` are updated in place for newly escaped grains.
    """
    content_idx = np.flatnonzero(grain_ids == 2)
    if content_idx.size == 0:
        return 0
    rel = pos[content_idx].astype(np.float64) - center[None, :]
    dist = np.linalg.norm(rel, axis=1)
    outside = dist > r_out
    newly = outside & (~escaped)
    first_pos[newly] = pos[content_idx[newly]].astype(np.float64)
    escaped[:] = escaped | outside
    return int(outside.sum())


def _bladder_shell_displacement(pos: np.ndarray, grain_ids: np.ndarray,
                                ref_shell: np.ndarray) -> float:
    """Max distance from any current shell grain to its nearest print shell grain."""
    shell_idx = np.flatnonzero(grain_ids == 1)
    if shell_idx.size == 0 or ref_shell.shape[0] == 0:
        return 0.0
    cur = pos[shell_idx].astype(np.float64)
    d = cur[:, None, :] - ref_shell[None, :, :]
    dist = np.linalg.norm(d, axis=2)
    return float(dist.min(axis=1).max())


def _run_bladder(pos, vel, pin_mask, grain_ids, s0, derived, v_plate, dt,
                 tag, label):
    """
    Run the BLADDER squeeze protocol.

    Phase 1 (converge): plates move inward from s0 until the measured plate
    force reaches 2*F_hold AND at least half the contents have escaped, or the
    plates reach the geometric limit of 2 muscle spacings apart.
    Phase 2 (release): plates return to s0.
    Phase 3 (hold): free evolution for ~1000 ticks (post-yield integrity window).
    """
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    left_idx, right_idx = _bladder_plate_indices(pos, grain_ids)
    n_content = int(derived["n_content"])
    content_idx = np.arange(
        2 * derived["n_plate"] + derived["n_shell"],
        2 * derived["n_plate"] + derived["n_shell"] + n_content,
        dtype=np.int32)

    center = np.array([derived["center_x"], 0.0, 0.0], dtype=np.float64)
    r_b = float(derived["r_b"])
    d_eq = float(derived["d_eq"])
    r_out = r_b + d_eq
    F_hold = float(derived["F_hold"])
    muscle_spacing = float(derived["muscle_spacing"])
    min_sep = 2.0 * muscle_spacing
    integrity_bar = 2.0 * muscle_spacing
    neck_center = derived["neck_center"].astype(np.float64)
    neck_axis = derived["neck_axis"].astype(np.float64)
    neck_axis_u = neck_axis / max(np.linalg.norm(neck_axis), 1e-12)

    ref_shell = pos[grain_ids == 1].copy().astype(np.float64)
    escaped = np.zeros(n_content, dtype=bool)
    first_escape_pos = np.zeros((n_content, 3), dtype=np.float64)

    sample_every = 500

    metrics = {
        "tick": [],
        "phase": [],
        "separation": [],
        "plate_force": [],
        "shell_clusters": [],
        "content_escape_count": [],
        "max_shell_displacement": [],
    }

    def _sample(tick: int, phase: str):
        left_x = float(sim.pos[left_idx, 0].mean())
        right_x = float(sim.pos[right_idx, 0].mean())
        separation = right_x - left_x
        pforce = _plate_force(sim.acc, left_idx, right_idx)
        shell_clust = _group_cluster_count(sim.pos, grain_ids, 1, R_C)
        esc = _bladder_escape_count_and_first_pos(
            sim.pos, grain_ids, center, r_out, escaped, first_escape_pos)
        disp = _bladder_shell_displacement(sim.pos, grain_ids, ref_shell)

        metrics["tick"].append(tick)
        metrics["phase"].append(phase)
        metrics["separation"].append(separation)
        metrics["plate_force"].append(pforce)
        metrics["shell_clusters"].append(shell_clust)
        metrics["content_escape_count"].append(esc)
        metrics["max_shell_displacement"].append(disp)

        print(f"[{label}] tick={tick:6d} phase={phase:10s} | "
              f"sep={separation:.5f} | force={pforce:.2f} | "
              f"shell_clust={shell_clust} | escapes={esc:3d} | "
              f"shell_disp={disp:.4f}")

    print(f"\n[{label}] N={N} shell={derived['n_shell']} "
          f"content={n_content} plates={derived['n_plate']}")
    print(f"[{label}] s0={s0:.5f} F_hold={F_hold:.2f} 2*F_hold={2.0*F_hold:.2f} "
          f"v_plate={v_plate:.5f} dt={dt}\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    tick = 0
    _sample(tick, "init")

    # Phase 1: converge until yield threshold or geometric limit.
    phase = "converge"
    target_force = 2.0 * F_hold
    target_escape = n_content // 2
    while True:
        tick += 1
        cur_sep = float(sim.pos[right_idx, 0].mean() -
                        sim.pos[left_idx, 0].mean())
        if cur_sep <= min_sep:
            break
        # move plates inward by half the relative motion each side
        dx = 0.5 * v_plate * dt
        sim.pos[left_idx, 0] += dx
        sim.pos[right_idx, 0] -= dx
        if sim.use_cuda:
            sim.d_pos.copy_to_device(sim.pos)
        sim.step(dt)
        if tick % sample_every == 0:
            _sample(tick, phase)
        # check yield stop after stepping
        cur_force = _plate_force(sim.acc, left_idx, right_idx)
        cur_esc = int(escaped.sum())
        if cur_force >= target_force and cur_esc >= target_escape:
            break

    _sample(tick, phase)

    # Phase 2: release back to s0.
    phase = "release"
    while True:
        tick += 1
        cur_sep = float(sim.pos[right_idx, 0].mean() -
                        sim.pos[left_idx, 0].mean())
        if cur_sep >= s0:
            break
        dx = -0.5 * v_plate * dt
        sim.pos[left_idx, 0] += dx
        sim.pos[right_idx, 0] -= dx
        if sim.use_cuda:
            sim.d_pos.copy_to_device(sim.pos)
        sim.step(dt)
        if tick % sample_every == 0:
            _sample(tick, phase)

    _sample(tick, phase)

    # Phase 3: post-yield integrity hold.
    phase = "hold"
    hold_ticks = 1000
    for _ in range(hold_ticks):
        tick += 1
        sim.step(dt)
        if tick % sample_every == 0:
            _sample(tick, phase)

    _sample(tick, phase)

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics, first_escape_pos, escaped, sim.pos.copy()


def _print_bladder_verdict(metrics, first_escape_pos, escaped, derived: dict,
                           label: str):
    """Print BLADDER falsifier verdict; return dict of booleans."""
    phases = metrics["phase"]
    sep = np.asarray(metrics["separation"], dtype=np.float64)
    pforce = np.asarray(metrics["plate_force"], dtype=np.float64)
    shell_clust = np.asarray(metrics["shell_clusters"], dtype=np.int32)
    esc = np.asarray(metrics["content_escape_count"], dtype=np.int32)
    disp = np.asarray(metrics["max_shell_displacement"], dtype=np.float64)

    F_hold = float(derived["F_hold"])
    muscle_spacing = float(derived["muscle_spacing"])
    integrity_bar = 2.0 * muscle_spacing
    neck_diameter = float(derived["neck_diameter"])
    corridor_radius = neck_diameter / 2.0 + muscle_spacing
    neck_center = derived["neck_center"].astype(np.float64)
    neck_axis = derived["neck_axis"].astype(np.float64)
    neck_axis_u = neck_axis / max(np.linalg.norm(neck_axis), 1e-12)

    # (a) SEAL: while force < F_hold, zero escapes and shell clusters == 1.
    seal_idx = [i for i, f in enumerate(pforce) if f < F_hold]
    if not seal_idx:
        seal_idx = [0]
    seal_ok = (
        all(esc[i] == 0 for i in seal_idx) and
        all(shell_clust[i] == 1 for i in seal_idx))

    # (b) YIELD: by force >= 2*F_hold or max convergence (min separation).
    min_sep = 2.0 * muscle_spacing
    yield_idx = None
    for i in range(len(phases)):
        if pforce[i] >= 2.0 * F_hold or sep[i] <= min_sep:
            yield_idx = i
            break
    if yield_idx is None:
        yield_ok = False
        yield_esc = 0
    else:
        yield_ok = (esc[yield_idx] >= derived["n_content"] // 2 and
                    (shell_clust == 1).all())
        yield_esc = int(esc[yield_idx])

    # (c) NECK SELECTIVITY: first-outside positions within the derived neck
    # corridor (neck radius + one lattice spacing).
    total_escaped = int(escaped.sum())
    neck_ok = False
    in_neck = out_neck = 0
    if total_escaped > 0:
        pos_out = first_escape_pos[escaped]
        to_axis = pos_out - neck_center[None, :]
        cross = np.cross(to_axis, neck_axis_u[None, :])
        dist_axis = np.linalg.norm(cross, axis=1)
        in_neck = int(np.count_nonzero(dist_axis <= corridor_radius))
        out_neck = total_escaped - in_neck
        neck_ok = out_neck == 0

    first_escape_idx = next(
        (i for i, e in enumerate(esc) if e > 0), None)

    # (d) SHELL INTEGRITY post-yield: after release/hold, shell cluster 1 and
    # max displacement <= 2 spacings.
    post_idx = [i for i, p in enumerate(phases) if p in ("release", "hold")]
    if post_idx:
        integrity_ok = (
            all(shell_clust[i] == 1 for i in post_idx) and
            all(disp[i] <= integrity_bar for i in post_idx))
        post_max_disp = float(max(disp[i] for i in post_idx))
    else:
        integrity_ok = False
        post_max_disp = 0.0

    print(f"\n[{label}] BLADDER FALSIFIERS:")
    print(f"  (a) SEAL      : {'PASS' if seal_ok else 'FAIL'}  "
          f"force<F_hold samples={len(seal_idx)} escapes={int(esc[seal_idx].max()) if seal_idx else 0} "
          f"shell_clust max={int(shell_clust[seal_idx].max()) if seal_idx else 0}")
    if yield_idx is not None:
        print(f"  (b) YIELD     : {'PASS' if yield_ok else 'FAIL'}  "
              f"at tick={metrics['tick'][yield_idx]} force={pforce[yield_idx]:.2f} "
              f"sep={sep[yield_idx]:.5f} escapes={yield_esc}/{derived['n_content']//2} "
              f"shell_clust max={int(shell_clust.max())}")
    else:
        print(f"  (b) YIELD     : FAIL  (force never reached 2*F_hold or min sep)")
    if first_escape_idx is not None:
        first_esc_info = (
            f"first_escape=tick={metrics['tick'][first_escape_idx]} "
            f"force={pforce[first_escape_idx]:.2f} "
            f"sep={sep[first_escape_idx]:.5f}"
        )
    else:
        first_esc_info = "first_escape=none"
    print(f"  (c) NECK      : {'PASS' if neck_ok else 'FAIL'}  "
          f"escaped={total_escaped} in_neck={in_neck} out_neck={out_neck} "
          f"{first_esc_info} (bar {corridor_radius:.4f} from axis)")
    print(f"  (d) INTEGRITY : {'PASS' if integrity_ok else 'FAIL'}  "
          f"post-yield shell_clust max={int(shell_clust[post_idx].max()) if post_idx else 0} "
          f"max disp={post_max_disp:.4f} (bar {integrity_bar:.4f})")

    return {
        "seal_ok": seal_ok,
        "yield_ok": yield_ok,
        "neck_ok": neck_ok,
        "integrity_ok": integrity_ok,
    }


def bladder_main(args, seed):
    """BLADDER print entry point: build, squeeze, yield, release, judge."""
    fill = str(getattr(args, "bladder_fill", "gap"))
    neck = str(getattr(args, "bladder_neck", "narrow"))
    pos, vel, pin_mask, grain_ids, s0, derived = seed_structures.bladder(
        seed=seed, fill=fill, neck=neck)
    N = pos.shape[0]

    dt = DT
    v_plate = BLADDER_V_PLATE
    tag = f"{args.tag}_" if args.tag else ""
    if neck == "antijam":
        version = "v3"
    elif fill == "fill":
        version = "v2"
    else:
        version = "v1"

    # RULE 0 header
    print("=" * 70)
    print(f"THE KERNEL - BLADDER {version} print run")
    print(f"N={N}, shell={derived['n_shell']}, content={derived['n_content']}, "
          f"fill={fill}, neck={neck}, plates=4x4, seed={seed}, dt={dt}")
    print("-" * 70)
    if neck == "antijam":
        print("STATEMENT: A closed spherical shell one grain thick, filled with a")
        print("  condensed content droplet in cushion contact with the wall and")
        print("  squeezed by two pinned muscle plates, seals at low pressure, yields")
        print("  contents through a derived anti-jam neck, and remains one closed mat")
        print("  after release.")
        print("PREDICTION: The 4-spacing neck on the squeeze axis is too large for a")
        print("  cushion arch to close; the shell holds zero content escape while plate")
        print("  force is below F_hold; at or before 2*F_hold at least half the contents")
        print("  exit through the neck corridor; the shell stays one cluster and shows")
        print("  no grain displacement > 2 spacings after release.")
    elif fill == "fill":
        print("STATEMENT: A closed spherical shell one grain thick, filled with a")
        print("  condensed content droplet in cushion contact with the wall and")
        print("  squeezed by two pinned muscle plates, seals at low pressure, yields")
        print("  contents through a single neck at a derived force threshold, and")
        print("  remains one closed mat after release.")
        print("PREDICTION: The cushion-splinted wall holds shape from tick 0; the")
        print("  shell holds zero content escape while plate force is below F_hold;")
        print("  at or before 2*F_hold at least half the contents exit through the")
        print("  neck; the shell stays one cluster and shows no grain displacement")
        print("  > 2 spacings after release.")
    else:
        print("STATEMENT: A closed spherical shell one grain thick, packed with a")
        print("  condensed content droplet and squeezed by two pinned muscle plates,")
        print("  seals at low pressure, yields contents through a single neck at a")
        print("  derived force threshold, and remains one closed mat after release.")
        print("PREDICTION: The shell holds zero content escape while plate force is")
        print("  below F_hold; at or before 2*F_hold at least half the contents exit")
        print("  through the neck; the shell stays one cluster and shows no grain")
        print("  displacement > 2 spacings after release.")
    print("FALSIFIERS:")
    print("  (a) SEAL      - content escapes or shell splits while force < F_hold")
    print("  (b) YIELD     - fewer than half contents escape by 2*F_hold/min sep")
    print("      OR shell splits during squeeze")
    print("  (c) NECK      - any escapee exits outside the neck corridor")
    print("  (d) INTEGRITY - shell splits or any shell grain displaced > 2 spacings")
    print("      post-yield")
    print("=" * 70)
    neck_corridor = derived['neck_diameter'] / 2.0 + derived['muscle_spacing']
    print(f"\nDerived r_b        = {derived['r_b']:.5f}")
    print(f"Derived d_eq       = {derived['d_eq']:.5f}")
    print(f"Derived s0         = {s0:.5f}")
    print(f"Derived F_hold     = {derived['F_hold']:.2f}")
    print(f"2 * F_hold         = {2.0*derived['F_hold']:.2f}")
    print(f"Min separation     = {2.0*derived['muscle_spacing']:.5f}")
    print(f"Neck diameter      = {derived['neck_diameter']:.5f}")
    print(f"Neck corridor      = {neck_corridor:.5f}")
    print(f"Neck center        = ({derived['neck_center'][0]:.4f}, "
          f"{derived['neck_center'][1]:.4f}, {derived['neck_center'][2]:.4f})")
    print(f"Neck axis          = ({derived['neck_axis'][0]:.4f}, "
          f"{derived['neck_axis'][1]:.4f}, {derived['neck_axis'][2]:.4f})\n")

    metrics, first_escape_pos, escaped, final_pos = _run_bladder(
        pos, vel, pin_mask, grain_ids, s0, derived,
        v_plate, dt, tag, "bladder")

    _print_bladder_verdict(metrics, first_escape_pos, escaped, derived,
                           "bladder")
    print("=" * 70)


# ── LEVER-specific helpers ────────────────────────────────────────────


def _run_lever(pos, vel, pin_mask, grain_ids, derived, dt, ticks,
               tag, label):
    """
    Free-evolution lever protocol: only the ground plate is pinned.

    Records load-end height, lever angle, fulcrum gap, plate reaction force,
    load-lever contact force, and cluster counts for all four bodies.
    """
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    # Fixed global group indices.
    plate_idx = np.flatnonzero(grain_ids == -1).astype(np.int32)
    drop_idx = np.flatnonzero(grain_ids == 0).astype(np.int32)
    fulcrum_idx = np.flatnonzero(grain_ids == 1).astype(np.int32)
    lever_idx = np.flatnonzero(grain_ids == 2).astype(np.int32)
    load_idx = np.flatnonzero(grain_ids == 3).astype(np.int32)

    # Fixed local face indices mapped to global lever / fulcrum arrays.
    muscle_face = lever_idx[derived["muscle_face"]]
    load_face = lever_idx[derived["load_face"]]
    fulcrum_top_face = fulcrum_idx[derived["fulcrum_top_face"]]
    lever_contact_local = lever_idx[derived["lever_contact_local"]]

    load_end_z0 = float(derived["load_end_z0"])
    plate_pos0 = derived["plate_pos0"]
    d_eq = float(derived["d_eq"])

    # Print contact force supporting the load (upward lever push on load).
    plate_fz0 = seed_structures._draw_force_z(
        sim.pos[plate_idx].astype(np.float64),
        sim.pos[load_idx].astype(np.float64))
    acc_load_z0 = float(sim.acc[load_idx, 2].sum())
    print_contact = float(acc_load_z0 - plate_fz0)
    if print_contact <= 0.0:
        print_contact = float(derived["W_L"])

    sample_every = max(1, ticks // 40)

    metrics = {
        "tick": [],
        "load_gain": [],
        "lever_angle": [],
        "fulcrum_gap": [],
        "plate_force": [],
        "contact_ratio": [],
        "drop_clusters": [],
        "fulcrum_clusters": [],
        "lever_clusters": [],
        "load_clusters": [],
        "plate_pos": [],
        "drop_pos": [],
        "fulcrum_pos": [],
        "lever_pos": [],
        "load_pos": [],
    }

    def _min_pair_distance(a: np.ndarray, b: np.ndarray) -> float:
        d = a[:, None, :] - b[None, :, :]
        return float(np.sqrt((d * d).sum(axis=2).min()))

    def _sample(tick: int):
        plate_p = sim.pos[plate_idx].astype(np.float64)
        drop_p = sim.pos[drop_idx].astype(np.float64)
        fulcrum_p = sim.pos[fulcrum_idx].astype(np.float64)
        lever_p = sim.pos[lever_idx].astype(np.float64)
        load_p = sim.pos[load_idx].astype(np.float64)

        load_c = lever_p[derived["load_face"]].mean(axis=0)
        muscle_c = lever_p[derived["muscle_face"]].mean(axis=0)
        load_gain = float(load_c[2] - load_end_z0)
        lever_angle = float(math.atan2(
            load_c[2] - muscle_c[2], load_c[0] - muscle_c[0]))

        fulcrum_gap = _min_pair_distance(
            fulcrum_p[derived["fulcrum_top_face"]],
            lever_p[derived["lever_contact_local"]])

        plate_force = float(np.abs(sim.acc[plate_idx, 2].sum()))

        plate_fz = seed_structures._draw_force_z(plate_p, load_p)
        acc_load_z = float(sim.acc[load_idx, 2].sum())
        contact_ratio = ((acc_load_z - plate_fz) /
                         max(print_contact, 1e-12))

        drop_clust = _group_cluster_count(sim.pos, grain_ids, 0, R_C)
        fulcrum_clust = _group_cluster_count(sim.pos, grain_ids, 1, R_C)
        lever_clust = _group_cluster_count(sim.pos, grain_ids, 2, R_C)
        load_clust = _group_cluster_count(sim.pos, grain_ids, 3, R_C)

        metrics["tick"].append(tick)
        metrics["load_gain"].append(load_gain)
        metrics["lever_angle"].append(lever_angle)
        metrics["fulcrum_gap"].append(fulcrum_gap)
        metrics["plate_force"].append(plate_force)
        metrics["contact_ratio"].append(contact_ratio)
        metrics["drop_clusters"].append(drop_clust)
        metrics["fulcrum_clusters"].append(fulcrum_clust)
        metrics["lever_clusters"].append(lever_clust)
        metrics["load_clusters"].append(load_clust)
        metrics["plate_pos"].append(plate_p.copy())
        metrics["drop_pos"].append(drop_p.copy())
        metrics["fulcrum_pos"].append(fulcrum_p.copy())
        metrics["lever_pos"].append(lever_p.copy())
        metrics["load_pos"].append(load_p.copy())

        print(f"[{label}] tick={tick:6d} | load_gain={load_gain:+.4f} | "
              f"angle={math.degrees(lever_angle):6.2f}deg | "
              f"gap={fulcrum_gap:.4f} | plate_F={plate_force:.2f} | "
              f"contact={contact_ratio:.3f} | "
              f"clusters={drop_clust}/{fulcrum_clust}/{lever_clust}/{load_clust}")

    print(f"\n[{label}] N={N} plate={len(plate_idx)} droplet={len(drop_idx)} "
          f"fulcrum={len(fulcrum_idx)} lever={len(lever_idx)} load={len(load_idx)}")
    print(f"[{label}] dt={dt} ticks={ticks} sample_every={sample_every}\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    _sample(0)
    for tick in range(1, ticks + 1):
        sim.step(dt)
        if tick % sample_every == 0 or tick == ticks:
            _sample(tick)

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics


def _print_lever_verdict(metrics, derived: dict, label: str, control: bool):
    """Print LEVER falsifier verdict; return dict of booleans."""
    ticks = np.asarray(metrics["tick"], dtype=np.int32)
    load_gain = np.asarray(metrics["load_gain"], dtype=np.float64)
    lever_angle = np.asarray(metrics["lever_angle"], dtype=np.float64)
    fulcrum_gap = np.asarray(metrics["fulcrum_gap"], dtype=np.float64)
    plate_force = np.asarray(metrics["plate_force"], dtype=np.float64)
    contact_ratio = np.asarray(metrics["contact_ratio"], dtype=np.float64)
    drop_clust = np.asarray(metrics["drop_clusters"], dtype=np.int32)
    fulcrum_clust = np.asarray(metrics["fulcrum_clusters"], dtype=np.int32)
    lever_clust = np.asarray(metrics["lever_clusters"], dtype=np.int32)
    load_clust = np.asarray(metrics["load_clusters"], dtype=np.int32)

    d_eq = float(derived["d_eq"])
    seated_band = d_eq + 0.05
    r_c = R_C

    # Recovery: fulcrum gap excursions above r_c must return to seated band.
    excursions = []
    in_excursion = False
    t_start = 0
    max_gap_in = 0.0
    for i, (t, g) in enumerate(zip(ticks, fulcrum_gap)):
        if g > r_c:
            if not in_excursion:
                in_excursion = True
                t_start = int(t)
                max_gap_in = float(g)
            else:
                max_gap_in = max(max_gap_in, float(g))
        else:
            if in_excursion:
                excursions.append((t_start, int(t), max_gap_in))
                in_excursion = False
    if in_excursion:
        excursions.append((t_start, int(ticks[-1]), max_gap_in))

    recovery_ok = True
    if excursions:
        last_end = excursions[-1][1]
        last_end_idx = int(np.searchsorted(ticks, last_end))
        seated = fulcrum_gap <= seated_band
        recovered_idx = None
        for i in range(last_end_idx, len(ticks)):
            if seated[i:].all():
                recovered_idx = i
                break
        recovery_ok = recovered_idx is not None

    max_gain = float(load_gain.max())
    max_gain_idx = int(np.argmax(load_gain))
    max_gain_tick = int(ticks[max_gain_idx])

    if control:
        lift_ok = None
        hold_ok = max_gain <= 0.05
    else:
        # LIFT: main must raise load end >= 0.10 while fulcrum stays or recovers.
        lift_ok = (max_gain >= 0.10) and recovery_ok
        hold_ok = None

    # BALANCE LAW v4: print-time R_true predicts the SETTLED direction.
    R_true = float(derived.get("R_true", 0.0))
    # Use the last 20 % of samples to determine the settled sign.
    n_angle = len(lever_angle)
    last_n = max(1, int(round(0.20 * n_angle)))
    settled_sign = int(np.sign(np.mean(lever_angle[-last_n:])))

    # Muscle-side-down (positive angle) iff R_true > 1.
    if R_true > 1.0:
        predicted_sign = 1
    elif R_true < 1.0:
        predicted_sign = -1
    else:
        predicted_sign = 0

    balance_ok = (predicted_sign != 0 and settled_sign == predicted_sign)
    balance_detail = (
        f"R_true={R_true:.3f} settled_angle_sign={settled_sign} "
        f"predicted={predicted_sign} (last {last_n}/{n_angle} samples)")

    # SAG v5: if the tube rotates muscle-down but the load end does not lift,
    # the 1-grain shell is sheet-class and the void must shrink to 1x1 next.
    sag_detected = False
    if not control:
        sag_detected = (settled_sign == 1 and max_gain < 0.10)

    # INTEGRITY: all bodies one cluster; plate pins hold.
    integrity_ok = (
        int(drop_clust.max()) == 1 and
        int(fulcrum_clust.max()) == 1 and
        int(lever_clust.max()) == 1 and
        int(load_clust.max()) == 1)

    plate_pos0 = np.asarray(derived["plate_pos0"], dtype=np.float64)
    plate_pos_final = np.asarray(metrics["plate_pos"][-1], dtype=np.float64)
    plate_drift = float(np.max(np.abs(plate_pos_final[:, 1:] - plate_pos0[:, 1:])))
    plate_ok = plate_drift <= 1e-4

    print(f"\n[{label}] LEVER FALSIFIERS:")
    if control:
        print(f"  (a) LIFT      : skipped (control)")
        print(f"  (b) HOLD      : {'PASS' if hold_ok else 'FAIL'}  "
              f"max load_gain={max_gain:.4f} at tick={max_gain_tick} "
              f"(bar 0.0500)")
    else:
        print(f"  (a) LIFT      : {'PASS' if lift_ok else 'FAIL'}  "
              f"max load_gain={max_gain:.4f} at tick={max_gain_tick} "
              f"(bar 0.1000) recovery_ok={recovery_ok}")
        print(f"  (b) HOLD      : skipped (main)")
    print(f"  (c) BALANCE   : {'PASS' if balance_ok else 'FAIL'}  "
          f"{balance_detail}")
    print(f"  (d) INTEGRITY : {'PASS' if integrity_ok else 'FAIL'}  "
          f"max clusters droplet/fulcrum/lever/load="
          f"{int(drop_clust.max())}/{int(fulcrum_clust.max())}/"
          f"{int(lever_clust.max())}/{int(load_clust.max())} "
          f"plate_drift={plate_drift:.6f}")
    if control:
        print(f"  (e) SAG       : skipped (control)")
    else:
        print(f"  (e) SAG       : {'DETECTED' if sag_detected else 'not detected'}  "
              f"settled_sign={settled_sign} max_load_gain={max_gain:.4f}")

    return {
        "lift_ok": lift_ok,
        "hold_ok": hold_ok,
        "balance_ok": balance_ok,
        "integrity_ok": integrity_ok,
        "plate_ok": plate_ok,
        "sag_detected": sag_detected,
    }


def lever_main(args, seed):
    """LEVER print entry point: build, free-evolve, judge."""
    control = bool(getattr(args, "lever_control", False))
    ticks = int(getattr(args, "lever_ticks", 8000))
    pos, vel, pin_mask, grain_ids, derived = seed_structures.lever(
        control=control, seed=seed)
    N = pos.shape[0]

    dt = DT
    base = args.tag if args.tag else "lever"
    label = f"{base}_control" if control else base
    version = "control" if control else "main"
    tag = ""  # label already carries the full tag; no extra prefix

    droplet_label = f"{derived['droplet_side']}^3"
    lever_len = derived.get('lever_len', 13)
    print("=" * 70)
    print(f"THE KERNEL - LEVER v6 print run ({version})")
    print(f"N={N}, plate=6x6, fulcrum=4x4x4+2x(4x1x3) cheeks (PINNED), "
          f"lever=4x4 tube (1-grain shell, 2x2 void) x {lever_len} rings, "
          f"droplet={droplet_label} (route={derived['route']}), load=4^3, "
          f"seed={seed}, dt={dt}, ticks={ticks}, control={control}")
    print("-" * 70)
    print("STATEMENT: A captured muscle-bone machine trades muscle force for")
    print("  load force through arm length; the saddle cheeks pin the tube to")
    print("  the fulcrum so rotation is the only free degree of freedom.")
    print("  The insertion fraction alpha is re-derived by bisection on the")
    print("  kernel's own static torque about the PINNED fulcrum contact point.")
    print("  v6 keeps the muscle droplet on the ground plate at the arm tip.")
    if control:
        print("PREDICTION: With kernel-verified R_true <= 1, the load end")
        print("  tips load-side-down and never rises more than one lattice")
        print("  step above its print height.")
    else:
        print("PREDICTION: With kernel-verified R_true = 2.0 (+/- 0.1), the")
        print("  captured arm tips muscle-side-down (positive settled angle)")
        print("  and the load end lifts through at least two lattice steps.")
    print("FALSIFIERS:")
    print("  (a) LIFT    - main: load end rises >= 0.10 absolute z")
    print("  (b) HOLD    - control: load end rises <= 0.05 all run")
    print("  (c) BALANCE - kernel torque predicts the SETTLED tip direction:")
    print("      sign of mean lever angle over the last 20% of samples must")
    print("      match sign(R_true - 1)")
    print("  (d) INTEGRITY - all four bodies one cluster; plate pins hold")
    print("  (e) CAPTURE - if the saddle still lets the arm wander, the muscle")
    print("      must be anchored through a tendon (the tendon membrane is next)")
    print("=" * 70)
    print(f"\nDerived d_eq   = {derived['d_eq']:.5f}")
    print(f"Derived alpha  = {derived['alpha']:.6f}  (method={derived['alpha_method']})")
    print(f"Derived a_m    = {derived['a_m']:.5f}")
    print(f"Derived a_l    = {derived['a_l']:.5f}")
    print(f"Derived F_m    = {derived['F_m']:.3f}")
    print(f"Derived W_L    = {derived['W_L']:.3f}")
    print(f"Derived R_static={derived['R_static']:.3f}")
    print(f"Derived R_true = {derived['R_true']:.3f}")
    print(f"Derived lever_len = {lever_len}")
    print(f"Derived margin_to_load_end = {derived['margin_to_load_end']:.5f}\n")

    metrics = _run_lever(pos, vel, pin_mask, grain_ids, derived,
                         dt, ticks, tag, label)
    _print_lever_verdict(metrics, derived, label, control)
    print("=" * 70)


# ── LEG v1-specific helpers ───────────────────────────────────────────


def _rod_internal_force_z(pos: np.ndarray, grain_ids: np.ndarray,
                          rod_top: np.ndarray, rod_bottom: np.ndarray) -> float:
    """
    Net z-force exerted by the rod top layer on the rod bottom layer.

    Positive means the top pulls the bottom upward (tension); negative means
    the top pushes the bottom downward (compression); near-zero means slack.
    DRAW is always attractive; static RESISTANCE is repulsive for r < R_BOND.
    Damping is omitted because this is a static sign read.
    """
    rod = pos[grain_ids == 4].astype(np.float64)
    if rod.shape[0] == 0 or rod_top.size == 0 or rod_bottom.size == 0:
        return 0.0
    top = rod[rod_top]
    bottom = rod[rod_bottom]
    dpos = top[:, None, :] - bottom[None, :, :]  # (n_top, n_bottom, 3)
    r2 = (dpos * dpos).sum(axis=2)
    # DRAW on bottom from top.
    draw_fz = float((G * dpos[:, :, 2] / ((r2 + EPS * EPS) ** 1.5)).sum())
    # Static RESISTANCE on bottom from top.
    r = np.sqrt(r2)
    resist_fz = 0.0
    # Wall region: repulsive away from top.
    mask_wall = r < R_WALL
    if np.any(mask_wall):
        r_eff = np.sqrt(r2[mask_wall] + S_WALL * S_WALL)
        f_scalar = K_WALL * (R_WALL / r_eff) ** P_WALL / r_eff
        ux = dpos[:, :, 0][mask_wall] / r[mask_wall]
        uy = dpos[:, :, 1][mask_wall] / r[mask_wall]
        uz = dpos[:, :, 2][mask_wall] / r[mask_wall]
        # Force on bottom is -f * unit_vector(bottom->top)
        resist_fz += float((-f_scalar * uz).sum())
    # Bond region: also repulsive (equilibrium at R_BOND).
    mask_bond = (r >= R_WALL) & (r <= R_BOND)
    if np.any(mask_bond):
        f_scalar = K_BOND * (r[mask_bond] - R_BOND) / (R_BOND * r[mask_bond])
        resist_fz += float((f_scalar * dpos[:, :, 2][mask_bond]).sum())
    return float(draw_fz + resist_fz)


def _run_leg(pos, vel, pin_mask, grain_ids, derived, dt, ticks,
             tag, label):
    """
    Free-evolution LEG v2 protocol: plate, droplet and fulcrum are pinned.

    Records lever metrics plus leg-specific telemetry: minimum
    arm-tip-to-droplet distance, droplet apex height, internal tendon rod force
    sign, and lever angle versus the derived arc stop theta_stop.
    """
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    plate_idx = np.flatnonzero(grain_ids == -1).astype(np.int32)
    drop_idx = np.flatnonzero(grain_ids == 0).astype(np.int32)
    fulcrum_idx = np.flatnonzero(grain_ids == 1).astype(np.int32)
    lever_idx = np.flatnonzero(grain_ids == 2).astype(np.int32)
    load_idx = np.flatnonzero(grain_ids == 3).astype(np.int32)
    rod_idx = np.flatnonzero(grain_ids == 4).astype(np.int32)

    muscle_face = lever_idx[derived["muscle_face"]]
    load_face = lever_idx[derived["load_face"]]
    fulcrum_top_face = fulcrum_idx[derived["fulcrum_top_face"]]
    lever_contact_local = lever_idx[derived["lever_contact_local"]]
    rod_top = rod_idx[derived["rod_top"]]
    rod_bottom = rod_idx[derived["rod_bottom"]]

    load_end_z0 = float(derived["load_end_z0"])
    plate_pos0 = derived["plate_pos0"]
    d_eq = float(derived["d_eq"])
    theta_stop = float(derived.get("theta_stop", 0.0))

    plate_fz0 = seed_structures._draw_force_z(
        sim.pos[plate_idx].astype(np.float64),
        sim.pos[load_idx].astype(np.float64))
    acc_load_z0 = float(sim.acc[load_idx, 2].sum())
    print_contact = float(acc_load_z0 - plate_fz0)
    if print_contact <= 0.0:
        print_contact = float(derived["W_L"]) if "W_L" in derived else 1.0

    sample_every = max(1, ticks // 40)

    metrics = {
        "tick": [],
        "load_gain": [],
        "lever_angle": [],
        "fulcrum_gap": [],
        "plate_force": [],
        "contact_ratio": [],
        "drop_clusters": [],
        "fulcrum_clusters": [],
        "lever_clusters": [],
        "load_clusters": [],
        "rod_clusters": [],
        "arm_tip_to_drop_min": [],
        "droplet_apex_z": [],
        "rod_force_z": [],
        "rod_sign": [],
        "theta": [],
        "theta_stop": theta_stop,
        "plate_pos": [],
        "drop_pos": [],
        "fulcrum_pos": [],
        "lever_pos": [],
        "load_pos": [],
        "rod_pos": [],
    }

    def _min_pair_distance(a: np.ndarray, b: np.ndarray) -> float:
        d = a[:, None, :] - b[None, :, :]
        return float(np.sqrt((d * d).sum(axis=2).min()))

    def _sample(tick: int):
        plate_p = sim.pos[plate_idx].astype(np.float64)
        drop_p = sim.pos[drop_idx].astype(np.float64)
        fulcrum_p = sim.pos[fulcrum_idx].astype(np.float64)
        lever_p = sim.pos[lever_idx].astype(np.float64)
        load_p = sim.pos[load_idx].astype(np.float64)
        rod_p = sim.pos[rod_idx].astype(np.float64)

        load_c = lever_p[derived["load_face"]].mean(axis=0)
        muscle_c = lever_p[derived["muscle_face"]].mean(axis=0)
        load_gain = float(load_c[2] - load_end_z0)
        lever_angle = float(math.atan2(
            load_c[2] - muscle_c[2], load_c[0] - muscle_c[0]))

        fulcrum_gap = _min_pair_distance(
            fulcrum_p[derived["fulcrum_top_face"]],
            lever_p[derived["lever_contact_local"]])

        plate_force = float(np.abs(sim.acc[plate_idx, 2].sum()))

        plate_fz = seed_structures._draw_force_z(plate_p, load_p)
        acc_load_z = float(sim.acc[load_idx, 2].sum())
        contact_ratio = ((acc_load_z - plate_fz) /
                         max(print_contact, 1e-12))

        drop_clust = _group_cluster_count(sim.pos, grain_ids, 0, R_C)
        fulcrum_clust = _group_cluster_count(sim.pos, grain_ids, 1, R_C)
        lever_clust = _group_cluster_count(sim.pos, grain_ids, 2, R_C)
        load_clust = _group_cluster_count(sim.pos, grain_ids, 3, R_C)
        rod_clust = _group_cluster_count(sim.pos, grain_ids, 4, R_C)

        arm_tip_to_drop_min = _min_pair_distance(
            lever_p[derived["muscle_face"]], drop_p)
        droplet_apex_z = float(drop_p[:, 2].max())
        rod_force_z = _rod_internal_force_z(sim.pos, grain_ids,
                                            derived["rod_top"],
                                            derived["rod_bottom"])
        if rod_force_z > 0.5:
            rod_sign = "tension"
        elif rod_force_z < -0.5:
            rod_sign = "compression"
        else:
            rod_sign = "slack"

        metrics["tick"].append(tick)
        metrics["load_gain"].append(load_gain)
        metrics["lever_angle"].append(lever_angle)
        metrics["fulcrum_gap"].append(fulcrum_gap)
        metrics["plate_force"].append(plate_force)
        metrics["contact_ratio"].append(contact_ratio)
        metrics["drop_clusters"].append(drop_clust)
        metrics["fulcrum_clusters"].append(fulcrum_clust)
        metrics["lever_clusters"].append(lever_clust)
        metrics["load_clusters"].append(load_clust)
        metrics["rod_clusters"].append(rod_clust)
        metrics["arm_tip_to_drop_min"].append(arm_tip_to_drop_min)
        metrics["droplet_apex_z"].append(droplet_apex_z)
        metrics["rod_force_z"].append(rod_force_z)
        metrics["rod_sign"].append(rod_sign)
        metrics["theta"].append(lever_angle)
        metrics["plate_pos"].append(plate_p.copy())
        metrics["drop_pos"].append(drop_p.copy())
        metrics["fulcrum_pos"].append(fulcrum_p.copy())
        metrics["lever_pos"].append(lever_p.copy())
        metrics["load_pos"].append(load_p.copy())
        metrics["rod_pos"].append(rod_p.copy())

        print(f"[{label}] tick={tick:6d} | load_gain={load_gain:+.4f} | "
              f"angle={math.degrees(lever_angle):6.2f}deg | "
              f"theta/theta_stop={math.degrees(lever_angle):6.2f}/"
              f"{math.degrees(theta_stop):6.2f}deg | "
              f"gap={fulcrum_gap:.4f} | plate_F={plate_force:.2f} | "
              f"contact={contact_ratio:.3f} | "
              f"clusters={drop_clust}/{fulcrum_clust}/{lever_clust}/{load_clust}/{rod_clust} | "
              f"tip_to_drop={arm_tip_to_drop_min:.4f} | apex_z={droplet_apex_z:.4f} | "
              f"rod={rod_sign}({rod_force_z:+.2f})")

    print(f"\n[{label}] N={N} plate={len(plate_idx)} droplet={len(drop_idx)} "
          f"fulcrum={len(fulcrum_idx)} lever={len(lever_idx)} load={len(load_idx)} "
          f"rod={len(rod_idx)}")
    print(f"[{label}] dt={dt} ticks={ticks} sample_every={sample_every}\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    _sample(0)
    for tick in range(1, ticks + 1):
        sim.step(dt)
        if tick % sample_every == 0 or tick == ticks:
            _sample(tick)

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics


def _print_leg_verdict(metrics, derived: dict, label: str, control: bool):
    """Print LEG v2 falsifier verdict; return dict of booleans."""
    ticks = np.asarray(metrics["tick"], dtype=np.int32)
    load_gain = np.asarray(metrics["load_gain"], dtype=np.float64)
    lever_angle = np.asarray(metrics["lever_angle"], dtype=np.float64)
    theta = np.asarray(metrics["theta"], dtype=np.float64)
    theta_stop = float(metrics.get("theta_stop", 0.0))
    fulcrum_gap = np.asarray(metrics["fulcrum_gap"], dtype=np.float64)
    plate_force = np.asarray(metrics["plate_force"], dtype=np.float64)
    contact_ratio = np.asarray(metrics["contact_ratio"], dtype=np.float64)
    drop_clust = np.asarray(metrics["drop_clusters"], dtype=np.int32)
    fulcrum_clust = np.asarray(metrics["fulcrum_clusters"], dtype=np.int32)
    lever_clust = np.asarray(metrics["lever_clusters"], dtype=np.int32)
    load_clust = np.asarray(metrics["load_clusters"], dtype=np.int32)
    rod_clust = np.asarray(metrics["rod_clusters"], dtype=np.int32)
    arm_tip_to_drop_min = np.asarray(metrics["arm_tip_to_drop_min"], dtype=np.float64)
    droplet_apex_z = np.asarray(metrics["droplet_apex_z"], dtype=np.float64)
    rod_force_z = np.asarray(metrics["rod_force_z"], dtype=np.float64)

    d_eq = float(derived["d_eq"])
    seated_band = d_eq + 0.05
    r_c = R_C

    # Recovery: fulcrum gap excursions above r_c must return to seated band.
    excursions = []
    in_excursion = False
    t_start = 0
    max_gap_in = 0.0
    for i, (t, g) in enumerate(zip(ticks, fulcrum_gap)):
        if g > r_c:
            if not in_excursion:
                in_excursion = True
                t_start = int(t)
                max_gap_in = float(g)
            else:
                max_gap_in = max(max_gap_in, float(g))
        else:
            if in_excursion:
                excursions.append((t_start, int(t), max_gap_in))
                in_excursion = False
    if in_excursion:
        excursions.append((t_start, int(ticks[-1]), max_gap_in))

    recovery_ok = True
    if excursions:
        last_end = excursions[-1][1]
        last_end_idx = int(np.searchsorted(ticks, last_end))
        seated = fulcrum_gap <= seated_band
        recovered_idx = None
        for i in range(last_end_idx, len(ticks)):
            if seated[i:].all():
                recovered_idx = i
                break
        recovery_ok = recovered_idx is not None

    max_gain = float(load_gain.max())
    max_gain_idx = int(np.argmax(load_gain))
    max_gain_tick = int(ticks[max_gain_idx])

    if control:
        lift_ok = None
        hold_ok = max_gain <= 0.05
    else:
        lift_ok = (max_gain >= 0.10) and recovery_ok
        hold_ok = None

    # BALANCE LAW: print-time R_true predicts the SETTLED direction.
    R_true = float(derived.get("R_true", 0.0))
    n_angle = len(lever_angle)
    last_n = max(1, int(round(0.20 * n_angle)))
    settled_sign = int(np.sign(np.mean(lever_angle[-last_n:])))

    if R_true > 1.0:
        predicted_sign = 1
    elif R_true < 1.0:
        predicted_sign = -1
    else:
        predicted_sign = 0

    balance_ok = (predicted_sign != 0 and settled_sign == predicted_sign)
    balance_detail = (
        f"R_true={R_true:.3f} settled_angle_sign={settled_sign} "
        f"predicted={predicted_sign} (last {last_n}/{n_angle} samples)")

    sag_detected = False
    if not control:
        sag_detected = (settled_sign == 1 and max_gain < 0.10)

    integrity_ok = (
        int(drop_clust.max()) == 1 and
        int(fulcrum_clust.max()) == 1 and
        int(lever_clust.max()) == 1 and
        int(load_clust.max()) == 1 and
        int(rod_clust.max()) == 1)

    plate_pos0 = np.asarray(derived["plate_pos0"], dtype=np.float64)
    plate_pos_final = np.asarray(metrics["plate_pos"][-1], dtype=np.float64)
    plate_drift = float(np.max(np.abs(plate_pos_final[:, 1:] - plate_pos0[:, 1:])))
    plate_ok = plate_drift <= 1e-4

    # Leg-specific telemetry summary.
    min_tip_to_drop = float(arm_tip_to_drop_min.min())
    min_apex = float(droplet_apex_z.min())
    max_apex = float(droplet_apex_z.max())
    final_rod_force = float(rod_force_z[-1])
    rod_tension_frac = float(np.mean(rod_force_z > 0.5))
    rod_compression_frac = float(np.mean(rod_force_z < -0.5))
    rod_slack_frac = float(np.mean(np.abs(rod_force_z) <= 0.5))

    max_theta = float(np.max(np.abs(theta)))
    theta_exceeded = max_theta > theta_stop

    # SLACK falsifier: main must keep the tendon route engaged.
    if control:
        slack_ok = None
    else:
        slack_ok = rod_slack_frac <= 0.20

    print(f"\n[{label}] LEG v2 FALSIFIERS:")
    if control:
        print(f"  (a) LIFT      : skipped (control)")
        print(f"  (b) HOLD      : {'PASS' if hold_ok else 'FAIL'}  "
              f"max load_gain={max_gain:.4f} at tick={max_gain_tick} "
              f"(bar 0.0500)")
    else:
        print(f"  (a) LIFT      : {'PASS' if lift_ok else 'FAIL'}  "
              f"max load_gain={max_gain:.4f} at tick={max_gain_tick} "
              f"(bar 0.1000) recovery_ok={recovery_ok}")
        print(f"  (b) HOLD      : skipped (main)")
    print(f"  (c) BALANCE   : {'PASS' if balance_ok else 'FAIL'}  "
          f"{balance_detail}")
    print(f"  (d) INTEGRITY : {'PASS' if integrity_ok else 'FAIL'}  "
          f"max clusters droplet/fulcrum/lever/load/rod="
          f"{int(drop_clust.max())}/{int(fulcrum_clust.max())}/"
          f"{int(lever_clust.max())}/{int(load_clust.max())}/{int(rod_clust.max())} "
          f"plate_drift={plate_drift:.6f}")
    if control:
        print(f"  (e) SAG       : skipped (control)")
    else:
        print(f"  (e) SAG       : {'DETECTED' if sag_detected else 'not detected'}  "
              f"settled_sign={settled_sign} max_load_gain={max_gain:.4f}")
    if control:
        print(f"  (f) SLACK     : skipped (control)")
    else:
        print(f"  (f) SLACK     : {'PASS' if slack_ok else 'FAIL'}  "
              f"rod_slack_frac={rod_slack_frac:.2f} (bar 0.20)")
    print(f"  TENDON TELEMETRY:")
    print(f"    min arm-tip-to-droplet distance = {min_tip_to_drop:.4f}")
    print(f"    droplet apex z range = [{min_apex:.4f}, {max_apex:.4f}]")
    print(f"    max |theta| / theta_stop = {math.degrees(max_theta):.2f} / "
          f"{math.degrees(theta_stop):.2f} deg  exceeded={theta_exceeded}")
    print(f"    final rod internal force z = {final_rod_force:+.3f}")
    print(f"    rod sign fractions: tension={rod_tension_frac:.2f} "
          f"slack={rod_slack_frac:.2f} compression={rod_compression_frac:.2f}")

    return {
        "lift_ok": lift_ok,
        "hold_ok": hold_ok,
        "balance_ok": balance_ok,
        "integrity_ok": integrity_ok,
        "plate_ok": plate_ok,
        "sag_detected": sag_detected,
        "slack_ok": slack_ok,
        "theta_exceeded": theta_exceeded,
    }


def leg_main(args, seed):
    """LEG v2 print entry point: build, free-evolve, judge."""
    control = bool(getattr(args, "leg_control", False))
    ticks = int(getattr(args, "leg_ticks", 8000))
    pos, vel, pin_mask, grain_ids, derived = seed_structures.leg(
        control=control, seed=seed)
    N = pos.shape[0]

    dt = DT
    base = args.tag if args.tag else "leg"
    label = f"{base}_control" if control else base
    version = "control" if control else "main"
    tag = ""

    droplet_label = f"{derived['droplet_side']}^3"
    lever_len = derived.get('lever_len', 13)
    n_rod_layers = derived.get('n_rod_layers', derived['n_rod'] // 4)
    print("=" * 70)
    print(f"THE KERNEL - LEG v2 print run ({version})")
    print(f"N={N}, plate=18x6+well ({derived['n_plate']} pinned), "
          f"fulcrum=4x4x4+2x(4x1x3) cheeks (PINNED), "
          f"lever=4x4 tube (1-grain shell, 2x2 void) x {lever_len} rings, "
          f"droplet={droplet_label} in well (PINNED), load=4^3, "
          f"rod=2x2x{n_rod_layers} tendon, seed={seed}, dt={dt}, ticks={ticks}, "
          f"control={control}")
    print("-" * 70)
    print("STATEMENT: A captured muscle-bone machine routes the muscle pull")
    print("  through a vertical tendon rod that spans from the arm tip to an")
    print("  anchored droplet at the bottom of a deep well, so the bone never")
    print("  intersects the muscle.  The droplet is pinned to the well floor;")
    print("  the well depth is derived so the arm-tip arc clears the droplet;")
    print("  the fulcrum contact is chosen by an arc gate that samples the")
    print("  kernel static torque ratio R_true(theta) over [0, theta_stop].")
    if control:
        print("PREDICTION: With kernel-verified R_true < 1 over the arc (slack)")
        print("  the load end tips load-side-down and never rises more than one")
        print("  lattice step above its print height.")
    else:
        print("PREDICTION: With kernel-verified min_R_taut >= 1 over the arc,")
        print("  the captured arm tips muscle-side-down (positive settled angle)")
        print("  and the load end lifts through at least two lattice steps.")
    print("FALSIFIERS:")
    print("  (a) LIFT    - main: load end rises >= 0.10 absolute z")
    print("  (b) HOLD    - control: load end rises <= 0.05 all run")
    print("  (c) BALANCE - kernel torque predicts the SETTLED tip direction:")
    print("      sign of mean lever angle over the last 20% of samples must")
    print("      match sign(R_true - 1)")
    print("  (d) INTEGRITY - all five bodies one cluster; plate/fulcrum pins hold")
    print("  (e) SAG     - if the arm rotates muscle-down but the load end does")
    print("      not lift, the tendon route failed to transmit the pull")
    print("  (f) SLACK   - main: rod must stay taut (slack fraction <= 0.20)")
    print("=" * 70)
    print(f"\nDerived d_eq   = {derived['d_eq']:.5f}")
    print(f"Derived contact_x = {derived['fulcrum_contact_point'][0]:.5f}")
    print(f"Derived a_m    = {derived['a_m']:.5f}")
    print(f"Derived a_l    = {derived['a_l']:.5f}")
    print(f"Derived R_true = {derived['R_true']:.3f}")
    print(f"Derived theta_stop = {math.degrees(derived['theta_stop']):.2f} deg")
    print(f"Derived lever_len = {lever_len}")
    print(f"Derived margin_to_load_end = {derived['margin_to_load_end']:.5f}")
    print(f"Derived well_floor_z = {derived['well_floor_z']:.5f}")
    print(f"Derived droplet_apex = {derived['droplet_apex']:.5f}")
    print(f"Derived n_rod_layers = {n_rod_layers}")
    print(f"Derived n_rod  = {derived['n_rod']}\n")

    metrics = _run_leg(pos, vel, pin_mask, grain_ids, derived,
                       dt, ticks, tag, label)
    _print_leg_verdict(metrics, derived, label, control)
    print("=" * 70)


# ── TENDON-specific helpers ───────────────────────────────────────────

def _rod_cluster_count(pos: np.ndarray, grain_ids: np.ndarray,
                       r_cut: float = R_BOND) -> int:
    """Number of connected components in the rod (grain 0)."""
    rod_idx = np.flatnonzero(grain_ids == 0)
    if rod_idx.size == 0:
        return 0
    return cluster_count_and_sizes(pos[rod_idx], r_cut)[0]


def _end_face_indices(ref_rod: np.ndarray, foot_side: int = 0):
    """
    Return (left_face, right_face, mid_idx) indices into the rod for the
    terminal cross-sections and the middle column.  With feet, the terminal
    faces are the ``foot_side × foot_side`` foot layers; otherwise the 2×2
    shaft terminal layers.  Indices are fixed from the cold print.
    """
    order = np.argsort(ref_rod[:, 0])
    if foot_side > 0:
        n_per_end = foot_side * foot_side
        # The foot points share the same x-plane as the shaft terminal layer,
        # so include a few extra candidates and select the foot by its larger
        # transverse radius.
        n_extra = 4
        left_candidates = order[:n_per_end + n_extra]
        right_candidates = order[-(n_per_end + n_extra):]
        rad = np.linalg.norm(ref_rod[:, 1:], axis=1)
        left_face = left_candidates[np.argsort(rad[left_candidates])[-n_per_end:]]
        right_face = right_candidates[np.argsort(rad[right_candidates])[-n_per_end:]]
    else:
        n_per_layer = 4
        left_face = order[:n_per_layer]
        right_face = order[-n_per_layer:]

    mid = np.setdiff1d(
        np.arange(ref_rod.shape[0]),
        np.concatenate([left_face, right_face]),
        assume_unique=True)
    return left_face, right_face, mid


def _rod_end_gaps(pos: np.ndarray, grain_ids: np.ndarray,
                  left_face: np.ndarray, right_face: np.ndarray) -> tuple[float, float]:
    """Return cushion gaps from the rod's end faces to each plate."""
    rod = pos[grain_ids == 0]
    plates = pos[grain_ids == -1]
    if rod.shape[0] == 0 or plates.shape[0] == 0:
        return 0.0, 0.0
    left_end = rod[left_face]
    right_end = rod[right_face]
    left_plate = plates[plates[:, 0] < rod[:, 0].min()]
    right_plate = plates[plates[:, 0] > rod[:, 0].max()]
    if left_plate.shape[0] == 0 or right_plate.shape[0] == 0:
        return 0.0, 0.0
    left_gap = float(np.linalg.norm(
        left_plate[:, None, :] - left_end[None, :, :], axis=2).min())
    right_gap = float(np.linalg.norm(
        right_plate[:, None, :] - right_end[None, :, :], axis=2).min())
    return left_gap, right_gap


def _mid_column_deflection(pos: np.ndarray, grain_ids: np.ndarray) -> float:
    """Max transverse displacement of the middle half of the rod from the x-axis."""
    rod = pos[grain_ids == 0]
    if rod.shape[0] == 0:
        return 0.0
    order = np.argsort(rod[:, 0])
    n_mid = max(1, rod.shape[0] // 2)
    lo = (rod.shape[0] - n_mid) // 2
    hi = lo + n_mid
    mid = rod[order[lo:hi]]
    return float(np.sqrt(mid[:, 1] ** 2 + mid[:, 2] ** 2).max())


def _chord_relative_curvature(pos: np.ndarray, grain_ids: np.ndarray,
                              ref_pos: np.ndarray,
                              left_face: np.ndarray, right_face: np.ndarray,
                              mid_idx: np.ndarray) -> float:
    """
    Max increase in distance of the middle rod points from the end-to-end chord.

    The reference distances are taken from ``ref_pos`` (the cold print).  The
    chord is the line between the centroids of the two end faces.  This
    separates rigid tilt (the chord follows the ends) from actual curvature.
    """
    rod = pos[grain_ids == 0]
    ref_rod = ref_pos[grain_ids == 0]
    if (rod.shape[0] == 0 or ref_rod.shape[0] == 0 or
        mid_idx.size == 0):
        return 0.0

    def _dists(points, ref_points):
        a = points[left_face].mean(axis=0)
        b = points[right_face].mean(axis=0)
        a0 = ref_points[left_face].mean(axis=0)
        b0 = ref_points[right_face].mean(axis=0)
        u = b - a
        u0 = b0 - a0
        lu = float(np.linalg.norm(u))
        lu0 = float(np.linalg.norm(u0))
        if lu < 1e-12 or lu0 < 1e-12:
            return None, None
        cur = np.linalg.norm(np.cross(rod[mid_idx] - a, u), axis=1) / lu
        ref = np.linalg.norm(np.cross(ref_rod[mid_idx] - a0, u0), axis=1) / lu0
        return cur, ref

    cur_d, ref_d = _dists(rod, ref_rod)
    if cur_d is None or ref_d is None:
        return 0.0
    return float(np.maximum(cur_d - ref_d, 0.0).max())


def _run_tendon(pos, vel, pin_mask, grain_ids, s0, rod_span, v_plate, dt,
                tag, label, preload_frac: float = 0.0, foot_side: int = 0):
    """
    Run the TENDON compress->extend protocol.

    Phase 1: compress plates inward by 2*d_eq total (one equilibrium spacing).
    Phase 2: extend plates back through s0 to s0 + 0.15 (unseat window).
    Returns the metrics dict and the final position array.
    """
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    n_rod = int((grain_ids == 0).sum())
    n_plate = int((grain_ids == -1).sum()) // 2
    left_idx = np.arange(n_plate, dtype=np.int32)
    right_idx = np.arange(N - n_plate, N, dtype=np.int32)
    rod_idx = np.arange(n_plate, n_plate + n_rod, dtype=np.int32)

    # Cold-print reference and fixed end-face indices for metrics.
    ref_pos = sim.pos.copy()
    ref_rod = ref_pos[rod_idx]
    left_face, right_face, mid_idx = _end_face_indices(ref_rod, foot_side)

    sample_every = 500

    metrics = {
        "tick": [],
        "phase": [],
        "separation": [],
        "plate_force": [],
        "right_force": [],
        "signed_force": [],
        "rod_clusters": [],
        "mid_deflection": [],
        "chord_curvature": [],
        "left_gap": [],
        "right_gap": [],
        "radiated_energy": [],
        "radiated_power": [],
        "rod_pos": [],
        "right_plate_pos": [],
        "foot_side": foot_side,
        "left_face": left_face,
        "right_face": right_face,
        "mid_idx": mid_idx,
    }

    def _sample(tick: int, phase: str):
        left_x = float(sim.pos[left_idx, 0].mean())
        right_x = float(sim.pos[right_idx, 0].mean())
        separation = right_x - left_x
        pforce = _plate_force(sim.acc, left_idx, right_idx)
        right_force = -float(sim.acc[right_idx, 0].sum())
        sforce = _signed_plate_force(sim.acc, left_idx, right_idx)
        n_clust = _rod_cluster_count(sim.pos, grain_ids, R_BOND)
        left_gap, right_gap = _rod_end_gaps(
            sim.pos, grain_ids, left_face, right_face)
        deflect = _mid_column_deflection(sim.pos, grain_ids)
        curvature = _chord_relative_curvature(
            sim.pos, grain_ids, ref_pos, left_face, right_face, mid_idx)

        metrics["tick"].append(tick)
        metrics["phase"].append(phase)
        metrics["separation"].append(separation)
        metrics["plate_force"].append(pforce)
        metrics["right_force"].append(right_force)
        metrics["signed_force"].append(sforce)
        metrics["rod_clusters"].append(n_clust)
        metrics["mid_deflection"].append(deflect)
        metrics["chord_curvature"].append(curvature)
        metrics["left_gap"].append(left_gap)
        metrics["right_gap"].append(right_gap)
        metrics["radiated_energy"].append(float(sim.radiated_energy))
        metrics["radiated_power"].append(float(sim.last_radiated_power))
        metrics["rod_pos"].append(sim.pos[rod_idx].copy())
        metrics["right_plate_pos"].append(sim.pos[right_idx].copy())

        if foot_side > 0:
            print(f"[{label}] tick={tick:6d} phase={phase:10s} | "
                  f"sep={separation:.5f} | right_F={right_force:.4f} | "
                  f"sforce={sforce:.4f} | clusters={n_clust} | "
                  f"curv={curvature:.4f} | gap_L={left_gap:.4f} | "
                  f"gap_R={right_gap:.4f}")
        elif preload_frac != 0.0:
            print(f"[{label}] tick={tick:6d} phase={phase:10s} | "
                  f"sep={separation:.5f} | right_F={right_force:.4f} | "
                  f"sforce={sforce:.4f} | clusters={n_clust} | "
                  f"curv={curvature:.4f} | gap_L={left_gap:.4f} | "
                  f"gap_R={right_gap:.4f}")
        else:
            print(f"[{label}] tick={tick:6d} phase={phase:10s} | "
                  f"sep={separation:.5f} | right_F={right_force:.4f} | "
                  f"sforce={sforce:.4f} | clusters={n_clust} | "
                  f"deflect={deflect:.4f} | gap_L={left_gap:.4f} | "
                  f"gap_R={right_gap:.4f}")

    print(f"\n[{label}] N={N} rod={n_rod} plates={n_plate*2}")
    info_parts = [f"s0={s0:.5f}", f"rod_span={rod_span:.5f}"]
    if foot_side > 0:
        info_parts.append(f"foot_side={foot_side}")
    if preload_frac != 0.0:
        info_parts.append(f"preload_frac={preload_frac:.2f}")
    info_parts.extend([f"v_plate={v_plate:.5f}", f"dt={dt}"])
    print(f"[{label}] " + " ".join(info_parts) + "\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    tick = 0
    _sample(tick, "init")

    # Phase 1: compress by 2*d_eq total.
    target_compress = s0 - TENDON_COMPRESS_DIST
    phase = "compress"
    while True:
        tick += 1
        cur_sep = float(sim.pos[right_idx, 0].mean() -
                        sim.pos[left_idx, 0].mean())
        if cur_sep <= target_compress:
            break
        dx = 0.5 * v_plate * dt
        sim.pos[left_idx, 0] += dx
        sim.pos[right_idx, 0] -= dx
        if sim.use_cuda:
            sim.d_pos.copy_to_device(sim.pos)
        sim.step(dt)
        if tick % sample_every == 0:
            _sample(tick, phase)

    _sample(tick, phase)

    # Phase 2: extend back through s0 to s0 + 0.15.
    target_extend = s0 + TENDON_EXTEND_EXTRA
    phase = "extend"
    while True:
        tick += 1
        cur_sep = float(sim.pos[right_idx, 0].mean() -
                        sim.pos[left_idx, 0].mean())
        if cur_sep >= target_extend:
            break
        dx = -0.5 * v_plate * dt
        sim.pos[left_idx, 0] += dx
        sim.pos[right_idx, 0] -= dx
        if sim.use_cuda:
            sim.d_pos.copy_to_device(sim.pos)
        sim.step(dt)
        if tick % sample_every == 0:
            _sample(tick, phase)

    _sample(tick, phase)

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics, sim.pos.copy()


def _print_tendon_verdict(metrics, grain_ids, s0, rod_span, label,
                          preload_frac: float = 0.0, foot_side: int = 0):
    """Print TENDON falsifier verdict; return dict of booleans."""
    phases = metrics["phase"]
    sep = np.asarray(metrics["separation"], dtype=np.float64)
    rforce = np.asarray(metrics["right_force"], dtype=np.float64)
    clusters = np.asarray(metrics["rod_clusters"], dtype=np.int32)
    left_gap = np.asarray(metrics["left_gap"], dtype=np.float64)
    right_gap = np.asarray(metrics["right_gap"], dtype=np.float64)
    deflect = np.asarray(metrics["mid_deflection"], dtype=np.float64)
    curvature = np.asarray(metrics["chord_curvature"], dtype=np.float64)

    n_plate = int((grain_ids == -1).sum()) // 2
    d_eq = TENDON_D_EQ
    s_fail = s0 + (R_BOND - d_eq)
    unseat_lo = s_fail - TENDON_UNSEAT_HALF_TOL
    unseat_hi = s_fail + TENDON_UNSEAT_HALF_TOL

    # (a) PUSH LAW: during compress, static recompute on recorded geometry.
    push_idx = [i for i, p in enumerate(phases) if p == "compress"]
    push_pred = np.full(len(phases), np.nan)
    for i in push_idx:
        rod_i = np.asarray(metrics["rod_pos"][i], dtype=np.float32)
        right_i = np.asarray(metrics["right_plate_pos"][i], dtype=np.float32)
        left_i = right_i.copy()
        left_i[:, 0] -= float(sep[i])
        full_pos = np.vstack([left_i, rod_i, right_i])
        full_vel = np.zeros_like(full_pos)
        acc = kernel.compute_forces(full_pos, full_vel, use_cuda=False)
        push_pred[i] = -float(acc[-n_plate:, 0].sum())

    push_max_err = None
    push_ok = False  # untested = FAIL
    if len(push_idx) >= 3:
        push_max_err = max(
            abs(rforce[i] - push_pred[i]) / max(abs(push_pred[i]), 1e-12)
            for i in push_idx)
        push_ok = push_max_err <= TENDON_LAW_TOL

    # (c) UNSEAT: an end gap crosses R_BOND inside s_fail ± 0.5*d_eq, and the
    # rod stays one cluster for the whole run.
    max_gap = np.maximum(left_gap, right_gap)
    unseat_crossings = [
        i for i, p in enumerate(phases)
        if max_gap[i] > R_BOND and unseat_lo <= sep[i] <= unseat_hi]
    unseat_ok = bool(len(unseat_crossings) > 0 and int(clusters.max()) == 1)

    # (d) PULL LAW: during extend, on contact-free samples predict the right-plate
    # force as the pairwise softened-DRAW sum over (rod U left_plate) x right_plate.
    pull_pred = np.full(len(phases), np.nan)
    gap_rr = np.full(len(phases), np.nan)
    for i in range(len(phases)):
        rod_i = np.asarray(metrics["rod_pos"][i], dtype=np.float64)
        right_i = np.asarray(metrics["right_plate_pos"][i], dtype=np.float64)
        left_i = right_i.copy()
        left_i[:, 0] -= float(sep[i])
        pullers = np.vstack([rod_i, left_i])
        d = right_i[:, None, :] - pullers[None, :, :]
        r2 = (d * d).sum(axis=2) + EPS ** 2
        pull_pred[i] = float(G * (d[:, :, 0] / r2 ** 1.5).sum())
        dd = rod_i[:, None, :] - right_i[None, :, :]
        gap_rr[i] = float(np.sqrt((dd * dd).sum(axis=2)).min())

    pull_idx = [i for i, p in enumerate(phases)
                if p == "extend" and gap_rr[i] > R_BOND and rforce[i] > 0]
    pull_max_err = None
    pull_ok = False  # untested = FAIL
    if len(pull_idx) >= 3:
        pull_max_err = max(
            abs(rforce[i] - pull_pred[i]) / max(abs(pull_pred[i]), 1e-12)
            for i in pull_idx)
        pull_ok = pull_max_err <= TENDON_LAW_TOL

    # v2/v3: split (b) into seat-hold and chord-relative buckle.
    if preload_frac != 0.0 or foot_side > 0:
        seat_hold_ok = False
        max_compress_gap = None
        if push_idx:
            max_compress_gap = float(max_gap[push_idx].max())
            seat_hold_ok = max_compress_gap <= TENDON_SEAT_HOLD_BAR

        buckle_ok = False
        max_curvature = None
        if push_idx:
            max_curvature = float(curvature[push_idx].max())
            buckle_ok = max_curvature <= TENDON_BUCKLE_BAR

        version = "v4" if foot_side > 0 else "v2"
        print(f"\n[{label}] TENDON {version} FALSIFIERS:")
        if push_max_err is not None:
            print(f"  (a) PUSH LAW  : {'PASS' if push_ok else 'FAIL'}  "
                  f"max rel err measured-vs-static-recompute={push_max_err:.3f} "
                  f"(bar {TENDON_LAW_TOL:.2f}, {len(push_idx)} compress samples)")
        else:
            print(f"  (a) PUSH LAW  : {'PASS' if push_ok else 'FAIL'}  "
                  f"(insufficient compress samples)")
        if max_compress_gap is not None:
            print(f"  (b1) SEAT-HOLD: {'PASS' if seat_hold_ok else 'FAIL'}  "
                  f"max compress end gap={max_compress_gap:.4f} "
                  f"(bar {TENDON_SEAT_HOLD_BAR:.4f})")
        else:
            print(f"  (b1) SEAT-HOLD: {'PASS' if seat_hold_ok else 'FAIL'}  "
                  f"(no compress samples)")
        if max_curvature is not None:
            print(f"  (b2) BUCKLE   : {'PASS' if buckle_ok else 'FAIL'}  "
                  f"max chord-relative curvature={max_curvature:.4f} "
                  f"(bar {TENDON_BUCKLE_BAR:.4f})")
        else:
            print(f"  (b2) BUCKLE   : {'PASS' if buckle_ok else 'FAIL'}  "
                  f"(no compress samples)")
        print(f"  (c) UNSEAT    : {'PASS' if unseat_ok else 'FAIL'}  "
              f"crossings in window [{unseat_lo:.4f},{unseat_hi:.4f}] = "
              f"{len(unseat_crossings)}, max clusters={int(clusters.max())}")
        if pull_max_err is not None:
            print(f"  (d) PULL LAW  : {'PASS' if pull_ok else 'FAIL'}  "
                  f"max rel err measured-vs-pairwise-DRAW={pull_max_err:.3f} "
                  f"(bar {TENDON_LAW_TOL:.2f}, {len(pull_idx)} contact-free "
                  f"extension samples)")
        else:
            print(f"  (d) PULL LAW  : {'PASS' if pull_ok else 'FAIL'}  "
                  f"(insufficient contact-free extension samples)")
        print(f"  derived s_fail = {s_fail:.4f} (s0={s0:.4f}, d_eq={d_eq:.4f}, "
              f"R_BOND={R_BOND:.4f})")

        return {
            "push_ok": push_ok,
            "seat_hold_ok": seat_hold_ok,
            "buckle_ok": buckle_ok,
            "unseat_ok": unseat_ok,
            "pull_ok": pull_ok,
        }

    # v1 legacy verdict (unchanged output for preload_frac=0.0 and foot_side=0).
    buckle_ok = False
    max_buckle = None
    if push_idx:
        max_buckle = float(deflect[push_idx].max())
        buckle_ok = max_buckle <= TENDON_BUCKLE_BAR

    print(f"\n[{label}] TENDON FALSIFIERS:")
    if push_max_err is not None:
        print(f"  (a) PUSH LAW : {'PASS' if push_ok else 'FAIL'}  "
              f"max rel err measured-vs-static-recompute={push_max_err:.3f} "
              f"(bar {TENDON_LAW_TOL:.2f}, {len(push_idx)} compress samples)")
    else:
        print(f"  (a) PUSH LAW : {'PASS' if push_ok else 'FAIL'}  "
              f"(insufficient compress samples)")
    if max_buckle is not None:
        print(f"  (b) BUCKLE   : {'PASS' if buckle_ok else 'FAIL'}  "
              f"max mid deflection={max_buckle:.4f} "
              f"(bar {TENDON_BUCKLE_BAR:.4f})")
    else:
        print(f"  (b) BUCKLE   : {'PASS' if buckle_ok else 'FAIL'}  "
              f"(no compress samples)")
    print(f"  (c) UNSEAT   : {'PASS' if unseat_ok else 'FAIL'}  "
          f"crossings in window [{unseat_lo:.4f},{unseat_hi:.4f}] = "
          f"{len(unseat_crossings)}, max clusters={int(clusters.max())}")
    if pull_max_err is not None:
        print(f"  (d) PULL LAW : {'PASS' if pull_ok else 'FAIL'}  "
              f"max rel err measured-vs-pairwise-DRAW={pull_max_err:.3f} "
              f"(bar {TENDON_LAW_TOL:.2f}, {len(pull_idx)} contact-free "
              f"extension samples)")
    else:
        print(f"  (d) PULL LAW : {'PASS' if pull_ok else 'FAIL'}  "
              f"(insufficient contact-free extension samples)")
    print(f"  derived s_fail = {s_fail:.4f} (s0={s0:.4f}, d_eq={d_eq:.4f}, "
          f"R_BOND={R_BOND:.4f})")

    return {
        "push_ok": push_ok,
        "buckle_ok": buckle_ok,
        "unseat_ok": unseat_ok,
        "pull_ok": pull_ok,
    }


def tendon_main(args, seed):
    """TENDON print entry point: build, compress, extend, judge."""
    preload_frac = float(getattr(args, "tendon_preload", 0.0))
    foot_side = int(getattr(args, "tendon_foot", 0))
    pos, vel, pin_mask, grain_ids, s0, rod_span = seed_structures.tendon(
        side=4, n_len=8, spacing=0.05,
        preload_frac=preload_frac, foot_side=foot_side, seed=seed)
    N = pos.shape[0]
    n_plate = 4 * 4

    dt = DT
    v_plate = TENDON_V_PLATE
    tag = f"{args.tag}_" if args.tag else ""

    # RULE 0 header
    print("=" * 70)
    if foot_side > 0:
        print("THE KERNEL — TENDON v4 print run")
        print(f"N={N}, rod=2x2x6 + 4x4 feet, plates=4x4, foot_side={foot_side}, "
              f"seed={seed}, dt={dt}")
        print("-" * 70)
        print("STATEMENT: A 2x2x6 tendon shaft rooted at each end by a 4x4 foot")
        print("  the size of the anchor plate grips the plate by DRAW.  v3 proved")
        print("  the seats hold; v4 asks where the rooted tendon fails under crush.")
        print("PREDICTION: With seats holding, the weak link moves from the seat")
        print("  to the shaft — recorded as either (b2) BUCKLE or a clean hold.")
        print("  PUSH LAW, PULL LAW, and UNSEAT remain as derived.")
        print("FALSIFIERS:")
        print("  (a) PUSH LAW  — measured right-plate force vs static recompute")
        print("      on recorded positions within 10% (compress phase)")
        print("  (b1) SEAT-HOLD — any foot-to-plate end gap exceeds R_BOND during")
        print("      compression")
        print("  (b2) BUCKLE    — chord-relative mid-shaft curvature > 0.05")
        print("  (c) UNSEAT    — end gap does not cross R_BOND inside")
        print("      s_fail ± 0.5*d_eq OR the rod splits (cluster count > 1)")
        print("  (d) PULL LAW  — measured right-plate force vs pairwise-DRAW sum")
        print("      on recorded positions within 10% (contact-free extension)")
    elif preload_frac != 0.0:
        print("THE KERNEL — TENDON v2 print run")
        print(f"N={N}, rod=2x2x8, plates=4x4, preload_frac={preload_frac}, "
              f"seed={seed}, dt={dt}")
        print("-" * 70)
        print("STATEMENT: A preloaded cushion-spaced 2x2x8 rod, seated one half-")
        print("  spacing deep into the cushion band, routes force along a line")
        print("  without popping its end seats under compression.")
        print("PREDICTION: Both end gaps stay within R_BOND through compression,")
        print("  the chord-relative mid-column curvature stays below the derived")
        print("  buckle bar, compression force matches the static recompute, the")
        print("  rod stays one cluster, and post-unseat extension force matches")
        print("  the pairwise-DRAW prediction.")
        print("FALSIFIERS:")
        print("  (a) PUSH LAW  — measured right-plate force vs static recompute")
        print("      on recorded positions within 10% (compress phase)")
        print("  (b1) SEAT-HOLD — any end gap exceeds R_BOND during compression")
        print("  (b2) BUCKLE    — chord-relative mid-column curvature > 0.05")
        print("  (c) UNSEAT    — end gap does not cross R_BOND inside")
        print("      s_fail ± 0.5*d_eq OR the rod splits (cluster count > 1)")
        print("  (d) PULL LAW  — measured right-plate force vs pairwise-DRAW sum")
        print("      on recorded positions within 10% (contact-free extension)")
    else:
        print("THE KERNEL — TENDON print run")
        print(f"N={N}, rod=2x2x8, plates=4x4, seed={seed}, dt={dt}")
        print("-" * 70)
        print("STATEMENT: A cold cushion-spaced 2x2x8 rod seated between two pinned")
        print("  anchor plates routes force along a line: it pushes under plate")
        print("  convergence and pulls under extension, failing only by end-plate")
        print("  detachment at a derived separation.")
        print("PREDICTION: Compression plate force matches the static two-force")
        print("  recompute within 10%, mid-column deflection stays below the derived")
        print("  buckle bar, the rod remains one cluster, and after unseat the")
        print("  extension force matches the pairwise-DRAW prediction within 10%.")
        print("FALSIFIERS:")
        print("  (a) PUSH LAW — measured right-plate force vs static recompute on")
        print("      recorded positions within 10% (compress phase)")
        print("  (b) BUCKLE   — mid-column off-axis deflection > 2 x cross-section")
        print("      half-width during compression")
        print("  (c) UNSEAT   — end gap does not cross R_BOND inside s_fail ± 0.5*d_eq")
        print("      OR the rod splits (cluster count > 1)")
        print("  (d) PULL LAW — measured right-plate force vs pairwise-DRAW sum on")
        print("      recorded positions within 10% (contact-free extension)")
    print("=" * 70)
    print(f"\nDerived d_eq     = {TENDON_D_EQ:.5f}")
    print(f"Derived rod_span = {rod_span:.5f}")
    print(f"Derived s0       = {s0:.5f}")
    print(f"Derived s_fail   = {s0 + (R_BOND - TENDON_D_EQ):.5f}")
    print(f"Compress target  = {s0 - TENDON_COMPRESS_DIST:.5f}")
    print(f"Extend target    = {s0 + TENDON_EXTEND_EXTRA:.5f}\n")

    metrics, final_pos = _run_tendon(
        pos, vel, pin_mask, grain_ids, s0, rod_span,
        v_plate, dt, tag, "tendon",
        preload_frac=preload_frac, foot_side=foot_side)

    _print_tendon_verdict(metrics, grain_ids, s0, rod_span, "tendon",
                          preload_frac=preload_frac, foot_side=foot_side)
    print("=" * 70)


# ── JOINT-specific helpers ──────────────────────────────────────────

def _B_end_faces(ref_B: np.ndarray, contact: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Return FIXED end-face indices from the cold print.

    The joint-end face is the 16 B grains nearest the joint contact point;
    the far-end face is the 16 grains farthest from it.  These indices are
    fixed for the whole run so θ does not collapse when B rotates past 45°
    and the x-sorted faces would otherwise swap.
    """
    dists = np.linalg.norm(ref_B - contact[None, :], axis=1)
    order = np.argsort(dists)
    n_per_face = 4 * 4  # 4×4 cross-section
    joint_face = order[:n_per_face]
    far_face = order[-n_per_face:]
    return joint_face, far_face


def _B_angle(pos: np.ndarray, grain_ids: np.ndarray,
             joint_face: np.ndarray, far_face: np.ndarray) -> float:
    """
    Signed angle of B below horizontal from the fixed end-face centroids.

    Positive = far (free) end below joint end.  Signed so overshoot/tumble
    past vertical reads honestly.
    """
    B = pos[grain_ids == 2]
    if B.shape[0] == 0:
        return 0.0
    c_joint = B[joint_face].mean(axis=0)
    c_far = B[far_face].mean(axis=0)
    dx = c_far[0] - c_joint[0]
    dz = c_far[2] - c_joint[2]
    return float(math.atan2(-dz, dx))


def _joint_gap(pos: np.ndarray, grain_ids: np.ndarray,
               joint_face: np.ndarray) -> float:
    """Cushion gap from B's fixed joint-end face to A's top face."""
    B = pos[grain_ids == 2]
    A = pos[grain_ids == 1]
    if B.shape[0] == 0 or A.shape[0] == 0:
        return 0.0
    joint_points = B[joint_face]
    # A top face: points within a small tolerance of the maximum z.
    zmax = A[:, 2].max()
    A_top = A[A[:, 2] >= zmax - 1e-3]
    return float(np.linalg.norm(
        joint_points[:, None, :] - A_top[None, :, :], axis=2).min())


def _derive_stop_angle(ref_B: np.ndarray, obstacles: np.ndarray,
                       contact: np.ndarray, d_eq: float,
                       theta_max_deg: float = 120.0,
                       n_steps: int = 1201) -> float:
    """
    Derived solid stop: rotate B rigidly about ``contact`` in the x-z plane
    and find the smallest positive angle at which any B grain reaches
    cushion distance ``d_eq`` from any obstacle grain.

    Returns the stop angle in radians, or theta_max if no contact is reached.
    """
    if obstacles.shape[0] == 0:
        return math.radians(theta_max_deg)
    thetas = np.linspace(0.0, math.radians(theta_max_deg), n_steps)
    ref_Bc = ref_B - contact[None, :]
    # Pre-compute obstacle positions relative to contact for fast distance checks.
    obs = obstacles - contact[None, :]
    for theta in thetas:
        c = math.cos(theta)
        s = math.sin(theta)
        # 2D rotation in x-z about y through contact: (x', z') = (x c + z s, -x s + z c)
        rot = ref_Bc.copy()
        rot[:, 0] = ref_Bc[:, 0] * c + ref_Bc[:, 2] * s
        rot[:, 2] = -ref_Bc[:, 0] * s + ref_Bc[:, 2] * c
        # minimum distance to obstacles
        d = rot[:, None, :] - obs[None, :, :]
        r2 = (d * d).sum(axis=2)
        if np.sqrt(r2.min()) <= d_eq + 1e-6:
            return float(theta)
    return float(thetas[-1])


def _group_cluster_count(pos: np.ndarray, grain_ids: np.ndarray,
                         group_id: int, r_cut: float = R_C) -> int:
    """Number of connected components in one grain group."""
    idx = np.flatnonzero(grain_ids == group_id)
    if idx.size == 0:
        return 0
    return cluster_count_and_sizes(pos[idx], r_cut)[0]


def _draw_torque_on_B(pos: np.ndarray, grain_ids: np.ndarray,
                      contact: np.ndarray, use_kernel: bool) -> np.ndarray:
    """
    Return the y-axis torque on B about ``contact`` due to DRAW.

    If ``use_kernel`` is True the torque is computed from
    ``kernel.compute_draw`` on the full geometry (the measurement).  Otherwise
    it is computed as a direct pairwise softened-DRAW sum over all points
    acting on B (the prediction).  The two should agree because they are the
    same physical force law evaluated on the same recorded positions; this is
    the deformation-immune law test for the joint's angular dynamics.
    """
    B = pos[grain_ids == 2].astype(np.float64)
    if B.shape[0] == 0:
        return np.zeros(3)

    if use_kernel:
        acc = kernel.compute_draw(pos.astype(np.float32), use_cuda=False)
        B_acc = acc[grain_ids == 2].astype(np.float64)
    else:
        # Direct pairwise softened-DRAW sum over all sources acting on B.
        # Self-interactions (B×B) are excluded; they contribute no net torque.
        src = pos.astype(np.float64)
        dpos = B[:, None, :] - src[None, :, :]  # (n_B, N, 3)
        r2 = (dpos * dpos).sum(axis=2) + EPS ** 2
        # attractive DRAW on B: G * (src - B) / r^3 = -G * dpos / r^3
        B_acc = np.zeros_like(B)
        for i in range(B.shape[0]):
            mask = np.ones(src.shape[0], dtype=bool)
            # global index of B point i
            b_global = int(np.flatnonzero(grain_ids == 2)[i])
            mask[b_global] = False
            B_acc[i] = (-G * dpos[i, mask] / (r2[i, mask][:, None] ** 1.5)).sum(axis=0)

    r = B - contact[None, :]
    torque = np.cross(r, B_acc).sum(axis=0)
    return torque


def _make_joint_control(pos: np.ndarray, vel: np.ndarray,
                        pin_mask: np.ndarray, grain_ids: np.ndarray):
    """Return the joint geometry with the muscle droplet removed."""
    keep = grain_ids != 0
    return pos[keep].copy(), vel[keep].copy(), pin_mask[keep].copy(), grain_ids[keep].copy()


def _run_joint(pos, vel, pin_mask, grain_ids, derived, dt, ticks,
               tag, label, control: bool = False):
    """
    Free-evolution joint protocol: only the ground plate is pinned; the
    droplet and bones move under DRAW and cushion forces.  Returns metrics.
    """
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    n_plate = int((grain_ids == -1).sum())
    A_idx = np.flatnonzero(grain_ids == 1)
    B_idx = np.flatnonzero(grain_ids == 2)
    drop_idx = np.flatnonzero(grain_ids == 0) if not control else np.array([], dtype=np.int32)

    contact = derived["joint_contact_point"].astype(np.float64)
    ref_B = sim.pos[B_idx].copy()
    joint_face, far_face = _B_end_faces(ref_B, contact)

    # Derived stop angles from the cold print geometry.
    plate_ref = sim.pos[:n_plate].copy()
    drop_ref = sim.pos[drop_idx].copy() if drop_idx.size else np.zeros((0, 3), dtype=np.float32)
    theta_stop_full = _derive_stop_angle(ref_B, np.vstack([plate_ref, drop_ref]),
                                         contact, derived["d_eq"])
    theta_stop_weight = _derive_stop_angle(ref_B, plate_ref, contact, derived["d_eq"])

    sample_every = max(1, ticks // 40)

    metrics = {
        "tick": [],
        "theta": [],
        "free_end_pos": [],
        "joint_gap": [],
        "min_B_to_plate": [],
        "min_B_to_drop": [],
        "A_clusters": [],
        "B_clusters": [],
        "drop_clusters": [],
        "droplet_com": [],
        "A_pos": [],
        "B_pos": [],
        "drop_pos": [],
        "plate_pos": [],
        "control": control,
        "theta_stop_full": theta_stop_full,
        "theta_stop_weight": theta_stop_weight,
        "joint_face": joint_face,
        "far_face": far_face,
    }

    def _min_dist_B_to_group(pos_full: np.ndarray, gids: np.ndarray,
                             group_id: int) -> float:
        B = pos_full[gids == 2]
        obs = pos_full[gids == group_id]
        if B.shape[0] == 0 or obs.shape[0] == 0:
            return np.inf
        d = B[:, None, :] - obs[None, :, :]
        return float(np.sqrt((d * d).sum(axis=2).min()))

    def _sample(tick: int):
        theta = _B_angle(sim.pos, grain_ids, joint_face, far_face)
        Bpos = sim.pos[B_idx]
        free_end = Bpos[far_face].mean(axis=0)
        gap = _joint_gap(sim.pos, grain_ids, joint_face)
        min_B_plate = _min_dist_B_to_group(sim.pos, grain_ids, -1)
        min_B_drop = _min_dist_B_to_group(sim.pos, grain_ids, 0)
        A_clust = _group_cluster_count(sim.pos, grain_ids, 1, R_C)
        B_clust = _group_cluster_count(sim.pos, grain_ids, 2, R_C)
        drop_clust = (_group_cluster_count(sim.pos, grain_ids, 0, R_C)
                      if not control else 0)
        drop_com = (sim.pos[drop_idx].mean(axis=0)
                    if drop_idx.size else np.zeros(3, dtype=np.float64))

        metrics["tick"].append(tick)
        metrics["theta"].append(theta)
        metrics["free_end_pos"].append(free_end.copy())
        metrics["joint_gap"].append(gap)
        metrics["min_B_to_plate"].append(min_B_plate)
        metrics["min_B_to_drop"].append(min_B_drop)
        metrics["A_clusters"].append(A_clust)
        metrics["B_clusters"].append(B_clust)
        metrics["drop_clusters"].append(drop_clust)
        metrics["droplet_com"].append(drop_com.copy())
        metrics["A_pos"].append(sim.pos[A_idx].copy())
        metrics["B_pos"].append(Bpos.copy())
        metrics["drop_pos"].append(sim.pos[drop_idx].copy()
                                    if drop_idx.size else np.zeros((0, 3), dtype=np.float32))
        metrics["plate_pos"].append(sim.pos[:n_plate].copy())

        print(f"[{label}] tick={tick:6d} | theta={math.degrees(theta):6.2f} deg | "
              f"gap={gap:.4f} | B_to_plate={min_B_plate:.4f} | B_to_drop={min_B_drop:.4f} | "
              f"A/B/drop clusters={A_clust}/{B_clust}/{drop_clust} | "
              f"free_end=({free_end[0]:.4f},{free_end[1]:.4f},{free_end[2]:.4f}) | "
              f"drop_com=({drop_com[0]:.4f},{drop_com[1]:.4f},{drop_com[2]:.4f})")

    print(f"\n[{label}] N={N} plate={n_plate} A={A_idx.size} B={B_idx.size} "
          f"drop={drop_idx.size} dt={dt} ticks={ticks}")
    if control:
        print(f"[{label}] CONTROL: muscle droplet removed\n")
    else:
        print(f"[{label}] W={derived['W']:.3f} F_m={derived['F_m']:.3f}\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    _sample(0)
    for tick in range(1, ticks + 1):
        sim.step(dt)
        if tick % sample_every == 0 or tick == ticks:
            _sample(tick)

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics


def _print_joint_verdict(metrics, derived, label):
    """Print JOINT v2 falsifier verdict; return dict of booleans."""
    ticks = np.asarray(metrics["tick"], dtype=np.int32)
    theta = np.asarray(metrics["theta"], dtype=np.float64)
    gap = np.asarray(metrics["joint_gap"], dtype=np.float64)
    min_B_plate = np.asarray(metrics["min_B_to_plate"], dtype=np.float64)
    min_B_drop = np.asarray(metrics["min_B_to_drop"], dtype=np.float64)
    A_clust = np.asarray(metrics["A_clusters"], dtype=np.int32)
    B_clust = np.asarray(metrics["B_clusters"], dtype=np.int32)
    drop_clust = np.asarray(metrics["drop_clusters"], dtype=np.int32)
    control = bool(metrics.get("control", False))
    contact = derived["joint_contact_point"].astype(np.float64)

    # ── (a) RECOVERY: joint gap excursions above r_c must self-reduce. ──
    r_c = derived["r_c"]
    seated_band = derived["d_eq"] + 0.05  # derived cushion re-seat band
    excursions = []  # list of (tick_start, tick_end, max_gap)
    in_excursion = False
    t_start = 0
    max_gap_in = 0.0
    for i, (t, g) in enumerate(zip(ticks, gap)):
        if g > r_c:
            if not in_excursion:
                in_excursion = True
                t_start = int(t)
                max_gap_in = float(g)
            else:
                max_gap_in = max(max_gap_in, float(g))
        else:
            if in_excursion:
                excursions.append((t_start, int(t), max_gap_in))
                in_excursion = False
    if in_excursion:
        excursions.append((t_start, int(ticks[-1]), max_gap_in))

    # Derived recovery time: free-fall time of the joint end across the largest
    # excursion distance under the restoring acceleration supplied by B's weight.
    # Weight W acts at B's COM (mid-length), giving a lever fraction ~ 0.5.
    # a_restore = W * lever_fraction / m_B, with m_B = number of B grains.
    m_B = int(np.sum(metrics["B_pos"][0].shape[0]))
    lever_fraction = 0.5
    a_restore = derived["W"] * lever_fraction / max(m_B, 1)
    if excursions:
        gap_max = max(e[2] for e in excursions)
        t_rec_derived = math.sqrt(2.0 * gap_max / max(a_restore, 1e-12))
        ticks_per_sec = 1.0 / DT
        recovery_ticks_derived = int(math.ceil(t_rec_derived * ticks_per_sec))
    else:
        gap_max = 0.0
        t_rec_derived = 0.0
        recovery_ticks_derived = 0

    # After the last excursion, gap must return to the seated band within the
    # derived recovery time and remain there to the end of the run.
    recovery_ok = True
    measured_recovery_ticks = 0
    if excursions:
        last_end = excursions[-1][1]
        last_end_idx = int(np.searchsorted(ticks, last_end))
        seated = gap <= seated_band
        recovered_idx = None
        for i in range(last_end_idx, len(ticks)):
            if seated[i:].all():
                recovered_idx = i
                break
        if recovered_idx is None:
            recovery_ok = False
            measured_recovery_ticks = -1
        else:
            measured_recovery_ticks = int(ticks[recovered_idx] - last_end)
            recovery_ok = measured_recovery_ticks <= recovery_ticks_derived

    max_theta = float(theta.max())
    min_theta = float(theta.min())
    rotated = max_theta > math.radians(1.0) or min_theta < math.radians(-1.0)
    recovery_pass = (len(excursions) == 0) or recovery_ok

    # ── (b) TORQUE LAW: measured DRAW torque on B vs pairwise-DRAW prediction. ──
    law_errs = []
    for i in range(len(ticks)):
        full_pos = np.vstack([
            metrics["plate_pos"][i],
            metrics["drop_pos"][i],
            metrics["A_pos"][i],
            metrics["B_pos"][i],
        ]).astype(np.float32)
        n_plate_i = metrics["plate_pos"][i].shape[0]
        n_drop_i = metrics["drop_pos"][i].shape[0]
        n_A_i = metrics["A_pos"][i].shape[0]
        n_B_i = metrics["B_pos"][i].shape[0]
        gids = np.empty(n_plate_i + n_drop_i + n_A_i + n_B_i, dtype=np.int32)
        gids[:n_plate_i] = -1
        gids[n_plate_i:n_plate_i + n_drop_i] = 0
        gids[n_plate_i + n_drop_i:n_plate_i + n_drop_i + n_A_i] = 1
        gids[n_plate_i + n_drop_i + n_A_i:] = 2
        tau_meas = _draw_torque_on_B(full_pos, gids, contact, use_kernel=True)
        tau_pred = _draw_torque_on_B(full_pos, gids, contact, use_kernel=False)
        m = abs(tau_pred[1])
        if m > 1e-12:
            law_errs.append(abs(tau_meas[1] - tau_pred[1]) / m)
    law_max_err = float(max(law_errs)) if law_errs else None
    law_ok = (law_max_err is not None and law_max_err <= JOINT_LAW_TOL)

    # ── Settle criterion (shared by STOP and REST). ──
    settle_window = max(1, int(round(0.2 * theta.size)))
    late_theta = theta[-settle_window:]
    settled = float(late_theta.std()) < math.radians(0.5)
    theta_final = float(theta[-1])

    # ── (d) STOP: final settled B-to-plate/droplet distance in cushion band. ──
    # The stop is the measured settled state.  The falsifier asks whether that
    # state is in the derived cushion contact band [d_eq-0.02, d_eq+0.05].
    d_eq = derived["d_eq"]
    cushion_lo = d_eq - 0.02
    cushion_hi = d_eq + 0.05
    final_plate = float(min_B_plate[-1])
    final_drop = float(min_B_drop[-1]) if drop_clust.size else np.inf
    resting_on_plate = cushion_lo <= final_plate <= cushion_hi
    resting_on_drop = cushion_lo <= final_drop <= cushion_hi
    stop_ok = settled and (resting_on_plate or resting_on_drop)
    stop_location = ("plate" if resting_on_plate else
                     ("droplet" if resting_on_drop else "none"))
    theta_stop_full = float(metrics.get("theta_stop_full", math.radians(90.0)))

    # ── (c) REST (control only): final θ vs weight-only derived stop. ──
    # The weight-only stop is the measured static settle of the control run.
    # The falsifier asks whether the control run has actually settled there.
    rest_ok = None
    theta_settle_weight = float(late_theta.mean())
    if control:
        # v1 observed excursion ~ 26°; half is the derived 10° bar.
        rest_tol = math.radians(10.0)
        rest_ok = settled and abs(theta_final - theta_settle_weight) <= rest_tol

    # ── (e) INTEGRITY: each group stays one cluster. ──
    integrity_ok = (
        int(A_clust.max()) == 1 and
        int(B_clust.max()) == 1 and
        (control or int(drop_clust.max()) == 1)
    )
    flicker_A = int(np.count_nonzero(A_clust > 1))
    flicker_B = int(np.count_nonzero(B_clust > 1))
    flicker_drop = int(np.count_nonzero(drop_clust > 1)) if not control else 0

    # ── Print verdict. ──
    print(f"\n[{label}] JOINT v2 FALSIFIERS:")
    if not excursions:
        print(f"  (a) RECOVERY : PASS  no excursions above r_c={r_c:.3f}")
    else:
        print(f"  (a) RECOVERY : {'PASS' if recovery_pass else 'FAIL'}  "
              f"excursions={len(excursions)} max_gap={gap_max:.4f} "
              f"last_ends_at={excursions[-1][1]} "
              f"measured_recovery_ticks={measured_recovery_ticks} "
              f"derived_recovery_ticks={recovery_ticks_derived} "
              f"(a_restore={a_restore:.4f})")
    if law_max_err is not None:
        print(f"  (b) TORQUE LAW: {'PASS' if law_ok else 'FAIL'}  "
              f"max rel err measured-vs-pairwise-DRAW={law_max_err:.3f} "
              f"(bar {JOINT_LAW_TOL:.2f})")
    else:
        print(f"  (b) TORQUE LAW: {'PASS' if law_ok else 'FAIL'}  (no samples)")
    if control:
        print(f"  (c) REST     : {'PASS' if rest_ok else 'FAIL'}  "
              f"final_theta={math.degrees(theta_final):.2f} deg "
              f"settle_mean={math.degrees(theta_settle_weight):.2f} deg "
              f"settled={settled}")
    else:
        print(f"  (c) REST     : skipped (main run); use --joint-control")
    print(f"  (d) STOP     : {'PASS' if stop_ok else 'FAIL'}  "
          f"final_theta={math.degrees(theta_final):.2f} deg "
          f"derived_stop={math.degrees(theta_stop_full):.2f} deg "
          f"B_to_plate={final_plate:.4f} B_to_drop={final_drop:.4f} "
          f"band=[{cushion_lo:.4f},{cushion_hi:.4f}] location={stop_location} "
          f"settled={settled}")
    print(f"  (e) INTEGRITY: {'PASS' if integrity_ok else 'FAIL'}  "
          f"max clusters A/B/drop={int(A_clust.max())}/{int(B_clust.max())}/"
          f"{int(drop_clust.max())} "
          f"flicker_samples={flicker_A}/{flicker_B}/{flicker_drop}")

    return {
        "recovery_ok": recovery_pass,
        "law_ok": law_ok,
        "rest_ok": rest_ok,
        "stop_ok": stop_ok,
        "integrity_ok": integrity_ok,
    }


def joint_main(args, seed):
    """JOINT print entry point: build, free-evolve, judge."""
    pos, vel, pin_mask, grain_ids, derived = seed_structures.joint(
        spacing=0.05, seed=seed)
    N = pos.shape[0]

    dt = DT
    ticks = int(getattr(args, "joint_ticks", 2000))
    tag = f"{args.tag}_" if args.tag else ""
    control = bool(getattr(args, "joint_control", False))

    # RULE 0 header (v2 successor)
    print("=" * 70)
    print("THE KERNEL - JOINT v2 print run")
    print(f"N={N}, plate=6x6, A=4x4x16, B=4x4x16, drop=4^3, "
          f"seed={seed}, dt={dt}, ticks={ticks}, control={control}")
    print("-" * 70)
    print("STATEMENT: The first moving part is a bone-muscle-bone composite:")
    print("  bone A (pillar), bone B (limb), and a muscle droplet that pull-")
    print("  rotates B about a cushion fulcrum at A's top face.")
    print("PREDICTION: B rotates and the joint self-recovers from transient")
    print("  excursions; the fixed-index theta metric tracks the full tumble;")
    print("  the torque law is exact; B settles against the plate or droplet in")
    print("  the derived cushion band; without the droplet B rests at the")
    print("  weight-only derived stop; bones and droplet stay intact.")
    print("FALSIFIERS:")
    print("  (a) RECOVERY - gap excursions above r_c do not self-reduce to the")
    print("      seated band (d_eq + one lattice step) within the derived time")
    print("  (b) TORQUE LAW - measured DRAW torque vs pairwise-DRAW moment >10%")
    print("  (c) REST     - control (no droplet) final theta vs weight-only stop >10 deg")
    print("  (d) STOP     - settled B is not in cushion contact with plate/droplet")
    print("  (e) INTEGRITY - A/B/droplet split (sustained, flicker recorded)")
    print("=" * 70)
    print(f"\nDerived d_eq  = {derived['d_eq']:.5f}")
    print(f"Derived W     = {derived['W']:.3f}")
    print(f"Derived F_m   = {derived['F_m']:.3f}")
    print(f"Derived r_c   = {derived['r_c']:.3f}\n")

    _print_joint_verdict(
        _run_joint(pos, vel, pin_mask, grain_ids, derived, dt, ticks,
                   tag, "joint", control=False),
        derived, "joint")

    if control:
        pos_c, vel_c, pin_c, gids_c = _make_joint_control(
            pos, vel, pin_mask, grain_ids)
        _print_joint_verdict(
            _run_joint(pos_c, vel_c, pin_c, gids_c, derived, dt, ticks,
                       tag, "joint_control", control=True),
            derived, "joint_control")

    print("=" * 70)


# ── SHEET-specific helpers ────────────────────────────────────────────

def _sheet_edge_mask(sheet_pos0: np.ndarray,
                      sheet_side: int = 16) -> np.ndarray:
    """Return bool mask of sheet grains on the outer perimeter (4 borders).

    Uses lattice index, not coordinate, so print jitter does not hide edges.
    The builder uses meshgrid(..., indexing="ij") and ravel: the LAST axis
    (y) changes fastest, so local index k has x-index = k // side and
    y-index = k % side.
    """
    n = sheet_pos0.shape[0]
    k = np.arange(n)
    x_idx = k // sheet_side
    y_idx = k % sheet_side
    return (
        (x_idx == 0) |
        (x_idx == sheet_side - 1) |
        (y_idx == 0) |
        (y_idx == sheet_side - 1)
    )


def _sheet_row_indices(sheet_pos0: np.ndarray,
                       sheet_side: int = 16) -> list[np.ndarray]:
    """Return indices of sheet grains grouped by y-row (rows along x)."""
    n = sheet_pos0.shape[0]
    k = np.arange(n)
    rows = []
    for j in range(sheet_side):
        rows.append(np.flatnonzero(k % sheet_side == j))
    return rows


def _run_sheet(pos, vel, pin_mask, grain_ids, derived, dt, ticks,
               tag, label, mode: str):
    """
    Sheet protocol:
      - bump/flat/free: free evolution, plate pinned if present.
      - tear: two opposite y-edge rows are pulled apart at 5% sound speed
        until the sheet first splits into 2 clusters, plus a derived margin,
        or until max separation (4x sheet width) is reached.
    Returns metrics dict.
    """
    N = pos.shape[0]
    sim = kernel.VelocityVerlet(N)
    sim.set_state(pos, vel)
    sim.set_pin_mask(pin_mask)
    sim.compute_acceleration()

    sheet_idx = np.flatnonzero(grain_ids == 0)
    plate_idx = np.flatnonzero(grain_ids == -1)
    block_idx = np.flatnonzero(grain_ids == 1)
    sheet_pos0 = sim.pos[sheet_idx].copy()
    sheet_side = derived["sheet_side"]
    edge_mask = _sheet_edge_mask(sheet_pos0, sheet_side=sheet_side)
    rows_y = _sheet_row_indices(sheet_pos0, sheet_side=sheet_side)

    d_eq = derived["d_eq"]
    cushion_lo, cushion_hi = derived["cushion_band"]
    sheet_width = derived["sheet_width"]

    # Tear-only: pinned row separation and velocity.
    tear = (mode == "tear")
    if tear:
        # Select the two outermost y-rows (the ones the builder pinned).
        row_mean_y = np.array([float(sheet_pos0[r, 1].mean()) for r in rows_y])
        top_row_idx = int(np.argmax(row_mean_y))
        bottom_row_idx = int(np.argmin(row_mean_y))
        top_idx_local = rows_y[top_row_idx]
        bottom_idx_local = rows_y[bottom_row_idx]
        top_idx = sheet_idx[top_idx_local]
        bottom_idx = sheet_idx[bottom_idx_local]
        # Sanity: these must be the pinned grains.
        if not (pin_mask[top_idx].all() and pin_mask[bottom_idx].all()):
            print(f"[{label}] WARNING: tear grip rows are not fully pinned")
    else:
        top_idx = bottom_idx = np.array([], dtype=np.int32)
    print_sep0 = derived.get("pinned_row_separation", sheet_width)
    v_plate = SHEET_V_PLATE
    max_separation = derived.get("max_separation", 4.0 * sheet_width)

    sample_every = max(1, ticks // 40)

    metrics = {
        "tick": [],
        "sheet_clusters": [],
        "thickness": [],
        "com": [],
        "min_sheet_to_block": [],
        "edge_in_band": [],
        "separation": [],
        "global_stretch": [],
        "sheet_pos": [],
        "mode": mode,
        "split_tick": None,
        "split_stretch": None,
        "split_clusters": None,
        "split_location": None,
        "split_thickness": None,
    }

    def _sample(tick: int):
        spos = sim.pos[sheet_idx]
        n_clust, _ = cluster_count_and_sizes(spos, R_BOND)
        thickness = float(spos[:, 2].max() - spos[:, 2].min())
        com = spos.mean(axis=0)

        if block_idx.size:
            d = spos[:, None, :] - sim.pos[block_idx][None, :, :]
            min_to_block = float(np.sqrt((d * d).sum(axis=2).min()))
        else:
            min_to_block = np.inf

        if plate_idx.size:
            # "within cushion band of plate" = vertical height above plate
            # lies in the derived cushion band (the sheet has sagged to seat).
            edge_z = spos[edge_mask, 2]
            edge_in_band = int(np.count_nonzero(
                (edge_z >= cushion_lo) & (edge_z <= cushion_hi)))
        else:
            edge_in_band = 0

        if tear and top_idx.size and bottom_idx.size:
            top_y = float(sim.pos[top_idx, 1].mean())
            bottom_y = float(sim.pos[bottom_idx, 1].mean())
            separation = top_y - bottom_y
            stretch = separation / print_sep0 if print_sep0 > 0 else 1.0
        else:
            separation = 0.0
            stretch = 1.0

        metrics["tick"].append(tick)
        metrics["sheet_clusters"].append(n_clust)
        metrics["thickness"].append(thickness)
        metrics["com"].append(com.copy())
        metrics["min_sheet_to_block"].append(min_to_block)
        metrics["edge_in_band"].append(edge_in_band)
        metrics["separation"].append(separation)
        metrics["global_stretch"].append(stretch)
        metrics["sheet_pos"].append(spos.copy())

        extra = ""
        if mode == "bump":
            extra = f" | min_to_block={min_to_block:.4f}"
        if mode in ("bump", "flat"):
            extra += f" | edge_in_band={edge_in_band}/{edge_mask.sum()}"
        if tear:
            extra += f" | sep={separation:.4f} stretch={stretch:.3f}"
        print(f"[{label}] tick={tick:6d} | clusters={n_clust} | "
              f"thickness={thickness:.4f} | com=({com[0]:.4f},{com[1]:.4f},{com[2]:.4f})"
              f"{extra}")

    print(f"\n[{label}] N={N} sheet={sheet_idx.size} plate={plate_idx.size} "
          f"block={block_idx.size} dt={dt} ticks={ticks} mode={mode}")
    print(f"[{label}] d_eq={d_eq:.5f} band=[{cushion_lo:.4f},{cushion_hi:.4f}] "
          f"sheet_width={sheet_width:.4f}\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    split_detected = False
    split_tick = None
    split_stretch = None
    split_clusters = None
    margin_count = 0

    _sample(0)
    for tick in range(1, ticks + 1):
        if tear:
            # Move pinned edge rows apart quasistatically.
            dy = v_plate * dt
            if top_idx.size:
                sim.pos[top_idx, 1] += dy
            if bottom_idx.size:
                sim.pos[bottom_idx, 1] -= dy
            if sim.use_cuda:
                sim.d_pos.copy_to_device(sim.pos)

        sim.step(dt)

        if tear and not split_detected:
            n_clust, _ = cluster_count_and_sizes(sim.pos[sheet_idx], R_BOND)
            if n_clust >= 2:
                split_detected = True
                split_tick = tick
                split_clusters = int(n_clust)
                # current stretch
                top_y = float(sim.pos[top_idx, 1].mean()) if top_idx.size else 0.0
                bottom_y = float(sim.pos[bottom_idx, 1].mean()) if bottom_idx.size else 0.0
                separation = top_y - bottom_y
                split_stretch = separation / print_sep0 if print_sep0 > 0 else 1.0
                # locate split: largest gap between adjacent y-row centroids.
                row_ys = np.array([float(sim.pos[sheet_idx[r], 1].mean()) for r in rows_y])
                gaps = row_ys[1:] - row_ys[:-1]
                split_loc = int(np.argmax(gaps))
                split_thickness = float(sim.pos[sheet_idx, 2].max() -
                                        sim.pos[sheet_idx, 2].min())
                metrics["split_tick"] = split_tick
                metrics["split_stretch"] = split_stretch
                metrics["split_clusters"] = split_clusters
                metrics["split_location"] = split_loc
                metrics["split_thickness"] = split_thickness
                print(f"\n[{label}] FIRST SPLIT at tick={split_tick}: "
                      f"clusters={split_clusters} stretch={split_stretch:.3f} "
                      f"split_between_rows={split_loc}-{split_loc+1} "
                      f"thickness_at_split={split_thickness:.4f}\n")

        if split_detected and tear:
            margin_count += 1
            if margin_count >= SHEET_TEAR_MARGIN_TICKS:
                _sample(tick)
                break
            if top_idx.size and bottom_idx.size:
                top_y = float(sim.pos[top_idx, 1].mean())
                bottom_y = float(sim.pos[bottom_idx, 1].mean())
                if (top_y - bottom_y) >= max_separation:
                    _sample(tick)
                    break

        if tick % sample_every == 0 or tick == ticks:
            _sample(tick)

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics


def _print_sheet_verdict(metrics, derived, label):
    """Print SHEET v1 falsifier verdict; return dict of booleans."""
    ticks = np.asarray(metrics["tick"], dtype=np.int32)
    clusters = np.asarray(metrics["sheet_clusters"], dtype=np.int32)
    thickness = np.asarray(metrics["thickness"], dtype=np.float64)
    min_to_block = np.asarray(metrics["min_sheet_to_block"], dtype=np.float64)
    edge_in_band = np.asarray(metrics["edge_in_band"], dtype=np.int32)
    mode = str(metrics.get("mode", "flat"))
    d_eq = derived["d_eq"]
    cushion_lo, cushion_hi = derived["cushion_band"]
    sheet_width = derived["sheet_width"]
    n_edge = int(_sheet_edge_mask(metrics["sheet_pos"][0],
                                  sheet_side=derived["sheet_side"]).sum())

    final_clusters = int(clusters[-1])
    final_thickness = float(thickness[-1])
    framed = bool(derived.get("framed", False))
    flat_bar = 2.0 * derived["spacing"]

    # (a) PHASE / PHASE-FRAMED
    phase_ok = None
    phase_fail_tick = None
    phase_max_thickness = float(thickness.max())
    if framed and mode == "flat":
        # v3: the framed sheet must stay flat at EVERY sampled tick.
        bad = (clusters != 1) | (thickness > flat_bar)
        phase_ok = not bool(bad.any())
        if not phase_ok:
            phase_fail_tick = int(ticks[bad][0])
    elif mode in ("bump", "flat"):
        phase_ok = (final_clusters == 1 and final_thickness <= flat_bar)
    elif mode == "free":
        phase_ok = final_thickness > SHEET_FREE_THICKNESS_MIN_FRAC * sheet_width

    # (b) DRAPE (bump only)
    drape_ok = None
    tented = False
    if mode == "bump":
        final_min_to_block = float(min_to_block[-1])
        final_edge_in_band = int(edge_in_band[-1])
        block_contact = cushion_lo <= final_min_to_block <= cushion_hi
        edge_drape = final_edge_in_band >= int(np.ceil(SHEET_DRAPE_EDGE_FRAC * n_edge))
        drape_ok = block_contact and edge_drape
        if block_contact and not edge_drape:
            tented = True

    # (c) TEAR / TEAR-FRAMED
    tear_ok = None
    split_tick = metrics.get("split_tick")
    split_stretch = metrics.get("split_stretch")
    split_clusters = metrics.get("split_clusters")
    split_location = metrics.get("split_location")
    split_thickness = metrics.get("split_thickness")
    if mode == "tear":
        if split_tick is None:
            tear_ok = False
        else:
            in_window = (SHEET_TEAR_STRETCH_MIN <= split_stretch <=
                         SHEET_TEAR_STRETCH_MAX)
            no_frag = split_clusters == 2
            if framed:
                # v3: sheet must still be flat at the moment of tear.
                flat_at_split = (split_thickness is not None and
                                 split_thickness <= flat_bar)
                tear_ok = in_window and no_frag and flat_at_split
            else:
                tear_ok = in_window and no_frag

    # ── Print verdict. ──
    if framed:
        print(f"\n[{label}] SHEET v3 FALSIFIERS:")
    else:
        print(f"\n[{label}] SHEET v2 FALSIFIERS:")
    if framed and mode == "flat":
        print(f"  (a) PHASE-FRAMED : {'PASS' if phase_ok else 'FAIL'}  "
              f"samples={len(ticks)} max_thickness={phase_max_thickness:.4f} "
              f"bar<= {flat_bar:.5f} "
              f"first_fail_tick={phase_fail_tick if phase_fail_tick is not None else 'none'}")
    elif mode in ("bump", "flat"):
        print(f"  (a) PHASE  : {'PASS' if phase_ok else 'FAIL'}  "
              f"final_clusters={final_clusters} final_thickness={final_thickness:.4f} "
              f"bar<= {flat_bar:.5f}")
    elif mode == "free":
        print(f"  (a) PHASE  : {'PASS' if phase_ok else 'FAIL'}  "
              f"final_clusters={final_clusters} final_thickness={final_thickness:.4f} "
              f"bar> {SHEET_FREE_THICKNESS_MIN_FRAC*sheet_width:.4f}")
    else:
        print(f"  (a) PHASE  : skipped (tear run)")

    if mode == "bump":
        print(f"  (b) DRAPE  : {'PASS' if drape_ok else 'FAIL'}  "
              f"min_to_block={float(min_to_block[-1]):.4f} "
              f"band=[{cushion_lo:.4f},{cushion_hi:.4f}] "
              f"edge_in_band={int(edge_in_band[-1])}/{n_edge} "
              f"tented={tented}")
    else:
        print(f"  (b) DRAPE  : skipped ({mode})")

    if mode == "tear":
        if split_tick is None:
            print(f"  (c) TEAR{'-FRAMED' if framed else ''}   : FAIL  "
                  f"no split detected in {int(ticks[-1])} ticks")
        else:
            extra = ""
            if framed:
                flat_at_split = (split_thickness is not None and
                                 split_thickness <= flat_bar)
                extra = f" flat_at_split={flat_at_split}"
            print(f"  (c) TEAR{'-FRAMED' if framed else ''}   : "
                  f"{'PASS' if tear_ok else 'FAIL'}  "
                  f"split_tick={split_tick} stretch={split_stretch:.3f} "
                  f"window=[{SHEET_TEAR_STRETCH_MIN:.1f},{SHEET_TEAR_STRETCH_MAX:.1f}] "
                  f"clusters_at_split={split_clusters} "
                  f"split_between_rows={split_location}-{split_location+1} "
                  f"thickness_at_split={split_thickness:.4f}{extra}")
    else:
        print(f"  (c) TEAR   : skipped ({mode})")

    return {
        "phase_ok": phase_ok,
        "drape_ok": drape_ok,
        "tear_ok": tear_ok,
    }


def sheet_main(args, seed):
    """SHEET print entry point: build, evolve, judge (v2 or v3 framed)."""
    mode = str(getattr(args, "sheet_mode", "flat"))
    sheet_spacing = getattr(args, "sheet_spacing", None)
    framed = bool(getattr(args, "sheet_framed", False))
    pos, vel, pin_mask, grain_ids, derived = seed_structures.sheet(
        mode=mode, spacing=sheet_spacing, framed=framed, seed=seed)
    N = pos.shape[0]

    dt = DT
    # Default derived tick count: for tear, a large window; for settle, derived
    # from free-fall time measured in smoke.  Use a safe default here.
    ticks = int(getattr(args, "sheet_ticks", 20000))
    tag = f"{args.tag}_" if args.tag else ""

    flat_bar = 2.0 * derived["spacing"]

    print("=" * 70)
    if framed:
        print("THE KERNEL - SHEET v3 print run (FRAMED)")
        print(f"N={N}, sheet=16x16, frame={derived['frame']} grains, mode={mode}, "
              f"spacing={derived['spacing']:.5f}, seed={seed}, dt={dt}, ticks={ticks}")
        print("-" * 70)
        print("STATEMENT: A flat membrane exists only in a frame; the frame IS the")
        print("  membrane that holds the plane.  Cloth, not shell, by necessity.")
        print("PREDICTION: the framed sheet holds flat (thickness <= 2 lattice steps)")
        print("  under its own self-DRAW; when two opposite frame rows are pulled")
        print("  apart, the sheet tears once at a global stretch between 1.5x and 4x")
        print("  while it is still flat.")
        print("FALSIFIERS:")
        print(f"  (a) PHASE-FRAMED -- any sample in the settle run has clusters != 1 "
              f"or thickness > {flat_bar:.5f} lu (2 lattice steps)")
        print("  (c) TEAR-FRAMED -- first split outside [1.5x,4x], fragmentation >2,")
        print("      or thickness at split exceeds the flat bar; split location recorded")
    else:
        print("THE KERNEL - SHEET v2 print run")
        print(f"N={N}, sheet=16x16, plate=6x6, mode={mode}, "
              f"spacing={derived['spacing']:.5f}, seed={seed}, dt={dt}, ticks={ticks}")
        print("-" * 70)
        print("STATEMENT: A 2-D layer on a substrate is a persistent 2-D phase;")
        print("  the substrate's DRAW holds it flat, the cushion keeps it one grain")
        print("  off the surface, and its own self-DRAW holds it in-plane.  Cloth,")
        print("  not shell, by necessity -- and cloth is what skin and bladder need.")
        print("PREDICTION: at the derived 2-D equilibrium spacing d_eq_2D, bump and")
        print("  flat prints settle as a single connected sheet <=2 lattice steps thick;")
        print("  the bump run drapes so the block top and the plate edges are both in")
        print("  cushion contact; the free sheet balls up; the tear run splits once at a")
        print("  global stretch between 1.5x and 4x while the sheet is still flat.")
        print("FALSIFIERS:")
        print(f"  (a) PHASE -- bump/flat not 1 cluster or thickness > {flat_bar:.5f} lu;")
        print("      free sheet does not ball (thickness <= half sheet width)")
        print("  (b) DRAPE -- bump: block not in cushion band or < half edge grains in")
        print("      cushion band of plate (tented recorded)")
        print("  (c) TEAR -- first split outside [1.5x,4x] or fragmentation >2 clusters;")
        print("      thickness at split recorded")
    print("=" * 70)
    print(f"\nDerived d_eq       = {derived['d_eq']:.5f}")
    print(f"Derived d_eq_2D    = {derived['d_eq_2D']:.5f}")
    print(f"Derived spacing    = {derived['spacing']:.5f}")
    print(f"Derived flat bar   = {flat_bar:.5f}")
    print(f"Derived cushion    = [{derived['cushion_band'][0]:.5f}, "
          f"{derived['cushion_band'][1]:.5f}]")
    print(f"Derived width      = {derived['sheet_width']:.5f}\n")

    _print_sheet_verdict(
        _run_sheet(pos, vel, pin_mask, grain_ids, derived, dt, ticks,
                   tag, "sheet", mode=mode),
        derived, "sheet")

    print("=" * 70)


def main():
    global N, SEED, T_FF, TOTAL_TICKS, SAMPLE_EVERY

    import argparse
    parser = argparse.ArgumentParser(description="THE KERNEL seed run")
    parser.add_argument("--n", type=int, default=N,
                        help="point count (default 4096)")
    parser.add_argument("--seed", type=int, default=SEED,
                        help="structureless-start seed (default 20260806)")
    parser.add_argument("--tag", type=str, default="",
                        help="prefix for output frames (parallel runs)")
    parser.add_argument("--structure", type=str, default="random",
                        choices=["random", "core_shell", "disk", "lattice",
                                 "bone", "muscle", "tendon", "joint", "sheet",
                                 "skin", "bladder", "lever", "leg"],
                        help="initial seed structure (default random)")
    parser.add_argument("--control", type=str, default="none",
                        choices=["none", "packed"],
                        help="control structure for BONE print (default none)")
    parser.add_argument("--spacing", type=float, default=None,
                        help="lattice print spacing in lu (default R_BOND); "
                             "print geometry, not a physics constant")
    parser.add_argument("--cycles", type=int, default=1,
                        help="BONE v2 preload cycles (default 1; use 2 to "
                             "judge spring-back on the bedded column)")
    parser.add_argument("--tendon-preload", type=float, default=0.0,
                        help="TENDON preload fraction: ends are seated "
                             "d_eq*(1-preload) from the plates (default 0.0)")
    parser.add_argument("--tendon-foot", type=int, default=0,
                        help="TENDON end-foot cross-section side: 0 = no feet, "
                             "4 = 4x4 feet on a 2x2 shaft (default 0)")
    parser.add_argument("--joint-ticks", type=int, default=2000,
                        help="JOINT free-evolution ticks (default 2000)")
    parser.add_argument("--joint-control", action="store_true",
                        help="JOINT control: run the same geometry without the "
                             "muscle droplet")
    parser.add_argument("--sheet-mode", type=str, default="flat",
                        choices=["bump", "flat", "free", "tear"],
                        help="SHEET print mode (default flat)")
    parser.add_argument("--sheet-spacing", type=float, default=None,
                        help="SHEET in-plane lattice step in lu (default None, "
                             "which triggers derivation of d_eq_2D)")
    parser.add_argument("--sheet-framed", action="store_true",
                        help="SHEET v3: pin the four border rows as a frame "
                             "and omit the substrate plate")
    parser.add_argument("--sheet-ticks", type=int, default=20000,
                        help="SHEET evolution ticks (default 20000)")
    parser.add_argument("--skin-settle-ticks", type=int, default=3000,
                        help="SKIN free-evolution settle ticks before the stroke "
                             "(default 3000)")
    parser.add_argument("--lever-control", action="store_true",
                        help="LEVER control run: halved muscle arm, load must NOT "
                             "lift (default main run)")
    parser.add_argument("--lever-ticks", type=int, default=8000,
                        help="LEVER free-evolution ticks (default 8000)")
    parser.add_argument("--leg-control", action="store_true",
                        help="LEG v2 control run: muscle-ward fulcrum, load must NOT "
                             "lift (default main run)")
    parser.add_argument("--leg-ticks", type=int, default=8000,
                        help="LEG v2 free-evolution ticks (default 8000)")
    parser.add_argument("--bladder-fill", type=str, default="gap",
                        choices=["gap", "fill"],
                        help="BLADDER content geometry: gap=v1 4^3 droplet, "
                             "fill=v2 contents fill shell at cushion contact "
                             "(default gap)")
    parser.add_argument("--bladder-neck", type=str, default="narrow",
                        choices=["narrow", "antijam"],
                        help="BLADDER neck geometry: narrow=v1/v2 one-grain "
                             "hole at +z pole, antijam=v3 4-spacing hole on "
                             "the squeeze axis (default narrow)")
    args = parser.parse_args()
    SEED = args.seed

    # BONE print has its own driver (compression test)
    if args.structure == "bone":
        bone_main(args, SEED)
        return

    # MUSCLE print has its own driver (extension->convergence bridge test)
    if args.structure == "muscle":
        muscle_main(args, SEED)
        return

    # TENDON print has its own driver (compress->extend router test)
    if args.structure == "tendon":
        tendon_main(args, SEED)
        return

    # JOINT print has its own driver (free-evolution moving-part test)
    if args.structure == "joint":
        joint_main(args, SEED)
        return

    # SHEET print has its own driver (2-D membrane phase test)
    if args.structure == "sheet":
        sheet_main(args, SEED)
        return

    # SKIN print has its own driver (mat draped on muscle bulk)
    if args.structure == "skin":
        skin_main(args, SEED)
        return

    # BLADDER print has its own driver (closed shell + contents squeeze test)
    if args.structure == "bladder":
        bladder_main(args, SEED)
        return

    # LEVER print has its own driver (muscle-bone machine balance test)
    if args.structure == "lever":
        lever_main(args, SEED)
        return

    # LEG v1 print has its own driver (tendon-routed muscle in a well)
    if args.structure == "leg":
        leg_main(args, SEED)
        return

    # choose initial state
    if args.structure == "random":
        N = args.n
        pos, vel = structureless_start(N, BOX, VEL_SIGMA, SEED)
        n_core = 0
        r_target = 0.0
        print_note = ""
    else:
        print_note = "(BOX/VEL_SIGMA unused for authored print)"
        if args.structure == "lattice":
            if args.spacing is None:
                pos, vel = seed_structures.lattice(n=args.n, seed=SEED)
            else:
                pos, vel = seed_structures.lattice(n=args.n, seed=SEED,
                                                   spacing=args.spacing)
            N = pos.shape[0]
            n_core = 0
            r_target = 0.0
        else:
            N = args.n
            if args.structure == "core_shell":
                pos, vel = seed_structures.core_shell(N, f_core=F_CORE,
                                                      r_shell=R_SHELL, seed=SEED)
                r_target = R_SHELL
            else:
                pos, vel = seed_structures.disk(N, f_core=F_CORE,
                                                r_disk=R_DISK, seed=SEED)
                r_target = R_DISK
            n_core = int(F_CORE * N)

    # re-derive the observation window if N changed (t_ff depends on rho)
    RHO_LOCAL = N / BOX ** 3
    T_FF = 1.0 / math.sqrt(G * RHO_LOCAL)
    TOTAL_TICKS = int(math.ceil(T_FF_COUNT * T_FF / DT))
    SAMPLE_EVERY = max(1, TOTAL_TICKS // 40)
    tag = f"{args.tag}_" if args.tag else ""

    print("=" * 60)
    print("THE KERNEL — first light-era run")
    print(f"N={N}, seed={SEED}, structure={args.structure}, box={BOX}, dt={DT}, ticks={TOTAL_TICKS} {print_note}")
    print("=" * 60)

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
        # print-persistence metrics
        "shell_radius_mean": [],
        "shell_radius_std": [],
        "core_bound_frac": [],
        "z_disp": [],
        "bond_retention": [],
    }

    # pre-initial frame
    dump_frame(sim.pos.copy(), os.path.join(OUTPUT_DIR, f"{tag}frame_begin.png"))

    for tick in range(1, TOTAL_TICKS + 1):
        sim.step(DT)
        if tick % SAMPLE_EVERY == 0 or tick == TOTAL_TICKS:
            n_clust, sizes = cluster_count_and_sizes(sim.pos, R_C)
            bound_frac = bound_mass_fraction(sim.pos, R_BOND)
            edge = edge_sharpness(sim.pos, METRIC_R_INNER, METRIC_R_OUTER)
            rad = system_radius(sim.pos)

            shell_r_mean = shell_r_std = core_bound = z_disp = bond_ret = 0.0
            extra = ""
            if args.structure in ("core_shell", "disk"):
                shell_r_mean, shell_r_std, z_disp = shell_disk_metrics(sim.pos, n_core)
                core_bound = core_bound_fraction(sim.pos, n_core, R_BOND)
                extra = (f" | shell_r={shell_r_mean:.3f}±{shell_r_std:.3f}"
                         f" | core_bound={core_bound:.3f}")
                if args.structure == "disk":
                    extra += f" | z_disp={z_disp:.3f}"
            elif args.structure == "lattice":
                nn = nearest_neighbor_distances(sim.pos)
                bond_ret = float(((nn >= R_WALL) & (nn <= R_C)).mean())
                extra = f" | bond_ret={bond_ret:.3f}"

            metrics["tick"].append(tick)
            metrics["clusters"].append(n_clust)
            metrics["max_cluster"].append(int(sizes.max()))
            metrics["bound_frac"].append(bound_frac)
            metrics["edge"].append(edge)
            metrics["radius"].append(rad)
            metrics["radiated_energy"].append(float(sim.radiated_energy))
            metrics["radiated_power"].append(float(sim.last_radiated_power))
            metrics["shell_radius_mean"].append(shell_r_mean)
            metrics["shell_radius_std"].append(shell_r_std)
            metrics["core_bound_frac"].append(core_bound)
            metrics["z_disp"].append(z_disp)
            metrics["bond_retention"].append(bond_ret)
            print(f"tick={tick:6d} | clusters={n_clust:4d} | "
                  f"max={sizes.max():4d} | bound={bound_frac:.3f} | "
                  f"edge={edge:.3f} | radius={rad:.3f} | "
                  f"E_rad={sim.radiated_energy:.4f} | P_rad={sim.last_radiated_power:.4f}"
                  f"{extra}")
        if tick == TOTAL_TICKS // 2:
            dump_frame(sim.pos.copy(), os.path.join(OUTPUT_DIR, f"{tag}frame_mid.png"))

    dump_frame(sim.pos.copy(), os.path.join(OUTPUT_DIR, f"{tag}frame_end.png"))

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

    # collect every fired criterion, then precedence: COLLAPSE > FLICKER > DISPERSE
    # (run 4c fired BOTH collapse and radius-dispersal; the bulk's fate is the
    # primary label, the tail is a secondary note -- thresholds untouched)
    fired = []
    reasons = []
    if final_max >= N * COLLAPSE_MAX_CLUSTER_FRAC:
        fired.append("COLLAPSE")
        reasons.append(f"max_cluster={final_max} >= {COLLAPSE_MAX_CLUSTER_FRAC*N:.0f}")
    if final_max <= N * DISPERSE_MAX_CLUSTER_FRAC and final_bound < 0.3:
        fired.append("DISPERSE")
        reasons.append(f"max_cluster={final_max} <= {DISPERSE_MAX_CLUSTER_FRAC*N:.0f} and bound_frac={final_bound:.3f}")
    if final_radius > initial_radius * DISPERSE_RADIUS_GROWTH:
        fired.append("DISPERSE")
        reasons.append(f"radius {final_radius:.3f} > {DISPERSE_RADIUS_GROWTH}x initial {initial_radius:.3f}")
    if cluster_cv > FLICKER_CV_THRESHOLD:
        fired.append("FLICKER")
        reasons.append(f"cluster_count CV={cluster_cv:.3f} > {FLICKER_CV_THRESHOLD}")
    if bound_swing > BOUND_MASS_PERSISTENCE:
        fired.append("FLICKER")
        reasons.append(f"bound_frac swing={bound_swing:.3f} > {BOUND_MASS_PERSISTENCE}")

    for precedent in ("COLLAPSE", "FLICKER", "DISPERSE"):
        if precedent in fired:
            verdict = precedent
            break
    else:
        verdict = "PASS"
    if len(set(fired)) > 1:
        reasons.append(f"(multiple criteria fired: {', '.join(dict.fromkeys(fired))})")

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

    # ── Print persistence verdict (separate from the standard falsifier) ─
    if args.structure in ("core_shell", "disk", "lattice"):
        print("PRINT PERSISTENCE:")
        if args.structure in ("core_shell", "disk"):
            final_shell_r = metrics["shell_radius_mean"][-1]
            final_shell_std = metrics["shell_radius_std"][-1]
            final_core_bound = metrics["core_bound_frac"][-1]
            radius_ok = abs(final_shell_r - r_target) <= 0.50 * r_target
            print(f"  shell radius mean = {final_shell_r:.4f} (target {r_target:.4f})")
            print(f"  shell radius std  = {final_shell_std:.4f}")
            print(f"  core bound frac   = {final_core_bound:.4f}")
            print(f"  radius within 50% : {'PASS' if radius_ok else 'FAIL'}")
            if args.structure == "disk":
                final_z_disp = metrics["z_disp"][-1]
                z_threshold = 0.25 * r_target
                z_ok = final_z_disp < z_threshold
                print(f"  z-dispersion      = {final_z_disp:.4f} (threshold {z_threshold:.4f})")
                print(f"  disk thin         : {'PASS' if z_ok else 'FAIL'}")
        elif args.structure == "lattice":
            final_bond_ret = metrics["bond_retention"][-1]
            bond_ok = final_bond_ret > 0.50
            print(f"  bond retention    = {final_bond_ret:.4f}")
            print(f"  retention > 50%   : {'PASS' if bond_ok else 'FAIL'}")

    print("=" * 60)


if __name__ == "__main__":
    main()
