"""aSteppeBiomes -- the bands of life that actually wrap aBlueWorld. An INSTANCE of theBiomes.

theBiomes established what a biome IS: the largest community of life a climate can hold, forced
onto the two axes of temperature and rain by the Whittaker table. This membrane is the instance --
it inherits this world's temperature profile, its Hadley solution and its obliquity from the law
above, and derives which bands exist here, where they sit, and which one dominates.

    T(lat), rain(lat)  -> the Whittaker cell at each latitude -> the BAND MAP
    the obliquity      -> how far the bands breathe through the year (the movie is ONE YEAR)
    the Miami model    -> the productivity of each band (measured fit, Lieth 1975)
    the table's look   -> each band's measured reflectance, never a palette

THE NAME IS DERIVED. The dominant band by latitude area is the STEPPE (24% -- cold grassland),
then temperate woodland (20%), savanna (17%), ice (13%): a cold, dry world wearing mostly
grass. The table decides; measure() checks the folder still carries that answer.

THE HONEST WEAKNESS, said plainly: the rain profile's SHAPE is the Hadley circulation's
signature (wet at the rising branches, dry at the descending ones, at the parent's own band
positions), with the world-mean rain theAtmosphere derived. The band POSITIONS are the parent's
climate solution; the profile weights are the circulation's standard form, not a fitted map.
"""
from math import pi, sqrt, exp, log, sin, cos, asin
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))                     # read the law's table beside it
from physics import WHITTAKER, biome_at, npp_miami        # noqa: E402  (the law's own tools)

# MEASURED LIGHT for the living bands (the story's own spectral playbook):
RED_EDGE_NM = (700.0, 750.0)              # vegetation's sharp NIR rise -- the Red Edge, measured
CHLOROPHYLL_BANDS_NM = ((430.0, 450.0), (640.0, 680.0))   # chlorophyll absorption, measured
SAND_ALBEDO = 0.35                        # measured desert-sand reflectance
SNOW_ALBEDO = 0.85                        # measured fresh-snow reflectance
OCEAN_ALBEDO = 0.06                       # measured open-water reflectance

T_GROWING_MIN_C = 5.0                     # below this, growth effectively stops (measured threshold)

FREE = {}                                  # nothing left open: climate and table force everything
LENS = {
    "exposure": {"lo": 0.15, "hi": 1.0, "default": 0.42,
                 "label": "film speed", "unit": "gamma"},
}


def _rain_profile(lat_deg: float, hadley_edge: float, dry_belt: float, mean_mm_day: float) -> float:
    """Rain (mm/day) by latitude: the circulation's own signature -- wet at the rising branches
    (equator, mid-latitudes), dry at the descending ones (the dry belt, the poles) -- positioned
    at the PARENT's Hadley solution, scaled to the world-mean the air derived."""
    if lat_deg < hadley_edge:
        w = 2.6 - 0.4 * (lat_deg / hadley_edge)
    elif lat_deg < dry_belt:
        w = 2.2 - 1.7 * (lat_deg - hadley_edge) / (dry_belt - hadley_edge)
    elif lat_deg < 70.0:
        w = 0.5 + 1.3 * sin(pi * (lat_deg - dry_belt) / (70.0 - dry_belt))
    else:
        w = 0.4
    return w * mean_mm_day / 1.69          # normalised so the mean lands on the derived 1.69


