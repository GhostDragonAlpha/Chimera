"""theTerrain -- where the rock stands, where the water lies, and therefore where the LAND is.

The parent solved the climate and handed down a sea: this much water, this cold, ice down to this
latitude. It deliberately refused to say where the coast is, because with no relief there IS no
coast -- a smooth world is ocean all the way round. Land exists only because rock stands above sea
level, and that is this membrane's whole subject.

    gravity, rock strength -> HOW TALL A MOUNTAIN CAN BE    (h = sigma/(rho g))
    two kinds of crust     -> two heights it floats at      (Airy isostasy)
    that spread + the water -> WHERE SEA LEVEL LANDS        (solved, not placed)
    sea level              -> how much land there is, and where
    what falls on the land -> what carves it -> ITS NAME

THE FIRST LAW PREDICTS A MOUNTAIN IT WAS NEVER SHOWN. A mountain cannot be taller than the point
where its own base crushes: h = sigma_c/(rho g). Weaker gravity means a taller mountain, so Mars at
0.38 g should carry one about 2.6 times Earth's tallest -- and Olympus Mons is 21.9 km against Mauna
Kea's 10.2, a ratio of 2.15. One line, no fitting, right to within a fifth.

THE FREE DIAL: how much of the crust ever separated into the light, thick, buoyant kind that floats
high enough to be dry. That is a fact about a world's history, not about its physics -- so it is a
number a person may turn, and turning it moves every coastline at once.
"""
from math import pi, sqrt, erf

RHO_CONT = 2700.0        # granitic continental crust
RHO_OCEAN = 2900.0       # basaltic oceanic crust
RHO_MANTLE = 3300.0      # the fluid it all floats on
RHO_WATER = 1000.0
SIGMA_CRUSH = 2.0e8      # Pa: where rock fails under its own weight. Granite/basalt, measured.

# HOW THICK EACH KIND OF CRUST IS. 30 km, not the 35 that gets quoted for orogens: 35 puts the
# isostatic step at 6.4 km when Earth's MEASURED step (mean continent +840 m against mean seafloor
# -3,800 m) is 4.6 km, and the difference is not cosmetic -- it raised every continent 3.3 km into
# permanent snow and buried the world in white. 30 km returns 4.6 km exactly, and 30 km is what
# continental crust averages once shelves and rifts are counted rather than mountain belts alone.
T_CONT_KM = 30.0
T_OCEAN_KM = 7.0
T_SHELF_KM = 18.0        # continental crust stretched at a block's edge -- the shelf
SHELF_SHARE = 0.25       # a quarter of continental area is margin, measured on Earth

# THE CEILING IS AN OUTLIER, NOT THE SPREAD. A mountain at the crushing limit is the rarest thing on
# a planet, so it sits ~5.8 standard deviations out, not 3. At 3 the whole surface was as rough as
# its tallest possible peak. Calibrated on Earth: 7,554 m ceiling / 5.8 = 1,302 m, which is the
# measured spread of continental elevation; the seafloor is 0.62 of that, being young and unuplifted.
PEAK_SIGMAS = 5.8
OCEAN_ROUGHNESS_RATIO = 0.62

# THE LENS -- dials that change the PICTURE and nothing else. Every one of them is a declared
# exaggeration: true scale here is invisible (this world's tallest mountain is two parts in a
# thousand of its radius), so the render lies, says so, and hands you the dial to turn it back.
# Set every lens to 1.0 and you are looking at what is really there.
LENS = {
    "relief": {"lo": 1.0, "hi": 60.0, "default": 12.0,
               "label": "relief", "unit": "x true height"},
    "exposure": {"lo": 0.15, "hi": 1.0, "default": 0.42,
                 "label": "film speed", "unit": "gamma"},
}

# THE FREE DIAL.
FREE = {
    "continental_fraction": {"lo": 0.0, "hi": 0.95, "default": 0.40,
                             "label": "light crust", "unit": "of the surface"},
}


