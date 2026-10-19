#pragma once
// ─── B2: TWO INDEPENDENT PARTS ON THE SHARED RESIDENT RUNTIME ───────────────
// GAME_PLAN_ACTION_RPG.md §13 B2, first step: two independent rigid parts,
// gravity and support, on the one resident engine state. The formulations are
// PORTED, not invented, from the accepted coupon model
// (tools/finite_area_attachment/native/native_coupon.cpp):
//   * per-site one-sided ground rung  (coupon contact_forces, :754-771)
//   * rigid integration with world inertia R·I_local·Rᵀ + Euler term
//     (coupon step, :854-862)
//   * admission validations: proper rotation, inertia triangle inequality,
//     finite numbers (coupon :278-295)
// Design + DOF/material ownership:
//   docs/evidence/construction_packet_20261012/B2_design_and_dof_ownership.md
// The scene is DEFAULT OFF: nothing exists until /tick_b2_admit admits a
// strict `chimera.b2_scene.v1` document; a mesh swap clears it. The resident
// single-body FALL rung is untouched — these parts own their DOFs exclusively.

#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace b2j { struct JVal; }   // strict JSON node; defined in b2_scene.cpp

class B2Scene {
public:
    // Strict admission of a chimera.b2_scene.v1 JSON document. Returns an
    // empty string on success, otherwise the refusal reason (self-naming).
    std::string admit(const std::string &json, const std::string &reason);
    void clear();
    bool active() const { return active_; }

    // Advance every part by dt seconds in fixed 1/4000 s substeps (frame dt
    // clamped to 0.05 s, the engine's own clamp). Returns false if any state
    // went non-finite (the scene then refuses to keep integrating).
    bool step(double dt);

    // Telemetry for /tick_b2_state (self-naming JSON, lock held by caller).
    std::string telemetry_json() const;
    // Static + current part data for /tick_b2_parts (lock held by caller).
    std::string parts_json() const;
    // Stable-ID inspection (B3 gate): body {"id":"..."}; on hit returns the
    // full record for that part, on miss returns "" and names the refusal.
    std::string inspect(const std::string &json, std::string &why) const;

    // B3 render/pick lane. render_mesh emits the scene's CURRENT world pose
    // as a render stream (9 floats/vertex: pos, normal, rgb; one flat-shaded
    // triangle per boundary triangle) plus indices -- the same boundary
    // triangles the contact solver walks. The palette is fixed by part
    // admission order so a frame capture can name the layer by color.
    void render_mesh(std::vector<float> &verts9, std::vector<uint32_t> &tris) const;
    // Ray pick (Moller-Trumbore, nearest hit) against the SAME world meshes
    // render_mesh draws and pp_pair_/ground contact uses: render, pick and
    // contact agree by construction. Returns false when the ray hits nothing.
    bool pick(const float eye[3], const float dir[3],
              std::string &id_out, float point_out[3]) const;
    // B-INTERACTIVE selection highlight (display only, never serialized --
    // save_doc_/state_hash never see it): the part id whose render pass uses
    // kHighlightRgb instead of its palette color; empty = none. A removed id
    // simply matches nothing (the palette shows through).
    void set_highlight(const std::string &id) { highlight_id_ = id; }

    // Controls (B2 gate right column). Empty string on success, refusal
    // otherwise. set_load: persistent force at a world point on one part
    // (zero vector removes it). set_support / set_gravity: switch the ground
    // rung / gravity term for the whole scene (support-removal control).
    std::string set_load(const std::string &json);
    std::string set_support(bool on);
    std::string set_gravity(bool on);
    // Finite-area connector (the B2 gate's "one finite-area connector",
    // coupon Weld form): weighted anchor pairs across the A-B interface.
    // set_weld captures the world anchor points in each part's local axes
    // (the weld rides the parts); >= 3 anchors so the patch is an AREA,
    // not a pin. remove_weld deletes the connector between the named pair
    // (the separate control's second half: connector removal -> free motion
    // under the still-applied pull).
    std::string set_weld(const std::string &json);
    std::string remove_weld(const std::string &json);

