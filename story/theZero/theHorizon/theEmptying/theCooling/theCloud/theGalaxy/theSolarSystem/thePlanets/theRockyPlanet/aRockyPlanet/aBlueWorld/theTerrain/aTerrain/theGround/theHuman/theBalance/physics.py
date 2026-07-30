"""theBalance -- the frontal plane, which does not currently exist

STUB. Declared from the story, derived from nothing yet. `derive()` returns its own size, its own
duration and `stub: True` -- and NO physics -- so the tree grows, the membrane is visible in
numbers.json, and nobody can mistake an empty chapter for a finished one.

WHAT IT MUST DERIVE, when someone fills it in:
    * lateral CoM excursion per step, from the frontal-plane inverted pendulum theHuman has
    * pelvic list and rotation -- what lengthens a stride without lengthening a leg
    * trunk counter-rotation and head stabilisation: the head stays still while all below moves
    * reticle sway as a function of breath phase, heart rate and stance -- braced vs standing

WHAT IT CONSUMES from theHuman (all of these are already published and checked):
    * height_m, mass_kg, com_height_m, leg_length_m -- the body
    * g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
    * duration_s (one stride), step_time_s, cadence_steps_s -- its clock
    * gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

THE STORY'S VERBS THAT LAND HERE:
    * Deploy Bipod / Brace [Y]
    * Steady Aim [Left Shift] -- and the sway IS theBreath, already derived at 15.7/min
    * the weight shift under every step, which no key presses and every eye sees

THE OPEN QUESTIONS -- what has to be decided before a line of physics is written:
    * does bracing consume theHand, theStance, or both?
    * is holding a breath a theBreath state with a CO2 cost, closing that loop?
    * does the derived 4.7% vault (against a human 2.5%) get fixed here or in theAnkle?
"""
from __future__ import annotations


def derive(parent, free):
    if parent is None or "height_m" not in parent:
        raise ValueError("theBalance requires theHuman as its parent")
    h = float(parent["height_m"])
    return {
        # A STUB STATES ITS SCALE AND NOTHING ELSE. `extent_m` is the only honest number available
        # before the physics exists -- it is a size, read off the body, not a claim about behaviour.
        "extent_m": float(parent['height_m']) * 0.1,
        "duration_s": float(parent["duration_s"]),
        "stub": True,
        "declared_by": "Chimera/docs/THE_STORY.md",
    }


def emit(nums, t=1.0):
    """No matter yet. A stub draws NOTHING rather than a placeholder: a placeholder in a splat buffer
    is a body this chapter has not built, and this project has a rule about that."""
    from matter import blank
    return blank(0)


def measure(nums):
    """The only thing a stub can honestly report is that it is one."""
    return {"stub": True, "derives_nothing_yet": True}
