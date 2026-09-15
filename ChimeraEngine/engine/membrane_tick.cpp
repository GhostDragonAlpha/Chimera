
#include "membrane_tick.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <functional>
#include <map>
#include <set>
#include <sstream>
#include <thread>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <utility>

namespace {

// Strong exception/refusal guarantee for compound anatomy operations. Capture
// before the first mutation; restore with non-allocating swaps while the caller
// still holds seal_mtx_. Commit only after every dependent registry validates.
template<class... T> class StateRollback {
    std::tuple<T&...> live_;
    std::tuple<T...> saved_;
    bool committed_ = false;
    template<size_t... I> void restore(std::index_sequence<I...>) noexcept {
        (std::swap(std::get<I>(live_), std::get<I>(saved_)), ...);
    }
public:
    explicit StateRollback(T&... state) : live_(state...), saved_(state...) {
        static_assert((std::is_nothrow_swappable_v<T> && ...));
    }
    StateRollback(const StateRollback&) = delete;
    StateRollback& operator=(const StateRollback&) = delete;
    ~StateRollback() { if (!committed_) restore(std::index_sequence_for<T...>{}); }
    void commit() noexcept { committed_ = true; }
};

// All count checks use remaining bytes (no offset+length overflow). Native
// snapshot formats are little-endian, as are the supported engine targets.
class StateReader {
    const std::string& body_;
    size_t offset_ = 0;
public:
    explicit StateReader(const std::string& body) : body_(body) {}
    size_t remaining() const { return body_.size() - offset_; }
    template<class T> bool take(T& value) {
        static_assert(std::is_trivially_copyable_v<T>);
        if (sizeof(T) > remaining()) return false;
        std::memcpy(&value, body_.data() + offset_, sizeof(T));
        offset_ += sizeof(T);
        return true;
    }
    bool name(std::string& value) {
        if (remaining() < 32) return false;
        const char* start = body_.data() + offset_;
        const size_t n = strnlen(start, 32);
        if (n == 0 || n == 32) return false;
        value.assign(start, n);
        offset_ += 32;
        return true;
    }
};

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

// ─── C1r REFLEX constants (PREREG.md + DERIVATIONS.md; every interim
// ─── VALUE below is AWAITING ASTRA -- the mechanisms and their measured
// ─── anchors are not) ────────────────────────────────────────────────
constexpr float REFLEX_BREATH_F_COEF = 53.5f;  // Stahl 1967 respiratory
constexpr float REFLEX_BREATH_F_EXP  = -0.26f; // allometry: f=53.5 M^-.26
                                               // breaths/min -> 4.485/min,
                                               // 13.38 s at 13,824.5 kg
constexpr float REFLEX_BREATH_VT_ML  = 6.2f;   // tidal volume = 6.2 mL/kg
constexpr float REFLEX_BREATH_VT_EXP = 1.01f;  // x M^1.01 -> 0.0940 m^3,
                                               // 0.752% of torso v0
constexpr float REFLEX_FLINCH_PA     = 1.0e5f; // 2x GAIT_P_RELAX_PA (gentle
                                               // handling tolerated), 0.67%
                                               // of yield_pa_, 150x below
                                               // damage; ladder-measured
                                               // between the 10 kN (51 kPa)
                                               // and 20 kN (432 kPa) rungs
constexpr float REFLEX_STARTLE_DPDPT = 1.0e6f; // Pa/s ~ 3.3 kPa/tick at the
                                               // measured 3.34 ms tick;
                                               // measured floors are EXACTLY
                                               // 0 Pa/s; a 500 N touch steps
                                               // 3.6 kPa in one tick
constexpr float REFLEX_QUIET_S       = 1.0f;   // post-gait refractory = 2x
                                               // tau_relax_: the walk's
                                               // measured pressure collapse
                                               // (583 MPa/s peaks) must not
                                               // ring a crossing
constexpr float REFLEX_S_PREREG      = 0.283f; // m/rad, stance prereg |S|
                                               // (fallback when stance has
                                               // never run: read live as
                                               // 1/stance_kp_ when it has)
constexpr float REFLEX_ENV_CUT       = 1e-3f;  // envelope cutoff (the 0.1 mm
                                               // press-cutoff analog, rad)
constexpr float DEG2RAD_F            = 3.14159265358979f / 180.f;

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
    // C1r: reflex state dies with the body -- the breath vert list, the
    // resolved pins and the detector membrane describe the OLD geometry
    // (the C1 stale-index crash class; a new body is born UN-ARMED: the
    // route is the operator's).
    reflex_ = ReflexState{};
    // AN2: the limb registry and the patches describe the OLD body's
    // cells -- the same stale-index crash class. A new body is born
    // un-partitioned and unpatched; the blobs revalidate or refuse.
    limb_segs_.clear();
    limb_done_ = false;
    limb_side_.clear();
    limb_report_.clear();
    patches_.clear();
    patches_armed_ = false;
    patch_clock_s_ = 0.f;
    patch_event_log_.clear();
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

    // ═══ AN2: SENSOR PATCHES (filter → saturate → finite delay →
    // ═══ deliver). Runs AFTER the press/volume passes (the patch feels
    // THIS tick's indentation field) and BEFORE the reflex detect (the
    // detector consumes THIS tick's deliveries). Internally gated by
    // patches_armed_; disarmed the executable path is unchanged.
    if (patches_armed_) patch_step_locked_(dt);

    // ═══ C1r: THE CREATURE ANSWERS — DETECT (flinch + startle) ══════════
    // Runs on THIS tick's fresh per-cell sealed pressures (computed just
    // above), BEFORE the stance/gait blocks so its pin writes land in the
    // same actuation-latency class as theirs (manifest next tick's
    // travel). Internally gated by reflex_.armed; the interaction gates
    // (gait suppression, quiet window, nerve cut) live inside.
    if (reflex_.armed) reflex_detect_locked_(dt);

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

    // ═══ C1r: STARTLE COMPOSE (the whole-body reflex's only channel) ════
    // After the stance block (composes OVER stance_th_, the same law the
    // gait machine's strut composer uses) and before the gait block (a
    // gait-armed tick overwrites the strut pins; the startle is gated off
    // under gait anyway).
    if (reflex_.armed) reflex_compose_locked_();

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
        // one completed ground-force evaluation under the flag: the
        // arm-on-readiness witness set_gravity(true) waits for
        ground_evals_.fetch_add(1, std::memory_order_release);
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

    // ═══ C1r: AUTONOMIC BREATHING (THE ABSOLUTE LAST surface pass) ══════
    // AFTER the seal-volume/stance/gait passes AND AFTER the FALL law's
    // root read (the window-9 hardening: the movement law's min-y read is
    // breath-blind too, so the root home cannot depend on the breath
    // phase -- the window-8 V10 suspicion, closed by construction; the
    // measured V10 failure was the pre-B10 leftover rung state, fresh-boot
    // armed 15/15, gait_verify_armed_fresh_scratch8167.json). Every
    // engine-internal measurement now reads the pre-breath surface; only
    // the /verts export (what the page renders) sees the breath. The root
    // offset composes as a uniform translation and commutes with the
    // displacement.
    if (reflex_.armed) reflex_breath_locked_(verts9, dt);
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
    return split_locked_(cell_idx);
}

bool MembraneTick::split_locked_(int cell_idx) {
    // caller holds seal_mtx_ (split() or limb_partition)
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
    // THE CUT COORDINATE (AN2): signed plane distance per point — the
    // general form of which the Y plane is the special case pd = py - y.
    // Rides parallel to pts/py; new cut points push pd == 0 exactly (the
    // same statement the H8 lesson pinned as py.push_back(y)).
    std::vector<float> pd(pts.size(), 0.f);
    for (size_t s = 0; s < pts.size(); ++s) pd[s] = py[s] - y;

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

    // CUT + WELD + VOLUME + GUARDS + PUBLISH — the shared core (AN2):
    // the horizontal plane here and the oblique limb walls run ONE
    // winding law, ONE weld law, ONE guard set (seal_cut_core_ below).
    if (!seal_cut_core_(cell_idx, pts, pd, py, rest9, ncut0)) return false;
    seal_y_ = y;   // last-cut report (Y cuts only; an oblique wall
                   // leaves the last Y in place)
    return true;
}

// ═══ THE SHARED CUT CORE (AN2, prereg ONE_LIMB/PREREG.md M1/M2) ═══
// Extracted VERBATIM from seal() so the horizontal seal and the oblique
// limb partition cannot drift: straddle-split → weld-chain → the winding
// law → divergence volumes → positivity + degenerate guards → publish.
// pd is the cut coordinate (signed plane distance, negative = below);
// py rides parallel (rest y per point) for the stored ylo/yhi bounds the
// already-satisfied checks of later Y cuts compare against.
bool MembraneTick::seal_cut_core_(int cell_idx,
                                  std::vector<CutBlend>& pts,
                                  std::vector<float>& pd,
                                  std::vector<float>& py,
                                  const std::vector<float>& rest9,
                                  size_t ncut0) {
    const uint32_t nv = (uint32_t)(base_pos_.size() / 9);
    // the boundary being cut: the named cell's pieces (or the whole creature)
    std::vector<uint32_t> src;
    if (seal_cells_.empty()) src.assign(tri_verts_.begin(), tri_verts_.end());
    else src = seal_cells_[cell_idx].pieces;

    // CUT: split every straddling piece; new cut points are merged convex
    // blends of the endpoints. Segment direction follows the BELOW-piece
    // boundary walk (the winding law below consumes that direction).
    std::map<std::pair<uint32_t, uint32_t>, uint32_t> cut_id;
    std::vector<uint32_t> lower, upper;         // 3 slots per piece
    std::vector<std::pair<uint32_t, uint32_t>> segs;
    int split = 0;
    // rc: 0 = ok, 1 = not a crossing edge, 2 = blend overflow
    auto edge_cut = [&](uint32_t sA, uint32_t sB, uint32_t* out) -> int {
        if (pd[sA] >= pd[sB]) std::swap(sA, sB);
        if (!(pd[sA] < 0.f && pd[sB] >= 0.f)) return 1;
        auto key = std::make_pair(std::min(sA, sB), std::max(sA, sB));
        auto it = cut_id.find(key);
        if (it != cut_id.end()) { *out = it->second; return 0; }
        float t = pd[sA] / (pd[sA] - pd[sB]);
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
        py.push_back(py[sA] + t * (py[sB] - py[sA]));
        pd.push_back(0.f);
        *out = id;
        return 0;
    };
    for (size_t i = 0; i + 2 < src.size(); i += 3) {
        uint32_t vs[3] = {src[i], src[i + 1], src[i + 2]};
        bool bl[3] = {pd[vs[0]] < 0.f, pd[vs[1]] < 0.f, pd[vs[2]] < 0.f};
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
    // stays intact (the replay/refusal is idempotent). THE GUARD STAYS
    // ARMED for the limb walls: a legitimate-segment refusal is a
    // finding with re-derived arithmetic, never a loosened threshold.
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
        seal_refusal_.clear();   // this cut is clean: the name clears
        sealed_ = true;   // published under the lock; step() checks first
    }
    return true;
}

// ═══ AN2: THE ONE-LIMB PARTITION + SENSOR PATCHES (prereg M1-M4) ═══
namespace {

constexpr float LIMB_BAND_TOL_M     = 2e-3f;  // band-boundary match vs pin y
                                              // (authored cuts sit 2-3e-4 from
                                              // the pins; 1000x under the 0.1 mm
                                              // scale is 1e-7 drift)
constexpr float LIMB_SEED_ADJ_FRAC  = 0.01f;  // pins p,q ADJACENT iff their
                                              // crossing-edge count >= 1% of
                                              // min(pop(p),pop(q)) -- the
                                              // connectivity floor (P1)
constexpr float LIMB_PATCH_FRAC     = 0.05f;  // a patch covers ~5% of its
                                              // segment's skin (the finite-
                                              // receptor coverage assertion)
constexpr float LIMB_CONDUCTION_V   = 70.f;   // m/s, A-beta afferent (Kandel,
                                              // Principles of Neural Science --
                                              // reference assertion, PREREG M3)
constexpr float LIMB_TAU_S          = 0.010f; // receptor filter: 3 ticks at
                                              // the 300 Hz tick (PREREG M3)
constexpr float LIMB_THRESH_M       = 1e-3f;  // delivered-signal trigger: 10x
                                              // the repo's 0.1 mm cutoff scale
constexpr int   LIMB_PIN_SPINE_LOW  = 4;      // the central terminus (the
                                              // lumbosacral analogue)
constexpr float LIMB_MASS_RHO       = 1000.f; // kg/m^3, water (the inventory)
constexpr float LIMB_MASS_TARGET_KG = 13824.5f;
constexpr size_t PATCH_LOG_N        = 64;     // bounded event log
constexpr uint32_t LIMB_STATE_MAGIC = 0x31424D4Cu;  // 'LMB1'
constexpr uint32_t PATCH_STATE_MAGIC = 0x31544150u; // 'PAT1'
constexpr uint32_t PATCH_CHECKPOINT_MAGIC = 0x32544150u; // 'PAT2', sensor continuation

// THE WINDOW-10 JSON LAW (the lead's standing rule, encoded): no float
// reaches JSON unguarded. NaN/Inf serialize as null -- valid JSON with
// the absence stated honestly -- never as nan/-inf, which is INVALID
// JSON and poisons every consumer of the channel (the window-10 defect
// class: one unguarded float took the live world's telemetry down).
// Every float emitter THIS lane added goes through jf().
std::string jf(float v) {
    if (std::isfinite(v)) {
        std::ostringstream o;
        o << v;
        return o.str();
    }
    return "null";
}

}  // namespace

// rest geometry on the tick's own blend (the seal() law: v0 measured on
// the SAME floats the per-frame volume uses -- rest dV exactly 0).
void MembraneTick::rest_geometry_locked_(std::vector<float>& rest9,
                                         std::vector<float>& cutrest) const {
    const uint32_t nv = (uint32_t)(base_pos_.size() / 9);
    rest9 = base_pos_;
    const bool classified = cell_joint_.size() == cells_.size()
                         && !joint_pins_.empty()
                         && joint_pins_.size() == joint_deg_.size()
                         && vert_bind_idx_.size() == (size_t)nv * 3
                         && vert_bind_w_.size() == (size_t)nv * 3;
    if (classified) apply_travel(rest9, nullptr);
    cutrest.assign(cut_src_.size() * 3, 0.f);
    for (size_t k = 0; k < cut_src_.size(); ++k) {
        const CutBlend& b = cut_src_[k];
        for (int i = 0; i < b.n; ++i)
            for (int d = 0; d < 3; ++d)
                cutrest[k * 3 + d] += b.w[i] * rest9[b.v[i] * 9 + d];
    }
}

