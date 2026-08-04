"""theThrust -- the body as an engine, and the floor as the thing that has to take it.

THE EDGE. The parent walks, and a walk never asks the ground for much more than one body weight --
it is a fall, caught. Every OTHER thing a person does with their legs -- jump, start, stop, climb,
shove -- is the same body converting muscle work into momentum against this planet's gravity, and it
asks the ground for SEVERAL body weights through a contact patch that shrinks by a factor of three
and a half at the moment the heel leaves the floor. Whether those two things collide is not a
judgement. It is arithmetic, and the parent published every number it needs.

WHAT IS DERIVED, in this order, because each needs the one before it:

  1. WHAT A JUMP IS. The parent publishes `jump_height_m` and `g`, so the specific muscle work falls
     straight back out of them (w = g*h) and this chapter holds NO muscle constant of its own.
     Take-off speed is sqrt(2w) -- and therefore has NO GRAVITY IN IT. The same legs leave the
     ground at the same 2.28 m/s on every world in the universe; what gravity sets is only how long
     they stay up.

  2. HOW FAR THE PUSH GOES. Work happens over a DISTANCE, and the distance is the body's own
     geometry: a crouch of half-angle phi shortens the hip-to-ankle line by L(1 - cos phi), and the
     ankle adds the heel coming up. Distance sets contact time; contact time sets force.

  3. THE PEAK FORCE -- and then, separately, THE PEAK PRESSURE, which is a different question with a
     different answer. The force peaks in mid-drive with both soles flat. The pressure peaks at
     HEEL-LIFT, whenever that is, because that is when the area collapses.

  4. WHETHER THE GROUND HOLDS IT. `ground_bearing_kPa` is asked directly, at every instant, for the
     take-off and the landing separately, and the answer is BOUNDED rather than asserted: it depends
     on when the heel lifts, and the two bounds straddle the bearing capacity.

  5. WHAT FRICTION ALLOWS. a_max = mu*g, mass-free, so every acceleration here is 72% of Earth's --
     but the maximum LEAN is arctan(mu) and is the same on every world.

  6. THE POWER, checked against the measured band for human countermovement jumps.

WHAT THIS CHAPTER FOUND IN ITS PARENT. `jump_height(g) = w/g` leaves out the lift the legs do
BEFORE the feet leave the ground. They raise the centre of mass through `s` during the push-off, and
that costs g*s J/kg on top of the flight energy. Counted, the same muscle gives 0.505 m here rather
than 0.367 -- 37% more -- and the total comes to 6.10 J/kg, which is where the measured concentric
work of a countermovement jump actually sits. The parent's number is still used as THE jump
everywhere below, because a child consumes its parent's numbers rather than arguing with them; the
correction is published beside it as `jump_height_full_work_m` and handed up.

WHAT IT DELIBERATELY DOES NOT DO. The stub this replaces declared jetpacks, specific impulse and a
propellant budget. Those are EQUIPMENT, not a body, and belong under `aHuman` with the suit. What
this chapter does say about them is the derived reason they exist: 0.64 s of every jump is spent
with no contact and therefore no thrust of any kind, and a thruster is the machine that deletes that
interval.

Contained in theHuman. Its movie is ONE JUMP: crouch, drive, flight, land.
"""
from __future__ import annotations

import math

import numpy as np

# ── DEFINITIONAL AND MEASURED CONSTANTS. Each says where it comes from; the two that are literature
#    central values rather than laws say that too, and are listed again in story.md as still open.
G_EARTH = 9.80665            # standard gravity, CGPM 1901 -- definitional, not measured
G_MOON = 1.625               # lunar surface gravity, measured

# THE BALL OF THE FOOT sits at 0.72 of foot length from the heel -- the metatarsal break, and the
# "ball length" ratio the shoe-lasting trade has used for a century. Everything forward of it is
# 0.28 of the sole, and that is the whole contact patch once the heel is up. The ball is also the
# widest part of the foot, so the width does not need scaling with the fraction.
BALL_OF_FOOT_FRAC = 0.72
FOREFOOT_AREA_FRAC = 1.0 - BALL_OF_FOOT_FRAC

# ANKLE PLANTARFLEXION AT TAKE-OFF in a maximal vertical jump. A LITERATURE CENTRAL VALUE, not a
# derivation: reported peak take-off plantarflexion runs about 40-55 degrees, and 45 is taken. It is
# far beyond the ~26 degrees of walking, which is why a jump has an ankle term worth naming at all.
PLANTARFLEX_TAKEOFF_RAD = math.pi / 4.0

# FOOT LENGTH AS THE PARENT'S OWN ANTHROPOMETRY GIVES IT (ANSUR II median, and the number its own
# `foot_area_m2` is built from). Used HERE ONLY as a sensitivity: the parent's published forefoot
# lever implies a foot 35% longer than its published foot area does, and that disagreement moves
# this chapter's central answer across the line. See `takeoff_ansur_foot_margin`.
ANSUR_FOOT_LEN_FRAC = 0.1544

# THE FORCE PROFILE. Measured propulsive ground-reaction traces in a countermovement jump are close
# to a half sine, and a half sine has an exact peak-to-mean ratio of pi/2. That ratio, and the
# velocity and distance curves that come with it, are the only things taken from the shape.
PEAK_OVER_MEAN = math.pi / 2.0

# ── LITERATURE BANDS USED ONLY AS CHECKS. None of these enters a derivation, and none was widened
#    after a number came out. Two of the six are MISSED and the misses are reported as misses.
LIT_PEAK_POWER_W_PER_KG = (20.0, 50.0)     # peak centre-of-mass power, countermovement jump
LIT_TAKEOFF_GRF_BW = (2.0, 2.6)            # peak vertical ground reaction at take-off
LIT_STIFF_LANDING_GRF_BW = (4.0, 6.0)      # peak vertical ground reaction, stiff drop landing
LIT_PROPULSION_TIME_S = (0.25, 0.35)       # duration of the propulsive phase
LIT_TOTAL_WORK_J_PER_KG = (5.0, 8.0)       # total concentric centre-of-mass work
LIT_STIFF_LANDING_TRAVEL_M = (0.10, 0.15)  # centre-of-mass travel during a stiff landing
LIT_PUSH_OFF_TRAVEL_M = (0.30, 0.45)       # centre-of-mass travel during the push-off

