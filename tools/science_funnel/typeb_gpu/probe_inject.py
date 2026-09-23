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

# 9) CLOSEOUT-4 ADVTRACE drill: the tick-3 interior bisection surface. Globals
# + per-advance-call event-sequence prints (ent/imp/split/live/evt/clamp/cross/
# wall/end) armed per substep from tick_integ at the diverging tick
# (a_ticks[e]==3), plus the free_step plane-mask census (FST). Line grammar is
# IDENTICAL to the C++ ADVTRACE in gait_controller_instr.hpp, so the two
# streams diff line-by-line and the first differing line names the divergence.
anchor = """int fkdbg4_fired = 0; // one-shot latch (rate checkpoint dump)"""
assert anchor in src, "fkdbg4 global anchor not found (section 8 must run first)"
src = src.replace(anchor, anchor + "\nint advdbg = 0; // CLOSEOUT-4 advance-trace gate (armed per substep from tick_integ)\nint advn = 0; // advance-trace sequence counter", 1)

# arm: before the TOP advance call of the substep loop (first of the three
# advance( call sites in tick_integ_kernel -- the bisection and round-retry
# calls inherit the armed value of their substep).
anchor = """        advance(q, v, w, eff, cst[CF_dt] * (double)(0.25), mdl, cst, M, gv, bv, fr, frd, frdd,"""
assert src.count(anchor) == 3, "advance call anchor count != 3"
src = src.replace(anchor, """        advdbg = ((a_ticks[e] == 74)) ? 1 : 0;
""" + anchor, 1)

# ADV ent: before the MAIN impact call (first of the two 8-space rcv sites; the
# second is the mu==0 wall branch at the advance tail).
anchor = """        rcv[0] = 0;
        caught =  impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv, mdi, csti);"""
assert src.count(anchor) == 2, "S1 rcv anchor count != 2"
src = src.replace(anchor, """        if (advdbg) {
            printf("ADV n=%d ent h=%.17g depth=%d clamps=%d", advn, rem, depth, clamps);
            for (int _cki = 0; _cki < (18); ++_cki) printf(" q%d=%.17g v%d=%.17g", _cki, q1[_cki], _cki, v1[_cki]);
            printf("\\n");
            advn = advn + 1;
}
""" + anchor, 1)

# ADV imp: after the main impact, before the split test.
anchor = """        if (cst[CF_mu] > (double)(0.0) && caught > (double)(1e-9) && depth < 5) {"""
assert src.count(anchor) == 1, "S2 split-test anchor not unique"
src = src.replace(anchor, """        if (advdbg) {
            printf("ADV n=%d imp caught=%.17g", advn, caught);
            for (int _cki = 0; _cki < (18); ++_cki) printf(" q%d=%.17g v%d=%.17g", _cki, q1[_cki], _cki, v1[_cki]);
            printf("\\n");
            advn = advn + 1;
}
""" + anchor, 1)

# ADV split: inside the Coulomb-catch split branch (rem already halved == C++ h/2).
anchor = """            sp =  sp + 1;
            rem =  rem * (double)(0.5);
            depth =  depth + 3;
            continue;"""
assert src.count(anchor) == 1, "S3 push anchor not unique"
src = src.replace(anchor, """            if (advdbg) {
                printf("ADV n=%d split half=%.17g\\n", advn, rem * (double)(0.5));
                advn = advn + 1;
            }
            sp =  sp + 1;
            rem =  rem * (double)(0.5);
            depth =  depth + 3;
            continue;""", 1)

# ADV live: before the main free_step (the live mask + pre-step gaps).
anchor = """        rcs =  free_step(q1, v1, w1, tau, live, rem, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, mdi, csti);"""
assert src.count(anchor) == 1, "S4 main free_step anchor not unique"
src = src.replace(anchor, """        if (advdbg) {
            printf("ADV n=%d live", advn);
            for (int _cki = 0; _cki < (4); ++_cki) printf(" l%d=%d g%d=%.17g", _cki, live[_cki], _cki, gap_of_k(ptp, pt_radius_g, _cki * 2, cst[CF_plane_y]));
            printf("\\n");
            advn = advn + 1;
}
""" + anchor, 1)

