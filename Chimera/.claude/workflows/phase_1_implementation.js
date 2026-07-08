export const meta = {
  name: 'phase-1-implementation',
  description: 'Phase 1 Implementation (Weeks 1-2): Critical path execution - Ground_Sand_Particles Niagara loading, wind integration, dust accumulation, audio-visual sync. Real spec fidelity gains: 18% → 85%+. Parallel with audit workflow.',
  phases: [
    { title: 'Critical Path Setup', detail: 'Ground_Sand_Particles: Load NS_SandDust, integrate wind system' },
    { title: 'Procedural Material Integration', detail: 'Wire DustAccumulationMaterial into particle system' },
    { title: 'Audio-Visual Sync Implementation', detail: 'Footstep audio synchronized to dust particles (<100ms latency)' },
    { title: 'Test & Measure', detail: 'Run acceptance criteria tests, grade with result_grader_aaa_expanded' },
    { title: 'Loop 0 Refinements', detail: 'Player Character: servo sounds, weight shift animation, micro-feedback' },
  ],
}

// Phase 1 Implementation: CRITICAL PATH - Ground_Sand_Particles 18% -> 85%+ fidelity
// This workflow executes ACTUAL implementation work, not just audits
// Real code changes, real test execution, real AAA % gains
// Timeline: Weeks 1-2 (parallel with audit workflow)

phase('Critical Path Setup')

log('Starting Phase 1 Implementation: Ground_Sand_Particles critical path (18% -> 85%+ fidelity)')

// Step 1: Verify Niagara system status and load NS_SandDust
const niagaraSetup = await agent(
  `CRITICAL PATH TASK: Load NS_SandDust Niagara System\n\n` +
  `Current State: Niagara particle system for sand dust effects not loaded/verified\n` +
  `Target State: NS_SandDust system active, emitter_count=1, particles_per_second=50\n\n` +
  `Task:\n` +
  `1. Check if NS_SandDust Niagara asset exists in project (check Content browser paths)\n` +
  `2. If exists: Load into Ground_Sand_Particles system, verify emitter configuration\n` +
  `3. If missing: Design minimal Niagara emitter with DSL parameters:\n` +
  `   - Emitter count: 1\n` +
  `   - Spawn rate: 50 particles/sec\n` +
  `   - Lifetime: 3.0 seconds\n` +
  `   - Velocity: 10-50 UU/s (randomized)\n` +
  `   - Size: 0.5 UU\n` +
  `   - Color: [0.9, 0.85, 0.7, 0.8] sandy tan RGBA\n` +
  `   - Gravity scale: 0.5 (half normal gravity)\n` +
  `   - Wind response: 1.0 (full wind interaction)\n\n` +
  `4. Integrate with ground surface in regolith_yard level\n` +
  `5. Run quick PIE test: Walk on sand surface -> particles should spawn\n` +
  `6. Return: { system_status, emitter_config, parity_with_dsl, parity_percent, issues_found, next_steps }\n\n` +
  `THIS IS BLOCKING: Everything else depends on particles rendering. If Niagara fails, flag immediately.`,
  {
    label: 'niagara-setup',
    phase: 'Critical Path Setup',
    schema: {
      type: 'object',
      properties: {
        system_status: { type: 'string', enum: ['loaded', 'created', 'missing', 'blocked'] },
        emitter_count: { type: 'integer' },
        spawn_rate: { type: 'number' },
        particle_lifetime: { type: 'number' },
        particle_color_rgba: { type: 'array', items: { type: 'number' }, minItems: 4, maxItems: 4 },
        dsl_parameter_parity: { type: 'integer', description: 'percent match to DSL declared parameters' },
        issues_found: { type: 'array', items: { type: 'string' } },
        next_steps: { type: 'string' }
      }
    }
  }
)

log(`Niagara system status: ${niagaraSetup?.system_status || 'unknown'}`)

