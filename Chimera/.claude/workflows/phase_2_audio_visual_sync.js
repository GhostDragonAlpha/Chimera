export const meta = {
  name: 'phase-2-audio-visual-sync',
  description: 'Phase 2 (Weeks 3-4): Audio-Visual Synchronization + Emergent Complexity. Critical path: Ground_Sand_Particles audio-visual coupling (<100ms latency). Parallel: Player Character servo sounds + weight-shift animation. Emergent complexity: surface erosion + geothermal vents.',
  phases: [
    { title: 'Audio-Visual Sync Verification', detail: 'Validate Phase 1 results: footstep audio latency <100ms, volume scaling working' },
    { title: 'Loop 0 Micro-Feedback Polish', detail: 'Servo sounds, weight-shift animation, visor micro-feedback' },
    { title: 'Emergent Complexity Implementation', detail: 'Surface erosion from footfalls, geothermal vent discovery, difficulty progression' },
    { title: 'Measurement & Grading', detail: 'Acceptance tests on all 9 Loop 0/1 features with Phase 2 improvements' },
  ],
}

// Phase 2: Audio-Visual Sync + Emergent Complexity (Weeks 3-4)
// Depends on Phase 1 delivering: Niagara loaded, wind integrated, accumulation material wired
// This workflow implements THE critical dimensions for AAA enjoyment: immersion + systems depth

phase('Audio-Visual Sync Verification')

log('Phase 2 Starting: Audio-Visual Sync Verification + Emergent Complexity Implementation')

// Verify Phase 1 audio-visual sync is working before moving to Phase 2 enhancements
const audioVisualVerification = await agent(
  `VERIFY Phase 1 Audio-Visual Sync Implementation\n\n` +
  `Task: Confirm Phase 1 implementation completed audio-visual sync on Ground_Sand_Particles\n\n` +
  `Verification Checklist:\n` +
  `1. Footstep audio trigger latency: <100ms (goal: 16-33ms @ 60fps)\n` +
  `2. Volume scaling: Sprint louder than run louder than walk\n` +
  `3. Surface-specific sounds: Sand/rock/metal distinct audio cues\n` +
  `4. Particle spawn: Synchronized dust particles with audio event\n` +
  `5. Sleepwalker beat: Walk/run/sprint verified in beat script\n\n` +
  `Evidence Needed:\n` +
  `- Latency measurement (timestamp audio event vs particle spawn)\n` +
  `- Volume level readings per movement speed\n` +
  `- Audio log showing surface-specific cues\n` +
  `- Screenshot of particles + audio waveform sync\n\n` +
  `Return: { phase_1_audio_visual_complete, latency_ms, volume_scaling_working, surfaces_audio_mapped, ready_for_phase_2 }\n\n` +
  `BLOCKING: If audio-visual sync not complete, Phase 2 cannot proceed with immersion enhancements.`,
  {
    label: 'phase2:audio-visual-verification',
    phase: 'Audio-Visual Sync Verification',
    schema: {
      type: 'object',
      properties: {
        phase_1_audio_visual_complete: { type: 'boolean' },
        latency_ms: { type: 'number' },
        within_aaa_standard: { type: 'boolean' },
        volume_scaling_working: { type: 'boolean' },
        surfaces_audio_mapped: { type: 'array', items: { type: 'string' } },
        ground_sand_particles_immersion_score: { type: 'integer', description: '0-50 on AAA scale' },
        ready_for_phase_2: { type: 'boolean' }
      }
    }
  }
)

log(`Audio-visual sync verified: ${audioVisualVerification?.phase_1_audio_visual_complete ? 'YES' : 'NO'} (latency ${audioVisualVerification?.latency_ms}ms)`)

if (!audioVisualVerification?.phase_1_audio_visual_complete) {
  log('WARNING: Phase 1 audio-visual sync incomplete. Cannot proceed with Phase 2.')
  return { status: 'blocked', reason: 'phase_1_audio_visual_sync_incomplete' }
}

phase('Loop 0 Micro-Feedback Polish')

