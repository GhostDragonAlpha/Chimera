#version 450
// render_tri.frag — the creature's shading. 2026-09-03, the eye (loaded review):
// "severely underexposed single-source light... the right arm and right leg fall
// to near-black and merge into the background." Diagnosis: one key + flat 0.25
// ambient on a near-black background — the unlit flank sat below the
// perception floor (~40/255, the 2026-09-02 grid law).
//
// The derived fix (three-point, no invented numbers):
//   key   0.85 unchanged, direction unchanged — the contact shadow
//         (render_tri_shadow.vert's L) must keep agreeing.
//   wrap  0.10 — the key has area, so the terminator softens: (d+0.10)/1.10.
//   fill  0.18 opposite the key, lower: a 4.7:1 key:fill ratio, the classic
//         readable-form band (4:1..5:1) — modelling without flatness.
//   amb   hemisphere mix(0.15, 0.35, up) — sky light above, dark-floor bounce
//         below; replaces flat 0.25 so verticals (arms, flanks) get 0.25 and
//         up-facing surfaces get more, down-facing less. Scene-coherent.
//
// THE LIGHT IS ONE FACT (2026-09-03 membrane): the key's direction arrives as
// a VERTEX-stage varying (vLightDir, read from the UBO by render_tri.vert —
// vertex UBO reads are the measured-trustworthy ones; fragment block reads on
// this pipeline are not). The fill is derived opposite-and-lower from the SAME
// vector, so steering /light moves the whole rig coherently and the contact
// shadow (same UBO vector in render_tri_shadow.vert) always agrees.
//
// E1 RIG (2026-09-13, fleet-2; the blind judges: "a prototype: one model on a
// grid"). STATEMENT: the SAME creature reads as a staged product with a cool
// 4:1 fill and a gold rim. PREDICTION: at the dark-side camera the unlit flank
// clears the ~40/255 perception floor and the rim stays an EDGE (p95 <= 240).
// FALSIFIER: flank still merges, or the rim reads as a second outline.
//   fill  0.18 -> 0.21: 25% of key 0.85 -> 4:1 key:fill (the readable-form band).
//         Tint FILL_TINT cool, luminance-normalized (0.299/0.587/0.114 -> 1.00),
//         so 0.21 stays the measured irradiance.
//   rim   NEW: pow(1-N.V, 3) grazing falloff * RIM 0.35 — 2-3x the dark flank's
//         ~0.15 ambient: clears the 40/255 floor, stays under the albedo clamp.
//         Tint RIM_TINT gold. N.V comes from vViewNormal (view-space, location 3;
//         V ~ +z in view space), computed in the VERTEX stage — fragment UBO
//         reads are untrustworthy on this lane.
// Values mirrored in the E1 STAGE BLOCK (engine.cpp) — change them together.
layout(location = 0) in vec3 vNormal;
layout(location = 1) in vec3 vColor;
layout(location = 2) in vec3 vLightDir;   // THE key (unit length, from the UBO)
layout(location = 3) in vec3 vViewNormal; // E1: view-space normal (rim only)
layout(location = 0) out vec4 fragColor;
void main() {
    const vec3 FILL_TINT = vec3(0.89, 1.00, 1.28);  // E1: cool; luma weights sum to 1.00
    const vec3 RIM_TINT  = vec3(1.00, 0.84, 0.55);  // E1: gold (3200K-class edge)
    vec3 N  = normalize(vNormal);
    vec3 K  = normalize(vLightDir);                 // THE key (the shadow's L too)
    vec3 F  = normalize(vec3(-K.x, -0.3, -K.z));    // fill: opposite, lower
    vec3 Nv = normalize(vViewNormal);               // E1: view-space N; V ~ +z, so N.V ~ Nv.z
    float key  = clamp((dot(N, K) + 0.10) * (0.9090909), 0.0, 1.0) * 0.85;
    float fill = max(dot(N, F), 0.0) * 0.21;        // E1: 25% of key (4:1); was 0.18 (4.7:1)
    float amb  = mix(0.15, 0.35, N.y * 0.5 + 0.5);
    float rim  = pow(1.0 - max(Nv.z, 0.0), 3.0) * 0.35;  // E1: grazing cubed; 0.35 = 2-3x dark flank
    // ENERGY CONSERVATION (2026-09-03, the eye's "overexposed orange" feet):
    // amb+key+fill can reach ~1.38 for up-facing normals caught by the key —
    // more light out than in, which a diffuse surface cannot do. Measured:
    // angle-dependent saturation (feet p95=170 static, hot only when the
    // turntable swings them toward the key). The albedo is the physical cap:
    // outgoing diffuse <= albedo, so the summed irradiance clamps to 1.0.
    // E1: the clamp is per-CHANNEL now (tints make the sum a vec3) and the rim
    // rides under it — a rim that could not clip would not need the clamp.
    vec3 lit = amb + key + fill * FILL_TINT + rim * RIM_TINT;
    fragColor = vec4(vColor * min(lit, vec3(1.0)), 1.0);
}
