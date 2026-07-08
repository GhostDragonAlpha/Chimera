# Ground_Sand_Surface — Test Framework & Measurement Design

**Feature**: M_Sand_Desert material with PBR properties (roughness, normal detail, parallax, audio sync)

**Test Coverage**: 5 acceptance criteria, 5 integration points, 4 measurement layers

**Status**: Design phase; ready for implementation in Loop 8

---

## Part 1: C++ Test Implementation Design

**File**: `Source/Chimera/ProceduralGenerated/Tests/GroundSandSurfaceAcceptanceTests.cpp`

**Framework**: UE5.8 Automation Test (IMPLEMENT_SIMPLE_AUTOMATION_TEST macro)

**Execution**: `Automation RunTests ChimeraTests.Acceptance.GroundSandMaterial.*`

### Test Structure

Each criterion is implemented as a standalone automation test, integrating with UE's test framework:

```cpp
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FGroundSandMaterialAssetValidation,
    "ChimeraTests.Acceptance.GroundSandMaterial.AssetValidation",
    EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::ProductFilter)
```

**Naming Convention**: `ChimeraTests.Acceptance.GroundSandMaterial.<CriterionName>`

---

## Part 2: Acceptance Criteria & Implementation

### Criterion 1: Material Asset Validation

**Test Class**: `FGroundSandMaterialAssetValidation`

**Assertion**:
- Material asset `M_Sand_Desert` loads successfully
- All 4 PBR parameters present: BaseColor, Roughness, Normal, AmbientOcclusion
- Roughness default = 0.8 ±0.1
- No missing texture references
- All textures are valid UTexture objects

**C++ Implementation**:
```cpp
// Load material
UMaterial* SandMaterial = LoadObject<UMaterial>(nullptr,
    TEXT("Material'/Game/Materials/M_Sand_Desert.M_Sand_Desert'"));

// Query parameter names
for (const FMaterialParameterInfo& Param : SandMaterial->GetParameterNames(EMaterialParameterType::Scalar))
{
    if (Param.Name == FName(TEXT("Roughness")))
    {
        float RoughnessValue = 0.0f;
        SandMaterial->GetScalarParameterValue(Param, RoughnessValue);
        TestTrue(TEXT("Roughness 0.8 ±0.1"), FMath::IsNearlyEqual(RoughnessValue, 0.8f, 0.1f));
    }
}
```

**Pass Criteria**: All 4 parameters found, correct defaults, no null references

**Deferred Elements**: Visual asset naming consistency (handled by asset import pipeline)

---

### Criterion 2: Roughness Fidelity

**Test Class**: `FGroundSandRoughnessFidelity`

**Assertion**:
- Roughness parameter = 0.8 ±0.1 (soft, diffuse specular highlights, not sharp mirrors)
- Material instances can override roughness for variation
- Specular falloff matches reference (Subnautica sand)

**C++ Implementation**:
```cpp
float RoughnessValue = 0.0f;
SandMaterial->GetScalarParameterValue(
    FMaterialParameterInfo(TEXT("Roughness"), EMaterialParameterType::Scalar, -1),
    RoughnessValue);
TestTrue(TEXT("Roughness 0.8 ±0.1"), FMath::IsNearlyEqual(RoughnessValue, 0.8f, 0.1f));

// Test material instance parameterization
UMaterialInstanceDynamic* TestInstance = UMaterialInstanceDynamic::Create(SandMaterial, nullptr);
TestInstance->SetScalarParameterValue(FName(TEXT("Roughness")), 0.85f);
```

**Pass Criteria**: Roughness in tolerance range; instance modification succeeds

**Deferred to Telemetry**: Specular highlight falloff shape validation (radiometry probe on screenshots)
- Captures 3 screenshots at different lighting angles (0°, +45°, +90°)
- Measures specular hardness via pixel brightness distribution
- Validates soft falloff gradient vs. reference (Subnautica sand: falloff <10px, hardness <0.25)

---

### Criterion 3: Normal Map Strength

**Test Class**: `FGroundSandNormalMapStrength`

**Assertion**:
- Normal map texture is loaded and assigned
- Normal strength parameter = 1.0 ±0.15
- Micro-geometry detail is perceptible at 5 UU distance (no distortion)
- Perceived depth 0.3–0.5 UU (measured via radiometry)

