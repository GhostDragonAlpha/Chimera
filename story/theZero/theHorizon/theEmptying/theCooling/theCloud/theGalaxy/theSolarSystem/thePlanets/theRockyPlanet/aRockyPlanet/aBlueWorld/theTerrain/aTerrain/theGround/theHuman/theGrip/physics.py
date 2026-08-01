"""theGrip -- close until you cannot, and let the object decide the rest.

THE EDGE. theHuman published a body and a world: a mass, a gravity, a suit. What it did not publish
is what happens when that body picks something up. This chapter is that -- and it is deliberately
NOT a set of hand poses. The operator's law, verbatim:

    COMMAND THE PROCESS AND ITS STOP CONDITION, NEVER THE FINAL POSITION. The hand does not aim
    its fingers at coordinates -- it CLOSES UNTIL IT CANNOT, and the OBJECT decides where they
    land. So one GRAB serves a pin and a bowling ball. POSITIONS ARE OUTPUTS.

So there is no grasp pose anywhere in this file. There is one inequality, and everything else is
what the objects do to it.

WHETHER IT HOLDS IS FRICTION, NOT STRENGTH. An object pinched between two pads does not fall while

        n * mu * F_grip  >=  m * g

-- n opposing contacts, each able to return mu times the force pressed into it, against the weight
hanging off them. Read it once and the chapter is already implied: the squeeze you need scales with
the object's MASS and inversely with its SURFACE, so a slippery light thing is HARDER than a grippy
heavy one; nothing in it mentions a finger, a pose, or a hand; and the only body-side term is the
CEILING on F_grip, which is why "can I hold this" has an answer before any geometry exists.

MU IS NOT A CONSTANT, AND THAT IS THE WHOLE SECOND HALF. Carre et al. (2017) fitted every one of
their finger-surface conditions with a POWER LAW, `COF = a * N^b`, and Zhang & Mak (1999) measured
the same sign independently. It follows from contact mechanics rather than from a fit: a soft pad
pressed on a flat makes a Hertzian contact of area A ~ N^(2/3), friction from adhesion is the shear
strength times that area, so

        mu = F_fric / N = tau * A / N ~ N^(-1/3)

-- the exponent is DERIVED, not chosen. Put that back into the inequality and the required grip
force stops being linear in the load:

        F_min = [ W / (n * mu_ref) ]^(3/2) / sqrt(F_ref)

A three-halves power. Twice the weight needs 2.83x the squeeze, not 2x. That is a prediction this
chapter was never fitted to, and it is why a heavy slippery object feels so much worse than its
weight says it should.

IT ALSO EATS THE SAFETY MARGIN. Squeezing 25% harder does not buy 25% more friction, because the
extra squeeze lowers mu: capacity goes as F^(2/3), so a 25% force margin is a 16% capacity margin.
The margin you feel is not the margin you get.

AND IT HAS A REGIME, DECLARED. The power law was measured between about 0.25 N and 2.2 N -- the
precision-grip range. Above that the pad flattens and the area stops growing, so mu levels off; the
law is CLAMPED at the top of its measured range rather than extrapolated. Below ~0.12 N it is
clamped at the highest mu anyone measured on skin. Extrapolating a power law past its data is how
you get 30 for a coefficient of friction, which is what the unclamped version does to the pin.

THE STOP CONDITION IS TACTILE, AND IT IS TOO SLOW TO CLOSE THE HAND. From slip onset to the motor
correction is 74 +- 9 ms (Johansson & Westling 1987). A grasp is a stop-condition process, so ask
what it would cost to run the CLOSING that way: the pads would have to travel less than the pad's
own compliance per decision, ~1 mm, and closing a 0.3 m aperture 1 mm at a time is 300 decisions --
about 22 seconds. Real grasps take under a second. THEREFORE THE APPROACH CANNOT BE FEEDBACK; it is
feed-forward, and the tactile loop only CORRECTS. That is exactly what the Johansson school found
(sensorimotor memory: the first lift of an object whose weight secretly changed is clumsy, and the
second is not), and this chapter arrives at it from a latency and a millimetre.

WHAT THIS CHAPTER DOES NOT OWN. Segment lengths, degrees of freedom, workspace, lever geometry and
the maximum span are theHand's -- a sibling, unread. The split shows up in the numbers rather than
just in the prose: the force law alone says a fingertip pinch could hold 8.4 kg, and at the density
of water that is a 25 cm sphere, which no hand can span. FORCE gives the lower bound on which grip
will serve; GEOMETRY gives the upper bound. Neither membrane can answer alone, and that is the
correct shape for two siblings.

WHAT IT CONSUMES from theHuman: mass_kg, g, height_m, duration_s, suit_mass_kg, consumables_kg,
suit_needs_pressure_shell, skin_albedo_rgb, S_earth.

Contained in theHuman. Its movie is ONE GRASP: five objects, one command, five answers.

SOURCES -- every typed number below is one of these or is derived from them.
  [ZM99]  Zhang M, Mak AFT (1999). In vivo friction properties of human skin. Prosthet Orthot Int
          23:135-141. 10 subjects, 6 sites, 5 materials, 100 g load, controlled 20-24 C / 55-65% RH.
          Local copy: research_references/human/skin_friction/zhang_mak1999_skin_friction_tables.html
  [TL75]  Taylor MM, Lederman SJ (1975), as reported in [ZM99]: fingertip-aluminium mu = 0.6,
          falling by at least 75% when soaped.
  [W89]   Wolfram LJ (1989), as reported in [ZM99]: skin mu generally 0.1-1.3.
  [CA17]  Carre MJ, Tan SK, Mylon PT, Lewis R (2017). Influence of medical gloves on fingerpad
          friction and feel. Wear 376-7:324-328. Power-law COF = a*N^b for every condition; gloved
          beat bare on DRY steel and glass, bare beat gloved on WET glass.
          Local copy: research_references/human/grip/carre2017_glove_friction_steel.pdf
  [MA85]  Mathiowetz V et al. (1985). Grip and pinch strength: normative data for adults. Arch Phys
          Med Rehabil 66:69-72. 310 M / 328 F, Jamar dynamometer, ASHT positioning.
          Local copy: research_references/human/grip/mathiowetz_grip_pinch_norms_adult.pdf
  [NH]    NHANES 2011-2012 (MGX_G) and 2013-2014 (MGX_H) muscle-strength files, 14,984 people with
          a valid best-of-six grip. US Government, public domain. Used ONLY as an independent check
          on [MA85], never as its replacement.
  [JW84]  Johansson RS, Westling G (1984). Roles of glabrous skin receptors and sensorimotor memory
          ... Exp Brain Res 56:550-564. Defines the SAFETY MARGIN as employed grip force minus the
          measured minimum; initial force adaptation ~0.1 s, slip-related adjustment 0.06-0.08 s.
  [JW87]  Johansson RS, Westling G (1987). Signals in tactile afferents ... Exp Brain Res 66:141-154.
          Slip onset to force-ratio change: 74 +- 9 ms.
  [USBC]  USBC/World Bowling Equipment Specifications Manual: ball mass <= 16 lb, diameter 8.500 to
          8.595 in for balls of 13 lb and over.

NOT SOURCED, AND SAID SO PLAINLY -- four numbers in this file are weaker than the rest:
  1. THE SAFETY MARGIN RANGE, 10-40%. [JW84] defines the margin and measures it, but its abstract
     states no percentage and the full text was not reachable from here; 10-40% is the figure the
     manipulation literature repeats second-hand. It is therefore carried as a FREE range with the
     midpoint as its default -- which is the honest place for a number like that, not a constant.
  2. THE FINGERPAD'S COMPLIANT TRAVEL, ~1 mm, used only in the feed-forward argument. It is an
     order of magnitude, and the conclusion survives a factor of several either way.
  3. BOOT-SOLE-ON-ROCK MU. Elkington et al. (2024) is downloaded and is about exactly this, but its
     coefficients live in tables the local HTML does not contain. So the mag-boot row is reported
     ACROSS a mu range instead of at one value, and is a parameterisation, not a prediction.
  4. GRIP ENDURANCE. Everything here is maximum VOLUNTARY force. How long it can be held is not
     traced at all, and a grip you cannot sustain is a grip you do not have.
"""
from __future__ import annotations