float MembraneTick::div_pieces_(const std::vector<uint32_t>& pieces,
                                const std::vector<float>& rest9,
                                const std::vector<float>& cutrest) const {
    const uint32_t nv = (uint32_t)(base_pos_.size() / 9);
    auto slot3 = [&](uint32_t s, float* x, float* y, float* z) {
        if (s < nv) {
            *x = rest9[s * 9 + 0]; *y = rest9[s * 9 + 1]; *z = rest9[s * 9 + 2];
        } else {
            size_t i = (size_t)(s - nv) * 3;
            *x = cutrest[i]; *y = cutrest[i + 1]; *z = cutrest[i + 2];
        }
    };
    float v = 0.f;
    for (size_t i = 0; i + 2 < pieces.size(); i += 3) {
        float a[3], b[3], c[3];
        slot3(pieces[i], &a[0], &a[1], &a[2]);
        slot3(pieces[i + 1], &b[0], &b[1], &b[2]);
        slot3(pieces[i + 2], &c[0], &c[1], &c[2]);
        v += (a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.f;
    }
    return v;
}

// closed-manifold test + Euler characteristic (V - E + F). Closure: every
// undirected edge of the piece set used EXACTLY twice.
bool MembraneTick::cell_topology_(const std::vector<uint32_t>& pieces,
                                  int* chi_out) const {
    std::map<std::pair<uint32_t, uint32_t>, int> edge;
    std::set<uint32_t> verts;
    for (size_t i = 0; i + 2 < pieces.size(); i += 3) {
        uint32_t t[3] = {pieces[i], pieces[i + 1], pieces[i + 2]};
        for (int k = 0; k < 3; ++k) verts.insert(t[k]);
        for (int k = 0; k < 3; ++k) {
            uint32_t a = t[k], b = t[(k + 1) % 3];
            edge[{std::min(a, b), std::max(a, b)}] += 1;
        }
    }
    for (const auto& [e, n] : edge)
        if (n != 2) return false;              // open or non-manifold
    if (chi_out)
        *chi_out = (int)verts.size() - (int)edge.size()
                 + (int)(pieces.size() / 3);   // chi = V - E + F
    return true;
}

bool MembraneTick::limb_partition(const std::string& side,
                                  std::string& report, bool* already) {
    if (already) *already = false;
    report.clear();
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) {
        report = "refused: no scene"; return false;
    }
    if (side != "L" && side != "R") {
        report = "refused: side must be \"L\" or \"R\""; return false;
    }
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (limb_done_ && limb_side_ == side) {
        report = limb_report_;
        if (already) *already = true;
        return true;                    // the executed partition is a state,
    }                                   // not an action to repeat
    if (!sealed_ || seal_cells_.empty()) {
        report = "refused: the body is not sealed"; return false;
    }
    const uint32_t nv = (uint32_t)(base_pos_.size() / 9);
    const bool classified = cell_joint_.size() == cells_.size()
                         && !joint_pins_.empty()
                         && joint_pins_.size() == joint_deg_.size()
                         && vert_bind_idx_.size() == (size_t)nv * 3
                         && vert_bind_w_.size() == (size_t)nv * 3;
    if (!classified) {
        report = "refused: the body is not classified"; return false;
    }
    if (joint_pins_.size() < 19) {
        report = "refused: need the leg pins (0-18)"; return false;
    }
    if (reflex_.armed || gait_on_ || stance_on_ || gravity_on_
        || patches_armed_ || touch_active_ || !patches_.empty()) {
        // !patches_.empty() (not the armed flag): the patch REGISTRY
        // indexes cells by index -- any later repartition would stale
        // it. One limb surgery per body in this delivery; the event log
        // is a record, not live state, and does not block.
        report = "refused: anatomy surgery runs at authored rest "
                 "(reflex/gait/stance/gravity/patches/touch all off, and "
                 "no prior limb registry may exist -- one-sided surgery "
                 "only in this delivery)";
        return false;
    }
    StateRollback transaction(sealed_, seal_y_, seal_nv_, seal_split_,
        seal_cuts_, seal_loops_, seal_caps_, seal_refusal_, vol_whole0_,
        vol_whole_, conserve_pct_, cut_src_, seal_cells_, cut_pos_,
        limb_segs_, limb_done_, limb_side_, limb_report_, patches_,
        patches_armed_, patch_clock_s_, patch_event_log_);
    const int PIN_HIP   = (side == "L") ? 13 : 14;
    const int PIN_KNEE  = (side == "L") ? 15 : 16;
    const int PIN_ANKLE = (side == "L") ? 17 : 18;
    const float hip_y = joint_pins_[(size_t)PIN_HIP][1];
    const float knee_y = joint_pins_[(size_t)PIN_KNEE][1];
    const float ankle_y = joint_pins_[(size_t)PIN_ANKLE][1];

    std::vector<float> rest9, cutrest;
    rest_geometry_locked_(rest9, cutrest);

    // THE GENUS LEDGER (prereg P6) — PER COMPONENT (the window-11
    // lesson, measured on the scratch): 2−χ is a genus measure only for
    // a CONNECTED closed surface. A band's cell is a multi-sheet book
    // (χ = the SUM over its sheets), so the old cell-wise Σ(2−χ) breaks
    // under ANY merge — merging k balls into one cell multiplies χ and
    // the ledger flagged honest partitions (window-11: genus_after −8
    // on a correct surgery). The invariant that actually holds: the
    // sum of (2−χ) over all CONNECTED CLOSED COMPONENTS. Flooded by
    // shared slots (split_locked_'s own law); merging sheets and
    // stripping the interior walls changes no component's topology.
    auto genus_of = [&](const std::vector<uint32_t>& pieces,
                        int* closed_out) -> long {
        const size_t npieces = pieces.size() / 3;
        std::vector<size_t> parent(npieces);
        for (size_t x = 0; x < npieces; ++x) parent[x] = x;
        std::function<size_t(size_t)> find =
            [&](size_t x) -> size_t {
            while (parent[x] != x) {
                parent[x] = parent[parent[x]];
                x = parent[x];
            }
            return x;
        };
        std::unordered_map<uint32_t, size_t> first;
        for (size_t p = 0; p < npieces; ++p)
            for (int k = 0; k < 3; ++k) {
                uint32_t s = pieces[p * 3 + (size_t)k];
                auto it = first.find(s);
                if (it == first.end()) first[s] = p;
                else {
                    size_t ra = find(it->second), rb = find(p);
                    if (ra != rb) parent[ra] = rb;
                }
            }
        std::map<size_t, std::vector<uint32_t>> comps;
        for (size_t p = 0; p < npieces; ++p)
            for (int k = 0; k < 3; ++k)
                comps[find(p)].push_back(pieces[p * 3 + (size_t)k]);
        long g = 0;
        int closed_n = 0;
        for (auto& kv : comps) {
            int chi = 0;
            if (cell_topology_(kv.second, &chi)) {
                g += 2 - chi;
                ++closed_n;
            }
        }
        if (closed_out) *closed_out = closed_n;
        return g;
    };
    long genus_before = 0;
    int closed_before = 0;
    {
        int closed_n = 0;
        for (const SealCell& c : seal_cells_) {
            genus_before += genus_of(c.pieces, &closed_n);
            closed_before += closed_n;
        }
    }

    // ── 1. THE CONNECTIVITY DERIVATION (prereg P1) ──────────────────
    // dominance: each vertex's heaviest binding pin; populations; then
    // the pin graph: pins p,q are adjacent iff enough mesh edges cross
    // their dominant regions. The chain is DERIVED from that graph and
    // must come out hip→knee→ankle, or P1 is falsified and the route
    // refuses by name (a silent nearest-pin fallback is forbidden).
    std::vector<int> dom(nv, 0);
    std::vector<uint32_t> pop(joint_pins_.size(), 0);
    for (uint32_t v = 0; v < nv; ++v) {
        int best = 0; float bw = vert_bind_w_[(size_t)v * 3 + 0];
        for (int k = 1; k < 3; ++k)
            if (vert_bind_w_[(size_t)v * 3 + (size_t)k] > bw) {
                bw = vert_bind_w_[(size_t)v * 3 + (size_t)k];
                best = k;
            }
        dom[v] = vert_bind_idx_[(size_t)v * 3 + (size_t)best];
        if (dom[v] < (int)pop.size()) ++pop[(size_t)dom[v]];
    }
    std::map<std::pair<int, int>, uint32_t> adj;
    for (size_t i = 0; i + 2 < tri_verts_.size(); i += 3)
        for (int k = 0; k < 3; ++k) {
            uint32_t a = tri_verts_[i + (size_t)k],
                     b = tri_verts_[i + (size_t)((k + 1) % 3)];
            if (dom[a] != dom[b]) {
                auto key = std::make_pair(std::min(dom[a], dom[b]),
                                          std::max(dom[a], dom[b]));
                adj[key] += 1;
            }
        }
    auto adj_count = [&](int p, int q) -> uint32_t {
        auto it = adj.find({std::min(p, q), std::max(p, q)});
        return it == adj.end() ? 0u : it->second;
    };
    auto adjacent = [&](int p, int q) -> bool {
        uint32_t c = adj_count(p, q);
        uint32_t m = std::min(pop[(size_t)p], pop[(size_t)q]);
        return m > 0 && c >= (uint32_t)(LIMB_SEED_ADJ_FRAC * (float)m);
    };
    // derive: knee = hip's strongest adjacent pin; ankle = knee's
    // strongest adjacent pin that is not the hip.
    int d_knee = -1, d_ankle = -1;
    {
        uint32_t best = 0;
        for (size_t q = 0; q < pop.size(); ++q) {
            if ((int)q == PIN_HIP || pop[q] == 0) continue;
            if (!adjacent(PIN_HIP, (int)q)) continue;
            uint32_t c = adj_count(PIN_HIP, (int)q);
            if (c > best) { best = c; d_knee = (int)q; }
        }
        if (d_knee >= 0) {
            best = 0;
            for (size_t q = 0; q < pop.size(); ++q) {
                if ((int)q == PIN_HIP || (int)q == d_knee || pop[q] == 0)
                    continue;
                if (!adjacent(d_knee, (int)q)) continue;
                uint32_t c = adj_count(d_knee, (int)q);
                if (c > best) { best = c; d_ankle = (int)q; }
            }
        }
    }
    char chainbuf[160];
    if (d_knee != PIN_KNEE || d_ankle != PIN_ANKLE || !adjacent(PIN_HIP, PIN_KNEE)
        || !adjacent(PIN_KNEE, PIN_ANKLE) || adjacent(PIN_HIP, PIN_ANKLE)) {
        std::snprintf(chainbuf, sizeof(chainbuf),
            "refused: DERIVED chain hip=%d knee=%d ankle=%d does not match the "
            "pinned chain hip=%d knee=%d ankle=%d -- connectivity falsifies "
            "the segment assumption (prereg P1)",
            PIN_HIP, d_knee, d_ankle, PIN_HIP, PIN_KNEE, PIN_ANKLE);
        report = chainbuf;
        return false;
    }

    // ── 2. IDENTIFY THE BAND CELLS ──────────────────────────────────
    // THE WINDOW-10 LESSON (measured on the scratch): the sculpt's bands
    // are NOT two-component (L/R) -- the thigh band is FOUR closed
    // components (outer + inner shells per side), the feet SIX. A
    // segment must own ALL of its band's side-components: they tile the
    // band's volume disjointly (the pre-surgery band v0 equals their
    // sum -- measured: 0.693 thigh band = 2x(0.0666 outer + 0.008
    // inner) + the wall/window residue in the old run). Grouping is by
    // CONTAINMENT in the band's y-window (a split component carries its
    // own narrower y-range; the unsplit band carries the full one --
    // both are contained, and the y-disjoint windows keep the bands
    // from mixing). Any member that still holds several closed surfaces
    // is split (a connected member refusing with an EMPTY seal_refusal_
    // is a normal "nothing to split"); the loop regroups after every
    // successful split because the split reindexes the cell vector.
    auto resolve_band = [&](bool has_lo, float lo, float hi)
                            -> std::vector<int> {
        for (int guard = 0; guard < 8; ++guard) {
            std::vector<int> m;
            for (size_t i = 0; i < seal_cells_.size(); ++i) {
                const SealCell& c = seal_cells_[i];
                if (has_lo && c.ylo < lo - LIMB_BAND_TOL_M) continue;
                if (c.yhi > hi + LIMB_BAND_TOL_M) continue;
                m.push_back((int)i);
            }
            bool grew = false;
            for (int idx : m) {
                seal_refusal_.clear();
                if (split_locked_(idx)) { grew = true; break; }
                if (!seal_refusal_.empty()) return {};   // a REAL refusal
                                                         // (degenerate etc.)
                // empty refusal = "one closed surface": a fully
                // componentized member, kept as-is
            }
            if (!grew) return m;
        }
        return {};   // split/regroup did not converge: refuse
    };
    auto cell_cx = [&](int idx) -> float {
        const uint32_t nvv = nv;
        double sx = 0.; size_t sw = 0;
        for (uint32_t s : seal_cells_[(size_t)idx].pieces) {
            if (s < nvv) { sx += rest9[(size_t)s * 9 + 0]; ++sw; }
            else { sx += cutrest[((size_t)s - nvv) * 3 + 0]; ++sw; }
        }
        return sw ? (float)(sx / (double)sw) : 0.f;
    };
    // thigh band: [knee, hip]; calf: [ankle, knee]; feet: below the
    // ankle plane (no lower bound -- the soles dip under 0).
    std::vector<int> thigh_cells = resolve_band(true, knee_y, hip_y);
    std::vector<int> calf_cells = resolve_band(true, ankle_y, knee_y);
    std::vector<int> feet_cells = resolve_band(false, 0.f, ankle_y);
    // side selection per COMPONENT (x >= 0 = L, the house law measured
    // from the pins): the segment takes ALL of the band's side
    // components, not one -- taking one left stray shells behind (the
    // window-10 frankenstein-leg lesson).
    const int sgn = (side == "L") ? 1 : -1;
    auto side_of = [&](const std::vector<int>& cells) {
        std::vector<int> out;
        for (int idx : cells) {
            float cx = cell_cx(idx);
            if (sgn > 0 ? cx >= 0.f : cx < 0.f) out.push_back(idx);
        }
        return out;
    };
    std::vector<int> thigh_L = side_of(thigh_cells);
    std::vector<int> calf_L = side_of(calf_cells);
    std::vector<int> foot_L = side_of(feet_cells);
    if (thigh_L.empty() || calf_L.empty() || foot_L.empty()) {
        std::ostringstream er;
        er << "refused: band identification failed (thigh components="
           << thigh_cells.size() << " left:" << thigh_L.size()
           << ", calf components=" << calf_cells.size()
           << " left:" << calf_L.size()
           << ", foot components=" << feet_cells.size()
           << " left:" << foot_L.size()
           << "); refusal=" << seal_refusal_
           << " -- the expected 4-band tree (cuts at the pin heights) is "
              "not what this body carries. NOTE: if a previous /tick_limb "
              "ran and failed validation, the tree is ALREADY partitioned "
              "(the left components are merged and the walls cut) and this "
              "refusal is that state seen through the band windows -- "
              "re-boot from the snapshot to retry the partition";
        report = er.str();
        return false;
    }

    // ── 3. MERGE THE LEG (the limb as ONE cell) ─────────────────────
    // EVERY side component of the three bands merges (the window-10
    // lesson: the bands are bilayer shells — thigh outer+inner per side,
    // multi-sheet feet; a segment owning one shell left stray sealed
    // cells behind). The interior band walls exist TWICE in the merged
    // piece set (both windings — one per daughter; one pair per sheet
    // boundary the bands cut). Remove BOTH copies of every twice-present
    // zero-original triangle: the wall is internal geometry, its two
    // windings cancel in the divergence sum anyway, and leaving it would
    // let the oblique cuts slice an invisible interior sheet. The hip
    // wall appears ONCE (its mate lives in the torso cell) and STAYS:
    // it is the ONE septum between thigh and torso.
    std::vector<int> side_cells;
    side_cells.insert(side_cells.end(), thigh_L.begin(), thigh_L.end());
    side_cells.insert(side_cells.end(), calf_L.begin(), calf_L.end());
    side_cells.insert(side_cells.end(), foot_L.begin(), foot_L.end());
    int TL = side_cells[0];          // the merged leg publishes here
    std::vector<uint32_t> merged;
    for (int idx : side_cells) {
        merged.insert(merged.end(), seal_cells_[(size_t)idx].pieces.begin(),
                      seal_cells_[(size_t)idx].pieces.end());
    }
    std::map<std::array<uint32_t, 3>, int> wall_count;
    auto canon = [](uint32_t a, uint32_t b, uint32_t c) {
        std::array<uint32_t, 3> t = {a, b, c};
        std::sort(t.begin(), t.end());
        return t;
    };
    for (size_t i = 0; i + 2 < merged.size(); i += 3)
        if (merged[i] >= nv && merged[i + 1] >= nv && merged[i + 2] >= nv)
            wall_count[canon(merged[i], merged[i + 1], merged[i + 2])] += 1;
    std::vector<uint32_t> leg;
    int walls_removed = 0;
    bool wall_anomaly = false;
    for (size_t i = 0; i + 2 < merged.size(); i += 3) {
        bool interior = merged[i] >= nv && merged[i + 1] >= nv
                     && merged[i + 2] >= nv;
        if (!interior) { leg.push_back(merged[i]); leg.push_back(merged[i + 1]);
                         leg.push_back(merged[i + 2]); continue; }
        int n = wall_count[canon(merged[i], merged[i + 1], merged[i + 2])];
        if (n == 2) { ++walls_removed; continue; }       // drop both copies
        if (n != 1) { wall_anomaly = true; break; }      // >2: not a clean
        leg.push_back(merged[i]); leg.push_back(merged[i + 1]);
        leg.push_back(merged[i + 2]);                    // double wall
    }
    if (wall_anomaly || walls_removed % 2 != 0 || leg.empty()) {
        report = "refused: interior wall structure is not a clean "
                 "double-winding set -- merge aborted";
        return false;
    }
    float v0_leg = div_pieces_(leg, rest9, cutrest);
    if (!(v0_leg > 0.f)) {
        report = "refused: merged leg volume signed non-positive";
        return false;
    }
    if ((float)walls_removed / 2.f < 1.f) {
        report = "refused: no interior band walls found to merge across";
        return false;
    }
    // publish the merged cell into side_cells[0], compact every other
    // side slot (they are dead: their pieces live in the merged cell).
    {
        float lo = 1e30f, hi = -1e30f;
        for (uint32_t s : leg) {
            float yy = s < nv ? rest9[s * 9 + 1]
                              : cutrest[((size_t)s - nv) * 3 + 1];
            lo = std::min(lo, yy); hi = std::max(hi, yy);
        }
        seal_cells_[(size_t)TL].pieces = leg;
        seal_cells_[(size_t)TL].v0 = v0_leg;
        seal_cells_[(size_t)TL].vol = v0_leg;
        seal_cells_[(size_t)TL].p = 0.f;
        seal_cells_[(size_t)TL].ylo = lo;
        seal_cells_[(size_t)TL].yhi = hi;
    }
    {
        std::vector<int> dead = side_cells;
        dead.erase(dead.begin());
        std::sort(dead.begin(), dead.end());
        for (size_t k = dead.size(); k-- > 0;)
            seal_cells_.erase(seal_cells_.begin() + dead[k]);
        int shifted = 0;
        for (int d : dead) if (d < TL) ++shifted;
        TL -= shifted;
    }

    // ── 4. THE OBLIQUE CUTS (the two walls; prereg P2/P3 geometry) ──
    // Each wall: plane through the JOINT PIN (the skeleton is the
    // placement authority), normal along the proximal bone axis,
    // pointing distal. pd < 0 = proximal. Below daughter = proximal
    // segment (thigh, then shin); above daughter appends.
    auto oblique_cut = [&](int cell_idx, const std::array<float,3>& nrm,
                           const std::array<float,3>& pt,
                           std::string& why) -> bool {
        const size_t ncut0 = cut_src_.size();
        std::vector<CutBlend> pts(nv + ncut0);
        for (uint32_t v = 0; v < nv; ++v) {
            pts[v].n = 1; pts[v].v[0] = v; pts[v].w[0] = 1.f;
        }
        for (size_t k = 0; k < ncut0; ++k) pts[nv + k] = cut_src_[k];
        std::vector<float> py(pts.size(), 0.f), pd(pts.size(), 0.f);
        float dmin = 1e30f, dmax = -1e30f;
        for (size_t s = 0; s < pts.size(); ++s) {
            const CutBlend& b = pts[s];
            float px = 0.f, pyy = 0.f, pz = 0.f;
            for (int i = 0; i < b.n; ++i) {
                px += b.w[i] * rest9[b.v[i] * 9 + 0];
                pyy += b.w[i] * rest9[b.v[i] * 9 + 1];
                pz += b.w[i] * rest9[b.v[i] * 9 + 2];
            }
            py[s] = pyy;
            pd[s] = nrm[0] * (px - pt[0]) + nrm[1] * (pyy - pt[1])
                  + nrm[2] * (pz - pt[2]);
            dmin = std::min(dmin, pd[s]); dmax = std::max(dmax, pd[s]);
        }
        if (!(dmin < 0.f) || !(dmax > 0.f)) {
            why = "refused: the plane does not cross the leg cell";
            return false;
        }
        return seal_cut_core_(cell_idx, pts, pd, py, rest9, ncut0);
    };
    auto norm3 = [](const std::array<float,3>& d) {
        float L = std::sqrt(d[0]*d[0] + d[1]*d[1] + d[2]*d[2]);
        std::array<float,3> o = {0.f, 0.f, 0.f};
        if (L > 1e-12f) { o = {d[0]/L, d[1]/L, d[2]/L}; }
        return o;
    };
    const std::array<float,3> knee_p = joint_pins_[(size_t)PIN_KNEE];
    const std::array<float,3> ankle_p = joint_pins_[(size_t)PIN_ANKLE];
    const std::array<float,3> hip_p = joint_pins_[(size_t)PIN_HIP];
    std::array<float,3> n_knee = norm3({knee_p[0]-hip_p[0], knee_p[1]-hip_p[1],
                                        knee_p[2]-hip_p[2]});
    std::array<float,3> n_ankle = norm3({ankle_p[0]-knee_p[0],
                                         ankle_p[1]-knee_p[1],
                                         ankle_p[2]-knee_p[2]});
    std::string why;
    if (!oblique_cut(TL, n_knee, knee_p, why)) {
        report = why + " [knee wall]"; return false;
    }
    const int SF = (int)seal_cells_.size() - 1;   // shin+foot daughter
    if (!oblique_cut(SF, n_ankle, ankle_p, why)) {
        report = why + " [ankle wall]"; return false;
    }
    const int SL = SF;                            // shin (proximal daughter)
    const int FT = (int)seal_cells_.size() - 1;   // foot (appended)

    // THE WINDOW-10 NaN, FIXED AT THE MECHANISM: the oblique cuts appended
    // wall slots to cut_src_; the geometry caches built at route entry do
    // not cover them, and any div_pieces_ over a new cell read PAST the
    // end of the stale cutrest vector (operator[] does not bound-check --
    // heap garbage as floats = -nan in all three segment volumes, while
    // the LIVE per-tick path stayed finite because step() recomputes
    // cut_pos_ from the resized cut_src_ every tick). Every cache is only
    // valid until the next cut mutates cut_src_: rebuild, then validate.
    rest_geometry_locked_(rest9, cutrest);

    // ── 5. NAME + VALIDATE (prereg P4-P7 numbers) ───────────────────
    // seed agreement: binding seeds vs the wall sides (prereg P2/P3).
    // Seed labels from the BINDING ONLY: hip->thigh, knee->shin,
    // ankle->foot. Wall truth from the plane sides at rest.
    auto pd_at = [&](const std::array<float,3>& nrm,
                     const std::array<float,3>& pt, uint32_t v) -> float {
        return nrm[0] * (rest9[(size_t)v * 9 + 0] - pt[0])
             + nrm[1] * (rest9[(size_t)v * 9 + 1] - pt[1])
             + nrm[2] * (rest9[(size_t)v * 9 + 2] - pt[2]);
    };
    int seed_tot[3] = {0, 0, 0}, seed_ok[3] = {0, 0, 0};
    for (uint32_t v = 0; v < nv; ++v) {
        int d = dom[v];
        if (d != PIN_HIP && d != PIN_KNEE && d != PIN_ANKLE) continue;
        int pop_i = d == PIN_HIP ? 0 : (d == PIN_KNEE ? 1 : 2);
        ++seed_tot[pop_i];
        bool thigh_side = pd_at(n_knee, knee_p, v) < 0.f;
        bool foot_side = !thigh_side && pd_at(n_ankle, ankle_p, v) >= 0.f;
        int wall_label = thigh_side ? 0 : (foot_side ? 2 : 1);
        if (wall_label == pop_i) ++seed_ok[pop_i];
    }
    int seed_all_tot = seed_tot[0] + seed_tot[1] + seed_tot[2];
    int seed_all_ok = seed_ok[0] + seed_ok[1] + seed_ok[2];

    // per-segment validation: closure/chi, volumes, pieces
    struct SegRep { int cell; float v0; int chi; bool closed; uint32_t pieces; };
    auto validate_cell = [&](int idx, SegRep* out) -> bool {
        SegRep r;
        r.cell = idx;
        r.v0 = div_pieces_(seal_cells_[(size_t)idx].pieces, rest9, cutrest);
        r.pieces = (uint32_t)(seal_cells_[(size_t)idx].pieces.size() / 3);
        r.closed = cell_topology_(seal_cells_[(size_t)idx].pieces, &r.chi);
        *out = r;
        return r.closed && r.v0 > 0.f
            && r.v0 >= SEAL_DEGENERATE_FRAC * v0_leg;
    };
    SegRep rt, rs, rf;
    bool okt = validate_cell(TL, &rt), oks = validate_cell(SL, &rs),
         okf = validate_cell(FT, &rf);
    // every OTHER cell must also still close (the torso holds the other
    // winding of the hip wall; the R components are untouched, but the
    // books must balance).
    bool others_ok = true;
    float sum_v0 = 0.f;
    long genus_after = 0;
    int closed_after = 0;
    // THE TRIANGLE BOOK (the window-11 fix; the old law counted SLOT
    // occurrences and could never pass: welded seams share SLOTS between
    // neighboring cells BY DESIGN — one physical wall = shared slots).
    // The honest invariant is per TRIANGLE (a slot-triple, the same
    // identity the wall-strip uses): a triangle appears ONCE (skin) or
    // TWICE (ONE septum's two windings, one per owning neighbor). Three
    // or more = a real triple-booking defect. septa = the count of
    // twice-owned triangles (the walls this body carries).
    std::map<std::array<uint32_t, 3>, int> triple_book;
    for (size_t i = 0; i < seal_cells_.size(); ++i) {
        const auto& pc = seal_cells_[i].pieces;
        for (size_t j = 0; j + 2 < pc.size(); j += 3) {
            std::array<uint32_t, 3> t = {pc[j], pc[j + 1], pc[j + 2]};
            std::sort(t.begin(), t.end());
            triple_book[t] += 1;
        }
        int closed_n = 0;
        genus_after += genus_of(pc, &closed_n);
        closed_after += closed_n;
        sum_v0 += div_pieces_(pc, rest9, cutrest);
    }
    int septa = 0;
    for (const auto& kv : triple_book) {
        if (kv.second > 2) others_ok = false;   // 3+ owners: a defect
        if (kv.second == 2) ++septa;
    }
    // THE WHOLE-VOLUME REFERENCE, RECOMPUTED (not assumed): vol_whole0_
    // is only set by the first EXECUTED seal and is not in the restore
    // blob -- reading it after a blob restore would silently trivialize
    // the coverage check. The reference is the whole-creature divergence
    // over THIS mesh's rest blend (the same arithmetic the first seal
    // used to set it), so the check is honest on any boot path.
    float vw_ref = 0.f;
    for (size_t i = 0; i + 2 < tri_verts_.size(); i += 3) {
        uint32_t a = tri_verts_[i], b = tri_verts_[i + 1], cc = tri_verts_[i + 2];
        vw_ref += (rest9[a*9+0] * (rest9[b*9+1] * rest9[cc*9+2] - rest9[b*9+2] * rest9[cc*9+1])
                 + rest9[a*9+1] * (rest9[b*9+2] * rest9[cc*9+0] - rest9[b*9+0] * rest9[cc*9+2])
                 + rest9[a*9+2] * (rest9[b*9+0] * rest9[cc*9+1] - rest9[b*9+1] * rest9[cc*9+0])) / 6.f;
    }
    float cover_pct = vw_ref != 0.f
        ? (sum_v0 - vw_ref) / vw_ref * 100.f : 0.f;
    float mass_total = sum_v0 * LIMB_MASS_RHO;

    // (genus_before captured at entry -- see below; kept next to the
    //  publication so the numbers live together in the report.)
    bool pass = okt && oks && okf && others_ok
        && std::fabs(cover_pct) < 0.01f
        && std::fabs(mass_total - LIMB_MASS_TARGET_KG) <= 0.0001f * LIMB_MASS_TARGET_KG
        && genus_after == genus_before;

    // ── 6. THE REPORT ───────────────────────────────────────────────
    std::ostringstream o;
    o << "{\"side\":\"" << side << "\""
      << ",\"chain\":{\"hip\":" << PIN_HIP << ",\"knee\":" << PIN_KNEE
      << ",\"ankle\":" << PIN_ANKLE
      << ",\"adj_hip_knee\":" << adj_count(PIN_HIP, PIN_KNEE)
      << ",\"adj_knee_ankle\":" << adj_count(PIN_KNEE, PIN_ANKLE)
      << ",\"adj_hip_ankle\":" << adj_count(PIN_HIP, PIN_ANKLE)
      << ",\"pop_hip\":" << pop[(size_t)PIN_HIP]
      << ",\"pop_knee\":" << pop[(size_t)PIN_KNEE]
      << ",\"pop_ankle\":" << pop[(size_t)PIN_ANKLE] << "}"
      << ",\"walls_removed\":" << (walls_removed / 2)
      << ",\"segments\":["
      // thigh
      << "{\"name\":\"thigh_" << side << "\",\"cell\":" << TL
      << ",\"pins\":[" << PIN_HIP << "," << PIN_KNEE << "]"
      << ",\"v0\":" << jf(rt.v0) << ",\"pieces\":" << rt.pieces
      << ",\"closed\":" << (rt.closed ? "true" : "false")
      << ",\"chi\":" << rt.chi
      << ",\"plane_n\":[" << n_knee[0] << "," << n_knee[1] << "," << n_knee[2] << "]"
      << ",\"plane_p\":[" << knee_p[0] << "," << knee_p[1] << "," << knee_p[2] << "]"
      << ",\"mass_kg\":" << jf(rt.v0 * LIMB_MASS_RHO) << "},"
      // shin
      << "{\"name\":\"shin_" << side << "\",\"cell\":" << SL
      << ",\"pins\":[" << PIN_KNEE << "," << PIN_ANKLE << "]"
      << ",\"v0\":" << jf(rs.v0) << ",\"pieces\":" << rs.pieces
      << ",\"closed\":" << (rs.closed ? "true" : "false")
      << ",\"chi\":" << rs.chi
      << ",\"plane_n\":[" << n_ankle[0] << "," << n_ankle[1] << "," << n_ankle[2] << "]"
      << ",\"plane_p\":[" << ankle_p[0] << "," << ankle_p[1] << "," << ankle_p[2] << "]"
      << ",\"mass_kg\":" << jf(rs.v0 * LIMB_MASS_RHO) << "},"
      // foot
      << "{\"name\":\"foot_" << side << "\",\"cell\":" << FT
      << ",\"pins\":[" << PIN_ANKLE << "]"
      << ",\"v0\":" << jf(rf.v0) << ",\"pieces\":" << rf.pieces
      << ",\"closed\":" << (rf.closed ? "true" : "false")
      << ",\"chi\":" << rf.chi
      << ",\"plane_n\":null,\"plane_p\":null"
      << ",\"mass_kg\":" << jf(rf.v0 * LIMB_MASS_RHO) << "}]"
      << ",\"seed_agreement\":{\"all\":{\"n\":" << seed_all_tot
      << ",\"ok\":" << seed_all_ok
      << ",\"frac\":" << jf(seed_all_tot ? (float)seed_all_ok / (float)seed_all_tot : 0.f)
      << "},\"hip\":{\"n\":" << seed_tot[0] << ",\"ok\":" << seed_ok[0] << "}"
      << ",\"knee\":{\"n\":" << seed_tot[1] << ",\"ok\":" << seed_ok[1] << "}"
      << ",\"ankle\":{\"n\":" << seed_tot[2] << ",\"ok\":" << seed_ok[2] << "}}"
      << ",\"validation\":{\"n_cells\":" << seal_cells_.size()
      << ",\"sum_v0\":" << sum_v0
      << ",\"vol_whole_ref\":" << vw_ref
      << ",\"coverage_pct\":" << cover_pct
      << ",\"mass_total_kg\":" << mass_total
      << ",\"mass_target_kg\":" << LIMB_MASS_TARGET_KG
      << ",\"genus_sum_2_minus_chi_before\":" << genus_before
      << ",\"genus_sum_2_minus_chi_after\":" << genus_after
      << ",\"closed_components_before\":" << closed_before
      << ",\"closed_components_after\":" << closed_after
      << ",\"septa_twice_owned_triangles\":" << septa
      << ",\"piece_book_unique\":" << (others_ok ? "true" : "false")
      << ",\"pass\":" << (pass ? "true" : "false") << "}}";
    report = o.str();

    if (!pass) {
        // publish NOTHING as done: the validation numbers are the refusal.
        report = "{\"pass\":false,\"detail\":" + report + "}";
        return false;
    }

    // ── 7. THE REGISTRY + PATCH REGIONS ─────────────────────────────
    limb_segs_.clear();
    LimbSeg sg;
    sg.name = std::string("thigh_") + side;
    sg.cell = TL; sg.pin_prox = PIN_HIP; sg.pin_dist = PIN_KNEE;
    sg.plane_n = n_knee; sg.plane_p = knee_p; sg.v0 = rt.v0;
    sg.pieces = rt.pieces;
    sg.seed_total = seed_tot[0]; sg.seed_agree = seed_ok[0];
    limb_segs_.push_back(sg);
    sg.name = std::string("shin_") + side;
    sg.cell = SL; sg.pin_prox = PIN_KNEE; sg.pin_dist = PIN_ANKLE;
    sg.plane_n = n_ankle; sg.plane_p = ankle_p; sg.v0 = rs.v0;
    sg.pieces = rs.pieces;
    sg.seed_total = seed_tot[1]; sg.seed_agree = seed_ok[1];
    limb_segs_.push_back(sg);
    sg.name = std::string("foot_") + side;
    sg.cell = FT; sg.pin_prox = PIN_ANKLE; sg.pin_dist = -1;
    sg.plane_n = {0.f, 0.f, 0.f}; sg.plane_p = {0.f, 0.f, 0.f};
    sg.v0 = rf.v0; sg.pieces = rf.pieces;
    sg.seed_total = seed_tot[2]; sg.seed_agree = seed_ok[2];
    limb_segs_.push_back(sg);
    limb_done_ = true;
    limb_side_ = side;
    limb_report_ = report;
    std::string perr;
    if (!patch_build_locked_(perr)) {
        report = "refused: sensor region construction failed: " + perr;
        return false;
    }
    transaction.commit();
    return true;
}