    // ─── B4: interactive assembly, transactional (GAME_PLAN §13 B4) ────────
    // Every edit below is all-or-nothing: the document is fully validated
    // against the live scene BEFORE anything mutates, so a rejected edit
    // leaves the scene bit-identical (state_hash proves it).
    // set_pause freezes integration while the scene stays live and readable
    // (the gate's "test" then "release").
    std::string set_pause(bool on);
    bool paused() const { return paused_; }
    // place adds one part (same element schema as an admission parts[]
    // entry; scene cap 6). The part spawns at its document pose, at rest.
    std::string place(const std::string &json);
    // remove_part releases one part by id: its persistent load dies with
    // it (loads live on the part) and every weld touching it is dropped --
    // no stale selections -- with the surviving weld indices remapped.
    std::string remove_part(const std::string &json);
    // patch is the mechanical material patch: {"id", "mu"?, "mass_kg"?}
    // (at least one of mu/mass_kg). A mass change scales inertia AND the
    // per-site ground constants by the same ratio: the rung law
    // k_total = m·g/s*, c_total = 2ζ√(k_total·m) is linear in m, so the
    // part keeps its rest sink s* and damping ratio ζ — the material
    // changed, the contact law did not.
    std::string patch(const std::string &json);
    // save_json serialises the FULL persistent state (admitted identity +
    // dynamic state + welds + switches + audit fields) as
    // chimera.b2_state.v1. Doubles print %.17g (exact round-trip) and the
    // pose carries the rotation matrix verbatim, so restore reproduces the
    // scene bit-for-bit. restore validates a saved document end-to-end and
    // swaps it in atomically (rejected documents leave the scene untouched).
    std::string save_json() const;
    std::string restore(const std::string &json);
    // FNV-1a-64 over the canonical save document: two scenes with equal
    // hashes are the same scene (used to prove rejected edits preserve
    // state and save/reload round-trips exactly).
    std::string state_hash() const;

    // ─── B6: working processes (GAME_PLAN §13 B6) ──────────────────────────
    // Chamber pressure/flux, valves, a finite actuator, sensors and heat
    // transfer, each a separately qualified channel on the SAME resident
    // scene and clock. The law is the membrane's own linear compressibility
    // (membrane_tick.cpp: p = (v0 - v)/(kappa*v0)) generalised to inventory
    // vs volume: P = kappa*(q - V)/V0, stored energy U = kappa*(q-V)^2/(2*V0)
    // -- the same quadratic a spring stores, so every paired exchange closes
    // EXACTLY against the quadratic identity dU = (P_old+P_new)/2 * dX.
    // Chambers hold inventory q (m^3, signed); volume V = V0 plus the
    // displacement of any coupled piston. Valves move inventory between two
    // chambers or to/from the environment (b == "env", P_env = 0); the flux
    // is applied to both sides in the same substep, so material inventories
    // are conserved by construction and the ledger proves it. Pistons apply
    // P*area along a world axis to one part (the reaction goes to the world:
    // the chamber is built into the lair ground, like the ground rung) and
    // are FINITE: a stroke stop zeroes the push beyond stroke, and f_max
    // clamps it (the clamped excess is relief dissipation, tracked). Heat
    // links move energy between chambers in exact pairs. The process
    // telemetry is the sensor channel: read-only, state_hash-invariant.
    // Every control validates fully before mutating (B4 transaction law).
    std::string add_chamber(const std::string &json);      // {"id","V0_m3","kappa_Pa","q_m3"?,"T_K"?,"C_th_J_K"?}
    std::string set_valve(const std::string &json);        // {"a","b","g_m3_Pa_s","open"?}  b: chamber id or "env"
    std::string set_valve_open(const std::string &json);   // {"a","b","on"}
    std::string remove_valve(const std::string &json);     // {"a","b"}
    std::string patch_valve(const std::string &json);      // {"a","b","cost_m3"} seal an env leak, debiting inventory
    std::string add_heat(const std::string &json);         // {"a","b","k_W_K"}
    std::string remove_heat(const std::string &json);      // {"a","b"}
    std::string add_piston(const std::string &json);       // {"chamber","part","axis":[3],"area_m2","stroke_m"?,"f_max_N"?}
    std::string remove_piston(const std::string &json);    // {"chamber","part"}
    std::string process_clear();                           // drop process state, parts untouched
    std::string process_telemetry_json() const;            // GET /tick_b2_process (sensor: const)

