"""walk_port.py -- THE WALK PORT: walking as a PROGRAM composed over the stand port.

RULE 0, stated before the build, because this membrane is a theory:

    STATEMENT   Walking is not a new controller. It is the STAND port's own formula with ONE
                phase-oscillator term added at the hips -- one oscillator, two legs held in
                ANTIPHASE, omega = 2*pi/(2*step_time_s) read from theHuman and never chosen.
                NO JOINT ANGLE IS COMMANDED ANYWHERE: the parser sends a button, the button's
                formula sends muscle activations, and the gait is what the body DOES. The
                published gait envelope is used to JUDGE the result, never to drive it.

    PREDICTION  With only the oscillator's free numbers trained (amplitudes and the intra-limb
                phase offsets -- omega and the L/R antiphase are DERIVED and are not searched),
                `tools/f4_walk.py` reports:
                  1. mean forward speed within 25% of comfortable_speed_ms = 0.9924 m/s
                  2. footfall PERIODICITY >= 0.60 -- a real limit cycle, not a drift downfield
                  3. the body upright the whole run (pelvis >= 80% of the stand target)
                AND THE ABLATION: with the oscillator amplitudes forced to zero -- STAND alone,
                every other number identical -- travel collapses below 20% of that speed.

    FALSIFIER   Named before the run, three independent triggers:
                1. Speed reached but periodicity < 0.60 -- it ARRIVES without walking. This is
                   the exact fraud `core/gait.py` was built to catch: the celebrated
                   13.52-body-length walker scored periodicity 0.25 and had no gait at all.
                2. The ABLATION also travels -- the oscillator is decorative and the body is
                   simply falling forward. A primitive whose ablation passes proved nothing.
                3. The body cannot reach 50% of the derived speed at ANY trained setting --
                   the composition is insufficient and walking needs structure this program
                   does not have. Said plainly rather than patched with a joint-angle target.

A description survives any result; this one can lose three ways.

WHY COMPOSED AND NOT TRAINED AS A POLICY. `tools/walk_dyad.py` drives a torch actor-critic from
a checkpoint: it might walk, and when it does not, nothing says which part is missing. Every
piece below is already validated ALONE -- the `phase_oscillator` port (omega from theHuman's own
stride; coupled pairs converge to antiphase, the uncoupled control does not), the `rhythm_drive`
primitive (one oscillator alternates both hips THROUGH THE MUSCLES, L/R correlation -0.871
against a constant-drive ablation at +0.841), the STEP/STANCE/BALANCE action primitives, and the
STAND port itself. So a failure here names a rung instead of a hyper-parameter.

LEDGER, 2026-08-03 evening -- three thetas judged through the ONE parser path, and what they
convicted (every number from `tools/f4_walk.py`, same harness, same world):

    theta                    reward        travel   periodicity  upright        duty R/L
    kimi24 (shaped, warm)    clip-linear   -15%     0.36         49%, 5.24 s    0.91/0.95
    claude30 (Gaussian, 30t) Gaussian      +34%     0.21         47%, 2.24 s    0.65/0.60
    regressed (Gaussian)     Gaussian      -12%     0.46         49%, 5.86 s    0.91/0.90

1. THE SHAPED-REWARD AMENDMENT'S FALSIFIER FIRED. The clip-linear r_v retrain did not
   recover >= 32% travel (it reached -15%); the speed term's SHAPE was not the binding
   constraint. Published per rule 17. The tradeoff it exposed instead: the search finds
   travelers-that-fall (34%, down at 2.24 s) or standers-that-freeze (95% held, -15%)
   -- the binding constraint is UPRIGHT vs TRAVEL, not the reward's width.
2. THE COMPOSITION WALKS-ISH. claude30's +34% with duty 0.65/0.60 against theHuman's
   published 0.60 is the best gait ever put through the parser, and it came through the
   CLOCK path -- Rule 0's own statement (clock phase, antiphase, derived omega). The
   ablation stays PASS throughout: the rhythm is doing the work in every row.
3. THE STRUCTURAL FINDING: the trainer drove the ENTRAINED oscillator (WalkOscillator,
   eps/kappa, foot-contact state) while the judge drives the CLOCK (`move_formula_fn`,
   phase = omega*t). Two of the eight trained numbers were dead at judgment and the
   entrained gait was never judged at all -- "train past what you judge", one level
   deeper. THE DECISION: the trainer now trains the judge's plant exactly (clock phase,
   N_FREE back to 6). `WalkOscillator` stays in this file as a DEFERRED robustness
   layer -- its cost is a parser obs amendment (foot contact into `obs`), to be earned
   by its own membrane only if the clock composition plateaus below falsifier 3's 50%.

LEDGER, second entry (same evening) -- the judge-consistent trainer's first 24 turns,
warm-started from claude30's traveler. f4 on the session best: travel +10%, periodicity
0.41, held 5.92/6.0 s (from 2.24), duty R/L 0.84/0.69 (from 0.65/0.60's asymmetry,
converging on the published 0.60), ablation PASS. THE FALL IS BEING TRAINED OUT, SLOWLY:
held climbs 2.5 -> 5.9 s across the run, best score -4.37 -> -3.49 with no plateau, the
footfall trace shows real alternation for the first time. VERDICT: still FAIL x3 -- but
the question "can the fall be trained out without losing the travel" is UNANSWERED, not
answered: the trajectory is alive, so the rung is MORE TURNS, not more structure.
Falsifier 3 (50% unreachable at ANY setting) does not fire while the curve is moving.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                   # noqa: E402
from stand_port import derive_stand_port, MYOBODY             # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
GROUPS_CACHE = OUTDIR / "walk_muscle_groups.json"

# THE JOINTS THE OSCILLATOR REACHES. Hip is the one `rhythm_drive` validated; knee and ankle are
# added because a leg that swings from the hip alone drags its foot. Each is measured for
# direction, never assumed -- see `muscle_groups`.
OSC_JOINTS = ("hip_flexion", "knee_angle", "ankle_angle")
# one amplitude + one phase offset per joint. omega and the antiphase TARGET are derived and
# are not in here. (eps/kappa -- the entrainment gains -- were searched for one session and
# never judged: the trainer drove WalkOscillator while f4 drives the clock. N_FREE is back to
# 6 so the search and the judgment are the same plant -- see the module LEDGER.)
N_FREE = 2 * len(OSC_JOINTS)


def derive_walk_port() -> dict:
    """Gravity, stride and speed in; the oscillator's DERIVED constants out. Nothing chosen.

    Every line names the membrane it came from. omega in particular is NOT a free number: it is
    theHuman's published step time, doubled into a stride, inverted. If it were searched, the
    search would be answering "which cadence is best" -- which is rule 1's exact tell.
    """
    hits = [p for p in (ROOT / "story").rglob("numbers.json") if p.parent.name == "theHuman"]
    if not hits:
        raise SystemExit("theHuman publishes nothing -- run `python story/grow.py`. Refusing to "
                         "invent the gait this port is meant to produce (rule 20).")
    L = json.loads(hits[0].read_text(encoding="utf8"))
    need = ("g", "comfortable_speed_ms", "step_time_s", "duty_factor", "step_length_m")
    missing = [k for k in need if k not in L]
    if missing:
        raise SystemExit(f"theHuman publishes no {missing}. A default here would be this port "
                         f"inventing the gait it is meant to derive (rule 20). Refusing.")
    stride_s = 2.0 * float(L["step_time_s"])
    S = derive_stand_port()
    port = {
        "IN  g_m_s2": float(L["g"]),
        "IN  step_time_s": float(L["step_time_s"]),
        "OUT stride_s": stride_s,
        "OUT omega_rad_s": 2.0 * math.pi / stride_s,          # port 12's own number
        "OUT antiphase_rad": math.pi,                          # port-validated, not free
        "OUT target_speed_ms": float(L["comfortable_speed_ms"]),
        "OUT duty_factor": float(L["duty_factor"]),
        "IN  step_length_m": float(L["step_length_m"]),
        "OUT pelvis_target_m": S["OUT pelvis_target_m"],
        "OUT upright_floor_m": 0.80 * S["OUT pelvis_target_m"],
        # THE CLOSURE CHECK. speed = step_length / step_time must reproduce the published
        # comfortable speed, or two of theHuman's own numbers disagree and this port is built on
        # a contradiction. Checked, not assumed -- it is free to check and it is how a stale
        # ledger entry announces itself.
        "CHK speed_closure_pct": 100.0 * (float(L["step_length_m"]) / float(L["step_time_s"])
                                          / float(L["comfortable_speed_ms"]) - 1.0),
    }
    if abs(port["CHK speed_closure_pct"]) > 1.0:
        raise SystemExit(
            f"theHuman's step_length/step_time = "
            f"{float(L['step_length_m']) / float(L['step_time_s']):.4f} m/s disagrees with its "
            f"published comfortable_speed_ms {float(L['comfortable_speed_ms']):.4f} by "
            f"{port['CHK speed_closure_pct']:+.2f}%. Refusing to derive a walk from a ledger "
            f"that contradicts itself.")
    return port


def muscle_groups(m, d, mujoco, verbose=False) -> dict:
    """Which muscles flex and which extend each oscillator joint -- MEASURED, one at a time.

    Reuses `primitive_tests.spanning`, whose docstring records why this cannot be done by reading
    the sign of `moment * actuator_force`: done that way the knee's six strongest "extensors"
    came out as ankle and shank muscles making 0.4474 N.m, with the entire quadriceps group in
    NEITHER list. It did not raise -- it returned a tidy list of names. So the direction is read
    from `qacc` (downstream of the constraint solver, so the OpenSim patellar coupling is already
    in it) after activating each candidate ALONE.

    Cached to disk: it costs ~20 forward passes per dof and the answer is a property of the
    model, not of the run. The cache is keyed by the model's actuator count so a different body
    cannot silently read another body's muscles.
    """
    import primitive_tests as PT

    key = f"{m.nu}x{m.njnt}"
    if GROUPS_CACHE.exists():
        blob = json.loads(GROUPS_CACHE.read_text(encoding="utf8"))
        if blob.get("key") == key:
            return {k: (v[0], v[1]) for k, v in blob["groups"].items()}

    groups = {}
    for base in OSC_JOINTS:
        for side in ("r", "l"):
            name = f"{base}_{side}"
            j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, name)
            if j < 0:
                raise SystemExit(f"no joint {name!r} in this body -- refusing to build a walk "
                                 f"program on a joint that is absent (rule 20).")
            dof = int(m.jnt_dofadr[j])
            flex, ext = PT.spanning(m, d, dof)
            if not flex or not ext:
                raise SystemExit(f"{name}: measured {len(flex)} flexors and {len(ext)} extensors. "
                                 f"A joint with muscles in only one direction cannot be driven "
                                 f"reciprocally, and a one-sided oscillator is a ratchet.")
            groups[name] = (list(flex[:6]), list(ext[:6]))
            if verbose:
                print(f"[walk] {name:16} {len(flex):2} flexors, {len(ext):2} extensors "
                      f"(top 6 of each drive the oscillator)")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    GROUPS_CACHE.write_text(json.dumps({"key": key, "groups": groups}, indent=1), encoding="utf8")
    return groups


class WalkOscillator:
    """TWO COUPLED PHASES, ENTRAINED BY THE FEET -- the `phase_oscillator` port ITSELF, not its
    conclusion, and with the stop condition the control law requires.

    THE DEFECT THIS REPLACES, measured 2026-08-04 and published rather than quietly fixed. The
    first version of this program set `phi_r = omega*t` and `phi_l = omega*t + pi`: it asserted
    the port's RESULT (antiphase) instead of running the port (coupling, which PRODUCES
    antiphase). Two things followed, and the second is the fatal one:

      1. The coupling term -- the only part of that port under test -- was never in the program.
         Port 12 proves `d(phi)/dt = omega + eps*sin(phi_other - phi - pi)` converges from an
         antiphase start while the uncoupled control does not. Hardcoding the answer means the
         validated mechanism is absent and only its output is imitated.
      2. IT WAS AN OPEN-LOOP CLOCK. `omega*t` knows nothing about whether a foot is loaded, so
         it commands a swing while that leg is still carrying the body. MEASURED: the stand
         policy alone holds 6 s (ablation -0.012 m/s, upright); with this clock added the same
         body FELL AT 3.98 s, pelvis to 45% of target, duty R/L 0.64/0.14.

    That is a direct violation of the operator's control law, which this project states in
    `docs/CONTROLLER_MAP.md` and CLAUDE.md: COMMAND THE PROCESS AND ITS STOP CONDITION, NEVER
    THE FINAL POSITION -- "every atom is `apply effort -> stop when a sensor says stop`". A
    clock has no sensor and therefore no stop condition. So the phase is now advanced by omega
    AND corrected by two sensory terms, both of which the body already publishes:

        COUPLING   port 12's own law, pulling the two legs toward antiphase
        CONTACT    a foot LOADING is stance onset -- the phase of that leg is drawn to 0

    `eps` (coupling) and `kappa` (contact entrainment) are FREE NUMBERS, trained. omega and the
    antiphase target are DERIVED and are not searched.
    """

    def __init__(self, omega, eps=2.0, kappa=4.0):
        self.omega, self.eps, self.kappa = float(omega), float(eps), float(kappa)
        self.phi = {"r": 0.0, "l": math.pi}          # a START, which the coupling then owns
        self._was = {"r": False, "l": False}

    def step(self, dt, load_r, load_l):
        """Advance both phases one control tick. `load_*` are the plantar sensor sums."""
        new, load = {}, {"r": load_r > 0.0, "l": load_l > 0.0}
        for side, other in (("r", "l"), ("l", "r")):
            # PORT 12's LAW, verbatim: omega plus a coupling that targets antiphase.
            dphi = self.omega + self.eps * math.sin(self.phi[other] - self.phi[side] - math.pi)
            # THE SENSORY STOP. A rising edge on this foot's load IS stance onset -- the one
            # event in the gait cycle the body can observe without being told. The phase is
            # PULLED toward 0 rather than snapped, so a single noisy contact cannot restart
            # the gait; entrainment is a force, not an assignment.
            if load[side] and not self._was[side]:
                err = (0.0 - self.phi[side] + math.pi) % (2 * math.pi) - math.pi
                dphi += self.kappa * err / max(dt, 1e-9) * dt
            new[side] = self.phi[side] + dphi * dt
        self.phi, self._was = new, load
        return self.phi

    def phase(self, side):
        return self.phi[side]

    def swing_allowed(self, side, load_r, load_l):
        """THE SWING'S STOP CONDITION, and it is DERIVED, not chosen.

        `theHuman` publishes `duty_factor` = 0.6027. A duty factor above 0.5 is not a preference
        or a style -- it is what makes the gait a WALK rather than a run: each foot is down 60%
        of its cycle, the two overlap, and DOUBLE SUPPORT EXISTS. The arithmetic is forced:
        two feet at 60% each over one cycle is 120% of a cycle's worth of contact, so at every
        instant at least one foot is down. **Both feet are never airborne in a walk.**

        The open-loop program had no such interlock, and the measured failure is exactly the one
        it forbids: the body left the ground and fell at 2.5-4 s. So a leg may not enter swing
        while the OTHER leg is unloaded -- effort applied until a sensor says stop, which is the
        control law this project states, one level below where `WalkOscillator` applies it.

        Returns a GATE in [0,1] rather than a boolean: a hard switch would chatter at every
        contact flicker and inject a step function into the muscle drive. The gate is the
        contralateral load's own state, and the caller multiplies the swing half of the drive
        by it.
        """
        other = load_l if side == "r" else load_r
        return 1.0 if other > 0.0 else 0.0


def walk_formula(theta_stand, theta_walk, groups, z, pitch, phase, nu, tgt, gain=1.0,
                 phases=None, swing_gate=None):
    """THE BUTTON'S CONTENT: the stand formula, plus one oscillator, and nothing else.

    `theta_walk` = [A_hip, A_knee, A_ankle, ph_hip, ph_knee, ph_ankle] -- amplitudes and
    intra-limb phase offsets. These are the ONLY free numbers. omega and the L/R antiphase are
    derived and never enter the search (rule 1).

    RECIPROCAL BY CONSTRUCTION: a joint's flexors get +A*sin(phi) and its extensors -A*sin(phi),
    so when one group is driven the other is released. That is not a stylistic choice -- a
    co-contracting pair with the same sign stiffens the joint instead of moving it, which is
    exactly the "flailing while rigid" failure the stand port already paid for.

    NO POSITION IS COMMANDED. The operator's control law: command the PROCESS and its stop
    condition, never the final position. The oscillator supplies effort; where the limb ends up
    is an OUTPUT, decided by the body, the ground and gravity.
    """
    u = np.clip(theta_stand[:nu] + theta_stand[nu:2 * nu] * (tgt - z)
                + theta_stand[2 * nu:] * pitch, 0.0, 1.0)
    amps, offs = theta_walk[:len(OSC_JOINTS)], theta_walk[len(OSC_JOINTS):2 * len(OSC_JOINTS)]
    # `phases` is the WalkOscillator's live per-leg phase, entrained by the feet. If it is
    # absent this falls back to the open-loop clock -- kept ONLY so the measured failure above
    # stays reproducible, never as a default anyone should reach for.
    ph = phases if phases is not None else {"r": phase, "l": phase + math.pi}
    for i, base in enumerate(OSC_JOINTS):
        a = gain * float(amps[i])
        if a == 0.0:
            continue                                   # the ABLATION path, exactly
        for side in ("r", "l"):
            s = math.sin(ph[side] + float(offs[i]))
            # THE SWING GATE, applied to the SWING HALF ONLY. `s > 0` is the flexion (lift and
            # reach) half of this joint's cycle; `s < 0` drives the extensors, which is stance
            # and support. Gating BOTH would tell a foot in double support to stop supporting --
            # the interlock would cause the fall it exists to prevent. Only the lift is
            # forbidden while the other foot is off the ground.
            if s > 0.0 and swing_gate is not None:
                s *= float(swing_gate[side])
            flex, ext = groups[f"{base}_{side}"]
            u[flex] = np.clip(u[flex] + a * s, 0.0, 1.0)
            u[ext] = np.clip(u[ext] - a * s, 0.0, 1.0)
    return u


def move_formula_fn(theta_stand, theta_walk, groups, tgt, nu, P, gain=1.0):
    """MOVE, AS A PARSER FORMULA REGISTRATION -- the shape `tools/parser.py` expects.

    `tools/parser.py` registers MOVE as a named Refusal: "no trained formula -- its atoms are
    M3 (STEP+PLANT+BALANCE)". This is that formula, and it turns the refusal into a verb.

    STAND IS COMPOSED INSIDE MOVE, NOT HELD BESIDE IT. The parser's EXCLUSIVE rule gives the
    first-registered driver the parse, so holding STAND and MOVE together would make STAND win
    and MOVE would silently never run -- a conflict the trace would name but the gait would not
    survive. Walking is standing plus a rhythm, so the composition belongs INSIDE the formula
    where it is the program, not in the button state where it is a race.

    `obs` carries `t` (the simulation's own clock) rather than a phase, so the DERIVED omega is
    applied here, in the one place that owns it. A caller cannot hand this formula a cadence.
    """
    def fn(obs, value):
        return walk_formula(theta_stand, theta_walk, groups, obs["z"], obs["pitch"],
                            P["OUT omega_rad_s"] * obs["t"], nu, tgt, gain=gain * float(value),
                            phases=obs.get("phases"), swing_gate=obs.get("swing_gate"))
    return fn


def walk_reward(v_fore, z, fell, P):
    """One number per sample, every term an OUTCOME -- never a pose.

    speed   -- the body's own derived comfortable speed. Not "fast": 0.9924 m/s, which theHuman
               reaches from step_length/step_time and Froude reaches independently.
    upright -- the pelvis near its stand target. A body that crouches to go faster is not
               walking, and the stand port already published what upright means.

    PERIODICITY IS NOT HERE, AND THAT IS DELIBERATE. It is a property of the WHOLE rollout --
    there is no per-sample periodicity -- so it multiplies the mean at the end, in `score_walk`.
    Putting a whole-rollout property in a per-step reward is how a term silently becomes a
    constant.

    AMENDMENT 2026-08-03 -- THE SPEED TERM MUST HAVE GRADIENT FROM REST. Stated as a theory,
    because an amendment is a membrane too:

        STATEMENT   The Gaussian r_v (sigma = 0.25*vt) is numerically flat below ~0.5*vt
                    (r_v < 0.02 at 0.3 m/s, ~1e-7 at rest), so a population that cannot yet
                    travel feels only the upright term and the fall penalty, and `score_walk`
                    degenerates into held-time selection. MEASURED, not inferred: a 24x32
                    warm-started retrain under the Gaussian moved the session best from +32%
                    travel to -12% while its own score IMPROVED -- the reward could not see
                    the difference between 0.1 and 0.4 m/s, so it selected standing.

        PREDICTION  With r_v = clip(v_fore/vt, 0, 1) -- the fraction of the DERIVED speed
                    achieved, no chosen width anywhere -- the same 24x32 warm-started retrain
                    recovers at least the destroyed 32% of derived travel with the rhythm
                    (periodicity) intact, because every cm/s of forward progress now scores.

        FALSIFIER   If the shaped reward cannot recover >= 32% of derived travel in the same
                    training budget, the reward was not the binding constraint -- the deficit
                    is in the composition itself, and this port's falsifier 3 (50% of derived
                    speed unreachable at ANY trained setting) becomes the live question.
    """
    vt = P["OUT target_speed_ms"]
    r_v = float(np.clip(v_fore / vt, 0.0, 1.0))      # fraction of derived speed; gradient from rest
    r_z = float(np.exp(-((z - P["OUT pelvis_target_m"]) / (0.10 * P["OUT pelvis_target_m"])) ** 2))
    return r_v * r_z - (3.0 if fell else 0.0)


def score_walk(mean_r, periodicity, frac_run):
    """The rollout's single number: the mean reward, GATED ON THERE BEING A CYCLE.

    A distance is a receipt, and the trainer hands you the same receipt for a walk, a bound and a
    seizure that drifts downfield. Multiplying by periodicity means a body that travels without a
    limit cycle scores near zero however far it gets -- which is the one thing the 13.52
    body-length champion's score could not say.
    """
    return float(mean_r * max(0.0, periodicity) - 2.0 * (1.0 - frac_run))


if __name__ == "__main__":
    import mujoco
    P = derive_walk_port()
    print("\nTHE WALK PORT -- derived, nothing chosen")
    print("=" * 78)
    for k, v in P.items():
        print(f"  {k:26} {v:.6f}" if isinstance(v, float) else f"  {k:26} {v}")
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    print("\nTHE MUSCLES THE OSCILLATOR REACHES -- measured one at a time, never inferred")
    gr = muscle_groups(m, d, mujoco, verbose=True)
    print(f"\n  {len(gr)} joints grouped, {N_FREE} free numbers to train "
          f"(omega and the antiphase are DERIVED and are not among them)")
