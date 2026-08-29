#version 450
// render_tri_frost.frag — H9 frost display: the decoded per-triangle relit RGB
// (Q16 int32 in the frost color SSBO, written by frost_decode.comp) shown RAW —
// the decode IS the shading; the stock render_tri.frag Lambert would double-shade.
// Flat per-triangle color via gl_PrimitiveID (the mesh's welded/shared vertices
// cannot carry per-triangle colors).
layout(location = 0) in vec3 vNormal;
layout(location = 1) in vec3 vColor;
layout(location = 0) out vec4 fragColor;
layout(std430, set = 1, binding = 0) readonly buffer FColor { int rgb[]; };
void main() {
    int t = gl_PrimitiveID;
    vec3 c = vec3(float(rgb[3 * t]), float(rgb[3 * t + 1]), float(rgb[3 * t + 2]))
             * (5.0 / 65536.0);   // x5 DISPLAY gain only (GT radiance p99.9 = 0.16 —
                                  //  purely presentational, outside the bit-exact
                                  //  boundary; the stored Q16 ints are untouched)
    fragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}
