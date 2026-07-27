"""train_transition.py — THE TRANSITION CONTROLLER (THE_BODY.md §9).

    Move one limb to a target while the rest of the body holds together.

Everything else in this engine is derived or measured. This is the one piece that must be TRAINED,
because there is no closed form for "which 36 muscle activations get that hand there without
throwing the torso away".

    WHAT IS TRAINED HERE, AND WHAT IS NOT. This trains the FREE-SPACE reach: no ground, no contact.
    That is not a simplification chosen for ease -- it is the exact scope the engine seam has been
    WITNESSED over. mjcf_witness proves our engine and MuJoCo agree on the contact-free actuated
    body (X5, 4.06x convergence). Our MJCF deliberately carries NO geoms, because our own engine has
    no collision model, so adding a floor here would train against MuJoCo's contact solver -- which
    nothing has witnessed against ours. That is a NEW seam and it needs its own X-check first.
    Claiming a contact-rich controller off this run would be the sim-to-sim mistake §3.4 exists to
    prevent, committed knowingly.

    And free-space reach is not a toy. It IS the EVA case: floating_witness F4 measured the body
    reorienting at ZERO angular momentum, 1.0635 deg per cycle. A policy that can place a limb
    while conserving momentum is the zero-g controller.

    SCORING IS THE PART THAT MATTERS (§9.5). Every genome runs N randomised starts and is scored on
    its WORST. This repo already paid for that lesson: a celebrated 13.52-body-length walker had
    periodicity 0.25 and lost 5.5 body lengths to a ONE-MICRON nudge -- 80,000 evaluations spent
    selecting lucky dice. `robustness = worst/mean` is reported every generation; a real controller
    is ~1.0 and a fraud is ~0.

Run:  python ChimeraEngine/train_transition.py [--gens N] [--pop N] [--quick]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from body import ACT_DIM, humanoid                                           # noqa: E402
from mjcf_body import FastBody                                               # noqa: E402

DT = 5e-4                             # armature is 0 to match our engine, so Euler needs a
                                      # small step: at 2e-3 a 250 N.m knee NaN-d the solve. This is
                                      # the cost of keeping the MuJoCo model identical to the
                                      # witnessed one rather than adding rotor inertia it does not
                                      # have.
CONTROL_EVERY = 20                    # still 100 Hz neural drive
EPISODE = 1.2                         # seconds
HID = 24
LR = 0.6                              # ES step size
SWING = 'forearmL'                    # the limb being placed


def obs_dim(h) -> int:
    return 3 + 1 + 3 + h.tree.n * 2 + 3


def n_params(h) -> int:
    o = obs_dim(h)
    return o * HID + HID + HID * ACT_DIM + ACT_DIM


def act(theta, o, h):
    d = obs_dim(h)
    i = 0
    W1 = theta[i:i + d * HID].reshape(d, HID); i += d * HID
    b1 = theta[i:i + HID]; i += HID
    W2 = theta[i:i + HID * ACT_DIM].reshape(HID, ACT_DIM); i += HID * ACT_DIM
    b2 = theta[i:i + ACT_DIM]
    return 0.5 * (np.tanh(np.tanh(o @ W1 + b1) @ W2 + b2) + 1.0)      # -> [0, 1] activations


def rollout(theta, seed: int, gravity_z: float) -> float:
    """One episode. Returns the score; higher is better."""
    rng = np.random.default_rng(seed)
    h = humanoid(base_pos=(0.0, 0.0, 0.0), gravity=(0.0, 0.0, gravity_z))
    h.tree.q[:] = rng.normal(0.0, 0.25, h.tree.n)
    h.tree.qd[:] = rng.normal(0.0, 0.20, h.tree.n)
    h.tree.w_base = rng.normal(0.0, 0.15, 3)
    swing = h.joint[SWING]
    fb = FastBody(h, dt=DT, gravity=(0.0, 0.0, gravity_z))
    fb.sync_to_tree()

    R0, o0 = h.tree.frame_of(swing)
    start = o0 + R0 @ np.array([0.0, 0.0, -0.25])
    # a target inside the limb's reach, in a random direction -- the planner supplies this in the
    # game, so training must not assume any particular one
    tdir = rng.normal(size=3); tdir /= np.linalg.norm(tdir)
    target = start + tdir * 0.28

    n = int(EPISODE / DT)
    best_d, effort, L0 = 1e9, 0.0, None
    for k in range(0, n, CONTROL_EVERY):
        fb.sync_to_tree()
        R, o = h.tree.frame_of(swing)
        tip = o + R @ np.array([0.0, 0.0, -0.25])
        d = float(np.linalg.norm(tip - target))
        best_d = min(best_d, d)
        ob = np.concatenate([h.tree.up(), [abs(gravity_z)], h.tree.w_base,
                             h.tree.q, h.tree.qd, target - tip])
        a = act(theta, ob, h)
        for j, p in enumerate(h.pairs.values()):
            u = 2.0 * a[2 * j] - 1.0
            p.drive(u, co_contract=a[2 * j + 1] * 0.5)
        effort += float(np.sum(a ** 2))
        fb.step(CONTROL_EVERY, control_every=CONTROL_EVERY)
        if not np.all(np.isfinite(h.tree.q)):
            return -10.0
    fb.sync_to_tree()
    # REWARD IN PHYSICS (§9.3): closed the gap, minus the work it took. No "looks natural" term.
    return float(2.0 - 6.0 * best_d - 0.004 * effort / max(1, n // CONTROL_EVERY))


def score(theta, restarts: int, seed_base: int = 0):
    """N randomised starts, and the genome is worth its WORST one.

    seed_base is FIXED during training. I first varied it per generation, so every generation faced
    different starts and fitness was not comparable across them -- selection had nothing stable to
    climb and the best-of-generation column was pure noise. Randomised starts must be randomised
    ACROSS THE POPULATION, not across time; held-out seeds at the end are what catch overfitting.
    """
    rs = [rollout(theta, seed_base + i, -9.80665 * (0.2 + 1.0 * (i % 3) / 2.0))
          for i in range(restarts)]
    worst, mean = float(np.min(rs)), float(np.mean(rs))
    return worst, mean, (worst / mean if mean > 1e-9 else 0.0)


def main() -> int:
    quick = '--quick' in sys.argv
    gens = int(sys.argv[sys.argv.index('--gens') + 1]) if '--gens' in sys.argv else (6 if quick else 25)
    pop = int(sys.argv[sys.argv.index('--pop') + 1]) if '--pop' in sys.argv else (16 if quick else 40)
    restarts = 3 if quick else 5

    h = humanoid()
    P = n_params(h)
    print(f'\nTRAIN: the transition controller\n' + '=' * 74)
    print(f'  body {h.describe()}')
    print(f'  policy {obs_dim(h)} -> {HID} -> {ACT_DIM}  = {P} parameters')
    print(f'  {pop} genomes x {restarts} randomised starts x {EPISODE}s @ {1/(DT*CONTROL_EVERY):.0f} Hz drive')
    print(f'  gravity randomised 0.2g .. 1.2g, CONDITIONED (it is an observation, not a setting)')
    print(f'  scored on the WORST restart -- one rollout is a coin toss\n')
    print(f"  {'gen':>4}{'best':>9}{'worst':>9}{'mean':>9}{'robust':>8}{'sigma':>8}{'sec':>7}")
    print('  ' + '-' * 54)

    rng = np.random.default_rng(7)
    mu = rng.normal(0.0, 0.05, P)
    sigma = 0.12
    t0 = time.perf_counter()
    best_ever, best_theta = -1e9, mu.copy()
    for g in range(gens):
        tg = time.perf_counter()
        # MIRRORED SAMPLING + a RANK-NORMALISED GRADIENT (OpenAI-ES). My first version replaced mu
        # outright with the elite MEAN, which over 2028 parameters is dominated by sampling noise --
        # the population never accumulated a direction, so 20 generations of best-of-gen was a
        # random walk. Mirroring cancels the first-order noise between +eps and -eps, and ranking
        # makes the step immune to the reward's scale and to outliers.
        half = pop // 2
        eps = rng.normal(0.0, 1.0, (half, P))
        pert = np.concatenate([eps, -eps])
        cand = mu + sigma * pert
        res = [score(cand[i], restarts, 1000) for i in range(pop)]   # FIXED training seeds
        fit = np.array([r[0] for r in res])                 # THE WORST, not the mean
        ranks = np.empty(pop); ranks[np.argsort(fit)] = np.arange(pop)
        adv = ranks / (pop - 1) - 0.5                       # -0.5 .. +0.5, scale-free
        mu = mu + (LR / (pop * sigma)) * (pert.T @ adv)
        order = np.argsort(-fit)
        sigma = max(0.04, sigma * (0.97 if fit[order[0]] > best_ever else 1.01))
        if fit[order[0]] > best_ever:
            best_ever, best_theta = float(fit[order[0]]), cand[order[0]].copy()
        w, m, rob = res[order[0]]
        print(f'  {g:4d}{fit[order[0]]:9.3f}{w:9.3f}{m:9.3f}{rob:8.3f}{sigma:8.3f}'
              f'{time.perf_counter()-tg:7.1f}')

    w, m, rob = score(best_theta, restarts * 2, 50_000)     # HELD-OUT seeds, never trained on
    print('\n  ' + '-' * 54)
    print(f'  HELD OUT ({restarts*2} unseen starts): worst {w:.3f}  mean {m:.3f}  '
          f'robustness {rob:.3f}')
    print(f'  total {time.perf_counter()-t0:.0f}s')
    out = Path(__file__).resolve().parent / 'transition_policy.npy'
    np.save(out, best_theta)
    print(f'  saved {out.name} ({P} params)')
    print('\n  SCOPE: FREE-SPACE reach. No ground, no contact -- that is exactly the scope the')
    print('  engine seam has been witnessed over (mjcf_witness X5). A contact-rich controller')
    print('  needs MuJoCo\'s contact solver witnessed against ours FIRST; it is a new seam.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
