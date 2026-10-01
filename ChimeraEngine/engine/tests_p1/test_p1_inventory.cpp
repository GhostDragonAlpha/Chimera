#include "../membrane_tick.hpp"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace {

struct Jv {
    enum Kind { NUL, BOOL, NUM, STR, ARR, OBJ };
    Kind kind = NUL;
    double num = 0.0;
    bool b = false;
    std::string str;
    std::string raw;
    std::vector<Jv> arr;
    std::vector<std::pair<std::string, Jv>> mem;

    const Jv* find(const char* key) const {
        if (kind != OBJ) return nullptr;
        for (const auto& kv : mem)
            if (kv.first == key) return &kv.second;
        return nullptr;
    }
};

struct JParser {
    const char* p;
    const char* end;
    bool ok = true;

    explicit JParser(const std::string& s)
        : p(s.c_str()), end(s.c_str() + s.size()) {}

    void ws() {
        while (p < end && (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r')) ++p;
    }
    Jv parse() {
        ws();
        return value();
    }
    void lit(const char* s, size_t n) {
        if ((size_t)(end - p) < n || std::memcmp(p, s, n) != 0) ok = false;
        else p += n;
    }
    std::string string() {
        std::string out;
        ++p;
        while (p < end && *p != '"') {
            if (*p == '\\' && p + 1 < end) {
                ++p;
                switch (*p) {
                    case '"': out.push_back('"'); break;
                    case '\\': out.push_back('\\'); break;
                    case '/': out.push_back('/'); break;
                    case 'n': out.push_back('\n'); break;
                    case 't': out.push_back('\t'); break;
                    case 'r': out.push_back('\r'); break;
                    case 'b': out.push_back('\b'); break;
                    case 'f': out.push_back('\f'); break;
                    case 'u':
                        if (end - p >= 5) { p += 4; out.push_back('?'); }
                        else ok = false;
                        break;
                    default: ok = false; break;
                }
                ++p;
            } else {
                out.push_back(*p++);
            }
        }
        if (p >= end) ok = false;
        else ++p;
        return out;
    }
    Jv value() {
        Jv v;
        if (p >= end) { ok = false; return v; }
        if (*p == '{') return object();
        if (*p == '[') return array();
        if (*p == '"') { v.kind = Jv::STR; v.str = string(); return v; }
        if (*p == 't') { lit("true", 4); v.kind = Jv::BOOL; v.b = true; return v; }
        if (*p == 'f') { lit("false", 5); v.kind = Jv::BOOL; return v; }
        if (*p == 'n') { lit("null", 4); v.kind = Jv::NUL; return v; }
        const char* s = p;
        while (p < end && (*p == '-' || *p == '+' || *p == '.' ||
                           (*p >= '0' && *p <= '9') || *p == 'e' || *p == 'E'))
            ++p;
        if (p == s) { ok = false; return v; }
        v.kind = Jv::NUM;
        v.raw.assign(s, p);
        v.num = std::strtod(v.raw.c_str(), nullptr);
        return v;
    }
    Jv object() {
        Jv v;
        v.kind = Jv::OBJ;
        ++p;
        ws();
        if (p < end && *p == '}') { ++p; return v; }
        while (p < end) {
            ws();
            if (p >= end || *p != '"') { ok = false; return v; }
            std::string k = string();
            ws();
            if (p >= end || *p != ':') { ok = false; return v; }
            ++p;
            Jv val = value();
            v.mem.emplace_back(std::move(k), std::move(val));
            ws();
            if (p < end && *p == ',') { ++p; continue; }
            if (p < end && *p == '}') { ++p; return v; }
            ok = false;
            return v;
        }
        ok = false;
        return v;
    }
    Jv array() {
        Jv v;
        v.kind = Jv::ARR;
        ++p;
        ws();
        if (p < end && *p == ']') { ++p; return v; }
        while (p < end) {
            Jv val = value();
            v.arr.push_back(std::move(val));
            ws();
            if (p < end && *p == ',') { ++p; continue; }
            if (p < end && *p == ']') { ++p; return v; }
            ok = false;
            return v;
        }
        ok = false;
        return v;
    }
};

int g_pass = 0;
int g_fail = 0;
std::vector<std::string> g_log;

void record(bool pass, const std::string& name, const std::string& detail) {
    if (pass) {
        ++g_pass;
        g_log.push_back("PASS " + name);
    } else {
        ++g_fail;
        g_log.push_back("FAIL " + name + (detail.empty() ? "" : (" | " + detail)));
    }
}

std::string num(double v) {
    std::ostringstream o;
    o << std::setprecision(17) << v;
    return o.str();
}

constexpr float kHalfSide = 0.025f;
constexpr double kCubeVol = 1.25e-4;
constexpr double kKappa = 4.6e-10;
constexpr float kDt = 1.0f / 300.0f;

void make_cube(std::vector<uint32_t>& idx, std::vector<float>& verts9) {
    const float C[8][3] = {
        {-kHalfSide, -kHalfSide, -kHalfSide}, { kHalfSide, -kHalfSide, -kHalfSide},
        { kHalfSide,  kHalfSide, -kHalfSide}, {-kHalfSide,  kHalfSide, -kHalfSide},
        {-kHalfSide, -kHalfSide,  kHalfSide}, { kHalfSide, -kHalfSide,  kHalfSide},
        { kHalfSide,  kHalfSide,  kHalfSide}, {-kHalfSide,  kHalfSide,  kHalfSide},
    };
    static const uint32_t IDX[36] = {
        1, 2, 6, 1, 6, 5,
        0, 4, 7, 0, 7, 3,
        3, 6, 2, 3, 7, 6,
        0, 1, 5, 0, 5, 4,
        4, 5, 6, 4, 6, 7,
        0, 2, 1, 0, 3, 2,
    };
    verts9.assign(8 * 9, 0.0f);
    const float inv = 1.0f / std::sqrt(3.0f);
    for (int v = 0; v < 8; ++v) {
        verts9[v * 9 + 0] = C[v][0];
        verts9[v * 9 + 1] = C[v][1];
        verts9[v * 9 + 2] = C[v][2];
        verts9[v * 9 + 3] = C[v][0] * inv;
        verts9[v * 9 + 4] = C[v][1] * inv;
        verts9[v * 9 + 5] = C[v][2] * inv;
        verts9[v * 9 + 6] = 0.5f;
        verts9[v * 9 + 7] = 0.5f;
        verts9[v * 9 + 8] = 0.5f;
    }
    idx.assign(IDX, IDX + 36);
}

void append_u32(std::string& s, uint32_t v) {
    s.append(reinterpret_cast<const char*>(&v), 4);
}
void append_f32(std::string& s, float v) {
    s.append(reinterpret_cast<const char*>(&v), 4);
}

std::string blob_classify_all(uint32_t tris, uint8_t pin) {
    std::string s;
    append_u32(s, tris);
    s.append(tris, static_cast<char>(pin));
    return s;
}

std::string blob_one_pin(float x, float y, float z) {
    std::string s;
    append_u32(s, 1);
    append_f32(s, x);
    append_f32(s, y);
    append_f32(s, z);
    return s;
}

std::string blob_vertbind_all(uint32_t nv, uint8_t pin) {
    std::string s;
    append_u32(s, nv);
    for (uint32_t v = 0; v < nv; ++v) {
        s.append(3, static_cast<char>(pin));
        append_f32(s, 1.0f);
        append_f32(s, 0.0f);
        append_f32(s, 0.0f);
    }
    return s;
}

struct CellRow {
    bool has_i = false;
    double i = -1;
    std::string v0_tok, w_tok, vol_tok, p_tok;
    double v0 = 0, vol = 0, w = 0, p = 0;
    double caps = -1, ylo = 0, yhi = 0;
    bool degenerate = false;
    std::string missing;
};

struct State {
    bool ok = false;
    double n_cells = -1;
    std::vector<CellRow> cells;
    bool has_legacy_cells = false;
    size_t legacy_cells_len = 0;
    bool has_w_sum = false;
    double w_sum = 0;
    std::string w_sum_tok;
    bool has_mass = false;
    double mass = 0;
    bool has_w_init = false;
    std::string w_init;
    bool sealed = false;
    double V_lower = 0, V_upper = 0, P_lower = 0, P_upper = 0;
    double v0_lower = 0, v0_upper = 0, V_whole = 0, conserve = 0;
    bool has_conserve = false;
};

State read_state(const std::string& js) {
    State st;
    JParser jp(js);
    Jv root = jp.parse();
    st.ok = jp.ok && root.kind == Jv::OBJ;
    if (!st.ok) return st;
    const Jv* x = root.find("n_cells");
    if (x) st.n_cells = x->num;
    x = root.find("sealed");
    if (x) st.sealed = (x->kind == Jv::BOOL && x->b);
    x = root.find("w_sum");
    if (x) { st.has_w_sum = true; st.w_sum = x->num; st.w_sum_tok = x->raw; }
    x = root.find("seal_mass_kg");
    if (x) { st.has_mass = true; st.mass = x->num; }
    x = root.find("seal_w_init");
    if (x) { st.has_w_init = true; st.w_init = x->kind == Jv::STR ? x->str : ""; }
    x = root.find("conserve_pct");
    if (x) { st.has_conserve = true; st.conserve = x->num; }
    x = root.find("V_lower");
    if (x) st.V_lower = x->num;
    x = root.find("V_upper");
    if (x) st.V_upper = x->num;
    x = root.find("P_lower");
    if (x) st.P_lower = x->num;
    x = root.find("P_upper");
    if (x) st.P_upper = x->num;
    x = root.find("v0_lower");
    if (x) st.v0_lower = x->num;
    x = root.find("v0_upper");
    if (x) st.v0_upper = x->num;
    x = root.find("V_whole");
    if (x) st.V_whole = x->num;
    const Jv* cells = root.find("seal_cells");
    if (cells && cells->kind == Jv::ARR) {
        for (const Jv& c : cells->arr) {
            CellRow r;
            const Jv* f;
            if ((f = c.find("i"))) { r.has_i = true; r.i = f->num; }
            else r.missing += " i";
            if ((f = c.find("v0"))) { r.v0 = f->num; r.v0_tok = f->raw; }
            else r.missing += " v0";
            if ((f = c.find("vol"))) { r.vol = f->num; r.vol_tok = f->raw; }
            else r.missing += " vol";
            if ((f = c.find("w"))) { r.w = f->num; r.w_tok = f->raw; }
            else r.missing += " w";
            if ((f = c.find("p"))) { r.p = f->num; r.p_tok = f->raw; }
            else r.missing += " p";
            if ((f = c.find("caps"))) r.caps = f->num;
            else r.missing += " caps";
            if ((f = c.find("ylo"))) r.ylo = f->num;
            else r.missing += " ylo";
            if ((f = c.find("yhi"))) r.yhi = f->num;
            else r.missing += " yhi";
            if ((f = c.find("degenerate"))) r.degenerate = (f->kind == Jv::BOOL && f->b);
            else r.missing += " degenerate";
            st.cells.push_back(std::move(r));
        }
    }
    const Jv* legacy = root.find("cells");
    if (legacy && legacy->kind == Jv::ARR) {
        st.has_legacy_cells = true;
        st.legacy_cells_len = legacy->arr.size();
    }
    return st;
}

void check_rest_cell(const State& st, size_t k, const std::string& tag) {
    const CellRow& c = st.cells[k];
    std::ostringstream d;
    if (!c.missing.empty()) {
        record(false, tag + ".keys", "missing:" + c.missing);
        return;
    }
    record(true, tag + ".keys", "");
    d << "w=" << c.w_tok << " v0=" << c.v0_tok;
    record(c.w_tok == c.v0_tok, tag + ".w_eq_v0_exact", d.str());
    d.str("");
    d << "p=" << num(c.p);
    record(c.p == 0.0, tag + ".p_exact_zero", d.str());
    record(!c.degenerate, tag + ".not_degenerate", "");
    record(c.v0 > 0.0, tag + ".v0_positive", num(c.v0));
}

bool cut_and_check(MembraneTick& m, float y, int cell, const std::string& tag,
                   size_t want_cells) {
    int oc = -1;
    bool okc = m.seal(y, cell, &oc);
    std::ostringstream d;
    d << "returned=" << okc << " outcome=" << oc;
    record(okc && oc == MembraneTick::SEAL_CUT, tag + ".executed", d.str());
    State st = read_state(m.state_json());
    record(st.ok, tag + ".json_parsed", "");
    if (!st.ok) return false;
    d.str("");
    d << "n_cells=" << num(st.n_cells) << " want=" << want_cells;
    record(st.cells.size() == want_cells && st.n_cells == (double)want_cells,
           tag + ".n_cells", d.str());
    if (st.cells.size() != want_cells) return false;
    for (size_t k = 0; k < st.cells.size(); ++k)
        check_rest_cell(st, k, tag + ".cell" + std::to_string(k));
    return true;
}

void run_all() {
    const std::string CUT1 = "T1.seal1";
    const std::string CUT2 = "T1.seal2";

    {
        MembraneTick m;
        std::vector<uint32_t> idx;
        std::vector<float> verts;
        make_cube(idx, verts);
        m.init((uint32_t)(idx.size() / 3), idx, verts);

        cut_and_check(m, 0.0f, 0, CUT1, 2);

        State st = read_state(m.state_json());
        double ymid = 0.0;
        const CellRow* c0 = st.cells.empty() ? nullptr : &st.cells[0];
        bool have_bounds = c0 && c0->missing.find(" ylo") == std::string::npos &&
                           c0->missing.find(" yhi") == std::string::npos;
        if (!have_bounds) {
            record(false, "T1.seal2.setup",
                   c0 ? ("cell0 missing ylo/yhi:" + c0->missing) : "no cells exported");
        } else {
            ymid = (c0->ylo + c0->yhi) / 2.0;
            cut_and_check(m, (float)ymid, 0, CUT2, 3);

            State st2 = read_state(m.state_json());
            double sum_v0 = 0.0;
            for (const CellRow& c : st2.cells) sum_v0 += c.v0;
            std::ostringstream d;
            d << "sum(v0)=" << num(sum_v0) << " cube=" << num(kCubeVol);
            record(std::fabs(sum_v0 - kCubeVol) <= 2e-5 * kCubeVol,
                   "T1.v0_tiles_cube", d.str());
        }
    }

    State t2;
    {
        MembraneTick m;
        std::vector<uint32_t> idx;
        std::vector<float> verts;
        make_cube(idx, verts);
        m.init((uint32_t)(idx.size() / 3), idx, verts);
        int oc = -1;
        m.seal(0.0f, 0, &oc);
        State st = read_state(m.state_json());
        double ymid = st.cells.empty() ? 0.0
                                       : (st.cells[0].ylo + st.cells[0].yhi) / 2.0;
        m.seal((float)ymid, 0, &oc);
        t2 = read_state(m.state_json());

        record(t2.ok, "T2.json_parsed", "");
        if (t2.ok) {
            std::ostringstream d;
            d << "len(seal_cells)=" << t2.cells.size() << " n_cells=" << num(t2.n_cells);
            record(t2.n_cells == 3.0 && t2.cells.size() == 3, "T2.cells_array_len", d.str());
            record(t2.has_legacy_cells && t2.legacy_cells_len == t2.cells.size(),
                   "T2.legacy_cells_array_intact",
                   t2.has_legacy_cells ? ("len=" + std::to_string(t2.legacy_cells_len))
                                       : "<missing legacy cells array>");

            bool all_keys = true;
            std::string missing;
            for (size_t k = 0; k < t2.cells.size(); ++k) {
                if (!t2.cells[k].missing.empty()) {
                    all_keys = false;
                    missing += " [cell" + std::to_string(k) + ":" + t2.cells[k].missing + " ]";
                }
            }
            record(all_keys, "T2.cell_keys_present",
                   "need i,v0,vol,w,p,caps,ylo,yhi,degenerate;" + missing);

            bool idx_ok = true;
            std::string idx_bad;
            for (size_t k = 0; k < t2.cells.size(); ++k) {
                if (!t2.cells[k].has_i || t2.cells[k].i != (double)k) {
                    idx_ok = false;
                    idx_bad += " cell" + std::to_string(k) + ".i=" +
                               (t2.cells[k].has_i ? num(t2.cells[k].i) : "<missing>");
                }
            }
            record(idx_ok, "T2.cell_i_indexed", idx_bad);

            bool wv_ok = true;
            std::string wv_bad;
            double sum_w = 0.0;
            for (size_t k = 0; k < t2.cells.size(); ++k) {
                const CellRow& c = t2.cells[k];
                sum_w += c.w;
                if (c.w_tok != c.v0_tok) {
                    wv_ok = false;
                    wv_bad += " cell" + std::to_string(k) +
                              " w=" + c.w_tok + " v0=" + c.v0_tok;
                }
            }
            record(wv_ok, "T2.w_eq_v0_per_cell", wv_bad);

            record(t2.has_w_sum, "T2.w_sum_present", "");
            if (t2.has_w_sum) {
                std::ostringstream d2;
                d2 << "w_sum=" << num(t2.w_sum) << " sum(w_i)=" << num(sum_w);
                // 1e-4 relative: per-token 6-significant-digit print quantization, <=3 addends
                record(std::fabs(t2.w_sum - sum_w) <= 1e-4 * std::max(1e-30, std::fabs(sum_w)),
                       "T2.w_sum_matches_cells", d2.str());
                record(t2.has_mass, "T2.seal_mass_kg_present", "");
                if (t2.has_mass) {
                    std::ostringstream d3;
                    d3 << "mass=" << num(t2.mass) << " w_sum*1000=" << num(t2.w_sum * 1000.0);
                    record(std::fabs(t2.mass - t2.w_sum * 1000.0) <=
                               1e-5 * std::max(1.0, std::fabs(t2.mass)),
                           "T2.seal_mass_kg_eq_wsum_times_1000", d3.str());
                }
            }
            record(t2.has_w_init && t2.w_init.empty(), "T2.seal_w_init_empty_fresh",
                   t2.has_w_init ? ("\"" + t2.w_init + "\"") : "<missing key>");
        }
    }

    {
        MembraneTick m;
        std::vector<uint32_t> idx;
        std::vector<float> verts;
        make_cube(idx, verts);
        m.init((uint32_t)(idx.size() / 3), idx, verts);
        bool cl = m.load_classify(blob_classify_all(12, 0));
        bool pj = m.load_joint_pins(blob_one_pin(0.0f, 0.0f, 0.0f));
        bool vb = m.load_vertbind(blob_vertbind_all(8, 0));
        std::ostringstream d;
        d << "classify=" << cl << " pins=" << pj << " vertbind=" << vb;
        record(cl && pj && vb, "T3.classification_loaded", d.str());

        int oc = -1;
        m.seal(0.0f, 0, &oc);
        State st = read_state(m.state_json());
        double ymid = st.cells.empty() ? 0.0
                                       : (st.cells[0].ylo + st.cells[0].yhi) / 2.0;
        m.seal((float)ymid, 0, &oc);

        std::vector<float> mirror;
        make_cube(idx, mirror);

        m.step(mirror, kDt);
        State rest = read_state(m.state_json());
        record(rest.ok && rest.cells.size() == 3, "T3.rest.state", "");
        for (size_t k = 0; rest.cells.size() == 3 && k < 3; ++k) {
            const CellRow& c = rest.cells[k];
            if (!c.missing.empty()) {
                record(false, "T3.rest.cell" + std::to_string(k) + ".keys",
                       "missing:" + c.missing);
                continue;
            }
            record(c.w_tok == c.v0_tok, "T3.rest.cell" + std::to_string(k) + ".w_eq_v0_exact",
                   "w=" + c.w_tok + " v0=" + c.v0_tok);
            record(c.vol_tok == c.v0_tok,
                   "T3.rest.cell" + std::to_string(k) + ".vol_eq_v0_exact",
                   "vol=" + c.vol_tok + " v0=" + c.v0_tok);
            record(c.p == 0.0, "T3.rest.cell" + std::to_string(k) + ".p_exact_zero",
                   "p=" + num(c.p));
        }
        double base_sum_w = 0.0;
        for (const CellRow& c : rest.cells) base_sum_w += c.w;

        bool pressed = m.intent_joint(0, 3000.0f);
        record(pressed, "T3.press_armed", "");

        bool deformed_seen = false;
        for (int tick = 1; tick <= 10; ++tick) {
            mirror[2 * 9 + 1] += 0.001f;
            mirror[5 * 9 + 0] -= 0.0005f;
            m.step(mirror, kDt);
            std::string tag = "T3.tick" + std::to_string(tick);
            State ts = read_state(m.state_json());
            if (!ts.ok || ts.cells.size() != 3) {
                record(false, tag + ".state", "cells parsed != 3");
                continue;
            }
            double sum_w = 0.0;
            for (size_t k = 0; k < 3; ++k) {
                const CellRow& c = ts.cells[k];
                sum_w += c.w;
                if (!c.missing.empty()) {
                    record(false, tag + ".cell" + std::to_string(k) + ".keys",
                           "missing:" + c.missing);
                    continue;
                }
                record(c.w_tok == c.v0_tok, tag + ".cell" + std::to_string(k) + ".w_invariant",
                       "w=" + c.w_tok + " v0=" + c.v0_tok);
                double dv = c.v0 - c.vol;
                if (dv != 0.0) {
                    deformed_seen = true;
                    double p_pred = dv / (kKappa * c.v0);
                    std::ostringstream d2;
                    d2 << "p=" << num(c.p) << " predicted=" << num(p_pred)
                       << " (v0=" << c.v0_tok << " vol=" << c.vol_tok << ")";
                    record(c.p != 0.0, tag + ".cell" + std::to_string(k) + ".p_answers", d2.str());
                    record(std::fabs(c.p - p_pred) <= 1e-3 * std::max(std::fabs(p_pred), 1e-30),
                           tag + ".cell" + std::to_string(k) + ".kappa_law", d2.str());
                } else {
                    record(c.p == 0.0, tag + ".cell" + std::to_string(k) + ".p_zero_at_rest_vol",
                           "p=" + num(c.p));
                }
            }
            record(sum_w == base_sum_w, tag + ".sum_w_constant",
                   "sum=" + num(sum_w) + " base=" + num(base_sum_w));
        }
        record(deformed_seen, "T3.deformation_reached_volume",
               "no cell ever reported vol != v0 under the held press");

        State post = read_state(m.state_json());
        m.clear_intent();
        record(post.ok && post.cells.size() == 3, "T4.state_available", "");
        bool cells_complete = true;
        for (const CellRow& c : post.cells)
            if (!c.missing.empty()) cells_complete = false;
        record(post.ok && post.cells.size() == 3 && cells_complete, "T4.cell_keys_present",
               cells_complete ? "" : "cells lack i/vol/w/p keys; T4 comparisons skipped");
        if (post.ok && post.cells.size() == 3 && cells_complete) {
            std::ostringstream d2;
            d2 << "n_cells=" << num(post.n_cells);
            record(post.n_cells == 3.0, "T4.n_cells", d2.str());
            record(post.sealed, "T4.sealed_flag", "");
            record(std::isfinite(post.V_whole) && std::isfinite(post.conserve) && post.has_conserve,
                   "T4.conserve_pct_finite",
                   "V_whole=" + num(post.V_whole) + " conserve_pct=" + num(post.conserve));
            record(post.V_lower == post.cells[0].vol, "T4.V_lower_eq_cells0_vol",
                   num(post.V_lower) + " vs " + num(post.cells[0].vol));
            record(post.V_upper == post.cells[1].vol, "T4.V_upper_eq_cells1_vol",
                   num(post.V_upper) + " vs " + num(post.cells[1].vol));
            record(post.P_lower == post.cells[0].p, "T4.P_lower_eq_cells0_p",
                   num(post.P_lower) + " vs " + num(post.cells[0].p));
            record(post.P_upper == post.cells[1].p, "T4.P_upper_eq_cells1_p",
                   num(post.P_upper) + " vs " + num(post.cells[1].p));
        }
    }
}

}  // namespace

int main(int argc, char** argv) {
    run_all();
    for (const std::string& line : g_log) std::printf("%s\n", line.c_str());
    std::printf("P1_INVENTORY: %d/%d PASS\n", g_pass, g_pass + g_fail);
    if (argc > 1) {
        std::ofstream out(argv[1]);
        for (const std::string& line : g_log) out << line << "\n";
        out << "P1_INVENTORY: " << g_pass << "/" << (g_pass + g_fail) << " PASS\n";
    }
    return g_fail == 0 ? 0 : 1;
}
