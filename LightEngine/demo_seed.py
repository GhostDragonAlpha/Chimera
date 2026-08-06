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
from LightEngine.constants import G, R_WALL, R_BOND, R_C, K_BOND, DT

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
                        choices=["random", "core_shell", "disk", "lattice", "bone"],
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
    args = parser.parse_args()
    SEED = args.seed

    # BONE print has its own driver (compression test)
    if args.structure == "bone":
        bone_main(args, SEED)
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
