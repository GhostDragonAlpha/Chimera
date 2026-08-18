#version 450
// N-body gravity + contact resistance compute shader.
// Ported verbatim from LightEngine/kernel.py _draw_cuda / _resist_cpu.

layout(local_size_x = 256, local_size_y = 1, local_size_z = 1) in;

layout(set = 0, binding = 0) readonly  buffer PosIn  { float pos_in[][4]; };
layout(set = 0, binding = 1) readonly  buffer VelIn  { float vel_in[][4]; };
layout(set = 0, binding = 2) writeonly buffer AccOut { float acc_out[][4]; };
layout(set = 0, binding = 3) readonly  uniform Params {
    float G;          // gravity constant
    float eps2;       // softening squared
    float rw;         // wall radius (contact repulsion)
    float rb;         // bond radius (spring attraction)
    float rc;         // cutoff radius
    float kw;         // wall stiffness
    float kb;         // bond stiffness
    float gamma_w;    // wall damping
    float dt;         // timestep
};

#define EPS 1e-8

void main() {
    uint i = gl_GlobalInvocationID.x;
    uint n = pos_in.length();
    if (i >= n) return;

    float xi = pos_in[i][0];
    float yi = pos_in[i][1];
    float zi = pos_in[i][2];
    float vxi = vel_in[i][0];
    float vyi = vel_in[i][1];
    float vzi = vel_in[i][2];

    float ax = 0.0f;
    float ay = 0.0f;
    float az = 0.0f;

    for (uint j = 0; j < n; j++) {
        if (i == j) continue;

        float dx = pos_in[j][0] - xi;
        float dy = pos_in[j][1] - yi;
        float dz = pos_in[j][2] - zi;
        float r2 = dx*dx + dy*dy + dz*dz;

        // ── Gravity (draw) ───────────────────────────────────────
        float inv_r3 = 1.0f / ((r2 + EPS) * sqrt(r2 + EPS));
        ax += G * inv_r3 * dx;
        ay += G * inv_r3 * dy;
        az += G * inv_r3 * dz;

        // ── Contact resistance (resist) ──────────────────────────
        float r = sqrt(r2);
        if (r < rc) {
            if (r < rw) {
                // Wall branch: repulsion + radial damping
                float pen = rw - r;
                float nx = dx/r, ny = dy/r, nz = dz/r;
                float v_radial = vxi*nx + vyi*ny + vzi*nz;
                ax += (kw * pen - gamma_w * v_radial) * nx;
                ay += (kw * pen - gamma_w * v_radial) * ny;
                az += (kw * pen - gamma_w * v_radial) * nz;
            } else if (r < rb) {
                // Bond branch: spring attraction toward rest length
                float stretch = r - rb;
                float nx = dx/r, ny = dy/r, nz = dz/r;
                ax += kb * stretch * nx;
                ay += kb * stretch * ny;
                az += kb * stretch * nz;
            }
        }
    }

    // ── Velocity Verlet integration ────────────────────────────
    float nvx = vxi + ax * dt;
    float nvy = vyi + ay * dt;
    float nvz = vzi + az * dt;

    acc_out[i][0] = nvx;
    acc_out[i][1] = nvy;
    acc_out[i][2] = nvz;
    acc_out[i][3] = 0.0f;
}
