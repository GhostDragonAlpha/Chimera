
#include "membrane_tick.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <cstdlib>
#include <functional>
#include <map>
#include <set>
#include <sstream>
#include <unordered_map>
#include <utility>

namespace {

constexpr float ANKLE_X_L = 0.4609f;   // measured ankle x (FEET prereg)
constexpr float ANKLE_X_R = -0.4609f;
constexpr float G_EARTH = 9.81f;       // m/s^2 -- THE FALL (movement law)

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
    std::lock_guard<std::mutex> lk(seal_mtx_);
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
    joint_verts_.clear();   // mesh changed: pressed regions rebuild
    press_off_.clear();     // and any dimple field dies with it
    press_field_ = false;
    touch_active_ = false;
    touch_f_ = 0.f;
    ticks_ = 0;
    force_l_ = force_r_ = 0.f;
    flex_l_ = flex_r_ = 0.f;
    root_y_ = root_vy_ = 0.f;    // a new body starts at its authored rest
    g_contact_n_ = 0.f;          // (gravity_on_ itself survives re-init:
                                 //  the law applies to whatever body loads)
    ready_.store(true, std::memory_order_release);
}

bool MembraneTick::intent(float force_n, const std::string& foot) {
    if (!std::isfinite(force_n) || force_n <= 0.f) return false;
    if (foot == "L") { force_l_ = force_n; return true; }
    if (foot == "R") { force_r_ = force_n; return true; }
    return false;
}

void MembraneTick::clear_intent() {
    // release ALL standing presses: feet + per-joint (the hydraulic
    // press needs a release op; force <= 0 is refused on /tick_intent)
    force_l_ = force_r_ = 0.f;
    std::fill(joint_force_.begin(), joint_force_.end(), 0.f);
}

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

