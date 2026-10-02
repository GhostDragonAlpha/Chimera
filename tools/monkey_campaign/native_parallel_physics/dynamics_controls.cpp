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
#include <vector>

using namespace chimera::multibody;

namespace {

CoupledDynamics make_dynamics(const J& data, double gravity, V shift,
                              double dt, std::size_t workers) {
#ifdef CHIMERA_PARALLEL_CANDIDATE
    return CoupledDynamics(data, gravity, shift, dt, workers);
#else
    (void)workers;
    return CoupledDynamics(data, gravity, shift, dt);
#endif
}

std::string double_bits(double value) {
    static_assert(sizeof(double) == sizeof(std::uint64_t), "binary64 required");
    std::uint64_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    std::ostringstream out;
    out << std::hex << std::setfill('0') << std::setw(16) << bits;
    return out.str();
}

J bitified(const J& value) {
    if (value.is_number_float()) return double_bits(value.get<double>());
    if (value.is_array()) {
        J result = J::array();
        for (const auto& item : value) result.push_back(bitified(item));
        return result;
    }
    if (value.is_object()) {
        J result = J::object();
        for (auto it = value.begin(); it != value.end(); ++it)
            result[it.key()] = bitified(it.value());
        return result;
    }
    return value;
}

void check(bool ok, const char* reason, int& checks) {
    require(ok, reason);
    ++checks;
}

bool finite_energy(const J& status) {
    for (auto it = status.at("energy").begin();
         it != status.at("energy").end(); ++it) {
        if (it.value().is_number() &&
            !std::isfinite(it.value().get<double>())) return false;
    }
    return true;
}

J final_state(const CoupledDynamics& dynamics) {
    return {{"angles_rad", dynamics.angles()}, {"speeds_rad_s", dynamics.speeds()}};
}

J verify_status(const CoupledDynamics& dynamics, int& checks) {
    const J status = dynamics.status();
    check(finite_energy(status), "nonfinite_energy", checks);
    check(number(status["energy"]["battery_J"]) >= 0, "store_negative", checks);
    for (std::size_t joint = 0; joint < dynamics.angles().size(); ++joint) {
        check(dynamics.angles()[joint] >= dynamics.model().lower[joint] - 1e-9 &&
              dynamics.angles()[joint] <= dynamics.model().upper[joint] + 1e-9,
              "source_joint_bounds", checks);
        check(std::abs(number(status["joints"][joint]["motor_torque_N_m"])) <=
              number(status["joints"][joint]["torque_limit_N_m"]) + 1e-12,
              "torque_cap", checks);
    }
    return status;
}

std::size_t parse_workers(int argc, char** argv) {
    require(argc == 2 || argc == 3, "usage_scene_fixture_optional_workers");
    if (argc == 2 || std::string(argv[2]) == "1" ||
        std::string(argv[2]) == "workers1") return 1;
    if (std::string(argv[2]) == "2" || std::string(argv[2]) == "workers2") return 2;
    if (std::string(argv[2]) == "4" || std::string(argv[2]) == "workers4") return 4;
    throw Refusal("invalid_worker_selector");
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const std::size_t workers = parse_workers(argc, argv);
        J fixture;
        std::ifstream input(argv[1]);
        require(input.good(), "scene_fixture_unreadable");
        input >> fixture;
        const J data = fixture.at("coupled_dynamics");
        // World placement of the mounted arm, same convention as the qualified
        // tests_coupled_arm native.cpp driver: scene.arm_translation_m. The
        // authored contact plane (recipe contact_plane_height_m) is world-fixed
        // and the constructor probe requires a strictly positive reset gap, so
        // the arm must be placed at the qualified earth-patch height.
        const V shift = fixture.at("scene").at("arm_translation_m").get<V>();
        int checks = 0;

        CoupledDynamics default_path(data, 9.7982854791873, shift);
        const J default_status = default_path.status();
        check(finite_energy(default_status), "default_constructor_energy", checks);

#ifdef CHIMERA_PARALLEL_CANDIDATE
        for (std::size_t invalid : {std::size_t(0), std::size_t(5)}) {
            bool refused = false;
            try {
                auto bad = make_dynamics(data, 9.81, shift, 1. / 300., invalid);
                (void)bad;
            }
            catch (const Refusal&) { refused = true; }
            require(refused, "candidate_worker_limit");
        }
#endif

        J intent_status;
        {
            auto intent = make_dynamics(data, 9.81, shift, 1. / 300., workers);
            intent.configure({{"shoulder_target_deg", -40.}, {"elbow_target_deg", 40.}});
            check(intent.angles() == intent.model().defaults && intent.speeds() == Dense(2),
                  "intent_changed_pose", checks);
            const J saved = verify_status(intent, checks);
            bool refused = false;
            try { intent.configure({{"load_N", 1.}, {"angles", J::array({0, 0})}}); }
            catch (const Refusal&) { refused = true; }
            check(refused && intent.status() == saved, "transactional_refusal", checks);
            intent_status = saved;
        }

        J tiny = data;
        tiny["recipe"]["battery_initial_J"] = 1e-5;
        J exhausted, empty_final;
        {
            auto empty = make_dynamics(tiny, 9.81, shift, 1. / 300., workers);
            for (int tick = 0; tick < 300; ++tick) {
                empty.step();
                verify_status(empty, checks);
            }
            exhausted = verify_status(empty, checks);
            check(exhausted["battery_empty_events"] == 1 &&
                  !exhausted["energy"]["battery_usable"].get<bool>(),
                  "exhaustion_event", checks);
            const double exhausted_work = number(exhausted["energy"]["actuator_work_J"]);
            for (int tick = 0; tick < 300; ++tick) {
                empty.step();
                empty_final = verify_status(empty, checks);
            }
            check(number(empty_final["energy"]["actuator_work_J"]) == exhausted_work,
                  "exhausted_motor_work", checks);
        }

        J free_state, driven_state;
        double free_elbow_speed = 0, driven_elbow_speed = 0;
        {
            auto free = make_dynamics(data, 0, shift, 1. / 300., workers);
            free.configure({{"power", false}});
            free.step();
            verify_status(free, checks);
            free_elbow_speed = free.speeds()[1];
            free_state = final_state(free);
        }
        {
            auto driven = make_dynamics(data, 0, shift, 1. / 300., workers);
            driven.configure({{"elbow_drive", false}});
            driven.step();
            verify_status(driven, checks);
            driven_elbow_speed = driven.speeds()[1];
            driven_state = final_state(driven);
        }
        check(std::abs(driven_elbow_speed - free_elbow_speed) > 1e-4,
              "cross_joint_coupling", checks);

        J refinement_states = J::array();
        std::vector<Dense> refined;
        for (int multiple : {1, 2, 4, 8}) {
            {
                auto dynamics = make_dynamics(data, 9.81, shift,
                                              1. / (300. * multiple), workers);
                dynamics.configure({{"power", false}});
                for (int tick = 0; tick < 24 * multiple; ++tick) {
                    dynamics.step();
                    verify_status(dynamics, checks);
                }
                Dense state = dynamics.angles();
                state.insert(state.end(), dynamics.speeds().begin(), dynamics.speeds().end());
                refined.push_back(std::move(state));
                refinement_states.push_back(final_state(dynamics));
            }
        }
        auto distance = [](const Dense& a, const Dense& b) {
            double sum = 0;
            for (std::size_t i = 0; i < a.size(); ++i)
                sum += (a[i] - b[i]) * (a[i] - b[i]);
            return std::sqrt(sum);
        };
        const double ratio = distance(refined[0], refined[1]) /
                             distance(refined[1], refined[2]);
        check(std::isfinite(ratio) && ratio > 12 && ratio < 20,
              "rk4_refinement", checks);

        J output = {
            {"suite", "native_coupled_dynamics_controls"},
            {"scope", "software regression fixture; no physical qualification claim"},
            {"synthetic_reduced_battery_scenario", "initial_store_1e-5_J; control only"},
            {"checks", checks}, {"rk4_refinement_ratio", ratio},
            {"default_status", default_status}, {"intent_status", intent_status},
            {"exhaustion_status", exhausted}, {"exhaustion_final_status", empty_final},
            {"cross_joint_free_state", free_state},
            {"cross_joint_driven_state", driven_state},
            {"refinement_states", refinement_states}, {"pass", true}
        };
        std::cout << bitified(output).dump() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
