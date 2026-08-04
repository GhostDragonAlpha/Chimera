"""theLoad -- what a body carries, and the four different ways it stops you.

THE EDGE. theHuman is a body that walks. Put a mass on it and it is a DIFFERENT body: heavier,
higher-centred, leaning, burning more, pressing harder into the ground. Nothing here is designed --
one added mass at one added height is the whole input, and every consequence is an arithmetic
consequence of it. That is the test of this chapter: if a number had to be chosen for the loaded
body that was not needed for the bare one, the derivation leaked.

WHAT IT SAYS, in order:

  1. THE COMBINED BODY. A mass m at height h and offset x behind gives one new centre of mass, one
     new fall rate, and one forward LEAN -- the lean that puts the combined CoM back over the ankle.
     `tan(lean) = m*x / (M*H + m*h)` exactly, no small-angle anywhere.

  2. WHICH STABILITY EFFECT WINS, and the answer is neither of the two the question offers. A pack
     RAISES the CoM, so w0 = sqrt(g/H) falls and the body topples MORE SLOWLY. That buys nothing:
     the time you gain is `1/w0` and the distance your capture point runs out to is `v/w0`, so both
     grow by the SAME factor and their ratio is still v. The extra time is exactly the extra ground
     to cover. What actually changes the margin is that THE FOOT DID NOT GET BIGGER -- and, far
     bigger than either, that the same ankle must hold a heavier body over the same toe. MEASURED
     HERE at 30% of body mass: geometry costs 4.7% of the lean limit, the mass costs 25.7% more
     ankle torque. The mass wins by five to one, and the slow topple is an illusion of safety.

  3. WHAT IT COSTS. Pandolf, Givoni & Goldman (1977) -- the US Army equation, fitted on treadmills,
     four terms. Its FIRST prediction is one it was never asked for: the grade coefficient 0.35
     contains a 28.0% muscular efficiency (`0.35 * 0.2803 = 9.81/100`), and the literature figure
     for positive work in walking is 25-30%. That identity is also what lets the equation off Earth,
     because it says the grade term is exactly proportional to g.

  4. THE KNEE, AND IT IS REAL AND IT IS NOT WHERE YOU LOOK FOR IT. Pandolf's load term is a
     polynomial, so the cost curve is smooth -- there is NO break in it anywhere, and any derivation
     claiming to find the famous "30%" as a kink in that curve has fitted it. The knee is in the
     MARGINAL comparison instead: differentiate the cost with respect to load and with respect to
     body mass and subtract, and every speed, grade and terrain term cancels, leaving

         2*b*f*(1+f)^2 = a          f = carried mass / body mass

     -- the load fraction above which one more kilogram in the pack costs more than one more
     kilogram of you. On Earth that is f = 0.243. The classic band, from porters and from soldiers,
     is 20-30%. NOTHING WAS FITTED: a and b are Pandolf's own 1.5 and 2.0.

  5. GRAVITY IS THE DIAL, AND IT MOVES THE KNEE. `a` is chemistry and `b` is weight, so lower g
     raises the knee: 24.3% on Earth, 28.5% here at 7.076, 62% on the Moon. And the check is not
     ours: NASA TN D-7883 measured 158.76 hours of Apollo lunar EVA and reports a mean of
     980 kJ/hr = 272 W. Pandolf UNSCALED, run on a suited Apollo astronaut, says 734 W -- wrong by
     2.7x. Pandolf with the gravity scaling above says 243-282 W. The scaling is not decoration.

  6. AND THE GROUND HAS A VOTE. theHuman's boot sits at 24.19 kPa against 110.35 kPa of bearing
     capacity. Ultimate failure needs 337 kg of cargo and never happens. But no foundation is
     designed to its ultimate -- the standard factor of safety is 3 -- and at q/3 the ground starts
     to take a print at 49 kg, which is inside the range a person actually carries. So the answer to
     the stub's own question is: YES, IT BITES, but only once you stop asking when the ground fails
     and start asking when it yields.

WHAT IT CONSUMES from theHuman, and nothing else: height_m, mass_kg, bare_mass_kg, suit_mass_kg,
com_height_m, leg_length_m, g, fall_rate_rad_s, comfortable_speed_ms, cadence_steps_s, step_length_m,
foot_area_m2, foot_pressure_kPa, ground_bearing_kPa, forefoot_lever_m, heel_lever_frac,
ankle_torque_Nm, excursion_hours, S_earth, duration_s.

WHAT IS NOT DERIVED HERE, stated because it has to be:
  * the TERRAIN FACTOR. Pandolf's eta is a property of the GROUND, and it should arrive down the
    chain from theGround through theHuman. theHuman publishes no such number, so it is a free dial
    here with Soule & Goldman's measured values as its range. This is the one number in this chapter
    that is in the wrong place.
  * eta AT REDUCED GRAVITY. Nobody has measured a terrain coefficient off Earth. Holding eta fixed
    makes the per-step sinkage come out gravity-INVARIANT, which cannot be true (a lighter foot
    presses less), so that invariance is an artifact of the assumption and is reported as one.
  * the CARGO DENSITY and the Apollo masses. Density is free with a sourced default; the Apollo body
    and EMU masses are the only two literals in this file that are not in this repository, and the
    Apollo check is published with its sensitivity so it does not hang on them.
  * the SUIT'S OWN CoM. theHuman publishes com_height_m = 0.575 * stature, which is the bare
    anthropometric figure, while its mass_kg already includes 9.91 kg of suit. Applying this
    chapter's own law to the suit would raise that CoM about 1.5 cm. The parent's number is consumed
    as published and the discrepancy is named rather than silently corrected.

Contained in theHuman. Its movie is ONE EXCURSION: eight hours, a hopper filling, and the limits
crossed in the order the physics puts them in.
"""
from __future__ import annotations

import math

import numpy as np


# ══ THE MEASURED BODY THE PACK RIDES ON ══════════════════════════════════════════════════════════
# ANSUR II (US Army 2012, public 2017), MALE, n = 4,082, median stature 1755 mm -- the same survey
# and the same median body theHuman derives itself from, so a pack sized from these fractions is
# sized to THIS person and not to a generic one. Medians read directly off
# research_references/human/ANSUR_II_MALE_Public.csv.
ACROMION_FRAC = 1439.0 / 1755.0        # 0.8199  shoulder height -- the top of the load-bearing span
ILIOCRISTALE_FRAC = 1061.0 / 1755.0    # 0.6046  iliac crest -- where a hip belt takes the weight
BIACROMIAL_FRAC = 415.0 / 1755.0       # 0.2365  shoulder breadth -- how wide a pack may be before
                                       #         it fouls the arms and stops them counter-swinging
CHESTDEPTH_FRAC = 253.0 / 1755.0       # 0.1442  torso depth -- the standoff between the body's own
                                       #         mid-plane and the pack's front face

# ══ PANDOLF, GIVONI & GOLDMAN 1977 ═══════════════════════════════════════════════════════════════
# "Predicting energy expenditure with loads while standing or walking very slowly",
# J Appl Physiol 43(4):577-581. The US Army's load-carriage equation, fitted to treadmill
# calorimetry and still the standard:
#
#     M = 1.5 W + 2.0 (W+L)(L/W)^2 + eta (W+L)(1.5 V^2 + 0.35 V G)     [W, kg, kg, m/s, %]
#
# Four coefficients, and one of them audits itself -- see grade_efficiency() below.
PANDOLF_REST = 1.5     # W per kg of body mass, standing
PANDOLF_LOAD = 2.0     # W per kg of (body+load), per unit (L/W)^2
PANDOLF_SPEED = 1.5    # W per kg of (body+load), per (m/s)^2
PANDOLF_GRADE = 0.35   # W per kg of (body+load), per (m/s) per percent of grade

G_EARTH = 9.80665
G_MOON = 1.62          # lunar surface gravity, the third rung of the gravity dial