// Loop 0: Enhance Player Character immersion with servo sounds + weight shifts
const loop0Enhancements = await parallel([
  () => agent(
    `Enhance Player Character: Servo Sounds Implementation\n\n` +
    `Current State: Player_Character_Model 97% (golden standard), but lacking micro-feedback\n` +
    `Task: Add high-frequency servo/pneumatic sounds on movement (suit actuators)\n\n` +
    `Implementation:\n` +
    `1. Create/load servo sound effect (UE5 Synthesis or external audio cue)\n` +
    `2. Trigger on Verb_Step with volume proportional to speed:\n` +
    `   - Walk: quiet (10% volume)\n` +
    `   - Run: medium (30% volume)\n` +
    `   - Sprint: loud (50% volume)\n` +
    `3. Pitch variation: Higher pitch on faster movement\n` +
    `4. Non-diegetic mix: Servo audio is subtle background feedback (not dialogue)\n` +
    `5. Test: Sleepwalker beat - walk/run/sprint, verify audio feedback responsive to speed\n` +
    `6. Measure: Player_Character_Model immersion score should increase 97% -> 98%+\n\n` +
    `Return: { servo_sounds_implemented, volume_scaling_working, pitch_variation, aaa_feedback_quality, immersion_score_gain }`,
    {
      label: 'phase2:servo-sounds',
      phase: 'Loop 0 Micro-Feedback Polish',
      schema: {
        type: 'object',
        properties: {
          servo_sounds_implemented: { type: 'boolean' },
          volume_scaling_working: { type: 'boolean' },
          pitch_variation_working: { type: 'boolean' },
          feedback_quality: { type: 'string', enum: ['AAA', 'high', 'moderate', 'placeholder'] },
          immersion_score_gain_percent: { type: 'integer' }
        }
      }
    }
  ),
  () => agent(
    `Enhance Player Character: Weight-Shift Animation\n\n` +
    `Current State: Player_Character_Model 97%, but noted 'slight mechanical stiffness'\n` +
    `Task: Add subtle weight-shift arcs to character animation on turns/stops\n\n` +
    `Implementation:\n` +
    `1. Modify animation blueprint root motion: Add weight-shift curve on state transitions\n` +
    `2. Fast turn behavior: Character leans back slightly, then settles forward\n` +
    `3. Stop behavior: Momentum overshoot followed by settle (6-8 frame recovery)\n` +
    `4. Magnitude: <5cm offset (believable, not cartoonish)\n` +
    `5. Animation curve: Ease-out settlement (natural deceleration feel)\n` +
    `6. Test: Sprint in circle, hard stop - character should sway, recover\n` +
    `7. Measure: Animation juice score increase (0/8 -> 6/8 with overshoot + settle)\n\n` +
    `Return: { weight_shift_implemented, overshoot_magnitude_cm, believability_score, animation_juice_gain, issues }`,
    {
      label: 'phase2:weight-shift',
      phase: 'Loop 0 Micro-Feedback Polish',
      schema: {
        type: 'object',
        properties: {
          weight_shift_implemented: { type: 'boolean' },
          overshoot_magnitude_cm: { type: 'number' },
          believability_score: { type: 'integer', minimum: 0, maximum: 10 },
          animation_juice_gain_percent: { type: 'integer' },
          issues: { type: 'array', items: { type: 'string' } }
        }
      }
    }
  )
])

log(`Loop 0 enhancements: servo=${loop0Enhancements[0]?.servo_sounds_implemented ? 'done' : 'pending'}, weight-shift=${loop0Enhancements[1]?.weight_shift_implemented ? 'done' : 'pending'}`)

phase('Emergent Complexity Implementation')