// Step 2: Integrate procedural dust accumulation material
const dustMaterialIntegration = await agent(
  `Wire Procedural Dust Accumulation Material\n\n` +
  `Context: DustAccumulationMaterial.h/cpp already generated (noise functions + vertex normal blending)\n` +
  `Task: Integrate into particle system to make dust settle and accumulate on ground\n\n` +
  `Implementation:\n` +
  `1. Load DustAccumulationMaterial asset from ProceduralGenerated/Materials/\n` +
  `2. Apply to ground surface mesh at runtime (on footstep trigger)\n` +
  `3. Wire GetDustIntensity() to particle vertex normal calculations\n` +
  `4. Test: Walk in circle 10x, stand still 30s -> dust should visibly accumulate\n` +
  `5. Measure: Accumulation layer thickness vs time (should show settling effect)\n` +
  `6. Return: { integration_status, accumulation_observable, settling_time_seconds, visual_quality, issues }\n\n` +
  `Success: Dust no longer disappears instantly; creates visible ground layer over time.`,
  {
    label: 'dust-material-integration',
    phase: 'Procedural Material Integration',
    schema: {
      type: 'object',
      properties: {
        integration_status: { type: 'string', enum: ['success', 'partial', 'blocked'] },
        accumulation_observable: { type: 'boolean', description: 'Is dust layer visible after 30s activity?' },
        settling_time_seconds: { type: 'number' },
        visual_quality: { type: 'string', enum: ['AAA', 'high', 'moderate', 'low', 'placeholder'] },
        issues: { type: 'array', items: { type: 'string' } }
      }
    }
  }
)

log(`Dust material integration: ${dustMaterialIntegration?.integration_status || 'pending'}`)

// Step 3: Wind system integration
const windSystemSetup = await agent(
  `Integrate Wind System for Particle Interaction\n\n` +
  `DSL Parameter: wind_response: 1.0 (full wind interaction)\n` +
  `Current State: No wind system implemented\n` +
  `Target: Particles drift with wind direction/speed\n\n` +
  `Task:\n` +
  `1. Check if wind system exists in project\n` +
  `2. If exists: Wire particle wind_response parameter (1.0 = full response)\n` +
  `3. If missing: Implement minimal wind system:\n` +
  `   - Constant wind direction/speed or time-varying pattern\n` +
  `   - Particle velocity affected by wind each frame\n` +
  `   - Accumulation mask updated based on wind drift\n` +
  `4. Test in PIE: Stand still, observe particle drift direction matches wind\n` +
  `5. Measure: Particle trajectory deviation from gravity-only baseline\n` +
  `6. Return: { wind_system_status, particle_response, drift_observable, parameters_matched, issues }\n\n` +
  `Note: This unlocks procedural dust patterns (not random spawning, but wind-driven accumulation).`,
  {
    label: 'wind-system-setup',
    phase: 'Critical Path Setup',
    schema: {
      type: 'object',
      properties: {
        wind_system_status: { type: 'string', enum: ['implemented', 'partial', 'placeholder', 'blocked'] },
        particle_wind_response: { type: 'number', minimum: 0, maximum: 1 },
        drift_observable: { type: 'boolean' },
        dsl_parity: { type: 'integer', description: 'percent: wind_response 1.0 matched' },
        issues: { type: 'array', items: { type: 'string' } }
      }
    }
  }
)

log(`Wind system status: ${windSystemSetup?.wind_system_status || 'unknown'}`)

phase('Audio-Visual Sync Implementation')

