export const meta = {
  name: 'phase-1-orchestrator',
  description: 'Phase 1 (Weeks 1-2): Parallel spec fidelity audits, test implementation, and measurement across Loop 0 (Player) and Loop 1 (Ground)',
  phases: [
    { title: 'Loop 0 Spec Audits', detail: 'Player Character: 4 features in parallel' },
    { title: 'Loop 1 Spec Audits', detail: 'Ground Environment: 5 features in parallel' },
    { title: 'Test Implementation', detail: 'Acceptance criteria framework + measurement harness' },
    { title: 'Grading & Consolidation', detail: 'Weekly measurement cycle: grade → study guide → Phase 2 handoff' },
  ],
}

// Phase 1 orchestrator: Parallel spec fidelity audits for all Loop 0/1 features
// Target: Loop 0 avg 56% -> 77%+, Loop 1 avg 26% -> 75%+
// Timeline: 2 weeks (Weeks 1-2 of 7-week roadmap)

phase('Loop 0 Spec Audits')

const loop0Features = [
  {
    name: 'Player_Character_Model',
    audit_doc: 'docs/SPEC_FIDELITY_AUDIT_LOOP_0.md',
    current_fidelity: 0.82,
    target_fidelity: 0.95,
    parameters_to_verify: 11,
    current_verified: 9,
    critical_gaps: ['mass_physics_test', 'visor_transparency_measurement'],
    test_criteria: 5
  },
  {
    name: 'Player_Character_Animation',
    audit_doc: 'docs/SPEC_FIDELITY_AUDIT_LOOP_0.md',
    current_fidelity: 0.71,
    target_fidelity: 0.85,
    parameters_to_verify: 7,
    current_verified: 5,
    critical_gaps: ['verb_sprint_implementation', 'gesture_library_completion'],
    test_criteria: 5
  },
  {
    name: 'Player_Character_Suit',
    audit_doc: 'docs/SPEC_FIDELITY_AUDIT_LOOP_0.md',
    current_fidelity: 0.25,
    target_fidelity: 0.60,
    parameters_to_verify: 8,
    current_verified: 2,
    critical_gaps: ['combat_test_suite', 'equipment_interaction', 'power_metering'],
    test_criteria: 5
  },
  {
    name: 'Player_Character_Lighting',
    audit_doc: 'docs/SPEC_FIDELITY_AUDIT_LOOP_0.md',
    current_fidelity: 0.37,
    target_fidelity: 0.70,
    parameters_to_verify: 8,
    current_verified: 3,
    critical_gaps: ['lighting_radiometry', 'shadow_distance_profiling', 'contact_shadow_test'],
    test_criteria: 5
  }
]

const loop0Audits = await parallel(loop0Features.map((feature, idx) => () =>
  agent(
    `Spec Fidelity Audit: ${feature.name}\n\n` +
    `Current fidelity: ${(feature.current_fidelity * 100).toFixed(0)}% (${feature.current_verified}/${feature.parameters_to_verify} parameters verified)\n` +
    `Target: ${(feature.target_fidelity * 100).toFixed(0)}%\n\n` +
    `Critical gaps to address:\n${feature.critical_gaps.map(g => `- ${g}`).join('\n')}\n\n` +
    `Task:\n` +
    `1. Run spec fidelity audit per ${feature.audit_doc}\n` +
    `2. Identify exactly which DSL parameters are missing verification\n` +
    `3. Design ${feature.test_criteria}-criterion acceptance test suite for this feature\n` +
    `4. Prioritize critical gaps by impact on AAA enjoyment percentile\n` +
    `5. Return: { feature_name, current_fidelity, gaps_ranked, test_design, week1_targets, week2_targets }\n\n` +
    `Context: Player_Character_Model is golden standard at 97% enjoyment. Use as reference for what AAA-quality looks like.`,
    {
      label: `loop0:${feature.name}`,
      phase: 'Loop 0 Spec Audits',
      schema: {
        type: 'object',
        properties: {
          feature_name: { type: 'string' },
          current_fidelity: { type: 'number', minimum: 0, maximum: 1 },
          parameters_verified: { type: 'integer' },
          parameters_total: { type: 'integer' },
          gaps_ranked: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                gap_name: { type: 'string' },
                parameter: { type: 'string' },
                current_state: { type: 'string' },
                verification_method: { type: 'string' },
                estimated_points_gain: { type: 'integer' }
              }
            }
          },
          test_design: {
            type: 'object',
            properties: {
              criterion_1: { type: 'string' },
              criterion_2: { type: 'string' },
              criterion_3: { type: 'string' },
              criterion_4: { type: 'string' },
              criterion_5: { type: 'string' }
            }
          },
          week1_targets: { type: 'object' },
          week2_targets: { type: 'object' }
        }
      }
    }
  )
))

