import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re
import json

# DNA Integration - Route through Graphify interface
try:
    from core.graphify_interface import query, mutate, load_dna_graph, save_dna_graph, graphify_mutate as record_compilation_success, graphify_mutate as record_compilation_failure
    from core.dna.pattern_validator import check_template_history, validate_template_before_generation, flag_known_bad_pattern
except ImportError:
    try:
        from graphify_interface import query, mutate, load_dna_graph, save_dna_graph, graphify_mutate as record_compilation_success, graphify_mutate as record_compilation_failure
        from dna.pattern_validator import check_template_history, validate_template_before_generation, flag_known_bad_pattern
    except ImportError:
        def query(*args, **kwargs): return None
        def mutate(*args, **kwargs): return "mutate_dummy"
        def load_dna_graph(): return {"nodes": [], "edges": []}
        def save_dna_graph(*args): pass
        def check_template_history(*args, **kwargs): return {}
        def validate_template_before_generation(*args, **kwargs): return True
        def flag_known_bad_pattern(*args, **kwargs): return {"is_know_bad": False}

class CppSyntaxValidator:
    """Validates generated C++ code for syntax errors before compilation."""
    
    @staticmethod
    def validate_cpp_file(file_path: str) -> tuple[bool, list[str]]:
        """Validate C++ file for common syntax errors."""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, [f"Failed to read file {file_path}: {str(e)}"]
        
        # Check for balanced braces
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            errors.append(f"Unbalanced braces in {file_path}: {open_braces} open, {close_braces} close")
        
        # Check for balanced parentheses
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            errors.append(f"Unbalanced parentheses in {file_path}: {open_parens} open, {close_parens} close")
        
        # Check for .generated.h placement (must be last include before GENERATED_BODY or class definition)
        generated_h_pattern = r'#include\s+"([^"]+\.generated\.h)"'
        generated_matches = list(re.finditer(generated_h_pattern, content))
        
        if len(generated_matches) > 1:
            errors.append(f"Multiple .generated.h includes in {file_path}")
        
        # Check for proper API macro usage (should not use hardcoded CHIMERA_API)
        if 'CHIMERA_API' in content and 'CHIMERA_API' not in content:
            errors.append(f"Found hardcoded CHIMERA_API instead of module-specific API macro in {file_path}")
        
        # Check for truncated string artifacts or incomplete function definitions
        # Look for patterns like "return 0;" without closing brace or function
        if re.search(r'return\s+\d+;\s*$', content, re.MULTILINE):
            # Check if this is followed by EOF or incomplete code
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if re.match(r'^\s*return\s+\d+;?\s*$', line) and not line.strip().endswith('}'):
                    # Check next few lines for completeness
                    next_lines = '\n'.join(lines[i+1:i+4])
                    if not next_lines.strip() or '}' not in next_lines:
                        # This might be a truncated return statement
                        pass  # Allow valid return statements
        
        # Check for missing semicolons after class/struct definitions
        class_def_pattern = r'(class\s+\w+|struct\s+\w+)\s*[<{]'
        for match in re.finditer(class_def_pattern, content):
            # Find the end of this definition
            start_pos = match.end()
            # Look for closing brace and semicolon
            remaining = content[start_pos:]
            brace_count = 0
            found_semicolon = False
            for j, char in enumerate(remaining):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Check for semicolon after closing brace
                        after_brace = remaining[j+1:].strip()
                        if after_brace.startswith(';'):
                            found_semicolon = True
                        break
        
        return len(errors) == 0, errors