void MembraneTick::step(std::vector<float>& verts9, float dt) {
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return;
    if (tri_verts_.size() != cells_.size() * 3) return;   // hardened
    // ONE lock for the whole tick body: travel reads the bindings that
    // init()/loaders rewrite, and the seal block reads the cell state a
    // cut republishes. try_lock: the render loop never blocks — a cut or
    // mesh upload in flight just skips this frame.
    std::unique_lock<std::mutex> lk(seal_mtx_, std::try_to_lock);
    if (!lk.owns_lock()) return;
    ++ticks_;

    const bool classified = cell_joint_.size() == cells_.size()
                         && !joint_pins_.empty()          // bindings without pins = OOB reads
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

    // THE HYDRAULIC PRESS + RETURN (appliance 3, preregs ff9033a0 /
    // 3716fecf): pressed cells dimple inward by the linear-membrane law
    // delta = F/(4 pi sigma), Gaussian falloff. Active presses SET their
    // offsets (force balances tension — steady state); on release the
    // offsets DECAY exp(-dt/tau) (soft-tissue stress relaxation) until
    // the 0.1 mm cutoff clears them. The divergence sums read the dimpled
    // geometry and the kappa law answers throughout.
    dimple_m_ = 0.f;
    bool any_press = false;
    if (classified && !joint_force_.empty()) {
        if (joint_verts_.size() != joint_force_.size()) {
            // lazy region build once classification is live: each pin's
            // cell-group vertices + centroid (authored rest)
            joint_verts_.assign(joint_force_.size(), {});
            joint_cent_.assign(joint_force_.size(), {0.f, 0.f, 0.f});
            std::vector<std::array<double, 3>> acc(joint_force_.size(), {0., 0., 0.});
            for (size_t i = 0; i < cells_.size(); ++i) {
                uint8_t j = cell_joint_[i];
                if (j >= joint_verts_.size()) continue;
                for (int k = 0; k < 3; ++k) {
                    uint32_t v = tri_verts_[i * 3 + (size_t)k];
                    joint_verts_[j].push_back(v);
                    acc[j][0] += base_pos_[v * 9 + 0];
                    acc[j][1] += base_pos_[v * 9 + 1];
                    acc[j][2] += base_pos_[v * 9 + 2];
                }
            }
            for (size_t j = 0; j < joint_verts_.size(); ++j) {
                float n = (float)std::max<size_t>(1, joint_verts_[j].size());
                joint_cent_[j] = {(float)(acc[j][0] / n),
                                  (float)(acc[j][1] / n),
                                  (float)(acc[j][2] / n)};
            }
        }
        const size_t nverts = verts9.size() / 9;
        if (press_off_.size() != nverts) press_off_.assign(nverts, 0.f);
        // THE TOUCH: offsets around the WORLD hit point, measured on the
        // POSED positions (the press follows the body)
        if (touch_active_) {
            any_press = true;
            float delta = touch_f_ / (4.f * 3.14159265358979f * sigma_n_);
            float r02 = press_r0_ * press_r0_;
            float mr02 = 9.f * r02;
            for (size_t v = 0; v < nverts; ++v) {
                float dx = verts9[v * 9 + 0] - touch_pt_[0];
                float dy = verts9[v * 9 + 1] - touch_pt_[1];
                float dz = verts9[v * 9 + 2] - touch_pt_[2];
                float d2 = dx * dx + dy * dy + dz * dz;
                if (d2 > mr02) continue;                 // outside the falloff
                float off = delta * std::exp(-d2 / r02);
                if (off > press_off_[v]) press_off_[v] = off;  // dominant wins
            }
        }
        for (size_t j = 0; j < joint_force_.size(); ++j) {
            float F = joint_force_[j];
            if (F <= 0.f) continue;
            any_press = true;
            float delta = F / (4.f * 3.14159265358979f * sigma_n_);
            (void)delta;
            const auto& C = joint_cent_[j];
            float r02 = press_r0_ * press_r0_;
            for (uint32_t v : joint_verts_[j]) {
                float dx = base_pos_[v * 9 + 0] - C[0];
                float dy = base_pos_[v * 9 + 1] - C[1];
                float dz = base_pos_[v * 9 + 2] - C[2];
                float q = (dx * dx + dy * dy + dz * dz) / r02;
                float off = delta * std::exp(-q);
                if (off > press_off_[v]) press_off_[v] = off;  // dominant wins
            }
        }
        if (!any_press && press_field_) {
            // THE HYDRAULIC RETURN: released offsets decay exp(-dt/tau)
            const float decay = std::exp(-(dt > 0.f ? dt : 0.f) / tau_relax_);
            float mx = 0.f;
            for (float& o : press_off_) {
                if (o == 0.f) continue;
                o *= decay;
                if (o < 1e-4f) o = 0.f;             // 0.1 mm cutoff
                mx = std::max(mx, o);
            }
            dimple_m_ = mx;
            if (mx == 0.f) {
                std::fill(press_off_.begin(), press_off_.end(), 0.f);
                press_field_ = false;               // deterministic rest
            }
        }
        // POSED NORMALS: the travel writes positions; recompute normals
        // from the posed surface every tick so touch directions and the
        // lighting ride the true skin (the stale-normal bug class).
        {
            std::vector<float> acc(nverts * 3, 0.f);
            for (size_t i = 0; i + 2 < tri_verts_.size(); i += 3) {
                uint32_t a = tri_verts_[i], b = tri_verts_[i + 1], c2 = tri_verts_[i + 2];
                float ux = verts9[b*9+0] - verts9[a*9+0];
                float uy = verts9[b*9+1] - verts9[a*9+1];
                float uz = verts9[b*9+2] - verts9[a*9+2];
                float wx = verts9[c2*9+0] - verts9[a*9+0];
                float wy = verts9[c2*9+1] - verts9[a*9+1];
                float wz = verts9[c2*9+2] - verts9[a*9+2];
                float nx = uy * wz - uz * wy;
                float ny = uz * wx - ux * wz;
                float nz = ux * wy - uy * wx;
                for (uint32_t v : {a, b, c2}) {
                    acc[(size_t)v * 3 + 0] += nx;
                    acc[(size_t)v * 3 + 1] += ny;
                    acc[(size_t)v * 3 + 2] += nz;
                }
            }
            for (size_t v = 0; v < nverts; ++v) {
                float nx = acc[v * 3 + 0], ny = acc[v * 3 + 1], nz = acc[v * 3 + 2];
                float len = std::sqrt(nx * nx + ny * ny + nz * nz);
                if (len < 1e-12f) continue;
                verts9[v * 9 + 3] = nx / len;
                verts9[v * 9 + 4] = ny / len;
                verts9[v * 9 + 5] = nz / len;
            }
        }

        // apply whatever offsets survive this tick
        if (any_press || press_field_) {
            press_field_ = true;
            float applied_max = 0.f;
            for (size_t v = 0; v < nverts; ++v) {
                float off = press_off_[v];
                if (off == 0.f) continue;
                applied_max = std::max(applied_max, off);
                verts9[v * 9 + 0] -= base_pos_[v * 9 + 3] * off;  // authored
                verts9[v * 9 + 1] -= base_pos_[v * 9 + 4] * off;  // normal
                verts9[v * 9 + 2] -= base_pos_[v * 9 + 5] * off;
            }
            // report the TRUE max applied offset, not the theoretical
            // delta — the Gaussian peak can fall between mesh vertices
            dimple_m_ = applied_max;
        }
        if (any_press || press_field_) {
            // normals from the DEFORMED surface: without this the shading
            // stays flat and the dimple is invisible. Face normals of the
            // offset-carrying cells accumulate to their verts, normalize.
            std::vector<float> acc(nverts * 3, 0.f);
            std::vector<uint8_t> touched(nverts, 0);
            for (size_t i = 0; i < cells_.size(); ++i) {
                uint32_t a = tri_verts_[i * 3 + 0], b = tri_verts_[i * 3 + 1],
                         c = tri_verts_[i * 3 + 2];
                if (press_off_[a] == 0.f && press_off_[b] == 0.f &&
                    press_off_[c] == 0.f)
                    continue;
                float ux = verts9[b*9+0] - verts9[a*9+0];
                float uy = verts9[b*9+1] - verts9[a*9+1];
                float uz = verts9[b*9+2] - verts9[a*9+2];
                float wx = verts9[c*9+0] - verts9[a*9+0];
                float wy = verts9[c*9+1] - verts9[a*9+1];
                float wz = verts9[c*9+2] - verts9[a*9+2];
                float nx = uy * wz - uz * wy;
                float ny = uz * wx - ux * wz;
                float nz = ux * wy - uy * wx;
                for (uint32_t v : {a, b, c}) {
                    acc[(size_t)v * 3 + 0] += nx;
                    acc[(size_t)v * 3 + 1] += ny;
                    acc[(size_t)v * 3 + 2] += nz;
                    touched[v] = 1;
                }
            }
            for (size_t v = 0; v < nverts; ++v) {
                if (!touched[v]) continue;
                float nx = acc[v * 3 + 0], ny = acc[v * 3 + 1], nz = acc[v * 3 + 2];
                float len = std::sqrt(nx * nx + ny * ny + nz * nz);
                if (len < 1e-12f) continue;
                verts9[v * 9 + 3] = nx / len;
                verts9[v * 9 + 4] = ny / len;
                verts9[v * 9 + 5] = nz / len;
            }
            normals_displaced_ = true;
        } else if (normals_displaced_) {
            // field fully cleared: restore the authored normals
            for (size_t v = 0; v < nverts; ++v)
                for (int k = 0; k < 3; ++k)
                    verts9[v * 9 + 3 + (size_t)k] = base_pos_[v * 9 + 3 + (size_t)k];
            normals_displaced_ = false;
        }
    }

    // PRESS (force known): spread over the cells of the pressed group.
    // Cells below the capacity floor are DEGENERATE membrane (the sculpt
    // has 206 slivers incl. exact zero-area — measured 2026-09-13): they
    // carry no share, or the damage law divides by ~zero and fires inf.
    if (classified && !joint_force_.empty()) {
        const float cap_floor = 0.1f;   // N; below this a patch is not a membrane
        std::vector<float> cnt(joint_pins_.size(), 0.f);
        for (size_t i = 0; i < cells_.size(); ++i)
            if (!cells_[i].failed && capacity_[i] > cap_floor) cnt[cell_joint_[i]] += 1.f;
        for (size_t i = 0; i < cells_.size(); ++i) {
            Cell& c = cells_[i];
            uint8_t jg = cell_joint_[i];
            c.load = (cnt[jg] > 0.f && !c.failed && capacity_[i] > cap_floor)
                         ? joint_force_[jg] / cnt[jg] : 0.f;
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
    // THE SEAL / MITOSIS (recursive cut-and-weld): blend points ride the
    // posed surface at fixed weights, so every cell's boundary stays
    // closed while the surface moves — each cell's divergence sum is a
    // true volume, and the cells' sum must equal the posed whole volume.
    // (Covered by the step-entry lock; no separate try_lock here.)
    if (sealed_ && !seal_cells_.empty()) {
        const size_t ncut = cut_src_.size();
        cut_pos_.assign(ncut * 3, 0.f);
        for (size_t k = 0; k < ncut; ++k) {
            const CutBlend& b = cut_src_[k];
            float sx = 0.f, sy = 0.f, sz = 0.f;
            for (int i = 0; i < b.n; ++i) {
                sx += b.w[i] * verts9[b.v[i] * 9 + 0];
                sy += b.w[i] * verts9[b.v[i] * 9 + 1];
                sz += b.w[i] * verts9[b.v[i] * 9 + 2];
            }
            cut_pos_[k * 3 + 0] = sx;
            cut_pos_[k * 3 + 1] = sy;
            cut_pos_[k * 3 + 2] = sz;
        }
        auto div6 = [&](uint32_t s0, uint32_t s1, uint32_t s2) -> float {
            float ax, ay, az, bx, by, bz, cx, cy, cz;
            slot_read(verts9, seal_nv_, cut_pos_, s0, &ax, &ay, &az);
            slot_read(verts9, seal_nv_, cut_pos_, s1, &bx, &by, &bz);
            slot_read(verts9, seal_nv_, cut_pos_, s2, &cx, &cy, &cz);
            return (ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz)
                  + az * (bx * cy - by * cx)) / 6.f;
        };
        float total = 0.f;
        for (SealCell& c : seal_cells_) {
            float v = 0.f;
            for (size_t i = 0; i + 2 < c.pieces.size(); i += 3)
                v += div6(c.pieces[i], c.pieces[i + 1], c.pieces[i + 2]);
            c.vol = v;
            c.p = (c.v0 - v) / (kappa_ * c.v0);
            total += v;
        }
        float vw = 0.f;
        for (size_t i = 0; i + 2 < tri_verts_.size(); i += 3) {
            uint32_t a = tri_verts_[i], b = tri_verts_[i + 1], cc2 = tri_verts_[i + 2];
            vw += (verts9[a*9+0] * (verts9[b*9+1] * verts9[cc2*9+2] - verts9[b*9+2] * verts9[cc2*9+1])
                 + verts9[a*9+1] * (verts9[b*9+2] * verts9[cc2*9+0] - verts9[b*9+0] * verts9[cc2*9+2])
                 + verts9[a*9+2] * (verts9[b*9+0] * verts9[cc2*9+1] - verts9[b*9+1] * verts9[cc2*9+0])) / 6.f;
        }
        vol_whole_ = vw;
        conserve_pct_ = vw != 0.f ? (total - vw) / vw * 100.f : 0.f;
    }

    // THE MOVEMENT LAW -- THE FALL (prereg appended to
    // SEAL_PREREGISTRATION.md). One rigid DOF along Y:
    //   y'' = -g + F_contact/m,
    // F_contact a penalty spring read ONLY at the body's lowest vertex
    // against the floor y=0: F = k*depth + c*max(0,-vy), depth = how far
    // the lowest point sits below the floor. At rest the spring carries
    // exactly the weight: k*sink = m*g (sink = 1 cm, derived). Placed
    // LAST: every other pass (travel, press, seal volumes) reads the
    // un-offset verts, so a uniform translation cannot leak into any
    // volume, normal or pressure -- dV = 0 by construction.
    if (gravity_on_) {
        const size_t nvg = verts9.size() / 9;
        float lo = nvg ? verts9[0 * 9 + 1] : 0.f;
        for (size_t v = 1; v < nvg; ++v)
            lo = std::min(lo, verts9[v * 9 + 1]);
        lo += root_y_;                       // world lowest point this tick
        const float depth = std::max(0.f, -lo);
        float F = k_ground_ * depth + c_ground_ * std::max(0.f, -root_vy_);
        const float F_cap = 50.f * mass_kg_ * G_EARTH;   // floor, not launcher
        g_contact_n_ = std::min(F, F_cap);
        float dts = std::min(std::max(dt, 0.f), 0.05f);  // stall guard
        if (dts > 0.f) {
            root_vy_ += (g_contact_n_ / mass_kg_ - G_EARTH) * dts;
            root_vy_ = std::min(std::max(root_vy_, -30.f), 30.f);
            root_y_ += root_vy_ * dts;
            if (root_y_ > 3.f)  { root_y_ = 3.f;  if (root_vy_ > 0.f) root_vy_ = 0.f; }
            if (root_y_ < -3.f) { root_y_ = -3.f; if (root_vy_ < 0.f) root_vy_ = 0.f; }
        }
        for (size_t v = 0; v < nvg; ++v)
            verts9[v * 9 + 1] += root_y_;
    }
}

bool MembraneTick::intent_joint(int idx, float force_n) {
    if (!std::isfinite(force_n) || force_n <= 0.f) return false;
    if (idx < 0 || idx >= (int)joint_force_.size()) return false;
    joint_force_[idx] = force_n;
    return true;
}

bool MembraneTick::load_classify(const std::string& body) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (body.size() < 4) return false;
    uint32_t n = 0;
    std::memcpy(&n, body.data(), 4);
    if (body.size() != 4 + n) return false;
    if (n != cells_.size()) return false;   // one type per triangle cell
    cell_joint_.assign(body.begin() + 4, body.end());
    joint_verts_.clear();   // pressed regions rebuild from the new types
    return true;
}