# ADV evt (before the plain-end branch) + ADV end (first thing inside it).
anchor = """        if (which == -1) {
            for (i = 0; i < (18); ++i) {
                q1[i] = end_q[i];"""
assert src.count(anchor) == 1, "S5/S9 which==-1 anchor not unique"
src = src.replace(anchor, """        if (advdbg) {
            printf("ADV n=%d evt which=%d khit=%d hit=%.17g wall=%.17g", advn, which, khit < 0 ? khit : khit * 2, hit, wall);
            for (int _cki = 0; _cki < (18); ++_cki) printf(" q%d=%.17g v%d=%.17g", _cki, end_q[_cki], _cki, end_v[_cki]);
            printf("\\n");
            advn = advn + 1;
}
        if (which == -1) {
            if (advdbg) {
                printf("ADV n=%d end\\n", advn);
                advn = advn + 1;
            }
            for (i = 0; i < (18); ++i) {
                q1[i] = qe[i];""", 1)

# ADV clamp: first thing in the fp-boundary pin branch.
anchor = """        if (hit <= (double)(1e-12)) {
            if (clamps >= 64) {"""
assert src.count(anchor) == 1, "S6 clamp anchor not unique"
src = src.replace(anchor, """        if (hit <= (double)(1e-12)) {
            if (advdbg) {
                printf("ADV n=%d clamp which=%d khit=%d wall=%.17g hit=%.17g\\n", advn, which, khit, wall, hit);
                advn = advn + 1;
            }
            if (clamps >= 64) {""", 1)

# ADV cross: first thing in the contact-crossing branch.
anchor = """        if (which == -2) {"""
assert src.count(anchor) == 1, "S7 which==-2 anchor not unique"
src = src.replace(anchor, """        if (which == -2) {
            if (advdbg) {
                printf("ADV n=%d cross khit=%d hit=%.17g\\n", advn, khit < 0 ? khit : khit * 2, hit);
                advn = advn + 1;
            }""", 1)

# ADV wallev: before the tail free_step of the drive-stop wall branch.
anchor = """        rcw =  free_step(q1, v1, w1, tau, live, hit, mdl, cst,"""
assert src.count(anchor) == 1, "S8 rcw anchor not unique"
src = src.replace(anchor, """        if (advdbg) {
            printf("ADV n=%d wallev which=%d hit=%.17g\\n", advn, which, hit);
            advn = advn + 1;
}
""" + anchor, 1)

# FST: the free_step plane-mask census, before the stage-a rate call. Guarded
# exactly like the C++ print (inside contact_&&mu_>0) so the streams align.
anchor = """    rc =  rate(q0, v0, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, qa, va, mdi, csti);"""
assert src.count(anchor) == 1, "FST rate-a anchor not unique"
src = src.replace(anchor, """    if (advdbg && csti[CI_contact] != 0 && cst[CF_mu] > (double)(0.0)) {
        printf("FST n=%d gate=%.17g h=%.17g", advn, gate, h);
        for (int _cki = 0; _cki < (4); ++_cki) printf(" p%d=%d g%d=%.17g", _cki, plane[_cki], _cki, gap_of_k(ptp, pt_radius_g, _cki * 2, cst[CF_plane_y]));
        printf("\\n");
        advn = advn + 1;
}
""" + anchor, 1)

# 10) CLOSEOUT-4 stage 2: FSEND -- the free_step END state (q1/v1 0..17) right
# after the RK combine, keyed to the FST n so the first bisection free_step
# whose end state differs in bits is pinpointed exactly.
anchor = """        w1[i] = w0[i] + tau[i] * (q1[i] - q0[i]);
}
    return 0;
}"""
assert src.count(anchor) == 1, "FSEND free_step tail anchor not unique"
src = src.replace(anchor, """        w1[i] = w0[i] + tau[i] * (q1[i] - q0[i]);
}
    if (advdbg) {
        printf("FSEND n=%d", advn);
        for (int _cki = 0; _cki < (18); ++_cki) printf(" q%d=%.17g v%d=%.17g", _cki, q1[_cki], _cki, v1[_cki]);
        printf("\\n");
    }
    return 0;
}""", 1)