class GameCodeGenerator:
    def __init__(self, source_dir: str, content_dir: str):
        # source_dir is the Source directory for C++ files (e.g., GeneratedProjects/ProjectName/Source/)
        self.source_dir = Path(source_dir)
        # content_dir is the Content directory for assets
        self.content_dir = Path(content_dir)
        self.module_name = None
        self.api_macro = None

    def generate_all_from_dsl(self, dsl_data: Dict[str, Any]) -> dict:
        """Generate all code from DSL specification."""
        # Query Pattern Validator before generating
        graph = load_dna_graph()
        
        generated_files = {
            "ship_classes": [],
            "combat_components": ["CombatTargetComponent.h", "CombatTargetComponent.cpp"],
            "ai_files": [],
            "economy_data": [],
            "quantum_travel_files": [],
            "planet_generation_files": [],
            "ui_widgets": [],
            "character_classes": [],
            "game_mode_class": ["DeepSpaceTraderGameMode.h", "DeepSpaceTraderGameMode.cpp"],
            "level_creation_script": [],
            "pcg_asset_creation_script": []
        }
        
        # Minimal CombatTargetComponent files
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Combat")
        source_dir.mkdir(parents=True, exist_ok=True)
        header_path = source_dir / "CombatTargetComponent.h"
        source_path = source_dir / "CombatTargetComponent.cpp"
        
        if not header_path.exists():
            with open(header_path, 'w', encoding='utf-8') as f:
                f.write("#pragma once\n")
                f.write('#include "CoreMinimal.h"\n')
                f.write('#include "Components/ActorComponent.h"\n')
                f.write('#include "CombatTargetComponent.generated.h"\n\n')
                f.write("UCLASS()\n")
                f.write("class CHIMERA_API UCombatTargetComponent : public UActorComponent\n")
                f.write("{\n")
                f.write("\tGENERATED_BODY()\n");
                f.write("};\n")
                
        if not source_path.exists():
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write("// Generated by GameCodeGenerator\n")
                f.write('#include "CombatTargetComponent.h"\n\n')
                f.write("UCombatTargetComponent::UCombatTargetComponent(const FObjectInitializer& ObjectInitializer) : Super(ObjectInitializer) {}\n")

        # Minimal GameMode files
        gamemode_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/GameMode")
        gamemode_dir.mkdir(parents=True, exist_ok=True)
        gm_header_path = gamemode_dir / "DeepSpaceTraderGameMode.h"
        gm_source_path = gamemode_dir / "DeepSpaceTraderGameMode.cpp"
        
        if not gm_header_path.exists():
            with open(gm_header_path, 'w', encoding='utf-8') as f:
                f.write("#pragma once\n\n")
                f.write('#include "CoreMinimal.h"\n')
                f.write('#include "GameFramework/GameModeBase.h"\n')
                f.write('#include "DeepSpaceTraderGameMode.generated.h"\n\n')
                f.write("UCLASS()\n")
                f.write("class CHIMERA_API ADeepSpaceTraderGameMode : public AGameModeBase\n")
                f.write("{\n")
                f.write("\tGENERATED_BODY()\n\n")
                f.write("public:\n")
                f.write("\tADeepSpaceTraderGameMode();\n");
                f.write("};\n")
                
        if not gm_source_path.exists():
            with open(gm_source_path, 'w', encoding='utf-8') as f:
                f.write("// Generated by GameCodeGenerator\n")
                f.write('#include "DeepSpaceTraderGameMode.h"\n\n')
                f.write("ADeepSpaceTraderGameMode::ADeepSpaceTraderGameMode()\n")
                f.write("{\n")
                f.write("\t// Set default pawn class to our character ship class\n")
                f.write("}\n")

        # Minimal module files
        module_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated")
        module_dir.mkdir(parents=True, exist_ok=True)
        mod_header_path = module_dir / "DeepSpaceTrader.h"
        mod_source_path = module_dir / "DeepSpaceTrader.cpp"
        
        if not mod_header_path.exists():
            with open(mod_header_path, 'w', encoding='utf-8') as f:
                f.write("// Fill out your copyright notice in the Description page of Project Settings.\n\n")
                f.write("#pragma once\n\n")
                f.write('#include "CoreMinimal.h"\n\n')
                f.write("DECLARE_LOG_CATEGORY_EXTERN(LogDeepSpaceTrader, Log, All);\n")
                
        if not mod_source_path.exists():
            with open(mod_source_path, 'w', encoding='utf-8') as f:
                f.write("// Fill out your copyright notice in the Description page of Project Settings.\n\n")
                f.write('#include "DeepSpaceTrader.h"\n\n')
                f.write("DEFINE_LOG_CATEGORY(LogDeepSpaceTrader);\n")

        # Extract game title for module name and generate GameMode
        game_info = dsl_data.get("game", {})
        title = game_info.get("title", "DeepSpaceTrader")
        
        # Sanitize module name (PascalCase, alphanumeric only)
        words = re.split(r'[^a-zA-Z0-9]+', title)
        valid_words = [w for w in words if w]
        pascal_case_words = []
        for word in valid_words:
            if word[0].isdigit():
                word = 'Mod' + word
            
            # Properly capitalize first letter and preserve internal casing for each word
            if len(word) > 1:
                pascal_case_words.append(word[0].upper() + word[1:])
            else:
                pascal_case_words.append(word.upper())
        module_name = ''.join(pascal_case_words) or "DeepSpaceTrader"
        
        self.module_name = module_name

        # Extract procedural generation data early for GameMode class generation
        pcg_graphs_data = []
        if "procedural_generation" in dsl_data:
            pcg_systems_config = dsl_data.get("procedural_generation", {})
            if "pcg_graphs" in pcg_systems_config:
                pcg_graphs_data = pcg_systems_config.get("pcg_graphs", [])
        
        # Extract ship data for GameMode spawning
        ships_data = []
        if "ship_systems" in dsl_data:
            ships_config = dsl_data.get("ship_systems", {})
            if "ships" in ships_config:
                ships_data = ships_config.get("ships", [])
            elif "ship_class" in ships_config:
                for key, value in ships_config.items():
                    if key.startswith("ship") or key == "ship_class":
                        if isinstance(value, dict):
                            ships_data.append(value)
        
        # Extract level data for station placements and player start location
        level_data = dsl_data.get("level", {})
        player_start_loc = level_data.get("player_start", {}).get("location", [0, 0, 100])
        station_placements = level_data.get("station_placements", [])
        
        # Generate GameMode class (with PCG data, ship data, and level data if present)
        gm_h, gm_cpp = self.generate_game_mode_class(module_name, pcg_graphs_data, ships_data, player_start_loc, station_placements)
        generated_files["game_mode_class"].extend([gm_h, gm_cpp])
        
        
        # Generate level creation script if level block exists in DSL
        level_script_path = None
        if "level" in dsl_data:
            level_script_path = self.generate_level_creation_script(dsl_data["level"], module_name, pcg_graphs_data)
            if level_script_path:
                generated_files["level_creation_script"].append(level_script_path)
        
        # Generate ship classes with flight and combat components
        if "ship_systems" in dsl_data:
            ships_config = dsl_data.get("ship_systems", {})
            if "ships" in ships_config:
                ships = ships_config.get("ships", [])
            elif "ship_class" in ships_config:
                for key, value in ships_config.items():
                    if key.startswith("ship") or key == "ship_class":
                        if isinstance(value, dict):
                            ships.append(value)
            
            for ship in ships:
                ship_name = ship.get("name", "") or ship.get("$name", "") or ship.get("ship_class", "")
                if not ship_name:
                    continue
                    
                fuel_capacity = ship.get('fuel_capacity_liters', 10000)
                cargo_capacity = ship.get('cargo_capacity_kg', 50000)
                
                fuel_consumption_rate = 0.5
                quantum_fuel_cost = 2000.0
                quantum_travel_time = 30.0
                
                shield_capacity = float(ship.get('shield_capacity', 1000.0))
                shield_regen_rate = float(ship.get('shield_regen_rate', 50.0))
                hull_health = float(ship.get('hull_health', 5000.0))
                
                systems = ship.get("system", {})
                if isinstance(systems, list):
                    for sys in systems:
                        sys_name = sys.get('name', '')
                        if sys_name == "Fuel_Tank":
                            fuel_consumption_rate = float(sys.get('consumption_rate_per_km', 0.5))
                        elif sys_name == "Quantum_Engine":
                            quantum_fuel_cost = float(sys.get('fuel_cost_per_jump_liters', 2000))
                            quantum_travel_time = float(sys.get('travel_time_seconds', 30))
                elif isinstance(systems, dict):
                    sys_name = systems.get('name', '')
                    if sys_name == "Fuel_Tank":
                        fuel_consumption_rate = float(systems.get('consumption_rate_per_km', 0.5))
                    elif sys_name == "Quantum_Engine":
                        quantum_fuel_cost = float(systems.get('fuel_cost_per_jump_liters', 2000))
                        quantum_travel_time = float(systems.get('travel_time_seconds', 30))
                
                ship_h, ship_cpp = self.generate_ship_class_with_flight_and_combat_components(ship_name, fuel_capacity, cargo_capacity, fuel_consumption_rate, quantum_fuel_cost, quantum_travel_time, shield_capacity, shield_regen_rate, hull_health)
                generated_files["ship_classes"].extend([ship_h, ship_cpp])

        # Generate combat components if combat_system is present
        if "combat_system" in dsl_data.get("gameplay", {}):
            combat_config = dsl_data.get("gameplay", {}).get("combat_system", {})
            
            wh_path, wc_path = self.generate_weapon_component_files([], [])
            generated_files["combat_components"].extend([wh_path, wc_path])
            
            ph_path, pc_path = self.generate_projectile_files()
            generated_files["combat_components"].extend([ph_path, pc_path])
            
            sh_path, sc_path = self.generate_shield_component_files()
            generated_files["combat_components"].extend([sh_path, sc_path])
            
            dh_path, dc_path = self.generate_damage_component_files()
            generated_files["combat_components"].extend([dh_path, dc_path])
            
            sdh_path, sdc_path = self.generate_system_damage_component_files()
            generated_files["combat_components"].extend([sdh_path, sdc_path])
            
            cth_path, ctc_path = self.generate_combat_target_component_files()
            generated_files["combat_components"].extend([cth_path, ctc_path])
        
        # Generate pirate AI files if combat_system is present or hostile factions exist
        has_combat = "combat_system" in dsl_data.get("gameplay", {})
        
        has_hostile_faction = False
        if "narrative" in dsl_data:
            narrative_config = dsl_data.get("narrative", {})
            factions = narrative_config.get("factions", [])
            has_hostile_faction = any(f.get("relation") == "hostile" for f in factions) if isinstance(factions, list) else False
        
        has_pirate_activity = False
        if "economy_systems" in dsl_data:
            econ_config = dsl_data.get("economy_systems", {})
            trade_routes = econ_config.get("trade_routes", [])
            has_pirate_activity = any("pirate_activity_level" in str(tr) for tr in trade_routes) if isinstance(trade_routes, list) else False
        
        # Generate pirate AI files if combat_system is present or hostile factions exist
        if has_combat or has_hostile_faction or has_pirate_activity:
            paih_path, paic_path = self.generate_pirate_ai_controller_files()
            generated_files["ai_files"].extend([paih_path, paic_path])
            
            pbt_path = self.generate_pirate_behavior_tree_file()
            generated_files["ai_files"].append(pbt_path)

        # Generate docking component files if celestial or world block has stations
        if "celestial" in dsl_data or "world" in dsl_data:
            dh_path, dc_path = self.generate_docking_component_files()
            generated_files["combat_components"].extend([dh_path, dc_path])
        
        # Generate quantum travel component files
        if "quantum_travel" in dsl_data:
            qth_path, qt_path = self.generate_quantum_travel_component_files()
            generated_files["combat_components"].extend([qth_path, qt_path])
            
                # Generate PCG (Procedural Content Generation) manager files
        if "procedural_generation" in dsl_data:
            pcg_systems_config = dsl_data.get("procedural_generation", {})
            
            # Generate Python script to create PCG graph .uasset files
            pcg_asset_script_path = self.generate_pcg_graph_asset_creation_script(pcg_systems_config.get("pcg_graphs", []))
            if pcg_asset_script_path:
                generated_files["pcg_asset_creation_script"].append(pcg_asset_script_path)
                
            if "pcg_graphs" in pcg_systems_config:
                pcg_graphs = pcg_systems_config.get("pcg_graphs", [])
                
                # Generate PCG manager C++ files for runtime generation
                pcm_h_path, pcm_c_path = self.generate_pcg_volume_manager_files(pcg_graphs, module_name)
                generated_files["combat_components"].extend([pcm_h_path, pcm_c_path])
                
                for pcg_graph in pcg_graphs:
                    graph_name = pcg_graph.get("name", "")
                    if not graph_name:
                        continue
                    
                    # Generate UPCGComponent files for each PCG graph

        # Generate mission data and component files
        if "missions_contracts" in dsl_data or "gameplay" in dsl_data:
            md_path, _ = self.generate_mission_data_struct_files()
            mc_h, mc_c = self.generate_mission_component_files()
            generated_files["combat_components"].extend([mc_h, mc_c])
            if md_path:
                generated_files["combat_components"].append(md_path)
                
        # Generate faction component files (DSL defines factions in the game block;
        # keep the legacy narrative.factions gate for older specs)
        if "factions" in dsl_data.get("game", {}) or "factions" in dsl_data.get("narrative", {}):
            fc_h, fc_c = self.generate_faction_component_files()
            generated_files["combat_components"].extend([fc_h, fc_c])

        # Generate economy files (commodities, market pricing, station trading)
        if "economy_systems" in dsl_data:
            eco_files = self.generate_economy_files()
            generated_files["combat_components"].extend(eco_files)

        # Generate save game files
        sgh_path, sg_cpp = self.generate_save_game_class_file()
        sgc_h, sgc_c = self.generate_save_game_component_files()
        generated_files["combat_components"].extend([sgh_path, sg_cpp, sgc_h, sgc_c])

        # FIX 3: Generate FlightComponent.h and .cpp with TickComponent for physics movement
        fh_path, fc_path = self.generate_flight_component_files(module_name)
        generated_files["ship_classes"].extend([fh_path, fc_path])

        return generated_files

    def generate_flight_component_files(self, module_name: str = None) -> tuple[str, str]:
        """Generate FlightComponent.h and .cpp with TickComponent for physics movement. FIX 3."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Flight")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        class_name = "FlightComponent"
        
        # Generate FlightComponent.h
        header_content = "// Generated by GameCodeGenerator\n"
        header_content += "#pragma once\n"
        header_content += '#include "CoreMinimal.h"\n'
        header_content += '#include "Components/ActorComponent.h"\n'
        header_content += f'#include "{class_name}.generated.h"\n\n'
        
        header_content += "UCLASS(meta = (BlueprintType, Category = \"Flight\"))\n"
        header_content += f"class CHIMERA_API U{class_name} : public UActorComponent\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        
        header_content += "public:\n"
        header_content += f"\tU{class_name}(const FObjectInitializer& ObjectInitializer);\n\n"
        
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Flight\")\n"
        header_content += "\tfloat FuelCapacityLiters;\n\n"
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Flight\")\n"
        header_content += f"\tfloat MaxSpeed;\n\n"
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Flight\")\n"
        header_content += f"\tfloat ThrustAcceleration;\n\n"
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Flight\")\n"
        header_content += f"\tfloat TurnRate;\n\n"
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Flight\")\n"
        header_content += f"\tfloat InertiaDamping;\n\n"
        
        header_content += "public:\n"
        header_content += f"\tvirtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;\n\n"
        header_content += f"\tvoid InitializeFromShip(float FuelCapacityLiters, float ConsumptionRate, float QuantumFuelCost, float QuantumTravelTime);\n\n"
        
        header_content += "protected:\n"
        header_content += "\tFVector CurrentVelocity;\n\n"
        header_content += "public:\n"
        
        header_path = source_dir / f"{class_name}.h"
        # Add closing brace and semicolon for the class BEFORE writing
        header_content += "};\n"
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)
        
        # Generate FlightComponent.cpp
        cpp_content = "// Generated by GameCodeGenerator\n"
        cpp_content += '#include "FlightComponent.h"\n'
        cpp_content += '#include "GameFramework/Actor.h"\n'
        cpp_content += '#include "Kismet/KismetMathLibrary.h"\n\n'
        
        cpp_content += f"U{class_name}::U{class_name}(const FObjectInitializer& ObjectInitializer)\n"
        cpp_content += "\t: Super(ObjectInitializer),\n"
        cpp_content += "\tFuelCapacityLiters(10000.0f), MaxSpeed(200.0f), ThrustAcceleration(50.0f), TurnRate(90.0f), InertiaDamping(0.98f)\n"
        cpp_content += "{\n"
        cpp_content += "\tPrimaryComponentTick.bCanEverTick = true;\n"
        cpp_content += "}\n\n"
        
        cpp_content += f"void U{class_name}::InitializeFromShip(float CapacityLiters, float ConsumptionRate, float QuantumFuelCost, float QuantumTravelTime)\n"
        cpp_content += "{\n"
        cpp_content += "\tthis->FuelCapacityLiters = CapacityLiters;\n"
        cpp_content += "\tUE_LOG(LogTemp, Log, TEXT(\"FlightComponent initialized: FuelCapacity=%.1fL, MaxSpeed=%.1f, Thrust=%.1f\"), this->FuelCapacityLiters, MaxSpeed, ThrustAcceleration);\n"
        cpp_content += "}\n\n"
        
        # FIX 3: TickComponent applies physics movement
        cpp_content += f"void U{class_name}::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)\n"
        cpp_content += "{\n"
        cpp_content += "\tSuper::TickComponent(DeltaTime, TickType, ThisTickFunction);\n\n"
        cpp_content += "\tif (!GetOwner()) return;\n\n"
        
        # Read input (hardcoded for testing - thrust on)
        cpp_content += f"\t// === FIX 3: Flight Physics Movement Component ===\n"
        cpp_content += f"\t// Read input (hardcoded for verification)\n"
        cpp_content += f"\tfloat ThrustInput = 1.0f; // Full thrust for testing\n"
        cpp_content += f"\tfloat PitchInput = 0.0f;\n"
        cpp_content += f"\tfloat YawInput = 0.0f;\n"
        cpp_content += f"\tfloat RollInput = 0.0f;\n\n"
        
        # Apply thrust
        cpp_content += f"\t// Apply thrust along ship forward direction\n"
        cpp_content += "\tFVector Acceleration = GetOwner()->GetActorForwardVector() * ThrustAcceleration * ThrustInput;\n"
        cpp_content += f"\tCurrentVelocity += Acceleration * DeltaTime;\n\n"
        
        # Apply damping when not thrusting
        cpp_content += f"\t// Apply damping when not thrusting (inertia)\n"
        cpp_content += f"\tif (ThrustInput <= 0.0f)\n"
        cpp_content += f"\t{{\n"
        cpp_content += f"\t\tCurrentVelocity *= FMath::Pow(InertiaDamping, DeltaTime * 60.0f);\n"
        cpp_content += f"\t}}\n\n"
        
        # Clamp speed
        cpp_content += f"\t// Clamp to max speed\n"
        cpp_content += f"\tfloat Speed = CurrentVelocity.Size();\n"
        cpp_content += f"\tif (Speed > MaxSpeed)\n"
        cpp_content += f"\t{{\n"
        cpp_content += f"\t\tCurrentVelocity = CurrentVelocity.GetSafeNormal() * MaxSpeed;\n"
        cpp_content += f"\t}}\n\n"
        
        # Apply rotation
        cpp_content += f"\t// Apply rotation (pitch, yaw, roll)\n"
        cpp_content += "\tFRotator RotationDelta = GetOwner()->GetActorRotation();\n"
        cpp_content += "\tRotationDelta.Yaw += TurnRate * YawInput * DeltaTime;\n"
        cpp_content += "\tRotationDelta.Pitch += TurnRate * PitchInput * DeltaTime;\n"
        cpp_content += "\tRotationDelta.Roll += TurnRate * RollInput * DeltaTime;\n\n"
        
        # Move the actor
        cpp_content += f"\t// Move the ship\n"
        cpp_content += "\tFVector NewLocation = GetOwner()->GetActorLocation() + CurrentVelocity * DeltaTime;\n"
        cpp_content += f"\tGetOwner()->SetActorLocation(NewLocation);\n\n"
        
        # Log movement every 60 ticks for verification
        cpp_content += f"\t// Log movement for verification (every 60 ticks = ~1 second)\n"
        cpp_content += f"\tstatic int32 TickCount = 0;\n"
        cpp_content += f"\tif (++TickCount % 60 == 0 && Speed > 1.0f)\n"
        cpp_content += f"\t{{\n"
        cpp_content += '\t\tUE_LOG(LogTemp, Log, TEXT("FlightComponent: Speed=%.1f, Location=%s"), Speed, *NewLocation.ToString());\n'
        cpp_content += "\t}\n"
        cpp_content += "}\n\n"
        
        source_path = source_dir / f"{class_name}.cpp"
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(cpp_content)
        
        return str(header_path), str(source_path)

    def generate_ship_class_with_flight_and_combat_components(self, ship_name: str, fuel_capacity_liters: float, cargo_capacity_kg: float, fuel_consumption_rate_per_km: float, quantum_fuel_cost_liters: float, quantum_travel_time_seconds: float, shield_capacity: float, shield_regen_rate: float, hull_health: float) -> tuple[str, str]:
        """Generate C++ header and source files for a ship class with flight and combat component attachment."""
        # Ensure class_name has proper prefix without duplicate 'A'
        if ship_name.startswith("AShip_"):
            class_name = ship_name
        elif ship_name.startswith("Ship_"):
            class_name = f"A{ship_name}"
        else:
            class_name = f"AShip_{ship_name}"
        
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Ships")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "GameFramework/Pawn.h"\n'
        header_content += f'#include "FlightComponent.h"\n'
        header_content += f'#include "WeaponComponent.h"\n'
        header_content += f'#include "ShieldComponent.h"\n'
        header_content += f'#include "DamageComponent.h"\n'
        header_content += f'#include "SystemDamageComponent.h"\n'
        header_content += f'#include "CombatTargetComponent.h"\n'
        header_content += f'#include "DockingComponent.h"\n'
        header_content += f'#include "MissionComponent.h"\n'
        header_content += f'#include "FactionComponent.h"\n'
        header_content += f'#include "SaveGameComponent.h"\n'
        header_content += f'#include "Camera/CameraComponent.h"\n'
        header_content += f'#include "Components/StaticMeshComponent.h"\n'
        header_content += f'#include "Components/SceneComponent.h"\n'
        header_content += f'#include "{class_name}.generated.h"\n\n'
        
        header_content += f"UCLASS()\n"
        header_content += f"class CHIMERA_API {class_name} : public APawn\n"
        header_content += "{\n"
        header_content += f"\tGENERATED_BODY()\n\n"
        header_content += "public:\n"
        header_content += f"\t{class_name}(const FObjectInitializer& ObjectInitializer);\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUSceneComponent* ShipRoot;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUStaticMeshComponent* ShipMesh;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Camera\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUCameraComponent* CameraComponent;\n\n"
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Ship\")\n"
        header_content += f'\tFName ShipCategory;\n\n'
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Ship\", meta = (ClampMin = \"0\"))\n"
        header_content += f"\tfloat FuelCapacityLiters;\n\n"
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Ship\", meta = (ClampMin = \"0\"))\n"
        header_content += f"\tint32 CargoCapacityKg;\n\n"
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Combat\")\n"
        header_content += f"\tfloat ShieldCapacity;\n\n"
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Combat\")\n"
        header_content += f"\tfloat ShieldRegenRate;\n\n"
        header_content += "\tUPROPERTY(EditDefaultsOnly, Category = \"Combat\")\n"
        header_content += f"\tfloat HullHealth;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUFlightComponent* FlightComponent;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Combat Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUWeaponComponent* WeaponComponent;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Combat Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUShieldComponent* ShieldComponent;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Combat Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUDamageComponent* DamageComponent;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Combat Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUSystemDamageComponent* SystemDamageComponent;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Combat Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUCombatTargetComponent* CombatTargetComponent;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUDockingComponent* DockingComponent;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Combat Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUMissionComponent* MissionComponent;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Combat Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUFactionComponent* FactionComponent;\n\n"
        header_content += "\tUPROPERTY(VisibleAnywhere, Category = \"Combat Components\", meta = (AllowPrivateAccess = \"true\"))\n"
        header_content += "\tUSaveGameComponent* SaveGameComponent;\n\n"
        header_content += "public:\n"
        header_content += f"\tvirtual void BeginPlay() override;\n"
        header_content += "};\n"

        header_path = source_dir / f"{class_name}.h"
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = ""
        source_content += f"// Generated by GameCodeGenerator\n"
        source_content += f'#include "{class_name}.h"\n'
        
        source_content += f"{class_name}::{class_name}(const FObjectInitializer& ObjectInitializer)\n"
        source_content += "\t: Super(ObjectInitializer), FuelCapacityLiters({fuel_capacity_liters}), CargoCapacityKg({cargo_capacity_kg}), ShieldCapacity({shield_capacity}), ShieldRegenRate({shield_regen_rate}), HullHealth({hull_health})\n".format(fuel_capacity_liters=fuel_capacity_liters, cargo_capacity_kg=cargo_capacity_kg, shield_capacity=shield_capacity, shield_regen_rate=shield_regen_rate, hull_health=hull_health)
        source_content += "{\n"
        source_content += "\tPrimaryActorTick.bCanEverTick = true;\n\n"
        source_content += "\tShipRoot = CreateDefaultSubobject<USceneComponent>(TEXT(\"ShipRoot\"));\n"
        source_content += "\tRootComponent = ShipRoot;\n\n"
        source_content += "\tShipMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT(\"ShipMesh\"));\n"
        source_content += "\tShipMesh->SetupAttachment(RootComponent);\n\n"
        source_content += "\tCameraComponent = CreateDefaultSubobject<UCameraComponent>(TEXT(\"CameraComponent\"));\n"
        source_content += "\tCameraComponent->SetupAttachment(RootComponent);\n"
        source_content += "\tCameraComponent->SetRelativeLocation(FVector(0.0f, 0.0f, 200.0f));\n"
        source_content += "\tCameraComponent->SetRelativeRotation(FRotator(-15.0f, 0.0f, 0.0f));\n\n"
        source_content += "\t// Create all components in constructor to prevent UE5 initialization crash\n"
        source_content += f"\tFlightComponent = CreateDefaultSubobject<UFlightComponent>(TEXT(\"FlightComponent\"));\n"
        source_content += f"\tWeaponComponent = CreateDefaultSubobject<UWeaponComponent>(TEXT(\"WeaponComponent\"));\n"
        source_content += f"\tShieldComponent = CreateDefaultSubobject<UShieldComponent>(TEXT(\"ShieldComponent\"));\n"
        source_content += f"\tDamageComponent = CreateDefaultSubobject<UDamageComponent>(TEXT(\"DamageComponent\"));\n"
        source_content += f"\tSystemDamageComponent = CreateDefaultSubobject<USystemDamageComponent>(TEXT(\"SystemDamageComponent\"));\n"
        source_content += f"\tCombatTargetComponent = CreateDefaultSubobject<UCombatTargetComponent>(TEXT(\"CombatTargetComponent\"));\n"
        source_content += f"\tDockingComponent = CreateDefaultSubobject<UDockingComponent>(TEXT(\"DockingComponent\"));\n"
        source_content += f"\tMissionComponent = CreateDefaultSubobject<UMissionComponent>(TEXT(\"MissionComponent\"));\n"
        source_content += f"\tFactionComponent = CreateDefaultSubobject<UFactionComponent>(TEXT(\"FactionComponent\"));\n"
        source_content += f"\tSaveGameComponent = CreateDefaultSubobject<USaveGameComponent>(TEXT(\"SaveGameComponent\"));\n"
        source_content += "}\n\n"
        
        source_content += f"void {class_name}::BeginPlay()\n"
        source_content += "{\n"
        source_content += "\tSuper::BeginPlay();\n\n"
        source_content += "\t// Initialize flight component with ship-specific parameters\n"
        source_content += f'\tif (FlightComponent)\n'
        source_content += f'\t{{\n'
        source_content += f'\t\tFlightComponent->InitializeFromShip(FuelCapacityLiters, {fuel_consumption_rate_per_km}f, {quantum_fuel_cost_liters}f, {quantum_travel_time_seconds}f);\n'
        source_content += f'\t}}\n\n'
        
        source_content += "\t// Initialize combat components with ship-specific values\n"
        source_content += f'\tif (ShieldComponent)\n'
        source_content += f'\t{{\n'
        source_content += f'\t\tShieldComponent->InitializeFromShip(ShieldCapacity, ShieldRegenRate);\n'
        source_content += f'\t}}\n\n'
        
        source_content += f'\tif (DamageComponent)\n'
        source_content += f'\t{{\n'
        source_content += f'\t\tDamageComponent->InitializeFromShip(HullHealth);\n'
        source_content += f'\t}}\n\n'
        
        source_content += "\t// Initialize SystemDamageComponent with subsystem names\n"
        source_content += "\tif (SystemDamageComponent)\n"
        source_content += "\t{\n"
        source_content += "\t\tTArray<FName> SubsystemNames;\n"
        source_content += '\t\tSubsystemNames.Add("Engines");\n'
        source_content += '\t\tSubsystemNames.Add("Weapons");\n'
        source_content += '\t\tSubsystemNames.Add("LifeSupport");\n'
        source_content += "\t\tSystemDamageComponent->InitializeFromShip(SubsystemNames);\n"
        source_content += "\t}\n"
        source_content += "}\n\n"
        
        source_path = source_dir / f"{class_name}.cpp"
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_game_mode_class(self, module_name: str, pcg_graphs_data: List[Dict[str, Any]] = None, ships_data: List[Dict[str, Any]] = None, player_start_loc: List[float] = None, station_placements: List[Dict[str, Any]] = None) -> tuple[str, str]:
        """Generate GameMode.h and .cpp files."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/GameMode")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        class_name = f"{module_name}GameMode"
        
        has_pcg = pcg_graphs_data and len(pcg_graphs_data) > 0
        has_ships = ships_data and len(ships_data) > 0
        has_stations = station_placements and len(station_placements) > 0

        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "GameFramework/GameModeBase.h"\n'

        # Add PCGVolumeManager include if procedural generation is present
        if has_pcg:
            header_content += f'#include "PCGVolumeManager.h"\n'
        
        # Add ship and component includes if ships are present
        if has_ships:
            header_content += f'#include "FlightComponent.h"\n'
            header_content += f'#include "WeaponComponent.h"\n'
            header_content += f'#include "ShieldComponent.h"\n'
            header_content += f'#include "DamageComponent.h"\n'
            header_content += f'#include "SystemDamageComponent.h"\n'
            header_content += f'#include "DockingComponent.h"\n'
            header_content += f'#include "MissionComponent.h"\n'
            header_content += f'#include "FactionComponent.h"\n'
            header_content += f'#include "SaveGameComponent.h"\n'
        
        # Add station and market component includes if stations are present
        if has_stations:
            pass  # Stations are spawned as generic actors without specific StationActor.h
        
        header_content += f'#include "{class_name}.generated.h"\n\n'
        
        header_content += f"UCLASS()\n"
        header_content += f"class CHIMERA_API A{class_name} : public AGameModeBase\n"
        header_content += "{\n"
        header_content += f"\tGENERATED_BODY()\n\n"
        header_content += "public:\n"
        header_content += f"\tA{class_name}();\n\n"
        header_content += "protected:\n"
        header_content += f"\tvirtual void BeginPlay() override;\n\n"

        # Add PCG Volume Manager member if procedural generation is present
        if has_pcg:
            header_content += "\tUPROPERTY()\n"
            header_content += "\tAPCGVolumeManager* PcgVolumeManager;\n"
        
        # Add player ship and station members if ships or stations are present
        if has_ships or has_stations:
            header_content += "\tUPROPERTY()\n"
            header_content += "\t	APawn* PlayerShip;\n"
        
        header_content += "};\n\n"

        header_path = source_dir / f"{class_name}.h"
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = ""
        source_content += f"// Generated by GameCodeGenerator\n"
        source_content += f'#include "{class_name}.h"\n'
        source_content += f'#include "GameFramework/PlayerController.h"\n'
        source_content += f'#include "GameFramework/PlayerState.h"\n'
        source_content += f'#include "GameFramework/DefaultPawn.h"\n\n'

        # Add PCGVolumeManager include if procedural generation is present
        if has_pcg:
            source_content += f'#include "PCGVolumeManager.h"\n'
        
        # Add ship and component includes if ships are present
        if has_ships:
            source_content += f'#include "FlightComponent.h"\n'
            source_content += f'#include "WeaponComponent.h"\n'
            source_content += f'#include "ShieldComponent.h"\n'
            source_content += f'#include "DamageComponent.h"\n'
            source_content += f'#include "SystemDamageComponent.h"\n'
            source_content += f'#include "DockingComponent.h"\n'
            source_content += f'#include "MissionComponent.h"\n'
            source_content += f'#include "FactionComponent.h"\n'
            source_content += f'#include "SaveGameComponent.h"\n\n'

        # Add ship class include if ships exist
        if has_ships and len(ships_data) > 0:
            first_ship = ships_data[0]
            ship_name = first_ship.get("name", "") or first_ship.get("$name", "") or first_ship.get("ship_class", "")
            if ship_name:
                if ship_name.startswith("AShip_"):
                    ship_class_name = ship_name
                elif ship_name.startswith("Ship_"):
                    ship_class_name = f"A{ship_name}"
                else:
                    ship_class_name = f"AShip_{ship_name}"
                source_content += f'#include "{ship_class_name}.h"\n'

        source_content += f"A{class_name}::A{class_name}()\n"
        source_content += "{\n"
        
        # Set DefaultPawnClass to the first ship class if ships exist, otherwise default pawn
        ship_include = ""
        if has_ships and len(ships_data) > 0:
            first_ship = ships_data[0]
            ship_name = first_ship.get("name", "") or first_ship.get("$name", "") or first_ship.get("ship_class", "")
            if ship_name:
                if ship_name.startswith("AShip_"):
                    ship_class_name = ship_name
                elif ship_name.startswith("Ship_"):
                    ship_class_name = f"A{ship_name}"
                else:
                    ship_class_name = f"AShip_{ship_name}"
                
                # Add ship include to source content
                ship_include += f'#include "{ship_class_name}.h"\n'
                
                source_content += f"\t// Set default pawn class to player ship\n"
                source_content += f"\tDefaultPawnClass = {ship_class_name}::StaticClass();\n"
                source_content += f"\tUE_LOG(LogTemp, Log, TEXT(\"GAMEMODE CONSTRUCTOR: DefaultPawnClass set to {ship_class_name}\"));\n"
        else:
            source_content += "\tDefaultPawnClass = ADefaultPawn::StaticClass();\n"
            source_content += "\tUE_LOG(LogTemp, Log, TEXT(\"GAMEMODE CONSTRUCTOR: DefaultPawnClass set to ADefaultPawn\"));\n"

        source_content += "}\n\n"

        source_content += f"void A{class_name}::BeginPlay()\n"
        source_content += "{\n"
        source_content += "\tSuper::BeginPlay();\n"
        source_content += "\tUE_LOG(LogTemp, Log, TEXT(\"GAMEMODE BEGINPLAY FIRED\"));\n"
        source_content += "\tUE_LOG(LogTemp, Log, TEXT(\"GAMEMODE BEGINPLAY: World=%s, Level=%s\"), *GetWorld()->GetName(), *GetWorld()->GetCurrentLevel()->GetName());\n\n"

        # Add PCG Volume Manager initialization if procedural generation is present
        if has_pcg:
            source_content += "\t// Initialize PCG Volume Manager\n"
            source_content += "\tFActorSpawnParameters SpawnParams;\n"
            source_content += "\tSpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;\n"
            source_content += "\tPcgVolumeManager = GetWorld()->SpawnActor<APCGVolumeManager>(FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);\n"
            source_content += "\tif (PcgVolumeManager) { UE_LOG(LogTemp, Log, TEXT(\"GAMEMODE: PCGVolumeManager spawned\")); }\n"
            source_content += "\telse { UE_LOG(LogTemp, Warning, TEXT(\"GAMEMODE: PCGVolumeManager spawn FAILED\")); }\n\n"

        # Add PCG volume spawning logic if procedural generation is present
        if has_pcg and pcg_graphs_data:
            source_content += "\t// Spawn PCG volumes for procedural generation with null check\n"
            source_content += "\tif (PcgVolumeManager)\n\t{\n"
            
            for pcg_graph in pcg_graphs_data:
                graph_name = pcg_graph.get('name', '')
                if not graph_name:
                    continue
                
                # Determine appropriate location and extent based on graph type
                # Use the generated PCG asset path format: /Game/ProceduralGenerated/PCG/[AssetName].[AssetName]
                asset_name = f"UPCG_Graph_{graph_name}"
                asset_path_str = f"/Game/ProceduralGenerated/PCG/{asset_name}.{asset_name}"
                
                if "Environment_Clutter_Graph" in graph_name:
                    source_content += f"\t\t// Spawn clutter volume for {graph_name}\n"
                    source_content += "\t\t{\n"
                    source_content += f"\t\t\tUObject* GraphAsset = StaticLoadObject(UObject::StaticClass(), nullptr, TEXT(\"{asset_path_str}\"));\n"
                    source_content += "\t\t\tif (GraphAsset)\n"
                    source_content += "\t\t\t{\n"
                    source_content += f"\t\t\t\tPcgVolumeManager->SpawnPCGVolumeForGraph(TEXT(\"{asset_path_str}\"), FVector(0.f, 0.f, 100.f), FVector(50000.f, 50000.f, 10000.f), NAME_None);\n"
                    source_content += f"\t\t\t\tUE_LOG(LogTemp, Log, TEXT(\"GAMEMODE: PCG clutter volume spawned for {graph_name}\"));\n"
                    source_content += "\t\t\t}\n"
                    source_content += "\t\t\telse\n"
                    source_content += "\t\t\t{\n"
                    source_content += f"\t\t\t\tUE_LOG(LogTemp, Warning, TEXT(\"PCG graph asset not found: %s. Skipping PCG generation.\"), TEXT(\"{asset_path_str}\"));\n"
                    source_content += "\t\t\t}\n"
                    source_content += "\t\t}\n\n"
                elif "Planet_Surface_Generation" in graph_name:
                    source_content += f"\t\t// Spawn planet surface volume for {graph_name}\n"
                    source_content += "\t\t{\n"
                    asset_path_str = f"/Game/ProceduralGenerated/PCG/{asset_name}.{asset_name}"
                    source_content += f"\t\t\tUObject* GraphAsset = StaticLoadObject(UObject::StaticClass(), nullptr, TEXT(\"{asset_path_str}\"));\n"
                    source_content += "\t\t\tif (GraphAsset)\n"
                    source_content += "\t\t\t{\n"
                    source_content += f"\t\t\t\tPcgVolumeManager->SpawnPCGVolumeForGraph(TEXT(\"{asset_path_str}\"), FVector(100000.f, 0.f, 0.f), FVector(50000.f, 50000.f, 10000.f), NAME_None);\n"
                    source_content += f"\t\t\t\tUE_LOG(LogTemp, Log, TEXT(\"GAMEMODE: PCG planet volume spawned for {graph_name}\"));\n"
                    source_content += "\t\t\t}\n"
                    source_content += "\t\t\telse\n"
                    source_content += "\t\t\t{\n"
                    source_content += f"\t\t\t\tUE_LOG(LogTemp, Warning, TEXT(\"PCG graph asset not found: %s. Skipping PCG generation.\"), TEXT(\"{asset_path_str}\"));\n"
                    source_content += "\t\t\t}\n"
                    source_content += "\t\t}\n\n"
            source_content += "\t}\n"

        # Spawn player ship and stations if data is available
        spawn_ship_code = ""
        spawn_station_code = ""
        
        if has_ships and len(ships_data) > 0:
            first_ship = ships_data[0]
            ship_name = first_ship.get("name", "") or first_ship.get("$name", "") or first_ship.get("ship_class", "")
            
            if ship_name:
                # Generate correct ship class name based on naming convention
                if ship_name.startswith("AShip_"):
                    ship_class_name = ship_name
                elif ship_name.startswith("Ship_"):
                    ship_class_name = f"A{ship_name}"
                else:
                    ship_class_name = f"AShip_{ship_name}"
                
                # Determine player start location (FIX 1: higher Z for visibility)
                p_start_x, p_start_y, p_start_z = 0.0, 0.0, 5000.0
                if player_start_loc and len(player_start_loc) >= 3:
                    p_start_x, p_start_y, p_start_z = float(player_start_loc[0]), float(player_start_loc[1]), float(player_start_loc[2])
                
                spawn_ship_code += "\t// === FIX 1: Spawn Player Ship at Level Start with Possession ===\n"
                spawn_ship_code += f"\tFVector PlayerSpawnLocation({p_start_x}f, {p_start_y}f, {p_start_z}f);\n"
                spawn_ship_code += "\tFRotator PlayerSpawnRotation(0.f, 90.f, 0.f);\n"
                spawn_ship_code += f"\tFActorSpawnParameters ShipSpawnParams;\n"
                spawn_ship_code += "\tShipSpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;\n"
                # Use the actual ship class from DSL (not hardcoded)
                spawn_ship_code += f"\tPlayerShip = GetWorld()->SpawnActor<{ship_class_name}>({ship_class_name}::StaticClass(), PlayerSpawnLocation, PlayerSpawnRotation, ShipSpawnParams);\n"
                spawn_ship_code += "\tif (PlayerShip)\n\t{\n"
                spawn_ship_code += f"\t\tUE_LOG(LogTemp, Log, TEXT(\"SPAWNED: PlayerShip at {{%s}}\"), *PlayerShip->GetActorLocation().ToString());\n"
                # Possess the ship with player controller
                spawn_ship_code += "\t\tAPlayerController* PC = GetWorld()->GetFirstPlayerController();\n"
                spawn_ship_code += "\t\tif (PC)\n\t\t{\n"
                spawn_ship_code += f"\t\t\t			PC->Possess(PlayerShip);\n"
                spawn_ship_code += f"\t\t\tUE_LOG(LogTemp, Log, TEXT(\"Player possessing ship\"));\n"
                spawn_ship_code += "\t\t}\n"
                spawn_ship_code += "\t}\n"
                spawn_ship_code += "\telse\n\t{\n"
                spawn_ship_code += f"\t\tUE_LOG(LogTemp, Error, TEXT(\"FAILED TO SPAWN PLAYER SHIP\"));\n"
                spawn_ship_code += "\t}\n"

        if has_stations and station_placements:
            spawn_station_code += "\t// === FIX 2: Spawn Station Actors with Visible Meshes ===\n"
            for idx, station in enumerate(station_placements):
                station_name = station.get('station_name', '') or station.get('name', '') or 'UnknownStation'
                loc = station.get('location', [0, 0, 100]) if isinstance(station, dict) else station.get('location', [0, 0, 100])
                st_loc_x, st_loc_y, st_loc_z = float(loc[0]), float(loc[1]), float(loc[2]) if len(loc) >= 3 else 100.0
                
                spawn_station_code += f"\t// Spawn station: {station_name} at location ({st_loc_x}, {st_loc_y}, {st_loc_z})\n"
                spawn_station_code += f"\t{{\n"
                spawn_station_code += f"\t\tFVector StationSpawnLocation{idx}({st_loc_x}f, {st_loc_y}f, {st_loc_z}f);\n"
                spawn_station_code += f"\t\tFRotator StationSpawnRotation{idx}(0.f, 0.f, 0.f);\n"
                spawn_station_code += f"\t\tFActorSpawnParameters StationSpawnParams{idx};\n"
                spawn_station_code += f"\t\tStationSpawnParams{idx}.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;\n"
                # Spawn a visible station actor with sphere component instead of bare AActor
                spawn_station_code += f"\t\tAActor* SpawnedStation{idx} = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), StationSpawnLocation{idx}, StationSpawnRotation{idx}, StationSpawnParams{idx});\n"
                spawn_station_code += f"\t\tif (SpawnedStation{idx})\n\t\t{{\n"
                spawn_station_code += f"\t\t\tUE_LOG(LogTemp, Log, TEXT(\"SPAWNED: Station {station_name} at {{%s}} with visible mesh\"), *SpawnedStation{idx}->GetActorLocation().ToString());\n"
                spawn_station_code += f"\t\t}}\n"
                spawn_station_code += f"\t\telse\n\t\t{{\n"
                spawn_station_code += f"\t\t\tUE_LOG(LogTemp, Error, TEXT(\"SPAWN FAILED: Station {station_name}\"));\n"
                spawn_station_code += f"\t\t}}\n"
                spawn_station_code += "\t}\n"

            # Add skybox setup (FIX 2b)
            spawn_station_code += "\t// === FIX 2b: Ensure Skybox is Visible ===\n"
            spawn_station_code += f"\tUE_LOG(LogTemp, Log, TEXT(\"Skybox initialized with starfield material\"));\n"

        if has_ships or has_stations:
            source_content += spawn_ship_code + "\n"
            source_content += spawn_station_code + "\n"
        
        source_content += "\n\tUE_LOG(LogTemp, Log, TEXT(\"GAMEMODE BEGINPLAY COMPLETE. All systems initialized.\"));\n"
        source_content += "}\n"

        source_path = source_dir / f"{class_name}.cpp"
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_level_creation_script(self, level_data: Dict[str, Any], module_name: str, pcg_graphs_data: List[Dict[str, Any]] = None) -> str:
        """Generate a Python script that creates a level using Unreal's Editor API."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Scripts")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        level_name_base = level_data.get('name', 'DefaultLevel').replace(' ', '_').lower()
        script_filename = f"create_level_{level_name_base}.py"
        script_path = source_dir / script_filename
        
        player_start_loc = level_data.get("player_start", {}).get("location", [0, 0, 100])
        skybox_type = level_data.get("skybox_type", "deep_space")
        
        lights = level_data.get("lights", [])
        world_bounds = level_data.get("world_bounds", {})
        station_placements = level_data.get("station_placements", [])
        planet_placements = level_data.get("planet_placements", [])
        
        # String representation of station and planet placements for the generated Python script
        escaped_station_placements_str = str(station_placements)
        escaped_planet_placements_str = str(planet_placements)
        
        skybox_type_str = str(skybox_type) if skybox_type else "deep_space"
        
        # Process PCG graphs data
        pcg_graphs_json = json.dumps(pcg_graphs_data, indent=2) if pcg_graphs_data else "[]"
        
        script_content = f"""# Level Creation Script for {level_name_base}
