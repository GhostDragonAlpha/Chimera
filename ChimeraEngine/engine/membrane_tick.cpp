
#include "membrane_tick.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <map>
#include <set>
#include <sstream>
#include <utility>

namespace {

constexpr float ANKLE_X_L = 0.4609f;   // measured ankle x (FEET prereg)
constexpr float ANKLE_X_R = -0.4609f;

std::array<float, 3> centroid(const std::vector<float>& v9,
                              uint32_t a, uint32_t b, uint32_t c) {
    return {(v9[a * 9 + 0] + v9[b * 9 + 0] + v9[c * 9 + 0]) / 3.f,
            (v9[a * 9 + 1] + v9[b * 9 + 1] + v9[c * 9 + 1]) / 3.f,
            (v9[a * 9 + 2] + v9[b * 9 + 2] + v9[c * 9 + 2]) / 3.f};
}

float tri_area(const std::vector<float>& v9,
               uint32_t a, uint32_t b, uint32_t c) {
    float ux = v9[b*9+0] - v9[a*9+0], uy = v9[b*9+1] - v9[a*9+1], uz = v9[b*9+2] - v9[a*9+2];
    float wx = v9[c*9+0] - v9[a*9+0], wy = v9[c*9+1] - v9[a*9+1], wz = v9[c*9+2] - v9[a*9+2];
    float cx = uy * wz - uz * wy, cy = uz * wx - ux * wz, cz = ux * wy - uy * wx;
    return 0.5f * std::sqrt(cx * cx + cy * cy + cz * cz);
}

// THE SEAL v2 slot read: slots below nv are original vertices (pos9,
// 9 floats each); slots nv+k are inserted cut points riding edge
// (a,b) at fixed t — their CURRENT positions live in cutpos (3 each).
void slot_read(const std::vector<float>& pos9, uint32_t nv,
               const std::vector<float>& cutpos, uint32_t s,
               float* x, float* y, float* z) {
    if (s < nv) {
        *x = pos9[s * 9 + 0]; *y = pos9[s * 9 + 1]; *z = pos9[s * 9 + 2];
    } else {
        size_t i = (size_t)(s - nv) * 3;
        *x = cutpos[i]; *y = cutpos[i + 1]; *z = cutpos[i + 2];
    }
}

}  // namespace

void MembraneTick::init(uint32_t tris, const std::vector<uint32_t>& indices,
                        const std::vector<float>& verts9) {
    // build into locals, commit atomically: the frame loop may call step()
    // while this runs (boot restore thread vs render thread)
    ready_.store(false, std::memory_order_release);

    std::vector<Cell> cells(tris, Cell{});
    std::vector<uint32_t> tri_verts(indices.begin(), indices.end());
    std::vector<float> capacity(tris);
    std::vector<uint8_t> foot(tris, 0);
    std::vector<std::vector<uint32_t>> neighbors(tris);

    std::map<std::pair<uint32_t, uint32_t>, std::vector<uint32_t>> edges;
    for (uint32_t t = 0; t < tris; ++t) {
        uint32_t a = indices[t * 3 + 0], b = indices[t * 3 + 1], cc = indices[t * 3 + 2];
        std::pair<uint32_t, uint32_t> e[3] = {{std::min(a,b), std::max(a,b)},{std::min(b,cc), std::max(b,cc)},{std::min(cc,a), std::max(cc,a)}};
        for (auto& k : e) edges[k].push_back(t);
        capacity[t] = yield_pa_ * tri_area(verts9, a, b, cc);
        foot[t] = (centroid(verts9, a, b, cc)[0] >= 0.f) ? 0u : 1u;
    }
    for (auto& [e, ts] : edges)
        for (size_t i = 0; i + 1 < ts.size(); ++i)
            for (size_t j = i + 1; j < ts.size(); ++j) {
                neighbors[ts[i]].push_back(ts[j]);
                neighbors[ts[j]].push_back(ts[i]);
            }

        // colors + authored rest into locals as well
    std::vector<float> base_color(verts9.size() / 9 * 3, 0.f);
    for (size_t v = 0; v < verts9.size() / 9; ++v)
        for (int kk = 0; kk < 3; ++kk)
            base_color[v * 3 + (size_t)kk] = verts9[v * 9 + 6 + (size_t)kk];
    std::vector<float> base_pos(verts9);   // authored rest (full copy)

    // ankle pivots: the collar-ring center of each foot (top region)
    std::array<std::array<float, 3>, 2> pivots = {};
    for (int f = 0; f < 2; ++f) {
        float sx = 0, sy = 0, sz = 0; int cnt = 0;
        for (size_t v = 0; v < verts9.size() / 9; ++v) {
            float vx = verts9[v * 9 + 0], vy = verts9[v * 9 + 1], vz = verts9[v * 9 + 2];
            bool left = f == 0;
            if ((left && vx >= 0.f) || (!left && vx < 0.f)) {
                if (vy >= 0.25f) { sx += vx; sy += vy; sz += vz; ++cnt; }
            }
        }
        if (cnt > 0) {
            pivots[f][0] = sx / cnt; pivots[f][1] = sy / cnt; pivots[f][2] = sz / cnt;
        } else {
            pivots[f][0] = f == 0 ? ANKLE_X_L : ANKLE_X_R;
            pivots[f][1] = 0.30f; pivots[f][2] = 0.0f;
        }
    }

    // commit atomically
    cells_ = std::move(cells);
    tri_verts_ = std::move(tri_verts);
    capacity_ = std::move(capacity);
    foot_ = std::move(foot);
    neighbors_ = std::move(neighbors);
    base_pos_ = base_pos;
    base_color_ = std::move(base_color);
    pivot_[0] = pivots[0];
    pivot_[1] = pivots[1];
    has_scene_ = tris > 0;
    ticks_ = 0;
    force_l_ = force_r_ = 0.f;
    flex_l_ = flex_r_ = 0.f;
    ready_.store(true, std::memory_order_release);
}

