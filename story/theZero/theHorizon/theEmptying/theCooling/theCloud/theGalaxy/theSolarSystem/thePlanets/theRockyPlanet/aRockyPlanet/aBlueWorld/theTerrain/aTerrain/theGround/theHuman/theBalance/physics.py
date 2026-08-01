"""theBalance -- the frontal plane. The same fall, turned ninety degrees, and nothing catches it.

THE EDGE. Everything above this is SAGITTAL: theHuman walks fore-and-aft, theAnkle rolls fore-and-aft,
and the whole gait table is a picture taken from the side. A body seen from the side is not falling
sideways, which is exactly why the side view is comfortable and exactly why it is incomplete.

WHY THE TWO PLANES ARE NOT THE SAME LAW WEARING A DIFFERENT NAME. Fore-aft, the catch is free: the
swing leg is going forward anyway, so a forward fall lands on a foot that was already on its way.
Sideways it is not -- the leg has to be PUT there, and if it is not, nothing stops the fall. That
asymmetry is measured, not asserted: Bauby & Kuo (2000) showed that lateral balance in walking
requires active control while fore-aft balance is passively stable, and that the lateral variability
is where the control shows up.

THE CHAPTER'S JOB, WITH A NUMBER ALREADY ATTACHED. theAnkle closed with a located residual: in double
support the parent's two legs disagree by 2.02% of stature about where the pelvis is, and it named
about 40% of that -- 0.81% of stature -- as PELVIC LIST, which a sagittal model cannot express
because it puts both hips at one height by construction. A pelvis is a rigid bar between two hip
joints; tilt it in the frontal plane and the two hips are at DIFFERENT heights, by exactly

    dz = W_pelvis * sin(phi)

That is the whole payoff, and it is one line. What it needs is a pelvis width and an obliquity, and
this chapter gets both from measurement.

THE FOUR THINGS DERIVED, in order, each one feeding the next:

    1. THE FRONTAL PENDULUM.  ÿ = w0^2 y about the stance foot, the parent's own w0 = sqrt(g/H),
       solved in closed form for a periodic gait. It gives the lateral sway, the margin of stability
       and the step width from ONE geometric criterion, and the three answers are startlingly simple:
           d_medial   = W/2                      the CoM sits over the pelvis centre at mid-stance
           step width = W * cosh(w0*T/2)
           sway       = W * (cosh(w0*T/2) - 1)
           margin b   = (W/2) * exp(-w0*T/2)
       A pelvis width, magnified by half a step's worth of e-folding. Nothing else is in them.
    2. THE STEP WIDTH CHECK, unfitted: fed Earth's gravity and the 246 adults' own step time, the
       law returns 0.2440 m against their measured 0.2119 -- 15% high, reported as it fell.
    3. THE PELVIC LIST, which is the payoff above.
    4. THE ABDUCTOR, because a list is held by a muscle. Moments about the stance hip give the hip
       contact force, and THAT is the check nothing here was fitted to: 2.50 body weights against
       the ~2.4 measured through instrumented hip prostheses.

WHERE EVERY NUMBER COMES FROM -- three sources, all of them files in this repo:

    story/data/gait_normative.json  -- Van Criekinge et al. (2023), 246 adults, read through
        `measured`. Supplies pelvic obliquity, frontal trunk lean and hip ad/abduction as CURVES,
        at the cohort and speed condition the PARENT chose. This membrane picks neither.
    research_references/human/opensim/gait2392_thelen2003muscle.osim  (Delp et al. 1990)
    research_references/human/opensim/Rajagopal2016.osim              (Rajagopal et al. 2016)
        Two independent published musculoskeletal models, tracked in git. They supply the hip joint
        separation and the gluteal moment arm -- geometry no anthropometric table measures, because
        a joint centre is inside you. THEY AGREE ON THE PELVIS TO 2.1%, which is what licenses using
        either. Their statures (1.80 m and 1.70 m) are quoted from the papers, and each file's own
        total mass (75.165 kg, 75.337 kg) independently confirms the mass half of that claim to four
        figures -- which is how the height half is earned rather than assumed.
    research_references/human/ansur_anchors.json -- ANSUR II, 4,082 men, for the foot's breadth,
        which is the ankle's entire lateral authority.

WHAT IS NOT SOURCED, said out loud because a guess dressed as a citation is the one defect no
checker can catch:

    * The two literature comparisons in `measure()` are quoted from memory of the papers and the
      papers are NOT in this repo: Orendurff et al. (2004) for mediolateral CoM excursion falling
      from ~7 cm at 0.7 m/s to ~4 cm at 1.6 m/s, and Bergmann et al. (2001) for a peak hip contact
      force near 2.4 body weights in level walking. Both are quoted to ONE significant figure and
      the checks against them are ballpark checks, not agreements to a percent. They are marked as
      such in `measure()` so nobody downstream reads them as measurements this repo holds.
    * The identification of the pelvis centre's LATERAL position with the whole body's centre of
      mass. The trunk leans (measured, +-6 deg here) and the arms swing, so the two differ by a
      centimetre or so. Every lateral number below inherits that approximation.
    * The measured frontal HIP angle is not used quantitatively at all, and that is deliberate --
      see `measure()["hip_abad_offset_deg"]`. It does not close with the other two frontal
      measurements, by about 3 degrees, and a static frontal offset is the classic marker-model
      artefact. Reporting the disagreement is worth more than picking a side of it.

Contained in theHuman. Its movie is ONE STRIDE, seen from the front: two steps, two lists, one sway.
"""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

# ── MEASURED. ANSUR II (US Army 2012, public release 2017), 4,082 men, via ansur_anchors.json,
# which is already in this repo and already read by other membranes. The foot's BREADTH is the
# ankle's whole lateral authority: the centre of pressure cannot leave the sole, so half of this is
# the furthest sideways the ankle can push without a step.
FOOT_BREADTH_FRAC = 0.05804        # of stature; ANSUR II male mean, n = 4,082

