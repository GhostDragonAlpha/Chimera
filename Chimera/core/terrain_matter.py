"""core/terrain_matter.py — Substrate rung C: terrain-as-matter, the shovel test
(headless). tb-0169.

READ FIRST: docs/THE_COMPOSITIONAL_WORLD_MODEL.md PART II SS13 (the scale ladder —
grain scale where the shovel digs, bulk scale where the dune sleeps, and "the
switch" = coalesce/fracture) + SS15 rung C: *"a bounded ground patch of atoms,
coalesced at rest, a scripted dig fractures it locally, grain physics on the freed
particles, splats follow. KILL IF fracture seams cannot be stitched, or the grain
budget breaks the frame — then landscaping is NOT abandoned and the finding is
recorded."* + docs/THE_MATTER_MODEL.md SS6 (coalesce/fracture: hysteresis so it does
not thrash, merging FORGETS per-cell state, the seam between merged and live
regions must be stitched).

THE EXPERIMENT, literally
--------------------------
An N x N grid of "atoms" (bulk sand parcels) starts COALESCED: one static
aggregate, O(1) to represent (a heightfield + one appearance sample), no per-atom
physics. A scripted dig event — replicating GA_Dig's OWN cell-delta shape verbatim
(CHIMERA_VISION.py; grep DIG / SURFACE_TABLE — cited as literal constants below,
NOT imported: CHIMERA_VISION.py is the seed's pseudocode spec, ast-parsed by
core/helm.py and never executed as a module, and no other core/*.py file imports
it either — matter_items.py/splat_emit.py cite the seed the same literal way) —
FRACTURES a local region INSTANTLY: those atoms become free rigid bodies (MuJoCo,
CPU, a SINGLE world — this is not the trainer's population-batch use case, so
mujoco-warp buys nothing here; plain `mujoco` is the honest, correct tool for one
dig event). They fall, collide, and settle under gravity + Coulomb friction sourced
from the sand entry of docs/matter/matter_library.json. Once ALL freed grains have
been below a velocity threshold for a HELD duration (hysteresis: instant fracture,
slow merge — SS6's own words), they RE-COALESCE: their individual final positions
are resampled into the coarse heightfield — this is where SS6's "merging forgets
per-cell state" is actually paid: multiple grains landing in one cell get SUMMED
into that cell's column, and any grain that exits the patch is a real, measured
mass loss, not silently kept. TWO dig cycles run (the second overlapping the
first's already-recoalesced ground) to prove the SAME mechanism works more than
once, on a mix of virgin and repaired sand — a harder, more honest test than one
shot.

RENDERING reuses core.matter_items + core.splat_emit UNCHANGED (imported, never
copied) for a before/during/after strip using sand's own optical DISTRIBUTION
(variance ON, per matter_library's "appearance is a distribution, never a
surface").

HONEST SCOPE — named gaps, not silently dropped
-------------------------------------------------
1. GRAIN SIZE. The library's sand grain_size_mm (median ~0.07mm, real regolith) is
   NOT individually simulated: a 2m^2 patch at 70 microns is O(10^8) particles.
   The simulated "atom"/"grain" here is a coarse DEM macro-particle (order
   ATOM_PITCH, ~0.17m) standing in for a bundled clump of real grains — a
   TRACTABILITY choice (design provenance below), orthogonal to the library's own
   physical numbers (density/friction), which are used UNSCALED.
2. COHESION. matter_library's sand cohesion_kpa (0.5 +/- 0.4) is NOT modelled.
   MuJoCo's stock contact model is frictional (Coulomb) only; true cohesive DEM
   bonding needs custom per-pair springs/constraints — impractical at this grain
   count for a first-pass shovel test. Named gap for a later rung.
3. PATCH SIZE. The packet asks for "~2m x 2m." GA_Dig's OWN footprint (radius
   0.6m, cell 0.5m -> a (2*halfwidth+1)=5-cell-wide square = 2.5m, using the
   seed's exact `cells = int(radius/cell)+1` formula) is already wider than 2m on
   its own — a literal 2m x 2m patch could never show a fractured sub-region next
   to a QUIET coalesced remainder; the whole patch would be dug in one scoop, and
   "fractures it LOCALLY" would be untestable by construction. Sized larger here
   (see PATCH_CELLS) so locality is a checkable claim, not a tautology — the
   deviation is stated here, not silent.
4. No fbm dune/ridge shaping (AGroundActor.HeightAt's other terms) — the patch
   starts FLAT. This isolates the one variable under test (coalesce / fracture /
   grain-physics), the same experimental discipline splat_emit.py used to isolate
   splats-vs-mesh from lighting-model differences.

FACTS ONLY below the CLI: every function reports numbers. Whether those numbers
mean KILL or SURVIVES is decided once, in main(), against the two criteria SS15
actually states (seam stitching, frame wall) — see the "verdict" block.

Run: python -m core.terrain_matter
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

import mujoco

from core.malcolm import load_envelope
from core.matter_items import (frame_of, load_library, register_material,
                               sample_variance)
from core.matter_items import rasterize as _rasterize_lib
from core.splat_emit import emit_splats, hstack_strip

ROOT = Path(__file__).resolve().parents[1]              # E:\PythonChimera\Chimera
OUT_DIR = ROOT / "Saved" / "TerrainMatter"

SEED = 11

# --- CITED, verbatim from CHIMERA_VISION.py (pseudocode seed; not imported — see
# module docstring) -------------------------------------------------------------
# DIG = dict(radius=0.6, scoop_depth=0.15, durability_per_scoop=1.0, cell=0.5)
DIG_RADIUS = 0.6
DIG_CELL = 0.5
DIG_SCOOP_DEPTH = 0.15
# GA_Dig.ActivateAbility: `cells = int(DIG["radius"] / DIG["cell"]) + 1` — verbatim
DIG_CELL_HALFWIDTH = int(DIG_RADIUS / DIG_CELL) + 1                # = 2 -> 5x5 dig-cells
# SURFACE_TABLE["SAND"] = (traction=0.75, makes_print=True, dust_scale=1.00, "SAND")
SAND_TRACTION = 0.75


def _sand_physical() -> dict:
    """docs/matter/matter_library.json materials.sand.physical — cited, not invented."""
    return load_library()["materials"]["sand"]["physical"]


# --- the bounded patch (see honest-scope gap #3 above for why this isn't ~2m) ---
PATCH_CELLS = 8                                    # dig-cells (0.5m) per side
PATCH_SIZE_M = PATCH_CELLS * DIG_CELL               # 4.0 m
SUB = 3                                             # fine-atom subdivisions / dig-cell edge
ATOM_PITCH = DIG_CELL / SUB                         # ~0.1667 m
N_SIDE = PATCH_CELLS * SUB                          # 24 atoms/side -> 576 total
H0 = 0.4                                             # baseline bulk height (design; the
                                                      # seed's dig_delta has no absolute
                                                      # origin either, it's a pure offset)
GRAIN_RADIUS = 0.4 * ATOM_PITCH                     # ~0.067 m simulated macro-particle

DT = 0.005
MAX_SETTLE_STEPS = 2000                             # TOTAL: a hard cap, never unbounded
QUIET_HOLD_STEPS = 60                               # ~0.3s held quiet before merge allowed
VEL_QUIET_THRESHOLD = 0.05                          # m/s

DIG_CENTERS = [(2, 2), (4, 4)]                      # cycle 2 overlaps cycle 1 (see docstring)


# --- geometry: atom grid <-> world <-> GA_Dig's own cell grid -------------------

def cell_of(x: float, y: float) -> tuple:
    return (math.floor(x / DIG_CELL), math.floor(y / DIG_CELL))


def atom_xy(i: int, j: int) -> tuple:
    return (i + 0.5) * ATOM_PITCH, (j + 0.5) * ATOM_PITCH


def dig_footprint_cells(center_cell: tuple) -> list:
    """GA_Dig's OWN shape, replicated verbatim: the square of dig-cells within
    DIG_CELL_HALFWIDTH of center_cell (CHIMERA_VISION.py's k0+dx,dy loop)."""
    k0x, k0y = center_cell
    return [(k0x + dx, k0y + dy)
            for dx in range(-DIG_CELL_HALFWIDTH, DIG_CELL_HALFWIDTH + 1)
            for dy in range(-DIG_CELL_HALFWIDTH, DIG_CELL_HALFWIDTH + 1)]


def freed_mask_for(center_cell: tuple) -> np.ndarray:
    footprint = set(dig_footprint_cells(center_cell))
    mask = np.zeros((N_SIDE, N_SIDE), dtype=bool)
    for i in range(N_SIDE):
        for j in range(N_SIDE):
            x, y = atom_xy(i, j)
            if cell_of(x, y) in footprint:
                mask[i, j] = True
    return mask


# --- grain-scale physics: MuJoCo, ONE bounded world, freed particles only ------

def _friction_str(mu: float) -> str:
    """sliding/torsional/rolling, all keyed off the library's sliding coefficient
    mu = tan(friction_angle).

    FIRST ATTEMPT (found wrong by running it, not by inspection): reused
    core/mjcf.py's ratio (torsional=mu/120, rolling=mu/1200) verbatim. That ratio
    was tuned for CAPSULE creature limbs, which have inherent geometric resistance
    to rolling from their length; applied to free SPHERES it reproduces the
    textbook DEM pitfall of "ideal spheres roll forever" — measured live: 22-25%
    of freed grains rolled clean off a 4m patch in the 10s settle budget, and
    settled_within_budget was FALSE for both cycles. Real sand grains are
    irregular, not smooth spheres, and stop; a smooth-sphere idealization must
    compensate with explicit rolling resistance or it is measuring the shape
    idealization, not the sand. Standard DEM-with-spheres practice (Zhou et al.
    and similar granular-mechanics literature) is rolling/torsional resistance
    comparable to, not three orders of magnitude below, the sliding coefficient —
    used here at mu*0.4 / mu*0.2, re-verified by re-running (see module history)."""
    return f"{mu:.6f} {mu * 0.2:.6f} {mu * 0.4:.6f}"


def _grain_xml(spawns: list, density: float, mu: float, floor_half: float) -> str:
    """N free spheres (freejoint each) + one floor plane. No hinges, no self-
    collision exemptions — UNLIKE core/mjcf.py's creature bodies, grains MUST
    collide with each other (that is granular contact physics), so MuJoCo's
    default contype=1/conaffinity=1 (collides with everything) is exactly right
    and nothing is overridden."""
    fr = _friction_str(mu)
    bodies = "".join(
        f'    <body name="g{k}" pos="{x:.6f} {y:.6f} {z:.6f}">\n'
        f'      <freejoint/>\n'
        f'      <geom type="sphere" size="{r:.6f}" density="{density:.3f}" '
        f'friction="{fr}" rgba="0.55 0.47 0.38 1"/>\n'
        f'    </body>\n'
        for k, (x, y, z, r) in enumerate(spawns))
    return f"""<mujoco model="grains">
  <option timestep="{DT:.8f}" gravity="0 0 -9.81" integrator="implicitfast" cone="pyramidal"/>
  <worldbody>
    <geom name="floor" type="plane" size="{floor_half:.4f} {floor_half:.4f} 0.1" friction="{fr}"/>
{bodies}  </worldbody>
</mujoco>
"""


def _grain_positions(data, k: int) -> np.ndarray:
    """World positions of grains 1..k (body 0 = world), in creation order."""
    return np.array(data.xpos[1:1 + k])


def run_dig_cycle(heights: np.ndarray, live: np.ndarray, center_cell: tuple,
                  density: float, mu: float, rng: np.random.Generator) -> dict:
    """One fracture -> grain-physics -> hysteresis -> recoalesce cycle. Returns
    FACTS (timing, positions, settle state) for the caller to measure/render/
    recoalesce with — this function does not judge, only reports."""
    mask = freed_mask_for(center_cell)
    freed_idx = np.argwhere(mask)
    k_freed = len(freed_idx)
    live[mask] = True

    spawns = [(*atom_xy(i, j), heights[i, j], GRAIN_RADIUS) for i, j in freed_idx]
    xml = _grain_xml(spawns, density, mu, PATCH_SIZE_M + 2.0)
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)

    # the toss: a small fling standing in for the seed's NS_DigBurst VFX (an
    # explicit, motivated EXTENSION — the seed never gives that burst real grain
    # physics; this experiment is testing whether it should).
    for k in range(k_freed):
        vx, vy = rng.uniform(-0.35, 0.35, size=2)
        vz = rng.uniform(0.3, 0.8)
        data.qvel[6 * k: 6 * k + 3] = [vx, vy, vz]

    mid_positions = None
    quiet_hold = 0
    step_times = []
    settled_at = None
    for step in range(MAX_SETTLE_STEPS):                # TOTAL: hard cap, never unbounded
        t0 = time.perf_counter()
        mujoco.mj_step(model, data)
        step_times.append(time.perf_counter() - t0)

        if step == 40:                                   # fixed early snapshot: "during"
            mid_positions = _grain_positions(data, k_freed).copy()

        speeds = np.linalg.norm(data.qvel.reshape(-1, 6)[:, :3], axis=1)
        if float(speeds.max()) < VEL_QUIET_THRESHOLD:
            quiet_hold += 1
        else:
            quiet_hold = 0
        if quiet_hold >= QUIET_HOLD_STEPS:
            settled_at = step + 1
            break

    final_positions = _grain_positions(data, k_freed)
    if mid_positions is None:                            # settled before step 40 (shouldn't
        mid_positions = final_positions.copy()            # happen given QUIET_HOLD_STEPS=60)

    return {
        "mask": mask, "freed_idx": freed_idx, "k_freed": k_freed,
        "mid_positions": mid_positions, "final_positions": final_positions,
        "settled_at": settled_at, "step_times": step_times,
    }


