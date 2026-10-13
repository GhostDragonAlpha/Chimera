// B2 scene implementation. See b2_scene.hpp for provenance: every physical
// formulation is ported from the accepted coupon model (native_coupon.cpp);
// this file adds only the resident-runtime plumbing around them.
#include "b2_scene.hpp"

#include <algorithm>
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
    if (!std::isfinite(x)) return "null";   // telemetry must stay valid JSON
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
// Named namespace OUTSIDE the anonymous one: B2Scene::parse_part_ takes a
// const b2j::JVal& forward-declared in the header at global scope, so the
// type must not be internal to this TU's anonymous namespace.
} // anonymous namespace (reopened below; same namespace within the TU)

namespace b2j {
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
} // namespace b2j
using namespace b2j;   // existing unqualified JVal/JParser uses resolve here

namespace {            // reopen the anonymous namespace for the helpers below

// ─── validation helpers (coupon req_keys/fnum precedent, :297-308) ──────────
JVal* need(const JVal &o, const char *key, const std::string &where) {
    for (auto &kv : o.obj) if (kv.first == key) return kv.second;
    throw std::runtime_error(where + ": missing required field '" + key + "'");
}
JVal* opt(const JVal &o, const char *key) {
    for (auto &kv : o.obj) if (kv.first == key) return kv.second;
    return nullptr;
}
void req_keys(const JVal &o, std::initializer_list<const char*> allowed,
              std::initializer_list<const char*> optional, const std::string &where) {
    for (auto &kv : o.obj) {
        bool ok = false;
        for (auto a : allowed) if (kv.first == a) ok = true;
        for (auto a : optional) if (kv.first == a) ok = true;
        if (!ok) throw std::runtime_error(where + ": unknown field '" + kv.first + "'");
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

// ─── one part element, validated and appended (admit / place / restore) ─────
// Shared verbatim by all three so a placed or restored part is admitted by
// exactly the same law as an admitted one. Optional dynamic fields
// (velocity_m_s, omega_rad_s, load_n, load_local_m, pose_R_rowmajor) carry
// the save/restore state; admission documents omit them (spawn at rest).
void B2Scene::parse_part_(const JVal &pj, const std::string &where,
                          std::vector<Part> &built) {
    if (pj.t != JVal::OBJ) throw std::runtime_error(where + ": object expected");
    req_keys(pj, {"id","mass_kg","com_local_m","inertia_com_local_kg_m2",
                  "vertices_local_m","boundary_triangles","pose_c_m","pose_q_wxyz",
                  "ground"},
             {"mu","velocity_m_s","omega_rad_s","load_n","load_local_m",
              "pose_R_rowmajor"}, where);
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
    // The save document carries the rotation matrix verbatim for an exact
    // round-trip (a quaternion printed at %.17g does not survive
    // quat->mat->quat bit-for-bit); when present it overrides the
    // quaternion, after being re-verified at this trust boundary.
    if (JVal *rj = opt(pj, "pose_R_rowmajor")) {
        std::vector<double> Rm = num_array(*rj, 9, where + ".pose_R_rowmajor");
        for (int i = 0; i < 3; ++i) {
            double L = Rm[3*i]*Rm[3*i] + Rm[3*i+1]*Rm[3*i+1] + Rm[3*i+2]*Rm[3*i+2];
            if (std::fabs(L - 1.0) > 1e-9)
                throw std::runtime_error(where + ".pose_R_rowmajor: rows must be unit length");
        }
        double n01[3]; cross3(Rm.data(), Rm.data() + 3, n01);
        double dot01 = n01[0]*Rm[6] + n01[1]*Rm[7] + n01[2]*Rm[8];
        if (std::fabs(dot01 - 1.0) > 1e-9)
            throw std::runtime_error(where + ".pose_R_rowmajor: must be right-handed orthonormal");
        for (int i = 0; i < 9; ++i) p.R[i] = Rm[i];
    }

    JVal *ground = need(pj, "ground", where);
    if (ground->t != JVal::OBJ) throw std::runtime_error(where + ".ground: object expected");
    req_keys(*ground, {"k_n_per_m","c_n_s_per_m"}, {}, where + ".ground");
    p.k_site = fnum(*need(*ground, "k_n_per_m", where + ".ground"), where + ".ground.k_n_per_m");
    p.c_site = fnum(*need(*ground, "c_n_s_per_m", where + ".ground"), where + ".ground.c_n_s_per_m");
    if (!(p.k_site > 0.0)) throw std::runtime_error(where + ".ground.k_n_per_m: must be positive");
    if (!(p.c_site >= 0.0)) throw std::runtime_error(where + ".ground.c_n_s_per_m: must be >= 0");
    if (JVal *mj = opt(pj, "mu")) {            // optional friction ratio
        p.mu = fnum(*mj, where + ".mu");
        if (!(p.mu >= 0.0)) throw std::runtime_error(where + ".mu: must be >= 0");
    }
    // dynamic state (save/restore; absent -> spawn at rest, unloaded)
    if (JVal *v = opt(pj, "velocity_m_s")) {
        std::vector<double> a = num_array(*v, 3, where + ".velocity_m_s");
        for (int i = 0; i < 3; ++i) p.v[i] = a[i];
    }
    if (JVal *w = opt(pj, "omega_rad_s")) {
        std::vector<double> a = num_array(*w, 3, where + ".omega_rad_s");
        for (int i = 0; i < 3; ++i) p.omega[i] = a[i];
    }
    if (JVal *f = opt(pj, "load_n")) {
        std::vector<double> a = num_array(*f, 3, where + ".load_n");
        for (int i = 0; i < 3; ++i) p.load_F[i] = a[i];
    }
    if (JVal *l = opt(pj, "load_local_m")) {
        std::vector<double> a = num_array(*l, 3, where + ".load_local_m");
        for (int i = 0; i < 3; ++i) p.load_local[i] = a[i];
    }
    built.push_back(std::move(p));
}

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
        // B2 qualified exactly two; B3 stacks three dissimilar layers;
        // B4 assembles interactively (place/remove transactions), so the
        // admission document may carry the full cradle up to the scene cap.
        if (parts->arr.size() < 2 || parts->arr.size() > 6)
            throw std::runtime_error("scene.parts: B2/B3/B4 needs 2 to 6 parts, got " +
                                     std::to_string(parts->arr.size()));

        std::vector<Part> built;
        for (size_t pi = 0; pi < parts->arr.size(); ++pi)
            parse_part_(*parts->arr[pi],
                        "scene.parts[" + std::to_string(pi) + "]", built);

        parts_ = std::move(built);
        welds_.clear();
        gravity_ = gravity;
        gravity_on_ = true;
        support_on_ = true;
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
    welds_.clear();
    active_ = false;
    paused_ = false;
    diverged_ = false;
    steps_ = 0;
    e0_j_ = 0.0;
    reason_.clear();
    gravity_on_ = true;
    support_on_ = true;
}

// ─── controls (gate right column: off-center load, support/power removal) ────
// set_load applies a persistent force at a world point on one part; the
// point is captured in the part's local axes so the load rides the pose
// (a weight sitting on the part, not a thruster chasing it). Zero force
// removes the load. Routes serialise through b2_mtx_ (membrane_tick.cpp).
std::string B2Scene::set_load(const std::string &json) {
    try {
        if (!active_) return "scene not admitted";
        JParser jp{json.c_str(), {}, 0};
        JVal *root = jp.parse();
        if (root->t != JVal::OBJ) throw std::runtime_error("load document must be a json object");
        req_keys(*root, {"part","force_n","point_world"}, {}, "load");
        JVal *idj = need(*root, "part", "load");
        if (idj->t != JVal::STR) throw std::runtime_error("load.part: string expected");
        Part *p = nullptr;
        for (auto &q : parts_) if (q.id == idj->str) { p = &q; break; }
        if (!p) throw std::runtime_error("load.part: no such part '" + idj->str + "'");
        std::vector<double> F = num_array(*need(*root, "force_n", "load"), 3, "load.force_n");
        std::vector<double> pt = num_array(*need(*root, "point_world", "load"), 3, "load.point_world");
        double d[3] = {pt[0]-p->c[0], pt[1]-p->c[1], pt[2]-p->c[2]};
        for (int i = 0; i < 3; ++i)   // local = Rᵀ·d
            p->load_local[i] = d[0]*p->R[i] + d[1]*p->R[3+i] + d[2]*p->R[6+i];
        for (int k = 0; k < 3; ++k) p->load_F[k] = F[k];
        return std::string();
    } catch (const std::exception &e) {
        return std::string(e.what());
    }
}
std::string B2Scene::set_support(bool on) {
    if (!active_) return "scene not admitted";
    support_on_ = on;
    return std::string();
}
std::string B2Scene::set_gravity(bool on) {
    if (!active_) return "scene not admitted";
    gravity_on_ = on;
    return std::string();
}

// ─── finite-area connector (the gate's "one finite-area connector") ─────────
// Coupon Weld { av, al, w, k } ported to two rigid parts: anchor pairs
// captured in local axes (the weld rides the parts), weights 1/N, and a
// central spring pair per anchor -- exact Newton-3 in force and torque.
// >= 3 anchors: a finite AREA, not a pin (design note: strict sub-area of
// the interface; the caller places them there, the count enforces area).
std::string B2Scene::set_weld(const std::string &json) {
    try {
        if (!active_) return "scene not admitted";
        JParser jp{json.c_str(), {}, 0};
        JVal *root = jp.parse();
        if (root->t != JVal::OBJ) throw std::runtime_error("weld document must be a json object");
        req_keys(*root, {"a","b","k","c_damp","anchors_world"}, {}, "weld");
        JVal *aj = need(*root, "a", "weld"), *bj = need(*root, "b", "weld");
        if (aj->t != JVal::STR || bj->t != JVal::STR)
            throw std::runtime_error("weld.a/weld.b: strings expected");
        if (aj->str == bj->str) throw std::runtime_error("weld: a part cannot weld to itself");
        Part *pa = nullptr, *pb = nullptr;
        for (auto &q : parts_) {
            if (q.id == aj->str) pa = &q;
            if (q.id == bj->str) pb = &q;
        }
        if (!pa) throw std::runtime_error("weld.a: no such part '" + aj->str + "'");
        if (!pb) throw std::runtime_error("weld.b: no such part '" + bj->str + "'");
        double k = fnum(*need(*root, "k", "weld"), "weld.k");
        if (!(k > 0.0)) throw std::runtime_error("weld.k: must be positive");
        double c = 0.0;
        if (JVal *cj = opt(*root, "c_damp")) {
            c = fnum(*cj, "weld.c_damp");
            if (!(c >= 0.0)) throw std::runtime_error("weld.c_damp: must be >= 0");
        }
        JVal *az = need(*root, "anchors_world", "weld");
        if (az->t != JVal::ARR || az->arr.size() < 3)
            throw std::runtime_error("weld.anchors_world: >= 3 anchor pairs expected (finite area)");
        Weld wd;
        wd.a = (size_t)(pa - parts_.data());
        wd.b = (size_t)(pb - parts_.data());
        wd.k = k;
        wd.c = c;
        for (auto &e : az->arr) {
            std::vector<double> ap = num_array(*e, 6, "weld.anchors_world[]");
            for (int side = 0; side < 2; ++side) {
                Part &p = side ? *pb : *pa;
                std::vector<double> &dst = side ? wd.lb : wd.la;
                double d[3] = {ap[3*side+0]-p.c[0], ap[3*side+1]-p.c[1], ap[3*side+2]-p.c[2]};
                double loc[3];
                for (int i = 0; i < 3; ++i)   // local = com_local + Rᵀ·d
                    loc[i] = p.com_local[i] + d[0]*p.R[i] + d[1]*p.R[3+i] + d[2]*p.R[6+i];
                dst.insert(dst.end(), loc, loc + 3);
            }
            wd.w.push_back(1.0 / (double)az->arr.size());
        }
        // one connector per part pair: a re-set replaces it (the control is
        // the weld itself, not a pile of them)
        welds_.erase(std::remove_if(welds_.begin(), welds_.end(),
                                    [&](const Weld &x) {
                                        return (x.a == wd.a && x.b == wd.b) ||
                                               (x.a == wd.b && x.b == wd.a);
                                    }), welds_.end());
        welds_.push_back(std::move(wd));
        return std::string();
    } catch (const std::exception &e) {
        return std::string(e.what());
    }
}
std::string B2Scene::remove_weld(const std::string &json) {
    try {
        if (!active_) return "scene not admitted";
        JParser jp{json.c_str(), {}, 0};
        JVal *root = jp.parse();
        if (root->t != JVal::OBJ) throw std::runtime_error("weld document must be a json object");
        req_keys(*root, {"a","b"}, {}, "weld");
        JVal *aj = need(*root, "a", "weld"), *bj = need(*root, "b", "weld");
        if (aj->t != JVal::STR || bj->t != JVal::STR)
            throw std::runtime_error("weld.a/weld.b: strings expected");
        size_t ia = parts_.size(), ib = parts_.size();
        for (size_t i = 0; i < parts_.size(); ++i) {
            if (parts_[i].id == aj->str) ia = i;
            if (parts_[i].id == bj->str) ib = i;
        }
        if (ia == parts_.size()) throw std::runtime_error("weld.a: no such part '" + aj->str + "'");
        if (ib == parts_.size()) throw std::runtime_error("weld.b: no such part '" + bj->str + "'");
        size_t n0 = welds_.size();
        welds_.erase(std::remove_if(welds_.begin(), welds_.end(),
                                    [&](const Weld &x) {
                                        return (x.a == ia && x.b == ib) ||
                                               (x.a == ib && x.b == ia);
                                    }), welds_.end());
        if (welds_.size() == n0)
            throw std::runtime_error("no weld between '" + aj->str + "' and '" + bj->str + "'");
        return std::string();
    } catch (const std::exception &e) {
        return std::string(e.what());
    }
}

// ─── B4: interactive assembly transactions (GAME_PLAN §13 B4) ───────────────
// The gate: "place, connect, test, release, mechanically patch, save and
// reload admitted parts through transactions". Every edit validates its
// document fully BEFORE mutating, so a rejected edit provably leaves the
// scene bit-identical (state_hash over the canonical save document).

std::string B2Scene::set_pause(bool on) {
    if (!active_) return "scene not admitted";
    paused_ = on;
    return std::string();
}

// place: add one part through the SAME parse law as admission
// (B2Scene::parse_part_), into a copy of the part list. The scene cap of
// 6 is enforced here as well as in admit.
std::string B2Scene::place(const std::string &json) {
    try {
        if (!active_) return "scene not admitted";
        if (parts_.size() >= 6) return "place: scene already holds the cap of 6 parts";
        JParser jp{json.c_str(), {}, 0};
        JVal *root = jp.parse();
        std::vector<Part> built = parts_;              // transaction: edit a copy
        parse_part_(*root, "place", built);            // throws -> parts_ untouched
        parts_ = std::move(built);
        // the energy baseline restarts at the new configuration (the drift
        // instrument measures evolution AFTER each structural edit)
        e0_j_ = kinetic_j_() + potential_j_() + stored_penalty_j_();
        return std::string();
    } catch (const std::exception &e) {
        return std::string(e.what());
    }
}

// remove_part: release one part by id. Its persistent load dies with it
// (loads live on the Part), and every weld touching it is dropped with the
// survivors' indices remapped -- no stale selections can point at a part
// that is gone. Refuses to empty the scene (that is clear()).
std::string B2Scene::remove_part(const std::string &json) {
    try {
        if (!active_) return "scene not admitted";
        JParser jp{json.c_str(), {}, 0};
        JVal *root = jp.parse();
        if (root->t != JVal::OBJ) throw std::runtime_error("remove document must be a json object");
        req_keys(*root, {"id"}, {}, "remove");
        JVal *idj = need(*root, "id", "remove");
        if (idj->t != JVal::STR) throw std::runtime_error("remove.id: string expected");
        size_t idx = parts_.size();
        for (size_t i = 0; i < parts_.size(); ++i)
            if (parts_[i].id == idj->str) { idx = i; break; }
        if (idx == parts_.size())
            throw std::runtime_error("remove: no part with id '" + idj->str + "'");
        if (parts_.size() <= 1)
            throw std::runtime_error("remove: refusing to empty the scene (clear it instead)");
        std::vector<Weld> keep;
        keep.reserve(welds_.size());
        for (auto &w : welds_) {
            if (w.a == idx || w.b == idx) continue;    // stale selection dies
            Weld n = std::move(w);
            if (n.a > idx) --n.a;
            if (n.b > idx) --n.b;
            keep.push_back(std::move(n));
        }
        welds_ = std::move(keep);
        parts_.erase(parts_.begin() + idx);
        e0_j_ = kinetic_j_() + potential_j_() + stored_penalty_j_();
        return std::string();
    } catch (const std::exception &e) {
        return std::string(e.what());
    }
}

// patch: the mechanical material patch. mu changes the Coulomb ratio;
// mass_kg rescales mass, inertia AND the ground-rung constants by the same
// ratio (k_total = m·g/s* and c_total = 2ζ√(k_total·m) are linear in m), so
// rest sink and damping ratio are preserved -- material changed, contact
// law did not. All values validated before any field mutates.
std::string B2Scene::patch(const std::string &json) {
    try {
        if (!active_) return "scene not admitted";
        JParser jp{json.c_str(), {}, 0};
        JVal *root = jp.parse();
        if (root->t != JVal::OBJ) throw std::runtime_error("patch document must be a json object");
        req_keys(*root, {"id"}, {"mu", "mass_kg"}, "patch");
        JVal *idj = need(*root, "id", "patch");
        if (idj->t != JVal::STR) throw std::runtime_error("patch.id: string expected");
        Part *p = nullptr;
        for (auto &q : parts_) if (q.id == idj->str) { p = &q; break; }
        if (!p) throw std::runtime_error("patch: no part with id '" + idj->str + "'");
        JVal *muj = opt(*root, "mu"), *mij = opt(*root, "mass_kg");
        if (!muj && !mij)
            throw std::runtime_error("patch: nothing to patch (give mu and/or mass_kg)");
        double mu = p->mu, mass = p->mass;
        if (muj) {
            mu = fnum(*muj, "patch.mu");
            if (!(mu >= 0.0)) throw std::runtime_error("patch.mu: must be >= 0");
        }
        if (mij) {
            mass = fnum(*mij, "patch.mass_kg");
            if (!(mass > 0.0)) throw std::runtime_error("patch.mass_kg: must be positive");
        }
        // validated -> apply
        p->mu = mu;
        if (mij) {
            double r = mass / p->mass;
            p->mass = mass;
            for (int i = 0; i < 9; ++i) p->inertia_com_local[i] *= r;
            p->k_site *= r;
            p->c_site *= r;
        }
        return std::string();
    } catch (const std::exception &e) {
        return std::string(e.what());
    }
}

// ─── save / restore: exact round-trip of the persistent state ────────────────
// Canonical document chimera.b2_state.v1. Every double prints %.17g (the
// shortest form that round-trips a double exactly) and each pose carries
// the rotation matrix verbatim beside its quaternion, so restore() rebuilds
// R bit-for-bit and state_hash() is stable across save -> restore -> save.
namespace {
std::string g17(double x) {
    char buf[64];
    std::snprintf(buf, sizeof buf, "%.17g", x);
    return buf;
}
std::string arr17(const double *a, size_t n) {
    std::string s = "[";
    for (size_t i = 0; i < n; ++i) { if (i) s += ","; s += g17(a[i]); }
    return s + "]";
}
std::string arr17v(const std::vector<double> &a) { return arr17(a.data(), a.size()); }
} // namespace

std::string B2Scene::save_doc_() const {
    std::string b = "{\"schema\":\"chimera.b2_state.v1\"";
    b += ",\"gravity_m_s2\":" + g17(gravity_);
    b += ",\"gravity_on\":" + std::string(gravity_on_ ? "true" : "false");
    b += ",\"support_on\":" + std::string(support_on_ ? "true" : "false");
    b += ",\"paused\":" + std::string(paused_ ? "true" : "false");
    b += ",\"steps\":" + std::to_string(steps_);
    b += ",\"energy0_j\":" + g17(e0_j_);
    b += ",\"reason\":\"" + json_escape(reason_) + "\"";
    b += ",\"parts\":[";
    for (size_t i = 0; i < parts_.size(); ++i) {
        const Part &p = parts_[i];
        if (i) b += ",";
        b += "{\"id\":\"" + json_escape(p.id) + "\"";
        b += ",\"mass_kg\":" + g17(p.mass);
        b += ",\"com_local_m\":" + arr17(p.com_local, 3);
        b += ",\"inertia_com_local_kg_m2\":" + arr17(p.inertia_com_local, 9);
        b += ",\"vertices_local_m\":" + arr17v(p.verts);
        b += ",\"boundary_triangles\":[";
        for (size_t t = 0; t < p.tris.size(); ++t) { if (t) b += ","; b += std::to_string(p.tris[t]); }
        b += "]";
        b += ",\"mu\":" + g17(p.mu);
        b += ",\"ground\":{\"k_n_per_m\":" + g17(p.k_site) + ",\"c_n_s_per_m\":" + g17(p.c_site) + "}";
        b += ",\"pose_c_m\":" + arr17(p.c, 3);
        double q[4]; mat3_to_quat(p.R, q);
        b += ",\"pose_q_wxyz\":" + arr17(q, 4);
        b += ",\"pose_R_rowmajor\":" + arr17(p.R, 9);
        b += ",\"velocity_m_s\":" + arr17(p.v, 3);
        b += ",\"omega_rad_s\":" + arr17(p.omega, 3);
        b += ",\"load_n\":" + arr17(p.load_F, 3);
        b += ",\"load_local_m\":" + arr17(p.load_local, 3) + "}";
    }
    b += "],\"welds\":[";
    for (size_t i = 0; i < welds_.size(); ++i) {
        const Weld &wd = welds_[i];
        if (i) b += ",";
        b += "{\"a\":\"" + json_escape(parts_[wd.a].id) +
             "\",\"b\":\"" + json_escape(parts_[wd.b].id) + "\"";
        b += ",\"k_n_per_m\":" + g17(wd.k);
        b += ",\"c_n_s_per_m\":" + g17(wd.c);
        b += ",\"weights\":" + arr17v(wd.w);
        b += ",\"anchors_local_a\":" + arr17v(wd.la);
        b += ",\"anchors_local_b\":" + arr17v(wd.lb) + "}";
    }
    b += "]}";
    return b;
}

std::string B2Scene::save_json() const { return save_doc_(); }

std::string B2Scene::state_hash() const {
    const std::string doc = save_doc_();
    uint64_t h = 1469598103934665603ULL;            // FNV-1a 64 basis
    for (unsigned char ch : doc) { h ^= ch; h *= 1099511628211ULL; }
    char buf[32];
    std::snprintf(buf, sizeof buf, "%016llx", (unsigned long long)h);
    return buf;
}

// restore: validate a chimera.b2_state.v1 document end-to-end (parts
// through the shared parse law, welds by id with the same invariants
// set_weld enforces) and swap it in atomically. A rejected document leaves
// the live scene untouched.
std::string B2Scene::restore(const std::string &json) {
    try {
        JParser jp{json.c_str(), {}, 0};
        JVal *root = jp.parse();
        if (root->t != JVal::OBJ) throw std::runtime_error("state document must be a json object");
        req_keys(*root, {"schema","gravity_m_s2","gravity_on","support_on","paused",
                         "steps","energy0_j","reason","parts","welds"}, {}, "state");
        JVal *schema = need(*root, "schema", "state");
        if (schema->t != JVal::STR || schema->str != "chimera.b2_state.v1")
            throw std::runtime_error("state: schema must be \"chimera.b2_state.v1\"");
        double gravity = fnum(*need(*root, "gravity_m_s2", "state"), "state.gravity_m_s2");
        if (gravity < 0.0) throw std::runtime_error("state.gravity_m_s2: must be >= 0");
        auto boolean = [&](const char *key) {
            JVal *v = need(*root, key, "state");
            if (v->t != JVal::BOOL) throw std::runtime_error(std::string("state.") + key + ": boolean expected");
            return v->bval;
        };
        bool g_on = boolean("gravity_on"), s_on = boolean("support_on"), paused = boolean("paused");
        double e0 = fnum(*need(*root, "energy0_j", "state"), "state.energy0_j");
        JVal *stepsj = need(*root, "steps", "state");
        if (stepsj->t != JVal::NUM || stepsj->num != std::floor(stepsj->num) || stepsj->num < 0)
            throw std::runtime_error("state.steps: non-negative integer expected");
        std::string reason;
        {
            JVal *rj = need(*root, "reason", "state");
            if (rj->t != JVal::STR) throw std::runtime_error("state.reason: string expected");
            reason = rj->str;
        }
        JVal *partsj = need(*root, "parts", "state");
        if (partsj->t != JVal::ARR || partsj->arr.size() < 1 || partsj->arr.size() > 6)
            throw std::runtime_error("state.parts: 1 to 6 parts expected, got " +
                                     std::to_string(partsj->arr.size()));
        std::vector<Part> built;
        for (size_t i = 0; i < partsj->arr.size(); ++i)
            parse_part_(*partsj->arr[i], "state.parts[" + std::to_string(i) + "]", built);

        std::vector<Weld> welds;
        JVal *weldsj = need(*root, "welds", "state");
        if (weldsj->t != JVal::ARR) throw std::runtime_error("state.welds: array expected");
        for (size_t i = 0; i < weldsj->arr.size(); ++i) {
            std::string where = "state.welds[" + std::to_string(i) + "]";
            const JVal &wj = *weldsj->arr[i];
            if (wj.t != JVal::OBJ) throw std::runtime_error(where + ": object expected");
            req_keys(wj, {"a","b","k_n_per_m","c_n_s_per_m","weights",
                          "anchors_local_a","anchors_local_b"}, {}, where);
            JVal *aj = need(wj, "a", where), *bj = need(wj, "b", where);
            if (aj->t != JVal::STR || bj->t != JVal::STR)
                throw std::runtime_error(where + ".a/.b: strings expected");
            if (aj->str == bj->str) throw std::runtime_error(where + ": a part cannot weld to itself");
            size_t ia = built.size(), ib = built.size();
            for (size_t k = 0; k < built.size(); ++k) {
                if (built[k].id == aj->str) ia = k;
                if (built[k].id == bj->str) ib = k;
            }
            if (ia == built.size()) throw std::runtime_error(where + ".a: no such part '" + aj->str + "'");
            if (ib == built.size()) throw std::runtime_error(where + ".b: no such part '" + bj->str + "'");
            for (auto &x : welds)
                if ((x.a == ia && x.b == ib) || (x.a == ib && x.b == ia))
                    throw std::runtime_error(where + ": duplicate weld between '" + aj->str + "' and '" + bj->str + "'");
            Weld wd;
            wd.a = ia; wd.b = ib;
            wd.k = fnum(*need(wj, "k_n_per_m", where), where + ".k_n_per_m");
            if (!(wd.k > 0.0)) throw std::runtime_error(where + ".k_n_per_m: must be positive");
            wd.c = fnum(*need(wj, "c_n_s_per_m", where), where + ".c_n_s_per_m");
            if (!(wd.c >= 0.0)) throw std::runtime_error(where + ".c_n_s_per_m: must be >= 0");
            // weights are variable-length -> read manually (num_array
            // demands an exact length; same strictness: finite numbers only)
            {
                const JVal &wv = *need(wj, "weights", where);
                if (wv.t != JVal::ARR || wv.arr.size() < 3)
                    throw std::runtime_error(where + ".weights: >= 3 anchors expected (finite area)");
                wd.w.clear();
                double sum = 0.0;
                for (size_t k = 0; k < wv.arr.size(); ++k) {
                    double x = fnum(*wv.arr[k], where + ".weights[" + std::to_string(k) + "]");
                    if (!(x > 0.0)) throw std::runtime_error(where + ".weights: each weight must be positive");
                    wd.w.push_back(x); sum += x;
                }
                if (std::fabs(sum - 1.0) > 1e-6)
                    throw std::runtime_error(where + ".weights: must sum to 1");
                wd.la = num_array(*need(wj, "anchors_local_a", where), 3 * wd.w.size(),
                                  where + ".anchors_local_a");
                wd.lb = num_array(*need(wj, "anchors_local_b", where), 3 * wd.w.size(),
                                  where + ".anchors_local_b");
            }
            welds.push_back(std::move(wd));
        }

        // validated end-to-end -> swap atomically
        parts_ = std::move(built);
        welds_ = std::move(welds);
        gravity_ = gravity;
        gravity_on_ = g_on;
        support_on_ = s_on;
        paused_ = paused;
        steps_ = (long)stepsj->num;
        e0_j_ = e0;
        reason_ = reason;
        active_ = true;
        diverged_ = false;
        return std::string();
    } catch (const std::exception &e) {
        return std::string(e.what());
    }
}

void B2Scene::world_vert_(const Part &p, size_t vi, double out[3]) {
    double pl[3] = {p.verts[3*vi] - p.com_local[0],
                    p.verts[3*vi+1] - p.com_local[1],
                    p.verts[3*vi+2] - p.com_local[2]};
    double r[3]; mat3_v(p.R, pl, r);
    out[0] = p.c[0] + r[0]; out[1] = p.c[1] + r[1]; out[2] = p.c[2] + r[2];
}
void B2Scene::world_point_(const Part &p, const double local[3], double out[3]) {
    double pl[3] = {local[0] - p.com_local[0],
                    local[1] - p.com_local[1],
                    local[2] - p.com_local[2]};
    double r[3]; mat3_v(p.R, pl, r);
    out[0] = p.c[0] + r[0]; out[1] = p.c[1] + r[1]; out[2] = p.c[2] + r[2];
}

// ─── loose contact between two parts (B2 gate: "loose contact") ─────────────
// Same one-sided rung law as the ground (coupon contact_forces :754-771):
// g = (P − A)·n with n the OUTWARD face normal of the penetrated part;
// fn = −(k·g + c·ġ), active only when g < 0 && fn > 0. A vertex counts as
// contacting a triangle only while its projection stays inside the triangle
// (edges/vertices of the mesh are not modelled — the wedge faces are large
// compared with the substep displacement, and the acceptance scenarios load
// faces onto faces). Pair constants: mean of the two parts' rung constants
// and friction ratios. Force pairs are exact Newton-3 (equal, opposite,
// same line of action through the contact point).
void B2Scene::pp_pair_(Part &a, Part &b,
                       double *Fa, double *Ta, double *Fb, double *Tb) const {
    const double k_pp = 0.5 * (a.k_site + b.k_site);
    const double c_pp = 0.5 * (a.c_site + b.c_site);
    const double mu_pp = 0.5 * (a.mu + b.mu);
    // direction 0: a's vertices against b's faces; direction 1: mirrored.
    for (int dir = 0; dir < 2; ++dir) {
        Part &o = dir ? b : a;   // vertex owner
        Part &s = dir ? a : b;   // surface owner
        double *Fo = dir ? Fb : Fa, *To = dir ? Tb : Ta;
        double *Fs = dir ? Fa : Fb, *Ts = dir ? Ta : Tb;
        size_t nt = s.tris.size() / 3, nv = o.verts.size() / 3;
        // A convex surface is the intersection of its face half-spaces, so
        // a vertex that has entered the volume through one face is behind
        // EVERY face plane it lies inside of. Firing all of them would add
        // the side faces' 30 mm "penetrations" to a 0.5 mm stack contact and
        // eject the upper part sideways. The vertex contacts the face it
        // entered through: the shallowest (max g) candidate face.
        for (size_t vi = 0; vi < nv; ++vi) {
            double P[3]; world_vert_(o, vi, P);
            bool have = false;
            double bg = 0.0, bn[3] = {0,0,0}, bq[3] = {0,0,0};
            for (size_t ti = 0; ti < nt; ++ti) {
                double w0[3], w1[3], w2[3];
                world_vert_(s, s.tris[3*ti], w0);
                world_vert_(s, s.tris[3*ti+1], w1);
                world_vert_(s, s.tris[3*ti+2], w2);
                double e1[3] = {w1[0]-w0[0], w1[1]-w0[1], w1[2]-w0[2]};
                double e2[3] = {w2[0]-w0[0], w2[1]-w0[1], w2[2]-w0[2]};
                double n[3]; cross3(e1, e2, n);
                double nl = std::sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2]);
                if (nl < 1e-12) continue;
                for (int k = 0; k < 3; ++k) n[k] /= nl;
                // convex part: outward normal points away from the COM
                double dc[3] = {(w0[0]+w1[0]+w2[0])/3.0 - s.c[0],
                                (w0[1]+w1[1]+w2[1])/3.0 - s.c[1],
                                (w0[2]+w1[2]+w2[2])/3.0 - s.c[2]};
                if (n[0]*dc[0] + n[1]*dc[1] + n[2]*dc[2] < 0.0)
                    for (int k = 0; k < 3; ++k) n[k] = -n[k];
                double d0[3] = {P[0]-w0[0], P[1]-w0[1], P[2]-w0[2]};
                double g = d0[0]*n[0] + d0[1]*n[1] + d0[2]*n[2];
                if (g >= 0.0) continue;
                // Contact radius: a vertex deeper than 5 cm behind a face
                // plane is a miss, not a weld. The acceptance scenarios load
                // faces onto faces with mm-scale penetration, while wedges
                // sharing the ground/back planes put far vertices' plane
                // projections exactly on triangle edges -- float noise there
                // otherwise "contacts" parts 0.8 m apart. 5 cm is an order
                // below the smallest wedge feature (9 cm).
                if (g < -0.05) continue;
                // containment: projected point STRICTLY inside the triangle.
                // Boundary points must be rejected: two wedges standing on
                // the same plane share coplanar faces, and a separated
                // vertex's projection can land exactly on a far triangle's
                // vertex/edge -- accepting it would weld the parts together
                // from 0.6 m away. Mesh edges/vertices are not contacts.
                double q[3] = {P[0]-g*n[0], P[1]-g*n[1], P[2]-g*n[2]};
                bool inside = true;
                const double *wv[3] = {w0, w1, w2};   // NOT w0+3*e: w0 is a
                // 3-element array; walking it off the end reads stack garbage
                for (int e = 0; e < 3 && inside; ++e) {
                    const double *va = wv[e], *vb = wv[(e+1)%3];
                    double ee[3] = {vb[0]-va[0], vb[1]-va[1], vb[2]-va[2]};
                    double qq[3] = {q[0]-va[0], q[1]-va[1], q[2]-va[2]};
                    double cc[3]; cross3(ee, qq, cc);
                    if (cc[0]*n[0] + cc[1]*n[1] + cc[2]*n[2] <= 0.0) inside = false;
                }
                if (!inside) continue;
                if (!have || g > bg) {
                    have = true; bg = g;
                    for (int k = 0; k < 3; ++k) { bn[k] = n[k]; bq[k] = q[k]; }
                }
            }
            if (!have) continue;
            const double *n = bn;
            const double *q = bq;
            double g = bg;
            // relative velocity at the contact (o's vertex vs s's face)
            double ra[3] = {P[0]-o.c[0], P[1]-o.c[1], P[2]-o.c[2]};
            double rb[3] = {q[0]-s.c[0], q[1]-s.c[1], q[2]-s.c[2]};
            double cra[3], crb[3];
            cross3(o.omega, ra, cra); cross3(s.omega, rb, crb);
            double rel[3] = {o.v[0]+cra[0]-s.v[0]-crb[0],
                             o.v[1]+cra[1]-s.v[1]-crb[1],
                             o.v[2]+cra[2]-s.v[2]-crb[2]};
            double gn = rel[0]*n[0] + rel[1]*n[1] + rel[2]*n[2];
            double fn = -(k_pp * g + c_pp * gn);
            if (fn <= 0.0) continue;
            // normal pair: the vertex owner penetrates the surface, so
            // +fn·n goes on o at its vertex, −fn·n on s at the contact.
            double f[3] = {fn*n[0], fn*n[1], fn*n[2]};
            for (int k = 0; k < 3; ++k) { Fo[k] += f[k]; Fs[k] -= f[k]; }
            double t1[3];
            cross3(ra, f, t1);
            for (int k = 0; k < 3; ++k) { To[k] += t1[k]; Ts[k] -= t1[k]; }
            // friction on the surface owner acts along -rel_t; the pair
            // on o is its opposite. Regularised Coulomb: full μ·fn when
            // sliding, linearly damped inside |v_t| < 1 mm/s (sticking).
            if (mu_pp > 0.0) {
                double vt[3] = {rel[0]-gn*n[0], rel[1]-gn*n[1], rel[2]-gn*n[2]};
                double sp = std::sqrt(vt[0]*vt[0] + vt[1]*vt[1] + vt[2]*vt[2]);
                if (sp > 1e-12) {
                    double sc = -mu_pp * fn / std::max(sp, 1e-3);
                    double ff[3] = {sc*vt[0], sc*vt[1], sc*vt[2]};
                    for (int k = 0; k < 3; ++k) { Fo[k] += ff[k]; Fs[k] -= ff[k]; }
                    double u1[3];
                    cross3(ra, ff, u1);
                    for (int k = 0; k < 3; ++k) { To[k] += u1[k]; Ts[k] -= u1[k]; }
                }
            }
            o.contact_pp_n += fn; ++o.contacts_pp_active;
            s.contact_pp_n += fn; ++s.contacts_pp_active;
            double pen = -g;
            if (pen > o.pen_step_m) o.pen_step_m = pen;
            if (pen > s.pen_step_m) s.pen_step_m = pen;
            if (pen > o.pen_pp_run_m) o.pen_pp_run_m = pen;
            if (pen > s.pen_pp_run_m) s.pen_pp_run_m = pen;
        }
    }
}

