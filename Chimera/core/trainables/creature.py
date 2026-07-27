"""creature — the terrarium body plan, as a trainable domain.

Exists to prove the trainer is GENERIC. Same core.trainer, same constraint format,
same optimiser — one domain is a market simulation and the other is a 3D skeleton,
and the trainer knows nothing about either.

It reports FACTS about a body. What makes a body GOOD lives in
docs/objectives/creature.json, written by the LLM.
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict

from core.terrarium import Genome, grow
from core.terrarium import mutate as _tmutate
from core.evolve import _hull, _margin, _area, _symmetry

EVAL_SEED = 7          # fixed: the same body every time, so fitness is not noisy


def seed() -> dict:
    return asdict(Genome.quadruped())


def mutate(g: dict, rng: random.Random) -> dict:
    return asdict(_tmutate(Genome(**g), rng))


def measure(g: dict) -> dict:
    bones = grow(Genome(**g), EVAL_SEED)
    dead = {"stands": 0.0, "tip_deg": 0.0, "height": 0.0, "base": 0.0,
            "symmetry": 0.0, "volume": 9.9, "bones": float(len(bones))}
    if len(bones) < 5:
        return dead

    lengths = [math.dist(b.p0, b.p1) for b in bones]
    total = sum(lengths)
    if total < 1e-6:
        return dead
    s = 1.0 / total                                   # scale-normalise: no winning by bigness

    ends = [b.p0 for b in bones] + [b.p1 for b in bones]
    zmin = min(p[2] for p in ends)
    contacts = [(round(p[0] * s, 6), round(p[1] * s, 6))
                for p in ends if p[2] <= zmin + 0.04 * total]
    hull = _hull(contacts)
    if len(hull) < 3 or _area(hull) < 1e-6:
        return dead                                   # no base to stand on

    wsum = cx = cy = cz = 0.0
    for b, ln in zip(bones, lengths):
        r = (b.r0 + b.r1) * 0.5
        w = max(1e-9, math.pi * r * r * ln)
        cx += w * (b.p0[0] + b.p1[0]) * 0.5
        cy += w * (b.p0[1] + b.p1[1]) * 0.5
        cz += w * (b.p0[2] + b.p1[2]) * 0.5
        wsum += w
    cx, cy, cz = cx / wsum, cy / wsum, cz / wsum

    marg = _margin(hull, (cx * s, cy * s))
    if marg <= 0.0:
        return dead                                   # centre of gravity outside the base

    height = (cz - zmin) * s
    return {
        "stands": 1.0,
        "tip_deg": math.degrees(math.atan2(marg, max(height, 1e-9))),
        "height": height,
        "base": math.sqrt(_area(hull)),
        "symmetry": _symmetry(bones, cx, s),
        "volume": wsum / (total ** 3),
        "bones": float(len(bones)),
    }
