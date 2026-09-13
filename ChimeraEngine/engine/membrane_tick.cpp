
#include "membrane_tick.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <map>
#include <sstream>

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

void MembraneTick::step(std::vector<float>& verts9) {
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return;
    if (tri_verts_.size() != cells_.size() * 3) return;   // hardened
    ++ticks_;

    const bool classified = cell_joint_.size() == cells_.size()
                         && joint_pins_.size() == joint_deg_.size()
                         && vert_joint_.size() == verts9.size() / 9;

    // TRAVEL
    if (!rig_.empty()) {
        apply_chain(verts9);
    } else if (classified) {
        // per-vertex rigid travel with the bound pin's pose
        for (size_t v = 0; v < verts9.size() / 9; ++v) {
            uint8_t j = vert_joint_[v];
            float th = joint_deg_[j];
            if (th == 0.f) continue;
            const auto& pv = joint_pins_[j];
            float bx = verts9[v * 9 + 0] - pv[0];
            float by = verts9[v * 9 + 1] - pv[1];
            float bz = verts9[v * 9 + 2] - pv[2];
            float cth = std::cos(th), sth = std::sin(th);
            verts9[v * 9 + 0] = bx + pv[0];
            verts9[v * 9 + 1] = by * cth - bz * sth + pv[1];
            verts9[v * 9 + 2] = by * sth + bz * cth + pv[2];
        }
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
    if (body.size() < 4) return false;
    uint32_t n = 0;
    std::memcpy(&n, body.data(), 4);
    if (n != verts_expected()) return false;
    vert_joint_.assign(body.begin() + 4, body.end());
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
      << ",\"has_scene\":" << (has_scene_ ? "true" : "false") << "}";
    return o.str();
}





