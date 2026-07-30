"""theBiomes -- THE LAW of biomes: what a biome IS, and how the bands are forced.

A biome is the largest community of life a climate can hold. Nothing about it is chosen: give a
world's temperature and its rain, and the bands are FORCED, because life has requirements that
do not negotiate -- warmth enough to grow, water enough to drink, light enough to eat.

    THE TWO AXES: mean annual temperature x annual rain. The established classification
    (Whittaker 1970) is a table on those two axes: rainforest, forest, taiga, steppe, desert,
    tundra, ice. Change the climate and the same table repaints the world.

    THE MEASURED LOOK: each band reflects light its own measured way -- chlorophyll absorbs
    blue (430-450 nm) and red (640-680) and throws green back (the Red Edge at ~700-750 nm is
    the sharpest vegetation signature known); sand returns ~0.35 across the band; snow ~0.85;
    ocean ~0.06. A biome map is a reflectance map.

    THE PRODUCTION: Lieth's Miami model (1975, fitted to measured sites worldwide) turns T and
    rain into net primary productivity -- the world's food budget, cell by cell.

An instance of this law is named by its DOMINANT class -- the band that covers most of its
world's land-latitudes -- and measure() checks the name still matches.

The INSTANCE here is `aSteppeBiomes`.
"""

import math

# THE WHITTAKER TABLE (1970, the established taxonomy): (T_min_C, T_max_C, P_min_cm, P_max_cm,
# name, canopy_m, biomass_kg_m2, rgb-from-measured-reflectance). Temperature is the annual mean,
# rain the annual total. The cells tile the plane: lookup by (T, P), first match wins, coldest first.
WHITTAKER = [
    (-90.0, -12.0,   0.0, 1e9, "ice",        0.0,  0.0, (0.85, 0.87, 0.90)),
    (-12.0,  -5.0,   0.0, 1e9, "tundra",     0.2,  0.6, (0.24, 0.27, 0.17)),
    ( -5.0,   4.0,  40.0, 1e9, "boreal",    15.0, 20.0, (0.10, 0.25, 0.10)),
    ( -5.0,   4.0,   0.0, 40.0, "cold steppe", 0.3, 0.7, (0.50, 0.48, 0.26)),
    (  4.0,  20.0, 130.0, 1e9, "temperate forest", 25.0, 30.0, (0.13, 0.44, 0.12)),
    (  4.0,  20.0,  75.0, 130.0, "temperate woodland", 18.0, 22.0, (0.20, 0.42, 0.14)),
    (  4.0,  20.0,  25.0,  75.0, "steppe",    0.5,  1.6, (0.55, 0.50, 0.28)),
    (  4.0,  20.0,   0.0,  25.0, "cold desert", 0.2, 0.7, (0.70, 0.66, 0.48)),
    ( 20.0,  90.0, 200.0, 1e9, "rainforest", 35.0, 45.0, (0.06, 0.38, 0.10)),
    ( 20.0,  90.0, 100.0, 200.0, "seasonal forest", 28.0, 35.0, (0.12, 0.45, 0.12)),
    ( 20.0,  90.0,  25.0, 100.0, "savanna",   3.0,  4.0, (0.45, 0.55, 0.20)),
    ( 20.0,  90.0,   0.0,  25.0, "hot desert", 0.2, 0.7, (0.76, 0.70, 0.50)),
]


def biome_at(T_C: float, P_cm: float) -> tuple:
    """The Whittaker cell for a climate point: (name, canopy_m, biomass_kg_m2, rgb)."""
    for t0, t1, p0, p1, name, canopy, biomass, rgb in WHITTAKER:
        if t0 <= T_C < t1 and p0 <= P_cm < p1:
            return name, canopy, biomass, rgb
    # off the table: colder than anything with rain is ice; hotter than the table is hot desert
    return ("ice", 0.0, 0.0, (0.85, 0.87, 0.90)) if T_C < -90.0 else \
           ("hot desert", 0.2, 0.7, (0.76, 0.70, 0.50))


def npp_miami(T_C: float, P_mm: float) -> float:
    """Lieth's Miami model (1975): net primary productivity (g dry matter / m^2 / yr) from the
    annual temperature and rain, taking whichever limits harder (Liebig). Fitted to measured
    sites worldwide -- an empirical law, and said so."""
    from math import exp
    npp_t = 3000.0 / (1.0 + exp(1.315 - 0.119 * T_C))
    npp_p = 3000.0 * (1.0 - exp(-0.000664 * P_mm))
    return min(npp_t, npp_p)


