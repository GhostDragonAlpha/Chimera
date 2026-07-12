"""Quarantine information-free unknown_* nodes from the DNA graph and re-record
the real work that was lost to the feature/feature_name key mismatch.

Root cause (fixed in core/graphify_interface.py on 2026-07-05):
- _mutate_feature_complete read details["feature"]; several record scripts passed
  "feature_name" (or only "features_completed"), so nodes were written as
  "unknown_feature" and the real feature status was lost.
- _mutate_pathway_attempt / _mutate_loop_complete silently defaulted missing keys
  to unknown_tool/unknown_action/unknown, producing zero-information nodes.

This script:
1. Moves junk nodes to docs/dna_graph_quarantine_unknown_nodes.json (never deletes).
2. Re-records the lost FeatureUpdates through the fixed handler.
3. Re-records Loop 0 completion (both prior LoopComplete nodes for loop 0 were junk).
"""
import json
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from graphify_interface import (
    graphify_mutate, record_feature, record_loop, load_dna_graph,
    save_dna_graph, DNA_GRAPH_PATH,
)

QUARANTINE_PATH = DNA_GRAPH_PATH.parent / "dna_graph_quarantine_unknown_nodes.json"
REPAIR_NOTE = "re-recorded 2026-07-05 after key-mismatch fix; original write lost to unknown_feature default"


def is_junk(n):
    t = n.get("type")
    if t == "FeatureUpdate" and n.get("feature_name") == "unknown_feature":
        return True
    if t == "pathway_attempt" and n.get("tool") == "unknown_tool" and n.get("action") == "unknown_action":
        return True
    if t == "LoopComplete" and n.get("name") == "unknown" and not n.get("features"):
        return True
    return False


def quarantine():
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])
    edges = dna.get("edges", [])

    junk = [n for n in nodes if is_junk(n)]
    keep = [n for n in nodes if not is_junk(n)]
    junk_ids = {n["id"] for n in junk}
    kept_edges = [e for e in edges
                  if e.get("source") not in junk_ids and e.get("target") not in junk_ids]

    print(f"nodes: {len(nodes)} -> {len(keep)} (quarantined {len(junk)})")
    print(f"edges: {len(edges)} -> {len(kept_edges)} (dropped {len(edges) - len(kept_edges)})")

    existing = []
    if QUARANTINE_PATH.exists():
        existing = json.loads(QUARANTINE_PATH.read_text(encoding="utf-8")).get("nodes", [])
    QUARANTINE_PATH.write_text(json.dumps({
        "quarantined_at": datetime.now(timezone.utc).isoformat(),
        "reason": "information-free nodes from mis-keyed g.mutate calls "
                  "(feature vs feature_name; missing tool/action/name keys)",
        "nodes": existing + junk,
    }, indent=2), encoding="utf-8")
    print(f"quarantine archive: {QUARANTINE_PATH} ({len(existing) + len(junk)} nodes total)")

    dna["nodes"] = keep
    dna["edges"] = kept_edges
    save_dna_graph(dna)
    return len(junk)


