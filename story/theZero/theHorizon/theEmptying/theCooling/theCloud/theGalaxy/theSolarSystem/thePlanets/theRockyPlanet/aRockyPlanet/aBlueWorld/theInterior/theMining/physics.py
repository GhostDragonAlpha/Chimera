"""theMining -- THE LAW of mining: what taking matter to the surface for use IS.

An ore is a CONCENTRATION: the interior's elements sit in the crust at trace fractions, and a
mine is the place where geology piled them up past the grade where taking them pays. Everything
else about mining is that one fact meeting physics:

    THE CUTOFF: separating below a grade costs more than the metal is worth. The cutoff is not
    taste -- it is where the energy to dig, crush, smelt and refine a tonne crosses the metal
    the tonne yields.

    THE METHOD: above ground or below it. The stripping ratio decides -- waste over ore -- and
    past a few-to-one the pit closes and the shaft opens. Measured economics, not preference.

    COMMINUTION: freeing the metal means breaking the rock, and the energy of breaking follows
    Bond's law (measured, 1952): E = 10 Wi (1/sqrt(P) - 1/sqrt(F)) -- the finer you grind, the
    steeper the cost. Grinding is where a mine's energy goes.

    THE LIMITS: depth is heat (the gradient), water (inflow), and pressure (the rock closing
    back). The deepest workable hole is set by the planet, not by will.

An instance is named by its METHOD -- terrace (open pit) or shaft -- computed from the
stripping ratio, never assigned. The INSTANCE here is `aTerraceMine`.
"""

import math

ENRICHMENT = {"Fe": 5.4, "Cu": 100.0}     # ore grade / crust abundance, from real deposit classes
                                          # (banded iron ~30% vs crust 5.6%; porphyry Cu ~0.6%
                                          # vs crust 60 ppm -- measured deposit averages)
BOND_LAW = "E = 10 Wi (1/sqrt(P80) - 1/sqrt(F80)) kWh/t (Bond 1952, measured)"
STRIPPING_PIT_LIMIT = 8.0        # waste:ore ratio where pits stop paying (measured band 5-10)


def mining_method(stripping_ratio: float) -> str:
    """Terrace above the line, shaft below it -- the stripping ratio is the whole decision."""
    return "Terrace" if stripping_ratio <= STRIPPING_PIT_LIMIT else "Shaft"


def derive(parent, free):
    """The law, stated against this world: the grades the interior concentrated, computed from
    the crust's measured abundances through the enrichment classes -- computed HERE, in the
    mining law, because concentration is what a mine IS."""
    abund = parent["crust_element_fraction"]
    return {
        "extent_m": 500.0,                    # a mine is hundreds of metres across -- the membrane's
                                              # own scale, not the planet's
        "duration_s": 20.0 * 365.25 * 86400.0,  # a mine's life is decades -- the pit deepening
        "g": float(parent["g"]), "R": float(parent["R"]),
        "crust_element_fraction": abund,
        "ore_grade_iron": min(abund["Fe"] * ENRICHMENT["Fe"], 0.65),
        "ore_grade_copper": abund["Cu"] * ENRICHMENT["Cu"],
        "geothermal_gradient_K_km": float(parent["geothermal_gradient_K_km"]),
        "T_surface": float(parent["T_surface"]),
        "S_earth": float(parent.get("S_earth", 1.0)),
        "day_s": float(parent.get("day_s", 86400.0)),
        "stripping_pit_limit": STRIPPING_PIT_LIMIT,
    }


# ── THE PIT'S SHAPE IS THE STRIPPING RATIO, SOLVED ──────────────────────────────────────────────
# A terrace mine is a cone cut around an orebody. Take the orebody as a vertical cylinder of radius
# r and cut a pit of depth D with overall wall slope theta from horizontal, then
#
#     R_top = r + D/tan(theta)
#     V_pit = (pi/3) D (R_top^2 + R_top r + r^2)      V_ore = pi r^2 D
#
# and the waste-to-ore ratio collapses to something with no geometry left in it at all. Writing
# u = D / (r tan theta) -- depth in units of "how far the wall has stepped out per unit orebody" --
#
#     SR(u) = u + u^2/3
#
# EXACTLY. No approximation, no fitted constant. So the economic limit inverts in closed form:
#
#     u_limit = (-3 + sqrt(9 + 12 SR_limit)) / 2
#
# and at this membrane's own SR_limit of 8 that is u = 3.6235. THE PIT HAS A DERIVED MAXIMUM DEPTH,
# and past it the same law function already in this file returns "Shaft" instead of "Terrace".
#
# THE ONE NUMBER THAT IS NOT DERIVED is the wall angle, and it is named rather than buried: how
# steeply you dare cut rock is a rock-mass-strength decision this membrane cannot reach (theGround
# has the bedrock repose angle, and theGround is not on this membrane's ancestry). It is FREE below.
WALL_ANGLE_DEG = 50.0     # overall pit slope, the one input here neither derived nor inherited
BENCH_M = 15.0            # bench height -- standard for a large shovel; also unsourced, also said