# 11) CLOSEOUT-4 stage 2: RT -- the rate() interior checkpoints (FRHS/FMUL/
# RTTOUCH/FFRIC/FPROJ), armed with the ADVTRACE window and narrowed by the
# RTLO/RTHI env window over the armed-call counter. Matches the C++ RT grammar.
anchor = """int advdbg = 0; // CLOSEOUT-4 advance-trace gate (armed per substep from tick_integ)
int advn = 0; // advance-trace sequence counter"""
assert anchor in src, "advdbg globals anchor not found"
src = src.replace(anchor, anchor + "\nint raten = 0; // armed rate() call counter\nint rt_lo = -1; int rt_hi = -1; int rt_init = 0; // RTLO/RTHI window (set once from env)", 1)

anchor = """    mat_vec(inv, free, free_acc);"""
assert src.count(anchor) == 1, "RTFRHS anchor not unique (after section 8)"
src = src.replace(anchor, """    if (!rt_init) {
        rt_init = 1;
        if (getenv("RTLO")) rt_lo = atoi(getenv("RTLO"));
        if (getenv("RTHI")) rt_hi = atoi(getenv("RTHI"));
    }
    if (advdbg && (rt_lo < 0 || (raten >= rt_lo && raten <= rt_hi))) {
        printf("RT n=%d FRHS", raten);
        for (int _cki = 0; _cki < (18); ++_cki) printf(" %.17g", free[_cki]);
        printf("\\n");
    }
""" + anchor, 1)

# FMUL: section 8 put the FKDBG4 FMUL block between the copy and the loop close;
# anchor on that block's tail and emit RT FMUL after the for-loop close.
anchor = """            printf("FKDBG4 FMUL");
            for (int _cki = 0; _cki < 18; ++_cki) printf(" %.17g", free[_cki]);
            printf("\\n");
        }
}"""
assert src.count(anchor) == 1, "RTFMUL anchor not unique (after section 8)"
src = src.replace(anchor, """            printf("FKDBG4 FMUL");
            for (int _cki = 0; _cki < 18; ++_cki) printf(" %.17g", free[_cki]);
            printf("\\n");
        }
}
    if (advdbg && (rt_lo < 0 || (raten >= rt_lo && raten <= rt_hi))) {
        printf("RT n=%d FMUL", raten);
        for (int _cki = 0; _cki < (18); ++_cki) printf(" %.17g", free[_cki]);
        printf("\\n");
}""", 1)

anchor = """    if (csti[CI_contact] != 0 && cst[CF_mu] > (double)(0.0) && stop == 0) {"""
assert src.count(anchor) == 1, "RTTOUCH anchor not unique"
src = src.replace(anchor, """    if (advdbg && (rt_lo < 0 || (raten >= rt_lo && raten <= rt_hi))) {
        printf("RT n=%d TOUCH stop=%d", raten, stop);
        for (int _cki = 0; _cki < (4); ++_cki) printf(" t%d=%d g%d=%.17g", _cki, touching[_cki], _cki, gap_of_k(ptp, pt_radius_g, _cki * 2, cst[CF_plane_y]));
        printf("\\n");
    }
""" + anchor, 1)

anchor = """    for (r = 0; r < (4); ++r) {
        if (touching[r] == 0) {
            continue;
}
        for (i = 0; i < (18); ++i) {
            rn[i] = ptJ[(r * 3 + 1) * 18 + i];
}
        floor_k =  -ptbias[r * 3 + 1];"""
assert src.count(anchor) == 1, "RTFFRIC anchor not unique"
src = src.replace(anchor, """    if (advdbg && (rt_lo < 0 || (raten >= rt_lo && raten <= rt_hi))) {
        printf("RT n=%d FFRIC", raten);
        for (int _cki = 0; _cki < (18); ++_cki) printf(" %.17g", free[_cki]);
        for (int _cki = 0; _cki < (4); ++_cki) printf(" m%d=%d", _cki, mode_k[_cki]);
        printf("\\n");
    }
""" + anchor, 1)