bool MembraneTick::intent(float force_n, const std::string& foot) {
    if (!std::isfinite(force_n) || force_n <= 0.f) return false;
    if (foot == "L") { force_l_ = force_n; return true; }
    if (foot == "R") { force_r_ = force_n; return true; }
    return false;
}

void MembraneTick::clear_intent() { force_l_ = force_r_ = 0.f; }

bool MembraneTick::flex(float deg_l, float deg_r) {
    if (!std::isfinite(deg_l) || !std::isfinite(deg_r)) return false;
    if (std::fabs(deg_l) > 90.f || std::fabs(deg_r) > 90.f) return false;
    flex_l_ = deg_l * 3.14159265358979f / 180.f;
    flex_r_ = deg_r * 3.14159265358979f / 180.f;
    return true;
}

void MembraneTick::apply_flex(std::vector<float>& verts9) {
    if (flex_l_ == 0.f && flex_r_ == 0.f) {
        if (!std::equal(base_pos_.begin(), base_pos_.end(), verts9.begin()))
            verts9 = base_pos_;
        return;
    }
    const uint32_t nv = (uint32_t)(verts9.size() / 9);
    for (uint32_t v = 0; v < nv; ++v) {
        bool left = verts9[v * 9 + 0] >= 0.f;
        float ang = left ? flex_l_ : flex_r_;
        const auto& pv = pivot_[left ? 0 : 1];
        // authored rest position, rotated rigidly about the pivot (X axis)
        float bx = base_pos_[v * 9 + 0] - pv[0];
        float by = base_pos_[v * 9 + 1] - pv[1];
        float bz = base_pos_[v * 9 + 2] - pv[2];
        float cy = std::cos(ang), sy = std::sin(ang);   // rotate in the YZ plane
        float ry = by * cy - bz * sy;
        float rz = by * sy + bz * cy;
        verts9[v * 9 + 0] = bx + pv[0];
        verts9[v * 9 + 1] = ry + pv[1];
        verts9[v * 9 + 2] = rz + pv[2];
    }
}

