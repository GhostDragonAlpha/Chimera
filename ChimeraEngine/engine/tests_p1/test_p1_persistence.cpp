// test_p1_persistence.cpp -- P1 WORKER 5: seal-state save/restore CPU tests.
// Console shim linking ../membrane_tick.cpp (no engine, no network, no GPU).
//
// Covers septa packet v3 phase-1 persistence (P1.3):
//   R1  new-format (SEL2) round-trip into a fresh instance, byte-deterministic
//   R2  supplied per-cell w inventory round-trips EXACTLY (never replaced)
//   R2b blob-level proof (B3): export_seal_state on the instance R2 restored
//       into must reproduce the crafted input BYTES exactly (size + memcmp)
//       -- supplied w round-trips at the byte level, complementing R1's
//       default-value byte identity. The crafted record carries v0 == vol
//       and p == 0 because restore legitimately re-normalizes the live
//       fields (vol := v0, p := 0) at commit; with those crafted rest-normal,
//       byte equality is the correct expectation, not a weakened one.
//   R3  legacy SEL1 migration: w := v0 per cell, NAMED "legacy_no_w",
//       the legacy snapshot FILE is never mutated
//   R4  named refusals: (a) NaN w (b) negative w (c) trailing garbage
//       (d) stale v0 -> volume witness; refusals leave the tree unchanged
//   R5  restore-at-rest semantics: vol := v0, p := 0; one tick re-measures;
//       supplied w SURVIVES the tick (inventory, not a scratch field)
//
// Telemetry law this test encodes (measured, worker 2's landed design):
// state_json keeps the legacy per-triangle "cells" array BYTE-IDENTICAL
// (backward compatibility) and exports the sealed-tree telemetry in the
// added "seal_cells" array ({i, v0, vol, w, p, caps, ylo, yhi, degenerate}).
// Floats print at 6 significant digits (jf), so full-precision blob values
// are compared against telemetry at 1e-6 relative (the print quantum is
// 5e-7 relative), while telemetry-vs-telemetry comparisons of the same f32
// are exact. Named refusals read "seal_refusal"; the migration marker reads
// "seal_w_init".
//
// Wire format under test (little-endian), magic-versioned:
//   SEL1 = 0x31534553: {u32 magic, u32 nv, u32 n_cuts,
//                       n_cuts x {u32 n, u8 v[32], u8 w[32]} (68 B each),
//                       u32 n_cells,
//                       per cell {u32 pn, u32 pieces[pn],
//                                 f32 v0, f32 vol, f32 p, i32 caps,
//                                 f32 ylo, f32 yhi, u8 degenerate}}
//   SEL2 = 0x32534553: the SEL1 layout + f32 w appended after the
//                      degenerate byte, per cell.
//
// Output: one PASS/FAIL line per test + final "P1_PERSISTENCE: x/9 PASS".
// Results are written to argv[1] when present. Exit code 0 iff all pass.

#include "membrane_tick.hpp"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static const uint32_t SEL1_MAGIC = 0x31534553u;  // 'SEL1' (legacy, no w)
static const uint32_t SEL2_MAGIC = 0x32534553u;  // 'SEL2' (explicit w)

// ─── little-endian byte helpers (native LE targets, same as the engine) ───
static bool rd_u32(const std::vector<uint8_t>& b, size_t off, uint32_t* v) {
    if (off + 4 > b.size()) return false;
    std::memcpy(v, b.data() + off, 4);
    return true;
}
static bool rd_f32(const std::vector<uint8_t>& b, size_t off, float* v) {
    return rd_u32(b, off, reinterpret_cast<uint32_t*>(v));
}
static void put_f32(std::vector<uint8_t>& b, size_t off, float v) {
    std::memcpy(b.data() + off, &v, 4);
}
static void put_u32(std::vector<uint8_t>& b, size_t off, uint32_t v) {
    std::memcpy(b.data() + off, &v, 4);
}
static uint64_t fnv1a64(const std::vector<uint8_t>& b) {
    uint64_t h = 1469598103934665603ull;
    for (uint8_t x : b) { h ^= x; h *= 1099511628211ull; }
    return h;
}
static std::string g17(double v) {   // full-precision detail printing
    char buf[40];
    std::snprintf(buf, sizeof buf, "%.17g", v);
    return buf;
}

