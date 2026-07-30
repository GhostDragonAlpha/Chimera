"""theGround -- what the surface is MADE of, at the scale a foot lands on.

The parent gave the shape of the land over twelve kilometres. It never said what any of it is made
of, and a shape cannot be stood on. This membrane is four metres across and it answers the only
question a body actually asks of a planet: **will it hold me, and how far do I sink?**

    bedrock + weather        -> loose material is MADE            (the soil production function)
    slope                    -> loose material is CARRIED AWAY    (erosion)
    the balance of those two -> HOW DEEP THE SOIL IS
    breaking rock repeatedly -> a grain size distribution         (fragmentation is fractal)
    grains + friction        -> how much load it carries          (Terzaghi)
    load vs a foot           -> how far the foot sinks

THE ONE THAT PREDICTS SOMETHING IT WAS NOT TOLD: soil is made from the bedrock underneath it, and
the deeper the soil the slower it is made, because the rock is insulated from frost, roots and
water. Production falls off exponentially with depth (Heimsath, Dietrich, Nishiizumi & Finkel 1997,
measured with cosmogenic nuclides):

    P(h) = P0 * exp(-h / h0)

Balance that against erosion and the steady depth is h = h0 * ln(P0 / E). Nothing in it mentions
slope -- but erosion rises steeply with slope, so the law says **soil thins on steep ground and
deepens in hollows, and above a critical steepness there is no soil at all, only bedrock.** That is
what every hillside on Earth looks like, and it was not put in.

THE ANGLE OF REPOSE IS THIS STUDIO'S OWN MEASUREMENT. `core/trainables/granular.py` grew a sandpile
from a local stochastic rule and the pile chose 40.03 +/- 1.55 degrees for dry regolith -- inside
the measured lunar band, and never fitted to it. That number is used here rather than looked up.
"""
from math import pi, sqrt, exp, log, tan, radians, degrees, atan

# ── making soil out of rock (Heimsath et al. 1997) ──
P0_MM_KYR = 77.0          # bare-bedrock production rate, mm per thousand years -- measured
H0_M = 0.50               # the e-folding depth: rock this far down is already insulated

# ── how fast the slope takes it away ──
# EROSION AT A REFERENCE GENTLE SLOPE. 21, not 50 -- and the difference is the whole chapter.
# At 50 the erosion rate passes bare-rock production at only 15 degrees, so soil would run out
# below this landscape's own MEAN slope of 17 and the entire hillside would be stripped rock. Real
# soil-mantled hillslopes carry soil to 30-35 degrees and then go bare, which is what 21 gives.
E_REF_MM_KYR = 21.0
SLOPE_REF_DEG = 10.0

# ── what broken rock is like ──
FRACTAL_D = 2.6           # fragmentation dimension: N(>d) ~ d^-D. Measured on real soils, 2.4-3.0
D_MAX_MM = 60.0           # the biggest clast a hillslope soil carries
D_MIN_MM = 0.002          # clay, the finest product of weathering
RHO_SOLID = 2650.0        # quartz/feldspar, kg/m^3
POROSITY = 0.42           # loose, unconsolidated, freshly disturbed

REPOSE_DRY_DEG = 40.03    # GROWN, not looked up: core/trainables/granular.py, +/- 1.55

# THE ANGLE THAT BEARS A LOAD IS NOT THE ANGLE A PILE STANDS AT. Loose material poured into a heap
# settles at its repose angle; the same material UNDER A FOOT is compacted, and what resists then is
# the friction of a denser packing. Using the repose angle here gave 413 kPa -- three times what a
# real soil carries -- because Terzaghi's factors climb steeply with the angle.
PHI_BEARING_DEG = 35.0    # compacted sandy soil
COHESION_PA = 2000.0      # damp soil holds itself together a little; dry sand is ~0

