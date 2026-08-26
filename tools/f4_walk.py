"""f4_walk.py -- THE BODY WALKS THROUGH THE PARSER, or the walk membrane's falsifiers fire.

`docs/THE_SLICE.md` rung 3's successor: the musculoskeletal body WALKING on muscle control --
not a mover with gait playback, and not a black-box policy. MOVE is a formula registered in the
real parser (`tools/parser.py`), and its content is the STAND port plus one derived oscillator.

RULE 0 lives in `tools/walk_port.py`'s docstring, stated before the build. Restated here as the
three things this harness measures, because a falsifier that is not in the harness is a wish:

    1. TRAVEL      mean forward speed within 25% of theHuman's comfortable_speed_ms (0.9924 m/s)
    2. PERIODICITY footfall autocorrelation >= 0.60 -- a limit cycle, not a drift downfield
    3. UPRIGHT     pelvis >= 80% of the derived stand target for the whole run
    ABLATION       oscillator amplitudes forced to zero -> travel collapses below 20% of target

FALSIFIER 1 IS THE ONE THIS PROJECT HAS ALREADY BEEN CAUGHT BY. A distance is a receipt, and the
trainer hands you the same receipt for a walk, a bound, and a seizure that drifts downfield: the
celebrated 13.52-body-length walker scored PERIODICITY 0.25 -- no repeating cycle at all -- and
lost 5.5 body lengths to a one-micron nudge. Speed alone can never distinguish those, so speed
alone is not reported here without the cycle beside it.

FALSIFIER 2 IS THE ABLATION, AND IT RUNS THE SAME CODE. `gain=0.0` multiplies the oscillator
amplitudes out inside `walk_formula` itself -- it is not a second harness that could drift away
from the thing it ablates. A body that travels just as far with the oscillator off was falling
forward, and the rhythm proved nothing.

TEN SEEDS, NOT ONE (2026-08-04), for the reason F3 carries the same amendment: a 1e-6 nudge --
73,000x below the finest angle this world publishes -- moves the stand policy's survival from
6.30 s to 9.08 s, so a single rollout is one sample of a distribution reported as the answer.
Walking is composed over standing and inherits that sensitivity whole.

    THE HEADLINE IS THE MEDIAN OF TEN, WITH THE MIN AND THE SPREAD BESIDE IT.

The ablation is run on the SAME seeds, because an ablation judged on one start against a live
arm judged on another is two experiments wearing one name.

ZERO POSE-SCRIPTED FRAMES, BY CONSTRUCTION. After `seat_in_limits` at reset, nothing here writes
`d.qpos`. Every frame is `mj_step` under muscle control and this world's gravity.

    python tools/f4_walk.py                    # 10 seeds; exit 0 PASS, 1 FAIL
    python tools/f4_walk.py --seeds 1          # the retired single-rollout behaviour, exactly
    python tools/f4_walk.py --theta <path>     # judge a named arm
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                              # noqa: E402
from stand_port import derive_stand_port, MYOBODY                        # noqa: E402
from train_stand import (joint_ids, seat_in_limits, joint_frac_named,   # noqa: E402
                         NUDGE)
from classify_fall import classify_trace                                 # noqa: E402
from walk_port import (derive_walk_port, muscle_groups, move_formula_fn,  # noqa: E402
                       N_FREE, footfall_interval_s, cadence_factor,
                       CADENCE_FLOOR_FRAC)
from train_walk import foot_contact, CTRL_EVERY                          # noqa: E402
from chimera_gait import _periodicity                                    # noqa: E402
from parser import Parser, default_registry, Formula, EXCLUSIVE          # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
STAND_THETA = OUTDIR / "stand_theta.npy"
WALK_THETA = OUTDIR / "walk_theta.npy"
SECS = 6.0                    # JUDGED at 6 s; train_walk optimises 8 s -- train past what you judge
SPEED_TOL = 0.25              # the prediction's own 25%
PERIODICITY_BAR = 0.60
UPRIGHT_FRAC = 0.80
ABLATION_BAR = 0.20
SEEDS = 10                    # the headline is the median of these


def run_one(m, d, mujoco, P, theta_stand, theta_walk, groups, tgt, nu, gain, frames=0,
            entrained=False, seed=0, stand_class=None, w0=None, forward=0.0):
    """One life THROUGH THE PARSER. `gain=0.0` is the ablation, same code path.

    `seed = 0` is the UNPERTURBED control; every other seed nudges qpos by `NUDGE` after the
    seat, exactly as `train_stand.evaluate` and `stand_survival.py` do. One perturbation, one
    landmark (rule 19) -- three instruments nudging by three amounts would make every
    disagreement between them the instruments' rather than the body's.

    `entrained=True` supplies the WalkOscillator's live per-leg phase and the swing interlock
    THROUGH THE PARSER'S OBS -- which is the amendment walk_port's LEDGER named as the cost of
    this variant ("its cost is a parser obs amendment, foot contact into `obs`"). It is here
    because the ledger's own lesson from 2026-08-03 was that the trainer drove the entrained
    oscillator while the judge drove the clock, so two of eight trained numbers were dead at
    judgment and the entrained gait was NEVER JUDGED AT ALL. Training a variant the judge cannot
    run is not a test of the variant; it is a test of nothing.
    """
    reg = default_registry(theta_stand, tgt, nu)
    # MOVE was a named Refusal ("no trained formula -- its atoms are M3"). This is the formula.
    # NO `w0=` HERE. `move_formula_fn` takes (…, gain, stand_class) and nothing else -- a blind
    # regex that added w0 to every `stand_class=stand_class)` call site put it here too, which
    # imports fine and raises TypeError the moment MOVE is registered. Caught by reading the
    # callee's signature rather than by trusting the edit.
    reg["MOVE"] = Formula("MOVE", move_formula_fn(theta_stand, theta_walk, groups, tgt, nu, P,
                                                  gain=gain, stand_class=stand_class), EXCLUSIVE)
    PARSER = Parser(reg)
    PARSER.set_verb("MOVE", True)

    jids = joint_ids(m, mujoco)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    if seed:
        d.qpos[:] = d.qpos + np.random.default_rng(seed).normal(0.0, NUDGE, size=d.qpos.shape)
        mujoco.mj_forward(m, d)
    steps = int(SECS / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    # `all` / `jf` / `jn` carry the PER-JOINT diagnostic ported from f3_stand.py (2026-08-04).
    # comx/comy/polx/poly carry the CoM against the polygon the feet make, so classify_fall can
    # label the failure. Both exist for the same reason: F4 used to return a bare scalar per
    # falsifier, and a scalar that moves for reasons you cannot attribute is the shape of
    # measurement this project keeps getting caught by. A walk that fails now names the joints
    # it failed at and which way it went down.
    tr = {k: [] for k in ("t", "x", "z", "cr", "cl", "sup", "jf", "jn", "all",
                          "comx", "comy", "polx", "poly")}
    pics, fell_t, x0, driver = [], None, float(d.qpos[0]), None
    observer = None
    if stand_class is not None:
        import policy_classes as _PC
        if w0 is None:
            raise ValueError(
                "a stand_class needs omega_0 and this function will not derive it per rollout: "
                "`derive_stand_port()` loads the whole MuJoCo model to read the simulated body's "
                "mass. Compute it once in `run()` and pass it in.")
        observer = _PC.Observer(tgt, w0, stand_class.window, CTRL_EVERY * m.opt.timestep)
    _b = lambda n: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)]
    from walk_port import WalkOscillator                                  # noqa: E402
    osc = WalkOscillator(P["OUT omega_rad_s"],
                         eps=float(theta_walk[6]) if theta_walk.size > 6 else 2.0,
                         kappa=float(theta_walk[7]) if theta_walk.size > 7 else 4.0)         if entrained else None
    ctrl_dt = CTRL_EVERY * m.opt.timestep
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            # ROLL WAS MISSING FROM THIS DICT, and `move_formula_fn` read `obs.get("roll", 0.0)`.
            # So this judge multiplied 290 of the frozen stand policy's 1160 numbers by ZERO for
            # every walk arm it ever graded, while `train_walk.evaluate` computed roll and
            # trained against it. MEASURED before the repair (tools/walk_roll_probe.py, held-out
            # seeds 3-9 on walk_theta_entrained): travel 0.3495 -> 0.4603 m/s, +32% on the exact
            # quantity falsifier 1 reads. The walk port's LEDGER already records this species
            # once -- the trainer drove an entrained oscillator the judge did not run -- and this
            # is the same defect in a second place. The formula now REFUSES an obs with no lean
            # in it, so it cannot recur silently.
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            obs = {"z": z, "pitch": pitch, "roll": roll, "t": float(d.time),
                   "forward": forward}
            if observer is not None:
                # THE SUBSTRATE'S OWN SENSE OF ITS STATE. A PD stand policy needs rates, and a
                # rate needs a past; the observer is the judge's, at the judge's cadence, so the
                # trained substrate is driven here exactly as it was trained.
                observer.push(z, pitch, roll)
                obs["chan"] = observer.channels()
            if osc is not None:
                # THE ENTRAINED PLANT, SUPPLIED THROUGH THE PARSER'S OBS -- not around it. The
                # formula reads `obs.get("phases")` and `obs.get("swing_gate")`; it already did,
                # and nothing was ever putting them there.
                _cr, _cl = foot_contact(m, d, mujoco)
                obs["phases"] = osc.step(ctrl_dt, _cr, _cl)
                obs["swing_gate"] = {s_: osc.swing_allowed(s_, _cr, _cl) for s_ in ("r", "l")}
            u, trace = PARSER.command(obs)
            driver = trace.driver
            if u is not None:
                d.ctrl[:] = u
        mujoco.mj_step(m, d)
        if k in grab and ren is not None:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            cr, cl = foot_contact(m, d, mujoco)
            tr["t"].append(k * m.opt.timestep); tr["x"].append(float(d.qpos[0]))
            tr["z"].append(z); tr["cr"].append(cr); tr["cl"].append(cl)
            tr["sup"].append((1.0 if cr > 0 else 0.0) + (1.0 if cl > 0 else 0.0))
            _jf, _jn = joint_frac_named(d, jids)
            tr["jf"].append(_jf); tr["jn"].append(_jn)
            # EVERY joint, every sample -- not just the worst. f3_stand.py's own note: recording
            # only the argmax and then asking "how bad was joint X" by filtering the samples
            # where X happened to be worst overall answers a different question and always
            # understates. A joint at 1.08 under another at 1.10 is invisible to it.
            tr["all"].append({n: abs(float(d.qpos[adr]) - c) / h for adr, c, h, n in jids})
            com = d.subtree_com[0]
            foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
            _px = [float(_b(n)[0]) for n in ("calcn_r", "calcn_l", "toes_r", "toes_l")]
            _py = [float(_b(n)[1]) for n in ("calcn_r", "calcn_l", "toes_r", "toes_l")]
            tr["comx"].append(float(com[0] - foot[0]))
            tr["comy"].append(float(com[1] - foot[1]))
            tr["polx"].append(max(1e-9, 0.5 * (max(_px) - min(_px))))
            tr["poly"].append(max(1e-9, 0.5 * (max(_py) - min(_py))))
            if z < 0.5 * tgt and fell_t is None:
                fell_t = k * m.opt.timestep
                break
    if ren is not None:
        ren.close()
    dt_s = CTRL_EVERY * m.opt.timestep
    per, period = _periodicity(np.array(tr["sup"]), dt_s) if len(tr["sup"]) > 16 else (0.0, 0.0)
    elapsed = max(tr["t"][-1], 1e-9) if tr["t"] else 1e-9
    # PER-JOINT PEAK AND TIME-OVER-STOP, the diagnostic f3_stand.py already carries. `over` is
    # the one the ligament membranes are written in: a peak says a joint touched its stop, the
    # FRACTION says whether anything caught it. A ligament that engages late still shows a peak;
    # what says it CAUGHT the joint is the joint coming back inside.
    names = sorted(tr["all"][0]) if tr["all"] else []
    nsamp = max(len(tr["all"]), 1)
    peak = {n: max((s[n] for s in tr["all"]), default=0.0) for n in names}
    over = {n: 100.0 * sum(1 for s in tr["all"] if s[n] >= 1.0) / nsamp for n in names}
    # THE JUDGE MEASURES WHAT THE TRAINER OPTIMISES. `train_walk --cadence` scores this exact
    # function; if the judge did not compute it, the trained number would be dead at judgment --
    # the walk port's own 2026-08-03 lesson (the entrained oscillator trained for a session and
    # was never judged at all). Measured on every arm, scored on none of them here.
    _interval = footfall_interval_s(tr["cr"], tr["cl"], dt_s)
    return dict(seed=seed,
                speed=(float(tr["x"][-1]) - x0) / elapsed if tr["x"] else 0.0,
                footfall_interval_s=_interval, cadence_factor=cadence_factor(_interval, P),
                periodicity=per, period_s=period, fell_t=fell_t, driver=driver,
                z_min=min(tr["z"]) if tr["z"] else 0.0, held=elapsed,
                duty_r=float(np.mean([c > 0 for c in tr["cr"]])) if tr["cr"] else 0.0,
                duty_l=float(np.mean([c > 0 for c in tr["cl"]])) if tr["cl"] else 0.0,
                jmax=max(tr["jf"]) if tr["jf"] else 0.0,
                jworst=(max(zip(tr["jf"], tr["jn"]))[1] if tr["jf"] else "?"),
                peak=peak, over=over,
                fall=classify_trace(tr, tgt) if tr["t"] else None,
                tr=tr, pics=pics)


def run() -> int:
    import mujoco
    if not STAND_THETA.exists():
        raise SystemExit(f"no {STAND_THETA} -- walking is composed over standing. Refusing.")
    # --theta NAMES THE POLICY TO JUDGE. It was WALK_THETA hardcoded, so an A/B of three
    # trained arms could only be judged by copying files over each other -- which is how a
    # comparison silently becomes three readings of one arm.
    _wt = Path(sys.argv[sys.argv.index("--theta") + 1]) if "--theta" in sys.argv else WALK_THETA
    if not _wt.is_absolute():
        _wt = OUTDIR / _wt.name
    if not _wt.exists():
        raise SystemExit(f"no {_wt} -- refusing to judge a walk that was never trained (rule 20).")
    # --stand / --stand-class NAME THE SUBSTRATE. Walking is composed over standing, so when the
    # stand port's policy class changes the walk inherits it -- and a judge that can only load
    # ONE substrate can only judge ONE composition. `p_only` is the incumbent's own form, so the
    # default path is what this file has always run (tools/walk_pd_ab.py --selftest measures it).
    import policy_classes as _PC
    _st = Path(sys.argv[sys.argv.index("--stand") + 1]) if "--stand" in sys.argv else STAND_THETA
    if not _st.is_absolute():
        _st = OUTDIR / _st.name
    if not _st.exists():
        raise SystemExit(f"no {_st} -- refusing to compose a walk over a stand that does not "
                         f"exist (rule 20).")
    _sc_name = (sys.argv[sys.argv.index("--stand-class") + 1] if "--stand-class" in sys.argv
                else None)
    stand_class = _PC.get(_sc_name) if _sc_name else None
    theta_stand, theta_walk = np.load(_st), np.load(_wt)
    print(f"\n  judging: {_wt.name}   over stand {_st.name}"
          + (f" [{_sc_name}]" if _sc_name else " [p_only -- the incumbent's own form]"))
    P, S = derive_walk_port(), derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    groups = muscle_groups(m, d, mujoco)
    tgt, nu = S["OUT pelvis_target_m"], m.nu
    vt = P["OUT target_speed_ms"]
    # DERIVE theta_step FROM THE BODY (no free number): rigid inverted pendulum about the contact
    # centre, THE_LEVERS' own formula. Reset to neutral, read CoM height and the fore BoS edge.
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    _com_x, _com_h = float(d.qpos[0]), float(d.qpos[2])
    _xs = []
    for _b in ("r_foot", "l_foot", "r_toes", "l_toes"):
        try:
            _xs.append(float(d.xpos[m.body(_b).id][0]))
        except Exception:
            pass
    _fore = (max(_xs) - _com_x) if _xs else 0.0
    P["theta_step"] = (float(np.arcsin(min(1.0, _fore / _com_h)))
                       if _com_h > 1e-6 else 0.0)
    P["forward_lever"] = forward

    # THE SUBSTRATE'S SHAPE, CHECKED AGAINST THE MODEL'S OWN nu (never against a block count
    # divided out of the file -- `parser.check_theta_shape`'s rule, and the substitution that
    # left `parser_tests` falsifier 1 silently dead for several commits).
    if stand_class is not None:
        stand_class.decode_theta(theta_stand, nu)
    # omega_0 ONCE PER RUN, not once per rollout -- `run_one`'s own ValueError says exactly this
    # ("this function will not derive it per rollout: derive_stand_port() loads the whole MuJoCo
    # model to read the simulated body's mass. Compute it once in run() and pass it in"). It was
    # referenced there and never defined or passed, so any --stand-class run raised NameError
    # BEFORE reaching the ValueError written to catch that case: the guard's own precondition was
    # the thing that crashed. Derived, not chosen: sqrt(g / com_height), both published.
    w0 = _PC.omega0(S) if stand_class is not None else None

    entrained = "--entrained" in sys.argv or theta_walk.size == N_FREE + 2
    nseeds = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else SEEDS
    # --held-out JUDGES ON SEEDS 3..9 ONLY. `docs/LOCOMOTION_OBJECTIVE_DIAGNOSIS.md` section 6:
    # the trainer selects on 0-2 and the train/test gap on the stand is +0.88 s, so a comparison
    # reporting all-ten medians ranks the arm that overfits its three training seeds best. The
    # default stays 0..9 so every number this file has already published remains reproducible.
    seed_ids = ([s for s in range(nseeds) if s not in (0, 1, 2)] if "--held-out" in sys.argv
                else list(range(nseeds)))
    nseeds = len(seed_ids)
    # THE FORWARD LEVER (THE_LEVERS.md, chain lever -> lean). Only T5's launch metric needs it;
    # default 0 keeps every historical run bit-identical. Measured from THIS body at reset, never
    # assumed: theta_step = asin(fore_edge / com_h), the operator's rigid-inverted-pendulum formula.
    forward = (float(sys.argv[sys.argv.index("--forward") + 1]) if "--forward" in sys.argv
               else 0.0)

    # THE SAME SEEDS FOR BOTH ARMS. The ablation is the walk's control, and a control
    # run from a different initial condition than the thing it controls is not a control.
    lives = [run_one(m, d, mujoco, P, theta_stand, theta_walk, groups, tgt, nu, 1.0,
                     entrained=entrained, seed=s, stand_class=stand_class, w0=w0,
                     forward=forward) for s in seed_ids]
    abls = [run_one(m, d, mujoco, P, theta_stand, theta_walk, groups, tgt, nu, 0.0,
                    entrained=entrained, seed=s, stand_class=stand_class, w0=w0,
                    forward=forward) for s in seed_ids]

    def med(rows, key):
        return float(np.median([r[key] for r in rows]))

    # THE REPRESENTATIVE IS A REAL SEED, never an average of ten -- an averaged trace is a body
    # nothing ever simulated, and the picture has to be a rollout that happened. Chosen on
    # PERIODICITY because that is falsifier 1, the one this project has already been caught by.
    per_all = np.array([r["periodicity"] for r in lives])
    med_per = float(np.median(per_all))
    rep_i = int(np.argmin(np.abs(per_all - med_per)))
    live = run_one(m, d, mujoco, P, theta_stand, theta_walk, groups, tgt, nu, 1.0, frames=8,
                   entrained=entrained, seed=lives[rep_i]["seed"], stand_class=stand_class, w0=w0,
                   forward=forward)
    abl = abls[rep_i]

    spd_all = np.array([r["speed"] for r in lives])
    zmin_all = np.array([r["z_min"] for r in lives])
    abl_all = np.array([r["speed"] for r in abls])
    med_spd, med_zmin, med_abl = float(np.median(spd_all)), float(np.median(zmin_all)), \
        float(np.median(abl_all))
    int_all = np.array([r["footfall_interval_s"] for r in lives])
    med_int = float(np.median(int_all))

    pct = 100.0 * med_spd / vt
    abl_pct = 100.0 * med_abl / vt
    # THE BARS READ THE MEDIAN OF TEN. Not the best seed, not seed 0: the bars are claims about
    # the POLICY, and a claim about a policy cannot be settled by one initial condition.
    ok_travel = abs(med_spd - vt) <= SPEED_TOL * vt
    ok_cycle = med_per >= PERIODICITY_BAR
    ok_up = med_zmin >= UPRIGHT_FRAC * tgt and sum(1 for r in lives
                                                   if r["fell_t"] is None) > nseeds // 2
    ok_abl = abs(med_abl) < ABLATION_BAR * vt
    ok = ok_travel and ok_cycle and ok_up and ok_abl
    n_pass = dict(
        travel=sum(1 for r in lives if abs(r["speed"] - vt) <= SPEED_TOL * vt),
        cycle=sum(1 for r in lives if r["periodicity"] >= PERIODICITY_BAR),
        upright=sum(1 for r in lives if r["z_min"] >= UPRIGHT_FRAC * tgt and r["fell_t"] is None),
        ablation=sum(1 for r in abls if abs(r["speed"]) < ABLATION_BAR * vt))

    print("\nF4 -- THE BODY WALKS THROUGH THE PARSER")
    print("=" * 78)
    print(f"  world: g = {g:.4f} m/s2 (theHuman, via load_body -- never assumed)")
    print(f"  parser driver: {live['driver']}   (MOVE was a named Refusal until this rung)")
    print(f"  DERIVED, not searched: omega {P['OUT omega_rad_s']:.4f} rad/s "
          f"(stride {P['OUT stride_s']:.4f} s), antiphase pi, target {vt:.4f} m/s")
    print(f"  forward lever: {forward:.3f}  (theta_step {P['theta_step']:.4f} rad from body "
          f"geometry; fore_edge {_fore:.4f} m, com_h {_com_h:.4f} m)")
    # N_FREE, not a re-derived `2*len(OSC_JOINTS)`: that expression was correct until the
    # oscillator gained eps and kappa, and then it silently reported 6 for an 8-number search.
    # An instrument that recomputes a fact instead of reading it will disagree with the thing
    # it measures the moment the thing changes.
    # THE COUNT IS READ FROM THE THETA, not from the clock's constant. This printed `{N_FREE}`
    # = 6 while judging an 8-number entrained policy -- the shape guard accepted it correctly and
    # the line beneath still said six. Exactly the species this file was already amended for:
    # "an instrument that recomputes a fact instead of reading it will disagree with the thing
    # it measures the moment the thing changes."
    print(f"  free numbers trained: {theta_walk.size} "
          f"({'ENTRAINED: 3 amps + 3 offsets + eps + kappa' if entrained else 'CLOCK: 3 amps + 3 offsets'})"
          f"  |  stand theta FROZEN ({theta_stand.size} numbers, reused unchanged)")
    # THE SHAPE GUARD NOW KNOWS TWO LEGAL WIDTHS, and says which plant it inferred. N_FREE is
    # the clock; N_FREE + 2 adds eps and kappa and MEANS the entrained oscillator. Inferring the
    # plant from the theta's own width is what stops the 2026-08-03 defect recurring by
    # accident: an 8-number theta can no longer be judged on a 6-number plant in silence.
    if theta_walk.size not in (N_FREE, N_FREE + 2):
        raise SystemExit(f"walk_theta holds {theta_walk.size} numbers; the port declares "
                         f"{N_FREE} (clock) or {N_FREE + 2} (entrained: +eps, +kappa). "
                         f"Refusing to judge a walk against a theta of the wrong shape.")
    print("-" * 78)
    print(f"  JUDGED OVER {nseeds} SEEDS -- nudge {NUDGE:g} on qpos, seed 0 UNPERTURBED. Every "
          f"bar below reads the MEDIAN;")
    print(f"  the min and the spread are printed with it, because one rollout is a coin toss.")
    print(f"{'seed':>5}{'speed':>10}{'period.':>9}{'period s':>10}{'foot dt':>9}"
          f"{'pelvis MIN':>12}{'held':>8}{'ablation':>10}  fall")
    for r, ab in zip(lives, abls):
        mark = " <- median" if r["seed"] == live["seed"] else ""
        _lab = (r["fall"]["label"] if r["fall"] is not None else "?") if r["fell_t"] else "-"
        print(f"{r['seed']:>5}{r['speed']:>+10.4f}{r['periodicity']:>9.2f}{r['period_s']:>10.2f}"
              f"{r['footfall_interval_s']:>8.3f}s{r['z_min']:>11.4f}m{r['held']:>7.2f}s"
              f"{ab['speed']:>+10.4f}  {_lab}{mark}")
    print(f"  {'':>3}  median  {med_spd:>+8.4f}{med_per:>9.2f}{'':>10}{med_zmin:>11.4f}m"
          f"{'':>8}{med_abl:>+10.4f}")
    print(f"  {'':>3}  spread  {spd_all.max()-spd_all.min():>8.4f}"
          f"{per_all.max()-per_all.min():>9.2f}{'':>10}"
          f"{zmin_all.max()-zmin_all.min():>11.4f}m{'':>8}"
          f"{abl_all.max()-abl_all.min():>10.4f}")
    print("-" * 78)
    print(f"  1. TRAVEL       median {med_spd:+.4f} m/s = {pct:.0f}% of derived "
          f"(bar {100*(1-SPEED_TOL):.0f}-{100*(1+SPEED_TOL):.0f}%)  ->  "
          f"{'PASS' if ok_travel else 'FAIL'}   [{n_pass['travel']}/{nseeds} seeds]")
    print(f"  2. PERIODICITY  median {med_per:.2f} (bar >= {PERIODICITY_BAR:.2f}), min "
          f"{per_all.min():.2f}, period {live['period_s']:.2f} s vs derived stride "
          f"{P['OUT stride_s']:.2f} s  ->  {'PASS' if ok_cycle else 'FAIL'}   "
          f"[{n_pass['cycle']}/{nseeds} seeds]")
    # THE CADENCE, MEASURED ON EVERY ARM AND SCORED ON NONE HERE. Reported beside periodicity
    # because the two answer different questions and were being conflated: periodicity asks IS
    # THERE A CYCLE, the interval asks HOW LONG IS A STEP. A body can shuffle rhythmically.
    print(f"  2b. CADENCE     median footfall interval {med_int:.3f} s vs theHuman's step_time "
          f"{P['IN  step_time_s']:.4f} s ({100*med_int/P['IN  step_time_s']:.0f}%), floor "
          f"{CADENCE_FLOOR_FRAC:.2f} -> {'stride' if med_int >= CADENCE_FLOOR_FRAC*P['IN  step_time_s'] else 'SHUFFLE'}"
          + ("   (no touchdown pair -- nothing to measure)" if med_int <= 0 else ""))
    print(f"  3. UPRIGHT      median pelvis MIN {med_zmin:.4f} m = "
          f"{100*med_zmin/tgt:.0f}% of target (bar {100*UPRIGHT_FRAC:.0f}%), held "
          f"{live['held']:.2f}/{SECS:.1f} s  ->  {'PASS' if ok_up else 'FAIL'}   "
          f"[{n_pass['upright']}/{nseeds} seeds]")
    print(f"     duty R/L {live['duty_r']:.2f}/{live['duty_l']:.2f} "
          f"(theHuman publishes {P['OUT duty_factor']:.2f})")
    print(f"  4. ABLATION     oscillator OFF (gain=0, same code path, same {nseeds} seeds): "
          f"median {med_abl:+.4f} m/s = {abl_pct:.0f}% of derived")
    print(f"     bar: must stay under {100*ABLATION_BAR:.0f}%  ->  "
          f"{'PASS -- the rhythm is doing the work' if ok_abl else 'FAIL -- it travels without the oscillator; the rhythm is decorative'}"
          f"   [{n_pass['ablation']}/{nseeds} seeds]")
    if nseeds > 1:
        # SEED 0 vs THE MEDIAN, per bar. Task 3's falsifier, and it is checked on the walk's own
        # quantities rather than inherited from the stand's.
        print(f"  SEED 0 vs MEDIAN, per bar:")
        devs = []
        for label, vals in (("speed", spd_all), ("periodicity", per_all),
                            ("pelvis min", zmin_all)):
            s0, md = float(vals[0]), float(np.median(vals))
            dev = 100.0 * (md - s0) / max(abs(s0), 1e-9)
            devs.append(abs(dev))
            print(f"    {label:14} seed 0 {s0:8.4f}   median {md:8.4f}   "
                  f"single-rollout is {(-dev):+6.1f}%")
        print(f"    task-3 falsifier (median within 5% of seed 0 on every bar): "
              + (f"FIRES -- worst deviation {max(devs):.1f}%; seed 0 was already the answer."
                 if max(devs) <= 5.0 else
                 f"does not fire -- worst deviation {max(devs):.1f}%."))
    # ── WHICH JOINTS, AND WHICH WAY IT WENT DOWN (ported from f3_stand.py, 2026-08-04) ──────
    # F4 used to return a bare scalar per falsifier. A walk that fails now NAMES its offenders,
    # because "periodicity 0.22" tells you the gait is not a gait and nothing about what to fix.
    print(f"  5. JOINTS       worst {live['jmax']:.2f} of range at {live['jworst']}"
          + ("  (< 1.00, none through a stop)" if live['jmax'] < 1.0 else "  -- THROUGH ITS STOP"))
    _off = sorted(((n, v) for n, v in live["peak"].items() if v >= 0.90), key=lambda p: -p[1])
    if _off:
        print(f"     per joint, peak and % of the run spent at/past the stop:")
        for _n, _v in _off[:6]:
            print(f"       {_n:22} peak {_v:.2f}   over {live['over'][_n]:5.1f}% of the run")
    else:
        print(f"     no joint reached 0.90 of its range")
    if live["fall"] is not None:
        _f = live["fall"]
        print(f"  6. THE FALL     {_f['label'].upper()}"
              + (f" at t={_f['t_fall']:.2f} s, confidence {_f['confidence']:.2f}"
                 if _f['t_fall'] is not None else " -- did not fall")
              + f"   (CoM peak: fore {_f.get('peak_fore_frac', 0):.2f}, "
                f"lat {_f.get('peak_lat_frac', 0):.2f} of the base the feet make)")
        if _f["confidence"] < 0.35 and _f["t_fall"] is not None:
            print(f"     LOW CONFIDENCE -- both axes left the base together, so this is a "
                  f"diagonal/tumbling fall, not a clean {_f['label']} one. Reported as the "
                  f"weak separation it is rather than as a label that reads clean.")
    print(f"  qpos writes after reset: 0 (by construction -- the harness contains no write)")
    print("=" * 78)
    print(f"  F4 VERDICT: {'PASS -- the body walks' if ok else 'FAIL'}")
    if not ok:
        which = [n for n, v in (("1 TRAVEL", ok_travel), ("2 PERIODICITY", ok_cycle),
                                ("3 UPRIGHT", ok_up), ("4 ABLATION", ok_abl)) if not v]
        print(f"  FIRED: {', '.join(which)}")
        if not ok_cycle and ok_travel:
            print("    speed reached WITHOUT a cycle -- this is falsifier 1 exactly: it arrives,")
            print("    it does not walk. The 13.52-body-length champion scored 0.25 here.")
        if not ok_abl:
            print("    the ablation travelled too -- the body is falling forward and the")
            print("    oscillator proved nothing (a primitive whose ablation passes proved nothing).")

    # ---- THE LEDGER: the headline triple per bar, machine-readable ---------
    # Named after the arm. Three walk arms judged in one session all wrote one file once
    # (stand_survival.py's own note, one directory over), and the A/B had one surviving row.
    import json
    LOGDIR = ROOT / "agent_logs"
    LOGDIR.mkdir(parents=True, exist_ok=True)
    # THE SUBSTRATE IS PART OF THE ARM'S NAME. Two walks over two different stand policies are
    # two arms, and a file named only after the walk theta would let them overwrite each other --
    # the exact defect the line above records for three walk arms sharing one filename.
    _stem = _wt.stem + (f"__{_sc_name}" if _sc_name else "") + ("__heldout" if "--held-out"
                                                                in sys.argv else "")
    _out = LOGDIR / f"f4_walk_{_stem}.json"
    _out.write_text(json.dumps(dict(
        theta=_wt.name, stand_theta=_st.name, stand_class=_sc_name or "p_only",
        forward_lever=forward, theta_step_rad=float(P["theta_step"]),
        held_out_only=bool("--held-out" in sys.argv), seed_ids=seed_ids,
        entrained=bool(entrained), seeds=nseeds, nudge=NUDGE, g=g,
        target_speed_ms=vt, stride_s=P["OUT stride_s"],
        speed_median=med_spd, speed_min=float(spd_all.min()), speed_max=float(spd_all.max()),
        speed_per_seed=[float(v) for v in spd_all],
        periodicity_median=med_per, periodicity_min=float(per_all.min()),
        periodicity_per_seed=[float(v) for v in per_all],
        footfall_interval_median_s=med_int,
        footfall_interval_per_seed=[float(v) for v in int_all],
        cadence_floor_s=CADENCE_FLOOR_FRAC * P["IN  step_time_s"],
        cadence_factor_median=float(np.median([r["cadence_factor"] for r in lives])),
        period_s_median=float(np.median([r["period_s"] for r in lives])),
        z_min_median=med_zmin, z_min_min=float(zmin_all.min()),
        held_median=float(np.median([r["held"] for r in lives])),
        held_min=float(min(r["held"] for r in lives)),
        ablation_median=med_abl, ablation_per_seed=[float(v) for v in abl_all],
        duty_r_median=float(np.median([r["duty_r"] for r in lives])),
        duty_l_median=float(np.median([r["duty_l"] for r in lives])),
        seeds_passing=n_pass, median_seed=int(live["seed"]),
        verdict=bool(ok), verdict_travel=bool(ok_travel), verdict_cycle=bool(ok_cycle),
        verdict_upright=bool(ok_up), verdict_ablation=bool(ok_abl)), indent=1), encoding="utf8")
    print(f"  JSON: {_out}")

    # ---- THE PICTURE ------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(15.0, 7.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.05, 1], hspace=0.4, wspace=0.28)
    if live["pics"]:
        ax = fig.add_subplot(gs[0, :]); ax.imshow(np.concatenate(live["pics"], axis=1))
        ax.axis("off")
        ax.set_title("eight frames: MOVE held, walking on muscle control", fontsize=10)
    t = live["tr"]["t"]
    ax = fig.add_subplot(gs[1, 0])
    # EVERY SEED, the median in full colour. A single trace is what this plot used to show, and
    # the spread it hid is the thing multi-seed judging exists to surface.
    for r in lives:
        ax.plot(r["tr"]["t"], r["tr"]["x"], color="#c0392b", lw=0.8, alpha=0.30)
    ax.plot(t, live["tr"]["x"], color="#c0392b", lw=2.0, label=f"walked (median seed {live['seed']})")
    for ab in abls:
        ax.plot(ab["tr"]["t"], ab["tr"]["x"], color="#7f8c8d", lw=0.7, alpha=0.30)
    ax.plot(abl["tr"]["t"], abl["tr"]["x"], color="#7f8c8d", lw=1.6, ls="-.",
            label="ABLATION (oscillator off)")
    ax.plot(t, [vt * s for s in t], color="#1a7f37", ls="--", lw=1.4, label=f"derived {vt:.3f} m/s")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7)
    ax.set_title(f"TRAVEL -- median {med_spd:.3f} m/s ({pct:.0f}%) vs ablation "
                 f"{med_abl:.3f} ({abl_pct:.0f}%)", fontsize=9)
    ax = fig.add_subplot(gs[1, 1])
    ax.step(t, [c > 0 for c in live["tr"]["cr"]], color="#c0392b", lw=1.4, where="post", label="R")
    ax.step(t, [1.3 if c > 0 else 0.3 for c in live["tr"]["cl"]], color="#2471a3", lw=1.4,
            where="post", label="L")
    ax.set_ylim(-0.3, 1.9); ax.set_xlabel("s"); ax.legend(fontsize=7)
    ax.set_title(f"FOOTFALL, median seed -- periodicity {live['periodicity']:.2f} "
                 f"(median of {nseeds}: {med_per:.2f}, bar {PERIODICITY_BAR:.2f}), period "
                 f"{live['period_s']:.2f} s", fontsize=8.5)
    ax = fig.add_subplot(gs[1, 2])
    for r in lives:
        ax.plot(r["tr"]["t"], r["tr"]["z"], color="#8e44ad", lw=0.8, alpha=0.30)
    ax.plot(t, live["tr"]["z"], color="#8e44ad", lw=1.6)
    ax.axhline(tgt, color="#1a7f37", lw=2.0, label=f"stand target {tgt:.3f} m")
    ax.axhline(UPRIGHT_FRAC * tgt, color="#1a7f37", ls="--", lw=1.2,
               label=f"{100*UPRIGHT_FRAC:.0f}% -- the bar")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7)
    ax.set_title(f"UPRIGHT, all {nseeds} -- median pelvis MIN {100*med_zmin/tgt:.0f}% of target",
                 fontsize=9)
    fig.suptitle(f"F4 -- WALK THROUGH THE PARSER   {_wt.name}   g={g:.3f} m/s2   "
                 f"median of {nseeds}: {'PASS' if ok else 'FAIL'}   speed {pct:.0f}%  "
                 f"periodicity {med_per:.2f}  ablation {abl_pct:.0f}%", fontsize=12)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    png = OUTDIR / f"f4_walk_{_wt.stem}.png"
    fig.savefig(png, dpi=100, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
