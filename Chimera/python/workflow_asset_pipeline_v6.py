"""
workflow_asset_pipeline_v6.py — Asset Pipeline Automation v6

Imports assets from external directories, generates materials and textures procedurally,
creates blueprint instances from templates, and runs dependency analysis on imported assets.

Usage (UE Editor): from workflow_asset_pipeline_v6 import run_asset_pipeline; run_asset_pipeline()
Usage (standalone): python workflow_asset_pipeline_v6.py --import-dir E:/Assets --generate materials,textures
"""

import os, sys, json, argparse, random
from pathlib import Path


try:
    from config import CHIMERA_CONTENT_DIR, GameConfiguration
except ImportError:
    CHIMERA_CONTENT_DIR = Path(r"E:\PythonChimera\Chimera\Content")
    class _GC:
        GENERATION_SEED = 42
    GameConfiguration = _GC


ASSET_CATEGORIES = {
    "mesh": {"extensions": (".fbx", ".obj"), "destination": "/Game/Assets/Meshes"},
    "texture": {"extensions": (".png", ".tga", ".exr"), "destination": "/Game/Assets/Textures"},
    "material": {"extensions": (".mat",), "destination": "/Game/Assets/Materials"},
    "sound": {"extensions": (".wav", ".ogg"), "destination": "/Game/Assets/Audio"},
}

PROCEDURAL_MATERIALS = [
    {"name": "MI_SurfaceConcrete", "type": "PhysicalMaterial", "color": (0.6, 0.55, 0.5)},
    {"name": "MI_SurfaceMetal", "type": "PhysicalMaterial", "color": (0.3, 0.3, 0.35)},
    {"name": "MI_SurfaceWood", "type": "PhysicalMaterial", "color": (0.45, 0.3, 0.15)},
    {"name": "MI_SurfaceGlass", "type": "TranslucentMaterial", "color": (0.8, 0.85, 0.9)},
]

PROCEDURAL_TEXTURES = [
    {"name": "T_NormalConcrete", "size": (512, 512), "format": "NormalMap"},
    {"name": "T_AlbedoWood", "size": (1024, 1024), "format": "Color"},
    {"name": "T_HeightTerrain", "size": (2048, 2048), "format": "HeightMap"},
]

BLUEPRINT_TEMPLATES = {
    "BP_Wall": {"parent_class": "/Game/Blueprints/BP_BaseStaticMesh", "components": ["StaticMeshComponent"],
                "properties": {"cast_shadow": True, "receive_shadow": True}},
    "BP_Floor": {"parent_class": "/Game/Blueprints/BP_BaseStaticMesh", "components": ["StaticMeshComponent"],
                 "properties": {"cast_shadow": False, "receive_shadow": True}},
    "BP_PropGeneric": {"parent_class": "/Game/Blueprints/BP_BaseActor", "components": ["SceneComponent", "StaticMeshComponent"],
                       "properties": {"auto_destroy": False, "b_collidable": True}},
}


def import_assets(import_dir: str) -> list[dict]:
    imported = []
    scan_path = Path(import_dir)
    if not scan_path.exists():
        print(f"[WARN] Import directory does not exist: {import_dir}")
        return imported
    for file in scan_path.rglob("*"):
        if file.is_file():
            ext = file.suffix.lower()
            category = None
            for cat, info in ASSET_CATEGORIES.items():
                if ext in info["extensions"]:
                    category = cat
                    break
            if category:
                imported.append({
                    "source_path": str(file),
                    "asset_name": file.stem,
                    "category": category,
                    "target_ue_path": f"{ASSET_CATEGORIES[category]['destination']}/{file.stem}",
                    "file_size_bytes": file.stat().st_size,
                })
    print(f"[OK] Cataloged {len(imported)} assets from {import_dir}")
    return imported


def generate_materials(mat_types: list[str]) -> list[dict]:
    available = {m["name"]: m for m in PROCEDURAL_MATERIALS}
    materials = []
    for type_name in mat_types:
        if type_name not in available:
            print(f"[WARN] Unknown material type: {type_name}")
            continue
        mat_def = available[type_name]
        color = mat_def["color"]
        materials.append({
            "material_name": type_name,
            "type": mat_def["type"],
            "parameters": {
                "base_color": {"r": round(color[0], 3), "g": round(color[1], 3), "b": round(color[2], 3)},
                "roughness": random.uniform(0.3, 0.8) if mat_def["type"] == "PhysicalMaterial" else 0.1,
                "metallic": random.uniform(0.0, 0.5) if mat_def["type"] == "PhysicalMaterial" else 0.0,
            },
            "shader_graph": [
                {"name": "BaseColor", "type": "ScalarParameter"},
                {"name": "Roughness", "type": "ScalarParameter"},
                {"name": "Metallic", "type": "ScalarParameter"},
                {"name": "MaterialOutput", "type": "Output"},
            ],
        })
    print(f"[OK] Generated {len(materials)} procedural materials")
    return materials


