# Task Board (generated — edit via `python -m core.task_board`, not by hand)

Updated 2026-07-17T03:06:20+00:00. Claim work with `python -m core.task_board claim --agent <your-id>`; the board only
grants tasks whose resource footprint is disjoint from active claims,
so claimed tasks are safe to run in parallel.

**Parallel frontier right now: 3 task(s) can proceed simultaneously.**

| id | status | pri | task | resources | agent / result |
|---|---|---|---|---|---|
| tb-0078 | open | 0.9 | Witness & collapse: Shelter_Habitat_Lighting | editor:open; excl:pie |  |
| tb-0093 | open | 0.6 | Pain verdict: ChimeraMovementComponent.h/.cpp, WeightShiftAn | Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.* |  |
| tb-0094 | open | 0.6 | Pain verdict: This session's evidence is compile-time only ( | core/game_code_generator.py; excl:generator |  |
| tb-0095 | open | 0.6 | Pain verdict: The observation_queue_processing dispatch prom | editor:open; excl:pie |  |
| tb-0079 | blocked | 1 | Build toward the seed: UGestureWheel | Source/Chimera/ProceduralGenerated/UI/** | Wrong task assigned; need to claim tb-0057 per instructions |
| tb-0005 | done | 1.5 | Hire_Audio_Sourcer (DREAM_ROSTER #7) `capable` | core/audio_sourcer.py, Content/Audio/**…; editor:open | core/audio_sourcer.py, docs/ASSET_LICENSES.md, pathway_attem |
| tb-0092 | done | 1.5 | Fix Loop 3 Sky realization: wire orphaned setup into live le | Source/Chimera/ProceduralGenerated/Sky/** | WITNESS (live PIE, 2 clean reached sessions each): sky_starf |
| tb-0099 | done | 1.5 | Realize remaining Loop 3 Sky (Earth/Moon/Sun) in live build | Source/Chimera/ProceduralGenerated/Sky/** | REALIZE REMAINING LOOP 3 SKY (Earth/Moon/Sun) tb-0099 sub-13 |
| tb-0006 | done | 1.4 | Hire_Regression_Curator (DREAM_ROSTER #6) `capable` | core/regression.py, docs/beats/** | Regression Curator (core/regression.py) built and verified:
 |
| tb-0011 | done | 1.3 | Curriculum Faculty: grow toward hundreds of checkpoints `capable` | docs/curriculum/** | Author new curriculum checkpoints in docs/curriculum/curricu |
| tb-0001 | done | 1.2 | audio_visual_sync/telemetry_accessors | Source/Chimera/ProceduralGenerated/Sound/**; editor:open; excl:pie | audio_visual_sync/telemetry_accessors: H-34 runtime attach i |
| tb-0002 | done | 1.2 | audio_visual_sync/report_telemetry | Source/Chimera/ProceduralGenerated/Sound/**; editor:open; excl:pie | audio_visual_sync/report_telemetry: H-34 runtime attach in C |
| tb-0007 | done | 1.2 | Hire_Chaos_Tester (DREAM_ROSTER #5) `capable` | core/chaos.py; editor:open; excl:pie | Created core/chaos.py for Chaos Tester (DREAM_ROSTER #5) wit |
| tb-0013 | done | 1.2 | Sprint_Input: movement state: verb flag changes the simulati | Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.* | Sprint_Input/state atom GREEN x2: SetSprinting(bool) scales  |
| tb-0057 | done | 1.2 | Fix 2 red rep atom(s): Game_Feel | Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.*, Source/Chimera/ProceduralGenerated/Sound/**; editor:open; excl:pie | rep_engine tend: subsystem_PCG no longer in failing list (wa |
| tb-0058 | done | 1.2 | Fix 2 red rep atom(s): Malcolm_Envelope | docs/envelope.json, docs/world/** | Investigation complete. Malcolm_Envelope had 2 red rep atoms |
| tb-0059 | done | 1.2 | Fix 1 red rep atom(s): Verb_Shovel | Source/Chimera/ProceduralGenerated/Interactions/**, Source/Chimera/ProceduralGenerated/Tools/** | resolved: Verb_Shovel green (13 atoms) in run_17841343390649 |
| tb-0060 | done | 1.2 | Fix 1 red rep atom(s): subsystem/Economy | core/game_code_generator.py; excl:generator | resolved: subsystem/Economy green (26 atoms) in run_17841343 |
| tb-0061 | done | 1.2 | Fix 1 red rep atom(s): subsystem/GameMode | core/game_code_generator.py; excl:generator | resolved: subsystem/GameMode green (2 atoms) in run_17841343 |
| tb-0062 | done | 1.2 | Fix 1 red rep atom(s): subsystem/PCG | core/game_code_generator.py; excl:generator | Fixed subsystem/PCG red rep atom: added UUniverseGenerationC |
| tb-0063 | done | 1.2 | Fix 1 red rep atom(s): subsystem/Ships | core/game_code_generator.py; excl:generator | resolved: subsystem/Ships green (11 atoms) in run_1784134339 |
| tb-0064 | done | 1.2 | Fix 1 red rep atom(s): subsystem/Stations | core/game_code_generator.py; excl:generator | Fixed generator core/game_code_generator.py (generate_ship_c |
| tb-0065 | done | 1.2 | Fix 1 red rep atom(s): subsystem/Travel | core/game_code_generator.py; excl:generator | tb-0065: Fixed 1 red rep atom for subsystem/Travel. atom_28f |
| tb-0066 | done | 1.2 | Fix 1 red rep atom(s): subsystem/VFX | core/game_code_generator.py; excl:generator | rep_engine tend: subsystem_VFX went from 1 red to 0 red (all |
| tb-0089 | done | 1.2 | Fix 1 red rep atom(s): Malcolm_Envelope | docs/envelope.json, docs/world/** | resolved: Malcolm_Envelope green (8 atoms) in run_1784134339 |
| tb-0090 | done | 1.2 | Fix 1 red rep atom(s): UGestureWheel | core/game_code_generator.py; excl:generator | rep_engine tend: 4 failing (was 5), UGestureWheel no longer  |
| tb-0017 | done | 1.2 | Sprint_Input: volume normalizer must exceed sprint speed | Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.* | volume_norm atom GREEN x2; normalizer = BaseMaxWalkSpeed(600 |
| tb-0018 | done | 1.2 | Sprint_Input: capture peak volume, not the decel tail | core/sleepwalker.py, docs/beats/audio_visual_sync.beats.json; editor:open; excl:pie | 5/5 beats reached, simtest_2d3122d6cefb0009 'Clean walk': pe |
| tb-0014 | done | 1.2 | Sprint_Input: input binding: the physical key drives the sta ⇐ tb-0013 | Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.*, Source/Chimera/ProceduralGenerated/GameMode/** | Sprint_Input/binding atom GREEN x2 (LeftShift polled via Pla |
| tb-0015 | done | 1.2 | Sprint_Input: harness parity: sleepwalker and bridge agree o | core/sleepwalker.py, Plugins/McpAutomationBridge/Source/** | harness_parity atom GREEN x2 from birth: Plugins tree alread |
| tb-0016 | done | 1.1 | Sprint_Input: live read-back: a beat proves the verb changed ⇐ tb-0014,tb-0015 | docs/beats/audio_visual_sync.beats.json; editor:open | READBACK PROVEN: simtest_2d3122d6cefb0009 5/5 — real LeftShi |
| tb-0008 | done | 1.1 | Hire_Lighting_Artist (DREAM_ROSTER #8) `capable` | core/lumen_rig.py; editor:open | Created core/lumen_rig.py for Lighting Artist (DREAM_ROSTER  |
| tb-0009 | done | 1 | Hire_Trailer_Director (DREAM_ROSTER #12) `capable` | core/trailer.py, Saved/Trailers/**; editor:open; excl:pie | Created core/trailer.py for Trailer Director (DREAM_ROSTER # |
| tb-0080 | done | 0.95 | Build toward the seed: UChimeraAttunementComponent | Source/Chimera/ProceduralGenerated/UI/** | Created core/audio_attunement.py with UChimeraAttunementComp |
| tb-0081 | done | 0.95 | Build toward the seed: ADotCharacter | Source/Chimera/ProceduralGenerated/UI/** | Added generate_adot_character_files() to core/game_code_gene |
| tb-0010 | done | 0.9 | Producer_Roadmap_Layer (DREAM_ROSTER #9, remaining half) `capable` | core/roadmap.py, docs/ROADMAP.md | Created core/roadmap.py for Producer Roadmap Layer (DREAM_RO |
| tb-0072 | done | 0.9 | Witness & collapse: Sky_Starfield | editor:open; excl:pie | WITNESS & COLLAPSE tb-0072 Sky_Starfield -> OUTCOME: rejecti |
| tb-0073 | done | 0.9 | Witness & collapse: Sky_Atmosphere_Scattering | editor:open; excl:pie | WITNESS & COLLAPSE tb-0073 Sky_Atmosphere_Scattering -> hone |
| tb-0074 | done | 0.9 | Witness & collapse: Tool_Scanner_Model | editor:open; excl:pie | simtest_df1a03ae03c7e517: [SIM] 0/1 beats reached in 'tool_s |
| tb-0075 | done | 0.9 | Witness & collapse: Tool_Scanner_Material | editor:open; excl:pie | Tool_Scanner_Material witness & collapse: simtest_55695e524a |
| tb-0076 | done | 0.9 | Witness & collapse: Social_Trade | editor:open; excl:pie | simtest_6eda875b25fb7be3: 2/2 beats reached in 'social_trade |
| tb-0077 | done | 0.9 | Witness & collapse: Shelter_Habitat_Materials | editor:open; excl:pie | simtest_f2856885f26a021f: 1/1 beats reached in 'shelter_habi |
| tb-0004 | done | 0.8 | Research: procedural dust-accumulation mask material creatio | docs/research/** | Research completed for procedural dust-accumulation mask mat |
| tb-0096 | done | 0.75 | Fix confirmed pain: The 54 founding checkpoints are untested | Source/Chimera/** | auto-closed: pain phase_c2b05e119221ff60:P1 already disposit |
| tb-0097 | done | 0.75 | Fix confirmed pain: walk_fast will keep failing until the Sh | Source/Chimera/** | auto-closed: pain phase_ac024b0d825b07d7:P1 already disposit |
| tb-0098 | done | 0.75 | Fix confirmed pain: A future session may assume 'the Bridge  | Source/Chimera/** | auto-closed: pain phase_c67559a04eceaec4:P2 already disposit |
| tb-0019 | done | 0.6 | Pain verdict: Distiller token-coverage will false-suppress g | docs/research/** | REFUTED phase_da55128aec6d109a:P1. Empirical vs live 160347- |
| tb-0020 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 | docs/research/** | REFUTED phase_62a9bf8fa8e97b42:P1 - DUPLICATE of phase_da551 |
| tb-0021 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 distiller token-cove | docs/research/** | STALE/ALREADY-DISPOSITIONED: phase_a3193c8fa52533c6:P1 was r |
| tb-0022 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 - Distiller token-co | docs/research/** | Pain verdict task tb-0022 for phase_da55128aec6d109a:P1 - Di |
| tb-0023 | done | 0.6 | Pain verdict: The verb TARGETS (BP_Verb_* actors) may be as  | docs/research/** | tb-0023 Pain verdict: The verb TARGETS (BP_Verb_* actors) ma |
| tb-0024 | done | 0.6 | Pain verdict: Phase 2 dependencies may still block Phase 3 w | docs/research/** | Spiral loop board shows Loop 2 Basic Verbs [DONE], Loop 3 Th |
| tb-0025 | done | 0.6 | Pain verdict: sleepwalker may still attempt PIE if runtime_r | docs/research/** | sleepwalker.py run() method checks rt = self._runtime() firs |
| tb-0026 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 | docs/research/** | phase_a06bc8140bd62718:P1 references phase_da55128aec6d109a: |
| tb-0027 | done | 0.6 | Pain verdict: The pipeline's visual stage used pyautogui des | docs/research/** | Pain verdict: The pipeline's visual stage used pyautogui des |
| tb-0029 | done | 0.6 | Pain verdict: The bridge's NOT_IMPLEMENTED on add_anim_notif | docs/research/** | Pain verdict: The bridge's NOT_IMPLEMENTED on add_anim_notif |
| tb-0030 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1, phase_762486f41e1ae | docs/research/** | Pain verdict: phase_da55128aec6d109a:P1, phase_762486f41e1ae |
| tb-0031 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1, phase_762486f41e1ae | docs/research/** | Pain verdict: phase_da55128aec6d109a:P1, phase_762486f41e1ae |
| tb-0032 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1, phase_762486f41e1ae | docs/research/** | Pain verdict: phase_da55128aec6d109a:P1, phase_762486f41e1ae |
| tb-0033 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1, phase_762486f41e1ae | docs/research/** | Pain verdict: phase_da55128aec6d109a:P1, phase_762486f41e1ae |
| tb-0034 | done | 0.6 | Pain verdict: The 20-deep observation queue will rot unobser | docs/research/** | Pain verdict: The 20-deep observation queue will rot unobser |
| tb-0035 | done | 0.6 | Pain verdict: The 20-deep observation queue will rot unobser | docs/research/** | Pain verdict: The 20-deep observation queue will rot unobser |
| tb-0036 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov | docs/research/** | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov |
| tb-0037 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov | docs/research/** | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov |
| tb-0039 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov | docs/research/** | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov |
| tb-0040 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov | docs/research/** | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov |
| tb-0041 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov | docs/research/** | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov |
| tb-0042 | done | 0.6 | Pain verdict: sleepwalker DSL/sleepwalker bridge mapping fix | docs/research/** | DSL beats already contain the reset_position and recentered  |
| tb-0043 | done | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 [distiller token-cov | docs/research/** | Distiller token-coverage suppression: 48 clusters consolidat |
| tb-0044 | done | 0.6 | Pain verdict: Observation queue holds 14 system-finalized fe | docs/research/** | Observation queue holds 22 system-finalized features awaitin |
| tb-0045 | done | 0.6 | Pain verdict: Observation queue still holds 14 system-finali | docs/research/** | Observation queue still holds 22 system-finalized features a |
| tb-0046 | done | 0.6 | Pain verdict: Niagara system status unknown - if NS_SandDust | docs/research/** | Niagara system status verified: NS_SandDust exists as Actor_ |
| tb-0047 | done | 0.6 | Pain verdict: Niagara system may not exist (creating from sc | docs/research/** | Niagara system verified: NS_SandDust exists as Actor_NS_Sand |
| tb-0048 | done | 0.6 | Pain verdict: Audit workflow consolidation step had script f | docs/research/** | Audit workflow consolidation step script filtering error (nu |
| tb-0049 | done | 0.6 | Pain verdict: Tier-1 organs (scholar/muse/visionkeeper) are  | docs/research/** | Tier-1 organs (scholar/muse/visionkeeper) are hired with rea |
| tb-0050 | done | 0.6 | Pain verdict: The IsAnimationAuthoringAction dual-routing tr | docs/research/** | The IsAnimationAuthoringAction dual-routing trap (McpConsoli |
| tb-0051 | done | 0.6 | Pain verdict: A future research/redesign cycle on the newly- | docs/research/** | verb_interactions sleepwalker achieved 9/9 beats with a 'Cle |
| tb-0052 | done | 0.6 | Pain verdict: H-12's changes (graphify_interface.py, build_o | docs/research/** | H-12's changes (graphify_interface.py extract_ubt_failure_li |
| tb-0053 | done | 0.6 | Pain verdict: No live UBT rebuild has ever exercised this ex | docs/research/** | H-12's changes verified via monkeypatched unit tests per AGE |
| tb-0054 | done | 0.6 | Pain verdict: core/gardener.py's tend() status-matching mis- | docs/research/** | gardener.py dry-run confirmed: H-9 (vetoed-auto (tombstone 2 |
| tb-0055 | done | 0.6 | Pain verdict: A future session may assume 'the Bridge Engine | docs/research/** | Pain verdict confirmed: Bridge Engineer backlog fix for add_ |
| tb-0056 | done | 0.6 | Pain verdict: WeightShiftAnimationTests.cpp compiles clean b | docs/research/** | Pain verdict confirmed: WeightShiftAnimationTests.cpp compil |
| tb-0003 | done | 0.4 | Verb_Shovel | Source/Chimera/ProceduralGenerated/Interactions/**, Source/Chimera/ProceduralGenerated/Tools/**; editor:open; excl:pie | Verb_Shovel: Implemented ATool_Shovel::Dig() (was rejected e |
| tb-0012 | done | 0.01 | Gauntlet sandbox: fable-5 | docs/gauntlet/fable-5/** | wrote docs/gauntlet/fable-5/tunnel_note.md per recipe: one p |
| tb-0028 | done | 0.01 | Gauntlet sandbox: haiku-1 | docs/gauntlet/haiku-1/** | docs/gauntlet/haiku-1/tunnel_note.md (one paragraph explaini |
| tb-0038 | done | 0.01 | Gauntlet sandbox: pi-agent-1 | docs/gauntlet/pi-agent-1/** | docs/gauntlet/pi-agent-1/tunnel_note.md |
| tb-0067 | abandoned | 0.9 | Witness & collapse: Sky_Earth_Model | editor:open; excl:pie |  |
| tb-0068 | abandoned | 0.9 | Witness & collapse: Sky_Earth_Material | editor:open; excl:pie |  |
| tb-0069 | abandoned | 0.9 | Witness & collapse: Sky_Moon_Model | editor:open; excl:pie |  |
| tb-0070 | abandoned | 0.9 | Witness & collapse: Sky_Moon_Material | editor:open; excl:pie |  |
| tb-0071 | abandoned | 0.9 | Witness & collapse: Sky_Sun_Lighting | editor:open; excl:pie |  |
| tb-0082 | abandoned | 0.8 | Build toward the seed: FFootstepEvent | Source/Chimera/ProceduralGenerated/UI/** |  |
| tb-0083 | abandoned | 0.8 | Build toward the seed: FGestureEvent | Source/Chimera/ProceduralGenerated/UI/** |  |
| tb-0084 | abandoned | 0.75 | Build toward the seed: UWeatherSubsystem | Source/Chimera/ProceduralGenerated/UI/** |  |
| tb-0085 | abandoned | 0.75 | Build toward the seed: AErisaidActor | Source/Chimera/ProceduralGenerated/UI/** |  |
| tb-0086 | abandoned | 0.75 | Build toward the seed: AHabitatActor | Source/Chimera/ProceduralGenerated/UI/** |  |
| tb-0087 | abandoned | 0.75 | Build toward the seed: FStar | Source/Chimera/ProceduralGenerated/UI/** |  |
| tb-0088 | abandoned | 0.75 | Build toward the seed: UStarMemorialSubsystem | Source/Chimera/ProceduralGenerated/UI/** |  |
| tb-0091 | abandoned | 0.75 | Build toward the seed: USacrificeLogComponent | Source/Chimera/ProceduralGenerated/UI/** |  |
