"""
attunement domain - EVOLVE THE MINIGAME ITSELF, judged by physics.

THE HUMAN'S FRAME (2026-07-16): "we can't rely too heavily on the system to define what
is fun itself, but when [you] give it a [reference] then it knows how to attune for it.
That is the key."

That is exactly this file, and exactly the game it trains. The chimera's call comes from
outside; the player does not invent it, they ATTUNE to it. One level up: the OBJECTIVE
(docs/objectives/attunement.json) is the call - a human/LLM statement of what good means
- and the TRAINER is the counter-wave that attunes to it at ~10k evals/sec. The system
never decides what is good. Given a reference, it finds the shape that answers it.

WHAT IS THE GENOME: the DESIGN of the minigame, not an instance of it.

    NOT a call - a GENERATOR of calls.

The distinction is load-bearing. A call's PHASE is meaningless as a design choice:
matching costs 4x E0 at every phase, and the exact inverse cancels at every phase, so
phase is the per-encounter roll, not a decision. Evolve one fixed call and you select a
design that is LUCKY in one instance - "one rollout is a coin toss" reappearing one
level up, at the design layer. So the genome states the STRUCTURE encounters are drawn
from (how many partials, over what band, at what amplitudes, how much coarse-tuning
help, how big the player's emitter is), measure() draws K encounters from it, and reports
the WORST. A design is judged on the encounters it GENERATES, never on its best night.

WHAT IS MEASURED: facts, never opinions (domain/objective discipline). Every number
comes out of core.attunement, where the rules ARE the physics: superposition decides,
nobody scores. No LLM is in this loop and none can be.

    python -m core.trainer --domain core.trainables.attunement \
                           --objective docs/objectives/attunement.json
"""
from __future__ import annotations

import random

import numpy as np

from core import attunement as A

# Evaluation cost is real: each encounter runs a listening agent to convergence.
# K x restarts x budget x ~113us. These are set so a population evaluates in minutes,
# not hours - and every one of them is a HONESTY knob, not a speed knob:
#   K_ENCOUNTERS > 1  because a design that works for one call is an anecdote.
#   RESTARTS     > 1  because the listener starts from a random emitter, so a single
#                     run measures its luck (core.attunement.measure keeps the WORST).
K_ENCOUNTERS = 3
RESTARTS = 2
BUDGET = 400
SEED = 0          # fixed: the trainer needs genome -> score to be deterministic


def seed() -> dict:
    """A deliberately MEDIOCRE starting design - not a good one.

    Seeding near a known-good answer would be hand-tuning wearing a trainer's coat: the
    result would be my taste with a fitness number stapled on. Start it bland and let
    the physics say what a good encounter is."""
    return {
        "n_partials": 3,
        "f_lo": 100.0,
        "f_hi": 800.0,
        "amp_lo": 0.4,
        "amp_hi": 1.0,
        "assist_hz": 40.0,     # deliberately too generous -> starts near "luck"
        "n_osc": 3,
    }


def mutate(g: dict, rng: random.Random) -> dict:
    """Perturb the DESIGN. Bounds are physical, not aesthetic:
    - frequencies stay inside what the sample rate can represent (Nyquist),
    - assist cannot go negative (it is a tolerance),
    - the emitter has at least one oscillator or there is no game."""
    h = dict(g)
    h["n_partials"] = max(1, min(6, g["n_partials"] + rng.choice([-1, 0, 0, 1])))
    h["n_osc"] = max(1, min(6, g["n_osc"] + rng.choice([-1, 0, 0, 1])))
    h["f_lo"] = min(max(20.0, g["f_lo"] * rng.gauss(1.0, 0.15)), A.SR * 0.4)
    h["f_hi"] = min(max(h["f_lo"] + 10.0, g["f_hi"] * rng.gauss(1.0, 0.15)), A.SR * 0.45)
    h["amp_lo"] = max(0.05, min(1.5, g["amp_lo"] * rng.gauss(1.0, 0.15)))
    h["amp_hi"] = max(h["amp_lo"], min(2.0, g["amp_hi"] * rng.gauss(1.0, 0.15)))
    h["assist_hz"] = max(0.0, min(400.0, g["assist_hz"] * rng.gauss(1.0, 0.25) + rng.gauss(0, 0.5)))
    return h


def _draw(g: dict, rng: np.random.Generator):
    """One encounter drawn from the design."""
    return [(float(rng.uniform(g["amp_lo"], g["amp_hi"])),
             float(rng.uniform(g["f_lo"], g["f_hi"])),
             float(rng.uniform(0, 2 * np.pi))) for _ in range(int(g["n_partials"]))]


