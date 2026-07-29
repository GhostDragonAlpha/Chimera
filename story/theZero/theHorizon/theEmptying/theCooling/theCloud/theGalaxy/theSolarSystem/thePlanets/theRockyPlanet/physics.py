"""theRockyPlanet -- what a body made of rock is FORCED to be, once you know its mass and its light.

The parent grew eleven bodies and said which side of the snow line each is on. This membrane is the
LAW for one kind of them, and it stops exactly where the rock stops:

    mass          -> radius        (rock compresses under its own weight)
    mass, radius  -> gravity       (g = GM/R^2)            <- THE NUMBER A BODY WALKS IN
    gravity, R    -> escape speed  (v = sqrt(2GM/R))
    escape, heat  -> WHICH GASES IT CAN HOLD AT ALL        (Jeans: v_esc against the thermal speed)
    what it holds -> the pressure at the bottom of that air

Every step is an equality, not a preference. And the chain ENDS there on purpose: what that air and
that light then DO -- how warm it gets, whether its water is ocean or glacier, and therefore what
colour it is and what it is called -- is a different question with a different answer, and it lives
in the child. The body is what the world IS; the climate is what is happening to it.

Same cut as theStar / aYellowStar: the parent establishes the kind and hands down the numbers that
select; the child derives the class, and the class IS its name.

WHAT IS NOT DERIVED, and is a dial instead: HOW FAST IT SPINS. Rotation is set by the last big
impact, which is chance, not law -- so it is FREE. It is also the one dial with consequences a person
can feel in a single evening: day length, how far the ground cools before dawn, and how hard the
Coriolis force bends the wind.
"""
from math import pi, sqrt

G = 6.67430e-11
K_B = 1.380649e-23
AMU = 1.66053907e-27
SIGMA_SB = 5.670374419e-8
AU = 1.495978707e11
M_EARTH = 5.9722e24
R_EARTH = 6.371e6

EARTH_ALBEDO = 0.30            # what Earth actually returns to space -- the reference for the bare temperature
LEG_M = 0.845                  # a person's leg, measured off this studio's own body. The handoff to walking.

# THE LENS -- picture-only dials, declared so the exaggerations are auditable and reversible.
LENS = {
    "exposure": {"lo": 0.15, "hi": 1.0, "default": 0.42, "label": "film speed", "unit": "gamma"},
    "star_marker": {"lo": 0.0, "hi": 4.0, "default": 1.0, "label": "star marker", "unit": "x"},
}

# THE FREE DIAL. Not derivable from formation: the spin a world ends with is whatever the last giant
# impact left it. Declared here so the engine can put a slider on it.
FREE = {
    "rotation_hours": {"lo": 2.0, "hi": 200.0, "default": 24.0,
                       "label": "day length", "unit": "h"},
}


# ── SIZE, AND THEREFORE WEIGHT ──────────────────────────────────────────────────────────────────
def rocky_radius(M):
    """Rock is not incompressible. Squeeze more of it together and the middle gives, so a world twice
    Earth's mass is NOT twice the volume -- empirically R ~ M^0.27 for an Earth-like iron/silicate
    mix (Seager 2007; Zeng 2016). The disk that grew these bodies assumed a constant density and so
    reported them too big; this is the correction, and it is why gravity here is stronger than the
    disk thought."""
    return R_EARTH * (M / M_EARTH) ** 0.27


def surface_gravity(M, R):
    """THE NUMBER EVERYTHING STANDING ON THIS WORLD IS BUILT AROUND. It is not a setting."""
    return G * M / (R * R)


def escape_speed(M, R):
    """How fast something must be moving upward to never come back. It decides the air."""
    return sqrt(2.0 * G * M / R)


def core_radius(R):
    """Iron sinks and silicate floats, so a molten world SORTS ITSELF. At Earth's iron fraction the
    core reaches ~0.55 of the radius -- and that sorted, convecting interior is what a magnetic field
    is made of. Nobody arranges the layers; density does."""
    return 0.547 * R


# ── LIGHT ARRIVING ──────────────────────────────────────────────────────────────────────────────
def insolation(L, a_au):
    """The light actually arriving, in W/m^2. Everything thermal starts here."""
    return L / (4.0 * pi * (a_au * AU) ** 2)


def bare_temperature(S, albedo):
    """The temperature a ball of rock sits at with NO air: it absorbs what it does not reflect and
    radiates it away, and the balance sets T. (1-A)S/4 = sigma T^4. The child starts from this."""
    return ((1.0 - albedo) * S / (4.0 * SIGMA_SB)) ** 0.25


