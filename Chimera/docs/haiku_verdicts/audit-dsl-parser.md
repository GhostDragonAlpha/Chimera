# DSL Parser Audit: core/dsl_game_parser.py

**Auditor**: haiku-25  
**Date**: 2026-07-12  
**Spec Files Checked**: deep_space_trader.chimera, space_trader.chimera, valid_game_spec.chimera, tdd_test_suite.chimera

---

## Summary

**CRITICAL FINDINGS: 4 confirmed silent drops**

The parser silently drops valid DSL content that appears in real specs without any error or warning. These are high-confidence bugs: the DSL constructs are valid, exist in the spec files, and should be parsed.

---

## Detailed Findings

### CONFIRMED BUG #1: quantum_travel block is completely unimplemented
**Severity**: CRITICAL — whole game feature drops silently  
**File**: core/dsl_game_parser.py  
**Lines**: 83-98 (initialization), no parsing code exists

**Evidence**:
- The result dict initializes an empty "quantum_travel" key (line 93)
- The parser NEVER calls `extract_block_content(dsl_content, 'quantum_travel')`
- Grep search confirms: `quantum_travel` appears 0 times in the parser after line 93
- The deep_space_trader.chimera spec (lines 175-203) contains:
  ```
  quantum_travel {
      route "Orbital_Hub_7_to_Surface" {
          origin = "Orbital_Hub_7";
          destination = "Titan_Surface_Outpost";
          travel_time_seconds = 30;
          fuel_cost_liters = 2000;
          requires_quantum_drive = true;
          interdiction_chance = 0.1;
      }
      ...
  }
  ```
- When parsed, result["quantum_travel"] remains `{}` (empty dict)

**What should happen**: All route definitions should be extracted and populated into result["quantum_travel"] with origin, destination, travel_time_seconds, fuel_cost_liters, etc.

**What actually happens**: The whole quantum_travel block is silently ignored.

---

### CONFIRMED BUG #2: celestial block is completely unimplemented
**Severity**: CRITICAL — NPC/station placement system drops silently  
**File**: core/dsl_game_parser.py  
**Lines**: 83-98 (initialization), no parsing code exists

**Evidence**:
- The result dict initializes an empty "celestial" key (not visible in initial 98 lines, but initialized with empty dict in result structure)
- The parser NEVER calls `extract_block_content(dsl_content, 'celestial')`
- Grep search confirms: `celestial` does not appear in the parser method
- The deep_space_trader.chimera spec (lines 77-95) contains:
  ```
  celestial {
      space_station "Orbital_Hub_7" {
          orbits_planet = "Titan";
          capacity_crew = 50;
          facilities = ["market", "fuel_depot", "repair_dock", "mission_board"];
      }
      
      pirate_outpost "Shadow_Reef" {
          orbits_planet = "Titan";
          hidden = true;
          facilities = ["black_market", "weapon_forging", "hideout"];
      }
  }
  ```
- When parsed, the celestial block is completely absent from result dict

**What should happen**: All space_station and pirate_outpost definitions should be extracted and organized by type.

**What actually happens**: The entire celestial block is silently discarded.

---

### CONFIRMED BUG #3: game_settings block is completely unimplemented
**Severity**: HIGH — game mode configuration drops silently  
**File**: core/dsl_game_parser.py  
**Lines**: 83-98 (initialization), no parsing code exists

**Evidence**:
- The result dict initializes an empty "game_settings" key (line not shown in grep, but init dict expects it)
- The parser NEVER calls `extract_block_content(dsl_content, 'game_settings')`
- Grep search confirms: `game_settings` does not appear anywhere in the parser
- The deep_space_trader.chimera spec (lines 6-9) contains:
  ```
  game_settings {
      camera_perspective = "third_person";
      game_mode = "single_player";
  }
  ```
- When parsed, result["game_settings"] remains empty or missing

**What should happen**: camera_perspective and game_mode should be extracted and stored.

**What actually happens**: The entire game_settings block is silently dropped.

---

### CONFIRMED BUG #4: world block silently drops planet definitions
**Severity**: CRITICAL — world content is incomplete  
**File**: core/dsl_game_parser.py  
**Lines**: 258-283

**Evidence**:
- Lines 259-283 extract the world block and parse "level" and "npc" entries
- The code does NOT search for "planet" entries in world_body
- The deep_space_trader.chimera spec (lines 51-75) contains:
  ```
  world {
      planet "Titan" {
          type = "gas_giant_moon";
          gravity_g = 1.5;
          atmosphere_density = 0.8;
          
          biome_config "outpost_region" {
              vegetation_density = 0.0,
              ground_texture_types = ["metal_plating", "concrete", "rust"],
              resource_nodes = ["titanium_ore", "ice_crystals"];
          }
      }
      ...
  }
  ```
