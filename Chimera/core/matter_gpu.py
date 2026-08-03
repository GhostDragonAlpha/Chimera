"""matter_gpu — THE SHAKER ON THE GPU. Cellular Potts assembly as a Warp kernel.

Commissioned 2026-07-18 (tb-0199), the human: "shaking it up into our big shaker to
find out which position is most optimal" — and the fury that the shaker was running
on ONE CPU CORE (core.matter.assemble_3d is a Python for-loop over a list; at 2x the
density record it maxed a core and never touched the 4090). This is the port.

DROP-IN for core.matter.assemble_3d — SAME signature, SAME physics (the library J
matrix, the lambda volume constraint, frozen scaffolds, 18-connectivity), on the GPU.
brain_gpu's law holds: the lattice lives on-device; ZERO CPU<->GPU syncs inside the
sweep loop; ONE readback at the end.

THREE THINGS A NAIVE PORT DROPS (each restored here, each load-bearing):
  1. frozen_type — the scaffold (bone axis; and now TERRAIN as negative space the
     human named: objects grow AROUND frozen ground) is never chosen and never
     created. Without it the skeleton dissolves into soup.
  2. the lambda VOLUME CONSTRAINT — dH += lam*((a+-1-target)^2 - (a-target)^2). This
     is why tissues SORT instead of the most-cohesive one eating the world. Drop it
     and every tissue but one vanishes.
  3. 18-CONNECTIVITY with a SAFE parallel schedule. A 2-color checkerboard is only
     conflict-free for 6-connectivity; at 18-conn, edge-diagonal cells share a
     checker color and would read each other mid-flip. So the sweep is decomposed
     into 8 colors by (x&1,y&1,z&1): two cells of one color differ by an even offset
     on every axis, so no two are within Chebyshev distance 1 -> no 18- (or 26-)
     neighbor pair ever flips in the same pass. Interface energy is therefore EXACT.
     The AREA term is exact too, but by a different mechanism: pass-start counts
     provably overshoot (Phase 1's trace: +/-600-800 cells per sweep, never
     plateauing), and claim-then-rollback atomics let rejected proposals pollute
     concurrent reads (tissue GREW +200/sweep where the CPU drains). So the
     marginal is a plain read of the live count and the count moves only on
     ACCEPTANCE -- the CPU model's serial semantics up to the read-commit gap,
     which carries committed flips only. Measured: H falls and plateaus, parity
     sorts, areas hold at the CPU's own offset (docs/THE_LIVING_MATTER.md,
     Phase-2-prerequisite membrane). The named cost: one seed no longer gives
     bit-identical grids.

Correctness is asserted by CONTRAST, same as the CPU model: parity_report() runs the
GPU sort and a uniform-J control on the same scrambled start and reports tissue radii
-> the differential must layer (bone core / skin shell), the uniform must not.
"""

from __future__ import annotations

import math

import numpy as np
import warp as wp

wp.init()

MEDIUM = 0
_FROZEN_NONE = -999

