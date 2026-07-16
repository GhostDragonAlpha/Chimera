"""
attunement - THE AUDIO MINIGAME, as PHYSICS.

THE THESIS (the human, 2026-07-16): "the physics thing is still true and that's the
only way that gives us verifiable data... we have to create a physicalized world and
all programming and decisions will be based off of physicalization."

This is the thinnest slice that tests it, on the seed's #1 gap
(UChimeraAttunementComponent, realized 0%, gap 0.90 - THE AUDIO MINIGAME).

WHY THIS ONE. Every design-training attempt died on the same rock: evaluating a design
needs a simulator, and Chimera's simulator is Unreal at ~6 min/eval. Here THE RULES ARE
THE SIMULATOR. Attunement is wave interference, so the game IS a physics equation:
    field(t) = call(t) + counter(t)          <- superposition. That is the whole game.
    E = mean(field^2)                        <- the residual. That is the whole score.
No Unreal, no rubric, no LLM judge, ~200us per evaluation. Ground truth for free.

THE VIOLATION IS IN THE PHYSICS, NOT IN A JUDGE'S OPINION. The expectation_violator
proposed (8/10, unprompted): "Attunement requires generating an inverse-phase acoustic
wave to CANCEL the chimera's sound rather than MATCHING it." A player's assumption is
that attunement means matching - tune until you sound the same. Superposition punishes
that automatically and without being told to:
    match  (phase + 0)  -> field = 2*call -> E = 4*E0   FOUR TIMES WORSE
    invert (phase + pi) -> field = 0      -> E = 0       silence
Nobody encoded "matching is wrong". Sin(x) + sin(x) = 2sin(x) encoded it. That is the
difference between a designed punishment and a discovered one, and it is why
`punishes_naive` below is a MEASUREMENT of the expectation violation rather than a
score somebody assigned to it.

WHAT THIS BUYS: design measures become PHYSICAL. Physics gives ground truth about the
WORLD; put AGENTS of graded skill in it and you get ground truth about the DESIGN -
skill differentiation, solvability, learnability are then distances and energies, not
taste. A foot was DISCOVERED (a link that touches the ground sometimes) because contact
is physical; skill is discovered here for the same reason.

HONEST LIMITS:
- This measures whether the minigame has SKILL IN IT. It cannot measure whether a human
  enjoys it. Physics does not make fun measurable; it makes a game whose fun is carried
  by measurable things.
- Real audio has propagation delay, room reflection, doppler, noise. This is the dry
  1-D field: superposition only. Those are rungs, not lies - each is addable, and each
  should be added only when a design question needs it.
- A physical measure is not automatically a GOOD measure. "distance travelled" was
  perfectly physical and produced the 13.52-body-length fraud. The objective still has
  to be chosen (docs/objectives/*.json). Physics supplies honest facts; not their worth.

Self-contained on purpose (numpy only, no studio imports): membrane-clean, trainer-
importable, deterministic.

    python -m core.attunement demo      # prove the physics + skill differentiation
    python -m core.attunement probe --seed 3
"""
import argparse
import math
import sys

import numpy as np

SR = 8000.0        # sample rate (Hz) - well above the partials; interference is exact
DUR = 0.25         # seconds per evaluation -> 2000 samples, ~200us
N_OSC = 3          # oscillators the player's emitter has (the control budget)
EPS = 1e-12

# THE FOURIER LIMIT, and it is load-bearing twice over. In a window DUR seconds long,
# two frequencies closer than 1/DUR are indistinguishable - so 1/DUR is BOTH the width
# of the cancellation basin (how near you must tune before the physics rewards you) and
# the largest search step that carries information. It is derived, never tuned: change
# DUR and it follows. Guessing a step 15x this size made a playable design read as
# unplayable (see agent_greedy).
F_RES = 1.0 / DUR  # 4.0 Hz at DUR=0.25s

_T = np.arange(int(SR * DUR)) / SR


# ---------------------------------------------------------------------------
# the physics. This is the entire game.
# ---------------------------------------------------------------------------
def wave(partials, t=None):
    """Sum of partials -> the pressure field. partials: [(amp, freq_hz, phase), ...]"""
    t = _T if t is None else t
    y = np.zeros_like(t)
    for a, f, p in partials:
        y += a * np.sin(2.0 * math.pi * f * t + p)
    return y


def energy(y):
    """Mean-square = the physical fact everything else is derived from."""
    return float(np.mean(y * y))


def residual(call, counter, t=None):
    """SUPERPOSITION. The counter does not 'score points' against the call - the two
    pressure fields ADD, and what is left over is what you hear. No rule says the
    player wins; the arithmetic says it."""
    return energy(wave(call, t) + wave(counter, t))


# ---------------------------------------------------------------------------
# the chimera's call - the DESIGN. This is what a trainer would evolve.
# ---------------------------------------------------------------------------
def make_call(rng, n_partials=3, f_lo=80.0, f_hi=900.0):
    return [(float(rng.uniform(0.4, 1.0)),
             float(rng.uniform(f_lo, f_hi)),
             float(rng.uniform(0, 2 * math.pi))) for _ in range(n_partials)]