log(`Loop 0 audits complete: ${loop0Audits.filter(Boolean).length}/4 features analyzed`)

phase('Loop 1 Spec Audits')

const loop1Features = [
  {
    name: 'Ground_Sand_Particles',
    audit_doc: 'docs/SPEC_FIDELITY_AUDIT_LOOP_1.md',
    current_fidelity: 0.18,
    target_fidelity: 0.85,
    parameters_to_verify: 11,
    current_verified: 2,
    critical_gaps: ['niagara_system_loading', 'wind_system_integration', 'dust_accumulation_mask', 'audio_visual_sync'],
    test_criteria: 5,
    priority: 'CRITICAL_PATH'
  },
  {
    name: 'Ground_Sand_Footprints',
    audit_doc: 'docs/SPEC_FIDELITY_AUDIT_LOOP_1.md',
    current_fidelity: 0.25,
    target_fidelity: 0.75,
    parameters_to_verify: 8,
    current_verified: 2,
    critical_gaps: ['decal_system_verification', 'weight_factor_test', 'wind_erosion_rate'],
    test_criteria: 5,
    priority: 'HIGH'
  },
  {
    name: 'Ground_Sand_Surface',
    audit_doc: 'docs/SPEC_FIDELITY_AUDIT_LOOP_1.md',
    current_fidelity: 0.38,
    target_fidelity: 0.75,
    parameters_to_verify: 8,
    current_verified: 3,
    critical_gaps: ['material_radiometry', 'parallax_depth_test', 'roughness_measurement'],
    test_criteria: 5,
    priority: 'HIGH'
  },
  {
    name: 'Ground_Rock_Surface',
    audit_doc: 'docs/SPEC_FIDELITY_AUDIT_LOOP_1.md',
    current_fidelity: 0.25,
    target_fidelity: 0.75,
    parameters_to_verify: 8,
    current_verified: 2,
    critical_gaps: ['detail_map_tiling_analysis', 'normal_strength_measurement', 'audio_resonance_spectrum'],
    test_criteria: 5,
    priority: 'MEDIUM'
  },
  {
    name: 'Ground_Metal_Surface',
    audit_doc: 'docs/SPEC_FIDELITY_AUDIT_LOOP_1.md',
    current_fidelity: 0.25,
    target_fidelity: 0.75,
    parameters_to_verify: 8,
    current_verified: 2,
    critical_gaps: ['material_radiometry', 'impact_resonance_measurement', 'rust_overlay_quantification'],
    test_criteria: 5,
    priority: 'MEDIUM'
  }
]

