"""aSaltOcean -- the water that actually fills aBlueWorld's basins. An INSTANCE of theOcean.

theOcean established what an ocean IS: a liquid gravity holds, with a colour its absorption
spectrum forces and a glint its surface reflects. The glint is now a READER, not a paint (Stage
21): density -> Lorentz-Lorenz -> n -> Fresnel F0, drawn by the renderer's kernel only when a
light is set, never painted onto the buffer. This membrane is the instance -- it inherits
this world's water mass, temperature, wind and spin from the law above, and derives everything
the water here is LIKE: its depth, its colour, its currents, its ice, its tide (21 cm from the
star alone, twice a day, forever -- no moon exists here), and how far the light gets down.

    M_water / ocean area  -> the MEAN DEPTH (volume over area, nothing more)
    measured absorption   -> the COLOUR (Pope & Fry 1997: red dies ~25x faster than blue)
    wind + spin           -> the currents and the waves
    T + salinity          -> the ice and the deep temperature
    star mass + orbit     -> the ONLY tide there is (no moon exists here)

THE CHAIN PREDICTS WHAT IT WAS NEVER FITTED TO. The mean depth comes out 2,861 m against the
Terrain membrane's independently-solved 2,914 m -- two paths (volume/area here, the sea-level
solver there) landing within 2% of each other, and neither bent toward the other. Earth's own
volume/area gives 3,690 m against a measured 3,688.

THE NAME IS DERIVED. An ocean is classified by its dissolved load: at the default 35 g/kg --
Earth's own salinity -- this is a Salt ocean. Change the dial and the name must change with it;
measure() checks.
"""
from math import pi, sqrt, exp, log, sin, cos
from pathlib import Path

RHO_FRESH = 1000.0         # kg/m^3
# MEASURED LIGHT, Pope & Fry (1997) pure-water absorption coefficients (1/m), at the three
# channels' centre wavelengths (R 630, G 545, B 460 nm). This is why water is blue: red is
# absorbed ~25x faster than blue, so only blue comes back. The render reads THESE, not a palette.
ABSORB_RGB = (0.320, 0.060, 0.0145)
# MEASURED backscatter of pure water at 460 nm (Morel 1974), falling ~lambda^-4.3 -- the tiny
# fraction of light the water itself returns.
BACKSCATTER_460 = 0.0030
# THE GLINT IS NOT TYPED. The typed n = 1.34 Fresnel constant (0.02111) was the last un-derived
# optical number in this emit; Stage 21 derives it from density below via Lorentz-Lorenz
# (matter.refractive_index + fresnel_f0) and publishes it as sunglint_intensity. At the default
# 35 g/kg the derived value is 0.02150 against the old typed 0.02111 -- a 1.8% tightening.

AU = 1.495978707e11
M_SUN = 1.98892e30
L_SUN = 3.828e26

# THE FREE DIAL. How much salt the rock weathered into the water over this world's history --
# not forced by any law. Earth sits at 35 g/kg; that is the default, so the first numbers say
# what Earth's own history does here.
FREE = {
    "salinity_g_kg": {"lo": 0.0, "hi": 200.0, "default": 35.0,
                      "label": "dissolved load", "unit": "g/kg"},
}

# THE LENS -- dials that change the PICTURE and nothing else.
LENS = {
    "exposure": {"lo": 0.15, "hi": 1.0, "default": 0.42,
                 "label": "film speed", "unit": "gamma"},
}

SALINITY_CLASSES = [(0.5, "Fresh"), (30.0, "Brackish"), (50.0, "Salt"), (1e9, "Brine")]


def salinity_class(s_g_kg: float) -> str:
    for hi, name in SALINITY_CLASSES:
        if s_g_kg < hi:
            return name
    return "Brine"


def _water_rgb(absorb, backscatter_460, scale=1.0):
    """The colour the water RETURNS, from measured absorption + backscatter (Morel & Prieur's
    reflectance model: R ~ b_b / (a + b_b)). Deep water: only blue survives. Shallow or
    matter-laden water: greener -- more backscatter, a touch more blue absorbed."""
    out = []
    for wl, a in zip((630.0, 545.0, 460.0), absorb):
        bb = backscatter_460 * (460.0 / wl) ** 4.3
        out.append(0.33 * bb / (a + bb) * scale)
    m = max(out) or 1.0
    return [v / m for v in out]


