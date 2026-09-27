// parity_gate_host.cxx -- ONT-W02 frozen reference-math equivalence gate.
//
// FROZEN IN PREREGISTRATION.md BEFORE ANY RUN (attempt 681e63e9e5d84eaa9702379faf347ac5).
//
// Demonstrates, at the card's frozen sites and WITHOUT tolerance relaxation
// (the gate is IEEE-754 bit equality, nothing softer), that the adopted
// reference-math implementation -- the UCRT reconstruction ucrt_math.c
// (pinned git blob efd87d67, extracted verbatim from the lane archive ref
// refs/chimera-archive-source/20260925/agent/typeb-gpu-finish-20260922) --
// is bit-equivalent to its declared reference, the MSVC UCRT (the live CRT
// this program links, the same "lib on disk as ground truth" oracle the lane
// pinned in closeout-5), at:
//   (1) the 125 frozen sites: the 25 pinned trig_inputs.txt inputs x 5
//       functions with the EXACT argument derivations of the card's original
//       probe trig_probe_host.cxx (git blob 007c6f6a);
//   (2) a dense sweep ported VERBATIM from trig_probe2_host.cxx
//       (git blob 5bfe2c46): same xorshift seed, generators, iteration counts.
//
// This is a CPU-only host leg. The on-device gate (55,517/55,517) remains a
// PRESERVED RECORD of the lane (co7_gate_out2.txt); no GPU claim is made here.
//
// The gate itself is enforced downstream by run_gate.py, which parses the
// printed gate lines (FROZEN125, DENSE, DENSE-TOTAL) and requires
// passed == total everywhere. Output lines are machine-parseable:
//   XBITS <i> <hex>                input x bit pattern (frozen125)
//   SITE <i> <FN> <oracle_hex> <recon_hex> <MATCH|DIFF>
//   FROZEN125 <passed>/<total>
//   [section markers] then DENSE <fn> <passed>/<total> lines,
//   DENSE-TOTAL <passed>/<total>
// Trailer Agent: GLM 5.3 (monkey campaign worker, ONT-W02).
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cmath>

extern "C" {
double ucrt_sin(double);
double ucrt_cos(double);
double ucrt_atan2(double, double);
double ucrt_acos(double);
double ucrt_hypot(double, double);
}

typedef union { uint64_t u; double d; } bits;
static uint64_t B(double x) { bits b; b.d = x; return b.u; }

static const char* FN[5] = { "SIN", "COS", "ATAN2", "ACOS", "HYPOT" };
static long long tot[5] = { 0, 0, 0, 0, 0 };
static long long bad[5] = { 0, 0, 0, 0, 0 };

static void fail_note(int f, const double* a, double got, double want) {
    if (bad[f] <= 8) {
        printf("DENSE-FAIL %s args", FN[f]);
        for (int i = 0; i < (f == 2 || f == 4 ? 2 : 1); ++i) printf(" %.17g", a[i]);
        printf("  got %016llx want %016llx\n", (unsigned long long)B(got),
               (unsigned long long)B(want));
    }
}

static void chk(int f, const double* a, double got, double want) {
    ++tot[f];
    if (B(got) != B(want)) { ++bad[f]; fail_note(f, a, got, want); }
}

/* ---- (1) the 125 frozen sites --------------------------------------------
 * Inputs pinned from trig_inputs.txt (25 lines); spelled exactly as the lane's
 * own embedded table in trig_probe2_host.cxx so the compiled artifact carries
 * the sites. run_gate.py cross-checks these printed XBITS against the pinned
 * trig_inputs.txt bytes.
 */
static const double T[25] = {
    0.0, -0.20640000000000000, 0.76460100000000009, -0.55238900000000002,
    0.06578700000000004, -0.071399000000000004, -0.94038900000000003,
    0.49178700000000009, -0.21051299999999995, 0.3714869999999999,
    -0.90293861457026869, 0.83791351673274095, 0.0, 1e-08, 0.0001,
    0.20513105922366801, 0.38607655499999999, 1.0, 2.0, 3.1415926535897931,
    -0.90000000000000002, 0.90000000000000002, 0.001, 0.25, 0.5 };

static void frozen125(void) {
    long long badsites = 0, total = 0;
    for (int i = 0; i < 25; ++i) {
        double x = T[i];
        printf("XBITS %d %016llx\n", i, (unsigned long long)B(x));
        double wy = sin(x * 0.5) * 0.2, wx = 0.3 + cos(x) * 0.15;   // trig_probe_host.cxx
        double ca = 1.0 - fabs(x) * 1e-6;
        if (ca > 1.0) ca = 1.0;
        if (ca < -1.0) ca = -1.0;
        struct { int f; double o; double r; double a0; double a1; } sites[5] = {
            { 0, sin(x),          ucrt_sin(x),          x,  0.0 },
            { 1, cos(x),          ucrt_cos(x),          x,  0.0 },
            { 2, atan2(wy, wx),   ucrt_atan2(wy, wx),   wy, wx  },
            { 3, acos(ca),        ucrt_acos(ca),        ca, 0.0 },
            { 4, hypot(wx, wy),   ucrt_hypot(wx, wy),   wx, wy  },
        };
        for (int s = 0; s < 5; ++s) {
            ++total;
            bool m = B(sites[s].o) == B(sites[s].r);
            if (!m) ++badsites;
            if (s == 2 || s == 4)
                printf("SITE %d %s %016llx %016llx %s ABITS %016llx %016llx\n",
                       i, FN[sites[s].f], (unsigned long long)B(sites[s].o),
                       (unsigned long long)B(sites[s].r), m ? "MATCH" : "DIFF",
                       (unsigned long long)B(sites[s].a0), (unsigned long long)B(sites[s].a1));
            else
                printf("SITE %d %s %016llx %016llx %s ABITS %016llx\n",
                       i, FN[sites[s].f], (unsigned long long)B(sites[s].o),
                       (unsigned long long)B(sites[s].r), m ? "MATCH" : "DIFF",
                       (unsigned long long)B(sites[s].a0));
        }
    }
    printf("FROZEN125 %lld/%lld\n", total - badsites, total);
}