FREE = {
    # HOW DEEP THE CROUCH IS. Countermovement depth is self-selected -- the clearest case in this
    # whole tree of a number a body CHOOSES rather than inherits -- and the choice costs either way:
    # deeper spreads the same work over more distance and lowers the peak force, shallower is
    # quicker and hits harder. 45 degrees of thigh-and-shank tilt is a knee flexed to about 90,
    # which is the measured self-selected depth.
    "crouch_rad": {"lo": 0.35, "hi": 1.20, "default": math.pi / 4.0,
                   "label": "crouch half-angle", "unit": "rad",
                   "local": "how deep to squat before a jump is a choice, not a law"},
    # HOW MUCH THE LANDING GIVES. The operator's control law says command the PROCESS and its STOP
    # CONDITION, never a position -- and a landing is exactly that. You do not aim your feet
    # anywhere; you decide how far you will travel before you stop, and the floor decides the rest.
    # 1.0 gives the landing the same range the push-off used; 0.0 is a stiff landing, which turns
    # out to BE the ankle alone.
    "landing_give": {"lo": 0.0, "hi": 1.0, "default": 1.0,
                     "label": "landing give", "unit": "of the push-off range",
                     "local": "how softly to land is a stop condition, and it is chosen"},
    # THE COEFFICIENT OF FRICTION, AND IT SHOULD NOT BE FREE. The physically correct source is the
    # ground's own angle of repose -- mu = tan(phi_repose) -- because a surface cannot resist a
    # shear steeper than the slope it will itself stand at. `theGround` derives and publishes
    # `repose_deg`. `theHuman` does not carry it, and a membrane may only read its parent, so this
    # chapter cannot reach it. THE MOMENT theHuman republishes repose_deg this entry is deleted and
    # the line becomes mu = tan(radians(parent["repose_deg"])). Until then: a measured central value
    # for a boot on dry compacted granular ground, with the honest band as the dial.
    "friction": {"lo": 0.30, "hi": 1.10, "default": 0.62,
                 "label": "shoe-on-ground friction", "unit": "ratio",
                 "local": "not a choice -- a number the chain cannot deliver yet"},
}


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE LAW
# ════════════════════════════════════════════════════════════════════════════════════════════════
def specific_work(g, h):
    """WHAT THE MUSCLE IS WORTH, recovered from what the parent published rather than typed again.

    The parent's jump law is h = w/g, so w = g*h returns its constant exactly. That matters more
    than it looks: it means there is no muscle number in this file that can drift out of step with
    the one above it, because there is no muscle number in this file."""
    return float(g) * float(h)


def takeoff_speed(w):
    """v = sqrt(2w). GRAVITY IS NOT IN IT.

    The muscle delivers a fixed energy per kilogram and all of it is kinetic at the instant the feet
    leave, so the SPEED a body leaves the ground at is a property of the body and identical on every
    world. What gravity changes is only how long the body stays up, and therefore how high it gets.
    A person on the Moon does not leave the ground faster; they leave it for longer."""
    return math.sqrt(2.0 * float(w))


def heel_rise(ball_lever, ankle_height, plantar):
    """HOW FAR THE ANKLE LIFTS THE WHOLE BODY when the heel comes up.

    The foot rotates about the BALL, not about the ankle, so the ankle -- and everything stacked on
    it -- swings up and slightly back on a lever of length `ball_lever`. And it sits `ankle_height`
    ABOVE the pivot plane, which costs a little of the rise back: the exact term is
    d*sin(a) - z*(1 - cos a), and the correction is 16% of the naive answer here. Small, and the
    kind of small that decides a 2% margin."""
    a = float(plantar)
    return float(ball_lever) * math.sin(a) - float(ankle_height) * (1.0 - math.cos(a))


def push_off_distance(leg_hip_to_ankle, crouch, ball_lever, ankle_height, plantar):
    """HOW FAR THE WORK GETS DONE OVER -- two joints in series, not one.

    The knee-and-hip term is the shortening of the hip-to-ankle line in a squat: thigh and shank
    each tilted `crouch` from vertical put the hip at L*cos(crouch), so the drop is L(1 - cos).
    The ankle term is the heel coming up, above.

    LEAVING THE ANKLE OUT IS NOT A ROUNDING ERROR. It is 29% of the push-off distance, and the
    DRIVING force goes as 1/distance for fixed work: drop the ankle term and the net drive comes out
    41% too high, the peak ground reaction 25% too high (the weight, which is the rest of it, does
    not care how far you push)."""
    s_knee = float(leg_hip_to_ankle) * (1.0 - math.cos(float(crouch)))
    s_ankle = heel_rise(ball_lever, ankle_height, plantar)
    return s_knee, s_ankle


def contact_time(s, v):
    """T = 2s/v, and it needs no assumption at all about the shape of the force.

    For ANY acceleration profile symmetric in time, the mean velocity through the push is exactly
    half the final velocity, so the distance is v*T/2 whatever the peak looks like. Constant
    acceleration, half sine and triangular all return the same T -- which is why this number is
    solid while the peak force below is only as good as the profile granted to it."""
    return 2.0 * float(s) / max(float(v), 1e-9)


def peak_force(m, g, v, s):
    """WHAT THE LEGS PUT THROUGH THE FLOOR.

        F_peak = m*g + (pi/2) * m * v^2 / (2s)

    The mean upward acceleration needed to reach v over s is v^2/(2s); a half sine peaks at pi/2 of
    its mean; and the ground carries the weight the whole time on top of that. The weight term is
    the SMALLER one, by a factor of two and a half -- which is the sentence this chapter turns on.
    A jump is not a weight. It is several."""
    a_mean = float(v) ** 2 / (2.0 * max(float(s), 1e-9))
    return float(m) * (float(g) + PEAK_OVER_MEAN * a_mean), a_mean


def fastest_countermovement(s_crouch, g):
    """HOW QUICKLY YOU CAN GET DOWN -- a BOUND, not a fit.

    The only forces on the centre of mass are gravity and the ground, and the ground can only PUSH.
    So the body CANNOT accelerate downwards faster than free fall. The quickest symmetric descent is
    therefore half the depth at exactly -g and half at +g: T = 2*sqrt(s/g).

    AND ITS GROUND REACTION IS ZERO FOR THE FIRST HALF. A maximally fast countermovement is a
    literal free fall: the feet carry nothing. Measured force traces show exactly that dip, never
    quite to zero, because nobody actually drops that fast."""
    return 2.0 * math.sqrt(max(float(s_crouch), 0.0) / max(float(g), 1e-9))