def recoalesce(heights: np.ndarray, live: np.ndarray, freed_idx: np.ndarray,
              final_pos: np.ndarray, grain_mass: float, density: float) -> int:
    """Fold settled grains back into the coarse heightfield. LOSSY BY DESIGN
    (THE_MATTER_MODEL.md SS6: merging FORGETS per-cell state) — grains landing in
    the same cell get SUMMED (their masses add, raising that cell's column); a
    freed cell that ends up with none settles to bedrock (0). Grains that leave
    the patch are a REAL, measured mass loss, returned as n_exited — never
    silently absorbed."""
    mass_col = np.zeros((N_SIDE, N_SIDE), dtype=np.float64)
    n_exited = 0
    for x, y, z in final_pos:
        i = int(math.floor(x / ATOM_PITCH))
        j = int(math.floor(y / ATOM_PITCH))
        if 0 <= i < N_SIDE and 0 <= j < N_SIDE and z > -0.5:
            mass_col[i, j] += grain_mass
        else:
            n_exited += 1
    area = ATOM_PITCH ** 2
    for i, j in freed_idx:
        heights[i, j] = mass_col[i, j] / (area * density)
        live[i, j] = False
    return n_exited


def seam_integrity(heights: np.ndarray, freed_mask: np.ndarray) -> dict:
    """Height discontinuity at every (just-recoalesced, never-touched-this-cycle)
    4-neighbour boundary pair. A big number is a visible crack/cliff; the doc
    calls this "the seam" and warns it must be stitched, not assumed."""
    diffs = []
    for i in range(N_SIDE):
        for j in range(N_SIDE):
            if not freed_mask[i, j]:
                continue
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < N_SIDE and 0 <= nj < N_SIDE and not freed_mask[ni, nj]:
                    diffs.append(abs(float(heights[i, j] - heights[ni, nj])))
    if not diffs:
        return {"n_boundary_pairs": 0, "max_discontinuity_m": 0.0, "mean_discontinuity_m": 0.0}
    return {"n_boundary_pairs": len(diffs),
            "max_discontinuity_m": float(np.max(diffs)),
            "mean_discontinuity_m": float(np.mean(diffs))}


