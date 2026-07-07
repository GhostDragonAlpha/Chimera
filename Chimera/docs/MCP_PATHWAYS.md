# MCP Pathways — Working Tool Sequences

## Overview

This document lists all proven MCP pathways for interacting with Unreal Engine 5.8 via the Chimera MCP bridge. Each pathway includes the exact tool, action, and parameter schema needed to execute it reliably.

**Query Rule**: Before using any tool, query Graphify first: `g.query("pathway", "what_you_want_to_do")` — see `THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` for the full rule.

---

## Working Pathways (12 original + 22-26 below)

### 1. control_actor.spawn_actor
- **Tool**: `unreal_engine_control_actor`
- **Action**: `spawn_actor`
- **Parameters**: `{actorName: string, classPath: string}`
- **Example**: `spawn_actor(actorName="TestActor", classPath="/Game/VehicleTemplate/Meshes/SM_Track_10M.SM_Track_10M")`
- **Result**: Returns actor object with id, name, path, guid. Actor exists after spawn.
- **Notes**: Use existing mesh paths from the project (e.g., `/Game/Vehicles/SportsCar/SM_SportsCar.SM_SportsCar`). Editor meshes like `/Engine/EditorMeshes/Cube` are not available in this project.

### 2. control_actor.set_transform
- **Tool**: `unreal_engine_control_actor`
- **Action**: `set_transform`
- **Parameters**: `{actorName: string, location?: {x: number, y: number, z: number}, rotation?: {pitch: number, yaw: number, roll: number}, scale?: {x: number, y: number, z: number}}`
- **Example**: `set_transform(actorName="Player", location={x:0,y:5,z:130}, scale={x:1.5,y:1.5,z:1.5})`
- **Result**: Actor transform updated successfully.

### 3. control_actor.get_components
- **Tool**: `unreal_engine_control_actor`
- **Action**: `get_components`
- **Parameters**: `{actorName: string}`
- **Example**: `get_components(actorName="PlayerTestPlaceholder")`
- **Result**: Returns array of component names (e.g., `["StaticMeshComponent0"]`). Required before calling `set_component_property`.

### 4. control_actor.set_component_property
- **Tool**: `unreal_engine_control_actor`
- **Action**: `set_component_property`
- **Parameters**: `{actorName: string, componentName: string, properties: {key: value}}`
- **Example**: `set_component_property(actorName="GroundPlane", componentName="StaticMeshComponent0", properties={material: "/Game/Chimera/Materials/MAT_GroundSand/MAT_GroundSand"})`
- **Result**: Component property updated. Use this to apply materials, set visibility, adjust collision.

### 5. manage_asset.search_assets
- **Tool**: `unreal_engine_manage_asset`
- **Action**: `search_assets`
- **Parameters**: `{directory: string, classNames?: string[], limit?: number}`
- **Example**: `search_assets(directory="/Game/", classNames=["StaticMesh"], limit=1)`
- **Result**: Returns array of asset paths matching the search criteria.

### 6. control_editor.screenshot
- **Tool**: `unreal_engine_control_editor`
- **Action**: `screenshot`
- **Parameters**: `{filename: string}`
- **Example**: `screenshot(filename="phase2_refinement_v1.png")`
- **Result**: Screenshot saved to `Saved/Screenshots/phase2_refinement_v1.png`. Returns width, height, sizeBytes.

### 7. control_editor.set_camera_position
- **Tool**: `unreal_engine_control_editor`
- **Action**: `set_camera_position`
- **Parameters**: `{location: {x: number, y: number, z: number}, rotation: {pitch: number, yaw: number, roll: number}}`
- **Example**: `set_camera_position(location={x:0,y:-250,z:130}, rotation={pitch:0,yaw:0,roll:0})`
- **Result**: Camera position and rotation updated.

### 8. inspect.get_project_settings
- **Tool**: `unreal_engine_inspect`
- **Action**: `get_project_settings`
- **Parameters**: `{}` (none)
- **Example**: `get_project_settings()`
- **Result**: Returns projectName, engineVersion, buildConfig, projectDir, projectVersion.