std::string MembraneTick::limb_report_json() const {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    return limb_report_;
}

// ── THE LIMB REGISTRY BLOB (acceptance 10: the partition survives a
// ── restart, or its staleness is VISIBLE). Self-validating: every
// ── segment's cell must exist with the stored piece count and a rest
// ── volume matching to 1e-3 relative (the seal-blob law). A stale blob
// ── refuses with NOTHING changed.
void MembraneTick::export_limb_state(std::vector<uint8_t>& out) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    out.clear();
    if (!limb_done_) return;
    auto put = [&out](const void* p, size_t n) {
        const uint8_t* b = reinterpret_cast<const uint8_t*>(p);
        out.insert(out.end(), b, b + n);
    };
    uint32_t magic = LIMB_STATE_MAGIC;
    uint32_t nv = (uint32_t)(base_pos_.size() / 9);
    uint32_t n_segs = (uint32_t)limb_segs_.size();
    put(&magic, 4); put(&nv, 4); put(&n_segs, 4);
    for (const LimbSeg& s : limb_segs_) {
        char name[32] = {};
        std::memcpy(name, s.name.c_str(),
                    std::min<size_t>(s.name.size(), 31));
        put(name, 32);
        int32_t cell = s.cell, pp = s.pin_prox, pd = s.pin_dist;
        put(&cell, 4); put(&pp, 4); put(&pd, 4);
        put(s.plane_n.data(), 12);
        put(s.plane_p.data(), 12);
        put(&s.v0, 4);
        uint32_t pieces = s.pieces;
        put(&pieces, 4);
    }
    uint32_t n_pat = (uint32_t)patches_.size();
    put(&n_pat, 4);
    for (const SensorPatch& p : patches_) {
        char name[32] = {};
        std::memcpy(name, p.name.c_str(),
                    std::min<size_t>(p.name.size(), 31));
        put(name, 32);
        int32_t cell = p.cell, sd = p.side;
        put(&cell, 4); put(&sd, 4);
        put(&p.tau_f, 4); put(&p.sat_m, 4);
        put(&p.delay_s, 4); put(&p.thresh_m, 4);
    }
}

