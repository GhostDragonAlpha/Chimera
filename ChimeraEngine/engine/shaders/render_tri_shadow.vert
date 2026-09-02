#version 450
// render_tri_shadow.vert — THE CONTACT SHADOW (the eye's "subject ungrounded",
// 2026-09-02): the same mesh drawn again, projected onto the grid plane along
// the LIGHT's own direction — the same L render_tri.frag shades by, so the
// shadow's offset always agrees with the lit side. Planar projection in the
// vertex stage: zero CPU work, zero readbacks, and the GPU hinge pose flows
// in for free (the shadow marches with the knees by construction).
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;   // stride-9 record: consumed for layout
layout(location = 2) in vec3 aColor;
layout(set = 0, binding = 0) uniform Ubo {
    mat4 uProj;
    mat4 uView;
    vec2 uResolution;
    float uFloorY;        // the grid plane's height (the shadow's canvas)
    float uShadowAlpha;
} ubo;

void main() {
    vec3 L = normalize(vec3(0.35, 0.8, 0.45));   // THE light (render_tri.frag's)
    float t = (aPos.y - ubo.uFloorY) / max(L.y, 1e-4);
    vec3 sp = aPos - L * t;                      // slide down the light ray...
    sp.y = ubo.uFloorY;                          // ...and pin to the floor plane
    gl_Position = ubo.uProj * ubo.uView * vec4(sp, 1.0);
}