// ─── one fixed substep: forces (ground rung, load, loose contact) then ──────
// rigid integration of every part. Ported: coupon contact_forces (:754-771) —
// g = (P - plane_p)·n with plane y = 0, n = +y, so g = P.y; fn = -(k·g + c·ġ);
// active only when g < 0 && fn > 0. Integration: coupon step (:854-862) —
// semi-implicit, world inertia R·I_local·Rᵀ, Euler term -ω×(Iw·ω), rotation
// by exp(h·[ω]x). Forces are accumulated for ALL parts before ANY part is
// integrated, so the Newton-3 contact pairs act on one consistent state.
bool B2Scene::substep_(double h) {
    const size_t np = parts_.size();
    std::vector<double> F(3*np, 0.0), T(3*np, 0.0);
    for (size_t pi = 0; pi < np; ++pi) {
        Part &p = parts_[pi];
        p.reaction_n = 0.0; p.pen_step_m = 0.0; p.contacts_active = 0;
        p.contact_pp_n = 0.0; p.contacts_pp_active = 0;
        if (gravity_on_) F[3*pi+1] -= p.mass * gravity_;
        // persistent external load (rides the part: arm captured in local axes)
        if (p.load_F[0] || p.load_F[1] || p.load_F[2]) {
            double rl[3]; mat3_v(p.R, p.load_local, rl);
            for (int k = 0; k < 3; ++k) F[3*pi+k] += p.load_F[k];
            double lt[3]; cross3(rl, p.load_F, lt);
            for (int k = 0; k < 3; ++k) T[3*pi+k] += lt[k];
        }
        if (!support_on_) { p.ground_fn.assign(p.verts.size()/3, 0.0); continue; }
        size_t nv = p.verts.size() / 3;
        p.ground_fn.assign(nv, 0.0);
        for (size_t vi = 0; vi < nv; ++vi) {
            double P[3]; world_vert_(p, vi, P);
            double r[3] = {P[0]-p.c[0], P[1]-p.c[1], P[2]-p.c[2]};
            double cr[3]; cross3(p.omega, r, cr);
            double vsy = p.v[1] + cr[1];
            double fn = -(p.k_site * P[1] + p.c_site * vsy);
            if (P[1] < 0.0 && fn > 0.0) {
                F[3*pi+1] += fn;
                T[3*pi] += -r[2] * fn;           // (r × (0,fn,0))_x = -r_z·fn
                T[3*pi+2] += r[0] * fn;          // (r × (0,fn,0))_z =  r_x·fn
                p.reaction_n += fn;
                p.ground_fn[vi] = fn;
                if (-P[1] > p.pen_step_m) p.pen_step_m = -P[1];
                ++p.contacts_active;
                // ground friction (slide control on the plane): tangential
                // velocity is (vx, vz); regularised Coulomb as in pp_pair_.
                if (p.mu > 0.0) {
                    double vt[3] = {p.v[0]+cr[0], 0.0, p.v[2]+cr[2]};
                    double sp = std::sqrt(vt[0]*vt[0] + vt[2]*vt[2]);
                    if (sp > 1e-12) {
                        double sc = -p.mu * fn / std::max(sp, 1e-3);
                        F[3*pi] += sc*vt[0]; F[3*pi+2] += sc*vt[2];
                        double ft[3] = {sc*vt[0], 0.0, sc*vt[2]};
                        double tt[3]; cross3(r, ft, tt);
                        for (int k = 0; k < 3; ++k) T[3*pi+k] += tt[k];
                    }
                }
            }
        }
        if (p.pen_step_m > p.pen_run_m) p.pen_run_m = p.pen_step_m;
    }
    for (size_t i = 0; i < np; ++i)
        for (size_t j = i + 1; j < np; ++j)
            pp_pair_(parts_[i], parts_[j], &F[3*i], &T[3*i], &F[3*j], &T[3*j]);

    // finite-area connectors: central spring-damper pairs, exact Newton-3.
    // The dashpot is along the anchor line (the same penalty-damper law as
    // every rung in this scene); c = 0 is the coupon Weld port exactly.
    for (auto &wd : welds_) {
        Part &a = parts_[wd.a];
        Part &b = parts_[wd.b];
        double *Fa = &F[3*wd.a], *Ta = &T[3*wd.a];
        double *Fb = &F[3*wd.b], *Tb = &T[3*wd.b];
        double fsum[3] = {0.0, 0.0, 0.0};
        for (size_t j = 0; j < wd.w.size(); ++j) {
            double la[3] = {wd.la[3*j], wd.la[3*j+1], wd.la[3*j+2]};
            double lb[3] = {wd.lb[3*j], wd.lb[3*j+1], wd.lb[3*j+2]};
            double pa[3], pb[3];
            world_point_(a, la, pa);
            world_point_(b, lb, pb);
            double f[3];
            double dvec[3] = {pb[0]-pa[0], pb[1]-pa[1], pb[2]-pa[2]};
            double kk = wd.k;
            if (wd.c > 0.0) {
                double L = std::sqrt(dvec[0]*dvec[0] + dvec[1]*dvec[1] + dvec[2]*dvec[2]);
                if (L > 1e-12) {
                    double n[3] = {dvec[0]/L, dvec[1]/L, dvec[2]/L};
                    double ra0[3] = {pa[0]-a.c[0], pa[1]-a.c[1], pa[2]-a.c[2]};
                    double rb0[3] = {pb[0]-b.c[0], pb[1]-b.c[1], pb[2]-b.c[2]};
                    double va[3], vb[3], wa[3], wb[3];
                    cross3(a.omega, ra0, wa);
                    cross3(b.omega, rb0, wb);
                    for (int k = 0; k < 3; ++k) {
                        va[k] = a.v[k] + wa[k];
                        vb[k] = b.v[k] + wb[k];
                    }
                    double vn = (vb[0]-va[0])*n[0] + (vb[1]-va[1])*n[1] + (vb[2]-va[2])*n[2];
                    // f_on_a = w*(k*d + c*vn*n): power = -w*c*vn^2 <= 0
                    for (int k = 0; k < 3; ++k)
                        dvec[k] += (wd.c / wd.k) * vn * n[k];   // k*d + c*vn*n
                }
            }
            for (int k = 0; k < 3; ++k)
                f[k] = wd.w[j] * kk * dvec[k];
            double ra[3] = {pa[0]-a.c[0], pa[1]-a.c[1], pa[2]-a.c[2]};
            double rb[3] = {pb[0]-b.c[0], pb[1]-b.c[1], pb[2]-b.c[2]};
            for (int k = 0; k < 3; ++k) {
                Fa[k] += f[k]; Fb[k] -= f[k];
                fsum[k] += f[k];
            }
            double t1[3];
            cross3(ra, f, t1);
            for (int k = 0; k < 3; ++k) Ta[k] += t1[k];
            cross3(rb, f, t1);
            for (int k = 0; k < 3; ++k) Tb[k] -= t1[k];
        }
        wd.force_n = std::sqrt(fsum[0]*fsum[0] + fsum[1]*fsum[1] + fsum[2]*fsum[2]);
    }

    for (size_t pi = 0; pi < np; ++pi) {
        Part &p = parts_[pi];
        double *Fp = &F[3*pi], *Tp = &T[3*pi];
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
        double rhs[3] = {Tp[0]-cw[0], Tp[1]-cw[1], Tp[2]-cw[2]};
        double dw[3];
        if (!solve3(Iw, rhs, dw)) return false;
        double omega_new[3] = {p.omega[0]+h*dw[0], p.omega[1]+h*dw[1], p.omega[2]+h*dw[2]};
        for (int k = 0; k < 3; ++k) p.v[k] += h * Fp[k] / p.mass;
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
    if (!active_ || paused_ || diverged_) return !diverged_;
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
    for (auto &wd : welds_) {          // connector elastic energy
        for (size_t j = 0; j < wd.w.size(); ++j) {
            double la[3] = {wd.la[3*j], wd.la[3*j+1], wd.la[3*j+2]};
            double lb[3] = {wd.lb[3*j], wd.lb[3*j+1], wd.lb[3*j+2]};
            double pa[3], pb[3];
            world_point_(parts_[wd.a], la, pa);
            world_point_(parts_[wd.b], lb, pb);
            double d2 = 0.0;
            for (int k = 0; k < 3; ++k) { double d = pb[k]-pa[k]; d2 += d*d; }
            E += wd.w[j] * 0.5 * wd.k * d2;
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
    b += ",\"gravity_on\":"; b += gravity_on_ ? "true" : "false";
    b += ",\"support_on\":"; b += support_on_ ? "true" : "false";
    b += ",\"paused\":"; b += paused_ ? "true" : "false";
    b += ",\"state_hash\":\"" + state_hash() + "\"";   // B4: transaction proof
    double wtot = 0.0, rtot = 0.0, pen = 0.0;
    const double g_eff = gravity_on_ ? gravity_ : 0.0;   // the power switch is real
    for (auto &p : parts_) {
        wtot += p.mass * g_eff;
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
    b += ",\"welds\":[";
    for (size_t i = 0; i < welds_.size(); ++i) {
        if (i) b += ",";
        b += "{\"a\":\"" + json_escape(parts_[welds_[i].a].id) +
             "\",\"b\":\"" + json_escape(parts_[welds_[i].b].id) +
             "\",\"n_anchors\":" + std::to_string(welds_[i].w.size()) +
             ",\"k_n_per_m\":" + fmt(welds_[i].k) +
             ",\"c_n_s_per_m\":" + fmt(welds_[i].c) +
             ",\"force_n\":" + fmt(welds_[i].force_n) + "}";
    }
    b += "]";
    b += ",\"parts\":[";
    for (size_t i = 0; i < parts_.size(); ++i) {
        const Part &p = parts_[i];
        if (i) b += ",";
        b += "{\"id\":\"" + json_escape(p.id) + "\"";
        b += ",\"mass_kg\":" + fmt(p.mass);
        b += ",\"weight_n\":" + fmt(p.mass * g_eff);
        b += ",\"reaction_n\":" + fmt(p.reaction_n);
        b += ",\"contacts_active\":" + std::to_string(p.contacts_active);
        b += ",\"pen_step_m\":" + fmt(p.pen_step_m);
        b += ",\"pen_run_m\":" + fmt(p.pen_run_m);
        b += ",\"contact_pp_n\":" + fmt(p.contact_pp_n);
        b += ",\"contacts_pp_active\":" + std::to_string(p.contacts_pp_active);
        b += ",\"pen_pp_run_m\":" + fmt(p.pen_pp_run_m);
        b += ",\"mu\":" + fmt(p.mu);
        b += ",\"load_n\":[" + fmt(p.load_F[0]) + "," + fmt(p.load_F[1]) + "," + fmt(p.load_F[2]) + "]";
        b += ",\"site_reactions_n\":[";
        for (size_t s = 0; s < p.ground_fn.size(); ++s) {
            if (s) b += ",";
            b += fmt(p.ground_fn[s]);
        }
        b += "]";
        b += ",\"com_m\":[" + fmt(p.c[0]) + "," + fmt(p.c[1]) + "," + fmt(p.c[2]) + "]";
        b += ",\"speed_m_s\":" + fmt(std::sqrt(dot3(p.v, p.v)));
        double q[4]; mat3_to_quat(p.R, q);
        b += ",\"pose_q_wxyz\":[" + fmt(q[0]) + "," + fmt(q[1]) + "," + fmt(q[2]) + "," + fmt(q[3]) + "]";
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
        b += ",\"mu\":" + fmt(p.mu);
        b += ",\"n_vertices\":" + std::to_string(p.verts.size() / 3);
        b += ",\"n_triangles\":" + std::to_string(p.tris.size() / 3);
        b += ",\"pose_c_m\":[" + fmt(p.c[0]) + "," + fmt(p.c[1]) + "," + fmt(p.c[2]) + "]";
        double q[4]; mat3_to_quat(p.R, q);
        b += ",\"pose_q_wxyz\":[" + fmt(q[0]) + "," + fmt(q[1]) + "," + fmt(q[2]) + "," + fmt(q[3]) + "]}";
    }
    b += "]}";
    return b;
}

// Stable-ID inspection (B3 gate "inspection by stable IDs"): the full
// record of one part — admitted identity (mass, COM, inertia, material
// mu, ground rung) plus live state (pose, speed, reactions, penetrations,
// load). Unknown ids are refused by name; the live scene is untouched.
std::string B2Scene::inspect(const std::string &json, std::string &why) const {
    std::string id;
    try {
        if (!active_) { why = "scene not admitted"; return std::string(); }
        JParser jp{json.c_str(), {}, 0};
        JVal *root = jp.parse();
        if (root->t != JVal::OBJ) { why = "inspect document must be a json object"; return std::string(); }
        req_keys(*root, {"id"}, {}, "inspect");
        JVal *ij = need(*root, "id", "inspect");
        if (ij->t != JVal::STR) { why = "inspect.id: string expected"; return std::string(); }
        id = ij->str;
    } catch (const std::exception &e) { why = e.what(); return std::string(); }
    for (const auto &p : parts_) {
        if (p.id != id) continue;
        std::string b = "{\"ok\":true,\"schema\":\"chimera.b2_scene.v1\",\"part\":{";
        b += "\"id\":\"" + json_escape(p.id) + "\"";
        b += ",\"mass_kg\":" + fmt(p.mass);
        b += ",\"weight_n\":" + fmt(p.mass * (gravity_on_ ? gravity_ : 0.0));
        b += ",\"mu\":" + fmt(p.mu);
        b += ",\"com_local_m\":[" + fmt(p.com_local[0]) + "," + fmt(p.com_local[1]) + "," + fmt(p.com_local[2]) + "]";
        b += ",\"inertia_com_local_kg_m2\":[";
        for (int k = 0; k < 9; ++k) { if (k) b += ","; b += fmt(p.inertia_com_local[k]); }
        b += "]";
        b += ",\"ground\":{\"k_n_per_m\":" + fmt(p.k_site) + ",\"c_n_s_per_m\":" + fmt(p.c_site) + "}";
        b += ",\"n_vertices\":" + std::to_string(p.verts.size() / 3);
        b += ",\"n_triangles\":" + std::to_string(p.tris.size() / 3);
        b += ",\"pose_c_m\":[" + fmt(p.c[0]) + "," + fmt(p.c[1]) + "," + fmt(p.c[2]) + "]";
        double q[4]; mat3_to_quat(p.R, q);
        b += ",\"pose_q_wxyz\":[" + fmt(q[0]) + "," + fmt(q[1]) + "," + fmt(q[2]) + "," + fmt(q[3]) + "]";
        b += ",\"speed_m_s\":" + fmt(std::sqrt(p.v[0]*p.v[0] + p.v[1]*p.v[1] + p.v[2]*p.v[2]));
        b += ",\"reaction_n\":" + fmt(p.reaction_n);
        b += ",\"contacts_active\":" + std::to_string(p.contacts_active);
        b += ",\"contact_pp_n\":" + fmt(p.contact_pp_n);
        b += ",\"contacts_pp_active\":" + std::to_string(p.contacts_pp_active);
        b += ",\"pen_run_m\":" + fmt(p.pen_run_m);
        b += ",\"pen_pp_run_m\":" + fmt(p.pen_pp_run_m);
        b += ",\"load_n\":[" + fmt(p.load_F[0]) + "," + fmt(p.load_F[1]) + "," + fmt(p.load_F[2]) + "]}}";
        return b;
    }
    why = "inspect: no part with id '" + id + "'";
    return std::string();
}

// Fixed palette by admission order: a frame capture names a layer by color,
// and the pick route names it by ID, so the two can be cross-checked.
// Slot 3 (yellow) names a B4 PLACED part against the three stack layers.
static const double kLayerRgb[4][3] = {
    {0.85, 0.25, 0.25},   // layer 0 (base)
    {0.25, 0.75, 0.30},   // layer 1 (middle)
    {0.30, 0.45, 0.90},   // layer 2 (top)
    {0.85, 0.75, 0.20},   // layer 3 (placed part)
};

void B2Scene::render_mesh(std::vector<float> &verts9,
                          std::vector<uint32_t> &tris) const {
    verts9.clear(); tris.clear();
    if (!active_) return;
    for (size_t pi = 0; pi < parts_.size(); ++pi) {
        const Part &p = parts_[pi];
        const double *rgb = kLayerRgb[pi % 4];
        const uint32_t base = (uint32_t)(verts9.size() / 9);
        for (size_t ti = 0; ti + 2 < p.tris.size(); ti += 3) {
            double w[3][3];
            for (int k = 0; k < 3; ++k)
                world_vert_(p, (size_t)p.tris[ti + k], w[k]);
            double e1[3] = {w[1][0]-w[0][0], w[1][1]-w[0][1], w[1][2]-w[0][2]};
            double e2[3] = {w[2][0]-w[0][0], w[2][1]-w[0][1], w[2][2]-w[0][2]};
            double n[3]; cross3(e1, e2, n);
            double nl = std::sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2]);
            if (nl < 1e-12) continue;
            // outward, exactly as the contact solver derives it
            double dc[3] = {(w[0][0]+w[1][0]+w[2][0])/3.0 - p.c[0],
                            (w[0][1]+w[1][1]+w[2][1])/3.0 - p.c[1],
                            (w[0][2]+w[1][2]+w[2][2])/3.0 - p.c[2]};
            if (n[0]*dc[0] + n[1]*dc[1] + n[2]*dc[2] < 0.0)
                for (int k = 0; k < 3; ++k) n[k] = -n[k];
            for (int k = 0; k < 3; ++k) n[k] /= nl;
            for (int k = 0; k < 3; ++k) {
                for (int a = 0; a < 3; ++a) verts9.push_back((float)w[k][a]);
                for (int a = 0; a < 3; ++a) verts9.push_back((float)n[a]);
                for (int a = 0; a < 3; ++a) verts9.push_back((float)rgb[a]);
                tris.push_back(base + (uint32_t)ti + (uint32_t)k);
            }
        }
    }
}

bool B2Scene::pick(const float eye[3], const float dir[3],
                   std::string &id_out, float point_out[3]) const {
    if (!active_) return false;
    float best_t = 1e30f;
    bool hit = false;
    for (const auto &p : parts_) {
        for (size_t ti = 0; ti + 2 < p.tris.size(); ti += 3) {
            double w[3][3];
            for (int k = 0; k < 3; ++k)
                world_vert_(p, (size_t)p.tris[ti + k], w[k]);
            float a[3] = {(float)w[0][0], (float)w[0][1], (float)w[0][2]};
            float b[3] = {(float)w[1][0], (float)w[1][1], (float)w[1][2]};
            float cc[3] = {(float)w[2][0], (float)w[2][1], (float)w[2][2]};
            float e1[3] = {b[0]-a[0], b[1]-a[1], b[2]-a[2]};
            float e2[3] = {cc[0]-a[0], cc[1]-a[1], cc[2]-a[2]};
            float pv[3] = {dir[1]*e2[2]-dir[2]*e2[1], dir[2]*e2[0]-dir[0]*e2[2],
                           dir[0]*e2[1]-dir[1]*e2[0]};
            float det = e1[0]*pv[0] + e1[1]*pv[1] + e1[2]*pv[2];
            if (det > -1e-10f && det < 1e-10f) continue;
            float inv = 1.f / det;
            float tv[3] = {eye[0]-a[0], eye[1]-a[1], eye[2]-a[2]};
            float uu = (tv[0]*pv[0] + tv[1]*pv[1] + tv[2]*pv[2]) * inv;
            if (uu < -1e-6f || uu > 1.f + 1e-6f) continue;
            float qv[3] = {tv[1]*e1[2]-tv[2]*e1[1], tv[2]*e1[0]-tv[0]*e1[2],
                           tv[0]*e1[1]-tv[1]*e1[0]};
            float vv = (dir[0]*qv[0] + dir[1]*qv[1] + dir[2]*qv[2]) * inv;
            if (vv < -1e-6f || uu + vv > 1.f + 1e-6f) continue;
            float t = (e2[0]*qv[0] + e2[1]*qv[1] + e2[2]*qv[2]) * inv;
            if (t <= 0.f || t >= best_t) continue;
            best_t = t; hit = true;
            id_out = p.id;
            for (int k = 0; k < 3; ++k) point_out[k] = eye[k] + t * dir[k];
        }
    }
    return hit;
}