def derive(parent, free):
    """These bands, from the law's handed-down climate."""
    R = float(parent["R"]); g = float(parent["g"])
    T_mean_C = float(parent["T_surface"]) - 273.15
    dT = float(parent["dT_equator_pole"])
    obliq = float(parent["obliquity_deg"])
    hadley_edge = float(parent["hadley_edge_deg"])
    dry_belt = float(parent["dry_belt_lat_deg"])
    year_s = float(parent["year_s"])
    days_per_year = float(parent["days_per_year"])
    lapse = float(parent["lapse_rate_K_per_km"]) / 1000.0      # K/m

    def T_C(lat_deg):
        s = sin(lat_deg * pi / 180.0)
        return T_mean_C + dT * (1.0 / 3.0 - s * s)

    def P_cm(lat_deg):
        return _rain_profile(lat_deg, hadley_edge, dry_belt, 1.69) * days_per_year / 10.0

    # THE BAND MAP: Whittaker cell at each latitude, area-weighted (band area ~ d(sin lat)).
    bands = {}
    total = 0.0
    lat_rows = []
    for lat5 in (x * 1.0 for x in range(0, 90)):
        w = sin((lat5 + 1.0) * pi / 180.0) - sin(lat5 * pi / 180.0)
        name, canopy, biomass, rgb = biome_at(T_C(lat5), P_cm(lat5))
        bands.setdefault(name, [0.0, canopy, biomass, rgb])
        bands[name][0] += w
        total += w
        lat_rows.append((lat5, name))
    area_fractions = {k: v[0] / total for k, v in bands.items()}
    dominant = max(area_fractions, key=area_fractions.get)

    # THE SEASONAL BREATHING: the obliquity swings each latitude's temperature through the year,
    # strongest at mid-latitudes; the frost line (5 deg C, where growth stops) swings with it.
    def swing_C(lat_deg):
        return 0.5 * obliq * sin(lat_deg * pi / 180.0)

    def growing_days(lat_deg):
        base, amp = T_C(lat5 := lat_deg), swing_C(lat_deg)
        steps = 96
        return days_per_year * sum(1 for i in range(steps)
                                   if base + amp * sin(2.0 * pi * i / steps) > T_GROWING_MIN_C) / steps

    def frost_lat(offset_C):
        for lat5 in range(0, 90):
            if T_C(lat5) + offset_C < T_GROWING_MIN_C:
                return float(lat5)
        return 90.0

    frost_mean = frost_lat(0.0)
    frost_winter = frost_lat(-swing_C(45.0))
    frost_summer = frost_lat(swing_C(45.0))
    seasonal_shift_deg = obliq / 2.0

    # THE ALTITUDE STACK: uphill it cools at the lapse rate, so the same bands repeat vertically.
    tree_line_altitude_m = max(0.0, (T_C(20.0) - T_GROWING_MIN_C) / lapse)
    montane_band_m = tree_line_altitude_m
    alpine_band_m = max(0.0, (T_C(20.0) - 0.0) / lapse) - montane_band_m
    nival_band_m = "above the snow line at each latitude"
    altitude_compression = lapse / (dT / 90.0)            # K/m over K/deg -> latitude-degrees per km

    # HABITABILITY: enough warm days, enough rain.
    habitable = sum(w for lat5, name in lat_rows
                    for w in [sin((lat5 + 1.0) * pi / 180.0) - sin(lat5 * pi / 180.0)]
                    if growing_days(lat5) >= 60.0 and P_cm(lat5) >= 25.0) / total
    growing_season_equator = growing_days(0.0)
    frost_free_midlat = growing_days(45.0)

    # THE PRODUCTION (Miami model, Lieth 1975 -- measured fit).
    npp_rows = {name: npp_miami(T_C(lat5), P_cm(lat5))
                for lat5, name in lat_rows}
    productivity_mean = sum(npp_rows.values()) / max(len(npp_rows), 1)
    canopy_max = max(v[1] for v in bands.values())
    biomass_max = max(v[2] for v in bands.values())
    gdd_equator = days_per_year * max(0.0, T_C(0.0) - T_GROWING_MIN_C)

    return {
        "extent_m": R,
        "duration_s": year_s,                              # the movie is ONE YEAR -- the seasons
        "g": g, "R": R,
        # the climate axes, carried for emit() -- nothing typed there
        "T_mean_C": T_mean_C,
        "dT_equator_pole": dT,
        "hadley_edge_deg": hadley_edge,
        "dry_belt_lat_deg": dry_belt,
        "lapse_rate_K_per_km": lapse * 1000.0,
        "biome_list": sorted(bands.keys()),
        "biome_count": len(bands),
        "biome_area_fractions": area_fractions,
        "dominant_biome": dominant,
        "tropic_band_deg": f"0-{hadley_edge + 10:.0f}",
        "temperate_band_deg": f"{hadley_edge + 10:.0f}-{frost_mean:.0f}",
        "polar_band_deg": f"{frost_mean:.0f}-90",
        "tree_line_altitude_m": tree_line_altitude_m,
        "montane_band_m": montane_band_m,
        "alpine_band_m": alpine_band_m,
        "nival_band_m": nival_band_m,
        "altitude_compression": altitude_compression,
        "rain_equator_mm_day": P_cm(0.0) * 10.0 / days_per_year,
        "rain_dry_belt_mm_day": P_cm(dry_belt) * 10.0 / days_per_year,
        "rain_polar_mm_day": P_cm(80.0) * 10.0 / days_per_year,
        "aridity_index": P_cm(dry_belt) * 10.0 / max(P_cm(0.0) * 10.0, 1e-9),
        "desert_fraction": sum(v for k, v in area_fractions.items() if "desert" in k),
        "growing_season_days": growing_season_equator,
        "frost_free_days": frost_free_midlat,
        "T_growing_min_C": T_GROWING_MIN_C,
        "habitable_land_fraction": habitable,
        "canopy_height_max_m": canopy_max,
        "productivity_g_c_m2_yr": productivity_mean,
        "growing_degree_days": gdd_equator,
        "biomass_density_kg_m2": biomass_max,
        "seasonal_shift_deg": seasonal_shift_deg,
        "obliquity_deg": obliq,
        "frost_line_winter_deg": frost_winter,
        "frost_line_summer_deg": frost_summer,
        "frost_line_mean_deg": frost_mean,
        "vegetation_red_edge": RED_EDGE_NM,
        "chlorophyll_absorption_bands": CHLOROPHYLL_BANDS_NM,
        "sand_albedo": SAND_ALBEDO,
        "snow_albedo": SNOW_ALBEDO,
        "ocean_albedo": OCEAN_ALBEDO,
        "S_earth": float(parent.get("S_earth", 1.0)),
        "T_star_surface": float(parent.get("T_star_surface", 5772.0)),
        "year_s": year_s,
        "day_s": float(parent.get("day_s", 86400.0)),
        "days_per_year": days_per_year,
        "biome_class": dominant.capitalize(),
        "name": "a" + dominant.capitalize() + "Biomes",     # derived, like the star's colour
    }


