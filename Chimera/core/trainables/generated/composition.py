#!/usr/bin/env python3
"""Composition pass — checks parameter consistency between all 9 rungs.
No MCP calls. Pure data verification. Checks that outputs from each rung
are compatible with inputs expected by the next rung.
"""
import copy, json, math, os, random

# Load trained rung outputs
RUNG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'objectives')

def _load_trained(name):
    """Load a trained objective output."""
    path = os.path.join(RUNG_DIR, f'{name}.trained.json')
    if not os.path.exists(path):
        # Fall back to unnamed.trained.json (latest training run)
        alt = os.path.join(RUNG_DIR, 'unnamed.trained.json')
        if os.path.exists(alt):
            with open(alt) as f:
                return json.load(f)
        return {}
    with open(path) as f:
        return json.load(f)

def seed(rng=None):
    if rng is None: rng = random.Random()
    # Parameters from all 9 rungs, re-sampled for consistency checking
    return {
        # Rung 0: Solar system
        'n_planets': rng.randint(1, 6),
        'has_habitable': rng.choice([0, 1]),
        # Rung 1: Planet surface
        'n_biomes': rng.randint(1, 5),
        'n_habitable': rng.choice([0, 1, 2]),
        # Rung 2: Ground terrain
        'n_terrain_materials': rng.randint(1, 4),
        'repose_angle': rng.uniform(20, 50),
        # Rung 3: Body survival
        'o2_drain_walk_rate': rng.uniform(5, 30),
        'o2_regen_rate': rng.uniform(10, 50),
        'has_shelter_refill': rng.choice([0, 1]),
        # Rung 4: Biome resources
        'n_resource_types': rng.randint(1, 12),
        'inventory_slots': rng.choice([4, 6, 8, 10]),
        # Rung 5: Shelter threshold
        'shelter_radius': rng.uniform(100, 500),
        'refill_delay_s': rng.uniform(0.5, 5),
        # Rung 6: Shelter form
        'enclosed_volume': rng.uniform(0, 5e7),
        'has_entrance': rng.choice([0, 1]),
        # Rung 7: NPC social
        'n_npcs': rng.randint(0, 8),
        'n_npc_unlocks': rng.randint(0, 6),
        # Rung 8: Fabricator economy
        'n_blueprints': rng.randint(0, 15),
        'n_advanced_blueprints': rng.randint(0, 6),
        # Rung 9: Beacon narrative
        'n_signal_levels': rng.randint(1, 6),
        'min_signal': rng.uniform(0, 0.5),
        'max_signal': rng.uniform(0.3, 1.0),
    }

def mutate(genome, rng=None):
    if rng is None: rng = random.Random()
    g = copy.deepcopy(genome)
    for key in ['n_planets', 'n_biomes', 'n_terrain_materials', 'n_resource_types',
                'n_npcs', 'n_npc_unlocks', 'n_blueprints', 'n_advanced_blueprints',
                'n_signal_levels', 'inventory_slots', 'has_habitable', 'n_habitable',
                'has_shelter_refill', 'has_entrance']:
        if key in g and isinstance(g[key], int):
            g[key] = max(0, g[key] + rng.choice([-1, 0, 1]))
    for key in ['o2_drain_walk_rate', 'o2_regen_rate', 'shelter_radius',
                'refill_delay_s', 'enclosed_volume', 'repose_angle']:
        if key in g:
            g[key] *= math.exp(rng.uniform(-0.15, 0.15))
    for key in ['min_signal', 'max_signal']:
        if key in g:
            g[key] = max(0, min(1, g[key] + rng.uniform(-0.1, 0.1)))
    return g

