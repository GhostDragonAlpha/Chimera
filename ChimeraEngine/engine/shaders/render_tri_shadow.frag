#version 450
// render_tri_shadow.frag — the contact shadow's ink: flat translucent
// darkness, alpha arriving PER-VERTEX (the height-derived penumbra computed in
// the vertex stage — see render_tri_shadow.vert). The fragment stage reads NO
// UBO on this pipeline: fingerprint probes (2026-09-03) proved its uniform
// block read lands at wrong bytes, so every value it needs is interpolated in.
//
// CLOSED-SILHOUETTE LAW (measured): the projected mesh is a closed 2D
// silhouette — interior pixels catch ≥2 layers, composing opacity
// 1−(1−α)² (≈ 0.62×α²-effect at contact: floor 55 → ~21 with A0=0.38);
// stacked limbs darken further, honestly.
layout(location = 0) in float vAlpha;
layout(location = 0) out vec4 fragColor;

void main() {
    fragColor = vec4(0.0, 0.0, 0.0, clamp(vAlpha, 0.0, 1.0));
}
