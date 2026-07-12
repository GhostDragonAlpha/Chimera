# Task Board (generated — edit via `python -m core.task_board`, not by hand)

Updated 2026-07-12T22:22:19+00:00. Claim work with `python -m core.task_board claim --agent <your-id>`; the board only
grants tasks whose resource footprint is disjoint from active claims,
so claimed tasks are safe to run in parallel.

**Parallel frontier right now: 7 task(s) can proceed simultaneously.**

| id | status | pri | task | resources | agent / result |
|---|---|---|---|---|---|
| tb-0005 | open | 1.5 | Hire_Audio_Sourcer (DREAM_ROSTER #7) `capable` | core/audio_sourcer.py, Content/Audio/**…; editor:open |  |
| tb-0006 | open | 1.4 | Hire_Regression_Curator (DREAM_ROSTER #6) `capable` | core/regression.py, docs/beats/** |  |
| tb-0011 | open | 1.3 | Curriculum Faculty: grow toward hundreds of checkpoints `capable` | docs/curriculum/** |  |
| tb-0007 | open | 1.2 | Hire_Chaos_Tester (DREAM_ROSTER #5) `capable` | core/chaos.py; editor:open; excl:pie |  |
| tb-0008 | open | 1.1 | Hire_Lighting_Artist (DREAM_ROSTER #8) `capable` | core/lumen_rig.py; editor:open |  |
| tb-0009 | open | 1 | Hire_Trailer_Director (DREAM_ROSTER #12) `capable` | core/trailer.py, Saved/Trailers/**; editor:open; excl:pie |  |
| tb-0010 | open | 0.9 | Producer_Roadmap_Layer (DREAM_ROSTER #9, remaining half) `capable` | core/roadmap.py, docs/ROADMAP.md |  |
| tb-0019 | open | 0.6 | Pain verdict: Distiller token-coverage will false-suppress g | docs/research/** |  |
| tb-0020 | open | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 | docs/research/** |  |
| tb-0021 | open | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 distiller token-cove | docs/research/** |  |
| tb-0022 | open | 0.6 | Pain verdict: phase_da55128aec6d109a:P1 - Distiller token-co | docs/research/** |  |
| tb-0023 | open | 0.6 | Pain verdict: The verb TARGETS (BP_Verb_* actors) may be as  | docs/research/** |  |
| tb-0024 | open | 0.6 | Pain verdict: Phase 2 dependencies may still block Phase 3 w | docs/research/** |  |
| tb-0001 | blocked | 1.2 | audio_visual_sync/telemetry_accessors | Source/Chimera/ProceduralGenerated/Sound/**; editor:open; excl:pie | Releasing to allow other agent to continue |
| tb-0002 | blocked | 1.2 | audio_visual_sync/report_telemetry | Source/Chimera/ProceduralGenerated/Sound/**; editor:open; excl:pie | Releasing to enable parallel work on ground features and cre |
| tb-0004 | blocked | 0.8 | Research: procedural dust-accumulation mask material creatio | docs/research/** | No parallel-safe open task for research writer |
| tb-0003 | blocked | 0.4 | Verb_Shovel | Source/Chimera/ProceduralGenerated/Interactions/**, Source/Chimera/ProceduralGenerated/Tools/**; editor:open; excl:pie | Releasing to enable parallel work on conversational loops an |
| tb-0013 | done | 1.2 | Sprint_Input: movement state: verb flag changes the simulati | Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.* | Sprint_Input/state atom GREEN x2: SetSprinting(bool) scales  |
| tb-0017 | done | 1.2 | Sprint_Input: volume normalizer must exceed sprint speed | Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.* | volume_norm atom GREEN x2; normalizer = BaseMaxWalkSpeed(600 |
| tb-0018 | done | 1.2 | Sprint_Input: capture peak volume, not the decel tail | core/sleepwalker.py, docs/beats/audio_visual_sync.beats.json; editor:open; excl:pie | 5/5 beats reached, simtest_2d3122d6cefb0009 'Clean walk': pe |
| tb-0014 | done | 1.2 | Sprint_Input: input binding: the physical key drives the sta ⇐ tb-0013 | Source/Chimera/ProceduralGenerated/ChimeraMovementComponent.*, Source/Chimera/ProceduralGenerated/GameMode/** | Sprint_Input/binding atom GREEN x2 (LeftShift polled via Pla |
| tb-0015 | done | 1.2 | Sprint_Input: harness parity: sleepwalker and bridge agree o | core/sleepwalker.py, Plugins/McpAutomationBridge/Source/** | harness_parity atom GREEN x2 from birth: Plugins tree alread |
| tb-0016 | done | 1.1 | Sprint_Input: live read-back: a beat proves the verb changed ⇐ tb-0014,tb-0015 | docs/beats/audio_visual_sync.beats.json; editor:open | READBACK PROVEN: simtest_2d3122d6cefb0009 5/5 — real LeftShi |
| tb-0012 | done | 0.01 | Gauntlet sandbox: fable-5 | docs/gauntlet/fable-5/** | wrote docs/gauntlet/fable-5/tunnel_note.md per recipe: one p |
