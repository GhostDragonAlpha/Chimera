// inv_probe.cxx -- run the KERNELS' inverse_spd18 + mat_vec on the replica's
// M/gv (dumped by py_fk_full.py) and compare against numpy's solve.
// Trailer Agent: GLM 5.3.
#include <cstdio>
#include <cmath>
#include <cstring>
#define __device__
#define __global__
struct Dim3 { unsigned x, y, z; };
static Dim3 blockIdx = {0, 0, 0}, blockDim = {1, 1, 1}, threadIdx = {0, 0, 0};
#include "walker_kernels.cuh"

static double M[324], gv[18], a_true[18];

int main() {
    FILE* f;
    f = fopen("host_shim/M_probe.txt", "r");
    for (int i = 0; i < 324; ++i) fscanf(f, "%lf", &M[i]);
    fclose(f);
    f = fopen("host_shim/gv_probe.txt", "r");
    for (int i = 0; i < 18; ++i) fscanf(f, "%lf", &gv[i]);
    fclose(f);
    f = fopen("host_shim/a_true.txt", "r");
    for (int i = 0; i < 18; ++i) fscanf(f, "%lf", &a_true[i]);
    fclose(f);

    double inv[324];
    int rc = inverse_spd18(M, inv);
    printf("inverse_spd18 rc=%d\n", rc);
    printf("inv row 4 (kernels): %.17g %.17g %.17g ... %.17g\n",
           inv[4*18+0], inv[4*18+1], inv[4*18+2], inv[4*18+4]);
    printf("M[4*18+4]=%.17g  1/M44=%.17g inv[4][4]=%.17g\n",
           M[4*18+4], 1.0/M[4*18+4], inv[4*18+4]);
    double acc[18];
    mat_vec(inv, gv, acc);
    printf("acc = inv*gv (kernels):");
    for (int i = 0; i < 18; ++i) printf(" %.6e", acc[i]);
    printf("\na_true (numpy)        :");
    for (int i = 0; i < 18; ++i) printf(" %.6e", a_true[i]);
    printf("\n");
    // worst row
    int worst = 0; double wd = 0;
    for (int i = 0; i < 18; ++i) { double d = fabs(acc[i]-a_true[i]); if (d > wd) { wd = d; worst = i; } }
    printf("worst row %d: kernels %.17g vs true %.17g\n", worst, acc[worst], a_true[worst]);
    // check inverse quality directly: inv*M should be I
    double worstI = 0; int wi = 0, wj = 0;
    for (int i = 0; i < 18; ++i)
        for (int j = 0; j < 18; ++j) {
            double s = 0;
            for (int k = 0; k < 18; ++k) s += inv[i*18+k] * M[k*18+j];
            double err = fabs(s - (i == j ? 1.0 : 0.0));
            if (err > worstI) { worstI = err; wi = i; wj = j; }
        }
    printf("worst |inv*M - I| = %.3e at (%d,%d)\n", worstI, wi, wj);
    return 0;
}