def mass_ledger(freed_mask: np.ndarray, grain_mass: float, n_exited: int,
                heights_after: np.ndarray, density: float) -> dict:
    """FACTS about where the mass went: physical loss (grains that left the
    patch) reported SEPARATELY from resample error (the lossy heightfield
    compression itself) — exactly the distinction SS6 asks for."""
    n_total = N_SIDE * N_SIDE
    n_freed = int(np.sum(freed_mask))
    area = ATOM_PITCH ** 2

    mass_before_total = n_total * grain_mass
    mass_freed_start = n_freed * grain_mass
    mass_exited = n_exited * grain_mass
    mass_freed_end_physical = mass_freed_start - mass_exited

    freed_idx = np.argwhere(freed_mask)
    mass_resampled = float(sum(heights_after[i, j] * area * density for i, j in freed_idx))
    resample_error = mass_resampled - mass_freed_end_physical

    mass_untouched = (n_total - n_freed) * grain_mass
    mass_after_total = mass_untouched + mass_resampled
    overall_drift = (mass_after_total - (mass_before_total - mass_exited)) / mass_before_total

    return {
        "n_total_atoms": n_total, "n_freed": n_freed, "n_exited": int(n_exited),
        "mass_before_total_kg": mass_before_total,
        "mass_exited_kg": mass_exited,
        "mass_resampled_kg": mass_resampled,
        "resample_error_kg": resample_error,
        "overall_drift_fraction": overall_drift,
    }


