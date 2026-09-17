// membrane_tick.hpp -- THE MEMBRANE TICK (Appliance 1, prereg 4c111341).
#pragma once

#include <array>
#include "joint_binding.hpp"
#include <atomic>
#include <cstdint>
#include <deque>
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
    bool load_body_binding(const std::string& body); // admitted JNT3, before seals/controllers
    bool body_active() const { return body_active_.load(std::memory_order_acquire); }
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
    // outcome (optional): 0 = executed, 1 = already satisfied (the
    // idempotent skip; nothing published, nothing refused). Refusal is
    // still `false` (the H8 degenerate-split guard keeps its category).
    static constexpr int SEAL_CUT = 0, SEAL_ALREADY = 1;
    bool seal(float y, int cell, int* outcome = nullptr);

    // THE SEAL-TREE SNAPSHOT (restore idempotency, R-restore-doctor):
    // the mitosis tree is fully determined by the mesh + the cut blends +
    // the per-cell piece lists, so it round-trips as bytes. Loading is
    // ALL-OR-NOTHING and self-validating: the vertex count must match the
    // loaded mesh and every cell's rest volume is RECOMPUTED from its
    // pieces and compared against the stored v0 -- a stale blob (any mesh
    // change) refuses without mutating anything, and the caller falls
    // back to the intent history (every entry then re-executes or skips
    // as already-satisfied, exactly as before this blob existed).
    bool load_seal_state(const std::string& body);
    void export_seal_state(std::vector<uint8_t>& out);

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

    // F1 STANCE (the balance rung; prereg appended to
    // SEAL_PREREGISTRATION.md): the body counters its own lean by
    // posing BOTH ankles (pins 17/18). set_stance(true) derives
    // everything from THIS engine's own travel arithmetic: the support
    // set (the rest blend's min-y band, FROZEN -- a per-frame
    // re-selected band chases the ankle pitch and self-cancels the
    // channel: measured |S| 0.056 m/rad re-selected vs 0.283 frozen),
    // the rest lean reference (the tail makes absolute rest lean
    // nonzero: lean_ref = (-0.0002, -0.8366) m), and the gain
    // k_p = 1/(|S| * tau), tau = 1 s (the 1 s nulling bar). The servo
    // runs in step() only while gravity is on (balance exists only in
    // a gravity field); OFF zeroes the ankles -- authored rest,
    // exactly (the flex-0 precedent). Refused honestly without
    // classification. The lead wires POST /tick_stance at the window.
    bool set_stance(bool on);

    // G1 GAIT CHECKPOINT MACHINE (the robot-stack rung 2; prereg appended
    // to SEAL_PREREGISTRATION.md): per-leg STANCE -> LIFT -> REACH -> LOAD
    // (+ RECOVER), every transition gated by a MEASURED number -- per-side
    // foot contact depth against the floor plane, sealed-cell pressures,
    // lean and support geometry read from the posed surface -- NEVER a
    // timer; dt enters only through the rate caps and the servo
    // integration. Actuates ONLY the hip/knee pins 13-16 through
    // joint_deg_, rate-capped (no teleporting); the ankles stay F1-owned:
    // the G1 block runs AFTER the stance block in step() and composes
    // over it. Requires gravity + stance ON (rung stacking),
    // classification, leg pins, and a sealed feet cell; refuses honestly
    // otherwise. THE FALSIFIER: cut the machine mid-stride and every
    // controller-driven motion stops within one tick -- it must NEVER
    // glide. The lead wires POST /tick_gait -> set_gait at the window.
    bool set_gait(bool on);

    // ─── C1r: THE CREATURE ANSWERS (three reflexes; prereg in
    // ─── docs/evidence/agent_fleet/SHIP/C1_CREATURE_ANSWERS/PREREG.md,
    // ─── derivations in the same directory). DEFAULT OFF ON BOOT; armed
    // ─── ONLY by route (POST /tick_reflex, lead-wired at window #8).
    // ─── Every reaction is PHYSICS through the existing machinery -- a
    // ─── flinch IS a servo pose, breathing IS a volume change -- never a
    // ─── keyframed animation:
    //   BREATHING  the torso cell's volume TARGET oscillates (Stahl
    //              respiratory allometry at mass_kg_: 4.485 breaths/min,
    //              tidal volume 0.752% of the measured torso v0), applied
    //              as THE ABSOLUTE LAST surface pass (after the FALL
    //              law's root read) so the kappa pressure law, the
    //              conservation export, every gait/stance measurement AND
    //              the root home are structurally blind to it. A
    //              water-stiff sealed cell cannot breathe: the honest
    //              tidal swell, if the kappa law saw it, would answer
    //              14.9 MPa = 99% of the skin yield every breath
    //              (DERIVATIONS.md §4) -- so the breath lives in the
    //              compliant thorax (volume target), not the coelom
    //              (pressure).
    //   FLINCH     a sealed cell's pressure crossing 1e5 Pa on a RISING
    //              edge flexes the touched side's binding-derived strut
    //              pin (the gait machine's own V3a net-weight pins, same-
    //              limb law) by <= STANCE_THETA_MAX_DEG toward its
    //              measured raising branch, decaying with tau_relax_.
    //              Two-neuron shape: stimulus cell -> response limb.
    //   STARTLE    a pressure TRANSIENT (max(0, dP/dt) > 1e6 Pa/s) biases
    //              the stance servo by one rest-sink lean quantum
    //              (GAIT_SINK_M / S, ~2.03 deg against the 5 deg cap),
    //              composed over stance_th_ exactly the way gait composes
    //              its strut component. The whole-body reflex.
    // INTERACTION LAWS (PREREG, measured-mandatory): gait_on suppresses
    //   flinch/startle + a 1 s quiet window after disarm (the walk's own
    //   pressures measured 24 MPa median -- 240x the flinch threshold;
    //   a level/rate detector CANNOT separate touch from stride, so the
    //   gate IS the design); stance-under-load suppresses the flinch (its
    //   response limb IS an ankle pin on this body) and is the startle's
    //   only channel; "pressure_coupling" is the NERVE -- route-cuttable,
    //   the battery's negative control (a reflex that fires without its
    //   stimulus is an animation); a mesh swap clears everything (the C1
    //   stale-index crash class); deterministic off (the flex-0
    //   precedent). Interim constants AWAITING ASTRA (see PREREG).
    bool set_reflex(bool on);

    // Channel switch for an armed reflex set (or a preference for the
    // next arm): "breathing", "flinch", "startle", "pressure_coupling".
    // Unknown name -> false. "pressure_coupling":false is THE NERVE CUT:
    // the flinch/startle detectors see nothing; breathing (not
    // pressure-driven) continues.
    bool set_reflex_channel(const std::string& name, bool v);

    // Compact reflex summary for the route response (state_json carries
    // the full reflex_* field set the page could read).
    std::string reflex_summary_json() const;

    // ─── AN2: THE ONE-LIMB PARTITION (prereg:
    // ─── docs/evidence/agent_fleet/SHIP/ONE_LIMB/PREREG.md, membranes
    // ─── M1/M2) ─────────────────────────────────────────────────────────
    // Repartitions ONE articulated limb (side "L" or "R") from skeleton
    // CONNECTIVITY, not horizontal bands and not Euclidean nearest-pin
    // labels: the pin chain (hip→knee→ankle) is DERIVED from mesh-edge
    // adjacency of dominant-pin vertex labels and must come out exactly
    // as the chain, or the route refuses BY NAME (prereg P1). The band
    // components of that leg are split, merged into one leg cell (the
    // interior band walls removed: both windings present in the merged
    // set), then sealed with TWO OBLIQUE plane cuts through the knee and
    // ankle pins, normals along the bone axes — the existing cut-and-weld
    // machinery generalized from the horizontal plane to an oriented one
    // (seal_cut_core_). Each new wall is ONE physical septum (shared
    // welded slots, opposite winding per neighbor's divergence sum); the
    // pre-existing hip wall stays the ONE septum to the torso. Ownership
    // is FIXED AT BUILD (piece lists are immutable afterwards; nothing
    // reclassifies per frame). Refuses while any rung is armed (anatomy
    // surgery at authored rest) and on any replay of an executed
    // partition ("already"). The full derivation + validation report
    // (closure, orientation, positive volumes, disjoint interiors,
    // whole-coverage, mass table, genus, seed-vs-wall agreement) is
    // returned and re-exported by limb_report_json().
    bool limb_partition(const std::string& side, std::string& report,
                        bool* already = nullptr);
    std::string limb_report_json() const;

    // THE LIMB REGISTRY SNAPSHOT (persistence, acceptance 10): the
    // segment registry + patch parameters round-trip as a versioned,
    // self-validating binary blob (magic 'LMB1'): on load every segment's
    // cell must exist with the stored piece count and a matching rest
    // volume (1e-3 relative); patch vertex sets are REBUILT by the same
    // deterministic radius rule. A stale blob refuses with NOTHING
    // changed (the seal-state law: a mesh change makes the registry
    // stale, and the staleness is visible, not silent).
    bool limb_restore(const std::string& body);
    void export_limb_state(std::vector<uint8_t>& out);
    bool limb_done() const { return limb_done_; }

    // ─── AN2: SENSOR PATCHES (prereg membrane M3) ───────────────────────
    // Scalar cell pressure cannot locate a touch inside a cell. A patch
    // is a FINITE receptor region of skin: raw = the skin's own local
    // indentation field (press_off_) over the patch's vertices — the
    // controller never sees the touch point, the force, or any object
    // identity — 1st-order filtered (tau 10 ms = 3 ticks), saturating
    // (sat*tanh at sat = press_r0_), carried over a path with an explicit
    // FINITE transport delay (|centroid − spine_lower| / 70 m/s, the
    // A-beta afferent assertion), delivered by a timestamped line. A path
    // CUT is a real state: nothing delivers, the cut carries a tick and
    // engine timestamp, reconnection cannot synthesize a stale spike
    // (the line drains on cut). Patch events trigger the EXISTING flinch
    // arc (same pins, same gates) as the LOCAL sensory layer; the scalar
    // cell-pressure trigger stays for the un-patched configuration.
    // DEFAULT OFF ON BOOT; armed only by route.
    bool patch_arm(bool on, std::string& err);
    bool patch_connect(const std::string& name, bool connected,
                       std::string& err);
    std::string patch_json() const;   // compact route echo
    // PAT2 exports/restores the sensor subsystem's filter/edge state, clocks
    // and in-flight samples, bound to the exact current receptor descriptors.
    // This is NOT a whole-engine continuation checkpoint: caller restores the
    // matching mesh/seal/LMB1 registry first, and owns mechanical/controller
    // state and the global tick. Historical cut/fire stamps retain provenance.
    // Legacy PAT1 is accepted as a recipe: reset sensors, apply connections.
    // Both formats validate fully before mutation; unknown versions refuse.
    bool patch_restore(const std::string& body);
    void export_patch_state(std::vector<uint8_t>& out);
    bool patches_armed() const { return patches_armed_; }

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
    std::atomic<bool> body_active_{false};
    chimera::articulation::JointBinding body_binding_;
    std::vector<float> published_verts_; // final posed/contact surface, under seal_mtx_
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
        // PHASE-1 EXPLICIT INVENTORY (septa packet v3): w is the cell's
        // fluid inventory as volume at reference density; mass follows
        // m = LIMB_MASS_RHO * w (1000 kg/m^3, water — conversion stated
        // once beside the constant in membrane_tick.cpp). v0 stays
        // IMMUTABLE REFERENCE GEOMETRY and p stays DERIVED-ONLY (the
        // kappa law is unchanged). Initial condition: w = v0 for every
        // fresh cell (full at rest, so p(0) = 0 matches the measured
        // baseline). Phase 1 has NO transfer path: w is invariant after
        // initialization/restore; a cut daughter is a new full-at-rest
        // cell (w := its own v0), consistent with the packet's
        // initial-condition law.
        float w = 0.f;
        int caps = 0;
        float ylo = 0.f, yhi = 0.f;     // rest y-range (refusal checks)
        bool degenerate = false;        // live volume under the sampling
                                        // floor (H8): p is withheld, the
                                        // flag is the truth instead
    };
    bool  sealed_ = false;              // any cell exists
    float seal_y_ = 0.f, kappa_ = 4.6e-10f;
    // THE DEGENERATE-CELL GUARD (H8 world-doctor): the live creature's
    // cell 4 was a flat "pancake" (v0 = 4.655e-9 m^3, ylo == yhi == the
    // cut plane y=0.338) created by a same-plane re-cut; the kappa law
    // then answered (v0-v)/(kappa*v0) ~ 1/4.6e-10-scale GPa pressures on
    // any pose and poisoned every judge/gait reader (live: 1.6228 GPa).
    // One law at both admission and per-tick: a cell whose volume is
    // under 0.5% of its parent's rest volume is NOT anatomy. Measured
    // separation on this creature (bisect 2026-09-14): real daughters
    // 9.51% / 47.3% / 52.7% / 46.3% / 53.8% of their parents; the
    // degenerate daughter 1.62e-8 of its parent (4.655e-9 / 0.2879 m^3)
    // -- nine orders of magnitude between the classes; the bar sits 19x
    // below the smallest real daughter and ~3e5 above the noise. In
    // pressure terms the singularity the guard prevents is v->0 ==>
    // p->1/kappa = 2.17 GPa, 145x the skin yield (yield_pa_, Yamada).
    static constexpr float SEAL_DEGENERATE_FRAC = 0.005f;
    std::string seal_refusal_;          // last refused seal/split, BY NAME
                                        // ("degenerate_split"); empty = none.
                                        // Exported in state_json.
    // PHASE-1 inventory migration marker: set to "legacy_no_w" when a
    // legacy SEL1 seal-state snapshot (no per-cell w) was restored and
    // every cell's w was initialized w := v0 (the physical full-at-rest
    // default) — a NAMED, logged initialization, never a silent one.
    // Empty when w came from a SEL2 blob or no restore happened.
    // Exported by state_json() as "seal_w_init".
    std::string seal_w_init_;
    // THE ALREADY-SATISFIED TOLERANCE (restore idempotency): a replayed
    // cut counts as already satisfied when the requested plane sits on a
    // stored cell bound. The stored bounds are exact (seal() forces new
    // cap slots to py == y), and the per-replay re-evaluation drift H8
    // measured is ~1 ulp (~1e-7 m at y = 0.338); authored cut planes on
    // this creature are >= 0.3 m apart. 1e-4 m is the repo's named 0.1 mm
    // scale (the press-decay cutoff): 1000x above the drift, 3000x below
    // the smallest authored separation.
    static constexpr float SEAL_ALREADY_TOL_M = 1e-4f;
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
    // THE ARM-ON-READINESS COUNTER (the intermittent inert start, V1b):
    // bumped by the gravity block every tick it evaluates the ground
    // force. set_gravity(true) returns only AFTER the first evaluation
    // under the flag -- arming is the first computed contact force, not
    // the flag flip (a settle probe reading between the flip and the
    // first integrating tick sees the init-reset 0/0 and calls a live
    // body inert -- the measured window-4 race).
    std::atomic<uint64_t> ground_evals_{0};
    // F1 STANCE state (see set_stance above). Default OFF; the lead owns
    // the policy flip after the bars pass (the gravity precedent).
    static constexpr uint8_t ANKLE_PIN_L = 17, ANKLE_PIN_R = 18;
    bool  stance_on_ = false;                  // the balance servo switch
    float stance_th_ = 0.f;                    // symmetric ankle angle, rad
    float stance_kp_ = 0.f;                    // rad/(m s), derived at enable
    float lean_ref_x_ = 0.f, lean_ref_z_ = 0.f;   // authored-rest lean, m
    float stance_lean_x_ = 0.f, stance_lean_z_ = 0.f;  // live lean, m (report)
    std::vector<uint32_t> stance_sup_;         // frozen support vert indices
    void  stance_off_locked_();                // assumes seal_mtx_ held
    // ─── G1: THE GAIT CHECKPOINT MACHINE (the robot-stack rung 2; prereg
    // ─── appended to SEAL_PREREGISTRATION.md) ──────────────────────────
    // The leg chain pins (the joint atlas: hip_L/R = 13/14, knee_L/R =
    // 15/16; the ankles are F1's ANKLE_PIN_L/R above and stay F1-owned).
    static constexpr uint8_t HIP_PIN_L = 13, HIP_PIN_R = 14;
    static constexpr uint8_t KNEE_PIN_L = 15, KNEE_PIN_R = 16;
    // The checkpoint phases. RECOVER is the MEASURED abort (support lost
    // or the swing foot touched down mid-reach): return the leg to
    // bearing and re-arm. No phase advances on a timer.
    enum class GaitPhase : uint8_t { STANCE = 0, LIFT = 1, REACH = 2,
                                     LOAD = 3, RECOVER = 4 };
    bool      gait_on_ = false;
    GaitPhase gait_phase_[2] = {GaitPhase::STANCE, GaitPhase::STANCE};
    // Frozen at set_gait(true) from the rest blend (the F1 frozen-support
    // lesson: a per-frame re-selected set chases its own actuation and
    // self-cancels the channel).
    std::vector<uint32_t> gait_foot_verts_[2];  // per-side foot vertex sets
    float gait_patch_r_[2] = {0.f, 0.f};        // support-patch radius, m
    float gait_foot_rest_z_[2] = {0.f, 0.f};    // rest z of each foot centroid
    float gait_lean_ref_x_ = 0.f, gait_lean_ref_z_ = 0.f;  // rest lean, m
    // Probe channels, MEASURED at +1 deg per pin on the rest blend (the
    // F1 probe precedent): d(foot-set min y)/dtheta and d(foot centroid
    // z)/dtheta, SIGNED -- the sign is measured, never assumed. [side].
    float gait_dminy_hip_[2] = {0.f, 0.f};      // m/rad
    float gait_dminy_knee_[2] = {0.f, 0.f};     // m/rad
    float gait_dcz_hip_[2] = {0.f, 0.f};        // m/rad
    float gait_dcz_knee_[2] = {0.f, 0.f};       // m/rad
    // The DRIVE PINS, RESOLVED FROM THE BINDING at set_gait(true) (the
    // V3a audit, R4_GAIT_VERIFY/ENABLE_AUDIT.md): the shipped W8 vertbind
    // gives the FOOT SETS zero weight on the hip pins 13/14 (measured:
    // 1095.96 of 1289 average blend weight sits on the ankle, 63.2 on the
    // knee, 0.000 on the hip -- pure skinning has no hip-to-foot chain),
    // so the machine's per-side "hip slot" and "knee slot" are ROLES, and
    // the pin that fills each role is measured, not assumed: per side,
    // the two pins with the largest NET blend weight on that side's foot
    // set (own-side minus opposite-side -- a pin belongs to the side it
    // moves more; this rejects the contralateral fill pin, whose net
    // coupling is negative). The role goes to the measured channel: the
    // STRUT (z-servo in REACH) is whichever resolved pin has the larger
    // |dcz|; the CLEAR pin holds the LIFT/REACH clearance. On the shipped
    // creature this resolves to ankle/knee 17/15 and 18/16; hips 13/14
    // stay at authored bearing (zero footprint -- measured).
    int gait_strut_pin_[2] = {-1, -1};          // resolved drive pin, z role
    int gait_clear_pin_[2] = {-1, -1};          // resolved drive pin, clearance
    // Derived rate caps: the foot's arc speed never exceeds its own
    // patch radius per STANCE_TAU_S (the named speed bar).
    float gait_rate_hip_[2] = {0.f, 0.f};       // rad/s
    float gait_rate_knee_[2] = {0.f, 0.f};      // rad/s
    // The LIFT combo: the hip:knee ratio that nulls the centroid z drift
    // (a_h = dcz_knee, a_k = -dcz_hip) with its measured rise channel
    // ch = a_h*dminy_hip + a_k*dminy_knee. Derived from the probes.
    float gait_lift_ah_[2] = {0.f, 0.f};
    float gait_lift_ak_[2] = {0.f, 0.f};
    float gait_lift_ch_[2] = {0.f, 0.f};
    // ─── THE STRIDE-SCALE BRANCH LAW (R4-stride-finisher; measured on the
    // ─── live binding, window-4 binary) ────────────────────────────────
    // The 1-deg probes above linearize the swing pins at bearing, but the
    // strut's z-channel is NONMONOTONIC in theta on this binding (measured
    // live ladder: +10.0 mm/deg posed at +1 deg -- membership-shifted; the
    // clean curve: +5 mm total near -4.6 deg, back through 0 near -10 deg,
    // then -35 mm/deg: an ORBIT about the pin pivot, not a linear rail).
    // A 1-deg probe cannot see the reversal, so REACH derives its law from
    // a +20 deg probe on the same rest blend (inside the 89-deg ROM):
    // lift_sign = the theta sign that RAISES the foot set (sign of
    // dminy20); reach_dir = the z direction that branch actually swings
    // (sign of lift_sign*dcz20; measured -1 here -- the usable swing is
    // backward). The opposite branch is measured unusable for a stride:
    // it presses the foot DOWN (dminy20 < 0 at +20 deg), faster than the
    // clear pin's measured rise (2.5-3.2 mm/deg to -43 deg) can pay.
    float gait_lift_sign_[2] = {0.f, 0.f};      // +/-1, the raising theta sign
    float gait_reach_dir_[2] = {0.f, 0.f};      // +/-1, the branch's z swing
    float gait_dminy20_hip_[2] = {0.f, 0.f};    // m/rad at the +20 deg probe
    float gait_dcz20_hip_[2] = {0.f, 0.f};      // m/rad at the +20 deg probe
    // THE WHAT-IF, re-derived for the MEASURED plant (the Y-only root):
    // a lifted foot cannot TIP this body -- the root has no horizontal or
    // rotational DOF (the prereg's own SCOPE), so the rigid-body premise of
    // the old absolute-centroid gate is unexpressable, and its demand (0.42
    // m of body travel toward the stance foot) has no actuator: measured
    // 0.9867 vs bar 0.5711 at rest, still 0.69 at full strut ROM -- F-STALL.
    // What CAN fail is GROUNDING: the lift's cross-coupled sink drops the
    // body until non-foot anatomy touches the floor. Measured at enable:
    // sink_ch = d(min-y of the OTHER foot set) per rad of the lift combo on
    // the rest blend (the root follows the support down by exactly this,
    // damping aside), headroom = the grounding distance from the feet's
    // rest min-y to the lowest NON-foot rest vertex, minus the derived sink
    // (the rest equilibrium sits one sink above authored rest). Gate: the
    // predicted sink for THIS lift must fit inside headroom minus the
    // bearing margin. Measured here: sink_ch ~12 mm/rad, a full lift sinks
    // ~14 mm against a 348 mm headroom -- passes with 25x margin, and a
    // body that would sit down mid-stride is refused BY NUMBER.
    float gait_sink_ch_[2] = {0.f, 0.f};        // m/rad of other-foot rise
    float gait_headroom_ = 0.f;                 // m of grounding headroom
    // The swing foot's OWN support-patch center, frozen at the STANCE->LIFT
    // transition. The stride bar is the prereg's geometric necessity --
    // "the new footfall lands outside the old support patch" -- measured
    // as the RADIUS condition |fcz[s] - z0| >= patch_r[s] on the foot's
    // own patch. The stance-relative reading is measured-unreachable on
    // this binding past one stride: the strut's whole z-reach is 0.677 m
    // (live ladder, -61 deg) while the stance-relative bar demands
    // 2x patch = 1.142 m once the feet are patch-separated -- F-STALL at
    // ROM. Feet start together here (homeL 0.7212 ~ homeR 0.7212), so the
    // first stride satisfies both readings; only the own-patch reading
    // keeps every later one reachable.
    float gait_swing_z0_[2] = {0.f, 0.f};       // m, centroid z at LIFT entry
    // The commanded leg angles (rad) -- the machine's own state; 0 =
    // authored bearing. Written to joint_deg_ pins 13-16 each tick.
    float gait_knee_rad_[2] = {0.f, 0.f};
    float gait_hip_rad_[2] = {0.f, 0.f};
    // Measured reports (state_json), fresh every tick.
    float gait_depth_[2] = {0.f, 0.f};          // world depth below y=0, m
    float gait_clear_[2] = {0.f, 0.f};          // above the other foot, m
    float gait_lean_x_ = 0.f, gait_lean_z_ = 0.f;  // live lean, m (report)
    float gait_p_max_ = 0.f;                    // max |P| over sealed cells
    std::string gait_block_[2];                 // the gate blocking this leg
    int gait_feet_cell_ = -1;                   // feet sealed cell (min yhi)
    uint32_t gait_stride_count_ = 0;
    uint64_t gait_last_done_[2] = {0, 0};       // ticks_ at last LOAD exit
    std::vector<std::string> gait_log_;         // bounded transition log
    std::string gait_enable_block_;             // the set_gait(true) refusal,
                                                // BY NAME (the seal_refusal_
                                                // law: an enable that refuses
                                                // without naming its blocker
                                                // is undiagnosable). Empty =
                                                // armed. Exported in
                                                // state_json.
    void  gait_off_locked_();                   // assumes seal_mtx_ held
    void  gait_step_locked_(std::vector<float>& verts9, float dt);
    void  gait_log_locked_(int leg, const char* from, const char* to,
                           const std::string& gates);
    static const char* gait_phase_name(GaitPhase p);
    // ─── C1r: THE CREATURE ANSWERS — reflex state (default OFF; see the
    // ─── set_reflex comment above and PREREG.md) ────────────────────────
    struct ReflexState {
        bool armed = false;
        bool breathing = true, flinch = true, startle = true;
        bool pressure_coupling = true;   // THE NERVE: false = cut
        std::string block;               // arm refusal BY NAME (the
                                         // gait_enable_block_ law: a bare
                                         // ok:false is undiagnosable)
        // -- breathing --
        int   breath_cell = -1;          // the torso cell (argmax v0)
        float breath_omega = 0.f;        // rad/s, Stahl allometry at arm
        float breath_period_s = 0.f;     // report
        float breath_amp_frac = 0.f;     // V_T / torso v0 (report)
        float breath_mean_disp = 0.f;    // m, V_T / torso skin area
        float breath_disp = 0.f;         // m, live peak displacement (report)
        float breath_phase = 0.f;        // rad (frozen when suspended)
        std::vector<uint32_t> breath_verts;  // torso-cell original slots
        std::vector<float>    breath_w;      // raised-cosine y-band profile
        // -- flinch --
        float flinch_theta = 0.f;        // rad (the 5 deg authority bound)
        float env_l = 0.f, env_r = 0.f;  // per-side envelopes (0..1)
        bool  pin_held[2] = {false, false};  // the flinch owns this write
        int   strut_pin[2] = {-1, -1};   // same-limb law (reuse-or-resolve)
        float lift_sign[2] = {0.f, 0.f}; // the raising branch, per side
        int   last_cell = -1;            // last trigger (report)
        uint64_t last_tick = 0;
        // -- startle --
        float startle_bias = 0.f;        // rad (one rest-sink lean quantum)
        float startle_env = 0.f;
        float startle_dir = 0.f;         // +/-1, away from the stimulus
        uint64_t startle_last_tick = 0;
        // -- stimulus geometry (rebuilt when the cell count changes) --
        std::vector<float> prev_p;       // per sealed cell (the detector's
                                         // own membrane: tracks the TRUE
                                         // pressure even through a nerve
                                         // cut, so reconnecting never sees
                                         // a stale rising edge)
        std::vector<float> cell_cx, cell_cz;  // rest centroids (report/dir)
        float body_cz = 0.f;             // rest whole-body centroid z
        bool  prev_p_valid = false;
        float quiet_s = 1e30f;           // time since the walker last ran
        float stance_s = 0.f;            // time the stance rung has been
                                         // armed under gravity (the
                                         // startle's corollary-discharge
                                         // gate: a rung still converging
                                         // after its own arm is the
                                         // creature's own motion)
    };
    ReflexState reflex_;
    void  reflex_detect_locked_(float dt);      // fresh per-cell pressures
    void  reflex_compose_locked_();             // startle over stance
    void  reflex_breath_locked_(std::vector<float>& verts9, float dt);
    bool  reflex_resolve_locked_(std::string& block);  // same-limb pins
    void  reflex_off_locked_();                 // assumes seal_mtx_ held
    // ─── AN2: THE ONE-LIMB PARTITION + SENSOR PATCHES (prereg M1-M4) ────
    // ONE generalized cut core shared by the horizontal seal() and the
    // oblique limb walls: straddle-split, weld-chain, the winding law,
    // divergence volumes, positivity + degenerate guards, publish. pd is
    // the SIGNED PLANE DISTANCE per point (the only Y-specific part of
    // the old code); new cut points push pd == 0 exactly (the H8 law).
    // py rides parallel (rest y per point) for the ylo/yhi bounds the
    // already-satisfied checks of later Y cuts compare against.
    bool  seal_cut_core_(int cell_idx,
                         std::vector<CutBlend>& pts,
                         std::vector<float>& pd,
                         std::vector<float>& py,
                         const std::vector<float>& rest9,
                         size_t ncut0);
    // split()'s body WITHOUT the lock (limb_partition runs the component
    // split inside its own seal_mtx_ critical section; std::mutex is not
    // recursive -- the public wrapper adds the lock).
    bool  split_locked_(int cell_idx);
    struct LimbSeg {
        std::string name;            // "thigh_L" | "shin_L" | "foot_L" (| _R)
        int cell = -1;               // sealed cell index (fixed at build)
        int pin_prox = -1, pin_dist = -1;   // chain pins (foot dist = -1)
        std::array<float,3> plane_n = {0.f, 0.f, 0.f};  // distal normal
        std::array<float,3> plane_p = {0.f, 0.f, 0.f};  // through-point
        float v0 = 0.f;
        uint32_t pieces = 0;         // piece-triangle count (blob validation)
        int seed_total = 0, seed_agree = 0;   // seed-vs-wall agreement
    };
    struct SensorPatch {
        std::string name;            // segment name (patch id)
        std::vector<uint32_t> verts; // the finite receptor region (frozen)
        std::array<float,3> c = {0.f, 0.f, 0.f};   // rest centroid
        int cell = -1;               // owning cell (fixed at build)
        int side = 0;                // 0 = L, 1 = R
        float tau_f = 0.010f;        // filter tau, s (= 3 ticks @ 300 Hz)
        float sat_m = 0.030f;        // saturation = press_r0_
        float delay_s = 0.f;         // finite transport delay, s
        float thresh_m = 1e-3f;      // rising-edge trigger, m
        // -- path state (a cut is a real state) --
        bool connected = true;
        uint64_t cut_tick = 0;
        int64_t  cut_us = 0;         // engine steady-clock at the cut
        // -- live signal --
        float filt = 0.f;            // filtered (pre-saturation, pre-delay)
        float out = 0.f;             // delivered (post-delay)
        float prev_out = 0.f;        // the delivered-edge membrane
        float clock_s = 0.f;         // the patch line's own time base
        std::deque<std::pair<float,float>> line;   // (t, saturated) in transit
        uint64_t last_fire_tick = 0;
        int fires = 0;
        float last_raw = 0.f;
    };
    std::vector<LimbSeg> limb_segs_;
    bool limb_done_ = false;
    std::string limb_side_;                      // "L" | "R" partitioned
    std::string limb_report_;                    // the full JSON report
    std::vector<SensorPatch> patches_;
    bool patches_armed_ = false;
    float patch_clock_s_ = 0.f;                  // armed-time accumulator
    std::vector<std::string> patch_event_log_;   // bounded JSON rows (64)
    bool  patch_step_locked_(float dt);          // filter/delay/deliver
    void  patch_off_locked_();                   // deterministic disarm
    bool  patch_build_locked_(std::string& err); // regions from the segments
    void  patch_log_locked_(const std::string& row);  // bounded event log
    std::string patch_json_locked() const;       // caller holds seal_mtx_
    // -- shared geometry helpers (partition / patches / blob validation) --
    void  rest_geometry_locked_(std::vector<float>& rest9,
                                std::vector<float>& cutrest) const;
    float div_pieces_(const std::vector<uint32_t>& pieces,
                      const std::vector<float>& rest9,
                      const std::vector<float>& cutrest) const;
    // closed-manifold test + Euler characteristic: every undirected edge
    // of the piece set must be used exactly twice (closure); chi = V-E+F.
    bool  cell_topology_(const std::vector<uint32_t>& pieces,
                         int* chi_out) const;
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