# TERRAIN COEFFICIENTS, MEASURED: Soule & Goldman (1972), "Terrain coefficients for energy cost
# prediction", J Appl Physiol 32:706-708. These are the multiplier eta above.
TERRAIN = {"blacktop": 1.0, "dirt road": 1.1, "light brush": 1.2, "heavy brush": 1.5,
           "swampy bog": 1.8, "loose sand": 2.1}

# ══ HOW MUCH OF STANDING STILL IS GRAVITY ════════════════════════════════════════════════════════
# NASA CR-1726 (1971), the reduced-gravity/bioastronautics handbook now in this repo
# (research_references/human/eva/), Webb's oxygen-cost table for one 167 lb man:
#     lying fully relaxed  290 Btu/hr        standing relaxed  440 Btu/hr
# The difference is the cost of holding yourself up against g; the remainder is chemistry that would
# read the same in free fall. That split is what lets Pandolf's rest term go to another world.
REST_LYING_BTU_HR = 290.0
REST_STANDING_BTU_HR = 440.0
POSTURAL_SHARE = 1.0 - REST_LYING_BTU_HR / REST_STANDING_BTU_HR      # 0.3409

# ══ WHAT A PERSON CAN HOLD FOR A WORKING DAY ═════════════════════════════════════════════════════
# Indirect calorimetry: 20.9 kJ of heat per litre of oxygen at RQ 0.85, a mixed diet (Brockway 1987
# gives 20.1-21.1 kJ/l over RQ 0.7-1.0). theHuman's own scrubber chemistry already uses RQ = 0.85,
# so the two agree by construction rather than by luck.
O2_KJ_PER_LITRE = 20.9
# The fraction of maximal aerobic power a person can sustain, by duration: Astrand & Rodahl,
# Textbook of Work Physiology -- about half of VO2max for an hour, about a third for an eight-hour
# working day. TWO ANCHORS, and the exponent between them is DERIVED, not chosen.
SUSTAIN_1H, SUSTAIN_8H = 0.50, 0.33

# ══ THE CHECK THAT IS NOT OURS ═══════════════════════════════════════════════════════════════════
# NASA TN D-7883 (Waligora, Hawkins, Humbert, Nelson, Vogel & Kuznetz, March 1975), "Apollo
# Experience Report -- Assessment of Metabolic Expenditures", TABLE I. 158.76 hours of Apollo 11-17
# lunar surface EVA, measured three independent ways (heart rate, oxygen consumption, liquid-cooled
# garment heat balance) and integrated. PDF in research_references/human/eva/.
APOLLO_MEAN_KJ_HR = 980.0     # mean, all activities, all missions
APOLLO_LO_KJ_HR = 822.0       # the range of per-EVA averages the report states
APOLLO_HI_KJ_HR = 1267.0
# THE TWO LITERALS IN THIS FILE THAT ARE NOT IN THIS REPOSITORY. Apollo crew body mass and the
# A7LB pressure garment + PLSS/OPS mass are widely documented (~75 kg and ~82 kg respectively) but
# neither is in a file here, so they are declared as assumptions and the check below is published
# with its sensitivity rather than as a point value.
APOLLO_BODY_KG = 75.0
APOLLO_EMU_KG = 82.0
APOLLO_SPEED_MS = 0.9         # assumed lunar walking speed; the sensitivity is published

# ══ WHEN THE GROUND GIVES ════════════════════════════════════════════════════════════════════════
# Terzaghi & Peck and every shallow-foundation text since: an ULTIMATE bearing capacity is the
# pressure at which the soil fails, and nothing is ever designed to it. The standard factor of
# safety for a footing is 3, and the allowable pressure is q_u/3. That is a design convention, not
# a physical threshold, and both numbers are published so a reader can tell them apart.
BEARING_SAFETY_FACTOR = 3.0

# ══ THE CARGO ════════════════════════════════════════════════════════════════════════════════════
# Solid basalt has a grain density near 2900 kg/m3 (standard petrophysics), and broken rock occupies
# about 1.55 times its in-situ volume (the mining "swell factor", 1.5-1.65 for hard rock). Loose
# broken basalt is therefore 2900/1.55 = 1871 kg/m3 -- the default a hopper of ore is filled with.
BASALT_GRAIN_KG_M3 = 2900.0
ROCK_SWELL = 1.55


FREE = {
    # HOW MUCH YOU DECIDED TO CARRY. Not a law: a person picks this up. The default is the figure
    # every army in the world writes down -- 30% of body mass -- and it is here as a DEFAULT, not as
    # a derivation, precisely so that the derived knee at 28.5% can disagree with it and be seen to.
    "cargo_fraction": {"lo": 0.0, "hi": 0.80, "default": 0.30,
                       "label": "cargo carried", "unit": "of bare body mass",
                       "local": "what you chose to pick up"},

    # HOW HIGH YOU PACKED IT. 0 = the pack spans hip belt to shoulders and no further, which is the
    # span the anatomy itself defines; 1 = it is built up until its top is level with the top of the
    # head. THIS DIAL HAS A REAL TRADE-OFF IN IT and the chapter does not resolve it: a taller pack
    # of the same volume is THINNER, so it sits closer in and demands less forward lean -- and it is
    # also HIGHER, so it lowers w0 and shortens the shove you can take. Doctrine says load high;
    # anyone who has carried one over broken ground says load low. Both are reading a real number.
    "pack_high": {"lo": 0.0, "hi": 1.0, "default": 0.0,
                  "label": "how high it is packed", "unit": "of the span above the shoulders",
                  "local": "hip-to-shoulder, or built up over the head"},

    # WHAT THE CARGO IS. Mass is what tires you; VOLUME is what forces the pack away from your back
    # and makes you lean. Two loads of the same mass do not cost the same. The default is derived
    # from basalt above; the range runs from packed snow to massive sulphide ore.
    "cargo_density_kg_m3": {"lo": 300.0, "hi": 5000.0,
                            "default": BASALT_GRAIN_KG_M3 / ROCK_SWELL,
                            "label": "cargo density", "unit": "kg/m3",
                            "local": "what is in the hopper"},

    # WHAT YOU ARE WALKING ON. THIS ONE IS IN THE WRONG PLACE and the docstring says so: eta belongs
    # to theGround. Range and labels are Soule & Goldman's measured coefficients.
    "terrain_factor": {"lo": 1.0, "hi": 2.1, "default": 1.2,
                       "label": "terrain factor", "unit": "Soule & Goldman eta",
                       "local": "blacktop 1.0 -> loose sand 2.1; belongs to theGround, not here"},

    # UP OR DOWN. Pandolf is valid for level and positive grades; it is known to over-predict on
    # descents (the equation has no eccentric-work term), so the dial is clamped at 0 and the
    # limitation is stated rather than papered over.
    "grade_pct": {"lo": 0.0, "hi": 25.0, "default": 0.0,
                  "label": "grade walked", "unit": "percent",
                  "local": "how steep the ground is"},

    # WHO IS CARRYING IT. Aerobic capacity is a fact about a person, like theHuman's height and its
    # melanin -- the third HUMAN-terminal dial on this body. Range: ACSM normative VO2max for a
    # 30-39 year-old male, which is exactly the age group theHuman's measured gait comes from.
    "aerobic_capacity": {"lo": 30.0, "hi": 60.0, "default": 45.0,
                         "label": "VO2max", "unit": "ml O2 per kg per minute",
                         "local": "fitness -- the operator's call, the measured range ACSM's"},
}


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE LAWS. Module level, because emit() runs every one of them again at every instant of the
#  excursion -- so the picture cannot drift from the numbers, it IS the numbers at another t.
# ════════════════════════════════════════════════════════════════════════════════════════════════
def combined_com(M, H, m, h):
    """One body and one load make ONE centre of mass. The whole chapter hangs off this line."""
    M, m = float(M), float(m)
    return (M * float(H) + m * float(h)) / max(M + m, 1e-12)


