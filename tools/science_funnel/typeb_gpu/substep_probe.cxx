// host_loop.cxx -- drive the translated tick kernels on the host, E=1,
// freefall config; find the first refusal/freeze tick and its rc.
#include <cstdio>
#include <cmath>
#include <cstring>
#include <cstdlib>
#define __device__
#define __global__
struct Dim3 { unsigned x, y, z; };
static Dim3 blockIdx = {0, 0, 0}, blockDim = {1, 1, 1}, threadIdx = {0, 0, 0};
#include "probe_kernels.cuh"

static double mdl[900]; static int mdi[232];
static double cst[30]; static int csti[20];
static double q0a[18], v0a[18]; static int t0a[2];
static double store_floor[12];
static double a_q[18], a_v[18], a_work[18], a_lt[18], a_bat[12], a_batp[1];
static double a_phi[2]; static int a_touch[2], a_cap[1], a_set[1], a_ikb[2];
static double a_pawt[6], a_pawy[2], a_swingf[6], a_swingt[6];
static double a_ft[2], a_fst[2], a_fcy[2];
static int a_fmo[2], a_fen[2], a_fcv[2], a_fdp[2], a_fcl[2], a_frp[2], a_ftd[2];
static int a_hmo[2]; static double a_ht[2], a_hfrom[6], a_hto[6], a_hpy[2], a_hap[2], a_hmp[2];
static int a_hbr[2], a_hheld[2]; static long long a_hlf[2], a_hlt[2];
static int a_hfi[2], a_htds[2]; static double a_hxo[2];
static int a_hl[1], a_cmdlive[1], a_cmdfires[1], a_advc[1], a_ref[1], a_refc[1], a_col[1], a_rc[1];
static double a_cmdvx[1]; static long long a_cft[1], a_ticks[1];
static double rb[6]; static int rbi[6];

