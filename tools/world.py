"""world.py -- load a body into THE WORLD IT LIVES IN, never MuJoCo's default.

FOUND BY THE PRE-FLIGHT, 2026-08-02, and it had been true since the body arrived.

`external/myo_sim/body/myobody.xml` declares no `<option gravity>`. MuJoCo therefore applies its
built-in default of **-9.81**, and not one of the eight places in this repo that build a myobody
model ever overrode it. Every training run, every gait evaluation and every render has simulated
this walker ON EARTH -- while the membranes underneath it derived `g = 7.076 m/s^2` and the
documentation argued about which target speed to ask for.

    THE TARGET BUG AND THE WORLD BUG ARE THE SAME BUG, AND THE WORLD ONE IS WORSE.
    Earth sim + Earth target was at least SELF-CONSISTENT. Earth sim + this-world target --
    which is what deriving the target alone produces -- is strictly worse than what it replaced.
    Half a fix here is a regression.

-9.81 is also not Earth. Standard gravity is 9.80665. The default was never a decision anybody
made; it is what you get when nobody decides.

WHY THIS IS ONE MODULE AND NOT EIGHT EDITS. `EXPERIMENTAL_METHOD.md`'s remake procedure: *a
systematic pattern is ONE decision, not N edits.* Eight call sites each setting gravity is eight
chances to drift, and rule 20 is explicit that an instrument must move with the membrane and keep
no private copy of it. So the world is read from the ledger, in one place, by everything.

    from world import load_body
    m, g = load_body(MYOBODY)     # g is this world's, and the model already has it

There is NO fallback. If the ledger cannot be read, this raises -- because a default here is
exactly the thing that produced the bug.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER_MEMBRANE = "theHuman"


class WorldUnknown(RuntimeError):
    """The world will not say what its gravity is. There is no sensible default; that is the point."""


def gravity() -> float:
    """This world's g, in m/s^2, read from the membrane that owns the body."""
    hits = [p for p in (ROOT / "story").rglob("numbers.json")
            if p.parent.name == LEDGER_MEMBRANE]
    if not hits:
        raise WorldUnknown(
            f"no {LEDGER_MEMBRANE}/numbers.json under story/ -- run `python Chimera/core/grow.py`. "
            f"Refusing to assume Earth.")
    led = json.loads(hits[0].read_text(encoding="utf8"))
    if "g" not in led:
        raise WorldUnknown(
            f"{LEDGER_MEMBRANE} publishes no `g`. The number belongs to the membrane; if it is "
            f"absent the membrane must derive it. Refusing to assume Earth.")
    g = float(led["g"])
    if not (g > 0.0):
        raise WorldUnknown(f"{LEDGER_MEMBRANE} publishes g={g!r}, which is not a gravity.")
    return g


# ---------------------------------------------------------------------------------------------
# PASSIVE TISSUE -- the ligaments, 2026-08-02, added because port test 6 measured their absence.
#
# `qfrc_passive` was identically 0.00000 N.m at 10%, 50% and 90% of the knee's range with every
# actuator silent. The body had no ligaments, so the hard constraint carried the whole end-range
# load and deflected 3.566 deg past a stop it is documented to enforce (port test 5). Both
# failures are ONE missing instruction, not two broken ones.
#
# THE DERIVATION, because rule 1 forbids choosing either number.
#
#   HOW STRONG.  A ligament that could be overpowered by the muscles crossing its own joint would
#   let every maximal contraction drive that joint through its own stop, which is a dislocation.
#   Bodies do not routinely dislocate themselves. So the ligament's strength is set by what the
#   actuators on the same joint can produce, and the model already knows it. That sentence took
#   four wrong arithmetics to write down, each of which returned a plausible number:
#
#     - `sum |moment * F_max|` added the ANTAGONISTS as though they helped. A ligament at the
#       extension stop is loaded by the extensors; the flexors pull away from it. 6x too stiff.
#     - the signed version read the sign of `moment` alone. Muscle force is NEGATIVE in MuJoCo --
#       a muscle pulls, it never pushes -- so the torque is `moment * force` and the sign of the
#       moment says the opposite of what it looks like.
#     - `F_max` from gainprm is peak ISOMETRIC force, which a muscle at an extreme joint angle is
#       nowhere near: 2212 N nominal against 719 N actually produced. Sizing a structure for a
#       load that never arrives. The model's own `actuator_force` carries the force-length curve.
#     - evaluated AT THE LIMIT it read ~0 for the knee, because at 120 deg the hamstrings are
#       fully shortened and make no force -- which is why you cannot actively flex your knee past
#       about 120 deg. True physiology, wrong number: the ligament still has to CATCH what was
#       launched from mid-band. The bound is the MAX OVER THE BAND.
#
#   And it is measured from `qpos0`, not the keyframe. Off the keyframe the left and right knee
#   came out 294 vs 504 N.m/rad on an anatomically symmetric body -- biarticular muscles reading a
#   stored asymmetric pose. A ligament is a property of a joint and must not depend on what the
#   rest of the body happens to be doing. L == R is now a CHECK; they agree to 0.6%.
#
#   HONEST BOUND: this sizes the ligament to hold MAXIMUM VOLUNTARY CONTRACTION at the stop, which
#   is an UPPER bound. Real passive moment-angle curves are softer and exponential rather than
#   linear, because reflex withdrawal shares the job -- the GTO, which is port 9. Measured human
#   passive moment-angle curves are the outstanding data item here, alongside ISB via-points and
#   the sensor noise floors.
#
#   WHERE IT GOES TAUT.  A ligament is slack through the motion the body actually performs; that
#   is what "range of motion" means. The parent publishes that motion: `theHuman.gait_envelope_deg`
#   is 101 samples of hip, knee and ankle through one cycle. The deadband is the envelope; the
#   ligament engages between the envelope's edge and the joint's own published limit.
#
#   k = tau_max / gap.  Nothing here is selected.
#
# AND WHERE IT REFUSES.  As `gap -> 0`, `k -> infinity`, and an infinitely stiff ligament is not a
# ligament -- it is a constraint, which the model already has. The honest floor is the envelope's
# own grain: the largest step between consecutive samples. A gap narrower than one sample step is
# not a small gap, it is a gap the instrument cannot see, and the difference matters -- walking
# takes the knee to 1.84 deg against a 0 deg extension stop, which does not mean the extension
# ligament engages over 1.84 deg. It means this dataset cannot say. So that side gets NO ligament
# and gets NAMED, rather than a plausible number nobody could check.
# ---------------------------------------------------------------------------------------------

