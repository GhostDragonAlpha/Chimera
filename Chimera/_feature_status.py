#!/usr/bin/env python
"""Quick feature status report."""

from core.graphify_interface import load_dna_graph
import json

nodes = load_dna_graph().get("nodes", [])

# Get latest FeatureUpdate per feature name
features = {}
for n in nodes:
    if n.get("type") == "FeatureUpdate":
        name = n.get("feature_name", "")
        ts = n.get("timestamp", "")
        if name and (name not in features or ts > features[name].get("timestamp", "")):
            features[name] = n

print(f"Total unique features: {len(features)}")
print()

# Group by status and loop
from collections import defaultdict

by_status = defaultdict(list)
for name, f in sorted(features.items()):
    by_status[f.get("status", "unknown")].append((f.get("loop", 0), name))

for status in sorted(by_status.keys()):
    items = sorted(by_status[status], key=lambda x: (x[0], -len(x[1])))
    print(f"\n{status}: {len(items)} features")
    for loop, name in items[:20]:  # Show first 20 per status
        print(f"  Loop {loop}: {name}")
