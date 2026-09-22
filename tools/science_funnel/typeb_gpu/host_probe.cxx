// host_probe.cxx -- run the TRANSLATED device functions (walker_kernels.cuh)
// on the host CPU against the real model arrays to iterate translation
// defects in seconds instead of GPU rebuild cycles.
// Build: g++ -O2 -I host_shim -I . host_probe.cxx -o host_probe
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#define __device__
#define __global__
struct Dim3 { unsigned x, y, z; };
static Dim3 blockIdx = {0, 0, 0}, blockDim = {1, 1, 1}, threadIdx = {0, 0, 0};
#include "walker_kernels.cuh"

static std::vector<double> readdbl(const char* p) {
    std::vector<double> v; std::ifstream f(p); double x;
    while (f >> x) v.push_back(x);
    return v;
}
static std::vector<int> readint(const char* p) {
    std::vector<int> v; std::ifstream f(p); long x;
    while (f >> x) v.push_back((int)x);
    return v;
}

int main() {
    auto mdl = readdbl("host_shim/mdl.txt");
    auto mdi = readint("host_shim/mdi.txt");
    auto cst = readdbl("host_shim/cst.txt");
    auto csti = readint("host_shim/csti.txt");
    auto q = readdbl("host_shim/q.txt");
    auto v = readdbl("host_shim/v.txt");
    printf("loaded mdl=%zu mdi=%zu cst=%zu csti=%zu q=%zu v=%zu\n",
           mdl.size(), mdi.size(), cst.size(), csti.size(), q.size(), v.size());

    // fk_eval's workspace (the kernel allocates these as locals)
    static double M[324], gv[18], bv[18], fr[224], frd[224], frdd[224];
    static double axw[54], axpiv[54], axdir[54], ptp[24], ptJ[216];
    static double ptcop[12], ptbias[12];
    double pot = fk_eval(q.data(), v.data(), mdl.data(), mdi.data(), cst.data(),
                         M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ,
                         ptcop, ptbias);
    printf("fk_eval pot = %.12g\n", pot);
    // M symmetry + diagonal
    double asym = 0.0; int asym_i = -1, asym_j = -1;
    double dmin = 1e300;
    for (int i = 0; i < 18; ++i) {
        if (M[i * 18 + i] < dmin) dmin = M[i * 18 + i];
        for (int j = 0; j < 18; ++j) {
            double a = fabs(M[i * 18 + j] - M[j * 18 + i]);
            if (a > asym) { asym = a; asym_i = i; asym_j = j; }
        }
    }
    printf("M: max asym = %.6g at (%d,%d); min diag = %.6g\n", asym, asym_i, asym_j, dmin);
    for (int i = 0; i < 18; ++i)
        printf("  M[%2d][%2d]=%13.6g  gv=%13.6g  bv=%13.6g\n", i, i, M[i*18+i], gv[i], bv[i]);
    static double inv[324];
    int r = inverse_spd18(M, inv);
    printf("inverse_spd18 -> %d (0 = FAILED)\n", r);
    if (r == 0) {
        // run the Cholesky by hand to find the first failing pivot
        double l[324]; for (int i2 = 0; i2 < 324; ++i2) l[i2] = 0.0;
        for (int i2 = 0; i2 < 18; ++i2)
            for (int j = 0; j <= i2; ++j) {
                double t = M[i2 * 18 + j];
                if (fabs(t - M[j * 18 + i2]) > 1e-12) { printf("asym first at (%d,%d)\n", i2, j); goto done; }
                if (std::isnan(t)) { printf("nan at (%d,%d)\n", i2, j); goto done; }
                for (int k = 0; k < j; ++k) t -= l[i2 * 18 + k] * l[j * 18 + k];
                if (i2 == j) {
                    if (!(t > 0.0)) { printf("pivot fail at diag %d: %.6g\n", i2, t); goto done; }
                    l[i2 * 18 + j] = sqrt(t);
                } else l[i2 * 18 + j] = t / l[j * 18 + j];
            }
        printf("cholesky completed??\n");
    }
done:
    // ---- advance() end-to-end: the freefall step (tau=0, live=0, contact=0)
    static double fre[18], srq[18], srv[18];
    static double qa[18], va[18], qb[18], vb[18], qc[18], vc[18], qd[18], vd[18];
    static double qe[18], ve[18], we[18], sq[576], sh[16], work[18];
    static int sdep[16], scl[16], advc[1], rca[1];
    static double oq[18], ov[18], ow[18], tau[18];
    double h = cst[2] * 0.25;
    for (int i = 0; i < 18; ++i) { work[i] = 0.0; tau[i] = 0.0; }
    advc[0] = 0; rca[0] = 0;
    double v4_before = v[4], v3_before = v[3];
    advance(q.data(), v.data(), work, tau, h, mdl.data(), cst.data(),
            M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias,
            inv, fre, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we,
            sq, sh, sdep, scl, advc, rca, oq, ov, ow,
            mdi.data(), csti.data());
    printf("advance: rc=%d adv_calls=%d h=%.6g\n", rca[0], advc[0], h);
    printf("  v[3] %.9g -> %.9g (dv=%.6g)\n", v3_before, ov[3], ov[3] - v3_before);
    printf("  v[4] %.9g -> %.9g (dv=%.6g; expect ~%.6g = -g*h)\n",
           v4_before, ov[4], ov[4] - v4_before, -9.80665 * h);
    printf("  q[4] %.9g -> %.9g\n", q[4], oq[4]);
    // ---- rate() directly: does the solve itself drop acc[4]?
    {
        static double M2[324], gv2[18], bv2[18], fr2[224], frd2[224], frdd2[224];
        static double axw2[54], axpiv2[54], axdir2[54], ptp2[24], ptJ2[216];
        static double ptcop2[12], ptbias2[12], inv2[324], fre2[18], rq2[18], rv2[18];
        int live0[4] = {0, 0, 0, 0};
        int plane0[4] = {0, 0, 0, 0};
        double tau0[18]; for (int i = 0; i < 18; ++i) tau0[i] = 0.0;
        long long rcs = rate(q.data(), v.data(), tau0, live0, plane0, mdl.data(), cst.data(),
                             M2, gv2, bv2, fr2, frd2, frdd2, axw2, axpiv2, axdir2, ptp2, ptJ2,
                             ptcop2, ptbias2, inv2, fre2, rq2, rv2, mdi.data(), csti.data());
    printf("rate: rc=%lld free[4]=%.6g gv2[4]=%.6g bv2[4]=%.6g rv2[4]=%.6g rv2[3]=%.6g\n",
           rcs, fre2[4], gv2[4], bv2[4], rv2[4], rv2[3]);
        printf("  inv[4*18+4]=%.6g inv[3*18+4]=%.6g\n", inv2[4 * 18 + 4], inv2[3 * 18 + 4]);
    }
    // ---- free_step directly: isolated RK4 (live=0, contact=0, tau=0)
    {
        static double fs_q1[18], fs_v1[18], fs_w1[18], fs_work[18], fs_tau[18];
        static double fs_inv[324], fs_fre[18], fs_srq[18], fs_srv[18];
        static double fs_qa[18], fs_va[18], fs_qb[18], fs_vb[18], fs_qc[18], fs_vc[18];
        static double fs_qd[18], fs_vd[18], fs_qe[18], fs_ve[18], fs_we[18];
        for (int i = 0; i < 18; ++i) { fs_work[i] = 0.0; fs_tau[i] = 0.0; }
        int live0[4] = {0, 0, 0, 0};
        // recompute inv from the fresh fk_eval M (already in M)
        inverse_spd18(M, fs_inv);
        long long fs_rc = free_step(q.data(), v.data(), fs_work, fs_tau, live0, h,
                                    mdl.data(), cst.data(), M, gv, bv, fr, frd, frdd,
                                    axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias,
                                    fs_inv, fs_fre, fs_srq, fs_srv,
                                    fs_qa, fs_va, fs_qb, fs_vb, fs_qc, fs_vc,
                                    fs_qd, fs_vd, fs_q1, fs_v1, fs_w1,
                                    mdi.data(), csti.data());
        printf("free_step: rc=%lld v1[4]=%.9g (v0[4]=%.9g) v1[3]=%.9g q1[4]=%.9g\n",
               fs_rc, fs_v1[4], v[4], fs_v1[3], fs_q1[4]);
        printf("  k1: qa[4]=%.6g va[4]=%.6g | k2: qb-state[4]=%.6g brq? | stage arrays sane check\n",
               fs_qa[4], fs_va[4], fs_qb[4]);
    }
    return 0;
}
