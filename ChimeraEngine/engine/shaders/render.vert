#version 450
// 3D Gaussian Splatting — EWA splat (anisotropic), 14-float vertex:
//   aPos(3) aColor(3) aAlpha(1) aScale(3) aRot(4 quaternion wxyz)

layout(location = 0) in vec3  aPos;
layout(location = 1) in vec3  aColor;
layout(location = 2) in float aAlpha;
layout(location = 3) in vec3  aScale;
layout(location = 4) in vec4  aRot;

layout(set = 0, binding = 0) uniform Ubo {
    mat4 uProj;
    mat4 uView;
    vec2 uResolution;
} ubo;

layout(location = 0) out vec3  vColor;
layout(location = 1) out float vAlpha;
layout(location = 2) out mat2  vCovInv;    // inverse 2D covariance (pixels) — takes locations 2,3
layout(location = 4) out float vPointSize;

void main() {
    vec4 viewPos = ubo.uView * vec4(aPos, 1.0);
    vec4 clip    = ubo.uProj * viewPos;
    gl_Position  = clip;

    // quaternion (w, x, y, z) -> rotation matrix
    vec4 q = normalize(aRot);
    float w = q.x, x = q.y, y = q.z, z = q.w;
    mat3 R = mat3(
        1.0 - 2.0*(y*y + z*z), 2.0*(x*y - w*z),     2.0*(x*z + w*y),
        2.0*(x*y + w*z),       1.0 - 2.0*(x*x + z*z), 2.0*(y*z - w*x),
        2.0*(x*z - w*y),       2.0*(y*z + w*x),     1.0 - 2.0*(x*x + y*y)
    );

    // 3D covariance: Sigma = R S^2 R^T
    vec3 s = max(aScale, vec3(1e-4));
    mat3 S = mat3(s.x, 0.0, 0.0,  0.0, s.y, 0.0,  0.0, 0.0, s.z);
    mat3 Sigma = R * S * S * transpose(R);

    // camera-space covariance: SigmaCam = W Sigma W^T  (W = view rotation)
    mat3 W = mat3(ubo.uView[0].xyz, ubo.uView[1].xyz, ubo.uView[2].xyz);
    mat3 SigmaCam = W * Sigma * transpose(W);

    // projection Jacobian J (2x3) and 2D covariance = J SigmaCam J^T
    float fx = ubo.uProj[0][0] * ubo.uResolution.x * 0.5;
    float fy = ubo.uProj[1][1] * ubo.uResolution.y * 0.5;
    float zc = max(-viewPos.z, 1e-4);
    float xc = viewPos.x, yc = viewPos.y;
    vec3 j0 = vec3(fx / zc, 0.0, -fx * xc / (zc * zc));
    vec3 j1 = vec3(0.0, fy / zc, -fy * yc / (zc * zc));

    mat2 cov;
    cov[0][0] = dot(j0, SigmaCam * j0);
    cov[0][1] = dot(j0, SigmaCam * j1);
    cov[1][0] = cov[0][1];
    cov[1][1] = dot(j1, SigmaCam * j1);
    cov[0][0] += 0.3;   // anti-aliasing / stability epsilon
    cov[1][1] += 0.3;

    float det = cov[0][0] * cov[1][1] - cov[0][1] * cov[1][0];
    vCovInv = mat2(cov[1][1], -cov[0][1], -cov[1][0], cov[0][0]) / det;

    // point size = 3 sigma per side (Gaussian falls to exp(-4.5)=0.011 at the edge)
    float trace = cov[0][0] + cov[1][1];
    float lam   = 0.5 * (trace + sqrt(max(trace * trace - 4.0 * det, 0.0)));
    float ps    = 6.0 * sqrt(max(lam, 0.0));
    gl_PointSize = clamp(ps, 1.0, 512.0);
    vPointSize   = gl_PointSize;

    vColor = aColor;
    vAlpha = aAlpha;
}