bool MembraneTick::load_vertbind(const std::string& body) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
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
    std::lock_guard<std::mutex> lk(seal_mtx_);
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

void MembraneTick::export_topology(std::vector<uint8_t>& out) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    uint32_t n = (uint32_t)(tri_verts_.size() / 3);   // header: TRIANGLE count
    out.resize(4 + tri_verts_.size() * 4);            // payload: ALL indices
    std::memcpy(out.data(), &n, 4);
    if (!tri_verts_.empty())
        std::memcpy(out.data() + 4, tri_verts_.data(), tri_verts_.size() * 4);
}

void MembraneTick::export_verts(const std::vector<float>& verts9,
                                std::vector<uint8_t>& out) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    uint32_t n = (uint32_t)(verts9.size() / 9);
    out.resize(4 + verts9.size() * 4);
    std::memcpy(out.data(), &n, 4);
    if (n) std::memcpy(out.data() + 4, verts9.data(), verts9.size() * 4);
}

bool MembraneTick::touch_press_at(const float hit[3], float force_n) {
    if (!std::isfinite(force_n) || force_n <= 0.f) return false;
    std::lock_guard<std::mutex> lk(seal_mtx_);
    touch_pt_[0] = hit[0]; touch_pt_[1] = hit[1]; touch_pt_[2] = hit[2];
    touch_f_ = force_n;
    touch_active_ = true;
    return true;
}