// ─── seal-blob parser (walks BOTH magics per the spec layout) ──────────────
struct ParsedBlob {
    uint32_t magic = 0, nv = 0, n_cuts = 0, n_cells = 0;
    bool has_w = false;               // true => SEL2 (w present per cell)
    std::vector<float> v0, vol, p, w;
    std::vector<size_t> v0_off, w_off;  // byte offsets of the f32 fields
    std::string err;
};

static bool parse_seal_blob(const std::vector<uint8_t>& b, ParsedBlob* out) {
    out->err.clear();
    if (!rd_u32(b, 0, &out->magic)) { out->err = "blob too small for magic"; return false; }
    if (out->magic == SEL2_MAGIC) out->has_w = true;
    else if (out->magic != SEL1_MAGIC) {
        std::ostringstream o; o << "unknown magic 0x" << std::hex << out->magic;
        out->err = o.str(); return false;
    }
    if (!rd_u32(b, 4, &out->nv) || !rd_u32(b, 8, &out->n_cuts)) {
        out->err = "blob too small for header"; return false;
    }
    size_t off = 12 + (size_t)out->n_cuts * 68u;
    if (off + 4 > b.size()) { out->err = "blob too small for cut table"; return false; }
    if (!rd_u32(b, off, &out->n_cells)) { out->err = "no n_cells"; return false; }
    off += 4;
    for (uint32_t ci = 0; ci < out->n_cells; ++ci) {
        uint32_t pn = 0;
        if (!rd_u32(b, off, &pn)) { out->err = "truncated cell header"; return false; }
        off += 4 + (size_t)pn * 4u;
        float f = 0.f;
        if (!rd_f32(b, off, &f)) { out->err = "truncated v0"; return false; }
        out->v0.push_back(f); out->v0_off.push_back(off); off += 4;
        if (!rd_f32(b, off, &f)) { out->err = "truncated vol"; return false; }
        out->vol.push_back(f); off += 4;
        if (!rd_f32(b, off, &f)) { out->err = "truncated p"; return false; }
        out->p.push_back(f); off += 4;
        off += 4;   // i32 caps
        off += 4;   // f32 ylo
        off += 4;   // f32 yhi
        off += 1;   // u8 degenerate
        if (out->has_w) {
            if (!rd_f32(b, off, &f)) { out->err = "truncated w"; return false; }
            out->w.push_back(f); out->w_off.push_back(off); off += 4;
        }
        if (off > b.size()) { out->err = "cell record past end"; return false; }
    }
    if (off != b.size()) {
        std::ostringstream o;
        o << "exact-size violation: walked " << off << " of " << b.size() << " bytes";
        out->err = o.str(); return false;
    }
    return true;
}

// SEL2 -> SEL1 fixture: strip the per-cell w field, rewind the magic.
static bool sel2_to_sel1(const std::vector<uint8_t>& src,
                         std::vector<uint8_t>* dst, std::string* err) {
    ParsedBlob pb;
    if (!parse_seal_blob(src, &pb)) { *err = "source blob does not parse: " + pb.err; return false; }
    if (!pb.has_w) { *err = "source blob is already SEL1"; return false; }
    *dst = src;
    put_u32(*dst, 0, SEL1_MAGIC);
    // remove the 4 w bytes per cell, back to front so offsets stay valid
    for (uint32_t ci = pb.n_cells; ci-- > 0;)
        dst->erase(dst->begin() + (long)pb.w_off[ci],
                   dst->begin() + (long)pb.w_off[ci] + 4);
    return true;
}