void MembraneTick::apply_travel(std::vector<float>& verts9,
                                const std::vector<float>* deg) const {
    // classified smooth travel, verbatim: each vertex mixes the poses of
    // its 3 nearest pins by its stored weights; deg == nullptr -> all
    // angles 0 (the exact rest blend). Shared by step() and seal() so
    // v0 and the live volume run the SAME arithmetic path.
    const size_t nv = verts9.size() / 9;
    for (size_t v = 0; v < nv; ++v) {
        float px = 0.f, py = 0.f, pz = 0.f;
        // blend source is the AUTHORED BASE: deterministic per tick
        float ox = base_pos_[v * 9 + 0], oy = base_pos_[v * 9 + 1], oz = base_pos_[v * 9 + 2];
        for (int k = 0; k < 3; ++k) {
            uint8_t j = vert_bind_idx_[v * 3 + (size_t)k];
            float w = vert_bind_w_[v * 3 + (size_t)k];
            float th = deg ? (*deg)[j] : 0.f;
            const auto& pv = joint_pins_[j];
            float bx = ox - pv[0], by = oy - pv[1], bz = oz - pv[2];
            float cth = std::cos(th), sth = std::sin(th);
            px += w * (bx + pv[0]);
            py += w * (by * cth - bz * sth + pv[1]);
            pz += w * (by * sth + bz * cth + pv[2]);
        }
        verts9[v * 9 + 0] = px;
        verts9[v * 9 + 1] = py;
        verts9[v * 9 + 2] = pz;
    }
}

void MembraneTick::step(std::vector<float>& verts9) {
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return;
    if (tri_verts_.size() != cells_.size() * 3) return;   // hardened
    ++ticks_;

    const bool classified = cell_joint_.size() == cells_.size()
                         && joint_pins_.size() == joint_deg_.size()
                         && vert_bind_idx_.size() == verts9.size() / 9 * 3
                         && vert_bind_w_.size() == verts9.size() / 9 * 3;

    // TRAVEL: blended per-vertex travel -- each vertex mixes the poses of
    // its 3 nearest pins by its stored weights. The surface BENDS; it
    // never tears (that was the rigid-pin method, rejected by the operator).
    if (classified) {
        apply_travel(verts9, &joint_deg_);
    } else if (!rig_.empty()) {
        apply_chain(verts9);
    } else {
        apply_flex(verts9);
    }

    // PRESS (force known): spread over the cells of the pressed group
    if (classified && !joint_force_.empty()) {
        std::vector<float> cnt(joint_pins_.size(), 0.f);
        for (size_t i = 0; i < cells_.size(); ++i)
            if (!cells_[i].failed) cnt[cell_joint_[i]] += 1.f;
        for (size_t i = 0; i < cells_.size(); ++i) {
            Cell& c = cells_[i];
            uint8_t jg = cell_joint_[i];
            c.load = (cnt[jg] > 0.f && !c.failed) ? joint_force_[jg] / cnt[jg] : 0.f;
        }
        // tensile (B3): overloaded cells shed the excess, half per neighbor
        for (size_t i = 0; i < cells_.size(); ++i) {
            Cell& c = cells_[i];
            if (c.failed || c.load <= capacity_[i]) continue;
            float give = (c.load - capacity_[i]) * 0.5f;
            c.load -= give;
            float share = give / std::max(1.f, (float)neighbors_[i].size());
            for (uint32_t nb : neighbors_[i])
                if (!cells_[nb].failed) cells_[nb].load += share;
        }
    }

    // damage + failure (computed, never scripted)
    for (size_t i = 0; i < cells_.size(); ++i) {
        Cell& c = cells_[i];
        if (c.failed) { c.load = 0.f; continue; }
        if (c.load > capacity_[i])
            c.damage += (c.load - capacity_[i]) / capacity_[i];
        if (c.damage >= 1.f) { c.failed = true; c.load = 0.f; }
    }

    // visibility: load tints toward red; failed cells go dark
    for (size_t i = 0; i < cells_.size(); ++i) {
        const Cell& c = cells_[i];
        float t = c.failed ? 0.f
                : std::min(1.f, c.load / std::max(capacity_[i], 1.f));
        for (int k = 0; k < 3; ++k) {
            uint32_t v = tri_verts_[i * 3 + (size_t)k];
            float base = base_color_[v * 3 + (size_t)k];
            float out;
            if (c.failed)    out = 0.08f;
            else if (k == 0) out = base + (1.f - base) * t;
            else             out = base * (1.f - t * 0.85f);
            verts9[v * 9 + 6 + (size_t)k] = std::min(out, 1.f);
        }
    }
    // THE SEAL v2 (cut-and-weld): cut slots ride their edges at fixed t,
    // so the daughters' boundaries stay closed while the surface moves.
    // Each daughter's divergence sum is a true volume, and their sum must
    // equal the posed whole-mesh volume — conservation is the weld's bar.
    if (sealed_) {
        cut_pos_.resize(cut_src_.size() * 3);
        for (size_t i = 0; i < cut_src_.size(); ++i) {
            const SealSlot& c = cut_src_[i];
            for (int k = 0; k < 3; ++k)
                cut_pos_[i * 3 + k] = verts9[c.a * 9 + k] * (1.f - c.t)
                                    + verts9[c.b * 9 + k] * c.t;
        }
        auto div6 = [&](uint32_t s0, uint32_t s1, uint32_t s2) -> float {
            float ax, ay, az, bx, by, bz, cx, cy, cz;
            slot_read(verts9, seal_nv_, cut_pos_, s0, &ax, &ay, &az);
            slot_read(verts9, seal_nv_, cut_pos_, s1, &bx, &by, &bz);
            slot_read(verts9, seal_nv_, cut_pos_, s2, &cx, &cy, &cz);
            return (ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz)
                  + az * (bx * cy - by * cx)) / 6.f;
        };
        float vl = 0.f, vu = 0.f;
        for (size_t i = 0; i + 2 < seal_lower_.size(); i += 3)
            vl += div6(seal_lower_[i], seal_lower_[i + 1], seal_lower_[i + 2]);
        for (size_t i = 0; i + 2 < seal_upper_.size(); i += 3)
            vu += div6(seal_upper_[i], seal_upper_[i + 1], seal_upper_[i + 2]);
        float vw = 0.f;
        for (size_t i = 0; i + 2 < tri_verts_.size(); i += 3) {
            uint32_t a = tri_verts_[i], b = tri_verts_[i + 1], cc2 = tri_verts_[i + 2];
            vw += (verts9[a*9+0] * (verts9[b*9+1] * verts9[cc2*9+2] - verts9[b*9+2] * verts9[cc2*9+1])
                 + verts9[a*9+1] * (verts9[b*9+2] * verts9[cc2*9+0] - verts9[b*9+0] * verts9[cc2*9+2])
                 + verts9[a*9+2] * (verts9[b*9+0] * verts9[cc2*9+1] - verts9[b*9+1] * verts9[cc2*9+0])) / 6.f;
        }
        vol_lower_ = vl; vol_upper_ = vu; vol_whole_ = vw;
        conserve_pct_ = vw != 0.f ? (vl + vu - vw) / vw * 100.f : 0.f;
        p_lower_ = (v0_lower_ - vl) / (kappa_ * v0_lower_);
        p_upper_ = (v0_upper_ - vu) / (kappa_ * v0_upper_);
    }
}

