/**
 * Visual Development Suite — Full Image Write + UE5 MCP Integration
 * 
 * For the visual game developer/artist:
 * - Capture UE5 viewport screenshots (read images)
 * - Create/save image files to disk (write images)
 * - Generate procedural art assets via MCP
 * - Material/lighting/geometry creation pipeline
 * - Visual verification loop with vision model feedback
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import * as fs from "fs";
import * as path from "path";

// ─── Minimal PNG Writers (no canvas dependency — pure Node.js) ──────

/** Create a minimal valid PNG file from raw pixel data */
function writePng(width: number, height: number, pixels: Uint8Array, outputPath: string): void {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

  function makeChunk(type: string, data: Buffer): Buffer {
    const len = Buffer.byteLength(data);
    const typeBuf = Buffer.from(type, 'ascii');
    const crcBuf = calcCrc(Buffer.concat([typeBuf, data]));
    return Buffer.concat([
      Buffer.from(len.toString(16).padStart(8, '0'), 'hex'),
      typeBuf,
      data,
      crcBuf
    ]);
  }

  function calcCrc(buf: Buffer): Buffer {
    const crc = pngCRC32(buf);
    return Buffer.from(crc.toString(16).padStart(8, '0'), 'hex');
  }

  function pngCRC32(buf: Buffer): number {
    let crc = 0xFFFFFFFF;
    for (let i = 0; i < buf.length; i++) {
      crc ^= buf[i];
      for (let j = 0; j < 8; j++) {
        crc = (crc >>> 1) ^ (0xEDB88320 & ((crc & 1) << 1));
      }
    }
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }

  const ihdrData = Buffer.alloc(13);
  ihdrData.writeUInt32BE(width, 0);
  ihdrData.writeUInt32BE(height, 4);
  ihdrData[8] = 8;
  ihdrData[9] = 6;
  ihdrData[10] = 0;
  ihdrData[11] = 0;
  ihdrData[12] = 0;

  const ihdrChunk = makeChunk('IHDR', ihdrData);

  let idatRaw = Buffer.alloc(height * (4 + 4 * width));
  for (let y = 0; y < height; y++) {
    const rowOffset = y * (1 + 4 * width);
    idatRaw[rowOffset] = 0;
    for (let x = 0; x < width; x++) {
      const pxOffset = rowOffset + 1 + x * 4;
      idatRaw[pxOffset] = pixels[y * width * 4 + x * 4];
      idatRaw[pxOffset + 1] = pixels[y * width * 4 + x * 4 + 1];
      idatRaw[pxOffset + 2] = pixels[y * width * 4 + x * 4 + 2];
      idatRaw[pxOffset + 3] = pixels[y * width * 4 + x * 4 + 3];
    }
  }

  const idatChunk = makeChunk('IDAT', idatRaw);
  const iendChunk = makeChunk('IEND', Buffer.alloc(0));

  fs.writeFileSync(outputPath, Buffer.concat([sig, ihdrChunk, idatChunk, iendChunk]));
}

/** Generate a solid color PNG image */
function createSolidColorImage(width: number, height: number, r: number, g: number, b: number, outputPath: string): void {
  const pixels = new Uint8Array(width * height * 4);
  for (let i = 0; i < width * height; i++) {
    pixels[i * 4] = Math.min(255, Math.max(0, r));
    pixels[i * 4 + 1] = Math.min(255, Math.max(0, g));
    pixels[i * 4 + 2] = Math.min(255, Math.max(0, b));
    pixels[i * 4 + 3] = 255;
  }
  writePng(width, height, pixels, outputPath);
}

/** Generate a gradient PNG image */
function createGradientImage(width: number, height: number, color1: {r:number,g:number,b:number}, color2: {r:number,g:number,b:number}, vertical: boolean, outputPath: string): void {
  const pixels = new Uint8Array(width * height * 4);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const t = vertical ? y / Math.max(1, height - 1) : x / Math.max(1, width - 1);
      const i = (y * width + x) * 4;
      pixels[i] = color1.r + (color2.r - color1.r) * t;
      pixels[i + 1] = color1.g + (color2.g - color1.g) * t;
      pixels[i + 2] = color1.b + (color2.b - color1.b) * t;
      pixels[i + 3] = 255;
    }
  }
  writePng(width, height, pixels, outputPath);
}

