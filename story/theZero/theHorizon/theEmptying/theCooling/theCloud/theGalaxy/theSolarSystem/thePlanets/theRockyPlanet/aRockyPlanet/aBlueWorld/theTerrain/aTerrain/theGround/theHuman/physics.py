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


def _ansur():
    """THE MEASURED POPULATION. ANSUR II (US Army 2012, public 2017): 6,068 subjects x 93
    measures, distilled to anchors by tools/build_ansur_anchors.py. The operator's law: for a
    human body, actual sources for every concept -- no guessing. Where a cadaver-joint number
    (Dempster, for the swing physics) and a surface-measure number (ANSUR) differ, both are
    kept and named for what they measure -- the same discipline as the two angles of repose."""
    import json
    from pathlib import Path
    p = Path(__file__).resolve()
    for q in p.parents:
        f = q / "research_references" / "human" / "ansur_anchors.json"
        if f.exists():
            return json.loads(f.read_text())
    raise FileNotFoundError("ansur_anchors.json -- run tools/build_ansur_anchors.py")


_AN = _ansur()["male"]          # the person of this story defaults to the measured male median

# ── DEMPSTER'S ANTHROPOMETRIC RATIOS: segment lengths and masses as fractions of stature and body
#    mass. Measured on cadavers (Dempster 1955, still the standard), so they are data, not choices.
LEG_FRAC = 0.530           # hip JOINT to floor (Dempster): the pendulum's length. The SURFACE
                           # landmark (trochanterion) sits lower: ANSUR II measures 0.5121 of
                           # stature (n=4,082) -- used for the outer body, not the swing.
THIGH_FRAC = 0.245         # hip to knee
SHANK_FRAC = 0.246         # knee to ankle
FOOT_LEN_FRAC = float(_AN["foot_length_m"]["median"]) / float(_AN["stature_m"]["median"])   # 0.1544, ANSUR II
COM_FRAC = 0.575           # standing centre of mass, as a fraction of height
# EYE HEIGHT, and it belongs to the body rather than to a camera. This lived in ChimeraEngine's
# walker as a bare `0.94 * height` -- a fact about human anatomy asserted inside a viewer, where no
# audit reaches it and nothing connects it to the stature it multiplies. MEASURED now: the ear
# level (tragion, ~eye level) sits at 0.9253 of stature across 4,082 subjects (ANSUR II;
# Dempster's cadaver eye was 0.936).
EYE_FRAC = float(_AN["eye_frac_of_stature"]["median"])
# LEG_MASS_FRAC AND LEG_COM_FRAC ARE GONE. They were 0.161 and 0.447 -- Dempster (1955), measured on
# EIGHT CADAVERS, and still the most-quoted figures anywhere. They now come from `story/measured.py`,
# which holds de Leva (1996): Zatsiorsky's GAMMA-RAY SCANS OF 100 LIVING ADULTS, re-referenced to
# joint centres. The whole leg comes out at 0.1986 rather than 0.161 -- 23% heavier -- and a leg's
# mass is what sets the swing period, which sets cadence.

BMI_REF = float(_AN["bmi"]["median"])   # MEASURED: 27.5, the median of 4,082 soldiers (ANSUR II)
                                         # -- muscular population. Was 22.5, a "healthy" guess:
                                         # mass = BMI * h^2 lands 84.7 kg at 1.755 m, against the
                                         # survey's own median of 84.6 kg. Self-consistent.