# model joint -> the envelope key that reports its motion. Signs are NOT assumed to agree; the
# derivation asserts the envelope lies inside the joint's own range and raises if it does not.
LIGAMENT_JOINTS = {
    "hip_flexion_r": "hip", "hip_flexion_l": "hip",
    "knee_angle_r": "knee", "knee_angle_l": "knee",
    "ankle_angle_r": "ankle", "ankle_angle_l": "ankle",
}

# THE TRUNK, 2026-08-04 -- docs/THE_TRUNK_TISSUE.md, opened by F3's judged debt: the stand
# policy arches L4_L5_FE 1.14-1.34x past its declared stop because no ligament acts there.
# The lumbar FE hinges have no gait envelope, so the derivation above could not reach them --
# but the envelope EDGE is published: intersegmental extension tilt rarely exceeds 5 deg in
# vivo (Pearcy & Tibrewal 1984, three-dimensional radiography; cited in Miller et al. 1986).
# Extension is the NEGATIVE direction in this model -- F3's measured violation sat at -14.6 deg
# against a -10.7 stop. Only the extension side is derived: the model's own flexion limit
# (+4.8 deg) sits INSIDE the ~15 deg per-segment performed envelope (Adams & Hutton 1982;
# Pearcy et al. 1984), so there is no gap to derive across -- named, not fitted.
LUMBAR_FE_JOINTS = ("L1_L2_FE", "L2_L3_FE", "L3_L4_FE", "L4_L5_FE")
LUMBAR_EXT_EDGE_DEG = -5.0       # the published in-vivo extension envelope edge (Pearcy & Tibrewal 1984)
LUMBAR_GRAIN_DEG = 1.0           # 3-D radiography resolution: a gap under this is invisible (Pearcy & Tibrewal 1984)

# LATERAL BENDING, same membrane, same citation, added 2026-08-04 when the leak moved:
# with the extension ligament in, the retrained stand policy stopped arching and started
# LEANING -- lat_bending -28.2 deg against a -25 stop, L1_L2_LB 1.13x. Miller 1986:
# "in extension AND LATERAL BENDING the maximum intervertebral tilt in the lumbar spine
# has been reported to rarely exceed 5 deg in vivo (Bakke 1931; Pearcy and Tibrewal
# 1984)". Both directions get the ligament where a gap exists; a level whose own stop
# sits inside the performed envelope (L1_L2_LB is +-4.7 deg) is refused, not fitted.
LUMBAR_LB_JOINTS = ("lat_bending", "L1_L2_LB", "L2_L3_LB", "L3_L4_LB", "L4_L5_LB")
LUMBAR_LAT_EDGE_DEG = 5.0        # the published in-vivo lateral-tilt envelope edge, each way (Bakke 1931; Pearcy & Tibrewal 1984, per Miller 1986)

# THE FOOT & HIP, 2026-08-04 -- docs/THE_FOOT_TISSUE.md: the off-sagittal joints the gait
# envelope does not publish. Edges from the literature (the membrane's research section);
# signs MEASURED from the actuator moments, never assumed: hip_adduction's POSITIVE side is
# loaded by glmed/glmin/tfl (the ABductors) -- the model's + end is abduction, which INVERTS
# the membrane table's first-principles guess (the table flagged itself; the measurement
# wins). Subtalar + is eversion (peroneals), hip_rotation + is external (piri/glmax).
OFFSAG_JOINTS = ("subtalar_angle_r", "subtalar_angle_l",
                 "hip_rotation_r", "hip_rotation_l",
                 "hip_adduction_r", "hip_adduction_l")
OFFSAG_EDGES = {     # joint base -> (edge at the model's lo end, edge at the hi end), deg
    "subtalar_angle": (-9.0, 9.0),   # Mann 6-8 deg gait; Campbell fluoroscopy peak 8.7
    "hip_rotation": (-8.0, 8.0),     # Kadaba via Lewis 2017; Winter's caveat carried
    "hip_adduction": (-9.0, 5.0),    # lo = ADDuction (Goetschius peak 8.8), hi = ABduction
}
OFFSAG_GRAIN_DEG = 1.0               # goniometry/fluoroscopy resolution, same as the trunk
# MTP IS REFUSED AT THE MEMBRANE, not here: the model's +-30 deg stop sits INSIDE the
# published 60-65 deg gait dorsiflexion envelope -- the stop contradicts gait, and a
# ligament cannot be derived across a stop that is wrong. The model-range amendment is
# its own membrane. The refused list below names it so nothing looks forgotten.