FOOT_AREA_M2 = 0.030      # one human foot, flat: ~0.03 m^2
BODY_MASS_KG = 82.04      # this studio's own measured body (docs/THE_MATHEMATICS_OF_WALKING.md)


def erosion_rate(slope_deg):
    """HOW FAST THE SLOPE STRIPS IT. Steeper ground loses material faster -- roughly linearly in the
    gradient for soil-mantled hillslopes, and without limit as the repose angle is approached."""
    s = tan(radians(min(abs(slope_deg), REPOSE_DRY_DEG - 0.5)))
    s_ref = tan(radians(SLOPE_REF_DEG))
    # perfectly flat ground still weathers and still creeps; a floor keeps the law finite there
    # rather than promising infinitely deep soil on a billiard table.
    return max(E_REF_MM_KYR * (s / s_ref), 0.05 * E_REF_MM_KYR)


def soil_depth(slope_deg):
    """THE STEADY DEPTH, where making equals losing:

        P0 exp(-h/h0) = E      ->      h = h0 ln(P0 / E)

    If erosion exceeds the bare-rock production rate the logarithm goes negative and there is no
    soil: the hillside is stripped to bedrock as fast as bedrock can turn into soil. That threshold
    is not a rule added on top -- it falls out of the same equation."""
    e = erosion_rate(slope_deg)
    if e >= P0_MM_KYR:
        return 0.0
    return H0_M * log(P0_MM_KYR / e)


def bare_rock_above_deg():
    """The slope at which soil runs out. Solve E(s) = P0."""
    s_ref = tan(radians(SLOPE_REF_DEG))
    t = (P0_MM_KYR / E_REF_MM_KYR) * s_ref
    return degrees(atan(t))


def grain_fraction_coarser(d_mm):
    """FRAGMENTATION IS FRACTAL. Break a rock and you get pieces; break those and you get the same
    distribution one scale down. Repeat and the mass fraction coarser than d follows a power law --
    which is why every soil on every planet has the same SHAPE of grain-size curve, however
    different its chemistry."""
    if d_mm >= D_MAX_MM:
        return 0.0
    if d_mm <= D_MIN_MM:
        return 1.0
    a = 3.0 - FRACTAL_D
    return (D_MAX_MM ** a - d_mm ** a) / (D_MAX_MM ** a - D_MIN_MM ** a)


def bulk_density():
    """Solid grains with holes between them. The holes are most of why soil is soft."""
    return RHO_SOLID * (1.0 - POROSITY)


def bearing_capacity(g, depth_m=0.05, phi_deg=PHI_BEARING_DEG, c=COHESION_PA):
    """WILL IT HOLD? Terzaghi: the ground fails when the load pushes a wedge of it sideways, and
    what resists is friction between grains plus whatever sticks them together.

        q = c Nc + rho g D Nq

    N_c and N_q come from the friction angle alone. It is the same PROPERTY as the repose angle --
    grains resisting grains -- but not the same NUMBER: a heap is loose and a footing is compacted,
    so the bearing angle is the lower one."""
    phi = radians(phi_deg)
    nq = exp(pi * tan(phi)) * tan(radians(45.0) + phi / 2.0) ** 2
    nc = (nq - 1.0) / tan(phi)
    return c * nc + bulk_density() * g * depth_m * nq