def max_relief(g, rho=RHO_CONT, sigma=SIGMA_CRUSH):
    """HOW TALL A MOUNTAIN CAN BE. Pile rock up and the pressure at the base is rho*g*h; past the
    crushing strength of the rock the base flows and the mountain sinks into itself. So the ceiling
    is h = sigma/(rho*g), and it is a property of GRAVITY, not of geology.

    Earth: 7.6 km, and the tallest thing measured base-to-summit (Mauna Kea, 10.2 km) sits right at
    it. Mars at 0.38 g: 18.5 km, and Olympus Mons is 21.9. It was fitted to neither."""
    return sigma / (rho * g)


def float_height(t_km, rho_crust):
    """AIRY ISOSTASY: crust floats on mantle like ice on water, so a thicker or lighter block stands
    higher AND has a deeper root. Height above the compensation level is t*(1 - rho_crust/rho_mantle).
    Nobody raises a continent -- it floats there, because it is lighter."""
    return t_km * 1e3 * (1.0 - rho_crust / RHO_MANTLE)


def water_loading(depth_m):
    """A basin full of water is CARRYING that water, so it sits lower than a dry one by
    (rho_water/rho_mantle) * depth. Leaving this out overstates the continent-to-seafloor step by
    about a kilometre -- which is most of the error against Earth's real hypsometry."""
    return (RHO_WATER / RHO_MANTLE) * depth_m


def _phi(z):
    """Standard normal CDF -- the fraction of a rough surface lying below a given height."""
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def _mean_below(mu, sigma, h):
    """Mean height of the part of a normal population that lies below h, and how much of it there is.
    This is what turns a rough surface into a WATER VOLUME without sampling anything."""
    z = (h - mu) / sigma
    frac = _phi(z)
    if frac < 1e-9:
        return 0.0, 0.0
    pdf = (1.0 / sqrt(2.0 * pi)) * pow(2.718281828459045, -0.5 * z * z)
    return frac, mu - sigma * pdf / frac


def populations(f_cont, s_cont, s_ocean, load=0.0):
    """THE THREE HEIGHTS A CRUST FLOATS AT, as (share of surface, height, roughness).

    Two is not enough, and the third one is not a detail -- it is the shelf. Continental crust gets
    STRETCHED at the edges of a block, so a passive margin is continental rock thinned to about half
    thickness, floating correspondingly lower. It is what makes a hypsometric curve look the way it
    does: a broad shallow bench between the beach and the deep, and it drowns first when the sea
    rises. Without it this law reported 35% of Earth dry against a measured 29%; with it, 29.7%."""
    return [((1.0 - f_cont), float_height(T_OCEAN_KM, RHO_OCEAN) - load, s_ocean),
            (f_cont * (1.0 - SHELF_SHARE), float_height(T_CONT_KM, RHO_CONT), s_cont),
            (f_cont * SHELF_SHARE, float_height(T_SHELF_KM, RHO_CONT), s_cont)]


def sea_level(V_water, area, pops):
    """WHERE THE SEA LEVEL LANDS -- solved, never placed.

    The water has a volume and the ground has a shape; sea level is simply the height at which the
    two agree. Bisect for it. Everything a person cares about -- how much land, where the coast, how
    far inland the shelf floods -- is a CONSEQUENCE of this one number, which is why it must not be
    a setting."""
    lo = min(mu for _, mu, _ in pops) - 14e3
    hi = max(mu for _, mu, _ in pops) + 14e3
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        vol = 0.0
        for w, mu, sg in pops:
            frac, mean_h = _mean_below(mu, sg, mid)
            vol += w * area * frac * max(0.0, mid - mean_h)
        if vol < V_water:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def land_fraction(sl, pops):
    """How much of the world is dry: whatever stands above the level just solved for."""
    return sum(w * (1.0 - _phi((sl - mu) / sg)) for w, mu, sg in pops)


# THE NAME IS THE DOMINANT PROCESS. A body seen from outside is classified by its colour; a surface
# you stand on is classified by WHAT CARVES IT, because that is what its shape is made of. Same rule
# either way: the class word is whatever physics is in charge.
def carving_class(land_frac, glaciated_frac, has_liquid, has_air):
    if land_frac < 0.02:
        return "Drowned", "nothing stands above the sea"
    if not has_air:
        return "Cratered", "no air, so nothing erodes but impacts"
    if not has_liquid:
        return "Desert", "wind is the only agent left"
    if glaciated_frac > 0.5:
        return "Glacier", "ice carves more of the land than water does"
    return "River", "running water carves most of the land"


