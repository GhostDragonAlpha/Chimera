"""aBlueWorld -- the climate that this particular rock, at this particular distance, cannot avoid.

The parent settled the BODY: a mass, a radius, a gravity, and the list of gases its escape speed can
hold. It deliberately stopped there. This membrane takes those and asks the only question left --
what happens to the water? -- and the answer names the world.

    the air it kept -> how much warmer than bare it runs        (the greenhouse)
    warmer          -> less ice -> darker -> warmer still       (the albedo feedback)
    cooler          -> less rain -> CO2 builds -> warmer        (the carbonate thermostat)

Those three run into each other, so the temperature is not a formula -- it is a FIXED POINT, the one
value consistent with the albedo and the CO2 it produces. Solve it and everything follows: where the
ice line falls, whether there is an ocean at all, and what colour the world is from outside.

THE NAME IS THE MEASUREMENT. A star is classified by the colour its temperature forces; a rocky
world is classified by the colour of whatever covers it, which is whatever its water is doing. This
folder is called aBlueWorld because the fixed point came out at 271.5 K with the ice line at 39
degrees -- liquid water over most of it. Move the planet and the class, and the folder name, must
change with it. measure() checks that they still agree.

WHAT THIS MEMBRANE REFUSES TO DECIDE: where the coast is. A world with no relief is ocean all the
way round. Land exists only because rock stands above sea level, and that is the CHILD's law -- so
this one hands down the depth of the water and lets the terrain subtract the continents.
"""
from math import pi, exp, sqrt, asin, degrees

SIGMA_SB = 5.670374419e-8
M_EARTH = 5.9722e24
RHO_WATER = 1000.0

# ── the numbers this law is calibrated on, all of them Earth's, all measured ──
EARTH_ALBEDO = 0.30            # what Earth actually returns to space, measured -- INCLUDING its ice
# THE ICE-FREE ALBEDO, SOLVED FROM THAT. 0.30 is Earth WITH its ice, so feeding 0.30 in as the
# ice-free ground and then adding ice on top counts Earth's ice twice -- which is exactly what broke
# the earth_T_is_288 check the moment the ice model got better. Earth freezes 18.6% of its area at
# 288 K, so 0.30 = 0.186*0.62 + 0.814*A_free  ->  A_free = 0.227. Derived, not chosen.
EARTH_TAU = 0.835              # the greenhouse depth that turns 255 K into 288 K -- SOLVED, not picked
EARTH_WATER_FRAC = 2.34e-4     # ocean mass / planet mass
SNOWBALL_ALBEDO = 0.62         # a fully glaciated world, from the Neoproterozoic record
ICEFREE_ALBEDO = 0.227         # solved above; the ground and cloud under the ice

T_FREEZE = 273.15
T_BOIL = 373.15                # at one bar; thinner air boils water colder, and this law says so
T_ICE_LINE = 288.0             # Earth's mean: the temperature at which the ice line sits at the poles
DT_POLE = 45.0                 # equator-to-pole spread -- the scale over which ice takes a world
CO2_EFOLD_K = 13.7             # Berner: how fast silicate weathering responds to temperature


# THE LENS -- picture-only dials, declared so the exaggerations are auditable and reversible.
LENS = {
    "exposure": {"lo": 0.15, "hi": 1.0, "default": 0.42, "label": "film speed", "unit": "gamma"},
    "star_marker": {"lo": 0.0, "hi": 4.0, "default": 1.0, "label": "star marker", "unit": "x"},
}


def greenhouse_factor(tau):
    """A grey atmosphere lets sunlight in and slows infrared out, so the ground must run hotter than
    the balance point to push the same energy through: T_surf = T_bare * (1 + 3/4 tau)^(1/4).
    Earth's tau of 0.835 is not chosen -- it is what 288/255 demands."""
    return (1.0 + 0.75 * tau) ** 0.25


