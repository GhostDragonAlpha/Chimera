/* ucrt_probe3.c -- closeout-8: the EXACT argument chain of the tick-74
   fore_ik_at call (the bits from the IKMID drill line), ucrt vs CRT.
   Trailer: Agent: GLM 5.3. */
#include <stdio.h>
#include <math.h>
#include "ucrt_math.c"

int main(void) {
    double dx, dy, th1, ex, ey, beta;
    if (sscanf("-0.24455983362531949", "%lf", &dx) != 1) return 1;
    if (sscanf("-0.092092214423816196", "%lf", &dy) != 1) return 1;
    if (sscanf("-2.7814537567622919", "%lf", &th1) != 1) return 1;
    if (sscanf("-0.12757884801571134", "%lf", &ex) != 1) return 1;
    if (sscanf("-0.04804168655178441", "%lf", &ey) != 1) return 1;
    if (sscanf("-1.3413908497442089", "%lf", &beta) != 1) return 1;

    double a1r = ucrt_atan2(dy, dx), a1c = atan2(dy, dx);
    printf("atan2(dy,dx): rec=%.17g crt=%.17g %s\n", a1r, a1c, a1r == a1c ? "MATCH" : "DIFF");
    double cr = ucrt_cos(th1), cc = cos(th1);
    double sr = ucrt_sin(th1), sc = sin(th1);
    printf("cos(th1):     rec=%.17g crt=%.17g %s\n", cr, cc, cr == cc ? "MATCH" : "DIFF");
    printf("sin(th1):     rec=%.17g crt=%.17g %s\n", sr, sc, sr == sc ? "MATCH" : "DIFF");
    double L1 = 0.125;
    double ex2r = dx - L1 * cr, ex2c = dx - L1 * cc;
    double ey2r = dy - L1 * sr, ey2c = dy - L1 * sc;
    printf("ex: rec=%.17g crt=%.17g %s\n", ex2r, ex2c, ex2r == ex2c ? "MATCH" : "DIFF");
    printf("ey: rec=%.17g crt=%.17g %s\n", ey2r, ey2c, ey2r == ey2c ? "MATCH" : "DIFF");
    double a2r = ucrt_atan2(ey2r, ex2r), a2c = atan2(ey2c, ex2c);
    printf("atan2(ey,ex): rec=%.17g crt=%.17g %s\n", a2r, a2c, a2r == a2c ? "MATCH" : "DIFF");
    double q2r = a2r - (-1.2106574299673953) - beta;
    double q2c = a2c - (-1.2106574299673953) - beta;
    printf("q2: rec=%.17g crt=%.17g %s\n", q2r, q2c, q2r == q2c ? "MATCH" : "DIFF");
    return 0;
}