LOST_FEATURES = [
    # record_ground_sand_surface.py
    {"feature": "Ground_Sand_Surface", "loop": 1, "status": "verified", "parameters": {
        "material_path": "/Game/Chimera/Materials/MAT_GroundSand/MAT_GroundSand",
        "roughness": 0.9, "metallic": 0.05, "base_color_rgb": [0.545, 0.498, 0.419],
        "description": "PBR sand material: color #8B7D6B, roughness 0.9, metallic 0.05",
        "re_recorded": REPAIR_NOTE}},
    # record_loop1_ground_refinements.py
    {"feature": "Ground_Rock_Surface", "loop": 1, "status": "verified", "parameters": {
        "mesh_path": "/Game/VehicleTemplate/Meshes/SM_Cone.SM_Cone",
        "material_path": "/Game/Chimera/Materials/MAT_RockSurface/MAT_RockSurface",
        "scale": [2.5, 2.5, 2.5],
        "description": "Rock surface using scaled cone mesh with MAT_RockSurface material applied",
        "re_recorded": REPAIR_NOTE}},
    {"feature": "Ground_Metal_Surface", "loop": 1, "status": "verified", "parameters": {
        "mesh_path": "/Game/VehicleTemplate/Meshes/SM_Track_10M.SM_Track_10M",
        "material_path": "/Game/Chimera/Materials/MAT_MetalSurface_PBR/MAT_MetalSurface_PBR",
        "dust_accumulation": 0.3,
        "description": "Metal surface with PBR material and dust accumulation mask parameter",
        "re_recorded": REPAIR_NOTE}},
    # record_player_character_animation_status.py
    {"feature": "Player_Character_Animation", "loop": 0, "status": "blocked", "parameters": {
        "reason": "No animation sequences exist in project. Need to import or create "
                  "walk/run/idle/jump animations for BP_Astronaut_Character skeleton.",
        "anim_blueprint_exists": "/Game/Chimera/Animations/Blueprints/AnimBP_Locomotion_VerbStep",
        "next_steps": "Import animation sequences from Mixamo, MotionBuilder, or create "
                      "procedural locomotion using AnimBlueprints.",
        "re_recorded": REPAIR_NOTE}},
    # record_loop2_verb_blueprints.py (per-verb records)
    *[{"feature": v, "loop": 2, "status": "verified", "parameters": {
        "blueprint_path": f"/Game/Chimera/Blueprints/BP_{v}",
        "description": f"Basic verb interaction blueprint created. Needs gameplay logic "
                       f"implementation for {v.split('_', 1)[1].lower()} action.",
        "re_recorded": REPAIR_NOTE}}
      for v in ["Verb_Step", "Verb_Bend", "Verb_PickUp", "Verb_Drop", "Verb_Shovel"]],
    # record_loop2_verb_blueprints_complete.py (batch, /Game/Chimera/Verbs generation)
    {"feature": "Verb_Blueprints_Loop2", "loop": 2, "status": "structural_ready", "parameters": {
        "blueprints": ["/Game/Chimera/Verbs/BP_Verb_PickUp", "/Game/Chimera/Verbs/BP_Verb_Step",
                       "/Game/Chimera/Verbs/BP_Verb_Bend", "/Game/Chimera/Verbs/BP_Verb_Drop",
                       "/Game/Chimera/Verbs/BP_Verb_Shovel"],
        "components_added": {"BP_Verb_PickUp": ["PickupInteractionComponent"],
                             "BP_Verb_Step": ["AudioComponent"]},
        "notes": "All 5 verb blueprints created and compiled. Gameplay logic events "
                 "(BlueprintImplementableEvent) need to be wired in Blueprint Graph via editor.",
        "re_recorded": REPAIR_NOTE}},
    # record_loop2_compilation_complete.py
    {"feature": "Verb_Blueprints_Compilation_Loop2", "loop": 2, "status": "compiled", "parameters": {
        "blueprints_compiled": ["/Game/Chimera/Verbs/BP_Verb_PickUp", "/Game/Chimera/Verbs/BP_Verb_Step",
                                "/Game/Chimera/Verbs/BP_Verb_Bend", "/Game/Chimera/Verbs/BP_Verb_Drop",
                                "/Game/Chimera/Verbs/BP_Verb_Shovel"],
        "notes": "All 5 verb blueprints compiled successfully via MCP. Structural components "
                 "added. Blueprint Graph events need manual wiring.",
        "re_recorded": REPAIR_NOTE}},
    # record_loop3_sky_assets.py
    {"feature": "Sky_Assets_Loop3", "loop": 3, "status": "placed", "parameters": {
        "assets_created": ["/Game/Textures/TEX_Earth_Atmosphere", "/Game/Materials/MAT_Sun_Lighting",
                           "/Game/Materials/MAT_Moon_Surface", "/Game/Textures/TEX_Starfield"],
        "actors_spawned": ["DirectionalLight (Sun, pitch=15 yaw=-80)", "SkyLight (Ambient)"],
        "re_recorded": REPAIR_NOTE}},
    # record_loop3_sky_sphere.py
    {"feature": "SkySphere_Starfield_Loop3", "loop": 3, "status": "created_ready", "parameters": {
        "actor_path": "/Game/Chimera/Levels/L_VerificationStudio/L_VerificationStudio:"
                      "PersistentLevel.SkySphere_Starfield",
        "radius": 10000, "numSides": 64, "numRings": 32,
        "re_recorded": REPAIR_NOTE}},
]