bool MembraneTick::intent_joint(int idx, float force_n) {
    if (!std::isfinite(force_n) || force_n <= 0.f) return false;
    if (idx < 0 || idx >= (int)joint_force_.size()) return false;
    joint_force_[idx] = force_n;
    return true;
}

bool MembraneTick::load_classify(const std::string& body) {
    if (body.size() < 4) return false;
    uint32_t n = 0;
    std::memcpy(&n, body.data(), 4);
    if (body.size() != 4 + n) return false;
    if (n != cells_.size()) return false;   // one type per triangle cell
    cell_joint_.assign(body.begin() + 4, body.end());
    return true;
}

bool MembraneTick::load_vertbind(const std::string& body) {
    // smooth-travel binding: per vertex, 3 pin indices (u8) and 3
    // normalized weights (f32) -- 15 bytes per vertex. The membrane
    // BENDS by blending the pins' rotations; it never tears.
    if (body.size() < 4) return false;
    uint32_t n = 0;
    std::memcpy(&n, body.data(), 4);
    if (body.size() != 4 + n * 15) return false;
    if (n != verts_expected()) return false;
    vert_bind_idx_.assign(n * 3, 0);
    vert_bind_w_.resize(n * 3);
    const uint8_t* src = reinterpret_cast<const uint8_t*>(body.data()) + 4;
    for (uint32_t v = 0; v < n; ++v) {
        const uint8_t* row = src + v * 15;
        for (int k = 0; k < 3; ++k) vert_bind_idx_[v * 3 + (size_t)k] = row[k];
        std::memcpy(&vert_bind_w_[v * 3], src + v * 15 + 3, 12);
    }
    return true;
}