// Critical: Emergent complexity + systems depth for Loop 1 (Ground Environment)
const emergentComplexity = await parallel([
  () => agent(
    `Implement Surface Erosion from Player Footfalls\n\n` +
    `Context: Ground_Sand_Particles currently 65% enjoyment (after Phase 1). Emergent complexity (0/10) is missing.\n` +
    `Task: Add surface erosion mechanic - repeated footfalls create visible paths\n\n` +
    `Implementation:\n` +
    `1. Track footstep positions over time (spatial accumulation array)\n` +
    `2. Frequency-based erosion: More footsteps = deeper worn path\n` +
    `3. Visual effect: Dust/sand compaction shader on worn areas (darker/different texture)\n` +
    `4. Persistence: Erosion patterns remain for 5+ minutes of gameplay (not instant reset)\n` +
    `5. Physics: Worn paths create slight height variation (player can walk along paths, off-path is harder)\n` +
    `6. Test: Walk in circle 10x, observe path forming; walk different route, observe dual paths\n` +
    `7. Measure: Systems depth 10/30 -> 18/30 (mechanical interdependencies + emergent patterns visible)\n\n` +
    `Return: { surface_erosion_implemented, path_visibility, persistence_seconds, physics_interaction, systems_depth_gain }`,
    {
      label: 'phase2:surface-erosion',
      phase: 'Emergent Complexity Implementation',
      schema: {
        type: 'object',
        properties: {
          surface_erosion_implemented: { type: 'boolean' },
          path_visibility: { type: 'boolean', description: 'Are worn paths visually distinct?' },
          persistence_seconds: { type: 'integer' },
          physics_interaction: { type: 'boolean', description: 'Do worn paths affect traversal?' },
          systems_depth_gain_percent: { type: 'integer' }
        }
      }
    }
  ),
  () => agent(
    `Implement Geothermal Vent Discovery Mechanic\n\n` +
    `Context: Ground surfaces need emergent complexity + world-building narrative\n` +
    `Task: Add hidden geothermal vents discoverable by exploration and erosion\n\n` +
    `Implementation:\n` +
    `1. Scattered geothermal vent actors beneath sand surface (not visible initially)\n` +
    `2. Discovery triggers: Player walks over vent location repeatedly (erosion reveals it) OR uses Tool_Scanner\n` +
    `3. Visual reveal: Heat shimmer effect emerges, dust swirls around vent, ground cracks slightly\n` +
    `4. Audio reveal: Low-frequency rumble + steam hiss sound (diegetic)\n` +
    `5. Gameplay impact: Vent locations are environmental hazards (heat damage) and resource sites (geothermal energy)\n` +
    `6. Test: Walk repeatedly over vent area until discovery, then use scanner on different vent\n` +
    `7. Measure: Emergent complexity (0/10 -> 6/10), systems depth (+interdependency: movement + discovery + hazards)\n\n` +
    `Return: { geothermal_vents_implemented, discovery_triggers_working, visual_audio_reveals, hazard_mechanic, emergent_complexity_gain }`,
    {
      label: 'phase2:geothermal-vents',
      phase: 'Emergent Complexity Implementation',
      schema: {
        type: 'object',
        properties: {
          geothermal_vents_implemented: { type: 'boolean' },
          discovery_by_erosion_working: { type: 'boolean' },
          discovery_by_scanner_working: { type: 'boolean' },
          visual_audio_reveals_working: { type: 'boolean' },
          hazard_mechanic_functional: { type: 'boolean' },
          emergent_complexity_gain_percent: { type: 'integer' }
        }
      }
    }
  ),
  () => agent(
    `Implement Difficulty Progression: Plains -> Craters -> Highlands -> Badlands\n\n` +
    `Context: Gameplay flow (15/40) needs clear progression and hazard variety\n` +
    `Task: Design ground progression zones with increasing hazards and challenge\n\n` +
    `Implementation:\n` +
    `Zone 1 - Plains (starting area):\n` +
    `  - Flat terrain, no hazards\n` +
    `  - Tutorial path clearly marked\n` +
    `  - Geothermal vents rare (1-2 in zone)\n\n` +
    `Zone 2 - Craters (medium difficulty):\n` +
    `  - Crater formations create elevation changes\n` +
    `  - Geothermal vents common (5-10 in zone)\n` +
    `  - Dust storms occasional (every 2-3 minutes)\n\n` +
    `Zone 3 - Highlands (high difficulty):\n` +
    `  - Steep slopes, challenging navigation\n` +
    `  - Geothermal vents frequent (10+ in zone)\n` +
    `  - Dust storms common, visibility reduced\n\n` +
    `Zone 4 - Badlands (extreme difficulty):\n` +
    `  - Jagged terrain, deep crevasses\n` +
    `  - Geothermal vents everywhere, high heat damage\n` +
    `  - Constant dust storms, near-zero visibility\n\n` +
    `7. Test: Walk progression from Plains -> Badlands, observe hazard escalation\n` +
    `8. Measure: Gameplay flow 15/40 -> 28/40 (pacing + progression + difficulty tuning)\n\n` +
    `Return: { difficulty_progression_implemented, zones_hazard_escalation, player_progression_satisfying, gameplay_flow_gain }`,
    {
      label: 'phase2:difficulty-progression',
      phase: 'Emergent Complexity Implementation',
      schema: {
        type: 'object',
        properties: {
          difficulty_progression_implemented: { type: 'boolean' },
          zones_count: { type: 'integer' },
          hazard_escalation_working: { type: 'boolean' },
          player_progression_satisfying: { type: 'boolean' },
          gameplay_flow_gain_percent: { type: 'integer' }
        }
      }
    }
  )
])

