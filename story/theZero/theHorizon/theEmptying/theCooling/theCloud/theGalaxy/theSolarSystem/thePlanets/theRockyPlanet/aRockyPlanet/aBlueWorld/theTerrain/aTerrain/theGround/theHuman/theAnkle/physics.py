"""theAnkle -- the joint that makes walking cheap, and the only one that touches the ground.

THE EDGE. The parent's gait was a SLED: both feet 4.2% of stature off the floor at mid-stride, duty
factor near 1.0 on each, no double support. Two faults, and the second is this chapter's subject --
the knee bent on the wrong leg, AND THE FOOT HAD NO JOINT. A rigid foot welded to a swinging shank
must plough its toe or lift its heel; it cannot keep a sole on the ground.

WHAT THIS MEMBRANE IS. The foot's roll-over shape -- the locus its effective contact point traces
during stance -- was measured by Hansen, Childress & Knox (2004) to be a circular arc of radius about
0.30 of leg length, near-independent of walking speed. A rocker of radius R rolls with its hub at
constant height, so the hip rises by (L - R)(1 - cos theta) rather than L(1 - cos theta): the foot
takes 30% out of the vault. That is a large part of why walking costs so little.

BUT THE ARC IS NOT A WHEEL, and modelling it as one is a trap this chapter fell into and climbed out
of. Drawn as a literal wheel the hip rose correctly and the sole left the ground, because a wheel has
nowhere to put a foot: measured, duty factor fell to 0.12. The arc is an EFFECTIVE description of
three rockers in sequence -- heel, then flat sole, then forefoot -- with an ankle pitching the foot
between them. Model the joint and the arc emerges; model the arc and the joint disappears.

Contained in theHuman. Its movie is ONE STANCE PHASE: heel strike to toe off.
"""
from __future__ import annotations

import math

import numpy as np

# ── MEASURED. Human ankle kinematics and kinetics in level walking; true outside this story.
PLANTARFLEX_RAD = 0.45      # heel-up range at push-off, ~26 degrees
HEEL_ROCKER = 0.15          # fraction of stance spent rolling over the heel
FLAT_ROCKER = 0.50          # ... flat, the shank rotating over a still foot
FORE_ROCKER = 0.35          # ... rolling over the forefoot, heel rising
ANKLE_WORK_SHARE_LIT = 0.475  # the ankle's share of positive work in walking, literature 45-50%

FREE = {
    # HOW HARD THE PUSH-OFF IS. The range a person actually plantarflexes varies with speed and
    # intent, and it is the one number here a body chooses rather than inherits.
    "push_off": {"lo": 0.0, "hi": 1.0, "default": 1.0,
                 "label": "push-off effort", "unit": "of the measured range",
                 "local": "how hard to push off is a choice, not a law"},
}


def rocker_radius(leg_L):
    """The arc the foot and ankle roll on: 0.30 of leg length (Hansen, Childress & Knox 2004)."""
    return 0.30 * float(leg_L)


def vault(leg_L, swing, R):
    """How far the hip rises between mid-stance and the extremes. Pass R = 0 for a point foot and the
    difference IS what the foot is worth."""
    return (float(leg_L) - float(R)) * (1.0 - math.cos(float(swing)))


def centre_of_pressure(u, heel, toe):
    """WHERE THE GROUND PUSHES, as a fraction along the sole, through stance.

    A FLAT FOOT HAS NO GEOMETRIC CONTACT POINT, and that is the subtlety this function exists for.
    While the sole is flat every point on it is equally low, so asking geometry "where does it touch"
    has no answer -- taking the lowest sample made the contact TELEPORT from heel to toe at the moment
    the pitch went negative, and the story above claimed it swept.

    It does sweep, but not because of the sole's shape: the centre of pressure is where the ground
    reaction meets the foot, and it advances because the BODY advances over it. Measured CoP in level
    walking runs monotonically from the heel at contact to the forefoot at push-off, and it is that
    travel -- not the pitch -- which makes the roll-over shape an arc rather than three points."""
    u = min(max(float(u), 0.0), 1.0)
    return float(heel) + (float(toe) - float(heel)) * (0.5 - 0.5 * math.cos(math.pi * u))


def push_off_work(torque_Nm, range_rad):
    """Positive work at toe-off: a torque through an angle. Nothing subtler is claimed."""
    return float(torque_Nm) * float(range_rad)


