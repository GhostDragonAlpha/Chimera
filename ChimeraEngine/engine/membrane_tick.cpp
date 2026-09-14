
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

// F1 STANCE constants -- the bars, not tunings (prereg derivation,
// SEAL_PREREGISTRATION.md "THE STANCE PREREGISTRATION"):
constexpr float STANCE_TAU_S          = 1.0f;  // the 1 s nulling bar
constexpr float STANCE_THETA_MAX_DEG  = 5.0f;  // the ankle ROM bar
constexpr float STANCE_BAND_M         = 0.05f; // support band: sole + 5 cm

// G1 GAIT bars -- every one named against an in-file law, none tuned
// (prereg: SEAL_PREREGISTRATION.md, "THE GAIT CHECKPOINT PREREGISTRATION").
constexpr float GAIT_SINK_M       = 0.01f;   // the derived rest sink (header: k*s = m*g)
constexpr float GAIT_BEARING_FRAC = 0.8f;    // bearing = depth >= 80% of the sink
constexpr float GAIT_SETTLE_VY    = 1e-3f;   // m/s (the 0.1 mm press-cutoff scale)
constexpr float GAIT_P_RELAX_PA   = 5.0e4f;  // 50 kPa, the repo's named gentle-hand bar
constexpr float GAIT_MIN_CHANNEL  = 1e-3f;   // m/rad -- the F1 no-channel refusal
constexpr float GAIT_MAX_ANG      = 89.f * 3.14159265358979f / 180.f; // pose_index's ROM law
constexpr size_t GAIT_LOG_N       = 16;      // bounded transition log

// F1: whole-body centroid + centroid over a FIXED index set (the frozen
// support). The support set is frozen at stance-engage because a
// per-frame re-selected min-y band CHASES the ankle pitch (the toe
// dives into the band, the heel rises out) and self-cancels the very
// channel the servo drives -- measured on this sculpt:
// |S| 0.056 m/rad re-selected vs 0.283 m/rad frozen (prereg DERIVATION).
void lean_centroids(const std::vector<float>& v9,
                    const std::vector<uint32_t>& sup,
                    float* cx, float* cz, float* sx, float* sz) {
    const size_t n = v9.size() / 9;
    float cxa = 0.f, cza = 0.f;
    for (size_t v = 0; v < n; ++v) { cxa += v9[v * 9 + 0]; cza += v9[v * 9 + 2]; }
    float sxa = 0.f, sza = 0.f;
    for (uint32_t v : sup) {
        sxa += v9[(size_t)v * 9 + 0];
        sza += v9[(size_t)v * 9 + 2];
    }
    const float inv_n = n ? 1.f / (float)n : 0.f;
    const float inv_s = sup.size() ? 1.f / (float)sup.size() : 0.f;
    *cx = cxa * inv_n; *cz = cza * inv_n;
    *sx = sxa * inv_s; *sz = sza * inv_s;
}

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

// G1: min y of a frozen vertex set on a posed buffer (shared by the
// enable probes and the per-tick measurement).
float gait_set_miny(const std::vector<float>& v9,
                    const std::vector<uint32_t>& set) {
    float lo = 1e30f;
    for (uint32_t v : set) lo = std::min(lo, v9[(size_t)v * 9 + 1]);
    return lo;
}

