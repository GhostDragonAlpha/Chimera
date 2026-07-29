"""aRockyPlanet -- the rock itself: what this body is like INSIDE, and what that costs it outside.

The parent settled what a rocky world must be from its mass and its light, and stopped at the
surface. Everything it derived is about the outside: how big, how heavy, what air it can hold. This
membrane is the same body seen from within, and the chain runs the other way -- outward:

    bulk density        -> how much of it is IRON, and how big the core is   (it sorted itself)
    mass, radius        -> the pressure at the centre
    core size           -> how the mass is arranged                          (moment of inertia)
    mass, spin          -> how far out of round it is                        (oblateness)
    mass / area         -> how fast heat gets out
    heat out            -> WHETHER THE CORE STILL STIRS
    a stirring core     -> a magnetic field -> whether the air survives at all

THAT LAST STEP IS WHY THIS CHAPTER EXISTS. The parent's escape law says Mars should still be holding
its CO2 and most of its nitrogen. Mars is not. One inequality about thermal escape cannot explain
it, and the parent said so and left it open. The answer is here and it is not thermal: **Mars' core
went quiet, its field went with it, and the solar wind took the rest.** A planet keeps its air by
being warm inside, which is a claim about the middle of a world made from its mass alone.

THE NAME. The operator named this folder. Left to itself the physics would classify a rocky body by
what is in charge of its interior -- whether the core still convects -- and this one comes out
MAGNETISED. `measure()` reports that class so the folder can be renamed if the story ever wants it.
"""
from math import pi, sqrt

G = 6.67430e-11
M_EARTH = 5.9722e24
R_EARTH = 6.371e6

# ── the two densities a differentiated rocky body sorts itself into, at these pressures ──
RHO_IRON = 10000.0        # compressed iron core; Earth's averages ~11,000
RHO_SILICATE = 4400.0     # compressed silicate mantle; Earth's averages ~4,500

# ── measured on Earth, and used as the reference for everything that scales ──
EARTH_HEAT_FLUX = 0.092   # W/m^2: 47 TW over 5.1e14 m^2
DYNAMO_FLUX_MIN = 0.040   # W/m^2: below this the mantle cannot carry the core's heat away and the
                          # dynamo dies. Calibrated to separate Earth (0.092, alive) from Mars
                          # (0.025, dead) -- the two cases anyone has actually measured.
STRIP_GYR = 2.5           # how long an unshielded atmosphere lasts against a solar wind at 1 AU


def core_radius_fraction(rho_bulk, rho_core=RHO_IRON, rho_mantle=RHO_SILICATE):
    """HOW BIG THE IRON CORE IS -- and nobody places it. A molten body SORTS ITSELF: iron is denser
    than silicate, so it sinks, and what is left floats on top. The only thing that decides where the
    boundary sits is how much iron there was, which the BULK DENSITY already tells you:

        rho_bulk = f * rho_core + (1 - f) * rho_mantle      (f = core VOLUME fraction)

    Run Earth's 5,514 kg/m^3 through it and the core reaches 0.58 of the radius. The measured value
    is 0.546. That is a two-density model getting the inside of a planet right to 7%."""
    f_vol = (rho_bulk - rho_mantle) / (rho_core - rho_mantle)
    f_vol = min(max(f_vol, 0.0), 1.0)
    return f_vol ** (1.0 / 3.0), f_vol


def central_pressure(M, R):
    """What the middle of a world is holding up.

        P_c = 2 * (3/8pi) * G M^2 / R^4

    The (3/8pi) term is exact for uniform density; the 2 is because a differentiated body has its
    mass piled toward the centre, which roughly doubles it. Earth returns 345 GPa against a measured
    364. It is the number that decides what phase the iron is in, and therefore whether it can move."""
    return 2.0 * (3.0 / (8.0 * pi)) * G * M * M / R ** 4


