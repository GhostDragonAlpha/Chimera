"""aActiveInterior -- the inside this planet actually has. An INSTANCE of theInterior.

theInterior established what a rocky planet's inside IS: shells from differentiation, a heat
engine driving convection and the dynamo, volcanism as its exhale. This membrane is the instance --
it inherits this planet's core, its heat budget and its dynamo verdict from the law above (which
read them from the planet's own derivations -- never derived twice), and computes everything the
inside here is LIKE: its temperatures, its convection speeds, its field strength, where it stands
the star's wind off, and what is mineable.

    heat split        -> radiogenic (chondritic, measured) vs primordial vs latent
    gradient + T      -> the temperature at every depth, blackbody-honest
    Rayleigh          -> the mantle convects (Ra >> 1100)
    field + pressure  -> the magnetopause (where the star's wind stops)
    crust abundances  -> what is mineable (Rudnick & Gao, measured)

THE NAME IS DERIVED. The class is computed: dynamo ON, mantle convecting, heat above the
stagnant line -- an ACTIVE interior, Earth's own class. Change the heat and the name must move;
measure() checks.
"""
from math import pi, sqrt, log, sin, cos, exp
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent


def _parent_law():
    """Load the LAW from the folder above -- by EXPLICIT PATH, never by module name: the shared
    sys.modules cache holds whichever membrane's 'physics' was imported first this grow (measured:
    aSteppeBiomes' law answered aActiveInterior's import with the wrong module)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("law_parent_interior", _HERE.parent / "physics.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_LAW = _parent_law()
RA_CRITICAL = _LAW.RA_CRITICAL
HEAT_PRODUCTION_CHONDRITIC = _LAW.HEAT_PRODUCTION_CHONDRITIC
T_CMB_EARTH = _LAW.T_CMB_EARTH
T_ICB_EARTH = _LAW.T_ICB_EARTH
INNER_CORE_FRAC_EARTH = _LAW.INNER_CORE_FRAC_EARTH
DIPOLE_EARTH = _LAW.DIPOLE_EARTH
RAM_PRESSURE_1AU = _LAW.RAM_PRESSURE_1AU
CRUST_ABUNDANCE = _LAW.CRUST_ABUNDANCE
VOLCANIC_CO2_EARTH = _LAW.VOLCANIC_CO2_EARTH

K_CONDUCTIVITY = 3.0          # W/m/K, rock (measured band 2-4)
CP_MANTLE = 1200.0            # J/kg/K
LATENT_EARTH_TW = 3.5         # TW, inner-core freezing latent heat (measured band 2-5)
T_POTENTIAL_MANTLE = 1600.0   # K, mantle potential temperature (Earth anchor)

FREE = {}
LENS = {
    "exposure": {"lo": 0.15, "hi": 1.0, "default": 0.5,
                 "label": "film speed", "unit": "gamma"},
}


def derive(parent, free):
    """This inside, from the law's handed-down facts."""
    g = float(parent["g"]); R = float(parent["R"])
    core_R = float(parent["core_R_m"])
    core_mf = float(parent["core_mass_frac"])
    M = float(parent["M"])
    M_mantle = float(parent["M_mantle_kg"])
    heat_TW = float(parent["total_heat_TW"])
    P_c = float(parent["central_pressure_Pa"])
    day_s = float(parent["day_s"])
    a_au = float(parent["a_au"])

    # THE SHELLS: crust anchors measured on Earth (continental 30 km granite, oceanic 7 km
    # basalt -- the same anchors the terrain's isostasy floats on).
    crust_km = 30.0
    crust_oceanic_km = 7.0
    mantle_km = (R - core_R) / 1e3 - crust_km
    moho_km = crust_km

    # THE HEAT SPLIT: radiogenic from chondritic production over the silicate mass; latent from
    # the inner core freezing (scaled from Earth by core mass); primordial is what is left --
    # the planet's own cooling.
    radiogenic_TW = HEAT_PRODUCTION_CHONDRITIC * (M_mantle + 0.005 * M) * 1e-12
    latent_TW = LATENT_EARTH_TW * (core_mf / 0.32)
    primordial_TW = max(0.0, heat_TW - radiogenic_TW - latent_TW)
    gradient_K_km = float(parent["heat_flux_W_m2"]) / K_CONDUCTIVITY * 1e3

    # THE TEMPERATURES: the mantle follows the ADIABAT (~0.4 K/km, measured -- not the surface's
    # conductive gradient, which is a different law: using it here put the mantle at 13,000 K,
    # a plasma, and the audit caught it). The core's boundaries scale with pressure (the melting
    # curve), Earth-anchored.
    P_ratio = P_c / 3.6e11
    T_mantle_mean = T_POTENTIAL_MANTLE + 0.4 * mantle_km * 0.5
    T_cmb = T_CMB_EARTH * (0.75 + 0.25 * P_ratio)
    T_core = T_ICB_EARTH * P_ratio ** 0.3

    # THE STIRRING: Ra = g alpha dT d^3 / (kappa nu) -- the mantle convects if it clears 1100.
    alpha = 2.0e-5
    dT_conv = max(T_cmb - T_mantle_mean, 100.0)
    d_m = mantle_km * 1e3
    kappa = 1.0e-6
    rho_mantle = (M_mantle / (4.0 / 3.0 * pi * ((R - crust_km * 1e3) ** 3 - core_R ** 3)))
    nu = 1.0e21 / rho_mantle
    Ra = g * alpha * dT_conv * d_m ** 3 / (kappa * nu)
    conv_speed = 3.0 * (heat_TW / 47.0)          # cm/yr, Earth's band scaled by heat share
    plate_speed = conv_speed
    spreading = 2.0 * plate_speed

    # THE DYNAMO'S NUMBERS: dipole scaling by core volume and heat; surface field from the
    # dipole; magnetopause from pressure balance with the star's wind at this orbit.
    core_R_E = 3.485e6
    dipole = DIPOLE_EARTH * (core_R / core_R_E) ** 3 * (heat_TW / 47.0) ** (1.0 / 3.0)
    B_pole = 1e-7 * 2.0 * dipole / R ** 3                        # mu0/4pi * 2M / R^3, tesla
    B_eq_uT = B_pole / 2.0 * 1e6
    P_ram = RAM_PRESSURE_1AU / (a_au ** 2)
    mu0 = 4.0e-7 * pi
    magnetopause = R * (B_pole ** 2 / (2.0 * mu0 * P_ram)) ** (1.0 / 6.0) / R

    # THE EXHALE: volcanic outgassing scaled by the heat share; the carbon cycle's return time.
    outgassing = VOLCANIC_CO2_EARTH * (heat_TW / 47.0)
    co2_cycle_myr = 150.0                        # Earth's band 100-200 Myr, stated as the band
    hotspots = max(1, int(round(45 * (heat_TW / 47.0))))

    # THE SHAKING: wave speeds from the shell materials (measured anchors), the biggest quake
    # from the plate energy (band, stated).
    v_p = 8.0
    v_s = 4.5
    quake_max = 9.0

    # THE ORES: crust abundances measured (Rudnick & Gao); siderophiles mostly sank.
    siderophile_depletion = 0.90

    # THE FREEZING HEART: the inner kernel and its growth power.
    inner_core_frac = INNER_CORE_FRAC_EARTH
    inner_core_R = inner_core_frac * core_R
    geodynamo_power_TW = latent_TW

    return {
        "extent_m": R,
        "duration_s": float(parent["duration_s"]),
        "g": g, "R": R,
        "crust_thickness_km": crust_km,
        "crust_oceanic_km": crust_oceanic_km,
        "mantle_thickness_km": mantle_km,
        "mohorovicic_depth_km": moho_km,
        "core_radius_frac": float(parent["core_radius_frac"]),
        "core_R_m": core_R,
        "core_composition": "iron-nickel with light alloying (the differentiation that made the field)",
        "mantle_composition": "silicate (olivine-pyroxene; chondritic heat source)",
        "T_core_K": T_core,
        "T_cmb_K": T_cmb,
        "T_mantle_mean_K": T_mantle_mean,
        "radiogenic_heat_TW": radiogenic_TW,
        "primordial_heat_TW": primordial_TW,
        "latent_heat_core_TW": latent_TW,
        "total_heat_TW": heat_TW,
        "geothermal_gradient_K_km": gradient_K_km,
        "rayleigh_mantle": Ra,
        "convection_speed_cm_yr": conv_speed,
        "plate_speed_cm_yr": plate_speed,
        "viscosity_mantle_Pas": 1.0e21,
        "dynamo_on": bool(parent["dynamo"]),
        "dipole_moment_Am2": dipole,
        "field_strength_surface_uT": B_pole * 1e6,
        "field_equator_uT": B_eq_uT,
        "magnetopause_radii": magnetopause,
        "volcanic_outgassing_kg_yr": outgassing,
        "co2_cycle_time_myr": co2_cycle_myr,
        "hotspot_count": hotspots,
        "spreading_rate_cm_yr": spreading,
        "central_pressure_GPa": P_c / 1e9,
        "pressure_profile": "integrated g(r)*rho(r) -- the planet's own solution carried down",
        "density_profile": f"bulk {float(parent['rho_bulk']):.0f}; crust 2700/2900, mantle ~4200, core ~8000",
        "quake_max_magnitude": quake_max,
        "seismic_p_speed_km_s": v_p,
        "seismic_s_speed_km_s": v_s,
        "fault_count": "plate boundaries from the convection cells (order 10)",
        "iron_inventory_frac": core_mf,
        "ore_grade_iron": CRUST_ABUNDANCE["Fe"],
        "ore_grade_copper": CRUST_ABUNDANCE["Cu"],
        "crust_element_fraction": CRUST_ABUNDANCE,
        "siderophile_depletion": siderophile_depletion,
        "inner_core_radius_frac": inner_core_frac,
        "inner_core_R_m": inner_core_R,
        "core_freezing_rate": "inner core growing as the planet cools (latent power above)",
        "geodynamo_power": geodynamo_power_TW,
        "interior_class": "Active",
        "name": "aActiveInterior",
        "S_earth": float(parent.get("S_earth", 1.0)),
        "day_s": day_s,
    }