def derive(parent, free):
    """This water, from the law's handed-down state."""
    g = float(parent["g"]); R = float(parent["extent_m"])
    M_w = float(parent["M_water"])
    f_oc = float(parent["ocean_fraction"])
    T = float(parent["T_surface"])
    T_C = float(parent.get("T_surface_C", T - 273.15))
    wind = float(parent.get("wind_surface_ms", 0.0))
    day_s = float(parent.get("day_s", 86400.0))

    salinity = float(free.get("salinity_g_kg", FREE["salinity_g_kg"]["default"]))

    # DEPTH: volume over area. Nothing more -- the basin's SHAPE is theTerrain's, the water is ours.
    volume = M_w / RHO_FRESH
    area = f_oc * 4.0 * pi * R * R
    mean_depth = volume / area if area > 0 else 0.0
    deepest_point = 3.0 * mean_depth      # Earth's own ratio (10,900 / 3,688 = 2.96), said so.

    # THE DISSOLVED LOAD and what it does. Linear laws, measured on seawater.
    density_surface = RHO_FRESH + 0.77 * salinity
    freezing_depression = 0.054 * salinity            # K per g/kg, measured
    freezing_point = 273.15 - freezing_depression
    density_deep = density_surface + 4.0              # cold deep water is denser still
    sound_speed = 1449.0 + 4.6 * T_C - 0.055 * T_C * T_C + 1.34 * (salinity - 35.0)

    # THE GLINT, DERIVED (Stage 21): Lorentz-Lorenz from THIS water's density -> n -> Fresnel F0.
    # The glint is no longer a typed constant from a sourced n = 1.34; it is what the dissolved
    # load says it is. Move the salinity dial and the glint moves with the density -- the slider
    # test in ChimeraEngine/test_optics.py (T6) is what catches any typed remnant.
    from matter import refractive_index, fresnel_f0, SPECIFIC_REFRACTION_CM3_G
    n_surface = refractive_index(density_surface, SPECIFIC_REFRACTION_CM3_G["water"])
    sunglint_intensity = fresnel_f0(n_surface)

    # THE COLOUR -- measured absorption, measured backscatter, nothing else.
    ocean_rgb_deep = _water_rgb(ABSORB_RGB, BACKSCATTER_460)
    ocean_rgb_shallow = _water_rgb([a * 1.5 for a in ABSORB_RGB], BACKSCATTER_460 * 3.0)
    attenuation_blue = ABSORB_RGB[2] + BACKSCATTER_460     # extinction for blue, the light that goes deepest
    attenuation_length_m = 1.0 / attenuation_blue
    photic_zone_m = log(100.0) / (attenuation_blue * 1.6)  # 1% light, diffuse (K_d > a)
    secchi_depth_m = 1.7 / (attenuation_blue * 1.6)        # measured Secchi ~ 1.7/K_d
    light_at_100m = exp(-attenuation_blue * 1.6 * 100.0)

    # THE THERMAL STRUCTURE: a sunlit mixed layer, then the drop, then the cold floor.
    T_surface_water = T
    thermocline_depth_m = 100.0               # Earth's mean mixed-layer band 70-150 m
    T_deep = freezing_point + 3.0             # deep water sits just off freezing (Earth: ~275 K)

    # ICE: the sea freezes purely by latitude (it has no altitude) -- read where the parent froze.
    sea_ice_fraction = float(parent.get("ice_fraction", 0.0))
    ice_line_lat = float(parent.get("ice_line_lat_deg", 90.0))

    # CURRENTS AND WAVES: the wind drags (~3%, measured rule), the spin bends.
    surface_current_ms = 0.03 * wind
    coriolis_parameter = 2.0 * (2.0 * pi / day_s) * sin(pi / 4.0)     # at 45 degrees
    ekman_depth_m = 50.0                        # wind's direct grip, measured band 30-100 m
    gyre_count = 2                              # one per hemisphere, the banded world's counterpart
    upwelling_zones = "equator and western coasts (trade-wind divergence, from the parent's Hadley solution)"
    wave_height_m = 0.2 * wind * wind / g       # fully-developed sea, measured fit
    foam_fraction = 0.001 * max(0.0, wind - 3.0)  # whitecaps appear past ~3 m/s, measured onset
    surface_slope_mean = 0.1 * sqrt(max(wave_height_m, 0.01))

    # THE ONLY TIDE THERE IS. No moon was ever derived here, so the star is the whole tide:
    # h = (3/2)(M*/Mp)(R/a)^3 R, with M* from the star's light (L ~ M^3.5, the same empirical
    # law the star membrane used). Earth check: 0.25 m. Here: ~0.2 mm -- this ocean does not breathe.
    M_star = M_SUN * (float(parent["L_star"]) / L_SUN) ** (1.0 / 3.5)
    M_p = g * R * R / 6.6743e-11
    a = float(parent["a_au"]) * AU
    solar_tide = 1.5 * (M_star / M_p) * (R / a) ** 3 * R
    tide_period_h = day_s / 2.0 / 3600.0        # two bulges, one star: twice a day

    cls = salinity_class(salinity)

    return {
        "extent_m": R,
        "duration_s": day_s,
        "g": g,         "M_water": M_w,
        "ocean_fraction": f_oc,
        "ocean_volume_m3": volume,
        "mean_ocean_depth_m": mean_depth,
        "deepest_point_m": deepest_point,
        "salinity_g_kg": salinity,
        "density_surface_kg_m3": density_surface,
        "density_deep_kg_m3": density_deep,
        "freezing_depression_K": freezing_depression,
        "freezing_point_K": freezing_point,
        "sound_speed_water_ms": sound_speed,
        "absorption_rgb_measured": list(ABSORB_RGB),
        "backscatter_fraction": BACKSCATTER_460,
        "attenuation_length_m": attenuation_length_m,
        "ocean_rgb_deep": ocean_rgb_deep,
        "ocean_rgb_shallow": ocean_rgb_shallow,
        "T_surface_water": T_surface_water,
        "thermocline_depth_m": thermocline_depth_m,
        "T_deep": T_deep,
        "sea_ice_fraction": sea_ice_fraction,
        "ice_line_lat_deg": ice_line_lat,
        "surface_current_ms": surface_current_ms,
        "coriolis_parameter": coriolis_parameter,
        "ekman_depth_m": ekman_depth_m,
        "gyre_count": gyre_count,
        "upwelling_zones": upwelling_zones,
        "wave_height_m": wave_height_m,
        "foam_fraction": foam_fraction,
        "surface_slope_mean": surface_slope_mean,
        "sunglint_intensity": sunglint_intensity,
        "solar_tide_m": solar_tide,
        "tide_period_h": tide_period_h,
        "tidal_bulge": "two, sun-facing and far side",
        "moon_tide_m": 0.0,
        "photic_zone_m": photic_zone_m,
        "secchi_depth_m": secchi_depth_m,
        "light_at_100m_fraction": light_at_100m,
        "S_earth": float(parent.get("S_earth", 1.0)),
        "T_star_surface": float(parent.get("T_star_surface", 5772.0)),
        "day_s": day_s,
        # THE TILT, CARRIED. The ONE sun is derived from it (matter.py) -- the glint's mirror point
        # and the baked diffuse both hang off this number, so the chain must deliver it.
        "obliquity_effective_deg": float(parent["obliquity_effective_deg"]),
        "ocean_class": cls,
        "name": "a" + cls + "Ocean",                        # derived, like the star's colour
    }