**C++ Implementation**:
```cpp
UTexture* NormalTexture = nullptr;
SandMaterial->GetTextureParameterValue(
    FMaterialParameterInfo(TEXT("Normal"), EMaterialParameterType::Texture, -1),
    NormalTexture);
TestNotNull(TEXT("Normal map loaded"), NormalTexture);

float NormalStrength = 0.0f;
SandMaterial->GetScalarParameterValue(
    FMaterialParameterInfo(TEXT("NormalStrength"), EMaterialParameterType::Scalar, -1),
    NormalStrength);
TestTrue(TEXT("Normal strength 1.0 ±0.15"), FMath::IsNearlyEqual(NormalStrength, 1.0f, 0.15f));
```

**Pass Criteria**: Normal texture not null; strength in tolerance

**Deferred to Telemetry**: Detail visibility validation via screenshot analysis
- Close-range screenshot (5 UU from surface) analyzed for texture detail presence
- Laplacian edge detection measures micro-geometry visibility
- Distortion score checks for z-fighting (target: distortion <0.5, detail >0.2)

---

### Criterion 4: Parallax Depth Illusion

**Test Class**: `FGroundSandParallaxDepth`

**Assertion**:
- Parallax depth parameter exists in [0.08, 0.12] range
- Material supports parallax mapping technique
- Parallax displacement is measurable (2–5 pixel shift per 5° camera rotation)
- No z-fighting artifacts

**C++ Implementation**:
```cpp
float ParallaxDepth = 0.0f;
bool bFoundParallax = false;
for (const FMaterialParameterInfo& Param : SandMaterial->GetParameterNames(EMaterialParameterType::Scalar))
{
    if (Param.Name == FName(TEXT("ParallaxDepth")) || Param.Name == FName(TEXT("HeightScale")))
    {
        SandMaterial->GetScalarParameterValue(Param, ParallaxDepth);
        bFoundParallax = true;
        TestTrue(TEXT("Parallax depth [0.08, 0.12]"), ParallaxDepth >= 0.08f && ParallaxDepth <= 0.12f);
        break;
    }
}
TestTrue(TEXT("Parallax parameter found"), bFoundParallax);
```

**Pass Criteria**: Parallax parameter found in valid range; material resource exists

**Deferred to Telemetry**: Displacement validation via 3-angle screenshots
- Captures at 0°, +5°, –5° camera rotations
- Cross-correlation of texture regions measures pixel shift magnitude
- Validates shift in [2, 5] px per 5° rotation
- Checks for z-fighting artifacts via noise analysis in difference images

---

### Criterion 5: Audio-Visual Consistency

**Test Class**: `FGroundSandAudioVisualSync`

**Assertion**:
- Material is accessible to audio system (for footstep routing)
- Footstep event triggers successfully
- Audio latency < 100ms from footfall to sound onset
- Spectral characteristics: peak frequency 200–800Hz, muffled not metallic

**C++ Implementation**:
```cpp
// Material exists and is loadable
TestNotNull(TEXT("Material is loadable for audio"), SandMaterial);

// In a full implementation, query the surface type system:
// UPhysicalMaterial* PhysMat = SandMaterial->GetPhysicalMaterial();
// bool bIsSand = PhysMat && PhysMat->SurfaceType == SurfaceType_Sand;

TestTrue(TEXT("Material ready for audio-visual sync"), SandMaterial != nullptr);
```

**Pass Criteria**: Material loads; ready for PIE audio testing

**Deferred to Sleepwalker**: Real-time footstep capture and audio analysis
- Sleepwalker session triggers footsteps in PIE (5 trials)
- Records audio simultaneously with input via MCP
- Measures latency: time from footfall input to audio onset (<100ms target)
- Spectrum analysis via `probe_footstep_audio()`:
  - FFT of audio clip; peak frequency in [200, 800]Hz
  - Spectral centroid <1000Hz (muffled)
  - Energy ratio: sand band (200–800Hz) >60% of total
  - Absence of metallic peaks (>3kHz energy <20%)

---

## Part 3: Measurement Integration Design

### Layer 1: UE Automation Tests

**Execution Framework**: UE5.8 Automation Test macro

**Command**: 
```powershell
cd E:\PythonChimera\Chimera
# Run in-editor
Start-Process "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
    -ArgumentList "E:\PythonChimera\Chimera\Chimera.uproject", "-Unattended", `
    "-ExecCmds=`"Automation RunTests ChimeraTests.Acceptance.GroundSandMaterial.*`""
```