# ---------------------------------------------------------------------------
# agents of GRADED SKILL - the instrument that makes the design measurable
# ---------------------------------------------------------------------------
def agent_analytic(call, n_osc=N_OSC):
    """The ceiling: exact inverse. Not a heuristic - it is what the physics says
    cancellation IS. Its residual is the design's floor."""
    return [(a, f, p + math.pi) for a, f, p in call[:n_osc]]


def agent_matcher(call, n_osc=N_OSC):
    """THE NAIVE PLAYER, acting on the assumption 'attunement = match the sound'.
    Physics punishes it 4x with nobody having authored a punishment."""
    return [(a, f, p) for a, f, p in call[:n_osc]]


def _start(call, rng, n_osc, assist_hz):
    """The emitter the GAME hands the player: coarse-tuned to within +/-assist_hz of
    each partial. ASSIST IS THE DESIGN'S DIAL, and it exists because measurement
    demanded it.

    First version had none (frequency uniform over 80-900 Hz) and scored skill_gap 1.0:
    cancellation needs frequency within ~1/DUR (~4 Hz), so the basin is ~0.5% of the
    range per partial and you must hit three at once. The landscape is FLAT except at a
    needle - no gradient to climb, so listening bought nothing and the score was luck.
    A human could not play that either; it was not hard, it was undiscoverable.

    Real tuning is refinement of a coarse setting (that is what a tuning peg IS), so
    assist is not a crutch bolted on to rescue the design - it is the design. Too much
    -> trivial; too little -> luck; the optimum is found by MEASURING, not arguing.
    """
    out = []
    for (a, f, _p) in call[:n_osc]:
        out.append((float(rng.uniform(0.2, 1.0)),
                    float(f + rng.uniform(-assist_hz, assist_hz)),
                    float(rng.uniform(0, 2 * math.pi))))
    return out


def agent_random(call, rng, n_osc=N_OSC, assist_hz=0.0):
    """Flails WITH THE SAME starting help the listener gets. That is what makes
    skill_gap mean something: both start in the same place, and the only difference
    is that the listener listens. It isolates the value of the SKILL, not the assist."""
    return _start(call, rng, n_osc, assist_hz)


def agent_greedy(call, rng, n_osc=N_OSC, budget=2000, assist_hz=0.0):
    """A LEARNER, deliberately weak: it can only listen. It never sees the call's
    parameters - it proposes an emitter, hears the residual, and keeps what is quieter.
    That is the honest analogue of a player with ears, and its improvement curve is the
    learnability measure.

    THE SEARCH STEP IS DERIVED FROM THE PHYSICS, NOT TUNED. F_RES = 1/DUR is the
    Fourier limit: in a window DUR long you cannot RESOLVE two frequencies closer than
    1/DUR, so that is both the width of the cancellation basin and the largest step
    that still means anything. The first version guessed +/-60 Hz - 15x the basin - so
    the agent kicked itself out of the solution on every single step and finished at
    1.59x E0, WORSE than not playing. It reported skill_gap 1.0 and nearly convicted a
    good design of having no skill in it. Scaled to 1/DUR it reaches total silence.
    A mis-scaled instrument reads exactly like a broken world.

    One oscillator at a time (coordinate descent): perturbing all three at once means a
    good move on one is masked by bad moves on the others - and it is what tuning IS,
    one peg at a time."""
    cur = _start(call, rng, n_osc, assist_hz)
    cur_e = residual(call, cur)
    curve = [cur_e]
    step = 1.0
    for i in range(budget):
        cand = list(cur)
        j = int(rng.integers(n_osc))
        a, f, p = cur[j]
        cand[j] = (max(0.0, a + rng.normal(0, 0.10 * step)),
                   max(20.0, f + rng.normal(0, F_RES * step)),
                   p + rng.normal(0, 0.6 * step))
        e = residual(call, cand)
        if e < cur_e:
            cur, cur_e = cand, e
        curve.append(cur_e)
        step *= 0.999                      # anneal: coarse search -> fine tuning
    return cur, cur_e, curve


