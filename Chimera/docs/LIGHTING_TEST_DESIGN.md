# Player Character Lighting Acceptance Test Suite — Complete Design

**Feature**: Player_Character_Lighting  
**Test Framework**: UE5 Automation + AAA-Expanded Result Grader  
**Criteria**: 5 lighting fidelity checks  
**Evidence Integration**: JSON schema (lighting_evidence_schema.json) → result_grader_aaa_expanded  

---

## 1. Test Framework Design

### Architecture Overview
```
DSL Spec (visor RGB, shadow distance, AO quality)
         ↓
Acceptance Criteria (5 checks) → C++ Tests (UE5 Automation)
         ↓
MCP Tools + Measurement Probes (radiometry, profiling, vision)
         ↓
Evidence Collection (JSON) → Result Grader (spec_fidelity + correctness scoring)
         ↓
Grade (A/B/C/F) + Retry Guidance
```

### C++ Test Implementations

**File**: `Source/Chimera/ProceduralGenerated/Tests/PlayerCharacterLightingTests.h` (header)  
**File**: `Source/Chimera/ProceduralGenerated/Tests/PlayerCharacterLightingTests.cpp` (implementation)

#### Criterion 1: Lighting_Radiometry_Visor_Glow_Measurement
- **Test Method**: Screenshot color picker + histogram analysis
- **Acceptance**: RGB [0.8, 0.9, 1.0] ±0.05, HDR peak 0.4-0.6, hue 180-240 deg
- **Pass Condition**: All 3 checks (RGB, HDR, hue) within tolerance
- **Implementation**: 
  - `CaptureViewportScreenshot()` → MCP `control_editor screenshot mode=editor_viewport`
  - `AnalyzeRadiometry()` → `radiometry_probe.py` color analysis
  - Direct RGB/HSV measurement with histogram binning

#### Criterion 2: Lighting_Shadow_Distance_Profiling
- **Test Method**: Engine profiling + visual horizon verification
- **Acceptance**: ShadowDistance==5000.0 UU, visual depth horizon matches
- **Pass Condition**: Profile matches DSL + visual alignment
- **Implementation**:
  - `QueryRuntimeLightingProfile()` → MCP `inspect action=runtime_report`
  - Extract ShadowDistance parameter from engine state
  - Capture screenshot for visual verification (deferred to sleepwalker)

#### Criterion 3: Lighting_Contact_Shadow_Close_Range
- **Test Method**: Close-range screenshot detail analysis (<2m)
- **Acceptance**: Visor shadows, hand recesses dark, no light leaking
- **Pass Condition**: All 3 visual checks pass (3/3 required)
- **Implementation**:
  - `CaptureViewportScreenshot()` at <2m distance (camera positioned by beat script)
  - `AnalyzeContactShadowVisuals()` → vision analysis for shadow detail
  - Detect darkness in recesses, absence of light artifacts

#### Criterion 4: Lighting_Dynamic_Shadow_Update_Rate
- **Test Method**: Sleepwalker PIE beat (light rotation + frame capture)
- **Acceptance**: Shadow direction updates within 1 frame, smooth (>=90%)
- **Pass Condition**: Frame latency <=1, smoothness >=0.90
- **Implementation**:
  - Rotate directional light 90 degrees
  - Capture 6+ frames at 60 FPS (~100ms sequence)
  - `AnalyzeShadowDirectionConsistency()` → detect direction change latency + smoothness
  - Note: Primarily deferred to sleepwalker beat script (real-time measurement)

#### Criterion 5: Lighting_Ambient_Occlusion_Crease_Definition
- **Test Method**: Material inspection + screenshot analysis
- **Acceptance**: Neck creases dark, knuckles shaded, edges 3D, AO resolution 1K+
- **Pass Condition**: All 4 visual checks pass (4/4 required)
- **Implementation**:
  - `CaptureViewportScreenshot()` at optimal AO inspection angle
  - `AnalyzeAOTextureQuality()` → `radiometry_probe.py` texture density analysis
  - Estimate AO map resolution from gradient frequency
  - Detect crease darkness, knuckle shading, edge contrast

---

## 2. Measurement Integration

### MCP Tools Required

