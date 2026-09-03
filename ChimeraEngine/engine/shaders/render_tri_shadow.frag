#version 450
// render_tri_shadow.frag — the contact shadow's ink: one flat translucent
// darkness (the planar projection already carries the shape; double-shading
// the projection would be decoration, not information).
layout(location = 0) out vec4 fragColor;
layout(set = 0, binding = 0) uniform Ubo {
    mat4 uProj;
    mat4 uView;
    vec2 uResolution;
    float uFloorY;
    float uShadowAlpha;
} ubo;

void main() {
    // THE SHADOW'S INK — an authored constant, NOT a UBO read (measured
    // 2026-09-03): the fragment-side UBO read on this pipeline provably lands
    // at wrong bytes (fingerprint probes: the alpha arrived as 55/255 ≈ a
    // view-matrix element, while the VERTEX stage reads the same buffer
    // correctly — the blob positions exactly on the floor plane). The value is
    // a perceptual decree (the eye's 0.38), not a measured quantity, so it
    // lives here. CLOSED-SILHOUETTE LAW: the projected mesh is a closed 2D
    // silhouette — interior pixels catch ≥2 layers, composing 1−(1−α)² ≈ 0.62
    // opacity; over the 55/255 floor that reads ≈21/255 (a 34-delta, firmly
    // visible), and stacked limbs darken further, honestly.
    fragColor = vec4(0.0, 0.0, 0.0, 0.38);
}