import math

import numpy as np

# ── MEASURED: SKIN, AND WHAT IT TOUCHES. All from [ZM99] unless marked. Dimensionless.
MU_PALM = 0.62              # palm of the hand, the highest of six sites [ZM99]; SD 0.22
MU_PALM_SD = 0.22
MU_SKIN_MEAN = 0.46         # all sites x all materials, n=10 subjects [ZM99]; SD 0.15
MU_SILICONE = 0.61          # skin on silicone, the grippiest material tested [ZM99]
MU_NYLON = 0.37             # skin on nylon, the slickest material tested [ZM99]
MU_METAL = 0.60             # fingertip on aluminium [TL75]
MU_SOAPED = 0.15            # [TL75]: soaped, "dropped by at least 75%" -> 0.60 * 0.25
MU_MAX_MEASURED = 1.26      # highest single measurement in [ZM99]; [W89] puts skin's ceiling at 1.3
MU_REF_LOAD_N = 0.981       # the 100 g load [ZM99] measured at, and ~the 1 N [CA17] normalises to

# ── THE LOAD DEPENDENCE. The exponent is DERIVED (Hertz area ~ N^(2/3), adhesive friction ~ area),
# and [CA17] found a power law of this form for every finger-surface condition it tested.
HERTZ_EXPONENT = -1.0 / 3.0
# THE REGIME, and it is not decoration. [ZM99] loaded 0.245-0.981 N; [CA17]'s reported datasets ran
# to 2.17 N. Above that the pad is flattening and the area stops growing with load, so the law is
# CLAMPED rather than extrapolated. Unclamped it hands a pin a coefficient of friction of 30.
HERTZ_MAX_N = 2.17

# ── THE TACTILE LOOP. This is the stop condition, and therefore this membrane's clock.
SLIP_RESPONSE_S = 0.074     # slip onset -> grip-force-ratio change, 74 +- 9 ms [JW87]
SLIP_RESPONSE_SD_S = 0.009
PRELOAD_S = 0.10            # contact -> load starts to rise, "approximately 0.1 s" [JW84]
LOAD_S = 0.10               # load phase to lift-off [JW84]
PAD_TRAVEL_M = 0.001        # NOT SOURCED -- order of magnitude, feed-forward argument only

# ── THE CEILING. [MA85] Table 2 and Tables 3-5, MEN aged 30-34, dominant (right) hand, in pounds
# force. That cell and not another: theHuman's body is the ANSUR-II male median and ANSUR-II's male
# mean age is 30.2 years, so the demographic is matched rather than chosen.
LBF_N = 4.4482216152605
GRIP_MEN_30_34_LB = 121.8   # Jamar power grip, dominant hand   [MA85] SD 22.4, range 70-170
GRIP_MEN_30_34_LB_OFF = 110.4   # non-dominant hand
TIP_PINCH_LB = 17.6         # thumb-index tip pinch, the pin grip [MA85]
KEY_PINCH_LB = 26.4         # lateral / key pinch [MA85]
PALMAR_PINCH_LB = 24.7      # palmar, three-jaw chuck [MA85]
# THE INDEPENDENT CHECK, computed from [NH] before it was written down here: best-of-six grip over
# 14,984 people of both sexes aged 6+. Median 31.4 kgf, p95 55.6 kgf, max 85.8 kgf.
NHANES_MEDIAN_KGF = 31.45
NHANES_P95_KGF = 55.65
NHANES_N = 14984
KGF_N = 9.80665