| Tool | Usage | Status |
|---|---|---|
| `control_editor screenshot mode=editor_viewport filename=...` | Capture viewport (all criteria) | Existing |
| `inspect action=runtime_report` | Query ShadowDistance, ContactShadow flags (criterion 2) | Existing |
| `move_actor actor=... location=...` | Position camera for close-range shots (criterion 3) | Existing |
| `radiometry_probe screenshot=... mode=radiance\|texture_density` | Color/texture analysis (criteria 1, 5) | **New** (Python module) |

### Python Measurement Modules

**File**: `core/radiometry_probe.py`  
**Capabilities**:
- `measure_visor_radiometry()` → RGB, HDR peak, HSV hue from screenshot
- `measure_ao_texture_density()` → AO resolution, crease visibility, texture quality
- CLI interface: `python -m core.radiometry_probe --screenshot file.png --mode radiance`

**Dependencies**: Pillow, numpy (image analysis + histogram)

### Sleepwalker Integration

**Beat Script**: `docs/beats/lighting_validation.beats.json` (todo: create)  
**Actions Required**:
- Move camera <2m from character head (criterion 3)
- Rotate directional light 90 degrees with frame capture (criterion 4)
- Screenshot capture at critical frames (PIE-native, high fidelity)

---

## 3. Evidence JSON Schema

**File**: `core/lighting_evidence_schema.json`  
**Size**: ~400 lines (comprehensive)

### Key Evidence Sections

```json
{
  "feature_name": "Player_Character_Lighting",
  "loop_id": 1,
  "tests": {
    "passed": 2,      "← Number of criteria that passed (0-5)
    "failed": 3,      "← Number that failed
    "criteria_total": 5
  },
  "evidence": {
    "criterion_1_radiometry": {
      "criterion_passed": false,
      "color_rgb": { "r": 0.79, "g": 0.88, "b": 1.02 },  "← Measured
      "color_spec": { "r": 0.8, "g": 0.9, "b": 1.0 },    "← DSL spec
      "color_within_tolerance": true,  "← All channels ±0.05
      "hdr_peak": 0.48,                "← Measured intensity
      "hdr_peak_spec": 0.5,
      "hdr_peak_within_tolerance": true,
      "hue_degrees": 244,              "← Out of 180-240 spec!
      "hue_within_tolerance": false,   "← FAIL
      "measurement_tool": "radiometry_probe"
    },
    "criterion_2_shadow_distance": {
      "criterion_passed": true,
      "shadow_distance_measured": 5000.0,
      "shadow_distance_spec": 5000.0,
      "shadow_distance_within_tolerance": true,
      "visual_horizon_match": true,
      "mcp_query_success": true
    },
    // ... (criteria 3-5 follow same pattern)
  },
  "spec_fidelity": {
    "declared_parameters": 13,  "← Total DSL lighting params
    "verified_parameters": 10,  "← Actual tests exercised
    "fidelity_ratio": 0.77      "← 77% = B-level for spec fidelity
  }
}
```

### Evidence Pathways (what gets measured)

- **Radiometry** (C1): Screenshot → PIL + numpy → RGB/HSV histograms
- **Shadow Profile** (C2): Engine state → MCP query → parameter extraction
- **Contact Shadows** (C3): Screenshot → Vision analysis → darkness detection
- **Dynamic Updates** (C4): Frame sequence → Direction consistency analysis → latency metric
- **AO Texture** (C5): Screenshot → Texture frequency analysis → resolution estimate

---

## 4. Week 1 Baseline Estimate (First Implementation)

### Pass Rate Breakdown

| Criterion | Challenge | Week 1 Estimate | Notes |
|---|---|---|---|
| 1. Radiometry | MCP radiometry_probe in development; screenshot color analysis unreliable in PIE | 20% | Placeholder measurements may work syntactically but fail spec checks |
| 2. Shadow Distance | Engine profiling straightforward; MCP inspect exists | 70% | Profile query works; visual verification deferred |
| 3. Contact Shadows | Requires precise camera <2m; sleepwalker beat script essential | 30% | Camera positioning may be off-target; detail analysis unreliable |
| 4. Dynamic Update | Real-time frame capture critical; timing sensitive | 10% | Sleepwalker timing not yet tuned; frame-by-frame capture nascent |
| 5. AO Creases | Texture density detection subjective; visual analysis immature | 25% | radiometry_probe.py AO functions provisional |