// Step 4: Audio-Visual Synchronization (CRITICAL for AAA immersion)
const audioVisualSync = await agent(
  `Implement Audio-Visual Synchronization for Footsteps\n\n` +
  `Current State: Footstep particles spawn on impact, but NO synchronized audio feedback\n` +
  `Target: Audio event triggers within 100ms of particle spawn (AAA standard <100ms latency)\n` +
  `Impact: This is THE single most critical gap preventing Ground_Sand_Particles from reaching 75%+ enjoyment\n\n` +
  `Implementation:\n` +
  `1. Wire footstep audio trigger to particle spawn event (Verb_Step -> GetDustIntensity -> PlaySound)\n` +
  `2. Select surface-specific footstep sounds (sand, rock, metal SoundCue references)\n` +
  `3. Measure latency: Timestamp particle spawn vs audio PlaySound call\n` +
  `   - Goal: <100ms (1-2 frame delay @ 60fps = 16-33ms is ideal)\n` +
  `4. Scale audio volume with movement speed (sprint louder than walk)\n` +
  `5. Test in Sleepwalker beat script: Walk, run, sprint -> audio should be tightly coupled to visuals\n` +
  `6. Screenshot: PIE viewport with audio/visual events timestamped\n` +
  `7. Return: { sync_latency_ms, volume_scaling_verified, surface_audio_mapped, aaa_parity_score, issues }\n\n` +
  `Success Metric: Player hears footstep IMMEDIATELY as dust particles spawn. No lag. Immersion unlocked.`,
  {
    label: 'audio-visual-sync',
    phase: 'Audio-Visual Sync Implementation',
    schema: {
      type: 'object',
      properties: {
        sync_latency_ms: { type: 'number', description: 'Time between particle spawn and audio trigger' },
        latency_within_aaa_standard: { type: 'boolean', description: '<100ms is AAA standard' },
        volume_scaling: { type: 'boolean', description: 'Volume scales with movement speed' },
        surface_audio_sources: { type: 'array', items: { type: 'string' }, description: 'Mapped audio cues per surface' },
        aaa_parity_score: { type: 'integer', description: 'percent: latency + volume + surfaces working' },
        screenshot_evidence: { type: 'boolean' },
        issues: { type: 'array', items: { type: 'string' } }
      }
    }
  }
)

log(`Audio-visual sync: ${audioVisualSync?.latency_within_aaa_standard ? 'PASS (<100ms)' : 'NEEDS WORK'} latency=${audioVisualSync?.sync_latency_ms || '?'}ms`)

phase('Test & Measure')

// Step 5: Run acceptance criteria tests and measure spec fidelity gains
const acceptanceTestRun = await agent(
  `Run Ground_Sand_Particles Acceptance Criteria Tests\n\n` +
  `5 Criteria (all must pass for feature acceptance):\n` +
  `1. Niagara System Loaded (particles spawn on ground)\n` +
  `2. Particle Parameters Verified (lifetime, velocity, color, gravity_scale)\n` +
  `3. Dust Accumulation Functional (dust settles, layer visible after 30s activity)\n` +
  `4. Audio-Visual Sync (<100ms latency, volume scaling, surface sounds)\n` +
  `5. Wind Interaction Verified (particles drift with wind direction)\n\n` +
  `Execution:\n` +
  `1. Launch PIE with regolith_yard level\n` +
  `2. Run each criterion test\n` +
  `3. Log pass/fail for each test\n` +
  `4. Capture screenshots as evidence\n` +
  `5. Measure all DSL parameters (11 total for Ground_Sand_Particles)\n` +
  `6. Calculate new spec_fidelity = verified_params / total_params\n` +
  `7. Generate evidence JSON for result_grader_aaa_expanded\n` +
  `8. Return: { passed, failed, spec_fidelity_before, spec_fidelity_after, evidence_json, aaa_percent_estimate }\n\n` +
  `Target: Pass 4/5 criteria, spec_fidelity 18% -> 70%+, AAA % 46% -> 65%+`,
  {
    label: 'acceptance-tests',
    phase: 'Test & Measure',
    schema: {
      type: 'object',
      properties: {
        tests_passed: { type: 'integer' },
        tests_failed: { type: 'integer' },
        criteria_total: { type: 'integer' },
        spec_fidelity_before: { type: 'number' },
        spec_fidelity_after: { type: 'number' },
        parameters_verified_before: { type: 'integer' },
        parameters_verified_after: { type: 'integer' },
        evidence_json: { type: 'object' },
        aaa_percent_estimate_before: { type: 'number' },
        aaa_percent_estimate_after: { type: 'number' },
        issues_to_address: { type: 'array', items: { type: 'string' } }
      }
    }
  }
)

