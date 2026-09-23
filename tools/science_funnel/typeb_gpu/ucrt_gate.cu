// ucrt_gate.cu -- THE ON-DEVICE GATE: the proven host UCRT reconstruction
// (ucrt_math.c, 55,517/55,517 vs the CRT) compiled for the device and
// compared bit-for-bit against the HOST CRT over the same dumped case set.
// PASS = every case bit-identical (then device==host-ucrt==CRT).
// Trailer Agent: lead
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <cuda_runtime.h>

#define UCRT_MATH_DEVICE 1
#include "ucrt_math.c"

struct Case { int kind; double a0, a1; };

__global__ void gate_kernel(const Case* cs, int n, double* out) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;
    const Case& c = cs[i];
    double r = 0;
    switch (c.kind) {
        case 0: r = ucrt_sin(c.a0); break;
        case 1: r = ucrt_cos(c.a0); break;
        case 2: r = ucrt_atan2(c.a0, c.a1); break;   // (y, x) order per dump
        case 3: r = ucrt_acos(c.a0); break;
        case 4: r = ucrt_hypot(c.a0, c.a1); break;
    }
    out[i] = r;
}

typedef unsigned long long u64;
static u64 B(double d) { u64 u; memcpy(&u, &d, 8); return u; }

int main() {
    FILE* f = fopen("dense_cases.bin", "rb");
    if (!f) { printf("dense_cases.bin missing (run trig_probe2_host.exe dumpdense)\n"); return 2; }
    std::vector<Case> host;
    for (;;) {
        int k; double a0, a1;
        if (fread(&k, sizeof(int), 1, f) != 1) break;
        if (fread(&a0, sizeof(double), 1, f) != 1) break;
        if (fread(&a1, sizeof(double), 1, f) != 1) break;
        host.push_back(Case{k, a0, a1});
    }
    fclose(f);
    int n = (int)host.size();
    printf("cases: %d\n", n);

    Case* d_cs; double* d_out; std::vector<double> out(n);
    cudaMalloc(&d_cs, n * sizeof(Case)); cudaMalloc(&d_out, n * sizeof(double));
    cudaMemcpy(d_cs, host.data(), n * sizeof(Case), cudaMemcpyHostToDevice);
    gate_kernel<<<(n + 255) / 256, 256>>>(d_cs, n, d_out);
    cudaError_t e = cudaDeviceSynchronize();
    if (e != cudaSuccess) { printf("KERNEL ERROR: %s\n", cudaGetErrorString(e)); return 2; }
    cudaMemcpy(out.data(), d_out, n * sizeof(double), cudaMemcpyDeviceToHost);

    const char* fn[5] = {"sin","cos","atan2","acos","hypot"};
    long long tot[5]={0,0,0,0,0}, bad[5]={0,0,0,0,0};
    for (int i = 0; i < n; ++i) {
        const Case& cc = host[i];
        double ref;
        switch (cc.kind) {
            case 0: ref = sin(cc.a0); break;
            case 1: ref = cos(cc.a0); break;
            case 2: ref = atan2(cc.a0, cc.a1); break;
            case 3: ref = acos(cc.a0); break;
            case 4: ref = hypot(cc.a0, cc.a1); break;
        }
        tot[cc.kind]++;
        if (B(out[i]) != B(ref)) {
            bad[cc.kind]++;
            if (bad[cc.kind] <= 4)
                printf("FAIL %-5s #%d args %.17g %.17g  dev %.17g (%016llx) crt %.17g (%016llx)\n",
                       fn[cc.kind], i, cc.a0, cc.a1, out[i], B(out[i]), ref, B(ref));
        }
    }
    long long T=0, D=0;
    for (int k=0;k<5;++k){ T+=tot[k]; D+=bad[k];
        printf("  %-5s %lld/%lld%s\n", fn[k], tot[k]-bad[k], tot[k], bad[k]?" FAIL":""); }
    printf("ON-DEVICE GATE: %lld/%lld bit-identical -- %s\n", T-D, T, D?"FAIL":"PASS");
    return D ? 1 : 0;
}
