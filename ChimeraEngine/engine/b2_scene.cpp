// B2 scene implementation. See b2_scene.hpp for provenance: every physical
// formulation is ported from the accepted coupon model (native_coupon.cpp);
// this file adds only the resident-runtime plumbing around them.
#include "b2_scene.hpp"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

// ─── small linear algebra (coupon style: row-major M3, V3 as double[3]) ──────
using V3 = double[3];
using M3 = double[9];   // row-major

double dot3(const V3 a, const V3 b) { return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; }
void cross3(const V3 a, const V3 b, V3 o) {
    o[0]=a[1]*b[2]-a[2]*b[1]; o[1]=a[2]*b[0]-a[0]*b[2]; o[2]=a[0]*b[1]-a[1]*b[0];
}
void mat3_v(const M3 R, const V3 v, V3 o) {
    for (int i = 0; i < 3; ++i) o[i] = R[3*i]*v[0] + R[3*i+1]*v[1] + R[3*i+2]*v[2];
}
void mat3_mul(const M3 A, const M3 B, M3 o) {
    M3 t;
    for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j)
        t[3*i+j] = A[3*i]*B[j] + A[3*i+1]*B[3+j] + A[3*i+2]*B[6+j];
    for (int i = 0; i < 9; ++i) o[i] = t[i];
}
double mat3_det(const M3 A) {
    return A[0]*(A[4]*A[8]-A[5]*A[7]) - A[1]*(A[3]*A[8]-A[5]*A[6])
         + A[2]*(A[3]*A[7]-A[4]*A[6]);
}
// Cramer solve A x = b; false if singular (coupon solve3, :70)
bool solve3(const M3 A, const V3 b, V3 x) {
    double det = mat3_det(A);
    if (std::fabs(det) < 1e-300) return false;
    M3 C;
    for (int col = 0; col < 3; ++col) {
        for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j)
            C[3*i+j] = (j == col) ? b[i] : A[3*i+j];
        x[col] = mat3_det(C) / det;
    }
    return true;
}
// Rodrigues exponential map: out = exp(h*[w]x) (coupon rot_exp, :80)
void rot_exp(const V3 w, double h, M3 out) {
    double wx = h*w[0], wy = h*w[1], wz = h*w[2];
    double th2 = wx*wx + wy*wy + wz*wz;
    double th = std::sqrt(th2);
    double A = 1.0, B = 0.5, C = 1.0/6.0;
    if (th > 1e-8) {
        double s = std::sin(th);
        A = s / th;
        B = (1.0 - std::cos(th)) / th2;
        C = (1.0 - A) / th2;
    }
    M3 K = {0, -wz, wy,  wz, 0, -wx,  -wy, wx, 0};
    M3 K2; mat3_mul(K, K, K2);
    for (int i = 0; i < 9; ++i) out[i] = (i%4==0 ? 1.0 : 0.0) + A*K[i] + B*K2[i];
    (void)C;
}
// eigenvalues of a symmetric 3x3 (trig method), descending: e0>=e1>=e2
void eigen_sym3(const M3 A, double e[3]) {
    double p1 = A[5]*A[5] + A[2]*A[2] + A[1]*A[1];
    double q = (A[0]+A[4]+A[8]) / 3.0;
    if (p1 < 1e-300) { e[0]=e[1]=e[2]=q; return; }
    double p2 = (A[0]-q)*(A[0]-q) + (A[4]-q)*(A[4]-q) + (A[8]-q)*(A[8]-q) + 2.0*p1;
    double p = std::sqrt(p2 / 6.0);
    double B[9];
    for (int i = 0; i < 9; ++i) B[i] = ((i%4==0) ? A[i]-q : A[i]) / p;
    double r = mat3_det(B) / 2.0;
    r = std::fmax(-1.0, std::fmin(1.0, r));
    double phi = std::acos(r) / 3.0;
    double m2pi = 2.0 * 3.14159265358979323846 / 3.0;
    e[0] = q + 2.0*p*std::cos(phi);
    e[2] = q + 2.0*p*std::cos(phi + m2pi);
    e[1] = 3.0*q - e[0] - e[2];
}
// quaternion (w,x,y,z) -> rotation matrix (proper by construction)
void quat_to_mat3(const double q[4], M3 R) {
    double w=q[0], x=q[1], y=q[2], z=q[3];
    R[0]=1-2*(y*y+z*z); R[1]=2*(x*y-w*z);   R[2]=2*(x*z+w*y);
    R[3]=2*(x*y+w*z);   R[4]=1-2*(x*x+z*z); R[5]=2*(y*z-w*x);
    R[6]=2*(x*z-w*y);   R[7]=2*(y*z+w*x);   R[8]=1-2*(x*x+y*y);
}
// rotation matrix -> quaternion (w,x,y,z), Shepperd's method
void mat3_to_quat(const M3 R, double q[4]) {
    double tr = R[0]+R[4]+R[8];
    if (tr > 0) {
        double s = std::sqrt(tr+1.0)*2;
        q[0]=0.25*s; q[1]=(R[7]-R[5])/s; q[2]=(R[2]-R[6])/s; q[3]=(R[3]-R[1])/s;
    } else if (R[0] > R[4] && R[0] > R[8]) {
        double s = std::sqrt(1.0+R[0]-R[4]-R[8])*2;
        q[0]=(R[7]-R[5])/s; q[1]=0.25*s; q[2]=(R[1]+R[3])/s; q[3]=(R[2]+R[6])/s;
    } else if (R[4] > R[8]) {
        double s = std::sqrt(1.0+R[4]-R[0]-R[8])*2;
        q[0]=(R[2]-R[6])/s; q[1]=(R[1]+R[3])/s; q[2]=0.25*s; q[3]=(R[5]+R[7])/s;
    } else {
        double s = std::sqrt(1.0+R[8]-R[0]-R[4])*2;
        q[0]=(R[3]-R[1])/s; q[1]=(R[2]+R[6])/s; q[2]=(R[5]+R[7])/s; q[3]=0.25*s;
    }
}

