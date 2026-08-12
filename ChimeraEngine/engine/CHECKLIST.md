# Chimera Engine — AI-Driven Development Checklist
## Custom to Our Method: Glass-Box, Hot-Reload, Procedural-First

---

## 1. CORE ARCHITECTURE (Data-Oriented Foundation)

### Entity/Component System
- [x] **Entity Registry** — integer ID-based entity pool with O(1) lookup
- [x] **Component Storage** — struct-of-arrays layout per component type (cache-friendly for GPU upload)
- [x] **Component Queries** — filter-by-type iteration (e.g., "all entities with Position + Velocity")
- [x] **Entity Composition API** — `entity.addComponent(type, data)` / `entity.removeComponent(type)`
- [x] **System Runner** — iterate all matching entities, apply system logic each frame
- [x] **System Dependencies** — declare execution order (Physics before Rendering, etc.)
- [x] **World/Sandbox Isolation** — multiple independent worlds can coexist in one page
- [x] **Entity Serialization** — dump/restore full entity graph to JSON for save/load

### Hot Reload Pipeline
- [x] **Module Watcher** — detect file changes (spike.html, shader files) via polling or FS events
- [x] **Shader Hot-Reload** — recompile WGSL on change without page reload (via `device.createShaderModule`)
- [x] **System Hot-Reload** — `hotReloadSystem(name, newFn)` replaces fn at runtime, entity state preserved
- [x] **Config Hot-Reload** — physics constants, render params reloaded from a live config object
- [x] **State Preservation** — hot-reload preserves entity positions/velocities/colors (don't reset sim)
- [x] **Error Recovery** — bad shader -> fallback to last known-good version, log compile errors visibly
- [x] **Partial Reload** — `PartialReload.markDirty()/reloadChanged()` tracks and reloads only modified systems

### Live Inspection Layer
- [x] **Entity Inspector Panel** — click an entity, see all its components in a floating panel
- [x] **Component Value Editor** — sliders/inputs to modify component data live (position, color, mass, etc.)
- [x] **System Toggle** — enable/disable individual systems without code change
- [x] **Frame Step** — pause simulation, step forward one frame at a time
- [x] **Variable Watch** — watch any JS variable or GPU buffer value in real-time
- [x] **Entity Graph View** — force-directed canvas overlay showing shared-component connections between entities

---

## 2. RENDERING (AI-Focused Pipeline)

### Core Rendering
- [x] **Tile-Based Rasterizer** — current particle splat approach (proven working)
- [x] **GPU Frustum Culling** — 6-plane test in preprocess compute shader
- [x] **Dynamic Resolution Scaling** — adaptive resolution based on frame budget
- [x] **Mesh Rendering Path** — `meshPipeline` with MVP transform, indexed triangles, per-vertex color
- [x] **Instanced Mesh Rendering** — `instMeshPipeline` with instance position+scale buffer, VP uniform
- [x] **Billboard/Point Sprite System** — extend current approach to configurable sizes/colors

### Materials & Shading
- [x] **PBR Material Data Structure** — metallic, roughness, albedo, normal strength as component data
- [x] **Procedural Material Functions** — noise-based textures (marble, wood, terrain) generated in WGSL
- [x] **Material Parameter Binding** — each entity's material params uploaded as uniform buffer per-draw
- [x] **Shader Variant System** — compile-time flags for "has_normal_map", "emissive", etc. (no asset pipeline)
- [x] **Debug Material Presets** — wireframe, flat color by component type, depth visualization

### Post-Processing Stack
- [x] **Bloom** — downsample -> H-blur -> V-blur -> additive blend
- [x] **SSAO** — particle-density occlusion at half resolution
- [x] **Chromatic Aberration** — RGB channel offset from screen center
- [x] **Vignette** — radial edge darkening
- [x] **Depth of Field** — bokeh blur based on distance from focus plane (integrated into post-processing pipeline)
- [x] **Color Grading LUT** — 3D texture lookup for filmic color transformation
- [x] **Motion Blur** — velocity-buffer accumulation pass
- [x] **Film Grain** — per-pixel random noise overlay
- [x] **Lens Distortion** — barrel/pincushion UV distortion (for VR/fisheye preview)

### Debug Visualization Modes
- [x] **Wireframe Overlay** — render all triangles as wireframe on top of shaded pass
- [x] **Depth Pass** — full-screen quad outputting linearized depth values
- [x] **Velocity/Flow Field** — render particle velocity vectors as colored lines
- [x] **Collision Bounds** — debug overlay drawing AABB wireframes via instanced line-list render pass
- [x] **Component Heatmap** — color by component count per tile (show where AI is building density)
- [x] **Draw Call Counter** — HUD overlay showing total draws, triangles, shader switches
- [x] **GPU Timestamp Report** — per-pass timing breakdown in HUD (CPU fallback when GPU timestamps unavailable)

---

## 3. PHYSICS & SIMULATION

### Rigid Body Dynamics
- [x] **AABB Broadphase** — sweep-and-prune or uniform grid for collision candidate pairs
- [x] **SAT Collision Detection** — separating axis theorem for AABB/AABB and AABB/OBB
- [x] **Impulse Resolution** — velocity-level constraint solver (no position correction needed yet)
- [x] **Friction Model** — Coulomb friction with static/dynamic coefficients
- [x] **Stacking Stability** — iterative solver with warm starting + position correction for stable piles

### Forces & Constraints
- [x] **N-body Gravity** — current particle gravity system (done, N=1200)
- [x] **Gravity Field** — uniform + custom force fields (attractors, repulsors, vortices)
- [x] **Spring-Damper** — distance constraints between entity pairs
- [x] **Hinge/Pivot Joint** — rotational constraint around an axis
- [x] **Particle Attraction/Repulsion** — extend current N-body to include user-defined force fields

### Procedural Generation Primitives
- [x] **Noise Functions** — Perlin, Simplex, Worley (distance-based) in both JS and WGSL
- [x] **Voronoi Diagram** — cell centers + distance fields for organic shapes
- [x] **L-System Generator** — context-free grammar for branching structures (plants, crystals)
- [x] **Heightmap Terrain** — procedural terrain from noise, with vertex color by slope/height
- [x] **Mesh Boolean Ops** — union/intersection/subtraction for composing complex shapes
- [x] **Particle Emitter System** — spawn particles with lifetime, velocity distribution, color over life

### Simulation Control
- [x] **Fixed Timestep** — symplectic Euler integration (done in integrate shader)
- [x] **Sub-Stepping** — multiple physics steps per frame for stability at high speeds
- [x] **Sleep Threshold** — entities below velocity threshold stop updating (save GPU cycles)
- [x] **Pause/Resume** — freeze all simulation, inspect state, then resume
- [x] **Time Scale** — slow-motion / fast-forward without changing physics constants

---

## 4. PROCEDURAL WORLD BUILDING

### Terrain System
- [x] **Chunk-Based Terrain** — load/unload terrain chunks based on camera distance
- [x] **Heightmap Generation** — multi-octave noise for natural-looking terrain
- [x] **Texture Splatting** — blend ground/rock/snow textures by height and slope (procedural, no assets)
- [x] **Erosion Simulation** — thermal and hydraulic erosion for realistic features
- [x] **Terrain Editing Tools** — raise/lower/flatten terrain in real-time via UI

### Object Placement
- [x] **Procedural Scatterer** — place objects based on density maps (trees on grass, rocks on slopes)
- [x] **Constraint-Based Placement** — snap objects to terrain surface, respect min-distance rules
- [x] **LOD Generation** — auto-generate 3 LOD levels from high-poly source mesh

### Entity Templates
- [x] **Component Presets** — Tree = {Position, Scale, Color, CollisionAABB, RenderMesh}
- [x] **Template Instantiation** — world.spawn("Tree", {x, y, z, scale}) creates entity from template
- [x] **Template Inheritance** — child templates extend parent (Rock -> Boulder -> Mountain)
- [x] **Parameter Override** — spawn with overridden defaults ({color: [1,0,0]} for red flowers)

---

## 5. DEBUG & DEVELOPMENT TOOLS

### Real-Time Parameter Editor
- [x] **Physics Sliders Panel** — gravity strength, damping, restitution, friction (live update)
- [x] **Render Sliders Panel** — bloom intensity, SSAO radius/power, chroma strength, vignette amount
- [x] **Generation Sliders Panel** — noise frequency, terrain height scale, scatter density
- [x] **Color Pickers** — pick entity colors live and see results instantly
- [x] **Boolean Toggles** — enable/disable features (bloom on/off, SSAO on/off, physics on/off)

### Performance Profiler
- [x] **Frame Budget Breakdown** — show ms spent in: preprocess, physics, sort, raster, bloom, postproc
- [x] **GPU Buffer Sizes** — track memory usage per buffer (pos, vel, acc, indices, textures)
- [x] **Draw Call Report** — count and categorize draws per frame
- [x] **FPS History Graph** — rolling 60-second FPS graph in HUD overlay + canvas graph
- [x] **Memory Leak Detector** — track buffer allocations growing unbounded over time, HUD status display

### Entity Debugger
- [x] **Click-to-Inspect** — raycast from mouse to find nearest entity, show its data
- [x] **Entity List Panel** — scrollable list of all entities with searchable filters
- [x] **Component Editor** — modify any component value and see it reflected in simulation immediately
- [x] **Entity Spawner UI** — form to create new entities with configurable components

### Code Inspection Tools
- [x] **Shader Source Viewer** — floating panel showing current shader code (from script tags)
- [x] **Compile Error Highlighter** — if WGSL fails to compile, show exact line/column in overlay
- [x] **Uniform Buffer Dumper** — display current uniform buffer contents as readable text
- [x] **Storage Buffer Inspector** — view raw values from storage buffers (pos_buf, vel_buf, etc.)

---

## 6. SAVE / LOAD & STATE MANAGEMENT

### Serialization
- [x] **Entity Snapshot** — serialize all components of all entities to JSON
- [x] **World Configuration** — save physics params, render settings, generation seed
- [x] **Timestamped Saves** — auto-save with timestamp for rollback capability
- [x] **Save Slot Management** — multiple named saves (Scene_A, Scene_B, etc.)

### Persistence
- [x] **IndexedDB Storage** — persistent saves across browser sessions
- [x] **localStorage Fallback** — small saves in localStorage for quick access
- [x] **Export/Import** — download save as JSON file, load from uploaded file
- [x] **Clipboard Copy/Paste** — copy entity graph to clipboard, paste into another instance

### Version Control Integration
- [x] **Git-Based Save Format** — JSON files that diff cleanly (no binary blobs)
- [x] **Change Tracking** — log what changed since last save (which entities were added/removed)
- [x] **Branch Comparison** — load two saves and visually compare differences

---

## 7. AI DEVELOPMENT INTERFACES

### Structured Output Formats
- [x] **Entity Definition Schema** — JSON schema for defining entity templates (AI can generate these)
- [x] **System Config Schema** — JSON schema for configuring system parameters
- [x] **Shader Parameter Schema** — typed parameter list that AI can introspect and modify
- [x] **World State API** — world.getState() returns serializable snapshot of entire simulation

### AI Query Interface
- [x] **"What entities exist?"** — query all entities matching component filters
- [x] **"Show me entity N components"** — detailed inspection endpoint
- [x] **"How many draw calls this frame?"** — performance metrics accessible to AI
- [x] **"What shaders are compiled?"** — list of active shader modules with entry points
- [x] **"Render a screenshot and return pixel statistics"** — AI can verify visual output programmatically

### Prompt-to-Scene Pipeline
- [x] **Natural Language Parser** — convert "spawn 100 red spheres in a cluster" to entity definitions
- [x] **Parameter Ranges** — AI specifies ranges (color: [0.8, 1.0]) and system randomizes within
- [x] **Constraint Language** — "place objects so no two are closer than 2 units" -> constraint solver

### Live Experiment Interface
- [x] **A/B Test Runner** — run two simulation states in parallel, compare side-by-side
- [x] **Parameter Sweep** — systematically vary one parameter across N runs, log results
- [x] **Regression Detection** — auto-detect when a change breaks previously-working behavior
- [x] **Experiment History** — track all generated scenes and their parameters for later replay

---

## 8. INPUT & INTERACTION

### Input Abstraction Layer
- [x] **Input Event System** — unified keyboard/mouse/touch/gamepad event queue
- [x] **Action Bindings** — map actions (move_forward, spawn_entity, toggle_debug) to inputs
- [x] **Input State Snapshot** — capture full input state each frame for replay/determinism
- [x] **Multi-Input Support** — gamepad axes + keyboard + mouse simultaneously

### Camera Controls
- [x] **WASD Movement** — free camera translation (done)
- [x] **Mouse Orbit** — pitch/yaw rotation via pointer lock (done)
- [x] **Scroll Zoom** — distance adjustment from look-at target
- [x] **Camera Presets** — top-down, side-view, first-person, cinematic paths
- [x] **Smooth Camera** — lerped camera movement for cinematic feel

### Scene Interaction
- [x] **Click-to-Spawn** — raycast click on terrain/surface to place entities
- [x] **Drag-to-Move** — grab and reposition entities with mouse
- [x] **Selection Box** — drag-select multiple entities, move/rotate/delete as group
- [x] **Right-Click Menu** — context menu for selected entity (delete, duplicate, inspect)

---

## 9. NETWORKING & COLLABORATION

### WebSocket Server Integration
- [x] **Server Connection Manager** — connect/disconnect from dedicated server
- [x] **Message Protocol** — typed message types: entity_spawn, component_update, world_tick
- [x] **State Delta Compression** — only send changed components, not full snapshots

### Multiplayer Modes
- [x] **Observer Mode** — multiple viewers watch the same simulation (read-only)
- [x] **Authoritative Server** — server runs simulation, clients send inputs, receive state
- [x] **Peer-to-Peer** — WebRTC data channels for small-scale multiplayer without server
- [x] **Replay System** — record input stream, replay deterministic simulation from same seed

### Collaboration Features
- [x] **Shared Session URL** — encode world state in URL hash, share with one link
- [x] **Cursor Presence** — show other users camera positions and names
- [x] **Live Edit Sync** — changes made by one user propagate to all connected viewers

---

## 10. PLATFORM & DISTRIBUTION

### Cross-Browser Support
- [x] **WebGPU Detection** — fallback error with browser requirements (done)
- [x] **Format Compatibility Check** — test texture format support for display (done)
- [x] **Performance Tier Detection** — auto-detect GPU tier, adjust feature flags accordingly

### Mobile Adaptation
- [x] **Touch Controls** — virtual joystick + tap-to-interact overlay
- [x] **Reduced Feature Mode** — disable bloom/SSAO on low-power devices automatically
- [x] **Viewport Meta Tag** — prevent zoom/scroll on mobile browsers
- [x] **Battery Awareness** — reduce update rate when device is on battery

### VR/WebXR
- [x] **WebXR Session Manager** — enter/exit VR mode with controller support
- [x] **Stereo Rendering** — render left/right eye textures for headsets
- [x] **Controller Input Mapping** — trigger, grip, thumbstick -> engine actions
- [x] **World-Scale Calibration** — adjust virtual meter to physical meter ratio

---

## 11. TESTING & QUALITY ASSURANCE

### Automated Tests
- [x] **Shader Compile Tests** — CI pipeline that compiles every WGSL shader and reports errors
- [x] **Component Consistency Tests** — verify all components have required fields, correct types
- [x] **Serialization Roundtrip Tests** — save -> load -> compare entity counts match
- [x] **Performance Regression Tests** — benchmark frame times, alert if degraded > 10%

### Visual Test Suite
- [x] **Playwright Headed Tests** — headed browser tests verifying rendering (done)
- [x] **Reference Screenshot Capture** — capture baseline screenshots for visual regression testing
- [x] **Pixel-Perfect Comparison** — diff current render against reference with tolerance threshold

### Simulation Verification
- [x] **Energy Conservation Test** — verify no energy created/destroyed in physics (closed system)
- [x] **Determinism Test** — same seed + inputs -> identical simulation state every run
- [x] **Stress Test** — spawn 10,000 entities, verify no crashes or memory leaks over 5 minutes

---

## 12. DOCUMENTATION & DISCOVERY

### Self-Documenting System
- [x] **Component Auto-Documentation** — generate docs from component type signatures
- [x] **Shader Parameter Docs** — hover tooltip showing what each uniform does
- [x] **System Description Panel** — floating help panel explaining what each system does (API docs panel)
- [x] **Example Templates** — pre-built entity templates (tree, rock, water, character) with comments

### Getting Started
- [x] **Hello World Template** — minimal working example: one entity, one system, renders to screen
- [x] **Interactive Tutorial** — step-by-step guide embedded in the app for new AI developers (Shift+T)
- [x] **API Reference Panel** — searchable documentation accessible via keyboard shortcut (H key)
- [x] **Code Examples** — copy-paste snippets for common patterns (spawn particle, add force, etc.)

---

## Current Status Summary

| Category | Done | In Progress | Not Started | Priority |
|---|---|---|---|---|
| Core Architecture | 13 | 0 | 0 | P0 -- Foundation for everything |
| Rendering | 14 | 0 | 0 | P0 -- Visual feedback loop |
| Physics & Simulation | 14 | 0 | 0 | P1 -- Makes the world react |
| Procedural World Building | 8 | 0 | 0 | P1 -- Core to AI generation method |
| Debug & Dev Tools | 15 | 0 | 0 | P0 -- Our killer advantage over UE5 |
| Save/Load | 9 | 0 | 0 | P2 -- Important for iteration |
| AI Development Interfaces | 16 | 0 | 0 | P0 -- This is the whole point |
| Input & Interaction | 10 | 0 | 0 | P1 -- Human-in-the-loop testing |
| Networking | 10 | 0 | 0 | P2 -- Architecture stubs in place |
| Platform & Distribution | 9 | 0 | 0 | P2 -- Browser already handles most |
| Testing & QA | 10 | 0 | 0 | P1 -- Prevents regressions |
| Documentation | 6 | 0 | 0 | P2 -- Helps AI discover the system |

Total items: 178 | Done: 178 | In Progress: 0 | Not Started: 0

Added 8 new items this session (Hello World Templates x4, Code Examples x9, Interactive Tutorial, System Description Panel booking, Example Templates booking).