anchor = """    for (i = 0; i < (18); ++i) {
        rv[i] = free[i];
        rq[i] = v[i];
}"""
assert src.count(anchor) == 1, "RTFPROJ anchor not unique"
src = src.replace(anchor, """    if (advdbg && (rt_lo < 0 || (raten >= rt_lo && raten <= rt_hi))) {
        printf("RT n=%d FPROJ R=%d ns=%d", raten, R, n_stops);
        for (int _cki = 0; _cki < (18); ++_cki) printf(" %.17g", free[_cki]);
        printf("\\n");
    }
    if (advdbg) {
        raten = raten + 1;
}
""" + anchor, 1)

# 12) CLOSEOUT-4 stage 3: per-point friction drill. RTFRI (in rate's friction
# loop, before friction_solve) dumps the direction-selection inputs; RTFS
# (inside friction_solve) dumps the 2x2 solve internals. Both gated by the
# same armed+window logic; fsdbg armed per rate() call so impact()'s
# friction_solve calls never print.
anchor = """int raten = 0; // armed rate() call counter
int rt_lo = -1; int rt_hi = -1; int rt_init = 0; // RTLO/RTHI window (set once from env)"""
assert anchor in src, "RT globals anchor not found"
src = src.replace(anchor, anchor + "\nint fsdbg = 0; // per-point friction drill gate (armed inside rate's friction loop)\nint fsk = -1; // the friction point index for RTFS", 1)

# RTFRI: at the top of each friction-loop iteration (after the touching skip),
# dump slip/planar/direction; and after friction_solve, dump mode/ln/lt.
anchor = """        for (r = 0; r < (4); ++r) {
            if (touching[r] == 0) {
                continue;
}
            for (i = 0; i < (18); ++i) {
                jt1[i] = ptJ[(r * 3 + 0) * 18 + i];
                jt2[i] = ptJ[(r * 3 + 2) * 18 + i];
}"""
assert src.count(anchor) == 1, "RTFRI loop head anchor not unique"
src = src.replace(anchor, """        fsdbg = (advdbg && (rt_lo < 0 || (raten >= rt_lo && raten <= rt_hi))) ? 1 : 0;
""" + anchor, 1)

anchor = """            friction_solve(free, inv, rn, row_t, -by, -(dir_x * bx + dir_z * bz), cst[CF_mu], slip_sign, force, ln, lt, md);
            if (md[0] > 0) {"""
assert src.count(anchor) == 1, "RTFRI solve anchor not unique"
src = src.replace(anchor, """            if (fsdbg) {
                printf("RTFRI n=%d k=%d svx=%.17g svz=%.17g planar=%.17g kslip=%.17g dx=%.17g dz=%.17g ss=%d fx=%.17g fz=%.17g ft=%.17g",
                    raten, r, svx, svz, planar, cst[CF_k_slip], dir_x, dir_z, slip_sign, -by, -(dir_x * bx + dir_z * bz), row_dot(row_t, v));
            }
            fsk = r;
            friction_solve(free, inv, rn, row_t, -by, -(dir_x * bx + dir_z * bz), cst[CF_mu], slip_sign, force, ln, lt, md);
            if (fsdbg) {
                printf("RTFRO n=%d k=%d mode=%d ln=%.17g lt=%.17g\\n", raten, r, md[0], ln[0], lt[0]);
            }
            if (md[0] > 0) {""", 1)

# disarm fsdbg after the friction block
anchor = """    for (r = 0; r < (4); ++r) {
        if (touching[r] == 0) {
            continue;
}
        for (i = 0; i < (18); ++i) {
            rn[i] = ptJ[(r * 3 + 1) * 18 + i];
}
        floor_k =  -ptbias[r * 3 + 1];"""
assert src.count(anchor) == 1, "fsdbg disarm anchor not unique"
src = src.replace(anchor, """    fsdbg = 0;
""" + anchor, 1)