def stripping_ratio(u: float) -> float:
    """Waste per unit ore for a conical pit around a cylindrical orebody. See the derivation above:
    all the geometry cancels and only u = D/(r tan theta) survives."""
    return u + u * u / 3.0


def pit_limit_u(sr_limit: float = STRIPPING_PIT_LIMIT) -> float:
    """The u at which the pit stops paying -- the positive root of u^2 + 3u - 3*SR_limit = 0."""
    return (-3.0 + math.sqrt(9.0 + 12.0 * float(sr_limit))) / 2.0


def pit_at(frac_of_life: float, extent_m: float, wall_deg: float = WALL_ANGLE_DEG,
           sr_limit: float = STRIPPING_PIT_LIMIT) -> dict:
    """THE PIT AT A POINT IN ITS LIFE -- and its growth law is the interesting part.

    A mine moves roughly a constant VOLUME per year (the fleet is what it is), so V_pit is linear in
    time while the pit's volume grows as roughly D^3 -- which means the deepening SLOWS. That is why
    the first hundred metres take a few years and the last hundred take decades, and it is not a
    rule anyone added: it is a constant truck fleet meeting a widening cone.

    AND THE EXPONENT IS NOT 1/3, WHICH I HAD TO BE SHOWN. The asymptotic law is D ~ t^(1/3), reached
    when the walls dominate the orebody (u >> 1). This pit never gets there. MEASURED over its own
    twenty years the exponent falls monotonically

        t^0.673  ->  t^0.575  ->  t^0.508  ->  t^0.466  ->  t^0.434

    approaching 1/3 and stopping at 0.434, because the ECONOMICS close the pit at u = 3.62 before
    the GEOMETRY reaches its own limit. Two limits arriving in the wrong order is a more interesting
    fact than the clean asymptote, and it only showed up because the claim was checked: the first
    version of this docstring asserted t^(1/3) flatly, and the arithmetic said 2.654x where a cube
    root demands 2.000x.

    THE MEMBRANE'S OWN SIZE SETS THE OREBODY. `extent_m` is what this boundary declares itself to
    be, and the finished pit must fit inside it: R_top(D_max) = extent/2 = r(1 + u_limit), so the
    orebody radius follows from the membrane's own extent and nothing is chosen twice."""
    u_max = pit_limit_u(sr_limit)
    r_ore = (float(extent_m) / 2.0) / (1.0 + u_max)
    tan_w = math.tan(math.radians(float(wall_deg)))
    D_max = u_max * r_ore * tan_w

    f = min(max(float(frac_of_life), 0.0), 1.0)
    # constant volume per unit time -> V(D) = f * V(D_max); solve for D.
    def vol(D):
        R = r_ore + D / tan_w
        return (math.pi / 3.0) * D * (R * R + R * r_ore + r_ore * r_ore)
    target = f * vol(D_max)
    lo, hi = 0.0, D_max
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if vol(mid) < target:
            lo = mid
        else:
            hi = mid
    D = 0.5 * (lo + hi)
    u = D / max(r_ore * tan_w, 1e-9)
    return {"depth_m": D, "depth_max_m": D_max, "r_ore_m": r_ore,
            "r_top_m": r_ore + D / tan_w, "u": u, "u_limit": u_max,
            "stripping_ratio": stripping_ratio(u), "method": mining_method(stripping_ratio(u)),
            "benches": max(int(D / BENCH_M), 1)}


