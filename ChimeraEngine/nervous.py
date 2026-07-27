"""nervous.py — THE NERVOUS SYSTEM (ROADMAP Track S, step S6).

    "With the muscles, we'll attach them to a nervous system -- trained algorithms of where to put
     your hands and feet based off surrounding state conditions and what the input is."

The nervous system is the thing that decides the DIALS. It reads the body's state and the goal,
and writes one activation per muscle. That is the whole interface, and it is deliberately the exact
signature a TRAINED policy has:

        observe(tree, goal) -> obs vector        (state conditions + input)
        act(obs)            -> activations       (one per muscle, each in [0, 1])

so `brain_gpu.py`-style training can replace the hand-written controller without anything else
changing. The body does not know or care which is driving it.

MUSCLES ONLY PULL, so every degree of freedom needs an ANTAGONIST -- a flexor and an extensor.
A controller cannot ask for negative force; it must choose a side and how hard. That constraint is
biology's, not a modelling convenience, and it is what makes co-contraction (bracing both at once
to stiffen a joint) a real, available strategy rather than a special case.

Nothing here authors motion. The controller sets activations; the physics decides what happens.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics_articulated import Tree, Muscle, make_muscle       # noqa: E402


# ── the antagonist pair: what one degree of freedom actually needs ────────────────────────────
@dataclass
class Antagonist:
    """Two muscles on opposite sides of one joint. `flexor` raises the angle, `extensor` lowers it.

    Which is which is MEASURED (by the sign of the moment arm), never assumed -- get it backwards
    and the controller drives the joint away from its target with perfect confidence.
    """
    joint: int
    flexor: Muscle
    extensor: Muscle

    def drive(self, u: float, co_contract: float = 0.0) -> None:
        """u in [-1, 1]: positive pulls the flexor, negative the extensor. `co_contract` adds equal
        tension to BOTH, which stiffens the joint without moving it -- exactly what a body does
        when it braces."""
        u = float(np.clip(u, -1.0, 1.0))
        c = float(np.clip(co_contract, 0.0, 1.0))
        self.flexor.dial = float(np.clip(max(u, 0.0) + c, 0.0, 1.0))
        self.extensor.dial = float(np.clip(max(-u, 0.0) + c, 0.0, 1.0))


def attach_antagonist(tree: Tree, joint: int, parent_link: int, child_link: int,
                      offset: float, along: float, max_tension: float,
                      name: str = 'j', offset_axis=(1.0, 0.0, 0.0)) -> Antagonist:
    """Bolt a flexor/extensor pair across a joint, then VERIFY the two levers oppose each other.

    The pair is placed symmetrically about the joint axis; which one turns out to be the flexor is
    then read off the measured moment arms rather than assumed from the geometry.
    """
    # `offset_axis` is the direction the pair straddles the joint in. It MUST be perpendicular to
    # the hinge axis or neither muscle has a moment arm -- an X-offset about an X-hinge is zero
    # leverage, and the check below catches it rather than quietly producing a limp joint.
    u = np.asarray(offset_axis, float)
    u = u / (np.linalg.norm(u) + 1e-15)
    a = tree.add_muscle(make_muscle(f'{name}_a', origin_link=parent_link,
                                    origin=tuple(u * offset + np.array([0.0, 0.0, along])),
                                    insert_link=child_link,
                                    insert=tuple(u * offset * 0.5 - np.array([0.0, 0.0, along])),
                                    max_tension=max_tension))
    b = tree.add_muscle(make_muscle(f'{name}_b', origin_link=parent_link,
                                    origin=tuple(-u * offset + np.array([0.0, 0.0, along])),
                                    insert_link=child_link,
                                    insert=tuple(-u * offset * 0.5 - np.array([0.0, 0.0, along])),
                                    max_tension=max_tension))
    arm_a = tree.moment_arm(a, joint)
    arm_b = tree.moment_arm(b, joint)
    if arm_a * arm_b >= 0:
        raise ValueError(f'{name}: the pair does not oppose -- arms {arm_a:+.5f} and {arm_b:+.5f}. '
                         'Both muscles pull the joint the same way, so it can only be driven one way.')
    flexor, extensor = (a, b) if arm_a > 0 else (b, a)
    return Antagonist(joint=joint, flexor=flexor, extensor=extensor)


# ── the interface a trained policy will implement ─────────────────────────────────────────────
class NervousSystem:
    """State conditions + input -> activations. Subclass and implement `act`."""

    def observe(self, tree: Tree, goal: np.ndarray) -> np.ndarray:
        """What the body can feel: joint angles, joint rates, and what it is being asked for.
        This IS the observation vector a trained policy would receive."""
        return np.concatenate([tree.q, tree.qd, np.asarray(goal, float)])

    def act(self, obs: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def drive(self, tree: Tree, pairs: list[Antagonist], goal, co_contract: float = 0.0) -> np.ndarray:
        u = self.act(self.observe(tree, goal))
        for k, pair in enumerate(pairs):
            pair.drive(u[k], co_contract)
        return u


class Reflex(NervousSystem):
    """A stretch reflex: pull toward the target angle, damped by the joint's own rate.

    u = kp * (target - q) - kd * qd, per joint. This is the simplest thing that genuinely deserves
    the name -- it senses length and rate and responds, which is what a spinal reflex does. It is a
    stand-in for a trained policy, not a rival to one: identical interface, so swapping in a learned
    controller changes nothing about the body.
    """

    def __init__(self, n: int, kp: float = 3.0, kd: float = 0.35):
        self.n = n
        self.kp = kp
        self.kd = kd

    def act(self, obs: np.ndarray) -> np.ndarray:
        q = obs[:self.n]
        qd = obs[self.n:2 * self.n]
        target = obs[2 * self.n:3 * self.n]
        return np.clip(self.kp * (target - q) - self.kd * qd, -1.0, 1.0)


@dataclass
class Policy(NervousSystem):
    """A LEARNED nervous system: a small tanh network, exactly what brain_gpu.py evolves.

    Present so the seam is provably real -- the same body, driven by weights instead of a rule.
    Untrained weights produce nonsense, which is the honest starting point; training fills them in.
    """
    n_obs: int
    n_act: int
    hidden: int = 16
    W1: np.ndarray = field(default=None)
    b1: np.ndarray = field(default=None)
    W2: np.ndarray = field(default=None)
    b2: np.ndarray = field(default=None)

    def __post_init__(self):
        rng = np.random.default_rng(0)
        if self.W1 is None:
            self.W1 = rng.normal(0, 0.5, (self.hidden, self.n_obs))
            self.b1 = np.zeros(self.hidden)
            self.W2 = rng.normal(0, 0.5, (self.n_act, self.hidden))
            self.b2 = np.zeros(self.n_act)

    def act(self, obs: np.ndarray) -> np.ndarray:
        h = np.tanh(self.W1 @ obs + self.b1)
        return np.tanh(self.W2 @ h + self.b2)

    def genome(self) -> np.ndarray:
        return np.concatenate([self.W1.ravel(), self.b1, self.W2.ravel(), self.b2])

    def set_genome(self, g: np.ndarray) -> 'Policy':
        i = 0
        for arr in (self.W1, self.b1, self.W2, self.b2):
            n = arr.size
            arr[...] = g[i:i + n].reshape(arr.shape)
            i += n
        return self


# ── running the loop ──────────────────────────────────────────────────────────────────────────
def run(tree: Tree, brain: NervousSystem, pairs: list[Antagonist], goal,
        seconds: float, dt: float = 1e-4, control_hz: float = 200.0,
        co_contract: float = 0.0, extra_forces=None) -> dict:
    """Close the loop: the brain sets dials at its own rate, the physics runs at its own.

    A real nervous system does not fire every microsecond -- separating the control rate from the
    integration rate is honest, and it is also what stops a controller from hiding instability
    behind an absurd update frequency.
    """
    every = max(1, int(round(1.0 / (control_hz * dt))))
    n_steps = int(seconds / dt)
    goal = np.asarray(goal, float)
    err_hist = []
    for k in range(n_steps):
        if k % every == 0:
            brain.drive(tree, pairs, goal, co_contract)
        tree.step(dt, extra_forces=extra_forces() if callable(extra_forces) else extra_forces)
        if not np.all(np.isfinite(tree.q)):
            return {'diverged': True, 'final_err': np.inf, 'settle_err': np.inf}
        err_hist.append(float(np.max(np.abs(tree.q - goal))))
    tail = err_hist[int(len(err_hist) * 0.8):]              # the last 20%: has it SETTLED?
    return {'diverged': False,
            'final_err': err_hist[-1],
            'settle_err': float(np.mean(tail)),
            'settle_jitter': float(np.std(tail)),
            'peak_err': float(np.max(err_hist))}


def robust_score(make_tree, brain, goal, n_starts: int = 8, seconds: float = 2.0,
                 spread: float = 0.35, seed: int = 0) -> dict:
    """Score from N RANDOMISED starts and keep the WORST.

    The project has already paid for this lesson once: a celebrated walker scored 13.5 body lengths
    from ONE rollout, had periodicity 0.25 (no limit cycle at all), and lost 5.5 body lengths to a
    ONE-MICRON change in start height. One rollout is a coin toss. `robustness` = worst/mean; a real
    controller sits near 1.0, a lucky one near 0.
    """
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(n_starts):
        tree, pairs = make_tree()
        tree.q[:] = np.asarray(goal, float) + rng.uniform(-spread, spread, tree.n)
        tree.qd[:] = rng.uniform(-spread, spread, tree.n)
        r = run(tree, brain, pairs, goal, seconds)
        scores.append(np.inf if r['diverged'] else r['settle_err'])
    scores = np.asarray(scores, float)
    finite = scores[np.isfinite(scores)]
    worst = float(np.max(scores))
    mean = float(np.mean(finite)) if finite.size else np.inf
    return {'worst_err': worst, 'mean_err': mean, 'n_diverged': int(np.sum(~np.isfinite(scores))),
            'robustness': float(mean / worst) if worst > 0 and np.isfinite(worst) else 0.0,
            'scores': scores.tolist()}
