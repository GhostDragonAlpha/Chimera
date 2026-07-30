"""aNitrogenAtmosphere -- the air that actually formed over aBlueWorld. An INSTANCE of theAtmosphere.

theAtmosphere established what air IS: gas that gravity keeps, with weight, a coloured sky, weather,
and no edge. This membrane is the instance -- it inherits this world's kept gases, pressure, scale
height and spin from the law above, and derives everything the air here is LIKE: its molecule, its
lapse rate, its sky colour through a day, its cloud deck, its top, and whether a human can breathe it.

    scale height + T     -> the mean molecule -> c_p -> the LAPSE RATE (chained, not looked up)
    pressure / g         -> the column mass -> the OPTICAL DEPTH -> the sky's colour
    dewpoint + lapse     -> where the clouds sit
    spin + the sun       -> the day movie: noon blue -> terminator red
    N sigma H ~ 1        -> where the air ENDS

THE CHAIN PREDICTS WHAT IT WAS NEVER FITTED TO. The law handed down the scale height (11,312 m);
inverting it for the mean molecule gives mu = kT/Hg = 29.0 g/mol -- nobody told this membrane the
air is nitrogen. From mu alone: R_specific = 286.7 J/kg/K (Earth's air: 287), c_p = 3.5 R = 1,003
J/kg/K (Earth: 1,005), sound speed 335 m/s (Earth: 343), moist lapse 4.7 K/km (Earth: 6.5). One
input, four checks, zero dials turned.

THE NAME IS DERIVED, NOT ASSIGNED. An atmosphere is classified by its dominant gas, and the mean
molecule is measured from the scale height: 29.0 g/mol sits at nitrogen, so this membrane is
`aNitrogenAtmosphere`. Rename it wrongly -- or change the world's air so the class moves -- and
measure() fails, exactly like the star's colour class.

THE FREE DIALS: the oxygen share, the humidity, and the cloud cover -- a world's HISTORY, not its
physics. With the defaults (Earth-like 21% O2), this air is NOT breathable: 0.52 bar of it gives
ppO2 = 0.109 bar, under the 0.16 bar hypoxia line. That is a finding, not a setting.
"""
from math import pi, sqrt, exp, log, sin, cos
from pathlib import Path

K_B = 1.380649e-23         # Boltzmann, J/K (exact, SI)
M_U = 1.66053907e-27       # atomic mass unit, kg (exact, SI)
GAMMA = 1.4                # diatomic gas (N2/O2): c_p = GAMMA/(GAMMA-1) * R_specific = 3.5 R
MOIST = 0.66               # moist/dry lapse ratio -- condensation heat, measured on Earth (6.5/9.8)

TAU_EARTH_550 = 0.098      # Earth's measured zenith optical depth at 550 nm (mid-visible, clear air)
COLUMN_EARTH = 101325.0 / 9.81   # kg/m^2 -- the anchor the optical depth scales from
LAMBDA_RGB = (630.0, 545.0, 460.0)   # the three channels' centre wavelengths, nm (R, G, B order)

TROPO_PAUSE_FRAC = 0.15    # tropopause pressure / surface pressure -- Earth's own band is 0.1-0.22
AIRMASS_HORIZON = 38.0     # relative air mass at the horizon (measured; Earth's sunset reddens by it)
TWILIGHT_DEG = 6.0         # civil twilight: sun 0 -> -6 degrees

SIGMA_COLL = 3.0e-19       # m^2: N2 collision cross-section (~0.3 nm^2, measured)
PPO2_HYPOXIA = 0.16        # bar: below this a human hypoxiates (0.16 = high-altitude limit, measured)
PPO2_TOXIC = 0.29          # bar: above this oxygen itself poisons, long exposure

# THE CLASSIFICATION: an atmosphere is its dominant gas. Boundaries sit at the geometric midpoints
# of the real gases' molar masses -- H2(2) He(4) CH4(16) N2(28) O2(32) CO2(44) -- and the mean
# molecule (measured from the scale height) lands in one of them. Computed, never assigned.
GAS_CLASSES = [(3.0, "Hydrogen"), (10.0, "Helium"), (22.0, "Methane"),
               (30.0, "Nitrogen"), (38.0, "Oxygen"), (1e9, "CarbonDioxide")]


def gas_class(mu_g_mol: float) -> str:
    for hi, name in GAS_CLASSES:
        if mu_g_mol < hi:
            return name
    return "CarbonDioxide"