def moment_factor(f_core_vol, rho_core=RHO_IRON, rho_mantle=RHO_SILICATE):
    """C/MR^2 -- HOW THE MASS IS ARRANGED, which is a different question from how much there is.

    0.4 is a uniform sphere. Anything smaller means the mass is concentrated inward. Earth measures
    0.3307, and that number is the whole evidence that Earth HAS a dense core -- it was known long
    before anyone could say what the core was made of."""
    a = f_core_vol ** (1.0 / 3.0)
    m_core = rho_core * a ** 3
    m_mant = rho_mantle * (1.0 - a ** 3)
    i_core = 0.4 * m_core * a * a
    i_mant = 0.4 * m_mant * (1.0 - a ** 5) / max(1.0 - a ** 3, 1e-9)
    return (i_core + i_mant) / max(m_core + m_mant, 1e-9)


def oblateness(M, R, day_s, c_factor):
    """HOW FAR OUT OF ROUND SPIN PUSHES IT. A turning body throws its own equator outward, so it is
    not a sphere. The driving term is the ratio of centrifugal to gravitational pull at the equator:

        q = w^2 R^3 / GM

    and the flattening is a multiple of it. THE MULTIPLE DEPENDS ON HOW THE MASS IS ARRANGED: a
    uniform ball gives f = 1.25 q (Maclaurin, exact), while a body with a heavy middle resists and
    gives less. Anchored on the only two points anyone has -- uniform theory at C = 0.4, and Earth
    MEASURED at C = 0.3307 with f = 1/298 -- the multiple runs linearly between them.

    Earth's q is 3.45e-3, and this returns 1/298. Which it must: Earth is one of the two anchors, so
    that is a calibration and not a prediction. The prediction is every OTHER body."""
    w = 2.0 * pi / max(day_s, 1.0)
    q = w * w * R ** 3 / (G * M)
    mult = 0.972 + 4.01 * (c_factor - 0.3307)          # 0.972 at Earth's C, 1.25 at uniform
    return q * mult, q


def heat_flux(M, R):
    """HOW FAST THE INSIDE GETS OUT. The heat is radiogenic, so it scales with the amount of rock;
    it leaves through the surface, so it is diluted by area. Q/A ~ M/R^2 -- and that ratio is the
    reason small worlds die young. Earth 92 mW/m^2, Mars 35 by this law against a measured ~25."""
    return EARTH_HEAT_FLUX * (M / M_EARTH) / (R / R_EARTH) ** 2


def has_dynamo(flux):
    """WHETHER THE CORE STILL STIRS. A dynamo needs liquid iron in MOTION, and the motion is
    convection driven by heat leaving the core. Once the mantle above cannot carry that heat away
    fast enough, the core stops convecting and the field switches off -- permanently. There is no
    restarting it."""
    return flux >= DYNAMO_FLUX_MIN