def _ledger() -> dict:
    hits = [p for p in (ROOT / "story").rglob("numbers.json") if p.parent.name == LEDGER_MEMBRANE]
    if not hits:
        raise WorldUnknown(f"no {LEDGER_MEMBRANE}/numbers.json under story/ -- run "
                           f"`python Chimera/core/grow.py`. Refusing to assume Earth.")
    return json.loads(hits[0].read_text(encoding="utf8"))


def _derive_side(m, d, mujoco, jname, adr, dof, lo, hi, side, limit, edge, grain):
    """One ligament, one side: k = tau_max / gap. Returns (entry, None) or (None, reason).

    tau_max is the MAX OVER THE BAND, not the value at the limit. Measured at the limit
    the knee reads ~0, because at 120 deg the hamstrings are fully shortened and make no
    force -- which is why you cannot actively flex your knee past about 120 deg. That is
    real physiology and it is the wrong number: the ligament still has to CATCH what was
    launched at it from mid-band, where the flexors are strong. A structure is sized by
    the largest load it can meet, not by the load present at the instant it is met.

    SIGNED, and the sign is the whole point. A ligament at the extension stop is loaded
    by the EXTENSORS; the flexors pull away from it. `sum |moment * F_max|` added the
    antagonists as though they helped and came out ~6x too stiff.

    AND ACTIVATION IS `act`, NOT `ctrl`. `ctrl` is excitation; the force reads `act`,
    which is a state with 15 ms dynamics (port test 3 measured it). A pass that sets
    ctrl and calls mj_forward changes nothing about the force -- it silently reports the
    keyframe's activation. Same species as the dense-reshape bug: a wrong index that
    RAISES costs an hour, a wrong index that returns a plausible number costs a diagnosis.
    """
    import math
    import numpy as np

    gap = abs(limit - edge)
    if gap <= grain:
        return None, (f"gap {math.degrees(gap):.2f} deg <= envelope grain "
                      f"{math.degrees(grain):.2f} deg -- unresolvable, not small")
    want = 1.0 if side == "flex" else -1.0
    n_samp = max(2, int(gap / grain) + 1)
    tau = 0.0
    for i in range(n_samp + 1):
        # FROM qpos0, NOT THE KEYFRAME. A ligament is a property of a joint; it must not
        # depend on what the rest of the body happens to be doing in one stored pose. Off
        # the keyframe the left and right knee ligaments came out 294 vs 504 N.m/rad on a
        # body that is anatomically symmetric -- biarticular muscles reading the keyframe's
        # asymmetric hips. qpos0 is the model's own reference configuration and is
        # symmetric by construction, so L == R becomes a CHECK rather than a hope.
        mujoco.mj_resetData(m, d)
        d.qpos[adr] = edge + (limit - edge) * i / n_samp
        d.qvel[:] = 0.0
        d.ctrl[:] = 1.0
        if m.na:
            d.act[:] = 1.0                      # the muscles at full drive, actually
        mujoco.mj_forward(m, d)
        flat = np.asarray(d.actuator_moment).ravel()
        s = 0.0
        for k in range(m.nu):
            n0, a0 = int(d.moment_rownnz[k]), int(d.moment_rowadr[k])
            for e in range(n0):
                if int(d.moment_colind[a0 + e]) == dof:
                    t = float(flat[a0 + e]) * float(d.actuator_force[k]) * want
                    if t > 0.0:                 # only what drives INTO this limit
                        s += t
        tau = max(tau, s)
    if not (tau > 0.0):
        return None, "no muscle spans this joint -- nothing to out-resist"

    pad = 10.0  # rad, far outside any joint range: makes each ligament one-directional
    band = (edge, hi + pad) if side == "ext" else (lo - pad, edge)
    return dict(joint=jname, side=side, name=f"lig_{jname}_{side}",
                k=tau / gap, tau=tau, gap=gap, edge=edge, limit=limit,
                band=band, grain=grain), None


