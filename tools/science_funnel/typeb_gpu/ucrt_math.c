/* ucrt_math.c -- bit-exact reconstruction of the MSVC UCRT double sin, cos,
 * atan2, acos, hypot on the FMA3-live path (__use_fma3_lib=3 on this machine),
 * transcribed literally from the extracted libucrt.lib objects:
 *   ucrt_objs/sin_mt.disasm  cos_mt.disasm  rempiby2_fma3.disasm
 *   acos_fma.disasm  atan2_fma.disasm  hypot_mt.disasm
 * Tables: ucrt_math_tables.h (generated verbatim from the .obj .rdata).
 * vfmadd/vfnmadd/vfmsub -> fma() (correctly-rounded fused multiply-add);
 * all other arithmetic is non-contracted on the host (/fp:precise) and runs
 * under -fmad=false on the device.
 * Trailer Agent: GLM 5.3.
 */
#include <math.h>
#include <stdint.h>
#include <string.h>
#include "ucrt_math_tables.h"

typedef union { uint64_t u; double d; } ubits;
static inline uint64_t b_of(double x) { ubits b; b.d = x; return b.u; }
static inline double d_of(uint64_t u) { ubits b; b.u = u; return b.d; }

#define U_PI_4        0x3FE921FB54442D18ULL
#define U_2NEG13      0x3F20000000000000ULL
#define U_2NEG27      0x3E40000000000000ULL
#define U_ONE_SIXTH   0x3FC5555555555555ULL
#define U_ONE_HALF    0x3FE0000000000000ULL
#define U_ONE         0x3FF0000000000000ULL
#define U_SMALL_CW    0x411E848000000000ULL   /* 5e5   */
#define U_SMALL_BDL   0x417312D000000000ULL   /* 2e7   */
#define U_INF_MASK    0x7FF0000000000000ULL
#define U_ABS_MASK    0x7FFFFFFFFFFFFFFFULL
#define U_SIGNBIT     0x8000000000000000ULL
#define U_L2BYPY      0x3FE45F306DC9C883ULL
#define U_2TO32       0x41F0000000000000ULL

#define C_PI2_LEAD 0x3FF921FB54442D18ULL
#define C_PI2_P1   0x3FF921FB50000000ULL
#define C_PI2_P2   0x3E5110B460000000ULL
#define C_PI2_P3   0x3C91A62633145C06ULL
#define C_FFF800   0xFFFFFFFFF8000000ULL
#define C_XC1      0x3FF921FB54442D18ULL
#define C_XC2      0x3C91A62633145C00ULL
#define C_XC3      0x397B839A252049C0ULL
#define C_SIGMA    0x4338000000000000ULL

static inline double fmsub(double a, double b, double c) { return -fma(-a, b, c); }

/* 64x64 -> 128 multiply (MSVC x64 has no __int128) */
static void mul64(uint64_t a, uint64_t b, uint64_t *lo, uint64_t *hi) {
    uint64_t a0 = a & 0xFFFFFFFFULL, a1 = a >> 32;
    uint64_t b0 = b & 0xFFFFFFFFULL, b1 = b >> 32;
    uint64_t p00 = a0 * b0, p01 = a0 * b1, p10 = a1 * b0, p11 = a1 * b1;
    uint64_t mid = (p00 >> 32) + (p01 & 0xFFFFFFFFULL) + (p10 & 0xFFFFFFFFULL);
    *lo = (p00 & 0xFFFFFFFFULL) | (mid << 32);
    *hi = p11 + (p01 >> 32) + (p10 >> 32) + (mid >> 32);
}

/* ── __remainder_piby2_fma3_bdl  (2e7 > |x| >= pi/4) ────────────────────── */
static void u_rem_bdl(double x, double *r_out, double *rt_out, int *n_out) {
    const double twobypi = d_of(U_L2BYPY);
    const double sigma = d_of(C_SIGMA);
    const double xc1 = d_of(C_XC1), xc2 = d_of(C_XC2), xc3 = d_of(C_XC3);
    double nd = fma(x, twobypi, sigma) - sigma;   /* round to nearest int */
    int n = (int)nd;                              /* vcvttpd2dq           */
    double w = fma(-nd, xc1, x);                  /* x - n*xc1, fused     */
    double t3 = nd * xc2;
    double z = xc2 * nd - t3;                     /* +0.0 (dead in asm)   */
    double u = w - t3;
    double u2 = (w - u) - t3;
    w = fma(-nd, xc2, w);
    u = (u - w) + u2;
    u = u - z;
    *r_out = w;
    *rt_out = fma(-nd, xc3, u);
    *n_out = n & 3;
}