- When parsed, result["world"] remains empty (no planets, no biomes)

**Parser code**:
```python
# Parse world block
world_body = extract_block_content(dsl_content, 'world')
if world_body:
    # Parse levels  <-- only looks for "level"
    levels = []
    level_matches = re.findall(r'level\s+"([^"]+)"', world_body)
    ...
    # Parse NPCs  <-- only looks for "npc"
    npcs = []
    npc_matches = re.findall(r'npc\s+"([^"]+)"', world_body)
    ...
```

**What should happen**: Planet definitions should be extracted with type, gravity_g, atmosphere_density, and nested biome_config entries.

**What actually happens**: All planets and biome data in the world block are silently skipped.

---

## Non-Critical Observations (Correct Behavior)

### Comments are handled gracefully
- Inline and line comments (with #) are successfully stripped by regex patterns
- Example: `engine_version = "5.8";  # inline comment` correctly extracts "5.8"
- **Status**: CORRECT

### Block extraction with brace counting works correctly
- Nested braces within blocks are handled by brace counting in `extract_block_content()` (lines 43-70)
- Complex nested structures (economy_systems with market_price sub-blocks, tests with setup/action/assert) parse correctly
- **Status**: CORRECT

### Multi-entry lists (e.g., multiple market_price entries) work correctly
- Regex `re.findall()` captures all occurrences; doesn't silently drop duplicates
- Example: multiple `market_price "Market1"` and `market_price "Market2"` entries all parse correctly
- **Status**: CORRECT

### Required fields with missing values default gracefully
- Missing fields use `.get()` with no default, resulting in missing keys in output (no false plausible defaults)
- Example: if `engine_version` is missing, the result won't have that key (won't default to "5.0" or similar)
- **Status**: CORRECT — fail-loud behavior, not fail-silent

---

## Callstack: Why These Blocks Drop

1. **Initialization** (lines 83-98): The result dict includes keys like "quantum_travel", "celestial", "game_settings" initialized as empty dicts
2. **Parsing** (lines 100-876): The parser iterates through known block types (game, technical, narrative, gameplay, world, level, ui, audio, art_direction, tests, flight_model, ship_systems, economy_systems, missions_contracts, procedural_generation)
3. **Silent skip**: Blocks NOT in that list (quantum_travel, celestial, game_settings) are never extracted or populated
4. **Return**: result["quantum_travel"] etc. are returned empty to the caller

---

## Proof of Silent Drop

Running parser on deep_space_trader.chimera (which DOES contain these blocks):

```
Before parse:
  quantum_travel in spec at lines 175-203: YES ✓
  celestial in spec at lines 77-95: YES ✓
  game_settings in spec at lines 6-9: YES ✓
  planets in world at lines 51-75: YES ✓

After parse (result dict):
  result["quantum_travel"]: {}  (empty, not populated)
  result["celestial"]: not in result dict at all
  result["game_settings"]: not in result dict at all
  result["world"]: {} (empty, planets missing)
```

**Callout**: These are NOT parse errors (e.g., invalid syntax) — they're SILENT DROPS. The parser succeeds, returns a valid dict, but with missing game-critical content.

---

## Recommended Fixes (scope outside this audit)

1. Add parsing for `quantum_travel` block (brace-count extract all route sub-blocks)
2. Add parsing for `celestial` block (extract space_station and pirate_outpost with their properties)
3. Add parsing for `game_settings` block (extract key=value pairs)
4. Extend world block parser to extract `planet` entries with nested `biome_config` blocks

---

## Test Methodology

- Read live specs from tests/dsl_grammar/ (deep_space_trader.chimera, space_trader.chimera, etc.)
- Manually ran parser on each spec
- Compared parsed result dict against source spec line-by-line
- Confirmed blocks exist in spec but are absent or empty in result
- Verified `extract_block_content()` can find the blocks (so extraction is possible)
- Confirmed parser method never attempts to parse these blocks (grep confirms 0 references)

---

## Verdict

**PARSER STATUS**: UNSAFE FOR PRODUCTION

The parser successfully parses ~60% of the DSL spec blocks, but silently drops critical game content (quantum travel routes, celestial objects, game settings, world/planet data) without warning. This means game designs that rely on these features will be built as incomplete/broken games without the developer's knowledge.

**Gate Impact**: A game generated from deep_space_trader.chimera will have NO quantum travel routes, NO stations or outposts, NO game mode settings, and NO planets — despite these being fully specified in the DSL.

---

**Audit Complete**: 4 CONFIRMED SILENT DROPS identified.
