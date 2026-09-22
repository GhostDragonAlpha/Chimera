"""probe_inject.py -- regenerate probe_kernels.cuh from walker_kernels.cuh by
injecting the per-substep drill instrumentation:
  - int fkdbg global (host-replay drill gate, set by the driver via getenv)
  - FKDBG prints in fk_eval's M assembly (slot-2 pair contributions)
  - SUBPRE / TAUFULL / SUBFULL per-substep state dumps in tick_integ_kernel
    (tick 1 only: a_ticks[e]==0), matching cpp_substep_probe_instr's SUBPRE/
    TAUFULL/SUBFULL stderr lines so diff_census.py can align the two sides.

Trailer Agent: GLM 5.3.
"""
from pathlib import Path

src = Path("walker_kernels.cuh").read_text(encoding="utf-8")

# 1) the fkdbg global after the includes
anchor = "#define PI 3.141592653589793"
assert anchor in src
src = src.replace(anchor, anchor + "\nint fkdbg = 0; // drill-only probe gate (host replay compile); set by the driver", 1)

# 2) FKDBG print before the M assembly accumulation
anchor = """                    M[si * 18 + sj] = M[si * 18 + sj] + m * jvd + jwd;"""
assert anchor in src
inject = """                    if (fkdbg && (si == 2 || sj == 2)) {
                        printf("FKDBG b=%d si=%d sj=%d m=%.17g jvd=%.17g jwd=%.17g jv2=%.17g,%.17g,%.17g jv5=%.17g,%.17g,%.17g jw2=%.17g,%.17g,%.17g jw5=%.17g,%.17g,%.17g\\n",
                            b, si, sj, m, jvd, jwd,
                            jv[6], jv[7], jv[8], jv[15], jv[16], jv[17],
                            jw[6], jw[7], jw[8], jw[15], jw[16], jw[17]);
                    }
""" + anchor
src = src.replace(anchor, inject, 1)

# 3) SUBPRE right after the substep-start fk_eval in tick_integ_kernel
anchor = """        pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
        d =  (int)(0);"""
assert anchor in src
inject = """        pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
        if (a_ticks[e] <= 1) {
            printf("SUBPRE t=%d sub=%d", a_ticks[e], sub - 1);
            printf(" batpost=%.17g w2=%.17g", bat_post, w[2]);
            for (i = 0; i < (18); ++i) printf(" q%d=%.17g", i, q[i]);
            for (i = 0; i < (18); ++i) printf(" v%d=%.17g", i, v[i]);
            for (i = 0; i < (324); ++i) printf(" M%d=%.17g", i, M[i]);
            for (i = 0; i < (18); ++i) printf(" gv%d=%.17g", i, gv[i]);
            for (i = 0; i < (18); ++i) printf(" bv%d=%.17g", i, bv[i]);
            printf("\\n");
        }
        d =  (int)(0);"""
src = src.replace(anchor, inject, 1)

# 4) TAUFULL after the posture-drive torque (end of tau computation)
anchor = """            tau[2] = tq;
}
        for (d = 0; d < (13); ++d) {
            scales[d] = (double)(1.0);
}"""
assert anchor in src
inject = """            tau[2] = tq;
}
        if (a_ticks[e] <= 1) {
            printf("TAUFULL t=%d sub=%d", a_ticks[e], sub - 1);
            printf(" batpost=%.17g w2=%.17g", bat_post, w[2]);
            for (i = 0; i < (18); ++i) printf(" tau%d=%.17g", i, tau[i]);
            printf("\\n");
        }
        for (d = 0; d < (13); ++d) {
            scales[d] = (double)(1.0);
}"""
src = src.replace(anchor, inject, 1)

# 5) SUBFULL after the trial commit
anchor = """        if (a_ticks[e] <= 1) {
            printf("[SUB] sub=%d rc=%d q12=%.17g v9=%.17g v12=%.17g v13=%.17g v14=%.17g v17=%.17g v4=%.17g\\n", sub, rc, q[12], v[9], v[12], v[13], v[14], v[17], v[4]);
        }"""
if anchor not in src:
    # regenerate from clean walker_kernels.cuh has no [SUB] print; add fresh
    anchor2 = """        for (i = 0; i < (18); ++i) {
            q[i] = trial_q[i];
            v[i] = trial_v[i];
            w[i] = trial_w[i];
}
        for (d = 0; d < (12); ++d) {"""
    assert anchor2 in src, "trial commit anchor not found"
    inject = """        for (i = 0; i < (18); ++i) {
            q[i] = trial_q[i];
            v[i] = trial_v[i];
            w[i] = trial_w[i];
}
        if (a_ticks[e] <= 1) {
            printf("SUBFULL t=%d sub=%d", a_ticks[e], sub);
            printf(" batpost=%.17g w2=%.17g", bat_post, w[2]);
            for (i = 0; i < (18); ++i) printf(" q%d=%.17g", i, q[i]);
            for (i = 0; i < (18); ++i) printf(" v%d=%.17g", i, v[i]);
            for (i = 0; i < (13); ++i) printf(" sc%d=%.17g", i, scales[i]);
            printf("\\n");
        }
        for (d = 0; d < (12); ++d) {"""
    src = src.replace(anchor2, inject, 1)
else:
    inject = """        if (a_ticks[e] <= 1) {
            printf("SUBFULL t=%d sub=%d", a_ticks[e], sub);
            printf(" batpost=%.17g w2=%.17g", bat_post, w[2]);
            for (i = 0; i < (18); ++i) printf(" q%d=%.17g", i, q[i]);
            for (i = 0; i < (18); ++i) printf(" v%d=%.17g", i, v[i]);
            for (i = 0; i < (13); ++i) printf(" sc%d=%.17g", i, scales[i]);
            printf("\\n");
        }"""
    src = src.replace(anchor, inject, 1)

# 6) STOREDBG after the drain loop (cur_w/trial_w/bat_post at drain time)
anchor = """            if (d < 12) {
                bat[d] = store - spent;
}
            else {
                bat_post =  store - spent;
}
}"""
assert anchor in src, "drain anchor not found"
inject = """            if (d < 12) {
                bat[d] = store - spent;
}
            else {
                bat_post =  store - spent;
}
}
        if (a_ticks[e] <= 1) {
            printf("STOREDBG t=%d sub=%d curw2=%.17g trialw2=%.17g spentw2=%.17g batpost=%.17g\\n", sub - 1, cur_w[2], trial_w[2], trial_w[2] - cur_w[2], bat_post);
        }"""
src = src.replace(anchor, inject, 1)

# 7) drain internals at d==12
anchor = """            if (d < 12) {
                bat[d] = store - spent;
}
            else {
                bat_post =  store - spent;
}"""
assert anchor in src, "drain inner anchor not found"
inject = """            if (d < 12) {
                bat[d] = store - spent;
}
            else {
                if (a_ticks[e] <= 1) {
                    printf("DRAIN12 sub=%d d=%d c=%d store=%.17g spent=%.17g\\n", sub - 1, d, c, store, spent);
}
                bat_post =  store - spent;
}"""
src = src.replace(anchor, inject, 1)

Path("probe_kernels.cuh").write_text(src, encoding="utf-8")
print("probe_kernels.cuh written:", len(src), "bytes")
