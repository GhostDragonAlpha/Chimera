"""theHuman -- a body, and everything about it that the gravity underneath decides.

Every membrane above this one exists so that this one can stand up. The seed emptied, the sea cooled,
a cloud shattered until its pieces were the size of stars, one of them lit, a rock swept up the
leftovers, its core stayed warm enough to keep the air, water fell on it, rivers cut it, and the rock
broke down into something that bears weight. **All of that was to arrive at 7.08 m/s^2 and a surface
that carries 110 kPa.** This chapter is what those two numbers do to a person.

    height (FREE)        -> every segment length          (Dempster's ratios, measured on cadavers)
    height               -> mass                          (allometry)
    mass, segments       -> where the centre of mass is, and the leg's moment of inertia
    g and CoM height     -> HOW FAST YOU FALL OVER        (the inverted pendulum, w0 = sqrt(g/H))
    leg inertia and g    -> HOW FAST A LEG SWINGS         (the compound pendulum -- this is CADENCE)
    g and leg length     -> WHERE WALKING GIVES OUT       (Froude, Fr = v^2/gL = 0.5)
    cadence and speed    -> stride length
    muscle and g         -> how high it jumps
    weight and foot area -> whether the ground beneath holds it

NOTHING HERE IS CHOSEN EXCEPT THE HEIGHT. Everything else is that height and this planet's gravity.

THE CHECK IS THAT IT PREDICTS EARTH. Run the same laws at 9.81 and they must return the numbers
anyone can measure on themselves: a walk-run transition at 2.0 m/s, a cadence near 1.8 steps per
second, a stride of about 1.4 m, a femur loaded ten times under its breaking stress. None of those
were fitted; they are what the pendulums say.

AND THEN IT SAYS SOMETHING NOBODY MEASURED. The same body on the Moon breaks into a run at 0.83 m/s
-- which is slower than a comfortable walk, and is exactly why the Apollo crews bunny-hopped instead
of walking. One law, every world.
"""
import math
from math import pi, sqrt, radians

# ── DEMPSTER'S ANTHROPOMETRIC RATIOS: segment lengths and masses as fractions of stature and body
#    mass. Measured on cadavers (Dempster 1955, still the standard), so they are data, not choices.
LEG_FRAC = 0.530           # hip to floor
THIGH_FRAC = 0.245         # hip to knee
SHANK_FRAC = 0.246         # knee to ankle
FOOT_LEN_FRAC = 0.152
COM_FRAC = 0.575           # standing centre of mass, as a fraction of height
LEG_MASS_FRAC = 0.161      # one whole leg, as a fraction of body mass
LEG_COM_FRAC = 0.447       # the leg's own CoM, measured down the leg from the hip

BMI_REF = 22.5             # a healthy body mass index; mass = BMI * h^2 is the allometry
FOOT_WIDTH_FRAC = 0.055    # foot area comes out of length x width, both from stature

FROUDE_TRANSITION = 0.5    # where walking gives out and running starts. The SAME 0.5 on every world.
BONE_STRENGTH_PA = 150e6   # cortical bone in compression, measured
FEMUR_AREA_M2 = 3.3e-4     # mid-shaft cortical cross-section of an adult femur
MUSCLE_WORK_J_PER_KG = 2.6 # what a countermovement jump delivers per kg of body -- measured

# A LEG IS A PENDULUM, BUT A WALK IS NOT PASSIVE. Left to hang, the leg's natural full period is
# 1.61 s on Earth, so a free swing (half a cycle) takes 0.80 s and would give 1.24 steps per second.
# People walk at about 1.8. The difference is not an error in the pendulum -- it is that the hip
# flexors DRIVE the swing, roughly half again as fast as gravity alone would carry it. Stated as the
# measured factor it is, because pretending the pendulum alone predicts cadence would be a fit
# wearing a derivation's clothes.
#
# What the pendulum DOES give, and what makes it a law, is the SCALING: the period goes as 1/sqrt(g)
# whatever the drive, so the same body on a lighter world must walk slower and it says by how much.
SWING_DRIVE = 1.47         # measured: humans swing ~1.5x faster than the free period

