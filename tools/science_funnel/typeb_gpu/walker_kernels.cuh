// AUTO-TRANSLATED by numba2cu.py v4. Hand-fix scalar args where the compiler
// names stragglers. Floordiv sites are positive-operand by inspection.
// cu_total_q stands in for a_q.shape[0]: a __device__ symbol the host sets to
// E*18 at env_create (cudaMemcpyToSymbol), so the `e >= ne` tail-thread guards
// fire exactly like numba's shape-based guards.
#pragma once
#include <cuda_runtime.h>
#include <math.h>
__device__ long long cu_total_q = 1073741824LL;
#define PI 3.141592653589793
static const int OF_ax_axis = 0;
static const int OF_ax_slope = 54;
static const int OF_ax_const = 72;
static const int OF_body_mass = 90;
static const int OF_body_com = 104;
static const int OF_body_inertia = 146;
static const int OF_body_fp = 188;
static const int OF_body_fc = 412;
static const int OF_pt_local = 636;
static const int OF_pt_radius = 660;
static const int OF_lower = 668;
static const int OF_upper = 686;
static const int OF_drive_cap = 704;
static const int OF_drive_damping = 716;
static const int OF_kp = 728;
static const int OF_kd = 740;
static const int OF_tab_hip = 752;
static const int OF_tab_knee = 773;
static const int OF_tab_ankle = 794;
static const int OF_tab_mp = 815;
static const int OF_zeros4 = 836;
static const int OF_vault = 840;
static const int OF_fore_mount_local = 861;
static const int OF_hind_mount = 867;
static const int OI_ax_rot = 0;
static const int OI_ax_slot = 18;
static const int OI_body_axoff = 36;
static const int OI_body_parent = 51;
static const int OI_chain_off = 65;
static const int OI_chain_ax = 80;
static const int OI_pt_body = 140;
static const int OI_drive_coord = 148;
static const int OI_fore_coord = 160;
static const int OI_hind_coord = 164;
static const int OI_hind_drive = 172;
static const int OI_fore_drive = 180;
static const int OI_fore_heel_pt = 184;
static const int OI_hind_heel_pt = 186;
static const int CF_plane_y = 0;
static const int CF_gy = 1;
static const int CF_dt = 2;
static const int CF_mu = 3;
static const int CF_k_touch = 4;
static const int CF_k_slip = 5;
static const int CF_k_release = 6;
static const int CF_t_cycle = 7;
static const int CF_duty = 8;
static const int CF_toe_off = 9;
static const int CF_capture_phi = 10;
static const int CF_kp_post = 11;
static const int CF_kd_post = 12;
static const int CF_store_post = 13;
static const int CF_height_crit = 14;
static const int CF_height_floor = 15;
static const int CF_fore_L1 = 16;
static const int CF_fore_rho = 17;
static const int CF_fore_beta = 18;
static const int CF_hind_L1 = 19;
static const int CF_hind_L2 = 20;
static const int CF_hind_xm = 21;
static const int CF_fore_pose_sh = 22;
static const int CF_fore_pose_el = 23;
static const int CF_collapse_y = 24;
static const int CF_pi = 25;
static const int CI_nbod = 12;
static const int CI_naxes = 13;
static const int CI_settle_total = 0;
static const int CI_contact = 1;
static const int CI_power = 2;
static const int CI_gait_enabled = 3;
static const int CI_capture_enabled = 4;
static const int CI_posture_drive = 5;
static const int CI_drive_en = 6;
static const int CI_reflex_level = 7;
static const int CI_fold_budget = 8;
static const int CI_unload_ticks = 9;
static const int CI_tair = 10;
static const int CI_pelvis_row = 11;

__device__ inline void mm(double* a, double* b, double* out) {
    int i;
    int j;
    double s;
    int k;
    for (i = 0; i < (4); ++i) {
        for (j = 0; j < (4); ++j) {
            s =  (double)(0.0);
            for (k = 0; k < (4); ++k) {
                s =  s + a[i * 4 + k] * b[k * 4 + j];
}
            out[i * 4 + j] = s;
}
}
}

__device__ inline void rot_axis(double* axis, double ang, double* out) {
    double c;
    double s;
    double t;
    double x;
    double y;
    double z;
    c =  cos(ang);
    s =  sin(ang);
    t =  (double)(1.0) - c;
    x =  axis[0];
    y =  axis[1];
    z =  axis[2];
    out[0] = c + x * x * t;
    out[1] = x * y * t - z * s;
    out[2] = x * z * t + y * s;
    out[3] = (double)(0.0);
    out[4] = y * x * t + z * s;
    out[5] = c + y * y * t;
    out[6] = y * z * t - x * s;
    out[7] = (double)(0.0);
    out[8] = z * x * t - y * s;
    out[9] = z * y * t + x * s;
    out[10] = c + z * z * t;
    out[11] = (double)(0.0);
    out[12] = (double)(0.0);
    out[13] = (double)(0.0);
    out[14] = (double)(0.0);
    out[15] = (double)(1.0);
}

__device__ inline void eye16(double* out) {
    int i;
    for (i = 0; i < (16); ++i) {
        out[i] = (double)(0.0);
}
    out[0] = (double)(1.0);
    out[5] = (double)(1.0);
    out[10] = (double)(1.0);
    out[15] = (double)(1.0);
}

__device__ inline void axial3(double* m, double* out) {
    out[0] = (m[2 * 4 + 1] - m[1 * 4 + 2]) * (double)(0.5);
    out[1] = (m[0 * 4 + 2] - m[2 * 4 + 0]) * (double)(0.5);
    out[2] = (m[1 * 4 + 0] - m[0 * 4 + 1]) * (double)(0.5);
}

__device__ inline void apply_point(double* m, double* p, double* out) {
    int i;
    for (i = 0; i < (3); ++i) {
        out[i] = m[i * 4 + 0] * p[0] + m[i * 4 + 1] * p[1] + m[i * 4 + 2] * p[2] + m[i * 4 + 3];
}
}

__device__ inline void rot_cols(double* m, double* v, double* out) {
    int i;
    for (i = 0; i < (3); ++i) {
        out[i] = m[i * 4 + 0] * v[0] + m[i * 4 + 1] * v[1] + m[i * 4 + 2] * v[2];
}
}

__device__ inline void transpose_rot(double* m, double* out) {
    int i;
    int j;
    for (i = 0; i < (16); ++i) {
        out[i] = (double)(0.0);
}
    for (i = 0; i < (3); ++i) {
        for (j = 0; j < (3); ++j) {
            out[i * 4 + j] = m[j * 4 + i];
}
}
    out[15] = (double)(1.0);
}

__device__ inline void load16(double* src, int off, double* out) {
    int i;
    for (i = 0; i < (16); ++i) {
        out[i] = src[off + i];
}
}

__device__ inline long long inverse_spd18(double* a, double* out) {
    int i;
    int j;
    double t;
    int k;
    int col;
    int ii;
    double an;
    double bn;
    double ar;
    double br;
    double l[324];
    for (i = 0; i < (324); ++i) {
        l[i] = (double)(0.0);
}
    for (i = 0; i < (18); ++i) {
        for (j = 0; j < (i + 1); ++j) {
            t =  a[i * 18 + j];
            if (fabs(t - a[j * 18 + i]) > (double)(1e-12)) {
                return 0;
}
            if (isnan(t)) {
                return 0;
}
            for (k = 0; k < (j); ++k) {
                t =  t - l[i * 18 + k] * l[j * 18 + k];
}
            if (i == j) {
                if (! (t > (double)(0.0))) {
                    return 0;
}
                l[i * 18 + j] = sqrt(t);
}
            else {
                l[i * 18 + j] = t / l[j * 18 + j];
}
}
}
    for (col = 0; col < (18); ++col) {
        double y[18];
        double x[18];
        for (i = 0; i < (18); ++i) {
            t =  (double)(0.0);
            if (i == col) {
                t =  (double)(1.0);
}
            for (k = 0; k < (i); ++k) {
                t =  t - l[i * 18 + k] * y[k];
}
            y[i] = t / l[i * 18 + i];
}
        ii =  (int)(17);
        while (ii >= 0) {
            t =  y[ii];
            for (k = (ii + 1); k < (18); ++k) {
                t =  t - l[k * 18 + ii] * x[k];
}
            x[ii] = t / l[ii * 18 + ii];
            out[ii * 18 + col] = x[ii];
            ii =  ii - 1;
}
}
    an =  (double)(0.0);
    bn =  (double)(0.0);
    for (i = 0; i < (18); ++i) {
        ar =  (double)(0.0);
        br =  (double)(0.0);
        for (j = 0; j < (18); ++j) {
            ar =  ar + fabs(a[i * 18 + j]);
            br =  br + fabs(out[i * 18 + j]);
}
        if (ar > an) {
            an =  ar;
}
        if (br > bn) {
            bn =  br;
}
}
    if (isnan(an * bn) || an * bn >= (double)(1e12)) {
        return 0;
}
    return 1;
}

__device__ inline void mv18(double* a, double* x, double* out) {
    int i;
    double s;
    int j;
    for (i = 0; i < (18); ++i) {
        s =  (double)(0.0);
        for (j = 0; j < (18); ++j) {
            s =  s + a[i * 18 + j] * x[j];
}
        out[i] = s;
}
}

__device__ inline double fk_eval(double* q, double* v, double* mdl, int* mdi, double* cst, double* M, double* gv, double* bv, double* fr, double* frd, double* frdd, double* axw, double* axpiv, double* axdir, double* ptp, double* ptJ, double* ptcop, double* ptbias) {
    int nbod;
    int naxes;
    double plane_y;
    double gy;
    int i;
    double potential;
    int b;
    int par;
    double tvx;
    double tvy;
    double tvz;
    double vvx;
    double vvy;
    double vvz;
    int a0;
    int a1;
    int ai;
    int slot;
    double ang;
    double rate;
    int k;
    double wx;
    double wy;
    double wz;
    int j;
    double aij;
    double px;
    double py;
    double pz;
    int idx;
    double rx;
    double ry;
    double rz;
    double s;
    double* Iw;
    double m;
    int nslots;
    int ii;
    int ai_i;
    int si;
    int jj;
    int ai_j;
    int sj;
    double jvd;
    int c;
    double jwd;
    double Iwj;
    int pb;
    int r;
    double gh;
    double gm;
    double dy;
    double a;
    double jx;
    double jy;
    double jz;
    int ax_rot[((OI_ax_rot + 18) - (OI_ax_rot))];
    for (int _si0 = 0; _si0 < ((OI_ax_rot + 18) - (OI_ax_rot)); ++_si0) ax_rot[_si0] = mdi[(OI_ax_rot) + _si0];
    double ax_axis[((OF_ax_axis + 54) - (OF_ax_axis))];
    for (int _si1 = 0; _si1 < ((OF_ax_axis + 54) - (OF_ax_axis)); ++_si1) ax_axis[_si1] = mdl[(OF_ax_axis) + _si1];
    int ax_slot[((OI_ax_slot + 18) - (OI_ax_slot))];
    for (int _si2 = 0; _si2 < ((OI_ax_slot + 18) - (OI_ax_slot)); ++_si2) ax_slot[_si2] = mdi[(OI_ax_slot) + _si2];
    double ax_slope[((OF_ax_slope + 18) - (OF_ax_slope))];
    for (int _si3 = 0; _si3 < ((OF_ax_slope + 18) - (OF_ax_slope)); ++_si3) ax_slope[_si3] = mdl[(OF_ax_slope) + _si3];
    double ax_const[((OF_ax_const + 18) - (OF_ax_const))];
    for (int _si4 = 0; _si4 < ((OF_ax_const + 18) - (OF_ax_const)); ++_si4) ax_const[_si4] = mdl[(OF_ax_const) + _si4];
    int body_axoff[((OI_body_axoff + 15) - (OI_body_axoff))];
    for (int _si5 = 0; _si5 < ((OI_body_axoff + 15) - (OI_body_axoff)); ++_si5) body_axoff[_si5] = mdi[(OI_body_axoff) + _si5];
    int body_parent[((OI_body_parent + 14) - (OI_body_parent))];
    for (int _si6 = 0; _si6 < ((OI_body_parent + 14) - (OI_body_parent)); ++_si6) body_parent[_si6] = mdi[(OI_body_parent) + _si6];
    double body_mass[((OF_body_mass + 14) - (OF_body_mass))];
    for (int _si7 = 0; _si7 < ((OF_body_mass + 14) - (OF_body_mass)); ++_si7) body_mass[_si7] = mdl[(OF_body_mass) + _si7];
    double body_com[((OF_body_com + 42) - (OF_body_com))];
    for (int _si8 = 0; _si8 < ((OF_body_com + 42) - (OF_body_com)); ++_si8) body_com[_si8] = mdl[(OF_body_com) + _si8];
    double body_inertia[((OF_body_inertia + 42) - (OF_body_inertia))];
    for (int _si9 = 0; _si9 < ((OF_body_inertia + 42) - (OF_body_inertia)); ++_si9) body_inertia[_si9] = mdl[(OF_body_inertia) + _si9];
    double body_fp[((OF_body_fp + 224) - (OF_body_fp))];
    for (int _si10 = 0; _si10 < ((OF_body_fp + 224) - (OF_body_fp)); ++_si10) body_fp[_si10] = mdl[(OF_body_fp) + _si10];
    double body_fc[((OF_body_fc + 224) - (OF_body_fc))];
    for (int _si11 = 0; _si11 < ((OF_body_fc + 224) - (OF_body_fc)); ++_si11) body_fc[_si11] = mdl[(OF_body_fc) + _si11];
    int chain_off[((OI_chain_off + 15) - (OI_chain_off))];
    for (int _si12 = 0; _si12 < ((OI_chain_off + 15) - (OI_chain_off)); ++_si12) chain_off[_si12] = mdi[(OI_chain_off) + _si12];
    int chain_ax[((OI_chain_ax + 60) - (OI_chain_ax))];
    for (int _si13 = 0; _si13 < ((OI_chain_ax + 60) - (OI_chain_ax)); ++_si13) chain_ax[_si13] = mdi[(OI_chain_ax) + _si13];
    int pt_body[((OI_pt_body + 8) - (OI_pt_body))];
    for (int _si14 = 0; _si14 < ((OI_pt_body + 8) - (OI_pt_body)); ++_si14) pt_body[_si14] = mdi[(OI_pt_body) + _si14];
    double pt_local[((OF_pt_local + 24) - (OF_pt_local))];
    for (int _si15 = 0; _si15 < ((OF_pt_local + 24) - (OF_pt_local)); ++_si15) pt_local[_si15] = mdl[(OF_pt_local) + _si15];
    double pt_radius[((OF_pt_radius + 8) - (OF_pt_radius))];
    for (int _si16 = 0; _si16 < ((OF_pt_radius + 8) - (OF_pt_radius)); ++_si16) pt_radius[_si16] = mdl[(OF_pt_radius) + _si16];
    nbod =  14;
    naxes =  18;
    plane_y =  cst[CF_plane_y];
    gy =  cst[CF_gy];
    double grav[3];
    grav[0] = (double)(0.0);
    grav[1] = -gy;
    grav[2] = (double)(0.0);
    for (i = 0; i < (18); ++i) {
        gv[i] = (double)(0.0);
        bv[i] = (double)(0.0);
}
    for (i = 0; i < (324); ++i) {
        M[i] = (double)(0.0);
}
    for (i = 0; i < (224); ++i) {
        fr[i] = (double)(0.0);
        frd[i] = (double)(0.0);
        frdd[i] = (double)(0.0);
}
    fr[0] = (double)(1.0);
    fr[5] = (double)(1.0);
    fr[10] = (double)(1.0);
    fr[15] = (double)(1.0);
    frd[0] = (double)(1.0);
    frd[5] = (double)(1.0);
    frd[10] = (double)(1.0);
    frd[15] = (double)(1.0);
    frdd[0] = (double)(1.0);
    frdd[5] = (double)(1.0);
    frdd[10] = (double)(1.0);
    frdd[15] = (double)(1.0);
    for (i = 0; i < (54); ++i) {
        axw[i] = (double)(0.0);
        axpiv[i] = (double)(0.0);
        axdir[i] = (double)(0.0);
}
    potential =  (double)(0.0);
    double one[16];
    double one_dt[16];
    double one_ddt[16];
    double sk[16];
    double motion[16];
    double motion_dt[16];
    double motion_ddt[16];
    double pfp[16];
    double t1[16];
    double t2[16];
    double t3[16];
    double t4[16];
    double fp16[16];
    double fc16[16];
    double rt[16];
    double mtmp[16];
    double mtmp2[16];
    double jv[54];
    double jw[54];
    for (b = (1); b < (nbod); ++b) {
        par =  body_parent[b];
        load16(body_fp, b * 16, fp16);
        load16(body_fc, b * 16, fc16);
        for (i = 0; i < (16); ++i) {
            t1[i] = fr[par * 16 + i];
}
        mm(t1, fp16, pfp);
        eye16(motion);
        eye16(motion_dt);
        eye16(motion_ddt);
        tvx =  (double)(0.0);
        tvy =  (double)(0.0);
        tvz =  (double)(0.0);
        vvx =  (double)(0.0);
        vvy =  (double)(0.0);
        vvz =  (double)(0.0);
        a0 =  body_axoff[b];
        a1 =  body_axoff[b + 1];
        for (ai = (a0); ai < (a1); ++ai) {
            slot =  ax_slot[ai];
            ang =  ax_const[ai];
            rate =  (double)(0.0);
            if (slot >= 0) {
                ang =  ang + ax_slope[ai] * q[slot];
                rate =  ax_slope[ai] * v[slot];
}
            double axis[3];
            axis[0] = ax_axis[ai * 3];
            axis[1] = ax_axis[ai * 3 + 1];
            axis[2] = ax_axis[ai * 3 + 2];
            if (ax_rot[ai] != 0) {
                rot_axis(axis, ang, one);
                for (i = 0; i < (16); ++i) {
                    sk[i] = (double)(0.0);
}
                sk[0 * 4 + 1] = -axis[2];
                sk[0 * 4 + 2] = axis[1];
                sk[1 * 4 + 0] = axis[2];
                sk[1 * 4 + 2] = -axis[0];
                sk[2 * 4 + 0] = -axis[1];
                sk[2 * 4 + 1] = axis[0];
                mm(sk, one, t2);
                for (i = 0; i < (16); ++i) {
                    one_dt[i] = t2[i] * rate;
}
                mm(sk, t2, t3);
                for (i = 0; i < (16); ++i) {
                    one_ddt[i] = t3[i] * rate * rate;
}
                mm(motion, one, t1);
                for (i = 0; i < (16); ++i) {
                    motion[i] = t1[i];
}
                mm(motion_dt, one, t1);
                mm(motion, one_dt, t2);
                for (i = 0; i < (16); ++i) {
                    motion_dt[i] = t1[i] + t2[i];
}
                mm(motion_ddt, one, t1);
                mm(motion_dt, one_dt, t2);
                for (i = 0; i < (16); ++i) {
                    motion_ddt[i] = t1[i] + (double)(2.0) * t2[i];
}
                mm(motion, one_ddt, t3);
                for (i = 0; i < (16); ++i) {
                    motion_ddt[i] = motion_ddt[i] + t3[i];
}
}
            else {
                tvx =  tvx + axis[0] * ang;
                tvy =  tvy + axis[1] * ang;
                tvz =  tvz + axis[2] * ang;
                vvx =  vvx + axis[0] * rate;
                vvy =  vvy + axis[1] * rate;
                vvz =  vvz + axis[2] * rate;
}
}
        for (k = 0; k < (3); ++k) {
            motion[k * 4 + 3] = (double)(0.0);
}
        motion[0 * 4 + 3] = tvx;
        motion[1 * 4 + 3] = tvy;
        motion[2 * 4 + 3] = tvz;
        motion_dt[0 * 4 + 3] = vvx;
        motion_dt[1 * 4 + 3] = vvy;
        motion_dt[2 * 4 + 3] = vvz;
        mm(pfp, motion, t1);
        mm(t1, fc16, t2);
        for (i = 0; i < (16); ++i) {
            fr[b * 16 + i] = t2[i];
}
        mm(pfp, motion_dt, t1);
        mm(t1, fc16, t2);
        for (i = 0; i < (16); ++i) {
            frd[b * 16 + i] = t2[i];
}
        mm(pfp, motion_ddt, t1);
        mm(t1, fc16, t2);
        for (i = 0; i < (16); ++i) {
            frdd[b * 16 + i] = t2[i];
}
        for (ai = (a0); ai < (a1); ++ai) {
            double axis[3];
            axis[0] = ax_axis[ai * 3];
            axis[1] = ax_axis[ai * 3 + 1];
            axis[2] = ax_axis[ai * 3 + 2];
            wx =  (double)(0.0);
            wy =  (double)(0.0);
            wz =  (double)(0.0);
            for (i = 0; i < (3); ++i) {
                for (j = 0; j < (3); ++j) {
                    aij =  pfp[i * 4 + j];
                    if (j == 0) {
                        wx =  wx + aij * axis[0];
}
                    else if (j == 1) {
                        wy =  wy + aij * axis[1];
}
                    else {
                        wz =  wz + aij * axis[2];
}
}
}
            if (ax_rot[ai] != 0) {
                axw[ai * 3] = wx;
                axw[ai * 3 + 1] = wy;
                axw[ai * 3 + 2] = wz;
                px =  pfp[0 * 4 + 3] + (pfp[0 * 4 + 0] * tvx + pfp[0 * 4 + 1] * tvy + pfp[0 * 4 + 2] * tvz);
                py =  pfp[1 * 4 + 3] + (pfp[1 * 4 + 0] * tvx + pfp[1 * 4 + 1] * tvy + pfp[1 * 4 + 2] * tvz);
                pz =  pfp[2 * 4 + 3] + (pfp[2 * 4 + 0] * tvx + pfp[2 * 4 + 1] * tvy + pfp[2 * 4 + 2] * tvz);
                axpiv[ai * 3] = px;
                axpiv[ai * 3 + 1] = py;
                axpiv[ai * 3 + 2] = pz;
}
            else {
                axdir[ai * 3] = wx;
                axdir[ai * 3 + 1] = wy;
                axdir[ai * 3 + 2] = wz;
}
}
        for (i = 0; i < (54); ++i) {
            jv[i] = (double)(0.0);
            jw[i] = (double)(0.0);
}
        double comw[3];
        double com[3];
        com[0] = body_com[b * 3];
        com[1] = body_com[b * 3 + 1];
        com[2] = body_com[b * 3 + 2];
        for (i = 0; i < (16); ++i) {
            t1[i] = fr[b * 16 + i];
}
        apply_point(t1, com, comw);
        for (idx = (chain_off[b]); idx < (chain_off[b + 1]); ++idx) {
            ai =  chain_ax[idx];
            slot =  ax_slot[ai];
            if (slot < 0) {
                continue;
}
            if (ax_rot[ai] != 0) {
                double w[3];
                w[0] = axw[ai * 3];
                w[1] = axw[ai * 3 + 1];
                w[2] = axw[ai * 3 + 2];
                double pv[3];
                pv[0] = axpiv[ai * 3];
                pv[1] = axpiv[ai * 3 + 1];
                pv[2] = axpiv[ai * 3 + 2];
                rx =  comw[0] - pv[0];
                ry =  comw[1] - pv[1];
                rz =  comw[2] - pv[2];
                jv[slot * 3] = jv[slot * 3] + (w[1] * rz - w[2] * ry);
                jv[slot * 3 + 1] = jv[slot * 3 + 1] + (w[2] * rx - w[0] * rz);
                jv[slot * 3 + 2] = jv[slot * 3 + 2] + (w[0] * ry - w[1] * rx);
                jw[slot * 3] = jw[slot * 3] + w[0];
                jw[slot * 3 + 1] = jw[slot * 3 + 1] + w[1];
                jw[slot * 3 + 2] = jw[slot * 3 + 2] + w[2];
}
            else {
                jv[slot * 3] = jv[slot * 3] + axdir[ai * 3];
                jv[slot * 3 + 1] = jv[slot * 3 + 1] + axdir[ai * 3 + 1];
                jv[slot * 3 + 2] = jv[slot * 3 + 2] + axdir[ai * 3 + 2];
}
}
        for (i = 0; i < (16); ++i) {
            t1[i] = fr[b * 16 + i];
}
        for (i = 0; i < (16); ++i) {
            t2[i] = frd[b * 16 + i];
}
        transpose_rot(t1, rt);
        mm(t2, rt, mtmp);
        double omega[3];
        axial3(mtmp, omega);
        for (i = 0; i < (16); ++i) {
            t3[i] = frdd[b * 16 + i];
}
        mm(t3, rt, mtmp);
        transpose_rot(t2, rt);
        mm(t2, rt, mtmp2);
        for (i = 0; i < (3); ++i) {
            for (j = 0; j < (3); ++j) {
                mtmp[i * 4 + j] = mtmp[i * 4 + j] + mtmp2[i * 4 + j];
}
}
        double alpha[3];
        axial3(mtmp, alpha);
        double acc_com[3];
        double comloc[3];
        comloc[0] = body_com[b * 3];
        comloc[1] = body_com[b * 3 + 1];
        comloc[2] = body_com[b * 3 + 2];
        for (i = 0; i < (16); ++i) {
            t3[i] = frdd[b * 16 + i];
}
        apply_point(t3, comloc, acc_com);
        double It[3];
        It[0] = body_inertia[b * 3];
        It[1] = body_inertia[b * 3 + 1];
        It[2] = body_inertia[b * 3 + 2];
        for (i = 0; i < (16); ++i) {
            t1[i] = fr[b * 16 + i];
}
        for (i = 0; i < (16); ++i) {
            t2[i] = (double)(0.0);
}
        for (i = 0; i < (3); ++i) {
            for (j = 0; j < (3); ++j) {
                s =  (double)(0.0);
                for (k = 0; k < (3); ++k) {
                    s =  s + t1[i * 4 + k] * (It[k] * t1[j * 4 + k]);
}
                t2[i * 4 + j] = s;
}
}
        Iw =  t2;
        double Iwom[3];
        for (i = 0; i < (3); ++i) {
            Iwom[i] = Iw[i * 4 + 0] * omega[0] + Iw[i * 4 + 1] * omega[1] + Iw[i * 4 + 2] * omega[2];
}
        double moment[3];
        moment[0] = Iw[0 * 4 + 0] * alpha[0] + Iw[0 * 4 + 1] * alpha[1] + Iw[0 * 4 + 2] * alpha[2] + (omega[1] * Iwom[2] - omega[2] * Iwom[1]);
        moment[1] = Iw[1 * 4 + 0] * alpha[0] + Iw[1 * 4 + 1] * alpha[1] + Iw[1 * 4 + 2] * alpha[2] + (omega[2] * Iwom[0] - omega[0] * Iwom[2]);
        moment[2] = Iw[2 * 4 + 0] * alpha[0] + Iw[2 * 4 + 1] * alpha[1] + Iw[2 * 4 + 2] * alpha[2] + (omega[0] * Iwom[1] - omega[1] * Iwom[0]);
        m =  body_mass[b];
        if (m > (double)(0.0)) {
            nslots =  chain_off[b + 1] - chain_off[b];
            for (ii = 0; ii < (nslots); ++ii) {
                ai_i =  chain_ax[chain_off[b] + ii];
                si =  ax_slot[ai_i];
                if (si < 0) {
                    continue;
}
                for (jj = 0; jj < (nslots); ++jj) {
                    ai_j =  chain_ax[chain_off[b] + jj];
                    sj =  ax_slot[ai_j];
                    if (sj < 0) {
                        continue;
}
                    jvd =  (double)(0.0);
                    for (c = 0; c < (3); ++c) {
                        jvd =  jvd + jv[si * 3 + c] * jv[sj * 3 + c];
}
                    jwd =  (double)(0.0);
                    for (c = 0; c < (3); ++c) {
                        Iwj =  Iw[c * 4 + 0] * jw[sj * 3 + 0] + Iw[c * 4 + 1] * jw[sj * 3 + 1] + Iw[c * 4 + 2] * jw[sj * 3 + 2];
                        jwd =  jwd + jw[si * 3 + c] * Iwj;
}
                    M[si * 18 + sj] = M[si * 18 + sj] + m * jvd + jwd;
}
}
            for (ii = 0; ii < (nslots); ++ii) {
                ai_i =  chain_ax[chain_off[b] + ii];
                si =  ax_slot[ai_i];
                if (si < 0) {
                    continue;
}
                gv[si] = gv[si] + m * (jv[si * 3 + 0] * grav[0] + jv[si * 3 + 1] * grav[1] + jv[si * 3 + 2] * grav[2]);
                bv[si] = bv[si] + m * (jv[si * 3 + 0] * acc_com[0] + jv[si * 3 + 1] * acc_com[1] + jv[si * 3 + 2] * acc_com[2]);
                bv[si] = bv[si] + (jw[si * 3 + 0] * moment[0] + jw[si * 3 + 1] * moment[1] + jw[si * 3 + 2] * moment[2]);
}
            potential =  potential - m * (grav[0] * comw[0] + grav[1] * comw[1] + grav[2] * comw[2]);
}
}
    for (k = 0; k < (8); ++k) {
        pb =  pt_body[k];
        double p[3];
        p[0] = pt_local[k * 3];
        p[1] = pt_local[k * 3 + 1];
        p[2] = pt_local[k * 3 + 2];
        for (i = 0; i < (16); ++i) {
            t1[i] = fr[pb * 16 + i];
}
        double out[3];
        apply_point(t1, p, out);
        ptp[k * 3] = out[0];
        ptp[k * 3 + 1] = out[1];
        ptp[k * 3 + 2] = out[2];
}
    for (r = 0; r < (4); ++r) {
        k =  r * 2;
        gh =  ptp[k * 3 + 1] + pt_radius[k] - plane_y;
        gm =  ptp[(k + 1) * 3 + 1] + pt_radius[k + 1] - plane_y;
        dy =  ptp[(k + 1) * 3 + 1] - ptp[k * 3 + 1];
        a =  (double)(0.5);
        if (! ((gh <= (double)(2e-6) && gm <= (double)(2e-6)) || fabs(dy) < (double)(1e-8))) {
            if (dy < (double)(0.0)) {
                a =  (double)(1.0);
}
            else {
                a =  (double)(0.0);
}
}
        double loc[3];
        for (c = 0; c < (3); ++c) {
            loc[c] = pt_local[k * 3 + c] + (pt_local[(k + 1) * 3 + c] - pt_local[k * 3 + c]) * a;
}
        ptcop[r * 3] = loc[0];
        ptcop[r * 3 + 1] = loc[1];
        ptcop[r * 3 + 2] = loc[2];
        pb =  pt_body[k];
        for (i = 0; i < (16); ++i) {
            t1[i] = fr[pb * 16 + i];
}
        double solew[3];
        apply_point(t1, loc, solew);
        double t3v[3];
        for (i = 0; i < (16); ++i) {
            t4[i] = frdd[pb * 16 + i];
}
        apply_point(t4, loc, t3v);
        ptbias[r * 3] = t3v[0];
        ptbias[r * 3 + 1] = t3v[1];
        ptbias[r * 3 + 2] = t3v[2];
        for (c = 0; c < (18); ++c) {
            ptJ[(r * 3 + 0) * 18 + c] = (double)(0.0);
            ptJ[(r * 3 + 1) * 18 + c] = (double)(0.0);
            ptJ[(r * 3 + 2) * 18 + c] = (double)(0.0);
}
        for (idx = (chain_off[pb]); idx < (chain_off[pb + 1]); ++idx) {
            ai =  chain_ax[idx];
            slot =  ax_slot[ai];
            if (slot < 0) {
                continue;
}
            if (ax_rot[ai] != 0) {
                double w[3];
                w[0] = axw[ai * 3];
                w[1] = axw[ai * 3 + 1];
                w[2] = axw[ai * 3 + 2];
                double pv[3];
                pv[0] = axpiv[ai * 3];
                pv[1] = axpiv[ai * 3 + 1];
                pv[2] = axpiv[ai * 3 + 2];
                rx =  solew[0] - pv[0];
                ry =  solew[1] - pv[1];
                rz =  solew[2] - pv[2];
                jx =  w[1] * rz - w[2] * ry;
                jy =  w[2] * rx - w[0] * rz;
                jz =  w[0] * ry - w[1] * rx;
                ptJ[(r * 3 + 0) * 18 + slot] = ptJ[(r * 3 + 0) * 18 + slot] + jx;
                ptJ[(r * 3 + 1) * 18 + slot] = ptJ[(r * 3 + 1) * 18 + slot] + jy;
                ptJ[(r * 3 + 2) * 18 + slot] = ptJ[(r * 3 + 2) * 18 + slot] + jz;
}
            else {
                ptJ[(r * 3 + 0) * 18 + slot] = ptJ[(r * 3 + 0) * 18 + slot] + axdir[ai * 3];
                ptJ[(r * 3 + 1) * 18 + slot] = ptJ[(r * 3 + 1) * 18 + slot] + axdir[ai * 3 + 1];
                ptJ[(r * 3 + 2) * 18 + slot] = ptJ[(r * 3 + 2) * 18 + slot] + axdir[ai * 3 + 2];
}
}
}
    return potential;
}