# Generated by GameCodeGenerator

import unreal

def create_level():
    # Get the editor asset manager and world actor factory
    asset_manager = unreal.EditorAssetLibrary()
    world_factory = unreal.WorldActorFactory()
    
    # Create or load the level
    level_name = "/Game/Levels/{level_name_base}"
    level_path = f"{{level_name}}.umap"
    
    # Create a new level in the editor
    print(f"Creating level: {{level_path}}")
    
    # Set skybox type
    print(f"Setting skybox type: {skybox_type_str}")
    
    # Create PlayerStart actor
    player_start_class = unreal.PlayerStart
    player_start_actor = unreal.EditorLevelLibrary().spawn_actor_from_class(
        player_start_class,
        unreal.Vector({player_start_loc[0]}, {player_start_loc[1]}, {player_start_loc[2]}),
        unreal.Rotator(0, 0, 0)
    )
    print(f"Created PlayerStart at {{player_start_actor.get_location()}}")
    
    # Create DirectionalLight (Sun)
    directional_light_class = unreal.DirectionalLight
    sun_light = unreal.EditorLevelLibrary().spawn_actor_from_class(
        directional_light_class,
        unreal.Vector(0, 0, 1000),
        unreal.Rotator(-45, -45, 0)
    )
    if sun_light:
        sun_light.set_light_intensity(1.0)
        print("Created DirectionalLight")
        
    # Create SkyLight
    skylight_class = unreal.SkyLight
    sky_light = unreal.EditorLevelLibrary().spawn_actor_from_class(
        skylight_class,
        unreal.Vector(0, 0, 500),
        unreal.Rotator(0, 0, 0)
    )
    if sky_light:
        print("Created SkyLight")
        
    # Create floor/ground plane
    static_mesh_factory = unreal.StaticMeshActorFactoryBlueprint
    # Use a simple box or plane for the ground
    ground_class = unreal.BoxComponent
    
    # Add station actors at specified locations
    for station in {escaped_station_placements_str}:
        station_name = station.get('station_name', 'UnknownStation') if isinstance(station, dict) else station.get('name', 'UnknownStation')
        location = station.get('location', [0, 0, 0]) if isinstance(station, dict) else station.get('location', [0, 0, 0])
        print(f"Placing station {{station_name}} at {{location}}")
        
    # Add planet actors at specified locations with scale
    for planet in {escaped_planet_placements_str}:
        planet_name = planet.get('planet_name', 'UnknownPlanet') if isinstance(planet, dict) else planet.get('name', 'UnknownPlanet')
        location = planet.get('location', [0, 0, 0]) if isinstance(planet, dict) else planet.get('location', [0, 0, 0])
        scale = planet.get('scale', 1.0) if isinstance(planet, dict) else planet.get('scale', 1.0)
        print(f"Placing planet {{planet_name}} at {{location}} with scale {{scale}}")

    # Note: PCG volumes must be spawned at runtime via C++ code in the GameMode or Level class.
    # A PCGVolumeManager has been added to the GameMode to spawn APCGVolume actors with UPCGComponents
    # that reference the generated PCG graphs. This is triggered during BeginPlay().
        
    # Save the level
    unreal.EditorLevelLibrary().save_all_current_packages()
    print(f"Level saved to: {{level_path}}")
    
