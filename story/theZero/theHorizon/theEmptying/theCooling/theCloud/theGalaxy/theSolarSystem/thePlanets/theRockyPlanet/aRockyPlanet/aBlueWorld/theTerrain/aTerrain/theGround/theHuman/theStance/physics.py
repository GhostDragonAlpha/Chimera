"""theStance -- standing still, which is not a state but a process that never stops.

THE EDGE. The parent solved balance for a body that is MOVING: a stride, a capture point, a walk-run
transition. It never asked the quieter question underneath -- what is a body standing on, how far can
it be pushed before it has to move, and what does holding a wide stance cost. That is this chapter.

WHAT A STANCE IS. Three things, and only the first is geometry:

    THE BASE OF SUPPORT -- the convex hull of whatever touches the ground. Two feet make a rectangle
    as long as a foot and as wide as the feet are apart. It is the region the ground can push from,
    and nothing outside it can be pushed from at all.

    THE MARGIN OF STABILITY (Hof, Gazendam & Sinke 2005) -- and this is the part that makes standing
    a process. A body is not stable because its centre of mass is inside its base; it is stable
    because its EXTRAPOLATED centre of mass is. XcoM = com + v/omega0: where the CoM is going, given
    where it is and how fast it is already moving. A body dead still at the edge of its base is safe;
    a body at the centre moving fast is not. The margin b = (edge - XcoM) is a LENGTH, and b*omega0
    is the velocity a shove may impart before the stance is lost -- so a stance has a measurable
    tolerance to a push, in metres per second and in newton-seconds.

    THE COST -- a wide stance buys margin and pays for it twice: the hips must hold the legs out
    (torque) or the ground must hold the feet in (friction), and the CoM has further to travel
    before a foot can be lifted. Both are derived here, and neither is free.

WHAT THIS CHAPTER MEASURED FOR ITSELF, and it changed one of the parent's numbers.

    The parent's `fall_rate_rad_s = sqrt(g/H)` is the POINT-MASS inverted pendulum. A real body is
    not a point: it has inertia about its own centre, which slows the topple. 261 quiet-standing
    force-plate trials (HBEDB, below) measure the real omega0 directly from force and centre of
    pressure -- using no anthropometry at all -- and it comes out **0.913 of the point-mass value**.
    Two idealisations bracket that number and neither was fitted to anything:

        a point mass at the CoM        1.000       (no inertia to slow it)
        a uniform rod, CoM at mid      0.866       ( = sqrt(3)/2, pure geometry)
        MEASURED, 261 trials           0.913       almost exactly between them

    So this chapter republishes `fall_rate_rad_s` as the corrected one and keeps the parent's under
    `fall_rate_point_mass_rad_s`. The correction is DIMENSIONLESS -- it is a property of how a body's
    mass is arranged, not of gravity -- which is why a measurement made on Earth is allowed to travel
    to a world with g = 7.076.

THE UNFITTED CHECKS (three, and all three are reported whichever way they fall -- see `measure()`):

    1. Put the CoM at the fore-aft middle of the foot, which is the position that maximises the
       smaller of the two sagittal margins. Nothing about quiet standing goes into that. It lands
       **47.8 mm ahead of the ankle** -- the 40-60 mm anterior offset quiet standing is measured at.
    2. The body's only time scale is 1/omega0. If sway has no clock of its own it must run at O(omega0),
       and the plates say **0.42 and 0.54 of omega0/2pi** on the two axes: about half the pendulum's
       own frequency, no fitting, no free parameter.
    3. Read foot length and breadth off ANSUR II, multiply them, and the product must equal the
       `foot_area_m2` the parent already published from its own read. It agrees to 1e-12.

WHAT IS STILL A STUB HERE. The other postures the story asks for are NOT derived and are not
pretended to be -- crouch, prone, the combat slide, corner lean, mantle. Each changes the contact
patch and the CoM height and so re-runs everything above with different numbers; none of it is
written. This chapter is STANDING, and standing only.

    * Low Profile Stance [Left Ctrl], Prone [X], Combat Slide, Corner Peek [Q/E], Mantle [Space]

THE STORY'S VERBS THAT LAND HERE AND ARE NOW DERIVED:
    * Deploy Bipod / Brace [Y]      -- the braced stance, its margin, and what the hips pay for it
    * Steady Aim [Left Shift]       -- the sway a held aim is fighting, in metres and in hertz
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np

# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MEASUREMENTS THIS CHAPTER STANDS ON
# ════════════════════════════════════════════════════════════════════════════════════════════════
# ── HBEDB / BDS. Santos DA & Duarte M (2016), "A public data set of human balance evaluations",
#    PeerJ 4:e2648, CC BY 4.0. Mirrored in this repo at
#    research_references/human/balance/hbedb_balance_figshare.zip (1,930 trials, 163 subjects).
#
#    THE SUBSET, stated because a subset is a choice: AgeGroup=Young, Vision=Open, Surface=Firm --
#    261 trials, 60 s each at 100 Hz, mean stature 1.667 m, mean mass 61.60 kg taken from the plate's
#    own Fz rather than from the questionnaire. Each trial mean-removed and linearly detrended (a
#    60 s drift is not sway), then: RMS per axis, resultant path speed, and the median power
#    frequency between 0.05 and 5 Hz.
#
#    THE AXES ARE NOT LABELLED IN THE DISTRIBUTED FILES. The columns are COPx and COPy with no key,
#    so the assignment below is made from the SIGNATURE and is stated as such: the larger, slower
#    axis is taken to be anteroposterior (the ankle carries it, and an ankle is slow) and the
#    smaller, faster one mediolateral (two feet share the load between them, which is quick). If
#    that is backwards then two labels swap and NO derived number moves -- the amplitude law uses
#    the resultant, and the movie uses both frequencies.
HBEDB_N_TRIALS = 261
HBEDB_COM_HEIGHT_M = 0.958300      # 0.575 * mean stature 1.66661 m -- the reference this scales from
HBEDB_RMS_AP_M = 3.802283e-3       # RMS of the larger, slower axis
HBEDB_RMS_ML_M = 2.506670e-3       # ... and of the smaller, faster one
HBEDB_RMS_RESULTANT_M = 4.623243e-3   # per-trial resultant, then averaged (not the sum of the above)
HBEDB_SPEED_M_S = 8.801447e-3      # mean COP path speed
HBEDB_F50_AP_HZ = 0.195382         # median power frequency, larger/slower axis
HBEDB_F50_ML_HZ = 0.253166         # ... smaller/faster axis

# ── omega0 MEASURED FROM THE SAME PLATES, and this is the number that corrects the parent.
#    The single-inverted-pendulum relation a_com = omega0^2 (com - cop) has both of its left-hand
#    terms on the plate: a_com = F_horizontal / m by Newton, cop from the moments. And com needs no
#    model either -- COM(w) = -A(w)/w^2, because acceleration IS the second derivative. So omega0^2
#    is the only unknown and it is a one-parameter least squares, fitted over 0.3-3.0 Hz, the band
#    the sway power actually lives in.
#
#    IT WAS FITTED TEN TIMES -- five frequency bands x two axes -- and the value used is the MEAN
#    OF ALL TEN, so that no band is doing the work and none had to be chosen:
#        (0.3,1.0) 2.817/2.918   (0.5,2.0) 2.971/2.984   (0.8,3.0) 3.063/2.988
#        (0.3,3.0) 2.900/2.941   (1.0,4.0) 3.146/2.979    rad/s
#    Mean 2.9708, full spread 2.817 to 3.146 (+-5.5%), which carries into the correction as
#    0.881 to 0.983 -- still inside the two brackets below at either end.
#
#    A FIRST VERSION OF THIS MEASUREMENT WAS WRONG and is recorded because it was nearly believed:
#    taking the ratio a_com/cop at high frequency and calling the CoM stationary measures
#    omega0^2 * w^2/(w^2+omega0^2), which is 16% low at 1 Hz. It returned exactly the uniform rod's
#    4/3 and looked like a beautiful result. It was an artifact of the approximation.
HBEDB_OMEGA0_MEASURED = 2.970752   # rad/s, mean of ten fits (5 bands x 2 axes)
HBEDB_OMEGA0_POINT_MASS = 3.198965  # sqrt(9.80665 / 0.958300) -- what a point mass would give
INERTIA_CORRECTION = HBEDB_OMEGA0_MEASURED / HBEDB_OMEGA0_POINT_MASS      # 0.9287

# THE TWO BRACKETS, computed from geometry alone and fitted to nothing.
# A rigid body toppling about a ground contact has an equivalent pendulum length h_eff = L(1+rho^2/L^2)
# where rho is its radius of gyration about the CoM, so the correction is 1/sqrt(1+(rho/L)^2).
CORRECTION_POINT_MASS = 1.0                    # rho = 0
CORRECTION_UNIFORM_ROD = math.sqrt(3.0) / 2.0  # rho/L = 1/sqrt(3) for a rod standing on its end

G_EARTH_MS2 = 9.80665                          # CGPM 1901 standard gravity, the plates' own g

_HERE = Path(__file__).resolve()


def _walk_up(*parts) -> Path:
    """Find a measured-data file by walking up to the repo root. The same move theHuman makes for
    ANSUR -- a measurement lives once and every membrane that needs it reads THAT file."""
    for q in _HERE.parents:
        f = q.joinpath(*parts)
        if f.exists():
            return f
    raise FileNotFoundError("/".join(parts) + " -- not found above " + str(_HERE))


def _ansur() -> dict:
    """ANSUR II (US Army Anthropometric Survey 2012, public release 2017): 4,082 male + 1,986 female
    subjects, 93 measures, distilled to anchors by tools/build_ansur_anchors.py.

    THIS CHAPTER NEEDS THE FOOT and the parent does not publish its shape -- only its area. A base of
    support is a POLYGON, so an area is not enough: 0.0276 m^2 is a foot and it is also a dinner
    plate, and the two do not hold a body up the same way."""
    return json.loads(_walk_up("research_references", "human", "ansur_anchors.json")
                      .read_text(encoding="utf-8"))["male"]


def _myo_hip() -> dict:
    """THE PELVIS, from the musculoskeletal model this studio already walks on.

    MyoSuite's myoLegs (vendored at vendor/myo_sim, an OpenSim gait model converted to MJCF) places
    the two femur bodies at +-0.07726 m either side of the pelvis origin, and chains femur -> tibia
    -> talus with measured segment lengths. That gives two things nothing else here has: the
    separation of the HIP JOINTS (not of the soft tissue over them, which is what a tape measure
    gets), and the hip's own measured range of abduction.

    WHY IT MATTERS: the stance that costs the hips NOTHING is the one with the feet directly under
    the hip joints. Without this file that width would have to be assumed, and the honest form of an
    assumption here is a different number entirely."""
    p = _walk_up("vendor", "myo_sim", "leg", "assets", "myolegs_chain.xml")
    txt = p.read_text(encoding="utf-8", errors="replace")

    def attr(tag, name, want):
        """One attribute off one named element. ORDER-AGNOSTIC on purpose: the first version of this
        assumed `name` came first and found the bodies but not the joints, which write
        `axis` before `name`. An XML attribute order is not a contract."""
        m = re.search(r'<%s\b[^>]*\bname="%s"[^>]*/?>' % (tag, name), txt)
        if not m:
            raise KeyError("%s %r not in %s" % (tag, name, p.name))
        v = re.search(r'\b%s="([-0-9.eE ]+)"' % want, m.group(0))
        if not v:
            raise KeyError("%s on %s %r not in %s" % (want, tag, name, p.name))
        return [float(x) for x in v.group(1).split()]

    def body_pos(name):
        return attr("body", name, "pos")

    def joint_range(name):
        lo, hi = attr("joint", name, "range")
        return lo, hi

    fr, fl = body_pos("femur_r"), body_pos("femur_l")
    tib, tal = body_pos("tibia_r"), body_pos("talus_r")
    lo, _hi = joint_range("hip_adduction_r")   # OpenSim sign: adduction +, so the LOW end is abduction
    return {
        "hip_separation_m": abs(fr[2] - fl[2]),                 # 0.15452
        "femur_m": abs(tib[1]),                                 # 0.404425
        "tibia_m": abs(tal[1]),                                 # 0.400
        "hip_to_ankle_m": abs(tib[1]) + abs(tal[1]),            # 0.804425
        "abduction_limit_rad": abs(lo),                         # 0.8727 = 50 deg
        "source": "MyoSuite myo_sim leg/assets/myolegs_chain.xml (OpenSim gait model, MJCF)",
    }


FREE = {
    # HOW HARD THE HIPS ARE WILLING TO WORK TO STAND WIDE. The stance width itself is NOT free --
    # it is what this effort buys, given the body's weight and leg length. 1.0 means "spend on
    # standing wide exactly what the ankles already spend on pushing off", which is the widest
    # stance a body holds without the stance becoming the effort.
    "brace_effort": {"lo": 0.0, "hi": 3.0, "default": 1.0,
                     "label": "brace effort", "unit": "of the ankle's own push-off torque",
                     "local": "how wide to stand is a choice; what it costs is not"},
}


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE LAWS
# ════════════════════════════════════════════════════════════════════════════════════════════════
def extrapolated_com(com, vel, omega0):
    """HOF'S XcoM -- where the centre of mass is GOING.

    A body leaning at 5 cm and dead still recovers by doing nothing. The same body at 5 cm moving at
    0.2 m/s does not. The difference is v/omega0: the distance the CoM will still travel before an
    inverted pendulum can stop it, which for a pendulum is exactly its velocity times its own time
    constant. Hof, Gazendam & Sinke, J Biomech 38:1-8 (2005).

    This is also why standing is a PROCESS and not a state: XcoM depends on a velocity, and a
    velocity has to be measured continuously or it is not known at all."""
    return np.asarray(com, float) + np.asarray(vel, float) / float(omega0)


def margin(half_extent, xcom):
    """How much base is left, in metres, along one axis. Negative means it is already gone."""
    return float(half_extent) - abs(float(xcom))


def push_survivable(b, omega0, mass):
    """THE SHOVE A STANCE SURVIVES, from a margin.

    Set XcoM at the boundary and solve for the velocity that puts it there: v = b*omega0. That is
    the fastest the CoM may be travelling and still be stoppable without moving a foot -- so a
    stance's tolerance is a VELOCITY first, and everything else follows from the body's mass.

    Returns (velocity, kinetic energy). THE IMPULSE m*v IS THE MORE NATURAL CURRENCY -- a force
    means nothing without a duration, and impulse is what a shove actually delivers -- but N.s is
    not in `story/folding.py`'s unit table, and publishing a number under a unit nothing can check
    is how this project got a Kelvin into a Celsius column. So the same fact is published twice in
    units that ARE checkable, a velocity and an energy, and the impulse is one multiplication away
    from `mass_kg`."""
    v = float(b) * float(omega0)
    return v, 0.5 * float(mass) * v * v


def hip_torque_for_offset(weight_N, offset_m):
    """A leg held out sideways is a lever on the hip. One leg carries half the weight, so the moment
    the hip must hold is (W/2) * (lateral distance from the hip joint to the foot). This is the
    ZERO-FRICTION solution: the ground pushes straight up and the hip does all the work."""
    return 0.5 * float(weight_N) * abs(float(offset_m))


def friction_for_offset(offset_m, hip_height_m):
    """...and the ZERO-TORQUE solution, the other end of the same trade. If the leg carries its load
    along its own axis like a strut, the hip needs no moment at all and the ground must instead stop
    the foot sliding outward: the reaction runs along the leg, so its horizontal-to-vertical ratio
    is offset/height, and that ratio IS the coefficient of friction required.

    A real stance sits somewhere on the line between the two. Both ends are published because the
    stance is legal if EITHER end is affordable, and this chapter cannot see the ground's mu -- it is
    not in anything the parent hands down. So the requirement is published and the ground decides,
    which is this project's rule about commanding a process and never a position."""
    return abs(float(offset_m)) / max(float(hip_height_m), 1e-9)