LOOP0_COMPLETE = {  # record_loop0_complete.py
    "loop": 0,
    "name": "The Player",
    "features": [
        {"feature_name": "Player_Character_Lighting", "status": "verified",
         "description": "Three-point lighting matches NASA reference"},
        {"feature_name": "Player_Character_Model", "status": "verified",
         "description": "BP_Astronaut_Character spawned, MAT_Visor_Polycarbonate_Gold applied "
                        "with PBR parameters (Metallic=0.8, Roughness=0.1, gold tint)"},
        {"feature_name": "Player_Character_Suit", "status": "verified",
         "description": "MAT_Visor_Polycarbonate_Gold created and applied to CharacterMesh0"},
    ],
    "emotional_anchor": "The seed",
}


def already_backfilled(nodes):
    """Return (feature_names, loop_keys) already re-recorded by this script.

    Re-running this fixer used to re-record every LOST_FEATURES entry with a
    fresh `datetime.now()` timestamp, so 2026-07-05-era statuses shadowed every
    genuine FeatureUpdate recorded since (observed 2026-07-11: the loop board
    showed Player_Character_Animation 'blocked' over a real 'verified' and
    Verb_Shovel 'verified' over a real 'needs_refinement'). The backfill is a
    one-time repair: skip anything the graph already carries.

    Idempotency check (2026-07-11 enhanced): Accept backfilled entries with:
    - backfilled flag + REPAIR_NOTE (primary marker), OR
    - backfilled flag + feature matches LOST_FEATURES (fallback)
    This prevents re-recording even if the repair note text ever changes.
    """
    feats, loops = set(), set()
    lost_feature_names = {d["feature"] for d in LOST_FEATURES}
    for n in nodes:
        if not n.get("backfilled"):
            continue
        if n.get("type") == "FeatureUpdate":
            fname = n.get("feature_name")
            # Accept if repair note matches OR if feature is in LOST_FEATURES (fallback)
            if (n.get("parameters") or {}).get("re_recorded") == REPAIR_NOTE or \
                    fname in lost_feature_names:
                feats.add(fname)
        elif n.get("type") == "LoopComplete" and \
                n.get("loop") == LOOP0_COMPLETE["loop"] and \
                n.get("name") == LOOP0_COMPLETE["name"]:
            loops.add((n.get("loop"), n.get("name")))
    return feats, loops


def re_record():
    dna = load_dna_graph()
    done_feats, done_loops = already_backfilled(dna.get("nodes", []))
    for d in LOST_FEATURES:
        if d["feature"] in done_feats:
            print(f"skip FeatureUpdate {d['feature']} — already re-recorded (idempotent)")
            continue
        rid = record_feature(
            feature=d["feature"], loop=d["loop"], status=d["status"],
            parameters=d.get("parameters", {}), backfilled=True,
        )
        print(f"re-recorded FeatureUpdate {d['feature']} (loop {d['loop']}, {d['status']}) -> {rid}")
    if (LOOP0_COMPLETE["loop"], LOOP0_COMPLETE["name"]) in done_loops:
        print("skip LoopComplete 'The Player' (loop 0) — already re-recorded (idempotent)")
        return
    rid = record_loop(
        loop=LOOP0_COMPLETE["loop"], name=LOOP0_COMPLETE["name"],
        features=LOOP0_COMPLETE["features"],
        emotional_anchor=LOOP0_COMPLETE.get("emotional_anchor", ""),
        backfilled=True,
    )
    print(f"re-recorded LoopComplete 'The Player' (loop 0) -> {rid}")


if __name__ == "__main__":
    removed = quarantine()
    re_record()
    dna = load_dna_graph()
    print(f"final node count: {len(dna.get('nodes', []))}")
    print("done")
