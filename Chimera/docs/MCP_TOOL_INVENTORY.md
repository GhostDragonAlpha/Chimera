# MCP Tool Inventory

## Overview

Chimera uses 36 MCP tools to interact with Unreal Engine 5.8. Each tool has multiple actions (methods). This document lists all tools, their actions, parameters, and links to proven pathways in `MCP_PATHWAYS.md`.

**Query Rule**: Before using any tool, query Graphify first: `g.query("pathway", "what_you_want_to_do")` — see `THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` for the full rule.

---

## Core Tools (8 tools)

### 1. unreal_engine_control_actor
**Purpose**: Spawn actors, set transforms, enable physics, add components, manage tags, attach/detach actors.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `spawn_actor` | actorName (string), classPath (string) | **WORKING** | `spawn_actor(actorName="TestActor", classPath="/Game/Test/Mesh")` |
| `set_transform` | actorName, location {x,y,z}, rotation {pitch,yaw,roll}, scale {x,y,z} | **WORKING** | `set_transform(actorName="Test", location={x:0,y:0,z:0})` |
| `get_components` | actorName (string) | **WORKING** | `get_components(actorName="Player")` |
| `set_component_property` | actorName, componentName, properties {key:value} | **WORKING** | `set_component_property(actorName="Ground", componentName="StaticMeshComponent0", properties={material: "/Game/Mats/MAT_Sand"})` |
| `spawn` | classPath (string) | Not tested | — |
| `delete` / `destroy_actor` | actorName | Not tested | — |
| `find_by_name` | name (string) | Not tested | — |
| `set_visibility` | actorName, visible (bool) | Not tested | — |

### 2. unreal_engine_control_editor
**Purpose**: Start/stop PIE, control viewport camera, run console commands, take screenshots, simulate input.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `screenshot` | filename (string) | **WORKING** | `screenshot(filename="test.png")` |
| `set_camera_position` | location {x,y,z}, rotation {pitch,yaw,roll} | **WORKING** | `set_camera_position(location={x:0,y:-250,z:130}, rotation={pitch:0,yaw:0,roll:0})` |
| `set_camera_fov` | fov (number) | Not tested | `set_camera_fov(fov=90)` |
| `console_command` / `execute_command` | command (string) | Failed — commands not recognized | — |
| `play` / `stop` / `pause` | — | Not tested | — |

### 3. unreal_engine_inspect
**Purpose**: Inspect any UObject: read/write properties, list components, export snapshots, query class info.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `get_project_settings` | (none) | **WORKING** | `get_project_settings()` |
| `get_material_details` | objectPath (string) | **WORKING** | `get_material_details(objectPath="/Game/Mats/MAT_Sand")` |
| `set_property` / `get_property` | objectPath, propertyName, value | Not tested | — |

### 4. unreal_engine_manage_pipeline
**Purpose**: Build automation and pipeline control (compile targets, show categories, get bridge status).

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `list_categories` | (none) | Not tested | — |
| `get_status` | (none) | Not tested | — |
| `run_ubt` | target, platform, configuration, arguments | Not tested | — |

### 5. unreal_engine_manage_tools
**Purpose**: Dynamic MCP tool management — enable/disable tools and categories at runtime.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `list_tools` | (none) | **WORKING** (via bash) | Returns all 36 tools with status |

### 6. unreal_engine_system_control
**Purpose**: Run profiling, set quality/CVars, execute console commands, manage widgets.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `execute_command` / `console_command` | command (string) | Failed — commands not recognized | — |
| `profile` | profileType | Not tested | — |

### 7. unreal_engine_manage_asset (create_material variant)
**Purpose**: Create materials, import assets, duplicate/rename/delete assets, edit material graphs.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_material` | name (string), path (string) — NOT materialPath | **WORKING** | `create_material(name="MAT_Sand", path="/Game/Chimera/Materials/MAT_Sand")` |
| `search_assets` | directory, classNames [], limit | **WORKING** | `search_assets(directory="/Game/", classNames=["StaticMesh"], limit=1)` |
| `list_instances` | materialPath | **FAILED** — "Action not previously tested" | — |

### 8. unreal_engine_manage_level
**Purpose**: Load/save levels, configure streaming, manage World Partition cells, build lighting.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `list_levels` | (none) | **WORKING** | `list_levels()` |
| `create_light` | lightType (string), intensity (number), location {x,y,z} | **WORKING** | `create_light(lightType="Directional", intensity=100.0, location={x:0,y:0,z:0})` |

---

## World Authoring Tools (4 tools)

### 9. unreal_engine_build_environment
**Purpose**: Create/sculpt landscapes, paint foliage, generate procedural terrain/biomes.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `sculpt` | — | Not tested | — |
| `paint_foliage` | — | Not tested | — |

### 10. unreal_engine_manage_geometry
**Purpose**: Create procedural meshes using Geometry Script: booleans, deformers, UVs, collision, LOD generation.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `boolean` / `deformer` / `uv_gen` | — | Not tested | — |

### 11. unreal_engine_manage_splines
**Purpose**: Create spline actors, add/modify points, attach meshes along splines.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create` / `add_point` | — | Not tested | — |