/* ── __remainder_piby2_fma3  (|x| >= 2e7) ───────────────────────────────── */
static void u_rem_gen(double x, double *r_out, double *rt_out, int *n_out) {
    uint64_t xb = b_of(x);
    int64_t e = (int64_t)(xb >> 52) - 1023;
    uint64_t m = (xb << 12) >> 12;
    m |= (1ULL << 52);
    int64_t tb = (e >> 3) - 0x86;
    tb = -tb;                          /* byte offset into the digit table */
    const unsigned char *T = u_l2bypi + tb;
    uint64_t q0, q1, q2;
    memcpy(&q0, T, 8); memcpy(&q1, T + 8, 8); memcpy(&q2, T + 16, 8);
    uint64_t r8, rh, lo1, hi1;
    mul64(q0, m, &r8, &rh);
    mul64(q1, m, &lo1, &hi1);
    uint64_t s1 = lo1 + rh;
    uint64_t cry = (s1 < lo1) ? 1u : 0u;
    uint64_t r10 = hi1 + cry;
    uint64_t r9 = s1;
    uint64_t p2lo, p2hi;
    mul64(q2, m, &p2lo, &p2hi);
    r10 = r10 + p2lo;                  /* carry intentionally dropped */
    int sh = 0x36 - (int)(e & 7);
    uint64_t nq = r10 >> sh;
    int half = (int)((r10 >> (sh - 1)) & 1ULL);
    uint64_t signflip = 0;
    if (half) { r10 = ~r10; r9 = ~r9; r8 = ~r8; signflip = U_SIGNBIT; }
    nq = nq + (uint64_t)half;
    int n = (int)(nq & 3);
    int sh2 = (int)(e & 7) + 10;
    r10 = (r10 << sh2) >> sh2;
    int64_t r11 = (int64_t)sh2 - 64;
    int pos;
    if (r10 == 0) {
        r10 = r9; r9 = r8; r8 = 0;
        pos = 63; { uint64_t v = r10; int p = -1; while (v) { p++; v >>= 1; } pos = p; }
        r11 -= 64;
    } else {
        pos = 63; { uint64_t v = r10; int p = -1; while (v) { p++; v >>= 1; } pos = p; }
    }
    r11 += pos;
    int c2 = pos - 0x34;
    uint64_t lead, tail;
    if (c2 < 0) {
        int k = -c2, k2 = 64 - k;
        uint64_t old9 = r9;
        lead = (r10 << k) | (old9 >> k2);
        tail = (r9 << k) | (r8 >> k2);
    } else if (c2 == 0) {
        lead = r10; tail = r9;
    } else {
        int k = c2, k2 = 64 - k;
        uint64_t old10 = r10;
        lead = old10 >> k;
        tail = (r9 >> k) | (old10 << k2);
    }
    int64_t e2 = r11 + 1023;
    lead &= ~(1ULL << 52);
    lead |= signflip;
    lead |= ((uint64_t)e2 << 52);
    double lead_d = d_of(lead);
    int pos9 = 63; { uint64_t v = tail; int p = -1; while (v) { p++; v >>= 1; } pos9 = p; }
    int k9 = 64 - pos9;
    tail = (tail << k9) >> 12;
    int64_t rc = k9 + 0x34;
    int64_t e3 = e2 - rc;
    tail |= signflip;
    tail |= ((uint64_t)e3 << 52);
    double tail_d = d_of(tail);

    const double p2lead = d_of(C_PI2_LEAD);
    const double part1 = d_of(C_PI2_P1), part2 = d_of(C_PI2_P2), part3 = d_of(C_PI2_P3);
    double h = d_of(lead & C_FFF800);
    double t = lead_d - h;
    double a = lead_d * p2lead;
    double b = h * part1;
    b = b - a;
    b = fma(t, part1, b);
    b = fma(h, part2, b);
    b = fma(t, part2, b);
    double c3 = tail_d * p2lead;
    c3 = fma(lead_d, part3, c3);
    b = b + c3;
    *r_out = a + b;
    *rt_out = (a - *r_out) + b;
    *n_out = n;
}