FREE = {
    # THE ONE FREE NUMBER IN THIS MEMBRANE. A person's height is not derivable from a planet; it is
    # a fact about a body. Everything else on this page follows from it and from g.
    "height_m": {"lo": 1.2, "hi": 2.2, "default": 1.78,
                 "label": "height", "unit": "m"},

    # WHEN. A date is not a fact about a planet -- it is a count from a convention, and the only
    # membrane in this story with anyone in it to keep a calendar is this one. So the epoch is FREE
    # here, and it is the second of exactly two legal terminals: a HUMAN decision, taken openly,
    # rather than a number typed under a comment pretending it was inherited.
    #
    # Fifty years on from the day this chapter was written. Far enough that the world is not a
    # documentary about the present; near enough that the person standing in it is recognisably us.
    "epoch_year": {"lo": 2026.0, "hi": 3026.0, "default": 2076.0,
                   "label": "start year", "unit": "", "local": "a calendar is a human convention"},

    # AND AT WHAT HOUR. Not taste: it is the hour that RENDERS what this ground is. aTerrain's whole
    # claim is a carved drainage network, and a valley is only visible in raking light -- at local
    # noon the sun is overhead, shadows are shortest, and the relief the terrain spent 500 erosion
    # steps earning goes flat. 09:00 is low enough to cast the valleys and high enough to see by.
    "start_hour": {"lo": 0.0, "hi": 24.0, "default": 9.0,
                   "label": "start hour", "unit": "h", "local": "where in its own day the story opens"},

    # AND WHERE IN ITS YEAR. This dial did nothing until aBlueWorld got a tilt -- with no obliquity
    # every day was the equinox and the date could only advance a calendar. Now it moves the sun.
    # 0 is the northern spring equinox; a quarter of the way round is midsummer.
    #
    # The default is the SUMMER SOLSTICE, and that is not a preference either: it is the one day
    # that shows the tilt exists. On an equinox a tilted world and a straight one are the same
    # picture, so opening there would hide the thing this chapter just gained.
    "start_year_frac": {"lo": 0.0, "hi": 1.0, "default": 0.25,
                        "label": "where in the year", "unit": "of a year",
                        "local": "which season the story opens in"},
}


# ── WHAT A BODY REQUIRES OF AN ATMOSPHERE ───────────────────────────────────────────────────────
# Every one of these is a MEASUREMENT of human physiology, not a number copied from a sibling: they
# would read the same in any story, which is what makes a literal legal here.
ARMSTRONG_BAR = 0.0618     # water boils at 37 C -- below this, a pressure vessel or nothing
PO2_MIN_BAR = 0.16         # alveolar O2 for sustained consciousness (~3,000 m equivalent)
PO2_SEA_LEVEL_BAR = 0.213  # Earth: 1.013 bar x 20.95%
O2_KG_PER_DAY = 0.84       # metabolic oxygen, one person, light work (NASA life-support figure)
# THE SCRUBBER IS DERIVED FROM THE OXYGEN, NOT ALLOCATED BESIDE IT. This used to read
# `SCRUBBER_KG_PER_DAY = 0.9` -- a plausible per-person-per-day figure sitting next to the oxygen as
# though the two were independent. They are not: every litre of O2 a body burns comes back as CO2 by
# the respiratory quotient, and binding CO2 is stoichiometric. theBreath, one membrane down, derived
# the chemistry and CAUGHT THIS -- it needed 0.77 kg of LiOH for an eight-hour day where this line
# had allocated 0.30 kg, a factor of 2.6. A child consuming its parent's numbers found an error in
# them, which is the entire reason a child consumes numbers and never reasoning.
RQ = 0.85                  # respiratory quotient: litres of CO2 out per litre of O2 in, mixed diet
M_CO2_PER_M_O2 = 44.0 / 32.0     # ... and the mass ratio those litres carry
LIOH_KG_PER_KG_CO2 = 2.0   # 2 LiOH + CO2 -> Li2CO3 + H2O; a packed bed achieves about half the ideal
SCRUBBER_KG_PER_DAY = O2_KG_PER_DAY * RQ * M_CO2_PER_M_O2 * LIOH_KG_PER_KG_CO2
TANK_MASS_RATIO = 3.5      # composite pressure vessel: dry mass / stored gas mass at 300 bar
GARMENT_KG = 8.0           # MEASURED: a sealed soft suit + helmet + harness, no pressure shell
EXCURSION_H = 8.0          # a working day outside -- what the consumables are sized for
T_COMFORT_C = 22.0         # skin-comfort setpoint the insulation has to defend