# RTFS: inside friction_solve, after the 2x2 assembly (gated by fsdbg).
anchor = """    det =  A * C - B * B;"""
assert src.count(anchor) == 1, "RTFS det anchor not unique"
src = src.replace(anchor, """    det =  A * C - B * B;
    if (fsdbg) {
        printf("RTFS k=%d A=%.17g B=%.17g C=%.17g rn=%.17g rt=%.17g det=%.17g\\n", fsk, A, B, C, rn, rt, det);
    }""", 1)

anchor = """    if (det > (double)(1e-18)) {
        nn =  (rn * C - rt * B) / det;
        t =  (rt * A - rn * B) / det;"""
assert src.count(anchor) == 1, "RTFS cone anchor not unique"
src = src.replace(anchor, """    if (det > (double)(1e-18)) {
        nn =  (rn * C - rt * B) / det;
        t =  (rt * A - rn * B) / det;
        if (fsdbg) {
            printf("RTFSC k=%d nn=%.17g t=%.17g abt=%.17g muNN=%.17g tss=%.17g\\n", fsk, nn, t, fabs(t), mu * nn + (double)(1e-12), t * (double)slip_sign);
        }""", 1)

# 13) CLOSEOUT-4 stage 4: RTSC -- the contact-scan per-point gap decision (the
# pair-min gap at the end state, printed before the g>=0 skip). Names which
# point the two implementations scan differently.
anchor = """                pot =  fk_eval(end_q,  end_v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
                g =  gap_of_k(ptp, pt_radius_g, (r - 1) * 2, cst[CF_plane_y]);
                if (g >= (double)(0.0)) {
                    continue;"""
assert src.count(anchor) == 1, "RTSC per-point scan anchor not unique"
src = src.replace(anchor, """                pot =  fk_eval(end_q,  end_v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
                g =  gap_of_k(ptp, pt_radius_g, (r - 1) * 2, cst[CF_plane_y]);
                if (advdbg) {
                    printf("RTSC n=%d r=%d g=%.17g gh=%.17g gm=%.17g py=%.17g q14=%.17g q15=%.17g q16=%.17g q17=%.17g live=%d\\n", advn, r - 1, g, ptp[((r - 1) * 2) * 3 + 1] + pt_radius_g[(r - 1) * 2] - cst[CF_plane_y], ptp[((r - 1) * 2 + 1) * 3 + 1] + pt_radius_g[(r - 1) * 2 + 1] - cst[CF_plane_y], cst[CF_plane_y], end_q[14], end_q[15], end_q[16], end_q[17], live[r - 1]);
                }
                if (g >= (double)(0.0)) {
                    continue;""", 1)


# 14) CLOSEOUT-4: impact() interior drill. IMPF per friction-catch point,
# IMPP after the projection. Gate: advdbg (armed) -- impact runs inside the
# advance window only.
anchor = """    if (cst[CF_mu] > (double)(0.0) && n_stops == 0 && csti[CI_contact] != 0) {
        double jt1[18];"""
assert src.count(anchor) == 1, "impact friction block anchor not found"
src = src.replace(anchor, """    if (advdbg) {
        printf("IMPE n=%d ns=%d t0=%d t1=%d t2=%d t3=%d g0=%.17g g1=%.17g g2=%.17g g3=%.17g\\n", advn, n_stops, touching[0], touching[1], touching[2], touching[3],
            gap_of_k(ptp, pt_radius_g, 0, cst[CF_plane_y]), gap_of_k(ptp, pt_radius_g, 2, cst[CF_plane_y]),
            gap_of_k(ptp, pt_radius_g, 4, cst[CF_plane_y]), gap_of_k(ptp, pt_radius_g, 6, cst[CF_plane_y]));
    }
""" + anchor, 1)

anchor = """            friction_solve(v, inv, rn, row_t, (double)(0.0), (double)(0.0), cst[CF_mu], 1, force, ln, lt, md);"""
assert src.count(anchor) == 1, "impact friction_solve anchor not found"
src = src.replace(anchor, """            friction_solve(v, inv, rn, row_t, (double)(0.0), (double)(0.0), cst[CF_mu], 1, force, ln, lt, md);
            if (advdbg) {
                printf("IMPF n=%d r=%d closing=%.17g planar=%.17g mode=%d ln=%.17g lt=%.17g caught=%.17g\\n", advn, r, closing, planar, md[0], ln[0], lt[0], caught);
            }""", 1)

