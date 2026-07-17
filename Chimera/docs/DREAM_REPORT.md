# DREAM REPORT — morning briefing for the Gardener
consolidated: 2026-07-17T04:24:47Z

## Awaiting your approval
3 pending heuristic(s) in docs/PENDING_HEURISTICS.md:
- H-48: human_rejection: Tool_Scanner_Model
- H-49: human_rejection: Tool_Scanner_Material
- H-50: grade_CF: X

## Open phantom pains
- phase_4d2da4e032a4aa07:P1 [10d] Tri-pad materials will read uniformly dark/indistinct at walk height (viewport shot shows a near-black strip); expect the temperature to flag ground look - route to Ground_* features, lighting/material-instance work, not placement
- phase_1b01fac303f3c24e:P1 [10d] The verb TARGETS (BP_Verb_* actors) may be as hollow as the walking was - built via bridge, never human-triggered; expect pick-up/drop/shovel interactions to no-op in Session A retry; if so route Verb_PickUp/Drop/Shovel rejections and pull BP-interaction wiring into the capable Phase 2 build
- phase_3414a5cc1ff49e30:P1 [10d] Phase 2 dependencies may still block Phase 3 wiring
- phase_33cc2d55125bc551:P1 [10d] sleepwalker may still attempt PIE if runtime_report is not checked properly
- phase_a06bc8140bd62718:P1 [10d] phase_da55128aec6d109a:P1
- phase_ef0be888042d96ff:P1 [10d] The pipeline's visual stage used pyautogui desktop capture again (forbidden); the prohibition constants say use MCP screenshot mode=editor_viewport but the pipeline code still calls the old path.

## Observation queue — the true collapse awaits your eyes
- Loop 5 **Social_Trade** (system-verified 2026-07-14T14:46:35)
- Loop 6 **Shelter_Habitat_Materials** (system-verified 2026-07-14T14:46:39)
- Loop 6 **Shelter_Habitat_Lighting** (system-verified 2026-07-14T14:46:39)
- Loop 7 **Travel_Ship_Exterior** (system-verified 2026-07-14T14:46:42)
- Loop 7 **Travel_Vehicle_Basic** (system-verified 2026-07-14T14:46:42)
- Loop 7 **Travel_Vehicle_Flight** (system-verified 2026-07-14T14:46:42)
- Loop 9 **Universe_Planet_Generation** (system-verified 2026-07-14T14:46:50)
- Loop 9 **Universe_Moon_Generation** (system-verified 2026-07-14T14:46:50)
- Loop 9 **Universe_Asteroid_Field** (system-verified 2026-07-14T14:46:50)
- Loop 9 **Universe_Debris_Field** (system-verified 2026-07-14T14:46:51)

Record verdicts: `python -m core.graphify_record observe --feature X --verdict accepted|rejected --notes "..." --loop N`

## Gardener tend (delegated authority — veto any line by editing its status)
`promoted:1; needs_draft:3; untouched:47 | provisional-collapse: 0 collapsed, 13 awaiting evidence`

## Rep ledger (resolution through repetition — the dog-sit threshold)
```
[rep] 51 batteries, 806 atoms, 781 reps this pass (3 failing), 25 PIE atoms exported
[rep] PROMOTED: Sprint_Input/volume_norm: tier 0 -> 1 (behaves)
[rep] failing: Sky_Loop_Realization (1 atoms red)
[rep] failing: subsystem_Audio (1 atoms red)
[rep] failing: System_DSL_Fidelity (1 atoms red)
```

