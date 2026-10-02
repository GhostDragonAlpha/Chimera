#include "coupled_dynamics.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

using namespace chimera::multibody;

namespace {
using Result = chimera::forces::json;

std::string word_hex(std::uint64_t word) {
    std::ostringstream out;
    out << std::hex << std::setfill('0') << std::setw(16) << word;
    return out.str();
}

std::string bits(double value) {
    static_assert(sizeof(double) == sizeof(std::uint64_t), "probe_requires_binary64");
    std::uint64_t word = 0;
    std::memcpy(&word, &value, sizeof(word));
    return word_hex(word);
}

struct Probe {
    Result values = Result::array();
    Result trajectory_bits = Result::array();

    void add(const std::string& name, double value) {
        chimera::forces::require(std::isfinite(value), "probe_nonfinite_named_value");
        values.push_back(Result::array({name, bits(value)}));
    }

    void add_trace(double value) {
        chimera::forces::require(std::isfinite(value), "probe_nonfinite_trajectory_value");
        trajectory_bits.push_back(bits(value));
    }

    void check(bool condition, const char* code) const {
        chimera::forces::require(condition, code);
    }

    static bool near(double actual, double expected) {
        const double scale = (std::max)(1.0, std::abs(expected));
        return std::isfinite(actual) && std::abs(actual - expected) <= 1e-10 * scale;
    }
};

Result synthetic_pendulum() {
    Result model = {{"schema", "chimera.anatomical_assembly.v1"}, {"coordinates", Result::object()}, {"bodies", Result::array()}};
    model["coordinates"]["theta"] = {{"locked", false}, {"default_rad", 0.0}, {"range_rad", {-2.5, 2.5}}};
    Result ground = {{"name", "ground"}, {"mass_kg", 0.0}, {"mass_center_m", {0.0, 0.0, 0.0}},
                     {"inertia_kg_m2", {0.0, 0.0, 0.0, 0.0, 0.0, 0.0}}, {"joint", nullptr}};
    Result axis = {{"name", "rotation_y"}, {"coordinate", "theta"}, {"axis", {0.0, 1.0, 0.0}},
                   {"function", {{"type", "LinearFunction"}, {"coefficients", {1.0, 0.0}}}}};
    Result joint = {{"parent", "ground"}, {"parent_location_m", {0.0, 0.0, 0.0}},
                    {"parent_orientation_rad", {0.0, 0.0, 0.0}}, {"child_location_m", {0.0, 0.0, 0.0}},
                    {"child_orientation_rad", {0.0, 0.0, 0.0}}, {"axes", Result::array({axis})}};
    Result pendulum = {{"name", "pendulum"}, {"mass_kg", 2.0}, {"mass_center_m", {1.0, 0.0, 0.0}},
                       {"inertia_kg_m2", {0.2, 0.2, 0.2, 0.0, 0.0, 0.0}}, {"joint", joint}};
    model["bodies"].push_back(std::move(ground));
    model["bodies"].push_back(std::move(pendulum));
    return model;
}

void run_synthetic(Probe& probe, std::size_t workers) {
    const Result model_data = synthetic_pendulum();
    Model model(model_data);
    const double q = 0.37;
    const double v = -0.8;
    const V gravity{0.0, 0.0, -9.81};
    Evaluation e;
#ifdef CHIMERA_PARALLEL_CANDIDATE
    ContributionExecutor executor(workers);
    e = model.evaluate(Dense{q}, Dense{v}, gravity, &executor);
#else
    e = model.evaluate(Dense{q}, Dense{v}, gravity);
#endif

    constexpr double mass = 2.0;
    constexpr double length = 1.0;
    constexpr double inertia_com = 0.2;
    const double generalized_mass = inertia_com + mass * length * length;
    const double generalized_gravity = mass * 9.81 * length * std::cos(q);
    const double potential = -mass * 9.81 * length * std::sin(q);
    const double kinetic = 0.5 * generalized_mass * v * v;
    probe.check(Probe::near(e.mass.at(0), generalized_mass), "synthetic_mass_analytic");
    probe.check(Probe::near(e.gravity.at(0), generalized_gravity), "synthetic_gravity_analytic");
    probe.check(Probe::near(e.bias.at(0), 0.0), "synthetic_bias_analytic");
    probe.check(Probe::near(e.potential, potential), "synthetic_potential_analytic");
    probe.check(Probe::near(kinetic, 0.5 * v * e.mass.at(0) * v), "synthetic_kinetic_analytic");
    probe.add("synthetic.mass_kg_m2", e.mass.at(0));
    probe.add("synthetic.gravity_N_m", e.gravity.at(0));
    probe.add("synthetic.bias_N_m", e.bias.at(0));
    probe.add("synthetic.potential_J", e.potential);
    probe.add("synthetic.kinetic_J", kinetic);

    const V local{0.4, 0.0, 0.0};
    const V applied{1.25, -4.0, -3.0};
    const auto point = e.point(model.body("pendulum"), local);
    const auto generalized_force = e.force(model.body("pendulum"), local, applied);
    const double radius = local[0];
    const double expected_force = -radius * std::sin(q) * applied[0]
                                - radius * std::cos(q) * applied[2];
    probe.check(Probe::near(point.first[0], radius * std::cos(q)), "synthetic_point_x");
    probe.check(Probe::near(point.first[2], -radius * std::sin(q)), "synthetic_point_z");
    probe.check(Probe::near(point.second[0][0], -radius * std::sin(q)), "synthetic_jacobian_x");
    probe.check(Probe::near(point.second[0][2], -radius * std::cos(q)), "synthetic_jacobian_z");
    probe.check(Probe::near(generalized_force.at(0), expected_force), "synthetic_virtual_work_analytic");
    probe.check(Probe::near(generalized_force.at(0), dot(point.second[0], applied)), "synthetic_virtual_work_jacobian");
    probe.add("synthetic.point_x_m", point.first[0]);
    probe.add("synthetic.point_z_m", point.first[2]);
    probe.add("synthetic.jacobian_x_m_rad", point.second[0][0]);
    probe.add("synthetic.jacobian_z_m_rad", point.second[0][2]);
    probe.add("synthetic.generalized_force_N_m", generalized_force.at(0));
    probe.check(bits(-0.0) == "8000000000000000", "negative_zero_bit_encoding");
    probe.add("encoding.negative_zero", -0.0);
}

void run_reference_cases(Probe& probe, const Result& scene, const Result& cases, std::size_t workers) {
    Model model(scene.at("coupled_dynamics").at("model"));
    std::size_t case_index = 0;
    for (const auto& c : cases.at("cases")) {
        Dense q, v;
        for (const auto& name : model.names) {
            q.push_back(chimera::forces::number(c.at("angles_rad").at(name)));
            v.push_back(c.at("rates_rad_s").value(name, 0.0));
        }
        const auto& ref = c.at("reference");
        const V g = ref.at("gravity_m_s2").get<V>();
        Evaluation e;
#ifdef CHIMERA_PARALLEL_CANDIDATE
        ContributionExecutor executor(workers);
        e = model.evaluate(q, v, g, &executor);
#else
        e = model.evaluate(q, v, g);
#endif
        const std::size_t n = model.names.size();
        const auto prefix = std::string("reference.") + std::to_string(case_index) + ".";
        for (std::size_t i = 0; i < n; ++i) {
            const double expected_gravity = ref.at("gravity_force_N_m").at(i).get<double>();
            const double expected_bias = ref.at("bias_force_N_m").at(i).get<double>();
            probe.check(std::abs(e.gravity.at(i) - expected_gravity) < 2e-9, "native_reference_gravity");
            probe.check(std::abs(e.bias.at(i) - expected_bias) < 2e-9, "native_reference_bias");
            probe.add(prefix + "gravity." + std::to_string(i), e.gravity.at(i));
            probe.add(prefix + "bias." + std::to_string(i), e.bias.at(i));
            for (std::size_t j = 0; j < n; ++j) {
                const double expected = ref.at("mass_matrix").at(i).at(j).get<double>();
                const double actual = e.mass.at(n * i + j);
                probe.check(std::abs(actual - expected) < 2e-9, "native_reference_mass");
                probe.add(prefix + "mass." + std::to_string(i) + "." + std::to_string(j), actual);
            }
        }
        probe.check(std::abs(e.potential - ref.at("potential_J").get<double>()) < 2e-9,
                    "native_reference_potential");
        probe.add(prefix + "potential", e.potential);
        const V local = c.at("hand_local_point_m").get<V>();
        const V applied = c.at("force_world_N").get<V>();
        const auto body = model.body("hand");
        const auto point = e.point(body, local);
        const auto force = e.force(body, local, applied);
        const auto acceleration = e.acceleration(force);
        const auto expected_point = c.at("hand_world_point_m").get<V>();
        const auto expected_j = c.at("hand_jacobian_m_per_rad");
        const auto expected_force = c.at("point_generalized_force_N_m");
        const auto expected_acceleration = c.at("unconstrained_acceleration_rad_s2");
        for (std::size_t k = 0; k < 3; ++k) {
            probe.check(std::abs(point.first[k] - expected_point[k]) < 2e-9, "native_reference_point");
            probe.add(prefix + "point." + std::to_string(k), point.first[k]);
            for (std::size_t i = 0; i < n; ++i) {
                probe.check(std::abs(point.second[i][k] - expected_j[k][i].get<double>()) < 2e-9,
                            "native_reference_jacobian");
                probe.add(prefix + "jacobian." + std::to_string(k) + "." + std::to_string(i),
                          point.second[i][k]);
            }
        }
        for (std::size_t i = 0; i < n; ++i) {
            probe.check(std::abs(force.at(i) - expected_force[i].get<double>()) < 2e-9,
                        "native_reference_force");
            probe.check(std::abs(acceleration.at(i) - expected_acceleration[i].get<double>()) < 2e-9,
                        "native_reference_acceleration");
            probe.add(prefix + "force." + std::to_string(i), force.at(i));
            probe.add(prefix + "acceleration." + std::to_string(i), acceleration.at(i));
        }
        for (std::size_t body_index = 0; body_index < e.frames.size(); ++body_index) {
            const auto frame_prefix = prefix + "frame." + std::to_string(body_index) + ".";
            const auto& frame = e.frames[body_index];
            const auto add_matrix = [&](const std::string& field, const Mat& matrix) {
                for (std::size_t k = 0; k < matrix.x.size(); ++k)
                    probe.add(frame_prefix + field + "." + std::to_string(k), matrix.x[k]);
            };
            add_matrix("t", frame.t);
            add_matrix("dt", frame.dt);
            add_matrix("ddt", frame.ddt);
            for (std::size_t coordinate = 0; coordinate < frame.d.size(); ++coordinate)
                add_matrix(std::string("d.") + std::to_string(coordinate), frame.d[coordinate]);
        }
        ++case_index;
    }
    probe.check(case_index > 0, "native_reference_cases_empty");
}

void run_trajectory(Probe& probe, const Result& scene, std::size_t workers, int ticks) {
    const Result data = scene.at("coupled_dynamics");
    // World placement of the mounted arm, same convention as the qualified
    // tests_coupled_arm native.cpp driver: scene.arm_translation_m. Master's
    // authored contact plane and its unconditional reset-gap probe require the
    // qualified earth-patch placement (see AMENDMENT_SCENE.md).
    const V shift = scene.at("scene").at("arm_translation_m").get<V>();
    const std::vector<Result> configs = {
        Result{{"power", false}}, Result::object(), Result{{"shoulder_drive", false}},
        Result{{"elbow_drive", false}}, Result{{"load_N", 3.0}},
        Result{{"shoulder_target_deg", -75.0}, {"elbow_target_deg", 20.0}},
        Result{{"shoulder_target_deg", 90.0}, {"elbow_target_deg", 140.0},
               {"shoulder_torque_limit_N_m", 1.0}, {"elbow_torque_limit_N_m", 0.6}}
    };
    static const char* const energy_keys[] = {
        "kinetic_J", "gravitational_J", "mechanical_J", "actuator_work_J",
        "external_work_J", "damping_heat_J", "impact_heat_J", "brake_heat_J",
        "battery_J", "balance_error_J", "store_balance_error_J"
    };
    for (std::size_t run = 0; run < configs.size(); ++run) {
#ifdef CHIMERA_PARALLEL_CANDIDATE
        CoupledDynamics dynamics(data, 9.7982854791873, shift, 1.0 / 300.0, workers);
#else
        CoupledDynamics dynamics(data, 9.7982854791873, shift, 1.0 / 300.0);
#endif
        if (!configs[run].empty()) dynamics.configure(configs[run]);
        const std::string prefix = "trajectory." + std::to_string(run) + ".";
        double peak_balance = 0.0;
        for (int tick = 0; tick < ticks; ++tick) {
            dynamics.step();
            const Result status = dynamics.status();
            const Result& energy = status.at("energy");
            for (std::size_t i = 0; i < dynamics.angles().size(); ++i) {
                probe.check(dynamics.angles()[i] >= dynamics.model().lower[i] - 1e-9 &&
                            dynamics.angles()[i] <= dynamics.model().upper[i] + 1e-9,
                            "trajectory_source_joint_bounds");
                probe.add_trace(dynamics.angles()[i]);
                probe.add_trace(dynamics.speeds()[i]);
            }
            for (const char* key : energy_keys) {
                const double value = energy.at(key).get<double>();
                probe.add_trace(value);
                if (std::string(key) == "balance_error_J" || std::string(key) == "store_balance_error_J")
                    peak_balance = (std::max)(peak_balance, std::abs(value));
            }
            probe.check(energy.at("battery_J").get<double>() >= -1e-12, "trajectory_battery_nonnegative");
            for (const auto& joint : status.at("joints")) {
                const double torque = joint.at("motor_torque_N_m").get<double>();
                const double cap = joint.at("torque_limit_N_m").get<double>();
                probe.check(std::abs(torque) <= cap + 1e-12, "trajectory_torque_cap");
            }
        }
        probe.check(peak_balance < 1e-5, "trajectory_energy_balance");
        if (run == 0)
            probe.check(dynamics.status().at("energy").at("actuator_work_J").get<double>() == 0.0,
                        "passive_trajectory_motor_work");
        probe.add(prefix + "peak_balance_J", peak_balance);
    }
}
}  // namespace

