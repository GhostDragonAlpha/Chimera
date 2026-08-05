"""theGarden -- THE LUSH PLACE, derived: where the world's physics makes the most life.

The biomes law told the world WHAT can grow where: the Whittaker cells a climate can hold.
This membrane asks the next question -- WHERE does the most life actually CASCADE OUT of the
climate? -- and answers it with the production field, not with a palette.

    THE GARDEN IS THE ARGMAX. Give a world its temperature and rain, feed them to the Miami
    model (Lieth 1975, the same measured fit the biomes law owns), and the answer to "where
    is the lush place" is not a choice: it is the latitude with the largest net primary
    productivity. On this world that latitude is the EQUATOR -- the warmest AND the wettest
    band, which is the rare coincidence of both axes peaking together.

    THE LUSH IS NOT PAINTED GREEN. The band's own Whittaker cell -- read from the biomes law
    by PATH, never re-typed -- is a SAVANNA: 21 deg C and 99.8 cm of rain are below the
    rainforest's 100 cm floor, so this world's "lush place" is a wet savanna-woodland, not a
    jungle. The green in the render is the cell's measured reflectance multiplied by how
    close the local production is to the peak. Where life cascades, the matter glows; where
    nothing can grow, it goes dark. That is the difference between a map and a verdict.

RULE 0, THE THEORY THIS MEMBRANE IS (stated before the run):

  STATEMENT   The lush place on a world is FORCED, not chosen: it is the argmax of net
              primary productivity over the climate profile, NPP(lat) = min(NPP_T, NPP_P)
              (Miami, Liebig). Its temperature and rain ARE the parent's published climate
              read at that latitude, and its band's cell comes from the biomes law.
  PREDICTION  (i) lush_lat_deg == 0.0 -- the equator, because T and P both peak there;
              (ii) the garden's published rain_rate_mm_day closes to aNitrogenAtmosphere's
              published rain rate to 1e-9 (one law, applied from the parent's own numbers);
              (iii) the garden's Whittaker cell is SAVANNA (99.8 cm < the rainforest's 100 cm
              floor); (iv) NPP_max is ~1.86x the world area-mean production -- the "lush"
              as a number, and the belt holding 90% of the peak spans about +-11 degrees
              (~2,018 km full width).
  FALSIFIER   Any of (i)-(iv) fails on a fresh grow, or the emit's green band is NOT at the
              peak of its own published production field (the render lies about the law).
"""

import math
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent


def _biomes_law():
    """Load THE LAW from the sibling folder by EXPLICIT PATH -- the folding rule: a membrane
    never re-types a law a sibling already owns (the Whittaker table and the Miami model are
    theBiomes'; this membrane is a READER of them, like aSteppeBiomes is)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("law_biomes_garden", _HERE.parent / "theBiomes" / "physics.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_LAW = _biomes_law()
WHITTAKER = _LAW.WHITTAKER
biome_at = _LAW.biome_at
npp_miami = _LAW.npp_miami

# THE ONE SUN at the garden's latitude, for a place scene: the garden sits on the equator, so
# its light is the world's single star seen from latitude 0 at the shared opening hour.
GARDEN_LAT_DEG = 0.0

N_GRAINS = 30000


def _rain_mm_day(mean_mm_day: float, lat_deg: float, hadley: float, dry: float) -> float:
    """The Hadley rain profile, positioned at the PARENT's own band edges and scaled to the
    world mean. The SHAPE is the circulation's (aSteppeBiomes' `_rain_profile`, the same law);
    the MEAN here is aNitrogenAtmosphere's own derived rain rate, so the garden's rain closes
    to the air's number rather than to a rounded copy of it."""
    a = abs(float(lat_deg))
    if a < hadley:
        w = 2.6 - 0.4 * (a / max(hadley, 1e-6))
    elif a < dry:
        w = 2.2 - 1.7 * (a - hadley) / max(dry - hadley, 1e-6)
    elif a < 70.0:
        w = 0.5 + 1.3 * math.sin(math.pi * (a - dry) / max(70.0 - dry, 1e-6))
    else:
        w = 0.4
    return w * float(mean_mm_day) / 1.69      # mean of the w shape is 1.69; rescale onto the air's mean