def sinkage(g, mass_kg=BODY_MASS_KG, foot_m2=FOOT_AREA_M2):
    """HOW FAR A FOOT GOES IN. Press until the ground's capacity matches the pressure under the foot.
    The capacity grows with depth, so there is always a depth at which it balances -- and on firm
    ground that depth is millimetres, which is why you do not think about it."""
    press = mass_kg * g / foot_m2
    lo, hi = 0.0, 2.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if bearing_capacity(g, depth_m=max(mid, 1e-4)) < press:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def derive(parent, free):
    if parent is None or "mean_slope_deg" not in parent:
        raise ValueError("theGround requires aTerrain as its parent")
    g = float(parent["g"])
    slope_mean = float(parent["mean_slope_deg"])
    slope_steep = float(parent["p95_slope_deg"])

    h_mean = soil_depth(slope_mean)
    h_steep = soil_depth(slope_steep)
    h_flat = soil_depth(2.0)
    q = bearing_capacity(g)
    sink = sinkage(g)
    press = BODY_MASS_KG * g / FOOT_AREA_M2

    return {
        # ITS REAL SIZE: four metres. The scale at which "the ground" stops being a surface and
        # becomes a material.
        #
        # ── OPEN ASSERTION. THIS NUMBER IS NOT DERIVED AND NOTHING IN THIS STORY DERIVES IT. ────────
        #
        # Every other number in this dict comes from a law: the soil depth from Heimsath's production
        # function against erosion, the grain curve from fractal fragmentation, the bearing capacity
        # from Terzaghi. This one is a FRAMING CHOICE wearing the same clothes, and it is written down
        # here so that it stops looking like the others.
        #
        # What is actually known bounds it but does not pick it:
        #   UPPER  it must fit inside ONE of the parent's terrain cells, because the whole law here
        #          reads a single slope and treats it as constant. aTerrain's cell_m is 93.75 m.
        #   LOWER  it must contain a representative sample of its own material, so many times the
        #          largest clast it carries -- D_MAX_MM = 60 mm, i.e. well above ~0.06 m.
        # 4 m sits inside 0.06 < x < 93.75 and so would 3 m and so would 20 m. The bracket is real;
        # the value is not in it by derivation.
        #
        # (The prose used to gloss this as "two paces", which is also wrong arithmetic -- a pace is
        # about 0.75 m, so four metres is five of them. Left corrected rather than restated, because
        # the honest description of 4.0 is that nobody derived it.)
        #
        # IT WAS ASSERTED TWICE and now it is not. aTerrain declares `ground_patch_m` -- how big a
        # child is IS the parent's to say -- and both this line and aTerrain's own layout() read that
        # one number. Previously each typed its own 4.0 and changing either mis-scaled the
        # composition in silence. NO DEFAULT: a missing key here is a broken chain, not a guess.
        #
        # The value is still nobody's derivation. Single-sourcing an assertion is not grounding it;
        # it just means there is one thing to fix when someone does.
        "extent_m": float(parent["ground_patch_m"]),
        # ITS OWN DURATION: one day, inherited -- soil does not move on any timescale a person sees.
        "duration_s": float(parent["day_s"]),

        "soil_depth_m": h_mean,
        "soil_depth_flat_m": h_flat,
        "soil_depth_steep_m": h_steep,
        "bare_rock_above_deg": bare_rock_above_deg(),
        "erosion_mm_kyr": erosion_rate(slope_mean),
        "production_mm_kyr": P0_MM_KYR,

        # ── TWO ANGLES OF REPOSE, AND THEY ARE NOT THE SAME QUESTION ─────────────────────────
        # The parent returns `repose_deg` too, at 33 degrees, and this membrane used to overwrite it
        # with 40.03 under the same key -- so a consumer reading `repose_deg` got whichever membrane
        # it happened to be nearest, with no way to tell. They are different materials:
        #   aTerrain's 33.0  -- LOOSE ROCK at its friction angle, which is what sets the gradient the
        #                       hillslope transport law runs away at. A property of a mountainside.
        #   this 40.03       -- DRY REGOLITH, and it was GROWN rather than looked up
        #                       (core/trainables/granular.py, 40.03 +/- 1.55). A property of what a
        #                       boot stands in.
        # Both are correct about their own material. Only the shared key was wrong, so both now
        # travel under names that say which is which.
        "repose_deg": REPOSE_DRY_DEG,          # regolith -- what a foot is on. GROWN, not looked up
        "repose_regolith_deg": REPOSE_DRY_DEG,
        "repose_bedrock_deg": float(parent["repose_deg"]),   # carried: the parent's loose-rock angle
        "fractal_D": FRACTAL_D,
        "d_median_mm": 0.35,                   # solved below and overwritten
        "bulk_density": bulk_density(),
        "porosity": POROSITY,

        "bearing_capacity_Pa": q,
        "bearing_capacity_kPa": q / 1e3,
        "foot_pressure_Pa": press,
        "foot_pressure_kPa": press / 1e3,
        "sinkage_m": sink,
        "sinkage_mm": sink * 1e3,
        "holds_a_person": q > press,

        # carried down for a body
        "g": g,
        # the Froude LAW travels; the answer is computed by whatever has a leg
        "walk_run_per_sqrt_leg": float(parent["walk_run_per_sqrt_leg"]),
        "swing_period_per_sqrt_leg": float(parent["swing_period_per_sqrt_leg"]),
        "T_surface": float(parent["T_surface"]),
        "S_earth": float(parent["S_earth"]),
        "latitude_deg": float(parent["latitude_deg"]),
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

    }


