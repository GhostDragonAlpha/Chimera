"""aTerrain -- one place on that world, at the size you would walk across.

The parent is the whole shell: where land is, where sea is, how high rock can stand. It works in
thousands of kilometres and it named the process in charge here -- running water. This membrane is
a PATCH of that shell, twelve kilometres across, and it lets that process actually run.

    a rough surface + uplift          -> something to carve
    water runs downhill and gathers   -> DRAINAGE AREA
    area and slope                    -> how fast the river cuts   (stream power)
    cutting for long enough           -> valleys, and a network between them
    what the network cannot carry     -> hillslopes, at the angle loose rock stands at

NOTHING HERE DRAWS A RIVER. The height field starts as noise with the parent's roughness; water is
routed downhill; each cell is lowered by how much water crosses it and how steeply. Repeat. The
branching network is what is LEFT, and it is the signature of running water -- you cannot get it
from noise at any amplitude, and noise is exactly what terrain used to be made of here.

THE CHECK IS HACK'S LAW, AND IT IS CURRENTLY FAILING. Measure every basin's area against the length
of its longest stream and real rivers give L ~ A^0.57, on every continent, since Hack 1957. It is
not put into this simulation anywhere, which is exactly why it is the test.

    measured here: 0.19        required: 0.50 - 0.65

So by this membrane's own standard THE NETWORK IS NOT YET A DRAINAGE NETWORK. What is built is real
and it is not noise -- stream-power incision, priority-flood depression filling, hillslope creep,
and the water does now reach the sea (one basin drains 74% of the patch, up from 8% before the
hollows were filled). But the branching is not organising the way running water organises, and I
have not found why. Suspect the flats: filling a hollow leaves a surface with no gradient, and
508 cells still have nowhere downhill to send their water.

It is recorded rather than tuned away. Widening the tolerance until the check passes is the one move
this project forbids, and a membrane that fails its own test honestly is worth more than one that
passes a weakened one.
"""
from math import pi, sqrt, atan, degrees

# ── the stream-power law: dz/dt = -K A^m S^n  (Howard & Kerby 1983) ──
M_EXP = 0.5               # how strongly discharge matters -- 0.4-0.6 in the field
N_EXP = 1.0               # how strongly slope matters
K_EROSION = 4.0e-5        # erodibility, per unit time in this membrane's own steps
UPLIFT = 1.0e-3           # rock delivered per step; the landscape is a balance, never a leftover
D_HILL = 0.06             # hillslope creep: what water cannot carry, gravity still moves

REPOSE_DEG = 33.0         # loose rock stands at its friction angle and no steeper. The studio
                          # MEASURED 40.03 deg for dry lunar regolith by growing a sandpile
                          # (core/trainables/granular.py); wet, weathered soil is shallower, ~33.

PATCH_M = 12000.0         # how much ground: a two-hour walk across, which is why this size
GRID = 128


def _red_surface(n, rng, roughness):
    """The starting ground: a red-spectrum surface, power ~ 1/k.

    Real topography is not white noise -- a hill's neighbour is nearly as high as it is. Summing
    waves with amplitude 1/k IS that spectrum, and it is the same law the parent uses at planet
    scale. This is only the CANVAS; the shape that matters gets carved into it."""
    import numpy as np
    y, x = np.mgrid[0:n, 0:n] / float(n)
    z = np.zeros((n, n))
    norm = 0.0
    for octv in range(7):
        k = 2.0 * pi * (2.0 ** octv)
        amp = 1.0 / (2.0 ** octv)
        for _ in range(3):
            th = rng.uniform(0, 2 * pi)
            z += amp * np.sin(k * (np.cos(th) * x + np.sin(th) * y) + rng.uniform(0, 2 * pi))
            norm += amp * amp
    return z / sqrt(norm) * roughness