    // ─── B7: bounded pools, display LOD, round-trip accounting ─────────────
    // GAME_PLAN §13 B7 ("bounded topology pools ... compatible render LOD";
    // gallery 13: "a different triangle order or display LOD does not change
    // material strength, secretly heal a crack or relabel a port").
    // The caps are the declared topology pools: admission/transactions
    // refuse past the cap by name, and the usage is telemetry.
    static constexpr size_t CAP_PARTS = 6, CAP_WELDS = 15, CAP_CHAMBERS = 6,
                            CAP_VALVES = 12, CAP_HEAT = 12, CAP_PISTONS = 6;
    // Display LOD: 0 = the physical boundary triangles (render, pick and
    // contact agree by construction); 1 = per-part world bounding boxes,
    // a DISPLAY-ONLY approximation — physics, contact and the state hash
    // never see it, and selection still resolves to the same part ids
    // (the box contains the part; the hit point is a declared approximation).
    std::string set_display_lod(const std::string &json);  // {"level":0|1}
    int display_lod() const { return lod_; }

private:
    struct Part {
        std::string id;
        double mass = 0.0;                       // kg
        double com_local[3] = {0, 0, 0};         // m, authored axes
        double inertia_com_local[9] = {0};       // kg m^2, about COM, authored axes
        std::vector<double> verts;               // 3N authored vertex positions (m)
        std::vector<int> tris;                   // 3T boundary triangle indices
        double k_site = 0.0, c_site = 0.0;       // this part's per-site ground rung
        double mu = 0.0;                         // Coulomb ratio, all contacts (0 = frictionless)
        // persistent external load (off-center load control): the load rides
        // the part — the application point is captured in local axes at
        // set_load time, so its torque arm follows the pose.
        double load_F[3] = {0, 0, 0};            // N, world frame
        double load_local[3] = {0, 0, 0};        // m, authored axes
        // dynamic state (world frame)
        double c[3] = {0, 0, 0};                 // COM position
        double R[9] = {1, 0, 0, 0, 1, 0, 0, 0, 1};
        double v[3] = {0, 0, 0};                 // COM velocity
        double omega[3] = {0, 0, 0};             // angular velocity (world)
        // per-step telemetry
        double reaction_n = 0.0;                 // summed active ground force (N)
        double pen_step_m = 0.0;                 // max penetration this step
        int contacts_active = 0;
        double contact_pp_n = 0.0;               // summed active part-part contact force (N)
        int contacts_pp_active = 0;
        std::vector<double> ground_fn;           // per-vertex ground rung force this step
        // run envelope
        double pen_run_m = 0.0;                  // max penetration since admit
        double pen_pp_run_m = 0.0;               // max part-part penetration
        // B9 material-geometry-solver qualification envelope (optional,
        // declared at admission; echoed in the save document so restore
        // revalidates the same tuple). Runtime event flags fire once per
        // part per limit; they are telemetry, never serialized.
        bool has_env = false;
        double env_lat_n = 0.0;                  // expected sustained lateral load at COM (N)
        double env_speed = -1.0;                 // expected max COM speed (m/s); -1 = undeclared
        int env_role = 0;                        // 0 none, 1 stand, 2 slide, 3 impinge
        bool env_ev_speed = false, env_ev_stop = false, env_ev_tilt = false;
    };

