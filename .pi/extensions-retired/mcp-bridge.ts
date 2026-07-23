/**
 * UE5 MCP Bridge Extension for Pi Coding Agent
 * 
 * Provides direct access to Unreal Engine's ModelContextProtocol plugin tools.
 * All development coding, level editing, and asset management goes through MCP.
 * 
 * Configuration: .pi/settings.json -> mcp.serverUrl (default: http://localhost:8091)
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const DEFAULT_MCP_URL = "http://localhost:8091";
const MCP_TIMEOUT_MS = 30000; // 30s timeout for MCP calls

class McpBridgeClient {
  private baseUrl: string;
  
  constructor(baseUrl: string = DEFAULT_MCP_URL) {
    this.baseUrl = baseUrl;
  }
  
  async call(tool: string, action: string, params: Record<string, any> = {}): Promise<any> {
    const url = `${this.baseUrl}/mcp`;
    const payload = JSON.stringify({ tool, action, ...params });
    
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        signal: AbortSignal.timeout(MCP_TIMEOUT_MS)
      });
      
      if (!response.ok) {
        throw new Error(`MCP call failed: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      return result;
    } catch (error) {
      console.error(`[MCP Bridge] Call to ${tool}.${action} failed:`, error);
      throw error;
    }
  }
  
  // Control Actor tools
  async spawnActor(actorName: string, classPath: string): Promise<any> {
    return this.call("unreal_engine_control_actor", "spawn_actor", { actorName, classPath });
  }
  
  async setTransform(actorName: string, transform?: any): Promise<any> {
    return this.call("unreal_engine_control_actor", "set_transform", { actorName, ...transform });
  }
  
  async getComponents(actorName: string): Promise<any> {
    return this.call("unreal_engine_control_actor", "get_components", { actorName });
  }
  
  async setComponentProperty(actorName: string, componentName: string, properties: any): Promise<any> {
    return this.call("unreal_engine_control_actor", "set_component_property", { 
      actorName, componentName, properties 
    });
  }
  
  async getActorDetails(actorName: string): Promise<any> {
    return this.call("inspect", "get_actor_details", { actorName });
  }
  
  // Manage Asset tools
  async searchAssets(directory: string, options?: any): Promise<any> {
    return this.call("unreal_engine_manage_asset", "search_assets", { 
      directory, ...options 
    });
  }
  
  async createMaterial(name: string, path: string): Promise<any> {
    return this.call("unreal_engine_manage_asset", "create_material", { name, path });
  }
  
  // Control Editor tools
  async screenshot(filename: string, mode?: string): Promise<any> {
    const params: any = { filename };
    if (mode) params.mode = mode;
    return this.call("unreal_engine_control_editor", "screenshot", params);
  }
  
  async setCameraPosition(location: any, rotation: any): Promise<any> {
    return this.call("unreal_engine_control_editor", "set_camera_position", { 
      location, rotation 
    });
  }
  
  async consoleCommand(command: string): Promise<any> {
    return this.call("unreal_engine_control_editor", "console_command", { command });
  }
  
  // Manage Level tools
  async listLevels(): Promise<any> {
    return this.call("unreal_engine_manage_level", "list_levels", {});
  }
  
  async createLight(lightType: string, intensity: number, location: any): Promise<any> {
    return this.call("unreal_engine_manage_level", "create_light", { 
      lightType, intensity, location 
    });
  }
  
  // Manage Geometry tools
  async createBox(width: number, height: number, depth: number): Promise<any> {
    return this.call("unreal_engine_manage_geometry", "create_box", { width, height, depth });
  }
  
  async createCylinder(radius: number, height: number, radialSegments?: number): Promise<any> {
    return this.call("unreal_engine_manage_geometry", "create_cylinder", { 
      radius, height, radialSegments 
    });
  }
}

export const mcpBridge = new McpBridgeClient();

// Register MCP tools with Pi's extension system
export default function (pi: ExtensionAPI): void {
  // Expose MCP bridge as a global utility for other extensions/tools
  (globalThis as any).__MCP_BRIDGE__ = mcpBridge;

  console.log("[MCP Bridge] Registered with Pi. Ready to use UE5 ModelContextProtocol tools.");
}
