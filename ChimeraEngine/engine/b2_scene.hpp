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
    void pp_pair_(Part &a, Part &b,
                  double *Fa, double *Ta, double *Fb, double *Tb) const;
    // Validate one part element (admission parts[] entry / place document)
    // and append it to `built`, rejecting duplicate ids. Throws
    // std::runtime_error naming the offending field on any violation, so
    // callers keep their transaction by building into a copy.
    static void parse_part_(const b2j::JVal &pj, const std::string &where,
                            std::vector<Part> &built);
    // Canonical serialisation shared by save_json() and state_hash().
    std::string save_doc_() const;
    double kinetic_j_() const;
    double potential_j_() const;
    double stored_penalty_j_() const;

    std::vector<Part> parts_;
    std::vector<Weld> welds_;                    // finite-area connectors
    double gravity_ = 9.81;                      // m/s^2 (down)
    bool gravity_on_ = true;                     // power-removal control
    bool support_on_ = true;                     // support-removal control
    bool active_ = false;
    bool paused_ = false;                        // B4: freeze integration
    bool diverged_ = false;
    long steps_ = 0;
    double e0_j_ = 0.0;                          // energy right after admission
    std::string reason_;                         // admission reason (audit)
};