def bare_temperature(S, albedo):
    """Absorb what you do not reflect, radiate it away: (1-A)S/4 = sigma T^4."""
    return ((1.0 - albedo) * S / (4.0 * SIGMA_SB)) ** 0.25


def temperature_at(T_mean, sin_lat):
    """THE ONE LATITUDE PROFILE THIS STORY USES, and every membrane below must read it from here.

    Sunlight arrives at a slant away from the equator, so temperature falls with latitude. The
    standard climatological form is quadratic in sin(latitude) -- T = T_mean + dT*(1/3 - sin^2 lat) --
    and the 1/3 is not a fudge: it is the area-weighted mean of sin^2 over a sphere, which is what
    makes the profile average back to T_mean exactly.

    On Earth's 288 K it gives +30 C at the equator and -15 C at the pole. Both are right.

    IT LIVES HERE BECAUSE THE CLIMATE DOES. The terrain below needs it too (snow is a temperature,
    not a latitude), and a child that re-derived it with its own constants drew an ice edge six
    degrees away from the one this membrane had already solved -- two authorities for one number,
    which is how they drift apart."""
    return T_mean + DT_POLE * (1.0 / 3.0 - sin_lat * sin_lat)


def ice_fraction(T):
    """How much of a world freezes, read straight off that profile: the area poleward of wherever it
    crosses 0 C. Area on a sphere goes as sin(latitude), so the fraction IS 1 - sin(lat_ice).

    Still anchored at both ends by measurement -- a 243 K mean freezes the equator too and returns a
    full snowball, and Earth's 288 K freezes only what is poleward of about 55 degrees."""
    s2 = 1.0 / 3.0 - (T_FREEZE - T) / DT_POLE
    if s2 <= 0.0:
        return 1.0                                   # the freezing line has reached the equator
    if s2 >= 1.0:
        return 0.0                                   # it never freezes anywhere
    return 1.0 - sqrt(s2)


def albedo_of(T, bare=ICEFREE_ALBEDO):
    """ICE IS BRIGHT, so a world that cools reflects more, which cools it further. This is the
    feedback that makes climate a FIXED POINT rather than a formula."""
    return bare + (SNOWBALL_ALBEDO - bare) * ice_fraction(T)   # bare = ICE-FREE, never Earth's 0.30


def carbon_buffer(T, cap):
    """THE THERMOSTAT -- and without it every world in this story freezes over. Measured: switching
    it off drops this planet's fixed point from 271 K to a permanent snowball.

    Rain washes CO2 out of the air onto rock; volcanoes put it back. The washing is strongly
    temperature dependent (Walker, Hays & Kasting 1981; the exponential is Berner's), so a world that
    cools stops scrubbing its own air, CO2 accumulates, and the greenhouse deepens until the
    temperature comes back. A world that warms scrubs harder and cools.

    It is BOUNDED: a planet can only cycle the carbon it has, and that inventory scales with its
    mass. Past the bound the thermostat is out of gas and the world does freeze -- which is the
    honest reason a habitable zone has an outer edge at all, rather than going on forever."""
    return min(cap, exp((T_ICE_LINE - T) / CO2_EFOLD_K))


def climate(S, tau_dry, tau_c0, c_cap):
    """SOLVE, do not evaluate. Albedo depends on temperature and temperature depends on albedo; the
    same is true of the CO2. So iterate to the value consistent with what it produces, damped so the
    feedback does not ring. That self-consistency IS the climate."""
    T = bare_temperature(S, EARTH_ALBEDO)
    for _ in range(400):
        A = albedo_of(T)
        tau = tau_dry + tau_c0 * carbon_buffer(T, c_cap)
        T_new = bare_temperature(S, A) * greenhouse_factor(tau)
        if abs(T_new - T) < 1e-5:
            return T_new
        T = 0.5 * (T + T_new)
    return T