def _priority_flood(z, n, eps=1e-4):
    """FILL THE HOLLOWS -- and this is not bookkeeping, it is what water does.

    A cell lower than all eight of its neighbours has nowhere to send its water. Left alone it keeps
    it, everything upstream is cut off from the sea, and the network never organises: the drainage
    areas stay small and scattered and Hack's exponent comes out 0.2 instead of 0.57.

    Water does not do that. It FILLS the hollow until it overflows the lowest point of the rim, and
    carries on from there.

    THE ALGORITHM MATTERS. Relaxing each pit up to just above its lowest neighbour looks equivalent
    and is not: it propagates the fill level one cell per pass, so a wide basin needs as many passes
    as it is wide. Measured here -- 40 passes took 220 pits down to 111 and stalled.

    This is priority-flood (Barnes, Lehman & Mulla 2014): start at the rim, always process the
    LOWEST cell reached so far, and give every cell the higher of its own height and the level it
    was reached at. Each cell is settled once, in one pass, exactly."""
    import heapq
    import numpy as np
    done = np.zeros((n, n), dtype=bool)
    heap = []
    for i in range(n):
        for (a, b) in ((0, i), (n - 1, i), (i, 0), (i, n - 1)):
            if not done[a, b]:
                done[a, b] = True
                heapq.heappush(heap, (float(z[a, b]), a, b))
    while heap:
        lvl, a, b = heapq.heappop(heap)
        for da, db in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            ra, rb = a + da, b + db
            if 0 <= ra < n and 0 <= rb < n and not done[ra, rb]:
                done[ra, rb] = True
                if z[ra, rb] <= lvl:
                    z[ra, rb] = lvl + eps                 # it is under water: raise it to the surface
                heapq.heappush(heap, (float(z[ra, rb]), ra, rb))
    return z


def _carve(z, dx, steps, rng):
    """RUN THE WATER. Each step: raise the rock, send every cell's water to its lowest neighbour,
    add up how much crosses each cell, and lower it by the stream-power law. Then let the hillslopes
    creep.

    The order matters and is the whole trick: process cells from HIGH to LOW, so by the time a cell
    is reached everything that drains into it has already handed its water over. One pass, no
    iteration, exact."""
    import numpy as np
    n = z.shape[0]
    area0 = dx * dx
    # the eight neighbours, and the distance to each
    offs = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
            (-1, -1, sqrt(2)), (-1, 1, sqrt(2)), (1, -1, sqrt(2)), (1, 1, sqrt(2))]
    idx = np.arange(n * n)
    iy, ix = idx // n, idx % n
    for _ in range(steps):
        z += UPLIFT
        z[0, :] = z[-1, :] = z[:, 0] = z[:, -1] = 0.0      # the edges are sea level: the outlet

        # ── FILL THE HOLLOWS FIRST, and this is not bookkeeping, it is what water does ──────────
        #
        # A cell lower than all eight of its neighbours has nowhere to send its water. Left alone it
        # keeps it, and everything upstream of it is cut off from the sea -- so the network never
        # organises and the drainage areas stay small and scattered.
        #
        # Water does not do that. It FILLS the hollow until it overflows the lowest rim, and then
        # carries on. Every landscape-evolution model needs this step and this one did not have it:
        # 511 pits out of 16,384 cells, and Hack's exponent came out 0.22 against a real 0.57.
        # Relax each pit up to just above its lowest neighbour until none are left.
        _priority_flood(z, n)

        flat = z.ravel()
        # steepest descent: for each cell, which neighbour is lowest, and how steep.
        #
        # THE NEIGHBOURS MUST NOT WRAP. The first version used np.roll, which is periodic -- so a
        # cell on the left edge drained to the right edge, and the "network" was stitched across the
        # patch in a way no water does. Hack's exponent came out 0.22 against a real 0.57, which is
        # what a fractal wearing valleys looks like. The test caught it before the render did.
        best_drop = np.zeros(n * n)
        recv = idx.copy()
        for dy, dxi, dist in offs:
            ry, rx = iy + dy, ix + dxi
            ok = (ry >= 0) & (ry < n) & (rx >= 0) & (rx < n)      # off the edge is not a neighbour
            r_lin = np.where(ok, ry * n + rx, idx)
            drop = np.where(ok, (flat - flat[r_lin]) / (dist * dx), -1.0)
            better = drop > best_drop
            best_drop[better] = drop[better]
            recv[better] = r_lin[better]

        # accumulate, high to low -- one pass, because a cell's donors are always above it
        order = np.argsort(-flat)
        acc = np.full(n * n, area0)
        for c in order:
            r = recv[c]
            if r != c:
                acc[r] += acc[c]

        # STREAM POWER: the river cuts by how much water crosses and how steeply it falls
        incision = K_EROSION * (acc ** M_EXP) * (best_drop ** N_EXP)
        z -= incision.reshape(n, n)

        # hillslope creep: what the channels cannot carry, gravity still moves downhill
        # the same non-periodic rule for creep: edge-pad rather than wrap
        zp = np.pad(z, 1, mode="edge")
        lap = (zp[:-2, 1:-1] + zp[2:, 1:-1] + zp[1:-1, :-2] + zp[1:-1, 2:] - 4.0 * z)
        z += D_HILL * lap
        np.maximum(z, 0.0, out=z)
    return z, recv, acc, best_drop