### Week 1 Cumulative Result

**Tests Passed**: 1-2 of 5 (20-40% pass rate)  
**Grade**: C (60-75 points on AAA rubric)  
**Spec Fidelity**: ~0.38 (38% of declared lighting parameters verified)

**Breakdown**:
- Technical Correctness: 20/40 (1 test pass, 5 declared, 50% coverage)
- Stability/Performance: ~22/25 (no crashes; FPS nominal)
- Design Checklist: ~12/20 (radiometry check incomplete; others deferred)
- Spec Fidelity: ~6/15 (shadow distance verified; visor spec unconfirmed)
- **Total: ~60/100 → C grade**

### Week 1 Blockers & Unknowns

1. **Radiometry_probe.py color analysis**: Does PIL screenshot reading capture HDR values correctly? Need empirical test.
2. **Sleepwalker beat timing**: Can we capture frames at exact 16.67ms intervals? Frame-sync test needed.
3. **Vision analysis tools**: Do MCP vision tools support arbitrary region detection (creases, knuckles)? May need custom ML.
4. **Camera positioning accuracy**: Can MCP move_actor place camera within <2m at exact heights? Blueprint test needed.

---

## 5. Week 2 Target (Refinement & Integration)

### Incremental Improvements

| Criterion | Week 1 Result | Improvement | Week 2 Target | Method |
|---|---|---|---|---|
| 1. Radiometry | 20% | Develop color picker + build histogram calibration | 85% | Empirical radiometry calibration on test visor assets |
| 2. Shadow Distance | 70% | Refine visual horizon matching algorithm | 95% | Implement depth-map analysis from screenshot |
| 3. Contact Shadows | 30% | Improve beat script camera positioning; tuning | 75% | Multiple camera positions tested; sleepwalker refinement |
| 4. Dynamic Update | 10% | Solve frame capture timing; frame-sync handshake | 70% | Implement frame-rate lock + timestamp logging |
| 5. AO Creases | 25% | Refine crease darkness detection algorithm | 80% | Improve gradient-based crease detection threshold |

### Week 2 Cumulative Result

**Tests Passed**: 4 of 5 (80% pass rate)  
**Grade**: B (75-85 points on AAA rubric)  
**Spec Fidelity**: ~0.81 (81% of declared parameters verified)

**Breakdown**:
- Technical Correctness: 32/40 (4 tests pass, 5 declared, 80% coverage)
- Stability/Performance: 24/25 (all criteria crash-free; FPS stable)
- Design Checklist: 16/20 (radiometry, shadow profile, contact detail all checked; AO margin)
- Spec Fidelity: 12/15 (visor RGB/intensity/hue verified; shadow distance verified; AO resolution 1K confirmed)
- **Total: ~84/100 → B grade (borderline A)**

### Week 2 Remaining Gaps

1. **Criterion 4 (Dynamic Update)**: Frame-by-frame capture timing may still have 1-2 frame lag; accept as "within spec" or refine sleepwalker tick sync.
2. **Criterion 5 (AO Texture)**: Visual checks (knuckle shading, silhouette 3D) still subjective; confidence ~0.80. Consider ML-based edge detection.
3. **Criterion 1 margin**: Radiometry still sensitive to screenshot lighting conditions; may fluctuate week-to-week. Recommend re-measuring under controlled beat script lighting.

---

## 6. Grading Rubric Mapping

### AAA-Expanded Result Grader Integration

**Category Weights** (400-point scale):