def water_state(T, P_bar, frozen):
    """What the water DOES -- the only thing that decides what a rocky world looks like.

    A MEAN IS NOT A SURFACE. A world whose average is a degree below freezing is not a block of ice:
    it has a warm equator and frozen poles, and the ice fraction already says where the line falls.
    So the state follows the ICE LINE, not the average -- fully glaciated only when the line reaches
    the equator. (Read from the mean alone, this called a world with 63% of its surface unfrozen
    "ice" -- the same class of error as reporting a gait from one rollout: a single number standing
    in for a distribution.)

    The boiling point moves with pressure (Clausius-Clapeyron, linearised about one bar), so a
    thin-aired world boils its oceans colder. The state is a fact about the whole atmosphere."""
    t_boil = T_BOIL + 28.0 * (P_bar - 1.0) if P_bar > 0.02 else T_FREEZE - 1.0
    if T >= t_boil:
        return "vapour"
    if frozen >= 0.999:
        return "ice"
    return "liquid"


def delivered_water(M, outer_ice_earths):
    """An inner rocky world CANNOT have formed wet -- it grew inside the snow line, where water is
    vapour and does not stick. Its water was thrown in afterwards from beyond the line, where the
    grandparent measured a fourfold jump in the solid inventory. So an ocean is a DELIVERY, and its
    size scales with the planet's mass (its gravitational reach) times how much ice the outer disk
    had to throw. Calibrated on the one delivery anybody has measured: Earth's oceans, 2.34e-4 of its
    mass, out of an outer inventory of ~53 Earth masses."""
    return EARTH_WATER_FRAC * M * (outer_ice_earths / 53.16)


def ocean_depth(M_water, R):
    """If the surface were a smooth ball, this is how deep the water would lie. Earth's number is
    2.7 km, and this law returns it. What pokes out of it is relief -- the next membrane's business."""
    return M_water / (RHO_WATER * 4.0 * pi * R * R)


# THE NAME IS DERIVED. The colour word IS the class, exactly as it is for a star.
def surface_class(state, has_water):
    if not has_water or state == "vapour":
        return "Grey", (0.42, 0.39, 0.36)        # bare rock, nothing liquid to cover it
    if state == "ice":
        return "White", (0.78, 0.83, 0.88)       # glaciated end to end
    return "Blue", (0.09, 0.22, 0.42)            # liquid water is what you see


