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
    fragColor = vec4(0.0, 0.0, 0.0, ubo.uShadowAlpha);
}