/* ── sin (sin_mt.obj, Lsin_fma3) ────────────────────────────────────────── */
double ucrt_sin(double x) {
    uint64_t ux = b_of(x);
    uint64_t axb = ux & U_ABS_MASK;
    double ax = d_of(axb);
    if (ax < d_of(U_PI_4)) {
        if (ax >= d_of(U_2NEG13)) {           /* Lsin_fma3_calc_sin_for_absx_lt_piby4 */
            double x2 = x * x;
            double p = d_of(u_sinarr[5]);
            p = fma(p, x2, d_of(u_sinarr[4]));
            p = fma(p, x2, d_of(u_sinarr[3]));
            p = fma(p, x2, d_of(u_sinarr[2]));
            p = fma(p, x2, d_of(u_sinarr[1]));
            p = fma(p, x2, d_of(u_sinarr[0]));
            double xx2 = x * x2;
            return fma(xx2, p, x);
        }
        if (ax >= d_of(U_2NEG27)) {           /* Lsin_fma3_compute_x_xxx_0_1666 */
            double x3 = (x * x) * x;
            return fma(-x3, d_of(U_ONE_SIXTH), x);
        }
        return x;                             /* the xmm1 stores are dead */
    }
    if (ax >= U_INF_MASK) return x + x;       /* _sin_special */
    double xr = ax;
    double r, rt; int n;
    if (ax >= d_of(U_SMALL_BDL)) u_rem_gen(xr, &r, &rt, &n);
    else                          u_rem_bdl(xr, &r, &rt, &n);
    double result;
    double x2 = r * r;
    if (n & 1) {                              /* Lsin_fma3_calc_cos */
        double h = x2 * d_of(U_ONE_HALF);
        double t1 = 1.0 - h;
        double t2 = 1.0 - t1;
        t2 = t2 - h;
        double p = d_of(u_cosarr[5]);
        p = fma(p, x2, d_of(u_cosarr[4]));
        p = fma(p, x2, d_of(u_cosarr[3]));
        p = fma(p, x2, d_of(u_cosarr[2]));
        p = fma(p, x2, d_of(u_cosarr[1]));
        p = fma(p, x2, d_of(u_cosarr[0]));
        double x4 = x2 * x2;
        t2 = fma(-r, rt, t2);                 /* vfnmadd231sd xmm2,xmm0,xmm1 */
        p = fma(p, x4, t2);                   /* vfmadd213sd  xmm5,xmm1,xmm2 */
        result = p + t1;
    } else {                                  /* Lsin_fma3_calc_sin */
        double p = d_of(u_sinarr[5]);
        p = fma(p, x2, d_of(u_sinarr[4]));
        p = fma(p, x2, d_of(u_sinarr[3]));
        p = fma(p, x2, d_of(u_sinarr[2]));
        p = fma(p, x2, d_of(u_sinarr[1]));
        double xx2 = r * x2;
        double px = xx2 * p;
        double h = rt * d_of(U_ONE_HALF);
        double t = h - px;
        t = x2 * t;
        t = t - rt;
        t = fma(-xx2, d_of(u_sinarr[0]), t);
        result = r - t;
    }
    uint64_t sb = ((n & 2) ? U_SIGNBIT : 0ULL) ^ (ux & U_SIGNBIT);
    return d_of(b_of(result) ^ sb);
}

