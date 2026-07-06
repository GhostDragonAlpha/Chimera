# Verification Studio — Architectural Plan

## Problem Statement

Visual verification screenshots from the UE5 editor viewport fail because:
1. **Multiple competing directional lights** render metallic materials as grey/blue
2. **Cluttered scene** — items are stacked on existing geometry
3. **No environment reflections** — gold metallic visor needs HDRI/reflections to show its sheen
4. **Inconsistent camera** — different angles per verification produce unreliable LM Studio comparisons

## Solution: Reusable Verification Studio Level

A single controlled environment level at `/Game/Chimera/Levels/L_VerificationStudio` used for ALL visual verification items. Items are swapped via script, lighting is fixed, camera is locked.

---

## 1. Level Layout

```
Top-Down View:

        [Rim Light]
            |
            |  (behind, above)
            |
  [Key] ---> 🎯 <--- [Fill]
   (L)     Pedestal    (R)
            |
            |
          📷 Camera
         (-200, 0, 100)
```

### Components

| Element | Type | Position | Scale | Material/Color |
|---------|------|----------|-------|----------------|
| **Floor** | Plane | (0, 0, -5) | (500, 500, 1) | Neutral grey 18% (RGB 0.5) with subtle grid |
| **Backdrop** | Curved cylinder (cyclorama) | (0, 0, 0) | Radius 400, Height 300 | Neutral grey (RGB 0.5) |
| **Pedestal** | Cylinder | (0, 0, 0) | R=50, H=20 | Neutral grey (RGB 0.5) |
| **Key Light** | DirectionalLight | (200, -150, 300) aim (0,0,50) | — | Intensity 10, Warm 5500K |
| **Fill Light** | DirectionalLight | (-120, 100, 200) aim (0,0,50) | — | Intensity 5, Cool 6500K |
| **Rim Light** | SpotLight | (0, -200, 250) aim (0,0,100) | — | Intensity 8, White, 30° cone |
| **Camera** | CineCameraActor | (-200, 0, 100) aim (0,0,50) | FOV 50mm | Resolution 1920x1080 |
| **Alternate Camera** | CineCameraActor | (-141, -141, 100) aim (0,0,50) | FOV 50mm | 3/4 view angle |

---

## 2. Lighting Design

### Why 3-Point Lighting?

The gold visor material uses:
- `Metallic = 1.0` — requires environment reflections to show color; without them metallic renders black
- `Roughness = 0.1` — near-mirror finish, highlights are sharp
- `Blend Mode = Translucent` — needs backlighting to show through

### Light Configuration

```
Key Light:    Direction  (45° azimuth, 30° elevation)
              Intensity  10.0 lux
              Color      Warm (R=1.0, G=0.95, B=0.85)
              Shadow     Cast shadows ON

Fill Light:   Direction  (-30° azimuth, 20° elevation)  
              Intensity  5.0 lux
              Color      Cool (R=0.85, G=0.90, B=1.0)
              Shadow     Cast shadows OFF

Rim Light:    Direction  (180° azimuth, 45° elevation)
              Intensity  8.0 lux (SpotLight)
              Color      White (R=1.0, G=1.0, B=1.0)
              Cone Angle 30°, Outer Cone 45°
              Shadow     Cast shadows OFF
```

### Skylight

If an HDRI cubemap texture exists in the project, apply it to a Skylight actor for environment reflections. Otherwise, use a simple SHDome with neutral ambient color (RGB 0.3).

**HDRI candidates to search for:**
- `/Engine/EngineSky/...` (check if any default HDRI exists)
- Only use if found — don't create one

---

## 3. Camera Setup

### Primary Camera (Front View)
```
Location:   X=-200, Y=0, Z=100
Rotation:   Pitch=0, Yaw=180, Roll=0
FOV:        50mm (~39.6° vertical)
Focus:      At (0, 0, 50) — pedestal center top
```

### Secondary Camera (3/4 View — optional)
```
Location:   X=-141, Y=-141, Z=100  
Rotation:   Pitch=0, Yaw=135, Roll=0
FOV:        50mm
```

### Viewport Configuration
- Resolution: 1920x1080
- ViewMode: Lit
- ShowFlags: Defaults
- PostProcess: Default (no DOF, no bloom)

---

## 4. Pedestal Design

A simple grey cylinder that provides:
- **Scale reference** (100cm diameter, 20cm height = ~3.3ft x 8in)
- **Neutral surface** that doesn't influence LM Studio color analysis
- **Clear center** at (0, 0, 10) top surface for item placement

Material: Simple constant color (RGB 0.5), no metallic, no roughness variation.

---

## 5. Verification Workflow Script

A Python script at `Chimera/Python/verification_studio_runner.py` that orchestrates the full cycle:

```python
# Pseudocode for verification_studio_runner.py

def verify_feature(feature_name, mesh_path, material_path, 
                   material_params, canonical_ref_path, camera="primary"):
    """
    Full verification loop for any feature.
    
    1. Open L_VerificationStudio level
    2. Clear actors tagged 'VerificationItem'
    3. Spawn mesh at (0, 0, 10) with tag
    4. Apply material
    5. Set material instance parameters (if any)
    6. Set viewport to camera
    7. Take screenshot via MCP control_editor.screenshot
       or pyautogui.screenshot()
    8. Send screenshot + canonical reference to LM Studio
    9. Parse LM Studio response (VERIFIED / NEEDS_REFINEMENT)
    10. If VERIFIED: record to DNA graph, return True
    11. If NEEDS_REFINEMENT: apply fix, loop back to step 7
    12. Return (verified, screenshot_path, lm_studio_response)
```

