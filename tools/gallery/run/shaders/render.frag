#version 450
// 3D Gaussian Splatting fragment — evaluates the anisotropic 2D Gaussian.
// gl_PointCoord is [0,1] within the point's square; p is the centered pixel offset.

layout(location = 0) in vec3  vColor;
layout(location = 1) in float vAlpha;
layout(location = 2) in mat2  vCovInv;
layout(location = 4) in float vPointSize;

layout(location = 0) out vec4 fragColor;

void main() {
    vec2 p = (gl_PointCoord - vec2(0.5)) * vPointSize;
    float g = exp(-0.5 * dot(p, vCovInv * p));
    float a = vAlpha * g;
    if (a < 1.0 / 255.0) discard;
    fragColor = vec4(vColor, a);   // straight alpha (back-to-front blend)
}
