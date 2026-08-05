"""policy_classes.py -- THE POLICY CLASS AS DATA: a named list of observation channels.

`docs/LOCOMOTION_POLICY_DESIGN.md` section 1 says what the stand policy IS:

    u = clip(a0 + kh*(tgt - z) + kp*pitch + kr*roll, 0, 1)

and section 2 names what it ASSUMES -- "a linear function of three instantaneous scalars. No
zdot, no pitch_rate, no roll_rate, so the controller cannot distinguish leaning forward and
returning from leaning forward and accelerating." Section 6's third consequence: "the missing
derivative outranks the missing phase."

THIS FILE IS THAT SENTENCE MADE INTO A PARAMETER. Read the formula again with the names taken
out and it is one shape:

    u = clip(a0 + SUM_c k_c * obs_c, 0, 1)

so a POLICY CLASS is fully specified by an ORDERED TUPLE OF CHANNEL NAMES plus whether it carries
the constant. `p_only` is `("z_err", "pitch", "roll")` -- and that is not a reimplementation of
the incumbent, it IS the incumbent: the same slices in the same order over the same theta, which
`benchmark_policies.py --selftest` proves bit-identically against `train_stand.evaluate` rather
than asserting here.

WHY THAT MATTERS MORE THAN THE TIDINESS. Every class in this file can be WARM-STARTED FROM THE
INCUMBENT by matching blocks ON THEIR CHANNEL NAME and zero-filling the rest. A PD policy whose
rate gains are zero is the P-only policy exactly, so the two arms of the T1 comparison begin at
the SAME POINT IN THE SAME SPACE and the derivative is the only variable between them. Train a
6-channel policy from scratch against the saved 3-channel one instead and the arms differ in the
form AND the training history AND the initial condition -- three coupled changes, which is a
three-body problem with no attributable answer (CLAUDE.md).

── THE THREE DERIVATIONS, because a channel is a quantity and a quantity has a unit ─────────────

1. THE RATE CHANNELS ARE DIVIDED BY omega_0 = sqrt(g / com_height), AND THAT IS NOT A SCALE
   FACTOR SOMEBODY LIKED. It is the plant's own frequency -- the inverted pendulum's, derived in
   `docs/THE_MATHEMATICS_OF_WALKING.md` and computed here from `theStance`'s published CoM height
   and this world's own g (2.6480 rad/s at g = 7.076, H = 1.0091). A mode of that pendulum has
   |xdot| = omega_0 * |x|, so `zdot / omega_0` carries the SAME UNIT (metres) and the SAME
   MAGNITUDE as `z_err`, and `pitch_rate / omega_0` the same as `pitch`. One spread therefore
   serves a position block and its rate block, and no per-channel constant is chosen (rule 1).
   Without it the two blocks would need different initial spreads and each would be a number
   nothing derives.

2. THE RATES ARE FINITE DIFFERENCES OF THE CONTROL SAMPLES, NOT `d.qvel`. Task 1 says "the
   policy computes velocity from one timestep difference" and task 2 contrasts that with a
   4-sample baseline; taking MuJoCo's exact qvel instead would make T2 a comparison between a
   noisy estimator and a noiseless one that no body has. The estimator is the policy's, at the
   policy's own 50 Hz cadence, and `window` is its one parameter.

3. THE PHASE'S ORIGIN IS THE DERIVED TARGET, NOT A RUNNING MEAN. `phi = atan2(zdot/omega_0,
   z - z_mean)` needs a z_mean; a running empirical mean would be a SECOND landmark for a
   quantity the port already publishes (rule 19) and would make phi depend on how long the
   rollout has run. `z_mean` is `OUT pelvis_target_m` -- the same 0.9201 m that `z_err` is
   measured from, so the phase plane and the height channel share one origin.

   NOTE WHAT THAT MAKES THE PHASE BASIS, because it is the whole of T3's falsifier: with
   cos(phi) = (z - z_mean)/A and sin(phi) = (zdot/omega_0)/A, the pair {sin phi, cos phi} is the
   PD pair {zdot/omega_0, -z_err} DIVIDED BY ITS OWN MAGNITUDE. Phase adds exactly one thing a PD
   policy does not have -- amplitude-independence, a response to the DIRECTION of the state in
   the phase plane regardless of how far from equilibrium it is. It adds no new sense.

── WHAT IS NOT HERE ─────────────────────────────────────────────────────────────────────────────

No trainer, no judge, no picture. This file answers "what is a policy" and nothing else, so the
runner (`tools/benchmark_policies.py`), the landscape instrument (`tools/search_landscape.py`)
and the walk arm all consume ONE definition. Two copies of a policy form is the species of defect
`tools/timestep_audit.py` was built for: they agree until one is edited.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# ── THE CHANNELS: every scalar a policy in this family may feed back, named once ───────────────
# name -> (unit, one-line meaning). DECLARED, never inferred -- `story/folding.py`'s rule, and
# the reason `aniso` misfolded four ways in one afternoon when it was inferred from equation text.
CHANNEL_UNITS = {
    "z_err":      ("m",   "tgt - z: pelvis height error against the DERIVED target"),
    "zdot":       ("m",   "d(z)/dt / omega_0: vertical rate, in the pendulum's own units"),
    "pitch":      ("rad", "sagittal lean"),
    "pitch_rate": ("rad", "d(pitch)/dt / omega_0"),
    "roll":       ("rad", "frontal lean"),
    "roll_rate":  ("rad", "d(roll)/dt / omega_0"),
    "sin_phi":    ("1",   "sin of the CoM phase angle in the (z_err, zdot) plane"),
    "cos_phi":    ("1",   "cos of the same"),
}

# The three the incumbent already has, in the order its theta stores them. This tuple IS the
# contract with every saved `stand_theta*.npy` on disk: a0 | kh | kp | kr.
P_CHANNELS = ("z_err", "pitch", "roll")
PD_CHANNELS = ("z_err", "zdot", "pitch", "pitch_rate", "roll", "roll_rate")
PHASE_CHANNELS = PD_CHANNELS + ("sin_phi", "cos_phi")

# The trainer's own cold spreads, read from `train_stand.main()` rather than restated: it builds
# sd = concat([full(nu, 0.15)] + [full(nu, 0.6)] * (blocks-1)). One landmark (rule 19).
COLD_A0_SD = 0.15
COLD_GAIN_SD = 0.6


def omega0(P) -> float:
    """The plant's own frequency, sqrt(g / com_height). Derived; nothing here chooses it.

    `docs/THE_MATHEMATICS_OF_WALKING.md`: stance is an inverted pendulum and `omega_0 = sqrt(g/H)`
    is what sets its capture point. Both inputs are published -- `theStance.g` and
    `theStance.com_height_m`, reaching this function through `stand_port.derive_stand_port`.
    """
    return math.sqrt(float(P["IN  g_m_s2"]) / float(P["OUT com_target_m"]))


class Observer:
    """THE POLICY'S OWN SENSE OF ITS STATE -- a ring of control samples, and the channels built
    from them. It is the only stateful thing in this file.

    The incumbent policy class is memoryless by construction (`u_t` is a function of the
    instantaneous observation), which is exactly why it has no derivative to feed back. Every
    class beyond `p_only` needs a PAST, and this is the smallest one that provides it: the last
    `window + 1` control samples of (z, pitch, roll).

    ONE RING, EVERY WINDOW. `window=1` is the single-tick difference of T1 and `window=4` the
    80 ms baseline of T2, and they run the identical code path so the baseline length is the one
    variable between them.

    THE FIRST FEW TICKS HAVE NO FULL BASELINE, and this uses the LONGEST ONE AVAILABLE rather
    than reporting zero. Reporting zero would make the policy P-only for the first 80 ms and then
    silently become PD -- a change of policy form mid-rollout, which is not a thing any falsifier
    here is written about. The shortest-baseline estimate is the SAME quantity at a coarser
    resolution, and at k = 0 both agree because the body starts from the keyframe at rest.
    """

    __slots__ = ("tgt", "w0", "window", "dt", "_z", "_p", "_r", "_n")

    def __init__(self, tgt: float, w0: float, window: int, dt: float):
        if window < 1:
            raise ValueError(f"window must be >= 1 control ticks, not {window}")
        self.tgt, self.w0, self.window, self.dt = float(tgt), float(w0), int(window), float(dt)
        n = self.window + 1
        self._z = np.zeros(n)
        self._p = np.zeros(n)
        self._r = np.zeros(n)
        self._n = 0                      # how many samples have ever been pushed

    def push(self, z: float, pitch: float, roll: float) -> None:
        i = self._n % (self.window + 1)
        self._z[i], self._p[i], self._r[i] = z, pitch, roll
        self._n += 1

    def _rate(self, buf) -> float:
        """(x_t - x_{t-k}) / (k*dt), with k the longest baseline this ring actually holds."""
        n = self._n
        if n < 2:
            return 0.0
        k = min(self.window, n - 1)
        cur = buf[(n - 1) % (self.window + 1)]
        old = buf[(n - 1 - k) % (self.window + 1)]
        return float(cur - old) / (k * self.dt)

    def channels(self) -> dict:
        """Every channel this family defines, for the sample just pushed. Cheap; the caller
        selects. Building all of them always is deliberate: a channel that is only computed when
        it is being fed back cannot be TRACED for the arm that does not feed it back, and a
        quantity you only measure when you are optimising it cannot say what the control arm was
        doing (train_walk's footfall interval, same rule)."""
        n = self._n
        i = (n - 1) % (self.window + 1)
        z, pitch, roll = float(self._z[i]), float(self._p[i]), float(self._r[i])
        # RATES IN THE PENDULUM'S UNITS -- see the module docstring, derivation 1.
        zdot = self._rate(self._z) / self.w0
        prate = self._rate(self._p) / self.w0
        rrate = self._rate(self._r) / self.w0
        # THE PHASE PLANE, origin at the DERIVED target (derivation 3). `z - z_mean` is
        # -(z_err) by construction, so the two channels share one landmark.
        dz = z - self.tgt
        phi = math.atan2(zdot, dz)
        return {
            "z_err": self.tgt - z,
            "zdot": zdot,
            "pitch": pitch,
            "pitch_rate": prate,
            "roll": roll,
            "roll_rate": rrate,
            "sin_phi": math.sin(phi),
            "cos_phi": math.cos(phi),
        }


@dataclass(frozen=True)
class PolicyClass:
    """A policy class IS its channel list. Everything else follows from it.

    `name`     the arm's name; also the checkpoint's stem, so two arms cannot overwrite each
               other's picture (the defect `train_stand.draw_turn` paid for).
    `channels` ordered; the order IS the theta's block order and is part of the contract.
    `has_a0`   the constant baseline. `docs/LOCOMOTION_POLICY_DESIGN.md` section 2.4 measured
               that this constant is doing the standing (a0 contributes 0.202 mean |activation|
               against kp's 0.076) and section 6.2 that it IS a memorised gravity. T5 turns it
               off, which is why it is a field and not an assumption.
    `window`   the derivative baseline, in control ticks. 1 = T1's single difference, 4 = T2's
               80 ms. Ignored by a class with no rate channel, and stated anyway so the two
               arms of T2 differ in this number and nothing else.
    """
    name: str
    channels: tuple = P_CHANNELS
    has_a0: bool = True
    window: int = 1
    note: str = ""

    # -- the three methods the runner's interface asks for ------------------------------------
    def obs_dim(self) -> int:
        """How many CHANNELS this class feeds back. Not the theta width -- that is obs_dim + a0,
        times nu, and conflating them is how `parser_tests` falsifier 1 sat silently dead for
        several commits (`nu = theta.size // 3` against a 4-block theta)."""
        return len(self.channels)

    def n_blocks(self) -> int:
        return self.obs_dim() + (1 if self.has_a0 else 0)

    def decode_theta(self, theta, nu: int) -> int:
        """theta -> obs_dim, REFUSING a checkpoint whose width this class cannot be.

        `nu` comes from the model. Deriving it from the theta instead is the substitution
        `parser.check_theta_shape` exists to forbid.
        """
        if nu <= 0:
            raise ValueError(f"nu = {nu}: refusing to decode a theta against nothing (rule 20).")
        if theta.size % nu:
            raise ValueError(
                f"{self.name}: theta holds {theta.size} numbers, not a whole number of "
                f"{nu}-muscle blocks ({theta.size / nu:.4f}). Refusing to guess the shape.")
        blocks = theta.size // nu
        want = self.n_blocks()
        if blocks != want:
            raise ValueError(
                f"{self.name}: theta holds {blocks} blocks of {nu}; this class applies {want} "
                f"({'a0, ' if self.has_a0 else ''}{', '.join(self.channels)}). Refusing to "
                f"zero-fill a policy into a shape it was never trained in.")
        return self.obs_dim()

    def build_obs(self, chan: dict) -> np.ndarray:
        """state -> the vector this class feeds back, in this class's own block order."""
        return np.fromiter((chan[c] for c in self.channels), dtype=float,
                           count=len(self.channels))

    def build_theta(self, nu: int, source=None, source_class=None) -> np.ndarray:
        """The starting point. COLD = the trainer's own cold init; WARM = the incumbent, matched
        BY CHANNEL NAME with everything this class adds set to ZERO.

        THE ZERO IS THE WHOLE EXPERIMENT. A PD policy whose rate gains are zero produces the same
        control as the P-only policy for every state, so the warm start is not "near" the
        incumbent, it IS the incumbent -- and `benchmark_policies.py --selftest` measures that
        rather than trusting this sentence. Every class therefore begins at one point, and the
        channels are the only difference between the arms.
        """
        if source is None:
            mu = [np.full(nu, 0.15)] if self.has_a0 else []
            mu += [np.zeros(nu)] * self.obs_dim()
            return np.concatenate(mu)
        if source_class is None:
            raise ValueError("a warm start needs the SOURCE's class -- a theta is a flat array "
                             "and its block order is not recoverable from its length. Refusing "
                             "to guess which gains are which (rule 19).")
        src = {}
        off = 0
        if source_class.has_a0:
            src["a0"] = source[:nu]
            off = nu
        for i, c in enumerate(source_class.channels):
            src[c] = source[off + i * nu: off + (i + 1) * nu]
        out = []
        if self.has_a0:
            out.append(np.array(src.get("a0", np.full(nu, 0.15)), dtype=float))
        for c in self.channels:
            out.append(np.array(src[c], dtype=float) if c in src else np.zeros(nu))
        return np.concatenate(out)

    def build_sd(self, nu: int) -> np.ndarray:
        """The cold SPREAD, one block per theta block.

        EVERY GAIN BLOCK GETS THE SAME SPREAD, and that is the payoff of derivation 1: the rate
        channels arrive already divided by omega_0, so a rate gain and its position gain have the
        same unit and the same magnitude, and one number covers both. A phase channel is
        dimensionless in [-1, 1] against pitch's ~0.26 rad, so its gain sits inside a factor of
        ~3 of the others -- a property of how far this body sways, not a constant chosen here,
        and the derived step (`derive_step`) measures the whole vector's usable scale anyway.
        """
        sd = [np.full(nu, COLD_A0_SD)] if self.has_a0 else []
        sd += [np.full(nu, COLD_GAIN_SD)] * self.obs_dim()
        return np.concatenate(sd)

    def blocks(self, theta, nu: int):
        """theta -> {block name: 290-vector}. The one place the slicing happens."""
        self.decode_theta(theta, nu)
        out, off = {}, 0
        if self.has_a0:
            out["a0"] = theta[:nu]
            off = nu
        for i, c in enumerate(self.channels):
            out[c] = theta[off + i * nu: off + (i + 1) * nu]
        return out

    def control(self, theta, nu: int, chan: dict) -> np.ndarray:
        """u = clip(a0 + SUM_c k_c * obs_c, 0, 1). The whole policy, and this is all of it."""
        off = 0
        if self.has_a0:
            u = np.array(theta[:nu], dtype=float)
            off = nu
        else:
            u = np.zeros(nu)
        for i, c in enumerate(self.channels):
            u = u + theta[off + i * nu: off + (i + 1) * nu] * chan[c]
        return np.clip(u, 0.0, 1.0)


# ── THE REGISTRY: every arm these tasks name, and nothing that answers "which number is best" ──
# A class here answers a QUESTION ("does the derivative matter", "does the phase add anything",
# "which channel is load-bearing"). If an entry ever answers "which value of N is best", it is a
# sweep where a derivation belongs and it does not go in this table (rule 1).
def _ablate(ch):
    return tuple(c for c in PD_CHANNELS if c != ch)


REGISTRY = {
    # -- the control arm: THE INCUMBENT'S OWN FORM, not an approximation of it ------------------
    "p_only": PolicyClass(
        "p_only", P_CHANNELS, True, 1,
        "the incumbent exactly: a0|kh|kp|kr. Every other arm's control."),
    # -- T1: the missing derivative ------------------------------------------------------------
    "pd": PolicyClass(
        "pd", PD_CHANNELS, True, 1,
        "T1: rate feedback, one-tick difference. 7 blocks = 2030 numbers."),
    # -- T2: a longer baseline for the same derivative ------------------------------------------
    "pd_windowed": PolicyClass(
        "pd_windowed", PD_CHANNELS, True, 4,
        "T2: the identical channels over an 80 ms baseline. ONE variable against `pd`."),
    # -- T3: the oscillator basis ---------------------------------------------------------------
    "pd_phase": PolicyClass(
        "pd_phase", PHASE_CHANNELS, True, 1,
        "T3: PD plus {sin phi, cos phi} -- the PD pair normalised by its own amplitude."),
    # -- T4: which observation matters (six ablations of `pd`, one channel each) -----------------
    "pd_no_z": PolicyClass("pd_no_z", _ablate("z_err"), True, 1, "T4: no height"),
    "pd_no_zdot": PolicyClass("pd_no_zdot", _ablate("zdot"), True, 1, "T4: no vertical rate"),
    "pd_no_pitch": PolicyClass("pd_no_pitch", _ablate("pitch"), True, 1, "T4: no pitch"),
    "pd_no_pitch_rate": PolicyClass("pd_no_pitch_rate", _ablate("pitch_rate"), True, 1,
                                    "T4: no pitch rate"),
    "pd_no_roll": PolicyClass("pd_no_roll", _ablate("roll"), True, 1, "T4: no roll"),
    "pd_no_roll_rate": PolicyClass("pd_no_roll_rate", _ablate("roll_rate"), True, 1,
                                   "T4: no roll rate"),
    # -- T5: the constant baseline ---------------------------------------------------------------
    "pd_no_a0": PolicyClass(
        "pd_no_a0", PD_CHANNELS, False, 1,
        "T5: PD with NO baseline activation. a0 is a memorised gravity (design doc 6.2)."),
    "p_only_no_a0": PolicyClass(
        "p_only_no_a0", P_CHANNELS, False, 1,
        "T5's control: the incumbent's channels with the baseline removed."),
}


def get(name: str) -> PolicyClass:
    if name not in REGISTRY:
        raise SystemExit(f"no policy class {name!r}. Registered: {', '.join(sorted(REGISTRY))}. "
                         f"Refusing to invent an arm nobody stated a question for (rule 1).")
    return REGISTRY[name]


# ── THE OBJECTIVES ────────────────────────────────────────────────────────────────────────────
# TWO, and the second one exists because the first was MEASURED not to rank policies.
# `agent_logs/objective_matrix.json`, within-rung (the ladder's confound held constant):
#
#       height  vs survival  -0.042      height vs joints  -0.943
#       support vs survival  +0.891
#       joints  vs survival  -0.057
#
# `support` is the only component that tracks survival; `height` and `joints` are nearly
# perfectly anti-correlated and NEITHER relates to survival -- and `stand_reward` MULTIPLIES all
# three. T6's v2 removes the two that do not inform and the effort term with them.
OBJECTIVES = ("full", "support_only")


def rollout_score(mean_r: float, fell: bool, frac_run: float) -> float:
    """The rollout-level composition, shared by both objectives so it is not the variable.

    `train_stand.evaluate`: `tot/n - 3*fell - 2*(1 - (k+1)/steps)`. THE DURATION PENALTY STAYS IN
    v2 and that is a decision worth naming: T6 says to remove height, joints and effort, which
    are the per-sample MULTIPLIED factors. `-2*(1 - frac_run)` is not one of them; it is what
    stops an early fall outscoring a late one, because `mean(support)` over the first second --
    when the CoM is still centred by the keyframe -- is HIGHER than over twelve. Removing it
    would introduce a defect T6 did not ask for.
    """
    return mean_r - (3.0 if fell else 0.0) - 2.0 * (1.0 - frac_run)
