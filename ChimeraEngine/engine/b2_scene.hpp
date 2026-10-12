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

private:
    struct Part {
        std::string id;
        double mass = 0.0;                       // kg
        double com_local[3] = {0, 0, 0};         // m, authored axes
        double inertia_com_local[9] = {0};       // kg m^2, about COM, authored axes
        std::vector<double> verts;               // 3N authored vertex positions (m)
        std::vector<int> tris;                   // 3T boundary triangle indices
        double k_site = 0.0, c_site = 0.0;       // this part's per-site ground rung
        // dynamic state (world frame)
        double c[3] = {0, 0, 0};                 // COM position
        double R[9] = {1, 0, 0, 0, 1, 0, 0, 0, 1};
        double v[3] = {0, 0, 0};                 // COM velocity
        double omega[3] = {0, 0, 0};             // angular velocity (world)
        // per-step telemetry
        double reaction_n = 0.0;                 // summed active ground force (N)
        double pen_step_m = 0.0;                 // max penetration this step
        int contacts_active = 0;
        // run envelope
        double pen_run_m = 0.0;                  // max penetration since admit
    };

    // one substep of all parts; returns false on divergence
    bool substep_(double h);
    double kinetic_j_() const;
    double potential_j_() const;
    double stored_penalty_j_() const;

    std::vector<Part> parts_;
    double gravity_ = 9.81;                      // m/s^2 (down)
    bool active_ = false;
    bool diverged_ = false;
    long steps_ = 0;
    double e0_j_ = 0.0;                          // energy right after admission
    std::string reason_;                         // admission reason (audit)
};
