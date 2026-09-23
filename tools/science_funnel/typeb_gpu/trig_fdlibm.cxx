// trig_fdlibm.cxx -- closeout-5 Target-B route (1): the fdlibm side of the
// transcendental bit-probe. Reads trig_inputs.txt, computes sin/cos/atan2/
// acos/hypot with the PORTED fdlibm (netlib sources, fd_ prefix) and prints
// the same records as trig_probe_host.cxx. The wy/wx/ca ARGUMENT SHAPES are
// computed with the CRT sin/cos exactly like trig_probe_host.cxx so the
// arguments are bit-identical on both sides and any mismatch attributes to
// the function under test alone. Gate: 125/125 (and any added points)
// bit-identical vs trig_host.txt before a kernel port may be adopted.
// Trailer Agent: GLM 5.3.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>

extern "C" double fd_sin(double);
extern "C" double fd_cos(double);
extern "C" double fd_atan2(double, double);
extern "C" double fd_acos(double);
extern "C" double fd_hypot(double, double);

static void pbits(const char* tag, int i, double v) {
    unsigned long long b;
    memcpy(&b, &v, 8);
    printf("%s %d %.17g %016llx\n", tag, i, v, b);
}

int main() {
    FILE* f = fopen("trig_inputs.txt", "r");
    if (!f) { printf("no trig_inputs.txt\n"); return 1; }
    static double buf[65536]; int n = 0;
    while (n < 65536 && fscanf(f, "%lf", &buf[n]) == 1) ++n;
    fclose(f);
    printf("N %d\n", n);
    for (int i = 0; i < n; ++i) {
        double x = buf[i];
        pbits("SIN", i, fd_sin(x));
        pbits("COS", i, fd_cos(x));
        double wy = sin(x * 0.5) * 0.2, wx = 0.3 + cos(x) * 0.15;
        pbits("ATAN2", i, fd_atan2(wy, wx));
        double ca = 1.0 - fabs(x) * 1e-6;
        if (ca > 1.0) ca = 1.0;
        if (ca < -1.0) ca = -1.0;
        pbits("ACOS", i, fd_acos(ca));
        pbits("HYPOT", i, fd_hypot(wx, wy));
    }
    return 0;
}