def derive_ligaments(m, mujoco) -> tuple[list, list]:
    """Derive every ligament this world's published data can support. Returns `(emit, refused)`.

    Each emitted entry is a dict with the two numbers and the arithmetic that produced them, so
    the caller can print the derivation rather than assert it.
    """
    import math

    led = _ledger()
    env = led.get("gait_envelope_deg")
    if not isinstance(env, dict):
        raise WorldUnknown(
            f"{LEDGER_MEMBRANE} publishes no `gait_envelope_deg` -- without the motion the body "
            f"actually performs there is nothing to derive a slack range from, and a chosen "
            f"deadband is a fitted ligament. Refusing.")

    d = mujoco.MjData(m)
    emit, refused = [], []
    for jname, ekey in LIGAMENT_JOINTS.items():
        j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jname)
        if j < 0 or ekey not in env:
            refused.append((jname, "both", "no published envelope for this joint"))
            continue
        adr, dof = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
        lo, hi = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
        samples = [math.radians(float(x)) for x in env[ekey]]
        e_lo, e_hi = min(samples), max(samples)

        # THE SIGN CHECK. If the dataset's convention disagreed with the model's, the envelope
        # would fall outside the joint's own range -- and a flipped ligament would resist the
        # motion it is supposed to permit. Dimensionally invisible; caught only by asking.
        if e_lo < lo - 1e-9 or e_hi > hi + 1e-9:
            raise WorldUnknown(
                f"{jname}: published envelope [{math.degrees(e_lo):+.2f}, {math.degrees(e_hi):+.2f}]"
                f" deg falls outside the model's range [{math.degrees(lo):+.2f}, "
                f"{math.degrees(hi):+.2f}] deg. The two sign conventions disagree; a ligament "
                f"derived across them would resist normal motion. Refusing.")

        grain = max(abs(samples[i + 1] - samples[i]) for i in range(len(samples) - 1))

        for side, limit, edge in (("flex", hi, e_hi), ("ext", lo, e_lo)):
            entry, why = _derive_side(m, d, mujoco, jname, adr, dof, lo, hi,
                                      side, limit, edge, grain)
            (emit.append(entry) if entry else refused.append((jname, side, why)))

    # THE LUMBAR, per docs/THE_TRUNK_TISSUE.md. Extension side only, envelope edge published
    # (LUMBAR_EXT_EDGE_DEG), per-level gap from the model's OWN declared ranges -- so a level
    # whose range does not reach the envelope edge is refused by the same grain rule, not by
    # an exception written here.
    edge = math.radians(LUMBAR_EXT_EDGE_DEG)
    grain = math.radians(LUMBAR_GRAIN_DEG)
    for jname in LUMBAR_FE_JOINTS:
        j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jname)
        if j < 0:
            refused.append((jname, "ext", "joint not in this model"))
            continue
        adr, dof = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
        lo, hi = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
        # THE SIGN CHECK, lumbar form: the published extension envelope must lie between the
        # model's two stops. If the model ever flips its FE convention this raises instead of
        # emitting a ligament that resists the motion it is meant to permit.
        if not (lo < edge < hi):
            raise WorldUnknown(
                f"{jname}: published extension edge {LUMBAR_EXT_EDGE_DEG:+.1f} deg falls outside "
                f"the model's range [{math.degrees(lo):+.2f}, {math.degrees(hi):+.2f}] deg. The "
                f"sign conventions disagree. Refusing.")
        entry, why = _derive_side(m, d, mujoco, jname, adr, dof, lo, hi,
                                  "ext", lo, edge, grain)
        (emit.append(entry) if entry else refused.append((jname, "ext", why)))
        refused.append((jname, "flex",
                        "model's flexion stop sits inside the ~15 deg performed envelope "
                        "(Adams & Hutton 1982) -- no gap, nothing to derive"))

    # LATERAL BENDING, both directions, per the leak the FE ligament exposed. A level whose
    # own stop does not reach the published edge has no gap on that side -- refused, named.
    lat = math.radians(LUMBAR_LAT_EDGE_DEG)
    for jname in LUMBAR_LB_JOINTS:
        j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jname)
        if j < 0:
            refused.append((jname, "both", "joint not in this model"))
            continue
        adr, dof = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
        lo, hi = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
        for side, limit, edge in (("flex", hi, lat), ("ext", lo, -lat)):
            if (side == "flex" and limit <= edge) or (side == "ext" and limit >= edge):
                refused.append((jname, side,
                                f"model's stop {math.degrees(limit):+.1f} deg sits inside the "
                                f"{LUMBAR_LAT_EDGE_DEG:.0f} deg performed envelope -- no gap"))
                continue
            entry, why = _derive_side(m, d, mujoco, jname, adr, dof, lo, hi,
                                      side, limit, edge, grain)
            (emit.append(entry) if entry else refused.append((jname, side, why)))

    # THE FOOT & HIP, off-sagittal, per docs/THE_FOOT_TISSUE.md. Both directions where the
    # model's stop clears the literature edge; refused and named where it does not.
    ograin = math.radians(OFFSAG_GRAIN_DEG)
    for base, (e_lo_deg, e_hi_deg) in OFFSAG_EDGES.items():
        for sfx in ("_r", "_l"):
            jname = base + sfx
            j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jname)
            if j < 0:
                refused.append((jname, "both", "joint not in this model"))
                continue
            adr, dof = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
            lo, hi = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
            for side, limit, edge in (("flex", hi, math.radians(e_hi_deg)),
                                      ("ext", lo, math.radians(e_lo_deg))):
                if (side == "flex" and limit <= edge) or (side == "ext" and limit >= edge):
                    refused.append((jname, side,
                                    f"model's stop {math.degrees(limit):+.1f} deg sits inside "
                                    f"the performed envelope -- no gap"))
                    continue
                entry, why = _derive_side(m, d, mujoco, jname, adr, dof, lo, hi,
                                          side, limit, edge, ograin)
                (emit.append(entry) if entry else refused.append((jname, side, why)))
    refused.append(("mtp_angle_r/l", "both",
                    "model's +-30 deg stop sits INSIDE the published 60-65 deg gait "
                    "dorsiflexion envelope -- the stop contradicts gait, not the tissue; "
                    "the model-range amendment is its own membrane (docs/THE_FOOT_TISSUE.md)"))
    return emit, refused