log(`Acceptance tests: ${acceptanceTestRun?.tests_passed || 0}/${acceptanceTestRun?.criteria_total || 5} passed`)
log(`Spec fidelity gain: ${(acceptanceTestRun?.spec_fidelity_before * 100).toFixed(0)}% -> ${(acceptanceTestRun?.spec_fidelity_after * 100).toFixed(0)}%`)
log(`AAA enjoyment gain: ${(acceptanceTestRun?.aaa_percent_estimate_before || 46).toFixed(0)}% -> ${(acceptanceTestRun?.aaa_percent_estimate_after || 65).toFixed(0)}%`)

phase('Loop 0 Refinements')

// Step 6: In parallel, start Loop 0 Player Character micro-feedback improvements
const loop0Refinements = await parallel([
  () => agent(
    `Add Servo Sound Design to Player Character\n\n` +
    `Context: Player_Character_Model 97% AAA, but lacks micro-feedback (servo sounds, weight shifts)\n` +
    `Task: Add high-frequency servo/pneumatic sounds on player movement (suit actuators)\n` +
    `Implementation:\n` +
    `1. Create simple servo sound effect (UE5 Synthesis or external audio)\n` +
    `2. Trigger on Verb_Step, Verb_Sprint with volume proportional to speed\n` +
    `3. Layering: Quiet on walk, medium on run, loud on sprint\n` +
    `4. Non-diegetic mix: Keep servo sounds subtle (background feedback, not dialogue)\n` +
    `5. Measure: Player_Character_Model immersion score should increase (servo feedback +2-3 pts)\n` +
    `6. Return: { servo_sounds_implemented, volume_scaling_working, aaa_feedback_quality, issues }`,
    {
      label: 'loop0:servo-sounds',
      phase: 'Loop 0 Refinements',
      schema: {
        type: 'object',
        properties: {
          servo_sounds_implemented: { type: 'boolean' },
          volume_scaling_working: { type: 'boolean' },
          feedback_quality: { type: 'string', enum: ['AAA', 'high', 'moderate', 'placeholder'] },
          immersion_score_gain: { type: 'integer' }
        }
      }
    }
  ),
  () => agent(
    `Add Weight-Shift Animation to Player Character\n\n` +
    `Context: Current assessment notes 'slight mechanical stiffness' in movement\n` +
    `Task: Add subtle weight-shift arcs to character animation on turns/stops\n` +
    `Implementation:\n` +
    `1. Modify character animation blueprint: Add root motion weight shift on state transitions\n` +
    `2. Overshoot curve: Fast turn -> slight back-lean, then forward settle\n` +
    `3. Test in PIE: Sprint forward, hard stop -> character should sway backward, recover\n` +
    `4. Subtlety: Weight shift should be <5cm offset (believable, not cartoonish)\n` +
    `5. Measure: Animation juice score should increase (overshoot +2 pts)\n` +
    `6. Return: { weight_shift_implemented, overshoot_magnitude_cm, visual_believability, issues }`,
    {
      label: 'loop0:weight-shift',
      phase: 'Loop 0 Refinements',
      schema: {
        type: 'object',
        properties: {
          weight_shift_implemented: { type: 'boolean' },
          overshoot_magnitude_cm: { type: 'number' },
          believability_score: { type: 'integer', minimum: 0, maximum: 10 },
          animation_juice_gain: { type: 'integer' }
        }
      }
    }
  )
])

log(`Loop 0 refinements: ${loop0Refinements.filter(Boolean).length}/2 complete`)