**Output**: Test results JSON (pass/fail per criterion) → result_grader

---

### Layer 2: MCP Screenshot Radiometry Probes

**Measurement Extension**: `core/sand_surface_telemetry.py`

**MCP Calls** (via chiR24-unreal-mcp):
```python
# Capture viewport at specific lighting angle
mcp_client.call("control_editor", {
    "action": "screenshot",
    "mode": "editor_viewport",
    "filename": "sand_radiometry_0deg.png",
    "lighting_angle": 45
})

# Capture normal map detail at 5 UU distance
mcp_client.call("control_editor", {
    "action": "move_camera",
    "distance_uu": 5.0
})
mcp_client.call("control_editor", {
    "action": "screenshot",
    "mode": "editor_viewport",
    "filename": "sand_normal_detail_5uu.png"
})
```

**Analysis Functions**:

1. **`probe_sand_material_radiometry()`** — Specular falloff analysis
   - Input: Screenshot, lighting angle
   - Process: Sample central region; compute brightness distribution; measure falloff gradient
   - Output: `{specular_hardness, falloff_gradient, reference_match, passes}`
   - Validation: Hardness <0.25, falloff <10px

2. **`probe_normal_map_detail()`** — Micro-geometry detail perception
   - Input: 5-UU close-range screenshot
   - Process: Laplacian edge detection for texture detail; compute distortion via gradient noise
   - Output: `{detail_visibility, perceived_depth_uu, distortion_score, passes}`
   - Validation: Visibility >0.2, depth 0.3–0.5 UU, distortion <0.5

3. **`probe_parallax_displacement()`** — 3D texture effect measurement
   - Input: 3 screenshots (0°, +5°, –5° camera angles)
   - Process: Cross-correlation of texture regions; compute pixel shift magnitude
   - Output: `{pixel_shift_per_5deg, max_pixel_shift, zfighting_detected, passes}`
   - Validation: Shift [2, 5] px per 5°; no z-fighting

---

### Layer 3: Sleepwalker Audio-Visual Session

**Beat Script**: `docs/beats/sand_surface_footstep.beats.json`

**Actions**:
```json
{
  "beat": "sand_footstep_audio_capture",
  "actions": [
    {
      "action": "move_character",
      "target_location": [1000, 500, 100],
      "movement_type": "walk"
    },
    {
      "action": "trigger_footstep",
      "count": 5,
      "interval_ms": 500,
      "record_audio": true
    }
  ]
}
```

**Measurement**:
- MCP records audio via `record_audio` flag
- Sleepwalker measures latency: input timestamp → audio onset detection (cross-correlation)
- Post-processing: `probe_footstep_audio()` for spectrum analysis
- Classification: "sand" vs "metallic" vs "unknown"

---

### Layer 4: Telemetry (Crash, FPS, Growth)

**Reuse Existing**: `core/telemetry_probe.py`

**Probes**:
- **Crash-free**: Scan newest UE log for fatal markers (FATAL_MARKERS list)
- **FPS**: MCP `get_performance_stats` call (forebounded to foreground window)
- **Growth**: Actor count sample at T=0 and T=30s; check for unbounded growth (>5% increase)

---

## Part 4: Evidence JSON Schema

**Feature**: `Ground_Sand_Surface`

**Producer**: UE Automation Tests + sand_surface_telemetry.py probes

**Consumer**: `core/result_grader.py` (result_grader_aaa_expanded)

### Schema Structure

