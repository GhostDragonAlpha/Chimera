# MCP Pathways — Working Tool Sequences

## Overview

This document lists all proven MCP pathways for interacting with Unreal Engine 5.8 via the Chimera MCP bridge. Each pathway includes the exact tool, action, and parameter schema needed to execute it reliably.

**Query Rule**: Before using any tool, query Graphify first: `g.query("pathway", "what_you_want_to_do")` — see `THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` for the full rule.

---

## Working Pathways (12)

### 1. control_actor.spawn_actor
- **Tool**: `unreal_engine_control_actor`
- **Action**: `spawn_actor`
- **Parameters**: `{actorName: string, classPath: string}`
- **Example**: `spawn_actor(actorName="TestActor", classPath="/Game/VehicleTemplate/Meshes/SM_Track_10M.SM_Track_10M")`
- **Result**: Returns actor object with id, name, path, guid. Actor exists after spawn.
- **Notes**: Use existing mesh paths from the project (e.g., `/Game/Vehicles/SportsCar/SM_SportsCar.SM_SportsCar`). Editor meshes like `/Engine/EditorMeshes/Cube` are not available in this project.

### 2. control_actor.set_transform
- **Tool**: `unreal_engine_control_actor`
- **Action**: `set_transform`
- **Parameters**: `{actorName: string, location?: {x: number, y: number, z: number}, rotation?: {pitch: number, yaw: number, roll: number}, scale?: {x: number, y: number, z: number}}`
- **Example**: `set_transform(actorName="Player", location={x:0,y:5,z:130}, scale={x:1.5,y:1.5,z:1.5})`
- **Result**: Actor transform updated successfully.

### 3. control_actor.get_components
- **Tool**: `unreal_engine_control_actor`
- **Action**: `get_components`
- **Parameters**: `{actorName: string}`
- **Example**: `get_components(actorName="PlayerTestPlaceholder")`
- **Result**: Returns array of component names (e.g., `["StaticMeshComponent0"]`). Required before calling `set_component_property`.

### 4. control_actor.set_component_property
- **Tool**: `unreal_engine_control_actor`
- **Action**: `set_component_property`
- **Parameters**: `{actorName: string, componentName: string, properties: {key: value}}`
- **Example**: `set_component_property(actorName="GroundPlane", componentName="StaticMeshComponent0", properties={material: "/Game/Chimera/Materials/MAT_GroundSand/MAT_GroundSand"})`
- **Result**: Component property updated. Use this to apply materials, set visibility, adjust collision.

### 5. manage_asset.search_assets
- **Tool**: `unreal_engine_manage_asset`
- **Action**: `search_assets`
- **Parameters**: `{directory: string, classNames?: string[], limit?: number}`
- **Example**: `search_assets(directory="/Game/", classNames=["StaticMesh"], limit=1)`
- **Result**: Returns array of asset paths matching the search criteria.

### 6. control_editor.screenshot
- **Tool**: `unreal_engine_control_editor`
- **Action**: `screenshot`
- **Parameters**: `{filename: string}`
- **Example**: `screenshot(filename="phase2_refinement_v1.png")`
- **Result**: Screenshot saved to `Saved/Screenshots/phase2_refinement_v1.png`. Returns width, height, sizeBytes.

### 7. control_editor.set_camera_position
- **Tool**: `unreal_engine_control_editor`
- **Action**: `set_camera_position`
- **Parameters**: `{location: {x: number, y: number, z: number}, rotation: {pitch: number, yaw: number, roll: number}}`
- **Example**: `set_camera_position(location={x:0,y:-250,z:130}, rotation={pitch:0,yaw:0,roll:0})`
- **Result**: Camera position and rotation updated.

### 8. inspect.get_project_settings
- **Tool**: `unreal_engine_inspect`
- **Action**: `get_project_settings`
- **Parameters**: `{}` (none)
- **Example**: `get_project_settings()`
- **Result**: Returns projectName, engineVersion, buildConfig, projectDir, projectVersion.

### 9. inspect.get_material_details
- **Tool**: `unreal_engine_inspect`
- **Action**: `get_material_details`
- **Parameters**: `{objectPath: string}`
- **Example**: `get_material_details(objectPath="/Game/TestRoom/Mat_ISS_Floor/Mat_ISS_Floor")`
- **Result**: Returns objectPath, className, classPath. Note: detailed material parameters (BaseColor, Roughness, Metallic) are not returned by this action — use asset creation and property setting instead.

### 10. manage_level.list_levels
- **Tool**: `unreal_engine_manage_level`
- **Action**: `list_levels`
- **Parameters**: `{}` (none)
- **Example**: `list_levels()`
- **Result**: Returns currentWorldLevels array, allMaps array, currentMap path.

### 11. manage_level.create_light
- **Tool**: `unreal_engine_manage_level`
- **Action**: `create_light`
- **Parameters**: `{lightType: string, intensity: number, location: {x: number, y: number, z: number}}`
- **Example**: `create_light(lightType="Directional", intensity=100.0, location={x:0,y:0,z:0})`
- **Result**: Returns actorName (e.g., "DirectionalLight1"), actorPath, actorGuid. Light is spawned and exists after creation.