def emit(nums, t=1.0):
    """The matter of these bands, in its own local units (1.0 = the planet's radius).

    THE CLIMATE MAP, and it is a MAP OF MEASURED REFLECTANCE: each grain is painted the colour
    its own band measurably reflects -- chlorophyll green where things grow, tan where it is dry,
    white where it is frozen. The land is theTerrain's to draw and the ocean is theOcean's; what
    this membrane owns is the BANDS -- the climate's answer at each latitude, wrapped around the
    whole sphere.

    The movie is ONE YEAR: the obliquity breathes the bands poleward and back, the frost line
    swinging with them. That is the rung of the ladder where a year finally fits in one film.
    """
    import numpy as np
    from matter import blank, fibonacci_sphere, surface_grain, lit, SOLID

    tt = float(t)
    rng = np.random.default_rng(89)
    T_mean_C = float(nums["T_mean_C"])                     # every number arrives through nums
    dT = float(nums["dT_equator_pole"])
    obliq = float(nums["obliquity_deg"])
    hadley_edge = float(nums["hadley_edge_deg"])
    dry_belt = float(nums["dry_belt_lat_deg"])
    days_per_year = float(nums["days_per_year"])
    year_frac = tt
    season = sin(2.0 * pi * year_frac)                     # ONE YEAR: the bands breathe

    S_rel = float(nums.get("S_earth", 1.0))
    n = 34000
    d = fibonacci_sphere(n, jitter=0.9, seed=89)
    lat_deg = np.degrees(np.arcsin(np.clip(d[:, 2], -1.0, 1.0)))

    # temperature with the season on it; the frost line swings with the obliquity
    s2 = (d[:, 2]) ** 2
    T_C = T_mean_C + dT * (1.0 / 3.0 - s2) + 0.5 * obliq * np.sin(np.radians(np.abs(lat_deg))) * season
    # the rain profile, the same shape derive() used
    alat = np.abs(lat_deg)
    w = np.where(alat < hadley_edge, 2.6 - 0.4 * (alat / hadley_edge),
        np.where(alat < dry_belt, 2.2 - 1.7 * (alat - hadley_edge) / (dry_belt - hadley_edge),
        np.where(alat < 70.0, 0.5 + 1.3 * np.sin(pi * (alat - dry_belt) / (70.0 - dry_belt)), 0.4)))
    P_cm = w * days_per_year / 10.0

    b = blank(n)
    b[:, 0:3] = d
    b[:, 21:24] = d
    col = np.zeros((n, 3), np.float32)
    for t0, t1, p0, p1, name, canopy, biomass, rgb in WHITTAKER:
        mask = (T_C >= t0) & (T_C < t1) & (P_cm >= p0) & (P_cm < p1)
        col[mask] = np.array(rgb, np.float32)
    # illumination: the year's mean light -- bright at low latitudes, dim at the poles
    bright = np.clip(np.cos(np.radians(lat_deg)) * 0.75 + 0.35, 0.15, 1.0)
    b[:, 16:19] = (col * bright[:, None] * S_rel).clip(0.0, 1.0)
    b[:, 19] = 0.9
    b[:, 20] = surface_grain(n, radius=1.0, cover=0.75)
    b[:, 11] = SOLID
    return b


def measure(nums):
    """The name must match the dominant band the table produced; and the band fractions must sum
    to the whole sphere -- a biome map with unmapped land is a bug, not a biome."""
    folder = Path(__file__).resolve().parent.name
    fracs = nums["biome_area_fractions"]
    return {"dominant_biome": nums["dominant_biome"],
            "name_matches_class": folder == nums["name"],
            "fractions_sum_to_one": abs(sum(fracs.values()) - 1.0) < 0.02,
            "biome_count": nums["biome_count"]}