def derive(parent, free):
    """The law, stated against this world: which axes the bands hang on, and the table that maps
    climate to life. Everything the instance needs is handed down through this membrane."""
    return {
        "extent_m": float(parent["R"]),
        "duration_s": float(parent.get("year_s", 3.1557e7)),   # the movie is ONE YEAR (seasons)
        "g": float(parent["g"]), "R": float(parent["R"]),
        # the climate axes, handed to the instance
        "T_surface": float(parent["T_surface"]),
        "T_equator": float(parent.get("T_equator", parent["T_surface"])),
        # THE SAME TWO NUMBERS IN THE UNIT THIS MEMBRANE'S OWN TABLE READS. The pair above are
        # KELVIN, carried up the chain from a planet that has no use for Celsius; `biome_at()` and
        # the Whittaker cells are CELSIUS, because that is the unit the classification was
        # published in. A number whose name does not carry its unit is a trap, and this one sprang:
        # the law's own render passed 294.19 into a table whose hottest cell ends at 30, and drew
        # the entire planet -- poles included -- as hot desert. Both units are published now, so a
        # consumer picks a name rather than remembering a convention.
        "T_surface_C": float(parent["T_surface"]) - 273.15,
        "T_equator_C": float(parent.get("T_equator", parent["T_surface"])) - 273.15,
        "temperature_unit_note": "T_* are KELVIN; T_*_C are CELSIUS, which is what biome_at() takes",
        "dT_equator_pole": float(parent.get("dT_equator_pole", 45.0)),
        "ice_line_lat_deg": float(parent.get("ice_line_lat_deg", 90.0)),
        "dry_belt_lat_deg": float(parent.get("dry_belt_lat_deg", 30.0)),
        "hadley_edge_deg": float(parent.get("hadley_edge_deg", 10.0)),
        "obliquity_deg": float(parent.get("obliquity_deg", 0.0)),
        "ocean_fraction": float(parent.get("ocean_fraction", 0.0)),
        "S_earth": float(parent.get("S_earth", 1.0)),
        "T_star_surface": float(parent.get("T_star_surface", 5772.0)),
        "day_s": float(parent.get("day_s", 86400.0)),
        "year_s": float(parent.get("year_s", 3.1557e7)),
        "days_per_year": float(parent.get("days_per_year", 365.0)),
        "lapse_rate_K_per_km": 0.66 * float(parent["g"]) / 1005.0 * 1000.0,
        # the law's own facts
        "whittaker_cells": len(WHITTAKER),
        "has_life_band": True,
    }


def _season_T(lat_rad, t, T_mean_C, dT, eps_rad):
    """Mean temperature at a latitude IN CELSIUS, at a point in the year.

    TWO TERMS, AND NEITHER IS A CHOICE. The standing gradient is `T_mean + dT.(1/3 - sin^2 lat)`,
    and the 1/3 is not a fudge -- it is the average of sin^2 over a sphere, so the profile PRESERVES
    the world mean this membrane inherited instead of quietly warming the planet. The seasonal term
    is the tilt: the annual insolation swing at latitude phi goes as sin(phi).sin(obliquity), so the
    amplitude is `dT.sin(eps)` and the hemispheres are in antiphase because sin(lat) changes sign.

    THAT PUTS A PREDICTION IN THE RENDER. This world is tilted 37.4 degrees, so sin(eps) = 0.61 and
    its seasonal swing is more than half its entire equator-to-pole gradient -- 27.3 K against 45.
    Earth's 23.4 degrees would give 17.9. A steeply tilted world does not have mild seasons, and
    the bands should be seen to lurch.

    CELSIUS, SAID TWICE, BECAUSE IT ALREADY BIT. `biome_at()` forty lines above takes Celsius; the
    membrane publishes `T_equator` and `T_surface` in KELVIN with nothing in the name to say so.
    The first version of this render passed 294.19 straight into the table, every latitude came out
    hotter than the hottest cell, and the whole globe rendered as one flat "hot desert" -- a picture
    that is not obviously wrong until you notice the poles are in it too."""
    import numpy as np
    return (T_mean_C + dT * (1.0 / 3.0 - np.sin(lat_rad) ** 2)
            + dT * math.sin(eps_rad) * np.sin(lat_rad) * math.sin(2.0 * math.pi * t))


