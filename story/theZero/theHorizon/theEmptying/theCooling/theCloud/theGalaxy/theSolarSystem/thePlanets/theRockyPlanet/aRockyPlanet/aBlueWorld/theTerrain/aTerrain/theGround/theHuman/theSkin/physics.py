"""theSkin -- the boundary itself: heat out, and what a laser does to it

STUB. Declared from the story, derived from nothing yet. `derive()` returns its own size, its own
duration and `stub: True` -- and NO physics -- so the tree grows, the membrane is visible in
numbers.json, and nobody can mistake an empty chapter for a finished one.

WHAT IT MUST DERIVE, when someone fills it in:
    * skin area from stature and mass (DuBois) -- theSweep already assumes 1.83 m2 and should read it
    * damage as an ENERGY, not a hit point: joules deposited, over what area, in what time
    * what a breach costs -- theBreath's loop pressure is what leaks, and it derived that
    * healing as a rate, so time is the currency rather than a potion

WHAT IT CONSUMES from theHuman (all of these are already published and checked):
    * height_m, mass_kg, com_height_m, leg_length_m -- the body
    * g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
    * duration_s (one stride), step_time_s, cadence_steps_s -- its clock
    * gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

THE STORY'S VERBS THAT LAND HERE:
    * Administer Bio-Patch [C] -- local coagulants after a laser graze
    * the suit breach the story implies but never spells out

THE OPEN QUESTIONS -- what has to be decided before a line of physics is written:
    * is damage a state of theSkin or a separate membrane?
    * does a breach couple to theBreath, ending the excursion the way the numbers already say?
    * is there a body temperature to lose, and does aHuman's 11.9 mm of insulation defend it?
"""
from __future__ import annotations


def derive(parent, free):
    if parent is None or "height_m" not in parent:
        raise ValueError("theSkin requires theHuman as its parent")
    h = float(parent["height_m"])
    return {
        # A STUB STATES ITS SCALE AND NOTHING ELSE. `extent_m` is the only honest number available
        # before the physics exists -- it is a size, read off the body, not a claim about behaviour.
        "extent_m": float(parent['height_m']),
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