### 9. inspect.get_material_details
- **Tool**: `unreal_engine_inspect`
- **Action**: `get_material_details`
- **Parameters**: `{objectPath: string}`
- **Example**: `get_material_details(objectPath="/Game/TestRoom/Mat_ISS_Floor/Mat_ISS_Floor")`
- **Result**: Returns objectPath, className, classPath. Note: detailed material parameters (BaseColor, Roughness, Metallic) are not returned by this action — use asset creation and property setting instead.

### 10. manage_level.list_levels
- **Tool**: `unreal_engine_manage_level`
- **Action**: `list_levels`
- **Parameters**: `{}` (none)
- **Example**: `list_levels()`
- **Result**: Returns currentWorldLevels array, allMaps array, currentMap path.

### 11. manage_level.create_light
- **Tool**: `unreal_engine_manage_level`
- **Action**: `create_light`
- **Parameters**: `{lightType: string, intensity: number, location: {x: number, y: number, z: number}}`
- **Example**: `create_light(lightType="Directional", intensity=100.0, location={x:0,y:0,z:0})`
- **Result**: Returns actorName (e.g., "DirectionalLight1"), actorPath, actorGuid. Light is spawned and exists after creation.

### 12. manage_asset.create_material
- **Tool**: `unreal_engine_manage_asset`
- **Action**: `create_material`
- **Parameters**: `{name: string, path: string}` — Note: use `path`, NOT `materialPath`
- **Example**: `create_material(name="MAT_GroundSand", path="/Game/Chimera/Materials/MAT_GroundSand")`
- **Result**: Returns assetPath (e.g., `/Game/Chimera/Materials/MAT_GroundSand/MAT_GroundSand.MAT_GroundSand`). Material is created but saved=false — call save action separately if needed.

### 13. professor_review
- **Tool**: N/A (text prompt to LM Studio via REST API)
- **Action**: Submit research summary for grading

### 14. manage_geometry.create_ship_exterior
- **Tool**: `unreal_engine_manage_geometry` + `unreal_engine_control_actor` + `unreal_engine_manage_asset`
- **Actions**: Multi-step pipeline for creating a procedural spacecraft exterior
- **Steps**:
  1. `manage_geometry.create_cylinder(radius=150, height=600, radialSegments=32)` → ship hull (GeneratedCylinder/DynamicMeshActor_0)
  2. `control_actor.set_transform(actorName="GeneratedCylinder", location={x:0,y:0,z:0})` → center hull
  3. `manage_geometry.create_cone(radius=120, height=200, radialSegments=32)` → cockpit nose (SM_Ship_Cockpit/DynamicMeshActor_1)
  4. `control_actor.set_transform(actorName="SM_Ship_Cockpit", location={x:0,y:0,z:400}, rotation={pitch:180,yaw:0,roll:0})` → nose forward
  5. `manage_geometry.create_box(width=40, height=60, depth=40)` → left thruster (GeneratedBox/DynamicMeshActor_2)
  6. `control_actor.set_transform(actorName="DynamicMeshActor_2", location={x:-80,y:0,z:-320})` → position left thruster
  7. `manage_geometry.create_box(width=40, height=60, depth=40)` → right thruster (GeneratedBox/DynamicMeshActor_3)
  8. `control_actor.set_transform(actorName="DynamicMeshActor_3", location={x:80,y:0,z:-320})` → position right thruster
- **Material Steps**:
  1. `manage_asset.create_material(name="MAT_Ship_Hull_Aluminum", path="/Game/Chimera/Materials/MAT_Ship_Hull_Aluminum")` → brushed aluminum hull
  2. `manage_asset.duplicate(sourcePath=<PBR_Metal>, destinationPath=<MAT_Ship_Accent_Carbon>)` → carbon composite accent
  3. `control_actor.set_component_property(actorName="GeneratedCylinder", componentName="DynamicMeshComponent", properties={material: "/Game/Chimera/Materials/MAT_Ship_Hull_Aluminum/MAT_Ship_Hull_Aluminum"})`
  4. Same for cockpit and thrusters with accent carbon material