std::string fmt(double x) {
    char buf[64];
    std::snprintf(buf, sizeof buf, "%.9g", x);
    return buf;
}
std::string json_escape(const std::string &s) {
    std::string o;
    for (char ch : s) {
        if (ch == '"' || ch == '\\') { o += '\\'; o += ch; }
        else if (ch == '\n') o += "\\n";
        else o += ch;
    }
    return o;
}

// ─── minimal strict JSON reader (no deps; coupon JV precedent) ──────────────
struct JVal {
    enum T { OBJ, ARR, NUM, STR, BOOL, NUL } t = NUL;
    std::vector<std::pair<std::string, JVal*>> obj;
    std::vector<JVal*> arr;
    double num = 0;
    std::string str;
    bool bval = false;
};

struct JParser {
    const char *p;
    std::vector<std::unique_ptr<JVal>> arena;
    int depth = 0;

    JVal* mk() { arena.push_back(std::unique_ptr<JVal>(new JVal())); return arena.back().get(); }
    void ws() { while (*p==' '||*p=='\t'||*p=='\n'||*p=='\r') ++p; }
    [[noreturn]] void die(const std::string &why) { throw std::runtime_error(why); }

    JVal* value() {
        if (++depth > 32) die("json nested deeper than 32");
        ws();
        JVal *v = mk();
        if (*p == '{') {
            v->t = JVal::OBJ; ++p; ws();
            if (*p == '}') { ++p; --depth; return v; }
            for (;;) {
                ws();
                if (*p != '"') die("object key must be a string");
                JVal *k = parse_string_raw();
                ws();
                if (*p != ':') die("expected ':' after object key");
                ++p;
                JVal *val = value();
                for (auto &kv : v->obj) if (kv.first == k->str) die("duplicate object key '" + k->str + "'");
                v->obj.emplace_back(k->str, val);
                ws();
                if (*p == ',') { ++p; continue; }
                if (*p == '}') { ++p; break; }
                die("expected ',' or '}' in object");
            }
        } else if (*p == '[') {
            v->t = JVal::ARR; ++p; ws();
            if (*p == ']') { ++p; --depth; return v; }
            for (;;) {
                v->arr.push_back(value());
                ws();
                if (*p == ',') { ++p; continue; }
                if (*p == ']') { ++p; break; }
                die("expected ',' or ']' in array");
            }
        } else if (*p == '"') {
            JVal *s = parse_string_raw();
            v->t = JVal::STR; v->str = s->str;
        } else if (*p == 't') {
            if (std::strncmp(p, "true", 4)) die("bad literal");
            p += 4; v->t = JVal::BOOL; v->bval = true;
        } else if (*p == 'f') {
            if (std::strncmp(p, "false", 5)) die("bad literal");
            p += 5; v->t = JVal::BOOL; v->bval = false;
        } else if (*p == 'n') {
            if (std::strncmp(p, "null", 4)) die("bad literal");
            p += 4; v->t = JVal::NUL;
        } else if (*p == '-' || (*p >= '0' && *p <= '9')) {
            char *e = nullptr;
            double d = std::strtod(p, &e);
            if (e == p) die("bad number");
            p = e;
            if (!std::isfinite(d)) die("number must be finite");
            v->t = JVal::NUM; v->num = d;
        } else die("unexpected json character");
        --depth;
        return v;
    }
    JVal* parse_string_raw() {
        JVal *v = mk(); v->t = JVal::STR;
        ++p;
        for (;;) {
            if (!*p) die("unterminated string");
            char ch = *p++;
            if (ch == '"') break;
            if (ch == '\\') {
                char e = *p++;
                switch (e) {
                    case '"': v->str += '"'; break;
                    case '\\': v->str += '\\'; break;
                    case '/': v->str += '/'; break;
                    case 'n': v->str += '\n'; break;
                    case 't': v->str += '\t'; break;
                    case 'r': v->str += '\r'; break;
                    case 'b': v->str += '\b'; break;
                    case 'f': v->str += '\f'; break;
                    default: die("bad string escape");
                }
            } else v->str += ch;
        }
        return v;
    }
    JVal* parse() {
        JVal *v = value();
        ws();
        if (*p) die("trailing characters after json");
        return v;
    }
};

