#include "ChimeraEngine/engine/coupled_articulation.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <utility>
#include <vector>

using namespace chimera::multibody;

namespace {
using J = chimera::forces::json;

struct Comparison {
    std::uint64_t scalar_count = 0;

    void exact(double expected, double actual) {
        chimera::forces::require(std::memcmp(&expected, &actual, sizeof(double)) == 0,
                                 "batch_evaluation_bit_mismatch");
        ++scalar_count;
    }

    void evaluation(const Evaluation& expected, const Evaluation& actual) {
        chimera::forces::require(expected.mass.size() == actual.mass.size(), "batch_mass_size_mismatch");
        chimera::forces::require(expected.gravity.size() == actual.gravity.size(), "batch_gravity_size_mismatch");
        chimera::forces::require(expected.bias.size() == actual.bias.size(), "batch_bias_size_mismatch");
        chimera::forces::require(expected.frames.size() == actual.frames.size(), "batch_frame_count_mismatch");
        for (std::size_t i = 0; i < expected.mass.size(); ++i) exact(expected.mass[i], actual.mass[i]);
        for (std::size_t i = 0; i < expected.gravity.size(); ++i) exact(expected.gravity[i], actual.gravity[i]);
        for (std::size_t i = 0; i < expected.bias.size(); ++i) exact(expected.bias[i], actual.bias[i]);
        exact(expected.potential, actual.potential);
        for (std::size_t i = 0; i < expected.frames.size(); ++i) {
            const auto& a = expected.frames[i];
            const auto& b = actual.frames[i];
            const auto matrix = [&](const Mat& x, const Mat& y) {
                for (std::size_t k = 0; k < x.x.size(); ++k) exact(x.x[k], y.x[k]);
            };
            matrix(a.t, b.t);
            matrix(a.dt, b.dt);
            matrix(a.ddt, b.ddt);
            chimera::forces::require(a.d.size() == b.d.size(), "batch_frame_derivative_count_mismatch");
            for (std::size_t j = 0; j < a.d.size(); ++j) matrix(a.d[j], b.d[j]);
        }
    }

    void batch(const std::vector<Evaluation>& expected, const std::vector<Evaluation>& actual) {
        chimera::forces::require(expected.size() == actual.size(), "batch_evaluation_count_mismatch");
        for (std::size_t i = 0; i < expected.size(); ++i) evaluation(expected[i], actual[i]);
    }
};

std::vector<EvaluationInput> make_inputs(const Model& model, const J& cases) {
    const auto& source = cases.at("cases");
    chimera::forces::require(source.size() == 7, "batch_expected_seven_pinned_cases");
    std::vector<EvaluationInput> inputs;
    inputs.reserve(256);
    for (std::size_t request = 0; request < 256; ++request) {
        const auto& c = source.at(request % source.size());
        EvaluationInput input;
        for (const auto& name : model.names) {
            input.q.push_back(chimera::forces::number(c.at("angles_rad").at(name)));
            input.v.push_back(c.at("rates_rad_s").value(name, 0.0));
        }
        input.gravity = c.at("reference").at("gravity_m_s2").get<V>();
        inputs.push_back(std::move(input));
    }
    return inputs;
}

std::vector<Evaluation> evaluate_serial(const Model& model, const std::vector<EvaluationInput>& inputs) {
    std::vector<Evaluation> output;
    output.reserve(inputs.size());
    for (const auto& input : inputs) output.push_back(model.evaluate(input.q, input.v, input.gravity));
    return output;
}

double median(std::vector<double> values) {
    std::sort(values.begin(), values.end());
    return values.at(values.size() / 2);
}

template<class F>
double time_ms(F&& function) {
    const auto start = std::chrono::steady_clock::now();
    function();
    const auto end = std::chrono::steady_clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count();
}

J run(const J& scene, const J& cases) {
    const Model model(scene.at("coupled_dynamics").at("model"));
    const auto inputs = make_inputs(model, cases);
    Comparison comparison;

    // This remains the reference path: one owner evaluates the 256 inputs in order.
    const auto serial = evaluate_serial(model, inputs);
    chimera::forces::require(serial.size() == 256, "batch_serial_count");

    std::vector<double> serial_samples;
    for (int repeat = 0; repeat < 5; ++repeat) {
        std::vector<Evaluation> result;
        serial_samples.push_back(time_ms([&] { result = evaluate_serial(model, inputs); }));
        comparison.batch(serial, result);
    }
    const auto serial_comparison_scalar_count = comparison.scalar_count;

    J modes = J::array();
    for (const std::size_t workers : {1u, 2u, 4u}) {
        const auto comparisons_before = comparison.scalar_count;
        ContributionExecutor executor(workers);

        // The earlier shape failure must win over a later nonfinite-input failure.
        auto invalid = inputs;
        invalid[3].q.pop_back();
        invalid[9].q[0] = std::numeric_limits<double>::quiet_NaN();
        std::string refusal;
        try {
            (void)model.evaluate_independent(invalid, executor);
        } catch (const Refusal& error) {
            refusal = error.what();
        }
        chimera::forces::require(refusal == "coupled_state_shape", "batch_shape_refusal_code");
        const auto empty = model.evaluate_independent(std::vector<EvaluationInput>{}, executor);
        chimera::forces::require(empty.empty(), "batch_empty_result");

        const auto recovered = model.evaluate_independent(inputs, executor);
        comparison.batch(serial, recovered);

        // One warmup, then five measured repetitions. Timing is diagnostic only.
        const auto warmup = model.evaluate_independent(inputs, executor);
        comparison.batch(serial, warmup);
        std::vector<double> samples;
        for (int repeat = 0; repeat < 5; ++repeat) {
            std::vector<Evaluation> result;
            samples.push_back(time_ms([&] { result = model.evaluate_independent(inputs, executor); }));
            comparison.batch(serial, result);
        }
        modes.push_back({{"workers", workers}, {"median_ms", median(samples)},
                         {"samples_ms", samples},
                         {"warmup_count", 1}, {"measured_repeats", 5},
                         {"shape_refusal", refusal}, {"recovery_count", recovered.size()},
                         {"comparison_scalar_count", comparison.scalar_count - comparisons_before}});
    }
    return {
        {"schema", "chimera.native_batch_parallel_probe.v1"},
        {"pass", true}, {"request_count", inputs.size()}, {"pinned_case_count", 7},
        {"comparison_scalar_count", comparison.scalar_count},
        {"timing_is_diagnostic_only", true}, {"serial_median_ms", median(serial_samples)},
        {"serial_samples_ms", serial_samples},
        {"serial_warmup_count", 1}, {"serial_measured_repeats", 5},
        {"serial_comparison_scalar_count", serial_comparison_scalar_count}, {"modes", modes}
    };
}
}  // namespace

int main(int argc, char** argv) {
    try {
        chimera::forces::require(argc == 3, "usage_batch_probe_scene_and_reference_cases");
        J scene, cases;
        std::ifstream(argv[1], std::ios::binary) >> scene;
        std::ifstream(argv[2], std::ios::binary) >> cases;
        chimera::forces::require(scene.is_object() && cases.is_object(), "batch_probe_input_json");
        std::cout << run(scene, cases).dump() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