bool MembraneTick::limb_restore(const std::string& body) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (body.size() < 12) return false;
    uint32_t magic = 0, nv = 0, n_segs = 0;
    std::memcpy(&magic, body.data() + 0, 4);
    std::memcpy(&nv, body.data() + 4, 4);
    std::memcpy(&n_segs, body.data() + 8, 4);
    if (magic != LIMB_STATE_MAGIC) return false;
    if (nv != (uint32_t)(base_pos_.size() / 9)) return false;
    if (n_segs != 3) return false;
    // per-segment record: name[32] + cell/prox/dist (12) + plane_n (12)
    // + plane_p (12) + v0 (4) + pieces (4) = 76 B
    size_t need = 12 + (size_t)n_segs * 76 + 4;
    if (body.size() < need) return false;
    // validate EVERY segment against the live tree before mutating
    std::vector<float> rest9, cutrest;
    rest_geometry_locked_(rest9, cutrest);
    std::vector<LimbSeg> cands;
    std::set<int> cells_seen;
    size_t off = 12;
    for (uint32_t i = 0; i < n_segs; ++i) {
        const char* name = body.data() + off; off += 32;
        int32_t cell, pp, pd; float v0; uint32_t pieces;
        std::memcpy(&cell, body.data() + off, 4); off += 4;
        std::memcpy(&pp, body.data() + off, 4); off += 4;
        std::memcpy(&pd, body.data() + off, 4); off += 4;
        LimbSeg s;
        s.name = std::string(name, strnlen(name, 32));
        s.cell = cell; s.pin_prox = pp; s.pin_dist = pd;
        std::memcpy(s.plane_n.data(), body.data() + off, 12); off += 12;
        std::memcpy(s.plane_p.data(), body.data() + off, 12); off += 12;
        std::memcpy(&v0, body.data() + off, 4); off += 4;
        std::memcpy(&pieces, body.data() + off, 4); off += 4;
        s.v0 = v0; s.pieces = pieces;
        if (cell < 0 || (size_t)cell >= seal_cells_.size()) return false;
        if (!cells_seen.insert(cell).second || !std::isfinite(v0) || v0 <= 0.f)
            return false;
        const bool right = s.name.size() >= 2 && s.name.back() == 'R';
        const char* names[3] = {"thigh_", "shin_", "foot_"};
        const int hip = right ? 14 : 13;
        if (s.name != std::string(names[i]) + (right ? "R" : "L")
            || (i && right != (cands.front().name.back() == 'R'))
            || pp != hip + (int)i * 2
            || pd != (i == 2 ? -1 : pp + 2)
            || (size_t)pp >= joint_pins_.size()) return false;
        for (int k = 0; k < 3; ++k)
            if (!std::isfinite(s.plane_n[k]) || !std::isfinite(s.plane_p[k]))
                return false;
        const SealCell& c = seal_cells_[(size_t)cell];
        if ((uint32_t)(c.pieces.size() / 3) != pieces) return false;
        float live = div_pieces_(c.pieces, rest9, cutrest);
        if (!(std::fabs(live - v0) <= 1e-3f * std::max(1e-12f, std::fabs(live))))
            return false;              // a stale blob refuses, unchanged
        cands.push_back(s);
    }
    uint32_t n_pat = 0;
    std::memcpy(&n_pat, body.data() + off, 4); off += 4;
    // LMB1 has ALWAYS written 56 bytes per patch (32 + six 4-byte fields).
    // Do not add padding to compensate for the old reader's 60-byte typo.
    constexpr size_t patch_record_bytes = 32 + 6 * 4;
    if (n_pat != cands.size() || n_pat > (body.size() - off) / patch_record_bytes
        || body.size() - off != (size_t)n_pat * patch_record_bytes) return false;
    struct PatCand { std::string name; int cell; int side;
                     float tau, sat, delay, thresh; };
    std::vector<PatCand> pats;
    std::set<std::string> patch_names;
    for (uint32_t i = 0; i < n_pat; ++i) {
        if (body.size() - off < patch_record_bytes) return false;
        const char* name = body.data() + off; off += 32;
        PatCand p;
        p.name = std::string(name, strnlen(name, 32));
        std::memcpy(&p.cell, body.data() + off, 4); off += 4;
        std::memcpy(&p.side, body.data() + off, 4); off += 4;
        std::memcpy(&p.tau, body.data() + off, 4); off += 4;
        std::memcpy(&p.sat, body.data() + off, 4); off += 4;
        std::memcpy(&p.delay, body.data() + off, 4); off += 4;
        std::memcpy(&p.thresh, body.data() + off, 4); off += 4;
        const auto seg = std::find_if(cands.begin(), cands.end(),
            [&](const LimbSeg& s) { return s.name == p.name; });
        if (seg == cands.end() || !patch_names.insert(p.name).second
            || p.cell != seg->cell || p.side != (p.name.back() == 'R' ? 1 : 0)
            || !std::isfinite(p.tau) || p.tau <= 0.f
            || !std::isfinite(p.sat) || p.sat <= 0.f
            || !std::isfinite(p.delay) || p.delay < 0.f
            || !std::isfinite(p.thresh) || p.thresh <= 0.f) return false;
        pats.push_back(p);
    }
    StateRollback transaction(limb_segs_, limb_report_, limb_done_, limb_side_,
        patches_, patches_armed_, patch_clock_s_, patch_event_log_);
    // commit: registry in, patch regions REBUILT by the deterministic
    // radius rule (vertex lists are derived state, not authored state),
    // then the stored receptor constants applied on top. The report is
    // an honest stub: the LIVE report is what /tick_limb answered with;
    // this says the registry came back from the blob, which is the truth.
    limb_segs_ = cands;
    limb_report_ = "{\"restored\":true}";
    limb_done_ = true;
    limb_side_ = "L";
    if (!limb_segs_.empty() && limb_segs_[0].name.size() >= 2
        && limb_segs_[0].name[limb_segs_[0].name.size() - 1] == 'R')
        limb_side_ = "R";
    patches_.clear();
    {
        // ONE radius-rule implementation (patch_build_locked_): the
        // receptor regions are DERIVED state, rebuilt from the validated
        // cells; the stored constants are then applied on top.
        std::string perr;
        if (!patch_build_locked_(perr)) return false;
    }
    if (patches_.size() != pats.size()) return false;
    for (const PatCand& p : pats) {
        SensorPatch* sp = nullptr;
        for (SensorPatch& q : patches_)
            if (q.name == p.name) { sp = &q; break; }
        if (!sp) return false;         // the blob's patches must be the
                                       // registry's patches, by name
        sp->tau_f = p.tau; sp->sat_m = p.sat;
        sp->delay_s = p.delay; sp->thresh_m = p.thresh;
        sp->connected = true;          // connection state lives in the
                                       // patch-state blob (applied after)
    }
    // LMB1 is a construction recipe. Its new receptors are disarmed until
    // the explicit arm command or subsequent PAT1/PAT2 restoration.
    patches_armed_ = false;
    patch_clock_s_ = 0.f;
    transaction.commit();
    return true;
}