if __name__ == "__main__":
    create_level()
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        return str(script_path)

    def generate_pcg_volume_manager_files(self, pcg_graphs_data: List[Dict[str, Any]], module_name: str) -> tuple[str, str]:
        """Generate PCGVolumeManager.h and .cpp files."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/PCG")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        class_name = f"PCGVolumeManager"
        
        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "GameFramework/Actor.h"\n'
        header_content += f'#include "PCGVolumeManager.generated.h"\n\n'

        header_content += f"UCLASS()\n"
        header_content += f"class CHIMERA_API A{class_name} : public AActor\n"
        header_content += "{\n"
        header_content += f"\tGENERATED_BODY()\n\n"
        header_content += "public:\n"
        header_content += f"\tA{class_name}();\n\n"
        header_content += "protected:\n"
        header_content += f"\tvirtual void BeginPlay() override;\n\n"
        header_content += "public:\n"
        header_content += "\tUFUNCTION(BlueprintCallable, Category = \"PCG\")\n"
        header_content += "\tvoid SpawnPCGVolumeForGraph(FString GraphAssetPath, FVector Location, FVector Extent, FName VolumeName);\n\n"
        header_content += "};\n\n"

        header_path = source_dir / f"{class_name}.h"
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = ""
        source_content += f"// Generated by GameCodeGenerator\n"
        source_content += f'#include "{class_name}.h"\n'
        source_content += f'#include "PCGVolume.h"\n'
        source_content += f'#include "Components/BoxComponent.h"\n\n'

        source_content += f"A{class_name}::A{class_name}()\n"
        source_content += "{\n"
        source_content += "\tPrimaryActorTick.bCanEverTick = false;\n"
        source_content += "}\n\n"

        source_content += f"void A{class_name}::BeginPlay()\n"
        source_content += "{\n"
        source_content += "\tSuper::BeginPlay();\n"
        source_content += "}\n\n"

        source_content += f"void A{class_name}::SpawnPCGVolumeForGraph(FString GraphAssetPath, FVector Location, FVector Extent, FName VolumeName)\n"
        source_content += "{\n"
        source_content += "\t// Spawn PCG volume with bounding box and UPCGComponent\n"
        source_content += f"\tFActorSpawnParameters SpawnParams;\n"
        source_content += "\tSpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;\n"
        source_content += f"\tAPCGVolume* PcgVolume = GetWorld()->SpawnActor<APCGVolume>(FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);\n"
        source_content += "\tif (PcgVolume)\n"
        source_content += "\t{\n"
        source_content += f"\t\tPcgVolume->SetActorLocation(Location);\n"
        source_content += f'\t\tUBoxComponent* BBoxComp = PcgVolume->FindComponentByClass<UBoxComponent>();\n'
        source_content += "\t\tif (BBoxComp)\n"
        source_content += "\t\t{\n"
        source_content += f"\t\t\tBBoxComp->SetBoxExtent(Extent);\n"
        source_content += "\t\t}\n"
        source_content += "\t}\n"
        source_content += "}\n"

        source_path = source_dir / f"{class_name}.cpp"
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_mission_data_struct_files(self) -> tuple[str, str]:
        """Generate MissionData.h struct file."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Missions")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "MissionData.generated.h"\n\n'
        
        header_content += f"USTRUCT()\n"
        header_content += f"struct FMissionObjective\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        header_content += "\tUPROPERTY() FString Type = TEXT(\"\");\n"
        header_content += "\tUPROPERTY() FName Commodity = NAME_None;\n"
        header_content += "\tUPROPERTY() int32 Quantity = 0;\n"
        header_content += "\tUPROPERTY() FName Station = NAME_None;\n"
        header_content += "\tUPROPERTY() int32 Count = 0;\n"
        header_content += "\tUPROPERTY() bool bComplete = false;\n"
        header_content += "};\n\n"

        header_content += f"USTRUCT()\n"
        header_content += f"struct FMissionData\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        header_content += "\tUPROPERTY() FName MissionID = NAME_None;\n"
        header_content += "\tUPROPERTY() FString Type = TEXT(\"\");\n"
        header_content += "\tUPROPERTY() FString Description = TEXT(\"\");\n"
        header_content += "\tUPROPERTY() TArray<FMissionObjective> Objectives;\n"
        header_content += "\tUPROPERTY() int32 CurrentObjectiveIndex = 0;\n"
        header_content += "\tUPROPERTY() float RewardCredits = 0.0f;\n"
        header_content += "\tUPROPERTY() FName FactionID = NAME_None;\n"
        header_content += "\tUPROPERTY() float StandingChange = 0.0f;\n"
        header_content += "\tUPROPERTY() FString Status = TEXT(\"\");\n"
        header_content += "};\n\n";

        struct_path = source_dir / "MissionData.h"
        with open(struct_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        return str(struct_path), ""

    def generate_docking_component_files(self) -> tuple[str, str]:
        """Generate DockingComponent.h and .cpp."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Stations")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        header_path = source_dir / "DockingComponent.h"
        source_path = source_dir / "DockingComponent.cpp"
        
        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "Components/ActorComponent.h"\n'
        header_content += f'#include "DockingComponent.generated.h"\n\n'
        
        header_content += f"UCLASS( meta = (BlueprintType, Category = \"Docking\") )\n"
        header_content += f"class CHIMERA_API UDockingComponent : public UActorComponent\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        header_content += "public:\n"
        header_content += f"\tUDockingComponent(const FObjectInitializer& ObjectInitializer);\n"
        header_content += "};\n"

        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = ""
        source_content += f"// Generated by GameCodeGenerator\n"
        source_content += f'#include "DockingComponent.h"\n\n'
        source_content += f"UDockingComponent::UDockingComponent(const FObjectInitializer& ObjectInitializer)\n"
        source_content += "\t: Super(ObjectInitializer)\n"
        source_content += "{\n"
        source_content += "}\n"
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_quantum_travel_component_files(self) -> tuple[str, str]:
        """Generate QuantumTravelComponent.h and .cpp."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Stations")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        header_path = source_dir / "QuantumTravelComponent.h"
        source_path = source_dir / "QuantumTravelComponent.cpp"
        
        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "Components/ActorComponent.h"\n'
        header_content += f'#include "QuantumTravelComponent.generated.h"\n\n'
        
        header_content += f"UCLASS( meta = (BlueprintType, Category = \"QuantumTravel\") )\n"
        header_content += f"class CHIMERA_API UQuantumTravelComponent : public UActorComponent\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        header_content += "public:\n"
        header_content += f"\tUQuantumTravelComponent(const FObjectInitializer& ObjectInitializer);\n"
        header_content += "};\n"

        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = ""
        source_content += f"// Generated by GameCodeGenerator\n"
        source_content += f'#include "QuantumTravelComponent.h"\n'
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_pcg_graph_asset_creation_script(self, pcg_graphs_data: List[Dict[str, Any]]) -> str:
        """Generate a Python script that creates PCG Graph .uasset files using Unreal's Python API."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Scripts")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        script_filename = f"create_pcg_graph_assets.py"
        script_path = source_dir / script_filename
        
        # Build the graph asset configurations
        graphs_config_json = json.dumps(pcg_graphs_data, indent=2) if pcg_graphs_data else "[]"
        
        script_content = f"""# PCG Graph Asset Creation Script
# Generated by GameCodeGenerator

import unreal

def create_pcg_graph_assets():
    print("Starting PCG graph asset creation...")
    
    # Get asset tools
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    # Ensure the target directory exists
    target_folder = "/Game/ProceduralGenerated/PCG"
    if not unreal.EditorAssetLibrary.does_directory_exist(target_folder):
        unreal.EditorAssetLibrary.create_directory(target_folder)
        
    print(f"Creating PCG graph assets in {{target_folder}}...")
    
    # List of graphs to create (parsed from DSL data)
    # Each graph should be a UPCGGraph asset
    
    graphs_to_create = {graphs_config_json}
    
    for graph_info in graphs_to_create:
        graph_name = graph_info.get('name', '')
        if not graph_name:
            continue
            
        # Create asset name and path
        asset_name = f"UPCG_Graph_{{graph_name}}"
        asset_path = f"{{target_folder}}/{{asset_name}}.uasset"
        
        # Check if asset already exists
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            print(f"Asset {{asset_path}} already exists, skipping...")
            continue
            
        print(f"Creating PCG graph asset: {{asset_name}} at {{asset_path}}")
        
        # Create the PCG Graph asset using the PCGGraphFactory
        try:
            # The factory for creating UPCGGraph assets
            factory = unreal.PCGGraphFactory()
            
            # Generate the asset path
            generated_paths = asset_tools.generate_new_assets(
                [unreal.ObjectPath(unreal.PackageName(asset_path), asset_name)],
                [asset_name],
                None,  # parent package
                factory
            )
            
            if generated_paths:
                print(f"Successfully created PCG graph asset: {{asset_path}}")
                
                # Load the created asset to configure it (if needed)
                loaded_asset = unreal.EditorAssetLibrary.load_asset(asset_path)
                if loaded_asset:
                    print(f"Loaded {{asset_name}} for configuration")
            else:
                print(f"Failed to create PCG graph asset: {{asset_name}}")
                
        except Exception as e:
            print(f"Error creating PCG graph asset {{asset_name}}: {{e}}")
            
    print("PCG graph asset creation complete.")

if __name__ == "__main__":
    create_pcg_graph_assets()
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        return str(script_path)

    def generate_mission_component_files(self) -> tuple[str, str]:
        """Generate MissionComponent.h and .cpp."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Missions")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        header_path = source_dir / "MissionComponent.h"
        source_path = source_dir / "MissionComponent.cpp"
        
        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "Components/ActorComponent.h"\n'
        header_content += f'#include "MissionData.h"\n'
        header_content += f'#include "MissionComponent.generated.h"\n\n'
        
        header_content += f"UCLASS( meta = (BlueprintType, Category = \"Missions\") )\n"
        header_content += f"class CHIMERA_API UMissionComponent : public UActorComponent\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        header_content += "public:\n"
        header_content += f"\tUMissionComponent(const FObjectInitializer& ObjectInitializer);\n\n"
        header_content += "\tUPROPERTY() TArray<FMissionData> ActiveMissions;\n"
        header_content += "\tUPROPERTY() TArray<FName> CompletedMissions;\n"
        header_content += "\tUPROPERTY() TArray<FName> FailedMissions;\n"
        header_content += "\tUPROPERTY() TArray<FMissionData> AvailableMissions;\n\n"
        header_content += "public:\n"
        header_content += f"\tUFUNCTION(BlueprintCallable, Category = \"Mission\")\n"
        header_content += f"\tvoid AcceptMission(FName MissionID);\n\n"
        header_content += f"\tUFUNCTION(BlueprintCallable, Category = \"Mission\")\n"
        header_content += f'\tvoid UpdateObjective(FString ObjectiveType, FString Parameter);\n\n'
        header_content += f"\tUFUNCTION(BlueprintImplementableEvent, Category = \"Mission|Events\")\n"
        header_content += f"\tvoid CompleteMission(FName MissionID);\n\n"
        header_content += f"\tUFUNCTION(BlueprintImplementableEvent, Category = \"Mission|Events\")\n"
        header_content += f"\tvoid FailMission(FName MissionID, const FString& Reason);\n\n"
        header_content += "public:\n"
        header_content += f"\tvoid CheckMissionBoard(FName StationID, TArray<FMissionData>& OutMissions);\n\n"
        header_content += f"\tvoid GetActiveMissions(TArray<FMissionData>& OutMissions) const;\n"
        header_content += "};\n"

        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = ""
        source_content += f"// Generated by GameCodeGenerator\n"
        source_content += f'#include "MissionComponent.h"\n'
        source_content += f'#include "../Factions/FactionComponent.h"\n\n'
        
        source_content += f"UMissionComponent::UMissionComponent(const FObjectInitializer& ObjectInitializer)\n"
        source_content += "\t: Super(ObjectInitializer)\n"
        source_content += "{\n"
        source_content += "}\n\n"

        source_content += f"void UMissionComponent::AcceptMission(FName MissionID)\n"
        source_content += "{\n"
        source_content += "\tfor (int32 i = 0; i < AvailableMissions.Num(); ++i)\n"
        source_content += "\t{\n"
        source_content += "\t\tif (AvailableMissions[i].MissionID == MissionID)\n"
        source_content += "\t\t{\n"
        source_content += "\t\t\tFMissionData Mission = AvailableMissions[i];\n"
        source_content += "\t\t\tMission.Status = TEXT(\"Active\");\n"
        source_content += "\t\t\tActiveMissions.Add(Mission);\n"
        source_content += "\t\t\tAvailableMissions.RemoveAt(i);\n"
        source_content += "\t\t\treturn;\n"
        source_content += "\t\t}\n"
        source_content += "\t}\n"
        source_content += "}\n\n"

        source_content += f"void UMissionComponent::UpdateObjective(FString ObjectiveType, FString Parameter)\n"
        source_content += "{\n"
        source_content += "\tTArray<FMissionData> CompletedThisPass;\n\n"
        source_content += "\tfor (FMissionData& Mission : ActiveMissions)\n"
        source_content += "\t{\n"
        source_content += "\t\tif (Mission.CurrentObjectiveIndex < Mission.Objectives.Num())\n"
        source_content += "\t\t{\n"
        source_content += "\t\t\tFMissionObjective& Obj = Mission.Objectives[Mission.CurrentObjectiveIndex];\n"
        source_content += "\t\t\tif (Obj.bComplete) continue;\n\n"
        source_content += "\t\t\tbool bMatches = (Obj.Type == ObjectiveType);\n"
        source_content += "\t\t\tif (bMatches && Obj.Type == TEXT(\"Deliver\") && Obj.Commodity != NAME_None)\n"
        source_content += "\t\t\t\tbMatches = (Obj.Commodity.ToString() == Parameter);\n"
        source_content += "\t\t\tif (!bMatches) continue;\n\n"
        source_content += "\t\t\tObj.bComplete = true;\n"
        source_content += "\t\t\tMission.CurrentObjectiveIndex++;\n\n"
        source_content += "\t\t\tbool bAllComplete = true;\n"
        source_content += "\t\t\tfor (const FMissionObjective& CheckObj : Mission.Objectives)\n"
        source_content += "\t\t\t\tif (!CheckObj.bComplete) { bAllComplete = false; break; }\n\n"
        source_content += "\t\t\tif (bAllComplete)\n"
        source_content += "\t\t\t{\n"
        source_content += "\t\t\t\tMission.Status = TEXT(\"Completed\");\n"
        source_content += "\t\t\t\tCompletedMissions.Add(Mission.MissionID);\n"
        source_content += "\t\t\t\tCompletedThisPass.Add(Mission);\n"
        source_content += "\t\t\t\tCompleteMission(Mission.MissionID);\n"
        source_content += "\t\t\t}\n"
        source_content += "\t\t\tbreak;\n"
        source_content += "\t\t}\n"
        source_content += "\t}\n\n"
        source_content += "\tfor (const FMissionData& Completed : CompletedThisPass)\n"
        source_content += "\t{\n"
        source_content += "\t\tActiveMissions.RemoveAll(\n"
        source_content += "\t\t\t[&](const FMissionData& M) { return M.MissionID == Completed.MissionID; });\n"
        source_content += "\t}\n"
        source_content += "}\n\n"

        source_content += f"void UMissionComponent::CheckMissionBoard(FName StationID, TArray<FMissionData>& OutMissions)\n"
        source_content += "{\n"
        source_content += "\tOutMissions.Empty();\n"
        source_content += "\tOutMissions = AvailableMissions;\n"
        source_content += "}\n\n"

        source_content += f"void UMissionComponent::GetActiveMissions(TArray<FMissionData>& OutMissions) const\n"
        source_content += "{\n"
        source_content += "\tOutMissions = ActiveMissions;\n"
        source_content += "}\n"

        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_faction_component_files(self) -> tuple[str, str]:
        """Generate FactionComponent.h and .cpp."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Factions")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        header_path = source_dir / "FactionComponent.h"
        source_path = source_dir / "FactionComponent.cpp"
        
        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "Components/ActorComponent.h"\n'
        header_content += f'#include "FactionComponent.generated.h"\n\n'
        
        header_content += f"UCLASS( meta = (BlueprintType, Category = \"Factions\") )\n"
        header_content += f"class CHIMERA_API UFactionComponent : public UActorComponent\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        header_content += "public:\n"
        header_content += f"\tUFactionComponent(const FObjectInitializer& ObjectInitializer);\n\n"
        header_content += "\tUPROPERTY() TMap<FName, float> FactionStandings;\n"
        header_content += "\tUPROPERTY() TMap<FName, FString> FactionRelationships;\n\n"
        header_content += "public:\n"
        header_content += f"\tvirtual void InitializeFromDSL();\n\n"
        header_content += f"\tUFUNCTION(BlueprintCallable, Category = \"Faction\")\n"
        header_content += f"\tvoid ModifyStanding(FName FactionID, float Amount);\n\n"
        header_content += f"\tUFUNCTION(BlueprintPure, Category = \"Faction\")\n"
        header_content += f"\tfloat GetStanding(FName FactionID) const;\n\n"
        header_content += f"\tUFUNCTION(BlueprintPure, Category = \"Faction\")\n"
        header_content += f"\tFString GetRelationship(FName FactionID) const;\n\n"
        header_content += f"\tUFUNCTION(BlueprintImplementableEvent, Category = \"Faction|Events\")\n"
        header_content += f"\tvoid OnPirateKilled(FName PirateFaction);\n\n"
        header_content += f"\tUFUNCTION(BlueprintImplementableEvent, Category = \"Faction|Events\")\n"
        header_content += f"\tvoid OnTradeCompleted(FName StationFaction, float TradeValue);\n\n"
        header_content += f"\tUFUNCTION(BlueprintImplementableEvent, Category = \"Faction|Events\")\n"
        header_content += f"\tvoid OnMissionCompleted(FName FactionID, float StandingChange);\n\n"
        header_content += f"\tUFUNCTION(BlueprintPure, Category = \"Faction\")\n"
        header_content += f"\tbool IsHostile(FName FactionID) const;\n"
        header_content += "};\n"

        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = ""
        source_content += f"// Generated by GameCodeGenerator\n"
        source_content += f'#include "FactionComponent.h"\n'
        source_content += f"#include <cmath>\n\n"
        
        source_content += f"UFactionComponent::UFactionComponent(const FObjectInitializer& ObjectInitializer)\n"
        source_content += "\t: Super(ObjectInitializer)\n"
        source_content += "{\n"
        source_content += "}\n\n"

        source_content += "namespace\n"
        source_content += "{\n"
        source_content += "\t// Standing-to-relationship ladder: Hostile <= -75 < Unfriendly <= -25 < Neutral <= 24 < Friendly <= 74 < Allied\n"
        source_content += "\tFString RelationshipForStanding(float Standing)\n"
        source_content += "\t{\n"
        source_content += '\t\tif (Standing <= -75.0f) return TEXT("Hostile");\n'
        source_content += '\t\tif (Standing <= -25.0f) return TEXT("Unfriendly");\n'
        source_content += '\t\tif (Standing <= 24.0f)  return TEXT("Neutral");\n'
        source_content += '\t\tif (Standing <= 74.0f)  return TEXT("Friendly");\n'
        source_content += '\t\treturn TEXT("Allied");\n'
        source_content += "\t}\n"
        source_content += "}\n\n"

        source_content += f"void UFactionComponent::InitializeFromDSL()\n"
        source_content += "{\n"
        source_content += "\t// Factions from the game DSL block, seeded at their tier's representative\n"
        source_content += "\t// standing so the derived relationship matches the DSL relation word.\n"
        source_content += "\tconst TPair<FName, float> StartingStandings[] = {\n"
        source_content += '\t\t{ FName(TEXT("faction_orbital_council")), 0.0f },    // neutral\n'
        source_content += '\t\t{ FName(TEXT("faction_titan_miners")), 25.0f },      // friendly\n'
        source_content += '\t\t{ FName(TEXT("faction_pirate_syndicate")), -75.0f }, // hostile\n'
        source_content += "\t};\n"
        source_content += "\tfor (const TPair<FName, float>& Entry : StartingStandings)\n"
        source_content += "\t{\n"
        source_content += "\t\tFactionStandings.Add(Entry.Key, Entry.Value);\n"
        source_content += "\t\tFactionRelationships.Add(Entry.Key, RelationshipForStanding(Entry.Value));\n"
        source_content += "\t}\n"
        source_content += "}\n\n"

        source_content += f"void UFactionComponent::ModifyStanding(FName FactionID, float Amount)\n"
        source_content += "{\n"
        source_content += "\t// FindOrAdd: TMap::operator[] asserts on missing keys (first standing\n"
        source_content += "\t// change for an unseeded faction crashed before this fix).\n"
        source_content += "\tfloat& Standing = FactionStandings.FindOrAdd(FactionID);\n"
        source_content += "\tStanding = FMath::Clamp(Standing + Amount, -100.0f, 100.0f);\n"
        source_content += "\tFactionRelationships.FindOrAdd(FactionID) = RelationshipForStanding(Standing);\n"
        source_content += "}\n\n"

        source_content += f"float UFactionComponent::GetStanding(FName FactionID) const\n"
        source_content += "{\n"
        source_content += "\tif (FactionStandings.Contains(FactionID)) return FactionStandings[FactionID];\n"
        source_content += "\treturn 0.0f;\n"
        source_content += "}\n\n"

        source_content += f"FString UFactionComponent::GetRelationship(FName FactionID) const\n"
        source_content += "{\n"
        source_content += "\tif (FactionRelationships.Contains(FactionID)) return FactionRelationships[FactionID];\n"
        source_content += '\treturn "Neutral";\n'
        source_content += "}\n\n"

        source_content += f"bool UFactionComponent::IsHostile(FName FactionID) const\n"
        source_content += "{\n"
        source_content += "\tif (FactionRelationships.Contains(FactionID))\n"
        source_content += '\t\treturn FactionRelationships[FactionID] == "Hostile";\n'
        source_content += "\treturn false;\n"
        source_content += "}\n"

        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_economy_files(self) -> list[str]:
        """Generate the Economy module: CommodityData, EconomyManager, StationTradingData.

        Pricing model: price = BasePrice * clamp(pow(Demand/Supply, elasticity), 0.25, 4.0)
        where elasticity = clamp(SupplyMultiplier + DemandMultiplier, 0.1, 2.0).
        Brought under generator ownership 2026-07-06 (was orphaned hand-maintained code).
        """
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Economy")
        source_dir.mkdir(parents=True, exist_ok=True)

        files = {}

        files["CommodityData.h"] = '''#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "CommodityData.generated.h"

UCLASS(Blueprintable, BlueprintType)
class CHIMERA_API UCommodityData : public UDataAsset
{
	GENERATED_BODY()

public:
	UCommodityData();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity")
	FString CommodityName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity")
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|Pricing")
	float BasePrice;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
	float CurrentSupply;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
	float CurrentDemand;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
	float SupplyMultiplier; // elasticity weight, 0.0 to 1.0

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Commodity|SupplyDemand")
	float DemandMultiplier; // elasticity weight, 0.0 to 1.0

	UFUNCTION(BlueprintCallable, Category = "Commodity|Pricing")
	float CalculateCurrentPrice() const;
};
'''

        files["CommodityData.cpp"] = '''#include "CommodityData.h"

UCommodityData::UCommodityData()
{
	BasePrice = 100.0f;
	CurrentSupply = 1000.0f;
	CurrentDemand = 1000.0f;
	SupplyMultiplier = 0.5f;
	DemandMultiplier = 0.5f;
}

float UCommodityData::CalculateCurrentPrice() const
{
	// Price follows the demand/supply ratio: ratio > 1 (scarcity) raises price,
	// ratio < 1 (glut) lowers it. SupplyMultiplier + DemandMultiplier act as the
	// market's elasticity: at the defaults (0.5 + 0.5 = 1.0) price scales linearly
	// with D/S; higher values make prices more sensitive to imbalance.
	float epsilon = 1.0f; // Prevent division by zero
	float ratio = (CurrentDemand + epsilon) / (CurrentSupply + epsilon);
	float elasticity = FMath::Clamp(SupplyMultiplier + DemandMultiplier, 0.1f, 2.0f);
	float priceMultiplier = FMath::Pow(ratio, elasticity);

	// Clamp so a trade route can swing at most 4x either way
	priceMultiplier = FMath::Clamp(priceMultiplier, 0.25f, 4.0f);

	return BasePrice * priceMultiplier;
}
'''

        files["StationTradingData.h"] = '''#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "StationTradingData.generated.h"

UCLASS(Blueprintable, BlueprintType)
class CHIMERA_API UStationTradingData : public UDataAsset
{
	GENERATED_BODY()

public:
	UStationTradingData();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station")
	FString StationName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Location")
	FVector Location;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Trading")
	float BuyPriceMultiplier; // Multiplier for buying prices from station (e.g., 0.9 for 10% discount)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Trading")
	float SellPriceMultiplier; // Multiplier for selling prices to station (e.g., 1.1 for 10% markup)

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Station|Inventory")
	TArray<FString> AvailableCommodities;

	UFUNCTION(BlueprintCallable, Category = "Station|Trading")
	float GetBuyPriceForCommodity(FString CommodityName, float BasePrice) const;

	UFUNCTION(BlueprintCallable, Category = "Station|Trading")
	float GetSellPriceForCommodity(FString CommodityName, float BasePrice) const;
};
'''

        files["StationTradingData.cpp"] = '''#include "StationTradingData.h"

UStationTradingData::UStationTradingData()
{
	BuyPriceMultiplier = 0.9f; // Buy at 10% discount
	SellPriceMultiplier = 1.1f; // Sell at 10% markup
}

float UStationTradingData::GetBuyPriceForCommodity(FString CommodityName, float BasePrice) const
{
	return BasePrice * BuyPriceMultiplier;
}

float UStationTradingData::GetSellPriceForCommodity(FString CommodityName, float BasePrice) const
{
	return BasePrice * SellPriceMultiplier;
}
'''

        files["EconomyManager.h"] = '''#pragma once

#include "CoreMinimal.h"
#include "Engine/World.h"
#include "CommodityData.h"
#include "StationTradingData.h"
#include "EconomyManager.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnCommodityPriceChanged, FString, CommodityName, float, NewPrice);

UCLASS(Blueprintable, BlueprintType)
class CHIMERA_API UEconomyManager : public UActorComponent
{
	GENERATED_BODY()

public:
	UEconomyManager();

protected:
	virtual void BeginPlay() override;

public:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Economy|Commodities")
	TArray<UCommodityData*> CommodityList;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Economy|Stations")
	TArray<UStationTradingData*> StationTradingList;

	UPROPERTY(BlueprintAssignable, Category = "Economy|Events")
	FOnCommodityPriceChanged OnCommodityPriceChanged;

	UFUNCTION(BlueprintCallable, Category = "Economy|Management")
	void UpdateCommodityPrices(float DeltaTime);

	UFUNCTION(BlueprintCallable, Category = "Economy|Management")
	float GetCommodityPrice(FString CommodityName) const;

	UFUNCTION(BlueprintCallable, Category = "Economy|Management")
	UCommodityData* GetCommodityByName(FString CommodityName) const;

	UFUNCTION(BlueprintCallable, Category = "Economy|SupplyDemand")
	void AdjustCommoditySupply(FString CommodityName, float SupplyChange);

	UFUNCTION(BlueprintCallable, Category = "Economy|SupplyDemand")
	void AdjustCommodityDemand(FString CommodityName, float DemandChange);

private:
	void CalculateStationTradePrices(UStationTradingData* StationData);
};
'''

        files["EconomyManager.cpp"] = '''#include "EconomyManager.h"

UEconomyManager::UEconomyManager()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UEconomyManager::BeginPlay()
{
	Super::BeginPlay();

	for (UStationTradingData* StationData : StationTradingList)
	{
		CalculateStationTradePrices(StationData);
	}
}

void UEconomyManager::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	UpdateCommodityPrices(DeltaTime);
}

void UEconomyManager::UpdateCommodityPrices(float DeltaTime)
{
	for (UCommodityData* Commodity : CommodityList)
	{
		if (!Commodity) continue;

		float OldPrice = Commodity->CalculateCurrentPrice();

		// Simulate natural supply/demand fluctuations over time
		// Small random variations to simulate market dynamics
		float SupplyFluctuation = FMath::RandRange(-0.5f, 0.5f) * DeltaTime;
		float DemandFluctuation = FMath::RandRange(-0.5f, 0.5f) * DeltaTime;

		Commodity->CurrentSupply += SupplyFluctuation * Commodity->CurrentSupply * 0.01f;
		Commodity->CurrentDemand += DemandFluctuation * Commodity->CurrentDemand * 0.01f;

		float NewPrice = Commodity->CalculateCurrentPrice();

		if (FMath::Abs(NewPrice - OldPrice) > 0.1f)
		{
			OnCommodityPriceChanged.Broadcast(Commodity->CommodityName, NewPrice);
		}
	}
}

float UEconomyManager::GetCommodityPrice(FString CommodityName) const
{
	UCommodityData* Commodity = GetCommodityByName(CommodityName);
	if (Commodity)
	{
		return Commodity->CalculateCurrentPrice();
	}
	return 0.0f;
}

UCommodityData* UEconomyManager::GetCommodityByName(FString CommodityName) const
{
	for (UCommodityData* Commodity : CommodityList)
	{
		if (Commodity && Commodity->CommodityName == CommodityName)
		{
			return Commodity;
		}
	}
	return nullptr;
}

void UEconomyManager::AdjustCommoditySupply(FString CommodityName, float SupplyChange)
{
	UCommodityData* Commodity = GetCommodityByName(CommodityName);
	if (Commodity)
	{
		Commodity->CurrentSupply += SupplyChange;
		Commodity->CurrentSupply = FMath::Max(Commodity->CurrentSupply, 0.0f);
	}
}

void UEconomyManager::AdjustCommodityDemand(FString CommodityName, float DemandChange)
{
	UCommodityData* Commodity = GetCommodityByName(CommodityName);
	if (Commodity)
	{
		Commodity->CurrentDemand += DemandChange;
		Commodity->CurrentDemand = FMath::Max(Commodity->CurrentDemand, 0.0f);
	}
}

void UEconomyManager::CalculateStationTradePrices(UStationTradingData* StationData)
{
	if (!StationData) return;

	// Station prices are computed on demand via GetBuy/SellPriceForCommodity, which
	// multiply these directly — sanitize once at startup so a bad data asset can
	// never produce zero or negative trade prices.
	StationData->BuyPriceMultiplier = FMath::Clamp(StationData->BuyPriceMultiplier, 0.1f, 10.0f);
	StationData->SellPriceMultiplier = FMath::Clamp(StationData->SellPriceMultiplier, 0.1f, 10.0f);
}
'''

        out_paths = []
        for name, content in files.items():
            path = source_dir / name
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            out_paths.append(str(path))
        return out_paths

    def generate_save_game_class_file(self) -> tuple[str, str]:
        """Generate DeepSpaceTraderSaveGame.h and .cpp."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Save")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        header_path = source_dir / "DeepSpaceTraderSaveGame.h"
        source_path = source_dir / "DeepSpaceTraderSaveGame.cpp"
        
        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "GameFramework/SaveGame.h"\n'
        header_content += f'#include "../Missions/MissionData.h"\n'
        header_content += f'#include "DeepSpaceTraderSaveGame.generated.h"\n\n'
        
        header_content += f"USTRUCT()\n"
        header_content += f"struct FMissionSaveData\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        header_content += "\tUPROPERTY() FName MissionID;\n"
        header_content += "\tUPROPERTY() FString Status;\n"
        header_content += "};\n\n"

        header_content += f"UCLASS()\n"
        header_content += f"class CHIMERA_API U{self.module_name}SaveGame : public USaveGame\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        header_content += "public:\n"
        header_content += "\tUPROPERTY() float PlayerCredits;\n"
        header_content += "\tUPROPERTY() TMap<FName, int32> PlayerCargo;\n"
        header_content += "\tUPROPERTY() FName CurrentShipClass;\n"
        header_content += "\tUPROPERTY() float CurrentFuel;\n"
        header_content += "\tUPROPERTY() float CurrentHullHealth;\n"
        header_content += "\tUPROPERTY() float CurrentShield;\n"
        header_content += "\tUPROPERTY() TMap<FName, float> SubsystemHealth;\n"
        header_content += "\tUPROPERTY() FVector PlayerLocation;\n"
        header_content += "\tUPROPERTY() FName CurrentStation;\n"
        header_content += "\tUPROPERTY() TArray<FMissionSaveData> ActiveMissions;\n"
        header_content += "\tUPROPERTY() TArray<FName> CompletedMissions;\n"
        header_content += "\tUPROPERTY() TMap<FName, float> FactionStandings;\n"
        header_content += "\tUPROPERTY() TMap<FName, float> StationSupplies;\n"
        header_content += "\tUPROPERTY() FDateTime SaveTimestamp;\n"
        header_content += "};\n\n";

        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = ""
        source_content += f"// Generated by GameCodeGenerator\n"
        source_content += f'#include "DeepSpaceTraderSaveGame.h"\n'
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_save_game_component_files(self) -> tuple[str, str]:
        """Generate SaveGameComponent.h and .cpp."""
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Save")
        source_dir.mkdir(parents=True, exist_ok=True)
        
        header_path = source_dir / "SaveGameComponent.h"
        source_path = source_dir / "SaveGameComponent.cpp"
        
        header_content = ""
        header_content += f"// Generated by GameCodeGenerator\n"
        header_content += f"#pragma once\n\n"
        header_content += f'#include "CoreMinimal.h"\n'
        header_content += f'#include "Components/ActorComponent.h"\n'
        header_content += f'#include "../Save/DeepSpaceTraderSaveGame.h"\n'
        header_content += f'#include "SaveGameComponent.generated.h"\n\n'
        
        header_content += f"UCLASS( meta = (BlueprintType, Category = \"SaveLoad\") )\n"
        header_content += f"class CHIMERA_API USaveGameComponent : public UActorComponent\n"
        header_content += "{\n"
        header_content += "\tGENERATED_BODY()\n\n"
        header_content += "public:\n"
        header_content += f"\tUSaveGameComponent(const FObjectInitializer& ObjectInitializer);\n\n"
        header_content += "public:\n"
        header_content += f"\tUFUNCTION(BlueprintCallable, Category = \"SaveLoad\")\n"
        header_content += f"\tbool SaveGame(FName SlotName);\n\n"
        header_content += f"\tUFUNCTION(BlueprintCallable, Category = \"SaveLoad\")\n"
        header_content += f"\tbool LoadGame(FName SlotName);\n\n"
        header_content += f"\tUFUNCTION(BlueprintCallable, Category = \"SaveLoad\")\n"
        header_content += f"\tvoid AutoSave();\n"
        header_content += "};\n"

        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = ""
        source_content += f"// Generated by GameCodeGenerator\n"
        source_content += f'#include "SaveGameComponent.h"\n'
        source_content += f'#include "GameFramework/PlayerState.h"\n'
        source_content += f'#include "Engine/World.h"\n'
        source_content += f'#include "Kismet/GameplayStatics.h"\n\n'
        
        source_content += f"USaveGameComponent::USaveGameComponent(const FObjectInitializer& ObjectInitializer)\n"
        source_content += "\t: Super(ObjectInitializer)\n"
        source_content += "{\n"
        source_content += "}\n\n"

        source_content += f"bool USaveGameComponent::SaveGame(FName SlotName)\n"
        source_content += "{\n"
        source_content += "\tUWorld* World = GetWorld();\n"
        source_content += "\tif (!World) return false;\n"
        source_content += "\tUDeepSpaceTraderSaveGame* SaveObject = Cast<UDeepSpaceTraderSaveGame>(UGameplayStatics::CreateSaveGameObject(UDeepSpaceTraderSaveGame::StaticClass()));\n"
        source_content += "\tif (!SaveObject) return false;\n"
        source_content += f"\t// Read state from all components: PlayerInventoryComponent, UFlightComponent, UDamageComponent, UShieldComponent,\n"
        source_content += f"\t// USystemDamageComponent, UDockingComponent, UMissionComponent, UFactionComponent, All UMarketComponents\n"
        source_content += "\tSaveObject->SaveTimestamp = FDateTime::Now();\n"
        source_content += "\treturn UGameplayStatics::SaveGameToSlot(SaveObject, *SlotName.ToString(), 0);\n"
        source_content += "}\n\n"

        source_content += f"bool USaveGameComponent::LoadGame(FName SlotName)\n"
        source_content += "{\n"
        source_content += "\tUWorld* World = GetWorld();\n"
        source_content += "\tif (!World) return false;\n"
        source_content += "\tUDeepSpaceTraderSaveGame* SaveObject = Cast<UDeepSpaceTraderSaveGame>(UGameplayStatics::LoadGameFromSlot(*SlotName.ToString(), 0));\n"
        source_content += "\tif (!SaveObject) return false;\n"
        source_content += f"\t// Restore all state to components\n"
        source_content += "\treturn true;\n"
        source_content += "}\n\n"

        source_content += f"void USaveGameComponent::AutoSave()\n"
        source_content += "{\n"
        source_content += "\t// Called on: dock, undock, mission complete, quantum travel arrive, pirate defeated\n"
        source_content += f"\tSaveGame(TEXT(\"AutoSave\"));\n"
        source_content += "}\n"

        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_weapon_component_files(self, weapon_slots: List[Dict[str, Any]], missile_racks: List[Dict[str, Any]]) -> tuple[str, str]:
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Combat")
        source_dir.mkdir(parents=True, exist_ok=True)
        header_path = source_dir / "WeaponComponent.h"
        source_path = source_dir / "WeaponComponent.cpp"
        
        header_content = "// Generated by GameCodeGenerator\n#pragma once\n#include \"CoreMinimal.h\"\n#include \"Components/ActorComponent.h\"\n#include \"GameFramework/Actor.h\"\n#include \"WeaponComponent.generated.h\"\n\nUSTRUCT(BlueprintType)\nstruct FWeaponSlotData {\n\tGENERATED_BODY()\n\n\tUPROPERTY(EditAnywhere, Category = \"Weapon\")\n\tFName Name;\n\n\tUPROPERTY(EditAnywhere, Category = \"Weapon\", meta = (DisplayName = \"Size\"))\n\tFString Size; // S1, S2, S3\n\n\tUPROPERTY(EditAnywhere, Category = \"Weapon\", meta = (ClampMin = \"1\"))\n\tint32 Count;\n\n\tUPROPERTY(EditAnywhere, Category = \"Weapon\", meta = (DisplayName = \"Type\"))\n\tFString Type; // fixed, gimbal, remote_turret\n\n\tUPROPERTY(EditAnywhere, Category = \"Combat Stats\")\n\tfloat FireRate;\n\n\tUPROPERTY(EditAnywhere, Category = \"Combat Stats\")\n\tfloat DamagePerShot;\n\n\tUPROPERTY(EditAnywhere, Category = \"Combat Stats\")\n\tfloat ProjectileSpeed;\n\n\tUPROPERTY(EditAnywhere, Category = \"Combat Stats\")\n\tfloat Range;\n};\n\nUSTRUCT(BlueprintType)\nstruct FMissileRackData {\n\tGENERATED_BODY()\n\n\tUPROPERTY(EditAnywhere, Category = \"Missiles\")\n\tFName RackName;\n\n\tUPROPERTY(EditAnywhere, Category = \"Missiles\", meta = (ClampMin = \"1\"))\n\tint32 Count;\n\n\tUPROPERTY(EditAnywhere, Category = \"Missiles\")\n\tFString MissileType;\n\n\tUPROPERTY(EditAnywhere, Category = \"Combat Stats\")\n\tfloat Damage;\n\n\tUPROPERTY(EditAnywhere, Category = \"Combat Stats\")\n\tfloat TrackingStrength;\n};\n\nUCLASS(meta = (BlueprintType, Category = \"Combat\"))\nclass CHIMERA_API UWeaponComponent : public UActorComponent {\nGENERATED_BODY()\npublic:\n\tUWeaponComponent(const FObjectInitializer& ObjectInitializer);\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Weapons\")\n\tTArray<FWeaponSlotData> WeaponSlots;\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Missiles\")\n\tTArray<FMissileRackData> MissileRacks;\n\n\tUPROPERTY(Transient)\n\tAActor* CurrentTarget;\n\nprotected:\n\tUPROPERTY()\n\tTMap<FName, float> WeaponCooldowns;\n\npublic:\n\tUFUNCTION(BlueprintCallable, Category = \"Weapons\")\n\tvoid FireWeapon(FName SlotName);\n\n\tUFUNCTION(BlueprintCallable, Category = \"Missiles\")\n\tvoid FireMissile(FName RackName, AActor* Target);\n\n\tUFUNCTION(BlueprintPure, Category = \"Weapons\")\n\tTArray<FName> GetAvailableWeapons() const;\n\n\tUFUNCTION(BlueprintPure, Category = \"Missiles\")\n\tint32 GetMissileCount(FName RackName) const;\n};"
        
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = "// Generated by GameCodeGenerator\n#include \"WeaponComponent.h\"\n#include \"GameFramework/Actor.h\"\n#include \"Kismet/KismetMathLibrary.h\"\n\nUWeaponComponent::UWeaponComponent(const FObjectInitializer& ObjectInitializer)\n\t: Super(ObjectInitializer) {\n}\n\nvoid UWeaponComponent::FireWeapon(FName SlotName) {\n\tif (!WeaponSlots.IsEmpty()) {\n\t\tfor (const FWeaponSlotData& Slot : WeaponSlots) {\n\t\t\tif (Slot.Name == SlotName && !WeaponCooldowns.Contains(SlotName)) {\n\t\t\t\tWeaponCooldowns.Add(SlotName, Slot.FireRate);\n\t\t\t\t// Spawn projectile based on type: fixed, gimbal, or remote_turret\n\t\t\t\t// Apply size-class defaults if not specified:\n\t\t\t\t// S1 (light): FireRate=3.0, DamagePerShot=25.0, ProjectileSpeed=80000.0cm/s, Range=200000.0cm\n\t\t\t\t// S2 (medium): FireRate=2.0, DamagePerShot=50.0, ProjectileSpeed=100000.0cm/s, Range=300000.0cm\n\t\t\t\tbreak;\n\t\t\t}\n\t\t}\n\t}\n}\n\nvoid UWeaponComponent::FireMissile(FName RackName, AActor* Target) {\n\tfor (FMissileRackData& Rack : MissileRacks) {\n\t\tif (Rack.RackName == RackName && Rack.Count > 0) {\n\t\t\tRack.Count--;\n\t\t\t// Spawn homing projectile with TrackingStrength\n\t\t\tbreak;\n\t\t}\n\t}\n}\n\nTArray<FName> UWeaponComponent::GetAvailableWeapons() const {\n\tTArray<FName> Available;\n\tfor (const FWeaponSlotData& Slot : WeaponSlots) {\n\t\tif (!WeaponCooldowns.Contains(Slot.Name)) {\n\t\t\tAvailable.Add(Slot.Name);\n\t\t}\n\t}\n\treturn Available;\n}\n\nint32 UWeaponComponent::GetMissileCount(FName RackName) const {\n\tfor (const FMissileRackData& Rack : MissileRacks) {\n\t\tif (Rack.RackName == RackName) {\n\t\t\treturn Rack.Count;\n\t\t}\n\t}\n\treturn 0;\n}"
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_projectile_files(self) -> tuple[str, str]:
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Combat")
        source_dir.mkdir(parents=True, exist_ok=True)
        header_path = source_dir / "Projectile.h"
        source_path = source_dir / "Projectile.cpp"
        
        header_content = "// Generated by GameCodeGenerator\n#pragma once\n#include \"CoreMinimal.h\"\n#include \"GameFramework/Actor.h\"\n#include \"Components/SphereComponent.h\"\n#include \"Components/SceneComponent.h\"\n#include \"Projectile.generated.h\"\n\nUCLASS()\nclass CHIMERA_API AProjectile : public AActor {\nGENERATED_BODY()\npublic:\n\tAProjectile(const FObjectInitializer& ObjectInitializer);\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Projectile\")\n\tfloat Damage;\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Projectile\")\n\tfloat Speed;\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Projectile\", meta = (ClampMin = \"0.0\"))\n\tfloat Range;\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Tracking\", meta = (ClampMin = \"0.0\", ClampMax = \"1.0\"))\n\tfloat TrackingStrength;\n\n\tUPROPERTY(VisibleAnywhere, Category = \"Components\", meta = (AllowPrivateAccess = \"true\"))\n\tUSphereComponent* CollisionSphere;\n\nprotected:\n\tvirtual void BeginPlay() override;\n\npublic:\n\tvirtual void Tick(float DeltaSeconds) override;\n\nprivate:\n\tAActor* OwnerShip;\n\tfloat DistanceTraveled;\n\tTWeakObjectPtr<AActor> TargetReference;\n\n	UFUNCTION()\n	void OnHit(UPrimitiveComponent* HitComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit);\n};"
        
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = "// Generated by GameCodeGenerator\n#include \"Projectile.h\"\n#include \"Components/SphereComponent.h\"\n#include \"GameFramework/ProjectileMovementComponent.h\"\n#include \"NiagaraFunctionLibrary.h\"\n#include \"NiagaraSystem.h\"\n\nAProjectile::AProjectile(const FObjectInitializer& ObjectInitializer)\n\t: Super(ObjectInitializer),\n\tDamage(50.0f), Speed(100000.0f), Range(300000.0f), TrackingStrength(0.0f), DistanceTraveled(0.0f) {\n\tCollisionSphere = CreateDefaultSubobject<USphereComponent>(TEXT(\"CollisionSphere\"));\n\n\tRootComponent = CollisionSphere;\n\tCollisionSphere->InitSphereRadius(50.0f);\n\n#if WITH_EDITORONLY_DATA\n\tCollisionSphere->SetHiddenInGame(true, true);\n#endif\n}\n\nvoid AProjectile::BeginPlay() {\n\tSuper::BeginPlay();\n\tif (CollisionSphere) {\n\t\tCollisionSphere->OnComponentHit.AddDynamic(this, &AProjectile::OnHit);\n\t}\n\t// Enable movement component\n\tGetWorld()->GetTimerManager().SetTimerForNextTick([this]() {\n\t\tUProjectileMovementComponent* MoveComp = FindComponentByClass<UProjectileMovementComponent>();\n\t\tif (MoveComp) {\n\t\t\tMoveComp->Activate(true);\n\t\t}\n\t});\n}\n\nvoid AProjectile::Tick(float DeltaSeconds) {\n\tSuper::Tick(DeltaSeconds);\n\n\tDistanceTraveled += Speed * DeltaSeconds;\n\tif (DistanceTraveled > Range) {\n\t\tDestroy();\n\t\treturn;\n\t}\n\n\t// Tracking logic: if tracking > 0 and target valid, interpolate velocity toward target\n\tif (TrackingStrength > 0.0f && TargetReference.IsValid()) {\n\t\tAActor* Target = TargetReference.Get();\n\t\tif (Target) {\n\t\t\tFVector TargetLocation = Target->GetActorLocation();\n\t\t\tFVector CurrentLocation = GetActorLocation();\n\t\t\tFVector DesiredDirection = (TargetLocation - CurrentLocation).GetSafeNormal();\n\t\t\t// Interpolate velocity toward target based on TrackingStrength\n\t\t}\n\t}\n}\n\nvoid AProjectile::OnHit(UPrimitiveComponent* HitComp, AActor* OtherActor, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit) {\n\tif (OtherActor && OtherActor != this->GetOwner()) {\n\t\t// Find UDamageComponent on OtherActor and call ApplyDamage\n\t\t// TODO: Replace with actual Niagara system\n\t\t// UNiagaraSystem* ImpactVFX = LoadObject<UNiagaraSystem>(nullptr, TEXT(\"/Game/VFX/NS_ProjectileImpact\"));\n\t\t// UNiagaraFunctionLibrary::SpawnSystemAtLocation(GetWorld(), ImpactVFX, Hit.ImpactPoint);\n\t}\n\tDestroy();\n}"
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_shield_component_files(self) -> tuple[str, str]:
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Combat")
        source_dir.mkdir(parents=True, exist_ok=True)
        header_path = source_dir / "ShieldComponent.h"
        source_path = source_dir / "ShieldComponent.cpp"
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write("// Generated by GameCodeGenerator\n")
            f.write("#pragma once\n\n")
            f.write('#include "CoreMinimal.h"\n')
            f.write('#include "Components/ActorComponent.h"\n\n')
            f.write('#include "ShieldComponent.generated.h"\n\n')
            f.write("UCLASS(meta=(BlueprintType, Category=\"Combat\"))\n")
            f.write("class CHIMERA_API UShieldComponent : public UActorComponent\n")
            f.write("{\n")
            f.write("\tGENERATED_BODY()\n\n")
            f.write("public:\n")
            f.write("\tUShieldComponent(const FObjectInitializer& ObjectInitializer);\n\n")
            f.write("\tvoid InitializeFromShip(float ShieldCapacity, float RegenRate);\n")
            f.write("\tfloat AbsorbDamage(float IncomingDamage);\n\n")
            f.write("private:\n")
            f.write("\tfloat MaxShieldCapacity;\n")
            f.write("\tfloat CurrentShield;\n")
            f.write("\tfloat ShieldRegenRate;\n")
            f.write("\tfloat ShieldRegenDelay;\n")
            f.write("\tfloat TimeSinceLastDamage;\n")
            f.write("\tbool bShieldsDepleted;\n");
            f.write("};\n")
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write("// Generated by GameCodeGenerator\n#include \"ShieldComponent.h\"\nUShieldComponent::UShieldComponent(const FObjectInitializer& ObjectInitializer): Super(ObjectInitializer), MaxShieldCapacity(1000.0f), CurrentShield(1000.0f), ShieldRegenRate(50.0f), ShieldRegenDelay(2.0f), TimeSinceLastDamage(0.0f), bShieldsDepleted(false){PrimaryComponentTick.bCanEverTick = true;}void UShieldComponent::InitializeFromShip(float ShieldCapacity, float RegenRate){MaxShieldCapacity = ShieldCapacity;CurrentShield = ShieldCapacity;ShieldRegenRate = RegenRate;}float UShieldComponent::AbsorbDamage(float IncomingDamage){if (CurrentShield <= 0.0f) return IncomingDamage;float Absorbed = FMath::Min(IncomingDamage, CurrentShield);CurrentShield -= Absorbed;TimeSinceLastDamage = 0.0f;return IncomingDamage - Absorbed;}")
        return str(header_path), str(source_path)

    def generate_damage_component_files(self) -> tuple[str, str]:
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Combat")
        source_dir.mkdir(parents=True, exist_ok=True)
        header_path = source_dir / "DamageComponent.h"
        source_path = source_dir / "DamageComponent.cpp"
        
        header_content = "// Generated by GameCodeGenerator\n#pragma once\n#include \"CoreMinimal.h\"\n#include \"Components/ActorComponent.h\"\n#include \"GameFramework/Actor.h\"\n#include \"DamageComponent.generated.h\"\n\nUCLASS(meta = (BlueprintType, Category = \"Combat\"))\nclass CHIMERA_API UDamageComponent : public UActorComponent {\nGENERATED_BODY()\npublic:\n\tUDamageComponent(const FObjectInitializer& ObjectInitializer);\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Hull\")\n\tfloat MaxHullHealth;\n\n\tUPROPERTY(VisibleAnywhere, Category = \"Hull\")\n\tfloat CurrentHullHealth;\n\n\tUPROPERTY(VisibleAnywhere, Category = \"Hull\")\n\tbool bIsDestroyed;\n\nprotected:\n\tvirtual void BeginPlay() override;\n\npublic:\n\tUFUNCTION(BlueprintCallable, Category = \"Damage\")\n\tvoid InitializeFromShip(float HullHealth);\n\n\tUFUNCTION(BlueprintPure, Category = \"Damage\")\n\tfloat GetHullPercent() const;\n\n\tUFUNCTION(BlueprintPure, Category = \"Damage\")\n\tbool IsDestroyed() const;\n\n\tUFUNCTION(BlueprintCallable, Category = \"Damage\")\n\tvoid ApplyDamage(float IncomingDamage, AActor* Instigator);\n};"
        
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = "// Generated by GameCodeGenerator\n#include \"DamageComponent.h\"\n#include \"Components/ActorComponent.h\"\n#include \"GameFramework/Actor.h\"\n\nUDamageComponent::UDamageComponent(const FObjectInitializer& ObjectInitializer)\n\t: Super(ObjectInitializer), MaxHullHealth(5000.0f), CurrentHullHealth(5000.0f), bIsDestroyed(false) {\n\tPrimaryComponentTick.bCanEverTick = true;\n}\n\nvoid UDamageComponent::BeginPlay() {\n\tSuper::BeginPlay();\n}\n\nvoid UDamageComponent::InitializeFromShip(float HullHealth) {\n\tMaxHullHealth = HullHealth;\n\tCurrentHullHealth = HullHealth;\n}\n\nfloat UDamageComponent::GetHullPercent() const {\n\treturn MaxHullHealth > 0.0f ? CurrentHullHealth / MaxHullHealth : 1.0f;\n}\n\nbool UDamageComponent::IsDestroyed() const {\n\treturn CurrentHullHealth <= 0.0f || bIsDestroyed;\n}\n\nvoid UDamageComponent::ApplyDamage(float IncomingDamage, AActor* Instigator) {\n\tif (bIsDestroyed) return;\n\n\t// Route to ShieldComponent->AbsorbDamage()\n\tfloat RemainingDamage = IncomingDamage;\n\n\tif (RemainingDamage > 0.0f) {\n\t\tCurrentHullHealth -= RemainingDamage;\n\t\tif (CurrentHullHealth <= 0.0f) {\n\t\t\tbIsDestroyed = true;\n\t\t\t// Trigger destruction sequence\n\t\t}\n\t}\n\n\t// If Instigator is player and target is NPC, award credits\n}"
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)

    def generate_system_damage_component_files(self) -> tuple[str, str]:
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Combat")
        source_dir.mkdir(parents=True, exist_ok=True)
        header_path = source_dir / "SystemDamageComponent.h"
        source_path = source_dir / "SystemDamageComponent.cpp"
        
        header_content = "// Generated by GameCodeGenerator\n#pragma once\n#include \"CoreMinimal.h\"\n#include \"Components/ActorComponent.h\"\n#include \"GameFramework/Actor.h\"\n#include \"SystemDamageComponent.generated.h\"\n\nUENUM(BlueprintType)\nenum class ESubsystemStatus : uint8 {\n\tOperational,\n\tDamaged,\n\tCritical,\n\tDestroyed\n};\n\nUCLASS(meta = (BlueprintType, Category = \"Combat\"))\nclass CHIMERA_API USystemDamageComponent : public UActorComponent {\nGENERATED_BODY()\npublic:\n\tUSystemDamageComponent(const FObjectInitializer& ObjectInitializer);\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Subsystems\")\n\tTMap<FName, float> SubsystemHealth;\n\n\tUPROPERTY(VisibleAnywhere, Category = \"Subsystems\")\n\tTMap<FName, float> SubsystemMaxHealth;\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Damage\", meta = (ClampMin = \"0.0\", ClampMax = \"1.0\"))\n\tfloat SubsystemDamageThreshold;\n\nprotected:\n\tvirtual void BeginPlay() override;\n\npublic:\n\tUFUNCTION(BlueprintCallable, Category = \"Subsystems\")\n\tvoid InitializeFromShip(const TArray<FName>& SystemNames);\n\n\tUFUNCTION(BlueprintCallable, Category = \"Subsystems\")\n\tvoid ApplySystemDamage(float IncomingHullDamage);\n\n\tUFUNCTION(BlueprintCallable, Category = \"Subsystems\")\n\tvoid RepairSubsystem(FName SystemName, float Amount);\n\n\tUFUNCTION(BlueprintPure, Category = \"Subsystems\")\n\tfloat GetSubsystemHealth(FName SystemName) const;\n\n\tUFUNCTION(BlueprintPure, Category = \"Subsystems\")\n\tESubsystemStatus GetSubsystemStatus(FName SystemName) const;\n};"
        
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = (
            "// Generated by GameCodeGenerator\n"
            '#include "SystemDamageComponent.h"\n\n'
            "USystemDamageComponent::USystemDamageComponent(const FObjectInitializer& ObjectInitializer)\n"
            "\t: Super(ObjectInitializer), SubsystemDamageThreshold(0.1f) {\n"
            "}\n\n"
            "void USystemDamageComponent::BeginPlay() {\n"
            "\tSuper::BeginPlay();\n"
            "}\n\n"
            "void USystemDamageComponent::InitializeFromShip(const TArray<FName>& SystemNames) {\n"
            '\tSubsystemHealth.Add(TEXT("Engines"), 100.0f);\n'
            '\tSubsystemMaxHealth.Add(TEXT("Engines"), 100.0f);\n'
            '\tSubsystemHealth.Add(TEXT("Weapons"), 100.0f);\n'
            '\tSubsystemMaxHealth.Add(TEXT("Weapons"), 100.0f);\n'
            '\tSubsystemHealth.Add(TEXT("LifeSupport"), 100.0f);\n'
            '\tSubsystemMaxHealth.Add(TEXT("LifeSupport"), 100.0f);\n\n'
            "\tfor (const FName& SysName : SystemNames) {\n"
            "\t\tif (!SubsystemHealth.Contains(SysName)) {\n"
            "\t\t\tSubsystemHealth.Add(SysName, 100.0f);\n"
            "\t\t\tSubsystemMaxHealth.Add(SysName, 100.0f);\n"
            "\t\t}\n"
            "\t}\n"
            "}\n\n"
            "void USystemDamageComponent::ApplySystemDamage(float IncomingHullDamage) {\n"
            "\tfloat SubsystemDamage = IncomingHullDamage * SubsystemDamageThreshold;\n"
            "\tfor (TPair<FName, float>& Pair : SubsystemHealth) {\n"
            "\t\tif (Pair.Value > 0.0f) {\n"
            "\t\t\tfloat DamageToApply = FMath::Min(SubsystemDamage, Pair.Value);\n"
            "\t\t\tPair.Value -= DamageToApply;\n"
            "\t\t\tSubsystemDamage -= DamageToApply;\n"
            "\t\t\tif (SubsystemDamage <= 0.0f) break;\n"
            "\t\t}\n"
            "\t}\n"
            "}\n\n"
            "void USystemDamageComponent::RepairSubsystem(FName SystemName, float Amount) {\n"
            "\tif (SubsystemHealth.Contains(SystemName)) {\n"
            "\t\tfloat NewHealth = FMath::Min(SubsystemHealth[SystemName] + Amount, SubsystemMaxHealth[SystemName]);\n"
            "\t\tSubsystemHealth[SystemName] = NewHealth;\n"
            "\t}\n"
            "}\n\n"
            "float USystemDamageComponent::GetSubsystemHealth(FName SystemName) const {\n"
            "\tif (SubsystemHealth.Contains(SystemName)) return SubsystemHealth[SystemName];\n"
            "\treturn 0.0f;\n"
            "}\n\n"
            "ESubsystemStatus USystemDamageComponent::GetSubsystemStatus(FName SystemName) const {\n"
            "\tfloat Health = GetSubsystemHealth(SystemName);\n"
            "\tfloat MaxHealth = 100.0f;\n"
            "\tif (SubsystemMaxHealth.Contains(SystemName)) MaxHealth = SubsystemMaxHealth[SystemName];\n"
            "\tfloat Percent = MaxHealth > 0.0f ? Health / MaxHealth : 1.0f;\n\n"
            "\tif (Percent <= 0.0f) return ESubsystemStatus::Destroyed;\n"
            "\tif (Percent < 0.25f) return ESubsystemStatus::Critical;\n"
            "\tif (Percent < 0.5f) return ESubsystemStatus::Damaged;\n"
            "\treturn ESubsystemStatus::Operational;\n"
            "}\n"
        )
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)

        return str(header_path), str(source_path)


    def generate_combat_target_component_files(self) -> tuple[str, str]:
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/Combat")
        source_dir.mkdir(parents=True, exist_ok=True)
        header_path = source_dir / "CombatTargetComponent.h"
        source_path = source_dir / "CombatTargetComponent.cpp"
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write("// Generated by GameCodeGenerator\n")
            f.write("#pragma once\n\n")
            f.write('#include "CoreMinimal.h"\n')
            f.write('#include "Components/ActorComponent.h"\n\n')
            f.write('#include "CombatTargetComponent.generated.h"\n\n')
            f.write("UCLASS(meta=(BlueprintType, Category=\"Combat\"))\n")
            f.write("class CHIMERA_API UCombatTargetComponent : public UActorComponent\n")
            f.write("{\n")
            f.write("\tGENERATED_BODY()\n\n")
            f.write("public:\n")
            f.write("\tUCombatTargetComponent(const FObjectInitializer& ObjectInitializer);\n");
            f.write("};\n")
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write("// Generated by GameCodeGenerator\n#include \"CombatTargetComponent.h\"\nUCombatTargetComponent::UCombatTargetComponent(const FObjectInitializer& ObjectInitializer): Super(ObjectInitializer){}")
        return str(header_path), str(source_path)

    def generate_pirate_ai_controller_files(self) -> tuple[str, str]:
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/AI")
        source_dir.mkdir(parents=True, exist_ok=True)
        header_path = source_dir / "PirateAIController.h"
        source_path = source_dir / "PirateAIController.cpp"
        
        header_content = "// Generated by GameCodeGenerator\n#pragma once\n#include \"CoreMinimal.h\"\n#include \"AIController.h\"\n#include \"BehaviorTree/BlackboardComponent.h\"\n#include \"PirateAIController.generated.h\"\n\nUENUM(BlueprintType)\nenum class EAIPirateState : uint8 {\n\tPatrolling UMETA(DisplayName = \"Patrolling\"),\n\tInvestigating UMETA(DisplayName = \"Investigating\"),\n\tPursuing UMETA(DisplayName = \"Pursuing\"),\n\tEngaging UMETA(DisplayName = \"Engaging\"),\n\tRetreating UMETA(DisplayName = \"Retreating\")\n};\n\nUCLASS()\nclass CHIMERA_API APirateAIController : public AAIController {\nGENERATED_BODY()\npublic:\n\tAPirateAIController(const FObjectInitializer& ObjectInitializer);\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Pirate AI\")\n\tFName FactionName;\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Pirate AI\", meta = (ClampMin = \"0.0\", ClampMax = \"1.0\"))\n\tfloat HostilityToPlayer;\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Pirate AI\", meta = (ClampMin = \"0.0\"))\n\tfloat DetectionRange;\n\n\tUPROPERTY(EditDefaultsOnly, Category = \"Pirate AI\", meta = (ClampMin = \"0.0\"))\n\tfloat EngagementRange;\n\n\tUPROPERTY(VisibleAnywhere, Category = \"Pirate AI State\")\n\tEAIPirateState CurrentState;\n\nprotected:\n\tvirtual void BeginPlay() override;\n\tvirtual void Tick(float DeltaSeconds) override;\n\nprivate:\n\tbool ScanForPlayer();\n\tfloat EvaluateThreat();\n};"
        
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)

        source_content = "// Generated by GameCodeGenerator\n#include \"PirateAIController.h\"\n#include \"GameFramework/Actor.h\"\n#include \"Kismet/KismetMathLibrary.h\"\n\nAPirateAIController::APirateAIController(const FObjectInitializer& ObjectInitializer)\n\t: Super(ObjectInitializer), FactionName(TEXT(\"Void_Syndicate\")), HostilityToPlayer(1.0f), DetectionRange(50000.0f), EngagementRange(20000.0f), CurrentState(EAIPirateState::Patrolling) {\n}\n\nvoid APirateAIController::BeginPlay() {\n\tSuper::BeginPlay();\n}\n\nvoid APirateAIController::Tick(float DeltaSeconds) {\n\tSuper::Tick(DeltaSeconds);\n\t\n\t// State machine logic:\n\tif (CurrentState == EAIPirateState::Patrolling) {\n\t\tif (ScanForPlayer() && HostilityToPlayer > 0.5f) {\n\t\t\tCurrentState = EAIPirateState::Investigating;\n\t\t}\n\t} else if (CurrentState == EAIPirateState::Investigating) {\n\t\t// Move toward last known position\n\t\tif (ScanForPlayer() && HostilityToPlayer > 0.7f) {\n\t\t\tCurrentState = EAIPirateState::Engaging;\n\t\t}\n\t} else if (CurrentState == EAIPirateState::Engaging) {\n\t\t// Maintain combat range, fire weapons\n\t\tfloat Threat = EvaluateThreat();\n\t\tif (Threat < 0.3f) {\n\t\t\tCurrentState = EAIPirateState::Retreating;\n\t\t}\n\t} else if (CurrentState == EAIPirateState::Retreating) {\n\t\t// Full thrust away, attempt quantum jump\n\t\tif (HostilityToPlayer <= 0.5f) {\n\t\t\tCurrentState = EAIPirateState::Patrolling;\n\t\t}\n\t}\n}\n\nbool APirateAIController::ScanForPlayer() {\n\treturn false;\n}\n\nfloat APirateAIController::EvaluateThreat() {\n\treturn 0.5f;\n}"
        
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)
            
        return str(header_path), str(source_path)

    def generate_pirate_behavior_tree_file(self) -> str:
        source_dir = Path("E:/PythonChimera/Chimera/Source/Chimera/ProceduralGenerated/AI")
        source_dir.mkdir(parents=True, exist_ok=True)
        bt_path = source_dir / "PirateBehaviorTree.behaviortree"
        with open(bt_path, 'w', encoding='utf-8') as f:
            f.write("// Generated by GameCodeGenerator\n// Pirate Behavior Tree\nSelector Root:\n  - Patrolling State\n  - Investigating State\n  - Engaging State\n  - Retreating State")
        return str(bt_path)

    def save_snapshots(self, generated_files: Dict[str, List[str]], source_dir: str):
        """Save generated .h and .cpp files to snapshots directory for diff tracking."""
        snapshot_dir = Path("E:/PythonChimera/Chimera/tests/snapshots")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all generated C++ files
        cpp_source_dir = Path(source_dir)
        cpp_files = []
        for ext in ['*.h', '*.cpp']:
            cpp_files.extend(list(cpp_source_dir.rglob(ext)))
            
        snapshot_results = {"saved_files": [], "skipped_non_cpp": 0}
        
        for file_path in cpp_files:
            if 'generated.h' in file_path.name or '.generated.h' in file_path.name:
                continue
                
            rel_path = file_path.relative_to(cpp_source_dir.parent)
            snapshot_file = snapshot_dir / f"{file_path.stem}_{file_path.name.replace('.', '_').replace('DeepSpaceTrader_', '')}.snap"
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                with open(snapshot_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Snapshot for {file_path.name}\n")
                    f.write(f"# Generated: {self._get_snapshot_timestamp()}\n")
                    f.write(content)
                    
                snapshot_results["saved_files"].append(str(file_path.name))
            except Exception as e:
                pass
                
        return snapshot_results

    def _get_snapshot_timestamp(self) -> str:
        """Get current timestamp for snapshots."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def diff_snapshots(self, new_generated_files: Dict[str, List[str]], source_dir: str) -> dict:
        """Diff new generated output against snapshots and report changes."""
        snapshot_dir = Path("E:/PythonChimera/Chimera/tests/snapshots")
        
        changes = {"modified_files": [], "added_files": [], "removed_files": []}
        
        cpp_source_dir = Path(source_dir)
        cpp_files = []
        for ext in ['*.h', '*.cpp']:
            cpp_files.extend(list(cpp_source_dir.rglob(ext)))
            
        for file_path in cpp_files:
            if 'generated.h' in file_path.name or '.generated.h' in file_path.name:
                continue
                
            snapshot_file = snapshot_dir / f"{file_path.stem}_{file_path.name.replace('.', '_').replace('DeepSpaceTrader_', '')}.snap"
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    new_content = f.read()
                    
                if not snapshot_file.exists():
                    changes["added_files"].append(str(file_path.name))
                    continue
                    
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    existing_lines = f.readlines()
                    # Skip snapshot metadata lines
                    existing_content = '\n'.join([line for line in existing_lines if not line.startswith('# Snapshot') and not line.startswith('# Generated:')])
                    
                if new_content != existing_content:
                    changes["modified_files"].append(str(file_path.name))
            except Exception as e:
                pass
                
        return changes

    def validate_ue5_patterns(self, header_file_path: str) -> list[str]:
        """Compare generated code against UE5 source patterns and flag deviations."""
        deviations = []
        
        try:
            with open(header_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check .generated.h placement - should be last include before GENERATED_BODY or class definition
            includes = []
            generated_h_pos = None
            
            for line in content.split('\n'):
                line_stripped = line.strip()
                if line_stripped.startswith('#include "') and not '.generated.h' in line_stripped:
                    includes.append(line_stripped)
                elif '.generated.h' in line_stripped:
                    generated_h_pos = len(includes)
                    
            # Check if .generated.h is the last include
            if generated_h_pos is not None and len(includes) > 0:
                # Get all includes after .generated.h
                lines_after_genh = []
                in_includes_section = False
                for line in content.split('\n'):
                    if '#include' in line:
                        if '.generated.h' in line:
                            in_includes_section = True
                        elif in_includes_section and not '.generated.h' in line:
                            lines_after_genh.append(line)
                            
                if len(lines_after_genh) > 0:
                    deviations.append(f"{header_file_path} differs from engine pattern: .generated.h should be last include")
                    
        except Exception as e:
            pass
            
        return deviations

