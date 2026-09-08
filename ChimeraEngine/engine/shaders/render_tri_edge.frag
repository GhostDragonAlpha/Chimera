#version 450
// render_tri_edge.frag — GLM-DEMO-CONTRAST-01: the opt-in edge-contrast twin
// of render_tri.frag. The ordinary wireframe pipeline is the FILL pipeline
// with polygon mode LINE, so wireframe edges carry the same vertex color and
// lighting as the fill and vanish against it (measured GLM-DYAD-02: the dyad
// could not resolve the B2 centre height; fill statistics identical across
// states at every camera). This fragment ignores the lighting varyings and
// emits ONE CONSTANT LIGHT EDGE COLOR for every edge pixel.
//
// Edge color derivation (from the measured evidence, no invented taste):
//   the demo fill band is 147..167 (8-bit) on all faces of the B2 states;
//   the family neutral is (0.60, 0.60, 0.65) — the +0.05 blue tint. The edge
//   color is the same neutral LIFTED above the whole fill band:
//   (0.90, 0.90, 0.95) -> 8-bit (230, 230, 242), contrast ratio ~1.4:1
//   against the brightest fill. Same hue family, strictly brighter.
//
// Opt-in law: the pipeline using this fragment is created ONLY when the env
// var CHIMERA_TRI_EDGE_CONTRAST is set; ordinary rendering never touches it.
layout(location = 0) in vec3 vNormal;    // unused (no lighting on edges)
layout(location = 1) in vec3 vColor;     // unused (constant edge color)
layout(location = 2) in vec3 vLightDir;  // unused (no lighting on edges)
layout(location = 0) out vec4 fragColor;
void main() {
    fragColor = vec4(0.90, 0.90, 0.95, 1.0);
}
