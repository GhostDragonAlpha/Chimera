"""theStance -- every configuration a body holds that is not standing

STUB. Declared from the story, derived from nothing yet. `derive()` returns its own size, its own
duration and `stub: True` -- and NO physics -- so the tree grows, the membrane is visible in
numbers.json, and nobody can mistake an empty chapter for a finished one.

WHAT IT MUST DERIVE, when someone fills it in:
    * CoM height per posture, which re-runs the inverted pendulum: fall_rate = sqrt(g/H)
    * contact area and bearing pressure per posture -- prone spreads a body over ~5x the area
    * the transition COST: how long standing-to-prone takes, and it is not free
    * a lean's limit: how far the CoM can go outside the feet before the capture point is unreachable

WHAT IT CONSUMES from theHuman (all of these are already published and checked):
    * height_m, mass_kg, com_height_m, leg_length_m -- the body
    * g, fall_rate_rad_s, capture_point_at_1ms -- the balance law
    * duration_s (one stride), step_time_s, cadence_steps_s -- its clock
    * gait_cycle (48 samples) -- the pose, so nothing re-derives how to walk

THE STORY'S VERBS THAT LAND HERE:
    * Low Profile Stance [Left Ctrl] -- crouch
    * Prone Stance [X] -- crawling under thermal motion grids
    * Combat Slide [Left Ctrl while sprinting]
    * Corner Peeking Left / Right [Q / E] -- leaning past cover
    * Mantle / Vault [Spacebar at a ledge]

THE OPEN QUESTIONS -- what has to be decided before a line of physics is written:
    * is prone a posture or a different LOCOMOTION (crawling is not walking)?
    * does a slide need friction from theGround, and does the regolith's repose angle bound it?
    * does mantling need theHand -- can you vault a ledge with a rifle in both hands?
"""
from __future__ import annotations


def derive(parent, free):
    if parent is None or "height_m" not in parent:
        raise ValueError("theStance requires theHuman as its parent")
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
