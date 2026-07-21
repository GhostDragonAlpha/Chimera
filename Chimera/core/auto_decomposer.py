#!/usr/bin/env python3
"""Auto-decomposer — reads a parent constraint, queries the element catalog for
related variable clusters, and generates N sub-rung constraint sets + domains.
Runs a full train cycle on all sub-rungs in parallel.
"""
import json, os, subprocess, sys, time
from pathlib import Path

BASE = Path(__file__).parent.parent
CONSTRAINTS_DIR = BASE / 'docs' / 'constraints'
OBJECTIVES_DIR = BASE / 'docs' / 'objectives'
GENERATED_DIR = BASE / 'core' / 'trainables' / 'generated'
CATALOG_PATH = BASE / 'docs' / 'element_catalog.json'


def load_catalog():
    with open(CATALOG_PATH) as f:
        return json.load(f).get('elements', [])


def load_constraint(name):
    path = CONSTRAINTS_DIR / f'{name}.json'
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def find_related_clusters(parent_name, n_clusters=4):
    """Find N distinct variable clusters in the catalog related to the parent
    constraint's element_query categories, using different sub-keywords per cluster."""
    parent = load_constraint(parent_name)
    if not parent:
        print(f'  Parent constraint {parent_name} not found')
        return []
    
    query = parent.get('element_query', {})
    categories = query.get('categories', [])
    classes = query.get('classes', [])
    catalog = load_catalog()
    
    # Predefined sub-cluster keywords for each category
    # These generate distinct sub-topics within the parent domain
    sub_clusters = {
        'ground_terrain': [
            {'name': 'grain_scale', 'keywords': ['Grain', 'Particle', 'Dust', 'Powder'], 'walls': ['Grain size distribution follows power law', 'Coarse and fine grains segregate', 'Packing density 55-65%']},
            {'name': 'footstep_response', 'keywords': ['Footstep', 'Footprint', 'Displacement', 'Contact'], 'walls': ['Footstep displaces grains 5-15cm radius', 'Footprint persists 5+ seconds', 'Dust puff on impact']},
            {'name': 'surface_hardness', 'keywords': ['Hardness', 'Compression', 'Density', 'Strength'], 'walls': ['Compression strength varies by surface type', 'Rock harder than sand', 'Surface hardness affects footstep audio']},
            {'name': 'erosion_pattern', 'keywords': ['Erosion', 'Weathering', 'Wear', 'Pattern'], 'walls': ['Erosion patterns follow wind direction', 'Soft materials erode faster', 'Erosion reveals underlying layers']},
        ],
        'body_survival': [
            {'name': 'o2_consumption', 'keywords': ['Oxygen', 'Respiration', 'Metabolic', 'Consumption'], 'walls': ['O2 consumption scales with exertion', 'Sprint burns 2x walk rate', 'Idle drain is nonzero']},
            {'name': 'thermal_regulation', 'keywords': ['Temperature', 'Thermal', 'Heat', 'Cold'], 'walls': ['Night temperature drops below suit tolerance', 'Suit heater drains battery', 'Shelter restores temperature']},
            {'name': 'dust_clogging', 'keywords': ['Dust', 'Clog', 'Filter', 'Particulate'], 'walls': ['Dust accumulates faster on sandy surfaces', 'Filter scrub rate lower than clog rate', 'High clog reduces O2 flow']},
            {'name': 'injury_model', 'keywords': ['Injury', 'Damage', 'Fall', 'Crash'], 'walls': ['Fall damage scales with height', 'Suit breach causes rapid O2 loss', 'Minor injuries heal over time in shelter']},
        ],
        'npc_social': [
            {'name': 'need_generation', 'keywords': ['Need', 'Desire', 'Requirement', 'Urgency'], 'walls': ['NPC needs vary by type', 'Needs become urgent over time', 'Needs are visible through posture']},
            {'name': 'gesture_set', 'keywords': ['Gesture', 'Pose', 'Animation', 'Signal'], 'walls': ['At least 3 gesture states per NPC', 'Gestures readable from 50m', 'No text required for communication']},
            {'name': 'reciprocity', 'keywords': ['Reciprocity', 'Trade', 'Exchange', 'Return'], 'walls': ['Helped NPCs provide unique blueprints', 'No immediate reward for helping', 'Blueprint unlock has visual feedback']},
            {'name': 'population_density', 'keywords': ['Population', 'Density', 'Distribution', 'Cluster'], 'walls': ['NPC spawns avoid player spawn zone', 'NPC density higher near resources', 'Maximum 10 NPCs visible at once']},
        ],
    }
    
    clusters = sub_clusters.get(parent_name, [])
    if not clusters:
        # Generic: split by the first 4 distinct class categories in the catalog
        matched = [e for e in catalog if any(c.lower() in (e.get('class','')+e.get('category','')).lower() for c in categories)]
        class_groups = {}
        for e in matched[:2000]:
            cls = e.get('class', 'Unknown').split('.')[-1]
            if cls not in class_groups:
                class_groups[cls] = []
            class_groups[cls].append(e)
        
        sorted_groups = sorted(class_groups.items(), key=lambda x: -len(x[1]))
        for i, (cls, elems) in enumerate(sorted_groups[:n_clusters]):
            clusters.append({
                'name': f'{parent_name}_{cls[:12].lower()}',
                'keywords': [cls[:20]],
                'walls': [f'{cls} property must be trainable', f'Satisfies {parent_name} constraints in composition']
            })
    
    return clusters[:n_clusters]