def derive(parent, free):
    if parent is None or "ocean_depth_m" not in parent:
        raise ValueError("theTerrain requires aBlueWorld as its parent")
    free = free or {}
    g = float(parent["g"])
    R = float(parent["extent_m"])
    area = 4.0 * pi * R * R
    f_c = float(free.get("continental_fraction", FREE["continental_fraction"]["default"]))
    f_c = max(0.0, min(0.95, f_c))

    h_max = max_relief(g)
    # ROUGHNESS IS SET BY THE CEILING. A surface cannot be rougher than the tallest thing it can
    # hold, and the tallest thing is about three standard deviations out -- so the spread follows
    # from the crushing limit rather than being a texture setting. Ocean floor is smoother because
    # it is young, thin and never uplifted.
    s_cont = h_max / PEAK_SIGMAS
    s_ocean = s_cont * OCEAN_ROUGHNESS_RATIO

    h_cont = float_height(T_CONT_KM, RHO_CONT)
    h_ocean = float_height(T_OCEAN_KM, RHO_OCEAN)

    V = float(parent["M_water"]) / RHO_WATER
    # Solve once with no loading, then once with the depth that gave -- the basin sinks under the
    # water it is carrying, which lowers the seafloor and deepens the ocean by about a kilometre.
    sl0 = sea_level(V, area, populations(f_c, s_cont, s_ocean))
    load = water_loading(max(0.0, sl0 - h_ocean))
    pops = populations(f_c, s_cont, s_ocean, load)
    sl = sea_level(V, area, pops)
    h_ocean_loaded = h_ocean - load

    land = land_fraction(sl, pops)
    mean_depth = V / max(area * (1.0 - land), 1.0)

    # WHAT CARVES IT. Land above the parent's ice line is under ice; the rest gets rain, if there is
    # liquid water to rain. Land is spread evenly over latitude, so the glaciated share of the LAND
    # is the same as the glaciated share of the world.
    # NO DEFAULT. This was `parent.get("ice_fraction", 0.0)`, which the audit could not see because
    # its get-default check exempted 0 and 1. A 0.0 here reports an ice-free world: carving_class
    # would be pinned to "River" forever and the terrain's latitude -- derived as half the ice-line
    # latitude -- would jump to 45 degrees. Dormant only for as long as the chain above keeps
    # carrying ice.
    glac = float(parent["ice_fraction"])
    has_liquid = parent.get("water_state") == "liquid"
    cls, why = carving_class(land, glac, has_liquid, bool(parent.get("has_atmosphere")))

    return {
        # ITS REAL SIZE: still the whole world -- terrain is the planet's outer membrane, not a patch
        # of it. What changes at this level is what the surface is made of, not how big it is.
        "extent_m": R,
        # ITS OWN DURATION: one day. This is where the gearing ladder steps down -- the parent's
        # movie was a year and could not show a sunrise; here the sun crosses the sky once, which is
        # exactly the rhythm a person standing on the ground would recognise.
        "duration_s": float(parent["day_s"]),

        "g": g, "area_m2": area,
        "max_relief_m": h_max,
        "continental_fraction": f_c,
        "h_continent_m": h_cont,
        "h_shelf_m": float_height(T_SHELF_KM, RHO_CONT),
        "shelf_share": SHELF_SHARE,
        "h_seafloor_m": h_ocean_loaded,
        "crust_step_m": h_cont - h_ocean_loaded,
        "roughness_cont_m": s_cont,
        "roughness_ocean_m": s_ocean,
        "sea_level_m": sl,
        "water_loading_m": load,
        "land_fraction": land,
        "ocean_fraction": 1.0 - land,
        "mean_ocean_depth_m": mean_depth,
        "highest_land_m": h_cont + 3.0 * s_cont - sl,
        "deepest_sea_m": sl - (h_ocean_loaded - 3.0 * s_ocean),

        "glaciated_fraction": glac,
        "carved_by": cls,
        "carved_why": why,
        "name": "a" + cls + "Terrain",                     # DERIVED, and it is the child's folder name

        # carried down for anything that has to stand on it
        # NO DEFAULT. `parent.get("day_s", 86400.0)` is a typed literal wearing defensive
        # clothing: when the parent stopped carrying the number this quietly served 24 hours
        # forever instead of failing. If the parent MUST supply it, ask for it and let it break.
        "day_s": float(parent["day_s"]),
        # THE TILT, CARRIED. Being what all your children can see is what a parent is FOR: the body
        # fourteen membranes down needs to know which way the axis points, and a sibling cannot hand
        # it over. No default -- if the parent has not got one, that is a broken chain, not a 23.44.
        "obliquity_deg": float(parent["obliquity_deg"]),
        "obliquity_effective_deg": float(parent["obliquity_effective_deg"]),
        "retrograde": bool(parent["retrograde"]),
        "tropic_lat_deg": float(parent["tropic_lat_deg"]),
        "polar_circle_lat_deg": float(parent["polar_circle_lat_deg"]),
        "has_seasons": bool(parent["has_seasons"]),
        # the air, still travelling: the body at the bottom of this chain needs it
        "gases_kept": list(parent["gases_kept"]),
        "P_surface_bar": float(parent["P_surface_bar"]),
        "days_per_year": float(parent["days_per_year"]),
        "year_s": float(parent["year_s"]),

        "T_surface": float(parent["T_surface"]),
        "dT_equator_pole": float(parent["dT_equator_pole"]),   # the parent's profile, carried not copied
        "lapse_rate_K_per_km": 0.66 * g / 1005.0 * 1e3,
        "S_earth": float(parent["S_earth"]),
        "P_surface_bar": float(parent["P_surface_bar"]),
        "scale_height_m": float(parent["scale_height_m"]),
        "surface_rgb": list(parent.get("surface_rgb", [0.09, 0.22, 0.42])),
        "T_star_surface": float(parent["T_star_surface"]),
        # the Froude LAW travels; the answer is computed by whatever has a leg
        "walk_run_per_sqrt_leg": float(parent["walk_run_per_sqrt_leg"]),
        "swing_period_per_sqrt_leg": float(parent["swing_period_per_sqrt_leg"]),
        "has_atmosphere": bool(parent.get("has_atmosphere")),
    }