int main(int argc, char** argv) {
    try {
        chimera::forces::require(argc >= 3 && argc <= 5,
                                 "usage_native_probe_scene_reference_cases_workers_ticks");
        const std::size_t workers = argc >= 4 ? static_cast<std::size_t>(std::stoul(argv[3])) : 1;
        const int ticks = argc == 5 ? std::stoi(argv[4]) : 300;
        chimera::forces::require(workers >= 1 && workers <= 4, "native_probe_worker_range");
        chimera::forces::require(ticks >= 1 && ticks <= 3000, "native_probe_tick_range");
#ifndef CHIMERA_PARALLEL_CANDIDATE
        chimera::forces::require(workers == 1, "baseline_requires_one_worker");
#endif
        Result scene, cases;
        std::ifstream(argv[1], std::ios::binary) >> scene;
        std::ifstream(argv[2], std::ios::binary) >> cases;
        chimera::forces::require(scene.is_object() && cases.is_object(), "native_probe_input_json");
        Probe probe;
        run_synthetic(probe, workers);
        run_reference_cases(probe, scene, cases, workers);
        run_trajectory(probe, scene, workers, ticks);
        Result output = {
            {"format", "native_parallel_physics_probe.v1"},
            {"pass", true}, {"ticks_per_configuration", ticks}, {"trajectory_configurations", 7},
            {"trajectory_bits", std::move(probe.trajectory_bits)},
            {"values", std::move(probe.values)}
        };
        std::cout << output.dump() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