# ── THE MTP ENVELOPE ──────────────────────────────────────────────────────────────────────────
# RULE 0, stated before the change:
#
#   STATEMENT   myobody declares the metatarsophalangeal joint at +/-30 deg. Human walking
#               demands 60-65 deg of HALLUX DORSIFLEXION at terminal stance -- the toes bend up
#               as the heel rises and the body rolls over the forefoot. A joint whose model range
#               is half what the motion needs sits at its stop, and `stand_reward`'s joints term
#               is exp(-((jf-0.8)/0.1)^2), which is ~0 for any jf >= 1.0. The term is a FACTOR,
#               so a permanently-pinned MTP multiplies the whole reward toward zero and the
#               search sees no gradient from anything else it does.
#
#   PREDICTION  Widened to the published envelope, F3's per-joint table shows mtp_angle_l falling
#               from "over its stop 97.6% of phase 1" to near zero, jmax drops, and the joints
#               factor r_j rises measurably on the SAME saved theta.
#
#   FALSIFIER   If F3's verdict and r_j do not change, the MTP was not the binding constraint --
#               revert and report it. (This is the task's own stated falsifier and it is a real
#               one: three other joints are also over their stops, and if they dominate the max
#               then freeing the MTP moves nothing.)
#
# WHICH SIDE OF THE RANGE, and this is where a naive fix would have proved nothing. The two MTP
# joints have MIRRORED AXES in the model -- r is `0.580954 0 -0.813936`, l is `-0.580954 0
# -0.813936` -- so one physical direction is +theta on the right and -theta on the left. MEASURED
# over a 5 s stand on the saved theta, 2026-08-04:
#
#     mtp_angle_r   mean +17.16 deg, max +29.88   -> pinned at its UPPER stop
#     mtp_angle_l   mean -29.87 deg, min -32.91   -> pinned at its LOWER stop, 2.9 deg PAST it
#
# Two independent routes -- the model's own axis signs, and where the body actually drives each
# joint -- agree on the same answer. Widening symmetrically would have added 35 deg of
# PLANTARflexion nobody asked for; widening one side only would have freed one foot and left the
# other pinned, and the run would have read as a refutation of a change that was never made.
#
# 65 deg is the envelope's upper edge from the clinical gait literature (hallux dorsiflexion
# required for normal walking, commonly given as 60-65 deg); the plantarflexion side is left at
# the model's own 30 deg, which is inside the published 30-40 deg. Taken from the literature
# exactly as the trunk membrane took its ligament edge, because theHuman's `gait_envelope_deg`
# publishes hip, knee and ankle only -- it has no curve for the toe.
MTP_DORSIFLEX_DEG = 65.0         # hallux dorsiflexion ROM, clinical gait literature (Root et al. 1977; Perry 1992)
MTP_SIDE_SIGN = {"mtp_angle_r": +1.0, "mtp_angle_l": -1.0}   # measured above, not assumed


def _widen_mtp(m, mujoco, deg) -> list:
    """Set the MTP joints' dorsiflexion limit on the LOADED MODEL. Returns what it changed.

    NOT AN XML REWRITE, and the first version was -- it regex'd `myobody.xml` and refused,
    correctly, with "no <joint name=mtp_angle_r ... range=...>". The MTP joints are declared four
    include levels down in `leg/assets/myolegs_chain.xml`; myobody.xml only includes it. Rewriting
    an included file means rewriting the include tree, and MJCF has no attribute-override
    mechanism to do it from the parent. `m.jnt_range` is writable on the loaded model and is the
    same quantity the solver reads, so the change is applied there -- one line, no generated
    files, and nothing vendored is touched.

    The refusal that sent me here is kept in spirit: this raises if a joint is absent rather than
    reporting a widening that did not happen.
    """
    import math
    rad, changed = math.radians(float(deg)), []
    for jname, sign in MTP_SIDE_SIGN.items():
        j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jname)
        if j < 0:
            raise WorldUnknown(f"no joint {jname!r} in this model. Refusing to report an MTP "
                               f"widening that did not happen (rule 20).")
        before = (float(m.jnt_range[j][0]), float(m.jnt_range[j][1]))
        lo, hi = (before[0], rad) if sign > 0 else (-rad, before[1])
        m.jnt_range[j] = (lo, hi)
        changed.append((jname, math.degrees(before[0]), math.degrees(before[1]),
                        math.degrees(lo), math.degrees(hi)))
    return changed


def _tissue_xml(xml_path, emit) -> "Path":
    """Write the body + its ligaments as a sibling file, so every relative path still resolves.

    Content-hashed and written once: `load_body` is called from parallel trainer workers, and two
    of them racing on one filename is a corrupt model that would be blamed on the physics.
    """
    import hashlib
    import os

    src = Path(xml_path)
    rows = "\n".join(
        f'    <fixed name="{e["name"]}" springlength="{e["band"][0]:.9f} {e["band"][1]:.9f}" '
        f'stiffness="{e["k"]:.6f}">\n'
        f'      <joint joint="{e["joint"]}" coef="1"/>\n'
        f'    </fixed>' for e in emit)
    block = ("  <!-- PASSIVE TISSUE. Derived by tools/world.py from theHuman's published gait\n"
             "       envelope and this model's own peak muscle torque. Generated -- do not edit;\n"
             "       edit the derivation. -->\n"
             f"  <tendon>\n{rows}\n  </tendon>\n")
    text = src.read_text(encoding="utf8")
    i = text.rfind("</mujoco>")
    if i < 0:
        raise WorldUnknown(f"{src} has no </mujoco> to insert passive tissue before")
    out = text[:i] + block + text[i:]
    dst = src.with_name(f"_tissue_{hashlib.sha1(out.encode('utf8')).hexdigest()[:8]}.xml")
    if not dst.exists():
        tmp = dst.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(out, encoding="utf8")
        os.replace(tmp, dst)
    return dst