# ── THE TWO MODELS, named here and read from disk below rather than transcribed. A transcribed
# number is a literal wearing a citation; a read number changes when the file does.
OPENSIM = {
    # file                                stature (m), from the paper, mass-confirmed by the file
    "gait2392_thelen2003muscle.osim": (1.80, 75.16, "Delp et al. 1990 / Thelen 2003, gait2392"),
    "Rajagopal2016.osim": (1.70, 75.3, "Rajagopal et al. 2016, full-body model"),
}

FREE = {
    # HOW WIDE TO STAND. The law below derives a NEUTRAL width -- the one at which the stance hip
    # sits directly over the stance ankle and the abductors carry no avoidable moment. A body may
    # choose otherwise: a braced shooter widens, a person on a beam narrows, and both cost more.
    # This is the only number in this chapter a body chooses rather than inherits.
    "stance_width": {"lo": 0.5, "hi": 2.5, "default": 1.0,
                     "label": "stance width", "unit": "of the neutral width",
                     "local": "how wide to stand is a choice; how it then falls is not"},
}


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE GEOMETRY NO TAPE MEASURE REACHES -- read from two published models
# ════════════════════════════════════════════════════════════════════════════════════════════════
_MODEL_CACHE = None


def _repo_root() -> Path:
    """The ancestor holding research_references. Found, not assumed, because this membrane is
    sixteen folders deep and counting `.parent` sixteen times is a bug waiting for a rename."""
    for p in Path(__file__).resolve().parents:
        if (p / "research_references" / "human" / "opensim").is_dir():
            return p
    raise FileNotFoundError(
        "research_references/human/opensim is not reachable from theBalance; it holds the two "
        "musculoskeletal models this chapter reads its pelvis geometry from.")