const loop1Audits = await parallel(loop1Features.map((feature, idx) => () =>
  agent(
    `Spec Fidelity Audit: ${feature.name} (Priority: ${feature.priority})\n\n` +
    `Current fidelity: ${(feature.current_fidelity * 100).toFixed(0)}% (${feature.current_verified}/${feature.parameters_to_verify} parameters verified)\n` +
    `Target: ${(feature.target_fidelity * 100).toFixed(0)}%\n\n` +
    `Critical gaps to address:\n${feature.critical_gaps.map(g => `- ${g}`).join('\n')}\n\n` +
    `Task:\n` +
    `1. Run spec fidelity audit per ${feature.audit_doc}\n` +
    `2. Identify exactly which DSL parameters are missing verification\n` +
    `3. Design ${feature.test_criteria}-criterion acceptance test suite for this feature\n` +
    `4. Flag measurement tools needed (radiometry, spectrum analysis, latency measurement)\n` +
    `5. Prioritize critical gaps by impact on AAA enjoyment percentile\n` +
    `6. Return: { feature_name, current_fidelity, gaps_ranked, test_design, measurement_tools, week1_targets, week2_targets }\n\n` +
    `Context: This is Ground Environment (Loop 1). Current avg fidelity 26% -> target 75%+. ` +
    `${feature.priority === 'CRITICAL_PATH' ? 'CRITICAL: This feature blocks Phase 2 audio-visual sync work. Niagara system loading is prerequisite.' : ''}`,
    {
      label: `loop1:${feature.name}`,
      phase: 'Loop 1 Spec Audits',
      schema: {
        type: 'object',
        properties: {
          feature_name: { type: 'string' },
          priority: { type: 'string' },
          current_fidelity: { type: 'number' },
          parameters_verified: { type: 'integer' },
          parameters_total: { type: 'integer' },
          gaps_ranked: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                gap_name: { type: 'string' },
                parameter: { type: 'string' },
                verification_method: { type: 'string' },
                measurement_tool: { type: 'string' },
                estimated_points_gain: { type: 'integer' }
              }
            }
          },
          test_design: {
            type: 'object',
            properties: {
              criterion_1: { type: 'string' },
              criterion_2: { type: 'string' },
              criterion_3: { type: 'string' },
              criterion_4: { type: 'string' },
              criterion_5: { type: 'string' }
            }
          },
          measurement_tools_needed: { type: 'array', items: { type: 'string' } },
          week1_targets: { type: 'object' },
          week2_targets: { type: 'object' }
        }
      }
    }
  )
))

log(`Loop 1 audits complete: ${loop1Audits.filter(Boolean).length}/5 features analyzed`)

phase('Test Implementation')

const allAudits = [...loop0Audits.filter(Boolean), ...loop1Audits.filter(Boolean)]

const testSuites = await parallel(allAudits.map((audit, idx) => () =>
  agent(
    `Build Acceptance Test Suite: ${audit.feature_name}\n\n` +
    `Criteria (5 total):\n${Object.entries(audit.test_design || {}).map(([k, v]) => `- ${k}: ${v}`).join('\n')}\n\n` +
    `Task:\n` +
    `1. Design C++ test implementations for all 5 criteria\n` +
    `2. Integrate with UE5 test framework (reference: PlayerCharacterAcceptanceTests.h/cpp)\n` +
    `3. Identify measurement tools required (MCP extensions, radiometry probe, spectrum analyzer)\n` +
    `4. Design evidence JSON schema for this feature (tests.passed, tests.criteria_total, spec_fidelity)\n` +
    `5. Estimate Week 1 test pass rate (baseline), Week 2 target pass rate\n` +
    `6. Return: { feature_name, test_framework_design, measurement_integration, evidence_schema, week1_estimate, week2_target }\n\n` +
    `Context: Tests feed result_grader_aaa_expanded as evidence. Each passing criterion increases spec_fidelity score.`,
    {
      label: `tests:${audit.feature_name}`,
      phase: 'Test Implementation',
      schema: {
        type: 'object',
        properties: {
          feature_name: { type: 'string' },
          test_framework_design: { type: 'string' },
          measurement_integration: { type: 'string' },
          evidence_schema: { type: 'object' },
          week1_estimate: {
            type: 'object',
            properties: {
              tests_passed: { type: 'integer' },
              tests_total: { type: 'integer' },
              expected_fidelity_percent: { type: 'integer' }
            }
          },
          week2_target: {
            type: 'object',
            properties: {
              tests_passed: { type: 'integer' },
              tests_total: { type: 'integer' },
              target_fidelity_percent: { type: 'integer' }
            }
          }
        }
      }
    }
  )
))