    // Finite-area weld between parts a and b (coupon Weld { av, al, w, k }
    // ported to two rigid bodies): anchor pairs (la_j, lb_j) in local axes,
    // weights summing to 1, stiffness k. Force w_j*k*(pb-pa) applied +on a
    // at pa and -on b at pb -- a central pair, exact Newton-3 in force AND
    // torque (total angular momentum conserved).
    struct Weld {
        size_t a = 0, b = 0;                     // part indices
        std::vector<double> la, lb;              // 3N local anchors (authored axes)
        std::vector<double> w;                   // N weights (sum 1)
        double k = 0.0;                          // N/m
        double c = 0.0;                          // N.s/m along anchor line (0 = coupon port)
        double force_n = 0.0;                    // |total force| this step (telemetry)
    };

    // ─── B6 process state (see the public block for the law) ───────────────
    struct Chamber {
        std::string id;
        double V0 = 0.0;            // rest volume, m^3 (> 0)
        double kappa = 0.0;         // bulk modulus, Pa (> 0)
        double q = 0.0;             // inventory (fluid volume), m^3, signed
        double T = 0.0;             // temperature, K
        double C_th = 0.0;          // heat capacity, J/K (>= 0)
        // per-step telemetry
        double p_pa = 0.0;          // pressure this step
        double flux_in_m3_s = 0.0;  // net volumetric flux IN this step
    };
    struct Valve {
        size_t a = 0;               // chamber index
        int b = -1;                 // chamber index, or -1 = environment
        double g = 0.0;             // conductance, m^3/(Pa.s) (> 0)
        bool open = true;
        double flux_m3_s = 0.0;     // signed a->b this step (telemetry)
        double diss_J_run = 0.0;    // chamber<->chamber: pressure energy dissipated
        double boundary_J_run = 0.0;// chamber<->env: energy carried across the boundary
    };
    struct HeatLink {
        size_t a = 0, b = 0;        // chamber indices (C_th > 0 both)
        double k = 0.0;             // conductance, W/K (> 0)
        double flux_W = 0.0;        // signed a->b this step
        double moved_J_run = 0.0;   // energy moved a->b (exact pair)
    };
    struct Piston {
        size_t ch = 0;              // chamber index
        size_t part = 0;            // part index
        double n[3] = {0, 1, 0};    // world axis (unit)
        double area = 0.0;          // m^2 (> 0)
        double x0 = 0.0;            // (c . n) captured at creation
        double stroke = 0.0;        // m; 0 = unlimited
        double f_max = 0.0;         // N; 0 = unlimited
        double force_n = 0.0;       // applied this step, signed along n
        double work_J_run = 0.0;    // thermodynamic work on the part: sum Pbar*dV
        double relief_J_run = 0.0;  // clamped excess dissipated (>= 0)
    };

    // process half of one substep: forces into F/T + inventory/thermal
    // updates before integration, work/ledger closure after.
    void process_forces_(double h, std::vector<double> &F, std::vector<double> &T);
    void process_post_(double h);
    double chamber_volume_(const Chamber &c) const;   // V0 + piston displacements
    size_t chamber_index_(const std::string &id) const;  // chambers_.size() = miss
    int valve_index_(const std::string &a, const std::string &b) const; // -1 = miss
    int heat_index_(const std::string &a, const std::string &b) const;  // -1 = miss
    int piston_index_(const std::string &ch, const std::string &part) const;