def _hack_exponent(recv, acc, z, n, dx):
    """MEASURE HACK'S LAW ON WHAT WAS CARVED. For every cell, the length of the longest stream
    reaching it; against the area draining into it. Fit log L against log A.

    Observed on real rivers since Hack 1957: L ~ A^0.57, and it is nowhere in the simulation."""
    import numpy as np
    order = np.argsort(-z.ravel())
    L = np.zeros(n * n)
    for c in order:
        r = recv[c]
        if r != c:
            ddx, ddy = abs(int(r) % n - int(c) % n), abs(int(r) // n - int(c) // n)
            step = dx * (sqrt(2) if (ddx and ddy) else 1.0)
            if L[c] + step > L[r]:
                L[r] = L[c] + step
    keep = (acc > 40 * dx * dx) & (L > 3 * dx)          # real channels only, not single cells
    if keep.sum() < 50:
        return float("nan"), L
    a, b = np.polyfit(np.log(acc[keep]), np.log(L[keep]), 1)
    return float(a), L


def derive(parent, free):
    if parent is None or "carved_by" not in parent:
        raise ValueError("aTerrain requires theTerrain as its parent")
    import numpy as np
    rng = np.random.default_rng(2029)
    dx = PATCH_M / GRID

    # WHERE THIS PATCH IS. Not chosen: the parent solved an ice line, so the temperate band is
    # everything equatorward of it, and this sits in the middle of that band -- the one place on
    # this world where a person could stand outside.
    ice_lat = 90.0 - float(parent.get("glaciated_fraction", 0.3)) * 90.0
    lat = 0.5 * ice_lat

    # the canvas: the parent's own continental roughness, brought down to this patch's size
    rough = float(parent["roughness_cont_m"]) * (PATCH_M / float(parent["extent_m"])) ** 0.5 * 12.0
    z = _red_surface(GRID, rng, rough)
    z, recv, acc, slope = _carve(z, dx, 60, rng)
    hack, L = _hack_exponent(recv, acc, z, GRID, dx)

    ang = np.degrees(np.arctan(slope))
    channels = acc > 40 * dx * dx
    return {
        # ITS REAL SIZE: the patch. Twelve kilometres -- a couple of hours on foot, which is the
        # unit that matters once there is a person.
        "extent_m": PATCH_M,
        # ITS OWN DURATION: one day, inherited. The sun crosses; the landscape does not move.
        "duration_s": float(parent["day_s"]),

        "latitude_deg": lat,
        "patch_m": PATCH_M,
        "grid": GRID,
        "cell_m": dx,
        "relief_m": float(z.max() - z.min()),
        "mean_slope_deg": float(ang.mean()),
        "p95_slope_deg": float(np.percentile(ang, 95)),
        "repose_deg": REPOSE_DEG,
        "slopes_below_repose": bool(np.percentile(ang, 95) < REPOSE_DEG),
        "drainage_density_per_km": float(channels.sum() * dx / (PATCH_M / 1e3) ** 2 / 1e3),
        "hack_exponent": hack,
        "carved_by": parent["carved_by"],

        # carried for anything that stands here
        "g": float(parent["g"]),
        "T_surface": float(parent["T_surface"]),
        "lapse_rate_K_per_km": float(parent["lapse_rate_K_per_km"]),
        "day_s": float(parent["day_s"]),
        "S_earth": float(parent["S_earth"]),
        "sea_level_m": float(parent["sea_level_m"]),
        "walk_run_ms": float(parent["walk_run_ms"]),
        "P_surface_bar": float(parent["P_surface_bar"]),
    }


def emit(nums, t=1.0):
    """The matter of aTerrain, in its own local units (1.0 = half the patch).

    The ground itself, one grain per cell, coloured by what the water did to it: channels dark and
    wet, hillslopes vegetated, anything steep enough to shed its soil bare rock. Height is at TRUE
    scale here -- a 12 km patch with a few hundred metres of relief needs no exaggeration, which is
    the first membrane in this whole story that can say so.

    The movie is ONE DAY. The sun crosses, and the shadows are the point: a landscape is legible
    because of them, and at noon a real valley nearly disappears."""
    import numpy as np
    from matter import blank, paint, lit, surface_grain, SOLID

    tt = float(t)
    rng = np.random.default_rng(2029)
    n = int(nums["grid"])
    dx = float(nums["cell_m"])
    z, recv, acc, slope = _carve(_red_surface(n, rng, float(nums["relief_m"]) * 0.55), dx, 60, rng)

    half = PATCH_M / 2.0
    y, x = np.mgrid[0:n, 0:n]
    px = (x.ravel() * dx - half) / half
    py = (y.ravel() * dx - half) / half
    pz = (z.ravel() - z.mean()) / half              # TRUE SCALE: no exaggeration needed at 12 km

    b = blank(n * n)
    b[:, 0] = px
    b[:, 1] = py
    b[:, 2] = pz

    # the surface normal, from the height field -- this is what lets the sun model the ground
    gy, gx = np.gradient(z, dx)
    nrm = np.stack([-gx.ravel(), -gy.ravel(), np.ones(n * n)], axis=1)
    nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
    b[:, 21:24] = nrm

    ang = np.degrees(np.arctan(slope))
    channel = acc > 40 * dx * dx
    steep = ang > float(nums["repose_deg"]) * 0.8
    water = np.array([0.10, 0.20, 0.30], np.float32)
    veg = np.array([0.20, 0.28, 0.14], np.float32)
    rock = np.array([0.34, 0.31, 0.27], np.float32)
    albedo = np.where(channel[:, None], water, np.where(steep[:, None], rock, veg))

    # ONE DAY: the sun crosses. Its height is the latitude's, so the shadows are this place's.
    hour = 2.0 * pi * tt
    alt = max(0.06, np.cos(np.radians(float(nums["latitude_deg"]))) * np.sin(hour))
    sun = np.array([np.cos(hour), 0.25, alt], np.float32)
    sun /= np.linalg.norm(sun)
    lam = np.clip(nrm @ sun, 0.0, None)
    b[:, 16:19] = lit(albedo, float(nums["S_earth"]) * lam + 0.05,
                      e_ref=float(nums["S_earth"]), tone=0.45)
    b[:, 19] = 0.95
    b[:, 20] = surface_grain(n * n, radius=1.0, cover=0.85)
    b[:, 11] = SOLID
    return b


def measure(nums):
    """Facts -- and the one that decides whether this is a landscape or a fractal in a hat."""
    return {
        "relief_m": nums["relief_m"],
        "mean_slope_deg": nums["mean_slope_deg"],
        "drainage_density_per_km": nums["drainage_density_per_km"],
        # HACK'S LAW, measured on the carved network. Observed 0.55-0.60 on real rivers worldwide
        # since 1957, and put into this simulation nowhere.
        "hack_exponent": nums["hack_exponent"],
        "obeys_hacks_law": 0.50 < nums["hack_exponent"] < 0.65,
        # loose rock cannot stand steeper than its friction angle
        "slopes_below_repose": nums["slopes_below_repose"],
    }