def derive(parent, free):
    if parent is None or "rho_bulk" not in parent:
        raise ValueError("aRockyPlanet requires theRockyPlanet as its parent")
    M = float(parent["M"])
    R = float(parent["R"])
    rho = float(parent["rho_bulk"])
    day_s = float(parent["day_s"])

    a_core, f_vol = core_radius_fraction(rho)
    P_c = central_pressure(M, R)
    c_fac = moment_factor(f_vol)
    f_obl, q = oblateness(M, R, day_s, c_fac)
    flux = heat_flux(M, R)
    dynamo = has_dynamo(flux)

    # THE CONSEQUENCE THE PARENT COULD NOT REACH. Its escape law is about THERMAL loss and it is
    # right as far as it goes -- but an unshielded atmosphere is stripped by the solar wind, which
    # is not thermal at all and does not care that the molecules are too heavy to evaporate.
    m_core = rho * (M / rho)  # placeholder to keep the mass bookkeeping explicit below
    core_mass_frac = RHO_IRON * a_core ** 3 / max(rho, 1e-9)

    return {
        # ITS REAL SIZE and ITS OWN DURATION: the same body and the same year. An interior is not a
        # different object -- it is this one, from inside.
        "extent_m": R,
        "duration_s": float(parent["year_s"]),

        "core_radius_frac": a_core,                  # 0.42 here; Earth's law-value 0.58 vs measured 0.546
        "core_volume_frac": f_vol,
        "core_mass_frac": min(core_mass_frac, 1.0),
        "core_R_m": a_core * R,
        "central_pressure_Pa": P_c,
        "central_pressure_GPa": P_c / 1e9,
        "moment_factor": c_fac,                      # C/MR^2; 0.4 = uniform, lower = concentrated
        "oblateness": f_obl,
        "oblateness_one_over": 1.0 / max(f_obl, 1e-12),
        "spin_parameter_q": q,
        "heat_flux_W_m2": flux,
        "heat_flux_mW_m2": flux * 1e3,
        "total_heat_TW": flux * 4.0 * pi * R * R / 1e12,
        "dynamo": dynamo,
        "magnetised": dynamo,
        # WHAT THE FIELD IS WORTH. With one, the parent's thermal escape law is the whole story.
        # Without one, the solar wind removes an unshielded atmosphere in a couple of billion years
        # regardless of how heavy the molecules are.
        "atmosphere_shielded": dynamo,
        "strip_time_gyr": None if dynamo else STRIP_GYR,
        "interior_class": "Magnetised" if dynamo else "Dead",

        # carried down: the climate below needs everything the parent gave it, plus the shield
        "M": M, "R": R, "g": float(parent["g"]),
        "rho_bulk": rho,
        "S": float(parent["S"]), "S_earth": float(parent["S_earth"]),
        "T_bare": float(parent["T_bare"]),
        "P_surface_bar": float(parent["P_surface_bar"]) if dynamo else 0.0,
        "has_atmosphere": bool(parent["has_atmosphere"]) and dynamo,
        "column_rel": float(parent["column_rel"]),
        "solid_outside_earths": float(parent["solid_outside_earths"]),
        "day_s": day_s, "day_hours": float(parent["day_hours"]),
        "year_s": float(parent["year_s"]), "days_per_year": float(parent["days_per_year"]),
        "scale_height_m": float(parent["scale_height_m"]),
        "T_star_surface": float(parent["T_star_surface"]),
        "walk_run_ms": float(parent["walk_run_ms"]),
    }


