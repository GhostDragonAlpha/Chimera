# DSL-MCP Bridge — Troubleshooting & Workflow Guide

## The Three-System Triangle

The Chimera project connects three systems into one unified workflow:

```
DSL Parser → Knows what the game IS
MCP Unreal Server → Knows how to BUILD
Graphify → Knows what HAPPENED
```

### How It Works

1. **DSL Parser** (`core/dsl_game_parser.py`) reads `.chimera` files and validates them against `schema/dsl_game_schema.json`
2. **DSL-MCP Bridge** (`core/dsl_mcp_bridge.py`) translates parsed DSL blocks into MCP operations
3. **MCP Unreal Server** (`chiR24-unreal-mcp`) executes those operations via tools like `control_actor`, `inspect`, etc.
4. **Graphify** records every operation as a mutation node in the knowledge graph

### Running the Bridge

```bash
cd E:\PythonChimera\Chimera
python core\dsl_mcp_bridge.py tests/dsl_grammar/deep_space_trader.chimera
```

This will:
1. Parse the DSL file
2. Generate MCP operations (spawn actors, set properties, etc.)
3. Log mutations to Graphify

## Known Issues & Fixes

### Issue 1: Schema Path Not Found
**Error:** `FileNotFoundError: schema\dsl_game_schema.json`

**Fix:** The bridge resolves paths relative to the Chimera root using `Path(__file__).parent.parent`. Ensure you run from any directory — the path resolution is absolute.

### Issue 2: Unicode Encoding Error
**Error:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'`

**Fix:** Arrow characters (→) in print statements are not supported on Windows cp1252 encoding. Use `[>]` instead of `→`.

### Issue 3: Python Can't Call MCP Tools Directly
**Error:** All operations fail because Python subprocesses can't connect to MCP stdio servers.

**Fix:** MCP tools must be invoked via Cline's `use_mcp_tool` mechanism, not from within Python code. The bridge generates the operation list; execution happens through Cline calling each tool.

## Manual Execution Workflow

Since Python can't call MCP tools directly, use this manual workflow:

### Step 1: Stop PIE
```python
# Via use_mcp_tool:
server_name: chiR24-unreal-mcp
tool_name: control_editor
arguments: {"action": "stop"}
```

### Step 2: List Available Tools
```python
server_name: chiR24-unreal-mcp
tool_name: manage_tools
arguments: {"action": "list_tools"}
# Returns 22 tools (all enabled)
```

### Step 3: List Current Actors
```python
server_name: chiR24-unreal-mcp
tool_name: inspect
arguments: {"action": "list_objects", "className": "Actor"}
# Returns current actors in the level
```

### Step 4: Spawn an Actor

**Engine classes use `/Script/` prefix:**
```python
server_name: chiR24-unreal-mcp
tool_name: control_actor
arguments: {
    "action": "spawn",
    "actorName": "MyShip",
    "classPath": "/Script/Engine.StaticMeshActor"
}
```

**Custom C++ classes need to be compiled first.** The ship class `AShip_Trader_Vessel_Alpha` exists in Source but hasn't been compiled yet. Once built, the path would be:
```python
"classPath": "/Game/DeepSpaceTrader/Ships/BP_Trader_Vessel_Alpha"  # Blueprint version
# or for compiled C++ classes:
"classPath": "/Script/Chimera.AShip_Trader_Vessel_Alpha"
```

**Verified working spawns:**
- `StaticMeshActor` → `/Script/Engine.StaticMeshActor` ✅
- `DirectionalLight` → `/Script/Engine.DirectionalLight` ✅

### Step 5: Verify Spawn
```python
server_name: chiR24-unreal-mcp
tool_name: inspect
arguments: {"action": "list_objects", "className": "Actor"}
# Should now include your spawned actor
```

## Current Level State (as of last check)

- **World:** chimeradefaultlevel
- **Is PIE World:** false
- **Actors:** 8 (DirectionalLight_0, SkyAtmosphere_0, SkyLight_0, ExponentialHeightFog_0, VolumetricCloud_0, PlayerStart_0, StaticMeshActor_0, Floor_0)

## DSL-MCP Bridge Output Example

```
============================================================
DSL-MCP Bridge — Starting Pipeline
============================================================

[Step 1] Clearing current level...
  [WARN] Level clear failed: clear_level requires MCP stdio transport

[Step 2] Translating DSL blocks to MCP operations...
      Generated 13 operations:
        [>] spawn_actor on AShip_Trader_Vessel_Alpha (Trader_Vessel_Alpha_Spawned)
        [>] set_property on Trader_Vessel_Alpha_Spawned ()
        ...

[Step 3] Executing MCP operations...

============================================================
DSL-MCP Bridge — Complete
  Successes: 0
  Failures:  13
============================================================
```

The "Failures" are expected because Python can't call MCP tools directly. The important part is that the DSL was parsed and 13 operations were generated correctly.

## Graphify Mutation Logging

Every bridge operation is logged to `docs/chimera_knowledge_graph.json` as a mutation node:
- **Type:** Mutation
- **error_signature:** bridge_{operation} or bridge_success
- **template_file:** dsl_mcp_bridge:{operation}
- **compilation_result:** success/failed

This allows tracking which DSL blocks were processed and what operations they generated.