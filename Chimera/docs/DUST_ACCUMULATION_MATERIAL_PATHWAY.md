> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# Procedural Dust-Accumulation Mask Material Pathway

## Overview

This document describes the MCP pathways for creating a procedural dust-accumulation mask material in Unreal Engine 5 using:
- **Procedural noise functions** (Perlin/Gradient and Voronoi/Worley)
- **Vertex normal-based masking** using dot product with world Z-axis or down vector

## Material Expression Nodes Used

### 1. Vertex Normal Input
- **MCP Action**: `add_vertex_normal`
- **UE Node**: `UMaterialExpressionVertexNormalWS` (World-Space Vertex Normal)
- **Purpose**: Provides the world-space normal for each vertex/pixel of the surface

### 2. Dot Product for Surface Orientation
- **MCP Action**: Use operations node with `DotProduct` function or manual multiplication/addition
- **Formula**: `Dot(VertexNormal, WorldUpVector)` or `Dot(VertexNormal, WorldDownVector)`
- **Purpose**: Determine if surfaces are facing upward, downward, or horizontal

### 3. Procedural Noise Functions
- **MCP Actions**: 
  - `add_noise` - Perlin/Gradient noise (default)
  - `add_voronoi` - Voronoi/Worley noise (`ENoiseFunction::NOISEFUNCTION_VoronoiALU`)
- **Purpose**: Generate organic variation for dust distribution

### 4. Combination Nodes
- **MCP Actions**: Operations nodes with `Multiply`, `Lerp`, or `Add`
- **Purpose**: Combine normal-based factor and procedural noise mask

## Material Graph Construction Recipe

### Step 1: Create Base Material
```
Tool: unreal_engine_manage_asset
Action: create_material
Parameters: {name: "MAT_DustAccumulationMask", path: "/Game/Chimera/Materials/MAT_DustAccumulationMask"}
```

### Step 2: Add Vertex Normal Node
```
Tool: unreal_engine_manage_asset
Action: add_vertex_normal
Parameters: {assetPath: "/Game/Chimera/Materials/MAT_DustAccumulationMask/MAT_DustAccumulationMask", x: -400, y: 200}
Result Node ID: <vertex_normal_node_id>
```

### Step 3: Add World Up Vector Constant
```
Tool: unreal_engine_manage_asset
Action: add_vector_parameter (or use constant node)
Parameters: {assetPath: "...", parameterName: "WorldUpVector", defaultValue: {r:0, g:0, b:1, a:1}}
Result Node ID: <world_up_vector_node_id>
```

### Step 4: Calculate Dot Product (Up-Facing Factor)
```
Tool: unreal_engine_manage_asset
Action: connect_material_pins or use operation node for dot product
Formula: UpFacingFactor = Dot(VertexNormalWS, WorldUpVector)
```

### Step 5: Calculate Normal-Based Dust Factor
```
Operations to apply:
1. Invert up-facing factor: 1.0 - UpFacingFactor
2. Clamp to [0, 1]: max(0, 1.0 - UpFacingFactor)
3. Apply threshold check: if (UpFacingFactor > NormalThreshold) return 0.0

Result: DownFacingFactor = max(0, 1.0 - UpFacingFactor)
```

### Step 6: Add Procedural Noise Node
Choose one of the following based on desired organic variation style:

**Option A: Perlin/Gradient Noise (default)**
```
Tool: unreal_engine_manage_asset
Action: add_noise
Parameters: {assetPath: "...", x: -200, y: 400}
Result Node ID: <noise_node_id>
```

**Option B: Voronoi/Worley Noise**
```
Tool: unreal_engine_manage_asset
Action: add_voronoi
Parameters: {assetPath: "...", x: -200, y: 400}
Result Node ID: <voronoi_node_id>
Note: Internally sets ENoiseFunction::NOISEFUNCTION_VoronoiALU
```

### Step 7: Connect Noise to Texture Coordinates or World Position
For time-varying or position-based noise:
- Use `add_world_position` node and extract X/Y coordinates
- Or use texture coordinate UV channel with tiling parameters

### Step 8: Combine Normal Factor and Noise Mask
```
Operations:
1. Multiply DownFacingFactor by NoiseMask value
2. Apply Lerp or blend based on noise intensity parameter
3. Final intensity = NormalFactor * NoiseMask * AccumulationRate
4. Clamp to [0, 1] range
```

### Step 9: Connect to Material Output
Connect the final combined intensity to the material's mask output or use it as a parameter for blending with base ground materials.

## C++ Implementation Reference

The `UDustAccumulationMaterial` class provides the following methods:

| Method | Purpose |
|--------|---------|
| `GetDustIntensity(FVector VertexNormal, float Time)` | Basic dust intensity calculation using sin/cos noise |
| `CalculateNormalFactor(const FVector& VertexNormal, float Threshold)` | Dot product with world up vector to determine downward-facing surfaces |
| `GenerateProceduralNoise(float X, float Y, float Time, bool bUseVoronoi)` | Procedural noise generation (Perlin or Voronoi/Worley) |
| `GetCombinedDustIntensity(FVector VertexNormal, float Time, float NoiseScale, bool bUseVoronoi)` | Complete combined intensity calculation |

## Material Parameters to Expose

| Parameter Name | Type | Default | Description |
|----------------|------|---------|-------------|
| `AccumulationRate` | Scalar | 0.5 | Base rate of dust accumulation |
| `DecayRate` | Scalar | 0.2 | Rate at which dust dissipates |
| `NormalThreshold` | Scalar | 0.7 | Threshold for upward-facing surfaces (no dust above this) |
| `NoiseScale` | Scalar | 1.0 | Scale of procedural noise variation |
| `NoiseFrequency` | Scalar | 3.0 | Tile/frequency size for noise generation |

## MCP Pathway Integration Notes

- Use `add_vertex_normal` to get world-space vertex normals
- Use `add_noise` or `add_voronoi` for procedural variation
- Voronoi uses `ENoiseFunction::NOISEFUNCTION_VoronoiALU` internally
- Connect noise output and normal factor using multiply/lerp operations
- Compile material after all connections are made

## Related Files

- `Source/Chimera/ProceduralGenerated/Materials/DustAccumulationMaterial.h` - C++ interface
- `Source/Chimera/ProceduralGenerated/Materials/DustAccumulationMaterial.cpp` - Implementation
- `Source/Chimera/ProceduralGenerated/Materials/DustAccumulationParticleComponent.h/cpp` - Particle system component