// ─── validation helpers (coupon req_keys/fnum precedent, :297-308) ──────────
JVal* need(const JVal &o, const char *key, const std::string &where) {
    for (auto &kv : o.obj) if (kv.first == key) return kv.second;
    throw std::runtime_error(where + ": missing required field '" + key + "'");
}
void req_keys(const JVal &o, std::initializer_list<const char*> allowed,
              std::initializer_list<const char*> optional, const std::string &where) {
    for (auto &kv : o.obj) {
        bool ok = false;
        for (auto a : allowed) if (kv.first == a) ok = true;
        if (!ok) throw std::runtime_error(where + ": unknown field '" + kv.first + "'");
        (void)optional;
    }
}
double fnum(const JVal &v, const std::string &where) {
    if (v.t != JVal::NUM) throw std::runtime_error(where + ": number expected");
    if (!std::isfinite(v.num)) throw std::runtime_error(where + ": number must be finite");
    return v.num;
}
std::vector<double> num_array(const JVal &v, size_t len, const std::string &where) {
    if (v.t != JVal::ARR) throw std::runtime_error(where + ": array expected");
    if (v.arr.size() != len)
        throw std::runtime_error(where + ": expected exactly " + std::to_string(len) +
                                 " numbers, got " + std::to_string(v.arr.size()));
    std::vector<double> o;
    for (size_t i = 0; i < len; ++i) o.push_back(fnum(*v.arr[i], where + "[" + std::to_string(i) + "]"));
    return o;
}

} // namespace

