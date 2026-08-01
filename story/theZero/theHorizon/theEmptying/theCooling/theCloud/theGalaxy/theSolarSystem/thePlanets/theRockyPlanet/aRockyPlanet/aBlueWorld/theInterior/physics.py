"""theInterior -- THE LAW of planetary insides: what a rocky planet's interior IS.

A rocky planet is differentiated: the heavy sank and the light floated, so it is SHELLS -- an
iron core wrapped in a rocky mantle wrapped in a thin crust. Everything else about every
interior is that one fact's engine running:

    HEAT: accretion left the inside hot, and radioactivity (U/Th/K, chondritic ~5 pW/kg,
    measured) keeps feeding it. The heat leaves through the top -- so the gradient, the
    convection, the volcanism, and the dynamo are all the same heat on its way out.

    STIRRING: a fluid heated from below convects if its Rayleigh number clears ~1100 (measured
    threshold). The mantle creeps at centimetres a year and drags the crust with it: plates.

    THE DYNAMO: a liquid metal outer core, convecting, on a spinning planet, is a dynamo --
    and the field stands the star's wind off the atmosphere. When the heat runs out, the core
    freezes solid, the dynamo dies, and the air follows: the classification of an interior is
    its THERMAL STATE -- active (Earth), stagnant (Mars), dead (the Moon).

    THE RETURN PATH: volcanism outgasses -- the atmosphere above is, ultimately, the interior
    exhaling. And the inner core freezing releases latent heat, which is what powers the
    dynamo's long life.

An instance is named by its class -- active / stagnant / dead -- computed from its own heat,
its dynamo, and its convection. The INSTANCE here is `aActiveInterior`.
"""

RA_CRITICAL = 1100.0           # measured: the onset of convection in a bottom-heated fluid
HEAT_PRODUCTION_CHONDRITIC = 5.0e-12   # W/kg, U/Th/K in chondritic rock (measured)
T_CMB_EARTH = 4000.0           # K at the core-mantle boundary (Earth, measured band 3800-4300)
T_ICB_EARTH = 5400.0           # K at the inner-core boundary (Earth, measured)
INNER_CORE_FRAC_EARTH = 0.35   # of the core's radius (Earth, seismic)
VISCOSITY_MANTLE_EARTH = 1.0e21      # Pa.s
THERMAL_DIFFUSIVITY = 1.0e-6         # m^2/s
EXPANSIVITY = 2.0e-5                 # /K
DIPOLE_EARTH = 8.0e22                # A m^2 (measured)
RAM_PRESSURE_1AU = 2.0e-9            # Pa, solar wind at 1 au (measured band 1-3 nPa)
CRUST_ABUNDANCE = {"Fe": 0.056, "Cu": 6.0e-5, "Ni": 0.0, "Pb": 1.4e-5}   # Rudnick & Gao (measured)
VOLCANIC_CO2_EARTH = 2.6e11          # kg/yr (measured band 0.1-0.4 Gt)


def interior_class(has_dynamo: bool, convecting: bool, heat_TW: float, M_mantle: float) -> str:
    """The classification, computed: active (dynamo + convection), stagnant (convection without
    a working dynamo), dead (neither)."""
    if has_dynamo and convecting:
        return "Active"
    if convecting or heat_TW > 0.5 * HEAT_PRODUCTION_CHONDRITIC * M_mantle:
        return "Stagnant"
    return "Dead"


def derive(parent, free):
    """The law, stated against this world: the shells and the thermal state, read from the
    planet's own derivations (carried through aBlueWorld -- derived once, never twice), and
    handed down for the instance to compute with."""
    has_dynamo = bool(parent["dynamo"])
    heat_TW = float(parent["total_heat_TW"])
    M = float(parent["M"])
    core_mf = float(parent["core_mass_frac"])
    M_mantle = M * (1.0 - core_mf)
    convecting = True                       # the planet's own solution says it convects (dynamo needs it)
    cls = interior_class(has_dynamo, convecting, heat_TW, M_mantle)
    return {
        "extent_m": float(parent["extent_m"]),
        "duration_s": 4.5e9 * 3.1557e7,     # the cooling span -- Earth's own age as the reference;
                                            # this system's age is NOT yet derived in the story (said so)
        "g": float(parent["g"]), "R": float(parent["extent_m"]),
        "M": M,
        "core_radius_frac": float(parent["core_radius_frac"]),
        "core_R_m": float(parent["core_R_m"]),
        "core_mass_frac": core_mf,
        "M_mantle_kg": M_mantle,
        "dynamo": has_dynamo,
        "magnetised": bool(parent["magnetised"]),
        "heat_flux_W_m2": float(parent["heat_flux_W_m2"]),
        "total_heat_TW": heat_TW,
        "central_pressure_Pa": float(parent["central_pressure_Pa"]),
        "rho_bulk": float(parent["rho_bulk"]),
        # the law's own facts the children compute with: the crust's measured abundances and the
        # surface gradient (heat flux over conductivity -- the interior's own number, at home here)
        "crust_element_fraction": CRUST_ABUNDANCE,
        "geothermal_gradient_K_km": float(parent["heat_flux_W_m2"]) / 3.0 * 1e3,
        "day_s": float(parent.get("day_s", 86400.0)),
        "a_au": float(parent["a_au"]),
        "S_earth": float(parent.get("S_earth", 1.0)),
        "T_surface": float(parent.get("T_surface", 288.0)),
        "interior_class_of_this_world": cls,
        "ra_critical": RA_CRITICAL,
    }