log(`Test suites designed: ${testSuites.filter(Boolean).length}/9 features`)

phase('Grading & Consolidation')

// Consolidate all audits and test designs
const consolidation = await agent(
  `Consolidate Phase 1 Results & Generate Handoff Report\n\n` +
  `Input Data:\n` +
  `- Loop 0 audits: ${allAudits.filter(a => a.feature_name.includes('Player')).length} features\n` +
  `- Loop 1 audits: ${allAudits.filter(a => !a.feature_name.includes('Player')).length} features\n` +
  `- Test suite designs: ${testSuites.filter(Boolean).length} features\n\n` +
  `Task:\n` +
  `1. Calculate Phase 1 progress summary:\n` +
  `   - Loop 0 current avg fidelity vs target (56% -> 77%+)\n` +
  `   - Loop 1 current avg fidelity vs target (26% -> 75%+)\n` +
  `   - Critical path status (Ground_Sand_Particles Niagara integration)\n\n` +
  `2. Generate weekly measurement cycle schedule:\n` +
  `   - Week 1: audit + baseline grading (Criterion 1 tests)\n` +
  `   - Week 2: measurement + parameter verification + final grading\n\n` +
  `3. Identify blockers & risks:\n` +
  `   - Missing tools (Niagara inspector, radiometry probe, spectrum analyzer)\n` +
  `   - Features at risk of not meeting targets\n` +
  `   - Phase 2 dependencies\n\n` +
  `4. Generate Phase 2 handoff priorities (Weeks 3-4):\n` +
  `   - Audio-visual sync (based on Phase 1 measurement gaps)\n` +
  `   - Emergent complexity (based on Phase 1 systems depth findings)\n` +
  `   - Playable feature list (features ready for Phase 2 work)\n\n` +
  `5. Return: { loop0_progress, loop1_progress, critical_path_status, week1_schedule, week2_schedule, blockers, phase2_priorities, handoff_report }`,
  {
    label: 'consolidation',
    phase: 'Grading & Consolidation',
    schema: {
      type: 'object',
      properties: {
        loop0_progress: {
          type: 'object',
          properties: {
            current_avg_fidelity: { type: 'number' },
            target_avg_fidelity: { type: 'number' },
            features_on_track: { type: 'integer' },
            features_at_risk: { type: 'integer' }
          }
        },
        loop1_progress: {
          type: 'object',
          properties: {
            current_avg_fidelity: { type: 'number' },
            target_avg_fidelity: { type: 'number' },
            features_on_track: { type: 'integer' },
            features_at_risk: { type: 'integer' },
            critical_path_status: { type: 'string' }
          }
        },
        week1_schedule: { type: 'object' },
        week2_schedule: { type: 'object' },
        blockers: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              blocker: { type: 'string' },
              impact: { type: 'string' },
              mitigation: { type: 'string' }
            }
          }
        },
        phase2_priorities: { type: 'array', items: { type: 'string' } },
        handoff_report_summary: { type: 'string' }
      }
    }
  }
)

log(`Phase 1 consolidation complete`)

// Generate final report
const finalReport = {
  phase: 'Phase 1: Spec Fidelity & Test Coverage',
  timeline: 'Weeks 1-2 of 7-week roadmap',
  loop0_audits: loop0Audits.filter(Boolean).length,
  loop1_audits: loop1Audits.filter(Boolean).length,
  test_suites: testSuites.filter(Boolean).length,
  consolidation_status: consolidation ? 'complete' : 'pending',
  loop0_targets: 'avg fidelity 56% -> 77%+',
  loop1_targets: 'avg fidelity 26% -> 75%+',
  critical_path: 'Ground_Sand_Particles 18% -> 85%+ (Niagara, wind, accumulation, audio-visual)',
  measurement_cycle: 'Weekly: audit -> test -> grade -> study guide',
  next_phase: 'Phase 2 (Weeks 3-4): Player Experience - Audio-Visual Sync + Emergent Complexity',
  phase2_handoff_ready: true
}

return finalReport