// ─── admission: strict chimera.b2_scene.v1 ───────────────────────────────────
std::string B2Scene::admit(const std::string &json, const std::string &reason) {
    try {
        JParser jp{json.c_str(), {}, 0};
        JVal *root = jp.parse();
        if (root->t != JVal::OBJ) throw std::runtime_error("scene document must be a json object");
        req_keys(*root, {"schema","gravity_m_s2","parts","reason"}, {}, "scene");

        JVal *schema = need(*root, "schema", "scene");
        if (schema->t != JVal::STR || schema->str != "chimera.b2_scene.v1")
            throw std::runtime_error("scene: schema must be \"chimera.b2_scene.v1\"");

        double gravity = 9.81;
        for (auto &kv : root->obj)
            if (kv.first == "gravity_m_s2") {
                gravity = fnum(*kv.second, "scene.gravity_m_s2");
                if (gravity < 0.0) throw std::runtime_error("scene.gravity_m_s2: must be >= 0");
            }
        std::string why = reason;
        for (auto &kv : root->obj)
            if (kv.first == "reason" && kv.second->t == JVal::STR) why = kv.second->str;

        // The support rung is PER PART (not scene-level): the rung law is
        // the FALL's one-sided penalty contact, but its constants are
        // derived from each part's own mass (rest sink s* and damping
        // ratio zeta, the same derivation that produced k_ground_/
        // c_ground_ for the 13.8 t resident body). Reusing the resident
        // constants verbatim on a ~10 kg part would make the explicit
        // damping term unstable (h*c/m >> 2) and is physically wrong.
        JVal *parts = need(*root, "parts", "scene");
        if (parts->t != JVal::ARR) throw std::runtime_error("scene.parts: array expected");
        if (parts->arr.size() != 2)
            throw std::runtime_error("scene.parts: B2 needs exactly two parts, got " +
                                     std::to_string(parts->arr.size()));

        std::vector<Part> built;
        for (size_t pi = 0; pi < parts->arr.size(); ++pi) {
            const JVal &pj = *parts->arr[pi];
            std::string where = "scene.parts[" + std::to_string(pi) + "]";
            if (pj.t != JVal::OBJ) throw std::runtime_error(where + ": object expected");
            req_keys(pj, {"id","mass_kg","com_local_m","inertia_com_local_kg_m2",
                          "vertices_local_m","boundary_triangles","pose_c_m","pose_q_wxyz",
                          "ground"},
                     {}, where);
            Part p;
            JVal *idj = need(pj, "id", where);
            if (idj->t != JVal::STR || idj->str.empty())
                throw std::runtime_error(where + ".id: non-empty string expected");
            p.id = idj->str;
            for (auto &q : built)
                if (q.id == p.id) throw std::runtime_error(where + ".id: duplicate part id '" + p.id + "'");
            p.mass = fnum(*need(pj, "mass_kg", where), where + ".mass_kg");
            if (p.mass <= 0.0) throw std::runtime_error(where + ".mass_kg: must be positive");
            std::vector<double> com = num_array(*need(pj, "com_local_m", where), 3, where + ".com_local_m");
            for (int i = 0; i < 3; ++i) p.com_local[i] = com[i];

            std::vector<double> I = num_array(*need(pj, "inertia_com_local_kg_m2", where), 9,
                                              where + ".inertia_com_local_kg_m2");
            // symmetry (coupon check_proper_rotation analogue for tensors)
            double imax = 0;
            for (int i = 0; i < 9; ++i) imax = std::fmax(imax, std::fabs(I[i]));
            for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j)
                if (std::fabs(I[3*i+j] - I[3*j+i]) > 1e-9 * (imax + 1.0))
                    throw std::runtime_error(where + ".inertia_com_local_kg_m2: must be symmetric");
            // positive principal moments + physical triangle inequality
            // (coupon check_inertia, :289-295)
            double ev[3];
            eigen_sym3(I.data(), ev);
            double lo = std::fmin(ev[0], std::fmin(ev[1], ev[2]));
            double hi = std::fmax(ev[0], std::fmax(ev[1], ev[2]));
            double mid = ev[0] + ev[1] + ev[2] - lo - hi;
            double slack = 1e-9 * std::fmax(std::fabs(ev[0]), std::fmax(std::fabs(ev[1]), std::fabs(ev[2])));
            if (!(lo > 0.0) || lo + mid < hi - slack)
                throw std::runtime_error(where + ".inertia_com_local_kg_m2: principal moments must be "
                                         "positive and satisfy the physical triangle inequality");
            for (int i = 0; i < 9; ++i) p.inertia_com_local[i] = I[i];

            JVal *vj = need(pj, "vertices_local_m", where);
            if (vj->t != JVal::ARR || vj->arr.size() < 12 || vj->arr.size() % 3 != 0)
                throw std::runtime_error(where + ".vertices_local_m: at least 4 vertices (3N numbers) expected");
            for (size_t i = 0; i < vj->arr.size(); ++i)
                p.verts.push_back(fnum(*vj->arr[i], where + ".vertices_local_m[" + std::to_string(i) + "]"));
            size_t nv = p.verts.size() / 3;

            JVal *tj = need(pj, "boundary_triangles", where);
            if (tj->t != JVal::ARR || tj->arr.size() < 12 || tj->arr.size() % 3 != 0)
                throw std::runtime_error(where + ".boundary_triangles: at least 4 triangles (3T indices) expected");
            for (size_t i = 0; i < tj->arr.size(); ++i) {
                double d = fnum(*tj->arr[i], where + ".boundary_triangles[" + std::to_string(i) + "]");
                if (d != std::floor(d) || d < 0 || d >= (double)nv)
                    throw std::runtime_error(where + ".boundary_triangles: index out of range");
                p.tris.push_back((int)d);
            }

            std::vector<double> pc = num_array(*need(pj, "pose_c_m", where), 3, where + ".pose_c_m");
            for (int i = 0; i < 3; ++i) p.c[i] = pc[i];

            std::vector<double> q = num_array(*need(pj, "pose_q_wxyz", where), 4, where + ".pose_q_wxyz");
            double qn = std::sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3]);
            if (qn < 0.999 || qn > 1.001)
                throw std::runtime_error(where + ".pose_q_wxyz: quaternion norm must be within [0.999, 1.001]");
            for (int i = 0; i < 4; ++i) q[i] /= qn;
            quat_to_mat3(q.data(), p.R);

            JVal *ground = need(pj, "ground", where);
            if (ground->t != JVal::OBJ) throw std::runtime_error(where + ".ground: object expected");
            req_keys(*ground, {"k_n_per_m","c_n_s_per_m"}, {}, where + ".ground");
            p.k_site = fnum(*need(*ground, "k_n_per_m", where + ".ground"), where + ".ground.k_n_per_m");
            p.c_site = fnum(*need(*ground, "c_n_s_per_m", where + ".ground"), where + ".ground.c_n_s_per_m");
            if (!(p.k_site > 0.0)) throw std::runtime_error(where + ".ground.k_n_per_m: must be positive");
            if (!(p.c_site >= 0.0)) throw std::runtime_error(where + ".ground.c_n_s_per_m: must be >= 0");
            built.push_back(std::move(p));
        }

        parts_ = std::move(built);
        gravity_ = gravity;
        reason_ = reason.empty() ? why : reason;
        active_ = true;
        diverged_ = false;
        steps_ = 0;
        e0_j_ = kinetic_j_() + potential_j_() + stored_penalty_j_();
        return std::string();
    } catch (const std::exception &e) {
        return std::string(e.what());
    }
}