### 12. unreal_engine_manage_level_structure
**Purpose**: Create levels and sublevels, configure World Partition, streaming, data layers.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_sublevel` / `streaming` | — | Not tested | — |

---

## Authoring Tools (3 tools)

### 13. unreal_engine_manage_material_authoring
**Purpose**: Create materials with expressions, parameters, functions, instances, landscape blend layers.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `add_expression` / `set_parameter` | — | Not tested | — |

### 14. unreal_engine_manage_texture
**Purpose**: Create procedural textures, process images, bake normal/AO maps.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_normal_map` / `bake_ao` | — | Not tested | — |

### 15. unreal_engine_manage_blueprint
**Purpose**: Create Blueprints, add SCS components (mesh, collision, camera), manipulate graph nodes.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create` / `add_component` | — | Not tested | — |

---

## Gameplay Tools (7 tools)

### 16. unreal_engine_manage_character
**Purpose**: Create Character Blueprints with movement, locomotion, animation state machines.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create` / `add_locomotion` | — | Not tested | — |

### 17. unreal_engine_animation_physics
**Purpose**: Create animation blueprints, blend spaces, montages, state machines, Control Rig, IK rigs, ragdolls.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_blend_space` / `add_ik_rig` | — | Not tested | — |

### 18. unreal_engine_manage_combat
**Purpose**: Create weapons with hitscan/projectile firing, configure damage types, hitboxes, reload, melee combat.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_weapon` / `add_damage_type` | — | Not tested | — |

### 19. unreal_engine_manage_gas
**Purpose**: Create Gameplay Abilities, Effects, Attribute Sets, and Gameplay Cues for ability systems.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_ability` / `add_attribute_set` | — | Not tested | — |

### 20. unreal_engine_manage_ai
**Purpose**: Create AI Controllers, configure Behavior Trees, Blackboards, EQS queries, perception systems.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_controller` / `add_behavior_tree` | — | Not tested | — |

### 21. unreal_engine_manage_inventory
**Purpose**: Create item data assets, inventory components, world pickups, loot tables, crafting recipes.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_item` / `add_loot_table` | — | Not tested | — |

### 22. unreal_engine_manage_interaction
**Purpose**: Create interactive objects: doors, switches, chests, levers, destructible meshes, trigger volumes.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_door` / `add_switch` | — | Not tested | — |

---

## Utility Tools (6 tools)

### 23. unreal_engine_manage_widget_authoring
**Purpose**: Create UMG widgets: buttons, text, images, sliders. Configure layouts, bindings, animations.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_button` / `add_slider` | — | Not tested | — |

### 24. unreal_engine_manage_networking
**Purpose**: Configure multiplayer: property replication, RPCs (Server/Client/Multicast), authority, relevancy.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `set_replication` / `add_rpc` | — | Not tested | — |

### 25. unreal_engine_manage_game_framework
**Purpose**: Create GameMode, GameState, PlayerController, PlayerState Blueprints. Configure match flow, teams.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_gamemode` / `add_player_state` | — | Not tested | — |

### 26. unreal_engine_manage_sessions
**Purpose**: Configure local multiplayer: split-screen layouts, LAN hosting/joining, voice chat channels.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `configure_split_screen` / `add_voice_channel` | — | Not tested | — |

### 27. unreal_engine_manage_audio
**Purpose**: Play/stop sounds, add audio components, configure mixes, attenuation, spatial audio.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `play_sound` / `add_attenuation` | — | Not tested | — |

### 28. unreal_engine_manage_behavior_tree
**Purpose**: Create Behavior Trees, add task/decorator/service nodes, configure node properties.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_bt` / `add_task_node` | — | Not tested | — |

---

## Effect & Performance Tools (2 tools)

### 29. unreal_engine_manage_effect
**Purpose**: Niagara particle systems, VFX, debug shapes, GPU simulations. Create systems, emitters, modules.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_niagara_system` / `add_emitter` | — | Not tested | — |

### 30. unreal_engine_manage_performance
**Purpose**: Run profiling/benchmarks, configure scalability, LOD, Nanite, optimization settings.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `run_profiling` / `configure_lod` | — | Not tested | — |

---

## Navigation & Volumes Tools (2 tools)

### 31. unreal_engine_manage_navigation
**Purpose**: Configure NavMesh settings, add nav modifiers, create nav links and smart links for pathfinding.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `configure_navmesh` / `add_smart_link` | — | Not tested | — |

### 32. unreal_engine_manage_volumes
**Purpose**: Create trigger volumes, blocking volumes, physics volumes, audio volumes, navigation bounds.

| Action | Parameters | Pathway Status | Example |
|--------|-----------|----------------|---------|
| `create_trigger_volume` / `add_blocking_volume` | — | Not tested | — |

---

## Summary

| Category | Tools | Tested/Working | Notes |
|----------|-------|----------------|-------|
| Core | 8 | 5 working, 1 failed (list_instances), 2 untested | spawn_actor, set_transform, get_components, set_component_property, screenshot, camera_position all verified |
| World Authoring | 4 | 0 tested | Landscape/geometry/spline tools not yet used |
| Authoring | 3 | 0 tested | Material authoring, texture creation, blueprint editing not yet used |
| Gameplay | 7 | 0 tested | Character, animation, combat, GAS, AI, inventory, interaction — all untested |
| Utility | 6 | 0 tested | Widgets, networking, game framework, sessions, audio, behavior trees — all untested |
| Effects/Performance | 2 | 0 tested | Niagara, profiling — not yet used |
| Navigation/Volumes | 2 | 0 tested | NavMesh, volumes — not yet used |

**Total**: 36 tools. 5 actions proven working via pathway discovery. The remaining 31 tools await testing in future phases.