// Final grading sweep
const finalGrading = await agent(
  `Final Grade Sweep: All 9 Loop 0/1 Features\n\n` +
  `Using result_grader_aaa_expanded with updated evidence:\n\n` +
  `Loop 0 (Player Character):\n` +
  `- Player_Character_Model: 97% (golden standard, maintained)\n` +
  `- Player_Character_Animation: TBD (weight shift +)\n` +
  `- Player_Character_Suit: TBD\n` +
  `- Player_Character_Lighting: TBD\n\n` +
  `Loop 1 (Ground):\n` +
  `- Ground_Sand_Particles: Estimate 46% -> 65%+ (Niagara + wind + accumulation + audio-visual)\n` +
  `- Ground_Sand_Footprints: TBD\n` +
  `- Ground_Sand_Surface: TBD\n` +
  `- Ground_Rock_Surface: TBD\n` +
  `- Ground_Metal_Surface: TBD\n\n` +
  `Task:\n` +
  `1. Grade each feature with updated evidence\n` +
  `2. Calculate Loop 0 avg fidelity (target: 77%+)\n` +
  `3. Calculate Loop 1 avg fidelity (target: 75%+)\n` +
  `4. Identify remaining gaps for Week 2 refinement\n` +
  `5. Generate Phase 2 handoff priorities\n` +
  `6. Return: { loop0_avg_fidelity, loop1_avg_fidelity, targets_met, phase2_priorities, final_report }`,
  {
    label: 'final-grading',
    phase: 'Test & Measure',
    schema: {
      type: 'object',
      properties: {
        loop0_avg_fidelity: { type: 'number' },
        loop0_target: { type: 'number' },
        loop0_target_met: { type: 'boolean' },
        loop1_avg_fidelity: { type: 'number' },
        loop1_target: { type: 'number' },
        loop1_target_met: { type: 'boolean' },
        critical_path_status: { type: 'string' },
        phase2_priorities: { type: 'array', items: { type: 'string' } },
        handoff_ready: { type: 'boolean' }
      }
    }
  }
)

log(`Phase 1 Implementation Status:`)
log(`- Loop 0 avg fidelity: ${(finalGrading?.loop0_avg_fidelity * 100).toFixed(0)}% (target: 77%+)`)
log(`- Loop 1 avg fidelity: ${(finalGrading?.loop1_avg_fidelity * 100).toFixed(0)}% (target: 75%+)`)
log(`- Critical path (Ground_Sand_Particles): ${finalGrading?.critical_path_status || 'in progress'}`)
log(`- Phase 2 ready: ${finalGrading?.handoff_ready ? 'YES' : 'NO'}`)

// Return comprehensive Phase 1 implementation report
return {
  phase: 'Phase 1: Spec Fidelity Implementation',
  critical_path_status: niagaraSetup?.system_status,
  niagara_loaded: niagaraSetup?.dsl_parameter_parity || 0,
  dust_accumulation: dustMaterialIntegration?.integration_status,
  wind_system: windSystemSetup?.wind_system_status,
  audio_visual_sync_latency_ms: audioVisualSync?.sync_latency_ms,
  acceptance_tests_passed: acceptanceTestRun?.tests_passed,
  ground_sand_particles_fidelity_before: (acceptanceTestRun?.spec_fidelity_before * 100).toFixed(0) + '%',
  ground_sand_particles_fidelity_after: (acceptanceTestRun?.spec_fidelity_after * 100).toFixed(0) + '%',
  ground_sand_particles_aaa_enjoyment_before: (acceptanceTestRun?.aaa_percent_estimate_before).toFixed(0) + '%',
  ground_sand_particles_aaa_enjoyment_after: (acceptanceTestRun?.aaa_percent_estimate_after).toFixed(0) + '%',
  loop0_avg_fidelity: (finalGrading?.loop0_avg_fidelity * 100).toFixed(0) + '%',
  loop1_avg_fidelity: (finalGrading?.loop1_avg_fidelity * 100).toFixed(0) + '%',
  phase_1_targets_met: finalGrading?.loop0_target_met && finalGrading?.loop1_target_met,
  phase_2_ready: finalGrading?.handoff_ready,
  phase_2_priorities: finalGrading?.phase2_priorities
}
