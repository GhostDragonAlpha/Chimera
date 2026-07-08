# Spec Fidelity Audit: Loop 1 (The Ground) — DSL Parameter Verification

**Framework**: AAA-Expanded Result Grader  
**Dimension**: Spec Fidelity (15 pts — DSL declared parameters must be verified in built result)  
**Current State**: Ground_Sand_Particles 33% fidelity (critical gap), other ground features TBD  
**Target**: All Loop 1 features ≥80% spec fidelity  
**Timeline**: Parallel with Week 1-2 (Loop 0), intensive Week 3-4  

---

## Feature: Ground_Sand_Particles (CRITICAL FOCUS)

### DSL-Declared Parameters
```
GroundSandParticles {
  particle_system: "NS_SandDust"
  emitter_count: 1
  particles_per_second: 50
  particle_lifetime: 3.0  # seconds
  particle_velocity: [10, 50]  # UU/s range
  particle_size: 0.5  # UU
  particle_color: [0.9, 0.85, 0.7, 0.8]  # RGBA sandy tan
  gravity_scale: 0.5  # Half normal gravity
  wind_response: 1.0  # Full wind interaction
  accumulation_enabled: true  # Dust settles and accumulates
  footstep_trigger_enabled: true  # Dust on player impact
}
```

### Verification Checklist (11 parameters, 80% = 9/11)

| Parameter | Type | Expected Value | Current Status | Verification Method |
|-----------|------|-----------------|------------------|-------------------|
| particle_system | Asset | NS_SandDust | ❌ MISSING | Niagara system not loaded |
| emitter_count | Int | 1 | ❌ NOT TESTED | Need MCP query |
| particles_per_second | Float | 50 | ❌ NOT VERIFIED | Need telemetry measurement |
| particle_lifetime | Float | 3.0 seconds | ❌ NOT VERIFIED | Screenshot analysis → visual duration |
| particle_velocity | Float range | 10-50 UU/s | ❌ NOT VERIFIED | Sleepwalker: movement speed correlation |
| particle_size | Float | 0.5 UU | ⚠️ PARTIAL | Visual inspection says ~1-2 UU (needs tuning) |
| particle_color | Color RGBA | [0.9, 0.85, 0.7, 0.8] | ✅ VERIFIED | Screenshot matches sandy tan color |
| gravity_scale | Float | 0.5 (half gravity) | ❌ NOT VERIFIED | Particle settling time analysis |
| wind_response | Float | 1.0 (full wind) | ❌ NOT VERIFIED | No wind system implemented |
| accumulation_enabled | Bool | true | ❌ NOT VERIFIED | Dust persistence test |
| footstep_trigger_enabled | Bool | true | ✅ VERIFIED | Sleepwalker: footstep dust visible |

### Result
- **Verified**: 2/11 parameters (18%)
- **Partial**: 1/11 parameters
- **Current Actual Fidelity**: 33% (per CRITIC audit, likely includes visual polish penalty)
- **Gap to Target**: 18% → 80% requires **9+ additional verifications**

### Critical Missing Implementations
1. **Niagara System (NS_SandDust)**: Asset not loaded — entire particle effect framework missing
2. **Wind System**: No wind interaction implemented (gravity_scale and wind_response untested)
3. **Accumulation Mask Material**: Dust settling not permanent (procedural dust-accumulation mask C++ written but not integrated)
4. **Audio-Visual Coupling**: Particles spawn but no synchronized audio feedback (footstep sound missing)
5. **Parameter Exposure**: Only particle_color and footstep_trigger are tunable; others hardcoded

### Refinement Path to 80% Fidelity
```
Week 1: Load NS_SandDust Niagara system → verify emitter_count, particles_per_second
Week 2: Implement wind system → verify wind_response, gravity_scale, accumulation
Week 3: Integrate DustAccumulationMaterial (procedural mask) → test accumulation_enabled
Week 4: Add audio feedback → verify footstep_trigger with synchronized audio
Result: 11/11 parameters verified → 100% fidelity
```

---

## Feature: Ground_Sand_Footprints