anchor = """        if (project_rows(v, inv, rows, floors, R, n_stops, p, mult) == 0) {
            rc[0] = 5;
            return (double)(0.0);
}"""
assert src.count(anchor) == 1, "impact projection anchor not found"
src = src.replace(anchor, """        if (project_rows(v, inv, rows, floors, R, n_stops, p, mult) == 0) {
            rc[0] = 5;
            return (double)(0.0);
}
        if (advdbg) {
            printf("IMPP n=%d R=%d ns=%d", advn, R, n_stops);
            for (int _cki = 0; _cki < (R); ++_cki) printf(" m%d=%.17g", _cki, mult[_cki]);
            printf("\\n");
        }""", 1)



# 15) CLOSEOUT-4: poscorr gram drill. IMPC dumps the 2x2 gram inputs, rhs, the
# factor result and the multipliers at the knife-edge pivot.
anchor = """        if (gram_factor4(gram, npen, rhs, lam) == 1) {"""
assert src.count(anchor) == 1, "gram_factor4 call anchor not found"
src = src.replace(anchor, """        const int gok =  gram_factor4(gram, npen, rhs, lam);
        if (advdbg) {
            printf("IMPC n=%d npen=%d g00=%.17g g01=%.17g g10=%.17g g11=%.17g r0=%.17g r1=%.17g ok=%d l0=%.17g l1=%.17g\\n", advn, npen, gram[0], gram[1], gram[2], gram[3], rhs[0], rhs[1], gok, lam[0], lam[1]);
        }
        if (gok == 1) {""", 1)

# 16) CLOSEOUT-6 SEAT/SV drill: the plan-phase fore-follow pipeline checkpoint
# (the tick-61 fore-left tau[14]/[15] ~390-ulp source hunt). Grammar is
# IDENTICAL to the C++ SEATIN/SEATF/SEATOUT/SV prints in
# gait_controller_instr.hpp so the two streams diff line-by-line:
#   SEATIN  -- the liftoff decision inputs (clocks, wall headroom, gate,
#              target headrooms th1/th2, thin/due/envelope) before the branch;
#   SEATF   -- the fore_follow result seat at both call sites;
#   SEATOUT -- post-application target/branch/ikb/clock;
#   SV      -- the servo's per-drive target/state/raw-PD (fore drives only).
# Armed exactly like the RT window: a_ticks[e]==66 (host tick 67).
# CLOSEOUT-8: the SEATIN print moved to mirror the C++ site EXACTLY --
# gait_controller_instr.hpp prints it at the decision INPUTS (after env_t,
# before the branch chain); the old placement (inside the act==1 lift branch)
# only printed when the lift fired, so the sides' SEATIN sets could never
# pair (cpp 9 lines vs host 2 at the 66-window) and the flipping tick's
# envt was invisible on the host side.
anchor = """                env_t =  fore_env(mdl, cst, fr, leg, paw_t, v[3], csti, paw_y[leg]);"""
assert src.count(anchor) == 1, "SEATIN env_t anchor not unique"
src = src.replace(anchor, """                env_t =  fore_env(mdl, cst, fr, leg, paw_t, v[3], csti, paw_y[leg]);
                if (a_ticks[e] >= 40 && a_ticks[e] <= 75) {
                    printf("SEATIN t=%d leg=%d ft=%.17g fst=%.17g fcy=%.17g wb=%d whr=%.17g gt=%d th1=%.17g th2=%.17g thin=%d due=%d envt=%.17g p0=%.17g p1=%.17g p2=%.17g\\n",
                        (int)a_ticks[e], leg, f_t[leg], f_st[leg], f_cy[leg], wall_bound, wall_hr, gated, th1, th2, thin_seat, due, env_t, paw_t[leg * 3], paw_t[leg * 3 + 1], paw_t[leg * 3 + 2]);
                }""", 1)

