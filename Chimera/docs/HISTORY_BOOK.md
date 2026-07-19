# THE HISTORY BOOK

> Everything the studio has learned, written down. Regenerated nightly
> by `dream_loop`; full-text search over EVERY entry (this file caps
> chapters at 40 for readability):
> `python -m core.history_book search --query <anything> [--chapter closed-doors]`

**1440 entries** across 8 chapters.

## I. The Constitution (promoted heuristics)

*81 entries; showing 40.*

### H-1
<sub>`claude:H-1`</sub>

> A C2039 missing-member error in ProceduralGenerated/ means template drift — emit the accessor in the same generator change that emits its test.

### H-2
<sub>`claude:H-2`</sub>

> Never verify from desktop screenshots — capture via MCP control_editor screenshot mode=editor_viewport, which renders the viewport regardless of window focus, and (since the 2026-07-13 Slate-widget capture fix, McpAutomationBridge_ControlHandlers.cpp/McpAutomationBridge_UiHandlers.cpp) now also includes composited UMG/Slate HUDs during PIE, cropped to just the viewport — full_editor_window is only needed for whole-editor-chrome captures now, not to see a HUD (docs/MCP_PATHWAYS.md #32).

### H-3
<sub>`claude:H-3`</sub>

> An LM response containing its own reasoning dump ("Here's a thinking process") is a RETRY with a larger token budget, never a verdict — schema-validate before consuming.

### H-7
<sub>`claude:H-7`</sub>

> Record the MCP response's error field, never raw CLI stdout — a DynamicToolManager boot banner inside an "error" means the wrong stream was captured.

### H-13
<sub>`claude:H-13`</sub>

> Economy features repeatedly grade C/F on partial criteria coverage and unmeasured fps; run telemetry foregrounded and test every declared criterion before grading System_Economy.

### H-14
<sub>`claude:H-14`</sub>

> Verified-by-injection is not playable — never stage a feature for observation until real player input drives it end-to-end, read back in PIE.

### H-17
<sub>`claude:H-17`</sub>

> Beat scripts must declare only Sleepwalker-registered actions before playtest dispatch.

### H-19
<sub>`claude:H-19`</sub>

> Before running a rejection sweep, use the most recent simtest for that feature -- an old simtest_id can indict a feature already fixed and re-verified since.

### H-21
<sub>`claude:H-21`</sub>

> A verb needs behavior, not metadata: ATool_Shovel had DigRadius but no Dig() — beats must press the verb key and assert a world-state change.

### H-22
<sub>`claude:H-22`</sub>

> Read back live-PIE pawn components before staging an interaction verb — PickUp's component was never attached, bound, or given a level actor to grab.

### H-24
<sub>`claude:H-24`</sub>

> A feature tagged only by movement beats is hostage to rig health — zero-displacement failures (GameMode PlayerControllerClass unset) indict the rig, not the surface.

### H-25
<sub>`claude:H-25`</sub>

> Position-expect beats must reset_position at beat start — W-drift accumulates across sequential beats and BugItGo is refused during PIE.

### H-28
<sub>`claude:H-28`</sub>

> Probe jumps by timed pawn_z read-back, not log_contains — and reset_position first: z=-26947 shows the pawn had already drifted off the world.

### H-29
<sub>`claude:H-29`</sub>

> Compound beats fail for shifting root causes (frozen input, then missing SandDrift_FX) — attribute rejection to the failing expect's subsystem, not every tagged feature.

### H-30
<sub>`claude:H-30`</sub>

> Expects are schema-bound like actions — unknown expects (screenshot_taken, unreadable controller properties) fail beats at runtime; validate the expect vocabulary at dispatch.

### H-31
<sub>`claude:H-31`</sub>

> Telemetry commands that fall back to hardcoded defaults indicate missing component integration at runtime (UComponent not attached, or not populating properties at BeginPlay) — verify component attachment in character blueprint and initialization order before blaming MCP action handlers.

### H-32
<sub>`claude:H-32`</sub>

> When telemetry queries return hardcoded defaults (count=0, latency=999), the beat's expectations fail not because of beat schema but because the backend component isn't populating data — verify SandSoundComponent attachment and footstep event tracking at runtime before debugging beat expectations.

### H-33
<sub>`claude:H-33`</sub>

> Investigate audio_visual_sync report_telemetry; verify test harness and beat reg

### H-34
<sub>`claude:H-34`</sub>

> Verify required components and assets are spawned and registered.

### H-35
<sub>`claude:H-35`</sub>

> Investigate elimination_audio_visual_sync telemetry_accessors; verify test harne

### H-36
<sub>`claude:H-36`</sub>

> Implement missing input bindings and verify actor registration.

### H-37
<sub>`claude:H-37`</sub>

> Verify beat spawn location distances and pawn navigation constraints.

### H-38
<sub>`claude:H-38`</sub>

> Investigate correction feature; verify test harness and beat registration.

### H-40
<sub>`claude:H-40`</sub>

> Investigate actors bp_verb_; verify test harness and beat registration.

### H-41
<sub>`claude:H-41`</sub>

> Investigate bad costless; verify test harness and beat registration.

### H-42
<sub>`claude:H-42`</sub>

> Investigate blocker draft; verify test harness and beat registration.

### H-43
<sub>`claude:H-43`</sub>

> Investigate chaos chaos_organ; verify test harness and beat registration.

### H-44
<sub>`claude:H-44`</sub>

> Investigate fixes generationsubsystem; verify test harness and beat registration

### H-45
<sub>`claude:H-45`</sub>

> Investigate bridge dsl; verify test harness and beat registration.

### H-46
<sub>`claude:H-46`</sub>

> Investigate human_rejection sky_starfield; verify test harness and beat registra

### H-47
<sub>`claude:H-47`</sub>

> Investigate human_rejection sky_atmosphere_scattering; verify test harness and b

### H-51
<sub>`claude:H-51`</sub>

> Implement screenshot action and state-capture in sleepwalker beat registry.

### H-54
<sub>`claude:H-54`</sub>

> Verify event logging and signal traces on success path.

### H-58
<sub>`claude:H-58`</sub>

> Verify correct pawn class and rig bindings on initialization.

### compilation_fail `2026-07-07T01:45`
<sub>`heuristic_837905aa7e86de78`</sub>

> A C2039 missing-member error in ProceduralGenerated/ means template drift — emit the accessor in the same generator change that emits its test.

### grade_CF: Visual_Verification `2026-07-07T01:45`
<sub>`heuristic_ba0b31439f9de388`</sub>

> Never verify from desktop screenshots — capture via MCP control_editor screenshot mode=editor_viewport, which renders the viewport regardless of window focus.

### verification_not_verified `2026-07-07T01:45`
<sub>`heuristic_bc4050e6a87ef5aa`</sub>

> An LM response containing its own reasoning dump ("Here's a thinking process") is a RETRY with a larger token budget, never a verdict — schema-validate before consuming.

### ralph_apply_<feature>_step `2026-07-07T01:45`
<sub>`heuristic_58e592d099d13f3c`</sub>

> Record the MCP response's error field, never raw CLI stdout — a DynamicToolManager boot banner inside an "error" means the wrong stream was captured.

### pathway: build_orchestrator.ue_shutdown -> killed_for_build `2026-07-07T01:45`
<sub>`heuristic_3718f256a2152296`</sub>

> killed_for_build is the build lifecycle working as designed, not a pathway failure — record intended shutdowns as success with a note, or routine builds pollute the failure ledger.

### grade_CF: System_Economy `2026-07-07T01:45`
<sub>`heuristic_a205a08f1a755211`</sub>

> Economy features repeatedly grade C/F on partial criteria coverage and unmeasured fps; run telemetry foregrounded and test every declared criterion before grading System_Economy.

## II. Closed Doors (eliminations — proven negatives)

*14 entries; showing 14.*

### audio_visual_sync/telemetry_accessors: NOT MCP action handlers / command dispatch as root cause `2026-07-12T16:21`
<sub>`elim_65f84a195c149377`</sub>

> NOT: MCP action handlers / command dispatch as root cause
> observed: handlers verified working; telemetry still returned defaults
> eliminates: hypothesis: McpAutomationBridge HandleAction broken
> SURVIVES (the narrowed search space): hypothesis: SandSoundComponent never attached at runtime
> evidence: H-31 lineage, sim_av_sync_test 2026-07-11

### audio_visual_sync/telemetry_accessors: NOT beat expect schema as root cause `2026-07-12T16:21`
<sub>`elim_71b935361cee2319`</sub>

> NOT: beat expect schema as root cause
> observed: all expects schema-valid after H-30 validation; failures persisted
> eliminates: hypothesis: beat scripts malformed
> SURVIVES (the narrowed search space): hypothesis: backend component not populating at BeginPlay
> evidence: H-32 lineage, sim_av_sync_test 2026-07-11

### audio_visual_sync/report_telemetry: NOT hardcoded fallback sentinels masking absent backend data `2026-07-12T16:21`
<sub>`elim_b39ca7951a8cd8f8`</sub>

> NOT: hardcoded fallback sentinels masking absent backend data
> observed: count=0, latency=999 defaults where live data should be
> eliminates: hypothesis: telemetry pipeline healthy
> SURVIVES (the narrowed search space): hypothesis: component attachment (CONFIRMED by rep atom, red on first pass)
> evidence: H-31/H-34, rep_engine first pass 2026-07-12

### audio_visual_sync/telemetry_accessors: NOT beat schema or MCP dispatch as root cause `2026-07-12T16:24`
<sub>`elim_043bb7affad30ff4`</sub>

> NOT: beat schema or MCP dispatch as root cause
> observed: 
> eliminates: 
> SURVIVES (the narrowed search space): 
> evidence: H-31/H-32 lineage + rep atom evidence 2026-07-12

### System_DSL_Fidelity: NOT probe token-noise as the dominant cause of DSL battery reds `2026-07-12T16:48`
<sub>`elim_5db874e721a6c962`</sub>

> NOT: probe token-noise as the dominant cause of DSL battery reds
> observed: v1 probe (literal snake, ProceduralGenerated-only) produced 13 false reds of 145; camel-aware Source-wide v2 probe leaves 136 reds standing
> eliminates: hypothesis: DSL battery reds are mostly regex artifacts
> SURVIVES (the narrowed search space): fact: generator coverage of declared spec is ~19% — 136 unkept promises, ledgered in docs/rep_batteries/dsl_drift.json
> evidence: rep ledger System_DSL_Fidelity 962 reps + triage 2026-07-12

### System_DSL_Fidelity: NOT probe token-noise as dominant cause of battery reds `2026-07-12T16:52`
<sub>`elim_fc1e3b5e9ce65fbe`</sub>

> NOT: probe token-noise as dominant cause of battery reds
> observed: 
> eliminates: 
> SURVIVES (the narrowed search space): 
> evidence: triage 2026-07-12 + rep ledger 962 reps

### Verb_Step: NOT audio volume-scaling as the walk_fast_on_sand failure cause `2026-07-12T17:25`
<sub>`elim_b58535a07e3675b0`</sub>

> NOT: audio volume-scaling as the walk_fast_on_sand failure cause
> observed: beat RAN (no Shift block) but GetVolumeScalesWithSpeed()==false: all samples landed in the slow bucket
> eliminates: hypothesis: SandSoundComponent telemetry/accessors broken (they returned live, honest data)
> SURVIVES (the narrowed search space): sprint input (Shift modifier) never raises pawn speed >= 300 cm/s bucket threshold — the input rig, not the audio
> evidence: simtest_536c81002961d807 post_h34_ubt_green 2026-07-12

### Sprint_Input/harness_parity: NOT bridge LShift-vs-LeftShift mismatch as a live blocker `2026-07-12T17:38`
<sub>`elim_e1ceb1b092b179af`</sub>

> NOT: bridge LShift-vs-LeftShift mismatch as a live blocker
> observed: 
> eliminates: 
> SURVIVES (the narrowed search space): 
> evidence: birth atom green, rep ledger 2026-07-12

### Malcolm_Envelope: NOT heuristics_per_night breach as a real leak `2026-07-12T17:55`
<sub>`elim_58026efcf3adc442`</sub>

> NOT: heuristics_per_night breach as a real leak
> observed: 
> eliminates: 
> SURVIVES (the narrowed search space): 
> evidence: census error, rejection-lineage records excluded, surprise_17fda10a5eba4cf3

### Sprint_Input/capture_peak: NOT last-footstep volume as a valid sprint measurement `2026-07-12T18:39`
<sub>`elim_1b283361406a25a0`</sub>

> NOT: last-footstep volume as a valid sprint measurement
> observed: post-key_up captures read the deceleration tail (0.431 @ 517cm/s) while the pawn provably sprinted 2800uu
> eliminates: hypothesis: sprint state/binding/normalizer broken (all confirmed working by UE log + distance)
> SURVIVES (the narrowed search space): rule: capture PEAKS for hold-verbs; instantaneous 'last' samples race the release
> evidence: simtest_9aac4a49214915ad -> fixed in simtest_2d3122d6cefb0009

### System_SaveGame: NOT SaveGame UPROPERTY fields as dead metadata (used-in-cpp atom false pos `2026-07-12T22:26`
<sub>`elim_8f4f3dbdf1bd7e24`</sub>

> NOT: SaveGame UPROPERTY fields as dead metadata (used-in-cpp atom false positives)
> observed: 12 of 13 System_SaveGame reds were UPROPERTY(SaveGame) data/BP fields in ChimeraSaveGame/InheritanceData — serialized, not .cpp-referenced by design
> eliminates: hypothesis: SaveGame struct fields are dead metadata needing .cpp use
> SURVIVES (the narrowed search space): rule: SaveGame-flagged UPROPERTYs are data; gen_code_reflection now skips them, so red means real
> evidence: rep prune System_SaveGame 40->15 atoms, 13 red -> 1 real (H-34)

### Substrate_Terrain: NOT Coarse free-sphere MuJoCo grain physics (ATOM_PITCH ~0.167m macro-part `2026-07-18T07:38`
<sub>`elim_06e43126d4d0332f`</sub>

> NOT: Coarse free-sphere MuJoCo grain physics (ATOM_PITCH ~0.167m macro-particles standing in for 0.07mm regolith grains, GA_Dig's own dig footprint replicated verbatim from CHIMERA_VISION.py, mu=tan(35deg) sand friction from matter_library.json) cannot re-coalesce a dig event back into a seamless heightfield within the current recoalesce algorithm (per-cell mass summing, no blend pass).
> observed: Committed run (core/terrain_matter.py, commit e794f1a, seed=11): cycle1 n_freed=225 n_exited=57 (25.3%) seam_max=0.4000m (bar 0.333m) mass_drift=-4.86%; cycle2 n_freed=225 n_exited=50 (22.2%) seam_max=0.4000m mass_drift=-7.12%; mean_ms/step=0.31 vs frame wall 16.6ms (held, >50x headroom); settled_within_budget=False both cycles (2000-step/10s cap hit). INDEPENDENTLY REPRODUCED by sub-28 in a burned membrane (2026-07-18, same seed): cycle1 n_exited=60 (26.7%) seam_max=0.4000m mass_drift=-4.69%; cycle2 n_exited=47 (20.9%) seam_max=0.4000m mass_drift=-8.51%; verdict KILL both the original and the reproduction run. Render (Saved/TerrainMatter/shovel_test_strip.png) visually confirms: the after-recoalesced frames show a persistent raised, jagged bright ridge at the dig site that never blends into the flat surrounding patch.
> eliminates: free-sphere DEM macro-particles at this ATOM_PITCH recoalesce seamlessly into the coarse heightfield without an explicit smoothing/blend pass across the fracture boundary; the current rolling/torsional friction tuning (mu*0.2 / mu*0.4) lets a 225-grain GA_Dig-sized event reach the quiet-hold threshold within a 10s/2000-step settle budget
> SURVIVES (the narrowed search space): frame budget is NOT the blocker -- 0.31ms/step vs a 16.6ms wall holds over 50x headroom, so landscaping-as-matter is not killed by compute cost, only by the seam/settle algorithm; cohesive bonding (matter_library sand cohesion_kpa=0.5+/-0.4, not modelled this rung -- MuJoCo stock contact is frictional-only) or an explicit post-recoalesce smoothing pass across the seam boundary might close the 0.4m gap -- untested, named as the next rung; a larger settle budget or a retuned velocity-quiet threshold might let grains settle in-budget without necessarily changing the seam outcome -- untested
> evidence: 

### Substrate_Terrain: NOT free-sphere DEM macro-particles at ATOM_PITCH~0.167m recoalesce seamle `2026-07-18T07:42`
<sub>`elim_d7f65379cd4984b1`</sub>

> NOT: free-sphere DEM macro-particles at ATOM_PITCH~0.167m recoalesce seamlessly into the heightfield without an explicit blend pass, AND the current friction tuning lets a 225-grain GA_Dig-sized event settle within a 10s/2000-step budget
> observed: 
> eliminates: 
> SURVIVES (the narrowed search space): 
> evidence: elim_06e43126d4d0332f (+ independent membrane reproduction, this session)

### witness_rig: NOT The witness anchor (0,0,130) must never sit inside colliding geometry: `2026-07-18T22:47`
<sub>`elim_41064db78ef9a045`</sub>

> NOT: The witness anchor (0,0,130) must never sit inside colliding geometry: SM_StarSphere (2km-radius colliding shell centered at origin, unowned - zero repo references) was THE levitator behind tb-0189/tb-0184/tb-0196 - CharacterMovement penetration-resolves possessed pawns upward every move tick (unpossessed pawns never move, hence the possession discriminator; per-tick pushout, hence dt-proportional rates; fixed verify window, hence deterministic z~3085)
> observed: 
> eliminates: 
> SURVIVES (the narrowed search space): 4/4 causal matrix same boot: sphere present = climb (simtest_140a70674941d472, simtest_ae7dc6dd3cca28a9 - the latter WITH root-collision stripped, proving editor-runtime SetCollisionEnabled does not survive into PIE duplication), sphere destroyed = clean walk (simtest_6ba72f3a8f193188, simtest_4ea739ba22ed2aaa - the latter with all wiring actors present, exonerating them). Durable fix: sphere deleted from chimeradefaultlevel and level SAVED
> evidence: 

## III. Surprises (expectation vs reality)

*519 entries; showing 40.*

### First live spiral_forks run on Ground_Sand_Particles `2026-07-06T15:42`
<sub>`surprise_204ae52a13d1dea9`</sub>

> context: First live spiral_forks run on Ground_Sand_Particles
> expected: 3 research briefs generated via LM Studio
> reality: All 3 forks died: qwen3.6 thinking-mode consumed the 1600-token budget, no JSON in content field - the exact H-3 lesson repeating live
> lesson hint: H-3 confirmed: schema-validate LM output, /no_think + larger budget + check reasoning_content [engine]

### P2 citation verification attempt via WebSearch during Ground_Sand_Particles rese `2026-07-06T16:00`
<sub>`surprise_20b9411526ef0209`</sub>

> context: P2 citation verification attempt via WebSearch during Ground_Sand_Particles research
> expected: WebSearch verifies whether NASA TR 1967-304 exists
> reality: WebSearch itself fails with deepseek-v4-flash routing error - the ANTHROPIC_* env poisoning breaks subagents, the permission classifier, AND WebSearch (wider blast radius than P3 declared)
> lesson hint: P3 undersold: the env vars break every model-dependent harness tool, not just future-session startup [engine]

### Niagara authoring via manage_effect for Ground_Sand_Particles `2026-07-06T16:05`
<sub>`surprise_32206520902943bf`</sub>

> context: Niagara authoring via manage_effect for Ground_Sand_Particles
> expected: add_emitter_to_system + 5 module adds (all success:true, validate isValid) produce a rendering emitter
> reality: get_niagara_info reports emitterCount=0 and viewport shows zero particles - every authoring call succeeded onto an empty system
> lesson hint: manage_effect authoring responses are facades; trust get_niagara_info emitterCount + viewport render, never per-call success flags [engine]

### Niagara render debugging for Ground_Sand_Particles `2026-07-06T16:09`
<sub>`surprise_71189195f7cf3156`</sub>

> context: Niagara render debugging for Ground_Sand_Particles
> expected: Empty viewport meant the authored system/control were empty facades
> reality: Background-throttled editor froze ALL Niagara simulation - foregrounded at 120fps the stock FountainLightweight renders a full particle column; earlier empty frames measured a frozen editor, not empty systems
> lesson hint: Simulation-dependent verification (particles/anims) requires foregrounded editor + realtime viewport BEFORE trusting an empty frame - generalizes the Loop 8 background-throttle fps trap [engine]

### Observation Collapse intake design - per-feature verdict queue (20 entries) awai `2026-07-06T19:02`
<sub>`surprise_af9753abad6be2c4`</sub>

> context: Observation Collapse intake design - per-feature verdict queue (20 entries) awaiting the human
> expected: Human records observe --feature X --verdict per feature
> reality: The observer's actual nature: observation happens during PLAYTESTING as a few sentences describing the ENTIRE experience - the overall temperature of the game, boiled down to a few tokens. The AI must attribute that holistic signal to features itself - guess on intentions, but now it has the information
> lesson hint: Holistic temperature + agent attribution with quoted provenance, three tiers: directly-implicated / exercised-but-unmentioned (tacit) / not-exercised (stays queued). Every attribution reversible by one human sentence [human]

### Footprints study guide hinge add_anim_notify: expected risk was facade #3 (fake  `2026-07-06T19:43`
<sub>`surprise_3ddd345289e269b4`</sub>

> context: Footprints study guide hinge add_anim_notify: expected risk was facade #3 (fake success:true that only read-back would catch)
> expected: 
> reality: Bridge returns honest NOT_IMPLEMENTED for add_anim_notify AND get_anim_sequence_info - the actions do not exist; failure mode is absence, not facade; read-back tool itself is also missing
> lesson hint:  [agent]

### Assumed generated DeepSpaceTraderGameMode governed chimeradefaultlevel PIE (per  `2026-07-07T00:01`
<sub>`surprise_3503c5554337bc32`</sub>

> context: Assumed generated DeepSpaceTraderGameMode governed chimeradefaultlevel PIE (per C++ audit inference)
> expected: 
> reality: WorldSettings.DefaultGameMode was null - the generated GameMode never ran in this map; double-ship bug was latent, not live. Set explicitly to GameModeBase for Session A.
> lesson hint:  [agent]

### Human observation of system-finalized feature 'Verb_Step' `2026-07-07T00:07`
<sub>`surprise_8f2156a52fee6dee`</sub>

> context: Human observation of system-finalized feature 'Verb_Step'
> expected: system verification (rubric grade) matches human judgment
> reality: I have no ability to move my character
> lesson hint: frame-level correction: what the machine measured is not what the human sees [human]

### Expected possessed BP_Astronaut_Character to be walkable in PIE (16 on-foot feat `2026-07-07T00:07`
<sub>`surprise_2b3d79676e3d4206`</sub>

> context: Expected possessed BP_Astronaut_Character to be walkable in PIE (16 on-foot features verified across loops 0-2)
> expected: 
> reality: BP has ZERO input wiring (strings scan: no IA_/IMC_/AddMappingContext refs; parent bare /Script/Engine.Character). Bridge cannot author BP graphs, so it never existed; all prior locomotion evidence was CharMoveComp velocity injection - proxy evidence, never player-reachable
> lesson hint:  [human]

### Sleepwalker expected beat 'jump_probe' to be reachable (regolith_yard) `2026-07-07T00:47`
<sub>`surprise_561ad640d61383db`</sub>

> context: Sleepwalker expected beat 'jump_probe' to be reachable (regolith_yard)
> expected: 
> reality: failed: {"expect": {"log_contains": "[DEMOBEAT]"}, "ok": false, "note": "log_hit=False"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### SLEEPWALKER_DESIGN guard test: expected observe-without-derived-from to be techn `2026-07-07T00:49`
<sub>`surprise_1451fd0fc19c66f3`</sub>

> context: SLEEPWALKER_DESIGN guard test: expected observe-without-derived-from to be technically rejected for agents
> expected: 
> reality: It succeeded and flipped Verb_Step to observed - the human-provenance guard is procedural only (CLI cannot know who types). Test artifacts purged; env-sentinel guard added (CHIMERA_AGENT_SIM=1 rejects direct observe). Stronger rule needs Gardener decision.
> lesson hint: direct observe is an honor-system surface; automation processes must set CHIMERA_AGENT_SIM [agent]

### Constitution: every heuristic waited on the human Gardener; 14 pendings suppress `2026-07-07T01:45`
<sub>`surprise_972f134950fbb734`</sub>

> context: Constitution: every heuristic waited on the human Gardener; 14 pendings suppressed ALL distiller output
> expected: 
> reality: Gardener authority DELEGATED to automation (human directive 2026-07-07): core/gardener.py auto-rules pendings (doc-organs self-promote, gate-organs queue for capable implementation, subsumed tombstone); human keeps veto-after (edit status to vetoed -> demoted) and playtests at will
> lesson hint:  [human]

### H-2 prohibition: Never verify from desktop screenshots — capture via MCP control `2026-07-07T04:32`
<sub>`surprise_f5f2b789f3768800`</sub>

> context: H-2 prohibition: Never verify from desktop screenshots — capture via MCP control_editor screenshot mode=editor_viewport
> expected: 
> reality: Successfully replaced all pyautogui.screenshot() usages with MCP control_editor screenshot mode=editor_viewport in visual_verifier.py, ralph_loop_harness.py, and verification_studio_runner.py
> lesson hint:  [agent]

### Novel blocker: editor viewport renders black after level load `2026-07-07T06:21`
<sub>`surprise_4791e25a3101c831`</sub>

> context: Novel blocker: editor viewport renders black after level load
> expected: 
> reality: Solver drafted a fix plan (confidence 0.3); steps executed: 0
> lesson hint: solver draft in task_progress — dream fodder for a recipe [agent]

### Duty agent in continuous-operation drift: skipped bookends as ceremonial, idled  `2026-07-07T06:36`
<sub>`surprise_f436d226e166d785`</sub>

> context: Duty agent in continuous-operation drift: skipped bookends as ceremonial, idled on re-verification (preflight/unblock/doc_audit loops on a clean system), rewrote a solver draft in task_progress, and described a failed-and-reverted bridge repair as fix-in-place
> expected: 
> reality: Human surfaced the transcript. ANTI-IDLE LAWS added to CYCLE_PROMPT (one item then close; FRESHLY VERIFIED = dead work; bookends never waived; NEXT items protected; reverted attempt = failure). rehearsal freshness cooldown demotes repeat verification mechanically.
> lesson hint:  [human]

### Sleepwalker expected beat 'verb_look_360' to be reachable (verb_interactions) `2026-07-07T07:12`
<sub>`surprise_f732e4e5178a9cc4`</sub>

> context: Sleepwalker expected beat 'verb_look_360' to be reachable (verb_interactions)
> expected: 
> reality: blocked: {"error": "unknown action {'camera_yaw_rotate': 360}"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_bend_trigger' to be reachable (verb_interactions `2026-07-07T07:12`
<sub>`surprise_bd61a47547bc4f90`</sub>

> context: Sleepwalker expected beat 'verb_bend_trigger' to be reachable (verb_interactions)
> expected: 
> reality: blocked: {"error": "unknown action {'simulate_input': {'type': 'key_down', 'key': 'E'}}"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_pickup_weapon_tool' to be reachable (verb_intera `2026-07-07T07:12`
<sub>`surprise_22575007835ae5b4`</sub>

> context: Sleepwalker expected beat 'verb_pickup_weapon_tool' to be reachable (verb_interactions)
> expected: 
> reality: blocked: {"error": "unknown action {'move_to': {'x': 400, 'y': -400, 'z': 50}}"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_drop_item' to be reachable (verb_interactions) `2026-07-07T07:12`
<sub>`surprise_4723e5cef53ef4cf`</sub>

> context: Sleepwalker expected beat 'verb_drop_item' to be reachable (verb_interactions)
> expected: 
> reality: blocked: {"error": "unknown action {'simulate_input': {'type': 'key_down', 'key': 'Q'}}"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_shovel_metal_surface' to be reachable (verb_inte `2026-07-07T07:12`
<sub>`surprise_d0db022ba909e608`</sub>

> context: Sleepwalker expected beat 'verb_shovel_metal_surface' to be reachable (verb_interactions)
> expected: 
> reality: blocked: {"error": "unknown action {'move_to': {'x': 0, 'y': 0, 'z': 0}}"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_shovel_rock_surface' to be reachable (verb_inter `2026-07-07T07:12`
<sub>`surprise_717d27a484955a65`</sub>

> context: Sleepwalker expected beat 'verb_shovel_rock_surface' to be reachable (verb_interactions)
> expected: 
> reality: blocked: {"error": "unknown action {'move_to': {'x': 2000, 'y': 0, 'z': 0}}"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_shovel_sand_surface' to be reachable (verb_inter `2026-07-07T07:12`
<sub>`surprise_b6864047f6143dfc`</sub>

> context: Sleepwalker expected beat 'verb_shovel_sand_surface' to be reachable (verb_interactions)
> expected: 
> reality: blocked: {"error": "unknown action {'move_to': {'x': 4000, 'y': 0, 'z': 0}}"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'visor_inspection_pedestal' to be reachable (verb_inte `2026-07-07T07:12`
<sub>`surprise_a03f87954817bb5c`</sub>

> context: Sleepwalker expected beat 'visor_inspection_pedestal' to be reachable (verb_interactions)
> expected: 
> reality: blocked: {"error": "unknown action {'move_to': {'x': 600, 'y': 600, 'z': 120}}"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'weapon_tool_examine' to be reachable (verb_interactio `2026-07-07T07:12`
<sub>`surprise_8afbbfe69a873427`</sub>

> context: Sleepwalker expected beat 'weapon_tool_examine' to be reachable (verb_interactions)
> expected: 
> reality: blocked: {"error": "unknown action {'move_to': {'x': 400, 'y': -400, 'z': 50}}"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_look_location' to be reachable (verb_interaction `2026-07-07T07:13`
<sub>`surprise_4ca916118ba86493`</sub>

> context: Sleepwalker expected beat 'verb_look_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"screenshot_taken": "verb_look_360_view"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_bend_location' to be reachable (verb_interaction `2026-07-07T07:13`
<sub>`surprise_7b6ab8193c62e8a2`</sub>

> context: Sleepwalker expected beat 'verb_bend_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_pickup_weapon_tool_location' to be reachable (ve `2026-07-07T07:13`
<sub>`surprise_f8dd0e516ef4553a`</sub>

> context: Sleepwalker expected beat 'verb_pickup_weapon_tool_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"screenshot_taken": "verb_pickup_weapon_tool_view"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_drop_location' to be reachable (verb_interaction `2026-07-07T07:13`
<sub>`surprise_fa05843845be6fe7`</sub>

> context: Sleepwalker expected beat 'verb_drop_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_shovel_metal_surface_location' to be reachable ( `2026-07-07T07:13`
<sub>`surprise_35b021b4eb279dce`</sub>

> context: Sleepwalker expected beat 'verb_shovel_metal_surface_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"screenshot_taken": "verb_shovel_metal_view"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_shovel_rock_surface_location' to be reachable (v `2026-07-07T07:13`
<sub>`surprise_70650f765fecef2c`</sub>

> context: Sleepwalker expected beat 'verb_shovel_rock_surface_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"screenshot_taken": "verb_shovel_rock_view"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_shovel_sand_surface_location' to be reachable (v `2026-07-07T07:13`
<sub>`surprise_0f6a24638dbf6622`</sub>

> context: Sleepwalker expected beat 'verb_shovel_sand_surface_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"actor_exists": "SandDrift_FX"}, "ok": false, "note": "present=False"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'visor_inspection_pedestal' to be reachable (verb_inte `2026-07-07T07:13`
<sub>`surprise_2bfb8bb8f4312a59`</sub>

> context: Sleepwalker expected beat 'visor_inspection_pedestal' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"screenshot_taken": "visor_inspection_pedestal"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'weapon_tool_examine' to be reachable (verb_interactio `2026-07-07T07:13`
<sub>`surprise_45ac1f83e97fba3c`</sub>

> context: Sleepwalker expected beat 'weapon_tool_examine' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"screenshot_taken": "weapon_tool_examine"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_look_location' to be reachable (verb_interaction `2026-07-07T07:25`
<sub>`surprise_0fcb29cbaf318278`</sub>

> context: Sleepwalker expected beat 'verb_look_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_bend_location' to be reachable (verb_interaction `2026-07-07T07:25`
<sub>`surprise_933952dd4f1a0160`</sub>

> context: Sleepwalker expected beat 'verb_bend_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_pickup_weapon_tool_location' to be reachable (ve `2026-07-07T07:25`
<sub>`surprise_05cef877d3fb129a`</sub>

> context: Sleepwalker expected beat 'verb_pickup_weapon_tool_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_drop_location' to be reachable (verb_interaction `2026-07-07T07:25`
<sub>`surprise_5f82311e3820d496`</sub>

> context: Sleepwalker expected beat 'verb_drop_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_shovel_metal_surface_location' to be reachable ( `2026-07-07T07:25`
<sub>`surprise_c1966512f66d8a08`</sub>

> context: Sleepwalker expected beat 'verb_shovel_metal_surface_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"pawn_within": {"x": 0, "y": 0, "r": 600}}, "ok": false, "note": "dist=3600uu (loc x=3600.0008583068848, y=0)"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_shovel_rock_surface_location' to be reachable (v `2026-07-07T07:25`
<sub>`surprise_06c076d65aea17fc`</sub>

> context: Sleepwalker expected beat 'verb_shovel_rock_surface_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"pawn_within": {"x": 2000, "y": 0, "r": 900}}, "ok": false, "note": "dist=5601uu (loc x=7600.763583183289, y=0)"}
> lesson hint: sim-discovered gap; verify before human session [agent]

### Sleepwalker expected beat 'verb_shovel_sand_surface_location' to be reachable (v `2026-07-07T07:25`
<sub>`surprise_e612fb523bc4cb5a`</sub>

> context: Sleepwalker expected beat 'verb_shovel_sand_surface_location' to be reachable (verb_interactions)
> expected: 
> reality: failed: {"expect": {"actor_exists": "SandDrift_FX"}, "ok": false, "note": "present=False"}
> lesson hint: sim-discovered gap; verify before human session [agent]

## IV. Verdicts & Grades

*355 entries; showing 40.*

### Test_Feature: grade A `2026-07-03T22:01`
<sub>`professor_grade_194f6be1dc1b74ec`</sub>

> Test grade

### Loop_4_Tools_Expanded: grade A `2026-07-04T02:28`
<sub>`professor_grade_9da1c1319e880576`</sub>

> The summary demonstrates exceptional technical precision with well-defined PBR parameters, accurate dimensional scaling, and clear alignment with Art, Engineering, and Unreal Engine Craft methodologies, fully satisfying all research requirements.

### Travel_Walking: grade A `2026-07-04T03:16`
<sub>`professor_grade_f4fa95fd0c69ab19`</sub>

> The submission demonstrates exceptional research depth, precise parameter extraction from credible EVA and lunar locomotion sources, seamless integration of UE5 implementation standards, and strict adherence to engineering constraints and emotional safety guidelines.

### Ground_Sand_Sound: grade A `2026-07-04T03:21`
<sub>`professor_grade_07fdf2b5e86aa60f`</sub>

> 
> 
> A This specification earns an A for its rigorous integration of NASA acoustic research, precise UE5 implementation parameters, and a compelling emotional audio framework that effectively bridges sci

### Ground_Metal_Surface: grade C `2026-07-04T04:27`
<sub>`prof_grade_73b132f72683a4d3`</sub>

> Here's a thinking process:
> 
> 1.  **Analyze User Input:**
>    - The user provided a "RESEARCH SUMMARY FOR FEATURE: Ground_Metal_Surface" that looks like a draft/thinking process rather than a complete, structured output. It contains steps (1-4), some drafted parameters, references, and schools, but it's not in the requested JSON format. Wait, the prompt says "Please review this research summary and a

### Ground_Metal_Surface: grade C `2026-07-04T04:29`
<sub>`prof_grade_6f1def660833e414`</sub>

> Here's a thinking process:
> 
> 1.  **Analyze User Input:**
>    - The user provided a "RESEARCH SUMMARY FOR FEATURE: Ground_Metal_Surface" which appears to be an internal thought process/analysis rather than the final output they want me to grade. Wait, the prompt says "Please review this research summary and assign a grade...". The text provided is actually the *thinking process* of an AI or analyst, 

### Ground_Metal_Surface: grade C `2026-07-04T04:30`
<sub>`prof_grade_69ce58e03c7f5ac8`</sub>

> [reasoning sentence]
> 
> 2.  **Evaluate against Criteria:**
>    - *Specific technical parameters:* The draft includes dimensions `[10.0, 10.0, 0.4]`, colors `[172, 178, 185]`, materials with baseColor, roughness (0.45), metallic (0.92), positions `{x:0,y:0,z:0}`, intensities `[1.0, 0.85]`. These are specific and match UE5 PBR workflows.
>    - *Real-world references:* The draft mentions "Weathered steel

### Ground_Rock_Surface: grade C `2026-07-04T04:30`
<sub>`prof_grade_bec71f9e63043118`</sub>

> [reasoning sentence]
> 
> 2.  **Evaluate the Input against Criteria:**
>    - *Completeness:* The input is structured as a "thinking process" and draft JSON, but it's incomplete (cuts off at `"`). It lacks a final polished output, but contains parameters, references, schools, dimensions, colors, materials, positions.
>    - *Technical Parameters:* Provides dimensions (2048x2048x300mm), colors ([38, 40, 42

### Ground_Sand_Surface: grade C `2026-07-04T04:30`
<sub>`prof_grade_aeb4f8f54f636fdb`</sub>

> [reasoning sentence].
> 
> 2.  **Evaluate against Criteria:**
>    - *Specific technical parameters:* The draft includes dimensions (tileSizeX, tileSizeY, thickness), colors ([R,G,B]), materials ({baseColor, roughness, metallic}), positions ({x,y,z}), and intensities ({normalMapStrength, emissionIntensity, lightmapScale}). These are specific and match the requested structure.
>    - *Real-world references

### Ground_Sand_Surface: grade C `2026-07-04T04:31`
<sub>`prof_grade_ab1739bd8cefcb3a`</sub>

> Here's a thinking process:
> 
> 1.  **Analyze User Input:**
>    - The user provided a "RESEARCH SUMMARY FOR FEATURE: Ground_Sand_Surface" which appears to be an internal thought process/analysis for generating JSON parameters for a game asset (UE5 deep-space trading game).
>    - It includes steps for analyzing requirements, deconstructing the `parameters` object structure, and determining realistic valu

### Player_Character_Model: grade C `2026-07-04T04:31`
<sub>`prof_grade_5b0c3fa2dca3572f`</sub>

> [reasoning sentence].
> 
> 2.  **Evaluate against Criteria:**
>    - *Specific Technical Parameters:* The input provides dimensions (180cm/185cm height, width/depth), colors (RGB values like [50, 50, 55] and [240, 100, 20]), materials (roughness/metallic PBR values for suit base and visor), positions (root bone {x,y,z}, head center {x,y,z}), intensities (emissive intensity 2.5). These are specific and r

### Player_Character_Model: grade C `2026-07-04T04:32`
<sub>`prof_grade_629a04ca3e067c51`</sub>

> Here's a thinking process:
> 
> 1.  **Analyze User Input:**
>    - The user provided a "RESEARCH SUMMARY FOR FEATURE: Player_Character_Model"
>    - It includes a thinking process, description draft, parameters draft, references draft, schools draft, and a JSON structure outline.
>    - However, the actual output is incomplete. It cuts off at `  "parameters":` without providing the full JSON or completing t

### Player_Character_Model: grade C `2026-07-04T04:32`
<sub>`prof_grade_2e63165139491b63`</sub>

> [reasoning sentence]
> 
> 2.  **Evaluate against Criteria:**
>    - *Specific technical parameters:* The summary provides dimensions (height, width), colors (RGB values), materials (baseColor, roughness, metallic for suit fabric, armor plating, visor), positions (root, head, backpack), and intensities (suit lights intensity). These are specific and well-structured.
>    - *Real-world references:* Mentions

### Player_Character_Suit: grade C `2026-07-04T04:35`
<sub>`prof_grade_f38f94e79e174041`</sub>

> [reasoning sentence]
> 
> 2.  **Evaluate the Input against Criteria:**
>    - *Completeness:* The input is cut off mid-sentence in the parameters section (`1.  \`Helmet_Assembly\`: Position {x:0, y`). It doesn't contain a complete JSON structure or fully fleshed-out parameters.
>    - *Technical Parameters:* Mentions colors and materials conceptually but lacks concrete, fully specified data for all compon

### Verb_Shovel: grade C `2026-07-04T04:35`
<sub>`prof_grade_dc971d60df30178e`</sub>

> Here's a thinking process:
> 
> 1.  **Analyze User Input:**
>    - The user provided a "RESEARCH SUMMARY FOR FEATURE: Verb_Shovel"
>    - It includes a thinking process, understanding of the feature, drafted parameters in JSON format, and a draft description (cut off at the end).
>    - I need to evaluate this against the grading criteria for the Chimera Project's Ralph Loop.
> 
> 2.  **Grading Criteria:**
>    -

### Verb_Step: grade C `2026-07-04T04:35`
<sub>`prof_grade_b95495e2f021ba8d`</sub>

> Here's a thinking process:
> 
> 1.  **Analyze User Input:**
>    - The user provided a "RESEARCH SUMMARY FOR FEATURE: Verb_Step"
>    - It includes a description, parameters (dimensions, colors, materials, positions, intensities), and mentions schools.
>    - Wait, the prompt says "Output Format: Structured JSON with keys: `description`, `parameters`, `references`, `schools`". But the user's input doesn't a

### Verb_Step: grade C `2026-07-04T04:37`
<sub>`prof_grade_03b0a0ba4be20838`</sub>

> Here's a thinking process:
> 
> 1.  **Analyze User Input:**
>    - The user provided a "RESEARCH SUMMARY FOR FEATURE: Verb_Step"
>    - It includes a thinking process, deconstruction, parameter determination, and JSON structure outline.
>    - However, the actual output is incomplete/cut off at the end ("Unreal Engine 5"). It doesn't actually provide the final structured JSON or complete the references/scho

### Verb_Look: grade A `2026-07-04T04:37`
<sub>`prof_grade_6a97b22d6c0770cf`</sub>

> [reasoning sentence].
> 
> 2.  **Evaluate against Criteria:**
>    - *Specific technical parameters:* The summary provides concrete values for dimensions (1920x1080, radius 64.0), colors ([0.0, 0.85, 1.0]), materials (baseColor, roughness=0.3, metallic=0.7), positions ({x:0.0, y:0.0, z:2.5}), and intensities (1500.0 lumens, zoomSpeed 1.2). These are specific and realistic for UE5 development.
>    - *Real

### Player_Character_Lighting: grade C `2026-07-04T04:53`
<sub>`prof_grade_76ec897d5061a616`</sub>

> The user wants me to act as the Professor for the Chimera Project's Ralph Loop.
> I need to review a research summary provided in the prompt.
> Wait, looking at the prompt structure:
> The user provided a "RESEARCH SUMMARY FOR FEATURE: Player_Character_Lighting" which includes a thinking process and JSON generation instructions. But wait, the actual content of the research summary isn't fully generated 

### Player_Character_Lighting: grade C `2026-07-04T04:56`
<sub>`prof_grade_55783a2583f54dd8`</sub>

> Here's a thinking process:
> 
> 1.  **Analyze User Input:**
>    - Role: Research analyst for Chimera Project (deep-space trading game in UE5)
>    - Task: Feature = 'Player_Character_Lighting', Type = 'Lighting'
>    - Required Output Format: ONLY valid JSON, exactly these keys: "description", "parameters" (with specific sub-keys), "references", "web_references", "schools". NO thinking process, NO markdown

### Player_Character_Lighting: grade C `2026-07-04T05:00`
<sub>`prof_grade_9b000e15bf8b6d6a`</sub>

> 
>    - *F: Inadequate or missing research.*
> 
>    Let's check the provided summary against these criteria:
>    - **Technical Parameters:** Has `dimensions`, `radius`, `base_color`, `roughness`, `metallic`, `position`, `intensity`, `light_type`. These are specific and relevant to UE5 lighting. However, some parameters like roughness/metallic/dimensions seem more suited for a material/geometry than a li

### Player_Character_Lighting: grade C `2026-07-04T05:01`
<sub>`prof_grade_0ccf095915f32920`</sub>

> [reasoning sentence]
> 
> 2.  **Evaluate the Input against Criteria:**
>    - *Specific technical parameters*: Yes, it has width, height, depth, radius, base_color, roughness, metallic, position, intensity, light_type. All are specific floats/arrays/strings.
>    - *Real-world references*: Yes, lists films (Blade Runner 2049, Alien), games (Mass Effect 3), and UE5 docs/GDC talks. These are real and releva

### Player_Character_Lighting: grade C `2026-07-04T05:04`
<sub>`prof_grade_7dfe00e4c944fd99`</sub>

> pecific technical parameters, real-world references, and clear implementation path.
>      - B: Good research but missing some specific parameters or references.
>      - C: Basic research with vague parameters, no real references.
>      - F: Inadequate or missing research.
> 
> 2.  **Evaluate against Criteria:**
>    - *Specific technical parameters:* Yes, detailed lighting setup (color, roughness, metallic

### Player_Character_Lighting: grade C `2026-07-04T05:05`
<sub>`prof_grade_5c5143f0cf135bce`</sub>

> { "description": "...", "parameters": { "dimensions": {"width": 0.8, "height": 1.5, "depth": 0.2}

### Player_Character_Lighting: grade C `2026-07-04T05:06`
<sub>`prof_grade_cee394fd32358a7b`</sub>

> eature:** Player_Character_Lighting
>    - **Description:** Mentions tint for space environment, roughness, metallic, position, intensity, light_type (RectArea), dimensions, radius, base_color. It's framed as a draft with some self-correction/adjustment notes ("Wait, the prompt says `parameters` must have exactly these keys...").
>    - **References:** Lists creative reference strings like "Cinematic 

### Player_Character_Lighting: grade C `2026-07-04T05:10`
<sub>`prof_grade_76afa05b125eea94`</sub>

> The summary provides complete and specific technical parameters aligned with UE5 standards, includes relevant real-world references from film and game development schools, and outlines a clear implementation path for dynamic character lighting in deep-space environments.
> 
> Wait, let's double check the exact format requested:
> Grade: [Letter]
> Score: [Score]
> Reasoning: [reasoning sentence]
> 
> I will out

### Player_Character_Lighting: grade C `2026-07-04T05:11`
<sub>`prof_grade_a952ce9a15984447`</sub>

> Here's a thinking process:
> 
> 1.  **Analyze User Input:**
>    - Role: Professor for Chimera Project's Ralph Loop
>    - Task: Review research summaries for features and assign a grade (A, B, C, or F) based on quality, completeness, fidelity to references/parameters.
>    - Grading Criteria:
>      - A: Complete research with specific technical parameters, real-world references, clear implementation path.
>  

### Player_Character_Lighting: grade F `2026-07-04T05:13`
<sub>`prof_grade_e07d15902718e3b0`</sub>

> The submission is severely truncated, missing critical parameters, references, and structural completeness required for adequate research evaluation.
> 
>    Check constraints: Format exactly as requested. "Grade: [Letter]\nScore: [Score]\nReasoning: [reasoning sentence]"
>    All good. I will output exactly that. No extra text.
>    Wait, let's verify the exact format requested:
>    "Format your response 

### Player_Character_Lighting: grade C `2026-07-04T05:15`
<sub>`prof_grade_59be0d0d7b02f6a6`</sub>

> [reasoning sentence]
> 
> Let's evaluate the provided summary against the criteria.
> The summary includes:
> 
> Does it meet "A"? It has specific technical parameters, clear implementation path (mentions Lumen, rim lighting setup), and references/web refs. The parameters match the exact schema requested. The description is solid. I'd lean towards A or B. Given the strict grading criteria, if it has all par

### Player_Character_Lighting: grade F `2026-07-04T05:18`
<sub>`prof_grade_2f44e8e8b04fa5a0`</sub>

> The submission consists of a thinking process and drafting notes rather than a complete, structured research summary with valid JSON output containing specific technical parameters and references.
> 
> Wait, let me double-check the input text again.
> The user pasted:
> "RESEARCH SUMMARY FOR FEATURE: Player_Character_Lighting
> Description: Here's a thinking process: ... [Steps] ... Let's construct the JSON

### Player_Character_Lighting: grade B `2026-07-04T05:29`
<sub>`prof_grade_b72be99dca18d9db`</sub>

> The research provides specific technical parameters for a point light overlay but lacks detailed implementation paths and real-world references beyond generic school topics.

### Player_Character_Lighting: grade B `2026-07-04T05:35`
<sub>`prof_grade_e81515ea3164e981`</sub>

> The research provides specific technical parameters for the lighting system and a relevant reference to Unreal Engine's lighting capabilities, but it lacks detailed implementation steps or references to specific shader/material workflows required for dynamic emissive changes based on emotional states.

### Player_Character_Lighting: grade B `2026-07-04T05:43`
<sub>`prof_grade_d75828d5c61fd20b`</sub>

> The research provides specific technical parameters for lighting but lacks detailed implementation methodology and sufficient real-world references to achieve an A grade.

### Tool_Shovel_Model: grade C `2026-07-04T15:01`
<sub>`professor_grade_ef64717b4d520850`</sub>

> LM Studio unavailable, default grade assigned.

### Player_Character_Suit_Visor: grade A `2026-07-04T16:24`
<sub>`professor_grade_1bf1d076b6c54468`</sub>

> The submission earns an A because it provides exact numerical parameters for geometry and materials, includes specific real-world URLs, and outlines a clear implementation path using defined MCP tools.

### Player_Character_Model: grade A `2026-07-04T16:59`
<sub>`professor_grade_092f9a02863066b6`</sub>

> The submission fully satisfies the A-level criteria by providing exact numerical parameters, verifiable real-world references with direct URLs, and a detailed implementation path specifying MCP tools and sequential steps.

### Build_Pipeline: grade F `2026-07-05T21:47`
<sub>`professor_grade_1a92c9ff41eb66f4`</sub>

> UBT compilation fail: E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Tests\ChimeraDSLTests.cpp(52,53): error C2039: 'GetCurrentFuelLiters': is not a member of 'UFlightComponent'

### Build_Pipeline: grade F `2026-07-05T21:47`
<sub>`professor_grade_8f4a03f041187ce9`</sub>

> UBT compilation fail: no error text captured

### Visual_Verification: grade C `2026-07-05T21:49`
<sub>`professor_grade_d543406104bab7ca`</sub>

> Visual verification returned aborted_wrong_window: Foreground window was 'PythonChimera – README.md'

### Visual_Verification: grade C `2026-07-05T21:49`
<sub>`professor_grade_4b3ac1a8094ad245`</sub>

> Visual verification returned incomplete: Screenshot aborted: Unreal Editor was not the foreground window

## V. Wills & Pains (generational inheritance)

*401 entries; showing 40.*

### Loop 8 System_Economy defect fixes + workflow hardening `2026-07-05T21:49`
<sub>`phase_4fdbf6143a64e0e1`</sub>

> result: UBT Result: Succeeded (8 actions, 13.75s, 0 errors). 3 playtests failed (stub implementations). Visual verification aborted: UE not foreground. Graph: 758 nodes, 283 mutations. All 8 workflow-hardening recommendations implemented and verified (syntax, guard tests, DNA repair, preflight, stale-tree c

### Workflow_Test `2026-07-05T21:52`
<sub>`phase_beb2f083138ac75a`</sub>

> result: pass

### CLI_Test_Phase `2026-07-05T21:53`
<sub>`phase_7b153f75a17749fc`</sub>

> result: pass

### Workflow_Test_Phase `2026-07-05T21:56`
<sub>`phase_6118d7207a361a36`</sub>

> result: ALL COMPONENTS VERIFIED

### System_Economy professor review fixes `2026-07-05T23:04`
<sub>`phase_8fa72cc6149d5f7a`</sub>

> result: Implemented: mean reversion (fluctuation fix) + station tier bounds (price bounds fix). Build: Succeeded (9 actions, 0 errors). Grade: C->B. Status: implemented (pending LM Studio re-review for A).

### Recursive gap closure `2026-07-06T00:10`
<sub>`phase_a0b0c20b9154deca`</sub>

> result: Build Succeeded. 9 actions, 0 errors. All gap fixes verified.

### Recursive gap closure — final `2026-07-06T00:12`
<sub>`phase_4f1c0b6e86fed7f1`</sub>

> result: Build Succeeded (9 actions, 0 errors). Integrity check: 40 files present. Pre-flight trend: 20 pass, 0 fail. SSR retry: verified. Git status: automated. MCP pre-checks: active. Build-retry loop: in place.

### 5-Cycle Autonomous Run `2026-07-06T01:02`
<sub>`phase_53d4fe66c7ef1a62`</sub>

> result: 5 builds: 5 pass, 0 fail. 7 recursive discoveries, all fixed. LM Studio: adapted to qwen3.6 text-only. Visual gate: blocks on UE not being foreground.

### Full Pipeline — 4-Layer Scene Verification `2026-07-06T02:51`
<sub>`phase_29fede184b02da93`</sub>

> result: Build: Succeeded (9 actions, 0 errors). Scene: Layer1+2+3 pass, Layer4 FAIL (empty level). Gate correctly blocked. Need to spawn actors before verification passes.

### Full pipeline solidification — 4-layer scene verification `2026-07-06T03:18`
<sub>`phase_4563fbb2b43b5a92`</sub>

> result: UBT Result: Succeeded (9 actions, 13.75s, 0 errors). Scene Verifier Layers 1-3 PASS, Layer 4 FAIL (greybox level — qwen3.6 vision correctly identified no game actors). Pipeline blocked on mandatory vision gate. Exit code 1.

### Full system integration — all 6 phases `2026-07-06T04:04`
<sub>`phase_970980f3e1199f6c`</sub>

> result: UBT: Succeeded (9 actions, 0 errors). Stage 7: Campuses queried, Professor grade B, screenshot captured, recorded to graph. All gates passed. Exit code 0.

### Loop 8: System_SaveLoad implemented via generator; SaveLoad/Economy/Factions reg `2026-07-06T06:11`
<sub>`phase_96edcf8dc7176f53`</sub>

> result: UBT verbatim: Result: Succeeded. Total execution time: 83.03 seconds. Exit code 0. All gates passed. Professor grade B. 46 generated files verified. Playtests 3 skipped (headless env). Merged to master 7203b62.

### First result-graded cycle: in-editor acceptance tests `2026-07-06T06:47`
<sub>`phase_a4dc9e87d8232ac0`</sub>

> result: Automation RunTests ChimeraTests.Acceptance: 4/4 Success, TEST COMPLETE EXIT CODE: 0. All four Loop 8 systems graded A (90/100) by result_grader from measured evidence; promoted to verified.

### Workflow rerun cycle 2 `2026-07-06T06:58`
<sub>`phase_b08caa7ccb3b5042`</sub>

> result: Pipeline exit 0; 7/7 ChimeraTests Success in-engine; grades: Economy F59.5, Factions C64.5, SaveLoad F47.8, Missions C72.2 — movement tracks real coverage only

### Retry cycle: SaveLoad+Missions coverage closed `2026-07-06T07:20`
<sub>`phase_65cf908af964d19f`</sub>

> result: UBT Result: Succeeded exit 0 (after gate-caught LNK2019 fixed); Automation 9/9 Success; SaveLoad B76 verified, Missions B75.5 verified. Frame audit: measuring executed criteria not test count; grader did not judge author-only claims; fix landed in generator template not C++; a would-look-good-but-wr

### Loop 8 blitz complete: all four systems verified `2026-07-06T07:41`
<sub>`phase_e1bb922e25e10de7`</sub>

> result: UBT Succeeded exit 0 x2 (one gate-caught private-member error fixed at generator); 13/13 automation tests Success in-engine; grades Economy 78.5B Factions 89.2B SaveLoad 79.0B Missions 88.5B, all verified; GPA 2.4. Frame audit: measured executed criteria against research-declared denominators; grade

### Engine-on telemetry cycle: Loop 8 final grades `2026-07-06T13:10`
<sub>`phase_8d20a871a2d84acf`</sub>

> result: 14/14 tests Success; fps 120 vs target 60; growth bounded; crash-free. Economy 90.5A Factions 99.2A SaveLoad 89.0B Missions 98.5A. Frame audit: fps measured foregrounded after catching the background-throttle proxy trap; delegate-fire and fuel/station wiring remain declared-open; grader consumed mac

### Loop 0 cycles: Player_Character_Model refined + Player_Character_Animation unblo `2026-07-06T14:33`
<sub>`phase_dea710ca642501cb`</sub>

> result: No build (asset-only cycles). Model A 98.8, Animation A 98.5 — 12/12 declared criteria measured in-engine. Read-backs: SKM_Manny_Simple + ABP_Unarmed_C on CharacterMesh0, OverrideMaterials=EVASuit x2, bones 161, height 191.5uu. PIE: anim instance live (UEDPIE ABP_Unarmed_C_0), idle at v=0 (vision: S

### Generation Protocol built (Legacy Loop + Circadian adaptation) `2026-07-06T15:46`
<sub>`phase_da55128aec6d109a`</sub>

> result: All 5 workstreams delivered and verified: inheritance handshake (postflight/preflight/graph), surprise capture, heuristic distiller (8 candidates staged H-1..H-8, idempotency proven), dream loop (cap 2/night, DREAM_REPORT.md), sacrificial forks (live: 3 died H-3 death, fixed, re-run winner conservat
> THE WILL: This generation built the Generation Protocol: sessions now wake with a Will, record surprises live, dream heuristic candidates nightly, and grow the constitution only through the Gardener's hands. Its own fork run died the H-3 death live and was resurrected by applying that pending lesson - approve H-2 and H-3 first. The archive keeps everything; the live graph stays light.
> pain P1: Distiller token-coverage will false-suppress genuinely new lessons once PENDING_HEURISTICS.md grows large - watch for repeat failures that never re-stage
> pain P2: Fork briefs cite LM-confabulated references (NASA TR 1967-304 may not exist) - Phase 1 research that trusts fork citations unverified builds on fiction
> pain P3: The four ANTHROPIC_*=deepseek User env vars still poison model routing and the permission classifier - any session without bypass permissions will stall again

### Dress rehearsal + Observation Collapse: full circadian cycle on Ground_Sand_Part `2026-07-06T16:24`
<sub>`phase_762486f41e1aeafb`</sub>

> result: CYCLE: fork winner citation FAILED verification (P2 proven: 'NASA TR 1967-304' matches no NASA series; params matched real Lunar Sourcebook anyway) -> corrected research + 6-criterion exam -> Niagara apply via 6 discovery iterations (authoring facade, lying instruments, throttle-freeze, duplication 
> THE WILL: The dress rehearsal ran the full circadian cycle: a fork brief died citation-verification, Niagara fought through four bridge traps, and the feature landed at an honest B. The lesson that outranks everything: the machine's verified is preliminary - 20 features now await the human's eyes, and that observation is the true collapse. Review the queue and PENDING_HEURISTICS before building anything new.
> pain P1: The 20-deep observation queue will rot unobserved unless verdicts become habitual - if none are recorded within a week the collapse step failed as designed
> pain P2: Every future VFX/particle feature will fight the Niagara authoring facade until the bridge plugin is fixed - budget template-reference workarounds, never trust authoring success flags
> pain P3: Expect human rejections to reopen [DONE*] loops when observed (sand particles are white bubbles at B 79.3) - the first rejections will demote board state and that is the system working

### Documentation solidification + GitHub push `2026-07-06T16:46`
<sub>`phase_12a084a3958002fc`</sub>

> result: All docs aligned to the Generation Protocol era: CLAUDE.md (key-paths drift fixed - phantom mcp_client.py/scene_verifier.py rows replaced with the real modules; verification section rewritten to the result-grading regime with human observation as final authority; protocol command block added), Contr

### Succession cycles + runbook: prepared for a less capable heir `2026-07-06T18:33`
<sub>`phase_fda9e71b0c0841b4`</sub>

> result: Cycle 1: sand fidelity debt formally BRIDGE-BLOCKED (binary scan: zero User params on all 7 stock templates; set_niagara_parameter = facade #2). Cycle 2: Ground_Sand_Footprints honest C 72.9 -> needs_refinement with 3-step study guide (FX wiring unconfirmed, anim notifies missing, decals unknown); B
> THE WILL: Two honest cycles: the sand debt is bridge-blocked (repair McpAutomationBridge before retrying VFX), and Footprints sits at C with a three-step study guide whose hinge - add_anim_notify - is untested. Your instructions are in SUCCESSOR_RUNBOOK.md: follow the task order, read everything back, and let a sharp C outrank a fake A. The queues belong to the human; surface them every dawn and never answer them yourself.
> pain P1: The successor will trust a success:true echo without read-back at least once despite prime directive 5 - watch the footprints retry for facade-blindness
> pain P2: add_anim_notify is the untested hinge of the footprints study guide - if it is facade #3 the feature stalls until the bridge plugin is repaired
> pain P3: Zero human verdicts have been recorded since the queues opened - if a week passes with the Gardener and Observer idle, the protocol is running open-circuit and DONE* loops are quietly rotting

### Ground_Sand_Footprints retry: tested the add_anim_notify hinge (NEXT item 2) `2026-07-06T19:43`
<sub>`phase_17828713d9c76201`</sub>

> result: add_anim_notify t=0.3 and t=0.8 both: success: false | error: Animation/Physics action 'add_anim_notify' not implemented | NOT_IMPLEMENTED. get_anim_sequence_info: identical NOT_IMPLEMENTED. No asset modified. Recorded pathway_attempt_e7fbb6ba12043a86 + surprise_3ddd345289e269b4
> THE WILL: Footprints retry dead-ended at step (a): the bridge implements neither add_anim_notify nor get_anim_sequence_info, so the study-guide hinge cannot be tested until McpAutomationBridge grows both actions (capable sessions only). No asset changed; grade stands C 72.9 needs_refinement. With human queues untouched, duty successors will fall to branch D (pipeline health check).
> pain P1: When a capable session implements add_anim_notify and reruns the recipe, notifies will add and read back fine but PIE footstep events will STILL not fire, because configure_footstep_fx only echoed scale vars (facade-scent) and the BP AnimNotify event wiring was never confirmed.

### pipeline health check `2026-07-06T20:05`
<sub>`phase_62a9bf8fa8e97b42`</sub>

> result: build_completed, grade B 75, all gates pass, 6 generated assets, 49 files
> THE WILL: Pipeline ran clean: build + visual verification both passed. Grade B (75). No feature changes — this was a health check cycle.
> pain P1: phase_da55128aec6d109a:P1

### demo architecture design `2026-07-06T21:56`
<sub>`phase_a3193c8fa52533c6`</sub>

> result: DEMO_ARCHITECTURE.md created with hybrid two-act demo plan: walkabout + trader loop, flight input bindings fix, station placement, possession transition
> THE WILL: Demo architecture designed for 20-feature queue closure. Phase 1: flight input bindings via generator method is first playtestable milestone.
> pain P1: phase_da55128aec6d109a:P1 distiller token-coverage suppression

### pipeline health check `2026-07-06T22:51`
<sub>`phase_4cf94206335d7778`</sub>

> result: exit code 0, grade B (75), build succeeded, visual verification passed, 6 generated assets, 49 files, 3 tests skipped; UBT result: Build.cs already has all required modules
> THE WILL: Pipeline health check completed with grade B. No human verdicts arrived; observation queue remains at 20 features awaiting eyes.
> pain P1: phase_da55128aec6d109a:P1 - Distiller token-coverage will false-suppress genuinely new lessons once PENDING_

### Demo 1 (Regolith Yard) Phase 1: yard assembled, zero-build `2026-07-07T00:02`
<sub>`phase_4d2da4e032a4aa07`</sub>

> result: grade A 98.5 (8/8 criteria); umap saved md5 BF835B4337DA843A8B43AFF26C701AD4 mtime 18:57; PIE possessed pawn BP_Astronaut_Character_C (Player_Astronaut); 3 pads OverrideMaterials read back MAT_Metal/Rock/GroundSand; SandDrift FX renders; soak 120fps crash-free 34->34 actors
> THE WILL: Regolith Yard persists in chimeradefaultlevel; WorldSettings GameMode explicitly GameModeBase (was null - generated GM never ran here). Session A is ready: brief the human, capture temperature #1, attribute across the 16 on-foot queue features. Phase 2 (DemoTerminal+generator surgery) is capable-only.
> pain P1: Tri-pad materials will read uniformly dark/indistinct at walk height (viewport shot shows a near-black strip); expect the temperature to flag ground look - route to Ground_* features, lighting/material-instance work, not placement

### Session A hotfix: input-from-zero for the astronaut (human playtest #1 dead-on-a `2026-07-07T00:17`
<sub>`phase_1b01fac303f3c24e`</sub>

> result: Human temperature #1: 'I have no ability to move my character' -> Verb_Step rejected->needs_refinement->repaired->re-verified. Root cause: BP_Astronaut has ZERO input graph (bridge cannot author BP graphs; all prior locomotion evidence was velocity injection). Fix: manual-lane Demo/DemoPlayerControl
> THE WILL: Regolith Yard is now actually walkable: WASD+mouse+space via DemoPlayerController, third-person camera auto-attached. Session A retry is ready - press Play. Verb_* observation verdicts must come from the human's replay; proxy locomotion evidence is now a known systemic gap.
> pain P1: The verb TARGETS (BP_Verb_* actors) may be as hollow as the walking was - built via bridge, never human-triggered; expect pick-up/drop/shovel interactions to no-op in Session A retry; if so route Verb_PickUp/Drop/Shovel rejections and pull BP-interaction wiring into the capable Phase 2 build

### Sleepwalker system implemented and integrated (SLEEPWALKER_DESIGN M1+M2+M3 essen `2026-07-07T00:55`
<sub>`phase_34195900a1671e58`</sub>

> result: grade A pending (8/8 criteria measured); first sleepwalk 4/5 beats (honest jump-probe failure), find->fix->verify loop closed at 5/5 clean walk; SimPlaytest simtest_73ce1be773dade94; rehearsal veto table live; distiller clusters sim_rejection (ranked below human_rejection); preflight [4.6] renders; 
> THE WILL: The game can now play itself: core/sleepwalker.py runs beat scripts in PIE, core/rehearsal.py decides next moves with veto tables, both feed the dream loop. Nightly rhythm (M4) staged as a rehearsal candidate. The human's word overrides everything; sim signals rank below human_rejection permanently.
> pain P1: Nightly unattended sleepwalks will eventually collide with a human/agent session already using PIE - first collision strands PIE running or corrupts a chronicle; needs an is-PIE-already-active check before play (one runtime_report call) and a polite retry

### Sleepwalker M4 nightly rhythm (sim_m4_nightly_20260707) + is-PIE-active guard im `2026-07-07T01:39`
<sub>`phase_3414a5cc1ff49e30`</sub>

> result: [SIM] 5/5 beats reached in 'regolith_yard'. Clean walk.
> THE WILL: Sleepwalker M4 nightly rhythm executed successfully with is-PIE-active check guard. Next: Demo_Phase3_SessionB_wiring or human session A retry.
> pain P1: Phase 2 dependencies may still block Phase 3 wiring

### fixed sleepwalker.py PIE-collision guard, gardener.py dry-run bug, verified proh `2026-07-07T02:09`
<sub>`phase_33cc2d55125bc551`</sub>

> result: sleepwalker.py PIE-collision guard added; gardener.py dry-run bug fixed; prohibitions documented.
> THE WILL: PIE-collision guard and dry-run fix applied; prohibitions verified in .roo/rules and AGENTS.md.
> pain P1: sleepwalker may still attempt PIE if runtime_report is not checked properly

### rehearsal branch C2 decision `2026-07-07T03:06`
<sub>`phase_a06bc8140bd62718`</sub>

> result: Rehearsal decided Demo_Phase3_SessionB_wiring (blocked by Phase 2); rollout_d574121026b1c97d.
> THE WILL: Rehearsal branch C2 decided Demo_Phase3_SessionB_wiring (blocked by Phase 2); no sleepwalker execution performed as next executable item is blocked.
> pain P1: phase_da55128aec6d109a:P1

### fallback pipeline health check (branch D) `2026-07-07T03:46`
<sub>`phase_ef0be888042d96ff`</sub>

> result: Result: Succeeded. Total execution time: 17.47 seconds. Build passed, 6 assets, 49 files, 3 tests skipped. Grade B. LM Studio HTTP 400 on Stage 7.2.
> THE WILL: Pipeline build succeeds cleanly (17.47s). Rehearsal again chose Demo_Phase3_SessionB_wiring (blocked by Phase 2, skip-cond hit again). LM Studio HTTP 400 on professor review stage. 22 observations still awaiting human verdicts. The pipeline's screenshot stage still uses pyautogui (prohibited by CYCLE_PROMPT) despite the successful compilation.
> pain P1: The pipeline's visual stage used pyautogui desktop capture again (forbidden); the prohibition constants say use MCP screenshot mode=editor_viewport but the pipeline code still calls the old path.

### Ground_Sand_Footprints MCP apply + save (setup_footstep_system + map_surface_to_ `2026-07-07T04:01`
<sub>`phase_0ddffb52d2d75240`</sub>

> result: setup_footstep_system: success true (foot_l/foot_r/trace 100); map_surface_to_sound: success true (Sand surface map); save_all: savedCount=1; runtime_report: isPIE=false, level loaded, actors present
> THE WILL: Ground_Sand_Footprints footstep system wired at BP level via MCP but footstep events still blocked (add_anim_notify NOT_IMPLEMENTED in bridge). Pipeline LM Studio URL fixed (localhost). Rehearsal now picks Ground_Sand_Footprints instead of blocked Phase 3. Three import-fallback bugs fixed. Next executable item: Ground_Sand_Footprints (need bridge fix for add_anim_notify) or Demo_Phase2_DemoTerminal (capable only, unblocks loop).
> pain P1: The bridge's NOT_IMPLEMENTED on add_anim_notify will re-block every feature needing anim events until a capable session patches Plugins/McpAutomationBridge

### fix_screenshot_pathway_and_verify_anim_notify `2026-07-07T04:32`
<sub>`phase_3baeff0ccd0f4556`</sub>

> result: Replaced pyautogui desktop screenshots with MCP control_editor screenshot mode=editor_viewport per H-2 prohibition; confirmed add_anim_notify/get_anim_sequence_info are NOT_IMPLEMENTED (facade #3) for Ground_Sand_Footprints
> THE WILL: Fixed pipeline screenshot path to use MCP control_editor screenshot mode=editor_viewport per H-2 prohibition. Ground_Sand_Footprints remains blocked on add_anim_notify NOT_IMPLEMENTED (capable sessions only).
> pain P1: phase_da55128aec6d109a:P1, phase_762486f41e1aeafb:P1, phase_762486f41e1aeafb:P3, phase_fda9e71b0c0841b4:P3

### remove_blocks_and_proceed_workflow_cycles `2026-07-07T04:51`
<sub>`phase_88190a038d6883e3`</sub>

> result: Fixed screenshot pathway per H-2 prohibition; confirmed add_anim_notify NOT_IMPLEMENTED (facade #3); implemented heuristics H-10, H-7, H-3
> THE WILL: Removed pyautogui desktop screenshots in favor of MCP control_editor screenshot mode=editor_viewport. Fixed killed_for_build recording, MCP error field capture, and LM reasoning dump retry logic.
> pain P1: phase_da55128aec6d109a:P1, phase_762486f41e1aeafb:P1, phase_762486f41e1aeafb:P3, phase_fda9e71b0c0841b4:P3

### remove_blocks_and_proceed_workflow_cycles_ultracode `2026-07-07T05:17`
<sub>`phase_e51e3b3461665ef9`</sub>

> result: Fixed screenshot pathway per H-2; confirmed add_anim_notify NOT_IMPLEMENTED (facade #3); implemented heuristics H-10, H-7, H-3, H-13
> THE WILL: Removed pyautogui desktop screenshots in favor of MCP control_editor screenshot mode=editor_viewport. Fixed killed_for_build recording, MCP error field capture, LM reasoning dump retry logic, and telemetry foreground execution for System_Economy grading.
> pain P1: phase_da55128aec6d109a:P1, phase_762486f41e1aeafb:P1, phase_762486f41e1aeafb:P3, phase_fda9e71b0c0841b4:P3

### remove_blocks_and_proceed_workflow_cycles_ultracode_mcp_fix `2026-07-07T05:35`
<sub>`phase_48f85d284182082f`</sub>

> result: Fixed screenshot pathway per H-2; fixed add_anim_notify/get_anim_sequence_info MCP command registration routing issue in McpConsolidatedActionRouting.h; implemented heuristics H-10, H-7, H-3, H-13
> THE WILL: Removed pyautogui desktop screenshots in favor of MCP control_editor screenshot mode=editor_viewport. Fixed killed_for_build recording, MCP error field capture, LM reasoning dump retry logic, telemetry foreground execution, and added add_anim_notify/get_anim_sequence_info to MCP action routing lists.
> pain P1: phase_da55128aec6d109a:P1, phase_762486f41e1aeafb:P1, phase_762486f41e1aeafb:P3, phase_fda9e71b0c0841b4:P3

### Confirmed Ground_Sand_Footprints facade #3 - add_anim_notify/get_anim_sequence_i `2026-07-07T05:58`
<sub>`phase_0f0bac451e5ce1dd`</sub>

> result: add_anim_notify and get_anim_sequence_info return NOT_IMPLEMENTED despite McpConsolidatedActionRouting.h registration. Sleepwalker: 5/5 beats reached in 'regolith_yard'. Clean walk.
> THE WILL: Confirmed facade #3 for add_anim_notify/get_anim_sequence_info; BP wiring remains – capable sessions only. Removed pyautogui screenshots, fixed MCP error field capture, LM reasoning dump retry logic, telemetry foreground execution.
> pain P1: The 20-deep observation queue will rot unobserved unless verdicts become habitual

### Rehearsal selected Ground_Sand_Footprints; already confirmed facade #3 - add_ani `2026-07-07T06:03`
<sub>`phase_7658c4f6f43483ad`</sub>

> result: add_anim_notify and get_anim_sequence_info return NOT_IMPLEMENTED despite McpConsolidatedActionRouting.h registration. Sleepwalker: 5/5 beats reached in 'regolith_yard'. Clean walk.
> THE WILL: Confirmed facade #3 for add_anim_notify/get_anim_sequence_info; BP wiring remains – capable sessions only. Removed pyautogui screenshots, fixed MCP error field capture, LM reasoning dump retry logic, telemetry foreground execution.
> pain P1: The 20-deep observation queue will rot unobserved unless verdicts become habitual

## VI. Rep Milestones (resolution through repetition)

*68 entries; showing 40.*

### Ground_Sand_Sound promoted to tier 1
<sub>`promo:Ground_Sand_Sound:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Environment promoted to tier 1
<sub>`promo:subsystem/Environment:1`</sub>

> shaping promotion (streak rule): streak 8 @ 99%

### subsystem/Flight promoted to tier 1
<sub>`promo:subsystem/Flight:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Stations promoted to tier 1
<sub>`promo:subsystem/Stations:1`</sub>

> shaping promotion (streak rule): streak 8 @ 99%

### Verb_PickUp promoted to tier 1
<sub>`promo:Verb_PickUp:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### audio_visual_sync/telemetry_accessors promoted to tier 1
<sub>`promo:audio_visual_sync/telemetry_accessors:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Inventory promoted to tier 1
<sub>`promo:subsystem/Inventory:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Combat promoted to tier 1
<sub>`promo:subsystem/Combat:1`</sub>

> shaping promotion (streak rule): streak 8 @ 97%

### subsystem/Travel promoted to tier 1
<sub>`promo:subsystem/Travel:1`</sub>

> shaping promotion (streak rule): streak 8 @ 97%

### subsystem/Economy promoted to tier 1
<sub>`promo:subsystem/Economy:1`</sub>

> shaping promotion (streak rule): streak 8 @ 96%

### subsystem/PCG promoted to tier 1
<sub>`promo:subsystem/PCG:1`</sub>

> shaping promotion (streak rule): streak 8 @ 95%

### System_DSL_Fidelity promoted to tier 1
<sub>`promo:System_DSL_Fidelity:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### System_SaveGame promoted to tier 1
<sub>`promo:System_SaveGame:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Suit promoted to tier 1
<sub>`promo:subsystem/Suit:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/root promoted to tier 1
<sub>`promo:subsystem/root:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Materials promoted to tier 1
<sub>`promo:subsystem/Materials:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Shelter promoted to tier 1
<sub>`promo:subsystem/Shelter:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/AI promoted to tier 1
<sub>`promo:subsystem/AI:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### UI_Suit_HUD promoted to tier 1
<sub>`promo:UI_Suit_HUD:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Tests promoted to tier 1
<sub>`promo:subsystem/Tests:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Ships promoted to tier 1
<sub>`promo:subsystem/Ships:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### Verb_Shovel promoted to tier 1
<sub>`promo:Verb_Shovel:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Demo promoted to tier 1
<sub>`promo:subsystem/Demo:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### Malcolm_Envelope promoted to tier 2
<sub>`promo:Malcolm_Envelope:2`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/GameMode promoted to tier 1
<sub>`promo:subsystem/GameMode:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/VFX promoted to tier 1
<sub>`promo:subsystem/VFX:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### Sleepwalker_Beats promoted to tier 2
<sub>`promo:Sleepwalker_Beats:2`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### Game_Feel promoted to tier 3
<sub>`promo:Game_Feel:3`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### Sprint_Input/binding promoted to tier 1
<sub>`promo:Sprint_Input/binding:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### Sprint_Input/harness_parity promoted to tier 1
<sub>`promo:Sprint_Input/harness_parity:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### Sprint_Input/state promoted to tier 1
<sub>`promo:Sprint_Input/state:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### Sprint_Input/volume_norm promoted to tier 1
<sub>`promo:Sprint_Input/volume_norm:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Movement promoted to tier 1
<sub>`promo:subsystem/Movement:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Subsystems promoted to tier 1
<sub>`promo:subsystem/Subsystems:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### subsystem/Characters promoted to tier 1
<sub>`promo:subsystem/Characters:1`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### audio_visual_sync/report_telemetry promoted to tier 2
<sub>`promo:audio_visual_sync/report_telemetry:2`</sub>

> shaping promotion (streak rule): streak 8 @ 100%

### ADotCharacter — ledger standing
<sub>`repstat:ADotCharacter`</sub>

> ADotCharacter                         254 reps  100%  streak  8  battery   2 (0 pie)  READY

### AErisaidActor — ledger standing
<sub>`repstat:AErisaidActor`</sub>

> AErisaidActor                          44 reps  100%  streak  8  battery   2 (0 pie)  tier 0/0

### Any — ledger standing
<sub>`repstat:Any`</sub>

> Any position-dependent beat agains     24 reps   50%  streak  0  battery   2 (0 pie)  tier 0/0

### audio_visual_sync/report_telemetry — ledger standing
<sub>`repstat:audio_visual_sync/report_telemetry`</sub>

> audio_visual_sync/report_telemetry    228 reps  100%  streak  8  battery   1 (0 pie)  READY

## VII. The Drift Ledger (spec promises vs kept)

*1 entries; showing 1.*

### Spec coverage: 169/169 tokens implemented (100%)
<sub>`drift:coverage`</sub>

> DSL spec->code fidelity ledger (probe v2: snake|CamelCase across Source/).
> triage: 2026-07-12 full arc: 19% (145 reds, mostly assumed noise -> proven 84% true drift) -> 50% (deep_space_trader kept via spec-binding components) -> 100% (satellite sweep: 8 more domain components + carrier).

## VIII. The Breakdown Ledger (compound targets -> processed parts)

*1 entries; showing 1.*

### Sprint_Input -> 4 parts `2026-07-12T17:35`
<sub>`dc_b1af6b6e2f33`</sub>

> kind: input_rig
> evidence: simtest_536c81002961d807; elim_b58535a07e3675b0
> part state: tb-0013 (Sprint_Input/state)
> part binding: tb-0014 (Sprint_Input/binding)
> part harness_parity: tb-0015 (Sprint_Input/harness_parity)
> part readback: tb-0016 (Sprint_Input/readback)

## Index of Features

- **AAA Quality** — 1 entry: `observation_766c8e839f115065`
- **AAA_Quality** — 1 entry: `observation_e4d6503c704ed448`
- **ADotCharacter** — 1 entry: `repstat:ADotCharacter`
- **AErisaidActor** — 1 entry: `repstat:AErisaidActor`
- **Any** — 1 entry: `repstat:Any`
- **Beat_Scripts_Tautology_Fix** — 1 entry: `repstat:Beat_Scripts_Tautology_Fix`
- **Build_Pipeline** — 65 entries: `professor_grade_1a92c9ff41eb66f4`, `professor_grade_8f4a03f041187ce9`, `professor_grade_0f7ad1992f6d1372`, `professor_grade_3b51652770d01ac1`, `professor_grade_828db6a52893ed78`, `professor_grade_9892b433ad232f61` ...
- **CLI_Test** — 1 entry: `professor_grade_2e8f98354014d117`
- **Competitive_Feature_Design_Patterns_Research** — 2 entries: `observation_4e4ccc9b30b5f883`, `observation_e5af82bfa4350985`
- **Competitive_Feature_Design_Patterns_Research_Summary** — 1 entry: `observation_0efae6fbbe195f0b`
- **Costless Life Bad Ending Trigger** — 1 entry: `observation_3872db7a8dbcb6d4`
- **Costless_Life_Bad_Ending_Trigger** — 4 entries: `observation_58b488734ad7e735`, `observation_5885fbddda77f1ce`, `observation_c3a652ef1a497917`, `observation_1716e4e117c19313`
- **DeepSpaceTrader** — 34 entries: `prof_grade_2ac718a056316db9`, `prof_grade_b1867a4a6f54cffb`, `prof_grade_07ae65f2016e5e81`, `prof_grade_8a6acac25d85a1e3`, `prof_grade_303b6c831904ca75`, `prof_grade_917ce58a7c1c99b2` ...
- **DeepSpaceTrader Pipeline** — 1 entry: `observation_af50928ba15028ec`
- **DeepSpaceTrader_Pipeline** — 1 entry: `observation_92944298190692d6`
- **Demo_Level** — 1 entry: `repstat:Demo_Level`
- **Demo_Phase2_DemoTerminal** — 1 entry: `observation_2d78fc6cfdb7442e`
- **Demo_RegolithYard_InputFix** — 1 entry: `professor_grade_9b907100ec5edf92`
- **Demo_RegolithYard_L1** — 2 entries: `professor_grade_e7dc8ca35cdb75cd`, `observation_4dcd58a93e4d30f0`
- **Demo_RegolithYard_Systems** — 1 entry: `professor_grade_9e2f64b5d75f177d`
- **Diagnose** — 1 entry: `repstat:Diagnose`
- **FFootstepEvent** — 1 entry: `repstat:FFootstepEvent`
- **FStar** — 1 entry: `repstat:FStar`
- **Game_Feel** — 2 entries: `promo:Game_Feel:3`, `repstat:Game_Feel`
- **Ground_Metal_Surface** — 8 entries: `prof_grade_73b132f72683a4d3`, `prof_grade_6f1def660833e414`, `prof_grade_69ce58e03c7f5ac8`, `observation_b64690eb06c29e34`, `observation_620b633919bd58de`, `observation_72620c81985763fc` ...
- **Ground_Rock_Surface** — 6 entries: `prof_grade_bec71f9e63043118`, `observation_8650722006d93846`, `observation_cf32cafa76fd3b40`, `observation_4041b18f4f89b640`, `observation_49ecad284084ddab`, `observation_1bc2480d62a36f98`
- **Ground_Sand_Footprints** — 3 entries: `professor_grade_f5f95d125880d69b`, `observation_e0159ce465c0a841`, `observation_c6cff95d6bca1e16`
- **Ground_Sand_Particles** — 7 entries: `professor_grade_f6341a2dcf895b0f`, `observation_01ac5afa8acdcc0b`, `observation_c1eb6cfb82d8fc19`, `observation_01f675d910535fdb`, `prof_grade_880c3b754225d00c`, `observation_dcdf9808285fe705` ...
- **Ground_Sand_Sound** — 3 entries: `professor_grade_07fdf2b5e86aa60f`, `promo:Ground_Sand_Sound:1`, `repstat:Ground_Sand_Sound`
- **Ground_Sand_Surface** — 8 entries: `prof_grade_aeb4f8f54f636fdb`, `prof_grade_ab1739bd8cefcb3a`, `observation_9f0cdcfdc1c92f93`, `observation_17f31e2349d85e8a`, `observation_0cbedc2aa655ee37`, `observation_5b9bb3c07dfe4a33` ...
- **Groundskeeping_floor** — 1 entry: `observation_c29b810e69f7c7db`
- **Loop_4_Tools_Expanded** — 1 entry: `professor_grade_9da1c1319e880576`
- **MCP_Pathways** — 1 entry: `repstat:MCP_Pathways`
- **Malcolm_Envelope** — 3 entries: `elim_58026efcf3adc442`, `promo:Malcolm_Envelope:2`, `repstat:Malcolm_Envelope`
- **Pipeline_Gates** — 1 entry: `professor_grade_8fe800ca62b96505`
- **Player_Character_Animation** — 2 entries: `professor_grade_0d659c2ad91db9c0`, `observation_b2e38b785162731b`
- **Player_Character_Lighting** — 17 entries: `prof_grade_76ec897d5061a616`, `prof_grade_55783a2583f54dd8`, `prof_grade_9b000e15bf8b6d6a`, `prof_grade_0ccf095915f32920`, `prof_grade_7dfe00e4c944fd99`, `prof_grade_5c5143f0cf135bce` ...
- **Player_Character_Model** — 16 entries: `prof_grade_5b0c3fa2dca3572f`, `prof_grade_629a04ca3e067c51`, `prof_grade_2e63165139491b63`, `professor_grade_092f9a02863066b6`, `prof_grade_9ad8b9d5fff54539`, `prof_grade_e7237a099dc54076` ...
- **Player_Character_Model_Visor_Apply** — 1 entry: `observation_b62aa5f1f36ce0a6`
- **Player_Character_Suit** — 3 entries: `prof_grade_f38f94e79e174041`, `observation_d801087b243f5dbe`, `observation_f5ead6a385323c1e`
- **Player_Character_Suit_Visor** — 1 entry: `professor_grade_1bf1d076b6c54468`
- **Regolith_Dust_Accumulation_Visual_Feedback** — 1 entry: `observation_44947b0e1ef55883`
- **Shelter_Habitat_Geometry** — 1 entry: `observation_1a64d91760b71c72`
- **Shelter_Habitat_Lighting** — 2 entries: `observation_e5809b7506f928d1`, `repstat:Shelter_Habitat_Lighting`
- **Shelter_Habitat_Materials** — 2 entries: `observation_f9f0c860d53c4d2a`, `repstat:Shelter_Habitat_Materials`
- **Sky_Atmosphere_Scattering** — 3 entries: `observation_6df7bf32c69dc5ff`, `observation_d9772e6bb1395ac4`, `repstat:Sky_Atmosphere_Scattering`
- **Sky_Earth_Material** — 1 entry: `observation_d98165bc5d378bc0`
- **Sky_Earth_Model** — 1 entry: `observation_516b96cf549ce230`
- **Sky_Loop_Realization** — 1 entry: `repstat:Sky_Loop_Realization`
- **Sky_Moon_Material** — 1 entry: `observation_451fa0d313ca675c`
- **Sky_Moon_Model** — 1 entry: `observation_38357b09bd9525ac`
- **Sky_Starfield** — 3 entries: `observation_408512d7f36aff6e`, `observation_87f13262d22bd319`, `repstat:Sky_Starfield`
- **Sky_Sun_Lighting** — 1 entry: `observation_2906c8aa1adb1c23`
- **Sleepwalker_Beats** — 2 entries: `promo:Sleepwalker_Beats:2`, `repstat:Sleepwalker_Beats`
- **Sleepwalker_System** — 2 entries: `professor_grade_c672ff663bf3651b`, `observation_79bd753c166a2901`
- **Social_Trade** — 3 entries: `observation_a54d668be0240c2b`, `observation_a02f3340f1bf3b5c`, `repstat:Social_Trade`
- **Sprint_Input** — 1 entry: `dc_b1af6b6e2f33`
- **Sprint_Input/binding** — 2 entries: `promo:Sprint_Input/binding:1`, `repstat:Sprint_Input/binding`
- **Sprint_Input/capture_peak** — 2 entries: `elim_1b283361406a25a0`, `repstat:Sprint_Input/capture_peak`
- **Sprint_Input/harness_parity** — 3 entries: `elim_e1ceb1b092b179af`, `promo:Sprint_Input/harness_parity:1`, `repstat:Sprint_Input/harness_parity`
- **Sprint_Input/readback** — 1 entry: `repstat:Sprint_Input/readback`
- **Sprint_Input/state** — 2 entries: `promo:Sprint_Input/state:1`, `repstat:Sprint_Input/state`
- **Sprint_Input/volume_norm** — 1 entry: `promo:Sprint_Input/volume_norm:1`
- **Substrate_Terrain** — 2 entries: `elim_06e43126d4d0332f`, `elim_d7f65379cd4984b1`
- **System_DSL_Fidelity** — 4 entries: `elim_5db874e721a6c962`, `elim_fc1e3b5e9ce65fbe`, `observation_178caf29b500bc22`, `promo:System_DSL_Fidelity:1`
- **System_Economy** — 8 entries: `professor_grade_7886af92f495ccd1`, `professor_grade_987966987f9c8be5`, `professor_grade_cbdfff41c119fe65`, `professor_grade_364a07e3116f20a6`, `professor_grade_bf25d5d3a1fc673f`, `professor_grade_c5197b91a28559eb` ...
- **System_Factions** — 6 entries: `professor_grade_eed210f4ab52757d`, `professor_grade_490fe77b72f70388`, `professor_grade_b2bb156bf98b0f0a`, `professor_grade_2cef42bbe0482227`, `professor_grade_311a8a7ca7b93bff`, `observation_dd211c641ad2d9ae`
- **System_Missions** — 7 entries: `professor_grade_2a09ab2aa52757cf`, `professor_grade_f0b8a52f650f4cf9`, `professor_grade_a43257c7bf4c0783`, `professor_grade_df839bc8e137db81`, `professor_grade_8b0cf44f4627423c`, `professor_grade_cdfa82d2982b429b` ...
- **System_SaveGame** — 2 entries: `elim_8f4f3dbdf1bd7e24`, `promo:System_SaveGame:1`
- **System_SaveLoad** — 7 entries: `professor_grade_48116037dcbb5a91`, `professor_grade_d3df7c53cd313883`, `professor_grade_38cb65693e29e58e`, `professor_grade_ef959c286f6fb9a6`, `professor_grade_4acb446775c3c0ba`, `professor_grade_10f28412a70cf5a4` ...
- **Test_Feature** — 1 entry: `professor_grade_194f6be1dc1b74ec`
- **The Erisaid Audio Attunement Minigame** — 1 entry: `observation_cae671193d829088`
- **The_Erisaid_Audio_Attunement_Minigame** — 1 entry: `observation_0fb21208605b76f0`
- **Titan_Run_Gravity_Shift_Mechanics** — 1 entry: `observation_93afffe7c4d6dcf2`
- **Tool_Scanner_Material** — 1 entry: `observation_92639a8143037cac`
- **Tool_Scanner_Model** — 1 entry: `observation_b1c08c983da0e237`
- **Tool_Shovel_Model** — 1 entry: `professor_grade_ef64717b4d520850`
- **Tool_Weapon_Model** — 2 entries: `observation_af7f40abe37d1f59`, `observation_c941ed7c5d84c89d`
- **Travel_Ship_Exterior** — 1 entry: `observation_b4e929ab127f9760`
- **Travel_Vehicle_Basic** — 1 entry: `observation_a640c045d6ceaf69`
- **Travel_Walking** — 1 entry: `professor_grade_f4fa95fd0c69ab19`
- **UChimeraAttunementComponent** — 1 entry: `observation_455906b50c6a0a1a`
- **UI_Suit_HUD** — 1 entry: `promo:UI_Suit_HUD:1`
- **Verb_Bend** — 8 entries: `observation_44efdff7a36a3d5c`, `observation_f425fa8d8104e1ab`, `observation_895434ae9b085bf4`, `observation_4547f04de239b0c6`, `observation_4c8c2edcd5f7c90a`, `observation_7a2b4ea2a2acfeaa` ...
- **Verb_Drop** — 7 entries: `observation_22aff4c35c846157`, `observation_837c826fac9186ed`, `observation_2d845fd5545f3279`, `observation_6bea305cf7f95767`, `observation_5820fdfd7a98a822`, `observation_de5cd62f1961749e` ...
- **Verb_Look** — 6 entries: `prof_grade_6a97b22d6c0770cf`, `observation_4f5df1d23ee81c4b`, `observation_29973953faf496a2`, `observation_bdbc5d02c1f55134`, `observation_f2a158b150113299`, `observation_15a1c92436f8c2da`
- **Verb_PickUp** — 10 entries: `observation_e9e42a55deceea63`, `observation_bbd3824598c5d283`, `observation_894b90c0c982fb7e`, `observation_ed0254872e5fb7b9`, `observation_b55ec24356ac6d0e`, `observation_9d3a133b4e663033` ...
- **Verb_Shovel** — 7 entries: `prof_grade_dc971d60df30178e`, `observation_45b8b52d04bb680f`, `observation_bb1ac7c1c90f2343`, `observation_c1af4475a658d6b3`, `observation_d30ab5686b763ed3`, `observation_b4e171a33eea4038` ...
- **Verb_Step** — 10 entries: `prof_grade_b95495e2f021ba8d`, `prof_grade_03b0a0ba4be20838`, `observation_f629252c5bdbcd07`, `observation_f165beba3aac9059`, `observation_07b6bd92e7707c41`, `observation_055f108c6b057f3f` ...
- **Visual_Verification** — 41 entries: `professor_grade_d543406104bab7ca`, `professor_grade_4b3ac1a8094ad245`, `professor_grade_5c4febabf91f23f0`, `professor_grade_caf6e3de66d62355`, `professor_grade_146029f24a743a1c`, `professor_grade_7a0262bc83441f63` ...
- **Will_Forewarning_Inheritance_UI** — 1 entry: `observation_8ce91d7d1a60ddfc`
- **Workflow_Test** — 1 entry: `professor_grade_609983d30ed38756`
- **X** — 11 entries: `professor_grade_ac905fba474a25d0`, `professor_grade_82edc8d7f573c657`, `professor_grade_b938fb4036ab29b8`, `professor_grade_09a3128fe31df8dd`, `professor_grade_ce42b26ebc8e6140`, `professor_grade_350c4b5e69351cc1` ...
- **audio_visual_sync/report_telemetry** — 5 entries: `observation_153fd8cfaaf2cae1`, `elim_b39ca7951a8cd8f8`, `observation_727df84d60f7d526`, `promo:audio_visual_sync/report_telemetry:2`, `repstat:audio_visual_sync/report_telemetry`
- **audio_visual_sync/telemetry_access** — 1 entry: `repstat:audio_visual_sync/telemetry_access`
- **audio_visual_sync/telemetry_accessors** — 5 entries: `observation_b7a437ed43c79e13`, `elim_65f84a195c149377`, `elim_71b935361cee2319`, `elim_043bb7affad30ff4`, `promo:audio_visual_sync/telemetry_accessors:1`
- **audio_visual_sync_report_telemetry_fix** — 1 entry: `observation_700fa185592de247`
- **audio_visual_sync_telemetry_fix** — 1 entry: `observation_5df7cfceb2a42bff`
- **granular_matter** — 1 entry: `repstat:granular_matter`
- **materialization** — 1 entry: `repstat:materialization`
- **matter_library** — 1 entry: `repstat:matter_library`
- **planet_averages** — 1 entry: `repstat:planet_averages`
- **solar_accretion** — 1 entry: `repstat:solar_accretion`
- **subsystem/AI** — 1 entry: `promo:subsystem/AI:1`
- **subsystem/Characters** — 1 entry: `promo:subsystem/Characters:1`
- **subsystem/Combat** — 1 entry: `promo:subsystem/Combat:1`
- **subsystem/Demo** — 1 entry: `promo:subsystem/Demo:1`
- **subsystem/Economy** — 1 entry: `promo:subsystem/Economy:1`
- **subsystem/Environment** — 1 entry: `promo:subsystem/Environment:1`
- **subsystem/Flight** — 1 entry: `promo:subsystem/Flight:1`
- **subsystem/GameMode** — 1 entry: `promo:subsystem/GameMode:1`
- **subsystem/Inventory** — 1 entry: `promo:subsystem/Inventory:1`
- **subsystem/Materials** — 1 entry: `promo:subsystem/Materials:1`
- **subsystem/Movement** — 1 entry: `promo:subsystem/Movement:1`
- **subsystem/PCG** — 1 entry: `promo:subsystem/PCG:1`
- **subsystem/Shelter** — 1 entry: `promo:subsystem/Shelter:1`
- **subsystem/Ships** — 1 entry: `promo:subsystem/Ships:1`
- **subsystem/Stations** — 1 entry: `promo:subsystem/Stations:1`
- **subsystem/Subsystems** — 1 entry: `promo:subsystem/Subsystems:1`
- **subsystem/Suit** — 1 entry: `promo:subsystem/Suit:1`
- **subsystem/Tests** — 1 entry: `promo:subsystem/Tests:1`
- **subsystem/Travel** — 1 entry: `promo:subsystem/Travel:1`
- **subsystem/VFX** — 1 entry: `promo:subsystem/VFX:1`
- **subsystem/root** — 1 entry: `promo:subsystem/root:1`
- **witness_rig** — 1 entry: `elim_41064db78ef9a045`
