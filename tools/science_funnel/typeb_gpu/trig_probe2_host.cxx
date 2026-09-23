/* trig_probe2_host.cxx -- the adoption gate for ucrt_math.c: bit-for-bit
 * equality of the reconstruction against the CRT the reference links, at
 * (a) the trig_probe's 125 sampled evaluations (25 inputs x 5 functions,
 * trig_inputs.txt) and (b) dense sweeps over the walk's domain classes.
 * The gate is 100%: any differing bit fails the adoption.
 * Trailer Agent: GLM 5.3.
 */
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cmath>
#include <vector>

extern "C" {
double ucrt_sin(double);
double ucrt_cos(double);
double ucrt_atan2(double, double);
double ucrt_acos(double);
double ucrt_hypot(double, double);
}

typedef union { uint64_t u; double d; } bits;
static uint64_t B(double x) { bits b; b.d = x; return b.u; }

static int fails[5] = { 0, 0, 0, 0, 0 };
static long long total[5] = { 0, 0, 0, 0, 0 };
static const char* fn[5] = { "sin", "cos", "atan2", "acos", "hypot" };

static void chk(int f, double args[], double got, double want, long long idx) {
    total[f]++;
    if (B(got) != B(want)) {
        fails[f]++;
        if (fails[f] <= 8) {
            printf("FAIL %-5s #%lld args", fn[f], idx);
            for (int i = 0; i < (f == 2 || f == 4 ? 2 : 1); ++i) printf(" %.17g", args[i]);
            printf("  got %.17g (%016llx) want %.17g (%016llx)\n",
                   got, B(got), want, B(want));
        }
    }
}

