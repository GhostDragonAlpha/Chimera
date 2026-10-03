// membrane_gate.cpp -- the whole-game gate capture of the REAL per-tick
// combine-core consumer (PREREGISTERED; see PREREGISTRATION.md in this
// directory).
//
// Drives MembraneTick::step() -- the ordered-pass tail whose fall pass is the
// first routed consumer of the deterministic combine core (combine_core.hpp,
// over the PR #319 contribution_executor.hpp seam) -- over a deterministic
// synthetic membrane scene, and captures a byte-stable projection of every
// tick: the fall scalars, the tick's combine receipt, and the full verts9
// stream in C99 hexfloat. The capture is the qualification artifact: the
// gate's verdict is BYTE-IDENTITY of this stream across worker counts and
// against the unwired baseline, per compiler.
//
// Also proves the lifted core's mechanism laws in-engine (the approved
// Python fixtures' counterpart): owner-routed writes, non-owner refusal,
// double-write refusal, undeclared-output refusal, and the 4-worker budget
// refusal. Determinism is the only claim; no physics claim is made.
//
// stdout only; no wall-clock, no addresses, no locale-dependent formatting.
#include "membrane_tick.hpp"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <string>
#include <vector>

#include "combine_core.hpp"

namespace {

constexpr float kDt = 1.f / 60.f;         // pinned capture timestep
constexpr int kDefaultTicks = 180;        // 3 s: fall + penalty-spring settle

// A deterministic synthetic membrane: nx x nz grid, two triangles per cell.
// All generation is integer/float arithmetic on constants -- no library
// randomness anywhere.
constexpr int kNX = 9, kNZ = 7;

void build_scene(std::vector<uint32_t>& indices, std::vector<float>& verts9) {
    const int nv = kNX * kNZ;
    verts9.assign((size_t)nv * 9, 0.f);
    for (int z = 0; z < kNZ; ++z) {
        for (int x = 0; x < kNX; ++x) {
            const size_t v = (size_t)(z * kNX + x);
            // Pinned constants: authored rest slightly ABOVE the floor so
            // the fall pass engages with a nonzero penalty depth.
            verts9[v * 9 + 0] = -0.06f + 0.015f * (float)x;
            verts9[v * 9 + 1] = 0.02f + 0.0005f * (float)((x * 7 + z * 3) % 5);
            verts9[v * 9 + 2] = -0.045f + 0.015f * (float)z;
            verts9[v * 9 + 3] = 0.f;
            verts9[v * 9 + 4] = 1.f;
            verts9[v * 9 + 5] = 0.f;
            verts9[v * 9 + 6] = 0.5f;
            verts9[v * 9 + 7] = 0.5f;
            verts9[v * 9 + 8] = 0.5f;
        }
    }
    indices.clear();
    for (int z = 0; z + 1 < kNZ; ++z) {
        for (int x = 0; x + 1 < kNX; ++x) {
            const uint32_t a = (uint32_t)(z * kNX + x);
            const uint32_t b = (uint32_t)(z * kNX + x + 1);
            const uint32_t c = (uint32_t)((z + 1) * kNX + x);
            const uint32_t d = (uint32_t)((z + 1) * kNX + x + 1);
            indices.push_back(a); indices.push_back(c); indices.push_back(b);
            indices.push_back(b); indices.push_back(c); indices.push_back(d);
        }
    }
}

std::string combine_mechanism_checks() {
    // The lifted core's refusal laws, exercised in-engine (deterministic).
    std::string out;
    // 1. non-owner write refused, store byte-identical.
    {
        chimera::combine::OwnedStateStore store;
        store.register_state("gate.state", "membrane.pass.fall");
        const std::string before = store.canonical_bytes();
        bool refused = false;
        try {
            store.apply("gate.state", 1.0, "membrane.pass.gait");
        } catch (const chimera::combine::Refusal& r) {
            refused = r.code() == "combine_non_owner_write";
        }
        out += "non_owner_write=";
        out += refused && store.canonical_bytes() == before ? "pass" : "FAIL";
        out += ";";
    }
    // 2. double-write refused across two contributions claiming one state.
    {
        chimera::combine::OwnedStateStore store;
        store.register_state("gate.shared", "membrane.pass.fall");
        chimera::combine::Contribution a, b;
        a.contribution_id = "gate.a"; a.owner_membrane = "membrane.pass.fall";
        a.produces = {"gate.shared"};
        a.compute = [](std::size_t) {
            chimera::combine::ContributionResult r;
            r.states["gate.shared"] = 1.0; return r; };
        b.contribution_id = "gate.b"; b.owner_membrane = "membrane.pass.fall";
        b.produces = {"gate.shared"};
        b.compute = [](std::size_t) {
            chimera::combine::ContributionResult r;
            r.states["gate.shared"] = 2.0; return r; };
        chimera::combine::CombineScheduler scheduler({a, b}, nullptr, store);
        bool refused = false;
        try {
            scheduler.run_window();
        } catch (const chimera::combine::Refusal& r) {
            refused = r.code() == "combine_double_state_write";
        }
        out += "double_write=";
        out += refused ? "pass" : "FAIL";
        out += ";";
    }
    // 3. undeclared output refused (frozen produces).
    {
        chimera::combine::OwnedStateStore store;
        store.register_state("gate.known", "membrane.pass.fall");
        chimera::combine::Contribution a;
        a.contribution_id = "gate.a"; a.owner_membrane = "membrane.pass.fall";
        a.produces = {"gate.known"};
        a.compute = [](std::size_t) {
            chimera::combine::ContributionResult r;
            r.states["gate.undeclared"] = 1.0; return r; };
        chimera::combine::CombineScheduler scheduler({a}, nullptr, store);
        bool refused = false;
        try {
            scheduler.run_window();
        } catch (const chimera::combine::Refusal& r) {
            refused = r.code() == "combine_undeclared_contribution_output";
        }
        out += "undeclared_output=";
        out += refused ? "pass" : "FAIL";
        out += ";";
    }
    // 4. thread budget: the engine setter refuses >4 and keeps the count.
    {
#ifdef MEMBRANE_GATE_BASELINE
        out += "thread_budget=skip_baseline;";
#else
        MembraneTick tick;
        const bool refused_high = !tick.set_contribution_workers(5);
        out += "thread_budget=";
        out += refused_high && tick.contribution_workers() == 1 ? "pass"
                                                               : "FAIL";
        out += ";";
#endif
    }
    return out;
}

// The material payload parity check: the engine's compiled membrane material
// constants must bit-match tools/material_iface's first-consumer payload
// (tools/engine_material_bridge.py emits it; see that module's provenance).
// This is the consumer loop: the validated preset is the parameter SOURCE;
// drift on either side refuses by name.
bool check_material_payload(const char* path, std::string& detail) {
    FILE* fh = std::fopen(path, "rb");
    if (!fh) {
        detail = "engine_material_payload_unreadable";
        return false;
    }
    std::string text;
    char buf[4096];
    size_t got;
    while ((got = std::fread(buf, 1, sizeof(buf), fh)) > 0) text.append(buf, got);
    std::fclose(fh);
    struct Pin {
        const char* key;
        float compiled;
    };
    const float sigma = 4000.f;    // membrane_tick.hpp skin working tension
    const float r0 = 0.03f;        // falloff radius
    const float tau = 0.5f;        // stress relaxation time
    const Pin pins[] = {
        {"\"sigma_n_per_m\":", sigma},
        {"\"press_falloff_radius_m\":", r0},
        {"\"stress_relaxation_time_s\":", tau},
    };
    for (const auto& pin : pins) {
        const std::string key = pin.key;
        const auto at = text.find(key);
        if (at == std::string::npos) {
            detail = std::string("engine_material_payload_missing_") +
                     (pin.key + 1);
            return false;
        }
        // Canonical payload shape: "key":{"engine_pin":...,"unit":...,
        // "value":"0x1..."} -- step to the nested "value":" hexfloat.
        const auto vkey = text.find("\"value\":\"", at);
        if (vkey == std::string::npos || vkey > at + key.size() + 240) {
            detail = "engine_material_payload_value_not_hexfloat_string";
            return false;
        }
        const char* raw =
            text.c_str() + vkey + std::strlen("\"value\":\"");
        const double parsed = std::strtod(raw, nullptr);
        const float value = (float)parsed;
        std::uint32_t bits_value, bits_compiled;
        std::memcpy(&bits_value, &value, 4);
        std::memcpy(&bits_compiled, &pin.compiled, 4);
        if (bits_value != bits_compiled) {
            char row[160];
            std::snprintf(row, sizeof(row),
                          "engine_material_payload_drift key=%s "
                          "payload_bits=%08x compiled_bits=%08x",
                          pin.key, bits_value, bits_compiled);
            detail = row;
            return false;
        }
    }
    detail = "engine_material_payload_parity=pass";
    return true;
}

}  // namespace