def travelled_push(u):
    """FRACTION OF THE PUSH-OFF DISTANCE COVERED at fraction u of the push-off TIME.

    Integrating the half-sine acceleration once gives v(u) = (v/2)(1 - cos pi u) and twice gives
    this. It is not decoration: it is what says WHEN the heel leaves the ground, and the heel-lift
    instant is where the ground pressure peaks."""
    u = min(max(float(u), 0.0), 1.0)
    return u - math.sin(math.pi * u) / math.pi


def travelled_land(u):
    """The same integral for a landing, where the body arrives at v and is brought to rest: the
    velocity runs (v/2)(1 + cos pi u), so distance accumulates fast and then slows."""
    u = min(max(float(u), 0.0), 1.0)
    return u + math.sin(math.pi * u) / math.pi


def _solve_frac(f, target, iters=60):
    """The u at which f(u) = target. Both curves above are monotone on [0, 1], so bisection is exact
    to machine precision and needs no library."""
    target = min(max(float(target), 0.0), 1.0)
    lo, hi = 0.0, 1.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def com_power(m, g, v, s, n=513):
    """PEAK MECHANICAL POWER AT THE CENTRE OF MASS: P = N*v, sampled along the push-off.

    Both factors are already derived -- the ground reaction from the half-sine profile, the velocity
    by integrating it -- so the peak is READ OFF the same curve that produced the force rather than
    estimated separately. N*v integrates to the FULL leg work, kinetic plus the lift through s,
    which is why the mean below is larger than (flight energy)/(contact time)."""
    a_mean = float(v) ** 2 / (2.0 * max(float(s), 1e-9))
    a_pk = PEAK_OVER_MEAN * a_mean
    T = contact_time(s, v)
    u = np.linspace(0.0, 1.0, n)
    vel = (a_pk * T / math.pi) * (1.0 - np.cos(math.pi * u))
    P = float(m) * (float(g) + a_pk * np.sin(math.pi * u)) * vel
    return float(P.max()), float(np.trapezoid(P, u * T) / T), a_pk, T


def slip_ceiling(mu, g):
    """THE MOST A BODY CAN ACCELERATE ON A SURFACE, and the most it can lean while doing it.

    Horizontal force cannot exceed mu*N, and on the flat N = mg, so a_max = mu*g -- MASS FALLS OUT.
    A heavy person and a light one accelerate identically, which is why a sprint start is technique
    rather than size.

    AND THE LEAN HAS NO GRAVITY IN IT EITHER. The ground reaction must lie inside the friction cone,
    so the angle it makes with vertical is at most arctan(mu): the same on Earth, here, and on the
    Moon. Only what that lean BUYS changes. If mu came from the ground's repose angle -- which is
    where it should come from -- this says something neater still: a body may accelerate up to
    exactly the slope the ground would stand at on its own."""
    return float(mu) * float(g), math.atan(float(mu))


def phase_state(nums, tau):
    """WHERE THE BODY IS AT TIME tau THROUGH ONE JUMP, and what the ground feels.

    Every phase duration is derived; the pose comes from the same crouch and plantarflexion the
    forces came from; the ground reaction is read from the SAME half sine that set the peak. There
    is no second model of a jump for drawing purposes, which is the entire reason emit() lives in
    this file."""
    t_c = float(nums["crouch_time_s"])
    t_p = float(nums["contact_time_s"])
    t_f = float(nums["flight_time_s"])
    t_l = float(nums["landing_time_s"])
    m, g, W = float(nums["mass_kg"]), float(nums["g"]), float(nums["weight_N"])
    crouch = float(nums["crouch_rad"])
    plantar = float(nums["plantarflex_rad"])
    L = float(nums["leg_hip_to_ankle_m"])
    s_knee = float(nums["push_off_knee_m"])
    v = float(nums["takeoff_speed_m_s"])
    A_flat = float(nums["contact_area_flat_m2"])
    A_fore = float(nums["contact_area_forefoot_m2"])
    u_lift = float(nums["heel_lift_at_frac"])
    u_down = float(nums["heel_down_at_frac"])

    tau = max(0.0, min(float(tau), t_c + t_p + t_f + t_l))
    if tau < t_c:
        phase, u = "crouch", tau / max(t_c, 1e-9)
    elif tau < t_c + t_p:
        phase, u = "push", (tau - t_c) / max(t_p, 1e-9)
    elif tau < t_c + t_p + t_f:
        phase, u = "flight", (tau - t_c - t_p) / max(t_f, 1e-9)
    else:
        phase, u = "land", (tau - t_c - t_p - t_f) / max(t_l, 1e-9)

    lift = 0.0
    if phase == "crouch":
        # THE BANG-BANG DESCENT: free fall at -g, then braked at +g. Distance is quadratic in each
        # half, and the ground reaction is zero and then two body weights -- both derived, and both
        # what a real force trace shows in softened form.
        d = (2.0 * u * u) if u < 0.5 else (1.0 - 2.0 * (1.0 - u) ** 2)
        phi, alpha, N = crouch * d, 0.0, (0.0 if u < 0.5 else 2.0 * W)
    elif phase == "push":
        # PROXIMAL TO DISTAL: the ankle's travel is the LAST part of the push, so the crouch
        # straightens over the whole drive and the heel comes up only at the end.
        a_pk = float(nums["peak_accel_m_s2"])
        N = m * (g + a_pk * math.sin(math.pi * u))
        phi = crouch * (1.0 - min(travelled_push(u) / max(travelled_push(u_lift), 1e-9), 1.0))
        alpha = plantar * (max(u - u_lift, 0.0) / max(1.0 - u_lift, 1e-9))
    elif phase == "flight":
        phi, alpha, N = 0.0, plantar, 0.0
        tt = u * t_f
        lift = v * tt - 0.5 * g * tt * tt          # ballistic: nothing to push on
    else:
        # DISTAL TO PROXIMAL, the reverse: the ankle absorbs first and the heel comes down early,
        # then the knee takes the rest. Which is why a soft landing is safe -- see the story.
        a_pk_l = float(nums["landing_peak_accel_m_s2"])
        N = m * (g + a_pk_l * math.sin(math.pi * u))
        alpha = plantar * (1.0 - min(u / max(u_down, 1e-9), 1.0))
        after = max(u - u_down, 0.0) / max(1.0 - u_down, 1e-9)
        phi = crouch * float(nums["landing_give_frac"]) * after

    area = 0.0 if phase == "flight" else (A_fore if alpha > 1e-6 else A_flat)
    press = (N / area) if area > 1e-9 else 0.0
    z_com = float(nums["com_height_m"]) - L * (1.0 - math.cos(phi)) \
        + heel_rise(nums["ball_lever_m"], nums["ankle_height_m"], alpha) + lift
    return {"phase": phase, "u": u, "crouch_rad": phi, "plantar_rad": alpha,
            "grf_N": N, "area_m2": area, "pressure_Pa": press, "com_m": z_com, "lift_m": lift}