    // one substep of all parts; returns false on divergence
    bool substep_(double h);
    // world position of authored vertex vi of p
    static void world_vert_(const Part &p, size_t vi, double out[3]);
    // world position of an arbitrary local (authored-axes) point of p
    static void world_point_(const Part &p, const double local[3], double out[3]);
    // loose contact between two parts: vertices of each against boundary
    // triangles of the other, one-sided penalty rung (same law as ground),
    // regularised Coulomb friction; exact Newton-3 pairs accumulated into
    // the force/torque accumulators of a and b.
    void pp_pair_(Part &a, Part &b, double h,
                  double *Fa, double *Ta, double *Fb, double *Tb) const;
    // Validate one part element (admission parts[] entry / place document)
    // and append it to `built`, rejecting duplicate ids. Throws
    // std::runtime_error naming the offending field on any violation, so
    // callers keep their transaction by building into a copy.
    static void parse_part_(const b2j::JVal &pj, const std::string &where,
                            std::vector<Part> &built, double gravity);
    // Canonical serialisation shared by save_json() and state_hash().
    std::string save_doc_() const;
    // Moller-Trumbore against one world triangle; nearest-t bookkeeping
    // lives in the caller so boundary and bbox (LOD 1) picks share the law.
    static bool mt_hit_(const float eye[3], const float dir[3],
                        const double w[3][3], float &t_out);
    // world-space AABB corners of one part (LOD 1 display/pick geometry)
    void bbox_corners_(const Part &p, double out[8][3]) const;
    double kinetic_j_() const;
    double potential_j_() const;
    double stored_penalty_j_() const;

    std::vector<Part> parts_;
    std::string highlight_id_;                   // B-INTERACTIVE selection (display only)
    std::vector<Weld> welds_;                    // finite-area connectors
    std::vector<Chamber> chambers_;              // B6 pressure/flux inventories
    std::vector<Valve> valves_;                  // B6 paired transport paths
    std::vector<HeatLink> heat_;                 // B6 paired energy paths
    std::vector<Piston> pistons_;                // B6 finite actuators
    // B6 scene ledger (run totals; reset by admit/clear/process_clear)
    double vented_m3_ = 0.0;                     // inventory lost to boundary
                                                 // transactions (env valve, patch)
    double diss_run_j_ = 0.0;                    // valve dissipation (ch<->ch)
    double work_run_j_ = 0.0;                    // piston thermodynamic work
    double boundary_run_j_ = 0.0;                // energy across the boundary
    double inv0_m3_ = 0.0;                       // ledger baseline: sum q + vented
    double max_resid_energy_j_ = 0.0;            // worst per-substep closure error
    // per-substep ledger scratch, staged by process_forces_, closed by post_
    double resid_pre_upress_ = 0.0, resid_pre_uth_ = 0.0;
    double resid_pre_diss_ = 0.0, resid_pre_bound_ = 0.0, resid_pre_work_ = 0.0;
    std::vector<double> resid_vpre_;             // chamber volumes at force time
    double gravity_ = 9.81;                      // m/s^2 (down)
    bool gravity_on_ = true;                     // power-removal control
    bool support_on_ = true;                     // support-removal control
    bool active_ = false;
    bool paused_ = false;                        // B4: freeze integration
    bool diverged_ = false;
    long steps_ = 0;
    double e0_j_ = 0.0;                          // energy right after admission
    std::string reason_;                         // admission reason (audit)
    int lod_ = 0;                                // B7 display LOD (never physics)
    // B7 round-trip accounting: full-state serialisations happen ONLY on
    // explicit routes — never per tick. Instrumentation, not state: never
    // serialised, so the state hash is invariant across saves/reads.
    mutable long save_count_ = 0, restore_count_ = 0, hash_count_ = 0;
    // B8 declared impact backstop (gallery item 16): engagement counter is
    // instrumentation (never serialized, hash-invariant); bs_energy_ is the
    // current substep's backstop spring energy, booked in stored_penalty_j_.
    mutable long bs_engagements_ = 0;
    mutable double bs_energy_ = 0.0;   // pp_pair_ is const; gauge only
    // B9 out-of-envelope runtime events (cumulative across admits, like the
    // backstop counter; tests use deltas). env_last_ is a JSON object naming
    // the part, the violated limit, and measured vs declared values.
    long env_events_ = 0;
    std::string env_last_;
    std::map<std::string, long> env_limits_;   // per-limit event counts
};