def lean_angle(M, H, m, h, x):
    """THE FORWARD LEAN a load behind you forces, exactly.

    Pivot at the ankle. Lean the whole rigid assembly forward by phi: the body's CoM goes to
    (H sin phi, H cos phi) and the load, which is bolted to it, goes to
    (h sin phi - x cos phi, h cos phi + x sin phi). Setting the combined horizontal coordinate to
    zero -- the combined CoM over the ankle, which is what standing up means -- gives

        M H sin phi + m h sin phi = m x cos phi   ->   tan phi = m x / (M H + m h)

    No small-angle approximation and no fitted constant. Note what the denominator says: a load
    carried HIGH resists the lean it causes, because its own height is in the restoring term."""
    return math.atan2(float(m) * float(x), float(M) * float(H) + float(m) * float(h))


def pack_geometry(stature_m, volume_m3, pack_high):
    """THE SHAPE OF THE THING ON YOUR BACK, from the body's own measured breadths.

    Width is the shoulders (wider and the arms cannot swing past it). The span runs from the hip
    belt at the iliac crest up to the shoulders, and `pack_high` builds it further up towards the
    top of the head. Depth is then whatever the volume requires -- which is why a bulky cargo makes
    a DEEP pack, and a deep pack sits further behind you, and that is the whole reason volume
    appears in a chapter about mass."""
    s = float(stature_m)
    width = BIACROMIAL_FRAC * s
    span_lo = (ACROMION_FRAC - ILIOCRISTALE_FRAC) * s          # the anatomy's own span
    span_hi = (1.0 - ILIOCRISTALE_FRAC) * s                    # built up to the top of the head
    span = span_lo + min(max(float(pack_high), 0.0), 1.0) * (span_hi - span_lo)
    depth = float(volume_m3) / max(width * span, 1e-12)
    base = ILIOCRISTALE_FRAC * s
    standoff = 0.5 * CHESTDEPTH_FRAC * s                       # body mid-plane to the back surface
    return {"width_m": width, "span_m": span, "depth_m": depth, "base_m": base,
            "com_height_m": base + 0.5 * span, "offset_m": standoff + 0.5 * depth}


def grade_efficiency():
    """WHAT PANDOLF'S GRADE COEFFICIENT KNOWS THAT PANDOLF DID NOT PUT IN IT.

    Climbing at V m/s on a grade of G percent lifts (W+L) kg at V*G/100 m/s, so the MECHANICAL power
    is (W+L) * g * V * G / 100 = 0.0981 (W+L) V G on Earth. Pandolf's metabolic coefficient for the
    same term is 0.35. The ratio is the efficiency with which muscle turns fuel into height:

        0.0981 / 0.35 = 0.2803

    28.0%. The measured efficiency of positive muscular work in walking is 25-30%. Nothing was
    fitted to that -- 0.35 came out of a treadmill regression -- and it is the single fact that
    licenses taking this equation to another planet, because it says the grade term is EXACTLY
    proportional to g."""
    return (G_EARTH / 100.0) / PANDOLF_GRADE


def gravity_coefficients(g):
    """PANDOLF'S FOUR TERMS, TAKEN OFF EARTH. Each scaling is labelled by how much it is worth.

      rest    a  -- DERIVED FROM A MEASUREMENT (CR-1726's lying-vs-standing pair): the chemistry
                    part is g^0 and the postural part is g^1.
      load    b  -- ASSUMED g^1. It is weight being stabilised, and weight is mg. Untested.
      speed  kv  -- SIMILARITY, g^0.5. A body's own frequency is sqrt(g/L); Pandolf's speed
                    coefficient carries the dimension of a frequency (1/s), and dynamic similarity
                    -- the Froude argument this whole story walks on -- makes it scale with one.
                    Untested; no reduced-gravity load-carriage calorimetry exists.
      grade  kg  -- DERIVED, g^1, exactly, from grade_efficiency() above.

    Three of the four are arguments rather than results, and the honest weight of this function is
    carried by the Apollo comparison at the bottom of derive(), which tests all four at once."""
    gr = float(g) / G_EARTH
    return {
        "rest": PANDOLF_REST * ((1.0 - POSTURAL_SHARE) + POSTURAL_SHARE * gr),
        "load": PANDOLF_LOAD * gr,
        "speed": PANDOLF_SPEED * math.sqrt(gr),
        "grade": PANDOLF_GRADE * gr,
        "g_ratio": gr,
    }


def pandolf(W_body, L_carried, v_ms, grade_pct, eta, g):
    """The metabolic rate of a loaded body, term by term, in watts."""
    c = gravity_coefficients(g)
    W, L = float(W_body), max(float(L_carried), 0.0)
    X = W + L
    f = L / max(W, 1e-12)
    rest = c["rest"] * W
    load = c["load"] * X * f * f
    speed = float(eta) * X * c["speed"] * float(v_ms) ** 2
    grade = float(eta) * X * c["grade"] * float(v_ms) * max(float(grade_pct), 0.0)
    return {"rest_W": rest, "load_W": load, "speed_W": speed, "grade_W": grade,
            "total_W": rest + load + speed + grade, "fraction": f}


def knee_fraction(g):
    """THE LOAD FRACTION AT WHICH CARRYING STOPS BEING CHEAP, and every other variable cancels.

    Differentiate the metabolic rate twice, once with respect to the LOAD and once with respect to
    the BODY, and subtract. Everything with eta, V or G in it multiplies (W+L) linearly and drops
    out identically:

        dM/dL - dM/dW = 2 b f (1+f)^2 - a

    Below the root, a kilogram in the pack is cheaper than a kilogram of you; above it, it is dearer.
    That is a real economic threshold and it needed no curve-reading to find. On Earth (a=1.5,
    b=2.0, Pandolf's own numbers, nothing fitted) the root is f = 0.243, and the load-carriage
    literature -- soldiers, and Nepalese and African porters -- puts the economical band at 20-30%.

    IT ALSO SAYS WHAT NOBODY MEASURED: a is chemistry and b is weight, so the knee RISES as gravity
    falls. 24.3% on Earth, 62% on the Moon, and an Apollo crewman carried more than his own body
    mass in suit and backpack without the equation calling it extravagant."""
    c = gravity_coefficients(g)
    a, b = c["rest"], c["load"]
    if b <= 0.0:
        return float("inf")                 # in free fall, carrying is free. Correct.
    target = a / (2.0 * b)
    lo, hi = 0.0, 1.0
    while hi * (1.0 + hi) ** 2 < target and hi < 1e6:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid * (1.0 + mid) ** 2 < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def sustainable_power(body_kg, vo2max_ml_kg_min, hours):
    """WHAT A PERSON CAN HOLD FOR A WHOLE EXCURSION, and it is a ceiling, not a preference.

    Oxygen uptake x 20.9 kJ per litre gives the aerobic ceiling in watts. What can be SUSTAINED is a
    fraction of it that falls with duration: Astrand & Rodahl's two anchors are ~50% for an hour and
    ~33% for eight. The exponent between them is derived -- ln(0.33/0.50)/ln(8) = -0.200 -- not
    picked, and -0.2 is the exponent the endurance-time literature keeps arriving at independently."""
    vo2_l_min = float(vo2max_ml_kg_min) * float(body_kg) / 1000.0
    ceiling_W = vo2_l_min * O2_KJ_PER_LITRE * 1000.0 / 60.0
    p = math.log(SUSTAIN_8H / SUSTAIN_1H) / math.log(8.0)
    frac = SUSTAIN_1H * max(float(hours), 1e-6) ** p
    return ceiling_W, frac, ceiling_W * frac


