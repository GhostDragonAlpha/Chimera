#!/usr/bin/env python
"""Get detailed status of needs_refinement features."""

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

# Filter to needs_refinement only
for name, f in sorted(features.items()):
    if f.get("status") == "needs_refinement":
        print(f"\n{name} (Loop {f.get('loop')}):")
        params = f.get("parameters", {})
        for k, v in params.items():
            val_str = str(v)[:200].encode("ascii", "ignore").decode()