bool MembraneTick::touch_press(float u, float v, float force_n,
                               const std::function<bool(float[3])>& pick_fn,
                               std::string& err, float hit_out[3]) {
    if (!std::isfinite(force_n) || force_n <= 0.f) {
        err = "force_n must be positive";
        return false;
    }
    std::lock_guard<std::mutex> lk(seal_mtx_);
    float hit[3];
    if (!pick_fn(hit)) {
        err = "the ray misses the body";
        return false;
    }
    touch_pt_[0] = hit[0]; touch_pt_[1] = hit[1]; touch_pt_[2] = hit[2];
    if (hit_out) { hit_out[0] = hit[0]; hit_out[1] = hit[1]; hit_out[2] = hit[2]; }
    touch_f_ = force_n;
    touch_active_ = true;
    return true;
}

bool MembraneTick::touch_clear() {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    touch_active_ = false;
    return true;
}

bool MembraneTick::split(int cell_idx) {
    // THE COMPONENT SPLIT: flood-fill the named cell's pieces through
    // shared slots; each closed component becomes its own sealed cell.
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return false;
    // body-wide lock: same contract as seal() (HTTP readers vs writers)
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (seal_cells_.empty()) return false;              // nothing sealed yet
    if (cell_idx < 0 || cell_idx >= (int)seal_cells_.size()) return false;
    const uint32_t nv = (uint32_t)(base_pos_.size() / 9);

    const std::vector<uint32_t>& pieces = seal_cells_[cell_idx].pieces;
    const size_t np = pieces.size() / 3;
    if (np == 0) return false;

    // union-find over pieces via shared slots (originals + cut blends)
    std::unordered_map<uint32_t, size_t> first;
    std::vector<size_t> parent(np);
    for (size_t i = 0; i < np; ++i) parent[i] = i;
    std::function<size_t(size_t)> find = [&](size_t x) -> size_t {
        while (parent[x] != x) { parent[x] = parent[parent[x]]; x = parent[x]; }
        return x;
    };
    for (size_t p = 0; p < np; ++p) {
        for (int k = 0; k < 3; ++k) {
            uint32_t s = pieces[p * 3 + (size_t)k];
            auto it = first.find(s);
            if (it == first.end()) first[s] = p;
            else {
                size_t ra = find(it->second), rb = find(p);
                if (ra != rb) parent[ra] = rb;
            }
        }
    }
    std::map<size_t, std::vector<uint32_t>> comps;   // root -> flat pieces
    for (size_t p = 0; p < np; ++p)
        for (int k = 0; k < 3; ++k)
            comps[find(p)].push_back(pieces[p * 3 + (size_t)k]);
    if (comps.size() < 2) return false;   // one closed surface: nothing to split

    // rest volumes per component on the tick's rest blend (same path as
    // seal(): blended rest verts, weighted cut slots)
    std::vector<float> rest9(base_pos_);
    {
        const bool classified = cell_joint_.size() == cells_.size()
                             && !joint_pins_.empty()          // bindings without pins = OOB reads
                             && joint_pins_.size() == joint_deg_.size()
                             && vert_bind_idx_.size() == (size_t)nv * 3
                             && vert_bind_w_.size() == (size_t)nv * 3;
        if (classified) apply_travel(rest9, nullptr);
    }
    std::vector<float> rest_cut(cut_src_.size() * 3, 0.f);
    for (size_t k = 0; k < cut_src_.size(); ++k) {
        const CutBlend& b = cut_src_[k];
        for (int i = 0; i < b.n; ++i)
            for (int d = 0; d < 3; ++d)
                rest_cut[k * 3 + d] += b.w[i] * rest9[b.v[i] * 9 + d];
    }
    std::vector<SealCell> out;
    for (auto& [root, flat] : comps) {
        SealCell c;
        c.pieces = std::move(flat);
        float v = 0.f, lo = 1e30f, hi = -1e30f;
        for (size_t i = 0; i + 2 < c.pieces.size(); i += 3) {
            float s[3][3];
            for (int t = 0; t < 3; ++t) {
                uint32_t sl = c.pieces[i + (size_t)t];
                if (sl < nv) {
                    s[t][0] = rest9[sl * 9 + 0];
                    s[t][1] = rest9[sl * 9 + 1];
                    s[t][2] = rest9[sl * 9 + 2];
                } else {
                    s[t][0] = rest_cut[(sl - nv) * 3 + 0];
                    s[t][1] = rest_cut[(sl - nv) * 3 + 1];
                    s[t][2] = rest_cut[(sl - nv) * 3 + 2];
                }
            }
            v += (s[0][0] * (s[1][1] * s[2][2] - s[1][2] * s[2][1])
                + s[0][1] * (s[1][2] * s[2][0] - s[1][0] * s[2][2])
                + s[0][2] * (s[1][0] * s[2][1] - s[1][1] * s[2][0])) / 6.f;
        }
        for (uint32_t sl : c.pieces) {
            float yy = sl < nv ? rest9[sl * 9 + 1]
                               : rest_cut[(sl - nv) * 3 + 1];
            lo = std::min(lo, yy);
            hi = std::max(hi, yy);
        }
        if (!(v > 0.f)) return false;   // orientation broke: refuse honestly
        c.v0 = v;
        c.vol = v;
        c.p = 0.f;
        c.caps = seal_cells_[cell_idx].caps;   // cap count carries over
        c.ylo = lo;
        c.yhi = hi;
        out.push_back(std::move(c));
    }

    // publish: component 0 replaces the cell, the rest append (under the
    // body-wide lock taken at entry)
    seal_cells_[cell_idx] = std::move(out[0]);
    for (size_t i = 1; i < out.size(); ++i)
        seal_cells_.push_back(std::move(out[i]));
    return true;
}