# ── MATERIALS AND OBJECTS. Bulk densities are the standard values for the named material; each
# object's grasp diameter is its own dimension where it has one, and otherwise the sphere-equivalent
# of its mass at that density -- derived, so that changing a mass moves a size.
RHO_STEEL = 7850.0          # carbon steel
RHO_WATER = 1000.0
BOWLING_MASS_KG = 16.0 * 0.45359237     # [USBC] maximum sanctioned ball mass, 16 lb
BOWLING_DIAM_M = 8.500 * 0.0254         # [USBC] minimum diameter for balls of 13 lb and over
PIN_LENGTH_M = 0.030        # a dressmaker's pin: its mass is DERIVED from these and RHO_STEEL
PIN_DIAM_M = 0.0006

G_EARTH = 9.80665           # for the gravity dial, and nothing else

FREE = {
    # HOW MUCH MORE THAN THE MINIMUM. [JW84] defines this quantity and measures it per subject; the
    # 10-40% band is what the later literature repeats, and no primary percentage was reachable from
    # here. So it is FREE over the reported band, defaulting to its midpoint -- and a midpoint is
    # declared as a midpoint, not dressed up as a measurement.
    "safety_margin": {"lo": 0.10, "hi": 0.40, "default": 0.25,
                      "label": "safety margin over the slip minimum", "unit": "ratio",
                      "local": "how paranoid this body is, in units of the force it needs anyway"},
    # HOW LONG THE APPROACH TAKES, in tactile loop times. The approach is feed-forward (see the
    # docstring), so its speed is NOT set by the stop condition and this membrane cannot derive it;
    # the muscle and the hand set it. Free, and its default makes the approach as long as the grasp
    # it sets up -- a symmetry, stated as one, not a law.
    "close_loops": {"lo": 1.0, "hi": 20.0, "default": 4.0,
                    "label": "approach length", "unit": "tactile loop times",
                    "local": "how fast the pads travel before anything has been touched"},
}


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE LAW -- three functions, and the whole chapter is in them
# ════════════════════════════════════════════════════════════════════════════════════════════════
def mu_at(F_N, mu_ref=MU_PALM, mu_ceiling=MU_MAX_MEASURED):
    """THE COEFFICIENT OF FRICTION AT A GIVEN SQUEEZE, which is not a constant.

    mu = mu_ref * (F / F_ref)^(-1/3), clamped at both ends of the range anyone measured.

    The exponent is Hertz: a soft pad on a flat makes contact over an area ~ N^(2/3), adhesive
    friction is a shear strength times that area, so mu = tau*A/N ~ N^(-1/3). [CA17] found a power
    law of exactly this form for bare and gloved fingers on steel and on glass, wet and dry.

    THE CLAMPS ARE THE POINT, not tidying-up. A power law asked for its value outside its data is a
    guess wearing an equation's clothes: unclamped, this function gives a dressmaker's pin -- held
    with about 0.2 mN -- a coefficient of friction of THIRTY. Clamped, it says 1.26, which is the
    largest number anyone has ever measured on skin."""
    F = max(float(F_N), 1e-12)
    mu = float(mu_ref) * (min(F, HERTZ_MAX_N) / MU_REF_LOAD_N) ** HERTZ_EXPONENT
    return min(mu, float(mu_ceiling))


def grip_needed(weight_N, mu_ref, n_contacts=2):
    """THE MINIMUM SQUEEZE THAT DOES NOT DROP IT. Solves n * mu(F) * F = W for F.

    In the Hertz regime mu ~ F^(-1/3), so capacity ~ F^(2/3) and the equation closes in one line:

        F = [ W / (n * mu_ref) ]^(3/2) / sqrt(F_ref)

    THREE HALVES, not one. Above the regime top mu is flat and it reverts to the schoolbook
    F = W/(n*mu); below the low-load clamp likewise. Returns (F_N, mu_effective).

    Nothing here knows what a finger is. n is however many opposing surfaces share the squeeze: two
    for a pinch between thumb and finger, one for a boot clamped to a wall."""
    W = max(float(weight_N), 0.0)
    n = float(n_contacts)
    if W <= 0.0:
        return 0.0, float(mu_ref)
    F = (W / (n * float(mu_ref))) ** 1.5 / math.sqrt(MU_REF_LOAD_N)
    if F > HERTZ_MAX_N:                      # pad flattened: mu has stopped falling
        mu = mu_at(HERTZ_MAX_N, mu_ref)
        return W / (n * mu), mu
    mu = mu_at(F, mu_ref)
    if mu >= MU_MAX_MEASURED - 1e-12:        # below the low-load clamp: mu has stopped rising
        mu = MU_MAX_MEASURED
        return W / (n * mu), mu
    return F, mu


def gravity_that_drops_it(mass_kg, mu_ref, ceiling_N, margin, n_contacts=2):
    """THE GRAVITY AT WHICH THIS OBJECT LEAVES YOUR HAND -- the same law read backwards.

    Everything above scales with g, and nothing else in the law does: mu is a property of two
    surfaces and the ceiling is a property of a body. So each object has a gravity at which the
    force it needs crosses the force the hand has, and that number is a fact about the pair. It
    predicts play on worlds this was never run on, which is the only reason to compute it."""
    lo, hi = 1e-6, 1.0e4
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        F, _mu = grip_needed(float(mass_kg) * mid, mu_ref, n_contacts)
        if F * (1.0 + float(margin)) <= float(ceiling_N):
            lo = mid
        else:
            hi = mid
    return lo


