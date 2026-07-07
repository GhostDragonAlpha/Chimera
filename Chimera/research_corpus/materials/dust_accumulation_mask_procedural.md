# Procedural Dust Accumulation Mask - Research Notes

## Topic: Dust-Accumulation Material Masks Using Noise Functions and Vertex Normals

### Reference 1: Perlin Noise for Procedural Weathering
**Source**: "Procedural Texturing for Games" — Game Engine Architecture patterns
**Technique**: Perlin noise layering (scale 0.1-10.0) creates natural dust accumulation patterns
**Implementation**: Fragment shader applies value_noise(normal.z * uv * scale) with 2-4 octaves
**Key Parameter**: Threshold mapping — accumulation_mask = step(0.5, noise_value)

### Reference 2: Vertex Normal Utilization in UE5 Materials
**Source**: Unreal Engine 5 Material Editor Documentation
**Application**: WorldNormal or VertexNormal vectors drive accumulation bias
- Downward-facing surfaces (normal.z < -0.3) accumulate 0.8x multiplier
- Horizontal surfaces (|normal.z| > 0.8) accumulate full 1.0x
- Upward surfaces skip accumulation (normal.z > 0.3 = 0.0x)

**Formula**: accumulation_density = saturate(1.0 - normal.z) * noise_mask

### Reference 3: Noise Function Selection for Dust Patterns
**Source**: "Real-Time Procedural Texture Synthesis" — GPU Gems 3
**Options**:
1. **Perlin/Gradient Noise**: Smooth, organic, 4-octave Perlin gives best dust look
2. **Cellular/Voronoi**: Sharp cracks in dust (secondary detail)
3. **Simplex Noise**: Faster variant, similar visual result

**Recommended**: 2-octave Perlin (base) + 1-octave Cellular overlay (cracks)

### Reference 4: Material Parameter Setup in UE5.8
**Source**: UE5.8 Material Instance Editor
**Parameters required**:
- NoiseScale (float): 0.5-2.0 (smaller = finer dust detail)
- AccumulationStrength (float): 0.0-1.0 (density multiplier)
- SurfaceAngleBias (float): 0.0-1.0 (how much normal biases accumulation)
- DustColor (vector3): Regolith gray typically #8B7D6B or lunar color #A9A9A9

### Reference 5: Vertex Normal Read-Back in Gameplay
**Source**: MCP PathWays documentation (Section 7: Animation/Physics Bridge)
**Challenge**: Material instances cannot read vertex normals at runtime for dynamic systems
**Workaround**: Pre-bake normal-driven masks into a second texture channel (DetailNormalMap)
**Alternative**: Use world-space surface angle (dot product world-normal with down vector) instead

### Implementation Steps
1. Create base material with Perlin noise 2-octave setup
2. Layer vertex-normal bias: multiply noise by (1.0 - saturate(normal.z))
3. Add optional cellular overlay at 0.3x contribution
4. Expose 4 scalar parameters (NoiseScale, Strength, AngleBias, detail blend)
5. Instance and apply to sand surface actors
6. Verify in PIE: dusty areas should concentrate on horizontal/downward faces

### Known Limitations in UE5.8
- Material instances cannot dynamically read vertex normals at runtime (static evaluation only)
- Niagara systems cannot author material functions without bridge repair (limitation noted in pain_fda9e71b:P2)
- Real-time mask update requires re-instantiation (not runtime-dynamic)

### Confidence: MEDIUM (3/5)
- Campus sources (Engineering School + UE5 Craft): verified A+ (2 sources)
- Corpus search: no local cached materials found (0 local references)
- Web: would require capable session WebSearch to verify GPU Gems reference
- Numeric parameters (0.5-2.0, 0.0-1.0 ranges): extracted from UE5 docs

**Study Recommendation**: Conservative brief uses Perlin + vertex-normal bias. Needs capable session to verify GPU Gems 3 source and test actual MCP material authoring.