def derive(parent, free):
    if parent is None or "jump_height_m" not in parent:
        raise ValueError("theThrust requires theHuman as its parent")
    free = free or {}
    crouch = float(free.get("crouch_rad", FREE["crouch_rad"]["default"]))
    give = float(free.get("landing_give", FREE["landing_give"]["default"]))
    mu = float(free.get("friction", FREE["friction"]["default"]))

    h_body = float(parent["height_m"])
    m = float(parent["mass_kg"])
    g = float(parent["g"])
    W = float(parent["weight_N"])
    com = float(parent["com_height_m"])
    leg = float(parent["leg_length_m"])
    h_jump = float(parent["jump_height_m"])
    foot_area = float(parent["foot_area_m2"])
    bearing = float(parent["ground_bearing_kPa"]) * 1e3
    ball_lever = float(parent["forefoot_lever_m"])
    heel_lever = float(parent["heel_lever_frac"]) * h_body
    ankle_z = float(parent["ankle_drop_frac"]) * h_body
    v_walk = float(parent["comfortable_speed_ms"])
    v_run = float(parent["walk_run_ms"])
    # the femur's strength, recovered from the parent's own two stress numbers rather than retyped
    bone_MPa = float(parent["femur_stress_running_MPa"]) * float(parent["bone_safety_factor"])
    stress_per_bw_MPa = float(parent["femur_stress_MPa"])

    # ── 1. WHAT A JUMP IS ────────────────────────────────────────────────────────────────────────
    w = specific_work(g, h_jump)                  # J/kg -- the parent's constant, recovered
    v = takeoff_speed(w)                          # and there is no g in it
    t_flight = 2.0 * v / g

    # ── 2. HOW FAR THE PUSH GOES ─────────────────────────────────────────────────────────────────
    L = leg - ankle_z                             # hip to ANKLE: the part of the leg that folds
    plantar = PLANTARFLEX_TAKEOFF_RAD
    s_knee, s_ankle = push_off_distance(L, crouch, ball_lever, ankle_z, plantar)
    s = s_knee + s_ankle

    # ── 3. THE FORCES ────────────────────────────────────────────────────────────────────────────
    T = contact_time(s, v)
    F_pk, a_mean = peak_force(m, g, v, s)
    P_pk, P_mean, a_pk, _ = com_power(m, g, v, s)
    t_crouch = fastest_countermovement(s_knee, g)
    s_land = s_ankle + give * s_knee
    t_land = contact_time(s_land, v)
    F_land, a_land_mean = peak_force(m, g, v, s_land)
    a_pk_land = PEAK_OVER_MEAN * a_land_mean
    F_stiff, _ = peak_force(m, g, v, s_ankle)     # A STIFF LANDING IS THE ANKLE ALONE

    A_flat_ = 2.0 * foot_area
    A_fore_ = A_flat_ * FOREFOOT_AREA_FRAC

    def landing_peak_pressure(gv):
        """THE WORST PRESSURE OF A LANDING that gives `gv` of the push-off range.

        Two candidates and the larger wins: the forefoot window before the heel comes down, and
        everything after it with both soles flat. Which of the two is worse SWITCHES as gv grows,
        which is why this is solved numerically rather than inverted -- an inverted closed form
        would silently be the wrong branch on one side of the switch."""
        sl = s_ankle + gv * s_knee
        Fl, am = peak_force(m, g, v, sl)
        apk = PEAK_OVER_MEAN * am
        ud = _solve_frac(travelled_land, min(s_ankle / max(sl, 1e-9), 1.0))
        return max(m * (g + apk * math.sin(math.pi * min(ud, 0.5))) / A_fore_, Fl / A_flat_)

    # HOW MUCH THE LANDING MUST GIVE, bisected. Pressure falls monotonically with give, so this is
    # a single number and it is the chapter's rule for landing on this world.
    lo_g, hi_g = 0.0, 1.0
    if landing_peak_pressure(1.0) <= bearing:
        for _ in range(50):
            mid = 0.5 * (lo_g + hi_g)
            if landing_peak_pressure(mid) > bearing:
                lo_g = mid
            else:
                hi_g = mid
        give_needed = hi_g
        give_suffices = True
    else:
        # NO AMOUNT OF GIVE IS ENOUGH, and `inf` was the honest answer to the wrong question.
        # A FRACTION LIVES IN 0..1; publishing infinity under a `_frac` name is a quantity docking
        # at an interface whose unit forbids its value -- the same misfold `story/folding.py audit`
        # caught in theLoad the day theGround stopped typing its cohesion. The soft-landing limit
        # is give = 1.0, so that is what the fraction says, and the SHORTFALL is published beside
        # it as a dimensionless ratio, which has no such bound.
        #
        # It is not an error state. On this world's real regolith -- 41.2 kPa, not the 110.4 kPa a
        # typed cohesion used to claim -- a landing from this body's own jump punches in HOWEVER
        # softly it is taken. That is a fact about the soil, and now it is one the numbers can say.
        give_needed = 1.0
        give_suffices = False
    over_ratio = landing_peak_pressure(1.0) / max(bearing, 1e-9)

    # WHEN THE HEEL LEAVES, AND WHEN IT COMES BACK DOWN. Derived, not chosen: the ankle owns the
    # last s_ankle of the push-off's distance and the first s_ankle of the landing's, and the
    # distance-versus-time curve above says what fraction of the TIME that is.
    u_lift = _solve_frac(travelled_push, 1.0 - s_ankle / max(s, 1e-9))
    u_down = _solve_frac(travelled_land, min(s_ankle / max(s_land, 1e-9), 1.0))

    # ── 4. WHETHER THE GROUND HOLDS IT ───────────────────────────────────────────────────────────
    # TWO feet, and TWO contact areas: both soles flat, and the two forefeet alone once the heel is
    # up. The parent's `foot_pressure_kPa` is one foot standing; a jump is on two.
    A_flat, A_fore = A_flat_, A_fore_
    # THE LARGEST FORCE WHILE THE CONTACT IS FOREFOOT-ONLY, and the guard here is load-bearing.
    # The force peaks at the middle of the push (sin is largest at u = 0.5). The forefoot window is
    # [u_lift, 1] going up and [0, u_down] coming down, so the worst instant inside each window is
    # its own edge ONLY IF the window misses the peak. Take the peak when the window contains it --
    # without that, a stiff landing (whose forefoot window is the WHOLE landing) reported the force
    # at touchdown, 43 kPa, and declared a 283 kPa overload safe.
    N_lift = m * (g + a_pk * math.sin(math.pi * max(u_lift, 0.5)))
    N_down = m * (g + a_pk_land * math.sin(math.pi * min(u_down, 0.5)))
    p_takeoff = N_lift / A_fore                             # the worst instant of the take-off
    p_takeoff_worst = F_pk / A_fore                         # ... if the heel lifted at the peak
    p_landing = max(N_down / A_fore, F_land / A_flat)
    p_stiff = F_stiff / A_fore                              # a toe landing with locked legs

    # THE SHALLOWEST CROUCH THIS GROUND WILL TOLERATE, solved rather than searched, under the WORST
    # case (heel-lift exactly at the force peak). Beneath it the take-off breaks the floor.
    s_needed = PEAK_OVER_MEAN * m * w / max(bearing * A_fore - m * g, 1e-9)
    cos_needed = 1.0 - max(s_needed - s_ankle, 0.0) / L
    crouch_needed = math.acos(max(min(cos_needed, 1.0), -1.0))
    # AND THE FALL A FLAT, STIFF LANDING SURVIVES: solve F_peak(v) = bearing*A_flat for the height.
    v2_max = (bearing * A_flat - m * g) * 2.0 * s_ankle / (PEAK_OVER_MEAN * m)
    drop_limit = max(v2_max, 0.0) / (2.0 * g)
    # THE SENSITIVITY THAT MATTERS MOST, and it is a disagreement inside the parent: its published
    # forefoot lever implies a foot 0.208 of stature, its published foot AREA is built from 0.1544.
    ball_short = max(BALL_OF_FOOT_FRAC * ANSUR_FOOT_LEN_FRAC * h_body - heel_lever, 1e-4)
    s_short = s_knee + heel_rise(ball_short, ankle_z, plantar)
    F_short, _ = peak_force(m, g, v, s_short)

    # ── 5. WHAT FRICTION ALLOWS ──────────────────────────────────────────────────────────────────
    a_max, lean = slip_ceiling(mu, g)
    a_max_earth, _ = slip_ceiling(mu, G_EARTH)
    # A LEAP: the take-off must stay inside the friction cone, so the projectile optimum of 45
    # degrees from horizontal is only reachable at mu >= 1. Below that, friction picks the angle.
    alpha_allowed = max(math.pi / 2.0 - lean, math.pi / 4.0)
    leap = v * v * math.sin(2.0 * alpha_allowed) / g
    leap_ideal = v * v / g

    # ── 6. THE PARENT'S JUMP LAW, CORRECTED. NOT USED ANYWHERE ABOVE. ────────────────────────────
    # The legs lift the body through s before the feet leave, and that work is not in w. Calibrate
    # the total on Earth -- where the parent's constant was measured -- and the same muscle then
    # gives more on every lighter world, by an amount the parent's law cannot express.
    w_total = w + G_EARTH * s

    def h_full(gg):
        return w_total / gg - s

    duration = t_crouch + T + t_flight + t_land
    return {
        # ITS REAL SIZE: the ceiling this jump needs. The crown of the head at the top of the
        # flight, with the toes pointed -- exactly height + heel-rise + jump height, and a corridor
        # shorter than this is a corridor nobody jumps in.
        "extent_m": h_body + s_ankle + h_jump,
        # ITS OWN DURATION: ONE JUMP, crouch to landing. Every one of the four terms is derived.
        "duration_s": duration,

        # ── the jump
        "muscle_work_per_mass": w,
        "muscle_work_J": w * m,
        "takeoff_speed_m_s": v,
        "jump_height_m": h_jump,
        "flight_time_s": t_flight,
        "apex_com_m": com + s_ankle + h_jump,

        # ── the push
        "crouch_rad": crouch,
        "crouch_deg": math.degrees(crouch),
        "plantarflex_rad": plantar,
        "leg_hip_to_ankle_m": L,
        "ball_lever_m": ball_lever,
        "heel_lever_m": heel_lever,
        "ankle_height_m": ankle_z,
        "trunk_length_m": h_body - (ankle_z + L),
        "push_off_knee_m": s_knee,
        "ankle_rise_m": s_ankle,
        "push_off_m": s,
        "ankle_share_of_push_frac": s_ankle / s,
        "contact_time_s": T,
        "crouch_time_s": t_crouch,
        "landing_time_s": t_land,
        "heel_lift_at_frac": u_lift,
        "heel_down_at_frac": u_down,

        # ── the forces
        "mean_accel_m_s2": a_mean,
        "peak_accel_m_s2": a_pk,
        "landing_peak_accel_m_s2": a_pk_land,
        "peak_force_N": F_pk,
        "peak_force_bodyweights_ratio": F_pk / W,
        "force_at_heel_lift_N": N_lift,
        "crouch_min_force_N": 0.0,
        "crouch_brake_force_N": 2.0 * W,
        "landing_force_N": F_land,
        "landing_force_bodyweights_ratio": F_land / W,
        "stiff_landing_force_N": F_stiff,
        "stiff_landing_bodyweights_ratio": F_stiff / W,
        "stiff_landing_travel_m": s_ankle,
        "landing_give_frac": give,
        "landing_travel_m": s_land,

        # ── the ground, asked directly
        "contact_area_flat_m2": A_flat,
        "contact_area_forefoot_m2": A_fore,
        "ground_bearing_kPa": bearing / 1e3,
        "takeoff_pressure_kPa": p_takeoff / 1e3,
        "takeoff_pressure_worst_kPa": p_takeoff_worst / 1e3,
        "takeoff_margin": bearing / p_takeoff,
        "takeoff_worst_margin": bearing / p_takeoff_worst,
        "takeoff_ansur_foot_margin": bearing * A_fore / F_short,
        "takeoff_ground_holds": p_takeoff <= bearing,
        "takeoff_holds_even_at_worst": p_takeoff_worst <= bearing,
        "landing_pressure_kPa": p_landing / 1e3,
        "landing_margin": bearing / p_landing,
        "landing_ground_holds": p_landing <= bearing,
        "landing_give_required_frac": give_needed,
        "landing_give_suffices": give_suffices,
        "landing_softest_overpressure_ratio": over_ratio,
        "landing_travel_required_m": s_ankle + give_needed * s_knee,
        "stiff_toe_landing_pressure_kPa": p_stiff / 1e3,
        "stiff_toe_landing_overload_ratio": p_stiff / bearing,
        "crouch_required_deg": math.degrees(crouch_needed),
        "crouch_shortfall_deg": math.degrees(crouch_needed - crouch),
        "flat_stiff_landing_drop_limit_m": drop_limit,
        # AND THE BONE IS NEVER THE PROBLEM. The same force through the femur, against the strength
        # the parent's own two stress numbers imply between them.
        "femur_stress_landing_MPa": stress_per_bw_MPa * (F_stiff / W),
        "femur_strength_MPa": bone_MPa,
        "bone_margin": bone_MPa / max(stress_per_bw_MPa * (F_stiff / W), 1e-9),

        # ── friction: the ceiling on every horizontal thing a body does
        "friction_coefficient_ratio": mu,
        "accel_max_m_s2": a_max,
        "accel_max_earth_m_s2": a_max_earth,
        "accel_vs_earth_ratio": a_max / a_max_earth,
        "max_lean_deg": math.degrees(lean),
        "time_to_walk_speed_s": v_walk / a_max,
        "time_to_run_speed_s": v_run / a_max,
        "stopping_distance_walk_m": v_walk ** 2 / (2.0 * a_max),
        "stopping_distance_run_m": v_run ** 2 / (2.0 * a_max),
        "stopping_distance_run_earth_m": v_run ** 2 / (2.0 * a_max_earth),
        "stopping_longer_than_earth_ratio": a_max_earth / a_max,
        "leap_m": leap,
        "leap_unlimited_m": leap_ideal,
        "leap_cost_of_friction_frac": 1.0 - leap / leap_ideal,

        # ── the power
        "peak_power_W": P_pk,
        "peak_power_per_mass": P_pk / m,
        "mean_power_W": P_mean,
        "mean_power_per_mass": P_mean / m,
        "leg_work_J": m * (w + g * s),
        "leg_work_per_mass": w + g * s,

        # ── GRAVITY AS A DIAL: the SAME body, three worlds
        "jump_height_earth_m": w / G_EARTH,
        "jump_height_moon_m": w / G_MOON,
        "flight_time_earth_s": 2.0 * v / G_EARTH,
        "flight_time_moon_s": 2.0 * v / G_MOON,

        # ── the correction handed UP to theHuman. Nothing above reads these.
        "leg_work_total_per_mass": w_total,
        "jump_height_full_work_m": h_full(g),
        "jump_height_full_work_earth_m": h_full(G_EARTH),
        "jump_height_full_work_moon_m": h_full(G_MOON),
        "jump_height_understated_frac": h_full(g) / h_jump - 1.0,

        # ── the thing a jump cannot do
        "unsteerable_time_s": t_flight,
        "unsteerable_jump_frac": t_flight / duration,

        # ── carried on
        "height_m": h_body,
        "mass_kg": m,
        "weight_N": W,
        "com_height_m": com,
        "g": g,
        "foot_area_m2": foot_area,
        "S_earth": float(parent["S_earth"]),
        "skin_albedo_rgb": [float(c) for c in parent["skin_albedo_rgb"]],
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- one jump, and the floor being asked to take it
# ════════════════════════════════════════════════════════════════════════════════════════════════
def emit(nums, t=1.0):
    """ONE JUMP: crouch, drive, flight, land. LOCAL UNITS: 1.0 is `extent_m`, the headroom the jump
    needs. +X is forward, +Z is up, the ground is z = 0, and the view is sagittal.

    EVERY DRAWN THING IS A DERIVED QUANTITY. There is nothing here for decoration:

      THE BODY, posed by the same crouch angle and plantarflexion the forces came from. The knee
      juts forward because a squat is a two-bar linkage with the hip held over the foot -- which is
      what keeps the centre of mass over the base, and is why the hip drops by L(1 - cos phi). The
      foot is TWO segments hinged at the ball, because that is where a foot actually bends: the heel
      section rotates, the forefoot stays flat on the ground, and so the contact patch you can see
      IS the area the pressure is divided by.

      THE CENTRE OF MASS as a bright mark on the body, and to the left, ITS HEIGHT PLOTTED AGAINST
      TIME. The horizontal axis of that curve is TIME, not space -- it is a graph, not a path -- and
      it shares the ground line as its zero. It sags through the crouch, climbs through the drive,
      arcs through the flight and sinks into the landing.

      THE GROUND REACTION as a bar, in body weights. IT GOES TO ZERO TWICE, and both zeroes are
      physics rather than convenience: once in the first half of the countermovement, because the
      fastest possible descent is a free fall and the feet genuinely carry nothing; and once in
      flight, because a body with no contact cannot push on anything at all. No single frame can
      tell you that, which is the reason a chapter is a film.

      THE RED TICK ACROSS THE BAR is what the ground can take RIGHT NOW -- bearing capacity times
      the contact area at this instant. It sits high while both soles are flat and DROPS by a factor
      of 3.6 the moment the heel lifts. Watching the white bar and the red tick approach each other
      is this chapter's whole argument, and it is invisible in a still."""
    from matter import blank, lit, SOLID, GLOW, AR, AG, AB

    total = float(nums["duration_s"])
    tau = min(max(float(t), 0.0), 1.0) * total
    st = phase_state(nums, tau)
    E = float(nums["extent_m"])
    L = float(nums["leg_hip_to_ankle_m"])
    seg = L / 2.0                                     # thigh and shank, equal
    ball = float(nums["ball_lever_m"])
    heel = float(nums["heel_lever_m"])
    ankle_z = float(nums["ankle_height_m"])
    trunk = float(nums["trunk_length_m"])
    phi, alpha = float(st["crouch_rad"]), float(st["plantar_rad"])
    lift = float(st["lift_m"])
    toe = ball + FOREFOOT_AREA_FRAC * (heel + ball) / BALL_OF_FOOT_FRAC

    # ── THE FOOT: hinged at the ball, which is where a foot bends. Heel section rotates by -alpha
    #    about the ball; forefoot stays on the ground. Ankle rides the rotating section.
    ca, sa = math.cos(-alpha), math.sin(-alpha)

    def about_ball(x, z):
        dx = x - ball
        return np.array([ball + dx * ca - z * sa, dx * sa + z * ca + lift])

    heel_pt = about_ball(-heel, 0.0)
    ball_pt = np.array([ball, lift])
    toe_pt = np.array([toe, lift])
    ankle = about_ball(0.0, ankle_z)
    knee = ankle + np.array([seg * math.sin(phi), seg * math.cos(phi)])
    hip = ankle + np.array([0.0, L * math.cos(phi)])
    shoulder = hip + np.array([0.0, trunk * 0.77])
    r_head = trunk * 0.115
    head = hip + np.array([0.0, trunk - r_head])       # crown lands exactly on height_m
    # ARM SWING: down and back through the crouch, up and through on the drive. Measured to be worth
    # about a tenth of jump height, and none of that tenth is in the parent's constant -- story.md.
    swing = {"crouch": -1.15 + 0.45 * st["u"], "push": -0.70 + 2.35 * st["u"],
             "flight": 1.65, "land": 1.65 - 2.50 * st["u"]}[st["phase"]]
    hand = shoulder + np.array([math.sin(swing), -math.cos(swing)]) * (trunk * 0.62)

    def bar(p0, p1, n, width=0.0):
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        u = np.linspace(0.0, 1.0, n)[:, None]
        line = p0[None, :] + (p1 - p0)[None, :] * u
        if width <= 0.0:
            return line
        d = p1 - p0
        nz = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-12)
        return np.concatenate([line + nz * width * f for f in (-1.0, -0.35, 0.35, 1.0)], 0)

    th = np.linspace(0.0, 2.0 * math.pi, 96)
    body = np.concatenate([
        bar(heel_pt, ball_pt, 54, 0.010),              # the heel section, hinged at the ball
        bar(ball_pt, toe_pt, 40, 0.008),               # the forefoot, flat on the floor
        bar(ankle, knee, 70, 0.026),                   # shank
        bar(knee, hip, 70, 0.032),                     # thigh
        bar(hip, shoulder, 90, 0.045),                 # trunk
        bar(shoulder, hand, 66, 0.018),                # arm
        np.stack([head[0] + r_head * np.cos(th), head[1] + r_head * np.sin(th)], 1),
    ], 0)

    P = [np.stack([body[:, 0], np.zeros(len(body)), body[:, 1]], 1)]
    kind = [np.zeros(len(body))]

    # ── THE GROUND
    gx = np.linspace(-0.46 * E, 0.42 * E, 250)
    P.append(np.stack([gx, np.zeros(250), np.zeros(250)], 1))
    kind.append(np.full(250, 1.0))

    # ── THE CONTACT PATCH: the part of the sole actually on the floor, coloured by how close the
    #    pressure under it is to what the floor can take. In flight it follows the sole and goes
    #    transparent -- nothing is pressing, so nothing is drawn pressing.
    x0 = heel_pt[0] if alpha <= 1e-6 else ball
    cx = np.linspace(x0, toe, 48)
    P.append(np.stack([cx, np.zeros(48), np.full(48, lift + 0.004)], 1))
    kind.append(np.full(48, 2.0))

    # ── THE CENTRE OF MASS, on the body
    P.append(np.array([[0.0, 0.0, st["com_m"]]]))
    kind.append(np.array([3.0]))

    # ── TWO CURVES AGAINST TIME, to the left. THESE ARE GRAPHS, NOT PATHS: x is TIME, and they
    #    share the ground line as their zero. The first is the centre of mass's height. The second
    #    is the PRESSURE under the feet, scaled so that the bearing capacity sits on a fixed red
    #    line -- which is the only way this chapter's event stays visible, because heel-lift lasts
    #    about one frame in forty-eight and the still that follows it would show nothing at all.
    NT = 160
    GX0, GW = -0.46 * E, 0.21 * E
    taus = np.linspace(0.0, tau, NT)
    hist = [phase_state(nums, tt) for tt in taus]
    gx_t = GX0 + GW * (taus / max(total, 1e-9))
    tr = np.zeros((NT, 3))
    tr[:, 0], tr[:, 2] = gx_t, [h["com_m"] for h in hist]
    P.append(tr)
    kind.append(np.full(NT, 4.0))

    bearing = float(nums["ground_bearing_kPa"]) * 1e3
    BEAR_Z = 0.20 * E                                  # where the bearing capacity is drawn
    pr = np.zeros((NT, 3))
    pr[:, 0] = gx_t
    pr[:, 2] = [min(h["pressure_Pa"] / bearing, 1.7) * BEAR_Z for h in hist]
    P.append(pr)
    kind.append(np.full(NT, 7.0))
    blx = np.linspace(GX0, GX0 + GW, 60)
    P.append(np.stack([blx, np.zeros(60), np.full(60, BEAR_Z)], 1))
    kind.append(np.full(60, 8.0))

    # ── THE GROUND REACTION, in body weights, and what the ground can take right now
    W = float(nums["weight_N"])
    bw = st["grf_N"] / W
    BW = 0.075 * E                                     # one body weight, drawn
    bx = 0.30 * E
    P.append(np.stack([np.full(130, bx), np.zeros(130), np.linspace(0.0, bw * BW, 130)], 1))
    kind.append(np.full(130, 5.0))
    lim = bearing * st["area_m2"] / W
    lx = np.linspace(bx - 0.032 * E, bx + 0.032 * E, 36)
    P.append(np.stack([lx, np.zeros(36), np.full(36, min(lim, 9.5) * BW)], 1))
    kind.append(np.full(36, 6.0))

    P = np.concatenate(P, 0) / E                       # INTO LOCAL UNITS: 1.0 is the headroom
    kind = np.concatenate(kind)

    n = len(P)
    b = blank(n)
    b[:, 0:3] = P
    nrm = np.zeros((n, 3), np.float32)
    nrm[:, 1] = -1.0                                   # sagittal: everything faces the camera
    b[:, 21:24] = nrm

    skin = np.asarray(nums.get("skin_albedo_rgb", [0.62, 0.44, 0.35]), np.float32)
    over = min(max(st["pressure_Pa"] / max(float(nums["ground_bearing_kPa"]) * 1e3, 1e-9), 0.0), 1.5)
    patch = np.clip([0.22 + 0.74 * over, 0.82 - 0.56 * over, 0.32 - 0.20 * over], 0.0, 1.0)
    alb = np.zeros((n, 3), np.float32)
    alb[kind == 0] = skin                                        # the body
    alb[kind == 1] = np.array([0.19, 0.20, 0.22], np.float32)    # the ground
    alb[kind == 2] = np.asarray(patch, np.float32)               # what is pressing, and how hard
    alb[kind == 3] = np.array([1.00, 0.74, 0.24], np.float32)    # the centre of mass, now
    alb[kind == 4] = np.array([0.52, 0.60, 0.82], np.float32)    # where the CoM has been
    alb[kind == 5] = np.array([0.86, 0.90, 0.98], np.float32)    # the ground reaction
    alb[kind == 6] = np.array([0.95, 0.24, 0.20], np.float32)    # what the ground can take NOW
    alb[kind == 7] = np.array([0.98, 0.62, 0.22], np.float32)    # the pressure, against time
    alb[kind == 8] = np.array([0.95, 0.24, 0.20], np.float32)    # ... and the line it may not cross

    S = float(nums.get("S_earth", 1.0))
    b[:, 16:19] = lit(alb, S * 0.85 + 0.15, e_ref=S, tone=0.45)
    b[:, AR:AB + 1] = alb
    a_ = np.where((kind == 4) | (kind == 7), 0.55, 0.96)
    a_ = np.where(kind == 8, 0.42, a_)
    # NO CONTACT, NO PATCH: in flight the sole is drawn by the body and nothing is pressing on it.
    b[:, 19] = np.where((kind == 2) & (st["area_m2"] <= 1e-9), 0.0, a_)
    b[:, 20] = np.where((kind == 3) | (kind == 6), 0.011, 0.0055)
    b[:, 11] = np.where((kind == 3) | (kind == 2), GLOW, SOLID)
    return b