// G1: centroid of a frozen vertex set on a posed buffer.
void gait_set_centroid(const std::vector<float>& v9,
                       const std::vector<uint32_t>& set,
                       float* cx, float* cy, float* cz) {
    float sx = 0.f, sy = 0.f, sz = 0.f;
    for (uint32_t v : set) {
        sx += v9[(size_t)v * 9 + 0];
        sy += v9[(size_t)v * 9 + 1];
        sz += v9[(size_t)v * 9 + 2];
    }
    const float inv = set.empty() ? 0.f : 1.f / (float)set.size();
    *cx = sx * inv; *cy = sy * inv; *cz = sz * inv;
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
    // THE MESH-SWAP SEAL CLEAR (C1's crash root cause, landed by the lead):
    // init() rebuilds the cell field for the NEW mesh but the seal tree
    // held the OLD creature's slot ids — verts9 reads through them ran
    // ~600 KB past the buffer on any swap onto a sealed tick (the import
    // crash, detonating in a map alloc). A new body is born unsealed.
    seal_cells_.clear(); sealed_ = false; cut_src_.clear(); cut_pos_.clear();
    seal_nv_ = 0; vol_whole0_ = vol_whole_ = 0.f; conserve_pct_ = 0.f;
    seal_split_ = seal_cuts_ = seal_loops_ = seal_caps_ = 0;
    seal_refusal_.clear();   // a new body carries no refusals
    root_y_ = root_vy_ = 0.f;    // a new body starts at its authored rest
    g_contact_n_ = 0.f;          // (gravity_on_ itself survives re-init:
                                 //  the law applies to whatever body loads)
    // F1: a new body starts UN-STANCED -- its frozen support set and
    // derived gain described the OLD geometry and must not survive a
    // mesh swap (the C1 crash class: stale indices into a new body).
    stance_on_ = false;
    stance_th_ = 0.f;
    stance_sup_.clear();
    // G1: gait state dies with the body -- the frozen vertex sets
    // describe the OLD geometry (the C1 stale-index crash class).
    gait_on_ = false;
    gait_phase_[0] = gait_phase_[1] = MembraneTick::GaitPhase::STANCE;
    gait_foot_verts_[0].clear();
    gait_foot_verts_[1].clear();
    for (int s = 0; s < 2; ++s) {
        gait_patch_r_[s] = 0.f;   gait_foot_rest_z_[s] = 0.f;
        gait_dminy_hip_[s] = 0.f; gait_dminy_knee_[s] = 0.f;
        gait_dcz_hip_[s] = 0.f;   gait_dcz_knee_[s] = 0.f;
        gait_rate_hip_[s] = 0.f;  gait_rate_knee_[s] = 0.f;
        gait_lift_ah_[s] = 0.f;   gait_lift_ak_[s] = 0.f;
        gait_lift_ch_[s] = 0.f;
        gait_knee_rad_[s] = 0.f;  gait_hip_rad_[s] = 0.f;
        gait_depth_[s] = 0.f;     gait_clear_[s] = 0.f;
        gait_block_[s].clear();
        gait_last_done_[s] = 0;
    }
    gait_lean_ref_x_ = gait_lean_ref_z_ = 0.f;
    gait_lean_x_ = gait_lean_z_ = 0.f;
    gait_p_max_ = 0.f;
    gait_feet_cell_ = -1;
    gait_strut_pin_[0] = gait_strut_pin_[1] = -1;   // drives unresolved
    gait_clear_pin_[0] = gait_clear_pin_[1] = -1;   // until the next enable
    gait_stride_count_ = 0;
    gait_log_.clear();
    gait_enable_block_.clear();   // the new body has answered nothing yet
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
    // E2: per-vertex AVERAGED load through a saturating ramp t/(1+t). The
    // per-cell write let the LAST cell touching a vertex win, painting a
    // full-contrast ring at every joint-group boundary (measured 0.47
    // channel jump, .tmp/E2_SEAM_NOTE.md); the vertex's own average is
    // shared by both flanking cells and the saturating curve (slope <= 1,
    // -> 0 past capacity) turns that ring into a one-ring gradient
    // (0.47 -> 0.15 measured). A failed cell darkens every vertex it
    // touches, deterministically (was last-writer-wins).
    {
        const size_t nvt = verts9.size() / 9;
        std::vector<float> tsum(nvt, 0.f);
        std::vector<uint32_t> tcnt(nvt, 0u);
        std::vector<uint8_t> vfail(nvt, 0u);
        for (size_t i = 0; i < cells_.size(); ++i) {
            const Cell& c = cells_[i];
            float t = std::min(1.f, c.load / std::max(capacity_[i], 1.f));
            for (int k = 0; k < 3; ++k) {
                uint32_t v = tri_verts_[i * 3 + (size_t)k];
                if (c.failed) vfail[v] = 1u;
                else { tsum[v] += t; tcnt[v] += 1u; }
            }
        }
        for (size_t v = 0; v < nvt; ++v) {
            float out[3];
            if (vfail[v]) {
                out[0] = out[1] = out[2] = 0.08f;
            } else {
                float t = tsum[v] / (tcnt[v] ? (float)tcnt[v] : 1.f);
                t = t / (1.f + t);   // saturating: softens group boundaries
                out[0] = base_color_[v * 3 + 0]
                       + (1.f - base_color_[v * 3 + 0]) * t;
                out[1] = base_color_[v * 3 + 1] * (1.f - t * 0.85f);
                out[2] = base_color_[v * 3 + 2] * (1.f - t * 0.85f);
            }
            for (int k = 0; k < 3; ++k)
                verts9[v * 9 + 6 + (size_t)k] = std::min(out[k], 1.f);
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
            // THE LIVE FLOOR (H8 world-doctor): a real pose or press
            // shifts a real cell by tens of percent; a cell reading
            // under 0.5% of its OWN rest volume has collapsed to its
            // surface-sampling noise, and the kappa law below would
            // answer p -> 1/kappa = 2.17 GPa (145x the skin yield) --
            // the live cell-4 lesson poison (1.6228 GPa on V=0.000).
            // Withhold the pressure BY NAME: p reads 0 and the
            // exported flag tells the truth instead.
            c.degenerate = v < SEAL_DEGENERATE_FRAC * c.v0;
            c.p = c.degenerate ? 0.f : (c.v0 - v) / (kappa_ * c.v0);
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

    // ═══ F1: THE STANCE (the balance rung; prereg appended to
    // SEAL_PREREGISTRATION.md) ═══════════════════════════════════════
    // The body keeps itself balanced: lean -- the horizontal (xz) offset
    // of the whole-body posed centroid from its FROZEN support set (the
    // contact patch identified at stance engage) -- drives BOTH ankles
    // as one integral servo:
    //   dtheta/dt = -k_p * lean_z,   |theta| <= 5 deg,
    // with k_p = 1/(|S|*tau) derived at set_stance(true) from this
    // engine's own travel arithmetic (a +1 deg ankle probe on the rest
    // blend), tau = 1 s (the nulling bar). A static-gain plant
    // integrated by the controller nulls any PERSISTENT disturbance
    // exactly (a held touch, a held pose): lean_ss -> 0, and the
    // state-clamped integrator saturates gracefully beyond the
    // authority A = |S|*5 deg ~= 2.8 cm -- no windup, no ringing.
    // Poses only: no root teleporting, no invented forces. Only while
    // gravity is on (balance exists only in a gravity field). Placed
    // AFTER travel/press (reads the posed surface) and BEFORE the root
    // offset (a uniform translation leaves xz unchanged). Disclosed in
    // the prereg: every pin rotates about X, so the actuated subspace
    // is the SAGITTAL (z) lean; the coronal (x) lean is measured and
    // reported but unactuated (no twist axis in the travel law).
    if (stance_on_ && gravity_on_ && classified
        && !stance_sup_.empty()
        && joint_deg_.size() > (size_t)std::max(ANKLE_PIN_L, ANKLE_PIN_R)) {
        float cx, cz, sx, sz;
        lean_centroids(verts9, stance_sup_, &cx, &cz, &sx, &sz);
        const float lean_x = (cx - sx) - lean_ref_x_;
        const float lean_z = (cz - sz) - lean_ref_z_;
        const float dts = std::min(std::max(dt, 0.f), 0.05f);  // stall guard
        stance_th_ -= stance_kp_ * lean_z * dts;
        const float th_max = STANCE_THETA_MAX_DEG * 3.14159265358979f / 180.f;
        stance_th_ = std::min(std::max(stance_th_, -th_max), th_max);
        joint_deg_[ANKLE_PIN_L] = stance_th_;
        joint_deg_[ANKLE_PIN_R] = stance_th_;
        stance_lean_x_ = lean_x;
        stance_lean_z_ = lean_z;
    }

    // ═══ G1: THE GAIT CHECKPOINT MACHINE (the robot-stack rung 2;
    // prereg appended to SEAL_PREREGISTRATION.md) ══════════════════════
    // Per-leg STANCE -> LIFT -> REACH -> LOAD (+ RECOVER, the measured
    // abort), every transition gated by a number the body reports --
    // per-side foot contact depth against the floor plane, sealed-cell
    // pressures, lean and support geometry -- and NO phase advances on a
    // timer: dt enters only through the rate caps and the servo
    // integration. Actuates hip/knee pins 13-16 ONLY, rate-capped (no
    // teleporting); placed AFTER the F1 stance block so the ankles stay
    // F1-owned (composition, not clobbering), and BEFORE the root offset
    // so the measurements read the un-translated posed surface (world y
    // adds root_y_ explicitly). The falsifier: cutting the machine
    // mid-stride stops every controller-driven motion within one tick --
    // it must NEVER glide. Every transition logs its measured gate
    // values (gait_log in state_json).
    if (gait_on_) gait_step_locked_(verts9, dt);

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

float MembraneTick::point_skin_dist2(const float p[3]) const {
    float best = 1e30f;
    const size_t nv = base_pos_.size() / 9;
    for (size_t v = 0; v < nv; ++v) {
        float dx = base_pos_[v * 9 + 0] - p[0];
        float dy = base_pos_[v * 9 + 1] - p[1];
        float dz = base_pos_[v * 9 + 2] - p[2];
        float d2 = dx * dx + dy * dy + dz * dz;
        if (d2 < best) best = d2;
    }
    return best;
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
        // THE DEGENERATE-SPLIT REFUSAL (H8 world-doctor): a component
        // under 0.5% of the parent's rest volume is surface noise, not
        // anatomy. Refusing here publishes NOTHING -- the parent stays
        // intact -- and names itself in state_json (seal_refusal).
        if (v < SEAL_DEGENERATE_FRAC * seal_cells_[cell_idx].v0) {
            seal_refusal_ = "degenerate_split";
            return false;
        }
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

bool MembraneTick::seal(float y, int cell_idx, int* outcome) {
    // MITOSIS — the recursive cut-and-weld (preregs 4eb9480c, be971e7c).
    // Cuts sealed cell `cell_idx` (0 = the whole creature before any
    // cut) into two sealed cells. Inserted points are convex blends over
    // original vertices, so they ride the posed surface at fixed weights.
    if (outcome) *outcome = SEAL_CUT;
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
    // ═══ THE ALREADY-SATISFIED SEAL (restore idempotency, R-restore-
    // ═══ doctor 2026-09-14) ══════════════════════════════════════════
    // The session snapshot journals INTENTS, and boot restore replays
    // them in order — but the accumulated history holds ~60 repeats of
    // the three foundation cuts, and every boot re-refused them (measured:
    // replayed:7, failed:60-66, seal_refusal "degenerate_split", history
    // +3 lines per restore attempt). A cut whose STATE ALREADY EXISTS is
    // not a failure and not a degenerate singularity: it is a no-op.
    // Two admission tests, both float-honest:
    //   (a) the named cell's own stored bounds sit on the plane — the
    //       bound was recorded when the cell (or an ancestor of this
    //       request's below-daughter) was cut at exactly y;
    //   (b) the plane does not cross the named cell AND some sealed cell
    //       carries the plane as a bound — the cut's partition already
    //       exists elsewhere in the tree (a repeat of an ancestor cut,
    //       e.g. {"y":3.415} against the feet cell it no longer spans).
    // A plane at a bound that CROSSES only because the recomputed blend
    // drifted a fraction of an ulp (H8's named mechanism) is caught by
    // (a) before the cut arithmetic can build a sliver daughter. The
    // refusal path keeps every genuinely degenerate/invalid cut: a plane
    // that crosses nothing and touches no bound (e.g. {"y":99}) still
    // falls through to the guard below.
    {
        auto on_bound = [&](float lo, float hi) {
            return std::fabs(y - lo) <= SEAL_ALREADY_TOL_M
                || std::fabs(y - hi) <= SEAL_ALREADY_TOL_M;
        };
        bool already = false;
        if (!seal_cells_.empty()) {
            const SealCell& named = seal_cells_[cell_idx];
            if (on_bound(named.ylo, named.yhi)) {
                already = true;                          // (a)
            } else if (y <= ymin || y >= ymax) {         // plane does not cross
                for (const SealCell& c : seal_cells_) {
                    if (on_bound(c.ylo, c.yhi)) {        // (b)
                        already = true;
                        break;
                    }
                }
            }
        }
        if (already) {
            // skipped, not executed: nothing published, nothing refused,
            // nothing re-journaled (the caller answers "seal":"already").
            if (outcome) *outcome = SEAL_ALREADY;
            return true;
        }
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
    // THE DEGENERATE-SPLIT REFUSAL (H8 world-doctor): either daughter
    // under 0.5% of the cut parent's rest volume is a flat/noise
    // artifact, not a water cell. The live poison entered exactly here:
    // re-cutting cell 0 at its own cap plane (y=0.338) passed the
    // plane-crossing guard above because seal() forces NEW cut slots to
    // py == y exactly (py.push_back(y)), while every LATER seal
    // re-evaluates those blends over rest9 (py[s] = sum w*rest9), which
    // drifts ~1 ulp below the plane — so the "plane outside the cell"
    // refusal never fired and the cut produced a closed double-layer
    // pancake (ylo == yhi == 0.338) with v0 = 4.655e-9 m^3 = 1.6e-8 of
    // its parent. Refuse BY NAME; nothing was published, the parent
    // stays intact (the replay/refusal is idempotent).
    {
        const float parent_v0 = seal_cells_.empty()
            ? vl + vu                       // first cut: daughters tile it
            : seal_cells_[cell_idx].v0;
        if (vl < SEAL_DEGENERATE_FRAC * parent_v0
            || vu < SEAL_DEGENERATE_FRAC * parent_v0) {
            seal_refusal_ = "degenerate_split";
            return false;
        }
    }

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
        seal_refusal_.clear();   // this cut is clean: the name clears
        sealed_ = true;   // published under the lock; step() checks first
    }
    return true;
}

// ═══ THE SEAL-TREE SNAPSHOT (restore idempotency, R-restore-doctor) ═══
// Wire format (little-endian), versioned by magic:
//   u32 magic 'SEL1' = 0x31534553
//   u32 nv                        -- the vertex count the tree was cut on
//   u32 n_cuts, n_cuts x {u32 n, u32 v[8], f32 w[8]}          (68 B each)
//   u32 n_cells, per cell: u32 piece_n, piece_n x u32,
//                          f32 v0, f32 vol, f32 p,
//                          i32 caps, f32 ylo, f32 yhi, u8 degenerate
// Loading validates before it mutates: nv must equal the loaded mesh's
// vertex count, every blend/cell index must be in range, and EVERY cell's
// rest volume is recomputed from its own pieces over this mesh's rest
// blend and compared with the stored v0 (1e-4 relative -- 50x under the
// degenerate guard's 0.5% band). Any mismatch refuses with NOTHING
// changed, and the caller falls back to the intent history, which
// rebuilds the tree the slow, honest way (executed cuts + already-skips).
static const uint32_t SEAL_STATE_MAGIC = 0x31534553u;  // 'SEL1'

bool MembraneTick::load_seal_state(const std::string& body) {
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return false;
    const uint32_t nv = (uint32_t)(base_pos_.size() / 9);
    if (nv == 0) return false;
    std::lock_guard<std::mutex> lk(seal_mtx_);

    auto rd32 = [&](size_t off, uint32_t* v) {
        if (off + 4 > body.size()) return false;
        std::memcpy(v, body.data() + off, 4);
        return true;
    };
    auto rdf32 = [&](size_t off, float* v) {
        return rd32(off, reinterpret_cast<uint32_t*>(v));
    };
    uint32_t magic = 0, hdr_nv = 0, n_cuts = 0, n_cells = 0;
    if (!rd32(0, &magic) || magic != SEAL_STATE_MAGIC) return false;
    if (!rd32(4, &hdr_nv) || hdr_nv != nv) return false;   // stale blob
    if (!rd32(8, &n_cuts) || n_cuts > (1u << 20)) return false;
    // cut blends: validate every index against the MESH vertices and
    // every weight sum against 1 (convex blends; seal() guarantees it)
    std::vector<CutBlend> cuts(n_cuts);
    {
        size_t off = 12;
        for (uint32_t k = 0; k < n_cuts; ++k, off += 4 + 32 + 32) {
            uint32_t n = 0;
            if (!rd32(off, &n) || n == 0 || n > 8) return false;
            cuts[k].n = (uint8_t)n;
            float wsum = 0.f;
            for (int i = 0; i < (int)n; ++i) {
                uint32_t vi = 0;
                float wv = 0.f;
                if (!rd32(off + 4 + (size_t)i * 4, &vi)) return false;
                if (vi >= nv) return false;                    // stale mesh
                if (!rdf32(off + 36 + (size_t)i * 4, &wv)) return false;
                cuts[k].v[i] = vi;
                cuts[k].w[i] = wv;
                wsum += wv;
            }
            if (!(wsum > 0.999f && wsum < 1.001f)) return false;
        }
        if (!rd32(off, &n_cells) || n_cells < 2 || n_cells > (1u << 16))
            return false;
    }
    // cells: parse into locals, then recompute each rest volume
    struct CellRec {
        std::vector<uint32_t> pieces;
        float v0 = 0.f, vol = 0.f, p = 0.f;
        int caps = 0;
        float ylo = 0.f, yhi = 0.f;
        bool degenerate = false;
    };
    std::vector<CellRec> cells(n_cells);
    {
        // (+4, R-restore-doctor): the u32 n_cells the cut block above just
        // consumed sits between the cut table and cell 0. Without it pn
        // reads n_cells itself (4 -> 4 % 3 != 0) and EVERY blob -- the
        // loader's own exports included -- refused in microseconds, so
        // every boot silently fell back to the intent-history replay
        // (measured: "seal-tree blob refused" on every boot, 3 seals
        // re-executed each boot, blob rewritten byte-identically).
        size_t off = 12 + n_cuts * (4 + 32 + 32) + 4;
        for (uint32_t ci = 0; ci < n_cells; ++ci) {
            uint32_t pn = 0;
            if (!rd32(off, &pn) || pn == 0 || pn > (1u << 24)
                || pn % 3 != 0)
                return false;
            off += 4;
            cells[ci].pieces.resize(pn);
            for (uint32_t p3 = 0; p3 < pn; ++p3, off += 4) {
                uint32_t s = 0;
                if (!rd32(off, &s) || s >= nv + n_cuts) return false;
                cells[ci].pieces[p3] = s;
            }
            if (!rdf32(off, &cells[ci].v0)) return false;      off += 4;
            if (!rdf32(off, &cells[ci].vol)) return false;     off += 4;
            if (!rdf32(off, &cells[ci].p)) return false;       off += 4;
            {
                int32_t caps32 = 0;
                if (off + 4 > body.size()) return false;
                std::memcpy(&caps32, body.data() + off, 4);
                cells[ci].caps = (int)caps32;
                if (caps32 < 0) return false;
            }                                                  off += 4;
            if (!rdf32(off, &cells[ci].ylo)) return false;     off += 4;
            if (!rdf32(off, &cells[ci].yhi)) return false;     off += 4;
            {
                uint8_t dg = 0;
                if (off + 1 > body.size()) return false;
                dg = (uint8_t)body[off];
                cells[ci].degenerate = dg != 0;
            }                                                  off += 1;
            if (!(cells[ci].v0 > 0.f)) return false;
        }
        if (off != body.size()) return false;   // trailing bytes = wrong gen
    }

    // THE VOLUME WITNESS: recompute every cell's rest volume on THIS
    // mesh's rest blend (the exact arithmetic seal() publishes with --
    // classified blend at zero angles, cut slots as weighted sums) and
    // demand it matches the stored v0.
    std::vector<float> rest9(base_pos_);
    {
        const bool classified = cell_joint_.size() == cells_.size()
                             && !joint_pins_.empty()
                             && joint_pins_.size() == joint_deg_.size()
                             && vert_bind_idx_.size() == (size_t)nv * 3
                             && vert_bind_w_.size() == (size_t)nv * 3;
        if (classified) apply_travel(rest9, nullptr);
    }
    auto slot3 = [&](uint32_t s, float* x, float* yy, float* z) {
        if (s < nv) {
            *x = rest9[s * 9 + 0]; *yy = rest9[s * 9 + 1];
            *z = rest9[s * 9 + 2];
        } else {
            const CutBlend& b = cuts[s - nv];
            float sx = 0.f, sy = 0.f, sz = 0.f;
            for (int i = 0; i < b.n; ++i) {
                sx += b.w[i] * rest9[b.v[i] * 9 + 0];
                sy += b.w[i] * rest9[b.v[i] * 9 + 1];
                sz += b.w[i] * rest9[b.v[i] * 9 + 2];
            }
            *x = sx; *yy = sy; *z = sz;
        }
    };
    const float vol_tol = 1e-4f;   // relative; 50x under the 0.5% guard
    for (const CellRec& c : cells) {
        float v = 0.f;
        for (size_t i = 0; i + 2 < c.pieces.size(); i += 3) {
            float ax, ay, az, bx, by, bz, cx, cy, cz;
            slot3(c.pieces[i], &ax, &ay, &az);
            slot3(c.pieces[i + 1], &bx, &by, &bz);
            slot3(c.pieces[i + 2], &cx, &cy, &cz);
            v += (ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz)
                + az * (bx * cy - by * cx)) / 6.f;
        }
        if (std::fabs(v - c.v0) > vol_tol * c.v0) return false;  // stale
    }

    // commit (under the lock taken at entry): the exact live tree
    std::vector<SealCell> publish(n_cells);
    for (uint32_t ci = 0; ci < n_cells; ++ci) {
        publish[ci].pieces = std::move(cells[ci].pieces);
        publish[ci].v0 = cells[ci].v0;
        publish[ci].vol = cells[ci].v0;   // rest pose: live vol == v0 until
                                          // the next tick re-measures
        publish[ci].p = 0.f;
        publish[ci].caps = cells[ci].caps;
        publish[ci].ylo = cells[ci].ylo;
        publish[ci].yhi = cells[ci].yhi;
        publish[ci].degenerate = cells[ci].degenerate;
    }
    seal_cells_ = std::move(publish);
    cut_src_ = std::move(cuts);
    cut_pos_.assign(cut_src_.size() * 3, 0.f);
    seal_nv_ = nv;
    sealed_ = true;
    seal_cuts_ = (int)n_cuts;      // report: the tree's cut count
    seal_refusal_.clear();         // a cleanly restored tree owes nothing
    return true;
}

void MembraneTick::export_seal_state(std::vector<uint8_t>& out) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (seal_cells_.empty()) { out.clear(); return; }
    const uint32_t nv = seal_nv_;
    const uint32_t n_cuts = (uint32_t)cut_src_.size();
    const uint32_t n_cells = (uint32_t)seal_cells_.size();
    size_t need = 12 + n_cuts * (4 + 32 + 32) + 4;
    for (const SealCell& c : seal_cells_)
        need += 4 + c.pieces.size() * 4 + 4 * 6 + 1;
    out.resize(need);
    uint8_t* w = out.data();
    auto wr = [&](const void* p, size_t n) {
        std::memcpy(w, p, n);
        w += n;
    };
    wr(&SEAL_STATE_MAGIC, 4);
    wr(&nv, 4);
    wr(&n_cuts, 4);
    for (const CutBlend& b : cut_src_) {
        uint32_t n = b.n;
        wr(&n, 4);
        wr(b.v.data(), 32);
        wr(b.w.data(), 32);
    }
    wr(&n_cells, 4);
    for (const SealCell& c : seal_cells_) {
        uint32_t pn = (uint32_t)c.pieces.size();
        wr(&pn, 4);
        if (pn) wr(c.pieces.data(), pn * 4);
        wr(&c.v0, 4);
        wr(&c.vol, 4);
        wr(&c.p, 4);
        int32_t caps32 = (int32_t)c.caps;
        wr(&caps32, 4);
        wr(&c.ylo, 4);
        wr(&c.yhi, 4);
        uint8_t dg = c.degenerate ? 1 : 0;
        wr(&dg, 1);
    }
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
        stance_off_locked_();   // F1: the rest contract is exact -- the
                                // servo may not keep holding ankle poses
                                // the law no longer balances
    }
    return true;
}

// F1: the stance switch (the lead wires POST /tick_stance to this,
// next to POST /tick_gravity). Everything measurable is derived here,
// under the lock, from this engine's own arithmetic -- no tuned gains.
bool MembraneTick::set_stance(bool on) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (!on) { stance_off_locked_(); return true; }

    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return false;
    const size_t nv = base_pos_.size() / 9;
    const bool classified = cell_joint_.size() == cells_.size()
                         && !joint_pins_.empty()   // bindings without pins = OOB
                         && joint_pins_.size() == joint_deg_.size()
                         && vert_bind_idx_.size() == nv * 3
                         && vert_bind_w_.size() == nv * 3;
    if (!classified
        || joint_deg_.size() <= (size_t)std::max(ANKLE_PIN_L, ANKLE_PIN_R))
        return false;   // no travel bindings / no ankle pins: refuse honestly

    // The support set: the rest blend's min-y band, FROZEN (why frozen:
    // a re-selected band chases the ankle pitch and self-cancels the
    // channel -- measured 0.056 vs 0.283 m/rad, prereg DERIVATION).
    // rest9 is the exact surface the tick itself produces at rest --
    // seal()'s rest-blend path, so the reference is deterministic.
    std::vector<float> rest9(base_pos_);
    apply_travel(rest9, nullptr);
    float lo = nv ? rest9[1] : 0.f;
    for (size_t v = 1; v < nv; ++v)
        lo = std::min(lo, rest9[v * 9 + 1]);
    const float band_hi = lo + STANCE_BAND_M;
    std::vector<uint32_t> sup;
    sup.reserve(256);
    for (size_t v = 0; v < nv; ++v)
        if (rest9[v * 9 + 1] <= band_hi) sup.push_back((uint32_t)v);
    if (sup.empty()) return false;   // nothing on the ground: refuse

    // Rest lean reference (the tail puts -0.84 m of "lean" into the
    // metric at authored rest): the servo nulls the ERROR from rest.
    float cx, cz, sx, sz;
    lean_centroids(rest9, sup, &cx, &cz, &sx, &sz);

    // |S| measured on this engine's own travel arithmetic: pose the
    // rest blend +1 deg on BOTH ankles and read d(lean_z).
    std::vector<float> probe9(rest9);
    std::vector<float> degs(joint_deg_.size(), 0.f);
    degs[ANKLE_PIN_L] = degs[ANKLE_PIN_R] =
        1.f * 3.14159265358979f / 180.f;
    apply_travel(probe9, &degs);
    float pcx, pcz, psx, psz;
    lean_centroids(probe9, sup, &pcx, &pcz, &psx, &psz);
    const float S = ((pcz - psz) - (cz - sz)) / degs[ANKLE_PIN_L];
    if (std::fabs(S) < 1e-3f) return false;   // no measurable channel

    stance_kp_ = 1.f / (std::fabs(S) * STANCE_TAU_S);
    lean_ref_x_ = cx - sx;
    lean_ref_z_ = cz - sz;
    stance_sup_ = std::move(sup);
    stance_th_ = 0.f;
    joint_deg_[ANKLE_PIN_L] = 0.f;
    joint_deg_[ANKLE_PIN_R] = 0.f;
    stance_on_ = true;
    return true;
}