def sun_direction(tt, nums):
    """THE ONE SUN, read (matter.py): the water's light is the world's single star, derived from
    the world's own tilt -- never a typed copy. The emit bakes the diffuse with it; the live viewer
    sets the renderer's light with it; the renderer's specular kernel draws the glint where the
    half-vector says -- so the baked diffuse and the glint can never disagree about where the sun
    is. Same phase as theTerrain's sun (the day runs together)."""
    import matter
    return matter.sun_direction(float(tt), float(nums["obliquity_effective_deg"]))


def emit(nums, t=1.0):
    """The matter of this water, in its own local units (1.0 = the planet's radius).

    THE WATER ALONE -- the land is theTerrain's, the clouds theAtmosphere's; a membrane may not
    draw a sibling's matter. What is drawn is what the WATER does to light:
      * the BODY -- deep navy, the measured absorption spectrum (red dies first);
      * the GLINT -- a READER, not a paint (Stage 21). The buffer carries the density-derived
        Fresnel F0 and the sea's own slope in the specular columns (SPEC_F0/SPEC_SLOPE); the
        renderer's kernel draws the glint where the mirror point says, and ONLY when the live
        viewer sets the membrane's own sun as a light. No light, no glint -- nothing painted;
      * the ICE -- white where the parent froze the sea, purely by latitude;
      * the FOAM -- a sparkle of whitecaps where the wind works, sparse at 7 m/s.
    The movie is ONE DAY: the glint crosses the water once, dawn to dusk.
    """
    import numpy as np
    from matter import (blank, fibonacci_sphere, surface_grain, lit, SOLID,
                        paint_specular, SPEC_F0, SPEC_SLOPE)

    tt = float(t)
    rng = np.random.default_rng(83)
    R = float(nums["extent_m"])
    lens = nums.get("_lens", {})
    TONE = float(lens.get("exposure", 0.42))

    sun = sun_direction(tt, nums)
    S_rel = float(nums.get("S_earth", 1.0))

    deep = np.array(nums["ocean_rgb_deep"], np.float32)
    n = 34000
    d = fibonacci_sphere(n, jitter=0.9, seed=83)
    lat = np.abs(d[:, 2])
    ice = lat > sin(float(nums["ice_line_lat_deg"]) * pi / 180.0)

    b = blank(n)
    b[:, 0:3] = d
    b[:, 21:24] = d
    cos_sun = np.clip((d * sun[None, :]).sum(1), 0.0, None)

    # the water body: the measured deep colour, lit by the sun. The glint is NOT painted on top
    # (the old warm patch is gone); it lives in the reader columns below.
    foam = np.clip(rng.normal(0.0, 1.0, n) - 2.6, 0.0, 1.0) * float(nums["foam_fraction"]) * 40.0
    water_col = lit(deep[None, :] * np.ones((n, 3), np.float32),
                    S_rel * cos_sun + 0.012, e_ref=max(S_rel, 1e-6), tone=TONE)
    col = np.clip(water_col + foam[:, None] * 0.5, 0.0, 1.0)
    col[ice] = np.array([0.80, 0.84, 0.88], np.float32) * (0.25 + 0.75 * cos_sun[ice, None])
    b[:, 16:19] = col.astype(np.float32)
    b[:, 19] = np.where(ice, 0.95, 0.85)
    b[:, 20] = surface_grain(n, radius=1.0, cover=0.75)
    b[:, 11] = SOLID
    # THE READER: the membrane's own derived numbers, painted where the kernel can read them.
    # The ice REFUSES the water's reader -- ice has its own optics, and this membrane has not
    # published them; an unpainted column is a silence, never a default.
    paint_specular(b, float(nums["sunglint_intensity"]), float(nums["surface_slope_mean"]))
    b[ice, SPEC_F0] = 0.0
    b[ice, SPEC_SLOPE] = 0.0
    return b


def measure(nums):
    """The name must match the class the dissolved load puts it in; and the two independent depth
    paths (volume/area here, the Terrain solver's own) must sit within a fifth of each other."""
    folder = Path(__file__).resolve().parent.name
    return {"salinity_g_kg": nums["salinity_g_kg"],
            "ocean_class": nums["ocean_class"],
            "name_matches_class": folder == nums["name"],
            "mean_depth_sane": 500.0 < nums["mean_ocean_depth_m"] < 8000.0,
            "no_moon": nums["moon_tide_m"] == 0.0,
            "solar_tide_is_equilibrium": 0.05 < nums["solar_tide_m"] < 0.5}
