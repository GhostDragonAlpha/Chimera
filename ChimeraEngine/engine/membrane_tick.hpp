// membrane_tick.hpp -- THE MEMBRANE TICK (Appliance 1, prereg 4c111341).
#pragma once

#include <array>
#include <atomic>
#include <cstdint>
#include <functional>
#include <mutex>
#include <string>
#include <string>
#include <vector>

class MembraneTick {
public:
    void init(uint32_t tris, const std::vector<uint32_t>& indices,
              const std::vector<float>& verts9);

    // POST /tick_intent {"force_n": F, "foot": "L"|"R"} -- a standing
    // press that persists until replaced. F <= 0 or unknown foot -> refused.
    bool intent(float force_n, const std::string& foot);

    void clear_intent();

    // One tick: advance state, tint the vertex colors in place.
    // verts9 is the host mirror posted via update_mesh.
    void step(std::vector<float>& verts9, float dt);

    std::string state_json() const;

    // TRAVEL (Appliance 2): flex the feet about their ankle pivots.
    // Poses are intents; flex 0 restores the authored base exactly.
    bool flex(float deg_l, float deg_r);

    // THE LEG (Appliance 3): a hinged membrane chain. The rig is posted
    // by the authoring script, one line per part:
    //   name|start|count|pivot_x|pivot_y|pivot_z|parent_index
    // parents come before children; parent -1 = root. Angles per joint
    // are set by pose(joint, deg); FK composes parents down the chain.
    bool load_rig(const std::string& config);
    bool pose(const std::string& joint, float deg);
    size_t rig_parts() const { return rig_.size(); }

    // CA CLASSIFICATION (Appliance 4): the existing object's triangles
    // are typed by joint and bound to the 28 measured pins.
    bool load_classify(const std::string& body);    // [u32 n][u8 * n]
    bool load_joint_pins(const std::string& body);  // [u32 n][f32 x3 * n]
    bool load_vertbind(const std::string& body);    // [u32 n][u8 * n]
    bool pose_index(int idx, float deg);
    bool intent_joint(int idx, float force_n);

    // THE SEAL / MITOSIS (Appliance 4, recursive): POST /tick_seal
    // {"y": Y, "cell": k} cuts sealed cell k with plane Y into two sealed
    // cells (cell 0 = the whole creature before any cut). v2 is the
    // CUT-AND-WELD: straddling pieces split at the plane, cross-section
    // loops chain from the cut segments, each loop is capped twice (both
    // windings, lower reversed per the edge-orientation law). Inserted
    // points are convex blends over original vertices, so every point
    // rides the posed surface at fixed weights — repeated cuts grow the
    // body-part tree (the growth law). Volume by divergence, pressure by
    // dP = -dV/(kappa*V0), kappa = water at 25 C.
    bool seal(float y, int cell);

    // THE COMPONENT SPLIT (the L/R separation): a cell made of several
    // disjoint closed surfaces (left+right feet after the ankle band cut)
    // divides into one cell per connected component — flood-fill the
    // pieces through shared slots. Refused by name for a connected cell.
    bool split(int cell);

    // THE MOVEMENT LAW, first bar -- THE FALL (prereg appended to
    // SEAL_PREREGISTRATION.md): the body has mass; gravity pulls it;
    // the floor y=0 holds what presses it through a penalty spring at
    // the body's lowest vertex. One rigid root DOF -- volumes, normals,
    // poses, touches and seals are translation-invariant, so none of
    // that arithmetic changes. Off = authored rest, exactly. The lead
    // wires POST /tick_gravity -> set_gravity at the build window.
    bool set_gravity(bool on);

    // R3 TOUCH (prereg 0935695e): press AT a world point (the camera-ray
    // hit), Gaussian falloff around it, along the POSED skin normals.
    // The pick callback runs under the tick lock so the geometry it reads
    // is exactly the geometry the next tick deforms.
    bool touch_press(float u, float v, float force_n,
                     const std::function<bool(float[3])>& pick_fn,
                     std::string& err, float hit_out[3] = nullptr);
    bool touch_clear();
    const std::vector<uint32_t>& tri_verts() const { return tri_verts_; }