def _pivot_xml(xml_path, body, anchor, kind="connect", hang_z=0.0) -> "Path":
    """Write the body + one world equality as a sibling file: a pivot INSIDE THE SOLVER.

    A pendulum needs its pivot INSIDE THE SOLVER. A kinematic pin (restoring qpos each step)
    only projects the position afterwards -- the constraint force that turns gravity into
    torque about the pivot never enters the dynamics, and the "pendulum" reads 0.42 rad/s of
    brace sway against a 2.76 prediction. The equality makes the solver supply that force.

    TWO KINDS, for two different pendulums:
      connect -- a BALL JOINT to the world at `anchor` (body-local). Fixes the point's POSITION,
                  leaves it free to rotate. That is an INVERTED PENDULUM pivoting on a foot: the
                  whole body must be able to tip about that point (`a_balance`).
      weld -- fixes the body's position AND orientation to the world. The pivot cannot move or
                turn at all, so only the joints you leave free can move. That is a COMPOUND
                PENDULUM hung from a rigid point: `a_swing` welds the pelvis and frees one hip,
                because a ball joint there lets the pelvis counter-rotate against the swinging leg
                (measured 17% fast) while a kinematic pin reads 16% slow -- the truth is only
                reachable with a pivot that is rigid in the solver. `anchor` is unused for welds.

    `hang_z` (welds only): MuJoCo bakes an equality's reference transform from qpos0 AT COMPILE
    TIME, and qpos0 is the body standing on the floor -- so a weld compiled there drags any
    runtime lift back down to floor level (the "free fall" that looked like a rigidity failure).
    The hang height must therefore be baked into qpos0 itself: this bumps the root free-joint
    body's `pos z` by `hang_z` before compiling, so the weld's reference IS the lifted pose and
    holds it rigidly. The test then resets with mj_resetData (qpos0), never a keyframe -- the
    authored keyframe is an independent pose that does not track this bump.
    """
    import hashlib
    import os
    import re

    src = Path(xml_path)
    expected_root_z = None
    if kind == "weld" and hang_z:
        # Bump the FIRST <body ... pos="x y z"> inside worldbody -- the free root whose pos IS
        # qpos[0:3]. Everything hangs below it, so lifting it lifts the whole body clear of the
        # floor without touching any joint angle or the welded (child) body's local frame.
        m = re.search(
            r'(<worldbody>.*?<body\b[^>]*?\bpos=")([-+]?\d*\.?\d+)( [-+]?\d*\.?\d+)'
            r'( [-+]?\d*\.?\d+)(")', src.read_text(encoding='utf8'), re.S)
        if not m:
            raise WorldUnknown(f"{src} has no root <body pos> to hang {hang_z:+.3f} m from")
        z = float(m.group(4)) + float(hang_z)
        expected_root_z = z          # what the free-joint body's qpos0 z MUST read back as
        text = (src.read_text(encoding='utf8')[:m.start()]
                + m.group(1) + m.group(2) + m.group(3) + f" {z:.6f}" + m.group(5)
                + src.read_text(encoding='utf8')[m.end():])
    else:
        text = src.read_text(encoding='utf8')
    if kind == "weld":
        # THE WELD MUST BE STIFF, AND MUJOCO'S DEFAULT IS NOT. An equality is a soft constraint
        # (solref/solimp like a contact); at the default solref 0.02 this heavy body sags ~16 cm
        # off its pivot under gravity even at rest, and a moving pivot corrupts the period
        # (a_swing read 15.4% fast). Stiffen to the codebase's bond value (port_tests_matter.py):
        # solref 1e-5 -> ~1 cm residual, and the swing reads its true period (12.4%, under bar).
        block = ("  <!-- PIVOT (WELD). The body is welded to the world -- position AND orientation\n"
                 "       fixed, so only the joints left free can move. Injected by tools/world.py;\n"
                 "       do not edit the file, edit the call. -->\n"
                 "  <equality>\n"
                 f'    <weld body1="{body}" body2="world" solref="1e-5 1"\n'
                 '         solimp="0.9999 0.99999 1e-6 0.5 2"/>\n'
                 "  </equality>\n")
    else:
        block = ("  <!-- PIVOT. A ball joint to the world for the inverted-pendulum measurement;\n"
                 "       injected by tools/world.py -- do not edit the file, edit the call. -->\n"
                 "  <equality>\n"
                 f'    <connect body1="{body}" body2="world" '
                 f'anchor="{anchor[0]:.6f} {anchor[1]:.6f} {anchor[2]:.6f}"/>\n'
                 "  </equality>\n")
    i = text.rfind("</mujoco>")
    if i < 0:
        raise WorldUnknown(f"{src} has no </mujoco> to insert a pivot before")
    out = text[:i] + block + text[i:]
    dst = src.with_name(f"_pivot_{hashlib.sha1(out.encode('utf8')).hexdigest()[:8]}.xml")
    if not dst.exists():
        tmp = dst.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(out, encoding="utf8")
        os.replace(tmp, dst)
    return dst, expected_root_z