def derive(parent, free):
    if parent is None or "mass_kg" not in parent or "g" not in parent:
        raise ValueError("theGrip requires theHuman as its parent")
    free = free or {}
    margin = float(free.get("safety_margin", FREE["safety_margin"]["default"]))
    close_loops = float(free.get("close_loops", FREE["close_loops"]["default"]))

    m_body = float(parent["mass_kg"])
    g = float(parent["g"])
    h = float(parent["height_m"])
    suit_kg = float(parent.get("suit_mass_kg", 0.0))
    ration_kg = float(parent.get("consumables_kg", 0.0))
    pressurised = bool(parent.get("suit_needs_pressure_shell", False))

    # ── THE CEILING, in newtons. Measured, not scaled: theHuman IS the ANSUR-II male median and
    # [MA85]'s men-30-34 cell is the mean of a comparable population, so the median body takes the
    # population mean without an allometric transfer. The transfer LAW (force ~ mass^(2/3), because
    # muscle force goes with cross-section) is published below for a body that is NOT the median,
    # but it is not applied here and no reference mass is claimed for [MA85]'s subjects.
    F_power = GRIP_MEN_30_34_LB * LBF_N
    F_power_off = GRIP_MEN_30_34_LB_OFF * LBF_N
    F_tip = TIP_PINCH_LB * LBF_N
    F_key = KEY_PINCH_LB * LBF_N
    F_palmar = PALMAR_PINCH_LB * LBF_N
    nh_p95_N = NHANES_P95_KGF * KGF_N

    # ── WHERE THE THREE-HALVES LAW ACTUALLY FIRES, and it is a much smaller window than it sounds.
    # mu only slides between its two clamps, so the superlinear law owns a band of MASS and nothing
    # outside it. Converting the two force clamps into masses at the palm's mu is two lines, and it
    # is the honest scope of everything the docstring boasts about above.
    mu_hi_load = mu_at(HERTZ_MAX_N)
    F_low_clamp = MU_REF_LOAD_N * (MU_MAX_MEASURED / MU_PALM) ** (1.0 / HERTZ_EXPONENT)
    m_regime_hi = 2.0 * mu_hi_load * HERTZ_MAX_N / g
    m_regime_lo = 2.0 * MU_MAX_MEASURED * F_low_clamp / g
    m_demo = math.sqrt(m_regime_lo * m_regime_hi)          # the middle of the band, in log
    F_demo, _mu_demo = grip_needed(m_demo * g, MU_PALM, 2)
    F_demo_linear = m_demo * g / (2.0 * MU_PALM)           # what the schoolbook law would say

    # ── THE OBJECTS. Masses are sourced or derived; nothing on this list was invented to make a
    # point. The SURFACE is what varies as hard as the mass does, which is the argument.
    pin_kg = math.pi * (PIN_DIAM_M / 2.0) ** 2 * PIN_LENGTH_M * RHO_STEEL
    tool_kg = 1.0                                  # one kilogram: a unit, not a guess
    tool_d = (6.0 * tool_kg / (math.pi * RHO_STEEL)) ** (1.0 / 3.0)
    ration_d = (6.0 * max(ration_kg, 1e-9) / (math.pi * RHO_WATER)) ** (1.0 / 3.0)

    spec = [
        # name                        mass_kg     mu            diameter_m     n  surface
        ("a steel pin",               pin_kg,     MU_METAL,     PIN_DIAM_M,    2, "polished steel"),
        ("a one-kilogram hand tool",  tool_kg,    MU_SILICONE,  tool_d,        2, "silicone grip"),
        ("a full water ration",       ration_kg,  MU_METAL,     ration_d,      2, "bare aluminium"),
        ("the same ration, soaped",   ration_kg,  MU_SOAPED,    ration_d,      2, "soaped aluminium"),
        ("a regulation bowling ball", BOWLING_MASS_KG, MU_NYLON, BOWLING_DIAM_M, 2, "polished coverstock"),
        ("the pressure suit itself",  suit_kg,    MU_SKIN_MEAN, 0.0,           2, "suit fabric"),
    ]
    # THE GRIP LADDER, weakest first. The FORCE law picks the weakest grip that can hold the thing;
    # theHand's geometry is what rules out the ones that are too big or too small to fit. Two
    # membranes, two bounds, and this one only owns the lower.
    ladder = [("tip pinch", F_tip), ("palmar pinch", F_palmar), ("key pinch", F_key),
              ("power grip", F_power), ("two-handed power grip", 2.0 * F_power)]

    objects = []
    for name, m, mu_ref, d, n, surface in spec:
        W = m * g
        F_min, mu_eff = grip_needed(W, mu_ref, n)
        F_app = F_min * (1.0 + margin)
        F_min_e, _ = grip_needed(m * G_EARTH, mu_ref, n)
        need = next((lab for lab, cap in ladder if F_app <= cap), None)
        need_e = next((lab for lab, cap in ladder if F_min_e * (1.0 + margin) <= cap), None)
        g_pinch = gravity_that_drops_it(m, mu_ref, F_tip, margin, n)
        g_power = gravity_that_drops_it(m, mu_ref, F_power, margin, n)
        objects.append({
            "name": name, "surface": surface,
            "mass_kg": m, "diameter_m": d, "friction_ratio": mu_ref, "contacts_count": n,
            "weight_N": W,
            "grip_min_N": F_min,             # the slip threshold
            "grip_applied_N": F_app,         # ... plus the measured margin
            "friction_effective_ratio": mu_eff,   # what mu actually is at that squeeze
            "grip_per_weight_ratio": F_min / max(W, 1e-12),
            "grip_min_earth_N": F_min_e,
            "earth_over_here_ratio": F_min_e / max(F_min, 1e-12),
            "grip_needed": need or "beyond two hands",
            "grip_needed_on_earth": need_e or "beyond two hands",
            "held_in_a_pinch": bool(F_app <= F_tip),
            "held_at_all": need is not None,
            # is mu still sliding at this squeeze, or has it hit one of its clamps?
            "in_hertz_regime": bool(F_low_clamp < F_min < HERTZ_MAX_N),
            "gravity_that_drops_it_from_a_pinch_m_s2": g_pinch,
            "gravity_that_drops_it_from_a_power_grip_m_s2": g_power,
            # A SEARCH THAT HIT ITS OWN CEILING IS NOT A RESULT. The pin never leaves the fingers at
            # any gravity this bisection covers, and reporting 10,000 m/s2 as if it were an answer is
            # exactly the kind of number that gets quoted later as a fact.
            "gravity_search_hit_the_cap": bool(g_pinch >= 0.999e4 or g_power >= 0.999e4),
        })

    # ── THE MAG-BOOT. The stub asked whether the adhesion beats the body weight it holds against the
    # normal; it is the SAME inequality with the object set to the body and n = 1, because a sole is
    # one surface and gravity now runs ALONG it. mu for a boot sole on rock is not sourced here, so
    # this is reported across the skin range rather than at a value -- a parameterisation, said so.
    W_body = m_body * g
    boot = {mu: W_body / mu for mu in (MU_NYLON, MU_SKIN_MEAN, MU_PALM)}

    # ── THE FEED-FORWARD RESULT. What a purely closed-loop close would cost.
    aperture_m = 1.4 * BOWLING_DIAM_M          # the pads must start wider than the widest object
    loops_by_feel = aperture_m / PAD_TRAVEL_M
    close_s = close_loops * SLIP_RESPONSE_S
    grasp_s = SLIP_RESPONSE_S + PRELOAD_S + LOAD_S + SLIP_RESPONSE_S

    return {
        # ITS REAL SIZE: the widest thing on the list -- because a grip has no size of its own. It
        # is a process, and the size of a process is the size of what it closes on. The chapter's
        # thesis, stated as a choice of unit.
        "extent_m": max(o["diameter_m"] for o in objects),
        # ITS OWN DURATION: one grasp, approach through secure hold. Set by the TACTILE LOOP and by
        # nothing else -- so it does NOT move when gravity does. Only the forces do.
        "duration_s": close_s + grasp_s,

        # ── the law
        "friction_palm_ratio": MU_PALM,
        "friction_palm_sd_ratio": MU_PALM_SD,
        "friction_skin_mean_ratio": MU_SKIN_MEAN,
        "friction_silicone_ratio": MU_SILICONE,
        "friction_nylon_ratio": MU_NYLON,
        "friction_metal_ratio": MU_METAL,
        "friction_soaped_ratio": MU_SOAPED,
        "friction_ceiling_ratio": MU_MAX_MEASURED,
        "friction_reference_load_N": MU_REF_LOAD_N,
        "hertz_exponent": HERTZ_EXPONENT,
        "hertz_regime_max_N": HERTZ_MAX_N,
        "friction_floor_ratio": mu_hi_load,              # mu once the pad has flattened
        "grip_scales_as_weight_exponent": 1.5,           # DERIVED, and the chapter's best surprise
        # ... AND THE BAND IT IS TRUE OVER. Outside these two masses mu is clamped and the exponent
        # falls back to 1: the three-halves law governs the LIGHT end -- a pen, a switch, a sample
        # vial -- and every object on this chapter's own table is heavier than that. Said here in
        # numbers rather than left for a reader to discover the boast does not cover the table.
        "hertz_regime_min_mass_kg": m_regime_lo,
        "hertz_regime_max_mass_kg": m_regime_hi,
        "hertz_demo_mass_kg": m_demo,
        "hertz_demo_grip_N": F_demo,
        "hertz_demo_grip_if_mu_were_constant_N": F_demo_linear,
        "hertz_demo_over_constant_mu_ratio": F_demo / max(F_demo_linear, 1e-12),
        "gravity_search_cap_m_s2": 1.0e4,
        # the margin, and how much of it survives its own effect on mu
        "safety_margin": margin,
        "safety_margin_min_ratio": FREE["safety_margin"]["lo"],
        "safety_margin_max_ratio": FREE["safety_margin"]["hi"],
        "margin_capacity_gain_ratio": (1.0 + margin) ** (2.0 / 3.0),
        "margin_capacity_gain_above_regime_ratio": 1.0 + margin,
        "margin_lost_to_its_own_squeeze_ratio":
            1.0 - ((1.0 + margin) ** (2.0 / 3.0) - 1.0) / margin,

        # ── the clock
        "tactile_loop_s": SLIP_RESPONSE_S,
        "tactile_loop_sd_s": SLIP_RESPONSE_SD_S,
        "preload_s": PRELOAD_S,
        "load_s": LOAD_S,
        "grasp_event_s": grasp_s,
        "grasp_in_loops_count": grasp_s / SLIP_RESPONSE_S,
        "approach_s": close_s,
        "approach_loops_count": close_loops,
        "aperture_m": aperture_m,
        "pad_travel_m": PAD_TRAVEL_M,
        "close_by_feel_alone_s": loops_by_feel * SLIP_RESPONSE_S,
        "close_by_feel_alone_loops_count": loops_by_feel,
        "approach_must_be_feedforward": bool(loops_by_feel * SLIP_RESPONSE_S > close_s),

        # ── the ceiling
        "max_grip_N": F_power,
        "max_grip_off_hand_N": F_power_off,
        "tip_pinch_max_N": F_tip,
        "key_pinch_max_N": F_key,
        "palmar_pinch_max_N": F_palmar,
        "two_handed_max_N": 2.0 * F_power,
        "grip_over_body_weight_ratio": F_power / max(m_body * g, 1e-9),
        "grip_norm_source": "Mathiowetz 1985 men 30-34 dominant hand; ANSUR-II male mean age 30.2",
        "grip_scaling_exponent": 2.0 / 3.0,     # force ~ mass^(2/3): stated, NOT applied here
        "grip_scaling_is_applied": False,
        # the independent check, and it is not the same instrument
        "nhanes_median_N": NHANES_MEDIAN_KGF * KGF_N,
        "nhanes_p95_N": nh_p95_N,
        "nhanes_people_count": NHANES_N,
        "norm_over_nhanes_p95_ratio": F_power / nh_p95_N,
        # the biggest thing the FORCE law allows -- and the sphere it would be, which no hand spans
        "pinch_mass_ceiling_kg": 2.0 * mu_at(HERTZ_MAX_N) * F_tip / ((1.0 + margin) * g),
        "power_mass_ceiling_kg": 2.0 * mu_at(HERTZ_MAX_N) * F_power / ((1.0 + margin) * g),
        "pinch_ceiling_as_water_sphere_m": (
            6.0 * (2.0 * mu_at(HERTZ_MAX_N) * F_tip / ((1.0 + margin) * g))
            / (math.pi * RHO_WATER)) ** (1.0 / 3.0),

        # ── the mag-boot: the same inequality, one contact, the object is the body
        "body_weight_N": W_body,
        "boot_clamp_at_mu_037_N": boot[MU_NYLON],
        "boot_clamp_at_mu_046_N": boot[MU_SKIN_MEAN],
        "boot_clamp_at_mu_062_N": boot[MU_PALM],
        "boot_clamp_over_body_weight_ratio": 1.0 / MU_SKIN_MEAN,
        "boot_mu_is_sourced": False,

        # ── the suit, read from the parent rather than assumed
        "glove_is_pressurised": pressurised,
        "pressurised_glove_penalty_traced": False,
        "glove_friction_source": "Carre 2017: gloved beats bare on DRY steel and glass; bare beats "
                                 "gloved on WET glass. Values at 1 N are figure-only in the local "
                                 "copy, so the numbers above are BARE-skin friction throughout.",

        # ── the table
        "objects": objects,
        "objects_count": len(objects),
        "mass_span_ratio": max(o["mass_kg"] for o in objects) / min(o["mass_kg"] for o in objects),
        "friction_span_ratio": (max(o["friction_ratio"] for o in objects)
                                / min(o["friction_ratio"] for o in objects)),
        "objects_in_hertz_regime_count": sum(1 for o in objects if o["in_hertz_regime"]),
        "g_earth_m_s2": G_EARTH,

        # ── carried on, so a child never has to reach past me
        "g": g,
        "mass_kg": m_body,
        "height_m": h,
        "S_earth": float(parent.get("S_earth", 1.0)),
        "skin_albedo_rgb": list(parent.get("skin_albedo_rgb", [0.65, 0.45, 0.36])),
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- one command, four objects, four answers
# ════════════════════════════════════════════════════════════════════════════════════════════════
def emit(nums, t=1.0):
    """FOUR GRASPS RUNNING AT ONCE ON THE SAME COMMAND, and the objects decide what happens.

    LOCAL UNITS: 1.0 is the widest object on the list (a regulation bowling ball). +X across the
    row, +Z up. Four stations, left to right in order of the squeeze they need.

    WHAT IS BEING DRAWN, and why each part is the law rather than an illustration of it:

      THE PADS CLOSE AT THE SAME RATE AT EVERY STATION. Nothing tells them where to stop. They stop
      where the OBJECT is -- so the ball stops them early and the pin stops them late, and the four
      contact moments are four different times inside one movie, from one command. That is the
      operator's law: the stop comes from the object's size, never from a keyframe.

      THEN THE FORCE RISES, and the pad presses INTO the object by an amount read straight from
      grip_applied_N over the grip's ceiling. The pin barely dimples. The soaped ration is crushed.
      Same command again; the object set the force.

      THE TWO BARS UNDER EACH STATION are grip_min_N and grip_applied_N against the same ceiling, so
      the GAP between them IS the safety margin and the height of the taller one is how close to the
      ceiling the object has driven you. When it overtops the ceiling line the object falls, and it
      falls at the g theHuman published -- not at a chosen rate.

      THE OBJECT'S COLOUR IS ITS FRICTION. Slick is pale and cold, grippy is dark and warm; that is
      a measurement of mu and not a decision about how a bowling ball ought to look.

    ONE DECLARED EXAGGERATION, and it scales what exists rather than minting anything. The real
    diameters span 360:1 -- a pin beside a bowling ball is a third of a pixel. The drawn radii are
    on a LOG remap of that true range, so the ordering and every contact moment are real and only
    the ratio is compressed. Every circle on screen is an object in the published table.
    """
    from matter import blank, lit, SOLID, GLOW, AR, AG, AB

    u = min(max(float(t), 0.0), 1.0)

    # EVERY OBJECT THAT HAS A GRASP DIAMETER GETS A STATION -- the table is not curated for the
    # picture. Sorted by the squeeze each one needs, so the row reads left to right as the law does.
    objs = sorted([o for o in nums["objects"] if o["diameter_m"] > 0.0],
                  key=lambda o: o["grip_applied_N"])
    n_st = len(objs)

    ceiling = float(nums["tip_pinch_max_N"])         # these are pinches: two pads, two fingers
    g = float(nums["g"])
    d = [float(o["diameter_m"]) for o in objs]
    d_lo, d_hi = min(d), max(d)
    span = math.log10(d_hi / d_lo) if d_hi > d_lo else 1.0

    # phase boundaries, in fractions of duration_s, taken from the published clock
    T = float(nums["duration_s"])
    f_close = float(nums["approach_s"]) / T
    f_load = f_close + (float(nums["preload_s"]) + float(nums["load_s"])) / T

    A0 = 0.30                                        # the aperture, in local units
    PAD_H, PAD_T = 0.150, 0.050
    STEP = 0.60
    x0 = -STEP * (n_st - 1) / 2.0
    R_MIN, R_MAX = 0.055, 0.235                      # the drawn ends of the log remap

    # THE BUFFER IS A FIXED SIZE AT EVERY t. A splat count that changes with time is a scene that
    # cannot be differenced frame to frame, and differencing frames is how this project catches a
    # movie that silently stopped moving. So nothing here appears or disappears -- things that are
    # not yet real are emitted with alpha 0 at the place they will be.
    N_OBJ, N_PAD, N_MARK, N_BAR = 300, 150, 16, 90

    P, kind, tint, vis = [], [], [], []

    def ring(cx, cz, r, n, jitter=0.0, seed=0):
        rng = np.random.default_rng(seed)
        a = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
        rr = r * (1.0 + jitter * rng.standard_normal(n))
        return np.stack([cx + rr * np.cos(a), np.zeros(n), cz + rr * np.sin(a)], 1)

    def disc(cx, cz, r, n, seed=0):
        rng = np.random.default_rng(seed)
        k = np.sqrt(rng.random(n)) * r
        a = rng.random(n) * 2 * np.pi
        return np.stack([cx + k * np.cos(a), np.zeros(n), cz + k * np.sin(a)], 1)

    base_z = -0.30
    top_z = base_z + 0.34                            # the ceiling line, in bar units

    for i, o in enumerate(objs):
        cx = x0 + STEP * i
        # DECLARED LOG REMAP of the true 360:1 diameter range
        r = R_MIN + (R_MAX - R_MIN) * (math.log10(d[i] / d_lo) / span)

        F_app = float(o["grip_applied_N"])
        F_min = float(o["grip_min_N"])
        over = F_app / ceiling

        # ── WHERE THE PADS ARE. One rate at every station; the OBJECT supplies the stop, so the
        # five contact moments below are five different times produced by one command.
        u_hit = f_close * ((A0 - r) / max(A0 - R_MIN, 1e-9))
        if u <= u_hit:
            gap = A0 - (A0 - r) * (u / max(u_hit, 1e-9))
            press = 0.0
        else:
            gap = r
            ramp = min(1.0, (u - u_hit) / max(f_load - u_hit, 1e-9))
            press = min(1.0, over) * 0.30 * r * ramp   # the dimple IS grip_applied over the ceiling

        # ── DOES IT STAY? The ceiling and the bars decide, and both were derived, not chosen.
        drop_z = 0.0
        if F_app > ceiling and u > f_load:
            dt = (u - f_load) * T                      # it falls at the planet's own g
            drop_z = -0.5 * g * dt * dt / max(float(nums["extent_m"]), 1e-9)

        # THE OBJECT
        O = disc(cx, drop_z, max(r - 0.35 * press, 1e-3), N_OBJ, seed=17 + i)
        P.append(O); kind += [1] * N_OBJ
        tint += [float(o["friction_ratio"])] * N_OBJ; vis += [1.0] * N_OBJ

        # THE TWO PADS, closing horizontally, bowing around the object as the force rises
        for s in (-1.0, +1.0):
            px = cx + s * (gap + PAD_T * 0.5)
            rng = np.random.default_rng(97 + i * 7 + int(s))
            zz = (rng.random(N_PAD) - 0.5) * 2.0 * PAD_H
            bow = press * np.clip(1.0 - (np.abs(zz) / max(r, 1e-9)) ** 2, 0.0, 1.0)
            xx = px + s * (rng.random(N_PAD) - 0.5) * PAD_T - s * bow
            P.append(np.stack([xx, np.zeros(N_PAD), zz], 1))
            kind += [0] * N_PAD; tint += [0.0] * N_PAD; vis += [1.0] * N_PAD

        # THE CONTACT MARKS -- emitted always, at alpha 0 until the object has stopped the pads,
        # so the buffer keeps its shape and nothing pops into existence mid-movie.
        touched = 1.0 if u > u_hit else 0.0
        for s in (-1.0, +1.0):
            C = ring(cx + s * r * 0.92, drop_z,
                     (0.018 + 0.030 * min(over, 1.5)) * touched, N_MARK, seed=5 + i)
            P.append(C); kind += [2] * N_MARK
            tint += [min(over, 1.5)] * N_MARK; vis += [touched] * N_MARK

        # THE TWO BARS. The SLIP THRESHOLD and the FORCE ACTUALLY APPLIED, both against the same
        # ceiling line -- so the gap between them IS the safety margin, drawn, and a bar that
        # overtops the line is an object that is about to be on the floor.
        for val, k, w, ox in ((F_min, 3, 0.034, -0.10), (F_app, 4, 0.018, -0.10)):
            hgt = 0.34 * min(val / ceiling, 1.45) * min(1.0, u / max(f_load, 1e-9))
            rng = np.random.default_rng(41 + i * 3 + k)
            bz = base_z + rng.random(N_BAR) * max(hgt, 1e-5)
            bx = cx + ox + (rng.random(N_BAR) - 0.5) * w
            P.append(np.stack([bx, np.zeros(N_BAR), bz], 1))
            kind += [k] * N_BAR
            tint += [min(val / ceiling, 2.0)] * N_BAR; vis += [1.0] * N_BAR

    # THE CEILING LINE -- this hand's maximum pinch, the same at every station
    n_line = 220
    gx = np.linspace(x0 - 0.32, x0 + STEP * (n_st - 1) + 0.32, n_line)
    P.append(np.stack([gx, np.zeros(n_line), np.full(n_line, top_z)], 1))
    kind += [5] * n_line; tint += [0.0] * n_line; vis += [1.0] * n_line

    P = np.concatenate(P, 0)
    kind = np.asarray(kind, float)
    tint = np.asarray(tint, float)
    vis = np.asarray(vis, float)
    n = len(P)

    b = blank(n)
    b[:, 0:3] = P
    nrm = np.zeros((n, 3)); nrm[:, 2] = 1.0
    b[:, 21:24] = nrm

    alb = np.zeros((n, 3), np.float32)
    skin = np.asarray(nums.get("skin_albedo_rgb", [0.65, 0.45, 0.36]), np.float32)
    alb[kind == 0] = skin                                     # the pads ARE theHuman's skin
    # THE OBJECT'S COLOUR IS ITS MU: slick -> pale cold, grippy -> dark warm. A measurement.
    om = kind == 1
    if om.any():
        f = np.clip((tint[om] - 0.10) / (0.70 - 0.10), 0.0, 1.0)[:, None]
        alb[om] = (np.array([0.80, 0.85, 0.92], np.float32) * (1 - f)
                   + np.array([0.24, 0.17, 0.13], np.float32) * f)
    # the contact mark and the applied-force bar redden as they approach the ceiling
    for k in (2, 4):
        mk = kind == k
        if mk.any():
            f = np.clip(tint[mk], 0.0, 1.5)[:, None] / 1.5
            alb[mk] = (np.array([0.35, 0.85, 0.45], np.float32) * (1 - f)
                       + np.array([1.00, 0.25, 0.15], np.float32) * f)
    alb[kind == 3] = np.array([0.42, 0.50, 0.72], np.float32)   # the slip threshold, cool
    alb[kind == 5] = np.array([0.85, 0.80, 0.35], np.float32)   # the ceiling

    S = float(nums.get("S_earth", 1.0))
    b[:, 16:19] = lit(alb, S * 0.85 + 0.15, e_ref=S, tone=0.45)
    b[:, AR:AB + 1] = alb
    b[:, 19] = np.where(kind == 3, 0.55, 0.95) * vis      # vis carries the not-yet-real marks
    b[:, 20] = np.where(kind == 2, 0.014, np.where(kind == 5, 0.008, 0.012))
    b[:, 11] = np.where((kind == 2) | (kind == 5), GLOW, SOLID)
    return b


def measure(nums):
    """Facts a reader can check without trusting a word of the prose."""
    objs = nums["objects"]
    by = {o["name"]: o for o in objs}
    ration = by["a full water ration"]
    soaped = by["the same ration, soaped"]
    ball = by["a regulation bowling ball"]
    return {
        # THE CHECK IT WAS NOT FITTED TO: an independent instrument, a different population and a
        # different decade. [MA85]'s men-30-34 mean should land near the 95th percentile of a
        # mixed-sex, 6-to-80 population's best hand -- and it lands at 0.99 of it, over 14,984 people.
        "norm_over_nhanes_p95_ratio": nums["norm_over_nhanes_p95_ratio"],
        "ceiling_agrees_with_nhanes": abs(nums["norm_over_nhanes_p95_ratio"] - 1.0) < 0.10,

        # THE CHAPTER'S THESIS, AS A NUMBER: same object, same mass, same world, one soaped. If the
        # required force changes, "whether it holds" is a fact about the SURFACE, not about strength.
        "soap_costs_this_much_more_grip_ratio":
            soaped["grip_min_N"] / max(ration["grip_min_N"], 1e-12),
        "same_mass_different_answer": abs(soaped["mass_kg"] - ration["mass_kg"]) < 1e-12,

        # ONE COMMAND, MANY OBJECTS: the spread the identical law produces across the table.
        "mass_span_ratio": nums["mass_span_ratio"],
        "grip_span_ratio": (max(o["grip_min_N"] for o in objs)
                            / max(min(o["grip_min_N"] for o in objs), 1e-12)),
        "grips_named_count": len({o["grip_needed"] for o in objs}),

        # THE DERIVED SURPRISE: because mu falls as the pad flattens, the squeeze goes as the 3/2
        # power of the load, so a heavier object costs MORE than proportionally more.
        "grip_scales_as_weight_exponent": nums["grip_scales_as_weight_exponent"],
        "margin_survives_ratio": nums["margin_capacity_gain_ratio"] - 1.0,
        "margin_asked_for": nums["safety_margin"],
        "margin_is_smaller_than_asked":
            (nums["margin_capacity_gain_ratio"] - 1.0) < nums["safety_margin"],
        # ... AND THE SCOPE, reported next to the boast rather than somewhere it can be missed.
        # ZERO objects on this table sit in the band where mu is still sliding: the three-halves
        # law and the margin erosion are real, derived, and they govern things lighter than
        # hertz_regime_max_mass_kg. Everything on the table is heavier, so the linear law is what
        # actually runs on it. A result with a stated range beats a result with a headline.
        "objects_in_hertz_regime_count": nums["objects_in_hertz_regime_count"],
        "hertz_regime_max_mass_kg": nums["hertz_regime_max_mass_kg"],
        "hertz_demo_over_constant_mu_ratio": nums["hertz_demo_over_constant_mu_ratio"],

        # GRAVITY IS A DIAL, and only the forces move: the clock does not, and mu does not.
        "earth_costs_this_much_more_ratio": ball["earth_over_here_ratio"],
        "ball_holdable_in_a_pinch_here": ball["held_in_a_pinch"],
        "ball_drops_from_a_pinch_above_m_s2": ball["gravity_that_drops_it_from_a_pinch_m_s2"],

        # THE APPROACH CANNOT BE FEEDBACK -- 300 decisions at 74 ms is 22 s, and a grasp is under 1 s.
        "close_by_feel_alone_s": nums["close_by_feel_alone_s"],
        "approach_must_be_feedforward": nums["approach_must_be_feedforward"],

        # and its own rhythm sits in a human's band without gearing
        "grasp_in_human_band": 0.04 <= nums["duration_s"] <= 10.0,
        "grasp_in_loops_count": nums["grasp_in_loops_count"],

        # what is NOT sourced, reported rather than buried
        "boot_mu_is_sourced": nums["boot_mu_is_sourced"],
        "pressurised_glove_penalty_traced": nums["pressurised_glove_penalty_traced"],
        "grip_scaling_is_applied": nums["grip_scaling_is_applied"],
    }