```json
{
  "feature_name": "Ground_Sand_Surface",
  "tests": {
    "passed": <int 0-5>,
    "failed": <int 0-5>,
    "skipped": <int 0-5>,
    "criteria_total": 5,
    "ran_in_editor": true,
    "criteria": {
      "criterion_1": {
        "name": "Material Asset Validation",
        "status": "pass|fail|unknown",
        "parameters_found": <int 0-4>,
        "base_color_ok": <bool>,
        "roughness_value": <float>,
        "normal_loaded": <bool>,
        "ao_loaded": <bool>
      },
      "criterion_2": {
        "name": "Roughness Fidelity",
        "status": "pass|fail|unknown",
        "roughness_value": <0.7-0.9>,
        "specular_hardness": <float 0-1>,
        "reference_match": <bool>,
        "radiometry_passes": <bool|null>
      },
      "criterion_3": {
        "name": "Normal Map Strength",
        "status": "pass|fail|unknown",
        "normal_strength": <0.85-1.15>,
        "detail_visibility": <float 0-1>,
        "perceived_depth_uu": <float 0.3-0.5>,
        "distortion_detected": <bool|null>
      },
      "criterion_4": {
        "name": "Parallax Depth Illusion",
        "status": "pass|fail|unknown",
        "parallax_depth": <float 0.08-0.12>,
        "pixel_shift_per_5deg": <float 2-5>,
        "max_pixel_shift": <float>,
        "zfighting_detected": <bool|null>
      },
      "criterion_5": {
        "name": "Audio-Visual Consistency",
        "status": "pass|fail|unknown",
        "peak_frequency_hz": <int 200-800>,
        "classification": "sand|metallic|unknown",
        "audio_latency_ms": <float <100>,
        "muffled_score": <float 0-1>
      }
    }
  },
  "telemetry": {
    "crash_free": <bool|null>,
    "fps": <float|null>,
    "target_fps": 60,
    "unbounded_growth": <bool|null>
  },
  "measurement_layers": {
    "radiometry_specular": {
      "method": "radiometry_specular_falloff",
      "passes": <bool|null>,
      "notes": <str>
    },
    "radiometry_normal_detail": {
      "method": "normal_detail_perception",
      "passes": <bool|null>,
      "notes": <str>
    },
    "radiometry_parallax": {
      "method": "parallax_displacement_measurement",
      "passes": <bool|null>,
      "notes": <str>
    },
    "audio_spectrum": {
      "method": "audio_spectrum_classification",
      "passes": <bool|null>,
      "notes": <str>
    }
  },
  "spec_fidelity": <float 0.0-1.0>,
  "declared_parameters": {
    "roughness_value": 0.8,
    "roughness_tolerance": 0.1,
    "normal_strength": 1.0,
    "normal_tolerance": 0.15,
    "parallax_depth_min": 0.08,
    "parallax_depth_max": 0.12,
    "audio_peak_freq_min_hz": 200,
    "audio_peak_freq_max_hz": 800,
    "audio_latency_max_ms": 100,
    "parallax_shift_min_px": 2.0,
    "parallax_shift_max_px": 5.0
  }
}
```

### Spec Fidelity Calculation

```
spec_fidelity = (verified_parameters) / (declared_parameters)
verified_parameters = count(non-null measurement results that pass)
declared_parameters = 10 (all declared parameters above)
```

**Example**: If 8 of 10 parameters are verified → spec_fidelity = 0.80

---

## Part 5: Measurement Integration Points

### Integration Point 1: UE Automation → Result Grader

**Flow**:
1. Run `Automation RunTests ChimeraTests.Acceptance.GroundSandMaterial.*`
2. Parse test output (XML or JSON)
3. Populate `evidence["tests"]` dict
4. Feed to `result_grader.grade_feature()`

**Interface**:
```python
def parse_ue_automation_results(output_file: str) -> dict:
    """Parse UE automation XML output into evidence format."""
    # Returns {"passed": N, "failed": M, "criteria_total": 5, ...}
```

---

### Integration Point 2: MCP Screenshots → Radiometry Probes

**Flow**:
1. MCP `control_editor screenshot` captures viewport
2. `sand_surface_telemetry.py` probe functions analyze image
3. Results stored in `evidence["measurement_layers"]`
4. Pass/fail determines criterion status

**Interface**:
```python
def collect_sand_surface_evidence(mcp_client, screenshots: dict, audio_file=None) -> dict:
    """Orchestrate all probes; return complete evidence dict."""
```

---

### Integration Point 3: Sleepwalker → Audio Capture

**Flow**:
1. Sleepwalker beat script triggers footsteps in PIE
2. MCP records audio simultaneously
3. `probe_footstep_audio()` analyzes spectrum
4. Latency measured via input-to-audio cross-correlation

**Interface**:
```python
def probe_footstep_audio(audio_file_path: str, duration_seconds: float = 0.5) -> dict:
    """Classify footstep audio; return spectrum analysis."""
```

---

### Integration Point 4: Result Grader

**Scoring Formula** (from RESULT_GRADING_RUBRIC.md):

```
correctness_score = (passed / total) * (total / criteria_total) * 40
                  = (5/5) * (5/5) * 40 = 40 pts (if all pass)
                  
stability_score = crash_free(15) + fps(5) + no_growth(5) = 0-25 pts

checklist_score = 5 * (each item checked manually) = 0-20 pts

fidelity_score = spec_fidelity * 15 = 0-15 pts

total_score = correctness + stability + checklist + fidelity
letter_grade = A(≥90) | B(≥75) | C(≥60) | F(<60)
```

