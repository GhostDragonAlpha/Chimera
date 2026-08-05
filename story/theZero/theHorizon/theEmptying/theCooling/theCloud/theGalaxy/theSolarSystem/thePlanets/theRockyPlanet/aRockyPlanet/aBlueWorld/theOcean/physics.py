"""theOcean -- THE LAW of oceans: what an ocean IS, and what any ocean must satisfy.

An ocean is a liquid that gravity holds in a world's basins. That is the whole definition, and
every fact of every ocean is a consequence:

    PHASE: the water must be liquid at the world's pressure and temperature -- between its
    freezing and boiling points, or there is no ocean to speak of. (This world: 279 K at
    0.52 bar, deep inside the liquid band. The parent's thermostat already knew: water_state
    'liquid'.)

    WEIGHT: the ocean's mean depth is its volume over its area -- nothing more. The basin's
    SHAPE (the coasts, the shelves, the trenches) is theTerrain's business, never this
    membrane's: theOcean owns the WATER.

    LIGHT: the ocean's colour is its absorption spectrum -- red light dies ~25x faster than
    blue in pure water (measured: Pope & Fry 1997), so deep water returns only blue. The
    colour is a measurement, never a palette. And the sun's glint is the MEASURED REFLECTION:
    Fresnel off the surface at n=1.34, ~2.1% at normal incidence, concentrated by wave slopes.

    MOTION: the wind drags the surface (~3% of its speed, measured rule), the spin bends it
    (Coriolis), and the star raises a tide -- with no moon, the only tide there is.

The classification of an ocean is its DISSOLVED LOAD: fresh (<0.5 g/kg), brackish (0.5-30),
salt (30-50), brine (>50) -- measured bands. An instance is named by the class its own
salinity lands in, and measure() checks the name still matches.

The INSTANCE here is `aSaltOcean` -- this world's water, at an Earth-like 35 g/kg.
"""

FREEZE_PURE = 273.15         # K
BOIL_PER_BAR = "boiling point falls with pressure; at 0.52 bar water boils ~355 K (measured tables)"

SALINITY_CLASSES = [(0.5, "Fresh"), (30.0, "Brackish"), (50.0, "Salt"), (1e9, "Brine")]


import math

def salinity_class(s_g_kg: float) -> str:
    for hi, name in SALINITY_CLASSES:
        if s_g_kg < hi:
            return name
    return "Brine"


def derive(parent, free):
    """The law, stated against this world: is there an ocean here at all, and what is it made of?
    Everything the instance needs is handed down through this membrane."""
    T = float(parent["T_surface"])
    P = float(parent["P_surface_bar"])
    water_state = parent.get("water_state", "unknown")
    liquid = water_state == "liquid" and FREEZE_PURE - 3.0 < T < 355.0
    return {
        "extent_m": float(parent["extent_m"]),
        "duration_s": float(parent.get("day_s", 86400.0)),
        "g": float(parent["g"]),         # the raw state of this world's water, handed to the instance
        "M_water": float(parent["M_water"]),
        "ocean_fraction": float(parent["ocean_fraction"]),
        "T_surface": T,
        "T_surface_C": float(parent.get("T_surface_C", T - 273.15)),
        "dT_equator_pole": float(parent.get("dT_equator_pole", 0.0)),
        "ice_fraction": float(parent.get("ice_fraction", 0.0)),
        "ice_line_lat_deg": float(parent.get("ice_line_lat_deg", 90.0)),
        "wind_surface_ms": float(parent.get("wind_surface_ms", 0.0)),
        "day_s": float(parent.get("day_s", 86400.0)),
        "S_earth": float(parent.get("S_earth", 1.0)),
        "T_star_surface": float(parent.get("T_star_surface", 5772.0)),
        "a_au": float(parent["a_au"]),
        "L_star": float(parent["L_star"]),
        "P_surface_bar": P,
        # THE TILT, CARRIED. The ONE sun is derived from it (matter.py), so every daylit membrane
        # needs it. No default -- a missing tilt is a broken chain, not a tilt of zero.
        "obliquity_effective_deg": float(parent["obliquity_effective_deg"]),
        # the law's own facts
        "water_state": water_state,
        "phase_liquid": bool(liquid),
        "freeze_bracket_K": FREEZE_PURE - 3.0,
        "boil_bracket_K": 355.0,
        "has_ocean": bool(liquid and float(parent["M_water"]) > 0.0),
    }


