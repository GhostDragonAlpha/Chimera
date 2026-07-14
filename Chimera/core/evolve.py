"""evolve — TRAIN the terrarium. Get the LLM out of the inner loop.

The human, 2026-07-14: "this needs to be trained like an ai model not with llm
thinking (too slow)". Correct, and the arithmetic is brutal:

    grow()                    1.2 ms
    fitness()                 ~0.3 ms
    -> one core               ~650 evaluations / second
    -> 24 cores (i9-13900K)   ~15,000 evaluations / second
    -> one hour               ~50,000,000 evaluations

    an LLM hand-tuning the grammar   ~20 edits / hour

Six orders of magnitude. Hand-tuning an L-system with a reasoning model is
training a network by moving weights with tweezers.

NOT BACKPROP — EVOLUTION. There is no gradient through `A -> F[+B]`; the genome is
a discrete grammar plus continuous parameters, which is precisely the domain
genetic algorithms exist for. "Trained like a model" here means: write a loss, run
an optimiser, get out of the way.

THE OBJECTIVE IS PHYSICS, NOT TASTE
-----------------------------------
Nothing below asks for four legs. Asking for legs would just be my aesthetic,
encoded — and a fitness function full of my opinions can only rediscover my
opinions.

It asks for something a body cannot fake:

    hold your mass HIGH, on a WIDE base, with your centre of gravity INSIDE it.

A pancake is stable and low.  A pole is high and topples.  The only structure that
scores is one that lifts a mass up on spread-out supports.

LEGS ARE NOT SPECIFIED. LEGS ARE THE ANSWER.

Everything is scale-normalised (total bone length = 1) so evolution cannot cheat by
simply growing enormous, and parsimony is charged so it cannot cheat by growing a
hairball.
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import random
import time
from dataclasses import asdict
from pathlib import Path

from core.terrarium import Genome, grow, mutate, MAX_BONES


# --- geometry helpers (pure python; microseconds) -----------------------------

def _hull(pts: list) -> list:
    """Andrew's monotone chain. Returns a CCW convex hull."""
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2:
                (ox, oy), (ax, ay) = out[-2], out[-1]
                if (ax - ox) * (p[1] - oy) - (ay - oy) * (p[0] - ox) > 0:
                    break
                out.pop()
            out.append(p)
        return out

    return half(pts)[:-1] + half(reversed(pts))[:-1]