def measure(nums):
    """THE CHECKS THIS CHAPTER WAS NOT FITTED TO.

    Every band below is used HERE and nowhere else -- not one of them entered a derivation -- so
    agreement is a prediction and disagreement is a fault. Both the number and the verdict are
    reported, because a bare boolean hides how close a near-miss was, and two of these ARE near
    misses. They are left failing, with their causes named in story.md."""
    lo, hi = LIT_PEAK_POWER_W_PER_KG
    return {
        # ── the unfitted checks
        "peak_power_per_mass": nums["peak_power_per_mass"],
        "peak_power_in_band": lo <= nums["peak_power_per_mass"] <= hi,
        "push_off_m": nums["push_off_m"],
        "push_off_in_band":
            LIT_PUSH_OFF_TRAVEL_M[0] <= nums["push_off_m"] <= LIT_PUSH_OFF_TRAVEL_M[1],
        "contact_time_s": nums["contact_time_s"],
        "contact_time_in_band":
            LIT_PROPULSION_TIME_S[0] <= nums["contact_time_s"] <= LIT_PROPULSION_TIME_S[1],
        "stiff_landing_travel_m": nums["stiff_landing_travel_m"],
        "stiff_travel_in_band":
            LIT_STIFF_LANDING_TRAVEL_M[0] <= nums["stiff_landing_travel_m"] <= LIT_STIFF_LANDING_TRAVEL_M[1],
        # THE ONE THAT CONVICTS THE PARENT: total concentric work, calibrated on Earth from the
        # parent's own jump height plus a push-off distance this chapter derived. Never aimed at the
        # band, and it lands inside it -- which is the evidence that the missing term is real.
        "leg_work_total_per_mass": nums["leg_work_total_per_mass"],
        "total_work_in_band":
            LIT_TOTAL_WORK_J_PER_KG[0] <= nums["leg_work_total_per_mass"] <= LIT_TOTAL_WORK_J_PER_KG[1],
        # ── the two that MISS, reported as misses with the size of the miss
        "peak_takeoff_bodyweights": nums["peak_force_bodyweights_ratio"],
        "takeoff_grf_in_band":
            LIT_TAKEOFF_GRF_BW[0] <= nums["peak_force_bodyweights_ratio"] <= LIT_TAKEOFF_GRF_BW[1],
        "takeoff_grf_over_band_top": nums["peak_force_bodyweights_ratio"] / LIT_TAKEOFF_GRF_BW[1],
        "stiff_landing_bodyweights": nums["stiff_landing_bodyweights_ratio"],
        "stiff_landing_in_band":
            LIT_STIFF_LANDING_GRF_BW[0] <= nums["stiff_landing_bodyweights_ratio"] <= LIT_STIFF_LANDING_GRF_BW[1],
        "stiff_landing_over_band_top":
            nums["stiff_landing_bodyweights_ratio"] / LIT_STIFF_LANDING_GRF_BW[1],

        # ── the laws that must hold EXACTLY, whatever the numbers are
        "takeoff_speed_gravity_free":
            abs(nums["takeoff_speed_m_s"] - math.sqrt(2.0 * nums["muscle_work_per_mass"])) < 1e-9,
        "flight_matches_jump_height":
            abs(nums["jump_height_m"] - nums["takeoff_speed_m_s"] ** 2 / (2.0 * nums["g"])) < 1e-9,
        "moon_over_here_is_the_g_ratio":
            abs(nums["jump_height_moon_m"] / nums["jump_height_m"] - nums["g"] / G_MOON) < 1e-9,
        "lean_is_arctan_mu":
            abs(math.tan(math.radians(nums["max_lean_deg"])) - nums["friction_coefficient_ratio"]) < 1e-12,
        "earth_correction_agrees_with_parent":
            abs(nums["jump_height_full_work_earth_m"] - nums["jump_height_earth_m"]) < 1e-9,
        "heel_lift_is_late": nums["heel_lift_at_frac"] > 0.5,

        # ── the answers to the questions this chapter was set
        "takeoff_ground_holds": nums["takeoff_ground_holds"],
        "takeoff_margin": nums["takeoff_margin"],
        "takeoff_holds_even_at_worst": nums["takeoff_holds_even_at_worst"],
        "takeoff_worst_margin": nums["takeoff_worst_margin"],
        "takeoff_ansur_foot_margin": nums["takeoff_ansur_foot_margin"],
        "landing_ground_holds": nums["landing_ground_holds"],
        "stiff_toe_landing_overload_ratio": nums["stiff_toe_landing_overload_ratio"],
        "flat_stiff_landing_drop_limit_m": nums["flat_stiff_landing_drop_limit_m"],
        "accel_vs_earth_ratio": nums["accel_vs_earth_ratio"],
        "bone_margin": nums["bone_margin"],
        # and its own rhythm needs no gearing: theHumanClock's band, like the ankle and the stride
        "jump_in_human_band": 0.04 <= nums["duration_s"] <= 10.0,
    }