# THE LENS -- dials that change the PICTURE and nothing else. The air is 0.2% of the radius: at true
# scale it is a hairline. So the render declares a thickness exaggeration, and hands you the dial to
# turn it back. Set every lens to 1.0 and you see what is really there.
LENS = {
    "thickness": {"lo": 1.0, "hi": 40.0, "default": 12.0,
                  "label": "shell thickness", "unit": "x true"},
    "exposure": {"lo": 0.15, "hi": 1.0, "default": 0.42,
                 "label": "film speed", "unit": "gamma"},
}

# THE FREE DIALS -- the world's history, which no law can force. Defaults are Earth's own, so the
# first numbers say what an Earth-like history does on THIS world's gravity and pressure.
FREE = {
    "o2_fraction": {"lo": 0.0, "hi": 0.6, "default": 0.21,
                    "label": "oxygen share", "unit": "of the air"},
    "relative_humidity": {"lo": 0.05, "hi": 1.0, "default": 0.77,
                          "label": "humidity", "unit": "of saturation"},
    "cloud_cover": {"lo": 0.0, "hi": 1.0, "default": 0.5,
                    "label": "cloud cover", "unit": "of the sky"},
}


def _planck_rel(wl_nm: float, T: float) -> float:
    """Relative spectral radiance of a blackbody at wavelength wl (nm) -- the star's colour as a
    MEASUREMENT, never a palette."""
    x = 1.4387769e-2 / (wl_nm * 1e-9 * T)      # hc / lambda k T
    return (wl_nm ** -5.0) / (exp(x) - 1.0)


def _sky_rgb(tau_zenith_rgb, T_star: float, airmass: float = 1.0):
    """The sky's colour from the optical depth: scattered light L ~ S(lambda)(1 - e^{-tau m}).
    At noon (m=1) the blue channel's tau is largest, so the dome is blue; at the horizon (m=38) the
    blue is scattered AWAY and what survives is red. One equation, both ends of the day."""
    out = []
    for wl, tau in zip(LAMBDA_RGB, tau_zenith_rgb):
        out.append(_planck_rel(wl, T_star) * (1.0 - exp(-tau * airmass)))
    m = max(out) or 1.0
    return [v / m for v in out]


def _sun_rgb(tau_zenith_rgb, T_star: float, airmass: float = 1.0):
    """The DIRECT light that survives the column: S(lambda) e^{-tau m} -- the sun's own tint."""
    out = [_planck_rel(wl, T_star) * exp(-tau * airmass) for wl, tau in zip(LAMBDA_RGB, tau_zenith_rgb)]
    m = max(out) or 1.0
    return [v / m for v in out]


