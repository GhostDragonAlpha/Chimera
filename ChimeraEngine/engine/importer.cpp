// importer.cpp -- THE ALIVENESS LAW ingestion (see importer.hpp).
// One internal pipeline, two front doors: a minimal OBJ subset and a
// minimal glTF 2.0 reader (own JSON parser -- no dependency is worth a
// build-system branch for this). Both end in the SAME finish(): center,
// divergence closure (the prereg's named falsifier), area-weighted
// normals, warm tan, and the engine's full mesh format.
#include "importer.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace importer {
namespace {

const float kTan[3] = {0.80f, 0.55f, 0.35f};   // uniform warm tan

struct RawMesh {
    std::vector<float>    pos;   // 3 per vertex, source coordinates
    std::vector<uint32_t> idx;   // 3 per triangle, CCW outward
};

bool finite3(float x, float y, float z) {
    return std::isfinite(x) && std::isfinite(y) && std::isfinite(z);
}

// ── OBJ subset ─────────────────────────────────────────────────────────────
// v lines (w ignored), f lines in all four index forms (v, v/vt, v/vt/vn,
// v//vn) with negative (relative) indices; every other keyword ignored.
// Faces fan-triangulate; only < 3 vertices makes that impossible.

bool obj_corner_index(const char* s, size_t n, int64_t vcount, uint32_t* out) {
    // only the first number of "a", "a/b", "a/b/c", "a//c" selects the vertex
    size_t i = 0;
    bool neg = false;
    if (i < n && (s[i] == '-' || s[i] == '+')) { neg = (s[i] == '-'); ++i; }
    int64_t v = 0;
    bool any = false;
    for (; i < n && s[i] >= '0' && s[i] <= '9'; ++i) {
        v = v * 10 + (s[i] - '0');
        if (v > ((int64_t)1 << 40)) return false;   // absurd, not a count
        any = true;
    }
    if (!any) return false;
    int64_t signed_i = neg ? -v : v;
    // OBJ is 1-based; negatives count back from the current vertex total
    int64_t z = signed_i > 0 ? signed_i - 1 : vcount + signed_i;
    if (z < 0 || z >= vcount) return false;
    *out = (uint32_t)z;
    return true;
}

bool parse_obj(const std::string& src, RawMesh& m, std::string& err) {
    uint32_t lineno = 0;
    size_t at = 0;
    const size_t S = src.size();
    while (at < S) {
        size_t eol = src.find('\n', at);
        if (eol == std::string::npos) eol = S;
        size_t end = eol;
        if (end > at && src[end - 1] == '\r') --end;
        ++lineno;
        const char* p  = src.data() + at;
        const char* pe = src.data() + end;
        at = eol + 1;

        while (p < pe && (*p == ' ' || *p == '\t')) ++p;
        const char* kw = p;
        while (p < pe && *p != ' ' && *p != '\t') ++p;
        size_t kwn = (size_t)(p - kw);
        if (kwn == 0) continue;

        if (kwn == 1 && kw[0] == 'v') {
            // sscanf absorbs any whitespace run between the numbers
            float x, y, z;
            if (std::sscanf(p, " %f %f %f", &x, &y, &z) != 3 ||
                !finite3(x, y, z)) {
                err = "OBJ line " + std::to_string(lineno) +
                      ": v needs three finite coordinates";
                return false;
            }
            m.pos.push_back(x); m.pos.push_back(y); m.pos.push_back(z);
            if (m.pos.size() / 3 > kMaxVerts) {
                err = "OBJ exceeds the vertex limit (" +
                      std::to_string(kMaxVerts) + ")";
                return false;
            }
        } else if (kwn == 1 && kw[0] == 'f') {
            const int64_t vc = (int64_t)(m.pos.size() / 3);
            uint32_t corner[64];
            size_t nc = 0;
            for (;;) {
                while (p < pe && (*p == ' ' || *p == '\t')) ++p;
                const char* tok = p;
                while (p < pe && *p != ' ' && *p != '\t') ++p;
                if (p == tok) break;
                if (nc >= 64) {
                    err = "OBJ line " + std::to_string(lineno) +
                          ": face with more than 64 corners refused";
                    return false;
                }
                uint32_t vi;
                if (!obj_corner_index(tok, (size_t)(p - tok), vc, &vi)) {
                    err = "OBJ line " + std::to_string(lineno) +
                          ": face vertex out of range or malformed "
                          "(forward references are not accepted)";
                    return false;
                }
                corner[nc++] = vi;
            }
            if (nc < 3) {
                err = "OBJ line " + std::to_string(lineno) +
                      ": face with fewer than 3 vertices -- fan "
                      "triangulation impossible";
                return false;
            }
            for (size_t k = 1; k + 1 < nc; ++k) {
                m.idx.push_back(corner[0]);
                m.idx.push_back(corner[k]);
                m.idx.push_back(corner[k + 1]);
            }
            if (m.idx.size() / 3 > kMaxTris) {
                err = "OBJ exceeds the triangle limit (" +
                      std::to_string(kMaxTris) + ")";
                return false;
            }
        }
        // vn / vt / g / o / s / usemtl / mtllib / comments: ignored -- the
        // tick recomputes normals and the aliveness law owns colors.
    }
    return true;
}

// ── Minimal JSON (glTF is the only consumer) ───────────────────────────────
// Recursive descent, whitespace-robust, depth-capped: a malformed file
// must not blow the HTTP thread's stack.

struct JVal {
    enum T { NUL, BOOL, NUM, STR, ARR, OBJ } t = NUL;
    bool        b = false;
    double      num = 0.0;
    std::string str;
    std::vector<JVal> arr;
    std::vector<std::pair<std::string, JVal> > mem;

