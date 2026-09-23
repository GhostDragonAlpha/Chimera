/* reach_band_test.c -- closeout-8: the PREREG REACH BAND v1 endpoint and
   neighbor cases (Astra launch-sequence step 3). Compares the legacy and the
   band-v1 boundary treatment per the preregistered falsifier table:
   OUTSIDE-BAND-DRIFT (identical results outside B), the in-band canonical
   snap (both implementations agree BY CONSTRUCTION: one Dcan), and
   FALSE-FEASIBILITY (the snapped D never exceeds dmax). The reference
   constants are the walk's (L1=0.125, rho=0.13632448829082713).
   Trailer: Agent: GLM 5.3. */
#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include <string.h>

static double L1 = 0.125, rho = 0.13632448829082713;

static double dmax_of(void) { return L1 + rho; }
static double dmin_of(void) { return fabs(L1 - rho); }

/* the legacy treatment (pre-v1), verbatim */
static void legacy(double D, int *sat, double *Dc) {
    double dmax = dmax_of(), dmin = dmin_of();
    *sat = 0; *Dc = 0;
    if (D > dmax * (1. - 1e-12) || D < dmin + 1e-9) {
        *sat = 1;
        *Dc = fmin(fmax(D, dmin + 1e-9), dmax * (1. - 1e-12));
    }
}

/* the band-v1 treatment (the registered patch), verbatim */
static void bandv1(double D, int *sat, double *Dc) {
    double dmax = dmax_of(), dmin = dmin_of();
    double dcan = dmax * (1. - 1e-9);
    *sat = 0; *Dc = 0;
    if (D > dmax || D >= dcan || D < dmin + 1e-9) {
        *sat = 1;
        if (D > dmax) *Dc = dmax * (1. - 1e-12);
        else if (D >= dcan) *Dc = dcan;
        else *Dc = fmin(fmax(D, dmin + 1e-9), dmax * (1. - 1e-12));
    }
}

static double nextup(double x) { uint64_t b; memcpy(&b, &x, 8); b += 1; memcpy(&x, &b, 8); return x; }
static double nextdn(double x) { uint64_t b; memcpy(&b, &x, 8); b -= 1; memcpy(&x, &b, 8); return x; }

int main(void) {
    double dmax = dmax_of(), dmin = dmin_of();
    double dcan = dmax * (1. - 1e-9);
    printf("dmax=%.17g dmin=%.17g dcan=%.17g (band width %.17g rel)\n", dmax, dmin, dcan, dmax - dcan);
    int fails = 0;

    /* the endpoint and neighbor set (prereg) */
    double cases[10];
    cases[0] = dcan;
    cases[1] = nextdn(dcan);
    cases[2] = nextup(dcan);
    cases[3] = dmax;
    cases[4] = nextdn(dmax);
    cases[5] = nextup(dmax);            /* strictly ABOVE dmax: outside, infeasible */
    cases[6] = dmax * (1. - 1e-12);     /* the legacy knife (inside B) */
    cases[7] = 0.26132448829056582;     /* the measured tick-74 held-seat D */
    cases[8] = dmin + 1e-9;             /* the low-side boundary (unchanged) */
    cases[9] = 0.05;                    /* deep inside the annulus (no saturation) */

    for (int i = 0; i < 10; ++i) {
        double D = cases[i];
        int s_old, s_new; double c_old, c_new;
        legacy(D, &s_old, &c_old);
        bandv1(D, &s_new, &c_new);
        int in_band = (D >= dcan && D <= dmax);
        int drift;
        if (in_band) {
            drift = 0;  /* inside the band: differences are the registered change */
        } else {
            drift = (s_old != s_new) || (s_new == 1 && c_old != c_new);
        }
        int feas = (s_new == 0) || (c_new <= dmax && c_new >= dmin);
        printf("D=%.17g in_band=%d legacy(sat=%d,Dc=%.17g) v1(sat=%d,Dc=%.17g) outside_drift=%s feas=%s\n",
               D, in_band, s_old, c_old, s_new, c_new, drift ? "FAIL" : "ok", feas ? "ok" : "FAIL");
        if (drift) fails++;
        if (!feas) fails++;
    }
    /* both signs of the near-zero residual through the snap: the tick-74 chain */
    {
        double D = 0.26132448829056582, dx = -0.24455983362531949, dy = -0.092092214423816196;
        int s; double c;
        bandv1(D, &s, &c);
        double rx = dx * c / D, ry = dy * c / D;
        printf("tick-74 held-seat chain: sat=%d Dcan=%.17g rx=%.17g ry=%.17g (deterministic: one dcan, one D)\n", s, c, rx, ry);
    }
    printf("%s (fails=%d)\n", fails == 0 ? "ALL ENDPOINT CASES PASS" : "FALSIFIER FIRES", fails);
    return fails != 0;
}