bool MembraneTick::load_joint_pins(const std::string& body) {
    if (body.size() < 4) return false;
    uint32_t n = 0;
    std::memcpy(&n, body.data(), 4);
    if (n == 0 || body.size() != 4 + n * 12) return false;
    joint_pins_.clear();
    joint_deg_.assign(n, 0.f);
    joint_force_.assign(n, 0.f);
    for (uint32_t i = 0; i < n; ++i) {
        float x, y, z;
        std::memcpy(&x, body.data() + 4 + i * 12 + 0, 4);
        std::memcpy(&y, body.data() + 4 + i * 12 + 4, 4);
        std::memcpy(&z, body.data() + 4 + i * 12 + 8, 4);
        joint_pins_.push_back({x, y, z});
    }
    return true;
}

bool MembraneTick::pose_index(int idx, float deg) {
    if (idx < 0 || idx >= (int)joint_deg_.size()) return false;
    if (!std::isfinite(deg) || std::fabs(deg) > 90.f) return false;
    joint_deg_[idx] = deg * 3.14159265358979f / 180.f;
    return true;
}


bool MembraneTick::load_rig(const std::string& config) {
    // line format: name|start|count|px|py|pz|parent   (parents first)
    std::vector<RigPart> parts;
    size_t pos = 0;
    while (pos <= config.size()) {
        size_t eol = config.find(char(10), pos);
        if (eol == std::string::npos) eol = config.size();
        std::string line = config.substr(pos, eol - pos);
        pos = eol + 1;
        if (line.empty()) continue;
        std::vector<std::string> f;
        size_t p2 = 0;
        while (true) {
            size_t bar = line.find(char(124), p2);
            if (bar == std::string::npos) { f.push_back(line.substr(p2)); break; }
            f.push_back(line.substr(p2, bar - p2));
            p2 = bar + 1;
        }
        if (f.size() < 7) continue;
        RigPart part;
        part.joint = f[0];
        part.start = (uint32_t)std::strtoul(f[1].c_str(), nullptr, 10);
        part.count = (uint32_t)std::strtoul(f[2].c_str(), nullptr, 10);
        part.pivot[0] = std::strtof(f[3].c_str(), nullptr);
        part.pivot[1] = std::strtof(f[4].c_str(), nullptr);
        part.pivot[2] = std::strtof(f[5].c_str(), nullptr);
        part.parent = (int)std::strtol(f[6].c_str(), nullptr, 10);
        parts.push_back(part);
    }
    if (parts.empty()) return false;
    rig_ = parts;
    rig_angle_.assign(rig_.size(), 0.f);
    return true;
}

bool MembraneTick::pose(const std::string& joint, float deg) {
    if (!std::isfinite(deg) || std::fabs(deg) > 90.f) return false;
    for (size_t i = 0; i < rig_.size(); ++i) {
        if (rig_[i].joint == joint) {
            rig_angle_[i] = deg * 3.14159265358979f / 180.f;
            return true;
        }
    }
    return false;
}

void MembraneTick::apply_chain(std::vector<float>& verts9) {
    bool all_zero = true;
    for (float a : rig_angle_)
        if (a != 0.f) { all_zero = false; break; }
    if (all_zero) {
        if (verts9 != base_pos_) verts9 = base_pos_;
        return;
    }
    struct Xf { float th; std::array<float, 3> piv; };
    std::vector<Xf> xf(rig_.size());
    for (size_t i = 0; i < rig_.size(); ++i) {
        float th = rig_angle_[i];
        std::array<float, 3> piv = rig_[i].pivot;
        int parent = rig_[i].parent;
        if (parent >= 0 && parent < (int)i) {
            th += xf[parent].th;
            float by = piv[1] - xf[parent].piv[1];
            float bz = piv[2] - xf[parent].piv[2];
            float cth = std::cos(xf[parent].th), sth = std::sin(xf[parent].th);
            piv[1] = xf[parent].piv[1] + by * cth - bz * sth;
            piv[2] = xf[parent].piv[2] + by * sth + bz * cth;
        }
        xf[i] = {th, piv};
    }
    const uint32_t nv = (uint32_t)(verts9.size() / 9);
    for (size_t i = 0; i < rig_.size(); ++i) {
        float th = xf[i].th, cth = std::cos(th), sth = std::sin(th);
        const auto& pv = xf[i].piv;
        for (uint32_t v = rig_[i].start; v < rig_[i].start + rig_[i].count && v < nv; ++v) {
            float bx = verts9[v * 9 + 0] - pv[0];
            float by = verts9[v * 9 + 1] - pv[1];
            float bz = verts9[v * 9 + 2] - pv[2];
            verts9[v * 9 + 0] = bx + pv[0];
            verts9[v * 9 + 1] = by * cth - bz * sth + pv[1];
            verts9[v * 9 + 2] = by * sth + bz * cth + pv[2];
        }
    }
}

