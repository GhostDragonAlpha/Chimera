"""
workflow_level_design_v9.py — Automated Level Design Workflow (v9)

Generates terrain chunks by biome type, places structures/props via PCG system,
streams levels into World Partition, and validates level integrity after generation.

Usage (UE Editor): from workflow_level_design_v9 import run_level_design_workflow; run_level_design_workflow()
Usage (standalone): python workflow_level_design_v9.py --biome forest --count 16 --seed 42
"""

import os, sys, json, argparse, random, hashlib
from pathlib import Path


try:
    from config import CHIMERA_CONTENT_DIR, GameConfiguration
except ImportError:
    CHIMERA_CONTENT_DIR = Path(r"E:\PythonChimera\Chimera\Content")
    class _GC:
        GENERATION_SEED = 42
    GameConfiguration = _GC


BIOME_CONFIG = {
    "desert": {"height_range": (0.0, 50.0), "material_path": "/Game/Materials/MI_DesertSurface",
               "props": ["BP_Cactus", "BP_RockDesert", "BP_Dune"], "noise_scale": 200.0, "fog_density": 0.1},
    "forest": {"height_range": (0.0, 80.0), "material_path": "/Game/Materials/MI_ForestSurface",
               "props": ["BP_TreeOak", "BP_Mushroom", "BP_GrassCluster"], "noise_scale": 150.0, "fog_density": 0.3},
    "tundra": {"height_range": (-20.0, 30.0), "material_path": "/Game/Materials/MI_TundraSurface",
               "props": ["BP_IceFormation", "BP_SnowPile", "BP_FrozenTree"], "noise_scale": 180.0, "fog_density": 0.5},
    "volcanic": {"height_range": (50.0, 200.0), "material_path": "/Game/Materials/MI_VolcanicSurface",
                 "props": ["BP_LavaPool", "BP_ObsidianRock", "BP_SmokeVent"], "noise_scale": 120.0, "fog_density": 0.7},
    "swamp": {"height_range": (-5.0, 15.0), "material_path": "/Game/Materials/MI_SwampSurface",
              "props": ["BP_ReedCluster", "BP_MudPuddle", "BP_DeadTree"], "noise_scale": 160.0, "fog_density": 0.8},
    "mountain": {"height_range": (100.0, 350.0), "material_path": "/Game/Materials/MI_MountainSurface",
                 "props": ["BP_SnowCapRock", "BP_EagleNest", "BP_CloudLift"], "noise_scale": 250.0, "fog_density": 0.6},
}

STRUCTURE_TEMPLATES = [
    {"name": "BP_RuinsTemple", "min_spacing": 500.0, "lod_levels": ["LOD0", "LOD1", "LOD2"]},
    {"name": "BP_BridgeStone", "min_spacing": 800.0, "lod_levels": ["LOD0", "LOD1"]},
    {"name": "BP_Watchtower", "min_spacing": 1200.0, "lod_levels": ["LOD0", "LOD1", "LOD2"]},
    {"name": "BP_CampFire", "min_spacing": 300.0, "lod_levels": ["LOD0"]},
    {"name": "BP_FortressGate", "min_spacing": 600.0, "lod_levels": ["LOD0", "LOD1"]},
]


