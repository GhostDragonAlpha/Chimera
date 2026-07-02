"""
Incremental Generator — Accepts updated DSL from user after review and incrementally regenerates 
only the affected parts, maintaining existing stable assets without regeneration.

Supports Stage 6 of the 6-stage pipeline: Regenerate & Iterate.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Set


class IncrementalGenerator:
    """Incrementally regenerates only affected parts of a game project based on updated DSL."""

    def __init__(self, content_dir: str, source_dir: str):
        self.content_dir = Path(content_dir) / "ProceduralGenerated"
        self.source_dir = Path(source_dir)
        
        # Track generated assets and their DSL sources for incremental updates
        self.asset_registry = {
            "meshes": {},
            "textures": {},
            "animations": {},
            "sounds": {},
            "character_classes": {},
            "ability_classes": {},
            "effect_classes": {}
        }

    def load_asset_registry(self) -> Dict[str, Any]:
        """Load existing asset registry if available."""
        registry_path = self.content_dir / "asset_registry.json"
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.asset_registry

    def save_asset_registry(self, registry: Dict[str, Any]):
        """Save asset registry for future incremental updates."""
        registry_path = self.content_dir / "asset_registry.json"
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)

    def determine_affected_components(self, old_dsl: Dict[str, Any], new_dsl: Dict[str, Any]) -> Set[str]:
        """Determine which components need regeneration based on DSL changes."""
        affected = set()

        # Check for gameplay changes
        if "gameplay" in new_dsl and "gameplay" in old_dsl:
            old_gameplay = old_dsl["gameplay"]
            new_gameplay = new_dsl["gameplay"]
            
            # Check character changes
            old_chars = {c.get("name") for c in old_gameplay.get("characters", [])}
            new_chars = {c.get("name") for c in new_gameplay.get("characters", [])}
            
            if old_chars != new_chars:
                affected.add("character_classes")
                
            # Check ability changes
            old_abilities = {a.get("name") for a in old_gameplay.get("abilities", [])}
            new_abilities = {a.get("name") for a in new_gameplay.get("abilities", [])}
            
            if old_abilities != new_abilities:
                affected.add("ability_classes")
                
        # Check for world/npc changes
        if "world" in new_dsl and "world" in old_dsl:
            old_world = old_dsl["world"]
            new_world = new_dsl["world"]
            
            # Check level changes
            old_levels = {l.get("name") for l in old_world.get("levels", [])}
            new_levels = {l.get("name") for l in new_world.get("levels", [])}
            
            if old_levels != new_levels:
                affected.add("environment_meshes")
                
            # Check NPC changes
            old_npcs = {n.get("name") for n in old_world.get("npcs", [])}
            new_npcs = {n.get("name") for n in new_world.get("npcs", [])}
            
            if old_npcs != new_npcs:
                affected.add("npc_meshes")
                
        # Check for UI changes
        if "ui" in new_dsl and "ui" in old_dsl:
            old_ui = old_dsl["ui"]
            new_ui = new_dsl["ui"]
            
            if old_ui.get("hud", {}).get("elements") != new_ui.get("hud", {}).get("elements"):
                affected.add("ui_widgets")
                
        # Check for audio changes
        if "audio" in new_dsl and "audio" in old_dsl:
            old_audio = old_dsl["audio"]
            new_audio = new_dsl["audio"]
            
            old_music = {m.get("name") for m in old_audio.get("music_cues", [])}
            new_music = {m.get("name") for m in new_audio.get("music_cues", [])}
            
            if old_music != new_music:
                affected.add("music_sounds")
                
            old_sfx = {s.get("name") for s in old_audio.get("sfx", [])}
            new_sfx = {s.get("name") for s in new_audio.get("sfx", [])}
            
            if old_sfx != new_sfx:
                affected.add("sfx_sounds")

        return affected

    def incrementally_generate(self, old_dsl: Dict[str, Any], new_dsl: Dict[str, Any], 
                               game_code_generator, asset_generator) -> Dict[str, List[str]]:
        """Incrementally generate only affected components."""
        # Determine affected components
        affected_components = self.determine_affected_components(old_dsl, new_dsl)
        
        print(f"Identified {len(affected_components)} affected components for regeneration:")
        for comp in affected_components:
            print(f"  - {comp}")

        # Load existing asset registry
        registry = self.load_asset_registry()
        
        generated_files = {
            "character_classes": [],
            "ability_classes": [],
            "effect_classes": [],
            "behavior_trees": [],
            "ui_widgets": [],
            "replication_rules": [],
            "meshes": [],
            "textures": [],
            "animations": [],
            "sounds": []
        }

        # Generate only affected components
        if "character_classes" in affected_components:
            print("Regenerating character classes...")
            char_files = game_code_generator.generate_all_from_dsl(new_dsl)["character_classes"]
            generated_files["character_classes"].extend(char_files)
            
            # Update registry
            if "gameplay" in new_dsl and "characters" in new_dsl["gameplay"]:
                for char in new_dsl["gameplay"]["characters"]:
                    char_name = char.get("name", "UnknownCharacter")
                    registry["character_classes"][char_name] = [f for f in char_files if char_name.lower() in f.lower()]

        if "ability_classes" in affected_components:
            print("Regenerating ability classes...")
            ab_files = game_code_generator.generate_all_from_dsl(new_dsl)["ability_classes"]
            generated_files["ability_classes"].extend(ab_files)
            
            # Update registry
            if "gameplay" in new_dsl and "abilities" in new_dsl["gameplay"]:
                for ab in new_dsl["gameplay"]["abilities"]:
                    ab_name = ab.get("name", "UnknownAbility")
                    registry["ability_classes"][ab_name] = [f for f in ab_files if ab_name.lower() in f.lower()]

        if "environment_meshes" in affected_components or "npc_meshes" in affected_components:
            print("Regenerating mesh assets...")
            asset_results = asset_generator.generate_assets_from_dsl(new_dsl)
            
            if "environment_meshes" in affected_components and "meshes" in asset_results:
                generated_files["meshes"].extend([f for f in asset_results["meshes"] if "Environment" in f or "level" in f.lower()])
                
            if "npc_meshes" in affected_components and "meshes" in asset_results:
                generated_files["meshes"].extend([f for f in asset_results["meshes"] if "NPC" in f or "Character" in f])
                
            # Update registry
            if "world" in new_dsl:
                if "levels" in new_dsl["world"]:
                    for level in new_dsl["world"]["levels"]:
                        level_name = level.get("name", "UnknownLevel")
                        registry["meshes"][level_name] = [f for f in asset_results.get("meshes", []) if level_name.lower() in f.lower()]
                        
                if "npcs" in new_dsl["world"]:
                    for npc in new_dsl["world"]["npcs"]:
                        npc_name = npc.get("name", "UnknownNPC")
                        registry["meshes"][f"npc_{npc_name}"] = [f for f in asset_results.get("meshes", []) if npc_name.lower() in f.lower()]

        if "ui_widgets" in affected_components:
            print("Regenerating UI widgets...")
            widget_files = game_code_generator.generate_all_from_dsl(new_dsl)["ui_widgets"]
            generated_files["ui_widgets"].extend(widget_files)

        if "music_sounds" in affected_components or "sfx_sounds" in affected_components:
            print("Regenerating audio assets...")
            asset_results = asset_generator.generate_assets_from_dsl(new_dsl)
            
            if "music_sounds" in affected_components and "sounds" in asset_results:
                generated_files["sounds"].extend([f for f in asset_results["sounds"] if "Music" in f or "music_cue" in f.lower()])
                
            if "sfx_sounds" in affected_components and "sounds" in asset_results:
                generated_files["sounds"].extend([f for f in asset_results["sounds"] if "SFX" in f or "sound_effect" in f.lower()])

        # Save updated registry
        self.save_asset_registry(registry)

        return generated_files

    def incrementally_generate_with_graph(self, old_dsl: Dict[str, Any], new_dsl: Dict[str, Any], 
                                          game_code_generator, asset_generator, affected_files: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Incrementally generate only affected components based on knowledge graph analysis."""
        print(f"Using knowledge graph to regenerate {len(affected_files)} categories of files...")
        
        # Load existing asset registry
        registry = self.load_asset_registry()
        
        generated_files = {
            "character_classes": [],
            "ability_classes": [],
            "effect_classes": [],
            "behavior_trees": [],
            "ui_widgets": [],
            "replication_rules": [],
            "ship_classes": [],
            "combat_components": [],
            "ai_files": [],
            "economy_data": [],
            "quantum_travel_files": [],
            "planet_generation_files": [],
            "game_mode_class": [],
            "level_creation_script": [],
            "pcg_asset_creation_script": []
        }

        # Generate only affected components based on graph analysis
        if "combat_components" in affected_files and affected_files["combat_components"]:
            print(f"Regenerating combat components: {affected_files['combat_components']}")
            all_gen_files = game_code_generator.generate_all_from_dsl(new_dsl)
            for comp_file in affected_files["combat_components"]:
                if comp_file in str(all_gen_files).replace("'", "").replace('"', '') or any(comp_file.lower() in f.lower() for cat_files in all_gen_files.values() for f in (cat_files if isinstance(cat_files, list) else [])):
                    generated_files.setdefault("combat_components", []).append(comp_file)

        if "ai_files" in affected_files and affected_files["ai_files"]:
            print(f"Regenerating AI files: {affected_files['ai_files']}")
            all_gen_files = game_code_generator.generate_all_from_dsl(new_dsl)
            for ai_file in affected_files["ai_files"]:
                if any(ai_file.lower() in f.lower() for cat_files in all_gen_files.values() for f in (cat_files if isinstance(cat_files, list) else [])):
                    generated_files.setdefault("ai_files", []).append(ai_file)

        if "economy_data" in affected_files and affected_files["economy_data"]:
            print(f"Regenerating economy data: {affected_files['economy_data']}")
            for eco_file in affected_files["economy_data"]:
                generated_files.setdefault("economy_data", []).append(eco_file)

        if "planet_generation_files" in affected_files and affected_files["planet_generation_files"]:
            print(f"Regenerating planet generation files: {affected_files['planet_generation_files']}")
            for pg_file in affected_files["planet_generation_files"]:
                generated_files.setdefault("planet_generation_files", []).append(pg_file)

        if "pcg_asset_creation_script" in affected_files and affected_files["pcg_asset_creation_script"]:
            print(f"Regenerating PCG asset creation script: {affected_files['pcg_asset_creation_script']}")
            for pcg_file in affected_files["pcg_asset_creation_script"]:
                generated_files.setdefault("pcg_asset_creation_script", []).append(pcg_file)

        if "level_creation_script" in affected_files and affected_files["level_creation_script"]:
            print(f"Regenerating level creation script: {affected_files['level_creation_script']}")
            for lc_file in affected_files["level_creation_script"]:
                generated_files.setdefault("level_creation_script", []).append(lc_file)

        if "game_mode_class" in affected_files and affected_files["game_mode_class"]:
            print(f"Regenerating game mode class: {affected_files['game_mode_class']}")
            for gm_file in affected_files["game_mode_class"]:
                generated_files.setdefault("game_mode_class", []).append(gm_file)

        # Save updated registry
        self.save_asset_registry(registry)

        return generated_files
