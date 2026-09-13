// membrane_tick.hpp -- THE MEMBRANE TICK (Appliance 1, prereg 4c111341).
#pragma once

#include <array>
#include <atomic>
#include <cstdint>
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
    void step(std::vector<float>& verts9);

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

    // THE SEAL (Appliance 4): mitosis — one intent divides the creature
    // into two sealed hydraulic cells at plane y. v2 is the CUT-AND-WELD:
    // straddling triangles split at the plane, the cross-section loops
    // chain from the cut segments, and each loop is capped twice (both
    // windings) so both daughters' boundaries are closed surfaces.
    // Volume by divergence, pressure by dP = -dV/(kappa*V0),
    // kappa = water at 25 C.
    bool seal(float y);

    bool   enabled_ = true;
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
    std::vector<uint8_t> vert_bind_idx_;       // 3 pin indices per vertex
    std::vector<float>   vert_bind_w_;         // 3 normalized weights per vertex
    std::vector<uint8_t> vert_joint_;          // dominant pin per vertex
    std::vector<std::array<float, 3>> joint_pins_;  // the 28 measured pins
    std::vector<float>  joint_deg_;            // pose per pin (radians)
    std::vector<float>  joint_force_;          // standing press per pin, N
    // THE SEAL v2 (cut-and-weld): the wall is the welded cross-section
    // itself. Cut slots ride surface edges at fixed t, so the weld holds
    // while poses move the surface — the daughters' boundaries stay
    // closed and their divergence sums stay true volumes.
    struct SealSlot { uint32_t a, b; float t; };   // cut point on edge (a,b)
    bool  sealed_ = false;
    float seal_y_ = 0.f, kappa_ = 4.6e-10f;
    float v0_lower_ = 0.f, v0_upper_ = 0.f;    // rest volumes at seal time
    float vol_whole0_ = 0.f;                   // whole divergence vol at seal
    float vol_lower_ = 0.f, vol_upper_ = 0.f;  // live daughter volumes
    float vol_whole_ = 0.f;                    // live posed whole volume
    float conserve_pct_ = 0.f;                 // (Vl+Vu-Vw)/Vw * 100
    float p_lower_ = 0.f, p_upper_ = 0.f;      // hydraulic gauge pressure
    uint32_t seal_nv_ = 0;                     // original vertex count
    int seal_split_ = 0, seal_cuts_ = 0, seal_loops_ = 0, seal_caps_ = 0;
    std::vector<SealSlot> cut_src_;            // slot nv+k -> edge (a,b,t)
    std::vector<uint32_t> seal_lower_, seal_upper_;  // 3 slots per piece
    std::vector<float>  cut_pos_;              // per-frame posed cut positions
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