# ── WHAT AIR IT CAN HOLD ────────────────────────────────────────────────────────────────────────
def exobase_temperature(T_bare, S_rel):
    """The top of an atmosphere is far hotter than the ground -- the star's extreme ultraviolet is
    absorbed up there, and only the top matters for escape. Calibrated on Earth: 255 K bare, ~1000 K
    exobase, scaled by the square root of the arriving flux."""
    return T_bare + 750.0 * sqrt(max(S_rel, 0.0))


def retains(amu, T_exo, v_esc, margin=6.0):
    """WHICH GASES A WORLD CAN KEEP -- one inequality, no chemistry in it.

    A molecule's most probable speed is sqrt(2kT/m); the fast tail of that distribution leaks away,
    and over the age of a system a gas survives only if the escape speed is at least ~6 times it.
    Light molecules are fast, so small worlds lose hydrogen and helium first.

    IT PREDICTS WHAT IT WAS NEVER FITTED TO: run Earth through it and H2 and He are gone while N2,
    O2, H2O and CO2 stay -- which is Earth's actual inventory. Run Mars and it sits on the margin,
    still holding CO2 while the lighter things go, which is Mars' actual story."""
    v_mp = sqrt(2.0 * K_B * T_exo / (amu * AMU))
    return v_esc / v_mp >= margin, v_esc / v_mp


GASES = [("H2", 2.016), ("He", 4.003), ("CH4", 16.04), ("H2O", 18.02),
         ("N2", 28.01), ("O2", 32.00), ("CO2", 44.01)]


def scale_height(T, g, mu=29.0):
    """How thick the air is: H = kT/(mu m_H g). Warmer or weaker gravity means a deeper atmosphere,
    which is a thing you can SEE on a rendered limb -- so it is drawn at its real ratio."""
    return K_B * T / (mu * AMU * g)


def derive(parent, free):
    if parent is None or "worlds" not in parent:
        raise ValueError("theRockyPlanet requires thePlanets as its parent")
    free = free or {}

    # WHICH WORLD. Not chosen: the parent grew a list, and this law applies to the rocky one that
    # receives closest to Earth's light -- the one whose insolation is nearest 1. Move the star or
    # regrow the disk and a DIFFERENT world is selected, automatically.
    L = float(parent["L"])
    rocky = [w for w in parent["worlds"] if not w["icy"]]
    if not rocky:
        raise ValueError("no rocky world in this system")
    S_earth = insolation(3.828e26, 1.0)
    w = min(rocky, key=lambda x: abs(insolation(L, x["a_au"]) / S_earth - 1.0))

    M = float(w["M"])
    a_au = float(w["a_au"])
    R = rocky_radius(M)                                   # compressed, not the disk's constant-density guess
    g = surface_gravity(M, R)
    v_esc = escape_speed(M, R)
    S = insolation(L, a_au)
    S_rel = S / S_earth

    T_bare = bare_temperature(S, EARTH_ALBEDO)            # bare rock: where the child's climate starts
    T_exo = exobase_temperature(T_bare, S_rel)
    kept, ratios = [], {}
    for name, amu in GASES:
        ok, ratio = retains(amu, T_exo, v_esc)
        ratios[name] = ratio
        if ok:
            kept.append(name)
    has_air = ("N2" in kept) or ("CO2" in kept)
    # Pressure at the bottom of the air it kept. Same volatile fraction as Earth by mass, so the
    # column scales as M/R^2 and the pressure as that column times g.
    column_rel = (M / M_EARTH) / (R / R_EARTH) ** 2
    P_bar = column_rel * (g / 9.80665) if has_air else 0.0

    year_s = 2.0 * pi * sqrt((a_au * AU) ** 3 / (G * float(parent["M_star"])))
    day_h = float(free.get("rotation_hours", FREE["rotation_hours"]["default"]))
    day_s = day_h * 3600.0

    return {
        # ITS REAL SIZE: the solid surface. Everything emits at radius ~1 locally, so this is the
        # only place the true scale is written down.
        "extent_m": R,
        # ITS OWN DURATION: one year. t=1 in emit() is one trip around the star -- the longest rhythm
        # a person standing on it would still call a cycle rather than history.
        "duration_s": year_s,

        "a_au": a_au,
        "M": M, "M_earth": M / M_EARTH,
        "R": R, "R_earth": R / R_EARTH,
        "g": g, "g_earth": g / 9.80665,
        "v_escape": v_esc,
        "core_R": core_radius(R), "core_frac": 0.547,
        "rho_bulk": M / (4.0 / 3.0 * pi * R ** 3),

        "L": L,
        "S": S, "S_earth": S_rel,
        "T_bare": T_bare,
        "T_exobase": T_exo,
        "gases_kept": kept,
        "escape_ratios": ratios,
        "has_atmosphere": has_air,
        "P_surface_bar": P_bar,
        "column_rel": column_rel,
        "scale_height_m": scale_height(T_bare, g) if has_air else 0.0,

        "year_s": year_s, "year_days": year_s / 86400.0,
        "day_s": day_s, "day_hours": day_h,
        "days_per_year": year_s / day_s,

        # THE HANDOFF TO A BODY, and the reason this membrane exists at all. A leg is a pendulum, so
        # g fixes how fast it can swing and therefore how fast anything walks here. Fr = v^2/(gL) is
        # the Froude number: 0.5 is where walking gives out and running starts, and it is the SAME
        # 0.5 on every world -- which is what makes it a law instead of a fit. It is also why the
        # Apollo crews bunny-hopped: on the Moon that speed falls to 0.83 m/s.
        "walk_run_ms": sqrt(0.5 * g * LEG_M),
        "leg_swing_s": 2.0 * pi * sqrt(LEG_M / g),
        "leg_m": LEG_M,

        "T_star_surface": float(parent["T_star_surface"]),
        "solid_outside_earths": float(parent["solid_outside_earths"]),
    }