### DSL-Declared Parameters
```
SandFootprints {
  decal_system: "DM_Footprint_Sand"
  decal_lifetime: 30.0  # seconds until fade
  decal_depth: 0.5  # visual depth impression
  decal_size: 30.0  # decal scale (UU)
  player_weight_factor: 1.0  # depth scales with speed
  wind_erosion_rate: 0.5  # footprints fade due to wind
  surface_interaction: true  # indents ground on impact
  physics_interaction: false  # footprints don't create collision
}
```

### Verification Checklist (8 parameters, 80% = 6.4/8)

| Parameter | Status | Notes |
|-----------|--------|-------|
| decal_system | ❌ NOT VERIFIED | DM_Footprint_Sand asset status unknown |
| decal_lifetime | ❌ NOT VERIFIED | Test: footprint visible at T=0s, faded at T=31s |
| decal_depth | ⚠️ PARTIAL | Visually appears ~0.5 UU in screenshots |
| decal_size | ❌ NOT VERIFIED | Need pixel-to-UU conversion from screenshot |
| player_weight_factor | ❌ NOT VERIFIED | Sprint footprints should be deeper than walk |
| wind_erosion_rate | ❌ NOT VERIFIED | No wind system → can't test erosion |
| surface_interaction | ✅ VERIFIED | Footprints visible on sand surface in sleepwalker beats |
| physics_interaction | ✅ VERIFIED | Player clips through footprints (no collision) |

### Result
- **Verified**: 2/8 (25%)
- **Partial**: 1/8
- **Target**: 6.4/8 (80%)
- **Gap**: Need decal system + weight factor + wind erosion tests

---

## Feature: Ground_Sand_Surface

### DSL-Declared Parameters
```
SandSurface {
  material: "M_Sand_Desert"
  tiling_scale: 2.0  # texture repeat
  normal_map_strength: 1.0
  roughness: 0.8  # high roughness for sand
  metallic: 0.0
  ao_map: true  # ambient occlusion mapped
  parallax_depth: 0.1  # depth illusion
  sound_material_type: "sand"  # footstep audio cue
}
```

### Verification Checklist (8 parameters)

| Parameter | Status | Verification Method |
|-----------|--------|-------------------|
| material | ✅ VERIFIED | M_Sand_Desert loaded in viewport |
| tiling_scale | ⚠️ PARTIAL | Visual: texture repeats at ~2m intervals (estimate) |
| normal_map_strength | ❌ NOT VERIFIED | Need material editor inspection |
| roughness | ❌ NOT VERIFIED | Lighting test: specular reflection analysis |
| metallic | ✅ VERIFIED | No metallic shine observed (0.0 correct) |
| ao_map | ⚠️ PARTIAL | AO visible in shadows (unquantified) |
| parallax_depth | ❌ NOT VERIFIED | Close-range screenshot → depth illusion analysis |
| sound_material_type | ✅ VERIFIED | Footsteps sound sandy (audio log confirms) |

### Result
- **Verified**: 3/8 (37%)
- **Target**: 6.4/8 (80%)
- **Gap**: Need material radiometry tests (roughness, AO map intensity, parallax depth)

---

## Feature: Ground_Rock_Surface

### DSL-Declared Parameters
```
RockSurface {
  material: "M_Rock_Basalt"
  detail_map_tiling: 0.5  # fine detail scale
  roughness: 0.6  # less rough than sand
  normal_strength: 1.2  # exaggerated normal map
  color_variation: true  # procedural color streaks
  moss_coverage: 0.1  # slight green algae
  sound_material_type: "rock"
  footstep_resonance: 1.5  # audio resonance multiplier
}
```

### Verification Checklist (8 parameters)

| Parameter | Status | Notes |
|-----------|--------|-------|
| material | ✅ VERIFIED | M_Rock_Basalt loaded |
| detail_map_tiling | ❌ NOT VERIFIED | Need close-range texture analysis |
| roughness | ❌ NOT VERIFIED | Material radiometry test needed |
| normal_strength | ⚠️ PARTIAL | Visual: strong normal relief visible |
| color_variation | ❌ NOT VERIFIED | Procedural variation not confirmed |
| moss_coverage | ❌ NOT VERIFIED | Green tint barely visible (if at all) |
| sound_material_type | ✅ VERIFIED | Footsteps sound rocky (audio logs confirm) |
| footstep_resonance | ❌ NOT VERIFIED | Need audio spectrum analysis (should be >1.0x baseline) |