    const JVal* find(const char* key) const {
        for (size_t i = 0; i < mem.size(); ++i)
            if (mem[i].first == key) return &mem[i].second;
        return nullptr;
    }
    double num_of(double def) const { return t == NUM ? num : def; }
};

struct JParser {
    const char* p  = nullptr;
    const char* pe = nullptr;
    int  depth = 0;
    bool bad = false;
    std::string why;

    void ws() {
        while (p < pe && (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r')) ++p;
    }
    void fail(const char* m) { if (!bad) { bad = true; why = m; } }
    bool lit(const char* s) {
        size_t n = std::strlen(s);
        if ((size_t)(pe - p) < n || std::memcmp(p, s, n) != 0) return false;
        p += n;
        return true;
    }
    static void utf8(std::string& out, uint32_t cp) {
        if (cp < 0x80) {
            out += (char)cp;
        } else if (cp < 0x800) {
            out += (char)(0xC0 | (cp >> 6));
            out += (char)(0x80 | (cp & 0x3F));
        } else if (cp < 0x10000) {
            out += (char)(0xE0 | (cp >> 12));
            out += (char)(0x80 | ((cp >> 6) & 0x3F));
            out += (char)(0x80 | (cp & 0x3F));
        } else {
            out += (char)(0xF0 | (cp >> 18));
            out += (char)(0x80 | ((cp >> 12) & 0x3F));
            out += (char)(0x80 | ((cp >> 6) & 0x3F));
            out += (char)(0x80 | (cp & 0x3F));
        }
    }
    bool hex4(uint32_t* out) {
        if (pe - p < 4) return false;
        uint32_t v = 0;
        for (int i = 0; i < 4; ++i) {
            char c = p[i];
            v <<= 4;
            if (c >= '0' && c <= '9')      v |= (uint32_t)(c - '0');
            else if (c >= 'a' && c <= 'f') v |= (uint32_t)(c - 'a' + 10);
            else if (c >= 'A' && c <= 'F') v |= (uint32_t)(c - 'A' + 10);
            else return false;
        }
        p += 4;
        *out = v;
        return true;
    }
    bool jstr(std::string& out) {
        if (p >= pe || *p != '"') return false;
        ++p;
        while (p < pe && *p != '"') {
            char c = *p++;
            if (c != '\\') { out += c; continue; }
            if (p >= pe) return false;
            char e = *p++;
            switch (e) {
                case '"':  out += '"';  break;
                case '\\': out += '\\'; break;
                case '/':  out += '/';  break;
                case 'b':  out += '\b'; break;
                case 'f':  out += '\f'; break;
                case 'n':  out += '\n'; break;
                case 'r':  out += '\r'; break;
                case 't':  out += '\t'; break;
                case 'u': {
                    uint32_t cp;
                    if (!hex4(&cp)) return false;
                    // surrogate pair: a non-BMP codepoint arrives as two
                    if (cp >= 0xD800 && cp <= 0xDBFF &&
                        pe - p >= 6 && p[0] == '\\' && p[1] == 'u') {
                        p += 2;
                        uint32_t lo;
                        if (!hex4(&lo) || lo < 0xDC00 || lo > 0xDFFF) return false;
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                    }
                    utf8(out, cp);
                    break;
                }
                default:
                    return false;
            }
        }
        if (p >= pe) return false;
        ++p;                                       // the closing quote
        return true;
    }
    bool parse(JVal& v) {
        if (++depth > 128) { fail("JSON nested too deep"); return false; }
        ws();
        if (p >= pe) { fail("JSON ended early"); return false; }
        char c = *p;
        if (c == '{') {
            v.t = JVal::OBJ;
            ++p;
            ws();
            if (p < pe && *p == '}') { ++p; --depth; return true; }
            for (;;) {
                ws();
                std::string key;
                if (!jstr(key)) { fail("JSON object key expected"); return false; }
                ws();
                if (p >= pe || *p != ':') { fail("JSON ':' expected"); return false; }
                ++p;
                JVal m;
                if (!parse(m)) return false;
                v.mem.push_back(std::make_pair(key, m));
                ws();
                if (p < pe && *p == ',') { ++p; continue; }
                if (p < pe && *p == '}') { ++p; --depth; return true; }
                fail("JSON ',' or '}' expected");
                return false;
            }
        }
        if (c == '[') {
            v.t = JVal::ARR;
            ++p;
            ws();
            if (p < pe && *p == ']') { ++p; --depth; return true; }
            for (;;) {
                JVal e;
                if (!parse(e)) return false;
                v.arr.push_back(e);
                ws();
                if (p < pe && *p == ',') { ++p; continue; }
                if (p < pe && *p == ']') { ++p; --depth; return true; }
                fail("JSON ',' or ']' expected");
                return false;
            }
        }
        if (c == '"') {
            v.t = JVal::STR;
            if (!jstr(v.str)) { fail("JSON string unterminated"); return false; }
            --depth;
            return true;
        }
        if (lit("true"))  { v.t = JVal::BOOL; v.b = true;  --depth; return true; }
        if (lit("false")) { v.t = JVal::BOOL; v.b = false; --depth; return true; }
        if (lit("null"))  { v.t = JVal::NUL;  --depth; return true; }
        // strict JSON number: strtod alone would also accept nan/inf words
        if (c != '-' && c != '+' && c != '.' &&
            (c < '0' || c > '9')) { fail("JSON value malformed"); return false; }
        {
            char* endp = nullptr;
            double d = std::strtod(p, &endp);
            // endp may rest on the string's null terminator (pe + 1); any
            // further and it walked past the buffer we own
            if (endp == p || endp > pe + 1) { fail("JSON number malformed"); return false; }
            v.t = JVal::NUM;
            v.num = d;
            p = (endp > pe) ? pe : endp;
            --depth;
            return true;
        }
    }
};

// ── glTF 2.0 ───────────────────────────────────────────────────────────────
// POSITION + indices only, mode 4 (TRIANGLES) only, embedded buffers only
// (the GLB bin chunk or a data: URI). Node TRS/matrix transforms compose
// down the scene graph -- a mesh parented at an offset must land where its
// author put it, or the "standing body" the seal cuts is a lie.

size_t comp_size(uint32_t ct) {
    switch (ct) {
        case 5120: case 5121: return 1;    // i8 / u8
        case 5122: case 5123: return 2;    // i16 / u16
        case 5125: case 5126: return 4;    // u32 / f32
        default: return 0;
    }
}

struct GBuffer { const uint8_t* data; size_t len; };

struct GltfCtx {
    const JVal*             root  = nullptr;
    const JVal*             views = nullptr;
    std::vector<GBuffer>    buffers;
    // decoded data-URI payloads; GBuffer holds raw pointers INTO these, so
    // this vector must outlive every accessor read below
    std::vector<std::vector<uint8_t> > owned;
};

const JVal* arr_at(const JVal* arr, int64_t i) {
    if (!arr || arr->t != JVal::ARR || i < 0 || (size_t)i >= arr->arr.size())
        return nullptr;
    return &arr->arr[(size_t)i];
}

// byte pointer of element i of an accessor (stride-aware, bounds-checked:
// a malformed file must not read one byte past its own buffer)
bool accessor_ptr(const GltfCtx& g, const JVal* acc, size_t i, size_t elem,
                  std::string& err, const uint8_t** out) {
    if (!acc || acc->t != JVal::OBJ) { err = "glTF accessor missing"; return false; }
    const JVal* view_ref = acc->find("bufferView");
    if (!view_ref) { err = "glTF accessor without a bufferView"; return false; }
    const JVal* view = arr_at(g.views, (int64_t)view_ref->num_of(-1));
    if (!view) { err = "glTF accessor references a missing bufferView"; return false; }
    int64_t bi = view->find("buffer") ? (int64_t)view->find("buffer")->num_of(-1) : -1;
    if (bi < 0 || (size_t)bi >= g.buffers.size()) {
        err = "glTF bufferView references a missing buffer";
        return false;
    }
    size_t off = view->find("byteOffset") ?
                 (size_t)view->find("byteOffset")->num_of(0) : 0;
    size_t blen = view->find("byteLength") ?
                  (size_t)view->find("byteLength")->num_of(0) : 0;
    const GBuffer& b = g.buffers[(size_t)bi];
    if (off > b.len || blen > b.len - off) {
        err = "glTF bufferView exceeds its buffer range";
        return false;
    }
    size_t aoff = acc->find("byteOffset") ?
                  (size_t)acc->find("byteOffset")->num_of(0) : 0;
    size_t stride = view->find("byteStride") ?
                    (size_t)view->find("byteStride")->num_of(0) : elem;
    if (stride < elem) stride = elem;              // illegal file: be safe
    if (aoff > blen) {
        err = "glTF accessor byteOffset outside its bufferView";
        return false;
    }
    size_t need = aoff + i * stride + elem;
    if (need < aoff || need > blen) {
        err = "glTF accessor element out of bufferView range";
        return false;
    }
    *out = b.data + off + aoff + i * stride;
    return true;
}

uint32_t read_comp(const uint8_t* p, uint32_t ct) {
    switch (ct) {
        case 5120: return (uint32_t)(int32_t)*(const int8_t*)p;
        case 5121: return *p;
        case 5122: return (uint32_t)*(const int16_t*)p;
        case 5123: return *(const uint16_t*)p;
        default:   return *(const uint32_t*)p;     // 5125
    }
}

struct Mat4 { float m[16]; };                      // column-major, glTF style

static Mat4 mat_id() {
    Mat4 r;
    std::memset(r.m, 0, sizeof(r.m));
    r.m[0] = r.m[5] = r.m[10] = r.m[15] = 1.f;
    return r;
}

static Mat4 mat_mul(const Mat4& a, const Mat4& b) {   // a * b (b applied first)
    Mat4 r;
    for (int col = 0; col < 4; ++col)
        for (int row = 0; row < 4; ++row) {
            float s = 0.f;
            for (int k = 0; k < 4; ++k)
                s += a.m[k * 4 + row] * b.m[col * 4 + k];
            r.m[col * 4 + row] = s;
        }
    return r;
}

static Mat4 node_local(const JVal* node) {
    const JVal* mx = node->find("matrix");
    if (mx && mx->t == JVal::ARR && mx->arr.size() == 16) {
        Mat4 r = mat_id();
        for (int i = 0; i < 16; ++i) r.m[i] = (float)mx->arr[(size_t)i].num_of(0);
        return r;
    }
    Mat4 r = mat_id();
    const JVal* t = node->find("translation");
    if (t && t->t == JVal::ARR && t->arr.size() == 3) {
        r.m[12] = (float)t->arr[0].num_of(0);
        r.m[13] = (float)t->arr[1].num_of(0);
        r.m[14] = (float)t->arr[2].num_of(0);
    }
    const JVal* q = node->find("rotation");        // (x, y, z, w) unit quat
    if (q && q->t == JVal::ARR && q->arr.size() == 4) {
        float x = (float)q->arr[0].num_of(0), y = (float)q->arr[1].num_of(0);
        float z = (float)q->arr[2].num_of(0), w = (float)q->arr[3].num_of(1);
        r.m[0] = 1.f - 2.f * (y * y + z * z);
        r.m[1] = 2.f * (x * y + z * w);
        r.m[2] = 2.f * (x * z - y * w);
        r.m[4] = 2.f * (x * y - z * w);
        r.m[5] = 1.f - 2.f * (x * x + z * z);
        r.m[6] = 2.f * (y * z + x * w);
        r.m[8] = 2.f * (x * z + y * w);
        r.m[9] = 2.f * (y * z - x * w);
        r.m[10] = 1.f - 2.f * (x * x + y * y);
    }
    const JVal* s = node->find("scale");
    if (s && s->t == JVal::ARR && s->arr.size() == 3) {
        r.m[0]  *= (float)s->arr[0].num_of(1);
        r.m[5]  *= (float)s->arr[1].num_of(1);
        r.m[10] *= (float)s->arr[2].num_of(1);
    }
    return r;
}

bool base64_decode(const std::string& in, std::vector<uint8_t>& out) {
    static int8_t T[256];
    static bool init = false;
    if (!init) {
        const char* A =
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        for (int i = 0; i < 256; ++i) T[i] = -1;
        for (int i = 0; i < 64; ++i) T[(uint8_t)A[i]] = (int8_t)i;
        init = true;
    }
    uint32_t acc = 0;
    int bits = 0;
    for (size_t i = 0; i < in.size(); ++i) {
        char c = in[i];
        if (c == '=') break;
        int8_t v = T[(uint8_t)c];
        if (v < 0) continue;                       // embedded whitespace
        acc = (acc << 6) | (uint32_t)v;
        bits += 6;
        if (bits >= 8) {
            bits -= 8;
            out.push_back((uint8_t)((acc >> bits) & 0xFF));
        }
    }
    return true;
}

struct NodeWalk {
    const JVal* nodes;
    std::vector<std::pair<int, Mat4> >* out;       // (mesh index, world xform)
    std::string* err;
    bool walk(int64_t ni, const Mat4& parent, int depth) {
        if (depth > 64) {
            *err = "glTF node graph deeper than 64 (cyclic scene?)";
            return false;
        }
        const JVal* node = arr_at(nodes, ni);
        if (!node || node->t != JVal::OBJ) {
            *err = "glTF node index out of range";
            return false;
        }
        Mat4 world = mat_mul(parent, node_local(node));
        const JVal* mesh = node->find("mesh");
        if (mesh && mesh->t == JVal::NUM)
            out->push_back(std::make_pair((int)mesh->num_of(-1), world));
        const JVal* kids = node->find("children");
        if (kids && kids->t == JVal::ARR)
            for (size_t i = 0; i < kids->arr.size(); ++i)
                if (!walk((int64_t)kids->arr[i].num_of(-1), world, depth + 1))
                    return false;
        return true;
    }
};

bool parse_gltf(const std::string& src, RawMesh& m, std::string& err) {
    std::string json;
    std::vector<uint8_t> bin;

    if (src.size() >= 12 && std::memcmp(src.data(), "glTF", 4) == 0) {
        // GLB container: 12-byte header, then chunks (JSON first, optional
        // BIN). The BIN chunk backs buffers that carry no uri.
        uint32_t ver = 0, glen = 0;
        std::memcpy(&ver,  src.data() + 4, 4);
        std::memcpy(&glen, src.data() + 8, 4);
        if (ver != 2) {
            err = "GLB version " + std::to_string(ver) + " is not 2";
            return false;
        }
        size_t limit = (glen && glen <= src.size()) ? (size_t)glen : src.size();
        size_t at = 12;
        while (at + 8 <= limit) {
            uint32_t clen = 0, ctype = 0;
            std::memcpy(&clen,  src.data() + at,     4);
            std::memcpy(&ctype, src.data() + at + 4, 4);
            if ((size_t)clen > limit - (at + 8)) {
                err = "GLB chunk overruns the container";
                return false;
            }
            if (ctype == 0x4E4F534A) {                 // 'JSON'
                json.assign(src.data() + at + 8, (size_t)clen);
            } else if (ctype == 0x004E4942) {          // 'BIN\0'
                bin.assign(src.data() + at + 8,
                           src.data() + at + 8 + (size_t)clen);
            }
            at += 8 + (size_t)clen;
        }
        if (json.empty()) {
            err = "GLB without a JSON chunk";
            return false;
        }
    } else {
        json = src;    // .gltf text: buffers must carry data: URIs
    }

    JVal root;
    {
        JParser jp;
        jp.p  = json.data();
        jp.pe = json.data() + json.size();
        if (!jp.parse(root) || root.t != JVal::OBJ) {
            err = "glTF JSON parse failed: " +
                  (jp.bad ? jp.why : std::string("root is not an object"));
            return false;
        }
    }

    GltfCtx g;
    g.root  = &root;
    g.views = root.find("bufferViews");
    const JVal* buffers = root.find("buffers");
    if (!buffers || buffers->t != JVal::ARR) {
        err = "glTF without a buffers array";
        return false;
    }
    for (size_t i = 0; i < buffers->arr.size(); ++i) {
        const JVal& b = buffers->arr[i];
        const JVal* uri = b.find("uri");
        if (!uri || uri->t != JVal::STR) {
            g.buffers.push_back(GBuffer{bin.data(), bin.size()});
            continue;
        }
        const std::string& u = uri->str;
        size_t comma = u.find(',');
        if (u.compare(0, 5, "data:") != 0 || comma == std::string::npos) {
            err = "glTF external buffer URI not supported (embed the "
                  "buffer or use GLB)";
            return false;
        }
        g.owned.push_back(std::vector<uint8_t>());
        base64_decode(u.substr(comma + 1), g.owned.back());
        g.buffers.push_back(
            GBuffer{g.owned.back().data(), g.owned.back().size()});
    }

    const JVal* nodes     = root.find("nodes");
    const JVal* meshes    = root.find("meshes");
    const JVal* accessors = root.find("accessors");
    if (!nodes || nodes->t != JVal::ARR ||
        !meshes || meshes->t != JVal::ARR ||
        !accessors || accessors->t != JVal::ARR) {
        err = "glTF missing nodes/meshes/accessors";
        return false;
    }

    const JVal* scene_i = root.find("scene");
    const JVal* sc = arr_at(root.find("scenes"),
                            scene_i ? (int64_t)scene_i->num_of(0) : 0);
    const JVal* roots = sc ? sc->find("nodes") : nullptr;
    if (!roots || roots->t != JVal::ARR) {
        err = "glTF scene without nodes";
        return false;
    }

    std::vector<std::pair<int, Mat4> > node_meshes;
    NodeWalk w;
    w.nodes = nodes;
    w.out   = &node_meshes;
    w.err   = &err;
    for (size_t i = 0; i < roots->arr.size(); ++i)
        if (!w.walk((int64_t)roots->arr[i].num_of(-1), mat_id(), 0))
            return false;

    size_t verts_in = m.pos.size() / 3;
    bool any_tri = false;

    for (size_t nm = 0; nm < node_meshes.size(); ++nm) {
        const JVal* mesh = arr_at(meshes, (int64_t)node_meshes[nm].first);
        if (!mesh) { err = "glTF mesh index out of range"; return false; }
        const JVal* prims = mesh->find("primitives");
        if (!prims || prims->t != JVal::ARR) continue;
        const Mat4& W = node_meshes[nm].second;
        for (size_t pi = 0; pi < prims->arr.size(); ++pi) {
            const JVal& prim = prims->arr[pi];
            const JVal* mode = prim.find("mode");
            if (mode && (int)mode->num_of(4) != 4) {
                err = "glTF primitive mode " +
                      std::to_string((int)mode->num_of(0)) +
                      " is not TRIANGLES (4) -- refused";
                return false;
            }
            const JVal* attrs = prim.find("attributes");
            const JVal* pos_ref = attrs ? attrs->find("POSITION") : nullptr;
            const JVal* pacc = pos_ref ?
                arr_at(accessors, (int64_t)pos_ref->num_of(-1)) : nullptr;
            if (!pacc) { err = "glTF primitive without POSITION"; return false; }
            const JVal* pct    = pacc->find("componentType");
            const JVal* ptype  = pacc->find("type");
            const JVal* pcount = pacc->find("count");
            if (!pct || (int)pct->num_of(0) != 5126 || !ptype ||
                ptype->t != JVal::STR || ptype->str != "VEC3" || !pcount) {
                err = "glTF POSITION accessor must be f32 VEC3 with a count";
                return false;
            }
            size_t pv0  = m.pos.size() / 3;
            size_t pnv  = (size_t)pcount->num_of(0);
            if (pnv == 0) { err = "glTF POSITION accessor is empty"; return false; }
            for (size_t i = 0; i < pnv; ++i) {
                const uint8_t* p;
                if (!accessor_ptr(g, pacc, i, 12, err, &p)) return false;
                float x, y, z;
                std::memcpy(&x, p + 0, 4);
                std::memcpy(&y, p + 4, 4);
                std::memcpy(&z, p + 8, 4);
                if (!finite3(x, y, z)) {
                    err = "glTF POSITION holds a non-finite coordinate";
                    return false;
                }
                // column-major M*v: out[row] = sum_col m[col*4+row] * v[col]
                m.pos.push_back(W.m[0]  * x + W.m[4]  * y +
                                W.m[8]  * z + W.m[12]);
                m.pos.push_back(W.m[1]  * x + W.m[5]  * y +
                                W.m[9]  * z + W.m[13]);
                m.pos.push_back(W.m[2]  * x + W.m[6]  * y +
                                W.m[10] * z + W.m[14]);
            }
            if (m.pos.size() / 3 > kMaxVerts) {
                err = "glTF exceeds the vertex limit (" +
                      std::to_string(kMaxVerts) + ")";
                return false;
            }
            const JVal* idx_ref = prim.find("indices");
            if (!idx_ref) {
                // no indices: the vertex sequence IS the triangle soup
                if (pnv % 3 != 0) {
                    err = "glTF non-indexed primitive vertex count is not "
                          "a multiple of 3";
                    return false;
                }
                for (size_t i = 0; i < pnv; ++i)
                    m.idx.push_back((uint32_t)(pv0 + i));
            } else {
                const JVal* iacc = arr_at(accessors,
                                          (int64_t)idx_ref->num_of(-1));
                if (!iacc) { err = "glTF indices accessor missing"; return false; }
                const JVal* ict    = iacc->find("componentType");
                const JVal* icount = iacc->find("count");
                uint32_t ict_n = ict ? (uint32_t)ict->num_of(0) : 0;
                if (!icount || ict_n == 5126 || comp_size(ict_n) == 0) {
                    err = "glTF indices accessor componentType must be "
                          "u8/u16/u32 with a count";
                    return false;
                }
                size_t nin = (size_t)icount->num_of(0);
                if (nin % 3 != 0) {
                    err = "glTF indices count is not a multiple of 3";
                    return false;
                }
                size_t esz = comp_size(ict_n);
                for (size_t i = 0; i < nin; ++i) {
                    const uint8_t* p;
                    if (!accessor_ptr(g, iacc, i, esz, err, &p)) return false;
                    uint32_t v = read_comp(p, ict_n);
                    if ((size_t)v >= pnv) {
                        err = "glTF index out of the primitive's vertex range";
                        return false;
                    }
                    m.idx.push_back((uint32_t)(pv0 + v));
                }
            }
            if (m.idx.size() / 3 > kMaxTris) {
                err = "glTF exceeds the triangle limit (" +
                      std::to_string(kMaxTris) + ")";
                return false;
            }
            any_tri = true;
        }
    }
    if (!any_tri || m.pos.size() / 3 == verts_in) {
        err = "glTF contains no triangle primitive";
        return false;
    }
    return true;
}

// ── THE DIVERGENCE CLOSURE (the prereg's named falsifier) ──────────────────
// A sealable body is a CLOSED oriented surface: every directed edge (a->b)
// matched by exactly one (b->a). With closure proven, the divergence sum
// V = sum(dot(a, cross(b, c)))/6 IS the enclosed volume -- that identity is
// the consistency check; a leaky mesh can invoke it on nothing, which is
// exactly why it is refused here instead of sealing.
bool finish(RawMesh& m, std::string& body, Stats& st, std::string& err) {
    const size_t nv = m.pos.size() / 3;
    const size_t nt = m.idx.size() / 3;
    if (nv == 0 || nt == 0) {
        err = "mesh has no triangles";
        return false;
    }
    for (size_t i = 0; i < m.idx.size(); ++i)
        if ((size_t)m.idx[i] >= nv) {
            err = "face index " + std::to_string(m.idx[i]) +
                  " out of vertex range";
            return false;
        }

    float lo[3] = { 1e30f,  1e30f,  1e30f};
    float hi[3] = {-1e30f, -1e30f, -1e30f};
    for (size_t i = 0; i < nv; ++i)
        for (int d = 0; d < 3; ++d) {
            float c = m.pos[i * 3 + (size_t)d];
            if (c < lo[d]) lo[d] = c;
            if (c > hi[d]) hi[d] = c;
        }
    float scale = hi[0] - lo[0];
    for (int d = 1; d < 3; ++d) scale = std::max(scale, hi[d] - lo[d]);
    if (!(scale > 0.f) || !std::isfinite(scale)) {
        err = "degenerate bounds: the mesh occupies zero extent";
        return false;
    }

    // key = (min<<32)|max, value = (forward count, backward count)
    std::unordered_map<uint64_t, std::pair<uint32_t, uint32_t> > edge;
    edge.reserve(nt * 3);
    for (size_t t = 0; t < nt; ++t) {
        uint32_t tri[3] = {m.idx[t * 3], m.idx[t * 3 + 1], m.idx[t * 3 + 2]};
        if (tri[0] == tri[1] || tri[1] == tri[2] || tri[2] == tri[0]) {
            err = "degenerate triangle (repeated indices) at triangle " +
                  std::to_string(t);
            return false;
        }
        for (int e = 0; e < 3; ++e) {
            uint32_t a = tri[e], b = tri[(e + 1) % 3];
            uint64_t key = a < b ? (((uint64_t)a << 32) | (uint64_t)b)
                                 : (((uint64_t)b << 32) | (uint64_t)a);
            std::pair<uint32_t, uint32_t>& c = edge[key];
            if (a < b) ++c.first; else ++c.second;
        }
    }
    size_t boundary = 0;
    for (auto it = edge.begin(); it != edge.end(); ++it) {
        const std::pair<uint32_t, uint32_t>& c = it->second;
        size_t total = (size_t)c.first + (size_t)c.second;
        if (total == 1) { ++boundary; continue; }      // an open border
        if (total > 2) {
            err = "non-manifold edge touched by more than two triangles";
            return false;
        }
        if (c.first != 1 || c.second != 1) {           // two same-direction
            err = "inconsistent winding: an edge is not shared by exactly "
                  "one triangle per side";
            return false;
        }
    }
    if (boundary) {
        err = "mesh not closed: " + std::to_string(boundary) +
              " boundary edges (leaky/open surface refused -- the seal "
              "cuts a closed body or nothing)";
        return false;
    }

    double vol = 0.0;
    for (size_t t = 0; t < nt; ++t) {
        double ax = m.pos[(size_t)m.idx[t * 3 + 0] * 3 + 0];
        double ay = m.pos[(size_t)m.idx[t * 3 + 0] * 3 + 1];
        double az = m.pos[(size_t)m.idx[t * 3 + 0] * 3 + 2];
        double bx = m.pos[(size_t)m.idx[t * 3 + 1] * 3 + 0];
        double by = m.pos[(size_t)m.idx[t * 3 + 1] * 3 + 1];
        double bz = m.pos[(size_t)m.idx[t * 3 + 1] * 3 + 2];
        double cx = m.pos[(size_t)m.idx[t * 3 + 2] * 3 + 0];
        double cy = m.pos[(size_t)m.idx[t * 3 + 2] * 3 + 1];
        double cz = m.pos[(size_t)m.idx[t * 3 + 2] * 3 + 2];
        vol += (ax * (by * cz - bz * cy) -
                ay * (bx * cz - bz * cx) +
                az * (bx * cy - by * cx)) / 6.0;
    }
    double bbox_vol = (double)(hi[0] - lo[0]) * (double)(hi[1] - lo[1]) *
                      (double)(hi[2] - lo[2]);
    double eps = bbox_vol * 1e-6;
    double s3 = (double)scale * (double)scale * (double)scale;
    if (!(eps > 0.0)) eps = s3 * 1e-9;
    if (!(std::fabs(vol) > eps)) {
        err = "zero enclosed volume (divergence |V| = " +
              std::to_string(std::fabs(vol)) + " vs epsilon " +
              std::to_string(eps) + ") -- a flat or self-canceling "
              "surface cannot seal";
        return false;
    }
    if (vol < 0.0) {
        // inward source winding: the source's convention is taste, the
        // SIGN of V is physics -- flip to outward
        for (size_t t = 0; t < nt; ++t)
            std::swap(m.idx[t * 3 + 1], m.idx[t * 3 + 2]);
        vol = -vol;
        st.winding_flipped = true;
    }

    // center at the origin: the seal plane cuts a STANDING body at
    // mid-height, and the engine's camera targets the origin
    float ctr[3];
    for (int d = 0; d < 3; ++d) ctr[d] = 0.5f * (lo[d] + hi[d]);
    for (size_t i = 0; i < nv; ++i)
        for (int d = 0; d < 3; ++d) m.pos[i * 3 + (size_t)d] -= ctr[d];

    // area-weighted vertex normals: the cross product's magnitude IS the
    // triangle area, so summing raw cross products weights by area
    std::vector<float> nrm(m.pos.size(), 0.f);
    for (size_t t = 0; t < nt; ++t) {
        size_t a = (size_t)m.idx[t * 3 + 0] * 3;
        size_t b = (size_t)m.idx[t * 3 + 1] * 3;
        size_t c = (size_t)m.idx[t * 3 + 2] * 3;
        float ux = m.pos[b + 0] - m.pos[a + 0];
        float uy = m.pos[b + 1] - m.pos[a + 1];
        float uz = m.pos[b + 2] - m.pos[a + 2];
        float vx = m.pos[c + 0] - m.pos[a + 0];
        float vy = m.pos[c + 1] - m.pos[a + 1];
        float vz = m.pos[c + 2] - m.pos[a + 2];
        float nx = uy * vz - uz * vy;
        float ny = uz * vx - ux * vz;
        float nz = ux * vy - uy * vx;
        size_t ids[3] = {a, b, c};
        for (int k = 0; k < 3; ++k) {
            nrm[ids[k] + 0] += nx;
            nrm[ids[k] + 1] += ny;
            nrm[ids[k] + 2] += nz;
        }
    }

    // the full mesh format (little-endian, the /mesh_bin payload):
    //   [u32 N][u32 idxCount][f32 cam_radius][f32 cam_theta][f32 cam_phi]
    //   [f32 slotmode][f32 * N * 9][u32 * idxCount]
    float radius = 2.2f * (0.5f * scale) + 1e-3f;  // fit: whole body in view
    float theta = 0.0f, phi = 0.3f, slotmode = 0.0f;   // slot 0 = cell field
    auto put = [&body](const void* p, size_t n) {
        body.append(reinterpret_cast<const char*>(p), n);
    };
    uint32_t N  = (uint32_t)nv;
    uint32_t IC = (uint32_t)(nt * 3);
    put(&N, 4); put(&IC, 4);
    put(&radius, 4); put(&theta, 4); put(&phi, 4); put(&slotmode, 4);
    for (size_t i = 0; i < nv; ++i) {
        put(&m.pos[i * 3 + 0], 4);
        put(&m.pos[i * 3 + 1], 4);
        put(&m.pos[i * 3 + 2], 4);
        float x = nrm[i * 3 + 0], y = nrm[i * 3 + 1], z = nrm[i * 3 + 2];
        float len = std::sqrt(x * x + y * y + z * z);
        if (len > 1e-20f) { x /= len; y /= len; z /= len; }
        else              { x = 0.f; y = 1.f; z = 0.f; }   // isolated pole
        put(&x, 4); put(&y, 4); put(&z, 4);
        put(kTan, 12);
    }
    put(m.idx.data(), m.idx.size() * 4);

    st.verts = N;
    st.tris  = (uint32_t)nt;
    st.volume = vol;
    st.ymin = lo[1] - ctr[1];
    st.ymax = hi[1] - ctr[1];
    return true;
}

}  // namespace

bool import_mesh(char kind, const std::string& src,
                 std::string& body, Stats& st, std::string& err) {
    RawMesh m;
    bool ok = false;
    if (src.empty()) {
        err = "empty source bytes after the kind prefix";
    } else if (kind == 'O') {
        ok = parse_obj(src, m, err);
    } else if (kind == 'G') {
        ok = parse_gltf(src, m, err);
    } else {
        err = "unknown source kind: the first byte must be 'O' (OBJ) "
              "or 'G' (glTF)";
    }
    if (!ok) {
        if (err.empty()) err = "import failed without a named cause";
        return false;
    }
    return finish(m, body, st, err);
}

}  // namespace importer