__device__ inline double gap_of_k(double* ptp, double* pt_radius, int k, double plane_y) {
    int h;
    double gh;
    double gm;
    h =  k - (k % 2);
    gh =  ptp[h * 3 + 1] + pt_radius[h] - plane_y;
    gm =  ptp[(h + 1) * 3 + 1] + pt_radius[h + 1] - plane_y;
    if (gh < gm) {
        return gh;
}
    return gm;
}

__device__ inline double row_dot(double* row, double* x) {
    double s;
    int i;
    s =  (double)(0.0);
    for (i = 0; i < (18); ++i) {
        s =  s + row[i] * x[i];
}
    return s;
}

__device__ inline void mat_vec(double* inv, double* row, double* out) {
    int i;
    double s;
    int j;
    for (i = 0; i < (18); ++i) {
        s =  (double)(0.0);
        for (j = 0; j < (18); ++j) {
            s =  s + inv[i * 18 + j] * row[j];
}
        out[i] = s;
}
}

__device__ inline void rows_row(double* rows, int k, double* out) {
    int i;
    for (i = 0; i < (18); ++i) {
        out[i] = rows[k * 18 + i];
}
}

__device__ inline long long gram_factor10(double* g, int k, double* rhs, double* lam) {
    double scale;
    int i;
    double d;
    int j;
    double avg;
    double t;
    int m;
    int col;
    int ii;
    scale =  (double)(0.0);
    for (i = 0; i < (k); ++i) {
        d =  g[i * k + i];
        if (d < (double)(0.0)) {
            d =  -d;
}
        if (d > scale) {
            scale =  d;
}
}
    if (! (scale > (double)(0.0))) {
        return 0;
}
    for (i = 0; i < (k); ++i) {
        for (j = 0; j < (i); ++j) {
            avg =  (g[i * k + j] + g[j * k + i]) * (double)(0.5);
            g[i * k + j] = avg;
            g[j * k + i] = avg;
}
}
    double l[100];
    for (i = 0; i < (k); ++i) {
        for (j = 0; j < (i + 1); ++j) {
            t =  g[i * k + j];
            for (m = 0; m < (j); ++m) {
                t =  t - l[i * k + m] * l[j * k + m];
}
            if (i == j) {
                if (! (t > (double)(1e-9) * scale)) {
                    return 0;
}
                l[i * k + j] = sqrt(t);
}
            else {
                l[i * k + j] = t / l[j * k + j];
}
}
}
    for (i = 0; i < (k); ++i) {
        lam[i] = (double)(0.0);
}
    for (col = 0; col < (k); ++col) {
        double y[10];
        double x[10];
        for (i = 0; i < (k); ++i) {
            t =  (double)(0.0);
            if (col == i) {
                t =  (double)(1.0);
}
            for (m = 0; m < (i); ++m) {
                t =  t - l[i * k + m] * y[m];
}
            y[i] = t / l[i * k + i];
}
        ii =  k - 1;
        while (ii >= 0) {
            t =  y[ii];
            for (m = (ii + 1); m < (k); ++m) {
                t =  t - l[m * k + ii] * x[m];
}
            x[ii] = t / l[ii * k + ii];
            lam[ii] = lam[ii] + x[ii] * rhs[col];
            ii =  ii - 1;
}
}
    return 1;
}

__device__ inline long long project_rows(double* initial, double* inv, double* rows, double* floors, int R, int n_stops, double* p_out, double* multipliers) {
    int tier;
    int mask;
    int skip;
    int holds;
    int k;
    int cnt;
    int legal;
    int allok;
    double tol;
    int i;
    int a;
    int b;
    double s;
    int valid;
    double l;
    double got;
    if (R < 1 || R > 10) {
        return 0;
}
    tier =  (int)(0);
    while (tier <= 1) {
        mask =  (int)(0);
        while (mask < (1 << R)) {
            skip =  (int)(0);
            if (mask != 0) {
                holds =  (int)(1);
                for (k = 0; k < (n_stops); ++k) {
                    if (! ((mask >> k) & 1)) {
                        holds =  0;
}
}
                if (holds != (int)(tier == 0)) {
                    skip =  1;
}
}
            else {
                if (tier != 0) {
                    skip =  1;
}
}
            if (skip == 0) {
                int act[10];
                cnt =  (int)(0);
                for (k = 0; k < (R); ++k) {
                    if ((mask >> k) & 1) {
                        act[cnt] = k;
                        cnt =  cnt + 1;
}
}
                legal =  (int)(1);
                if (cnt > 18) {
                    legal =  0;
}
                if (legal == 1) {
                    if (cnt == 0) {
                        allok =  (int)(1);
                        double rk[18];
                        for (k = 0; k < (R); ++k) {
                            rows_row(rows, k, rk);
                            tol =  (double)(1e-9) * ((double)(1.0) + fabs(floors[k]));
                            if (row_dot(rk, initial) < floors[k] - tol) {
                                allok =  0;
}
}
                        if (allok == 1) {
                            for (i = 0; i < (18); ++i) {
                                p_out[i] = (double)(0.0);
}
                            for (k = 0; k < (R); ++k) {
                                multipliers[k] = (double)(0.0);
}
                            return 1;
}
}
                    else {
                        double gram[100];
                        double rhs[10];
                        double ra[18];
                        double rb[18];
                        double ia[18];
                        for (a = 0; a < (cnt); ++a) {
                            for (b = 0; b < (cnt); ++b) {
                                rows_row(rows, act[a], ra);
                                rows_row(rows, act[b], rb);
                                mat_vec(inv, ra, ia);
                                s =  (double)(0.0);
                                for (i = 0; i < (18); ++i) {
                                    s =  s + ia[i] * rb[i];
}
                                gram[a * cnt + b] = s;
}
                            rows_row(rows, act[a], ra);
                            rhs[a] = floors[act[a]] - row_dot(ra, initial);
}
                        double lam[10];
                        if (gram_factor10(gram, cnt, rhs, lam) == 1) {
                            valid =  (int)(1);
                            for (k = 0; k < (cnt); ++k) {
                                if (lam[k] < (double)(-1e-10)) {
                                    valid =  0;
}
}
                            if (valid == 1) {
                                for (i = 0; i < (18); ++i) {
                                    p_out[i] = (double)(0.0);
}
                                for (k = 0; k < (cnt); ++k) {
                                    l =  lam[k];
                                    if (l < (double)(0.0)) {
                                        l =  (double)(0.0);
}
                                    double rk[18];
                                    rows_row(rows, act[k], rk);
                                    for (i = 0; i < (18); ++i) {
                                        p_out[i] = p_out[i] + l * rk[i];
}
}
                                double chg[18];
                                mat_vec(inv, p_out, chg);
                                double rk[18];
                                for (k = 0; k < (R); ++k) {
                                    tol =  (double)(1e-9) * ((double)(1.0) + fabs(floors[k]));
                                    rows_row(rows, k, rk);
                                    got =  row_dot(rk, initial) + row_dot(rk, chg);
                                    if (got < floors[k] - tol) {
                                        valid =  0;
}
}
                                if (valid == 1) {
                                    for (k = 0; k < (R); ++k) {
                                        multipliers[k] = (double)(0.0);
}
                                    for (k = 0; k < (cnt); ++k) {
                                        l =  lam[k];
                                        if (l < (double)(0.0)) {
                                            l =  (double)(0.0);
}
                                        multipliers[act[k]] = l;
}
                                    return 1;
}
}
}
}
}
}
            mask =  mask + 1;
}
        tier =  tier + 1;
}
    return 0;
}

__device__ inline void friction_solve(double* initial, double* inv, double* row_n, double* row_t, double floor_n, double floor_t, double mu, double slip_sign, double* force, double* ln, double* lt, int* mode) {
    int i;
    double A;
    double B;
    double C;
    double rn;
    double rt;
    double det;
    double nn;
    double t;
    double at;
    double s;
    double den;
    for (i = 0; i < (18); ++i) {
        force[i] = (double)(0.0);
}
    ln[0] = (double)(0.0);
    lt[0] = (double)(0.0);
    mode[0] = 0;
    double rn_v[18];
    mat_vec(inv, row_n, rn_v);
    double rt_v[18];
    mat_vec(inv, row_t, rt_v);
    A =  row_dot(row_n, rn_v);
    B =  row_dot(row_n, rt_v);
    C =  row_dot(row_t, rt_v);
    rn =  -(row_dot(row_n, initial) - floor_n);
    rt =  -(row_dot(row_t, initial) - floor_t);
    det =  A * C - B * B;
    if (det > (double)(1e-18)) {
        nn =  (rn * C - rt * B) / det;
        t =  (rt * A - rn * B) / det;
        at =  t;
        if (at < (double)(0.0)) {
            at =  -at;
}
        if (nn >= (double)(0.0) && at <= mu * nn + (double)(1e-12) && (slip_sign == 0 || t * (double)(slip_sign) <= (double)(0.0))) {
            for (i = 0; i < (18); ++i) {
                force[i] = row_n[i] * nn + row_t[i] * t;
}
            ln[0] = nn;
            lt[0] = t;
            mode[0] = 1;
            return;
}
}
    s =  (double)(0.0);
    if (slip_sign != 0) {
        s =  (double)(slip_sign);
}
    else {
        if (rt >= (double)(0.0)) {
            s =  (double)(-1.0);
}
        else {
            s =  (double)(1.0);
}
}
    den =  A - s * mu * B;
    if (den <= (double)(1e-12)) {
        mode[0] = -1;
        return;
}
    nn =  rn / den;
    t =  -s * mu * nn;
    if (nn >= (double)(0.0)) {
        for (i = 0; i < (18); ++i) {
            force[i] = row_n[i] * nn + row_t[i] * t;
}
        ln[0] = nn;
        lt[0] = t;
        mode[0] = 2;
        return;
}
    ln[0] = (double)(0.0);
    lt[0] = (double)(0.0);
    mode[0] = 0;
}