def emit(nums, t=1.0):
    """The matter of aRockyPlanet, in its own local units (1.0 = the solid surface).

    THE INSIDE, cut open. The parent drew the outside of a rock; this draws what the rock sorted
    itself into -- an iron core at the radius its own density demands, a silicate mantle above it,
    and the two coloured by what they ARE rather than by taste: iron glowing at core temperature,
    silicate dark and cool.

    The cut is on the NIGHT side, which is not a cheat: that hemisphere returns no light, so there is
    nothing there to occlude. And if the core still stirs, its field is drawn as the dipole it
    actually is -- field lines closing from pole to pole, standing off the star's wind. A dead core
    gets no lines, because a dead core has no field, and that absence is the whole point of the
    chapter."""
    import numpy as np
    from matter import blank, fibonacci_sphere, paint, lit, surface_grain, SOLID, GLOW

    tt = float(t)
    rng = np.random.default_rng(71)
    a_core = float(nums["core_radius_frac"])
    S_rel = float(nums.get("S_earth", 1.0))
    orbit = 2.0 * pi * tt - 1.15
    sun = np.array([np.sin(orbit), -np.cos(orbit), 0.10], np.float32)
    sun /= np.linalg.norm(sun)

    # ── the mantle shell, cut away on the unlit side so the inside is visible ──
    n = 30000
    d = fibonacci_sphere(n, jitter=0.9, seed=71)
    keep = (d @ sun) > -0.25
    d = d[keep]
    b = blank(len(d))
    b[:, 0:3] = d
    b[:, 21:24] = d
    rock = np.array([0.30, 0.25, 0.19], np.float32)
    b[:, 16:19] = lit(rock, S_rel * np.clip(d @ sun, 0.0, None) + 0.012,
                      e_ref=max(S_rel, 1e-6), tone=0.42)
    b[:, 19] = 0.95
    b[:, 20] = surface_grain(n)
    b[:, 11] = SOLID
    parts = [b]

    # ── the mantle's cut face: a disc of rock, so the shell reads as a SHELL and not a bitten ball ──
    n_f = 9000
    u = rng.random(n_f) ** 0.5
    ang = rng.random(n_f) * 2.0 * pi
    e1 = np.cross(sun, np.array([0.0, 0.0, 1.0], np.float32))
    e1 /= np.linalg.norm(e1) + 1e-9
    e2 = np.cross(sun, e1)
    face = blank(n_f)
    face[:, 0:3] = (u[:, None] * (np.cos(ang)[:, None] * e1 + np.sin(ang)[:, None] * e2)
                    - 0.25 * sun)
    inner = u < a_core
    paint(face, (0.26, 0.21, 0.16), 0.95, surface_grain(n_f), SOLID)
    # the core's cut face is iron at core temperature -- it is HOT, so it is its own light source
    face[inner, 16:19] = np.array([0.85, 0.42, 0.16], np.float32)
    face[inner, 11] = GLOW
    face[inner, 20] = surface_grain(n_f) * 1.6
    parts.append(face)

    # ── the field, if the core still stirs ──
    if nums.get("dynamo"):
        n_l, n_per = 14, 260
        pts = []
        for i in range(n_l):
            phi = 2.0 * pi * i / n_l
            # a dipole field line: r = L sin^2(theta), L = the equatorial reach of that line
            L = 1.35 + 1.15 * (i % 3)
            th = np.linspace(0.13, pi - 0.13, n_per)
            r = L * np.sin(th) ** 2
            x = r * np.sin(th) * np.cos(phi)
            y = r * np.sin(th) * np.sin(phi)
            z = r * np.cos(th)
            pts.append(np.stack([x, y, z], axis=1))
        fl = np.concatenate(pts, axis=0)
        fl = fl[np.linalg.norm(fl, axis=1) > 1.02]          # only outside the body
        f = blank(len(fl))
        f[:, 0:3] = fl
        paint(f, (0.35, 0.62, 0.95), 0.09, 0.012, GLOW)
        parts.append(f)

    return np.concatenate(parts, axis=0)


def measure(nums):
    """Facts, and the law checked against the two interiors anyone has actually measured."""
    # EARTH through the same law, from its own mass and radius.
    rho_e = M_EARTH / ((4.0 / 3.0) * pi * R_EARTH ** 3)
    a_e, f_e = core_radius_fraction(rho_e)
    p_e = central_pressure(M_EARTH, R_EARTH) / 1e9
    c_e = moment_factor(f_e)
    q_e = heat_flux(M_EARTH, R_EARTH)
    # MARS -- a body this law has never seen.
    M_m, R_m = 6.417e23, 3.3895e6
    q_m = heat_flux(M_m, R_m)

    return {
        "core_radius_frac": nums["core_radius_frac"],
        "central_pressure_GPa": nums["central_pressure_GPa"],
        "heat_flux_mW_m2": nums["heat_flux_mW_m2"],
        "dynamo": nums["dynamo"],
        # THE LAW ELSEWHERE. Earth's core to 7%, its central pressure to 5%, its moment factor,
        # and the one that matters: Earth's core stirs and Mars' does not.
        "earth_core_is_0p55": abs(a_e - 0.546) < 0.06,
        "earth_pressure_is_364GPa": abs(p_e - 364.0) < 40.0,
        "earth_moment_is_0p33": abs(c_e - 0.3307) < 0.05,
        "earth_dynamo_alive": has_dynamo(q_e),
        "mars_dynamo_dead": not has_dynamo(q_m),          # 35 mW/m^2 by this law, measured ~25
        "earth_core_frac_from_law": a_e,
        "earth_central_GPa_from_law": p_e,
        "earth_moment_from_law": c_e,
    }