    // THE WEB KERNEL (prereg b88d6657): the browser renders the world
    // from streamed STATE. Topology is one-time; the posed buffer is the
    // per-pull payload. Both serialize UNDER the tick lock so a player's
    // pull can never tear a mid-step surface. touch_press_at presses a
    // WORLD point the browser found by its own ray-cast.
    void export_topology(std::vector<uint8_t>& out);
    void export_verts(const std::vector<float>& verts9, std::vector<uint8_t>& out);
    bool touch_press_at(const float hit[3], float force_n);

    // A1's finding (R4 run): a hit 0.355 m from the skin answered
    // ok:true with ZERO effect — a silent lie. Truthfulness helper:
    // squared distance from a world point to the nearest authored
    // vertex (posed approximated by base; the caller refuses beyond
    // the press Gaussian's reach).
    float point_skin_dist2(const float p[3]) const;

    bool   enabled_ = true;
    bool   gravity_on_ = false;   // THE FALL: initialized false; the lead
                                  // flips true after the fall bar passes
    uint64_t ticks_ = 0;
    float  force_l_ = 0.0f, force_r_ = 0.0f;   // active presses, newtons
    float  yield_pa_ = 15.0e6f;                // mat.skin, Yamada 1970
    float  flex_l_ = 0.0f, flex_r_ = 0.0f;     // radians

private:
    struct Cell { float load = 0.f, damage = 0.f; bool failed = false; };
    struct RigPart {
        std::string joint;
        uint32_t start = 0, count = 0;
        std::array<float, 3> pivot = {0.f, 0.f, 0.f};
        int parent = -1;
    };
    std::vector<Cell>   cells_;
    std::vector<std::vector<uint32_t>> neighbors_;
    std::vector<float>  capacity_;             // newtons per cell
    std::vector<uint8_t> foot_;                // 0 = left cluster, 1 = right
    std::vector<float>  base_color_;           // 3 per vertex
    std::vector<float>  base_pos_;             // 3 per vertex (authored rest)
    std::vector<uint32_t> tri_verts_;          // 3 indices per cell
    std::array<std::array<float, 3>, 2> pivot_ = {};   // ankle pivots [L, R]
    std::vector<RigPart> rig_;                 // the chain (Appliance 3)
    std::vector<float>  rig_angle_;            // radians per part
    std::vector<uint8_t> cell_joint_;          // per-triangle CA type (pin idx)
    std::vector<std::vector<uint32_t>> joint_verts_;  // per-pin pressed region
    std::vector<std::array<float, 3>> joint_cent_;    // per-pin region centroid
    std::vector<uint8_t> vert_bind_idx_;       // 3 pin indices per vertex
    std::vector<float>   vert_bind_w_;         // 3 normalized weights per vertex
    std::vector<uint8_t> vert_joint_;          // dominant pin per vertex
    std::vector<std::array<float, 3>> joint_pins_;  // the 28 measured pins
    std::vector<float>  joint_deg_;            // pose per pin (radians)
    std::vector<float>  joint_force_;          // standing press per pin, N
    // THE SEAL v2 / MITOSIS (cut-and-weld, recursive). The wall is the
    // welded cross-section itself; cut points are convex blends over
    // original vertices (merged, <= 8 entries), so the weld holds at any
    // recursion depth while poses move the surface.
    struct CutBlend {
        uint8_t n = 0;
        std::array<uint32_t, 8> v = {};
        std::array<float, 8> w = {};
    };
    struct SealCell {
        std::vector<uint32_t> pieces;   // 3 global slot ids per piece
        float v0 = 0.f, vol = 0.f, p = 0.f;
        int caps = 0;
        float ylo = 0.f, yhi = 0.f;     // rest y-range (refusal checks)
    };
    bool  sealed_ = false;              // any cell exists
    float seal_y_ = 0.f, kappa_ = 4.6e-10f;
    float vol_whole0_ = 0.f;                   // whole divergence vol at seal
    float vol_whole_ = 0.f;                    // live posed whole volume
    float conserve_pct_ = 0.f;                 // (sum cells - Vw)/Vw * 100
    uint32_t seal_nv_ = 0;                     // original vertex count
    int seal_split_ = 0, seal_cuts_ = 0, seal_loops_ = 0, seal_caps_ = 0;  // last cut
    std::vector<CutBlend> cut_src_;     // global slot nv+k -> blend
    std::vector<SealCell> seal_cells_;
    std::vector<float>  cut_pos_;       // per-frame posed cut positions
    // recursion mutates the seal state while the render thread reads it
    // (v2 was write-once and safe; mitosis is not). seal() swaps members
    // under this lock; step() try_locks and skips a frame's volume
    // update rather than blocking the render loop. init() and the tick
    // loaders take the SAME lock: the boot-restore thread can re-init
    // while the render thread travels the old bindings (the AV race).
    mutable std::mutex seal_mtx_;
    void  load_lock_() { seal_mtx_.lock(); }        // RAII at call sites
    void  load_unlock_() { seal_mtx_.unlock(); }
    // THE HYDRAULIC PRESS (appliance 3): pressed cells dimple by the
    // linear-membrane law delta = F/(4 pi sigma), Gaussian falloff r0;
    // the divergence sums read the dimpled geometry, so the kappa law
    // answers. Release restores the surface exactly.
    float sigma_n_ = 4000.f;    // skin working tension, N/m (Yamada ULS
                                // 8 MPa x 1.5 mm / safety 3)
    float press_r0_ = 0.03f;    // falloff radius, m
    float tau_relax_ = 0.5f;    // soft-tissue stress relaxation, s (named
                                // at Yamada skin-creep scale; HR bar tests it)
    float dimple_m_ = 0.f;      // deepest active dimple (state report)
    bool  normals_displaced_ = false;  // dimpled normals need restore
    // THE HYDRAULIC RETURN: persistent offset per vertex. Active presses
    // set offsets to the forced Gaussian; released offsets decay
    // exp(-dt/tau) until the 0.1 mm cutoff clears them (deterministic
    // rest preserved).
    std::vector<float> press_off_;             // nv offsets, aligned to verts
    bool  press_field_ = false;
    // THE FALL (one rigid DOF along Y). Derived, not tuned: mass from
    // the sealed cells (13.8245 m^3 x water = 13,824.5 kg); rest sink
    // s* = m g/k <= 1 cm -> k = 1.3562e7 N/m; zeta = 0.7 -> c =
    // 2 zeta sqrt(k m) = 6.062e5 N s/m; omega_n = sqrt(k/m) = 31.3
    // rad/s (settle ~0.18 s). Clamps: |root_y| <= 3 m, |vy| <= 30 m/s.
    float mass_kg_  = 13824.5f;
    float k_ground_ = 1.3562e7f;               // N/m  (= m g / 0.01)
    float c_ground_ = 6.062e5f;                // N s/m
    float root_y_ = 0.f, root_vy_ = 0.f;       // the state; 0 = authored rest
    float g_contact_n_ = 0.f;                  // last contact force (report)
    // THE TOUCH: a world-space press point + force (set via touch_press
    // under the tick lock; consumed by step)
    bool  touch_active_ = false;
    float touch_pt_[3] = {0.f, 0.f, 0.f};
    float touch_f_ = 0.f;                // press_off_ has entries
    bool  has_scene_ = false;
    float dirty_ = 0.f;                        // tint changed -> needs upload
    std::atomic<bool> ready_{false};           // committed only after init
    uint32_t verts_expected() const { return (uint32_t)(base_pos_.size() / 9); }
    void  apply_flex(std::vector<float>& verts9);
    void  apply_chain(std::vector<float>& verts9);
    // classified smooth travel; deg == nullptr poses all angles at 0
    // (used by seal() so v0 is measured on the SAME rest-blend floats
    // the per-frame volume uses — rest dV is exactly 0, not float-noise)
    void  apply_travel(std::vector<float>& verts9,
                       const std::vector<float>* deg) const;
};