__device__ inline long long rate(double* q, double* v, double* tau, int* live, int* plane, double* mdl, double* cst, double* M, double* gv, double* bv, double* fr, double* frd, double* frdd, double* axw, double* axpiv, double* axdir, double* ptp, double* ptJ, double* ptcop, double* ptbias, double* inv, double* free, double* rq, double* rv, int* mdi, int* csti) {
    double pot;
    int i;
    int d;
    int c;
    int R;
    int n_stops;
    int stop;
    double speed_scale;
    double gate;
    int r;
    double g;
    double bx;
    double by;
    double bz;
    double svx;
    double svz;
    double planar;
    double dir_x;
    double dir_z;
    int slip_sign;
    double d1;
    double d2;
    double accel;
    double floor_k;
    double pt_radius_g[((OF_pt_radius + 8) - (OF_pt_radius))];
    for (int _si0 = 0; _si0 < ((OF_pt_radius + 8) - (OF_pt_radius)); ++_si0) pt_radius_g[_si0] = mdl[(OF_pt_radius) + _si0];
    pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
    if (inverse_spd18(M, inv) == 0) {
        return 8;
}
    for (i = 0; i < (18); ++i) {
        free[i] = gv[i] - bv[i];
        rq[i] = (double)(0.0);
}
    for (d = 0; d < (12); ++d) {
        c =  mdi[OI_drive_coord + d];
        free[c] = free[c] + tau[c] - mdl[OF_drive_damping + d] * v[c];
}
    mat_vec(inv, free, free);
    double rows[180];
    double floors[10];
    R =  (int)(0);
    n_stops =  (int)(0);
    stop =  (int)(0);
    double jn[18];
    for (d = 0; d < (12); ++d) {
        c =  mdi[OI_drive_coord + d];
        jn[c] = (double)(0.0);
        if (fabs(q[c] - mdl[OF_lower + c]) < (double)(1e-10)) {
            jn[c] = (double)(1.0);
}
        else if (fabs(q[c] - mdl[OF_upper + c]) < (double)(1e-10)) {
            jn[c] = (double)(-1.0);
}
}
    speed_scale =  (double)(0.0);
    for (d = 0; d < (12); ++d) {
        speed_scale =  speed_scale + fabs(v[mdi[OI_drive_coord + d]]);
}
    gate =  (double)(1e-6) + (double)(1e-3) * speed_scale;
    for (d = 0; d < (12); ++d) {
        c =  mdi[OI_drive_coord + d];
        if (jn[c] != (double)(0.0) && fabs(v[c]) <= (double)(1e-9)) {
            if (R >= 10) {
                return 5;
}
            for (i = 0; i < (18); ++i) {
                rows[R * 18 + i] = (double)(0.0);
}
            rows[R * 18 + c] = jn[c];
            floors[R] = (double)(0.0);
            R =  R + 1;
            n_stops =  n_stops + 1;
            stop =  1;
}
}
    int touching[4];
    int mode_k[4];
    double rn[18];
    for (r = 0; r < (4); ++r) {
        for (i = 0; i < (18); ++i) {
            rn[i] = ptJ[(r * 3 + 1) * 18 + i];
}
        g =  gap_of_k(ptp, pt_radius_g, r * 2, cst[CF_plane_y]);
        touching[r] = 0;
        if (plane[r] != 0) {
            touching[r] = 1;
}
        else if (live[r] != 0 && g <= cst[CF_k_touch] && row_dot(rn, v) <= gate) {
            touching[r] = 1;
}
}
    if (csti[CI_contact] != 0 && cst[CF_mu] > (double)(0.0) && stop == 0) {
        double jt1[18];
        double jt2[18];
        double row_t[18];
        double force[18];
        double corr[18];
        double ln[1];
        double lt[1];
        int md[1];
        for (r = 0; r < (4); ++r) {
            if (touching[r] == 0) {
                continue;
}
            for (i = 0; i < (18); ++i) {
                jt1[i] = ptJ[(r * 3 + 0) * 18 + i];
                jt2[i] = ptJ[(r * 3 + 2) * 18 + i];
}
            bx =  ptbias[r * 3];
            by =  ptbias[r * 3 + 1];
            bz =  ptbias[r * 3 + 2];
            svx =  row_dot(jt1, v);
            svz =  row_dot(jt2, v);
            planar =  sqrt(svx * svx + svz * svz);
            dir_x =  (double)(0.0);
            dir_z =  (double)(0.0);
            slip_sign =  (int)(0);
            if (planar > cst[CF_k_slip]) {
                dir_x =  svx / planar;
                dir_z =  svz / planar;
                slip_sign =  1;
}
            else {
                d1 =  bx;
                d2 =  bz;
                for (i = 0; i < (18); ++i) {
                    d1 =  d1 + jt1[i] * free[i];
                    d2 =  d2 + jt2[i] * free[i];
}
                accel =  sqrt(d1 * d1 + d2 * d2);
                if (accel > (double)(1e-9)) {
                    dir_x =  d1 / accel;
                    dir_z =  d2 / accel;
                    slip_sign =  1;
}
}
            if (dir_x == (double)(0.0) && dir_z == (double)(0.0)) {
                continue;
}
            for (i = 0; i < (18); ++i) {
                row_t[i] = dir_x * jt1[i] + dir_z * jt2[i];
}
            friction_solve(free, inv, rn, row_t, -by, -(dir_x * bx + dir_z * bz), cst[CF_mu], slip_sign, force, ln, lt, md);
            if (md[0] > 0) {
                mat_vec(inv, force, corr);
                for (i = 0; i < (18); ++i) {
                    free[i] = free[i] + corr[i];
}
                mode_k[r] = md[0];
}
}
}
    for (r = 0; r < (4); ++r) {
        if (touching[r] == 0) {
            continue;
}
        for (i = 0; i < (18); ++i) {
            rn[i] = ptJ[(r * 3 + 1) * 18 + i];
}
        floor_k =  -ptbias[r * 3 + 1];
        if (mode_k[r] != 0 && row_dot(rn, free) >= floor_k - (double)(1e-9)) {
            continue;
}
        if (R >= 10) {
            return 5;
}
        for (i = 0; i < (18); ++i) {
            rows[R * 18 + i] = rn[i];
}
        floors[R] = floor_k;
        R =  R + 1;
}
    if (R > 0) {
        double p[18];
        double mult[10];
        if (project_rows(free, inv, rows, floors, R, n_stops, p, mult) == 0) {
            return 5;
}
        double corr[18];
        mat_vec(inv, p, corr);
        for (i = 0; i < (18); ++i) {
            free[i] = free[i] + corr[i];
}
}
    for (i = 0; i < (18); ++i) {
        rv[i] = free[i];
        rq[i] = v[i];
}
    return 0;
}

__device__ inline long long free_step(double* q0, double* v0, double* w0, double* tau, int* live, int h, double* mdl, double* cst, double* M, double* gv, double* bv, double* fr, double* frd, double* frdd, double* axw, double* axpiv, double* axdir, double* ptp, double* ptJ, double* ptcop, double* ptbias, double* inv, double* free, double* srq, double* srv, double* qa, double* va, double* qb, double* vb, double* qc, double* vc, double* qd, double* vd, double* q1, double* v1, double* w1, int* mdi, int* csti) {
    double pot;
    double speed_scale;
    int d;
    double gate;
    int r;
    int i;
    double g;
    double rc;
    double half;
    double sixth;
    double pt_radius_g[((OF_pt_radius + 8) - (OF_pt_radius))];
    for (int _si0 = 0; _si0 < ((OF_pt_radius + 8) - (OF_pt_radius)); ++_si0) pt_radius_g[_si0] = mdl[(OF_pt_radius) + _si0];
    double rq[18];
    double rv[18];
    int plane[4];
    pot =  fk_eval(q0,  v0, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
    speed_scale =  (double)(0.0);
    for (d = 0; d < (12); ++d) {
        speed_scale =  speed_scale + fabs(v0[mdi[OI_drive_coord + d]]);
}
    gate =  (double)(1e-6) + (double)(1e-3) * speed_scale;
    double rn[18];
    for (r = 0; r < (4); ++r) {
        for (i = 0; i < (18); ++i) {
            rn[i] = ptJ[(r * 3 + 1) * 18 + i];
}
        g =  gap_of_k(ptp, pt_radius_g, r * 2, cst[CF_plane_y]);
        if (live[r] != 0 && g <= cst[CF_k_touch] && row_dot(rn, v0) <= gate) {
            plane[r] = 1;
}
}
    rc =  rate(q0, v0, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, csti, mdi);
    if (rc != 0) {
        return rc;
}
    half =  h * (double)(0.5);
    for (i = 0; i < (18); ++i) {
        qb[i] = q0[i] + qa[i] * half;
        vb[i] = v0[i] + va[i] * half;
}
    rc =  rate(qb, vb, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, csti, mdi);
    if (rc != 0) {
        return rc;
}
    double brq[18];
    double brv[18];
    for (i = 0; i < (18); ++i) {
        brq[i] = qb[i];
        brv[i] = vb[i];
}
    for (i = 0; i < (18); ++i) {
        qc[i] = q0[i] + brq[i] * half;
        vc[i] = v0[i] + brv[i] * half;
}
    rc =  rate(qc, vc, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, csti, mdi);
    if (rc != 0) {
        return rc;
}
    double crq[18];
    double crv[18];
    for (i = 0; i < (18); ++i) {
        crq[i] = qc[i];
        crv[i] = vc[i];
}
    for (i = 0; i < (18); ++i) {
        qd[i] = q0[i] + crq[i] * h;
        vd[i] = v0[i] + crv[i] * h;
}
    rc =  rate(qd, vd, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, csti, mdi);
    if (rc != 0) {
        return rc;
}
    double drq[18];
    double drv[18];
    for (i = 0; i < (18); ++i) {
        drq[i] = qd[i];
        drv[i] = vd[i];
}
    sixth =  h / (double)(6.0);
    for (i = 0; i < (18); ++i) {
        q1[i] = q0[i] + sixth * (qa[i] + (double)(2.0) * brq[i] + (double)(2.0) * crq[i] + drq[i]);
        v1[i] = v0[i] + sixth * (va[i] + (double)(2.0) * brv[i] + (double)(2.0) * crv[i] + drv[i]);
        w1[i] = w0[i] + tau[i] * (q1[i] - q0[i]);
}
    return 0;
}

__device__ inline long long gram_factor4(double* g, int k, double* rhs, double* lam) {
    double scale;
    int i;
    double d;
    int j;
    double t;
    int m;
    int col;
    int ii;
    scale =  (double)(0.0);
    for (i = 0; i < (k); ++i) {
        d =  g[i * k + i];
        if (d < (double)(0.0)) {
            d =  -d;
}
        if (d > scale) {
            scale =  d;
}
}
    if (! (scale > (double)(0.0))) {
        return 0;
}
    double l[16];
    for (i = 0; i < (k); ++i) {
        for (j = 0; j < (i + 1); ++j) {
            t =  g[i * k + j];
            for (m = 0; m < (j); ++m) {
                t =  t - l[i * k + m] * l[j * k + m];
}
            if (i == j) {
                if (! (t > (double)(1e-9) * scale)) {
                    return 0;
}
                l[i * k + j] = sqrt(t);
}
            else {
                l[i * k + j] = t / l[j * k + j];
}
}
}
    for (i = 0; i < (k); ++i) {
        lam[i] = (double)(0.0);
}
    for (col = 0; col < (k); ++col) {
        double y[4];
        double x[4];
        for (i = 0; i < (k); ++i) {
            t =  (double)(0.0);
            if (col == i) {
                t =  (double)(1.0);
}
            for (m = 0; m < (i); ++m) {
                t =  t - l[i * k + m] * y[m];
}
            y[i] = t / l[i * k + i];
}
        ii =  k - 1;
        while (ii >= 0) {
            t =  y[ii];
            for (m = (ii + 1); m < (k); ++m) {
                t =  t - l[m * k + ii] * x[m];
}
            x[ii] = t / l[ii * k + ii];
            lam[ii] = lam[ii] + x[ii] * rhs[col];
            ii =  ii - 1;
}
}
    return 1;
}

__device__ inline double impact(double* q, double* v, double* mdl, double* cst, double* M, double* gv, double* bv, double* fr, double* frd, double* frdd, double* axw, double* axpiv, double* axdir, double* ptp, double* ptJ, double* ptcop, double* ptbias, double* inv, double* free, int* rc, int* mdi, int* csti) {
    double pot;
    double caught;
    int R;
    int n_stops;
    int d;
    int c;
    int i;
    int r;
    double g;
    double closing;
    double svx;
    double svz;
    double planar;
    int npen;
    int a;
    int b;
    double s;
    double dq_max;
    double pt_radius_g[((OF_pt_radius + 8) - (OF_pt_radius))];
    for (int _si0 = 0; _si0 < ((OF_pt_radius + 8) - (OF_pt_radius)); ++_si0) pt_radius_g[_si0] = mdl[(OF_pt_radius) + _si0];
    pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
    if (inverse_spd18(M, inv) == 0) {
        rc[0] = 8;
        return (double)(0.0);
}
    caught =  (double)(0.0);
    double rows[180];
    double floors[10];
    R =  (int)(0);
    n_stops =  (int)(0);
    double jn[18];
    for (d = 0; d < (12); ++d) {
        c =  mdi[OI_drive_coord + d];
        jn[c] = (double)(0.0);
        if (fabs(q[c] - mdl[OF_lower + c]) < (double)(1e-10)) {
            jn[c] = (double)(1.0);
}
        else if (fabs(q[c] - mdl[OF_upper + c]) < (double)(1e-10)) {
            jn[c] = (double)(-1.0);
}
}
    for (d = 0; d < (12); ++d) {
        c =  mdi[OI_drive_coord + d];
        if (jn[c] != (double)(0.0)) {
            if (R >= 10) {
                rc[0] = 5;
                return (double)(0.0);
}
            for (i = 0; i < (18); ++i) {
                rows[R * 18 + i] = (double)(0.0);
}
            rows[R * 18 + c] = jn[c];
            floors[R] = (double)(0.0);
            R =  R + 1;
            n_stops =  n_stops + 1;
}
}
    int touching[4];
    for (r = 0; r < (4); ++r) {
        g =  gap_of_k(ptp, pt_radius_g, r * 2, cst[CF_plane_y]);
        touching[r] = ((csti[CI_contact] != 0 && g <= cst[CF_k_touch])) ? ((int)(1)) : ((int)(0));
}
    double rn[18];
    if (cst[CF_mu] > (double)(0.0) && n_stops == 0 && csti[CI_contact] != 0) {
        double jt1[18];
        double jt2[18];
        double row_t[18];
        double force[18];
        double corr[18];
        double ln[1];
        double lt[1];
        int md[1];
        for (r = 0; r < (4); ++r) {
            if (touching[r] == 0) {
                continue;
}
            for (i = 0; i < (18); ++i) {
                jt1[i] = ptJ[(r * 3 + 0) * 18 + i];
                jt2[i] = ptJ[(r * 3 + 2) * 18 + i];
                rn[i] = ptJ[(r * 3 + 1) * 18 + i];
}
            closing =  row_dot(rn, v);
            if (closing > (double)(-1e-12)) {
                continue;
}
            svx =  row_dot(jt1, v);
            svz =  row_dot(jt2, v);
            planar =  sqrt(svx * svx + svz * svz);
            if (planar <= cst[CF_k_slip]) {
                continue;
}
            for (i = 0; i < (18); ++i) {
                row_t[i] = (svx * jt1[i] + svz * jt2[i]) / planar;
}
            friction_solve(v, inv, rn, row_t, (double)(0.0), (double)(0.0), cst[CF_mu], 1, force, ln, lt, md);
            if (md[0] > 0) {
                mat_vec(inv, force, corr);
                for (i = 0; i < (18); ++i) {
                    v[i] = v[i] + corr[i];
}
                if (ln[0] > caught) {
                    caught =  ln[0];
}
}
}
}
    for (r = 0; r < (4); ++r) {
        if (touching[r] == 0) {
            continue;
}
        if (R >= 10) {
            rc[0] = 5;
            return (double)(0.0);
}
        for (i = 0; i < (18); ++i) {
            rows[R * 18 + i] = ptJ[(r * 3 + 1) * 18 + i];
}
        floors[R] = (double)(0.0);
        R =  R + 1;
}
    if (R > 0) {
        double p[18];
        double mult[10];
        if (project_rows(v, inv, rows, floors, R, n_stops, p, mult) == 0) {
            rc[0] = 5;
            return (double)(0.0);
}
        double corr[18];
        mat_vec(inv, p, corr);
        for (i = 0; i < (18); ++i) {
            v[i] = v[i] + corr[i];
}
}
    pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
    int pen[4];
    npen =  (int)(0);
    double gaps[4];
    for (r = 0; r < (4); ++r) {
        g =  gap_of_k(ptp, pt_radius_g, r * 2, cst[CF_plane_y]);
        if (csti[CI_contact] != 0 && g < (double)(-1e-6)) {
            pen[npen] = r;
            gaps[npen] = g;
            npen =  npen + 1;
}
}
    if (npen > 0) {
        double gram[16];
        double rhs[4];
        double lam[4];
        double ra[18];
        double ia[18];
        for (a = 0; a < (npen); ++a) {
            for (i = 0; i < (18); ++i) {
                ra[i] = ptJ[(pen[a] * 3 + 1) * 18 + i];
}
            mat_vec(inv, ra, ia);
            for (b = 0; b < (npen); ++b) {
                s =  (double)(0.0);
                for (i = 0; i < (18); ++i) {
                    s =  s + ia[i] * ptJ[(pen[b] * 3 + 1) * 18 + i];
}
                gram[a * 4 + b] = s;
}
            rhs[a] = -gaps[a];
}
        if (gram_factor4(gram, npen, rhs, lam) == 1) {
            double corr[18];
            for (a = 0; a < (npen); ++a) {
                for (i = 0; i < (18); ++i) {
                    ra[i] = ptJ[(pen[a] * 3 + 1) * 18 + i];
}
                mat_vec(inv, ra, ia);
                for (i = 0; i < (18); ++i) {
                    corr[i] = corr[i] + lam[a] * ia[i];
}
}
            dq_max =  (double)(0.0);
            for (i = 0; i < (18); ++i) {
                if (fabs(corr[i]) > dq_max) {
                    dq_max =  fabs(corr[i]);
}
}
            if (dq_max > (double)(0.05)) {
                rc[0] = 3;
                return (double)(0.0);
}
            for (i = 0; i < (18); ++i) {
                q[i] = q[i] + corr[i];
}
}
}
    return caught;
}

__device__ inline void advance(double* q0, double* v0, double* w0, double* tau, int h, double* mdl, double* cst, double* M, double* gv, double* bv, double* fr, double* frd, double* frdd, double* axw, double* axpiv, double* axdir, double* ptp, double* ptJ, double* ptcop, double* ptbias, double* inv, double* free, double* srq, double* srv, double* qa, double* va, double* qb, double* vb, double* qc, double* vc, double* qd, double* vd, double* qe, double* ve, double* we, double* sq, double* sh, int* sdep, int* scl, int* adv, int* rc, double* q1, double* v1, double* w1, int* mdi, int* csti) {
    int i;
    int sp;
    double rem;
    int depth;
    int clamps;
    int it;
    int done;
    double caught;
    double pot;
    int r;
    double g;
    double rcs;
    double hit;
    int which;
    int khit;
    double wall;
    int d;
    int c;
    int low;
    double depth_v;
    int bound;
    double left;
    double right;
    int j;
    double mid;
    double rcb;
    int ok2;
    double t;
    int rr;
    double rcc;
    double rcw;
    double pt_radius_g[((OF_pt_radius + 8) - (OF_pt_radius))];
    for (int _si0 = 0; _si0 < ((OF_pt_radius + 8) - (OF_pt_radius)); ++_si0) pt_radius_g[_si0] = mdl[(OF_pt_radius) + _si0];
    for (i = 0; i < (18); ++i) {
        q1[i] = q0[i];
        v1[i] = v0[i];
        w1[i] = w0[i];
}
    if (h < (double)(1e-12)) {
        return;
}
    sp =  (int)(0);
    rem =  h;
    depth =  (int)(0);
    clamps =  (int)(0);
    int live[4];
    int probe[4];
    it =  (int)(0);
    done =  (int)(0);
    int rcv[1];
    while (done == 0) {
        it =  it + 1;
        if (it > 4000) {
            rc[0] = 6;
            return;
}
        if (rem < (double)(1e-12)) {
            if (sp > 0) {
                sp =  sp - 1;
                rem =  sh[sp];
                depth =  sdep[sp];
                clamps =  scl[sp];
                continue;
}
            else {
                done =  1;
                break;
}
}
        adv[0] = adv[0] + 1;
        if (adv[0] > 3000) {
            rc[0] = 2;
            return;
}
        if (depth >= 10 + 6 * 8) {
            rc[0] = 6;
            return;
}
        rcv[0] = 0;
        caught =  impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv, csti, mdi);
        if (rcv[0] != 0) {
            rc[0] = rcv[0];
            return;
}
        if (cst[CF_mu] > (double)(0.0) && caught > (double)(1e-9) && depth < 5) {
            sh[sp] = rem * (double)(0.5);
            sdep[sp] = depth + 3;
            scl[sp] = clamps;
            sp =  sp + 1;
            rem =  rem * (double)(0.5);
            depth =  depth + 3;
            continue;
}
        pot =  fk_eval(q1,  v1, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
        for (r = 0; r < (4); ++r) {
            g =  gap_of_k(ptp, pt_radius_g, r * 2, cst[CF_plane_y]);
            live[r] = ((csti[CI_contact] != 0 && g <= cst[CF_k_touch])) ? ((int)(1)) : ((int)(0));
}
        rcs =  free_step(q1, v1, w1, tau, live, rem, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, csti, mdi);
        if (rcs != 0) {
            rc[0] = rcs;
            return;
}
        hit =  rem;
        which =  (int)(-1);
        khit =  (int)(-1);
        wall =  (double)(0.0);
        d =  (int)(0);
        while (d < 12) {
            d =  d + 1;
            c =  mdi[OI_drive_coord + d - 1];
            low =  (qe[c] < mdl[OF_lower + c]) ? ((int)(1)) : ((int)(0));
            if (low == 0 && qe[c] <= mdl[OF_upper + c]) {
                continue;
}
            if (low != 0) {
                depth_v =  mdl[OF_lower + c] - qe[c];
}
            else {
                depth_v =  qe[c] - mdl[OF_upper + c];
}
            if (depth_v <= (double)(1e-12)) {
                continue;
}
            bound =  (low != 0) ? (mdl[OF_lower + c]) : (mdl[OF_upper + c]);
            left =  (double)(0.0);
            right =  rem;
            j =  (int)(0);
            while (j < 42) {
                j =  j + 1;
                mid =  (left + right) * (double)(0.5);
                rcb =  free_step(q1, v1, w1, tau, live, mid, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, csti, mdi);
                if (rcb != 0) {
                    rc[0] = rcb;
                    return;
}
                if (low != 0) {
                    ok2 =  (qe[c] <= bound) ? ((int)(1)) : ((int)(0));
}
                else {
                    ok2 =  (qe[c] >= bound) ? ((int)(1)) : ((int)(0));
}
                if (ok2 != 0) {
                    right =  mid;
}
                else {
                    left =  mid;
}
}
            t =  (left + right) * (double)(0.5);
            if (t < hit || (t == hit && which >= 0 && (d - 1) < which)) {
                hit =  t;
                which =  d - 1;
                khit =  -1;
                wall =  bound;
}
}
        if (csti[CI_contact] != 0) {
            pot =  fk_eval(qe,  ve, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
            r =  (int)(0);
            while (r < 4) {
                r =  r + 1;
                if (live[r - 1] != 0) {
                    continue;
}
                g =  gap_of_k(ptp, pt_radius_g, (r - 1) * 2, cst[CF_plane_y]);
                if (g >= (double)(0.0)) {
                    continue;
}
                for (rr = 0; rr < (4); ++rr) {
                    probe[rr] = live[rr];
}
                probe[r - 1] = 0;
                left =  (double)(0.0);
                right =  rem;
                j =  (int)(0);
                while (j < 42) {
                    j =  j + 1;
                    mid =  (left + right) * (double)(0.5);
                    rcb =  free_step(q1, v1, w1, tau, probe, mid, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, csti, mdi);
                    if (rcb != 0) {
                        rc[0] = rcb;
                        return;
}
                    if (gap_of_k(ptp, pt_radius_g, r * 2, cst[CF_plane_y]) <= (double)(0.0)) {
                        right =  mid;
}
                    else {
                        left =  mid;
}
}
                t =  (left + right) * (double)(0.5);
                if (t < hit) {
                    hit =  t;
                    which =  -2;
                    khit =  r - 1;
}
                r =  r;
}
}
        if (which == -1) {
            for (i = 0; i < (18); ++i) {
                q1[i] = qe[i];
                v1[i] = ve[i];
                w1[i] = we[i];
}
            if (sp > 0) {
                sp =  sp - 1;
                rem =  sh[sp];
                depth =  sdep[sp];
                clamps =  scl[sp];
                continue;
}
            else {
                done =  1;
                break;
}
}
        if (hit <= (double)(1e-12)) {
            if (clamps >= 64) {
                rc[0] = 6;
                return;
}
            if (which >= 0) {
                q1[mdi[OI_drive_coord + which]] = wall;
}
            rcv[0] = 0;
            caught =  impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv, csti, mdi);
            if (rcv[0] != 0) {
                rc[0] = rcv[0];
                return;
}
            clamps =  clamps + 1;
            continue;
}
        if (which == -2) {
            for (rr = 0; rr < (4); ++rr) {
                probe[rr] = live[rr];
}
            probe[khit] = 0;
            rcc =  free_step(q1, v1, w1, tau, probe, hit, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, csti, mdi);
            if (rcc != 0) {
                rc[0] = rcc;
                return;
}
            for (i = 0; i < (18); ++i) {
                q1[i] = qe[i];
                v1[i] = ve[i];
                w1[i] = we[i];
}
            rcv[0] = 0;
            caught =  impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv, csti, mdi);
            if (rcv[0] != 0) {
                rc[0] = rcv[0];
                return;
}
            if (cst[CF_mu] > (double)(0.0)) {
                sh[sp] = (rem - hit) * (double)(0.5);
                sdep[sp] = depth + 2;
                scl[sp] = clamps;
                sp =  sp + 1;
                rem =  (rem - hit) * (double)(0.5);
                depth =  depth + 1;
}
            else {
                rem =  rem - hit;
                depth =  depth + 1;
}
            continue;
}
        rcw =  free_step(q1, v1, w1, tau, live, hit, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, csti, mdi);
        if (rcw != 0) {
            rc[0] = rcw;
            return;
}
        for (i = 0; i < (18); ++i) {
            q1[i] = qe[i];
            v1[i] = ve[i];
            w1[i] = we[i];
}
        q1[mdi[OI_drive_coord + which]] = wall;
        rcv[0] = 0;
        caught =  impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv, csti, mdi);
        if (rcv[0] != 0) {
            rc[0] = rcv[0];
            return;
}
        rem =  rem - hit;
        depth =  depth + 1;
        continue;
}
}

