#!/usr/bin/env python3
"""Meta-feature discovery — feature list emerges from the catalog, not from authoring."""
import copy, json, math, os, random


def _load_catalog():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'docs', 'element_catalog.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("elements", [])


def seed(rng=None):
    if rng is None:
        rng = random.Random()
    catalog = _load_catalog()
    genome = {}
    idx = 0
    active = set()

    cats = [
        ("movement", ["CharacterMovement", "Input", "Pawn", "Velocity"]),
        ("survival", ["LifeSupport", "Oxygen", "Suit", "Health", "Damage"]),
        ("interaction", ["Pickup", "Interact", "Inventory", "Tool"]),
        ("social", ["NPC", "Social", "Dialogue", "Gesture", "Faction"]),
        ("economy", ["Trade", "Economy", "Market", "Currency"]),
        ("narrative", ["Quest", "Mission", "Sacrifice", "Beacon"]),
        ("environment", ["Sky", "Weather", "Terrain", "Celestial"]),
        ("physics", ["Physics", "Collision", "Gravity", "Force"]),
    ]
    for sys_name, keywords in cats:
        matches = [e for e in catalog if any(
            k.lower() in (e.get("class", "") + " " + e.get("property", "") + " " + e.get("category", "")).lower()
            for k in keywords)]
        if matches and rng.random() < 0.85:
            elem = rng.choice(matches)
            cls = elem.get("class", "X").split(".")[-1][:12]
            prop = elem.get("property", "x")[:12]
            genome[f"f{idx}_{cls}_{prop}"] = rng.uniform(0.0, 1.0)
            active.add(sys_name)
            idx += 1

    for s in active:
        genome[f"s_{s}"] = 1
    genome["n_features"] = idx
    genome["n_systems"] = len(active)
    return genome


def mutate(genome, rng=None):
    if rng is None:
        rng = random.Random()
    g = copy.deepcopy(genome)
    for key in list(g.keys()):
        if key.startswith("f"):
            if rng.random() < 0.2:
                g[key] = max(0.0, min(1.0, g[key] * math.exp(rng.uniform(-0.3, 0.3))))
    return g


def _classify_features(genome):
    systems = {k: 0 for k in ["movement", "survival", "interaction", "social",
                                "economy", "narrative", "environment", "physics"]}
    for key in genome:
        if key.startswith("s_"):
            sys_name = key[2:]
            if sys_name in systems:
                systems[sys_name] = int(genome[key])
    return systems, {k: v for k, v in genome.items()
                     if not k.startswith("s_") and k not in ("n_features", "n_systems")}


def measure(genome):
    try:
        systems, features = _classify_features(genome)
        n_features = len(features)
        n_systems = sum(1 for v in systems.values() if v > 0)

        has_movement = systems.get("movement", 0) > 0
        has_survival = systems.get("survival", 0) > 0
        has_interaction = systems.get("interaction", 0) > 0
        has_narrative = systems.get("narrative", 0) > 0
        has_social = systems.get("social", 0) > 0
        has_economy = systems.get("economy", 0) > 0
        has_environment = systems.get("environment", 0) > 0
        has_physics = systems.get("physics", 0) > 0

        completable = 1 if (has_movement and has_survival and has_interaction and has_narrative) else 0
        mirror_viable = 1 if (has_social and has_economy and has_narrative) else 0
        diversity = n_systems / 8.0 if n_systems > 0 else 0.0

        surprises = 0
        if has_physics and has_social:
            surprises += 1
        if has_environment and has_economy:
            surprises += 1
        if has_physics and has_narrative:
            surprises += 1

        return {
            "n_features": n_features,
            "n_systems": n_systems,
            "completable": completable,
            "mirror_viable": mirror_viable,
            "diversity": diversity,
            "surprises": surprises,
            "has_movement": 1 if has_movement else 0,
            "has_survival": 1 if has_survival else 0,
            "has_interaction": 1 if has_interaction else 0,
            "has_social": 1 if has_social else 0,
            "has_economy": 1 if has_economy else 0,
            "has_narrative": 1 if has_narrative else 0,
            "has_environment": 1 if has_environment else 0,
            "has_physics": 1 if has_physics else 0,
        }
    except Exception as e:
        return {k: 0 for k in ["n_features", "n_systems", "completable", "mirror_viable",
                                "surprises", "has_movement", "has_survival", "has_interaction",
                                "has_social", "has_economy", "has_narrative", "has_environment",
                                "has_physics"]} | {"diversity": 0.0}


def get_walls():
    return [
        "Game must be completable: movement + survival + interaction + narrative (completable >= 1)",
        "Mirror must be viable: social + economy + narrative (mirror_viable >= 1)",
        "At least 3 systems must have features (n_systems >= 3)",
    ]


def get_domain_info():
    return {
        "name": "meta_feature_discovery",
        "description": "Feature list emerges from the 69,749-element catalog. No pre-authored rungs.",
        "catalog_size": 69749,
        "samples_per_genome": "~8-16",
    }
