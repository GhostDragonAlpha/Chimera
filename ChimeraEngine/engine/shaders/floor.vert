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
    vec3 uLightDir;       // std140: 160..171 (vec3 aligns like the C struct's
                          // float[3]; uMeshR then lands at 172 EXACTLY — the old
                          // vec4 pushed it to 176, past the 176-byte C block:
                          // an out-of-bounds undefined read (NaN-ish vMeshR)
                          // that killed the whole plane's ink — the fix measured
                          // 2026-09-20, lane agent/triangle-monkey-grid
    float uMeshR;         // the cyclorama's inner radius (0 pre-mesh)
} ubo;

layout(location = 0) out vec2 vXZ;    // FLOOR-VISIBILITY FIX (2026-09-20,
                                      // lane agent/triangle-monkey-grid): the
                                      // distance is computed in the FRAGMENT
                                      // stage from the interpolated position.
                                      // The old per-VERTEX `length(aPos.xz)`
                                      // interpolated the CORNER distances
                                      // (424 on the R=300 quad) — every
                                      // fragment read ~283, t saturated at 1
                                      // and the whole plane inked to the
                                      // background: an INVISIBLE plane that
                                      // still depth-wrote and occluded (the
                                      // operator's Defect B).
layout(location = 1) out float vMeshR;

void main() {
    vec3 wp = vec3(aPos.x, ubo.uFloorY, aPos.z);
    gl_Position = ubo.uProj * ubo.uView * vec4(wp, 1.0);
    vXZ     = aPos.xz;
    vMeshR  = max(ubo.uMeshR, 1.0);   // pre-mesh: fade starts at 1 wu, floor flat near origin
}
