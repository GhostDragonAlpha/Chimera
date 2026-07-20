"""npc_behavior — NPC social state machine as a trainable domain.

CWM rung: Other Dots (Loop 5). Design Law 3: wordless. Design Law 1: embodied.

ELEMENTS:
  - NPC_ROLES: trader, pirate, stranger, drifter, merchant, quiet, wanderer, seeker
  - GESTURES: 8 social verb slots (offer, request, threaten, greet, ignore, follow, flee, share)
  - STATES: idle, approaching, interacting, fleeing, trading, remembering

PRINCIPLES:
  - Proximity governs attention (an NPC far away ignores the player)
  - Reputation accumulates across gestures (a threatened NPC remembers)
  - Reciprocity: positive gestures increase chance of positive response
  - Persistence: nothing observed is lost (Design Law 4)

THE STATE MACHINE:
  IDLE → APPROACHING (player within range) → INTERACTING (gesture received) →
  RESPONDING (NPC picks response gesture) → REMEMBERING (state stored) → IDLE

MEASURABLE PHYSICS:
  - engagement_rate: fraction of approaches that lead to interaction
  - response_diversity: distinct gestures used across population
  - reciprocity_index: positive gestures → positive responses correlation
  - memory_fidelity: does NPC state persist across encounters?
  - conflict_emergence: do pirate/stranger roles produce more negative interactions?
  - role_discrimination: can an observer tell roles apart from behavior alone?
"""

from __future__ import annotations

import copy, math, random

EVAL_SEED = 137
N_ENCOUNTERS = 400
N_NPCS = 40
MAX_DISTANCE = 80.0

ROLES = ["trader", "pirate", "stranger", "drifter", "merchant", "quiet", "wanderer", "seeker"]
GESTURES = ["offer", "request", "threaten", "greet", "ignore", "follow", "flee", "share"]
GESTURE_VALENCE = {
    "offer": 1.0, "request": 0.3, "threaten": -1.0, "greet": 0.5,
    "ignore": -0.2, "follow": 0.2, "flee": -0.8, "share": 0.8,
}


def seed(rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()
    return {
        "approach_radius": rng.uniform(5.0, 40.0),
        "interact_radius": rng.uniform(1.0, 10.0),
        "memory_decay": rng.uniform(0.0, 0.5),
        "reciprocity_strength": rng.uniform(0.0, 0.8),
        "role_affinity": {role: {gesture: rng.uniform(-1, 1) for gesture in GESTURES} for role in ROLES},
        "pirate_aggression": rng.uniform(0.2, 0.9),
        "trader_generosity": rng.uniform(0.1, 0.7),
        "quiet_avoidance": rng.uniform(0.3, 0.9),
        "response_delay": rng.uniform(0.0, 3.0),
        "persistence_threshold": rng.uniform(0.0, 0.6),
    }


def mutate(genome: dict, rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()
    g = copy.deepcopy(genome)
    for k in ["approach_radius", "interact_radius", "memory_decay", "reciprocity_strength",
              "pirate_aggression", "trader_generosity", "quiet_avoidance", "response_delay", "persistence_threshold"]:
        if rng.random() < 0.5:
            g[k] = max(0.001, g[k] * math.exp(rng.uniform(-0.2, 0.2)))
    for role in ROLES:
        for gesture in GESTURES:
            if rng.random() < 0.3:
                g["role_affinity"][role][gesture] = max(-1, min(1, g["role_affinity"][role][gesture] + rng.uniform(-0.2, 0.2)))
    g["approach_radius"] = max(g["approach_radius"], g["interact_radius"] + 1.0)
    return g


class _NPC:
    def __init__(self, role: str, genome: dict, rng: random.Random):
        self.role = role
        self.genome = genome
        self.rng = rng
        self.state = "IDLE"
        self.memory: dict[str, float] = {}
        self.position = rng.uniform(0, MAX_DISTANCE)
        self.last_gesture: str | None = None

    def step(self, player_distance: float, player_gesture: str | None) -> str:
        g = self.genome
        if player_distance <= g["interact_radius"] and player_gesture:
            self.state = "INTERACTING"
            self.last_gesture = player_gesture
            response = self._pick_response(player_gesture)
            self.memory[player_gesture] = self.memory.get(player_gesture, 0) + 1
            self.state = "REMEMBERING"
            return response
        elif player_distance <= g["approach_radius"]:
            self.state = "APPROACHING"
            return "wait"
        else:
            self.state = "IDLE"
            return "none"

    def _pick_response(self, gesture: str) -> str:
        g = self.genome
        scores = {}
        for resp in GESTURES:
            base = g["role_affinity"][self.role].get(resp, 0)
            reciprocity = g["reciprocity_strength"] * GESTURE_VALENCE.get(gesture, 0)
            noise = self.rng.uniform(-0.3, 0.3)
            scores[resp] = base + reciprocity + noise
        if self.role == "pirate":
            scores["threaten"] += g["pirate_aggression"]
        elif self.role == "quiet":
            scores["flee"] += g["quiet_avoidance"]
        elif self.role == "trader":
            scores["offer"] += g["trader_generosity"]
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "ignore"


def measure(genome: dict) -> dict:
    rng = random.Random(EVAL_SEED)
    npcs = [_NPC(rng.choice(ROLES), genome, rng) for _ in range(N_NPCS)]

    engagements, responses, reciprocities = [], [], []
    role_responses = {r: [] for r in ROLES}
    memories = []

    for _ in range(N_ENCOUNTERS):
        npc = rng.choice(npcs)
        # Simulate player APPROACHING: start far, walk toward NPC
        dist = rng.uniform(0, genome["approach_radius"] * 1.5)
        gesture = rng.choice(GESTURES) if dist < genome["interact_radius"] and rng.random() < 0.7 else None
        if dist > genome["approach_radius"]:
            gesture = None  # too far to gesture
        response = npc.step(dist, gesture)
        if response not in ("none", "wait"):
            engagements.append(1)
            responses.append(response)
            role_responses[npc.role].append(response)
            if gesture:
                reciprocities.append(1 if GESTURE_VALENCE.get(response, 0) * GESTURE_VALENCE.get(gesture, 0) > 0 else 0)
        memories.append(len(npc.memory))

    def _mean(v): return sum(v) / len(v) if v else 0
    def _diversity(vals): return len(set(vals)) / max(1, len(vals))

    return {
        "engagement_rate": sum(engagements) / max(1, N_ENCOUNTERS),
        "response_diversity": _diversity(responses),
        "reciprocity_index": _mean(reciprocities),
        "memory_depth": _mean(memories),
        "pirate_aggression_measured": len([r for r in role_responses.get("pirate", []) if r == "threaten"]) / max(1, len(role_responses.get("pirate", []))),
        "trader_generosity_measured": len([r for r in role_responses.get("trader", []) if r == "offer"]) / max(1, len(role_responses.get("trader", []))),
        "quiet_avoidance_measured": len([r for r in role_responses.get("quiet", []) if r == "flee"]) / max(1, len(role_responses.get("quiet", []))),
        "pirate_response_spread": _diversity(role_responses.get("pirate", [])),
        "trader_response_spread": _diversity(role_responses.get("trader", [])),
        "quiet_response_spread": _diversity(role_responses.get("quiet", [])),
        "role_response_diversity": {r: _diversity(v) for r, v in role_responses.items()},
        "genome_summary": {
            "approach_radius": genome["approach_radius"],
            "reciprocity": genome["reciprocity_strength"],
            "roles": len(ROLES),
        },
    }