int main() {
    FILE* f; int E = 1;
    f = fopen("host_shim/mdl.txt", "r"); for (int i = 0; i < 900; ++i) fscanf(f, "%lf", &mdl[i]); fclose(f);
    f = fopen("host_shim/mdi.txt", "r"); for (int i = 0; i < 232; ++i) fscanf(f, "%d", &mdi[i]); fclose(f);
    f = fopen("host_shim/cst.txt", "r"); for (int i = 0; i < 30; ++i) fscanf(f, "%lf", &cst[i]); fclose(f);
    f = fopen("host_shim/csti_nom.txt", "r"); for (int i = 0; i < 20; ++i) fscanf(f, "%d", &csti[i]); fclose(f);
    if (getenv("HL_NOCONTACT")) csti[1] = 0;
    if (getenv("HL_NOPOWER")) csti[2] = 0;
    if (getenv("HL_NOGAIT")) csti[3] = 0;
    if (getenv("HL_SETTLE")) csti[0] = atoi(getenv("HL_SETTLE"));
    f = fopen("host_shim/q.txt", "r"); for (int i = 0; i < 18; ++i) fscanf(f, "%lf", &q0a[i]); fclose(f);
    f = fopen("host_shim/v.txt", "r"); for (int i = 0; i < 18; ++i) fscanf(f, "%lf", &v0a[i]); fclose(f);
    f = fopen("host_shim/store.txt", "r"); for (int i = 0; i < 12; ++i) fscanf(f, "%lf", &store_floor[i]); fclose(f);
    f = fopen("host_shim/touch0.txt", "r"); t0a[0] = fgetc(f) - 48; t0a[1] = fgetc(f) - 48; fclose(f);
    double phi_l0 = 0.0, phi_r0 = 0.5; (void)phi_l0; (void)phi_r0; int settle_total = 60; double store_post = 1.0;
    reset_kernel(q0a, v0a, t0a, phi_l0, phi_r0, settle_total, store_floor, store_post,
                 a_q, a_v, a_work, a_lt, a_bat, a_batp, a_phi, a_touch, a_cap, a_set, a_ikb,
                 a_pawt, a_pawy, a_swingf, a_swingt, a_ft, a_fst, a_fcy, a_fmo, a_fen, a_fcv,
                 a_fdp, a_fcl, a_frp, a_ftd, a_hmo, a_ht, a_hfrom, a_hto, a_hpy, a_hap, a_hmp,
                 a_hbr, a_hheld, a_hlf, a_hlt, a_hfi, a_htds, a_hxo, a_hl, a_cmdvx, a_cmdlive,
                 a_cft, a_cmdfires, a_ticks, a_advc, a_ref, a_refc, a_col);
    printf("reset: q4=%.9f rc_uninit\n", a_q[4]);
    for (int t = 1; t <= 100; ++t) {
        tick_plan_kernel(mdl, mdi, cst, csti, a_q, a_v, a_work, a_lt, a_bat, a_batp,
            a_phi, a_touch, a_cap, a_set, a_ikb, a_pawt, a_pawy, a_swingf, a_swingt,
            a_ft, a_fst, a_fcy, a_fmo, a_fen, a_fcv, a_fdp, a_fcl, a_frp, a_ftd,
            a_hmo, a_ht, a_hfrom, a_hto, a_hpy, a_hap, a_hmp, a_hbr, a_hheld, a_hlf,
            a_hlt, a_hfi, a_htds, a_hxo, a_hl, a_cmdvx, a_cmdlive, a_cft, a_cmdfires,
            a_ticks, a_advc, a_ref, a_refc, a_col, rb, rbi, a_rc);
        tick_integ_kernel(mdl, mdi, cst, csti, a_q, a_v, a_work, a_lt, a_bat, a_batp,
            a_phi, a_touch, a_cap, a_set, a_ikb, a_pawt, a_pawy, a_swingf, a_swingt,
            a_ft, a_fst, a_fcy, a_fmo, a_fen, a_fcv, a_fdp, a_fcl, a_frp, a_ftd,
            a_hmo, a_ht, a_hfrom, a_hto, a_hpy, a_hap, a_hmp, a_hbr, a_hheld, a_hlf,
            a_hlt, a_hfi, a_htds, a_hxo, a_hl, a_cmdvx, a_cmdlive, a_cft, a_cmdfires,
            a_ticks, a_advc, a_ref, a_refc, a_col, rb, rbi, a_rc);
        tick_post_kernel(mdl, mdi, cst, csti, a_q, a_v, a_work, a_lt, a_bat, a_batp,
            a_phi, a_touch, a_cap, a_set, a_ikb, a_pawt, a_pawy, a_swingf, a_swingt,
            a_ft, a_fst, a_fcy, a_fmo, a_fen, a_fcv, a_fdp, a_fcl, a_frp, a_ftd,
            a_hmo, a_ht, a_hfrom, a_hto, a_hpy, a_hap, a_hmp, a_hbr, a_hheld, a_hlf,
            a_hlt, a_hfi, a_htds, a_hxo, a_hl, a_cmdvx, a_cmdlive, a_cft, a_cmdfires,
            a_ticks, a_advc, a_ref, a_refc, a_col, rb, rbi, a_rc);
        if (t <= 12 || a_rc[0] != 0 || a_ref[0] != 0 || t % 20 == 0)
            printf("tick %3d: y=%.9f vx=%.6f rc=%d adv=%d refused=%d ticks=%lld\n",
                   t, a_q[4], a_v[3], a_rc[0], a_advc[0], a_ref[0], (long long)a_ticks[0]);
        if (getenv("HL_FULL")) {
            printf("FULL t=%d", t);
            for (int i = 0; i < 18; ++i) printf(" q%d=%.17g", i, a_q[i]);
            for (int i = 0; i < 18; ++i) printf(" v%d=%.17g", i, a_v[i]);
            printf("\n");
        }
        if (a_ref[0] != 0) break;
    }
    return 0;
}