- **Screenshot**: `control_editor.screenshot(filename="loop7_ship_exterior_v1.png", mode="editor_viewport")` → saves to `Saved/Screenshots/`
- **Result**: Full ship exterior with hull, cockpit, and twin thrusters, material-assigned
- **Parameters**: `hull={radius:150, height:600}`, `cockpit={radius:120, height:200}`, `thrusters={width:40, height:60, depth:40}`
- **Materials**: Hull = MAT_Ship_Hull_Aluminum (brushed, metallic 0.7, roughness 0.35, #A0A5A8), Accent = MAT_Ship_Accent_Carbon (composite, metallic 0.0, roughness 0.8, #2A2D30)
- **Notes**: Create material folders first via `manage_asset.create_folder(path="/Game/Chimera/...")` before `create_material`. Use existing PBR materials as duplication source for accent materials.

### 15. manage_character.configure_mesh_component (2026-07-06)
- **Tool**: `manage_character`
- **Action**: `configure_mesh_component`
- **Parameters**: `{blueprintPath, skeletalMeshPath?, animBlueprintPath?, meshOffset?: {x,y,z}, meshRotation?: {pitch,yaw,roll}}`
- **Result**: Durable Blueprint-level mesh + AnimBP assignment (survives respawn; save with `control_editor save_all`). Standard mannequin fit: offset z=-90, yaw=-90.

### 16. control_editor camera — BugItGo (2026-07-06)
- **Tool**: `control_editor`
- **Action**: `console_command` with `command: "BugItGo x y z pitch yaw roll"`
- **Result**: Moves the editor viewport camera reliably.
- **TRAP**: `set_camera_position` and `focus_actor` report success but a locked/piloted viewport does NOT move (verified: 3 different camera commands produced identical frames). Always use BugItGo.

### 17. control_actor.set_material (2026-07-06)
- **Tool**: `control_actor`
- **Action**: `set_material`
- **Parameters**: `{actorName, componentName?, materialPath, materialSlot}`
- **Result**: Real per-slot override; verify via `get_component_property propertyName=OverrideMaterials`.
- **TRAP**: `set_component_property` with `properties: {material: ...}` reports success but writes nothing.

### 18. Verification read-backs (2026-07-06)
- `control_actor.get_component_property {actorName, componentName, propertyName}` — SkeletalMesh, AnimClass, OverrideMaterials, Velocity, AnimScriptInstance, RelativeScale3D…
- ACharacter movement component is named **CharMoveComp** (not CharacterMovement).
- `control_actor.get_actor_bounds {actorName}` — origin+extent (height = 2×extent.z).
- `animation_physics.get_skeleton_info {skeletonPath}` — boneCount, socketCount (`get_skeleton_bones` NOT implemented).
- `inspect.get_property` on arbitrary object paths (e.g. anim instances) is NOT supported — smart lookup only resolves actors. Anim-node variables are unreachable; use velocity + displacement + vision instead.

### 19. PIE verification workflow (2026-07-06)
- `control_editor play` / `stop_pie` — PIE session control. Level actors keep their editor names inside PIE.
- **TRAP**: `possess` reports success but the PIE PlayerController keeps DefaultPawn_0 (`inputDiagnostics` proves it). `simulate_input` (type must be `key_down`/`key_up`) drives the DefaultPawn, not your actor.
- **PIE camera**: `set_transform` on `DefaultPawn0` positions the view; control rotation is FIXED at spawn yaw — place the pawn so its +X view frames the subject (rotating the pawn actor does not turn the view).
- **Input-free locomotion for anim evidence**: zero `BrakingDecelerationWalking`/`GroundFriction`/`BrakingFrictionFactor` on CharMoveComp, then write `Velocity` — sustains ~1s of real walking (velocity read-back + displacement + stride frames).
- `ShowDebug Animation` via console_command fails (EXEC_FAILED) — no anim debug overlay through the bridge.

### 20. control_actor.attach (2026-07-06)
- **Parameters**: `{actorName, parentActor, socketName?}` — arg is `parentActor` (`parentActorName` rejected).
- Keeps world transform on attach — snap into place with `set_transform` afterwards.

### 21b. Niagara particles (2026-07-06, Ground_Sand_Particles cycle)
- **THE working pathway**: `manage_effect spawn_niagara {systemPath, actorName, location}` — engine plugin template paths work directly (e.g. `/Niagara/DefaultAssets/Templates/Systems/FountainLightweight`).
- **TRAP (facade)**: `create_niagara_system` + `add_emitter_to_system` + all `add_*_module` actions return success:true but produce systems that render NOTHING. The plugin's own `/Game/MCPTest` leftovers have the same disease. Only the viewport render is truth.
- **TRAP (lying instruments)**: `get_niagara_info` reports emitterCount=0 even for working systems; `validate_niagara_system` says isValid=true for systems that error on spawn.
- **TRAP (simulation freeze)**: a background-throttled editor (~3fps) ticks no Niagara — systems look dead even with `set_viewport_realtime` on. Foreground the editor (PowerShell AppActivate) before trusting ANY empty frame.
- **TRAP (duplication)**: duplicating lightweight/stateless templates into /Game breaks their data interfaces (`Error initializing data interfaces`). Reference the engine asset directly.
- Property-writing `Asset` on an existing NiagaraComponent does NOT reinitialize it — delete + fresh `spawn_niagara`.
- `set_niagara_parameter`: `User.SpawnRate` works on FountainLightweight; `User.Color` rejected — param surface is per-template.

### 21. Saving (2026-07-06)
- `control_editor save_all` — saves dirty BP assets AND the level (returns savedCount).
- `manage_asset` has NO save action; `manage_level save_level` saves only the level.

---


### 22. control_actor.set_property / inspect.get_property (2026-07-06)
- **Parameters**: `{objectPath: "<ActorLabel>", propertyName, value}` — NOT actorName; missing `value` errors INVALID_VALUE.
- **Proven on**: `WorldSettings1` DefaultGameMode (swap game modes per map; survives save/restart), pawn `AutoPossessPlayer` ("Player0"/"Disabled").
- **Read back** with `inspect get_property {objectPath, propertyName}` -> result.value.

### 23. Blueprint spawning — the asset-form rule (2026-07-06)
- `control_actor spawn_actor {actorName, classPath: "/Game/X/BP_Y.BP_Y"}` — the ASSET-duplication form WORKS for Blueprints.
- **TRAP**: the class form `/Game/X/BP_Y.BP_Y_C` fails CLASS_NOT_FOUND through this bridge.
- **REVISION to pathway 1's note**: `/Engine/BasicShapes/Plane.Plane` DOES spawn — the old "no /Engine paths" lesson was specific to /Engine/EditorMeshes.
- `manage_geometry create_box` names EVERY box "GeneratedBox" — address by FName `DynamicMeshActor_<n>` (find_by_class DynamicMeshActor gives paths).

### 24. simulate_input drives AutoPossess pawns (2026-07-06, refines pathway 19's trap)
- With a level-placed pawn possessed via `AutoPossessPlayer=Player0` and NO DefaultPawn in the world, `simulate_input {type: key_down/key_up, key}` reaches the REAL player pawn (verified: W 2.0s -> 1333uu displacement read back).
- Pathway 19's "drives DefaultPawn_0" trap applies only when a DefaultPawn exists to steal input.
- Mouse-axis simulation remains UNPROVEN — beat scripts are WASD-first.

### 25. Honest fps — killing the 3fps background-throttle trap (2026-07-06)
- Write `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini` section `[/Script/UnrealEd.EditorPerformanceSettings]` -> `bThrottleCPUWhenNotForeground=False`, then **FORCE-kill** the editor (graceful shutdown overwrites the ini from memory) and relaunch.
- **Residual**: if a human actively holds window focus, run the AppActivate one-liner in the SAME command as the probe. `set_viewport_realtime` succeeds but does NOT lift the throttle.
- `get_performance_stats` reading exactly 3.0000 fps = throttle artifact, not game performance.

### 26. Sleepwalker beat runs + the save-proof ritual (2026-07-07)
- `python -m core.sleepwalker --beats docs/beats/<demo>.beats.json --session <name>` — PIE play -> beats (simulate_input + read-backs) -> stop_pie; records SimPlaytest + chronicle. Runs under CHIMERA_AGENT_SIM=1 (cannot fake human observations).
- **Save-proof ritual** (the level-loss killer): `control_editor save_all` (savedCount>=1) -> md5 of the .umap CHANGED vs baseline -> mtime now -> `get_scene_stats` recount matches. All four or it did not happen.

### 27. animation_physics add_anim_notify & get_anim_sequence_info (2026-07-07)
- **Tool**: `animation_physics`
- **Actions**: `add_anim_notify`, `get_anim_sequence_info`
- **Parameters for add_anim_notify**: `{action: "add_anim_notify", assetPath: string, notifyName: string, time: number, save: boolean}`
- **Parameters for get_anim_sequence_info**: `{action: "get_anim_sequence_info", assetPath: string}`
- **Example add_anim_notify**: `animation_physics.add_anim_notify({assetPath="/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd", notifyName="FootPlant", time=0.3, save=true})`
- **Result**: Notify event added to AnimSequence's NotifyEvents array; asset saved if save=true.
- **Read-back verification**: `animation_physics.get_anim_sequence_info({assetPath: "..."})` returns `notifyEventsCount` and other sequence info.
- **Note**: These actions are supported for AnimSequence assets. For montages, use montage notify slots via add_montage_notify or set_section_timing.

## Failed Pathways (1)

### manage_asset.list_instances
- **Tool**: `unreal_engine_manage_asset`
- **Action**: `list_instances`
- **Error**: "Action not previously tested"
- **Status**: Not yet verified as working or broken — needs testing with valid parameters.

---

## Graphify Pathways (Research Campus Queries)

### query_research_campus
- **Pathway**: `query_research_campus`
- **Steps**:
  1. `g.query('campus', school_name)`
  2. navigate to primary source
  3. extract reference data
  4. record discovery if new source found
- **Example**: `g.query("campus", "Game Development School")`
- **Result**: Returns trusted research sources and seed references for the specified school/campus from the Research Campuses directory.

---

## Automatic Pathway Recording Rule

### Before Every MCP Call:
1. Query Graphify: `g.query("pathway", "what_you_want_to_do")`
2. If pathway exists → follow it exactly
3. If pathway does NOT exist → test simplest approach, record result

### After Every MCP Call:
Record in DNA graph as a mutation node:
```json
{
  "type": "Mutation",
  "error_signature": "success_no_error" or "pathway_failed",
  "template_file": "Pathway_Name",
  "error_category": "none" or specific error type,
  "fix_description": "What was done and the result",
  "compilation_result": "pass" or "fail"
}
```

This ensures every successful MCP interaction becomes a pathway for future use. Every failure becomes a warning that prevents repeating the same mistake. The graph grows smarter with every call.

---

## How to Use This Document

1. **Find your task**: Search this document for the action you need (e.g., "spawn_actor", "create_material")
2. **Copy the parameters exactly**: Do not guess parameter names — use the schema shown above
3. **Execute via MCP**: Call the tool with the exact action and parameters
4. **Record the result**: After execution, add a mutation node to the DNA graph

If your task is NOT listed here:
1. Query Graphify first (as required by the contract)
2. If no pathway exists, test the simplest possible approach
3. If it works → add this pathway to this document and record in DNA graph
4. If it fails → note the error and try a different tool/action

## Promoted Heuristic Traps (auto-tended)

- **[H-10] pathway: build_orchestrator.ue_shutdown -> killed_for_build** — killed_for_build is the build lifecycle working as designed, not a pathway failure — record intended shutdowns as success with a note, or routine builds pollute the failure ledger.

### 27. Level-state protection (2026-07-07, root-cause fix)
- **HISTORICAL TRAP (fixed)**: build_orchestrator stamped templates/DefaultLevel.umap over
  Content/Levels/chimeradefaultlevel.umap on EVERY pipeline build — level content only survived
  while the editor held the file lock. This erased the 2026-07-03 walkabout AND the 2026-07-07
  Regolith Yard. Now seed-only (never overwrites an existing level).
- Clobber fingerprint: umap md5 == B734CFF5B6D6343B7A2BCCA43A1CB756 -> template bytes.
  Restore: editor closed -> copy L_RegolithYard.umap over -> relaunch (preflight [4.55] shouts).
- Beat scripts assert their world: expect {"world_is": "<map>"} fails fast on a wrong level.
- Sleepwalker action kinds now include {"interact"|"pickup": true} (E) and {"drop": true} (Q).
