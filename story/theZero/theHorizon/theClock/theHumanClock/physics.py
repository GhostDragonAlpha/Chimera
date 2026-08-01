"""theHumanClock -- the band a person can act in, and therefore the only band the game can use.

Every other clock in this story is set by DENSITY. This one is set by a body, and because the player
acts only through it, it decides which of the other clocks can be put in their hands at all.

A button is a DURATION and a stick is a MAGNITUDE; together they are an impulse. Anything whose
response time falls outside the band must be GEARED into it -- the physics being right is not
sufficient, it has to be reachable.
"""
from math import sqrt, log10

FRAME_S = 1.0 / 60.0            # one tick at 60 Hz: the finest grain that can be shown
FUSION_S = 0.040                # below this, separate events are perceived as one
TAP_S = 0.110                   # the shortest deliberate press
REACTION_S = 0.250              # see -> press
HOLD_MIN_S, HOLD_MAX_S = 0.20, 3.0     # comfortable, controllable, repeatable
SUSTAINED_S = 10.0              # past this it is a setting, not an action


def impulse(stick, a_max, held_s):
    """THE WHOLE INPUT VOCABULARY, in one line.

        dv = stick * a_max * held

    The button says HOW LONG, the stick says HOW HARD, and the membrane being acted on supplies
    everything else. A tap and a lean are the same act with two dials -- which is why twelve controls
    can express so much."""
    return max(0.0, min(1.0, float(stick))) * float(a_max) * max(0.0, float(held_s))


def gearing_for(delta_v, held_s=1.0):
    """THE GEARING LAW. Choose a_max so that ONE SECOND of full deflection produces a noticeable
    fraction of the change the player is trying to make. Too much and a 110 ms tap overshoots; too
    little and a 10 s hold does nothing visible -- and the control feels broken even though the
    physics is perfect."""
    return float(delta_v) / max(float(held_s), 1e-6)


def controllable(response_s):
    """Is a system's own response time inside the band a person can act in?"""
    return FUSION_S <= float(response_s) <= SUSTAINED_S


def gear_ratio(response_s):
    """If it is not, this is how far out it is -- the factor it must be geared by."""
    r = float(response_s)
    if r < FUSION_S:
        return FUSION_S / max(r, 1e-30)          # too fast: must be slowed
    if r > SUSTAINED_S:
        return r / SUSTAINED_S                    # too slow: must be sped up
    return 1.0


def derive(parent, free):
    if parent is None or "duration_s" not in parent:
        raise ValueError("theHumanClock requires theClock as its parent")
    band_lo, band_hi = FUSION_S, SUSTAINED_S
    # How far the human band sits from the clocks this story has already derived -- i.e. how much
    # gearing each one needs before a player could ever feel it.
    sun_dyn = float(parent["t_dyn_sun_s"])
    return {
        # ITS OWN DURATION: one comfortable press -- the unit the player actually acts in.
        "duration_s": HOLD_MAX_S,
        # ITS REAL SIZE: a person. The only unit nobody has to imagine.
        #
        # A MEASURED LITERAL, AND IT IS LEGAL FOR THE SAME REASON THE SIX CONSTANTS ABOVE ARE: it is
        # an anthropometric measurement of the species, not a number carried by any parent of this
        # membrane. Mean adult stature, pooled across populations, is 1.70 m to three figures
        # (NCD-RisC 2016, ~1,470 studies / 18.6M adults: 171.0 cm men, 159.5 cm women). theClock, its
        # parent, carries only densities and ticks -- there is no body anywhere above this membrane to
        # inherit a height from.
        #
        # HONEST ABOUT WHAT IT IS NOT: theHuman, fourteen membranes down the OTHER branch, derives a
        # body 1.78 m tall from its own anthropometry, and this is not that number and must not be
        # made into it. They are different claims -- a population mean here, one specific derived body
        # there -- and this membrane cannot read that one anyway (it is not an ancestor). What this
        # 1.7 is FOR is stating the scale of the band below in a unit a reader already owns.
        "extent_m": 1.7,
        "frame_s": FRAME_S,
        "fusion_s": FUSION_S,
        "tap_s": TAP_S,
        "reaction_s": REACTION_S,
        "hold_min_s": HOLD_MIN_S,
        "hold_max_s": HOLD_MAX_S,
        "band_lo_s": band_lo,
        "band_hi_s": band_hi,
        # HOW NARROW THE BAND IS -- ARITHMETIC ON THE TWO MEASUREMENTS, not a stated number.
        #
        # This used to read `2.5`, and the two constants it is a statement about are ten lines above
        # it: FUSION_S = 0.040 and SUSTAINED_S = 10.0, both measured facts about a nervous system.
        # log10(10.0 / 0.040) = 2.398, so the typed 2.5 was 4% wide of the numbers in its own file --
        # and, worse, it stood still. Retime the flicker-fusion threshold and band_lo_s moved while
        # the width of the band did not, which is the typed-number failure inside a single membrane
        # instead of across two.
        #
        # A decade IS log10 of a ratio, so there is nothing here to choose. The ends are this
        # membrane's own two measurements; the width follows.
        "band_decades": log10(band_hi / band_lo),
        "gear_for_a_star": gear_ratio(sun_dyn),   # a star's own tick is ~30 min: needs gearing
        "planck_ticks_per_tap": TAP_S / float(parent["duration_s"])   # theClock's duration IS the Planck tick,
    }


