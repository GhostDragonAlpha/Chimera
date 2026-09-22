"""inject_probe.py -- (re)create probe_kernels.cuh: dump rate() entry state and
RHS ingredients. Trailer Agent: GLM 5.3."""
src = open('walker_kernels.cuh', encoding='utf-8').read()
NL = chr(10)
BSN = chr(92) + 'n'

old3 = """    double free_acc[18];
    mat_vec(inv, free, free_acc);
    for (i = 0; i < (18); ++i) {
        free[i] = free_acc[i];
}"""
assert old3 in src, "pattern3 not found"
old2 = """    for (k = 0; k < (8); ++k) {
        pb =  pt_body[k];"""
assert old2 in src, "pattern2 not found"
marker = ('fprintf(stderr, "PROBEGV '
          + ' '.join('%.17g ' for _ in range(18)) + BSN + '", '
          + ', '.join(f'gv[{i}]' for i in range(18)) + ');' + NL +
          'fprintf(stderr, "PROBEBV '
          + ' '.join('%.17g ' for _ in range(18)) + BSN + '", '
          + ', '.join(f'bv[{i}]' for i in range(18)) + ');' + NL)
src = src.replace(old2, "    " + marker + old2, 1)

lines = ["    { int _p, _q; fprintf(stderr, \"PROBEM \"); for (_p = 0; _p < 18; ++_p) for (_q = 0; _q < 18; ++_q) fprintf(stderr, \"%.17g \", M[_p*18+_q]); fprintf(stderr, \"" + BSN + "\"); }",
         "    { int _p, _q; fprintf(stderr, \"PROBEINV \"); for (_p = 0; _p < 18; ++_p) for (_q = 0; _q < 18; ++_q) fprintf(stderr, \"%.17g \", inv[_p*18+_q]); fprintf(stderr, \"" + BSN + "\"); }",
         "    { int _p; fprintf(stderr, \"PROBEFREE \"); for (_p = 0; _p < 18; ++_p) fprintf(stderr, \"%.17g \", free[_p]); fprintf(stderr, \"" + BSN + "\"); }"]
src = src.replace(old3, old3 + NL + NL.join(lines), 1)

open('probe_kernels.cuh', 'w', encoding='utf-8').write(src)
print("probe_kernels.cuh written")
