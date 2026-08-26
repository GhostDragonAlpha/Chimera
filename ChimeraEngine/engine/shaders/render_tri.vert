#version 450
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec3 aColor;
layout(set = 0, binding = 0) uniform Ubo {
    mat4 uProj;
    mat4 uView;
    vec2 uResolution;
} ubo;
layout(location = 0) out vec3 vNormal;
layout(location = 1) out vec3 vColor;
void main() {
    vec4 viewPos = ubo.uView * vec4(aPos, 1.0);
    gl_Position = ubo.uProj * viewPos;
    vNormal = mat3(ubo.uView) * aNormal;
    vColor = aColor;
}