/** Generate a noise/texture PNG image */
function createNoiseTexture(width: number, height: number, intensity: number, outputPath: string): void {
  const pixels = new Uint8Array(width * height * 4);
  for (let i = 0; i < width * height; i++) {
    const noise = Math.random() * intensity;
    pixels[i * 4] = noise;
    pixels[i * 4 + 1] = noise;
    pixels[i * 4 + 2] = noise;
    pixels[i * 4 + 3] = 255;
  }
  writePng(width, height, pixels, outputPath);
}

/** Generate procedural art PNG image */
function createProceduralArt(width: number, height: number, seed: number, outputPath: string): void {
  const pixels = new Uint8Array(width * height * 4);
  let s = seed;
  function seededRandom() {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  }

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const i = (y * width + x) * 4;
      const dist = Math.sqrt((x - width/2)**2 + (y - height/2)**2) / Math.max(width, height);
      pixels[i] = seededRandom() * 100 * (1 - dist);
      pixels[i + 1] = seededRandom() * 80 * (1 - dist);
      pixels[i + 2] = seededRandom() * 60 * (1 - dist);
      pixels[i + 3] = 255;
    }
  }

  for (let i = 0; i < 50; i++) {
    const cx = Math.floor(seededRandom() * width);
    const cy = Math.floor(seededRandom() * height);
    const size = Math.floor(seededRandom() * 100 + 20);
    const hue = seededRandom() * 360;
    const r = Math.floor(hue / 3.6);
    const g = Math.floor((120 - hue / 3.6) % 256);
    const b = Math.floor(seededRandom() * 256);

    for (let dy = -size; dy <= size; dy++) {
      for (let dx = -size; dx <= size; dx++) {
        if (dx*dx + dy*dy <= size*size) {
          const px = cx + dx;
          const py = cy + dy;
          if (px >= 0 && px < width && py >= 0 && py < height) {
            const pi = (py * width + px) * 4;
            pixels[pi] = Math.min(255, pixels[pi] + r);
            pixels[pi+1] = Math.min(255, pixels[pi+1] + g);
            pixels[pi+2] = Math.min(255, pixels[pi+2] + b);
          }
        }
      }
    }
  }

  writePng(width, height, pixels, outputPath);
}

// ─── UE5 MCP Server Client (JSON-RPC 2.0 over HTTP) ────────────────

class VisualMcpClient {
  private baseUrl: string;
  private sessionId: string | null = null;
  private nextId: number = 1;

  constructor(serverUrl: string = "http://localhost:8091/mcp") {
    this.baseUrl = serverUrl;
  }

