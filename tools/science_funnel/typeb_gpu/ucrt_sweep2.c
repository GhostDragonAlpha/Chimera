/* ucrt_sweep2.c -- closeout-8: atan2/acos coverage hunt over the walk's
   fore-geometry argument ranges. Trailer: Agent: GLM 5.3. */
#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include <string.h>
#include "ucrt_math.c"

int main(void) {
    long long na = 0, bad_a = 0, nc = 0, bad_c = 0;
    /* atan2 grid: the fore IK's dx,dy neighborhood */
    for (long long i = 0; i <= 2000; ++i) {
        for (long long j = 0; j <= 2000; ++j) {
            double y = -0.4 + 0.8 * (double)i / 2000.0;
            double x = -0.6 + 1.2 * (double)j / 2000.0;
            double r1 = ucrt_atan2(y, x), r2 = atan2(y, x);
            if (r1 != r2) { if (bad_a < 8) printf("ATAN2 y=%.17g x=%.17g rec=%.17g crt=%.17g\n", y, x, r1, r2); bad_a++; }
            na++;
        }
    }
    /* acos: ca over [-1,1] */
    for (long long i = 0; i <= 60000000; ++i) {
        double c = -1.0 + 2.0 * (double)i / 60000000.0;
        double r1 = ucrt_acos(c), r2 = acos(c);
        if (r1 != r2) { if (bad_c < 8) printf("ACOS c=%.17g rec=%.17g crt=%.17g\n", c, r1, r2); bad_c++; }
        nc++;
    }
    printf("atan2: %lld cases, %lld mismatches; acos: %lld cases, %lld mismatches\n", na, bad_a, nc, bad_c);
    return 0;
}