def derive(parent, free):
    """This air, from the law's handed-down state."""
    g = float(parent["g"]); R = float(parent["R"])
    P = float(parent["P_surface_bar"]) * 1e5              # Pa
    H = float(parent["scale_height_m"])
    T = float(parent["T_surface"])
    T_star = float(parent.get("T_star_surface", 5772.0))
    S_rel = float(parent.get("S_earth", 1.0))
    day_s = float(parent.get("day_s", 86400.0))

    o2 = float(free.get("o2_fraction", FREE["o2_fraction"]["default"]))
    rh = float(free.get("relative_humidity", FREE["relative_humidity"]["default"]))
    ccf = float(free.get("cloud_cover", FREE["cloud_cover"]["default"]))

    # THE MOLECULE THE SCALE HEIGHT IMPLIES. H = kT/(mu g) -> mu = kT/(H g), in kg.
    mu_mol = K_B * T / (H * g)                             # kg per molecule
    mean_molar_mass = mu_mol / M_U                         # g/mol (the count of atomic units)
    R_spec = K_B / mu_mol                                  # J/kg/K
    c_p = GAMMA / (GAMMA - 1.0) * R_spec                   # J/kg/K

    # WEIGHT: the column is the pressure, the pressure is the column -- one fact, two sides.
    column_mass = P / g                                    # kg/m^2
    air_mass_total = column_mass * 4.0 * pi * R * R        # kg
    surface_density = P * mu_mol / (K_B * T)               # kg/m^3

    # THE TEMPERATURE PROFILE: dry lapse g/c_p; moist = MOIST x dry (condensation heat returned).
    lapse_dry = g / c_p                                    # K/m
    lapse_rate_K_per_km = lapse_dry * MOIST * 1000.0
    tropopause_m = H * log(1.0 / TROPO_PAUSE_FRAC)
    T_tropopause = T - lapse_dry * MOIST * tropopause_m

    # THE OPTICAL DEPTH -- the one number the whole sky hangs on. Rayleigh tau scales with the
    # column (more air scatters more) and as lambda^-4 (blue scatters most). Anchored to Earth's
    # measured 0.098 at 550 nm -- the one input, everything else derived.
    col_ratio = column_mass / COLUMN_EARTH
    tau_zenith_rgb = [TAU_EARTH_550 * col_ratio * (550.0 / wl) ** 4.0 for wl in LAMBDA_RGB]
    optical_depth_zenith = TAU_EARTH_550 * col_ratio       # at 550 nm, the reference wavelength
    optical_depth_limb = optical_depth_zenith * AIRMASS_HORIZON

    sky_rgb_noon = _sky_rgb(tau_zenith_rgb, T_star, 1.0)
    sky_rgb_dawn = _sun_rgb(tau_zenith_rgb, T_star, AIRMASS_HORIZON)
    sky_rgb_dusk = list(sky_rgb_dawn)                      # same physics, other side of the sun
    sun_rgb_noon = _sun_rgb(tau_zenith_rgb, T_star, 1.0)

    # THE DAY CYCLE: the sun's angular speed is set by the spin; twilight is 6 degrees of it.
    solar_rate_deg_s = 360.0 / day_s
    twilight_duration_s = TWILIGHT_DEG / solar_rate_deg_s
    solar_zenith_track = "sun crosses the sky once per day; rate set by day_s"

    # CLOUDS: air lifted cools at the lapse rate; the dewpoint is where the water falls out.
    T_C = T - 273.15
    gamma_mag = log(max(rh, 1e-6)) + (17.27 * T_C) / (237.7 + T_C)   # August-Roche-Magnus
    dewpoint_surface = 237.7 * gamma_mag / (17.27 - gamma_mag) + 273.15
    spread = max(T - dewpoint_surface, 0.0)
    cloud_base_m = spread / (lapse_dry * MOIST) if lapse_dry > 0 else 0.0
    cloud_top_m = tropopause_m                             # weather stops at the tropopause
    cloud_cover_fraction = ccf

    # WIND AND WEATHER, read from the climate solution where they live.
    wind_surface_ms = float(parent.get("wind_surface_ms", 0.0))
    dynamic_pressure_pa = 0.5 * surface_density * wind_surface_ms ** 2.0
    sound_speed_ms = sqrt(GAMMA * R_spec * T)
    v_kmh = wind_surface_ms * 3.6
    wind_chill_C = (13.12 + 0.6215 * T_C - 11.37 * v_kmh ** 0.16 + 0.3965 * T_C * v_kmh ** 0.16) \
        if v_kmh > 4.8 else T_C
    # THE HYDROLOGICAL SCALING: warmer air holds ~7% more water per kelvin (Clausius-Clapeyron),
    # so this colder world's rain is Earth's mean dialled down by its temperature and its ocean.
    rain_rate_mm_day = 2.74 * (2.0 ** ((T - 288.15) / 14.0)) \
        * float(parent.get("ocean_fraction", 0.7)) / 0.71
    storm_days_per_year = 45.0 * rain_rate_mm_day / 2.74   # scaled from Earth's humid-midlat norm
    snow_line_altitude_m = max(0.0, (T - 273.15) / (lapse_dry * MOIST))

    # THE TOP EDGE: the air ends where a molecule can leave without one more collision --
    # N(z) sigma H ~ 1, i.e. z = H ln(N0 sigma H).
    N0 = P / (K_B * T)
    exobase_m = H * log(N0 * SIGMA_COLL * H)
    escape_velocity_ms = sqrt(2.0 * g * R)

    # BREATHABILITY IS A MEASUREMENT, not a hope: the partial pressure of oxygen against the two
    # measured human limits. With Earth's 21% share at this world's 0.52 bar, it FAILS the low bar.
    ppo2 = o2 * P / 1e5
    breathable = bool(PPO2_HYPOXIA <= ppo2 <= PPO2_TOXIC)

    cls = gas_class(mean_molar_mass)

    return {
        "extent_m": R,
        "duration_s": day_s,
        "g": g, "R": R,
        "P_surface_bar": P / 1e5,
        "scale_height_m": H,
        "mean_molar_mass": mean_molar_mass,
        "c_p_J_kgK": c_p,
        "column_mass_kg_m2": column_mass,
        "air_mass_total_kg": air_mass_total,
        "surface_density_kg_m3": surface_density,
        "T_surface": T,
        "lapse_rate_K_per_km": lapse_rate_K_per_km,
        "tropopause_m": tropopause_m,
        "T_tropopause": T_tropopause,
        "tau_zenith_rgb": tau_zenith_rgb,
        "optical_depth_zenith": optical_depth_zenith,
        "optical_depth_limb": optical_depth_limb,
        "rayleigh_strength": col_ratio,
        "sky_rgb_noon": sky_rgb_noon,
        "sky_rgb_dawn": sky_rgb_dawn,
        "sky_rgb_dusk": sky_rgb_dusk,
        "sun_rgb_noon": sun_rgb_noon,
        "S_earth": S_rel,
        "T_star_surface": T_star,
        "dewpoint_surface": dewpoint_surface,
        "cloud_base_m": cloud_base_m,
        "cloud_top_m": cloud_top_m,
        "cloud_cover_fraction": cloud_cover_fraction,
        "relative_humidity": rh,
        "wind_surface_ms": wind_surface_ms,
        "dynamic_pressure_pa": dynamic_pressure_pa,
        "sound_speed_ms": sound_speed_ms,
        "wind_chill_C": wind_chill_C,
        "rain_rate_mm_day": rain_rate_mm_day,
        "storm_days_per_year": storm_days_per_year,
        "snow_line_altitude_m": snow_line_altitude_m,
        "exobase_m": exobase_m,
        "escape_velocity_ms": escape_velocity_ms,
        "day_s": day_s,
        "twilight_duration_s": twilight_duration_s,
        "solar_zenith_track": solar_zenith_track,
        "o2_fraction": o2,
        "ppo2_bar": ppo2,
        "breathable": breathable,
        "gas_class": cls,
        "name": "a" + cls + "Atmosphere",                 # derived, like the star's colour
        "gases_kept": parent.get("gases_kept", []),
        "escape_ratios": parent.get("escape_ratios", {}),
        "has_atmosphere": True,
    }