  /** Initialize session and get session ID */
  async initSession(): Promise<boolean> {
    try {
      const response = await fetch(this.baseUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: 1,
          method: "initialize",
          params: {
            protocolVersion: "2024-11-07",
            capabilities: {},
            clientInfo: { name: "ChimeraClient", version: "1.0" }
          }
        }),
        signal: AbortSignal.timeout(30000)
      });

      if (!response.ok) return false;
      const data = await response.json();

      // Session ID is in the response headers (Mcp-Session-Id)
      this.sessionId = response.headers.get("Mcp-Session-Id");
      console.log(`[Visual MCP] Session initialized: ${this.sessionId}`);
      return true;
    } catch (error) {
      console.error(`[Visual MCP] Session init failed:`, error);
      return false;
    }
  }

  /** Call any MCP tool/action on the UE5 ModelContextProtocol server */
  async call(tool: string, action: string, args: Record<string, any> = {}): Promise<any> {
    if (!this.sessionId) await this.initSession();

    try {
      const response = await fetch(this.baseUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Mcp-Session-Id": this.sessionId || ""
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: this.nextId++,
          method: "tools/call",
          params: { name: tool, arguments: { action, ...args } }
        }),
        signal: AbortSignal.timeout(60000)
      });

      if (!response.ok) throw new Error(`MCP failed: ${response.status}`);

      // SSE response: "event: message\ndata: {...}"
      const text = await response.text();
      const dataMatch = text.match(/data:\s*(.+)$/m);
      if (!dataMatch) return null;

      const jsonStr = dataMatch[1];
      let parsed: any;
      try {
        parsed = JSON.parse(jsonStr);
      } catch (e) {
        console.error(`[Visual MCP] Parse error: ${jsonStr.substring(0, 200)}`);
        return null;
      }

      if (parsed.result?.structuredContent) {
        return parsed.result.structuredContent;
      }
      if (parsed.result?.content?.[0]?.text) {
        try {
          const textData = JSON.parse(parsed.result.content[0].text);
          return textData;
        } catch {
          return { text: parsed.result.content[0].text };
        }
      }
      return parsed.result || null;
    } catch (error) {
      console.error(`[Visual MCP] Call to ${tool}.${action} failed:`, error);
      return null;
    }
  }

  // ─── Screenshot Capture ──────────────────────────────────────────
  async captureViewport(filename: string = "viewport.png", mode: "editor_viewport" | "game_viewport" = "editor_viewport"): Promise<any> {
    const result = await this.call("control_editor", "screenshot", { filename, mode });
    if (result) {
      console.log(`[Visual MCP] Screenshot saved: ${filename} (${result.width}x${result.height}, ${result.sizeBytes} bytes)`);
    }
    return result;
  }

  // ─── Actor Management ────────────────────────────────────────────
  async spawnActor(name: string, classPath: string): Promise<any> {
    const result = await this.call("control_actor", "spawn_actor", { actorName: name, classPath });
    return result;
  }

  async setTransform(actorName: string, location?: {x:number,y:number,z:number}, rotation?: {pitch:number,yaw:number,roll:number}): Promise<any> {
    const args: any = { actorName };
    if (location) args.location = location;
    if (rotation) args.rotation = rotation;
    return this.call("control_actor", "set_transform", args);
  }

  async destroyActor(actorName: string): Promise<any> {
    return this.call("control_actor", "destroy_actor", { actorName });
  }

  // ─── Level Management ────────────────────────────────────────────
  async listLevels(): Promise<any> {
    return this.call("manage_level", "list_levels");
  }

  // ─── Asset Management ────────────────────────────────────────────
  async searchAssets(directory: string = "/Game/", classNames?: string[], limit: number = 10): Promise<any> {
    const args: any = { directory, limit };
    if (classNames) args.classNames = classNames;
    return this.call("manage_asset", "search_assets", args);
  }

  // ─── Inspect ──────────────────────────────────────────────────────
  async getProjectSettings(): Promise<any> {
    return this.call("inspect", "get_project_settings");
  }
}

// ─── Pi Tool Registration ───────────────────────────────────────────