# ---------------------------------------------------------------------------
# THE DESIGN MEASURES - physical, derived, no judge anywhere
# ---------------------------------------------------------------------------
def measure(call, seed=0, n_osc=N_OSC, budget=300, restarts=5, assist_hz=20.0):
    """FACTS about the design (never opinions - domain/objective discipline).

    Every number is an energy ratio against E0, the call's own energy, so they are
    dimensionless and comparable across calls.

    restarts>1 because one rollout is a coin toss: the greedy learner starts from a
    random emitter, so a single run measures its luck. Keep the WORST.
    """
    rng = np.random.default_rng(seed)
    e0 = energy(wave(call))
    e_analytic = residual(call, agent_analytic(call, n_osc))
    e_match = residual(call, agent_matcher(call, n_osc))

    e_rand = float(np.mean([residual(call, agent_random(call, rng, n_osc, assist_hz))
                            for _ in range(restarts * 4)]))
    greedy_es, curves = [], []
    for _ in range(restarts):
        _, e, curve = agent_greedy(call, rng, n_osc, budget, assist_hz)
        greedy_es.append(e)
        curves.append(curve)
    e_greedy = max(greedy_es)              # WORST of N - honest, not lucky
    first = float(np.mean([c[0] for c in curves]))
    last = float(np.mean([c[-1] for c in curves]))

    return {
        # can it be solved at all? ~0 = perfectly cancellable by the exact inverse
        "solvable": e_analytic / (e0 + EPS),
        # >1 means the ASSUMED strategy (match) makes it WORSE. THE VIOLATION, MEASURED.
        "punishes_naive": e_match / (e0 + EPS),
        # is there room to be good? how far a listener gets vs flailing
        "skill_gap": e_rand / (e_greedy + EPS),
        # does listening actually pay? fraction of initial energy the learner removed
        "learnability": (first - last) / (first + EPS),
        # how close the best listener got to the physical floor
        "headroom": e_greedy / (e0 + EPS),
        "e0": e0, "e_analytic": e_analytic, "e_match": e_match,
        "e_random": e_rand, "e_greedy": e_greedy,
    }


# ---------------------------------------------------------------------------
def demo():
    print("=" * 74)
    print("ATTUNEMENT AS PHYSICS - the rules ARE the simulator")
    print("=" * 74)
    rng = np.random.default_rng(7)
    call = make_call(rng)
    e0 = energy(wave(call))
    print("\nchimera call (amp, freq_hz, phase):")
    for a, f, p in call:
        print(f"    {a:.3f}  {f:7.2f} Hz  {p:.3f} rad")
    print(f"\n  E0 (call alone) = {e0:.6f}")

    print("\n--- [1] does the PHYSICS do what physics must? (no rule authored this) ---")
    e_inv = residual(call, agent_analytic(call))
    e_mat = residual(call, agent_matcher(call))
    print(f"  INVERT (phase + pi) -> E = {e_inv:.3e}   ratio {e_inv/e0:.2e}   want ~0 (silence)")
    print(f"  MATCH  (phase + 0)  -> E = {e_mat:.6f}   ratio {e_mat/e0:.2f}x    want 4.00x")
    ok1 = e_inv / e0 < 1e-9 and abs(e_mat / e0 - 4.0) < 1e-6
    print(f"  => superposition is real: {'PASS' if ok1 else 'FAIL'}")
    print("     nobody encoded 'matching is wrong'. sin(x)+sin(x)=2sin(x) did.")

    print("\n--- [2] is the VIOLATION measurable? (not an LLM's 8/10) ---")
    m = measure(call, seed=1)
    print(f"  punishes_naive = {m['punishes_naive']:.2f}x")
    print("     the assumed mental model (match it) is punished FOURFOLD, by arithmetic.")
    print("     this is the expectation violation as a NUMBER, derived not judged.")

    print("\n--- [3] is there SKILL in it? (agents of graded skill) ---")
    print(f"  random flailing   E = {m['e_random']:.6f}   ({m['e_random']/e0:.2f}x E0)")
    print(f"  greedy listener   E = {m['e_greedy']:.6f}   ({m['headroom']:.3f}x E0)  [worst of 5]")
    print(f"  perfect inverse   E = {m['e_analytic']:.3e}   (the physical floor)")
    print(f"  skill_gap    = {m['skill_gap']:.1f}x   (listener beats flailing by this much)")
    print(f"  learnability = {m['learnability']:.3f}  (fraction of energy listening removed)")
    ok2 = m["skill_gap"] > 2.0 and m["learnability"] > 0.5
    print(f"  => the design has skill in it: {'PASS' if ok2 else 'FAIL'}")

    print("\n--- [4] what it cost ---")
    import time
    t0 = time.time()
    for _ in range(200):
        residual(call, agent_analytic(call))
    dt = (time.time() - t0) / 200
    print(f"  {dt*1e6:.0f} us per evaluation  (~{1/dt:,.0f}/sec, one core)")
    print(f"  Unreal would be ~6 min. That is ~{360/dt:,.0f}x.")

    print("\n" + "=" * 74)
    print("Physics gives ground truth about the WORLD. Agents of graded skill in that")
    print("physics give ground truth about the DESIGN. Neither needed a judge.")
    print("=" * 74)
    return 0 if (ok1 and ok2) else 1


def probe(seed):
    rng = np.random.default_rng(seed)
    call = make_call(rng)
    m = measure(call, seed=seed)
    for k in ("solvable", "punishes_naive", "skill_gap", "learnability", "headroom"):
        print(f"  {k:16s} {m[k]:.4f}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="attunement", description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo")
    pr = sub.add_parser("probe")
    pr.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    return demo() if a.cmd == "demo" else probe(a.seed)


if __name__ == "__main__":
    sys.exit(main())
