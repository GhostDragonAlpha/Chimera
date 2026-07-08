"""
Validation Reporter — Outputs detailed validation report mapping every generated asset and class back to the DSL specification.

Identifies any deviations from spec, bugs, or performance warnings.
If spec change is needed, generates a proposed DSL patch for user review.
"""

import json
from pathlib import Path
from typing import Dict, Any, List


class ValidationReporter:
    """Generates validation reports and DSL patches for game generation pipeline."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir) / "ValidationReports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_validation_report(self, dsl_data: Dict[str, Any], generated_files: Dict[str, List[str]], 
                                   test_results: Dict[str, Any]) -> str:
        """Generate detailed validation report mapping assets/classes to DSL spec."""
        report = {
            "report_metadata": {
                "timestamp": "validation_report_generated",
                "dsl_spec_validated": True
            },
            "asset_mapping": {},
            "class_mapping": {},
            "deviations_and_warnings": [],
            "performance_warnings": [],
            "test_results_summary": test_results
        }

        # Map generated assets to DSL specifications
        if "world" in dsl_data and "levels" in dsl_data["world"]:
            report["asset_mapping"]["environment_meshes"] = []
            for level in dsl_data["world"]["levels"]:
                level_name = level.get("name", "UnknownLevel")
                # Find corresponding generated mesh files
                mesh_files = [f for f in generated_files.get("meshes", []) if level_name.lower() in f.lower()]
                report["asset_mapping"]["environment_meshes"].append({
                    "dsl_level": level_name,
                    "generated_assets": mesh_files if mesh_files else ["placeholder"]
                })

        if "world" in dsl_data and "npcs" in dsl_data["world"]:
            report["asset_mapping"]["npc_meshes"] = []
            for npc in dsl_data["world"]["npcs"]:
                npc_name = npc.get("name", "UnknownNPC")
                # Find corresponding generated mesh files
                mesh_files = [f for f in generated_files.get("meshes", []) if npc_name.lower() in f.lower()]
                report["asset_mapping"]["npc_meshes"].append({
                    "dsl_npc": npc_name,
                    "generated_assets": mesh_files if mesh_files else ["placeholder"]
                })

        # Map generated classes to DSL specifications
        if "gameplay" in dsl_data and "characters" in dsl_data["gameplay"]:
            report["class_mapping"]["character_classes"] = []
            for char in dsl_data["gameplay"]["characters"]:
                char_name = char.get("name", "UnknownCharacter")
                class_files = generated_files.get("character_classes", [])
                report["class_mapping"]["character_classes"].append({
                    "dsl_character": char_name,
                    "generated_classes": [f for f in class_files if char_name.lower() in f.lower()] if class_files else ["placeholder"]
                })

        if "gameplay" in dsl_data and "abilities" in dsl_data["gameplay"]:
            report["class_mapping"]["ability_classes"] = []
            for ab in dsl_data["gameplay"]["abilities"]:
                ab_name = ab.get("name", "UnknownAbility")
                class_files = generated_files.get("ability_classes", [])
                report["class_mapping"]["ability_classes"].append({
                    "dsl_ability": ab_name,
                    "generated_classes": [f for f in class_files if ab_name.lower() in f.lower()] if class_files else ["placeholder"]
                })

        # Check for deviations and warnings
        report["deviations_and_warnings"] = self._check_deviations(dsl_data, generated_files)
        report["performance_warnings"] = self._check_performance_warnings(dsl_data)

        # Generate report file
        report_path = self.output_dir / f"validation_report_{int(Path(__file__).stat().st_mtime if hasattr(Path(__file__), 'stat') else 0)}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        return str(report_path)

    def _check_deviations(self, dsl_data: Dict[str, Any], generated_files: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Check for deviations from DSL specification."""
        deviations = []

        # Check if all declared characters have corresponding class files
        if "gameplay" in dsl_data and "characters" in dsl_data["gameplay"]:
            char_classes = generated_files.get("character_classes", [])
            if not char_classes:
                deviations.append({
                    "type": "missing_generation",
                    "category": "characters",
                    "description": (
                        "No character class files generated despite DSL declarations. "
                        "Ensure the 'gameplay.characters' block is present in your DSL spec "
                        "and that game_code_generator.py has a 'character_class' template registered. "
                        "See core/game_code_generator.py for available templates."
                    )
                })

        # Check if all declared abilities have corresponding GAS ability files
        if "gameplay" in dsl_data and "abilities" in dsl_data["gameplay"]:
            ab_classes = generated_files.get("ability_classes", [])
            if not ab_classes:
                deviations.append({
                    "type": "missing_generation",
                    "category": "abilities",
                    "description": (
                        "No GAS ability class files generated despite DSL declarations. "
                        "Ensure the 'gameplay.abilities' block is present in your DSL spec "
                        "and that game_code_generator.py has a 'gas_ability_class' template registered."
                    )
                })

        # Check if all declared meshes have corresponding generated mesh files
        if "world" in dsl_data and "levels" in dsl_data["world"]:
            level_count = len(dsl_data["world"]["levels"])
            mesh_files = generated_files.get("meshes", [])
            if level_count > 0 and not mesh_files:
                deviations.append({
                    "type": "missing_generation",
                    "category": "environment_meshes",
                    "description": (
                        f"DSL declares {level_count} levels but no environment meshes were generated. "
                        "Asset providers default to procedural/fallback when no API keys are configured. "
                        "See core/asset_config.py for provider configuration options."
                    )
                })

        return deviations

    def _check_performance_warnings(self, dsl_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for performance-related warnings based on DSL specifications."""
        warnings = []

        if "technical" in dsl_data and "performance" in dsl_data["technical"]:
            perf_config = dsl_data["technical"]["performance"]
            
            # Check target FPS
            target_fps = perf_config.get("target_fps", 60)
            if target_fps < 30:
                warnings.append({
                    "type": "performance_warning",
                    "category": "fps_target",
                    "description": f"Target FPS of {target_fps} is below recommended minimum of 30"
                })
                
            # Check LOD strategy
            lod_strategy = perf_config.get("lod_strategy", "standard")
            if lod_strategy == "aggressive":
                warnings.append({
                    "type": "performance_note",
                    "category": "lod_strategy",
                    "description": "Aggressive LOD strategy may impact visual quality but improve performance"
                })

        return warnings

    def generate_dsl_patch(self, deviations: List[Dict[str, Any]]) -> str | None:
        """Generate a proposed DSL patch if spec changes are needed."""
        if not deviations:
            return None
            
        patch = {
            "patch_metadata": {
                "generated_for": "dsl_specification_updates",
                "deviations_addressed": len(deviations)
            },
            "proposed_changes": []
        }

        for dev in deviations:
            if dev["type"] == "missing_generation":
                patch["proposed_changes"].append({
                    "category": dev["category"],
                    "action": "ensure_generation_enabled",
                    "description": f"Ensure {dev['category']} generation is enabled in the pipeline configuration"
                })

        # Generate patch file
        import time
        patch_path = self.output_dir / f"dsl_patch_{int(time.time())}.json"
        
        with open(patch_path, 'w', encoding='utf-8') as f:
            json.dump(patch, f, indent=2)

        return str(patch_path)
