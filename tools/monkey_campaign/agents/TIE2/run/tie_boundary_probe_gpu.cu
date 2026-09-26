/* tie_boundary_probe_gpu.cu -- TIE2 battery, CASE 1 GPU leg (QUEUED-BEHIND-BROKER).
   The SAME registered cases as tie_boundary_probe.cxx, executed on the DEVICE
   against the FROZEN walker_kernels.cuh (compiled by nvcc, the DLL's own
   compilation path, UCRT_MATH_DEVICE included). Zero physics authored.
   Build (build_gpu_probe.cmd mirrors build_dll_v2.ps1's frozen flags).
   Trailer: Agent: GLM 5.3 */
#include <cstdio>
#include <cmath>

static void run_case_on_device(double viol, double tol_band, long long* rc_out, double* p0_out, double* mult_out, double* got_out);

#include "walker_kernels.cuh"

__global__ void probe_kernel(double viol, double tol_band, long long* rc_out, double* p0_out, double* mult_out, double* got_out) {
    // only thread 0 of 1 block runs the registered cases
    double initial[18], inv[18*18], rows[18], floors[1], p_out[18], multipliers[1];
    for (int i = 0; i < 18; ++i) initial[i] = 0.0;
    initial[0] = -viol;
    for (int i = 0; i < 18*18; ++i) inv[i] = 0.0;
    for (int i = 0; i < 18; ++i) inv[i*18+i] = 1.0;
    for (int i = 0; i < 18; ++i) rows[i] = 0.0;
    rows[0] = 1.0;
    floors[0] = 0.0;
    for (int i = 0; i < 18; ++i) p_out[i] = 0.0;
    multipliers[0] = 0.0;
    long long rc = project_rows(initial, inv, rows, floors, 1, 0, p_out, multipliers, tol_band);
    *rc_out = rc;
    *p0_out = p_out[0];
    *mult_out = multipliers[0];
    *got_out = -viol + p_out[0] * (rows[0] * rows[0]);
}

static void run_case_on_device(double viol, double tol_band, long long* rc_out, double* p0_out, double* mult_out, double* got_out) {
    long long* d_rc; double *d_p0, *d_mult, *d_got;
    cudaMalloc((void**)&d_rc, sizeof(long long));
    cudaMalloc((void**)&d_p0, sizeof(double));
    cudaMalloc((void**)&d_mult, sizeof(double));
    cudaMalloc((void**)&d_got, sizeof(double));
    probe_kernel<<<1, 1>>>(viol, tol_band, d_rc, d_p0, d_mult, d_got);
    cudaDeviceSynchronize();
    cudaMemcpy(rc_out, d_rc, sizeof(long long), cudaMemcpyDeviceToHost);
    cudaMemcpy(p0_out, d_p0, sizeof(double), cudaMemcpyDeviceToHost);
    cudaMemcpy(mult_out, d_mult, sizeof(double), cudaMemcpyDeviceToHost);
    cudaMemcpy(got_out, d_got, sizeof(double), cudaMemcpyDeviceToHost);
    cudaFree(d_rc); cudaFree(d_p0); cudaFree(d_mult); cudaFree(d_got);
}

int main() {
    // the frozen constants, read from the frozen shim file on the host side
    FILE* f = fopen("host_shim/cst.txt", "r");
    if (!f) { printf("FATAL: host_shim/cst.txt not readable\n"); return 2; }
    double cst[30];
    for (int i = 0; i < 30; ++i) fscanf(f, "%lf", &cst[i]);
    fclose(f);
    double dt = cst[2], ktouch = cst[4];
    double tb = ktouch / dt;
    printf("== TIE2 boundary probe, GPU leg (frozen walker_kernels.cuh under nvcc) ==\n");
    printf("tb = %.17g  tb-1ulp = %.17g  tb+1ulp = %.17g\n", tb, nextafter(tb, -1e308), nextafter(tb, 1e308));
    struct { const char* name; double viol; } cases[] = {
        {"A1 tb-exact       ", tb},
        {"A2 tb-minus-1ulp  ", nextafter(tb, -1e308)},
        {"A3 tb-plus-1ulp   ", nextafter(tb, 1e308)},
        {"A4 above 1e-2     ", 1e-2},
        {"A5 above 1.0      ", 1.0},
        {"A6 zero violation ", 0.0},
        {"A7 t41 g0 residual", 6.9388939039072284e-18},
    };
    for (int c = 0; c < 7; ++c) {
        for (int leg = 0; leg < 2; ++leg) {
            double tba = leg == 0 ? tb : 0.0;
            long long rc; double p0, mult, got;
            run_case_on_device(cases[c].viol, tba, &rc, &p0, &mult, &got);
            printf("CASE %s viol=%.17g leg=[%s] rc=%lld p0=%.17g mult0=%.17g got_after=%.17g decision=%s\n",
                   cases[c].name, cases[c].viol, leg == 0 ? "v2" : "prev2",
                   (long long)rc, p0, mult, got,
                   rc == 0 ? "REJECT(enum-fail)" : (p0 == 0.0 ? "ACCEPT-norepair(tie)" : "ACCEPT-repair"));
        }
    }
    return 0;
}
