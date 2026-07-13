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
- **Reconfirmed live 2026-07-08** (`roster_and_bridge_progress` subagent, DREAM_ROSTER Tier-2 #4
  first real diagnostic pass on this TRAP — diagnosis only, no fix landed): re-ran the "lying
  instruments" claim against the actually-running editor (compiled
  `UnrealEditor-McpAutomationBridge.dll` confirmed to postdate the untouched-since-2026-06-30
  Niagara handler source, so this is live current code, not stale). `get_niagara_info` on
  `FountainLightweight` still reports `emitterCount=0` today. New finding: the SAME
  `emitterCount=0` also fires on a system created fresh via `create_niagara_system` in the same
  test run, one that the C++ explicitly attaches a `DefaultEmitter` handle to before returning
  success — tested both dotted and undotted asset-path forms, no difference. Since a
  years-old, definitely-non-empty Epic template and a system created seconds earlier in the same
  process show the identical symptom, the likelier read is a `GetEmitterHandles()`
  introspection-layer bug shared by `get_niagara_info` AND `validate_niagara_system` (same
  accessor, same result), not proof that `create_niagara_system`'s write path itself does
  nothing — `create_niagara_system` → `spawn_niagara` on the new asset → `control_actor
  get_components` chain completed with no errors and a real `NiagaraComponent0` attached.
  Whether the resulting system actually emits particles remains genuinely unverified (needs a
  foregrounded `editor_viewport` screenshot comparison, not yet done). Recorded as
  `pathway_attempt_f02d476674795953` (get_niagara_info, failed), `pathway_attempt_7c9316ed7278b9d9`
  (validate_niagara_system, failed), `pathway_attempt_5e56a84a847139dc` (create_niagara_system,
  success_unverified). Full writeup: `docs/DREAM_ROSTER.md` Tier-2 #4.

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
- `python -m core.sleepwalker --beats docs/beats/<demo>.beats.json --session <name>` — PIE play -> beats (simulate_input + read-backs) -> stop_pie; records SimPlaytest + chronicle. Runs under CHIMERA_AGENT_SIM=1 (cannot fake observations — its evidence is agent-sim SimPlaytest, never a human verdict).
- **Save-proof ritual** (the level-loss killer): `control_editor save_all` (savedCount>=1) -> md5 of the .umap CHANGED vs baseline -> mtime now -> `get_scene_stats` recount matches. All four or it did not happen.

