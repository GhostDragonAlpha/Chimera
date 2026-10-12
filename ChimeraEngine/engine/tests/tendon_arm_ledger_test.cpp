// ChimeraEngine/engine/tests/tendon_arm_ledger_test.cpp
// Round-13: arm-transition ledger tests for the tendon-drive module.
// The shipped per-frame guard (membrane_tick.cpp ledger_guard_frame_) is
// emulated here exactly, because the module is header-only and the engine
// side is exercised live (round-13 evidence). External invariant asserted
// EVERY armed frame of every transition:
//     drain == work + heat + (elastic - elastic0)      [tol 1e-6 J]
// where drain = battery0 - battery and (battery0, elastic0) are the
// arm-time snapshots taken AFTER the re-init at the CURRENT joint angle
// (the round-13 fix). Pre-fix, arm-from-limp/severed showed a constant
// 1.1111 J error on every armed frame (round-12 repro); the
// SENSITIVITY test below proves this harness would have caught it.
// Build:
//   g++ -std=c++17 -O2 -I ChimeraEngine/engine
//       ChimeraEngine/engine/tests/tendon_arm_ledger_test.cpp -o .tmp/tendon_arm_test.exe
#include "tendon_drive.hpp"

#include <cstdarg>
#include <cmath>
#include <cstdint>
#include <cstdio>

using chimera::tendon::TendonDriveParams;
using chimera::tendon::TendonDriveState;
namespace td = chimera::tendon;

static int g_failures = 0;

static void report(const char* name, bool ok, const char* fmt, ...) {
    printf("[%s] %s: ", ok ? "PASS" : "FAIL", name);
    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
    printf("\n");
    if (!ok) ++g_failures;
}

// ── Emulation of the engine's arm session (membrane_tick.cpp) ───────────
struct Session {
    TendonDriveParams p;
    TendonDriveState  s;
    double joint_q = 0.0;          // the pin's current angle (joint_deg_)
    double battery0_J = 0.0, elastic0_J = 0.0;
    uint64_t frames = 0, violations = 0;
    double max_err_J = 0.0;
    bool   armed = false;

    // MembraneTick::tendon_reset_ (round-13): re-init at the CURRENT joint
    // angle; guard baselines snapshotted AFTER the re-init.
    void reset() {
        armed = false;
        td::tendon_drive_init_at(p, s, joint_q);
        battery0_J = s.battery_J;
        elastic0_J = s.elastic_J;
        frames = 0; violations = 0; max_err_J = 0.0;
    }
    void arm(double /*u*/) { reset(); armed = true; }
    void disarm() { armed = false; }   // freeze state for the ledger read

    // One armed engine frame: step, write the pin, guard (same order).
    void frame(double u, double dt) {
        td::tendon_drive_step(p, s, u, 0.0, dt);
        joint_q = s.q;
        const double drain = battery0_J - s.battery_J;
        const double expected = s.work_muscle_J + s.heat_J +
                                (s.elastic_J - elastic0_J);
        const double err = std::fabs(drain - expected);
        if (err > max_err_J) max_err_J = err;
        ++frames;
        if (err > 1e-6) ++violations;
    }
    void run(double u, double seconds) {
        const double dt = 1.0 / 60.0;                    // engine tick
        const int n = static_cast<int>(seconds / dt + 0.5);
        for (int i = 0; i < n; ++i) frame(u, dt);
    }
};

static double pretension_j(const TendonDriveParams& p) {
    const double stretch = p.L0m - p.L0t;                // at q = 0
    return 0.5 * (p.EA / p.L0t) * stretch * stretch;     // = 10/9 J
}

// Test 1: FROM REST — fresh binding (joint q = 0), arm, run. Clean, and
// the arm-time baseline is byte-identical to the pre-fix rest init
// (falsifier: arm-from-rest numbers must not change).
static void test_from_rest() {
    Session x;
    x.arm(0.6);
    const double e0 = x.elastic0_J;
    x.run(0.6, 1.5);
    const bool baseline_ok = std::fabs(e0 - pretension_j(x.p)) < 1e-12 &&
                             x.s.q != 0.0;   // it actually ran
    report("FROM_REST", x.violations == 0 && x.max_err_J < 1e-6 && baseline_ok,
           "violations=%llu max_err=%.3e J (tol 1e-6), elastic0=%.16f J "
           "(10/9=%.16f J), frames=%llu",
           (unsigned long long)x.violations, x.max_err_J, e0,
           pretension_j(x.p), (unsigned long long)x.frames);
}