// ─── minimal JSON readers for state_json (generated, machine-format) ───────
static bool json_string_field(const std::string& j, const char* key,
                              std::string* out) {
    std::string pat = std::string("\"") + key + "\":\"";
    size_t p = j.find(pat);
    if (p == std::string::npos) return false;
    p += pat.size();
    size_t e = j.find('"', p);
    if (e == std::string::npos) return false;
    *out = j.substr(p, e - p);
    return true;
}
static bool json_int_field(const std::string& j, const char* key, long* out) {
    std::string pat = std::string("\"") + key + "\":";
    size_t p = j.find(pat);
    if (p == std::string::npos) return false;
    *out = std::strtol(j.c_str() + p + pat.size(), nullptr, 10);
    return true;
}
// span of a named array (between "\"key\":[" and its matching bracket)
static bool json_array_span(const std::string& j, const char* key,
                            size_t* begin, size_t* end) {
    std::string pat = std::string("\"") + key + "\":[";
    size_t p = j.find(pat);
    if (p == std::string::npos) return false;
    *begin = p + pat.size();
    int depth = 0;
    for (size_t i = *begin; i < j.size(); ++i) {
        if (j[i] == '[' || j[i] == '{') ++depth;
        else if (j[i] == ']' && depth == 0) { *end = i; return true; }
        else if (j[i] == '}' || j[i] == ']') --depth;
    }
    return false;
}
// per-object spans inside a flat JSON array of objects
static void json_array_objects(const std::string& j, const char* key,
                               std::vector<std::string>* objs) {
    size_t b = 0, e = 0;
    if (!json_array_span(j, key, &b, &e)) return;
    size_t i = b;
    while (i < e) {
        size_t o = j.find('{', i);
        if (o == std::string::npos || o >= e) break;
        int depth = 0;
        size_t k = o;
        for (; k < e; ++k) {
            if (j[k] == '{') ++depth;
            else if (j[k] == '}') { --depth; if (depth == 0) break; }
        }
        objs->push_back(j.substr(o, k - o + 1));
        i = k + 1;
    }
}
static bool json_num_in(const std::string& obj, const char* key, double* out) {
    std::string pat = std::string("\"") + key + "\":";
    size_t p = obj.find(pat);
    if (p == std::string::npos) return false;
    const char* s = obj.c_str() + p + pat.size();
    char* endp = nullptr;
    *out = std::strtod(s, &endp);
    return endp != s;
}

// ─── the synthetic body: closed unit cube, outward winding, 8 verts ────────
static void make_cube(std::vector<uint32_t>* idx, std::vector<float>* verts9) {
    static const float V[8][3] = {
        {0.f, 0.f, 0.f}, {1.f, 0.f, 0.f}, {1.f, 1.f, 0.f}, {0.f, 1.f, 0.f},
        {0.f, 0.f, 1.f}, {1.f, 0.f, 1.f}, {1.f, 1.f, 1.f}, {0.f, 1.f, 1.f},
    };
    static const uint32_t F[12][3] = {
        {0, 1, 5}, {0, 5, 4},   // bottom  (-y)
        {3, 7, 6}, {3, 6, 2},   // top     (+y)
        {0, 2, 1}, {0, 3, 2},   // front   (-z)
        {4, 5, 6}, {4, 6, 7},   // back    (+z)
        {1, 2, 6}, {1, 6, 5},   // right   (+x)
        {0, 4, 7}, {0, 7, 3},   // left    (-x)
    };
    verts9->clear();
    idx->clear();
    for (int i = 0; i < 8; ++i) {
        verts9->push_back(V[i][0]); verts9->push_back(V[i][1]);
        verts9->push_back(V[i][2]);
        verts9->push_back(0.f); verts9->push_back(1.f); verts9->push_back(0.f);
        verts9->push_back(0.5f); verts9->push_back(0.5f); verts9->push_back(0.5f);
    }
    for (int t = 0; t < 12; ++t) {
        idx->push_back(F[t][0]); idx->push_back(F[t][1]); idx->push_back(F[t][2]);
    }
}

// init + two seal cuts -> the 3-cell tree (nominal volumes 0.25 / 0.25 / 0.5)
static bool build_tree(MembraneTick* mt, std::string* err) {
    std::vector<uint32_t> idx;
    std::vector<float> verts9;
    make_cube(&idx, &verts9);
    mt->init((uint32_t)idx.size() / 3u, idx, verts9);
    int oc = -1;
    if (!mt->seal(0.5f, 0, &oc) || oc != MembraneTick::SEAL_CUT) {
        *err = "first seal (y=0.5) failed"; return false;
    }
    // cut the lower daughter (min ylo) at y = 0.25, index-agnostic
    std::string j = mt->state_json();
    std::vector<std::string> objs;
    json_array_objects(j, "seal_cells", &objs);
    long lower = -1;
    double best = 1e30;
    for (size_t i = 0; i < objs.size(); ++i) {
        double ylo = 0;
        if (!json_num_in(objs[i], "ylo", &ylo)) continue;
        if (ylo < best) { best = ylo; lower = (long)i; }
    }
    if (lower < 0) { *err = "no daughter cell after first seal"; return false; }
    if (!mt->seal(0.25f, (int)lower, &oc) || oc != MembraneTick::SEAL_CUT) {
        *err = "second seal (y=0.25) failed"; return false;
    }
    return true;
}
// MembraneTick is non-movable (mutex member): instances live behind
// unique_ptr, built by init + the two seal cuts.
static std::unique_ptr<MembraneTick> fresh_sealed(std::string* err) {
    auto mt = std::make_unique<MembraneTick>();
    if (!build_tree(mt.get(), err)) return nullptr;
    return mt;
}
static std::unique_ptr<MembraneTick> fresh_unsealed(void) {
    auto mt = std::make_unique<MembraneTick>();
    std::vector<uint32_t> idx;
    std::vector<float> verts9;
    make_cube(&idx, &verts9);
    mt->init((uint32_t)idx.size() / 3u, idx, verts9);
    return mt;
}

