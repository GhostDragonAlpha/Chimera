// trig_probe_host.cxx -- the CRT side of the libdevice-vs-CRT transcendental
// parity probe (pair 3). Same inputs, same five functions as trig_probe.cu,
// computed on the HOST with the same cl/UCRT the C++ reference uses.
// Trailer Agent: GLM 5.3.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>

static void pbits(const char* tag, int i, double v) {
    unsigned long long b;
    memcpy(&b, &v, 8);
    printf("%s %d %.17g %016llx\n", tag, i, v, b);
}

int main() {
    FILE* f = fopen("trig_inputs.txt", "r");
    if (!f) { printf("no trig_inputs.txt\n"); return 1; }
    double buf[4096]; int n = 0;
    while (n < 4096 && fscanf(f, "%lf", &buf[n]) == 1) ++n;
    fclose(f);
    printf("N %d\n", n);
    for (int i = 0; i < n; ++i) {
        double x = buf[i];
        pbits("SIN", i, sin(x));
        pbits("COS", i, cos(x));
        double wy = sin(x * 0.5) * 0.2, wx = 0.3 + cos(x) * 0.15;
        pbits("ATAN2", i, atan2(wy, wx));
        double ca = 1.0 - fabs(x) * 1e-6;
        if (ca > 1.0) ca = 1.0;
        if (ca < -1.0) ca = -1.0;
        pbits("ACOS", i, acos(ca));
        pbits("HYPOT", i, hypot(wx, wy));
    }
    return 0;
}