/* ── cos (cos_mt.obj, L_cos_fma3) ───────────────────────────────────────── */
double ucrt_cos(double x) {
    uint64_t ux = b_of(x);
    uint64_t axb = ux & U_ABS_MASK;
    double ax = d_of(axb);
    if (ax < d_of(U_PI_4)) {
        if (ax >= d_of(U_2NEG13)) {           /* Lcompute_cos_piby4 */
            double x2 = x * x;
            double p = d_of(u_cosarr[5]);
            p = fma(p, x2, d_of(u_cosarr[4]));
            p = fma(p, x2, d_of(u_cosarr[3]));
            p = fma(p, x2, d_of(u_cosarr[2]));
            p = fma(p, x2, d_of(u_cosarr[1]));
            p = fma(p, x2, d_of(u_cosarr[0]));      /* vfmadd213sd .. cosarray+0 */
            p = fma(p, x2, -d_of(U_ONE_HALF));/* vfmsub213sd .. L_one_half */
            p = fma(p, x2, 1.0);              /* vfmadd213sd .. L_one      */
            return p;
        }
        if (ax >= d_of(U_2NEG27)) {           /* Lcompute_1_xx_5 */
            double h = x * d_of(U_ONE_HALF);
            return fma(-x, h, 1.0);           /* vfnmadd213sd xmm0,xmm1,L_one */
        }
        (void)d_of(U_2TO32);                  /* the x+2^32 store is dead */
        return 1.0;
    }
    if (ax >= U_INF_MASK) return x + x;       /* _cos_special */
    double xr = ax;
    double r, rt; int n;
    if (ax >= d_of(U_SMALL_BDL)) u_rem_gen(xr, &r, &rt, &n);
    else                          u_rem_bdl(xr, &r, &rt, &n);
    double result;
    double x2 = r * r;
    if (n & 1) {                              /* Lsin_piby4_compute (cos: odd) */
        double p = d_of(u_sinarr[4]);
        p = fma(x2, d_of(u_sinarr[5]), p);
        p = fma(p, x2, d_of(u_sinarr[3]));
        p = fma(p, x2, d_of(u_sinarr[2]));
        p = fma(p, x2, d_of(u_sinarr[1]));
        double xx2 = r * x2;
        double px = xx2 * p;
        double h = rt * d_of(U_ONE_HALF);
        double t = h - px;
        t = x2 * t;
        t = t - rt;
        t = fma(-xx2, d_of(u_sinarr[0]), t);
        result = r - t;
    } else {                                  /* Lcos_piby4_compute (cos: even) */
        double h = x2 * d_of(U_ONE_HALF);
        double t1 = 1.0 - h;
        double t2 = 1.0 - t1;
        t2 = t2 - h;
        double q = d_of(u_cosarr[4]);
        q = fma(x2, d_of(u_cosarr[5]), q);
        q = fma(q, x2, d_of(u_cosarr[3]));
        q = fma(q, x2, d_of(u_cosarr[2]));
        q = fma(q, x2, d_of(u_cosarr[1]));
        q = fma(q, x2, d_of(u_cosarr[0]));
        double x4 = x2 * x2;
        t2 = fma(-r, rt, t2);                 /* vfnmadd231sd xmm2,xmm0,xmm1 */
        q = fma(q, x4, t2);                   /* vfmadd213sd  xmm5,xmm1,xmm2 */
        result = q + t1;
    }
    /* the disasm's sign rule (Lcos_exit: add eax,1; and eax,2; cmovne
       L_signbit): flip when ((n+1)&2)!=0 — n==1,2 mod 4 — and NEVER x's
       own sign (cos is even; the old line XORed ux's signbit, flipping
       every negative input and missing cos(pi) */
    uint64_t sb = (((n + 1) & 2) != 0) ? U_SIGNBIT : 0ULL;
    return d_of(b_of(result) ^ sb);
}

