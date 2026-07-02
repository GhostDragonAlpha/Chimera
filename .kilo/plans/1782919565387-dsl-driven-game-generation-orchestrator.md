# DSL-Driven One-Shot Game Generation Orchestrator

## Overview

This plan implements a comprehensive game development DSL orchestrator that takes a structured domain-specific language (DSL) specification and transforms it into a fully functional, AAA-quality Unreal Engine 5 project. The system follows a strict pipeline with no creative invention beyond the declared specification.

## Goals

1. **Implement DSL Parser & Validator** - Parse and validate game specifications written in a unified DSL format covering `game`, `narrative`, `gameplay`, `world`, `ui`, `audio`, and `technical` blocks
2. **Implement 6-Stage Generation Pipeline** - Execute: Parse & Validate → Asset Generation → Code Generation → Integration & Build → Report & Refine Prompt → Regenerate & Iterate
3. **Generate Unreal-Specific C++ Code** - Create correct C++ classes with UCLASS, UPROPERTY, UFUNCTION macros, configure Gameplay Ability System (GAS), Enhanced Input, Behavior Trees, Niagara, MetaSounds subsystems
4. **Implement Multiplayer Replication Rules** - Generate explicit property and RPC replication rules for dedicated server with client prediction or client-server models
5. **Produce Final Outputs** - Compile .uproject with all source code, generate packaged executable for primary platform, output debug report mapping every generated asset and class back to DSL specification

## DSL Format Schema

### Top-Level Blocks

```
game "GameTitle" {
    engine_version = "5.4";
    target_platforms = ["PC", "PS5", "XboxSeriesX"];
}

narrative {
    act "ActName" { ... } // branching story with dialogues, conditions, animations
    dialogue_tree "ID" { ... }
    cutscene "ID" { camera_shots, character animations, triggers }
}

gameplay {
    character "Player" inherits "ACharacter" { ... } // properties, components, abilities
    ability "Dash" uses GAS { // exact Unreal GAS mapping
        ability_tags = ["Ability.Dash"];
        cooldown = 3.0s via GE_Dash_Cooldown;
        activation = {
            launch_character(speed=2000, direction=input_movement);
            play_montage(AM_Dash, slot=FullBody);
        };
    }
    combat_system { ... } // damage formulas, hit reactions, status effects
    inventory { ... }
    progression { ... }
}

world {
    level "MainCity" {
        // environment assets, spawn points, scripted events, World Partition settings
    }
    npc "Blacksmith" { behavior_tree "BT_Blacksmith", dialogue_tree "DT_Blacksmith" }
}

ui {
    hud { health_bar, minimap, ability_bar using CommonUI }
    pause_menu { ... }
}

audio {
    music_cue "Exploration" { ... }
    sfx "SwordSwing" { ... }
    dynamic_mixing_rules { ... }
}

technical {
    network_model = "dedicated_server_with_client_prediction";
    replication { // explicit property and RPC replication rules
        health: Replicated, RepNotify;
        RPC_Server_Attack: reliable, server;
    }
    performance { target_fps=60, LOD_strategy="aggressive", ... }
    module_dependencies = ["GameplayAbilities", "EnhancedInput", "Niagara", ...];
}
```

## 6-Stage Pipeline Implementation

### Stage 1: Parse & Validate

**Component:** `dsl_game_parser.py` and `dsl_schema_validator.py`

- Check DSL for consistency, type errors, missing references
- Report any issues before generation begins
- Validate against comprehensive DSL schema covering all blocks and sub-blocks
- Flag explicitly missing details that prevent generation; never guess creative elements not explicitly declared

### Stage 2: Asset Generation

**Component:** `asset_generator.py`

- Create all declared assets at specified paths using AI tools
- Use `art_direction` block in DSL for style guidance
- Generate meshes, textures, animations, sounds
- Place assets at Content paths specified in the DSL (e.g., `Content/ProceduralGenerated/Assets/`)

### Stage 3: Code Generation

**Component:** `game_code_generator.py` (extends existing `cpp_generator.py`)

- Emit all C++ and Blueprint logic, data tables, configuration files
- Use exact class and property names from DSL
- Generate C++ classes with UCLASS, UPROPERTY, UFUNCTION macros
- Configure Gameplay Ability System with proper GAS mapping (UGameplayAbility, UGameplayEffect, UAttributeSet)
- Implement Enhanced Input bindings
- Generate Behavior Trees for NPCs
- Create Niagara particle systems and MetaSound audio assets as specified

### Stage 4: Integration & Build

**Component:** `build_orchestrator.py`

- Assemble the .uproject file with all source code and modules
- Compile using Unreal Build Tool (UBT)
- Run automated tests including AI playtests to verify quest completion, combat balance, UI flow
- Validate that generated assets and classes match DSL specifications

### Stage 5: Report & Refine Prompt

**Component:** `validation_reporter.py`

- Output detailed validation report mapping every generated asset and class back to the DSL specification
- Identify any deviations from spec, bugs, or performance warnings
- If spec change is needed, generate a proposed DSL patch for user review

### Stage 6: Regenerate & Iterate

**Component:** `incremental_generator.py`

- Accept updated DSL from user after review
- Incrementally regenerate only the affected parts
- Maintain existing stable assets without regeneration

## Integration with Existing Components

### Extended `cpp_generator.py`

The existing `cpp_generator.py` handles basic C++ component generation (ProceduralGeneratorComponent, VehicleSpawnerComponent, FlightControlComponent, LevelGeneratorComponent). The new orchestrator will extend this to:

- Generate character classes with UGameplayAbilitySystemComponent and UAttributeSet
- Generate GAS ability classes (UGameplayAbility subclasses) with cooldown effects via UGameplayEffect
- Generate NPC AI behavior tree configuration files (.behaviortree)
- Generate CommonUI widget Blueprints for HUD elements

### Extended `dsl_workflow_orchestrator.py`

The existing `dsl_workflow_orchestrator.py` handles term alignment and logic mapping (operations: semantic_match, log_alignment, conditional_branch). The new orchestrator will replace/extend this with:

- Full game DSL parsing and validation
- 6-stage pipeline execution orchestration
- Integration with LM Studio API for asset generation guidance and AI playtest analysis

## Data Flow

```
User provides DSL specification
    -> Stage 1: Parse & Validate (dsl_game_parser.py + dsl_schema_validator.py)
        -> Check consistency, type errors, missing references
            -> If invalid: report issues and halt
            -> If valid: proceed to Stage 2
    
    -> Stage 2: Asset Generation (asset_generator.py)
        -> Read art_direction block for style guidance
            -> Generate meshes, textures, animations, sounds at Content paths
        
    -> Stage 3: Code Generation (game_code_generator.py)
        -> Emit C++ classes with UCLASS, UPROPERTY, UFUNCTION macros
            -> Configure GAS, Enhanced Input, Behavior Trees, Niagara, MetaSounds
                -> Implement replication rules for network_model specified
        
    -> Stage 4: Integration & Build (build_orchestrator.py)
        -> Assemble .uproject file
            -> Compile using Unreal Build Tool
                -> Run automated tests and AI playtests
        
    -> Stage 5: Report & Refine (validation_reporter.py)
        -> Output validation report mapping assets/classes to DSL spec
            -> Generate proposed DSL patch if deviations found
        
    -> Stage 6: Regenerate & Iterate (incremental_generator.py)
        -> Accept updated DSL from user
            -> Incrementally regenerate only affected parts
```

## Failure Modes & Recovery

| Scenario | Behavior | Recovery |
|----------|----------|----------|
| DSL missing required blocks | Parser halts and reports missing blocks | User must provide complete DSL specification |
| DSL references undefined terms | Validator reports missing term definitions | User must add terms to registry or remove invalid references |
| Asset generation fails | AI tool returns error or incomplete assets | Report in validation report; halt build or use fallback placeholder assets |
| C++ compilation fails | UBT reports syntax or linking errors | Report in validation report with specific compiler errors; generate DSL patch for fixes |
| AI playtest fails quest completion | Playtest agent cannot complete designated quest | Report failure in validation report; suggest DSL patch for quest logic or spawn points |
| Spec change needed during generation | Ambiguity or conflict detected in DSL | Halt generation; output proposed DSL patch for user review before proceeding |

## Rollout / Migration Path

1. **Create DSL schema** - Generate comprehensive `dsl_game_schema.json` covering all game, narrative, gameplay, world, ui, audio, technical blocks
2. **Implement parser & validator** - Create `dsl_game_parser.py` and `dsl_schema_validator.py` for Stage 1 validation
3. **Extend code generator** - Modify or extend `cpp_generator.py` to handle GAS, Enhanced Input, Behavior Trees, Niagara, MetaSounds generation
4. **Implement asset generator** - Create `asset_generator.py` for AI-powered asset creation guided by art_direction block
5. **Build orchestrator integration** - Create `build_orchestrator.py` for .uproject assembly and UBT compilation
6. **Validation reporter & iterative generator** - Create `validation_reporter.py` and `incremental_generator.py` for Stage 5 and Stage 6

## Open Questions (Out of Scope)

- Specific AI tool integration details for asset generation - to be determined based on available AI image/3D model generation APIs
- Exact Unreal Build Tool command-line parameters for compilation - to be determined based on UE 5.4/5.5 UBT documentation
- AI playtest agent implementation details - to be developed as part of the TEST_ENGINEER validation loop integration

## Validation Steps

### Step 1 - DSL Schema Validation (Terminal)

```bash
python Chimera/core/dsl_game_validator.py --spec game_spec.dsl --schema schema/dsl_game_schema.json
```

Expected output: All validation checks pass, report shows "DSL specification is valid and complete"

### Step 2 - Code Generation Verification (UE Editor)

Open generated `.uproject` in Unreal Engine 5.4/5.5 editor and verify:
- Source code compiles without errors in Visual Studio / UE Build System
- C++ classes contain correct UCLASS, UPROPERTY, UFUNCTION macros
- Gameplay Ability System components are properly configured with ASC and Attribute Sets
- Enhanced Input bindings are present in project settings

### Step 3 - AI Playtest Validation (Terminal)

```bash
python Chimera/Python/playtest_validator.py --game-spec game_spec.dsl --test-scenarios quest_completion,combat_balance,ui_flow
```

Expected output: All playtest scenarios pass, report shows "AI playtests completed successfully with no critical failures"

### Step 4 - Final Output Verification (Terminal)

```bash
# Verify .uproject exists and is valid JSON/INI
cat GeneratedProject/YourGame.uproject | grep -E '"EngineAssociation"|"Modules"'

# Verify packaged executable exists for primary platform
ls -la GeneratedProject/Binaries/Win64/YourGame.exe
```

Expected output: `.uproject` file contains valid engine association and module definitions; packaged executable exists in Binaries/Win64 directory.