# --- rendering: heightfield/grains -> voxels -> splat_emit/matter_items --------

def _heightfield_voxels(heights: np.ndarray, live_mask: np.ndarray, z_res: int,
                        supersample: int) -> np.ndarray:
    """Coalesced bulk -> a solid voxel block (X,Y,Z order, matching
    core.matter_items._coords' own convention). Cells in `live_mask` (currently
    freed/airborne) are EXCLUDED — that is the visible pit while grains fly."""
    n = N_SIDE * supersample
    vp = ATOM_PITCH / supersample
    grid = np.zeros((n, n, z_res), dtype=bool)
    for i in range(N_SIDE):
        for j in range(N_SIDE):
            if live_mask[i, j]:
                continue
            h_vox = max(0, min(int(round(heights[i, j] / vp)), z_res))
            if h_vox <= 0:
                continue
            grid[i * supersample:(i + 1) * supersample,
                 j * supersample:(j + 1) * supersample, 0:h_vox] = True
    return grid


def _grain_voxels(grid_shape: tuple, positions: np.ndarray, radius: float,
                  supersample: int) -> np.ndarray:
    n, _, z_res = grid_shape
    vp = ATOM_PITCH / supersample
    out = np.zeros(grid_shape, dtype=bool)
    r_vox = max(1, int(round(radius / vp)))
    for x, y, z in positions:
        cx, cy, cz = int(round(x / vp)), int(round(y / vp)), int(round(z / vp))
        for dx in range(-r_vox, r_vox + 1):
            for dy in range(-r_vox, r_vox + 1):
                for dz in range(-r_vox, r_vox + 1):
                    if dx * dx + dy * dy + dz * dz > r_vox * r_vox:
                        continue
                    xx, yy, zz = cx + dx, cy + dy, cz + dz
                    if 0 <= xx < n and 0 <= yy < n and 0 <= zz < z_res:
                        out[xx, yy, zz] = True
    return out


