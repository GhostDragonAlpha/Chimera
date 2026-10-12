// ChimeraEngine/engine/tendon_drive.hpp
// Standalone tendon-drive physics module (energy increment 2026-10-10).
// Header-only, float64, no heap, no exceptions, deterministic.
// Decision record: docs/DECISION_ENERGY_INCREMENT_2026-10-10.md
// Inventory laws cited inline: A7 muscle, A8 tendon, A5 capsule
// (docs/THE_MEMBRANE_INVENTORY.md).
#ifndef CHIMERA_TENDON_DRIVE_HPP
#define CHIMERA_TENDON_DRIVE_HPP

#include <cmath>

namespace chimera {
namespace tendon {

// All parameters below are declared synthetic, monkey-scale, coupon
// precedent (finite_area_attachment) — NOT sourced from measurement.
// Plausibility is judged only against the qualitative ranges in
// docs/research/muscle_physiology_reference.md.
struct TendonDriveParams {
    // Segment inertia reflected at the joint [kg*m^2]. Synthetic, monkey-
    // scale, coupon precedent — NOT sourced from measurement. Plausible
    // for a small distal limb segment about one joint.
    double I = 0.02;
    // Moment arm of the tendon about the joint [m]. Synthetic, monkey-
    // scale, coupon precedent — NOT sourced from measurement. Order of
    // magnitude matches anatomical moment arms of digit/wrist tendons.
    double r = 0.03;
    // Muscle rest (optimal) fibre length L0m [m]. Synthetic, monkey-
    // scale, coupon precedent — NOT sourced from measurement. Matches
    // the reference range for small primate limb muscles (~5-15 cm).
    double L0m = 0.10;
    // Tendon stiffness parameter EA [N]. Declared in force units, so the
    // tendon spring constant is EA/L0t [N/m] (A8). Synthetic, monkey-
    // scale, coupon precedent — NOT sourced from measurement. Tendon
    // springs are anatomically an order of magnitude stiffer than the
    // muscle belly, which 2000 N gives at this scale.
    double EA = 2000.0;
    // Tendon slack (unloaded) length L0t [m]. Synthetic, monkey-scale,
    // coupon precedent — NOT sourced from measurement. Slightly shorter
    // than the muscle so the tendon is pre-tensioned near rest.
    double L0t = 0.09;
    // Maximal isometric muscle force Fmax [N]. Synthetic, monkey-scale,
    // coupon precedent — NOT sourced from measurement. Within the
    // reference range for small primate limb muscles.
    double Fmax = 150.0;
    // Passive tension at full stretch [N] (see F_passive below).
    // Synthetic, monkey-scale, coupon precedent — NOT sourced from
    // measurement. Reference notes passive force well below Fmax.
    double Fpassive = 5.0;
    // Activation time constant tau_a [s]. Synthetic, monkey-scale,
    // coupon precedent — NOT sourced from measurement. Reference gives
    // muscle activation time constants of tens to hundreds of ms.
    double tau_a = 0.05;
    // Capsule rotational stiffness k_capsule [N*m/rad]; torque is
    // tau = -dU/dtheta of U = 0.5*k*(q-theta_rest)^2 (A5). Synthetic,
    // monkey-scale, coupon precedent — NOT sourced from measurement.
    double k_capsule = 2.0;
    // Rest joint angle theta_rest [rad]. Synthetic, monkey-scale, coupon
    // precedent — NOT sourced from measurement. Mid-range neutral.
    double theta_rest = 0.0;
    // Lower range-of-motion stop [rad]. Synthetic, monkey-scale, coupon
    // precedent — NOT sourced from measurement. ~-131 deg, knee-like.
    double rom_lo = -2.29;
    // Upper range-of-motion stop [rad]. Synthetic, monkey-scale, coupon
    // precedent — NOT sourced from measurement. ~147 deg, knee-like.
    double rom_hi = 2.56;
    // Viscous joint damping c [N*m*s/rad]. Synthetic, monkey-scale,
    // coupon precedent — NOT sourced from measurement. Light damping so
    // motion settles within a few seconds.
    double c = 0.05;
    // Activation (metabolic incl. stall) heat rate at full activation
    // [W]. Synthetic, monkey-scale, coupon precedent — NOT sourced from
    // measurement. Chosen so an obstructed muscle visibly consumes the
    // battery (A7 stall falsifier: obstructed muscle still consumes).
    double heat_rate = 2.0;
    // Battery capacity / initial charge [J]. Synthetic, monkey-scale,
    // coupon precedent — NOT sourced from measurement. Generous so the
    // battery never depletes inside a test run.
    double battery_J0 = 1000.0;
    // Fixed internal integration step [s]. Synthetic, monkey-scale,
    // coupon precedent — NOT sourced from measurement. 300 Hz keeps the
    // stiff tendon spring (EA/L0t ~ 22 kN/m) stable under semi-implicit
    // Euler at this inertia.
    double dt_internal = 1.0 / 300.0;
};
// Running state of one muscle->tendon->joint drive. Plain data, no heap.
struct TendonDriveState {
    double q = 0.0;            // joint angle [rad]
    double qd = 0.0;           // joint angular velocity [rad/s]
    double a = 0.0;            // activation, clamped to [0,1]
    double battery_J = 0.0;    // remaining stored energy [J] (A1 ledger)
    double work_muscle_J = 0.0; // cumulative concentric work out of muscle [J]
    double heat_J = 0.0;       // metabolic + elastic-recoil heat [J]
    double elastic_J = 0.0;    // current stored elastic energy (tendon+capsule) [J]
    bool   severed = false;    // tendon transmission broken (A8 falsifier)
    double accumulator = 0.0;  // leftover real time not yet integrated [s]
};
namespace detail {

// A8 tendon: F = (EA/L0t) * max(0, L - L0t). EA is declared in [N], so
// EA/L0t is the spring constant [N/m]; tension only, never compression.
inline double tendon_tension_n(const TendonDriveParams& p,
                               const TendonDriveState& s) {
    if (s.severed) return 0.0;
    const double L = p.L0m - p.r * s.q; // muscle-tendon unit length model
    const double stretch = L - p.L0t;
    return (stretch > 0.0) ? (p.EA / p.L0t) * stretch : 0.0;
}

// Stored elastic energy [J]: capsule (A5) + tendon (A8). A severed tendon
// stores nothing; its recoil is booked to heat at the sever step.
inline double elastic_energy_j(const TendonDriveParams& p,
                               const TendonDriveState& s) {
    const double cap = 0.5 * p.k_capsule * (s.q - p.theta_rest) *
                                   (s.q - p.theta_rest);
    if (s.severed) return cap;
    const double L = p.L0m - p.r * s.q;
    const double stretch = (L - p.L0t > 0.0) ? (L - p.L0t) : 0.0;
    return cap + 0.5 * (p.EA / p.L0t) * stretch * stretch;
}

// One fixed internal step. u = command [0,1], tau_ext = external joint
// torque [N*m]. Energy ledger (battery side) closes exactly per step:
//   drain = w + h + dE, with w,h >= 0 and recoil (dE<0) folded into h,
// so the battery never recharges and the invariant telescopes.
inline void step_internal(const TendonDriveParams& p, TendonDriveState& s,
                          double u, double tau_ext) {
    const double dt = p.dt_internal;
    const double e_old = elastic_energy_j(p, s);

    // A7 muscle: activation low-pass toward command, clamped to [0,1].
    s.a += (u - s.a) * dt / p.tau_a;
    if (s.a < 0.0) s.a = 0.0;
    if (s.a > 1.0) s.a = 1.0;

    // A7 muscle force: F = a*Fmax + F_passive. fL = fV = 1 declared
    // simplification (no length/tension or force/velocity curve).
    // Passive tension only on stretch beyond L0m, ramping over 2 cm.
    const double L = p.L0m - p.r * s.q;
    double strain = (L - p.L0m) / 0.02;
    if (strain < 0.0) strain = 0.0;
    if (strain > 1.0) strain = 1.0;
    const double f_muscle = s.a * p.Fmax + p.Fpassive * strain;

    // A8 tendon is the transmission path: severed => no torque reaches
    // the joint and the tendon stores/releases nothing further.
    const double tau_act = s.severed ? 0.0 : f_muscle * p.r;

    // A5 capsule: tau = -dU/dtheta = -k*(q - theta_rest); plus damping
    // and external torque. I*qdd = tau; semi-implicit Euler.
    const double tau = tau_act - p.k_capsule * (s.q - p.theta_rest) -
                       p.c * s.qd + tau_ext;
    s.qd += (tau / p.I) * dt;
    s.q += s.qd * dt;

    // Unilateral ROM stops: clamp q, kill outward velocity. Impact KE is
    // dissipated joint-side (not a battery cost) — declared simplification.
    if (s.q > p.rom_hi) { s.q = p.rom_hi; if (s.qd > 0.0) s.qd = 0.0; }
    if (s.q < p.rom_lo) { s.q = p.rom_lo; if (s.qd < 0.0) s.qd = 0.0; }

    // Battery-side ledger terms. w: concentric work out of the muscle.
    // h: metabolic heat incl. stall cost (a*heat_rate*dt) + elastic
    // recoil dissipation. drain = w + h + dE >= 0 always.
    const double e_new = elastic_energy_j(p, s);
    const double de = e_new - e_old;
    const double dw_mech = tau_act * s.qd * dt;
    const double w = (dw_mech > 0.0) ? dw_mech : 0.0;
    const double recoil = (de < 0.0) ? -de : 0.0;
    const double h = s.a * p.heat_rate * dt + recoil;
    s.work_muscle_J += w;
    s.heat_J += h;
    s.battery_J -= (w + h + de);
    s.elastic_J = e_new;
}

} // namespace detail
// Initialize a drive at joint angle q0 [rad]: full battery, zero motion,
// zero activation, UNSEVERED. ROUND-13 LEDGER CONTINUITY FIX:
// (1) severed is cleared BEFORE the elastic baseline is computed. The old
//     order computed elastic_energy_j with a stale severed==true flag, so
//     arming from a previously-severed state booked a capsule-only baseline
//     (0 at q=0) while the first step_internal measured e_old UNSEVERED and
//     therefore included the tendon pretension 0.5*(EA/L0t)*(L0m-L0t)^2
//     = 10/9 J. That 1.1111 J appeared in reported elastic_J without ever
//     being booked to the battery: unbooked energy creation at arm time,
//     which the per-frame A1 guard correctly flagged (round-12 repro).
// (2) q0 lets the engine arm at the CURRENT joint angle instead of
//     teleporting the limb to the fixed rest q=0; the drive's elastic
//     baseline then reflects the pose the limb is actually in.
inline void tendon_drive_init_at(const TendonDriveParams& p,
                                 TendonDriveState& s, double q0) {
    s.severed = false;
    s.q = q0; s.qd = 0.0; s.a = 0.0;
    s.battery_J = p.battery_J0;
    s.work_muscle_J = 0.0; s.heat_J = 0.0;
    s.elastic_J = detail::elastic_energy_j(p, s);
    s.accumulator = 0.0;
}

// Initialize a resting drive: full battery, zero motion, zero activation,
// at the rest angle q = 0. Byte-identical to the pre-round-13 init for any
// starting state (the severed-flag ordering fix only changes the result for
// a stale severed==true input, which was the bug).
inline void tendon_drive_init(const TendonDriveParams& p,
                              TendonDriveState& s) {
    tendon_drive_init_at(p, s, 0.0);
}

// Public step: accumulate real time, run fixed internal steps. Bounded
// substep count keeps a pathological real_dt deterministic and finite.
inline void tendon_drive_step(const TendonDriveParams& p,
                              TendonDriveState& s,
                              double u, double tau_ext, double real_dt) {
    if (real_dt > 0.0) s.accumulator += real_dt;
    int guard = 100000;
    while (s.accumulator >= p.dt_internal && guard-- > 0) {
        detail::step_internal(p, s, u, tau_ext);
        s.accumulator -= p.dt_internal;
    }
}

// A8 tendon tension [N]; zero once severed (transmission falsifier).
inline double tendon_force_n(const TendonDriveParams& p,
                             const TendonDriveState& s) {
    return detail::tendon_tension_n(p, s);
}

// Torque the muscle delivers across the joint [N*m]; zero once severed.
// Mirrors the force law inside step_internal (keep in sync).
inline double tendon_actuation_torque_nm(const TendonDriveParams& p,
                                         const TendonDriveState& s) {
    if (s.severed) return 0.0;
    const double L = p.L0m - p.r * s.q;
    double strain = (L - p.L0m) / 0.02;
    if (strain < 0.0) strain = 0.0;
    if (strain > 1.0) strain = 1.0;
    return (s.a * p.Fmax + p.Fpassive * strain) * p.r;
}

// Current stored elastic energy (tendon + capsule) [J].
inline double tendon_elastic_J(const TendonDriveParams& p,
                               const TendonDriveState& s) {
    return detail::elastic_energy_j(p, s);
}

// Ledger check: battery drain must equal work + heat + delta_elastic,
// where expected_total_J is the caller's sum of those three terms.
inline bool ledger_ok(const TendonDriveParams& p, const TendonDriveState& s,
                      double expected_total_J, double tol) {
    const double drain = p.battery_J0 - s.battery_J;
    return std::fabs(drain - expected_total_J) <= tol;
}

} // namespace tendon
} // namespace chimera
#endif // CHIMERA_TENDON_DRIVE_HPP
