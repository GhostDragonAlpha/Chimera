#version 450
// floor.vert — THE GROUND PLANE under the creature (2026-09-03, the eye's
// standing render finding: "shadow detached from the contact point / floor
// barely visible"). The contact shadow projects onto y=0, but a plane of
// sparse grid LINES gave the shadow nothing to land on: black@0.38 over a
// ~15/255 background is a ~6/255 delta — below the perception floor. A
// filled, LIGHT plane receives it. Position-only input; y comes from the UBO
// so the plane and the shadow's canvas can never disagree.
//
// THE CYCLORAMA (2026-09-03, the eye twice: "the back plane falls off flat
// with no fill or rim, so the silhouette edge gets muddy"): a real studio
// sweep darkens with distance from the subject. The fragment receives the
// horizontal distance from the origin and the mesh's own measured radius —
// computed HERE (vertex UBO reads are the measured-trustworthy ones; no
// fragment stage touches the UBO on this lane). The fade starts at the mesh
// extent and bottoms at 1/3 floor ink by R*3 — beyond any camera's view.
layout(location = 0) in vec3 aPos;
layout(set = 0, binding = 0) uniform Ubo {
    mat4 uProj;
    mat4 uView;
    vec2 uResolution;
    float uFloorY;        // the same plane the shadow pins to
    float uShadowAlpha;
    float uShadowH0;
    vec4 uLightDir;
    float uMeshR;         // the cyclorama's inner radius (0 pre-mesh)
} ubo;

layout(location = 0) out float vDist;
layout(location = 1) out float vMeshR;

void main() {
    vec3 wp = vec3(aPos.x, ubo.uFloorY, aPos.z);
    gl_Position = ubo.uProj * ubo.uView * vec4(wp, 1.0);
    vDist   = length(aPos.xz);
    vMeshR  = max(ubo.uMeshR, 1.0);   // pre-mesh: fade starts at 1 wu, floor flat near origin
}
