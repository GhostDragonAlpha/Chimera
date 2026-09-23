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
src = src.replace(anchor, anchor + "\nint fkdbg = 0; // drill-only probe gate (host replay compile); set by the driver\nint fkdbg2 = 0; // CLOSEOUT-3 per-body jv/jw drill gate\nint fkdbg2_fired = 0; // one-shot latch\nint fkdbg3_fired = 0; // one-shot latch (contribution dump)", 1)

# 2) FKDBG print before the M assembly accumulation
anchor = """                    M[si * 18 + sj] = M[si * 18 + sj] + (m * jvd + jwd);"""
assert anchor in src, "M assembly anchor not found (regenerated form)"
inject = """                    if (fkdbg && (si == 2 || sj == 2)) {
                        printf("FKDBG b=%d si=%d sj=%d m=%.17g jvd=%.17g jwd=%.17g jv2=%.17g,%.17g,%.17g jv5=%.17g,%.17g,%.17g jw2=%.17g,%.17g,%.17g jw5=%.17g,%.17g,%.17g\\n",
                            b, si, sj, m, jvd, jwd,
                            jv[6], jv[7], jv[8], jv[15], jv[16], jv[17],
                            jw[6], jw[7], jw[8], jw[15], jw[16], jw[17]);
                    }
""" + anchor
src = src.replace(anchor, inject, 1)

# 2b) CLOSEOUT-3 per-body drill: at the first fk_eval whose q[0] equals the
# drill state's q0 (tick-0 substep-0 SUBPRE state), dump every body's jv/jw
# for slots 0..5 (matches the C++ CPPFK2 prints in coupled_articulation_instr.hpp).
anchor = """        transpose_rot(t1, rt);"""
assert anchor in src, "transpose_rot anchor not found"
inject = """        if (fkdbg2 && (!fkdbg2_fired) && q[0] == 0.0 && v[0] == 0.0 && v[3] == 0.76362478896964736) {
            printf("FKDBG2 b=%d m=%.17g", b, body_mass[b]);
            for (int _cki = 0; _cki < 6; ++_cki) printf(" jv%d=%.17g,%.17g,%.17g", _cki, jv[_cki * 3], jv[_cki * 3 + 1], jv[_cki * 3 + 2]);
            for (int _cki = 0; _cki < 6; ++_cki) printf(" jw%d=%.17g,%.17g,%.17g", _cki, jw[_cki * 3], jw[_cki * 3 + 1], jw[_cki * 3 + 2]);
            printf("\\n");
            if (b == 13) {
                fkdbg2_fired = 1;
            }
        }
        transpose_rot(t1, rt);"""
src = src.replace(anchor, inject, 1)

# 3) SUBPRE right after the substep-start fk_eval in tick_integ_kernel
anchor = """        pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
        d =  (int)(0);"""