## Tonight's distillation
```
clusters >= 3: 55  |  suppressed (covered/pending): 55  |  staged: 0
  covered   [  5x] human_rejection: Verb_Shovel  <- PENDING_HEURISTICS.md
  covered   [  4x] human_rejection: Verb_Look  <- PENDING_HEURISTICS.md
  covered   [  4x] human_rejection: Verb_Bend  <- PENDING_HEURISTICS.md
  covered   [  4x] human_rejection: Verb_PickUp  <- PENDING_HEURISTICS.md
  covered   [  4x] human_rejection: Verb_Drop  <- PENDING_HEURISTICS.md
  covered   [  2x] human_rejection: Verb_Step  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Tool_Weapon_Model  <- MCP_PATHWAYS.md
  covered   [  1x] human_rejection: Ground_Metal_Surface  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Ground_Rock_Surface  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Ground_Sand_Surface  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Ground_Sand_Particles  <- MCP_PATHWAYS.md
  covered   [  1x] human_rejection: Ground_Sand_Footprints  <- MCP_PATHWAYS.md
  covered   [  1x] human_rejection: audio_visual_sync/telemetry_accessors  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: audio_visual_sync/report_telemetry  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Sky_Starfield  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Sky_Atmosphere_Scattering  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Tool_Scanner_Model  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Tool_Scanner_Material  <- PENDING_HEURISTICS.md
  covered   [ 24x] sim_rejection: verb_interactions/visor_inspection_pedestal  <- PENDING_HEURISTICS.md
  covered   [ 24x] sim_rejection: verb_interactions/weapon_tool_examine  <- PENDING_HEURISTICS.md
  covered   [ 23x] sim_rejection: verb_interactions/verb_shovel_rock_surface_location  <- PENDING_HEURISTICS.md
  covered   [ 23x] sim_rejection: verb_interactions/verb_shovel_sand_surface_location  <- PENDING_HEURISTICS.md
  covered   [ 19x] sim_rejection: verb_interactions/verb_shovel_metal_surface_location  <- PENDING_HEURISTICS.md
  covered   [ 16x] sim_rejection: regolith_yard/jump_probe  <- PENDING_HEURISTICS.md
  covered   [ 10x] sim_rejection: regolith_yard/walk_rock_to_sand_basin  <- PENDING_HEURISTICS.md
  covered   [  9x] sim_rejection: audio_visual_sync/walk_fast_on_sand  <- PENDING_HEURISTICS.md
  covered   [  6x] sim_rejection: audio_visual_sync/walk_slow_on_sand  <- PENDING_HEURISTICS.md
  covered   [  5x] sim_rejection: audio_visual_sync/spawn_and_verify_audio_system  <- PENDING_HEURISTICS.md
  covered   [  5x] sim_rejection: audio_visual_sync/report_telemetry  <- PENDING_HEURISTICS.md
  covered   [  5x] sim_rejection: regolith_yard/walk_metal_to_rock  <- PENDING_HEURISTICS.md
  covered   [  4x] sim_rejection: verb_interactions/verb_look_location  <- PENDING_HEURISTICS.md
  covered   [172x] surprise: beat discovered expected gap  <- PENDING_HEURISTICS.md
  covered   [ 63x] grade_CF: Build_Pipeline  <- PENDING_HEURISTICS.md
  covered   [ 41x] grade_CF: Visual_Verification  <- PENDING_HEURISTICS.md
  covered   [ 36x] pathway: sleepwalker.beat_run -> partial  <- PENDING_HEURISTICS.md
  covered   [ 33x] surprise: correction feature finalized frame  <- PENDING_HEURISTICS.md
  covered   [ 26x] verification_not_verified  <- PENDING_HEURISTICS.md
  covered   [ 25x] surprise: audio_visual_sync beat discovered expected  <- PENDING_HEURISTICS.md
  covered   [ 25x] compilation_fail  <- PENDING_HEURISTICS.md
  covered   [ 18x] pathway: build_orchestrator.ue_shutdown -> success_intended_kill  <- PENDING_HEURISTICS.md
  covered   [ 17x] pathway: build_orchestrator.ue_shutdown -> killed_for_build  <- PENDING_HEURISTICS.md
  covered   [ 12x] grade_CF: Player_Character_Lighting  <- PENDING_HEURISTICS.md
  covered   [ 11x] grade_CF: X  <- already pending
  covered   [  4x] grade_CF: Player_Character_Model  <- PENDING_HEURISTICS.md
  covered   [  4x] surprise: actors bp_verb_ hollow may  <- PENDING_HEURISTICS.md
  covered   [  4x] surprise: bad costless creation ending  <- PENDING_HEURISTICS.md
  covered   [  4x] surprise: bridge dsl fixes mapping  <- PENDING_HEURISTICS.md
  covered   [  3x] grade_CF: Ground_Metal_Surface  <- PENDING_HEURISTICS.md
  covered   [  3x] grade_CF: System_Economy  <- PENDING_HEURISTICS.md
  covered   [  3x] pathway: animation_physics.add_anim_notify -> failed  <- PENDING_HEURISTICS.md
  covered   [  3x] elimination_audio_visual_sync/telemetry_accessors  <- PENDING_HEURISTICS.md
  covered   [  3x] surprise: blocker draft dream endpoint  <- PENDING_HEURISTICS.md
  covered   [  3x] surprise: chaos chaos_organ core created  <- PENDING_HEURISTICS.md
  covered   [  3x] surprise: fixes generationsubsystem pipeline research  <- PENDING_HEURISTICS.md
  covered   [  3x] surprise: gate postflight refused shelter_habitat_materials  <- PENDING_HEURISTICS.md
nothing new to stage — the constitution already covers today's lessons
```

## Compaction preview (dry-run — apply is always manual)
```
live nodes: 2589  |  archivable (>30d, superseded, unreferenced): 0
dry-run: nothing moved. Re-run with --apply to archive.
```

## Research Mandate Compliance (Phase 3 Pipeline Integration)

- **Research summaries recorded:** 6
- **Documentation reviews completed:** 1
- **Pathway attempts logged:** 4
- **Tier distribution:** Tier 1=0, Tier 2=5, Tier 3=1
- **Traps avoided (PathwayAttempt trap_hit + workaround):** 0

### Tier 3 Compliance
- All Tier 3 tasks have associated research summaries (or none exist)