// sealed-tree telemetry snapshot: the "seal_cells" array, byte-for-byte,
// plus the per-cell numbers this suite asserts on
struct TreeSnapshot {
    bool ok = false;
    long n_cells = -1;
    std::string cells_sub;    // raw "seal_cells":[...] span (byte compare)
    std::vector<double> v0, vol, w, p;
};

static TreeSnapshot snapshot(const MembraneTick& mt) {
    TreeSnapshot s;
    std::string j = mt.state_json();
    if (!json_int_field(j, "n_cells", &s.n_cells)) return s;
    size_t b = 0, e = 0;
    if (!json_array_span(j, "seal_cells", &b, &e)) return s;
    s.cells_sub = j.substr(b, e - b);
    std::vector<std::string> objs;
    json_array_objects(j, "seal_cells", &objs);
    for (const std::string& o : objs) {
        double v = 0;
        if (!json_num_in(o, "v0", &v)) return s;   s.v0.push_back(v);
        if (!json_num_in(o, "vol", &v)) return s;  s.vol.push_back(v);
        if (!json_num_in(o, "w", &v)) return s;    s.w.push_back(v);
        if (!json_num_in(o, "p", &v)) return s;    s.p.push_back(v);
    }
    s.ok = true;
    return s;
}

// ─── tiny test harness ─────────────────────────────────────────────────────
struct Report {
    std::vector<std::string> lines;
    int pass = 0, total = 0;
    void add(const std::string& name, bool ok, const std::string& detail) {
        ++total;
        if (ok) ++pass;
        std::string l = name + std::string(": ") + (ok ? "PASS" : "FAIL");
        if (!detail.empty()) l += ok ? ("  [" + detail + "]") : ("  -- " + detail);
        lines.push_back(l);
        std::printf("%s\n", l.c_str());
    }
    std::string summary() const {
        std::ostringstream o;
        o << "P1_PERSISTENCE: " << pass << "/" << total << " PASS";
        return o.str();
    }
};

// telemetry-vs-telemetry (same f32, same print) must be bit-identical
static bool teq(double a, double b) { return a == b; }
// full-precision blob vs 6-significant-digit telemetry: the print quantum
// is 5e-7 relative, so 1e-6 relative is the honest "matches" bound
static bool feq(double a, double b, double rel = 1e-6) {
    return std::fabs(a - b) <= rel * std::max(1.0, std::fabs(a));
}

