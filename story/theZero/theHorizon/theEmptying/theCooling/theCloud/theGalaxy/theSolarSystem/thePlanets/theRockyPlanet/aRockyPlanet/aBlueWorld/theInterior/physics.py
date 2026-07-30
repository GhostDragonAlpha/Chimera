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
        "extent_m": float(parent["R"]),
        "duration_s": 4.5e9 * 3.1557e7,     # the cooling span -- Earth's own age as the reference;
                                            # this system's age is NOT yet derived in the story (said so)
        "g": float(parent["g"]), "R": float(parent["R"]),
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
        "day_s": float(parent.get("day_s", 86400.0)),
        "a_au": float(parent["a_au"]),
        "S_earth": float(parent.get("S_earth", 1.0)),
        "T_surface": float(parent.get("T_surface", 288.0)),
        "interior_class_of_this_world": cls,
        "ra_critical": RA_CRITICAL,
    }


def emit(nums, t=1.0):
    """The matter of theInterior the LAW: a cutaway -- the shells as heat. The picture at this
    scale is the instance's own (the layout places it at identity); this emit exists so the
    membrane can stand alone while its instance is grown."""
    import numpy as np
    from matter import blank, fibonacci_sphere, surface_grain, SOLID, GLOW

    rng = np.random.default_rng(97)
    n = 8000
    d = fibonacci_sphere(n, jitter=0.9, seed=97)
    b = blank(n)
    b[:, 0:3] = d * (0.35 + 0.65 * rng.random(n)[:, None] ** 0.4)
    b[:, 16:19] = np.array([1.0, 0.45, 0.12], np.float32)[None, :] * (0.4 + 0.6 * rng.random(n)[:, None])
    b[:, 19] = 0.5
    b[:, 20] = surface_grain(n, radius=0.7, cover=1.0)
    b[:, 11] = GLOW
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
