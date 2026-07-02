"""
Build Validator - Reverse-maps compilation errors from UBT/UAT back to DSL specification blocks.

When UBT or UAT fails, error messages reference generated C++ files and line numbers.
This validator reverse-maps those back to the DSL blocks that produced them, so users see
meaningful error messages like "Dash ability cooldown specification caused error" 
instead of raw compiler output.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class BuildValidator:
    """Validator for reverse-mapping build errors to DSL blocks."""

    def __init__(self):
        self.file_to_dsl_mapping: Dict[str, Dict[str, Any]] = {}

    def register_generated_files(self, dsl_data: Dict[str, Any], generated_files: Dict[str, List[str]]) -> None:
        """Register mapping between generated files and DSL blocks."""
        self.file_to_dsl_mapping = {}

        # Map character classes to character definitions in DSL
        if "character_classes" in generated_files:
            for file_path in generated_files["character_classes"]:
                self.file_to_dsl_mapping[file_path] = {
                    "type": "character_class",
                    "dsl_block": "gameplay.character",
                    "context": "Character class generation from DSL gameplay character block"
                }

        # Map ability classes to ability definitions in DSL
        if "ability_classes" in generated_files:
            for file_path in generated_files["ability_classes"]:
                # Extract ability name from file path (e.g., GA_Dash.cpp -> Dash)
                file_name = Path(file_path).stem
                ability_name = self._extract_ability_name(file_name)
                
                self.file_to_dsl_mapping[file_path] = {
                    "type": "ability_class",
                    "dsl_block": f"gameplay.ability.{ability_name}",
                    "context": f"Ability class generation from DSL gameplay.abilities block for '{ability_name}'"
                }

        # Map effect classes to effect definitions
        if "effect_classes" in generated_files:
            for file_path in generated_files["effect_classes"]:
                self.file_to_dsl_mapping[file_path] = {
                    "type": "effect_class",
                    "dsl_block": "gameplay.effects",
                    "context": "Effect class generation from DSL gameplay block"
                }

        # Map behavior trees to NPC or level definitions
        if "behavior_trees" in generated_files:
            for file_path in generated_files["behavior_trees"]:
                self.file_to_dsl_mapping[file_path] = {
                    "type": "behavior_tree",
                    "dsl_block": "world.npc or world.level",
                    "context": "Behavior tree generation from DSL world block"
                }

        # Map UI widgets to UI definitions
        if "ui_widgets" in generated_files:
            for file_path in generated_files["ui_widgets"]:
                self.file_to_dsl_mapping[file_path] = {
                    "type": "ui_widget",
                    "dsl_block": "ui.hud or ui.pause_menu",
                    "context": "UI widget generation from DSL ui block"
                }

    def _extract_ability_name(self, file_name: str) -> str:
        """Extract ability name from generated C++ file name."""
        # Remove common prefixes like GA_, AB_, etc.
        name = re.sub(r'^(GA_|AB_|Ability_)', '', file_name)
        
        # Convert PascalCase to readable format
        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        name = name.replace('_', ' ').strip()
        
        return name or "Unknown Ability"

    def parse_build_error(self, error_output: str) -> List[Dict[str, Any]]:
        """
        Parse UBT/UAT error output and extract file/line references.
        
        Returns list of errors with file path, line number, and error message.
        """
        errors = []
        
        # Pattern 1: CS####: Syntax error messages (C# compiler errors in .Build.cs files)
        # Example: EchoesOfEternity.Build.cs(4,21): error CS1514: { expected
        csharp_pattern = r'([^\s\(\)]+\.cs)\((\d+),(\d+)\):\s+(error\s+\w+:?\s+.+)'
        
        for match in re.finditer(csharp_pattern, error_output):
            file_path = match.group(1)
            line_num = int(match.group(2))
            error_msg = match.group(4)
            
            errors.append({
                "file": file_path,
                "line": line_num,
                "column": int(match.group(3)),
                "message": error_msg,
                "type": "csharp_compiler"
            })

        # Pattern 2: C++ compiler errors (MSVC/Clang)
        # Example: EchoesOfEternityCharacter.cpp(45): error C2065: 'DashAbility' undeclared identifier
        cpp_pattern = r'([^\s\(\)]+\.cpp?)\((\d+)\):\s+(error\s+C\d+:\s+.+|warning\s+C\d+:\s+.+)'
        
        for match in re.finditer(cpp_pattern, error_output):
            file_path = match.group(1)
            line_num = int(match.group(2))
            error_msg = match.group(3)
            
            errors.append({
                "file": file_path,
                "line": line_num,
                "column": None,
                "message": error_msg,
                "type": "cpp_compiler"
            })

        # Pattern 3: UHT (Unreal Header Tool) errors
        # Example: C:\path\to\EchoesOfEternityAbility.cpp(12): Error: Missing UCLASS macro
        uht_pattern = r'([^\s\(\)]+\.(cpp|h))\((\d+)\):\s+(Error|Warning|Fatal):\s+.+'
        
        for match in re.finditer(uht_pattern, error_output):
            file_path = match.group(1)
            line_num = int(match.group(2))
            error_type = match.group(3)
            error_msg = match.group(4) if len(match.groups()) > 4 else "UHT error"
            
            errors.append({
                "file": file_path,
                "line": line_num,
                "column": None,
                "message": f"{error_type}: {error_msg}",
                "type": "uht_error"
            })

        # Pattern 4: UnrealBuildTool Rules errors
        # Example: Couldn't find target rules file for target 'EchoesOfEternityEditor' in rules assembly
        if "RulesError" in error_output or "Could not find definition for module" in error_output:
            errors.append({
                "file": "Build.cs or Target.cs",
                "line": None,
                "column": None,
                "message": error_output.split("Result: Failed")[0].strip() if "Result: Failed" in error_output else error_output,
                "type": "rules_error"
            })

        return errors

    def map_errors_to_dsl(self, errors: List[Dict[str, Any]], dsl_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Map parsed build errors back to DSL specification blocks.
        
        Returns enhanced error list with DSL context for each error.
        """
        mapped_errors = []

        for error in errors:
            file_path = error.get("file", "")
            
            # Try to find matching DSL block from registered files
            dsl_context = None
            for registered_file, mapping in self.file_to_dsl_mapping.items():
                # Check if error file path contains the registered file name
                error_file_name = Path(file_path).name
                
                if registered_file in file_path or error_file_name in registered_file:
                    dsl_context = mapping
                    break
            
            # If no specific file match, try to infer from error message content
            if not dsl_context:
                error_msg = error.get("message", "").lower()
                
                if "dash" in error_msg or "ga_dash" in error_msg:
                    dsl_context = {
                        "type": "ability_class",
                        "dsl_block": "gameplay.ability.Dash",
                        "context": "Dash ability specification from DSL gameplay.abilities block"
                    }
                elif "attack" in error_msg or "ga_attack" in error_msg:
                    dsl_context = {
                        "type": "ability_class",
                        "dsl_block": "gameplay.ability.Attack",
                        "context": "Attack ability specification from DSL gameplay.abilities block"
                    }
                elif "jump" in error_msg or "ga_jump" in error_msg:
                    dsl_context = {
                        "type": "ability_class",
                        "dsl_block": "gameplay.ability.Jump",
                        "context": "Jump ability specification from DSL gameplay.abilities block"
                    }
                elif "replicated" in error_msg or "repnotify" in error_msg or "rpc" in error_msg:
                    dsl_context = {
                        "type": "replication_rules",
                        "dsl_block": "technical.replication",
                        "context": "Replication specification from DSL technical.replication block"
                    }
                elif "uclass" in error_msg or "uproperty" in error_msg or "ufunction" in error_msg:
                    dsl_context = {
                        "type": "c++_macros",
                        "dsl_block": "gameplay.character or gameplay.ability",
                        "context": "Unreal reflection macro specification from DSL character/ability blocks"
                    }

            # Create mapped error with DSL context
            mapped_error = {
                "original_error": error,
                "dsl_context": dsl_context
            }
            
            # Generate user-friendly error message
            if dsl_context:
                mapped_error["user_message"] = (
                    f"[{error['type'].upper()}] {dsl_context['context']}\n"
                    f"DSL Block: {dsl_context['dsl_block']}\n"
                    f"File Reference: {error['file']}:{error.get('line', 'N/A')}\n"
                    f"Error Details: {error['message']}"
                )
            else:
                mapped_error["user_message"] = (
                    f"[{error['type'].upper()}] File Reference: {error['file']}:{error.get('line', 'N/A')}\n"
                    f"Error Details: {error['message']}"
                )
            
            mapped_errors.append(mapped_error)

        return mapped_errors

    def generate_validation_report(self, dsl_data: Dict[str, Any], generated_files: Dict[str, List[str]], 
                                   build_success: bool, error_output: str = None) -> Dict[str, Any]:
        """
        Generate validation report with error mapping if build failed.
        
        Returns dict with validation results and mapped errors.
        """
        self.register_generated_files(dsl_data, generated_files)

        report = {
            "build_success": build_success,
            "mapped_errors": [],
            "dsl_blocks_affected": set()
        }

        if not build_success and error_output:
            # Parse errors from build output
            raw_errors = self.parse_build_error(error_output)
            
            # Map to DSL blocks
            mapped_errors = self.map_errors_to_dsl(raw_errors, dsl_data)
            report["mapped_errors"] = mapped_errors
            
            # Track affected DSL blocks
            for mapped_err in mapped_errors:
                if mapped_err.get("dsl_context"):
                    report["dsl_blocks_affected"].add(mapped_err["dsl_context"]["dsl_block"])

        return report


# Global build validator instance
build_validator = BuildValidator()