def emit(nums, t=1.0):
    """The matter of theHumanClock, in its own local units.

    There is no matter here either -- what can be drawn is the BAND. A log axis of durations from a
    frame to ten seconds, with the human's reachable stretch lit and everything outside it dark. The
    movie is a press: the bar fills across the band as the button is held, and the rate at which it
    fills is the only thing a player ever really controls."""
    import numpy as np
    from matter import blank, paint, GLOW, SOLID

    tt = float(t)
    lo, hi = np.log10(FUSION_S), np.log10(SUSTAINED_S)
    n = 14000
    rng = np.random.default_rng(19)

    # the whole span the story covers, log-spaced: Planck tick out to a star's life
    x = rng.uniform(-44.0, 18.0, n)
    b = blank(n)
    b[:, 0] = x / 31.0                                     # squeeze 62 decades into [-1, 1]
    b[:, 1] = rng.normal(0.0, 0.05, n)
    b[:, 2] = rng.normal(0.0, 0.02, n)
    inside = (x >= lo) & (x <= hi)
    b[:, 16] = np.where(inside, 1.00, 0.20)
    b[:, 17] = np.where(inside, 0.85, 0.24)
    b[:, 18] = np.where(inside, 0.35, 0.32)
    b[:, 19] = np.where(inside, 0.55, 0.06)
    b[:, 20] = 0.060  # x6: GLOW no longer carries a hidden multiplier (gpu_pipeline._profile)
    b[:, 11] = GLOW

    # the press: a bar filling across the band, which is the one thing the player controls
    n_p = 3000
    held = TAP_S * (1.0 - tt) + SUSTAINED_S * tt
    xp = np.linspace(lo, np.log10(max(held, FUSION_S)), n_p)
    p = blank(n_p)
    p[:, 0] = xp / 31.0
    p[:, 1] = -0.12 + rng.normal(0.0, 0.012, n_p)
    paint(p, (1.0, 0.95, 0.75), 0.9, 0.014, SOLID)
    return np.concatenate([b, p], axis=0)


def measure(nums):
    """Facts: the band is narrow -- under two and a half decades, against the whole ladder's span in
    theClock's `orders_of_magnitude` -- and a star's own tick is far outside it, so anything a player
    touches must be geared, never handed over raw.

    THE SPAN IS NAMED BY ITS KEY AND NOT BY ITS VALUE, deliberately. This line used to say "against
    the ladder's 60"; theClock now computes that span from its own two ends instead of stating it, so
    a number copied into this sentence would have gone stale the moment it did. Prose drifts exactly
    the way a typed literal drifts, and it cannot be caught by the audit -- so point at where the
    number lives."""
    return {"band_decades": nums["band_decades"],
            "star_needs_gearing": nums["gear_for_a_star"] > 1.0,
            "gear_for_a_star": nums["gear_for_a_star"],
            "tap_is_controllable": controllable(nums["tap_s"])}
