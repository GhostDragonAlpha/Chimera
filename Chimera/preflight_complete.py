import sys; sys.path.insert(0, r'E:\PythonChimera\Chimera')
from core.graphify_interface import graphify_query

# 1. Health
health = graphify_query("health")
print(f"HEALTH: {health['total_nodes']} nodes, {health['mutations']} mutations, {health['pathways']} pathways, {health['features']} features")

# 2. Patterns
patterns_actor = graphify_query('pattern', 'AActor')
patterns_component = graphify_query('pattern', 'UActorComponent')
print(f"PATTERNS: AActor and UActorComponent patterns available")

# 3. Mutations
mutations_brace = graphify_query('mutation', 'brace_mismatch')
print(f"MUTATIONS for brace_mismatch: {len(mutations_brace)} past bugs found")

# 4. Pathways
pathways_material = graphify_query('pathway', 'create_material')
print(f"PATHWAYS for create_material: {len(pathways_material)} existing pathways")

# 5. Campus sources
campus_eng = graphify_query('campus', 'engineering_school')
print(f"CAMPUS sources from engineering_school: {len(campus_eng.get('seed_sources', []))} seed sources with quality ratings A+/B+")

# 6. GPA trend
gpa = graphify_query("gpa", "trend")
print(f"GPA trend: {gpa['gpa']} - {gpa['trend']} over {gpa['grades_count']} grades")

# Feature ledger for Loop 0-3
features_loop0 = graphify_query('feature', 'Player_')
features_loop1 = graphify_query('feature', 'Ground_')
print(f"FEATURES: Loop 0 (Player_) - {len(features_loop0)} features | Loop 1 (Ground_) - {len(graphify_query('feature', 'Ground_'))} features")

# Print first few features from loop 0 and 1
if isinstance(features_loop0, list) and len(features_loop0) > 0:
    print("LOOP 0 FEATURES:")
    for f in features_loop0[:3]:
        if isinstance(f, dict):
            print(f" - {f.get('feature_name')}: status={f.get('status')}, loop={f.get('loop')}")

if isinstance(graphify_query('feature', 'Ground_'), list) and len(graphify_query('feature', 'Ground_')) > 0:
    g_features = graphify_query('feature', 'Ground_')
    print("LOOP 1 FEATURES:")
    for f in g_features[:3]:
        if isinstance(f, dict):
            print(f" - {f.get('feature_name')}: status={f.get('status')}, loop={f.get('loop')}")