/* ── hypot (hypot_mt.obj, _hypot) ───────────────────────────────────────── */
double ucrt_hypot(double x, double y) {
    uint64_t xb = b_of(x) & U_ABS_MASK;       /* r8  = |x| bits */
    uint64_t yb = b_of(y) & U_ABS_MASK;       /* rdx = |y| bits */
    uint64_t xe = xb >> 52, ye = yb >> 52;
    const uint64_t absmask = 0x7FFFFFFFFFFFFFFFULL;
    if (xe == 0x7FFULL) {                     /* x inf/nan */
        if ((xb & 0x000FFFFFFFFFFFFFULL) == 0 && (yb & absmask) == 0) {
            /* x inf, y 0 -> set_statfp; +inf */
            return d_of(0x7FF0000000000000ULL);
        }
        if (ye == 0x7FF && (yb & 0x000FFFFFFFFFFFFFULL) == 0) {
            return d_of(0x7FF0000000000000ULL);  /* both inf */
        }
        double a = d_of(xb), b = d_of(yb);
        return a * a + b * b;                 /* inf/nan propagation */
    }
    if (ye == 0x7FF) {                        /* y inf/nan */
        if ((yb & 0x000FFFFFFFFFFFFFULL) == 0 && (xb & absmask) == 0) {
            return d_of(0x7FF0000000000000ULL);
        }
        double a = d_of(xb), b = d_of(yb);
        return a * a + b * b;
    }
    double ax = d_of(xb), ay = d_of(yb);
    if (xb == 0) return ay;                   /* test r8 / movaps xmm3 */
    if (yb == 0) return ax;                   /* test rdx / movaps xmm2 */
    int64_t diff = (int64_t)xe - (int64_t)ye + 0x36;
    if ((uint64_t)diff > 0x6CULL) {           /* > 108: gap too big */
        return ax + ay;                       /* addsd xmm2,xmm3 (max-ish) */
    }
    double a = ax, b = ay, scale = 1.0;
    int r10 = 0;                              /* the rescale exponent */
    if (xe > 0x5F3ULL || ye > 0x5F3ULL) {
        /* scale down: add 0xDA80000000000000 to both bit patterns */
        a = d_of(b_of(ax) + 0xDA80000000000000ULL);
        b = d_of(b_of(ay) + 0xDA80000000000000ULL);
        r10 = 0x258;                          /* +600 */
    } else if (xe < 0x20BULL || ye < 0x20BULL) {
        /* scale up: subnormals get the +0x259 bump, normals +0x258 */
        (void)d_of(0xA590000000000000ULL);
        if (xe == 0) a = d_of(b_of(ax) + 0x2590000000000000ULL);
        else         a = d_of(b_of(ax) + 0x2580000000000000ULL);
        if (ye == 0) b = d_of(b_of(ay) + 0x2590000000000000ULL);
        else         b = d_of(b_of(ay) + 0x2580000000000000ULL);
        r10 = -600;
    }
    double r = sqrt(a * a + b * b);           /* mulsd,mulsd,addsd,sqrtsd */
    if (r10 != 0) {
        r = d_of(((uint64_t)(int64_t)(r10 + 0x3FF)) << 52) * r;
    }
    if (r > d_of(0x7FEFFFFFFFFFFFFFULL)) return d_of(0x7FF0000000000000ULL);
    return r;
}