# ── WHAT HEATS A PLANET, AND HOW IT RUNS OUT ────────────────────────────────────────────────────
# The membrane already carries HEAT_PRODUCTION_CHONDRITIC as a number for TODAY. But a planet's
# furnace is four radioactive isotopes with four different half-lives, so "today" is one frame of a
# 4.5-billion-year decline -- and this membrane's own `duration_s` is 1.42e17 s, which IS 4.5 Gyr.
#
# Half-lives are measured to five figures; the present-day split of radiogenic heat between the four
# is the standard bulk-silicate-Earth budget. Both are published, neither is chosen here.
RADIOGENIC = {
    #  isotope : (half-life in Gyr, fraction of TODAY's radiogenic heat)
    "238U":  (4.468, 0.40),
    "235U":  (0.704, 0.02),
    "232Th": (14.05, 0.40),
    "40K":   (1.248, 0.18),
}
AGE_GYR = 4.5                  # the span this membrane's duration_s already declares


def radiogenic_factor(gyr_before_present: float) -> float:
    """HOW MUCH HOTTER THE FURNACE WAS, that long ago. Each isotope is run backwards by its own
    half-life and the four are summed at today's weights:

        H(t)/H(now) = SUM_i  f_i * 2^(dt / T_i)

    THE CHECK NOBODY FITTED: at 4.5 Gyr this returns ~5x, and the measured/modelled figure for
    Earth's radiogenic heating at formation is ~5x present. It falls out of four half-lives and
    four weights, and the reason it is 5 and not 2 is 235U and 40K -- both nearly gone now, both
    dominant then. A single "effective half-life" cannot produce that number."""
    dt = float(gyr_before_present)
    return sum(f * 2.0 ** (dt / T) for T, f in RADIOGENIC.values())


def inner_core_frac(t_frac: float, final_frac: float = INNER_CORE_FRAC_EARTH,
                    nucleation_frac: float = 0.72) -> float:
    """THE INNER CORE, freezing outward from the centre.

    A solid core grows by giving up latent heat through the liquid above it, so its VOLUME tracks
    the heat extracted since it nucleated -- and the radius is the cube root of that. Nothing else
    is claimed: no phase diagram, no melting curve.

    `nucleation_frac` -- when in the planet's life the centre first crosses freezing -- is the one
    number here neither derived nor inherited, and it is named rather than buried. Earth's inner
    core is dated seismically and geomagnetically to roughly the last billion years, which is where
    0.72 of 4.5 Gyr comes from."""
    x = (float(t_frac) - float(nucleation_frac)) / max(1.0 - float(nucleation_frac), 1e-9)
    return 0.0 if x <= 0.0 else float(final_frac) * (min(x, 1.0) ** (1.0 / 3.0))