def emit(nums, t=1.0):
    """The matter of theGround, in its own local units (1.0 = two metres, half the patch).

    Four metres of it, at TRUE SCALE, one splat per stone. The size distribution is the fractal one
    the law derived, so the big clasts are rare and the fines are everywhere, exactly as breaking
    rock over and over produces. Colour is mineral, not taste: quartz pale, feldspar buff, iron
    oxide red on the weathered faces.

    The movie is ONE DAY. Nothing here moves -- soil does not, on any timescale a person notices --
    so what changes is the light. At dawn the stones cast long shadows and the ground reads as
    ROUGH; at noon the shadows vanish and the same ground reads as flat. That is worth seeing,
    because it is the whole reason a real landscape is legible at all."""
    import numpy as np
    from matter import blank, paint, lit, SOLID

    rng = np.random.default_rng(4141)
    tt = float(t)
    half = 2.0                                        # metres; the patch is 4 m across

    # ── the stones: sizes drawn from the fractal distribution the law derived ──
    n = 26000
    D = float(nums.get("fractal_D", 2.6))
    a = 3.0 - D
    u = rng.random(n)
    # invert the mass-fraction-coarser curve for d
    d_mm = (D_MAX_MM ** a - u * (D_MAX_MM ** a - D_MIN_MM ** a)) ** (1.0 / a)
    d_m = np.clip(d_mm, 0.05, D_MAX_MM) / 1000.0

    x = rng.uniform(-half, half, n)
    y = rng.uniform(-half, half, n)
    # a stone sits ON the surface, so its centre is half its own size above it, and the surface has
    # its own small roughness -- the grains beneath it
    rough = 0.012 * np.sin(3.1 * x) * np.cos(2.7 * y) + 0.006 * np.sin(11.0 * y + 1.3)
    zed = rough + d_m * 0.5

    b = blank(n)
    b[:, 0] = x / half
    b[:, 1] = y / half
    b[:, 2] = zed / half
    # normals: mostly up, tilted by the local roughness, so the light models the surface
    nz = np.ones(n)
    nx = -(0.012 * 3.1 * np.cos(3.1 * x) * np.cos(2.7 * y))
    ny = -(-0.012 * 2.7 * np.sin(3.1 * x) * np.sin(2.7 * y) + 0.006 * 11.0 * np.cos(11.0 * y + 1.3))
    nrm = np.stack([nx, ny, nz], axis=1)
    nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
    b[:, 21:24] = nrm

    # MINERAL COLOUR, and the big grains are more weathered because they have been exposed longer
    quartz = np.array([0.62, 0.60, 0.56], np.float32)
    feldspar = np.array([0.52, 0.45, 0.35], np.float32)
    oxide = np.array([0.42, 0.24, 0.14], np.float32)
    pick = rng.random(n)
    albedo = np.where((pick < 0.35)[:, None], quartz,
                      np.where((pick < 0.80)[:, None], feldspar, oxide))
    weathered = (d_mm > 8.0) & (rng.random(n) < 0.55)
    albedo[weathered] = oxide

    # ONE DAY: the sun crosses at this latitude's height. The shadows are the point. The +0.9
    # phase starts the film mid-morning, sun ~45 degrees up: the day-movie's two ends (t=0, t=1)
    # share that readable light instead of opening on the sunrise graze, where the patch renders
    # nearly black and the whole point -- stones, texture, shadows -- is invisible to the eye.
    hour = 2.0 * pi * tt + 0.9
    alt = np.cos(np.radians(float(nums.get("latitude_deg", 31.0)))) * np.sin(hour)
    sun = np.array([np.cos(hour), 0.30, max(alt, 0.04)], np.float32)
    sun /= np.linalg.norm(sun)
    lam = np.clip(nrm @ sun, 0.0, None)
    b[:, 16:19] = lit(albedo, float(nums.get("S_earth", 1.0)) * lam + 0.06,
                      e_ref=float(nums.get("S_earth", 1.0)), tone=0.45)
    b[:, 19] = 0.95
    b[:, 20] = np.clip(d_m / half * 0.75, 0.0016, 0.05)     # TRUE SIZE: the stone is the splat
    b[:, 11] = SOLID
    return b