def emit(nums, t=1.0):
    """The matter of theRockyPlanet, in its own local units (1.0 = the solid surface).

    THE BODY, not the weather: a sphere of bare rock with the air it managed to keep, and nothing
    about oceans or ice -- those are the child's, and drawing them here would be this membrane
    claiming a result it did not derive. What IS shown is what the law settled: how big it is, how
    deep its air is (the scale height, at its true ratio, so a weak-gravity world visibly wears a
    puffier atmosphere), and its sorted interior, cut open on the night side where nothing is lit
    anyway.

    Nothing is painted a colour. Each surface is an ALBEDO -- the fraction of arriving light it
    returns -- and what you see is that fraction times the light this world actually receives.

    The movie is ONE YEAR, and the thing that moves is the terminator: the world turns, so the lit
    half sweeps around it."""
    import numpy as np
    from matter import (blank, fibonacci_sphere, paint, lit, blackbody_rgb,
                        surface_grain, SOLID, GLOW)

    tt = float(t)
    rng = np.random.default_rng(31)
    lens = nums.get("_lens", {})
    TONE = float(lens.get("exposure", 0.42))
    MARK = float(lens.get("star_marker", 1.0))
    S_rel = float(nums.get("S_earth", 1.0))
    rock = np.array([0.32, 0.26, 0.20], np.float32)       # dry silicate, albedo ~0.26

    # WHERE THE STAR IS -- and THIS MEMBRANE SHOWS THE ORBIT, NOT THE SPIN.
    #
    # theHumanClock's gearing law, applied. This movie is one YEAR; the world turns 394 times inside
    # it. Drawing the spin here strobes 394 sunrises past in a few seconds -- far outside the band a
    # person can resolve, so it reads as flicker, not as a day. The rhythm that FITS a year-long
    # movie is the orbit: one slow turn of the star's direction as the planet goes round it.
    # The day is a faster clock and belongs to a faster membrane -- to the ground, where standing
    # still and watching the sun cross is exactly the right length of film.
    #
    # The 0.6 rad offset is DECLARED: it puts the terminator inside the default view, because a fully
    # lit face reads flat and a fully dark one reads like nothing at all.
    orbit = 2.0 * pi * tt - 1.15      # ~65 deg off the default eye: a sphere needs its shadow line
    sun = np.array([np.sin(orbit), -np.cos(orbit), 0.10], np.float32)
    sun /= np.linalg.norm(sun)

    # ── the solid surface ──
    n = 30000
    d = fibonacci_sphere(n, jitter=0.9, seed=31)
    b = blank(n)
    b[:, 0:3] = d
    b[:, 21:24] = d
    # Lambert's cosine law: a patch receives S*cos(angle to the star), and nothing on the night side.
    # This is the whole reason a planet reads as ROUND rather than as a disc.
    cosang = np.clip(d @ sun, 0.0, None)
    # EXPOSURE IS AN INSTRUMENT SETTING, AND IT IS DECLARED HERE. e_ref is the irradiance the render
    # calls "correct exposure", and leaving it at 1.0 (one solar constant, at Earth) rendered this
    # world at a measured 47->15 grey ramp: the terminator was physically right and simply too dark
    # to read. A camera pointed at a planet exposes FOR that planet, so the reference is the light
    # this world actually receives. The falloff across the disk is unchanged -- only the film speed.
    b[:, 16:19] = lit(rock, S_rel * cosang + 0.010, e_ref=max(S_rel, 1e-6), tone=TONE)   # the floor is scattered skylight
    b[:, 19] = 0.95
    b[:, 20] = surface_grain(n)          # closes the surface by arithmetic, not by eye
    b[:, 11] = SOLID
    parts = [b]

    # ── the interior it sorted itself into, shown on the unlit side ──
    # A CUTAWAY IS NOT A CHEAT HERE: the night hemisphere returns no light, so there is nothing to
    # occlude. Iron below, silicate above, at the radius ratio density forces.
    n_i = 7000
    di = fibonacci_sphere(n_i, jitter=1.0, seed=33)
    keep = (di @ sun) < -0.15
    di = di[keep]
    rr = float(nums.get("core_frac", 0.547)) * (rng.random(len(di)) ** (1.0 / 3.0))
    ib = blank(len(di))
    ib[:, 0:3] = di * rr[:, None]
    paint(ib, (0.55, 0.30, 0.16), 0.30, 0.060, GLOW)      # iron at core temperature, seen as heat  # x6: GLOW no longer carries a hidden multiplier (gpu_pipeline._profile)
    parts.append(ib)

    # ── the air, if it kept any: a shell as deep as its own scale height says ──
    if nums.get("has_atmosphere"):
        h_rel = float(nums["scale_height_m"]) / float(nums["extent_m"])
        n_a = 9000
        da = fibonacci_sphere(n_a, jitter=1.0, seed=32)
        rad = 1.0 + h_rel * (14.0 * rng.random(n_a) ** 1.6)      # ~14 scale heights to space
        a = blank(n_a)
        a[:, 0:3] = da * rad[:, None]
        # AIR IS BLUE BECAUSE OF THE PHYSICS, not because skies are blue: Rayleigh scattering goes as
        # 1/lambda^4, so short wavelengths are turned aside far more. That ratio IS this colour.
        ca = np.clip(np.array([0.30, 0.52, 1.00]) * (0.35 + 0.9 * float(nums["P_surface_bar"])), 0, 1)
        cosa = np.clip(da @ sun, 0.0, None)
        a[:, 16:19] = (ca[None, :] * (0.08 + 0.92 * cosa)[:, None]).astype(np.float32)
        a[:, 19] = 0.035
        a[:, 20] = 0.0270      # the grain must be finer than the shell is thick, or blur IS the sky  # x6: GLOW no longer carries a hidden multiplier (gpu_pipeline._profile)
        a[:, 11] = GLOW
        parts.append(a)

    # ── the star it is lit BY, drawn in the direction it actually is ──
    # NO STAR-BALL. It used to be drawn here as a "marker" at 1.3 planetary radii -- and at that
    # distance it is not a star, it is a MOON. This story has never derived a moon, so putting a
    # moon-shaped object in the frame is the render asserting a body that does not exist, which is
    # the one thing this whole method exists to prevent. Its true angular size from the ground is a
    # quarter of a degree at 28,000 radii: off-screen and sub-pixel at any framing that shows the
    # planet. WHERE THE STAR IS, IS ALREADY BEING SAID -- by the terminator, by which limb is bright,
    # by the length of the shadow. A light source is told by its light. Nothing replaces it.
    return np.concatenate(parts, axis=0)