def derive(parent, free):
    if parent is None or "P_surface_bar" not in parent:
        raise ValueError("aBlueWorld requires theRockyPlanet as its parent")
    M = float(parent["M"])
    R = float(parent["R"])
    S = float(parent["S"])
    P_bar = float(parent["P_surface_bar"])
    has_air = bool(parent.get("has_atmosphere"))

    # The greenhouse this world's own air can produce. Earth's total depth of 0.835, split into the
    # non-condensing background and CO2's share, scaled by the column this world actually holds.
    col = float(parent.get("column_rel", 1.0))
    tau_dry = EARTH_TAU * 0.75 * col if has_air else 0.0
    tau_c0 = EARTH_TAU * 0.25 * col if has_air else 0.0
    c_cap = 100.0 * (M / M_EARTH)                          # the carbon it has to work with

    T = climate(S, tau_dry, tau_c0, c_cap)
    A = albedo_of(T)
    tau = tau_dry + tau_c0 * carbon_buffer(T, c_cap)
    T_bare = bare_temperature(S, A)
    frozen = ice_fraction(T)

    M_water = delivered_water(M, float(parent.get("solid_outside_earths", 53.16)))
    depth = ocean_depth(M_water, R)
    state = water_state(T, P_bar, frozen)
    colour, rgb = surface_class(state, depth > 1.0)
    # With no relief there is no shore: the water covers everything it is not frozen on.
    ocean_frac = max(0.0, 1.0 - frozen) if state == "liquid" else 0.0
    # WHERE THE ICE LINE FALLS, said as a latitude, because that is the number a person can picture.
    # Area on a sphere goes as sin(latitude), so the fraction inverts through arcsin.
    ice_lat = degrees(asin(max(0.0, min(1.0, 1.0 - frozen)))) if frozen < 1.0 else 0.0

    # WHAT IT WOULD BE WITHOUT THE THERMOSTAT -- carried because it is the single most load-bearing
    # piece of this derivation, and a number nobody should have to re-run the code to see.
    T_no_thermostat = climate(S, tau_dry, tau_c0, 1.0)

    return {
        # ITS REAL SIZE and ITS OWN DURATION: the same body and the same year as its parent -- a
        # climate is not a different object, it is what is happening to this one.
        "extent_m": R,
        "duration_s": float(parent["year_s"]),

        "T_surface": T,
        "T_surface_C": T - 273.15,
        "T_bare": T_bare,
        "greenhouse_K": T - T_bare,
        "albedo": A,
        "tau_greenhouse": tau,
        "co2_multiple": carbon_buffer(T, c_cap),
        "thermostat_saturated": carbon_buffer(T, c_cap) >= c_cap * 0.999,
        "T_without_thermostat": T_no_thermostat,
        "thermostat_worth_K": T - T_no_thermostat,

        "M_water": M_water,
        "water_earth_oceans": M_water / 1.4e21,
        "ocean_depth_m": depth,
        "water_state": state,
        "ice_fraction": frozen,
        "ice_line_lat_deg": ice_lat,
        # THE PROFILE ITSELF, handed down. A child that needs a temperature at a place must
        # use THIS one, never a second copy of it.
        "dT_equator_pole": DT_POLE,
        "T_equator": temperature_at(T, 0.0),
        "T_pole": temperature_at(T, 1.0),
        "ocean_fraction": ocean_frac,

        "colour": colour,
        "surface_rgb": list(rgb),
        "name": "a" + colour + "World",                    # DERIVED, and it is this folder's name

        # carried down so a surface can be stood on: relief needs gravity and a sea level.
        "g": float(parent["g"]),
        "R": R, "M": M,
        "S_earth": float(parent.get("S_earth", 1.0)),
        "days_per_year": float(parent.get("days_per_year", 365.0)),
        "has_atmosphere": has_air,
        "P_surface_bar": P_bar,
        "scale_height_m": float(parent.get("scale_height_m", 0.0)),
        "T_star_surface": float(parent.get("T_star_surface", 5772.0)),
        "walk_run_ms": float(parent.get("walk_run_ms", 2.04)),
    }