void MembraneTick::stance_off_locked_() {
    // Deterministic off: ankles to authored 0 (the flex-0 precedent) --
    // no hidden pose decay, no stale integrator.
    stance_on_ = false;
    stance_th_ = 0.f;
    if (joint_deg_.size() > (size_t)std::max(ANKLE_PIN_L, ANKLE_PIN_R)) {
        joint_deg_[ANKLE_PIN_L] = 0.f;
        joint_deg_[ANKLE_PIN_R] = 0.f;
    }
}

// ═══ G1: THE GAIT CHECKPOINT MACHINE ══════════════════════════════════

const char* MembraneTick::gait_phase_name(GaitPhase p) {
    switch (p) {
        case GaitPhase::LIFT:    return "LIFT";
        case GaitPhase::REACH:   return "REACH";
        case GaitPhase::LOAD:    return "LOAD";
        case GaitPhase::RECOVER: return "RECOVER";
        default:                 return "STANCE";
    }
}

void MembraneTick::gait_log_locked_(int leg, const char* from,
                                    const char* to,
                                    const std::string& gates) {
    std::ostringstream e;
    e << "{\"tick\":" << ticks_
      << ",\"leg\":\"" << (leg == 0 ? "L" : "R")
      << "\",\"from\":\"" << from << "\",\"to\":\"" << to
      << "\",\"gates\":" << gates << "}";
    gait_log_.push_back(e.str());
    if (gait_log_.size() > GAIT_LOG_N)
        gait_log_.erase(gait_log_.begin(),
                        gait_log_.begin() + (gait_log_.size() - GAIT_LOG_N));
}