bool MembraneTick::seal(float y) {
    // THE SEAL v2 — the cut-and-weld (prereg 4eb9480c). The v1 floating
    // disc is REPLACED: straddling triangles split at the plane, the cut
    // segments chain into the cross-section loops, and each loop is
    // capped twice (both windings) so both daughters are closed surfaces.
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return false;
    if (!std::isfinite(y)) return false;
    if (sealed_) return false;   // one seal per creature
    if (tri_verts_.size() != cells_.size() * 3) return false;
    const uint32_t nv = (uint32_t)(base_pos_.size() / 9);
    if (nv == 0) return false;

    // rest9: the verts the tick ITSELF produces at rest — the classified
    // blend with all angles 0, the same arithmetic path step() runs per
    // frame. v0 measured on these floats makes the rest dV exactly 0
    // (base_pos_ differs from the blended rest by float32 rounding,
    // which kappa amplifies into ~kPa of phantom pressure).
    std::vector<float> rest9(base_pos_);
    {
        const bool classified = cell_joint_.size() == cells_.size()
                             && joint_pins_.size() == joint_deg_.size()
                             && vert_bind_idx_.size() == (size_t)nv * 3
                             && vert_bind_w_.size() == (size_t)nv * 3;
        if (classified) apply_travel(rest9, nullptr);
    }

    // the plane must cross the body (authored rest pose)
    float ymin = 1e30f, ymax = -1e30f;
    for (uint32_t v = 0; v < nv; ++v) {
        float yy = rest9[v * 9 + 1];
        ymin = std::min(ymin, yy);
        ymax = std::max(ymax, yy);
    }
    if (y <= ymin || y >= ymax) return false;   // seal outside the body

    // CUT: split every straddling triangle; cut slots ride their edges at
    // fixed t. Segment direction follows the BELOW-piece boundary walk, so
    // chained loops inherit the surface winding (both daughters sign+).
    std::map<std::pair<uint32_t, uint32_t>, uint32_t> cut_id;
    std::vector<SealSlot> cut_src;
    std::vector<uint32_t> lower, upper;         // 3 slots per piece
    std::vector<std::pair<uint32_t, uint32_t>> segs;
    int split = 0;
    auto edge_cut = [&](uint32_t va, uint32_t vb, uint32_t* out) -> bool {
        float ya = rest9[va * 9 + 1], yb = rest9[vb * 9 + 1];
        if (ya >= yb) { std::swap(va, vb); std::swap(ya, yb); }
        if (!(ya < y && y <= yb)) return false; // not a crossing edge
        auto key = std::make_pair(std::min(va, vb), std::max(va, vb));
        auto it = cut_id.find(key);
        if (it != cut_id.end()) { *out = it->second; return true; }
        float t = (y - ya) / (yb - ya);
        uint32_t id = nv + (uint32_t)cut_src.size();
        cut_id[key] = id;
        cut_src.push_back({va, vb, t});
        *out = id;
        return true;
    };
    for (size_t i = 0; i < cells_.size(); ++i) {
        uint32_t vs[3] = {tri_verts_[i * 3 + 0], tri_verts_[i * 3 + 1],
                          tri_verts_[i * 3 + 2]};
        bool bl[3] = {rest9[vs[0] * 9 + 1] < y,
                      rest9[vs[1] * 9 + 1] < y,
                      rest9[vs[2] * 9 + 1] < y};
        int nb = (bl[0] ? 1 : 0) + (bl[1] ? 1 : 0) + (bl[2] ? 1 : 0);
        if (nb == 3) {
            lower.push_back(vs[0]); lower.push_back(vs[1]); lower.push_back(vs[2]);
            continue;
        }
        if (nb == 0) {
            upper.push_back(vs[0]); upper.push_back(vs[1]); upper.push_back(vs[2]);
            continue;
        }
        ++split;
        if (nb == 1) {
            // one below (A); the below piece is (A, Pab, Pca)
            int iA = bl[0] ? 0 : (bl[1] ? 1 : 2);
            uint32_t A = vs[iA], B = vs[(iA + 1) % 3], C = vs[(iA + 2) % 3];
            uint32_t pab = 0, pca = 0;
            if (!edge_cut(A, B, &pab) || !edge_cut(C, A, &pca)) return false;
            lower.push_back(A); lower.push_back(pab); lower.push_back(pca);
            upper.push_back(pab); upper.push_back(B); upper.push_back(C);
            upper.push_back(pab); upper.push_back(C); upper.push_back(pca);
            segs.push_back({pab, pca});
        } else {
            // two below (A,B); the below piece is (A, B, Pbc, Pca)
            int iC = !bl[0] ? 0 : (!bl[1] ? 1 : 2);
            uint32_t C = vs[iC], A = vs[(iC + 1) % 3], B = vs[(iC + 2) % 3];
            uint32_t pbc = 0, pca = 0;
            if (!edge_cut(B, C, &pbc) || !edge_cut(C, A, &pca)) return false;
            lower.push_back(A); lower.push_back(B); lower.push_back(pbc);
            lower.push_back(A); lower.push_back(pbc); lower.push_back(pca);
            upper.push_back(pbc); upper.push_back(C); upper.push_back(pca);
            segs.push_back({pbc, pca});
        }
    }

    // WELD: chain the segments into closed loops. Every cut node must have
    // exactly one out-edge and every walk must return to its start — any
    // anomaly (non-manifold plane crossing) refuses the seal BY NAME
    // rather than guessing around it.
    std::map<uint32_t, uint32_t> next;
    for (const auto& s : segs) {
        if (next.count(s.first)) return false;   // out-degree > 1
        next[s.first] = s.second;
    }
    std::set<uint32_t> visited;
    int loops = 0, caps = 0;
    for (const auto& start : next) {
        if (visited.count(start.first)) continue;
        std::vector<uint32_t> ring;
        uint32_t cur = start.first;
        while (true) {
            ring.push_back(cur);
            visited.insert(cur);
            auto it = next.find(cur);
            if (it == next.end()) return false;             // open chain
            cur = it->second;
            if (ring.size() > cut_src.size() + 1u) return false;  // runaway
            if (cur == start.first) break;
            if (visited.count(cur)) return false;           // cross-linked
        }
        ++loops;
        // fan from ring[0], both windings — one cap per daughter. The
        // divergence integral is triangulation-independent, so the fan is
        // exact for volume; caps are internal membrane (not rendered).
        for (size_t k = 1; k + 1 < ring.size(); ++k) {
            lower.push_back(ring[0]); lower.push_back(ring[k]); lower.push_back(ring[k + 1]);
            upper.push_back(ring[0]); upper.push_back(ring[k + 1]); upper.push_back(ring[k]);
            ++caps;
        }
    }
    if (caps == 0) return false;   // empty cross-section (guarded above)

    // rest volumes at seal time (the tick's own rest blend). Cut slots
    // resolve by lerping the rest edge endpoints at their fixed t — the
    // same lerp step() performs per frame.
    std::vector<float> cutpos(cut_src.size() * 3);
    for (size_t i = 0; i < cut_src.size(); ++i) {
        const SealSlot& c = cut_src[i];
        for (int k = 0; k < 3; ++k)
            cutpos[i * 3 + k] = rest9[c.a * 9 + k] * (1.f - c.t)
                              + rest9[c.b * 9 + k] * c.t;
    }
    auto div6 = [&](uint32_t s0, uint32_t s1, uint32_t s2) -> float {
        float ax, ay, az, bx, by, bz, cx, cy, cz;
        slot_read(rest9, nv, cutpos, s0, &ax, &ay, &az);
        slot_read(rest9, nv, cutpos, s1, &bx, &by, &bz);
        slot_read(rest9, nv, cutpos, s2, &cx, &cy, &cz);
        return (ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz)
              + az * (bx * cy - by * cx)) / 6.f;
    };
    float vl = 0.f, vu = 0.f, vw = 0.f;
    for (size_t i = 0; i + 2 < lower.size(); i += 3)
        vl += div6(lower[i], lower[i + 1], lower[i + 2]);
    for (size_t i = 0; i + 2 < upper.size(); i += 3)
        vu += div6(upper[i], upper[i + 1], upper[i + 2]);
    for (size_t i = 0; i + 2 < tri_verts_.size(); i += 3) {
        uint32_t a = tri_verts_[i], b = tri_verts_[i + 1], cc = tri_verts_[i + 2];
        vw += (rest9[a*9+0] * (rest9[b*9+1] * rest9[cc*9+2] - rest9[b*9+2] * rest9[cc*9+1])
             + rest9[a*9+1] * (rest9[b*9+2] * rest9[cc*9+0] - rest9[b*9+0] * rest9[cc*9+2])
             + rest9[a*9+2] * (rest9[b*9+0] * rest9[cc*9+1] - rest9[b*9+1] * rest9[cc*9+0])) / 6.f;
    }
    // a daughter signing negative = inconsistent orientation through the
    // cut — refuse honestly instead of taking an absolute value.
    if (!(vl > 0.f) || !(vu > 0.f)) return false;

    // publish last: step() reads sealed_ before touching these members
    seal_nv_ = nv;
    cut_src_ = std::move(cut_src);
    cut_pos_ = std::move(cutpos);
    seal_lower_ = std::move(lower);
    seal_upper_ = std::move(upper);
    seal_split_ = split;
    seal_cuts_ = (int)cut_src_.size();
    seal_loops_ = loops;
    seal_caps_ = caps;
    v0_lower_ = vl; v0_upper_ = vu;
    vol_whole0_ = vw;
    vol_lower_ = vl; vol_upper_ = vu; vol_whole_ = vw;
    conserve_pct_ = vw != 0.f ? (vl + vu - vw) / vw * 100.f : 0.f;
    p_lower_ = p_upper_ = 0.f;
    seal_y_ = y;
    sealed_ = true;
    return true;
}