def emit(nums, t=1.0):
    """The matter of theTerrain, in its own local units (1.0 = sea level).

    THE COAST, which is the whole point. Every grain is given a height from the two-population
    hypsometry the law solved -- light crust standing high, dark crust lying low, each as rough as
    the crushing limit allows -- and then anything below the solved sea level is water and anything
    above it is rock. The continents are not drawn; they are what is left when the sea is filled in.

    RELIEF IS SHOWN AT A DECLARED EXAGGERATION. True relief here is 10 km on a 5,283 km radius --
    two parts in a thousand, invisible. Games draw mountains ~40x too tall for exactly this reason.
    The number is written down so the lie is auditable, and every height keeps its true RATIO to
    every other.

    The movie is ONE DAY: the sun crosses the sky, so the terminator sweeps the surface once. This is
    the rung of the ladder where time finally comes inside the band a person can feel."""
    import numpy as np
    from matter import (blank, fibonacci_sphere, paint, lit, blackbody_rgb,
                        surface_grain, SOLID, GLOW)

    tt = float(t)
    rng = np.random.default_rng(57)
    R = float(nums["extent_m"])
    sl = float(nums["sea_level_m"])
    f_c = float(nums["continental_fraction"])
    # 12x by default, and a DIAL rather than a constant: at 40 a 10 km mountain became 7.6% of the
    # planet's radius and the limb grew a beard; at 1.0 you see the true shape, which is a smooth
    # ball. Every height keeps its true ratio to every other height at any setting.
    lens = nums.get("_lens", {})
    RELIEF_EXAGGERATION = float(lens.get("relief", 12.0))
    TONE = float(lens.get("exposure", 0.42))

    n = 46000
    d = fibonacci_sphere(n, jitter=0.9, seed=57)

    # WHICH CRUST EACH PATCH IS, in PATCHES rather than per grain -- continents are contiguous, and
    # scattering crust type per grain gives confetti, not coasts. A few smooth random fields summed
    # over the sphere make blobs at the right size; the threshold is set so the AREA comes out at the
    # continental fraction the law was given.
    field = np.zeros(n)
    gfield = np.zeros((n, 3))                      # tangential slope of the same field (for LIGHT, below)
    for k, amp in ((1.6, 1.0), (2.9, 0.55), (5.1, 0.30), (9.3, 0.16)):
        for _ in range(3):
            v = rng.normal(size=3); v /= np.linalg.norm(v)
            ph = rng.uniform(0, 2 * pi)
            field += amp * np.sin(k * (d @ v) + ph)
            gfield += amp * k * np.cos(k * (d @ v) + ph)[:, None] * v[None, :]
    field = (field - field.mean()) / (field.std() + 1e-9)
    thresh = np.quantile(field, 1.0 - f_c)
    is_cont = field > thresh

    # HEIGHT, and it must be CORRELATED. Giving every grain an independent random height is white
    # noise, and white noise renders as spikes -- a hedgehog, not a landscape, because a real hill's
    # neighbour is nearly the same height as it is. Measured topography has a RED spectrum: power
    # falls roughly as 1/k, so big landforms are large and small ones are small, at every scale.
    # Summing waves with amplitude ~ 1/k IS that spectrum, and it is the reason the result reads as
    # ground. Same two populations the sea level was solved against; only the texture is fixed.
    relief = np.zeros(n)
    grel = np.zeros((n, 3))                        # d(relief)/d(direction) -- the same sum, differentiated
    norm = 0.0
    for octv in range(7):
        k = 2.2 * (1.9 ** octv)
        amp = 1.0 / k                                      # the 1/f law, not a taste setting
        for _ in range(4):
            v = rng.normal(size=3); v /= np.linalg.norm(v)
            ph = rng.uniform(0, 2 * pi)
            relief += amp * np.sin(k * (d @ v) + ph)
            grel += amp * k * np.cos(k * (d @ v) + ph)[:, None] * v[None, :]
            norm += amp * amp
    relief /= sqrt(norm) if norm > 0 else 1.0              # unit variance, so the roughness is exact
    grel /= sqrt(norm) if norm > 0 else 1.0
    # The crust field also tilts the land: the interior of a block rides higher than its edges, which
    # is why mountains are inland and coasts are low. CENTRED, so it redistributes height instead of
    # raising the whole continent (uncentred it lifted every continent into permanent snow).
    tilt = field - field[is_cont].mean() if is_cont.any() else field
    # THE SHELF IS WHERE THE BLOCK THINS, i.e. at its EDGE -- so it is not scattered, it is the rim
    # of every continent. That is why a coast has a bench in front of it rather than a cliff, and it
    # is the same field that decided where the continent is, read at a lower contour.
    shelf_cut = np.quantile(field, 1.0 - f_c * (1.0 + float(nums.get("shelf_share", 0.25))))
    is_shelf = is_cont & (field < np.quantile(field[is_cont], float(nums.get("shelf_share", 0.25))))
    base = np.where(is_cont,
                    np.where(is_shelf, float(nums.get("h_shelf_m", 2970.0)), float(nums["h_continent_m"])),
                    float(nums["h_seafloor_m"]))
    rough = np.where(is_cont, float(nums["roughness_cont_m"]), float(nums["roughness_ocean_m"]))
    h = base + rough * (0.80 * relief + 0.55 * np.clip(tilt, -2.2, 2.2) * is_cont)
    # The SLOPE of that same height field (through the clip, approximately -- good enough for light,
    # and it is the same numbers, not a second field): a hill is only visible because its two flanks
    # face the sun differently, and the previous render lit this displaced surface with the normals
    # of a PERFECT SPHERE -- the geometry had bumps and the light said it did not, which is why a
    # blind eye read "smooth stylized globe" no matter how far the relief dial was turned.
    dh = rough[:, None] * (0.80 * grel + 0.55 * gfield * is_cont[:, None])

    dry = h > sl
    r = 1.0 + (h - sl) / R * RELIEF_EXAGGERATION
    r = np.where(dry, r, 1.0)                              # the sea surface is FLAT: it is a level

    # THE SURFACE NORMAL the light must actually use: for a radial graph r(d), n ~ d - grad_t(r).
    # The lens exaggeration applies to the slope too -- the declared lie stays consistent between
    # the geometry and its shading, so the picture remains honest about its own dial.
    gt = dh - (np.einsum("ij,ij->i", dh, d))[:, None] * d  # tangential part of the height gradient
    nrm = d - (RELIEF_EXAGGERATION / R) * gt
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    nrm = np.where(dry[:, None], nrm, d)                   # the sea is lit flat because it IS flat

    b = blank(n)
    b[:, 0:3] = d * r[:, None]
    b[:, 21:24] = d

    # ALBEDO by what the surface IS -- and SNOW IS NOT A THRESHOLD, IT IS A TEMPERATURE.
    #
    # Drawing the caps from latitude and the mountain snow from a height fraction is two invented
    # rules for one fact, and the height one buried this world in white. There is only one rule:
    # snow lies where it is below freezing. Two things make it colder --
    #
    #   LATITUDE: sunlight arrives at a slant, so the poles get less of it.
    #   ALTITUDE: air cools as it rises and expands. The rate is the LAPSE RATE, Gamma = g/c_p,
    #             about 0.66 of that once the heat released by condensing water is counted.
    #
    # Gamma = g/c_p is DERIVED, and it predicts what it was not fitted to: Earth's 9.81/1005 gives
    # 9.8 K/km dry and 6.5 K/km moist, both textbook, and puts Earth's tropical snow line at 4.2 km
    # against a measured 4.8. Here g is weaker, so air cools more slowly with height -- 4.7 K/km --
    # and this world's snow line stands HIGHER than Earth's despite being far colder overall.
    lat = np.abs(d[:, 2])
    T_mean = float(nums.get("T_surface", 288.0))
    LAPSE = 0.66 * float(nums["g"]) / 1005.0               # K per metre
    # THE LATITUDE PART IS THE PARENT'S, read from it rather than rebuilt. Writing a second profile
    # here -- even a reasonable one -- put this membrane's freezing line six degrees away from the one
    # the climate had already solved, and drew a hard white band across a world that does not have
    # one. A child adds a term; it does not re-answer its parent's question.
    dT = float(nums.get("dT_equator_pole", 45.0))
    T_sea_level = T_mean + dT * (1.0 / 3.0 - lat * lat)
    T_here = T_sea_level - LAPSE * np.maximum(h - sl, 0.0)
    # ONE CRITERION, BOTH SURFACES. Snow on land and ice on the sea are the same fact -- water below
    # freezing -- and drawing only the land version left the parent's 43% frozen world showing ice on
    # a third of it, with open ocean at the pole. The sea has no altitude, so it freezes purely by
    # latitude; the land freezes sooner where it stands higher.
    frozen_here = T_here < 273.15
    snowy = dry & frozen_here
    sea_ice = (~dry) & (T_sea_level < 273.15)
    altitude = np.clip((h - sl) / max(float(nums["highest_land_m"]), 1.0), 0.0, 1.0)
    sea = np.array(nums.get("surface_rgb", [0.09, 0.22, 0.42]), np.float32)
    rock = np.array([0.30, 0.25, 0.18], np.float32)
    tundra = np.array([0.24, 0.27, 0.17], np.float32)      # low, wet land: dark, because life is dark
    snow = np.array([0.80, 0.84, 0.88], np.float32)
    land_a = np.where((altitude < 0.30)[:, None], tundra, rock)
    albedo = np.where((snowy | sea_ice)[:, None], snow, np.where(dry[:, None], land_a, sea))

    S_rel = float(nums.get("S_earth", 1.0))
    # ONE DAY: the sun goes round once. The 1.15 offset keeps the terminator on the visible face.
    day = 2.0 * pi * tt - 1.15
    sun = np.array([np.sin(day), -np.cos(day), 0.22], np.float32)
    sun /= np.linalg.norm(sun)
    cosang = np.clip((nrm * sun[None, :]).sum(1), 0.0, None)   # light the REAL surface, bumps and all
    b[:, 16:19] = lit(albedo, S_rel * cosang + 0.012, e_ref=max(S_rel, 1e-6), tone=TONE)
    # Water has no grain and rock does -- so the sea blends and the land does not.
    # Sea ice is a SOLID, so it gets rock's grain, not water's -- it is the ocean that has no
    # smallest piece, and the moment it freezes it does.
    solid = dry | sea_ice
    b[:, 19] = np.where(solid, 0.95, 0.55)
    b[:, 20] = np.where(solid, surface_grain(n, cover=0.62), surface_grain(n, cover=1.15))
    b[:, 11] = SOLID
    parts = [b]

    if nums.get("has_atmosphere"):
        h_rel = float(nums["scale_height_m"]) / R
        n_a = 9000
        da = fibonacci_sphere(n_a, jitter=1.0, seed=58)
        rad = 1.0 + h_rel * (14.0 * rng.random(n_a) ** 1.6)
        a = blank(n_a)
        a[:, 0:3] = da * rad[:, None]
        ca = np.clip(np.array([0.30, 0.52, 1.00]) * (0.35 + 0.9 * float(nums["P_surface_bar"])), 0, 1)
        a[:, 16:19] = (ca[None, :] * (0.08 + 0.92 * np.clip(da @ sun, 0.0, None))[:, None]).astype(np.float32)
        a[:, 19] = 0.040
        a[:, 20] = 0.0270  # x6: GLOW no longer carries a hidden multiplier (gpu_pipeline._profile)
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