void MembraneTick::gait_off_locked_() {
    // Deterministic off (the flex-0 precedent): hips/knees to authored 0,
    // all legs to STANCE -- no hidden decay, no stale integrator. A cut
    // MID-STRIDE logs the abort with the measured state: that entry is
    // the F-GLIDE falsifier's evidence (P3 in the prereg).
    for (int s = 0; s < 2; ++s) {
        if (gait_phase_[s] != GaitPhase::STANCE || gait_knee_rad_[s] != 0.f
            || gait_hip_rad_[s] != 0.f) {
            std::ostringstream g;
            g << "{\"why\":\"cut\",\"vy\":" << root_vy_
              << ",\"dL\":" << gait_depth_[0]
              << ",\"dR\":" << gait_depth_[1]
              << ",\"knee\":" << gait_knee_rad_[s] * 57.29577951308232
              << ",\"hip\":" << gait_hip_rad_[s] * 57.29577951308232 << "}";
            gait_log_locked_(s, gait_phase_name(gait_phase_[s]), "STANCE",
                             g.str());
        }
        gait_phase_[s] = GaitPhase::STANCE;
        gait_knee_rad_[s] = gait_hip_rad_[s] = 0.f;
        gait_block_[s].clear();
    }
    gait_on_ = false;
    if (joint_deg_.size() > (size_t)KNEE_PIN_R) {
        joint_deg_[HIP_PIN_L] = joint_deg_[HIP_PIN_R] = 0.f;
        joint_deg_[KNEE_PIN_L] = joint_deg_[KNEE_PIN_R] = 0.f;
    }
    // THE COMPOSED ANKLES (the V3a audit fix): while armed, the machine
    // writes joint_deg_[strut_pin] = stance_th_ + its own strut component
    // (the prereg's "composes over" law). Disarming stops the write; the
    // pin must return to stance's OWN component exactly, not to 0 -- a
    // zero here would stomp the balance servo's live lean term.
    for (int s = 0; s < 2; ++s) {
        if (gait_strut_pin_[s] >= 0
            && (size_t)gait_strut_pin_[s] < joint_deg_.size())
            joint_deg_[(size_t)gait_strut_pin_[s]]
                = stance_on_ ? stance_th_ : 0.f;
    }
}