FOOT_WIDTH_FRAC = float(_AN["foot_breadth_m"]["median"]) / float(_AN["stature_m"]["median"])  # ANSUR II

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
    # a fact about a body. Everything else on this page follows from it and from g. The default and
    # the dial's range are MEASURED now: the ANSUR II male median and its 5th-95th percentile band
    # (1.648-1.87 m, n=4,082) -- no longer a chosen 1.78 between invented 1.2 and 2.2.
    "height_m": {"lo": float(_AN["stature_m"]["p5"]), "hi": float(_AN["stature_m"]["p95"]),
                 "default": float(_AN["stature_m"]["median"]),
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

    # AND WHO THE PERSON IS. Melanin is not derivable from a planet either; it is a fact about a
    # body, and the second HUMAN-terminal dial here (the first is the calendar). What IS measured
    # is the dial's range: Jacques' melanosome volume fractions by pigmentation class
    # (light 1.3-6.3%, moderate 11-16%, dark 18-43%). What the dial changes is not a palette: it is
    # how much light the epidermis eats before the dermis can return any -- the physics is in
    # story/skin_optics.py, the choice is the operator's.
    "melanin_fraction": {"lo": 0.013, "hi": 0.43, "default": 0.135,
                         "label": "melanosome fraction", "unit": "of epidermis volume",
                         "local": "pigmentation -- the operator's call, the measured range Jacques published"},
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


# ── THE FOOT IS A WHEEL, and that is a measurement, not a metaphor ──────────────────────────────
# Hansen, Childress & Knox (2004) measured the "roll-over shape": the locus the effective contact
# point traces during stance, in a shank-based frame. It is very nearly a CIRCULAR ARC, and its
# radius is about 0.30 of leg length -- almost independent of walking speed, which is what makes it
# a property of the limb rather than of the gait.
#
# A rocker of radius R rolls with its hub at CONSTANT height R. So the hip, rigidly at distance
# (L - R) from that hub, rises and falls by (L - R)(1 - cos theta) instead of L(1 - cos theta): the
# foot takes 30% of the vault out of the walk for free. That is a large part of why walking is cheap.
ROCKER_FRAC = 0.30         # rocker radius / leg length -- Hansen, Childress & Knox 2004
ANKLE_DROP_FRAC = LEG_FRAC - (THIGH_FRAC + SHANK_FRAC)   # ankle to sole: a foot has thickness
FOREFOOT_FRAC = 0.10       # ball-of-foot to ankle, as a fraction of stature (Dempster)


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE GAIT IS NOW MEASURED -- 246 adults, not a sine
# ════════════════════════════════════════════════════════════════════════════════════════════════
# WHAT WAS HERE. `SWING_AMP = 0.42`, described in its own comment as "the one number in this gait
# that is neither derived nor measured", and a `foot_pitch` built from three hand-placed fractions.
# Every number that scales with the hip amplitude -- the vault, the centre-of-pressure travel, the
# stride -- inherited that. Naming it was the honest half of the fix. This is the other half.
#
# WHAT REPLACES IT. Van Criekinge et al. (2023): 246 healthy adults aged 18-91 walking at three
# self-selected speeds, joint angles for every percent of the cycle, grouped by sex and age decade.
# CC BY 4.0, OSF doi 10.17605/OSF.IO/T72CW. Read through `measured.gait_*`.
#
# WHAT A SINE COULD NEVER HAVE GIVEN, and the reason this matters more than a better amplitude:
#   * A real hip curve is ASYMMETRIC. It rises steeply through swing and falls slowly through
#     stance. A sine is symmetric by construction, so half of every step was drawn backwards.
#   * The knee has TWO flexion peaks, and the small one is the important one: an ~18 degree wave
#     during STANCE, at 11% of the cycle. theAnkle named exactly this as the missing mechanism
#     behind its vault being 4.7% of stature against a human 2.5%, and wrote "the mechanism is
#     named rather than the number scaled, because scaling it would be tuning the answer." The
#     mechanism now arrives as data, and the vault falls or it does not.
#   * The foot's angle to the ground stops being a model at all. It FOLLOWS from the other three
#     by forward kinematics -- see foot_pitch() -- so the three rockers are a consequence rather
#     than an input, and `measure()` checks the sole really does go flat when it should.
#
# THE TEMPO IS STILL DERIVED, AND THAT SEPARATION IS DELIBERATE. The compound-pendulum law gives
# the period; the 246 adults give the shape. Substituting measured cadence for the derived one
# would delete a derivation and put data in its place, which is the opposite of the method. They
# are compared in measure() instead, where a disagreement is a finding rather than a silent patch.
GAIT_SEX = "male"          # which measured cohort this body's walk is read from
GAIT_AGE = 30.0            # years -- a dial: turn it and the curves change, because people do
_GAIT_CACHE = None


def measured_gait(v_ms=None, sex=None, age=None):
    """The measured curves for this body's cohort, at the speed it actually walks.

    THE SPEED IS A DIAL BECAUSE THE STUDY MEASURED THREE OF THEM. A membrane derives a comfortable
    speed from its own Froude number, and that speed selects the curve shape -- interpolated between
    slow, comfortable and fast, clamped at the ends. Walk faster and the hip really does reach
    further, because 246 people were measured reaching further, not because a gain was raised."""
    global _GAIT_CACHE
    import measured

    g = measured.gait_group(sex or GAIT_SEX, GAIT_AGE if age is None else age)
    v = None if v_ms is None else float(v_ms)
    key = (g, None if v is None else round(v, 4))
    if _GAIT_CACHE is not None and _GAIT_CACHE["key"] == key:
        return _GAIT_CACHE

    # which measured speed condition sits nearest, for the scalars that have no curve
    speeds = sorted((abs(measured.gait_walking_speed(s, g) - (v if v else 1.3)), s)
                    for s in measured.GAIT_SPEEDS)
    near = speeds[0][1]
    d = measured.gait_duty(near, g)

    def curve(p):
        if v is None:
            return [measured.gait_sample(p, i / 100.0, near, g) for i in range(100)]
        return [measured.gait_sample_at_speed(p, i / 100.0, v, g) for i in range(100)]

    _GAIT_CACHE = {
        "key": key, "group": g, "nearest_condition": near,
        "hip": curve("hip_flex"), "knee": curve("knee_flex"), "ankle": curve("ankle_flex"),
        # HOW MUCH OF THE BODY EACH LEG IS ACTUALLY CARRYING, at every point of the cycle. This is
        # not decoration -- it is what decides the hip's height during double support. See _gait_table.
        "grf": curve("grf_vert"),
        "duty": d["duty"], "double_support": d["double_support_frac"],
        "measured_speed_ms": measured.gait_walking_speed(near, g),
        "measured_cadence_min": measured.gait_scalar("Cadans [1/m]", near, g)[0],
        "measured_stride_m": measured.gait_scalar("R.Stride.Length [m]", near, g)[0],
        "measured_step_width_m": measured.gait_scalar("R.Step.Width [m]", near, g)[0],
        "measured_clearance_m": measured.gait_scalar("R.Foot.Clear [cm]", near, g)[0] / 100.0,
        "grf_peak_bw": max(measured.gait_curve("grf_vert", near, g)["mean"]),
        "ankle_moment_peak_Nm_per_kg": max(measured.gait_curve("ankle_moment", near, g)["mean"]),
        "source": d["source"],
    }
    return _GAIT_CACHE


def _at(curve, f):
    """Sample a 100-point measured curve at cycle fraction f, in RADIANS.

    Degrees in the source, radians here: the source's unit is what it published, and this story's
    unit is what its trigonometry needs. Converting at the boundary is the only place it is safe."""
    x = (float(f) % 1.0) * 100.0
    i = int(x) % 100
    j = (i + 1) % 100
    w = x - int(x)
    return math.radians(curve[i] + (curve[j] - curve[i]) * w)


# THE PEAK VERTICAL GROUND REACTION, measured off the same 246 rather than quoted. It was typed here
# as 1.2 body weights; the measurement is 1.10. That 9% mattered -- see ankle_torque().
GRF_PEAK_BW_TYPED = 1.2


# ── THE ANKLE AS A JOINT, which is what actually produces the rocker ───────────────────────────
# The 0.30-of-leg-length arc is an EFFECTIVE description of a foot that has three contact regions in
# sequence -- heel, then flat sole, then forefoot -- and an ankle that pitches the foot between them.
# Modelling it as a literal wheel raises the hip without giving the foot anywhere to be: measured,
# that lifted the sole and cut duty factor to 0.12. So the joint is modelled, and the arc emerges.
#
# The pitch angles are measured human ankle kinematics in level walking.
HEEL_FRAC = 0.050          # heel behind the ankle, fraction of stature (Dempster)
# DUTY FACTOR is no longer typed. It was 0.60, chosen because a sine hip angle puts each foot down
# for EXACTLY half the cycle -- so the two stances abut, never overlap, and the walk has no double
# support and therefore no leg pushing off while the other reaches. The reasoning was right and the
# number was a guess. Measured on the 246: stance/stride = 0.6051, double support 0.2125.


GAIT_N = 48                # samples of the cycle published for children to index


def _gait_table(h, v_ms=None, ball=None, curves=None):
    """The whole gait, sampled, in units of stature. See "THE GAIT AS A TABLE" in derive().

    EACH ROW IS [hip height, then per leg: hip angle, knee angle, foot pitch, stance progress,
    planted]. The knee and the pitch are new: the child used to rebuild both from a copy of the
    law, which is the drift this table exists to prevent -- two gaits that agree until one is
    edited. Now there is one gait, it is measured, and everything downstream indexes it.

    `curves` overrides the curve set: None is the forward walk (246 adults, measured_gait);
    directional_curves(name) hands in a CMU-measured direction (A3). When that direction's legs
    are NOT the same curve -- a sidestep's trailing leg crosses -- the dict carries "legs" and
    each leg reads its own."""
    G = curves if curves is not None else measured_gait(v_ms)
    out = []
    for k in range(GAIT_N):
        tt = k / GAIT_N
        legs, sup, wts = [], [], []
        for li, off in enumerate((0.0, 0.5)):
            Gl = G["legs"][li] if "legs" in G else G
            hip_a, knee_a, u, planted = leg_cycle(tt + off, v_ms, Gl)
            pitch = foot_pitch(hip_a, knee_a, tt + off, v_ms, Gl)
            legs.append((hip_a, knee_a, pitch, u, 1.0 if planted else 0.0))
            if planted:
                sup.append(hip_above_ankle(hip_a, knee_a) + ankle_height(pitch, ball))
                # HOW MUCH THIS LEG IS CARRYING, measured, at its own point in the cycle.
                wts.append(max(_grf(G, tt + off), 0.0))
        # ── THE HIP RIDES THE LEGS IN PROPORTION TO WHAT THEY ARE CARRYING ───────────────────────
        # This used to be `max(sup)`: the body rests on whichever planted leg holds it highest. That
        # is a rigid-strut model, and with the measured curves in place it broke visibly. At 6% of
        # the cycle the TRAILING leg is at 91% of its stance, up on a plantarflexed toe, and `max`
        # let it prop the pelvis at full extension; six percent later it lifts and the hip fell 3.9%
        # of stature in two samples. A cliff in a body's height is not a walk.
        #
        # The error was treating "planted" as a switch. A trailing limb in terminal double support
        # is UNLOADING -- its ground reaction is already on its way to zero -- so it is pushing, not
        # propping. `max` was a stand-in for "whichever leg is carrying the body", and the vertical
        # ground reaction answers that question directly and continuously. Weighting by it removes
        # the discontinuity BY CONSTRUCTION: a leg stops setting the body's height at exactly the
        # rate it stops bearing it, and the GRF curve goes smoothly to zero at toe-off.
        #
        # Nothing here is smoothed or blended for looks. The blend IS the load transfer, measured.
        if sup and sum(wts) > 1e-6:
            hip = sum(s * w for s, w in zip(sup, wts)) / sum(wts)
        elif sup:
            hip = max(sup)                     # both feet down and neither loaded: nothing to weight
        else:
            hip = ANKLE_DROP_FRAC + THIGH_FRAC + SHANK_FRAC
        out.append([round(hip, 6)] + [round(v, 6) for lg in legs for v in lg])
    return out


def _grf(G, f):
    """What one leg is carrying at cycle fraction f, in body weights. Measured; zero through swing."""
    x = (float(f) % 1.0) * 100.0
    i = int(x) % 100
    j = (i + 1) % 100
    w = x - int(x)
    return G["grf"][i] + (G["grf"][j] - G["grf"][i]) * w


def directional_curves(name, grf):
    """One measured DIRECTION as the curves dict _gait_table consumes (A3).

    The forward walk in this story is 246 adults on an instrumented treadmill; the other directions
    are CMU MoCap trials -- a hallway, no force plates -- distilled to story/data/gait_directional.json
    by tools/ingest_gait_cmu_directional.py. So the LOAD curve (how much of the body each leg carries
    through the cycle) stays the treadmill's, handed in as `grf`; what each direction brings is its
    own hip/knee/ankle shapes and its own duty factor, measured off the trials. A sidestep's legs are
    NOT the same curve -- the trailing one crosses -- so those arrive per leg ("legs"), the leading
    leg first."""
    import measured as _m
    d = _m.gait_directional()["directions"][name]
    if d.get("symmetric", True):
        return {"hip": d["hip_deg"], "knee": d["knee_deg"], "ankle": d["ankle_deg"],
                "duty": d["duty"], "grf": grf}
    return {"grf": grf,
            "legs": [{"hip": d["lead"]["hip_deg"], "knee": d["lead"]["knee_deg"],
                      "ankle": d["lead"]["ankle_deg"], "duty": d["lead"]["duty"]},
                     {"hip": d["trail"]["hip_deg"], "knee": d["trail"]["knee_deg"],
                      "ankle": d["trail"]["ankle_deg"], "duty": d["trail"]["duty"]}]}


def leg_cycle(f, v_ms=None, G=None):
    """WHERE ONE LEG IS at cycle fraction f (0 = its own heel strike).

    Returns (hip angle, knee angle, stance progress u, planted). Both angles are read from the
    measured curves; `planted` comes from the measured duty factor. Nothing in this function is a
    shape any more -- it is an index into 246 people.

    `G` overrides the curve set: the forward walk leaves it None (246 adults on a treadmill);
    a DIRECTION hands in its own CMU-measured curves (see directional_curves) -- same law,
    different measurement."""
    G = G if G is not None else measured_gait(v_ms)
    f = float(f) % 1.0
    duty = G["duty"]
    hip_a, knee_a = _at(G["hip"], f), _at(G["knee"], f)
    if f < duty:
        return hip_a, knee_a, f / duty, True
    return hip_a, knee_a, (f - duty) / (1.0 - duty), False


def foot_pitch(hip_a, knee_a, f, v_ms=None, G=None):
    """THE FOOT'S ANGLE TO THE GROUND -- DERIVED, not modelled, and this is the good part.

    The three-rocker model used to live here: toe up for the first 15% of stance, flat for 50%,
    heel up for the last 35%, with the fractions placed by hand. It is gone, because the foot's
    angle to the GROUND is not free once the three joint angles are known. Walk the chain down:

        thigh from the hip at  hip_a  from vertical
        shank from the knee at hip_a - knee_a       (knee flexion folds the shank backward)
        foot  from the ankle, dorsiflexed by ankle_a from perpendicular to the shank

    so the sole's angle to the floor is

        pitch = ankle_a + hip_a - knee_a

    THE CHECK NOBODY FITTED: this identity is pure kinematics -- no gait in it -- yet fed the three
    measured curves it reproduces the three rockers on its own. It gives +23 degrees of toe-up at
    heel strike (the measured foot-floor angle at initial contact is ~20-25), passes through zero
    in mid-stance where the sole is flat, and goes heel-up through push-off. Three independently
    measured curves and one piece of geometry agreeing is what a derivation looks like when it is
    real. `measure()` checks the flat phase explicitly rather than trusting this paragraph."""
    G = G if G is not None else measured_gait(v_ms)
    return _at(G["ankle"], f) + float(hip_a) - float(knee_a)


def hip_above_ankle(hip_a, knee_a):
    """HOW FAR THE HIP SITS ABOVE THE ANKLE, in units of stature, for a two-link leg.

    The old model had one link: L*cos(theta), a leg that could not bend. That is what made the walk
    a pole-vault -- a rigid strut has no way to shorten as the body passes over it, so the hip had
    to rise. A real stance knee flexes ~18 degrees just after contact and absorbs exactly that."""
    return (SHANK_FRAC * math.cos(float(hip_a) - float(knee_a))
            + THIGH_FRAC * math.cos(float(hip_a)))


def forefoot_lever_frac(g=9.80665, h=1.78, v_ms=None):
    """WHERE THE FOOT PIVOTS AT PUSH-OFF, derived from two measured curves instead of typed.

    It was `FOREFOOT_FRAC = 0.10` of stature, attributed to Dempster in a comment. Two measurements
    from the same study give it without anyone choosing: at push-off the ground reaction F acts on
    the forefoot lever r and produces the ankle moment tau, so

        r = tau / F        with tau measured in N.m/kg and F measured in body weights

    which is r/h = tau_per_kg / (F_bw * g * h). Both peaks occur within one percent of the cycle of
    each other (moment at 47%, the second force peak at 46%), which is what licenses treating them
    as the same instant -- stated because it is an assumption, not a fact."""
    G = measured_gait(v_ms)
    return (G["ankle_moment_peak_Nm_per_kg"]
            / max(G["grf_peak_bw"] * float(g) * float(h), 1e-9))


def ankle_height(pitch, ball_frac=None):
    """HOW HIGH THE ANKLE SITS when the foot is pitched and its lowest point is on the ground.

    THE PIVOT IS THE BALL OF THE FOOT, NOT THE TOE TIP, and getting that wrong was worth 3.6% of
    stature. This used to swing the foot about `FOOT_LEN_FRAC` -- the whole 0.152 of stature from
    ankle to toe end -- so a plantarflexed trailing leg stood on its toe TIP and lifted the pelvis
    nearly 11 cm. A real foot rolls over the metatarsal heads; the toes beyond them go down with it
    but do not carry the body.

    THE NUMBER CAME FROM SOMEWHERE ELSE, WHICH IS WHY IT COUNTS. The lever that closes the geometry
    is ~0.071 of stature, and 0.071 is independently what the measured ankle MOMENT divided by the
    measured ground REACTION says the lever must be -- see forefoot_lever_frac(). A kinematic check
    and a kinetic check, from different sheets of the same study, on the same millimetre. Measured:
    the two legs' demanded pelvis heights disagreed by 5.73% of stature with the toe-tip pivot and
    2.10% with this one, and the residual is the unsourced segment lengths, named in measured.py.

    The heel end is unchanged. Taking the lower of the two ends is still the whole case analysis --
    no branch for heel-strike versus toe-off is written, because the geometry already knows."""
    ball = FOREFOOT_FRAC if ball_frac is None else float(ball_frac)
    hz = -HEEL_FRAC * math.sin(pitch) - ANKLE_DROP_FRAC * math.cos(pitch)
    tz = ball * math.sin(pitch) - ANKLE_DROP_FRAC * math.cos(pitch)
    return -min(hz, tz)


def rocker_radius(leg_L):
    """The effective radius the foot and ankle roll on."""
    return ROCKER_FRAC * float(leg_L)


def hip_height(leg_L, theta, R=None):
    """HOW HIGH THE HIP SITS while the stance leg is at angle theta from vertical.

    With a point foot this is L cos(theta) and the body pole-vaults over its own heel. With a rocker
    the hub stays at R and only the remainder swings, so the path flattens. Set R = 0 to recover the
    point-foot pendulum and see the difference."""
    R = rocker_radius(leg_L) if R is None else float(R)
    return R + (float(leg_L) - R) * math.cos(float(theta))


def ankle_torque(mass, g, h, v_ms=None):
    """WHAT THE ANKLE HAS TO PUSH WITH at toe-off. Now read from the measured moment curve.

    A CORRECTION THIS CHAPTER OWES ITS READER. What stood here was
        tau = GRF_PEAK_BW * m * g * FOREFOOT_FRAC * h,  with GRF 1.2 BW and the lever 0.10h
    which gives 1.51 N*m/kg, and the docstring called that an unfitted check against a literature
    peak of ~1.5. The RESULT was right: the same 246 adults measure the peak plantarflexor moment
    at 1.51 N*m/kg, which is as close as measurements of a person get.

    But the inputs were not. The measured peak vertical ground reaction is 1.10 body weights, not
    1.2 -- so the factor was 9% high, and the product only landed because the true forefoot lever is
    about 9% longer than 0.10h. TWO ERRORS OF OPPOSITE SIGN CANCELLED, and a check that passes for
    a compensating reason is not a check. This is the sharpest illustration in the chapter of why a
    source beats a plausible number: nothing about that agreement looked wrong from the inside.

    So the torque is now the measurement, scaled by this body's own mass, and the old product is
    kept as `ankle_torque_from_lever` so the discrepancy stays visible instead of being tidied away.
    The gravity argument still applies: the moment scales with weight, so a lighter world asks less
    of the ankle, and the ratio to Earth's g carries that."""
    G = measured_gait(v_ms)
    return G["ankle_moment_peak_Nm_per_kg"] * float(mass) * (float(g) / 9.80665)


def ankle_torque_from_lever(mass, g, h, grf_bw):
    """The superseded product, kept so the two can be printed side by side."""
    return float(grf_bw) * float(mass) * float(g) * FOREFOOT_FRAC * float(h)


def body_mass(h):
    """Mass from stature. Mass goes as height SQUARED, not cubed -- which is the empirical finding
    behind BMI, and the reason tall people are not as heavy as pure geometric scaling predicts."""
    return BMI_REF * h * h


def leg_inertia(h, m, sex="male"):
    """The swinging leg as a compound pendulum about the hip -- COMPOSED FROM THREE MEASURED SEGMENTS
    rather than approximated as one rod.

    This used to model the whole leg as a single rod: mass 0.161 of the body (Dempster, 8 cadavers),
    centre at 0.447 of its length, radius of gyration "about 0.326 of its length". All three were
    assertions, and the composite disagrees with them by 19%.

    measured.leg_inertia_about_hip() sums m(k^2 + d^2) over thigh, shank and foot using de Leva's
    per-segment masses, centres and gyration radii, with the parallel-axis theorem doing the rest.

    IT LANDS WHERE THE MODEL DOES. The composite gives I = 2.890 kg m^2; this studio's own
    measurement off myobody, recorded in CLAUDE.md, was 2.879 -- 0.4% apart from two independent
    sources, where the rod approximation was 24% away from both. (The two bodies differ in mass and
    in leg length, so some of that agreement is luck; the direction of the correction is not.)"""
    import measured
    r = measured.leg_inertia_about_hip(h, m, THIGH_FRAC, SHANK_FRAC, FOOT_LEN_FRAC, sex)
    return r["I_hip_kgm2"], r["leg_mass_kg"], r["leg_com_from_hip_m"]


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


def walk_run_speed(coeff, h):
    """WHERE WALKING GIVES OUT. Fr = v^2/(gL); at Fr ~ 0.5 the stance leg would need centripetal force
    greater than gravity can supply, so the gait must change. The SAME 0.5 everywhere, which is what
    makes it a law rather than a fit.

    THE COEFFICIENT COMES FROM THE PLANET AND THE LENGTH FROM HERE. theRockyPlanet publishes
    sqrt(0.5 g) because g is the only half of this it can honestly know; this membrane multiplies by
    the square root of its own leg. The planet used to publish the whole speed from a typed 0.845 m
    leg, six membranes above the first body in the story -- an ancestor holding a descendant's number,
    and 5.4% away from what the body itself derives. Splitting it this way means there is exactly one
    walk-run speed in the tree and its two factors come from the two places that own them."""
    return float(coeff) * sqrt(LEG_FRAC * float(h))


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
    v_walkrun = walk_run_speed(parent["walk_run_per_sqrt_leg"], h)
    v_comfort = 0.55 * v_walkrun                 # the speed people actually choose, ~55% of the limit
    # A STEP IS NOT A STRIDE, and this line was publishing one under the other's name. `cadence` is
    # STEPS per second, so speed / cadence is metres per STEP -- and a stride is two steps, left plus
    # right. The measured comparison is what caught it: 0.60 against a measured stride of 1.13 is not
    # a 47% error in a derivation, it is a factor of two in a label. Doubled, they agree to 6%.
    step_len = v_comfort / cadence
    stride = 2.0 * step_len

    # ── THE MEASURED GAIT, at the speed this body derived for itself ──────────────────────────
    # The chain runs the right way round: the Froude law gives a comfortable speed, that speed picks
    # the measured curve shape, and the shape then decides the vault and the push-off. Nothing here
    # reads a number back to set the speed it came from.
    G = measured_gait(v_comfort)
    import measured as _measured
    leg_frac_measured = _measured.leg_over_stature(GAIT_SEX)[0]
    # WHERE THE FOOT PIVOTS, derived from the measured moment and force rather than typed as 0.10.
    ball = forefoot_lever_frac(g, h, v_comfort)

    # ── THE VAULT, MEASURED OFF THE GAIT ITSELF ───────────────────────────────────────────────
    # With a sine hip it was L(1 - cos(SWING_AMP)) -- a closed form, because a sine has an amplitude.
    # A real leg has no amplitude: the hip's path is whatever the three measured curves and the load
    # transfer make it, so the only honest number is the range of the path the body actually takes.
    _tab = _gait_table(h, v_comfort, ball)
    # ── THE OTHER DIRECTIONS A BODY WALKS, measured too (A3) ──────────────────────────────────
    # Backward and sidestep are not the forward gait played in reverse or rotated: the shapes are
    # their own measurements (CMU trials, story/data/gait_directional.json), built into tables by
    # the SAME law above, so the hip's height, the boot's pitch and the child's IK agree with them
    # by construction. A sidestep's stride is shorter -- published per direction so the walker's
    # phase (distance / stride) does not make a backpedal's feet skate.
    gait_cycles = {"forward": _tab}
    gait_dir_stride = {"forward": stride}
    for _dn in ("backward", "left", "right"):
        gait_cycles[_dn] = _gait_table(h, v_comfort, ball,
                                       curves=directional_curves(_dn, G["grf"]))
        gait_dir_stride[_dn] = float(_measured.gait_directional()["directions"][_dn]["stride_m"])
    hip_path = [r[0] for r in _tab]
    vault_measured = (max(hip_path) - min(hip_path)) * h
    hip_max, hip_min = max(r[1] for r in _tab), min(r[1] for r in _tab)
    # WHAT THE SAME BODY WOULD DO WITHOUT ITS FOOT AND WITHOUT ITS KNEE, over the SAME cycle rather
    # than from a closed form -- a straight leg, a point contact at the ankle, same hip angles. That
    # is the compass gait, and the difference between the two is what a foot and a knee are worth.
    _rigid = []
    for _k in range(GAIT_N):
        _sup = [(THIGH_FRAC + SHANK_FRAC) * math.cos(leg_cycle(_k / GAIT_N + _o, v_comfort)[0])
                for _o in (0.0, 0.5) if leg_cycle(_k / GAIT_N + _o, v_comfort)[3]]
        if _sup:
            _rigid.append(max(_sup))
    vault_point = ((max(_rigid) - min(_rigid)) * h) if _rigid else 0.0

    tau_ankle = ankle_torque(m, g, h, v_comfort)
    tau_lever = ankle_torque_from_lever(m, g, h, GRF_PEAK_BW_TYPED)

    foot_area = (FOOT_LEN_FRAC * h) * (FOOT_WIDTH_FRAC * h)
    weight = m * g
    foot_press = weight / foot_area              # standing on one foot
    ground_holds = float(parent["bearing_capacity_Pa"])

    femur_stress = weight / FEMUR_AREA_M2        # standing, both legs share it -> one femur, half
    femur_stress_run = 3.0 * femur_stress        # running peaks near 3x body weight per leg

    # ── THE SKIN THE BODY IS IN, measured optics rather than a picked tone ────────────────────
    # The law is story/skin_optics.py (Jacques 1998 + Prahl's archived hemoglobin table): the
    # epidermis is a melanin filter crossed twice, the dermis a blood-and-collagen diffuser. What
    # this membrane publishes is the law's answer at the renderer's own three bands, so the face
    # aHuman draws and the swatch theSkin draws are the SAME skin, derived once, here -- the parent
    # carrying what both children need, the star-colour rule applied to a body.
    import skin_optics as _skin
    f_mel = float(free.get("melanin_fraction", FREE["melanin_fraction"]["default"]))
    # the dial is continuous but the taxonomy is banded: take the class whose band is nearest
    melanin_class = min(_skin.F_MEL_CLASSES,
                        key=lambda c: 0.0 if _skin.F_MEL_CLASSES[c][0] <= f_mel <= _skin.F_MEL_CLASSES[c][1]
                        else min(abs(f_mel - e) for e in _skin.F_MEL_CLASSES[c]))
    # DuBois & DuBois 1916: body surface from mass and stature -- the number aHuman's thermal
    # balance and theSkin's breach accounting both size themselves with. It was typed as 1.83 m2
    # (the 70 kg "standard man"); THIS body is the ANSUR median, and the formula says otherwise.
    skin_area = 0.007184 * (m_bare ** 0.425) * ((100.0 * h) ** 0.725)

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

        # ── THE SKIN, DERIVED ONCE FOR BOTH CHILDREN (aHuman's face, theSkin's swatch) ─────────
        "melanin_fraction": f_mel,
        "melanin_class": melanin_class,                  # the name is a claim, measured bands above
        "skin_albedo_rgb": _skin.skin_albedo_rgb(f_mel), # at 615/535/465 nm -- the renderer's bands
        "skin_bands_nm": list(_skin.BANDS_NM),
        "skin_sss_mfp_mm": _skin.skin_sss_mfp_mm(),      # subsurface reach per band, for wrap light
        "skin_area_m2": skin_area,                       # DuBois 1916 on the BARE mass and stature
        "skin_blood_fraction": _skin.F_BLOOD_AVG,
        "skin_optics_source": ("Jacques OMLC 1998 (archived) + Prahl hemoglobin table "
                               "(research_references/human/hemoglobin_extinction_prahl.json)"),

        "height_m": h,
        "mass_kg": m,
        "com_height_m": com_h,
        "eye_height_m": EYE_FRAC * h,          # what a first-person camera sits at, derived here
        "leg_length_m": leg_L,
        "leg_inertia_kgm2": I_leg,
        # WHERE THE BODY'S NUMBERS CAME FROM, carried so a reader need not trust a comment.
        "anthropometry_source": "de Leva 1996 (Zatsiorsky gamma-ray, 100 living adults)",
        "leg_mass_frac": m_leg / m,
        "segment_lengths_are_sourced": False,   # THIGH/SHANK/FOOT fractions are still this repo's
        "leg_mass_kg": m_leg,
        "g": g,

        # ── THE GAIT AS A TABLE, so a child can walk without re-deriving how ──────────────────
        # aHuman needs the same pose to hang a suit on, and the rule is that a child consumes its
        # parent's NUMBERS and never its parent's reasoning. Restating leg_cycle/foot_pitch in the
        # child would satisfy the letter and invite the drift the rule exists to prevent -- two
        # copies of a gait that agree until one is edited. So the pose is published: 48 samples of
        # (hip height, and per leg the hip angle, the stance progress, and whether it is planted).
        # A child indexes it. There is exactly one gait in this story and it lives here.
        "gait_samples": GAIT_N,
        "gait_cycle": _tab,
        "gait_cycles": gait_cycles,               # A3: forward/backward/left/right, same law
        "gait_dir_stride_m": gait_dir_stride,     # each direction's OWN measured stride
        "gait_row": "hip_height, then per leg: hip_rad, knee_rad, foot_pitch_rad, u, planted",

        # ── WHERE THE WALK CAME FROM, so no child has to trust a comment ──────────────────────
        "gait_source": G["source"],
        "gait_group": G["group"],
        "gait_is_measured": True,
        "gait_speed_condition": G["nearest_condition"],
        "duty_factor": G["duty"],
        "double_support_frac": G["double_support"],
        # THE MEASURED COUNTERPARTS OF NUMBERS THIS MEMBRANE DERIVES. Published side by side rather
        # than substituted: the law predicts, the data judges, and a gap is a finding.
        "measured_cadence_steps_min": G["measured_cadence_min"],
        "measured_speed_ms": G["measured_speed_ms"],
        "measured_stride_m": G["measured_stride_m"],
        "measured_step_width_m": G["measured_step_width_m"],
        "measured_foot_clearance_m": G["measured_clearance_m"],
        "measured_grf_peak_bw": G["grf_peak_bw"],
        "measured_leg_over_stature": leg_frac_measured,
        "leg_over_stature_used": LEG_FRAC,

        # ── THE ANKLE, which is why the walk is cheap ─────────────────────────────────────────
        "rocker_radius_m": rocker_radius(leg_L),
        "rocker_over_leg": ROCKER_FRAC,
        "vault_point_foot_m": vault_point,
        "vault_rocker_m": vault_measured,
        "vault_saved_frac": rocker_radius(leg_L) / leg_L,
        "cop_travel_m": rocker_radius(leg_L) * (hip_max - hip_min),
        "ankle_torque_Nm": tau_ankle,
        "ankle_torque_Nm_per_kg": tau_ankle / m,
        # the superseded product and the 9% that was hiding inside it -- see ankle_torque()
        "ankle_torque_from_lever_Nm": tau_lever,
        "ankle_torque_lever_error_pct": 100.0 * (tau_lever - tau_ankle) / tau_ankle,
        "grf_peak_bw_typed_was": GRF_PEAK_BW_TYPED,
        # THE FOOT'S PIVOT, derived from the measured moment and force -- and it was 40% wrong.
        "forefoot_lever_m": ball * h,
        "forefoot_lever_frac": ball,
        "forefoot_lever_typed_was_m": FOREFOOT_FRAC * h,
        "foot_pivot_is_derived": True,
        # THE REST OF THE CONTACT LAW, published so a child can draw a foot that agrees with the
        # gait table: the heel's lever behind the ankle (where initial contact lands), and the
        # ankle's height above the sole plane it pivots over. The table's hip heights were solved
        # against exactly these -- a boot built from them cannot disagree with the hip it serves.
        "heel_lever_frac": HEEL_FRAC,
        "ankle_drop_frac": ANKLE_DROP_FRAC,

        "fall_rate_rad_s": w0,                   # sqrt(g/H): how fast balance is lost
        "time_to_fall_s": 1.0 / w0,
        "capture_point_at_1ms": capture_point(g, com_h, 1.0),
        "swing_period_free_s": T_swing,          # the leg left to hang
        "step_time_s": T_step,                   # what the hip flexors actually deliver
        "swing_drive": SWING_DRIVE,
        "cadence_steps_s": cadence,
        "cadence_steps_min": cadence * 60.0,
        "walk_run_ms": v_walkrun,
        # the planet's coefficient, carried so a reader can check the multiplication themselves
        "walk_run_per_sqrt_leg": float(parent["walk_run_per_sqrt_leg"]),
        "swing_period_per_sqrt_leg": float(parent["swing_period_per_sqrt_leg"]),
        "comfortable_speed_ms": v_comfort,
        "stride_m": stride,                      # left heel strike to the next left heel strike
        "step_length_m": step_len,               # one foot ahead of the other -- half a stride
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

    # ── the walk, READ FROM THE PUBLISHED TABLE ──────────────────────────────────────────────────
    # Not recomputed. derive() sampled the measured curves into `gait_cycle`, and this membrane's own
    # picture indexes the same rows its children do -- so the drawing and the numbers cannot drift,
    # and if the table is wrong the render is visibly wrong rather than quietly different.
    _GT = nums["gait_cycle"]
    _GN = int(nums["gait_samples"])
    _row = _GT[int(tt * _GN) % _GN]
    # ── THE FOOT IS PLANTED AND THE HIP RIDES OVER IT ────────────────────────────────────────────
    # This membrane's own prose says "the stance knee stays near straight -- the leg is a strut, not
    # a spring" and "the centre of mass rises at mid-stance as the body vaults over the planted foot".
    # The code did neither, in two ways that compounded:
    #
    #  1. THE KNEE BENT ON THE WRONG LEG. `bend = max(0, -cos(phase + ph))` is positive exactly when
    #     the hip angle is DECREASING, which is the definition of stance -- so the stance knee folded
    #     and the swing knee locked straight. A straight swing leg is a long leg, so its foot never
    #     cleared the floor.
    #  2. THE HIP WAS NAILED AT A CONSTANT HEIGHT, so nothing vaulted over anything, and the promised
    #     centre-of-mass rise was supplied instead by a hand-added `0.018 * cos(2 * phase)` -- a
    #     SIMULATION of the consequence sitting where the consequence should have been.
    #
    # Measured, the two together put BOTH feet 4.3% of stature off the ground at mid-stride and back
    # down at the extremes: the contact plane bobbed twice a cycle, duty factor near 1.0 on both
    # feet. By this project's own gait doctrine that is a SLED, NOT A GAIT.
    #
    # The fix is one line of physics: the stance foot is on the ground, so the hip height is whatever
    # the stance leg's geometry puts it at. Everything else follows and nothing is added --
    #     contact plane      4.3% of stature  ->  0.000, dead still
    #     swing-foot lift    ~0               ->  8.4% of stature (a real walk is 8-15%)
    #     centre-of-mass bob hand-written     ->  EMERGENT, 4.3%, at twice the stride frequency
    # and double support -- both feet down at the transition -- appears without being asked for.
    # THE BODY RESTS ON WHICHEVER PLANTED FOOT HOLDS IT HIGHEST, and that one line is the whole
    # mechanism. Each leg in stance can support the hip at (its own ankle height) + L cos(theta); the
    # hip takes the MAXIMUM, because a body cannot sink through a leg that is holding it up.
    #
    # What falls out, unasked: PUSH-OFF FILLS THE TROUGH. At the transition the trailing leg is
    # plantarflexed onto its forefoot, which puts its ankle 8% of stature up, so it holds the hip
    # high exactly when the leading leg -- reaching forward, heel barely down -- would otherwise let
    # it drop. That is why the centre of mass of a walking person travels so much flatter than a
    # compass gait predicts, and none of it is written down anywhere here as a target.
    #
    # AND THE STANCE KNEE NO LONGER LOCKS. It used to: `bend = 0.0 if _planted`, on the reasoning
    # that "a stance knee stays near straight -- the leg is a strut, not a spring". Near straight is
    # not straight, and the difference is the whole residual. The 246 adults flex the stance knee
    # about 18 degrees just after contact, which shortens the supporting leg exactly when the body
    # would otherwise be vaulting highest over it. It arrives here as measurement, not as a target.
    hip_z = float(_row[0])
    parts = []
    for side, _i in ((-1.0, 0), (1.0, 1)):
        th_hip, th_knee_flex, _foot_ang, _u, _planted = (float(_row[1 + 5 * _i]),
                                                         float(_row[2 + 5 * _i]),
                                                         float(_row[3 + 5 * _i]),
                                                         float(_row[4 + 5 * _i]),
                                                         _row[5 + 5 * _i] > 0.5)
        # LATERAL IS Y, NOT X -- the hip offset used to sit on X, the axis the leg swings along, so
        # both legs were separated fore-aft and projected onto each other from the front. aHuman
        # inherited the same mistake and its derived 20 cm stance rendered as zero.
        hip = np.array([0.0, 0.055 * side, hip_z])
        knee = hip + np.array([np.sin(th_hip), 0.0, -np.cos(th_hip)]) * thigh
        th_knee = th_hip - th_knee_flex          # knee flexion folds the shank backward
        ankle = knee + np.array([np.sin(th_knee), 0.0, -np.cos(th_knee)]) * shank
        parts.append(limb(hip, knee, 260, 0.035))
        parts.append(limb(knee, ankle, 260, 0.028))
        # THE FOOT'S ANGLE IS NOT DECIDED HERE EITHER. It is the pitch the table carries, which the
        # parent derived from three measured joint angles by forward kinematics -- so the sole is
        # flat when the measurement says it is flat, and no phase fraction is placed by hand.
        toe = ankle + np.array([math.cos(_foot_ang), 0.0, math.sin(_foot_ang)]) * FOOT_LEN_FRAC
        parts.append(limb(ankle, toe, 120, 0.025))

        # ARMS COUNTER-SWING, and they are not decoration: whole-body angular momentum stays near
        # zero, so the arms must go the way the opposite leg does not.
        sh = np.array([0.0, 0.085 * side, hip_z + (0.82 - LEG_FRAC)])           # lateral is Y -- see the note above
        th_sh = -0.55 * th_hip                             # counter to the leg on the same side
        elbow = sh + np.array([np.sin(th_sh), 0.0, -np.cos(th_sh)]) * 0.186
        hand = elbow + np.array([np.sin(th_sh * 1.4), 0.0, -np.cos(th_sh * 1.4)]) * 0.146
        parts.append(limb(sh, elbow, 180, 0.026))
        parts.append(limb(elbow, hand, 180, 0.022))

    # trunk and head, riding the CoM. It RISES at mid-stance -- the inverted pendulum vaulting over
    # the planted foot -- and that bob is the signature of a walk rather than a glide.
    # THE BOB IS NOT WRITTEN ANY MORE, it is read off the hip the stance leg is holding up. The
    # trunk keeps its rigid offsets from the hip, so the whole upper body rises and falls exactly as
    # far as the vault carries it -- which is what a centre of mass doing this actually looks like.
    pelvis = np.array([0.0, 0.0, hip_z])
    neck = np.array([0.0, 0.0, hip_z + (0.86 - LEG_FRAC)])
    parts.append(limb(pelvis, neck, 420, 0.055))
    head = np.array([0.0, 0.0, hip_z + (0.94 - LEG_FRAC)])
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