// ═══════════════════════════════════════════════════════════════════════════
int main(int argc, char** argv) {
    Report rep;

    // ─── shared fixture: sealed 3-cell tree, export B1 ─────────────────────
    std::string ferr;
    auto inst_a = fresh_sealed(&ferr);
    std::vector<uint8_t> B1;
    if (!inst_a) {
        rep.add("FIXTURE", false, ferr);
        std::printf("%s\n", rep.summary().c_str());
        return 1;
    }
    inst_a->export_seal_state(B1);
    ParsedBlob blob1;
    bool b1_ok = !B1.empty() && parse_seal_blob(B1, &blob1);
    if (!b1_ok) {
        rep.add("FIXTURE", false,
                "export empty or unparseable: " + blob1.err);
        std::printf("%s\n", rep.summary().c_str());
        return 1;
    }
    const bool sel2_landed = blob1.magic == SEL2_MAGIC;

    // ═══ R1: NEW-FORMAT ROUND-TRIP ═════════════════════════════════════════
    {
        std::ostringstream d;
        bool ok = true;
        if (!sel2_landed) {
            ok = false;
            d << "export wrote legacy SEL1 -- SEL2 not landed (worker 2)";
        }
        auto inst_b = fresh_unsealed();
        if (ok) {
            bool loaded = inst_b->load_seal_state(
                std::string((const char*)B1.data(), B1.size()));
            if (!loaded) { ok = false; d << "load_seal_state(B1) refused"; }
        }
        TreeSnapshot sb;
        if (ok) {
            sb = snapshot(*inst_b);
            if (!sb.ok) { ok = false; d << "seal_cells telemetry unreadable"; }
            else if (sb.n_cells != (long)blob1.n_cells) {
                ok = false;
                d << "n_cells " << sb.n_cells << " != " << blob1.n_cells;
            }
        }
        if (ok) {
            for (size_t i = 0; i < sb.v0.size(); ++i) {
                // w == v0: same f32, same print -- must be exact
                if (!teq(sb.w[i], sb.v0[i])) {
                    ok = false;
                    d << "cell " << i << " w=" << g17(sb.w[i])
                      << " != v0=" << g17(sb.v0[i]);
                    break;
                }
                // blob v0 (full f32) vs telemetry print quantum
                if (!feq(sb.v0[i], (double)blob1.v0[i])) {
                    ok = false;
                    d << "cell " << i << " telemetry v0=" << g17(sb.v0[i])
                      << " vs blob v0=" << g17((double)blob1.v0[i]);
                    break;
                }
            }
        }
        if (ok) {
            std::string swi;
            json_string_field(inst_b->state_json(), "seal_w_init", &swi);
            if (!swi.empty()) {
                ok = false;
                d << "seal_w_init=\"" << swi << "\" (SEL2 path must leave it empty)";
            }
        }
        std::vector<uint8_t> B2;
        if (ok) {
            inst_b->export_seal_state(B2);
            if (B2 != B1) {
                ok = false;
                d << "B2 != B1 (" << B2.size() << " vs " << B1.size()
                  << " bytes) -- export not deterministic";
            }
        }
        rep.add("R1 NEW-FORMAT ROUND-TRIP", ok, d.str());
    }

    // ═══ R2: W ROUND-TRIP EXACTNESS ════════════════════════════════════════
    std::vector<uint8_t> patched;      // reused by R5 (and R2b's byte proof)
    std::vector<float> expected_w;     // the supplied inventory
    std::unique_ptr<MembraneTick> r2_inst;   // the instance R2 restored into
    bool r2_loaded = false;                  // (R2b exports from THAT instance)
    {
        std::ostringstream d;
        bool ok = sel2_landed;
        if (!ok) d << "needs SEL2 export -- not landed (worker 2)";
        static const float FACTOR[3] = {0.5f, 0.75f, 1.25f};
        if (ok) {
            patched = B1;
            expected_w.clear();
            for (uint32_t i = 0; i < blob1.n_cells; ++i) {
                float v = blob1.v0[i] * FACTOR[i % 3];  // finite, > 0, != v0
                put_f32(patched, blob1.w_off[i], v);
                expected_w.push_back(v);
                // R2b crafting law: restore legitimately re-normalizes the
                // live fields at commit (vol := v0, p := 0), so the crafted
                // record must ALREADY carry v0 == vol and p == 0 -- then
                // R2b's exported-bytes == input-bytes is the correct
                // expectation. (The fresh sealed fixture exports exactly
                // these rest values anyway; crafted explicitly so the
                // expectation does not lean on that.) v0/vol/p are
                // contiguous f32s right after the pieces list.
                put_f32(patched, blob1.v0_off[i] + 4, blob1.v0[i]);  // vol
                put_f32(patched, blob1.v0_off[i] + 8, 0.f);          // p
            }
        }
        r2_inst = fresh_unsealed();
        MembraneTick* inst_c = r2_inst.get();
        if (ok) {
            bool loaded = inst_c->load_seal_state(
                std::string((const char*)patched.data(), patched.size()));
            r2_loaded = loaded;
            if (!loaded) { ok = false; d << "load refused a valid SEL2 blob"; }
        }
        if (ok) {
            TreeSnapshot sc = snapshot(*inst_c);
            if (!sc.ok || sc.v0.size() != expected_w.size()) {
                ok = false; d << "seal_cells telemetry unreadable after restore";
            }
            for (size_t i = 0; ok && i < sc.w.size(); ++i) {
                if (!feq(sc.w[i], (double)expected_w[i])) {
                    ok = false;
                    d << "cell " << i << " w=" << g17(sc.w[i])
                      << " != supplied " << g17((double)expected_w[i])
                      << " -- inventory replaced";
                    break;
                }
                if (std::fabs(sc.w[i] - (double)blob1.v0[i])
                    <= 1e-3 * (double)blob1.v0[i]) {
                    ok = false;
                    d << "cell " << i << " w silently reset to v0";
                    break;
                }
            }
            std::string swi;
            json_string_field(inst_c->state_json(), "seal_w_init", &swi);
            if (ok && !swi.empty()) {
                ok = false;
                d << "seal_w_init=\"" << swi << "\" (SEL2 path must leave it empty)";
            }
        }
        rep.add("R2 W ROUND-TRIP EXACTNESS", ok, d.str());
    }

    // ═══ R2b: BLOB-LEVEL ROUND-TRIP (B3) — export(restored) == input ═══════
    // The byte-level complement to R1: R1 proved the DEFAULT-value tree
    // re-exports byte-identically; R2b proves a tree holding SUPPLIED,
    // arbitrary w re-exports the very bytes the loader consumed. The input
    // is crafted rest-normal (v0 == vol, p == 0 -- see R2's crafting law)
    // because restore re-normalizes exactly those two live fields.
    {
        std::ostringstream d;
        bool ok = r2_loaded;
        if (!ok) d << "needs R2's restored instance (R2 failed or not run)";
        std::vector<uint8_t> B3;
        if (ok) {
            r2_inst->export_seal_state(B3);
            if (B3.empty()) { ok = false; d << "export empty after restore"; }
        }
        if (ok) {
            if (B3.size() != patched.size()) {
                ok = false;
                d << "size " << B3.size() << " != crafted input "
                  << patched.size() << " bytes";
            } else if (std::memcmp(B3.data(), patched.data(), B3.size()) != 0) {
                size_t off = 0;
                while (off < B3.size() && B3[off] == patched[off]) ++off;
                ok = false;
                d << "byte diff at offset " << off << " (of " << B3.size()
                  << "): expected(crafted) 0x" << std::hex << std::uppercase
                  << (unsigned)patched[off] << ", actual(exported) 0x"
                  << (unsigned)B3[off] << std::dec << std::nouppercase;
            }
        }
        rep.add("R2b EXPORT BYTES == CRAFTED INPUT", ok, d.str());
    }

    // ═══ R3: LEGACY MIGRATION (SEL1 snapshot, file untouched) ══════════════
    {
        std::ostringstream d;
        bool ok = true;
        std::vector<uint8_t> legacy;
        std::string method;
        if (sel2_landed) {
            std::string e2;
            if (!sel2_to_sel1(B1, &legacy, &e2)) {
                ok = false; d << "fixture build failed: " << e2;
            }
            method = "stripped the 4 per-cell w bytes from the SEL2 export, "
                     "magic rewound to 0x31534553";
        } else {
            legacy = B1;   // export is already legacy-format today
            method = "B1 already legacy SEL1 (worker 2 unlanded); used as-is";
        }
        fs::path fpath;
        std::vector<uint8_t> file_before;
        if (ok) {
            std::error_code ec;
            fpath = fs::temp_directory_path(ec) / "p1_legacy_seal_state.bin";
            if (ec) { ok = false; d << "no temp dir: " << ec.message(); }
        }
        if (ok) {
            std::ofstream f(fpath, std::ios::binary | std::ios::trunc);
            if (!f) { ok = false; d << "cannot write " << fpath.string(); }
            else {
                f.write((const char*)legacy.data(), (std::streamsize)legacy.size());
                f.close();
                std::ifstream r(fpath, std::ios::binary);
                file_before.assign((std::istreambuf_iterator<char>(r)),
                                   std::istreambuf_iterator<char>());
                if (file_before != legacy) {
                    ok = false; d << "file bytes != fixture bytes (write broke)";
                }
            }
        }
        auto inst_d = fresh_unsealed();
        if (ok) {
            bool loaded = inst_d->load_seal_state(
                std::string((const char*)legacy.data(), legacy.size()));
            if (!loaded) { ok = false; d << "legacy SEL1 restore refused"; }
        }
        if (ok) {
            TreeSnapshot sd = snapshot(*inst_d);
            std::string jd = inst_d->state_json();
            if (!sd.ok || sd.v0.size() != (size_t)blob1.n_cells) {
                ok = false; d << "seal_cells telemetry unreadable after legacy restore";
            }
            for (size_t i = 0; ok && i < sd.w.size(); ++i) {
                if (!teq(sd.w[i], sd.v0[i])) {   // migration law w := v0
                    ok = false;
                    d << "cell " << i << " w=" << g17(sd.w[i])
                      << " != v0=" << g17(sd.v0[i]);
                    break;
                }
            }
            std::string swi;
            bool present = json_string_field(jd, "seal_w_init", &swi);
            if (ok && (!present || swi != "legacy_no_w")) {
                ok = false;
                d << "seal_w_init " << (present ? "= \"" + swi + "\""
                                                : std::string("missing"))
                  << " -- must be named \"legacy_no_w\"";
            }
        }
        if (ok) {
            std::ifstream r(fpath, std::ios::binary);
            std::vector<uint8_t> file_after((std::istreambuf_iterator<char>(r)),
                                            std::istreambuf_iterator<char>());
            if (file_after != file_before) {
                ok = false;
                d << "legacy snapshot FILE mutated by restore (hash "
                  << fnv1a64(file_after) << " != " << fnv1a64(file_before) << ")";
            }
        }
        d << "; fixture: " << method;
        rep.add("R3 LEGACY MIGRATION", ok, d.str());
    }

    // ═══ R4: NAMED REFUSALS (all-or-nothing, tree untouched) ═══════════════
    {
        auto unchanged = [&](const MembraneTick& mt, const TreeSnapshot& before,
                             std::ostringstream* d) {
            TreeSnapshot after = snapshot(mt);
            if (!after.ok) { *d << "post-state unreadable"; return false; }
            if (after.n_cells != before.n_cells
                || after.cells_sub != before.cells_sub) {
                *d << "TREE MUTATED by refusal (n_cells " << after.n_cells
                   << " vs " << before.n_cells << ")";
                return false;
            }
            return true;
        };

        // (a) one w = NaN
        {
            std::ostringstream d;
            std::string ea;
            auto inst = fresh_sealed(&ea);
            const bool ready = inst != nullptr;
            TreeSnapshot before;
            if (ready) before = snapshot(*inst);
            bool ok = sel2_landed && ready && before.ok;
            if (!ok) {
                d << (sel2_landed ? "tree/telemetry unavailable: " + ea
                                  : "needs SEL2 export -- not landed (worker 2)");
            }
            std::vector<uint8_t> nanb = B1;
            if (ok) {
                put_u32(nanb, blob1.w_off[1], 0x7FC00000u);   // quiet NaN
                bool loaded = inst->load_seal_state(
                    std::string((const char*)nanb.data(), nanb.size()));
                if (loaded) { ok = false; d << "NaN w ACCEPTED"; }
            }
            if (ok) {
                std::string ref;
                json_string_field(inst->state_json(), "seal_refusal", &ref);
                if (ref != "seal_state_invalid_w") {
                    ok = false;
                    d << "seal_refusal=\"" << ref << "\" != seal_state_invalid_w";
                }
            }
            if (ok && !unchanged(*inst, before, &d)) ok = false;
            rep.add("R4a REFUSAL NaN w", ok, d.str());
        }
        // (b) one w negative
        {
            std::ostringstream d;
            std::string eb;
            auto inst = fresh_sealed(&eb);
            const bool ready = inst != nullptr;
            TreeSnapshot before;
            if (ready) before = snapshot(*inst);
            bool ok = sel2_landed && ready && before.ok;
            if (!ok) {
                d << (sel2_landed ? "tree/telemetry unavailable: " + eb
                                  : "needs SEL2 export -- not landed (worker 2)");
            }
            std::vector<uint8_t> negb = B1;
            if (ok) {
                put_f32(negb, blob1.w_off[1], -1e-3f);
                bool loaded = inst->load_seal_state(
                    std::string((const char*)negb.data(), negb.size()));
                if (loaded) { ok = false; d << "negative w ACCEPTED"; }
            }
            if (ok) {
                std::string ref;
                json_string_field(inst->state_json(), "seal_refusal", &ref);
                if (ref != "seal_state_invalid_w") {
                    ok = false;
                    d << "seal_refusal=\"" << ref << "\" != seal_state_invalid_w";
                }
            }
            if (ok && !unchanged(*inst, before, &d)) ok = false;
            rep.add("R4b REFUSAL NEGATIVE w", ok, d.str());
        }
        // (c) trailing garbage (wrong generation)
        {
            std::ostringstream d;
            std::string ec;
            auto inst = fresh_sealed(&ec);
            const bool ready = inst != nullptr;
            TreeSnapshot before;
            if (ready) before = snapshot(*inst);
            bool ok = ready && before.ok;
            if (!ok) d << "tree/telemetry unavailable: " << ec;
            if (ok) {
                std::vector<uint8_t> gb = B1;
                gb.push_back(0xAA);
                bool loaded = inst->load_seal_state(
                    std::string((const char*)gb.data(), gb.size()));
                if (loaded) { ok = false; d << "garbage-appended blob ACCEPTED"; }
            }
            if (ok && !unchanged(*inst, before, &d)) ok = false;
            rep.add("R4c REFUSAL TRAILING GARBAGE", ok, d.str());
        }
        // (d) stored v0 off by 5% -> volume witness
        {
            std::ostringstream d;
            std::string ed;
            auto inst = fresh_sealed(&ed);
            const bool ready = inst != nullptr;
            TreeSnapshot before;
            if (ready) before = snapshot(*inst);
            bool ok = sel2_landed && ready && before.ok;
            if (!ok) {
                d << (sel2_landed ? "tree/telemetry unavailable: " + ed
                                  : "needs SEL2 export -- not landed (worker 2)");
            }
            if (ok) {
                std::vector<uint8_t> vb = B1;
                float tampered = blob1.v0[1] * 1.05f;
                put_f32(vb, blob1.v0_off[1], tampered);
                bool loaded = inst->load_seal_state(
                    std::string((const char*)vb.data(), vb.size()));
                if (loaded) { ok = false; d << "5%-off v0 ACCEPTED (witness dead)"; }
            }
            if (ok && !unchanged(*inst, before, &d)) ok = false;
            rep.add("R4d REFUSAL VOLUME WITNESS (v0 off 5%)", ok, d.str());
        }
    }

    // ═══ R5: RESTORE SEMANTICS (vol := v0, p := 0, w survives the tick) ════
    {
        std::ostringstream d;
        bool ok = sel2_landed && !patched.empty();
        if (!ok) d << "needs SEL2 export + R2 patch -- not landed (worker 2)";
        auto inst_f = fresh_unsealed();
        if (ok) {
            bool loaded = inst_f->load_seal_state(
                std::string((const char*)patched.data(), patched.size()));
            if (!loaded) { ok = false; d << "restore refused"; }
        }
        TreeSnapshot s0;
        if (ok) {
            s0 = snapshot(*inst_f);
            if (!s0.ok) { ok = false; d << "seal_cells telemetry unreadable"; }
        }
        if (ok) {
            for (size_t i = 0; i < s0.v0.size(); ++i) {
                // restore-at-rest: vol == v0 (same f32, same print)
                if (!teq(s0.vol[i], s0.v0[i])) {
                    ok = false;
                    d << "at restore: cell " << i << " vol=" << g17(s0.vol[i])
                      << " != v0=" << g17(s0.v0[i]);
                    break;
                }
                if (s0.p[i] != 0.0) {
                    ok = false;
                    d << "at restore: cell " << i << " p=" << g17(s0.p[i])
                      << " != 0";
                    break;
                }
                if (!feq(s0.w[i], (double)expected_w[i])) {
                    ok = false;
                    d << "at restore: cell " << i << " w=" << g17(s0.w[i])
                      << " != supplied " << g17((double)expected_w[i]);
                    break;
                }
            }
        }
        if (ok) {
            std::vector<uint32_t> idx;
            std::vector<float> rest;
            make_cube(&idx, &rest);   // the authored rest surface
            inst_f->step(rest, 1.0f / 300.0f);
        }
        TreeSnapshot s1;
        if (ok) {
            s1 = snapshot(*inst_f);
            if (!s1.ok) { ok = false; d << "post-tick telemetry unreadable"; }
        }
        if (ok) {
            for (size_t i = 0; i < s1.v0.size(); ++i) {
                // the tick re-measures on the rest surface: vol == v0 again
                if (!teq(s1.vol[i], s1.v0[i])) {
                    ok = false;
                    d << "after tick: cell " << i << " vol=" << g17(s1.vol[i])
                      << " != v0=" << g17(s1.v0[i]);
                    break;
                }
                if (s1.p[i] != 0.0) {
                    ok = false;
                    d << "after tick: cell " << i << " p=" << g17(s1.p[i])
                      << " != 0 (rest re-measure law)";
                    break;
                }
                if (!feq(s1.w[i], (double)expected_w[i])) {
                    ok = false;
                    d << "after tick: cell " << i << " w=" << g17(s1.w[i])
                      << " != supplied " << g17((double)expected_w[i])
                      << " -- inventory did NOT survive the tick";
                    break;
                }
            }
        }
        rep.add("R5 RESTORE SEMANTICS", ok, d.str());
    }

    const std::string sum = rep.summary();
    std::printf("%s\n", sum.c_str());
    rep.lines.push_back(sum);
    if (argc > 1) {
        std::ofstream out(argv[1], std::ios::binary | std::ios::trunc);
        for (const std::string& l : rep.lines) out << l << "\n";
    }
    return rep.pass == rep.total ? 0 : 1;
}