bool MembraneTick::seal(float y, int cell_idx) {
    // MITOSIS — the recursive cut-and-weld (preregs 4eb9480c, be971e7c).
    // Cuts sealed cell `cell_idx` (0 = the whole creature before any
    // cut) into two sealed cells. Inserted points are convex blends over
    // original vertices, so they ride the posed surface at fixed weights.
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return false;
    if (!std::isfinite(y)) return false;
    if (tri_verts_.size() != cells_.size() * 3) return false;
    const uint32_t nv = (uint32_t)(base_pos_.size() / 9);
    if (nv == 0) return false;
    // ONE lock for the whole seal body: this HTTP thread reads bindings,
    // cells, and the blend table that other HTTP threads (loaders) and
    // the render thread (init) rewrite under the same mutex. Blocking
    // here is bounded by one tick; the render loop never waits on us.
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (seal_cells_.empty()) {
        if (cell_idx != 0) return false;        // only cell 0 exists
    } else if (cell_idx < 0 || cell_idx >= (int)seal_cells_.size()) {
        return false;                           // cell index out of range
    }

    // rest9: the verts the tick ITSELF produces at rest — the classified
    // blend with all angles 0, the same arithmetic path step() runs per
    // frame. v0 measured on these floats makes the rest dV exactly 0.
    std::vector<float> rest9(base_pos_);
    {
        const bool classified = cell_joint_.size() == cells_.size()
                             && !joint_pins_.empty()          // bindings without pins = OOB reads
                             && joint_pins_.size() == joint_deg_.size()
                             && vert_bind_idx_.size() == (size_t)nv * 3
                             && vert_bind_w_.size() == (size_t)nv * 3;
        if (classified) apply_travel(rest9, nullptr);
    }

    // global point space: [0, nv) originals, then existing cuts, then the
    // new cuts this seal appends (ids stay dense and global).
    const size_t ncut0 = cut_src_.size();
    std::vector<CutBlend> pts(nv + ncut0);
    for (uint32_t v = 0; v < nv; ++v) {
        pts[v].n = 1; pts[v].v[0] = v; pts[v].w[0] = 1.f;
    }
    for (size_t k = 0; k < ncut0; ++k) pts[nv + k] = cut_src_[k];
    std::vector<float> py(nv + ncut0);          // rest y per point
    for (size_t s = 0; s < pts.size(); ++s) {
        const CutBlend& b = pts[s];
        float sy = 0.f;
        for (int i = 0; i < b.n; ++i) sy += b.w[i] * rest9[b.v[i] * 9 + 1];
        py[s] = sy;
    }

    // the boundary being cut: the named cell's pieces (or the whole creature)
    std::vector<uint32_t> src;
    if (seal_cells_.empty()) src.assign(tri_verts_.begin(), tri_verts_.end());
    else src = seal_cells_[cell_idx].pieces;

    // the plane must cross the cell
    float ymin = 1e30f, ymax = -1e30f;
    for (uint32_t s : src) {
        ymin = std::min(ymin, py[s]);
        ymax = std::max(ymax, py[s]);
    }
    if (y <= ymin || y >= ymax) return false;   // plane outside the cell

    // CUT: split every straddling piece; new cut points are merged convex
    // blends of the endpoints. Segment direction follows the BELOW-piece
    // boundary walk (the winding law below consumes that direction).
    std::map<std::pair<uint32_t, uint32_t>, uint32_t> cut_id;
    std::vector<uint32_t> lower, upper;         // 3 slots per piece
    std::vector<std::pair<uint32_t, uint32_t>> segs;
    int split = 0;
    // rc: 0 = ok, 1 = not a crossing edge, 2 = blend overflow
    auto edge_cut = [&](uint32_t sA, uint32_t sB, uint32_t* out) -> int {
        if (py[sA] >= py[sB]) std::swap(sA, sB);
        if (!(py[sA] < y && y <= py[sB])) return 1;
        auto key = std::make_pair(std::min(sA, sB), std::max(sA, sB));
        auto it = cut_id.find(key);
        if (it != cut_id.end()) { *out = it->second; return 0; }
        float t = (y - py[sA]) / (py[sB] - py[sA]);
        CutBlend b;
        for (int i = 0; i < pts[sA].n; ++i) {
            float w = (1.f - t) * pts[sA].w[i];
            bool merged = false;
            for (int j = 0; j < b.n; ++j)
                if (b.v[j] == pts[sA].v[i]) { b.w[j] += w; merged = true; break; }
            if (!merged) {
                if (b.n >= 8) return 2;
                b.v[b.n] = pts[sA].v[i]; b.w[b.n] = w; ++b.n;
            }
        }
        for (int i = 0; i < pts[sB].n; ++i) {
            float w = t * pts[sB].w[i];
            bool merged = false;
            for (int j = 0; j < b.n; ++j)
                if (b.v[j] == pts[sB].v[i]) { b.w[j] += w; merged = true; break; }
            if (!merged) {
                if (b.n >= 8) return 2;
                b.v[b.n] = pts[sB].v[i]; b.w[b.n] = w; ++b.n;
            }
        }
        uint32_t id = (uint32_t)pts.size();
        cut_id[key] = id;
        pts.push_back(b);
        py.push_back(y);
        *out = id;
        return 0;
    };
    for (size_t i = 0; i + 2 < src.size(); i += 3) {
        uint32_t vs[3] = {src[i], src[i + 1], src[i + 2]};
        bool bl[3] = {py[vs[0]] < y, py[vs[1]] < y, py[vs[2]] < y};
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
        uint32_t p0 = 0, p1 = 0;
        if (nb == 1) {
            // one below (A); the below piece is (A, Pab, Pca)
            int iA = bl[0] ? 0 : (bl[1] ? 1 : 2);
            uint32_t A = vs[iA], B = vs[(iA + 1) % 3], C = vs[(iA + 2) % 3];
            int ra = edge_cut(A, B, &p0), rb = edge_cut(C, A, &p1);
            if (ra == 2 || rb == 2) return false;   // blend overflow
            if (ra != 0 || rb != 0) return false;   // degenerate
            lower.push_back(A); lower.push_back(p0); lower.push_back(p1);
            upper.push_back(p0); upper.push_back(B); upper.push_back(C);
            upper.push_back(p0); upper.push_back(C); upper.push_back(p1);
            segs.push_back({p0, p1});
        } else {
            // two below (A,B); the below piece is (A, B, Pbc, Pca)
            int iC = !bl[0] ? 0 : (!bl[1] ? 1 : 2);
            uint32_t C = vs[iC], A = vs[(iC + 1) % 3], B = vs[(iC + 2) % 3];
            int ra = edge_cut(B, C, &p0), rb = edge_cut(C, A, &p1);
            if (ra == 2 || rb == 2) return false;   // blend overflow
            if (ra != 0 || rb != 0) return false;   // degenerate
            lower.push_back(A); lower.push_back(B); lower.push_back(p0);
            lower.push_back(A); lower.push_back(p0); lower.push_back(p1);
            upper.push_back(p0); upper.push_back(C); upper.push_back(p1);
            segs.push_back({p0, p1});
        }
    }

    // WELD: chain the segments into closed loops. Every cut node must have
    // exactly one out-edge and every walk must return to its start — any
    // anomaly refuses the cut BY NAME rather than guessing around it.
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
            if (ring.size() > pts.size()) return false;     // runaway
            if (cur == start.first) break;
            if (visited.count(cur)) return false;           // cross-linked
        }
        ++loops;
        // WINDING LAW: every edge of a closed oriented surface appears
        // exactly twice, once per direction. The below pieces walk each
        // cut edge in the chained direction, so the LOWER cap traverses
        // the ring REVERSED and the UPPER cap as chained. (v2 had this
        // swapped — silent at y=2.6, loud at the hip band; corrected per
        // prereg be971e7c with ray-parity ground truth.)
        for (size_t k = 1; k + 1 < ring.size(); ++k) {
            lower.push_back(ring[0]); lower.push_back(ring[k + 1]); lower.push_back(ring[k]);
            upper.push_back(ring[0]); upper.push_back(ring[k]); upper.push_back(ring[k + 1]);
            ++caps;
        }
    }
    if (caps == 0) return false;   // empty cross-section (guarded above)

    // rest volumes on the tick's own rest blend; blend positions resolve
    // with the same weighted sum step() performs per frame.
    auto slot3 = [&](uint32_t s, float* x, float* yy, float* z) {
        if (s < nv) {
            *x = rest9[s * 9 + 0]; *yy = rest9[s * 9 + 1]; *z = rest9[s * 9 + 2];
        } else {
            const CutBlend& b = pts[s];
            float sx = 0.f, sy = 0.f, sz = 0.f;
            for (int i = 0; i < b.n; ++i) {
                sx += b.w[i] * rest9[b.v[i] * 9 + 0];
                sy += b.w[i] * rest9[b.v[i] * 9 + 1];
                sz += b.w[i] * rest9[b.v[i] * 9 + 2];
            }
            *x = sx; *yy = sy; *z = sz;
        }
    };
    auto div6 = [&](uint32_t s0, uint32_t s1, uint32_t s2) -> float {
        float ax, ay, az, bx, by, bz, cx, cy, cz;
        slot3(s0, &ax, &ay, &az);
        slot3(s1, &bx, &by, &bz);
        slot3(s2, &cx, &cy, &cz);
        return (ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz)
              + az * (bx * cy - by * cx)) / 6.f;
    };
    float vl = 0.f, vu = 0.f;
    for (size_t i = 0; i + 2 < lower.size(); i += 3)
        vl += div6(lower[i], lower[i + 1], lower[i + 2]);
    for (size_t i = 0; i + 2 < upper.size(); i += 3)
        vu += div6(upper[i], upper[i + 1], upper[i + 2]);
    // a daughter signing negative = inconsistent orientation through the
    // cut — refuse honestly instead of taking an absolute value.
    if (!(vl > 0.f) || !(vu > 0.f)) return false;

    // per-cell rest y-ranges (for future refusal checks)
    auto range_of = [&](const std::vector<uint32_t>& pieces, float* lo, float* hi) {
        float l = 1e30f, h = -1e30f;
        for (uint32_t s : pieces) { l = std::min(l, py[s]); h = std::max(h, py[s]); }
        *lo = l; *hi = h;
    };
    SealCell below, above;
    below.pieces = std::move(lower); below.v0 = vl; below.caps = caps;
    above.pieces = std::move(upper); above.v0 = vu; above.caps = caps;
    below.vol = vl; below.p = 0.f;
    above.vol = vu; above.p = 0.f;
    range_of(below.pieces, &below.ylo, &below.yhi);
    range_of(above.pieces, &above.ylo, &above.yhi);

    // publish: new cuts append to the global blend table (slot ids match);
    // cell k is REPLACED by its below daughter, the above daughter appends.
    // (Under the body-wide lock taken at entry.)
    {
        seal_nv_ = nv;               // slot-space base (NaN bug: was unset)
        cut_src_.insert(cut_src_.end(), pts.begin() + (nv + ncut0), pts.end());
        cut_pos_.assign(cut_src_.size() * 3, 0.f);
        if (seal_cells_.empty()) {
            seal_cells_.push_back(std::move(below));
            seal_cells_.push_back(std::move(above));
            // whole-creature divergence volume at first seal (reference)
            float vw = 0.f;
            for (size_t i = 0; i + 2 < tri_verts_.size(); i += 3) {
                uint32_t a = tri_verts_[i], b = tri_verts_[i + 1], cc = tri_verts_[i + 2];
                vw += (rest9[a*9+0] * (rest9[b*9+1] * rest9[cc*9+2] - rest9[b*9+2] * rest9[cc*9+1])
                     + rest9[a*9+1] * (rest9[b*9+2] * rest9[cc*9+0] - rest9[b*9+0] * rest9[cc*9+2])
                     + rest9[a*9+2] * (rest9[b*9+0] * rest9[cc*9+1] - rest9[b*9+1] * rest9[cc*9+0])) / 6.f;
            }
            vol_whole0_ = vw;
            vol_whole_ = vw;
        } else {
            seal_cells_[cell_idx] = std::move(below);
            seal_cells_.push_back(std::move(above));
        }
        seal_split_ = split;
        seal_cuts_ = (int)cut_id.size();
        seal_loops_ = loops;
        seal_caps_ = caps;
        seal_y_ = y;
        sealed_ = true;   // published under the lock; step() checks first
    }
    return true;
}