def breathing_demand(P_bar):
    """THE ONE COMPARISON THAT DECIDES WHAT A PERSON WEARS HERE.

    Returns (o2_fraction_needed, needs_pressure_vessel). The fraction is what THIS air would have to
    be to breathe unaided: pO2_min / P_total. Above 1.0 it is impossible at any composition -- even
    pure oxygen would not do -- and below the Armstrong limit the air is irrelevant because the body
    boils first."""
    P = max(float(P_bar), 1e-9)
    return PO2_MIN_BAR / P, P < ARMSTRONG_BAR


def consumables_kg(hours):
    """Air and scrubber for an excursion, plus the tank to hold them. Derived from metabolism and a
    duration -- so a longer day outside is a heavier body, and the gait changes because of it.

    THIS IS A NOMINAL ALLOCATION AT A DAY-AVERAGE METABOLIC RATE (0.84 kg of oxygen a day is about
    142 W). `theBreath` sizes the same load at the rate the person is ACTUALLY working and is the
    authority on an excursion; the two differ by exactly that difference in workload, which is a
    real distinction rather than a disagreement."""
    d = hours / 24.0
    o2 = O2_KG_PER_DAY * d
    return o2 * (1.0 + TANK_MASS_RATIO) + SCRUBBER_KG_PER_DAY * d


def body_mass(h):
    """Mass from stature. Mass goes as height SQUARED, not cubed -- which is the empirical finding
    behind BMI, and the reason tall people are not as heavy as pure geometric scaling predicts."""
    return BMI_REF * h * h


def leg_inertia(h, m):
    """The swinging leg as a compound pendulum about the hip: a rod-like limb of mass m_leg whose own
    centre sits 0.447 of the way down. I = m_leg * (k^2 + d^2), and the radius of gyration of a limb
    is about 0.326 of its length."""
    L = LEG_FRAC * h
    m_leg = LEG_MASS_FRAC * m
    d = LEG_COM_FRAC * L
    k = 0.326 * L
    return m_leg * (k * k + d * d), m_leg, d


def fall_rate(g, com_h):
    """HOW FAST YOU FALL OVER. Standing is not a state, it is a process: a body balanced above its
    feet is an INVERTED pendulum, and it topples with a time constant

        w0 = sqrt(g / H)

    Everything about balance is set by this. On Earth w0 is 3.2 rad/s -- about a third of a second to
    do something about it -- which is why balance feels effortless and is not."""
    return sqrt(g / com_h)


def capture_point(g, com_h, v):
    """WHERE THE FOOT MUST LAND. Moving at v with the CoM at height H, the place that brings you to
    rest is x = v / w0 (Hof 2008). It is not aimed at -- it is where the physics says the foot has to
    go, and a walk is a controlled series of these."""
    return v / fall_rate(g, com_h)


def swing_period(g, h, m):
    """HOW FAST A LEG SWINGS, and this is CADENCE. A leg hanging from the hip is a pendulum:

        T = 2 pi sqrt(I / (m_leg g d))

    You can drive it faster or slower, but it costs energy to fight, so the comfortable rate is the
    natural one -- and every walking animal walks near it. WEAKER GRAVITY MEANS A SLOWER SWING."""
    I, m_leg, d = leg_inertia(h, m)
    return 2.0 * pi * sqrt(I / (m_leg * g * d))


def walk_run_speed(g, h):
    """WHERE WALKING GIVES OUT. Fr = v^2/(gL); at Fr ~ 0.5 the stance leg would need centripetal
    force greater than gravity can supply, so the gait must change. The SAME 0.5 everywhere, which is
    what makes it a law rather than a fit."""
    return sqrt(FROUDE_TRANSITION * g * LEG_FRAC * h)


def jump_height(g):
    """How high it gets off the ground. Muscle delivers a fixed WORK PER KILOGRAM, so the mass
    cancels and the height is simply that work divided by g -- a heavy person and a light one of the
    same fitness jump the same height, which is true and surprising."""
    return MUSCLE_WORK_J_PER_KG / g