void B2Scene::clear() {
    parts_.clear();
    active_ = false;
    diverged_ = false;
    steps_ = 0;
    e0_j_ = 0.0;
    reason_.clear();
}

// ─── one fixed substep: per-site one-sided ground rung + rigid integration ───
// Ported: coupon contact_forces (:754-771) — g = (P - plane_p)·n with plane
// y = 0, n = +y, so g = P.y; fn = -(k·g + c·ġ); active only when g < 0 &&
// fn > 0. Integration: coupon step (:854-862) — semi-implicit, world inertia
// R·I_local·Rᵀ, Euler term -ω×(Iw·ω), rotation by exp(h·[ω]x).
bool B2Scene::substep_(double h) {
    for (auto &p : parts_) {
        double F[3] = {0.0, -p.mass * gravity_, 0.0};
        double tau[3] = {0.0, 0.0, 0.0};
        double reac = 0.0, pen = 0.0;
        int nact = 0;
        size_t nv = p.verts.size() / 3;
        for (size_t vi = 0; vi < nv; ++vi) {
            double pl[3] = {p.verts[3*vi] - p.com_local[0],
                            p.verts[3*vi+1] - p.com_local[1],
                            p.verts[3*vi+2] - p.com_local[2]};
            double r[3]; mat3_v(p.R, pl, r);
            double P[3] = {p.c[0]+r[0], p.c[1]+r[1], p.c[2]+r[2]};
            double cr[3]; cross3(p.omega, r, cr);
            double vsy = p.v[1] + cr[1];
            double fn = -(p.k_site * P[1] + p.c_site * vsy);
            if (P[1] < 0.0 && fn > 0.0) {
                F[1] += fn;
                tau[0] += -r[2] * fn;          // (r × (0,fn,0))_x = -r_z·fn
                tau[2] += r[0] * fn;           // (r × (0,fn,0))_z =  r_x·fn
                reac += fn;
                if (-P[1] > pen) pen = -P[1];
                ++nact;
            }
        }
        p.reaction_n = reac;
        p.pen_step_m = pen;
        p.contacts_active = nact;
        if (pen > p.pen_run_m) p.pen_run_m = pen;

        // world inertia Iw = R · diag? no: full I_local — R·I_local·Rᵀ
        double RI[9];
        for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j)
            RI[3*i+j] = p.R[3*i]*p.inertia_com_local[j]
                      + p.R[3*i+1]*p.inertia_com_local[3+j]
                      + p.R[3*i+2]*p.inertia_com_local[6+j];
        double Iw[9];
        for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j)
            Iw[3*i+j] = RI[3*i]*p.R[3*j] + RI[3*i+1]*p.R[3*j+1] + RI[3*i+2]*p.R[3*j+2];
        double IwW[3]; mat3_v(Iw, p.omega, IwW);
        double cw[3]; cross3(p.omega, IwW, cw);
        double rhs[3] = {tau[0]-cw[0], tau[1]-cw[1], tau[2]-cw[2]};
        double dw[3];
        if (!solve3(Iw, rhs, dw)) return false;
        double omega_new[3] = {p.omega[0]+h*dw[0], p.omega[1]+h*dw[1], p.omega[2]+h*dw[2]};
        for (int k = 0; k < 3; ++k) p.v[k] += h * F[k] / p.mass;
        for (int k = 0; k < 3; ++k) p.c[k] += h * p.v[k];
        for (int k = 0; k < 3; ++k) p.omega[k] = omega_new[k];
        double dR[9]; rot_exp(p.omega, h, dR);
        double Rn[9]; mat3_mul(dR, p.R, Rn);
        for (int i = 0; i < 9; ++i) p.R[i] = Rn[i];
    }
    for (auto &p : parts_)
        for (int k = 0; k < 3; ++k)
            if (!std::isfinite(p.c[k]) || !std::isfinite(p.v[k]) || !std::isfinite(p.omega[k]))
                return false;
    return true;
}