assert anchor in src
inject = """        pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
        if (a_ticks[e] <= 4) {
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
        if (a_ticks[e] <= 4) {
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
anchor = """        if (a_ticks[e] <= 4) {
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
        if (a_ticks[e] <= 4) {
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
    inject = """        if (a_ticks[e] <= 4) {
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
        if (a_ticks[e] <= 4) {
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
                if (a_ticks[e] <= 4) {
                    printf("DRAIN12 sub=%d d=%d c=%d store=%.17g spent=%.17g\\n", sub - 1, d, c, store, spent);
}
                bat_post =  store - spent;
}"""
src = src.replace(anchor, inject, 1)

# 2c) CLOSEOUT-3 contribution drill: per-body Iw 3x3 + the M[0][0]/M[2][2]
# contributions (FKDBG3), gated by the same one-shot evaluate latch.
anchor = """        Iw =  t2;"""
assert anchor in src, "Iw anchor not found"
inject = """        Iw =  t2;
        if (fkdbg2 && (!fkdbg3_fired) && q[0] == 0.0 && v[0] == 0.0 && v[3] == 0.76362478896964736) {
            double c00, c22, w0a, w0b, w0c, w2a, w2b, w2c;
            w0a = Iw[0] * jw[0] + Iw[1] * jw[1] + Iw[2] * jw[2];
            w0b = Iw[4] * jw[0] + Iw[5] * jw[1] + Iw[6] * jw[2];
            w0c = Iw[8] * jw[0] + Iw[9] * jw[1] + Iw[10] * jw[2];
            w2a = Iw[0] * jw[6] + Iw[1] * jw[7] + Iw[2] * jw[8];
            w2b = Iw[4] * jw[6] + Iw[5] * jw[7] + Iw[6] * jw[8];
            w2c = Iw[8] * jw[6] + Iw[9] * jw[7] + Iw[10] * jw[8];
            c00 = body_mass[b] * (jv[0] * jv[0] + jv[1] * jv[1] + jv[2] * jv[2]) + (jw[0] * w0a + jw[1] * w0b + jw[2] * w0c);
            c22 = body_mass[b] * (jv[6] * jv[6] + jv[7] * jv[7] + jv[8] * jv[8]) + (jw[6] * w2a + jw[7] * w2b + jw[8] * w2c);
            printf("FKDBG3 b=%d m=%.17g Iw=%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g c00=%.17g c22=%.17g\\n",
                b, body_mass[b], Iw[0], Iw[1], Iw[2], Iw[4], Iw[5], Iw[6], Iw[8], Iw[9], Iw[10], c00, c22);
            if (b == 13) {
                fkdbg3_fired = 1;
            }
        }"""
src = src.replace(anchor, inject, 1)

# 8) CLOSEOUT-3 rate() checkpoint drill: on the FIRST rate() call, dump the
# free (acceleration) vector at four checkpoints -- FRHS (after the rhs
# assembly), FMUL (after the inv multiply), FFRIC (after the friction loop),
# FPROJ (after the row projection). Matches the C++ CPPFK4 prints.
anchor = """int fkdbg3_fired = 0; // one-shot latch (contribution dump)"""
assert anchor in src
src = src.replace(anchor, anchor + "\nint fkdbg4_fired = 0; // one-shot latch (rate checkpoint dump)", 1)

def ckpt_dump(tag):
    return ('{{\n'
            '            char _cktag[8] = "' + tag + '";\n'
            '            (void)_cktag;\n'
            '            printf("FKDBG4 ' + tag + '");\n'
            '            for (int _cki = 0; _cki < 18; ++_cki) printf(" %.17g", free[_cki]);\n'
            '            printf("\\n");\n'
            '        }}\n')

# FRHS: before the multiply (anchor is unique inside rate())
anchor = """    mat_vec(inv, free, free_acc);"""
assert src.count(anchor) == 1, "FRHS anchor not unique/found"
inject = """    if (fkdbg2 && (!fkdbg4_fired) && q[0] == 0.0 && v[0] == 0.0 && v[3] == 0.76362478896964736) {
        printf("FKDBG4 FRHS");
        for (int _cki = 0; _cki < 18; ++_cki) printf(" %.17g", free[_cki]);
        printf("\\n");
        printf("FKDBG4 RHSIN");
        for (int _cki = 0; _cki < 18; ++_cki) printf(" gv%d=%.17g bv%d=%.17g tau%d=%.17g v%d=%.17g", _cki, gv[_cki], _cki, bv[_cki], _cki, tau[_cki], _cki, v[_cki]);
        printf("\\n");
    }
""" + anchor
src = src.replace(anchor, inject, 1)

# FMUL: after free = free_acc copy
anchor = """        free[i] = free_acc[i];"""
assert src.count(anchor) == 1, "FMUL anchor not unique/found"
inject = anchor + """
        if (fkdbg2 && (!fkdbg4_fired) && q[0] == 0.0 && v[0] == 0.0 && v[3] == 0.76362478896964736) {
            printf("FKDBG4 FMUL");
            for (int _cki = 0; _cki < 18; ++_cki) printf(" %.17g", free[_cki]);
            printf("\\n");
        }"""
src = src.replace(anchor, inject, 1)

# FFRIC: before the projection call
anchor = """        if (project_rows(free, inv, rows, floors, R, n_stops, p, mult) == 0) {"""
assert src.count(anchor) == 1, "FFRIC anchor not unique/found"
inject = """        if (fkdbg2 && (!fkdbg4_fired) && q[0] == 0.0 && v[0] == 0.0 && v[3] == 0.76362478896964736) {
            printf("FKDBG4 FFRIC");
            for (int _cki = 0; _cki < 18; ++_cki) printf(" %.17g", free[_cki]);
            printf("\\n");
        }
""" + anchor
src = src.replace(anchor, inject, 1)

# FPROJ: before rv write (end of rate)
anchor = """    for (i = 0; i < (18); ++i) {
        rv[i] = free[i];
        rq[i] = v[i];
}"""
assert src.count(anchor) == 1, "FPROJ anchor not unique/found"
inject = """    if (fkdbg2 && (!fkdbg4_fired) && q[0] == 0.0 && v[0] == 0.0 && v[3] == 0.76362478896964736) {
        fkdbg4_fired = 1;
        printf("FKDBG4 FPROJ");
        for (int _cki = 0; _cki < 18; ++_cki) printf(" %.17g", free[_cki]);
        printf("\\n");
    }
""" + anchor
src = src.replace(anchor, inject, 1)

Path("probe_kernels.cuh").write_text(src, encoding="utf-8")
print("probe_kernels.cuh written:", len(src), "bytes")