// ── THE PATCH RECIPE (single implementation of the finite receptor
// ── region: distal-half anchor, the 5%-coverage radius rule, the
// ── measured conduction delay). Called by /tick_limb (fresh build) and
// ── limb_restore (deterministic rebuild). Assumes seal_mtx_ held.
bool MembraneTick::patch_build_locked_(std::string& err) {
    std::vector<SensorPatch> built;
    err.clear();
    if (!limb_done_ || limb_segs_.empty()) {
        err = "no limb registry"; return false;
    }
    if (joint_pins_.size() <= (size_t)LIMB_PIN_SPINE_LOW) {
        err = "no spine-lower pin for the delay path"; return false;
    }
    const uint32_t nv = (uint32_t)(base_pos_.size() / 9);
    std::vector<float> rest9, cutrest;
    rest_geometry_locked_(rest9, cutrest);
    const std::array<float,3> term = joint_pins_[(size_t)LIMB_PIN_SPINE_LOW];
    for (const LimbSeg& seg : limb_segs_) {
        if (seg.cell < 0 || (size_t)seg.cell >= seal_cells_.size()) {
            err = "segment cell out of range"; return false;
        }
        std::vector<uint32_t> verts;
        for (uint32_t s : seal_cells_[(size_t)seg.cell].pieces)
            if (s < nv) verts.push_back(s);
        std::sort(verts.begin(), verts.end());
        verts.erase(std::unique(verts.begin(), verts.end()), verts.end());
        if (verts.size() < 32) {
            err = "segment too small for a receptor region"; return false;
        }
        std::array<float,3> cseg = {0.f, 0.f, 0.f};
        for (uint32_t v : verts) {
            cseg[0] += rest9[(size_t)v * 9 + 0];
            cseg[1] += rest9[(size_t)v * 9 + 1];
            cseg[2] += rest9[(size_t)v * 9 + 2];
        }
        float inv = 1.f / (float)verts.size();
        cseg = {cseg[0] * inv, cseg[1] * inv, cseg[2] * inv};
        std::array<float,3> axis = seg.plane_n;
        float al = std::sqrt(axis[0]*axis[0] + axis[1]*axis[1]
                           + axis[2]*axis[2]);
        if (al < 1e-12f) axis = {0.f, -1.f, 0.f};   // the foot: distal = down
        else axis = {axis[0]/al, axis[1]/al, axis[2]/al};
        std::vector<float> tproj(verts.size());
        for (size_t i = 0; i < verts.size(); ++i) {
            uint32_t v = verts[i];
            tproj[i] = axis[0] * (rest9[(size_t)v * 9 + 0] - cseg[0])
                     + axis[1] * (rest9[(size_t)v * 9 + 1] - cseg[1])
                     + axis[2] * (rest9[(size_t)v * 9 + 2] - cseg[2]);
        }
        std::vector<float> st = tproj;
        std::sort(st.begin(), st.end());
        float med = st[st.size() / 2];
        std::array<float,3> anchor = {0.f, 0.f, 0.f};
        size_t na = 0;
        for (size_t i = 0; i < verts.size(); ++i)
            if (tproj[i] >= med) {
                anchor[0] += rest9[(size_t)verts[i] * 9 + 0];
                anchor[1] += rest9[(size_t)verts[i] * 9 + 1];
                anchor[2] += rest9[(size_t)verts[i] * 9 + 2];
                ++na;
            }
        if (!na) { err = "no distal half"; return false; }
        anchor = {anchor[0] / (float)na, anchor[1] / (float)na,
                  anchor[2] / (float)na};
        std::vector<float> dists(verts.size());
        for (size_t i = 0; i < verts.size(); ++i) {
            uint32_t v = verts[i];
            float dx = rest9[(size_t)v * 9 + 0] - anchor[0];
            float dy = rest9[(size_t)v * 9 + 1] - anchor[1];
            float dz = rest9[(size_t)v * 9 + 2] - anchor[2];
            dists[i] = std::sqrt(dx*dx + dy*dy + dz*dz);
        }
        std::vector<float> sd = dists;
        std::sort(sd.begin(), sd.end());
        size_t k = std::min(verts.size() - 1,
            (size_t)std::ceil(LIMB_PATCH_FRAC * (float)verts.size()) - 1);
        float R = sd[k];
        SensorPatch p;
        p.name = seg.name;
        for (size_t i = 0; i < verts.size(); ++i)
            if (dists[i] <= R) p.verts.push_back(verts[i]);
        p.c = anchor;
        p.cell = seg.cell;
        p.side = (!seg.name.empty() && seg.name.back() == 'R') ? 1 : 0;
        float dx = anchor[0] - term[0], dy = anchor[1] - term[1],
              dz = anchor[2] - term[2];
        p.delay_s = std::sqrt(dx*dx + dy*dy + dz*dz) / LIMB_CONDUCTION_V;
        p.tau_f = LIMB_TAU_S;
        p.sat_m = press_r0_;
        p.thresh_m = LIMB_THRESH_M;
        built.push_back(std::move(p));
    }
    patches_.swap(built);
    return true;
}

bool MembraneTick::patch_arm(bool on, std::string& err) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    err.clear();
    if (on) {
        if (!limb_done_ || patches_.empty()) {
            err = "refused: no limb registry (run /tick_limb first)";
            return false;
        }
        if (!patches_armed_) {
            patches_armed_ = true;
            patch_clock_s_ = 0.f;
            for (SensorPatch& p : patches_) {
                p.filt = 0.f; p.out = 0.f; p.prev_out = 0.f;
                p.line.clear();
            }
        }
        return true;
    }
    patch_off_locked_();
    return true;
}

bool MembraneTick::patch_connect(const std::string& name, bool connected,
                                 std::string& err) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    err.clear();
    for (SensorPatch& p : patches_) {
        if (p.name != name) continue;
        if (p.connected == connected) return true;   // already the state
        p.connected = connected;
        if (!connected) {
            // A CUT IS A REAL STATE: the line drains, nothing delivers,
            // the cut carries its tick and the engine's own timestamp.
            p.line.clear();
            p.out = 0.f; p.prev_out = 0.f;
            p.cut_tick = ticks_;
            p.cut_us = std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::steady_clock::now().time_since_epoch()).count();
            patch_log_locked_(std::string("{\"ev\":\"path_cut\",\"patch\":\"")
                + p.name + "\",\"tick\":" + std::to_string(ticks_)
                + ",\"t_us\":" + std::to_string(p.cut_us) + "}");
        } else {
            // reconnection delivers only NEWLY filtered samples: the line
            // is empty, so no stale spike can synthesize (prereg P10)
            int64_t us = std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::steady_clock::now().time_since_epoch()).count();
            patch_log_locked_(std::string("{\"ev\":\"path_connect\",\"patch\":\"")
                + p.name + "\",\"tick\":" + std::to_string(ticks_)
                + ",\"t_us\":" + std::to_string(us) + "}");
        }
        return true;
    }
    err = "refused: unknown patch \"" + name + "\"";
    return false;
}

// bounded event log (the acceptance-9 surface: consistent IDs + the
// engine's own timestamps, one line per sensor/cut event)
void MembraneTick::patch_log_locked_(const std::string& row) {
    patch_event_log_.push_back(row);
    if (patch_event_log_.size() > PATCH_LOG_N)
        patch_event_log_.erase(patch_event_log_.begin(),
                               patch_event_log_.begin() + (long)
                                   (patch_event_log_.size() - PATCH_LOG_N));
}

bool MembraneTick::patch_step_locked_(float dt) {
    if (!patches_armed_ || patches_.empty()) return true;
    const float dts = std::min(std::max(dt, 0.f), 0.05f);   // stall guard
    const size_t nverts = press_off_.size();
    for (SensorPatch& p : patches_) {
        p.clock_s += dts;
        // raw = the skin's OWN local indentation over the patch's
        // vertices -- the only quantity the controller may feel
        float raw = 0.f;
        for (uint32_t v : p.verts)
            if ((size_t)v < nverts) raw = std::max(raw, press_off_[v]);
        p.last_raw = raw;
        if (dts > 0.f)
            p.filt += (raw - p.filt)
                    * (1.f - std::exp(-dts / std::max(1e-6f, p.tau_f)));
        const float satv = p.sat_m > 0.f
            ? p.sat_m * std::tanh(p.filt / p.sat_m) : p.filt;
        if (p.connected) {
            p.line.emplace_back(p.clock_s, satv);
            // deliver everything old enough: the FINITE transport delay
            while (!p.line.empty()
                   && p.line.front().first <= p.clock_s - p.delay_s) {
                p.out = p.line.front().second;
                p.line.pop_front();
            }
        }
        // rising edge on the DELIVERED signal only
        if (p.connected && p.out >= p.thresh_m && p.prev_out < p.thresh_m) {
            ++p.fires;
            p.last_fire_tick = ticks_;
            int64_t us = std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::steady_clock::now().time_since_epoch()).count();
            patch_log_locked_(std::string("{\"ev\":\"sensor\",\"patch\":\"")
                + p.name + "\",\"cell\":" + std::to_string(p.cell)
                + ",\"tick\":" + std::to_string(ticks_)
                + ",\"t_us\":" + std::to_string(us)
                + ",\"out_m\":" + jf(p.out) + "}");
        }
        p.prev_out = p.out;
    }
    return true;
}

void MembraneTick::patch_off_locked_() {
    // deterministic off (the flex-0 precedent): the receptor state
    // empties, the paths return CONNECTED (a disarm is not a cut history),
    // the event log keeps its history (it is the record).
    patches_armed_ = false;
    for (SensorPatch& p : patches_) {
        p.filt = 0.f; p.out = 0.f; p.prev_out = 0.f;
        p.line.clear();
        p.connected = true;
    }
    patch_clock_s_ = 0.f;
}

std::string MembraneTick::patch_json() const {
    // route callers: lock (the vector is mutated under seal_mtx_)
    std::lock_guard<std::mutex> lk(seal_mtx_);
    return patch_json_locked();
}

std::string MembraneTick::patch_json_locked() const {
    // caller holds seal_mtx_ (state_json / patch_json)
    std::ostringstream o;
    o << "{\"armed\":" << (patches_armed_ ? "true" : "false")
      << ",\"n\":" << patches_.size() << ",\"patches\":[";
    for (size_t i = 0; i < patches_.size(); ++i) {
        const SensorPatch& p = patches_[i];
        if (i) o << ",";
        o << "{\"name\":\"" << p.name << "\",\"cell\":" << p.cell
          << ",\"side\":" << (p.side == 0 ? "\"L\"" : "\"R\"")
          << ",\"nv\":" << p.verts.size()
          << ",\"connected\":" << (p.connected ? "true" : "false")
          << ",\"cut_tick\":" << p.cut_tick
          << ",\"delay_s\":" << jf(p.delay_s)
          << ",\"tau_s\":" << jf(p.tau_f)
          << ",\"sat_m\":" << jf(p.sat_m)
          << ",\"thresh_m\":" << jf(p.thresh_m)
          << ",\"filt_m\":" << jf(p.filt)
          << ",\"out_m\":" << jf(p.out)
          << ",\"fires\":" << p.fires
          << ",\"last_fire_tick\":" << p.last_fire_tick << "}";
    }
    o << "]}";
    return o.str();
}

void MembraneTick::export_patch_state(std::vector<uint8_t>& out) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    out.clear();
    auto put = [&out](const void* p, size_t n) {
        const uint8_t* b = reinterpret_cast<const uint8_t*>(p);
        out.insert(out.end(), b, b + n);
    };
    // PAT2: sensor-subsystem checkpoint. The descriptor preceding each state
    // record must match the already-restored receptor registry exactly.
    uint32_t magic = PATCH_CHECKPOINT_MAGIC;
    uint8_t armed = patches_armed_ ? 1 : 0;
    uint32_t n = (uint32_t)patches_.size();
    put(&magic, 4); put(&armed, 1); put(&n, 4);
    put(&patch_clock_s_, 4);
    for (const SensorPatch& p : patches_) {
        char name[32] = {};
        std::memcpy(name, p.name.c_str(),
                    std::min<size_t>(p.name.size(), 31));
        put(name, 32);
        int32_t cell = p.cell, side = p.side;
        put(&cell, 4); put(&side, 4); put(p.c.data(), 12);
        put(&p.tau_f, 4); put(&p.sat_m, 4);
        put(&p.delay_s, 4); put(&p.thresh_m, 4);
        uint32_t nv = (uint32_t)p.verts.size();
        put(&nv, 4);
        for (uint32_t v : p.verts) put(&v, 4);
        uint8_t conn = p.connected ? 1 : 0;
        put(&conn, 1);
        uint64_t ct = p.cut_tick;
        put(&ct, 8);
        put(&p.cut_us, 8);
        put(&p.filt, 4); put(&p.out, 4); put(&p.prev_out, 4); put(&p.clock_s, 4);
        put(&p.last_fire_tick, 8);
        int32_t fires = p.fires;
        put(&fires, 4); put(&p.last_raw, 4);
        uint32_t nq = (uint32_t)p.line.size();
        put(&nq, 4);
        for (const auto& sample : p.line) {
            put(&sample.first, 4); put(&sample.second, 4);
        }
    }
}

