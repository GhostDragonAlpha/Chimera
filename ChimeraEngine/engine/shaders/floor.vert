#version 450
// floor.vert — THE GROUND PLANE under the creature (2026-09-03, the eye's
// standing render finding: "shadow detached from the contact point / floor
// barely visible"). The contact shadow projects onto y=0, but a plane of
// sparse grid LINES gave the shadow nothing to land on: black@0.38 over a
// ~15/255 background is a ~6/255 delta — below the perception floor. A
// filled, LIGHT plane receives it. Position-only input; y comes from the UBO
// so the plane and the shadow's canvas can never disagree.
layout(location = 0) in vec3 aPos;
layout(set = 0, binding = 0) uniform Ubo {
    mat4 uProj;
    mat4 uView;
    vec2 uResolution;
    float uFloorY;        // the same plane the shadow pins to
    float uShadowAlpha;
} ubo;

void main() {
    vec3 wp = vec3(aPos.x, ubo.uFloorY, aPos.z);
    gl_Position = ubo.uProj * ubo.uView * vec4(wp, 1.0);
}
