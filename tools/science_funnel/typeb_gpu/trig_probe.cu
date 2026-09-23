// trig_probe.cu -- the libdevice-vs-CRT transcendental parity probe (pair 3).
// Reads the same inputs as trig_probe_host.cxx (trig_inputs.txt: first the
// exact tick-1 rot_axis angles, then a synthetic IK grid), computes
// sin/cos/atan2/acos/hypot on the DEVICE, prints %.17g + hex bits.
// Run after trig_probe_host.exe; diff the two outputs.
// Trailer Agent: GLM 5.3.
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cuda_runtime.h>

__global__ void trig_kernel(const double* in, int n, double* so, double* co,
                            double* ao, double* ac, double* hy) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;
    double x = in[i];
    so[i] = sin(x);
    co[i] = cos(x);
    // the IK-path argument shapes: atan2(wy,wx) with wx~0.3..0.5, wy~+-0.2;
    // acos(ca) with ca = 1 - eps (the near-straight chain); hypot(wx,wy).
    double wy = sin(x * 0.5) * 0.2, wx = 0.3 + cos(x) * 0.15;
    ao[i] = atan2(wy, wx);
    double ca = 1.0 - fabs(x) * 1e-6;
    if (ca > 1.0) ca = 1.0;
    if (ca < -1.0) ca = -1.0;
    ac[i] = acos(ca);
    hy[i] = hypot(wx, wy);
}

static void pbits(const char* tag, int i, double v) {
    unsigned long long b;
    memcpy(&b, &v, 8);
    printf("%s %d %.17g %016llx\n", tag, i, v, b);
}

int main() {
    FILE* f = fopen("trig_inputs.txt", "r");
    if (!f) { printf("no trig_inputs.txt\n"); return 1; }
    double buf[4096]; int n = 0;
    while (n < 4096 && fscanf(f, "%lf", &buf[n]) == 1) ++n;
    fclose(f);
    printf("N %d\n", n);
    double* din; double* so; double* co; double* ao; double* ac; double* hy;
    cudaMalloc(&din, n * 8); cudaMalloc(&so, n * 8); cudaMalloc(&co, n * 8);
    cudaMalloc(&ao, n * 8); cudaMalloc(&ac, n * 8); cudaMalloc(&hy, n * 8);
    cudaMemcpy(din, buf, n * 8, cudaMemcpyHostToDevice);
    trig_kernel<<<(n + 127) / 128, 128>>>(din, n, so, co, ao, ac, hy);
    double* h = (double*)malloc(n * 8);
    cudaMemcpy(h, so, n * 8, cudaMemcpyDeviceToHost);
    for (int i = 0; i < n; ++i) pbits("SIN", i, h[i]);
    cudaMemcpy(h, co, n * 8, cudaMemcpyDeviceToHost);
    for (int i = 0; i < n; ++i) pbits("COS", i, h[i]);
    cudaMemcpy(h, ao, n * 8, cudaMemcpyDeviceToHost);
    for (int i = 0; i < n; ++i) pbits("ATAN2", i, h[i]);
    cudaMemcpy(h, ac, n * 8, cudaMemcpyDeviceToHost);
    for (int i = 0; i < n; ++i) pbits("ACOS", i, h[i]);
    cudaMemcpy(h, hy, n * 8, cudaMemcpyDeviceToHost);
    for (int i = 0; i < n; ++i) pbits("HYPOT", i, h[i]);
    return 0;
}