bool MembraneTick::patch_restore(const std::string& body) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    StateReader reader(body);
    uint32_t magic = 0; uint8_t armed = 0; uint32_t n = 0;
    if (!reader.take(magic) || !reader.take(armed) || !reader.take(n)
        || armed > 1 || n != patches_.size()) return false;
    const bool checkpoint = magic == PATCH_CHECKPOINT_MAGIC;
    if (!checkpoint && magic != PATCH_STATE_MAGIC) return false;
    float clock = 0.f;
    if (checkpoint) {
        if (!reader.take(clock) || !std::isfinite(clock) || clock < 0.f) return false;
    } else if (n > reader.remaining() / 41 || reader.remaining() != (size_t)n * 41) {
        return false;  // PAT1 is an exact, fixed-width recipe, never a checkpoint.
    }
    auto candidate = patches_;
    std::set<std::string> seen;
    for (uint32_t i = 0; i < n; ++i) {
        std::string name;
        if (!reader.name(name) || !seen.insert(name).second) return false;
        auto it = std::find_if(candidate.begin(), candidate.end(),
            [&](const SensorPatch& p) { return p.name == name; });
        if (it == candidate.end()) return false;
        SensorPatch& p = *it;
        if (checkpoint) {
            int32_t cell = -1, side = -1;
            std::array<float, 3> center;
            std::array<float, 4> params;
            uint32_t nv = 0;
            if (!reader.take(cell) || !reader.take(side) || !reader.take(center)
                || !reader.take(params) || !reader.take(nv)
                || cell != p.cell || side != p.side || center != p.c
                || params != std::array<float, 4>{p.tau_f,p.sat_m,p.delay_s,p.thresh_m}
                || nv != p.verts.size() || nv > reader.remaining() / 4) return false;
            for (uint32_t v : p.verts) {
                uint32_t saved = 0;
                if (!reader.take(saved) || saved != v) return false;
            }
        }
        uint8_t conn = 0; uint64_t ct = 0;
        if (!reader.take(conn) || !reader.take(ct) || conn > 1) return false;
        p.connected = conn != 0;
        p.cut_tick = ct;
        p.line.clear();
        if (checkpoint) {
            int32_t fires = 0; uint32_t nq = 0;
            if (!reader.take(p.cut_us) || !reader.take(p.filt) || !reader.take(p.out)
                || !reader.take(p.prev_out) || !reader.take(p.clock_s)
                || !reader.take(p.last_fire_tick) || !reader.take(fires)
                || !reader.take(p.last_raw) || !reader.take(nq)
                || fires < 0 || nq > reader.remaining() / 8) return false;
            for (float v : {p.filt,p.out,p.prev_out,p.clock_s,p.last_raw})
                if (!std::isfinite(v)) return false;
            if (p.clock_s < 0.f) return false;
            p.fires = fires;
            float previous = 0.f;
            for (uint32_t j = 0; j < nq; ++j) {
                float time = 0.f, value = 0.f;
                if (!reader.take(time) || !reader.take(value)
                    || !std::isfinite(time) || !std::isfinite(value)
                    || time < previous || time > p.clock_s) return false;
                p.line.emplace_back(time, value);
                previous = time;
            }
            if (!p.connected && (!p.line.empty() || p.out != 0.f || p.prev_out != 0.f))
                return false;
        } else {
            // Legacy recipe has no time/filter/queue state to resume. Reset
            // explicitly only after its complete payload has been validated.
            p.cut_tick = p.connected ? 0 : ct;
            p.cut_us = 0;
            p.filt = p.out = p.prev_out = p.clock_s = p.last_raw = 0.f;
            p.fires = 0; p.last_fire_tick = 0;
        }
    }
    if (reader.remaining() != 0) return false;
    patches_.swap(candidate);
    patches_armed_ = armed != 0;
    patch_clock_s_ = clock;
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
    uint64_t evals0 = 0;
    {
        std::lock_guard<std::mutex> lk(seal_mtx_);
        gravity_on_ = on;
        if (!on) {
            root_y_ = 0.f;
            root_vy_ = 0.f;
            g_contact_n_ = 0.f;
            stance_off_locked_();   // F1: the rest contract is exact -- the
                                    // servo may not keep holding ankle poses
                                    // the law no longer balances
            return true;
        }
        // snapshot BEFORE the flag is visible as armed: any ground-force
        // evaluation from here on is one of ours
        evals0 = ground_evals_.load(std::memory_order_relaxed);
    }
    // THE ARM-ON-READINESS GATE (V1b's intermittent inert start, measured
    // window-4): arming used to be a flag flip; a settle probe that read
    // between the flip and the first integrating tick saw the init-reset
    // 0/0 (root_vy exactly 0, contact exactly 0) and called a live body
    // inert -- gravity "engaged MID-RUN" when the tick caught up. The arm
    // now RETURNS on the first completed ground-force evaluation under
    // the flag (bounded: a dead tick loop must not hang the route -- 500 ms
    // degrades to the old flag-only arm). The lock is NOT held here: the
    // tick try_locks and must be free to run.
    for (int i = 0; i < 2500; ++i) {
        if (ground_evals_.load(std::memory_order_acquire) != evals0) break;
        std::this_thread::sleep_for(std::chrono::microseconds(200));
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
    // THE SERVO FRAME IS RADIANS (the 57.3x probe-unit gain, measured):
    // joint_deg_ and apply_travel take radians, but the probe posed
    // exactly 1 deg, so every delta below was PER-DEG while every consumer
    // (servo err/(ch*tau), rate caps, ROM clamp) treats it as PER-RAD. The
    // commanded rotations came out 57.3x over the derived rate caps (the
    // cap clamp itself computed in the deg frame and its product landed in
    // a radian field). Divide by the probed angle ONCE here: every channel
    // below is honestly m/rad and the caps bound the real rad/s.
    const float kProbeRad = 1.f * 3.14159265358979f / 180.f;
    for (int s = 0; s < 2; ++s) {
        const float miny0 = gait_set_miny(rest9, fset[s]);
        float cx0, cy0, cz0;
        gait_set_centroid(rest9, fset[s], &cx0, &cy0, &cz0);
        for (int c = 0; c < 2; ++c) {
            std::vector<float> degs(npins, 0.f);
            std::vector<float> p9;
            float cx, cy, cz;
            degs[(size_t)drive_pin[s][c]] = kProbeRad;
            p9 = rest9;
            apply_travel(p9, &degs);
            dminy_cand[s][c] = (gait_set_miny(p9, fset[s]) - miny0) / kProbeRad;
            gait_set_centroid(p9, fset[s], &cx, &cy, &cz);
            dcz_cand[s][c] = (cz - cz0) / kProbeRad;
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
    // binding the null-z rise channel is 9.5e-2 m/rad in the radian servo
    // frame (the two drive channels are nearly collinear), while the REAL
    // lift is ~5.5 deg of strut for the full 60 mm band (measured live:
    // the 1-deg linearization overshoots the world rise by the root's
    // 10-20 mm follow), rate-capped by mx. An enable refusal
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

    // THE STRIDE-SCALE BRANCH LAW (the strut's z-channel is nonmonotonic
    // in theta on this binding: the 1-deg probe reads +2.6 mm/deg while
    // the measured live ladder peaks near -4.6 deg and swings BACKWARD
    // -35 mm/deg by -20 deg -- an orbit about the pivot, not a rail). A
    // 1-deg probe cannot see the reversal, so the REACH law probes at
    // +20 deg (inside the 89-deg ROM, same rest blend, same travel
    // arithmetic) and derives, per side: lift_sign = the theta sign that
    // RAISES the foot set; reach_dir = the z direction that branch
    // actually swings (sign of lift_sign*dcz20; -1 on the shipped
    // creature -- the usable swing is backward). The opposite branch is
    // measured unusable: it presses the foot DOWN (dminy at +20 deg is
    // about -0.30 m), more than the clear pin's measured rise (2.5-3.2
    // mm/deg, live ladder) can pay while also holding the band.
    // THE WHAT-IF channels (same rest blend): sink_ch = d(min-y of the
    // OTHER foot set) under the lift combo at dparam = 1 rad -- the
    // cross-coupled rise the root follows the support down by; headroom =
    // the grounding distance from the feet's rest min-y to the lowest
    // NON-foot rest vertex minus the derived sink (the rest equilibrium
    // sits one sink above authored rest).
    float dminy20[2], dcz20[2], lift_sign[2], reach_dir[2], sink_ch[2];
    for (int s = 0; s < 2; ++s) {
        const float kBranchRad = 20.f * 3.14159265358979f / 180.f;
        const float miny0 = gait_set_miny(rest9, fset[s]);
        float cx0, cy0, cz0;
        gait_set_centroid(rest9, fset[s], &cx0, &cy0, &cz0);
        std::vector<float> degs(npins, 0.f);
        std::vector<float> p9;
        float cx, cy, cz;
        degs[(size_t)strut_pin[s]] = kBranchRad;
        p9 = rest9;
        apply_travel(p9, &degs);
        dminy20[s] = (gait_set_miny(p9, fset[s]) - miny0) / kBranchRad;
        gait_set_centroid(p9, fset[s], &cx, &cy, &cz);
        dcz20[s] = (cz - cz0) / kBranchRad;
        lift_sign[s] = dminy20[s] > 0.f ? 1.f : -1.f;
        reach_dir[s] = (lift_sign[s] * dcz20[s]) > 0.f ? 1.f : -1.f;
        // the combo at dparam = 1 rad, measured on the OTHER foot set:
        // its min-y RISE is the body sink the root follows
        for (size_t j = 0; j < npins; ++j) degs[j] = 0.f;
        degs[(size_t)strut_pin[s]] = lift_ah[s];
        degs[(size_t)clear_pin[s]] = lift_ak[s];
        p9 = rest9;
        apply_travel(p9, &degs);
        sink_ch[s] = gait_set_miny(p9, fset[1 - s])
                   - gait_set_miny(rest9, fset[1 - s]);
    }
    float nonfoot_miny = 1e30f;
    for (size_t v = 0; v < nv; ++v)
        if (rest9[v * 9 + 1] > feet_yhi)
            nonfoot_miny = std::min(nonfoot_miny, rest9[v * 9 + 1]);
    const float feet_miny = std::min(gait_set_miny(rest9, fset[0]),
                                     gait_set_miny(rest9, fset[1]));
    const float headroom = (nonfoot_miny < 1e29f && feet_miny > -1e29f)
        ? (nonfoot_miny - feet_miny) - GAIT_SINK_M : 0.f;

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
        gait_lift_sign_[s] = lift_sign[s];
        gait_reach_dir_[s] = reach_dir[s];
        gait_dminy20_hip_[s] = dminy20[s];
        gait_dcz20_hip_[s] = dcz20[s];
        gait_sink_ch_[s] = sink_ch[s];
        gait_phase_[s] = GaitPhase::STANCE;
        gait_knee_rad_[s] = gait_hip_rad_[s] = 0.f;
        gait_block_[s].clear();
        gait_last_done_[s] = 0;
    }
    gait_headroom_ = headroom;
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
          << ",\"dminyH20L\":" << gait_dminy20_hip_[0]
          << ",\"dminyH20R\":" << gait_dminy20_hip_[1]
          << ",\"dczH20L\":" << gait_dcz20_hip_[0]
          << ",\"dczH20R\":" << gait_dcz20_hip_[1]
          << ",\"liftSignL\":" << gait_lift_sign_[0]
          << ",\"liftSignR\":" << gait_lift_sign_[1]
          << ",\"reachDirL\":" << gait_reach_dir_[0]
          << ",\"reachDirR\":" << gait_reach_dir_[1]
          << ",\"sinkChL\":" << gait_sink_ch_[0]
          << ",\"sinkChR\":" << gait_sink_ch_[1]
          << ",\"headroom\":" << gait_headroom_
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
    // minyL/minyR are the per-side world min-y the support-lost and
    // touchdown gates themselves read (wminy above, pre-root pose +
    // root_y_): logged so an abort entry's CLAIM is auditable against
    // the entry's OWN numbers, not just its why-string (the gait
    // harness replays it: support_lost demands the lost foot's min-y
    // >= -1e-3, touchdown the swing foot's min-y < 0).
    auto gates0 = [&]() -> std::string {
        std::ostringstream g;
        g << "{\"dL\":" << gait_depth_[0]
          << ",\"dR\":" << gait_depth_[1]
          << ",\"minyL\":" << wminy[0]
          << ",\"minyR\":" << wminy[1]
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
            // THE WHAT-IF (rung 4), RE-DERIVED FOR THE MEASURED PLANT
            // (window-4 audit): the old form demanded the whole-body
            // centroid to lie inside the would-be stance foot's patch --
            // a rigid-body tipping premise. This root is 1-DOF Y (the
            // prereg's own SCOPE): it cannot tip, the demand has no
            // actuator (measured 0.9867 m vs bar 0.5711 m at rest, still
            // 0.69 m at full strut ROM -- the feet splay 1.87 m and the
            // strut's x-authority is ~1.1 mm/deg: F-STALL by construction).
            // What CAN fail here is GROUNDING: the lift's cross-coupled
            // sink drops the body until non-foot anatomy touches the
            // floor. The gate predicts this lift's sink (the measured
            // cross channel times the lift's full drive) and demands it
            // fit inside the measured headroom with the bearing margin.
            const float err_full = STANCE_BAND_M - wminy[s];
            const float dp_full = std::fabs(gait_lift_ch_[s]) > 1e-12f
                ? err_full / gait_lift_ch_[s] : 0.f;
            const float sink = std::fabs(gait_sink_ch_[s] * dp_full);
            const float sink_bar = gait_headroom_
                                 - GAIT_BEARING_FRAC * GAIT_SINK_M;
            if (sink > sink_bar)
                b << "whatif:sink" << sink << ">" << sink_bar;
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
        // the swing foot's OWN support-patch center, frozen at entry: the
        // stride bar is the prereg's necessity ("land outside the old
        // support patch") measured on this foot's own patch -- the
        // stance-relative reading is measured-unreachable past one stride
        // (the strut's whole z-reach is 0.677 m; the stance-relative bar
        // demands 2x patch once the feet separate: F-STALL at ROM)
        gait_swing_z0_[pick] = fcz[pick];
        std::ostringstream g;
        g << gates0()
          << ",\"whatif\":true,\"patch\":" << gait_patch_r_[1 - pick]
          << ",\"z0\":" << gait_swing_z0_[pick]
          << ",\"reachDir\":" << gait_reach_dir_[pick] << "}";
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
            // THE STRIDE ALONG THE MEASURED BRANCH: the strut's z-channel
            // is nonmonotonic in theta (the 1-deg probe reads +2.6 mm/deg;
            // the +20 deg stride-scale probe and the live ladder show the
            // raising branch swings the foot BACKWARD -- reach_dir, signed
            // from the probes at enable), and the +z branch is unusable
            // (it presses the foot down 15 mm/deg -- more than the clear
            // pin's measured rise can pay). So the strut drives FURTHER
            // INTO ITS LIFTING BRANCH (the direction LIFT established,
            // lift_sign) with the branch-scale gain dcz20, toward the
            // radius bar: the new footfall must land outside the foot's
            // OWN old support patch (|fcz[s] - z0| >= own patch -- the
            // prereg's geometric necessity; the stance-relative reading
            // demands 2x patch of travel once the feet separate, beyond
            // the measured 0.677 m strut reach: F-STALL at ROM).
            const float zrad = fcz[s] - gait_swing_z0_[s];
            const float zrem = gait_patch_r_[s] - std::fabs(zrad);
            if (zrem > 0.f) {
                const float gain = std::fabs(gait_dcz20_hip_[s]);
                const float step = gain > 1e-9f
                    ? std::min(zrem / (gain * STANCE_TAU_S),
                               gait_rate_hip_[s] * dts)
                    : gait_rate_hip_[s] * dts;
                gait_hip_rad_[s] += gait_lift_sign_[s] * step;
                clamp_rom(&gait_hip_rad_[s]);
            }
            if (std::fabs(zrad) >= gait_patch_r_[s]) {
                gait_phase_[s] = GaitPhase::LOAD;
                std::ostringstream g;
                g << gates0()
                  << ",\"z\":" << std::fabs(zrad)
                  << ",\"bar\":" << gait_patch_r_[s]
                  << ",\"z0\":" << gait_swing_z0_[s] << "}";
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

// ═══ C1r: THE CREATURE ANSWERS — implementation (PREREG.md) ════════════

bool MembraneTick::set_reflex(bool on) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (!on) { reflex_off_locked_(); return true; }
    if (!has_scene_ || !ready_.load(std::memory_order_acquire)) return false;
    const size_t nv = base_pos_.size() / 9;
    const bool classified = cell_joint_.size() == cells_.size()
                         && !joint_pins_.empty()   // bindings without pins = OOB
                         && joint_pins_.size() == joint_deg_.size()
                         && vert_bind_idx_.size() == nv * 3
                         && vert_bind_w_.size() == nv * 3;
    reflex_.block.clear();
    std::string blocks;
    // -- BREATHING: a sealed torso cell (argmax v0 -- taste-free: 90.5% of
    //    THIS body) on a classified body (the travel law rebuilds the
    //    surface from base every tick, so the breath is a pure function of
    //    phase and can never accumulate) --
    if (reflex_.breathing) {
        std::string b;
        if (!classified) b = "unclassified";
        else if (!sealed_ || seal_cells_.empty()) b = "unsealed";
        int tor = -1;
        float v0max = 0.f;
        if (b.empty()) {
            for (size_t i = 0; i < seal_cells_.size(); ++i)
                if (seal_cells_[i].v0 > v0max) {
                    v0max = seal_cells_[i].v0;
                    tor = (int)i;
                }
            if (tor < 0) b = "no_torso_cell";
        }
        if (b.empty()) {
            const SealCell& tc = seal_cells_[(size_t)tor];
            // the allometric numbers at THIS body's mass (DERIVATIONS §3-4;
            // both interim values AWAITING ASTRA)
            const double M = (double)mass_kg_;
            const double f_bpm = (double)REFLEX_BREATH_F_COEF
                               * std::pow(M, (double)REFLEX_BREATH_F_EXP);
            reflex_.breath_omega =
                (float)(2.0 * 3.14159265358979 * f_bpm / 60.0);
            reflex_.breath_period_s = (float)(60.0 / f_bpm);
            const double vt_m3 = ((double)REFLEX_BREATH_VT_ML * 1e-6)
                               * std::pow(M, (double)REFLEX_BREATH_VT_EXP);
            reflex_.breath_amp_frac = (float)(vt_m3 / (double)tc.v0);
            // torso skin area on the rest blend (the frozen arm-time
            // reference; external surface only -- cap triangles ride cut
            // blends and are internal walls)
            std::vector<float> rest9(base_pos_);
            apply_travel(rest9, nullptr);
            double area = 0.0;
            const std::vector<uint32_t>& pc = tc.pieces;
            for (size_t k = 0; k + 2 < pc.size(); k += 3) {
                const uint32_t va = pc[k], vb = pc[k + 1], vc = pc[k + 2];
                if (va >= nv || vb >= nv || vc >= nv) continue;
                area += (double)tri_area(rest9, va, vb, vc);
            }
            if (!(area > 1e-6)) b = "torso_area_degenerate";
            else {
                reflex_.breath_mean_disp = (float)(vt_m3 / area);
                // the vert list + raised-cosine y-band profile: zero at
                // both band ends (no seam at the cell boundary), peak at
                // mid-band. Originals only: cut blends ride originals at
                // fixed weights, so moving originals carries the welds.
                reflex_.breath_verts.clear();
                reflex_.breath_w.clear();
                const float inv_h =
                    tc.yhi > tc.ylo ? 1.f / (tc.yhi - tc.ylo) : 0.f;
                for (size_t k = 0; k < pc.size(); ++k) {
                    const uint32_t sl = pc[k];
                    if (sl >= nv) continue;
                    const float u = (rest9[(size_t)sl * 9 + 1] - tc.ylo) * inv_h;
                    float w = 0.f;
                    if (u > 0.f && u < 1.f)
                        w = 0.5f * (1.f - std::cos(2.f * 3.14159265358979f * u));
                    if (w <= 0.f) continue;   // the band ends stay pinned
                    reflex_.breath_verts.push_back(sl);
                    reflex_.breath_w.push_back(w);
                }
                if (reflex_.breath_verts.empty()) b = "breath_verts_empty";
            }
        }
        if (b.empty()) reflex_.breath_cell = tor;
        else {
            reflex_.breath_cell = -1;
            blocks += (blocks.empty() ? "" : "; ")
                    + std::string("breathing:") + b;
        }
    }
    // -- FLINCH: the same-limb drive pins (the gait machine's resolution;
    //    no silent re-derivation: if this body was never gait-resolved,
    //    the refusal NAMES it -- arm gait once (it may disarm immediately;
    //    the resolution persists) to measure the drive pins) --
    if (reflex_.flinch) {
        std::string b;
        if (!classified) b = "unclassified";
        else if (!reflex_resolve_locked_(b)) { /* b named inside */ }
        if (b.empty())
            reflex_.flinch_theta = STANCE_THETA_MAX_DEG * DEG2RAD_F;
        else
            blocks += (blocks.empty() ? "" : "; ")
                    + std::string("flinch:") + b;
    }
    // -- STARTLE: needs the ankle pins on a classified body; the stance
    //    rung is its channel (it stays latent without stance) --
    if (reflex_.startle) {
        std::string b;
        if (!classified) b = "unclassified";
        else if (joint_deg_.size() <= (size_t)std::max(ANKLE_PIN_L, ANKLE_PIN_R))
            b = "no_ankle_pins";
        if (b.empty()) {
            // one rest-sink lean quantum through the stance channel
            // (DERIVATIONS §6), clamped inside the existing ankle cap
            const float S = stance_kp_ > 0.f ? 1.f / stance_kp_
                                             : REFLEX_S_PREREG;
            if (!(S > 1e-4f)) b = "no_stance_channel";
            else reflex_.startle_bias = std::min(
                GAIT_SINK_M / S, STANCE_THETA_MAX_DEG * DEG2RAD_F);
        }
        if (!b.empty())
            blocks += (blocks.empty() ? "" : "; ")
                    + std::string("startle:") + b;
    }
    const bool breath_ok = reflex_.breathing && reflex_.breath_cell >= 0;
    const bool flinch_ok = reflex_.flinch
                        && reflex_.strut_pin[0] >= 0
                        && reflex_.strut_pin[1] >= 0;
    const bool startle_ok = reflex_.startle && reflex_.startle_bias > 0.f;
    if (!breath_ok && !flinch_ok && !startle_ok) {
        reflex_.block = blocks.empty() ? std::string("no_channel") : blocks;
        reflex_.armed = false;
        return false;
    }
    reflex_.block = blocks;   // a partial arm names the channels that refused
    reflex_.armed = true;
    reflex_.prev_p_valid = false;   // the detector seeds on its next tick
    return true;
}

bool MembraneTick::set_reflex_channel(const std::string& name, bool v) {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    if (name == "breathing") {
        reflex_.breathing = v;   // suspend freezes the phase; the pass
        return true;             // stops displacing -> exact rest (M5)
    }
    if (name == "flinch") {
        reflex_.flinch = v;
        if (!v) {
            // let go of any pin WE hold (an armed rung's pin is already
            // being written by its owner -- never stomp it)
            const bool owned = gait_on_ || (stance_on_ && gravity_on_);
            for (int s = 0; s < 2; ++s) {
                const int pin = reflex_.strut_pin[s];
                if (reflex_.pin_held[s] && pin >= 0
                    && (size_t)pin < joint_deg_.size() && !owned)
                    joint_deg_[(size_t)pin] = 0.f;
                reflex_.pin_held[s] = false;
            }
            reflex_.env_l = reflex_.env_r = 0.f;
        }
        return true;
    }
    if (name == "startle") {
        reflex_.startle = v;
        if (!v) reflex_.startle_env = 0.f;
        return true;
    }
    if (name == "pressure_coupling") {
        reflex_.pressure_coupling = v;   // THE NERVE (the negative control)
        return true;
    }
    return false;
}

std::string MembraneTick::reflex_summary_json() const {
    std::lock_guard<std::mutex> lk(seal_mtx_);
    std::ostringstream o;
    o << "{\"reflex_on\":" << (reflex_.armed ? "true" : "false")
      << ",\"breathing\":" << (reflex_.breathing ? "true" : "false")
      << ",\"flinch\":" << (reflex_.flinch ? "true" : "false")
      << ",\"startle\":" << (reflex_.startle ? "true" : "false")
      << ",\"pressure_coupling\":"
      << (reflex_.pressure_coupling ? "true" : "false")
      << ",\"breath_cell\":" << reflex_.breath_cell
      << ",\"breath_period_s\":" << reflex_.breath_period_s
      << ",\"breath_disp_m\":" << reflex_.breath_disp
      << ",\"flinch_pin_l\":" << reflex_.strut_pin[0]
      << ",\"flinch_pin_r\":" << reflex_.strut_pin[1]
      << ",\"flinch_env_l\":" << reflex_.env_l
      << ",\"flinch_env_r\":" << reflex_.env_r
      << ",\"startle_env\":" << reflex_.startle_env
      << ",\"quiet_s\":" << reflex_.quiet_s
      << ",\"block\":\"" << reflex_.block << "\"}";
    return o.str();
}

// THE SAME-LIMB LAW: the flinch drives the gait machine's binding-derived
// strut pins. The resolution is measured, never assumed (the V3a audit):
// when THIS body has one it persists after disarm (gait_off_locked_ keeps
// the pins), so the reflex reuses it -- one source of truth. A body that
// was never gait-resolved refuses BY NAME: no silent re-derivation, no
// duplicated probe code -- arm gait once (it may disarm immediately) to
// measure the drive pins.
bool MembraneTick::reflex_resolve_locked_(std::string& block) {
    if (gait_strut_pin_[0] >= 0 && gait_strut_pin_[1] >= 0
        && (size_t)std::max(gait_strut_pin_[0], gait_strut_pin_[1])
               < joint_deg_.size()) {
        for (int s = 0; s < 2; ++s) {
            reflex_.strut_pin[s] = gait_strut_pin_[s];
            reflex_.lift_sign[s] =
                (gait_lift_sign_[s] >= 0.f) ? 1.f : -1.f;
        }
        return true;
    }
    block = "no_drive_resolution (arm gait once to measure this body's "
            "drive pins; the resolution persists after disarming)";
    return false;
}

void MembraneTick::reflex_detect_locked_(float dt) {
    const float dts = std::min(std::max(dt, 0.f), 0.05f);   // stall guard
    // THE QUIET WINDOW (PREREG gate 1): time since the walker last ran.
    // The walk's own pressures measured 24 MPa median / 583 MPa/s collapse
    // peaks -- a level or rate detector CANNOT separate touch from stride,
    // so suppression is the design, and the 1 s (= 2 tissue taus) window
    // after disarm defers the post-cut collapse.
    if (gait_on_) reflex_.quiet_s = 0.f;
    else if (reflex_.quiet_s < 1e29f) reflex_.quiet_s += dts;
    const bool quiet = reflex_.quiet_s >= REFLEX_QUIET_S;
    // Envelopes decay with the named tissue tau whether or not the servo
    // may answer: the tissue relaxes regardless of gating (the state
    // fields still show that the stimulus was felt -- suppression is not
    // deafness).
    const float decay = std::exp(-(dts > 0.f ? dts : 0.f) / tau_relax_);
    if (reflex_.env_l > 0.f) {
        reflex_.env_l *= decay;
        if (reflex_.env_l < REFLEX_ENV_CUT) reflex_.env_l = 0.f;
    }
    if (reflex_.env_r > 0.f) {
        reflex_.env_r *= decay;
        if (reflex_.env_r < REFLEX_ENV_CUT) reflex_.env_r = 0.f;
    }
    if (reflex_.startle_env > 0.f) {
        reflex_.startle_env *= decay;
        if (reflex_.startle_env < REFLEX_ENV_CUT) reflex_.startle_env = 0.f;
    }
    // -- the flinch's motor: UNOWNED strut pins only. Ownership: gait
    //    writes the drive pins while armed; stance writes the ankles (the
    //    strut pins on this body) while armed under gravity. A flinch
    //    writing an owned pin would be stomped same-tick -- a lying
    //    reflex -- so the gate is absolute (PREREG gate 2).
    const bool owned = gait_on_ || (stance_on_ && gravity_on_);
    for (int s = 0; s < 2; ++s) {
        const float env = (s == 0) ? reflex_.env_l : reflex_.env_r;
        const int pin = reflex_.strut_pin[s];
        if (pin < 0 || (size_t)pin >= joint_deg_.size()) continue;
        if (env > 0.f && !owned) {
            joint_deg_[(size_t)pin] =
                reflex_.lift_sign[s] * reflex_.flinch_theta * env;
            reflex_.pin_held[s] = true;
        } else if (reflex_.pin_held[s]) {
            // the envelope died or a rung took the pin: return OUR write
            // to authored bearing once if still unowned (the flex-0
            // precedent); if owned, the owner writes it -- just let go.
            if (!owned) joint_deg_[(size_t)pin] = 0.f;
            reflex_.pin_held[s] = false;
        }
    }
    // -- the detector membrane: per sealed cell --
    if (seal_cells_.empty()) return;
    // THE WINDOW-9 FIX (deadlock, reproduced on the window-8 binary): the
    // reseed used to be gated by the SIZE check alone, but set_reflex
    // invalidates prev_p_valid at every arm. First arm on a fresh boot:
    // sizes 0 != 4 -> the reseed ran and the detector lived. Any LATER
    // re-arm: sizes already match -> prev_p_valid stayed false -> THIS
    // FUNCTION RETURNED HERE EVERY TICK FOREVER -- prev_p frozen, both
    // triggers dead (measured: a 0 -> 431 kPa step, dP/dt 1.3e8 Pa/s,
    // fired nothing after a re-arm). Seed when the FLAG says so too.
    if (!reflex_.prev_p_valid
        || (int)reflex_.prev_p.size() != (int)seal_cells_.size()
        || (int)reflex_.cell_cx.size() != (int)seal_cells_.size()) {
        // an arm or a cut changed the tree: rebuild centroids and SEED
        // prev_p with the current pressures -- a new cell must never read
        // as a spike
        const size_t nc2 = seal_cells_.size();
        reflex_.prev_p.assign(nc2, 0.f);
        reflex_.cell_cx.assign(nc2, 0.f);
        reflex_.cell_cz.assign(nc2, 0.f);
        const uint32_t nv = (uint32_t)(base_pos_.size() / 9);
        double bsz = 0.;
        for (size_t v = 0; v < base_pos_.size() / 9; ++v)
            bsz += base_pos_[v * 9 + 2];
        reflex_.body_cz = (float)(bsz / (double)std::max<size_t>(1, base_pos_.size() / 9));
        for (size_t i = 0; i < nc2; ++i) {
            reflex_.prev_p[i] = seal_cells_[i].p;
            double sx = 0., sz = 0.;
            size_t sw = 0;
            const std::vector<uint32_t>& pc = seal_cells_[i].pieces;
            for (size_t k = 0; k < pc.size(); ++k) {
                const uint32_t sl = pc[k];
                if (sl >= nv) continue;
                sx += base_pos_[(size_t)sl * 9 + 0];
                sz += base_pos_[(size_t)sl * 9 + 2];
                ++sw;
            }
            if (sw) {
                reflex_.cell_cx[i] = (float)(sx / (double)sw);
                reflex_.cell_cz[i] = (float)(sz / (double)sw);
            }
        }
        reflex_.prev_p_valid = true;
        return;   // seeded this tick: no detection
    }
    // BUG-1 FIX (window-8): the same-limb drive pins are ADOPTED LIVE.
    // Arming before the gait machine's first enable used to freeze the
    // flinch at its named refusal until a manual re-arm, even after gait
    // had resolved (the resolution persists after disarm -- measured:
    // gait on->off left the reflex reader at -1/-1 until a re-arm, which
    // then adopted 17/18). When the resolution appears, take it and clear
    // the flinch component of the block (the gait_enable_block_ law: the
    // refusal must vanish when its cause does).
    if (reflex_.flinch
        && (reflex_.strut_pin[0] < 0 || reflex_.strut_pin[1] < 0)) {
        std::string b;
        if (reflex_resolve_locked_(b)) {
            reflex_.flinch_theta = STANCE_THETA_MAX_DEG * DEG2RAD_F;
            const std::string key = "flinch:";
            const size_t at = reflex_.block.find(key);
            if (at != std::string::npos) {
                const size_t end = reflex_.block.find("; ", at);
                reflex_.block.erase(at,
                    (end == std::string::npos)
                        ? reflex_.block.size() - at
                        : end - at + 2);
                if (reflex_.block.rfind("; ", 0) == 0)
                    reflex_.block.erase(0, 2);
            }
        }
    }
    // THE STARTLE'S COROLLARY-DISCHARGE GATE: the startle's channel IS the
    // stance servo, so a rung still converging after its own arm is the
    // creature's OWN motion -- measured on window-8's binary: the stance
    // arm transient fired the startle once (tick 3273) with no stimulus.
    // Self-generated transients do not startle; require the rung settled
    // for one quiet window.
    if (stance_on_ && gravity_on_) reflex_.stance_s += dts;
    else reflex_.stance_s = 0.f;
    // ─── AN2: THE PATCH TRIGGER (the LOCAL sensory layer) ───────────
    // When the patch layer is armed it SUPERSEDES the scalar cell-pressure
    // trigger (M3: a scalar cannot locate a touch inside a cell). The
    // nerve gate (pressure_coupling) belongs to the SCALAR path only;
    // each patch path is gated by its OWN connected flag (a cut path
    // delivers nothing -- prereg P9). The startle stays scalar: it is
    // the whole-body transient detector by design.
    if (patches_armed_ && reflex_.flinch && quiet
        && reflex_.strut_pin[0] >= 0 && reflex_.strut_pin[1] >= 0) {
        for (const SensorPatch& p : patches_) {
            if (!p.connected || p.last_fire_tick != ticks_) continue;
            // two-neuron arc, local: stimulus PATCH -> that side's limb
            if (p.side == 0) reflex_.env_l = 1.f;
            else             reflex_.env_r = 1.f;
            reflex_.last_cell = p.cell;   // the locality: the patch's
            reflex_.last_tick = ticks_;   // owning segment cell
        }
    }
    const bool flinch_armed = !patches_armed_ && reflex_.flinch
        && reflex_.pressure_coupling
        && quiet && reflex_.strut_pin[0] >= 0 && reflex_.strut_pin[1] >= 0;
    const bool startle_armed = reflex_.startle && reflex_.pressure_coupling
        && quiet && reflex_.stance_s >= REFLEX_QUIET_S
        && reflex_.startle_bias > 0.f;
    for (size_t i = 0; i < seal_cells_.size(); ++i) {
        const SealCell& c = seal_cells_[i];
        const float p = c.p;
        const float pp = reflex_.prev_p[i];
        if (!c.degenerate && dts > 0.f
            && (flinch_armed || startle_armed)) {
            // RISING level crossing only: a hit LOADS the cell; a release
            // (the post-walk collapse, a lifted touch) never fires
            if (flinch_armed && pp < REFLEX_FLINCH_PA && p >= REFLEX_FLINCH_PA) {
                // two-neuron arc: stimulus cell -> touched side's limb.
                // The side is the stimulus's LOCALITY: the live touch
                // point's x when a press is held, else the cell's rest
                // centroid (the house L/R convention: x >= 0 = L).
                const float sx = touch_active_ ? touch_pt_[0]
                                               : reflex_.cell_cx[i];
                if (sx >= 0.f) reflex_.env_l = 1.f;   // the attack is a
                else           reflex_.env_r = 1.f;   // reflex: instant
                reflex_.last_cell = (int)i;
                reflex_.last_tick = ticks_;
            }
            // TRANSIENT: the INCREASE rate only (a release does not startle);
            // envelope-gated refractory (re-trigger below 10% envelope)
            if (startle_armed && reflex_.startle_env < 0.1f) {
                const float dpdt = (p - pp) / dts;
                if (dpdt > REFLEX_STARTLE_DPDPT) {
                    const float sz = touch_active_ ? touch_pt_[2]
                                                   : reflex_.cell_cz[i];
                    reflex_.startle_dir =
                        (sz >= reflex_.body_cz) ? -1.f : 1.f;
                    reflex_.startle_env = 1.f;
                    reflex_.startle_last_tick = ticks_;
                }
            }
        }
        reflex_.prev_p[i] = p;   // track the truth even through a cut:
                                 // reconnecting the nerve must never see
                                 // a stale rising edge
    }
}

void MembraneTick::reflex_compose_locked_() {
    // THE STARTLE rides the stance servo (PREREG R3): a decaying lean bias
    // composed over stance_th_ exactly the way the gait machine composes
    // its strut component. Active ONLY while the stance rung is armed and
    // the walker is not; the TOTAL stays inside the existing ankle cap.
    if (!reflex_.startle || !reflex_.pressure_coupling) return;
    if (!stance_on_ || !gravity_on_ || gait_on_) return;
    if (reflex_.startle_env <= 0.f || reflex_.startle_bias <= 0.f) return;
    if (joint_deg_.size() <= (size_t)std::max(ANKLE_PIN_L, ANKLE_PIN_R))
        return;
    const float th_max = STANCE_THETA_MAX_DEG * DEG2RAD_F;
    const float a = reflex_.startle_dir * reflex_.startle_bias
                  * reflex_.startle_env;
    const float total = std::min(std::max(stance_th_ + a, -th_max), th_max);
    joint_deg_[ANKLE_PIN_L] = total;
    joint_deg_[ANKLE_PIN_R] = total;
}

void MembraneTick::reflex_breath_locked_(std::vector<float>& verts9,
                                         float dt) {
    // AUTONOMIC BREATHING (PREREG R1): the torso cell's volume TARGET
    // oscillates; the surface follows along authored normals through the
    // raised-cosine band profile. The displacement is a PURE function of
    // (phase, vertex) -- the travel law rebuilds the surface from base
    // every tick, so suspending the oscillator restores the measured
    // zero-motion reference EXACTLY (the negative control).
    if (!reflex_.breathing || reflex_.breath_cell < 0
        || reflex_.breath_verts.empty()) return;
    const float dts = std::min(std::max(dt, 0.f), 0.05f);   // stall guard
    reflex_.breath_phase += reflex_.breath_omega * dts;
    // wrap at 2pi: a multi-day phase would eat float precision (sin is
    // periodic; the wrap keeps the oscillator exact at any uptime)
    if (reflex_.breath_phase > 2.f * 3.14159265358979f)
        reflex_.breath_phase =
            std::fmod(reflex_.breath_phase, 2.f * 3.14159265358979f);
    const float s = std::sin(reflex_.breath_phase);
    reflex_.breath_disp = reflex_.breath_mean_disp * s;   // live report
    if (s == 0.f) return;   // the zero-crossing is exact rest
    for (size_t i = 0; i < reflex_.breath_verts.size(); ++i) {
        const size_t v = (size_t)reflex_.breath_verts[i];
        const float d = reflex_.breath_mean_disp * reflex_.breath_w[i] * s;
        verts9[v * 9 + 0] += base_pos_[v * 9 + 3] * d;
        verts9[v * 9 + 1] += base_pos_[v * 9 + 4] * d;
        verts9[v * 9 + 2] += base_pos_[v * 9 + 5] * d;
    }
}

void MembraneTick::reflex_off_locked_() {
    // Deterministic off (the flex-0 precedent): envelopes to zero, phase
    // to zero, any pin WE hold back to authored bearing -- no hidden
    // decay, no stale integrator.
    const bool owned = gait_on_ || (stance_on_ && gravity_on_);
    for (int s = 0; s < 2; ++s) {
        const int pin = reflex_.strut_pin[s];
        if (reflex_.pin_held[s] && pin >= 0
            && (size_t)pin < joint_deg_.size() && !owned)
            joint_deg_[(size_t)pin] = 0.f;
        reflex_.pin_held[s] = false;
    }
    reflex_.armed = false;
    reflex_.env_l = reflex_.env_r = 0.f;
    reflex_.startle_env = 0.f;
    reflex_.breath_phase = 0.f;
    reflex_.breath_disp = 0.f;
    reflex_.prev_p_valid = false;
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
    // ts_us / ts_ms: the engine's OWN monotonic clock (steady; on Windows
    // its epoch is machine boot), read ONCE under the SAME lock pass as
    // every field below, printed as INTEGERS. Integers, not a float: a
    // double through ostringstream's default 6 significant digits
    // quantizes to 100 ms at a day's clock magnitude -- the whole poll
    // interval -- which false-fired the gait harness's per-poll
    // F-TELEPORT audit at 1.24x on an up-88485-s host (window-6
    // evidence: both stamps exact multiples of 100; the true window was
    // ~123.8 ms). A poller divides a pose delta by the exact server
    // window the machine had to move in; differences are meaningful,
    // the epoch base is not.
    const auto ts_now = std::chrono::steady_clock::now().time_since_epoch();
    o << "{\"ts_us\":"
      << std::chrono::duration_cast<std::chrono::microseconds>(ts_now).count()
      << ",\"ts_ms\":"
      << std::chrono::duration_cast<std::chrono::milliseconds>(ts_now).count()
      << ",\"ticks\":" << ticks_
      << ",\"enabled\":" << (enabled_ ? "true" : "false")
      << ",\"reflex_cell_count\":" << cells_.size()
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
      // C1r: the reflex fields -- the state the page could read (default
      // OFF on boot; every reaction's envelope/phase is here so the HUD
      // can show WHAT the creature felt, not just that it moved).
      << ",\"reflex_on\":" << (reflex_.armed ? "true" : "false")
      << ",\"reflex_breathing\":" << (reflex_.breathing ? "true" : "false")
      << ",\"reflex_breath_cell\":" << reflex_.breath_cell
      << ",\"reflex_breath_period_s\":" << reflex_.breath_period_s
      << ",\"reflex_breath_amp_frac\":" << reflex_.breath_amp_frac
      << ",\"reflex_breath_disp_m\":" << reflex_.breath_disp
      << ",\"reflex_breath_phase_deg\":"
      << reflex_.breath_phase * 57.29577951308232
      << ",\"reflex_flinch\":" << (reflex_.flinch ? "true" : "false")
      << ",\"reflex_flinch_pin_l\":" << reflex_.strut_pin[0]
      << ",\"reflex_flinch_pin_r\":" << reflex_.strut_pin[1]
      << ",\"reflex_flinch_env_l\":" << reflex_.env_l
      << ",\"reflex_flinch_env_r\":" << reflex_.env_r
      << ",\"reflex_flinch_last_cell\":" << reflex_.last_cell
      << ",\"reflex_flinch_last_tick\":" << reflex_.last_tick
      << ",\"reflex_startle\":" << (reflex_.startle ? "true" : "false")
      << ",\"reflex_startle_env\":" << reflex_.startle_env
      << ",\"reflex_startle_bias_deg\":"
      << reflex_.startle_bias * 57.29577951308232
      << ",\"reflex_startle_last_tick\":" << reflex_.startle_last_tick
      << ",\"reflex_p_coupling\":"
      << (reflex_.pressure_coupling ? "true" : "false")
      << ",\"reflex_quiet_s\":" << reflex_.quiet_s
      << ",\"reflex_block\":\"" << reflex_.block << "\""
      // AN2: the one-limb partition + the sensor patches. IDs: segment
      // names -> cell indices (the same indices the cells[] array
      // reports), patch names -> owning cell -> response pins. Every
      // event row carries ticks_ and ts_us from the engine's own clock
      // (acceptance 9: one ID space, one clock).
      << ",\"limb_done\":" << (limb_done_ ? "true" : "false")
      << ",\"limb_side\":\"" << limb_side_ << "\""
      << ",\"limb_segs\":[";
      for (size_t i = 0; i < limb_segs_.size(); ++i) {
          const LimbSeg& s = limb_segs_[i];
          if (i) o << ",";
          o << "{\"name\":\"" << s.name << "\",\"cell\":" << s.cell
            << ",\"v0\":" << jf(s.v0)
            << ",\"pieces\":" << s.pieces
            << ",\"seed_agree\":" << s.seed_agree
            << ",\"seed_n\":" << s.seed_total << "}";
      }
      o << "]"
      << ",\"patches\":" << patch_json_locked()
      << ",\"patch_events\":[";
      for (size_t i = 0; i < patch_event_log_.size(); ++i) {
          if (i) o << ",";
          o << patch_event_log_[i];
      }
      o << "]"
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