anchor = """                    fore_follow(mdl, cst, fr, leg, paw_t, ikb[leg], mdi, csti, seat);"""
assert src.count(anchor) == 2, "SEATF fore_follow call anchor count != 2"
src = src.replace(anchor, """                    fore_follow(mdl, cst, fr, leg, paw_t, ikb[leg], mdi, csti, seat);
                    if (a_ticks[e] >= 40 && a_ticks[e] <= 75) {
                        printf("SEATF t=%d leg=%d s0=%.17g s1=%.17g s2=%.17g\\n", (int)a_ticks[e], leg, seat[0], seat[1], seat[2]);
                    }""", 2)

anchor = """            if (f_t[leg] >= f_cy[leg]) {
                f_hgh[leg] = 0;
                f_hhl[leg] = 0;
                hpt =  mdi[OI_fore_heel_pt + leg];"""
assert src.count(anchor) == 1, "SEATOUT anchor not unique"
src = src.replace(anchor, """                if (a_ticks[e] >= 40 && a_ticks[e] <= 75) {
                    printf("SEATOUT t=%d leg=%d act=%d p0=%.17g p1=%.17g p2=%.17g ikb=%d ft=%.17g fmo=%d fst=%.17g\\n",
                        (int)a_ticks[e], leg, act, paw_t[leg * 3], paw_t[leg * 3 + 1], paw_t[leg * 3 + 2], ikb[leg], f_t[leg], f_mo[leg], f_st[leg]);
                }
            if (f_t[leg] >= f_cy[leg]) {
                hpt =  mdi[OI_fore_heel_pt + leg];""", 1)

anchor = """            tq =  mdl[OF_kp + d - 1] * (target - q[c]) - mdl[OF_kd + d - 1] * v[c];"""
assert src.count(anchor) == 1, "SV tq anchor not unique"
src = src.replace(anchor, anchor + """
            if (a_ticks[e] >= 40 && a_ticks[e] <= 75 && d >= 9) {
                printf("SV t=%d d=%d c=%d tgt=%.17g qc=%.17g vc=%.17g tqr=%.17g\\n", (int)a_ticks[e], d - 1, c, target, q[c], v[c], tq);
                if (d == 9 && a_ticks[e] >= 73 && a_ticks[e] <= 75) {
                    printf("IKIK t=%d q1f=%.17g q2f=%.17g q1rx=%.17g q2rx=%.17g\\n", (int)a_ticks[e], q1f, q2f, q1rx, q2rx);
                }
            }""", 1)

# 16b) CLOSEOUT-8 FKIN: the exact fore_ik inputs at the flipping tick (the
# 2-ulp hunt). Appended inside the generated SV block.
anchor = """                if (d == 9 && a_ticks[e] >= 73 && a_ticks[e] <= 75) {
                    printf("IKIK t=%d q1f=%.17g q2f=%.17g q1rx=%.17g q2rx=%.17g\\n", (int)a_ticks[e], q1f, q2f, q1rx, q2rx);
                }"""
assert src.count(anchor) == 1, "IKIK anchor not unique"
src = src.replace(anchor, anchor + """
                {
                    const int offk = csti[CI_pelvis_row] * 16;
                    printf("FKIN m=%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g paw=%.17g,%.17g,%.17g beta=%.17g L1=%.17g rho=%.17g ikb=%d\\n",
                        fr[offk + 0], fr[offk + 1], fr[offk + 2], fr[offk + 3], fr[offk + 4], fr[offk + 5], fr[offk + 6], fr[offk + 7], fr[offk + 8], fr[offk + 9], fr[offk + 10], fr[offk + 11], fr[offk + 12], fr[offk + 13], fr[offk + 14], fr[offk + 15],
                        paw_t[0], paw_t[1], paw_t[2], cst[CF_fore_beta], cst[CF_fore_L1], cst[CF_fore_rho], ikb[0]);
                }""", 1)

Path("probe_kernels.cuh").write_text(src, encoding="utf-8")
print("probe_kernels.cuh rewritten with hold drill:", len(src), "bytes")