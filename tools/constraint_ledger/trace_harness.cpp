// THE CONSTRAINT-LEDGER TRACE INSTRUMENT (lane agent/constraint-ledger-20260921).
// Runs the UNCHANGED walk (the gait_unit walk_run(true) recipe) and dumps the
// per-tick lossless census the compiled record replay consumes.
//
// EVIDENCE BOUNDARY (preregistration amendment-2): the substrate is READ-ONLY;
// this TU relaxes member access for OBSERVATION ONLY — the pad-center world y
// the fire capture reads is not exposed by the public status (the status
// carries the sole-segment CoP instead). Access specifiers do not affect
// layout or codegen in the Itanium/MSVC ABIs; the double-run byte-equality
// check and the refusal-tick cross-check verify the instrument.
//
// The std headers and the vendored json.hpp are pre-included BEFORE the hack
// so their textual re-includes inside the substrate headers are no-ops.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <string>
#include <utility>
#include <vector>
#include "../../ChimeraEngine/native/viewer3rd/json.hpp"
#define private public
#include "../../ChimeraEngine/engine/gait_controller.hpp"
#undef private

using namespace chimera::multibody;

static uint64_t bits_of(double d) {
    uint64_t u;
    std::memcpy(&u, &d, sizeof u);
    return u;
}

int main(int argc, char** argv) {
    if (argc < 3) {
        std::fprintf(stderr, "usage: trace_harness scene.json out.jsonl\n");
        return 2;
    }
    std::ifstream f(argv[1]);
    if (!f) { std::fprintf(stderr, "scene open failed\n"); return 2; }
    J scene; f >> scene;
    const J& data = scene.at("gait_controller");
    const J& recipe = data.at("recipe");
    const double tick_hz = number(recipe.at("tick_hz"));
    const double dt = 1.0 / tick_hz;
    const int CYCLE_TICKS = (int)std::lround(GaitWalker::T_CYCLE * tick_hz);
    const int WALK = 10 * CYCLE_TICKS;
    const double tair = (std::ceil)((GaitWalker::T_CYCLE - GaitWalker::DUTY_SAMPLED) / dt);

    std::FILE* out = std::fopen(argv[2], "wb");
    if (!out) { std::fprintf(stderr, "out open failed\n"); return 2; }

    GaitWalker d(data, 9.80665, V{0, 0, 0}, dt);
    d.configure({{"capture_enabled", true}, {"reset", true}});

    // meta row (the registered constants, dumped from the substrate itself;
    // kTouch/kReleaseBand are implicitly-private head members — their values
    // are pinned by the record constants and by the replay itself)
    std::fprintf(out,
        "{\"meta\":true,\"tick_hz\":%.17g,\"tair\":%.17g,\"T_CYCLE\":%.17g,"
        "\"DUTY_SAMPLED\":%.17g,\"TOE_OFF\":%.17g,"
        "\"cycle_ticks\":%d,\"walk_ticks\":%d}\n",
        tick_hz, tair, GaitWalker::T_CYCLE, GaitWalker::DUTY_SAMPLED,
        GaitWalker::TOE_OFF, CYCLE_TICKS, WALK);

    auto dump = [&](int j) {
        auto e = d.evaluate(d.s_);
        char line[1024];
        int n = std::snprintf(line, sizeof line, "{\"j\":%d,\"gaps\":[%.17g,%.17g,%.17g,%.17g],\"gaps_bits\":[%llu,%llu,%llu,%llu],\"touch\":[%d,%d],\"leg\":[",
            j, d.gap_of(e, 0), d.gap_of(e, 1), d.gap_of(e, 2), d.gap_of(e, 3),
            (unsigned long long)bits_of(d.gap_of(e, 0)), (unsigned long long)bits_of(d.gap_of(e, 1)),
            (unsigned long long)bits_of(d.gap_of(e, 2)), (unsigned long long)bits_of(d.gap_of(e, 3)),
            d.touching_prev_[0] ? 1 : 0, d.touching_prev_[1] ? 1 : 0);
        // per leg: the shipped decisions + the anchor inputs (pad centers)
        for (size_t hl = 0; hl < 2; ++hl) {
            double hy = e.point(d.points_[d.hind_heel_pt_[hl]].index,
                                d.points_[d.hind_heel_pt_[hl]].local).first[1];
            double my = e.point(d.points_[d.hind_mp_pt_[hl]].index,
                                d.points_[d.hind_mp_pt_[hl]].local).first[1];
            n += std::snprintf(line + n, sizeof line - n,
                "%s{\"mode\":%d,\"t\":%.17g,\"fires\":%llu,\"tds\":%llu,"
                "\"held\":%d,\"clear_tick\":%d,\"fire_class\":%d,"
                "\"plant_y\":%.17g,\"plant_y_bits\":%llu,\"phase\":%.17g,"
                "\"heel_y\":%.17g,\"heel_y_bits\":%llu,\"mp_y\":%.17g,\"mp_y_bits\":%llu,"
                "\"alt_due\":%d,\"hold_ticks\":%llu}",
                hl ? "," : "", d.hind_step_mode_[hl], d.hind_step_t_[hl],
                (unsigned long long)d.hind_step_fires_[hl], (unsigned long long)d.hind_step_tds_[hl],
                d.hind_step_held_[hl] ? 1 : 0, d.hind_step_clear_tick_[hl],
                d.hind_step_alt_[hl], d.hind_step_plant_y_[hl],
                (unsigned long long)bits_of(d.hind_step_plant_y_[hl]),
                d.phi_[hl], hy, (unsigned long long)bits_of(hy),
                my, (unsigned long long)bits_of(my),
                d.hind_step_alt_due_[hl], (unsigned long long)d.hind_step_hold_ticks_[hl]);
        }
        std::snprintf(line + n, sizeof line - n, "]}\n");
        std::fputs(line, out);
    };

    dump(0);  // the reset row (initial state; the init values are the declared ones)
    int refused_tick = -1;
    char refusal[256] = {0};
    for (int i = 0; i < WALK; ++i) {
        try {
            d.step();
        } catch (const Refusal& ex) {
            refused_tick = i;
            std::snprintf(refusal, sizeof refusal, "%s", ex.what());
            std::fprintf(stderr, "REFUSED tick %d: %s\n", i, ex.what());
            break;
        }
        dump(i + 1);  // row j = after step j-1; decisions at row j read row j-1
    }
    std::fclose(out);
    std::printf("rows=%d refused_tick=%d refusal=%s\n",
                refused_tick < 0 ? WALK : refused_tick, refused_tick, refusal);
    return 0;
}