/* ── acos (acos_fma.obj) ────────────────────────────────────────────────── */
double ucrt_acos(double x) {
    uint64_t ux = b_of(x);
    uint64_t axb = ux & 0x7FFFFFFFFFFFFFFFULL;
    uint64_t xe = (ux >> 52) & 0x7FF;
    if (axb > 0x7FF0000000000000ULL) return x + x;         /* NaN */
    if (xe < 0x3C7) return 1.5707963267948966;             /* |x| < 2^-56: pi/2 */
    if (xe >= 0x3FF) {                                     /* |x| >= 1 */
        if (x == 1.0) return 0.0;
        if (x == -1.0) return 3.141592653589793;
        return x + x;                                      /* domain error NaN */
    }
    double axv = d_of(axb);                   /* xmm6 */
    double r, s = 0.0;
    if (xe >= 0x3FE) {                        /* |x| >= 0.5 */
        r = (1.0 - axv) * d_of(0x3FE0000000000000ULL);
        s = sqrt(r);
    } else {
        r = axv * axv;
    }
    /* p (numer) chain */
    double p = 4.8290192034478698e-05;        /* 0x3F0951665D321061 */
    p = fma(p, r, 0.0010924269723507467);     /* 0x3F51E5F887A62135 */
    p = fmsub(p, r, 0.054998980923568586);    /* 0x3FAC28D390C29690 */
    p = fma(p, r, d_of(0x3FD1A2BEC1B7EF59ULL)); /* the term the first
                                                   transcription DROPPED (the
                                                   disasm's 0164 vfmadd213; the
                                                   measured ~5.6e-5 acos class) */
    p = fmsub(p, r, 0.44501721686763562);     /* 0x3FDC7B297E269EAC */
    p = fma(p, r, 0.22748583555693502);       /* 0x3FCD1E4180029834 */
    double pnum = p * r;
    /* q (denom) chain */
    double q = 0.10586942208720437;           /* 0x3FBB1A422982CE76 */
    q = fmsub(q, r, 0.94363913703249269);     /* 0x3FEE324AB418F78D */
    q = fma(q, r, 2.7656885915727099);        /* 0x40062021571DCCFC */
    q = fmsub(q, r, 3.2843150572095867);      /* 0x400A4646F903CDEA */
    q = fma(q, r, 1.3649150133416104);        /* 0x3FF5D6B12001F228 */
    double pq = pnum / q;                     /* xmm7 */
    /* RESULT PATHS — branch order per the disasm: the |x|<0.5 test (jb 01B3)
       comes FIRST and its path uses SIGNED x throughout (xmm4=x at 025F:
       t1 = x - t, NOT |x| - t — classes (a)+(b) of the dense-sweep fails);
       the sign split below applies only when |x| >= 0.5. */
    if (xe < 0x3FE) {                         /* |x| < 0.5 (disasm 0246 path) */
        double t = fma(-x, pq, 6.123233995736766e-17);  /* -(x*pq)+tail */
        double t1 = x - t;                    /* SIGNED (was axv — class (a)) */
        return 1.5707963267948966 - t1;
    }
    if (ux >= 0x8000000000000000ULL) {        /* x < 0, |x|>=0.5 (01BE path) */
        double t0 = fmsub(pq, axv, 6.123233995736766e-17); /* pq*ax - tail */
        double t1 = t0 + s;
        double t2 = t1 + t1;
        return 3.141592653589793 - t2;
    }
    /* x >= 0, |x| >= 0.5 (01F0 path) */
    double sh = d_of(b_of(s) & 0xFFFFFFFF00000000ULL);
    double a = sh + s;
    double bnum = fma(-sh, sh, r);
    double bq = bnum / a;
    double b2 = bq + bq;
    double b3 = fma(pq, s + s, b2);           /* 022E vfmadd231sd xmm3,xmm7,xmm2:
                                                 b3 = b2 + pq*(2s) — was mistranscribed
                                                 as fma(b2,pq,s)=b2*pq+s (class (c);
                                                 proven by acos(0.5): got exactly 1.5
                                                 want pi/3) */
    double res = b3 + (sh + sh);
    return res;
}

