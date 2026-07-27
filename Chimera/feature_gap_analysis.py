#!/usr/bin/env python3
"""
Feature Gap Analysis v2 - improved orphan detection.
Focuses on structured dependency extraction from is_edge questions.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

FEATURES_DIR = Path(r"E:\PythonChimera\Chimera\docs\features")

# Words that appear in question/answer text but are NOT feature references
STOP_WORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "had",
    "her", "was", "one", "our", "out", "has", "his", "how", "its", "may",
    "who", "did", "get", "got", "let", "say", "she", "too", "use", "way",
    "many", "then", "them", "these", "some", "time", "very", "when", "come",
    "could", "make", "like", "been", "call", "long", "look", "many", "most",
    "over", "such", "take", "than", "that", "them", "well", "were", "what",
    "will", "with", "work", "year", "your", "also", "back", "been", "being",
    "both", "even", "find", "give", "good", "have", "here", "high", "just",
    "keep", "know", "last", "left", "life", "line", "live", "made", "make",
    "more", "much", "must", "need", "next", "only", "open", "part", "play",
    "real", "same", "show", "side", "some", "soon", "sure", "take", "tell",
    "than", "that", "them", "time", "turn", "upon", "used", "very", "want",
    "well", "went", "what", "when", "will", "with", "work", "year", "your",
    "about", "after", "again", "being", "below", "between", "both", "came",
    "each", "from", "going", "great", "help", "into", "just", "kind", "know",
    "large", "might", "never", "often", "place", "point", "right", "small",
    "start", "still", "three", "under", "until", "using", "water", "where",
    "which", "world", "would", "write", "above", "across", "along", "among",
    "because", "before", "behind", "below", "best", "better", "beyond",
    "big", "body", "both", "brought", "build", "built", "case", "change",
    "check", "class", "clear", "close", "come", "consider", "could", "course",
    "done", "draw", "during", "early", "end", "enough", "every", "example",
    "fact", "face", "far", "feel", "few", "find", "first", "follow", "found",
    "full", "general", "given", "going", "gone", "group", "hand", "happen",
    "hard", "head", "hear", "hold", "home", "horse", "however", "hundred",
    "idea", "instead", "keep", "king", "knew", "land", "large", "later",
    "least", "let", "letter", "level", "light", "list", "little", "long",
    "look", "made", "main", "man", "map", "matter", "may", "mean", "men",
    "mind", "money", "moon", "move", "mountain", "must", "name", "near",
    "need", "new", "night", "north", "note", "nothing", "notice", "number",
    "old", "order", "page", "paper", "part", "pass", "past", "path", "pay",
    "people", "picture", "plan", "plant", "possible", "power", "problem",
    "put", "question", "quickly", "ran", "rather", "read", "rest", "river",
    "room", "run", "said", "sea", "second", "seem", "sent", "set", "short",
    "should", "since", "sit", "sleep", "small", "snow", "song", "soon",
    "sound", "south", "space", "speak", "stand", "star", "state", "stay",
    "step", "stone", "story", "street", "study", "sun", "system", "table",
    "talk", "teacher", "tell", "thought", "through", "together", "toward",
    "tree", "tried", "turn", "unit", "upon", "voice", "walk", "wall",
    "wanted", "warm", "watch", "wave", "week", "weight", "west", "white",
    "whole", "whose", "wide", "within", "without", "wood", "word", "work",
    "young", "thing", "another", "area", "around", "away", "black", "blue",
    "body", "book", "box", "brown", "car", "catch", "central", "city",
    "color", "complete", "contain", "copy", "correct", "couple", "cross",
    "dark", "data", "deep", "define", "detail", "different", "direct",
    "draw", "drive", "earth", "east", "edge", "energy", "engine", "error",
    "event", "evidence", "exist", "experience", "eye", "face", "feature",
    "field", "figure", "fire", "food", "form", "future", "game", "ground",
    "half", "heart", "history", "human", "image", "include", "increase",
    "information", "interest", "island", "job", "join", "judge", "key",
    "knowledge", "language", "later", "laugh", "learn", "less", "likely",
    "local", "machine", "material", "measure", "memory", "metal", "mile",
    "mineral", "model", "moment", "natural", "north", "object", "off",
    "operation", "pattern", "person", "physical", "pick", "piece", "planet",
    "player", "population", "position", "practice", "present", "private",
    "produce", "product", "program", "property", "public", "race", "raise",
    "range", "rate", "reach", "region", "require", "resource", "result",
    "rich", "rise", "rock", "role", "round", "rule", "safe", "scale",
    "scene", "science", "section", "sense", "service", "shape", "shoot",
    "short", "shoulder", "simple", "single", "skill", "skin", "source",
    "special", "spot", "stage", "station", "steam", "step", "store",
    "strange", "surface", "talk", "tall", "temperature", "term", "test",
    "top", "total", "toward", "town", "travel", "trouble", "type", "value",
    "view", "village", "visit", "voice", "war", "warm", "weather", "website",
    "west", "wheel", "white", "whole", "window", "wish", "zone",
    # Feature-system words that are NOT features
    "mcp", "ue5", "python", "blueprint", "foundry", "sequencer", "lod",
    "ssim", "steam", "hud", "camera", "terrain", "canyon", "cloud",
    "scanner", "shelter", "tool", "flight", "fuel", "star", "temperature",
    "night", "celestial", "travel", "environmental", "trigger", "prompt",
    "notification", "npc", "edu", "demo", "cloud", "strata", "habitat",
    "module", "weather", "shadow", "rendering", "orbital", "mechanics",
    "consumption", "durability", "maintenance", "crafting", "progression",
    "dialogue", "trade", "basic", "behavior", "system", "implementation",
    "display", "audio", "feedback", "selection", "placement", "strategy",
    "educational", "cinematic", "sequence", "lighting", "transitions",
    "showcase", "indicators", "visuals", "generation", "rotation",
    "connection", "types", "visibility", "gameplay", "navigation", "prop",
    "props", "path", "physics", "scan", "resource", "biome",
    # Feature-specific domain words
    "inventory", "crafting", "recipe", "upgrade", "repair", "station",
    "reputation", "economy", "barter", "supply", "demand", "faction",
    "quest", "mission", "route", "waypoint", "auto", "pilot",
    "soi", "patched", "conic", "approximation", "docking",
    "animator", "safezone", "resolver", "history", "log",
    "priority", "cooldown", "context", "matcher", "queue", "cancel",
    "density", "map", "sky", "observation", "weather", "front",
    "flash", "flood", "wind", "direction", "barometric", "pressure",
    "fossil", "layer", "marker", "erosion", "texture", "rock", "type",
    "color", "banding", "grain", "fracture", "pattern", "legend",
    "overlay", "comparison", "tool", "cave", "overhang", "underground",
    "river", "system", "erosion", "layer", "biome", "specific",
    "carving", "simulation", "procedural", "material", "support",
    "landscape", "subsystem", "initialized", "shadow", "quality", "tier",
    "grass", "water", "refraction", "optical", "depth", "darkness",
    "altitude", "indicator", "formation", "speed", "rain", "storm",
    "clearing", "wind", "barometric", "pressure", "hud",
    "patrol", "route", "reaction", "system", "scheduling", "editor",
    "translation", "engine", "relationship", "tracker", "dialogue",
    "supply", "demand", "reputation", "economy", "barter",
    "voiceover", "music", "stinger", "activation", "sound", "scan",
    "loop", "result", "chime", "domain", "error",
    "upgrade", "tree", "category", "unlock", "knowledge", "tier",
    "recipe", "unlock", "crafting", "panel", "layout", "reticle",
    "design", "knowledge", "log", "integration",
    "terrain", "generator", "biome", "specific", "erosion",
    "cave", "generation", "overhang", "support", "underground",
    "river", "system", "procedural", "material", "landscape",
    "subsystem", "initialized", "shadow", "quality", "tier",
    "per", "should", "would", "could", "might", "does", "is",
    "do", "can", "have", "has", "had", "was", "were", "been",
    "are", "am", "be", "being", "be", "will", "shall", "may",
    "must", "need", "require", "want", "like", "know",
}

# Known feature names (loaded at runtime)
KNOWN_FEATURES = set()

def load_all_features():
    """Load every .json in the features directory."""
    features = {}
    for fp in sorted(FEATURES_DIR.glob("*.json")):
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        name = data.get("name", fp.stem)
        features[name] = data
    return features


def extract_explicit_edge_references(data):
    """Extract feature references from is_edge questions only.
    
    These are the structured dependency questions (category in EDGE_CATEGORIES).
    We look for feature names in the question text specifically.
    """
    edge_refs = defaultdict(set)
    EDGE_CATS = {"depends_on", "requires", "conflicts", "proves", "derived_from"}
    
    for q in data.get("questions", []):
        cat = q.get("category", "").lower()
        if cat not in EDGE_CATS or not q.get("is_edge"):
            continue
        qtext = q.get("question", "")
        # Look for feature names in the question text
        for feat in KNOWN_FEATURES:
            # Check exact name
            if feat in qtext:
                edge_refs[cat].add(feat)
            # Check human-readable form
            human = feat.replace("_", " ")
            if human in qtext:
                edge_refs[cat].add(feat)
            # Check partial matches (e.g., "Canyon Terrain" matches "Canyon_Terrain_Generation")
            parts = feat.split("_")
            if len(parts) >= 2:
                for i in range(len(parts) - 1):
                    partial = " ".join(parts[:i+2])
                    if partial in qtext:
                        edge_refs[cat].add(feat)
    return edge_refs


def find_sub_feature_hints(data):
    """Find explicit sub-feature decomposition mentions."""
    hints = []
    SUB_KW = {"sub-features", "sub features", "sub_features", "decompose",
              "break down", "breakdown", "sibling", "child", "children"}
    for q in data.get("questions", []):
        blob = (q.get("question", "") + " " + q.get("answer", "")).lower()
        if any(kw in blob for kw in SUB_KW):
            hints.append((q.get("id"), q.get("question", "")[:140]))
    return hints


def find_depth_hierarchy_mentions(data):
    """Find questions about depth, breadth, parent, dependency relationships."""
    hits = []
    KW = {"depth", "breadth", "parent", "dependency", "dependencies",
          "sub-feature", "sub-sub-feature"}
    for q in data.get("questions", []):
        blob = q.get("question", "").lower()
        if any(kw in blob for kw in KW):
            hits.append((q.get("id"), q.get("question", "")[:140]))
    return hits


def main():
    global KNOWN_FEATURES
    features = load_all_features()
    KNOWN_FEATURES = set(features.keys())
    print(f"Loaded {len(KNOWN_FEATURES)} features\n")

    # 1. Extract explicit edge references
    all_edges = {}
    for fname, data in features.items():
        edges = extract_explicit_edge_references(data)
        if edges:
            all_edges[fname] = edges

    # 2. Build dependency graph
    dependents = defaultdict(set)
    dependencies = defaultdict(set)
    
    for fname, edges in all_edges.items():
        for cat in ("depends_on", "requires"):
            for target in edges.get(cat, set()):
                if target != fname:
                    dependencies[fname].add(target)
                    dependents[target].add(fname)

    # 3. Find orphans (referenced in edge questions but no .json exists)
    orphans = defaultdict(list)
    for fname, edges in all_edges.items():
        for cat, targets in edges.items():
            for t in targets:
                if t not in KNOWN_FEATURES:
                    orphans[fname].append((cat, t))

    # 4. Leaf/root features
    leaf_features = sorted(KNOWN_FEATURES - set(dependents.keys()))
    root_features = sorted(KNOWN_FEATURES - set(dependencies.keys()))

    # 5. Sub-feature hints
    sub_hints = {}
    depth_hints = {}
    for fname, data in features.items():
        sf = find_sub_feature_hints(data)
        if sf:
            sub_hints[fname] = sf
        dh = find_depth_hierarchy_mentions(data)
        if dh:
            depth_hints[fname] = dh

    # 6. Question count (complexity proxy)
    q_counts = {fname: len(data.get("questions", [])) for fname, data in features.items()}

    # =====================================================================
    #  OUTPUT
    # =====================================================================
    print("=" * 72)
    print("  DEPENDENCY GRAPH SUMMARY")
    print("=" * 72)
    print(f"  Total features:           {len(KNOWN_FEATURES)}")
    print(f"  Features WITH deps:       {len(dependencies)}")
    print(f"  Features WITHOUT deps:    {len(root_features)} (roots)")
    print(f"  Features WITH dependents: {len(dependents)}")
    print(f"  Features WITHOUT deps:    {len(leaf_features)} (leaves)")

    print(f"\n{'='*72}")
    print("  ROOT FEATURES (no dependencies -- potential top-level modules)")
    print("=" * 72)
    for f in root_features:
        d = len(dependents.get(f, set()))
        print(f"  {f:<48} depended on by {d}")

    print(f"\n{'='*72}")
    print("  LEAF FEATURES (nothing depends on them -- potential leaves)")
    print("=" * 72)
    for f in leaf_features:
        my_deps = dependencies.get(f, set())
        dep_str = ", ".join(sorted(my_deps)) or "(none)"
        print(f"  {f}")
        print(f"    depends on {len(my_deps)}: {dep_str}")

    print(f"\n{'='*72}")
    print("  FULL DEPENDENCY MAP")
    print("=" * 72)
    for fname in sorted(dependencies):
        print(f"\n  {fname}")
        for d in sorted(dependencies[fname]):
            print(f"    --> {d}")
    for fname in sorted(root_features):
        print(f"\n  {fname}  [ROOT]")

    # Orphan references
    print(f"\n{'='*72}")
    print("  ORPHAN REFERENCES (mentioned in edge questions, no .json file)")
    print("=" * 72)
    if orphans:
        for fname, refs in sorted(orphans.items()):
            for cat, raw in sorted(refs):
                print(f"  {fname} --[{cat}]--> \"{raw}\"")
    else:
        print("  (none found)")

    # Sub-feature candidates
    print(f"\n{'='*72}")
    print("  SUB-FEATURE CANDIDATES (explicit decomposition mentions)")
    print("=" * 72)
    if sub_hints:
        for fname, hints in sorted(sub_hints.items()):
            print(f"\n  {fname}:")
            for qid, qtext in hints:
                print(f"    Q{qid}: {qtext}")
    else:
        print("  (none found)")

    # Depth / hierarchy mentions
    print(f"\n{'='*72}")
    print("  DEPTH / BREADTH / PARENT / HIERARCHY MENTIONS")
    print("=" * 72)
    if depth_hints:
        for fname, hints in sorted(depth_hints.items()):
            print(f"\n  {fname}:")
            for qid, qtext in hints:
                print(f"    Q{qid}: {qtext}")
    else:
        print("  (none found)")

    # Domain clusters
    print(f"\n{'='*72}")
    print("  DOMAIN CLUSTERS (features sharing a common prefix)")
    print("=" * 72)
    clusters = defaultdict(list)
    for fname in sorted(KNOWN_FEATURES):
        prefix = fname.split("_")[0]
        clusters[prefix].append(fname)
    for prefix, members in sorted(clusters.items(), key=lambda x: -len(x[1])):
        if len(members) > 1:
            print(f"\n  [{prefix}] ({len(members)} features):")
            for m in members:
                dc = len(dependents.get(m, set()))
                mc = len(dependencies.get(m, set()))
                print(f"    {m:<44} deps={mc:<3} dependents={dc}")

    # Complexity ranking
    print(f"\n{'='*72}")
    print("  COMPLEXITY RANKING (by question count)")
    print("=" * 72)
    for fname, count in sorted(q_counts.items(), key=lambda x: -x[1])[:15]:
        ec = sum(1 for q in features[fname].get("questions", []) if q.get("is_edge"))
        print(f"  {fname:<48} {count:>3} questions, {ec} edge")

    print(f"\n{'='*72}")
    print("  ANALYSIS COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