def derive(parent, free):
    """The garden, from the world's own climate -- no free numbers."""
    R = float(parent["extent_m"]); g = float(parent["g"])
    T_mean_C = float(parent["T_surface"]) - 273.15
    dT = float(parent["dT_equator_pole"])
    obliq = float(parent.get("obliquity_deg", 0.0))
    hadley = float(parent["hadley_edge_deg"])
    dry = float(parent["dry_belt_lat_deg"])
    dpy = float(parent["days_per_year"])
    year_s = float(parent["year_s"])
    ocean = float(parent["ocean_fraction"])
    T_surf = float(parent["T_surface"])

    # THE RAIN LAW, APPLIED FROM THE PARENT'S OWN NUMBERS (aNitrogenAtmosphere's law: Earth's
    # mean 2.74 mm/day dialled by temperature through Clausius-Clapeyron's ~7%/K and by the
    # world's ocean fraction). Applied here independently, it must close to the atmosphere's
    # published number -- the garden cannot read aNitrogenAtmosphere's numbers.json (it is not
    # an ancestor), so this is one law reached twice, and T14 checks the two meet.
    rain_mean_mm_day = 2.74 * (2.0 ** ((T_surf - 288.15) / 14.0)) * ocean / 0.71

    def T_C(lat_deg):
        s = math.sin(lat_deg * math.pi / 180.0)
        return T_mean_C + dT * (1.0 / 3.0 - s * s)     # the parent's published profile (mean preserved)

    def P_mm_yr(lat_deg):
        return _rain_mm_day(rain_mean_mm_day, lat_deg, hadley, dry) * dpy

    def npp(lat_deg):
        return npp_miami(T_C(lat_deg), P_mm_yr(lat_deg))

    # THE ARGMAX, INTEGRATED OVER LATITUDE AREA (d(sin lat)), like aSteppeBiomes' band map.
    npp_rows = []
    total = 0.0
    for lat5 in range(0, 90):
        wgt = math.sin((lat5 + 1) * math.pi / 180.0) - math.sin(lat5 * math.pi / 180.0)
        npp_rows.append((lat5, npp(lat5), wgt))
        total += wgt
    npp_max = max(n for _, n, _ in npp_rows)
    world_mean = sum(n * w for _, n, w in npp_rows) / total
    lush_lat = max(npp_rows, key=lambda r: r[1])[0]
    factor = npp_max / max(world_mean, 1e-9)

    # THE BELT: how wide the "lush" is. 90% of the peak is the garden's own core; 50% is its
    # whole reach. Width in km = 2 * arc length of the latitude span, on the parent's radius.
    def belt(frac):
        lo = next((lat5 for lat5, n, _ in npp_rows if n >= frac * npp_max), 90)
        hi = next((lat5 for lat5, n, _ in reversed(npp_rows) if n >= frac * npp_max), 0)
        # The band straddles the equator (NPP is symmetric in |lat| and peaks at 0), so the full
        # width is BOTH arcs and the half-span in degrees is simply hi - lo.
        return 2.0 * R * math.radians(hi - lo) / 1000.0, float(hi - lo)
    belt_90_km, belt_90_span_deg = belt(0.9)
    belt_50_km, _ = belt(0.5)

    # THE GARDEN'S OWN CLIMATE AND CELL (read from the biomes law, never re-typed).
    T_garden_C = T_C(lush_lat)
    P_garden_mm = P_mm_yr(lush_lat)
    cell_name, canopy_m, biomass_kg_m2, cell_rgb = biome_at(T_garden_C, P_garden_mm / 10.0)

    # THE ONE SUN at the garden (the T12 pattern: publish the altitude the law gives at the
    # garden's own latitude and opening hour, so a reader can check the light it baked).
    import matter as M
    sun_alt = M.sun_altitude_deg(1.0, obliq, GARDEN_LAT_DEG, M.SUN_OPEN_HOUR)
    sun_decl = math.degrees(M.sun_declination(1.0, obliq))

    return {
        "extent_m": R,                              # the whole-world production field is the scene
        "duration_s": year_s,                       # the movie is ONE YEAR: the light seasons
        "g": g,
        "lush_lat_deg": float(lush_lat),
        "T_garden_C": T_garden_C,
        "P_garden_mm_yr": P_garden_mm,
        "P_garden_cm": P_garden_mm / 10.0,
        "rain_rate_mm_day": rain_mean_mm_day,
        "garden_biome": cell_name,
        "garden_canopy_m": canopy_m,
        "garden_biomass_kg_m2": biomass_kg_m2,
        "garden_rgb": list(cell_rgb),
        "npp_max_g_m2_yr": npp_max,
        "npp_world_mean_g_m2_yr": world_mean,
        "npp_garden_over_world": factor,
        "lush_belt_90pct_full_width_km": belt_90_km,
        "lush_belt_50pct_full_width_km": belt_50_km,
        "lush_belt_90pct_half_lat_deg": belt_90_span_deg,
        "T_mean_C": T_mean_C,                  # the world's climate, handed to the emit (the profile base)
        "dT_equator_pole": dT,
        "hadley_edge_deg": hadley,
        "dry_belt_lat_deg": dry,
        "growing_season_days": dpy,                  # equator: no seasonal swing, grows all year
        "latitude_deg": GARDEN_LAT_DEG,
        "obliquity_deg": obliq,
        "obliquity_effective_deg": float(parent.get("obliquity_effective_deg", obliq)),
        "sun_altitude_at_garden_deg": sun_alt,
        "sun_declination_deg": sun_decl,
        "S_earth": float(parent.get("S_earth", 1.0)),
        "day_s": float(parent.get("day_s", 86400.0)),
        "days_per_year": dpy,
        "year_s": year_s,
        "n_grains": N_GRAINS,
        "name": "theGarden",
    }


