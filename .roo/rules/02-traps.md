# Paid-For Traps (violating any of these wastes recorded tuition)

Full registry: `Chimera/docs/MCP_PATHWAYS.md` (traps inline) + `SUCCESSOR_RUNBOOK.md` addendum.

- **Niagara authoring is a facade**: create_niagara_system / add_emitter / add_*_module return
  success:true and render NOTHING. Spawn-only: `manage_effect spawn_niagara` with engine
  template paths (e.g. /Niagara/DefaultAssets/Templates/Systems/FountainLightweight).
- **`control_editor possess` fakes success** (PIE keeps the prior pawn). Use level-placed pawn
  `AutoPossessPlayer=Player0` + GameMode DefaultPawnClass; in-game C++ Possess() is fine.
- **`simulate_input`** drives the REAL player pawn only when it is the AutoPossess-possessed
  pawn and no DefaultPawn exists. Mouse axes UNPROVEN — script WASD-first.
- **BP spawning**: `spawn_actor classPath="/Game/X/BP_Y.BP_Y"` (asset form). The `.BP_Y_C`
  class form fails CLASS_NOT_FOUND. `/Engine/BasicShapes/*` works (old no-/Engine note was
  EditorMeshes-specific). `manage_geometry create_box` names every box "GeneratedBox" —
  address by FName `DynamicMeshActor_<n>`.
- **Actor properties**: `control_actor set_property {objectPath: "<ActorLabel>", propertyName,
  value}` (NOT actorName); read back with `inspect get_property`. Proven on WorldSettings1
  and pawn AutoPossessPlayer.
- **Save-proof ritual** (level content was lost once): `save_all` (savedCount>=1) -> umap md5
  CHANGED vs baseline -> mtime now -> scene recount. All four or it did not happen.
- **`set_component_property {material: ...}` lies** — use `control_actor set_material` and read
  back OverrideMaterials.
- **fps == exactly 3.0** = background-throttle artifact, not game performance. Foreground first
  (AppActivate in the SAME command) or rely on the applied throttle-off preference.
- **Editor config edits**: the editor overwrites its ini files on graceful shutdown — write ini,
  FORCE-kill (`taskkill //F //IM UnrealEditor.exe`), relaunch.
- **`Config/DefaultInput.ini`**: no trailing newline; ends with a GameInput section. Insert
  mappings INSIDE `[/Script/Engine.InputSettings]`, never blind-append.
- **Bridge NOT_IMPLEMENTED**: `animation_physics add_anim_notify` and `get_anim_sequence_info`.
- **Camera**: `set_camera_position`/`focus_actor` report success but a locked viewport does not
  move — BugItGo only.
- **Material params**: `manage_asset add_*_parameter` creates orphaned nodes — use
  `system_control.execute_python` with SINGLE-LINE scripts.
- **UE C++**: `TMap::operator[]` asserts on missing keys (FindOrAdd); TickComponent must match
  the exact UActorComponent signature.
- **Local LM calls** (qwen via LM Studio): prefix `/no_think`, max_tokens >= 1200, parse
  `content` AND `reasoning_content`; a reasoning dump = retry, never an answer.