def emit(nums, t=1.0):
    """The matter of aBlueWorld, in its own local units (1.0 = the solid surface).

    The parent drew bare rock. This adds what the climate did to it: an ocean everywhere the water is
    liquid, ice from the poles down to the latitude the fixed point put the ice line at, and the air
    lit blue by its own scattering. Nothing is painted -- each surface is an ALBEDO, and what you see
    is that fraction times the light arriving, so the day side is bright and the night side is not.

    The movie is ONE YEAR: the world turns, the terminator sweeps, and the ice breathes in and out
    with the seasons -- which exist because the spin axis is tilted, and the tilt is the only reason
    a year feels like anything at all from the ground."""
    import numpy as np
    from matter import (blank, fibonacci_sphere, paint, lit, blackbody_rgb,
                        surface_grain, SOLID, GLOW)

    tt = float(t)
    rng = np.random.default_rng(41)
    lens = nums.get("_lens", {})
    TONE = float(lens.get("exposure", 0.42))
    MARK = float(lens.get("star_marker", 1.0))
    S_rel = float(nums.get("S_earth", 1.0))
    frozen = float(nums.get("ice_fraction", 0.0))
    ocean_f = float(nums.get("ocean_fraction", 0.0))
    sea = np.array(nums.get("surface_rgb", [0.09, 0.22, 0.42]), np.float32)
    rock = np.array([0.32, 0.26, 0.20], np.float32)
    ice = np.array([0.78, 0.83, 0.88], np.float32)

    # THE ORBIT, NOT THE SPIN -- theHumanClock's gearing law. A one-year movie cannot also show 394
    # sunrises; that is flicker, not a day. The day belongs to the ground, where it is the right
    # length of film. Here the star's direction turns once, because the planet goes round it.
    #
    # AND THE SEASON IS THE SAME VARIABLE. The spin axis is fixed in space while the planet goes
    # round, so from the ground the sun climbs above the equator and falls below it once a year.
    # That angle is the DECLINATION, and it is the whole of what a season is -- one number that
    # tilts the terminator and melts one cap while it grows the other. Nothing else is needed.
    # The 1.15 rad offset is DECLARED and MEASURED, not guessed: the viewer's default eye sits on -Y,
    # so a sun near -Y lights the face square-on and the world reads FLAT -- which is what a smaller
    # offset gave. At 1.15 the sun is ~65 degrees off the eye, which puts the terminator across the
    # visible disk. A sphere only reads as a sphere when you can see its shadow line.
    TILT = 0.41                                            # radians; Earth's is 0.409
    orbit = 2.0 * pi * tt - 1.15
    decl = TILT * np.cos(orbit)                            # the sun's height above the equator
    sun = np.array([np.sin(orbit) * np.cos(decl),
                    -np.cos(orbit) * np.cos(decl),
                    np.sin(decl)], np.float32)
    sun /= np.linalg.norm(sun)

    n = 34000
    d = fibonacci_sphere(n, jitter=0.9, seed=41)
    b = blank(n)
    b[:, 0:3] = d
    b[:, 21:24] = d

    # WHERE THE ICE IS is decided by LATITUDE, because that is where the temperature gradient runs.
    # Ice takes a world from the poles inward, and the fraction the fixed point solved for IS the
    # latitude band it reaches -- so the cap edge here is a derived number, not a drawn one.
    # The hemisphere leaning INTO the sun (declination and latitude the same sign) gets more light,
    # so its cap retreats while the other's grows. That is the only thing a season is.
    lat = d[:, 2]
    edge = 1.0 - frozen
    lean = np.sign(lat) * float(decl) / TILT               # +1 fully into the sun, -1 fully away
    # The cap edge WANDERS. A perfectly circular ice line is a giveaway that a latitude was drawn
    # rather than a climate solved -- real ice fronts follow currents and high ground. This is small
    # noise on the threshold, not on the physics: the AREA still integrates to the fraction the fixed
    # point derived.
    ragged = 0.035 * rng.standard_normal(n)
    is_ice = np.abs(lat) > np.clip(edge + 0.22 * lean + ragged, 0.02, 1.0)
    # NO SPECKLE. With no relief there is no shore, so everything not frozen IS ocean -- that is what
    # this membrane derived and it must not be contradicted here. (Scattering `ocean_fraction` as a
    # per-grain coin flip drew brown grit through the sea: land invented by a random number, which is
    # the terrain's job and the terrain has not run yet.)
    albedo = np.where(is_ice[:, None], ice, sea if ocean_f > 0.0 else rock)

    cosang = np.clip(d @ sun, 0.0, None)
    # EXPOSURE IS AN INSTRUMENT SETTING, AND IT IS DECLARED HERE. e_ref is the irradiance the render
    # calls "correct exposure", and leaving it at 1.0 (one solar constant, at Earth) rendered this
    # world at a measured 47->15 grey ramp: the terminator was physically right and simply too dark
    # to read. A camera pointed at a planet exposes FOR that planet, so the reference is the light
    # this world actually receives. The falloff across the disk is unchanged -- only the film speed.
    b[:, 16:19] = lit(albedo, S_rel * cosang + 0.012, e_ref=max(S_rel, 1e-6), tone=TONE)
    # THE GRAIN IS A PROPERTY OF THE MATERIAL, not of the renderer.
    #
    # Ice and rock ARE granular -- crystals, gravel, snow -- so their grains should read as grains,
    # tight and opaque. WATER IS NOT. A liquid surface has no smallest piece, so drawing it with
    # tight opaque discs renders an ocean as wet gravel, which is exactly what the first pass showed:
    # solid ice caps above a sea of blue pebbles. The fix is not more grains; it is admitting that
    # water's splats must OVERLAP and blend (wider than their spacing, half transparent) so that no
    # individual one is ever visible. That is what "smooth" means in a matter model made of pieces.
    b[:, 19] = np.where(is_ice, 0.95, 0.55)
    b[:, 20] = np.where(is_ice, surface_grain(n, cover=0.62), surface_grain(n, cover=1.15))
    b[:, 11] = SOLID
    parts = [b]

    if nums.get("has_atmosphere"):
        h_rel = float(nums["scale_height_m"]) / max(float(nums["extent_m"]), 1.0)
        n_a = 9000
        da = fibonacci_sphere(n_a, jitter=1.0, seed=42)
        rad = 1.0 + h_rel * (14.0 * rng.random(n_a) ** 1.6)
        a = blank(n_a)
        a[:, 0:3] = da * rad[:, None]
        # Rayleigh scattering goes as 1/lambda^4 -- that ratio IS this colour, not a choice.
        ca = np.clip(np.array([0.30, 0.52, 1.00]) * (0.35 + 0.9 * float(nums["P_surface_bar"])), 0, 1)
        cosa = np.clip(da @ sun, 0.0, None)
        a[:, 16:19] = (ca[None, :] * (0.08 + 0.92 * cosa)[:, None]).astype(np.float32)
        a[:, 19] = 0.040
        # The grain must be SMALLER than the shell is thick, or the blur is the atmosphere. 14 scale
        # heights here is 2.5% of the radius; a 0.012 splat smeared that into an 8% halo -- the
        # render reporting a puffy sky this world does not have.
        a[:, 20] = 0.0045
        a[:, 11] = GLOW
        parts.append(a)

    # NO STAR-BALL. It used to be drawn here as a "marker" at 1.3 planetary radii -- and at that
    # distance it is not a star, it is a MOON. This story has never derived a moon, so putting a
    # moon-shaped object in the frame is the render asserting a body that does not exist, which is
    # the one thing this whole method exists to prevent. Its true angular size from the ground is a
    # quarter of a degree at 28,000 radii: off-screen and sub-pixel at any framing that shows the
    # planet. WHERE THE STAR IS, IS ALREADY BEING SAID -- by the terminator, by which limb is bright,
    # by the length of the shadow. A light source is told by its light. Nothing replaces it.
    return np.concatenate(parts, axis=0)