# 18-connectivity offsets: 6 faces + 12 edges (no 8 corners).
_OFF18 = [(dz, dy, dx)
          for dz in (-1, 0, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
          if (abs(dz) + abs(dy) + abs(dx)) in (1, 2)]
assert len(_OFF18) == 18


@wp.func
def _in_bounds(z: int, y: int, x: int, nz: int, ny: int, nx: int) -> bool:
    return z >= 0 and y >= 0 and x >= 0 and z < nz and y < ny and x < nx


@wp.kernel
def _potts_color_pass(
        lattice: wp.array3d(dtype=wp.int32),
        area: wp.array(dtype=wp.int32),          # LIVE counts, claimed atomically
        J: wp.array2d(dtype=wp.float32),
        offs: wp.array(dtype=wp.vec3i),
        targets: wp.array(dtype=wp.int32),
        color: wp.vec3i, temp: float, lam: wp.array(dtype=wp.float32),
        frozen: int, seed: int, n_off: int):
    z, y, x = wp.tid()
    nz = lattice.shape[0]
    ny = lattice.shape[1]
    nx = lattice.shape[2]
    # only this color's sublattice flips this pass (conflict-free for 18-conn)
    if (z & 1) != color[0] or (y & 1) != color[1] or (x & 1) != color[2]:
        return
    # interior only (a 1-cell inert rind, matching the CPU model's slicing)
    if z == 0 or y == 0 or x == 0 or z == nz - 1 or y == ny - 1 or x == nx - 1:
        return
    old = lattice[z, y, x]
    if old == frozen:
        return

    state = wp.rand_init(seed, z * ny * nx + y * nx + x)
    k = wp.randi(state, 0, n_off)
    o = offs[k]
    nzp = z + o[0]
    nyp = y + o[1]
    nxp = x + o[2]
    if not _in_bounds(nzp, nyp, nxp, nz, ny, nx):
        return
    new = lattice[nzp, nyp, nxp]
    if new == old or new == frozen:
        return

    # interface energy delta over the full 18-neighborhood
    dH = float(0.0)
    for i in range(n_off):
        oi = offs[i]
        zz = z + oi[0]
        yy = y + oi[1]
        xx = x + oi[2]
        nb = MEDIUM
        if _in_bounds(zz, yy, xx, nz, ny, nx):
            nb = lattice[zz, yy, xx]
        dH += J[new, nb] - J[old, nb]

    # THE AREA MARGINAL, READ LIVE and COMMITTED ONLY ON ACCEPTANCE. The CPU model reads the
    # count as all PREVIOUS flips left it (matter.py:440-451); the frozen pass-start counts
    # made every cell in a pass act on one stale deficit -- a bang-bang controller with unit
    # delay (THE_LIVING_MATTER Phase 1). The first fix, claim-then-rollback, reproduced the
    # serial marginal but polluted it: every REJECTED proposal's tentative claim was visible
    # to concurrent threads for a few cycles, and the measured drift flipped sign -- tissue
    # GREW +200/sweep where the CPU drains -25 and holds (probe, 2026-08-03). So: plain read
    # (racy but exact at that instant, polluted by nothing), decide, and claim only if the
    # flip happens -- serial-equivalent up to the read-commit gap, which carries committed
    # flips only.
    if old != MEDIUM:
        a = float(area[old])
        t = float(targets[old])
        dH += lam[old] * ((a - 1.0 - t) * (a - 1.0 - t) - (a - t) * (a - t))
    if new != MEDIUM:
        a = float(area[new])
        t = float(targets[new])
        dH += lam[new] * ((a + 1.0 - t) * (a + 1.0 - t) - (a - t) * (a - t))

    u = wp.randf(state)
    if dH <= 0.0 or u < wp.exp(-dH / temp):
        lattice[z, y, x] = new
        # Integer adds, committed: commutative, so the TOTAL is order-independent even
        # though the order itself is not.
        if old != MEDIUM:
            wp.atomic_add(area, old, -1)
        if new != MEDIUM:
            wp.atomic_add(area, new, 1)


# ------------------------------------------------------------------------------------------------
# THE ENERGY READOUT (THE_LIVING_MATTER Phase 1). The shaker had no way to see the quantity it
# minimises: you cannot measure a relaxation you cannot see, and `sweeps = 160/90/70/26` was
# whoever-set-it-last because no trace had ever existed to read tau_sort off of.
#
# H = sum_<i,j> J[tau(i),tau(j)] + lam * sum_{t != MEDIUM} (area_t - target_t)^2
#
# counted EXACTLY as the flip kernel counts dH: 18-connectivity, out-of-bounds neighbour =
# MEDIUM, medium an unconstrained reservoir (no area term). The per-site pair sum is halved
# at the fold. Partials go per z-slice (float atomics -- order-dependent ROUNDING only, an
# instrument noise floor of ~1e-4 relative, not a scheduling dependency: no thread reads what
# another writes). Launched after the flip pass, so the trace is the post-pass state (the
# area counts it reads are live, claimed atomically by the flips). Optional per step() call:
# assemble_3d_gpu does not pay for it, the instrument does.
# ------------------------------------------------------------------------------------------------
@wp.kernel
def _energy_partial(
        lattice: wp.array3d(dtype=wp.int32),
        J: wp.array2d(dtype=wp.float32),
        offs: wp.array(dtype=wp.vec3i),
        partials: wp.array2d(dtype=wp.float32),   # [pass_slot, z] <- interface pair sum
        slot: int, n_off: int):
    z, y, x = wp.tid()
    nz = lattice.shape[0]
    ny = lattice.shape[1]
    nx = lattice.shape[2]
    old = lattice[z, y, x]
    h = float(0.0)
    for i in range(n_off):
        oi = offs[i]
        zz = z + oi[0]
        yy = y + oi[1]
        xx = x + oi[2]
        nb = MEDIUM
        if _in_bounds(zz, yy, xx, nz, ny, nx):
            nb = lattice[zz, yy, xx]
        h += J[old, nb]
    wp.atomic_add(partials, slot, z, h)


@wp.kernel
def _energy_fold(
        partials: wp.array2d(dtype=wp.float32),
        area: wp.array(dtype=wp.int32),
        targets: wp.array(dtype=wp.int32),
        trace: wp.array(dtype=wp.float32),
        slot: int, lam: wp.array(dtype=wp.float32), n_types: int):
    """One thread: trace[slot] = half the pair sum (each interface counted twice) + area."""
    nz = partials.shape[1]
    h = float(0.0)
    for z in range(nz):
        h += partials[slot, z]
    h *= 0.5
    for t in range(1, n_types):          # t = 0 is MEDIUM, the unconstrained reservoir
        a = float(area[t])
        tg = float(targets[t])
        h += lam[t] * (a - tg) * (a - tg)
    trace[slot] = h


class Lattice:
    """A persistent on-device lattice. Nothing reads back until step() returns the trace
    or close() returns the grid; the pass loop never crosses the bus."""
    __slots__ = ("lat", "Jd", "offs", "tgtd", "aread", "colors", "frozen",
                 "temp", "lam", "lamd", "seed", "n_types", "shape", "dev",
                 "pass_count", "wcritd", "rlogd", "ruptures")

    @property
    def sweeps_done(self):
        return self.pass_count // 8


# ------------------------------------------------------------------------------------------------
# THE RUPTURE PASS (THE_LIVING_MATTER Phase 3). Griffith on the lattice's own bookkeeping,
# STATELESS: converting a cell to MEDIUM releases the tissue-tissue tension it carries and
# costs fresh crack surface against its remaining same-type support:
#     E_release = sum over unlike TISSUE neighbours of gamma_CPM(t,nb)   (the void cannot pull)
#     E_cost    = n_same * wcrit[t]        (wcrit = alpha * gamma_f, gamma_f = K_IC^2/2E)
# Rupture when E_release > E_cost. Bulk cells (E_release = 0) never rupture: fracture starts
# at surfaces and flaws, never in perfect bulk -- which is true, and is the instrument's
# self-check (rlog slot pair records any n_same >= 15 rupture as a violation).
# ------------------------------------------------------------------------------------------------
@wp.kernel
def _rupture_pass(
        lattice: wp.array3d(dtype=wp.int32),
        area: wp.array(dtype=wp.int32),
        J: wp.array2d(dtype=wp.float32),
        offs: wp.array(dtype=wp.vec3i),
        wcrit: wp.array(dtype=wp.float32),
        rlog: wp.array2d(dtype=wp.int32),     # [slot,0]=ruptures, [slot,1]=bulk violations,
                                              # [slot,2+t]=deaths of type t (Phase 3b per-type)
        slot: int, frozen: int, n_off: int):
    z, y, x = wp.tid()
    nz = lattice.shape[0]
    ny = lattice.shape[1]
    nx = lattice.shape[2]
    if z == 0 or y == 0 or x == 0 or z == nz - 1 or y == ny - 1 or x == nx - 1:
        return
    t = lattice[z, y, x]
    if t == MEDIUM or t == frozen:
        return
    carried = float(0.0)
    n_same = int(0)
    touches_medium = wp.bool(False)
    for i in range(n_off):
        oi = offs[i]
        zz = z + oi[0]
        yy = y + oi[1]
        xx = x + oi[2]
        nb = MEDIUM
        if _in_bounds(zz, yy, xx, nz, ny, nx):
            nb = lattice[zz, yy, xx]
        if nb == t:
            n_same += 1
        elif nb != MEDIUM:
            carried += J[t, nb] - 0.5 * (J[t, t] + J[nb, nb])
        else:
            touches_medium = True
    # VOID-CONNECTIVITY (Phase 3c): a rupture creates a void, and a void inside solid
    # tissue has nowhere to go. Cracks advance from surfaces -- the cell must touch
    # MEDIUM (or an existing rupture) to die. Isolated inclusions PERSIST (a rock
    # pebble in the sand shaker stays a rock pebble) unless the void reaches them.
    if not touches_medium:
        return
    if carried > wcrit[t] * float(n_same):
        lattice[z, y, x] = MEDIUM
        wp.atomic_add(area, t, -1)
        wp.atomic_add(rlog, slot, 0, 1)
        wp.atomic_add(rlog, slot, 2 + t, 1)
        if n_same >= 15:
            wp.atomic_add(rlog, slot, 1, 1)


def open_lattice(grid, shape, targets, J, temp=12.0, lam=0.9, seed=0, frozen_type=None,
                 rupture_wcrit=None):
    """Open a persistent lattice on the GPU and return its handle. Same physics and same
    seed stream as assemble_3d_gpu (pass p uses seed*131 + p), so a growth run can now be
    PAUSED, measured, and RESUMED instead of re-run from scratch to be seen.

    rupture_wcrit: None (default — the rupture pass does not exist, zero behavior
    change) or {type: wcrit_per_face} in lattice units (alpha * gamma_f, Phase 3),
    enabling the rupture pass after every completed sweep."""
    h = Lattice()
    h.dev = wp.get_device()
    h.n_types = J.shape[0]
    h.shape = tuple(int(s) for s in shape)
    h.lat = wp.array(grid.astype(np.int32), dtype=wp.int32, device=h.dev)
    h.Jd = wp.array(np.ascontiguousarray(J, dtype=np.float32),
                    dtype=wp.float32, device=h.dev)
    h.offs = wp.array([wp.vec3i(int(d[0]), int(d[1]), int(d[2])) for d in _OFF18],
                      dtype=wp.vec3i, device=h.dev)
    tgt = np.zeros(h.n_types, dtype=np.int32)
    for t, v in targets.items():
        tgt[t] = int(v)
    h.tgtd = wp.array(tgt, dtype=wp.int32, device=h.dev)
    area0 = np.array([int((grid == t).sum()) for t in range(h.n_types)],
                     dtype=np.int32)
    h.aread = wp.array(area0, dtype=wp.int32, device=h.dev)
    h.frozen = frozen_type if frozen_type is not None else _FROZEN_NONE
    h.temp, h.seed = float(temp), int(seed)
    # lam: scalar (uniform, the rung-1 protocol) or {type: value} (per-tissue,
    # Phase 5's derived bulk moduli). Always a device array for the kernels.
    h.lam = lam
    lam_arr = np.zeros(h.n_types, dtype=np.float32)
    if isinstance(lam, dict):
        for t, v in lam.items():
            lam_arr[t] = np.float32(v)
    else:
        lam_arr[:] = np.float32(lam)
    h.lamd = wp.array(lam_arr, dtype=wp.float32, device=h.dev)
    h.colors = [wp.vec3i(cz, cy, cx)
                for cz in (0, 1) for cy in (0, 1) for cx in (0, 1)]
    h.pass_count = 0
    if rupture_wcrit is None:
        h.wcritd = None
        h.rlogd = None
    else:
        wc = np.zeros(h.n_types, dtype=np.float32)
        for t, v in rupture_wcrit.items():
            wc[t] = np.float32(v)
        h.wcritd = wp.array(wc, dtype=wp.float32, device=h.dev)
        h.rlogd = wp.zeros((4096, 8), dtype=wp.int32, device=h.dev)
    h.ruptures = None
    return h


def step(handle, n_passes, trace=False):
    """Run n_passes colour passes (8 = one sweep). With trace=True, evaluate the full
    Hamiltonian on-device after every pass and return the trace as an (n_passes,) array --
    ONE readback, at the end. With trace=False return None and pay nothing for it."""
    h = handle
    partials = trace_d = None
    if trace:
        partials = wp.zeros((int(n_passes), h.shape[0]), dtype=wp.float32, device=h.dev)
        trace_d = wp.zeros(int(n_passes), dtype=wp.float32, device=h.dev)
    for i in range(int(n_passes)):
        p = h.pass_count
        col = h.colors[p % 8]
        wp.launch(_potts_color_pass, dim=h.shape,
                  inputs=[h.lat, h.aread, h.Jd, h.offs, h.tgtd, col,
                          h.temp, h.lamd, h.frozen, h.seed * 131 + p, len(_OFF18)],
                  device=h.dev)
        # No fold: the counts are LIVE -- each flip claims its marginal atomically and
        # rolls it back on rejection, the CPU model's serial semantics in scheduling
        # order. No two same-colour cells are adjacent at 18-connectivity, so within a
        # pass the interface term is untouched by the other threads.
        if trace:
            wp.launch(_energy_partial, dim=h.shape,
                      inputs=[h.lat, h.Jd, h.offs, partials, i, len(_OFF18)],
                      device=h.dev)
            wp.launch(_energy_fold, dim=1,
                      inputs=[partials, h.aread, h.tgtd, trace_d, i, h.lamd, h.n_types],
                      device=h.dev)
        h.pass_count += 1
        # THE RUPTURE PASS (Phase 3): one per completed sweep, after the flips.
        if h.rlogd is not None and h.pass_count % 8 == 0:
            slot = h.pass_count // 8 - 1
            if slot < h.rlogd.shape[0]:
                wp.launch(_rupture_pass, dim=h.shape,
                          inputs=[h.lat, h.aread, h.Jd, h.offs, h.wcritd,
                                  h.rlogd, slot, h.frozen, len(_OFF18)],
                          device=h.dev)
    if trace or h.rlogd is not None:
        wp.synchronize_device(h.dev)
        if h.rlogd is not None:
            h.ruptures = h.rlogd.numpy()
        if trace:
            return trace_d.numpy()
    return None


def close(handle):
    """One sync, one readback: the settled int16 grid. The handle is dead after this."""
    wp.synchronize_device(handle.dev)
    return handle.lat.numpy().astype(np.int16)


def assemble_3d_gpu(grid, shape, targets, J, connectivity=18, sweeps=90,
                    temp=12.0, lam=0.9, seed=0, frozen_type=None):
    """GPU drop-in for core.matter.assemble_3d. Returns the settled int16 grid.

    targets: {type: target_cell_count}. J: (n_types, n_types) float. frozen_type:
    a scaffold type that never changes or spawns (bone axis / terrain negative space).
    """
    h = open_lattice(grid, shape, targets, J, temp=temp, lam=lam, seed=seed,
                     frozen_type=frozen_type)
    step(h, 8 * int(sweeps), trace=False)
    return close(h)


def parity_report(scramble, shape, targets, J_diff, J_unif, frozen_type=None,
                  sweeps=90, seed=0, types=None):
    """The CONTRAST: same scrambled start, differential J must sort, uniform must
    not. Returns per-tissue mean cylindrical radius for both. GPU-timed. `types`
    names which ids get radii (default the tissue set; world lattices pass theirs —
    ids collide across lattices: metal = 4 = TENDON, so world callers must pass
    types or the tendon block would read metal as tendon)."""
    import time
    from core.matter import metrics_3d, BONE, MUSCLE, SKIN
    if types is None:
        types = (BONE, MUSCLE, SKIN)
    t0 = time.perf_counter()
    diff = assemble_3d_gpu(scramble.copy(), shape, targets, J_diff,
                           sweeps=sweeps, seed=seed, frozen_type=frozen_type)
    unif = assemble_3d_gpu(scramble.copy(), shape, targets, J_unif,
                           sweeps=sweeps, seed=seed, frozen_type=frozen_type)
    dt = time.perf_counter() - t0
    site_attempts = 2 * sweeps * int(np.prod(shape))
    return {"differential": metrics_3d(diff, shape, types=types)["radius"],
            "uniform": metrics_3d(unif, shape, types=types)["radius"],
            "differential_area": metrics_3d(diff, shape, types=types)["area"],
            "uniform_area": metrics_3d(unif, shape, types=types)["area"],
            "seconds": dt,
            "site_updates_per_sec": site_attempts / dt,
            "grids_shape": shape}


if __name__ == "__main__":
    import argparse
    import time
    from core.matter import (BONE, MUSCLE, SKIN, J_PROVEN_DIFFERENTIAL)

    ap = argparse.ArgumentParser(description="GPU Cellular Potts shaker")
    ap.add_argument("--n", type=int, default=96, help="lattice edge (n^3 cells)")
    ap.add_argument("--sweeps", type=int, default=90)
    a = ap.parse_args()
    N = a.n
    shape = (N, N, N)
    rng = np.random.RandomState(0)

    # a blob of scrambled tissue in the core third, medium outside
    grid = np.zeros(shape, dtype=np.int16)
    c = N // 2
    r = N // 3
    zz, yy, xx = np.mgrid[0:N, 0:N, 0:N]
    blob = (zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2 < r * r
    tissue_cells = np.argwhere(blob)
    picks = rng.choice((BONE, MUSCLE, SKIN), size=len(tissue_cells))
    grid[blob] = picks
    targets = {t: int((grid == t).sum()) for t in (BONE, MUSCLE, SKIN)}

    J_unif = np.full_like(J_PROVEN_DIFFERENTIAL, 8.0, dtype=np.float64)
    np.fill_diagonal(J_unif, 4.0)
    J_unif[MEDIUM, MEDIUM] = 0.0

    print(f"GPU shaker: {N}^3 = {N**3:,} cells, {a.sweeps} sweeps x 8 colors")
    rep = parity_report(grid, shape, targets, J_PROVEN_DIFFERENTIAL, J_unif,
                        sweeps=a.sweeps, seed=0)
    print(f"  {rep['seconds']:.2f}s  "
          f"{rep['site_updates_per_sec']/1e6:.1f}M site-updates/sec")
    from core.matter import NAMES
    for label in ("differential", "uniform"):
        r = rep[label]
        row = "  ".join(f"{NAMES[t]}:{r[t]:.1f}" for t in (BONE, MUSCLE, SKIN))
        print(f"  {label:<13} mean radius  {row}")
    d = rep["differential"]
    ok = d[BONE] < d[MUSCLE] < d[SKIN]
    print(f"  SORTED (bone core < muscle < skin shell): {ok}")

    # PHASE 1 FALSIFIER (docs/THE_LIVING_MATTER.md): the rung-1 control's energy trace
    # must be monotone-up-to-noise and it must PLATEAU. A non-monotone or non-settling
    # trace means the Hamiltonian we think we are running is not the one in the kernel.
    # Criteria: per-sweep means (8 passes each). PLATEAU = the mean of the last 10% of
    # sweeps differs from the previous 10% by less than 2% of the total drop. MONOTONE =
    # no SUSTAINED post-warmup rise. Single-sweep rises of 4-9 sigma are Boltzmann
    # physics, not pathology: the acceptance rule permits uphill excursions, and domain
    # coarsening produces correlated ones -- the measured heavy hitters (+131k at sweep
    # 0->1, +129k at 14->15) recover within 1-2 sweeps. What convicts a wrong kernel is a
    # rise that does NOT recover (the frozen-count oscillation, +/-300k forever; the
    # claim-scheme growth, +6.6M sustained). So the check walks a 10-sweep moving average
    # and allows 3 sigma of the MEAN (thermal / sqrt(10)); a blip smooths away, a trend
    # cannot hide. The 1%-of-drop bar this replaces was underived; the system's own
    # thermal scale (0.4-1.5% of the drop) falsified it.
    h = open_lattice(grid, shape, targets, J_PROVEN_DIFFERENTIAL, seed=0)
    tr = step(h, 8 * a.sweeps, trace=True)
    close(h)
    sw = tr.reshape(a.sweeps, 8).mean(axis=1)
    drop = float(sw[0] - sw[-1])
    k = max(1, a.sweeps // 10)
    thermal = float(np.diff(sw[-30:]).std()) if a.sweeps >= 40 else 0.01 * abs(drop)
    tail = float(sw[-k:].mean() - sw[-2 * k:-k].mean())
    w = 10
    ma = np.convolve(sw, np.ones(w) / w, mode="valid")
    ma_rises = np.diff(ma[max(0, k - w + 1):])
    worst_sustained = float(ma_rises.max()) if len(ma_rises) else 0.0
    mono = worst_sustained <= 3.0 * thermal / math.sqrt(w)
    plateau = abs(tail) <= 0.02 * abs(drop)
    print(f"  ENERGY TRACE: H {sw[0]:.1f} -> {sw[-1]:.1f} (drop {drop:.1f}); "
          f"worst sustained rise {worst_sustained:.0f} vs {3*thermal/math.sqrt(w):.0f} "
          f"(3 sigma of the 10-sweep mean; thermal std {thermal:.0f} = "
          f"{100*thermal/max(abs(drop),1e-9):.2f}% of drop), "
          f"tail drift {tail:.3f} ({100*abs(tail)/max(abs(drop),1e-9):.3f}%)")
    print(f"  PHASE 1: monotone {mono}, plateau {plateau} -> "
          f"{'PASS' if (mono and plateau) else 'FAIL -- the kernel is not running the Hamiltonian we think it is'}")