def derive(parent, free):
    if parent is None or "ankle_torque_Nm" not in parent:
        raise ValueError("theAnkle requires theHuman as its parent")
    free = free or {}
    effort = float(free.get("push_off", FREE["push_off"]["default"]))

    h = float(parent["height_m"])
    m = float(parent["mass_kg"])
    g = float(parent["g"])
    leg_L = float(parent["leg_length_m"])
    tau = float(parent["ankle_torque_Nm"])
    stride_s = float(parent["duration_s"])
    step_s = float(parent["step_time_s"])

    R = rocker_radius(leg_L)
    swing = 0.42                       # the parent's hip amplitude, and its one untuned number
    v_point = vault(leg_L, swing, 0.0)
    v_rock = vault(leg_L, swing, R)

    plantar = PLANTARFLEX_RAD * effort
    W_push = push_off_work(tau, plantar)
    # what it costs to lift the body over the vault, twice a stride
    W_com = 2.0 * m * g * v_rock
    share = W_push / max(W_push + W_com, 1e-9)

    return {
        # ITS REAL SIZE: a foot, heel to toe.
        "extent_m": 0.202 * h,
        # ITS OWN DURATION: one stance phase. Inside theHumanClock's band without gearing -- the
        # third membrane in the story that can say that, and all three are parts of a body.
        "duration_s": 0.60 * stride_s,

        # the rocker
        "rocker_radius_m": R,
        "rocker_over_leg": R / leg_L,
        "vault_point_foot_m": v_point,
        "vault_with_rocker_m": v_rock,
        "vault_saved_m": v_point - v_rock,
        "vault_saved_frac": (v_point - v_rock) / max(v_point, 1e-9),

        # the three rockers in sequence, which is what the arc really is
        "heel_rocker_frac": HEEL_ROCKER,
        "flat_rocker_frac": FLAT_ROCKER,
        "forefoot_rocker_frac": FORE_ROCKER,
        "rockers_sum_to_one": abs(HEEL_ROCKER + FLAT_ROCKER + FORE_ROCKER - 1.0) < 1e-9,

        # the kinetics
        "torque_Nm": tau,
        "torque_Nm_per_kg": tau / m,
        "plantarflex_rad": plantar,
        "push_off_effort": effort,
        "push_off_work_J": W_push,
        "push_off_power_W": W_push / max(step_s, 1e-9),
        "com_work_per_stride_J": W_com,
        "ankle_work_share": share,
        "ankle_work_share_literature": ANKLE_WORK_SHARE_LIT,
        "cop_travel_m": R * 2.0 * swing,

        # carried on
        "height_m": h,
        "leg_length_m": leg_L,
        "S_earth": float(parent["S_earth"]),
        "gait_cycle": [list(r) for r in parent["gait_cycle"]],
        "gait_samples": int(parent["gait_samples"]),
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- a foot rolling through one stance phase
# ════════════════════════════════════════════════════════════════════════════════════════════════
def emit(nums, t=1.0):
    """One foot, from heel strike to toe off, with the contact point marked as it travels.

    LOCAL UNITS: 1.0 is the foot's length, heel to toe. +X is the walking direction.

    WHAT IS BEING DRAWN. The foot, pitched by the angle the three-rocker law gives at this point in
    stance; the ground line; and the CENTRE OF PRESSURE as a bright mark. It starts under the heel,
    sweeps forward along the sole, and ends under the ball. That travelling pressure IS the roll-over
    shape, and its arc is why the hip above it need not pole-vault over a heel.

    The pale trail behind the mark is where the pressure has already been -- so the shape is drawn by
    the thing that makes it, not by a curve fitted over the top.

    AND IT IS NOT THE LOWEST POINT OF THE SOLE, which is what this first asked for. A flat foot has no
    lowest point: every part of it is equally low, so the mark sat on the heel for half of stance and
    then teleported to the toe. See centre_of_pressure().
    """
    from matter import blank, lit, SOLID, GLOW, AR, AG, AB

    u = min(max(float(t), 0.0), 1.0)             # stance progress: 0 heel strike, 1 toe off
    # the parent's own three-rocker pitch law, rebuilt from its published fractions
    hf, ff = float(nums["heel_rocker_frac"]), 1.0 - float(nums["forefoot_rocker_frac"])
    plantar = float(nums["plantarflex_rad"])
    if u < hf:
        pitch = 0.10 * (1.0 - u / hf)
    elif u < ff:
        pitch = 0.0
    else:
        pitch = -plantar * (u - ff) / (1.0 - ff)

    HEEL, TOE = -0.25, 0.75                      # the ankle sits a quarter of the way along the foot
    THICK = 0.11

    def rot(x, z):
        c, s = math.cos(pitch), math.sin(pitch)
        return x * c - z * s, x * s + z * c

    # the sole, and the ground it is on
    n_sole = 260
    xs = np.linspace(HEEL, TOE, n_sole)
    sx, sz = np.array([rot(x, 0.0) for x in xs]).T
    lift = -min(sz.min(), 0.0)                   # the lowest point of the sole is ON the ground
    sz = sz + lift

    # the upper of the foot, offset along the pitched normal
    ux, uz = np.array([rot(x, THICK) for x in xs]).T
    uz = uz + lift

    pts = [np.stack([sx, np.zeros(n_sole), sz], 1),
           np.stack([ux, np.zeros(n_sole), uz], 1)]
    # fill between, so it reads as a foot rather than two lines
    for f in (0.25, 0.5, 0.75):
        mx, mz = np.array([rot(x, THICK * f) for x in xs]).T
        pts.append(np.stack([mx, np.zeros(n_sole), mz + lift], 1))
    P = np.concatenate(pts, 0)
    kind = np.zeros(len(P))

    # THE GROUND, a plain line, so the contact is visibly a contact
    gx = np.linspace(HEEL - 0.35, TOE + 0.35, 200)
    G = np.stack([gx, np.zeros(200), np.zeros(200)], 1)
    P = np.concatenate([P, G], 0); kind = np.concatenate([kind, np.full(200, 1)])

    # THE CENTRE OF PRESSURE, and the trail of where it has been -- the roll-over shape, self-drawn.
    # Read from centre_of_pressure() rather than from the sole's lowest sample, because a flat foot
    # has no lowest sample: see that function's note.
    x_now = centre_of_pressure(u, HEEL, TOE * 0.92)
    C = [np.stack([[x_now], [0.0], [0.0]], 1)]
    trail_n = 0
    if u > 0.02:
        us = np.linspace(0.0, u, 40)
        tx = np.array([centre_of_pressure(uu, HEEL, TOE * 0.92) for uu in us])
        trail_n = len(tx)
        C.append(np.stack([tx, np.zeros(trail_n), np.full(trail_n, 0.004)], 1))
    Cc = np.concatenate(C, 0)
    P = np.concatenate([P, Cc], 0)
    kind = np.concatenate([kind, [2], np.full(trail_n, 3)])

    n = len(P)
    b = blank(n)
    b[:, 0:3] = P
    nrm = np.zeros((n, 3)); nrm[:, 2] = 1.0
    b[:, 21:24] = nrm

    alb = np.zeros((n, 3), np.float32)
    alb[kind == 0] = np.array([0.42, 0.36, 0.31], np.float32)   # the foot
    alb[kind == 1] = np.array([0.20, 0.22, 0.24], np.float32)   # the ground
    alb[kind == 2] = np.array([1.00, 0.72, 0.25], np.float32)   # where it touches NOW
    alb[kind == 3] = np.array([0.55, 0.62, 0.80], np.float32)   # where it has touched
    S = float(nums.get("S_earth", 1.0))
    b[:, 16:19] = lit(alb, S * 0.85 + 0.15, e_ref=S, tone=0.45)
    b[:, AR:AB + 1] = alb
    b[:, 19] = np.where(kind == 3, 0.55, 0.96)
    b[:, 20] = np.where(kind == 2, 0.045, 0.016)
    b[:, 11] = np.where(kind == 2, GLOW, SOLID)
    return b


def measure(nums):
    """Facts a reader can check without trusting the prose."""
    return {
        # THE CHECK THIS WAS NOT FITTED TO
        "torque_Nm_per_kg": nums["torque_Nm_per_kg"],
        "torque_matches_literature": abs(nums["torque_Nm_per_kg"] - 1.5) < 0.15,
        # the foot is worth 30% of the vault
        "vault_saved_frac": nums["vault_saved_frac"],
        "rocker_over_leg": nums["rocker_over_leg"],
        # three rockers, and they are a partition of stance
        "rockers_sum_to_one": nums["rockers_sum_to_one"],
        # the ankle does a large share of the work, though this model understates it
        "ankle_work_share": nums["ankle_work_share"],
        "share_vs_literature": nums["ankle_work_share"] / nums["ankle_work_share_literature"],
        # and its own rhythm needs no gearing
        "stance_in_human_band": 0.04 <= nums["duration_s"] <= 10.0,
    }
