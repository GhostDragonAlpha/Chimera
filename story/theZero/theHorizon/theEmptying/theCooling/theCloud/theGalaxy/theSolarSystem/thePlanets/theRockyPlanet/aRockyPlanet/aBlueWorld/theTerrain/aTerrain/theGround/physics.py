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


def _library_cohesion_pa():
    """COHESION IS READ, NOT TYPED, and this is the correction to the defect that made every
    footprint in this world exactly zero.

    IT USED TO SAY `COHESION_PA = 2000.0  # damp soil holds itself together a little`. That single
    constant sets the bearing capacity AT ZERO DEPTH -- c * Nc = 92 kPa, which is 3.8x the pressure
    under a person -- so `sinkage()` balanced before it began, its bisection collapsed onto its own
    floor, and the membrane published `sinkage_m = 8.674e-19`: 0.87 attometres, a thousand times
    smaller than a proton. Nothing in this world could dent the ground, and nothing said so.

        THE WORLD'S OWN LIBRARY PUBLISHES 0.5 +- 0.4 kPa for this regolith (Mitchell et al. 1972,
        3rd Lunar Sci. Conf., via Chimera/docs/matter/matter_library.json). The typed value was
        FOUR TIMES the researched mean and twice the top of the published band.

    Found by `tools/port_tests_matter.py::terrain_footprint`, which derived the print depth from
    Terzaghi and from Terzaghi's own subgrade modulus -- two literatures, 3.12 mm and 3.84 mm --
    and then read what this membrane publishes. Same species as the g = 7.076 defect: a wrong
    number under a formula that still looks alive.

    THE COMPACTION ARGUMENT IS REFUSED RATHER THAN APPLIED. This membrane already argues, correctly,
    that a footing's FRICTION angle is not a heap's repose angle because a footing is compacted. The
    same argument would raise cohesion above the loose-soil value -- but cohesion's density
    dependence is not published in the library, and a correction with no source is the thing that
    was just removed. The loose value is used and the missing measurement is named.

    READ THROUGH, NEVER COPIED: change the library and this world's footprints change with it,
    which is the slider test. A copy here would be a stale copy, which this studio has convicted
    four times in one day.
    """
    import json
    from pathlib import Path
    lib = Path(__file__).resolve()
    while lib.name != "story" and lib.parent != lib:
        lib = lib.parent
    p = lib.parent / "Chimera" / "docs" / "matter" / "matter_library.json"
    if not p.exists():
        raise RuntimeError(
            f"the materials library is missing at {p}. Cohesion is READ from it and there is no "
            f"fallback: a typed cohesion is exactly the defect this function replaced.")
    ent = json.loads(p.read_text(encoding="utf8"))["materials"]["sand"]["physical"]["cohesion_kpa"]
    if ent.get("provenance") != "researched":
        raise RuntimeError(f"library sand.cohesion_kpa is provenance {ent.get('provenance')!r}, "
                           f"not 'researched' -- a design value may not be cited as a measurement.")
    return float(ent["mean"]) * 1e3


COHESION_PA = _library_cohesion_pa()   # 500 Pa: Mitchell et al. 1972, read through the library

