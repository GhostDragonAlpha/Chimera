#ifdef CHIMERA_USE_BASELINE_CORE
#include "baseline_combine_core.hpp"
#else
#include "combine_core.hpp"
#endif

#include <algorithm>
#include <exception>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace cc = chimera::combine;
using chimera::multibody::ContributionExecutor;

namespace {

void check(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

cc::OwnedStateStore make_store() {
    cc::OwnedStateStore store;
    store.register_state("good", "owner-a");
    store.register_state("late-state", "owner-a");
    store.register_state("wrong-owner-state", "owner-b");
    store.register_state("shared", "owner-a");
    return store;
}

cc::Contribution contribution(
    std::string id, std::string owner, std::vector<std::string> produces,
    std::function<cc::ContributionResult(std::size_t)> compute) {
    return {std::move(id), std::move(owner), std::move(produces),
            std::move(compute)};
}

cc::ContributionResult result(
    std::initializer_list<std::pair<const std::string, double>> states,
    std::string ledger_id, double ledger_value) {
    cc::ContributionResult out;
    out.states.insert(states.begin(), states.end());
    out.ledger.push_back({std::move(ledger_id), "J", ledger_value});
    return out;
}

struct Snapshot {
    std::string bytes;
    std::string digest;
    std::size_t applies;
    std::string ledger;
};

Snapshot snapshot(const cc::OwnedStateStore& store,
                  const cc::CombineScheduler& scheduler) {
    return {store.canonical_bytes(), store.digest(), store.applies(),
            scheduler.ledger_digest()};
}

bool same(const Snapshot& a, const Snapshot& b) {
    return a.bytes == b.bytes && a.digest == b.digest &&
           a.applies == b.applies && a.ledger == b.ledger;
}

std::vector<cc::Contribution> refusal_case(const std::string& kind) {
    auto good = contribution(
        "a-good", "owner-a", {"good"},
        [](std::size_t) { return result({{"good", 1.25}}, "early", 2.5); });
    cc::Contribution late;
    if (kind == "undeclared") {
        late = contribution("z-late", "owner-a", {"late-state"},
            [](std::size_t) { return result({{"rogue", 9.0}}, "late", 4.0); });
    } else if (kind == "wrong_owner") {
        late = contribution("z-late", "owner-a", {"wrong-owner-state"},
            [](std::size_t) {
                return result({{"wrong-owner-state", 9.0}}, "late", 4.0);
            });
    } else if (kind == "unknown_state") {
        late = contribution("z-late", "owner-a", {"missing-state"},
            [](std::size_t) {
                return result({{"missing-state", 9.0}}, "late", 4.0);
            });
    } else if (kind == "duplicate") {
        good = contribution("a-good", "owner-a", {"good", "shared"},
            [](std::size_t) {
                return result({{"good", 1.25}, {"shared", 3.0}}, "early", 2.5);
            });
        late = contribution("z-late", "owner-a", {"shared"},
            [](std::size_t) {
                return result({{"shared", 9.0}}, "late", 4.0);
            });
    } else if (kind == "callback") {
        late = contribution("z-late", "owner-a", {"late-state"},
            [](std::size_t) -> cc::ContributionResult {
                throw cc::Refusal("test_callback_failure", "pinned late callback refusal");
            });
    } else {
        throw std::runtime_error("unknown refusal case " + kind);
    }
    return {std::move(late), std::move(good)}; // deliberately non-canonical input
}

void expect_refused_unchanged(const std::string& kind,
                              const std::string& expected_code,
                              std::size_t workers) {
    auto store = make_store();
    ContributionExecutor executor(workers);
    cc::CombineScheduler scheduler(refusal_case(kind), &executor, store);
    const auto before = snapshot(store, scheduler);
    bool refused = false;
    try {
        (void)scheduler.run_window();
    } catch (const cc::Refusal& ex) {
        refused = true;
        check(ex.code() == expected_code,
              kind + " refusal code was " + ex.code() +
                  ", expected " + expected_code);
    }
    check(refused, kind + " window unexpectedly succeeded");
    const auto after = snapshot(store, scheduler);
    check(same(before, after), kind + " refusal changed store/apply/ledger snapshot at workers=" +
                                   std::to_string(workers));
}

void baseline_discriminator() {
    auto store = make_store();
    auto contributions = refusal_case("undeclared");
    ContributionExecutor executor(1);
    cc::CombineScheduler scheduler(std::move(contributions), &executor, store);
    const auto before = snapshot(store, scheduler);
    bool refused = false;
    try {
        (void)scheduler.run_window();
    } catch (const cc::Refusal& ex) {
        refused = ex.code() == "combine_undeclared_contribution_output";
    }
    check(refused, "baseline did not produce late undeclared-output refusal");
    const auto after = snapshot(store, scheduler);
    const bool partial = before.bytes != after.bytes &&
                         before.digest != after.digest &&
                         before.applies < after.applies &&
                         before.ledger != after.ledger;
    check(partial, "baseline failed to reproduce expected late partial mutation");
    std::cout << "BASELINE_PARTIAL_MUTATION=true\n"
              << "BASELINE_APPLIES_BEFORE=" << before.applies << '\n'
              << "BASELINE_APPLIES_AFTER=" << after.applies << '\n'
              << "BASELINE_STORE_CHANGED=true\n"
              << "BASELINE_LEDGER_CHANGED=true\n";
}

struct SuccessSnapshot {
    std::string store_bytes;
    std::string store_digest;
    std::size_t applies = 0;
    std::string ledger_digest;
    std::vector<std::string> routed;
};

SuccessSnapshot run_success(std::size_t workers,
                            std::vector<cc::Contribution> contributions) {
    auto store = make_store();
    ContributionExecutor executor(workers);
    cc::CombineScheduler scheduler(std::move(contributions), &executor, store);
    auto report = scheduler.run_window();
    return {store.canonical_bytes(), store.digest(), store.applies(),
            scheduler.ledger_digest(), std::move(report.routed)};
}

void print_success_signature(const SuccessSnapshot& value) {
    std::string routed;
    for (std::size_t i = 0; i < value.routed.size(); ++i) {
        if (i) routed += ',';
        routed += value.routed[i];
    }
    std::cout << "SUCCESS_STORE_BYTES=" << value.store_bytes << '\n'
              << "SUCCESS_STORE_DIGEST=" << value.store_digest << '\n'
              << "SUCCESS_APPLIES=" << value.applies << '\n'
              << "SUCCESS_LEDGER_DIGEST=" << value.ledger_digest << '\n'
              << "SUCCESS_ROUTED=" << routed << '\n';
}

std::vector<cc::Contribution> success_contributors() {
    std::vector<cc::Contribution> cs;
    cs.push_back(contribution("c-force", "owner-a", {"good"},
        [](std::size_t) { return result({{"good", 1.0 / 3.0}}, "force", 0.125); }));
    cs.push_back(contribution("a-pressure", "owner-a", {"late-state"},
        [](std::size_t) { return result({{"late-state", -2.75}}, "pressure", -0.5); }));
    cs.push_back(contribution("b-heat", "owner-a", {"shared"},
        [](std::size_t) { return result({{"shared", 12.0}}, "heat", 3.25); }));
    return cs;
}

bool same_success(const SuccessSnapshot& a, const SuccessSnapshot& b) {
    return a.store_bytes == b.store_bytes && a.store_digest == b.store_digest &&
           a.applies == b.applies && a.ledger_digest == b.ledger_digest &&
           a.routed == b.routed;
}

void success_parity() {
    auto canonical_input = success_contributors();
    const auto expected = run_success(1, canonical_input);
    std::vector<std::vector<cc::Contribution>> permutations;
    permutations.push_back(canonical_input);
    auto reverse = canonical_input;
    std::reverse(reverse.begin(), reverse.end());
    permutations.push_back(reverse);
    auto rotate = canonical_input;
    std::rotate(rotate.begin(), rotate.begin() + 1, rotate.end());
    permutations.push_back(rotate);
    for (std::size_t workers : {1u, 2u, 4u}) {
        for (std::size_t p = 0; p < permutations.size(); ++p) {
            auto actual = run_success(workers, permutations[p]);
            check(same_success(expected, actual),
                  "accepted-window parity failed for workers=" +
                      std::to_string(workers) + " permutation=" +
                      std::to_string(p));
        }
    }
}

void same_scheduler_repeat_and_recovery() {
    auto first = contribution("a-first", "owner-a", {"good"},
        [](std::size_t) { return result({{"good", 5.0}}, "first", 1.0); });
    auto second = contribution("z-second", "owner-a", {"late-state"},
        [](std::size_t) {
            return result({{"rogue", 8.0}}, "failed-window", 7.0);
        });
    auto store = make_store();
    ContributionExecutor executor(2);
    cc::CombineScheduler scheduler({second, first}, &executor, store);
    const auto before = snapshot(store, scheduler);
    for (int attempt = 0; attempt < 2; ++attempt) {
        bool refused = false;
        try { (void)scheduler.run_window(); }
        catch (const cc::Refusal& ex) {
            refused = ex.code() == "combine_undeclared_contribution_output";
        }
        check(refused, "repeated fixed-input window did not refuse deterministically");
        check(same(before, snapshot(store, scheduler)),
              "repeated refused window changed scheduler/store state");
    }

    // The current scheduler API freezes its callback set at construction.
    // Recovery therefore uses a new scheduler with immutable valid callbacks,
    // sharing the same caller-owned store that both refusals left untouched.
    auto clean_first = contribution("a-first", "owner-a", {"good"},
        [](std::size_t) { return result({{"good", 5.0}}, "first", 1.0); });
    auto clean_second = contribution("z-second", "owner-a", {"late-state"},
        [](std::size_t) {
            return result({{"late-state", 8.0}}, "valid-window", 7.0);
        });
    cc::CombineScheduler recovery({clean_second, clean_first}, &executor, store);
    const auto recovered_report = recovery.run_window();
    auto clean_store = make_store();
    ContributionExecutor clean_executor(1);
    cc::CombineScheduler clean({clean_second, clean_first}, &clean_executor,
                               clean_store);
    const auto clean_report = clean.run_window();
    check(store.canonical_bytes() == clean_store.canonical_bytes() &&
              store.digest() == clean_store.digest() &&
              store.applies() == clean_store.applies() &&
              recovery.ledger_digest() == clean.ledger_digest() &&
              recovered_report.routed == clean_report.routed,
          "new-scheduler recovery differs from a clean valid window");
}

void candidate_suite() {
    const std::vector<std::pair<std::string, std::string>> refusals{
        {"undeclared", "combine_undeclared_contribution_output"},
        {"wrong_owner", "combine_non_owner_write"},
        {"unknown_state", "combine_unknown_state"},
        {"duplicate", "combine_double_state_write"},
        {"callback", "test_callback_failure"},
    };
    std::size_t refusal_cases = 0;
    for (const auto& item : refusals) {
        for (std::size_t workers : {1u, 2u, 4u}) {
            expect_refused_unchanged(item.first, item.second, workers);
            ++refusal_cases;
        }
    }
    same_scheduler_repeat_and_recovery();
    success_parity();
    print_success_signature(run_success(1, success_contributors()));
    std::cout << "CANDIDATE_REFUSAL_CASES=" << refusal_cases << '\n'
              << "CANDIDATE_REPEAT_AND_RECOVERY=PASS\n"
              << "CANDIDATE_SUCCESS_PARITY=9\n";
}

} // namespace

int main(int argc, char** argv) {
    try {
        check(argc == 2, "usage: transaction_gate baseline|candidate");
        const std::string mode = argv[1];
        if (mode == "baseline") baseline_discriminator();
        else if (mode == "reference")
            print_success_signature(run_success(1, success_contributors()));
        else if (mode == "candidate") candidate_suite();
        else throw std::runtime_error("unknown mode " + mode);
        std::cout << "GATE_PASS=" << mode << '\n';
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "GATE_FAIL=" << ex.what() << '\n';
        return 1;
    }
}
