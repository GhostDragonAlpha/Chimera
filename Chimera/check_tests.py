import json
from core.graphify_interface import graphify_query, load_dna_graph

# Health check
health = graphify_query("health")
print(f"Health: {health}")

# Check features related to the tests or the specific DSL blocks from tests
dna = load_dna_graph()
nodes = dna.get("nodes", [])

features = [n for n in nodes if n.get("type") == "FeatureUpdate"]
test_features = [f for f in features if any(kw in str(f.get('name', '')).lower() or kw in str(f.get('dsl_block', '')).lower() for kw in ['buytitanium', 'quantumtravel', 'missiondelivery', 'trade_route'])]
print(f"\nTest-related features: {len(test_features)}")
for f in test_features[:3]:  # Print first 3
    print(json.dumps(f, indent=2)[:500])

# Check for any pathway related to these tests
pathways = [n for n in nodes if n.get('type') in ('Pathway', 'pathway_attempt')]
test_pathways = [p for p in pathways if any(kw in str(p).lower() for kw in ['buy', 'commodity', 'quantum', 'travel', 'mission', 'delivery'])]
print(f"\nTest-related pathways: {len(test_pathways)}")