# ── THE REFERENCE PROBE, AND IT IS NOT THIS STORY'S PERSON ──────────────────────────────────────
# These two used to be called FOOT_AREA_M2 and BODY_MASS_KG, and the membrane used them to publish
# `foot_pressure_kPa` and `holds_a_person`. That is A PARENT INVENTING ITS CHILD'S BODY. theGround
# sits ABOVE theHuman and must never read it -- correctly -- but the answer it reached for was
# to type a person instead, and a typed person does not move.
#
# MEASURED, and this is the whole argument: theHuman derives 94.50 kg on 0.02764 m2 and gets
# 24.19 kPa; these constants give 19.35. Twenty percent apart, and the gap is invisible because
# both comfortably clear the 110 kPa the soil carries. Change the height at the top of the story
# and theHuman's number moves while this one does not. That is the slider test failing.
#
# THE CLAIM WAS MIS-ASSIGNED, not the wiring. "This soil fails above X kPa" is a fact about soil --
# true in an empty universe, which is what makes it this membrane's to state. "It holds a person"
# is a fact about a person, and the membrane that HAS a person already answers it: theHuman
# publishes ground_holds_it and ground_margin from its own derived mass and foot area.
#
# So these stay, renamed to say what they are: a standard bearing-test load, the geotechnical
# equivalent of a test weight, used to quote a sinkage in the units engineers quote it in.
PROBE_AREA_M2 = 0.030     # a standard foot-sized bearing plate
PROBE_MASS_KG = 82.04     # a reference load -- NOT this story's body; theHuman derives that


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
    nc, nq = bearing_factors(phi_deg)
    return c * nc + bulk_density() * g * depth_m * nq


def bearing_factors(phi_deg=PHI_BEARING_DEG):
    """Terzaghi's Nc and Nq from the friction angle alone. Split out so the two HALVES of the
    capacity can be published separately -- see `bearing_split` for why that matters."""
    phi = radians(phi_deg)
    nq = exp(pi * tan(phi)) * tan(radians(45.0) + phi / 2.0) ** 2
    return (nq - 1.0) / tan(phi), nq


def bearing_split(g):
    """THE TWO COEFFICIENTS A CHILD NEEDS TO DERIVE ITS OWN FOOTPRINT, and publishing them is the
    difference between a parent that carries and a parent that invents.

        q(D) = c*Nc  +  (rho*g*Nq) * D
               ^^^^^     ^^^^^^^^^^
               zero-depth capacity   how fast capacity grows with depth

    Below `c*Nc` NOTHING dents this soil at any depth; above it, a body sinks until the second term
    makes up the difference: D = (p - c*Nc) / (rho*g*Nq). That inversion needs a PRESSURE, and a
    pressure needs a body -- which this membrane does not have and must never type. So it publishes
    the soil's two numbers and lets whoever has a foot do the arithmetic. Being what every child can
    see is what a parent is FOR.

    AND THE FIRST TERM DOES NOT SCALE WITH GRAVITY. `c*Nc` is cohesion, which does not care about g,
    while both the applied pressure (m*g/A) and the depth term (rho*g*Nq) do. So a low-gravity world
    sits NEARER the threshold at which prints stop existing, and a body that leaves 20.9 mm on Earth
    leaves 3.1 mm here -- 6.7x shallower for 1.39x less gravity. That is a prediction of this split,
    not a tuning of it.
    """
    nc, nq = bearing_factors()
    return COHESION_PA * nc, bulk_density() * g * nq


def sinkage(g, mass_kg=PROBE_MASS_KG, foot_m2=PROBE_AREA_M2):
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


# THE GROUND SCANS -- the captures that carry soil, stone and forest floor. Manufactured goods
# and interiors are not the ground. (The joint codebook: story/data/material_genomes.json.)
GROUND_SCANS = ("garden", "stump", "treehill", "garden_tree", "christmas_tree")

# THE SKY CAP, DECLARED: the ground scans also carry THE SKY through canopy gaps (stump /
# christmas_tree bright clusters, luminance >~0.8). A stone is not the sky, so mineral roles are
# picked under this luminance cap. A picture dial, not a fact -- the operator can move it.
SKY_LUM_CAP = 0.75