bool B2Scene::step(double dt) {
    if (!active_ || diverged_) return !diverged_;
    double d = dt;
    if (d > 0.05) d = 0.05;          // the engine's own frame clamp
    if (d <= 0.0) return true;
    const double H = 1.0 / 4000.0;   // fixed substep
    int n = (int)std::ceil(d / H);
    for (int s = 0; s < n; ++s) {
        if (!substep_(H)) { diverged_ = true; return false; }
        ++steps_;
    }
    return true;
}

double B2Scene::kinetic_j_() const {
    double T = 0.0;
    for (auto &p : parts_) {
        double RI[9];
        for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j)
            RI[3*i+j] = p.R[3*i]*p.inertia_com_local[j]
                      + p.R[3*i+1]*p.inertia_com_local[3+j]
                      + p.R[3*i+2]*p.inertia_com_local[6+j];
        double Iw[9];
        for (int i = 0; i < 3; ++i) for (int j = 0; j < 3; ++j)
            Iw[3*i+j] = RI[3*i]*p.R[3*j] + RI[3*i+1]*p.R[3*j+1] + RI[3*i+2]*p.R[3*j+2];
        double IwW[3]; mat3_v(Iw, p.omega, IwW);
        T += 0.5 * p.mass * dot3(p.v, p.v) + 0.5 * dot3(p.omega, IwW);
    }
    return T;
}
double B2Scene::potential_j_() const {
    double U = 0.0;
    for (auto &p : parts_) U += p.mass * gravity_ * p.c[1];
    return U;
}
double B2Scene::stored_penalty_j_() const {
    double E = 0.0;
    for (auto &p : parts_) {
        size_t nv = p.verts.size() / 3;
        for (size_t vi = 0; vi < nv; ++vi) {
            double pl[3] = {p.verts[3*vi] - p.com_local[0],
                            p.verts[3*vi+1] - p.com_local[1],
                            p.verts[3*vi+2] - p.com_local[2]};
            double r[3]; mat3_v(p.R, pl, r);
            double y = p.c[1] + r[1];
            if (y < 0.0) E += 0.5 * p.k_site * y * y;
        }
    }
    return E;
}

