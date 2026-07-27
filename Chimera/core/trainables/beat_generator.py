"""beat_generator — optimal sleepwalker beat configuration as a trainable domain.

ELEMENTS: actions, expects, timing, features
PRINCIPLES: maximize pass rate, minimize false positives, cover feature space
MEASURE: beat pass rate, feature coverage, execution time
"""

from __future__ import annotations
import copy, math, random

EVAL_SEED = 531
N_BEATS = 12
N_RUNS = 20

ACTIONS = ["wait", "reset_position", "interact", "drop", "screenshot", "key_down", "key_up"]
EXPECTS = ["is_pie", "pawn_class", "actor_exists", "log_contains", "pawn_within", "pawn_property_toggles", "world_is"]
FEATURES = ["Verb_Look", "Verb_Bend", "Verb_PickUp", "Verb_Drop", "Verb_Shovel", "NPC_Basic_Model", "Social_Conflict",
            "Tool_Weapon_Model", "Ground_Sand_Surface", "Player_Character_Suit", "System_Sacrifice"]

def seed(rng=None):
    rng = rng or random.Random()
    beats = []
    for _ in range(N_BEATS):
        beats.append({
            "settle_s": rng.uniform(1, 8),
            "n_actions": rng.randint(1, 6),
            "action_mix": rng.sample(ACTIONS, rng.randint(1, len(ACTIONS))),
            "n_expects": rng.randint(1, 5),
            "expect_mix": rng.sample(EXPECTS, rng.randint(1, len(EXPECTS))),
            "features_tagged": rng.sample(FEATURES, rng.randint(1, min(4, len(FEATURES)))),
        })
    return {"beats": beats}

def mutate(g, rng=None):
    rng = rng or random.Random()
    g = copy.deepcopy(g)
    for b in g["beats"]:
        if rng.random() < 0.3:
            b["settle_s"] = max(1, b["settle_s"] + rng.uniform(-2, 2))
        if rng.random() < 0.2:
            b["n_actions"] = max(1, min(8, b["n_actions"] + rng.choice([-1, 1])))
        if rng.random() < 0.2:
            b["n_expects"] = max(1, min(6, b["n_expects"] + rng.choice([-1, 1])))
        if rng.random() < 0.2 and FEATURES:
            b["features_tagged"] = rng.sample(FEATURES, rng.randint(1, min(4, len(FEATURES))))
    return g

def measure(g):
    rng = random.Random(EVAL_SEED)
    # Simulate beat execution: each beat has a probability of passing based on its composition
    passes = []
    coverage = set()
    times = []
    for beat in g["beats"]:
        # Simpler beats with fewer expects pass more often
        complexity = beat["n_expects"] / 6.0 + beat["n_actions"] / 8.0
        base_pass = 0.85 - complexity * 0.4
        pass_rate = base_pass + rng.uniform(-0.15, 0.15)
        for _ in range(N_RUNS // N_BEATS):
            passes.append(1 if rng.random() < pass_rate else 0)
            for f in beat.get("features_tagged", []):
                coverage.add(f)
        times.append(beat["settle_s"] + beat["n_actions"] * 1.5)

    def _mean(v): return sum(v) / len(v) if v else 0
    return {
        "pass_rate": _mean(passes),
        "feature_coverage": len(coverage) / len(FEATURES),
        "mean_beat_time": _mean(times),
        "total_test_time": sum(times),
        "genome_summary": {"n_beats": len(g["beats"]), "coverage": len(coverage)},
    }