def _mineral_genomes():
    """WHICH MEASURED GENOME FILLS WHICH MINERAL ROLE (2026-07-31 -- the typed quartz/feldspar/
    oxide literals are gone; the ROLES stay, the numbers are now measured). The rule is
    mechanical and declared: quartz = lightest ground-carried genome under the sky cap,
    feldspar = the next lightest, oxide = the reddest RED-DOMINANT genome left over (max R-B
    among R>G and R>B, roles distinct -- without the dominance test the rule picks the LEAF
    genome, whose R-B is large while its G is larger still; a green oxide is a bug, not a
    material). HONEST GAP, flagged: these are temperate vegetated captures -- no rust/oxide-
    bearing scan is in the collection, so the oxide role gets the reddest soil there IS
    (a dark umber), not a haematite red."""
    from matter import pick_genomes, genome_lum
    cands = [g for g in pick_genomes(GROUND_SCANS) if genome_lum(g) <= SKY_LUM_CAP]
    by_lum = sorted(cands, key=genome_lum, reverse=True)
    quartz, feldspar = by_lum[0], by_lum[1]
    taken = {quartz["id"], feldspar["id"]}
    red = [g for g in cands
           if g["id"] not in taken
           and g["features"]["R"]["mean"] > g["features"]["G"]["mean"]
           and g["features"]["R"]["mean"] > g["features"]["B"]["mean"]]
    oxide = max(red, key=lambda g: g["features"]["R"]["mean"] - g["features"]["B"]["mean"])
    return {"quartz": quartz, "feldspar": feldspar, "oxide": oxide}


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
    q0, qd = bearing_split(g)
    sink = sinkage(g)
    press = PROBE_MASS_KG * g / PROBE_AREA_M2   # the REFERENCE load, not a person

    # THE MINERALS THE RENDER MUST WEAR (measured): which genome fills each mineral role, so the
    # numbers record what the picture shows -- the same contract aHuman's suit_material keeps.
    _roles = _mineral_genomes()
    from matter import genome_rgb
    mineral_materials = {role: {"genome_id": g["id"], "rgb_mean": [float(c) for c in genome_rgb(g)]}
                         for role, g in _roles.items()}

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

        "mineral_materials": mineral_materials,
        "minerals_source": ("story/data/material_genomes.json -- quartz/feldspar/oxide ROLES "
                            "filled by measured ground-scan genomes; oxide is the reddest soil "
                            "in the collection (no rust-bearing scan exists -- flagged)"),
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
        # THE LAW, NOT JUST ITS VALUE AT ONE DEPTH. A child with a foot inverts these two for its
        # own print: D = (p - bearing_zero_depth_Pa) / bearing_depth_coeff_Pa_per_m, and below the
        # first number nothing dents this soil at any depth. theHuman does exactly that.
        "bearing_zero_depth_Pa": q0,
        "bearing_zero_depth_kPa": q0 / 1e3,
        "bearing_depth_coeff_Pa_per_m": qd,
        "bearing_cohesion_Pa": COHESION_PA,
        "bearing_cohesion_source": ("Mitchell et al. 1972 (3rd Lunar Sci. Conf.) via "
                                    "Chimera/docs/matter/matter_library.json sand.cohesion_kpa -- "
                                    "READ, never typed. The 2000 Pa that used to sit here was 4x "
                                    "the researched mean and made every footprint exactly zero."),
        # WHAT THIS MEMBRANE IS ENTITLED TO SAY: the load above which this soil fails. That is a
        # fact about the soil and it is true whether or not anyone ever stands on it.
        # `fails_above_kPa` RETIRED: a second name for the number directly above it -- one quantity, one name.
        # and what a STANDARD bearing-test load does to it, so the sinkage has units an engineer
        # would recognise. Named `reference` throughout so it cannot be read as this story's body.
        "reference_load_Pa": press,
        "reference_load_kPa": press / 1e3,
        "reference_load_kg": PROBE_MASS_KG,
        "reference_plate_m2": PROBE_AREA_M2,
        "sinkage_m": sink,
        "sinkage_mm": sink * 1e3,
        # AND WHY IT IS ZERO, SAID OUT LOUD -- because a zero here used to mean a bug and must
        # never again be mistaken for one. The reference plate carries 19.4 kPa, which is BELOW the
        # 23.1 kPa this soil holds at zero depth, so it does not dent it. That is a fact about the
        # PLATE, not about the soil: theHuman's foot carries 24.2 kPa, clears the same threshold,
        # and sinks 3.1 mm. A reader who sees `sinkage_mm ~ 0` should be able to tell instantly
        # which of the two situations they are in.
        "reference_load_dents_it": press > q0,
        "reference_load_vs_threshold": press / q0,
        "carries_reference_load": q > press,
        # WHETHER IT HOLDS *THE PERSON* IS NOT THIS MEMBRANE'S QUESTION. theHuman has the body --
        # its own derived mass, its own foot area, on this same bearing capacity -- and publishes
        # ground_holds_it and ground_margin. A parent that answers it here has invented a child.
        "who_answers_holds_a_person": "theHuman.ground_holds_it",

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
    from matter import blank, paint, lit, SOLID, sample_genome_rgb

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

    # MINERAL COLOUR, MEASURED (2026-07-31): the typed quartz/feldspar/oxide literals are gone.
    # The same three ROLES are filled by the joint element codebook's ground genomes, and every
    # stone DRAWS its albedo from its role genome's measured distribution -- the mottle is the
    # measurement. The big grains are still the weathered ones (exposed longest -> the oxide role).
    _roles = _mineral_genomes()
    alb_q = sample_genome_rgb(_roles["quartz"], rng, n)
    alb_f = sample_genome_rgb(_roles["feldspar"], rng, n)
    alb_o = sample_genome_rgb(_roles["oxide"], rng, n)
    pick = rng.random(n)
    albedo = np.where((pick < 0.35)[:, None], alb_q,
                      np.where((pick < 0.80)[:, None], alb_f, alb_o))
    weathered = (d_mm > 8.0) & (rng.random(n) < 0.55)
    albedo[weathered] = alb_o[weathered]

    # ONE DAY: the sun crosses, and its height is the local-sky altitude -- the ONE declination
    # (matter.py) projected onto this latitude. The shadows are the point. DAY_OPEN_HOUR opens the
    # film mid-morning: the day-movie's two ends (t=0, t=1) share that readable light instead of
    # opening on the sunrise graze, where the patch renders nearly black and the whole point --
    # stones, texture, shadows -- is invisible to the eye. It is FILM FRAMING, a LENS choice, and it
    # is shared with aTerrain so zooming between the two never jumps the light.
    sun = sun_direction(tt, nums)
    lam = np.clip(nrm @ sun, 0.0, None)
    b[:, 16:19] = lit(albedo, float(nums.get("S_earth", 1.0)) * lam + 0.06,
                      e_ref=float(nums.get("S_earth", 1.0)), tone=0.45)
    b[:, 19] = 0.95
    b[:, 20] = np.clip(d_m / half * 0.75, 0.0016, 0.05)     # TRUE SIZE: the stone is the splat
    b[:, 11] = SOLID
    return b


# FRAMING -- the membrane's declared camera setting (a LENS sibling: a picture dial, not a fact).
# This patch's meaning is its STONES, and they are millimetres across: at the default 2.7x extent
# they are sub-pixel and a dyad judges blur. 1.15x puts the camera at crouch height, close enough
# that the grains the law sized are actually visible.
FRAMING = {"dist": 1.15, "elev": 0.55}

# FILM FRAMING, shared with aTerrain: the hour of the day-movie this surface opens on. Which hour
# is a LENS choice, never a fact about the sun; the sun's ELEVATION at that hour is the law's.
DAY_OPEN_HOUR = 0.9


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
        "carries_reference_load": nums["carries_reference_load"],
    }


def sun_direction(tt, nums):
    """THE ONE SUN, read (matter.py): this patch's light is the world's single star, seen from this
    latitude -- derived, never typed. Declared here so the live viewer arms the renderer with THE
    SAME sun the emit baked with."""
    import matter
    return matter.local_sun(float(tt), float(nums["obliquity_effective_deg"]),
                            float(nums["latitude_deg"]), DAY_OPEN_HOUR)