std::string B2Scene::telemetry_json() const {
    std::string b = "{\"ok\":true,\"schema\":\"chimera.b2_scene.v1\",\"active\":";
    b += active_ ? "true" : "false";
    b += ",\"diverged\":"; b += diverged_ ? "true" : "false";
    b += ",\"steps\":" + std::to_string(steps_);
    b += ",\"dt_substep_s\":0.00025";
    b += ",\"gravity_m_s2\":" + fmt(gravity_);
    double wtot = 0.0, rtot = 0.0, pen = 0.0;
    for (auto &p : parts_) {
        wtot += p.mass * gravity_;
        rtot += p.reaction_n;
        pen = std::fmax(pen, p.pen_run_m);
    }
    double e = kinetic_j_() + potential_j_() + stored_penalty_j_();
    b += ",\"total_weight_n\":" + fmt(wtot);
    b += ",\"total_reaction_n\":" + fmt(rtot);
    b += ",\"max_penetration_m\":" + fmt(pen);
    b += ",\"energy_j\":" + fmt(e);
    b += ",\"energy_drift_j\":" + fmt(e - e0_j_);
    b += ",\"admission_reason\":\"" + json_escape(reason_) + "\"";
    b += ",\"parts\":[";
    for (size_t i = 0; i < parts_.size(); ++i) {
        const Part &p = parts_[i];
        if (i) b += ",";
        b += "{\"id\":\"" + json_escape(p.id) + "\"";
        b += ",\"mass_kg\":" + fmt(p.mass);
        b += ",\"weight_n\":" + fmt(p.mass * gravity_);
        b += ",\"reaction_n\":" + fmt(p.reaction_n);
        b += ",\"contacts_active\":" + std::to_string(p.contacts_active);
        b += ",\"pen_step_m\":" + fmt(p.pen_step_m);
        b += ",\"pen_run_m\":" + fmt(p.pen_run_m);
        b += ",\"com_m\":[" + fmt(p.c[0]) + "," + fmt(p.c[1]) + "," + fmt(p.c[2]) + "]";
        b += ",\"speed_m_s\":" + fmt(std::sqrt(dot3(p.v, p.v)));
        b += ",\"ground\":{\"k_n_per_m\":" + fmt(p.k_site) + ",\"c_n_s_per_m\":" + fmt(p.c_site) + "}}";
    }
    b += "]}";
    return b;
}

std::string B2Scene::parts_json() const {
    std::string b = "{\"ok\":true,\"schema\":\"chimera.b2_scene.v1\",\"parts\":[";
    for (size_t i = 0; i < parts_.size(); ++i) {
        const Part &p = parts_[i];
        if (i) b += ",";
        b += "{\"id\":\"" + json_escape(p.id) + "\"";
        b += ",\"mass_kg\":" + fmt(p.mass);
        b += ",\"weight_n\":" + fmt(p.mass * gravity_);
        b += ",\"com_local_m\":[" + fmt(p.com_local[0]) + "," + fmt(p.com_local[1]) + "," + fmt(p.com_local[2]) + "]";
        b += ",\"inertia_com_local_kg_m2\":[";
        for (int k = 0; k < 9; ++k) { if (k) b += ","; b += fmt(p.inertia_com_local[k]); }
        b += "]";
        b += ",\"n_vertices\":" + std::to_string(p.verts.size() / 3);
        b += ",\"n_triangles\":" + std::to_string(p.tris.size() / 3);
        b += ",\"pose_c_m\":[" + fmt(p.c[0]) + "," + fmt(p.c[1]) + "," + fmt(p.c[2]) + "]";
        double q[4]; mat3_to_quat(p.R, q);
        b += ",\"pose_q_wxyz\":[" + fmt(q[0]) + "," + fmt(q[1]) + "," + fmt(q[2]) + "," + fmt(q[3]) + "]}";
    }
    b += "]}";
    return b;
}