/* ── atan2 (atan2_fma.obj) ──────────────────────────────────────────────── */
static void u_atan_ratio(double big, double sml, int flip,
                         uint64_t xb_raw, uint64_t yb_raw,
                         double *base_out, double *val_out) {
    /* returns (base, val): result = base + val with the sign/quad fixups
       applied by the caller exactly as the asm does. */
    double base = 0.0, val;
    double rq = sml / big;                    /* vdivsd xmm5,xmm9,xmm7 with
                                                 xmm9=min(blend), xmm7=max(blend):
                                                 rq = smaller/larger <= 1 (the
                                                 2026-09-23 fix — was big/sml,
                                                 overflowing u_atan_lead via
                                                 k=rq*256+0.5; proven at the
                                                 blend chain 0393-03C6) */
    if (rq > 0.0625) {                        /* comisd 3fb0.../jbe    */
        int k = (int)trunc(fma(rq, 256.0, 0.5));   /* fma + cvttsd2si   */
        int idx = k - 16;
        base = d_of(u_atan_lead[idx]);        /* xmm6 = lead           */
        double kd = (double)k;                /* vcvtsi2sd             */
        double rnew = kd * 0.00390625;        /* xmm5 = k/256          */
        /* split sml's exponent so max/sml is computed without cancellation */
        uint64_t mb = b_of(sml);
        int64_t me = (int64_t)((mb >> 52) & 0x7FF);
        int64_t r8 = 1023 - me;
        int64_t h1 = r8 / 2;                  /* cdq;sub edx;sar,1     */
        int64_t h2 = r8 - h1;
        double s1 = d_of(((uint64_t)(h1 + 1023)) << 52);
        double s2 = d_of(((uint64_t)(h2 + 1023)) << 52);
        double mins1 = sml * s1;              /* xmm0 = min*scale1     */
        double mins2 = mins1 * s2;            /* xmm4 = min scaled     */
        double maxs1 = big * s1;              /* xmm0 = max*scale1    */
        double maxs2 = maxs1 * s2;            /* xmm3 = max scaled     */
        /* the head-split runs on MAXS2 (047E: rax=bits(maxs2)&~0x7FFFFF) and
           the residual numerator is mins2 - rnew*maxs2 (0492/049B: min -
           mhead*rnew - rnew*mrest) — the first transcription had the two
           roles swapped (num = max - rnew*min), computing O(1) garbage where
           the true residual is O(1/256^2); numerically verified: for
           wy=0.1729,wx=0.7646 the correct num/den ~ -4.5e-4 */
        double mhead = d_of(b_of(maxs2) & 0xFFFFFFFFF8000000ULL);
        double mrest = maxs2 - mhead;
        double num = fma(-mhead, rnew, mins2);
        num = fma(-rnew, mrest, num);
        double den = fma(mins2, rnew, maxs2);  /* 04AC vfmadd231sd xmm1,xmm3,xmm5:
                                                  den = maxs2 + mins2*rnew (the
                                                  transcription had the two roles
                                                  swapped: maxs2*rnew+mins2 — the
                                                  measured ~6e-4 class) */
        double frac = num / den;
        val = frac + d_of(u_atan_tail[idx]);
        double x2 = frac * frac;
        double poly = fma(-x2, 0.19999918038989142, 0.33333333333224097);
        poly = poly * x2;
        val = fma(-frac, poly, val);
    } else if (1e-8 > rq) {                   /* r < 1e-8: atan = r    */
        base = 0.0;
        val = rq;
    } else {                                  /* direct poly on r      */
        base = 0.0;
        double x2 = rq * rq;
        /* the same role-swap as the k-branch (5th instance of the class,
           proven empirically by the tiny-x fails: got == big/sml exactly):
           num = sml - rq*big (big's head split), corr = num / big */
        double rh = d_of(b_of(rq) & 0xFFFFFFFF00000000ULL);
        double bh = d_of(b_of(big) & 0xFFFFFFFF00000000ULL);
        double brest = big - bh;
        double rrest = rq - rh;
        double num = fma(-bh, rh, sml);
        num = fma(-rh, brest, num);
        num = fma(-big, rrest, num);
        double poly = 0.090029810285449791;
        poly = fma(poly, x2, 0.11110736283514526);
        poly = fma(poly, x2, 0.1428571356180717);
        poly = fma(poly, x2, 0.19999999999393223);
        poly = fma(poly, x2, 0.33333333333333171);
        double x3 = x2 * rq;
        double corr = num / big;
        corr = fma(-x3, poly, corr);
        val = corr + rq;
    }
    /* the quadrant/sign fixups (057D..05C6) */
    if (flip) {
        base = 1.5707963267948966 - base;
        val = 6.123233995736766e-17 - val;
    }
    if ((int64_t)xb_raw < 0) {
        base = 3.1415926218032837 - base;
        val = 3.1786509547056392e-08 - val;
    }
    *base_out = base;
    *val_out = val;
}