| Category | Points | Evidence Source | Week 1 | Week 2 |
|---|---|---|---|---|
| Technical Correctness (tests pass × coverage) | 40 | C1-C5 test results | 8/40 | 32/40 |
| Stability & Performance | 25 | Telemetry (crash-free, FPS ≥60) | 22/25 | 24/25 |
| Design Checklist (feedback, consistency, meaningful params, fail-safety, balance) | 20 | C1-C5 checks + agent judgment | 12/20 | 16/20 |
| Spec Fidelity (parameters verified vs. declared) | 15 | evidence.spec_fidelity | 6/15 | 12/15 |
| Player Immersion (visual polish, animation) | 50 | C3, C5 visual checks | 10/50 | 35/50 |
| Visual Fidelity (lighting quality, AO detail) | 35 | C1, C2, C5 measurements | 5/35 | 28/35 |
| *Other categories* | 215 | Deferred to other features | — | — |
| **SUBTOTAL (Lighting-relevant)** | 185 | **Week 1: ~63/185** | **Week 2: ~147/185** |

---

## 7. Frame Audit (Pre-Verification Checklist)

Before declaring testing complete, answer:

1. **Proxy vs. Target**: Are we measuring the right thing?
   - ✓ Radiometry measures actual color output (not proxy)
   - ✓ Shadow distance measures engine parameter + visual effect
   - ✓ Contact shadows measure fine-detail illumination (target)
   - ⚠ Dynamic update rate measures latency, not visual smoothness (proxy)
   - ✓ AO texture quality measures resolution + visibility (target)

2. **Who judges the judge?**
   - ✓ radiometry_probe.py is deterministic (no LM)
   - ✓ MCP inspect is engine-authoritative
   - ⚠ Vision analysis (C3, C5) uses heuristic darkness/contrast thresholds (may need tuning)
   - ✓ Sleepwalker beat script is reproducible

3. **Fixing artifact or generator?**
   - All test implementations are in PlayerCharacterLightingTests.cpp (generator-owned)
   - radiometry_probe.py is a new measurement tool (not a generator; independent)
   - Evidence collection follows standard schema (consistent with other features)

4. **What looks good but is wrong?**
   - ⚠ Radiometry may read as "in spec" if HDR screenshot captures wrong tone curve
   - ⚠ Shadow distance may match numerically but visual horizon misaligned (perspective effect)
   - ⚠ Contact shadows may show dark recesses from model geometry, not AO
   - ✓ Dynamic update metrics are frame-truth (hard to fake)
   - ⚠ AO crease detection may trigger on unrelated shadows

---

## 8. File Summary

### New Files Created

| File | Purpose | Size |
|---|---|---|
| `Source/.../Tests/PlayerCharacterLightingTests.h` | Test declarations (5 criteria + helpers) | 120 lines |
| `Source/.../Tests/PlayerCharacterLightingTests.cpp` | Test implementations (full C++ logic) | 450 lines |
| `core/radiometry_probe.py` | Radiometry + AO texture analysis (Python) | 400 lines |
| `core/lighting_evidence_schema.json` | Evidence schema for result grader | 400 lines |
| `docs/LIGHTING_TEST_DESIGN.md` | This design document | 500 lines |

### Integration Points

- **DSL Spec** → Criteria pass/fail (automated)
- **MCP Tools** → Engine state + screenshots (existing + radiometry_probe)
- **Result Grader** → Evidence JSON → Grade (A/B/C/F)
- **Sleepwalker** → Beat scripts for criteria 3-4 (PIE testing)
- **Graph** → record_grade + record_loop (DNA tracking)

---

## Next Steps

1. **Week 1 Go-Live**:
   - Compile C++ tests into UE5 project
   - Deploy radiometry_probe.py to core/ with numpy dependency
   - Create initial sleepwalker beat scripts (skeleton)
   - Run first automation pass; capture baseline evidence
   - Record C-grade with per-category breakdown

2. **Week 2 Refinement**:
   - Tune radiometry threshold calibration (test against known visor assets)
   - Implement frame-sync timing in sleepwalker beat scripts
   - Enhance vision analysis heuristics (crease detection, edge contrast)
   - Run repeat automation; measure improvement trajectory
   - Target B-grade with 80%+ spec fidelity

3. **Automated Observation** (Sleepwalker II):
   - Playtest with real character under PIE
   - Verify visual quality matches grade (frame audit validation)
   - Record surprise/deviation if metrics ≠ observed reality
   - Automated observation verdict (accepted/rejected) → final feature state

---

**Design completed**: 2026-07-07  
**Implementation status**: Ready for Week 1 deployment  
**Estimated effort**: 16-20 agent-hours total (Week 1-2)