export default function (api: ExtensionAPI): void {
  const mcp = new VisualMcpClient("http://localhost:8091/mcp");

  // Expose globally for other extensions/tools
  (globalThis as any).__VISUAL_DEV__ = {
    mcp,
    createSolidColorImage,
    createGradientImage,
    createNoiseTexture,
    createProceduralArt
  };

  const chimeraRoot = process.env.CHIMERA_ROOT || "E:/PythonChimera/Chimera";
  const imagesDir = path.join(chimeraRoot, "Saved", "Images");
  fs.mkdirSync(imagesDir, { recursive: true });

  // ─── Image Writing Tools ────────────────────────────────────────

  api.registerTool({
    name: "write_solid_color_image",
    label: "Write Solid Color Image",
    description: "Generate a solid color PNG image and save to disk. Useful for testing materials, creating placeholder assets.",
    parameters: Type.Object({
      width: Type.Number({ default: 1024 }),
      height: Type.Number({ default: 1024 }),
      r: Type.Number({ default: 128 }),
      g: Type.Number({ default: 128 }),
      b: Type.Number({ default: 128 }),
      outputPath: Type.Optional(Type.String())
    }),
    async execute(_toolCallId, params) {
      const outputDir = params.outputPath ? path.dirname(params.outputPath) : imagesDir;
      const filename = params.outputPath ? path.basename(params.outputPath) : `solid_${params.r}_${params.g}_${params.b}_${Date.now()}.png`;
      const outputPath = path.join(outputDir, filename);

      fs.mkdirSync(outputDir, { recursive: true });
      createSolidColorImage(params.width, params.height, params.r, params.g, params.b, outputPath);

      return {
        content: [{ type: "text", text: `✅ Solid color image saved to ${outputPath} (${params.width}x${params.height})` }],
        details: { status: "success", path: outputPath, size: fs.statSync(outputPath).size },
        image: outputPath
      };
    }
  });

  api.registerTool({
    name: "write_gradient_image",
    label: "Write Gradient Image",
    description: "Generate a gradient PNG image and save to disk. Useful for testing lighting transitions, skyboxes.",
    parameters: Type.Object({
      width: Type.Number({ default: 1024 }),
      height: Type.Number({ default: 1024 }),
      color1R: Type.Number({ default: 0 }),
      color1G: Type.Number({ default: 0 }),
      color1B: Type.Number({ default: 139 }),
      color2R: Type.Number({ default: 255 }),
      color2G: Type.Number({ default: 69 }),
      color2B: Type.Number({ default: 69 }),
      vertical: Type.Boolean({ default: true }),
      outputPath: Type.Optional(Type.String())
    }),
    async execute(_toolCallId, params) {
      const outputDir = params.outputPath ? path.dirname(params.outputPath) : imagesDir;
      const filename = params.outputPath ? path.basename(params.outputPath) : `gradient_${Date.now()}.png`;
      const outputPath = path.join(outputDir, filename);

      fs.mkdirSync(outputDir, { recursive: true });
      createGradientImage(
        params.width, params.height,
        { r: params.color1R, g: params.color1G, b: params.color1B },
        { r: params.color2R, g: params.color2G, b: params.color2B },
        params.vertical,
        outputPath
      );

      return {
        content: [{ type: "text", text: `✅ Gradient image saved to ${outputPath} (${params.width}x${params.height})` }],
        details: { status: "success", path: outputPath, size: fs.statSync(outputPath).size },
        image: outputPath
      };
    }
  });

  api.registerTool({
    name: "write_noise_texture",
    label: "Write Noise Texture",
    description: "Generate a noise/texture PNG image and save to disk. Useful for testing material roughness, normal maps.",
    parameters: Type.Object({
      width: Type.Number({ default: 1024 }),
      height: Type.Number({ default: 1024 }),
      intensity: Type.Number({ default: 80 }),
      outputPath: Type.Optional(Type.String())
    }),
    async execute(_toolCallId, params) {
      const outputDir = params.outputPath ? path.dirname(params.outputPath) : imagesDir;
      const filename = params.outputPath ? path.basename(params.outputPath) : `noise_${params.intensity}_${Date.now()}.png`;
      const outputPath = path.join(outputDir, filename);

      fs.mkdirSync(outputDir, { recursive: true });
      createNoiseTexture(params.width, params.height, params.intensity, outputPath);

      return {
        content: [{ type: "text", text: `✅ Noise texture saved to ${outputPath} (${params.width}x${params.height}, intensity=${params.intensity})` }],
        details: { status: "success", path: outputPath, size: fs.statSync(outputPath).size },
        image: outputPath
      };
    }
  });

  api.registerTool({
    name: "write_procedural_art",
    label: "Write Procedural Art",
    description: "Generate procedural art PNG image and save to disk. Useful for inspiration, testing visual pipelines.",
    parameters: Type.Object({
      width: Type.Number({ default: 1024 }),
      height: Type.Number({ default: 1024 }),
      seed: Type.Number({ default: 42 }),
      outputPath: Type.Optional(Type.String())
    }),
    async execute(_toolCallId, params) {
      const outputDir = params.outputPath ? path.dirname(params.outputPath) : imagesDir;
      const filename = params.outputPath ? path.basename(params.outputPath) : `art_seed${params.seed}_${Date.now()}.png`;
      const outputPath = path.join(outputDir, filename);

      fs.mkdirSync(outputDir, { recursive: true });
      createProceduralArt(params.width, params.height, params.seed, outputPath);

      return {
        content: [{ type: "text", text: `✅ Procedural art saved to ${outputPath} (${params.width}x${params.height}, seed=${params.seed})` }],
        details: { status: "success", path: outputPath, size: fs.statSync(outputPath).size },
        image: outputPath
      };
    }
  });

  // ─── UE5 Visual Pipeline Tools (MCP Integration) ────────────────

  api.registerTool({
    name: "mcp_capture_viewport",
    label: "Capture UE5 Viewport",
    description: "Capture screenshot from Unreal Editor viewport. Returns image data for vision analysis.",
    parameters: Type.Object({
      filename: Type.Optional(Type.String()),
      mode: Type.Union([Type.Literal("editor_viewport"), Type.Literal("game_viewport")], { default: "editor_viewport" })
    }),
    async execute(_toolCallId, params) {
      const result = await mcp.captureViewport(params.filename || `viewport_${Date.now()}.png`, params.mode);

      if (result && result.path) {
        return {
          content: [{ type: "text", text: `✅ Viewport captured: ${result.path} (${result.width}x${result.height})` }],
          details: { status: "success", path: result.path, width: result.width, height: result.height },
          image: result.path
        };
      }
      return { content: [{ type: "text", text: `❌ Viewport capture failed` }], details: { status: "error" }, isError: true };
    }
  });

  api.registerTool({
    name: "mcp_spawn_actor",
    label: "Spawn Actor in UE5",
    description: "Spawn an actor (character, prop, etc.) at a location. Use Blueprint paths.",
    parameters: Type.Object({
      name: Type.String(),
      classPath: Type.String(),
      x: Type.Optional(Type.Number()),
      y: Type.Optional(Type.Number()),
      z: Type.Optional(Type.Number())
    }),
    async execute(_toolCallId, params) {
      const result = await mcp.spawnActor(params.name, params.classPath);

      if (result && result.actorName) {
        if (params.x !== undefined || params.y !== undefined || params.z !== undefined) {
          await mcp.setTransform(result.actorName, { x: params.x || 0, y: params.y || 0, z: params.z || 0 });
        }

        return {
          content: [{ type: "text", text: `✅ Actor spawned: ${result.actorName}` }],
          details: { status: "success", name: result.actorName, path: result.path },
          image: undefined
        };
      }
      return { content: [{ type: "text", text: `❌ Actor spawn failed` }], details: { status: "error" }, isError: true };
    }
  });

  api.registerTool({
    name: "mcp_set_camera",
    label: "Set Camera Position in UE5",
    description: "Position the editor viewport camera. Use BugItGo for reliable positioning.",
    parameters: Type.Object({
      x: Type.Number({ default: 0 }),
      y: Type.Number({ default: -250 }),
      z: Type.Number({ default: 130 }),
      pitch: Type.Number({ default: 0 }),
      yaw: Type.Number({ default: 0 }),
      roll: Type.Number({ default: 0 })
    }),
    async execute(_toolCallId, params) {
      const result = await mcp.call("control_editor", "console_command", {
        command: `BugItGo ${params.x} ${params.y} ${params.z} ${params.pitch} ${params.yaw} ${params.roll}`
      });

      if (result && result.success !== false) {
        return {
          content: [{ type: "text", text: `✅ Camera positioned at (${params.x}, ${params.y}, ${params.z})` }],
          details: { status: "success", location: { x: params.x, y: params.y, z: params.z }, rotation: { pitch: params.pitch, yaw: params.yaw, roll: params.roll } },
          image: undefined
        };
      }
      return { content: [{ type: "text", text: `❌ Camera positioning failed` }], details: { status: "error" }, isError: true };
    }
  });

  api.registerTool({
    name: "visual_dev_workflow_capture_and_analyze",
    label: "Capture & Analyze Viewport (Vision Loop)",
    description: "Capture UE5 viewport, then analyze with vision model. Returns image for visual feedback.",
    parameters: Type.Object({
      mode: Type.Union([Type.Literal("editor_viewport"), Type.Literal("game_viewport")], { default: "editor_viewport" })
    }),
    async execute(_toolCallId, params) {
      const filename = `visual_loop_${Date.now()}.png`;
      const result = await mcp.captureViewport(filename, params.mode);

      if (result && result.path) {
        return {
          content: [{ type: "text", text: `✅ Viewport captured for vision analysis: ${result.path}` }],
          details: { status: "success", path: result.path },
          image: result.path
        };
      }
      return { content: [{ type: "text", text: `❌ Capture failed` }], details: { status: "error" }, isError: true };
    }
  });

  console.log("[Visual Dev] Registered with Pi. All visual tools ready.");
}
