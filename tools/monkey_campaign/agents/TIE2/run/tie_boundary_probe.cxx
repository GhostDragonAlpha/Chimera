/* tie_boundary_probe.cxx -- TIE2 battery harness (cases 1-3, CPU leg).
   PREREG RESIDUAL TIE v2 (9376c3d8): EDGE-CLASS-SPLIT / FALSE-FEASIBILITY /
   OUTSIDE-BAND-DRIFT at the kTouch/dt_ boundary +-1 ulp.
   ZERO PHYSICS AUTHORED: this includes the FROZEN walker_kernels.cuh
   (byte-verified == git a62b286e) via the host_loop.cxx shim pattern and
   calls the FROZEN project_rows. tol_band=0.0 reproduces the pre-v2
   decision on the same frozen code (tol_band is a parameter of the frozen
   signature; max() then selects the exact pre-v2 tolerance).
   Constants come from the FROZEN host_shim/cst.txt (cst[2]=dt_, cst[4]=kTouch).
   Trailer: Agent: GLM 5.3 */
#include <cstdio>
#include <cmath>
#include <cstring>
#include <cstdlib>
#define __device__
#define __global__
struct Dim3 { unsigned x, y, z; };
static Dim3 blockIdx = {0, 0, 0}, blockDim = {1, 1, 1}, threadIdx = {0, 0, 0};
#include "walker_kernels.cuh"

static double cst[30];

struct Outcome { long long rc; double p0; double mult0; double got_after; };

static Outcome run_case(double viol, double tol_band_arg) {
    double initial[18], inv[18*18], rows[18], floors[1], p_out[18], multipliers[1];
    for (int i = 0; i < 18; ++i) initial[i] = 0.0;
    initial[0] = -viol;                    /* row_dot(rk, initial) = -viol; violation = 0 - (-viol) = +viol */
    for (int i = 0; i < 18*18; ++i) inv[i] = 0.0;
    for (int i = 0; i < 18; ++i) inv[i*18+i] = 1.0;   /* identity inverse mass matrix */
    for (int i = 0; i < 18; ++i) rows[i] = 0.0;
    rows[0] = 1.0;                          /* one unit contact row */
    floors[0] = 0.0;                        /* the measured all-zero floor (PROROW enter f0..f4=0) */
    for (int i = 0; i < 18; ++i) p_out[i] = 0.0;
    multipliers[0] = 0.0;
    Outcome o;
    o.rc = project_rows(initial, inv, rows, floors, 1, 0, p_out, multipliers, tol_band_arg);
    o.p0 = p_out[0];
    o.mult0 = multipliers[0];
    /* post-decision residual on row 0: got = row.r(initial) + row.r(chg), chg = inv*p_out = p_out (identity) */
    o.got_after = -viol + p_out[0] * (rows[0] * rows[0]);
    return o;
}

static void report(const char* name, double viol, double tb) {
    printf("CASE %s viol=%.17g\n", name, viol);
    for (int leg = 0; leg < 2; ++leg) {
        double tba = leg == 0 ? tb : 0.0;
        const char* legname = leg == 0 ? "v2 (tol_band=cst[kTouch]/cst[dt])" : "prev2 (tol_band=0.0)";
        Outcome o = run_case(viol, tba);
        double tol_print = tba > (1e-9 * (1.0 + 0.0)) ? tba : (1e-9 * (1.0 + 0.0));
        printf("  leg=[%s] rc=%lld p0=%.17g mult0=%.17g got_after=%.17g tol_eff=%.17g decision=%s repair=%s feas: viol*dt=%.17g <= kTouch(%1.17g)? %s\n",
               legname, (long long)o.rc, o.p0, o.mult0, o.got_after, tol_print,
               o.rc == 0 ? "REJECT(enum-fail)" : (o.p0 == 0.0 ? "ACCEPT-norepair(tie)" : "ACCEPT-repair"),
               o.p0 == 0.0 ? "no" : "yes",
               viol * cst[2], cst[4], (viol * cst[2] <= cst[4]) ? "YES" : "NO");
    }
}

int main() {
    FILE* f = fopen("host_shim/cst.txt", "r");
    if (!f) { printf("FATAL: host_shim/cst.txt not readable (run from the frozen typeb_gpu dir)\n"); return 2; }
    for (int i = 0; i < 30; ++i) fscanf(f, "%lf", &cst[i]);
    fclose(f);
    double dt = cst[2], ktouch = cst[4];
    double tb = ktouch / dt;   /* the frozen call sites' own expression: cst[CF_k_touch]/cst[CF_dt] */
    printf("== TIE2 boundary probe (frozen walker_kernels.cuh; frozen cst) ==\n");
    printf("FROZEN cst[2]=dt=%.17g cst[4]=kTouch=%.17g\n", dt, ktouch);
    printf("tb = kTouch/dt = %.17g\n", tb);
    printf("tb-1ulp = %.17g  tb+1ulp = %.17g\n", nextafter(tb, -1e308), nextafter(tb, 1e308));
    printf("FEASIBILITY IDENTITY: (kTouch/dt)*dt = %.17g  <= kTouch = %.17g ? %s\n",
           tb * dt, ktouch, (tb * dt <= ktouch) ? "YES" : "NO");
    printf("rel-only tol (floor=0) = %.17g\n", 1e-9 * (1.0 + 0.0));
    report("A1 tb-exact       ", tb, tb);
    report("A2 tb-minus-1ulp  ", nextafter(tb, -1e308), tb);
    report("A3 tb-plus-1ulp   ", nextafter(tb, 1e308), tb);
    report("A4 above 1e-2     ", 1e-2, tb);
    report("A5 above 1.0      ", 1.0, tb);
    report("A6 zero violation ", 0.0, tb);
    report("A7 t41 g0 residual", 6.9388939039072284e-18, tb);
    return 0;
}