def measure(nums):
    """Facts. The first four are this world's; the rest are the LAW run on worlds it was never fitted
    to, which is the only test of a derivation that means anything."""
    R_e = rocky_radius(M_EARTH)
    g_e = surface_gravity(M_EARTH, R_e)
    v_e = escape_speed(M_EARTH, R_e)
    S_e = insolation(3.828e26, 1.0)
    T_exo_e = exobase_temperature(bare_temperature(S_e, EARTH_ALBEDO), 1.0)
    earth_keeps = [n for n, amu in GASES if retains(amu, T_exo_e, v_e)[0]]

    M_m = 6.417e23                                        # Mars, a world this law has never seen
    R_m = rocky_radius(M_m)
    v_m = escape_speed(M_m, R_m)
    S_m = insolation(3.828e26, 1.524)
    T_exo_m = exobase_temperature(bare_temperature(S_m, 0.25), S_m / S_e)
    mars_keeps = [n for n, amu in GASES if retains(amu, T_exo_m, v_m)[0]]

    return {
        "g_ms2": nums["g"],
        "v_escape_kms": nums["v_escape"] / 1e3,
        "P_surface_bar": nums["P_surface_bar"],
        "walk_run_ms": nums["walk_run_ms"],
        # THE LAW, TESTED ELSEWHERE.
        "earth_g_from_law": abs(g_e - 9.80665) < 0.3,     # 9.81 from M and the compression law alone
        "earth_loses_H2_He": ("H2" not in earth_keeps) and ("He" not in earth_keeps),
        "earth_keeps_air": all(x in earth_keeps for x in ("N2", "O2", "CO2", "H2O")),
        "mars_keeps_CO2": "CO2" in mars_keeps,            # it does, and it is why Mars still has any air
        "mars_loses_more_than_earth": len(mars_keeps) < len(earth_keeps),
        # Froude closes on Earth: 2.0 m/s is the measured walk-run transition for a human leg.
        "earth_walk_run_is_2ms": abs(sqrt(0.5 * 9.80665 * LEG_M) - 2.04) < 0.05,
    }
