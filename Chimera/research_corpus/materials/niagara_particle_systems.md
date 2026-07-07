# Niagara Particle Systems and Material Integration - Technical Reference

## Topic: Dust Particle Rendering with Procedural Material Masks in UE5.8

### Reference 1: UE5.8 Niagara System Architecture
**Source**: Unreal Engine 5.8 Official Documentation - Niagara System Guide
**Structure**: Emitter (spawn/lifetime) → Module Stack (physics, render) → Renderer (sprite/mesh/ribbon)
**Material Integration**: Each emitter has optional Material override slot
**Key Limitation**: In UE5.8, material instances cannot dynamically read per-particle vertex normals

### Reference 2: Sprite Renderer vs Mesh Renderer for Dust
**Source**: "Particle Effects in Modern Game Engines" - GDC Technical Art Track
**Sprite Renderer**: 
- Best for dust clouds (camera-facing billboards)
- Can use procedural texture atlases
- Material driven by particle properties (age, lifetime, velocity)

**Mesh Renderer**:
- Better for settling dust on surfaces
- Can inherit surface normals (if mesh-based accumulation desired)
- More expensive computationally

**Dust Recommendation**: Sprite renderer with animated texture + fade/scale over lifetime

### Reference 3: Procedural Texture Atlas for Dust Particles
**Source**: "Fluid Simulation and Particle Effects" - Real-Time Rendering (4th ed.)
**Technique**: Create procedural material with noise-based mask
**Atlas Approach**: 2x2 or 4x4 grid of dust sprites, each with unique Perlin noise pattern
**Parameter Variation**:
- Particle index selects atlas tile (modulo operation)
- Per-particle random seed varies noise phase
- Result: no visible repetition in sprite sheet

**Frame**: Single frame (not animated) with built-in spatial variation

### Reference 4: Material Parameter Exposure for Particle Interaction
**Source**: UE5 Material Instance Editor - Scalar/Vector Parameter Lists
**Exposed Parameters**:
- NoiseFrequency (scalar): 0.5-3.0 (higher = more fine detail)
- DustOpacity (scalar): 0.3-0.9 (dust transparency over lifetime)
- FallVelocityBias (scalar): 0.1-1.0 (affects sprite fade gradient)
- DustTint (vector): Color modulation per-particle (if vertex color used)

### Reference 5: Niagara Module Stack for Dust Accumulation Emitter
**Source**: Unreal Engine Niagara Documentation - Module Reference
**Required Modules**:
1. Spawn (Rate or Burst)
2. Lifetime (5-30 second range for dust settling)
3. Velocity (initial: 0-50 cm/s random, gravity driven)
4. Forces (gravity: -162 cm/s², air resistance: 0.1-0.3)
5. Scale (start: 1.0, end: 0.8-1.0, maintains visual weight)
6. Fade (alpha: 1.0 start → 0.3 end, settling appearance)
7. Renderer (Sprite, material with procedural dust mask)

### Reference 6: Known Issues - UE5.8 Niagara Authoring via MCP
**Source**: McpAutomationBridge Limitation Documentation (LOCAL)
**Issue**: set_niagara_parameter calls succeed but do not persist
- Status: **FACADE #2 CONFIRMED** (writes to transient, not saved)
- Workaround: Requires capable session to fix bridge implementation
- Current blocker: Ground_Sand_Particles fidelity debt (pain_fda9e71b:P2)

**Timeline**: Repair planned for capable-session-only phase

## Implementation Checklist
- [x] Lunar regolith color: #8B7D6B confirmed
- [x] Gravity: -162 cm/s² confirmed
- [x] Dust particle lifetime: 5-20 seconds reasonable
- [x] Sprite atlas variation: Perlin noise per-tile proven technique
- [ ] MCP niagara authoring: Blocked until bridge repair (capable-only)
- [ ] Material mask generation: Scholar brief recommends conservative approach

## Confidence: MEDIUM-HIGH (3.5/5)
- UE5 documentation: A+ verified
- GDC technical talks: B+ verified
- Niagara module reference: A+ verified
- Local pain points: Confirmed via graph
- Gap: Cannot validate actual MCP calls without capable session

## Cross-Reference
- **Ground_Sand_Particles** (Loop 1 feature): Uses this system for dust rendering
- **Material_Dust_Accumulation_Mask** (pending research): Integrates with this particle system
- **Bridge Pain (P2)**: Blocks full-fidelity implementation until Niagara authoring repaired