int main(int argc, char** argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int dense = (argc > 1 && 0 == strcmp(argv[1], "dense"));
    /* (a) the 125 trig_probe points (25 inputs from trig_inputs.txt) */
    static const double T[25] = {
        0.0, -0.20640000000000000, 0.76460100000000009, -0.55238900000000002,
        0.06578700000000004, -0.071399000000000004, -0.94038900000000003,
        0.49178700000000009, -0.21051299999999995, 0.3714869999999999,
        -0.90293861457026869, 0.83791351673274095, 0.0, 1e-08, 0.0001,
        0.20513105922366801, 0.38607655499999999, 1.0, 2.0, 3.1415926535897931,
        -0.90000000000000002, 0.90000000000000002, 0.001, 0.25, 0.5 };
    long long idx = 0;
    for (int i = 0; i < 25; ++i) {
        double x = T[i];
        double a1[1] = { x };
        chk(0, a1, ucrt_sin(x), sin(x), idx);
        chk(1, a1, ucrt_cos(x), cos(x), idx);
        double y = x * 0.37 - 0.11;
        double a2[2] = { y, x };
        chk(2, a2, ucrt_atan2(y, x), atan2(y, x), idx);
        double c = x - floor(x) * 0.5;
        if (c > 1.0) c = 1.0 / c;
        if (c < -1.0) c = -1.0 / c;
        double a3[1] = { c };
        chk(3, a3, ucrt_acos(c), acos(c), idx);
        double h1 = fabs(x) + 0.0625, h2 = 0.449 - fabs(x) * 0.21;
        double a4[2] = { h1, h2 };
        chk(4, a4, ucrt_hypot(h1, h2), hypot(h1, h2), idx);
        ++idx;
    }
    if (!dense) {
        printf("125-point probe: sin %lld/%lld cos %lld/%lld atan2 %lld/%lld acos %lld/%lld hypot %lld/%lld\n",
               total[0]-fails[0], total[0], total[1]-fails[1], total[1],
               total[2]-fails[2], total[2], total[3]-fails[3], total[3],
               total[4]-fails[4], total[4]);
        return 1;
    }
    /* (b) dense sweeps over the walk's domain classes */
    unsigned long long st = 0x243F6A8885A308D3ULL;
    auto rnd = [&]() {
        st ^= st << 13; st ^= st >> 7; st ^= st << 17;
        return (double)(st >> 11) * (1.0 / 9007199254740992.0);
    };
    printf("[sc4]\n");
    /* sin/cos: the walk's angles ~[-4,4], plus reductions to 1e6, tiny args */
    for (int i = 0; i < 4000; ++i) {
        double x = (rnd() * 2 - 1) * 4.0;
        double a[1] = { x };
        chk(0, a, ucrt_sin(x), sin(x), i);
        chk(1, a, ucrt_cos(x), cos(x), i);
    }
    printf("[sc1e6]\n");
    for (int i = 0; i < 1000; ++i) {
        double x = (rnd() * 2 - 1) * 1e6;
        double a[1] = { x };
        chk(0, a, ucrt_sin(x), sin(x), i);
        chk(1, a, ucrt_cos(x), cos(x), i);
    }
    for (int i = 0; i < 500; ++i) {
        double x = (rnd() * 2 - 1) * 1e-3;
        double a[1] = { x };
        chk(0, a, ucrt_sin(x), sin(x), i);
        chk(1, a, ucrt_cos(x), cos(x), i);
    }
    printf("[edge]\n");
    /* boundary neighborhoods: pi/4, 2e7, 2^-13, 2^-27, pi/2 multiples */
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
            chk(0, a, ucrt_sin(x.d), sin(x.d), i * 64 + j);
            chk(1, a, ucrt_cos(x.d), cos(x.d), i * 64 + j);
        }
    }
    printf("[atan2grid]\n");
    /* atan2: the IK grid class dx,dy in [-1,1] plus signs and extremes */
    for (int i = 0; i < 200; ++i) {
        for (int j = 0; j < 200; ++j) {
            double dy = (i + 0.5) / 100.0 - 1.0;
            double dx = (j + 0.5) / 100.0 - 1.0;
            double a[2] = { dy, dx };
            chk(2, a, ucrt_atan2(dy, dx), atan2(dy, dx), i * 200 + j);
        }
    }
    printf("[atan2pow]\n");
    for (int i = 0; i < 400; ++i) {
        double s1 = rnd() < 0.5 ? -1.0 : 1.0, s2 = rnd() < 0.5 ? -1.0 : 1.0;
        double dy = s1 * pow(10.0, rnd() * 8 - 4);
        double dx = s2 * pow(10.0, rnd() * 8 - 4);
        double a[2] = { dy, dx };
        chk(2, a, ucrt_atan2(dy, dx), atan2(dy, dx), i);
    }
    printf("[acos]\n");
    /* acos: [-1,1] dense near +-1 and uniform */
    for (int i = 0; i < 500; ++i) {
        double x = 2.0 * rnd() - 1.0;
        double a[1] = { x };
        chk(3, a, ucrt_acos(x), acos(x), i);
    }
    for (int i = 0; i < 500; ++i) {
        double s = rnd() < 0.5 ? -1.0 : 1.0;
        double x = 1.0 - s * pow(10.0, -rnd() * 15);
        if (x > 1.0) x = 1.0;
        if (x < -1.0) x = -1.0;
        double a[1] = { x };
        chk(3, a, ucrt_acos(x), acos(x), i);
    }
    printf("[hypot]\n");
    /* hypot: the walk class [0,1] plus big/small scales */
    for (int i = 0; i < 1000; ++i) {
        double a = rnd() * 2 - 1, b = rnd() * 2 - 1;
        double q[2] = { a, b };
        chk(4, q, ucrt_hypot(a, b), hypot(a, b), i);
    }
    printf("[hypotscale]\n");
    for (int i = 0; i < 200; ++i) {
        double s = pow(10.0, rnd() * 600 - 300);
        double a = rnd() * 2 * s, b = rnd() * 2 * s;
        double q[2] = { a, b };
        chk(4, q, ucrt_hypot(a, b), hypot(a, b), i);
    }
    long long T0 = 0, TT = 0;
    for (int f = 0; f < 5; ++f) { T0 += total[f] - fails[f]; TT += total[f]; }
    printf("dense sweep: %lld/%lld bit-identical\n", T0, TT);
    for (int f = 0; f < 5; ++f)
        printf("  %-5s %lld/%lld%s\n", fn[f], total[f] - fails[f], total[f],
               fails[f] ? "  FAIL" : "");
    return 1;
}