### 27. animation_physics add_anim_notify & get_anim_sequence_info (documented 2026-07-07, ACTUALLY IMPLEMENTED + live-verified 2026-07-07)
- **CORRECTION**: this entry previously documented these actions as working from a plan/attempt that was never actually reachable — every real invocation returned NOT_IMPLEMENTED or UNKNOWN_ACTION until the Bridge Engineer fix landed (see pathway_attempt_6b3829ef3f6ea25d / pathway_attempt_bc47c3c55923ccd0, this session). Do not trust a MCP_PATHWAYS.md entry's existence as proof an action works — it wasn't, here. Re-verify live if the behavior matters.
- **TRAP (the actual root cause, surprise_39aaae26f50a1230)**: the `animation_physics` tool's dispatcher (`McpAutomationBridgeSubsystem.cpp` RegisterHandler) checks `McpConsolidatedActions::IsAnimationAuthoringAction(SubAction)` FIRST. Because `add_anim_notify`/`get_anim_sequence_info` are listed in `AnimationAuthoring()` (McpConsolidatedActionRouting.h), every call is rerouted to `HandleManageAnimationAuthoringAction` -> `HandleAnimationAuthoringRequest` in **McpAutomationBridge_AnimationAuthoringHandlers.cpp** — NOT to `HandleAnimationPhysicsAction` in McpAutomationBridge_AnimationHandlers.cpp (a separate file with its own, differently-shaped `add_notify` implementation that looks like the obvious place to fix this and IS NOT — code added there is unreachable dead code for these two action names specifically). If an action name appears in more than one `McpConsolidatedActions::Is*Action()` allowlist, trace the actual `RegisterHandler` chain before editing a handler; a clean compile proves nothing about reachability.
- **Tool**: `animation_physics`
- **Actions**: `add_anim_notify` (alias of the pre-existing `add_notify` SubAction), `get_anim_sequence_info`
- **Parameters for add_anim_notify**: `{action: "add_anim_notify", assetPath: string, notifyName: string, time: number (seconds; takes precedence over frame if present), frame: number (fallback, needs frameRate context), notifyClass: string (optional), trackIndex: number (optional), save: boolean (default true)}`
- **Parameters for get_anim_sequence_info**: `{action: "get_anim_sequence_info", assetPath: string}` (accepts `animationPath` too)
- **Example add_anim_notify**: `animation_physics.add_anim_notify({assetPath="/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd", notifyName="FootPlant", time=0.3, save=true})`
- **Live-verified result** (this session): `{success:true, message:"Notify added", assetClass:"AnimSequence", existsAfter:true}`; asset .uasset mtime updated (disk-persisted, not just in-memory).
- **Read-back verification**: `animation_physics.get_anim_sequence_info({assetPath: "..."})` returns `{notifyEventsCount, playLength, notifies:[{notifyName, time, duration, notifyClass}, ...]}`. Live-verified before/after: `notifyEventsCount` 0 -> 1, added notify's `time` read back as 0.30000001192092896 (float32 rounding of the requested 0.3 — confirms the explicit `time` param is honored, not silently dropped to the frame-based default).
- **Note**: AnimSequence assets only. For montages, use montage notify slots via `add_montage_notify` or `set_section_timing`.
- **Reverified independently 2026-07-07** (`roster_and_bridge_progress` subagent, different session from the one above — did not trust this entry at face value, per the entry's own warning): confirmed `UnrealEditor-McpAutomationBridge.dll` (mtime 18:57:19) postdates the edited source (18:55:34 / 18:48:06), then re-ran the full round trip against the live running editor from scratch: baseline (0 notifies) -> `add_anim_notify` with a distinctly-named test marker (`BridgeReverify_subagent_20260707`, time=0.42) -> read-back (1 notify, time 0.41999998688697815, float32 rounding of 0.42 confirms explicit `time` honored) -> disk mtime confirmed the write persisted -> `git checkout --` reverted the production asset -> full editor restart to resync in-memory state -> final read-back confirmed clean (0 notifies, git status clean). Recorded as `pathway_attempt_4bf27f49ed497dd1` / `pathway_attempt_f938ca71b7dd2a7c`. Both actions hold up under independent re-verification.

### 28. manage_blueprint event-graph wiring: AnimNotify -> Niagara spawn recipe + the compile gap (2026-07-08, Ground_Sand_Footprints)
- **The wiring recipe (structurally verified, non-facade, real)**: `manage_blueprint create_node` with `nodeType:"CustomEvent", eventName:"AnimNotify_<NotifyName>"` creates a genuine `K2Node_CustomEvent` matching the exact name UE's runtime notify dispatch looks up (`UAnimInstance` builds `FString::Printf(TEXT("AnimNotify_%s"), *NotifyName)` and does `FindFunction()` — this is why the event must be named with the `AnimNotify_` prefix, not the bare notify name). Chain: `CustomEvent.then -> K2Node_CallFunction(memberClass:"NiagaraFunctionLibrary", memberName:"SpawnSystemAtLocation").execute`, with `WorldContextObject`/`Location` fed from a `VariableGet(variableName:"Character")` (or equivalent actor-reference variable) piped through `nodeType:"GetActorLocation"` (aliased to `AActor::K2_GetActorLocation`), and `SystemTemplate` set via `set_pin_default_value` to a proven engine template path in `Package.Object` form (e.g. `/Niagara/DefaultAssets/Templates/Systems/FountainLightweight.FountainLightweight` — confirmed the full doubled path is required for `TrySetDefaultValue` to resolve an object pin; read back via `get_node_details`, which shows the resolved value as `defaultObjectPath`). `connect_pins` requires `fromNodeId`/`fromPinName`/`toNodeId`/`toPinName` (NOT `sourceNodeId`/`targetNodeId` — that guess returns `NODE_NOT_FOUND`).
- **TRAP (no standalone compile action)**: `manage_blueprint`'s 13 subActions do NOT include a `compile` action. `connect_pins`/`set_pin_default_value`/most `create_node` paths only call `FBlueprintEditorUtils::MarkBlueprintAsModified` + `SaveLoadedAssetThrottled` (a plain asset save, NOT a recompile) — the ONLY path that calls `FKismetEditorUtilities::CompileBlueprint` is `create_node` with `nodeType:"CustomEvent"` (`McpAutomationBridge_BlueprintGraphHandlers.cpp:1110`). If your last graph edit is a `connect_pins`/`set_pin_default_value` call made AFTER a `CustomEvent` was created, that edit is NOT baked into the compiled bytecode the running instance actually executes. **Workaround**: after finishing all wiring, create one more harmless, clearly-named, disconnected `CustomEvent` (e.g. `Mcp_CompileTrigger_<Feature>`) purely to force a final compile capturing the complete graph state. Verified this does not disturb existing wiring (re-read every node via `get_node_details` after the trigger — all connections intact).
- **TRAP (screenshot mode during PIE)**: `control_editor screenshot mode="editor_viewport"` is documented as ASYNC ("written on the next rendered viewport frame") — if the viewport isn't actively rendering new frames (background-throttle, pathway 25), repeated calls return the SAME stale frame indefinitely (confirmed: pixel-identical captures taken seconds apart across a live, moving PIE session). `mode="game_viewport"` is synchronous and PIE-specific — its response includes `"forcedViewportDraw":true` confirming it forces a fresh render; frames taken 0.5s apart genuinely differed after switching to this mode. `mode="full_editor_window"` exists too but returned `EDITOR_WINDOW_NOT_AVAILABLE` in this session even after `SetForegroundWindow` via PowerShell succeeded — untrusted/unproven.
- **UPDATE (2026-07-13, McpAutomationBridge Slate-widget capture fix)**: this TRAP's practical impact is now
  much smaller — `editor_viewport`/`game_viewport` during PIE independently capture composited UMG too now
  (see pathway #32's addendum below), so `full_editor_window`'s `EDITOR_WINDOW_NOT_AVAILABLE` flakiness noted
  above no longer forces a choice between "see the HUD" and "a reliable capture." The flakiness itself was
  NOT reproduced or fixed this session (every `full_editor_window` call this session returned clean
  `success:true`) — if it recurs, `editor_viewport`/`game_viewport` are now a working fallback for UMG
  verification specifically, not just for a scene-only capture.
- **TRAP (BugItGo during active PIE)**: works reliably in EDITOR mode (confirmed: `success:true`, moves the viewport camera). During ACTIVE PIE it consistently returned `success:false` with no visible effect — it appears to target player-pawn teleport semantics, not a general camera mover, once a PIE session/pawn exists. Setting the editor viewport camera BEFORE pressing Play does NOT carry over into PIE either (confirmed: pre-framed a clear editor shot, then PIE-start screenshot showed a completely different, fixed view). During PIE, the actual camera actor is `PlayerCameraManager0` / `PlayerCameraManager_0` — `get_actor_details` on it shows its location tracks the possessed pawn automatically each tick, and its rotation is effectively fixed (0 pitch/yaw/roll in this project's pawn, which has no camera component — `hasCamera:false`, falls back to a zero-pitch eyes-forward view at the pawn's own position). `control_actor set_transform` on it did not change the rendered frame either (likely overwritten by the next camera-update tick before capture) — getting a genuine third-person framing during PIE in a pawn with no camera component remains unsolved; the reliable evidence channel that DID work was direct engine read-back (actor/component counts, not pixels).
- **Gap (honestly unimplemented, not a facade)**: `animation_physics get_blend_space_info` returns `{success:false, error:"Animation/Physics action 'get_blend_space_info' not implemented"}` — a clean, honest failure. Blend Space sample grids and per-sample notify-trigger-weight settings cannot currently be inspected via any MCP primitive.
- **New architecture fact (Ground_Sand_Footprints specifically, likely generalizes)**: `ABP_Unarmed`'s `Walk / Run` locomotion state does not play a raw `AnimSequence` node — it uses `AnimGraphNode_BlendSpacePlayer` sampling `BS_Idle_Walk_Run` (X=Direction, Y=GroundSpeed, both computed in `BlueprintUpdateAnimation` from `CharacterMovement->Velocity`). Notifies added directly to a clip (`MF_Unarmed_Walk_Fwd`) that is sampled inside a blend space, rather than played standalone, were NOT observed to fire at runtime in extensive testing (7 walk bursts, up to 9.7s, fine-grained polling, zero firings) — genuinely unresolved whether this is the blend space itself suppressing/not-propagating the notify, or an unrelated cause; flagged, not solved.

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

### 28. Tool_Weapon_Model refinement session (2026-07-08) — geometry/material detail pass, 5 new pathway findings

**Context**: Loop4_Tools_Complete.md's known limitations ("weapon needs sight/trigger", "materials need PBR parameter tuning... could not be set via set_vector_parameter_value") were still both true when this session started — `manage_asset get_material_info` on the documented `MAT_WeaponBody` path returned `ASSET_NOT_FOUND` and the level had only 2 unrelated `GeneratedBox` actors (the original Loop4 tool scene was never saved and is gone, consistent with known limitation #5). This session rebuilt WeaponBody+WeaponBarrel and added 5 new detail parts (WeaponFrontSight, WeaponRearSightLeft/Right notch, WeaponTrigger, WeaponTriggerGuard via `create_torus`), then built two REAL parameterized materials (see #29 below) — the first time this feature's materials have had actual BaseColor/Roughness/Metallic values wired to the shader output rather than being aspirational numbers in a doc table.

**TRAP (double-transform bug, all `manage_geometry create_*` primitive actions)**: `create_box`/`create_cylinder`/`create_sphere`/`create_cone`/`create_torus`/`create_ring`/etc. all share `SpawnDynamicMeshActorWithMesh()` (McpAutomationBridge_GeometryHandlers.cpp ~line 220), which bakes the payload's `location`/`rotation` into the mesh via `AppendBox`/`AppendCylinder`/etc. (as the primitive's own `Transform` argument) AND THEN applies the SAME transform again to the spawned actor via `SetActorLocationAndRotation`. Net effect: a requested `location:{x:50,y:0,z:0}` lands the actor's real-world center at `(100,0,0)` (translations double additively); a requested single-axis rotation doubles too (`pitch:90` composes with itself into a net 180°, confirmed empirically — a cylinder requested with `rotation:{pitch:90}` at creation came back with `get_actor_bounds` extent unchanged from unrotated, exactly what a net-180°-pitch on a Z-up cylinder produces). The success response never echoes back the actor's real transform, so this is silent unless you explicitly read bounds/transform after creating.
**Workaround (used this session, works cleanly)**: create at identity (omit `location`/`rotation` entirely, or pass zeros) so nothing gets doubled, then reposition with `control_actor set_transform` (pathway #2) — a single, non-doubling application. Verified via `inspect get_actor_details` (the authoritative real-transform read, see next TRAP) that this produces exactly the intended final location/rotation.

**TRAP (lying instrument): `get_actor_bounds`/`get_bounding_box` on a `DynamicMeshComponent` caches the bounds computed at mesh-creation time and does NOT recompute after a later `control_actor set_transform`.** Moved an actor from its doubled spawn position to the intended one via `set_transform` (which itself reported the correct new location and is genuinely correct — confirmed independently), then immediately called `get_actor_bounds` on the same actor: it still reported the STALE pre-move origin. `inspect get_actor_details {actorName}` (returns `transform: {location, rotation, scale}` directly off the actor, not a cached component bounds box) and `control_actor get_component_property {propertyName: "RelativeLocation"}` both correctly showed the new, real position. **Rule: for a `DynamicMeshActor` that has ever been moved post-creation, do not trust `get_actor_bounds`'s origin — use `inspect get_actor_details` or a direct property read instead.** This is the same "lying instruments" shape as the Niagara `get_niagara_info` trap in #21b: the write path is correct, the specific introspection endpoint is not.

**TRAP (path-format footgun, self-inflicted but worth flagging): `create_material`'s response `assetPath` field is a BARE package path (`/Game/Tools/Materials/MAT_Foo`), not the doubled `/Path/Name/Name` form used elsewhere in this doc (e.g. pathway #12's own example).** Constructing `{path}/{name}/{name}` by hand for a subsequent `get_material_info`/`compile_material`/`connect_material_pins` call reliably returns `ASSET_NOT_FOUND` even though the asset genuinely exists — cost real time this session chasing a phantom "environment instability" theory before the actual cause (wrong path string) was found. **Use the exact `assetPath` string `create_material` returns, unmodified** (both the bare form and the dotted `Name.Name` form work; the doubled-slash form does not).

**TRAP: `create_material` can return `ASSET_EXISTS` (or, on the very first attempt against a brand-new name under load, a generic `ENGINE_ERROR` that still silently creates a blocking in-memory package) for a name `get_material_info`/`delete_assets` both simultaneously report as `ASSET_NOT_FOUND`.** Reproduced twice this session (`MAT_WeaponBody` — likely an orphaned unsaved package surviving from the original 2026-07-03 Loop4 session in the long-running editor process; `MAT_WeaponFrame` — created fresh by this same session's own first, failed `ENGINE_ERROR` attempt). `delete_assets` cannot clear these zombies either (same `ASSET_NOT_FOUND`). **Workaround: just use a different, never-tried name** (this session landed on `MAT_WeaponFrame2`, hence the material is NOT named `MAT_WeaponBody` as Loop4_Tools_Complete.md's table would suggest — a deliberate, documented naming deviation, not a mistake).

**TRAP: `control_actor set_material` on a `DynamicMeshComponent` calls `Component->SetMaterial(Slot, Material)` (McpAutomationBridge_ControlHandlers.cpp ~line 1690) and reports genuine success (verified: no error, correct `resolvedMaterialPath` echoed) — but `get_component_property {propertyName: "OverrideMaterials"}` reads back `[]` empty both before AND after, unlike pathway #17's documented behavior for a `StaticMeshComponent`.** Tried `ConfiguredMaterialSet`/`MaterialSet`/`Materials`/`Material` as alternate property names — all `PROPERTY_NOT_FOUND`. `DynamicMeshComponent` evidently does not expose its material slot(s) through any reflectable property name this bridge can read, only through the `SetMaterial()` function call itself. **Pathway #17's "verify via OverrideMaterials" rule is StaticMeshComponent-specific; for DynamicMeshActor material assignment, the only available verification is visual (screenshot) or trusting the error-free `set_material` response.**

**TRAP (reconfirms #19's world-preference note under a new operation class): during an active PIE session — started by a concurrent agent's own task in this same shared editor, not this session — `control_actor set_material`, `inspect get_actor_details`, and `manage_geometry create_*` all resolve against `GEditor->PlayWorld` (actor paths show a `UEDPIE_0_` prefix) instead of the persistent editor level. A `set_material` call issued mid-PIE returns a distinct, checkable error (`ENGINE_ERROR: "The Editor is currently in a play mode."`) rather than silently succeeding against the wrong world, which makes it safe to detect and retry — poll `inspect get_actor_details` on a known actor and check for the `UEDPIE_0_` prefix before issuing any `create_*`/`set_material`/camera call, retry once the prefix is gone.** `console_command BugItGo` and `set_viewport_camera` BOTH report `success:true`/`EXEC_FAILED` inconsistently and do not move the viewport at all while a concurrent PIE session holds it — this is pathway #16's "locked/piloted viewport" trap, now confirmed to also apply to a viewport piloted by SOMEONE ELSE'S PIE session, not just your own.

### 29. Building a REAL tunable PBR material (2026-07-08) — the actual fix for the #21/known-limitations "set_vector_parameter_value doesn't work" complaint

**Root cause of the historical failure**: `manage_asset create_material` (`UMaterialFactoryNew` + `UMaterial::StaticClass()`) creates a completely BLANK material — zero expression nodes, nothing wired to BaseColor/Roughness/Metallic. It does NOT accept `baseColor`/`roughness`/`metallic` payload fields despite Loop4_Tools_Complete.md's asset table listing specific values as if they'd been applied — those values were evidently never actually baked into the graph. `set_vector_parameter_value`/`set_scalar_parameter_value` (also under `manage_asset`) only work on a `UMaterialInstanceConstant` that already has a NAMED parameter of that type on its parent material to override — calling them on a plain, blank `UMaterial` (which has no parameters at all) is a category error, not a path-resolution bug as the original doc guessed.
**The actual working pathway** (`manage_asset`, all in one asset, no MaterialInstance needed):
1. `create_material {name, path}` → blank `UMaterial`.
2. `add_vector_parameter {assetPath, parameterName:"BaseColor", defaultValue:{r,g,b,a}}` → returns `nodeId` (parse from the response's `text` field, e.g. regex `nodeId:\s*(\S+)` — the structured JSON's nesting for this field was unreliable this session, the flat text summary was not).
3. `add_scalar_parameter {assetPath, parameterName:"Roughness"|"Metallic", defaultValue:N}` → same, one call per scalar.
4. `connect_material_pins {assetPath, sourceNodeId:<from step 2/3>, targetNodeId:"Main", inputName:"BaseColor"|"Roughness"|"Metallic"}` — `targetNodeId:"Main"` (or omitted) is the sentinel for "the material's own root output pins", NOT another expression node; also accepts `EmissiveColor`/`Specular`/`Normal`/`Opacity`/`OpacityMask`/`AmbientOcclusion`/`SubsurfaceColor`/`WorldPositionOffset`.
5. `compile_material {assetPath, save:true}` → forces `PostEditChange`+save.
6. Verify with `get_material_info {assetPath}` — check `connections` array has one entry per wired input, and `expressions[].desc` shows the literal baked value (e.g. `"Param (0.42) 'Roughness'"`).
**Result this session**: `MAT_WeaponFrame2` (gunmetal frame/barrel: BaseColor (0.11,0.115,0.125), Roughness 0.42, Metallic 0.85) and `MAT_WeaponAccent` (matte polymer sights/trigger/guard: BaseColor (0.025,0.025,0.025), Roughness 0.68, Metallic 0.05) both compiled clean with exactly 3 real connections each, confirmed via `get_material_info` read-back — the first time this feature's material has had genuine, verified PBR parameters rather than an aspirational doc table.
- Sleepwalker action kinds now include {"interact"|"pickup": true} (E) and {"drop": true} (Q).

### 28. manage_geometry create_* traps + DynamicMeshComponent material gap (2026-07-08, Travel_Ship_Exterior cycle)
- **TRAP (location double-bake)**: passing `location` directly to `manage_geometry` `create_cylinder`/
  `create_cone`/`create_box` bakes the offset into the generated mesh's LOCAL vertex data **and** sets
  the actor's `Transform.Location` to the same value — the rendered mesh ends up at 2x the requested
  world position (requested z=1400 -> rendered at z=2800, confirmed via `get_actor_bounds` on 2
  independent actors). **WORKAROUND**: never pass `location` to `create_*`; spawn with no location
  (renders at local/world 0,0,0), then a *separate* `control_actor set_transform` call to place it —
  this is why pathway #14's recipe already used a 2-step create-then-transform pattern.
- **TRAP (cone radius ignored)**: `create_cone`'s `radius` parameter is not applied to the generated
  mesh — radius=200 and radius=800 both produced identical `extent.x=extent.y=50` (2 independent clean
  spawns). `height` is applied correctly (`extent.z = height/2`). **WORKAROUND**: spawn, read bounds,
  then apply a corrective non-uniform `set_transform` scale (`scale.x=scale.y=target_radius/50,
  scale.z=1.0`). Cone's default orientation is apex-up (+Z) with zero rotation — confirmed visually,
  no pitch=180 needed (unlike pathway #14's assumption for a different, unverified recipe).
- **Axis mapping (create_box)**: on an unrotated box, `width` maps to local X, `height` maps to local Y,
  `depth` maps to local Z — confirmed via bounds (w=300,h=400,d=800 -> extent=[150,200,400]). This is
  NOT the intuitive convention (height often assumed -> Z); account for it when choosing dimensions for
  a specific world-space orientation.
- **TRAP (DynamicMeshComponent set_material)**: `control_actor set_material` (proven for
  StaticMeshComponent by pathway #17) reports `success:true` with fully correct routing info
  (actorPath/resolvedMaterialPath/materialSlot all echoed) on a `DynamicMeshActor`'s
  `DynamicMeshComponent`, but an immediate `get_component_property propertyName=OverrideMaterials`
  read-back (zero-latency, PIE confirmed inactive at both calls) still returns an empty array. 0/7
  tested pieces persisted. Root cause unconfirmed; `DynamicMeshComponent` (GeometryScripting) may store
  its material list through a path the generic `OverrideMaterials` reflection doesn't see.
- **TRAP (material root-pin connection undiscoverable)**: `add_scalar_parameter`/`add_vector_parameter`
  work correctly (nodes created with correct values, confirmed via `get_material_info`), but wiring them
  to the material's root Base Color/Metallic/Roughness output via `connect_material_pins` or
  `connect_nodes` never succeeded — 6 reasonable `targetNodeId` sentinels (`Material`, `Root`, `Result`,
  `0`, `MaterialOutput`, `Output`) all returned `NODE_NOT_FOUND`. **Not unique to one material**:
  `MAT_Rover_Chassis_Aluminum` and `MAT_GroundSand` — both tied to already-`implemented` features — show
  the identical unconnected state (`connections: []`) despite one having scalar params in active use.
  This looks like a pre-existing, project-wide gap in the material-authoring MCP surface, not something
  any single feature session introduced. The correct `targetNodeId` convention for the root output
  remains genuinely undiscovered — a fresh session should NOT re-guess sentinels without new information.
- **TRAP (concurrent-agent interference)**: observed PIE starting/stopping without this session ever
  calling `action=play`; `manage_geometry` spawns intermittently landing in a transient
  `/Game/Levels/UEDPIE_0_chimeradefaultlevel` world instead of the persistent level; `BugItGo`
  intermittently `EXEC_FAILED` or silently framing an unrelated part of the level (one screenshot showed
  Niagara dust particles + rope/tether props consistent with a different concurrent agent's work); and 3
  of 7 correctly-positioned+saved `DynamicMeshActor` transforms reverted to `(0,0,0)` between two reads
  with no `set_transform` call from this session in between. 4 concurrent `python.exe` processes were
  observed running. No `.ORCHESTRATOR_STATUS` file and the orchestrator HTTP status endpoint was
  unreachable, so the exact other process was not identified. **WORKAROUND**: call `stop_pie`
  defensively before every `create_*`/`set_material` call, check `actorPath` in the response for a
  `UEDPIE_` taint and retry if found, re-verify bounds after any gap before trusting prior state, and
  `save_all` (with an md5 check) as soon as a milestone is reached rather than deferring it.
- **CONFIRMED working**: `manage_asset search_assets`'s `directory` parameter is a no-op — it returns
  the same alphabetically-first N project-wide assets regardless of the `directory` value passed (tested
  against 3 different directory values, identical results each time). `classNames` filtering DOES work
  correctly. Use `classNames` + page via `offset` and filter client-side if you need a specific folder.

### 30. Rebuilding without killing the shared editor — LiveCoding.Compile via console_command (2026-07-08, task_c11196d2 fix)
- **Problem**: `build_orchestrator.py`'s documented build lifecycle (CLAUDE.md "Build fails — DLL locked")
  force-kills `UnrealEditor.exe` before invoking UBT. In a session with heavy confirmed concurrent
  multi-agent activity (4 other `python.exe` processes observed; no `.ORCHESTRATOR_STATUS` file or
  reachable `:8765/status` to identify them), the harness's own permission system BLOCKED the
  `taskkill /F /IM UnrealEditor.exe` call outright ("risks destroying another concurrent session's live
  PIE/editor state") — this is a hard stop, not a suggestion to retry via a different command.
- **`manage_pipeline run_ubt`** (McpAutomationBridge_PipelineHandlers.cpp) does NOT solve this — it just
  spawns `Build.bat` as a detached process without closing the editor first, so it hits the identical
  DLL-lock link failure a manual Build.bat invocation would.
- **THE working non-destructive alternative**: `control_editor console_command command="LiveCoding.Compile"`.
  Patches the already-running editor's module DLL in place — no process kill, no PIE interruption. Confirmed
  live: compiled a `.cpp`-only change (new #include + 2 constructor lines, header untouched — exactly
  Live Coding's sweet spot, no ABI/layout change) in ~90s end-to-end. Poll `Saved/Logs/Chimera.log` for
  `LogLiveCoding: Display: Live coding succeeded` (success) vs an error after `Starting Live Coding compile`
  (failure) — the command's own MCP response only confirms the console command was *issued*, not that the
  compile finished, since Live Coding runs async.
- **Don't be spooked by**: an `ERROR: Access violation writing at address: ...` inside `UbaCli.exe`'s own
  callstack appearing mid-log — this is the Unreal Build Accelerator helper process, and it appeared here
  immediately BEFORE `Display: Reload/Re-instancing Complete` and `Live coding succeeded` both fired cleanly
  right after. Confirmed benign by the strongest evidence available: the patched code's own new `UE_LOG`
  line (`"PlayerControllerClass set to ADemoPlayerController"`) printed in the log seconds later, from CDO
  reconstruction during the reload — content-specific proof the new code compiled AND executed, not just a
  hopeful reading of "succeeded".
- **CAVEAT**: only proven for a function-body-only `.cpp` change so far. Header/layout changes (new
  UPROPERTY/UFUNCTION, new base class, changed member order) are widely known to be unreliable-to-impossible
  for Live Coding in UE5 generally — for those, the editor-kill path (or asking the user directly, per the
  permission system's own guidance) is still the only proven route in this project.

### 31. BugItGo during active PIE is HARD-REJECTED, not just a silent no-op (2026-07-08, verb_interactions H-17 reverify)
- **Strengthens pathway 28's "BugItGo during active PIE" trap** (line ~240, discovered as `success:false`
  with no visible effect during camera-framing work). This session hit a harder failure mode attempting to
  use `move_to` (sleepwalker's `console_command command="BugItGo x y z pitch yaw roll"` wrapper) as a
  position-reset for beat-script pawn teleports: **`control_editor.console_command` raised an explicit error,
  `"Command not executed: BugItGo <x> <y> <z> 0.0 0.0 0.0"`, on all 5 attempts**, once PIE was active with
  `ADemoPlayerController` possessing `BP_Astronaut_Character_C` (the now-working post-task_c11196d2 setup).
- **Confirmed PIE-specific, not a general BugItGo failure**: the identical command (`BugItGo 0.0 0.0 150.0
  0.0 0.0 0.0`) issued in EDITOR mode (`isPIE:false`, freshly confirmed via `runtime_report` immediately
  before the call) returned clean `success:true` / `"Command executed: BugItGo ..."`. The failure is
  specific to the moment a real PlayerController/pawn exists under PIE — consistent with pathway 28's own
  read ("appears to target player-pawn teleport semantics, not a general camera mover, once a PIE
  session/pawn exists"), now confirmed as an outright rejection rather than a quiet no-op. Likely cause
  (untested this session, flagged for whoever picks this up): `BugItGo` is a `UCheatManager` exec function
  gated behind cheats being enabled on the possessing `PlayerController`; `ADemoPlayerController` may never
  call `EnableCheats()` / may have no `CheatClass` set, so the command has nothing to resolve against once
  a real PIE PlayerController (as opposed to the editor's implicit context) is in the loop.
- **Practical impact**: `docs/beats/*.beats.json` cannot currently use `move_to` to reset pawn position
  mid-PIE for choreography that spans multiple checkpoints in one continuous beat run — every beat sharing
  a PIE session inherits whatever position the previous beats' real WASD movement left it at. Position-
  dependent `pawn_within` expects must either (a) tolerate cumulative drift by using very generous radii and
  ordering beats along a single monotonic walking path, or (b) wait for a real fix (cheats-enabled on
  `ADemoPlayerController`, or an alternate teleport primitive) before relying on absolute-coordinate resets.
  `docs/beats/verb_interactions.beats.json` currently uses approach (a) implicitly (and imperfectly — see
  its own `_provenance` field for the exact drift numbers) rather than (b).

### 32. TRAP — UMG/Slate HUD verification MUST use `mode=full_editor_window`, never `editor_viewport`/`game_viewport` (2026-07-13, P0 O2 witness workflow)
- **Root cause (read directly from source, both capture paths)**: `editor_viewport` and the empty-mode
  default both route to `HandleControlEditorScreenshot` (`McpAutomationBridge_ControlHandlers.cpp` ~3941),
  which calls `Viewport->ReadPixels(Bitmap, ReadFlags)` on the active viewport's render target.
  `game_viewport` routes to a second, separate `ReadPixels` call in `McpAutomationBridge_UiHandlers.cpp`
  (~line 533). **Both are raw 3D-scene render-target readbacks that run BEFORE the Slate/UMG compositor
  draws the UI layer on top** — a `UUserWidget` added via `AddToViewport()` (e.g. `WID_O2HUD`, the diegetic
  O2/battery/dust wrist gauge) is genuinely on screen but simply is not IN the buffer either mode reads.
  This is why a HUD can false-negative as "not rendering" when the underlying widget tree, bindings, and
  `AddToViewport()` call are all completely correct — the capture method itself is blind to Slate, not the
  widget.
- **The one mode that works**: `mode=full_editor_window` calls `CaptureSlateWindowPngForMcp` on
  `GetFullEditorSlateWindowForMcp()` (~line 3870) — a genuine Slate **window** capture (the whole editor
  frame, compositor included), which DOES show UMG. Confirmed empirically this session for `WID_O2HUD`.
  Trade-off: it captures the full editor chrome (menus/panels), not just the game view, and is a heavier,
  synchronous capture — acceptable for a HUD-verification screenshot, not a substitute for routine
  world/actor screenshots.
- **Not cheaply fixable at the other two modes** — don't rabbit-hole trying: making `ReadPixels` include
  Slate would mean either compositing UMG onto the 3D render target before the readback (a real rendering
  pipeline change) or switching those paths to a Slate-level capture too (which is exactly what
  `full_editor_window` already is, just scoped to the whole window instead of one viewport). The convention
  below IS the fix.
- **Rule**: any beat/verification that needs to SEE a UMG HUD (not just confirm it exists/attaches) must
  request `mode="full_editor_window"` explicitly. `core/sleepwalker.py`'s `screenshot` action now accepts an
  optional `"mode"` key on the action (`{"screenshot": "name", "mode": "full_editor_window"}`); it still
  defaults to `"editor_viewport"` for backward compatibility with beat files that only want a world shot.
- **Freshly reconfirmed with live values, not just presence** (`docs/beats/o2_survival_witness.beats.json`,
  2026-07-13): three `full_editor_window` captures across one continuous session show the SAME gauge cluster
  tracking real, changing numbers — `O2: 95%` (healthy), `O2: 10%` + a visible yellow `WARNING: Low O2` line
  (alarm), `O2: 71%` with the warning gone (recovered) — each matching that beat's `component_property_above/
  below` read-back within a percent or two. This is stronger evidence than "the HUD renders": the SAME
  screenshot mode was proven to reflect LIVE component state across three different states in one run.
- **FIXED (2026-07-13, later same day — McpAutomationBridge_ControlHandlers.cpp / McpAutomationBridge_UiHandlers.cpp)**:
  `editor_viewport` and `game_viewport` now ALSO capture composited UMG during PIE, via a genuine Slate-widget
  capture (`FSlateApplication::TakeScreenshot` on the level viewport's actual `SViewport` widget —
  `IAssetViewport::GetViewportWidget()`, falling back to `AsWidget()` if that weak pointer is stale — instead
  of `FViewport::ReadPixels`). `TakeScreenshot` forces a real Slate paint of the widget's owning window (so
  UMG composited via `SGameLayerManager` is genuinely drawn into the frame) then crops the result to the
  widget's own on-screen rectangle — scene + UMG, cropped to just the viewport, NOT the whole editor window
  like `full_editor_window`. Falls back automatically to the original scene-only `ReadPixels` path if PIE
  isn't active, the LevelEditor module/viewport widget is unavailable, or the Slate capture fails/returns
  empty pixels — the plain-editor-mode (no PIE) behavior is completely untouched by this fix.
  **Empirically verified this session** with `docs/beats/mcp_screenshot_hud_repro.beats.json` (possess → all
  3 modes fired back-to-back against the identical on-screen HUD state, before AND after an editor rebuild):
  BEFORE the fix, `editor_viewport`/`game_viewport` were both 1048×462 with NO "SUIT STATUS" HUD visible (the
  raw particle-fountain scene only, confirmed by opening the actual PNGs); `full_editor_window` was 1490×906
  WITH the HUD but the whole editor chrome (menu bar, Outliner, World Partition/Settings tabs, Output Log).
  AFTER the fix (rebuilt `UnrealEditor-McpAutomationBridge.dll`, fresh PIE session), `editor_viewport` and
  `game_viewport` are both 1048×461 (viewport-sized, not 1490×906 — confirmed via PNG IHDR dimensions) and
  BOTH now show the identical "SUIT STATUS / O2: 99% / BAT: 100% / DUST: 0%" HUD in the bottom-left, matching
  what `full_editor_window` already showed in the same run; `full_editor_window` itself unchanged (still
  1490×906, still shows the HUD, still whole-window — no regression). The response JSON also gained two
  fields on this path: `includesUmgOverlay: true` and `captureMethod: "slate_widget"` (vs `"read_pixels"` on
  the scene-only fallback), so a caller can tell which path actually served a given capture without having to
  infer it from pixels.
  **New recommendation**: `editor_viewport` (or `game_viewport`) is now sufficient for UMG/HUD verification
  during PIE — `full_editor_window` is no longer required for that purpose specifically, though it remains
  available and unchanged for whole-editor-chrome captures. See also pathway #28's addendum above. CLAUDE.md's
  H-2 heuristic updated accordingly.

### 33. Bounded, self-cleaning witness runs — `core/witness_runner.py` (2026-07-13, P0 O2 witness workflow)
- **The failure this fixes**: a prior witness session hung for ~7-8 real minutes (an O2-depletion beat
  waiting out the drain rate live, real-time) and left `UnrealEditor.exe` running — orphaned, because
  nothing outside the hung process ever got to run `Sleepwalker.run()`'s own `finally: stop_pie()`.
  `core.sleepwalker` has no OUTER wall-clock cap of its own (only a 30s-per-MCP-call socket timeout inside
  `MCPStdioClient._read`); a beat script whose actions sum to several minutes of real `wait`/`hold_s` (or one
  hung call retried across several beats) has no ceiling, and whatever external process is driving it (an
  agent's own tool-call timeout, a closed terminal) can kill it before its cleanup code ever runs.
- **The fix**: `python -m core.witness_runner --beats <path> --session <name> [--budget-s 240]
  [--close-editor-on-exit]` wraps `core.sleepwalker` instead of calling it directly for any witness run
  expected to run unattended or for longer than a minute or two:
  1. Runs the beat script as a **child process** under a real `subprocess` timeout — the sleepwalker no
     longer has to be trusted to self-terminate.
  2. On timeout, kills the child's **whole process tree** (`taskkill /T /F /PID <pid>`, not a bare
     `.kill()`) — a plain single-process kill can strand grandchildren, e.g. the `node.exe` MCP bridge CLI
     each `MCPStdioClient()` construction spawns.
  3. **ALWAYS**, in a `finally` (timeout, crash, or clean exit alike), opens a **fresh** `MCPStdioClient` and
     issues `stop_pie` — proven safe to rely on regardless of the child's fate, since `MCPStdioClient` spawns
     its own short-lived bridge-CLI process per construction and reaches the SAME running editor over its
     socket; it does not depend on the dead child's pipes or in-process state.
  4. `--close-editor-on-exit` additionally force-kills `UnrealEditor.exe`/`-Cmd.exe`/
     `CrashReportClientEditor.exe` (the same list `core.editor_scheduler._kill_ue_processes()` uses) and
     releases this agent's scheduler claim. **Off by default** — the studio's normal mode is ONE shared
     long-lived editor across concurrent agents (`core/editor_scheduler.py`); only pass this flag for a
     witness session that is explicitly the last thing an agent does before ending its shift.
  5. **Un-throttles before every launch it triggers** — see the NEW trap below (#34); a background-launched
     editor stalling at 3fps looks EXACTLY like a hang from the outside, and was in fact the root cause this
     session re-discovered while trying to re-run the SuitLifeSupport acceptance tests headlessly.

### 34. TRAP — a background-launched (unfocused) editor can silently stall `Automation RunTests` forever, not just run it slowly (2026-07-13, re-running SuitLifeSupport acceptance tests)
- **Symptom**: `core.unblock.ensure_editor()` (or any headless/background editor launch) followed by
  `Automation RunTests ChimeraTests.Acceptance.<X>` via `console_command` never produces a single test
  result, no matter how long you wait — indistinguishable from a hang unless you read the log.
- **Root cause, confirmed live in `Chimera.log`**: `LogEngineAutomationLatentCommand: FWaitForInteractiveFrameRate:
  Starting wait for framerate of >= 10 FPS`, then repeating `Current FPS=3` every 30s, `Will timeout in
  570[s]`. UE's OWN automation framework refuses to start the queued tests until the engine reaches 10fps —
  and an editor launched without OS window focus throttles to ~3fps (`bThrottleCPUWhenNotForeground`,
  pathway #25's trap, generalized here: it doesn't just fake low telemetry readings, it can block an entire
  automation run for its full timeout, which for `FWaitForInteractiveFrameRate` is 600 real seconds).
- **The fix**: set `bThrottleCPUWhenNotForeground=False` in
  `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini`
  (`[/Script/UnrealEd.EditorPerformanceSettings]`) BEFORE the editor launches — `core/witness_runner.py`'s
  `_ensure_unthrottled()` does this automatically now. Only takes effect on the editor's NEXT launch (an
  already-running instance must be restarted to pick it up). Foregrounding the window
  (`SetForegroundWindow`) is a belt-and-suspenders addition, not a substitute — a human stealing focus can
  defeat it mid-session (pathway #25's own caveat), the ini fix does not depend on focus at all.
- **Practical impact for THIS session**: this is very likely why the design directive's own reported ~7-8
  minute witness stall happened, and why standalone `UnrealEditor-Cmd.exe -ExecCmds="Automation RunTests..."`
  invocations in this environment either exit near-instantly via a `-TestExit` race (the phrase the exit
  watcher looks for can match before any test has actually run) or spin for the framework's own multi-hundred
  -second internal timeout with `-TestExit` omitted — neither is a fast, reliable headless test path here.
  The reliable path found this session: launch/confirm the editor via `core.unblock.ensure_editor()` (with
  the ini fix already in place), then issue `Automation RunTests <suite>` via
  `control_editor console_command` through the MCP bridge, and poll `Chimera.log` for
  `LogAutomationController`/`LogAutomationTest` result lines with your OWN bounded timeout — the same
  discipline pathway #33 documents for witness beat runs applies here too.
- **Compress game-time, don't wait it out**: `core/sleepwalker.py` gained an `advance_suit_seconds` beat
  action instead of `wait`-ing out the real ~5-6 minute O2 drain/regen curves.
  - **First attempt (FAILED, corrected same session)**: called `USuitLifeSupportComponent::AdvanceLifeSupport(N)`
    via `execute_python`, finding the component with
    `unreal.EditorLevelLibrary.get_all_level_actors()`. Confirmed live this session that this silently does
    nothing during PIE: `EditorLevelLibrary` resolves the EDITOR world, not the active PLAY world, so it never
    finds a component that was runtime-attached (`NewObject`+`RegisterComponent`) to the PIE pawn at
    `OnPossess` — the beat's O2 read-back afterward showed only the ordinary real-time drain from the
    beats around it, not the intended multi-hundred-second jump (`simtest_3d6d12a284a70d04`,
    `o2_drains_to_alarm` failure evidence).
  - **Working fix**: no `control_actor` primitive can call a component `UFUNCTION` with a real argument
    either (`call_function`/`HandleControlActorCallFunction` only finds functions on the ACTOR, not its
    components, and zeroes every parameter buffer regardless of what you pass — verified by reading the
    handler source, not assumed), so instead of calling the component's function at all,
    `advance_suit_seconds` now computes the SAME per-game-minute delta the component's own `TickLifeSupport`
    would (`property += rate_per_min * seconds/60`, clamped to an optional `min_floor`/`max_ceiling`) and
    writes the result through `control_actor set_component_property` — proven to correctly resolve the live
    PIE actor all session (every `reset_position`/`get_component_property` call in the same beat run worked).
    A short settle wait afterward lets the component's own next real `TickComponent` (still ticking normally
    in PIE) run `UpdateO2Edges()` off the new baseline, so `bLowO2`/`bDead` flip through the REAL edge-detection
    logic, not a second manual property write. `min_floor` (e.g. 10.0 for a drain call) matters: a plain
    `current + delta` clamped only to the component's own 0..100 range can overshoot to exactly 0 and trip
    `bDead` depending on incidental real-time drain from the surrounding beats — a floor above 0 makes the
    landing value insensitive to that noise while staying in the intended alarm band.
  - Verified afterward through the already-proven `get_component_property` read-back (new generic
    `component_property_below`/`component_property_above` expects) either way — the fast-forward mechanism's
    own correctness is never trusted on faith. See `docs/beats/o2_survival_witness.beats.json` for the full
    pattern (walk/sprint/bend legs are real PIE input; only the O2-depletion and refill legs are
    time-compressed, and are labeled as such in that file's `_provenance` and per-beat `_note`s).
- **TRAP found while building this (not yet fixed — flagged for a follow-up, not blocking)**: `core.sleepwalker`'s
  pre-existing `_TELEMETRY_SCRIPTS` execute_python fallback (Tier 2 of the `"command"` action) searches for a
  component whose type name contains `'SandSound'` and calls e.g. `.FootstepSyncEventCount` as a bare
  property access — but `GetFootstepSyncEventCount()` and its siblings are `static` `UFUNCTION`s on
  `UChimeraMovementComponent` (reading a module-global `TArray`), not properties on `USandSoundComponent` at
  all (confirmed by reading `ChimeraMovementComponent.h`/`.cpp` directly). This fallback would silently fail
  (wrong class searched, then a property-vs-function-call mismatch) every time it's actually invoked. It is
  currently latent/harmless because **Tier 1 already works**: `manage_tools` routes these exact action names
  to a correct, dedicated native handler (`HandleManageToolsAction`,
  `McpAutomationBridgeSubsystem.cpp` ~847, calling `UChimeraMovementComponent::Get*()` directly) — confirmed
  by reading that handler too. `docs/beats/o2_survival_witness.beats.json`'s `footstep_telemetry_summary`
  beat relies on Tier 1, not the fallback. Worth fixing the fallback anyway so a real Tier-1 regression
  degrades to a working Tier 2 instead of a differently-broken one.
