# DREAM REPORT — morning briefing for the Gardener
consolidated: 2026-08-03T07:15:01Z

## Awaiting your approval
14 pending heuristic(s) in docs/PENDING_HEURISTICS.md:
- H-48: human_rejection: Tool_Scanner_Model
- H-49: human_rejection: Tool_Scanner_Material
- H-50: grade_CF: X
- H-59: surprise: aerisaidactor candidate expectation score
- H-60: surprise: research shelter_habitat_lighting waived witness
- H-61: surprise: atom beat_scripts_tautology_fix fix red
- H-62: sim_rejection: travel_vehicle_basic/vehicle_component_initialized
- H-63: sim_rejection: solar_system_stand/stand_on_grown_ocean_world

## Open phantom pains
- phase_4d2da4e032a4aa07:P1 [27d] Tri-pad materials will read uniformly dark/indistinct at walk height (viewport shot shows a near-black strip); expect the temperature to flag ground look - route to Ground_* features, lighting/material-instance work, not placement
- phase_3414a5cc1ff49e30:P1 [27d] Phase 2 dependencies may still block Phase 3 wiring
- phase_33cc2d55125bc551:P1 [27d] sleepwalker may still attempt PIE if runtime_report is not checked properly
- phase_a06bc8140bd62718:P1 [27d] phase_da55128aec6d109a:P1
- phase_0ddffb52d2d75240:P1 [27d] The bridge's NOT_IMPLEMENTED on add_anim_notify will re-block every feature needing anim events until a capable session patches Plugins/McpAutomationBridge
- phase_3baeff0ccd0f4556:P1 [27d] phase_da55128aec6d109a:P1, phase_762486f41e1aeafb:P1, phase_762486f41e1aeafb:P3, phase_fda9e71b0c0841b4:P3

## Observation queue — the true collapse awaits your eyes
- Loop 1 **Hierarchical_Membrane_System** (system-verified 2026-07-22T00:52:10)
- Loop 1 **Biological_Specificity_Labeling** (system-verified 2026-07-22T00:52:13)
- Loop 2 **Bark_Quercus_alba_Gray_Scaly_Fissures** (system-verified 2026-07-22T00:54:32)
- Loop 3 **Biological_Specificity_Quercus_alba_Bark_Pattern** (system-verified 2026-07-22T00:55:09)
- Loop 4 **Astro_Spiral_Galaxy_Density_Wave_Pattern** (system-verified 2026-07-22T01:01:55)
- Loop 4 **Astro_Ring_Particle_Cassini_Division_Gap** (system-verified 2026-07-22T01:02:01)
- Loop 4 **Astro_Nebula_Emission_H_II_Region** (system-verified 2026-07-22T01:02:07)
- Loop 5 **Geology_Basalt_Hexagonal_Columnar_Jointing** (system-verified 2026-07-22T01:07:06)
- Loop 5 **Geology_Quartz_Crystal_Cluster_Hexagonal** (system-verified 2026-07-22T01:12:42)
- Loop 5 **Geology_Granite_Outcrop_Phaneritic_Interlocking** (system-verified 2026-07-22T01:13:25)

Record verdicts: `python -m core.graphify_record observe --feature X --verdict accepted|rejected --notes "..." --loop N`

## Gardener tend (delegated authority — veto any line by editing its status)
`tend FAILED: 'str' object has no attribute 'get'`

## Rep ledger (resolution through repetition — the dog-sit threshold)
```
[rep] 82 batteries, 914 atoms, 884 reps this pass (11 failing), 28 PIE atoms exported
[rep] failing: subsystem_AErisaid (4 atoms red)
[rep] failing: Any_position-dependent_beat_against_chimeradefault (1 atoms red)
[rep] failing: Substrate_Engine (1 atoms red)
```