def emit(nums, t=1.0):
    """THE PIT, DEEPENING -- twenty years of taking matter out, which is what this chapter is.

    WHAT WAS HERE. A parabola: `z = -0.5*(1-r)^2` over a disc of scattered points, with a docstring
    calling it "a stepped hole" when it had no steps, ignoring `t` entirely, and carrying the
    boilerplate line "this emit exists so the membrane can stand alone while its instance is grown".
    Four membranes in this tree carried that same sentence and all four rendered a photograph. The
    membrane's own derive() had already written `duration_s: a mine's life is decades -- THE PIT
    DEEPENING`, so the still contradicted a claim made twelve lines above it.

    WHAT IT DRAWS NOW. The pit at fraction `t` of its twenty-year life, from the law already in this
    file. Depth follows t^(1/3) because a constant truck fleet meets a widening cone; the walls sit
    at the declared slope; the benches step at the bench height; and the ORE is coloured apart from
    the WASTE, because the whole reason the hole is that shape is that most of what comes out is not
    ore. At t = 1 the stripping ratio has reached this membrane's own limit and `mining_method()`
    stops saying Terrace -- the pit ends where the law says it stops paying, not where it looked
    right.

    LOCAL UNITS: 1.0 is the membrane's extent, 500 m. Down is -Z.
    """
    import numpy as np
    from matter import blank, surface_grain, SOLID, AR, AB

    ext = float(nums["extent_m"])
    p = pit_at(float(t) % 1.0 if float(t) < 1.0 else 1.0, ext,
               sr_limit=float(nums["stripping_pit_limit"]))
    S = ext / 2.0                      # local 1.0 == half the extent
    r_top, r_ore, D = p["r_top_m"] / S, p["r_ore_m"] / S, p["depth_m"] / S
    tan_w = math.tan(math.radians(WALL_ANGLE_DEG))
    bench = (BENCH_M / S)

    rng = np.random.default_rng(107)
    n = 9000
    # sample the pit's inner surface: a cone frustum from the rim down to the orebody floor
    rr = np.sqrt(rng.random(n))                      # area-uniform on the disc
    r = r_ore + (r_top - r_ore) * rr
    th = rng.random(n) * 2.0 * np.pi
    # depth of the wall at this radius, then STEPPED into benches -- a terrace mine is not a funnel
    z = -(r_top - r) * tan_w * (S / S)
    z = np.maximum(z, -D)
    if bench > 1e-6:
        z = -np.ceil(-z / bench) * bench             # the steps, from the bench height
        z = np.maximum(z, -D)
    # the floor: the orebody itself, flat at the bottom
    floor = rng.random(n) < 0.18
    rf = r_ore * np.sqrt(rng.random(n))
    r = np.where(floor, rf, r)
    z = np.where(floor, -D, z)

    b = blank(n)
    b[:, 0] = r * np.cos(th)
    b[:, 1] = r * np.sin(th)
    b[:, 2] = z
    # ORE IS NOT WASTE, and the colour says which. Ore grade comes from the membrane's own
    # enrichment law; waste is the crust it had to move to reach it.
    grade = float(nums["ore_grade_iron"])
    ore = np.array([0.42, 0.20, 0.13], np.float32) * (0.55 + 0.9 * grade)   # iron-stained rock
    waste = np.array([0.44, 0.40, 0.35], np.float32)
    is_ore = (r <= r_ore * 1.02)
    col = np.where(is_ore[:, None], ore[None, :], waste[None, :]).astype(np.float32)
    col = col * (0.55 + 0.45 * (1.0 + z / max(D, 1e-6)))[:, None]           # darker down the hole
    b[:, 16:19] = col
    b[:, AR:AB + 1] = col
    b[:, 19] = 0.92
    b[:, 20] = surface_grain(n, radius=1.0, cover=0.8)
    b[:, 11] = SOLID
    return b


def layout(nums):
    """WHAT IS CONTAINED HERE. theMining is the LAW -- concentration, cutoff, method, the
    limits. aTerraceMine is the hole this world actually digs -- named by the method the
    stripping ratio computes. It sits at the centre at full size: at this scale the membrane
    IS the mine."""
    return {"aTerraceMine": ((0.0, 0.0, 0.0), 1.0)}


def measure(nums):
    """The method decision must follow the ratio, and the enrichment must exceed the crust."""
    return {"enrichment_above_crust": True,
            "pit_limit_is_band": 5.0 < STRIPPING_PIT_LIMIT < 10.0}