__device__ inline void fore_ik_at(double* mdl, double* cst, double* fr, int leg, double* paw, double branch, int* mdi, int* csti, double* __o0, double* __o1, double* __o2, double* __o3, double* __o4) {
    int off;
    double rx;
    double ry;
    double rz;
    double ml0;
    double ml1;
    double dx;
    double dy;
    double D;
    double dmax;
    double dmin;
    int sat;
    double Dc;
    double ca;
    double th1;
    double q1;
    double ex;
    double ey;
    double q2;
    int c1;
    int c2;
    double q1r;
    double q2r;
    off =  csti[CI_pelvis_row] * 16;
    rx =  paw[0] - fr[off + 3];
    ry =  paw[1] - fr[off + 7];
    rz =  paw[2] - fr[off + 11];
    ml0 =  mdl[OF_fore_mount_local + leg * 3];
    ml1 =  mdl[OF_fore_mount_local + leg * 3 + 1];
    dx =  fr[off + 0] * rx + fr[off + 4] * ry + fr[off + 8] * rz - ml0;
    dy =  fr[off + 1] * rx + fr[off + 5] * ry + fr[off + 9] * rz - ml1;
    D =  sqrt(dx * dx + dy * dy);
    dmax =  cst[CF_fore_L1] + cst[CF_fore_rho];
    dmin =  fabs(cst[CF_fore_L1] - cst[CF_fore_rho]);
    sat =  (int)(0);
    if (D > dmax * ((double)(1.0) - (double)(1e-12)) || D < dmin + (double)(1e-9)) {
        sat =  1;
        Dc =  fmin(fmax(D, dmin + (double)(1e-9)), dmax * ((double)(1.0) - (double)(1e-12)));
        dx =  dx * Dc / D;
        dy =  dy * Dc / D;
        D =  Dc;
}
    ca =  (D * D + cst[CF_fore_L1] * cst[CF_fore_L1] - cst[CF_fore_rho] * cst[CF_fore_rho]) / ((double)(2.0) * D * cst[CF_fore_L1]);
    ca =  fmin((double)(1.0), fmax((double)(-1.0), ca));
    th1 =  atan2(dy, dx) + (double)(branch) * acos(ca);
    q1 =  th1 + PI * (double)(0.5);
    ex =  dx - cst[CF_fore_L1] * cos(th1);
    ey =  dy - cst[CF_fore_L1] * sin(th1);
    q2 =  atan2(ey, ex) - q1 - cst[CF_fore_beta];
    c1 =  mdi[OI_fore_coord + leg * 2];
    c2 =  mdi[OI_fore_coord + leg * 2 + 1];
    q1r =  q1;
    q2r =  q2;
    q1 =  fmin(mdl[OF_upper + c1], fmax(mdl[OF_lower + c1], q1));
    q2 =  fmin(mdl[OF_upper + c2], fmax(mdl[OF_lower + c2], q2));
    (*__o0) = q1;
    (*__o1) = q2;
    (*__o2) = q1r;
    (*__o3) = q2r;
    (*__o4) = sat;
    return;
}

__device__ inline double fore_D_at(double* mdl, double* cst, double* fr, int leg, double* paw, int* csti) {
    int off;
    double rx;
    double ry;
    double rz;
    double ml0;
    double ml1;
    double dx;
    double dy;
    off =  csti[CI_pelvis_row] * 16;
    rx =  paw[0] - fr[off + 3];
    ry =  paw[1] - fr[off + 7];
    rz =  paw[2] - fr[off + 11];
    ml0 =  mdl[OF_fore_mount_local + leg * 3];
    ml1 =  mdl[OF_fore_mount_local + leg * 3 + 1];
    dx =  fr[off + 0] * rx + fr[off + 4] * ry + fr[off + 8] * rz - ml0;
    dy =  fr[off + 1] * rx + fr[off + 5] * ry + fr[off + 9] * rz - ml1;
    return sqrt(dx * dx + dy * dy);
}

__device__ inline void hind_ik_at(double* mdl, double* cst, double* fr, double* tgt, double ap, double branch, int* csti, double* __o0, double* __o1, double* __o2) {
    int off;
    double rx;
    double ry;
    double rz;
    double dx;
    double dy;
    double wx;
    double wy;
    double D;
    double dmax;
    double dmin;
    double Dc;
    double ca;
    double k;
    double a1;
    double qh;
    double qk;
    double qa;
    off =  csti[CI_pelvis_row] * 16;
    rx =  tgt[0] - fr[off + 3];
    ry =  tgt[1] - fr[off + 7];
    rz =  tgt[2] - fr[off + 11];
    dx =  fr[off + 0] * rx + fr[off + 4] * ry + fr[off + 8] * rz;
    dy =  fr[off + 1] * rx + fr[off + 5] * ry + fr[off + 9] * rz;
    wx =  dx - cst[CF_hind_xm] * cos(ap);
    wy =  dy - cst[CF_hind_xm] * sin(ap);
    D =  sqrt(wx * wx + wy * wy);
    dmax =  cst[CF_hind_L1] + cst[CF_hind_L2];
    dmin =  fabs(cst[CF_hind_L1] - cst[CF_hind_L2]);
    Dc =  fmin(fmax(D, dmin + (double)(1e-9)), dmax * ((double)(1.0) - (double)(1e-12)));
    ca =  (Dc * Dc - cst[CF_hind_L1] * cst[CF_hind_L1] - cst[CF_hind_L2] * cst[CF_hind_L2]) / ((double)(2.0) * cst[CF_hind_L1] * cst[CF_hind_L2]);
    ca =  fmin((double)(1.0), fmax((double)(-1.0), ca));
    k =  (double)(branch) * acos(ca);
    a1 =  atan2(wy, wx) - atan2(-cst[CF_hind_L1] - cst[CF_hind_L2] * cos(k), cst[CF_hind_L2] * sin(k));
    qh =  a1;
    qk =  k;
    qa =  ap - a1 - k;
    (*__o0) = qh;
    (*__o1) = qk;
    (*__o2) = qa;
    return;
}

__device__ inline void tables_at(double* mdl, double phi, double* out) {
    double p;
    double x;
    int k;
    double f;
    p =  phi - floor(phi);
    x =  p * (double)(20.0);
    k =  (int)(x);
    if (k > 19) {
        k =  19;
}
    f =  x - (double)(k);
    out[0] = mdl[OF_tab_hip + k] * ((double)(1.0) - f) + mdl[OF_tab_hip + k + 1] * f + mdl[OF_zeros4 + 0];
    out[1] = mdl[OF_tab_knee + k] * ((double)(1.0) - f) + mdl[OF_tab_knee + k + 1] * f + mdl[OF_zeros4 + 1];
    out[2] = mdl[OF_tab_ankle + k] * ((double)(1.0) - f) + mdl[OF_tab_ankle + k + 1] * f + mdl[OF_zeros4 + 2];
    out[3] = mdl[OF_tab_mp + k] * ((double)(1.0) - f) + mdl[OF_tab_mp + k + 1] * f + mdl[OF_zeros4 + 3];
    return;
}

__device__ inline double vault_at(double* mdl, double phi) {
    double p;
    double x;
    int k;
    double f;
    p =  phi - floor(phi);
    x =  p * (double)(20.0);
    k =  (int)(x);
    if (k > 19) {
        k =  19;
}
    f =  x - (double)(k);
    return mdl[OF_vault + k] * ((double)(1.0) - f) + mdl[OF_vault + k + 1] * f;
}

__global__ void reset_kernel(double* a_q0, double* a_v0, int* a_touching0, double phi_l0, double phi_r0, int settle_total, double* a_store_floor, double store_post, double* a_q, double* a_v, double* a_work, double* a_last_torque, double* a_battery, double* a_battery_post, double* a_phi, int* a_touching, int* a_captured, int* a_settle, int* a_ik_branch, double* a_paw_target, double* a_paw_plant_y, double* a_swing_from, double* a_swing_to, double* a_fore_t, double* a_fore_stance, double* a_fore_cycle, int* a_fore_mode, int* a_fore_entry, int* a_fore_conv, int* a_fore_td_plant, int* a_fore_clamped, int* a_fore_replants, int* a_fore_td_count, int* a_hind_mode, double* a_hind_t, double* a_hind_from, double* a_hind_to, double* a_hind_plant_y, double* a_hind_ap, double* a_hind_mp, int* a_hind_branch, int* a_hind_held, long long* a_hind_last_fire, long long* a_hind_last_td, int* a_hind_fires, int* a_hind_tds, double* a_hind_xoff, int* a_height_latched, double* a_cmd_vx, int* a_cmd_live, long long* a_cmd_first_tick, int* a_cmd_fires, long long* a_ticks, int* a_adv_calls, int* a_refused, int* a_refused_class, int* a_collapsed) {
    int i;
    int d;
    int l;
    int c;
    int e = blockIdx.x * blockDim.x + threadIdx.x;
    for (i = 0; i < (18); ++i) {
        a_q[e * 18 + i] = a_q0[e * 18 + i];
        a_v[e * 18 + i] = a_v0[e * 18 + i];
        a_work[e * 18 + i] = (double)(0.0);
        a_last_torque[e * 18 + i] = (double)(0.0);
}
    for (d = 0; d < (12); ++d) {
        a_battery[e * 12 + d] = a_store_floor[d];
}
    a_battery_post[e] = store_post;
    a_phi[e * 2] = phi_l0;
    a_phi[e * 2 + 1] = phi_r0;
    for (l = 0; l < (2); ++l) {
        a_touching[e * 2 + l] = a_touching0[e * 2 + l];
}
    a_captured[e] = 0;
    a_settle[e] = settle_total;
    a_ik_branch[e * 2] = 1;
    a_ik_branch[e * 2 + 1] = 1;
    for (l = 0; l < (2); ++l) {
        a_paw_plant_y[e * 2 + l] = (double)(0.0);
        a_fore_t[e * 2 + l] = (double)(0.0);
        a_fore_stance[e * 2 + l] = (double)(0.0);
        a_fore_cycle[e * 2 + l] = (double)(0.0);
        a_fore_mode[e * 2 + l] = 0;
        a_fore_entry[e * 2 + l] = 0;
        a_fore_conv[e * 2 + l] = 0;
        a_fore_td_plant[e * 2 + l] = 1;
        a_fore_clamped[e * 2 + l] = 0;
        a_fore_replants[e * 2 + l] = 0;
        a_fore_td_count[e * 2 + l] = 0;
        a_hind_mode[e * 2 + l] = 0;
        a_hind_t[e * 2 + l] = (double)(0.0);
        a_hind_plant_y[e * 2 + l] = (double)(0.0);
        a_hind_ap[e * 2 + l] = (double)(0.0);
        a_hind_mp[e * 2 + l] = (double)(0.0);
        a_hind_branch[e * 2 + l] = -1;
        a_hind_held[e * 2 + l] = 0;
        a_hind_last_fire[e * 2 + l] = (long long)(0);
        a_hind_last_td[e * 2 + l] = (long long)(0);
        a_hind_fires[e * 2 + l] = 0;
        a_hind_tds[e * 2 + l] = (int)(0);
        a_hind_xoff[e * 2 + l] = (double)(0.0);
        for (c = 0; c < (3); ++c) {
            a_paw_target[e * 6 + l * 3 + c] = (double)(0.0);
            a_swing_from[e * 6 + l * 3 + c] = (double)(0.0);
            a_swing_to[e * 6 + l * 3 + c] = (double)(0.0);
            a_hind_from[e * 6 + l * 3 + c] = (double)(0.0);
            a_hind_to[e * 6 + l * 3 + c] = (double)(0.0);
}
}
    a_height_latched[e] = 0;
    a_cmd_vx[e] = (double)(0.0);
    a_cmd_live[e] = 0;
    a_cmd_first_tick[e] = (long long)(-1);
    a_cmd_fires[e] = 0;
    a_ticks[e] = (long long)(0);
    a_adv_calls[e] = 0;
    a_refused[e] = 0;
    a_refused_class[e] = 0;
    a_collapsed[e] = 0;
}

__device__ inline double fore_target_headroom(double* mdl, double* cst, double* fr, int leg, double* paw, double branch, int* mdi, int* csti) {
    double d1a;
    double d1b;
    double q1r;
    double q2r;
    double d1c;
    int c1;
    int c2;
    double h1;
    double h2;
    fore_ik_at(mdl, cst, fr, leg, paw, branch, csti, mdi, &d1a, &d1b, &q1r, &q2r, &d1c);
    c1 =  mdi[OI_fore_coord + leg * 2];
    c2 =  mdi[OI_fore_coord + leg * 2 + 1];
    h1 =  fmin(q1r - mdl[OF_lower + c1], mdl[OF_upper + c1] - q1r);
    h2 =  fmin(q2r - mdl[OF_lower + c2], mdl[OF_upper + c2] - q2r);
    return fmin(h1, h2);
}

__device__ inline void fore_follow(double* mdl, double* cst, double* fr, int leg, double* paw_t, double branch, int* mdi, int* csti, double* result) {
    double dirn;
    double dmax;
    double lo;
    double hi;
    int j;
    double mid;
    double edge;
    double p[3];
    p[0] = paw_t[leg * 3];
    p[1] = paw_t[leg * 3 + 1];
    p[2] = paw_t[leg * 3 + 2];
    double px[3];
    double py[3];
    px[0] = p[0] + (double)(1e-3);
    px[1] = p[1];
    px[2] = p[2];
    py[0] = p[0] - (double)(1e-3);
    py[1] = p[1];
    py[2] = p[2];
    dirn =  (double)(1.0);
    if (fore_target_headroom(mdl, cst, fr, leg, px, branch, csti, mdi) < fore_target_headroom(mdl, cst, fr, leg, py, branch, csti, mdi)) {
        dirn =  (double)(-1.0);
}
    dmax =  cst[CF_fore_L1] + cst[CF_fore_rho];
    lo =  (double)(0.0);
    hi =  (double)(2.0) * dmax;
    for (j = 0; j < (42); ++j) {
        mid =  (lo + hi) * (double)(0.5);
        double t[3];
        t[0] = p[0] + dirn * mid;
        t[1] = p[1];
        t[2] = p[2];
        if (fore_D_at(mdl, cst, fr, leg, t, csti) < dmax) {
            lo =  mid;
}
        else {
            hi =  mid;
}
}
    edge =  (lo + hi) * (double)(0.5);
    double te[3];
    te[0] = p[0] + dirn * edge;
    te[1] = p[1];
    te[2] = p[2];
    if (fore_target_headroom(mdl, cst, fr, leg, te, branch, csti, mdi) < (double)(0.1022)) {
        result[0] = te[0];
        result[1] = te[1];
        result[2] = te[2];
        return;
}
    lo =  (double)(0.0);
    hi =  edge;
    for (j = 0; j < (42); ++j) {
        mid =  (lo + hi) * (double)(0.5);
        double t[3];
        t[0] = p[0] + dirn * mid;
        t[1] = p[1];
        t[2] = p[2];
        if (fore_target_headroom(mdl, cst, fr, leg, t, branch, csti, mdi) < (double)(0.1022)) {
            lo =  mid;
}
        else {
            hi =  mid;
}
}
    double out[3];
    out[0] = p[0] + dirn * ((lo + hi) * (double)(0.5));
    out[1] = p[1];
    out[2] = p[2];
    result[0] = out[0];
    result[1] = out[1];
    result[2] = out[2];
    return;
}