### 12. manage_asset.create_material
- **Tool**: `unreal_engine_manage_asset`
- **Action**: `create_material`
- **Parameters**: `{name: string, path: string}` — Note: use `path`, NOT `materialPath`
- **Example**: `create_material(name="MAT_GroundSand", path="/Game/Chimera/Materials/MAT_GroundSand")`
- **Result**: Returns assetPath (e.g., `/Game/Chimera/Materials/MAT_GroundSand/MAT_GroundSand.MAT_GroundSand`). Material is created but saved=false — call save action separately if needed.

### 13. professor_review
- **Tool**: N/A (text prompt to LM Studio via REST API)
- **Action**: Submit research summary for grading

### 14. manage_geometry.create_ship_exterior
- **Tool**: `unreal_engine_manage_geometry` + `unreal_engine_control_actor` + `unreal_engine_manage_asset`
- **Actions**: Multi-step pipeline for creating a procedural spacecraft exterior
- **Steps**:
  1. `manage_geometry.create_cylinder(radius=150, height=600, radialSegments=32)` → ship hull (GeneratedCylinder/DynamicMeshActor_0)
  2. `control_actor.set_transform(actorName="GeneratedCylinder", location={x:0,y:0,z:0})` → center hull
  3. `manage_geometry.create_cone(radius=120, height=200, radialSegments=32)` → cockpit nose (SM_Ship_Cockpit/DynamicMeshActor_1)
  4. `control_actor.set_transform(actorName="SM_Ship_Cockpit", location={x:0,y:0,z:400}, rotation={pitch:180,yaw:0,roll:0})` → nose forward
  5. `manage_geometry.create_box(width=40, height=60, depth=40)` → left thruster (GeneratedBox/DynamicMeshActor_2)
  6. `control_actor.set_transform(actorName="DynamicMeshActor_2", location={x:-80,y:0,z:-320})` → position left thruster
  7. `manage_geometry.create_box(width=40, height=60, depth=40)` → right thruster (GeneratedBox/DynamicMeshActor_3)
  8. `control_actor.set_transform(actorName="DynamicMeshActor_3", location={x:80,y:0,z:-320})` → position right thruster
- **Material Steps**:
  1. `manage_asset.create_material(name="MAT_Ship_Hull_Aluminum", path="/Game/Chimera/Materials/MAT_Ship_Hull_Aluminum")` → brushed aluminum hull
  2. `manage_asset.duplicate(sourcePath=<PBR_Metal>, destinationPath=<MAT_Ship_Accent_Carbon>)` → carbon composite accent
  3. `control_actor.set_component_property(actorName="GeneratedCylinder", componentName="DynamicMeshComponent", properties={material: "/Game/Chimera/Materials/MAT_Ship_Hull_Aluminum/MAT_Ship_Hull_Aluminum"})`
  4. Same for cockpit and thrusters with accent carbon material
- **Screenshot**: `control_editor.screenshot(filename="loop7_ship_exterior_v1.png", mode="editor_viewport")` → saves to `Saved/Screenshots/`
- **Result**: Full ship exterior with hull, cockpit, and twin thrusters, material-assigned
- **Parameters**: `hull={radius:150, height:600}`, `cockpit={radius:120, height:200}`, `thrusters={width:40, height:60, depth:40}`
- **Materials**: Hull = MAT_Ship_Hull_Aluminum (brushed, metallic 0.7, roughness 0.35, #A0A5A8), Accent = MAT_Ship_Accent_Carbon (composite, metallic 0.0, roughness 0.8, #2A2D30)
- **Notes**: Create material folders first via `manage_asset.create_folder(path="/Game/Chimera/...")` before `create_material`. Use existing PBR materials as duplication source for accent materials.

---

## Failed Pathways (1)

### manage_asset.list_instances
- **Tool**: `unreal_engine_manage_asset`
- **Action**: `list_instances`
- **Error**: "Action not previously tested"
- **Status**: Not yet verified as working or broken — needs testing with valid parameters.

---

## Graphify Pathways (Research Campus Queries)

### query_research_campus
- **Pathway**: `query_research_campus`
- **Steps**:
  1. `g.query('campus', school_name)`
  2. navigate to primary source
  3. extract reference data
  4. record discovery if new source found
- **Example**: `g.query("campus", "Game Development School")`
- **Result**: Returns trusted research sources and seed references for the specified school/campus from the Research Campuses directory.

---

## Automatic Pathway Recording Rule

### Before Every MCP Call:
1. Query Graphify: `g.query("pathway", "what_you_want_to_do")`
2. If pathway exists → follow it exactly
3. If pathway does NOT exist → test simplest approach, record result

### After Every MCP Call:
Record in DNA graph as a mutation node:
```json
{
  "type": "Mutation",
  "error_signature": "success_no_error" or "pathway_failed",
  "template_file": "Pathway_Name",
  "error_category": "none" or specific error type,
  "fix_description": "What was done and the result",
  "compilation_result": "pass" or "fail"
}
```

This ensures every successful MCP interaction becomes a pathway for future use. Every failure becomes a warning that prevents repeating the same mistake. The graph grows smarter with every call.

---

## How to Use This Document

1. **Find your task**: Search this document for the action you need (e.g., "spawn_actor", "create_material")
2. **Copy the parameters exactly**: Do not guess parameter names — use the schema shown above
3. **Execute via MCP**: Call the tool with the exact action and parameters
4. **Record the result**: After execution, add a mutation node to the DNA graph

If your task is NOT listed here:
1. Query Graphify first (as required by the contract)
2. If no pathway exists, test the simplest possible approach
3. If it works → add this pathway to this document and record in DNA graph
4. If it fails → note the error and try a different tool/action