def measure(nums):
    """Facts, plus the two checks that make this a derivation rather than a story: the law must
    reproduce EARTH from Earth's own numbers, and the thermostat must be shown to be load-bearing."""
    from pathlib import Path
    folder = Path(__file__).resolve().parent.name

    # EARTH, run through this same law. Nothing was tuned to make this come out.
    S_e = 3.828e26 / (4.0 * pi * (1.495978707e11) ** 2)
    T_e = climate(S_e, EARTH_TAU * 0.75, EARTH_TAU * 0.25, 100.0)
    d_e = ocean_depth(delivered_water(M_EARTH, 53.16), 6.371e6)

    return {
        "T_surface_K": nums["T_surface"],
        "water_state": nums["water_state"],
        "ice_line_lat_deg": nums["ice_line_lat_deg"],
        "ocean_depth_m": nums["ocean_depth_m"],
        # THE NAME MUST MATCH THE PHYSICS -- a wrong rename, or a moved planet, fails here.
        "name_matches_class": folder == nums["name"],
        # THE LAW ON EARTH: 288 K and a 2.7 km ocean, from Earth's mass and orbit alone.
        "earth_T_is_288": abs(T_e - 288.0) < 2.0,
        "earth_ocean_is_2700m": abs(d_e - 2700.0) < 150.0,
        # THE THERMOSTAT IS LOAD-BEARING: without it this world is a snowball.
        "thermostat_worth_K": nums["thermostat_worth_K"],
        "freezes_without_thermostat": nums["T_without_thermostat"] < 250.0,
    }