def _margin(hull: list, p: tuple) -> float:
    """Signed distance from p to the hull boundary. Positive == inside.

    This is the whole stability criterion, and it is not negotiable by taste: a
    body whose centre of gravity falls outside its support polygon FALLS OVER."""
    best = 1e9
    n = len(hull)
    for i in range(n):
        ax, ay = hull[i]
        bx, by = hull[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        ln = math.hypot(ex, ey)
        if ln < 1e-9:
            continue
        cross = (ex * (p[1] - ay) - ey * (p[0] - ax)) / ln   # +ve = left = inside
        best = min(best, cross)
    return best


def _area(hull: list) -> float:
    a = 0.0
    n = len(hull)
    for i in range(n):
        x0, y0 = hull[i]
        x1, y1 = hull[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return abs(a) * 0.5


# --- THE LOSS ----------------------------------------------------------------

def fitness(bones: list, sym_w: float = 0.25) -> tuple:
    """(score, breakdown). Higher is better. 0.0 == it falls over or is degenerate."""
    zero = (0.0, {})
    if len(bones) < 5 or len(bones) > MAX_BONES:
        return zero

    lengths = [math.dist(b.p0, b.p1) for b in bones]
    total_len = sum(lengths)
    if total_len < 1e-6:
        return zero

    s = 1.0 / total_len                      # SCALE-NORMALISE: no winning by bigness
    ends = [b.p0 for b in bones] + [b.p1 for b in bones]
    zmin = min(p[2] for p in ends)

    # ground contacts: whatever is touching down
    tol = 0.04 / s * s                       # 4% of unit body length, in world units
    tol = 0.04 * total_len
    contacts = [((p[0] - 0) * s, (p[1] - 0) * s)
                for p in ends if p[2] <= zmin + tol]
    hull = _hull([(round(x, 6), round(y, 6)) for x, y in contacts])
    if len(hull) < 3:
        return zero                          # cannot even form a base

    area = _area(hull)
    if area < 1e-6:
        return zero                          # collinear feet: a knife edge

    # centre of mass, weighted by bone VOLUME (a fat bone is heavy)
    wsum = 0.0
    cx = cy = cz = 0.0
    for b, ln in zip(bones, lengths):
        r = (b.r0 + b.r1) * 0.5
        w = max(1e-9, math.pi * r * r * ln)
        mx = (b.p0[0] + b.p1[0]) * 0.5
        my = (b.p0[1] + b.p1[1]) * 0.5
        mz = (b.p0[2] + b.p1[2]) * 0.5
        cx += w * mx
        cy += w * my
        cz += w * mz
        wsum += w
    cx, cy, cz = cx / wsum, cy / wsum, cz / wsum

    marg = _margin(hull, (cx * s, cy * s))
    if marg <= 0.0:
        return zero                          # centre of gravity outside the base: TOPPLES

    height = (cz - zmin) * s                 # how high the mass is held
    base = math.sqrt(area)                   # how wide the stance is

    # THE TIPPING ANGLE. How far can the ground tilt before the centre of gravity
    # leaves the support polygon and the animal falls over? atan(margin / height).
    #
    # This replaced `height * base * margin`, which was maximised by a LOLLIPOP —
    # a boulder on a pole over a tripod, found by the very first run in 3 seconds.
    # Static stability alone never says "and stay up when something nudges you".
    #
    #   lollipop   height 0.49, margin 0.07  ->  tips at  7.8 deg
    #   quadruped  height 0.30, margin 0.15  ->  tips at 26.6 deg
    #
    # Now holding your mass high COSTS you the robustness you need to keep it there,
    # and the only way to have both is to spread your weight onto separated supports.
    # Which is a leg. Still nothing here says "leg".
    tip = math.atan2(marg, height)           # radians
    score = height * tip

    # bilateral symmetry: a soft PRIOR, not a requirement. Real development is
    # symmetric because it is cheap, not because symmetry is fit. Weight it low and
    # let evolution tell us whether it wants it.
    sym = _symmetry(bones, cx, s)
    score *= (1.0 - sym_w) + sym_w * sym

    # METABOLIC COST — charge by VOLUME, not by bone count. Charging per bone was
    # the other half of the lollipop exploit: one enormous bone is "1 bone", so a
    # boulder was free. Mass costs.
    vol = wsum / (total_len ** 3)            # dimensionless: material per unit body
    score /= (1.0 + 0.6 * vol + 0.004 * len(bones))

    return score, {"h": round(height, 3), "base": round(base, 3),
                   "tip_deg": round(math.degrees(tip), 1), "sym": round(sym, 2),
                   "vol": round(vol, 4), "bones": len(bones)}


def _symmetry(bones: list, cx: float, s: float) -> float:
    """0..1. Mirror every bone midpoint across the sagittal plane x=cx and see how
    well the body maps onto itself."""
    mids = [((b.p0[0] + b.p1[0]) * 0.5, (b.p0[1] + b.p1[1]) * 0.5,
             (b.p0[2] + b.p1[2]) * 0.5) for b in bones]
    if len(mids) < 2:
        return 0.0
    tot = 0.0
    for m in mids:
        mir = (2.0 * cx - m[0], m[1], m[2])
        tot += min(math.dist(mir, o) for o in mids)
    mean = (tot / len(mids)) * s
    return 1.0 / (1.0 + 12.0 * mean)


# --- the optimiser (a GA; module-level so it pickles onto the worker pool) -----

def _eval(job: tuple) -> tuple:
    gd, seed, sym_w = job
    g = Genome(**gd)
    sc, br = fitness(grow(g, seed), sym_w)
    return sc, br


def evolve(seed_genome: Genome, pop: int, gens: int, seed: int, workers: int,
           sym_w: float = 0.25, elite_frac: float = 0.10, log=print) -> tuple:
    rng = random.Random(seed)
    population = [seed_genome] + [mutate(seed_genome, rng) for _ in range(pop - 1)]
    n_elite = max(1, int(pop * elite_frac))

    best, best_score, evals = seed_genome, -1.0, 0
    t0 = time.time()

    with mp.Pool(workers) as poolp:
        for gen in range(gens):
            jobs = [(asdict(g), seed + gen, sym_w) for g in population]
            results = poolp.map(_eval, jobs, chunksize=max(1, pop // (workers * 4)))
            evals += len(jobs)

            ranked = sorted(zip((r[0] for r in results), range(pop)), reverse=True)
            if ranked[0][0] > best_score:
                best_score = ranked[0][0]
                best = population[ranked[0][1]]

            if gen % max(1, gens // 12) == 0 or gen == gens - 1:
                br = results[ranked[0][1]][1]
                log(f"  gen {gen:>4}  best {ranked[0][0]:.5f}  {br}")

            # tournament selection + elitism
            elites = [population[i] for _, i in ranked[:n_elite]]
            nxt = list(elites)
            while len(nxt) < pop:
                a = rng.randrange(pop)
                b = rng.randrange(pop)
                winner = population[a] if results[a][0] >= results[b][0] \
                    else population[b]
                nxt.append(mutate(winner, rng))
            population = nxt

    dt = time.time() - t0
    return best, best_score, evals, dt


def _main() -> int:
    ap = argparse.ArgumentParser(
        prog="python -m core.evolve",
        description="Evolve a body that can stand. Legs are not specified.")
    ap.add_argument("--genome", default=None, help="seed genome (default: quadruped)")
    ap.add_argument("--plan", choices=["plant", "quadruped"], default="quadruped")
    ap.add_argument("--pop", type=int, default=400)
    ap.add_argument("--gens", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 2))
    ap.add_argument("--symmetry", type=float, default=0.25,
                    help="weight of the bilateral PRIOR. 0 = let it emerge or not.")
    ap.add_argument("--out", default="docs/terrarium/evolved.json")
    a = ap.parse_args()

    if a.genome:
        g0 = Genome.from_json(Path(a.genome).read_text(encoding="utf-8"))
    else:
        g0 = Genome.quadruped() if a.plan == "quadruped" else Genome()

    s0, br0 = fitness(grow(g0, a.seed), a.symmetry)
    print(f"objective: hold mass HIGH on a WIDE base with CoG INSIDE it.")
    print(f"           nothing here asks for legs.\n")
    print(f"seed fitness {s0:.5f}  {br0}")
    print(f"pop {a.pop} x gens {a.gens} = {a.pop*a.gens:,} evaluations "
          f"on {a.workers} workers\n")

    best, score, evals, dt = evolve(g0, a.pop, a.gens, a.seed, a.workers, a.symmetry)

    print(f"\n{evals:,} evaluations in {dt:.1f}s "
          f"= {evals/dt:,.0f} evals/sec")
    print(f"best fitness {score:.5f}  (seed was {s0:.5f}, "
          f"x{score/max(s0,1e-9):.1f})")

    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(best.to_json(), encoding="utf-8")
    print(f"-> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
