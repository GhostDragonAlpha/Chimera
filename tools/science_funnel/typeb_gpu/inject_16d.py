"""inject_16d.py -- closeout-8: append the TIE-V2 PROROW drill section to
probe_inject.py (16d) and regenerate probe_kernels.cuh. Run AFTER
probe_inject.py's own write (this module appends its own write).

Reset probe_inject.py to HEAD first if a previous append is present
(`git checkout HEAD -- probe_inject.py`).

The drill: the project_rows per-mask decision trace, self-gated to the
sub-scale projection (every |floors[k]| < 1e-8 -- the pads are all within
their own position resolution). One __device__ latch (g_allsub_proj) set at
function entry; three prints: lamneg (the lambda<0 invalidations), chk (the
per-row floor checks), and the g1 1x1 solve (A/rhs/lam).

Trailer: Agent: GLM 5.3.
"""
from pathlib import Path

BS = chr(92)
NN = BS + BS + 'n'   # the two-char backslash-n, as probe_inject.py file bytes
TQ3 = chr(34) * 3   # the three-double-quote sequence, file bytes

p = Path("probe_inject.py")
s = p.read_text(encoding="utf-8")
start = s.find("# 16d) CLOSEOUT-8 TIE-V2 DRILL")
if start > 0:
    s = s[:start]

sig = '__device__ inline long long project_rows(double* initial, double* inv, double* rows, double* floors, int R, int n_stops, double* p_out, double* multipliers, double tol_band) {'

L = []
def a(x):
    L.append(x)

a("")
a("# 16d) CLOSEOUT-8 TIE-V2 DRILL: the project_rows per-mask decision trace at")
a("# the sub-scale projection (the tick-41 row-budget hunt). Self-gated: the")
a("# enter print and the latch fire only when EVERY floor is below the")
a("# contact-residual scale (|floors[k]| < 1e-8).")
a("anchor0 = " + TQ3 + sig + TQ3)
a("assert src.count(anchor0) == 1, \"project_rows signature anchor not unique\"")
a("src = src.replace(anchor0, " + TQ3 + "__device__ int g_allsub_proj = 0; // tie-v2 drill latch")
a("__device__ inline int allsub_dbg_proj() { return g_allsub_proj; }")
a(sig)
a("    {")
a("        int allsub = 1;")
a("        for (int fk = 0; fk < R; ++fk) {")
a("            if (fabs(floors[fk]) >= 1e-8) { allsub = 0; }")
a("        }")
a("        g_allsub_proj = allsub;")
a("        if (allsub) {")
a('            printf("PROROW enter R=%d f0=%.17g f1=%.17g f2=%.17g f3=%.17g f4=%.17g' + NN + '", R, floors[0], R > 1 ? floors[1] : 0.0, R > 2 ? floors[2] : 0.0, R > 3 ? floors[3] : 0.0, R > 4 ? floors[4] : 0.0);')
a("        }")
a("    }" + TQ3 + " , 1)")
a("")
# lamneg: the print goes INSIDE the existing if -- no extra brace, no re-append
a("lamanchor = " + TQ3 + "                                if (lam[k] < (double)(-1e-10)) {" + TQ3)
a("assert src.count(lamanchor) == 1, \"project_rows lam anchor not unique\"")
a("src = src.replace(lamanchor, " + TQ3 + "                                if (lam[k] < (double)(-1e-10)) {")
a("                                    if (g_allsub_proj) {")
a('                                        printf("PROROW lamneg tier=%d mask=%d k=%d lam=%.17g' + NN + '", tier, mask, k, lam[k]);')
a("                                    }" + TQ3 + ", 1)")
a("")
# chk: the print goes BEFORE the existing if (fires on every row's check);
# the if-line IS re-appended here (the replacement does not contain it)
a("chkanchor = " + TQ3 + "                                    if (got < floors[k] - tol) {" + TQ3)
a("assert src.count(chkanchor) == 1, \"project_rows chk anchor not unique\"")
a("src = src.replace(chkanchor, " + TQ3 + "                                    if (g_allsub_proj) {")
a('                                        printf("PROROW chk tier=%d mask=%d k=%d got=%.17g floor=%.17g tol=%.17g' + NN + '", tier, mask, k, got, floors[k], tol);')
a("                                    }" + TQ3 + " + chkanchor, 1)")
a("")
# g1: the 1x1 solve print INSIDE the gram_factor success branch
a("gramanchor = " + TQ3 + "                        if (gram_factor10(gram, cnt, rhs, lam) == 1) {" + TQ3)
a("assert src.count(gramanchor) == 1, \"project_rows gram anchor not unique\"")
a("src = src.replace(gramanchor, " + TQ3 + "                        if (gram_factor10(gram, cnt, rhs, lam) == 1) {")
a("                            if (g_allsub_proj && cnt == 1) {")
a('                                printf("PROROW g1 A=%.17g rhs=%.17g lam=%.17g' + NN + '", gram[0], rhs[0], lam[0]);')
a("                            }" + TQ3 + ", 1)")
a("")
a('Path("probe_kernels.cuh").write_text(src, encoding="utf-8")')
a('print("probe_kernels.cuh rewritten with tie-v2 drill:", len(src), "bytes")')

s = s + "\n".join(L)
p.write_text(s, encoding="utf-8")
print("16d appended (clean v2)")