log(`Emergent complexity: surface_erosion=${emergentComplexity[0]?.surface_erosion_implemented ? 'done' : 'pending'}, geothermal=${emergentComplexity[1]?.geothermal_vents_implemented ? 'done' : 'pending'}, progression=${emergentComplexity[2]?.difficulty_progression_implemented ? 'done' : 'pending'}`)

phase('Measurement & Grading')

// Final grading sweep for Phase 2 results
const phase2Grading = await agent(
  `Phase 2 Final Grade Sweep: All 9 Loop 0/1 Features\n\n` +
  `Using result_grader_aaa_expanded with Phase 2 improvements:\n\n` +
  `Loop 0 (Player Character) - Expected improvements:\n` +
  `- Servo sounds + weight-shift animation added\n` +
  `- Player_Character_Model: 97% -> 98%+ (micro-feedback complete)\n` +
  `- Player_Character_Animation: 82% -> 87%+ (animation juice + overshoot)\n` +
  `- Player_Character_Suit: 72% -> 78%+ (servo feedback + weight shifting)\n` +
  `- Player_Character_Lighting: 78% -> 82%+ (consistent with other enhancements)\n` +
  `- Loop 0 avg: 77%+ -> 85%+ TARGET MET\n\n` +
  `Loop 1 (Ground) - Expected improvements:\n` +
  `- Audio-visual sync complete, emergent complexity added\n` +
  `- Ground_Sand_Particles: 65% -> 75%+ (immersion + systems depth)\n` +
  `- Ground_Sand_Footprints: TBD -> 70%+ (erosion paths, discovery)\n` +
  `- All ground surfaces: ~70% (difficulty progression, geothermal discovery)\n` +
  `- Loop 1 avg: 75%+ -> 80%+ (on track for 85%+ by Phase 3)\n\n` +
  `Task:\n` +
  `1. Grade each feature with Phase 2 evidence\n` +
  `2. Calculate Loop 0/1 avg fidelity + AAA enjoyment %\n` +
  `3. Confirm targets met (Loop 0 85%+, Loop 1 on track for 80%+)\n` +
  `4. Generate study guides for Phase 3 (production quality: audio design, visual fidelity, animation juice)\n` +
  `5. Prepare Phase 3 handoff data\n\n` +
  `Return: { loop0_avg_percent, loop0_target_met, loop1_avg_percent, loop1_on_track, phase3_priorities, ready_for_phase_3 }`,
  {
    label: 'phase2:final-grading',
    phase: 'Measurement & Grading',
    schema: {
      type: 'object',
      properties: {
        loop0_avg_percent: { type: 'number' },
        loop0_target_met: { type: 'boolean' },
        loop1_avg_percent: { type: 'number' },
        loop1_on_track: { type: 'boolean' },
        critical_path_status: { type: 'string' },
        phase3_priorities: { type: 'array', items: { type: 'string' } },
        ready_for_phase_3: { type: 'boolean' }
      }
    }
  }
)

log(`Phase 2 Complete:`)
log(`- Loop 0 avg: ${(phase2Grading?.loop0_avg_percent || 0).toFixed(0)}% (target: 85%+)`)
log(`- Loop 1 avg: ${(phase2Grading?.loop1_avg_percent || 0).toFixed(0)}% (target: 80%+)`)
log(`- Phase 3 ready: ${phase2Grading?.ready_for_phase_3 ? 'YES' : 'NO'}`)

return {
  phase: 'Phase 2: Audio-Visual Sync + Emergent Complexity',
  audio_visual_sync_verified: audioVisualVerification?.phase_1_audio_visual_complete,
  loop0_servo_sounds: loop0Enhancements[0]?.servo_sounds_implemented,
  loop0_weight_shift: loop0Enhancements[1]?.weight_shift_implemented,
  emergent_surface_erosion: emergentComplexity[0]?.surface_erosion_implemented,
  emergent_geothermal_vents: emergentComplexity[1]?.geothermal_vents_implemented,
  emergent_difficulty_progression: emergentComplexity[2]?.difficulty_progression_implemented,
  loop0_avg_percent: phase2Grading?.loop0_avg_percent,
  loop0_target_85_percent_met: phase2Grading?.loop0_target_met,
  loop1_avg_percent: phase2Grading?.loop1_avg_percent,
  loop1_on_track_for_80_percent: phase2Grading?.loop1_on_track,
  phase_3_ready: phase2Grading?.ready_for_phase_3,
  phase_3_priorities: phase2Grading?.phase3_priorities
}
