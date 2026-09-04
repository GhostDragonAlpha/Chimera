#version 450
// floor.frag — the plane's ink. A lit floor is a second scene to keep
// coherent; this is the canvas the contact shadow needs. THE INK LAW
// (measured, twice judged by the eye): floor 55 under the subject, shadow
// 55*0.62^layers — the contact zone stays EXACTLY 55.
//
// THE CYCLORAMA (2026-09-03, the eye twice: "back plane falls off flat with
// no fill or rim, silhouette edge muddy"). FIRST DRAFT measured HOLD: 55->18
// at 3 radii "overcooked" — black void, cast shadow read as a second object.
// THE EYE'S PRESCRIPTION APPLIED: outer ink 55->32 (a third down, flank 35-50
// still reads against it, the shadow stays a SHADOW at ~20 over it), full
// depth at 5 radii so the lit-cove horizon glow survives. Inner zone and ink
// law untouched.
layout(location = 0) in float vDist;
layout(location = 1) in float vMeshR;
layout(location = 0) out vec4 fragColor;

void main() {
    const vec3 inner = vec3(55.0 / 255.0);
    const vec3 outer = vec3(32.0 / 255.0);   // the eye's gentler pool
    float t = clamp((vDist - vMeshR) / (4.0 * vMeshR), 0.0, 1.0);
    t = t * t;                               // ease-in: the subject's zone stays flat
    fragColor = vec4(mix(inner, outer, t), 1.0);
}
