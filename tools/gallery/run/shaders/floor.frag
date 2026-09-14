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
//
// E1 STAGE (2026-09-13, fleet-2; the blind judges: "a prototype: one model on
// a grid"). STATEMENT: a warm cyclorama pool that lands on the engine's own
// background hue reads as a product stage. PREDICTION: no seam where the sweep
// meets the background, and the composed shadow stays a shadow (>= ~25/255
// below its surround). FALSIFIER: a horizon ring, or the glow lifting the
// contact zone off 55 (the ink law). Values mirrored in the E1 STAGE BLOCK
// (engine.cpp) — change them together.
//   outer  32 gray -> (34,31,27): warmer at the SAME luminance
//          (0.299*34+0.587*31+0.114*27 = 31.4 ~ the eye-approved 32).
//   stage_far: past the approved pool zone the sweep hue-shifts onto the
//          ENGINE CLEAR COLOR (0.015,0.02,0.06 = E1_CLEAR_COLOR, engine.cpp)
//          so the cyclorama terminates in the background, not against it.
//   glow:  a warm light-pool RING, peak 9/255 at 1.5*Rc (Rc mirrors
//          g_shadow_contact_radius = max(2, 0.65*uMeshR)); the center reads
//          e^-(1.5/0.9)^2 ~ 0.06 of peak = +0.6/255 at contact, so the ink
//          law's EXACTLY 55 holds within quantization; the ring dies with the
//          sweep via (1-t).
layout(location = 0) in float vDist;
layout(location = 1) in float vMeshR;
layout(location = 0) out vec4 fragColor;

void main() {
    const vec3 inner = vec3(55.0 / 255.0);
    const vec3 outer = vec3(34.0 / 255.0, 31.0 / 255.0, 27.0 / 255.0); // E1: warm, luma-equal to 32
    const vec3 stage_far = vec3(0.015, 0.02, 0.06);  // E1: THE clear color (E1_CLEAR_COLOR)
    float t = clamp((vDist - vMeshR) / (4.0 * vMeshR), 0.0, 1.0);
    t = t * t;                               // ease-in: the subject's zone stays flat
    vec3 pool = mix(inner, outer, t);
    pool = mix(pool, stage_far, smoothstep(0.70, 1.0, t));  // E1: far hue-shift onto the background;
                                                            // approved 55->32 zone (t<0.7) untouched
    // E1 GROUND GLOW — Gaussian ring; squared by hand (pow(neg, y) is undefined):
    float rc   = max(2.0, 0.65 * vMeshR);                   // mirrors g_shadow_contact_radius
    float d    = (vDist - 1.5 * rc) / (0.9 * rc);           // peak 1.5*Rc, sigma 0.9*Rc
    vec3  glow = (9.0 / 255.0) * vec3(1.0, 0.85, 0.62)      // warm, subtle: shadow stays >= ~25/255
                 * exp(-d * d) * (1.0 - t);                 // below its surround; dies with the sweep
    fragColor = vec4(pool + glow, 1.0);
}
