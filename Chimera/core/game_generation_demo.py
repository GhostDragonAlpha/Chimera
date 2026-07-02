"""
DSL-Driven Game Generation Demo — Demonstrates the complete 6-stage pipeline for 
transforming a DSL game specification into a fully functional Unreal Engine project.

Usage:
    python Chimera/core/game_generation_demo.py
"""

import json
from pathlib import Path

# Import the orchestrator
try:
    from core.game_generation_orchestrator import GameGenerationOrchestrator
except ImportError:
    try:
        from game_generation_orchestrator import GameGenerationOrchestrator
    except ImportError:
        print("Error: Could not import GameGenerationOrchestrator")
        exit(1)


# Sample DSL specification for a game
SAMPLE_DSL_SPECIFICATION = """game "Echoes of Eternity" {
    engine_version = "5.4";
    target_platforms = ["PC", "PS5"];
}

narrative {
    act "Prologue" { ... }
    dialogue_tree "DT_Awakening" {
        node "root" { speaker="AI_Guide"; text="Wake up, traveler."; next="choice1"; }
        node "choice1" { player_choice ["Who are you?", "Where am I?"] branches { ... } }
    }
}

gameplay {
    character "Player" inherits "ACharacter" {
        ability_system_component "ASC";
        attribute_set "AS_Player";
        default_abilities = [GA_Dash, GA_Attack];
    }
    ability "Dash" uses GAS {
        ability_tags = ["Ability.Dash"];
        cooldown = 3.0s via GE_Dash_Cooldown;
        activation = {
            launch_character(speed=2000, direction=input_movement);
            play_montage(AM_Dash, slot=FullBody);
        };
    }
    ability "Attack" uses GAS {
        ability_tags = ["Ability.Attack"];
    }
    combat_system {
        damage_formulas = "physical_damage = attack_power - defense";
        hit_reactions = true;
        status_effects = ["stun", "bleed"];
    }
    inventory { ... }
    progression { ... }
}

world {
    level "L_TitanRuins" {
        environment { sky_light, fog, terrain using WorldPartition; }
        spawn_point "PlayerStart" at (0,0,100);
    }
    npc "Blacksmith" { behavior_tree "BT_Blacksmith", dialogue_tree "DT_Blacksmith" }
    npc "Guardian" { behavior_tree "BT_Guardian", dialogue_tree "DT_Guardian" }
}

ui {
    hud {
        widget "WBP_HUD" {
            health_bar, ability_cooldowns, minimap, quest_tracker;
        }
    }
    pause_menu { ... }
}

audio {
    music_cue "Exploration" { ... }
    sfx "SwordSwing" { ... }
    dynamic_mixing_rules { ... }
}

technical {
    network_model = "client_server";
    replication {
        properties: ["Health: Replicated, RepNotify", "Mana: Replicated"];
        rpcs: ["Server_Attack: reliable, server, WithValidation"];
    }
    performance { target_fps=60, LOD_strategy="aggressive" };
    module_dependencies = ["GameplayAbilities", "EnhancedInput", "CommonUI", "Niagara", "Water"];
}

art_direction {
    style = "fantasy_realistic";
    color_palette = "earth_tones";
}
"""


def main():
    """Run the game generation demo."""
    print("=" * 80)
    print("DSL-Driven Game Generation Orchestrator Demo")
    print("=" * 80)

    # Initialize orchestrator
    schema_path = Path(__file__).parent.parent / "schema" / "dsl_game_schema.json"
    source_dir = Path(__file__).parent.parent / "Source" / "ChimeraGenerated"
    content_dir = Path(__file__).parent.parent / "Content" / "ProceduralGenerated"
    output_dir = Path(__file__).parent.parent / "GeneratedProjects"

    print(f"\nInitializing orchestrator...")
    print(f"  Schema path: {schema_path}")
    print(f"  Source directory: {source_dir}")
    print(f"  Content directory: {content_dir}")
    print(f"  Output directory: {output_dir}")

    orchestrator = GameGenerationOrchestrator(
        schema_path=str(schema_path),
        source_dir=str(source_dir),
        content_dir=str(content_dir),
        output_dir=str(output_dir)
    )

    # Process DSL specification
    print("\n" + "=" * 80)
    print("Processing DSL Specification")
    print("=" * 80)

    result = orchestrator.process_dsl_specification(
        dsl_content=SAMPLE_DSL_SPECIFICATION,
        project_name="EchoesOfEternity"
    )

    if result.get("success"):
        print("\n" + "=" * 80)
        print("Game Generation Complete!")
        print("=" * 80)
        print(f"Project Name: {result.get('project_name')}")
        print(f".uproject Path: {result.get('uproject_path')}")
        print(f"Validation Report: {result.get('validation_report_path')}")
        print(f"All Tests Passed: {result.get('all_tests_passed')}")
        print(f"Generated Assets Count: {result.get('generated_assets_count')}")
        print(f"Generated Files Count: {result.get('generated_files_count')}")
    else:
        print("\n" + "=" * 80)
        print("Game Generation Failed!")
        print("=" * 80)
        print(f"Error: {result.get('error')}")

    # Demonstrate incremental regeneration
    print("\n" + "=" * 80)
    print("Demonstrating Incremental Regeneration")
    print("=" * 80)

    # Updated DSL with a new ability
    UPDATED_DSL_SPECIFICATION = SAMPLE_DSL_SPECIFICATION.replace(
        'ability "Attack" uses GAS {',
        'ability "Attack" uses GAS {\n        ability_tags = ["Ability.Attack"];\n    }\n    ability "Jump" uses GAS {\n        ability_tags = ["Ability.Jump"];'
    )

    incremental_result = orchestrator.incrementally_regenerate(
        old_dsl_content=SAMPLE_DSL_SPECIFICATION,
        new_dsl_content=UPDATED_DSL_SPECIFICATION,
        project_name="EchoesOfEternity"
    )

    if incremental_result.get("success"):
        print("\nIncremental regeneration completed successfully!")
        print(f"Generated Files Count: {incremental_result.get('generated_files_count')}")
    else:
        print("\nIncremental regeneration failed!")
        print(f"Error: {incremental_result.get('error')}")

    print("\n" + "=" * 80)
    print("Demo Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