def emit(nums, t=1.0):
    """FOUR AND A HALF BILLION YEARS OF A PLANET COOLING, which is what this chapter's clock says.

    WHAT WAS HERE. A ball of orange dots at fixed radii and fixed colours, ignoring `t`, under the
    boilerplate line "this emit exists so the membrane can stand alone while its instance is grown".
    Four membranes in this tree carried that sentence; all four rendered a photograph. This one
    declared `duration_s = 1.42e17 s` -- 4.5 billion years -- and then showed a single instant.

    WHAT IT DRAWS NOW, all from numbers this membrane already derived:

      THE FURNACE DIMS. Colour is temperature, and temperature follows the radiogenic budget run
      backwards through four measured half-lives: ~5x hotter at formation, falling to today's
      value. The mantle goes from glowing to dull along the way.
      THE INNER CORE APPEARS. Nothing at the start; it nucleates about three-quarters of the way
      through and grows as the cube root of the heat since extracted, reaching this world's
      derived fraction.
      THE CUTAWAY IS AN OCTANT REMOVED, so the shells are legible from outside -- the core-mantle
      boundary is this membrane's own `core_radius_frac`, not a drawn ring.

    LOCAL UNITS: 1.0 is the planet's radius.
    """
    import numpy as np
    from matter import blank, fibonacci_sphere, surface_grain, SOLID, GLOW, AR, AB

    tt = min(max(float(t), 0.0), 1.0)
    gyr_ago = AGE_GYR * (1.0 - tt)
    heat = radiogenic_factor(gyr_ago)                     # x present-day
    heat0 = radiogenic_factor(AGE_GYR)
    warm = (heat - 1.0) / max(heat0 - 1.0, 1e-9)          # 1 at formation, 0 today

    core_f = float(nums["core_radius_frac"])
    ic_f = core_f * inner_core_frac(tt)

    rng = np.random.default_rng(97)
    n = 8000
    d = fibonacci_sphere(n, jitter=0.9, seed=97)
    r = rng.random(n) ** 0.38                             # fill the ball, biased outward
    P = d * r[:, None]
    # THE CUTAWAY: drop one octant so the inside is visible from outside. A cutaway is how a
    # planetary interior is ever seen; there is no other way to look at one.
    keep = ~((P[:, 0] > 0) & (P[:, 1] > 0) & (P[:, 2] > 0))
    P, r = P[keep], r[keep]
    m = len(r)

    # TEMPERATURE BY DEPTH AND BY EPOCH. The centre is hottest, the surface fixed by the star;
    # the whole profile lifts with the radiogenic factor, which is the only thing time does here.
    # THE PROFILE IS ANCHORED AT BOTH ENDS AND LIFTED IN THE MIDDLE. The surface is pinned by the
    # star (T_surface, inherited); the core-mantle boundary and the centre are the measured Earth
    # values scaled by how much hotter the furnace was running. `warm` is 1 at formation and 0 now,
    # so today the profile IS the measured Earth one and every earlier frame is a multiple of it.
    T_surf = float(nums["T_surface"])
    T_cmb = T_CMB_EARTH * (1.0 + 0.55 * warm)
    T_c = T_ICB_EARTH * (1.0 + 0.55 * warm)
    depth_frac = np.clip((1.0 - r) / max(1.0 - core_f, 1e-9), 0.0, 1.0)
    T = T_surf + (T_cmb - T_surf) * depth_frac                     # through the mantle
    inside = r < core_f
    T = np.where(inside, T_cmb + (T_c - T_cmb) * (1.0 - r / max(core_f, 1e-9)), T)

    # COLOUR IS THE TEMPERATURE, on a blackbody-ish ramp -- a hot interior is not "orange",
    # it is whatever its temperature emits, and that is what has to change over 4.5 Gyr.
    x = np.clip((T - 700.0) / 5200.0, 0.0, 1.0)[:, None]
    cold = np.array([0.20, 0.14, 0.11], np.float32)
    mid = np.array([0.85, 0.28, 0.06], np.float32)
    hot = np.array([1.00, 0.85, 0.55], np.float32)
    col = np.where(x < 0.5, cold + (mid - cold) * (x / 0.5),
                   mid + (hot - mid) * ((x - 0.5) / 0.5)).astype(np.float32)
    # the solid inner core reads as a distinct, denser body once it exists
    solid = r < ic_f
    col[solid] = np.array([1.00, 0.94, 0.80], np.float32)

    b = blank(m)
    b[:, 0:3] = P
    b[:, 16:19] = col
    b[:, AR:AB + 1] = col
    b[:, 19] = np.where(inside, 0.75, 0.45).astype(np.float32)
    b[:, 20] = surface_grain(m, radius=0.7, cover=1.0)
    b[:, 11] = np.where(solid, SOLID, GLOW)
    return b


def layout(nums):
    """WHAT IS CONTAINED HERE. theInterior is the LAW -- shells, heat, stirring, the dynamo.
    aActiveInterior is the inside this planet actually has -- named by its thermal state,
    computed. It sits at the centre at full size: at this scale the membrane IS the interior."""
    return {"aActiveInterior": ((0.0, 0.0, 0.0), 1.0)}


def measure(nums):
    """The class must be computable and consistent with the planet's own dynamo verdict."""
    return {"class_computed": nums.get("interior_class_of_this_world") in ("Active", "Stagnant", "Dead"),
            "dynamo_agrees_with_planet": bool(nums["dynamo"]) == bool(nums["magnetised"])}