def pelvis_geometry() -> dict:
    """HIP JOINT SEPARATION AND ABDUCTOR MOMENT ARM, as fractions of stature, read from two models.

    WHY A MODEL AND NOT A TABLE. ANSUR II measured 4,082 men with callipers and has no hip joint
    separation in it, because a joint centre is INSIDE a person: the tape reaches the greater
    trochanter (0.197 of stature across, which is where the classic 0.191 H figure comes from) and
    the joint sits some centimetres medial of that. A musculoskeletal model is where that number
    lives, and there are two independent ones tracked in this repo.

    TWO OF THEM, AND THE DISAGREEMENT IS KEPT. Delp's 1990 lower-extremity model puts the hip joint
    centres 0.1670 m apart in a body 1.80 m tall; Rajagopal's 2016 full-body model puts them
    0.15452 m apart in a body 1.70 m. As fractions of stature that is 0.09278 and 0.09089 -- 2.1%
    apart, from two labs a quarter-century apart. The mean is used and the spread is published, in
    the manner of `measured.compare()`: averaging away a disagreement throws out the only estimate
    of how well the number is known.

    THE STATURES ARE QUOTED FROM THE PAPERS, and that would be a bare literal except that each file
    independently confirms the other half of the same claim: the papers say 1.80 m / 75.16 kg and
    1.70 m / 75.3 kg, and summing the bodies in the files gives 75.165 kg and 75.337 kg. A file that
    agrees on the mass to four figures is the file the height belongs to.

    THE ABDUCTOR MOMENT ARM is not a coordinate at all -- it is computed. For each gluteus medius
    and minimus compartment the line of action is taken from its origin on the ilium to its
    insertion on the trochanter, both expressed relative to the hip joint centre, and the moment arm
    about the fore-aft axis is the x-component of r x u. Averaged over the six compartments weighted
    by their maximum isometric force it comes to 0.0422 m in a 1.80 m body -- 0.02345 of stature.
    The textbook figure for the abductor lever is "about 5 cm"; this is that, derived."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    base = _repo_root() / "research_references" / "human" / "opensim"
    seps, arms, masses = [], [], []
    for fname, (stature, m_paper, cite) in OPENSIM.items():
        path = base / fname
        if not path.exists():
            raise FileNotFoundError(f"{path} is missing; theBalance reads its pelvis geometry from it")
        root = ET.parse(path).getroot()

        # total mass, as the check that this file is the body the paper describes
        mass = sum(float(b.find("mass").text) for b in root.iter("Body")
                   if b.find("mass") is not None)
        masses.append((fname, mass, m_paper))

        # the hip joint centre in the pelvis frame -- its lateral coordinate, doubled
        hip = None
        for j in root.iter("CustomJoint"):
            if j.get("name") == "hip_r":
                for f in j.iter("PhysicalOffsetFrame"):
                    if f.get("name") == "pelvis_offset":
                        hip = [float(v) for v in f.find("translation").text.split()]
        if hip is None:
            raise ValueError(f"no hip_r joint in {fname}")
        seps.append(2.0 * abs(hip[2]) / stature)

        # the abductors, only in the model that carries the full muscle set at the hip
        num = den = 0.0
        for mus in root.iter():
            nm = mus.get("name") or ""
            if not (nm.startswith(("glut_med", "glut_min")) and nm.endswith("_r")):
                continue
            pts = [(pp.find("socket_parent_frame").text.strip().split("/")[-1],
                    [float(v) for v in pp.find("location").text.split()])
                   for pp in mus.iter("PathPoint")]
            if len(pts) < 2:
                continue
            org = [pts[0][1][k] - hip[k] for k in range(3)]     # origin, relative to the hip centre
            ins = pts[1][1]                                     # the femur frame IS the hip centre
            u = [ins[k] - org[k] for k in range(3)]
            L = math.sqrt(sum(v * v for v in u)) or 1.0
            u = [v / L for v in u]
            arm = org[1] * u[2] - org[2] * u[1]                 # (r x u)_x : about the fore-aft axis
            F = mus.find("max_isometric_force")
            F = float(F.text) if F is not None else 1.0
            num += F * arm
            den += F
        if den > 0.0:
            arms.append(num / den / stature)

    _MODEL_CACHE = {
        "hip_separation_frac": sum(seps) / len(seps),
        "hip_separation_spread_pct": 100.0 * (max(seps) - min(seps)) / (sum(seps) / len(seps)),
        "abductor_lever_frac": sum(arms) / len(arms),
        "models": [c for _, (_, _, c) in OPENSIM.items()],
        "mass_confirms": [{"file": f, "file_kg": mk, "paper_kg": mp} for f, mk, mp in masses],
    }
    return _MODEL_CACHE


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE FRONTAL PENDULUM, SOLVED
# ════════════════════════════════════════════════════════════════════════════════════════════════
def sway_solution(pelvis_W, w0, step_s, stance=1.0):
    """A PERIODIC LATERAL GAIT, in closed form. Four numbers out, and each is one line.

    THE MODEL. During single support the body is an inverted pendulum about the stance foot in the
    frontal plane -- the same law the parent already uses fore-aft, the same w0 = sqrt(g/H), turned
    ninety degrees. With y measured from the stance foot:

        ÿ = w0^2 y      ->      y(t) = y0 cosh(w0 t) + (v0/w0) sinh(w0 t)

    THE PERIODICITY CONDITION IS WHAT MAKES IT SOLVABLE, and it costs nothing to state: a walk is
    the same step, mirrored, forever. Put t = 0 at mid-step, where by that mirror symmetry the
    lateral velocity is zero and the CoM is at its extreme. Then y(t) = d cosh(w0 t) with d the
    CoM's medial offset from the stance foot, and half a step later the mirror must hold about the
    OTHER foot, a step width w away:

        2 d cosh(w0 T/2) = w                    (T = one step)

    THE ONE CRITERION THAT CLOSES IT. That relates d and w and fixes neither. What fixes both is a
    statement about the LEG: at mid-stance the stance hip sits over the stance ankle, so the leg is
    a strut carrying a vertical load with no frontal moment demanded at either end. Then the CoM,
    which is d medial of the ankle, is d medial of the HIP -- and half a pelvis medial of a hip is
    the pelvis centre. So

        d = W/2

    and everything else falls out of the line above it. This is a claim about a body, not a fit, and
    `measure()` reports how far the real body misses it: 0.65 degrees of leg tilt.

    THE MARGIN OF STABILITY is Hof's, unchanged: the extrapolated centre of mass, XcoM = y + v/w0,
    is where the body would come to rest if the pressure point stayed put, so a foot placed lateral
    of it reverses the fall and a foot placed medial of it does not. At the step transition
    (t = T/2) the XcoM is at d*exp(w0 T/2) from the old foot, and the new foot is w away, so

        b = w - d exp(w0 T/2) = (W/2) exp(-w0 T/2)

    Half a pelvis, discounted by the step's own e-folding. Nothing was chosen to make it come out
    that clean.

    `stance` widens or narrows the step from the neutral value; the sway and margin follow it, and
    the leg stops being vertical at mid-stance, which is what makes a wide stance cost something."""
    th = float(w0) * float(step_s) / 2.0          # how many e-folds of fall in half a step
    W = float(pelvis_W)
    w = float(stance) * W * math.cosh(th)         # step width, foot centre to foot centre
    d = w / (2.0 * math.cosh(th))                 # CoM's medial offset from the stance foot
    return {
        "efolds": th,
        "gain": math.cosh(th),
        "step_width_m": w,
        "com_medial_offset_m": d,
        "sway_pp_m": w - 2.0 * d,                 # = W(cosh th - 1) at stance = 1
        "margin_m": d * math.exp(-th),            # = (W/2) exp(-th) at stance = 1
        "xcom_at_contact_m": d * math.exp(th),    # from the old foot; = w - b
    }


def com_lateral(sol, w0, step_s, phase):
    """WHERE THE CENTRE OF MASS AND ITS CAPTURE POINT ARE, at phase 0..1 of one STRIDE.

    Returns (y, ydot, xcom, stance_side) with +y to the body's LEFT and the midline at zero. This is
    the sway_solution above evaluated rather than a curve: the render draws the equation.

    stance_side is -1 while the right foot carries and +1 while the left does. The CoM crosses the
    midline exactly at the transition, which is not arranged -- it is what 2 d cosh(w0 T/2) = w says
    when you evaluate it at the end of a step."""
    d, W0 = float(sol["com_medial_offset_m"]), float(w0)
    half = 0.5 * float(sol["step_width_m"])
    p = (float(phase) % 1.0) * 2.0
    k = int(p)                                    # 0 = right foot carries, 1 = left
    tau = (p - k - 0.5) * float(step_s)
    side = -1.0 if k == 0 else 1.0                # which side the stance foot is on
    y = side * (half - d * math.cosh(W0 * tau))
    ydot = -side * d * W0 * math.sinh(W0 * tau)
    return y, ydot, y + ydot / W0, side


def abductor(mass_supported_frac, weight_N, lever_m, com_offset_m):
    """WHAT HOLDS THE PELVIS UP, and what the hip pays for it. Moments about the stance hip joint.

    In single support the pelvis is a lever: everything the stance leg is not -- trunk, head, arms
    and the whole swinging leg -- hangs medial of the hip, and the abductors are the only thing on
    the other side. Balance the moments:

        F_abd * a  =  W_supported * c        ->    F_abd = W_s c / a

    with `a` the gluteal moment arm read off the model and `c` the supported mass's lateral distance
    from the stance hip. The femoral head then carries both of them pressing the same way, so the
    joint contact force is about F_abd + W_s -- which is why standing on one leg loads a hip far
    harder than standing on two, and why this is the number instrumented prostheses measure.

    c IS NOT THE WHOLE-BODY CoM OFFSET. The stance leg is a fifth of the body and it hangs under the
    hip, contributing nothing to the moment; removing it moves the remaining mass's centre FURTHER
    medial, by exactly the factor 1/(1 - leg mass fraction). Skip that and the answer is 20% light."""
    f = float(mass_supported_frac)
    c = float(com_offset_m) / max(f, 1e-9)
    W_s = f * float(weight_N)
    F = W_s * c / max(float(lever_m), 1e-9)
    return {"supported_N": W_s, "lever_arm_m": float(lever_m), "com_arm_m": c,
            "abductor_N": F, "contact_N": F + W_s}


# ════════════════════════════════════════════════════════════════════════════════════════════════
def derive(parent, free):
    if parent is None or "fall_rate_rad_s" not in parent:
        raise ValueError("theBalance requires theHuman as its parent")
    import measured
    free = free or {}
    stance = float(free.get("stance_width", FREE["stance_width"]["default"]))

    h = float(parent["height_m"])
    m = float(parent["mass_kg"])
    g = float(parent["g"])
    H = float(parent["com_height_m"])
    leg_L = float(parent["leg_length_m"])
    weight = float(parent["weight_N"])
    leg_frac = float(parent["leg_mass_frac"])
    w0 = float(parent["fall_rate_rad_s"])              # sqrt(g/H) -- the same one, sideways
    step_s = float(parent["step_time_s"])
    stride_s = float(parent["duration_s"])
    duty = float(parent["duty_factor"])
    ds_frac = float(parent["double_support_frac"])
    w_meas = float(parent["measured_step_width_m"])
    group = str(parent["gait_group"])                  # the cohort the PARENT chose
    speed = str(parent["gait_speed_condition"])        # ... and the speed condition. Not re-picked.

    P = pelvis_geometry()
    W_pelvis = P["hip_separation_frac"] * h
    lever = P["abductor_lever_frac"] * h
    foot_breadth = FOOT_BREADTH_FRAC * h

    # ── 1. THE SWAY, THE WIDTH AND THE MARGIN, on this world ────────────────────────────────────
    S = sway_solution(W_pelvis, w0, step_s, stance)

    # ── 2. THE SAME LAW AT EARTH GRAVITY, which is the only place the check can be made ─────────
    # The 246 adults walked on Earth, so their step width may only be compared with what this law
    # says AT EARTH -- with Earth's w0 and Earth's own measured step time. Feeding this world's
    # gravity into a comparison with Earth data is the mistake theAnkle's struck-through paragraph
    # is a monument to: a formula that lands on the literature only at the local g has not been
    # checked, it has been flattered.
    G_EARTH = 9.80665                                  # m/s2, standard gravity, by definition
    w0_e = math.sqrt(G_EARTH / H)
    step_e = measured.gait_duty(speed, group)["stride_s"] / 2.0
    E = sway_solution(W_pelvis, w0_e, step_e, 1.0)
    # and the sway that faces the literature uses the MEASURED width, so that this check does not
    # inherit the error of the width check above it. Two checks, kept independent on purpose.
    th_e = w0_e * step_e / 2.0
    sway_e_meas = w_meas * (1.0 - 1.0 / math.cosh(th_e))
    d_e_meas = w_meas / (2.0 * math.cosh(th_e))

    # THE SPEED TREND. Step width barely moves with walking speed -- 0.2119, 0.2110, 0.2125 over a
    # near doubling -- but the sway does, and the law says why: the sway is the width times
    # (cosh - 1), and cosh falls because the step gets SHORTER IN TIME. Nothing narrows.
    trend = {}
    for cond in ("slow", "comf", "fast"):
        T_c = measured.gait_duty(cond, group)["stride_s"] / 2.0
        w_c = measured.gait_scalar("R.Step.Width [m]", cond, group)[0]
        th_c = w0_e * T_c / 2.0
        trend[cond] = {"v": measured.gait_walking_speed(cond, group),
                       "sway": w_c * (1.0 - 1.0 / math.cosh(th_c)),
                       "margin": w_c / (math.exp(2.0 * th_c) + 1.0),
                       "width_law": W_pelvis * math.cosh(th_c)}

    # ── 3. THE PELVIC LIST -- this chapter's reason for existing ────────────────────────────────
    # The measured obliquity, read at the cohort and speed the parent already chose, sampled onto
    # the same 48 the parent's gait table uses so a child can index one against the other.
    N = int(parent.get("gait_samples", 48))
    cyc = [[math.radians(measured.gait_sample("pelvic_obl", k / N, speed, group)),
            math.radians(measured.gait_sample("trunk_flex", k / N, speed, group)),
            math.radians(measured.gait_sample("hip_abad", k / N, speed, group))]
           for k in range(N)]
    obl = measured.gait_curve("pelvic_obl", speed, group)["mean"]
    list_peak = max(abs(min(obl)), abs(max(obl)))
    list_range = max(obl) - min(obl)
    # DOUBLE SUPPORT is where theAnkle measured its residual, so that is where this must be read.
    # The windows are the overlap of the two stance phases: [0, duty-0.5] and [0.5, duty].
    ds_lo, ds_hi = max(duty - 0.5, 0.0), duty
    list_ds = max(abs(measured.gait_sample("pelvic_obl", u / 400.0 * ds_lo, speed, group))
                  for u in range(401)) if ds_lo > 0 else 0.0
    list_ds = max(list_ds, max(abs(measured.gait_sample("pelvic_obl", 0.5 + (ds_hi - 0.5) * u / 400.0,
                                                       speed, group)) for u in range(401)))
    split_peak = W_pelvis * math.sin(math.radians(list_peak))
    split_ds = W_pelvis * math.sin(math.radians(list_ds))
    RESIDUAL = 0.0202          # of stature -- theAnkle's measured two-leg disagreement in double
    LIST_SHARE = 0.40          # support, and the share it attributed to frontal-plane list.

    # ── 4. THE ABDUCTOR, and the hip it loads ───────────────────────────────────────────────────
    A = abductor(1.0 - leg_frac, weight, lever, S["com_medial_offset_m"])
    A_e = abductor(1.0 - leg_frac, weight, lever, d_e_meas)   # the same body, Earth's sway

    # ── the closure that says how good the one criterion is ─────────────────────────────────────
    # At Earth, with the MEASURED width, the pendulum puts the CoM 7.00 cm medial of the stance foot
    # while half a pelvis is 8.06 cm. The gap is the stance leg NOT being vertical -- and over a
    # 0.93 m leg it is 0.65 of a degree. That is how much the criterion in sway_solution() misses by.
    tilt = math.degrees(math.asin(min(abs(W_pelvis / 2.0 - d_e_meas) / leg_L, 1.0)))
    abad_mid = measured.gait_sample("hip_abad", 0.5 * duty, speed, group)

    return {
        # ITS SIZE. Not a smaller thing than its parent -- the SAME body, seen along the other axis.
        # The frontal pendulum's own length is the height of the mass that swings, and that is the
        # unit this chapter works in. The PICTURE runs from the floor to that mass and is centred
        # between them, so the extent -- which `matter.grains_for` reads as the 99th-percentile
        # radius -- is half the pendulum, not all of it. Measured on the emitted buffer: 0.535 of
        # the pendulum's length, against the 0.5 declared here.
        "extent_m": 0.5 * H,
        "pendulum_length_m": H,
        # ITS DURATION: one full stride, because the frontal cycle needs BOTH steps -- one list to
        # the left and one to the right. Half of it is half a story.
        "duration_s": stride_s,

        # ── the pelvis, read from two models that agree to 2.1% ──────────────────────────────
        "pelvis_width_m": W_pelvis,
        "pelvis_width_frac": P["hip_separation_frac"],
        "pelvis_width_spread_pct": P["hip_separation_spread_pct"],
        "abductor_lever_m": lever,
        "abductor_lever_frac": P["abductor_lever_frac"],
        "pelvis_source": " + ".join(P["models"]),

        # ── the frontal pendulum, this world ─────────────────────────────────────────────────
        "fall_rate_rad_s": w0,
        "step_time_s": step_s,
        "frontal_efolds_ratio": S["efolds"],
        "sway_gain_ratio": S["gain"],
        "stance_width_ratio": stance,
        "step_width_m": S["step_width_m"],
        "com_medial_offset_m": S["com_medial_offset_m"],
        "sway_pp_m": S["sway_pp_m"],
        "sway_pp_frac": S["sway_pp_m"] / h,
        "margin_of_stability_m": S["margin_m"],
        "xcom_at_contact_m": S["xcom_at_contact_m"],

        # ── the same law at Earth, which is where the checks live ────────────────────────────
        "step_width_earth_m": E["step_width_m"],
        "step_width_measured_m": w_meas,
        "step_width_error_pct": 100.0 * (E["step_width_m"] - w_meas) / w_meas,
        "sway_pp_earth_m": sway_e_meas,
        "margin_earth_m": w_meas / (math.exp(2.0 * th_e) + 1.0),
        "speed_slow_ms": trend["slow"]["v"],
        "speed_comf_ms": trend["comf"]["v"],
        "speed_fast_ms": trend["fast"]["v"],
        "sway_earth_slow_m": trend["slow"]["sway"],
        "sway_earth_comf_m": trend["comf"]["sway"],
        "sway_earth_fast_m": trend["fast"]["sway"],
        "margin_earth_slow_m": trend["slow"]["margin"],
        "margin_earth_fast_m": trend["fast"]["margin"],
        "width_law_slow_m": trend["slow"]["width_law"],
        "width_law_fast_m": trend["fast"]["width_law"],

        # ── what the ankle can and cannot cover ──────────────────────────────────────────────
        "foot_breadth_m": foot_breadth,
        "foot_half_breadth_m": 0.5 * foot_breadth,
        "foot_clearance_m": float(parent["measured_foot_clearance_m"]),
        "ankle_authority_used_frac": S["margin_m"] / (0.5 * foot_breadth),
        "lateral_reserve_m": 0.5 * foot_breadth - S["margin_m"],
        # NOT `..._speed_ms`, and that is not fussiness. A socket in the physics catalog wants a
        # WALKING speed by the name fragment `speed_ms`, and it grabbed this -- a 0.04 m/s sideways
        # nudge -- and convicted it for being below a walking speed's floor. It is not a walking
        # speed; it is how hard you may be pushed sideways before the ankle alone stops being
        # enough. `folding.py membrane theBalance` found it, which is the tool doing its job.
        "reserve_velocity_ms": (0.5 * foot_breadth - S["margin_m"]) * w0,

        # ── THE PAYOFF: pelvic list, and the residual it accounts for ────────────────────────
        "list_peak_deg": list_peak,
        "list_range_deg": list_range,
        "list_double_support_deg": list_ds,
        "hip_split_peak_m": split_peak,
        "hip_split_double_support_m": split_ds,
        "hip_split_peak_frac": split_peak / h,
        "hip_split_double_support_frac": split_ds / h,
        "residual_frac": RESIDUAL,
        "residual_list_attributed_frac": RESIDUAL * LIST_SHARE,
        "residual_closed_frac": split_ds / h / RESIDUAL,
        "list_source": measured.gait_data()["source"],

        # ── the abductor, and the hip it loads ───────────────────────────────────────────────
        "supported_weight_N": A["supported_N"],
        "abductor_moment_arm_m": A["lever_arm_m"],
        "body_moment_arm_m": A["com_arm_m"],
        "abductor_force_N": A["abductor_N"],
        "hip_contact_force_N": A["contact_N"],
        "abductor_over_weight_ratio": A["abductor_N"] / weight,
        "hip_contact_over_weight_ratio": A["contact_N"] / weight,
        "hip_contact_earth_over_weight_ratio": A_e["contact_N"] / weight,

        # ── how well the one criterion closes ────────────────────────────────────────────────
        "leg_tilt_at_midstance_deg": tilt,
        "hip_abad_measured_at_midstance_deg": abad_mid,

        # ── carried on, so a child draws the same body ───────────────────────────────────────
        "frontal_cycle_rad": cyc,
        "frontal_sample_count": N,
        "gait_cycle": [list(r) for r in parent["gait_cycle"]],
        "gait_samples": N,
        "duty_factor": duty,
        "double_support_frac": ds_frac,
        "height_m": h,
        "mass_kg": m,
        "g": g,
        "com_height_m": H,
        "leg_length_m": leg_L,
        "S_earth": float(parent["S_earth"]),
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- a body from the FRONT, for one stride
# ════════════════════════════════════════════════════════════════════════════════════════════════
def emit(nums, t=1.0):
    """One stride seen from the front: the sway, the list, and the capture point reaching sideways.

    LOCAL UNITS: 1.0 is the centre of mass's standing height, which is the frontal pendulum's own
    length. +Y is the body's LEFT and Z is up; X is zero everywhere, because this membrane IS the
    frontal plane and drawing depth into it would be drawing the parent's chapter again.

    WHAT MOVES, AND WHY EACH THING MOVES:

      the two feet      stay at +-w/2 -- in this plane a step does not go anywhere, it only lifts.
                        Planted and swinging come from the PARENT's own gait table, so the frontal
                        view cannot disagree with the sagittal one about which foot is down.
      the pelvis BAR    tilts by the measured obliquity. This is the chapter: the bar is rigid and
                        W wide, so tilting it puts its two ends at DIFFERENT HEIGHTS, and the two
                        hips visibly separate vertically. That separation is the number theAnkle
                        could not produce and could not spend.
      the LEVEL line    behind it does not tilt, ever. It is the sagittal model's pelvis -- both
                        hips at one height by construction -- so the gap opening at each end of the
                        bar IS the residual, drawn at the size it actually is.
      the legs          follow, because each runs from a hip that is now moving to a foot that is
                        not. Nothing tells them to splay; the pelvis above them does.
      the ROD           from the stance foot to the mass is the inverted pendulum itself. It leans
                        over, comes back, and swaps feet at the transition, because that is what
                        the equation at the top of this file says a walking body does sideways.
      the CoM mark      sways, from `com_lateral()` -- the hyperbolic solution evaluated, not a
                        curve looked up. It is furthest out at mid-step and crosses the midline at
                        the transition, which is the periodicity condition made visible.
      the XcoM mark     runs AHEAD of it along the ground, and this is the one to watch. It is the
                        capture point: where the body is GOING, not where it is. It sweeps out
                        towards the next foot and arrives exactly `b` short of it -- and `b` is the
                        margin of stability. The gap you can see between the bright mark and the
                        foot it is arriving at IS that number.

    The pale trails are where each has already been, so the two paths are drawn by the things that
    make them rather than by a curve laid over the top -- the same arrangement theAnkle's centre of
    pressure uses, for the same reason.

    ONE THING JUMPS, AND IT IS SUPPOSED TO. The pendulum's pivot swaps feet instantly, at the middle
    of double support. That is the model being a SINGLE-support pendulum with a point pivot: the
    real handover is spread over the 24.6% of the stride when both feet are down, and the centre of
    pressure crosses between them continuously. Smoothing it here would draw a physics this chapter
    has not written."""
    from matter import blank, lit, SOLID, GLOW, AR, AB

    tt = float(t) % 1.0
    H = 1.0                                            # local unit: the CoM's standing height
    h = float(nums["height_m"])
    scale = float(nums["com_height_m"])                # metres per local unit
    W = float(nums["pelvis_width_m"]) / scale
    w = float(nums["step_width_m"]) / scale
    leg_L = float(nums["leg_length_m"]) / scale
    w0 = float(nums["fall_rate_rad_s"])
    step_s = float(nums["step_time_s"])
    duty = float(nums["duty_factor"])
    clear = float(nums["foot_clearance_m"]) / scale     # swing-foot lift, the parent's own measure

    sol = {"com_medial_offset_m": float(nums["com_medial_offset_m"]) / scale,
           "step_width_m": w}
    GT, GN = nums["gait_cycle"], int(nums["gait_samples"])
    FC, FN = nums["frontal_cycle_rad"], int(nums["frontal_sample_count"])

    # THE STRIDE'S PHASE IS OFFSET so that phase 0 of the FRONTAL cycle is the middle of a double
    # support -- which is where a step transition actually is. Derived from the published duty
    # factor, not placed: the two stance phases overlap on [0, duty - 0.5], so its centre is where
    # the body hands itself from one foot to the other.
    swap = 0.5 * max(duty - 0.5, 0.0)
    y_com, ydot, xcom, side = com_lateral(sol, w0, step_s, tt - swap)

    row = GT[int(tt * GN) % GN]
    hip_z = float(row[0]) * h / scale                  # the parent's own vertical bob, converted
    fr = FC[int(tt * FN) % FN]
    phi, trunk = float(fr[0]), float(fr[1])

    # ── the pelvis: a rigid bar of width W, TILTED, with the trunk's lean deciding where it sits ─
    # The centre of mass is above the hips, so a trunk leaning by the measured frontal angle puts
    # the pelvis to one side of the CoM by (H - hip) sin(lean). Both lengths are inherited and the
    # angle is measured; nothing here is a drawing constant.
    # + obliquity is the measured (right) side up, so the right hip rises and the left one drops by
    # the same (W/2)sin(phi). That difference is what a sagittal model has no way to represent.
    y_pel = y_com - (H - hip_z) * math.sin(trunk)
    cs, sn = math.cos(phi), math.sin(phi)
    hipR = np.array([y_pel - 0.5 * W * cs, hip_z + 0.5 * W * sn])
    hipL = np.array([y_pel + 0.5 * W * cs, hip_z - 0.5 * W * sn])

    def seg(p0, p1, n, jitter):
        u = np.linspace(0.0, 1.0, n)[:, None]
        P = np.asarray(p0)[None, :] * (1 - u) + np.asarray(p1)[None, :] * u
        return P + np.random.default_rng(19).normal(0.0, jitter, P.shape)

    pts, kind = [], []

    def add(P, k):
        pts.append(P)
        kind.append(np.full(len(P), k))

    # ── the ground, and the two feet on it ──────────────────────────────────────────────────────
    # THE GROUND IS AS WIDE AS THE WALK IS, and not a pixel wider: half a step plus a foot's
    # breadth is exactly the ground this body uses, so the frame is set by the derivation too.
    fb = 0.5 * float(nums["foot_breadth_m"]) / scale
    edge = 0.5 * w + 2.0 * fb
    gx = np.linspace(-edge, edge, 220)
    add(np.stack([gx, np.zeros(220)], 1), 1)

    ankles = []
    for i, sgn in ((0, -1.0), (1, +1.0)):              # leg 0 is the right foot, at -y
        planted = row[5 + 5 * i] > 0.5
        u_sw = float(row[4 + 5 * i])
        z = 0.0 if planted else clear * math.sin(math.pi * u_sw)
        y = sgn * 0.5 * w
        ankles.append(np.array([y, z]))
        fx = np.linspace(y - fb, y + fb, 46)
        add(np.stack([fx, np.full(46, z)], 1), 0)

    # ── the legs: hip to ankle. They splay because the pelvis above them tilted. ────────────────
    add(seg(hipR, ankles[0], 240, 0.004), 0)
    add(seg(hipL, ankles[1], 240, 0.004), 0)

    # ── the pelvis bar itself, drawn thick so its TILT is the loudest thing in the frame ────────
    for off in (-0.012, 0.0, 0.012):
        add(seg(hipR + np.array([0.0, off]), hipL + np.array([0.0, off]), 150, 0.0025), 4)
    # A LEVEL LINE THROUGH THE PELVIS CENTRE, at the same width. It is the sagittal model's pelvis:
    # both hips at one height, by construction. The bar crossing it is this chapter, and the gap at
    # each end is (W/2) sin(phi) -- the number theAnkle's residual was missing.
    add(seg([y_pel - 0.5 * W, hip_z], [y_pel + 0.5 * W, hip_z], 110, 0.0012), 7)

    # ── the upper body, as the one thing above the pelvis this chapter derives ──────────────────
    # NOTHING ELSE IS DRAWN ABOVE THE HIPS. A trunk's length and a head's size are not derived here,
    # and a render may not invent a body. What IS known is where the centre of mass is -- the parent
    # published its height -- and which way the trunk leans, which the 246 adults measured. So the
    # segment from the pelvis to the mass is drawn, and it is exactly the top of the pendulum.
    add(seg([y_pel, hip_z], [y_com, H], 90, 0.006), 0)
    # AND THE PENDULUM ITSELF: stance foot to centre of mass. This is the law, drawn as a rod, and
    # it swaps feet at the transition because the law does.
    add(seg(ankles[0] if side < 0 else ankles[1], [y_com, H], 200, 0.0035), 8)

    # ── THE TWO MARKS: where the body IS, and where it is GOING ─────────────────────────────────
    add(np.array([[y_com, H]]), 2)                                   # the centre of mass
    add(np.array([[xcom, 0.0]]), 3)                                  # the capture point, on the floor
    # a dropped line from the CoM to its own capture point, so the v/w0 lead is a visible length
    add(seg([y_com, H], [xcom, 0.0], 70, 0.0015), 5)

    # the trails: half a stride of history each, drawn from the same solution
    tr_c, tr_x = [], []
    for k in range(56):
        p = tt - swap - 0.5 * k / 56.0
        yy, _, xx, _ = com_lateral(sol, w0, step_s, p)
        tr_c.append([yy, H])
        tr_x.append([xx, 0.004])
    add(np.asarray(tr_c), 6)
    add(np.asarray(tr_x), 6)

    P = np.concatenate(pts, 0)
    K = np.concatenate(kind, 0)
    n = len(P)
    b = blank(n)
    b[:, 0] = 0.0                                      # the frontal plane, and only it
    b[:, 1] = P[:, 0]
    b[:, 2] = P[:, 1] - 0.5 * H                        # centre the framing between floor and CoM
    nrm = np.zeros((n, 3), np.float32)
    nrm[:, 0] = -1.0                                   # a plane seen face on: everything faces out
    b[:, 21:24] = nrm

    alb = np.zeros((n, 3), np.float32)
    alb[K == 0] = np.array([0.50, 0.44, 0.39], np.float32)   # the body
    alb[K == 1] = np.array([0.20, 0.22, 0.24], np.float32)   # the ground
    alb[K == 2] = np.array([1.00, 0.72, 0.25], np.float32)   # where the mass IS  (warm)
    alb[K == 3] = np.array([0.35, 0.85, 1.00], np.float32)   # where it is GOING  (cool)
    alb[K == 4] = np.array([0.86, 0.52, 0.44], np.float32)   # the pelvis bar, the chapter's subject
    alb[K == 5] = np.array([0.30, 0.46, 0.58], np.float32)   # the v/w0 lead, drawn as a length
    alb[K == 6] = np.array([0.55, 0.62, 0.80], np.float32)   # where both have already been
    alb[K == 7] = np.array([0.26, 0.28, 0.30], np.float32)   # the level line: a sagittal pelvis
    alb[K == 8] = np.array([0.42, 0.50, 0.44], np.float32)   # the pendulum rod, foot to mass
    S = float(nums.get("S_earth", 1.0))
    b[:, 16:19] = lit(alb, S * 0.85 + 0.15, e_ref=S, tone=0.45)
    b[:, AR:AB + 1] = alb
    b[:, 19] = np.where(K == 6, 0.50, np.where(K == 7, 0.45,
                        np.where(K == 5, 0.60, np.where(K == 8, 0.88, 0.96))))
    b[:, 20] = np.where((K == 2) | (K == 3), 0.030,
                        np.where((K == 6) | (K == 7), 0.009, 0.014))
    b[:, 11] = np.where((K == 2) | (K == 3), GLOW, SOLID)
    return b


def measure(nums):
    """Facts a reader can check without trusting a word of the prose above.

    THREE OF THESE FACE THE LITERATURE AND TWO OF THOSE PAPERS ARE NOT IN THIS REPO. The step-width
    check is fully internal -- 246 adults, in a file here. The sway and hip-contact checks are
    against figures quoted to ONE significant figure from memory of Orendurff et al. (2004) and
    Bergmann et al. (2001), and they are flagged `_is_quoted_not_held` so that nothing downstream
    can mistake them for measurements this story owns."""
    d = dict(nums)
    return {
        # ── THE CHECK THAT IS FULLY INTERNAL ─────────────────────────────────────────────────
        # A pelvis width from two musculoskeletal models, a step time from 246 adults, Earth's g,
        # and one geometric criterion. Nothing was fitted to a step width; here is the step width.
        "step_width_earth_m": d["step_width_earth_m"],
        "step_width_measured_m": d["step_width_measured_m"],
        "step_width_error_pct": d["step_width_error_pct"],
        "step_width_within_20pct": abs(d["step_width_error_pct"]) < 20.0,
        # and how far the one criterion -- hip over ankle at mid-stance -- actually misses by
        "leg_tilt_at_midstance_deg": d["leg_tilt_at_midstance_deg"],

        # ── THE PAYOFF: what the frontal plane hands back to theAnkle ────────────────────────
        "hip_split_double_support_frac": d["hip_split_double_support_frac"],
        "residual_list_attributed_frac": d["residual_list_attributed_frac"],
        "list_closes_share_of_residual": d["residual_closed_frac"],
        "list_covers_what_ankle_attributed": (d["hip_split_double_support_frac"]
                                              / max(d["residual_list_attributed_frac"], 1e-9)),

        # ── THE SWAY, AND ITS TREND, WHICH IS THE PART NOTHING COULD HAVE BEEN FITTED TO ─────
        # Step width is flat across a near doubling of speed; the sway falls by a third. The law
        # says the whole fall is in the step's DURATION, and here it is, three speeds of it.
        "sway_earth_slow_m": d["sway_earth_slow_m"],
        "sway_earth_comf_m": d["sway_earth_comf_m"],
        "sway_earth_fast_m": d["sway_earth_fast_m"],
        "sway_falls_with_speed": (d["sway_earth_slow_m"] > d["sway_earth_comf_m"]
                                  > d["sway_earth_fast_m"]),
        "sway_in_literature_band": 0.03 <= d["sway_earth_comf_m"] <= 0.08,
        "sway_literature_is_quoted_not_held": True,   # Orendurff et al. 2004, ~7 cm -> ~4 cm

        # ── THE HIP, WHICH IS THE OTHER UNFITTED CHECK ───────────────────────────────────────
        "hip_contact_earth_over_weight_ratio": d["hip_contact_earth_over_weight_ratio"],
        "hip_contact_near_measured_2p4BW": abs(d["hip_contact_earth_over_weight_ratio"] - 2.4) < 0.4,
        "hip_contact_literature_is_quoted_not_held": True,   # Bergmann et al. 2001, ~2.4 BW

        # ── THE THREE IDENTITIES THE CLOSED FORM CLAIMS, checked rather than asserted ────────
        "d_equals_half_pelvis": abs(d["com_medial_offset_m"] - 0.5 * d["pelvis_width_m"]) < 1e-9,
        "sway_equals_W_cosh_minus_one": abs(
            d["sway_pp_m"] - d["pelvis_width_m"] * (d["sway_gain_ratio"] - 1.0)) < 1e-9,
        "margin_equals_half_pelvis_efolded": abs(
            d["margin_of_stability_m"]
            - 0.5 * d["pelvis_width_m"] * math.exp(-d["frontal_efolds_ratio"])) < 1e-9,
        # the capture point arrives exactly one margin short of the foot it is arriving at
        "xcom_lands_one_margin_short": abs(
            d["xcom_at_contact_m"] + d["margin_of_stability_m"] - d["step_width_m"]) < 1e-9,

        # ── WHAT THE ANKLE CAN COVER, and what it cannot ─────────────────────────────────────
        "ankle_authority_used_frac": d["ankle_authority_used_frac"],
        "ankle_has_reserve": d["ankle_authority_used_frac"] < 1.0,
        "reserve_velocity_ms": d["reserve_velocity_ms"],

        # ── THE TWO MODELS, and their disagreement, kept ─────────────────────────────────────
        "pelvis_width_spread_pct": d["pelvis_width_spread_pct"],

        # ── THE ONE MEASUREMENT THIS CHAPTER REFUSED TO USE, and by how much it disagrees ────
        # The measured frontal HIP angle says the stance leg is adducted 3.8 degrees at mid-stance.
        # The pendulum, the pelvis and the step width together say 0.65. A three-degree static
        # offset is the classic frontal marker-model artefact, so the number is reported and not
        # spent -- see the module docstring.
        "hip_abad_offset_deg": (d["hip_abad_measured_at_midstance_deg"]
                                - d["leg_tilt_at_midstance_deg"]),

        # and its own rhythm needs no gearing to be watchable
        "stride_in_human_band": 0.04 <= d["duration_s"] <= 10.0,
    }
