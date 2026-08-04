"""f3_stand.py -- F3 OF THE SLICE: the body stands THROUGH THE PARSER, or the slice's third
falsifier fires.

`docs/THE_SLICE.md`, rung 3: *the musculoskeletal body standing on the world's gravity through
the parser, zero pose-scripted frames*. This file is that rung's harness.

RULE 0, stated before the build, because this membrane is a theory:

    STATEMENT   The stand formula (`a0 + kh*(tgt-z) + kp*pitch`, clipped to [0,1]) is enough to
                hold this body upright for five full seconds under THIS world's gravity
                (g = 7.076, read by `world.load_body` from theHuman, never assumed), with the
                parser -- not the harness -- deciding every control step.
    PREDICTION  Phase 1 (STAND held on): pelvis MINIMUM over 5.0 s >= 90% of the derived target
                0.9201 m, the CoM stays inside the base of support the feet make, and no joint
                reaches its stop. Phase 2 (STAND released): the body SLUMPS -- pelvis drops below
                50% of target.
    FALSIFIER   Phase 1: pelvis min < 90% of target over the full 5 s, or a joint at its limit,
                or the CoM outside the BoS. Phase 2: the body stays upright with STAND off --
                which would mean the parser is decorative and the checkpoint was being replayed.

TEN SEEDS, NOT ONE (2026-08-04). THIS HARNESS USED TO REPORT ONE ROLLOUT. `tools/stand_survival.py`
then measured what that rollout is worth: a nudge of 1e-6 -- 73,000x below the finest angle this
world publishes -- moves survival from 6.30 s to 9.08 s across ten seeds (median 7.01, SPREAD
2.78 s), and the UNPERTURBED start is the LUCKIEST OF THE TEN. So every single-rollout number
this file ever printed was the top of a distribution reported as its centre, overstating by ~30%.

    THE HEADLINE IS NOW THE MEDIAN OF TEN, WITH THE MIN AND THE SPREAD BESIDE IT.

That is not a softer bar, it is a different QUESTION. "Did seed 0 pass" and "does this policy
pass" are two quantities, and this harness was answering the first while its exit code claimed
the second (rule 19: one quantity, one landmark). The per-seed verdicts are all printed, so a
policy that passes on the median and fails on the worst is visible as exactly that rather than
hidden behind either number alone.

ZERO POSE-SCRIPTED FRAMES, PROVEN BY CONSTRUCTION. After `seat_in_limits` -- a one-time
projection of the keyframe into the body's OWN declared joint ranges, at reset only -- nothing in
this file ever writes `d.qpos`. Every subsequent state is `mj_step` under muscle control and
gravity. The harness is the proof; there is no flag to trust.

THE PARSER HERE IS THE REAL ONE (2026-08-04): `tools/parser.py`, the Phase D grammar of
docs/THE_PARSER.md -- button state -> formula layer -> muscles, with the stand port as a
registered formula and every other verb a named refusal. v1 was `BUTTONS = {"stand": ...}`,
one hard-wired lambda; the membrane's falsifier 1 proved the grammar carries the identical
signal (bit-identical over a 135-sample sweep), and Phase 2 exists precisely to test that
the button is load-bearing -- through the grammar now, not around it.

    python tools/f3_stand.py                      # 10 seeds; exit 0 PASS, 1 FAIL
    python tools/f3_stand.py --seeds 1            # the retired single-rollout behaviour, exactly
    python tools/f3_stand.py --theta <path>       # judge a named arm
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body
from stand_port import derive_stand_port, MYOBODY
from train_stand import joint_ids, seat_in_limits, joint_frac_named, CTRL_EVERY, NUDGE
from parser import Parser, default_registry

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
THETA = OUTDIR / "stand_theta.npy"
# CTRL_EVERY IS IMPORTED, NOT REDECLARED (2026-08-04, tools/timestep_audit.py). It was `= 20`
# here, `= 20` in train_walk.py and a bare `k % 20` literal in train_stand.py -- three copies of
# one number across the trainer, the judge and the walk, which must agree or the thing being
# trained is not the thing being judged. They did all agree; that is how this species survives
# long enough to matter. The trainer owns it now, and the judge reads the trainer's.
# NUDGE is imported for the same reason: the trainer's randomized starts, `stand_survival.py`'s
# and this judge's must be the SAME perturbation or the disagreement between them is the
# instrument's, not the policy's.
PHASE1_SECS = 5.0               # the slice's bar: five full seconds upright
PHASE2_MAX = 3.0                # release; the body must slump well inside this
SEEDS = 10                      # the headline is the median of these


def run_one(m, d, mujoco, theta, P, jids, seed, frames=0):
    """ONE SEED. Seed 0 is the UNPERTURBED control; every other nudges qpos by NUDGE.

    Returns every quantity the verdicts read, so the aggregation over seeds happens in ONE place
    and no bar is computed twice from two rollouts.
    """
    tgt = P["OUT pelvis_target_m"]
    hw, hl = P["OUT bos_half_lat_m"], P["OUT bos_half_fore_m"]
    nu = m.nu

    # THE PARSER (tools/parser.py, docs/THE_PARSER.md): the stand port is a REGISTERED
    # FORMULA; the phase toggles the button's STATE; the parse produces the control.
    # Nothing below reads or writes qpos except the one-time seat at reset.
    PARSER = Parser(default_registry(theta, tgt, nu))

    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)      # one-time, at reset: the keyframe's own violation
    if seed:
        # Applied AFTER the seat, so a seed cannot push the body back outside the limits the
        # line above just enforced. Same order as train_stand.evaluate and stand_survival.
        d.qpos[:] = d.qpos + np.random.default_rng(seed).normal(0.0, NUDGE, size=d.qpos.shape)
        mujoco.mj_forward(m, d)

    tr = {k: [] for k in ("t", "z", "comx", "comy", "jf", "jn", "all", "polx", "poly", "phase")}
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    pics = []
    steps = int((PHASE1_SECS + PHASE2_MAX) / m.opt.timestep)
    phase2_start = int(PHASE1_SECS / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    slumped_at = None
    fell_t = None

    for k in range(steps):
        stand_on = k < phase2_start
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            # ROLL, the frontal-plane lean. Supplied because the stand formula now feeds it
            # back: the body's fall was MEASURED to be lateral (CoM-y to -812 mm while CoM-x
            # stayed under 52 mm), and a 3-D inverted pendulum has two lean angles.
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            PARSER.set_verb("STAND", stand_on)
            u, _trace = PARSER.command({"z": z, "pitch": pitch, "roll": roll})
            d.ctrl[:] = u if u is not None else 0.0
        mujoco.mj_step(m, d)
        if k in grab and ren is not None:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            com = d.subtree_com[0]
            _b = lambda n: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)]
            foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
            tr["t"].append(k * m.opt.timestep)
            tr["z"].append(z)
            tr["comx"].append(float(com[0] - foot[0]))
            tr["comy"].append(float(com[1] - foot[1]))
            # THE BASE OF SUPPORT THE FEET ACTUALLY MAKE -- reported ALONGSIDE the published
            # box, never instead of it. F3's falsifier is written "the CoM stays inside the
            # base of support THE FEET MAKE", and this is that sentence measured: the convex
            # extent of the four contact bodies, this pose, this instant. The published box is
            # `theStance.together_*`, which describes a DIFFERENT stance (feet together) --
            # measured 1.90x narrower laterally than the polygon this body actually stands on.
            # Two landmarks for one quantity (rule 19), so both are printed and NEITHER bar is
            # moved; which one F3 should read is a question for theStance, not for this harness.
            _px = [float(_b(n)[0]) for n in ("calcn_r", "calcn_l", "toes_r", "toes_l")]
            _py = [float(_b(n)[1]) for n in ("calcn_r", "calcn_l", "toes_r", "toes_l")]
            tr["polx"].append(max(1e-9, 0.5 * (max(_px) - min(_px))))
            tr["poly"].append(max(1e-9, 0.5 * (max(_py) - min(_py))))
            _jf, _jn = joint_frac_named(d, jids)
            tr["jf"].append(_jf)
            tr["jn"].append(_jn)
            # EVERY joint, every sample -- not just the worst one. The first version of this
            # diagnostic recorded only the argmax, and then asked "how bad was the lumbar" by
            # filtering the samples where a lumbar joint HAPPENED to be worst overall. That
            # answers a different question and always understates: a lumbar sitting at 1.08
            # under an mtp at 1.10 is invisible to it. The trunk membrane's falsifier 1 turns
            # on the word SUSTAINED, so it needs the joint's own time series, not a projection
            # of it through another joint's maximum.
            tr["all"].append({n: abs(float(d.qpos[adr]) - c) / h for adr, c, h, n in jids})
            tr["phase"].append(1 if stand_on else 0)
            if stand_on and z < 0.5 * tgt and fell_t is None:
                fell_t = k * m.opt.timestep
            if not stand_on and z < 0.5 * tgt:
                slumped_at = k * m.opt.timestep - PHASE1_SECS
                break
    if ren is not None:
        ren.close()

    # ---- THIS SEED'S NUMBERS -----------------------------------------------
    p1 = [i for i, ph in enumerate(tr["phase"]) if ph == 1]
    z1 = [tr["z"][i] for i in p1]
    held = min(z1) if z1 else 0.0
    held_frac = 100.0 * held / tgt
    p1_secs = len(p1) * CTRL_EVERY * m.opt.timestep
    # THE SAME CoM, AGAINST THE POLYGON THE FEET ACTUALLY MAKE. Reported, never substituted:
    # `ok_com` below still reads the published box, because relaxing a falsifier to pass it is
    # the one forbidden move. This exists so the DISAGREEMENT is visible (rule 17) instead of
    # one landmark quietly standing in for the other.
    pol_series = [max(abs(tr["comx"][i]) / tr["polx"][i], abs(tr["comy"][i]) / tr["poly"][i])
                  for i in p1]
    pol_out = max(pol_series) if pol_series else 99.0
    pol_over = 100.0 * sum(1 for v in pol_series if v > 1.0) / max(len(pol_series), 1)
    pol_w = float(np.mean([tr["poly"][i] for i in p1])) if p1 else 0.0
    com_series = [max(abs(tr["comx"][i]) / hl, abs(tr["comy"][i]) / hw) for i in p1]
    com_out = max(com_series) if com_series else 99.0
    # PEAK AND SUSTAINED, for the same reason the joints get both. The keyframe is a POSE, not
    # an equilibrium: the body settles into standing over the first few tenths of a second and
    # the CoM swings while it does. A max over the whole phase cannot tell that transient from
    # a body that stands leaning outside its own feet. THE BAR IS NOT MOVED -- `ok_com` still
    # reads the peak, because relaxing a falsifier to pass it is the one forbidden move. This
    # only makes the number say which of the two it is.
    com_over = 100.0 * sum(1 for v in com_series if v > 1.0) / max(len(com_series), 1)
    com_settled = max(com_series[int(0.2 * len(com_series)):], default=0.0)
    _ci = max(range(len(com_series)), key=lambda i: com_series[i]) if com_series else 0
    com_t = tr["t"][p1[_ci]] if com_series else 0.0
    com_win = [tr["t"][p1[i]] for i, v in enumerate(com_series) if v > 1.0]
    jmax, jworst = max(((tr["jf"][i], tr["jn"][i]) for i in p1),
                       key=lambda p: p[0]) if p1 else (9.0, "?")
    # WHICH JOINTS, AND HOW LONG -- not one instant on one joint. A ligament that catches the
    # arch late still shows a peak; what says it CAUGHT it is the joint coming back inside. So
    # every joint gets BOTH numbers: its own peak, and the fraction of phase 1 it spent at or
    # past its stop. The second is the one the trunk membrane's falsifier 1 is written in.
    names = sorted(tr["all"][0]) if tr["all"] else []
    peak = {n: max((tr["all"][i][n] for i in p1), default=0.0) for n in names}
    over = {n: 100.0 * sum(1 for i in p1 if tr["all"][i][n] >= 1.0) / max(len(p1), 1)
            for n in names}
    over_frac = 100.0 * sum(1 for i in p1 if tr["jf"][i] >= 1.0) / max(len(p1), 1)
    # UPRIGHT-TIME: how long phase 1 lasted before the body went under the fall bar. It is the
    # quantity `stand_survival.py` reports, measured here so the two instruments can be compared
    # without either re-deriving the other's number.
    upright_s = fell_t if fell_t is not None else p1_secs
    return dict(seed=seed, tr=tr, pics=pics, names=names, peak=peak, over=over,
                held=held, held_frac=held_frac, p1_secs=p1_secs, upright_s=upright_s,
                com_out=com_out, com_over=com_over, com_settled=com_settled, com_t=com_t,
                com_win=com_win, pol_out=pol_out, pol_over=pol_over, pol_w=pol_w,
                jmax=jmax, jworst=jworst, over_frac=over_frac,
                fell_t=fell_t, slumped_at=slumped_at, p1=p1,
                ok1=(held_frac >= 90.0 and p1_secs >= PHASE1_SECS - 0.01 and fell_t is None),
                ok_com=(com_out <= 1.0), ok_joints=(jmax < 1.0),
                ok2=(slumped_at is not None))


def run() -> int:
    import mujoco
    a = sys.argv
    nseeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else SEEDS
    tpath = Path(a[a.index("--theta") + 1]) if "--theta" in a else THETA
    if not tpath.is_absolute():
        tpath = OUTDIR / tpath.name
    if not tpath.exists():
        raise SystemExit(f"no {tpath} -- run `python tools/train_stand.py` first. Refusing to "
                         f"stand on nothing (rule 20).")
    theta = np.load(tpath)
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    tgt = P["OUT pelvis_target_m"]
    hw, hl = P["OUT bos_half_lat_m"], P["OUT bos_half_fore_m"]

    runs = [run_one(m, d, mujoco, theta, P, jids, s) for s in range(nseeds)]
    # THE MEDIAN SEED IS THE ONE DRAWN AND DIAGNOSED, and it is a REAL seed, never an average of
    # ten. An averaged trace is a body nothing ever simulated; the picture has to be a rollout
    # that happened. For an even count numpy's median interpolates, so the representative is the
    # seed whose upright time is closest to it -- named, so the reader knows which one they see.
    up = np.array([r["upright_s"] for r in runs])
    med_up = float(np.median(up))
    rep = runs[int(np.argmin(np.abs(up - med_up)))]
    worst = runs[int(np.argmin(up))]
    # the representative is re-run WITH frames, the same pattern train_stand.score_theta uses:
    # the common path never pays for a renderer, and the picture is the rollout that was graded
    rep = run_one(m, d, mujoco, theta, P, jids, rep["seed"], frames=8)

    held_fracs = np.array([r["held_frac"] for r in runs])
    n_ok1 = sum(1 for r in runs if r["ok1"])
    n_okc = sum(1 for r in runs if r["ok_com"])
    n_okj = sum(1 for r in runs if r["ok_joints"])
    n_ok2 = sum(1 for r in runs if r["ok2"])
    spread = float(up.max() - up.min())
    tick = CTRL_EVERY * m.opt.timestep

    # THE VERDICT IS THE MEDIAN SEED'S, and the min is printed beside it every time. A policy
    # that passes on the median and fails on the worst is a COIN TOSS, and this prints that
    # sentence rather than letting either number stand alone as "the" answer.
    ok1, ok_com, ok_joints, ok2 = rep["ok1"], rep["ok_com"], rep["ok_joints"], rep["ok2"]
    # TWO VERDICTS, because two documents state two bars and conflating them is how a debt
    # goes silent. F3's letter (docs/THE_SLICE.md:48): stand up, on this world's gravity,
    # through the parser, zero pose-scripted frames -- "stand up" carries theStance's own
    # definition (the CoM over the base of support; outside it the body IS a falling
    # pendulum). THE PORT'S FULL CONTRACT (stand_port.py's printed PROVEN line) adds: joints
    # off their limits.
    #
    # 2026-08-04, AFTER THE TRUNK MEMBRANE: the lumbar is no longer what breaks that term.
    # It went from SUSTAINED 1.14-1.34 (peak 1.56) to a 1.12 TRANSIENT over 6.4% of phase 1.
    # What breaks it now is subtalar / mtp / hip_rotation / the knee's extension side -- and
    # those are not an oversight, they are the joints for which THIS WORLD PUBLISHES NO
    # ENVELOPE. theHuman's `gait_envelope_deg` carries hip, knee and ankle: three sagittal
    # curves. The trunk closed by going to the literature for its edge (Pearcy & Tibrewal's
    # 5 deg); the foot and the hip's off-sagittal axes need the same, and that is a DIFFERENT
    # membrane with its own Rule 0 -- named here rather than quietly folded into this one.
    ok_f3 = ok1 and ok_com and ok2
    ok = ok_f3 and ok_joints

    # THE LUMBAR IS EVERY JOINT THE TRUNK MEMBRANE PUT A LIGAMENT ON, named from world.py
    # rather than matched on a letter -- `n.startswith("L")` would also catch nothing at all
    # if the model renamed a level, and would silently report 0.00 = "the theory survived".
    from world import LUMBAR_FE_JOINTS, LUMBAR_LB_JOINTS
    names = rep["names"]
    lum = [n for n in names if n in LUMBAR_FE_JOINTS or n in LUMBAR_LB_JOINTS]
    if not lum:
        raise SystemExit("no lumbar joint is being graded -- refusing to report that the trunk "
                         "membrane's falsifier did not fire when nothing measured it (rule 20).")
    # THE LUMBAR VERDICT IS OVER ALL SEEDS, not the representative's. "Sustained" is a claim
    # about the policy, and one rollout cannot carry it.
    lumbar_max = max(max(r["peak"][n] for n in lum) for r in runs)
    lumbar_over = float(np.median([max(r["over"][n] for n in lum) for r in runs]))
    # WHY does each over-the-stop joint have no ligament holding it? ASK THE DERIVATION, do not
    # infer it here. A first version of this line said "this world publishes no envelope for
    # knee_angle_l" -- which is false: theHuman publishes a knee envelope and world.py emits a
    # knee FLEXION ligament; what it refused was the EXTENSION side, because the gap there
    # (1.84 deg) is under the envelope's own grain (4.16 deg). Two different absences with two
    # different fixes, and a harness that guesses at the reason will send the next rung at the
    # wrong one. `derive_ligaments` already returns its refusals with their reasons.
    from world import derive_ligaments
    _emit, _refused = derive_ligaments(m, mujoco)
    have_lig = {e["joint"] for e in _emit}
    why_not = {}
    for _jn, _sd, _wy in _refused:
        why_not.setdefault(_jn, []).append(f"{_sd}: {_wy}")
    # PER-JOINT PEAK AND OVER-STOP, MEDIAN OVER SEEDS. The single-seed version of this table was
    # the same overstatement in miniature: one rollout's mtp number read as the policy's.
    peak_med = {n: float(np.median([r["peak"][n] for r in runs])) for n in names}
    over_med = {n: float(np.median([r["over"][n] for r in runs])) for n in names}
    offenders = [n for n in names if peak_med[n] >= 1.0]

    print("\nF3 -- STAND THROUGH THE PARSER, ZERO POSE-SCRIPTED FRAMES")
    print("=" * 78)
    print(f"  theta: {tpath.name} ({theta.size} numbers)")
    print(f"  world: g = {g:.4f} m/s2 (theHuman, via load_body -- never assumed)")
    print(f"  target pelvis {tgt:.4f} m (hip_to_ankle + ankle_height, theStance/theHuman)")
    print(f"  JUDGED OVER {nseeds} SEEDS -- nudge {NUDGE:g} on qpos, seed 0 UNPERTURBED. The "
          f"headline is the MEDIAN;")
    print(f"  the min and the spread are printed beside it because one rollout is a coin toss.")
    print("-" * 78)
    print(f"{'seed':>5}{'upright':>10}{'pelvis MIN':>13}{'%tgt':>8}{'CoM pk':>9}{'jmax':>7}"
          f"{'worst joint':>18}  ph1 ph2")
    for r in runs:
        mark = " <- median" if r["seed"] == rep["seed"] else ""
        print(f"{r['seed']:>5}{r['upright_s']:>9.2f}s{r['held']:>12.4f}m{r['held_frac']:>7.1f}%"
              f"{r['com_out']:>9.2f}{r['jmax']:>7.2f}{r['jworst']:>18}"
              f"{'  PASS' if r['ok1'] else '  FAIL'}"
              f"{' PASS' if r['ok2'] else ' FAIL'}{mark}")
    print("-" * 78)
    print(f"  UPRIGHT (phase 1)  median {med_up:.2f} s   min {up.min():.2f} s   "
          f"max {up.max():.2f} s   SPREAD {spread:.3f} s ({spread/tick:.0f} control ticks)")
    print(f"  PELVIS MIN         median {float(np.median(held_fracs)):.1f}%   "
          f"min {held_fracs.min():.1f}%   max {held_fracs.max():.1f}% of target")
    print(f"  SEEDS PASSING      phase1 {n_ok1}/{nseeds}   CoM {n_okc}/{nseeds}   "
          f"joints {n_okj}/{nseeds}   phase2 {n_ok2}/{nseeds}")
    # ---- SEED 0 vs THE MEDIAN, per headline quantity, WITH CENSORING NAMED ------------------
    # F3'S UPRIGHT TIME IS CENSORED AT `PHASE1_SECS`. A body that is still standing when the
    # window closes reports 5.00 s because the window ended, not because anything happened to
    # it -- so when every seed is censored the spread of that column is a fact about the
    # harness and none about the body, and comparing seed 0 to the median on it measures
    # nothing. `stand_survival.py` runs 20 s precisely to see past this, and measures a 2.78 s
    # spread on the same policy. MEASURE AT THE SCALE THE THING LIVES AT (rule 13): the
    # divergence is real and its timescale is LONGER THAN THIS WINDOW.
    n_censored = sum(1 for r in runs if r["fell_t"] is None
                     and r["p1_secs"] >= PHASE1_SECS - 1e-9)
    if nseeds > 1:
        quantities = [
            ("upright s", [r["upright_s"] for r in runs], n_censored == nseeds),
            ("pelvis min %", [r["held_frac"] for r in runs], False),
            ("CoM peak", [r["com_out"] for r in runs], False),
        ]
        print(f"  SEED 0 vs MEDIAN, per headline quantity"
              + (f"   ({n_censored}/{nseeds} seeds CENSORED at the {PHASE1_SECS:.1f} s window)"
                 if n_censored else ""))
        devs = []
        for label, vals, censored in quantities:
            s0, md = float(vals[0]), float(np.median(vals))
            dev = 100.0 * (md - s0) / max(abs(s0), 1e-9)
            tag = "  -- CENSORED, this column measures the window, not the body" if censored \
                else ""
            print(f"    {label:14} seed 0 {s0:8.3f}   median {md:8.3f}   "
                  f"single-rollout is {(-dev):+6.1f}%{tag}")
            if not censored:
                devs.append(abs(dev))
        worst_dev = max(devs) if devs else 0.0
        fires = worst_dev <= 5.0
        print(f"    task-3 falsifier (median within 5% of seed 0 on every UNCENSORED headline): "
              + (f"FIRES -- worst deviation {worst_dev:.1f}%." if fires else
                 f"does not fire -- worst deviation {worst_dev:.1f}%."))
        if fires:
            print(f"      AT THIS WINDOW, AND ONLY AT THIS WINDOW. The same policy over 20 s "
                  f"(tools/stand_survival.py)")
            print(f"      spans 6.30-9.08 s of survival. The divergence is real; it needs "
                  f"longer than {PHASE1_SECS:.0f} s to reach")
            print(f"      the fall bar, so F3's bars are NOT the ones the coin toss was "
                  f"inflating. Recorded, not averaged away.")
    print("-" * 78)
    print(f"  THE MEDIAN SEED ({rep['seed']}) IN FULL -- this is the rollout drawn below:")
    print(f"  PHASE 1 (stand ON, {PHASE1_SECS:.1f} s): pelvis MIN {rep['held']:.4f} m = "
          f"{rep['held_frac']:.1f}% of target  ->  {'PASS' if ok1 else 'FAIL'}")
    print(f"           CoM excursion PEAK {rep['com_out']:.2f} of BoS box (must be <= 1.00)  ->  "
          f"{'PASS' if ok_com else 'FAIL'}")
    print(f"           SAME CoM vs the polygon THE FEET MAKE (F3's own words): peak "
          f"{rep['pol_out']:.2f}, outside {rep['pol_over']:.1f}% of phase 1")
    print(f"             the two landmarks disagree: theStance publishes together_half_width "
          f"{hw:.4f} m,")
    print(f"             the feet make {rep['pol_w']:.4f} m ({rep['pol_w']/max(hw,1e-9):.2f}x). "
          f"theStance also publishes")
    print(f"             natural_ and braced_ widths -- stand_port picks together_ with no stated "
          f"reason.")
    print(f"             THE BAR BELOW IS UNMOVED; which one F3 should read is theStance's call.")
    print(f"           CoM outside the box {rep['com_over']:.1f}% of phase 1, peak at "
          f"t={rep['com_t']:.2f}s"
          + (f", outside during t={min(rep['com_win']):.2f}..{max(rep['com_win']):.2f}s"
             if rep["com_win"] else "")
          + (" -- a settle off the keyframe, not the stand"
             if rep["com_settled"] <= 1.0 < rep["com_out"] else ""))
    print(f"           worst joint {rep['jmax']:.2f} of range at {rep['jworst']} (must be < 1.00)"
          f"  ->  {'PASS' if ok_joints else 'FAIL'}")
    print(f"           SOME joint is over its stop for {rep['over_frac']:.0f}% of phase 1. "
          f"Per joint, MEDIAN over {nseeds} seeds of peak and % of phase 1 past the stop:")
    for _n, _v in sorted(peak_med.items(), key=lambda p: -p[1])[:6]:
        if _v < 0.90:
            break
        tag = "  <- LUMBAR, the trunk membrane's ligament" if _n in lum else ""
        print(f"             {_n:22} peak {_v:.2f}   over {over_med[_n]:5.1f}% of phase 1{tag}")
    print(f"           TRUNK MEMBRANE, falsifier 1: worst lumbar peak {lumbar_max:.2f} (any "
          f"seed), sustained over its stop {lumbar_over:.1f}% of phase 1 (median seed)")
    print(f"             -> {'FIRES -- the derived structure is insufficient' if lumbar_over >= 50.0 else ('holds -- the lumbar stays inside its stop' if lumbar_max < 1.0 else 'transient only, not sustained')}")
    if rep["fell_t"] is not None:
        print(f"           body fell during phase 1 at t={rep['fell_t']:.2f} s")
    print(f"  PHASE 2 (stand OFF): "
          + (f"slumped to <50% of target in {rep['slumped_at']:.2f} s  ->  PASS"
             if ok2 else
             f"still upright after {PHASE2_MAX:.1f} s -- the parser is decorative  ->  FAIL"))
    print(f"  qpos writes after reset: 0 (by construction -- the harness contains no write)")
    print("=" * 78)
    print(f"  F3 VERDICT (the slice's letter, on the MEDIAN of {nseeds}): "
          f"{'PASS' if ok_f3 else 'FAIL'}")
    if nseeds > 1 and ok_f3 and not worst["ok1"]:
        print(f"    AND IT IS A COIN TOSS: the median passes, seed {worst['seed']} does not "
              f"({worst['upright_s']:.2f} s upright). Both are printed; neither is 'the' answer.")
    print(f"  PORT CONTRACT (stand_port's full PROVEN line, incl. joints off limits): "
          + ("PASS" if ok else f"FAIL -- OPEN DEBT at {len(offenders)} joint(s), worst "
                               f"{rep['jworst']} {rep['jmax']:.2f}"))
    if not ok_joints:
        print(f"\n  WHY EACH OVER-THE-STOP JOINT IS NOT HELD -- from derive_ligaments' own refusals,"
              f"\n  not inferred here. This is the next membrane's work list:")
        for n in sorted(offenders, key=lambda n: -peak_med[n]):
            if n in lum:
                print(f"    {n:22} HAS a derived ligament (trunk membrane); peak {peak_med[n]:.2f} "
                      f"is {over_med[n]:.1f}% transient")
            elif n in have_lig and n in why_not:
                print(f"    {n:22} ligament on one side only -- {'; '.join(why_not[n])}")
            elif n in have_lig:
                print(f"    {n:22} HAS a derived ligament and still goes over")
            elif n in why_not:
                print(f"    {n:22} REFUSED -- {'; '.join(why_not[n])}")
            else:
                print(f"    {n:22} never reached the derivation: theHuman's gait_envelope_deg "
                      f"publishes no curve for this joint")
        print("  theHuman publishes three sagittal curves (hip, knee, ankle). The trunk closed its")
        print("  own joints by taking the edge from the LITERATURE instead (Pearcy & Tibrewal).")
        print("  The foot and the hip's off-sagittal axes want that same move -- and that is a")
        print("  SEPARATE membrane, which needs its own RULE 0 stated before anyone builds it.")

    # ---- THE LEDGER: the headline triple, machine-readable ------------------
    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / f"f3_stand_{tpath.stem}.json"
    out.write_text(json.dumps(dict(
        theta=tpath.name, seeds=nseeds, nudge=NUDGE, g=g, pelvis_target_m=tgt,
        upright_median_s=med_up, upright_min_s=float(up.min()), upright_max_s=float(up.max()),
        upright_spread_s=spread, upright_per_seed=[float(v) for v in up],
        upright_censored_seeds=n_censored, phase1_window_s=PHASE1_SECS,
        com_peak_per_seed=[float(r["com_out"]) for r in runs],
        pelvis_min_pct_median=float(np.median(held_fracs)),
        pelvis_min_pct_min=float(held_fracs.min()),
        seeds_pass_phase1=n_ok1, seeds_pass_com=n_okc, seeds_pass_joints=n_okj,
        seeds_pass_phase2=n_ok2, median_seed=int(rep["seed"]),
        verdict_f3=bool(ok_f3), verdict_port_contract=bool(ok),
        peak_frac_median=peak_med, pct_past_stop_median=over_med,
        lumbar_peak_max=lumbar_max, lumbar_over_median=lumbar_over), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    # ---- THE PICTURE: a turn you have not looked at did not end ------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(15.0, 7.2))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.05, 1], hspace=0.38, wspace=0.28)
    if rep["pics"]:
        ax = fig.add_subplot(gs[0, :]); ax.imshow(np.concatenate(rep["pics"], axis=1))
        ax.axis("off")
        ax.set_title(f"eight frames, MEDIAN seed {rep['seed']}: standing on the parser, "
                     f"then the button released", fontsize=10)
    ax = fig.add_subplot(gs[1, 0])
    # EVERY SEED IS DRAWN, the median in full colour. A single trace is what this plot used to
    # show, and the spread it hid is the whole finding.
    for r in runs:
        ax.plot(r["tr"]["t"], r["tr"]["z"], color="#c0392b", lw=0.8, alpha=0.32)
    ax.plot(rep["tr"]["t"], rep["tr"]["z"], color="#c0392b", lw=2.0,
            label=f"median seed {rep['seed']}")
    ax.axhline(tgt, color="#1a7f37", lw=2.2, label=f"derived target {tgt:.4f} m")
    ax.axhline(0.9 * tgt, color="#1a7f37", ls="--", lw=1.3, label="90% -- the proof bar")
    ax.axhline(0.5 * tgt, color="#8e44ad", ls=":", lw=1.3, label="50% -- the slump bar")
    ax.axvline(PHASE1_SECS, color="#555", ls="-", lw=1.0)
    ax.text(PHASE1_SECS + 0.05, 0.15, "STAND released", fontsize=7.5, color="#555")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7)
    ax.set_title(f"pelvis, all {nseeds} seeds -- median min {np.median(held_fracs):.0f}% "
                 f"(worst {held_fracs.min():.0f}%)", fontsize=9)
    ax = fig.add_subplot(gs[1, 1])
    ax.add_patch(matplotlib.patches.Rectangle((-hw, -hl), 2 * hw, 2 * hl, alpha=0.18,
                                              color="#1e8449", ec="#1e8449", lw=2))
    for r in runs:
        ax.plot(r["tr"]["comy"], r["tr"]["comx"], color="#c0392b", lw=0.7, alpha=0.32)
    ax.plot(rep["tr"]["comy"], rep["tr"]["comx"], color="#c0392b", lw=1.6)
    ax.scatter([0], [0], marker="X", s=110, color="#d35400")
    ax.set_xlim(-0.3, 0.3); ax.set_ylim(-0.3, 0.3); ax.set_aspect("equal")
    ax.set_title(f"CoM over the base -- median peak {rep['com_out']:.2f} of box", fontsize=9)
    ax = fig.add_subplot(gs[1, 2])
    ax.bar(range(nseeds), up, color="#2471a3")
    ax.axhline(med_up, color="#1a7f37", lw=2.0, label=f"median {med_up:.2f} s")
    ax.axhline(PHASE1_SECS, color="#c0392b", ls="--", lw=1.4, label=f"bar {PHASE1_SECS:.1f} s")
    ax.set_xlabel("seed"); ax.set_ylabel("upright s"); ax.legend(fontsize=7)
    ax.set_title(f"UPRIGHT per seed -- spread {spread:.2f} s = {spread/tick:.0f} ticks",
                 fontsize=9)
    fig.suptitle(f"F3 -- STAND THROUGH THE PARSER   {tpath.name}   g={g:.3f} m/s2   "
                 f"median of {nseeds}: F3 {'PASS' if ok_f3 else 'FAIL'} / port contract "
                 f"{'PASS' if ok else 'joints: OPEN DEBT'}", fontsize=12)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    png = OUTDIR / f"f3_stand_{tpath.stem}.png"
    fig.savefig(png, dpi=100, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    # THE EXIT CODE CARRIES F3'S LETTER, on the median seed. The port contract's joints term is
    # printed as the open debt it is -- not folded into this exit, not silently dropped either.
    return 0 if ok_f3 else 1


if __name__ == "__main__":
    sys.exit(run())
