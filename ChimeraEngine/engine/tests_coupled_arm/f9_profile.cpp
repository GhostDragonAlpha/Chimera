// F9 profile probe: counts the expensive machinery per tick in the exact
// F9 windows (mounted 2000 ticks, free 2000 ticks, static-hold, frictionless).
// Counts only -- no arithmetic moves, /fp:precise-safe, no timing perturbation
// of the measured sections. Built as a separate target so the falsifier
// binary stays the measured instrument.
#include "../free_root_dynamics.hpp"
#include "../graph_earth.hpp"
#include <chrono>
#include <cstdio>
#include <iostream>
#include <fstream>
using namespace chimera::multibody;

namespace chimera::multibody {
struct F9Profile {
    unsigned long long evaluate = 0, inverse_spd = 0, gram_factor = 0, friction_solve = 0;
    unsigned long long project_rows_calls = 0, project_rows_iters = 0, rate_calls = 0;
    unsigned long long free_step_calls = 0, advance_calls = 0, impact_calls = 0;
    unsigned long long bisection_steps = 0;
    bool on = false;
    void reset() { evaluate = inverse_spd = gram_factor = friction_solve = 0;
        project_rows_calls = project_rows_iters = rate_calls = 0;
        free_step_calls = advance_calls = impact_calls = bisection_steps = 0; }
};
static F9Profile g_prof;
F9Profile* f9_profile() { return &g_prof; }
}

// Hooks: definitions of the weak-inline counters declared in the headers when
// CHIMERA_F9_PROFILE is defined. (The header declares them; we define here.)
namespace chimera::multibody {
unsigned long long* f9_evaluate_count() { return &g_prof.evaluate; }
unsigned long long* f9_inverse_spd_count() { return &g_prof.inverse_spd; }
unsigned long long* f9_gram_factor_count() { return &g_prof.gram_factor; }
unsigned long long* f9_friction_solve_count() { return &g_prof.friction_solve; }
unsigned long long* f9_project_rows_calls() { return &g_prof.project_rows_calls; }
unsigned long long* f9_project_rows_iters() { return &g_prof.project_rows_iters; }
unsigned long long* f9_rate_count() { return &g_prof.rate_calls; }
unsigned long long* f9_free_step_count() { return &g_prof.free_step_calls; }
unsigned long long* f9_advance_count() { return &g_prof.advance_calls; }
unsigned long long* f9_impact_count() { return &g_prof.impact_calls; }
unsigned long long* f9_bisection_count() { return &g_prof.bisection_steps; }
}

int main(int argc, char** argv) {
    try {
        require(argc == 2, "usage: f9_profile free_scene.json");
        J scene; std::ifstream(argv[1]) >> scene;
        J data = scene.at("coupled_free_dynamics");
        V shift = scene.at("scene").at("arm_translation_m").get<V>();
        auto report = [&](const char* tag, unsigned long long ticks, double ms) {
            std::fprintf(stderr, "PROF %s ticks=%llu ms_per_tick=%.4f evaluate=%llu eval/tick=%.1f inverse_spd=%llu inv/tick=%.2f "
                "rate=%llu rate/tick=%.1f free_step=%llu advance=%llu impact=%llu "
                "project_rows=%llu pr_iters=%llu iters/call=%.2f gram_factor=%llu friction_solve=%llu bisection_free_steps=%llu\n",
                tag, ticks, ms, g_prof.evaluate, double(g_prof.evaluate) / ticks,
                g_prof.inverse_spd, double(g_prof.inverse_spd) / ticks,
                g_prof.rate_calls, double(g_prof.rate_calls) / ticks,
                g_prof.free_step_calls, g_prof.advance_calls, g_prof.impact_calls,
                g_prof.project_rows_calls, g_prof.project_rows_iters,
                g_prof.project_rows_calls ? double(g_prof.project_rows_iters) / g_prof.project_rows_calls : 0.,
                g_prof.gram_factor, g_prof.friction_solve, g_prof.bisection_steps);
        };
        // Mounted window: the F9 protocol window (CoupledDynamics, static hold).
        { CoupledDynamics d(data.at("qualified"), 9.80665, shift); d.configure({{"power", false}});
            g_prof.reset(); auto t0 = std::chrono::steady_clock::now();
            for (int i = 0; i < 200; ++i) d.step();
            double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count() / 200.;
            report("mounted_warm", 200, ms); }
        // Free window: frictionless static hold, the F9 protocol window.
        { FreeRootDynamics d(data, 9.80665, shift); d.configure({{"power", false}, {"contact_friction", 0.}});
            g_prof.reset(); auto t0 = std::chrono::steady_clock::now();
            int done = 0;
            try { for (int i = 0; i < 200; ++i) { d.step(); ++done; } }
            catch (const Refusal&) { /* timed window may hit the fold-slide event limit */ }
            double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count() / (std::max)(done, 1);
            if (done) report("free_warm", (unsigned long long)done, ms); }
        // Free WITH friction (mu=0.6): profile the cone-solve machinery too.
        { FreeRootDynamics d(data, 9.80665, shift); d.configure({{"power", false}});
            g_prof.reset(); auto t0 = std::chrono::steady_clock::now();
            int done = 0;
            try { for (int i = 0; i < 200; ++i) { d.step(); ++done; } }
            catch (const Refusal&) {}
            double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count() / (std::max)(done, 1);
            if (done) report("free_mu", (unsigned long long)done, ms); }
        std::cout << "{\"profiled\": true}\n";
        return 0;
    } catch (const std::exception& e) { std::fprintf(stderr, "%s\n", e.what()); return 1; }
}