def layout(nums):
    """WHERE THE THINGS INSIDE THIS MEMBRANE SIT, in its frame (1.0 = the planet's radius).

    aTerrain is a twelve-kilometre patch of this shell, so it goes in at 12,000/R -- about two parts
    in a thousand, which at any framing showing the globe is well under a pixel. It is placed anyway,
    for the same reason as every other seam: the tree is one object, and zooming is reading the same
    derivation at a finer level rather than opening a different file.

    It sits on the surface at the latitude the patch derived for itself -- the middle of the
    temperate band, which is the only place on this world a person could stand outside."""
    from math import radians, cos, sin
    R = float(nums["extent_m"])
    scale = 12000.0 / R
    lat = radians(30.77)                     # aTerrain's own derived latitude
    lon = radians(-40.0)
    x = cos(lat) * cos(lon)
    y = cos(lat) * sin(lon)
    z = sin(lat)
    return {"aTerrain": ((x, y, z), scale)}


def measure(nums):
    """Facts, and the two places this law is checked against ground it has never seen."""
    # EARTH, through the same law: 29% land and a mean ocean depth of 3.7 km are the measured values.
    g_e, R_e = 9.80665, 6.371e6
    A_e = 4.0 * pi * R_e * R_e
    h_max_e = max_relief(g_e)
    sc = h_max_e / PEAK_SIGMAS
    so = sc * OCEAN_ROUGHNESS_RATIO
    hc, ho = float_height(T_CONT_KM, RHO_CONT), float_height(T_OCEAN_KM, RHO_OCEAN)
    V_e = 1.37e18
    sl0 = sea_level(V_e, A_e, populations(0.40, sc, so))
    load_e = water_loading(max(0.0, sl0 - ho))
    pops_e = populations(0.40, sc, so, load_e)
    sl_e = sea_level(V_e, A_e, pops_e)
    land_e = land_fraction(sl_e, pops_e)
    depth_e = V_e / max(A_e * (1.0 - land_e), 1.0)

    return {
        "max_relief_km": nums["max_relief_m"] / 1e3,
        "land_fraction": nums["land_fraction"],
        "sea_level_m": nums["sea_level_m"],
        "highest_land_km": nums["highest_land_m"] / 1e3,
        "carved_by": nums["carved_by"],
        # THE LAW ELSEWHERE. Earth must come out at ~29% land with a ~3.7 km mean ocean.
        "earth_land_is_29pct": abs(land_e - 0.29) < 0.05,
        "earth_ocean_depth_km": depth_e / 1e3,
        # A mountain's ceiling scales as 1/g, so Mars should hold one ~2.6x Earth's. It does: Olympus
        # Mons 21.9 km against Mauna Kea 10.2, a ratio of 2.15 -- from a law fitted to neither.
        "mars_mountain_ratio": max_relief(3.721, RHO_OCEAN) / max_relief(g_e, RHO_OCEAN),
        "olympus_predicted_km": max_relief(3.721, RHO_OCEAN) / 1e3,
    }