double ucrt_atan2(double y, double x) {
    uint64_t yb_raw = b_of(y), xb_raw = b_of(x);
    uint64_t xabs = xb_raw & U_ABS_MASK, yabs = yb_raw & U_ABS_MASK;
    uint64_t xexp = xabs >> 52, yexp = yabs >> 52;
    if (xabs > U_INF_MASK) return y + y;      /* x NaN */
    if (yabs > U_INF_MASK) return x + x;      /* y NaN */
    if (yabs == 0) {                          /* y == +-0 */
        if ((int64_t)xb_raw >= 0) return y;
        return (yb_raw & U_SIGNBIT) ? -3.141592653589793 : 3.141592653589793;
    }
    if (xabs == 0) {                          /* x == +-0: +-pi/2 by y sign */
        return (yb_raw & U_SIGNBIT) ? -1.5707963267948966 : 1.5707963267948966;
    }
    int64_t edi;
    if ((int64_t)xexp < 0x3FD && (int64_t)yexp < 0x3FD) {
        /* both below 0.25: the exponent-bump measure (012D..01D5) */
        uint64_t rcx, rdi;
        if (xb_raw & U_SIGNBIT) rcx = xb_raw + 0x4000000000000000ULL;
        else {
            double v0 = d_of(xb_raw | 0x4010000000000000ULL);
            rcx = b_of(v0 + (-4.0));
        }
        if (yb_raw & U_SIGNBIT) rdi = yb_raw + 0x4000000000000000ULL;
        else {
            double v0 = d_of(yb_raw | 0x4010000000000000ULL);
            rdi = b_of(v0 + (-4.0));
        }
        edi = (int64_t)((rdi >> 52) & 0x7FF) - (int64_t)((rcx >> 52) & 0x7FF);
    } else {
        edi = (int64_t)yexp - (int64_t)xexp;
    }
    if (edi > 0x38) {                         /* y >> x by > 56: +-pi/2 */
        return (yb_raw & U_SIGNBIT) ? -1.5707963267948966 : 1.5707963267948966;
    }
    if (edi >= -28) {
        if (yabs == 0x7FF0000000000000ULL && xabs == 0x7FF0000000000000ULL) {
            if ((int64_t)yb_raw < 0)
                return (int64_t)xb_raw < 0 ? -2.3561944901923448 : -0.78539816339744828;
            return (int64_t)xb_raw < 0 ? 2.3561944901923448 : 0.78539816339744828;
        }
        {
            double ax = d_of(xabs), ay = d_of(yabs);
            int flip = (ay > ax) ? 1 : 0;
            double big = flip ? ay : ax;
            double sml = flip ? ax : ay;
            double base, val;
            u_atan_ratio(big, sml, flip, xb_raw, yb_raw, &base, &val);
            double final_ = base + val;
            return (yb_raw & U_SIGNBIT) ? -final_ : final_;
        }
    }
    /* edi < -28 */
    if ((int64_t)xb_raw < 0) {
        if (edi < -56) {
            return (yb_raw & U_SIGNBIT) ? -3.141592653589793 : 3.141592653589793;
        }
        if (yabs == 0x7FF0000000000000ULL && xabs == 0x7FF0000000000000ULL) {
            if ((int64_t)yb_raw < 0)
                return (int64_t)xb_raw < 0 ? -2.3561944901923448 : -0.78539816339744828;
            return (int64_t)xb_raw < 0 ? 2.3561944901923448 : 0.78539816339744828;
        }
        {
            double ax = d_of(xabs), ay = d_of(yabs);
            int flip = (ay > ax) ? 1 : 0;
            double big = flip ? ay : ax;
            double sml = flip ? ax : ay;
            double base, val;
            u_atan_ratio(big, sml, flip, xb_raw, yb_raw, &base, &val);
            double final_ = base + val;
            return (yb_raw & U_SIGNBIT) ? -final_ : final_;
        }
    }
    /* edi < -28, x >= 0 */
    if (edi < -1074) return (yb_raw & U_SIGNBIT) ? -0.0 : 0.0;
    if (edi >= -1022) return y / x;           /* direct signed division */
    {                                          /* edi in [-1074,-1022): denorm */
        double t = d_of(0x4630000000000000ULL) * y / x;
        uint64_t qb = b_of(t);
        uint64_t r8 = qb & 0x8000000000000000ULL;
        uint64_t rdx = qb & 0x7FFFFFFFFFFFFFFFULL;
        uint64_t rcx = (rdx >> 52);
        if (rcx > 100) {
            rdx &= 0x800FFFFFFFFFFFFFULL;
            rcx -= 100;
            rcx = (rcx << 52) | rdx;
        } else {
            rdx &= 0x801FFFFFFFFFFFFFULL;
            rdx |= 0x0010000000000000ULL;
            int64_t eax = 101 - (int64_t)rcx;
            if (eax > 54) {
                rcx = 0;
            } else {
                uint64_t sh = (uint64_t)(100 - eax);
                uint64_t t2v = rdx >> sh;
                uint64_t lowbit = t2v & 1;
                rcx = (t2v >> 1) + lowbit;
            }
        }
        return d_of(r8 | rcx);
    }
}