bool MembraneTick::set_gravity(bool on) {
    // THE FALL's switch (the lead wires POST /tick_gravity to this).
    // Turning gravity OFF returns the body to its authored rest exactly
    // -- no hidden decay, deterministic state (the flex-0 precedent).
    std::lock_guard<std::mutex> lk(seal_mtx_);
    gravity_on_ = on;
    if (!on) {
        root_y_ = 0.f;
        root_vy_ = 0.f;
        g_contact_n_ = 0.f;
    }
    return true;
}

std::string MembraneTick::state_json() const {
    // reads the cell state other threads rewrite — hold the same mutex
    // (bounded by one tick; state reads are not on the render path)
    std::lock_guard<std::mutex> lk(seal_mtx_);
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
      << ",\"n_cells\":" << seal_cells_.size()
      << ",\"V_lower\":" << (seal_cells_.size() > 0 ? seal_cells_[0].vol : 0.f)
      << ",\"V_upper\":" << (seal_cells_.size() > 1 ? seal_cells_[1].vol : 0.f)
      << ",\"P_lower\":" << (seal_cells_.size() > 0 ? seal_cells_[0].p : 0.f)
      << ",\"P_upper\":" << (seal_cells_.size() > 1 ? seal_cells_[1].p : 0.f)
      << ",\"v0_lower\":" << (seal_cells_.size() > 0 ? seal_cells_[0].v0 : 0.f)
      << ",\"v0_upper\":" << (seal_cells_.size() > 1 ? seal_cells_[1].v0 : 0.f)
      << ",\"V_whole\":" << vol_whole_
      << ",\"conserve_pct\":" << conserve_pct_
      << ",\"seal_split\":" << seal_split_
      << ",\"seal_cuts\":" << seal_cuts_
      << ",\"seal_loops\":" << seal_loops_
      << ",\"seal_caps\":" << seal_caps_
      << ",\"dimple_m\":" << dimple_m_
      << ",\"gravity_on\":" << (gravity_on_ ? "true" : "false")
      << ",\"root_y\":" << root_y_
      << ",\"root_vy\":" << root_vy_
      << ",\"g_contact_n\":" << g_contact_n_
      << ",\"cells\":[";
    for (size_t i = 0; i < seal_cells_.size(); ++i) {
        const SealCell& c = seal_cells_[i];
        if (i) o << ",";
        o << "{\"v0\":" << c.v0 << ",\"V\":" << c.vol << ",\"P\":" << c.p
          << ",\"pieces\":" << (c.pieces.size() / 3)
          << ",\"caps\":" << c.caps
          << ",\"ylo\":" << c.ylo << ",\"yhi\":" << c.yhi << "}";
    }
    o << "]"
      << ",\"has_scene\":" << (has_scene_ ? "true" : "false") << "}";
    return o.str();
}





