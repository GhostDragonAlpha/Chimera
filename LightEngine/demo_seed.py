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

# ── BONE print parameters (derived from force constants) ────────────
# Longitudinal sound speed in the bond lattice: c = sqrt(K_BOND) = 1.0 lu/tick
# because spacing R_BOND and spring constant K_BOND / R_BOND^2 cancel.
# Drive the anchor plates together at 5% of sound speed.
BONE_V_PLATE = 0.05 * math.sqrt(K_BOND)          # lu / tick
BONE_COMPRESS_DIST = 2.0 * R_BOND                # total plate closure, lu
BONE_HOLD_FRAC = 0.25                            # hold phase / compression phase
# BONE falsifier thresholds (named before the run; do not retune)
BONE_MERGE_PAIR_GROWTH = 2.0                     # merged grain pairs > 2x initial
BONE_PLASTIC_FRAC = 0.10                         # permanent length change > 10%
BONE_RUPTURE_FRAC = 0.10                         # > 10% of initial bonds ruptured
BONE_STIFFNESS_GAIN = 2.0                        # bone stiffer than packed bed by 2x


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


# ── BONE-specific helpers ───────────────────────────────────────────

def _rod_bounding_box(pos: np.ndarray, grain_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Axis-aligned bounding box of the rod points (grain_ids >= 0)."""
    rod = pos[grain_ids >= 0]
    return rod.min(axis=0), rod.max(axis=0)


def _make_packed_control(pos: np.ndarray, vel: np.ndarray, grain_ids: np.ndarray,
                         seed: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Return a packed-bed control: keep the two pinned plates, replace the rod
    with a uniform random fill of the same bounding box and point count.
    """
    pos = pos.copy()
    vel = vel.copy()
    rod_mask = grain_ids >= 0
    n_rod = int(rod_mask.sum())
    bbox_min, bbox_max = _rod_bounding_box(pos, grain_ids)
    rng = np.random.default_rng(seed)
    pos[rod_mask] = rng.uniform(bbox_min, bbox_max, (n_rod, 3)).astype(np.float32)
    return pos, vel


def _initial_bond_pairs(pos: np.ndarray, r_bond: float = R_BOND) -> np.ndarray:
    """Return unordered point pairs within r_bond in the given state."""
    rb2 = r_bond * r_bond
    pairs = []
    for lo, hi, r2 in _pairwise_r2(pos):
        ii, jj = np.nonzero(r2 <= rb2)
        ii = ii + lo
        keep = ii < jj
        pairs.extend(zip(ii[keep].tolist(), jj[keep].tolist()))
    if not pairs:
        return np.empty((0, 2), dtype=np.int64)
    return np.array(pairs, dtype=np.int64)


def _ruptured_count(pairs: np.ndarray, pos: np.ndarray, r_c: float = R_C) -> int:
    """How many of the initial pairs now exceed the resistance cutoff r_c."""
    if pairs.size == 0:
        return 0
    d2 = np.sum((pos[pairs[:, 0]] - pos[pairs[:, 1]]) ** 2, axis=1)
    return int(np.count_nonzero(d2 > r_c * r_c))


def _grain_metrics(pos: np.ndarray, grain_ids: np.ndarray,
                   r_bond: float = R_BOND) -> tuple[int, int]:
    """Return (number of distinct grain ids, number of merged grain pairs)."""
    unique = np.unique(grain_ids[grain_ids >= 0])
    n_grains = int(unique.shape[0])
    rb2 = r_bond * r_bond
    merged = set()
    g = grain_ids
    for lo, hi, r2 in _pairwise_r2(pos):
        ii, jj = np.nonzero(r2 <= rb2)
        ii = ii + lo
        keep = ii < jj
        for a, b in zip(ii[keep], jj[keep]):
            ga, gb = int(g[a]), int(g[b])
            if ga >= 0 and gb >= 0 and ga != gb:
                if ga > gb:
                    ga, gb = gb, ga
                merged.add((ga, gb))
    return n_grains, len(merged)


def _rod_shape(pos: np.ndarray, grain_ids: np.ndarray) -> tuple[float, float]:
    """Return (rod length along x, maximum transverse deflection)."""
    rod = pos[grain_ids >= 0]
    length = float(rod[:, 0].max() - rod[:, 0].min())
    deflection = float(np.sqrt(rod[:, 1] ** 2 + rod[:, 2] ** 2).max())
    return length, deflection


def _plate_force(acc: np.ndarray, left_idx: np.ndarray,
                 right_idx: np.ndarray) -> float:
    """Mean magnitude of the x-reaction force on the two anchor plates."""
    left = float(np.abs(acc[left_idx, 0].sum()))
    right = float(np.abs(acc[right_idx, 0].sum()))
    return 0.5 * (left + right)


def _stiffness(displacement: list[float], force: list[float]) -> float:
    """Linear slope dF/dx for the compression phase (magnitude)."""
    if len(displacement) < 2:
        return 0.0
    x = np.array(displacement, dtype=np.float64)
    y = np.array(force, dtype=np.float64)
    mask = x >= 0
    if mask.sum() < 2:
        return 0.0
    x = x[mask]
    y = y[mask]
    slope, _ = np.polyfit(x, y, 1)
    return float(abs(slope))


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


def _run_bone_compression(pos, vel, pin_mask, grain_ids, n_plate, initial_pairs,
                          initial_rod_length, initial_grain_count,
                          compress_ticks, hold_ticks, retract_ticks,
                          v_plate, dt, tag, label):
    """Run compress-hold-retract on one BOME (or packed control) configuration."""
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

    total_ticks = compress_ticks + hold_ticks + retract_ticks
    sample_every = max(1, total_ticks // 40)

    metrics = {
        "tick": [],
        "clusters": [],
        "max_cluster": [],
        "bound_frac": [],
        "edge": [],
        "radius": [],
        "radiated_energy": [],
        "radiated_power": [],
        "grain_count": [],
        "merged_pairs": [],
        "rod_length": [],
        "deflection": [],
        "ruptured_bonds": [],
        "plate_force": [],
        "closure": [],
    }

    print(f"\n[{label}] N={N} grains={initial_grain_count} "
          f"rod_length={initial_rod_length:.4f}")
    print(f"[{label}] compression={compress_ticks} hold={hold_ticks} "
          f"retract={retract_ticks} ticks")
    print(f"[{label}] v_plate={v_plate:.5f} lu/tick, "
          f"closure={BONE_COMPRESS_DIST:.4f} lu\n")

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_begin.png"))

    for tick in range(1, total_ticks + 1):
        if tick <= compress_ticks:
            dx = v_plate * dt
        elif tick <= compress_ticks + hold_ticks:
            dx = 0.0
        else:
            dx = -v_plate * dt

        if dx != 0.0:
            sim.pos[left_idx, 0] += dx
            sim.pos[right_idx, 0] -= dx
            if sim.use_cuda:
                sim.d_pos.copy_to_device(sim.pos)

        sim.step(dt)

        if tick % sample_every == 0 or tick == total_ticks:
            n_clust, sizes = cluster_count_and_sizes(sim.pos, R_C)
            bound_frac = bound_mass_fraction(sim.pos, R_BOND)
            edge = edge_sharpness(sim.pos, METRIC_R_INNER, METRIC_R_OUTER)
            rad = system_radius(sim.pos)
            n_grains, merged_pairs = _grain_metrics(sim.pos, grain_ids)
            rod_length, deflection = _rod_shape(sim.pos, grain_ids)
            ruptured = _ruptured_count(initial_pairs, sim.pos)
            plate_force = _plate_force(sim.acc, left_idx, right_idx)
            left_x = float(sim.pos[left_idx, 0].mean())
            right_x = float(sim.pos[right_idx, 0].mean())
            closure = initial_sep - (right_x - left_x)

            metrics["tick"].append(tick)
            metrics["clusters"].append(n_clust)
            metrics["max_cluster"].append(int(sizes.max()))
            metrics["bound_frac"].append(bound_frac)
            metrics["edge"].append(edge)
            metrics["radius"].append(rad)
            metrics["radiated_energy"].append(float(sim.radiated_energy))
            metrics["radiated_power"].append(float(sim.last_radiated_power))
            metrics["grain_count"].append(n_grains)
            metrics["merged_pairs"].append(merged_pairs)
            metrics["rod_length"].append(rod_length)
            metrics["deflection"].append(deflection)
            metrics["ruptured_bonds"].append(ruptured)
            metrics["plate_force"].append(plate_force)
            metrics["closure"].append(closure)

            print(f"[{label}] tick={tick:6d} | clusters={n_clust:4d} | "
                  f"max={sizes.max():4d} | bound={bound_frac:.3f} | "
                  f"grains={n_grains} | merged={merged_pairs} | "
                  f"length={rod_length:.4f} | deflect={deflection:.4f} | "
                  f"ruptured={ruptured} | force={plate_force:.3f} | "
                  f"closure={closure:.4f}")

        if tick == compress_ticks:
            dump_frame(sim.pos.copy(),
                       os.path.join(OUTPUT_DIR, f"{tag}{label}_mid.png"))

    dump_frame(sim.pos.copy(),
               os.path.join(OUTPUT_DIR, f"{tag}{label}_end.png"))
    return metrics


def _print_bone_verdict(metrics, initial_grain_count, initial_rod_length,
                        initial_bond_count, label):
    """Print BONE falsifier verdict for one run; return (stiffness, verdict)."""
    if not metrics["tick"]:
        return 0.0, "N/A", [], []

    final_merged = metrics["merged_pairs"][-1]
    initial_merged = max(1, initial_grain_count - 1)
    merge_ratio = final_merged / initial_merged
    final_length = metrics["rod_length"][-1]
    plastic = abs(final_length - initial_rod_length) / max(1e-9, initial_rod_length)
    ruptured = max(metrics["ruptured_bonds"])
    rupture_frac = ruptured / max(1, initial_bond_count)

    closure = np.array(metrics["closure"], dtype=np.float64)
    force = np.array(metrics["plate_force"], dtype=np.float64)
    max_idx = int(np.argmax(closure))
    if max_idx >= 2:
        stiff = _stiffness(closure[:max_idx + 1].tolist(),
                           force[:max_idx + 1].tolist())
    else:
        stiff = 0.0

    fired = []
    reasons = []
    if merge_ratio >= BONE_MERGE_PAIR_GROWTH:
        fired.append("MERGE")
        reasons.append(
            f"merged_pairs {final_merged}/{initial_merged} = ratio {merge_ratio:.2f}")
    if plastic > BONE_PLASTIC_FRAC:
        fired.append("PLASTIC")
        reasons.append(f"length change {plastic:.3f}")
    if rupture_frac > BONE_RUPTURE_FRAC:
        fired.append("RUPTURE")
        reasons.append(
            f"ruptured bonds {ruptured}/{initial_bond_count} = {rupture_frac:.3f}")

    verdict = fired[0] if fired else "PASS"

    print(f"\n[{label}] BONE FALSIFIER VERDICT: {verdict}")
    print(f"  grain count initial/final  = {initial_grain_count}/"
          f"{metrics['grain_count'][-1]}")
    print(f"  merged pairs ratio         = {merge_ratio:.3f}")
    print(f"  rod length initial/final   = {initial_rod_length:.4f}/"
          f"{final_length:.4f}")
    print(f"  plastic strain             = {plastic:.4f}")
    print(f"  ruptured bonds             = {ruptured}/{initial_bond_count}")
    print(f"  compression stiffness      = {stiff:.3f}")
    if reasons:
        print("  reasons:")
        for r in reasons:
            print(f"    - {r}")
    else:
        print("  reasons: none — prediction held")
    return stiff, verdict, fired, reasons


def bone_main(args, seed):
    """BONE print entry point: build, optionally run packed control, verdict."""
    pos, vel, pin_mask, grain_ids = seed_structures.bone(
        n=args.n, grain_side=6, seed=seed)
    N = pos.shape[0]
    n_plate = int(np.count_nonzero(grain_ids == -1) // 2)
    initial_grain_count = len(np.unique(grain_ids[grain_ids >= 0]))

    initial_pairs = _initial_bond_pairs(pos, R_BOND)
    initial_rod_length, _ = _rod_shape(pos, grain_ids)
    initial_bond_count = initial_pairs.shape[0]

    dt = DT
    v_plate = BONE_V_PLATE
    compress_ticks = int(math.ceil(BONE_COMPRESS_DIST / (2.0 * v_plate * dt)))
    hold_ticks = max(1, int(round(compress_ticks * BONE_HOLD_FRAC)))
    retract_ticks = compress_ticks

    tag = f"{args.tag}_" if args.tag else ""

    print("=" * 60)
    print("THE KERNEL — BONE print run")
    print(f"N={N}, seed={seed}, structure={args.structure}, "
          f"control={args.control}, dt={dt}")
    print("=" * 60)

    bone_metrics = _run_bone_compression(
        pos, vel, pin_mask, grain_ids, n_plate, initial_pairs,
        initial_rod_length, initial_grain_count,
        compress_ticks, hold_ticks, retract_ticks,
        v_plate, dt, tag, "bone")

    packed_metrics = None
    if args.control == "packed":
        pos_p, vel_p = _make_packed_control(pos, vel, grain_ids, seed=seed + 999)
        initial_pairs_p = _initial_bond_pairs(pos_p, R_BOND)
        initial_rod_length_p, _ = _rod_shape(pos_p, grain_ids)
        packed_metrics = _run_bone_compression(
            pos_p, vel_p, pin_mask, grain_ids, n_plate, initial_pairs_p,
            initial_rod_length_p, initial_grain_count,
            compress_ticks, hold_ticks, retract_ticks,
            v_plate, dt, tag, "packed")

    print("=" * 60)
    bone_stiff, bone_verdict, _, _ = _print_bone_verdict(
        bone_metrics, initial_grain_count, initial_rod_length,
        initial_bond_count, "bone")

    if packed_metrics is not None:
        packed_stiff, packed_verdict, _, _ = _print_bone_verdict(
            packed_metrics, initial_grain_count, initial_rod_length_p,
            initial_pairs_p.shape[0], "packed")
        # slope-based gain (positive now); guard against sign issues with abs
        gain = abs(bone_stiff) / max(1e-12, abs(packed_stiff))

        # deflection-per-unit-load comparison (matches THE_CATEGORIES.md wording)
        bone_force = max(bone_metrics["plate_force"])
        bone_deflect = max(bone_metrics["deflection"])
        packed_force = max(packed_metrics["plate_force"])
        packed_deflect = max(packed_metrics["deflection"])
        bone_dpl = bone_deflect / max(1e-12, bone_force)
        packed_dpl = packed_deflect / max(1e-12, packed_force)
        dpl_ratio = packed_dpl / max(1e-12, bone_dpl)
        stiffness_ok = dpl_ratio >= BONE_STIFFNESS_GAIN

        print("\nSTIFFNESS COMPARISON:")
        print(f"  bone dF/dx        = {bone_stiff:.3f}")
        print(f"  packed dF/dx      = {packed_stiff:.3f}")
        print(f"  slope gain        = {gain:.3f}")
        print(f"  bone max force    = {bone_force:.3f}")
        print(f"  bone max deflect  = {bone_deflect:.4f}")
        print(f"  packed max force  = {packed_force:.3f}")
        print(f"  packed max deflect= {packed_deflect:.4f}")
        print(f"  deflection/load ratio (packed/bone) = {dpl_ratio:.3f} "
              f"(threshold {BONE_STIFFNESS_GAIN:.1f})")
        print(f"  ordered > random  : {'PASS' if stiffness_ok else 'FAIL'}")
        if not stiffness_ok:
            print("  [bone] verdict updated: STIFFNESS (gain below threshold)")
            bone_verdict = "STIFFNESS"
    else:
        print("\nSTIFFNESS COMPARISON: skipped (no --control packed)")

    print(f"\nFINAL BONE VERDICT: {bone_verdict}")
    print("=" * 60)


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