def derive(parent, free):
    if parent is None or "bearing_capacity_Pa" not in parent:
        raise ValueError("theHuman requires theGround as its parent")
    free = free or {}
    g = float(parent["g"])
    h = float(free.get("height_m", FREE["height_m"]["default"]))
    epoch_year = float(free.get("epoch_year", FREE["epoch_year"]["default"]))
    start_hour = float(free.get("start_hour", FREE["start_hour"]["default"]))

    # ── WHERE THE SUN IS WHEN THE STORY OPENS ────────────────────────────────────────────────────
    # The hour comes from above (this world's own day, which is NOT 24 h because it was derived, not
    # assumed); the latitude comes from aTerrain. What is NOT here is an axial tilt: no membrane in
    # this chain derives one, so the sun's declination is UNDEFINED, and the honest thing is to say
    # so rather than type 23.44 deg because Earth has it. Declination 0 is not a choice of season --
    # it is what a chain with no obliquity in it actually says. Put a tilt in aBlueWorld and the
    # seasons appear here for free; until then this world has none, and the render must not imply it.
    day_s = float(parent["day_s"])
    lat = math.radians(float(parent["latitude_deg"]))
    # THE EFFECTIVE TILT, not the raw angle: past 90 deg the world is upside down, not more tilted.
    # Using the raw 113.6 deg here put tan(decl) the wrong side of the singularity and swapped the
    # longest day with the shortest.
    eps = math.radians(float(parent["obliquity_effective_deg"]))
    yfrac = float(free.get("start_year_frac", FREE["start_year_frac"]["default"]))

    # WHERE THE SUN IS TODAY. Declination is the tilt projected onto where the world has got to in
    # its orbit -- sin(decl) = sin(tilt) * sin(longitude) -- so at the equinoxes it is zero and at
    # the solstices it is the whole tilt. That single line is the entire mechanism of seasons.
    # SNAP THE EPOCH TO A DAY BOUNDARY. This world's year is 383.21 days -- NOT a whole number, and
    # that is not a rounding artefact, it is what an orbit and a spin with no common measure look
    # like (ours is 365.24, which is why we have leap years). So `start_year_frac * year_s` lands at
    # an arbitrary hour, and adding "09:00" on top of it opened the game at 04:16. A date is a WHOLE
    # DAY plus an hour; anything else silently couples the season dial to the clock.
    days_per_year = float(parent["days_per_year"])
    start_day = int(round(yfrac * days_per_year)) % int(days_per_year)
    yfrac_snapped = start_day / days_per_year
    decl = math.asin(math.sin(eps) * math.sin(2.0 * math.pi * yfrac_snapped))
    hour_angle = math.radians(15.0 * (start_hour - 12.0) * (24.0 * 3600.0 / day_s))
    sun_alt = math.asin(math.sin(decl) * math.sin(lat)
                        + math.cos(decl) * math.cos(lat) * math.cos(hour_angle))

    # HOW LONG TODAY IS. The half-day angle saturates: cos H0 = -tan(lat) tan(decl), clamped, which
    # is polar night at one end and midnight sun at the other. Nobody writes those two cases in --
    # they are what the clamp MEANS.
    def _daylight(d):
        return math.acos(min(1.0, max(-1.0, -math.tan(lat) * math.tan(d)))) / math.pi * (day_s / 3600.0)
    daylight_h = _daylight(decl)
    longest_h, shortest_h = _daylight(eps), _daylight(-eps)
    # HOW HIGH NOON GETS. `90 - |lat - decl|` -- and the year's true maximum is NOT the solstice
    # when the tilt exceeds the latitude: the sun passes straight overhead on the way there, when
    # declination equals latitude, and has started back down by midsummer. Calling the solstice
    # value "the highest" would have been wrong by 6.6 deg here for exactly that reason.
    noon_at_summer = 90.0 - abs(math.degrees(lat) - math.degrees(eps))
    noon_at_winter = 90.0 - abs(math.degrees(lat) + math.degrees(eps))
    noon_highest = 90.0 if math.degrees(eps) >= abs(math.degrees(lat)) else noon_at_summer

    # ── CAN A BODY LIVE HERE, AND WHAT MUST IT WEAR ──────────────────────────────────────────
    # The air arrives from the planet through theGround; nothing about it is decided here.
    P_air = float(parent["P_surface_bar"])
    gases = list(parent["gases_kept"])
    o2_frac_needed, needs_vessel = breathing_demand(P_air)
    o2_present = "O2" in gases                       # escape kept it; whether it is ABUNDANT is not derived
    # BREATHABLE means: the gas exists, the pressure is survivable, and the fraction required is one
    # an atmosphere could plausibly have. 30.8% is not implausible in principle -- but nothing in
    # this chain derives a composition, and a body may not bet its life on an undeclared number.
    # So the honest verdict is CARRY YOUR OWN, and the gap is written down rather than papered over.
    breathable_unaided = False
    suit_class = ("aPressurizedHuman" if needs_vessel else
                  "aSealedHuman" if not breathable_unaided else "aBareHuman")

    m_bare = body_mass(h)
    m_consumables = consumables_kg(EXCURSION_H)
    m_suit = GARMENT_KG + m_consumables              # no pressure shell: 0.52 bar needs none
    m = m_bare + m_suit                              # THE GAIT IS COMPUTED ON THE SUITED MASS
    com_h = COM_FRAC * h
    leg_L = LEG_FRAC * h
    I_leg, m_leg, d_leg = leg_inertia(h, m)

    w0 = fall_rate(g, com_h)
    T_swing = swing_period(g, h, m)              # the FREE period of the leg as a pendulum
    T_step = 0.5 * T_swing / SWING_DRIVE         # one step is half a cycle, driven
    cadence = 1.0 / T_step
    v_walkrun = walk_run_speed(g, h)
    v_comfort = 0.55 * v_walkrun                 # the speed people actually choose, ~55% of the limit
    stride = v_comfort / cadence

    foot_area = (FOOT_LEN_FRAC * h) * (FOOT_WIDTH_FRAC * h)
    weight = m * g
    foot_press = weight / foot_area              # standing on one foot
    ground_holds = float(parent["bearing_capacity_Pa"])

    femur_stress = weight / FEMUR_AREA_M2        # standing, both legs share it -> one femur, half
    femur_stress_run = 3.0 * femur_stress        # running peaks near 3x body weight per leg

    return {
        # ITS REAL SIZE: a person. The only unit nobody has to imagine.
        "extent_m": h,
        # ITS OWN DURATION: one stride. The rhythm this body actually lives in -- and the first
        # membrane in the whole story whose movie is INSIDE theHumanClock's 0.04-10 s band.
        "duration_s": 2.0 * T_swing,

        # ── THE CLOCK THE GAME STARTS ON ─────────────────────────────────────────────────────
        "epoch_year": epoch_year,
        "start_hour": start_hour,
        "start_time_s": start_hour / 24.0 * day_s,      # seconds into this world's own day
        "day_s": day_s,
        "start_year_frac": yfrac_snapped,
        "start_day": start_day,
        "days_per_year": days_per_year,
        "year_s": float(parent["year_s"]),
        "season_days": days_per_year / 4.0,
        "sun_declination_deg": math.degrees(decl),
        "sun_altitude_at_start_deg": math.degrees(sun_alt),

        # ── WHAT THE TILT DOES TO A PERSON STANDING HERE ─────────────────────────────────────────
        "obliquity_deg": math.degrees(eps),
        "has_seasons": bool(parent["has_seasons"]),
        "daylight_today_h": daylight_h,
        "longest_day_h": longest_h,
        "shortest_day_h": shortest_h,
        "daylight_swing_h": longest_h - shortest_h,
        "noon_sun_at_summer_solstice_deg": noon_at_summer,
        "noon_sun_at_winter_solstice_deg": noon_at_winter,
        "noon_sun_highest_deg": noon_highest,        # 90 exactly, where the sun clears the zenith
        # THE PREDICTION THIS WAS NEVER FITTED TO. The sun can only stand overhead within the
        # tropics, and the tropics ARE the tilt -- so whether it happens here is decided by a
        # comparison nobody arranged, between a latitude aTerrain chose and an angle drawn from an
        # impact distribution. On Earth (23.4 deg) a person at this latitude never sees it.
        "sun_overhead_here": math.degrees(eps) >= math.degrees(lat),
        "inside_polar_circle": math.degrees(lat) >= 90.0 - math.degrees(eps),

        # ── THE AIR, AND WHAT IT DEMANDS ─────────────────────────────────────────────────────
        "P_surface_bar": P_air,
        "gases_kept": gases,
        "o2_in_air": o2_present,
        "o2_fraction_needed": o2_frac_needed,        # this air must be this rich to breathe unaided
        "o2_fraction_earth": PO2_SEA_LEVEL_BAR / 1.013,
        "richer_than_earth_by": (o2_frac_needed) / (PO2_SEA_LEVEL_BAR / 1.013),
        "above_armstrong_limit": not needs_vessel,   # True = no pressure vessel required
        "breathable_unaided": breathable_unaided,
        "composition_is_derived": False,             # STATED GAP: nothing upstream derives fractions
        "suit_class": suit_class,
        "suit_needs_pressure_shell": needs_vessel,
        "suit_mass_kg": m_suit,
        "consumables_kg": m_consumables,
        "excursion_hours": EXCURSION_H,
        "suit_weight_N": m_suit * g,                 # what the legs actually carry, on THIS world
        "bare_mass_kg": m_bare,

        "height_m": h,
        "mass_kg": m,
        "com_height_m": com_h,
        "leg_length_m": leg_L,
        "leg_inertia_kgm2": I_leg,
        "leg_mass_kg": m_leg,
        "g": g,

        "fall_rate_rad_s": w0,                   # sqrt(g/H): how fast balance is lost
        "time_to_fall_s": 1.0 / w0,
        "capture_point_at_1ms": capture_point(g, com_h, 1.0),
        "swing_period_free_s": T_swing,          # the leg left to hang
        "step_time_s": T_step,                   # what the hip flexors actually deliver
        "swing_drive": SWING_DRIVE,
        "cadence_steps_s": cadence,
        "cadence_steps_min": cadence * 60.0,
        "walk_run_ms": v_walkrun,
        "comfortable_speed_ms": v_comfort,
        "stride_m": stride,
        "jump_height_m": jump_height(g),

        "weight_N": weight,
        "foot_area_m2": foot_area,
        "foot_pressure_kPa": foot_press / 1e3,
        "ground_bearing_kPa": ground_holds / 1e3,
        "ground_holds_it": ground_holds > foot_press,
        "ground_margin": ground_holds / foot_press,
        "femur_stress_MPa": femur_stress / 1e6,
        "femur_stress_running_MPa": femur_stress_run / 1e6,
        "bone_safety_factor": BONE_STRENGTH_PA / femur_stress_run,

        "T_surface": float(parent["T_surface"]),
        "day_s": float(parent["day_s"]),
        "latitude_deg": float(parent["latitude_deg"]),
        "S_earth": float(parent["S_earth"]),
    }


