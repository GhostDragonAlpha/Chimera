"""stand_port.py -- THE FIRST PORT. Stand. And show the bones.

WHY THIS IS THE FIRST PORT AND NOT THE FOURTH. `walk_dyad.py`'s first picture, 2026-08-02:
the pelvis starts at 1.0 m, wobbles three seconds, and CRASHES to 0.15 m; the right heel reaches
1.05 m -- the foot at pelvis height. That is not a crouch and not a gait. It is a collapse, and
NOTHING DOWNSTREAM OF A COLLAPSE IS WORTH TRAINING. Travel, tracking and speed were all being
optimised on a body that cannot hold itself up.

    THE COLLAPSE IS DATA. It says the connections are broken -- the hip is not receiving the
    pelvis's output, the knee is not receiving the hip's, the ground is not receiving the foot's.

SO THE VISUAL MUST SHOW THE BONES, AND THE BONES ARE THE ARCHITECTURE. A joint is an INTERFACE. A
segment is a DATA PATH. The skeleton is the dependency graph of the body, drawn. A picture of a
body with no connections in it is a picture, and a picture is a monad; a picture that shows what
flows through each joint is evidence about the STRUCTURE, which is the thing that is broken.

    pelvis --[ weight, 668.7 N ]--> hip --[ torque ]--> knee --[ torque ]--> ankle
           --[ CoP ]--> foot --[ ground reaction, up ]--> GROUND

EVERY NUMBER HERE IS READ, NOT CHOSEN (rule 1). `theStance` publishes the standing physics and
`theHuman` the body; this file derives the target and refuses if either is silent. The port's
target pelvis height closes on its own: hip_to_ankle_m + ankle_height_m = 0.8454 + 0.0747 =
0.9201 m, which is `leg_length_m` to twelve decimal places -- two independent routes, one number.

    python tools/stand_port.py                    # derive + draw the port (no policy needed)
    python tools/stand_port.py --policy X.pt      # and measure a policy against it
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body

MYOBODY = ROOT / "external" / "myo_sim" / "body" / "myobody.xml"
OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"


def read(name: str, keys) -> dict:
    hits = [p for p in (ROOT / "story").rglob("numbers.json") if p.parent.name == name]
    if not hits:
        raise SystemExit(f"{name} publishes nothing -- run `python Chimera/core/grow.py`. Refusing.")
    d = json.loads(hits[0].read_text(encoding="utf8"))
    missing = [k for k in keys if k not in d]
    if missing:
        raise SystemExit(f"{name} publishes no {missing}. A default here would be this port "
                         f"inventing the body it is meant to stand up (rule 20). Refusing.")
    return d


def derive_stand_port() -> dict:
    """THE PORT ITSELF: gravity + geometry in, a target pose and a base of support out.

    Nothing below is chosen. Each line names the membrane it came from, because a port whose
    inputs you cannot trace is a port that could be carrying anything.
    """
    S = read("theStance", ("hip_to_ankle_m", "ankle_height_m", "com_height_m", "foot_length_m",
                           "together_half_width_m", "together_half_length_m", "fall_rate_rad_s",
                           "time_to_fall_s", "weight_N", "g", "mass_kg", "hip_separation_m"))
    H = read("theHuman", ("leg_length_m", "thigh_frac", "shank_frac", "height_m", "ankle_drop_frac"))
    pelvis = float(S["hip_to_ankle_m"]) + float(S["ankle_height_m"])
    # THE MASS COMES FROM THE BODY, NOT FROM THE LEDGER -- found by tools/port_chain.py.
    # theHuman publishes mass_kg = 94.504 (668.7 N) because it wears a 9.9 kg suit and 1.9 kg of
    # consumables. `myobody.xml` wears neither: it is 82.041 kg (580.5 N). This port was deriving
    # a target weight 15.2% heavier than the body it is meant to stand up -- ONE QUANTITY, TWO
    # LANDMARKS (rule 19), dimensionally identical and invisible to fold, bond and regime.
    # theHuman keeps the SUITED mass, which is correct for a person on this world. The port takes
    # the mass of the thing actually in the simulator, because that is what has to be held up.
    import mujoco as _mj
    _m, _g = load_body(MYOBODY, _mj)
    sim_mass = float(sum(_m.body_mass))
    port = {
        "IN  g_m_s2": float(S["g"]),

        "IN  height_m": float(H["height_m"]),
        "OUT pelvis_target_m": pelvis,
        "OUT com_target_m": float(S["com_height_m"]),
        # WHY `together_` AND NOT `natural_` OR `braced_` -- MEASURED 2026-08-04, not preferred.
        # theStance publishes three stance widths and this line picked one with no stated
        # reason for two sessions; `f3_stand` printed the disagreement every run as an open
        # question. `tools/stance_choice.py` closed it: one set of ten 20 s rollouts scored five
        # ways (the stance is a JUDGING landmark -- it changes nothing in the plant, so survival
        # is identical across every candidate by construction and cannot discriminate between
        # them). The CONTACT POLYGON this body actually stands on -- the convex hull of the
        # points carrying load, which is what a base of support IS -- measures a half-width of
        # 0.1015 m against together_half_width_m's 0.1020 m:
        #
        #     measured 0.1015  |  together 0.1020  |  natural 0.1565  |  braced 0.3932
        #
        # A GAP OF 0.5 mm, well inside theStance's own grain (one foot breadth, 0.1020 m -- the
        # number every stance width it publishes is built from). So `together_` IS the
        # measurement rather than a description of some other posture, and every one of the five
        # landmarks returns the same in/out verdict on every seed: nothing measurable was ever
        # at stake between them. The pick was right; it is now READ instead of merely chosen.
        "OUT bos_half_lat_m": float(S["together_half_width_m"]),
        "OUT bos_half_fore_m": float(S["together_half_length_m"]),
        "OUT weight_N": sim_mass * float(S["g"]),        # the SIMULATED body's weight
        "IN  sim_mass_kg": sim_mass,
        "CHK ledger_mass_kg": float(S["mass_kg"]),
        "CHK suit_gap_pct": 100.0 * (float(S["mass_kg"]) / sim_mass - 1.0),
        "OUT fall_rate_rad_s": float(S["fall_rate_rad_s"]),
        "OUT time_to_fall_s": float(S["time_to_fall_s"]),
        "CHK leg_length_m": float(H["leg_length_m"]),
        "CHK closure_pct": 100.0 * (pelvis / float(H["leg_length_m"]) - 1.0),
        "seg thigh_m": float(H["thigh_frac"]) * float(H["height_m"]),
        "seg shank_m": float(H["shank_frac"]) * float(H["height_m"]),
        "seg foot_m": float(S["foot_length_m"]),
        "seg ankle_h_m": float(S["ankle_height_m"]),
        "seg hip_sep_m": float(S["hip_separation_m"]),
    }
    return port


# ── THE JOINTS TERM: where the passive tissue starts taking the load ──────────────────────────
# Both constants predate this file's current form and NEITHER is moved here. 0.8 is where the
# term goes cold (f3_stand.py draws it as "reward goes cold"); 0.1 is its width. This change is
# to the SHAPE ONLY, so that the shape is the single variable and the constants are the control.
JOINT_COLD = 0.8
JOINT_WIDTH = 0.1


def joints_factor(fracs):
    """How much of the body's weight is hanging on its own stops. 1.0 = none of it.

    THE DERIVATION, and it is why this replaced a max-then-gaussian on 2026-08-04.

    A joint past its declared range is resting on capsule and ligament: the body is being held
    by its PASSIVE tissue instead of by muscle. Strain energy is EXTENSIVE -- two joints on their
    stops store the sum of what each stores alone -- so the aggregate over joints is a SUM. The
    old form took `max()` over 29 graded joints, which is not an approximation of a sum; it is a
    projection that discards 28 of the 29 and reports nothing at all about them.

    That projection was invisible because of the SECOND defect, which is the shape. A gaussian in
    the overshoot is flat at BOTH ends: quadratically flat at the threshold (`1 - (e/w)^2`), and
    exponentially flat past it. With L4_L5_FE measured at 1.18 the overshoot is 3.8 widths and
    the factor is 5.4e-7 with a slope to match -- so a factor that MULTIPLIES height and support
    annihilated both, and every candidate in the population scored the same ~0. Measured by
    `tools/joints_gradient.py` before the change; the same tool is the after.

    The hinge sum keeps the two constants and fixes both properties:

        E   = SUM_j max(0, f_j - JOINT_COLD)          extensive, over every graded joint
        r_j = 1 / (1 + E / JOINT_WIDTH)               bounded (0, 1], never reaching 0

    * r_j is EXACTLY 1.0 when every joint is inside 0.8 -- identical to the retired form there,
      so nothing changes for a body that is not on its stops.
    * d r_j / d f_j = -(1/w) r_j^2 for EVERY joint past the threshold, at the same magnitude for
      each: 29 joints carry gradient where one did, and the one that did carried ~1e-5 of it.
    * It never reaches zero, so a body deep in its stops still earns credit for standing at the
      right height -- which is the whole point of a multiplicative reward and was being lost.

    NOTE THE N-DEPENDENCE, because a sum has one and a max does not: adding graded joints to
    `train_stand.PRIMARY` raises E for the same posture. That is correct for an extensive
    quantity -- more tissue loaded IS more load -- but it means the number is only comparable
    across runs that grade the same joint set. Named here rather than found later.

    Accepts a vector (every graded joint, the fix) or a scalar (one joint, for the carry and
    return trainers, which price the joints term themselves and only ever hand this one number).
    """
    e = np.maximum(0.0, np.atleast_1d(np.asarray(fracs, dtype=float)) - JOINT_COLD)
    return float(1.0 / (1.0 + float(e.sum()) / JOINT_WIDTH))


def load_joints_factor(overload):
    """The SAME shape and the SAME constants as `joints_factor`, fed a PHYSICAL quantity.

        joints_factor:      E = SUM_j max(0, f_j - JOINT_COLD)      f_j = fraction of RANGE
        load_joints_factor: S = SUM_j |limit torque_j| / capacity_j  measured in N.m, normalised
        both:               r_j = 1 / (1 + E / JOINT_WIDTH)

    ONE VARIABLE, AND IT IS THE QUANTITY. The aggregation (a sum), the shape (lorentzian) and
    both constants (0.8, 0.1) are held fixed, so an A/B between "hinge" and "load" cannot be
    confounded by any of them. That is only affordable because the two aggregates happen to land
    on the same scale -- MEASURED on the incumbent over 5 s, E = 0.7409 against S = 0.9021, a 22%
    difference -- so JOINT_WIDTH carries over unchanged rather than being re-fitted. Had they
    differed by an order of magnitude the honest arm would have needed a re-derived width, and
    then the width and the quantity would both be moving.

    NOTE THE MISSING THRESHOLD, and it is not an omission. `E` subtracts JOINT_COLD because a
    joint inside 0.8 of its range is not loading anything -- the threshold is doing the work of
    saying "no tissue is engaged yet". `S` needs no such subtraction because MuJoCo only reports
    a limit constraint when one is ACTUALLY ACTIVE: the zero point is measured, not declared.
    That is the whole argument for the physical quantity in one line -- the geometric one needs a
    threshold to guess where load begins, and the physical one is simply zero until it begins.

    WHAT THIS IS FOR (tools/joint_load.py's RULE 0, falsifier 3). The two measures were shown to
    RANK the joints alike -- both call knee_angle_l worst -- so the case for this form was
    explicitly recorded as UNPROVEN, and it is settled by a retrain rather than by argument.
    The one thing the geometric measure provably cannot see: a joint RESTING on its stop and one
    being DRIVEN into it sit at the same angle, and MEASURED they differ 32.9x here (S = 0.9021
    driven, 0.0274 under zero control).
    """
    return float(1.0 / (1.0 + max(0.0, float(overload)) / JOINT_WIDTH))


def retired_joints_factor(fracs):
    """The max-then-gaussian this replaced, kept EXECUTABLE so the A/B has a control.

    It lives here, beside its replacement, and not as a copy inside the trainer and another copy
    inside `joints_gradient.py`. Two copies of a retired formula is the same species as three
    copies of `CTRL_EVERY` (tools/timestep_audit.py): they agree until one is edited, and then
    the control arm and the instrument that judges it are measuring two different retirements.
    """
    f = np.atleast_1d(np.asarray(fracs, dtype=float))
    return float(np.exp(-((max(0.0, float(f.max()) - JOINT_COLD) / JOINT_WIDTH) ** 2)))


# ── THE PORT'S OWN PROOF BAR, as a number rather than a sentence ──────────────────────────────
# `main()` prints "PROVEN = 5 s upright, pelvis >= 90% of target". This is that 90%, read by the
# reward instead of being restated in it. Not a new constant: the same one, in one home.
PROOF_FRAC = 0.90


def support_gated(pelvis_z, com_xy, P):
    """THE MEASURED OBJECTIVE: the one predictive term, gated by the one satisfiable constraint.

    WHY THIS EXISTS (2026-08-04, `tools/objective_survival.py` + `tools/objective_matrix.py`,
    200 policies on a scale ladder, judged on held-out survival):

        component   correlation with survival (within-rung, confound held constant)
        support      +0.891      <- the only one that tracks it
        height       -0.042
        joints       -0.057
        height vs joints: -0.943  <- and they are almost perfectly OPPOSED

    `stand_reward` MULTIPLIES all three. So one informative factor is gated by two that are
    individually uninformative and mutually exclusive, and the optimiser has been asked for
    something the body cannot deliver in exchange for something the bar does not measure. Near
    the incumbent -- the only regime a warm-started search lives in -- the whole product
    correlates with survival at **-0.162**.

    THE FIX IS NOT AN INVENTION; IT IS THE PORT'S OWN SENTENCE. `stand_port.main()` already
    declares what standing is: *"5 s upright, pelvis >= 90% of target, CoM inside the base,
    joints off their limits."* That is ONE MAXIMAND (time upright) and THREE CONSTRAINTS. The
    reward inverted it -- it multiplied the constraints into a product and demoted the maximand
    to a penalty term. A constraint written as a multiplied gaussian trades off against
    everything else, which is precisely what the -0.943 is.

        r_t = support_t   if z_t >= 0.90 * target   else 0.0

    WHY HEIGHT BECOMES A GATE AND JOINTS DOES NOT. Measured: the body holds 102.9% of target, so
    the 90% bar is SATISFIABLE and a gate on it is a constraint the policy can meet. The joint
    bar is NOT -- 5 of 29 joints sit past their stop, three of them 98% of phase 1 -- so a hard
    joint gate would zero every score on every policy and leave the search with no gradient at
    all. `f3_stand` already handles that exactly this way: it reports the joints as OPEN DEBT and
    keeps them out of its exit code. This follows the precedent rather than inventing a second
    one.

    NO NEW CONSTANT ENTERS. 0.90 is the port's published proof bar; `support` is unchanged;
    `effort`'s chosen 0.01 and the joints term are dropped rather than retuned.

    THE GATE BITES DURING THE FALL, and that is the point. While the body is upright the bar is
    never near, so this equals `support_only` there; when the pelvis starts down the CoM can
    still sit over the feet, and the retired forms go on paying for "support" while the body is
    on its way to the floor.
    """
    mx = abs(com_xy[0]) / P["OUT bos_half_fore_m"]
    my = abs(com_xy[1]) / P["OUT bos_half_lat_m"]
    r_s = float(np.exp(-max(mx, my) ** 2))
    return r_s if pelvis_z >= PROOF_FRAC * P["OUT pelvis_target_m"] else 0.0


# ── THE REWARD, derived from the port and from nothing else ───────────────────────────────────
def stand_reward(pelvis_z, com_xy, joint_fracs, fell, effort, P, joints_form="hinge",
                 overload=None):
    """A single number, and every term traceable to a published one.

    height  -- the pelvis at its DERIVED target. Not "high", not "0.9 of something": 0.9201 m,
               which theStance and theHuman reach by two different routes.
    support -- the CoM inside the base of support the FEET actually make. Outside it the body is
               a falling inverted pendulum by definition, so this is not a preference.
    joints  -- neither locked straight nor collapsed. A knee at its limit is a strut, not a leg.
               `joint_fracs` is EVERY graded joint's fraction of its range, not the worst one --
               see `joints_factor` for why the max was throwing 28 of 29 joints away.
    still   -- the operator's control law: command the PROCESS and its stop condition, never a
               pose. So this rewards the OUTCOME (be still) and never a target angle.

    `joints_form` is the A/B's one variable and nothing else: "hinge" is the derived form,
    "retired" is the max-then-gaussian, executable so the control arm runs the identical code
    path with the identical constants. It is not a tuning knob and there is no third value.
    """
    z_err = abs(pelvis_z - P["OUT pelvis_target_m"]) / P["OUT pelvis_target_m"]
    r_h = float(np.exp(-(z_err / 0.05) ** 2))
    mx = abs(com_xy[0]) / P["OUT bos_half_fore_m"]
    my = abs(com_xy[1]) / P["OUT bos_half_lat_m"]
    r_s = float(np.exp(-max(mx, my) ** 2))
    if joints_form == "hinge":
        r_j = joints_factor(joint_fracs)
    elif joints_form == "retired":
        r_j = retired_joints_factor(joint_fracs)
    elif joints_form == "load":
        # THE PHYSICAL QUANTITY, same shape and constants -- see `load_joints_factor`. It is not
        # a third SHAPE (which rule 1 would forbid as a sweep); the shape is identical and the
        # QUANTITY is the variable, which is what makes hinge-vs-load a one-variable A/B.
        if overload is None:
            raise ValueError(
                "joints_form='load' needs the measured overload and this function will not "
                "derive it: it requires the model, the active constraint rows and the cached "
                "per-joint capacity. Compute it with tools/joint_load.limit_overload and pass "
                "it in. Refusing to score a physical term on a quantity nobody measured.")
        r_j = load_joints_factor(overload)
    else:
        raise ValueError(f"joints_form must be 'hinge', 'retired' or 'load', not "
                         f"{joints_form!r}. A new SHAPE would be a sweep where a derivation "
                         f"belongs (rule 1); 'load' is the same shape on a measured quantity.")
    return r_h * r_s * r_j - (3.0 if fell else 0.0) - 0.01 * effort, dict(
        height=r_h, support=r_s, joints=r_j, fell=fell)


# ── THE BONES: the architecture, drawn ────────────────────────────────────────────────────────
def draw_bones(P, ax):
    """The skeleton as a DEPENDENCY GRAPH, drawn FRONTALLY -- and the view is a finding.

    The first version drew this sagittally and put PELVIS and HIP at the same coordinate, so the
    edge "the hip receives the pelvis's output" had ZERO LENGTH: asserted, never shown. It is not
    a drawing bug. `theStance` publishes `hip_separation_m` = 0.162, so that connection is
    LATERAL, and a side view collapses it to a point.

    That is the whole reason standing is hard and the reason this port comes first: ONE centre of
    mass is carried by TWO hips 0.162 m apart, and every kilogram must be routed down one side or
    the other. A body that cannot decide which leg is carrying it is a body that falls over --
    which is exactly what the walker does at 3.12 s.
    """
    th, sh, fl = P["seg thigh_m"], P["seg shank_m"], P["seg foot_m"]
    ah, pel, hs = P["seg ankle_h_m"], P["OUT pelvis_target_m"], P["seg hip_sep_m"]
    knee_z, half = ah + sh, hs / 2.0
    W = P["OUT weight_N"]
    nodes = {"PELVIS": (0.0, pel + 0.085)}
    for s, sx in (("R", -1), ("L", +1)):
        nodes[f"HIP·{s}"] = (sx * half, pel)
        nodes[f"KNEE·{s}"] = (sx * half, knee_z)
        nodes[f"ANKLE·{s}"] = (sx * half, ah)
        nodes[f"FOOT·{s}"] = (sx * half, 0.0)
    edges = []
    for s, sx in (("R", -1), ("L", +1)):
        edges += [("PELVIS", f"HIP·{s}", f"{W/2:.0f} N", "#c0392b"),
                  (f"HIP·{s}", f"KNEE·{s}", f"thigh {th:.3f}", "#8e44ad"),
                  (f"KNEE·{s}", f"ANKLE·{s}", f"shank {sh:.3f}", "#2471a3"),
                  (f"ANKLE·{s}", f"FOOT·{s}", f"foot {fl:.3f}", "#1e8449")]
    for a, b, lbl, c in edges:
        (x0, y0), (x1, y1) = nodes[a], nodes[b]
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", lw=2.8, color=c, shrinkA=10, shrinkB=10))
        off = 0.035 if x1 >= 0 else -0.035
        ax.text((x0 + x1) / 2 + off, (y0 + y1) / 2, lbl, fontsize=7,
                color=c, va="center", ha="left" if x1 >= 0 else "right")
    for n, (x, y) in nodes.items():
        ax.scatter([x], [y], s=170, zorder=5, facecolor="white", edgecolor="#222", lw=1.6)
        ax.text(x, y + 0.045, n, fontsize=7, ha="center", weight="bold")
    # the ground, and the reaction each foot must return
    ax.axhline(0, color="#8b5a2b", lw=3.4)
    ax.text(0.30, -0.045, "GROUND", fontsize=8, color="#8b5a2b", weight="bold")
    for sx in (-1, +1):
        ax.annotate("", xy=(sx * half, 0.20), xytext=(sx * half, 0.0),
                    arrowprops=dict(arrowstyle="-|>", lw=2.4, color="#b7791f"))
    ax.text(0.0, 0.115, f"GRF  {W/2:.0f} N each\n(only while BOTH feet carry)",
            fontsize=7, color="#b7791f", ha="center")
    # gravity: one vector, on the CoM, which is what has to be routed
    ax.annotate("", xy=(0.0, P["OUT com_target_m"] - 0.26), xytext=(0.0, P["OUT com_target_m"]),
                arrowprops=dict(arrowstyle="-|>", lw=3.0, color="#c0392b"))
    ax.scatter([0], [P["OUT com_target_m"]], s=170, marker="X", color="#d35400", zorder=6)
    ax.text(0.035, P["OUT com_target_m"],
            f"CoM {P['OUT com_target_m']:.3f} m" + chr(10) +
            f"g = {P['IN  g_m_s2']:.3f} m/s2", fontsize=7.5, color="#d35400", va="center")
    ax.annotate("", xy=(half, pel - 0.055), xytext=(-half, pel - 0.055),
                arrowprops=dict(arrowstyle="<|-|>", lw=1.4, color="#555"))
    ax.text(0, pel - 0.10,
            f"hip separation {hs:.3f} m" + chr(10) + "ONE CoM, TWO hips - the routing problem",
            fontsize=7, ha="center", color="#555")
    ax.set_xlim(-0.34, 0.42); ax.set_ylim(-0.09, 1.22); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("THE BONES (frontal) — every joint an interface, every edge what flows",
                 fontsize=9.5)


def draw_base(P, ax, com_xy=None):
    """Top-down: the CONNECTION between the centre of mass and the ground that must carry it."""
    hw, hl = P["OUT bos_half_lat_m"], P["OUT bos_half_fore_m"]
    ax.add_patch(__import__("matplotlib").patches.Rectangle(
        (-hw, -hl), 2 * hw, 2 * hl, fill=True, alpha=0.18, color="#1e8449", ec="#1e8449", lw=2))
    ax.scatter([0], [0], s=120, marker="X", color="#d35400", label="CoM target (centred)")
    if com_xy is not None:
        ax.scatter([com_xy[1]], [com_xy[0]], s=90, color="#c0392b", label="CoM measured")
    ax.set_xlim(-0.22, 0.22); ax.set_ylim(-0.22, 0.22); ax.set_aspect("equal")
    ax.set_xlabel("lateral (m)"); ax.set_ylabel("fore-aft (m)")
    ax.set_title(f"BASE OF SUPPORT  ±{hw:.3f} lat × ±{hl:.3f} fore\n"
                 f"outside it the body IS a falling pendulum", fontsize=8.5)
    ax.legend(fontsize=7)


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    OUTDIR.mkdir(parents=True, exist_ok=True)
    P = derive_stand_port()

    print("\nTHE STAND PORT — derived, not chosen\n" + "=" * 78)
    for k, v in P.items():
        print(f"  {k:24} {v:.6f}" if isinstance(v, float) else f"  {k:24} {v}")
    print("=" * 78)
    print(f"  CLOSURE: hip_to_ankle + ankle_height = {P['OUT pelvis_target_m']:.6f} m vs "
          f"leg_length_m {P['CHK leg_length_m']:.6f} m  ->  {P['CHK closure_pct']:+.4f}%")
    print("  Two membranes, two routes, one number. That is the port being real rather than typed.")

    meas = None
    if "--policy" in sys.argv:
        import torch, mujoco
        from walk_dyad import build_ac, rollout, measure, ledger
        pol = Path(sys.argv[sys.argv.index("--policy") + 1])
        m, g = load_body(MYOBODY, mujoco)
        d = mujoco.MjData(m)
        mt = np.load(str(pol).replace("_policy.pt", "_meta.npy"), allow_pickle=True).item()
        ac = build_ac(int(mt["OBS"]), int(mt["ACT"]), int(mt["HID"]), torch)
        sd = torch.load(pol, map_location="cpu", weights_only=False)
        ac.load_state_dict(sd.get("model", sd) if isinstance(sd, dict) else sd)
        ac.eval()
        tr, _, fell, stand_z = rollout(m, d, ac, torch, mujoco, 5.0, 0, int(mt["OBS"]))
        mm = measure(tr, fell, stand_z, ledger())
        meas = dict(tr=tr, mm=mm, fell=fell)
        print(f"\n  MEASURED ({pol.name}): pelvis min {mm['stand_frac_min']*stand_z:.3f} m "
              f"vs target {P['OUT pelvis_target_m']:.3f} m -> "
              f"{100*mm['stand_frac_min']*stand_z/P['OUT pelvis_target_m']:.1f}% of target")
        print(f"  PROVEN = 5 s upright, pelvis >= 90% of target.  VERDICT: "
              f"{'PASS' if (not fell and mm['stand_frac_min']*stand_z >= 0.9*P['OUT pelvis_target_m']) else 'FAIL'}")

    fig = plt.figure(figsize=(15.5, 6.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1, 1.25], wspace=0.30)
    draw_bones(P, fig.add_subplot(gs[0, 0]))
    draw_base(P, fig.add_subplot(gs[0, 1]))
    ax = fig.add_subplot(gs[0, 2])
    if meas:
        t, z = meas["tr"]["t"], meas["tr"]["z"]
        ax.plot(t, z, color="#c0392b", lw=1.9, label="pelvis, measured")
        ax.axhline(P["OUT pelvis_target_m"], color="#1a7f37", lw=2.4, label="derived target")
        ax.axhline(0.9 * P["OUT pelvis_target_m"], color="#1a7f37", ls="--", lw=1.4,
                   label="90% — the proof bar")
        ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7.5)
        ax.set_title("THE CONNECTION, MEASURED\npelvis height vs what physics says it should be",
                     fontsize=9)
    else:
        ax.axis("off")
        ax.text(0, 1, "\n".join(
            ["THE PORT'S CONTRACT", "", "IN   gravity, mass, geometry",
             "OUT  pelvis target, CoM target, base of support", "",
             f"pelvis  {P['OUT pelvis_target_m']:.4f} m",
             f"CoM     {P['OUT com_target_m']:.4f} m",
             f"BoS     ±{P['OUT bos_half_lat_m']:.3f} × ±{P['OUT bos_half_fore_m']:.3f} m",
             f"weight  {P['OUT weight_N']:.1f} N",
             f"fall    {P['OUT fall_rate_rad_s']:.3f} rad/s "
             f"({P['OUT time_to_fall_s']:.3f} s to fall)", "",
             "PROVEN = 5 s upright, pelvis ≥ 90% of target,",
             "CoM inside the base, joints off their limits.", "",
             "next port: BALANCE (this port's output is its input)"]),
            family="monospace", fontsize=9, va="top")
    fig.suptitle("PORT 1 — STAND.  Every number read from theStance / theHuman; none chosen here.",
                 fontsize=11)
    png = OUTDIR / ("stand_port_measured.png" if meas else "stand_port.png")
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"\nPICTURE: {png}\nTHE PORT IS NOT DEFINED UNTIL YOU HAVE OPENED IT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
