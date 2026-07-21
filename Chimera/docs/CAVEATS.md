# Caveats — Things That Did Not Work, Why, and What To Do About Them

> Written 2026-07-21 after the first successful level build.
> Every agent reads this before building the level. These are not opinions —
> they are failures witnessed and measured.

---

## 1. D3D12 Crashes on Launch

**Symptom:** `EXCEPTION_PRIV_INSTRUCTION` in `D3D12RHI` at startup.
**Root cause:** Unknown — likely GPU driver (NVIDIA 610.47) + VRAM pressure
(LM Studio holding 19.8GB/24.5GB) + UE5.8 D3D12 codepath.
**Workaround:** Launch with `-d3d11`:
```
"/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe"
  "E:/PythonChimera/Chimera/Chimera.uproject" -d3d11
```
**Cost:** D3D11 disables some atmosphere rendering features (atmosphere sun light).
**If fixed:** Try updating NVIDIA driver or freeing VRAM by pausing LM Studio.

---

## 2. Editor Exits After -ExecutePythonScript

**Symptom:** The editor runs the build script then shuts down immediately.
**Root cause:** `-ExecutePythonScript` runs the script after init, then the editor
exits (expected behavior — it's for headless automation).
**Workaround:** Launch WITHOUT `-ExecutePythonScript` to keep the editor open.
Run the script manually from the Python console:
> Window → Developer Tools → Python → `exec(open("E:/PythonChimera/Chimera/build_level.py").read())`
**If editing the level:** Always launch without `-ExecutePythonScript`.

---

## 3. SkySphere Blueprint Cannot Be Spawned

**Symptom:** `[ERR] Cannot load mesh: /Engine/Blueprints/Sky/BP_SkySphere.BP_SkySphere`
**Root cause:** Two issues. First, `spawn_static_mesh` tries to load it as a
StaticMesh, but it's a Blueprint (needs `spawn_actor_from_object`). Second, the
Blueprints class path requires the GENERATED class, not the asset registry path.
**Workaround:** Use the editor's Place Actors panel to drag BP_SkySphere into the
level. Or use the correct loaded Blueprint class:
```python
bp = unreal.load_object(name="/Engine/Blueprints/Sky/BP_SkySphere.BP_SkySphere", outer=None)
```
**Status:** Needs a `spawn_blueprint` path in build_level.py.

---

## 4. DirectionalLight Has No attenuation_radius

**Symptom:** `Failed to find property 'attenuation_radius' on 'DirectionalLightComponent'`
**Root cause:** Only PointLightComponent has an attenuation radius. Directional
light is infinite — it illuminates the entire scene.
**Fix applied:** Added conditional check — only set `attenuation_radius` on
PointLightComponent.

---

## 5. enable_atmosphere_sun_light Property Missing in D3D11

**Symptom:** `Failed to find property 'enable_atmosphere_sun_light' on 'DirectionalLightComponent'`
**Root cause:** The property exists in D3D12 but may not in D3D11 mode, or the
property name is different (`atmosphere_sun_light`, `cast_atmosphere_shadows`?).
**Workaround:** Removed the property set — sun still works, just without
atmosphere integration.
**If fixed:** Try without `-d3d11`.

---

## 6. EditorActorSubsystem Deprecated Since UE5.2

**Symptom:** `DeprecationWarning: Creating an instance of an Editor subsystem
has been deprecated since UE 5.2`
**Root cause:** UE5.2+ requires `unreal.get_editor_subsystem(unreal.EditorActorSubsystem)`
instead of `unreal.EditorActorSubsystem()`.
**Fix applied:** Changed all subsystem instantiations to `get_editor_subsystem()`.

---

## 7. MCP Bridge HTTP Port Not Responding

**Symptom:** `http://localhost:3000/mcp` connection refused.
**Root cause:** The McpAutomationBridge plugin loads in the editor (confirmed in
logs: "MCP Automation Bridge module shut down") but the HTTP server at port 3000
requires the separate chiR24-unreal-mcp Node.js process to be running.
**Workaround:** Use the UE5 Python console directly instead of MCP.
**Status:** The `.mcp.json` config points to `localhost:3000` but the bridge
process needs to be started separately.

---

## 8. Level Uses Placeholder Geometry

**Symptom:** Resources are spheres. NPCs are cylinders. The shelter is a disk.
**Root cause:** No custom meshes or textures exist for this game. Everything is
UE5 engine primitives (Sphere, Cylinder, Plane).
**Known:** The element catalog has 69,749 elements but ~4 are in use.
**Fix path:** Each rung's decoded parameters need a corresponding mesh/material
in the Content browser. Until then, the game looks like a dev environment.

---

## 9. No Main Menu

**Symptom:** Game drops straight into the level.
**Root cause:** No UI system has been built. No HUD. No menu.
**Fix path:** Create a UMG widget blueprint for the main menu. Add level
blueprint to show it on game start.

---

## 10. No Audio, No VFX, No Save/Load

**Symptom:** Silent. No particles. No persistence.
**Root cause:** None of these systems have been connected to the pipeline.
**Fix path:** Each is a separate rung waiting for its decoded parameters to be
spawned in the level.

---

## 11. The Level Was Built From JSON, Not Trained Output

**Symptom:** The build script reads `docs/decoded/*.json` but these are the
*decoded parameters* — the trained winners written as JSON by the decoder.
**Correctness check:** The composition pass verified 12/12 inter-rung seams
consistent. The parameters are internally coherent.
**If rebuilding:** Always run `python -m core.composition_check` first to verify
seams before running the level builder.

---

## Summary

| Issue | Workaround | Permanent Fix |
|-------|-----------|---------------|
| D3D12 crash | `-d3d11` | Driver update / VRAM management |
| Editor auto-exit | Don't use `-ExecutePythonScript` | Headless mode is for CI only |
| SkySphere | Manual placement | Fix Blueprint spawn path |
| Light properties | Conditional checks | None needed |
| MCP bridge | Use Python console | Start chiR24 process |
| Placeholder art | N/A | Create game meshes |
| No menu | N/A | Build UMG widget |