## Tonight's distillation
```
clusters >= 3: 77  |  suppressed (covered/pending): 77  |  staged: 0
  covered   [  5x] human_rejection: Verb_Shovel  <- PENDING_HEURISTICS.md
  covered   [  4x] human_rejection: Verb_Look  <- PENDING_HEURISTICS.md
  covered   [  4x] human_rejection: Verb_Bend  <- PENDING_HEURISTICS.md
  covered   [  4x] human_rejection: Verb_PickUp  <- PENDING_HEURISTICS.md
  covered   [  4x] human_rejection: Verb_Drop  <- PENDING_HEURISTICS.md
  covered   [  2x] human_rejection: Verb_Step  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Tool_Weapon_Model  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Ground_Metal_Surface  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Ground_Rock_Surface  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Ground_Sand_Surface  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Ground_Sand_Particles  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Ground_Sand_Footprints  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: audio_visual_sync/telemetry_accessors  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: audio_visual_sync/report_telemetry  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Sky_Starfield  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Sky_Atmosphere_Scattering  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Tool_Scanner_Model  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: Tool_Scanner_Material  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: visual_validation_phenotypic_analysis  <- PENDING_HEURISTICS.md
  covered   [  1x] human_rejection: recombination_genetic_inheritance  <- PENDING_HEURISTICS.md
  covered   [ 27x] sim_rejection: verb_interactions/visor_inspection_pedestal  <- PENDING_HEURISTICS.md
  covered   [ 26x] sim_rejection: verb_interactions/weapon_tool_examine  <- PENDING_HEURISTICS.md
  covered   [ 26x] sim_rejection: verb_interactions/verb_shovel_rock_surface_location  <- PENDING_HEURISTICS.md
  covered   [ 26x] sim_rejection: verb_interactions/verb_shovel_sand_surface_location  <- PENDING_HEURISTICS.md
  covered   [ 23x] sim_rejection: regolith_yard/jump_probe  <- PENDING_HEURISTICS.md
  covered   [ 21x] sim_rejection: verb_interactions/verb_shovel_metal_surface_location  <- PENDING_HEURISTICS.md
  covered   [ 17x] sim_rejection: regolith_yard/walk_rock_to_sand_basin  <- PENDING_HEURISTICS.md
  covered   [ 13x] sim_rejection: regolith_yard/walk_metal_to_rock  <- PENDING_HEURISTICS.md
  covered   [ 10x] sim_rejection: audio_visual_sync/walk_fast_on_sand  <- PENDING_HEURISTICS.md
  covered   [  6x] sim_rejection: audio_visual_sync/walk_slow_on_sand  <- PENDING_HEURISTICS.md
  covered   [  6x] sim_rejection: travel_vehicle_basic/vehicle_component_initialized  <- PENDING_HEURISTICS.md
  covered   [  6x] sim_rejection: edu_spawn/collect_basalt  <- PENDING_HEURISTICS.md
  covered   [  5x] sim_rejection: audio_visual_sync/spawn_and_verify_audio_system  <- PENDING_HEURISTICS.md
  covered   [  5x] sim_rejection: audio_visual_sync/report_telemetry  <- PENDING_HEURISTICS.md
  covered   [  5x] sim_rejection: social_trade/social_trade_npc_proximity  <- PENDING_HEURISTICS.md
  covered   [  5x] sim_rejection: social_trade/social_trade_npc_interact  <- PENDING_HEURISTICS.md
  covered   [  5x] sim_rejection: verb_interactions/verb_pickup_weapon_tool_location  <- PENDING_HEURISTICS.md
  covered   [  4x] sim_rejection: verb_interactions/verb_look_location  <- PENDING_HEURISTICS.md
  covered   [  4x] sim_rejection: gesture_wheel/gesture_wheel_open_close  <- PENDING_HEURISTICS.md
  covered   [  4x] sim_rejection: gesture_wheel/gesture_wheel_commit_gesture  <- PENDING_HEURISTICS.md
  covered   [  4x] sim_rejection: verb_interactions/verb_bend_location  <- PENDING_HEURISTICS.md
  covered   [  4x] sim_rejection: solar_system_stand/stand_on_grown_ocean_world  <- PENDING_HEURISTICS.md
  covered   [  3x] sim_rejection: verb_interactions/verb_drop_location  <- PENDING_HEURISTICS.md
  covered   [  3x] sim_rejection: chimera_complete/generation_transition  <- PENDING_HEURISTICS.md
  covered   [  3x] sim_rejection: regolith_yard/spawn_on_metal_pad  <- PENDING_HEURISTICS.md
  covered   [258x] surprise: beat discovered expected gap  <- PENDING_HEURISTICS.md
  covered   [169x] grade_CF: Build_Pipeline  <- PENDING_HEURISTICS.md
  covered   [131x] compilation_fail  <- PENDING_HEURISTICS.md
  covered   [ 41x] grade_CF: Visual_Verification  <- PENDING_HEURISTICS.md
  covered   [ 36x] pathway: sleepwalker.beat_run -> partial  <- PENDING_HEURISTICS.md
  covered   [ 35x] surprise: correction feature finalized frame  <- PENDING_HEURISTICS.md
  covered   [ 26x] verification_not_verified  <- PENDING_HEURISTICS.md
  covered   [ 26x] surprise: audio_visual_sync beat discovered expected  <- PENDING_HEURISTICS.md
  covered   [ 18x] pathway: build_orchestrator.ue_shutdown -> success_intended_kill  <- PENDING_HEURISTICS.md
  covered   [ 17x] pathway: build_orchestrator.ue_shutdown -> killed_for_build  <- PENDING_HEURISTICS.md
  covered   [ 12x] grade_CF: Player_Character_Lighting  <- PENDING_HEURISTICS.md
  covered   [ 12x] surprise: dyad result turn  <- PENDING_HEURISTICS.md
  covered   [ 11x] grade_CF: X  <- already pending
  covered   [  7x] surprise: research shelter_habitat_lighting waived witness  <- PENDING_HEURISTICS.md
  covered   [  6x] surprise: aerisaidactor candidate expectation score  <- PENDING_HEURISTICS.md
  covered   [  6x] surprise: beat collect_basalt discovered edu_spawn  <- PENDING_HEURISTICS.md
  covered   [  4x] grade_CF: Player_Character_Model  <- PENDING_HEURISTICS.md
  covered   [  4x] surprise: actors bp_verb_ hollow may  <- PENDING_HEURISTICS.md
  covered   [  4x] surprise: bad costless creation ending  <- PENDING_HEURISTICS.md
  covered   [  4x] surprise: bridge dsl fixes mapping  <- PENDING_HEURISTICS.md
  covered   [  4x] surprise: candidate expectation score uweathersubsystem  <- PENDING_HEURISTICS.md
  covered   [  4x] surprise: beat chimera_complete discovered expected  <- PENDING_HEURISTICS.md
  covered   [  4x] surprise: beat discovered expected full_game_loop  <- PENDING_HEURISTICS.md
  covered   [  3x] grade_CF: Ground_Metal_Surface  <- PENDING_HEURISTICS.md
  covered   [  3x] grade_CF: System_Economy  <- PENDING_HEURISTICS.md
  covered   [  3x] pathway: animation_physics.add_anim_notify -> failed  <- PENDING_HEURISTICS.md
  covered   [  3x] elimination_audio_visual_sync/telemetry_accessors  <- PENDING_HEURISTICS.md
  covered   [  3x] surprise: blocker draft dream endpoint  <- PENDING_HEURISTICS.md
  covered   [  3x] surprise: chaos chaos_organ core created  <- PENDING_HEURISTICS.md
  covered   [  3x] surprise: fixes generationsubsystem pipeline research  <- PENDING_HEURISTICS.md
  covered   [  3x] surprise: gate postflight refused shelter_habitat_materials  <- PENDING_HEURISTICS.md
  covered   [  3x] surprise: atom beat_scripts_tautology_fix fix red  <- PENDING_HEURISTICS.md
nothing new to stage — the constitution already covers today's lessons
```

## Compaction preview (dry-run — apply is always manual)
```
live nodes: 3920  |  archivable (>30d, superseded, unreferenced): 0
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
