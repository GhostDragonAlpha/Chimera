
#include "membrane_tick.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <sstream>

namespace {

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
    cells_.assign(tris, Cell{});
    tri_verts_.assign(indices.begin(), indices.end());
    capacity_.resize(tris);
    foot_.assign(tris, 0);
    neighbors_.assign(tris, {});

    std::map<std::pair<uint32_t, uint32_t>, std::vector<uint32_t>> edges;
    for (uint32_t t = 0; t < tris; ++t) {
        uint32_t a = indices[t * 3 + 0], b = indices[t * 3 + 1], c = indices[t * 3 + 2];
        std::pair<uint32_t, uint32_t> e[3] = {{std::min(a,b), std::max(a,b)},
                                              {std::min(b,c), std::max(b,c)},
                                              {std::min(c,a), std::max(c,a)}};
        for (auto& k : e) edges[k].push_back(t);
        capacity_[t] = yield_pa_ * tri_area(verts9, a, b, c);
        foot_[t] = (centroid(verts9, a, b, c)[0] >= 0.f) ? 0u : 1u;
    }
    for (auto& [e, ts] : edges)
        for (size_t i = 0; i + 1 < ts.size(); ++i)
            for (size_t j = i + 1; j < ts.size(); ++j) {
                neighbors_[ts[i]].push_back(ts[j]);
                neighbors_[ts[j]].push_back(ts[i]);
            }

    base_color_.assign(verts9.size() / 9 * 3, 0.f);
    for (size_t v = 0; v < verts9.size() / 9; ++v)
        for (int k = 0; k < 3; ++k)
            base_color_[v * 3 + (size_t)k] = verts9[v * 9 + 6 + (size_t)k];

    has_scene_ = tris > 0;
    ticks_ = 0;
    force_l_ = force_r_ = 0.f;
}

bool MembraneTick::intent(float force_n, const std::string& foot) {
    if (!std::isfinite(force_n) || force_n <= 0.f) return false;
    if (foot == "L") { force_l_ = force_n; return true; }
    if (foot == "R") { force_r_ = force_n; return true; }
    return false;
}

void MembraneTick::clear_intent() { force_l_ = force_r_ = 0.f; }

void MembraneTick::step(std::vector<float>& verts9) {
    if (!has_scene_) return;
    ++ticks_;

    // press: spread each foot's standing force over its carrying cells
    float n_side[2] = {0.f, 0.f};
    for (size_t i = 0; i < cells_.size(); ++i)
        if (!cells_[i].failed) n_side[foot_[i]] += 1.f;
    for (size_t i = 0; i < cells_.size(); ++i) {
        Cell& c = cells_[i];
        if (c.failed) { c.load = 0.f; continue; }
        float force = foot_[i] == 0 ? force_l_ : force_r_;
        c.load = n_side[foot_[i]] > 0.f ? force / n_side[foot_[i]] : 0.f;
    }

    // tensile (B3): overloaded living cells shed the excess, half per
    // tick to their edge-neighbors
    for (size_t i = 0; i < cells_.size(); ++i) {
        Cell& c = cells_[i];
        if (c.failed || c.load <= capacity_[i]) continue;
        float give = (c.load - capacity_[i]) * 0.5f;
        c.load -= give;
        float share = give / std::max(1.f, (float)neighbors_[i].size());
        for (uint32_t nb : neighbors_[i])
            if (!cells_[nb].failed) cells_[nb].load += share;
    }

    // damage + failure (computed, never scripted)
    for (size_t i = 0; i < cells_.size(); ++i) {
        Cell& c = cells_[i];
        if (c.failed) continue;
        if (c.load > capacity_[i])
            c.damage += (c.load - capacity_[i]) / capacity_[i];
        if (c.damage >= 1.f) { c.failed = true; c.load = 0.f; }
    }

    // visibility: load tints the cell toward red; failed cells go dark
    for (size_t i = 0; i < cells_.size(); ++i) {
        const Cell& c = cells_[i];
        float t = c.failed ? 0.f
                : std::min(1.f, c.load / std::max(capacity_[i], 1.f));
        for (int k = 0; k < 3; ++k) {
            uint32_t v = tri_verts_[i * 3 + (size_t)k];
            float base = base_color_[v * 3 + (size_t)k];
            float out;
            if (c.failed)            out = 0.08f;
            else if (k == 0)         out = base + (1.f - base) * t;
            else                     out = base * (1.f - t * 0.85f);
            verts9[v * 9 + 6 + (size_t)k] = std::min(out, 1.f);
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
      << ",\"has_scene\":" << (has_scene_ ? "true" : "false") << "}";
    return o.str();
}