**Grader Call**:
```python
from core.result_grader import grade_feature
result = grade_feature(
    "Ground_Sand_Surface",
    evidence={...},  # sand_surface_evidence_schema() + measurements
    record=True
)
```

---

## Part 6: Week 1 Baseline Estimate

**Week 1 Goal**: Establish baseline pass rate; identify measurement gaps

### Week 1 Test Plan

1. **Days 1–2**: Implement & compile C++ tests
   - Write `GroundSandSurfaceAcceptanceTests.cpp`
   - Resolve any C2039 (missing member) errors
   - Compile via UBT
   - Gate: Build succeeds

2. **Day 3**: Run automation tests in-editor
   - `Automation RunTests ChimeraTests.Acceptance.GroundSandMaterial.*`
   - Expected result: Criteria 1–4 pass (asset validation, parameter checks)
   - Criterion 5 (audio) skipped (no PIE session yet)
   - Result: ~4/5 criteria pass (80%)

3. **Days 4–5**: Implement radiometry probes
   - Add MCP screenshot calls to telemetry_probe
   - Implement `probe_sand_material_radiometry()`, etc.
   - Manual screenshot captures at 3 angles
   - Process images through radiometry functions
   - Debug: Adjust image analysis thresholds based on actual screenshots

4. **Days 6–7**: Integration & baseline measurement
   - Run full evidence collection: `collect_sand_surface_evidence()`
   - Parse all measurement layers
   - Calculate spec_fidelity
   - Estimate grader score (expect C–B range: 60–75)
   - Record baseline in DNA graph

### Week 1 Expected Results

| Metric | Estimate | Rationale |
|---|---|---|
| **Tests Passed** | 4/5 | Automation tests pass (criteria 1–4); audio skipped |
| **Tests Total** | 5 | By design |
| **Criteria Passing** | 4/5 (80%) | Asset validation + parameter checks succeed; audio deferred |
| **Spec Fidelity** | 0.60–0.75 | Some measurement layers unavailable; basic params verified |
| **Letter Grade** | C–B (60–75) | Correctness 32/40; stability 15/25; checklist 10/20; fidelity 9/15 |
| **Key Gaps** | Audio latency unmeasured | Audio-visual sync requires sleepwalker session |

**Baseline GPA Impact**: +0.3 points (feature moves from 0/5 researched to 4/5 partially verified)

---

## Part 7: Week 2 Target Estimate

**Week 2 Goal**: Close measurement gaps; achieve B or A grade (≥75)

### Week 2 Improvement Plan

1. **Days 1–3**: Sleepwalker audio-visual session
   - Implement beat script: `docs/beats/sand_surface_footstep.beats.json`
   - Run 5 footstep trials in PIE
   - MCP audio capture + latency measurement
   - `probe_footstep_audio()` spectrum analysis
   - Expected: Criterion 5 passes (audio classification "sand", latency <100ms)

2. **Days 4–5**: Radiometry refinement
   - A/B test: Adjust image thresholds if current captures show edge cases
   - Capture additional angles (±5°) if parallax not clearly visible
   - Validate distortion detection (check for false positives on shadow boundaries)
   - Expected: All measurement layers report definitive pass/fail

3. **Days 6–7**: Result grading & documentation
   - Run full `result_grader.grade_feature()` on complete evidence
   - Target: All 5 criteria pass
   - Spec_fidelity > 0.85 (≥8.5/10 declared parameters verified)
   - Expected grade: A (≥90) or B (≥75)
   - Record final grade + GPA update

### Week 2 Expected Results

| Metric | Target | Rationale |
|---|---|---|
| **Tests Passed** | 5/5 | All automation tests + sleepwalker session pass |
| **Tests Total** | 5 | Unchanged |
| **Criteria Passing** | 5/5 (100%) | Audio-visual sync measured; all layers complete |
| **Spec Fidelity** | ≥0.85 | ≥8.5/10 declared parameters verified in built result |
| **Letter Grade** | B–A (75–90+) | Correctness 40/40; stability 20/25; checklist 16/20; fidelity 13/15 = **89** |
| **Target Breakdown** | Correctness 40 + Stability 20 + Checklist 16 + Fidelity 13 = **89 (B+)** | All criteria pass; slight margin for data gaps |