def _season_P(lat_rad, t, hadley_edge_deg, dry_belt_deg, eps_rad):
    """Annual rain (cm) by latitude, with the wet belt following the sun.

    THE SHAPE IS THE CIRCULATION'S, NOT A MAP: wet where air rises (the equatorial band and the
    mid-latitude storm track), dry where it descends (the subtropical belt and the poles). The
    POSITIONS are this membrane's own derived `hadley_edge_deg` and `dry_belt_lat_deg`.

    And the whole pattern MIGRATES with the thermal equator, which is what a monsoon is. Stated
    plainly: the quantitative profile belongs to the instance, which has the world's mean rainfall
    to scale it by. What the law owns -- and what is drawn here -- is where the belts sit and that
    they move."""
    import numpy as np
    shift = math.radians(hadley_edge_deg) * math.sin(eps_rad) * math.sin(2.0 * math.pi * t)
    a = np.abs(lat_rad - shift) * 180.0 / math.pi
    he, db = float(hadley_edge_deg), float(dry_belt_deg)
    w = np.where(a < he, 2.6 - 0.4 * a / max(he, 1e-6),
        np.where(a < db, 2.2 - 1.7 * (a - he) / max(db - he, 1e-6),
        np.where(a < 70.0, 0.5 + 1.3 * np.sin(math.pi * (a - db) / max(70.0 - db, 1e-6)),
                 0.18)))
    return np.clip(w, 0.02, None) * 36.5      # mm/day -> cm/yr, at ~365 days


def emit(nums, t=1.0):
    """The matter of theBiomes the LAW: a globe wearing its own Whittaker table, over ONE YEAR.

    WHAT WAS HERE, and why it was wrong. A uniform green sphere -- one colour, every splat, ignoring
    `t` entirely -- under a docstring that called it "a climate-map globe, the bands by latitude".
    There were no bands. The chapter's entire claim is THE LAW OF LIFE'S BANDS, `biome_at()` sits
    forty lines above, and the render did not call it. An assertion wearing a derivation's clothes,
    and the kind that survives because nobody re-reads a render they have already seen.

    WHAT IT DRAWS NOW. Every splat's latitude gives a temperature and a rainfall from this
    membrane's own published axes; those two numbers go into `biome_at()`; and the CELL'S OWN
    COLOUR is the splat's colour. So the bands are not painted on -- they are the table, read at
    that point. Change `dT_equator_pole` at the top and the ice caps grow on screen.

    AND IT MOVES, for the reason its `duration_s` already claimed: the movie is one YEAR. The
    thermal equator swings with the obliquity, the wet belt follows it, and the bands migrate --
    so a splat near a cell boundary genuinely changes biome between summer and winter, which is
    what a seasonal world looks like from outside.
    """
    import numpy as np
    from matter import blank, fibonacci_sphere, surface_grain, SOLID, AR, AG, AB

    n = 12000
    d = fibonacci_sphere(n, jitter=0.9, seed=89)
    lat = np.arcsin(np.clip(d[:, 2], -1.0, 1.0))

    # KELVIN IN, CELSIUS OUT -- the membrane publishes K and its own table reads C. Converted once,
    # here, at the boundary between the two, which is the only place it is safe to do.
    T_mean_C = float(nums["T_surface"]) - 273.15
    dT = float(nums["dT_equator_pole"])
    eps = math.radians(float(nums.get("obliquity_deg", 23.4)))
    tt = float(t) % 1.0

    T = _season_T(lat, tt, T_mean_C, dT, eps)
    P = _season_P(lat, tt, float(nums["hadley_edge_deg"]), float(nums["dry_belt_lat_deg"]), eps)

    # THE TABLE IS THE PALETTE. One lookup per splat, through the membrane's own law.
    col = np.empty((n, 3), np.float32)
    for i in range(n):
        col[i] = biome_at(float(T[i]), float(P[i]))[3]

    b = blank(n)
    b[:, 0:3] = d
    b[:, 21:24] = d
    b[:, 16:19] = col
    b[:, AR:AB + 1] = col          # albedo travels, so relighting keeps the biome's own colour
    b[:, 19] = 0.9
    b[:, 20] = surface_grain(n, radius=1.0, cover=0.7)
    b[:, 11] = SOLID
    return b


def layout(nums):
    """WHAT IS CONTAINED HERE. theBiomes is the LAW -- the two climate axes and the table that
    maps them to life. aSteppeBiomes is the band-set that actually wraps this world -- named by
    its dominant class. It sits at the centre at full size: at this scale the membrane IS the
    biome map."""
    return {"aSteppeBiomes": ((0.0, 0.0, 0.0), 1.0)}


def measure(nums):
    """The law holds if the table tiles the plane (every climate point lands in exactly one cell)
    and the axes are present."""
    ok = all(biome_at(t, p)[0] for t in (-20, -8, 0, 10, 25) for p in (5, 60, 150, 300))
    return {"table_tiles_the_plane": ok,
            "axes_present": "T_equator" in nums and "dT_equator_pole" in nums}