def sinkage_per_step(eta, v_ms, g, cadence_steps_s):
    """HOW DEEP THE BOOT GOES, read out of the terrain factor rather than out of a soil model.

    A terrain coefficient eta multiplies the walking term, so the EXTRA power it charges is
    (eta-1) * X * kv * v^2. If all of that extra is the work of compacting ground under the boot,
    then per step it is N*z with N = X*g, and the whole mass cancels:

        z = (eta - 1) * kv * v^2 / (g * cadence)

    On Earth at 1.17 m/s this returns 117 mm for loose sand (eta = 2.1) and 25 mm for light brush.
    Boots do sink about that far in deep sand. It is an UPPER BOUND -- brush also snags and sand
    also slips backwards, and neither of those is compaction -- and it is the only place in this
    chapter where a terrain factor is asked to say something physical."""
    c = gravity_coefficients(g)
    return (float(eta) - 1.0) * c["speed"] * float(v_ms) ** 2 / max(float(g) * float(cadence_steps_s), 1e-12)


def stability(M_total, com_h, g, toe_lever_m, ankle_torque_Nm):
    """THE THREE NUMBERS THAT SAY HOW EASY YOU ARE TO PUSH OVER.

    The base of support is the limit that binds in reality -- you may lean until the centre of
    pressure reaches the toe, and the plantarflexors can produce that torque (anyone can rise onto
    their toes, which is the whole body weight at that same lever). So the LEAN LIMIT is geometry,
    atan(toe / H), and the mass cancels out of it completely: both the toppling moment and the
    restoring ground reaction are proportional to weight.

    The SHOVE LIMIT is Hof's condition -- the extrapolated centre of mass, x + v/w0, must stay
    inside the base of support -- so v_max = toe * w0 = toe * sqrt(g/H).

    And the ANKLE DEMAND is what the muscle is being asked for at that limit, expressed against the
    torque theHuman measured its ankle producing at push-off. That torque is a WALKING number, not a
    maximum voluntary contraction, so a ratio above 1 does not mean failure -- it means the ankle is
    being asked for more than it spends on a step, and it is the only one of the three that grows
    with mass."""
    W_N = float(M_total) * float(g)
    w0 = math.sqrt(float(g) / max(float(com_h), 1e-12))
    lean_lim = math.atan(float(toe_lever_m) / max(float(com_h), 1e-12))
    return {
        "fall_rate_rad_s": w0,
        "topple_time_s": 1.0 / w0,
        "lean_limit_rad": lean_lim,
        "shove_limit_ms": float(toe_lever_m) * w0,
        "ankle_demand_ratio": W_N * float(toe_lever_m) / max(float(ankle_torque_Nm), 1e-12),
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE EDGE
# ════════════════════════════════════════════════════════════════════════════════════════════════
def derive(parent, free):
    if parent is None or "bare_mass_kg" not in parent or "com_height_m" not in parent:
        raise ValueError("theLoad requires theHuman as its parent")
    free = free or {}

    def dial(k):
        return float(free.get(k, FREE[k]["default"]))

    cargo_frac = dial("cargo_fraction")
    high = dial("pack_high")
    rho = dial("cargo_density_kg_m3")
    eta = dial("terrain_factor")
    grade = dial("grade_pct")
    vo2 = dial("aerobic_capacity")

    # ── what the parent hands down ──────────────────────────────────────────────────────────────
    h_m = float(parent["height_m"])
    M_suited = float(parent["mass_kg"])          # body + suit: the thing that already walks
    W_bare = float(parent["bare_mass_kg"])       # Pandolf's W is the PERSON
    suit = float(parent["suit_mass_kg"])         # ... and the suit is already a load
    H0 = float(parent["com_height_m"])
    g = float(parent["g"])
    v = float(parent["comfortable_speed_ms"])
    cadence = float(parent["cadence_steps_s"])
    step_len = float(parent["step_length_m"])
    A_foot = float(parent["foot_area_m2"])
    q_bear = float(parent["ground_bearing_kPa"]) * 1000.0
    toe = float(parent["forefoot_lever_m"])
    heel_frac = float(parent["heel_lever_frac"])
    tau = float(parent["ankle_torque_Nm"])
    hours = float(parent["excursion_hours"])

    # ── 1. THE LOAD, AND ITS SHAPE ──────────────────────────────────────────────────────────────
    cargo = cargo_frac * W_bare
    volume = cargo / max(rho, 1e-9)
    pk = pack_geometry(h_m, volume, high)

    # ── 2. THE COMBINED BODY ────────────────────────────────────────────────────────────────────
    M_tot = M_suited + cargo
    Hc = combined_com(M_suited, H0, cargo, pk["com_height_m"])
    lean = lean_angle(M_suited, H0, cargo, pk["com_height_m"], pk["offset_m"])

    # ── 3. WHICH STABILITY EFFECT WINS ──────────────────────────────────────────────────────────
    s0 = stability(M_suited, H0, g, toe, tau)
    s1 = stability(M_tot, Hc, g, toe, tau)
    # ONE GRAVITY WHERE THE ARGUMENT CHANGES SIDES. The toe lever is fixed by the foot; the lever the
    # ankle's walking torque can hold is tau/(M g), which grows as gravity falls. They are equal at
    # g = tau/(M toe). Below that the push-off torque alone already covers the whole base of support
    # -- balance is pure geometry and strength is free. Above it, holding the limit costs more than
    # taking a step does. This body, loaded, sits ABOVE it: strength is in the argument here, and on
    # the Moon it would not be. That is why lunar falls were a balance problem, not a strength one.
    g_cross = tau / max(M_tot * toe, 1e-12)

    # ── 4. WHAT IT COSTS ────────────────────────────────────────────────────────────────────────
    L_now = suit + cargo
    P = pandolf(W_bare, L_now, v, grade, eta, g)
    P_suit = pandolf(W_bare, suit, v, grade, eta, g)          # the suit alone: the standing start
    P_bare = pandolf(W_bare, 0.0, v, grade, eta, g)           # nothing at all: the reference
    P_grade10 = pandolf(W_bare, L_now, v, 10.0, eta, g)
    ceiling_W, sus_frac, sus_W = sustainable_power(W_bare, vo2, hours)

    # ── 5. THE KNEE ─────────────────────────────────────────────────────────────────────────────
    f_knee = knee_fraction(g)
    f_knee_earth = knee_fraction(G_EARTH)
    f_knee_moon = knee_fraction(G_MOON)
    knee_cargo = f_knee * W_bare - suit

    # the load that reaches the sustainable ceiling, by bisection on the same equation
    def _cargo_at_power(target_W):
        lo, hi = 0.0, 10.0
        while pandolf(W_bare, suit + hi, v, grade, eta, g)["total_W"] < target_W and hi < 1e5:
            hi *= 2.0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if pandolf(W_bare, suit + mid, v, grade, eta, g)["total_W"] < target_W:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    sus_cargo = _cargo_at_power(sus_W)

    # ── 6. WHAT THE GROUND SAYS ─────────────────────────────────────────────────────────────────
    p_foot = M_tot * g / A_foot
    # A CARGO CAPACITY IS A MASS AND A MASS CANNOT BE NEGATIVE, and the day theGround stopped
    # typing its cohesion this line started publishing -40.90 kg. The arithmetic was never wrong:
    # it is a HEADROOM, and a headroom is signed. Under the true (weaker) soil the suited body
    # alone already exceeds the allowable bearing pressure, so the cargo it may add before the
    # ground prints is ZERO and the interesting fact is by how much it is already over.
    #
    #     THE MISFOLD WAS THE NAME, NOT THE NUMBER -- a signed headroom docking at an interface
    #     whose unit forbids a negative. `story/folding.py audit` caught it the moment the ground
    #     became honest, which is what that audit is for.
    sink_head = q_bear * A_foot / g - M_suited                          # ultimate: it punches in
    settle_head = (q_bear / BEARING_SAFETY_FACTOR) * A_foot / g - M_suited   # allowable: it prints
    sink_cargo, settle_cargo = max(0.0, sink_head), max(0.0, settle_head)
    sink_over_kg, settle_over_kg = max(0.0, -sink_head), max(0.0, -settle_head)
    z_step = sinkage_per_step(eta, v, g, cadence)
    z_sand = sinkage_per_step(TERRAIN["loose sand"], v, g, cadence)

    # ── 7. GRAVITY IS A DIAL ────────────────────────────────────────────────────────────────────
    # Froude similarity carries the SPEED between worlds: same leg, v scales as sqrt(g). Nothing
    # else about the body changes, which is exactly the point of a dial.
    def _world(gw):
        vw = v * math.sqrt(gw / g)
        cw = cadence * math.sqrt(gw / g)
        Pw = pandolf(W_bare, L_now, vw, grade, eta, gw)
        sw = stability(M_tot, Hc, gw, toe, tau)
        return [round(gw, 4), round(knee_fraction(gw), 4), round(vw, 4), round(Pw["total_W"], 2),
                round(sw["shove_limit_ms"], 4), round(sw["ankle_demand_ratio"], 4),
                round(M_tot * gw / A_foot / 1000.0, 3),
                round(sinkage_per_step(eta, vw, gw, cw), 5)]

    ladder_g = [_world(gw) for gw in (G_MOON, 3.71, g, G_EARTH)]         # Moon, Mars, here, Earth

    # THE SAME BODY AND THE SAME PACK, PUT ON EARTH. Nothing about the person changes -- only g, and
    # the speed that Froude similarity carries with it. Every difference below is gravity's alone.
    v_e = v * math.sqrt(G_EARTH / g)
    P_e = pandolf(W_bare, L_now, v_e, grade, eta, G_EARTH)
    s_e = stability(M_tot, Hc, G_EARTH, toe, tau)

    def _cargo_at_power_on(target_W, gw, vw):
        lo, hi = 0.0, 10.0
        while pandolf(W_bare, suit + hi, vw, grade, eta, gw)["total_W"] < target_W and hi < 1e5:
            hi *= 2.0
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if pandolf(W_bare, suit + mid, vw, grade, eta, gw)["total_W"] < target_W:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    # ── 8. THE LOAD LADDER, the table the story prints ──────────────────────────────────────────
    ladder = []
    for fr in (0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60):
        c_kg = fr * W_bare
        Lk = suit + c_kg
        Pk = pandolf(W_bare, Lk, v, grade, eta, g)
        vol = c_kg / max(rho, 1e-9)
        pg = pack_geometry(h_m, vol, high)
        Hk = combined_com(M_suited, H0, c_kg, pg["com_height_m"])
        lk = lean_angle(M_suited, H0, c_kg, pg["com_height_m"], pg["offset_m"])
        sk = stability(M_suited + c_kg, Hk, g, toe, tau)
        per_kg = (Pk["total_W"] - P_bare["total_W"]) / max(Lk, 1e-9)
        ladder.append([round(fr, 3), round(c_kg, 2), round(Lk / W_bare, 4), round(Pk["total_W"], 1),
                       round(per_kg, 4), round(Hk, 5), round(math.degrees(lk), 3),
                       round(sk["shove_limit_ms"], 4), round(sk["ankle_demand_ratio"], 4),
                       round((M_suited + c_kg) * g / A_foot / 1000.0, 3)])

    # ── 9. THE CHECK THAT IS NOT OURS: APOLLO ───────────────────────────────────────────────────
    # A suited crewman on the Moon, run through the same four terms, with the gravity scaling on and
    # then off. The measured answer is in a 1975 NASA technical note; Pandolf was published in 1977
    # and was never fitted to any of it.
    ap_meas_W = APOLLO_MEAN_KJ_HR * 1000.0 / 3600.0
    ap_lo_meas_W = APOLLO_LO_KJ_HR * 1000.0 / 3600.0
    ap_hi_meas_W = APOLLO_HI_KJ_HR * 1000.0 / 3600.0
    ap_scaled_lo = pandolf(APOLLO_BODY_KG, APOLLO_EMU_KG, APOLLO_SPEED_MS, 0.0,
                           TERRAIN["heavy brush"], G_MOON)["total_W"]
    ap_scaled_hi = pandolf(APOLLO_BODY_KG, APOLLO_EMU_KG, APOLLO_SPEED_MS, 0.0,
                           TERRAIN["swampy bog"], G_MOON)["total_W"]
    ap_unscaled = pandolf(APOLLO_BODY_KG, APOLLO_EMU_KG, APOLLO_SPEED_MS, 0.0,
                          TERRAIN["heavy brush"], G_EARTH)["total_W"]

    # ── 10. THE MOVIE'S CLOCK ───────────────────────────────────────────────────────────────────
    # The hopper fills at a constant rate and is full at the end of the excursion -- which is what
    # an excursion IS, the interval the consumables buy. So the thresholds above are crossed at
    # times this chapter can name, and `inf` where the load never reaches them.
    dur = hours * 3600.0
    fill_kg_h = cargo / max(hours, 1e-9)

    def _cross_h(limit_kg):
        """When the filling hopper reaches a limit, at the excursion's own fill rate. Reported even
        past the end of the excursion -- a finite number that says 'not today, and by how far' is
        more useful than an infinity, and infinity is not JSON this tree has anywhere else."""
        return float(limit_kg) / fill_kg_h if fill_kg_h > 1e-9 else 0.0

    return {
        # ── ITS SIZE. The drawn subject is a standing body, the ground under it and the pack on it,
        # and its height is the body's height -- because A LOADED BODY IS THE SAME SIZE AS A BODY.
        # That is not a shrug, it is the chapter's premise: 25 kg of ore changes nothing you can see
        # in a silhouette and everything about what the silhouette can do.
        "extent_m": h_m,
        # ── ITS DURATION: ONE EXCURSION. Every other clock on this body is a stride or a stance,
        # and a load does not act on either -- it acts on the hours. The cost is a rate, the ceiling
        # is a rate, and neither becomes a LIMIT until you multiply by how long you must carry it.
        # theHuman sized its consumables for eight hours, so eight hours is the interval this
        # membrane lives in and the interval the hopper fills over.
        "duration_s": dur,
        "excursion_hours": hours,

        # ── the load ────────────────────────────────────────────────────────────────────────────
        "cargo_mass_kg": cargo,
        "cargo_fraction": cargo_frac,
        "cargo_density_kg_m3": rho,
        "cargo_volume_m3": volume,
        "carried_total_kg": L_now,
        "carried_fraction": L_now / W_bare,
        "suit_mass_kg": suit,
        "suit_fraction": suit / W_bare,
        "loaded_mass_kg": M_tot,
        "load_over_bare_ratio": M_tot / W_bare,

        # ── the pack ────────────────────────────────────────────────────────────────────────────
        "pack_width_m": pk["width_m"],
        "pack_span_m": pk["span_m"],
        "pack_depth_m": pk["depth_m"],
        "pack_base_m": pk["base_m"],
        "pack_com_height_m": pk["com_height_m"],
        "pack_offset_m": pk["offset_m"],
        "pack_high_frac": high,

        # ── the combined body ───────────────────────────────────────────────────────────────────
        "com_height_m": Hc,
        "com_height_unloaded_m": H0,
        "com_rise_m": Hc - H0,
        "com_rise_ratio": Hc / H0,
        "lean_rad": lean,
        "lean_deg": math.degrees(lean),
        "com_height_leaning_m": Hc * math.cos(lean),

        # ── balance: three numbers, and they do not agree about what is wrong ────────────────────
        "fall_rate_rad_s": s1["fall_rate_rad_s"],
        "fall_rate_unloaded_rad_s": s0["fall_rate_rad_s"],
        "topple_time_s": s1["topple_time_s"],
        "topple_time_unloaded_s": s0["topple_time_s"],
        "topple_time_ratio": s1["topple_time_s"] / s0["topple_time_s"],
        "lean_limit_rad": s1["lean_limit_rad"],
        "lean_limit_deg": math.degrees(s1["lean_limit_rad"]),
        "lean_limit_unloaded_deg": math.degrees(s0["lean_limit_rad"]),
        # NOT `lean_limit_ratio`. THE AUDIT CAUGHT THAT, and it was right: a `ratio` is
        # dimensionless and so are `rad` and `deg`, so `lean_limit_ratio` shared a stem with
        # `lean_limit_rad` and folding.py read the three as one quantity in three units and found
        # them 82.8% apart. They are not one quantity -- two are an angle and one is the quotient of
        # two angles -- and the fix is the NAME, because the name is what a machine reads.
        "lean_limit_over_unloaded_ratio": s1["lean_limit_rad"] / s0["lean_limit_rad"],
        "shove_limit_ms": s1["shove_limit_ms"],
        "shove_limit_unloaded_ms": s0["shove_limit_ms"],
        "shove_limit_over_unloaded_ratio": s1["shove_limit_ms"] / s0["shove_limit_ms"],
        "ankle_demand_ratio": s1["ankle_demand_ratio"],
        "ankle_demand_unloaded_ratio": s0["ankle_demand_ratio"],
        "ankle_demand_growth_ratio": s1["ankle_demand_ratio"] / s0["ankle_demand_ratio"],
        # AND THE ANSWER. Geometry loses this argument by a factor of five.
        "geometry_cost_ratio": 1.0 - s1["lean_limit_rad"] / s0["lean_limit_rad"],
        "mass_cost_ratio": s1["ankle_demand_ratio"] / s0["ankle_demand_ratio"] - 1.0,
        "mass_beats_geometry_by_ratio": (s1["ankle_demand_ratio"] / s0["ankle_demand_ratio"] - 1.0)
                                        / max(1.0 - s1["lean_limit_rad"] / s0["lean_limit_rad"], 1e-9),
        # the extra time and the extra distance are the SAME factor -- so the slow topple is free
        "capture_step_m": v / s1["fall_rate_rad_s"],
        "capture_step_unloaded_m": v / s0["fall_rate_rad_s"],
        "step_length_m": step_len,
        "catch_in_one_step": bool(v / s1["fall_rate_rad_s"] <= step_len),
        "toe_lever_m": toe,
        "heel_lever_m": heel_frac * h_m,
        "g_where_ankle_demand_is_one_m_s2": g_cross,
        "ankle_has_reserve_at_the_toe": bool(g < g_cross),

        # ── the cost ────────────────────────────────────────────────────────────────────────────
        "metabolic_W": P["total_W"],
        "metabolic_suit_only_W": P_suit["total_W"],
        "metabolic_bare_W": P_bare["total_W"],
        "rest_W": P["rest_W"],
        "load_penalty_W": P["load_W"],
        "walking_W": P["speed_W"],
        "climbing_W": P["grade_W"],
        "grade_10pct_metabolic_W": P_grade10["total_W"],
        "climb_10pct_is_sustainable": bool(P_grade10["total_W"] <= sus_W),
        "cost_over_bare_ratio": P["total_W"] / max(P_bare["total_W"], 1e-9),
        "next_10kg_costs_W": pandolf(W_bare, L_now + 10.0, v, grade, eta, g)["total_W"] - P["total_W"],
        "terrain_factor": eta,
        "grade_pct": grade,
        "speed_ms": v,

        # ── endurance ───────────────────────────────────────────────────────────────────────────
        "aerobic_ceiling_W": ceiling_W,
        "sustainable_frac": sus_frac,
        "sustainable_power_W": sus_W,
        "sustainable_cargo_kg": sus_cargo,
        "effort_of_ceiling_frac": min(P["total_W"] / max(sus_W, 1e-9), 1.0),
        "within_sustainable": bool(P["total_W"] <= sus_W),
        "excursion_energy_J": P["total_W"] * dur,

        # ── the knee, and it is the headline ────────────────────────────────────────────────────
        "knee_fraction": f_knee,
        "knee_cargo_kg": knee_cargo,
        # `knee_earth_fraction`, NOT `knee_fraction_earth`. The suffix is what declares the unit, so
        # the world's name goes in the middle -- the same rule that lets folding.py read 86% of this
        # story without a table. Named the other way round, both were invisible to every check.
        "knee_earth_fraction": f_knee_earth,
        "knee_moon_fraction": f_knee_moon,
        "knee_in_classic_band": bool(0.20 <= f_knee_earth <= 0.30),
        "suit_share_of_knee_frac": min(suit / max(f_knee * W_bare, 1e-9), 1.0),
        "over_the_knee": bool(L_now / W_bare > f_knee),
        "grade_efficiency_frac": grade_efficiency(),
        "grade_efficiency_in_literature_band": bool(0.25 <= grade_efficiency() <= 0.30),

        # ── the ground ──────────────────────────────────────────────────────────────────────────
        "foot_pressure_kPa": p_foot / 1000.0,
        "foot_pressure_unloaded_kPa": M_suited * g / A_foot / 1000.0,
        "ground_bearing_kPa": q_bear / 1000.0,
        "ground_margin_ratio": q_bear / max(p_foot, 1e-9),
        "sink_cargo_kg": sink_cargo,
        "settle_cargo_kg": settle_cargo,
        # AND THE OTHER SIDE OF ZERO, said as its own fact rather than as a negative mass.
        "settle_exceeded_unloaded": settle_over_kg > 0.0,
        "settle_over_by_kg": settle_over_kg,
        "sink_exceeded_unloaded": sink_over_kg > 0.0,
        "sink_over_by_kg": sink_over_kg,
        "ground_bites": bool(settle_cargo <= sus_cargo),
        "sink_per_step_m": z_step,
        "sink_loose_sand_m": z_sand,
        "foot_area_m2": A_foot,

        # ── the gravity dial ────────────────────────────────────────────────────────────────────
        # THE SAME LOAD ON EARTH. One number moved -- g -- and the whole page moves with it.
        "earth_metabolic_W": P_e["total_W"],
        "earth_speed_ms": v_e,
        "earth_knee_cargo_kg": f_knee_earth * W_bare - suit,
        "earth_sustainable_cargo_kg": _cargo_at_power_on(sus_W, G_EARTH, v_e),
        "earth_shove_limit_ms": s_e["shove_limit_ms"],
        "earth_ankle_demand_ratio": s_e["ankle_demand_ratio"],
        "earth_foot_pressure_kPa": M_tot * G_EARTH / A_foot / 1000.0,
        "earth_within_sustainable": bool(P_e["total_W"] <= sus_W),
        "earth_cost_ratio": P_e["total_W"] / max(P["total_W"], 1e-9),
        "gravity_ladder": ladder_g,
        "gravity_ladder_row": "g_m_s2, knee_fraction, speed_ms, metabolic_W, shove_limit_ms, "
                              "ankle_demand_ratio, foot_pressure_kPa, sink_per_step_m",
        "load_ladder": ladder,
        "load_ladder_row": "cargo_fraction, cargo_kg, carried_fraction, metabolic_W, "
                           "cost_per_kg_carried_W, com_height_m, lean_deg, shove_limit_ms, "
                           "ankle_demand_ratio, foot_pressure_kPa",

        # ── the Apollo comparison ───────────────────────────────────────────────────────────────
        "apollo_measured_W": ap_meas_W,
        "apollo_measured_lo_W": ap_lo_meas_W,
        "apollo_measured_hi_W": ap_hi_meas_W,
        "apollo_predicted_lo_W": ap_scaled_lo,
        "apollo_predicted_hi_W": ap_scaled_hi,
        "apollo_unscaled_W": ap_unscaled,
        "apollo_load_ratio": APOLLO_EMU_KG / APOLLO_BODY_KG,
        "apollo_brackets_measured": bool(ap_scaled_lo <= ap_meas_W <= ap_scaled_hi),
        "apollo_unscaled_error_ratio": ap_unscaled / ap_meas_W,

        # ── when each limit is crossed, at the excursion's own fill rate ────────────────────────
        # FOUR LIMITS, AND THE ORDER IS THE STORY. The economics go first and the ground goes last,
        # and the two in the middle -- what your lungs can hold for eight hours, and what the soil
        # will take a print at -- arrive within a kilogram of each other by pure coincidence.
        "knee_crossed_h": _cross_h(knee_cargo),
        "sustainable_crossed_h": _cross_h(sus_cargo),
        "settle_crossed_h": _cross_h(settle_cargo),
        "sink_crossed_h": _cross_h(sink_cargo),
        "knee_crossed_in_excursion": bool(0.0 <= knee_cargo <= cargo),
        "sustainable_crossed_in_excursion": bool(0.0 <= sus_cargo <= cargo),
        "settle_crossed_in_excursion": bool(0.0 <= settle_cargo <= cargo),
        "first_limit": min((("economy", knee_cargo), ("lungs", sus_cargo),
                            ("ground", settle_cargo)), key=lambda kv: kv[1])[0],

        # ── carried on, so the picture and any child need read nothing else ─────────────────────
        # theHuman's `cadence_steps_s` is used above and deliberately NOT republished: the key's own
        # suffix reads as SECONDS and the quantity is steps per second, so re-emitting it would be
        # spreading a bad bond one membrane further. Anything below that needs a cadence should take
        # it from theHuman, where it already is.
        "height_m": h_m,
        "suited_mass_kg": M_suited,
        "bare_mass_kg": W_bare,
        "g": g,
        "S_earth": float(parent.get("S_earth", 1.0)),
        "ankle_torque_Nm": tau,
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- one excursion: a hopper filling, and a body changing under it
# ════════════════════════════════════════════════════════════════════════════════════════════════
def emit(nums, t=1.0):
    """EIGHT HOURS, and the hopper fills the whole time.

    LOCAL UNITS: 1.0 is the person's standing height. +X is the walking direction, so the pack is
    behind at -X and the toe is ahead at +X.

    WHAT MOVES, and every one of these is re-run from the published numbers at this instant rather
    than interpolated between two drawn states:

      * THE HOPPER FILLS from its floor upward. Its shell is the derived pack -- shoulder-wide, hip
        belt to shoulders, and as deep as this cargo's density forces it to be.
      * THE COMBINED CENTRE OF MASS CLIMBS, because the contents' own centroid climbs as they pile
        up. Its trail is left behind it, so the rise is drawn by the thing doing it.
      * THE BODY LEANS FORWARD to put that centre of mass back over the ankle. The lean is
        `atan(m x / (M H + m h))`, computed here, at this fill, not read from a keyframe.
      * THE LEAN LIMIT NARROWS. The two pale lines from the ankle are atan(toe/H) and its mirror --
        the angle past which the centre of pressure would leave the foot. They close as the CoM
        rises, and the gap between the lean and the limit IS the margin.
      * THE COST COLUMN RISES against a tick at the sustainable ceiling. When the column passes the
        tick, the excursion is no longer something this body can finish.

    WHAT IS DELIBERATELY NOT DRAWN: flesh, a face, gear, a horizon. The same rule as the parent --
    the segment heights and breadths are measured and the load physics is derived, so those are
    drawn; nothing else is known, so nothing else appears."""
    from matter import blank, lit, SOLID, GLOW, AR, AB

    u = min(max(float(t), 0.0), 1.0)

    H_m = float(nums["height_m"])                 # metres per local unit
    M0 = float(nums["suited_mass_kg"])
    H0 = float(nums["com_height_unloaded_m"])      # the BARE body's, so the rise is drawn, not assumed
    g = float(nums["g"])
    toe = float(nums["toe_lever_m"])
    heel = float(nums["heel_lever_m"])
    cargo_full = float(nums["cargo_mass_kg"])
    span = float(nums["pack_span_m"])
    depth = float(nums["pack_depth_m"])
    base = float(nums["pack_base_m"])
    standoff = 0.5 * CHESTDEPTH_FRAC * H_m

    # ── THE LAW, RE-RUN AT THIS INSTANT ─────────────────────────────────────────────────────────
    # A hopper fills from the bottom, so at fill u the contents occupy the bottom u of the shell and
    # their centroid is at base + u*span/2. Mass is u of the full cargo. Everything else follows.
    m_now = cargo_full * u
    h_now = base + 0.5 * span * max(u, 1e-6)
    x_now = standoff + 0.5 * depth
    Hc = combined_com(M0, H0, m_now, h_now)
    lean = lean_angle(M0, H0, m_now, h_now, x_now)
    lim = math.atan(toe / max(Hc, 1e-9))

    S = 1.0 / H_m                                  # metres -> local units
    c, s = math.cos(lean), math.sin(lean)

    def rot(x, z):
        """Lean the rigid assembly forward about the ankle at the origin."""
        return x * c + z * s, -x * s + z * c

    P, kind = [], []

    def add(pts, k):
        if len(pts):
            P.append(np.asarray(pts, dtype=np.float64))
            kind.append(np.full(len(pts), k, dtype=np.float64))

    def slab(x0, x1, z0, z1, n, leaned=True):
        """A filled rectangle in the body frame, as a jittered point grid (blue noise, not a lattice
        -- a regular grid reads as a rendering artifact at any zoom)."""
        rng = np.random.default_rng(int(1000 * abs(x0 - z0) + 17) & 0xFFFF)
        q = np.sqrt(max((x1 - x0) * (z1 - z0), 1e-12))
        nx = max(int(round(math.sqrt(n) * (x1 - x0) / q)), 2)
        nz = max(int(round(math.sqrt(n) * (z1 - z0) / q)), 2)
        gx, gz = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(z0, z1, nz))
        gx = gx.ravel() + rng.normal(0.0, (x1 - x0) / max(nx, 1) * 0.35, gx.size)
        gz = gz.ravel() + rng.normal(0.0, (z1 - z0) / max(nz, 1) * 0.35, gz.size)
        if leaned:
            rx, rz = rot(gx, gz)
        else:
            rx, rz = gx, gz
        return np.stack([rx, np.zeros(rx.size), rz], 1)

    # ── THE GROUND, and the base of support on it ───────────────────────────────────────────────
    gx = np.linspace(-0.62, 0.46, 240)
    add(np.stack([gx, np.zeros(240), np.zeros(240)], 1), 0)
    bx = np.linspace(-heel * S, toe * S, 90)
    add(np.stack([bx, np.zeros(90), np.full(90, 0.006)], 1), 1)

    # ── THE BODY, leaning. Bands are ANSUR medians of this same person: legs to the iliac crest,
    #    torso to the shoulders, head above. Widths are the torso's own measured depth.
    half = 0.5 * CHESTDEPTH_FRAC
    add(slab(-0.030, 0.030, 0.0, ILIOCRISTALE_FRAC, 900), 2)                       # legs
    add(slab(-half, half, ILIOCRISTALE_FRAC, ACROMION_FRAC, 900), 2)               # torso
    add(slab(-0.022, 0.022, ACROMION_FRAC, 0.885, 120), 2)                         # neck
    add(slab(-0.055, 0.055, 0.885, 1.0, 320), 2)                                   # head

    # ── THE HOPPER: a shell that does not change, and contents that do ──────────────────────────
    px1, px0 = -standoff * S, -(standoff + depth) * S
    pz0, pz1 = base * S, (base + span) * S
    # the shell, as four thin edges -- an outline, because an empty hopper is not matter
    for (a0, a1, b0, b1) in ((px0, px1, pz0, pz0 + 0.004), (px0, px1, pz1 - 0.004, pz1),
                             (px0, px0 + 0.004, pz0, pz1), (px1 - 0.004, px1, pz0, pz1)):
        add(slab(a0, a1, b0, b1, 120), 3)
    if u > 1e-3:
        add(slab(px0 + 0.004, px1 - 0.004, pz0 + 0.004, pz0 + (pz1 - pz0) * u, int(700 * u) + 40), 4)

    # ── THE LEAN LIMIT: the two angles past which the centre of pressure leaves the foot. They
    #    close on the body as the load rises, and the gap to the leaned trunk IS the margin.
    r = np.linspace(0.0, Hc * S * 1.02, 130)
    for sgn in (+1.0, -1.0):
        a = sgn * lim
        add(np.stack([r * math.sin(a), np.zeros(130), r * math.cos(a)], 1), 5)

    # ── THE COMBINED CENTRE OF MASS, and the trail of where it has been ─────────────────────────
    cx, cz = rot(0.0, Hc * S)
    add(np.array([[cx, 0.0, cz]]), 6)
    if u > 0.02:
        us = np.linspace(0.0, u, 44)
        pts = []
        for uu in us:
            mm = cargo_full * uu
            hh = base + 0.5 * span * max(uu, 1e-6)
            HH = combined_com(M0, H0, mm, hh)
            ll = lean_angle(M0, H0, mm, hh, x_now)
            pts.append([HH * S * math.sin(ll), 0.0, HH * S * math.cos(ll)])
        add(np.asarray(pts), 7)

    # ── THE COST COLUMN, beside the body, with a tick at the sustainable ceiling ────────────────
    # The height of the column is the metabolic rate; the tick is what this body can hold for the
    # eight hours the movie runs. They are the two numbers that decide whether you get home.
    sus = float(nums["sustainable_power_W"])
    P_now = pandolf(float(nums["bare_mass_kg"]), float(nums["suit_mass_kg"]) + m_now,
                    float(nums["speed_ms"]), float(nums["grade_pct"]),
                    float(nums["terrain_factor"]), g)["total_W"]
    col_x, col_scale = 0.40, 0.85 / max(sus * 1.35, 1e-9)
    add(slab(col_x, col_x + 0.030, 0.0, max(P_now * col_scale, 0.004), 240, leaned=False), 8)
    tick = np.linspace(col_x - 0.018, col_x + 0.048, 40)
    add(np.stack([tick, np.zeros(40), np.full(40, sus * col_scale)], 1), 9)

    Pp = np.concatenate(P, 0)
    kk = np.concatenate(kind, 0)
    n = len(Pp)
    b = blank(n)
    b[:, 0:3] = Pp
    nrm = np.zeros((n, 3), np.float32)
    nrm[:, 1] = -1.0                                # the scene is a side elevation: face the camera
    b[:, 21:24] = nrm

    # COLOURS ARE MATERIAL, not decoration: ground and body are the parent's own palette, the cargo
    # is basalt, and the three things that are MEASUREMENTS rather than matter -- the support base,
    # the limit lines, the centre of mass -- are the only lit marks in the frame.
    alb = np.zeros((n, 3), np.float32)
    alb[kk == 0] = (0.20, 0.22, 0.24)      # the ground
    alb[kk == 1] = (0.55, 0.62, 0.80)      # the base of support
    alb[kk == 2] = (0.42, 0.36, 0.31)      # the body
    alb[kk == 3] = (0.30, 0.31, 0.34)      # the hopper shell
    alb[kk == 4] = (0.34, 0.29, 0.24)      # broken basalt
    alb[kk == 5] = (0.32, 0.42, 0.44)      # the lean limit
    alb[kk == 6] = (1.00, 0.72, 0.25)      # the combined centre of mass, NOW
    alb[kk == 7] = (0.70, 0.55, 0.30)      # ... and where it has been
    alb[kk == 8] = (0.86, 0.42, 0.30)      # what it is costing
    alb[kk == 9] = (0.40, 0.78, 0.55)      # what it can afford

    S_e = float(nums.get("S_earth", 1.0))
    b[:, 16:19] = lit(alb, S_e * 0.85 + 0.15, e_ref=S_e, tone=0.45)
    b[:, AR:AB + 1] = alb
    b[:, 19] = np.where((kk == 7) | (kk == 5), 0.5, 0.96)
    b[:, 20] = np.where(kk == 6, 0.030, np.where(kk == 0, 0.010, 0.0085))
    b[:, 11] = np.where(kk == 6, GLOW, SOLID)
    return b


def measure(nums):
    """Facts a reader can check without trusting a word of the prose above."""
    n = nums
    return {
        # ── THE CHECKS THIS CHAPTER WAS NOT FITTED TO ───────────────────────────────────────────
        # 1. Pandolf's grade coefficient contains a muscular efficiency nobody put in it.
        "grade_efficiency_frac": n["grade_efficiency_frac"],
        "grade_efficiency_in_literature_band": n["grade_efficiency_in_literature_band"],
        # 2. The knee, from Pandolf's own 1.5 and 2.0, lands inside the 20-30% band the porter and
        #    soldier literature reports -- and it MOVES with gravity, which nobody has measured.
        "knee_earth_fraction": n["knee_earth_fraction"],
        "knee_in_classic_band": n["knee_in_classic_band"],
        "knee_fraction": n["knee_fraction"],
        "knee_moon_fraction": n["knee_moon_fraction"],
        "knee_rises_as_gravity_falls": bool(
            n["knee_moon_fraction"] > n["knee_fraction"] > n["knee_earth_fraction"]),
        # 3. Apollo. 158.76 measured hours, a 1975 report, a 1977 equation, and a gravity scaling
        #    derived here. With the scaling it brackets; without it, it is wrong by a factor.
        "apollo_measured_W": n["apollo_measured_W"],
        "apollo_predicted_lo_W": n["apollo_predicted_lo_W"],
        "apollo_predicted_hi_W": n["apollo_predicted_hi_W"],
        "apollo_brackets_measured": n["apollo_brackets_measured"],
        "apollo_unscaled_error_ratio": n["apollo_unscaled_error_ratio"],
        "gravity_scaling_is_load_bearing": bool(n["apollo_unscaled_error_ratio"] > 2.0
                                                and n["apollo_brackets_measured"]),
        # 4. The terrain factor, asked to say a depth, says one a boot actually makes.
        "sink_loose_sand_m": n["sink_loose_sand_m"],
        "sink_is_ankle_deep": bool(0.05 <= n["sink_loose_sand_m"] <= 0.25),

        # ── WHICH STABILITY EFFECT WINS ─────────────────────────────────────────────────────────
        "geometry_cost_ratio": n["geometry_cost_ratio"],
        "mass_cost_ratio": n["mass_cost_ratio"],
        "mass_beats_geometry_by_ratio": n["mass_beats_geometry_by_ratio"],
        "topple_time_ratio": n["topple_time_ratio"],
        # the slow topple is exactly cancelled by the longer capture step: the same 1/w0 in both
        "slow_topple_buys_nothing": bool(abs(n["topple_time_ratio"]
                                             - n["capture_step_m"] / n["capture_step_unloaded_m"]) < 1e-9),

        # ── THE GROUND'S ANSWER TO THE STUB'S OWN QUESTION ──────────────────────────────────────
        "ground_margin_ratio": n["ground_margin_ratio"],
        "sink_cargo_kg": n["sink_cargo_kg"],
        "settle_cargo_kg": n["settle_cargo_kg"],
        "ground_bites": n["ground_bites"],

        # ── AND WHAT IT MEANS FOR THIS BODY ─────────────────────────────────────────────────────
        "knee_cargo_kg": n["knee_cargo_kg"],
        "suit_share_of_knee_frac": n["suit_share_of_knee_frac"],
        "sustainable_cargo_kg": n["sustainable_cargo_kg"],
        "first_limit": n["first_limit"],
        "metabolic_W": n["metabolic_W"],
        "climb_10pct_is_sustainable": n["climb_10pct_is_sustainable"],
        "effort_of_ceiling_frac": n["effort_of_ceiling_frac"],
        "lean_deg": n["lean_deg"],
        "com_rise_m": n["com_rise_m"],
        # its clock is the excursion, and an excursion is a real interval a person plans around
        "duration_s": n["duration_s"],
        "duration_is_the_excursion": bool(abs(n["duration_s"] - n["excursion_hours"] * 3600.0) < 1e-6),
    }
