// rate_probe.cxx -- call the kernels' rate() and free_step() directly on the
// defaults pose (freefall config) and print the accelerations, to isolate
// which layer breaks the exact weightless solve. Trailer Agent: GLM 5.3.
#include <cstdio>
#include <cmath>
#include <cstring>
#define __device__
#define __global__
struct Dim3 { unsigned x, y, z; };
static Dim3 blockIdx = {0, 0, 0}, blockDim = {1, 1, 1}, threadIdx = {0, 0, 0};
#include "walker_kernels.cuh"

static double mdl[900]; static int mdi[232];
static double cst[30]; static int csti[20];
static double q[18], v[18], tau[18];
static int live[4], plane[4];

static double M[324], gv[18], bv[18], fr[224], frd[224], frdd[224];
static double axw[54], axpiv[54], axdir[54], ptp[24], ptJ[216], ptcop[12], ptbias[12];
static double inv[324], free_[18], rq[18], rv[18];

int main() {
    FILE* f;
    f = fopen("host_shim/mdl.txt", "r"); for (int i = 0; i < 900; ++i) fscanf(f, "%lf", &mdl[i]); fclose(f);
    f = fopen("host_shim/mdi.txt", "r"); for (int i = 0; i < 232; ++i) fscanf(f, "%d", &mdi[i]); fclose(f);
    f = fopen("host_shim/cst.txt", "r"); for (int i = 0; i < 30; ++i) fscanf(f, "%lf", &cst[i]); fclose(f);
    f = fopen("host_shim/csti_ff.txt", "r"); for (int i = 0; i < 20; ++i) fscanf(f, "%d", &csti[i]); fclose(f);
    f = fopen("host_shim/q.txt", "r"); for (int i = 0; i < 18; ++i) fscanf(f, "%lf", &q[i]); fclose(f);
    // the DEFAULTS pose: scene defaults (hind joints 0, fore at the entry
    // pose, base y=0.345002) -- the freefall reset state
    double qd[18], vd[18];
    for (int i = 0; i < 18; ++i) { qd[i] = 0.0; vd[i] = 0.0; tau[i] = 0.0; }
    qd[4] = 0.345002;
    qd[14] = -0.9029386145702687; qd[15] = 0.837913516732741;
    qd[16] = -0.9029386145702687; qd[17] = 0.837913516732741;
    for (int i = 0; i < 4; ++i) { live[i] = 0; plane[i] = 0; }

    printf("== rate() at DEFAULTS pose (joints 0, y=0.345002, v=0, tau=0) ==\n");
    int rc = rate(qd, vd, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd,
                  axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free_, rq, rv, mdi, csti);
    printf("rate rc=%d\nM44=%.17g M66=%.17g M88=%.17g M14_15=%.17g M22=%.17g\n",
           M[4*18+4], M[6*18+6], M[8*18+8], M[14*18+15], M[2*18+2]);
    printf("acc:");
    for (int i = 0; i < 18; ++i) printf(" %.6e", free_[i]);
    printf("\n");
    printf("gv:");
    for (int i = 0; i < 18; ++i) printf(" %.6e", gv[i]);
    printf("\n");

    printf("\n== rate() at WALK-RESET (capture) pose ==\n");
    f = fopen("host_shim/v.txt", "r"); for (int i = 0; i < 18; ++i) fscanf(f, "%lf", &v[i]); fclose(f);
    for (int i = 0; i < 4; ++i) { live[i] = 0; plane[i] = 0; }
    rc = rate(q, v, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd,
              axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free_, rq, rv, mdi, csti);
    printf("rate rc=%d\nacc:", rc);
    for (int i = 0; i < 18; ++i) printf(" %.6e", free_[i]);
    printf("\n");
    return 0;
}