### MCP Tools Used

| Step | MCP Tool | Action |
|------|----------|--------|
| 1 | `manage_level.load_level` | Load L_VerificationStudio |
| 2 | `control_actor.find_by_tag` + `control_actor.delete` | Clear previous items |
| 3 | `control_actor.spawn_actor` | Spawn mesh at pedestal |
| 4 | `control_actor.set_actor_material` | Apply material to mesh |
| 5 | `system_control.execute_python` | Set material parameters via UE Python |
| 6 | `control_editor.set_viewport_camera` | Position viewport |
| 7 | `control_editor.screenshot` or pyautogui | Take screenshot |
| 8 | HTTP POST to LM Studio | Send for verification |
| 9 | stdout parsing | Parse response |
| 10 | `graphify_mutate` | Record to DNA graph |

---

## 6. Material Application Pathway (Critical)

**Problem found during previous runs:**
- `manage_asset.add_vector_parameter` creates **orphaned nodes** — NOT connected to material output pins
- `manage_asset.add_scalar_parameter` also creates **orphaned nodes**
- The default `MaterialExpressionConstant3Vector` and `MaterialExpressionConstant` remain connected

**Correct approach discovered:**
Use `system_control.execute_python` to run UE Python that:
1. Creates the material fresh via `MaterialFactoryNew`
2. Adds expressions via `MaterialEditingLibrary.create_material_expression`
3. Connects them via `MaterialEditingLibrary.connect_material_property`
4. The `execute_python` handler only accepts single-line scripts (multi-line crashes at line ~22)

**Single-line UE Python commands that work:**
```python
# Create material
mat = unreal.load_asset(...)
# Add and connect BaseColor
expr = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 100); expr.set_editor_property("constant", unreal.LinearColor(1.0, 0.85, 0.4, 1.0)); unreal.MaterialEditingLibrary.connect_material_property(expr, "", unreal.MaterialProperty.MP_BASE_COLOR)
# Add and connect Metallic
expr2 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 250); expr2.set_editor_property("r", 1.0); unreal.MaterialEditingLibrary.connect_material_property(expr2, "", unreal.MaterialProperty.MP_METALLIC)
# Add and connect Roughness
expr3 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 400); expr3.set_editor_property("r", 0.1); unreal.MaterialEditingLibrary.connect_material_property(expr3, "", unreal.MaterialProperty.MP_ROUGHNESS)
# Add and connect Opacity (for Translucent)
expr4 = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 550); expr4.set_editor_property("r", 0.7); unreal.MaterialEditingLibrary.connect_material_property(expr4, "", unreal.MaterialProperty.MP_OPACITY)
```

---

## 7. LM Studio Verification Endpoint

```python
import requests, json, base64

def verify_with_lm_studio(screenshot_path, canonical_path):
    with open(screenshot_path, "rb") as f:
        screenshot_b64 = base64.b64encode(f.read()).decode()
    with open(canonical_path, "rb") as f:
        canonical_b64 = base64.b64encode(f.read()).decode()
    
    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        json={
            "model": "qwen3.6-35b-a3b-mtp@iq2_m",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Does the gold visor in the first image match the Apollo 17 EVA suit visor canonical reference in the second image? Output exactly VERIFIED or NEEDS_REFINEMENT."},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{canonical_b64}"}}
                    ]
                }
            ],
            "max_tokens": 50
        }
    )
    return response.json()["choices"][0]["message"]["content"]
```

---

## 8. DNA Graph Recording

```python
from core.graphify_interface import mutate

mutate("visual_verification", {
    "feature": "Player_Character_Suit",
    "screenshot_path": "E:\\PythonChimera\\Chimera\\Saved\\Screenshots\\Player_Character_Suit_verified.png",
    "verified": True/False,
    "lm_studio_response": "<verbatim from LM Studio>",
    "verification_env": "L_VerificationStudio",
    "lighting_config": "3-point (key=10lux_warm, fill=5lux_cool, rim=8lux_white)"
})
```

---

## 9. Level Creation Steps (for implementation)

Use the following MCP commands in order:

1. **Create level directory**: Ensure `/Game/Chimera/Levels/` exists
2. **Create level asset**: Use `manage_level.create_level` with:
   - `levelPath`: `/Game/Chimera/Levels/L_VerificationStudio`
   - `template`: Leave empty for blank level
3. **Load the new level**: `manage_level.load_level`
4. **Spawn floor plane**: `control_actor.spawn_actor` with class `Plane` at (0,0,-5)
5. **Spawn pedestal cylinder**: `control_actor.spawn_actor` with class `Cylinder` at (0,0,0)
6. **Create directional lights**: Three lights with positions/colors from §2
7. **Spawn CineCameraActor**: at (-200,0,100) aiming at origin
8. **Save level**: `manage_level.save_level`
9. **Set viewport to camera**: `control_editor.set_viewport_camera` with camera position/rotation
10. **Verify lighting**: Take test screenshot, confirm neutral grey environment

---

## 10. Key Constraints

- The `system_control.execute_python` handler crashes on multi-line scripts — ALL UE Python must be single-line semicolon-separated
- The `manage_asset.add_vector_parameter` and `add_scalar_parameter` create orphaned nodes — DO NOT USE for material creation
- Always use `manage_asset.rebuild_material` after modifying material graph via Python
- Always `compile_material` before saving
- Use tag `VerificationItem` on all spawned verification meshes for easy cleanup