// G1: the gait switch (the lead wires POST /tick_gait to this, next to
// POST /tick_stance). Everything measurable is derived here, under the
// lock, from this engine's own arithmetic -- probes, never tunings
// (Rule 1: if a number needed choosing, the derivation broke).
bool MembraneTick::set_gait(bool on) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (!on) { gait_off_locked_(); gait_enable_block_.clear(); return true; }

    // the rung stack, checked in order, each refusal HONEST BY NAME
    // (gait_enable_block_ -- the seal_refusal_ law: a bare ok:false made
    // the restored-body gait refusal undiagnosable for a full ship-day).
    gait_enable_block_ = "no_scene";
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return false;
    if (!gravity_on_) { gait_enable_block_ = "gravity_off"; return false; }
    if (!stance_on_)  { gait_enable_block_ = "stance_off";  return false; }
    const size_t nv = base_pos_.size() / 9;
    const bool classified = cell_joint_.size() == cells_.size()
                         && !joint_pins_.empty()   // bindings without pins = OOB
                         && joint_pins_.size() == joint_deg_.size()
                         && vert_bind_idx_.size() == nv * 3
                         && vert_bind_w_.size() == nv * 3;
    if (!classified) { gait_enable_block_ = "unclassified"; return false; }
    if (joint_deg_.size() <= (size_t)KNEE_PIN_R) {
        gait_enable_block_ = "no_leg_pins";
        return false;
    }
    if (!sealed_ || seal_cells_.size() < 2) {
        gait_enable_block_ = "unsealed";   // need the feet cell
        return false;
    }

    // the feet cell: the sealed cell with the LOWEST yhi (the cell tree's
    // index order is cut HISTORY, not anatomy -- measured live: the feet
    // are cell 0 of 4, but only the y-band names them).
    int feet = -1;
    float feet_yhi = 1e30f;
    for (size_t i = 0; i < seal_cells_.size(); ++i)
        if (seal_cells_[i].yhi < feet_yhi) {
            feet_yhi = seal_cells_[i].yhi;
            feet = (int)i;
        }
    if (feet < 0 || !(feet_yhi < 1e29f)) {
        gait_enable_block_ = "no_feet_cell";
        return false;
    }

    // rest blend: the exact surface the tick itself produces at rest
    // (the seal()/set_stance path), so every reference is deterministic.
    std::vector<float> rest9(base_pos_);
    apply_travel(rest9, nullptr);

    // frozen per-side foot vertex sets: the feet cell's rest band, split
    // by the body's own L/R convention (x >= 0 = L, as in init()/flex()).
    std::vector<uint32_t> fset[2];
    for (size_t v = 0; v < nv; ++v) {
        if (rest9[v * 9 + 1] > feet_yhi) continue;
        fset[rest9[v * 9 + 0] >= 0.f ? 0 : 1].push_back((uint32_t)v);
    }
    if (fset[0].empty() || fset[1].empty()) {
        gait_enable_block_ = std::string("foot_set_empty_")
            + (fset[0].empty() ? "L" : "R");
        return false;
    }

    // frozen patch geometry: centroid + radius (xz) per side. The radius
    // is the STRIDE bar (a footfall must land outside the old support
    // patch -- geometric necessity) and the speed bar (below).
    float pcx[2], pcy[2], pcz[2], prad[2];
    for (int s = 0; s < 2; ++s) {
        gait_set_centroid(rest9, fset[s], &pcx[s], &pcy[s], &pcz[s]);
        float acc = 0.f;
        for (uint32_t v : fset[s]) {
            float dx = rest9[v * 9 + 0] - pcx[s];
            float dz = rest9[v * 9 + 2] - pcz[s];
            acc += dx * dx + dz * dz;
        }
        prad[s] = std::sqrt(acc / (float)fset[s].size());
        if (!(prad[s] > 1e-3f)) {
            gait_enable_block_ = std::string("patch_degenerate_")
                + (s == 0 ? "L" : "R");
            return false;   // degenerate patch: refuse
        }
    }

    // rest lean reference (whole-body centroid vs the both-feet support):
    // the servo/gates null the ERROR from rest (the tail is not "lean").
    float bx = 0.f, bz = 0.f;
    for (size_t v = 0; v < nv; ++v) { bx += rest9[v * 9 + 0]; bz += rest9[v * 9 + 2]; }
    bx /= (float)nv; bz /= (float)nv;
    const float snr = (float)(fset[0].size() + fset[1].size());
    const float sczr = (pcz[0] * (float)fset[0].size()
                      + pcz[1] * (float)fset[1].size()) / snr;

    // probes: +1 deg per pin on the rest blend (the F1 probe precedent).
    // MEASURED per pin: d(foot-set min y) and d(foot centroid z), SIGNED.
    //
    // THE DRIVE PINS ARE MEASURED, NOT ASSUMED (the V3a audit): the
    // shipped vertbind gives the foot sets EXACTLY ZERO hip-pin weight
    // (measured on the live blob: the L foot set's 1289-vert blend mass
    // sits 1095.96 on ankle_L, 63.20 on knee_L, 130.85 on the
    // contralateral FILL ankle, 0.000 on hip_L -- pure skinning has no
    // hip-to-foot chain, so a +1 deg hip probe moves no foot vertex and
    // the shipped hardcoded-hip probe read 0.0 -> no_channel_hip_L0 on
    // EVERY world this authoring line builds, fresh or restored).
    // THE LAW (derived, no taste): a pin's authority for a side is its
    // NET blend weight on that side's foot set (own minus opposite -- a
    // pin belongs to the side it moves more; this rejects the fill
    // ankle, whose net is negative). Each side's drive pair = its two
    // highest-net pins; the STRUT role (REACH z-servo) goes to whichever
    // has the larger |dcz| probe, the CLEAR role (LIFT/REACH clearance)
    // to the other. Refusal names carry the resolved pin ids.
    const size_t npins = joint_deg_.size();
    std::vector<float> wnet[2];   // per-side net blend weight per pin
    for (int s = 0; s < 2; ++s) wnet[s].assign(npins, 0.f);
    for (size_t v = 0; v < nv; ++v) {
        const int own = rest9[v * 9 + 1] > feet_yhi
            ? -1 : (rest9[v * 9 + 0] >= 0.f ? 0 : 1);
        if (own < 0) continue;   // not in either foot set
        for (int k = 0; k < 3; ++k) {
            const uint8_t j = vert_bind_idx_[v * 3 + (size_t)k];
            if ((size_t)j < npins)
                wnet[own][(size_t)j] += vert_bind_w_[v * 3 + (size_t)k];
        }
    }
    int cand[2][2] = {{-1, -1}, {-1, -1}};   // top-2 net pins per side
    float cand_net[2][2] = {{0.f, 0.f}, {0.f, 0.f}};
    for (size_t j = 0; j < npins; ++j) {
        const float dl = wnet[0][j] - wnet[1][j];   // net for the L side
        for (int s = 0; s < 2; ++s) {
            const float d = s == 0 ? dl : -dl;
            if (d <= 0.f) continue;   // the other side owns this pin
            float* cn = cand_net[s];
            int*    cc = cand[s];
            if (d > cn[0]) {
                cn[1] = cn[0]; cc[1] = cc[0]; cn[0] = d; cc[0] = (int)j;
            } else if (d > cn[1]) {
                cn[1] = d; cc[1] = (int)j;
            }
        }
    }
    for (int s = 0; s < 2; ++s) {
        if (cand[s][0] < 0 || cand[s][1] < 0) {
            gait_enable_block_ = std::string("no_drive_pins_")
                + (s == 0 ? "L" : "R");
            return false;   // the binding gives this side no leg to drive
        }
    }
    const uint8_t drive_pin[2][2] = {   // [side] [0=strut-cand, 1=clear-cand]
        {(uint8_t)cand[0][0], (uint8_t)cand[0][1]},
        {(uint8_t)cand[1][0], (uint8_t)cand[1][1]}};
    float dminy_cand[2][2], dcz_cand[2][2];   // probes per candidate
    for (int s = 0; s < 2; ++s) {
        const float miny0 = gait_set_miny(rest9, fset[s]);
        float cx0, cy0, cz0;
        gait_set_centroid(rest9, fset[s], &cx0, &cy0, &cz0);
        for (int c = 0; c < 2; ++c) {
            std::vector<float> degs(npins, 0.f);
            std::vector<float> p9;
            float cx, cy, cz;
            degs[(size_t)drive_pin[s][c]] = 1.f * 3.14159265358979f / 180.f;
            p9 = rest9;
            apply_travel(p9, &degs);
            dminy_cand[s][c] = gait_set_miny(p9, fset[s]) - miny0;
            gait_set_centroid(p9, fset[s], &cx, &cy, &cz);
            dcz_cand[s][c] = cz - cz0;
            const float m = std::sqrt(dminy_cand[s][c] * dminy_cand[s][c]
                                    + dcz_cand[s][c] * dcz_cand[s][c]);
            if (m < GAIT_MIN_CHANNEL) {
                // no measurable channel (the F1 refusal) -- NAME it:
                // which side, which resolved pin, the measured magnitude
                // against the bar, so the next auditor reads the
                // anatomy, not a bare ok:false.
                std::ostringstream b;
                b << "no_channel_pin" << (int)drive_pin[s][c]
                  << (s == 0 ? "_L_" : "_R_") << m;
                gait_enable_block_ = b.str();
                return false;
            }
        }
    }
    // slot the roles by the MEASURED z authority (never by anatomy)
    float dminy_strut[2], dcz_strut[2], dminy_clear[2], dcz_clear[2];
    int strut_pin[2], clear_pin[2];
    for (int s = 0; s < 2; ++s) {
        const bool first_is_strut =
            std::fabs(dcz_cand[s][0]) >= std::fabs(dcz_cand[s][1]);
        const int si = first_is_strut ? 0 : 1, ci = first_is_strut ? 1 : 0;
        strut_pin[s] = drive_pin[s][si];
        clear_pin[s] = drive_pin[s][ci];
        dminy_strut[s] = dminy_cand[s][si];
        dcz_strut[s]   = dcz_cand[s][si];
        dminy_clear[s] = dminy_cand[s][ci];
        dcz_clear[s]   = dcz_cand[s][ci];
    }

    // measured arc channels -> derived rate caps: the foot's linear speed
    // never exceeds its own patch radius per tau (the bar). The slot
    // aliases keep the commit/log field names stable (gait_dminy_hip_ now
    // carries the STRUT pin's channel -- resolved above, named below).
    float dminy_hip[2], dminy_knee[2], dcz_hip[2], dcz_knee[2];
    float rate_hip[2], rate_knee[2];
    for (int s = 0; s < 2; ++s) {
        const float ms = std::sqrt(dminy_strut[s] * dminy_strut[s]
                                 + dcz_strut[s] * dcz_strut[s]);
        const float mc = std::sqrt(dminy_clear[s] * dminy_clear[s]
                                 + dcz_clear[s] * dcz_clear[s]);
        dminy_hip[s] = dminy_strut[s];   dcz_hip[s] = dcz_strut[s];
        dminy_knee[s] = dminy_clear[s];  dcz_knee[s] = dcz_clear[s];
        rate_hip[s]  = (prad[s] / STANCE_TAU_S) / ms;
        rate_knee[s] = (prad[s] / STANCE_TAU_S) / mc;
    }

    // the LIFT combo: the strut:clear ratio that nulls the centroid z
    // drift (a_h = dcz_clear, a_k = -dcz_strut: a_h*dcz_s + a_k*dcz_c
    // == 0), with its measured rise channel ch = a_h*dminy_strut
    // + a_k*dminy_clear. NO enable refusal on |ch| here (the shipped
    // no_lift_channel gate is REMOVED by the V3a audit): the prereg's own
    // law for this number is "the linear-channel estimate only sizes the
    // step, and the measured error closes the rest" -- on the shipped
    // binding the null-z rise channel is 1.66e-5 m/deg (the two drive
    // channels are nearly collinear), while the REAL lift is 4.6 deg of
    // ankle within the 89-deg ROM, rate-capped by mx. An enable refusal
    // here would refuse a body its own gates can walk; the falsifier for
    // that claim is F-STALL (a phase not reaching its gate within 10 tau
    // -> the derivation is wrong). The servo stays well-defined as
    // ch -> 0: dparam is clamped by mx (the rate caps) before use.
    float lift_ah[2], lift_ak[2], lift_ch[2];
    for (int s = 0; s < 2; ++s) {
        lift_ah[s] = dcz_knee[s];
        lift_ak[s] = -dcz_hip[s];
        lift_ch[s] = lift_ah[s] * dminy_hip[s] + lift_ak[s] * dminy_knee[s];
    }

    // commit (all under the lock taken at entry)
    gait_foot_verts_[0] = std::move(fset[0]);
    gait_foot_verts_[1] = std::move(fset[1]);
    for (int s = 0; s < 2; ++s) {
        gait_patch_r_[s] = prad[s];
        gait_foot_rest_z_[s] = pcz[s];
        gait_dminy_hip_[s] = dminy_hip[s];
        gait_dminy_knee_[s] = dminy_knee[s];
        gait_dcz_hip_[s] = dcz_hip[s];
        gait_dcz_knee_[s] = dcz_knee[s];
        gait_rate_hip_[s] = rate_hip[s];
        gait_rate_knee_[s] = rate_knee[s];
        gait_lift_ah_[s] = lift_ah[s];
        gait_lift_ak_[s] = lift_ak[s];
        gait_lift_ch_[s] = lift_ch[s];
        gait_phase_[s] = GaitPhase::STANCE;
        gait_knee_rad_[s] = gait_hip_rad_[s] = 0.f;
        gait_block_[s].clear();
        gait_last_done_[s] = 0;
    }
    gait_lean_ref_x_ = bx - ((pcx[0] * (float)gait_foot_verts_[0].size()
                            + pcx[1] * (float)gait_foot_verts_[1].size()) / snr);
    gait_lean_ref_z_ = bz - sczr;
    gait_feet_cell_ = feet;
    for (int s = 0; s < 2; ++s) {
        gait_strut_pin_[s] = strut_pin[s];
        gait_clear_pin_[s] = clear_pin[s];
    }
    gait_stride_count_ = 0;
    gait_log_.clear();
    gait_enable_block_.clear();   // armed: nothing blocks this body
    // bearing enforcement at arm (the shipped law): the legacy leg pins
    // to authored 0; the drive pins take their composed arm values (the
    // strut component is 0 at arm, so the ankle pin carries exactly
    // stance's own lean term -- the machine composes over it, never
    // clobbers it).
    joint_deg_[HIP_PIN_L] = joint_deg_[HIP_PIN_R] = 0.f;
    for (int s = 0; s < 2; ++s) {
        if ((size_t)clear_pin[s] < npins)
            joint_deg_[(size_t)clear_pin[s]] = 0.f;
        if ((size_t)strut_pin[s] < npins)
            joint_deg_[(size_t)strut_pin[s]] = stance_th_;
    }
    gait_on_ = true;
    {
        std::ostringstream g;
        g << "{\"why\":\"enable\""
          << ",\"patchL\":" << gait_patch_r_[0]
          << ",\"patchR\":" << gait_patch_r_[1]
          << ",\"homeL\":" << gait_foot_rest_z_[0]
          << ",\"homeR\":" << gait_foot_rest_z_[1]
          << ",\"chLiftL\":" << gait_lift_ch_[0]
          << ",\"chLiftR\":" << gait_lift_ch_[1]
          << ",\"dminyHL\":" << gait_dminy_hip_[0]
          << ",\"dminyHR\":" << gait_dminy_hip_[1]
          << ",\"dminyKL\":" << gait_dminy_knee_[0]
          << ",\"dminyKR\":" << gait_dminy_knee_[1]
          << ",\"dczHL\":" << gait_dcz_hip_[0]
          << ",\"dczHR\":" << gait_dcz_hip_[1]
          << ",\"dczKL\":" << gait_dcz_knee_[0]
          << ",\"dczKR\":" << gait_dcz_knee_[1]
          << ",\"rateKL\":" << gait_rate_knee_[0]
          << ",\"rateKR\":" << gait_rate_knee_[1]
          << ",\"rateHL\":" << gait_rate_hip_[0]
          << ",\"rateHR\":" << gait_rate_hip_[1]
          << ",\"strutPinL\":" << gait_strut_pin_[0]
          << ",\"strutPinR\":" << gait_strut_pin_[1]
          << ",\"clearPinL\":" << gait_clear_pin_[0]
          << ",\"clearPinR\":" << gait_clear_pin_[1]
          << ",\"feetCell\":" << feet << "}";
        gait_log_locked_(0, "OFF", "STANCE", g.str());
    }
    return true;
}