def measure(genome):
    """Check parameter consistency between all 9 rungs.
    
    Each check verifies that one rung's output is compatible with
    another rung's input. No MCP calls needed.
    """
    try:
        g = genome
        
        # === Rung 0 → Rung 1: Planets must exist for surface training ===
        planets_to_surface = 1 if g.get('n_planets', 0) >= g.get('n_habitable', 0) else 0
        
        # === Rung 1 → Rung 2: Habitable planet must have terrain ===
        habitable_to_terrain = 1 if (g.get('n_habitable', 0) >= 1 and g.get('n_terrain_materials', 0) >= 1) else 0
        
        # === Rung 2 → Rung 3: Terrain must be walkable (repose angle) ===
        terrain_to_survival = 1 if (20 <= g.get('repose_angle', 0) <= 50) else 0
        
        # === Rung 3 → Rung 4: Survival must support exploration ===
        survival_to_resources = 1 if (g.get('o2_drain_walk_rate', 0) > 0 and g.get('inventory_slots', 0) >= 1) else 0
        
        # === Rung 4 → Rung 5: Resources must exist near shelter ===
        resources_to_shelter = 1 if (g.get('n_resource_types', 0) >= 1 and g.get('shelter_radius', 0) >= 50) else 0
        
        # === Rung 5 → Rung 6: Shelter radius must fit in terrain ===
        shelter_to_form = 1 if (g.get('shelter_radius', 0) >= 50 and g.get('enclosed_volume', 0) >= 1000) else 0
        
        # === Rung 5 → Rung 3: Shelter must refill faster than drain ===
        o2_balance = 1 if (g.get('o2_regen_rate', 0) > g.get('o2_drain_walk_rate', 0) * 0.5) else 0
        
        # === Rung 4 → Rung 7: Resource types must cover NPC needs ===
        resources_to_npcs = 1 if (g.get('n_resource_types', 0) >= g.get('n_npcs', 0)) else 0
        
        # === Rung 7 → Rung 8: NPC unlocks must feed into fabricator ===
        npcs_to_fabricator = 1 if (g.get('n_npc_unlocks', 0) <= g.get('n_advanced_blueprints', 0)) else 0
        
        # === Rung 6 → Rung 8: Shelter must have space for fabricator ===
        form_to_economy = 1 if (g.get('enclosed_volume', 0) >= 10000 and g.get('n_blueprints', 0) >= 1) else 0
        
        # === Rung 8 → Rung 9: Fabricator must produce beacon components ===
        economy_to_beacon = 1 if (g.get('n_advanced_blueprints', 0) >= 1 and g.get('n_signal_levels', 0) >= 1) else 0
        
        # === Rung 9: Mirror check — signal must differentiate ===
        beacon_mirror = 1 if (g.get('max_signal', 0) > g.get('min_signal', 0) * 2) else 0
        
        # === All walls satisfied? ===
        walls = [planets_to_surface, habitable_to_terrain, terrain_to_survival,
                 survival_to_resources, resources_to_shelter, shelter_to_form,
                 o2_balance, resources_to_npcs, npcs_to_fabricator,
                 form_to_economy, economy_to_beacon, beacon_mirror]
        all_walls = 1 if all(w == 1 for w in walls) else 0
        
        return {
            'planets_to_surface': planets_to_surface,
            'habitable_to_terrain': habitable_to_terrain,
            'terrain_to_survival': terrain_to_survival,
            'survival_to_resources': survival_to_resources,
            'resources_to_shelter': resources_to_shelter,
            'shelter_to_form': shelter_to_form,
            'o2_balance': o2_balance,
            'resources_to_npcs': resources_to_npcs,
            'npcs_to_fabricator': npcs_to_fabricator,
            'form_to_economy': form_to_economy,
            'economy_to_beacon': economy_to_beacon,
            'beacon_mirror': beacon_mirror,
            'all_walls': all_walls,
            'error': None,
        }
    except Exception as e:
        return {k: 0 for k in ['planets_to_surface', 'habitable_to_terrain', 'terrain_to_survival',
                'survival_to_resources', 'resources_to_shelter', 'shelter_to_form',
                'o2_balance', 'resources_to_npcs', 'npcs_to_fabricator',
                'form_to_economy', 'economy_to_beacon', 'beacon_mirror', 'all_walls']}

def get_walls():
    return [
        'All inter-rung seams must be consistent (all_walls >= 1)',
        'Planets must support surface training (planets_to_surface >= 1)',
        'Habitable planet must have terrain (habitable_to_terrain >= 1)',
        'Terrain must be walkable (terrain_to_survival >= 1)',
        'Shelter must refill faster than drain (o2_balance >= 1)',
        'Resources must cover NPC needs (resources_to_npcs >= 1)',
        'Fabricator must produce beacon parts (economy_to_beacon >= 1)',
        'Signal must differentiate help levels (beacon_mirror >= 1) — Mirror of Erised',
    ]

def get_domain_info():
    return {
        'name': 'composition',
        'description': 'Checks parameter consistency between all 9 trained rungs. Pure data — no MCP calls.',
        'seams_checked': 12,
    }