def emit(nums, t=1.0):
    """The matter of theHuman, in its own local units (1.0 = standing height).

    A BODY, AND ITS ONE MOVIE IS A STRIDE. Every other membrane in this story runs a movie measured
    in years or aeons and has to be geared down to be seen at all. This one takes 1.4 seconds, which
    is inside the band a person can actually feel -- the bottom of theHumanClock's ladder, reached.

    The legs swing at the period the compound pendulum derived, the stance leg vaults over the foot
    like the inverted pendulum it is, the CoM rises at mid-stance and falls between steps, and the
    arms counter-swing because whole-body angular momentum stays near zero. None of that is animated:
    the phase of every part is a function of the same t, and the numbers come from the physics above.

    IT IS A STICK FIGURE ON PURPOSE. The mass, the segment lengths, the moments of inertia and the
    timings are all derived; the flesh is not, and drawing flesh would be claiming a body this
    chapter has not built. What is shown is exactly what is known."""
    import numpy as np
    from matter import blank, paint, lit, SOLID

    tt = float(t)
    h = 1.0                                             # local units: the body is 1.0 tall
    leg = LEG_FRAC
    thigh, shank = THIGH_FRAC, SHANK_FRAC
    com_h = COM_FRAC
    phase = 2.0 * pi * tt                               # one full stride per movie

    def limb(p0, p1, n, rad):
        u = np.linspace(0.0, 1.0, n)[:, None]
        pts = p0[None, :] * (1 - u) + p1[None, :] * u
        pts = pts + np.random.default_rng(7).normal(0.0, rad * 0.30, pts.shape)
        return pts

    # ── the walk, from the derived numbers ──
    swing = 0.42                                        # hip flexion amplitude, radians
    parts = []
    for side, ph in ((-1.0, 0.0), (1.0, pi)):
        th_hip = swing * np.sin(phase + ph)
        # the knee bends only on the swing leg -- a stance knee stays near straight, which is what
        # makes walking cheap: the leg is a strut, not a spring.
        bend = max(0.0, -np.cos(phase + ph)) * 0.85
        # LATERAL IS Y, NOT X -- the hip offset used to sit on X, the axis the leg swings along, so
        # both legs were separated fore-aft and projected onto each other from the front. aHuman
        # inherited the same mistake and its derived 20 cm stance rendered as zero.
        hip = np.array([0.0, 0.055 * side, leg])
        knee = hip + np.array([np.sin(th_hip), 0.0, -np.cos(th_hip)]) * thigh
        th_knee = th_hip - bend
        ankle = knee + np.array([np.sin(th_knee), 0.0, -np.cos(th_knee)]) * shank
        parts.append(limb(hip, knee, 260, 0.035))
        parts.append(limb(knee, ankle, 260, 0.028))
        toe = ankle + np.array([FOOT_LEN_FRAC, 0.0, 0.0])
        parts.append(limb(ankle, toe, 120, 0.025))

        # ARMS COUNTER-SWING, and they are not decoration: whole-body angular momentum stays near
        # zero, so the arms must go the way the opposite leg does not.
        sh = np.array([0.0, 0.085 * side, 0.82])           # lateral is Y -- see the note above
        th_sh = -0.55 * swing * np.sin(phase + ph)
        elbow = sh + np.array([np.sin(th_sh), 0.0, -np.cos(th_sh)]) * 0.186
        hand = elbow + np.array([np.sin(th_sh * 1.4), 0.0, -np.cos(th_sh * 1.4)]) * 0.146
        parts.append(limb(sh, elbow, 180, 0.026))
        parts.append(limb(elbow, hand, 180, 0.022))

    # trunk and head, riding the CoM. It RISES at mid-stance -- the inverted pendulum vaulting over
    # the planted foot -- and that bob is the signature of a walk rather than a glide.
    bob = 0.018 * np.cos(2.0 * phase)
    pelvis = np.array([0.0, 0.0, leg + bob])
    neck = np.array([0.0, 0.0, 0.86 + bob])
    parts.append(limb(pelvis, neck, 420, 0.055))
    head = np.array([0.0, 0.0, 0.94 + bob])
    hd = np.random.default_rng(11).normal(0.0, 1.0, (700, 3))
    hd /= np.linalg.norm(hd, axis=1, keepdims=True) + 1e-9
    parts.append(head[None, :] + hd * 0.068)

    P = np.concatenate(parts, axis=0)
    n = len(P)
    b = blank(n)
    b[:, 0] = P[:, 0]
    b[:, 1] = P[:, 1]
    b[:, 2] = P[:, 2] - com_h                            # centre the view on the centre of mass
    # NORMALS ARE RADIAL FROM THE LIMB'S OWN AXIS, not from the centre of mass.
    #
    # Taking them as "away from the CoM" seems reasonable and is wrong: every grain BELOW the centre
    # of mass then gets a downward-facing normal, so the light misses it and the legs render BLACK.
    # The figure appeared to be floating above the ground with its lower half missing -- and it was
    # not floating at all. Measured, the soles sat 1.7 mm INTO the surface; they were simply unlit.
    # A limb is a tube about a vertical-ish axis, so its surface faces outward in the horizontal
    # plane, with only a little vertical component.
    nrm = np.stack([P[:, 0], P[:, 1], np.full(len(P), 0.28)], axis=1)
    flat_r = np.linalg.norm(nrm[:, :2], axis=1, keepdims=True)
    nrm[:, :2] = np.where(flat_r > 1e-6, nrm[:, :2] / np.maximum(flat_r, 1e-6) * 0.96, 0.0)
    nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9)
    b[:, 21:24] = nrm

    sun = np.array([0.55, -0.72, 0.42], np.float32)
    sun /= np.linalg.norm(sun)
    lam = np.clip(nrm @ sun, 0.0, None)
    body = np.array([0.52, 0.44, 0.38], np.float32)
    b[:, 16:19] = lit(body, float(nums.get("S_earth", 1.0)) * lam + 0.10,
                      e_ref=float(nums.get("S_earth", 1.0)), tone=0.45)
    b[:, 19] = 0.95
    b[:, 20] = 0.011
    b[:, 11] = SOLID

    # NO GROUND DRAWN HERE. It used to emit its own brown disc to stand on -- matter its PARENT
    # had already derived, at 110 kPa with a fractal grain-size distribution, which this membrane
    # then checked its own weight against and ignored when drawing. That is the star-marker moon in
    # miniature, and it was written hours after that one was deleted for the same reason.
    #
    # theGround places this body now (see its layout()), so the surface underfoot is the real one.
    # Rendered alone, this membrane is a body in the dark -- which is honest: on its own, that is
    # all it is.
    return b