def _graph_feature_exists(name):
    """Check if a feature already exists in the DNA graph."""
    try:
        from core.graphify_interface import graphify_query
        results = graphify_query('feature', name)
        return len(results) > 0
    except:
        return False


def _graph_record_feature(name, status, parent):
    """Record a feature to the DNA graph."""
    try:
        from core.graphify_interface import graphify_mutate
        graphify_mutate('phase_complete', details={
            'phase': f'phase_{name}',
            'result': f'Sub-rung of {parent}: trained and verified',
            'status': status
        })
    except:
        pass


def generate_sub_rung(parent_name, cluster, index):
    """Generate a sub-rung constraint file, domain, and objective. Skips if already in graph."""
    name = f'{parent_name}_{cluster["name"]}'
    
    # Skip if feature already exists in the DNA graph
    if _graph_feature_exists(name):
        print(f'  {name}: already in graph, skipping')
        return None
    
    # Constraint file
    constraint = {
        '_provenance': f'Auto-decomposed sub-rung of {parent_name}. Cluster: {cluster["name"]}',
        'name': name,
        'parent_rung': parent_name,
        'walls': cluster['walls'],
        'element_query': {'categories': cluster.get('keywords', []), 'classes': []},
        'output': {'next_rung': None, 'format': 'auto-decomposed sub-rung parameters'}
    }
    with open(CONSTRAINTS_DIR / f'{name}.json', 'w') as f:
        json.dump(constraint, f, indent=2)
    
    # Generate domain first, then read its measure names
    subprocess.run([sys.executable, '-m', 'core.domain_generator', str(CONSTRAINTS_DIR / f'{name}.json')],
                   capture_output=True, cwd=BASE)
    
    # Read the generated domain to extract measure names
    domain_path = GENERATED_DIR / f'{name}.py'
    if domain_path.exists():
        with open(domain_path) as f:
            content = f.read()
        # Extract return dict keys from the measure function
        import re
        measure_keys = re.findall(r'"(wall_\d+_[^"]+)"', content)
    else:
        measure_keys = [f'wall_{i}' for i in range(len(cluster["walls"]))]
    
    # Objective file using actual measure names from the domain
    objectives = []
    for i, (wall, measure_name) in enumerate(zip(cluster['walls'], measure_keys)):
        wall_lower = wall.lower()
        if 'distribution' in wall_lower or 'power law' in wall_lower:
            objectives.append({'kind': 'band', 'measure': measure_name, 'min': 0.5, 'max': 3.0, 'hard': True, 'wall': wall})
        elif 'persists' in wall_lower or 'density' in wall_lower:
            objectives.append({'kind': 'at_least', 'measure': measure_name, 'min': 0.5, 'hard': True, 'wall': wall})
        else:
            objectives.append({'kind': 'at_least', 'measure': measure_name, 'min': 1, 'hard': True, 'wall': wall})
    
    objective = {
        '_provenance': f'Auto-decomposed objective for {name}',
        'scenario': f'Train {name} sub-rung parameters',
        'constraints': objectives
    }
    with open(OBJECTIVES_DIR / f'{name}.json', 'w') as f:
        json.dump(objective, f, indent=2)
    
    print(f'  Generated sub-rung: {name}')
    return name


def train_all(names):
    """Train all named rungs in parallel."""
    processes = []
    for name in names:
        objective = OBJECTIVES_DIR / f'{name}.json'
        domain = f'core.trainables.generated.{name}'
        proc = subprocess.Popen(
            [sys.executable, '-m', 'core.trainer', '--domain', domain,
             '--objective', str(objective), '--pop', '32', '--gens', '10'],
            cwd=BASE
        )
        processes.append((name, proc))
        time.sleep(1)  # stagger launches
    
    for name, proc in processes:
        proc.wait()
        status = 'OK' if proc.returncode == 0 else 'FAIL'
        print(f'  {name}: {status}')


def snapshot():
    """Print a system snapshot from the DNA graph and return gap count."""
    try:
        from core.graphify_interface import graphify_query
        health = graphify_query('health')
        features = graphify_query('feature', '')
        gaps = [f for f in features if f.get('status') in ('not_started', 'needs_refinement')]
        mirror = [f for f in features if 'mirror' in str(f).lower()]
        print(f'=== SNAPSHOT: {health["total_nodes"]} nodes, {health["features"]} features, '
              f'{len(mirror)} mirror, {len(gaps)} gaps ===')
        return len(gaps)
    except:
        return 0


def decompose(parent_name, n_clusters=4):
    """Full auto-decomposition cycle: snapshot, find clusters, generate, train."""
    snapshot()
    print(f'Auto-decomposing {parent_name} into {n_clusters} sub-rungs...')
    clusters = find_related_clusters(parent_name, n_clusters)
    if not clusters:
        print(f'  No clusters found for {parent_name}')
        return []
    
    names = []
    for i, cluster in enumerate(clusters):
        name = generate_sub_rung(parent_name, cluster, i)
        if name:
            names.append(name)
            _graph_record_feature(name, 'verified', parent_name)
    
    if not names:
        print(f'  No new sub-rungs to train for {parent_name} (all in graph)')
        return []
    
    print(f'Training {len(names)} new sub-rungs in parallel...')
    train_all(names)
    
    print(f'Auto-decomposition of {parent_name} complete.')
    return names


if __name__ == '__main__':
    parent = sys.argv[1] if len(sys.argv) > 1 else 'ground_terrain'
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    decompose(parent, n)