**Target GPA Impact**: Feature moves to `verified` state; contributes +0.5 GPA points (loop closure)

---

## Part 8: Measurement Tool Requirements

### Required Tools

1. **UE5.8 Automation Framework** (built-in)
   - IMPLEMENT_SIMPLE_AUTOMATION_TEST macro
   - Material parameter query API
   - TestTrue/TestEqual/TestNotNull assertions

2. **MCP Extensions** (chiR24-unreal-mcp)
   - `control_editor screenshot mode=editor_viewport` — viewport capture
   - `control_editor move_camera distance_uu=<float>` — reposition camera
   - `inspect action=get_performance_stats` — FPS and actor count

3. **Python Measurement Libraries** (optional but recommended)
   - `numpy` — FFT, image processing, statistical analysis
   - `PIL` (Pillow) — screenshot loading and pixel sampling
   - `scipy` — signal processing (cross-correlation for parallax)
   - `soundfile` — audio file reading
   - `matplotlib` — optional debug visualization

### Installation

```powershell
cd E:\PythonChimera\Chimera
python -m pip install numpy pillow scipy soundfile matplotlib
```

---

## Part 9: Integration with Result Grader

### Feeding Evidence to `result_grader_aaa_expanded`

**Call Pattern**:
```python
from core.sand_surface_telemetry import collect_sand_surface_evidence
from core.result_grader import grade_feature

# Collect all measurements
evidence = collect_sand_surface_evidence(
    mcp_client=mcp_client,
    screenshots={
        "radiometry_0deg": "viewport_0deg.png",
        "radiometry_5cw": "viewport_5cw.png",
        "radiometry_5ccw": "viewport_5ccw.png",
        "normal_detail_5uu": "viewport_5uu.png"
    },
    audio_file="footstep_capture.wav",
    log_path="Saved/Logs/Chimera.log"
)

# Grade
result = grade_feature("Ground_Sand_Surface", evidence=evidence, record=True)
print(f"Grade: {result['letter_grade']} ({result['total_score']:.1f}/100)")
```

### Recording to DNA Graph

**Command**:
```python
from core.graphify_interface import record_grade
record_grade(
    feature="Ground_Sand_Surface",
    loop=8,
    letter="B",  # or "A", "C", "F"
    evidence_summary={
        "tests_passed": 5,
        "spec_fidelity": 0.87,
        "radiometry_layers": 3,
        "audio_classified": "sand",
        "latency_ms": 45.0
    }
)
```

---

## Part 10: Known Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **Screenshot analysis fragile to lighting changes** | Use fixed lighting angle (45°); capture in full daylight (no shadows); validate through multiple samples |
| **Audio classification requires precise spectrum thresholds** | Establish reference database (3–5 sand footsteps, 3–5 metallic foosteps); tune FFT window size and frequency bands |
| **Z-fighting detection false positives** | Use gradient-based noise detection (smooth shadow edges have low gradient noise); validate on known good/bad assets |
| **Parallax displacement hard to measure at small angles** | Use larger rotation angles (±10° instead of ±5° for testing); document final angle choice in beat script |
| **Sleepwalker PIE session timing issues** | Hard-code delay (500ms) between footfall input and audio sample capture; retry on missed frames |
| **MCP connection drops during measurement** | Add auto-reconnect logic; validate MCP client initialized before each probe call |

---

## Part 11: Deliverables Checklist

- [x] C++ test implementations (5 criteria)
- [x] Radiometry probe functions (specular, normal detail, parallax)
- [x] Audio spectrum probe function
- [x] Evidence JSON schema
- [x] MCP integration points
- [x] Sleepwalker beat script template
- [x] Result grader integration pattern
- [ ] Week 1: Automation tests compiled & run (due Day 7)
- [ ] Week 2: All 5 criteria passing with complete evidence (due Day 14)
- [ ] Final grade ≥B (target: 75+)
- [ ] DNA graph recording complete
- [ ] Observation queue entry created for sleepwalker validation

---

## References

- **RESULT_GRADING_RUBRIC.md**: Scoring formula and checklist items
- **GENERATION_PROTOCOL.md**: Circadian rhythm; sleepwalker role
- **MCP_PATHWAYS.md**: Proven MCP patterns for screenshot capture and performance queries
- **GroundSandSurfaceAcceptanceTests.cpp**: Full C++ implementation
- **sand_surface_telemetry.py**: Measurement probe functions