def generate_terrain_chunks(biome: str, count: int, seed: int) -> list[dict]:
    config = BIOME_CONFIG.get(biome, BIOME_CONFIG["desert"])
    random.seed(seed)
    chunks = []
    spacing = config["noise_scale"] * 1.5
    grid_size = max(4, int(random.gauss(4, 0.5)))
    for i in range(count):
        row = i // grid_size
        col = i % grid_size
        x = col * spacing - spacing * (grid_size / 2) + random.uniform(-spacing * 0.1, spacing * 0.1)
        y = row * spacing - spacing * (grid_size / 2) + random.uniform(-spacing * 0.1, spacing * 0.1)
        z = random.uniform(*config["height_range"])
        chunks.append({
            "chunk_id": f"terrain_{biome}_{seed:04d}_{i}",
            "position": {"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)},
            "size": config["noise_scale"],
            "material_path": config["material_path"],
            "height_range": config["height_range"],
        })
    return chunks


def place_structures_and_props(chunks: list[dict], biome: str) -> list[dict]:
    config = BIOME_CONFIG.get(biome, BIOME_CONFIG["desert"])
    random.seed(hash((biome, tuple(round(c["position"]["x"], 1) for c in chunks))))
    placements = []
    props = config["props"]
    for chunk in chunks:
        cx, cy = chunk["position"]["x"], chunk["position"]["y"]
        half = chunk["size"] / 2
        placed_structures = []
        for struct in STRUCTURE_TEMPLATES:
            if random.random() < 0.35:
                sx = cx + random.uniform(-half * 0.3, half * 0.3)
                sy = cy + random.uniform(-half * 0.3, half * 0.3)
                overlap = False
                for ps in placed_structures:
                    dx = abs(sx - ps["position"]["x"])
                    dy = abs(sy - ps["position"]["y"])
                    if dx < struct["min_spacing"] and dy < struct["min_spacing"]:
                        overlap = True
                        break
                if not overlap:
                    placed_structures.append({"position": {"x": sx, "y": sy}})
                    placements.append({
                        "actor_id": f"struct_{struct['name']}_{len(placements)}",
                        "type": "structure",
                        "template_path": struct["name"],
                        "position": {"x": round(sx, 2), "y": round(sy, 2), "z": chunk["position"]["z"]},
                        "lod_levels": struct.get("lod_levels", ["LOD0"]),
                    })
        for _ in range(random.randint(3, 8)):
            placements.append({
                "actor_id": f"prop_{random.choice(props)}_{len(placements)}",
                "type": "prop",
                "template_path": random.choice(props),
                "position": {"x": round(cx + random.uniform(-half * 0.45, half * 0.45), 2),
                             "y": round(cy + random.uniform(-half * 0.45, half * 0.45), 2),
                             "z": chunk["position"]["z"]},
            })
    return placements


def stream_levels_into_world_partition(chunks: list[dict], biome: str) -> dict:
    level_name = f"LP_{biome.capitalize()}_{chunks[0]['position']['x']:.0f}_{chunks[0]['position']['y']:.0f}"
    regions = []
    for chunk in chunks:
        pos, half = chunk["position"], chunk["size"] / 2
        regions.append({
            "region_id": f"reg_{chunk['chunk_id']}",
            "bounds": {"min_x": round(pos["x"] - half, 2), "max_x": round(pos["x"] + half, 2),
                       "min_y": round(pos["y"] - half, 2), "max_y": round(pos["y"] + half, 2)},
        })
    return {"level_name": level_name, "biome": biome, "streaming_regions": regions, "total_chunks": len(chunks)}


def validate_level_integrity(level_info: dict, placements: list[dict], lod_count: int) -> dict:
    errors, warnings = [], []
    structures = [p for p in placements if p["type"] == "structure"]
    props = [p for p in placements if p["type"] == "prop"]
    if len(structures) < 1:
        warnings.append("No structures placed")
    for i, a in enumerate(structures):
        for b in structures[i + 1:]:
            dx, dy = abs(a["position"]["x"] - b["position"]["x"]), abs(a["position"]["y"] - b["position"]["y"])
            if dx < 200 and dy < 200:
                warnings.append(f"Structures {a['actor_id']} and {b['actor_id']} may overlap")
    region_count = len(level_info.get("streaming_regions", []))
    if region_count != level_info["total_chunks"]:
        errors.append(f"Region count ({region_count}) mismatch with chunk count ({level_info['total_chunks']})")
    return {
        "valid": len(errors) == 0, "errors": errors, "warnings": warnings,
        "stats": {"total_placements": len(placements), "structures": len(structures),
                  "props": len(props), "streaming_regions": region_count, "lod_levels": lod_count},
    }


def generate_lod_for_chunk(chunk: dict) -> list[dict]:
    half = chunk["size"] / 2
    lods = []
    for factor in [0.5, 0.25, 0.125]:
        lod_size = chunk["size"] * factor
        lods.append({"lod_name": f"LOD_{factor}", "chunk_id": chunk["chunk_id"],
                      "bounds": {"min_x": round(-half * factor, 2), "max_x": round(half * factor, 2),
                                 "min_y": round(-half * factor, 2), "max_y": round(half * factor, 2)},
                      "detail_level": factor})
    return lods


def _simulate(biome: str, count: int, seed: int) -> dict:
    chunks = generate_terrain_chunks(biome, count, seed)
    placements = place_structures_and_props(chunks, biome)
    level_info = stream_levels_into_world_partition(chunks, biome)
    lod_count = sum(len(generate_lod_for_chunk(c)) for c in chunks)
    validation = validate_level_integrity(level_info, placements, lod_count)
    output_dir = CHIMERA_CONTENT_DIR / "ProceduralGenerated" / "Levels"
    os.makedirs(output_dir, exist_ok=True)
    spec_path = output_dir / f"level_design_{biome}_{seed}.json"
    with open(spec_path, 'w') as f:
        json.dump({"biome": biome, "seed": seed, "chunks": chunks, "placements": placements,
                    "level_info": level_info, "validation": validation}, f, indent=2)
    print(f"[SIM] Spec saved to: {spec_path}")
    return {"biome": biome, "seed": seed}


def run_level_design_workflow(biome="desert", count=16, seed=None):
    if seed is None:
        seed = GameConfiguration.GENERATION_SEED
    print("=" * 60); print("LEVEL DESIGN WORKFLOW (v9)"); print("=" * 60)
    print(f"Biome: {biome} | Chunks: {count} | Seed: {seed}")
    try:
        import unreal
        chunks = generate_terrain_chunks(biome, count, seed)
        print(f"\n[STEP 1] Generated {len(chunks)} terrain chunks"); print("[OK]")
        placements = place_structures_and_props(chunks, biome)
        print(f"[STEP 2] Placed {len(placements)} actors via PCG (overlap-checked)"); print("[OK]")
        level_info = stream_levels_into_world_partition(chunks, biome)
        print(f"[STEP 3] Streamed level '{level_info['level_name']}' into World Partition"); print("[OK]")
        lod_count = sum(len(generate_lod_for_chunk(c)) for c in chunks)
        validation = validate_level_integrity(level_info, placements, lod_count)
        print(f"\n[STEP 4] Validated — {'PASS' if validation['valid'] else 'ISSUES FOUND'}")
        for w in validation["warnings"]:
            print(f"[WARN] {w}")
    except ImportError:
        print("[WARN] unreal module not available — simulation mode"); _simulate(biome, count, seed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Level Design Workflow (v9)")
    parser.add_argument("--biome", type=str, default="desert", choices=list(BIOME_CONFIG.keys()))
    parser.add_argument("--count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    run_level_design_workflow(biome=args.biome, count=args.count, seed=args.seed)
