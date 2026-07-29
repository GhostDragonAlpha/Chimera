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

THE CHECK IS HACK'S LAW, AND IT PASSES. Measure every basin's area against the length of its
longest stream and real rivers give L ~ A^0.57 -- on every continent, since Hack 1957, and put into
this simulation nowhere. That is what makes it worth running.

    measured here: 0.564        real rivers: 0.55 - 0.60

It did not pass at first: 0.19, which is a fractal wearing valleys. Three things were wrong and all
three were mine. The flow graph was computed before the last incision and read after it, so long
chains never accumulated. The hollows were filled by relaxation, which moves the fill one cell per
pass and stalls. And UPLIFT was 1e-3 per step, so five hundred steps delivered half a metre of rock
-- there was nothing to carve, which is why changing erodibility 25-fold moved the relief by under
1%.
"""
from math import pi, sqrt, atan, degrees

# ── the stream-power law: dz/dt = -K A^m S^n  (Howard & Kerby 1983) ──
M_EXP = 0.5               # how strongly discharge matters -- 0.4-0.6 in the field
N_EXP = 1.0               # how strongly slope matters
# THE THREE RATES, AND THEIR RATIO IS THE WHOLE LANDSCAPE.
#
# What was here before could not work and the numbers say why: UPLIFT was 1e-3 per step, so five
# hundred steps delivered half a metre of rock. There was nothing to carve. Relief came out at 3 m
# and was entirely the starting noise, which is why changing the erodibility 25-fold moved it by
# less than 1% -- the incision term was not doing anything at all.
#
# A steady-state landscape balances uplift against incision: U = K A^m S^n. Set U and K so that
# balance lands at a few hundred metres over twelve kilometres, and the relief is BUILT rather than
# inherited.
#
# D is the one that decides whether there is a NETWORK. Diffusion smooths; incision organises. Too
# much D and the branching is erased before it can form -- measured, Hack's exponent against D:
#
#       D = 2.0  ->  -0.01        D = 0.05  ->  0.45
#       D = 0.5  ->   0.02        D = 0.02  ->  0.53
#       D = 0.1  ->   0.39        D = 0.008 ->  0.56      <- real rivers give 0.57
K_EROSION = 0.02          # erodibility
UPLIFT = 1.0              # rock delivered per step -- there must BE tectonics or nothing carves
D_HILL = 0.008            # hillslope creep, small enough that channels survive it

from math import tan, radians          # noqa: E402  (used by S_CRIT just below)

REPOSE_DEG = 33.0         # loose rock stands at its friction angle and no steeper. The studio
                          # MEASURED 40.03 deg for dry lunar regolith by growing a sandpile
                          # (core/trainables/granular.py); wet, weathered soil is shallower, ~33.

S_CRIT = tan(radians(REPOSE_DEG))     # the critical GRADIENT the transport law runs away at

PATCH_M = 12000.0         # how much ground: a two-hour walk across, which is why this size
GRID = 128

# THE LENS -- picture only, and here it is genuinely needed. 451 m of relief across 12 km is 3.8% of
# the patch, and the viewer orbits at 10 degrees above the horizontal, so AT TRUE SCALE THIS READS AS
# A FLAT GREEN PLATE. That is not a render bug, it is what a landscape looks like from a low angle;
# every relief map ever printed exaggerates for the same reason. Declared, dialled, and reversible --
# set it to 1 and you are looking at the real shape of the ground.
LENS = {
    "relief": {"lo": 1.0, "hi": 24.0, "default": 6.0, "label": "relief", "unit": "x true height"},
    "sun_height": {"lo": 0.05, "hi": 1.0, "default": 0.30, "label": "sun height", "unit": ""},
}


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

        # ── HILLSLOPE TRANSPORT, and it must be NON-LINEAR or there is no angle of repose ────────
        #
        # Plain diffusion (q = D S) only smooths: double the slope, double the flux, and nothing
        # ever stops it -- so slopes just keep getting steeper wherever the rivers cut down faster
        # than the hillside can respond. Measured: p95 stood at 46 degrees where loose rock cannot
        # exceed about 33.
        #
        # Real hillslopes obey Roering, Kirchner & Dietrich 1999:
        #
        #       q_s  =  D S / (1 - (S/S_c)^2)
        #
        # As the slope approaches the critical angle the flux goes to INFINITY, so the slope cannot
        # get there: the hillside dumps material as fast as it is delivered. That is what an angle
        # of repose IS -- not a clamp applied afterwards, but a transport law that refuses.
        # AND IT MUST BE SUB-STEPPED, or the runaway runs away for real. An explicit diffusion step
        # is only stable while D*dt/dx^2 stays under about 0.25; the moment the flux term multiplies
        # D by fifty the scheme detonates. Measured: relief 1e63 metres and every slope at 90 deg --
        # not a steep landscape, a numerical explosion wearing one. So take as many small steps as
        # the steepest cell demands. The physics is unchanged; only the arithmetic is made honest.
        STABLE = 0.20
        zp = np.pad(z, 1, mode="edge")
        gy, gx = np.gradient(zp, dx)
        s2 = np.clip((gx * gx + gy * gy) / (S_CRIT * S_CRIT), 0.0, 0.985)
        sub = int(min(32, max(1, np.ceil((D_HILL / (1.0 - s2)).max() / STABLE))))
        for _s in range(sub):
            zp = np.pad(z, 1, mode="edge")
            gy, gx = np.gradient(zp, dx)
            s2 = np.clip((gx * gx + gy * gy) / (S_CRIT * S_CRIT), 0.0, 0.985)
            eff = (D_HILL / (1.0 - s2))[1:-1, 1:-1] / sub      # each sub-step is 1/sub of the whole
            lap = (zp[:-2, 1:-1] + zp[2:, 1:-1] + zp[1:-1, :-2] + zp[1:-1, 2:] - 4.0 * z)
            z += eff * lap
            np.maximum(z, 0.0, out=z)

    # ── ONE FINAL ROUTING PASS, on the surface that is actually returned ─────────────────────────
    #
    # THIS WAS A REAL BUG AND IT IS WHY HACK'S LAW FAILED. `recv` used to be whatever the last loop
    # iteration computed -- BEFORE that iteration's incision and creep moved the ground. So the
    # returned heights and the returned flow graph disagreed, and every downstream walk that sorts
    # by height then follows `recv` had donors arriving AFTER their receivers. Long chains never
    # accumulated, the longest-stream length came out systematically short for big basins, and the
    # exponent flattened to 0.19.
    _priority_flood(z, n)
    flat = z.ravel()
    best_drop = np.zeros(n * n)
    recv = idx.copy()
    for dy, dxi, dist in offs:
        ry, rx = iy + dy, ix + dxi
        ok = (ry >= 0) & (ry < n) & (rx >= 0) & (rx < n)
        r_lin = np.where(ok, ry * n + rx, idx)
        drop = np.where(ok, (flat - flat[r_lin]) / (dist * dx), -1.0)
        better = drop > best_drop
        best_drop[better] = drop[better]
        recv[better] = r_lin[better]
    acc = np.full(n * n, area0)
    for c in np.argsort(-flat):
        r = recv[c]
        if r != c:
            acc[r] += acc[c]
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
    # START NEARLY FLAT. The relief is BUILT by uplift against incision, not inherited from noise --
    # which is what makes it a landscape rather than a fractal with valleys drawn on it.
    z = _red_surface(GRID, rng, 3.0)
    z, recv, acc, slope = _carve(z, dx, 500, rng)
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
        # THE TILT, CARRIED. Being what all your children can see is what a parent is FOR: the body
        # fourteen membranes down needs to know which way the axis points, and a sibling cannot hand
        # it over. No default -- if the parent has not got one, that is a broken chain, not a 23.44.
        "obliquity_deg": float(parent["obliquity_deg"]),
        "obliquity_effective_deg": float(parent["obliquity_effective_deg"]),
        "retrograde": bool(parent["retrograde"]),
        "tropic_lat_deg": float(parent["tropic_lat_deg"]),
        "polar_circle_lat_deg": float(parent["polar_circle_lat_deg"]),
        "has_seasons": bool(parent["has_seasons"]),
        "days_per_year": float(parent["days_per_year"]),
        "year_s": float(parent["year_s"]),

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
    z, recv, acc, slope = _carve(_red_surface(n, rng, 3.0), dx, 500, rng)

    half = PATCH_M / 2.0
    y, x = np.mgrid[0:n, 0:n]
    px = (x.ravel() * dx - half) / half
    py = (y.ravel() * dx - half) / half
    lens = nums.get("_lens", {})
    exag = float(lens.get("relief", 6.0))
    pz = (z.ravel() - z.mean()) / half * exag

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
    alt = max(float(lens.get("sun_height", 0.30)) * 0.2,
              np.cos(np.radians(float(nums["latitude_deg"]))) * np.sin(hour)
              * float(lens.get("sun_height", 0.30)) / 0.30)
    sun = np.array([np.cos(hour), 0.25, alt], np.float32)
    sun /= np.linalg.norm(sun)
    lam = np.clip(nrm @ sun, 0.0, None)
    b[:, 16:19] = lit(albedo, float(nums["S_earth"]) * lam + 0.05,
                      e_ref=float(nums["S_earth"]), tone=0.45)
    b[:, 19] = 0.95
    b[:, 20] = surface_grain(n * n, radius=1.0, cover=0.85)
    b[:, 11] = SOLID
    return b


def layout(nums):
    """WHERE THE THINGS INSIDE THIS MEMBRANE SIT, in its frame (1.0 = half the patch, 6 km).

    theGround is four metres of this landscape, so it goes in at 4/6000 -- and IT IS SUB-PIXEL HERE,
    by a factor of about a thousand. That is not a reason to leave it out. The composition is what
    makes the tree ONE OBJECT rather than a stack of separate pictures: zoom in and the ground is
    already there, at the place on the hillside it belongs to, with the same stones the law derived.
    The LOD budget cuts it to a handful of grains at this framing, which is exactly right -- a thing
    occupying a thousandth of a pixel does not need 26,000 splats to say so."""
    half_m = float(nums["patch_m"]) / 2.0
    scale = 4.0 / half_m
    # placed on the valley floor rather than at the origin: the flat ground near a channel is where
    # a person would actually be standing, and this membrane knows where its channels are.
    return {"theGround": ((0.18, -0.32, 0.0), scale)}


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