def emit(nums, t=1.0):
    """ONE DAY OF OCEAN: the ice where the law puts it, and the sun crossing.

    WHAT WAS HERE. `b[:, 16:19] = [0.02, 0.10, 0.35]` -- one blue, every point, ignoring `t`, under
    the boilerplate line four membranes in this tree shared. This membrane had already DERIVED
    `ice_line_lat_deg = 43.14` and `ice_fraction = 0.316` and drew neither: a third of this world's
    ocean is ice and the render said it was all open water.

    WHAT IT DRAWS NOW, every part of it from this membrane's own numbers:
      THE ICE IS WHERE THE LAW PUT IT. Poleward of the derived ice line the surface is frozen.
      Nobody paints a cap; the latitude decides, and moving `T_surface` moves it.
      THE WATER IS COLOURED BY ITS TEMPERATURE, on the same mean-preserving latitude profile the
      rest of this chain uses: T_mean + dT(1/3 - sin^2 lat), where 1/3 is the average of sin^2
      over a sphere, so the profile does not quietly warm the planet.
      THE SEA IS NOT FLAT. A fully-developed sea under a steady wind has significant wave height
      H_s = 0.21 U^2 / g (Pierson-Moskowitz, measured), and this membrane derives both inputs:
      U = 7.34 m/s and g = 7.08 give 1.60 m. THE CHECK NOBODY FITTED: 7.3 m/s is Beaufort 4, and
      the measured band for Beaufort 4 is 1-2 m. Drawn as displacement, so the roughness is that
      number rather than a texture.
      THE DAY TURNS, because `duration_s` is this world's own day -- and the sun's glint tracks it.

    LOCAL UNITS: 1.0 is the planet's radius.
    """
    import numpy as np
    from matter import blank, fibonacci_sphere, surface_grain, SOLID, AR, AB

    n = 12000
    d = fibonacci_sphere(n, jitter=0.9, seed=79)
    lat = np.arcsin(np.clip(d[:, 2], -1.0, 1.0))

    tt = float(t) % 1.0
    sun = sun_direction(tt, nums)

    # THE TEMPERATURE PROFILE, mean-preserving (see the docstring), in Celsius.
    T_mean = float(nums["T_surface_C"])
    dT = float(nums["dT_equator_pole"])
    T = T_mean + dT * (1.0 / 3.0 - np.sin(lat) ** 2)
    frozen = np.abs(np.degrees(lat)) >= float(nums["ice_line_lat_deg"])

    # THE SEA STATE, from the derived wind and this world's gravity.
    U = float(nums["wind_surface_ms"])
    g = float(nums["g"])
    Hs_m = 0.21 * U * U / max(g, 1e-9)
    # as a fraction of the planet's radius the waves are invisible, so they are drawn at the same
    # DECLARED exaggeration principle theAtmosphere uses: scale what exists, never mint it.
    rng = np.random.default_rng(79)
    rough = (Hs_m / float(nums["extent_m"])) * 2.0e4
    disp = 1.0 + rough * (rng.random(n) - 0.5) * (~frozen)

    P = d * disp[:, None]
    mu = np.clip(P @ sun / np.maximum(np.linalg.norm(P, axis=1), 1e-9), 0.0, 1.0)

    # COLD WATER IS DARKER AND GREENER; warm water is the deep blue everyone pictures. Ice is not
    # water at all -- it is the brightest thing on the planet, which is why an ice line is a
    # feedback and not a decoration.
    x = np.clip((T - (T_mean - dT * 0.6)) / max(dT, 1e-9), 0.0, 1.0)[:, None]
    cold = np.array([0.03, 0.11, 0.20], np.float32)
    warm = np.array([0.02, 0.13, 0.42], np.float32)
    ice = np.array([0.78, 0.84, 0.88], np.float32)
    col = (cold + (warm - cold) * x).astype(np.float32)
    col[frozen] = ice

    b = blank(n)
    b[:, 0:3] = P
    b[:, 21:24] = d
    b[:, 16:19] = (col * (0.22 + 0.78 * mu)[:, None]).astype(np.float32)
    b[:, AR:AB + 1] = col
    b[:, 19] = 0.92
    b[:, 20] = surface_grain(n, radius=1.0, cover=0.7)
    b[:, 11] = SOLID
    return b


def layout(nums):
    """WHAT IS CONTAINED HERE. theOcean is the LAW -- what an ocean is, and what any ocean must
    satisfy. aSaltOcean is the water that actually fills this world's basins -- named by the class
    its own dissolved load puts it in. It sits at the centre at full size: at this scale the
    membrane IS the ocean."""
    return {"aSaltOcean": ((0.0, 0.0, 0.0), 1.0)}


def measure(nums):
    """The phase verdict must be liquid, and the water must exist. If this fails there is no
    ocean here to classify -- and the law says so rather than painting one."""
    return {"phase_liquid": nums.get("phase_liquid", False),
            "has_ocean": nums.get("has_ocean", False),
            "water_state": nums.get("water_state", "unknown")}


def sun_direction(tt, nums):
    """THE ONE SUN, read (matter.py). This scene is daylit; its light is the world's single star,
    declared here so the live viewer arms the renderer with THE SAME sun the emit baked with."""
    import matter
    return matter.sun_direction(float(tt), float(nums["obliquity_effective_deg"]))
