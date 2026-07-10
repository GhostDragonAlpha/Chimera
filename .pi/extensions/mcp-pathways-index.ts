/**
 * MCP Pathways Index — Vector-Graphed UE5 ModelContextProtocol Tools
 *
 * This file documents all proven MCP pathways for the Chimera project.
 * All development coding, level editing, and asset management goes through these tools.
 *
 * Configuration: .pi/settings.json -> mcp.serverUrl (default: http://localhost:30010)
 *
 * `params` values are signature *descriptions* (data, not TypeScript types) — this is a
 * runtime object literal, so `?:` and bare type names are not valid here.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

/**
 * All vector-graphed MCP pathways for UE5 development.
 * Each pathway is a proven sequence of tool calls that has been tested and documented.
 */
export const MCP_PATHWAYS = {
  // ─── Control Actor Tools (Actor manipulation) ──────────────────────
  control_actor: {
    spawn_actor: {
      tool: "unreal_engine_control_actor",
      action: "spawn_actor",
      params: "actorName: string, classPath: string",
      example: 'spawn_actor(actorName="TestActor", classPath="/Game/VehicleTemplate/Meshes/SM_Track_10M.SM_Track_10M")',
      status: "verified"
    },
    set_transform: {
      tool: "unreal_engine_control_actor",
      action: "set_transform",
      params: "actorName: string, location?: {x,y,z}, rotation?: {pitch,yaw,roll}, scale?: {x,y,z}",
      example: 'set_transform(actorName="Player", location={x:0,y:5,z:130})',
      status: "verified"
    },
    get_components: {
      tool: "unreal_engine_control_actor",
      action: "get_components",
      params: "actorName: string",
      example: 'get_components(actorName="PlayerTestPlaceholder")',
      status: "verified"
    },
    set_component_property: {
      tool: "unreal_engine_control_actor",
      action: "set_component_property",
      params: "actorName: string, componentName: string, properties: Record<string, unknown>",
      example: 'set_component_property(actorName="GroundPlane", componentName="StaticMeshComponent0", properties={material:"/Game/Chimera/Materials/MAT_GroundSand"})',
      status: "verified"
    },
    set_material: {
      tool: "unreal_engine_control_actor",
      action: "set_material",
      params: "actorName: string, componentName?: string, materialPath: string, materialSlot?: number",
      example: 'set_material(actorName="GeneratedCylinder", materialPath="/Game/Chimera/Materials/MAT_Ship_Hull_Aluminum")',
      status: "verified"
    },
    attach: {
      tool: "unreal_engine_control_actor",
      action: "attach",
      params: "actorName: string, parentActor: string, socketName?: string",
      example: 'attach(actorName="ThrusterLeft", parentActor="ShipHull")',
      status: "verified"
    }
  },

  // ─── Manage Asset Tools (Material/Asset creation) ──────────────────
  manage_asset: {
    search_assets: {
      tool: "unreal_engine_manage_asset",
      action: "search_assets",
      params: "directory: string, classNames?: string[], limit?: number",
      example: 'search_assets(directory="/Game/", classNames=["StaticMesh"], limit=1)',
      status: "verified"
    },
    create_material: {
      tool: "unreal_engine_manage_asset",
      action: "create_material",
      params: "name: string, path: string",
      example: 'create_material(name="MAT_GroundSand", path="/Game/Chimera/Materials/MAT_GroundSand")',
      status: "verified"
    }
  },

  // ─── Control Editor Tools (Viewport/Camera/Screenshot) ─────────────
  control_editor: {
    screenshot: {
      tool: "unreal_engine_control_editor",
      action: "screenshot",
      params: 'filename: string, mode?: "editor_viewport" | "game_viewport"',
      example: 'screenshot(filename="phase2_refinement_v1.png")',
      status: "verified"
    },
    set_camera_position: {
      tool: "unreal_engine_control_editor",
      action: "set_camera_position",
      params: "location: {x,y,z}, rotation: {pitch,yaw,roll}",
      example: 'set_camera_position(location={x:0,y:-250,z:130}, rotation={pitch:0,yaw:0,roll:0})',
      status: "verified"
    },
    console_command: {
      tool: "unreal_engine_control_editor",
      action: "console_command",
      params: "command: string",
      example: 'console_command(command="BugItGo 0 -250 130 0 0 0")',
      status: "verified"
    }
  },

  // ─── Inspect Tools (Project/Actor/Material info) ────────────────────
  inspect: {
    get_project_settings: {
      tool: "unreal_engine_inspect",
      action: "get_project_settings",
      params: "",
      example: 'get_project_settings()',
      status: "verified"
    },
    get_material_details: {
      tool: "unreal_engine_inspect",
      action: "get_material_details",
      params: "objectPath: string",
      example: 'get_material_details(objectPath="/Game/Chimera/Materials/MAT_GroundSand")',
      status: "verified"
    }
  },

  // ─── Manage Level Tools (Level/Light management) ──────────────────
  manage_level: {
    list_levels: {
      tool: "unreal_engine_manage_level",
      action: "list_levels",
      params: "",
      example: 'list_levels()',
      status: "verified"
    },
    create_light: {
      tool: "unreal_engine_manage_level",
      action: "create_light",
      params: "lightType: string, intensity: number, location: {x,y,z}",
      example: 'create_light(lightType="Directional", intensity=100.0, location={x:0,y:0,z:0})',
      status: "verified"
    }
  },

  // ─── Manage Geometry Tools (Procedural geometry creation) ──────────
  manage_geometry: {
    create_box: {
      tool: "unreal_engine_manage_geometry",
      action: "create_box",
      params: "width: number, height: number, depth: number",
      example: 'create_box(width=100, height=50, depth=200)',
      status: "verified"
    },
    create_cylinder: {
      tool: "unreal_engine_manage_geometry",
      action: "create_cylinder",
      params: "radius: number, height: number, radialSegments?: number",
      example: 'create_cylinder(radius=150, height=600, radialSegments=32)',
      status: "verified"
    }
  },

  // ─── Animation/Physics Tools ──────────────────────────────────────
  animation_physics: {
    add_anim_notify: {
      tool: "animation_physics",
      action: "add_anim_notify",
      params: "assetPath: string, notifyName: string, time: number",
      example: 'add_anim_notify(assetPath="/Game/Characters/Mannequins/Anims/Walk/MF_Walk", notifyName="FootPlant", time=0.3)',
      status: "verified"
    }
  },

  // ─── Blueprint Tools ──────────────────────────────────────────────
  manage_blueprint: {
    create_node: {
      tool: "manage_blueprint",
      action: "create_node",
      params: "nodeType: string, eventName?: string",
      example: 'create_node(nodeType="CustomEvent", eventName="AnimNotify_FootPlant")',
      status: "verified"
    }
  }
} as const;

/**
 * Research tools (Playwright-based web browsing)
 */
export const RESEARCH_TOOLS = {
  web_browse: {
    description: "Open a URL in Chromium and extract readable content",
    params: "url: string, maxChars?: number",
    status: "verified"
  },
  web_search_real: {
    description: "Search the web using actual browser navigation to Google/Bing",
    params: "query: string, maxResults?: number",
    status: "verified"
  },
  web_extract: {
    description: "Extract specific data from a page using CSS selectors or XPath",
    params: "url: string, selector: string, field?: string",
    status: "verified"
  },
  web_screenshot: {
    description: "Take a screenshot of a webpage. Returns base64 image data.",
    params: "url: string, fullPage?: boolean",
    status: "verified"
  }
} as const;

/**
 * Register MCP pathways with Pi's extension system
 */
export default function (pi: ExtensionAPI): void {
  // Expose MCP pathways as a global utility for other extensions/tools
  (globalThis as any).__MCP_PATHWAYS__ = MCP_PATHWAYS;
  (globalThis as any).__RESEARCH_TOOLS__ = RESEARCH_TOOLS;

  console.log("[MCP Pathways] Registered with Pi. Available tools:", Object.keys(MCP_PATHWAYS).join(", "));
}