def measure(g: dict) -> dict:
    """FACTS about the encounters this design generates. WORST of K, never the mean.

    A mean hides the bad night; the player does not experience the mean, they
    experience the encounter they got."""
    rng = np.random.default_rng(SEED)
    n_osc = int(g["n_osc"])
    rows = []
    for _ in range(K_ENCOUNTERS):
        call = _draw(g, rng)
        m = A.measure(call, seed=SEED, n_osc=n_osc, budget=BUDGET,
                      restarts=RESTARTS, assist_hz=float(g["assist_hz"]))
        rows.append(m)

    def worst(key, hi_is_bad):
        v = [r[key] for r in rows]
        return float(max(v) if hi_is_bad else min(v))

    return {
        # can the exact inverse actually silence it? (>0 = the emitter cannot express
        # the call: too few oscillators for too many partials -> unwinnable by anyone)
        "solvable": worst("solvable", hi_is_bad=True),
        # does the ASSUMED strategy (match it) get punished? physics, not a designer
        "punishes_naive": worst("punishes_naive", hi_is_bad=False),
        # THE GAME: how much better is listening than flailing
        "skill_gap": worst("skill_gap", hi_is_bad=False),
        # does listening pay? fraction of energy a listener removes
        "learnability": worst("learnability", hi_is_bad=False),
        # where the best listener lands vs the raw call (0 = trivial, ~1 = hopeless)
        "headroom": worst("headroom", hi_is_bad=True),
        # reported so a winner can be READ, never optimised against
        "n_partials": float(g["n_partials"]),
        "n_osc": float(g["n_osc"]),
        "assist_hz": float(g["assist_hz"]),
        "band_hz": float(g["f_hi"] - g["f_lo"]),
    }


def pinned(m: dict) -> list:
    return []


# ---------------------------------------------------------------------------
# THE HUMAN-TEST THRESHOLD - the anti-easy-out gate
#
# The human (2026-07-16): "I only ask [for a] sufficient threshold for it to understand
# when it's time to ask me to test it, because that's an easy out and always has been
# for the AI."
#
# EVERY OTHER GATE IN THIS STUDIO STOPS THE AI CLAIMING SUCCESS. THIS ONE STOPS IT
# OFFLOADING. "Let's have the human try it" is the cheapest sentence an agent can write:
# it sounds humble, it defers to the operator, it costs the agent nothing, and it spends
# the only resource the studio cannot manufacture. It is `bare blocked` wearing a
# courteous face - the same escape, dressed as deference.
#
# The attunement frame is what makes the bar computable, and it cuts BOTH ways. The
# human supplies the call (what good means); the machine generates the counter. So the
# machine may not go back to the human until it has ATTUNED AS FAR AS THE PHYSICS ALLOWS.
# Asking earlier is not humility - it is handing back an un-cancelled wave and calling it
# collaboration.
#
# What a human can answer that physics cannot: "is this FUN?" - the label, the taste, the
# reference signal. What physics answers on its own, and must: is it winnable, does the
# naive strategy get punished, is there room to be good, does listening pay. Spending a
# human on THOSE is spending them on arithmetic.
#
# So a design reaches a human ONLY once every machine-checkable question is already
# answered and only the unanswerable one is left.
# ---------------------------------------------------------------------------
HUMAN_TEST_BAR = (
    # (measure, kind, threshold, why a human must NOT be spent until this holds)
    ("solvable", "at_most", 0.02,
     "the exact inverse must actually silence it. an unwinnable game is a BUG, and "
     "physics already knows it is unwinnable - asking a human to discover that is "
     "outsourcing arithmetic."),
    ("punishes_naive", "at_least", 2.0,
     "the assumed strategy (match it) must actually cost something, or there is no "
     "expectation to violate and nothing to discover. superposition reports this for "
     "free."),
    ("skill_gap", "at_least", 3.0,
     "a listener must measurably beat a flailer. below this the outcome is LUCK, and a "
     "human testing a coin flip learns nothing but their own variance."),
    ("learnability", "at_least", 0.5,
     "listening must pay. if the learner's curve is flat the game is unlearnable, and "
     "that is visible without a person."),
    ("headroom", "band", (0.05, 0.80),
     "not handed to you (<0.05 = trivial), not hopeless (>0.80 = the best listener "
     "barely dents it). both ends are machine-visible."),
)


def ready_for_human(m: dict) -> tuple:
    """(ready: bool, reasons: list[str]).

    ready=False is NOT 'ask the human anyway, with caveats'. It means the MACHINE still
    has work to do, and the work is named. Only ready=True has earned the question that
    physics genuinely cannot answer: is it FUN?
    """
    fails = []
    for name, kind, thr, why in HUMAN_TEST_BAR:
        x = m.get(name)
        if x is None:
            fails.append(f"{name}: not measured - the machine has not finished looking")
            continue
        if kind == "at_most" and x > thr:
            fails.append(f"{name}={x:.3f} > {thr} - {why}")
        elif kind == "at_least" and x < thr:
            fails.append(f"{name}={x:.3f} < {thr} - {why}")
        elif kind == "band" and not (thr[0] <= x <= thr[1]):
            fails.append(f"{name}={x:.3f} outside {thr} - {why}")
    return (not fails), fails
