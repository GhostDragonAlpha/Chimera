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
layout(location = 0) in vec3 vNormal;
layout(location = 1) in vec3 vColor;
layout(location = 0) out vec4 fragColor;
void main() {
    vec3 N = normalize(vNormal);
    vec3 K = normalize(vec3(0.35, 0.8, 0.45));    // THE key (shadow.vert agrees)
    vec3 F = normalize(vec3(-0.35, 0.25, -0.45)); // fill: opposite, lower
    float key  = clamp((dot(N, K) + 0.10) * (1.0 / 1.10), 0.0, 1.0) * 0.85;
    float fill = max(dot(N, F), 0.0) * 0.18;
    float amb  = mix(0.15, 0.35, N.y * 0.5 + 0.5);
    fragColor = vec4(vColor * (amb + key + fill), 1.0);
}
