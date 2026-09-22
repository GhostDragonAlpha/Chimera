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
static const int OI_pt_body = 184;
static const int OI_drive_coord = 192;
static const int OI_fore_coord = 204;
static const int OI_hind_coord = 208;
static const int OI_hind_drive = 216;
static const int OI_fore_drive = 224;
static const int OI_fore_heel_pt = 228;
static const int OI_hind_heel_pt = 230;
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
    int i;
    double s;
    double omc;
    int j;
    double d;
    double k[16];
    double kk[16];
    for (i = 0; i < (16); ++i) {
        k[i] = (double)(0.0);
}
    k[0 * 4 + 1] = -axis[2];
    k[0 * 4 + 2] = axis[1];
    k[1 * 4 + 0] = axis[2];
    k[1 * 4 + 2] = -axis[0];
    k[2 * 4 + 0] = -axis[1];
    k[2 * 4 + 1] = axis[0];
    mm(k, k, kk);
    s =  sin(ang);
    omc =  ((double)(1.0) - cos(ang));
    for (i = 0; i < (4); ++i) {
        for (j = 0; j < (4); ++j) {
            d =  (double)(0.0);
            if (i == j) {
                d =  (double)(1.0);
}
            out[i * 4 + j] = (d + k[i * 4 + j] * s) + kk[i * 4 + j] * omc;
}
}
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

