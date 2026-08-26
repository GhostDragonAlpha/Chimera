#version 450
layout(location = 0) in vec3 vNormal;
layout(location = 1) in vec3 vColor;
layout(location = 0) out vec4 fragColor;
void main() {
    vec3 N = normalize(vNormal);
    vec3 L = normalize(vec3(0.35, 0.8, 0.45));
    float diff = max(dot(N, L), 0.0);
    float amb = 0.25;
    vec3 col = vColor * (amb + 0.85 * diff);
    fragColor = vec4(col, 1.0);
}
