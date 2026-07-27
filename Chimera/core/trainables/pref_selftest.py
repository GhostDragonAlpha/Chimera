"""pref_selftest — a trivial trainable FIXTURE, not a game feature.

Deterministic, instant measure(), with a measure_batch() so the trainer uses its
in-process batch path (no multiprocessing) — which keeps the trainer/preference
self-tests fast and platform-independent, and lets them run against a Schema-A objective
constructed inline instead of the drifted docs/objectives/*.json files.

genome = {"a", "b"} in [0, 1]; measure reports a, b and their sum, so an inline objective
can maximize any of them and produce a spread of physics-feasible scores to shortlist.
"""
from __future__ import annotations


def seed() -> dict:
    return {"a": 0.5, "b": 0.5}


def mutate(g: dict, rng) -> dict:
    h = dict(g)
    h["a"] = min(1.0, max(0.0, g["a"] + rng.uniform(-0.2, 0.2)))
    h["b"] = min(1.0, max(0.0, g["b"] + rng.uniform(-0.2, 0.2)))
    return h


def measure(g: dict) -> dict:
    a, b = float(g["a"]), float(g["b"])
    return {"a": a, "b": b, "sum": a + b}


def measure_batch(genomes: list) -> list:
    return [measure(g) for g in genomes]