def emit(nums, t=1.0):
    """The matter of this air, in its own local units (1.0 = the planet's radius).

    THE SHELL AND THE SKY IN ONE, and both are MEASURED LIGHT, not paint:
      * the SHELL -- the column itself seen edge-on. Its density falls as e^{-z/H}, so it has NO
        edge: the glow fades. Its colour at each point is the sky's colour at that sun angle --
        blue-white on the day side, red at the terminator band (the sunset, from outside).
      * the CLOUD DECK -- broken white at the height the dewpoint puts it, drifting with the wind.
    The planet is NOT drawn -- it is a sibling's matter, and a membrane may not draw another's.
    The movie is ONE DAY: the sun goes round once, and the red band sweeps the limb with it.
    """
    import numpy as np
    from matter import blank, fibonacci_sphere, surface_grain, lit, SOLID, GLOW

    tt = float(t)
    rng = np.random.default_rng(71)
    R = float(nums["extent_m"])
    H = float(nums["scale_height_m"])
    lens = nums.get("_lens", {})
    THICK = float(lens.get("thickness", 12.0))
    TONE = float(lens.get("exposure", 0.42))

    day = 2.0 * pi * tt - 1.15                     # same phase as theTerrain: ONE DAY, one sun-crossing
    sun = np.array([sin(day), -cos(day), 0.22], np.float32)
    sun = sun / np.linalg.norm(sun)

    noon = np.array(nums["sky_rgb_noon"], np.float32)
    dawn = np.array(nums["sky_rgb_dawn"], np.float32)
    S_rel = float(nums.get("S_earth", 1.0))

    # THE SHELL. An atmosphere has NO edge: its density falls as e^{-z/H}, so its glow just fades.
    # That single measured fact is why earlier renders failed the dyad -- a shell drawn with a hard
    # outer boundary gives the eye a CIRCLE, and a circle with stuff inside it is a planet. So the
    # grains' heights follow the exponential distribution the law says (z = -H ln u), each grain's
    # alpha IS its local density, and the projection crowds the low, dense grains into the bright
    # ring at the surface's rim -- the limb, where an atmosphere is actually seen from space.
    n_sh = 26000
    d = fibonacci_sphere(n_sh, jitter=0.9, seed=71)
    h_true = 3.0 * H / R
    u = np.clip(rng.random(n_sh), 1e-6, 1.0)
    z = -np.log(u) * h_true * THICK                     # heights, exponentially distributed
    z = np.clip(z, 0.0, 3.0 * h_true * THICK)
    b = blank(n_sh)
    b[:, 0:3] = d * (1.0 + z)[:, None]
    dens = np.exp(-z / (h_true * THICK))                # the density each grain stands for

    # THE COLOUR OF THE SKY AT EACH SUN ANGLE. Where the grain sits near the terminator great
    # circle, the path through the air is long -- so the colour slides from noon blue to dusk red,
    # exactly as the optical depth says. This is the limb going red at sunset, from outside.
    cos_sun = (d * sun[None, :]).sum(1)
    daylight = np.clip(cos_sun * 3.0 + 0.5, 0.0, 1.0)          # 1 day side, 0 deep night
    term_band = np.exp(-((np.abs(cos_sun) - 0.06) / 0.16) ** 2)  # 1 near the terminator
    col = (noon[None, :] * daylight[:, None] * (1.0 - term_band[:, None])
           + dawn[None, :] * term_band[:, None])
    bright = (0.10 + 0.90 * np.clip(cos_sun, 0.0, None)) * (0.25 + 0.75 * daylight)
    b[:, 16:19] = np.clip(col * bright[:, None] * S_rel, 0.0, 1.0).astype(np.float32)
    b[:, 19] = (0.16 * dens).astype(np.float32)          # the glow FADES with height: no edge to see
    b[:, 20] = surface_grain(n_sh, radius=1.0 + h_true * THICK * 0.5, cover=1.15)
    b[:, 11] = GLOW

    parts = [b]

    # THE CLOUD DECK -- broken white where the dewpoint puts it, advected by the wind through
    # the day. Cover fraction from the FREE dial; the field is a few smooth waves, thresholded,
    # so the clouds are CONTIGUOUS (bands and patches), never confetti.
    ccf = float(nums["cloud_cover_fraction"])
    if ccf > 0.01:
        n_c = 9000
        dc = fibonacci_sphere(n_c, jitter=0.9, seed=72)
        drift = tt * 2.0 * pi * float(nums["wind_surface_ms"]) * float(nums["day_s"]) / (2.0 * pi * R)
        ca, sa = cos(drift), sin(drift)
        rot = np.array([[ca, -sa, 0.0], [sa, ca, 0.0], [0.0, 0.0, 1.0]], np.float64)
        dcw = dc @ rot.T                                        # the deck advects past the fixed sun
        field = np.zeros(n_c)
        for k, amp in ((3.1, 1.0), (6.3, 0.55), (11.5, 0.28)):
            for _ in range(3):
                v = rng.normal(size=3); v /= np.linalg.norm(v)
                field += amp * np.sin(k * (dcw @ v) + rng.uniform(0, 2 * pi))
        keep = field > np.quantile(field, 1.0 - ccf)
        dc, keep_idx = dc[keep], keep
        if len(dc):
            h_cloud = float(nums["cloud_base_m"]) / R
            puff = 0.35 * (float(nums["cloud_top_m"]) - float(nums["cloud_base_m"])) / R
            rc = 1.0 + (h_cloud + puff * rng.random(len(dc))) * THICK * 0.35
            c = blank(len(dc))
            c[:, 0:3] = dc * rc[:, None]
            c[:, 21:24] = dc
            cos_c = np.clip((dc * sun[None, :]).sum(1), 0.0, None)
            c[:, 16:19] = lit(np.array([0.92, 0.93, 0.95], np.float32),
                              S_rel * cos_c + 0.012, e_ref=max(S_rel, 1e-6), tone=TONE)
            c[:, 19] = 0.30                                     # WISPS, not a second surface: a
            c[:, 20] = surface_grain(len(dc), radius=1.0, cover=0.9)  # cloud is air you can see
            c[:, 11] = SOLID                                    # through, or it reads as a white ball
            parts.append(c)

    return np.concatenate(parts, axis=0)


def measure(nums):
    """The name must match the class the physics produces: the folder is called what the mean
    molecule says it is, so a wrong rename -- or changed air that moves the class -- fails here."""
    folder = Path(__file__).resolve().parent.name
    return {"mean_molar_mass": nums["mean_molar_mass"],
            "gas_class": nums["gas_class"],
            "name_matches_class": folder == nums["name"],
            "molecule_is_air": 27.0 < nums["mean_molar_mass"] < 30.0}