def render_snapshot(heights: np.ndarray, live_mask: np.ndarray, grain_positions,
                    ext: dict, rng: np.random.Generator, label: str,
                    supersample: int = 2, z_res: int = 22):
    """One splat-rasterized view of the patch's current state. REUSES
    core.splat_emit.emit_splats + core.matter_items' sample_variance/rasterize/
    frame_of verbatim (imported, not copied) with sand's library optics
    (variance ON, per the task)."""
    grid = _heightfield_voxels(heights, live_mask, z_res, supersample)
    if grain_positions is not None and len(grain_positions):
        grid = grid | _grain_voxels(grid.shape, grain_positions, GRAIN_RADIUS, supersample)
    splats = emit_splats(grid, "sand", sigma=0.9)
    if splats is None:
        raise RuntimeError(f"{label}: no surface voxels produced")
    splats = sample_variance(splats, ext, rng)
    center, radius = frame_of(splats)
    img = _rasterize_lib(splats, center, radius, -50.0, 30.0, 120.0, 45.0, w=360, h=360)
    return img, int(len(splats["pos"]))


# --- CLI -------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lib = load_library()
    ext = register_material(lib, "sand")
    sand_phys = _sand_physical()
    density = float(sand_phys["density_kg_m3"]["mean"])
    mu = math.tan(math.radians(float(sand_phys["friction_angle_deg"]["mean"])))
    grain_mass = density * (4.0 / 3.0 * math.pi * GRAIN_RADIUS ** 3)

    env = load_envelope()
    frame_wall_ms = env.get("axes", {}).get("frame_time_ms", {}).get("max")

    results = {
        "task": "tb-0169", "seed": a.seed,
        "patch_size_m": PATCH_SIZE_M, "n_side": N_SIDE, "atom_pitch_m": ATOM_PITCH,
        "grain_radius_m": GRAIN_RADIUS, "h0_m": H0, "grain_mass_kg": grain_mass,
        "cited": {
            "DIG": {"radius": DIG_RADIUS, "cell": DIG_CELL,
                    "scoop_depth": DIG_SCOOP_DEPTH, "cell_halfwidth": DIG_CELL_HALFWIDTH,
                    "source": "CHIMERA_VISION.py DIG dict + GA_Dig.ActivateAbility, verbatim"},
            "surface_table_sand_traction": SAND_TRACTION,
            "matter_library_sand_physical": sand_phys,
            "friction_coefficient_mu": mu,
            "frame_time_ms_wall_read_live": frame_wall_ms,
        },
        "honest_gaps": [
            "grain_size_mm (0.07mm regolith, matter_library) NOT individually simulated; "
            "ATOM_PITCH (~0.167m) is a coarse DEM macro-particle -- a tractability choice, "
            "not a library-sourced number",
            "cohesion_kpa (0.5+/-0.4, matter_library) NOT modelled -- MuJoCo stock contact "
            "is frictional-only; no cohesive bonding implemented this rung",
            f"patch sized {PATCH_SIZE_M}m (not the packet's ~2m) so GA_Dig's own "
            f"{(2 * DIG_CELL_HALFWIDTH + 1) * DIG_CELL}m-wide footprint leaves a quiet "
            "coalesced remainder to test locality against -- see module docstring gap #3",
            "flat patch (no fbm dune/ridge shaping) -- isolates the coalesce/fracture/"
            "grain-physics variable under test",
        ],
        "memory_estimate": {
            "coalesced_bulk_heights_bytes": int(np.zeros((N_SIDE, N_SIDE)).nbytes),
            "note": "coalesced = ONE static aggregate: this heights array + one appearance "
                    "sample, O(1) draw. 'live_state_bytes_estimate' per cycle below is a "
                    "rough per-body accounting (qpos7+qvel6+xpos3 float64), not a MuJoCo "
                    "internal profiler reading.",
        },
    }

    heights = np.full((N_SIDE, N_SIDE), H0, dtype=np.float64)
    live = np.zeros((N_SIDE, N_SIDE), dtype=bool)

    t_render0 = time.time()
    img_before, n_before = render_snapshot(heights, live, None, ext, rng, "before")
    strip_imgs = [img_before]
    strip_labels = ["before (coalesced, flat)"]
    results["splat_counts"] = {"before": n_before}

    cycles = []
    for cyc_i, center_cell in enumerate(DIG_CENTERS, start=1):
        cyc = run_dig_cycle(heights, live, center_cell, density, mu, rng)

        img_during, n_during = render_snapshot(
            heights, cyc["mask"], cyc["mid_positions"], ext, rng, f"cycle{cyc_i}_during")

        n_exited = recoalesce(heights, live, cyc["freed_idx"], cyc["final_positions"],
                              grain_mass, density)
        seam = seam_integrity(heights, cyc["mask"])
        ledger = mass_ledger(cyc["mask"], grain_mass, n_exited, heights, density)

        img_after, n_after = render_snapshot(
            heights, live, None, ext, rng, f"cycle{cyc_i}_after")

        step_times = cyc["step_times"]
        mean_ms = float(np.mean(step_times) * 1000.0)
        max_ms = float(np.max(step_times) * 1000.0)
        k_freed = cyc["k_freed"]

        cycles.append({
            "center_dig_cell": center_cell,
            "n_freed": k_freed,
            "settle_steps_used": cyc["settled_at"] if cyc["settled_at"] is not None else MAX_SETTLE_STEPS,
            "settled_within_budget": cyc["settled_at"] is not None,
            "mean_ms_per_step": mean_ms,
            "max_ms_per_step": max_ms,
            "frame_wall_ms": frame_wall_ms,
            "breaks_frame_wall_mean": bool(frame_wall_ms is not None and mean_ms > frame_wall_ms),
            "breaks_frame_wall_max": bool(frame_wall_ms is not None and max_ms > frame_wall_ms),
            "seam": seam,
            "mass_ledger": ledger,
            "splat_counts": {"during": n_during, "after": n_after},
            "live_state_bytes_estimate": int(k_freed * 16 * 8),
        })

        strip_imgs += [img_during, img_after]
        strip_labels += [f"cycle{cyc_i} during (dig+fall, n={k_freed})",
                         f"cycle{cyc_i} after (recoalesced)"]

        print(f"cycle {cyc_i} @ dig-cell {center_cell}: freed={k_freed} "
              f"settle_steps={cycles[-1]['settle_steps_used']} "
              f"(budget_ok={cyc['settled_at'] is not None}) "
              f"mean_ms/step={mean_ms:.4f} max_ms/step={max_ms:.4f} "
              f"seam_max={seam['max_discontinuity_m']:.4f}m "
              f"mass_drift={ledger['overall_drift_fraction']:.4%} n_exited={n_exited}")

    results["cycles"] = cycles
    results["render_secs_total"] = round(time.time() - t_render0, 2)

    strip = hstack_strip(strip_imgs, strip_labels)
    strip_path = OUT_DIR / "shovel_test_strip.png"
    strip.save(strip_path)
    results["png"] = str(strip_path)

    # --- verdict, per SS15 rung C's OWN stated KILL conditions, nothing else ---
    seam_bar_m = 2.0 * ATOM_PITCH        # design: "a step much bigger than one grid cell"
    seam_fail = any(c["seam"]["max_discontinuity_m"] > seam_bar_m for c in cycles)
    frame_fail = any(c["breaks_frame_wall_mean"] for c in cycles)
    kill = seam_fail or frame_fail
    results["verdict"] = {
        "seam_bar_m": seam_bar_m,
        "seam_stitched": not seam_fail,
        "frame_wall_held": not frame_fail,
        "result": "KILL" if kill else "SURVIVES",
    }

    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nVERDICT: {results['verdict']['result']}  "
          f"(seam_stitched={results['verdict']['seam_stitched']}, "
          f"frame_wall_held={results['verdict']['frame_wall_held']})")
    print(f"-> {strip_path}")
    print(f"-> {OUT_DIR / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