int main(int argc, char** argv) {
    const int workers = argc > 1 ? std::atoi(argv[1]) : 1;
    const int ticks = argc > 2 ? std::atoi(argv[2]) : kDefaultTicks;
    const char* payload_path = argc > 3 ? argv[3]
                                        : "engine_material_payload.json";
    if (workers < 1 || workers > 4) {
        std::printf("GATE refuse=combine_thread_budget_exceeded\n");
        return 2;
    }
    if (ticks < 1 || ticks > 3000) {
        std::printf("GATE refuse=gate_tick_count_out_of_range\n");
        return 2;
    }

    std::printf("GATE schema=chimera.engine_wiring_gate_capture.v1\n");
    std::printf("GATE workers=%d ticks=%d dt=%a\n", workers, ticks, kDt);

    // Material payload parity (the material_iface first-consumer loop).
    std::string payload_detail;
    const bool payload_ok =
        check_material_payload(payload_path, payload_detail);
    std::printf("GATE %s\n", payload_detail.c_str());
    if (!payload_ok) return 2;

    // Mechanism-law checks (deterministic; a FAIL fails the gate).
    const std::string checks = combine_mechanism_checks();
    std::printf("GATE %s\n", checks.c_str());
    if (checks.find("FAIL") != std::string::npos) return 2;

    std::vector<uint32_t> indices;
    std::vector<float> verts9;
    build_scene(indices, verts9);

    MembraneTick tick;
    tick.init((uint32_t)(indices.size() / 3), indices, verts9);
#ifndef MEMBRANE_GATE_BASELINE
    // The wired candidate only: set the combine worker count (the baseline
    // has no such knob and always runs its single serial path).
    if (!tick.set_contribution_workers((size_t)workers)) {
        std::printf("GATE refuse=combine_worker_count_refused\n");
        return 2;
    }
#endif
    const bool gravity = tick.set_gravity(true);
    const bool stance = tick.set_stance(true);   // expected false (no
                                                 // classification on this
                                                 // synthetic scene); recorded
    const bool reflex = tick.set_reflex(true);   // armed; breathing needs a
                                                 // sealed torso cell (none)
    std::printf("GATE gravity=%d stance=%d reflex=%d\n",
                (int)gravity, (int)stance, (int)reflex);

    for (int t = 0; t < ticks; ++t) {
        tick.step(verts9, kDt);
#ifdef MEMBRANE_GATE_BASELINE
        // The unwired baseline has no combine receipt; its T line is a
        // fixed marker. Comparisons: candidate@1/2/4 FULL streams must be
        // byte-identical (primary), and candidate@1's V stream (every
        // physics float) must equal the baseline's V stream byte-for-byte
        // (serial faithfulness of the wiring).
        std::printf("T %d baseline_serial\n", t);
#else
        std::printf("T %d %s\n", t, tick.last_combine_receipt().c_str());
#endif
        std::printf("V");
        char cell[64];
        for (float f : verts9) {
            std::snprintf(cell, sizeof(cell), " %a", f);
            std::printf("%s", cell);
        }
        std::printf("\n");
    }
    std::printf("GATE end\n");
    return 0;
}