### Result
- **Verified**: 2/8 (25%)
- **Target**: 6.4/8 (80%)
- **Gap**: Need material parameters + audio resonance measurement

---

## Feature: Ground_Metal_Surface

### DSL-Declared Parameters
```
MetalSurface {
  material: "M_Metal_Corroded_Steel"
  roughness: 0.4  # lower roughness (more reflective)
  metallic: 1.0  # fully metallic
  detail_normal_scale: 1.5  # corrosion detail
  rust_color_overlay: [0.7, 0.4, 0.1, 0.3]  # rust tint RGBA
  reflection_roughness: 0.35  # mirror-like
  sound_material_type: "metal"
  impact_resonance: 2.0  # high-frequency ring
}
```

### Verification Checklist (8 parameters)

| Parameter | Status | Notes |
|-----------|--------|-------|
| material | ✅ VERIFIED | M_Metal_Corroded_Steel loaded |
| roughness | ❌ NOT VERIFIED | Material parameter extraction needed |
| metallic | ✅ VERIFIED | Strong specular reflection observed |
| detail_normal_scale | ❌ NOT VERIFIED | Corrosion texture not clearly visible |
| rust_color_overlay | ⚠️ PARTIAL | Rust tint visible but not quantified |
| reflection_roughness | ❌ NOT VERIFIED | Specular analysis needed |
| sound_material_type | ✅ VERIFIED | Footsteps sound metallic (verified in sleepwalker) |
| impact_resonance | ⚠️ PARTIAL | High-frequency ring audible but not measured |

### Result
- **Verified**: 2/8 (25%)
- **Target**: 6.4/8 (80%)
- **Gap**: Need material radiometry + audio spectrum analysis

---

## Summary: Loop 1 Spec Fidelity Status

| Feature | Verified | Partial | Target | Gap | Priority |
|---------|----------|---------|--------|-----|----------|
| **Ground_Sand_Particles** | 2/11 (18%) | 1 | 9/11 (82%) | -64% | 🔴 CRITICAL |
| **Ground_Sand_Footprints** | 2/8 (25%) | 1 | 6/8 (75%) | -50% | 🔴 CRITICAL |
| **Ground_Sand_Surface** | 3/8 (38%) | 2 | 6/8 (75%) | -37% | 🟡 HIGH |
| **Ground_Rock_Surface** | 2/8 (25%) | 0 | 6/8 (75%) | -50% | 🟡 HIGH |
| **Ground_Metal_Surface** | 2/8 (25%) | 2 | 6/8 (75%) | -50% | 🟡 HIGH |
| **LOOP 1 AVERAGE** | **2.2/8.6 (26%)** | — | **6.4/8.6 (75%)** | **-49%** | **🔴 CRITICAL FOCUS** |

---

## Acceptance Criteria Tests Required (Week 2-4 Implementation)

### Critical Path: Ground_Sand_Particles (Prerequisite for other surfaces)

#### Criterion 1: Niagara System Loaded
```
TEST: GroundSandParticles_NiagaraLoaded
  GIVEN: Regolith Yard level loaded
  WHEN: Player walks on sand surface
  THEN:
    - NS_SandDust Niagara system instantiated
    - Emitter count = 1
    - Particle spawn rate visible (50+ particles/sec)
  ACCEPTANCE: System active, particles visible
```

#### Criterion 2: Particle Parameters Verified
```
TEST: GroundSandParticles_Parameters
  GIVEN: Niagara system active
  WHEN: Measure particle properties
  THEN:
    - Lifetime = 3.0s ±0.2s (screenshot @ T=0s, T=3.2s)
    - Velocity = 10-50 UU/s (correlation with movement speed)
    - Color = sandy tan (RGBA [0.9, 0.85, 0.7, 0.8] ±5%)
    - Gravity scale = 0.5 (settling speed relative to baseline)
  ACCEPTANCE: All 4 parameters within tolerance
```