/* ---- (2) dense sweep, ported verbatim from trig_probe2_host.cxx ---------- */
static void dense(void) {
    unsigned long long st = 0x243F6A8885A308D3ULL;
    auto rnd = [&]() {
        st ^= st << 13; st ^= st >> 7; st ^= st << 17;
        return (double)(st >> 11) * (1.0 / 9007199254740992.0);
    };
    printf("[sc4]\n");
    for (int i = 0; i < 4000; ++i) {
        double x = (rnd() * 2 - 1) * 4.0;
        double a[1] = { x };
        chk(0, a, ucrt_sin(x), sin(x));
        chk(1, a, ucrt_cos(x), cos(x));
    }
    printf("[sc1e6]\n");
    for (int i = 0; i < 1000; ++i) {
        double x = (rnd() * 2 - 1) * 1e6;
        double a[1] = { x };
        chk(0, a, ucrt_sin(x), sin(x));
        chk(1, a, ucrt_cos(x), cos(x));
    }
    for (int i = 0; i < 500; ++i) {
        double x = (rnd() * 2 - 1) * 1e-3;
        double a[1] = { x };
        chk(0, a, ucrt_sin(x), sin(x));
        chk(1, a, ucrt_cos(x), cos(x));
    }
    printf("[edge]\n");
    static const double edge[] = {
        0.78539816339744830961, 0.7853981633974483, 2.0e7, 2.0e7 * (1 + 1e-12),
        1.220703125e-4, 1.2207031249e-4, 7.450580596923828e-9, 7.45e-9,
        1.5707963267948966, 3.141592653589793, 6.283185307179586,
        0.0625, 0.06249999, 16.0 };
    int ne = (int)(sizeof(edge) / sizeof(edge[0]));
    for (int i = 0; i < ne; ++i) {
        for (int j = 0; j < 64; ++j) {
            bits x; x.u = B(edge[i]) + (j - 32);
            double a[1] = { x.d };
            chk(0, a, ucrt_sin(x.d), sin(x.d));
            chk(1, a, ucrt_cos(x.d), cos(x.d));
        }
    }
    printf("[atan2grid]\n");
    for (int i = 0; i < 200; ++i) {
        for (int j = 0; j < 200; ++j) {
            double dy = (i + 0.5) / 100.0 - 1.0;
            double dx = (j + 0.5) / 100.0 - 1.0;
            double a[2] = { dy, dx };
            chk(2, a, ucrt_atan2(dy, dx), atan2(dy, dx));
        }
    }
    printf("[atan2pow]\n");
    for (int i = 0; i < 400; ++i) {
        double s1 = rnd() < 0.5 ? -1.0 : 1.0, s2 = rnd() < 0.5 ? -1.0 : 1.0;
        double dy = s1 * pow(10.0, rnd() * 8 - 4);
        double dx = s2 * pow(10.0, rnd() * 8 - 4);
        double a[2] = { dy, dx };
        chk(2, a, ucrt_atan2(dy, dx), atan2(dy, dx));
    }
    printf("[acos]\n");
    for (int i = 0; i < 500; ++i) {
        double x = 2.0 * rnd() - 1.0;
        double a[1] = { x };
        chk(3, a, ucrt_acos(x), acos(x));
    }
    for (int i = 0; i < 500; ++i) {
        double s = rnd() < 0.5 ? -1.0 : 1.0;
        double x = 1.0 - s * pow(10.0, -rnd() * 15);
        if (x > 1.0) x = 1.0;
        if (x < -1.0) x = -1.0;
        double a[1] = { x };
        chk(3, a, ucrt_acos(x), acos(x));
    }
    printf("[hypot]\n");
    for (int i = 0; i < 1000; ++i) {
        double a = rnd() * 2 - 1, b = rnd() * 2 - 1;
        double q[2] = { a, b };
        chk(4, q, ucrt_hypot(a, b), hypot(a, b));
    }
    printf("[hypotscale]\n");
    for (int i = 0; i < 200; ++i) {
        double s = pow(10.0, rnd() * 600 - 300);
        double a = rnd() * 2 * s, b = rnd() * 2 * s;
        double q[2] = { a, b };
        chk(4, q, ucrt_hypot(a, b), hypot(a, b));
    }
    long long P = 0, TT = 0;
    for (int f = 0; f < 5; ++f) {
        printf("DENSE %s %lld/%lld%s\n", FN[f], tot[f] - bad[f], tot[f],
               bad[f] ? " FAIL" : "");
        P += tot[f] - bad[f]; TT += tot[f];
    }
    printf("DENSE-TOTAL %lld/%lld\n", P, TT);
}

int main(void) {
    frozen125();
    dense();
    return 0;
}