std::string MembraneTick::state_json() const {
    float load_l = 0.f, load_r = 0.f, dmg = 0.f, cap_sum = 0.f;
    uint32_t failed = 0;
    for (size_t i = 0; i < cells_.size(); ++i) {
        if (foot_[i] == 0) load_l += cells_[i].load; else load_r += cells_[i].load;
        dmg += cells_[i].damage;
        failed += cells_[i].failed ? 1u : 0u;
        cap_sum += capacity_[i];
    }
    std::ostringstream o;
    o << "{\"ticks\":" << ticks_
      << ",\"enabled\":" << (enabled_ ? "true" : "false")
      << ",\"cells\":" << cells_.size()
      << ",\"force_l\":" << force_l_ << ",\"force_r\":" << force_r_
      << ",\"load_l\":" << load_l << ",\"load_r\":" << load_r
      << ",\"damage_sum\":" << dmg
      << ",\"failed\":" << failed
      << ",\"capacity_sum\":" << cap_sum
      << ",\"flex_l_deg\":" << flex_l_ * 57.29577951308232
      << ",\"flex_r_deg\":" << flex_r_ * 57.29577951308232
      << ",\"sealed\":" << (sealed_ ? "true" : "false")
      << ",\"V_lower\":" << vol_lower_ << ",\"V_upper\":" << vol_upper_
      << ",\"P_lower\":" << p_lower_ << ",\"P_upper\":" << p_upper_
      << ",\"v0_lower\":" << v0_lower_ << ",\"v0_upper\":" << v0_upper_
      << ",\"V_whole\":" << vol_whole_
      << ",\"conserve_pct\":" << conserve_pct_
      << ",\"seal_split\":" << seal_split_
      << ",\"seal_cuts\":" << seal_cuts_
      << ",\"seal_loops\":" << seal_loops_
      << ",\"seal_caps\":" << seal_caps_
      << ",\"has_scene\":" << (has_scene_ ? "true" : "false") << "}";
    return o.str();
}