#### Criterion 3: Dust Accumulation Functional
```
TEST: GroundSandParticles_Accumulation
  GIVEN: Player walks in circle 10+ times, stays still
  WHEN: Observe dust behavior over 30s
  THEN:
    - Dust particles settle on ground (not disappear instantly)
    - Accumulation layer visible after sustained activity
    - DustAccumulationMaterial mask applied to surface
  ACCEPTANCE: Accumulation system functional
```

#### Criterion 4: Audio-Visual Sync
```
TEST: GroundSandParticles_AudioVisualSync
  GIVEN: Player walking on sand
  WHEN: Each footfall occurs
  THEN:
    - Dust particle burst within 16ms of foot impact (1 frame @ 60fps)
    - Audio event triggers within 100ms
    - Volume proportional to movement speed
  ACCEPTANCE: Latency <100ms, particles + audio coupled
```

#### Criterion 5: Wind Interaction Verified
```
TEST: GroundSandParticles_WindResponse
  GIVEN: Wind system active, player standing still
  WHEN: Wind blows across sand
  THEN:
    - Dust particles drift with wind (wind_response = 1.0)
    - Trajectory matches wind direction
    - Particle dispersion rate correlates with wind speed
  ACCEPTANCE: Wind interaction verified
```

---

## Testing Implementation Strategy

### Week 1-2: Setup & Material Parameters
1. Load/verify NS_SandDust Niagara system
2. Material radiometry tests (roughness, metallic, AO maps)
3. Audio spectrum analysis (material type verification)
4. Capture baseline evidence for all 5 ground features

### Week 3: Critical Path — Ground_Sand_Particles
1. Run Criterion 1-2 tests (Niagara, parameters)
2. Integrate DustAccumulationMaterial from procedural code
3. Run Criterion 3 test (accumulation)
4. Measure audio-visual latency (Criterion 4)

### Week 4: Refinement & Secondary Features
1. Verify wind system integration (Criterion 5)
2. Test other ground surfaces (footprints, rock, metal)
3. Run full Loop 1 grader sweep
4. Confirm all features ≥75%+ fidelity

### Success Metrics
- Ground_Sand_Particles: 18% → 85%+ fidelity (requires Niagara, wind, accumulation, audio)
- Ground_Sand_Footprints: 25% → 75%+ fidelity
- All other ground surfaces: 25-38% → 75%+ fidelity
- **Loop 1 Average**: 26% → 75%+ (major progress toward 85% target)

---

## Integration with Result Grader

Once all Loop 1 tests pass:

```python
evidence = {
    "tests": {
        "passed": 5,  # All criteria pass (per feature)
        "failed": 0,
        "criteria_total": 5,
        "ran_in_editor": True
    },
    "spec_fidelity": 0.85,  # 9+/11 parameters verified for sand particles
    "immersion": {
        "moment_to_moment_feel_quality": "AAA",  # After audio-visual sync
        "audio_visual_sync": True  # Footstep audio + dust particles
    },
    ...
}

result = grade_feature_aaa_expanded("Ground_Sand_Particles", evidence, benchmark_titles=["No Man's Sky", "Subnautica"])
# Expected: 46% → 75%+ (B/B+)
```

---

## Measurement Tools Required

1. **Niagara System Inspector** (MCP extension)
   - Query active emitters, spawn rate, lifetime
   - Measure particle velocity distribution

2. **Material Radiometry Probe**
   - Measure roughness, metallic, AO map intensity
   - Color picker for RGBA verification

3. **Audio Spectrum Analyzer**
   - Measure footstep resonance (frequency response)
   - Verify diegetic/non-diegetic mix

4. **Latency Measurement** (Sleepwalker integration)
   - Timestamp particle spawn vs audio trigger
   - Measure <100ms audio-visual coupling

---

**Timeline**: Week 1-2 (parallel with Loop 0), intensive Week 3-4  
**Target**: Loop 1 spec fidelity 26% → 75%+  
**Critical Path**: Ground_Sand_Particles 18% → 85%+ (all 11 parameters verified)  
**Next Review**: EOD Week 4 → Loop 1 average ≥75%, Loop 0 ≥85%+ → Phase 2 begins (audio-visual sync + emergent complexity)