def generate_textures(tex_types: list[str]) -> list[dict]:
    available = {t["name"]: t for t in PROCEDURAL_TEXTURES}
    textures = []
    for type_name in tex_types:
        if type_name not in available:
            print(f"[WARN] Unknown texture type: {type_name}")
            continue
        tex_def = available[type_name]
        w, h = tex_def["size"]
        channels = 4 if tex_def["format"] == "Color" else 3
        textures.append({
            "texture_name": type_name,
            "dimensions": {"width": w, "height": h},
            "format": tex_def["format"],
            "channels": channels,
            "mip_levels": max(1, max(w, h) // 64),
            "generation_seed": random.randint(0, 99999),
        })
    print(f"[OK] Generated {len(textures)} procedural textures")
    return textures


def create_blueprints(tpl_names: list[str]) -> list[dict]:
    available = dict(BLUEPRINT_TEMPLATES)
    blueprints = []
    for tpl_name in tpl_names:
        if tpl_name not in available:
            print(f"[WARN] Unknown blueprint template: {tpl_name}")
            continue
        tpl = available[tpl_name]
        bp_id = f"BP_{tpl_name}_{random.randint(100, 999)}"
        blueprints.append({
            "blueprint_id": bp_id,
            "template_source": tpl_name,
            "parent_class": tpl["parent_class"],
            "components": tpl["components"],
            "properties": dict(tpl["properties"]),
            "export_path": f"/Game/Blueprints/{bp_id}",
        })
    print(f"[OK] Created {len(blueprints)} blueprint instances")
    return blueprints


def dependency_analysis(assets: list[dict], materials: list[dict], blueprints: list[dict]) -> dict:
    mat_lookup = {m["material_name"]: m for m in materials}
    edges = []
    mesh_assets = [a for a in assets if a["category"] == "mesh"]
    texture_assets = [a for a in assets if a["category"] == "texture"]
    for mesh in mesh_assets:
        assigned = random.choice(list(mat_lookup.keys())) if mat_lookup else None
        if assigned:
            edges.append({"source": mesh["asset_name"], "target": assigned, "relation": "uses_material"})
    for tex in texture_assets:
        edges.append({"source": tex["asset_name"], "target": f"Material_{tex['texture_name']}", "relation": "feeds_texture"})
    bp_deps = [{"blueprint": bp["blueprint_id"], "parent_class": bp["parent_class"],
                "component_count": len(bp["components"])} for bp in blueprints]
    referenced = set(e["source"] for e in edges if e["relation"] == "uses_material")
    orphaned = [a["asset_name"] for a in mesh_assets if a["asset_name"] not in referenced]
    return {
        "dependency_graph": {"edges": edges, "total_edges": len(edges)},
        "blueprint_dependencies": bp_deps,
        "orphaned_assets": orphaned,
        "stats": {"total_assets": len(assets), "total_materials": len(materials),
                  "total_blueprints": len(blueprints), "dependency_edges": len(edges), "orphan_count": len(orphaned)},
    }


def _simulate(import_dir: str, gen_mats: list[str], gen_texs: list[str], bp_tpls: list[str]) -> dict:
    assets = import_assets(import_dir) if os.path.exists(import_dir) else []
    materials = generate_materials(gen_mats)
    textures = generate_textures(gen_texs)
    blueprints = create_blueprints(bp_tpls)
    analysis = dependency_analysis(assets, materials, blueprints)
    output_dir = CHIMERA_CONTENT_DIR / "ProceduralGenerated" / "Assets"
    os.makedirs(output_dir, exist_ok=True)
    spec_path = output_dir / f"asset_pipeline_v6_{hash((import_dir, tuple(gen_mats))) % 10000}.json"
    with open(spec_path, 'w') as f:
        json.dump({"import_dir": import_dir, "generated_materials": materials,
                   "generated_textures": textures, "blueprint_instances": blueprints,
                   "dependency_analysis": analysis}, f, indent=2)
    print(f"[SIM] Spec saved to: {spec_path}")
    return {"import_dir": import_dir}


def run_asset_pipeline(import_dir=None, gen_materials=None, gen_textures=None, bp_templates=None):
    print("=" * 60); print("ASSET PIPELINE WORKFLOW v6"); print("=" * 60)
    try:
        import unreal
        assets = import_assets(import_dir) if import_dir else []
        print(f"\n[STEP 1] Imported {len(assets)} assets"); print("[OK]")
        mat_types = gen_materials or [m["name"] for m in PROCEDURAL_MATERIALS[:3]]
        materials = generate_materials(mat_types)
        tex_types = gen_textures or [t["name"] for t in PROCEDURAL_TEXTURES[:2]]
        textures = generate_textures(tex_types)
        bp_names = bp_templates or list(BLUEPRINT_TEMPLATES.keys())
        blueprints = create_blueprints(bp_names)
        analysis = dependency_analysis(assets, materials, blueprints)
        stats = analysis["stats"]
        print(f"\n[STEP 5] Dependencies: {stats['dependency_edges']} edges | Orphaned: {stats['orphan_count']}")
    except ImportError:
        print("[WARN] unreal module not available — simulation mode")
        _simulate(import_dir or r"E:\Assets",
                  gen_materials or [m["name"] for m in PROCEDURAL_MATERIALS[:3]],
                  gen_textures or [t["name"] for t in PROCEDURAL_TEXTURES[:2]],
                  bp_templates or list(BLUEPRINT_TEMPLATES.keys()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asset Pipeline Automation v6")
    parser.add_argument("--import-dir", type=str, default=None)
    parser.add_argument("--generate", type=str, nargs="+", default=["materials", "textures"],
                        choices=["materials", "textures"])
    parser.add_argument("--templates", type=str, nargs="+", default=None, choices=list(BLUEPRINT_TEMPLATES.keys()))
    args = parser.parse_args()
    gen_mats = [m["name"] for m in PROCEDURAL_MATERIALS] if "materials" in args.generate and "textures" not in args.generate else None
    gen_texs = [t["name"] for t in PROCEDURAL_TEXTURES] if "textures" in args.generate and "materials" not in args.generate else None
    run_asset_pipeline(import_dir=args.import_dir, gen_materials=gen_mats,
                       gen_textures=gen_texs, bp_templates=args.templates)
