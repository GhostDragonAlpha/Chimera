# MCP Pathways Summary — Vector-Graphed Tools for Chimera Development

## Configuration
- **MCP Server**: `http://localhost:30010` (UE5 ModelContextProtocol plugin)
- **Always Use MCP**: `true` in `.pi/settings.json`
- **Fallback to Direct**: `false` — all development goes through MCP

---

## 1. Control Actor Tools (`unreal_engine_control_actor`)

| Action | Parameters | Status |
|--------|-----------|--------|
| `spawn_actor` | `{actorName, classPath}` | ✅ Verified |
| `set_transform` | `{actorName, location?, rotation?, scale?}` | ✅ Verified |
| `get_components` | `{actorName}` | ✅ Verified |
| `set_component_property` | `{actorName, componentName, properties}` | ✅ Verified |
| `set_material` | `{actorName, materialPath}` | ✅ Verified |
| `attach` | `{actorName, parentActor, socketName?}` | ✅ Verified |

---

## 2. Manage Asset Tools (`unreal_engine_manage_asset`)

| Action | Parameters | Status |
|--------|-----------|--------|
| `search_assets` | `{directory, classNames?, limit?}` | ✅ Verified |
| `create_material` | `{name, path}` | ✅ Verified |

---

## 3. Control Editor Tools (`unreal_engine_control_editor`)

| Action | Parameters | Status |
|--------|-----------|--------|
| `screenshot` | `{filename, mode?}` | ✅ Verified |
| `set_camera_position` | `{location, rotation}` | ✅ Verified |
| `console_command` | `{command}` (e.g., BugItGo) | ✅ Verified |

---

## 4. Inspect Tools (`unreal_engine_inspect`)

| Action | Parameters | Status |
|--------|-----------|--------|
| `get_project_settings` | `{}` | ✅ Verified |
| `get_material_details` | `{objectPath}` | ✅ Verified |

---

## 5. Manage Level Tools (`unreal_engine_manage_level`)

| Action | Parameters | Status |
|--------|-----------|--------|
| `list_levels` | `{}` | ✅ Verified |
| `create_light` | `{lightType, intensity, location}` | ✅ Verified |

---

## 6. Manage Geometry Tools (`unreal_engine_manage_geometry`)

| Action | Parameters | Status |
|--------|-----------|--------|
| `create_box` | `{width, height, depth}` | ✅ Verified |
| `create_cylinder` | `{radius, height, radialSegments?}` | ✅ Verified |

---

## 7. Animation/Physics Tools (`animation_physics`)

| Action | Parameters | Status |
|--------|-----------|--------|
| `add_anim_notify` | `{assetPath, notifyName, time}` | ✅ Verified |

---

## 8. Blueprint Tools (`manage_blueprint`)

| Action | Parameters | Status |
|--------|-----------|--------|
| `create_node` | `{nodeType, eventName?}` | ✅ Verified |

---

## 9. Research Tools (Playwright-based)

| Tool | Description | Status |
|------|-----------|--------|
| `web_browse` | Open URL and extract readable content | ✅ Verified |
| `web_search_real` | Search via Google/Bing browser automation | ✅ Verified |
| `web_extract` | Extract data using CSS selectors/XPath | ✅ Verified |
| `web_screenshot` | Take webpage screenshot (base64) | ✅ Verified |

---

## Usage Pattern

```typescript
// All development coding goes through MCP
const result = await mcpBridge.spawnActor("TestActor", "/Game/Characters/Astronaut/BP_Astronaut");
await mcpBridge.setTransform("TestActor", { location: { x: 0, y: 5, z: 130 } });

// Research uses Playwright directly
const searchResults = await web_search_real({ query: "UE5 C++ best practices" });
```

---

## Notes

- **MCP server must be running** (Unreal Editor with project loaded) before using MCP tools
- **Playwright browser** is managed automatically by the `web-browsing.ts` extension
- All pathways are vector-graphed in `.pi/extensions/mcp-pathways-index.ts` for reference
- Configuration: `.pi/settings.json -> mcp.serverUrl` and `.pi/settings.json -> research.playwright`
