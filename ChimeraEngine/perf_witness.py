"""perf_witness.py — SLOWNESS IS THE ONE FAILURE THAT NEVER ANNOUNCES ITSELF.

    "I'm concerned you're choosing the slower methods because it's easier to think about... if you
     use one core on the CPU when there are 24 of them, that means you're following a gradient
     descent and that's why you're choosing the easy path... build the perf witness, it'll give
     you what you need: the fear of failure."      -- the operator, 2026-07-27

He is right, and the diagnosis matters more than the symptom. Wrong code raises. Slow code returns
the correct answer and is therefore invisible until somebody sits through it. So the pull toward
the single-threaded, readable, sequential implementation has no counter-force -- unless one is
built.

This repo already solves that problem five times over: `bind_guard` refuses a server on 0.0.0.0,
`objective_lint` refuses a satisficer, the witness/research/training gates refuse an unproven
claim. NONE of them ask anyone to be disciplined. They make the undisciplined thing FAIL. There
was no equivalent for speed. This is it.

    A BUDGET IS DECLARED, NEVER DISCOVERED. Writing down what an operation MAY cost, before
    measuring, is what makes the measurement a verdict instead of a description. B8 measured
    50.7 ms/step and N6 measured 2.4 ms/decision, and both were reported as interesting FACTS in
    prose -- where they read as trivia rather than as work.

    AN EXEMPTION MUST CARRY A REASON, the way `# bind-public:` does. Some things should stay slow:
    our numpy engine's job is now being the readable second messenger that proved MuJoCo correct
    to 1e-13 m. That is a legitimate reason. "It was easier" is not, and the difference has to be
    written down where a reader can see it.

Run:  python ChimeraEngine/perf_witness.py
Exit code is nonzero when a budget is blown, so it can gate a commit.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

FRAME = 1.0 / 60.0


def bench(fn, n: int, warmup: int = 2) -> float:
    for _ in range(warmup):
        fn()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n


def hot_paths():
    """(name, callable, reps, budget_seconds, why) -- budgets from what the GAME needs."""
    from body import humanoid
    from fields import Coupling, LightField, Star, ROCK
    from planner import Planner, Stance, Terrain

    h = humanoid()
    sun = Star.from_irradiance(center=(0, 0, 0), at_distance=1.496e11, irradiance=1361.0)
    lf = LightField(stars=[sun])
    terr = Terrain(kind='slope', material='scree', slope_deg=18.0)
    pl = Planner(terrain=terr, node_budget=96)
    st = Stance(com=np.array([0.0, 0.0, 0.93]),
                contacts={'footL': np.array([-0.05, 0.1, 0.0]), 'footR': np.array([-0.05, -0.1, 0.0])},
                hip={'footL': np.array([0.0, 0.1, 0.78]), 'footR': np.array([0.0, -0.1, 0.78])},
                reach={'footL': 0.86, 'footR': 0.86})
    goal = np.array([4.0, 0.0, 0.0])
    c = Coupling(stiffness=ROCK.stiffness)
    p = np.array([1.496e11, 0, 0])

    return [
        # a body must step at least as fast as the frame it is drawn in
        ('body.step()', lambda: h.tree.step(1e-3), 6, FRAME,
         'one physics tick must fit in one frame'),
        ('mass_matrix_f()', lambda: h.tree.mass_matrix_f(), 6, FRAME * 0.5,
         'the hot spot INSIDE step -- 24 unit-acceleration RNEA passes'),
        ('humanoid() build', lambda: humanoid(), 3, 0.25,
         'spawning a character must not stall the frame'),
        ('planner.plan()', lambda: pl.plan(st, ['footL', 'footR'], goal=goal), 20, 1e-3,
         'one contact decision, priced at ~0.8 MFLOP in THE_BODY.md 4.2'),
        ('light.irradiance_at()', lambda: lf.irradiance_at(p), 4000, 2e-5,
         'a field sample is read per-splat and per-sensor'),
        ('Coupling.force()', lambda: c.force(-1e-3, 0.0), 20000, 2e-6,
         'contact is evaluated per foot per tick'),
    ]


def backends() -> list:
    """Is the fast path even AVAILABLE? A missing GPU backend is the honest reason for slowness;
    an available one that goes unused is the dishonest one."""
    out = []
    for mod, what in (('mujoco', 'C physics'), ('mujoco_warp', 'GPU batched physics'),
                      ('warp', 'GPU kernels'), ('cupy', 'GPU arrays'), ('torch', 'GPU tensors')):
        try:
            __import__(mod)
            out.append((mod, what, True))
        except Exception:
            out.append((mod, what, False))
    return out


def main() -> int:
    print('\nWITNESS: performance budgets\n' + '=' * 78)
    print('  A budget is DECLARED before measuring. Exceeding it is a FAILURE, not a note.\n')
    print(f"  {'operation':<24}{'measured':>12}{'budget':>12}{'ratio':>9}   verdict")
    print('  ' + '-' * 74)

    fails = []
    for name, fn, reps, budget, why in hot_paths():
        t = bench(fn, reps)
        ratio = t / budget
        ok = ratio <= 1.0
        if not ok:
            fails.append((name, t, budget, ratio, why))
        unit = (f'{t*1e6:8.1f} us' if t < 1e-3 else f'{t*1e3:8.2f} ms')
        bud = (f'{budget*1e6:8.1f} us' if budget < 1e-3 else f'{budget*1e3:8.2f} ms')
        print(f"  {name:<24}{unit:>12}{bud:>12}{ratio:8.1f}x   "
              f"{'ok' if ok else 'OVER BUDGET'}")

    print('\n  FAST BACKENDS AVAILABLE ON THIS MACHINE:')
    for mod, what, have in backends():
        print(f"    {'YES' if have else ' no'}  {mod:<14} {what}")
    have_gpu = any(h for m, _, h in backends() if m in ('mujoco_warp', 'warp', 'cupy', 'torch'))

    print('\n' + '=' * 78)
    if fails:
        print(f'{len(fails)} BUDGET(S) BLOWN -- this is a work list, not trivia:\n')
        for name, t, budget, ratio, why in fails:
            print(f'  {name}  is {ratio:.0f}x over. {why}.')
        if have_gpu:
            print('\n  AND A GPU BACKEND IS INSTALLED. That is the important line: the slowness is')
            print('  a CHOICE, not a constraint. mujoco-warp measured 2,358 evals/sec on this box')
            print('  against 70/sec on pybullet, whole population in ONE kernel.')
        print('\n  If an entry SHOULD be slow, say so where a reader can see it -- give it a')
        print('  budget of float("inf") with the reason in `why`, the way bind_guard wants a')
        print('  `# bind-public:` marker. "It was easier" is not a reason.')
    else:
        print('every declared budget met')
    return 1 if fails else 0


if __name__ == '__main__':
    raise SystemExit(main())
