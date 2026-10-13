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

#include <string>
#include <vector>

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

    // Controls (B2 gate right column). Empty string on success, refusal
    // otherwise. set_load: persistent force at a world point on one part
    // (zero vector removes it). set_support / set_gravity: switch the ground
    // rung / gravity term for the whole scene (support-removal control).
    std::string set_load(const std::string &json);
    std::string set_support(bool on);
    std::string set_gravity(bool on);

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

    // one substep of all parts; returns false on divergence
    bool substep_(double h);
    // world position of authored vertex vi of p
    static void world_vert_(const Part &p, size_t vi, double out[3]);
    // loose contact between two parts: vertices of each against boundary
    // triangles of the other, one-sided penalty rung (same law as ground),
    // regularised Coulomb friction; exact Newton-3 pairs accumulated into
    // the force/torque accumulators of a and b.
    void pp_pair_(Part &a, Part &b,
                  double *Fa, double *Ta, double *Fb, double *Tb) const;
    double kinetic_j_() const;
    double potential_j_() const;
    double stored_penalty_j_() const;

    std::vector<Part> parts_;
    double gravity_ = 9.81;                      // m/s^2 (down)
    bool gravity_on_ = true;                     // power-removal control
    bool support_on_ = true;                     // support-removal control
    bool active_ = false;
    bool diverged_ = false;
    long steps_ = 0;
    double e0_j_ = 0.0;                          // energy right after admission
    std::string reason_;                         // admission reason (audit)
};