def layout(nums):
    """WHERE THE THINGS INSIDE THIS MEMBRANE SIT, in its frame (1.0 = two metres, half the patch).

    A person stands ON this ground, so the body is placed here rather than drawn twice. Before this,
    theHuman emitted its own little brown disc to stand on -- inventing matter its own parent had
    already derived, which is the star-marker moon in miniature and was written a few hours after
    that one was deleted for the same reason.

    THE SCALE IS A UNIT CONVERSION AND NOTHING ELSE. The body is 1.78 m tall and emits at radius 1
    in its own frame; this membrane's 1.0 is 2 m. So the body arrives at 1.78/2 = 0.89, and its feet
    land on the surface because the surface is where this membrane put it."""
    body_m = 1.78                                   # theHuman's own extent; it emits at radius ~1
    half_m = float(nums["extent_m"]) / 2.0          # this membrane's 1.0
    scale = body_m / half_m
    # The body's frame is centred on its CENTRE OF MASS. Its SOLES sit 0.5377 of its height below
    # that -- not 0.575, which is the CoM height above the FLOOR and puts the feet 6 cm in the air.
    # The difference is the ankle: the foot is drawn horizontally from it, so the sole is the ankle,
    # at (leg - thigh - shank) = 0.039 above the floor. 0.575 - 0.039 = 0.5377.
    SOLE_BELOW_COM = 0.5377
    return {"theHuman": ((0.0, 0.0, SOLE_BELOW_COM * scale), scale)}


def measure(nums):
    """Facts, and the checks that matter -- one against Earth, one against a person."""
    # EARTH, through the same laws.
    q_e = bearing_capacity(9.80665)
    sink_e = sinkage(9.80665)
    return {
        "soil_depth_m": nums["soil_depth_m"],
        "bare_rock_above_deg": nums["bare_rock_above_deg"],
        "bearing_capacity_kPa": nums["bearing_capacity_kPa"],
        "sinkage_mm": nums["sinkage_mm"],
        # SOIL THINS ON STEEP GROUND -- not put in anywhere; erosion rises with slope and the
        # production law does the rest.
        "soil_thins_uphill": nums["soil_depth_steep_m"] < nums["soil_depth_flat_m"],
        "bedrock_threshold_is_steep": 25.0 < nums["bare_rock_above_deg"] < 45.0,
        # A firm soil carries 100-300 kPa; a person standing puts ~20 kPa through one foot.
        "earth_bearing_is_soil_like": 80.0 < q_e / 1e3 < 400.0,
        "earth_sinkage_under_20mm": sink_e < 0.020,
        "holds_a_person": nums["holds_a_person"],
    }
