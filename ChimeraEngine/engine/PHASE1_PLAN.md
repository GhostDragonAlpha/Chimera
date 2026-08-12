# SPIACE Phase 1: Orbital Space

## Goals
- N-body gravity on GPU (extend Chimera's existing compute shader)
- Multiple planets with proper orbital periods (Kepler's third law verified)
- Transfer orbits: Hohmann, bi-elliptic, gravity assists
- Render: ray-marched void + point-sprite bodies + star glow
- UI: orbital map, velocity readout, delta-v calculator
- Deliverable: Multi-body system with player ship navigating orbits

## Architecture

### GPU N-body Compute Shader (WGSL)
```wgsl
@group(0) @binding(0) var<storage, read_write> states: array<BodyState>;
@group(0) @binding(1) var<uniform> params: vec3<f32>; // G, dt, softening

@compute @workgroup_size(256)
fn nbody(@builtin(global_invocation_id) gid: vec3<u32>) {
    let idx = gid.x;
    if (idx >= arrayLength(&states)) return;

    var acc = vec3<f32>(0.0);
    for (let j = 0u; j < arrayLength(&states); j++) {
        if (j == idx) continue;
        let r = states[j].pos - states[idx].pos;
        let distSq = dot(r, r) + params.z; // softening
        let mag = params.x * states[j].mass / (distSq * sqrt(distSq));
        acc += mag * normalize(r);
    }

    // Symplectic Euler integration
    states[idx].vel += acc * params.y;
    states[idx].pos += states[idx].vel * params.y;
}
```

### Orbital Mechanics Extensions
- Hohmann transfer: two-ellipse burn sequence
- Gravity assist: patch conic approximation
- Delta-v budget calculator (UI overlay)

### Rendering Pipeline
1. Ray march from camera through each pixel
2. SDF sphere intersections for bodies
3. Point sprite billboard for ship
4. Star glow volumetric accumulation

## Files to Create/Modify
- `engine/spiace_phase1.html` - Main demo
- `engine/shaders/nbody.wgsl` - GPU N-body compute shader
- `engine/shaders/raymarch.wgsl` - Void ray marching fragment shader