// Test 2: FROM LIMP — arm, sever, settle at zero activation, disarm, then
// RE-ARM from the limp pose. Pre-fix: violations == frames, constant
// 1.1111 J error (round-12 B_after_arm_from_limp).
static void test_from_limp() {
    Session x;
    x.arm(1.0);
    x.run(1.0, 1.5);
    x.s.severed = true;                 // /tick_sever
    x.run(0.0, 3.5);                    // limp settle, zero activation
    x.disarm();                         // frozen severed state, q != 0
    const double q_limp = x.joint_q;
    x.arm(0.6);                         // re-arm from the limp pose
    const bool baseline_tracks_pose =   // checked at ARM TIME, before run
        std::fabs(x.elastic0_J - td::tendon_elastic_J(x.p, x.s)) < 1e-12;
    x.run(0.6, 1.5);
    report("FROM_LIMP", x.violations == 0 && x.max_err_J < 1e-6 &&
           baseline_tracks_pose && !x.s.severed,
           "violations=%llu max_err=%.3e J (tol 1e-6), q_limp=%.4f rad, "
           "elastic0=%.6f J, severed_after_arm=%d, frames=%llu",
           (unsigned long long)x.violations, x.max_err_J, q_limp,
           x.elastic0_J, (int)x.s.severed, (unsigned long long)x.frames);
}

// Test 3: FROM SEVERED — disarm straight out of a severed session (no
// settle) and re-arm: the init must clear severed BEFORE the baseline, so
// elastic0 is the FULL tendon+capsule energy at the arm-time angle, not
// the capsule-only value the stale flag produced.
static void test_from_severed() {
    Session x;
    x.arm(1.0);
    x.run(1.0, 1.0);
    x.s.severed = true;
    x.run(0.0, 0.5);
    x.disarm();
    const double q0 = x.joint_q;
    x.arm(0.6);
    // Expected baseline computed independently at the arm-time pose:
    const double cap = 0.5 * x.p.k_capsule * (q0 - x.p.theta_rest) *
                       (q0 - x.p.theta_rest);
    const double L = x.p.L0m - x.p.r * q0;
    const double st = (L - x.p.L0t > 0.0) ? (L - x.p.L0t) : 0.0;
    const double want = cap + 0.5 * (x.p.EA / x.p.L0t) * st * st;
    x.run(0.6, 1.5);
    report("FROM_SEVERED", x.violations == 0 && x.max_err_J < 1e-6 &&
           std::fabs(x.elastic0_J - want) < 1e-12 && !x.s.severed,
           "violations=%llu max_err=%.3e J (tol 1e-6), elastic0=%.6f J, "
           "expected_full_elastic=%.6f J (capsule-only would be %.6f J)",
           (unsigned long long)x.violations, x.max_err_J, x.elastic0_J, want,
           cap);
}

// Test 4: DISARM + RE-ARM (unsevered) — session 2 baselines restart from
// the frozen pin angle; both sessions close the ledger.
static void test_disarm_rearm() {
    Session x;
    x.arm(0.8);
    x.run(0.8, 1.0);
    x.disarm();
    const double q_frozen = x.joint_q;
    x.arm(0.6);
    const bool q0_ok = std::fabs(x.s.q - q_frozen) < 1e-15;
    const uint64_t f0 = x.frames;   // must be 0: counters restart
    x.run(0.6, 1.5);
    report("DISARM_REARM", x.violations == 0 && x.max_err_J < 1e-6 &&
           q0_ok && f0 == 0,
           "violations=%llu max_err=%.3e J (tol 1e-6), re-arm q=%.6f rad "
           "== frozen pin q, session2 counters restarted=%d",
           (unsigned long long)x.violations, x.max_err_J, x.s.q, (int)(f0 == 0));
}

// Test 5: SENSITIVITY — emulate the PRE-FIX baseline (stale-severed,
// capsule-only at q=0) on the limp re-arm and confirm this harness would
// have caught the round-12 bug (constant ~1.1111 J, every frame).
static void test_sensitivity() {
    Session x;
    x.arm(1.0);
    x.run(1.0, 1.5);
    x.s.severed = true;
    x.run(0.0, 3.5);
    x.disarm();
    // Pre-fix re-init: q forced to 0, baseline computed with the stale
    // severed flag (capsule only at q=0, theta_rest=0 -> 0 J).
    td::tendon_drive_init(x.p, x.s);          // q=0, severed cleared AFTER
    TendonDriveState stale = x.s;             // reproduce the old order:
    stale.severed = true;                     // flag still set at baseline
    const double old_baseline = td::tendon_elastic_J(x.p, stale);  // capsule-only
    x.battery0_J = x.s.battery_J;
    x.elastic0_J = old_baseline;              // the BUGGY baseline
    x.frames = 0; x.violations = 0; x.max_err_J = 0.0;
    x.joint_q = 0.0;
    x.run(0.6, 1.5);
    const double pret = pretension_j(x.p);
    const bool fired = x.violations == x.frames && x.frames > 0 &&
                       std::fabs(x.max_err_J - pret) < 1e-3;
    report("SENSITIVITY", fired,
           "pre-fix baseline reproduces the bug: violations=%llu/%llu "
           "(every frame), max_err=%.10f J ~= pretension %.10f J",
           (unsigned long long)x.violations, (unsigned long long)x.frames,
           x.max_err_J, pret);
}

int main() {
    test_from_rest();
    test_from_limp();
    test_from_severed();
    test_disarm_rearm();
    test_sensitivity();
    printf("[%s] total failures: %d\n",
           g_failures == 0 ? "PASS" : "FAIL", g_failures);
    return g_failures == 0 ? 0 : 1;
}
