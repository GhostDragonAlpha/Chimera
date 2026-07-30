"""theThrust -- EVA -- locomotion where there is no ground at all

STUB. Declared from the story, derived from nothing yet. `derive()` returns its own size, its own
duration and `stub: True` -- and NO physics -- so the tree grows, the membrane is visible in
numbers.json, and nobody can mistake an empty chapter for a finished one.

WHAT IT MUST DERIVE, when someone fills it in:
    * thrust and specific impulse -- and therefore a propellant budget, which is a MASS
    * delta-v for a crater-rim drift, from the gravity aBlueWorld derives
    * attitude control: a body with no contact rotates when it pushes off-centre
    * the interaction with theLoad -- carried ore is reaction mass you did not want

WHAT IT CONSUMES from theHuman (all of these are already published and checked):
    * height_m, mass_kg, com_height_m, leg_length_m -- the body
    * g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
    * duration_s (one stride), step_time_s, cadence_steps_s -- its clock
    * gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

THE STORY'S VERBS THAT LAND HERE:
    * EVA Thrusters / Jetpack (Hold Spacebar)
    * Vertical Hop / Zero-G Leap [Spacebar] -- the same key, a different physics
    * working in a depressurised cargo hold with the graviton beam

THE OPEN QUESTIONS -- what has to be decided before a line of physics is written:
    * is thrust a suit system (a child of aHuman) or a body verb (a child of theHuman)?
    * does the gait membrane switch OFF, or does it degrade continuously with contact time?
    * does propellant come out of the same budget as theBreath's oxygen?
"""
from __future__ import annotations


def derive(parent, free):
    if parent is None or "height_m" not in parent:
        raise ValueError("theThrust requires theHuman as its parent")
    h = float(parent["height_m"])
    return {
        # A STUB STATES ITS SCALE AND NOTHING ELSE. `extent_m` is the only honest number available
        # before the physics exists -- it is a size, read off the body, not a claim about behaviour.
        "extent_m": float(parent['height_m']) * 0.6,
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