__device__ inline double fore_env(double* mdl, double* cst, double* fr, int leg, double* paw_t, double v3, int* csti) {
    int i;
    double off;
    double hgt;
    double dd;
    double a2;
    double amax;
    double vv;
    double env_s;
    double m16[16];
    for (i = 0; i < (16); ++i) {
        m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
    double shw[3];
    double ml[3];
    ml[0] = mdl[OF_fore_mount_local + leg * 3];
    ml[1] = mdl[OF_fore_mount_local + leg * 3 + 1];
    ml[2] = mdl[OF_fore_mount_local + leg * 3 + 2];
    apply_point(m16, ml, shw);
    off =  paw_t[leg * 3] - shw[0];
    hgt =  fmax((double)(0.0), shw[1] - paw_t[leg * 3 + 1]);
    dd =  cst[CF_fore_L1] + cst[CF_fore_rho];
    a2 =  dd * dd - hgt * hgt;
    amax =  (a2 > (double)(0.0)) ? (sqrt(a2)) : ((double)(0.0));
    vv =  fmax((double)(0.0), v3);
    if (vv <= (double)(1e-9)) {
        return (double)(0.0);
}
    env_s =  (amax + off - vv * cst[CF_dt]) / vv / cst[CF_dt];
    if (env_s < (double)(0.0)) {
        env_s =  (double)(0.0);
}
    return env_s;
}

__device__ inline void hind_deadline_fn(double h_lt_o, double h_lt_h, double tair, double fold_budget, double unload_ticks, double* __o0, double* __o1) {
    long long dl;
    int is_unload;
    double fold;
    double unload;
    dl =  (long long)(0);
    is_unload =  (int)(0);
    if (h_lt_o == (long long)(0)) {
        (*__o0) = dl;
        (*__o1) = is_unload;
        return;
}
    fold =  h_lt_o + (long long)(fold_budget - tair - 1);
    dl =  fold;
    if (h_lt_h != (long long)(0)) {
        unload =  h_lt_o + (long long)(unload_ticks - 1);
        if (unload < fold) {
            dl =  unload;
            is_unload =  1;
}
}
    (*__o0) = dl;
    (*__o1) = is_unload;
    return;
}

__device__ inline void paw_leg(double* paw_t, int leg, double* out) {
    out[0] = paw_t[leg * 3];
    out[1] = paw_t[leg * 3 + 1];
    out[2] = paw_t[leg * 3 + 2];
    return;
}

__global__ void tick_plan_kernel(double* mdl, int* mdi, double* cst, int* csti, double* a_q, double* a_v, double* a_work, double* a_last_torque, double* a_battery, double* a_battery_post, double* a_phi, int* a_touching, int* a_captured, int* a_settle, int* a_ik_branch, double* a_paw_target, double* a_paw_plant_y, double* a_swing_from, double* a_swing_to, double* a_fore_t, double* a_fore_stance, double* a_fore_cycle, int* a_fore_mode, int* a_fore_entry, int* a_fore_conv, int* a_fore_td_plant, int* a_fore_clamped, int* a_fore_replants, int* a_fore_td_count, int* a_hind_mode, double* a_hind_t, double* a_hind_from, double* a_hind_to, double* a_hind_plant_y, double* a_hind_ap, double* a_hind_mp, int* a_hind_branch, int* a_hind_held, long long* a_hind_last_fire, long long* a_hind_last_td, int* a_hind_fires, int* a_hind_tds, double* a_hind_xoff, int* a_height_latched, double* a_cmd_vx, int* a_cmd_live, long long* a_cmd_first_tick, int* a_cmd_fires, long long* a_ticks, int* a_adv_calls, int* a_refused, int* a_refused_class, int* a_collapsed, double* rb, int* rbi, int* a_rc) {
    double ne;
    int rc;
    double tick;
    int i;
    int d;
    double bat_post;
    double capt;
    double settle_n;
    int l;
    int c;
    double h_latched;
    double cmd_v;
    double cmd_on;
    double cmd_first;
    double cmd_fires;
    double Tf;
    double tair;
    int walking;
    int round_n;
    double pot;
    double v_eff;
    int leg;
    int hpt;
    int fb;
    int c1;
    int c2;
    double qa1;
    double qa2;
    double qa1r;
    double qa2r;
    double sata;
    double qb1;
    double qb2;
    double qb1r;
    double qb2r;
    double satb;
    double e0;
    double e1;
    double off;
    double xoff;
    double hgt;
    double dd;
    double a2;
    double amax;
    double vv;
    double tau1;
    double env_s;
    double lift_wait;
    double tau_env;
    double g0;
    double g1;
    double gmin;
    int cls;
    int o;
    double sg;
    double carch;
    double h1;
    double h2;
    double wall_hr;
    int wall_bound;
    int gated;
    int o_prior;
    double dq1;
    double dq2;
    double tq1r;
    double tq2r;
    double dsat;
    double th1;
    double th2;
    int thin_seat;
    int due;
    double env_t;
    int act;
    double dsx;
    double dsy;
    double env_t2;
    int cc1;
    int cc2;
    double swing;
    double slot;
    double dslot;
    double offc;
    double envc;
    double smin;
    int found;
    int kk;
    int ww;
    double step;
    double stc;
    double shmin;
    int hl;
    double g2;
    int alt_due;
    double dl;
    double is_unload;
    int conc;
    double wait;
    int live_slot;
    int alt_fire;
    int gated_b;
    int floor_gated;
    int livec;
    int l2;
    double mn;
    int pt;
    double g;
    int promised;
    double mn2;
    int deadline_fire;
    int stall_era_link;
    double fx;
    double fy;
    double fz;
    int c0;
    int c1h;
    int c2h;
    double a2m;
    double dxs;
    double dys;
    double under;
    double xmax;
    int hn;
    int k;
    double mtot;
    double comx;
    double comy;
    double comz;
    int b;
    double mb;
    int j;
    double tx;
    double tz;
    int un;
    double cr;
    int t2;
    int cn;
    double v_bound;
    double slip_mx;
    int r;
    double svx;
    double svz;
    double sl;
    int side;
    int viol;
    double s;
    double ex;
    double ez;
    double nl;
    double nx;
    double nz;
    double cx;
    double cz;
    int i2;
    int touching_leg;
    int collapsed;
    double bat_sum;
    double pt_radius_g[((OF_pt_radius + 8) - (OF_pt_radius))];
    for (int _si0 = 0; _si0 < ((OF_pt_radius + 8) - (OF_pt_radius)); ++_si0) pt_radius_g[_si0] = mdl[(OF_pt_radius) + _si0];
    int e = blockIdx.x * blockDim.x + threadIdx.x;
    ne =  cu_total_q / 18;
    if (e >= ne) {
        return;
}
    if (a_refused[e] != 0 || a_collapsed[e] != 0) {
        return;
}
    rc =  (int)(0);
    tick =  a_ticks[e];
    double q[18];
    double v[18];
    double w[18];
    double ltau[18];
    for (i = 0; i < (18); ++i) {
        q[i] = a_q[e * 18 + i];
        v[i] = a_v[e * 18 + i];
        w[i] = a_work[e * 18 + i];
        ltau[i] = a_last_torque[e * 18 + i];
}
    double bat[12];
    for (d = 0; d < (12); ++d) {
        bat[d] = a_battery[e * 12 + d];
}
    bat_post =  a_battery_post[e];
    double phi[2];
    phi[0] = a_phi[e * 2];
    phi[1] = a_phi[e * 2 + 1];
    int tch[2];
    tch[0] = a_touching[e * 2];
    tch[1] = a_touching[e * 2 + 1];
    capt =  a_captured[e];
    settle_n =  a_settle[e];
    int ikb[2];
    ikb[0] = a_ik_branch[e * 2];
    ikb[1] = a_ik_branch[e * 2 + 1];
    double paw_t[6];
    double paw_y[2];
    double swf[6];
    double swt[6];
    double f_t[2];
    double f_st[2];
    double f_cy[2];
    int f_mo[2];
    int f_en[2];
    int f_cv[2];
    int f_dp[2];
    int f_cl[2];
    int f_rp[2];
    int f_td[2];
    for (l = 0; l < (2); ++l) {
        for (c = 0; c < (3); ++c) {
            paw_t[l * 3 + c] = a_paw_target[e * 6 + l * 3 + c];
            swf[l * 3 + c] = a_swing_from[e * 6 + l * 3 + c];
            swt[l * 3 + c] = a_swing_to[e * 6 + l * 3 + c];
}
        paw_y[l] = a_paw_plant_y[e * 2 + l];
        f_t[l] = a_fore_t[e * 2 + l];
        f_st[l] = a_fore_stance[e * 2 + l];
        f_cy[l] = a_fore_cycle[e * 2 + l];
        f_mo[l] = a_fore_mode[e * 2 + l];
        f_en[l] = a_fore_entry[e * 2 + l];
        f_cv[l] = a_fore_conv[e * 2 + l];
        f_dp[l] = a_fore_td_plant[e * 2 + l];
        f_cl[l] = a_fore_clamped[e * 2 + l];
        f_rp[l] = a_fore_replants[e * 2 + l];
        f_td[l] = a_fore_td_count[e * 2 + l];
}
    int h_mo[2];
    double h_t[2];
    double h_from[6];
    double h_to[6];
    double h_py[2];
    double h_ap[2];
    double h_mp[2];
    int h_br[2];
    int h_held[2];
    long long h_lf[2];
    long long h_lt[2];
    int h_fi[2];
    int h_tds[2];
    double h_xo[2];
    for (l = 0; l < (2); ++l) {
        h_mo[l] = a_hind_mode[e * 2 + l];
        h_t[l] = a_hind_t[e * 2 + l];
        h_py[l] = a_hind_plant_y[e * 2 + l];
        h_ap[l] = a_hind_ap[e * 2 + l];
        h_mp[l] = a_hind_mp[e * 2 + l];
        h_br[l] = a_hind_branch[e * 2 + l];
        h_held[l] = a_hind_held[e * 2 + l];
        h_lf[l] = a_hind_last_fire[e * 2 + l];
        h_lt[l] = a_hind_last_td[e * 2 + l];
        h_fi[l] = a_hind_fires[e * 2 + l];
        h_tds[l] = a_hind_tds[e * 2 + l];
        h_xo[l] = a_hind_xoff[e * 2 + l];
        for (c = 0; c < (3); ++c) {
            h_from[l * 3 + c] = a_hind_from[e * 6 + l * 3 + c];
            h_to[l * 3 + c] = a_hind_to[e * 6 + l * 3 + c];
}
}
    h_latched =  a_height_latched[e];
    cmd_v =  a_cmd_vx[e];
    cmd_on =  a_cmd_live[e];
    cmd_first =  a_cmd_first_tick[e];
    cmd_fires =  a_cmd_fires[e];
    int adv[1];
    adv[0] = a_adv_calls[e];
    Tf =  cst[CF_t_cycle] / cst[CF_dt];
    tair =  (double)(csti[CI_tair]);
    walking =  (int)(1);
    if (csti[CI_gait_enabled] == 0 || settle_n > 0 || csti[CI_reflex_level] == 0) {
        walking =  0;
}
    double M[324];
    double gv[18];
    double bv[18];
    double fr[224];
    double frd[224];
    double frdd[224];
    double axw[54];
    double axpiv[54];
    double axdir[54];
    double ptp[24];
    double ptJ[216];
    double ptcop[12];
    double ptbias[12];
    double inv[324];
    double free[18];
    double qa[18];
    double va[18];
    double qb[18];
    double vb[18];
    double qc[18];
    double vc[18];
    double qd[18];
    double vd[18];
    double qe[18];
    double ve[18];
    double we[18];
    double sq[576];
    double sh16[16];
    int sdep[16];
    int scl[16];
    double tr_q[18];
    double tr_v[18];
    double tr_w[18];
    double cd_q[18];
    double cd_v[18];
    double cd_w[18];
    double tau[18];
    double srq[18];
    double srv[18];
    double scales[13];
    round_n =  (int)(0);
    int dsf[1];
    double trial_q[18];
    double trial_v[18];
    double trial_w[18];
    double o_q[18];
    double o_v[18];
    double o_w[18];
    double cur_w[18];
    double eff[18];
    double lta[18];
    if (settle_n > 0) {
        settle_n =  settle_n - 1;
}
    pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
    v_eff =  fmax((double)(0.0), v[3]);
    if (cmd_on != 0) {
        cmd_fires =  cmd_fires + 1;
        if (cmd_first < (long long)(0)) {
            cmd_first =  tick;
}
        v_eff =  cmd_v;
}
    if (capt == 0 && csti[CI_settle_total] > 0 && settle_n == 0 && walking != 0 && csti[CI_power] != 0 && csti[CI_contact] != 0) {
        for (leg = 0; leg < (2); ++leg) {
            hpt =  mdi[OI_fore_heel_pt + leg];
            double prl[3];
            for (c = 0; c < (3); ++c) {
                prl[c] = (mdl[OF_pt_local + hpt * 3 + c] + mdl[OF_pt_local + (hpt + 1) * 3 + c]) * (double)(0.5);
}
            double T16[16];
            fb =  mdi[OI_pt_body + hpt];
            for (i = 0; i < (16); ++i) {
                T16[i] = fr[fb * 16 + i];
}
            double pw[3];
            apply_point(T16, prl, pw);
            for (c = 0; c < (3); ++c) {
                paw_t[leg * 3 + c] = pw[c];
}
            c1 =  mdi[OI_fore_coord + leg * 2];
            c2 =  mdi[OI_fore_coord + leg * 2 + 1];
            fore_ik_at(mdl, cst, fr, leg, pw, 1, csti, mdi, &qa1, &qa2, &qa1r, &qa2r, &sata);
            fore_ik_at(mdl, cst, fr, leg, pw, -1, csti, mdi, &qb1, &qb2, &qb1r, &qb2r, &satb);
            e0 =  sqrt((qa1 - q[c1]) * (qa1 - q[c1]) + (qa2 - q[c2]) * (qa2 - q[c2]));
            e1 =  sqrt((qb1 - q[c1]) * (qb1 - q[c1]) + (qb2 - q[c2]) * (qb2 - q[c2]));
            ikb[leg] = 1;
            if (e1 < e0) {
                ikb[leg] = -1;
}
}
        capt =  1;
        for (leg = 0; leg < (2); ++leg) {
            paw_y[leg] = paw_t[leg * 3 + 1];
            double shw[3];
            double ml[3];
            double m16[16];
            for (i = 0; i < (16); ++i) {
                m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
            ml[0] = mdl[OF_fore_mount_local + leg * 3];
            ml[1] = mdl[OF_fore_mount_local + leg * 3 + 1];
            ml[2] = mdl[OF_fore_mount_local + leg * 3 + 2];
            apply_point(m16, ml, shw);
            off =  paw_t[leg * 3] - shw[0];
            xoff =  v_eff * (cst[CF_duty] * cst[CF_t_cycle]) * (double)(0.5);
            hgt =  fmax((double)(0.0), shw[1] - paw_y[leg]);
            dd =  cst[CF_fore_L1] + cst[CF_fore_rho];
            a2 =  dd * dd - hgt * hgt;
            amax =  (a2 > (double)(0.0)) ? (sqrt(a2)) : ((double)(0.0));
            vv =  fmax((double)(0.0), v[3]);
            tau1 =  (double)(0.0);
            if (off < (double)(0.0) && vv > (double)(1e-9)) {
                f_en[leg] = 1;
                env_s =  (amax + off - vv * cst[CF_dt]) / vv;
                if (env_s < (double)(0.0)) {
                    env_s =  (double)(0.0);
}
                tau1 =  fmax((double)(0.0), env_s / cst[CF_dt] - (tair + (double)(1.0)));
}
            else if (xoff > (double)(0.0) && vv > (double)(1e-9)) {
                lift_wait =  fmax((double)(0.0), cst[CF_duty] - phi[leg]) * cst[CF_t_cycle] + (double)(0.25) * cst[CF_t_cycle];
                tau_env =  (amax + off - vv * cst[CF_dt]) / vv;
                if (tau_env < (double)(0.0)) {
                    tau_env =  (double)(0.0);
}
                tau1 =  fmin(lift_wait, tau_env);
}
            f_st[leg] = tau1 / cst[CF_dt];
            if (f_en[leg] != 0) {
                f_cy[leg] = f_st[leg] + tair;
}
            else {
                f_cy[leg] = f_st[leg] + ((double)(1.0) - cst[CF_duty]) / cst[CF_dt];
}
            f_t[leg] = (double)(0.0);
            f_mo[leg] = 0;
            f_cv[leg] = 0;
            f_cl[leg] = 0;
            f_rp[leg] = 0;
            f_td[leg] = 0;
}
}
    if (walking != 0) {
        for (leg = 0; leg < (2); ++leg) {
            g0 =  gap_of_k(ptp, pt_radius_g, leg * 2, cst[CF_plane_y]);
            g1 =  gap_of_k(ptp, pt_radius_g, leg * 2 + 1, cst[CF_plane_y]);
            gmin =  fmin(g0, g1);
            cls =  (int)(0);
            if (gmin <= cst[CF_k_touch]) {
                cls =  1;
}
            else if (gmin > cst[CF_k_touch] + cst[CF_k_release]) {
                cls =  0;
}
            else {
                cls =  tch[leg];
}
            if (cls != 0 && tch[leg] == 0) {
                phi[leg] = (double)(0.0);
}
            else {
                phi[leg] = fmod(phi[leg] + cst[CF_dt] / cst[CF_t_cycle], (double)(1.0));
}
            tch[leg] = cls;
}
}
    else {
        for (leg = 0; leg < (2); ++leg) {
            g0 =  gap_of_k(ptp, pt_radius_g, leg * 2, cst[CF_plane_y]);
            g1 =  gap_of_k(ptp, pt_radius_g, leg * 2 + 1, cst[CF_plane_y]);
            gmin =  fmin(g0, g1);
            cls =  (int)(0);
            if (gmin <= cst[CF_k_touch]) {
                cls =  1;
}
            else if (gmin > cst[CF_k_touch] + cst[CF_k_release]) {
                cls =  0;
}
            else {
                cls =  tch[leg];
}
            tch[leg] = cls;
}
}
    if (walking != 0 && capt != 0) {
        leg =  (int)(-1);
        while (leg < 1) {
            leg =  leg + 1;
            o =  1 - leg;
            f_t[leg] = f_t[leg] + (double)(1.0);
            if (f_mo[leg] == 1) {
                sg =  (f_t[leg] - f_st[leg]) / (f_cy[leg] - f_st[leg]);
                if (sg < (double)(0.0)) {
                    sg =  (double)(0.0);
}
                if (sg > (double)(1.0)) {
                    sg =  (double)(1.0);
}
                carch =  (double)(2.0) * mdl[OF_pt_radius + mdi[OI_fore_heel_pt + leg]];
                for (c = 0; c < (3); ++c) {
                    paw_t[leg * 3 + c] = swf[leg * 3 + c] + (swt[leg * 3 + c] - swf[leg * 3 + c]) * sg;
}
                paw_t[leg * 3 + 1] = paw_t[leg * 3 + 1] + carch * sin(PI * sg);
}
            if (f_mo[leg] == 0 && f_t[leg] >= f_st[leg]) {
                c1 =  mdi[OI_fore_coord + leg * 2];
                c2 =  mdi[OI_fore_coord + leg * 2 + 1];
                h1 =  fmin(q[c1] - mdl[OF_lower + c1], mdl[OF_upper + c1] - q[c1]);
                h2 =  fmin(q[c2] - mdl[OF_lower + c2], mdl[OF_upper + c2] - q[c2]);
                wall_hr =  fmin(h1, h2);
                wall_bound =  (int)(0);
                if (wall_hr <= (double)(0.0511)) {
                    wall_bound =  1;
}
                gated =  (int)(0);
                if (f_en[leg] != 0) {
                    if (f_mo[o] == 1) {
                        gated =  1;
}
                    else if (f_mo[o] == 0 && f_en[o] != 0 && f_dp[o] != 0 && f_t[o] < (double)(1.0)) {
                        gated =  1;
}
                    else if (f_mo[o] == 0 && f_en[o] != 0 && f_t[o] >= f_st[o]) {
                        o_prior =  (int)(0);
                        if (f_t[o] > f_t[leg]) {
                            o_prior =  1;
}
                        if (f_t[o] == f_t[leg]) {
                            double m16[16];
                            for (i = 0; i < (16); ++i) {
                                m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
                            double sha[3];
                            double ml0[3];
                            ml0[0] = mdl[OF_fore_mount_local + leg * 3];
                            ml0[1] = mdl[OF_fore_mount_local + leg * 3 + 1];
                            ml0[2] = mdl[OF_fore_mount_local + leg * 3 + 2];
                            apply_point(m16, ml0, sha);
                            double sho[3];
                            double ml1[3];
                            ml1[0] = mdl[OF_fore_mount_local + o * 3];
                            ml1[1] = mdl[OF_fore_mount_local + o * 3 + 1];
                            ml1[2] = mdl[OF_fore_mount_local + o * 3 + 2];
                            apply_point(m16, ml1, sho);
                            if ((paw_t[o * 3] - sho[0]) < (paw_t[leg * 3] - sha[0])) {
                                o_prior =  1;
}
}
                        gated =  o_prior;
}
}
                double plt[3];
                paw_leg(paw_t, leg, plt);
                fore_ik_at(mdl, cst, fr, leg, plt, ikb[leg], csti, mdi, &dq1, &dq2, &tq1r, &tq2r, &dsat);
                th1 =  fmin(tq1r - mdl[OF_lower + c1], mdl[OF_upper + c1] - tq1r);
                th2 =  fmin(tq2r - mdl[OF_lower + c2], mdl[OF_upper + c2] - tq2r);
                thin_seat =  (int)(0);
                if (fmin(th1, th2) < (double)(0.1022)) {
                    thin_seat =  1;
}
                due =  (int)(0);
                if (f_t[leg] >= f_st[leg] || wall_bound != 0) {
                    due =  1;
}
                env_t =  fore_env(mdl, cst, fr, leg, paw_t, v[3], csti);
                act =  (int)(0);
                double seat[3];
                if (gated == 0 && due != 0 && (thin_seat == 0 || wall_bound == 0)) {
                    act =  1;
}
                else if (gated == 0 && due != 0 && thin_seat != 0 && wall_bound != 0) {
                    double seat[3];
                    fore_follow(mdl, cst, fr, leg, paw_t, ikb[leg], csti, mdi, seat);
                    dsx =  seat[0] - paw_t[leg * 3];
                    dsy =  seat[1] - paw_t[leg * 3 + 1];
                    if (sqrt(dsx * dsx + dsy * dsy) < cst[CF_k_touch]) {
                        act =  1;
}
                    else {
                        act =  2;
}
}
                else if (gated != 0 && wall_bound != 0 && wall_hr < (double)(0.008040)) {
                    act =  1;
}
                else if (f_t[leg] >= f_cy[leg] || f_t[leg] >= env_t) {
                    if (wall_bound != 0 && fmin(th1, th2) < (double)(0.1022)) {
                        double seat[3];
                        fore_follow(mdl, cst, fr, leg, paw_t, ikb[leg], csti, mdi, seat);
                        dsx =  seat[0] - paw_t[leg * 3];
                        dsy =  seat[1] - paw_t[leg * 3 + 1];
                        if (sqrt(dsx * dsx + dsy * dsy) < cst[CF_k_touch]) {
                            act =  3;
}
                        else {
                            act =  2;
}
}
                    else {
                        act =  3;
}
}
                if (act == 1) {
                    f_mo[leg] = 1;
                    if (f_en[leg] != 0) {
                        f_t[leg] = (double)(0.0);
}
                    hpt =  mdi[OI_fore_heel_pt + leg];
                    double prl[3];
                    for (c = 0; c < (3); ++c) {
                        prl[c] = (mdl[OF_pt_local + hpt * 3 + c] + mdl[OF_pt_local + (hpt + 1) * 3 + c]) * (double)(0.5);
}
                    double T16[16];
                    fb =  mdi[OI_pt_body + hpt];
                    for (i = 0; i < (16); ++i) {
                        T16[i] = fr[fb * 16 + i];
}
                    double pw[3];
                    apply_point(T16, prl, pw);
                    double m16[16];
                    for (i = 0; i < (16); ++i) {
                        m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
                    double shw[3];
                    double ml[3];
                    ml[0] = mdl[OF_fore_mount_local + leg * 3];
                    ml[1] = mdl[OF_fore_mount_local + leg * 3 + 1];
                    ml[2] = mdl[OF_fore_mount_local + leg * 3 + 2];
                    apply_point(m16, ml, shw);
                    for (c = 0; c < (3); ++c) {
                        swf[leg * 3 + c] = pw[c];
}
                    xoff =  v_eff * (cst[CF_duty] * cst[CF_t_cycle]) * (double)(0.5);
                    hgt =  fmax((double)(0.0), shw[1] - paw_y[leg]);
                    dd =  cst[CF_fore_L1] + cst[CF_fore_rho];
                    a2 =  dd * dd - hgt * hgt;
                    amax =  (a2 > (double)(0.0)) ? (sqrt(a2)) : ((double)(0.0));
                    if (xoff > amax) {
                        xoff =  amax;
                        f_cl[leg] = f_cl[leg] + 1;
}
                    swt[leg * 3] = shw[0] + xoff;
                    swt[leg * 3 + 1] = paw_y[leg];
                    swt[leg * 3 + 2] = pw[2];
}
                else if (act == 2) {
                    for (c = 0; c < (3); ++c) {
                        paw_t[leg * 3 + c] = seat[c];
}
                    f_dp[leg] = 0;
                    f_rp[leg] = f_rp[leg] + 1;
                    f_t[leg] = (double)(0.0);
                    env_t2 =  fore_env(mdl, cst, fr, leg, paw_t, v[3], csti);
                    f_st[leg] = fmax((double)(0.0), env_t2 - (tair + (double)(1.0)));
                    f_cy[leg] = f_st[leg] + tair;
}
                else if (act == 3) {
                    hpt =  mdi[OI_fore_heel_pt + leg];
                    double prl[3];
                    for (c = 0; c < (3); ++c) {
                        prl[c] = (mdl[OF_pt_local + hpt * 3 + c] + mdl[OF_pt_local + (hpt + 1) * 3 + c]) * (double)(0.5);
}
                    double T16[16];
                    fb =  mdi[OI_pt_body + hpt];
                    for (i = 0; i < (16); ++i) {
                        T16[i] = fr[fb * 16 + i];
}
                    double pw[3];
                    apply_point(T16, prl, pw);
                    for (c = 0; c < (3); ++c) {
                        paw_t[leg * 3 + c] = pw[c];
}
                    cc1 =  mdi[OI_fore_coord + leg * 2];
                    cc2 =  mdi[OI_fore_coord + leg * 2 + 1];
                    fore_ik_at(mdl, cst, fr, leg, pw, 1, csti, mdi, &qa1, &qa2, &qa1r, &qa2r, &sata);
                    fore_ik_at(mdl, cst, fr, leg, pw, -1, csti, mdi, &qb1, &qb2, &qb1r, &qb2r, &satb);
                    e0 =  sqrt((qa1 - q[cc1]) * (qa1 - q[cc1]) + (qa2 - q[cc2]) * (qa2 - q[cc2]));
                    e1 =  sqrt((qb1 - q[cc1]) * (qb1 - q[cc1]) + (qb2 - q[cc2]) * (qb2 - q[cc2]));
                    ikb[leg] = 1;
                    if (e1 < e0) {
                        ikb[leg] = -1;
}
                    f_dp[leg] = 0;
                    f_rp[leg] = f_rp[leg] + 1;
                    f_t[leg] = (double)(0.0);
                    env_t2 =  fore_env(mdl, cst, fr, leg, paw_t, v[3], csti);
                    f_st[leg] = fmax((double)(0.0), env_t2 - (tair + (double)(1.0)));
                    f_cy[leg] = f_st[leg] + tair;
}
}
            if (f_t[leg] >= f_cy[leg]) {
                hpt =  mdi[OI_fore_heel_pt + leg];
                double prl[3];
                for (c = 0; c < (3); ++c) {
                    prl[c] = (mdl[OF_pt_local + hpt * 3 + c] + mdl[OF_pt_local + (hpt + 1) * 3 + c]) * (double)(0.5);
}
                double T16[16];
                fb =  mdi[OI_pt_body + hpt];
                for (i = 0; i < (16); ++i) {
                    T16[i] = fr[fb * 16 + i];
}
                double pw[3];
                apply_point(T16, prl, pw);
                for (c = 0; c < (3); ++c) {
                    paw_t[leg * 3 + c] = pw[c];
}
                cc1 =  mdi[OI_fore_coord + leg * 2];
                cc2 =  mdi[OI_fore_coord + leg * 2 + 1];
                fore_ik_at(mdl, cst, fr, leg, pw, 1, csti, mdi, &qa1, &qa2, &qa1r, &qa2r, &sata);
                fore_ik_at(mdl, cst, fr, leg, pw, -1, csti, mdi, &qb1, &qb2, &qb1r, &qb2r, &satb);
                e0 =  sqrt((qa1 - q[cc1]) * (qa1 - q[cc1]) + (qa2 - q[cc2]) * (qa2 - q[cc2]));
                e1 =  sqrt((qb1 - q[cc1]) * (qb1 - q[cc1]) + (qb2 - q[cc2]) * (qb2 - q[cc2]));
                ikb[leg] = 1;
                if (e1 < e0) {
                    ikb[leg] = -1;
}
                f_rp[leg] = f_rp[leg] + 1;
                f_td[leg] = f_td[leg] + 1;
                f_t[leg] = (double)(0.0);
                f_mo[leg] = 0;
                f_dp[leg] = 1;
                if (f_en[leg] != 0) {
                    double m16[16];
                    for (i = 0; i < (16); ++i) {
                        m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
                    double shw[3];
                    double ml[3];
                    ml[0] = mdl[OF_fore_mount_local + leg * 3];
                    ml[1] = mdl[OF_fore_mount_local + leg * 3 + 1];
                    ml[2] = mdl[OF_fore_mount_local + leg * 3 + 2];
                    apply_point(m16, ml, shw);
                    if (paw_t[leg * 3] - shw[0] >= (double)(0.0)) {
                        f_en[leg] = 0;
}
}
                if (f_en[leg] != 0) {
                    env_t2 =  fore_env(mdl, cst, fr, leg, paw_t, v[3], csti);
                    f_st[leg] = fmax((double)(0.0), env_t2 - (tair + (double)(1.0)));
                    f_cy[leg] = f_st[leg] + tair;
}
                else if (f_cv[leg] != 0) {
                    f_st[leg] = cst[CF_duty] / cst[CF_dt];
                    f_cy[leg] = Tf;
}
                else {
                    swing =  ((double)(1.0) - cst[CF_duty]) / cst[CF_dt];
                    slot =  (double)(csti[CI_settle_total]);
                    if (leg == 0) {
                        slot =  slot + (double)(0.25) * Tf;
}
                    else {
                        slot =  slot + (double)(0.75) * Tf;
}
                    while (slot <= (double)(tick) + (double)(1.0) + swing) {
                        slot =  slot + Tf;
}
                    dslot =  slot - ((double)(tick) + (double)(1.0) + Tf);
                    if (fabs(dslot) <= (double)(0.5)) {
                        f_cv[leg] = 1;
                        f_st[leg] = cst[CF_duty] / cst[CF_dt];
                        f_cy[leg] = Tf;
}
                    else {
                        double m16[16];
                        for (i = 0; i < (16); ++i) {
                            m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
                        double shw[3];
                        double ml[3];
                        ml[0] = mdl[OF_fore_mount_local + leg * 3];
                        ml[1] = mdl[OF_fore_mount_local + leg * 3 + 1];
                        ml[2] = mdl[OF_fore_mount_local + leg * 3 + 2];
                        apply_point(m16, ml, shw);
                        offc =  paw_t[leg * 3] - shw[0];
                        vv =  fmax((double)(0.0), v[3]);
                        hgt =  fmax((double)(0.0), shw[1] - paw_t[leg * 3 + 1]);
                        dd =  cst[CF_fore_L1] + cst[CF_fore_rho];
                        a2 =  dd * dd - hgt * hgt;
                        amax =  (a2 > (double)(0.0)) ? (sqrt(a2)) : ((double)(0.0));
                        envc =  (double)(-1.0);
                        if (vv > (double)(1e-9)) {
                            envc =  (offc + amax - vv * cst[CF_dt]) / vv / cst[CF_dt];
}
                        smin =  swing;
                        found =  (int)(0);
                        for (kk = (1); kk < (9); ++kk) {
                            for (ww = 0; ww < (2); ++ww) {
                                step =  (dslot - ((double)(ww) * Tf)) / (double)(kk);
                                stc =  cst[CF_duty] / cst[CF_dt] + step;
                                if (stc < smin - (double)(1e-9)) {
                                    continue;
}
                                if (step > (double)(0.0) && (envc < (double)(0.0) || stc > envc + (double)(1e-9))) {
                                    continue;
}
                                f_st[leg] = stc;
                                f_cy[leg] = stc + swing;
                                if (kk == 1 && ww == 0) {
                                    f_cv[leg] = 1;
}
                                found =  1;
                                break;
}
                            if (found != 0) {
                                break;
}
}
                        if (found == 0) {
                            f_st[leg] = cst[CF_duty] / cst[CF_dt];
                            f_cy[leg] = Tf;
}
}
}
}
}
}
    if (walking != 0 && capt != 0 && cst[CF_height_crit] > (double)(0.0) && h_latched == 0) {
        double m16[16];
        for (i = 0; i < (16); ++i) {
            m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
        double shl[3];
        double ml0[3];
        ml0[0] = mdl[OF_fore_mount_local + 0];
        ml0[1] = mdl[OF_fore_mount_local + 1];
        ml0[2] = mdl[OF_fore_mount_local + 2];
        apply_point(m16, ml0, shl);
        double shr[3];
        double ml1[3];
        ml1[0] = mdl[OF_fore_mount_local + 3];
        ml1[1] = mdl[OF_fore_mount_local + 4];
        ml1[2] = mdl[OF_fore_mount_local + 5];
        apply_point(m16, ml1, shr);
        shmin =  fmin(shl[1], shr[1]);
        if (shmin - cst[CF_height_crit] <= cst[CF_height_floor]) {
            h_latched =  1;
}
}
    if (walking != 0 && capt != 0 && h_latched != 0) {
        for (hl = 0; hl < (2); ++hl) {
            if (h_mo[hl] == 1) {
                if (h_held[hl] != 0) {
                    g1 =  gap_of_k(ptp, pt_radius_g, mdi[OI_hind_heel_pt + hl], cst[CF_plane_y]);
                    g2 =  gap_of_k(ptp, pt_radius_g, mdi[OI_hind_heel_pt + hl] + 1, cst[CF_plane_y]);
                    if (fmin(g1, g2) > cst[CF_k_touch] + cst[CF_k_release]) {
                        h_held[hl] = 0;
}
}
                h_t[hl] = h_t[hl] + (double)(1.0);
                if (h_t[hl] >= tair) {
                    g1 =  gap_of_k(ptp, pt_radius_g, mdi[OI_hind_heel_pt + hl], cst[CF_plane_y]);
                    g2 =  gap_of_k(ptp, pt_radius_g, mdi[OI_hind_heel_pt + hl] + 1, cst[CF_plane_y]);
                    if (fmin(g1, g2) <= cst[CF_k_touch]) {
                        h_mo[hl] = 0;
                        h_t[hl] = (double)(0.0);
                        h_held[hl] = 0;
                        h_lt[hl] = tick;
                        h_tds[hl] = h_tds[hl] + 1;
}
}
}
}
        for (hl = 0; hl < (2); ++hl) {
            o =  1 - hl;
            if (h_mo[hl] != 0) {
                continue;
}
            alt_due =  (int)(0);
            hind_deadline_fn(h_lt[o], h_lt[hl], csti[CI_tair], csti[CI_fold_budget], csti[CI_unload_ticks], &dl, &is_unload);
            if (h_lt[o] != (long long)(0)) {
                conc =  (int)(1);
                if (h_lf[o] < h_lt[hl] && h_lt[o] < h_lt[hl]) {
                    conc =  0;
}
                if (conc != 0 && phi[hl] < cst[CF_toe_off]) {
                    wait =  (cst[CF_toe_off] - phi[hl]) / (cst[CF_dt] / cst[CF_t_cycle]);
                    if ((double)(tick) + wait > (double)(dl)) {
                        alt_due =  1;
}
}
}
            live_slot =  (int)(0);
            if (phi[hl] >= cst[CF_toe_off] && tch[hl] != 0) {
                live_slot =  1;
}
            alt_fire =  (int)(0);
            if (alt_due != 0 && tch[hl] != 0) {
                alt_fire =  1;
}
            if (live_slot == 0 && alt_fire == 0) {
                continue;
}
            gated =  (int)(0);
            gated_b =  (int)(0);
            floor_gated =  (int)(0);
            if (h_mo[o] == 1) {
                gated =  1;
}
            else if (h_lt[o] + (long long)(1) > tick) {
                gated =  1;
                gated_b =  1;
}
            else {
                livec =  (int)(0);
                for (l2 = 0; l2 < (2); ++l2) {
                    mn =  (double)(1e300);
                    for (pt = 0; pt < (2); ++pt) {
                        g =  gap_of_k(ptp, pt_radius_g, 4 + l2 * 2 + pt, cst[CF_plane_y]);
                        if (g < mn) {
                            mn =  g;
}
}
                    if (mn <= cst[CF_k_touch]) {
                        livec =  livec + 1;
}
}
                mn =  (double)(1e300);
                for (pt = 0; pt < (2); ++pt) {
                    g =  gap_of_k(ptp, pt_radius_g, o * 2 + pt, cst[CF_plane_y]);
                    if (g < mn) {
                        mn =  g;
}
}
                if (mn <= cst[CF_k_touch]) {
                    livec =  livec + 1;
}
                if (livec < 2) {
                    floor_gated =  1;
}
                if (alt_fire != 0 && gated == 0 && floor_gated == 0) {
                    promised =  (int)(0);
                    if (tch[o] != 0) {
                        for (l2 = 0; l2 < (2); ++l2) {
                            mn2 =  (double)(1e300);
                            for (pt = 0; pt < (2); ++pt) {
                                g =  gap_of_k(ptp, pt_radius_g, 4 + l2 * 2 + pt, cst[CF_plane_y]);
                                if (g < mn2) {
                                    mn2 =  g;
}
}
                            if (mn2 > cst[CF_k_touch]) {
                                continue;
}
                            if (f_mo[l2] == 0 && f_st[l2] - f_t[l2] >= tair) {
                                promised =  1;
                                break;
}
}
}
                    if (promised == 0) {
                        floor_gated =  1;
}
}
}
            deadline_fire =  (int)(0);
            if (alt_due != 0 && dl > (long long)(0) && (double)(tick) >= (double)(dl)) {
                deadline_fire =  1;
}
            if (floor_gated != 0 && deadline_fire != 0) {
                floor_gated =  0;
}
            if (gated_b != 0 && deadline_fire != 0) {
                gated =  0;
                gated_b =  0;
}
            stall_era_link =  (int)(0);
            if (h_lt[hl] != (long long)(0) && h_lt[hl] - h_lf[hl] == (long long)(csti[CI_tair])) {
                stall_era_link =  1;
}
            if (gated != 0 && gated_b == 0 && floor_gated == 0 && alt_fire != 0 && is_unload != 0 && deadline_fire != 0 && h_held[o] == 0) {
                if (stall_era_link != 0) {
                    ;
}
                else {
                    gated =  0;
}
}
            if (gated != 0 || floor_gated != 0) {
                continue;
}
            h_mo[hl] = 1;
            h_t[hl] = (double)(0.0);
            h_held[hl] = 1;
            h_fi[hl] = h_fi[hl] + 1;
            h_lf[hl] = tick;
            hpt =  mdi[OI_hind_heel_pt + hl];
            double p1[3];
            double p2[3];
            for (c = 0; c < (3); ++c) {
                p1[c] = mdl[OF_pt_local + hpt * 3 + c];
                p2[c] = mdl[OF_pt_local + (hpt + 1) * 3 + c];
}
            double T16[16];
            fb =  mdi[OI_pt_body + hpt];
            for (i = 0; i < (16); ++i) {
                T16[i] = fr[fb * 16 + i];
}
            double w1p[3];
            apply_point(T16, p1, w1p);
            double w2p[3];
            apply_point(T16, p2, w2p);
            fx =  (w1p[0] + w2p[0]) * (double)(0.5);
            fy =  (w1p[1] + w2p[1]) * (double)(0.5);
            fz =  (w1p[2] + w2p[2]) * (double)(0.5);
            h_from[hl * 3] = fx;
            h_from[hl * 3 + 1] = fy;
            h_from[hl * 3 + 2] = fz;
            h_to[hl * 3 + 2] = fz;
            h_py[hl] = fy;
            c0 =  mdi[OI_hind_coord + hl * 4 + 0];
            c1h =  mdi[OI_hind_coord + hl * 4 + 1];
            c2h =  mdi[OI_hind_coord + hl * 4 + 2];
            h_ap[hl] = q[c0] + q[c1h] + q[c2h];
            h_mp[hl] = q[mdi[OI_hind_coord + hl * 4 + 3]];
            h_br[hl] = 1;
            if (q[c1h] < (double)(0.0)) {
                h_br[hl] = -1;
}
            xoff =  v_eff * (cst[CF_duty] * cst[CF_t_cycle]) * (double)(0.5);
            double m16[16];
            for (i = 0; i < (16); ++i) {
                m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
            double hipw[3];
            double mlh[3];
            mlh[0] = mdl[OF_hind_mount + hl * 3];
            mlh[1] = mdl[OF_hind_mount + hl * 3 + 1];
            mlh[2] = mdl[OF_hind_mount + hl * 3 + 2];
            apply_point(m16, mlh, hipw);
            hgt =  fmax((double)(0.0), hipw[1] - h_py[hl]);
            a2m =  cst[CF_hind_L1] + cst[CF_hind_L2];
            dxs =  cst[CF_hind_xm] * cos(h_ap[hl]);
            dys =  hgt + cst[CF_hind_xm] * sin(h_ap[hl]);
            under =  a2m * a2m - dys * dys;
            xmax =  dxs;
            if (under > (double)(0.0)) {
                xmax =  dxs + sqrt(under);
}
            if (xoff > xmax) {
                xoff =  xmax;
}
            h_xo[hl] = xoff;
            h_to[hl * 3] = hipw[0] + xoff;
            h_to[hl * 3 + 1] = h_py[hl];
}
}
    if (walking != 0 && csti[CI_capture_enabled] != 0) {
        double hx[8];
        double hz[8];
        hn =  (int)(0);
        for (k = 0; k < (8); ++k) {
            g =  gap_of_k(ptp, pt_radius_g, k, cst[CF_plane_y]);
            if (csti[CI_contact] != 0 && g <= cst[CF_k_touch]) {
                hx[hn] = ptp[k * 3];
                hz[hn] = ptp[k * 3 + 2];
                hn =  hn + 1;
}
}
        mtot =  (double)(0.0);
        comx =  (double)(0.0);
        comy =  (double)(0.0);
        comz =  (double)(0.0);
        double cw[3];
        double cb[3];
        double T16b[16];
        for (b = (1); b < (csti[CI_nbod]); ++b) {
            mb =  mdl[OF_body_mass + b];
            if (mb == (double)(0.0)) {
                continue;
}
            cb[0] = mdl[OF_body_com + b * 3];
            cb[1] = mdl[OF_body_com + b * 3 + 1];
            cb[2] = mdl[OF_body_com + b * 3 + 2];
            for (i = 0; i < (16); ++i) {
                T16b[i] = fr[b * 16 + i];
}
            apply_point(T16b, cb, cw);
            comx =  comx + mb * cw[0];
            comy =  comy + mb * cw[1];
            comz =  comz + mb * cw[2];
            mtot =  mtot + mb;
}
        comx =  comx / mtot;
        comz =  comz / mtot;
        if (hn >= 3) {
            for (i = 0; i < (hn); ++i) {
                for (j = (i + 1); j < (hn); ++j) {
                    if (hx[j] < hx[i] || (hx[j] == hx[i] && hz[j] < hz[i])) {
                        tx =  hx[i];
                        hx[i] = hx[j];
                        hx[j] = tx;
                        tz =  hz[i];
                        hz[i] = hz[j];
                        hz[j] = tz;
}
}
}
            double ux[8];
            double uz[8];
            un =  (int)(0);
            for (i = 0; i < (hn); ++i) {
                if (un == 0 || hx[i] != ux[un - 1] || hz[i] != uz[un - 1]) {
                    ux[un] = hx[i];
                    uz[un] = hz[i];
                    un =  un + 1;
}
}
            if (un >= 3) {
                double chx[16];
                double chz[16];
                kk =  (int)(0);
                for (i = 0; i < (un); ++i) {
                    while (kk >= 2) {
                        cr =  (chx[kk - 1] - chx[kk - 2]) * (uz[i] - chz[kk - 2]) - (chz[kk - 1] - chz[kk - 2]) * (ux[i] - chx[kk - 2]);
                        if (cr <= (double)(0.0)) {
                            kk =  kk - 1;
}
                        else {
                            break;
}
}
                    chx[kk] = ux[i];
                    chz[kk] = uz[i];
                    kk =  kk + 1;
}
                t2 =  kk + 1;
                for (i = (un - 1); i > (-1); --i) {
                    while (kk >= t2) {
                        cr =  (chx[kk - 1] - chx[kk - 2]) * (uz[i] - chz[kk - 2]) - (chz[kk - 1] - chz[kk - 2]) * (ux[i] - chx[kk - 2]);
                        if (cr <= (double)(0.0)) {
                            kk =  kk - 1;
}
                        else {
                            break;
}
}
                    chx[kk] = ux[i];
                    chz[kk] = uz[i];
                    kk =  kk + 1;
}
                cn =  kk - 1;
                if (cn >= 3) {
                    v_bound =  cst[CF_mu] * cst[CF_gy] * ((double)(1.0) - cst[CF_capture_phi]) * cst[CF_t_cycle];
                    slip_mx =  (double)(0.0);
                    for (r = 0; r < (4); ++r) {
                        g =  gap_of_k(ptp, pt_radius_g, r * 2, cst[CF_plane_y]);
                        if (! (csti[CI_contact] != 0 && g <= cst[CF_k_touch])) {
                            continue;
}
                        svx =  (double)(0.0);
                        svz =  (double)(0.0);
                        for (i = 0; i < (18); ++i) {
                            svx =  svx + ptJ[(r * 3 + 0) * 18 + i] * v[i];
                            svz =  svz + ptJ[(r * 3 + 2) * 18 + i] * v[i];
}
                        sl =  sqrt(svx * svx + svz * svz);
                        if (sl > slip_mx) {
                            slip_mx =  sl;
}
}
                    if (slip_mx <= v_bound) {
                        side =  (int)(0);
                        viol =  (int)(-1);
                        for (i = 0; i < (cn); ++i) {
                            j =  (i + 1) % cn;
                            cr =  (chx[j] - chx[i]) * (comz - chz[i]) - (chz[j] - chz[i]) * (comx - chx[i]);
                            if (fabs(cr) < (double)(1e-15)) {
                                continue;
}
                            s =  (cr > (double)(0.0)) ? ((int)(1)) : ((int)(-1));
                            if (side == 0) {
                                side =  s;
}
                            else if (s != side) {
                                viol =  i;
                                break;
}
}
                        if (viol >= 0) {
                            i =  viol;
                            j =  (viol + 1) % cn;
                            ex =  chx[j] - chx[i];
                            ez =  chz[j] - chz[i];
                            nl =  sqrt(ex * ex + ez * ez);
                            if (nl >= (double)(1e-12)) {
                                nx =  ez / nl;
                                nz =  -ex / nl;
                                cx =  (double)(0.0);
                                cz =  (double)(0.0);
                                for (i2 = 0; i2 < (cn); ++i2) {
                                    cx =  cx + chx[i2];
                                    cz =  cz + chz[i2];
}
                                cx =  cx / (double)(cn);
                                cz =  cz / (double)(cn);
                                if ((cx - chx[i]) * nx + (cz - chz[i]) * nz < (double)(0.0)) {
                                    nx =  -nx;
                                    nz =  -nz;
}
                                if (v[3] * nx + v[5] * nz > (double)(0.0)) {
                                    for (leg = 0; leg < (2); ++leg) {
                                        touching_leg =  (int)(0);
                                        g0 =  gap_of_k(ptp, pt_radius_g, leg * 2, cst[CF_plane_y]);
                                        g1 =  gap_of_k(ptp, pt_radius_g, leg * 2 + 1, cst[CF_plane_y]);
                                        if (csti[CI_contact] != 0 && fmin(g0, g1) <= cst[CF_k_touch]) {
                                            touching_leg =  1;
}
                                        if (touching_leg == 0 && phi[leg] >= cst[CF_toe_off]) {
                                            phi[leg] = cst[CF_capture_phi];
                                            break;
}
}
}
}
}
}
}
}
}
}
    rc =  (int)(0);
    collapsed =  (int)(0);
    for (i = 0; i < (18); ++i) {
        a_q[e * 18 + i] = q[i];
        a_v[e * 18 + i] = v[i];
        a_work[e * 18 + i] = w[i];
        a_last_torque[e * 18 + i] = lta[i];
}
    for (d = 0; d < (12); ++d) {
        a_battery[e * 12 + d] = bat[d];
}
    a_battery_post[e] = bat_post;
    a_phi[e * 2] = phi[0];
    a_phi[e * 2 + 1] = phi[1];
    a_touching[e * 2] = tch[0];
    a_touching[e * 2 + 1] = tch[1];
    a_captured[e] = capt;
    a_settle[e] = settle_n;
    a_ik_branch[e * 2] = ikb[0];
    a_ik_branch[e * 2 + 1] = ikb[1];
    for (l = 0; l < (2); ++l) {
        for (c = 0; c < (3); ++c) {
            a_paw_target[e * 6 + l * 3 + c] = paw_t[l * 3 + c];
            a_swing_from[e * 6 + l * 3 + c] = swf[l * 3 + c];
            a_swing_to[e * 6 + l * 3 + c] = swt[l * 3 + c];
            a_hind_from[e * 6 + l * 3 + c] = h_from[l * 3 + c];
            a_hind_to[e * 6 + l * 3 + c] = h_to[l * 3 + c];
}
        a_paw_plant_y[e * 2 + l] = paw_y[l];
        a_fore_t[e * 2 + l] = f_t[l];
        a_fore_stance[e * 2 + l] = f_st[l];
        a_fore_cycle[e * 2 + l] = f_cy[l];
        a_fore_mode[e * 2 + l] = f_mo[l];
        a_fore_entry[e * 2 + l] = f_en[l];
        a_fore_conv[e * 2 + l] = f_cv[l];
        a_fore_td_plant[e * 2 + l] = f_dp[l];
        a_fore_clamped[e * 2 + l] = f_cl[l];
        a_fore_replants[e * 2 + l] = f_rp[l];
        a_fore_td_count[e * 2 + l] = f_td[l];
        a_hind_mode[e * 2 + l] = h_mo[l];
        a_hind_t[e * 2 + l] = h_t[l];
        a_hind_plant_y[e * 2 + l] = h_py[l];
        a_hind_ap[e * 2 + l] = h_ap[l];
        a_hind_mp[e * 2 + l] = h_mp[l];
        a_hind_branch[e * 2 + l] = h_br[l];
        a_hind_held[e * 2 + l] = h_held[l];
        a_hind_last_fire[e * 2 + l] = h_lf[l];
        a_hind_last_td[e * 2 + l] = h_lt[l];
        a_hind_fires[e * 2 + l] = h_fi[l];
        a_hind_tds[e * 2 + l] = h_tds[l];
        a_hind_xoff[e * 2 + l] = h_xo[l];
}
    a_height_latched[e] = h_latched;
    a_cmd_vx[e] = cmd_v;
    a_cmd_live[e] = cmd_on;
    a_cmd_first_tick[e] = cmd_first;
    a_cmd_fires[e] = cmd_fires;
    a_adv_calls[e] = adv[0];
    bat_sum =  (double)(0.0);
    for (d = 0; d < (12); ++d) {
        bat_sum =  bat_sum + bat[d];
}
    rb[e * 6 + 0] = q[3];
    rb[e * 6 + 1] = q[4];
    rb[e * 6 + 2] = v[3];
    rb[e * 6 + 3] = phi[0];
    rb[e * 6 + 4] = phi[1];
    rb[e * 6 + 5] = bat_sum;
    rbi[e * 6 + 0] = h_fi[0];
    rbi[e * 6 + 1] = h_fi[1];
    rbi[e * 6 + 2] = f_mo[0];
    rbi[e * 6 + 3] = f_mo[1];
    rbi[e * 6 + 4] = tch[0];
    rbi[e * 6 + 5] = tch[1];
}

__global__ void tick_integ_kernel(double* mdl, int* mdi, double* cst, int* csti, double* a_q, double* a_v, double* a_work, double* a_last_torque, double* a_battery, double* a_battery_post, double* a_phi, int* a_touching, int* a_captured, int* a_settle, int* a_ik_branch, double* a_paw_target, double* a_paw_plant_y, double* a_swing_from, double* a_swing_to, double* a_fore_t, double* a_fore_stance, double* a_fore_cycle, int* a_fore_mode, int* a_fore_entry, int* a_fore_conv, int* a_fore_td_plant, int* a_fore_clamped, int* a_fore_replants, int* a_fore_td_count, int* a_hind_mode, double* a_hind_t, double* a_hind_from, double* a_hind_to, double* a_hind_plant_y, double* a_hind_ap, double* a_hind_mp, int* a_hind_branch, int* a_hind_held, long long* a_hind_last_fire, long long* a_hind_last_td, int* a_hind_fires, int* a_hind_tds, double* a_hind_xoff, int* a_height_latched, double* a_cmd_vx, int* a_cmd_live, long long* a_cmd_first_tick, int* a_cmd_fires, long long* a_ticks, int* a_adv_calls, int* a_refused, int* a_refused_class, int* a_collapsed, double* rb, int* rbi, int* a_rc) {
    double ne;
    int rc;
    double tick;
    int i;
    int d;
    double bat_post;
    double capt;
    double settle_n;
    int l;
    int c;
    double h_latched;
    double cmd_v;
    double cmd_on;
    double cmd_first;
    double cmd_fires;
    double Tf;
    double tair;
    int walking;
    int round_n;
    int sub;
    double pot;
    double target;
    int hl;
    int ji;
    double sg;
    double carch;
    int cc2;
    double qh_h;
    double qk_h;
    double qa_h;
    int fl;
    double q1f;
    double q2f;
    double q1rx;
    double q2rx;
    double satf;
    double tq;
    double cap;
    double amp;
    double tpost;
    int rcs;
    int enabled;
    int store;
    double wd;
    double lo;
    double hi;
    int j;
    double mid;
    int dsc;
    double wdc;
    double spent;
    int collapsed;
    double bat_sum;
    double pt_radius_g[((OF_pt_radius + 8) - (OF_pt_radius))];
    for (int _si0 = 0; _si0 < ((OF_pt_radius + 8) - (OF_pt_radius)); ++_si0) pt_radius_g[_si0] = mdl[(OF_pt_radius) + _si0];
    int e = blockIdx.x * blockDim.x + threadIdx.x;
    ne =  cu_total_q / 18;
    if (e >= ne) {
        return;
}
    if (a_refused[e] != 0 || a_collapsed[e] != 0) {
        return;
}
    rc =  (int)(0);
    tick =  a_ticks[e];
    double q[18];
    double v[18];
    double w[18];
    double ltau[18];
    for (i = 0; i < (18); ++i) {
        q[i] = a_q[e * 18 + i];
        v[i] = a_v[e * 18 + i];
        w[i] = a_work[e * 18 + i];
        ltau[i] = a_last_torque[e * 18 + i];
}
    double bat[12];
    for (d = 0; d < (12); ++d) {
        bat[d] = a_battery[e * 12 + d];
}
    bat_post =  a_battery_post[e];
    double phi[2];
    phi[0] = a_phi[e * 2];
    phi[1] = a_phi[e * 2 + 1];
    int tch[2];
    tch[0] = a_touching[e * 2];
    tch[1] = a_touching[e * 2 + 1];
    capt =  a_captured[e];
    settle_n =  a_settle[e];
    int ikb[2];
    ikb[0] = a_ik_branch[e * 2];
    ikb[1] = a_ik_branch[e * 2 + 1];
    double paw_t[6];
    double paw_y[2];
    double swf[6];
    double swt[6];
    double f_t[2];
    double f_st[2];
    double f_cy[2];
    int f_mo[2];
    int f_en[2];
    int f_cv[2];
    int f_dp[2];
    int f_cl[2];
    int f_rp[2];
    int f_td[2];
    for (l = 0; l < (2); ++l) {
        for (c = 0; c < (3); ++c) {
            paw_t[l * 3 + c] = a_paw_target[e * 6 + l * 3 + c];
            swf[l * 3 + c] = a_swing_from[e * 6 + l * 3 + c];
            swt[l * 3 + c] = a_swing_to[e * 6 + l * 3 + c];
}
        paw_y[l] = a_paw_plant_y[e * 2 + l];
        f_t[l] = a_fore_t[e * 2 + l];
        f_st[l] = a_fore_stance[e * 2 + l];
        f_cy[l] = a_fore_cycle[e * 2 + l];
        f_mo[l] = a_fore_mode[e * 2 + l];
        f_en[l] = a_fore_entry[e * 2 + l];
        f_cv[l] = a_fore_conv[e * 2 + l];
        f_dp[l] = a_fore_td_plant[e * 2 + l];
        f_cl[l] = a_fore_clamped[e * 2 + l];
        f_rp[l] = a_fore_replants[e * 2 + l];
        f_td[l] = a_fore_td_count[e * 2 + l];
}
    int h_mo[2];
    double h_t[2];
    double h_from[6];
    double h_to[6];
    double h_py[2];
    double h_ap[2];
    double h_mp[2];
    int h_br[2];
    int h_held[2];
    long long h_lf[2];
    long long h_lt[2];
    int h_fi[2];
    int h_tds[2];
    double h_xo[2];
    for (l = 0; l < (2); ++l) {
        h_mo[l] = a_hind_mode[e * 2 + l];
        h_t[l] = a_hind_t[e * 2 + l];
        h_py[l] = a_hind_plant_y[e * 2 + l];
        h_ap[l] = a_hind_ap[e * 2 + l];
        h_mp[l] = a_hind_mp[e * 2 + l];
        h_br[l] = a_hind_branch[e * 2 + l];
        h_held[l] = a_hind_held[e * 2 + l];
        h_lf[l] = a_hind_last_fire[e * 2 + l];
        h_lt[l] = a_hind_last_td[e * 2 + l];
        h_fi[l] = a_hind_fires[e * 2 + l];
        h_tds[l] = a_hind_tds[e * 2 + l];
        h_xo[l] = a_hind_xoff[e * 2 + l];
        for (c = 0; c < (3); ++c) {
            h_from[l * 3 + c] = a_hind_from[e * 6 + l * 3 + c];
            h_to[l * 3 + c] = a_hind_to[e * 6 + l * 3 + c];
}
}
    h_latched =  a_height_latched[e];
    cmd_v =  a_cmd_vx[e];
    cmd_on =  a_cmd_live[e];
    cmd_first =  a_cmd_first_tick[e];
    cmd_fires =  a_cmd_fires[e];
    int adv[1];
    adv[0] = a_adv_calls[e];
    Tf =  cst[CF_t_cycle] / cst[CF_dt];
    tair =  (double)(csti[CI_tair]);
    walking =  (int)(1);
    if (csti[CI_gait_enabled] == 0 || settle_n > 0 || csti[CI_reflex_level] == 0) {
        walking =  0;
}
    double M[324];
    double gv[18];
    double bv[18];
    double fr[224];
    double frd[224];
    double frdd[224];
    double axw[54];
    double axpiv[54];
    double axdir[54];
    double ptp[24];
    double ptJ[216];
    double ptcop[12];
    double ptbias[12];
    double inv[324];
    double free[18];
    double qa[18];
    double va[18];
    double qb[18];
    double vb[18];
    double qc[18];
    double vc[18];
    double qd[18];
    double vd[18];
    double qe[18];
    double ve[18];
    double we[18];
    double sq[576];
    double sh16[16];
    int sdep[16];
    int scl[16];
    double tr_q[18];
    double tr_v[18];
    double tr_w[18];
    double cd_q[18];
    double cd_v[18];
    double cd_w[18];
    double tau[18];
    double srq[18];
    double srv[18];
    double scales[13];
    round_n =  (int)(0);
    int dsf[1];
    double trial_q[18];
    double trial_v[18];
    double trial_w[18];
    double o_q[18];
    double o_v[18];
    double o_w[18];
    double cur_w[18];
    double eff[18];
    double lta[18];
    sub =  (int)(0);
    while (sub < 4) {
        sub =  sub + 1;
        for (i = 0; i < (18); ++i) {
            tau[i] = (double)(0.0);
            eff[i] = (double)(0.0);
}
        pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
        d =  (int)(0);
        while (d < 12) {
            d =  d + 1;
            c =  mdi[OI_drive_coord + d - 1];
            if (csti[CI_power] == 0 || ((csti[CI_drive_en] >> (d - 1)) & 1) == 0 || bat[d - 1] <= (double)(1e-12)) {
                continue;
}
            target =  (double)(0.0);
            if (csti[CI_gait_enabled] != 0) {
                if ((d - 1) < 8) {
                    hl =  (d - 1) / 4;
                    ji =  (d - 1) % 4;
                    if (h_mo[hl] == 1) {
                        sg =  h_t[hl] / tair;
                        if (sg < (double)(0.0)) {
                            sg =  (double)(0.0);
}
                        if (sg > (double)(1.0)) {
                            sg =  (double)(1.0);
}
                        carch =  (double)(2.0) * mdl[OF_pt_radius + mdi[OI_hind_heel_pt + hl]];
                        double tgt[3];
                        if (h_held[hl] != 0) {
                            for (cc2 = 0; cc2 < (3); ++cc2) {
                                tgt[cc2] = h_from[hl * 3 + cc2];
}
                            tgt[1] = tgt[1] + carch;
}
                        else {
                            for (cc2 = 0; cc2 < (3); ++cc2) {
                                tgt[cc2] = h_from[hl * 3 + cc2] + (h_to[hl * 3 + cc2] - h_from[hl * 3 + cc2]) * sg;
}
                            tgt[1] = tgt[1] + carch * sin(PI * sg);
}
                        hind_ik_at(mdl, cst, fr, tgt, h_ap[hl], h_br[hl], csti, &qh_h, &qk_h, &qa_h);
                        if (ji == 0) {
                            target =  qh_h;
}
                        else if (ji == 1) {
                            target =  qk_h;
}
                        else if (ji == 2) {
                            target =  qa_h;
}
                        else {
                            target =  h_mp[hl];
}
}
                    else {
                        double qstar[18];
                        tables_at(mdl, phi[hl], qstar);
                        target =  qstar[ji];
                        if (h_latched != 0 && tch[hl] != 0) {
                            target =  target + ltau[c] / mdl[OF_kp + d];
}
}
}
                else {
                    fl =  (d - 9) / 2;
                    ji =  (d - 9) % 2;
                    if (capt != 0) {
                        double plt[3];
                        paw_leg(paw_t, fl, plt);
                        fore_ik_at(mdl, cst, fr, fl, plt, ikb[fl], csti, mdi, &q1f, &q2f, &q1rx, &q2rx, &satf);
                        if (ji == 0) {
                            target =  q1f;
}
                        else {
                            target =  q2f;
}
}
                    else {
                        if (ji == 0) {
                            target =  cst[CF_fore_pose_sh];
}
                        else {
                            target =  cst[CF_fore_pose_el];
}
}
}
}
            tq =  mdl[OF_kp + d - 1] * (target - q[c]) - mdl[OF_kd + d - 1] * v[c];
            cap =  mdl[OF_drive_cap + d - 1];
            tq =  fmin(cap, fmax(-cap, tq));
            tau[c] = tq;
}
        if (csti[CI_power] != 0 && csti[CI_posture_drive] != 0 && bat_post > (double)(1e-12)) {
            amp =  (double)(0.0);
            if (csti[CI_gait_enabled] != 0) {
                if (csti[CI_settle_total] > 0) {
                    amp =  (double)(1.0) - (double)(settle_n) / (double)(csti[CI_settle_total]);
}
                else {
                    amp =  (double)(1.0);
}
}
            tpost =  amp * vault_at(mdl, phi[0]);
            tq =  cst[CF_kp_post] * (tpost - q[2]) - cst[CF_kd_post] * v[2];
            cap =  mdl[OF_drive_cap + 0];
            tq =  fmin(cap, fmax(-cap, tq));
            tau[2] = tq;
}
        for (d = 0; d < (13); ++d) {
            scales[d] = (double)(1.0);
}
        adv[0] = 0;
        for (i = 0; i < (18); ++i) {
            cur_w[i] = w[i];
}
        int rca[1];
        rcs =  (int)(0);
        if (sub == 0) {
            adv[0] = 0;
}
        for (i = 0; i < (18); ++i) {
            eff[i] = tau[i];
}
        for (d = 0; d < (12); ++d) {
            eff[mdi[OI_drive_coord + d]] = tau[mdi[OI_drive_coord + d]] * scales[d];
}
        eff[2] = tau[2] * scales[12];
        advance(q, v, w, eff, cst[CF_dt] * (double)(0.25), mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl, adv, rca, o_q, o_v, o_w, csti, mdi);
        for (i = 0; i < (18); ++i) {
            trial_q[i] = o_q[i];
            trial_v[i] = o_v[i];
            trial_w[i] = o_w[i];
}
        if (rca[0] != 0) {
            rc =  rca[0];
}
        if (rc == 0) {
            round_n =  (int)(0);
            dsf[0] = 0;
            while (round_n < 8) {
                dsf[0] = 0;
                d =  (int)(0);
                while (d < 13) {
                    d =  d + 1;
                    c =  ((d - 1) == 12) ? (2) : (mdi[OI_drive_coord + d - 1]);
                    enabled =  (int)(1);
                    if (csti[CI_power] == 0) {
                        enabled =  0;
}
                    else if ((d - 1) < 12 && ((csti[CI_drive_en] >> (d - 1)) & 1) == 0) {
                        enabled =  0;
}
                    else if ((d - 1) == 12 && csti[CI_posture_drive] == 0) {
                        enabled =  0;
}
                    if (enabled == 0) {
                        continue;
}
                    store =  ((d - 1) < 12) ? (bat[d - 1]) : (bat_post);
                    wd =  trial_w[c] - cur_w[c];
                    if (wd < (double)(0.0)) {
                        wd =  (double)(0.0);
}
                    if (wd > store) {
                        lo =  (double)(0.0);
                        hi =  (double)(1.0);
                        j =  (int)(0);
                        while (j < 40) {
                            j =  j + 1;
                            mid =  (lo + hi) * (double)(0.5);
                            scales[d] = mid;
                            for (i = 0; i < (18); ++i) {
                                eff[i] = tau[i];
}
                            for (dsc = 0; dsc < (12); ++dsc) {
                                eff[mdi[OI_drive_coord + dsc]] = tau[mdi[OI_drive_coord + dsc]] * scales[dsc];
}
                            eff[2] = tau[2] * scales[12];
                            advance(q, v, w, eff, cst[CF_dt] * (double)(0.25), mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl, adv, rca, o_q, o_v, o_w, csti, mdi);
                            if (rca[0] != 0) {
                                rc =  rca[0];
}
                            wdc =  o_w[c] - cur_w[c];
                            if (wdc < (double)(0.0)) {
                                wdc =  (double)(0.0);
}
                            if (wdc <= store) {
                                lo =  mid;
                                for (i = 0; i < (18); ++i) {
                                    trial_q[i] = o_q[i];
                                    trial_v[i] = o_v[i];
                                    trial_w[i] = o_w[i];
}
}
                            else {
                                hi =  mid;
}
}
                        scales[d - 1] = lo;
                        dsf[0] = 1;
}
}
                if (dsf[0] == 0) {
                    break;
}
                for (i = 0; i < (18); ++i) {
                    eff[i] = tau[i];
}
                for (dsc = 0; dsc < (12); ++dsc) {
                    eff[mdi[OI_drive_coord + dsc]] = tau[mdi[OI_drive_coord + dsc]] * scales[dsc];
}
                eff[2] = tau[2] * scales[12];
                advance(q, v, w, eff, cst[CF_dt] * (double)(0.25), mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl, adv, rca, o_q, o_v, o_w, csti, mdi);
                for (i = 0; i < (18); ++i) {
                    trial_q[i] = o_q[i];
                    trial_v[i] = o_v[i];
                    trial_w[i] = o_w[i];
}
                if (rca[0] != 0) {
                    rc =  rca[0];
}
                if (rc != 0) {
                    break;
}
                if (round_n == 7) {
                    for (d = 0; d < (13); ++d) {
                        c =  (d == 12) ? (2) : (mdi[OI_drive_coord + d]);
                        enabled =  (int)(1);
                        if (csti[CI_power] == 0) {
                            enabled =  0;
}
                        else if (d < 12 && ((csti[CI_drive_en] >> d) & 1) == 0) {
                            enabled =  0;
}
                        else if (d == 12 && csti[CI_posture_drive] == 0) {
                            enabled =  0;
}
                        if (enabled == 0) {
                            continue;
}
                        store =  (d < 12) ? (bat[d]) : (bat_post);
                        wdc =  trial_w[c] - cur_w[c];
                        if (wdc < (double)(0.0)) {
                            wdc =  (double)(0.0);
}
                        if (wdc > store) {
                            rc =  4;
}
}
}
                round_n =  round_n + 1;
}
}
        if (rc != 0) {
            break;
}
        for (d = 0; d < (13); ++d) {
            c =  (d == 12) ? (2) : (mdi[OI_drive_coord + d]);
            store =  (d < 12) ? (bat[d]) : (bat_post);
            spent =  trial_w[c] - cur_w[c];
            if (spent < (double)(0.0)) {
                spent =  (double)(0.0);
}
            if (d < 12) {
                bat[d] = store - spent;
}
            else {
                bat_post =  store - spent;
}
}
        for (i = 0; i < (18); ++i) {
            q[i] = trial_q[i];
            v[i] = trial_v[i];
            w[i] = trial_w[i];
}
        for (d = 0; d < (12); ++d) {
            lta[mdi[OI_drive_coord + d]] = lta[mdi[OI_drive_coord + d]] + tau[mdi[OI_drive_coord + d]] * (double)(0.25);
}
        lta[2] = lta[2] + tau[2] * (double)(0.25);
}
    a_rc[e] = rc;
    rc =  (int)(0);
    collapsed =  (int)(0);
    for (i = 0; i < (18); ++i) {
        a_q[e * 18 + i] = q[i];
        a_v[e * 18 + i] = v[i];
        a_work[e * 18 + i] = w[i];
        a_last_torque[e * 18 + i] = lta[i];
}
    for (d = 0; d < (12); ++d) {
        a_battery[e * 12 + d] = bat[d];
}
    a_battery_post[e] = bat_post;
    a_phi[e * 2] = phi[0];
    a_phi[e * 2 + 1] = phi[1];
    a_touching[e * 2] = tch[0];
    a_touching[e * 2 + 1] = tch[1];
    a_captured[e] = capt;
    a_settle[e] = settle_n;
    a_ik_branch[e * 2] = ikb[0];
    a_ik_branch[e * 2 + 1] = ikb[1];
    for (l = 0; l < (2); ++l) {
        for (c = 0; c < (3); ++c) {
            a_paw_target[e * 6 + l * 3 + c] = paw_t[l * 3 + c];
            a_swing_from[e * 6 + l * 3 + c] = swf[l * 3 + c];
            a_swing_to[e * 6 + l * 3 + c] = swt[l * 3 + c];
            a_hind_from[e * 6 + l * 3 + c] = h_from[l * 3 + c];
            a_hind_to[e * 6 + l * 3 + c] = h_to[l * 3 + c];
}
        a_paw_plant_y[e * 2 + l] = paw_y[l];
        a_fore_t[e * 2 + l] = f_t[l];
        a_fore_stance[e * 2 + l] = f_st[l];
        a_fore_cycle[e * 2 + l] = f_cy[l];
        a_fore_mode[e * 2 + l] = f_mo[l];
        a_fore_entry[e * 2 + l] = f_en[l];
        a_fore_conv[e * 2 + l] = f_cv[l];
        a_fore_td_plant[e * 2 + l] = f_dp[l];
        a_fore_clamped[e * 2 + l] = f_cl[l];
        a_fore_replants[e * 2 + l] = f_rp[l];
        a_fore_td_count[e * 2 + l] = f_td[l];
        a_hind_mode[e * 2 + l] = h_mo[l];
        a_hind_t[e * 2 + l] = h_t[l];
        a_hind_plant_y[e * 2 + l] = h_py[l];
        a_hind_ap[e * 2 + l] = h_ap[l];
        a_hind_mp[e * 2 + l] = h_mp[l];
        a_hind_branch[e * 2 + l] = h_br[l];
        a_hind_held[e * 2 + l] = h_held[l];
        a_hind_last_fire[e * 2 + l] = h_lf[l];
        a_hind_last_td[e * 2 + l] = h_lt[l];
        a_hind_fires[e * 2 + l] = h_fi[l];
        a_hind_tds[e * 2 + l] = h_tds[l];
        a_hind_xoff[e * 2 + l] = h_xo[l];
}
    a_height_latched[e] = h_latched;
    a_cmd_vx[e] = cmd_v;
    a_cmd_live[e] = cmd_on;
    a_cmd_first_tick[e] = cmd_first;
    a_cmd_fires[e] = cmd_fires;
    a_adv_calls[e] = adv[0];
    bat_sum =  (double)(0.0);
    for (d = 0; d < (12); ++d) {
        bat_sum =  bat_sum + bat[d];
}
    rb[e * 6 + 0] = q[3];
    rb[e * 6 + 1] = q[4];
    rb[e * 6 + 2] = v[3];
    rb[e * 6 + 3] = phi[0];
    rb[e * 6 + 4] = phi[1];
    rb[e * 6 + 5] = bat_sum;
    rbi[e * 6 + 0] = h_fi[0];
    rbi[e * 6 + 1] = h_fi[1];
    rbi[e * 6 + 2] = f_mo[0];
    rbi[e * 6 + 3] = f_mo[1];
    rbi[e * 6 + 4] = tch[0];
    rbi[e * 6 + 5] = tch[1];
}

__global__ void tick_post_kernel(double* mdl, int* mdi, double* cst, int* csti, double* a_q, double* a_v, double* a_work, double* a_last_torque, double* a_battery, double* a_battery_post, double* a_phi, int* a_touching, int* a_captured, int* a_settle, int* a_ik_branch, double* a_paw_target, double* a_paw_plant_y, double* a_swing_from, double* a_swing_to, double* a_fore_t, double* a_fore_stance, double* a_fore_cycle, int* a_fore_mode, int* a_fore_entry, int* a_fore_conv, int* a_fore_td_plant, int* a_fore_clamped, int* a_fore_replants, int* a_fore_td_count, int* a_hind_mode, double* a_hind_t, double* a_hind_from, double* a_hind_to, double* a_hind_plant_y, double* a_hind_ap, double* a_hind_mp, int* a_hind_branch, int* a_hind_held, long long* a_hind_last_fire, long long* a_hind_last_td, int* a_hind_fires, int* a_hind_tds, double* a_hind_xoff, int* a_height_latched, double* a_cmd_vx, int* a_cmd_live, long long* a_cmd_first_tick, int* a_cmd_fires, long long* a_ticks, int* a_adv_calls, int* a_refused, int* a_refused_class, int* a_collapsed, double* rb, int* rbi, int* a_rc) {
    double ne;
    int rc;
    double tick;
    int i;
    int d;
    double bat_post;
    double capt;
    double settle_n;
    int l;
    int c;
    double h_latched;
    double cmd_v;
    double cmd_on;
    double cmd_first;
    double cmd_fires;
    double Tf;
    double tair;
    int walking;
    int round_n;
    int collapsed;
    double bat_sum;
    double pt_radius_g[((OF_pt_radius + 8) - (OF_pt_radius))];
    for (int _si0 = 0; _si0 < ((OF_pt_radius + 8) - (OF_pt_radius)); ++_si0) pt_radius_g[_si0] = mdl[(OF_pt_radius) + _si0];
    int e = blockIdx.x * blockDim.x + threadIdx.x;
    ne =  cu_total_q / 18;
    if (e >= ne) {
        return;
}
    if (a_refused[e] != 0 || a_collapsed[e] != 0) {
        return;
}
    rc =  (int)(0);
    tick =  a_ticks[e];
    double q[18];
    double v[18];
    double w[18];
    double ltau[18];
    for (i = 0; i < (18); ++i) {
        q[i] = a_q[e * 18 + i];
        v[i] = a_v[e * 18 + i];
        w[i] = a_work[e * 18 + i];
        ltau[i] = a_last_torque[e * 18 + i];
}
    double bat[12];
    for (d = 0; d < (12); ++d) {
        bat[d] = a_battery[e * 12 + d];
}
    bat_post =  a_battery_post[e];
    double phi[2];
    phi[0] = a_phi[e * 2];
    phi[1] = a_phi[e * 2 + 1];
    int tch[2];
    tch[0] = a_touching[e * 2];
    tch[1] = a_touching[e * 2 + 1];
    capt =  a_captured[e];
    settle_n =  a_settle[e];
    int ikb[2];
    ikb[0] = a_ik_branch[e * 2];
    ikb[1] = a_ik_branch[e * 2 + 1];
    double paw_t[6];
    double paw_y[2];
    double swf[6];
    double swt[6];
    double f_t[2];
    double f_st[2];
    double f_cy[2];
    int f_mo[2];
    int f_en[2];
    int f_cv[2];
    int f_dp[2];
    int f_cl[2];
    int f_rp[2];
    int f_td[2];
    for (l = 0; l < (2); ++l) {
        for (c = 0; c < (3); ++c) {
            paw_t[l * 3 + c] = a_paw_target[e * 6 + l * 3 + c];
            swf[l * 3 + c] = a_swing_from[e * 6 + l * 3 + c];
            swt[l * 3 + c] = a_swing_to[e * 6 + l * 3 + c];
}
        paw_y[l] = a_paw_plant_y[e * 2 + l];
        f_t[l] = a_fore_t[e * 2 + l];
        f_st[l] = a_fore_stance[e * 2 + l];
        f_cy[l] = a_fore_cycle[e * 2 + l];
        f_mo[l] = a_fore_mode[e * 2 + l];
        f_en[l] = a_fore_entry[e * 2 + l];
        f_cv[l] = a_fore_conv[e * 2 + l];
        f_dp[l] = a_fore_td_plant[e * 2 + l];
        f_cl[l] = a_fore_clamped[e * 2 + l];
        f_rp[l] = a_fore_replants[e * 2 + l];
        f_td[l] = a_fore_td_count[e * 2 + l];
}
    int h_mo[2];
    double h_t[2];
    double h_from[6];
    double h_to[6];
    double h_py[2];
    double h_ap[2];
    double h_mp[2];
    int h_br[2];
    int h_held[2];
    long long h_lf[2];
    long long h_lt[2];
    int h_fi[2];
    int h_tds[2];
    double h_xo[2];
    for (l = 0; l < (2); ++l) {
        h_mo[l] = a_hind_mode[e * 2 + l];
        h_t[l] = a_hind_t[e * 2 + l];
        h_py[l] = a_hind_plant_y[e * 2 + l];
        h_ap[l] = a_hind_ap[e * 2 + l];
        h_mp[l] = a_hind_mp[e * 2 + l];
        h_br[l] = a_hind_branch[e * 2 + l];
        h_held[l] = a_hind_held[e * 2 + l];
        h_lf[l] = a_hind_last_fire[e * 2 + l];
        h_lt[l] = a_hind_last_td[e * 2 + l];
        h_fi[l] = a_hind_fires[e * 2 + l];
        h_tds[l] = a_hind_tds[e * 2 + l];
        h_xo[l] = a_hind_xoff[e * 2 + l];
        for (c = 0; c < (3); ++c) {
            h_from[l * 3 + c] = a_hind_from[e * 6 + l * 3 + c];
            h_to[l * 3 + c] = a_hind_to[e * 6 + l * 3 + c];
}
}
    h_latched =  a_height_latched[e];
    cmd_v =  a_cmd_vx[e];
    cmd_on =  a_cmd_live[e];
    cmd_first =  a_cmd_first_tick[e];
    cmd_fires =  a_cmd_fires[e];
    int adv[1];
    adv[0] = a_adv_calls[e];
    Tf =  cst[CF_t_cycle] / cst[CF_dt];
    tair =  (double)(csti[CI_tair]);
    walking =  (int)(1);
    if (csti[CI_gait_enabled] == 0 || settle_n > 0 || csti[CI_reflex_level] == 0) {
        walking =  0;
}
    double M[324];
    double gv[18];
    double bv[18];
    double fr[224];
    double frd[224];
    double frdd[224];
    double axw[54];
    double axpiv[54];
    double axdir[54];
    double ptp[24];
    double ptJ[216];
    double ptcop[12];
    double ptbias[12];
    double inv[324];
    double free[18];
    double qa[18];
    double va[18];
    double qb[18];
    double vb[18];
    double qc[18];
    double vc[18];
    double qd[18];
    double vd[18];
    double qe[18];
    double ve[18];
    double we[18];
    double sq[576];
    double sh16[16];
    int sdep[16];
    int scl[16];
    double tr_q[18];
    double tr_v[18];
    double tr_w[18];
    double cd_q[18];
    double cd_v[18];
    double cd_w[18];
    double tau[18];
    double srq[18];
    double srv[18];
    double scales[13];
    round_n =  (int)(0);
    int dsf[1];
    double trial_q[18];
    double trial_v[18];
    double trial_w[18];
    double o_q[18];
    double o_v[18];
    double o_w[18];
    double cur_w[18];
    double eff[18];
    double lta[18];
    rc =  a_rc[e];
    if (rc == 0) {
        for (i = 0; i < (18); ++i) {
            if (isnan(q[i]) || isnan(v[i]) || isinf(q[i]) || isinf(v[i])) {
                rc =  1;
}
}
}
    collapsed =  (int)(0);
    if (rc == 0 && q[4] < (double)(0.20)) {
        collapsed =  1;
}
    if (rc != 0) {
        a_refused[e] = 1;
        a_refused_class[e] = rc;
}
    if (collapsed != 0) {
        a_collapsed[e] = 1;
}
    for (i = 0; i < (18); ++i) {
        a_q[e * 18 + i] = q[i];
        a_v[e * 18 + i] = v[i];
        a_work[e * 18 + i] = w[i];
        a_last_torque[e * 18 + i] = lta[i];
}
    for (d = 0; d < (12); ++d) {
        a_battery[e * 12 + d] = bat[d];
}
    a_battery_post[e] = bat_post;
    a_phi[e * 2] = phi[0];
    a_phi[e * 2 + 1] = phi[1];
    a_touching[e * 2] = tch[0];
    a_touching[e * 2 + 1] = tch[1];
    a_captured[e] = capt;
    a_settle[e] = settle_n;
    a_ik_branch[e * 2] = ikb[0];
    a_ik_branch[e * 2 + 1] = ikb[1];
    for (l = 0; l < (2); ++l) {
        for (c = 0; c < (3); ++c) {
            a_paw_target[e * 6 + l * 3 + c] = paw_t[l * 3 + c];
            a_swing_from[e * 6 + l * 3 + c] = swf[l * 3 + c];
            a_swing_to[e * 6 + l * 3 + c] = swt[l * 3 + c];
            a_hind_from[e * 6 + l * 3 + c] = h_from[l * 3 + c];
            a_hind_to[e * 6 + l * 3 + c] = h_to[l * 3 + c];
}
        a_paw_plant_y[e * 2 + l] = paw_y[l];
        a_fore_t[e * 2 + l] = f_t[l];
        a_fore_stance[e * 2 + l] = f_st[l];
        a_fore_cycle[e * 2 + l] = f_cy[l];
        a_fore_mode[e * 2 + l] = f_mo[l];
        a_fore_entry[e * 2 + l] = f_en[l];
        a_fore_conv[e * 2 + l] = f_cv[l];
        a_fore_td_plant[e * 2 + l] = f_dp[l];
        a_fore_clamped[e * 2 + l] = f_cl[l];
        a_fore_replants[e * 2 + l] = f_rp[l];
        a_fore_td_count[e * 2 + l] = f_td[l];
        a_hind_mode[e * 2 + l] = h_mo[l];
        a_hind_t[e * 2 + l] = h_t[l];
        a_hind_plant_y[e * 2 + l] = h_py[l];
        a_hind_ap[e * 2 + l] = h_ap[l];
        a_hind_mp[e * 2 + l] = h_mp[l];
        a_hind_branch[e * 2 + l] = h_br[l];
        a_hind_held[e * 2 + l] = h_held[l];
        a_hind_last_fire[e * 2 + l] = h_lf[l];
        a_hind_last_td[e * 2 + l] = h_lt[l];
        a_hind_fires[e * 2 + l] = h_fi[l];
        a_hind_tds[e * 2 + l] = h_tds[l];
        a_hind_xoff[e * 2 + l] = h_xo[l];
}
    a_height_latched[e] = h_latched;
    a_cmd_vx[e] = cmd_v;
    a_cmd_live[e] = cmd_on;
    a_cmd_first_tick[e] = cmd_first;
    a_cmd_fires[e] = cmd_fires;
    a_adv_calls[e] = adv[0];
    if (rc == 0 && collapsed == 0) {
        a_ticks[e] = tick + (long long)(1);
}
    bat_sum =  (double)(0.0);
    for (d = 0; d < (12); ++d) {
        bat_sum =  bat_sum + bat[d];
}
    rb[e * 6 + 0] = q[3];
    rb[e * 6 + 1] = q[4];
    rb[e * 6 + 2] = v[3];
    rb[e * 6 + 3] = phi[0];
    rb[e * 6 + 4] = phi[1];
    rb[e * 6 + 5] = bat_sum;
    rbi[e * 6 + 0] = h_fi[0];
    rbi[e * 6 + 1] = h_fi[1];
    rbi[e * 6 + 2] = f_mo[0];
    rbi[e * 6 + 3] = f_mo[1];
    rbi[e * 6 + 4] = tch[0];
    rbi[e * 6 + 5] = tch[1];
}
