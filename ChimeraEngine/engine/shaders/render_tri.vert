#version 450
// render_tri.vert — passes the geometry through and hands the fragment the ONE
// light vector (the Studio-owned direction from the UBO). Vertex stages are the
// measured-trustworthy UBO readers on this pipeline; the fragment consumes the
// light as a varying so /light steering works without any frag-side block read.
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec3 aColor;
layout(set = 0, binding = 0) uniform Ubo {
    mat4 uProj;
    mat4 uView;
    vec2 uResolution;
    float uFloorY;
    float uShadowAlpha;
    float uShadowH0;
    vec4 uLightDir;       // THE LIGHT (xyz unit length; Studio-owned). VEC4, NOT
                          // vec3: std140 aligns a vec3 to 16 bytes — after the
                          // scalars that is offset 160 while the C++ struct packs
                          // 152 — every read lands 16 bytes off (measured: NaN
                          // light, black body, vanished shadow). vec4 aligns
                          // naturally; the alignment trap class dies here.
} ubo;
layout(location = 0) out vec3 vNormal;
layout(location = 1) out vec3 vColor;
layout(location = 2) out vec3 vLightDir;
void main() {
    vec4 viewPos = ubo.uView * vec4(aPos, 1.0);
    gl_Position = ubo.uProj * viewPos;
    vNormal = aNormal;   // WORLD space: the light is anchored to the world,
                         // not glued to the camera (was mat3(uView) * aNormal,
                         // which made brightness change as the camera orbits)
    vColor = aColor;
    vLightDir = ubo.uLightDir.xyz;
}
