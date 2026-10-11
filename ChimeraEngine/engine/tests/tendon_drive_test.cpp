// ChimeraEngine/engine/tests/tendon_drive_test.cpp
// Standalone tests for the tendon-drive module (no engine, no gtest).
// Build:
//   g++ -std=c++17 -O2 -I ChimeraEngine/engine
//       ChimeraEngine/engine/tests/tendon_drive_test.cpp -o .tmp/tendon_test.exe
#include "tendon_drive.hpp"

#include <cstdarg>
#include <cmath>
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

static double drain_j(const TendonDriveParams& p, const TendonDriveState& s) {
    return p.battery_J0 - s.battery_J;
}

// |battery drain - (work + heat + delta_elastic)|, the ledger invariant.
static double ledger_err(const TendonDriveParams& p, const TendonDriveState& s,
                         double elastic0_j) {
    const double expected = s.work_muscle_J + s.heat_J +
        (td::tendon_elastic_J(p, s) - elastic0_j);
    return std::fabs(drain_j(p, s) - expected);
}

static void run_s(TendonDriveParams& p, TendonDriveState& s, double u,
                  double tau_ext, double seconds) {
    const double frame = 1.0 / 240.0;
    const int n = static_cast<int>(seconds / frame + 0.5);
    for (int i = 0; i < n; ++i) td::tendon_drive_step(p, s, u, tau_ext, frame);
}

// Test 1: LEDGER — u=1 for 3 s, battery ledger closes to 1e-9 J.
static void test_ledger() {
    TendonDriveParams p;
    TendonDriveState s;
    td::tendon_drive_init(p, s);
    const double e0 = td::tendon_elastic_J(p, s);
    run_s(p, s, 1.0, 0.0, 3.0);
    const double err = ledger_err(p, s, e0);
    report("LEDGER", err < 1e-9,
           "ledger_err=%.3e J (tol 1e-9), drain=%.6f J work=%.6f J "
           "heat=%.6f J dE=%.6f J",
           err, drain_j(p, s), s.work_muscle_J, s.heat_J,
           td::tendon_elastic_J(p, s) - e0);
}
// Test 2: SEVER — after severing, tendon force and actuation torque go to
// zero within one internal step, q decays toward theta_rest, and the
// actuation part of the battery drain stops (A8 falsifier).
static void test_sever() {
    TendonDriveParams p;
    TendonDriveState s;
    td::tendon_drive_init(p, s);
    const double e0 = td::tendon_elastic_J(p, s);
    run_s(p, s, 1.0, 0.0, 0.5);
    const double d0 = drain_j(p, s);
    run_s(p, s, 1.0, 0.0, 0.5);
    const double drain_before = drain_j(p, s) - d0;
    s.severed = true;
    td::tendon_drive_step(p, s, 1.0, 0.0, p.dt_internal); // one step
    const double f_after = td::tendon_force_n(p, s);
    const double t_after = td::tendon_actuation_torque_nm(p, s);
    const double q_sev = s.q, w_sev = s.work_muscle_J;
    run_s(p, s, 1.0, 0.0, 2.0);
    const double w_drift = s.work_muscle_J - w_sev;
    const double d1 = drain_j(p, s);
    run_s(p, s, 1.0, 0.0, 0.5);
    const double drain_after = drain_j(p, s) - d1;
    const bool ok = f_after == 0.0 && t_after == 0.0 &&
                    std::fabs(s.q) < std::fabs(q_sev) && w_drift == 0.0 &&
                    drain_after < drain_before &&
                    ledger_err(p, s, e0) < 1e-9;
    report("SEVER", ok,
           "F=%.1f tau=%.1f q %.4f->%.4f(rest %.1f) dWorkPost=%.1e "
           "drain %.4f->%.4f J/0.5s ledger=%.2e",
           f_after, t_after, q_sev, s.q, p.theta_rest, w_drift,
           drain_before, drain_after, ledger_err(p, s, e0));
}

// Test 3: STALL — q held at rom_hi by an external torque; actuation
// torque is positive, mechanical work is zero, battery still drains
// (A7: an obstructed muscle consumes energy).
static void test_stall() {
    TendonDriveParams p;
    TendonDriveState s;
    td::tendon_drive_init(p, s);
    s.q = p.rom_hi;
    const double tau_ext = p.k_capsule * (p.rom_hi - p.theta_rest);
    const double e0 = td::tendon_elastic_J(p, s);
    const double w0 = s.work_muscle_J, d0 = drain_j(p, s);
    run_s(p, s, 1.0, tau_ext, 1.0);
    const double tau_act = td::tendon_actuation_torque_nm(p, s);
    const double dw = s.work_muscle_J - w0, dd = drain_j(p, s) - d0;
    const bool ok = tau_act > 0.0 && std::fabs(dw) < 1e-9 && dd > 0.0 &&
                    std::fabs(s.q - p.rom_hi) < 1e-12 &&
                    ledger_err(p, s, e0) < 1e-9;
    report("STALL", ok,
           "tau_act=%.4f Nm dWork=%.1e J drain=%.4f J q-rom_hi=%.1e "
           "ledger=%.2e",
           tau_act, dw, dd, s.q - p.rom_hi, ledger_err(p, s, e0));
}
// Test 4: REST — u=0 at q=qd=0 must stay at rest exactly.
static void test_rest() {
    TendonDriveParams p;
    TendonDriveState s;
    td::tendon_drive_init(p, s);
    run_s(p, s, 0.0, 0.0, 3.0);
    report("REST", std::fabs(s.q) < 1e-12 && std::fabs(s.qd) < 1e-12,
           "|q|=%.1e |qd|=%.1e after 3 s", std::fabs(s.q), std::fabs(s.qd));
}

// Test 5: MONOTONIC — settled q strictly increases with command u.
static void test_monotonic() {
    const double us[5] = {0.0, 0.25, 0.5, 0.75, 1.0};
    double qs[5];
    for (int i = 0; i < 5; ++i) {
        TendonDriveParams p;
        TendonDriveState s;
        td::tendon_drive_init(p, s);
        run_s(p, s, us[i], 0.0, 5.0);
        qs[i] = s.q;
    }
    bool ok = true;
    for (int i = 1; i < 5; ++i) ok = ok && qs[i] > qs[i - 1];
    report("MONOTONIC", ok,
           "q_ss = %.4f %.4f %.4f %.4f %.4f rad", qs[0], qs[1], qs[2], qs[3],
           qs[4]);
}
int main() {
    test_ledger();
    test_sever();
    test_stall();
    test_rest();
    test_monotonic();
    printf("[%s] total failures: %d\n",
           g_failures == 0 ? "PASS" : "FAIL", g_failures);
    return g_failures == 0 ? 0 : 1;
}