def load_body(xml_path, mujoco=None, tissue=True, verbose=False, pivot=None, fix_body=None,
              hang_z=0.0):
    """Load an MJCF and put it in this world, with its passive tissue. Returns `(model, g)`.

    Prints what it changed, because a silent world change is how the original defect survived:
    nothing in the logs ever said which gravity a run had used, so nothing could contradict it.

    `pivot=(body_name, anchor_local)` injects a ball-joint-to-the-world equality constraint at
    that point on that body -- the inverted-pendulum instrument (position fixed, rotation free).
    `fix_body=body_name` welds that body to the world instead -- position AND orientation fixed,
    so only joints you leave free can move; the compound-pendulum instrument. See `_pivot_xml`.
    `hang_z` (with fix_body) lifts the whole body that far above the floor by baking it into
    qpos0 before the weld is compiled, so the weld holds the lifted pose rigidly instead of
    dragging a runtime lift back to floor level. Reset with mj_resetData, never a keyframe.
    """
    if mujoco is None:
        import mujoco  # local import: this module is useful without it (see `gravity()`)
    g = gravity()
    # THE MTP WIDENING, opt-in via the environment so the A/B changes ONE thing. Every harness
    # (f3_stand, f4_walk, the trainers) calls `load_body` with no extra argument, so an env
    # switch is what lets the identical judge run against two worlds -- add a parameter instead
    # and the arms would differ by a call-site edit as well as by the world. Absent or 0 = the
    # model's own +/-30 deg, untouched.
    _mtp = os.environ.get("CHIMERA_MTP_DEG", "").strip()
    m = mujoco.MjModel.from_xml_path(str(xml_path))

    # SEAT THE KEYFRAME INSIDE THE BODY'S OWN LIMITS. myobody's keyframe starts hip_flexion_l at
    # -40.39 deg against a published range of [-30, +120], and both knees a few degrees
    # hyperextended. With no passive tissue the constraint solver absorbed that silently, which is
    # why it survived unnoticed; a ligament is a spring, and a spring held past its engagement
    # point PUSHES -- 689.57 N.m on that hip at t=0, which threw the body into a tangle and made
    # the foot sensors read 4.4 N while three metres in the air. The sensor was fine.
    #
    # A pose outside the joint's own range is not a pose the body can hold. Clamping to the
    # PUBLISHED range and nothing else: the limit is the body's number, not a margin I picked.
    if tissue:
        emit, refused = derive_ligaments(m, mujoco)
        if emit:
            xml_path = _tissue_xml(xml_path, emit)
            m = mujoco.MjModel.from_xml_path(str(xml_path))
            if verbose:
                for e in emit:
                    import math
                    print(f"[tissue] {e['name']:28} k = {e['tau']:7.1f} N.m / "
                          f"{math.degrees(e['gap']):5.2f} deg = {e['k']:9.1f} N.m/rad")
                for jn, side, why in refused:
                    print(f"[tissue] REFUSED {jn}/{side}: {why}")
    if pivot is not None:
        xml_path, _ = _pivot_xml(xml_path, pivot[0], pivot[1])
        m = mujoco.MjModel.from_xml_path(str(xml_path))
        print(f"[world] pivot: ball joint to world at {pivot[0]} {pivot[1]}")
    if fix_body is not None:
        xml_path, expected_root_z = _pivot_xml(
            xml_path, fix_body, (0.0, 0.0, 0.0), kind="weld", hang_z=hang_z)
        m = mujoco.MjModel.from_xml_path(str(xml_path))
        if expected_root_z is not None:
            # THE BUMP MUST HAVE LANDED. A regex that hit the wrong <body> -- or a compile that
            # dropped it -- would leave qpos0 at floor level and the weld would drag any lift back
            # down, indistinguishable from a physics result without this check. The free-joint
            # body's world z in qpos0 is exactly what we bumped (jnt_type 0 = FREE; 1 is BALL), so assert it.
            landed = any(
                abs(float(m.qpos0[int(m.jnt_qposadr[jj]) + 2]) - expected_root_z) < 1e-3
                for jj in range(m.njnt) if m.jnt_type[jj] == 0)
            if not landed:
                raise WorldUnknown(
                    f"hang_z bump did not land: no free-joint body has qpos0 z = "
                    f"{expected_root_z:.6f} -- the root <body pos> regex hit the wrong element")
        print(f"[world] pivot: {fix_body} WELDED to world (position + orientation fixed)"
              + (f", hung {hang_z:+.3f} m above floor (baked into qpos0, verified)" if hang_z else ""))
    # SEATED AFTER THE TISSUE RELOAD, and the order is load-bearing. It ran BEFORE first:
    # it clamped key_qpos on the model that the tissue reload then THREW AWAY, and printed
    # a confident 'seated 1' while changing nothing -- the plantar sensor read back
    # identical to four decimals, which is what caught it. A fix applied to an object that
    # is about to be replaced is the same silent-success species as the double registry.
    # ONLY THE JOINTS THIS CHANGE PUT A LIGAMENT ON. A first pass clamped every out-of-range
    # keyframe joint and moved 16 of them -- including `knee_angle_r_rotation2`,
    # `knee_angle_r_translation1` and four more, which are the OpenSim knee's COUPLED degrees of
    # freedom, driven from `knee_angle_r` by equality constraints. They are not free, their
    # published ranges are nominal, and clamping them independently puts the knee in a
    # configuration inconsistent with its own coupling. Fixing what this change broke is repair;
    # clamping those is meddling, and it would have been invisible under a summary line.
    #
    # The lumbar joints are genuinely out of range too. Until 2026-08-04 no ligament acted
    # there, so they were NAMED and left alone; the trunk membrane (docs/THE_TRUNK_TISSUE.md)
    # now derives their extension ligaments, and an out-of-range start is a ligament held past
    # its engagement point at t=0 -- the same 689 N.m defect the seating exists to prevent.
    seated, noted = [], []
    for k in range(m.nkey):
        for j in range(m.njnt):
            if not m.jnt_limited[j] or m.jnt_type[j] not in (2, 3):   # slide, hinge
                continue
            a = int(m.jnt_qposadr[j])
            lo, hi = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
            q = float(m.key_qpos[k][a])
            if lo <= q <= hi:
                continue
            nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j) or f"j{j}"
            if (nm in LIGAMENT_JOINTS or nm in LUMBAR_FE_JOINTS or nm in LUMBAR_LB_JOINTS
                    or nm in OFFSAG_JOINTS):
                m.key_qpos[k][a] = min(max(q, lo), hi)
                seated.append((nm, q, float(m.key_qpos[k][a])))
            else:
                noted.append(nm)
    # THE OFF-SAGITTAL DEADBAND, 2026-08-04 -- the foot membrane's falsifier 2 fired and
    # taught this: a keyframe INSIDE the range but PAST a ligament's engagement edge starts
    # the body with the spring taut, and the range-clamp above never sees it. Measured:
    # the keyframe's hip_rotation_r sits at -35.18 deg against the -8 deg literature edge --
    # 113 N.m of phantom torque at t=0, the 689 N.m defect one level subtler. A gait frame's
    # transverse rotation frozen into a stand is not a pose the body can hold NEUTRALLY, so
    # the off-sagittal joints are seated to their published edges (zero deflection there).
    import math as _math2
    for k in range(m.nkey):
        for j in range(m.njnt):
            nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j) or ""
            base = nm[:-2] if nm.endswith(("_r", "_l")) else nm
            if base not in OFFSAG_EDGES:
                continue
            a = int(m.jnt_qposadr[j])
            e_lo, e_hi = (_math2.radians(x) for x in OFFSAG_EDGES[base])
            q = float(m.key_qpos[k][a])
            if e_lo <= q <= e_hi:
                continue
            m.key_qpos[k][a] = min(max(q, e_lo), e_hi)
            seated.append((nm, q, float(m.key_qpos[k][a])))
    if seated or noted:
        import math as _math
        print(f"[world] keyframe: seated {len(seated)}, left alone {len(noted)} "
              f"(out of range, no ligament -- not this change's to move)")
        if verbose:
            for nm, was, now in seated:
                print(f"[world]   seated {nm:18} {_math.degrees(was):+8.2f} -> "
                      f"{_math.degrees(now):+8.2f} deg")
            for nm in noted:
                print(f"[world]   noted  {nm}")

    before = float(m.opt.gravity[2])
    m.opt.gravity[2] = -g
    if abs(before + g) > 1e-9:
        print(f"[world] gravity {before:+.5f} -> {-g:+.6f} m/s^2  "
              f"({g / 9.80665:.4f} of Earth, from {LEDGER_MEMBRANE})")
    assert abs(float(m.opt.gravity[2]) + g) < 1e-12, "gravity did not take"
    # THE MTP WIDENING, applied LAST and on the final model. Order is load-bearing for the same
    # reason the keyframe seat is: everything above may reload the model (tissue, pivot), and a
    # range set on a model that is then thrown away is a change that prints and does not happen
    # -- the defect `seat_in_limits` already paid for once ("it clamped key_qpos on the model
    # that the tissue reload then THREW AWAY, and printed a confident 'seated 1'").
    if _mtp and float(_mtp) > 0:
        for nm, b0, b1, a0, a1 in _widen_mtp(m, mujoco, float(_mtp)):
            print(f"[world] mtp {nm:14} [{b0:+.1f},{b1:+.1f}] -> [{a0:+.1f},{a1:+.1f}] deg "
                  f"(CHIMERA_MTP_DEG -- published hallux dorsiflexion)")

    # THE HARD STOP, 2026-08-25 -- port test 5 (joint_limit) measured 3.555 deg of steady-state
    # penetration past the knee's published +120 deg under a sustained 400 N.m drive. The
    # ligaments are innocent: they were sized to hold MAXIMUM VOLUNTARY CONTRACTION, and they
    # do. The leak is MuJoCo's DEFAULT limit impedance -- jnt_solimp d_max = 0.95 leaves the
    # stop permanently 5%-compliant, so any sustained overload walks through it at equilibrium.
    # Mother Nature's joint stops are GEOMETRY (bone face on bone face): compliant while
    # approaching, effectively rigid once reached. That is ology "MuJoCo solver documentation"
    # (solimp impedance semantics) docked into ology "biomechanics" (a stop that yields without
    # end under sustained sub-injury load describes neither cartilage nor bone). The probe
    # torque itself obeys ALLOMETRY (THE_WOLFRAM_FRAME.md section 11): 400 N.m is ~2x an adult
    # knee-extension maximum voluntary contraction (~200 N.m, kinesiology) -- an ABUSE load by
    # design, because falls load joints beyond the voluntary band, and the body's own scaled
    # ceiling was never the question. Applied LAST, on the final model, after every reload --
    # the same load-bearing order the keyframe seating paid for. Only LIMITED slide/hinge
    # joints; free/ball joints have no stop to harden.
    _hardened = 0
    for j in range(m.njnt):
        if not m.jnt_limited[j] or m.jnt_type[j] not in (2, 3):   # slide, hinge
            continue
        m.jnt_solimp[j] = (0.95, 0.9999, 0.001, 0.5, 2.0)
        _hardened += 1
    if _hardened:
        print(f"[world] hard stops: {_hardened} limited joints -> "
              f"jnt_solimp d 0.95->0.9999 at depth (geometry, not advice)")
    return m, g


if __name__ == "__main__":
    import mujoco as _mj
    print(f"this world's gravity: {gravity():.6f} m/s^2")
    _m, _g = load_body(ROOT / "external" / "myo_sim" / "body" / "myobody.xml", _mj, verbose=True)
    print(f"tendons in the loaded model: {_m.ntendon}")