void MembraneTick::gait_step_locked_(std::vector<float>& verts9, float dt) {
    // Disarmed-hold: if the balance rung or gravity left, the machine
    // falls to the off-contract -- pins 13-16 to authored 0, all legs to
    // STANCE -- deterministic and idempotent, logged once from a real
    // hold (not every tick).
    if (!gravity_on_ || !stance_on_) {
        bool holding = false;
        for (int s = 0; s < 2; ++s)
            if (gait_phase_[s] != GaitPhase::STANCE || gait_knee_rad_[s] != 0.f
                || gait_hip_rad_[s] != 0.f) { holding = true; break; }
        if (holding) {
            for (int s = 0; s < 2; ++s) {
                if (gait_phase_[s] != GaitPhase::STANCE)
                    gait_log_locked_(s, gait_phase_name(gait_phase_[s]),
                                     "STANCE",
                                     "{\"why\":\"balance or gravity left the rung\"}");
                gait_phase_[s] = GaitPhase::STANCE;
                gait_knee_rad_[s] = gait_hip_rad_[s] = 0.f;
                gait_block_[s] = "superseded";
            }
            if (joint_deg_.size() > (size_t)KNEE_PIN_R) {
                joint_deg_[HIP_PIN_L] = joint_deg_[HIP_PIN_R] = 0.f;
                joint_deg_[KNEE_PIN_L] = joint_deg_[KNEE_PIN_R] = 0.f;
            }
            // the composed ankles return to stance's own component (the
            // same law as gait_off_locked_; in the gravity-off/stance-on
            // corner the balance servo keeps its lean term)
            for (int s = 0; s < 2; ++s) {
                if (gait_strut_pin_[s] >= 0
                    && (size_t)gait_strut_pin_[s] < joint_deg_.size())
                    joint_deg_[(size_t)gait_strut_pin_[s]]
                        = stance_on_ ? stance_th_ : 0.f;
            }
        }
        return;
    }
    if (joint_deg_.size() <= (size_t)KNEE_PIN_R) return;   // pins vanished
    const size_t nverts = verts9.size() / 9;
    if (nverts == 0 || gait_foot_verts_[0].empty() || gait_foot_verts_[1].empty())
        return;
    const float dts = std::min(std::max(dt, 0.f), 0.05f);  // the stall guard

    // -- SENSE: everything below is measured from the live posed surface
    // (pre-root-offset; world y adds root_y_). Per side: the foot set's
    // lowest world y (contact depth) and its centroid (support geometry).
    float wminy[2], fcx[2], fcz[2];
    for (int s = 0; s < 2; ++s) {
        wminy[s] = gait_set_miny(verts9, gait_foot_verts_[s]) + root_y_;
        float cy;
        gait_set_centroid(verts9, gait_foot_verts_[s], &fcx[s], &cy, &fcz[s]);
        gait_depth_[s] = std::max(0.f, -wminy[s]);
    }
    gait_clear_[0] = wminy[0] - wminy[1];
    gait_clear_[1] = wminy[1] - wminy[0];
    float bx = 0.f, bz = 0.f;
    for (size_t v = 0; v < nverts; ++v) {
        bx += verts9[v * 9 + 0];
        bz += verts9[v * 9 + 2];
    }
    bx /= (float)nverts; bz /= (float)nverts;
    const float sn = (float)(gait_foot_verts_[0].size()
                           + gait_foot_verts_[1].size());
    const float scx = (fcx[0] * (float)gait_foot_verts_[0].size()
                     + fcx[1] * (float)gait_foot_verts_[1].size()) / sn;
    const float scz = (fcz[0] * (float)gait_foot_verts_[0].size()
                     + fcz[1] * (float)gait_foot_verts_[1].size()) / sn;
    gait_lean_x_ = (bx - scx) - gait_lean_ref_x_;
    gait_lean_z_ = (bz - scz) - gait_lean_ref_z_;
    const float lean = std::sqrt(gait_lean_x_ * gait_lean_x_
                               + gait_lean_z_ * gait_lean_z_);
    // the sealed-pressure witness: the water law answering the poses
    gait_p_max_ = 0.f;
    for (const SealCell& c : seal_cells_)
        gait_p_max_ = std::max(gait_p_max_, std::fabs(c.p));
    const bool settled = std::fabs(root_vy_) <= GAIT_SETTLE_VY;

    // shared gate numbers on EVERY transition log (P5: no gateless moves)
    auto gates0 = [&]() -> std::string {
        std::ostringstream g;
        g << "{\"dL\":" << gait_depth_[0]
          << ",\"dR\":" << gait_depth_[1]
          << ",\"cL\":" << gait_clear_[0]
          << ",\"cR\":" << gait_clear_[1]
          << ",\"lean\":" << lean
          << ",\"vy\":" << root_vy_
          << ",\"pmax\":" << gait_p_max_;
        return g.str();
    };
    // G1 servo law (the F1 structure): dtheta = err/(channel*TAU), rate
    // capped by the MEASURED arc rate, ROM-clamped under pose_index's
    // 90-deg law -- the pose channel can never teleport.
    auto servo_dth = [&](float err, float channel, float rate_cap) -> float {
        float dth = err / (channel * STANCE_TAU_S);
        const float mx = rate_cap * dts;
        return std::min(std::max(dth, -mx), mx);
    };
    auto clamp_rom = [&](float* th) {
        *th = std::min(std::max(*th, -GAIT_MAX_ANG), GAIT_MAX_ANG);
    };
    // LOAD/RECOVER/STANCE housekeeping: walk the pose back to authored
    // bearing (0) at the measured rate cap -- the rest pose IS the
    // bearing pose (home + ground), so the exit gates are the body's.
    auto return_zero = [&](float rate, float* th) {
        if (*th == 0.f) return;
        const float step = std::min(std::fabs(*th), rate * dts);
        *th += (*th > 0.f) ? -step : step;
        if (std::fabs(*th) < 1e-7f) *th = 0.f;
    };

    // -- PASS A: the STANCE gates, evaluated on measured numbers, in
    // order; the FIRST failing gate is the reported blocker.
    for (int s = 0; s < 2; ++s) {
        if (gait_phase_[s] != GaitPhase::STANCE) { gait_block_[s].clear(); continue; }
        const int o = 1 - s;
        std::ostringstream b;
        if (gait_phase_[o] != GaitPhase::STANCE)
            b << "other:" << gait_phase_name(gait_phase_[o]);
        else if (gait_depth_[o] < GAIT_BEARING_FRAC * GAIT_SINK_M)
            b << "other_depth:" << gait_depth_[o]
              << "<" << GAIT_BEARING_FRAC * GAIT_SINK_M;
        else if (lean > gait_patch_r_[o])
            b << "lean:" << lean << ">" << gait_patch_r_[o];
        else {
            // THE WHAT-IF (rung 4, answered from live numbers): if I lift
            // this foot, does the support hold my weight? After the lift
            // the support is the other foot alone; the body centroid must
            // already lie inside that foot's measured patch.
            const float wdx = bx - fcx[o], wdz = bz - fcz[o];
            const float wx = std::sqrt(wdx * wdx + wdz * wdz);
            if (wx > gait_patch_r_[o])
                b << "whatif:" << wx << ">" << gait_patch_r_[o];
        }
        gait_block_[s] = b.str();
    }
    // -- PASS B: the schedule. When BOTH legs qualify, the leg that
    // stepped LONGER AGO swings (deterministic alternation -- a decision
    // the controller makes, not a gate; the gates stay measured).
    int pick = -1;
    for (int s = 0; s < 2; ++s)
        if (gait_phase_[s] == GaitPhase::STANCE && gait_block_[s].empty()) {
            if (pick < 0) { pick = s; continue; }
            const int keep = gait_last_done_[s] < gait_last_done_[pick] ? s : pick;
            const int drop = (keep == s) ? pick : s;
            gait_block_[drop] = "schedule:turn";
            pick = keep;
        }
    if (pick >= 0) {
        gait_phase_[pick] = GaitPhase::LIFT;
        std::ostringstream g;
        g << gates0()
          << ",\"whatif\":true,\"patch\":" << gait_patch_r_[1 - pick] << "}";
        gait_log_locked_(pick, "STANCE", "LIFT", g.str());
    }

    // -- PASS C: actuate + gate
    for (int s = 0; s < 2; ++s) {
        const int o = 1 - s;
        switch (gait_phase_[s]) {
        case GaitPhase::STANCE: {
            return_zero(gait_rate_knee_[s], &gait_knee_rad_[s]);
            return_zero(gait_rate_hip_[s],  &gait_hip_rad_[s]);
            break;
        }
        case GaitPhase::LIFT: {
            // THE FALL RESPONSE: the planted foot left the floor -- the
            // swing leg lands (LOAD's guarded target) while the failed
            // support leg drives straight back down (RECOVER).
            if (wminy[o] >= 0.f) {
                const char* ofrom = gait_phase_name(gait_phase_[o]);
                gait_phase_[o] = GaitPhase::RECOVER;
                gait_phase_[s] = GaitPhase::LOAD;
                std::ostringstream g;
                g << gates0() << ",\"why\":\"support_lost\"}";
                gait_log_locked_(o, ofrom, "RECOVER", g.str());
                gait_log_locked_(s, "LIFT", "LOAD", g.str());
                break;
            }
            // the derived null-z combo, driven by the MEASURED rise
            // error: the target is one support band above the floor
            // (STANCE_BAND_M -- the named bar; from the rest sink the
            // total rise is sink + band = 0.06 m). The per-pin rate caps
            // bound the combo step.
            const float err = STANCE_BAND_M - wminy[s];
            float dparam = err / (gait_lift_ch_[s] * STANCE_TAU_S);
            const float bh = std::fabs(gait_lift_ah_[s]) > 1e-6f
                ? gait_rate_hip_[s] * dts / std::fabs(gait_lift_ah_[s])
                : 1e30f;
            const float bk = std::fabs(gait_lift_ak_[s]) > 1e-6f
                ? gait_rate_knee_[s] * dts / std::fabs(gait_lift_ak_[s])
                : 1e30f;
            const float mx = std::min(bh, bk);
            dparam = std::min(std::max(dparam, -mx), mx);
            gait_hip_rad_[s]  += dparam * gait_lift_ah_[s];
            gait_knee_rad_[s] += dparam * gait_lift_ak_[s];
            clamp_rom(&gait_hip_rad_[s]);
            clamp_rom(&gait_knee_rad_[s]);
            if (wminy[s] >= STANCE_BAND_M) {
                gait_phase_[s] = GaitPhase::REACH;
                std::ostringstream g;
                g << gates0() << ",\"miny\":" << wminy[s] << "}";
                gait_log_locked_(s, "LIFT", "REACH", g.str());
            }
            break;
        }
        case GaitPhase::REACH: {
            // single support: the reference is the STANCE foot's live
            // centroid -- including the swing foot in the reference set
            // would chase the actuated limb (the measured F1 self-cancel
            // failure mode, avoided by construction here).
            if (wminy[o] >= 0.f) {   // support lost mid-reach: the abort
                const char* ofrom = gait_phase_name(gait_phase_[o]);
                gait_phase_[o] = GaitPhase::RECOVER;
                gait_phase_[s] = GaitPhase::LOAD;
                std::ostringstream g;
                g << gates0() << ",\"why\":\"support_lost\"}";
                gait_log_locked_(o, ofrom, "RECOVER", g.str());
                gait_log_locked_(s, "REACH", "LOAD", g.str());
                break;
            }
            // hold the clearance on the knee while the hip reaches
            const float kerr = STANCE_BAND_M - wminy[s];
            gait_knee_rad_[s] += servo_dth(kerr, gait_dminy_knee_[s],
                                           gait_rate_knee_[s]);
            clamp_rom(&gait_knee_rad_[s]);
            // the hip reaches: z target = stance centroid + own patch
            // (the new footfall must land outside the old support patch)
            const float zerr = (fcz[o] + gait_patch_r_[s]) - fcz[s];
            gait_hip_rad_[s] += servo_dth(zerr, gait_dcz_hip_[s],
                                          gait_rate_hip_[s]);
            clamp_rom(&gait_hip_rad_[s]);
            if (fcz[s] - fcz[o] >= gait_patch_r_[s]) {
                gait_phase_[s] = GaitPhase::LOAD;
                std::ostringstream g;
                g << gates0() << ",\"z\":" << (fcz[s] - fcz[o])
                  << ",\"bar\":" << gait_patch_r_[s] << "}";
                gait_log_locked_(s, "REACH", "LOAD", g.str());
            } else if (wminy[s] < 0.f) {
                // the swing foot touched down mid-reach: the reach FAILED
                // (a measured fact) -- recover and re-arm, log the abort.
                gait_phase_[s] = GaitPhase::RECOVER;
                std::ostringstream g;
                g << gates0() << ",\"why\":\"touchdown\"}";
                gait_log_locked_(s, "REACH", "RECOVER", g.str());
            }
            break;
        }
        case GaitPhase::LOAD: {
            // return both pins toward authored bearing at the measured
            // caps; the foot lands wherever bearing puts it. The EXIT is
            // the body's number: penetration past the bearing bar AND
            // vertical settle (weight accepted), never an elapsed time.
            return_zero(gait_rate_knee_[s], &gait_knee_rad_[s]);
            return_zero(gait_rate_hip_[s],  &gait_hip_rad_[s]);
            if (gait_depth_[s] >= GAIT_BEARING_FRAC * GAIT_SINK_M && settled) {
                gait_phase_[s] = GaitPhase::STANCE;
                ++gait_stride_count_;
                gait_last_done_[s] = ticks_;
                std::ostringstream g;
                g << gates0()
                  << ",\"prelax\":"
                  << (gait_p_max_ <= GAIT_P_RELAX_PA ? "true" : "false")
                  << ",\"stride\":" << gait_stride_count_ << "}";
                gait_log_locked_(s, "LOAD", "STANCE", g.str());
            }
            break;
        }
        case GaitPhase::RECOVER: {
            return_zero(gait_rate_knee_[s], &gait_knee_rad_[s]);
            return_zero(gait_rate_hip_[s],  &gait_hip_rad_[s]);
            if (gait_depth_[s] >= GAIT_BEARING_FRAC * GAIT_SINK_M && settled) {
                gait_phase_[s] = GaitPhase::STANCE;
                std::ostringstream g;
                g << gates0()
                  << ",\"prelax\":"
                  << (gait_p_max_ <= GAIT_P_RELAX_PA ? "true" : "false")
                  << "}";
                gait_log_locked_(s, "RECOVER", "STANCE", g.str());
            }
            break;
        }
        }
    }

    // -- ACT: the commanded angles land on the RESOLVED drive pins (the
    // V3a audit: measured from the binding at enable, ankle/knee on the
    // shipped creature). The strut pin's angle is COMPOSED over stance's
    // own lean term (the prereg: "the G1 block runs AFTER the stance
    // block and composes over it" -- the ankle pin carries
    // stance_th_ + the machine's strut component, so the balance servo
    // keeps its channel while the machine strides). The legacy hip pins
    // 13/14 are left at authored bearing: the shipped binding gives them
    // ZERO foot weight (the measured no_channel_hip_L0 fact), so writing
    // them would be motion with no channel -- animation, not control.
    if ((size_t)gait_strut_pin_[0] < joint_deg_.size())
        joint_deg_[(size_t)gait_strut_pin_[0]] =
            stance_th_ + gait_hip_rad_[0];
    if ((size_t)gait_strut_pin_[1] < joint_deg_.size())
        joint_deg_[(size_t)gait_strut_pin_[1]] =
            stance_th_ + gait_hip_rad_[1];
    if ((size_t)gait_clear_pin_[0] < joint_deg_.size())
        joint_deg_[(size_t)gait_clear_pin_[0]] = gait_knee_rad_[0];
    if ((size_t)gait_clear_pin_[1] < joint_deg_.size())
        joint_deg_[(size_t)gait_clear_pin_[1]] = gait_knee_rad_[1];
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
      << ",\"seal_refusal\":\"" << seal_refusal_ << "\""
      << ",\"dimple_m\":" << dimple_m_
      << ",\"gravity_on\":" << (gravity_on_ ? "true" : "false")
      << ",\"root_y\":" << root_y_
      << ",\"root_vy\":" << root_vy_
      << ",\"g_contact_n\":" << g_contact_n_
      << ",\"stance_on\":" << (stance_on_ ? "true" : "false")
      << ",\"stance_ankle_deg\":" << stance_th_ * 57.29577951308232
      << ",\"stance_kp\":" << stance_kp_
      << ",\"stance_lean_x\":" << stance_lean_x_
      << ",\"stance_lean_z\":" << stance_lean_z_
      // G1: the gait checkpoint fields -- per-leg phase, measured
      // depths/clearances, commanded poses, the gate currently blocking
      // each leg, and the bounded transition log (every entry carries
      // its measured gate values -- P5: no gateless moves).
      << ",\"gait_on\":" << (gait_on_ ? "true" : "false")
      << ",\"gait_l\":\"" << gait_phase_name(gait_phase_[0]) << "\""
      << ",\"gait_r\":\"" << gait_phase_name(gait_phase_[1]) << "\""
      << ",\"gait_stride\":" << gait_stride_count_
      << ",\"gait_depth_l\":" << gait_depth_[0]
      << ",\"gait_depth_r\":" << gait_depth_[1]
      << ",\"gait_clear_l\":" << gait_clear_[0]
      << ",\"gait_clear_r\":" << gait_clear_[1]
      << ",\"gait_lean_x\":" << gait_lean_x_
      << ",\"gait_lean_z\":" << gait_lean_z_
      << ",\"gait_p_max\":" << gait_p_max_
      << ",\"gait_hip_l_deg\":" << gait_hip_rad_[0] * 57.29577951308232
      << ",\"gait_hip_r_deg\":" << gait_hip_rad_[1] * 57.29577951308232
      << ",\"gait_knee_l_deg\":" << gait_knee_rad_[0] * 57.29577951308232
      << ",\"gait_knee_r_deg\":" << gait_knee_rad_[1] * 57.29577951308232
      << ",\"gait_feet_cell\":" << gait_feet_cell_
      << ",\"gait_strut_pin_l\":" << gait_strut_pin_[0]
      << ",\"gait_strut_pin_r\":" << gait_strut_pin_[1]
      << ",\"gait_clear_pin_l\":" << gait_clear_pin_[0]
      << ",\"gait_clear_pin_r\":" << gait_clear_pin_[1]
      << ",\"gait_enable_block\":\"" << gait_enable_block_ << "\""
      << ",\"gait_block_l\":\"" << gait_block_[0] << "\""
      << ",\"gait_block_r\":\"" << gait_block_[1] << "\""
      << ",\"gait_log\":[";
    for (size_t i = 0; i < gait_log_.size(); ++i) {
        if (i) o << ",";
        o << gait_log_[i];
    }
    o << "]"
      << ",\"cells\":[";
    for (size_t i = 0; i < seal_cells_.size(); ++i) {
        const SealCell& c = seal_cells_[i];
        if (i) o << ",";
        o << "{\"v0\":" << c.v0 << ",\"V\":" << c.vol << ",\"P\":" << c.p
          << ",\"pieces\":" << (c.pieces.size() / 3)
          << ",\"caps\":" << c.caps
          << ",\"ylo\":" << c.ylo << ",\"yhi\":" << c.yhi
          << ",\"degenerate\":" << (c.degenerate ? "true" : "false") << "}";
    }
    o << "]"
      << ",\"has_scene\":" << (has_scene_ ? "true" : "false") << "}";
    return o.str();
}





