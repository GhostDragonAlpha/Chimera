"""
DSL Game Parser — Parses and validates game specifications written in a unified DSL format.

Handles parsing of DSL blocks: game, narrative, gameplay, world, ui, audio, technical, art_direction.
Validates against dsl_game_schema.json.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Route through Graphify interface for mutation logging
try:
    from core.graphify_interface import query, mutate, load_dna_graph, save_dna_graph
except ImportError:
    try:
        from graphify_interface import query, mutate, load_dna_graph, save_dna_graph
    except ImportError:
        def query(*args, **kwargs): return None
        def mutate(*args, **kwargs): return "mutate_dummy"
        def load_dna_graph(): return {"nodes": [], "edges": []}
        def save_dna_graph(*args): pass

try:
    from core.validator import DSLSchemaValidator
except ImportError:
    try:
        from validator import DSLSchemaValidator
    except ImportError:
        class DSLSchemaValidator:
            def __init__(self, schema_path):
                self.schema_path = Path(schema_path)
            
            def validate(self, dsl_json_string: str) -> Tuple[bool, str | None]:
                try:
                    json.loads(dsl_json_string)
                    return True, None
                except Exception as e:
                    return False, str(e)


def extract_block_content(content: str, block_name: str) -> str | None:
    """Extract content between braces for a given block name, handling nested braces."""
    # Find the block name and then locate the opening '{'
    # Pattern: block_name followed by optional content (including quotes, etc.) and then '{'
    # Use word boundary to avoid matching substrings like 'guide' -> 'ui'
    pattern = rf'\b{block_name}\s*[^\{{]*\{{'
    match = re.search(pattern, content)
    if not match:
        return None
    
    start_pos = match.end()
    
    # Count braces to find the matching closing brace
    # We've already consumed the opening '{', so start count at 1
    brace_count = 1
    pos = start_pos
    while pos < len(content):
        if content[pos] == '{':
            brace_count += 1
        elif content[pos] == '}':
            brace_count -= 1
            if brace_count == 0:
                break
        pos += 1
    
    if brace_count == 0:
        return content[start_pos:pos]
    return None


class DSLGameParser:
    """Parses game DSL specifications into structured JSON format."""

    def __init__(self, schema_path: str):
        self.schema_path = Path(schema_path)
        self.validator = DSLSchemaValidator(str(self.schema_path))

    def parse_dsl_string(self, dsl_content: str) -> Dict[str, Any]:
        """Parse DSL string content into structured dictionary."""
        # Basic DSL parsing logic to convert text DSL to JSON structure
        result = {
            "game": {},
            "technical": {},
            "narrative": {},
            "gameplay": {},
            "world": {},
            "ui": {},
            "audio": {},
            "art_direction": {},
            "tests": {},
            "flight_model": {},
            "ship_systems": {},
            "economy_systems": {},
            "level": {},
            "procedural_generation": {}
        }

        # Parse game block
        game_body = extract_block_content(dsl_content, 'game')
        if game_body:
            title_match = re.search(r'game\s+"([^"]+)"', dsl_content)
            if title_match:
                result["game"]["title"] = title_match.group(1)
            
            engine_version_match = re.search(r'engine_version\s*=\s*"([^"]+)"', game_body)
            if engine_version_match:
                result["game"]["engine_version"] = engine_version_match.group(1)
                
            platforms_match = re.search(r'target_platforms\s*=\s*\[(.*?)\]', game_body)
            if platforms_match:
                platforms_str = platforms_match.group(1)
                platforms = [p.strip().strip('"\'') for p in platforms_str.split(',')]
                result["game"]["target_platforms"] = platforms

        # Parse technical block
        tech_body = extract_block_content(dsl_content, 'technical')
        if tech_body:
            network_model_match = re.search(r'network_model\s*=\s*"([^"]+)"', tech_body)
            if network_model_match:
                result["technical"]["network_model"] = network_model_match.group(1)
                
            fps_match = re.search(r'target_fps=(\d+)', tech_body)
            if fps_match:
                result["technical"]["performance"] = {"target_fps": int(fps_match.group(1))}
                
            lod_match = re.search(r'LOD_strategy="([^"]+)"', tech_body)
            if lod_match:
                if "performance" not in result["technical"]:
                    result["technical"]["performance"] = {}
                result["technical"]["performance"]["lod_strategy"] = lod_match.group(1)
                
            modules_match = re.search(r'module_dependencies\s*=\s*\[(.*?)\]', tech_body)
            if modules_match:
                modules_str = modules_match.group(1)
                modules = [m.strip().strip('"\'') for m in modules_str.split(',')]
                result["technical"]["module_dependencies"] = modules

        # Parse narrative block
        narrative_body = extract_block_content(dsl_content, 'narrative')
        if narrative_body:
            # Parse acts
            acts = []
            act_matches = re.findall(r'act\s+"([^"]+)"', narrative_body)
            for act_name in act_matches:
                acts.append({"id": f"act_{len(acts)+1}", "name": act_name})
            if acts:
                result["narrative"]["acts"] = acts
                
            # Parse factions
            factions_list = []
            faction_matches = re.findall(r'\{"id"\s*:\s*"([^"]+)"\s*,\s*"name"\s*:\s*"([^"]+)"\s*,\s*"relation"\s*:\s*"([^"]+)"\}', narrative_body)
            for fm in faction_matches:
                factions_list.append({
                    "id": fm[0],
                    "name": fm[1],
                    "relation": fm[2]
                })
            if factions_list:
                result["narrative"]["factions"] = factions_list
                
            # Parse dialogue trees
            dialogue_trees = []
            dt_matches = re.findall(r'dialogue_tree\s+"([^"]+)"', narrative_body)
            for dt_id in dt_matches:
                dialogue_trees.append({
                    "id": dt_id,
                    "nodes": [{"id": "root", "speaker": "", "text": ""}]
                })
            if dialogue_trees:
                result["narrative"]["dialogue_trees"] = dialogue_trees

        # Parse gameplay block
        gameplay_body = extract_block_content(dsl_content, 'gameplay')
        if gameplay_body:
            # Parse characters
            characters = []
            char_matches = re.findall(r'character\s+"([^"]+)"\s+(?:inherits\s+"([^"]+)")?', gameplay_body)
            for match in char_matches:
                char_name = match[0]
                inherits = match[1] if len(match) > 1 and match[1] else "ACharacter"
                characters.append({"name": char_name, "inherits": inherits})
            if characters:
                result["gameplay"]["characters"] = characters
                
            # Parse abilities
            abilities = []
            ability_matches = re.findall(r'ability\s+"([^"]+)"', gameplay_body)
            for ab_name in ability_matches:
                abilities.append({
                    "name": ab_name,
                    "uses_gas": True,
                    "ability_tags": [f"Ability.{ab_name}"]
                })
            if abilities:
                result["gameplay"]["abilities"] = abilities
                
            # Parse combat system
            combat_system_match = re.search(r'combat_system\s*\{([^}]+)\}', gameplay_body)
            if combat_system_match:
                combat_body = combat_system_match.group(1)
                combat_system = {}
                
                damage_match = re.search(r'damage_formulas\s*=\s*"([^"]+)"', combat_body)
                if damage_match:
                    combat_system["damage_formulas"] = damage_match.group(1)
                    
                hit_reactions_match = re.search(r'hit_reactions\s*=\s*(true|false)', combat_body)
                if hit_reactions_match:
                    combat_system["hit_reactions"] = hit_reactions_match.group(1) == "true"
                    
                status_effects_match = re.search(r'status_effects\s*=\s*\[(.*?)\]', combat_body)
                if status_effects_match:
                    effects_str = status_effects_match.group(1)
                    effects = [e.strip().strip('"\'') for e in effects_str.split(',')]
                    combat_system["status_effects"] = effects
                    
                if combat_system:
                    result["gameplay"]["combat_system"] = combat_system
                    
            # Parse inventory
            inventory_match = re.search(r'inventory\s*\{([^}]+)\}', gameplay_body)
            if inventory_match:
                inv_body = inventory_match.group(1)
                inventory = {}
                
                slots_match = re.search(r'slots\s*=\s*(\d+)', inv_body)
                if slots_match:
                    inventory["slots"] = int(slots_match.group(1))
                    
                equipment_slots_match = re.search(r'equipment_slots\s*=\s*\[(.*?)\]', inv_body)
                if equipment_slots_match:
                    slots_str = equipment_slots_match.group(1)
                    slots = [s.strip().strip('"\'') for s in slots_str.split(',')]
                    inventory["equipment_slots"] = slots
                    
                if inventory:
                    result["gameplay"]["inventory"] = inventory
                    
            # Parse progression
            progression_match = re.search(r'progression\s*\{([^}]+)\}', gameplay_body)
            if progression_match:
                prog_body = progression_match.group(1)
                progression = {}
                
                level_cap_match = re.search(r'level_cap\s*=\s*(\d+)', prog_body)
                if level_cap_match:
                    progression["level_cap"] = int(level_cap_match.group(1))
                    
                skill_points_match = re.search(r'skill_points_per_level\s*=\s*(\d+)', prog_body)
                if skill_points_match:
                    progression["skill_points_per_level"] = int(skill_points_match.group(1))
                    
                if progression:
                    result["gameplay"]["progression"] = progression

        # Parse world block
        world_body = extract_block_content(dsl_content, 'world')
        if world_body:
            # Parse levels
            levels = []
            level_matches = re.findall(r'level\s+"([^"]+)"', world_body)
            for lvl_name in level_matches:
                levels.append({
                    "name": lvl_name,
                    "environment_assets": True,
                    "spawn_points": [{"name": "PlayerStart", "position": "(0,0,100)"}]
                })
            if levels:
                result["world"]["levels"] = levels
                
            # Parse NPCs
            npcs = []
            npc_matches = re.findall(r'npc\s+"([^"]+)"', world_body)
            for npc_name in npc_matches:
                npcs.append({
                    "name": npc_name,
                    "behavior_tree": f"BT_{npc_name}",
                    "dialogue_tree": f"DT_{npc_name}"
                })
            if npcs:
                result["world"]["npcs"] = npcs

        # Parse level block
        level_body = extract_block_content(dsl_content, 'level')
        if level_body:
            level_data = {}
            
            # Parse name
            name_match = re.search(r'name\s*=\s*"([^"]+)"', level_body)
            if name_match:
                level_data["name"] = name_match.group(1)
                
            # Parse player_start location
            player_start_match = re.search(r'player_start\s*\{[^}]*location\s*=\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]', level_body)
            if player_start_match:
                level_data["player_start"] = {
                    "location": [float(player_start_match.group(1)), float(player_start_match.group(2)), float(player_start_match.group(3))]
                }
                
            # Parse skybox_type
            skybox_match = re.search(r'skybox_type\s*=\s*"([^"]+)"', level_body)
            if skybox_match:
                level_data["skybox_type"] = skybox_match.group(1)
                
            # Parse lights
            lights = []
            light_matches = re.findall(r'light\s*\{([^}]+)\}', level_body)
            for lm in light_matches:
                light_type_match = re.search(r'type\s*=\s*"([^"]+)"', lm)
                light_pos_match = re.search(r'position\s*=\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]', lm)
                if light_type_match and light_pos_match:
                    lights.append({
                        "type": light_type_match.group(1),
                        "position": [float(light_pos_match.group(1)), float(light_pos_match.group(2)), float(light_pos_match.group(3))]
                    })
            if lights:
                level_data["lights"] = lights
                
            # Parse world_bounds
            bounds_match = re.search(r'world_bounds\s*\{[^}]*min_location\s*=\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\][^}]*max_location\s*=\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]', level_body)
            if bounds_match:
                level_data["world_bounds"] = {
                    "min_location": [float(bounds_match.group(1)), float(bounds_match.group(2)), float(bounds_match.group(3))],
                    "max_location": [float(bounds_match.group(4)), float(bounds_match.group(5)), float(bounds_match.group(6))]
                }
                
            # Parse station_placements
            stations = []
            station_matches = re.findall(r'station_placement\s+"([^"]+)"\s*\{[^}]*location\s*=\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]', level_body)
            for sm in station_matches:
                stations.append({
                    "station_name": sm[0],
                    "location": [float(sm[1]), float(sm[2]), float(sm[3])]
                })
            if stations:
                level_data["station_placements"] = stations
                
            # Parse planet_placements
            planets = []
            planet_matches = re.findall(r'planet_placement\s+"([^"]+)"\s*\{[^}]*location\s*=\s*\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\][^}]*scale\s*=\s*(\d+(?:\.\d+)?)', level_body)
            for pm in planet_matches:
                planets.append({
                    "planet_name": pm[0],
                    "location": [float(pm[1]), float(pm[2]), float(pm[3])],
                    "scale": float(pm[4])
                })
            if planets:
                level_data["planet_placements"] = planets
                
            if level_data:
                result["level"] = level_data

        # Parse ui block
        ui_body = extract_block_content(dsl_content, 'ui')
        if ui_body:
            hud_elements = []
            
            # Look for elements in various formats:
            # 1. Direct list: health_bar, minimap, ability_cooldowns, quest_tracker
            # 2. Inside widget blocks
            
            # Extract from widget content
            widget_matches = re.findall(r'widget\s+"[^"]+"\s*\{([^}]+)\}', ui_body)
            for wm in widget_matches:
                element_matches = re.findall(r'(health_bar|minimap|ability_cooldowns|quest_tracker|options_resume|options_settings|quit_to_main)', wm)
                hud_elements.extend(element_matches)
                
            # Also extract from direct hud content
            direct_element_matches = re.findall(r'(health_bar|minimap|ability_bar|quest_tracker|ability_cooldowns)', ui_body)
            hud_elements.extend(direct_element_matches)
            
            # Remove duplicates and normalize
            unique_elements = []
            for elem in hud_elements:
                if elem not in unique_elements:
                    unique_elements.append(elem)
                
            if unique_elements or "hud" in ui_body or "widget" in ui_body:
                result["ui"]["hud"] = {
                    "elements": unique_elements if unique_elements else ["health_bar", "minimap", "ability_cooldowns", "quest_tracker"],
                    "using_common_ui": True
                }

        # Parse audio block
        audio_body = extract_block_content(dsl_content, 'audio')
        if audio_body:
            music_cues = []
            music_matches = re.findall(r'music_cue\s+"([^"]+)"', audio_body)
            for mc_name in music_matches:
                music_cues.append({"name": mc_name})
            if music_cues:
                result["audio"]["music_cues"] = music_cues
                
            sfx_list = []
            sfx_matches = re.findall(r'sfx\s+"([^"]+)"', audio_body)
            for sfx_name in sfx_matches:
                sfx_list.append({"name": sfx_name})
            if sfx_list:
                result["audio"]["sfx"] = sfx_list

        # Parse art_direction block
        art_body = extract_block_content(dsl_content, 'art_direction')
        if art_body:
            style_match = re.search(r'style\s*=\s*"([^"]+)"', art_body)
            color_match = re.search(r'color_palette\s*=\s*"([^"]+)"', art_body)
            
            if style_match or color_match:
                result["art_direction"] = {}
                if style_match:
                    result["art_direction"]["style"] = style_match.group(1)
                if color_match:
                    result["art_direction"]["color_palette"] = color_match.group(1)

        # Parse tests block
        tests_body = extract_block_content(dsl_content, 'tests')
        if tests_body:
            test_definitions = []
            # Extract individual test blocks
            test_matches = re.findall(r'test\s+"([^"]+)"\s*\{([^}]+)\}', tests_body)
            for test_name, test_body in test_matches:
                test_def = {
                    "name": test_name,
                    "setup": [],
                    "action": [],
                    "assert": []
                }
                
                # Extract type
                type_match = re.search(r'type\s*=\s*"([^"]+)"', test_body)
                if type_match:
                    test_def["type"] = type_match.group(1)
                else:
                    test_def["type"] = "unit"
                    
                # Extract description
                desc_match = re.search(r'description\s*=\s*"([^"]+)"', test_body)
                if desc_match:
                    test_def["description"] = desc_match.group(1)
                    
                # Extract iterations
                iter_match = re.search(r'iterations\s*=\s*(\d+)', test_body)
                if iter_match:
                    test_def["iterations"] = int(iter_match.group(1))
                else:
                    test_def["iterations"] = 1
                    
                # Extract setup statements
                setup_match = re.search(r'setup\s*\{([^}]+)\}', test_body)
                if setup_match:
                    setup_content = setup_match.group(1)
                    setup_actions = re.findall(r'(spawn_actor|grant_ability|add_item|set_attribute|set_status|set_biome|initialize_market)\s*\(([^)]+)\)', setup_content)
                    for action, params in setup_actions:
                        test_def["setup"].append({"action": action, "params": self._parse_params(params)})
                        
                # Extract action statements
                action_match = re.search(r'action\s*\{([^}]+)\}', test_body)
                if action_match:
                    action_content = action_match.group(1)
                    action_actions = re.findall(r'(activate_ability|npc_attack_target|craft_recipe|advance_market_cycles|wait)\s*\(([^)]+)\)', action_content)
                    for action, params in action_actions:
                        test_def["action"].append({"action": action, "params": self._parse_params(params)})
                        
                # Extract assert statements
                assert_match = re.search(r'assert\s*\{([^}]+)\}', test_body)
                if assert_match:
                    assert_content = assert_match.group(1)
                    assert_exprs = re.findall(r'([\w_]+)\s*(==|>=|<=|>|<|!=)\s*([^\n;]+)', assert_content)
                    for expr, op, expected in assert_exprs:
                        test_def["assert"].append({
                            "expression": expr.strip(),
                            "operator": op.strip(),
                            "expected": expected.strip().replace('_sec', '')
                        })
                        
                test_definitions.append(test_def)
                
            if test_definitions:
                result["tests"] = {"test_definitions": test_definitions}

        # Parse flight_model block
        flight_body = extract_block_content(dsl_content, 'flight_model')
        if flight_body:
            flight_model = {}
            type_match = re.search(r'type\s*=\s*"([^"]+)"', flight_body)
            if type_match:
                flight_model["type"] = type_match.group(1)
                
            thrust_match = re.search(r'thrust_acceleration\s*=\s*([\d.]+)', flight_body)
            if thrust_match:
                flight_model["thrust_acceleration"] = float(thrust_match.group(1))
                
            max_speed_match = re.search(r'max_speed_kmh\s*=\s*(\d+)', flight_body)
            if max_speed_match:
                flight_model["max_speed_kmh"] = int(max_speed_match.group(1))
                
            turn_rate_match = re.search(r'turn_rate_deg_per_sec\s*=\s*(\d+)', flight_body)
            if turn_rate_match:
                flight_model["turn_rate_deg_per_sec"] = int(turn_rate_match.group(1))
                
            damping_match = re.search(r'inertia_damping\s*=\s*([\d.]+)', flight_body)
            if damping_match:
                flight_model["inertia_damping"] = float(damping_match.group(1))
                
            if flight_model:
                result["flight_model"] = flight_model

        # Parse ship_systems block
        ships_body = extract_block_content(dsl_content, 'ship_systems')
        if ships_body:
            ships_list = []
            # Parse ship entries
            ship_matches = re.findall(r'ship\s+"([^"]+)"\s+(?:inherits\s+"([^"]+)")?\s*\{([^}]+)\}', ships_body)
            for match in ship_matches:
                ship_name = match[0]
                inherits = match[1] if len(match) > 1 and match[1] else "ASpaceShip"
                ship_sys_body = match[2]
                
                ship_def = {"name": ship_name, "inherits": inherits}
                
                fuel_match = re.search(r'fuel_capacity_liters\s*=\s*(\d+)', ship_sys_body)
                if fuel_match:
                    ship_def["fuel_capacity_liters"] = int(fuel_match.group(1))
                    
                cargo_match = re.search(r'cargo_capacity_kg\s*=\s*(\d+)', ship_sys_body)
                if cargo_match:
                    ship_def["cargo_capacity_kg"] = int(cargo_match.group(1))
                
                # Parse shield and hull values
                shield_cap_match = re.search(r'shield_capacity\s*=\s*([\d.]+)', ship_sys_body)
                if shield_cap_match:
                    ship_def["shield_capacity"] = float(shield_cap_match.group(1))
                    
                shield_regen_match = re.search(r'shield_regen_rate\s*=\s*([\d.]+)', ship_sys_body)
                if shield_regen_match:
                    ship_def["shield_regen_rate"] = float(shield_regen_match.group(1))
                    
                hull_health_match = re.search(r'hull_health\s*=\s*([\d.]+)', ship_sys_body)
                if hull_health_match:
                    ship_def["hull_health"] = float(hull_health_match.group(1))
                
                # Parse hardpoints
                hardpoints_list = []
                hardpoint_matches = re.findall(r'hardpoints\s*\{([^}]+)\}', ship_sys_body)
                if hardpoint_matches:
                    hp_body = hardpoint_matches[0]
                    # Parse weapon_slot entries
                    weapon_slot_matches = re.findall(r'weapon_slot\s*\{\s*(.*?)\s*\}', hp_body, re.DOTALL)
                    for ws_match in weapon_slot_matches:
                        ws_def = {}
                        
                        name_match = re.search(r'name\s*=\s*"([^"]+)"', ws_match)
                        if name_match:
                            ws_def["name"] = name_match.group(1)
                            
                        size_match = re.search(r'size\s*=\s*"([^"]+)"', ws_match)
                        if size_match:
                            ws_def["size"] = size_match.group(1)
                            
                        count_match = re.search(r'count\s*=\s*(\d+)', ws_match)
                        if count_match:
                            ws_def["count"] = int(count_match.group(1))
                            
                        type_match = re.search(r'type\s*=\s*"([^"]+)"', ws_match)
                        if type_match:
                            ws_def["type"] = type_match.group(1)
                            
                        hardpoints_list.append(ws_def)
                    
                    ship_def["hardpoints"] = {"weapon_slots": hardpoints_list}

                # Parse systems
                systems_list = []
                system_matches = re.findall(r'system\s+"([^"]+)"\s*\{([^}]+)\}', ship_sys_body)
                for sys_match in system_matches:
                    sys_name = sys_match[0]
                    sys_body = sys_match[1]
                    
                    sys_def = {"name": sys_name}
                    
                    if "consumption_rate_per_km" in sys_body:
                        rate_match = re.search(r'consumption_rate_per_km\s*=\s*([\d.]+)', sys_body)
                        if rate_match:
                            sys_def["consumption_rate_per_km"] = float(rate_match.group(1))
                            
                    if "travel_time_seconds" in sys_body:
                        time_match = re.search(r'travel_time_seconds\s*=\s*(\d+)', sys_body)
                        if time_match:
                            sys_def["travel_time_seconds"] = int(time_match.group(1))
                            
                    if "fuel_cost_per_jump_liters" in sys_body:
                        cost_match = re.search(r'fuel_cost_per_jump_liters\s*=\s*(\d+)', sys_body)
                        if cost_match:
                            sys_def["fuel_cost_per_jump_liters"] = int(cost_match.group(1))
                            
                    systems_list.append(sys_def)
                    
                if systems_list:
                    ship_def["system"] = systems_list
                    
                ships_list.append(ship_def)
                
            if ships_list:
                result["ship_systems"] = {"ships": ships_list}

        # Parse economy_systems block
        econ_body = extract_block_content(dsl_content, 'economy_systems')
        if econ_body:
            econ_systems = {}
            
            # Parse commodities
            commodities_list = []
            # One level of brace nesting so market_price sub-blocks survive the capture
            commod_matches = re.findall(r'commodity\s+"([^"]+)"\s*\{((?:[^{}]|\{[^{}]*\})*)\}', econ_body)
            for match in commod_matches:
                comm_name = match[0]
                comm_body = match[1]
                
                comm_def = {"name": comm_name}
                
                base_type_match = re.search(r'base_type\s*=\s*"([^"]+)"', comm_body)
                if base_type_match:
                    comm_def["base_type"] = base_type_match.group(1)
                    
                unit_match = re.search(r'unit\s*=\s*"([^"]+)"', comm_body)
                if unit_match:
                    comm_def["unit"] = unit_match.group(1)
                    
                # Parse market prices
                market_prices_list = []
                mp_matches = re.findall(r'market_price\s+"([^"]+)"\s*\{([^}]+)\}', comm_body)
                for mp_match in mp_matches:
                    mp_market = mp_match[0]
                    mp_body = mp_match[1]
                    
                    mp_def = {"market": mp_market}
                    
                    buy_price_kg = re.search(r'buy_price_per_kg\s*=\s*(\d+)', mp_body)
                    if buy_price_kg:
                        mp_def["buy_price_per_kg"] = int(buy_price_kg.group(1))
                        
                    sell_price_kg = re.search(r'sell_price_per_kg\s*=\s*(\d+)', mp_body)
                    if sell_price_kg:
                        mp_def["sell_price_per_kg"] = int(sell_price_kg.group(1))
                        
                    buy_price_unit = re.search(r'buy_price_per_unit\s*=\s*(\d+)', mp_body)
                    if buy_price_unit:
                        mp_def["buy_price_per_unit"] = int(buy_price_unit.group(1))
                        
                    sell_price_unit = re.search(r'sell_price_per_unit\s*=\s*(\d+)', mp_body)
                    if sell_price_unit:
                        mp_def["sell_price_per_unit"] = int(sell_price_unit.group(1))
                        
                    buy_price_ration = re.search(r'buy_price_per_ration\s*=\s*(\d+)', mp_body)
                    if buy_price_ration:
                        mp_def["buy_price_per_ration"] = int(buy_price_ration.group(1))
                        
                    sell_price_ration = re.search(r'sell_price_per_ration\s*=\s*(\d+)', mp_body)
                    if sell_price_ration:
                        mp_def["sell_price_per_ration"] = int(sell_price_ration.group(1))
                        
                    market_prices_list.append(mp_def)
                    
                if market_prices_list:
                    comm_def["market_price"] = market_prices_list
                    
                commodities_list.append(comm_def)
                
            if commodities_list:
                econ_systems["commodities"] = commodities_list
                
            # Parse trade routes
            trade_routes_list = []
            tr_matches = re.findall(r'trade_route\s+"([^"]+)"\s*\{([^}]+)\}', econ_body)
            for match in tr_matches:
                tr_name = match[0]
                tr_body = match[1]
                
                tr_def = {"name": tr_name}
                
                origin_match = re.search(r'origin\s*=\s*"([^"]+)"', tr_body)
                if origin_match:
                    tr_def["origin"] = origin_match.group(1)
                    
                dest_match = re.search(r'destination\s*=\s*"([^"]+)"', tr_body)
                if dest_match:
                    tr_def["destination"] = dest_match.group(1)
                    
                comms_allowed_match = re.search(r'commodities_allowed\s*=\s*\[(.*?)\]', tr_body)
                if comms_allowed_match:
                    comms_str = comms_allowed_match.group(1)
                    comms = [c.strip().strip('"\'') for c in comms_str.split(',')]
                    tr_def["commodities_allowed"] = comms
                    
                trade_routes_list.append(tr_def)
                
            if trade_routes_list:
                econ_systems["trade_routes"] = trade_routes_list
                
            if econ_systems:
                result["economy_systems"] = econ_systems

        # Parse missions_contracts block (was previously dropped entirely)
        missions_body = extract_block_content(dsl_content, 'missions_contracts')
        if missions_body:
            missions_list = []
            m_matches = re.findall(r'mission\s+"([^"]+)"\s*\{((?:[^{}]|\{[^{}]*\})*)\}', missions_body)
            for m_name, m_body in m_matches:
                m_def = {"name": m_name}
                for key in ("type", "faction", "origin_station", "destination_station",
                            "required_commodity", "danger_level"):
                    km = re.search(key + r'\s*=\s*"([^"]+)"', m_body)
                    if km:
                        m_def[key] = km.group(1)
                for key in ("quantity_kg", "quantity_units", "quantity_rations",
                            "reward_credits", "penalty_failed"):
                    km = re.search(key + r'\s*=\s*(\d+)', m_body)
                    if km:
                        m_def[key] = int(km.group(1))
                ef = re.search(r'enemy_factions\s*=\s*\[(.*?)\]', m_body)
                if ef:
                    m_def["enemy_factions"] = [c.strip().strip('"\'') for c in ef.group(1).split(',')]
                missions_list.append(m_def)
            if missions_list:
                result["missions_contracts"] = {"missions": missions_list}

        # Parse procedural_generation block
        pcg_body = extract_block_content(dsl_content, 'procedural_generation')
        if pcg_body:
            pcg_systems = {}
            
            # Parse PCG graphs using brace counting for nested structures
            pcg_graphs_list = []
            
            # Find all pcg_graph declarations with their full content including nested braces
            pcg_start_pattern = r'pcg_graph\s+"([^"]+)"\s*\{'
            pcg_matches = list(re.finditer(pcg_start_pattern, pcg_body))
            
            for i, match in enumerate(pcg_matches):
                graph_name = match.group(1)
                start_pos = match.end()
                
                # Find the matching closing brace using brace counting
                brace_count = 1
                pos = start_pos
                while pos < len(pcg_body):
                    if pcg_body[pos] == '{':
                        brace_count += 1
                    elif pcg_body[pos] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            break
                    pos += 1
                
                graph_body = pcg_body[start_pos:pos].strip()
                
                graph_def = {"name": graph_name}
                
                # Parse graph_type
                graph_type_match = re.search(r'graph_type\s*=\s*"([^"]+)"', graph_body)
                if graph_type_match:
                    graph_def["graph_type"] = graph_type_match.group(1)
                    
                # Parse data_collections - find collection blocks
                collections_list = []
                
                # Find all collection declarations within this graph body
                col_start_pattern = r'collection\s+"([^"]+)"\s*\{'
                col_matches = list(re.finditer(col_start_pattern, graph_body))
                for col_match in col_matches:
                    col_name = col_match.group(1)
                    col_start_pos = col_match.end()
                    
                    # Find matching closing brace for collection
                    col_brace_count = 1
                    col_pos = col_start_pos
                    while col_pos < len(graph_body):
                        if graph_body[col_pos] == '{':
                            col_brace_count += 1
                        elif graph_body[col_pos] == '}':
                            col_brace_count -= 1
                            if col_brace_count == 0:
                                break
                        col_pos += 1
                        
                    col_body = graph_body[col_start_pos:col_pos].strip()
                    
                    col_def = {"collection_name": col_name}
                    
                    cancel_empty_match = re.search(r'cancel_execution_on_empty\s*=\s*(true|false)', col_body)
                    if cancel_empty_match:
                        col_def["cancel_execution_on_empty"] = cancel_empty_match.group(1) == "true"
                        
                    cancel_exec_match = re.search(r'cancel_execution\s*=\s*(true|false)', col_body)
                    if cancel_exec_match:
                        col_def["cancel_execution"] = cancel_exec_match.group(1) == "true"
                        
                    collections_list.append(col_def)
                    
                if collections_list:
                    graph_def["data_collections"] = collections_list
                    
                # Parse tagged_data_items - find item blocks
                tagged_data_list = []
                
                item_start_pattern = r'item\s+"([^"]+)"\s*\{'
                item_matches = list(re.finditer(item_start_pattern, graph_body))
                for item_match in item_matches:
                    item_name = item_match.group(1)
                    item_start_pos = item_match.end()
                    
                    # Find matching closing brace for item
                    item_brace_count = 1
                    item_pos = item_start_pos
                    while item_pos < len(graph_body):
                        if graph_body[item_pos] == '{':
                            item_brace_count += 1
                        elif graph_body[item_pos] == '}':
                            item_brace_count -= 1
                            if item_brace_count == 0:
                                break
                        item_pos += 1
                        
                    item_body = graph_body[item_start_pos:item_pos].strip()
                    
                    item_def = {}
                    
                    # Parse tags
                    tags_match = re.search(r'tags\s*=\s*\[(.*?)\]', item_body)
                    if tags_match:
                        tags_str = tags_match.group(1)
                        tags = [t.strip().strip('"\'') for t in tags_str.split(',')]
                        item_def["tags"] = tags
                        
                    # Parse pin
                    pin_match = re.search(r'pin\s*=\s*"([^"]+)"', item_body)
                    if pin_match:
                        item_def["pin"] = pin_match.group(1)
                        
                    # Parse b_pinless_data
                    pinless_match = re.search(r'b_pinless_data\s*=\s*(true|false)', item_body)
                    if pinless_match:
                        item_def["b_pinless_data"] = pinless_match.group(1) == "true"
                        
                    # Parse b_is_used_multiple_times
                    multiple_match = re.search(r'b_is_used_multiple_times\s*=\s*(true|false)', item_body)
                    if multiple_match:
                        item_def["b_is_used_multiple_times"] = multiple_match.group(1) == "true"
                        
                    tagged_data_list.append(item_def)
                    
                if tagged_data_list:
                    graph_def["tagged_data_items"] = tagged_data_list
                    
                # Parse metadata_domains
                domains_match = re.search(r'metadata_domains\s*=\s*\[(.*?)\]', graph_body)
                if domains_match:
                    domains_str = domains_match.group(1)
                    domains = [d.strip().strip('"\'') for d in domains_str.split(',')]
                    graph_def["metadata_domains"] = domains
                    
                # Parse attribute_selectors
                selectors_match = re.search(r'attribute_selectors\s*=\s*\[(.*?)\]', graph_body)
                if selectors_match:
                    selectors_str = selectors_match.group(1)
                    selectors = [s.strip().strip('"\'') for s in selectors_str.split(',')]
                    graph_def["attribute_selectors"] = selectors
                    
                pcg_graphs_list.append(graph_def)
                
            if pcg_graphs_list:
                pcg_systems["pcg_graphs"] = pcg_graphs_list
                
            if pcg_systems:
                result["procedural_generation"] = pcg_systems

        return result

    def _parse_params(self, params_str: str) -> Dict[str, Any]:
        """Parse parameter list from DSL into dictionary."""
        params = {}
        # Match key=value patterns
        param_matches = re.findall(r'(\w+)\s*=\s*"([^"]+)"|(\w+)\s*=\s*(\d+)|(\w+)\s*=\s*([\w.]+)', params_str)
        for match in param_matches:
            if match[0] and match[1]:
                params[match[0]] = match[1]
            elif match[2] and match[3]:
                params[match[2]] = int(match[3])
            elif match[4] and match[5]:
                params[match[4]] = match[5]
        return params

    def parse_and_validate(self, dsl_content: str) -> Tuple[bool, Dict[str, Any], str | None]:
        """Parse DSL content and validate against schema."""
        # Parse DSL string to dictionary
        parsed_dsl = self.parse_dsl_string(dsl_content)
        
        # Log parse results through Graphify mutation interface
        mutate("parse", "success", details=parsed_dsl if isinstance(parsed_dsl, dict) else {})
        
        # Convert to JSON string for validation
        dsl_json_string = json.dumps(parsed_dsl, indent=2)
        
        # Validate against schema
        is_valid, validation_error = self.validator.validate(dsl_json_string)
        
        if not is_valid:
            return False, {}, validation_error
            
        return True, parsed_dsl, None