def time_to_unload(travel_m, cop_reach_m, omega0):
    """HOW LONG BEFORE A FOOT CAN LEAVE THE GROUND -- the cost of a wide stance, in seconds.

    To lift a foot the body must first get its CoM over the OTHER one. It does that by pushing the
    centre of pressure to the far side and letting itself fall the right way: with the CoP a distance
    c from the CoM, the pendulum gives com(t) = c(cosh(omega0 t) - 1), so travelling a distance a
    takes  t = arccosh(1 + a/c) / omega0.

    Everything in that is already derived -- c is how far the CoP can reach (the outer edge of the
    far foot), a is half the stance width, and omega0 is the body's own toppling rate. Stand wider
    and a grows faster than c does, so the time goes up. That is the whole trade in one line."""
    a, c = abs(float(travel_m)), max(abs(float(cop_reach_m)), 1e-9)
    return math.acosh(1.0 + a / c) / float(omega0)


def derive(parent, free):
    if parent is None or "com_height_m" not in parent:
        raise ValueError("theStance requires theHuman as its parent")
    free = free or {}
    effort = float(free.get("brace_effort", FREE["brace_effort"]["default"]))

    h = float(parent["height_m"])
    m = float(parent["mass_kg"])
    g = float(parent["g"])
    W = float(parent["weight_N"])
    L = float(parent["com_height_m"])          # CoM above the GROUND -- the CoP is on the ground
    leg = float(parent["leg_length_m"])        # hip height above the ground
    tau_ankle = float(parent["ankle_torque_Nm"])
    step_len = float(parent["step_length_m"])
    step_t = float(parent["step_time_s"])
    walk_v = float(parent["comfortable_speed_ms"])
    ankle_h = float(parent["ankle_drop_frac"]) * h
    heel_back = float(parent["heel_lever_frac"]) * h    # the ankle sits this far ahead of the heel

    # ── THE FOOT, from ANSUR, as FRACTIONS of stature so the slider still works ─────────────────
    an = _ansur()
    f_len_frac = an["foot_length_m"]["median"] / an["stature_m"]["median"]
    f_brd_frac = an["foot_breadth_m"]["median"] / an["stature_m"]["median"]
    f_len, f_brd = f_len_frac * h, f_brd_frac * h

    # ── THE PELVIS, from the musculoskeletal model ───────────────────────────────────────────────
    myo = _myo_hip()
    hip_over_shank = myo["hip_separation_m"] / myo["hip_to_ankle_m"]
    hip_to_ankle = leg - ankle_h                       # this body's own hip-to-ankle length
    hip_sep = hip_over_shank * hip_to_ankle
    hip_half = 0.5 * hip_sep

    # ── THE PENDULUM, corrected by what the plates measured ──────────────────────────────────────
    w0_point = float(parent["fall_rate_rad_s"])        # the parent's point-mass rate
    w0 = w0_point * INERTIA_CORRECTION                 # ...and the body's real one
    rho_over_L = math.sqrt(1.0 / INERTIA_CORRECTION ** 2 - 1.0)
    rho = rho_over_L * L

    # ── THE STANCES ──────────────────────────────────────────────────────────────────────────────
    # A stance is named by ONE number: how far each foot's centre sits from the midline.
    #   together  -- the feet touching, which is as narrow as a body gets
    #   natural   -- the step width the parent's own gait measurement recorded
    #   braced    -- as wide as `brace_effort` of the ankle's push-off torque will hold the legs out
    brace_offset = effort * 2.0 * tau_ankle / W        # lateral distance from HIP to foot
    stances = {
        "together": 0.5 * f_brd,
        "natural": 0.5 * float(parent["measured_step_width_m"]),
        "braced": hip_half + brace_offset,
    }

    out = {}
    for name, centre in stances.items():
        half_w = centre + 0.5 * f_brd                  # the outer edge of the outer foot
        half_l = 0.5 * f_len                           # fore-aft, and it never changes with width
        off = centre - hip_half                        # + is abducted, - is adducted
        # the hip drops as the leg goes out sideways -- the leg length is fixed, so the height is not
        hip_h = math.sqrt(max(hip_to_ankle ** 2 - off ** 2, 0.0)) + ankle_h
        v_lat, e_lat = push_survivable(half_w, w0, m)
        v_fore, e_fore = push_survivable(half_l, w0, m)
        out.update({
            f"{name}_foot_centre_m": centre,
            f"{name}_half_width_m": half_w,
            f"{name}_width_m": 2.0 * half_w,
            f"{name}_half_length_m": half_l,
            f"{name}_area_m2": 2.0 * half_w * f_len,
            f"{name}_hip_offset_m": off,
            f"{name}_hip_abduction_deg": math.degrees(math.asin(
                min(abs(off) / max(hip_to_ankle, 1e-9), 1.0))) * (1.0 if off >= 0 else -1.0),
            f"{name}_hip_torque_Nm": hip_torque_for_offset(W, off),
            f"{name}_friction_required_ratio": friction_for_offset(off, hip_h),
            f"{name}_margin_lateral_m": half_w,        # from the centre, at rest: the margin IS half
            f"{name}_margin_fore_aft_m": half_l,
            f"{name}_push_velocity_lateral_ms": v_lat,
            f"{name}_push_velocity_fore_aft_ms": v_fore,
            f"{name}_push_energy_lateral_J": e_lat,
            f"{name}_push_energy_fore_aft_J": e_fore,
            # the cost: the CoM must cross to the far foot before the near one can lift
            f"{name}_step_ready_s": time_to_unload(centre, half_w, w0),
        })

    # THE HIP'S OWN CEILING, and the ground's. Two different things stop a stance widening, and it
    # is worth knowing which one arrives first.
    off_hip_max = hip_to_ankle * math.sin(myo["abduction_limit_rad"])
    hip_h_max = math.sqrt(max(hip_to_ankle ** 2 - off_hip_max ** 2, 0.0)) + ankle_h

    # ── THE SWAY ─────────────────────────────────────────────────────────────────────────────────
    # WHAT TRANSFERS BETWEEN BODIES IS AN ANGLE, not a distance. A lean of theta puts the CoM
    # L*theta off centre, so a taller body sways further for the same lean; the plates measure the
    # distance and dividing by their own CoM height turns it into the invariant.
    lean_ap = HBEDB_RMS_AP_M / HBEDB_COM_HEIGHT_M
    lean_ml = HBEDB_RMS_ML_M / HBEDB_COM_HEIGHT_M
    lean_r = HBEDB_RMS_RESULTANT_M / HBEDB_COM_HEIGHT_M
    rms_ap, rms_ml, rms_r = lean_ap * L, lean_ml * L, lean_r * L

    # AND WHAT TRANSFERS FOR THE RATE IS omega0. The body carries no other clock: no spring, no
    # resonance, nothing tuned -- so a frequency measured on Earth moves to this world by the ratio
    # of the two omega0. On a world with less gravity every part of standing runs slower.
    rate_over_w0 = (HBEDB_SPEED_M_S / HBEDB_RMS_RESULTANT_M) / HBEDB_OMEGA0_MEASURED
    f_ap = HBEDB_F50_AP_HZ * w0 / HBEDB_OMEGA0_MEASURED
    f_ml = HBEDB_F50_ML_HZ * w0 / HBEDB_OMEGA0_MEASURED
    sway_speed = rate_over_w0 * w0 * rms_r
    pend_hz = w0 / (2.0 * math.pi)

    # what the same body would do on Earth -- the gravity comparison, same body, one number changed
    w0_earth = math.sqrt(G_EARTH_MS2 / L) * INERTIA_CORRECTION

    extent = math.hypot(out["braced_half_width_m"], out["braced_half_length_m"])
    return {
        # ITS SIZE: the half-diagonal of the widest base of support it derives. A stance IS a region
        # on the ground, so its extent is that region -- not the body standing in it.
        "extent_m": extent,
        # ITS CLOCK: one full cycle of the slower sway axis. A stance has no stride and no step; the
        # only thing that repeats while a body holds still is its own wander.
        "duration_s": 1.0 / f_ap,

        # ── the pendulum, corrected ──────────────────────────────────────────────────────────────
        "fall_rate_rad_s": w0,
        "fall_rate_point_mass_rad_s": w0_point,
        "inertia_correction_factor": INERTIA_CORRECTION,
        "inertia_correction_point_mass_factor": CORRECTION_POINT_MASS,
        "inertia_correction_uniform_rod_factor": CORRECTION_UNIFORM_ROD,
        "radius_of_gyration_m": rho,
        "radius_of_gyration_over_com_ratio": rho_over_L,
        "radius_of_gyration_frac": rho / h,
        # THE WHOLE BODY'S rotational inertia about its own CoM, which is what the correction above
        # is a measurement OF. It trips H1.02/H1.04 in the physics catalog, and the trip is worth
        # keeping: those signatures ask for a SEGMENT inertia (regime <= 10 kg.m2) but their key
        # fragment is the bare word "inertia", so a whole body docks into a thigh's socket. A site
        # that binds everything is a site not doing its job -- reported, not renamed around.
        "whole_body_inertia_kgm2": m * rho * rho,
        "time_to_fall_s": 1.0 / w0,
        "time_to_fall_point_mass_s": 1.0 / w0_point,
        "omega0_measured_source": ("HBEDB/BDS 261 quiet-stance trials, Santos & Duarte 2016 PeerJ "
                                   "4:e2648 CC BY 4.0; one-parameter fit of a_com = w0^2(com-cop) "
                                   "over 0.3-3.0 Hz, +-5% across five bands"),

        # ── the foot and the pelvis ──────────────────────────────────────────────────────────────
        "foot_length_m": f_len,
        "foot_breadth_m": f_brd,
        "foot_area_m2": f_len * f_brd,
        # ...and the parent's own read of the same measurement, carried so `measure()` can put the
        # two side by side. A cross-check that cannot see both numbers is not a cross-check.
        "parent_foot_area_m2": float(parent["foot_area_m2"]),
        "foot_length_frac": f_len_frac,
        "foot_breadth_frac": f_brd_frac,
        "hip_separation_m": hip_sep,
        "hip_separation_over_leg_ratio": hip_over_shank,
        "hip_to_ankle_m": hip_to_ankle,
        "ankle_height_m": ankle_h,
        "ankle_ahead_of_heel_m": heel_back,
        # THE UNFITTED ONE: the fore-aft centre of the base is where the smaller sagittal margin is
        # largest, and it lands where quiet standing is measured to put the CoM.
        "com_ahead_of_ankle_m": 0.5 * f_len - heel_back,
        "anthropometry_source": ("ANSUR II 2012 (4,082 males) for the foot; MyoSuite myo_sim "
                                 "myolegs_chain.xml for the hip joints and their range"),

        # ── the three stances ────────────────────────────────────────────────────────────────────
        **out,
        "brace_effort_ratio": effort,
        "brace_offset_m": brace_offset,
        "hip_limit_offset_m": off_hip_max,
        "hip_limit_abduction_deg": math.degrees(myo["abduction_limit_rad"]),
        "hip_limit_width_m": 2.0 * (hip_half + off_hip_max + 0.5 * f_brd),
        "hip_limit_friction_required_ratio": friction_for_offset(off_hip_max, hip_h_max),
        "braced_over_together_margin": out["braced_half_width_m"] / out["together_half_width_m"],
        "braced_step_delay_s": out["braced_step_ready_s"] - out["together_step_ready_s"],
        "braced_step_delay_ratio": (out["braced_step_ready_s"]
                                    - out["together_step_ready_s"]) / step_t,

        # ── the push, once a step is allowed ─────────────────────────────────────────────────────
        # Hof's rule for a recovery step: the foot must land at or beyond the XcoM, so the base is
        # not the feet you have but the feet you can REACH. One step forward extends it by a stride's
        # half -- and that is why a body can absorb far more when it is allowed to move.
        "step_reach_m": step_len,
        "push_velocity_with_step_ms": (0.5 * f_len + step_len) * w0,
        "push_energy_with_step_J": 0.5 * m * ((0.5 * f_len + step_len) * w0) ** 2,
        "step_time_s": step_t,
        "push_velocity_over_walk_ratio": ((0.5 * f_len + step_len) * w0) / walk_v,

        # ── the sway ─────────────────────────────────────────────────────────────────────────────
        "sway_rms_m": rms_r,
        "sway_rms_fore_aft_m": rms_ap,
        "sway_rms_lateral_m": rms_ml,
        "sway_lean_rad": lean_r,
        "sway_lean_deg": math.degrees(lean_r),
        # NAMED `velocity` AND NOT `speed` ON PURPOSE. As `sway_speed_ms` it docked into H3.08's
        # V_walk socket -- a cost-of-transport law wanting a WALKING speed -- because "speed_ms" is
        # that signature's key fragment and 7.7 mm/s matched it before `comfortable_speed_ms` did.
        # The unit was right, the quantity was not. Mean COP velocity is the posturography term
        # anyway, so the honest name and the non-promiscuous one are the same name.
        "sway_velocity_ms": sway_speed,
        "sway_rate_over_fall_ratio": rate_over_w0,
        # THE FREQUENCIES, in hertz because that is how sway is measured and reported everywhere,
        # with the same three facts also published as PERIODS so nothing depends on `_hz` being
        # declared in story/data/units.json.
        "sway_freq_fore_aft_hz": f_ap,
        "sway_freq_lateral_hz": f_ml,
        "pendulum_freq_hz": pend_hz,
        "sway_period_s": 1.0 / f_ap,
        "sway_period_lateral_s": 1.0 / f_ml,
        "pendulum_period_s": 1.0 / pend_hz,
        # THE UNFITTED ONE: the body has no clock but its own topple, so this ratio must be O(1).
        "sway_over_pendulum_fore_aft_ratio": f_ap / pend_hz,
        "sway_over_pendulum_lateral_ratio": f_ml / pend_hz,
        # ...and how much of the base the sway actually uses. Standing still is a small motion inside
        # a large permission, which is exactly why a person can stand without thinking about it.
        "sway_over_margin_lateral_ratio": rms_ml / out["natural_half_width_m"],
        "sway_over_margin_fore_aft_ratio": rms_ap / out["natural_half_length_m"],
        "sway_source": ("HBEDB/BDS 261 trials young/eyes-open/firm; RMS and median power frequency "
                        "per axis, carried to this body as a LEAN ANGLE and to this world by w0"),

        # ── the same body on Earth, so the gravity term is visible rather than argued ────────────
        "g": g,
        "g_earth_m_s2": G_EARTH_MS2,
        "gravity_ratio": g / G_EARTH_MS2,
        "fall_rate_earth_rad_s": w0_earth,
        "balance_slower_than_earth_ratio": w0_earth / w0,
        "time_to_fall_earth_s": 1.0 / w0_earth,
        "push_velocity_natural_earth_ms": out["natural_half_width_m"] * w0_earth,

        # ── how the movie draws a 5 mm wander in a 0.4 m frame ───────────────────────────────────
        # A DECLARED EXAGGERATION, and it scales something derived rather than minting anything:
        # the sway is 1.2% of the frame and would be two pixels. Everything else is true scale.
        "sway_drawn_factor": 8.0,

        # ── carried ──────────────────────────────────────────────────────────────────────────────
        "height_m": h,
        "mass_kg": m,
        "weight_N": W,
        "com_height_m": L,
        "leg_length_m": leg,
        "step_length_m": step_len,
        "comfortable_speed_ms": walk_v,
        "skin_albedo_rgb": [float(x) for x in parent["skin_albedo_rgb"]],
        "S_earth": float(parent["S_earth"]),
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- a base of support, seen from above, with the body's fate wandering inside it
# ════════════════════════════════════════════════════════════════════════════════════════════════
def emit(nums, t=1.0):
    """THE STANCE OPENING, and the margin opening with it.

    LOCAL UNITS: 1.0 is `extent_m`, the half-diagonal of the widest base this law derives. Looking
    DOWN at the ground: +X is the way the body faces, +Y is its left, and everything drawn lies on
    z = 0 because a base of support is a region on the ground and nothing else.

    WHAT MOVES, and there are two clocks running at once because a stance really does have two:

      THE STANCE ITSELF opens from feet-together to the derived braced stance over the movie. The
      feet slide apart, the support polygon grows with them, and the MARGIN -- drawn as the segment
      from the extrapolated CoM to the nearest edge -- grows from 0.10 m to 0.39 m. That segment's
      length is the whole chapter: it is how hard a shove the stance survives, divided by m*omega0.

      THE BODY SWAYS at the two frequencies the force plates measured, carried to this world by its
      own omega0. The two axes run at DIFFERENT rates -- 0.16 Hz fore-aft against 0.21 Hz laterally
      -- so the trace never closes, and that is why a real stabilogram wanders instead of orbiting.
      The pale trail is where the CoM has been: the movie draws the measurement, not a picture of it.

      AND THE TWO MARKS ARE NOT THE SAME POINT. The dim one is the centre of mass; the bright one is
      the EXTRAPOLATED centre of mass, ahead of it by v/omega0. Watch it lead: it swings furthest out
      exactly when the CoM is moving fastest, which is at the middle of the sway, not the ends. That
      lead is the entire reason standing is a process -- a body has to know its own velocity.

    THE ONE EXAGGERATION, declared: the sway is drawn `sway_drawn_x` times life size, because 4.8 mm
    inside a 0.4 m frame is two pixels. It scales something derived. Nothing here is invented: every
    foot, edge, mark and segment is a number `derive()` published.
    """
    from matter import blank, lit, SOLID, GLOW, AR, AG, AB

    u = min(max(float(t), 0.0), 1.0)
    E = float(nums["extent_m"])
    w0 = float(nums["fall_rate_rad_s"])
    f_len, f_brd = float(nums["foot_length_m"]), float(nums["foot_breadth_m"])
    mag = float(nums["sway_drawn_factor"])

    # ── the stance at this instant: together -> braced, smoothly ────────────────────────────────
    s = u * u * (3.0 - 2.0 * u)                       # smoothstep, so it starts and ends at rest
    c0, c1 = float(nums["together_foot_centre_m"]), float(nums["braced_foot_centre_m"])
    centre = c0 + (c1 - c0) * s
    half_w = centre + 0.5 * f_brd
    half_l = 0.5 * f_len

    # ── the sway at this instant, from the derived frequencies ──────────────────────────────────
    T = float(nums["duration_s"])
    time_s = u * T
    A_ap = float(nums["sway_rms_fore_aft_m"]) * math.sqrt(2.0)     # RMS -> amplitude of a sinusoid
    A_ml = float(nums["sway_rms_lateral_m"]) * math.sqrt(2.0)
    wa = 2.0 * math.pi * float(nums["sway_freq_fore_aft_hz"])
    wm = 2.0 * math.pi * float(nums["sway_freq_lateral_hz"])

    def com_at(ts):
        return A_ap * math.sin(wa * ts), A_ml * math.sin(wm * ts + 1.0)

    def vel_at(ts):
        return A_ap * wa * math.cos(wa * ts), A_ml * wm * math.cos(wm * ts + 1.0)

    cx, cy = com_at(time_s)
    vx, vy = vel_at(time_s)
    xx, xy = cx + vx / w0, cy + vy / w0                # Hof's XcoM, and it leads

    P, kind = [], []

    def add(pts, k):
        if len(pts):
            P.append(np.asarray(pts, np.float32) / E)
            kind.append(np.full(len(pts), k))

    # ── THE TWO FEET, at true scale, as filled soles ────────────────────────────────────────────
    # the ankle sits `ankle_ahead_of_heel_m` from the heel, so the foot is NOT centred on it -- the
    # polygon is placed by its own heel, and where the ankle lands inside it is a consequence.
    nx, ny = 26, 11
    fx = np.linspace(-half_l, half_l, nx)
    fy = np.linspace(-0.5 * f_brd, 0.5 * f_brd, ny)
    FX, FY = np.meshgrid(fx, fy)
    # round the toe and heel a little, by the foot's own breadth -- a sole is not a rectangle
    keep = (np.abs(FX) < half_l - 0.5 * f_brd) | \
           (((np.abs(FX) - (half_l - 0.5 * f_brd)) / (0.5 * f_brd)) ** 2
            + (FY / (0.5 * f_brd)) ** 2 <= 1.0)
    for side in (+1.0, -1.0):
        pts = np.stack([FX[keep], side * centre + FY[keep], np.zeros(int(keep.sum()))], 1)
        add(pts, 0)

    # ── THE BASE OF SUPPORT: the bounding rectangle of the two soles ────────────────────────────
    # WHICH IS THE CONVEX HULL to within the rounding of the toe and heel -- the true hull cuts the
    # four corners with short tangent lines. Stated because it is a simplification and not a
    # derivation, and because it makes the drawn base very slightly LARGER than the real one.
    n_e = 150
    ex = np.linspace(-half_l, half_l, n_e)
    ey = np.linspace(-half_w, half_w, n_e)
    hull = np.concatenate([
        np.stack([ex, np.full(n_e, +half_w), np.zeros(n_e)], 1),
        np.stack([ex, np.full(n_e, -half_w), np.zeros(n_e)], 1),
        np.stack([np.full(n_e, +half_l), ey, np.zeros(n_e)], 1),
        np.stack([np.full(n_e, -half_l), ey, np.zeros(n_e)], 1)])
    add(hull, 1)

    # ── THE STABILOGRAM: where the CoM has already been ─────────────────────────────────────────
    # ALWAYS the same number of grains, including at t = 0 where the trail has no length yet and
    # they all pile onto the starting point. A buffer whose LENGTH changes with t cannot be compared
    # frame to frame, and comparing frames is the only way to catch a movie that silently stopped.
    n_tr = 220
    ts = np.linspace(0.0, time_s, n_tr)
    tr = np.array([com_at(v) for v in ts])
    add(np.stack([tr[:, 0] * mag, tr[:, 1] * mag, np.full(n_tr, 0.002)], 1), 2)

    # ── THE TWO MARKS, and the gap between them is v/omega0 ─────────────────────────────────────
    def disc(x, y, r, n=54):
        a = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
        rr = np.repeat(np.linspace(0.25 * r, r, 3), n)
        aa = np.tile(a, 3)
        return np.stack([x + rr * np.cos(aa), y + rr * np.sin(aa), np.full(len(aa), 0.004)], 1)

    add(disc(cx * mag, cy * mag, 0.010 * E), 3)                     # the centre of mass
    add(disc(xx * mag, xy * mag, 0.015 * E), 4)                     # ...and where it is GOING

    # ── THE MARGIN: from the XcoM to the nearest edge of the base ───────────────────────────────
    # which edge is nearest is itself a measurement: it is whichever of the four the XcoM is closest
    # to, and as the stance opens the answer flips from a side to an end.
    dx_p, dx_m = half_l - xx * mag, half_l + xx * mag
    dy_p, dy_m = half_w - xy * mag, half_w + xy * mag
    d, tgt = min((dx_p, (half_l, xy * mag)), (dx_m, (-half_l, xy * mag)),
                 (dy_p, (xx * mag, half_w)), (dy_m, (xx * mag, -half_w)), key=lambda z: z[0])
    n_m = 90
    seg = np.stack([np.linspace(xx * mag, tgt[0], n_m),
                    np.linspace(xy * mag, tgt[1], n_m),
                    np.full(n_m, 0.003)], 1)
    add(seg, 5)

    Pts = np.concatenate(P, 0)
    K = np.concatenate(kind)
    n = len(Pts)
    b = blank(n)
    b[:, 0:3] = Pts
    nrm = np.zeros((n, 3), np.float32)
    nrm[:, 2] = 1.0                                   # a ground plan is seen from above
    b[:, 21:24] = nrm

    # THE SOLES ARE SKIN, and their albedo is the parent's own measured skin -- one derivation, two
    # consumers. Everything else here is a DIAGRAM colour and is said to be: a base of support is a
    # geometric region, it has no spectrum, and pretending otherwise would be the aesthetic pass
    # this project does not take.
    alb = np.zeros((n, 3), np.float32)
    alb[K == 0] = np.array(nums["skin_albedo_rgb"], np.float32)     # the soles
    alb[K == 1] = np.array([0.35, 0.55, 0.42], np.float32)          # the base of support
    alb[K == 2] = np.array([0.42, 0.48, 0.66], np.float32)          # where the CoM has been
    alb[K == 3] = np.array([0.72, 0.74, 0.78], np.float32)          # the CoM now
    alb[K == 4] = np.array([1.00, 0.76, 0.24], np.float32)          # the XcoM -- where it is going
    alb[K == 5] = np.array([0.95, 0.35, 0.28], np.float32)          # the margin that is left
    S = float(nums.get("S_earth", 1.0))
    b[:, 16:19] = lit(alb, S * 0.85 + 0.15, e_ref=S, tone=0.45)
    b[:, AR:AB + 1] = alb
    b[:, 19] = np.where(K == 2, 0.5, 0.96)
    b[:, 20] = np.where(K == 4, 0.030, np.where(K == 0, 0.020, 0.012))
    b[:, 11] = np.where(K == 4, GLOW, SOLID)
    return b


def measure(nums):
    """Facts a reader can check without trusting the prose. The three checks nothing was fitted to
    are first, and each reports its NUMBER so it can be judged rather than believed."""
    ap = nums["sway_over_pendulum_fore_aft_ratio"]
    ml = nums["sway_over_pendulum_lateral_ratio"]
    return {
        # ── 1. the CoM lands where quiet standing puts it, from a margin argument alone ──────────
        "com_ahead_of_ankle_m": nums["com_ahead_of_ankle_m"],
        "com_offset_in_measured_band": 0.040 <= nums["com_ahead_of_ankle_m"] <= 0.060,

        # ── 2. the sway has no clock but the pendulum's ─────────────────────────────────────────
        "sway_over_pendulum_fore_aft_ratio": ap,
        "sway_over_pendulum_lateral_ratio": ml,
        "sway_is_order_of_the_pendulum": 0.25 <= ap <= 1.0 and 0.25 <= ml <= 1.0,

        # ── 3. two sources for one foot, and they must agree ────────────────────────────────────
        # ANSUR's length times ANSUR's breadth against the area theHuman published from its own
        # read. Same survey, two paths; if they ever disagree one of the two reads is broken.
        "foot_area_m2": nums["foot_area_m2"],
        "foot_area_matches_parent": abs(nums["foot_area_m2"]
                                        - nums["parent_foot_area_m2"]) < 1e-12,

        # ── the inertia correction sits between its two brackets, both computed from geometry ───
        "inertia_correction_factor": nums["inertia_correction_factor"],
        "correction_between_point_and_rod": (nums["inertia_correction_uniform_rod_factor"]
                                             < nums["inertia_correction_factor"]
                                             < nums["inertia_correction_point_mass_factor"]),
        "radius_of_gyration_frac": nums["radius_of_gyration_frac"],

        # ── the trade, stated as the two numbers that oppose each other ─────────────────────────
        "braced_over_together_margin": nums["braced_over_together_margin"],
        "braced_step_delay_ratio": nums["braced_step_delay_ratio"],
        "bracing_buys_more_than_it_costs": (nums["braced_over_together_margin"]
                                            > 1.0 + nums["braced_step_delay_ratio"]),

        # ── bracing wide does NOTHING for a push from in front, and that is the point ───────────
        "fore_aft_margin_is_stance_independent": abs(nums["braced_margin_fore_aft_m"]
                                                     - nums["together_margin_fore_aft_m"]) < 1e-12,

        # ── the braced stance must be affordable by SOMETHING the world can supply ──────────────
        "braced_friction_required_ratio": nums["braced_friction_required_ratio"],
        "braced_hip_torque_Nm": nums["braced_hip_torque_Nm"],
        "braced_within_hip_range": abs(nums["braced_hip_offset_m"]) < nums["hip_limit_offset_m"],
        "hip_limit_needs_impossible_friction": nums["hip_limit_friction_required_ratio"] > 1.0,

        # ── and the world's gravity, which is the whole reason this body is not on Earth ────────
        "time_to_fall_s": nums["time_to_fall_s"],
        "balance_slower_than_earth_ratio": nums["balance_slower_than_earth_ratio"],
        "stance_in_human_band": 0.04 <= nums["duration_s"] <= 10.0,
    }
