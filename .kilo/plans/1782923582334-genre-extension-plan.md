# Genre Extension Plan: Open-World Survival Crafting Game

## Context

The Chimera DSL-driven game generation orchestrator currently supports:
- **Fully implemented systems**: GAS abilities with cooldown effects, behavior trees for NPCs, CommonUI/UMG HUD widgets, multiplayer replication rules (client-server), mock/procedural asset generation (meshes, textures, animations, sounds)
- **Partially supported**: inventory and progression blocks exist in schema but have no C++ template generation; cutscenes, dynamic_mixing_rules, priority_system in audio block lack full implementation
- **Absent systems**: Crafting, building, survival stats, procedural world generation (PCG), day/night cycles, vehicle systems, stealth mechanics

### Hardcoded Assumptions to Address
1. Every character gets AbilitySystemComponent and AttributeSet
2. Player is always an ACharacter subclass
3. Networking is always client-server model
4. No camera perspective (third-person vs first-person) differentiation in schema
5. No game mode (single-player vs multiplayer) differentiation in schema

---

## Recommended Implementation Approach: Incremental System-by-System

### Implementation Order

**Step 1: Game Settings / Camera Perspective (Low Effort)**
- Add game_settings block to schema and grammar
- Generate appropriate GameModeBase with correct default pawn/HUD configuration

**Step 2: Survival Stats Attributes (Medium Effort)**
- Add survival_stats block to schema and grammar
- Generate UAttributeSet subclass with hunger/thirst/temperature properties
- Integrate with existing GAS ability system component generation

**Step 3: Crafting Systems - Recipes & Workstations (Medium Effort)**
- Add crafting_systems block to schema and grammar
- Generate UDataTable or UScriptStruct for crafting recipes
- Generate workstation actor components

**Step 4: Asset Generation Extensions (Low-Medium Effort)**
- Extend asset_generator.py with biome textures, crafting station meshes, survival UI elements

**Step 5: Procedural World Generation - PCG Integration (High Effort - Optional Phase)**
- Add world_generation block with biomes and PCG modules
- Integrate with UE's PCG framework (PCGGraph, PCGBuildings)

---

## Validation Steps

After each implementation step:
1. Schema validation: Run existing tests against updated dsl_game_schema.json
2. Grammar parsing: Verify ANTLR4 parser generates correct parse trees for new DSL constructs
3. Code generation test: Generate C++ files and verify UHT reflection macros are valid
4. UBT compilation: Run build_orchestrator.py pipeline and verify zero C++ or rules errors
5. Error mapping validation: Test build_validator.py to ensure new DSL blocks produce meaningful error messages