__device__ inline void vec_point(double* m, double* p, double* out) {
    int i;
    double acc;
    for (i = 0; i < (3); ++i) {
        acc =  m[i * 4 + 3];
        acc =  acc + m[i * 4 + 0] * p[0];
        acc =  acc + m[i * 4 + 1] * p[1];
        acc =  acc + m[i * 4 + 2] * p[2];
        out[i] = acc;
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
    int _zzero0;
    int i;
    int j;
    double t;
    int k;
    int col;
    int _zzero1;
    int _zzero2;
    int ii;
    double an;
    double bn;
    double ar;
    double br;
    double l[324];
    for (_zzero0 = 0; _zzero0 < (324); ++_zzero0) {
        l[_zzero0] = 0.0;
}
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
        for (_zzero1 = 0; _zzero1 < (18); ++_zzero1) {
            y[_zzero1] = 0.0;
}
        double x[18];
        for (_zzero2 = 0; _zzero2 < (18); ++_zzero2) {
            x[_zzero2] = 0.0;
}
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
    int _zzero3;
    int _zzero4;
    int b2;
    int ai2;
    int s2;
    int n_own;
    int b;
    int par;
    int _dtseed;
    int _ddtseed;
    double tvx;
    double tvy;
    double tvz;
    double vvx;
    double vvy;
    double vvz;
    int a0;
    int a1;
    int _mds;
    int _djj;
    int ai;
    int slot;
    double ang;
    double rate;
    double r2;
    int _oi;
    int _os;
    int k;
    int _zzero5;
    int j;
    int idx;
    int npath;
    int cwalk;
    int _pi;
    int c;
    int c2;
    int _zzero6;
    double* Iw;
    int _zzero7;
    int _zzero8;
    double m;
    int nslots;
    int ii;
    int ai_i;
    int si;
    int jj;
    int ai_j;
    int sj;
    double jvd;
    double jwd;
    double Iwj;
    int pb;
    int r;
    double gh;
    double gm;
    double dy;
    double a;
    int _zzero9;
    int _zzero10;
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
    int chain_ax[((OI_chain_ax + 104) - (OI_chain_ax))];
    for (int _si13 = 0; _si13 < ((OI_chain_ax + 104) - (OI_chain_ax)); ++_si13) chain_ax[_si13] = mdi[(OI_chain_ax) + _si13];
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
    double one_ds[16];
    double ta16[16];
    double tb16[16];
    double motion[16];
    double motion_dt[16];
    double motion_ddt[16];
    double pfp[16];
    double t1[16];
    double t2[16];
    double t3[16];
    double t4[16];
    double pfpd[16];
    double pfpedd[16];
    double fp16[16];
    double fc16[16];
    double rt[16];
    double mtmp[16];
    double mtmp2[16];
    double jv[54];
    for (_zzero3 = 0; _zzero3 < (54); ++_zzero3) {
        jv[_zzero3] = 0.0;
}
    double jw[54];
    for (_zzero4 = 0; _zzero4 < (54); ++_zzero4) {
        jw[_zzero4] = 0.0;
}
    int owner_of[18];
    for (i = 0; i < (18); ++i) {
        owner_of[i] = (int)(-1);
}
    for (b2 = (1); b2 < (nbod); ++b2) {
        for (ai2 = (body_axoff[b2]); ai2 < (body_axoff[b2 + 1]); ++ai2) {
            s2 =  ax_slot[ai2];
            if (s2 >= 0) {
                owner_of[s2] = (int)(b2);
}
}
}
    double motion_all[224];
    double mds[288];
    double od16[288];
    double dj[54];
    double fd16[16];
    double fd2[16];
    int own_slots[8];
    int pathb[10];
    double vt3[3];
    double ftT[16];
    n_own =  (int)(0);
    for (b = (1); b < (nbod); ++b) {
        par =  body_parent[b];
        load16(body_fp, b * 16, fp16);
        load16(body_fc, b * 16, fc16);
        for (i = 0; i < (16); ++i) {
            t1[i] = fr[par * 16 + i];
}
        mm(t1, fp16, pfp);
        eye16(motion);
        for (_dtseed = 0; _dtseed < (16); ++_dtseed) {
            motion_dt[_dtseed] = (double)(0.0);
}
        for (_ddtseed = 0; _ddtseed < (16); ++_ddtseed) {
            motion_ddt[_ddtseed] = (double)(0.0);
}
        tvx =  (double)(0.0);
        tvy =  (double)(0.0);
        tvz =  (double)(0.0);
        vvx =  (double)(0.0);
        vvy =  (double)(0.0);
        vvz =  (double)(0.0);
        a0 =  body_axoff[b];
        a1 =  body_axoff[b + 1];
        n_own =  (int)(0);
        for (_mds = 0; _mds < (288); ++_mds) {
            mds[_mds] = (double)(0.0);
}
        for (_djj = 0; _djj < (54); ++_djj) {
            dj[_djj] = (double)(0.0);
}
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
                r2 =  rate * rate;
                for (i = 0; i < (16); ++i) {
                    one_ddt[i] = t3[i] * r2;
}
                for (i = 0; i < (16); ++i) {
                    one_ds[i] = t2[i] * ax_slope[ai];
}
                for (_oi = 0; _oi < (n_own); ++_oi) {
                    _os =  own_slots[_oi];
                    for (i = 0; i < (16); ++i) {
                        ta16[i] = mds[_os * 16 + i];
}
                    mm(ta16, one, tb16);
                    for (i = 0; i < (16); ++i) {
                        mds[_os * 16 + i] = tb16[i];
}
}
                mm(motion, one_ds, tb16);
                for (i = 0; i < (16); ++i) {
                    mds[slot * 16 + i] = tb16[i];
}
                own_slots[n_own] = (int)(slot);
                n_own =  (int)(n_own + 1);
                mm(motion, one, t1);
                mm(motion_dt, one, t2);
                mm(motion, one_dt, t3);
                for (i = 0; i < (16); ++i) {
                    mtmp[i] = motion_dt[i];
}
                mm(mtmp, one_dt, t4);
                mm(motion_ddt, one, rt);
                mm(motion, one_ddt, sk);
                for (i = 0; i < (16); ++i) {
                    motion_ddt[i] = rt[i] + (double)(2.0) * t4[i] + sk[i];
}
                for (i = 0; i < (16); ++i) {
                    motion_dt[i] = t2[i] + t3[i];
}
                for (i = 0; i < (16); ++i) {
                    motion[i] = t1[i];
}
}
            else {
                tvx =  tvx + axis[0] * ang;
                tvy =  tvy + axis[1] * ang;
                tvz =  tvz + axis[2] * ang;
                vvx =  vvx + axis[0] * rate;
                vvy =  vvy + axis[1] * rate;
                vvz =  vvz + axis[2] * rate;
                if (slot >= 0) {
                    dj[slot * 3 + 0] = dj[slot * 3 + 0] + axis[0] * ax_slope[ai];
                    dj[slot * 3 + 1] = dj[slot * 3 + 1] + axis[1] * ax_slope[ai];
                    dj[slot * 3 + 2] = dj[slot * 3 + 2] + axis[2] * ax_slope[ai];
                    own_slots[n_own] = (int)(slot);
                    n_own =  (int)(n_own + 1);
}
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
        for (_oi = 0; _oi < (n_own); ++_oi) {
            _os =  own_slots[_oi];
            mds[_os * 16 + 0 * 4 + 3] = dj[_os * 3 + 0];
            mds[_os * 16 + 1 * 4 + 3] = dj[_os * 3 + 1];
            mds[_os * 16 + 2 * 4 + 3] = dj[_os * 3 + 2];
}
        for (i = 0; i < (16); ++i) {
            motion_all[b * 16 + i] = motion[i];
}
        for (_oi = 0; _oi < (n_own); ++_oi) {
            _os =  own_slots[_oi];
            for (i = 0; i < (16); ++i) {
                ta16[i] = mds[_os * 16 + i];
}
            mm(pfp, ta16, tb16);
            mm(tb16, fc16, ta16);
            for (i = 0; i < (16); ++i) {
                od16[_os * 16 + i] = ta16[i];
}
}
        for (i = 0; i < (16); ++i) {
            t1[i] = frd[par * 16 + i];
}
        mm(t1, fp16, pfpd);
        for (i = 0; i < (16); ++i) {
            t1[i] = frdd[par * 16 + i];
}
        mm(t1, fp16, pfpedd);
        mm(pfp, motion, t1);
        mm(t1, fc16, t2);
        for (i = 0; i < (16); ++i) {
            fr[b * 16 + i] = t2[i];
}
        mm(pfpd, motion, t1);
        mm(pfp, motion_dt, t3);
        for (i = 0; i < (16); ++i) {
            t1[i] = t1[i] + t3[i];
}
        mm(t1, fc16, t2);
        for (i = 0; i < (16); ++i) {
            frd[b * 16 + i] = t2[i];
}
        mm(pfpedd, motion, t1);
        mm(pfpd, motion_dt, t3);
        for (i = 0; i < (16); ++i) {
            t1[i] = t1[i] + (double)(2.0) * t3[i];
}
        mm(pfp, motion_ddt, t3);
        for (i = 0; i < (16); ++i) {
            t1[i] = t1[i] + t3[i];
}
        mm(t1, fc16, t2);
        for (i = 0; i < (16); ++i) {
            frdd[b * 16 + i] = t2[i];
}
        for (i = 0; i < (54); ++i) {
            jv[i] = (double)(0.0);
            jw[i] = (double)(0.0);
}
        double comw[3];
        for (_zzero5 = 0; _zzero5 < (3); ++_zzero5) {
            comw[_zzero5] = 0.0;
}
        double com[3];
        com[0] = body_com[b * 3];
        com[1] = body_com[b * 3 + 1];
        com[2] = body_com[b * 3 + 2];
        for (i = 0; i < (16); ++i) {
            t1[i] = fr[b * 16 + i];
}
        vec_point(t1, com, comw);
        for (i = 0; i < (16); ++i) {
            rt[i] = (double)(0.0);
}
        for (i = 0; i < (3); ++i) {
            for (j = 0; j < (3); ++j) {
                rt[i * 4 + j] = fr[b * 16 + j * 4 + i];
}
}
        for (idx = (chain_off[b]); idx < (chain_off[b + 1]); ++idx) {
            ai =  chain_ax[idx];
            slot =  ax_slot[ai];
            if (slot < 0) {
                continue;
}
            for (i = 0; i < (16); ++i) {
                fd16[i] = od16[slot * 16 + i];
}
            npath =  (int)(0);
            cwalk =  (int)(b);
            while (cwalk != owner_of[slot]) {
                pathb[npath] = cwalk;
                npath =  (int)(npath + 1);
                cwalk =  (int)(body_parent[cwalk]);
}
            for (_pi = 0; _pi < (npath); ++_pi) {
                c =  pathb[npath - 1 - _pi];
                load16(body_fp, c * 16, fp16);
                load16(body_fc, c * 16, fc16);
                for (i = 0; i < (16); ++i) {
                    ta16[i] = fd16[i];
}
                mm(ta16, fp16, tb16);
                for (i = 0; i < (16); ++i) {
                    ta16[i] = tb16[i];
}
                for (i = 0; i < (16); ++i) {
                    tb16[i] = motion_all[c * 16 + i];
}
                mm(ta16, tb16, fd2);
                mm(fd2, fc16, ta16);
                for (i = 0; i < (16); ++i) {
                    fd16[i] = ta16[i];
}
}
            jv[slot * 3] = fd16[0 * 4 + 3];
            jv[slot * 3 + 1] = fd16[1 * 4 + 3];
            jv[slot * 3 + 2] = fd16[2 * 4 + 3];
            for (c2 = 0; c2 < (3); ++c2) {
                jv[slot * 3 + 0] = jv[slot * 3 + 0] + fd16[0 * 4 + c2] * com[c2];
                jv[slot * 3 + 1] = jv[slot * 3 + 1] + fd16[1 * 4 + c2] * com[c2];
                jv[slot * 3 + 2] = jv[slot * 3 + 2] + fd16[2 * 4 + c2] * com[c2];
}
            mm(fd16, rt, ta16);
            jw[slot * 3] = (ta16[2 * 4 + 1] - ta16[1 * 4 + 2]) * ((double)(1.0) / (double)(2.0));
            jw[slot * 3 + 1] = (ta16[0 * 4 + 2] - ta16[2 * 4 + 0]) * ((double)(1.0) / (double)(2.0));
            jw[slot * 3 + 2] = (ta16[1 * 4 + 0] - ta16[0 * 4 + 1]) * ((double)(1.0) / (double)(2.0));
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
        for (i = 0; i < (4); ++i) {
            for (j = 0; j < (4); ++j) {
                ftT[i * 4 + j] = t2[j * 4 + i];
}
}
        mm(t2, ftT, mtmp2);
        for (i = 0; i < (3); ++i) {
            for (j = 0; j < (3); ++j) {
                mtmp[i * 4 + j] = mtmp[i * 4 + j] + mtmp2[i * 4 + j];
}
}
        double alpha[3];
        axial3(mtmp, alpha);
        double acc_com[3];
        for (_zzero6 = 0; _zzero6 < (3); ++_zzero6) {
            acc_com[_zzero6] = 0.0;
}
        double comloc[3];
        comloc[0] = body_com[b * 3];
        comloc[1] = body_com[b * 3 + 1];
        comloc[2] = body_com[b * 3 + 2];
        for (i = 0; i < (16); ++i) {
            t3[i] = frdd[b * 16 + i];
}
        vec_point(t3, comloc, acc_com);
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
            t2[i * 4 + i] = It[i];
}
        mm(t1, t2, mtmp);
        mm(mtmp, rt, t2);
        Iw =  t2;
        double Iwom[3];
        for (_zzero7 = 0; _zzero7 < (3); ++_zzero7) {
            Iwom[_zzero7] = 0.0;
}
        for (i = 0; i < (3); ++i) {
            Iwom[i] = Iw[i * 4 + 0] * omega[0] + Iw[i * 4 + 1] * omega[1] + Iw[i * 4 + 2] * omega[2];
}
        double moment[3];
        for (_zzero8 = 0; _zzero8 < (3); ++_zzero8) {
            moment[_zzero8] = 0.0;
}
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
        vec_point(t1, p, out);
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
        for (_zzero9 = 0; _zzero9 < (3); ++_zzero9) {
            loc[_zzero9] = 0.0;
}
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
        vec_point(t1, loc, solew);
        double t3v[3];
        for (_zzero10 = 0; _zzero10 < (3); ++_zzero10) {
            t3v[_zzero10] = 0.0;
}
        for (i = 0; i < (16); ++i) {
            t4[i] = frdd[pb * 16 + i];
}
        vec_point(t4, loc, t3v);
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
            for (i = 0; i < (16); ++i) {
                fd16[i] = od16[slot * 16 + i];
}
            npath =  (int)(0);
            cwalk =  (int)(pb);
            while (cwalk != owner_of[slot]) {
                pathb[npath] = cwalk;
                npath =  (int)(npath + 1);
                cwalk =  (int)(body_parent[cwalk]);
}
            for (_pi = 0; _pi < (npath); ++_pi) {
                c =  pathb[npath - 1 - _pi];
                load16(body_fp, c * 16, fp16);
                load16(body_fc, c * 16, fc16);
                for (i = 0; i < (16); ++i) {
                    ta16[i] = fd16[i];
}
                mm(ta16, fp16, tb16);
                for (i = 0; i < (16); ++i) {
                    ta16[i] = tb16[i];
}
                for (i = 0; i < (16); ++i) {
                    tb16[i] = motion_all[c * 16 + i];
}
                mm(ta16, tb16, fd2);
                mm(fd2, fc16, ta16);
                for (i = 0; i < (16); ++i) {
                    fd16[i] = ta16[i];
}
}
            ptJ[(r * 3 + 0) * 18 + slot] = fd16[0 * 4 + 3];
            ptJ[(r * 3 + 1) * 18 + slot] = fd16[1 * 4 + 3];
            ptJ[(r * 3 + 2) * 18 + slot] = fd16[2 * 4 + 3];
            for (c2 = 0; c2 < (3); ++c2) {
                ptJ[(r * 3 + 0) * 18 + slot] = ptJ[(r * 3 + 0) * 18 + slot] + fd16[0 * 4 + c2] * loc[c2];
                ptJ[(r * 3 + 1) * 18 + slot] = ptJ[(r * 3 + 1) * 18 + slot] + fd16[1 * 4 + c2] * loc[c2];
                ptJ[(r * 3 + 2) * 18 + slot] = ptJ[(r * 3 + 2) * 18 + slot] + fd16[2 * 4 + c2] * loc[c2];
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
    int _zzero11;
    double t;
    int m;
    int col;
    int _zzero12;
    int _zzero13;
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
    for (_zzero11 = 0; _zzero11 < (100); ++_zzero11) {
        l[_zzero11] = 0.0;
}
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
        for (_zzero12 = 0; _zzero12 < (10); ++_zzero12) {
            y[_zzero12] = 0.0;
}
        double x[10];
        for (_zzero13 = 0; _zzero13 < (10); ++_zzero13) {
            x[_zzero13] = 0.0;
}
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
    int _zzero14;
    int cnt;
    int legal;
    int allok;
    int _zzero15;
    double tol;
    int i;
    int _zzero16;
    int _zzero17;
    int _zzero18;
    int _zzero19;
    int _zzero20;
    int a;
    int b;
    double s;
    int _zzero21;
    int valid;
    double l;
    int _zzero22;
    int _zzero23;
    int _zzero24;
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
                for (_zzero14 = 0; _zzero14 < (10); ++_zzero14) {
                    act[_zzero14] = 0;
}
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
                        for (_zzero15 = 0; _zzero15 < (18); ++_zzero15) {
                            rk[_zzero15] = 0.0;
}
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
                        for (_zzero16 = 0; _zzero16 < (100); ++_zzero16) {
                            gram[_zzero16] = 0.0;
}
                        double rhs[10];
                        for (_zzero17 = 0; _zzero17 < (10); ++_zzero17) {
                            rhs[_zzero17] = 0.0;
}
                        double ra[18];
                        for (_zzero18 = 0; _zzero18 < (18); ++_zzero18) {
                            ra[_zzero18] = 0.0;
}
                        double rb[18];
                        for (_zzero19 = 0; _zzero19 < (18); ++_zzero19) {
                            rb[_zzero19] = 0.0;
}
                        double ia[18];
                        for (_zzero20 = 0; _zzero20 < (18); ++_zzero20) {
                            ia[_zzero20] = 0.0;
}
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
                        for (_zzero21 = 0; _zzero21 < (10); ++_zzero21) {
                            lam[_zzero21] = 0.0;
}
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
                                    for (_zzero22 = 0; _zzero22 < (18); ++_zzero22) {
                                        rk[_zzero22] = 0.0;
}
                                    rows_row(rows, act[k], rk);
                                    for (i = 0; i < (18); ++i) {
                                        p_out[i] = p_out[i] + l * rk[i];
}
}
                                double chg[18];
                                for (_zzero23 = 0; _zzero23 < (18); ++_zzero23) {
                                    chg[_zzero23] = 0.0;
}
                                mat_vec(inv, p_out, chg);
                                double rk[18];
                                for (_zzero24 = 0; _zzero24 < (18); ++_zzero24) {
                                    rk[_zzero24] = 0.0;
}
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
    int _zzero25;
    int _zzero26;
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
    for (_zzero25 = 0; _zzero25 < (18); ++_zzero25) {
        rn_v[_zzero25] = 0.0;
}
    mat_vec(inv, row_n, rn_v);
    double rt_v[18];
    for (_zzero26 = 0; _zzero26 < (18); ++_zzero26) {
        rt_v[_zzero26] = 0.0;
}
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
    int _zzero27;
    int _zzero28;
    int R;
    int n_stops;
    int stop;
    int _zzero29;
    double speed_scale;
    double gate;
    int _zzero30;
    int _zzero31;
    int _zzero32;
    int r;
    double g;
    int _zzero33;
    int _zzero34;
    int _zzero35;
    int _zzero36;
    int _zzero37;
    int _zzero38;
    int _zzero39;
    int _zzero40;
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
    int _zzero41;
    int _zzero42;
    int _zzero43;
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
    double free_acc[18];
    mat_vec(inv, free, free_acc);
    for (i = 0; i < (18); ++i) {
        free[i] = free_acc[i];
}
    double rows[180];
    for (_zzero27 = 0; _zzero27 < (180); ++_zzero27) {
        rows[_zzero27] = 0.0;
}
    double floors[10];
    for (_zzero28 = 0; _zzero28 < (10); ++_zzero28) {
        floors[_zzero28] = 0.0;
}
    R =  (int)(0);
    n_stops =  (int)(0);
    stop =  (int)(0);
    double jn[18];
    for (_zzero29 = 0; _zzero29 < (18); ++_zzero29) {
        jn[_zzero29] = 0.0;
}
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
    for (_zzero30 = 0; _zzero30 < (4); ++_zzero30) {
        touching[_zzero30] = 0;
}
    int mode_k[4];
    for (_zzero31 = 0; _zzero31 < (4); ++_zzero31) {
        mode_k[_zzero31] = 0;
}
    double rn[18];
    for (_zzero32 = 0; _zzero32 < (18); ++_zzero32) {
        rn[_zzero32] = 0.0;
}
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
        for (_zzero33 = 0; _zzero33 < (18); ++_zzero33) {
            jt1[_zzero33] = 0.0;
}
        double jt2[18];
        for (_zzero34 = 0; _zzero34 < (18); ++_zzero34) {
            jt2[_zzero34] = 0.0;
}
        double row_t[18];
        for (_zzero35 = 0; _zzero35 < (18); ++_zzero35) {
            row_t[_zzero35] = 0.0;
}
        double force[18];
        for (_zzero36 = 0; _zzero36 < (18); ++_zzero36) {
            force[_zzero36] = 0.0;
}
        double corr[18];
        for (_zzero37 = 0; _zzero37 < (18); ++_zzero37) {
            corr[_zzero37] = 0.0;
}
        double ln[1];
        for (_zzero38 = 0; _zzero38 < (1); ++_zzero38) {
            ln[_zzero38] = 0.0;
}
        double lt[1];
        for (_zzero39 = 0; _zzero39 < (1); ++_zzero39) {
            lt[_zzero39] = 0.0;
}
        int md[1];
        for (_zzero40 = 0; _zzero40 < (1); ++_zzero40) {
            md[_zzero40] = 0;
}
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
        for (_zzero41 = 0; _zzero41 < (18); ++_zzero41) {
            p[_zzero41] = 0.0;
}
        double mult[10];
        for (_zzero42 = 0; _zzero42 < (10); ++_zzero42) {
            mult[_zzero42] = 0.0;
}
        if (project_rows(free, inv, rows, floors, R, n_stops, p, mult) == 0) {
            return 5;
}
        double corr[18];
        for (_zzero43 = 0; _zzero43 < (18); ++_zzero43) {
            corr[_zzero43] = 0.0;
}
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

__device__ inline long long free_step(double* q0, double* v0, double* w0, double* tau, int* live, double h, double* mdl, double* cst, double* M, double* gv, double* bv, double* fr, double* frd, double* frdd, double* axw, double* axpiv, double* axdir, double* ptp, double* ptJ, double* ptcop, double* ptbias, double* inv, double* free, double* srq, double* srv, double* qa, double* va, double* qb, double* vb, double* qc, double* vc, double* qd, double* vd, double* q1, double* v1, double* w1, int* mdi, int* csti) {
    int _zzero44;
    int _zzero45;
    int _zzero46;
    double pot;
    double speed_scale;
    int d;
    double gate;
    int _zzero47;
    int r;
    int i;
    double g;
    double rc;
    double half;
    int _zzero48;
    int _zzero49;
    int _zzero50;
    int _zzero51;
    int _zzero52;
    int _zzero53;
    double sixth;
    double pt_radius_g[((OF_pt_radius + 8) - (OF_pt_radius))];
    for (int _si0 = 0; _si0 < ((OF_pt_radius + 8) - (OF_pt_radius)); ++_si0) pt_radius_g[_si0] = mdl[(OF_pt_radius) + _si0];
    double rq[18];
    for (_zzero44 = 0; _zzero44 < (18); ++_zzero44) {
        rq[_zzero44] = 0.0;
}
    double rv[18];
    for (_zzero45 = 0; _zzero45 < (18); ++_zzero45) {
        rv[_zzero45] = 0.0;
}
    int plane[4];
    for (_zzero46 = 0; _zzero46 < (4); ++_zzero46) {
        plane[_zzero46] = 0;
}
    pot =  fk_eval(q0,  v0, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
    speed_scale =  (double)(0.0);
    for (d = 0; d < (12); ++d) {
        speed_scale =  speed_scale + fabs(v0[mdi[OI_drive_coord + d]]);
}
    gate =  (double)(1e-6) + (double)(1e-3) * speed_scale;
    double rn[18];
    for (_zzero47 = 0; _zzero47 < (18); ++_zzero47) {
        rn[_zzero47] = 0.0;
}
    for (r = 0; r < (4); ++r) {
        for (i = 0; i < (18); ++i) {
            rn[i] = ptJ[(r * 3 + 1) * 18 + i];
}
        g =  gap_of_k(ptp, pt_radius_g, r * 2, cst[CF_plane_y]);
        if (live[r] != 0 && g <= cst[CF_k_touch] && row_dot(rn, v0) <= gate) {
            plane[r] = 1;
}
}
    rc =  rate(q0, v0, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, qa, va, mdi, csti);
    if (rc != 0) {
        return rc;
}
    half =  h * (double)(0.5);
    for (i = 0; i < (18); ++i) {
        qb[i] = q0[i] + qa[i] * half;
        vb[i] = v0[i] + va[i] * half;
}
    double brq[18];
    for (_zzero48 = 0; _zzero48 < (18); ++_zzero48) {
        brq[_zzero48] = 0.0;
}
    double brv[18];
    for (_zzero49 = 0; _zzero49 < (18); ++_zzero49) {
        brv[_zzero49] = 0.0;
}
    rc =  rate(qb, vb, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, brq, brv, mdi, csti);
    if (rc != 0) {
        return rc;
}
    for (i = 0; i < (18); ++i) {
        qc[i] = q0[i] + brq[i] * half;
        vc[i] = v0[i] + brv[i] * half;
}
    double crq[18];
    for (_zzero50 = 0; _zzero50 < (18); ++_zzero50) {
        crq[_zzero50] = 0.0;
}
    double crv[18];
    for (_zzero51 = 0; _zzero51 < (18); ++_zzero51) {
        crv[_zzero51] = 0.0;
}
    rc =  rate(qc, vc, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, crq, crv, mdi, csti);
    if (rc != 0) {
        return rc;
}
    for (i = 0; i < (18); ++i) {
        qd[i] = q0[i] + crq[i] * h;
        vd[i] = v0[i] + crv[i] * h;
}
    double drq[18];
    for (_zzero52 = 0; _zzero52 < (18); ++_zzero52) {
        drq[_zzero52] = 0.0;
}
    double drv[18];
    for (_zzero53 = 0; _zzero53 < (18); ++_zzero53) {
        drv[_zzero53] = 0.0;
}
    rc =  rate(qd, vd, tau, live, plane, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, drq, drv, mdi, csti);
    if (rc != 0) {
        return rc;
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
    int _zzero54;
    int j;
    double t;
    int m;
    int col;
    int _zzero55;
    int _zzero56;
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
    for (_zzero54 = 0; _zzero54 < (16); ++_zzero54) {
        l[_zzero54] = 0.0;
}
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
        for (_zzero55 = 0; _zzero55 < (4); ++_zzero55) {
            y[_zzero55] = 0.0;
}
        double x[4];
        for (_zzero56 = 0; _zzero56 < (4); ++_zzero56) {
            x[_zzero56] = 0.0;
}
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
    int _zzero57;
    int _zzero58;
    int R;
    int n_stops;
    int _zzero59;
    int d;
    int c;
    int i;
    int _zzero60;
    int r;
    double g;
    int _zzero61;
    int _zzero62;
    int _zzero63;
    int _zzero64;
    int _zzero65;
    int _zzero66;
    int _zzero67;
    int _zzero68;
    int _zzero69;
    double closing;
    double svx;
    double svz;
    double planar;
    int _zzero70;
    int _zzero71;
    int _zzero72;
    int _zzero73;
    int npen;
    int _zzero74;
    int _zzero75;
    int _zzero76;
    int _zzero77;
    int _zzero78;
    int _zzero79;
    int a;
    int b;
    double s;
    int _zzero80;
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
    for (_zzero57 = 0; _zzero57 < (180); ++_zzero57) {
        rows[_zzero57] = 0.0;
}
    double floors[10];
    for (_zzero58 = 0; _zzero58 < (10); ++_zzero58) {
        floors[_zzero58] = 0.0;
}
    R =  (int)(0);
    n_stops =  (int)(0);
    double jn[18];
    for (_zzero59 = 0; _zzero59 < (18); ++_zzero59) {
        jn[_zzero59] = 0.0;
}
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
    for (_zzero60 = 0; _zzero60 < (4); ++_zzero60) {
        touching[_zzero60] = 0;
}
    for (r = 0; r < (4); ++r) {
        g =  gap_of_k(ptp, pt_radius_g, r * 2, cst[CF_plane_y]);
        touching[r] = ((csti[CI_contact] != 0 && g <= cst[CF_k_touch])) ? ((int)(1)) : ((int)(0));
}
    double rn[18];
    for (_zzero61 = 0; _zzero61 < (18); ++_zzero61) {
        rn[_zzero61] = 0.0;
}
    if (cst[CF_mu] > (double)(0.0) && n_stops == 0 && csti[CI_contact] != 0) {
        double jt1[18];
        for (_zzero62 = 0; _zzero62 < (18); ++_zzero62) {
            jt1[_zzero62] = 0.0;
}
        double jt2[18];
        for (_zzero63 = 0; _zzero63 < (18); ++_zzero63) {
            jt2[_zzero63] = 0.0;
}
        double row_t[18];
        for (_zzero64 = 0; _zzero64 < (18); ++_zzero64) {
            row_t[_zzero64] = 0.0;
}
        double force[18];
        for (_zzero65 = 0; _zzero65 < (18); ++_zzero65) {
            force[_zzero65] = 0.0;
}
        double corr[18];
        for (_zzero66 = 0; _zzero66 < (18); ++_zzero66) {
            corr[_zzero66] = 0.0;
}
        double ln[1];
        for (_zzero67 = 0; _zzero67 < (1); ++_zzero67) {
            ln[_zzero67] = 0.0;
}
        double lt[1];
        for (_zzero68 = 0; _zzero68 < (1); ++_zzero68) {
            lt[_zzero68] = 0.0;
}
        int md[1];
        for (_zzero69 = 0; _zzero69 < (1); ++_zzero69) {
            md[_zzero69] = 0;
}
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
        for (_zzero70 = 0; _zzero70 < (18); ++_zzero70) {
            p[_zzero70] = 0.0;
}
        double mult[10];
        for (_zzero71 = 0; _zzero71 < (10); ++_zzero71) {
            mult[_zzero71] = 0.0;
}
        if (project_rows(v, inv, rows, floors, R, n_stops, p, mult) == 0) {
            rc[0] = 5;
            return (double)(0.0);
}
        double corr[18];
        for (_zzero72 = 0; _zzero72 < (18); ++_zzero72) {
            corr[_zzero72] = 0.0;
}
        mat_vec(inv, p, corr);
        for (i = 0; i < (18); ++i) {
            v[i] = v[i] + corr[i];
}
}
    pot =  fk_eval(q,  v, mdl, mdi, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias);
    int pen[4];
    for (_zzero73 = 0; _zzero73 < (4); ++_zzero73) {
        pen[_zzero73] = 0;
}
    npen =  (int)(0);
    double gaps[4];
    for (_zzero74 = 0; _zzero74 < (4); ++_zzero74) {
        gaps[_zzero74] = 0.0;
}
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
        for (_zzero75 = 0; _zzero75 < (16); ++_zzero75) {
            gram[_zzero75] = 0.0;
}
        double rhs[4];
        for (_zzero76 = 0; _zzero76 < (4); ++_zzero76) {
            rhs[_zzero76] = 0.0;
}
        double lam[4];
        for (_zzero77 = 0; _zzero77 < (4); ++_zzero77) {
            lam[_zzero77] = 0.0;
}
        double ra[18];
        for (_zzero78 = 0; _zzero78 < (18); ++_zzero78) {
            ra[_zzero78] = 0.0;
}
        double ia[18];
        for (_zzero79 = 0; _zzero79 < (18); ++_zzero79) {
            ia[_zzero79] = 0.0;
}
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
            for (_zzero80 = 0; _zzero80 < (18); ++_zzero80) {
                corr[_zzero80] = 0.0;
}
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

__device__ inline void advance(double* q0, double* v0, double* w0, double* tau, double h, double* mdl, double* cst, double* M, double* gv, double* bv, double* fr, double* frd, double* frdd, double* axw, double* axpiv, double* axdir, double* ptp, double* ptJ, double* ptcop, double* ptbias, double* inv, double* free, double* srq, double* srv, double* qa, double* va, double* qb, double* vb, double* qc, double* vc, double* qd, double* vd, double* qe, double* ve, double* we, double* sq, double* sh, int* sdep, int* scl, int* adv, int* rc, double* q1, double* v1, double* w1, int* mdi, int* csti) {
    int i;
    int sp;
    double rem;
    int depth;
    int clamps;
    int _zzero81;
    int _zzero82;
    int it;
    int done;
    int _zzero83;
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
    double low;
    double depth_v;
    double bound;
    double left;
    double right;
    int j;
    double mid;
    double rcb;
    double ok2;
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
    for (_zzero81 = 0; _zzero81 < (4); ++_zzero81) {
        live[_zzero81] = 0;
}
    int probe[4];
    for (_zzero82 = 0; _zzero82 < (4); ++_zzero82) {
        probe[_zzero82] = 0;
}
    it =  (int)(0);
    done =  (int)(0);
    int rcv[1];
    for (_zzero83 = 0; _zzero83 < (1); ++_zzero83) {
        rcv[_zzero83] = 0;
}
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
        caught =  impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv, mdi, csti);
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
        rcs =  free_step(q1, v1, w1, tau, live, rem, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, mdi, csti);
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
                rcb =  free_step(q1, v1, w1, tau, live, mid, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, mdi, csti);
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
                    rcb =  free_step(q1, v1, w1, tau, probe, mid, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, mdi, csti);
                    if (rcb != 0) {
                        rc[0] = rcb;
                        return;
}
                    if (gap_of_k(ptp, pt_radius_g, (r - 1) * 2, cst[CF_plane_y]) <= (double)(0.0)) {
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
            caught =  impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv, mdi, csti);
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
            rcc =  free_step(q1, v1, w1, tau, probe, hit, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, mdi, csti);
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
            caught =  impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv, mdi, csti);
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
        rcw =  free_step(q1, v1, w1, tau, live, hit, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, mdi, csti);
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
        caught =  impact(q1, v1, mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, rcv, mdi, csti);
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
    fore_ik_at(mdl, cst, fr, leg, paw, branch, mdi, csti, &d1a, &d1b, &q1r, &q2r, &d1c);
    c1 =  mdi[OI_fore_coord + leg * 2];
    c2 =  mdi[OI_fore_coord + leg * 2 + 1];
    h1 =  fmin(q1r - mdl[OF_lower + c1], mdl[OF_upper + c1] - q1r);
    h2 =  fmin(q2r - mdl[OF_lower + c2], mdl[OF_upper + c2] - q2r);
    return fmin(h1, h2);
}

__device__ inline void fore_follow(double* mdl, double* cst, double* fr, int leg, double* paw_t, double branch, int* mdi, int* csti, double* result) {
    int _zzero84;
    int _zzero85;
    int _zzero86;
    double dirn;
    double dmax;
    double lo;
    double hi;
    int j;
    double mid;
    int _zzero87;
    double edge;
    int _zzero88;
    int _zzero89;
    int _zzero90;
    double p[3];
    for (_zzero84 = 0; _zzero84 < (3); ++_zzero84) {
        p[_zzero84] = 0.0;
}
    p[0] = paw_t[leg * 3];
    p[1] = paw_t[leg * 3 + 1];
    p[2] = paw_t[leg * 3 + 2];
    double px[3];
    for (_zzero85 = 0; _zzero85 < (3); ++_zzero85) {
        px[_zzero85] = 0.0;
}
    double py[3];
    for (_zzero86 = 0; _zzero86 < (3); ++_zzero86) {
        py[_zzero86] = 0.0;
}
    px[0] = p[0] + (double)(1e-3);
    px[1] = p[1];
    px[2] = p[2];
    py[0] = p[0] - (double)(1e-3);
    py[1] = p[1];
    py[2] = p[2];
    dirn =  (double)(1.0);
    if (fore_target_headroom(mdl, cst, fr, leg, px, branch, mdi, csti) < fore_target_headroom(mdl, cst, fr, leg, py, branch, mdi, csti)) {
        dirn =  (double)(-1.0);
}
    dmax =  cst[CF_fore_L1] + cst[CF_fore_rho];
    lo =  (double)(0.0);
    hi =  (double)(2.0) * dmax;
    for (j = 0; j < (42); ++j) {
        mid =  (lo + hi) * (double)(0.5);
        double t[3];
        for (_zzero87 = 0; _zzero87 < (3); ++_zzero87) {
            t[_zzero87] = 0.0;
}
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
    for (_zzero88 = 0; _zzero88 < (3); ++_zzero88) {
        te[_zzero88] = 0.0;
}
    te[0] = p[0] + dirn * edge;
    te[1] = p[1];
    te[2] = p[2];
    if (fore_target_headroom(mdl, cst, fr, leg, te, branch, mdi, csti) < (double)(0.1022)) {
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
        for (_zzero89 = 0; _zzero89 < (3); ++_zzero89) {
            t[_zzero89] = 0.0;
}
        t[0] = p[0] + dirn * mid;
        t[1] = p[1];
        t[2] = p[2];
        if (fore_target_headroom(mdl, cst, fr, leg, t, branch, mdi, csti) < (double)(0.1022)) {
            lo =  mid;
}
        else {
            hi =  mid;
}
}
    double out[3];
    for (_zzero90 = 0; _zzero90 < (3); ++_zzero90) {
        out[_zzero90] = 0.0;
}
    out[0] = p[0] + dirn * ((lo + hi) * (double)(0.5));
    out[1] = p[1];
    out[2] = p[2];
    result[0] = out[0];
    result[1] = out[1];
    result[2] = out[2];
    return;
}

__device__ inline double fore_env(double* mdl, double* cst, double* fr, int leg, double* paw_t, double v3, int* csti) {
    int _zzero91;
    int i;
    int _zzero92;
    int _zzero93;
    double off;
    double hgt;
    double dd;
    double a2;
    double amax;
    double vv;
    double env_s;
    double m16[16];
    for (_zzero91 = 0; _zzero91 < (16); ++_zzero91) {
        m16[_zzero91] = 0.0;
}
    for (i = 0; i < (16); ++i) {
        m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
    double shw[3];
    for (_zzero92 = 0; _zzero92 < (3); ++_zzero92) {
        shw[_zzero92] = 0.0;
}
    double ml[3];
    for (_zzero93 = 0; _zzero93 < (3); ++_zzero93) {
        ml[_zzero93] = 0.0;
}
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
    int _zzero94;
    int _zzero95;
    int _zzero96;
    int _zzero97;
    int i;
    int _zzero98;
    int d;
    double bat_post;
    int _zzero99;
    int _zzero100;
    double capt;
    double settle_n;
    int _zzero101;
    int _zzero102;
    int _zzero103;
    int _zzero104;
    int _zzero105;
    int _zzero106;
    int _zzero107;
    int _zzero108;
    int _zzero109;
    int _zzero110;
    int _zzero111;
    int _zzero112;
    int _zzero113;
    int _zzero114;
    int _zzero115;
    int l;
    int c;
    int _zzero116;
    int _zzero117;
    int _zzero118;
    int _zzero119;
    int _zzero120;
    int _zzero121;
    int _zzero122;
    int _zzero123;
    int _zzero124;
    int _zzero125;
    int _zzero126;
    int _zzero127;
    int _zzero128;
    int _zzero129;
    double h_latched;
    double cmd_v;
    double cmd_on;
    double cmd_first;
    double cmd_fires;
    int _zzero130;
    double Tf;
    double tair;
    int walking;
    int _zzero131;
    int _zzero132;
    int _zzero133;
    int _zzero134;
    int _zzero135;
    int _zzero136;
    int _zzero137;
    int _zzero138;
    int _zzero139;
    int _zzero140;
    int _zzero141;
    int _zzero142;
    int _zzero143;
    int _zzero144;
    int _zzero145;
    int _zzero146;
    int _zzero147;
    int _zzero148;
    int _zzero149;
    int _zzero150;
    int _zzero151;
    int _zzero152;
    int _zzero153;
    int _zzero154;
    int _zzero155;
    int _zzero156;
    int _zzero157;
    int _zzero158;
    int _zzero159;
    int _zzero160;
    int _zzero161;
    int _zzero162;
    int _zzero163;
    int _zzero164;
    int _zzero165;
    int _zzero166;
    int _zzero167;
    int _zzero168;
    int _zzero169;
    int _zzero170;
    int round_n;
    int _zzero171;
    int _zzero172;
    int _zzero173;
    int _zzero174;
    int _zzero175;
    int _zzero176;
    int _zzero177;
    int _zzero178;
    int _zzero179;
    int _zzero180;
    double pot;
    double v_eff;
    int leg;
    int hpt;
    int _zzero181;
    int _zzero182;
    int fb;
    int _zzero183;
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
    int _zzero184;
    int _zzero185;
    int _zzero186;
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
    int _zzero187;
    int _zzero188;
    int _zzero189;
    int _zzero190;
    int _zzero191;
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
    int _zzero192;
    int _zzero193;
    double dsx;
    double dsy;
    int _zzero194;
    int _zzero195;
    int _zzero196;
    int _zzero197;
    int _zzero198;
    int _zzero199;
    int _zzero200;
    double env_t2;
    int _zzero201;
    int _zzero202;
    int _zzero203;
    int cc1;
    int cc2;
    int _zzero204;
    int _zzero205;
    int _zzero206;
    int _zzero207;
    int _zzero208;
    int _zzero209;
    double swing;
    double slot;
    double dslot;
    int _zzero210;
    int _zzero211;
    int _zzero212;
    double offc;
    double envc;
    double smin;
    int found;
    int kk;
    int ww;
    double step;
    double stc;
    int _zzero213;
    int _zzero214;
    int _zzero215;
    int _zzero216;
    int _zzero217;
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
    int _zzero218;
    int _zzero219;
    int _zzero220;
    int _zzero221;
    int _zzero222;
    double fx;
    double fy;
    double fz;
    int c0;
    int c1h;
    int c2h;
    int _zzero223;
    int _zzero224;
    int _zzero225;
    double a2m;
    double dxs;
    double dys;
    double under;
    double xmax;
    int _zzero226;
    int _zzero227;
    int hn;
    int k;
    double mtot;
    double comx;
    double comy;
    double comz;
    int _zzero228;
    int _zzero229;
    int _zzero230;
    int b;
    double mb;
    int j;
    double tx;
    double tz;
    int _zzero231;
    int _zzero232;
    int un;
    int _zzero233;
    int _zzero234;
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
    for (_zzero94 = 0; _zzero94 < (18); ++_zzero94) {
        q[_zzero94] = 0.0;
}
    double v[18];
    for (_zzero95 = 0; _zzero95 < (18); ++_zzero95) {
        v[_zzero95] = 0.0;
}
    double w[18];
    for (_zzero96 = 0; _zzero96 < (18); ++_zzero96) {
        w[_zzero96] = 0.0;
}
    double ltau[18];
    for (_zzero97 = 0; _zzero97 < (18); ++_zzero97) {
        ltau[_zzero97] = 0.0;
}
    for (i = 0; i < (18); ++i) {
        q[i] = a_q[e * 18 + i];
        v[i] = a_v[e * 18 + i];
        w[i] = a_work[e * 18 + i];
        ltau[i] = a_last_torque[e * 18 + i];
}
    double bat[12];
    for (_zzero98 = 0; _zzero98 < (12); ++_zzero98) {
        bat[_zzero98] = 0.0;
}
    for (d = 0; d < (12); ++d) {
        bat[d] = a_battery[e * 12 + d];
}
    bat_post =  a_battery_post[e];
    double phi[2];
    for (_zzero99 = 0; _zzero99 < (2); ++_zzero99) {
        phi[_zzero99] = 0.0;
}
    phi[0] = a_phi[e * 2];
    phi[1] = a_phi[e * 2 + 1];
    int tch[2];
    for (_zzero100 = 0; _zzero100 < (2); ++_zzero100) {
        tch[_zzero100] = 0;
}
    tch[0] = a_touching[e * 2];
    tch[1] = a_touching[e * 2 + 1];
    capt =  a_captured[e];
    settle_n =  a_settle[e];
    int ikb[2];
    for (_zzero101 = 0; _zzero101 < (2); ++_zzero101) {
        ikb[_zzero101] = 0;
}
    ikb[0] = a_ik_branch[e * 2];
    ikb[1] = a_ik_branch[e * 2 + 1];
    double paw_t[6];
    for (_zzero102 = 0; _zzero102 < (6); ++_zzero102) {
        paw_t[_zzero102] = 0.0;
}
    double paw_y[2];
    for (_zzero103 = 0; _zzero103 < (2); ++_zzero103) {
        paw_y[_zzero103] = 0.0;
}
    double swf[6];
    for (_zzero104 = 0; _zzero104 < (6); ++_zzero104) {
        swf[_zzero104] = 0.0;
}
    double swt[6];
    for (_zzero105 = 0; _zzero105 < (6); ++_zzero105) {
        swt[_zzero105] = 0.0;
}
    double f_t[2];
    for (_zzero106 = 0; _zzero106 < (2); ++_zzero106) {
        f_t[_zzero106] = 0.0;
}
    double f_st[2];
    for (_zzero107 = 0; _zzero107 < (2); ++_zzero107) {
        f_st[_zzero107] = 0.0;
}
    double f_cy[2];
    for (_zzero108 = 0; _zzero108 < (2); ++_zzero108) {
        f_cy[_zzero108] = 0.0;
}
    int f_mo[2];
    for (_zzero109 = 0; _zzero109 < (2); ++_zzero109) {
        f_mo[_zzero109] = 0;
}
    int f_en[2];
    for (_zzero110 = 0; _zzero110 < (2); ++_zzero110) {
        f_en[_zzero110] = 0;
}
    int f_cv[2];
    for (_zzero111 = 0; _zzero111 < (2); ++_zzero111) {
        f_cv[_zzero111] = 0;
}
    int f_dp[2];
    for (_zzero112 = 0; _zzero112 < (2); ++_zzero112) {
        f_dp[_zzero112] = 0;
}
    int f_cl[2];
    for (_zzero113 = 0; _zzero113 < (2); ++_zzero113) {
        f_cl[_zzero113] = 0;
}
    int f_rp[2];
    for (_zzero114 = 0; _zzero114 < (2); ++_zzero114) {
        f_rp[_zzero114] = 0;
}
    int f_td[2];
    for (_zzero115 = 0; _zzero115 < (2); ++_zzero115) {
        f_td[_zzero115] = 0;
}
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
    for (_zzero116 = 0; _zzero116 < (2); ++_zzero116) {
        h_mo[_zzero116] = 0;
}
    double h_t[2];
    for (_zzero117 = 0; _zzero117 < (2); ++_zzero117) {
        h_t[_zzero117] = 0.0;
}
    double h_from[6];
    for (_zzero118 = 0; _zzero118 < (6); ++_zzero118) {
        h_from[_zzero118] = 0.0;
}
    double h_to[6];
    for (_zzero119 = 0; _zzero119 < (6); ++_zzero119) {
        h_to[_zzero119] = 0.0;
}
    double h_py[2];
    for (_zzero120 = 0; _zzero120 < (2); ++_zzero120) {
        h_py[_zzero120] = 0.0;
}
    double h_ap[2];
    for (_zzero121 = 0; _zzero121 < (2); ++_zzero121) {
        h_ap[_zzero121] = 0.0;
}
    double h_mp[2];
    for (_zzero122 = 0; _zzero122 < (2); ++_zzero122) {
        h_mp[_zzero122] = 0.0;
}
    int h_br[2];
    for (_zzero123 = 0; _zzero123 < (2); ++_zzero123) {
        h_br[_zzero123] = 0;
}
    int h_held[2];
    for (_zzero124 = 0; _zzero124 < (2); ++_zzero124) {
        h_held[_zzero124] = 0;
}
    long long h_lf[2];
    for (_zzero125 = 0; _zzero125 < (2); ++_zzero125) {
        h_lf[_zzero125] = 0;
}
    long long h_lt[2];
    for (_zzero126 = 0; _zzero126 < (2); ++_zzero126) {
        h_lt[_zzero126] = 0;
}
    int h_fi[2];
    for (_zzero127 = 0; _zzero127 < (2); ++_zzero127) {
        h_fi[_zzero127] = 0;
}
    int h_tds[2];
    for (_zzero128 = 0; _zzero128 < (2); ++_zzero128) {
        h_tds[_zzero128] = 0;
}
    double h_xo[2];
    for (_zzero129 = 0; _zzero129 < (2); ++_zzero129) {
        h_xo[_zzero129] = 0.0;
}
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
    for (_zzero130 = 0; _zzero130 < (1); ++_zzero130) {
        adv[_zzero130] = 0;
}
    adv[0] = a_adv_calls[e];
    Tf =  cst[CF_t_cycle] / cst[CF_dt];
    tair =  (double)(csti[CI_tair]);
    walking =  (int)(1);
    if (csti[CI_gait_enabled] == 0 || settle_n > 0 || csti[CI_reflex_level] == 0) {
        walking =  0;
}
    double M[324];
    for (_zzero131 = 0; _zzero131 < (324); ++_zzero131) {
        M[_zzero131] = 0.0;
}
    double gv[18];
    for (_zzero132 = 0; _zzero132 < (18); ++_zzero132) {
        gv[_zzero132] = 0.0;
}
    double bv[18];
    for (_zzero133 = 0; _zzero133 < (18); ++_zzero133) {
        bv[_zzero133] = 0.0;
}
    double fr[224];
    for (_zzero134 = 0; _zzero134 < (224); ++_zzero134) {
        fr[_zzero134] = 0.0;
}
    double frd[224];
    for (_zzero135 = 0; _zzero135 < (224); ++_zzero135) {
        frd[_zzero135] = 0.0;
}
    double frdd[224];
    for (_zzero136 = 0; _zzero136 < (224); ++_zzero136) {
        frdd[_zzero136] = 0.0;
}
    double axw[54];
    for (_zzero137 = 0; _zzero137 < (54); ++_zzero137) {
        axw[_zzero137] = 0.0;
}
    double axpiv[54];
    for (_zzero138 = 0; _zzero138 < (54); ++_zzero138) {
        axpiv[_zzero138] = 0.0;
}
    double axdir[54];
    for (_zzero139 = 0; _zzero139 < (54); ++_zzero139) {
        axdir[_zzero139] = 0.0;
}
    double ptp[24];
    for (_zzero140 = 0; _zzero140 < (24); ++_zzero140) {
        ptp[_zzero140] = 0.0;
}
    double ptJ[216];
    for (_zzero141 = 0; _zzero141 < (216); ++_zzero141) {
        ptJ[_zzero141] = 0.0;
}
    double ptcop[12];
    for (_zzero142 = 0; _zzero142 < (12); ++_zzero142) {
        ptcop[_zzero142] = 0.0;
}
    double ptbias[12];
    for (_zzero143 = 0; _zzero143 < (12); ++_zzero143) {
        ptbias[_zzero143] = 0.0;
}
    double inv[324];
    for (_zzero144 = 0; _zzero144 < (324); ++_zzero144) {
        inv[_zzero144] = 0.0;
}
    double free[18];
    for (_zzero145 = 0; _zzero145 < (18); ++_zzero145) {
        free[_zzero145] = 0.0;
}
    double qa[18];
    for (_zzero146 = 0; _zzero146 < (18); ++_zzero146) {
        qa[_zzero146] = 0.0;
}
    double va[18];
    for (_zzero147 = 0; _zzero147 < (18); ++_zzero147) {
        va[_zzero147] = 0.0;
}
    double qb[18];
    for (_zzero148 = 0; _zzero148 < (18); ++_zzero148) {
        qb[_zzero148] = 0.0;
}
    double vb[18];
    for (_zzero149 = 0; _zzero149 < (18); ++_zzero149) {
        vb[_zzero149] = 0.0;
}
    double qc[18];
    for (_zzero150 = 0; _zzero150 < (18); ++_zzero150) {
        qc[_zzero150] = 0.0;
}
    double vc[18];
    for (_zzero151 = 0; _zzero151 < (18); ++_zzero151) {
        vc[_zzero151] = 0.0;
}
    double qd[18];
    for (_zzero152 = 0; _zzero152 < (18); ++_zzero152) {
        qd[_zzero152] = 0.0;
}
    double vd[18];
    for (_zzero153 = 0; _zzero153 < (18); ++_zzero153) {
        vd[_zzero153] = 0.0;
}
    double qe[18];
    for (_zzero154 = 0; _zzero154 < (18); ++_zzero154) {
        qe[_zzero154] = 0.0;
}
    double ve[18];
    for (_zzero155 = 0; _zzero155 < (18); ++_zzero155) {
        ve[_zzero155] = 0.0;
}
    double we[18];
    for (_zzero156 = 0; _zzero156 < (18); ++_zzero156) {
        we[_zzero156] = 0.0;
}
    double sq[576];
    for (_zzero157 = 0; _zzero157 < (576); ++_zzero157) {
        sq[_zzero157] = 0.0;
}
    double sh16[16];
    for (_zzero158 = 0; _zzero158 < (16); ++_zzero158) {
        sh16[_zzero158] = 0.0;
}
    int sdep[16];
    for (_zzero159 = 0; _zzero159 < (16); ++_zzero159) {
        sdep[_zzero159] = 0;
}
    int scl[16];
    for (_zzero160 = 0; _zzero160 < (16); ++_zzero160) {
        scl[_zzero160] = 0;
}
    double tr_q[18];
    for (_zzero161 = 0; _zzero161 < (18); ++_zzero161) {
        tr_q[_zzero161] = 0.0;
}
    double tr_v[18];
    for (_zzero162 = 0; _zzero162 < (18); ++_zzero162) {
        tr_v[_zzero162] = 0.0;
}
    double tr_w[18];
    for (_zzero163 = 0; _zzero163 < (18); ++_zzero163) {
        tr_w[_zzero163] = 0.0;
}
    double cd_q[18];
    for (_zzero164 = 0; _zzero164 < (18); ++_zzero164) {
        cd_q[_zzero164] = 0.0;
}
    double cd_v[18];
    for (_zzero165 = 0; _zzero165 < (18); ++_zzero165) {
        cd_v[_zzero165] = 0.0;
}
    double cd_w[18];
    for (_zzero166 = 0; _zzero166 < (18); ++_zzero166) {
        cd_w[_zzero166] = 0.0;
}
    double tau[18];
    for (_zzero167 = 0; _zzero167 < (18); ++_zzero167) {
        tau[_zzero167] = 0.0;
}
    double srq[18];
    for (_zzero168 = 0; _zzero168 < (18); ++_zzero168) {
        srq[_zzero168] = 0.0;
}
    double srv[18];
    for (_zzero169 = 0; _zzero169 < (18); ++_zzero169) {
        srv[_zzero169] = 0.0;
}
    double scales[13];
    for (_zzero170 = 0; _zzero170 < (13); ++_zzero170) {
        scales[_zzero170] = 0.0;
}
    round_n =  (int)(0);
    int dsf[1];
    for (_zzero171 = 0; _zzero171 < (1); ++_zzero171) {
        dsf[_zzero171] = 0;
}
    double trial_q[18];
    for (_zzero172 = 0; _zzero172 < (18); ++_zzero172) {
        trial_q[_zzero172] = 0.0;
}
    double trial_v[18];
    for (_zzero173 = 0; _zzero173 < (18); ++_zzero173) {
        trial_v[_zzero173] = 0.0;
}
    double trial_w[18];
    for (_zzero174 = 0; _zzero174 < (18); ++_zzero174) {
        trial_w[_zzero174] = 0.0;
}
    double o_q[18];
    for (_zzero175 = 0; _zzero175 < (18); ++_zzero175) {
        o_q[_zzero175] = 0.0;
}
    double o_v[18];
    for (_zzero176 = 0; _zzero176 < (18); ++_zzero176) {
        o_v[_zzero176] = 0.0;
}
    double o_w[18];
    for (_zzero177 = 0; _zzero177 < (18); ++_zzero177) {
        o_w[_zzero177] = 0.0;
}
    double cur_w[18];
    for (_zzero178 = 0; _zzero178 < (18); ++_zzero178) {
        cur_w[_zzero178] = 0.0;
}
    double eff[18];
    for (_zzero179 = 0; _zzero179 < (18); ++_zzero179) {
        eff[_zzero179] = 0.0;
}
    double lta[18];
    for (_zzero180 = 0; _zzero180 < (18); ++_zzero180) {
        lta[_zzero180] = 0.0;
}
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
            for (_zzero181 = 0; _zzero181 < (3); ++_zzero181) {
                prl[_zzero181] = 0.0;
}
            for (c = 0; c < (3); ++c) {
                prl[c] = (mdl[OF_pt_local + hpt * 3 + c] + mdl[OF_pt_local + (hpt + 1) * 3 + c]) * (double)(0.5);
}
            double T16[16];
            for (_zzero182 = 0; _zzero182 < (16); ++_zzero182) {
                T16[_zzero182] = 0.0;
}
            fb =  mdi[OI_pt_body + hpt];
            for (i = 0; i < (16); ++i) {
                T16[i] = fr[fb * 16 + i];
}
            double pw[3];
            for (_zzero183 = 0; _zzero183 < (3); ++_zzero183) {
                pw[_zzero183] = 0.0;
}
            apply_point(T16, prl, pw);
            for (c = 0; c < (3); ++c) {
                paw_t[leg * 3 + c] = pw[c];
}
            c1 =  mdi[OI_fore_coord + leg * 2];
            c2 =  mdi[OI_fore_coord + leg * 2 + 1];
            fore_ik_at(mdl, cst, fr, leg, pw, 1, mdi, csti, &qa1, &qa2, &qa1r, &qa2r, &sata);
            fore_ik_at(mdl, cst, fr, leg, pw, -1, mdi, csti, &qb1, &qb2, &qb1r, &qb2r, &satb);
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
            for (_zzero184 = 0; _zzero184 < (3); ++_zzero184) {
                shw[_zzero184] = 0.0;
}
            double ml[3];
            for (_zzero185 = 0; _zzero185 < (3); ++_zzero185) {
                ml[_zzero185] = 0.0;
}
            double m16[16];
            for (_zzero186 = 0; _zzero186 < (16); ++_zzero186) {
                m16[_zzero186] = 0.0;
}
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
                            for (_zzero187 = 0; _zzero187 < (16); ++_zzero187) {
                                m16[_zzero187] = 0.0;
}
                            for (i = 0; i < (16); ++i) {
                                m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
                            double sha[3];
                            for (_zzero188 = 0; _zzero188 < (3); ++_zzero188) {
                                sha[_zzero188] = 0.0;
}
                            double ml0[3];
                            for (_zzero189 = 0; _zzero189 < (3); ++_zzero189) {
                                ml0[_zzero189] = 0.0;
}
                            ml0[0] = mdl[OF_fore_mount_local + leg * 3];
                            ml0[1] = mdl[OF_fore_mount_local + leg * 3 + 1];
                            ml0[2] = mdl[OF_fore_mount_local + leg * 3 + 2];
                            apply_point(m16, ml0, sha);
                            double sho[3];
                            for (_zzero190 = 0; _zzero190 < (3); ++_zzero190) {
                                sho[_zzero190] = 0.0;
}
                            double ml1[3];
                            for (_zzero191 = 0; _zzero191 < (3); ++_zzero191) {
                                ml1[_zzero191] = 0.0;
}
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
                fore_ik_at(mdl, cst, fr, leg, plt, ikb[leg], mdi, csti, &dq1, &dq2, &tq1r, &tq2r, &dsat);
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
                for (_zzero192 = 0; _zzero192 < (3); ++_zzero192) {
                    seat[_zzero192] = 0.0;
}
                if (gated == 0 && due != 0 && (thin_seat == 0 || wall_bound == 0)) {
                    act =  1;
}
                else if (gated == 0 && due != 0 && thin_seat != 0 && wall_bound != 0) {
                    double seat[3];
                    for (_zzero193 = 0; _zzero193 < (3); ++_zzero193) {
                        seat[_zzero193] = 0.0;
}
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
                        for (_zzero194 = 0; _zzero194 < (3); ++_zzero194) {
                            seat[_zzero194] = 0.0;
}
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
                    for (_zzero195 = 0; _zzero195 < (3); ++_zzero195) {
                        prl[_zzero195] = 0.0;
}
                    for (c = 0; c < (3); ++c) {
                        prl[c] = (mdl[OF_pt_local + hpt * 3 + c] + mdl[OF_pt_local + (hpt + 1) * 3 + c]) * (double)(0.5);
}
                    double T16[16];
                    for (_zzero196 = 0; _zzero196 < (16); ++_zzero196) {
                        T16[_zzero196] = 0.0;
}
                    fb =  mdi[OI_pt_body + hpt];
                    for (i = 0; i < (16); ++i) {
                        T16[i] = fr[fb * 16 + i];
}
                    double pw[3];
                    for (_zzero197 = 0; _zzero197 < (3); ++_zzero197) {
                        pw[_zzero197] = 0.0;
}
                    apply_point(T16, prl, pw);
                    double m16[16];
                    for (_zzero198 = 0; _zzero198 < (16); ++_zzero198) {
                        m16[_zzero198] = 0.0;
}
                    for (i = 0; i < (16); ++i) {
                        m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
                    double shw[3];
                    for (_zzero199 = 0; _zzero199 < (3); ++_zzero199) {
                        shw[_zzero199] = 0.0;
}
                    double ml[3];
                    for (_zzero200 = 0; _zzero200 < (3); ++_zzero200) {
                        ml[_zzero200] = 0.0;
}
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
                    for (_zzero201 = 0; _zzero201 < (3); ++_zzero201) {
                        prl[_zzero201] = 0.0;
}
                    for (c = 0; c < (3); ++c) {
                        prl[c] = (mdl[OF_pt_local + hpt * 3 + c] + mdl[OF_pt_local + (hpt + 1) * 3 + c]) * (double)(0.5);
}
                    double T16[16];
                    for (_zzero202 = 0; _zzero202 < (16); ++_zzero202) {
                        T16[_zzero202] = 0.0;
}
                    fb =  mdi[OI_pt_body + hpt];
                    for (i = 0; i < (16); ++i) {
                        T16[i] = fr[fb * 16 + i];
}
                    double pw[3];
                    for (_zzero203 = 0; _zzero203 < (3); ++_zzero203) {
                        pw[_zzero203] = 0.0;
}
                    apply_point(T16, prl, pw);
                    for (c = 0; c < (3); ++c) {
                        paw_t[leg * 3 + c] = pw[c];
}
                    cc1 =  mdi[OI_fore_coord + leg * 2];
                    cc2 =  mdi[OI_fore_coord + leg * 2 + 1];
                    fore_ik_at(mdl, cst, fr, leg, pw, 1, mdi, csti, &qa1, &qa2, &qa1r, &qa2r, &sata);
                    fore_ik_at(mdl, cst, fr, leg, pw, -1, mdi, csti, &qb1, &qb2, &qb1r, &qb2r, &satb);
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
                for (_zzero204 = 0; _zzero204 < (3); ++_zzero204) {
                    prl[_zzero204] = 0.0;
}
                for (c = 0; c < (3); ++c) {
                    prl[c] = (mdl[OF_pt_local + hpt * 3 + c] + mdl[OF_pt_local + (hpt + 1) * 3 + c]) * (double)(0.5);
}
                double T16[16];
                for (_zzero205 = 0; _zzero205 < (16); ++_zzero205) {
                    T16[_zzero205] = 0.0;
}
                fb =  mdi[OI_pt_body + hpt];
                for (i = 0; i < (16); ++i) {
                    T16[i] = fr[fb * 16 + i];
}
                double pw[3];
                for (_zzero206 = 0; _zzero206 < (3); ++_zzero206) {
                    pw[_zzero206] = 0.0;
}
                apply_point(T16, prl, pw);
                for (c = 0; c < (3); ++c) {
                    paw_t[leg * 3 + c] = pw[c];
}
                cc1 =  mdi[OI_fore_coord + leg * 2];
                cc2 =  mdi[OI_fore_coord + leg * 2 + 1];
                fore_ik_at(mdl, cst, fr, leg, pw, 1, mdi, csti, &qa1, &qa2, &qa1r, &qa2r, &sata);
                fore_ik_at(mdl, cst, fr, leg, pw, -1, mdi, csti, &qb1, &qb2, &qb1r, &qb2r, &satb);
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
                    for (_zzero207 = 0; _zzero207 < (16); ++_zzero207) {
                        m16[_zzero207] = 0.0;
}
                    for (i = 0; i < (16); ++i) {
                        m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
                    double shw[3];
                    for (_zzero208 = 0; _zzero208 < (3); ++_zzero208) {
                        shw[_zzero208] = 0.0;
}
                    double ml[3];
                    for (_zzero209 = 0; _zzero209 < (3); ++_zzero209) {
                        ml[_zzero209] = 0.0;
}
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
                        for (_zzero210 = 0; _zzero210 < (16); ++_zzero210) {
                            m16[_zzero210] = 0.0;
}
                        for (i = 0; i < (16); ++i) {
                            m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
                        double shw[3];
                        for (_zzero211 = 0; _zzero211 < (3); ++_zzero211) {
                            shw[_zzero211] = 0.0;
}
                        double ml[3];
                        for (_zzero212 = 0; _zzero212 < (3); ++_zzero212) {
                            ml[_zzero212] = 0.0;
}
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
        for (_zzero213 = 0; _zzero213 < (16); ++_zzero213) {
            m16[_zzero213] = 0.0;
}
        for (i = 0; i < (16); ++i) {
            m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
        double shl[3];
        for (_zzero214 = 0; _zzero214 < (3); ++_zzero214) {
            shl[_zzero214] = 0.0;
}
        double ml0[3];
        for (_zzero215 = 0; _zzero215 < (3); ++_zzero215) {
            ml0[_zzero215] = 0.0;
}
        ml0[0] = mdl[OF_fore_mount_local + 0];
        ml0[1] = mdl[OF_fore_mount_local + 1];
        ml0[2] = mdl[OF_fore_mount_local + 2];
        apply_point(m16, ml0, shl);
        double shr[3];
        for (_zzero216 = 0; _zzero216 < (3); ++_zzero216) {
            shr[_zzero216] = 0.0;
}
        double ml1[3];
        for (_zzero217 = 0; _zzero217 < (3); ++_zzero217) {
            ml1[_zzero217] = 0.0;
}
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
            for (_zzero218 = 0; _zzero218 < (3); ++_zzero218) {
                p1[_zzero218] = 0.0;
}
            double p2[3];
            for (_zzero219 = 0; _zzero219 < (3); ++_zzero219) {
                p2[_zzero219] = 0.0;
}
            for (c = 0; c < (3); ++c) {
                p1[c] = mdl[OF_pt_local + hpt * 3 + c];
                p2[c] = mdl[OF_pt_local + (hpt + 1) * 3 + c];
}
            double T16[16];
            for (_zzero220 = 0; _zzero220 < (16); ++_zzero220) {
                T16[_zzero220] = 0.0;
}
            fb =  mdi[OI_pt_body + hpt];
            for (i = 0; i < (16); ++i) {
                T16[i] = fr[fb * 16 + i];
}
            double w1p[3];
            for (_zzero221 = 0; _zzero221 < (3); ++_zzero221) {
                w1p[_zzero221] = 0.0;
}
            apply_point(T16, p1, w1p);
            double w2p[3];
            for (_zzero222 = 0; _zzero222 < (3); ++_zzero222) {
                w2p[_zzero222] = 0.0;
}
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
            for (_zzero223 = 0; _zzero223 < (16); ++_zzero223) {
                m16[_zzero223] = 0.0;
}
            for (i = 0; i < (16); ++i) {
                m16[i] = fr[csti[CI_pelvis_row] * 16 + i];
}
            double hipw[3];
            for (_zzero224 = 0; _zzero224 < (3); ++_zzero224) {
                hipw[_zzero224] = 0.0;
}
            double mlh[3];
            for (_zzero225 = 0; _zzero225 < (3); ++_zzero225) {
                mlh[_zzero225] = 0.0;
}
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
        for (_zzero226 = 0; _zzero226 < (8); ++_zzero226) {
            hx[_zzero226] = 0.0;
}
        double hz[8];
        for (_zzero227 = 0; _zzero227 < (8); ++_zzero227) {
            hz[_zzero227] = 0.0;
}
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
        for (_zzero228 = 0; _zzero228 < (3); ++_zzero228) {
            cw[_zzero228] = 0.0;
}
        double cb[3];
        for (_zzero229 = 0; _zzero229 < (3); ++_zzero229) {
            cb[_zzero229] = 0.0;
}
        double T16b[16];
        for (_zzero230 = 0; _zzero230 < (16); ++_zzero230) {
            T16b[_zzero230] = 0.0;
}
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
            for (_zzero231 = 0; _zzero231 < (8); ++_zzero231) {
                ux[_zzero231] = 0.0;
}
            double uz[8];
            for (_zzero232 = 0; _zzero232 < (8); ++_zzero232) {
                uz[_zzero232] = 0.0;
}
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
                for (_zzero233 = 0; _zzero233 < (16); ++_zzero233) {
                    chx[_zzero233] = 0.0;
}
                double chz[16];
                for (_zzero234 = 0; _zzero234 < (16); ++_zzero234) {
                    chz[_zzero234] = 0.0;
}
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
    int _zzero235;
    int _zzero236;
    int _zzero237;
    int _zzero238;
    int i;
    int _zzero239;
    int d;
    double bat_post;
    int _zzero240;
    int _zzero241;
    double capt;
    double settle_n;
    int _zzero242;
    int _zzero243;
    int _zzero244;
    int _zzero245;
    int _zzero246;
    int _zzero247;
    int _zzero248;
    int _zzero249;
    int _zzero250;
    int _zzero251;
    int _zzero252;
    int _zzero253;
    int _zzero254;
    int _zzero255;
    int _zzero256;
    int l;
    int c;
    int _zzero257;
    int _zzero258;
    int _zzero259;
    int _zzero260;
    int _zzero261;
    int _zzero262;
    int _zzero263;
    int _zzero264;
    int _zzero265;
    int _zzero266;
    int _zzero267;
    int _zzero268;
    int _zzero269;
    int _zzero270;
    double h_latched;
    double cmd_v;
    double cmd_on;
    double cmd_first;
    double cmd_fires;
    int _zzero271;
    double Tf;
    double tair;
    int walking;
    int _zzero272;
    int _zzero273;
    int _zzero274;
    int _zzero275;
    int _zzero276;
    int _zzero277;
    int _zzero278;
    int _zzero279;
    int _zzero280;
    int _zzero281;
    int _zzero282;
    int _zzero283;
    int _zzero284;
    int _zzero285;
    int _zzero286;
    int _zzero287;
    int _zzero288;
    int _zzero289;
    int _zzero290;
    int _zzero291;
    int _zzero292;
    int _zzero293;
    int _zzero294;
    int _zzero295;
    int _zzero296;
    int _zzero297;
    int _zzero298;
    int _zzero299;
    int _zzero300;
    int _zzero301;
    int _zzero302;
    int _zzero303;
    int _zzero304;
    int _zzero305;
    int _zzero306;
    int _zzero307;
    int _zzero308;
    int _zzero309;
    int _zzero310;
    int _zzero311;
    int round_n;
    int _zzero312;
    int _zzero313;
    int _zzero314;
    int _zzero315;
    int _zzero316;
    int _zzero317;
    int _zzero318;
    int _zzero319;
    int _zzero320;
    int _zzero321;
    int sub;
    double pot;
    double target;
    int hl;
    int ji;
    double sg;
    double carch;
    int _zzero322;
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
    int _zzero323;
    int rcs;
    int enabled;
    double store;
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
    for (_zzero235 = 0; _zzero235 < (18); ++_zzero235) {
        q[_zzero235] = 0.0;
}
    double v[18];
    for (_zzero236 = 0; _zzero236 < (18); ++_zzero236) {
        v[_zzero236] = 0.0;
}
    double w[18];
    for (_zzero237 = 0; _zzero237 < (18); ++_zzero237) {
        w[_zzero237] = 0.0;
}
    double ltau[18];
    for (_zzero238 = 0; _zzero238 < (18); ++_zzero238) {
        ltau[_zzero238] = 0.0;
}
    for (i = 0; i < (18); ++i) {
        q[i] = a_q[e * 18 + i];
        v[i] = a_v[e * 18 + i];
        w[i] = a_work[e * 18 + i];
        ltau[i] = a_last_torque[e * 18 + i];
}
    double bat[12];
    for (_zzero239 = 0; _zzero239 < (12); ++_zzero239) {
        bat[_zzero239] = 0.0;
}
    for (d = 0; d < (12); ++d) {
        bat[d] = a_battery[e * 12 + d];
}
    bat_post =  a_battery_post[e];
    double phi[2];
    for (_zzero240 = 0; _zzero240 < (2); ++_zzero240) {
        phi[_zzero240] = 0.0;
}
    phi[0] = a_phi[e * 2];
    phi[1] = a_phi[e * 2 + 1];
    int tch[2];
    for (_zzero241 = 0; _zzero241 < (2); ++_zzero241) {
        tch[_zzero241] = 0;
}
    tch[0] = a_touching[e * 2];
    tch[1] = a_touching[e * 2 + 1];
    capt =  a_captured[e];
    settle_n =  a_settle[e];
    int ikb[2];
    for (_zzero242 = 0; _zzero242 < (2); ++_zzero242) {
        ikb[_zzero242] = 0;
}
    ikb[0] = a_ik_branch[e * 2];
    ikb[1] = a_ik_branch[e * 2 + 1];
    double paw_t[6];
    for (_zzero243 = 0; _zzero243 < (6); ++_zzero243) {
        paw_t[_zzero243] = 0.0;
}
    double paw_y[2];
    for (_zzero244 = 0; _zzero244 < (2); ++_zzero244) {
        paw_y[_zzero244] = 0.0;
}
    double swf[6];
    for (_zzero245 = 0; _zzero245 < (6); ++_zzero245) {
        swf[_zzero245] = 0.0;
}
    double swt[6];
    for (_zzero246 = 0; _zzero246 < (6); ++_zzero246) {
        swt[_zzero246] = 0.0;
}
    double f_t[2];
    for (_zzero247 = 0; _zzero247 < (2); ++_zzero247) {
        f_t[_zzero247] = 0.0;
}
    double f_st[2];
    for (_zzero248 = 0; _zzero248 < (2); ++_zzero248) {
        f_st[_zzero248] = 0.0;
}
    double f_cy[2];
    for (_zzero249 = 0; _zzero249 < (2); ++_zzero249) {
        f_cy[_zzero249] = 0.0;
}
    int f_mo[2];
    for (_zzero250 = 0; _zzero250 < (2); ++_zzero250) {
        f_mo[_zzero250] = 0;
}
    int f_en[2];
    for (_zzero251 = 0; _zzero251 < (2); ++_zzero251) {
        f_en[_zzero251] = 0;
}
    int f_cv[2];
    for (_zzero252 = 0; _zzero252 < (2); ++_zzero252) {
        f_cv[_zzero252] = 0;
}
    int f_dp[2];
    for (_zzero253 = 0; _zzero253 < (2); ++_zzero253) {
        f_dp[_zzero253] = 0;
}
    int f_cl[2];
    for (_zzero254 = 0; _zzero254 < (2); ++_zzero254) {
        f_cl[_zzero254] = 0;
}
    int f_rp[2];
    for (_zzero255 = 0; _zzero255 < (2); ++_zzero255) {
        f_rp[_zzero255] = 0;
}
    int f_td[2];
    for (_zzero256 = 0; _zzero256 < (2); ++_zzero256) {
        f_td[_zzero256] = 0;
}
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
    for (_zzero257 = 0; _zzero257 < (2); ++_zzero257) {
        h_mo[_zzero257] = 0;
}
    double h_t[2];
    for (_zzero258 = 0; _zzero258 < (2); ++_zzero258) {
        h_t[_zzero258] = 0.0;
}
    double h_from[6];
    for (_zzero259 = 0; _zzero259 < (6); ++_zzero259) {
        h_from[_zzero259] = 0.0;
}
    double h_to[6];
    for (_zzero260 = 0; _zzero260 < (6); ++_zzero260) {
        h_to[_zzero260] = 0.0;
}
    double h_py[2];
    for (_zzero261 = 0; _zzero261 < (2); ++_zzero261) {
        h_py[_zzero261] = 0.0;
}
    double h_ap[2];
    for (_zzero262 = 0; _zzero262 < (2); ++_zzero262) {
        h_ap[_zzero262] = 0.0;
}
    double h_mp[2];
    for (_zzero263 = 0; _zzero263 < (2); ++_zzero263) {
        h_mp[_zzero263] = 0.0;
}
    int h_br[2];
    for (_zzero264 = 0; _zzero264 < (2); ++_zzero264) {
        h_br[_zzero264] = 0;
}
    int h_held[2];
    for (_zzero265 = 0; _zzero265 < (2); ++_zzero265) {
        h_held[_zzero265] = 0;
}
    long long h_lf[2];
    for (_zzero266 = 0; _zzero266 < (2); ++_zzero266) {
        h_lf[_zzero266] = 0;
}
    long long h_lt[2];
    for (_zzero267 = 0; _zzero267 < (2); ++_zzero267) {
        h_lt[_zzero267] = 0;
}
    int h_fi[2];
    for (_zzero268 = 0; _zzero268 < (2); ++_zzero268) {
        h_fi[_zzero268] = 0;
}
    int h_tds[2];
    for (_zzero269 = 0; _zzero269 < (2); ++_zzero269) {
        h_tds[_zzero269] = 0;
}
    double h_xo[2];
    for (_zzero270 = 0; _zzero270 < (2); ++_zzero270) {
        h_xo[_zzero270] = 0.0;
}
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
    for (_zzero271 = 0; _zzero271 < (1); ++_zzero271) {
        adv[_zzero271] = 0;
}
    adv[0] = a_adv_calls[e];
    Tf =  cst[CF_t_cycle] / cst[CF_dt];
    tair =  (double)(csti[CI_tair]);
    walking =  (int)(1);
    if (csti[CI_gait_enabled] == 0 || settle_n > 0 || csti[CI_reflex_level] == 0) {
        walking =  0;
}
    double M[324];
    for (_zzero272 = 0; _zzero272 < (324); ++_zzero272) {
        M[_zzero272] = 0.0;
}
    double gv[18];
    for (_zzero273 = 0; _zzero273 < (18); ++_zzero273) {
        gv[_zzero273] = 0.0;
}
    double bv[18];
    for (_zzero274 = 0; _zzero274 < (18); ++_zzero274) {
        bv[_zzero274] = 0.0;
}
    double fr[224];
    for (_zzero275 = 0; _zzero275 < (224); ++_zzero275) {
        fr[_zzero275] = 0.0;
}
    double frd[224];
    for (_zzero276 = 0; _zzero276 < (224); ++_zzero276) {
        frd[_zzero276] = 0.0;
}
    double frdd[224];
    for (_zzero277 = 0; _zzero277 < (224); ++_zzero277) {
        frdd[_zzero277] = 0.0;
}
    double axw[54];
    for (_zzero278 = 0; _zzero278 < (54); ++_zzero278) {
        axw[_zzero278] = 0.0;
}
    double axpiv[54];
    for (_zzero279 = 0; _zzero279 < (54); ++_zzero279) {
        axpiv[_zzero279] = 0.0;
}
    double axdir[54];
    for (_zzero280 = 0; _zzero280 < (54); ++_zzero280) {
        axdir[_zzero280] = 0.0;
}
    double ptp[24];
    for (_zzero281 = 0; _zzero281 < (24); ++_zzero281) {
        ptp[_zzero281] = 0.0;
}
    double ptJ[216];
    for (_zzero282 = 0; _zzero282 < (216); ++_zzero282) {
        ptJ[_zzero282] = 0.0;
}
    double ptcop[12];
    for (_zzero283 = 0; _zzero283 < (12); ++_zzero283) {
        ptcop[_zzero283] = 0.0;
}
    double ptbias[12];
    for (_zzero284 = 0; _zzero284 < (12); ++_zzero284) {
        ptbias[_zzero284] = 0.0;
}
    double inv[324];
    for (_zzero285 = 0; _zzero285 < (324); ++_zzero285) {
        inv[_zzero285] = 0.0;
}
    double free[18];
    for (_zzero286 = 0; _zzero286 < (18); ++_zzero286) {
        free[_zzero286] = 0.0;
}
    double qa[18];
    for (_zzero287 = 0; _zzero287 < (18); ++_zzero287) {
        qa[_zzero287] = 0.0;
}
    double va[18];
    for (_zzero288 = 0; _zzero288 < (18); ++_zzero288) {
        va[_zzero288] = 0.0;
}
    double qb[18];
    for (_zzero289 = 0; _zzero289 < (18); ++_zzero289) {
        qb[_zzero289] = 0.0;
}
    double vb[18];
    for (_zzero290 = 0; _zzero290 < (18); ++_zzero290) {
        vb[_zzero290] = 0.0;
}
    double qc[18];
    for (_zzero291 = 0; _zzero291 < (18); ++_zzero291) {
        qc[_zzero291] = 0.0;
}
    double vc[18];
    for (_zzero292 = 0; _zzero292 < (18); ++_zzero292) {
        vc[_zzero292] = 0.0;
}
    double qd[18];
    for (_zzero293 = 0; _zzero293 < (18); ++_zzero293) {
        qd[_zzero293] = 0.0;
}
    double vd[18];
    for (_zzero294 = 0; _zzero294 < (18); ++_zzero294) {
        vd[_zzero294] = 0.0;
}
    double qe[18];
    for (_zzero295 = 0; _zzero295 < (18); ++_zzero295) {
        qe[_zzero295] = 0.0;
}
    double ve[18];
    for (_zzero296 = 0; _zzero296 < (18); ++_zzero296) {
        ve[_zzero296] = 0.0;
}
    double we[18];
    for (_zzero297 = 0; _zzero297 < (18); ++_zzero297) {
        we[_zzero297] = 0.0;
}
    double sq[576];
    for (_zzero298 = 0; _zzero298 < (576); ++_zzero298) {
        sq[_zzero298] = 0.0;
}
    double sh16[16];
    for (_zzero299 = 0; _zzero299 < (16); ++_zzero299) {
        sh16[_zzero299] = 0.0;
}
    int sdep[16];
    for (_zzero300 = 0; _zzero300 < (16); ++_zzero300) {
        sdep[_zzero300] = 0;
}
    int scl[16];
    for (_zzero301 = 0; _zzero301 < (16); ++_zzero301) {
        scl[_zzero301] = 0;
}
    double tr_q[18];
    for (_zzero302 = 0; _zzero302 < (18); ++_zzero302) {
        tr_q[_zzero302] = 0.0;
}
    double tr_v[18];
    for (_zzero303 = 0; _zzero303 < (18); ++_zzero303) {
        tr_v[_zzero303] = 0.0;
}
    double tr_w[18];
    for (_zzero304 = 0; _zzero304 < (18); ++_zzero304) {
        tr_w[_zzero304] = 0.0;
}
    double cd_q[18];
    for (_zzero305 = 0; _zzero305 < (18); ++_zzero305) {
        cd_q[_zzero305] = 0.0;
}
    double cd_v[18];
    for (_zzero306 = 0; _zzero306 < (18); ++_zzero306) {
        cd_v[_zzero306] = 0.0;
}
    double cd_w[18];
    for (_zzero307 = 0; _zzero307 < (18); ++_zzero307) {
        cd_w[_zzero307] = 0.0;
}
    double tau[18];
    for (_zzero308 = 0; _zzero308 < (18); ++_zzero308) {
        tau[_zzero308] = 0.0;
}
    double srq[18];
    for (_zzero309 = 0; _zzero309 < (18); ++_zzero309) {
        srq[_zzero309] = 0.0;
}
    double srv[18];
    for (_zzero310 = 0; _zzero310 < (18); ++_zzero310) {
        srv[_zzero310] = 0.0;
}
    double scales[13];
    for (_zzero311 = 0; _zzero311 < (13); ++_zzero311) {
        scales[_zzero311] = 0.0;
}
    round_n =  (int)(0);
    int dsf[1];
    for (_zzero312 = 0; _zzero312 < (1); ++_zzero312) {
        dsf[_zzero312] = 0;
}
    double trial_q[18];
    for (_zzero313 = 0; _zzero313 < (18); ++_zzero313) {
        trial_q[_zzero313] = 0.0;
}
    double trial_v[18];
    for (_zzero314 = 0; _zzero314 < (18); ++_zzero314) {
        trial_v[_zzero314] = 0.0;
}
    double trial_w[18];
    for (_zzero315 = 0; _zzero315 < (18); ++_zzero315) {
        trial_w[_zzero315] = 0.0;
}
    double o_q[18];
    for (_zzero316 = 0; _zzero316 < (18); ++_zzero316) {
        o_q[_zzero316] = 0.0;
}
    double o_v[18];
    for (_zzero317 = 0; _zzero317 < (18); ++_zzero317) {
        o_v[_zzero317] = 0.0;
}
    double o_w[18];
    for (_zzero318 = 0; _zzero318 < (18); ++_zzero318) {
        o_w[_zzero318] = 0.0;
}
    double cur_w[18];
    for (_zzero319 = 0; _zzero319 < (18); ++_zzero319) {
        cur_w[_zzero319] = 0.0;
}
    double eff[18];
    for (_zzero320 = 0; _zzero320 < (18); ++_zzero320) {
        eff[_zzero320] = 0.0;
}
    double lta[18];
    for (_zzero321 = 0; _zzero321 < (18); ++_zzero321) {
        lta[_zzero321] = 0.0;
}
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
                        for (_zzero322 = 0; _zzero322 < (3); ++_zzero322) {
                            tgt[_zzero322] = 0.0;
}
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
                        fore_ik_at(mdl, cst, fr, fl, plt, ikb[fl], mdi, csti, &q1f, &q2f, &q1rx, &q2rx, &satf);
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
        for (_zzero323 = 0; _zzero323 < (1); ++_zzero323) {
            rca[_zzero323] = 0;
}
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
        advance(q, v, w, eff, cst[CF_dt] * (double)(0.25), mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl, adv, rca, o_q, o_v, o_w, mdi, csti);
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
                            scales[d - 1] = mid;
                            for (i = 0; i < (18); ++i) {
                                eff[i] = tau[i];
}
                            for (dsc = 0; dsc < (12); ++dsc) {
                                eff[mdi[OI_drive_coord + dsc]] = tau[mdi[OI_drive_coord + dsc]] * scales[dsc];
}
                            eff[2] = tau[2] * scales[12];
                            advance(q, v, w, eff, cst[CF_dt] * (double)(0.25), mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl, adv, rca, o_q, o_v, o_w, mdi, csti);
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
                advance(q, v, w, eff, cst[CF_dt] * (double)(0.25), mdl, cst, M, gv, bv, fr, frd, frdd, axw, axpiv, axdir, ptp, ptJ, ptcop, ptbias, inv, free, srq, srv, qa, va, qb, vb, qc, vc, qd, vd, qe, ve, we, sq, sh16, sdep, scl, adv, rca, o_q, o_v, o_w, mdi, csti);
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
    int _zzero324;
    int _zzero325;
    int _zzero326;
    int _zzero327;
    int i;
    int _zzero328;
    int d;
    double bat_post;
    int _zzero329;
    int _zzero330;
    double capt;
    double settle_n;
    int _zzero331;
    int _zzero332;
    int _zzero333;
    int _zzero334;
    int _zzero335;
    int _zzero336;
    int _zzero337;
    int _zzero338;
    int _zzero339;
    int _zzero340;
    int _zzero341;
    int _zzero342;
    int _zzero343;
    int _zzero344;
    int _zzero345;
    int l;
    int c;
    int _zzero346;
    int _zzero347;
    int _zzero348;
    int _zzero349;
    int _zzero350;
    int _zzero351;
    int _zzero352;
    int _zzero353;
    int _zzero354;
    int _zzero355;
    int _zzero356;
    int _zzero357;
    int _zzero358;
    int _zzero359;
    double h_latched;
    double cmd_v;
    double cmd_on;
    double cmd_first;
    double cmd_fires;
    int _zzero360;
    double Tf;
    double tair;
    int walking;
    int _zzero361;
    int _zzero362;
    int _zzero363;
    int _zzero364;
    int _zzero365;
    int _zzero366;
    int _zzero367;
    int _zzero368;
    int _zzero369;
    int _zzero370;
    int _zzero371;
    int _zzero372;
    int _zzero373;
    int _zzero374;
    int _zzero375;
    int _zzero376;
    int _zzero377;
    int _zzero378;
    int _zzero379;
    int _zzero380;
    int _zzero381;
    int _zzero382;
    int _zzero383;
    int _zzero384;
    int _zzero385;
    int _zzero386;
    int _zzero387;
    int _zzero388;
    int _zzero389;
    int _zzero390;
    int _zzero391;
    int _zzero392;
    int _zzero393;
    int _zzero394;
    int _zzero395;
    int _zzero396;
    int _zzero397;
    int _zzero398;
    int _zzero399;
    int _zzero400;
    int round_n;
    int _zzero401;
    int _zzero402;
    int _zzero403;
    int _zzero404;
    int _zzero405;
    int _zzero406;
    int _zzero407;
    int _zzero408;
    int _zzero409;
    int _zzero410;
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
    for (_zzero324 = 0; _zzero324 < (18); ++_zzero324) {
        q[_zzero324] = 0.0;
}
    double v[18];
    for (_zzero325 = 0; _zzero325 < (18); ++_zzero325) {
        v[_zzero325] = 0.0;
}
    double w[18];
    for (_zzero326 = 0; _zzero326 < (18); ++_zzero326) {
        w[_zzero326] = 0.0;
}
    double ltau[18];
    for (_zzero327 = 0; _zzero327 < (18); ++_zzero327) {
        ltau[_zzero327] = 0.0;
}
    for (i = 0; i < (18); ++i) {
        q[i] = a_q[e * 18 + i];
        v[i] = a_v[e * 18 + i];
        w[i] = a_work[e * 18 + i];
        ltau[i] = a_last_torque[e * 18 + i];
}
    double bat[12];
    for (_zzero328 = 0; _zzero328 < (12); ++_zzero328) {
        bat[_zzero328] = 0.0;
}
    for (d = 0; d < (12); ++d) {
        bat[d] = a_battery[e * 12 + d];
}
    bat_post =  a_battery_post[e];
    double phi[2];
    for (_zzero329 = 0; _zzero329 < (2); ++_zzero329) {
        phi[_zzero329] = 0.0;
}
    phi[0] = a_phi[e * 2];
    phi[1] = a_phi[e * 2 + 1];
    int tch[2];
    for (_zzero330 = 0; _zzero330 < (2); ++_zzero330) {
        tch[_zzero330] = 0;
}
    tch[0] = a_touching[e * 2];
    tch[1] = a_touching[e * 2 + 1];
    capt =  a_captured[e];
    settle_n =  a_settle[e];
    int ikb[2];
    for (_zzero331 = 0; _zzero331 < (2); ++_zzero331) {
        ikb[_zzero331] = 0;
}
    ikb[0] = a_ik_branch[e * 2];
    ikb[1] = a_ik_branch[e * 2 + 1];
    double paw_t[6];
    for (_zzero332 = 0; _zzero332 < (6); ++_zzero332) {
        paw_t[_zzero332] = 0.0;
}
    double paw_y[2];
    for (_zzero333 = 0; _zzero333 < (2); ++_zzero333) {
        paw_y[_zzero333] = 0.0;
}
    double swf[6];
    for (_zzero334 = 0; _zzero334 < (6); ++_zzero334) {
        swf[_zzero334] = 0.0;
}
    double swt[6];
    for (_zzero335 = 0; _zzero335 < (6); ++_zzero335) {
        swt[_zzero335] = 0.0;
}
    double f_t[2];
    for (_zzero336 = 0; _zzero336 < (2); ++_zzero336) {
        f_t[_zzero336] = 0.0;
}
    double f_st[2];
    for (_zzero337 = 0; _zzero337 < (2); ++_zzero337) {
        f_st[_zzero337] = 0.0;
}
    double f_cy[2];
    for (_zzero338 = 0; _zzero338 < (2); ++_zzero338) {
        f_cy[_zzero338] = 0.0;
}
    int f_mo[2];
    for (_zzero339 = 0; _zzero339 < (2); ++_zzero339) {
        f_mo[_zzero339] = 0;
}
    int f_en[2];
    for (_zzero340 = 0; _zzero340 < (2); ++_zzero340) {
        f_en[_zzero340] = 0;
}
    int f_cv[2];
    for (_zzero341 = 0; _zzero341 < (2); ++_zzero341) {
        f_cv[_zzero341] = 0;
}
    int f_dp[2];
    for (_zzero342 = 0; _zzero342 < (2); ++_zzero342) {
        f_dp[_zzero342] = 0;
}
    int f_cl[2];
    for (_zzero343 = 0; _zzero343 < (2); ++_zzero343) {
        f_cl[_zzero343] = 0;
}
    int f_rp[2];
    for (_zzero344 = 0; _zzero344 < (2); ++_zzero344) {
        f_rp[_zzero344] = 0;
}
    int f_td[2];
    for (_zzero345 = 0; _zzero345 < (2); ++_zzero345) {
        f_td[_zzero345] = 0;
}
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
    for (_zzero346 = 0; _zzero346 < (2); ++_zzero346) {
        h_mo[_zzero346] = 0;
}
    double h_t[2];
    for (_zzero347 = 0; _zzero347 < (2); ++_zzero347) {
        h_t[_zzero347] = 0.0;
}
    double h_from[6];
    for (_zzero348 = 0; _zzero348 < (6); ++_zzero348) {
        h_from[_zzero348] = 0.0;
}
    double h_to[6];
    for (_zzero349 = 0; _zzero349 < (6); ++_zzero349) {
        h_to[_zzero349] = 0.0;
}
    double h_py[2];
    for (_zzero350 = 0; _zzero350 < (2); ++_zzero350) {
        h_py[_zzero350] = 0.0;
}
    double h_ap[2];
    for (_zzero351 = 0; _zzero351 < (2); ++_zzero351) {
        h_ap[_zzero351] = 0.0;
}
    double h_mp[2];
    for (_zzero352 = 0; _zzero352 < (2); ++_zzero352) {
        h_mp[_zzero352] = 0.0;
}
    int h_br[2];
    for (_zzero353 = 0; _zzero353 < (2); ++_zzero353) {
        h_br[_zzero353] = 0;
}
    int h_held[2];
    for (_zzero354 = 0; _zzero354 < (2); ++_zzero354) {
        h_held[_zzero354] = 0;
}
    long long h_lf[2];
    for (_zzero355 = 0; _zzero355 < (2); ++_zzero355) {
        h_lf[_zzero355] = 0;
}
    long long h_lt[2];
    for (_zzero356 = 0; _zzero356 < (2); ++_zzero356) {
        h_lt[_zzero356] = 0;
}
    int h_fi[2];
    for (_zzero357 = 0; _zzero357 < (2); ++_zzero357) {
        h_fi[_zzero357] = 0;
}
    int h_tds[2];
    for (_zzero358 = 0; _zzero358 < (2); ++_zzero358) {
        h_tds[_zzero358] = 0;
}
    double h_xo[2];
    for (_zzero359 = 0; _zzero359 < (2); ++_zzero359) {
        h_xo[_zzero359] = 0.0;
}
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
    for (_zzero360 = 0; _zzero360 < (1); ++_zzero360) {
        adv[_zzero360] = 0;
}
    adv[0] = a_adv_calls[e];
    Tf =  cst[CF_t_cycle] / cst[CF_dt];
    tair =  (double)(csti[CI_tair]);
    walking =  (int)(1);
    if (csti[CI_gait_enabled] == 0 || settle_n > 0 || csti[CI_reflex_level] == 0) {
        walking =  0;
}
    double M[324];
    for (_zzero361 = 0; _zzero361 < (324); ++_zzero361) {
        M[_zzero361] = 0.0;
}
    double gv[18];
    for (_zzero362 = 0; _zzero362 < (18); ++_zzero362) {
        gv[_zzero362] = 0.0;
}
    double bv[18];
    for (_zzero363 = 0; _zzero363 < (18); ++_zzero363) {
        bv[_zzero363] = 0.0;
}
    double fr[224];
    for (_zzero364 = 0; _zzero364 < (224); ++_zzero364) {
        fr[_zzero364] = 0.0;
}
    double frd[224];
    for (_zzero365 = 0; _zzero365 < (224); ++_zzero365) {
        frd[_zzero365] = 0.0;
}
    double frdd[224];
    for (_zzero366 = 0; _zzero366 < (224); ++_zzero366) {
        frdd[_zzero366] = 0.0;
}
    double axw[54];
    for (_zzero367 = 0; _zzero367 < (54); ++_zzero367) {
        axw[_zzero367] = 0.0;
}
    double axpiv[54];
    for (_zzero368 = 0; _zzero368 < (54); ++_zzero368) {
        axpiv[_zzero368] = 0.0;
}
    double axdir[54];
    for (_zzero369 = 0; _zzero369 < (54); ++_zzero369) {
        axdir[_zzero369] = 0.0;
}
    double ptp[24];
    for (_zzero370 = 0; _zzero370 < (24); ++_zzero370) {
        ptp[_zzero370] = 0.0;
}
    double ptJ[216];
    for (_zzero371 = 0; _zzero371 < (216); ++_zzero371) {
        ptJ[_zzero371] = 0.0;
}
    double ptcop[12];
    for (_zzero372 = 0; _zzero372 < (12); ++_zzero372) {
        ptcop[_zzero372] = 0.0;
}
    double ptbias[12];
    for (_zzero373 = 0; _zzero373 < (12); ++_zzero373) {
        ptbias[_zzero373] = 0.0;
}
    double inv[324];
    for (_zzero374 = 0; _zzero374 < (324); ++_zzero374) {
        inv[_zzero374] = 0.0;
}
    double free[18];
    for (_zzero375 = 0; _zzero375 < (18); ++_zzero375) {
        free[_zzero375] = 0.0;
}
    double qa[18];
    for (_zzero376 = 0; _zzero376 < (18); ++_zzero376) {
        qa[_zzero376] = 0.0;
}
    double va[18];
    for (_zzero377 = 0; _zzero377 < (18); ++_zzero377) {
        va[_zzero377] = 0.0;
}
    double qb[18];
    for (_zzero378 = 0; _zzero378 < (18); ++_zzero378) {
        qb[_zzero378] = 0.0;
}
    double vb[18];
    for (_zzero379 = 0; _zzero379 < (18); ++_zzero379) {
        vb[_zzero379] = 0.0;
}
    double qc[18];
    for (_zzero380 = 0; _zzero380 < (18); ++_zzero380) {
        qc[_zzero380] = 0.0;
}
    double vc[18];
    for (_zzero381 = 0; _zzero381 < (18); ++_zzero381) {
        vc[_zzero381] = 0.0;
}
    double qd[18];
    for (_zzero382 = 0; _zzero382 < (18); ++_zzero382) {
        qd[_zzero382] = 0.0;
}
    double vd[18];
    for (_zzero383 = 0; _zzero383 < (18); ++_zzero383) {
        vd[_zzero383] = 0.0;
}
    double qe[18];
    for (_zzero384 = 0; _zzero384 < (18); ++_zzero384) {
        qe[_zzero384] = 0.0;
}
    double ve[18];
    for (_zzero385 = 0; _zzero385 < (18); ++_zzero385) {
        ve[_zzero385] = 0.0;
}
    double we[18];
    for (_zzero386 = 0; _zzero386 < (18); ++_zzero386) {
        we[_zzero386] = 0.0;
}
    double sq[576];
    for (_zzero387 = 0; _zzero387 < (576); ++_zzero387) {
        sq[_zzero387] = 0.0;
}
    double sh16[16];
    for (_zzero388 = 0; _zzero388 < (16); ++_zzero388) {
        sh16[_zzero388] = 0.0;
}
    int sdep[16];
    for (_zzero389 = 0; _zzero389 < (16); ++_zzero389) {
        sdep[_zzero389] = 0;
}
    int scl[16];
    for (_zzero390 = 0; _zzero390 < (16); ++_zzero390) {
        scl[_zzero390] = 0;
}
    double tr_q[18];
    for (_zzero391 = 0; _zzero391 < (18); ++_zzero391) {
        tr_q[_zzero391] = 0.0;
}
    double tr_v[18];
    for (_zzero392 = 0; _zzero392 < (18); ++_zzero392) {
        tr_v[_zzero392] = 0.0;
}
    double tr_w[18];
    for (_zzero393 = 0; _zzero393 < (18); ++_zzero393) {
        tr_w[_zzero393] = 0.0;
}
    double cd_q[18];
    for (_zzero394 = 0; _zzero394 < (18); ++_zzero394) {
        cd_q[_zzero394] = 0.0;
}
    double cd_v[18];
    for (_zzero395 = 0; _zzero395 < (18); ++_zzero395) {
        cd_v[_zzero395] = 0.0;
}
    double cd_w[18];
    for (_zzero396 = 0; _zzero396 < (18); ++_zzero396) {
        cd_w[_zzero396] = 0.0;
}
    double tau[18];
    for (_zzero397 = 0; _zzero397 < (18); ++_zzero397) {
        tau[_zzero397] = 0.0;
}
    double srq[18];
    for (_zzero398 = 0; _zzero398 < (18); ++_zzero398) {
        srq[_zzero398] = 0.0;
}
    double srv[18];
    for (_zzero399 = 0; _zzero399 < (18); ++_zzero399) {
        srv[_zzero399] = 0.0;
}
    double scales[13];
    for (_zzero400 = 0; _zzero400 < (13); ++_zzero400) {
        scales[_zzero400] = 0.0;
}
    round_n =  (int)(0);
    int dsf[1];
    for (_zzero401 = 0; _zzero401 < (1); ++_zzero401) {
        dsf[_zzero401] = 0;
}
    double trial_q[18];
    for (_zzero402 = 0; _zzero402 < (18); ++_zzero402) {
        trial_q[_zzero402] = 0.0;
}
    double trial_v[18];
    for (_zzero403 = 0; _zzero403 < (18); ++_zzero403) {
        trial_v[_zzero403] = 0.0;
}
    double trial_w[18];
    for (_zzero404 = 0; _zzero404 < (18); ++_zzero404) {
        trial_w[_zzero404] = 0.0;
}
    double o_q[18];
    for (_zzero405 = 0; _zzero405 < (18); ++_zzero405) {
        o_q[_zzero405] = 0.0;
}
    double o_v[18];
    for (_zzero406 = 0; _zzero406 < (18); ++_zzero406) {
        o_v[_zzero406] = 0.0;
}
    double o_w[18];
    for (_zzero407 = 0; _zzero407 < (18); ++_zzero407) {
        o_w[_zzero407] = 0.0;
}
    double cur_w[18];
    for (_zzero408 = 0; _zzero408 < (18); ++_zzero408) {
        cur_w[_zzero408] = 0.0;
}
    double eff[18];
    for (_zzero409 = 0; _zzero409 < (18); ++_zzero409) {
        eff[_zzero409] = 0.0;
}
    double lta[18];
    for (_zzero410 = 0; _zzero410 < (18); ++_zzero410) {
        lta[_zzero410] = 0.0;
}
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
