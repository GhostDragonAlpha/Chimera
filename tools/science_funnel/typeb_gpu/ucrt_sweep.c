/* ucrt_sweep.c -- closeout-8: hunt the tick-74 2-ulp class. Compare the
   ucrt_math reconstruction against the MSVC CRT over the walk's fore-angle
   argument ranges, fine grid, report every mismatch with exact bits.
   Trailer: Agent: GLM 5.3. */
#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include <string.h>
#include "ucrt_math.c"

int main(void) {
    long long ns = 0, nc = 0, bad_s = 0, bad_c = 0;
    double lo = -3.3, hi = 0.2;
    long long N = 60000000;
    for (long long i = 0; i <= N; ++i) {
        double x = lo + (hi - lo) * (double)i / (double)N;
        double rs = ucrt_sin(x), rs2 = sin(x);
        double rc = ucrt_cos(x), rc2 = cos(x);
        if (rs != rs2) { if (bad_s < 5) printf("SIN x=%.17g (bits %016llx) rec=%.17g crt=%.17g\n", x, (unsigned long long)b_of(x), rs, rs2); bad_s++; }
        if (rc != rc2) { if (bad_c < 5) printf("COS x=%.17g (bits %016llx) rec=%.17g crt=%.17g\n", x, (unsigned long long)b_of(x), rc, rc2); bad_c++; }
        ns++; nc++;
    }
    printf("sin: %lld cases, %lld mismatches; cos: %lld cases, %lld mismatches\n", ns, bad_s, nc, bad_c);
    return 0;
}