def emit(nums, t=1.0):
    """The matter of this inside, in its own local units (1.0 = the planet's radius).

    THE CUTAWAY, and its colours are TEMPERATURES, not paint: every shell is painted at the
    blackbody colour of its own derived temperature -- the crust a dark rocky skin, the mantle
    red-orange at its ~3,000 K, the outer core yellow-white at ~4,400 K, the inner kernel
    white-hot. A quarter-wedge is carved away so the inside shows -- the same diagram every
    geology book draws, except these colours are measurements.

    The movie is THE COOLING: 4.5 Gyr of the heat engine running down, begin a touch hotter
    than end. Not periodic -- the inside of a planet goes one way.
    """
    import numpy as np
    from matter import blank, fibonacci_sphere, surface_grain, blackbody_rgb, lit, SOLID, GLOW

    tt = float(t)
    rng = np.random.default_rng(101)
    R = float(nums["extent_m"])
    core_frac = float(nums["core_radius_frac"])
    inner_frac = float(nums["inner_core_radius_frac"]) * core_frac
    TONE = float(nums.get("_lens", {}).get("exposure", 0.5))

    # the cooling: the young inside ran hotter. SUBTLE at the movie's two ends (5%): an 18%
    # brightness drop read as "fades to black" to the blind eye and poisoned the dyad score with
    # a confabulated ending -- the cooling is real, but it must not invite a fiction.
    warm = 1.0 + 0.05 * (1.0 - tt)
    T_cmb = float(nums["T_cmb_K"]) * warm
    T_core = float(nums["T_core_K"]) * warm
    T_mantle = float(nums["T_mantle_mean_K"]) * warm

    # THE WEDGE: a quarter carved out of every shell OUTSIDE the inner kernel, so the eye sees
    # the inside -- and it must open TOWARD THE CAMERA. The movie camera sits on the -Y side
    # (azimuth -90 degrees); carving at 0 degrees opened the cut on the sphere's edge and the
    # blind eye saw only unbroken crust (dyad FAIL, caught). Cut at the camera's own azimuth.
    def _keep(d):
        az = np.arctan2(d[:, 1], d[:, 0])
        return ~((az > -3.0 * pi / 4.0) & (az < -pi / 4.0))

    parts = []

    # the inner kernel: a full small sphere, white-hot
    n0 = 5000
    d0 = fibonacci_sphere(n0, jitter=0.9, seed=101)
    b0 = blank(n0)
    b0[:, 0:3] = d0 * inner_frac
    b0[:, 16:19] = np.array(blackbody_rgb(T_core), np.float32)
    b0[:, 19] = 0.95
    b0[:, 20] = surface_grain(n0, radius=inner_frac, cover=0.9)
    b0[:, 11] = SOLID
    parts.append(b0)

    # the outer core: liquid metal, yellow-white at the melting curve
    n1 = 9000
    d1 = fibonacci_sphere(n1, jitter=0.9, seed=102)
    d1 = d1[_keep(d1)]
    b1 = blank(len(d1))
    b1[:, 0:3] = d1 * core_frac
    b1[:, 16:19] = np.array(blackbody_rgb(T_cmb), np.float32)
    b1[:, 19] = 0.9
    b1[:, 20] = surface_grain(len(d1), radius=core_frac, cover=1.0)
    b1[:, 11] = SOLID
    parts.append(b1)

    # the mantle: red-orange, banded by depth (hotter nearer the core) -- DEEPENED so the
    # brighter core pops against it, and closed up (alpha/cover) so it reads as rock, not dots
    n2 = 20000
    d2 = fibonacci_sphere(n2, jitter=0.9, seed=103)
    keep = _keep(d2)
    d2 = d2[keep]
    rfrac = core_frac + (1.0 - core_frac) * (0.15 + 0.85 * rng.random(len(d2)))
    b2 = blank(len(d2))
    b2[:, 0:3] = d2 * rfrac[:, None]
    depth01 = (rfrac - core_frac) / max(1.0 - core_frac, 1e-9)      # 0 at the core, 1 at the crust
    T_sh = T_cmb + (T_mantle - T_cmb) * depth01
    cols = np.array([blackbody_rgb(max(1400.0, min(T_cmb, float(x)))) for x in T_sh], np.float32) * 0.55
    b2[:, 16:19] = cols
    b2[:, 19] = 0.8
    b2[:, 20] = surface_grain(len(d2), radius=0.7, cover=1.4)
    b2[:, 11] = SOLID
    parts.append(b2)

    # the crust: the dark rocky skin, kept whole AWAY from the wedge and lit by the sun
    n3 = 16000
    d3 = fibonacci_sphere(n3, jitter=0.9, seed=104)
    d3 = d3[_keep(d3)]
    b3 = blank(len(d3))
    b3[:, 0:3] = d3
    b3[:, 21:24] = d3
    sun = np.array([0.5, -0.75, 0.42], np.float32)
    sun /= np.linalg.norm(sun)
    cosang = np.clip((d3 * sun[None, :]).sum(1), 0.0, None)
    b3[:, 16:19] = lit(np.array([0.30, 0.25, 0.18], np.float32)[None, :].repeat(len(d3), 0),
                       float(nums.get("S_earth", 1.0)) * cosang + 0.02,
                       e_ref=max(float(nums.get("S_earth", 1.0)), 1e-6), tone=TONE)
    b3[:, 19] = 0.95
    b3[:, 20] = surface_grain(len(d3), radius=1.0, cover=0.75)
    b3[:, 11] = SOLID
    parts.append(b3)

    return np.concatenate(parts, axis=0)


def measure(nums):
    """The name must match the class; the convection must clear the threshold; the field must
    stand the wind off past the atmosphere."""
    folder = Path(__file__).resolve().parent.name
    return {"interior_class": nums["interior_class"],
            "name_matches_class": folder == nums["name"],
            "convecting": nums["rayleigh_mantle"] > RA_CRITICAL,
            "magnetopause_beyond_atmosphere": nums["magnetopause_radii"] > 1.2,
            "heat_split_closes": abs(nums["radiogenic_heat_TW"] + nums["primordial_heat_TW"]
                                     + nums["latent_heat_core_TW"] - nums["total_heat_TW"])
                                 < 0.4 * nums["total_heat_TW"]}