def emit(nums, t=1.0):
    """The world's production field, lit by the ONE SUN from the garden's own latitude.

    WHAT IT DRAWS, and why it is not a second biome map. aSteppeBiomes paints the Whittaker
    CELLS -- the taxonomy, flat per band. This membrane paints the MIAMI NUMBER -- how much
    life each latitude actually makes -- as the brightness of the cell's measured reflectance.
    The garden band is the place where the field is near its peak, so it GLOWS; the ice caps
    and the dry belts sit in it dark. You cannot paint that: it is the production field read
    at every point, and the render is the falsifier for the whole law.

    THE LIGHT IS THE WORLD'S STAR. The sun direction is matter.local_sun at this membrane's
    own latitude (the equator) at the shared opening hour -- the same one T12 proved the human
    chain reads -- and sun_direction() below declares it so the viewer arms the renderer with
    exactly what the emit baked. The movie is one year: the declination swings the terminator
    while the production field (an ANNUAL number, Miami) stays put -- the garden's green is
    stable, its light is not, and that is the honest pair.
    """
    import numpy as np
    import matter as M
    from matter import blank, fibonacci_sphere, surface_grain, lit, SOLID

    tt = float(t)
    T_mean_C = float(nums["T_mean_C"])
    dT = float(nums["dT_equator_pole"])
    hadley = float(nums["hadley_edge_deg"])
    dry = float(nums["dry_belt_lat_deg"])
    dpy = float(nums["days_per_year"])
    obliq = float(nums["obliquity_deg"])
    npp_max = float(nums["npp_max_g_m2_yr"])
    rain_mean = float(nums["rain_rate_mm_day"])
    S_rel = float(nums.get("S_earth", 1.0))

    n = int(nums.get("n_grains", N_GRAINS))
    d = fibonacci_sphere(n, jitter=0.9, seed=71)
    lat = np.degrees(np.arcsin(np.clip(d[:, 2], -1.0, 1.0)))

    # THE PRODUCTION FIELD -- vectorised Miami over the profile, exactly as derive() sampled it.
    s2 = (d[:, 2]) ** 2
    T = T_mean_C + dT * (1.0 / 3.0 - s2)
    alat = np.abs(lat)
    w = np.where(alat < hadley, 2.6 - 0.4 * (alat / max(hadley, 1e-6)),
        np.where(alat < dry, 2.2 - 1.7 * (alat - hadley) / max(dry - hadley, 1e-6),
        np.where(alat < 70.0, 0.5 + 1.3 * np.sin(np.pi * (alat - dry) / max(70.0 - dry, 1e-6)),
                 0.4)))
    P_mm = w * (rain_mean / 1.69) * dpy        # the same field derive sampled: shape x the air's own mean
    npp_t = 3000.0 / (1.0 + np.exp(1.315 - 0.119 * T))
    npp_p = 3000.0 * (1.0 - np.exp(-0.000664 * P_mm))
    prod = np.minimum(npp_t, npp_p) / max(npp_max, 1e-9)          # 1 at the garden, ~0 at the poles

    # THE CELL'S MEASURED REFLECTANCE at each point (the biomes law's table, read -- never a palette).
    col = np.empty((n, 3), np.float32)
    for t0, t1, p0, p1, name, canopy, biomass, rgb in WHITTAKER:
        mask = (T >= t0) & (T < t1) & (P_mm / 10.0 >= p0) & (P_mm / 10.0 < p1)
        col[mask] = np.array(rgb, np.float32)

    # THE FIELD AS LIGHT: near the peak the cell's own colour glows; away from it the world dims.
    bright = 0.18 + 0.82 * np.clip(prod, 0.0, 1.0)
    albedo = (col * bright[:, None]).clip(0.0, 1.0)

    # THE ONE SUN at the garden's latitude -- baked, and declared below for the viewer.
    sun = M.local_sun(tt, obliq, GARDEN_LAT_DEG, M.SUN_OPEN_HOUR)
    lam = np.clip(d @ sun, 0.0, None)                              # each grain's own terminator
    irr = S_rel * lam + 0.03                                       # a floor: night is not zero

    b = blank(n)
    b[:, 0:3] = d
    b[:, 21:24] = d                                                # normals: day/night reads solid
    b[:, 16:19] = lit(albedo, irr, e_ref=S_rel, tone=0.45)
    b[:, 19] = 0.9
    b[:, 20] = surface_grain(n, radius=1.0, cover=0.75)
    b[:, 11] = SOLID
    return b


def measure(nums):
    """The law holds if the garden is the argmax and the world-mean production closes."""
    return {
        "lush_lat_deg": nums["lush_lat_deg"],
        "garden_biome": nums["garden_biome"],
        "npp_max_g_m2_yr": nums["npp_max_g_m2_yr"],
        "npp_garden_over_world": nums["npp_garden_over_world"],
        "is_argmax": nums["lush_lat_deg"] == 0.0,
        "closes_to_the_air": abs(nums["rain_rate_mm_day"] - 1.6934643871492006) < 1e-9,
    }


def sun_direction(tt, nums):
    """THE ONE SUN at the garden's own latitude (the equator), the shared opening hour --
    read from matter.py, declared so the viewer arms exactly the light the emit baked."""
    import matter
    return matter.local_sun(float(tt), float(nums["obliquity_effective_deg"]),
                            float(nums["latitude_deg"]), matter.SUN_OPEN_HOUR)
